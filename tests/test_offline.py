"""Offline acceptance tests for the AF1204 pipelines (no network needed).

M1 accept: Z-Score matches a hand-checked example; no crash on missing data.
M5 accept: Item 1A extractor returns readable text (not raw HTML) from sample HTML.
M6 accept: LLM JSON parsing survives fences/misalignment; scoring thresholds correct.
Run: .venv/bin/python -m pytest tests/ -q   (or python tests/test_offline.py)
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipelines"))

from pipeline_1_financials import zscore, zone
from pipeline_2_edgar import extract_risk_factors
from pipeline_3_llm import (extract_forward_looking, extract_json_from_response,
                            label_from_mean_score)


def test_zscore_hand_checked():
    # Hand-checked: TA=100, CA=40, CL=20, RE=30, EBIT=10, TL=60, Sales=80, MCap=90
    # Z = 1.2*0.2 + 1.4*0.3 + 3.3*0.1 + 0.6*1.5 + 1.0*0.8 = 2.69 (Grey zone)
    z = zscore(100, 40, 20, 30, 10, 60, 80, 90)
    assert abs(z - 2.69) < 1e-9, z
    assert zone(z) == "Grey"
    assert zone(3.0) == "Safe" and zone(1.80) == "Distress"


def test_zscore_missing_data_is_nan_not_crash():
    assert math.isnan(zscore(100, 40, 20, 30, 10, 0, 80, 90))      # zero liabilities
    assert math.isnan(zscore(100, None, 20, 30, 10, 60, 80, 90))   # missing field


def test_edgar_extraction_readable_text():
    html = b"""<html><body>
    <p>Item 1.</p><p>Business blah blah.</p>
    <p>Item 1A. Risk Factors</p>
    <p>Our revenue depends on consumer demand. Competition is intense and
    increasing. Cybersecurity incidents could harm our reputation and results.
    """ + b"Supply chain disruption is an ongoing concern. " * 20 + b"""</p>
    <p>Item 1B. Unresolved Staff Comments</p><p>None.</p>
    </body></html>"""
    text = extract_risk_factors(html)
    assert text is not None and text.startswith("Item 1A")
    assert "Cybersecurity" in text and "<p>" not in text
    assert "Unresolved Staff Comments" not in text


def test_edgar_extraction_skips_table_of_contents():
    # Real 10-Ks list "Item 1A. Risk Factors" in the TOC first; a first-match
    # extractor sweeps the whole "Item 1. Business" section into the extract.
    body = ("Consumer demand may decline. Competition is intense. "
            "Regulatory scrutiny is increasing. " * 30)
    html = (
        "<html><body>"
        "<p>TABLE OF CONTENTS</p>"
        "<p>Item 1. Business 3</p><p>Item 1A. Risk Factors 15</p>"
        "<p>Item 1B. Unresolved Staff Comments 40</p><p>Item 2. Properties 41</p>"
        "<p>Item 1. Business</p>"
        "<p>" + "We design, manufacture and market smartphones. " * 40 + "</p>"
        "<p>Item 1A. Risk Factors</p>"
        "<p>" + body + "</p>"
        "<p>Item 1B. Unresolved Staff Comments</p><p>None.</p>"
        "</body></html>"
    ).encode()
    text = extract_risk_factors(html)
    assert text is not None
    assert "Consumer demand may decline" in text
    assert "manufacture and market smartphones" not in text, \
        "extractor swept the Business section (TOC first-match bug)"


def test_edgar_extraction_handles_split_letter_headings():
    # Real MSFT/TSLA 10-Ks flatten with page anchors splitting heading words:
    # "I TEM 1A", "RIS K FACTORS" — extraction must still find the section.
    body = "Competition is intense. Cyberattacks could harm results. " * 40
    html = ("<html><body>"
            "<p>Item 1. Business 3</p><p>Item 1A. Risk Factors 16</p>"
            "<p>Item 1B. Unresolved Staff Comments 30</p><p>Item 2. Properties 32</p>"
            "<p>Item 1. Business</p><p>" + "We sell software. " * 60 + "</p>"
            "<p>PART I Item 1A I TEM 1A. RIS K FACTORS</p>"
            "<p>" + body + "</p>"
            "<p>I TEM 1B. Unresolved Staff Comments</p>"
            "</body></html>").encode()
    text = extract_risk_factors(html)
    assert text is not None and "Cyberattacks could harm" in text
    assert "We sell software" not in text


def test_edgar_extraction_prefers_real_heading_over_cross_reference():
    # A cross-reference inside "Item 1. Business" sweeps into the real section
    # and comes out LONGER — the real heading (latest start) must win.
    risk = "Demand may decline. Regulation could adversely affect us. " * 400
    html = ("<html><body>"
            "<p>see Item 1A Risk Factors of this Annual Report for details.</p>"
            "<p>" + "Our people are critical to our success. " * 200 + "</p>"
            "<p>ITEM 1A. RISK FACTORS</p><p>" + risk + "</p>"
            "<p>Item 1B. Unresolved Staff Comments</p>"
            "</body></html>").encode()
    text = extract_risk_factors(html)
    assert text is not None and text.upper().startswith("ITEM 1A. RISK FACTORS")
    assert "Our people are critical" not in text


def test_llm_json_parsing_with_fences_and_gaps():
    raw = """```json
    {"sentences": [{"index": 1, "sentiment": "positive", "rationale": "growth"},
                   {"index": 3, "sentiment": "negative", "rationale": "decline"}]}
    ```"""
    parsed = extract_json_from_response(raw)
    assert parsed["sentences"][0]["sentiment"] == "positive"
    assert len(parsed["sentences"]) == 2  # index 2 missing -> caller defaults it to 0


def test_firm_label_thresholds():
    assert label_from_mean_score(0.25) == "positive"
    assert label_from_mean_score(0.24) == "neutral"
    assert label_from_mean_score(-0.25) == "negative"


def test_forward_looking_extraction():
    text = ("Our revenue was flat. We expect competition to intensify in future "
            "periods. The company was founded in 1998. Management anticipates "
            "higher costs will impact margins going forward.")
    fls = extract_forward_looking(text)
    assert len(fls) == 2
    assert all("expect" in s or "anticipates" in s for s in fls)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("All offline acceptance tests passed.")
