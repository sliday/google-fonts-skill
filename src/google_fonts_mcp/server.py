"""Google Fonts MCP Server — Typography system generator for agents."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from google_fonts_mcp.core import (
    MAX_QUERY_LENGTH,
    MAX_RESULTS_LIMIT,
    SCALES,
    search_fonts as _search_fonts,
    compute_sizes,
    get_fallback,
    generate_css,
    generate_tailwind,
    generate_embed,
    _load_csv,
)

mcp = FastMCP("google-fonts")


@mcp.tool
def search_fonts(
    query: Annotated[str, Field(min_length=1, max_length=MAX_QUERY_LENGTH)],
    mode: Literal["single", "pair", "lookup", "scale"] = "single",
    tier: Literal["A", "B", "C"] | None = None,
    max_results: Annotated[int, Field(ge=1, le=MAX_RESULTS_LIMIT)] = 5,
) -> list[dict]:
    """Search Google Fonts by description, mood, or use case.

    Modes:
    - single: Body-suitable fonts for heading + body (default)
    - pair: Proven font pairings with contrast type
    - scale: Typographic scales by use case

    Tier filter (A/B/C) applies to single mode only.
    """
    return _search_fonts(query, mode=mode, tier=tier, max_results=max_results)


@mcp.tool
def generate_typography_system(
    heading: Annotated[str, Field(min_length=1, max_length=200)],
    body: Annotated[str, Field(min_length=1, max_length=200)] | None = None,
    scale: Literal["minor-second", "major-second", "minor-third", "major-third", "perfect-fourth", "augmented-fourth", "perfect-fifth", "golden-ratio"] = "major-third",
    base: Annotated[int, Field(ge=1, le=512)] = 16,
    heading_weights: Annotated[str, Field(min_length=1, max_length=200)] = "400;700",
    body_weights: Annotated[str, Field(min_length=1, max_length=200)] = "300;400;500;600;700",
    format: Literal["css", "tailwind", "embed", "all"] = "all",
) -> dict:
    """Generate a complete typography system from font selection + scale.

    Returns CSS custom properties, Tailwind config, and/or Google Fonts embed HTML.
    Format: css, tailwind, embed, or all.
    Weights: semicolon-separated per the css2 API (e.g. "400;700"); variable
    ranges use ".." (e.g. "100..900"). Legacy comma input is auto-converted.
    """
    heading = heading.strip()
    if not heading:
        raise ValueError("heading must not be blank")
    if len(heading) > 200:
        raise ValueError("heading must be at most 200 characters")
    if body is None:
        body = heading
    else:
        body = body.strip()
        if not body:
            raise ValueError("body must not be blank")
        if len(body) > 200:
            raise ValueError("body must be at most 200 characters")
    if scale not in SCALES:
        raise ValueError("scale is not supported")
    if not 1 <= base <= 512:
        raise ValueError("base must be between 1 and 512")
    if format not in {"css", "tailwind", "embed", "all"}:
        raise ValueError("format must be one of: css, tailwind, embed, all")
    ratio = SCALES[scale]
    sizes = compute_sizes(base, ratio)
    heading_fb = get_fallback(heading)
    body_fb = get_fallback(body) if body != heading else heading_fb

    result = {}
    if format in ("css", "all"):
        result["css"] = generate_css(heading, body, heading_fb, body_fb, sizes, scale, ratio, base)
    if format in ("tailwind", "all"):
        result["tailwind"] = generate_tailwind(heading, body, heading_fb, body_fb, sizes, scale, ratio, base)
    if format in ("embed", "all"):
        result["embed"] = generate_embed(heading, body, heading_weights, body_weights)
    return result


@mcp.tool
def lookup_font(name: str) -> dict | None:
    """Look up a specific Google Font by exact name. Returns full metadata."""
    results = _search_fonts(name, mode="lookup")
    return results[0] if results else None


@mcp.tool
def list_scales() -> list[dict]:
    """Return all 8 typographic scales with ratios and use-case recommendations."""
    return _load_csv("scales")


@mcp.tool
def list_pairings(category: str | None = None) -> list[dict]:
    """Return all 73 proven font pairings. Optionally filter by contrast type (Structure, Proportion, Era, Weight)."""
    rows = _load_csv("pairings")
    if category:
        cat_lower = category.strip().lower()
        rows = [r for r in rows if r.get("Contrast_Type", "").strip().lower() == cat_lower]
    return rows


def main():
    from google_fonts_mcp._banner import print_banner

    print_banner()
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
