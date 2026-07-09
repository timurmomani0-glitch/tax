"""
pipeline_1_financials.py — Layer A (offline). AF1204 portfolio.

Builds the Magnificent-7 firm-year panel (fiscal years 2021-2025) from Yahoo Finance
and computes the Altman Z-Score per firm-year, following the course notebooks:
  - Z-Score formula + try/except NaN handling  -> Wk02_Marimo_ZScore
  - panel download loop, statement-column selection by fiscal year, exact yfinance
    field keys, rate limiting                  -> Wk02x_DLdata_fromYahooFinance

Yahoo Finance only serves ~the last 4-5 fiscal years for free (course note), hence
2021-2025 rather than 2015-2025; the 2015-vs-2025 comparison lives in the EDGAR
text layer (pipeline_2), which has no such limit.

Output: data/financials.csv — one row per firm-year with raw inputs + Z_Score.
Run:    python pipelines/pipeline_1_financials.py   (needs internet access to Yahoo)
"""

import os
import time

import pandas as pd
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
os.makedirs(DATA, exist_ok=True)

MAG7 = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "META": "Meta Platforms", "NVDA": "Nvidia", "TSLA": "Tesla",
}
YEAR_START, YEAR_END = 2021, 2025

# Zone thresholds (Altman, 1968): > 2.99 safe, 1.81-2.99 grey, < 1.81 distress
SAFE, DISTRESS = 2.99, 1.81


def zscore(total_assets, current_assets, current_liab, retained_earnings,
           ebit, total_liab, sales, market_cap):
    """Altman Z-Score, exactly as defined in the Week 2 course notebook.

    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    X1 working capital / TA, X2 retained earnings / TA, X3 EBIT / TA,
    X4 market value of equity / book value of total liabilities, X5 sales / TA.
    Assumes no preferred stock (course simplification). NaN on zero denominators.
    """
    try:
        wkcap2ta = (current_assets - current_liab) / total_assets
        re2ta = retained_earnings / total_assets
        ebit2ta = ebit / total_assets
        mv2tl = (market_cap + 0) / total_liab  # preferred_market_cap = 0
        sales2ta = sales / total_assets
        return (1.2 * wkcap2ta + 1.4 * re2ta + 3.3 * ebit2ta
                + 0.6 * mv2tl + 1.0 * sales2ta)
    except (ZeroDivisionError, TypeError):
        return float("nan")


def zone(z):
    if pd.isna(z):
        return "N/A"
    return "Safe" if z > SAFE else ("Grey" if z >= DISTRESS else "Distress")


def _select_series_for_date(df, target_date):
    """Pick the statement column whose date is the latest <= target_date
    (falls back to the most recent column) — course Wk02x pattern."""
    try:
        col_dates = pd.to_datetime(df.columns.astype(str), errors="coerce")
        valid = col_dates[col_dates <= target_date]
        if len(valid) == 0:
            return df.iloc[:, 0]
        chosen = valid.max()
        return df[df.columns[(col_dates == chosen)][0]]
    except Exception:
        return df.iloc[:, 0]


def _get_numeric(series, key):
    try:
        v = series.get(key)
        if isinstance(v, (tuple, list)) and len(v) == 1:
            v = v[0]
        if v is None or pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def fetch_firm_year(stock, ticker, year_int):
    """One firm-year row, or None if the fiscal year / data is unavailable."""
    target_date = pd.Timestamp(f"{year_int}-12-31")
    bs_df = getattr(stock, "balance_sheet", None)
    is_df = getattr(stock, "income_stmt", None)
    if bs_df is None or is_df is None or bs_df.empty or is_df.empty:
        return None

    balance_sheet = _select_series_for_date(bs_df, target_date)
    income_stmt = _select_series_for_date(is_df, target_date)
    report_year = pd.Timestamp(balance_sheet.name).year
    if report_year != year_int:
        return None  # strict fiscal-year gate (course pattern)

    total_assets = _get_numeric(balance_sheet, "Total Assets")
    if total_assets is None or total_assets <= 0:
        return None  # Z-Score components require Total Assets > 0

    current_assets = _get_numeric(balance_sheet, "Current Assets")
    current_liab = _get_numeric(balance_sheet, "Current Liabilities")
    retained_earnings = _get_numeric(balance_sheet, "Retained Earnings")
    total_liab = _get_numeric(balance_sheet, "Total Liabilities Net Minority Interest")
    shares = _get_numeric(balance_sheet, "Ordinary Shares Number")
    ebit = _get_numeric(income_stmt, "EBIT")  # or Operating Income
    sales = _get_numeric(income_stmt, "Total Revenue")

    # Market cap = shares outstanding x last close <= fiscal year end (course pattern)
    market_cap = None
    close_price = None
    try:
        hist = stock.history(start=f"{year_int}-01-01", end=f"{year_int + 1}-03-31",
                             interval="1d")
        hist.index = hist.index.tz_localize(None)
        upto = hist[hist.index <= pd.Timestamp(balance_sheet.name).tz_localize(None)]
        if not upto.empty and shares:
            close_price = float(upto["Close"].iloc[-1])
            market_cap = shares * close_price
    except Exception as e:
        print(f"  Warning: price history failed for {ticker} {year_int}: {e}")

    z = zscore(total_assets, current_assets, current_liab, retained_earnings,
               ebit, total_liab, sales, market_cap)
    return {
        "Ticker": ticker, "Name": MAG7[ticker], "Year": year_int,
        "Fiscal_Year_End": str(pd.Timestamp(balance_sheet.name).date()),
        "Total_Assets": total_assets, "Current_Assets": current_assets,
        "Current_Liab": current_liab, "Retained_Earnings": retained_earnings,
        "Total_Liab": total_liab, "EBIT": ebit, "Sales": sales,
        "Shares": shares, "Closing_Price": close_price, "Market_Cap": market_cap,
        "Z_Score": z, "Zone": zone(z),
    }


def main():
    rows = []
    for year_int in range(YEAR_START, YEAR_END + 1):
        print(f"Fiscal year {year_int}...")
        for ticker in MAG7:
            try:
                row = fetch_firm_year(yf.Ticker(ticker), ticker, year_int)
                if row:
                    rows.append(row)
                    print(f"  {ticker}: Z = {row['Z_Score']:.2f} ({row['Zone']})")
                else:
                    print(f"  {ticker}: no {year_int} statements available, skipped")
            except Exception as e:
                print(f"  Error for {ticker} in {year_int}: {e}")
            time.sleep(0.05)  # respect Yahoo Finance rate limits (course guidance)
        time.sleep(1)

    df = pd.DataFrame(rows)
    out = os.path.join(DATA, "financials.csv")
    df.to_csv(out, index=False)
    print(f"\nWrote {len(df)} firm-year rows -> {out}")


if __name__ == "__main__":
    main()
