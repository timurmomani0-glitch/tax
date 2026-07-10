# Claude Code prompt — AF1204 individual portfolio, finish & deploy (target 90)

Copy everything below this line into Claude Code (Codespace or any session with
open internet). Do NOT paste API keys into the prompt — the Groq key belongs in
`.env` (local) or Codespaces secrets, never in chat or git.

---

ROLE — You are the lead engineer finishing a data-literacy portfolio for the Bayes
Business School **AF1204 individual assignment (50% of the module)**. The build is
already ~80% done and merged to `main` of `timurmomani0-glitch/tax`. Your job is to
run the remaining data pipelines, verify everything, migrate the project to the
official course fork, deploy, and prep the video. Work milestone by milestone and
show me each acceptance check's output.

## OFFICIAL SUBMISSION REQUIREMENTS (from the assignment brief — non-negotiable)

- Webpage loads at `https://bayesug-ai.github.io/repo2-AF1204-[username]` or
  `https://bayesug-ai.github.io/repoAF1204-[username]` and "is working in every
  aspect as described and seen in the video".
- Code lives on the **main branch** of that fork; working Python **marimo**
  notebook(s) generate the webpage.
- Video: MP4, ≤3 min, narration + screen recording + face visible throughout
  (picture-in-video), filename `[StudentEmailAddress][StudentIDNumber][yourGitHubUsername].mp4`.
- Grading: 40–54 = Weeks 1–4 skills; 55–69 = + (self-exploration OR Weeks 6+10);
  **70+ = + Weeks 7–9 (scraping, LLMs, LLM APIs) AND self-exploration**. Aim 90:
  one coherent research story, visible depth, honest limitations.

## WHAT ALREADY EXISTS (do not rebuild — read these first)

Repo `timurmomani0-glitch/tax`, all merged to main:
- `portfolio.py` — 5-tab marimo app (Overview / Financial Health / ESG & Valuation
  / Risk Language / Method & Limitations), reactive widgets, tab state persisted
  via `mo.state`, WASM-exported to `docs/`. Data loads from `RAW_BASE` (raw GitHub
  URL at the top of the file) because bundled local files don't survive GitHub
  Pages compression (course Week 4 caveat).
- `pipelines/pipeline_4_merge.py` — ALREADY RUN on the provided course data:
  Polars merge (245k ESG rows → 8,849 firm-years), statsmodels Models 1–4.
  Real result committed: ESGscore on Tobin's q = **0.0026\*\* (se 0.0012, N=7,895)**
  with industry+year FE; robustness: survives winsorisation, flips sign under
  Provider A, insignificant for large firms and 2010–2019. Site text matches this.
- `pipelines/pipeline_1_financials.py` — yfinance Mag-7 FY2021–2025 Altman Z-Score
  panel (course Week 2 formula, hand-checked test passes). NOT YET RUN (needs net).
- `pipelines/pipeline_2_edgar.py` — SEC EDGAR Item 1A for Mag-7 × {2015, 2025}.
  Improved over the course notebook: fiscal-period (reportDate) matching so
  AAPL/MSFT map fiscal years correctly, and a TOC-aware extractor (regression
  test covers it). NOT YET RUN.
- `pipelines/pipeline_3_llm.py` — Groq few-shot sentiment (`openai/gpt-oss-120b`,
  temp 0, course Week 9 JSON contract) + independent AI judge
  (`llama-3.3-70b-versatile`) primed with the Week 8 ambiguous-terms CSV. NOT YET RUN.
- `pipelines/pipeline_3b_wordclouds.py` — 3-tier NLP engine (en_core_web_trf GPU /
  en_core_web_sm CPU / nltk fallback), course stopwords + blacklist +
  redundant-unigram rule, Reds(2015)/Blues(2025) clouds. NOT YET RUN.
- `analysis_R/WK10_ResultTables_AF1204.Rmd` — same Models 1–4 in R, stargazer →
  `data/regression_r.html` + printed Python↔R agreement check. NOT YET RUN.
- `notebooks_colab/wordclouds_gpu_colab.ipynb` — Colab T4 GPU rerun with timings.
- `tests/test_offline.py` — 7/7 pass. `.env` is gitignored; `.env.example` template.
- `README.md` — full reproduce steps + fork migration notes.

## VERIFIED COURSE FACTS (do not re-derive or invent)

- Export: `marimo export html-wasm portfolio.py -o docs --sandbox --force`
- Deploy: push `docs/` to main → Settings → Pages → branch `main`, folder `/docs`
  (if re-deploying: set branch to None, Save, then back to main/docs; watch Actions)
- SEC requires `User-Agent: "Timur Momani timurmomani0@gmail.com"` (in `.env` as
  SEC_USER_AGENT) and 0.5 s politeness sleeps. EDGAR is official — never bypass
  CAPTCHAs anywhere.
- Yahoo free data ≈ last 4–5 fiscal years → Z panel is FY2021–2025 by design.
- marimo: a top-level name may be defined in exactly ONE cell; temporaries get a
  leading underscore. WASM: plotly installs via `await micropip.install` cell.

## MILESTONES (stop after each; show the acceptance output)

M-A **Run the data pipelines** (in this order, venv + `pip install -r requirements.txt`,
  `.env` from `.env.example` with GROQ_API_KEY + SEC_USER_AGENT):
  1. `python pipelines/pipeline_1_financials.py` → accept: `data/financials.csv` has
     ~35 firm-year rows, Z-Scores plausible (AAPL > 5, TSLA varies), zones assigned.
  2. `python pipelines/pipeline_2_edgar.py` → accept: `data/risk_data.json` has 7
     tickers × 2 years, each >5,000 chars, snippet reads as risk prose (not TOC,
     not "Business" section, not HTML).
  3. `python pipelines/pipeline_3_llm.py` → accept: `data/sentiment.csv` per
     firm-year tone + `data/judge_eval.csv` with an agreement rate; report the rate.
  4. `python pipelines/pipeline_3b_wordclouds.py` → accept: 14 PNGs +
     `top_phrases.csv` + `engine_report.json` naming the engine used.
  Commit `data/` to main.

M-B **R cross-validation**: render `analysis_R/WK10_ResultTables_AF1204.Rmd`
  (RStudio or Codespace R). Accept: `data/regression_r.html` exists AND the printed
  R Model-4 ESGscore coefficient matches Python's 0.0026 to 4 decimals. Then update
  the site's ESG-tab wording from "should agree" to the confirmed fact, and embed
  or link the R table.

M-C **GPU clouds** (optional but 90-level): run the Colab notebook on T4; commit the
  regenerated `data/wordclouds/` + note GPU vs CPU timing on the Method tab.

M-D **Re-export & verify locally**: 7/7 tests, then the export command above;
  `python -m http.server --directory docs` and click through every tab — no dead
  widgets, no "pending" callouts left, tab selection survives widget clicks.

M-E **Migrate to the official fork** (`BayesUG-AI/repo[2-]AF1204-[username]`):
  copy `portfolio.py`, `pipelines/`, `data/`, `analysis_R/`, `notebooks_colab/`,
  `docs/`, `tests/`, `requirements.txt`, `.env.example`, `README.md`. Change the
  `RAW_BASE` line in `portfolio.py` to the fork's raw URL, re-export, push to
  **main**, enable Pages (main, /docs). Accept: the official
  `https://bayesug-ai.github.io/...` URL loads and every tab works — this exact
  view is what the video records.

M-F **Video prep**: 3-minute script, one segment per tab: (1) question + method map,
  (2) Z-Score dashboard interaction, (3) regression tables + R agreement line,
  (4) 2015→2025 clouds + LLM tone + judge agreement, (5) limitations & tool choices
  "for potential employers". Face bubble on throughout; filename
  `[StudentEmailAddress][StudentIDNumber][yourGitHubUsername].mp4`.

## HARD CONSTRAINTS

- Never print, commit, or paste the Groq key; `.env` stays gitignored.
- Never fabricate data — every number on the site must come from a pipeline artifact.
- Keep claims honest (the robustness caveats on the Overview tab stay).
- Prefer official APIs; no CAPTCHA bypass; keep the 0.5 s SEC sleeps.

FIRST ACTION: read `README.md` and `portfolio.py`, confirm the fork name and that
GROQ_API_KEY + SEC_USER_AGENT are set, then start M-A and show me pipeline 1's output.
