#!/usr/bin/env python3
"""
Descriptive analysis of published LLM API list prices.

The question behind the numbers comes from Bergemann, Bonatti and Smolin
(EC 2025), "The Economics of Large Language Models". Their Proposition 7
says the optimal mechanism is a menu of two-part tariffs in which the
per-token price of each token type is that token's marginal cost times a
markup that varies across tariff plans.

That has an observable implication. Input tokens and output tokens are
produced by genuinely different operations: prefill is compute-bound and
parallel, decoding is memory-bandwidth-bound and sequential. Their cost
ratio should therefore differ across models of different size and
architecture. If the published output/input ratio instead sits on a
fixed number across a provider's whole lineup, the ratio is not tracking
marginal cost.

This script computes the ratios and prints what does and does not move.

Run:  python3 scripts/analyze.py
"""

import csv
import os
from collections import defaultdict


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["input_price"] = float(r["input_price"])
        r["output_price"] = float(r["output_price"])
        r["cached_input_price"] = (
            float(r["cached_input_price"]) if r["cached_input_price"] else None
        )
    return rows


def rule(char="-", n=68):
    print(char * n)


def section(title):
    print()
    rule("=")
    print(title)
    rule("=")


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = load(os.path.join(here, "data", "prices_current.csv"))

    live = [r for r in rows if r["tier"] in ("standard",)]

    # ---------------------------------------------------------------
    section("1. Output / input price ratio, by provider")
    print("Bonatti et al. Prop. 7: this ratio should track c_y / c_x.")
    print()

    by_provider = defaultdict(list)
    for r in live:
        ratio = r["output_price"] / r["input_price"]
        by_provider[r["provider"]].append((r["model"], r["context_bucket"], ratio))

    for provider in sorted(by_provider):
        vals = [v for _, _, v in by_provider[provider]]
        distinct = sorted({round(v, 3) for v in vals})
        spread = max(vals) - min(vals)
        print(f"{provider:10s}  n={len(vals):2d}  "
              f"min={min(vals):5.2f}  max={max(vals):5.2f}  spread={spread:5.2f}")
        print(f"{'':10s}  distinct ratios: "
              f"{', '.join(f'{d:g}' for d in distinct)}")
        print()

    # ---------------------------------------------------------------
    section("2. Anthropic: the ratio against the price level")
    print("If the ratio were cost-driven it should drift with model size.")
    print("The input price is a proxy for where the model sits in the lineup.")
    print()
    ant = sorted(
        [r for r in rows if r["provider"] == "anthropic"],
        key=lambda r: -r["input_price"],
    )
    print(f"{'model':22s} {'tier':9s} {'input':>7s} {'output':>7s} {'out/in':>7s}")
    rule()
    for r in ant:
        print(f"{r['model']:22s} {r['tier']:9s} "
              f"{r['input_price']:7.2f} {r['output_price']:7.2f} "
              f"{r['output_price'] / r['input_price']:7.2f}")

    lo = min(r["input_price"] for r in ant)
    hi = max(r["input_price"] for r in ant)
    print()
    print(f"Input price ranges over a factor of {hi / lo:.0f}x "
          f"({lo:g} to {hi:g} USD per 1M tokens).")

    # ---------------------------------------------------------------
    section("3. Cache discount: cached input / standard input")
    print("A cache hit skips prefill. The discount should reflect that saving,")
    print("which has no reason to be identical across independent firms.")
    print()
    print(f"{'provider':10s} {'model':32s} {'discount':>9s}")
    rule()
    for r in live:
        if r["cached_input_price"] is None:
            continue
        disc = r["cached_input_price"] / r["input_price"]
        print(f"{r['provider']:10s} {r['model']:32s} {disc:9.3f}")

    # ---------------------------------------------------------------
    section("4. Long context: what each provider charges extra for")
    print("Multiplier applied when the request crosses the context threshold.")
    print()
    pairs = defaultdict(dict)
    for r in live:
        if r["context_bucket"] in ("short", "long"):
            pairs[(r["provider"], r["model"])][r["context_bucket"]] = r

    print(f"{'provider':10s} {'model':32s} {'input x':>8s} {'output x':>9s}")
    rule()
    for (provider, model), d in sorted(pairs.items()):
        if "short" not in d or "long" not in d:
            continue
        ix = d["long"]["input_price"] / d["short"]["input_price"]
        ox = d["long"]["output_price"] / d["short"]["output_price"]
        print(f"{provider:10s} {model:32s} {ix:8.2f} {ox:9.2f}")

    print()
    rule("=")
    print("Coverage gap: DeepSeek is absent. Its official pricing page did not")
    print("resolve on the access date and no third-party figure was substituted.")
    rule("=")


if __name__ == "__main__":
    main()
