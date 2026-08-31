# Changelog

## 1.4.1 — 2026-08-31

### Fixed
- Removed the unpublished npm launcher, package metadata, tests, and documentation.
- Version parity tests no longer require `package.json`.
- Source distributions now include the scripts, canonical data, and plugin metadata
  required by their included parity tests.

## 1.4.0 — 2026-08-31

### Security
- Escaped font names for CSS and Tailwind output, URL-encoded Google Fonts families,
  HTML-escaped embed URLs, and rejected malformed css2 weight specifications.
- Bounded MCP query length, result count, font names, base size, and documented enums.
- Upgraded the locked FastMCP dependency graph and pinned the build backend plus all
  GitHub Actions to reviewed commit SHAs.
- Enrichment now fails closed when required upstream metadata is unavailable and writes
  `fonts.csv` atomically. Replicate polling stops after three consecutive transport errors.

### Fixed
- Single-font embeds now merge heading and body weights instead of dropping body weights.
- Non-default base sizes now affect generated rem values; zero and negative bases fail
  with a validation error.
- Pairing regeneration preserves explicit `ital,wght` tuples and the two Google-only
  replacements for Fontshare families.
- Agent-reference Markdown escapes pipe-delimited data, and showcase color hashing marks
  MD5 as non-security use.
- CLI scripts reject conflicting `--font`/`--body`, tier filters outside single mode,
  and out-of-range result limits.

### Added
- Regression coverage for generated-code injection, input bounds, generator failure paths,
  CLI conflicts, and packaged-data parity.

## 1.3.1 — 2026-08-24

### Fixed
- **Broken Google Fonts embed URLs** (#1): `generate_embed` emitted comma-separated
  weights (`wght@400,700`), which the css2 API rejects with HTTP 400. New
  `normalize_weights()` converts legacy commas to semicolons, dedupes and sorts
  discrete weights, and passes through `..` ranges and explicit axis specs
  (`ital,wght@0,400;1,700`). Covers the MCP server, CLI scripts, and showcase.
  Thanks @tamasys for the report and PR.
- Showcase generator corrupted correct CSV data into comma/dash URL syntax; static
  fonts now use discrete weights from the Styles column (ranges 400 on static
  fonts), variable fonts use `..` ranges. All 100 gallery pages regenerated —
  every embed URL now returns HTTP 200.
- Pairings "Premium Sans" and "Startup Bold" referenced Fontshare fonts not on
  Google Fonts; replaced with the Google alternatives their notes named
  (Plus Jakarta Sans + DM Sans, Outfit + Rubik).
- Startup banner fallback reported stale v1.1.0; version and counts now derive
  from the package.

### Changed
- `scripts/core.py` is now a thin shim over `google_fonts_mcp.core` — one
  implementation instead of two drifting copies (parity-tested).
- Banner extracted to `_banner.py`; `server.py` is tools-only.
- MCP tool and CLI weight defaults use css2 syntax (`400;700`).
- SKILL.md: MCP-tools note, full fonts.csv schema, lookup/scale modes, css2 rule.

### Added
- LICENSE file (MIT was declared but missing; now shipped in wheel + sdist).
- Test suite grown 4 → 27: css2 grammar regression, weight normalization, exact
  scale math, CSV schema, version sync, scripts↔package parity.
- pytest declared as dev dependency; CI runs tests before publishing.
- `fastmcp` capped `<4`.
