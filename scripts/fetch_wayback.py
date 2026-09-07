#!/usr/bin/env python3
"""
Collect monthly snapshots of provider pricing pages from the Internet Archive.

This script was written but NOT run when the repository was created: the
Wayback Machine was unreachable from the machine used to build the current
cross-section. Run it yourself and commit both the raw HTML and the log.

What it does
------------
For each pricing page it queries the Wayback CDX API for every capture in
the requested window, keeps the first capture in each calendar month, and
downloads that capture's raw HTML into raw/<provider>/<YYYY-MM>.html. It
also writes raw/manifest.csv recording, for every file, the exact archive
URL and capture timestamp it came from.

It deliberately does not parse prices. Parsing is a separate step, because
provider pages change layout and a parser that silently drifts is worse
than no parser. Extract prices with parse_wayback.py once you have looked
at a few files by hand.

Usage
-----
    pip install requests
    python3 scripts/fetch_wayback.py --from 2023-01 --to 2026-09
    python3 scripts/fetch_wayback.py --provider anthropic --from 2024-06

Be polite: the archive is a free service. SLEEP_SECONDS throttles requests
and should not be lowered.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    sys.exit("This script needs the requests library:  pip install requests")

CDX_ENDPOINT = "http://web.archive.org/cdx/search/cdx"
SLEEP_SECONDS = 1.5
TIMEOUT = 60
USER_AGENT = (
    "llm-api-price-panel/0.1 (academic price-history collection; "
    "contact: add your email here)"
)

# Pages worth tracking. Providers move their pricing pages, so several
# historical URLs per provider are listed; captures from all of them are
# merged and de-duplicated by month.
TARGETS: dict[str, list[str]] = {
    "openai": [
        "openai.com/api/pricing",
        "openai.com/pricing",
        "platform.openai.com/docs/pricing",
        "developers.openai.com/api/docs/pricing",
    ],
    "anthropic": [
        "anthropic.com/pricing",
        "anthropic.com/api",
        "docs.anthropic.com/en/docs/about-claude/pricing",
        "docs.claude.com/en/docs/about-claude/pricing",
        "platform.claude.com/docs/en/about-claude/pricing",
    ],
    "google": [
        "ai.google.dev/pricing",
        "ai.google.dev/gemini-api/docs/pricing",
        "cloud.google.com/vertex-ai/generative-ai/pricing",
    ],
    "xai": [
        "x.ai/api",
        "docs.x.ai/docs/models",
        "docs.x.ai/developers/pricing",
    ],
    "mistral": [
        "mistral.ai/technology",
        "mistral.ai/pricing",
        "mistral.ai/pricing/api",
    ],
    "deepseek": [
        "api-docs.deepseek.com/quick_start/pricing",
        "platform.deepseek.com/api-docs/pricing",
        "deepseek.com/pricing",
    ],
}


def month_key(timestamp: str) -> str:
    """20240517093000 -> 2024-05"""
    return f"{timestamp[:4]}-{timestamp[4:6]}"


def list_captures(session, url: str, ts_from: str, ts_to: str) -> list[tuple[str, str]]:
    """Return [(timestamp, original_url)] for successful captures of `url`."""
    params = {
        "url": url,
        "output": "json",
        "from": ts_from,
        "to": ts_to,
        "fl": "timestamp,original,statuscode",
        "filter": "statuscode:200",
        "collapse": "timestamp:6",  # one capture per month at the source
    }
    resp = session.get(CDX_ENDPOINT, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        return []
    return [(r[0], r[1]) for r in rows[1:]]  # drop the header row


def download(session, timestamp: str, original: str) -> str:
    """Fetch the raw archived HTML. `id_` asks for the unrewritten original."""
    archive_url = f"http://web.archive.org/web/{timestamp}id_/{original}"
    resp = session.get(archive_url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", default="2023-01", help="YYYY-MM")
    ap.add_argument("--to", dest="to", default=datetime.utcnow().strftime("%Y-%m"))
    ap.add_argument("--provider", default=None, help="limit to one provider")
    ap.add_argument("--out", default="raw", help="output directory")
    args = ap.parse_args()

    ts_from = args.frm.replace("-", "") + "01"
    ts_to = args.to.replace("-", "") + "28"

    providers = [args.provider] if args.provider else list(TARGETS)
    for p in providers:
        if p not in TARGETS:
            sys.exit(f"unknown provider: {p}. known: {', '.join(TARGETS)}")

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_root = os.path.join(root, args.out)
    os.makedirs(out_root, exist_ok=True)

    manifest_path = os.path.join(out_root, "manifest.csv")
    new_manifest = not os.path.exists(manifest_path)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    with open(manifest_path, "a", newline="", encoding="utf-8") as mf:
        writer = csv.writer(mf)
        if new_manifest:
            writer.writerow([
                "provider", "month", "wayback_timestamp",
                "original_url", "archive_url", "local_path", "bytes",
            ])

        for provider in providers:
            os.makedirs(os.path.join(out_root, provider), exist_ok=True)
            seen_months: set[str] = set()

            for url in TARGETS[provider]:
                try:
                    captures = list_captures(session, url, ts_from, ts_to)
                except Exception as exc:  # noqa: BLE001
                    print(f"  ! CDX failed for {url}: {exc}")
                    time.sleep(SLEEP_SECONDS)
                    continue

                print(f"{provider:10s} {url:52s} {len(captures):4d} captures")

                for timestamp, original in captures:
                    month = month_key(timestamp)
                    if month in seen_months:
                        continue

                    local_path = os.path.join(out_root, provider, f"{month}.html")
                    if os.path.exists(local_path):
                        seen_months.add(month)
                        continue

                    try:
                        html = download(session, timestamp, original)
                    except Exception as exc:  # noqa: BLE001
                        print(f"  ! download failed {month}: {exc}")
                        time.sleep(SLEEP_SECONDS)
                        continue

                    with open(local_path, "w", encoding="utf-8") as fh:
                        fh.write(html)

                    seen_months.add(month)
                    writer.writerow([
                        provider, month, timestamp, original,
                        f"http://web.archive.org/web/{timestamp}id_/{original}",
                        os.path.relpath(local_path, root), len(html),
                    ])
                    mf.flush()
                    print(f"  + {month}  {len(html):>9,d} bytes")
                    time.sleep(SLEEP_SECONDS)

    print("\ndone. raw HTML is under", out_root)
    print("next: read a few files by hand before writing any parser.")


if __name__ == "__main__":
    main()
