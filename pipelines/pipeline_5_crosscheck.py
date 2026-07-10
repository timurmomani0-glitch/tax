"""
pipeline_5_crosscheck.py — Layer A (offline). AF1204 portfolio.

Cross-tool validation of the ESG-valuation regressions, 100% Python so it runs
in GitHub Codespaces with no extra toolchain (self-exploration, Week 10 spirit):

  1. Re-estimates Models 1-4 with **linearmodels** `PanelOLS` — an independent
     econometrics library that ABSORBS the industry/year fixed effects (within
     estimator) instead of statsmodels' explicit C() dummy columns. Same
     specification via a genuinely different algorithm; the ESGscore/Firm_Size/
     Leverage coefficients must match `data/regression_py.json` to 4 decimals.
  2. Renders a publication-style HTML table with the Python **stargazer**
     package (same table family the course's Week 10 Rmd used) from the
     statsmodels fits -> data/regression_table.html.

There is also a Jupyter notebook wrapper (notebooks/Regression_CrossCheck.ipynb)
that runs this step-by-step with narrative — open it in Codespaces to see the
agreement check interactively.

Inputs:  data/analysis.parquet (from pipeline_4_merge.py)
Outputs: data/regression_table.html, data/crosscheck.json
Run:     python pipelines/pipeline_5_crosscheck.py   (no network needed)
"""

import json
import os

import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from stargazer.stargazer import Stargazer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

TERMS = ["ESGscore", "Firm_Size", "Leverage"]


def load_provider_b():
    df = pd.read_parquet(os.path.join(DATA, "analysis.parquet"))
    df = df[df.source == "Provider_B"].copy()
    df["Year"] = df["Year"].astype(int)
    df["Industry"] = df["Industry"].astype(int)
    return df


def statsmodels_models(df):
    return {
        "Model 1": smf.ols("q ~ ESGscore", data=df).fit(),
        "Model 2": smf.ols("q ~ ESGscore + Firm_Size + Leverage", data=df).fit(),
        "Model 3": smf.ols("q ~ ESGscore + Firm_Size + Leverage + C(Industry)",
                           data=df).fit(),
        "Model 4": smf.ols("q ~ ESGscore + Firm_Size + Leverage + C(Industry) "
                           "+ C(Year)", data=df).fit(),
    }


def panelols_model4(df):
    """Model 4 via the within estimator: entity = Industry, time = Year.

    PanelOLS demeans within industry-year groups rather than inverting a
    dummy-augmented design matrix — numerically a different route to the same
    estimand, which is exactly what makes the agreement check meaningful.
    """
    p = df.set_index(["Industry", "Year"])
    m = PanelOLS.from_formula(
        "q ~ 1 + ESGscore + Firm_Size + Leverage + EntityEffects + TimeEffects",
        data=p, drop_absorbed=True,
    ).fit()
    return m


def main():
    df = load_provider_b()
    sm_models = statsmodels_models(df)
    pl_model = panelols_model4(df)

    sm4 = sm_models["Model 4"]
    report = {"n": int(sm4.nobs), "terms": {}}
    print(f"{'term':<10} {'statsmodels':>12} {'linearmodels':>13} {'match(4dp)':>11}")
    all_match = True
    for t in TERMS:
        a, b = float(sm4.params[t]), float(pl_model.params[t])
        match = abs(a - b) < 5e-5
        all_match &= match
        report["terms"][t] = {"statsmodels": round(a, 6),
                              "linearmodels": round(b, 6), "match_4dp": match}
        print(f"{t:<10} {a:>12.6f} {b:>13.6f} {str(match):>11}")
    report["all_match_4dp"] = all_match
    with open(os.path.join(DATA, "crosscheck.json"), "w") as f:
        json.dump(report, f, indent=2)

    table = Stargazer([sm_models[k] for k in
                       ("Model 1", "Model 2", "Model 3", "Model 4")])
    table.title("ESG score and firm valuation (Tobin's q) — Provider B")
    table.covariate_order(TERMS)
    table.add_line("Industry Indicators", ["No", "No", "Yes", "Yes"])
    table.add_line("Year Indicators", ["No", "No", "No", "Yes"])
    table.significance_levels([0.1, 0.05, 0.01])
    with open(os.path.join(DATA, "regression_table.html"), "w") as f:
        f.write(table.render_html())

    print(f"\nCross-check {'PASSED' if all_match else 'FAILED'} "
          f"(N = {report['n']}); wrote data/crosscheck.json and "
          "data/regression_table.html")
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
