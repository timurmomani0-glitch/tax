# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.19.10",
#     "pandas>=2.2",
#     "plotly>=6.0",
# ]
# ///

# AF1204 Data-Literacy Portfolio — Timur Momani
#
# Layer B (deployed): this marimo notebook is exported to WASM and served on
# GitHub Pages. It reads ONLY pre-computed artifacts produced by the Layer A
# pipelines (pipelines/pipeline_1..5), loaded over raw GitHub URLs with a
# same-origin fallback — the remote-URL approach the Week 4 course notebook
# uses, because local file loading does not survive GitHub Pages' compression
# of bundled assets. No API keys, no live scraping, no GPU in this layer.
#
# Chart colors are a validated categorical palette (CVD-checked): firms keep
# fixed hues, 2015/2025 keep a red/blue pair matching the word clouds, and
# Z-Score zones use reserved status colors.

import marimo

__generated_with = "0.19.11"
app = marimo.App(width="medium")

with app.setup:
    import os

    import marimo as mo
    import pandas as pd

    # Overridable for local runs (PORTFOLIO_DATA_BASE=data/); in the deployed WASM
    # app os.environ is empty, so the raw-GitHub URL is always used there.
    RAW_BASE = os.environ.get(
        "PORTFOLIO_DATA_BASE",
        "https://raw.githubusercontent.com/timurmomani0-glitch/tax/main/data/",
    )
    DISTRESS_Z, SAFE_Z = 1.81, 2.99
    MAG7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

    # Validated palette (dataviz method): fixed slot order, never cycled.
    FIRM_COLORS = dict(zip(MAG7, [
        "#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948",
        "#e87ba4",
    ]))
    C_2015, C_2025 = "#e34948", "#2a78d6"          # matches Reds/Blues clouds
    ZONE_COLORS = {"Safe": "#0ca30c", "Grey": "#898781", "Distress": "#d03b3b"}
    ACCENT = "#2a78d6"


@app.cell
async def _():
    # WASM runtime needs plotly installed via micropip (course Week 4 pattern);
    # locally (Codespaces) plotly comes from the venv, so only import micropip
    # when actually running in the browser (pyodide reports sys.platform as
    # "emscripten"), which also keeps the editor's import linter quiet.
    import sys
    if sys.platform == "emscripten":
        import micropip  # type: ignore[import-not-found]  # noqa: F401
        await micropip.install("plotly")
    import plotly.express as px
    return (px,)


@app.function
def load_csv(name, required=()):
    """Fetch one Layer-A artifact; None when unavailable or malformed.

    Tries the raw-GitHub URL first (course Week 4 pattern), then a same-origin
    copy under the deployed site's own data/ folder. Validates the expected
    columns because a 404/rate-limit TEXT response still parses as a CSV — a
    junk frame must degrade to the "pending" callout, not crash cells
    downstream (learned from a live 'DataFrame has no attribute' incident).
    """
    bases = [RAW_BASE]
    try:
        bases.append(str(mo.notebook_location() / "data") + "/")
    except Exception:
        pass
    for base in bases:
        try:
            df = pd.read_csv(base + name)
        except Exception:
            continue
        if all(col in df.columns for col in required):
            return df
    return None


@app.function
def load_text(name, must_contain=""):
    """Fetch a small text/HTML/JSON artifact with the same fallback chain."""
    import urllib.request
    bases = [RAW_BASE]
    try:
        bases.append(str(mo.notebook_location() / "data") + "/")
    except Exception:
        pass
    for base in bases:
        try:
            if str(base).startswith("http"):
                with urllib.request.urlopen(base + name) as resp:
                    text = resp.read().decode("utf-8", "replace")
            else:  # local run: the base is a filesystem path
                with open(str(base) + name, encoding="utf-8") as f:
                    text = f.read()
            if must_contain in text:
                return text
        except Exception:
            continue
    return None


@app.function
def pending(msg):
    return mo.callout(mo.md(f"⏳ **Artifact pending.** {msg}"), kind="warn")


@app.function
def polish(fig):
    """House chart style: system sans, recessive hairline grid, quiet chrome."""
    fig.update_layout(
        template="plotly_white",
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif',
                  size=14, color="#0b0b0b"),
        title_font=dict(size=17),
        paper_bgcolor="#fcfcfb",
        plot_bgcolor="#fcfcfb",
        legend=dict(borderwidth=0),
    )
    fig.update_xaxes(gridcolor="#e1e0d9", zerolinecolor="#c3c2b7",
                     linecolor="#c3c2b7")
    fig.update_yaxes(gridcolor="#e1e0d9", zerolinecolor="#c3c2b7",
                     linecolor="#c3c2b7")
    return fig


@app.cell
def _():
    df_fin = load_csv("financials.csv", required=("Ticker", "Year", "Z_Score", "Zone"))
    df_mag7 = load_csv("mag7_provided.csv", required=("instrument", "Year", "q", "Leverage"))
    df_reg = load_csv("site_regression.csv", required=("group", "model", "term", "coef"))
    df_desc = load_csv("site_descriptive.csv", required=("variable",))
    df_corr = load_csv("site_correlation.csv", required=("pair",))
    df_panel = load_csv("site_panel_b.csv", required=("sector", "q", "ESGscore"))
    df_sent = load_csv("sentiment.csv", required=("ticker", "year", "mean_score"))
    df_phrases = load_csv("wordclouds/top_phrases.csv",
                          required=("ticker", "year", "phrase", "count"))
    df_judge = load_csv("judge_eval.csv", required=("agree", "classifier_label"))
    return (df_corr, df_desc, df_fin, df_judge, df_mag7, df_panel, df_phrases,
            df_reg, df_sent)


@app.cell
def _(df_judge, df_panel, df_reg, df_sent):
    # Headline number + KPI tiles, all pulled live from the pipeline artifacts
    _m4 = None
    if df_reg is not None:
        _rows = df_reg[(df_reg.model == "Model 4") & (df_reg.term == "ESGscore")
                       & (df_reg.group == "main")]
        if len(_rows):
            _m4 = _rows.iloc[0]
    headline = (
        f"ESG score coefficient on Tobin's q: **{_m4.coef}{_m4.stars}** "
        f"(se {_m4.se}, N = {_m4.n:,}, industry + year fixed effects)"
        if _m4 is not None else "regression artifact pending"
    )

    _tiles = []
    if _m4 is not None:
        _tiles.append(mo.stat(value=f"+{_m4.coef}", label="ESG → Tobin's q",
                              caption=f"Model 4{_m4.stars} · N = {_m4.n:,}",
                              bordered=True))
    if df_panel is not None:
        _tiles.append(mo.stat(value=f"{len(df_panel):,}", label="Firm-years analysed",
                              caption="provided ESG × accounting panel",
                              bordered=True))
    if df_sent is not None:
        _tiles.append(mo.stat(value=f"{df_sent.mean_score.mean():+.2f}",
                              label="Avg. 10-K tone",
                              caption="forward-looking, −1 … +1",
                              bordered=True))
    if df_judge is not None:
        _agree = df_judge.dropna(subset=["agree"])
        _rate = (_agree.agree.astype(str).str.lower() == "true").mean()
        judge_rate_txt = f"{_rate:.0%} over {len(_agree)} sentences"
        _tiles.append(mo.stat(value=f"{_rate:.0%}", label="AI-judge agreement",
                              caption=f"{len(_agree)} sentences re-judged",
                              bordered=True))
    else:
        judge_rate_txt = "see data/judge_eval.csv"
    kpi_row = (mo.hstack(_tiles, widths="equal", gap=1)
               if _tiles else mo.md(""))
    return headline, judge_rate_txt, kpi_row


@app.cell
def _(headline, kpi_row):
    tab_overview = mo.vstack([
        mo.md(
            f"""
            ## 🔍 Research question

            > **For large US listed firms, does the risk language and tone a company
            > discloses in its filings align with its financial health and market
            > valuation?**

            **Universe:** the "Magnificent 7" ({", ".join(MAG7)}) — large US firms
            present in both the financial and the disclosure-text layers.
            """
        ),
        kpi_row,
        mo.md("### How the pieces fit"),
        mo.mermaid(
            """
            flowchart LR
                A["SEC EDGAR<br>10-K Item 1A (Wk 7)"] --> B["Groq LLM tone<br>+ AI judge (Wk 8–9)"]
                A --> C["n-gram word clouds<br>(Wk 10)"]
                D["SEC XBRL +<br>course market caps"] --> E["Altman Z-Scores<br>(Wk 2–3)"]
                F["Provided ESG +<br>accounting data (Wk 6)"] --> G["Polars merge<br>(Wk 10)"]
                G --> H["Models 1–4, statsmodels<br>× linearmodels check"]
                B --> I[("data/ artifacts")]
                C --> I
                E --> I
                H --> I
                I --> J["This site<br>marimo → WASM → Pages (Wk 4)"]
            """
        ),
        mo.md(
            f"""
            | Layer | Week(s) | Tooling | Output |
            |---|---|---|---|
            | Financial health — Altman Z-Score per firm-year | 2–3 | SEC XBRL + provided market caps (yfinance fallback) | `financials.csv` |
            | Valuation & ESG — Tobin's q regressions | 6 | **Polars** + statsmodels, cross-validated with **linearmodels** | `site_regression.csv`, `regression_table.html` |
            | Disclosed risk & tone — 10-K Item 1A text | 7 | SEC EDGAR official API | `risk_data.json` |
            | LLM sentiment + independent AI judge | 8–9 | Groq (`openai/gpt-oss-120b` + `llama-3.3-70b-versatile`) | `sentiment.csv`, `judge_eval.csv` |
            | Risk-language shift 2015 → 2025 | 10 | spaCy/nltk n-grams | word clouds |

            ### Headline finding

            {headline}

            Small in economic terms; significant and robust to winsorisation — but it
            **flips sign under the alternative ESG provider** and loses significance
            among large firms and in 2010–2019. Provider choice and sample matter;
            see the robustness table on the **ESG & Valuation** tab.
            """
        ),
    ])
    return (tab_overview,)


@app.cell
def _(df_fin):
    _firms = sorted(df_fin.Ticker.unique().tolist()) if df_fin is not None else MAG7
    firm_select = mo.ui.multiselect(options=_firms, value=_firms,
                                    label="**Firms:**")
    return (firm_select,)


@app.cell
def _(df_mag7):
    _years = sorted(df_mag7.Year.unique().tolist()) if df_mag7 is not None else [2005, 2023]
    year_range = mo.ui.range_slider(start=int(min(_years)), stop=int(max(_years)),
                                    step=1, value=[2010, int(max(_years))],
                                    label="**Year range (provided data):**")
    return (year_range,)


@app.cell
def _(df_fin, df_mag7, firm_select, px, year_range):
    _parts = [mo.md("## 🏦 Financial health of the Magnificent 7")]

    if df_fin is not None:
        _latest = df_fin[df_fin.Year == df_fin.Year.max()]
        _parts.append(mo.hstack([
            mo.stat(value=str(int((_latest.Zone == "Safe").sum())) + " / " + str(len(_latest)),
                    label=f"Firms in the Safe zone, FY{int(df_fin.Year.max())}",
                    caption="Altman Z > 2.99", bordered=True),
            mo.stat(value=f"{_latest.Z_Score.min():.1f}",
                    label="Lowest Z-Score",
                    caption=_latest.loc[_latest.Z_Score.idxmin(), "Ticker"],
                    bordered=True),
            mo.stat(value=f"{_latest.Z_Score.max():.0f}",
                    label="Highest Z-Score",
                    caption=_latest.loc[_latest.Z_Score.idxmax(), "Ticker"],
                    bordered=True),
        ], widths="equal", gap=1))

        _f = df_fin[df_fin.Ticker.isin(firm_select.value)]
        _src = (df_fin["Source"].iloc[0] if "Source" in df_fin.columns
                else "yfinance")
        _fig_z = px.bar(
            _f, x="Ticker", y="Z_Score", color="Zone", animation_frame="Year",
            color_discrete_map=ZONE_COLORS,
            title=f"Altman Z-Score by firm and fiscal year<br><sup>Week 2 formula; data: {_src}</sup>",
            height=480,
        )
        _fig_z.add_hline(y=DISTRESS_Z, line_dash="dash", line_color="#d03b3b",
                         annotation_text="Distress threshold (1.81)",
                         annotation_position="bottom right",
                         annotation_font_color="#d03b3b")
        _fig_z.add_hline(y=SAFE_Z, line_dash="dash", line_color="#0ca30c",
                         annotation_text="Safe threshold (2.99)",
                         annotation_position="top left",
                         annotation_font_color="#0ca30c")
        _parts += [firm_select, mo.ui.plotly(polish(_fig_z))]
    else:
        _parts.append(pending(
            "Z-Scores appear after `pipelines/pipeline_1b_financials_sec.py` "
            "(or the yfinance pipeline) runs."))

    if df_mag7 is not None:
        _m = df_mag7[(df_mag7.Year >= year_range.value[0])
                     & (df_mag7.Year <= year_range.value[1])]
        _fig_q = px.line(
            _m, x="Year", y="q", color="instrument", markers=True,
            color_discrete_map=FIRM_COLORS,
            title="Tobin's q — Magnificent 7, from the course-provided data (Week 6)",
            labels={"q": "Tobin's q", "instrument": "Firm"},
            height=450,
        )
        _fig_lev = px.box(
            _m, x="instrument", y="Leverage", color="instrument",
            color_discrete_map=FIRM_COLORS,
            title="Leverage distribution per firm (box = IQR, Week 3 outlier lens)",
            labels={"instrument": "Firm"},
            height=400,
        )
        _fig_lev.update_layout(showlegend=False)
        _parts += [year_range, mo.ui.plotly(polish(_fig_q)),
                   mo.ui.plotly(polish(_fig_lev)),
                   mo.callout(mo.md(
                       "**Takeaway.** A q above 1 means the market values the firm "
                       "above its book assets; the Mag 7 sit far above 1 for most "
                       "of the sample — intangible-heavy business models. All 7 "
                       "stay in the Altman Safe zone throughout FY2021–2023; "
                       "Amazon runs closest to the thresholds, Meta's 2022 "
                       "valuation crash is clearly visible."), kind="info")]
    else:
        _parts.append(pending("Mag-7 valuation series appears after "
                              "`pipelines/pipeline_4_merge.py` runs."))
    tab_financial = mo.vstack(_parts)
    return (tab_financial,)


@app.cell
def _(df_panel):
    provider_note = mo.md(
        "_Main sample: **Provider B** ESG scores (as in the course material); "
        "Provider A is the robustness alternative._")
    _sectors = (sorted(df_panel.sector.dropna().unique().tolist())
                if df_panel is not None else [])
    sector_select = mo.ui.multiselect(options=_sectors, value=_sectors,
                                      label="**Sectors (distribution plot):**")
    return provider_note, sector_select


@app.cell
def _(df_corr, df_desc, df_panel, df_reg, provider_note, px, sector_select):
    _parts = [mo.md("## 🌱 ESG and firm valuation (provided data, Weeks 6 + 10)")]

    if df_desc is not None:
        _parts += [mo.md("### Descriptive statistics (Provider B)"),
                   mo.ui.table(df_desc, selection=None)]
    if df_corr is not None:
        _parts += [mo.md("### Pairwise correlations (stars: * p<0.1, ** p<0.05, *** p<0.01)"),
                   mo.ui.table(df_corr.fillna(""), selection=None)]

    if df_panel is not None:
        _p = df_panel[df_panel.sector.isin(sector_select.value)].copy()
        # Full sector names ("Professional, Scientific, and Technical Services")
        # overflow the axis — plot with truncated labels, keep full names in
        # the widget and hover.
        _p["sector_label"] = _p["sector"].where(
            _p["sector"].str.len() <= 16, _p["sector"].str.slice(0, 15) + "…")
        _fig_v = px.violin(
            _p, x="sector_label", y="q", box=True, points=False,
            hover_name="sector",
            color_discrete_sequence=[ACCENT],
            title="Tobin's q distribution by sector (violin + box, Week 3)",
            labels={"sector_label": "sector"},
            height=500,
        )
        _fig_v.update_yaxes(range=[0, 10])  # zoom past extreme outliers
        _fig_v.update_xaxes(tickangle=40, automargin=True,
                            tickfont=dict(size=12))
        _fig_v.update_layout(margin=dict(b=120))
        _fig_sc = px.scatter(
            _p.sample(min(len(_p), 2500), random_state=7),
            x="ESGscore", y="q", opacity=0.45, hover_data=["sector"],
            color_discrete_sequence=[ACCENT],
            title="ESG score vs Tobin's q (sample of firm-years)",
            height=450,
        )
        _fig_sc.update_yaxes(range=[0, 12])
        _parts += [sector_select, mo.ui.plotly(polish(_fig_v)),
                   mo.ui.plotly(polish(_fig_sc))]

    if df_reg is not None:
        _parts += [mo.md("### Regression: q ~ ESGscore + controls "
                         "(Python / statsmodels)"), provider_note]
        _star = load_text("regression_table.html", must_contain="<table")
        if _star:
            _parts.append(mo.Html(
                '<div style="overflow-x:auto; font-size:14px; '
                'font-family:system-ui,sans-serif">' + _star + "</div>"))
        else:
            _main = df_reg[df_reg.group == "main"].copy()
            _main["estimate"] = (_main.coef.astype(str) + _main.stars
                                 + " (" + _main.se.astype(str) + ")")
            _wide = _main.pivot_table(index="term", columns="model",
                                      values="estimate",
                                      aggfunc="first").reset_index().fillna("–")
            _parts.append(mo.ui.table(_wide, selection=None))
        _rob = df_reg[(df_reg.group == "robustness") & (df_reg.term == "ESGscore")][
            ["model", "coef", "se", "stars", "n", "r2"]].fillna("")
        _parts += [
            mo.md("### Robustness — ESGscore coefficient across samples "
                  "(incl. winsorised 1/99%)"),
            mo.ui.table(_rob, selection=None),
            mo.md(
                "**Cross-tool validation (self-exploration) — confirmed:** the same "
                "Model 4 re-estimated with an independent econometrics library, "
                "**linearmodels `PanelOLS`** (fixed effects absorbed by the within "
                "estimator instead of statsmodels' dummy variables), reproduces every "
                "coefficient to 6 decimal places — ESGscore = **0.002650** in both. "
                "See `notebooks/Regression_CrossCheck.ipynb` (Jupyter, runs in "
                "Codespaces)."),
            mo.callout(mo.md(
                "**Interpretation.** Model 1's raw association is *negative*, but "
                "once firm size, leverage and industry/year fixed effects are added "
                "(Models 3–4) the ESG coefficient turns **positive and significant** "
                "— higher-rated firms trade at a modest valuation premium *within* "
                "industry-year. The sign flip is a classic omitted-variable lesson: "
                "big, mature firms have better ESG coverage *and* lower q. The "
                "robustness row for Provider A flips the sign — ESG measurement "
                "choice genuinely matters."), kind="success"),
        ]
    else:
        _parts.append(pending("Run `pipelines/pipeline_4_merge.py`."))
    tab_esg = mo.vstack(_parts)
    return (tab_esg,)


@app.cell
def _(df_phrases):
    _opts = sorted(df_phrases.ticker.unique().tolist()) if df_phrases is not None else MAG7
    cloud_firm = mo.ui.dropdown(options=_opts, value=_opts[0], label="**Firm:**")
    return (cloud_firm,)


@app.cell
def _(cloud_firm, df_phrases, df_sent, judge_rate_txt, px):
    _parts = [mo.md("## 📰 Risk language, 2015 → 2025 (Weeks 7–10)")]

    if df_phrases is not None:
        _t = cloud_firm.value
        _imgs = [
            mo.vstack([
                mo.md(f"**{_t} — {_yr}**"),
                mo.image(src=f"{RAW_BASE}wordclouds/{_t}_{_yr}.png", width=430),
            ])
            for _yr in (2015, 2025)
        ]
        _tp = df_phrases[df_phrases.ticker == _t].copy()
        _tp["year"] = _tp["year"].astype(str)  # categorical colors, not a gradient
        _fig_ph = px.bar(
            _tp.sort_values("count").groupby("year").tail(12),
            x="count", y="phrase", color="year", orientation="h",
            facet_col="year", title=f"Top risk phrases — {_t}",
            color_discrete_map={"2015": C_2015, "2025": C_2025},
            height=520,
        )
        _fig_ph.update_yaxes(matches=None, showticklabels=True,
                             automargin=True, tickfont=dict(size=12))
        _fig_ph.update_layout(margin=dict(l=210))

        # Data-driven "what's new" line: 2025 top phrases absent from 2015's list
        _p15 = set(_tp[_tp.year == "2015"].phrase)
        _new = [p for p in _tp[_tp.year == "2025"]
                .sort_values("count", ascending=False).phrase
                if p not in _p15][:6]
        _new_md = (mo.md(f"**New in {_t}'s 2025 top risk language:** "
                         + " · ".join(f"`{p}`" for p in _new))
                   if _new else mo.md(""))
        _parts += [cloud_firm, mo.hstack(_imgs, justify="start"),
                   mo.ui.plotly(polish(_fig_ph)), _new_md]
    else:
        _parts.append(pending(
            "Word clouds appear after `pipeline_2_edgar.py` + "
            "`pipeline_3b_wordclouds.py` run (needs SEC EDGAR access)."))

    if df_sent is not None:
        _ds = df_sent.copy()
        _ds["year"] = _ds["year"].astype(str)  # categorical colors, not a gradient
        _fig_tone = px.bar(
            _ds, x="ticker", y="mean_score", color="year", barmode="group",
            title="LLM forward-looking tone per firm (−1 cautious … +1 optimistic)",
            labels={"mean_score": "Mean sentiment score"},
            color_discrete_map={"2015": C_2015, "2025": C_2025},
            height=430,
        )
        _fig_tone.add_hline(y=0.25, line_dash="dot", line_color="#898781",
                            annotation_text="positive threshold")
        _fig_tone.add_hline(y=-0.25, line_dash="dot", line_color="#898781",
                            annotation_text="negative threshold")
        _parts += [
            mo.ui.plotly(polish(_fig_tone)),
            mo.callout(mo.md(
                f"**Takeaway.** Forward-looking sentences inside Item 1A are "
                f"structurally cautious — every firm-year scores negative, and the "
                f"language shifts from product/IT risks in 2015 toward supply "
                f"chains, regulation and AI by 2025. Classifier: "
                f"`openai/gpt-oss-120b` (few-shot, temperature 0); an independent "
                f"`llama-3.3-70b-versatile` judge agrees on **{judge_rate_txt}** "
                f"(full log in `data/judge_eval.csv`)."), kind="info"),
        ]
    else:
        _parts.append(pending(
            "Tone scores appear after `pipeline_3_llm.py` runs (needs a Groq key)."))
    tab_risk = mo.vstack(_parts)
    return (tab_risk,)


@app.cell
def _():
    import json as _json_mod
    _engine_txt = load_text("wordclouds/engine_report.json", must_contain="engine")
    _engine = ""
    if _engine_txt:
        try:
            _engine = _json_mod.loads(_engine_txt).get("engine", "")
        except Exception:
            _engine = ""
    _engine_line = (f"- **NLP engine actually used:** {_engine} — the pipeline "
                    "auto-upgrades to a spaCy transformer model when one is "
                    "available.\n" if _engine else "")
    tab_method = mo.vstack([
        mo.md(
            f"""
            ## 🛠️ Method, choices & limitations

            ### Two-layer architecture
            **Layer A (offline pipelines, this repo, never deployed)** downloads and
            computes everything that needs the network, secrets or heavy compute, and
            writes small artifacts to `data/`. **Layer B (this page)** is a marimo
            notebook exported to WASM on GitHub Pages: static, no server, no secrets —
            it only reads the Layer-A artifacts over raw GitHub URLs with a
            same-origin fallback, and every load is validated before use.

            ### Why these tools
            - **EDGAR over scraping corporate sites** — an official API with no bot
              detection; the SEC only requires a self-identifying `User-Agent`
              (and 0.5 s politeness delays between requests). The extractor handles
              two real-filing traps found during the build: iXBRL split-letter
              headings (`I TEM 1A`) and tables of contents that sweep the Business
              section into a first-match extraction.
            - **SEC XBRL for the Z-Score inputs** — when Yahoo rate-limited the
              build environment, the five Altman inputs were rebuilt from the SEC's
              official `companyfacts` API plus the course-provided market caps
              (hand-verified against Apple's FY2023 filing); the course-faithful
              yfinance pipeline remains for reproduction.
            - **Polars for the merge (Week 10 self-exploration)** — the ESG file is
              245k rows × 2 providers; Polars' lazy engine joins and filters it in one
              optimised pass and writes Parquet.
            - **Two-library cross-validation (self-exploration)** — Model 4
              re-estimated with linearmodels' within estimator alongside
              statsmodels' dummy-variable approach (`notebooks/
              Regression_CrossCheck.ipynb`); the coefficients match to 6 decimals.
              The publication table uses the Python `stargazer` package — the same
              table family as the course's Week 10 material.
            - **Two LLM families (self-exploration)** — `openai/gpt-oss-120b`
              classifies (course Week 9 settings: few-shot, temperature 0, JSON-only
              contract, chunked prompts with exponential backoff); `llama-3.3-70b-versatile`
              independently re-judges a sample, primed with the Week 8 list of
              ambiguous finance terms.
            {_engine_line}
            ### Limitations & critical evaluation
            - **LLM accuracy** — sentiment labels are model outputs, not ground truth.
              Deterministic settings reduce variance, not bias; the judge agreement
              rate quantifies (dis)agreement but two models can share blind spots.
              Sentences are capped per firm-year for API cost; failed API calls are
              marked as failures, never silently recorded as neutral.
            - **Z-Score** — Altman (1968) was calibrated on manufacturers; for
              asset-light tech firms the thresholds are indicative, not diagnostic.
            - **ESG data** — provider scores disagree (hence the Provider A/B
              robustness column); coverage is sparse pre-2005.
            - **Causality** — the q regressions are associations with fixed effects,
              not causal estimates; sentiment enters descriptively (7 firms is far
              too few for a firm-level tone regression).

            ### Reproduce
            `README.md` documents the exact pipeline order, the WASM export command
            (`marimo export html-wasm portfolio.py -o docs --sandbox --force`) and
            the GitHub Pages deployment (a GitHub Action publishes `docs/` on every
            push to `main`).
            """
        ),
    ])
    return (tab_method,)


@app.cell
def _():
    # Widget interactions re-create the tabs element (marimo re-runs the consuming
    # cells); without external state the recreated element would snap back to the
    # first tab on every slider/dropdown change.
    get_tab, set_tab = mo.state("🔍 Overview")
    return get_tab, set_tab


@app.cell
def _(get_tab, set_tab, tab_esg, tab_financial, tab_method, tab_overview, tab_risk):
    app_tabs = mo.ui.tabs(
        {
            "🔍 Overview": tab_overview,
            "🏦 Financial Health": tab_financial,
            "🌱 ESG & Valuation": tab_esg,
            "📰 Risk Language": tab_risk,
            "🛠️ Method & Limitations": tab_method,
        },
        value=get_tab(),
        on_change=set_tab,
    )
    return (app_tabs,)


@app.cell
def _(app_tabs):
    mo.vstack([
        mo.md(
            """
            # **Do firms disclose what their numbers say?**
            ### Risk language, tone and financial health of the Magnificent 7
            _AF1204 data-literacy portfolio · Timur Momani ·
            [code & pipelines on GitHub](https://github.com/timurmomani0-glitch/tax)_

            ---
            """
        ),
        app_tabs,
        mo.md(
            """
            ---
            <small>Built with marimo (WASM) · data: SEC EDGAR & XBRL, course-provided
            ESG/accounting panel, Groq LLM API · every figure on this page is
            generated by a pipeline in the repo — reproduction steps in the
            README.</small>
            """
        ),
    ])
    return


if __name__ == "__main__":
    app.run()
