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

**Cross-section:** 61 rows, 5 providers, read 2026-09-07.
**History:** 188 archived captures, 6 providers, 2023-01 to 2026-09,
collected and catalogued — **not yet parsed into prices.**

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

## The price history

`scripts/fetch_wayback.py` has been run. It pulled one Internet Archive
capture per calendar month for each provider's pricing page and catalogued
every one in `raw/manifest.csv`, which records the capture timestamp and
the exact archive URL each file came from.

| provider | captures | earliest |
|---|---:|---|
| OpenAI | 45 | 2023-01 |
| Google | 34 | |
| Mistral | 31 | |
| Anthropic | 28 | |
| DeepSeek | 27 | |
| xAI | 23 | |

The archived HTML is about 50 MB and is deliberately **not** committed. The
manifest makes it reproducible: re-run the script, or fetch any single
capture from the archive URL in the manifest.

**These captures have not been parsed yet.** Nothing in this repository
currently makes a claim about how prices moved over time. Writing the
parser is the next piece of work, and it is not trivial — the providers
redesigned their pricing pages several times over three years, and a
parser that silently drifts across layouts is worse than no parser.

---

## Layout

```
data/prices_current.csv     the cross-section
raw/manifest.csv            188 archive captures: timestamp + source URL
scripts/build_current.py    hand-transcribed source records -> csv
scripts/analyze.py          the ratios above
scripts/fetch_wayback.py    monthly history collector
```

### Columns in `prices_current.csv`

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

Every row in the cross-section was transcribed by hand from the provider's
own documentation on the access date. No price-comparison site, aggregator
or blog was used as a source, and no missing value was imputed — where a
provider does not publish a number the field is empty.

Known limitations, in the order they would bite:

- **The analysis is still one time point.** The captures are collected but
  unparsed, so every number above describes a single day.
- **DeepSeek is missing from the cross-section.** Its official pricing page
  did not render on the access date. Third-party figures were available and
  were not used. Its 27 archived captures are in the manifest, so the gap
  closes when the parser exists.
- **List prices, not transaction prices.** Enterprise contracts,
  committed-use discounts and negotiated rates are invisible here, and for
  the largest buyers those are the prices that exist.
- **Batch, flex and priority tiers are only partly captured.** Google
  publishes four service tiers; only standard is in the table.
- **Fine-tuning is barely covered.** OpenAI bills training by the hour, not
  the token, which does not fit the schema and does not fit the model in
  the paper either.
- **Model identity is not stable.** A provider can change what sits behind
  a model name without changing the name. Nothing here detects that.

Ratios as clean as the ones above are usually a sign of an administered
price — a number chosen for being round and defensible rather than derived
from costs — but distinguishing that from a genuine cost ratio needs the
time series, and the time series is not parsed yet.

---

## Running it

```bash
python3 scripts/build_current.py    # rebuild the csv from source records
python3 scripts/analyze.py          # print the ratios

pip install requests
python3 scripts/fetch_wayback.py --from 2023-01 --to 2026-09
```

`fetch_wayback.py` is incremental: it skips months already on disk, so it
is safe to re-run to extend coverage.

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
