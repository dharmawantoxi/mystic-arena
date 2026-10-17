"""Source oracle for the `mobile/combat_audio.py` port (layer 9ar).

The source combat-sound layer is a GATE in front of the mixer: seven sound
kinds (hero melee/ranged, four tower shots, minion hit), each with a base
volume and a minimum spacing, a budget of four new sounds per frame, a
channel lookup that never steals, and a master*sfx volume read from the
SoundManager. Towers/heroes/minions/bosses call it from their attack code.

This oracle executes the REAL module under a pygame shim whose clock,
channel availability and SoundManager volume are scriptable (the sound
files are discovered from the real `assets/sounds` directory through the
real `init()`), then records every decision of a scripted request stream so
the native gate (`scripts/audio/combat_audio.gd`) replays it exactly.

Run: python godot_rebuild/tests/combat_audio_source_oracle.py
"""
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mobile" / "combat_audio.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "combat_audio_source.json"


class _Clock:
    ms = 0


class _Sound:
    def __init__(self, path):
        self.path = Path(path).name
        self.volume = None

    def set_volume(self, value):
        self.volume = value


class _Channel:
    def __init__(self):
        self.played = None

    def play(self, sound):
        self.played = sound


class _Mixer:
    free_channels = 24
    Sound = _Sound

    @staticmethod
    def get_init():
        return (44100, -16, 2)

    @staticmethod
    def init():
        return None

    @staticmethod
    def get_num_channels():
        return 8

    @staticmethod
    def set_num_channels(_count):
        return None

    @staticmethod
    def find_channel(_force=False):
        if _Mixer.free_channels <= 0:
            return None
        return _Channel()


class _SoundManager:
    enabled = True
    master_volume = 0.7
    sfx_volume = 0.6


def _load():
    shim = types.ModuleType("pygame")
    shim.mixer = _Mixer
    shim.time = types.SimpleNamespace(get_ticks=lambda: _Clock.ms)
    system = types.ModuleType("_system")
    system.SoundManager = lambda: _SoundManager
    # The shims stay installed while the fixture is generated: `play()`
    # re-imports `_system.SoundManager` on every call for the live volume.
    saved = {name: sys.modules.get(name) for name in ("pygame", "_system")}
    sys.modules["pygame"] = shim
    sys.modules["_system"] = system
    namespace = {"__name__": "combat_audio_oracle", "__file__": str(SOURCE)}
    exec(compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec"), namespace)
    assert namespace["init"]() is True, namespace["LAPORAN"]

    def restore():
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    return namespace, restore


# (ms, kind, volume_mult, free_channels, new_frame_before, enabled, master, sfx)
STREAM = [
    (0, "minion_hit", 1.0, 24, True, True, 0.7, 0.6),
    (0, "minion_hit", 1.0, 24, False, True, 0.7, 0.6),      # spacing 140 ms
    (139, "minion_hit", 1.0, 24, True, True, 0.7, 0.6),     # still inside spacing
    (140, "minion_hit", 1.0, 24, True, True, 0.7, 0.6),     # exactly the spacing -> ok
    (200, "tower_archer", 1.0, 24, True, True, 0.7, 0.6),
    (200, "tower_archer", 0.8, 24, False, True, 0.7, 0.6),  # spacing 110 ms
    (200, "tower_cannon", 0.8, 24, False, True, 0.7, 0.6),  # red tower volume
    (200, "tower_ice", 1.0, 24, False, True, 0.7, 0.6),
    (200, "tower_mage", 1.0, 24, False, True, 0.7, 0.6),    # 4th in the frame -> ok
    (200, "hero_melee", 1.0, 24, False, True, 0.7, 0.6),    # 5th -> budget rejected
    (201, "hero_melee", 1.0, 24, True, True, 0.7, 0.6),     # new frame -> ok
    (290, "hero_melee", 1.0, 24, True, True, 0.7, 0.6),     # 89 ms < 90 -> rejected
    (291, "hero_melee", 1.0, 24, True, True, 0.7, 0.6),
    (400, "hero_ranged", 1.0, 0, True, True, 0.7, 0.6),     # no free channel
    (401, "hero_ranged", 1.0, 1, True, True, 0.7, 0.6),
    (500, "hero_ranged", 1.0, 24, True, False, 0.7, 0.6),   # sound disabled -> volume 0
    (600, "hero_ranged", 2.0, 24, True, True, 1.0, 1.0),    # clamp to 1.0
    (700, "unknown_kind", 1.0, 24, True, True, 0.7, 0.6),   # no bank -> False
]


def source_fixture():
    src, restore = _load()
    try:
        return _build(src)
    finally:
        restore()


def _build(src):
    config = {kind: list(values) for kind, values in src["_KONFIG"].items()}
    bank = {kind: [sound.path for sound in sounds] for kind, sounds in src["_bank"].items()}
    events = []
    for (ms, kind, mult, free, new_frame, enabled, master, sfx) in STREAM:
        _Clock.ms = ms
        _Mixer.free_channels = free
        _SoundManager.enabled = enabled
        _SoundManager.master_volume = master
        _SoundManager.sfx_volume = sfx
        if new_frame:
            src["new_frame"]()
        before = dict(src["_stats"])
        ok = src["play"](kind, volume_mult=mult)
        after = dict(src["_stats"])
        delta = {key: after[key] - before[key] for key in after}
        volume = None
        if ok:
            volume = src["_bank"][kind][0].volume
        events.append({
            "ms": ms, "kind": kind, "volume_mult": mult, "free_channels": free,
            "new_frame": new_frame, "enabled": enabled, "master": master, "sfx": sfx,
            "ok": bool(ok), "volume": volume, "stats_delta": delta,
            "budget_left": src["_sisa_frame"][0],
        })

    class _Hero:
        def __init__(self, is_melee_hero=None, range_px=40):
            if is_melee_hero is not None:
                self.is_melee_hero = is_melee_hero
            self.range = range_px

    hero_kinds = []
    _Clock.ms = 100000
    for label, hero in (
        ("flag_melee", _Hero(True, 500)),
        ("flag_ranged", _Hero(False, 40)),
        ("range_99", _Hero(None, 99)),
        ("range_100", _Hero(None, 100)),
        ("range_none", _Hero(None, None)),
    ):
        _Clock.ms += 1000
        src["new_frame"]()
        kind = (src["HERO_MELEE"] if getattr(hero, "is_melee_hero", None) is True
                else src["HERO_RANGED"] if getattr(hero, "is_melee_hero", None) is False
                else src["jenis_serangan"](hero.range))
        played = src["play_hero_basic"](hero)
        hero_kinds.append({"case": label, "kind": kind, "played": bool(played)})

    return {
        "source": "mobile/combat_audio.py (real module under a scriptable pygame shim)",
        "kinds": [src["HERO_MELEE"], src["HERO_RANGED"], src["TOWER_ARCHER"],
                  src["TOWER_CANNON"], src["TOWER_ICE"], src["TOWER_MAGE"],
                  src["MINION_HIT"]],
        "config": config,
        "ranged_threshold": src["AMBANG_RANGED"],
        "frame_budget": 4,
        "mixer_channels": 24,
        "fallback_volume": 0.6,
        "bank": bank,
        "attack_kind": {str(r): src["jenis_serangan"](r) for r in (0, 40, 99, 100, 101, 250)},
        "attack_kind_none": src["jenis_serangan"](None),
        "tower_kind": {t: src["jenis_tower"](t)
                       for t in ("archer", "cannon", "ice", "mage", "nexus", "")},
        "hero_kinds": hero_kinds,
        "events": events,
    }


def main():
    fixture = source_fixture()
    assert fixture["events"][1]["ok"] is False
    assert fixture["events"][9]["stats_delta"]["tolak_anggaran"] == 1
    assert fixture["events"][13]["stats_delta"]["tolak_channel"] == 1
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)


if __name__ == "__main__":
    main()
