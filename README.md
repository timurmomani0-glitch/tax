# AF1204 Data-Literacy Portfolio — Do firms disclose what their numbers say?

**Research question:** for large US listed firms (the "Magnificent 7"), does the risk
language and tone a company discloses in its filings align with its financial health
and market valuation?

**Deliverable:** `portfolio.py` (marimo) → standalone WASM HTML site in `docs/` →
GitHub Pages. Live demo of Weeks 1–10 skills in one research story.

> `course_materials/` holds only the course-provided data files the pipelines
> read (ESG panel, few-shot examples, vocabulary list) — see its README.

## Architecture — two layers

**Layer A (offline pipelines → `data/` artifacts; never deployed):**

| Pipeline | Weeks | What it does | Needs network? |
|---|---|---|---|
| `pipelines/pipeline_1_financials.py` | 2–3 | yfinance → Mag-7 firm-year panel (FY 2021–2025) → Altman Z-Score → `financials.csv` | Yahoo Finance |
| `pipelines/pipeline_1b_financials_sec.py` | 2–3 + self-exp | Fallback when Yahoo rate-limits: SEC XBRL companyfacts (fundamentals) + course-provided market caps → Z-Scores FY 2021–2023 → `financials.csv` | sec.gov |
| `pipelines/pipeline_2_edgar.py` | 7 | SEC EDGAR 10-K → Item 1A risk text (2015, 2025) → `risk_data.json` | sec.gov |
| `pipelines/pipeline_3_llm.py` | 8–9 | Groq LLM few-shot tone + independent AI-judge → `sentiment.csv`, `judge_eval.csv` | Groq API |
| `pipelines/pipeline_3b_wordclouds.py` | 10 | spaCy/nltk n-grams → 2015-vs-2025 word clouds → `data/wordclouds/` | no (after 2) |
| `pipelines/pipeline_4_merge.py` | 6, 10 | **Polars** merge of provided ESG+accounting data → Tobin's q regressions (statsmodels Models 1–4 + robustness) → `site_*.csv`, `analysis.parquet` | no |
| `pipelines/pipeline_5_crosscheck.py` + `notebooks/Regression_CrossCheck.ipynb` | 10 + self-exp | Model 4 re-estimated with **linearmodels** (within estimator) — coefficients match statsmodels to 6dp; Python **stargazer** table → `regression_table.html` | no |

**Layer B (deployed):** `portfolio.py` reads ONLY the `data/` artifacts over raw
GitHub URLs (the Week 4 course pattern — bundled local files don't survive GitHub
Pages compression). Static WASM: no server, no secrets, no live API calls.

## Reproduce from a clean clone

```bash
# 0. secrets (never committed — .env is gitignored)
cp .env.example .env        # then fill in GROQ_API_KEY and SEC_USER_AGENT

# 1. environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. offline layer (order matters)
python pipelines/pipeline_4_merge.py        # provided data → regressions (no network)
python pipelines/pipeline_1_financials.py   # Yahoo Finance → Z-Scores
python pipelines/pipeline_2_edgar.py        # SEC EDGAR → Item 1A text
python pipelines/pipeline_3_llm.py          # Groq → tone + judge
python pipelines/pipeline_3b_wordclouds.py  # word clouds
python pipelines/pipeline_5_crosscheck.py   # two-library regression cross-check
# interactive version: open notebooks/Regression_CrossCheck.ipynb (Jupyter)

# 3. tests
python tests/test_offline.py

# 4. export + deploy (course Week 4 commands)
marimo export html-wasm portfolio.py -o docs --sandbox --force
# same-origin data fallback (the site tries raw GitHub first, then ./data/)
mkdir -p docs/data && cp data/*.csv docs/data/ && cp -r data/wordclouds docs/data/
git add -A && git commit -m "Update site" && git push
# GitHub → Settings → Pages → Build from branch: main, folder /docs
```

### Deploying from a different repo (e.g. the course fork `timurmomani/tax`)

Copy the project files (`portfolio.py`, `pipelines/`, `data/`, `notebooks/`,
`docs/`, `requirements.txt`, `.env.example`, this README) into the fork. The site
loads its data from the `RAW_BASE` URL at the top of `portfolio.py`, which points at
this repo — that keeps working from any host while this repo is public. To make the
fork fully self-contained instead, change that one line to the fork's raw URL
(e.g. `https://raw.githubusercontent.com/timurmomani/tax/main/data/`), re-run the
export command above, and push.

## Two-library agreement check — confirmed

`pipeline_4_merge.py` (statsmodels, dummy-variable FE) Model 4 on Provider B:
**ESGscore = 0.0026\*\*** (se 0.0012, N = 7,895). `pipeline_5_crosscheck.py`
re-estimates it with **linearmodels PanelOLS** (within estimator): every
coefficient matches to 6 decimals (`data/crosscheck.json`). The interactive
walk-through is `notebooks/Regression_CrossCheck.ipynb` (Jupyter, Codespaces-ready).

## Why these tools (short version — long version on the site's Method tab)

- **EDGAR over scraping**: official API, no bot detection; requires only a
  self-identifying `User-Agent` and politeness delays (0.5 s).
- **yfinance for Z-Scores**: the provided accounting file lacks current
  assets/liabilities and retained earnings; free Yahoo data covers ~4–5 years,
  hence FY 2021–2025.
- **Polars** (self-exploration): 245k-row ESG panel × 2 providers joined lazily in
  one optimised pass, Parquet output.
- **linearmodels + Python stargazer** (self-exploration): independent
  re-estimation (within estimator vs dummy variables) guards against silent
  specification bugs — everything stays in Python, Codespaces-ready.
- **Two LLM families** (self-exploration): `openai/gpt-oss-120b` classifies (course
  Week 9 settings), `llama-3.3-70b-versatile` re-judges a sample, primed with the
  Week 8 ambiguous-vocabulary list; agreement rate in `data/judge_eval.csv`.

## Video segments (3 min)

Tab 1 Overview → Tab 2 Financial Health (widgets!) → Tab 3 ESG & Valuation
(tables + two-library agreement) → Tab 4 Risk Language (clouds + tone) → Tab 5 Method &
Limitations. Each tab is one segment.
