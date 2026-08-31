"""Tests for google_fonts_mcp.core."""

import pytest

from google_fonts_mcp.core import (
    BM25, SCALES, _load_csv, compute_sizes, generate_css, generate_embed,
    generate_tailwind, get_fallback, normalize_weights, search_fonts,
)


def test_search_single():
    results = search_fonts("modern clean", mode="single", max_results=3)
    assert len(results) > 0
    assert "Family" in results[0]


def test_search_pair():
    results = search_fonts("elegant luxury", mode="pair", max_results=3)
    assert len(results) > 0
    assert "Heading_Font" in results[0]


def test_search_scale():
    results = search_fonts("dense compact", mode="scale", max_results=2)
    assert len(results) > 0
    assert "Scale_Name" in results[0]


def test_lookup():
    results = search_fonts("Inter", mode="lookup")
    assert len(results) == 1
    assert results[0]["Family"] == "Inter"


def test_compute_sizes():
    sizes = compute_sizes(16, 1.25)
    assert sizes["base"] == 1.0
    assert sizes["lg"] > 1.0
    assert sizes["sm"] < 1.0


def test_compute_sizes_honors_non_default_base():
    assert compute_sizes(20, 1.25)["base"] == 1.25
    with pytest.raises(ValueError, match="greater than zero"):
        compute_sizes(0, 1.25)


def test_get_fallback():
    fb = get_fallback("Inter")
    assert fb == "sans-serif"


def test_generate_css():
    sizes = compute_sizes(16, SCALES["major-third"])
    css = generate_css("Inter", "Inter", "sans-serif", "sans-serif", sizes, "major-third", 1.25, 16)
    assert ":root {" in css
    assert "--font-body" in css
    assert "--font-size-base: 1rem" in css


def test_generate_embed():
    embed = generate_embed("Playfair Display", "Inter", "400;700", "300;400;700")
    assert "fonts.googleapis.com" in embed
    assert "Playfair+Display" in embed
    assert "Inter" in embed
    assert ":wght@400;700" in embed
    assert ":wght@300;400;700" in embed


def test_generate_embed_css2_grammar():
    """css2 rejects comma-separated weights (issue #1); legacy input must normalize."""
    embed = generate_embed("Playfair Display", "Inter", "400,700", "300,400,500,600,700")
    href = next(line for line in embed.splitlines() if "fonts.googleapis.com/css2" in line)
    assert "wght@400;700" in href
    assert "wght@300;400;500;600;700" in href
    for param in href.split("&"):
        if "wght@" in param:
            axis = param.split("wght@", 1)[1].split("&")[0].rstrip('" ').split('"')[0]
            assert "," not in axis, f"comma in weight axis: {param}"


def test_generate_embed_pair_and_single_families():
    pair = generate_embed("Playfair Display", "Inter", "400;700", "300")
    href = next(line for line in pair.splitlines() if "css2" in line)
    assert href.count("family=") == 2
    single = generate_embed("Inter", "Inter", "400;700", "300")
    href = next(line for line in single.splitlines() if "css2" in line)
    assert href.count("family=") == 1


def test_generate_embed_merges_same_family_weights():
    embed = generate_embed("Inter", "Inter", "700", "300;400;500")
    href = next(line for line in embed.splitlines() if "css2" in line)
    assert href.count("family=") == 1
    assert "Inter:wght@300;400;500;700" in href


def test_normalize_weights():
    assert normalize_weights("400,700") == "400;700"
    assert normalize_weights("400;700") == "400;700"
    assert normalize_weights("700;400;400") == "400;700"  # dedupe + sort (css2 400s on dupes)
    assert normalize_weights("100..900") == "100..900"  # variable range passthrough
    assert normalize_weights("ital,wght@0,400;1,700") == "ital,wght@0,400;1,700"  # axis passthrough


@pytest.mark.parametrize("weights", [
    "", "400;evil", "400..100", '400\" onload=\"x', "ital,wght@0,400;1",
    "wght,ital@400,0", "wght,wght@400,700", "wght@1001",
])
def test_normalize_weights_rejects_invalid_specs(weights):
    with pytest.raises(ValueError):
        normalize_weights(weights)


def test_explicit_axis_specs_sort_and_dedupe_tuples():
    assert normalize_weights("wght@700;400;700") == "wght@400;700"
    embed = generate_embed("Inter", "inter", "wght@700", "wght@1000")
    assert "Inter:wght@700;1000" in embed


def test_generated_outputs_escape_font_names():
    font = "Bad'; color: red; /*\nnext</style></script>"
    sizes = compute_sizes(16, 1.25)
    css = generate_css(font, font, "sans-serif", "sans-serif", sizes, "major-third", 1.25, 16)
    tailwind = generate_tailwind(font, font, "sans-serif", "sans-serif", sizes, "major-third", 1.25, 16)
    embed = generate_embed('Inter\" onload=\"alert(1)', None, "400", "400")
    assert "--font-body: 'Bad\\'; color: red; /*\\a next\\3c /style\\3e \\3c /script\\3e ', sans-serif;" in css
    assert 'body: ["Bad\'; color: red; /*\\nnext\\u003c/style\\u003e\\u003c/script\\u003e", "sans-serif"],' in tailwind
    assert "</style>" not in css
    assert "</script>" not in tailwind
    assert ' onload="' not in embed
    assert "Inter%22+onload%3D%22alert%281%29" in embed


def test_bm25_refit_replaces_previous_corpus():
    bm25 = BM25()
    bm25.fit(["alpha"])
    bm25.fit(["beta", "beta gamma"])
    assert len(bm25.score("beta")) == 2
    assert all(score > 0 for score in bm25.score("beta"))


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"query": "", "mode": "single"}, "blank"),
        ({"query": "x" * 501, "mode": "single"}, "at most"),
        ({"query": "clean", "mode": "typo"}, "mode"),
        ({"query": "clean", "mode": "pair", "tier": "A"}, "single mode"),
        ({"query": "clean", "mode": "single", "max_results": 0}, "between"),
    ],
)
def test_search_rejects_invalid_inputs(kwargs, message):
    with pytest.raises(ValueError, match=message):
        search_fonts(**kwargs)


def test_compute_sizes_exact():
    sizes = compute_sizes(16, 1.25)
    assert sizes == {"xs": 0.64, "sm": 0.8, "base": 1.0, "lg": 1.25,
                     "xl": 1.5625, "2xl": 1.9531, "3xl": 2.4414, "4xl": 3.0518}
    vals = list(sizes.values())
    assert vals == sorted(vals)


def test_csv_required_columns():
    from google_fonts_mcp.core import CSV_CONFIG, _load_csv
    for key in ("fonts", "pairings", "scales"):
        rows = _load_csv(key)
        assert rows, f"{key} csv empty"
        cols = set(rows[0].keys())
        need = set(CSV_CONFIG[key]["search_cols"]) | set(CSV_CONFIG[key]["output_cols"])
        missing = need - cols
        assert not missing, f"{key} csv missing columns: {missing}"


def test_load_scales():
    scales = _load_csv("scales")
    assert len(scales) == 8


def test_load_pairings():
    pairings = _load_csv("pairings")
    assert len(pairings) == 73


def test_load_fonts():
    fonts = _load_csv("fonts")
    assert len(fonts) > 1900
