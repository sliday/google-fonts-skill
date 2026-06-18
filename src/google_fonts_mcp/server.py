"""Google Fonts MCP Server — Typography system generator for agents."""

import sys

from fastmcp import FastMCP

from google_fonts_mcp.core import (
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


def _print_banner():
    try:
        from rich.console import Console, Group
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        console = Console(stderr=True)

        fonts = _load_csv("fonts")
        pairings = _load_csv("pairings")
        body_suitable = sum(1 for f in fonts if f.get("Body_Suitable") == "Yes")
        tier_a = sum(1 for f in fonts if f.get("Quality_Tier") == "A")

        # Header
        header = Text()
        header.append("  google-fonts-mcp", style="bold cyan")
        from google_fonts_mcp import __version__; header.append(f"  v{__version__}", style="dim")

        # What this is
        desc = Text("  Typography system generator for AI agents", style="italic dim")

        # Stats bar
        stats = Text()
        stats.append(f"  {len(fonts):,}", style="bold white")
        stats.append(" fonts  ", style="dim")
        stats.append(f"{len(pairings)}", style="bold white")
        stats.append(" pairings  ", style="dim")
        stats.append(f"{len(SCALES)}", style="bold white")
        stats.append(" scales  ", style="dim")
        stats.append(f"{tier_a}", style="bold white")
        stats.append(" tier-A  ", style="dim")
        stats.append(f"{body_suitable}", style="bold white")
        stats.append(" body-suitable", style="dim")

        # Tools table
        tools_header = Text("  Available tools:", style="bold white")
        tools = Table(show_header=False, box=None, padding=(0, 2, 0, 2))
        tools.add_column(style="cyan bold", min_width=32)
        tools.add_column(style="dim")
        tools.add_row("search_fonts", "Search by mood, use case, or style")
        tools.add_row("generate_typography_system", "CSS + Tailwind + embed link")
        tools.add_row("lookup_font", "Full metadata for any font")
        tools.add_row("list_scales", "8 modular type scales")
        tools.add_row("list_pairings", "73 proven font pairs")

        # Next steps
        next_steps = Text()
        next_steps.append("\n  How to connect:\n", style="bold white")
        next_steps.append("  Claude Code  ", style="dim")
        next_steps.append("claude mcp add google-fonts -- uvx google-fonts-mcp\n", style="green")
        next_steps.append("  Cursor       ", style="dim")
        next_steps.append("Add to .cursor/mcp.json\n", style="green")
        next_steps.append("  Any client   ", style="dim")
        next_steps.append("Connect via stdio to this process\n", style="green")

        links = Text()
        links.append("\n  Docs   ", style="dim")
        links.append("https://github.com/sliday/google-fonts-skill", style="blue underline")
        links.append("\n  Gallery ", style="dim")
        links.append("https://sliday.github.io/google-fonts-skill/", style="blue underline")

        content = Group(header, desc, Text(), stats, Text(), tools_header, tools, next_steps, links)

        panel = Panel(
            content,
            border_style="blue",
            padding=(1, 1),
        )
        console.print(panel)
        console.print("[dim]  Server ready. Waiting for MCP client connection (stdio)...[/dim]\n")
    except ImportError:
        print("google-fonts-mcp v1.1.0 | 1,923 fonts | 73 pairings | 5 tools", file=sys.stderr)
        print("Connect: claude mcp add google-fonts -- uvx google-fonts-mcp", file=sys.stderr)
        print("Waiting for MCP client connection (stdio)...", file=sys.stderr)


@mcp.tool
def search_fonts(
    query: str,
    mode: str = "single",
    tier: str | None = None,
    max_results: int = 5,
) -> list[dict]:
    """Search Google Fonts by description, mood, or use case.

    Modes:
    - single: Body-suitable fonts for heading + body (default)
    - pair: Proven font pairings with contrast type
    - scale: Typographic scales by use case

    Tier filter (A/B/C) applies to single mode only.
    """
    return _search_fonts(query, mode=mode, tier=tier, max_results=max_results)


def _validate_value(val: str, label: str, raw: str) -> None:
    """Validate a single <value>: either <float> or <float>..<float>."""
    if ".." in val:
        parts = val.split("..")
        if len(parts) != 2 or not all(p.strip() for p in parts):
            raise ValueError(f"{label} has an invalid range '{val}' ('{raw}'). Use 'float..float'.")
        for p in parts:
            _validate_float(p.strip(), label, raw)
    else:
        _validate_float(val.strip(), label, raw)


def _validate_float(s: str, label: str, raw: str) -> None:
    """Check a string parses as a valid float."""
    if not s:
        raise ValueError(f"{label} has an empty value ('{raw}').")
    try:
        v = float(s)
    except ValueError:
        raise ValueError(f"{label} contains '{s}', which is not a valid number ('{raw}').")


def parse_weights(raw: str, label: str) -> str:
    """Validate weight strings for the Google Fonts css2 API.

    https://developers.google.com/fonts/docs/css2#forming_api_urls
    """
    if not raw.strip():
        return raw

    # Auto-convert "i"-suffixed weights (from Styles column) to axis notation
    if "@" not in raw and any(p.strip().endswith("i") for p in raw.split(";")):
        upright = sorted(int(p.strip()) for p in raw.split(";") if not p.strip().endswith("i"))
        italic = sorted(int(p.strip()[:-1]) for p in raw.split(";") if p.strip().endswith("i"))
        tuples = [f"0,{w}" for w in upright] + [f"1,{w}" for w in italic]
        raw = "ital,wght@" + ";".join(tuples)

    if "@" in raw:
        # axis_tag_list@axis_tuple_list — e.g. "ital,wght@0,400;1,700"
        parts = raw.split("@")
        if len(parts) != 2:
            raise ValueError(
                f"{label} has an invalid axis specification ('{raw}'): "
                "use the format 'axis1,axis2@value1,value2;value1,value2'."
            )
        axis_spec, tuple_spec = parts
        axes = [a.strip() for a in axis_spec.split(",")]
        if not all(a for a in axes):
            raise ValueError(f"{label} has an empty axis tag ('{raw}'): axes must be comma-separated tags.")
        # Sorted alphabetically (en-US locale)
        if axes != sorted(axes, key=str.lower):
            raise ValueError(
                f"{label} has axes not in alphabetical order: {axes} ('{raw}'). "
                "Axis tags must be sorted alphabetically (e.g. 'ital,wght', not 'wght,ital')."
            )
        tuples = [t.strip() for t in tuple_spec.split(";")]
        if not all(t for t in tuples):
            raise ValueError(f"{label} has an empty tuple ('{raw}'): tuples must be semicolon-separated.")

        parsed = []
        for t in tuples:
            values = [v.strip() for v in t.split(",")]
            # Same length as axis_tag_list
            if len(values) != len(axes):
                raise ValueError(
                    f"{label} has {len(values)} values in tuple '{t}' but {len(axes)} axes "
                    f"('{raw}'). Each tuple must have one value per axis."
                )
            row = []
            for v in values:
                _validate_value(v, label, raw)
                if ".." in v:
                    lo, hi = v.split("..")
                    row.append((float(lo.strip()), float(hi.strip())))
                else:
                    n = float(v.strip())
                    row.append((n, n))
            parsed.append(row)

        # Sorted numerically + no overlap/touch
        for i in range(len(parsed) - 1):
            a, b, = parsed[i], parsed[i + 1]
            for axis_idx in range(len(axes)):
                amin, amax = a[axis_idx]
                bmin, bmax = b[axis_idx]
                if amax > bmin:
                    raise ValueError(
                        f"{label} has tuples not in numerical order ('{raw}'). "
                        "Tuples must be sorted numerically."
                    )
                if amax < bmin:
                    break
            else:
                raise ValueError(
                    f"{label} has tuples that overlap or touch ('{raw}'). "
                    "Tuples must not overlap or share boundary values."
                )
        return raw

    # Simple weights — semicolons for discrete, .. for ranges
    # Reject old css API comma syntax
    if "," in raw:
        raise ValueError(
            f"{label} contains commas ('{raw}'). "
            "Google Fonts css2 endpoint uses semicolons between discrete weights "
            "(e.g. '400;700'), not commas. Use semicolons instead."
        )

    # Reject bare dash — range syntax uses "..", not "-"
    if "-" in raw and ".." not in raw:
        raise ValueError(
            f"{label} contains a single dash ('{raw}'). "
            "Google Fonts css2 endpoint uses double-dot notation for weight ranges "
            "(e.g. '400..700'), not a dash. Use '..' instead."
        )

    parts = raw.replace("..", ";").split(";")
    for part in parts:
        part = part.strip()
        if not part:
            raise ValueError(f"{label} has an empty value ('{raw}').")
        try:
            val = int(part)
            if val < 100 or val > 1000:
                raise ValueError(
                    f"{label} contains '{part}', which is outside the valid weight range (100-1000)."
                )
        except ValueError:
            raise ValueError(
                f"{label} contains '{part}', which is not a valid weight number ('{raw}')."
            )

    return raw


@mcp.tool
def generate_typography_system(
    heading: str,
    body: str | None = None,
    scale: str = "major-third",
    base: int = 16,
    heading_weights: str = "400;700",
    body_weights: str = "300;400;500;600;700",
    format: str = "all",
) -> dict:
    """Generate a complete typography system from font selection + scale.

    Returns CSS custom properties, Tailwind config, and/or Google Fonts embed HTML.
    Format: css, tailwind, embed, or all.
    """
    heading_weights = parse_weights(heading_weights, "heading_weights")
    body_weights = parse_weights(body_weights, "body_weights")
    if body is None:
        body = heading
    ratio = SCALES.get(scale, 1.25)
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
    _print_banner()
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
