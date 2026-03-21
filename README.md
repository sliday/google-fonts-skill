# Google Fonts Skill

Claude Code skill for typography system generation using Google Fonts. Searches 1,923 enriched fonts, suggests singles or pairs, and generates complete CSS/Tailwind typographic systems.

## What It Does

- **Font search** with BM25 ranking across personality, mood, and use-case tags
- **Single font mode** — one font for heading + body (body-suitable, multi-weight)
- **Pair mode** — 73 proven pairings with contrast type classification
- **CSS generation** — custom properties, Tailwind config, Google Fonts embed links
- **8 modular scales** — from minor-second (dense UI) to golden-ratio (hero sections)

## Installation

Copy to your Claude Code skills directory:

```bash
cp -r . ~/.claude/skills/google-fonts
```

Or clone directly:

```bash
git clone https://github.com/sliday/google-fonts-skill.git ~/.claude/skills/google-fonts
```

## Usage

The skill activates automatically when you mention fonts, typography, or type scales in Claude Code.

### CLI Scripts

```bash
# Search for a single body-suitable font
python3 scripts/search.py "modern clean SaaS" --mode single

# Search proven font pairings
python3 scripts/search.py "elegant editorial luxury" --mode pair

# Look up a specific font
python3 scripts/search.py "Inter" --mode lookup

# Search type scales
python3 scripts/search.py "marketing bold" --mode scale

# Generate CSS + Tailwind + embed for a single font
python3 scripts/generate-css.py --font "Inter" --scale major-third --format all

# Generate for a font pair
python3 scripts/generate-css.py --heading "Playfair Display" --body "Inter" \
  --scale perfect-fourth --format all
```

## Data

| File | Records | Description |
|------|---------|-------------|
| `data/fonts.csv` | 1,923 | Google Fonts with personality, contrast, body-suitability, quality tier |
| `data/pairings.csv` | 73 | Proven pairings with contrast type and scale recommendations |
| `data/scales.csv` | 8 | Modular type scales with sizes, line-heights, letter-spacing |

## Scale Reference

| Scale | Ratio | Best For |
|-------|-------|----------|
| minor-second | 1.067 | Dense UI, dashboards |
| major-second | 1.125 | Apps, admin panels |
| minor-third | 1.2 | General purpose |
| major-third | 1.25 | Blogs, content |
| perfect-fourth | 1.333 | Marketing, editorial |
| augmented-fourth | 1.414 | Magazines, expressive |
| perfect-fifth | 1.5 | Display-heavy |
| golden-ratio | 1.618 | Hero sections |

## Project Structure

```
├── SKILL.md                          # Claude Code skill definition
├── CLAUDE.md                         # Project instructions
├── data/
│   ├── fonts.csv                     # Enriched font database
│   ├── pairings.csv                  # Proven font pairings
│   └── scales.csv                    # Modular type scales
├── scripts/
│   ├── core.py                       # BM25 search engine
│   ├── search.py                     # CLI search interface
│   ├── generate-css.py               # CSS/Tailwind generator
│   ├── fetch-and-enrich.py           # Font data enrichment pipeline
│   └── build-pairings.py             # Pairing data builder
└── references/
    ├── typographic-rhythm.md         # Scale math and spacing rules
    └── pairing-principles.md         # Contrast theory and decision trees
```

## License

MIT
