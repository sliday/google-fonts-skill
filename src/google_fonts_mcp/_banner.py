"""Startup banner for the Google Fonts MCP server."""

import sys

from google_fonts_mcp import __version__
from google_fonts_mcp.core import SCALES, _load_csv


def print_banner():
    fonts = _load_csv("fonts")
    pairings = _load_csv("pairings")
    try:
        from rich.console import Console, Group
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        console = Console(stderr=True)

        body_suitable = sum(1 for f in fonts if f.get("Body_Suitable") == "Yes")
        tier_a = sum(1 for f in fonts if f.get("Quality_Tier") == "A")

        # Header
        header = Text()
        header.append("  google-fonts-mcp", style="bold cyan")
        header.append(f"  v{__version__}", style="dim")

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
        tools.add_row("list_scales", f"{len(SCALES)} modular type scales")
        tools.add_row("list_pairings", f"{len(pairings)} proven font pairs")

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
        print(f"google-fonts-mcp v{__version__} | {len(fonts):,} fonts | {len(pairings)} pairings | 5 tools", file=sys.stderr)
        print("Connect: claude mcp add google-fonts -- uvx google-fonts-mcp", file=sys.stderr)
        print("Waiting for MCP client connection (stdio)...", file=sys.stderr)
