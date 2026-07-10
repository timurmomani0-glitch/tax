"""
pipeline_2_edgar.py — Layer A (offline). AF1204 portfolio.

Downloads 10-K "Item 1A. Risk Factors" text for the Magnificent 7 from SEC EDGAR
for filing years 2015 and 2025, adapted directly from the course Week 10 notebook
(Wk10_BigramCloud_GPUorCPU_Moodle.py): ticker->CIK lookup, submissions JSON,
primary-document fetch, regex extraction between "Item 1A ... Risk Factors" and
"Item 1B"/"Item 2", 0.5 s politeness sleep, JSON cache.

EDGAR is an official API: no bot detection or CAPTCHA, but the SEC REQUIRES a
User-Agent identifying you. Set SEC_USER_AGENT in .env ("Name email@domain.com").

Output: data/risk_data.json — {ticker: {year: item_1a_text}}
Run:    python pipelines/pipeline_2_edgar.py    (needs internet access to sec.gov)
"""

import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)
load_dotenv(os.path.join(ROOT, ".env"))

SEC_HEADERS = {"User-Agent": os.getenv("SEC_USER_AGENT", "Your Name yourname@example.com")}

MAG7 = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
    "META": "Meta Platforms", "NVDA": "Nvidia", "TSLA": "Tesla",
}
YEARS = [2015, 2025]
RISK_DATA_PATH = os.path.join(DATA, "risk_data.json")

# Course Week 10 regexes, verbatim
START_PAT = re.compile(r"Item\s+1A[\.\s]*[—\-]?\s*Risk\s+Factors", re.IGNORECASE)
END_PAT = re.compile(r"Item\s+1B[\.\s]|Item\s+2[\.\s]", re.IGNORECASE)


def ticker_to_cik(ticker):
    resp = requests.get("https://www.sec.gov/files/company_tickers.json",
                        headers=SEC_HEADERS, timeout=15)
    resp.raise_for_status()
    for entry in resp.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    return None


def list_10k_filings(cik):
    """All 10-K filings for a CIK, newest first (recent block + paginated files)."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = requests.get(url, headers=SEC_HEADERS, timeout=15).json()
    filings = []

    def collect(block):
        for form, accession, primary_doc, filing_date, report_date in zip(
            block["form"], block["accessionNumber"],
            block["primaryDocument"], block["filingDate"],
            block.get("reportDate", [""] * len(block["form"])),
        ):
            if form == "10-K":
                filings.append({
                    "accession": accession, "primary_doc": primary_doc,
                    "date": filing_date, "report_date": report_date,
                })

    collect(data["filings"]["recent"])
    for page in data["filings"].get("files", []):
        page_data = requests.get(f"https://data.sec.gov/submissions/{page['name']}",
                                 headers=SEC_HEADERS, timeout=15).json()
        collect(page_data)
    return filings


def extract_risk_factors(html_bytes):
    """Item 1A text between the start and end regexes.

    Improvement over the course notebook's first-match approach: 10-K primary
    documents mention "Item 1A ... Risk Factors" first in the table of contents,
    so taking the FIRST match sweeps the whole "Item 1. Business" section into
    the extract. Every start candidate is considered instead; candidates whose
    opening chars are dense with "Item N" tokens (the TOC signature — a real
    section start has at most a stray cross-reference) are dropped, and among
    the rest the longest properly-bounded section wins.
    """
    soup = BeautifulSoup(html_bytes, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    # iXBRL page anchors sometimes split heading words into fragments that
    # defeat the regexes ("I TEM 1A", "RIS K FACTORS" in real MSFT/TSLA 10-Ks) —
    # rejoin them, preserving the original casing.
    for word in ("ITEM", "RISK", "FACTORS"):
        pattern = r"\b" + r"\s?".join(word) + r"\b"
        text = re.sub(pattern, lambda m: m.group(0).replace(" ", ""), text,
                      flags=re.IGNORECASE)

    candidates = []  # (start_pos, text, has_end_marker)
    for m in START_PAT.finditer(text):
        tail = text[m.start():]
        end = END_PAT.search(tail, pos=200)  # skip the section header itself
        cand = tail[:end.start()].strip() if end else tail[:80_000].strip()
        candidates.append((m.start(), cand, end is not None))
    if not candidates:
        return None

    def looks_like_toc(cand):
        return len(re.findall(r"Item\s+\d+[A-C]?[\.\s]", cand[:600], re.IGNORECASE)) >= 3

    pool = [c for c in candidates if not looks_like_toc(c[1])] or candidates
    # Cross-references earlier in the filing ("see Item 1A Risk Factors ...")
    # sweep forward into the same section end, so among the long bounded
    # candidates the real section heading is the one that starts LATEST.
    big = [c for c in pool if c[2] and len(c[1]) >= 20_000]
    if big:
        return max(big, key=lambda c: c[0])[1]
    bounded = [c[1] for c in pool if c[2]]
    return max(bounded or [c[1] for c in pool], key=len)


def fetch_item_1a(cik, filings, target_year):
    """Best 10-K for the target FISCAL year.

    Filings whose report period (reportDate) falls in the target year are tried
    first — fiscal-year accurate for non-December filers like AAPL (Sep FYE) and
    MSFT (Jun FYE), whose fiscal-N 10-K is filed in calendar year N so the course
    filing-date window would pick the year-N+1 (= fiscal N+1) filing instead.
    The course window (filing year in {target, target+1}) remains as a fallback.
    """
    primary = [f for f in filings if f.get("report_date", "")[:4] == str(target_year)]
    fallback = [f for f in filings
                if f not in primary
                and int(f["date"][:4]) in (target_year, target_year + 1)]
    for filing in primary + fallback:
        accession_clean = filing["accession"].replace("-", "")
        doc_url = (f"https://www.sec.gov/Archives/edgar/data/"
                   f"{int(cik)}/{accession_clean}/{filing['primary_doc']}")
        html = requests.get(doc_url, headers=SEC_HEADERS, timeout=30).content
        result = extract_risk_factors(html)
        time.sleep(0.5)  # be polite to SEC servers
        if result and len(result) > 500:
            return result
        print(f"    extracted only {len(result) if result else 0} chars from "
              f"{filing['date']} (period {filing.get('report_date', '?')}), "
              f"trying next filing")
    return None


def main(force_refresh=False):
    if not force_refresh and os.path.exists(RISK_DATA_PATH):
        print(f"{RISK_DATA_PATH} exists — using cache (force_refresh=True to re-download)")
        return

    risk_data = {}
    for ticker, name in MAG7.items():
        print(f"{ticker} ({name})")
        cik = ticker_to_cik(ticker)
        if not cik:
            print("  no CIK found, skipped")
            continue
        filings = list_10k_filings(cik)
        risk_data[ticker] = {}
        for year in YEARS:
            text = fetch_item_1a(cik, filings, year)
            if text:
                risk_data[ticker][str(year)] = text
                print(f"  {year}: {len(text):,} chars of Item 1A extracted")
            else:
                print(f"  {year}: extraction FAILED")

    with open(RISK_DATA_PATH, "w") as f:
        json.dump(risk_data, f)
    print(f"\nWrote {RISK_DATA_PATH}")


if __name__ == "__main__":
    main()
