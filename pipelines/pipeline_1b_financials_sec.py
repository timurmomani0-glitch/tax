"""
pipeline_1b_financials_sec.py — Layer A (offline). AF1204 portfolio.

FALLBACK route for the Altman Z-Score panel (self-exploration): when Yahoo
Finance rate-limits the environment (yfinance returns empty statements, as
happened in the cloud build environment), the five Altman inputs can be taken
from the SEC's official XBRL "companyfacts" API — the same official-API
philosophy as the Week 7/10 EDGAR work — and the market value of equity at
fiscal year-end from the course-provided ESG dataset (Provider_B reports
month-end market caps in dollars through early 2024).

Coverage: fiscal years 2021-2023 (limited by the provided price data).
`pipeline_1_financials.py` (course-faithful yfinance route) extends the panel
to FY2025 when run somewhere Yahoo allows, and simply overwrites the output.

Output: data/financials.csv — same schema as pipeline_1 plus a Source column.
Run:    python pipelines/pipeline_1b_financials_sec.py  (needs sec.gov access)
"""

import os
import time
from datetime import date

import pandas as pd
import pyreadr
import requests
from dotenv import load_dotenv

from pipeline_1_financials import MAG7, zone, zscore

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
ESG_RDATA = os.path.join(ROOT, "course_materials", "week10", "notebooks", "public",
                         "ESG_data_Moodle.RData")
os.makedirs(DATA, exist_ok=True)
load_dotenv(os.path.join(ROOT, ".env"))

SEC_HEADERS = {"User-Agent": os.getenv("SEC_USER_AGENT", "Your Name yourname@example.com")}
YEARS = [2021, 2022, 2023]

# us-gaap tags for the Altman inputs; EBIT falls back to Operating Income
# exactly as the course Week 2 notebook notes ("EBIT, # Or Operating Income").
TAGS = {
    "Total_Assets": ["Assets"],
    "Current_Assets": ["AssetsCurrent"],
    "Current_Liab": ["LiabilitiesCurrent"],
    "Retained_Earnings": ["RetainedEarningsAccumulatedDeficit"],
    "Total_Liab": ["Liabilities"],
    "EBIT": ["OperatingIncomeLoss"],
    "Sales": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
              "SalesRevenueNet"],
}
EQUITY_FALLBACK = "StockholdersEquity"  # Total_Liab = Assets - Equity when untagged


def ticker_to_cik(ticker):
    resp = requests.get("https://www.sec.gov/files/company_tickers.json",
                        headers=SEC_HEADERS, timeout=15)
    resp.raise_for_status()
    for entry in resp.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    return None


def fy_values(facts, tag, duration):
    """{calendar year of period end: (value, end_date)} from 10-K facts.

    Instant tags (balance sheet) key on the balance date; duration tags
    (income statement) only accept full-year periods (300-400 days). Restated
    figures from later filings win via the latest 'filed' date.
    """
    try:
        entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
    except KeyError:
        return {}
    best = {}
    for e in entries:
        if e.get("form") != "10-K" or not e.get("end"):
            continue
        if duration:
            if not e.get("start"):
                continue
            span = (date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days
            if not 300 <= span <= 400:
                continue
        y = int(e["end"][:4])
        key = (e["end"], e.get("filed", ""))
        if y not in best or key > best[y][0]:
            best[y] = (key, float(e["val"]), e["end"])
    return {y: (v, end) for y, ((_, __), v, end) in
            ((y, (k, v, end)) for y, (k, v, end) in best.items())}


def load_market_caps():
    """Provider_B month-end market caps (dollars) from the provided ESG data."""
    df = pyreadr.read_r(ESG_RDATA)["ESG_data"]
    sub = df[(df.instrument.isin(MAG7)) & (df.source == "Provider_B")]
    return {(r.instrument, str(r.date)): float(r.market_cap)
            for r in sub.itertuples() if pd.notna(r.market_cap)}


def month_end(iso_date):
    return str(pd.Period(iso_date[:7], "M").end_time.date())


def main():
    caps = load_market_caps()
    rows = []
    for ticker in MAG7:
        cik = ticker_to_cik(ticker)
        facts = requests.get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            headers=SEC_HEADERS, timeout=60).json()
        time.sleep(0.5)  # be polite to SEC servers

        values = {}
        for field, tags in TAGS.items():
            merged = {}
            # Firms switch tags across filing eras (e.g. Revenues ->
            # RevenueFromContractWithCustomer...), so merge per-year across
            # all candidates — earlier tags in the list win where both exist.
            for tag in tags:
                got = fy_values(facts, tag, duration=field in ("EBIT", "Sales"))
                for y, pair in got.items():
                    merged.setdefault(y, pair)
            if merged:
                values[field] = merged
        equity = fy_values(facts, EQUITY_FALLBACK, duration=False)

        for year in YEARS:
            def val(field):
                return values.get(field, {}).get(year, (None, None))[0]

            total_assets = val("Total_Assets")
            if not total_assets:
                print(f"{ticker} {year}: no XBRL balance sheet, skipped")
                continue
            fye = values["Total_Assets"][year][1]
            total_liab = val("Total_Liab")
            if total_liab is None and year in equity:
                total_liab = total_assets - equity[year][0]

            market_cap = caps.get((ticker, month_end(fye)))
            z = zscore(total_assets, val("Current_Assets"), val("Current_Liab"),
                       val("Retained_Earnings"), val("EBIT"), total_liab,
                       val("Sales"), market_cap)
            rows.append({
                "Ticker": ticker, "Name": MAG7[ticker], "Year": year,
                "Fiscal_Year_End": fye,
                "Total_Assets": total_assets, "Current_Assets": val("Current_Assets"),
                "Current_Liab": val("Current_Liab"),
                "Retained_Earnings": val("Retained_Earnings"),
                "Total_Liab": total_liab, "EBIT": val("EBIT"), "Sales": val("Sales"),
                "Shares": None, "Closing_Price": None, "Market_Cap": market_cap,
                "Z_Score": z, "Zone": zone(z),
                "Source": "SEC XBRL companyfacts + course-provided market caps",
            })
            print(f"{ticker} {year} (FYE {fye}): Z = {z:.2f} ({zone(z)})"
                  if pd.notna(z) else f"{ticker} {year}: Z undefined (missing input)")

    df = pd.DataFrame(rows)
    out = os.path.join(DATA, "financials.csv")
    df.to_csv(out, index=False)
    print(f"\nWrote {len(df)} firm-year rows -> {out}")


if __name__ == "__main__":
    main()
