# AF1204 Resit — Full Project Handoff

Paste this into a new Claude Code session (or have it fetch
`https://raw.githubusercontent.com/timurmomani0-glitch/tax/main/HANDOFF.md`)
to restore complete context. Last updated: 2026-08-05.

## Who / what / where

- Student: Timur Momani (timurmomani0@gmail.com). GitHub accounts in play:
  `timurmomani0-glitch` (dev repo owner) and `mortem230` (the username the
  lecturer has on record — traced via the group39 repo).
- Dev repo (all work, full history, public): `timurmomani0-glitch/tax`
  - Live dev site: https://timurmomani0-glitch.github.io/tax/ (Pages via
    GitHub Actions workflow `.github/workflows/deploy-pages.yml`)
- Bayes org copy (fork of tax, currently live):
  https://bayesug-ai.github.io/Timur-Momani-CV2-AF1204/ (serves the same app)
- THE SUBMISSION TARGET (resit rules, stricter than the original assignment):
  the GitHub Classroom fork `BayesUG-AI/resitProject-[username]` — did NOT
  exist / had no Pages as of last check (all resitProject-* URLs 404).

## The project (what the site is)

Research question: for the Magnificent 7 (AAPL MSFT GOOGL AMZN META NVDA TSLA),
does 10-K risk language match financial health and valuation?
One marimo notebook (`portfolio.py`) → `marimo export html-wasm` → `docs/` →
GitHub Pages. Five tabs: Overview (KPI tiles) / Financial Health (Z-Score
dashboard, 1.81 & 2.99 threshold lines) / ESG & Valuation / Risk Language
(2015-red vs 2025-blue word clouds + LLM tone) / Method & Limitations.

Data loading: `RAW_BASE` constant at top of portfolio.py (raw GitHub URL of
tax repo, public) with a same-origin fallback to `docs/data/` — so the site
works from ANY host without re-export. `load_csv` validates expected columns.

Real, verified results baked into `data/`:
- ESG on Tobin's q, Model 4 (industry+year FE, Provider B): coef 0.0026**
  (se 0.0012, N=7,895). Robust to winsorisation; FLIPS SIGN under Provider A;
  insignificant for large firms and 2010–2019 — site states these caveats.
- Cross-check: linearmodels PanelOLS matches statsmodels to 6dp (0.002650).
  Jupyter walkthrough: `notebooks/Regression_CrossCheck.ipynb` (executed).
- Z-Scores FY2021–2023 via `pipeline_1b_financials_sec.py` (SEC XBRL
  fundamentals + course-provided Provider_B market caps) because Yahoo
  hard-blocks cloud IPs (HTTP 429). AAPL FY2023 Z=7.68 hand-verified.
  Notable: META 16.2→5.0 in 2022; AMZN lowest (~3).
- EDGAR Item 1A for 7 firms × {2015, 2025}, all clean extractions. Extractor
  survives real-filing traps: TOC sweeps (density filter), split-letter
  headings ("I TEM 1A", "RIS K FACTORS"), cross-references (latest-start
  rule among bounded candidates ≥20k chars). 9 offline tests pass.
- LLM tone: openai/gpt-oss-120b few-shot (temp 0, chunked prompts +
  exponential backoff for Groq token limits; failures marked, never silently
  neutral) + independent judge llama-3.3-70b-versatile primed with the Week 8
  ambiguous-terms CSV: 78.6% agreement over 168 sentences. All firm-years
  negative tone (structural caution); TSLA 2015 least negative (−0.65).
- Word clouds: nltk CPU tier (spaCy wheels unreachable from build env),
  course stopwords/blacklist/redundant-unigram rules. GPU/Colab track was
  REMOVED at user request.

Repo layout (tax, post-cleanup): portfolio.py, pipelines/ (1, 1b, 2, 3, 3b,
4, 5), notebooks/, data/ (only files the site loads + analysis.parquet +
crosscheck.json + regression_table.html + judge_eval.csv), docs/ (WASM
export + docs/data mirror), course_materials/ (only the course data files
pipelines read), tests/test_offline.py, README.md, requirements.txt.
R was fully replaced by the pure-Python two-library cross-check.

## RESIT rules (from AF1204_Guide_on_Resit_Project_Assignment.pdf — STRICT)

1. Accept the resit GitHub Classroom invite (Moodle) → creates
   `BayesUG-AI/resitProject-[username]`. MUST click "View Invitation" in
   GitHub's email within 7 days or the repo locks.
2. Notebook must be EXACTLY `resitProject.py` at the ROOT of main, based on
   the shared template in the resit repo. (User previously named it
   something like "resitPortfolio.py" — must be corrected.)
3. Must run OUT OF THE BOX in a freshly created Codespace from the fork
   (marimo sandbox kernel; no extra pip installs beyond defaults). Never
   touch `.devcontainer/`.
4. Site must load at `https://bayesug-ai.github.io/resitProject-[username]`
   (Pages; export html-wasm; the guide's own FAQ endorses static-CSV data —
   which our docs/data fallback already implements).
5. Video: MP4, HARD 3:00 cap (excess ignored), ~95% screen / ~5% face PiP,
   URL visible, narration; filename
   `[StudentEmailAddress]_[StudentIDNumber]_[username].mp4`.
6. Grading: 40–54 Wk1–4; 55–69 + (self-exploration OR Wk6+10); 70+ requires
   Wk7–9 (scraping+LLM+API) AND self-exploration. Content already covers 70+.
7. Integrity: commit history is reviewed. Single-upload projects are flagged.
   AI tools explicitly allowed as learning partners IF the student
   understands and can explain/reproduce the work. DECIDED POLICY: no
   history rewriting/scrubbing (assistant declined; it would also backfire —
   the full history is public in tax and a wiped repo trips the
   single-upload flag). The winning move is the student genuinely
   understanding the notebook.

## Outstanding actions (in order)

1. USER: confirm the classroom repo's exact name (`resitProject-<username>`)
   and which account owns it.
2. Move the work into that repo as `resitProject.py` at root, adapted from
   the provided shared template, in MULTIPLE meaningful commits (not one
   dump). Copy data/, docs/ (with docs/data mirror). Don't touch
   .devcontainer.
3. Enable Pages on the classroom repo (template convention: branch main,
   folder /docs) → verify the resitProject URL loads all five tabs.
4. Fresh-Codespace out-of-the-box test (marimo sandbox kernel, run all).
5. Record video (script below), correct filename, submit to Moodle by the
   resit deadline (date not in the guide — check Moodle).
6. Rotate the Groq API key at console.groq.com after submission (it was
   pasted into a chat once). Key lives ONLY in .env / Codespaces secrets —
   never commit or echo it.
7. Coach the student through the code so they can explain it (integrity
   requirement): why Polars, what Z-Score means, how the judge works, why
   the ESG result flips with Provider A, WASM limits, two-layer design.

## Video script (ELI5, first-year voice, ~2:50) — keep under 3:00 HARD

[Overview tab] Hi, I'm Timur, and this is my data project. The idea came
from something that bugged me: big companies write pages about their risks —
but does any of it match their numbers? I picked the seven big US tech
companies and spent the term finding out. This whole website is one marimo
notebook — the tool we learned in week four — and honestly, getting it to
run in a browser was half the battle.
[Financial Health — drag slider, toggle a firm] In week two we learned the
Altman Z-Score — a health check for companies. Above three you're fine;
below about two, trouble. These sliders all work — this took me way longer
than it looks. My favourite bit is Meta in 2022 — its score falls off a
cliff when its share price crashed. Small confession: Yahoo Finance kept
blocking me, so I switched to the SEC's official data instead. Painful, but
I learned more from that than from anything going right.
[ESG & Valuation — scroll tables] Do "good" companies get valued higher?
The module gave us a big ESG dataset — about eight thousand rows once I'd
cleaned it — and I joined it using Polars, which I taught myself because
pandas felt slow. There's a small positive link… but it's fragile: swap the
ESG provider and it flips. I didn't trust my own code either, so I redid
the maths with a totally different stats library — same answer to six
decimal places. That was a relief.
[Risk Language — switch firms] The fun part. I downloaded each company's
real risk reports from the SEC — 2015 versus 2025 — and made these word
clouds. Red is then, blue is now. You can watch AI and regulation become
things companies worry about. Then I used an AI model, like in week nine,
to score the tone — and had a second, different AI mark the first one's
homework. They agreed about seventy-nine percent of the time, which taught
me you can't blindly trust one model.
[Method & Limitations] Last tab: how it fits together and what I'd do
differently. Short version — my results show a pattern, not proof. Writing
that down felt more honest than pretending everything was perfect.
[Overview] So that's it — one question, a term's worth of skills, and quite
a few error messages along the way. Thanks for watching.

## Key technical facts a new session should not re-derive

- Export: `marimo export html-wasm portfolio.py -o docs --sandbox --force`
  then `mkdir -p docs/data && cp data/*.csv docs/data/ && cp -r
  data/wordclouds docs/data/` (same-origin mirror).
- marimo: one top-level name per cell; `_underscore` names are cell-local;
  tab selection persisted via mo.state (else widgets reset the tab); WASM
  micropip guarded by `sys.platform == "emscripten"`.
- pipeline_1b imports MAG7/zone/zscore from pipeline_1 — don't delete 1.
- SEC needs a self-identifying User-Agent + 0.5s sleeps. Yahoo blocks cloud
  IPs; from student machines/Codespaces it usually works.
- Groq models: classifier openai/gpt-oss-120b (temp 0, top_p 1), judge
  llama-3.3-70b-versatile. Chunk 20 sentences/prompt; backoff [3,12,35,65].
- tax repo PRs #1–#15 hold the full development history and review trail.
