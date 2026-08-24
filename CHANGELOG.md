# Changelog

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
