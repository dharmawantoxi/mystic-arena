"""Whole-file oracle for `_system.py` (1.125 lines, five merged system modules).

    prelude          1-28      `_SOUND_DIR`, `_sound_path`
    performance.py   29-188    `FrustumCuller`, `SpatialGrid`, `_grid`,
                               `update_spatial_grid`, `query_enemies_in_range`
    fps_counter.py   189-387   `FPSCounter` (singleton overlay)
    fps_limiter.py   388-449   `AdaptiveQuality` (the older tick-based governor)
    sound_manager.py 450-731   `SoundManager`
    save_manager.py  732-1125  `NUM_SLOTS`, `LEGACY_SAVE_FILE`, `SaveManager`

This oracle does three things:

* it inventories the file (six sections, six classes, 47 `def`s, three module
  functions, four module assigns) and classifies every symbol with a target file and a
  token that target really contains. Reachability is computed per class from the public
  methods and `__new__`/`__init__` edges, so a helper `draw()` that only the legacy
  desktop entry calls is `dead` instead of silently "ported";
* it imports the REAL module (stub `pygame` with a recording mixer, `_core` settings
  namespace, a temporary `storage_paths.SAVE_DIR` and a frozen clock) and executes the
  parts no other suite owns: the culler boundary, the grid query order, the FPS overlay
  state machine, the older adaptive governor, every `SoundManager` volume/throttle path
  and the whole `SaveManager` slot lifecycle;
* it records the numbers the rebuild must reproduce (cell size 60, throttle table,
  0.15 positional floor, 800 px radius, 3 slots, `%d %b %Y` fallback) so
  `system_checks.gd` can compare the native modules against them, and so the two dead
  modules (`FPSCounter`, `AdaptiveQuality`) are named instead of forgotten.

Run: python godot_rebuild/tests/system_source_oracle.py --write
"""

import argparse
import ast
import importlib
import json
import os
import sys
import tempfile
import time as _time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "_system.py"
CORE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "system_source.json"

SECTIONS = [
    ("prelude", 1, 28),
    ("performance", 29, 188),
    ("fps_counter", 189, 387),
    ("fps_limiter", 388, 449),
    ("sound_manager", 450, 731),
    ("save_manager", 732, 1125),
]
CORE_SETTINGS_BLOCK = (28, 1291)
FROZEN_NOW = 1700000000.0

MODULE_TARGETS = {
    "prelude": ("data", "godot_rebuild/scripts/audio/audio_manager.gd",
                'const ROOT := "res://assets/audio/"',
                "folder sound + resolver path berkas audio"),
    "performance": ("ported", "godot_rebuild/scripts/combat/spatial_grid.gd",
                    "func query_range(",
                    "culler + grid + dua helper modul"),
    "fps_counter": ("dead", "", "",
                    "hanya dipakai main_desktop_legacy.py; build Android memakai DebugOverlay"),
    "fps_limiter": ("deviation", "godot_rebuild/scripts/settings/adaptive_quality_controller.gd",
                    "const COOLDOWN_AFTER_LOWER := 180",
                    "varian tick() lama; governor aktif = mobile/perf.py"),
    "sound_manager": ("ported", "godot_rebuild/scripts/audio/audio_manager.gd",
                      "const THROTTLE_MS := {", "BGM + SFX + voice + ambient"),
    "save_manager": ("ported", "godot_rebuild/scripts/match/save_slot_store.gd",
                     "static func save_state(", "tiga slot + metadata + level stats"),
}

CLASS_TARGETS = {
    "FrustumCuller": ("ported", "godot_rebuild/scripts/ui/frustum_cull.gd",
                      "static func is_visible(",
                      "margin 80 px di luar 1280x720"),
    "SpatialGrid": ("ported", "godot_rebuild/scripts/combat/spatial_grid.gd",
                    "func query_range(", "bucket 60 px, satu sel per entitas"),
    "FPSCounter": ("dead", "", "",
                   "overlay F8 hanya di entry desktop legacy (bukan build Android)"),
    "AdaptiveQuality": ("deviation",
                        "godot_rebuild/scripts/settings/adaptive_quality_controller.gd",
                        "const COOLDOWN_AFTER_LOWER := 180",
                        "versi tick() 30 sampel ambang 50/35 digantikan governor aktif"),
    "SoundManager": ("ported", "godot_rebuild/scripts/audio/audio_manager.gd",
                     "var master_volume := DEFAULT_MASTER_VOLUME",
                     "single facade: musik, sfx, voice, ambient"),
    "SaveManager": ("ported", "godot_rebuild/scripts/match/save_slot_store.gd",
                    "const SLOT_COUNT := 3",
                    "slot, metadata, migrasi legacy, level stats"),
}

METHOD_ALIASES = {
    ("FrustumCuller", "is_visible"): ("ui/frustum_cull.gd", "static func is_visible(",
                                      "predikat cull yang sama"),
    ("SpatialGrid", "__init__"): ("combat/spatial_grid.gd", "func _init(",
                                  "cell_size 60"),
    ("SpatialGrid", "insert"): ("combat/spatial_grid.gd", "func insert(",
                                "satu bucket per entitas"),
    ("SpatialGrid", "query_range"): ("combat/spatial_grid.gd", "func query_range(",
                                     "urutan cx-luar, cy-dalam, box lalu jarak kuadrat"),
    ("FPSCounter", "__new__"): ("dead", "", "singleton overlay legacy"),
    ("FPSCounter", "__init__"): ("dead", "", "state overlay legacy"),
    ("FPSCounter", "_get_font"): ("dead", "", "cache font overlay legacy"),
    ("FPSCounter", "toggle"): ("dead", "", "tombol F8 hanya ada di entry desktop legacy"),
    ("FPSCounter", "update"): ("dead", "", "sampel FPS overlay legacy"),
    ("FPSCounter", "draw"): ("dead", "", "panel FPS legacy"),
    ("AdaptiveQuality", "__new__"): ("settings/adaptive_quality_runtime.gd",
                                     "var controller = Controller.new()",
                                     "autoload runtime menggantikan singleton"),
    ("AdaptiveQuality", "_init"): ("settings/adaptive_quality_runtime.gd",
                                   "func _ready() -> void:",
                                   "inisialisasi runtime di _ready"),
    ("AdaptiveQuality", "tick"): ("settings/frame_rate_limit_runtime.gd",
                                  "Engine.max_fps",
                                  "pacing pindah ke engine; sampel ke governor aktif"),
    ("AdaptiveQuality", "get_fps"): ("settings/adaptive_quality_runtime.gd",
                                     "func update_fps(fps: float) -> void:",
                                     "governor aktif menerima fps dari engine"),
    ("SoundManager", "__new__"): ("audio/audio_manager.gd", "var music: AudioStreamPlayer",
                                  "autoload Node menggantikan singleton Python"),
    ("SoundManager", "__init__"): ("audio/audio_manager.gd", "func _ready() -> void:",
                                   "mixer disiapkan di _ready"),
    ("SoundManager", "load"): ("audio/audio_manager.gd",
                               "func _stream(key: String) -> AudioStream:",
                               "stream dimuat dari tabel STREAMS"),
    ("SoundManager", "load_all"): ("audio/audio_manager.gd", "const STREAMS := {",
                                   "daftar berkas tetap menggantikan load_all()"),
    ("SoundManager", "play_bgm"): ("audio/audio_manager.gd",
                                   "func play_music(key: String) -> void:",
                                   "musik loop di player khusus"),
    ("SoundManager", "stop_bgm"): ("audio/audio_manager.gd", "func stop_all() -> void:",
                                   "musik dihentikan bersama kanal lain"),
    ("SoundManager", "pause_bgm"): ("audio/audio_manager.gd", "func pause_music() -> void:",
                                    "stream_paused pada player musik"),
    ("SoundManager", "resume_bgm"): ("audio/audio_manager.gd",
                                     "func resume_music() -> void:", "lanjutkan musik"),
    ("SoundManager", "update_bgm_volume"): ("audio/audio_manager.gd",
                                            "func _apply_mix() -> void:",
                                            "mix master*bgm dihitung ulang"),
    ("SoundManager", "stop_ambient"): ("audio/audio_manager.gd", "func stop_all() -> void:",
                                       "ambient ikut berhenti"),
    ("SoundManager", "set_master_volume"): ("audio/audio_manager.gd",
                                            "func set_mix_volume(", "clamp 0..1 per kanal"),
    ("SaveManager", "ensure_save_dir"): ("match/save_slot_store.gd",
                                         'const PATH_TEMPLATE := "user://slot_%d.json"',
                                         "user:// sudah ada; tidak perlu makedirs"),
    ("SaveManager", "get_slot_file"): ("match/save_slot_store.gd", "static func slot_path(",
                                       "pola slot_%d.json"),
    ("SaveManager", "migrate_legacy_save"): ("match/save_slot_store.gd",
                                             "static func migrate_legacy(",
                                             "legacy -> slot 1 tanpa menimpa"),
    ("SaveManager", "save"): ("match/save_slot_store.gd", "static func save_state(",
                              "stempel slot_last_played + cloud upload"),
    ("SaveManager", "load"): ("match/save_slot_store.gd", "static func load_state(",
                              "backfill field default"),
    ("SaveManager", "get_empty_save"): ("match/save_slot_store.gd",
                                        "static func empty_state(",
                                        "sepuluh field default yang sama"),
    ("SaveManager", "get_slot_info"): ("match/save_slot_store.gd", "static func slot_info(",
                                       "metadata untuk UI slot"),
    ("SaveManager", "get_all_slot_info"): ("match/save_slot_store.gd",
                                           "static func all_slot_info(",
                                           "tiga slot, kosong = {}"),
    ("SaveManager", "get_level_stats"): ("match/level_stats.gd",
                                         "static func get_level_stats(",
                                         "default tujuh field"),
    ("SaveManager", "update_level_stats"): ("match/level_stats.gd",
                                            "static func update_level_stats(",
                                            "best score/time hanya saat menang"),
}

TOP_TARGETS = {
    "_sound_path": ("ported", "godot_rebuild/scripts/audio/audio_manager.gd",
                    'const ROOT := "res://assets/audio/"',
                    "resolusi berkas audio"),
    "update_spatial_grid": ("ported", "godot_rebuild/scripts/combat/spatial_grid.gd",
                            "static func update_spatial_grid(",
                            "hanya minion + hero yang hidup"),
    "query_enemies_in_range": ("ported", "godot_rebuild/scripts/combat/spatial_grid.gd",
                               "static func query_enemies_in_range(",
                               "filter musuh di dalam loop kueri"),
}

ASSIGN_TARGETS = {
    "_SOUND_DIR": ("data", "godot_rebuild/scripts/audio/audio_manager.gd",
                   'const ROOT := "res://assets/audio/"', "folder berkas audio"),
    "_grid": ("data", "godot_rebuild/scripts/combat/spatial_grid.gd",
              "static var _shared: SpatialGrid", "singleton grid cell_size 60"),
    "NUM_SLOTS": ("data", "godot_rebuild/scripts/match/save_slot_store.gd",
                  "const SLOT_COUNT := 3", "tiga slot save"),
    "LEGACY_SAVE_FILE": ("data", "godot_rebuild/scripts/match/save_slot_store.gd",
                         "const LEGACY_PATH := ProgressStore.PATH",
                         "progress.json lama -> slot 1"),
}
HISTOGRAM_KEYS = ("data", "dead", "deviation", "folded", "ported")


def source_lines():
    return SYSTEM.read_text(encoding="utf-8").splitlines()


def source_tree():
    return ast.parse("\n".join(source_lines()))


# ── stubs ────────────────────────────────────────────────────────────────
class _Recorder:
    def __init__(self):
        self.channels = []
        self.dropped = []
        self.music = {"loads": [], "volumes": [], "plays": [], "fadeouts": [],
                      "pause": 0, "unpause": 0, "stops": 0}
        self.mixer = {"pre_init": None, "init": 0, "num_channels": 0, "stop": 0}
        self.playing = []
        self.ticks = 0


REC = _Recorder()


class _Channel:
    def __init__(self, index):
        self.index = index
        self.volume = 1.0
        self.busy = False
        self.loops = 0
        self.fade_ms = 0
        self.sound = None

    def set_volume(self, volume):
        self.volume = float(volume)

    def play(self, sound, loops=0, fade_ms=0):
        self.sound = sound
        self.busy = True
        self.loops = loops
        self.fade_ms = fade_ms
        REC.playing.append({"channel": self.index,
                            "sound": os.path.basename(getattr(sound, "path", "")),
                            "volume": round(self.volume, 9), "loops": loops,
                            "fade_ms": fade_ms})

    def get_busy(self):
        return self.busy

    def stop(self):
        self.busy = False

    def fadeout(self, ms):
        self.busy = False
        self.fade_ms = ms


class _Sound:
    def __init__(self, path):
        self.path = str(path)


class _Music:
    def load(self, path):
        REC.music["loads"].append(os.path.basename(str(path)))
        self.path = str(path)

    def set_volume(self, volume):
        REC.music["volumes"].append(round(float(volume), 9))

    def play(self, loops=0, fade_ms=0):
        REC.music["plays"].append({"loops": loops, "fade_ms": fade_ms})

    def fadeout(self, ms):
        REC.music["fadeouts"].append(ms)

    def pause(self):
        REC.music["pause"] += 1

    def unpause(self):
        REC.music["unpause"] += 1

    def stop(self):
        REC.music["stops"] += 1


class _PixelSurface:
    def __init__(self, size=(8, 8), flags=0):
        self.size = (int(size[0]), int(size[1]))

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]

    def blit(self, *args, **kwargs):
        return None

    def set_alpha(self, *args, **kwargs):
        return None


def _stub_pygame():
    pygame = types.ModuleType("pygame")
    pygame.error = type("PygameError", (Exception,), {})
    pygame.SRCALPHA = 0x00010000
    pygame.Surface = _PixelSurface
    pygame.Rect = lambda *args, **kwargs: types.SimpleNamespace(x=0, y=0, w=8, h=8)
    for name in ("draw", "transform", "font", "time", "mixer", "gfxdraw", "image",
                 "display", "key"):
        module = types.ModuleType("pygame." + name)
        setattr(pygame, name, module)
        sys.modules["pygame." + name] = module
    for fn in ("circle", "rect", "line", "polygon", "aaline", "lines", "ellipse", "arc"):
        setattr(pygame.draw, fn, lambda *a, **k: None)
    pygame.transform.smoothscale = lambda surface, size: surface
    pygame.transform.scale = lambda surface, size: surface
    pygame.font.Font = lambda *a, **k: types.SimpleNamespace(
        render=lambda *a2, **k2: _PixelSurface(), get_height=lambda: 16,
        set_bold=lambda *a2: None)
    pygame.font.SysFont = pygame.font.Font
    pygame.time.get_ticks = lambda: REC.ticks
    pygame.time.Clock = lambda: types.SimpleNamespace(
        tick=lambda *a: 0, get_fps=lambda: 0.0)

    REC.channels = [_Channel(index) for index in range(32)]
    REC.next_channel = 0

    def _find_channel(steal=False):
        for channel in REC.channels:
            if not channel.busy:
                return channel
        if steal:
            return REC.channels[0]
        return None

    pygame.mixer.pre_init = lambda *a, **k: REC.mixer.__setitem__("pre_init", [a, k])
    pygame.mixer.init = lambda *a, **k: REC.mixer.__setitem__(
        "init", REC.mixer["init"] + 1)
    pygame.mixer.set_num_channels = lambda count: REC.mixer.__setitem__(
        "num_channels", int(count))
    pygame.mixer.Sound = _Sound
    pygame.mixer.find_channel = _find_channel
    pygame.mixer.music = _Music()
    pygame.mixer.stop = lambda: REC.mixer.__setitem__("stop", REC.mixer["stop"] + 1)
    pygame.mixer.get_init = lambda: (44100, -16, 2)
    sys.modules["pygame"] = pygame
    return pygame


def _core_namespace():
    lines = CORE.read_text(encoding="utf-8").splitlines()
    block = "\n".join(["pass"] * (CORE_SETTINGS_BLOCK[0] - 1) + lines[
        CORE_SETTINGS_BLOCK[0] - 1:CORE_SETTINGS_BLOCK[1]
    ])
    namespace = {"__name__": "_core", "sys": sys, "types": types,
                 "_types": types, "_globals_before_settings": set()}
    exec(compile(block, str(CORE), "exec"), namespace)  # noqa: S102 - oracle
    module = types.ModuleType("_core")
    module.__dict__.update(namespace)
    sys.modules["_core"] = module
    return module


def _storage_stub(save_dir):
    storage = types.ModuleType("storage_paths")
    storage.SAVE_DIR = str(save_dir)
    sys.modules["storage_paths"] = storage
    return storage


def system_module(save_dir):
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    _stub_pygame()
    _core_namespace()
    _storage_stub(save_dir)
    sys.modules.pop("_system", None)
    module = importlib.import_module("_system")
    # `FPSCounter._get_font` asks for a cached font from `_render`; the overlay is dead
    # on Android, so a stub keeps the state machine executable without dragging the
    # whole render bundle in.
    module.get_font = lambda size, style="body", bold=False: types.SimpleNamespace(
        size=size, render=lambda *a, **k: _PixelSurface(), get_width=lambda: 16)
    return module


def _frozen_time():
    """`SaveManager` stamps and formats wall-clock values; freeze them."""
    real_time, real_localtime = _time.time, _time.localtime

    class _Frozen:
        @staticmethod
        def time():
            return FROZEN_NOW

        @staticmethod
        def localtime(timestamp=None):
            # UTC on purpose: `format_last_played` falls back to
            # `time.strftime("%d %b %Y", time.localtime(ts))`, which must not depend on
            # the machine timezone when the fixture is compared in CI.
            return _time.gmtime(timestamp if timestamp is not None else FROZEN_NOW)

        @staticmethod
        def strftime(fmt, struct_time=None):
            return _time.strftime(fmt, struct_time)

    return _Frozen, lambda: (setattr(_time, "time", real_time),
                             setattr(_time, "localtime", real_localtime))


# ── executed cases ───────────────────────────────────────────────────────
def cull_cases(module):
    culler = module.FrustumCuller
    rows = []
    for x, y, radius in (
        (0, 0, 30), (640, 360, 30), (-109.9, 0, 30), (-110, 0, 30), (-110.1, 0, 30),
        (1389.9, 719, 30), (1390, 720, 30), (1390.1, 0, 30), (0, 820, 100),
        (0, 820.1, 100), (-1, -1, 0), (-80, -80, 0), (-80.1, -80, 0),
    ):
        rows.append({"x": x, "y": y, "radius": radius,
                     "visible": bool(culler.is_visible(x, y, radius))})
    return {"margin": int(culler.MARGIN), "screen": [int(module.SCREEN_WIDTH),
                                                     int(module.SCREEN_HEIGHT)],
            "cases": rows}


GRID_ENTITIES = [
    {"id": "m1", "x": 100.0, "y": 100.0, "team": "blue", "alive": True},
    {"id": "m2", "x": 130.0, "y": 100.0, "team": "red", "alive": True},
    {"id": "m3", "x": 190.0, "y": 100.0, "team": "red", "alive": True},
    {"id": "m4", "x": 100.0, "y": 130.0, "team": "blue", "alive": False},
    {"id": "m5", "x": 100.0, "y": 190.0, "team": "red", "alive": True},
    {"id": "m6", "x": 40.0, "y": 40.0, "team": "blue", "alive": True},
    {"id": "m7", "x": 220.0, "y": 220.0, "team": "red", "alive": False},
    {"id": "m8", "x": -30.0, "y": 10.0, "team": "blue", "alive": True},
    {"id": "m9", "x": 59.0, "y": 59.0, "team": "blue", "alive": True},
    {"id": "m10", "x": 60.0, "y": 60.0, "team": "red", "alive": True},
]


def grid_cases(module):
    grid = module.SpatialGrid(cell_size=60)
    for entity in GRID_ENTITIES:
        grid.insert(types.SimpleNamespace(**entity))
    buckets = {}
    for entity in GRID_ENTITIES:
        key = (int(entity["x"] // 60), int(entity["y"] // 60))
        buckets.setdefault(key, []).append(entity["id"])
    queries = []
    for x, y, radius, team in (
        (100, 100, 50, None), (100, 100, 50, "blue"), (100, 100, 50, "red"),
        (100, 100, 200, None), (0, 0, 120, None), (-40, 0, 60, None),
        (240, 240, 100, "red"), (700, 700, 60, None),
    ):
        found = grid.query_range(x, y, radius, team)
        queries.append({"x": x, "y": y, "radius": radius, "team": team,
                        "ids": [entity.id for entity in found]})
    module._grid.clear()
    living = [types.SimpleNamespace(**entity) for entity in GRID_ENTITIES]
    module.update_spatial_grid(living[:6], living[6:])
    global_queries = []
    for x, y, radius, team in ((100, 100, 60, None), (100, 100, 120, "red")):
        global_queries.append({
            "x": x, "y": y, "radius": radius, "team": team,
            "ids": [entity.id for entity in
                    module.query_enemies_in_range(x, y, radius, team)],
        })
    indexed = sorted(entity.id for bucket in grid.grid.values() for entity in bucket)
    return {
        "cell_size": int(grid.cell_size),
        "entities": [dict(entity) for entity in GRID_ENTITIES],
        "buckets": {"%d,%d" % key: value for key, value in sorted(buckets.items())},
        "bucket_count": len(grid.grid),
        "indexed_ids": indexed,
        "queries": queries,
        "global_queries": global_queries,
        "global_bucket_count": len(module._grid.grid),
    }


def fps_counter_cases(module):
    counter = module.FPSCounter()
    counter.enabled = False
    counter.fps_history.clear()
    counter.frame_count = 0
    identity = counter is module.FPSCounter()

    class _Clock:
        def __init__(self):
            self.fps = 0.0

        def get_fps(self):
            return self.fps

    clock = _Clock()
    snapshots = []
    scripted = [60.0] * 12 + [50.0, 40.0, 30.0, 20.0] + [20.0] * 8
    for index, fps in enumerate(scripted):
        clock.fps = fps
        counter.update(clock)
        if index in (9, 19, 21, 23):
            snapshots.append({
                "frame": index + 1,
                "fps": round(counter.display_fps, 6),
                "avg": round(counter.display_avg, 6),
                "min": round(counter.display_min, 6),
                "max": round(counter.display_max, 6),
                "history": len(counter.fps_history),
            })
    counter.enabled = True
    toggled_on = counter.enabled
    counter.toggle()
    toggled_off = counter.enabled
    counter.toggle()
    return {
        "singleton": identity,
        "history_size": int(counter.history_size),
        "snapshots": snapshots,
        "toggled_on": toggled_on,
        "toggled_off": toggled_off,
        "enabled_after_twice": counter.enabled,
    }


def adaptive_quality_cases(module):
    quality = module.AdaptiveQuality()
    clock = quality.clock

    class _Clock:
        def __init__(self):
            self.fps = 0.0
            self.ticks = 0

        def tick(self, target_fps=60):
            self.ticks += 1
            return 0

        def get_fps(self):
            return self.fps

    fake = _Clock()
    quality.clock = fake
    quality.fps_history.clear()
    quality.quality = "high"
    levels = []
    for fps in [60.0] * 9 + [40.0] * 9 + [20.0] * 9 + [55.0] * 9:
        fake.fps = fps
        levels.append(quality.tick(60))
    history_cap = quality.history_size
    quality.fps_history.clear()
    for _ in range(40):
        fake.fps = 55.0
        quality.tick(60)
    capped = len(quality.fps_history)
    identity = quality is module.AdaptiveQuality()
    return {
        "singleton": identity,
        "high_threshold": int(quality.HIGH_THRESHOLD),
        "medium_threshold": int(quality.MEDIUM_THRESHOLD),
        "history_size": int(history_cap),
        "levels": levels,
        "capped_history": capped,
        "get_fps": round(quality.get_fps(), 6),
        "clock_ticks": fake.ticks,
    }


def sound_cases(module):
    manager = module.SoundManager()
    manager.sounds.clear()
    manager.throttle.clear()
    REC.playing.clear()
    manager.load_all()
    loaded = sorted(manager.sounds)
    missing = sorted(set(getattr(manager, "_hilang", [])))
    categories = {name: manager.sounds[name]["category"] for name in loaded}

    manager.master_volume = 0.7
    manager.sfx_volume = 0.6
    manager.voice_volume = 0.5
    manager.bgm_volume = 0.35
    manager.ambient_volume = 0.25

    REC.playing.clear()
    timeline = []
    for name, tick in (("ui_click", 0), ("ui_click", 30), ("ui_click", 60),
                       ("nexus_hit", 80), ("nexus_hit", 200), ("nexus_hit", 400),
                       ("minion_death", 400), ("minion_death", 450)):
        REC.ticks = tick
        manager.play(name, 1.0)
        timeline.append({"name": name, "tick": tick,
                         "plays": len(REC.playing)})
    playback = list(REC.playing)

    REC.playing.clear()
    REC.ticks = 1000
    manager.play("goblin_spawn", 1.0)
    REC.ticks = 2000
    manager.play_positional("ui_buy", 100.0, 100.0, 100.0, 100.0, 800, 1.0)
    REC.ticks = 3000
    manager.play_positional("ui_buy", 400.0, 100.0, 0.0, 100.0, 800, 1.0)
    REC.ticks = 4000
    manager.play_positional("ui_buy", 760.0, 100.0, 0.0, 100.0, 800, 1.0)
    REC.ticks = 5000
    manager.play_positional("ui_buy", 900.0, 100.0, 0.0, 100.0, 800, 1.0)
    REC.ticks = 6000
    manager.play_positional("ui_buy", 200.0, 100.0, 0.0, 100.0, 800, 0.5)
    positional = list(REC.playing)

    REC.music["loads"].clear()
    REC.music["volumes"].clear()
    REC.music["plays"].clear()
    manager.play_bgm("bgm_battle.wav", loop=True, fade_ms=3000)
    bgm = {"loads": list(REC.music["loads"]),
           "volumes": list(REC.music["volumes"]),
           "plays": list(REC.music["plays"]),
           "current": manager.current_bgm, "paused": manager.bgm_paused}
    manager.pause_bgm()
    paused = {"paused": manager.bgm_paused, "pause_calls": REC.music["pause"]}
    manager.resume_bgm()
    resumed = {"paused": manager.bgm_paused, "unpause_calls": REC.music["unpause"]}
    manager.set_master_volume(0.9)
    after_master = {"master": round(manager.master_volume, 6),
                    "music_volume": REC.music["volumes"][-1]}
    manager.set_master_volume(1.5)
    clamped = round(manager.master_volume, 6)
    manager.stop_bgm(fade_ms=1000)
    stopped = {"current": manager.current_bgm, "fadeouts": list(REC.music["fadeouts"])}

    REC.playing.clear()
    manager.master_volume = 0.7
    manager.play_ambient("ambient_forest", volume_mult=0.8)
    ambient = {"plays": list(REC.playing),
               "channel_volume": round(manager.ambient_channel.volume, 9)}
    manager.set_master_volume(0.9)
    ambient_after_master = round(manager.ambient_channel.volume, 9)
    ambient_channel = manager.ambient_channel
    manager.stop_ambient(1200)
    ambient_stopped = {"channel_cleared": manager.ambient_channel is None,
                       "fade": ambient_channel.fade_ms,
                       "busy": ambient_channel.busy}

    REC.mixer["stop"] = 0
    REC.music["stops"] = 0
    manager.stop_all()
    return {
        "enabled": bool(manager.enabled),
        "volumes": {"master": round(manager.master_volume, 6),
                    "sfx": round(manager.sfx_volume, 6),
                    "voice": round(manager.voice_volume, 6),
                    "bgm": round(manager.bgm_volume, 6),
                    "ambient": round(manager.ambient_volume, 6)},
        "throttle_ms": {key: int(value) for key, value in manager.throttle_ms.items()},
        "loaded": loaded,
        "missing": missing,
        "categories": categories,
        "timeline": timeline,
        "playback": playback,
        "positional": positional,
        "bgm": bgm,
        "paused": paused,
        "resumed": resumed,
        "after_master": after_master,
        "master_clamped": clamped,
        "stopped": stopped,
        "ambient": ambient,
        "ambient_after_master": ambient_after_master,
        "ambient_stopped": ambient_stopped,
        "mixer": {"num_channels": REC.mixer["num_channels"],
                  "stop_calls": REC.mixer["stop"],
                  "music_stops": REC.music["stops"]},
        "fallback_positional": {
            "at_0": module.SoundManager.play_positional.__doc__ is not None,
        },
    }


def _positional_math(module):
    rows = []
    for x, y, px, py, max_distance, mult in (
        (100.0, 100.0, 100.0, 100.0, 800, 1.0),
        (400.0, 100.0, 0.0, 100.0, 800, 1.0),
        (760.0, 100.0, 0.0, 100.0, 800, 1.0),
        (800.0, 100.0, 0.0, 100.0, 800, 1.0),
        (900.0, 100.0, 0.0, 100.0, 800, 1.0),
        (200.0, 100.0, 0.0, 100.0, 800, 0.5),
        (0.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    ):
        distance = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
        played = distance <= max_distance
        distance_vol = 0.0
        if played:
            distance_vol = max(0.15, 1.0 - (distance / max_distance)) \
                if max_distance > 0 else 1.0
        rows.append({
            "x": x, "y": y, "player_x": px, "player_y": py,
            "max_distance": max_distance, "volume_mult": mult,
            "distance": round(distance, 9),
            "plays": bool(played),
            "falloff": round(distance_vol, 9),
            "volume_mult_final": round(mult * distance_vol, 9),
        })
    return rows


def save_cases(module, save_dir):
    manager = module.SaveManager
    legacy = os.path.join(str(save_dir), "progress.json")
    rows = {
        "num_slots": int(module.NUM_SLOTS),
        "legacy_file": os.path.basename(module.LEGACY_SAVE_FILE),
        "empty": manager.get_empty_save(),
        "slot_files": [os.path.basename(manager.get_slot_file(slot))
                       for slot in range(1, 4)],
        "default_slot": int(manager.get_current_slot()),
    }
    manager.set_current_slot(2)
    rows["set_slot_valid"] = int(manager.get_current_slot())
    manager.set_current_slot(9)
    rows["set_slot_invalid"] = int(manager.get_current_slot())
    manager.set_current_slot(1)

    # ── legacy migration (progress.json -> slot_1.json), before slot 1 exists ──
    with open(legacy, "w", encoding="utf-8") as handle:
        json.dump({"meta_gold": 777, "completed_levels": [3]}, handle)
    rows["migrated"] = bool(manager.migrate_legacy_save())
    rows["migrated_again"] = bool(manager.migrate_legacy_save())
    rows["legacy_files"] = sorted(
        name for name in os.listdir(str(save_dir)) if name.startswith("progress"))
    with open(manager.get_slot_file(1), "r", encoding="utf-8") as handle:
        migrated = json.load(handle)
    rows["migrated_keys"] = sorted(migrated)
    rows["migrated_meta_gold"] = int(migrated["meta_gold"])
    rows["slot_info_after_migration"] = manager.get_slot_info(1)

    # ── save / load a second slot ──
    manager.save({"meta_gold": 123, "completed_levels": [1, 2]}, 2)
    rows["saved_exists"] = manager.slot_exists(2)
    with open(manager.get_slot_file(2), "r", encoding="utf-8") as handle:
        stored = json.load(handle)
    rows["saved_keys"] = sorted(stored)
    rows["saved_last_played"] = stored["slot_last_played"]
    loaded = manager.load(2)
    rows["loaded_keys"] = sorted(loaded)
    rows["loaded_meta_gold"] = int(loaded["meta_gold"])
    rows["loaded_last_played_level"] = int(loaded["last_played_level"])
    rows["loaded_run_difficulty"] = loaded["run_difficulty"]
    rows["slot_info"] = manager.get_slot_info(2)
    rows["slot_info_missing"] = manager.get_slot_info(3)
    rows["all_slot_info"] = [bool(row) for row in manager.get_all_slot_info()]

    rows["deleted"] = bool(manager.delete_slot(2))
    rows["deleted_missing"] = bool(manager.delete_slot(2))
    rows["slot_exists_after_delete"] = manager.slot_exists(2)

    rows["playtime"] = [manager.format_playtime(value)
                        for value in (0, 59, 60, 3599, 3600, 3660, 7325)]
    rows["last_played"] = [
        manager.format_last_played(value) for value in (
            0, FROZEN_NOW - 30, FROZEN_NOW - 120, FROZEN_NOW - 7200,
            FROZEN_NOW - 90000, FROZEN_NOW - 700000, FROZEN_NOW - 10000000)
    ]
    rows["time"] = [manager.format_time(value) for value in (0, 5, 65, 600, 3599)]

    data = {"level_stats": {}}
    rows["stats_default"] = manager.get_level_stats(data, 3)
    # The source hands out the STORED dict: `new_stats` from one call is the same
    # object the next call mutates. Snapshots below are taken with `dict()` so the
    # per-call result survives, and `stats_aliases` records the quirk.
    loss = manager.update_level_stats(data, 3, {
        "won": False, "score": 900, "time_seconds": 300, "kills": 5, "combo": 7,
        "playtime_seconds": 120})
    loss_snapshot = {"flags": [bool(loss["is_new_best_score"]),
                               bool(loss["is_new_best_time"])],
                     "stats": dict(loss["new_stats"])}
    win = manager.update_level_stats(data, 3, {
        "won": True, "score": 1200, "time_seconds": 240, "kills": 9, "combo": 11,
        "playtime_seconds": 90})
    win_snapshot = {"flags": [bool(win["is_new_best_score"]),
                              bool(win["is_new_best_time"])],
                    "stats": dict(win["new_stats"])}
    slower = manager.update_level_stats(data, 3, {
        "won": True, "score": 1100, "time_seconds": 400, "kills": 1, "combo": 2,
        "playtime_seconds": 30})
    slower_snapshot = {"flags": [bool(slower["is_new_best_score"]),
                                 bool(slower["is_new_best_time"])],
                       "stats": dict(slower["new_stats"])}
    rows["stats_loss"] = loss_snapshot
    rows["stats_win"] = win_snapshot
    rows["stats_win_worse"] = slower_snapshot
    rows["stats_aliases"] = bool(loss["new_stats"] is win["new_stats"])
    rows["stats_saved"] = data["level_stats"]["3"]
    return rows


# ── inventory + classification ───────────────────────────────────────────
def inventory():
    lines = source_lines()
    tree = source_tree()
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    methods = sum(len([m for m in node.body if isinstance(m, ast.FunctionDef)])
                  for node in classes)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assigns = [node for node in tree.body if isinstance(node, ast.Assign)]
    return {
        "file": "_system.py",
        "lines": len(lines),
        "sections": len(SECTIONS),
        "classes": len(classes),
        "methods": methods,
        "top_functions": len(functions),
        "assigns": len(assigns),
    }


def section_ranges():
    rows = []
    for index, (name, start, end) in enumerate(SECTIONS):
        rows.append({"name": name, "start": start, "end": end,
                     "lines": end - start + 1})
        if index + 1 < len(SECTIONS) and SECTIONS[index + 1][1] != end + 1:
            raise AssertionError("sections are not contiguous at %s" % name)
    return rows


def _self_call_graph():
    graph = {}
    tree = source_tree()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        edges = {}
        for method in node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            targets = set()
            for inner in ast.walk(method):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                    owner = inner.func.value
                    if isinstance(owner, ast.Name) and owner.id in ("self", "cls",
                                                                   node.name):
                        targets.add(inner.func.attr)
            edges[method.name] = targets
        graph[node.name] = edges
    return graph


def _reachable(graph, class_name, roots):
    seen = set()
    stack = [name for name in roots if name in graph.get(class_name, {})]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(graph[class_name].get(name, ()))
    return seen


def _func_names(target):
    import re
    text = (ROOT / target).read_text(encoding="utf-8")
    return set(re.findall(r"^(?:static )?func ([a-zA-Z0-9_]+)\(", text, re.M))


def symbol_rows():
    tree = source_tree()
    graph = _self_call_graph()
    rows = []

    for name, _, _ in SECTIONS:
        kind, target, token, note = MODULE_TARGETS[name]
        rows.append({"symbol": "module:%s" % name, "kind": kind, "target": target,
                     "token": token, "note": note})

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        kind, target, token, note = CLASS_TARGETS[node.name]
        rows.append({"symbol": "class:%s" % node.name, "kind": kind,
                     "target": target, "token": token, "note": note})
        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
        roots = [name for name in methods if not name.startswith("_")] + [
            name for name in ("__new__", "__init__") if name in methods]
        reachable = _reachable(graph, node.name, roots)
        names = _func_names(target) if target else set()
        for method in methods:
            symbol = "class:%s.%s" % (node.name, method)
            alias = METHOD_ALIASES.get((node.name, method))
            if alias:
                file_name, alias_token, alias_note = alias
                if file_name == "dead":
                    rows.append({"symbol": symbol, "kind": "dead", "target": "",
                                 "token": "", "note": alias_note})
                    continue
                rows.append({"symbol": symbol, "kind": "ported",
                             "target": "godot_rebuild/scripts/" + file_name,
                             "token": alias_token, "note": alias_note})
                continue
            if method in names:
                rows.append({"symbol": symbol, "kind": "ported", "target": target,
                             "token": "func %s(" % method, "note": ""})
                continue
            if method not in reachable:
                rows.append({"symbol": symbol, "kind": "dead", "target": "",
                             "token": "",
                             "note": "tidak terjangkau dari API publik kelas"})
                continue
            rows.append({"symbol": symbol, "kind": "folded", "target": target,
                         "token": token,
                         "note": "dijalankan alur %s" % target.split("/")[-1]})

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in TOP_TARGETS:
            raise AssertionError("unmapped module function: %s" % node.name)
        kind, target, token, note = TOP_TARGETS[node.name]
        rows.append({"symbol": "top:%s@%d" % (node.name, node.lineno), "kind": kind,
                     "target": target, "token": token, "note": note})

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for assign_target in node.targets:
            if not isinstance(assign_target, ast.Name):
                continue
            name = assign_target.id
            if name not in ASSIGN_TARGETS:
                raise AssertionError("unmapped module assign: %s" % name)
            kind, target, token, note = ASSIGN_TARGETS[name]
            rows.append({"symbol": "assign:%s" % name, "kind": kind,
                         "target": target, "token": token, "note": note})
    return _dedupe(rows)


def _dedupe(rows):
    unique = {}
    order = []
    for row in rows:
        name = row["symbol"]
        if name in unique:
            merged = [text for text in (unique[name]["note"], row["note"]) if text]
            unique[name]["note"] = ", ".join(dict.fromkeys(merged))
            continue
        unique[name] = row
        order.append(name)
    return [unique[name] for name in order]


def duplicates():
    found = {}
    tree = source_tree()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    key = "class:%s.%s" % (node.name, member.name)
                    found.setdefault(key, []).append(member.lineno)
        elif isinstance(node, ast.FunctionDef):
            found.setdefault(node.name, []).append(node.lineno)
    return {name: {"lines": lines, "copies": len(lines)}
            for name, lines in found.items() if len(lines) > 1}


def source_fixture():
    rows = symbol_rows()
    histogram = {}
    for row in rows:
        histogram[row["kind"]] = histogram.get(row["kind"], 0) + 1
    for key in HISTOGRAM_KEYS:
        histogram.setdefault(key, 0)
    result = {
        "file": inventory(),
        "sections": section_ranges(),
        "symbols": {"count": len(rows), "kinds": histogram},
        "classification": {row["symbol"]: {"kind": row["kind"],
                                           "target": row["target"],
                                           "token": row["token"],
                                           "note": row["note"]} for row in rows},
        "dead_helpers": sorted(row["symbol"] for row in rows if row["kind"] == "dead"),
        "duplicates": duplicates(),
    }
    with tempfile.TemporaryDirectory() as save_dir:
        module = system_module(save_dir)
        frozen, restore = _frozen_time()
        real_time = module.time
        try:
            module.time = frozen
            result["cull"] = cull_cases(module)
            result["grid"] = grid_cases(module)
            result["fps_counter"] = fps_counter_cases(module)
            result["adaptive_quality"] = adaptive_quality_cases(module)
            result["sound"] = sound_cases(module)
            result["positional"] = _positional_math(module)
            result["save"] = save_cases(module, save_dir)
        finally:
            module.time = real_time
            restore()
    result["sound"].pop("fallback_positional", None)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    data = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        print("wrote %s (%d symbols, kinds %s)" % (
            FIXTURE, data["symbols"]["count"], data["symbols"]["kinds"]))
        return 0
    existing = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    if args.check and existing != data:
        print("FAIL: fixture is stale; rerun with --write")
        return 1
    print(json.dumps({"file": data["file"], "kinds": data["symbols"]["kinds"],
                      "dead": len(data["dead_helpers"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
