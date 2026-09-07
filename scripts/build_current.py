#!/usr/bin/env python3
"""
Build the current cross-section of published LLM API list prices.

Every row below was transcribed by hand from the provider's own
documentation on the access date recorded in ACCESS_DATE. No third-party
aggregator, price-comparison site or blog was used. Where a provider does
not publish a number, the field is left empty rather than imputed.

Prices are US dollars per 1,000,000 tokens unless stated otherwise.

Run:  python3 scripts/build_current.py
Out:  data/prices_current.csv
"""

import csv
import os

ACCESS_DATE = "2026-09-07"

SOURCES = {
    "openai": "https://developers.openai.com/api/docs/pricing",
    "anthropic": "https://platform.claude.com/docs/en/about-claude/pricing",
    "google": "https://ai.google.dev/gemini-api/docs/pricing",
    "xai": "https://docs.x.ai/developers/pricing",
    "mistral": "https://mistral.ai/pricing/api",
}

FIELDS = [
    "provider", "model", "tier", "context_bucket",
    "input_price", "cached_input_price", "output_price",
    "currency", "unit", "access_date", "source_url", "notes",
]

# provider, model, tier, context_bucket, input, cached_input, output, notes
ROWS = [
    # ---------------- OpenAI ----------------
    ("openai", "gpt-6-astra",   "standard", "short", 10.00, 1.00, 50.00, ""),
    ("openai", "gpt-6-astra",   "standard", "long",  20.00, 2.00, 75.00, ""),
    ("openai", "gpt-5.6-sol",   "standard", "short",  4.00, 0.40, 20.00, ""),
    ("openai", "gpt-5.6-sol",   "standard", "long",   8.00, 0.80, 30.00, ""),
    ("openai", "gpt-5.6-terra", "standard", "short",  2.00, 0.20, 12.00, ""),
    ("openai", "gpt-5.6-terra", "standard", "long",   4.00, 0.40, 18.00, ""),
    ("openai", "gpt-5.6-luna",  "standard", "short",  0.20, 0.02,  1.20, ""),
    ("openai", "gpt-5.6-luna",  "standard", "long",   0.40, 0.04,  1.80, ""),
    ("openai", "gpt-5.6-cyber", "standard", "short", 12.50, 1.25, 75.00, ""),
    ("openai", "o4-mini-2025-04-16", "finetuned_inference", "short",
     4.00, 1.00, 16.00, "fine-tuning training billed at $100/hour, not per token"),
    ("openai", "o4-mini-2025-04-16", "finetuned_inference_batch", "short",
     2.00, 0.50, 8.00, ""),

    # ---------------- Anthropic ----------------
    # cached_input_price = cache hit (read) price
    ("anthropic", "claude-fable-5.1",  "standard", "all", 10.00, 0.25, 50.00,
     "cache hit is 0.025x input, not the 0.1x used elsewhere in the lineup"),
    ("anthropic", "claude-mythos-5.1", "standard", "all", 10.00, 0.25, 50.00,
     "cache hit is 0.025x input"),
    ("anthropic", "claude-fable-5",    "standard", "all", 10.00, 1.00, 50.00, ""),
    ("anthropic", "claude-mythos-5",   "standard", "all", 10.00, 1.00, 50.00, ""),
    ("anthropic", "claude-opus-5",     "standard", "all",  5.00, 0.50, 25.00, ""),
    ("anthropic", "claude-opus-4.8",   "standard", "all",  5.00, 0.50, 25.00, ""),
    ("anthropic", "claude-opus-4.7",   "standard", "all",  5.00, 0.50, 25.00, ""),
    ("anthropic", "claude-opus-4.6",   "standard", "all",  5.00, 0.50, 25.00, ""),
    ("anthropic", "claude-opus-4.5",   "standard", "all",  5.00, 0.50, 25.00, ""),
    ("anthropic", "claude-sonnet-5",   "standard", "all",  2.00, 0.20, 10.00, ""),
    ("anthropic", "claude-sonnet-4.6", "standard", "all",  3.00, 0.30, 15.00, ""),
    ("anthropic", "claude-sonnet-4.5", "standard", "all",  3.00, 0.30, 15.00, ""),
    ("anthropic", "claude-haiku-4.5",  "standard", "all",  1.00, 0.10,  5.00, ""),
    ("anthropic", "claude-opus-4.1",   "retired",  "all", 15.00, 1.50, 75.00, ""),
    ("anthropic", "claude-opus-4",     "retired",  "all", 15.00, 1.50, 75.00, ""),
    ("anthropic", "claude-sonnet-4",   "retired",  "all",  3.00, 0.30, 15.00, ""),
    ("anthropic", "claude-haiku-3.5",  "retired",  "all",  0.80, 0.08,  4.00, ""),

    # ---------------- Google ----------------
    ("google", "gemini-3.8-flash", "standard", "all", 0.75, 0.075, 3.75,
     "promotional rate through 2026-12-31; doubles on 2027-01-01"),
    ("google", "gemini-3.7-flash", "standard", "all", 0.75, 0.075, 3.75,
     "promotional rate through 2026-12-31"),
    ("google", "gemini-3.6-flash", "standard", "all", 0.75, 0.075, 3.75,
     "promotional rate through 2026-12-31"),
    ("google", "gemini-3.5-flash", "standard", "all", 1.50, None, 9.00, ""),
    ("google", "gemini-3.5-flash-lite", "standard", "all", 0.30, None, 2.50, ""),
    ("google", "gemini-3.1-flash-lite", "standard", "all", 0.25, None, 1.50,
     "text/image/video rate; audio input is 0.50"),
    ("google", "gemini-3.1-pro-preview", "standard", "short", 2.00, None, 12.00,
     "short = context up to 200k tokens"),
    ("google", "gemini-3.1-pro-preview", "standard", "long", 4.00, None, 18.00,
     "long = context above 200k tokens"),
    ("google", "gemini-2.5-pro", "standard", "short", 1.25, None, 10.00, ""),
    ("google", "gemini-2.5-pro", "standard", "long",  2.50, None, 15.00, ""),
    ("google", "gemini-2.5-flash", "standard", "all", 0.30, None, 2.50,
     "text/image/video rate; audio input is 1.00"),

    # ---------------- xAI ----------------
    ("xai", "grok-4.6",       "standard", "short", 2.00, 0.50,  6.00, ""),
    ("xai", "grok-4.6",       "standard", "long",  4.00, 1.00, 12.00, ""),
    ("xai", "grok-build-0.1", "standard", "short", 1.00, 0.20,  2.00, ""),
    ("xai", "grok-build-0.1", "standard", "long",  2.00, 0.40,  4.00, ""),
    ("xai", "grok-4.5",       "standard", "short", 2.00, 0.30,  6.00, ""),
    ("xai", "grok-4.5",       "standard", "long",  4.00, 0.60, 12.00, ""),
    ("xai", "grok-4.3",       "standard", "short", 1.25, 0.20,  2.50, ""),
    ("xai", "grok-4.3",       "standard", "long",  2.50, 0.40,  5.00, ""),
    ("xai", "grok-4.20-multi-agent-0309",  "standard", "short", 1.25, 0.20, 2.50, ""),
    ("xai", "grok-4.20-multi-agent-0309",  "standard", "long",  2.50, 0.40, 5.00, ""),
    ("xai", "grok-4.20-0309-reasoning",    "standard", "short", 1.25, 0.20, 2.50, ""),
    ("xai", "grok-4.20-0309-reasoning",    "standard", "long",  2.50, 0.40, 5.00, ""),
    ("xai", "grok-4.20-0309-non-reasoning","standard", "short", 1.25, 0.20, 2.50, ""),
    ("xai", "grok-4.20-0309-non-reasoning","standard", "long",  2.50, 0.40, 5.00, ""),

    # ---------------- Mistral ----------------
    ("mistral", "mistral-medium-3.5", "standard", "all", 1.50, None, 7.50, ""),
    ("mistral", "mistral-small-4",    "standard", "all", 0.15, None, 0.60, ""),
    ("mistral", "mistral-large-3",    "standard", "all", 0.50, None, 1.50, ""),
    ("mistral", "glm-5.2",            "standard", "all", 1.40, 0.14, 4.40,
     "third-party model served on Mistral's platform"),
    ("mistral", "ministral-3-3b",     "standard", "all", 0.10, None, 0.10, ""),
    ("mistral", "ministral-3-8b",     "standard", "all", 0.15, None, 0.15, ""),
    ("mistral", "ministral-3-14b",    "standard", "all", 0.20, None, 0.20, ""),
    ("mistral", "codestral",          "standard", "all", 0.30, None, 0.90, ""),
]


def main() -> None:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(here, "data", "prices_current.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for provider, model, tier, bucket, inp, cached, out, notes in ROWS:
            writer.writerow({
                "provider": provider,
                "model": model,
                "tier": tier,
                "context_bucket": bucket,
                "input_price": inp,
                "cached_input_price": "" if cached is None else cached,
                "output_price": out,
                "currency": "USD",
                "unit": "per_1M_tokens",
                "access_date": ACCESS_DATE,
                "source_url": SOURCES[provider],
                "notes": notes,
            })

    print(f"wrote {len(ROWS)} rows to {out_path}")


if __name__ == "__main__":
    main()
