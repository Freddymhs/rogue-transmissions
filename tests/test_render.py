#!/usr/bin/env python3
"""tests/test_render.py — validate JSON schema + render output."""
import json, sys, pathlib, subprocess, pytest

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data" / "transmissions.json"
TEMPLATE = ROOT / "template.html"


def test_data_json_loads():
    assert DATA.exists(), f"missing {DATA}"
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert "days" in data
    assert isinstance(data["days"], list)
    assert len(data["days"]) >= 1


def test_data_day_shape():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    for day in data["days"]:
        assert "date" in day
        assert "open" in day
        assert "entries" in day
        assert isinstance(day["entries"], list)
        for e in day["entries"]:
            assert "time" in e
            assert "type" in e
            assert "body_html" in e
            assert e["type"] in ("plain", "found", "verified", "hypothesis")


def test_data_mystery_and_hypothesis():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert isinstance(data.get("mystery"), list)
    assert isinstance(data.get("hypothesis"), list)
    for h in data["hypothesis"]:
        assert {"label", "pct", "text"} <= set(h.keys())


def test_template_has_placeholders():
    template = TEMPLATE.read_text(encoding="utf-8")
    for marker in ("BEGIN_DAYS", "BEGIN_MYSTERY", "BEGIN_HYPOTHESIS"):
        assert f"<!-- {marker} -->" in template, f"missing marker {marker}"


def test_render_runs():
    result = subprocess.run(
        ["python3", str(ROOT / "render.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"render failed: {result.stderr}"


def test_render_output_valid_html():
    subprocess.run(["python3", str(ROOT / "render.py")], check=True)
    out = (ROOT / "index.html").read_text(encoding="utf-8")
    # markers appear exactly once each (as boundaries, not duplicated)
    for marker in ("BEGIN_DAYS", "BEGIN_MYSTERY", "BEGIN_HYPOTHESIS"):
        assert out.count(marker) == 1, f"{marker} should appear once"
    # structure present
    assert '<details class="day"' in out
    assert "Hipótesis" in out
    assert "GENERADA POR IA" in out or "generada por IA" in out
    # no unbalanced tags (basic sanity)
    assert out.count("<details") == out.count("</details>")


def test_render_idempotent():
    """Re-running render produces identical output."""
    subprocess.run(["python3", str(ROOT / "render.py")], check=True)
    first = (ROOT / "index.html").read_text(encoding="utf-8")
    subprocess.run(["python3", str(ROOT / "render.py")], check=True)
    second = (ROOT / "index.html").read_text(encoding="utf-8")
    assert first == second, "render is not idempotent"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))