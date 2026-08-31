#!/usr/bin/env python3
"""
Reads typography.csv and transforms it into pairings.csv for the auto-google-font skill.

Computes: Contrast_Type, Scale_Recommendation, Heading_Weights, Body_Weights
"""

import csv
import re
from pathlib import Path

INPUT = Path.home() / ".claude/skills/ui-ux-pro-max/data/typography.csv"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "pairings.csv"
PACKAGE_OUTPUT = Path(__file__).resolve().parent.parent / "src" / "google_fonts_mcp" / "data" / "pairings.csv"

PAIRING_OVERRIDES = {
    "Premium Sans": {
        "Heading_Font": "Plus Jakarta Sans",
        "Body_Font": "DM Sans",
        "Heading_Weights": "400;700",
        "Body_Weights": "400;500;700",
        "Google_Fonts_URL": "https://fonts.google.com/share?selection.family=Plus+Jakarta+Sans:wght@400;700|DM+Sans:wght@400;500;700",
        "CSS_Import": "@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');",
        "Notes": "Note: Google alternatives for Fontshare's Satoshi/General Sans.",
    },
    "Startup Bold": {
        "Heading_Font": "Outfit",
        "Body_Font": "Rubik",
        "Heading_Weights": "400;500;600;700",
        "Body_Weights": "300;400;500;600;700",
        "Google_Fonts_URL": "https://fonts.google.com/share?selection.family=Outfit:wght@400;500;600;700|Rubik:wght@300;400;500;600;700",
        "CSS_Import": "@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Rubik:wght@300;400;500;600;700&display=swap');",
        "Notes": "Note: Google alternatives for Fontshare's Clash Display/Satoshi.",
    },
}


def derive_contrast_type(category: str, heading: str, body: str) -> str:
    cat = category.strip().lower()
    if heading.strip().lower() == body.strip().lower():
        return "Weight"
    if cat == "serif + sans":
        return "Structure"
    if cat == "sans + sans":
        return "Proportion"
    if cat == "serif + serif":
        return "Era"
    if cat.startswith("display +"):
        return "Weight"
    if cat.startswith("script +"):
        return "Structure"
    if cat.startswith("mono +"):
        return "Structure"
    return "Proportion"


def derive_scale(best_for: str, mood: str) -> str:
    combined = (best_for + " " + mood).lower()
    if any(k in combined for k in ("dashboard", "admin", "data", "dense")):
        return "major-second"
    if any(k in combined for k in ("blog", "reading", "editorial", "content", "magazine")):
        return "major-third"
    if any(k in combined for k in ("marketing", "landing", "portfolio", "agency")):
        return "perfect-fourth"
    if any(k in combined for k in ("luxury", "fashion", "premium", "hero")):
        return "augmented-fourth"
    if any(k in combined for k in ("saas", "startup", "app", "corporate")):
        return "minor-third"
    if any(k in combined for k in ("children", "playful", "gaming", "fun")):
        return "minor-third"
    return "major-third"


def parse_weights_from_css(css_import: str, font_name: str) -> str:
    """Extract wght@ values for a specific font from the CSS import URL."""
    url_name = font_name.strip().replace(" ", "+")
    pattern = r"family=" + re.escape(url_name) + r"(?=[:&])(?::([^&'\"]+))?"
    match = re.search(pattern, css_import)
    if not match or not match.group(1):
        return "400"
    spec = match.group(1)
    if "@" not in spec:
        return "400"
    axes_text, values_text = spec.split("@", 1)
    axes = axes_text.split(",")
    if "wght" not in axes:
        return "400"
    weight_index = axes.index("wght")
    weights = []
    for axis_tuple in values_text.split(";"):
        values = axis_tuple.split(",")
        if len(values) != len(axes):
            return "400"
        weights.append(values[weight_index])
    return ";".join(dict.fromkeys(weights))


def main():
    rows = []
    with open(INPUT, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            heading = row["Heading Font"]
            body = row["Body Font"]
            category = row["Category"]
            best_for = row["Best For"]
            mood = row["Mood/Style Keywords"]
            css_import = row["CSS Import"]

            pairing = {
                "Pairing_Name": row["Font Pairing Name"],
                "Category": category,
                "Heading_Font": heading,
                "Body_Font": body,
                "Mood_Keywords": mood,
                "Best_For": best_for,
                "Contrast_Type": derive_contrast_type(category, heading, body),
                "Scale_Recommendation": derive_scale(best_for, mood),
                "Heading_Weights": parse_weights_from_css(css_import, heading),
                "Body_Weights": parse_weights_from_css(css_import, body),
                "Google_Fonts_URL": row["Google Fonts URL"],
                "CSS_Import": css_import,
                "Notes": row["Notes"],
            }
            pairing.update(PAIRING_OVERRIDES.get(pairing["Pairing_Name"], {}))
            rows.append(pairing)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Pairing_Name", "Category", "Heading_Font", "Body_Font",
        "Mood_Keywords", "Best_For", "Contrast_Type", "Scale_Recommendation",
        "Heading_Weights", "Body_Weights", "Google_Fonts_URL", "CSS_Import", "Notes",
    ]
    for output in (OUTPUT, PACKAGE_OUTPUT):
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    print(f"Produced {len(rows)} pairings -> {OUTPUT} and {PACKAGE_OUTPUT}")


if __name__ == "__main__":
    main()
