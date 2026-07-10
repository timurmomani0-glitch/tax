"""
pipeline_4_merge.py — Layer A (offline). AF1204 portfolio.

Merges the course-provided ESG panel (ESG_data_Moodle.RData, monthly, Providers A/B)
with the Compustat-style accounting file (ESGscore_TobinsQ_Moodle.csv) using POLARS
(Week 10 self-exploration: Polars chosen over pandas for the big merge — the ESG file
is 245k rows x 2 providers and Polars' lazy engine does the join + filters in one
optimised pass), then estimates the Week 6 ESG-valuation regressions with statsmodels.

Variable construction mirrors the course Rmd (WK10_ResultTables_Moodle.Rmd) EXACTLY so
the Python and R coefficients can be compared 1:1:
    q         = (prcc_f * csho + dltt + dlc) / at      (at > 0 else NA)
    Firm_Size = log(at)
    Leverage  = (dltt + dlc) / ceq                     (ceq > 0 else NA)
    Year      = fyear ;  Industry = sich
Models (Provider_B, like the Rmd):
    M1: q ~ ESGscore
    M2: q ~ ESGscore + Firm_Size + Leverage
    M3: M2 + C(Industry)
    M4: M3 + C(Year)
Robustness: Provider_A, large firms (> median size), 2010-2019, winsorised 1/99%.

Outputs (all under data/):
    analysis.parquet / analysis.csv   — merged firm-year panel (both providers)
    descriptive.json                  — N/Mean/Median/SD/Min/Max per variable
    correlation.json                  — pairwise r with significance stars
    regression_py.json                — coefficients/SE/stars/N/R2 for all models
    profile.json                      — missing/outlier profile before cleaning
"""

import json
import os

import numpy as np
import pandas as pd
import polars as pl
import pyreadr
import statsmodels.formula.api as smf
from scipy import stats as scistats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PUB = os.path.join(ROOT, "course_materials", "week10", "notebooks", "public")
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)


def load_provided_data() -> pl.DataFrame:
    """Read the two course files and merge them with Polars (lazy)."""
    rdata = pyreadr.read_r(os.path.join(PUB, "ESG_data_Moodle.RData"))
    esg_pd = rdata["ESG_data"]
    esg_pd["date"] = esg_pd["date"].astype(str)  # mirrors mutate(date = as.character(date))
    esg = pl.from_pandas(esg_pd).lazy()

    acct = pl.scan_csv(
        os.path.join(PUB, "ESGscore_TobinsQ_Moodle.csv"),
        schema_overrides={"datadate": pl.Utf8, "sich": pl.Float64},
    )

    merged = esg.join(
        acct,
        left_on=["instrument", "date"],
        right_on=["tic", "datadate"],
        how="left",
    )

    panel = (
        merged.with_columns(
            at_pos=pl.when(pl.col("at") > 0).then(pl.col("at")).otherwise(None),
            ceq_pos=pl.when(pl.col("ceq") > 0).then(pl.col("ceq")).otherwise(None),
        )
        .with_columns(
            q=(pl.col("prcc_f") * pl.col("csho") + pl.col("dltt") + pl.col("dlc"))
            / pl.col("at_pos"),
            ESGscore=pl.col("esg_metric"),
            Firm_Size=pl.col("at_pos").log(),
            Leverage=(pl.col("dltt") + pl.col("dlc")) / pl.col("ceq_pos"),
            Year=pl.col("fyear"),
            Industry=pl.col("sich"),
        )
        .select(
            "source", "instrument", "name", "sector",
            "q", "ESGscore", "Firm_Size", "Leverage", "Year", "Industry",
        )
    )
    return panel.collect()


def profile(panel: pl.DataFrame) -> dict:
    """Missing/outlier profile BEFORE drop_na — evidence for the cleaning choices."""
    n = panel.height
    miss = {c: int(panel[c].null_count()) for c in ["q", "ESGscore", "Firm_Size", "Leverage"]}
    qs = panel.select(
        pl.col("q").quantile(0.01).alias("q_p01"),
        pl.col("q").quantile(0.99).alias("q_p99"),
        pl.col("q").max().alias("q_max"),
        pl.col("Leverage").quantile(0.01).alias("lev_p01"),
        pl.col("Leverage").quantile(0.99).alias("lev_p99"),
        pl.col("Leverage").max().alias("lev_max"),
    ).to_dicts()[0]
    return {"rows_raw": n, "missing": miss, "quantiles": {k: fnum(v) for k, v in qs.items()}}


def fnum(v):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else round(float(v), 4)


def winsorise(df: pd.DataFrame, cols, lo=0.01, hi=0.99) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        lo_v, hi_v = out[c].quantile(lo), out[c].quantile(hi)
        out[c] = out[c].clip(lo_v, hi_v)
    return out


def stars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def fit(formula: str, df: pd.DataFrame) -> dict:
    m = smf.ols(formula, data=df).fit()
    keep = [t for t in m.params.index if t in ("Intercept", "ESGscore", "Firm_Size", "Leverage")]
    return {
        "terms": {
            t: {
                "coef": round(float(m.params[t]), 4),
                "se": round(float(m.bse[t]), 4),
                "p": round(float(m.pvalues[t]), 4),
                "stars": stars(float(m.pvalues[t])),
            }
            for t in keep
        },
        "n": int(m.nobs),
        "r2": round(float(m.rsquared), 3),
        "industry_fe": "C(Industry)" in formula,
        "year_fe": "C(Year)" in formula,
    }


def main():
    panel = load_provided_data()
    prof = profile(panel)

    clean = panel.drop_nulls(["q", "ESGscore", "Firm_Size", "Leverage", "Year", "Industry"])
    clean.write_parquet(os.path.join(DATA, "analysis.parquet"))
    prof["rows_clean"] = clean.height
    with open(os.path.join(DATA, "profile.json"), "w") as f:
        json.dump(prof, f, indent=2)

    df_b = clean.filter(pl.col("source") == "Provider_B").to_pandas()
    df_a = clean.filter(pl.col("source") == "Provider_A").to_pandas()

    variables = ["q", "ESGscore", "Firm_Size", "Leverage"]
    desc = {
        v: {
            "N": int(df_b[v].count()),
            "Mean": fnum(df_b[v].mean()),
            "Median": fnum(df_b[v].median()),
            "SD": fnum(df_b[v].std()),
            "Min": fnum(df_b[v].min()),
            "Max": fnum(df_b[v].max()),
        }
        for v in variables
    }
    with open(os.path.join(DATA, "descriptive.json"), "w") as f:
        json.dump(desc, f, indent=2)

    corr = {}
    for i, a in enumerate(variables):
        for b in variables[i + 1:]:
            r, p = scistats.pearsonr(df_b[a], df_b[b])
            corr[f"{a}~{b}"] = {"r": round(float(r), 3), "stars": stars(float(p))}
    with open(os.path.join(DATA, "correlation.json"), "w") as f:
        json.dump(corr, f, indent=2)

    base = "q ~ ESGscore"
    ctrl = base + " + Firm_Size + Leverage"
    ife = ctrl + " + C(Industry)"
    iyfe = ife + " + C(Year)"

    df_large = df_b[df_b["Firm_Size"] > df_b["Firm_Size"].median()]
    df_1019 = df_b[(df_b["Year"] >= 2010) & (df_b["Year"] <= 2019)]
    df_wins = winsorise(df_b, ["q", "Leverage"])

    results = {
        "main": {
            "Model 1": fit(base, df_b),
            "Model 2": fit(ctrl, df_b),
            "Model 3": fit(ife, df_b),
            "Model 4": fit(iyfe, df_b),
        },
        "robustness": {
            "Main (Provider B)": fit(iyfe, df_b),
            "Alt. ESG (Provider A)": fit(iyfe, df_a),
            "Large firms": fit(iyfe, df_large),
            "2010-2019": fit(iyfe, df_1019),
            "Winsorised 1/99%": fit(iyfe, df_wins),
        },
    }
    with open(os.path.join(DATA, "regression_py.json"), "w") as f:
        json.dump(results, f, indent=2)

    # --- Flat CSV artifacts for the deployed WASM site (raw-URL friendly) ---
    reg_rows = []
    for group, models in results.items():
        for model_name, res in models.items():
            for term, t in res["terms"].items():
                reg_rows.append({
                    "group": group, "model": model_name, "term": term,
                    "coef": t["coef"], "se": t["se"], "p": t["p"], "stars": t["stars"],
                    "n": res["n"], "r2": res["r2"],
                    "industry_fe": res["industry_fe"], "year_fe": res["year_fe"],
                })
    pd.DataFrame(reg_rows).to_csv(os.path.join(DATA, "site_regression.csv"), index=False)
    pd.DataFrame([{"variable": v, **stats_} for v, stats_ in desc.items()]).to_csv(
        os.path.join(DATA, "site_descriptive.csv"), index=False)
    pd.DataFrame([{"pair": k, **v} for k, v in corr.items()]).to_csv(
        os.path.join(DATA, "site_correlation.csv"), index=False)

    # Real Mag-7 valuation series from the PROVIDED data (q + Leverage per year),
    # so the Financial Health tab has live course data even before pipeline_1 runs.
    mag7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
    clean.filter(
        (pl.col("instrument").is_in(mag7)) & (pl.col("source") == "Provider_B")
    ).select("instrument", "name", "Year", "q", "ESGscore", "Firm_Size", "Leverage") \
     .sort("instrument", "Year") \
     .write_csv(os.path.join(DATA, "mag7_provided.csv"))

    # Provider-B panel (rounded) so the site can draw distribution plots client-side
    clean.filter(pl.col("source") == "Provider_B").select(
        "instrument", "sector", "Year",
        pl.col("q").round(4), pl.col("ESGscore").round(2),
        pl.col("Firm_Size").round(3), pl.col("Leverage").round(4),
    ).write_csv(os.path.join(DATA, "site_panel_b.csv"))

    m4 = results["main"]["Model 4"]["terms"]["ESGscore"]
    print(f"Panel: {prof['rows_raw']} raw -> {prof['rows_clean']} clean firm-year rows")
    print(f"Provider_B N={results['main']['Model 4']['n']}, "
          f"Model 4 ESGscore coef={m4['coef']}{m4['stars']} (se={m4['se']})")
    print("Artifacts written to data/: analysis.parquet, descriptive.json, "
          "correlation.json, regression_py.json, profile.json")


if __name__ == "__main__":
    main()
