# Do firms disclose what their numbers say?

**Live site:** https://bayesug-ai.github.io/Timur-Momani-CV2-AF1204/
(development mirror: https://timurmomani0-glitch.github.io/tax/)

A data-literacy portfolio built for AF1204 at Bayes Business School. It asks one
question about the "Magnificent 7" (Apple, Microsoft, Alphabet, Amazon, Meta,
Nvidia, Tesla): does the risk language a company publishes in its 10-K filings
line up with its financial health and market valuation?

The deliverable is a single marimo notebook, `portfolio.py`, exported to a
standalone WebAssembly site and served on GitHub Pages. Everything on the page —
Altman Z-Scores, ESG–valuation regressions, LLM tone scores, word clouds — comes
from data pipelines in this repository. Nothing is hand-typed.

## What the analysis found

Firms with higher ESG scores trade at a modest valuation premium once industry
and year effects are controlled for (ESG coefficient on Tobin's q: 0.0026,
significant at 5%, N = 7,895 firm-years). The result survives winsorisation but
flips sign under an alternative ESG provider and fades in sub-samples, so the
site presents it with those caveats rather than as a headline truth.

On the text side, the forward-looking sentences inside Item 1A risk sections are
overwhelmingly cautious for every firm in both 2015 and 2025 — which is itself
the finding: risk-factor language is structurally negative, and what changes
over the decade is *what* firms worry about (visible in the word clouds), not
how optimistically they phrase it. An independent second model re-judged a
sample of the classifications and agreed 78.6% of the time.

## How it is built

The project has two layers.

**The pipelines** (in `pipelines/`) do all the data work offline and write small
artifacts to `data/`:

| Script | What it does |
|---|---|
| `pipeline_1_financials.py` | Altman Z-Scores from Yahoo Finance statements (yfinance) |
| `pipeline_1b_financials_sec.py` | Same panel from the SEC's XBRL API + course market caps — used when Yahoo rate-limits cloud IPs |
| `pipeline_2_edgar.py` | Downloads 10-K "Item 1A Risk Factors" text from SEC EDGAR for 2015 and 2025 |
| `pipeline_3_llm.py` | Classifies forward-looking sentences with a Groq-hosted LLM, then has a second model family re-judge a sample |
| `pipeline_3b_wordclouds.py` | Lemmatised n-gram word clouds of the risk text, 2015 vs 2025 |
| `pipeline_4_merge.py` | Polars merge of the provided ESG and accounting panels; Tobin's q regressions in statsmodels |
| `pipeline_5_crosscheck.py` | Re-estimates the main regression with linearmodels; coefficients match statsmodels to six decimals |

**The site** (`portfolio.py`) never calls an API and holds no secrets. It reads
the committed artifacts over raw GitHub URLs, with a same-origin fallback under
`docs/data/`, and renders five tabs of interactive Plotly charts and tables.
`notebooks/Regression_CrossCheck.ipynb` is a Jupyter walk-through of the
two-library regression check.

`course_materials/` contains only the course-provided data files the pipelines
read (the ESG panel, few-shot sentiment examples, and a vocabulary list).

## Running it yourself

```bash
cp .env.example .env          # add your own GROQ_API_KEY and SEC_USER_AGENT
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python pipelines/pipeline_4_merge.py         # regressions (no network needed)
python pipelines/pipeline_5_crosscheck.py    # two-library cross-check
python pipelines/pipeline_2_edgar.py         # EDGAR risk text
python pipelines/pipeline_3_llm.py           # LLM tone + judge
python pipelines/pipeline_3b_wordclouds.py   # word clouds
python pipelines/pipeline_1_financials.py    # Z-Scores (or pipeline_1b via SEC)

python tests/test_offline.py                 # offline test suite
```

To preview the site locally, run `marimo run portfolio.py`. To rebuild the
deployed version:

```bash
marimo export html-wasm portfolio.py -o docs --sandbox --force
mkdir -p docs/data && cp data/*.csv docs/data/ && cp -r data/wordclouds docs/data/
```

Pushing to `main` triggers the GitHub Actions workflow in
`.github/workflows/deploy-pages.yml`, which publishes `docs/` to GitHub Pages
(the repository's Pages source is set to "GitHub Actions").

## Deploying from another repository

The site fetches data from the `RAW_BASE` URL defined at the top of
`portfolio.py`. If you copy the project into a different repository, either
leave that URL pointing here (it works from any host while this repo is public)
or change the one line to your own repo's raw URL and re-run the export.

## Design notes

- EDGAR was chosen over scraping corporate sites: it is an official API with no
  bot detection, asking only for a self-identifying User-Agent and polite
  request spacing.
- Polars handles the 245k-row ESG merge; the regression sample is 8,849
  firm-years after cleaning.
- Two LLM families are used deliberately — one classifies, a different one
  audits — so the accuracy check is not a model grading its own homework.
- The regression is estimated twice, in statsmodels and linearmodels, as a
  guard against silent specification mistakes.

Limitations (Z-Score calibration, ESG provider disagreement, LLM accuracy,
causality) are discussed on the site's Method & Limitations tab.
