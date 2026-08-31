import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def load_script(name):
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pairing_weight_parser_handles_explicit_axes():
    module = load_script("build-pairings")
    css = "@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');"
    assert module.parse_weights_from_css(css, "Playfair Display") == "400;700"
    prefix_css = "@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700&family=Barlow:wght@300;400;700&display=swap');"
    assert module.parse_weights_from_css(prefix_css, "Barlow") == "300;400;700"
    assert module.PAIRING_OVERRIDES["Premium Sans"]["Heading_Font"] == "Plus Jakarta Sans"


def test_enrichment_refuses_to_overwrite_on_fetch_failure(tmp_path, monkeypatch):
    module = load_script("fetch-and-enrich")
    base = tmp_path / "base.csv"
    base.write_text("Family,Category\nInter,Sans Serif\n")
    output = tmp_path / "fonts.csv"
    output.write_text("keep\n")
    monkeypatch.setattr(module, "BASE_CSV", str(base))
    monkeypatch.setattr(module, "OUTPUT_CSV", str(output))
    monkeypatch.setattr(module, "fetch_url", lambda _url: None)
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 1
    assert output.read_text() == "keep\n"


def test_markdown_cell_escapes_table_delimiters():
    module = load_script("generate-llms-full")
    assert module.markdown_cell("calm|warm\nclean") == "calm\\|warm clean"


def test_og_poll_stops_after_three_transport_errors(monkeypatch):
    module = load_script("generate-og-images")
    calls = 0

    def fail(_request, timeout):
        nonlocal calls
        calls += 1
        raise OSError("offline")

    monkeypatch.setattr(module.urllib.request, "urlopen", fail)
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    assert module.poll_prediction("https://api.replicate.com/v1/predictions/test") is None
    assert calls == 3


def test_cli_rejects_conflicting_or_misleading_options():
    css = subprocess.run(
        [sys.executable, REPO / "scripts" / "generate-css.py", "--font", "Inter", "--body", "Roboto"],
        capture_output=True,
        text=True,
    )
    search = subprocess.run(
        [sys.executable, REPO / "scripts" / "search.py", "clean", "--mode", "pair", "--tier", "A"],
        capture_output=True,
        text=True,
    )
    assert css.returncode == 2
    assert "--body cannot be used with --font" in css.stderr
    assert search.returncode == 2
    assert "--tier is only supported in single mode" in search.stderr
