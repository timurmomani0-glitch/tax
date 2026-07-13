# Video script — 3-minute portfolio showcase (target 2:55)

Filename: `[StudentEmailAddress][StudentIDNumber][yourGitHubUsername].mp4`.
Face bubble on throughout. Before recording: open the live site, let it boot
(~20 s), click through every tab once so everything is warm.

## Segment 1 — Overview (0:00–0:35) · the hook
SHOW: page load → mouse over the four KPI tiles → the flow diagram.
SAY: "Hi, I'm Timur. For my portfolio I asked one question: do the risks
companies *talk about* in their filings match what their *numbers* say? I
answered it for the Magnificent 7 tech firms, with a pipeline covering every
week of this module. Everything on this page — these headline stats, every
chart — is computed by Python pipelines in my repo, and this diagram shows how
they fit: SEC filings feed an LLM tone analysis and word clouds, official SEC
data feeds Altman Z-Scores, and the course's ESG panel feeds a regression —
all landing in this marimo site, exported to WebAssembly on GitHub Pages."

## Segment 2 — Financial Health (0:35–1:10) · Weeks 2–4 + problem-solving
SHOW: press play on the Z-Score animation, toggle a firm in the multiselect,
drag the year-range slider on the q chart.
SAY: "First, financial health. This is the Week 2 Altman Z-Score, computed per
firm and year — all seven firms sit in the Safe zone, with Amazon closest to
the threshold. One thing I'm proud of: Yahoo Finance rate-limited my cloud
environment, so I rebuilt the five Altman inputs from the SEC's official XBRL
API instead and hand-verified Apple's figures against its actual filing.
Below, Tobin's q from the course data — you can see Meta's 2022 valuation
crash right here."

## Segment 3 — ESG & Valuation (1:10–1:50) · Weeks 6 + 10 + self-exploration
SHOW: scroll past the violin → stop on the stargazer table → point at Model 1
vs Model 4 → robustness table → green interpretation callout.
SAY: "Next, does ESG performance show up in valuation? I merged the
245-thousand-row ESG panel with accounting data using Polars, then estimated
four regressions. Here's the interesting part: the raw correlation is
*negative* — but add firm size, leverage, and industry-year fixed effects, and
ESG turns positive and significant. A classic omitted-variable lesson. To make
sure that wasn't a coding artifact, I re-estimated the model with a second
econometrics library — the coefficients match to six decimal places. And
honestly: under the alternative ESG provider the sign flips, so measurement
choice really matters."

## Segment 4 — Risk Language (1:50–2:30) · Weeks 7–9, the 70+ gate
SHOW: switch the firm dropdown, hover the 2015 vs 2025 clouds, point at the
"new in 2025" line, then the tone chart.
SAY: "Then the language itself. I pulled ten years of 10-K Risk Factors from
the SEC EDGAR API — my extractor handles real-world traps like split headings
and tables of contents. An LLM classifies each forward-looking sentence,
few-shot at temperature zero, and — my own extension — a *second, independent*
model re-judges a sample: 79% agreement. Every firm's tone is negative — risk
sections are structurally cautious — but *what* they worry about changed: for
Apple, 'government investigation' and 'supply chain' are new top phrases by
2025."

## Segment 5 — Method & close (2:30–2:55) · judgment, for employers
SHOW: Method tab, scroll slowly through Limitations → back to Overview.
SAY: "Finally, the engineering: a two-layer design keeps API keys and heavy
compute offline, so the deployed site is pure static WebAssembly. And the
limitations are stated openly — LLM labels aren't ground truth, Altman was
calibrated on manufacturers, and these are associations, not causation.
Everything is reproducible from the README. Thanks for watching."

## Delivery
- Rehearse twice with a timer; reads at ~2:50–2:55. If over, cut the Apple
  hand-verification sentence and the "traps" clause first.
- Move the mouse WHILE talking — the widgets are the proof of interactivity.
- Conversational delivery beats reading; the phrasing is spoken-style on purpose.
