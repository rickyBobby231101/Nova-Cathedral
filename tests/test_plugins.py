"""
Tests for the hand-written Cathedral plugins (moon_phase, gematria).
Plugins are self-contained input->output classes; these load them straight
from the runtime plugin dir and exercise process() directly.
"""
import importlib.util
from pathlib import Path

import pytest

PLUGIN_DIR = Path.home() / "cathedral" / "plugins" / "auto"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, PLUGIN_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.get_plugin()(None)


@pytest.mark.skipif(not (PLUGIN_DIR / "moon_phase.py").exists(), reason="plugin not installed")
class TestMoonPhase:
    def test_known_full_moon(self):
        # 2026-12-25 is a full moon (verified against the synodic model live).
        r = _load("moon_phase").process({"date": "2026-12-25"})
        assert r["phase_name"] == "Full Moon"
        assert r["illumination_pct"] > 95

    def test_illumination_bounds(self):
        p = _load("moon_phase")
        for date in ("2026-01-01", "2026-06-15", "2027-03-03"):
            r = p.process({"date": date})
            assert 0 <= r["illumination_pct"] <= 100
            assert 0 <= r["age_days"] <= 29.6

    def test_bad_date(self):
        assert "error" in _load("moon_phase").process({"date": "nope"})

    def test_default_is_today(self):
        r = _load("moon_phase").process({})
        assert "phase_name" in r and "emoji" in r


@pytest.mark.skipif(not (PLUGIN_DIR / "gematria.py").exists(), reason="plugin not installed")
class TestGematria:
    def test_ordinal_value(self):
        # a=1..z=26; "abc" = 1+2+3 = 6
        r = _load("gematria").process({"text": "abc", "method": "ordinal"})
        assert r["value"] == 6
        assert r["reduced"] == 6

    def test_reduction_preserves_master_numbers(self):
        p = _load("gematria")
        # Build a word summing to 29 -> 2+9=11, a master number, must survive.
        # 'k'(11 ordinal->reduced 2) not needed; just check the reducer via a
        # known total: "value" 29 reduces to 11.
        assert p._reduce(29) == 11
        assert p._reduce(22) == 22
        assert p._reduce(38) == 11  # 3+8=11

    def test_pythagorean_differs_from_ordinal(self):
        p = _load("gematria")
        o = p.process({"text": "z", "method": "ordinal"})["value"]      # 26
        y = p.process({"text": "z", "method": "pythagorean"})["value"]  # 8
        assert o == 26 and y == 8

    def test_ignores_non_letters(self):
        r = _load("gematria").process({"text": "a-b-c!"})
        assert r["letters"] == 3
        assert r["value"] == 6

    def test_empty_and_bad_method(self):
        p = _load("gematria")
        assert "error" in p.process({"text": ""})
        assert "error" in p.process({"text": "abc", "method": "klingon"})
