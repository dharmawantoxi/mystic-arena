"""Source oracle for layer 9b: the ingame hero balance baseline.

The user unlocked rebalance work; the project doctrine (`hero_balance.py`
header, `tools/balance_audit.py`) is that balance changes answer to MEASURED
metrics, not opinions. The source Python stays read-only, so this oracle pins
the current post-balance catalog as the golden baseline every future native
rebalance slice must intentionally move:

* runs `tools/balance_audit.py --ingame` (the project's own audit tool, same
  formulas as the hero_balance pass) headlessly: a self-written MagicMock
  pygame stub is injected through PYTHONPATH, so no engine/display/pygame
  install is needed in CI (same trick the effect_manager oracle line uses);
* asserts the audit's own health targets hold (violations == [], plus the
  TARGETS bands and the redistribution power anchors);
* pins the exact metric snapshot and writes it to
  `tests/fixtures/balance_baseline_ingame.json` for the native suite.

Measured baseline (2026-10-16): corr(HP,DPS) 0.535 (<= 0.80), identity
spread 1.64x (>= 1.20), school ratio 1.000/1.001 (0.90..1.15), boss pref
1.49 (>= 1.20), price spread 1.89x (<= 2.20), pool power delta 1.0/1.0
(redistribution, max 0.12), starter gap 5.67x, balance pass applied to 216
boss heroes, violations [].

Run: python godot_rebuild/tests/balance_baseline_source_oracle.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_TOOL = ROOT / "tools" / "balance_audit.py"
HERO_BALANCE = ROOT / "hero_balance.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "balance_baseline_ingame.json"

# Headless pygame stub: `_core` only needs the import to succeed; the audit
# math is pure Python over the hero/boss catalogs.
PYGAME_STUB = '''"""Minimal headless pygame stub for source-oracle imports (CI parity)."""
from unittest.mock import MagicMock

_mod = MagicMock()


def __getattr__(name):
    return getattr(_mod, name)


display = _mod.display
Surface = _mod.Surface
Color = _mod.Color
Vector2 = _mod.Vector2
font = _mod.font
image = _mod.image
draw = _mod.draw
time = _mod.time
event = _mod.event
key = _mod.key
mouse = _mod.mouse
locals = _mod.locals
transform = _mod.transform
mixer = _mod.mixer
math = _mod.math
Rect = _mod.Rect
SRCALPHA = 0
QUIT = 0
K_ESCAPE = 0
'''


def _run_ingame_audit():
    """Run tools/balance_audit.py --ingame under the headless stub."""
    with tempfile.TemporaryDirectory() as stub_dir:
        (Path(stub_dir) / "pygame.py").write_text(PYGAME_STUB, encoding="utf-8")
        env = dict(os.environ)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = stub_dir + (os.pathsep + existing if existing else "")
        env["SDL_VIDEODRIVER"] = "dummy"
        out_path = Path(stub_dir) / "audit.json"
        proc = subprocess.run(
            [sys.executable, str(AUDIT_TOOL), "--json", str(out_path)],
            env=env, capture_output=True, text=True, cwd=str(ROOT))
        assert proc.returncode == 0, proc.stderr[-3000:]
        return json.loads(out_path.read_text(encoding="utf-8"))


def _balance_switches():
    text = HERO_BALANCE.read_text(encoding="utf-8")
    switches = {}
    for name in ("ENABLE_REBUDGET", "ENABLE_SCHOOL_MOD", "ENABLE_STARTER_CATCHUP"):
        match = re.search(r"^%s\s*=\s*(True|False)" % name, text, re.MULTILINE)
        assert match, "hero_balance.py must keep the %s switch" % name
        switches[name] = match.group(1) == "True"
    return switches


def balance_baseline():
    audit = _run_ingame_audit()
    assert audit["mode"] == "ingame", audit["mode"]
    assert audit["n_hero"] == 222 and audit["n_boss_hero"] == 216
    assert audit["violations"] == [], audit["violations"]
    # The audit tool's own TARGETS bands (tools/balance_audit.py:47-55).
    assert audit["corr_hp_dps"] <= 0.80, audit["corr_hp_dps"]
    assert audit["identity_spread_x"] >= 1.20, audit["identity_spread_x"]
    for mode in ("mini", "true"):
        ratio = audit["effective_dps_vs_boss"][mode]["ratio_magic_over_phys"]
        assert 0.90 <= ratio <= 1.15, (mode, ratio)
    assert audit["boss_pref_ratio"] >= 1.20, audit["boss_pref_ratio"]
    assert audit["price_spread_x"] <= 2.20, audit["price_spread_x"]
    delta = audit["pool_power_delta"]
    assert abs(delta["dps_x"] - 1.0) <= 0.12 and abs(delta["ehp_x"] - 1.0) <= 0.12, delta
    # Exact snapshot pins (deterministic arithmetic over the frozen source
    # catalog - any movement means the catalog or the audit changed).
    assert audit["corr_hp_dps"] == 0.535, audit["corr_hp_dps"]
    assert audit["identity_spread_x"] == 1.64, audit["identity_spread_x"]
    assert audit["boss_pref_ratio"] == 1.49, audit["boss_pref_ratio"]
    assert audit["price_spread_x"] == 1.89, audit["price_spread_x"]
    assert audit["starter_gap"]["gap_x"] == 5.67, audit["starter_gap"]
    assert audit["balance_pass"]["applied_to"] == 216, audit["balance_pass"]
    assert audit["balance_pass"]["hp_mult"] == [0.7189, 1.3868], audit["balance_pass"]
    assert audit["balance_pass"]["dmg_mult"] == [0.5851, 2.0474], audit["balance_pass"]
    assert audit["hero_level_curve"] == {
        "max_level": 15, "dmg_mult": 10.0, "hp_mult": 12.5}, audit["hero_level_curve"]
    switches = _balance_switches()
    assert switches == {
        "ENABLE_REBUDGET": True,
        "ENABLE_SCHOOL_MOD": False,
        "ENABLE_STARTER_CATCHUP": True,
    }, switches
    return {
        "source": "tools/balance_audit.py --ingame (headless pygame stub)",
        "switches": switches,
        "audit": audit,
    }


def main():
    fixture = balance_baseline()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    audit = fixture["audit"]
    print("balance_baseline: ingame corr %.3f | spread %.2fx | school %.3f/%.3f | "
          "boss-pref %.2f | price %.2fx | starter gap %.2fx | violations %d"
          % (audit["corr_hp_dps"], audit["identity_spread_x"],
             audit["effective_dps_vs_boss"]["mini"]["ratio_magic_over_phys"],
             audit["effective_dps_vs_boss"]["true"]["ratio_magic_over_phys"],
             audit["boss_pref_ratio"], audit["price_spread_x"],
             audit["starter_gap"]["gap_x"], len(audit["violations"])))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
