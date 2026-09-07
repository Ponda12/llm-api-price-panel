# LLM API price panel

Published list prices for large language model APIs, transcribed from the
providers' own documentation, in one machine-readable table.

The dataset exists because of a gap. Bergemann, Bonatti and Smolin (ACM EC
2025, [*The Economics of Large Language Models*](https://arxiv.org/abs/2502.07736))
derive how a monopolist selling LLM inference should price input tokens,
output tokens and fine-tuning. Their Proposition 7 says the optimal
mechanism is a menu of two-part tariffs in which each token type is priced
at its marginal cost times a markup that varies across plans. The paper is
pure theory and contains no data. The prices it is a theory of are public.

So this repository collects them.

**Access date: 2026-09-07. 61 rows, 5 providers, 44 model-tier
combinations.**

---

## What the numbers look like

Three patterns are visible in the current cross-section. None of them is a
result — one snapshot cannot establish anything — but each is specific
enough to be worth explaining or explaining away.

### 1. Anthropic prices output at exactly five times input, everywhere

Across seventeen models, from Haiku 3.5 at \$0.80 per million input tokens
to Opus 4.1 at \$15.00, a nineteen-fold range of price level, the
output/input ratio is 5.00. Not approximately five. Five, with no
variation, including on retired models.

The other four providers spread out: Google 4.50–8.33, Mistral 1.00–5.00,
OpenAI 3.75–6.00, xAI 2.00–3.00.

This matters for the theory because prefill and decode are different
operations. Prefill is compute-bound and parallel; decode is
memory-bandwidth-bound and sequential, and the gap between them depends on
model size, attention shape and batch policy. A ratio that survives a
nineteen-fold change in model tier is not tracking $c_y / c_x$.

### 2. Three independent firms landed on a cache discount of exactly 0.100

A cache hit skips prefill, so the discount should reflect whatever prefill
actually costs that provider. OpenAI prices cached input at 0.100 of
standard input on every model. Google, 0.100. Mistral's GLM 5.2, 0.100.
Anthropic, 0.100 on eleven of thirteen models.

xAI is the exception and prices cache per model: 0.150, 0.160, 0.200,
0.250.

Anthropic is the other exception, in the opposite direction. Fable 5.1 and
Mythos 5.1 discount cached input to 0.025 — a four-fold deeper discount
than the rest of the same lineup, and the documentation flags it as
deliberate.

### 3. Long context costs twice as much to read and half again as much to write

Where a provider splits pricing at a context threshold, OpenAI and Google
apply the same pair of multipliers: input × 2.00, output × 1.50. Four
OpenAI models and two Gemini models, identical.

xAI charges × 2.00 on both.

Two firms treat a long prompt as making generation more expensive than it
otherwise would be, but less than proportionally. One treats it as
proportional. They cannot both be reading the cost structure correctly.

Reproduce all of this with `python3 scripts/analyze.py`.

---

## Layout

```
data/prices_current.csv     the cross-section
scripts/build_current.py    hand-transcribed source records -> csv
scripts/analyze.py          the ratios above
scripts/fetch_wayback.py    monthly history collector (see caveat below)
```

### Columns

| column | meaning |
|---|---|
| `provider` | openai, anthropic, google, xai, mistral |
| `model` | model id as the provider writes it |
| `tier` | standard, retired, finetuned_inference, finetuned_inference_batch |
| `context_bucket` | `short` / `long` where pricing splits at a threshold, else `all` |
| `input_price` | USD per 1M input tokens |
| `cached_input_price` | USD per 1M cached-read input tokens; empty if unpublished |
| `output_price` | USD per 1M output tokens |
| `access_date` | when the page was read |
| `source_url` | the page it was read from |
| `notes` | anything that would mislead without it |

---

## How it was built, and what is wrong with it

Every row was transcribed by hand from the provider's own documentation on
the access date. No price-comparison site, aggregator or blog was used as a
source, and no missing value was imputed — where a provider does not
publish a number the field is empty.

Known limitations, in the order they would bite:

- **One time point.** The Wayback Machine was unreachable from the machine
  used to build this, so the history is not here yet.
  `scripts/fetch_wayback.py` is written and documented but **has not been
  run**. Nothing in this repository has been checked over time.
- **DeepSeek is missing.** Its official pricing page did not resolve on the
  access date. Third-party figures were available and were not used.
- **List prices, not transaction prices.** Enterprise contracts, committed-use
  discounts and negotiated rates are invisible here, and for the largest
  buyers those are the prices that exist.
- **Batch, flex and priority tiers are only partly captured.** Google
  publishes four service tiers; only standard is in the table.
- **Fine-tuning is barely covered.** OpenAI bills training by the hour, not
  the token, which does not fit the schema and does not fit the model in
  the paper either.
- **Model identity is not stable.** A provider can change what sits behind
  a model name without changing the name. Nothing here detects that.

The three patterns above are descriptive statistics on a single day. Ratios
this clean are usually a sign of an administered price — a number chosen for
being round and defensible rather than derived — but distinguishing that
from a genuine cost ratio needs the time series, and the time series is the
next piece of work.

---

## Running it

```bash
python3 scripts/build_current.py    # rebuild the csv from source records
python3 scripts/analyze.py          # print the ratios

pip install requests
python3 scripts/fetch_wayback.py --from 2023-01 --to 2026-09
```

`fetch_wayback.py` downloads raw archived HTML and writes a manifest
recording which capture each file came from. It does not parse prices. Read
a few files by hand before writing a parser — provider pages change layout,
and a parser that drifts silently is worse than no parser at all.

---

## Contributing

Corrections are the most useful thing you can send. If a number here is
wrong, open an issue with the provider's own URL and the date you read it.
Numbers from aggregator sites will not be merged.

---


## License

CC0 1.0 — public domain. The underlying prices are published by their
providers and are facts; this repository is the transcription. Cite it if it
helps you, or don't.
