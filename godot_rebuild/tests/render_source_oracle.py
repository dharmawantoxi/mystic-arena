"""Whole-file oracle for `_render.py` (3.671 lines, seven merged render modules).

`_render.py` is the rendering half of the pygame runtime:

    font system      1-77     (Cinzel + four Barlow weights, `_make_font`, `title_font`)
    map_renderer.py  78-270   `MapRenderer`
    effects.py       271-1572 ten effect classes + four easing helpers
    effects_death.py 1573-2139 `_begin_prompt_text`, `_skip_button_label`,
                              `BossDeathAnimation`
    effects_intro.py 2140-2666 `BossIntroCinematic`
    effects_level_intro.py    `LevelIntroScreen`
    sprite_cache.py  3380-3548 `SpriteCache` + three module shortcuts
    render_cache.py  3549-3671 `RenderCache` + four module shortcuts

The rebuild has carried these classes for many layers (`floating_text.gd`,
`hit_particle.gd`, `death_explosion.gd`, `screen_shake.gd`, `effect_manager.gd`,
`combo_counter.gd`, `wave_announcer.gd`, `kill_feed.gd`, `popup_animation.gd`,
`path_preview.gd`, `achievement_popup.gd`, `boss_death_animation.gd`,
`boss_intro_cinematic.gd`, `level_intro_screen.gd`, `map_renderer.gd`,
`dynamic_map_renderer.gd`, `sprite_cache.gd`, `render_cache.gd` and the
`*_layout.gd` draw layers), so this oracle does three things:

* it inventories the file (eight sections, 17 classes, 108 `def`s, 16 module-level
  functions, seven module assigns) and classifies every symbol with a target file and
  a token that target really contains. Reachability is computed per class (`self.x()`
  edges from the public methods and `draw()`), so the pygame draw helpers that
  `draw()` never calls are `dead` instead of silently "ported";
* it executes the real module (stub `pygame`, the `_core` settings namespace) for the
  parts no other oracle runs: the font resolver (`_font_path`, `_make_font`,
  `title_font`), the four easing helpers, the two input-mode labels
  (`_begin_prompt_text`, `_skip_button_label` in all three modes) and the two module
  singletons (`_sprite_cache`, `_cache` with their global shortcuts);
* it records that `_skip_button_label()` is player-facing on Android ("TAP", not
  "SPACE") — the cell `boss_celebration_layout.gd` had hardcoded before layer 9ch
  wired `scripts/ui/skip_hint.gd` in.

Run: python godot_rebuild/tests/render_source_oracle.py --write
"""

import argparse
import ast
import importlib
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "_render.py"
CORE = ROOT / "_core.py"
GODOT = ROOT / "godot_rebuild"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "render_source.json"

SECTIONS = [
    ("font_system", 1, 77),
    ("map_renderer", 78, 270),
    ("effects", 271, 1572),
    ("effects_death", 1573, 2139),
    ("effects_intro", 2140, 2666),
    ("effects_level_intro", 2667, 3379),
    ("sprite_cache", 3380, 3548),
    ("render_cache", 3549, 3671),
]
CORE_SETTINGS_BLOCK = (28, 1291)

MODULE_TARGETS = {
    "font_system": ("data", "godot_rebuild/scripts/ui/source_fonts.gd",
                    "const STYLE_FILES := {",
                    "font bundle: lima TTF di assets/fonts + tabel gaya"),
    "map_renderer": ("ported", "godot_rebuild/scripts/ui/map_renderer.gd",
                     "func get_lane_path(",
                     "lane path, posisi shop dan klik shop"),
    "effects": ("ported", "godot_rebuild/scripts/ui/effect_manager.gd",
                "func add_damage_number(",
                "sepuluh kelas efek dalam satu manajer"),
    "effects_death": ("ported", "godot_rebuild/scripts/ui/boss_death_animation.gd",
                      "func get_death_visual_state(",
                      "kematian boss tiga fase + selebrasi"),
    "effects_intro": ("ported", "godot_rebuild/scripts/ui/boss_intro_cinematic.gd",
                      "func update() -> bool:",
                      "banner intro boss (strip atas, bukan overlay)"),
    "effects_level_intro": ("ported", "godot_rebuild/scripts/ui/level_intro_screen.gd",
                            "func get_begin_prompt(",
                            "layar intro level + prompt input-mode"),
    "sprite_cache": ("ported", "godot_rebuild/scripts/ui/sprite_cache.gd",
                     "func get_or_render(",
                     "cache surface sprite, evict FIFO 2000 entri"),
    "render_cache": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                     "func get_glow_surface(",
                     "cache font/lingkaran/glow + shortcut global"),
}

CLASS_TARGETS = {
    "MapRenderer": ("ported", "godot_rebuild/scripts/ui/map_renderer.gd",
                    "func is_click_on_shop(",
                    "lane, slot shop dan klik; draw di dynamic_map_renderer.gd"),
    "FloatingText": ("ported", "godot_rebuild/scripts/ui/floating_text.gd",
                     "func presentation_state()",
                     "angka damage: drift, lifetime 45, skala pop"),
    "HitParticle": ("ported", "godot_rebuild/scripts/ui/hit_particle.gd",
                    "func update() -> void:",
                    "partikel benturan, gesekan 0.95 + gravitasi 0.15"),
    "DeathExplosion": ("ported", "godot_rebuild/scripts/ui/death_explosion.gd",
                       "func get_particle_snapshot(",
                       "ledakan kematian + kilatan 8 tick"),
    "ScreenShake": ("ported", "godot_rebuild/scripts/ui/screen_shake.gd",
                    "func get_offset() -> Vector2i:",
                    "shake meluruh 0.85, cutoff 0.5"),
    "EffectManager": ("ported", "godot_rebuild/scripts/ui/effect_manager.gd",
                      "func register_kill(",
                      "orkestrator semua efek + cache state"),
    "ComboCounter": ("ported", "godot_rebuild/scripts/ui/combo_counter.gd",
                     "func add_kill(",
                     "combo 3 kill, FLASH 20, POP 1.3"),
    "WaveAnnouncer": ("ported", "godot_rebuild/scripts/ui/wave_announcer.gd",
                      "func announce(value: int) -> void:",
                      "pita gelombang: slide masuk 0.2, tahan 0.7"),
    "KillFeed": ("ported", "godot_rebuild/scripts/ui/kill_feed.gd",
                 "func add_kill(",
                 "feed kill 5 entri, umur 180 tick"),
    "PopupAnimation": ("ported", "godot_rebuild/scripts/ui/popup_animation.gd",
                       "func get_scale() -> float:",
                       "popup slide 30px, ease-out-back 1.70158"),
    "PathPreview": ("ported", "godot_rebuild/scripts/ui/path_preview.gd",
                    "func show(lane_paths: Array) -> void:",
                    "pratinjau jalur: dash 20/2, panah 8/5"),
    "AchievementPopup": ("ported", "godot_rebuild/scripts/ui/achievement_popup.gd",
                         "func unlock(",
                         "popup achievement 280x60, glow 150"),
    "BossDeathAnimation": ("ported", "godot_rebuild/scripts/ui/boss_death_animation.gd",
                           "func get_celebration_visual_state(",
                           "tiga fase kematian + selebrasi true boss"),
    "BossIntroCinematic": ("ported", "godot_rebuild/scripts/ui/boss_intro_cinematic.gd",
                           "func handle_skip(",
                           "banner intro 100 tick, fade 12/20, slide 18"),
    "LevelIntroScreen": ("ported", "godot_rebuild/scripts/ui/level_intro_screen.gd",
                         "func handle_skip(",
                         "intro level 120 tick + prompt touch/keyboard"),
    "SpriteCache": ("ported", "godot_rebuild/scripts/ui/sprite_cache.gd",
                    "static func get_shared()",
                    "singleton: cache penuh + versi crop"),
    "RenderCache": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                    "static func get_shared()",
                    "singleton: font, lingkaran, glow"),
}

METHOD_ALIASES = {
    ("MapRenderer", "draw"): ("dynamic_map_renderer.gd",
                              "func draw(canvas: CanvasItem, t: int) -> void:",
                              "draw peta: art statis + overlay dinamis"),
    ("FloatingText", "draw"): ("floating_text.gd", "func presentation_state()",
                               "draw() jadi presentation_state(); view mengeblit"),
    ("HitParticle", "draw"): ("hit_particle_layout.gd", "static func ops(",
                              "ops() menggambar partikel"),
    ("DeathExplosion", "draw"): ("death_explosion_layout.gd", "static func ops(",
                                 "ops() menggambar ledakan"),
    ("DeathExplosion", "alive"): ("death_explosion.gd", "func is_alive() -> bool:",
                                  "properti `alive` jadi method is_alive()"),
    ("EffectManager", "draw"): ("scenes/prototype/prototype_view.gd",
                                "func _draw_world_effects(",
                                "efek dunia digambar view (ikut shake)"),
    ("EffectManager", "draw_ui"): ("scenes/prototype/prototype_view.gd",
                                   "func _draw_wave_announcer(",
                                   "efek UI digambar view tanpa shake"),
    ("ComboCounter", "draw"): ("combo_counter_layout.gd", "static func ops(",
                               "ops() menggambar combo"),
    ("WaveAnnouncer", "draw"): ("wave_announcer.gd", "func visual_rect(",
                                "layout pita diekspos sebagai visual_rect/alpha"),
    ("KillFeed", "draw"): ("kill_feed_layout.gd", "static func ops(",
                           "ops() menggambar feed"),
    ("PathPreview", "draw"): ("path_preview.gd", "static func arrow_points(",
                              "geometry dash/panah diekspos untuk view"),
    ("AchievementPopup", "draw"): ("scenes/prototype/prototype_view.gd",
                                   "func _draw_achievement_popup(",
                                   "panel achievement digambar view"),
    ("AchievementPopup", "_draw_icon"): ("achievement_popup.gd", "func icon_ops(",
                                         "ikon vektor jadi icon_ops()"),
    ("BossDeathAnimation", "draw"): ("boss_death_sequence_layout.gd", "static func ops(",
                                     "ops() menggambar fase kematian"),
    ("BossDeathAnimation", "_draw_death_sequence"): (
        "boss_death_sequence_layout.gd", "static func ops(",
        "gelombang ledakan, fragmen, partikel naik"),
    ("BossDeathAnimation", "_draw_celebration"): (
        "boss_celebration_layout.gd", "static func ops(",
        "selebrasi true boss (hint input-mode lewat skip_hint.gd)"),
    ("BossDeathAnimation", "_init_fragments"): (
        "boss_death_animation.gd", "func _make_fragments(",
        "_init_fragments jadi _make_fragments"),
    ("BossDeathAnimation", "_init_rising_particles"): (
        "boss_death_animation.gd", "func _make_rising_particles(",
        "_init_rising_particles jadi _make_rising_particles"),
    ("BossIntroCinematic", "_init_fonts"): (
        "boss_intro_layout.gd", "const NAME_SIZE := 46",
        "ukuran font intro jadi konstanta layout (66/46/24)"),
    ("BossIntroCinematic", "draw"): ("boss_intro_layout.gd", "static func ops(",
                                     "banner strip: rect, tick sudut, teks, bar"),
    ("LevelIntroScreen", "draw"): ("level_intro_layout.gd", "static func ops(",
                                   "layar intro penuh sebagai op list"),
    ("LevelIntroScreen", "_draw_level_info"): ("level_intro_layout.gd",
                                               "func _level_info(",
                                               "nama level, tema, info gelombang"),
    ("LevelIntroScreen", "_draw_boss_preview"): ("level_intro_layout.gd",
                                                 "func _boss_preview(",
                                                 "kartu boss + siluet di intro"),
    ("LevelIntroScreen", "_draw_boss_silhouette"): ("level_intro_layout.gd",
                                                    "func _silhouette(",
                                                    "siluet boss level intro"),
    ("LevelIntroScreen", "_draw_space_prompt"): ("level_intro_layout.gd",
                                                 "func _space_prompt(",
                                                 "bar prompt + teks input-mode"),
    ("SpriteCache", "__new__"): ("sprite_cache.gd", "static func get_shared()",
                                 "singleton pygame jadi get_shared()"),
    ("SpriteCache", "__init__"): ("sprite_cache.gd",
                                  "var max_cache := DEFAULT_MAX_CACHE",
                                  "isi cache, kapasitas 2000, hit/miss"),
    ("RenderCache", "__new__"): ("render_cache.gd", "static func get_shared()",
                                 "singleton pygame jadi get_shared()"),
    ("RenderCache", "__init__"): ("render_cache.gd", "var _fonts: Array = []",
                                  "tiga kamus cache + statistik"),
}

# `__init__` rows that are a plain constructor of a ported class.
DEFAULT_INIT_TARGETS = {
    "MapRenderer": ("map_renderer.gd", "var map_width := MAP_WIDTH",
                    "konstruktor peta: ukuran peta + font"),
    "FloatingText": ("floating_text.gd", "func configure(", "konfigurasi teks"),
    "HitParticle": ("hit_particle.gd", "var x := 0.0", "partikel baru"),
    "DeathExplosion": ("death_explosion.gd", "var team := \"red\"", "ledakan baru"),
    "ScreenShake": ("screen_shake.gd", "var intensity := 0.0", "shake baru"),
    "EffectManager": ("effect_manager.gd", "func _reset_effects(",
                      "orkestrator baru: empat daftar efek"),
    "ComboCounter": ("combo_counter.gd", "var count := 0", "combo baru"),
    "WaveAnnouncer": ("wave_announcer.gd", "var active := false", "pita baru"),
    "KillFeed": ("kill_feed.gd", "var entries: Array[Dictionary] = []",
                 "feed baru"),
    "PopupAnimation": ("popup_animation.gd", "var progress := 0.0", "popup baru"),
    "PathPreview": ("path_preview.gd", "var paths: Array = []", "pratinjau baru"),
    "AchievementPopup": ("achievement_popup.gd", "var queue: Array = []",
                         "popup baru: antrean achievement"),
    "BossDeathAnimation": ("boss_death_animation.gd", "func configure(",
                           "animasi baru (konfigurasi boss)"),
    "BossIntroCinematic": ("boss_intro_cinematic.gd", "var sound_played := false",
                           "banner baru"),
    "LevelIntroScreen": ("level_intro_screen.gd", "var timer := 0", "intro baru"),
}

TOP_TARGETS = {
    "_font_path": ("ported", "godot_rebuild/scripts/ui/source_fonts.gd",
                   "static func file_for_style(",
                   "gaya -> nama file TTF, default Barlow-Regular.ttf"),
    "_make_font": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                   "func get_font(size: int",
                   "font TTF + fallback sistem"),
    "title_font": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                   "static func get_cached_font(",
                   "Cinzel untuk judul, clamp 8..220"),
    "_ease_out_back": ("ported", "godot_rebuild/scripts/ui/popup_animation.gd",
                       "static func _ease_out_back(",
                       "popup/achievement bounce, c1 1.70158"),
    "_ease_in_back": ("ported", "godot_rebuild/scripts/ui/wave_announcer.gd",
                      "static func _ease_in_back(",
                      "slide keluar pita gelombang"),
    "_ease_out_cubic": ("dead", "", "",
                        "didefinisikan tapi tidak pernah dipanggil di pohon pygame"),
    "_ease_out_elastic": ("dead", "", "",
                          "didefinisikan tapi tidak pernah dipanggil di pohon pygame"),
    "_begin_prompt_text": ("ported", "godot_rebuild/scripts/ui/level_intro_screen.gd",
                           "func get_begin_prompt(",
                           "TAP TO BEGIN vs PRESS SPACE TO BEGIN"),
    "_skip_button_label": ("ported", "godot_rebuild/scripts/ui/skip_hint.gd",
                           "static func label(",
                           "TAP / label controller / SPACE"),
    "get_cached_sprite": ("ported", "godot_rebuild/scripts/ui/sprite_cache.gd",
                          "static func get_cached_sprite(",
                          "shortcut canvas penuh"),
    "get_cached_sprite_cropped": ("ported", "godot_rebuild/scripts/ui/sprite_cache.gd",
                                  "static func get_cached_sprite_cropped(",
                                  "shortcut versi crop + jangkar"),
    "clear_sprite_cache": ("ported", "godot_rebuild/scripts/ui/sprite_cache.gd",
                           "static func clear_sprite_cache(",
                           "kosongkan cache sprite"),
    "get_font": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                 "static func get_cached_font(",
                 "shortcut font ter-cache"),
    "get_circle": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                   "static func get_cached_circle(",
                   "shortcut lingkaran ter-cache"),
    "get_glow": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                 "static func get_cached_glow(",
                 "shortcut glow ter-cache"),
    "clear_cache": ("ported", "godot_rebuild/scripts/ui/render_cache.gd",
                    "static func clear_shared_cache(",
                    "kosongkan cache render"),
}

ASSIGN_TARGETS = {
    "_FONT_DIR": ("data", "godot_rebuild/scripts/ui/source_fonts.gd",
                  'const REGULAR = preload("res://assets/fonts/Barlow-Regular.ttf")',
                  "direktori font pygame = assets/fonts"),
    "_TITLE_FONT_FILE": ("data", "godot_rebuild/scripts/ui/source_fonts.gd",
                         'const TITLE = preload("res://assets/fonts/Cinzel.ttf")',
                         "Cinzel untuk gaya title"),
    "_BODY_FONT_FILES": ("data", "godot_rebuild/scripts/ui/source_fonts.gd",
                         "const STYLE_FILES := {",
                         "empat bobot Barlow"),
    "_SYS_FALLBACKS": ("deviation", "godot_rebuild/scripts/ui/source_fonts.gd",
                       'const DEFAULT_FILE := "Barlow-Regular.ttf"',
                       "Godot membundel TTF; rantai SysFont tidak diperlukan"),
    "_STYLE_FONT_MAP": ("data", "godot_rebuild/scripts/ui/source_fonts.gd",
                        '"body_semibold": "Barlow-SemiBold.ttf",',
                        "gaya -> file, dipakai _font_path"),
    "_sprite_cache": ("data", "godot_rebuild/scripts/ui/sprite_cache.gd",
                      "static var _shared", "singleton modul SpriteCache"),
    "_cache": ("data", "godot_rebuild/scripts/ui/render_cache.gd",
               "static var _shared", "singleton modul RenderCache"),
}
HISTOGRAM_KEYS = ("data", "dead", "deviation", "folded", "ported")


def source_lines():
    return RENDER.read_text(encoding="utf-8").splitlines()


def source_tree():
    return ast.parse("\n".join(source_lines()))


def section_of(line):
    for name, start, end in SECTIONS:
        if start <= line <= end:
            return name
    return "unknown"


# ── stub pygame + the real module ────────────────────────────────────────
class _Rect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x, self.y, self.w, self.h = x, y, w, h

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    @property
    def width(self):
        return self.w

    @property
    def height(self):
        return self.h


class _Surface:
    def __init__(self, size=(8, 8), flags=0):
        self.width = int(size[0]) if isinstance(size, (tuple, list)) else 8
        self.height = int(size[1]) if isinstance(size, (tuple, list)) else 8
        self.size = (self.width, self.height)

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_size(self):
        return self.size

    def get_rect(self, **kwargs):
        return _Rect(0, 0, self.width, self.height)

    def get_bounding_rect(self, min_alpha=1):
        return _Rect(0, 0, self.width, self.height)

    def blit(self, *args, **kwargs):
        return _Rect()

    def fill(self, *args, **kwargs):
        return _Rect()

    def copy(self):
        return _Surface(self.size)

    def convert(self):
        return self

    def convert_alpha(self):
        return self

    def subsurface(self, rect):
        if isinstance(rect, _Rect):
            return _Surface((max(1, rect.w), max(1, rect.h)))
        return _Surface(rect[2:4] if len(rect) > 3 else self.size)

    def set_colorkey(self, *args, **kwargs):
        return None

    def set_alpha(self, *args, **kwargs):
        return None

    def set_at(self, *args, **kwargs):
        return None


class _Font:
    """Records how `_make_font` resolved a (path, size) pair."""

    calls = []

    def __init__(self, path=None, size=12, bold=False, **kwargs):
        self.path = path
        self.size = size
        self.bold = bold
        self.bold_set = False
        _Font.calls.append({"path": None if path is None else str(path),
                            "size": int(size)})

    def set_bold(self, bold=True):
        self.bold = bool(bold)
        self.bold_set = True

    def set_italic(self, italic=True):
        return None

    def render(self, text, antialias=True, color=(255, 255, 255)):
        return _Surface()

    def get_height(self):
        return int(self.size)

    def get_ascent(self):
        return int(self.size * 0.8)

    def size_of(self, text):
        return (len(str(text)) * 6, int(self.size))


def _stub_pygame():
    pygame = types.ModuleType("pygame")
    pygame.SRCALPHA = 0x00010000
    pygame.Surface = _Surface
    pygame.Rect = lambda *args, **kwargs: _Rect(*args[:4] if len(args) >= 4 else ())
    for name in ("draw", "transform", "font", "time", "mixer", "gfxdraw", "image",
                 "display", "key", "locals"):
        module = types.ModuleType("pygame." + name)
        setattr(pygame, name, module)
        sys.modules["pygame." + name] = module
    for fn in ("circle", "rect", "line", "polygon", "aaline", "aalines", "lines",
               "ellipse", "arc", "polygon", "antialiased"):
        setattr(pygame.draw, fn, lambda *a, **k: None)
    pygame.draw.aacircle = lambda *a, **k: None
    pygame.transform.smoothscale = lambda surface, size: _Surface(size)
    pygame.transform.scale = lambda surface, size: _Surface(size)
    pygame.transform.rotate = lambda surface, angle: surface
    pygame.transform.flip = lambda surface, *a, **k: surface
    _Font.calls = []
    pygame.font.Font = lambda path=None, size=12, **kwargs: _Font(path, size)
    pygame.font.SysFont = lambda name, size=12, bold=False, **kwargs: _Font(
        "/sys/" + str(name), size, bold)
    pygame.font.get_init = lambda: True
    pygame.font.init = lambda: None
    pygame.time.get_ticks = lambda: 0
    pygame.time.Clock = lambda: types.SimpleNamespace(tick=lambda *a: 0)
    pygame.key = sys.modules["pygame.key"]
    pygame.key.get_pressed = lambda: [False] * 512
    pygame.K_SPACE = 32
    pygame.K_ESCAPE = 27
    pygame.K_RETURN = 13
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


def _platform_stub(touch_mode=False):
    package = types.ModuleType("mobile")
    platform_utils = types.ModuleType("mobile.platform_utils")
    platform_utils.TOUCH_MODE = touch_mode
    package.platform_utils = platform_utils
    sys.modules["mobile"] = package
    sys.modules["mobile.platform_utils"] = platform_utils
    return platform_utils


def _ui_theme_stub():
    theme = types.ModuleType("ui_theme")
    theme.corner_ticks = lambda *a, **k: None
    theme.gradient_text = lambda text, *a, **k: None
    theme.letter = lambda text, gap=" ": gap.join(str(text))
    theme.fit_ellipsis = lambda text, font, width: text
    sys.modules["ui_theme"] = theme
    return theme


def render_module():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    _stub_pygame()
    _core_namespace()
    _platform_stub(False)
    _ui_theme_stub()
    sys.modules.pop("_render", None)
    return importlib.import_module("_render")


# ── executed cases ───────────────────────────────────────────────────────
EASING_CASES = ("_ease_out_back", "_ease_in_back", "_ease_out_cubic",
                "_ease_out_elastic")
EASING_INPUTS = [0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99, 1.0]


def easing_cases(render):
    rows = {}
    for name in EASING_CASES:
        func = getattr(render, name)
        rows[name] = [round(float(func(t)), 9) for t in EASING_INPUTS]
    rows["inputs"] = EASING_INPUTS
    return rows


class _ControllerManager:
    def __init__(self, label):
        self.label = label
        self.mode = True

    def is_controller_mode(self):
        return self.mode

    def get_action_label(self, action):
        return self.label if action == "skip" else "?"


def prompt_cases(render):
    platform_utils = sys.modules["mobile.platform_utils"]
    main = sys.modules["__main__"]
    had_instance = hasattr(main, "game_instance")
    previous = getattr(main, "game_instance", None)
    rows = {}
    try:
        platform_utils.TOUCH_MODE = False
        if hasattr(main, "game_instance"):
            delattr(main, "game_instance")
        rows["begin_prompt_keyboard"] = render._begin_prompt_text()
        rows["skip_label_keyboard"] = render._skip_button_label()

        platform_utils.TOUCH_MODE = True
        rows["begin_prompt_touch"] = render._begin_prompt_text()
        rows["skip_label_touch"] = render._skip_button_label()

        platform_utils.TOUCH_MODE = False
        for label in ("A", "Cross"):
            main.game_instance = types.SimpleNamespace(
                controller_mgr=_ControllerManager(label))
            rows["skip_label_controller_%s" % label] = render._skip_button_label()

        manager = _ControllerManager("A")
        manager.mode = False
        main.game_instance = types.SimpleNamespace(controller_mgr=manager)
        rows["skip_label_controller_mode_off"] = render._skip_button_label()
        main.game_instance = types.SimpleNamespace(controller_mgr=None)
        rows["skip_label_no_manager"] = render._skip_button_label()
    finally:
        platform_utils.TOUCH_MODE = False
        if had_instance:
            main.game_instance = previous
        elif hasattr(main, "game_instance"):
            delattr(main, "game_instance")
    rows["hint_continue_keyboard"] = "[%s] to continue" % rows["skip_label_keyboard"]
    rows["hint_continue_touch"] = "[%s] to continue" % rows["skip_label_touch"]
    rows["hint_skip_touch_line"] = "[%s] to skip" % rows["skip_label_touch"]
    return rows


def font_cases(render):
    styles = {}
    for style in ("title", "body", "body_medium", "body_semibold", "body_bold"):
        styles[style] = os.path.basename(render._font_path(style))
    styles["unknown"] = os.path.basename(render._font_path("nope"))

    _Font.calls = []
    body = render._make_font(24, "body", False)
    body_call = dict(_Font.calls[-1])
    title = render.title_font(66)
    title_call = dict(_Font.calls[-1])
    _Font.calls = []
    clamped = render.title_font(400)
    clamp_call = dict(_Font.calls[-1])
    return {
        "styles": styles,
        "title_file": render._TITLE_FONT_FILE,
        "body_files": dict(render._BODY_FONT_FILES),
        "style_map": dict(render._STYLE_FONT_MAP),
        "system_fallbacks": list(render._SYS_FALLBACKS),
        "font_dir_tail": os.path.basename(render._FONT_DIR),
        "make_font": {"style": "body", "size": 24, "resolved_size": body_call["size"],
                      "resolved_file": os.path.basename(body_call["path"] or ""),
                      "bold": bool(body.bold)},
        "title_font": {"size": 66, "resolved_size": title_call["size"],
                       "resolved_file": os.path.basename(title_call["path"] or ""),
                       "bold": bool(title.bold)},
        "title_clamp": {"requested": 400, "resolved_size": clamp_call["size"]},
    }


def cache_cases(render):
    rendered = []

    def paint(surface):
        size = surface.get_size()
        rendered.append([int(size[0]), int(size[1])])

    sprite = render._sprite_cache
    sprite.clear()
    sprite._hits = 0
    sprite._misses = 0
    first = render.get_cached_sprite(("idle", "blue", 1, "walk"), 40, 40, paint)
    second = render.get_cached_sprite(("idle", "blue", 1, "walk"), 40, 40, paint)
    cropped = render.get_cached_sprite_cropped(
        ("idle", "red", 1, "walk"), 40, 40, paint, anchor=(20, 36))
    sprite_stats = dict(sprite.get_stats())
    render.clear_sprite_cache()
    cleared_stats = dict(sprite.get_stats())
    invalidate_hits = None
    render.get_cached_sprite(("a", 1), 8, 8, paint)
    render.get_cached_sprite(("b", 1), 8, 8, paint)
    sprite.invalidate("a")
    invalidate_hits = dict(sprite.get_stats())

    render.clear_cache()
    cache = render._cache
    font_a = render.get_font(20, "title", True)
    font_b = render.get_font(20, "title", True)
    circle_a = render.get_circle(10, (255, 0, 0), 0)
    circle_b = render.get_circle(10, (255, 0, 0), 0)
    glow = render.get_glow(12, (0, 255, 0), 3)
    glow_again = render.get_glow(12, (0, 255, 0), 3)
    clamp_high = render.get_font(400, "body", False)
    clamp_low = render.get_font(1, "body", False)
    render_stats = dict(cache.get_stats())
    render.clear_cache()
    cleared_render = dict(cache.get_stats())
    return {
        "sprite": {
            "renders": len(rendered),
            "sizes": rendered,
            "same_full_surface": first is second,
            "cropped_anchor": [int(cropped[1]), int(cropped[2])],
            "stats": sprite_stats,
            "cleared": cleared_stats,
            "after_invalidate": invalidate_hits,
            "max_cache": int(sprite._max_cache),
        },
        "render": {
            "same_font": font_a is font_b,
            "same_circle": circle_a is circle_b,
            "font_size": int(font_a.size),
            "font_bold": bool(font_a.bold),
            "same_glow": glow is glow_again,
            "glow_size": [int(glow.get_width()), int(glow.get_height())],
            "font_clamp": [int(clamp_low.size), int(clamp_high.size)],
            "stats": render_stats,
            "cleared": cleared_render,
        },
    }


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
        "file": "_render.py",
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
    """`class -> {method -> names called through self}` from the real source."""
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
                    if isinstance(owner, ast.Name) and owner.id == "self":
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
            name for name in ("__init__", "draw", "update") if name in methods]
        reachable = _reachable(graph, node.name, roots)
        names = _func_names(target) if target else set()
        for method in methods:
            symbol = "class:%s.%s" % (node.name, method)
            alias = METHOD_ALIASES.get((node.name, method))
            if alias:
                file_name, alias_token, alias_note = alias
                alias_target = "godot_rebuild/scripts/ui/" + file_name \
                    if not file_name.startswith("scenes/") else "godot_rebuild/" + file_name
                rows.append({"symbol": symbol, "kind": "ported", "target": alias_target,
                             "token": alias_token, "note": alias_note})
                continue
            if method in names:
                rows.append({"symbol": symbol, "kind": "ported", "target": target,
                             "token": "func %s(" % method if method not in (
                                 "__init__",) else "func _init(",
                             "note": ""})
                continue
            if method == "__init__" and node.name in DEFAULT_INIT_TARGETS:
                file_name, init_token, init_note = DEFAULT_INIT_TARGETS[node.name]
                rows.append({"symbol": symbol, "kind": "ported",
                             "target": "godot_rebuild/scripts/ui/" + file_name,
                             "token": init_token, "note": init_note})
                continue
            if method not in reachable:
                rows.append({"symbol": symbol, "kind": "dead", "target": "",
                             "token": "",
                             "note": "tidak terjangkau dari API publik/draw() kelas"})
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
    tree = source_tree()
    found = {}
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


def class_suites():
    """Which per-class oracle/checks pair already pins each class's behaviour."""
    rows = {}
    for name in CLASS_TARGETS:
        snake = ""
        for index, char in enumerate(name):
            if char.isupper() and index:
                snake += "_"
            snake += char.lower()
        oracle = "godot_rebuild/tests/%s_source_oracle.py" % snake
        checks = "godot_rebuild/tests/%s_checks.gd" % snake
        rows[name] = {
            "oracle": oracle if (ROOT / oracle).is_file() else "",
            "checks": checks if (ROOT / checks).is_file() else "",
        }
    return rows


def source_fixture():
    render = render_module()
    rows = symbol_rows()
    histogram = {}
    for row in rows:
        histogram[row["kind"]] = histogram.get(row["kind"], 0) + 1
    for key in HISTOGRAM_KEYS:
        histogram.setdefault(key, 0)
    return {
        "file": inventory(),
        "sections": section_ranges(),
        "symbols": {"count": len(rows), "kinds": histogram},
        "classification": {row["symbol"]: {"kind": row["kind"],
                                           "target": row["target"],
                                           "token": row["token"],
                                           "note": row["note"]} for row in rows},
        "dead_helpers": sorted(row["symbol"] for row in rows if row["kind"] == "dead"),
        "duplicates": duplicates(),
        "easing": easing_cases(render),
        "prompts": prompt_cases(render),
        "fonts": font_cases(render),
        "caches": cache_cases(render),
        "suites": class_suites(),
    }


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
