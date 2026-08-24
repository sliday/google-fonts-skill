"""Compatibility shim over the canonical implementation in src/google_fonts_mcp/core.py.

Scripts run from a repo checkout without installing the package, so this file
puts src/ on sys.path and points the package's data loader at the repo-level
data/ directory. All logic lives in google_fonts_mcp.core — fix bugs there.
"""

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
os.environ.setdefault("GOOGLE_FONTS_MCP_DATA", str(_REPO_ROOT / "data"))

from google_fonts_mcp.core import (  # noqa: E402,F401
    BM25,
    CSV_CONFIG,
    LETTER_SPACINGS,
    LINE_HEIGHTS,
    MARGIN_BOTTOMS,
    MAX_RESULTS,
    SCALES,
    TIERS,
    _load_csv,
    _search_csv,
    compute_sizes,
    encode_font,
    fmt_rem,
    generate_css,
    generate_embed,
    generate_tailwind,
    normalize_weights,
    search_fonts,
)
from google_fonts_mcp.core import get_fallback as _pkg_get_fallback  # noqa: E402
from google_fonts_mcp.core import lookup_category as _pkg_lookup_category  # noqa: E402

DATA_DIR = _REPO_ROOT / "data"
PROJECT_ROOT = str(_REPO_ROOT)


def lookup_category(font_name, data_dir=None):
    """Back-compat wrapper; data_dir is ignored (repo data/ is preconfigured)."""
    return _pkg_lookup_category(font_name)


def get_fallback(font_name, data_dir=None):
    """Back-compat wrapper; data_dir is ignored (repo data/ is preconfigured)."""
    return _pkg_get_fallback(font_name)


def search(query, config_key, max_results=MAX_RESULTS):
    """Back-compat wrapper around the shared BM25 CSV search."""
    return _search_csv(query, config_key, max_results)
