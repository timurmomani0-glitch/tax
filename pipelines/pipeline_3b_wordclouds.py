"""
pipeline_3b_wordclouds.py — Layer A (offline). AF1204 portfolio.

Renders 2015-vs-2025 risk-language word clouds per firm from data/risk_data.json,
adapting the course Week 10 NLP recipe (Wk10_BigramCloud_GPUorCPU_Moodle.py):
US-term normalisation, conjunction chunk boundaries, lemmatisation, nltk n-grams,
domain stop-words, boilerplate-bigram blacklist, redundant-unigram removal (90%
coverage rule), WordCloud Reds (2015) / Blues (2025).

NLP engine — three tiers, best available wins, and the engine + runtime are
printed and saved so the GPU/CPU comparison can be reported:
  1. spaCy en_core_web_trf + spacy.prefer_gpu()  (GPU; use the Colab notebook in
     notebooks_colab/ — model wheels are not downloadable from this environment)
  2. spaCy en_core_web_sm                        (CPU)
  3. nltk WordNet lemmatiser + rule-based chunks (CPU fallback, no spaCy model)

Outputs: data/wordclouds/{ticker}_{year}.png, data/wordclouds/top_phrases.json,
         data/wordclouds/engine_report.json
Run:     python pipelines/pipeline_3b_wordclouds.py
"""

import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "wordclouds")
os.makedirs(OUT, exist_ok=True)

YEARS = [2015, 2025]
MIN_COUNT = 3
UNIGRAM_COVERAGE_THRESHOLD = 0.9   # course rule: bigram covering 90% of a unigram kills it
MAX_CHARS = 100_000                # course cap on NLP input length

BOUNDARY_WORDS = {"and", "or", "but", "nor", "yet", "so", "although", "whereas"}

# Course Week 10 domain stop-words (on top of nltk English stop-words)
DOMAIN_STOP = {
    "inc", "corp", "corporation", "llc", "co", "may", "could", "will", "would",
    "should", "shall", "subject", "including", "however", "also", "per", "within",
    "without", "form", "state", "believe", "addition", "example", "event", "expect",
    "partner", "year", "years", "fiscal", "period", "quarter", "note", "item",
    "company", "factor", "risk", "business", "operation", "product", "service",
    "result", "unitedstate", "unitedstates",
}

# Course Week 10 boilerplate blacklist (applied after lemmatisation)
BLACKLIST = {
    "product", "service", "subject_to", "unitedstates", "unitedstates_government",
    "may_result", "could_adversely", "would_adversely", "adversely_affect",
    "negatively_impact", "business_may", "reputation_financial", "financial_condition",
    "table_content", "table_contents", "risk_factor", "forward_look", "look_statement",
    "report_form", "annual_report", "vice_president", "executive_vice",
    "common_stock", "per_share",
}
BLACKLIST_PREFIXES = {"product", "servic", "busi", "oper", "result"}


def normalise_us(text):
    text = re.sub(r"\bUnited States\b", "unitedstates", text, flags=re.IGNORECASE)
    text = re.sub(r"\bU\.?S\.?\b", "unitedstates", text, flags=re.IGNORECASE)
    return re.sub(r"\bUS\b", "unitedstates", text)


def build_nlp():
    """Return (engine_name, lemmatise_fn). lemmatise_fn: text -> list of chunks,
    each chunk a list of lemmas (conjunctions split chunks, course Fix 1)."""
    import nltk
    from nltk.corpus import stopwords
    try:
        stop = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        stop = set(stopwords.words("english"))
    stop |= DOMAIN_STOP

    try:
        import spacy
        gpu = spacy.prefer_gpu()
        for model in ("en_core_web_trf", "en_core_web_sm"):
            try:
                nlp = spacy.load(model)
                engine = f"spaCy {model} on {'GPU' if gpu else 'CPU'}"

                def lemmatise(text, _nlp=nlp, _stop=stop):
                    doc = _nlp(text[:MAX_CHARS])
                    chunks, current = [], []
                    for token in doc:
                        lemma = token.lemma_.lower()
                        if token.pos_ in {"CCONJ", "SCONJ"} or lemma in BOUNDARY_WORDS:
                            if current:
                                chunks.append(current)
                            current = []
                            continue
                        if (not token.is_alpha or token.is_stop or token.is_punct
                                or token.is_space or len(lemma) <= 2 or lemma in _stop):
                            continue
                        current.append(lemma)
                    if current:
                        chunks.append(current)
                    return chunks

                return engine, lemmatise
            except OSError:
                continue
    except ImportError:
        pass

    # Tier 3: nltk-only fallback (no spaCy model download available)
    from nltk.stem import WordNetLemmatizer
    try:
        lemmatizer = WordNetLemmatizer()
        lemmatizer.lemmatize("testing")
    except LookupError:
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
        lemmatizer = WordNetLemmatizer()
    engine = "nltk WordNetLemmatizer on CPU (fallback — no spaCy model available)"

    def lemmatise(text, _stop=stop, _lem=lemmatizer):
        words = re.findall(r"[A-Za-z]+", text[:MAX_CHARS].lower())
        chunks, current = [], []
        for w in words:
            if w in BOUNDARY_WORDS:
                if current:
                    chunks.append(current)
                current = []
                continue
            lemma = _lem.lemmatize(_lem.lemmatize(w), pos="v")
            if len(lemma) <= 2 or w in _stop or lemma in _stop:
                continue
            current.append(lemma)
        if current:
            chunks.append(current)
        return chunks

    return engine, lemmatise


def ngram_frequencies(chunks):
    """Unigram+bigram counts within chunks, course fixes applied."""
    from collections import Counter
    from nltk.util import ngrams
    counts = Counter()
    for chunk in chunks:
        for n in (1, 2):
            for gram in ngrams(chunk, n):
                if n > 1 and len(set(gram)) == 1:
                    continue  # drop "time time"-style bigrams (course Fix 3)
                counts["_".join(gram)] += 1
    return counts


def remove_redundant_unigrams(counts, threshold=UNIGRAM_COVERAGE_THRESHOLD):
    unigrams = {k: v for k, v in counts.items() if "_" not in k}
    bigrams = {k: v for k, v in counts.items() if k.count("_") == 1}
    final = dict(bigrams)
    for word, uni_count in unigrams.items():
        covered = sum(v for k, v in bigrams.items() if word in k.split("_"))
        coverage_ratio = covered / uni_count if uni_count > 0 else 0
        if coverage_ratio < threshold:
            final[word] = uni_count
    return final


def apply_blacklist(freq):
    out = {}
    for k, v in freq.items():
        if k in BLACKLIST:
            continue
        parts = k.split("_")
        if len(parts) == 2 and parts[0] in BLACKLIST_PREFIXES:
            continue
        out[k] = v
    return out


def render_cloud(freq, year, path):
    from wordcloud import WordCloud
    wc = WordCloud(width=600, height=350, background_color="white",
                   colormap="Reds" if year == 2015 else "Blues",
                   max_words=70, min_font_size=10, prefer_horizontal=0.9,
                   ).generate_from_frequencies(freq)
    wc.to_image().save(path, format="PNG", optimize=True)


def main():
    with open(os.path.join(DATA, "risk_data.json")) as f:
        risk_data = json.load(f)

    engine, lemmatise = build_nlp()
    print(f"NLP engine: {engine}")

    top_phrases, timings = {}, {}
    for ticker, years in risk_data.items():
        top_phrases[ticker] = {}
        for year in YEARS:
            text = years.get(str(year)) or years.get(year)
            if not text or len(text.strip()) < 200:
                print(f"{ticker} {year}: no / insufficient data, skipped")
                continue
            t0 = time.perf_counter()
            chunks = lemmatise(normalise_us(text))
            counts = ngram_frequencies(chunks)
            freq = apply_blacklist(remove_redundant_unigrams(counts))
            freq = {k: v for k, v in freq.items() if v >= MIN_COUNT}
            elapsed = time.perf_counter() - t0
            timings[f"{ticker}_{year}"] = round(elapsed, 2)
            if not freq:
                print(f"{ticker} {year}: nothing left after filtering, skipped")
                continue
            png = os.path.join(OUT, f"{ticker}_{year}.png")
            render_cloud(freq, year, png)
            top = sorted(freq.items(), key=lambda kv: -kv[1])[:20]
            top_phrases[ticker][str(year)] = [
                {"phrase": k.replace("_", " "), "count": v} for k, v in top
            ]
            print(f"{ticker} {year}: {len(freq)} phrases, {elapsed:.1f}s -> {png}")

    with open(os.path.join(OUT, "top_phrases.json"), "w") as f:
        json.dump(top_phrases, f, indent=2)
    # Flat CSV for the deployed WASM site (raw-URL friendly)
    with open(os.path.join(OUT, "top_phrases.csv"), "w", encoding="utf-8") as f:
        f.write("ticker,year,phrase,count\n")
        for t, yrs in top_phrases.items():
            for y, rows in yrs.items():
                for r in rows:
                    f.write(f"{t},{y},{r['phrase']},{r['count']}\n")
    with open(os.path.join(OUT, "engine_report.json"), "w") as f:
        json.dump({"engine": engine, "seconds_per_firm_year": timings}, f, indent=2)
    print(f"Engine report + top phrases written to {OUT}")


if __name__ == "__main__":
    main()
