"""Guards against the scripts/ vs src/ implementations drifting apart."""

import importlib.util
import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load_scripts_core():
    spec = importlib.util.spec_from_file_location("scripts_core", REPO / "scripts" / "core.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scripts_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_scripts_core_matches_package():
    scripts_core = _load_scripts_core()
    from google_fonts_mcp import core

    assert scripts_core.SCALES == core.SCALES
    assert scripts_core.compute_sizes(16, 1.25) == core.compute_sizes(16, 1.25)
    args = ("Playfair Display", "Inter", "400;700", "300;400;700")
    assert scripts_core.generate_embed(*args) == core.generate_embed(*args)
    single = ("Inter", "Inter", "400;700", "400;700")
    assert scripts_core.generate_embed(*single) == core.generate_embed(*single)


def test_versions_in_sync():
    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]
    from google_fonts_mcp import __version__

    plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())["version"]
    marketplace = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
    assert __version__ == pyproject == plugin
    assert marketplace["metadata"]["version"] == pyproject
    assert marketplace["plugins"][0]["version"] == pyproject


def test_packaged_data_matches_canonical_data():
    for name in ("fonts.csv", "pairings.csv", "scales.csv"):
        assert (REPO / "data" / name).read_bytes() == (REPO / "src" / "google_fonts_mcp" / "data" / name).read_bytes()
