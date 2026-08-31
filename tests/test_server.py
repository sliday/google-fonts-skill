"""Tests for google_fonts_mcp.server tools."""

import pytest

from google_fonts_mcp.server import (
    search_fonts, generate_typography_system, lookup_font,
    list_scales, list_pairings,
)


def test_search_fonts_tool():
    results = search_fonts("modern SaaS dashboard", mode="single", max_results=3)
    assert isinstance(results, list)
    assert len(results) > 0


def test_generate_typography_system_single():
    result = generate_typography_system(heading="Inter", scale="major-third", format="all")
    assert "css" in result
    assert "tailwind" in result
    assert "embed" in result
    assert "--font-body" in result["css"]


def test_generate_typography_system_pair():
    result = generate_typography_system(
        heading="Playfair Display", body="Inter",
        scale="perfect-fourth", format="css"
    )
    assert "css" in result
    assert "--font-heading" in result["css"]


def test_lookup_font_exists():
    result = lookup_font("Inter")
    assert result is not None
    assert result["Family"] == "Inter"


def test_lookup_font_missing():
    result = lookup_font("NonExistentFont12345")
    assert result is None


def test_list_scales():
    scales = list_scales()
    assert len(scales) == 8
    assert scales[0]["Scale_Name"] is not None


def test_list_pairings_all():
    pairings = list_pairings()
    assert len(pairings) == 73


def test_list_pairings_filtered():
    pairings = list_pairings(category="Structure")
    assert len(pairings) > 0
    assert all(p["Contrast_Type"] == "Structure" for p in pairings)


def test_generate_typography_system_defaults():
    """Default call must produce a css2-valid embed (regression for issue #1)."""
    result = generate_typography_system(heading="Inter")
    assert set(result) == {"css", "tailwind", "embed"}
    assert "--font-size-base: 1rem" in result["css"]
    embed = result["embed"]
    href = next(line for line in embed.splitlines() if "css2" in line)
    assert href.count("family=") == 1
    assert "Inter:wght@" in href
    axis = href.split("wght@", 1)[1].split("&")[0]
    assert "," not in axis
    assert "400" in axis and "700" in axis


@pytest.mark.parametrize(
    "kwargs",
    [
        {"heading": ""},
        {"heading": "Inter", "body": " "},
        {"heading": "Inter", "scale": "bogus"},
        {"heading": "Inter", "base": 0},
        {"heading": "Inter", "format": "bogus"},
    ],
)
def test_generate_typography_system_rejects_invalid_inputs(kwargs):
    with pytest.raises((KeyError, ValueError)):
        generate_typography_system(**kwargs)
