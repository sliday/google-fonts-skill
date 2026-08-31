"""Core search engine and CSS generation for Google Fonts MCP."""

import csv
import html
import importlib.resources
import json
import os
import re
from collections import defaultdict
from math import log
from pathlib import Path
from urllib.parse import quote_plus

MAX_RESULTS = 5
MAX_RESULTS_LIMIT = 50
MAX_QUERY_LENGTH = 500


def _data_dir() -> Path:
    override = os.environ.get("GOOGLE_FONTS_MCP_DATA")
    if override:
        return Path(override)
    return Path(str(importlib.resources.files("google_fonts_mcp") / "data"))


SCALES = {
    "minor-second":     1.067,
    "major-second":     1.125,
    "minor-third":      1.200,
    "major-third":      1.250,
    "perfect-fourth":   1.333,
    "augmented-fourth": 1.414,
    "perfect-fifth":    1.500,
    "golden-ratio":     1.618,
}

TIERS = ["xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl"]

LINE_HEIGHTS = {
    "xs": 1.6, "sm": 1.6, "base": 1.5, "lg": 1.45,
    "xl": 1.35, "2xl": 1.25, "3xl": 1.15, "4xl": 1.1,
}

LETTER_SPACINGS = {
    "xs": "0.01em", "sm": "0.01em", "base": "0em", "lg": "-0.005em",
    "xl": "-0.01em", "2xl": "-0.015em", "3xl": "-0.02em", "4xl": "-0.025em",
}

MARGIN_BOTTOMS = {
    "xs": "0.5em", "sm": "0.5em", "base": "0.75em", "lg": "1em",
    "xl": "1.25em", "2xl": "1.5em", "3xl": "1.75em", "4xl": "2em",
}

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
        self.doc_len = []
        self.doc_freqs = []
        self.idf = {}
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


# Cached data loading and BM25 index
_csv_cache: dict[str, list[dict]] = {}
_bm25_cache: dict[str, tuple[BM25, list[dict]]] = {}


def _load_csv(config_key):
    if config_key in _csv_cache:
        return _csv_cache[config_key]
    cfg = CSV_CONFIG[config_key]
    path = _data_dir() / cfg["file"]
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    _csv_cache[config_key] = rows
    return rows


def _get_bm25(config_key):
    if config_key in _bm25_cache:
        return _bm25_cache[config_key]
    cfg = CSV_CONFIG[config_key]
    rows = _load_csv(config_key)
    corpus = [" ".join(row.get(col, "") for col in cfg["search_cols"]) for row in rows]
    bm25 = BM25()
    bm25.fit(corpus)
    _bm25_cache[config_key] = (bm25, rows)
    return bm25, rows


def _search_csv(query, config_key, max_results=MAX_RESULTS):
    cfg = CSV_CONFIG[config_key]
    bm25, rows = _get_bm25(config_key)
    if not rows:
        return []
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


def search_fonts(query, mode="single", tier=None, max_results=5):
    query = str(query).strip()
    if not query:
        raise ValueError("query must not be blank")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"query must be at most {MAX_QUERY_LENGTH} characters")
    if mode not in {"single", "pair", "lookup", "scale"}:
        raise ValueError("mode must be one of: single, pair, lookup, scale")
    if not 1 <= max_results <= MAX_RESULTS_LIMIT:
        raise ValueError(f"max_results must be between 1 and {MAX_RESULTS_LIMIT}")
    if tier:
        tier = tier.strip().upper()
        if tier not in {"A", "B", "C"}:
            raise ValueError("tier must be one of: A, B, C")
        if mode != "single":
            raise ValueError("tier is only supported in single mode")

    if mode == "lookup":
        rows = _load_csv("fonts")
        cfg = CSV_CONFIG["fonts"]
        q_lower = query.strip().lower()
        for row in rows:
            if row.get("Family", "").strip().lower() == q_lower:
                return [{col: row[col] for col in cfg["output_cols"] if col in row}]
        return []

    if mode == "pair":
        return _search_csv(query, "pairings", max_results)

    if mode == "scale":
        return _search_csv(query, "scales", max_results)

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


def compute_sizes(base, ratio):
    if base <= 0:
        raise ValueError("base must be greater than zero")
    if ratio <= 0:
        raise ValueError("ratio must be greater than zero")
    sizes = {}
    powers = {"xs": -2, "sm": -1, "base": 0, "lg": 1, "xl": 2, "2xl": 3, "3xl": 4, "4xl": 5}
    for tier, power in powers.items():
        sizes[tier] = round((base * (ratio ** power)) / 16, 4)
    return sizes


def lookup_category(font_name):
    rows = _load_csv("fonts")
    for row in rows:
        if row.get("Family", "").strip().lower() == font_name.strip().lower():
            return row.get("Category")
    return None


def get_fallback(font_name):
    cat = lookup_category(font_name)
    if cat:
        cat_lower = cat.lower()
        if "serif" in cat_lower and "sans" not in cat_lower:
            return "serif"
        if "sans" in cat_lower:
            return "sans-serif"
        if "mono" in cat_lower:
            return "monospace"
    return "sans-serif"


def encode_font(name):
    return quote_plus(name.strip())


def fmt_rem(val):
    return f"{val:.4f}".rstrip("0").rstrip(".")


def _css_string(value):
    escaped = []
    for char in str(value):
        codepoint = ord(char)
        if char in {"\\", "'"}:
            escaped.append(f"\\{char}")
        elif codepoint < 32 or codepoint == 127 or char in {"<", ">", "&"}:
            escaped.append(f"\\{codepoint:x} ")
        else:
            escaped.append(char)
    return "".join(escaped)


def _js_string(value):
    return json.dumps(str(value), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _comment_text(value):
    return str(value).replace("*/", "* /").replace("<", "\\3c ").replace("\r", " ").replace("\n", " ")


def generate_css(heading, body, heading_fb, body_fb, sizes, scale_name, ratio, base):
    lines = ["/* Typography System — Generated by google-fonts-mcp */",
             f"/* Scale: {_comment_text(scale_name)} ({ratio}) | Base: {base}px */", "", ":root {",
             "  /* Font Families */"]
    if heading and body and heading != body:
        lines.append(f"  --font-heading: '{_css_string(heading)}', {heading_fb};")
        lines.append(f"  --font-body: '{_css_string(body)}', {body_fb};")
    else:
        font = heading or body
        fb = heading_fb or body_fb
        lines.append(f"  --font-body: '{_css_string(font)}', {fb};")
    lines.append("")
    lines.append("  /* Font Sizes */")
    for tier in TIERS:
        lines.append(f"  --font-size-{tier}: {fmt_rem(sizes[tier])}rem;")
    lines.append("")
    lines.append("  /* Line Heights */")
    for tier in TIERS:
        lines.append(f"  --line-height-{tier}: {LINE_HEIGHTS[tier]};")
    lines.append("")
    lines.append("  /* Letter Spacing */")
    for tier in TIERS:
        lines.append(f"  --letter-spacing-{tier}: {LETTER_SPACINGS[tier]};")
    lines.append("")
    lines += ["  /* Measure */", "  --measure-narrow: 45ch;",
              "  --measure-base: 65ch;", "  --measure-wide: 75ch;", "}"]
    return "\n".join(lines)


def generate_tailwind(heading, body, heading_fb, body_fb, sizes, scale_name, ratio, base):
    lines = ["// tailwind.config.js extension",
             f"// Scale: {_comment_text(scale_name)} ({ratio}) | Base: {base}px",
             "module.exports = {", "  theme: {", "    extend: {", "      fontFamily: {"]
    if heading and body and heading != body:
        lines.append(f"        heading: [{_js_string(heading)}, {_js_string(heading_fb)}],")
        lines.append(f"        body: [{_js_string(body)}, {_js_string(body_fb)}],")
    else:
        font = heading or body
        fb = heading_fb or body_fb
        lines.append(f"        body: [{_js_string(font)}, {_js_string(fb)}],")
    lines.append("      },")
    lines.append("      fontSize: {")
    for tier in TIERS:
        ls = LETTER_SPACINGS[tier]
        lh = str(LINE_HEIGHTS[tier])
        lines.append(f"        '{tier}': ['{fmt_rem(sizes[tier])}rem', {{ lineHeight: '{lh}', letterSpacing: '{ls}' }}],")
    lines += ["      },", "    },", "  },", "}"]
    return "\n".join(lines)


def normalize_weights(weights):
    """Normalize a weight string for the Google Fonts css2 API.

    css2 separates discrete weights with semicolons (wght@400;700) and ranges
    with double dots (wght@100..900). Legacy comma input ("400,700") is accepted
    and converted; explicit axis specs ("ital,wght@0,400;1,700") and ranges pass
    through untouched. Discrete lists are deduped and sorted (css2 rejects
    duplicates).
    """
    w = re.sub(r"\s+", "", str(weights))
    if not w:
        raise ValueError("weights must not be blank")
    if "@" in w:
        if w.count("@") != 1:
            raise ValueError("weights contain an invalid axis specification")
        axis_text, tuple_text = w.split("@", 1)
        axes = axis_text.split(",")
        if ("wght" not in axes or axes != sorted(axes) or len(axes) != len(set(axes))
                or any(not re.fullmatch(r"[a-z]{4}", axis) for axis in axes)):
            raise ValueError("weights contain an invalid axis specification")
        tuples = tuple_text.split(";")
        if any(len(values.split(",")) != len(axes) for values in tuples):
            raise ValueError("weights axis tuples do not match their axes")
        if any(not _valid_axis_value(value) for values in tuples for value in values.split(",")):
            raise ValueError("weights contain an invalid axis value")
        weight_index = axes.index("wght")
        if any(not _valid_explicit_weight(values.split(",")[weight_index]) for values in tuples):
            raise ValueError("weight axis values must be between 1 and 1000")
        tuples = sorted(set(tuples), key=_axis_tuple_sort_key)
        return f"{','.join(axes)}@{';'.join(tuples)}"
    if ".." in w:
        if not _valid_weight_range(w):
            raise ValueError("weights contain an invalid range")
        return w
    parts = {part for part in re.split(r"[;,]", w) if part}
    if not parts or any(not _valid_weight(part) for part in parts):
        raise ValueError("weights must contain integers from 1 to 1000")
    return ";".join(sorted(parts, key=int))


def _valid_weight(value):
    return value.isdigit() and 1 <= int(value) <= 1000


def _valid_weight_range(value):
    match = re.fullmatch(r"(\d+)\.\.(\d+)", value)
    return bool(match and _valid_weight(match.group(1)) and _valid_weight(match.group(2)) and int(match.group(1)) <= int(match.group(2)))


def _valid_axis_value(value):
    match = re.fullmatch(r"-?\d+(?:\.\d+)?(?:\.\.-?\d+(?:\.\d+)?)?", value)
    if not match:
        return False
    if ".." in value:
        start, end = (float(part) for part in value.split("..", 1))
        return start <= end
    return True


def _valid_explicit_weight(value):
    if ".." in value:
        return _valid_weight_range(value)
    return _valid_weight(value)


def _axis_tuple_sort_key(value):
    key = []
    for part in value.split(","):
        if ".." in part:
            start, end = (float(item) for item in part.split("..", 1))
        else:
            start = end = float(part)
        key.append((start, end))
    return tuple(key)


def _merge_weight_specs(first, second):
    first = normalize_weights(first)
    second = normalize_weights(second)
    if first == second:
        return first
    if "@" in first or "@" in second:
        if "@" not in first or "@" not in second:
            raise ValueError("same-family weights use incompatible axis specifications")
        first_axes, first_values = first.split("@", 1)
        second_axes, second_values = second.split("@", 1)
        if first_axes != second_axes:
            raise ValueError("same-family weights use incompatible axis specifications")
        values = set(first_values.split(";")) | set(second_values.split(";"))
        return f"{first_axes}@{';'.join(sorted(values, key=_axis_tuple_sort_key))}"
    if ".." in first or ".." in second:
        ranges = [value for value in (first, second) if ".." in value]
        discrete = [value for value in (first, second) if ".." not in value]
        if len(ranges) == 2:
            first_start, first_end = (int(value) for value in ranges[0].split(".."))
            second_start, second_end = (int(value) for value in ranges[1].split(".."))
            if first_start <= second_start and first_end >= second_end:
                return ranges[0]
            if second_start <= first_start and second_end >= first_end:
                return ranges[1]
            raise ValueError("same-family weight ranges are incompatible")
        start, end = (int(value) for value in ranges[0].split(".."))
        if all(start <= int(value) <= end for value in discrete[0].split(";")):
            return ranges[0]
        raise ValueError("same-family weights fall outside the variable range")
    values = set(first.split(";")) | set(second.split(";"))
    return ";".join(sorted(values, key=int))


def _family_param(font, weights):
    w = normalize_weights(weights)
    if "@" in w:
        return f"family={encode_font(font)}:{w}"
    return f"family={encode_font(font)}:wght@{w}"


def generate_embed(heading, body, heading_weights, body_weights):
    lines = ['<link rel="preconnect" href="https://fonts.googleapis.com">',
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>']
    families = []
    same_family = heading and body and heading.strip().casefold() == body.strip().casefold()
    if same_family:
        families.append(_family_param(heading, _merge_weight_specs(heading_weights, body_weights)))
    else:
        if heading:
            families.append(_family_param(heading, heading_weights))
        if body:
            families.append(_family_param(body, body_weights))
    if not families:
        raise ValueError("at least one font family is required")
    url = "https://fonts.googleapis.com/css2?" + "&".join(families) + "&display=swap"
    lines.append(f'<link href="{html.escape(url, quote=True)}" rel="stylesheet">')
    return "\n".join(lines)
