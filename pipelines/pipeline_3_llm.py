"""
pipeline_3_llm.py — Layer A (offline). AF1204 portfolio.

LLM sentiment on the forward-looking sentences inside each firm's Item 1A risk text,
plus an INDEPENDENT AI-as-judge validation pass (self-exploration — the course Week 9
notebook only asks the classifier for a rationale; a second-model judge is new here).

Design, following the course Week 9 notebook (Wk9_LLM_API_Moodle.ipynb):
  - Groq client, key from environment (.env via python-dotenv here; Codespaces
    secrets work identically since both surface as env vars)
  - classifier model:   openai/gpt-oss-120b, temperature=0, top_p=1 (course settings)
  - judge model:        llama-3.3-70b-versatile — a DIFFERENT model family so the
    check is genuinely independent, primed with the Week 8 ambiguous-vocabulary list
  - few-shot examples:  the course's own 10-per-class files (Week 9 public/llm/)
  - JSON-only output contract, markdown-fence stripping, index re-alignment,
    3-retry loop with sleep, all-neutral fallback on total failure (course patterns)
  - scoring: positive=+1, neutral=0, negative=-1; firm label thresholds +/-0.25

Outputs: data/sentiment.json   — per firm-year tone scores + labels
         data/judge_eval.csv   — sentence-level classifier vs judge agreement
Run:     python pipelines/pipeline_3_llm.py   (needs GROQ_API_KEY + internet)
"""

import csv
import json
import os
import re
import time

from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
FEWSHOT_DIR = os.path.join(ROOT, "course_materials", "week09", "notebooks", "public", "llm")
VOCAB_CSV = os.path.join(ROOT, "course_materials", "week08", "Wk08b_few_shot_examples.csv")
os.makedirs(DATA, exist_ok=True)
load_dotenv(os.path.join(ROOT, ".env"))

CLASSIFIER_MODEL = "openai/gpt-oss-120b"        # course Week 9 classification model
JUDGE_MODEL = "llama-3.3-70b-versatile"          # independent judge (different family)
TEMPERATURE, TOP_P = 0, 1                        # deterministic (course setting)
MAX_SENTENCES_PER_FIRM_YEAR = 40                 # API-cost cap; noted in Limitations
JUDGE_SAMPLE_PER_FIRM_YEAR = 12                  # sentences re-judged per firm-year

# Forward-looking cue words (Muslu et al.-style heuristic; course pre-extracted FLS
# upstream, so the extractor is reimplemented here and documented as an adaptation)
FL_CUES = re.compile(
    r"\b(will|expect|expects|expected|anticipate|anticipates|anticipated|intend|"
    r"intends|plan|plans|planned|future|forecast|forecasts|project|projects|"
    r"believe|believes|may|could|estimate|estimates|likely|outlook|goal|target|"
    r"targets|aim|aims|continue to|going forward)\b", re.IGNORECASE)


def load_sentences(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_ambiguous_vocab():
    """Week 8 self-exploration tie-in: ambiguous finance terms fed to the judge."""
    terms = []
    try:
        with open(VOCAB_CSV, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                terms.append(row["Word"])
    except Exception:
        pass
    return terms


def extract_forward_looking(text, cap=MAX_SENTENCES_PER_FIRM_YEAR):
    """Split into sentences, keep those with forward-looking cues, 30-500 chars."""
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    keep = [s.strip() for s in sentences
            if 30 <= len(s.strip()) <= 500 and FL_CUES.search(s)]
    return keep[:cap]


def build_classifier_prompt(sentences, few_shot):
    few_shot_block = ""
    for label, examples in few_shot.items():
        few_shot_block += f"\n{label.upper()} EXAMPLES (forward-looking, sentiment = {label}):\n"
        few_shot_block += "\n".join(f"- {s} | sentiment: {label}" for s in examples) + "\n"
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences, start=1))
    return f"""You are an expert in analysing forward-looking statements made by US-listed companies in their 10-K risk-factor disclosures.

## Task
Classify each numbered sentence below as "positive", "neutral" or "negative".
Provide a brief rationale (in less than 15 words) for each classification,
focusing on expectations, direction, and strength of language.

## Few-shot examples
{few_shot_block}

## Output format
Return ONLY a JSON object with this exact structure:
{{"sentences": [{{"index": 1, "sentiment": "positive" | "neutral" | "negative", "rationale": "..."}}]}}
Do NOT include any additional keys outside this structure.
Do NOT add commentary outside the JSON object.

## Sentences to classify
{numbered}
"""


def build_judge_prompt(sentence, classifier_label, ambiguous_terms):
    vocab_note = ""
    if ambiguous_terms:
        vocab_note = ("Beware that these finance terms are ambiguous and context-dependent: "
                      + ", ".join(ambiguous_terms[:12]) + ". ")
    return f"""You are a sceptical financial-text auditor. Another AI classified the sentiment of a forward-looking 10-K sentence. Judge independently whether the label is correct. {vocab_note}

Sentence: "{sentence}"
Other AI's label: {classifier_label}

Return ONLY JSON: {{"your_label": "positive" | "neutral" | "negative", "agree": true | false, "reason": "<15 words"}}
"""


def extract_json_from_response(text):
    """Strip markdown fences, slice first {{ to last }} (course pattern)."""
    text = text.strip().strip("`")
    if text.lower().startswith("json"):
        text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No valid JSON object found in model response.")
    return json.loads(text[start:end + 1])


def call_with_retries(client, model, prompt, max_retries=4):
    # Groq free-tier rate limits are token-based, so waits must grow long enough
    # for the per-minute window to reset — quick fixed sleeps are not enough.
    backoff = [3, 12, 35, 65]
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE, top_p=TOP_P,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"  Error calling Groq on attempt {attempt}: {e}")
            time.sleep(backoff[min(attempt, len(backoff)) - 1])
    return None


def classify_firm_year(client, sentences, few_shot, chunk_size=20):
    """Sentence scores aligned to input order, classified in chunks to stay
    inside Groq's token-per-minute limits. Returns (None, None) on total
    failure — the caller marks the firm-year 'failed' rather than pretending
    the tone was neutral (a lesson from the first run)."""
    mapping = {"positive": 1, "neutral": 0, "negative": -1}
    scores, rationales = [], []
    for start in range(0, len(sentences), chunk_size):
        chunk = sentences[start:start + chunk_size]
        raw = call_with_retries(client, CLASSIFIER_MODEL,
                                build_classifier_prompt(chunk, few_shot))
        if raw is None:
            return None, None
        try:
            parsed = extract_json_from_response(raw)
        except ValueError:
            return None, None
        by_index, rat_by_index = {}, {}
        for item in parsed.get("sentences", []):
            try:
                i = int(item.get("index"))
                by_index[i] = mapping.get(str(item.get("sentiment", "")).lower(), 0)
                rat_by_index[i] = str(item.get("rationale", ""))
            except Exception:
                continue  # skip malformed items silently (course pattern)
        scores += [by_index.get(i, 0) for i in range(1, len(chunk) + 1)]
        rationales += [rat_by_index.get(i, "") for i in range(1, len(chunk) + 1)]
        time.sleep(2)  # spacing between chunks, same rate-limit budget
    return scores, rationales


def label_from_mean_score(mean_score):
    if mean_score >= 0.25:
        return "positive"
    if mean_score <= -0.25:
        return "negative"
    return "neutral"


def main():
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise KeyError("GROQ_API_KEY not set. Add it to .env (or Codespaces secrets) "
                       "and restart.")
    client = Groq(api_key=api_key)

    with open(os.path.join(DATA, "risk_data.json")) as f:
        risk_data = json.load(f)

    few_shot = {
        "positive": load_sentences(os.path.join(FEWSHOT_DIR, "positive_examples_Moodle.txt")),
        "negative": load_sentences(os.path.join(FEWSHOT_DIR, "negative_examples_Moodle.txt")),
        "neutral": load_sentences(os.path.join(FEWSHOT_DIR, "neutral_examples_Moodle.txt")),
    }
    ambiguous_terms = load_ambiguous_vocab()
    inv = {1: "positive", 0: "neutral", -1: "negative"}

    sentiment, judge_rows = {}, []
    for ticker, years in risk_data.items():
        sentiment[ticker] = {}
        for year, text in years.items():
            sentences = extract_forward_looking(text)
            if not sentences:
                print(f"{ticker} {year}: no forward-looking sentences found")
                continue
            scores, rationales = classify_firm_year(client, sentences, few_shot)
            if scores is None:
                print(f"{ticker} {year}: classification FAILED after retries — "
                      "not recorded (rerun to fill in)")
                continue
            mean_score = sum(scores) / float(len(scores))
            sentiment[ticker][year] = {
                "n_sentences": len(sentences),
                "mean_score": round(mean_score, 3),
                "label": label_from_mean_score(mean_score),
                "share_negative": round(scores.count(-1) / len(scores), 3),
                "share_positive": round(scores.count(1) / len(scores), 3),
                "examples": [
                    {"sentence": s, "score": sc, "rationale": r}
                    for s, sc, r in list(zip(sentences, scores, rationales))[:5]
                ],
            }
            print(f"{ticker} {year}: {len(sentences)} sentences, "
                  f"mean {mean_score:+.2f} ({sentiment[ticker][year]['label']})")

            # AI-as-judge second pass on a fixed sample (chained prompts)
            for s, sc in list(zip(sentences, scores))[:JUDGE_SAMPLE_PER_FIRM_YEAR]:
                raw = call_with_retries(client, JUDGE_MODEL,
                                        build_judge_prompt(s, inv[sc], ambiguous_terms))
                verdict = {"your_label": "", "agree": None, "reason": "judge call failed"}
                if raw is not None:
                    try:
                        verdict = extract_json_from_response(raw)
                    except ValueError:
                        verdict["reason"] = "judge returned non-JSON"
                judge_rows.append({
                    "ticker": ticker, "year": year, "sentence": s[:300],
                    "classifier_label": inv[sc],
                    "judge_label": str(verdict.get("your_label", "")).lower(),
                    "agree": verdict.get("agree"),
                    "judge_reason": str(verdict.get("reason", ""))[:120],
                })
                time.sleep(0.3)  # stay well inside Groq free-tier rate limits

    with open(os.path.join(DATA, "sentiment.json"), "w") as f:
        json.dump(sentiment, f, indent=2)

    # Flat CSV for the deployed WASM site (raw-URL friendly)
    with open(os.path.join(DATA, "sentiment.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "year", "n_sentences", "mean_score", "label",
                         "share_negative", "share_positive"])
        for t, yrs in sentiment.items():
            for y, s in yrs.items():
                writer.writerow([t, y, s["n_sentences"], s["mean_score"], s["label"],
                                 s["share_negative"], s["share_positive"]])

    judge_path = os.path.join(DATA, "judge_eval.csv")
    with open(judge_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(judge_rows[0].keys()))
        writer.writeheader()
        writer.writerows(judge_rows)

    judged = [r for r in judge_rows if r["agree"] is not None]
    agreement = (sum(1 for r in judged if r["agree"]) / len(judged)) if judged else float("nan")
    print(f"\nJudge agreement rate: {agreement:.1%} over {len(judged)} sentences")
    print(f"Wrote data/sentiment.json and {judge_path}")


if __name__ == "__main__":
    main()
