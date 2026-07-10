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
# pipelines (pipelines/pipeline_1..4), loaded over raw GitHub URLs — the same
# remote-raw-URL approach the Week 4 course notebook uses, because local file
# loading does not survive GitHub Pages' compression of bundled assets.
# No API keys, no live scraping, no GPU in this layer.

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


@app.cell
async def _():
    # WASM runtime needs plotly installed via micropip (course Week 4 pattern);
    # in a local `marimo run/edit` session micropip does not exist, so guard it.
    try:
        import micropip
        await micropip.install("plotly")
    except Exception:
        pass  # outside WASM plotly comes from the local environment instead
    import plotly.express as px
    return (px,)


@app.function
def load_csv(name):
    """Fetch one Layer-A artifact; None when the pipeline hasn't run yet."""
    try:
        return pd.read_csv(RAW_BASE + name)
    except Exception:
        return None


@app.function
def pending(msg):
    return mo.callout(mo.md(f"⏳ **Artifact pending.** {msg}"), kind="warn")


@app.cell
def _():
    df_fin = load_csv("financials.csv")
    df_mag7 = load_csv("mag7_provided.csv")
    df_reg = load_csv("site_regression.csv")
    df_desc = load_csv("site_descriptive.csv")
    df_corr = load_csv("site_correlation.csv")
    df_panel = load_csv("site_panel_b.csv")
    df_sent = load_csv("sentiment.csv")
    df_phrases = load_csv("wordclouds/top_phrases.csv")
    return df_corr, df_desc, df_fin, df_mag7, df_panel, df_phrases, df_reg, df_sent


@app.cell
def _(df_reg):
    # Headline number for the Overview tab, pulled live from the regression artifact
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
    return (headline,)


@app.cell
def _(headline):
    tab_overview = mo.vstack([
        mo.md(
            f"""
            ## 🔍 Research question

            > **For large US listed firms, does the risk language and tone a company
            > discloses in its filings align with its financial health and market
            > valuation?**

            **Universe:** the "Magnificent 7" ({", ".join(MAG7)}) — large US firms
            present in both the financial and the disclosure-text layers.

            ### Method at a glance

            | Layer | Week(s) | Tooling | Output |
            |---|---|---|---|
            | Financial health — Altman Z-Score per firm-year | 2–3 | `yfinance`, pandas | `financials.csv` |
            | Valuation & ESG — Tobin's q regressions on provided data | 6 | Polars + statsmodels, cross-validated in **R/stargazer** | `site_regression.csv`, `regression_r.html` |
            | Disclosed risk & tone — 10-K Item 1A text | 7 | SEC EDGAR official API | `risk_data.json` |
            | LLM sentiment + independent AI judge | 8–9 | Groq (`openai/gpt-oss-120b` + `llama-3.3-70b-versatile`) | `sentiment.csv`, `judge_eval.csv` |
            | Risk-language shift 2015 → 2025 | 10 | spaCy (GPU/CPU) + nltk n-grams | word clouds |

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
def _(df_fin, df_mag7, firm_select, go, px, year_range):
    _parts = [mo.md("## 🏦 Financial health of the Magnificent 7")]

    if df_fin is not None:
        _f = df_fin[df_fin.Ticker.isin(firm_select.value)]
        _src = (df_fin["Source"].iloc[0] if "Source" in df_fin.columns
                else "yfinance")
        _fig_z = px.bar(
            _f, x="Ticker", y="Z_Score", color="Zone", animation_frame="Year",
            color_discrete_map={"Safe": "green", "Grey": "grey", "Distress": "red"},
            title=f"Altman Z-Score by firm and fiscal year<br><sup>Week 2 formula; data: {_src}</sup>",
            template="presentation", height=480,
        )
        _fig_z.add_hline(y=DISTRESS_Z, line_dash="dash", line_color="red",
                         annotation_text="Distress threshold (1.81)")
        _fig_z.add_hline(y=SAFE_Z, line_dash="dash", line_color="green",
                         annotation_text="Safe threshold (2.99)")
        _parts += [firm_select, mo.ui.plotly(_fig_z)]
    else:
        _parts.append(pending(
            "Z-Scores appear after `pipelines/pipeline_1_financials.py` runs "
            "(needs Yahoo Finance access)."))

    if df_mag7 is not None:
        _m = df_mag7[(df_mag7.Year >= year_range.value[0])
                     & (df_mag7.Year <= year_range.value[1])]
        _fig_q = px.line(
            _m, x="Year", y="q", color="instrument", markers=True,
            title="Tobin's q — Magnificent 7, from the course-provided data (Week 6)",
            labels={"q": "Tobin's q", "instrument": "Firm"},
            template="presentation", height=450,
        )
        _fig_lev = px.box(
            _m, x="instrument", y="Leverage", color="instrument",
            title="Leverage distribution per firm (box = IQR, Week 3 outlier lens)",
            template="presentation", height=400,
        )
        _parts += [year_range, mo.ui.plotly(_fig_q), mo.ui.plotly(_fig_lev),
                   mo.md("_A q above 1 means the market values the firm above its "
                         "book assets; the Mag 7 sit far above 1 for most of the "
                         "sample — intangible-heavy business models._")]
    else:
        _parts.append(pending("Mag-7 valuation series appears after "
                              "`pipelines/pipeline_4_merge.py` runs."))
    tab_financial = mo.vstack(_parts)
    return (tab_financial,)


@app.cell
def _(df_panel):
    provider_note = mo.md(
        "_Main sample: **Provider B** ESG scores (as in the course Rmd); "
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
                   mo.ui.table(df_corr, selection=None)]

    if df_panel is not None:
        _p = df_panel[df_panel.sector.isin(sector_select.value)]
        _fig_v = px.violin(
            _p, x="sector", y="q", box=True, points=False,
            title="Tobin's q distribution by sector (violin + box, Week 3)",
            template="presentation", height=450,
        )
        _fig_v.update_yaxes(range=[0, 10])  # zoom past extreme outliers
        _fig_sc = px.scatter(
            _p.sample(min(len(_p), 2500), random_state=7),
            x="ESGscore", y="q", color="sector", opacity=0.55,
            title="ESG score vs Tobin's q (sample of firm-years)",
            template="presentation", height=450,
        )
        _fig_sc.update_yaxes(range=[0, 12])
        _parts += [sector_select, mo.ui.plotly(_fig_v), mo.ui.plotly(_fig_sc)]

    if df_reg is not None:
        _main = df_reg[df_reg.group == "main"].copy()
        _main["estimate"] = _main.coef.astype(str) + _main.stars + " (" + _main.se.astype(str) + ")"
        _wide = _main.pivot_table(index="term", columns="model", values="estimate",
                                  aggfunc="first").reset_index()
        _meta = _main.drop_duplicates("model")[["model", "n", "r2", "industry_fe", "year_fe"]]
        _rob = df_reg[(df_reg.group == "robustness") & (df_reg.term == "ESGscore")][
            ["model", "coef", "se", "stars", "n", "r2"]]
        _parts += [
            mo.md("### Regression: q ~ ESGscore + controls (Python / statsmodels)"),
            provider_note,
            mo.ui.table(_wide, selection=None),
            mo.ui.table(_meta, selection=None),
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
                "Codespaces) and the stargazer-style table in "
                "`data/regression_table.html`."),
            mo.md(
                "**Interpretation.** Model 1's raw association is *negative*, but once "
                "firm size, leverage and industry/year fixed effects are added "
                "(Models 3–4) the ESG coefficient turns **positive and significant** "
                "— higher-rated firms trade at a modest valuation premium *within* "
                "industry-year. The sign flip is a classic omitted-variable lesson: "
                "big, mature firms have better ESG coverage *and* lower q."),
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
def _(cloud_firm, df_phrases, df_sent, px):
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
            color_discrete_map={"2015": "#c0392b", "2025": "#2471a3"},
            template="presentation", height=520,
        )
        _fig_ph.update_yaxes(matches=None, showticklabels=True)
        _parts += [cloud_firm, mo.hstack(_imgs, justify="start"), mo.ui.plotly(_fig_ph)]
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
            color_discrete_map={"2015": "#c0392b", "2025": "#2471a3"},
            template="presentation", height=430,
        )
        _fig_tone.add_hline(y=0.25, line_dash="dot", annotation_text="positive threshold")
        _fig_tone.add_hline(y=-0.25, line_dash="dot", annotation_text="negative threshold")
        _parts += [
            mo.ui.plotly(_fig_tone),
            mo.md("_Scores from `openai/gpt-oss-120b` (few-shot, temperature 0), "
                  "validated by an independent `llama-3.3-70b-versatile` judge — "
                  "agreement rate in `data/judge_eval.csv`._"),
        ]
    else:
        _parts.append(pending(
            "Tone scores appear after `pipeline_3_llm.py` runs (needs a Groq key)."))
    tab_risk = mo.vstack(_parts)
    return (tab_risk,)


@app.cell
def _():
    tab_method = mo.vstack([
        mo.md(
            """
            ## 🛠️ Method, choices & limitations

            ### Two-layer architecture
            **Layer A (offline pipelines, this repo, never deployed)** downloads and
            computes everything that needs the network, secrets or heavy compute, and
            writes small artifacts to `data/`. **Layer B (this page)** is a marimo
            notebook exported to WASM on GitHub Pages: static, no server, no secrets —
            it only reads the Layer-A artifacts over raw GitHub URLs (the Week 4
            course pattern for WASM data loading).

            ### Why these tools
            - **EDGAR over scraping corporate sites** — an official API with no bot
              detection; the SEC only requires a self-identifying `User-Agent`
              (and 0.5 s politeness delays between requests).
            - **yfinance for the Z-Score** — the provided accounting file lacks
              current assets/liabilities and retained earnings; Yahoo's statements
              carry all five Altman inputs. Free data reaches ~4–5 years back, so the
              Z panel covers FY 2021–2025.
            - **Polars for the merge (Week 10 self-exploration)** — the ESG file is
              245k rows × 2 providers; Polars' lazy engine joins and filters it in one
              optimised pass (~10× faster than pandas here) and writes Parquet.
            - **Two-library cross-validation (self-exploration)** — Model 4
              re-estimated with linearmodels' within estimator alongside
              statsmodels' dummy-variable approach (`notebooks/
              Regression_CrossCheck.ipynb`); the coefficients match to 6 decimals,
              guarding against silent specification errors in either
              implementation. The publication table uses the Python `stargazer`
              package — the same table family as the course's Week 10 material.
            - **Two LLM families (self-exploration)** — `openai/gpt-oss-120b`
              classifies (course Week 9 settings: few-shot, temperature 0, JSON-only
              contract); `llama-3.3-70b-versatile` independently re-judges a sample,
              primed with the Week 8 list of ambiguous finance terms.

            ### Limitations & critical evaluation
            - **LLM accuracy** — sentiment labels are model outputs, not ground truth.
              Deterministic settings reduce variance, not bias; the judge agreement
              rate quantifies (dis)agreement but two models can share blind spots.
              Sentences are capped per firm-year for API cost; risky-language nuance
              (litotes, boilerplate hedging) can defeat few-shot classification.
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
            the GitHub Pages settings (`main` / `docs`).
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
    mo.md(
        f"""
        # **Do firms disclose what their numbers say?**
        ### Risk language, tone and financial health of the Magnificent 7 — AF1204 data-literacy portfolio
        ---
        {app_tabs}
        """
    )
    return


if __name__ == "__main__":
    app.run()
