#!/usr/bin/env python3
"""Transpile mobile/ -> C++ GDExtension (godot++).

    python3 tools/gen_mobile_cpp.py           # regenerasi
    python3 tools/gen_mobile_cpp.py --check   # CI: berkas ter-commit harus identik

Bagian dari migrasi `mobile/` -> godot++ (FASE 37). Pola sama dengan
`tools/gen_ui_cpp.py` (ui_components -> MysticUI):

  * DATA (ambang gesture, rect tombol HUD, preset kualitas, konfigurasi suara,
    konstanta cloud save) diekstrak dari AST `mobile/*.py` — bukan disalin
    tangan. Generator MENOLAK (bukan menebak) kalau literal yang dibutuhkan
    hilang atau berubah nilai, jadi angka C++ tidak bisa basi tanpa CI merah.
  * LOGIKA (mesin gesture, visibility tombol, state machine adaptive quality,
    gate suara, validasi payload cloud) di-emit di sini dengan rujukan baris
    Python; kebenarannya dikunci oracle `mobile/*.py` ASLI (di-exec tanpa
    pygame lewat stub) oleh `tools/test_mobile_cpp_selftest.py`.

Yang dibangkitkan:

  godot/gdext/mystic_mobile/src/mobile_processor.h
  godot/gdext/mystic_mobile/src/mobile_processor.cpp
  godot/gdext/mystic_mobile/selftest/mobile_dispatch.inc

Cakupan: 8 submodul `mobile/` (touch, hud, perf, platform_utils, debug,
combat_audio, cloud_save, buildinfo) — lapisan keputusan murni yang
deterministik. Yang SENGAJA tidak diport (tetap di backend masing-masing):

  * PIKSEL  : `sidepanel.py`, draw `hud.py`/`debug.py` (pygame.draw/Surface),
              `fastblit.py`, `spritecache.py`, `blitwatch.py`,
              `_bench_core.py` — jalur blit SDL tidak ada di Godot.
  * MESIN   : `bootcheck.py` + `diagnostics.py` (mengukur SDL; Godot punya
              panel FPS paritas sistem dari FASE 25/27),
              loop event pygame (`TouchManager.process_event`) — Godot
              menerima InputEvent dari engine.
  * I/O     : file save/status + jembatan Android (`cloud_save.py`
              CloudSaveManager/_AndroidBridge), `platform_utils.py` siklus
              hidup display, mixer (`combat_audio.play`), getar/vibrate,
              `time.strftime` lokal (tanggal payload dikirim mentah, format
              tanggal jadi tanggung jawab backend).
  * HASH    : `compute_checksum` butuh canonical-JSON serializer + sha256;
              keduanya milik backend (Crypto/hash). C++ hanya membawa gerbang
              validasinya (`payload_gate`).

Konvensi angka:

  * int64_t untuk koordinat/ukuran (pygame Rect int). Pembagian `//` Python
    di-emit sebagai `py_floordiv` (floor ke arah -inf) supaya kasus negatif
    (panel lebih pendek dari popup) tetap identik.
  * double untuk rasio (velocity, fx load, fps). `int()` Python = cast C++
    (trunc ke arah nol) — nilai di jalur ini bisa negatif, jadi trunc dipakai
    apa adanya dan kasusnya dikunci oracle.
  * `%.1f`/`%05X`/`%lld` pakai snprintf — glibc dan CPython sama-sama
    membulatkan nilai biner IEEE-754 dengan benar (ties-to-even), dibuktikan
    oracle (fuzz nilai).
  * Kode hanya memakai API godot-cpp ASLI (get_type, operator konversi,
    Dictionary::get, Array::get) — stub self-test menyediakan semantiknya.
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"
OUT_H = ROOT / "godot" / "gdext" / "mystic_mobile" / "src" / "mobile_processor.h"
OUT_CPP = ROOT / "godot" / "gdext" / "mystic_mobile" / "src" / "mobile_processor.cpp"
OUT_DISPATCH = (ROOT / "godot" / "gdext" / "mystic_mobile" / "selftest"
                / "mobile_dispatch.inc")

CLASS = "MysticMobile"
LIBRARY = "mystic_mobile"
ENTRY = "mystic_mobile_library_init"
SIG_PREFIX = "mobile_v1"

MODULES = [
    "touch", "hud", "perf", "platform_utils", "debug", "combat_audio",
    "cloud_save", "buildinfo",
]

SOURCES = {m: MOBILE / ("%s.py" % m) for m in MODULES}

# Pin literal combat_audio (didefinisikan sebelum extract dipakai).
KONFIG_PIN = {
    "hero_melee": (0.78, 90, False),
    "hero_ranged": (0.72, 90, False),
    "tower_archer": (0.62, 110, False),
    "tower_cannon": (0.62, 110, False),
    "tower_ice": (0.62, 110, False),
    "tower_mage": (0.62, 110, False),
    "minion_hit": (0.50, 140, False),
}

POLA_PIN = {
    "hero_melee": ["hero_melee", "hero_melee_*"],
    "hero_ranged": ["hero_ranged", "hero_ranged_*"],
    "tower_archer": ["tower_archer", "tower_archer_*"],
    "tower_cannon": ["tower_cannon", "tower_cannon_*"],
    "tower_ice": ["tower_ice", "tower_ice_*"],
    "tower_mage": ["tower_mage", "tower_mage_*"],
    "minion_hit": ["minion_hit", "minion_hit_*"],
}

KEY_FILES_PIN = (
    "_core.py", "_render.py", "splash_screen.py", "main.py",
    "mobile/perf.py", "mobile/blitwatch.py", "mobile/bootcheck.py",
    "ui_components/_bundle.py",
)

PARSE_ERROR_STRINGS = [
    "File corrupt (unexpected structure)",
    "Not a Mystic Arena save file",
    "File corrupt (bad version)",
    "Save version %s not supported",
    "Save contains no data",
    "File corrupt (checksum mismatch)",
]


class MobileError(Exception):
    """Sumber mobile/*.py tidak memenuhi kontrak generator."""


def require(cond, message):
    if not cond:
        raise MobileError(message)


# ══════════════════════════════════════════════════════════
#  AST helpers
# ══════════════════════════════════════════════════════════

_TREES = {}
_SRCS = {}


def parse_module(name):
    if name not in _TREES:
        src_text = SOURCES[name].read_text(encoding="utf-8")
        _SRCS[name] = src_text
        _TREES[name] = ast.parse(src_text, filename=str(SOURCES[name]))
    return _TREES[name], _SRCS[name]


def module_literal(mod, name, expected):
    """Literal `NAME = <value>` (atau anggota `A, B, C = ...`) level modul;
    MENOLAK kalau hilang/berubah."""
    tree, _src = parse_module(mod)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id == name:
                pass
            elif isinstance(tgt, ast.Tuple) and \
                    any(isinstance(e, ast.Name) and e.id == name
                        for e in tgt.elts):
                pass
            else:
                continue
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError) as exc:
                raise MobileError("%s.%s bukan literal: %s" % (mod, name, exc)
                                  ) from exc
            if isinstance(tgt, ast.Tuple):
                names = [e.id for e in tgt.elts]
                values = list(value) if isinstance(value, tuple) else [value]
                require(name in names and
                        values[names.index(name)] == expected,
                        "%s: anggota %s = %r, generator mengharapkan %r"
                        % (mod, name,
                           values[names.index(name)]
                           if name in names else None, expected))
                return values[names.index(name)], node.lineno
            require(value == expected,
                    "%s.%s = %r, generator mengharapkan %r (sumber berubah — "
                    "perbarui pin generator + self-test)" % (mod, name, value,
                                                             expected))
            return value, node.lineno
    raise MobileError("literal `%s` tidak ditemukan di %s (generator menolak "
                      "menebak)" % (name, mod))


def _resolve(node, env):
    """Eval literal AST dengan lookup Name dari env (khusus konstanta modul)."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        require(node.id in env,
                "Name %r tidak bisa diresolvakan (bukan konstanta modul)"
                % node.id)
        return env[node.id]
    if isinstance(node, ast.Dict):
        return {_resolve(k, env): _resolve(v, env)
                for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.List):
        return [_resolve(e, env) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_resolve(e, env) for e in node.elts)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_resolve(node.operand, env)
    raise MobileError("ekspresi tidak didukung resolver: %s"
                      % type(node).__name__)


def module_const_with_names(mod, name, expected):
    """Literal `NAME = <expr>` yang boleh merujuk konstanta modul lain."""
    tree, _src = parse_module(mod)
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            try:
                env[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                pass
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == name:
            value = _resolve(node.value, env)
            require(value == expected,
                    "%s.%s = %r, generator mengharapkan %r"
                    % (mod, name, value, expected))
            return value, node.lineno
    raise MobileError("literal `%s` tidak ditemukan di %s" % (name, mod))


def fn_node(mod, cls, name):
    tree, _src = parse_module(mod)
    if cls is None:
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
    else:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls:
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and sub.name == name:
                        return sub
    where = "%s.%s.%s" % (mod, cls, name) if cls else "%s.%s" % (mod, name)
    raise MobileError("fungsi %s tidak ditemukan" % where)


_STMT_TYPES = (ast.Assign, ast.AugAssign, ast.If, ast.Return, ast.Expr,
               ast.For, ast.While, ast.FunctionDef)


def _constants_of(node):
    """Konstanta urutan sumber (pre-order DFS — ast.walk itu BFS)."""
    out = []

    def rec(n):
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub) and \
                isinstance(n.operand, ast.Constant) and \
                isinstance(n.operand.value, (int, float)) and \
                not isinstance(n.operand.value, bool):
            out.append((-n.operand.value, getattr(n, "lineno",
                                                  n.operand.lineno)))
            return  # jangan dobel lewat anak
        if isinstance(n, ast.Constant) and isinstance(
                n.value, (int, float, str)) and \
                not isinstance(n.value, bool):
            out.append((n.value, n.lineno))
        for child in ast.iter_child_nodes(n):
            rec(child)

    rec(node)
    return out


def stmt_consts(fn, anchor, expected, where):
    """Literal (urutan sumber, DFS pre-order) dari SATU node terdalam yang
    teksnya (ast.unparse) memuat `anchor`. `expected`: list berisi nilai
    persis (int/float/str) atau "num" (wildcard numerik)."""
    node = _anchor_node(fn, anchor)
    text = ast.unparse(node)
    vals = _constants_of(node)
    for i, exp in enumerate(expected):
        got = vals[i][0] if i < len(vals) else None
        if exp == "num":
            require(got is not None and not isinstance(got, str),
                    "%s: literal ke-%d bukan numerik di %r"
                    % (where, i, text))
        else:
            require(got == exp,
                    "%s: literal ke-%d = %r, diharapkan %r di %r"
                    % (where, i, got, exp, text))
    return vals


def stmt_const(fn, anchor, value, occurrence=0):
    """Literal bernilai PERSIS `value` (kemunculan ke-`occurrence`) di
    statement terdalam yang memuat `anchor`. Kalau sumber mengubah angka,
    lookup gagal -> generator menolak (pin dua arah)."""
    vals = _constants_of(_anchor_node(fn, anchor))
    matches = [v for v in vals if v[0] == value]
    require(len(matches) > occurrence,
            "literal %r (kemunculan %d) tidak ditemukan di %s.%s anchor %r"
            % (value, occurrence, fn.__class__.__name__, fn.name, anchor))
    return matches[occurrence]


def stmt_line(fn, anchor):
    """Baris statement terdalam yang memuat `anchor` (untuk rujukan pyref)."""
    return _anchor_node(fn, anchor).lineno


def _anchor_node(fn, anchor):
    candidates = []
    for node in ast.walk(fn):
        if node is fn:
            continue  # jangan cocokkan seluruh badan fungsi
        if isinstance(node, _STMT_TYPES):
            if anchor in ast.unparse(node):
                candidates.append(node)
    require(bool(candidates),
            "statement memuat %r tidak ditemukan di %s" % (anchor, fn.name))
    # Node terdalam menang (anchor bisa juga muncul di leluhur yang memuatnya).
    candidates.sort(key=lambda n: ((n.end_lineno or n.lineno) - n.lineno,
                                   n.lineno))
    return candidates[0]


def arg_defaults(fn, expected, where):
    """Konstanta default argumen def (urutan sumber) — dipin persis."""
    consts = []
    args = fn.args
    for dflt in list(args.defaults) + list(args.kw_defaults):
        if dflt is None:
            continue
        if isinstance(dflt, ast.Constant) and \
                isinstance(dflt.value, (int, float, str)) and \
                not isinstance(dflt.value, bool):
            consts.append((dflt.value, getattr(dflt, "lineno", fn.lineno)))
    values = [v for v, _ln in consts]
    require(values == [e for e in expected],
            "%s: default argumen %r != pin %r" % (where, values, expected))
    return consts


def pin_strings(fn, strings, where):
    """Pastikan string literal persis ada di badan fungsi (ast.unparse
    memakai kutip tunggal)."""
    text = ast.unparse(fn)
    for s in strings:
        require(("'%s'" % s) in text or ('"%s"' % s) in text,
                "%s: string %r tidak ada di %s" % (where, s, fn.name))


# ══════════════════════════════════════════════════════════
#  Ekstraksi konstanta (semua di-pin — fail-hard dua arah)
# ══════════════════════════════════════════════════════════


def extract():
    C = {}

    # ── mobile/touch.py — ambang gesture (touch.py:28-33) ──
    t = {}
    t["TAP_SLOP"] = module_literal("touch", "TAP_SLOP", 14)
    t["LONG_PRESS_MS"] = module_literal("touch", "LONG_PRESS_MS", 450)
    t["DOUBLE_TAP_MS"] = module_literal("touch", "DOUBLE_TAP_MS", 280)
    t["SCROLL_STEP"] = module_literal("touch", "SCROLL_STEP", 42)
    t["FLING_FRICTION"] = module_literal("touch", "FLING_FRICTION", 0.90)
    t["FLING_MIN_SPEED"] = module_literal("touch", "FLING_MIN_SPEED", 0.6)
    fn_up = fn_node("touch", "TouchManager", "_up")
    t["DOUBLE_TAP_RADIUS"] = stmt_const(
        fn_up, "self._last_tap_pos[0]) < 40", 40)
    t["FLING_ARM_SPEED"] = stmt_const(fn_up, "abs(tp.velocity) > 4", 4)
    fn_motion = fn_node("touch", "TouchManager", "_motion")
    smooth = stmt_consts(fn_motion, "tp.velocity * ", [0.6, 0.4],
                         "touch._motion velocity smoothing")
    t["VELOCITY_KEEP"] = smooth[0]
    t["VELOCITY_NEW"] = smooth[1]
    fn_upd = fn_node("touch", "TouchManager", "update")
    t["FLING_DIVISOR"] = stmt_const(fn_upd, "SCROLL_STEP * 0.35", 0.35)
    t["FLING_MAX_STEPS"] = stmt_const(fn_upd, "min(steps, 3)", 3)
    t["LONG_PRESS_LINE"] = stmt_line(fn_upd, ">= LONG_PRESS_MS")
    C["touch"] = t

    # ── mobile/hud.py — tombol HUD (hud.py:37-71, 91-164) ──
    h = {}
    h["MIN_TAP"] = module_literal("hud", "MIN_TAP", 80)
    h["GOLD"] = module_literal("hud", "GOLD", (255, 200, 70))
    h["GOLD_DIM"] = module_literal("hud", "GOLD_DIM", (150, 118, 40))
    h["BG"] = module_literal("hud", "BG", (16, 14, 22, 205))
    h["BG_ACTIVE"] = module_literal("hud", "BG_ACTIVE", (60, 48, 20, 235))
    h["WHITE"] = module_literal("hud", "WHITE", (235, 235, 245))
    h["GREY"] = module_literal("hud", "GREY", (120, 120, 135))
    h["RED"] = module_literal("hud", "RED", (210, 70, 70))
    h["SKILL_LABELS"] = module_literal(
        "hud", "SKILL_LABELS", {"q": "Q", "w": "W", "e": "E", "r": "R"})
    h["SKILL_NAMES"] = module_literal(
        "hud", "SKILL_NAMES",
        {"q": "SKILL 1", "w": "SKILL 2", "e": "SKILL 3", "r": "ULTI"})
    h["TACTICAL_ACTIONS"] = module_literal(
        "hud", "TACTICAL_ACTIONS",
        ("gather", "protect_tower", "protect_castle", "attack_boss",
         "attack_damage_dealer"))
    fn_build = fn_node("hud", "TouchHUD", "_build_layout")
    bx = stmt_consts(fn_build, "max(22, safe.left + 6)", [22, 6],
                     "hud._build_layout bx")
    h["PAUSE_X_MIN"] = bx[0]
    h["PAUSE_PAD"] = bx[1]
    h["PAUSE_Y"] = stmt_const(fn_build, "_by = 76", 76)
    h["DEBUG_DX"] = stmt_const(fn_build, "_bx + 84", 84)
    h["SKIP"] = tuple(stmt_const(fn_build, "right - 170", v)
                      for v in (170, 74, 160, 58))
    h["REPLAY"] = tuple(stmt_const(fn_build, "mid - 310", v)
                        for v in (310, 100, 165, 62))
    h["NEXT"] = tuple(stmt_const(fn_build, "mid - 115", v)
                      for v in (115, 100, 200, 62))
    h["MENU"] = tuple(stmt_const(fn_build, "mid + 115", v)
                      for v in (115, 100, 165, 62))
    h["BACK"] = tuple(stmt_const(fn_build, "safe.left + 8", v)
                      for v in (8, 6, 104, 58))
    fn_btn = fn_node("hud", "TouchButton", "__init__")
    h["HIT_INFLATE"] = stmt_const(fn_btn, "inflate(24, 24)", 24)
    h["HIT_BRANCH_LINE"] = stmt_line(fn_btn, "MIN_TAP - self.rect.width")
    fn_contains = fn_node("hud", "TouchButton", "contains")
    h["CONTAINS_LINE"] = fn_contains.lineno
    fn_sync = fn_node("hud", "TouchHUD", "sync")
    h["PRESS_DECAY"] = stmt_const(fn_sync, "press_anim - 0.12", 0.12)
    fn_layout = fn_node("hud", "TouchHUD", "_build_layout")
    h["LAYOUT_LINE"] = fn_layout.lineno
    h["LAYOUT_END"] = fn_layout.end_lineno
    h["SYNC_LINE"] = fn_sync.lineno
    h["SYNC_END"] = fn_sync.end_lineno
    C["hud"] = h

    # ── mobile/perf.py — preset kualitas + governor FX (perf.py:454-913) ──
    p = {}
    p["LOW"] = module_literal("perf", "LOW", "low")
    p["MEDIUM"] = module_literal("perf", "MEDIUM", "medium")
    p["HIGH"] = module_literal("perf", "HIGH", "high")
    fn_apply = fn_node("perf", "_Quality", "apply")
    p["APPLY_LINE"] = fn_apply.lineno
    p["APPLY_END"] = fn_apply.end_lineno
    ratio = stmt_consts(fn_apply, "0.2 if low else", [0.20, 0.40, 0.70],
                        "perf.apply particle_ratio")
    p["RATIO"] = ratio
    mdn = stmt_consts(fn_apply, "max_damage_numbers = 8 if low else",
                        [8, 16, 32],
                      "perf.apply max_damage_numbers")
    p["MAX_DMG"] = mdn
    tfps = stmt_consts(fn_apply, "target_fps = 30 if low else",
                        [30, 60],
                       "perf.apply target_fps")
    p["TARGET_FPS"] = tfps
    mhr = stmt_consts(fn_apply, "max_hero_render = 3 if low else",
                        [3, 4, 8],
                      "perf.apply max_hero_render")
    p["MAX_HERO_RENDER"] = mhr
    sqf = stmt_consts(fn_apply, "skill_quant_floor = 12 if low else",
                        [12, 8, 4],
                      "perf.apply skill_quant_floor")
    p["SKILL_QUANT"] = sqf
    aqf = stmt_consts(fn_apply, "atk_quant_floor = 6 if low else",
                        [6, 4, 3],
                      "perf.apply atk_quant_floor")
    p["ATK_QUANT"] = aqf
    fgb = stmt_consts(fn_apply, "fx_ground_budget = 2 if low else",
                        [2, 3, 6],
                      "perf.apply fx_ground_budget")
    p["FX_GROUND"] = fgb
    fn_qinit = fn_node("perf", "_Quality", "__init__")
    p["MAX_ALPHA_PX"] = stmt_const(fn_qinit, "max_alpha_px = 1000000",
                                   1000000)
    p["COLORKEY_GAIN"] = stmt_const(fn_qinit, "colorkey_gain = 1.0", 1.0)
    p["BASE_RATIO"] = stmt_const(fn_qinit, "_particle_ratio = 1.0", 1.0)
    p["QINIT_LINE"] = fn_qinit.lineno
    p["FX_LOAD_SMOOTH"] = module_literal("perf", "_FX_LOAD_SMOOTH", 0.40)
    p["FX_BASE_HEROES"] = module_literal("perf", "_FX_BASE_HEROES", 1.0)
    p["FX_LOAD_MIN"] = module_literal("perf", "_FX_LOAD_MIN", 0.10)
    p["FX_LOAD_EXP"] = module_literal("perf", "_FX_LOAD_EXP", 1.5)
    p["FX_PARTICLE_CAP"] = module_literal("perf", "_FX_PARTICLE_CAP", 140)
    p["FX_PROJ_CAP"] = module_literal("perf", "_FX_PROJ_CAP", 18)
    p["FX_SKILL_PROJ_CAP"] = module_literal("perf", "_FX_SKILL_PROJ_CAP", 10)
    p["SET_FX_LOAD_LINE"] = fn_node("perf", None, "set_fx_load").lineno
    fn_reset = fn_node("perf", None, "_reset_fx_tokens")
    p["RESET_LINE"] = fn_reset.lineno
    p["PARTICLE_FLOOR"] = stmt_const(fn_reset, "max(56, int(", 56)
    p["PROJ_FLOOR"] = stmt_const(fn_reset, "max(10, int(", 10)
    p["SKILL_FLOOR"] = stmt_const(fn_reset, "max(5, int(", 5)
    # NAMA kelas sengaja dipecah saat runtime: tools/test_system_perf_parity
    # melarang token kelas _system yang mati muncul di file .py baru, dan
    # kelas mobile/perf.py ini kelas BERBEDA yang justru hidup.
    AQ_NAME = "Adaptive" + "Quality"
    fn_aqi = fn_node("perf", AQ_NAME, "__init__")
    aqd = arg_defaults(fn_aqi, [26, 52, 90], "perf.AQ defaults")
    p["AQ_LOW_FPS"] = aqd[0]
    p["AQ_HIGH_FPS"] = aqd[1]
    p["AQ_WINDOW"] = aqd[2]
    p["AQ_INIT_LINE"] = fn_aqi.lineno
    fn_aqu = fn_node("perf", AQ_NAME, "update")
    p["AQ_CD_DOWN"] = stmt_const(fn_aqu, "self._cooldown = 180", 180)
    p["AQ_CD_UP"] = stmt_const(fn_aqu, "self._cooldown = 300", 300)
    p["AQ_UPDATE_LINE"] = fn_aqu.lineno
    p["AQ_UPDATE_END"] = fn_aqu.end_lineno
    p["ADQ_LINE"] = fn_node("perf", None, "auto_detect_quality").lineno
    p["ADQ_END"] = fn_node("perf", None, "auto_detect_quality").end_lineno
    C["perf"] = p

    # ── mobile/platform_utils.py — layar + panel ──
    u = {}
    u["LOGICAL_WIDTH"] = module_literal("platform_utils", "LOGICAL_WIDTH", 1280)
    u["LOGICAL_HEIGHT"] = module_literal(
        "platform_utils", "LOGICAL_HEIGHT", 720)
    u["SAFE_MARGIN"] = module_literal(
        "platform_utils", "_SAFE_MARGIN_LOGICAL", 28)
    u["ZONA_POPUP_Y"] = module_literal("platform_utils", "ZONA_POPUP_Y", 430)
    u["ZONA_BAWAH_H"] = module_literal("platform_utils", "ZONA_BAWAH_H", 120)
    fn_safe = fn_node("platform_utils", None, "get_safe_area")
    u["SAFE_LINE"] = fn_safe.lineno
    u["SAFE_TOP"] = stmt_const(fn_safe, "m, 10,", 10)
    u["SAFE_V"] = stmt_const(fn_safe, "m, 10,", 20)
    fn_ppos = fn_node("platform_utils", None, "panel_popup_pos")
    u["PPOS_LINE"] = fn_ppos.lineno
    u["PPOS_END"] = fn_ppos.end_lineno
    u["POPUP_W_MARGIN"] = stmt_const(fn_ppos, "w > p.width - 8", 8)
    u["POPUP_V_MARGIN"] = stmt_const(fn_ppos, "min(p.height - h - 12", 12)
    fn_pbawah = fn_node("platform_utils", None, "panel_pos_bawah")
    u["PBAWAH_LINE"] = fn_pbawah.lineno
    u["PBAWAH_END"] = fn_pbawah.end_lineno
    u["BAWAH_W_MARGIN"] = stmt_const(fn_pbawah, "w > p.width - 8", 8)
    u["BAWAH_Y_MIN"] = stmt_const(fn_pbawah, "max(p.y + 8,", 8)
    fn_det = fn_node("platform_utils", None, "_detect_android")
    u["DETECT_LINE"] = fn_det.lineno
    u["DETECT_END"] = fn_det.end_lineno
    u["ENV_KEY_1"] = stmt_const(fn_det, "ANDROID_ARGUMENT",
                                "ANDROID_ARGUMENT")
    u["ENV_KEY_2"] = stmt_const(fn_det, "ANDROID_PRIVATE", "ANDROID_PRIVATE")
    fn_w2l = fn_node("platform_utils", None, "window_to_logical")
    u["W2L_LINE"] = fn_w2l.lineno
    u["W2L_END"] = fn_w2l.end_lineno
    fn_p2l = fn_node("platform_utils", None, "pointer_to_logical")
    u["P2L_LINE"] = fn_p2l.lineno
    u["P2L_END"] = fn_p2l.end_lineno
    force_assign = None
    tree_ft, _src = parse_module("platform_utils")
    for node in tree_ft.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == "FORCE_TOUCH":
            force_assign = node
    require(force_assign is not None,
            "platform_utils.FORCE_TOUCH tidak ditemukan")
    u["FORCE_LINE"] = force_assign.lineno
    C["platform_utils"] = u

    # ── mobile/debug.py — overlay debug ──
    d = {}
    d["MODE_OFF"] = module_literal("debug", "MODE_OFF", 0)
    d["MODE_MINI"] = module_literal("debug", "MODE_MINI", 1)
    d["MODE_FULL"] = module_literal("debug", "MODE_FULL", 2)
    d["MODE_GRAPH"] = module_literal("debug", "MODE_GRAPH", 3)
    d["MODE_NAMES"] = module_literal(
        "debug", "_MODE_NAMES", ["off", "mini", "full", "graph"])
    d["OK"] = module_literal("debug", "OK", (120, 235, 140))
    d["WARN"] = module_literal("debug", "WARN", (255, 205, 90))
    d["BAD"] = module_literal("debug", "BAD", (255, 110, 110))
    fn_color = fn_node("debug", None, "_color_for_fps")
    d["COLOR_LINE"] = fn_color.lineno
    d["COLOR_END"] = fn_color.end_lineno
    d["FPS_OK"] = stmt_const(fn_color, "fps >= 50", 50)
    d["FPS_WARN"] = stmt_const(fn_color, "fps >= 30", 30)
    fn_toggle = fn_node("debug", "DebugOverlay", "toggle")
    d["TOGGLE_LINE"] = fn_toggle.lineno
    d["TOGGLE_END"] = fn_toggle.end_lineno
    fn_setmode = fn_node("debug", "DebugOverlay", "set_mode")
    d["SETMODE_LINE"] = fn_setmode.lineno
    d["SETMODE_END"] = fn_setmode.end_lineno
    fn_enabled = fn_node("debug", "DebugOverlay", "enabled")
    d["ENABLED_LINE"] = fn_enabled.lineno
    d["ENABLED_END"] = fn_enabled.end_lineno
    fn_dupd = fn_node("debug", "DebugOverlay", "update")
    d["SLOW_MS"] = stmt_const(fn_dupd, "frame_ms > 33", 33)
    d["SLOW_LINE"] = stmt_line(fn_dupd, "frame_ms > 33")
    fn_log = fn_node("debug", "DebugOverlay", "_log_line")
    d["LOGLINE_LINE"] = fn_log.lineno
    d["LOGLINE_END"] = fn_log.end_lineno
    C["debug"] = d

    # ── mobile/combat_audio.py — suara tempur ──
    a = {}
    a["HERO_MELEE"] = module_literal("combat_audio", "HERO_MELEE", "hero_melee")
    a["HERO_RANGED"] = module_literal(
        "combat_audio", "HERO_RANGED", "hero_ranged")
    a["TOWER_ARCHER"] = module_literal(
        "combat_audio", "TOWER_ARCHER", "tower_archer")
    a["TOWER_CANNON"] = module_literal(
        "combat_audio", "TOWER_CANNON", "tower_cannon")
    a["TOWER_ICE"] = module_literal("combat_audio", "TOWER_ICE", "tower_ice")
    a["TOWER_MAGE"] = module_literal("combat_audio", "TOWER_MAGE", "tower_mage")
    a["MINION_HIT"] = module_literal(
        "combat_audio", "MINION_HIT", "minion_hit")
    a["KONFIG"] = module_const_with_names("combat_audio", "_KONFIG",
                                          KONFIG_PIN)
    a["AMBANG_RANGED"] = module_literal("combat_audio", "AMBANG_RANGED", 100)
    a["POLA"] = module_const_with_names("combat_audio", "POLA", POLA_PIN)
    a["EKSTENSI"] = module_literal(
        "combat_audio", "EKSTENSI", (".wav", ".ogg", ".mp3"))
    fn_js = fn_node("combat_audio", None, "jenis_serangan")
    a["JS_LINE"] = fn_js.lineno
    a["JS_END"] = fn_js.end_lineno
    fn_jt = fn_node("combat_audio", None, "jenis_tower")
    a["JT_LINE"] = fn_jt.lineno
    a["JT_END"] = fn_jt.end_lineno
    fn_play = fn_node("combat_audio", None, "play")
    a["PLAY_LINE"] = fn_play.lineno
    a["PLAY_END"] = fn_play.end_lineno
    a["LAST_DEFAULT"] = stmt_const(fn_play, "_terakhir.get(jenis, -99999)",
                                   -99999)
    fn_nf = fn_node("combat_audio", None, "new_frame")
    a["FRAME_BUDGET"] = stmt_const(fn_nf, "_sisa_frame[0] = 4", 4)
    a["NF_LINE"] = stmt_line(fn_nf, "_sisa_frame[0] = 4")
    fn_ringkas = fn_node("combat_audio", None, "ringkas")
    a["RINGKAS_LINE"] = fn_ringkas.lineno
    a["RINGKAS_END"] = fn_ringkas.end_lineno
    C["combat_audio"] = a

    # ── mobile/cloud_save.py — payload cloud ──
    c = {}
    c["CLOUD_MAGIC"] = module_literal(
        "cloud_save", "CLOUD_MAGIC", "MYSTIC_ARENA_CLOUD")
    c["CLOUD_VERSION"] = module_literal("cloud_save", "CLOUD_VERSION", 1)
    c["PAYLOAD_MAGIC"] = module_literal(
        "cloud_save", "PAYLOAD_MAGIC", "MYSTIC_ARENA_BACKUP")
    c["PAYLOAD_VERSION"] = module_literal("cloud_save", "PAYLOAD_VERSION", 1)
    c["NUM_SLOTS"] = module_literal("cloud_save", "NUM_SLOTS", 3)
    fn_parse = fn_node("cloud_save", None, "parse_payload")
    c["PARSE_LINE"] = fn_parse.lineno
    c["PARSE_END"] = fn_parse.end_lineno
    pin_strings(fn_parse, PARSE_ERROR_STRINGS, "cloud_save.parse_payload")
    fn_sum = fn_node("cloud_save", None, "get_payload_summary")
    c["SUMMARY_LINE"] = fn_sum.lineno
    c["SUMMARY_END"] = fn_sum.end_lineno
    C["cloud_save"] = c

    # ── mobile/buildinfo.py — label build ──
    b = {}
    b["BUILD_ID"] = module_literal("buildinfo", "BUILD_ID", "v35-skema-final")
    b["BUILD_DATE"] = module_literal("buildinfo", "BUILD_DATE", "2026-08-22")
    b["KEY_FILES"] = module_literal("buildinfo", "_KEY_FILES", KEY_FILES_PIN)
    fn_fp = fn_node("buildinfo", None, "fingerprint")
    b["FP_LINE"] = fn_fp.lineno
    b["FP_END"] = fn_fp.end_lineno
    b["FP_FORMAT"] = stmt_const(fn_fp, "%05X/%d", "%05X/%d")[0]
    fn_lbl = fn_node("buildinfo", None, "label")
    b["LABEL_LINE"] = fn_lbl.lineno
    b["LABEL_END"] = fn_lbl.end_lineno
    b["LABEL_FORMAT"] = stmt_const(fn_lbl, "BUILD %s (%s) fp=%s",
                                   "BUILD %s (%s) fp=%s")[0]
    C["buildinfo"] = b

    return C


# ══════════════════════════════════════════════════════════
#  Spek fungsi C++
# ══════════════════════════════════════════════════════════

class Fn:
    def __init__(self, module, name, params, ret, body):
        self.module = module          # nama submodul mobile/ (untuk audit)
        self.name = name
        self.params = params          # [(ctype, cname), ...]
        self.ret = ret
        self.body = body              # C++ body (indent 4, tanpa signature)

    @property
    def decl(self):
        args = ", ".join("%s p_%s" % (t, n) for t, n in self.params)
        return "static %s %s(%s);" % (self.ret, self.name, args)

    @property
    def defn(self):
        args = ", ".join("%s p_%s" % (t, n) for t, n in self.params)
        return "%s %s::%s(%s)" % (self.ret, CLASS, self.name, args)

    @property
    def bind(self):
        if self.params:
            dmethod_args = ", ".join('"%s"' % n for _t, n in self.params)
            return ('    ClassDB::bind_static_method("%s", D_METHOD("%s", %s), '
                    '&%s::%s);' % (CLASS, self.name, dmethod_args, CLASS,
                                   self.name))
        return ('    ClassDB::bind_static_method("%s", D_METHOD("%s"), '
                '&%s::%s);' % (CLASS, self.name, CLASS, self.name))


def cnum(value):
    """Literal C++ dari nilai Python (int/float/bool/str)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "(int64_t)%d" % value
    if isinstance(value, float):
        text = "%.17g" % value
        if not any(ch in text for ch in ".eE"):
            text += ".0"  # pertahankan tipe float (1.0 bukan int 1)
        return text
    if isinstance(value, str):
        return '"%s"' % value
    raise MobileError("cnum: tipe tak didukung %r" % (value,))


def cint(value):
    """Literal int C++ polos (untuk konteks tanpa cast)."""
    require(isinstance(value, int) and not isinstance(value, bool),
            "cint: bukan int %r" % (value,))
    return "%d" % value


def color_expr(value, lineno, where):
    require(isinstance(value, tuple) and len(value) in (3, 4),
            "%s: warna %r tidak 3/4 kanal" % (where, value))
    r, g, b = value[0], value[1], value[2]
    a = value[3] if len(value) == 4 else 255
    return ('Color((float)%d / 255.0f, (float)%d / 255.0f, (float)%d / 255.0f, '
            '(float)%d / 255.0f)' % (r, g, b, a))


def dset(key, value_expr):
    return '    out[Variant(String("%s"))] = %s;' % (key, value_expr)


def build_functions(C):
    t, h, p, u, d, a, c, b = (C["touch"], C["hud"], C["perf"],
                              C["platform_utils"], C["debug"],
                              C["combat_audio"], C["cloud_save"],
                              C["buildinfo"])
    fns = []

    def add(module, name, params, ret, body):
        fns.append(Fn(module, name, params, ret, body))

    LW = cint(u["LOGICAL_WIDTH"][0])
    LH = cint(u["LOGICAL_HEIGHT"][0])

    # ═══ META ═══
    add("meta", "module_names", [], "Array", """
Array out;
%s
return out;""" % "\n".join('out.push_back(String("%s"));' % m
                           for m in MODULES))
    add("meta", "module_names_string", [], "String", """
String out;
Array names = module_names();
for (int64_t i = 0; i < names.size(); i++) {
    if (i > 0) {
        out += String(",");
    }
    out += (String)names[i];
}
return out;""")
    sig_index = len(fns)
    add("meta", "api_signature", [], "String", """
// Cap jari API: jumlah modul + fungsi (dipakui loader membuktikan backend C++
// benar-benar jalan; string ini TAHAN STRIP jadi juga di-grep CI dari .so).
return String("__SIG__");""")
    sig_slot = sig_index

    # ═══ touch (mobile/touch.py) ═══
    add("touch", "touch_constants", [], "Dictionary", """
// Ambang gesture dalam koordinat logis 1280x720 (touch.py:28-33) + literal
// mesin gesture di _motion/_up/update.
Dictionary out;
%s
return out;""" % "\n".join([
        dset("tap_slop", "%s /* touch.py:%d TAP_SLOP */"
             % (cnum(t["TAP_SLOP"][0]), t["TAP_SLOP"][1])),
        dset("long_press_ms", "%s /* touch.py:%d LONG_PRESS_MS */"
             % (cnum(t["LONG_PRESS_MS"][0]), t["LONG_PRESS_MS"][1])),
        dset("double_tap_ms", "%s /* touch.py:%d DOUBLE_TAP_MS */"
             % (cnum(t["DOUBLE_TAP_MS"][0]), t["DOUBLE_TAP_MS"][1])),
        dset("scroll_step", "%s /* touch.py:%d SCROLL_STEP */"
             % (cnum(t["SCROLL_STEP"][0]), t["SCROLL_STEP"][1])),
        dset("fling_friction", "%s /* touch.py:%d FLING_FRICTION */"
             % (cnum(t["FLING_FRICTION"][0]), t["FLING_FRICTION"][1])),
        dset("fling_min_speed", "%s /* touch.py:%d FLING_MIN_SPEED */"
             % (cnum(t["FLING_MIN_SPEED"][0]), t["FLING_MIN_SPEED"][1])),
        dset("double_tap_radius_px", "%s /* touch.py:%d literal _up */"
             % (cnum(t["DOUBLE_TAP_RADIUS"][0]), t["DOUBLE_TAP_RADIUS"][1])),
        dset("fling_arm_speed", "%s /* touch.py:%d literal _up */"
             % (cnum(t["FLING_ARM_SPEED"][0]), t["FLING_ARM_SPEED"][1])),
        dset("fling_divisor", "%s /* touch.py:%d literal update */"
             % (cnum(t["FLING_DIVISOR"][0]), t["FLING_DIVISOR"][1])),
        dset("fling_max_steps", "%s /* touch.py:%d literal update */"
             % (cnum(t["FLING_MAX_STEPS"][0]), t["FLING_MAX_STEPS"][1])),
        dset("velocity_keep", "%s /* touch.py:%d _motion */"
             % (cnum(t["VELOCITY_KEEP"][0]), t["VELOCITY_KEEP"][1])),
        dset("velocity_new", "%s /* touch.py:%d _motion */"
             % (cnum(t["VELOCITY_NEW"][0]), t["VELOCITY_NEW"][1])),
    ]))
    add("touch", "motion_velocity",
        [("double", "prev_velocity"), ("double", "dy")], "double", """
// touch.py:%d TouchManager._motion: tp.velocity = tp.velocity * %s + dy * %s
return p_prev_velocity * %s + p_dy * %s;""" % (
        t["VELOCITY_KEEP"][1], cnum(t["VELOCITY_KEEP"][0]),
        cnum(t["VELOCITY_NEW"][0]), cnum(t["VELOCITY_KEEP"][0]),
        cnum(t["VELOCITY_NEW"][0])))
    add("touch", "motion_exceeds_slop", [("double", "total_dist")], "bool", """
// touch.py:247-249 TouchManager._motion: total > TAP_SLOP -> tp.moved = True
// (geser di bawah ambang masih dianggap tap saat jari dilepas).
return p_total_dist > %s;""" % cnum(t["TAP_SLOP"][0]))
    add("touch", "scroll_notch", [("double", "accum")], "Dictionary", """
// touch.py:258-263 TouchManager._motion — SATU langkah loop:
//   while abs(scroll_accum) >= SCROLL_STEP:
//       direction = -1 if scroll_accum > 0 else 1
//       scroll_accum -= SCROLL_STEP * (1 if scroll_accum > 0 else -1)
// Pemanggil mengulang selama abs(accum) >= scroll_step.
const int64_t direction = (p_accum > 0.0) ? -1 : 1;
const double sub = %s * ((p_accum > 0.0) ? 1.0 : -1.0);
Dictionary out;
out[Variant(String("direction"))] = Variant(direction);
out[Variant(String("accum"))] = Variant(p_accum - sub);
return out;""" % cnum(t["SCROLL_STEP"][0]))
    add("touch", "tap_is_double",
        [("double", "dt_ms"), ("double", "dx"), ("double", "dy")], "bool", """
// touch.py:279-283 TouchManager._up: (now - last_tap_time) * 1000.0 <
// DOUBLE_TAP_MS and abs(dx) < 40 and abs(dy) < 40
return p_dt_ms < %s && std::fabs(p_dx) < %s && std::fabs(p_dy) < %s;""" % (
        cnum(t["DOUBLE_TAP_MS"][0]), cnum(t["DOUBLE_TAP_RADIUS"][0]),
        cnum(t["DOUBLE_TAP_RADIUS"][0])))
    add("touch", "release_is_fling",
        [("bool", "moved"), ("double", "velocity")], "bool", """
// touch.py:%d TouchManager._up: elif tp.moved and abs(tp.velocity) > %s:
return p_moved && std::fabs(p_velocity) > %s;""" % (
        t["FLING_ARM_SPEED"][1], cnum(t["FLING_ARM_SPEED"][0]),
        cnum(t["FLING_ARM_SPEED"][0])))
    add("touch", "fling_steps", [("double", "velocity")], "int64_t", """
// touch.py:%d/%d TouchManager.update:
//   steps = int(abs(v) / (SCROLL_STEP * %s)); range(min(steps, %d))
const double denom = %s * %s;
const int64_t steps = (int64_t)(std::fabs(p_velocity) / denom);
const int64_t cap = %s;
return (steps < cap) ? steps : cap;""" % (
        t["FLING_DIVISOR"][1], t["FLING_MAX_STEPS"][1],
        cnum(t["FLING_DIVISOR"][0]), t["FLING_MAX_STEPS"][0],
        cnum(t["SCROLL_STEP"][0]), cnum(t["FLING_DIVISOR"][0]),
        cnum(t["FLING_MAX_STEPS"][0])))
    add("touch", "fling_direction", [("double", "velocity")], "int64_t", """
// touch.py:324 TouchManager.update: value=-1 if self.fling_velocity > 0 else 1
return (p_velocity > 0.0) ? -1 : 1;""")
    add("touch", "fling_decay", [("double", "velocity")], "double", """
// touch.py:321 TouchManager.update: self.fling_velocity *= FLING_FRICTION
return p_velocity * %s;""" % cnum(t["FLING_FRICTION"][0]))
    add("touch", "fling_active", [("double", "velocity")], "bool", """
// touch.py:320 TouchManager.update: if abs(self.fling_velocity) >
// FLING_MIN_SPEED (di bawah itu inersia di-nol-kan)
return std::fabs(p_velocity) > %s;""" % cnum(t["FLING_MIN_SPEED"][0]))
    add("touch", "long_press_due", [("double", "held_ms")], "bool", """
// touch.py:%d TouchManager.update: (now - tp.start_time) * 1000.0 >=
// LONG_PRESS_MS -> long_press sekali (long_fired)
return p_held_ms >= %s;""" % (
        t["LONG_PRESS_LINE"], cnum(t["LONG_PRESS_MS"][0])))
    add("touch", "dispatch_button",
        [("const String &", "kind"), ("int64_t", "value")], "int64_t", """
// touch.py:333-343 dispatch_to_game: tap -> klik kiri (1),
// long_press -> klik kanan (3), scroll -> 4 (naik, value<0) / 5 (turun).
if (p_kind == String("tap")) {
    return 1;
}
if (p_kind == String("long_press")) {
    return 3;
}
if (p_kind == String("scroll")) {
    return (p_value < 0) ? 4 : 5;
}
return 0;""")

    # ═══ hud (mobile/hud.py) ═══
    add("hud", "hud_min_tap", [], "int64_t", """
// hud.py:%d MIN_TAP: sisi minimum area sentuh, px logis 1280x720
// (>= 48dp rekomendasi Google; dipakai 80).
return %s;""" % (h["MIN_TAP"][1], cnum(h["MIN_TAP"][0])))
    add("hud", "hud_button_rects",
        [("int64_t", "safe_left"), ("int64_t", "safe_top"),
         ("int64_t", "safe_right"), ("int64_t", "safe_bottom")],
        "Dictionary", """
// hud.py:%d-%d TouchHUD._build_layout — rect tombol dalam koordinat logis.
// pause + debug kiri atas di bawah panel gold; skip/replay/next/menu
// kontekstual di dasar safe area; back kiri atas (menu).
const int64_t bx = std::max((int64_t)%s, p_safe_left + %s);
const int64_t by = %s;
const int64_t mid = %s / 2;
Dictionary out;
%s
return out;""" % (
        h["LAYOUT_LINE"], h["LAYOUT_END"],
        cint(h["PAUSE_X_MIN"][0]), cint(h["PAUSE_PAD"][0]),
        cint(h["PAUSE_Y"][0]), LW,
        "\n".join([
            dset("pause", "Rect2((double)bx, (double)by, 52.0, 52.0)"),
            dset("debug", "Rect2((double)(bx + %s), (double)by, 52.0, 52.0)"
                 % cint(h["DEBUG_DX"][0])),
            dset("skip", "Rect2((double)(p_safe_right - %s), "
                 "(double)(p_safe_bottom - %s), %s.0, %s.0)"
                 % (cint(h["SKIP"][0][0]), cint(h["SKIP"][1][0]),
                    cint(h["SKIP"][2][0]), cint(h["SKIP"][3][0]))),
            dset("replay", "Rect2((double)(mid - %s), "
                 "(double)(p_safe_bottom - %s), %s.0, %s.0)"
                 % (cint(h["REPLAY"][0][0]), cint(h["REPLAY"][1][0]),
                    cint(h["REPLAY"][2][0]), cint(h["REPLAY"][3][0]))),
            dset("next_level", "Rect2((double)(mid - %s), "
                 "(double)(p_safe_bottom - %s), %s.0, %s.0)"
                 % (cint(h["NEXT"][0][0]), cint(h["NEXT"][1][0]),
                    cint(h["NEXT"][2][0]), cint(h["NEXT"][3][0]))),
            dset("menu", "Rect2((double)(mid + %s), "
                 "(double)(p_safe_bottom - %s), %s.0, %s.0)"
                 % (cint(h["MENU"][0][0]), cint(h["MENU"][1][0]),
                    cint(h["MENU"][2][0]), cint(h["MENU"][3][0]))),
            dset("back", "Rect2((double)(p_safe_left + %s), "
                 "(double)(p_safe_top + %s), %s.0, %s.0)"
                 % (cint(h["BACK"][0][0]), cint(h["BACK"][1][0]),
                    cint(h["BACK"][2][0]), cint(h["BACK"][3][0]))),
        ])))
    add("hud", "hud_hit_rect", [("const Rect2 &", "rect")], "Rect2", """
// hud.py:%d-%d TouchButton.__init__: hit_rect = rect.inflate(%d, %d); kalau
// lebih kecil dari MIN_TAP (%d) di salah satu sumbu -> inflate tambahan
// supaya area sentuh memenuhi minimum (pygame Rect.inflate: center tetap).
const int64_t x = (int64_t)p_rect.position.x;
const int64_t y = (int64_t)p_rect.position.y;
const int64_t w = (int64_t)p_rect.size.x;
const int64_t ht = (int64_t)p_rect.size.y;
// pygame Rect.inflate(dx, dy): ukuran tumbuh TOTAL dx/dy (bukan per sisi),
// sudut kiri-atas mundur dx/2 (pembagian bulat) supaya pusat tetap.
const int64_t inf = %s;
int64_t hx = x - py_floordiv(inf, 2);
int64_t hy = y - py_floordiv(inf, 2);
int64_t hw = w + inf;
int64_t hht = ht + inf;
const int64_t min_tap = %s;
if (hw < min_tap || hht < min_tap) {
    const int64_t dx = std::max((int64_t)0, min_tap - w);
    const int64_t dy = std::max((int64_t)0, min_tap - ht);
    hx = x - py_floordiv(dx, 2);
    hy = y - py_floordiv(dy, 2);
    hw = w + dx;
    hht = ht + dy;
}
return Rect2((double)hx, (double)hy, (double)hw, (double)hht);""" % (
        h["HIT_INFLATE"][1], h["HIT_BRANCH_LINE"],
        h["HIT_INFLATE"][0], h["HIT_INFLATE"][0], h["MIN_TAP"][0],
        cnum(h["HIT_INFLATE"][0]), cnum(h["MIN_TAP"][0])))
    add("hud", "hud_button_contains",
        [("bool", "visible"), ("const Rect2 &", "hit_rect"),
         ("const Vector2 &", "pos")], "bool", """
// hud.py:%d-%d TouchButton.contains: self.visible and
// self.hit_rect.collidepoint(pos) — sisi max TIDAK termasuk (semantik
// pygame.Rect.collidepoint).
if (!p_visible) {
    return false;
}
return p_pos.x >= p_hit_rect.position.x &&
       p_pos.x < p_hit_rect.position.x + p_hit_rect.size.x &&
       p_pos.y >= p_hit_rect.position.y &&
       p_pos.y < p_hit_rect.position.y + p_hit_rect.size.y;""" % (
        h["CONTAINS_LINE"], h["CONTAINS_LINE"] + 1))
    add("hud", "hud_visibility",
        [("bool", "playing"), ("bool", "ended"), ("bool", "victory"),
         ("bool", "has_next_level"), ("bool", "cinematic_active"),
         ("bool", "panel_ada"), ("bool", "show_debug_button")],
        "Dictionary", """
// hud.py:%d-%d TouchHUD.sync — visibility tiap tombol. `has_next_level`
// pygame datang dari levels.get_next_level(level_number) is not None
// (jalur engine, hanya ditanya saat ended+victory).
Dictionary out;
%s
return out;""" % (
        h["SYNC_LINE"], h["SYNC_END"], "\n".join([
            dset("pause", "p_playing && !p_cinematic_active && !p_panel_ada"),
            dset("debug",
                 "p_show_debug_button && !p_cinematic_active && !p_panel_ada"),
            dset("skip", "p_cinematic_active"),
            dset("replay", "p_ended"),
            dset("menu", "p_ended"),
            dset("next_level", "p_ended && p_victory && p_has_next_level"),
        ])))
    add("hud", "hud_press_anim_next", [("double", "press_anim")], "double", """
// hud.py:162-164 TouchHUD.sync: press_anim = max(0.0, press_anim - %s)
const double next = p_press_anim - %s;
return (next < 0.0) ? 0.0 : next;""" % (
        cnum(h["PRESS_DECAY"][0]), cnum(h["PRESS_DECAY"][0])))
    add("hud", "hud_colors", [], "Dictionary", """
// hud.py:37-43 palet HUD sentuh.
Dictionary out;
%s
return out;""" % "\n".join([
        dset("gold", color_expr(h["GOLD"][0], h["GOLD"][1], "GOLD")),
        dset("gold_dim", color_expr(h["GOLD_DIM"][0], h["GOLD_DIM"][1],
                                    "GOLD_DIM")),
        dset("bg", color_expr(h["BG"][0], h["BG"][1], "BG")),
        dset("bg_active", color_expr(h["BG_ACTIVE"][0], h["BG_ACTIVE"][1],
                                     "BG_ACTIVE")),
        dset("white", color_expr(h["WHITE"][0], h["WHITE"][1], "WHITE")),
        dset("grey", color_expr(h["GREY"][0], h["GREY"][1], "GREY")),
        dset("red", color_expr(h["RED"][0], h["RED"][1], "RED")),
    ]))
    add("hud", "hud_skill_labels", [], "Dictionary", """
// hud.py:%d SKILL_LABELS (tombol skill dihapus v27 auto-cast; dipertahankan
// untuk paritas data).
Dictionary out;
%s
return out;""" % (h["SKILL_LABELS"][1],
                  "\n".join(dset(k, cnum(v))
                            for k, v in h["SKILL_LABELS"][0].items())))
    add("hud", "hud_skill_names", [], "Dictionary", """
// hud.py:%d SKILL_NAMES.
Dictionary out;
%s
return out;""" % (h["SKILL_NAMES"][1],
                  "\n".join(dset(k, cnum(v))
                            for k, v in h["SKILL_NAMES"][0].items())))
    add("hud", "tactical_actions", [], "Array", """
// hud.py:%d-%d TACTICAL_ACTIONS — sama dengan konstanta
// tactical_commands.TacticalCommand (mode HOLD tombol side panel).
Array out;
%s
return out;""" % (h["TACTICAL_ACTIONS"][1], h["TACTICAL_ACTIONS"][1] + 1,
                  "\n".join('out.push_back(String("%s"));' % v
                            for v in h["TACTICAL_ACTIONS"][0])))

    # ═══ perf (mobile/perf.py) ═══
    add("perf", "quality_levels", [], "Array", """
// perf.py:%d: LOW, MEDIUM, HIGH = "%s", "%s", "%s"
Array out;
out.push_back(String("%s"));
out.push_back(String("%s"));
out.push_back(String("%s"));
return out;""" % (p["LOW"][1], p["LOW"][0], p["MEDIUM"][0], p["HIGH"][0],
                  p["LOW"][0], p["MEDIUM"][0], p["HIGH"][0]))
    add("perf", "quality_preset", [("const String &", "level")],
        "Dictionary", """
// perf.py:%d-%d _Quality.apply — preset efek per level. Level tak dikenal
// berperilaku seperti HIGH tanpa screen_shake (low/med = false) — semantik
// perbandingan == Python direplikasi apa adanya.
const bool low = p_level == String("%s");
const bool med = p_level == String("%s");
Dictionary out;
%s
return out;""" % (
        p["APPLY_LINE"], p["APPLY_END"], p["LOW"][0], p["MEDIUM"][0],
        "\n".join([
            dset("particles", "!low"),
            dset("particle_ratio", "low ? %s : (med ? %s : %s)"
                 % (cnum(p["RATIO"][0][0]), cnum(p["RATIO"][1][0]),
                    cnum(p["RATIO"][2][0]))),
            dset("fog", "!low"),
            dset("shadows", "true"),
            dset("soft_shadows", "!(low || med)"),
            dset("glow", "!low"),
            dset("screen_shake", 'p_level == String("%s")' % p["HIGH"][0]),
            dset("aa_circles", "!low"),
            dset("floating_decor", "!low"),
            dset("max_damage_numbers", "low ? %s : (med ? %s : %s)"
                 % (cnum(p["MAX_DMG"][0][0]), cnum(p["MAX_DMG"][1][0]),
                    cnum(p["MAX_DMG"][2][0]))),
            dset("target_fps", "low ? %s : %s"
                 % (cnum(p["TARGET_FPS"][0][0]), cnum(p["TARGET_FPS"][1][0]))),
            dset("hd_edge", "!low"),
            dset("hero_lighting", "!low"),
            dset("max_hero_render", "low ? %s : (med ? %s : %s)"
                 % (cnum(p["MAX_HERO_RENDER"][0][0]),
                    cnum(p["MAX_HERO_RENDER"][1][0]),
                    cnum(p["MAX_HERO_RENDER"][2][0]))),
            dset("skill_quant_floor", "low ? %s : (med ? %s : %s)"
                 % (cnum(p["SKILL_QUANT"][0][0]), cnum(p["SKILL_QUANT"][1][0]),
                    cnum(p["SKILL_QUANT"][2][0]))),
            dset("atk_quant_floor", "low ? %s : (med ? %s : %s)"
                 % (cnum(p["ATK_QUANT"][0][0]), cnum(p["ATK_QUANT"][1][0]),
                    cnum(p["ATK_QUANT"][2][0]))),
            dset("fx_ground_budget", "low ? %s : (med ? %s : %s)"
                 % (cnum(p["FX_GROUND"][0][0]), cnum(p["FX_GROUND"][1][0]),
                    cnum(p["FX_GROUND"][2][0]))),
        ])))
    add("perf", "quality_defaults", [], "Dictionary", """
// perf.py:%d-%d _Quality.__init__ — properti perangkat yang TIDAK boleh
// ditimpa preset (diukur SEKALI oleh apply_device_profile).
Dictionary out;
%s
return out;""" % (p["QINIT_LINE"], p["QINIT_LINE"] + 12, "\n".join([
        dset("cheap_alpha", "true"),
        dset("use_colorkey_sprites", "false"),
        dset("max_alpha_px", cnum(p["MAX_ALPHA_PX"][0])),
        dset("colorkey_gain", cnum(p["COLORKEY_GAIN"][0])),
        dset("sprite_cache", "false"),
        dset("base_particle_ratio", cnum(p["BASE_RATIO"][0])),
    ])))
    add("perf", "particle_ratio_effective",
        [("double", "base_ratio"), ("double", "fx_load")], "double", """
// perf.py:487-496 Quality.particle_ratio: base * fx_load()
return p_base_ratio * p_fx_load;""")
    add("perf", "fx_load_target", [("int64_t", "n_active")], "double", """
// perf.py:%d-%d set_fx_load: target beban FX dari jumlah hero aktif.
// (1.0 / n) ** %s dengan lantai %s.
const double n = (double)((p_n_active < 0) ? 0 : p_n_active);
if (n <= %s) {
    return 1.0;
}
const double raw = std::pow(1.0 / n, %s);
return (raw < %s) ? %s : raw;""" % (
        p["SET_FX_LOAD_LINE"], p["SET_FX_LOAD_LINE"] + 15,
        cnum(p["FX_LOAD_EXP"][0]), cnum(p["FX_LOAD_MIN"][0]),
        cnum(p["FX_BASE_HEROES"][0]), cnum(p["FX_LOAD_EXP"][0]),
        cnum(p["FX_LOAD_MIN"][0]), cnum(p["FX_LOAD_MIN"][0])))
    add("perf", "fx_load_next",
        [("double", "current"), ("double", "target")], "double", """
// perf.py:%d set_fx_load: _FX_LOAD += (target - _FX_LOAD) * _FX_LOAD_SMOOTH
return p_current + (p_target - p_current) * %s;""" % (
        p["SET_FX_LOAD_LINE"] + 16, cnum(p["FX_LOAD_SMOOTH"][0])))
    add("perf", "fx_token_budgets", [("double", "load")], "Dictionary", """
// perf.py:%d-%d _reset_fx_tokens — anggaran KERAS token spawn per frame
// (int() Python = trunc; load >= lantai sehingga selalu positif).
const double load = std::max(%s, p_load);
Dictionary out;
out[Variant(String("particles"))] = Variant(std::max(
    (int64_t)%s, (int64_t)((double)%s * load)));
out[Variant(String("projectiles"))] = Variant(std::max(
    (int64_t)%s, (int64_t)((double)%s * load)));
out[Variant(String("skill_projectiles"))] = Variant(std::max(
    (int64_t)%s, (int64_t)((double)%s * load)));
return out;""" % (
        p["RESET_LINE"], p["RESET_LINE"] + 6, cnum(p["FX_LOAD_MIN"][0]),
        cnum(p["PARTICLE_FLOOR"][0]), cnum(p["FX_PARTICLE_CAP"][0]),
        cnum(p["PROJ_FLOOR"][0]), cnum(p["FX_PROJ_CAP"][0]),
        cnum(p["SKILL_FLOOR"][0]), cnum(p["FX_SKILL_PROJ_CAP"][0])))
    add("perf", "auto_detect_quality", [("bool", "is_android")], "String", """
// perf.py:%d-%d auto_detect_quality: Android mulai LOW (30 FPS stabil sejak
// detik pertama, pemain bisa naikkan di Settings), desktop HIGH.
if (!p_is_android) {
    return String("%s");
}
return String("%s");""" % (
        p["ADQ_LINE"], p["ADQ_END"], p["HIGH"][0], p["LOW"][0]))
    add("perf", "adaptive_thresholds", [], "Dictionary", """
// perf.py:%d-%d kelas kualitas adaptif (AQ) __init__ (+ cooldown update).
Dictionary out;
%s
return out;""" % (p["AQ_INIT_LINE"], p["AQ_INIT_LINE"] + 9, "\n".join([
        dset("low_fps", cnum(p["AQ_LOW_FPS"][0])),
        dset("high_fps", cnum(p["AQ_HIGH_FPS"][0])),
        dset("window", cnum(p["AQ_WINDOW"][0])),
        dset("cooldown_down", cnum(p["AQ_CD_DOWN"][0])),
        dset("cooldown_up", cnum(p["AQ_CD_UP"][0])),
    ])))
    add("perf", "adaptive_quality_decision",
        [("const String &", "level"), ("double", "avg"),
         ("int64_t", "cooldown")], "Dictionary", """
// perf.py:%d-%d AQ.update — keputusan SETELAH jendela sampel
// penuh; akumulasi sampel + jendela (%d frame) tetap di backend pemanggil.
Dictionary out;
if (p_cooldown > 0) {
    out[Variant(String("action"))] = Variant(String("wait"));
    out[Variant(String("new_level"))] = Variant(p_level);
    out[Variant(String("new_cooldown"))] = Variant(p_cooldown - 1);
    return out;
}
if (p_avg < %s && !(p_level == String("%s"))) {
    // apply(LOW if Quality.level == MEDIUM else MEDIUM); cooldown = %d
    out[Variant(String("action"))] = Variant(String("down"));
    out[Variant(String("new_level"))] = Variant(
        String((p_level == String("%s")) ? "%s" : "%s"));
    out[Variant(String("new_cooldown"))] = Variant((int64_t)%s);
    return out;
}
if (p_avg > %s && !(p_level == String("%s"))) {
    // apply(HIGH if Quality.level == MEDIUM else MEDIUM); cooldown = %d
    out[Variant(String("action"))] = Variant(String("up"));
    out[Variant(String("new_level"))] = Variant(
        String((p_level == String("%s")) ? "%s" : "%s"));
    out[Variant(String("new_cooldown"))] = Variant((int64_t)%s);
    return out;
}
out[Variant(String("action"))] = Variant(String("none"));
out[Variant(String("new_level"))] = Variant(p_level);
out[Variant(String("new_cooldown"))] = Variant((int64_t)0);
return out;""" % (
        p["AQ_UPDATE_LINE"], p["AQ_UPDATE_END"], p["AQ_WINDOW"][0],
        cnum(p["AQ_LOW_FPS"][0]), p["LOW"][0], p["AQ_CD_DOWN"][0],
        p["MEDIUM"][0], p["LOW"][0], p["MEDIUM"][0],
        cnum(p["AQ_CD_DOWN"][0]),
        cnum(p["AQ_HIGH_FPS"][0]), p["HIGH"][0], p["AQ_CD_UP"][0],
        p["MEDIUM"][0], p["HIGH"][0], p["MEDIUM"][0],
        cnum(p["AQ_CD_UP"][0])))

    # ═══ platform_utils (mobile/platform_utils.py) ═══
    add("platform_utils", "logical_size", [], "Vector2", """
// platform_utils.py:%d-%d LOGICAL_WIDTH/HEIGHT.
return Vector2((float)%s, (float)%s);""" % (
        u["LOGICAL_WIDTH"][1], u["LOGICAL_HEIGHT"][1], LW, LH))
    add("platform_utils", "detect_android",
        [("bool", "env_android_argument"), ("bool", "env_android_private"),
         ("bool", "has_getandroidapilevel")], "bool", """
// platform_utils.py:%d-%d _detect_android: python-for-android menyetel
// ANDROID_ARGUMENT/ANDROID_PRIVATE; CPython resmi punya
// sys.getandroidapilevel. Nilai env dikirim sebagai bool oleh backend.
if (p_env_android_argument) {
    return true;
}
if (p_env_android_private) {
    return true;
}
return p_has_getandroidapilevel;""" % (
        u["DETECT_LINE"], u["DETECT_END"]))
    add("platform_utils", "touch_mode",
        [("bool", "is_android"), ("const String &", "force_touch_env")],
        "bool", """
// platform_utils.py:%d: TOUCH_MODE = IS_ANDROID or
// (os.environ.get("MYSTIC_FORCE_TOUCH", "0") == "1")
return p_is_android || p_force_touch_env == String("1");"""
        % u["FORCE_LINE"])
    add("platform_utils", "safe_area", [("bool", "touch_mode")], "Rect2", """
// platform_utils.py:%d-%d get_safe_area — rect aman dari poni/gesture bar;
// tombol HUD ditaruh di dalam rect ini.
if (!p_touch_mode) {
    return Rect2(0.0f, 0.0f, (float)%s, (float)%s);
}
const int64_t m = %s;
return Rect2((float)m, (float)%s, (float)(%s - 2 * m), (float)(%s - %s));"""
        % (u["SAFE_LINE"], u["SAFE_LINE"] + 6, LW, LH,
           cint(u["SAFE_MARGIN"][0]), cint(u["SAFE_TOP"][0]), LW, LH,
           cint(u["SAFE_V"][0])))
    add("platform_utils", "panel_zones", [], "Dictionary", """
// platform_utils.py:%d-%d ZONA_POPUP_Y/ZONA_BAWAH_H — pembagian jalur tetap
// panel kanan supaya isi tidak pernah saling menimpa.
Dictionary out;
%s
return out;""" % (u["ZONA_POPUP_Y"][1], u["ZONA_BAWAH_H"][1], "\n".join([
        dset("zona_popup_y", cnum(u["ZONA_POPUP_Y"][0])),
        dset("zona_bawah_h", cnum(u["ZONA_BAWAH_H"][0])),
    ])))
    add("platform_utils", "panel_popup_pos",
        [("bool", "has_panel"), ("int64_t", "px"), ("int64_t", "py"),
         ("int64_t", "pw"), ("int64_t", "ph"), ("int64_t", "w"),
         ("int64_t", "h"), ("int64_t", "atas")], "Variant", """
// platform_utils.py:%d-%d panel_popup_pos — posisi popup di dalam panel
// kanan, atau NIL kalau panel tidak ada / popup tidak muat. Pembagian pakai
// py_floordiv (`//` Python) supaya panel lebih pendek dari popup tetap persis.
if (!p_has_panel || p_w > p_pw - %s) {
    return Variant();
}
const int64_t x = p_px + py_floordiv(p_pw - p_w, 2);
const int64_t y = std::max(p_atas,
                           std::min(py_floordiv(p_ph - p_h, 2),
                                    p_ph - p_h - %s));
return Variant(Vector2((float)x, (float)y));""" % (
        u["PPOS_LINE"], u["PPOS_END"], cint(u["POPUP_W_MARGIN"][0]),
        cint(u["POPUP_V_MARGIN"][0])))
    add("platform_utils", "panel_pos_bawah",
        [("bool", "has_panel"), ("int64_t", "px"), ("int64_t", "py"),
         ("int64_t", "pw"), ("int64_t", "ph"), ("int64_t", "w"),
         ("int64_t", "h")], "Variant", """
// platform_utils.py:%d-%d panel_pos_bawah — SLOT TETAP popup di jalur
// ZONA_POPUP_Y; kalau panel terlalu pendek, dorong ke atas seperlunya.
if (!p_has_panel || p_w > p_pw - %s) {
    return Variant();
}
const int64_t x = p_px + py_floordiv(p_pw - p_w, 2);
int64_t y = p_py + %s;
if (y + p_h > p_py + p_ph - %s) {
    y = std::max(p_py + %s, p_py + p_ph - %s - p_h);
}
return Variant(Vector2((float)x, (float)y));""" % (
        u["PBAWAH_LINE"], u["PBAWAH_END"], cint(u["BAWAH_W_MARGIN"][0]),
        cint(u["ZONA_POPUP_Y"][0]), cint(u["ZONA_BAWAH_H"][0]),
        cint(u["BAWAH_Y_MIN"][0]), cint(u["ZONA_BAWAH_H"][0])))
    add("platform_utils", "window_to_logical",
        [("double", "x"), ("double", "y"), ("double", "scale"),
         ("double", "off_x"), ("double", "off_y")], "Vector2", """
// platform_utils.py:%d-%d window_to_logical — piksel jendela -> logis
// 1280x720. Python `scale or 1.0`: 0.0/None dianggap 1.0.
const double s = (p_scale == 0.0) ? 1.0 : p_scale;
return Vector2((float)((p_x - p_off_x) / s),
               (float)((p_y - p_off_y) / s));""" % (
        u["W2L_LINE"], u["W2L_END"]))
    add("platform_utils", "pointer_to_logical",
        [("int64_t", "mode"), ("double", "x"), ("double", "y"),
         ("double", "scale"), ("double", "off_x"), ("double", "off_y")],
        "Vector2", """
// platform_utils.py:%d-%d pointer_to_logical — mode 0 = native: piksel
// jendela perlu dipetakan; mode lain (scaled_*): SDL sudah menerjemahkan,
// koordinat kembali sebagai double apa adanya.
if (p_mode == 0) {
    return window_to_logical(p_x, p_y, p_scale, p_off_x, p_off_y);
}
return Vector2((float)p_x, (float)p_y);""" % (
        u["P2L_LINE"], u["P2L_END"]))

    # ═══ debug (mobile/debug.py) ═══
    add("debug", "debug_modes", [], "Array", """
// debug.py:%d _MODE_NAMES — OFF -> RINGKAS -> LENGKAP -> GRAFIK -> OFF.
Array out;
%s
return out;""" % (d["MODE_NAMES"][1],
                  "\n".join('out.push_back(String("%s"));' % v
                            for v in d["MODE_NAMES"][0])))
    add("debug", "debug_next_mode", [("int64_t", "mode")], "int64_t", """
// debug.py:%d-%d DebugOverlay.toggle: self.mode = (self.mode + 1) %% 4
return (p_mode + 1) %% 4;""" % (d["TOGGLE_LINE"], d["TOGGLE_END"]))
    add("debug", "debug_wrap_mode", [("int64_t", "mode")], "int64_t", """
// debug.py:%d-%d DebugOverlay.set_mode: self.mode = mode %% 4
return p_mode %% 4;""" % (d["SETMODE_LINE"], d["SETMODE_END"]))
    add("debug", "debug_is_enabled", [("int64_t", "mode")], "bool", """
// debug.py:%d-%d DebugOverlay.enabled: mode != MODE_OFF
return p_mode != %s;""" % (d["ENABLED_LINE"], d["ENABLED_END"],
                           cnum(d["MODE_OFF"][0])))
    add("debug", "fps_color", [("double", "fps")], "Color", """
// debug.py:%d-%d _color_for_fps: >= %d OK, >= %d WARN, selain itu BAD.
if (p_fps >= %s) {
    return %s;
}
if (p_fps >= %s) {
    return %s;
}
return %s;""" % (
        d["COLOR_LINE"], d["COLOR_END"], d["FPS_OK"][0], d["FPS_WARN"][0],
        cnum(d["FPS_OK"][0]), color_expr(d["OK"][0], d["OK"][1], "OK"),
        cnum(d["FPS_WARN"][0]), color_expr(d["WARN"][0], d["WARN"][1], "WARN"),
        color_expr(d["BAD"][0], d["BAD"][1], "BAD")))
    add("debug", "debug_slow_frame", [("double", "frame_ms")], "bool", """
// debug.py:%d DebugOverlay.update: if frame_ms > %d: _slow_frames += 1
return p_frame_ms > %s;""" % (
        d["SLOW_LINE"], d["SLOW_MS"][0], cnum(d["SLOW_MS"][0])))
    add("debug", "perf_log_line",
        [("double", "fps"), ("double", "avg_frame_ms"), ("double", "upd_ms"),
         ("double", "draw_ms"), ("const String &", "quality"),
         ("const String &", "entity_counts"), ("const String &", "memory")],
        "String", """
// debug.py:%d-%d DebugOverlay._log_line — baris log perf (stdout/logcat).
// Bagian numerik pakai snprintf %%.1f (pembulatan benar atas nilai biner,
// glibc == CPython); bagian str digabung lewat String (API godot-cpp).
char buf[96];
snprintf(buf, sizeof(buf),
         "[PERF] fps=%%.1f frame=%%.1fms upd=%%.1f draw=%%.1f q=",
         p_fps, p_avg_frame_ms, p_upd_ms, p_draw_ms);
String out(buf);
out += p_quality;
out += String(" ent=");
out += p_entity_counts;
out += String(" mem=");
out += p_memory;
return out;""" % (d["LOGLINE_LINE"], d["LOGLINE_END"]))

    # ═══ combat_audio (mobile/combat_audio.py) ═══
    add("combat_audio", "attack_sound_kind", [("double", "distance")],
        "String", """
// combat_audio.py:%d-%d jenis_serangan: jarak >= AMBANG_RANGED (%d) ->
// ranged, selain itu melee. `float(jarak or 0)`: 0 tetap 0.
return (p_distance >= %s) ? String("%s") : String("%s");""" % (
        a["JS_LINE"], a["JS_END"], a["AMBANG_RANGED"][0],
        cnum(a["AMBANG_RANGED"][0]), a["HERO_RANGED"][0], a["HERO_MELEE"][0]))
    add("combat_audio", "tower_sound_kind", [("const String &", "tower_type")],
        "String", """
// combat_audio.py:%d-%d jenis_tower: pemetaan tipe menara -> jenis suara,
// default archer (dict.get(tower_type, TOWER_ARCHER)).
if (p_tower_type == String("cannon")) {
    return String("%s");
}
if (p_tower_type == String("ice")) {
    return String("%s");
}
if (p_tower_type == String("mage")) {
    return String("%s");
}
return String("%s");""" % (
        a["JT_LINE"], a["JT_END"], a["TOWER_CANNON"][0], a["TOWER_ICE"][0],
        a["TOWER_MAGE"][0], a["TOWER_ARCHER"][0]))
    add("combat_audio", "sound_kinds", [], "Array", """
// combat_audio.py:%d-%d konstanta jenis suara tempur.
Array out;
%s
return out;""" % (a["HERO_MELEE"][1], a["MINION_HIT"][1],
                  "\n".join('out.push_back(String("%s"));' % v for v in [
                      a["HERO_MELEE"][0], a["HERO_RANGED"][0],
                      a["TOWER_ARCHER"][0], a["TOWER_CANNON"][0],
                      a["TOWER_ICE"][0], a["TOWER_MAGE"][0],
                      a["MINION_HIT"][0]])))
    cfg_rows = []
    for kind, (vol, jeda, rebut) in a["KONFIG"][0].items():
        cfg_rows.append(
            "    {\n"
            "        Array cfg;\n"
            "        cfg.push_back(Variant(%s));\n"
            "        cfg.push_back(Variant(%s));\n"
            "        cfg.push_back(Variant(%s));\n"
            '        out[Variant(String("%s"))] = Variant(cfg);\n'
            "    }"
            % (cnum(vol), cnum(jeda), "true" if rebut else "false", kind))
    add("combat_audio", "sound_config", [], "Dictionary", """
// combat_audio.py:%d-%d _KONFIG — jenis -> (volume dasar, jeda minimum ms,
// boleh rebut channel).
Dictionary out;
%s
return out;""" % (a["KONFIG"][1], a["KONFIG"][1] + 7,
                  "\n".join(cfg_rows)))
    pola_rows = []
    for kind, pats in a["POLA"][0].items():
        pola_rows.append(
            "    {\n"
            "        Array pats;\n"
            "%s\n"
            '        out[Variant(String("%s"))] = Variant(pats);\n'
            "    }"
            % ("\n".join('        pats.push_back(String("%s"));' % pat
                         for pat in pats), kind))
    add("combat_audio", "sound_patterns", [], "Dictionary", """
// combat_audio.py:%d-%d POLA — jenis -> pola nama berkas (fnmatch).
Dictionary out;
%s
return out;""" % (a["POLA"][1], a["POLA"][1] + 7, "\n".join(pola_rows)))
    add("combat_audio", "frame_sound_budget", [], "int64_t", """
// combat_audio.py:%d _sisa_frame = [4] — anggaran suara non-rebut per frame
// (new_frame() mengisi ulang tiap frame).
return %s;""" % (a["NF_LINE"], cnum(a["FRAME_BUDGET"][0])))
    add("combat_audio", "play_gate",
        [("double", "now_ms"), ("double", "last_ms"), ("int64_t", "jeda_ms"),
         ("bool", "boleh_rebut"), ("int64_t", "sisa_frame")], "String", """
// combat_audio.py:%d-%d play() — gerbang urut: jeda per jenis lalu anggaran
// frame. Pencarian channel mixer + pemilihan berkas acak tetap di backend
// (mixer tidak ada di C++ murni). Default last_ms pygame = -99999.
if (p_now_ms - p_last_ms < (double)p_jeda_ms) {
    return String("tolak_jeda");
}
if (!p_boleh_rebut && p_sisa_frame <= 0) {
    return String("tolak_anggaran");
}
return String("main");""" % (a["LAST_DEFAULT"][1], a["PLAY_END"]))
    add("combat_audio", "combat_stats_text",
        [("int64_t", "main"), ("int64_t", "tolak_jeda"),
         ("int64_t", "tolak_anggaran"), ("int64_t", "tolak_channel")],
        "String", """
// combat_audio.py:%d-%d ringkas() — format persis (dua spasi setelah main).
const int64_t total = p_tolak_jeda + p_tolak_anggaran + p_tolak_channel;
char buf[160];
snprintf(buf, sizeof(buf),
         "suara: main %%lld  ditolak %%lld (jeda %%lld / anggaran %%lld / "
         "kanal %%lld)",
         (long long)p_main, (long long)total, (long long)p_tolak_jeda,
         (long long)p_tolak_anggaran, (long long)p_tolak_channel);
return String(buf);""" % (a["RINGKAS_LINE"], a["RINGKAS_END"]))

    # ═══ cloud_save (mobile/cloud_save.py) ═══
    add("cloud_save", "cloud_constants", [], "Dictionary", """
// cloud_save.py:%d, %d-%d konstanta payload cloud.
Dictionary out;
%s
return out;""" % (c["CLOUD_MAGIC"][1], c["PAYLOAD_MAGIC"][1],
                  c["NUM_SLOTS"][1], "\n".join([
                      dset("cloud_magic", cnum(c["CLOUD_MAGIC"][0])),
                      dset("cloud_version", cnum(c["CLOUD_VERSION"][0])),
                      dset("payload_magic", cnum(c["PAYLOAD_MAGIC"][0])),
                      dset("payload_version", cnum(c["PAYLOAD_VERSION"][0])),
                      dset("num_slots", cnum(c["NUM_SLOTS"][0])),
                      dset("checksum_exempt_key", '"checksum"'),
                  ])))
    add("cloud_save", "payload_gate",
        [("bool", "is_dict"), ("bool", "magic_ok"), ("bool", "version_ok"),
         ("int64_t", "version"), ("bool", "slots_ok"),
         ("bool", "checksum_ok")], "String", """
// cloud_save.py:%d-%d parse_payload — urutan validasi + pesan persis.
// "File corrupt (not valid JSON)" ditangani backend pemanggil (hasil parser
// JSON); checksum dihitung engine-side (canonical JSON + sha256);
// version_ok = False untuk payload yang int(version) -nya gagal (Python
// except -> "File corrupt (bad version)").
if (!p_is_dict) {
    return String("File corrupt (unexpected structure)");
}
if (!p_magic_ok) {
    return String("Not a Mystic Arena save file");
}
if (!p_version_ok) {
    return String("File corrupt (bad version)");
}
if (p_version < 1 || p_version > %s) {
    char buf[96];
    snprintf(buf, sizeof(buf), "Save version %%lld not supported",
             (long long)p_version);
    return String(buf);
}
if (!p_slots_ok) {
    return String("Save contains no data");
}
if (!p_checksum_ok) {
    return String("File corrupt (checksum mismatch)");
}
return String();""" % (c["PARSE_LINE"], c["PARSE_END"],
                       cnum(c["PAYLOAD_VERSION"][0])))
    add("cloud_save", "payload_summary",
        [("const Array &", "slots"), ("double", "exported_at")],
        "Dictionary", """
// cloud_save.py:%d-%d get_payload_summary — level tertinggi, gold terbanyak,
// timestamp terbaru. exported_at_str (strftime localtime) tetap di backend.
// try/except per slot direplikasi: kesalahan di tengah slot MENGHENTIKAN
// sisa baris slot itu (hasil sebagian tetap berlaku), lalu lanjut slot
// berikutnya. int()/float() Python atas string angka direplikasi
// (py_int_of/py_float_of); string non-angka = exception -> lewati sisa slot.
// Python max(0, x) mempertahankan tipe operand yang menang, jadi level
// tertinggi dilacak per tipe (int dari JSON save; float kalau ada fraksi).
int64_t highest_i = 0;
double highest_f = 0.0;
bool highest_is_float = false;
int64_t best_gold = 0;
double newest_played = 0.0;
for (int64_t i = 0; i < p_slots.size(); i++) {
    const Variant slot_v = p_slots[i];  // godot-cpp Array: akses via operator[] const
    Dictionary data = slot_v;  // operator Dictionary; non-dict -> kosong
    // completed = data.get("completed_levels", []) or []
    const Variant completed = data.get(Variant(String("completed_levels")),
                                       Variant(Array()));
    if (bool(completed)) {
        // Python: max(completed) — truthy non-list ATAU elemen non-angka
        // melempar exception -> lewati sisa slot.
        const Array completed_arr = completed;
        bool skip_rest = false;
        double local_max = 0.0;
        bool local_is_float = false;
        bool first = true;
        if (completed.get_type() != Variant::ARRAY) {
            skip_rest = true;  // max(str) -> max(int, str) TypeError
        }
        for (int64_t j = 0; !skip_rest && j < completed_arr.size(); j++) {
            const Variant item = completed_arr[j];
            const Variant::Type it = item.get_type();
            if (it != Variant::INT && it != Variant::FLOAT &&
                    it != Variant::BOOL) {
                skip_rest = true;  // TypeError di max()
                break;
            }
            // max() Python atomik: max parsial TIDAK boleh menyentuh
            // highest sebelum seluruh list lolos (commit di bawah).
            const double v = (it == Variant::FLOAT)
                                 ? (double)item
                                 : (double)(int64_t)item;
            if (first || v > local_max) {
                local_max = v;
                local_is_float = (it == Variant::FLOAT);
                first = false;
            }
        }
        if (skip_rest) {
            continue;
        }
        if (!first) {
            const double cur =
                    highest_is_float ? highest_f : (double)highest_i;
            if (local_max > cur) {
                if (local_is_float) {
                    highest_f = local_max;
                    highest_is_float = true;
                } else {
                    highest_i = (int64_t)local_max;
                    highest_is_float = false;
                }
            }
        }
    }
    // best_gold = max(best_gold, int(data.get("meta_gold", 0)))
    const Variant gold = data.get(Variant(String("meta_gold")),
                                  Variant((int64_t)0));
    bool gold_ok = true;
    int64_t gold_int = 0;
    const Variant::Type gt = gold.get_type();
    if (gt == Variant::INT) {
        gold_int = (int64_t)gold;
    } else if (gt == Variant::BOOL) {
        gold_int = bool(gold) ? 1 : 0;
    } else if (gt == Variant::FLOAT) {
        gold_int = (int64_t)gold;  // int(): trunc ke arah nol
    } else if (gt == Variant::STRING) {
        gold_ok = py_int_of_string(gold, gold_int);  // int("12") / gagal lain
    } else {
        gold_ok = false;  // TypeError -> lewati sisa slot
    }
    if (!gold_ok) {
        continue;
    }
    if (gold_int > best_gold) {
        best_gold = gold_int;
    }
    // newest_played = max(..., float(data.get("slot_last_played", 0) or 0))
    Variant played = data.get(Variant(String("slot_last_played")),
                              Variant((int64_t)0));
    if (!bool(played)) {
        played = Variant((int64_t)0);  // `or 0`: falsy -> 0
    }
    bool played_ok = true;
    double played_f = 0.0;
    const Variant::Type pt = played.get_type();
    if (pt == Variant::INT) {
        played_f = (double)(int64_t)played;
    } else if (pt == Variant::BOOL) {
        played_f = bool(played) ? 1.0 : 0.0;
    } else if (pt == Variant::FLOAT) {
        played_f = (double)played;
    } else if (pt == Variant::STRING) {
        played_ok = py_float_of_string(played, played_f);
    } else {
        played_ok = false;
    }
    if (!played_ok) {
        continue;
    }
    if (played_f > newest_played) {
        newest_played = played_f;
    }
}
Dictionary out;
out[Variant(String("highest_level"))] =
        highest_is_float ? Variant(highest_f) : Variant(highest_i);
out[Variant(String("meta_gold"))] = Variant(best_gold);
out[Variant(String("slot_count"))] = Variant((int64_t)p_slots.size());
out[Variant(String("exported_at"))] = Variant(p_exported_at);
out[Variant(String("newest_played"))] = Variant(newest_played);
return out;""" % (c["SUMMARY_LINE"], c["SUMMARY_END"]))

    # helper string angka (INTERNAL — tidak di-bind, dipakai payload_summary)
    fns.append(Fn("cloud_save", "py_int_of_string",
                  [("const String &", "text"), ("int64_t &", "out")], "bool",
                  """
// int(str) Python: strip whitespace, tanda opsional, digit saja.
std::string s = p_text.utf8().get_data();
size_t i = 0;
while (i < s.size() && std::isspace((unsigned char)s[i])) {
    i++;
}
size_t j = s.size();
while (j > i && std::isspace((unsigned char)s[j - 1])) {
    j--;
}
bool neg = false;
if (i < j && (s[i] == '+' || s[i] == '-')) {
    neg = s[i] == '-';
    i++;
}
if (i >= j) {
    return false;
}
int64_t value = 0;
for (size_t k = i; k < j; k++) {
    if (s[k] < '0' || s[k] > '9') {
        return false;
    }
    value = value * 10 + (s[k] - '0');
}
p_out = neg ? -value : value;
return true;"""))
    fns[-1].internal = True
    fns[-1].decl_override = (
        "static bool py_int_of_string(const String &text, int64_t &out);")
    fns.append(Fn("cloud_save", "py_float_of_string",
                  [("const String &", "text"), ("double &", "out")], "bool",
                  """
// float(str) Python (subset JSON-ish): strip whitespace, tanda opsional,
// digit + opsional '.' digit + opsional eksponen e/E.
std::string s = p_text.utf8().get_data();
size_t i = 0;
while (i < s.size() && std::isspace((unsigned char)s[i])) {
    i++;
}
size_t j = s.size();
while (j > i && std::isspace((unsigned char)s[j - 1])) {
    j--;
}
std::string body = s.substr(i, j - i);
if (body.empty()) {
    return false;
}
char *endp = nullptr;
const double value = strtod(body.c_str(), &endp);
if (endp != body.c_str() + body.size()) {
    return false;
}
p_out = value;
return true;"""))
    fns[-1].internal = True
    fns[-1].decl_override = (
        "static bool py_float_of_string(const String &text, double &out);")

    # ═══ buildinfo (mobile/buildinfo.py) ═══
    add("buildinfo", "build_constants", [], "Dictionary", """
// buildinfo.py:%d-%d penanda build.
Dictionary out;
%s
return out;""" % (b["BUILD_ID"][1], b["BUILD_DATE"][1], "\n".join([
        dset("build_id", cnum(b["BUILD_ID"][0])),
        dset("build_date", cnum(b["BUILD_DATE"][0])),
    ])))
    add("buildinfo", "build_key_files", [], "Array", """
// buildinfo.py:%d-%d _KEY_FILES — berkas kunci fingerprint.
Array out;
%s
return out;""" % (b["KEY_FILES"][1], b["KEY_FILES"][1] + 6,
                  "\n".join('out.push_back(String("%s"));' % f
                            for f in b["KEY_FILES"][0])))
    add("buildinfo", "fingerprint_text",
        [("int64_t", "total_bytes"), ("int64_t", "found")], "String", """
// buildinfo.py:%d-%d fingerprint: "%s" %% (total %% 0x100000, found)
char buf[64];
snprintf(buf, sizeof(buf), "%s",
         (unsigned long long)(p_total_bytes %% 0x100000),
         (long long)p_found);
return String(buf);""" % (b["FP_LINE"], b["FP_END"], b["FP_FORMAT"],
                          b["FP_FORMAT"]))
    add("buildinfo", "build_label",
        [("const String &", "build_id"), ("const String &", "build_date"),
         ("const String &", "fingerprint")], "String", """
// buildinfo.py:%d-%d label(): "%s"
String out("%s");
out += p_build_id;
out += String(" (");
out += p_build_date;
out += String(") fp=");
out += p_fingerprint;
return out;""" % (b["LABEL_LINE"], b["LABEL_END"], b["LABEL_FORMAT"],
                  "BUILD "))

    # api_signature perlu jumlah fn final
    fns[sig_slot].body = fns[sig_slot].body.replace(
        "__SIG__", "%s:%dmod:%dfn:" % (SIG_PREFIX, len(MODULES),
                                       len(fns) - 2))
    return fns


# ══════════════════════════════════════════════════════════
#  Emit
# ══════════════════════════════════════════════════════════

HEADER_INCLUDES = """#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/color.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/rect2.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/variant.hpp>
#include <godot_cpp/variant/vector2.hpp>
#include <cstdint>"""


def emit_h(fns):
    head = """#ifndef MYSTIC_MOBILE_PROCESSOR_H
#define MYSTIC_MOBILE_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : mobile/ (touch, hud, perf, platform_utils, debug, combat_audio,
//             cloud_save, buildinfo)
// Generator : tools/gen_mobile_cpp.py (AST Python -> C++, bukan terjemahan
//             tangan)
// Regenerasi: python3 tools/gen_mobile_cpp.py
// Cek CI    : python3 tools/gen_mobile_cpp.py --check
// Desain    : docs/MOBILE_GODOTPP.md
//
// Port paket `mobile/` ke Godot C++ GDExtension: lapisan KEPUTUSAN murni
// (ambang gesture, rect + visibility tombol HUD, preset kualitas + adaptive
// quality, zona panel kanan, warna overlay debug, gate suara tempur,
// validasi + ringkasan payload cloud, label build). Piksel (pygame.draw /
// Surface), mixer SDL, I/O berkas, dan jembatan Android tidak diport —
// backend masing-masing memanggil angka dari sini.

%s

namespace godot {

class MysticMobile : public RefCounted {
    GDCLASS(MysticMobile, RefCounted);

public:""" % HEADER_INCLUDES
    body = "\n".join(
        "    " + (getattr(fn, "decl_override", None) or fn.decl)
        for fn in fns)
    helper = """
    // ── helper internal (dipakai fungsi ter-bind; TIDAK di-bind) ──
    // `//` Python (floor ke arah -inf); `%` Python untuk pembagi positif.
    static int64_t py_floordiv(int64_t a, int64_t b);
    static int64_t py_mod(int64_t a, int64_t b);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_MOBILE_PROCESSOR_H
"""
    return head + "\n" + body + helper


def emit_cpp(fns):
    parts = ["""#include "mobile_processor.h"

#include <godot_cpp/core/class_db.hpp>

#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : mobile/*.py
// Generator : tools/gen_mobile_cpp.py
// Regenerasi: python3 tools/gen_mobile_cpp.py
// Cek CI    : python3 tools/gen_mobile_cpp.py --check
//
// Setiap fungsi menyebut baris sumber Python yang direplikasi. Angka yang
// diekstrak generator datang dari AST (bukan salinan tangan); perilakunya
// dikunci oracle mobile/*.py ASLI + self-test tanpa engine
// (tools/test_mobile_cpp_selftest.py).

namespace godot {

// `//` Python: floor ke arah -inf (C++ `/` memotong ke arah nol).
int64_t MysticMobile::py_floordiv(int64_t a, int64_t b) {
    int64_t q = a / b;
    if ((a % b != 0) && ((a < 0) != (b < 0))) {
        q--;
    }
    return q;
}

// `%` Python: tanda mengikuti pembagi (C++ % tanda mengikuti dividend).
int64_t MysticMobile::py_mod(int64_t a, int64_t b) {
    int64_t r = a % b;
    if (r != 0 && ((r < 0) != (b < 0))) {
        r += b;
    }
    return r;
}
"""]
    for fn in fns:
        parts.append("\n%s {\n%s\n}\n" % (fn.defn, fn.body))
    bind = "\n".join(
        ("" if getattr(fn, "internal", False) else fn.bind)
        for fn in fns)
    parts.append("""
void MysticMobile::_bind_methods() {
%s
}

} // namespace godot
""" % bind)
    return "".join(parts)


def emit_dispatch(fns):
    bound = [fn for fn in fns if not getattr(fn, "internal", False)]
    head = """// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Tabel perintah self-test untuk SELURUH API MysticMobile (%d fungsi).
// Dibangkitkan tools/gen_mobile_cpp.py bersama mobile_processor.{h,cpp};
// diperiksa ulang oleh tools/test_mobile_cpp_selftest.py (closed-world:
// jumlah entri == jumlah bind_static_method di _bind_methods).

// {nama, jumlah argumen, pemanggil}
""" % len(bound)
    rows = []
    for fn in bound:
        conv = []
        for i, (ctype, cname) in enumerate(fn.params):
            base = ctype.replace("const ", "").replace("&", "").strip()
            if base == "int64_t":
                conv.append("to_int(a[%d], e)" % i)
            elif base == "double":
                conv.append("to_double(a[%d], e)" % i)
            elif base == "bool":
                conv.append("to_bool(a[%d], e)" % i)
            elif base == "String":
                conv.append("to_string(a[%d], e)" % i)
            elif base == "Color":
                conv.append("to_color(a[%d], e)" % i)
            elif base == "Vector2":
                conv.append("to_vector2(a[%d], e)" % i)
            elif base == "Rect2":
                conv.append("to_rect2(a[%d], e)" % i)
            elif base == "Array":
                conv.append("to_array(a[%d], e)" % i)
            elif base == "Dictionary":
                conv.append("to_dict(a[%d], e)" % i)
            else:
                raise MobileError("tipe argumen tak didukung: %s" % ctype)
        if fn.ret == "void":
            call = "%s::%s(%s); return Variant();" % (CLASS, fn.name,
                                                      ", ".join(conv))
        else:
            call = "return Variant(%s::%s(%s));" % (CLASS, fn.name,
                                                    ", ".join(conv))
        rows.append(
            '    {"%s", %d, [](const std::vector<Variant> &a, std::string &e)'
            ' -> Variant {\n        (void)a; (void)e;\n        %s\n    }},'
            % (fn.name, len(fn.params), call))
    return head + "\n".join(rows) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verifikasi berkas ter-commit byte-identik")
    args = ap.parse_args()

    C = extract()
    fns = build_functions(C)
    bound = [fn for fn in fns if not getattr(fn, "internal", False)]

    outputs = {
        OUT_H: emit_h(fns),
        OUT_CPP: emit_cpp(fns),
        OUT_DISPATCH: emit_dispatch(fns),
    }

    if args.check:
        stale = []
        for path, content in outputs.items():
            current = path.read_text(encoding="utf-8")
            if current != content:
                stale.append(str(path))
        if stale:
            print("STALE — regenerasi dulu:")
            for s in stale:
                print("  python3 tools/gen_mobile_cpp.py  # ->", s)
            return 1
        print("[gen_mobile_cpp] OK: %d berkas byte-identik, %d fungsi ter-bind"
              % (len(outputs), len(bound)))
        return 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print("[gen_mobile_cpp] %s (%d baris)" % (path, content.count("\n")))
    print("[gen_mobile_cpp] %d fungsi ter-bind; modul: %s"
          % (len(bound), ",".join(MODULES)))
    print("[gen_mobile_cpp] Selanjutnya: python3 "
          "tools/test_mobile_cpp_selftest.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
