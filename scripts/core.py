import csv, re
from pathlib import Path
from math import log
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
MAX_RESULTS = 5

CSV_CONFIG = {
    "fonts": {
        "file": "fonts.csv",
        "search_cols": ["Family", "Category", "Stroke", "Personality", "Expressive", "Mood", "Best_For", "Keywords", "Subsets"],
        "output_cols": ["Family", "Category", "Stroke", "Personality", "Contrast", "Width", "Styles", "Weight_Range", "Variable", "Variable_Axes", "Body_Suitable", "Quality_Tier", "Popularity_Rank", "Mood", "Best_For", "Google_Fonts_URL", "CSS_Import"]
    },
    "pairings": {
        "file": "pairings.csv",
        "search_cols": ["Pairing_Name", "Category", "Mood_Keywords", "Best_For", "Heading_Font", "Body_Font", "Contrast_Type"],
        "output_cols": ["Pairing_Name", "Category", "Heading_Font", "Body_Font", "Mood_Keywords", "Best_For", "Contrast_Type", "Scale_Recommendation", "Heading_Weights", "Body_Weights", "Google_Fonts_URL", "CSS_Import", "Notes"]
    },
    "scales": {
        "file": "scales.csv",
        "search_cols": ["Scale_Name", "Best_For", "Mood"],
        "output_cols": ["Scale_Name", "Ratio", "Best_For", "Mood", "Sizes_rem", "Line_Heights", "Letter_Spacing_em", "Margin_Below_em"]
    }
}


class BM25:
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.doc_len = []
        self.doc_freqs = []
        self.idf = {}
        self.avg_dl = 0
        self.corpus_size = 0

    def fit(self, corpus):
        self.corpus_size = len(corpus)
        df = defaultdict(int)
        for doc in corpus:
            tokens = self._tokenize(doc)
            self.doc_len.append(len(tokens))
            freqs = defaultdict(int)
            for t in tokens:
                freqs[t] += 1
            self.doc_freqs.append(freqs)
            for t in set(tokens):
                df[t] += 1
        self.avg_dl = sum(self.doc_len) / self.corpus_size if self.corpus_size else 1
        for term, freq in df.items():
            self.idf[term] = log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query):
        tokens = self._tokenize(query)
        scores = []
        for i in range(self.corpus_size):
            s = 0
            dl = self.doc_len[i]
            for t in tokens:
                if t not in self.doc_freqs[i]:
                    continue
                tf = self.doc_freqs[i][t]
                idf = self.idf.get(t, 0)
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                s += idf * num / den
            scores.append(s)
        return scores

    @staticmethod
    def _tokenize(text):
        return re.findall(r'[a-z0-9]+', text.lower())


def _load_csv(config_key):
    cfg = CSV_CONFIG[config_key]
    path = DATA_DIR / cfg["file"]
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _search_csv(query, config_key, max_results=MAX_RESULTS):
    cfg = CSV_CONFIG[config_key]
    rows = _load_csv(config_key)
    if not rows:
        return []
    corpus = []
    for row in rows:
        parts = []
        for col in cfg["search_cols"]:
            parts.append(row.get(col, ""))
        corpus.append(" ".join(parts))
    bm25 = BM25()
    bm25.fit(corpus)
    scores = bm25.score(query)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for idx, sc in ranked[:max_results]:
        if sc <= 0:
            break
        out = {}
        for col in cfg["output_cols"]:
            if col in rows[idx]:
                out[col] = rows[idx][col]
        out["_score"] = round(sc, 4)
        results.append(out)
    return results


def search(query, config_key, max_results=MAX_RESULTS):
    return _search_csv(query, config_key, max_results)


def search_fonts(query, mode="single", tier=None, max_results=5):
    if mode == "lookup":
        rows = _load_csv("fonts")
        cfg = CSV_CONFIG["fonts"]
        results = []
        q_lower = query.strip().lower()
        for row in rows:
            if row.get("Family", "").strip().lower() == q_lower:
                out = {}
                for col in cfg["output_cols"]:
                    if col in row:
                        out[col] = row[col]
                results.append(out)
                break
        return results

    if mode == "pair":
        return _search_csv(query, "pairings", max_results)

    if mode == "scale":
        return _search_csv(query, "scales", max_results)

    # mode == "single" (default)
    # Use large pool — tier/body filtering can eliminate most results
    pool_size = 200 if tier else max_results * 5
    results = _search_csv(query, "fonts", pool_size)
    filtered = []
    for r in results:
        if r.get("Body_Suitable", "").strip().lower() != "yes":
            continue
        if tier and r.get("Quality_Tier", "").strip().upper() != tier.upper():
            continue
        filtered.append(r)
        if len(filtered) >= max_results:
            break
    # If tier filter was applied but no body-suitable constraint produced few results,
    # fall back to just tier filtering
    if not filtered and tier:
        for r in results:
            if r.get("Quality_Tier", "").strip().upper() != tier.upper():
                continue
            filtered.append(r)
            if len(filtered) >= max_results:
                break
    if not filtered and not tier:
        filtered = results[:max_results]
    return filtered
