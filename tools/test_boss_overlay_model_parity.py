#!/usr/bin/env python3
"""test_boss_overlay_model_parity — KEMBARAN (twin) BossOverlay.gd di Python.

Sumber kebenaran lapisan overlay boss adalah pygame ASLI:
``tools/test_boss_draw_parity.py`` menjalankan ``Boss.draw`` sungguhan dan
menulis ``godot/tests/fixtures/boss_draw.json``. Replay resminya ada di
``godot/tests/BossDrawParityTest.tscn`` (Godot headless, dijalankan CI).

Berkas ini adalah JARING KEDUA untuk dipakai tanpa engine Godot: logika
``godot/scripts/render/BossOverlay.gd`` disalin apa adanya ke Python —
KONSTANTA DIBACA LANGSUNG dari berkas .gd (bukan diketik ulang) — lalu hasilnya
dibandingkan dengan fixture untuk semua skenario, op demi op (jenis, urutan,
geometri, warna, alpha, metrik teks).

Yang ditangkap: salah transkripsi rumus (floor division ``//``, pemotongan
``int()``, urutan lapisan, konstanta yang diedit tanpa memperbarui fixture,
pita alpha yang kembali jadi tumpukan cakram). Yang TIDAK ditangkap: perbedaan
antara twin ini dan GDScript aslinya — karena itu replay Godot di CI tetap
wajib, dan twin ini sengaja ditulis baris-per-baris mengikuti .gd.

Jalankan: python3 tools/test_boss_overlay_model_parity.py
Butuh:     fixture dari tools/test_boss_draw_parity.py (tanpa pygame/Godot).
"""
import ast
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERLAY_GD = os.path.join(ROOT, "godot", "scripts", "render", "BossOverlay.gd")
FIXTURE = os.path.join(ROOT, "godot", "tests", "fixtures", "boss_draw.json")

_pass = 0
_fail = 0
_shown = 0


def check(name, cond, detail=""):
    global _pass, _fail, _shown
    if cond:
        _pass += 1
    else:
        _fail += 1
        if _shown < 25:
            _shown += 1
            print("  FAIL %s%s" % (name, (" - " + detail) if detail else ""))


def section(title):
    print("\n== %s ==" % title)


# ═══════════════════════════════════════════════════════════════════
# Konstanta dibaca dari BossOverlay.gd
# ═══════════════════════════════════════════════════════════════════

def gd_consts(path):
    src = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^const (\w+)[^\n=]*=\s*", src, re.M):
        name = m.group(1)
        i = m.end()
        # Ambil literal seimbang (array/dict bisa multi-baris di GDScript).
        depth = 0
        j = i
        while j < len(src):
            ch = src[j]
            if ch in "[{(":
                depth += 1
            elif ch in "]})":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            elif ch == "\n" and depth == 0:
                break
            j += 1
        expr = src[i:j].strip()
        if not expr or expr.startswith("preload"):
            continue
        try:
            out[name] = ast.literal_eval(expr)
        except (ValueError, SyntaxError):
            continue
    return out


C = gd_consts(OVERLAY_GD)


def k(name):
    if name not in C:
        raise AssertionError("konstanta %s tidak terbaca dari BossOverlay.gd"
                             % name)
    return C[name]


# ═══════════════════════════════════════════════════════════════════
# Utilitas (cermin BossOverlay.gd)
# ═══════════════════════════════════════════════════════════════════

def idiv(a, b):
    """`a // b` Python == `idiv()` GDScript (floor, bukan trunc)."""
    return int(math.floor(float(a) / float(b)))


def a255(v):
    return max(0, min(255, int(v)))


def a200(v):
    return max(0, min(int(k("ENRAGE_ALPHA_MAX")), int(v)))


def with_alpha(c, alpha):
    return [int(c[0]), int(c[1]), int(c[2]), int(alpha)]


def lighten(c, add=None):
    add = int(k("GENERIC_HL_ADD")) if add is None else int(add)
    return [min(255, int(c[0]) + add), min(255, int(c[1]) + add),
            min(255, int(c[2]) + add), 255]


def is_true(state):
    return str(state.get("boss_class", "mini")) == "true"


def col_arr(state, key, fallback):
    v = state.get(key)
    if isinstance(v, (list, tuple)) and len(v) >= 3:
        return [int(v[0]), int(v[1]), int(v[2]),
                int(v[3]) if len(v) > 3 else 255]
    return list(fallback)


def text_metrics(state, text, size, style):
    inj = state.get("metrics", {})
    key = "%s|%d|%s" % (text, int(size), style)
    if key not in inj:
        raise AssertionError(
            "metrik teks tidak disuntik fixture: %r (Godot akan jatuh ke "
            "metrik font-nya sendiri dan geometri teks tidak bisa dibandingkan)"
            % key)
    m = inj[key]
    return [int(m[0]), int(m[1]), int(m[2]) if len(m) > 2 else int(m[1])]


def text_width(state, text, size, style):
    return text_metrics(state, text, size, style)[0]


# ═══════════════════════════════════════════════════════════════════
# Pembangun op (cermin BossOverlay.gd, urutan sama)
# ═══════════════════════════════════════════════════════════════════

def wrap_entrance(state, text, size):
    lines, cur = [], ""
    for w in text.split(" "):
        trial = (cur + " " + w).strip()
        if text_width(state, trial, size, "body_semibold") <= int(k("ENTRANCE_WRAP_W")):
            cur = trial
        else:
            if cur != "":
                lines.append(cur)
            cur = w
    if cur != "":
        lines.append(cur)
    if not lines:
        lines.append(text)
    return lines


def entrance_ops(state):
    ops = []
    timer = int(state.get("entrance_timer", 0))
    max_timer = int(state.get(
        "entrance_max",
        k("ENTRANCE_TRUE_FRAMES") if is_true(state) else k("ENTRANCE_MINI_FRAMES")))
    if max_timer <= 0:
        return ops
    progress = 1.0 - float(timer) / float(max_timer)
    radius = int(state.get("radius", 30))
    size = int(float(radius) * progress * 2.0)
    x = int(state.get("x", 0))
    y = int(state.get("y", 0))
    ecol = col_arr(state, "entrance_color", [140, 100, 220, 255])
    if size > 0:
        ops.append({"k": "disc", "c": [x, y], "r": size,
                    "col": with_alpha(ecol, a255(
                        int(k("ENTRANCE_DISC_ALPHA")) * (1.0 - progress)))})
    if timer > idiv(max_timer, 2):
        font_size = int(k("ENTRANCE_SIZE_TRUE")) if is_true(state) \
            else int(k("ENTRANCE_SIZE_MINI"))
        pulse = math.sin(float(int(state.get("anim_time", 0)))
                         * float(k("ABILITY_PULSE_RATE"))) * 0.3 + 0.7
        alpha = a255(float(k("ENTRANCE_TEXT_ALPHA")) * pulse)
        shadow_alpha = a255(float(k("ENTRANCE_SHADOW_ALPHA")) * pulse)
        lines = wrap_entrance(state, str(state.get("entrance_text", "")), font_size)
        start_y = int(k("ENTRANCE_BASE_Y")) - (len(lines) - 1) * int(k("ENTRANCE_LINE_COMPACT"))
        cx = idiv(int(state.get("screen_w", k("SCREEN_W"))), 2)
        for li, line in enumerate(lines):
            ly = start_y + li * int(k("ENTRANCE_LINE_STEP"))
            m = text_metrics(state, line, font_size, "body_semibold")
            tx0 = cx - idiv(int(m[0]), 2)
            ty0 = ly - idiv(int(m[1]), 2)
            base = {"k": "text", "text": line, "size": font_size,
                    "style": "body_semibold", "anchor": "topleft",
                    "wh": [int(m[0]), int(m[1])], "asc": int(m[2])}
            sh = dict(base)
            sh["col"] = with_alpha(k("GENERIC_BLACK"), shadow_alpha)
            sh["pos"] = [tx0 + int(k("ENTRANCE_SHADOW_OFFSET")),
                         ty0 + int(k("ENTRANCE_SHADOW_OFFSET"))]
            ops.append(sh)
            tx = dict(base)
            tx["col"] = with_alpha(ecol, alpha)
            tx["pos"] = [tx0, ty0]
            ops.append(tx)
    return ops


def filled_aura_bands(c, aura_r, rings, step, alpha_step, pulse, col):
    ops = []
    if aura_r <= 0:
        return ops
    radii, alphas = [], []
    for i in range(1, int(rings)):
        r_off = aura_r - int(float(step) * float(i))
        if r_off <= 0:
            continue
        alpha = a255(float(aura_r - r_off) * float(alpha_step) * pulse)
        if alpha <= 0:
            continue
        radii.append(r_off)
        alphas.append(alpha)
    for i in range(len(radii)):
        outer = int(radii[i])
        inner = int(radii[i + 1]) if i + 1 < len(radii) else 0
        ops.append({"k": "band", "c": list(c), "ri": inner, "ro": outer,
                    "col": with_alpha(col, int(alphas[i]))})
    return ops


def ability_aura_ops(state):
    pulse = math.sin(float(int(state.get("anim_time", 0)))
                     * float(k("ABILITY_PULSE_RATE"))) * 0.3 + 0.7
    aura_r = int(float(state.get("ability_range", 0.0)) * pulse)
    return filled_aura_bands([int(state.get("x", 0)), int(state.get("y", 0))],
                             aura_r, k("ABILITY_RINGS"), k("ABILITY_STEP"),
                             k("ABILITY_ALPHA_STEP"), pulse,
                             col_arr(state, "entrance_color",
                                     [140, 100, 220, 255]))


def enrage_aura_ops(state):
    ops = []
    pulse = math.sin(float(state.get("enrage_pulse", 0.0))) * 0.3 + 0.7
    radius = int(state.get("radius", 30))
    aura_r = radius + int(float(k("ENRAGE_MARGIN")) * pulse)
    col = k("ENRAGE_COLOR_TRUE") if is_true(state) else k("ENRAGE_COLOR_MINI")
    stop = max(int(k("ENRAGE_MIN_R")), aura_r - int(k("ENRAGE_SPAN")))
    c = [int(state.get("x", 0)), int(state.get("y", 0))]
    r_off = aura_r
    while r_off > stop:
        alpha = a200(float(aura_r - r_off) * float(k("ENRAGE_ALPHA_STEP")) * pulse)
        if alpha > 0 and r_off > 0:
            ops.append({"k": "ring", "c": list(c), "r": r_off,
                        "w": float(k("ENRAGE_RING_W")),
                        "col": with_alpha(col, alpha)})
        r_off -= int(k("ENRAGE_STEP"))
    return ops


def true_aura_ops(state):
    pulse = math.sin(float(state.get("pulse", 0.0))) * 0.3 + 0.7
    aura_r = int(state.get("radius", 30)) + int(k("AURA_MARGIN"))
    return filled_aura_bands([int(state.get("x", 0)), int(state.get("y", 0))],
                             aura_r, k("AURA_RINGS"), k("AURA_STEP"),
                             k("AURA_ALPHA_STEP"), pulse,
                             col_arr(state, "color", [140, 100, 220, 255]))


def shadow_ops(state):
    radius = int(state.get("radius", 30))
    w = radius * 2 + (int(k("SHADOW_TRUE_EXTRA")) if is_true(state) else 0)
    x = int(state.get("x", 0))
    y = int(state.get("y", 0))
    return [{"k": "ellipse", "w": 0,
             "rect": [x - idiv(w, 2), y + radius - int(k("SHADOW_DY")), w,
                      int(k("SHADOW_H"))],
             "col": list(k("SHADOW_COLOR"))}]


def debuff_ops(state):
    ops = []
    debuff = state.get("debuff", {})
    radius = int(state.get("radius", 30))
    x = int(state.get("x", 0))
    y = int(state.get("y", 0))
    if bool(debuff.get("slow", False)):
        ops.append({"k": "ellipse", "w": 1,
                    "rect": [x - radius - 2, y + radius - 7,
                             (radius + 2) * 2, 10],
                    "col": with_alpha(k("DEBUFF_SLOW_RING"), 255)})
    if bool(debuff.get("burn", False)):
        anim = float(int(state.get("anim_time", 0)))
        flick = int(1.5 + 1.5 * math.sin(anim * 0.6))
        flames = [[-radius + 2, -radius - 2, 2 + flick],
                  [radius - 2, -radius - 3, 2],
                  [0, -radius - 6, 3 + flick]]
        for fl in flames:
            fr = int(fl[2])
            fc = [x + int(fl[0]), y + int(fl[1])]
            ops.append({"k": "disc", "c": fc, "r": fr,
                        "col": with_alpha(k("DEBUFF_BURN_OUTER"), 255)})
            ops.append({"k": "disc", "c": fc, "r": max(1, fr - 1),
                        "col": with_alpha(k("DEBUFF_BURN_INNER"), 255)})
    pips = []
    for key in k("DEBUFF_PIP_ORDER"):
        if bool(debuff.get(str(key), False)):
            pips.append(k("DEBUFF_PIP_COLORS")[key])
    if pips:
        pip_y = y + radius + int(k("DEBUFF_PIP_DY"))
        total_w = len(pips) * int(k("DEBUFF_PIP_STEP")) - 1
        px = x - idiv(total_w, 2)
        for c in pips:
            ops.append({"k": "rect", "w": 0, "radius": 0,
                        "rect": [px - 1, pip_y - 1, int(k("DEBUFF_PIP_STEP")),
                                 int(k("DEBUFF_PIP_STEP"))],
                        "col": with_alpha(k("DEBUFF_PIP_BG"), 255)})
            ops.append({"k": "rect", "w": 0, "radius": 0,
                        "rect": [px, pip_y, int(k("DEBUFF_PIP_SIZE")),
                                 int(k("DEBUFF_PIP_SIZE"))],
                        "col": with_alpha(c, 255)})
            px += int(k("DEBUFF_PIP_STEP"))
    return ops


def generic_body_ops(state):
    ops = []
    radius = int(state.get("radius", 30))
    x = int(state.get("x", 0))
    y = int(state.get("y", 0))
    true_boss = is_true(state)
    body = col_arr(state, "color", [140, 100, 220, 255])
    if bool(state.get("hurt_flash", False)):
        body = k("GENERIC_HURT")
    dark = col_arr(state, "color_dark", body)
    ops.append({"k": "disc", "c": [x + 1, y + 1], "r": radius + 2,
                "col": with_alpha(k("GENERIC_BLACK"), 255)})
    ops.append({"k": "disc", "c": [x, y], "r": radius,
                "col": with_alpha(body, 255)})
    ops.append({"k": "ring", "c": [x, y], "r": radius, "w": 3.0,
                "col": with_alpha(dark, 255)})
    ops.append({"k": "disc",
                "c": [x - idiv(radius, 3), y - idiv(radius, 3)],
                "r": idiv(radius, 2), "col": lighten(body)})
    crown_count = 7 if true_boss else 5
    crown = k("GENERIC_CROWN_TRUE") if true_boss else k("GENERIC_CROWN_MINI")
    spike_h = 8 if true_boss else 6
    for i in range(crown_count):
        angle = math.pi + float(i - idiv(crown_count, 2)) * 0.25
        sx = x + int(math.cos(angle) * float(radius + 3))
        sy = y + int(math.sin(angle) * float(radius + 3))
        ops.append({"k": "poly", "col": with_alpha(crown, 255),
                    "pts": [[sx - 2, sy], [sx, sy - spike_h], [sx + 2, sy]]})
        if true_boss:
            ops.append({"k": "poly",
                        "col": with_alpha(k("GENERIC_CROWN_INNER"), 255),
                        "pts": [[sx - 1, sy], [sx, sy - spike_h + 2],
                                [sx + 1, sy]]})
    eye = k("GENERIC_EYE_TRUE") if true_boss else k("GENERIC_EYE_MINI")
    ops.append({"k": "disc", "c": [x - idiv(radius, 3), y - idiv(radius, 4)],
                "r": 4, "col": with_alpha(k("GENERIC_BLACK"), 255)})
    ops.append({"k": "disc", "c": [x + idiv(radius, 3), y - idiv(radius, 4)],
                "r": 4, "col": with_alpha(k("GENERIC_BLACK"), 255)})
    ops.append({"k": "disc", "c": [x - idiv(radius, 3), y - idiv(radius, 4)],
                "r": 2, "col": with_alpha(eye, 255)})
    ops.append({"k": "disc", "c": [x + idiv(radius, 3), y - idiv(radius, 4)],
                "r": 2, "col": with_alpha(eye, 255)})
    ops.append({"k": "ellipse", "w": 0,
                "rect": [x - 10, y - idiv(radius, 4) - 4, 20, 8],
                "col": with_alpha(eye, int(k("GENERIC_GLOW_ALPHA")))})
    return ops


def head_top(state):
    radius = int(state.get("radius", 30))
    if not bool(state.get("has_renderer", True)):
        return radius + 12
    label_top = int(state.get("label_top", 0))
    if label_top <= 0:
        label_top = radius
    return max(label_top, radius)


def bar_top_y(state):
    bar_h = int(k("BAR_H_TRUE")) if is_true(state) else int(k("BAR_H_MINI"))
    return int(state.get("y", 0)) - head_top(state) - int(k("BAR_GAP")) - bar_h


def bar_width(state):
    return int(k("BAR_W_TRUE")) if is_true(state) else int(k("BAR_W_MINI"))


def bar_height(state):
    return int(k("BAR_H_TRUE")) if is_true(state) else int(k("BAR_H_MINI"))


def border_color(state):
    if bool(state.get("is_enraged", False)):
        return k("BORDER_ENRAGED")
    return k("BORDER_TRUE") if is_true(state) else k("BORDER_MINI")


def label_color(state):
    if bool(state.get("is_enraged", False)):
        return k("LABEL_ENRAGED")
    return k("LABEL_TRUE") if is_true(state) else k("LABEL_MINI")


def plate_text(state):
    prefix = "TRUE BOSS" if is_true(state) else "BOSS"
    tag = ""
    if bool(state.get("is_enraged", False)):
        tag = " [ENRAGED]" if is_true(state) else " [FRENZY]"
    return "%s: %s%s" % (prefix, str(state.get("name", "Boss")), tag)


def plate_font_size(state):
    return int(k("PLATE_SIZE_TRUE")) if is_true(state) else int(k("PLATE_SIZE_MINI"))


def hp_bar_ops(state):
    bar_w, bar_h = bar_width(state), bar_height(state)
    x = int(state.get("x", 0))
    bx = x - idiv(bar_w, 2)
    by = bar_top_y(state)
    ops = [{"k": "rect", "w": 0, "radius": 0, "rect": [bx, by, bar_w, bar_h],
            "col": with_alpha(k("BAR_BG"), 255)}]
    max_hp = max(1.0, float(state.get("max_hp", 1.0)))
    ratio = float(state.get("hp", 0.0)) / max_hp
    fill = int(float(bar_w) * ratio)
    if fill > 0:
        if ratio > 0.5:
            hpc = k("HP_HIGH")
        elif ratio > 0.25:
            hpc = k("HP_MID")
        else:
            hpc = k("HP_LOW")
        ops.append({"k": "rect", "w": 0, "radius": 0,
                    "rect": [bx, by, fill, bar_h],
                    "col": with_alpha(hpc, 255)})
    ops.append({"k": "rect", "w": 1, "radius": 0,
                "rect": [bx, by, bar_w, bar_h],
                "col": with_alpha(border_color(state), 255)})
    return ops


def name_plate_ops(state):
    ops = []
    by = bar_top_y(state)
    font_size = plate_font_size(state)
    text = plate_text(state)
    m = text_metrics(state, text, font_size, "body_bold")
    tw, th = int(m[0]), int(m[1])
    x = int(state.get("x", 0))
    nx = x - idiv(tw, 2)
    ny = by - int(k("PLATE_TEXT_GAP")) - th
    bx = nx - idiv(int(k("PLATE_INFLATE_X")), 2)
    byy = ny - idiv(int(k("PLATE_INFLATE_Y")), 2)
    bw = tw + int(k("PLATE_INFLATE_X"))
    bh = th + int(k("PLATE_INFLATE_Y"))
    screen_w = int(state.get("screen_w", k("SCREEN_W")))
    margin = int(k("PLATE_MARGIN"))
    shift = 0
    if bx < margin:
        shift = margin - bx
    elif bx + bw > screen_w - margin:
        shift = -(bx + bw - (screen_w - margin))
    if shift != 0:
        nx += shift
        bx += shift
    ops.append({"k": "rect", "w": 0, "radius": int(k("PLATE_RADIUS")),
                "rect": [bx, byy, bw, bh],
                "col": with_alpha(k("PLATE_BG"), 255)})
    ops.append({"k": "rect", "w": 1, "radius": int(k("PLATE_RADIUS")),
                "rect": [bx, byy, bw, bh],
                "col": with_alpha(border_color(state), 255)})
    ops.append({"k": "text", "text": text, "size": font_size,
                "style": "body_bold",
                "col": with_alpha(label_color(state), 255),
                "anchor": "topleft", "pos": [nx, ny], "wh": [tw, th],
                "asc": int(m[2])})
    return ops


def is_entrance(state):
    return int(state.get("entrance_timer", 0)) > 0


def underlay_ops(state):
    if is_entrance(state):
        return entrance_ops(state)
    ops = []
    if bool(state.get("ability_active", False)):
        ops += ability_aura_ops(state)
    if bool(state.get("is_enraged", False)):
        ops += enrage_aura_ops(state)
    if is_true(state):
        ops += true_aura_ops(state)
    ops += shadow_ops(state)
    ops += debuff_ops(state)
    if not bool(state.get("has_renderer", True)):
        ops += generic_body_ops(state)
    return ops


def over_ops(state):
    if is_entrance(state):
        return []
    return hp_bar_ops(state) + name_plate_ops(state)


# ═══════════════════════════════════════════════════════════════════
# Pembanding
# ═══════════════════════════════════════════════════════════════════

def norm(v):
    """Samakan int/float supaya 2 == 2.0 (GDScript juga membandingkan begitu)."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, list):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {kk: norm(vv) for kk, vv in v.items()}
    return v


def diff_ops(got, want, layer):
    g, w = norm(got), norm(want)
    if len(g) != len(w):
        return "%s: jumlah op %d != %d" % (layer, len(g), len(w))
    for i, (a, b) in enumerate(zip(g, w)):
        if a != b:
            return "%s op[%d]:\n      twin   %s\n      pygame %s" % (
                layer, i, json.dumps(a, ensure_ascii=False),
                json.dumps(b, ensure_ascii=False))
    return None


# ═══════════════════════════════════════════════════════════════════
# Fidelitas transkripsi: twin Python harus memakai KONSTANTA dan LITERAL
# ANGKA yang sama dengan BossOverlay.gd. Tanpa ini, twin bisa "benar"
# sementara .gd salah ketik konstanta (nyata terjadi: ability_aura_ops
# .gd sempat memakai AURA_RINGS=8 padahal pygame-nya ABILITY_RINGS=7 —
# twin hijau, engine merah).
# ═══════════════════════════════════════════════════════════════════

TWIN_FUNCS = [
    "wrap_entrance", "entrance_ops", "filled_aura_bands", "ability_aura_ops",
    "enrage_aura_ops", "true_aura_ops", "shadow_ops", "debuff_ops",
    "generic_body_ops", "head_top", "bar_top_y", "bar_width", "bar_height",
    "border_color", "label_color", "plate_text", "plate_font_size",
    "hp_bar_ops", "name_plate_ops", "is_entrance", "is_true", "col_arr",
    "underlay_ops", "over_ops", "idiv", "a255", "a200", "with_alpha",
    "lighten",
]


def _strip_comments(lines):
    out = []
    for ln in lines:
        code = ln.split("#", 1)[0].rstrip()
        if code.strip():
            out.append(code)
    return "\n".join(out)


def gd_func_body(name):
    src = open(OVERLAY_GD, encoding="utf-8").read().splitlines()
    start = None
    for i, ln in enumerate(src):
        if ln.startswith("static func %s(" % name):
            start = i
            break
    if start is None:
        return None
    body = [src[start]]  # signature ikut: default arg bisa memakai konstanta
    for ln in src[start + 1:]:
        if ln.startswith("static func ") or ln.startswith("# ═") or ln.startswith("func "):
            break
        body.append(ln)
    return _strip_comments(body)


def py_func_body(name):
    import inspect
    fn = globals().get(name)
    if fn is None or not callable(fn):
        return None
    lines = inspect.getsource(fn).splitlines()
    # baris def ikut (simetris dengan signature .gd), docstring dibuang
    out, in_doc = [], False
    for i, ln in enumerate(lines):
        st = ln.strip()
        if not in_doc and (st.startswith('"""') or st.startswith("'''")):
            if st.count('"""') >= 2 or st.count("'''") >= 2:
                continue
            in_doc = True
            continue
        if in_doc:
            if '"""' in st or "'''" in st:
                in_doc = False
            continue
        out.append(ln)
    return _strip_comments(out)


def const_tokens_gd(body):
    return {t for t in re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b", body) if t in C}


def const_tokens_py(body):
    return set(re.findall(r'k\(\s*"(\w+)"\s*\)', body))


def number_tokens(body):
    nums = re.findall(r"(?<![\w.\"\'])(\d+\.\d+|\d+)(?![\w.])", body)
    out = []
    for n in nums:
        out.append(float(n))
    return sorted(out)


def fidelity_checks():
    section("Fidelitas transkripsi twin Python ↔ BossOverlay.gd")
    for name in TWIN_FUNCS:
        gb = gd_func_body(name)
        pb = py_func_body(name)
        if gb is None:
            check("%s: ada di BossOverlay.gd" % name, False, "static func tidak ditemukan")
            continue
        if pb is None:
            check("%s: ada di twin" % name, False, "fungsi Python tidak ditemukan")
            continue
        gt, pt = const_tokens_gd(gb), const_tokens_py(pb)
        check("%s: konstanta yang dipakai identik (%d)" % (name, len(gt | pt)),
              gt == pt,
              "hanya di .gd: %s | hanya di twin: %s"
              % (sorted(gt - pt), sorted(pt - gt)))
        gn, pn = number_tokens(gb), number_tokens(pb)
        check("%s: literal angka identik (%s)" % (name, gn), gn == pn,
              ".gd %s | twin %s" % (gn, pn))


def main():
    if not os.path.exists(FIXTURE):
        print("fixture belum ada: jalankan tools/test_boss_draw_parity.py")
        return 1
    fx = json.load(open(FIXTURE, encoding="utf-8"))
    scen = fx["scenarios"]
    print("BossOverlay.gd: %d konstanta dibaca | fixture: %d skenario, %d op"
          % (len(C), len(scen),
             sum(len(s["underlay"]) + len(s["over"]) for s in scen)))

    section("Konstanta .gd == angka pygame (base_boss.py / _core.py)")
    expect = {
        "AURA_RINGS": 8, "AURA_STEP": 2.0, "AURA_MARGIN": 15.0,
        "AURA_ALPHA_STEP": 5.0, "PULSE_SPEED": 6.0,
        "ABILITY_RINGS": 7, "ABILITY_STEP": 3.0, "ABILITY_ALPHA_STEP": 8.0,
        "ABILITY_PULSE_RATE": 0.2,
        "ENRAGE_STEP": 3, "ENRAGE_SPAN": 18, "ENRAGE_MIN_R": 5.0,
        "ENRAGE_ALPHA_STEP": 12.0, "ENRAGE_ALPHA_MAX": 200,
        "ENRAGE_MARGIN": 14.0, "ENRAGE_RING_W": 2.0,
        "ENTRANCE_TRUE_FRAMES": 180, "ENTRANCE_MINI_FRAMES": 120,
        "ENTRANCE_DISC_ALPHA": 200, "ENTRANCE_SHADOW_OFFSET": 2,
        "ENTRANCE_BASE_Y": 84, "ENTRANCE_LINE_COMPACT": 18,
        "ENTRANCE_LINE_STEP": 34, "ENTRANCE_SIZE_TRUE": 28,
        "ENTRANCE_SIZE_MINI": 24, "ENTRANCE_WRAP_W": 1000,
        "BAR_W_TRUE": 70, "BAR_W_MINI": 60, "BAR_H_TRUE": 10,
        "BAR_H_MINI": 8, "BAR_GAP": 6, "PLATE_MARGIN": 2,
        "PLATE_RADIUS": 3, "PLATE_INFLATE_X": 8, "PLATE_INFLATE_Y": 4,
        "PLATE_TEXT_GAP": 5, "PLATE_SIZE_TRUE": 20, "PLATE_SIZE_MINI": 18,
        "SHADOW_H": 12, "SHADOW_DY": 5, "SHADOW_TRUE_EXTRA": 10,
        "DEBUFF_PIP_STEP": 5, "DEBUFF_PIP_SIZE": 4, "DEBUFF_PIP_DY": 12,
        "SCREEN_W": 1280,
    }
    for name, val in sorted(expect.items()):
        check("%s = %s" % (name, val), norm(C.get(name)) == norm(val),
              "gdscript %s" % C.get(name))
    check("warna bayangan (0,0,0,120)", norm(C.get("SHADOW_COLOR")) == [0, 0, 0, 120],
          str(C.get("SHADOW_COLOR")))
    check("pip debuff 5 jenis urut pygame",
          [str(x) for x in C.get("DEBUFF_PIP_ORDER", [])]
          == ["slow", "atk_slow", "skill_down", "anti_heal", "burn"],
          str(C.get("DEBUFF_PIP_ORDER")))

    fidelity_checks()

    section("Op twin == op pygame (semua skenario fixture)")
    n_ops = 0
    for s in scen:
        name, state = s["name"], s["state"]
        try:
            gu, go = underlay_ops(state), over_ops(state)
        except AssertionError as exc:
            check("%s: twin berjalan" % name, False, str(exc))
            continue
        d = diff_ops(gu, s["underlay"], "underlay") or \
            diff_ops(go, s["over"], "over")
        check("%s: %d op underlay + %d op over identik"
              % (name, len(gu), len(go)), d is None, d or "")
        n_ops += len(gu) + len(go)

    section("Sifat lapisan (regresi makna, bukan cuma angka)")
    ent = [s for s in scen if s["state"]["entrance_timer"] > 0]
    check("entrance: %d skenario tanpa op bar/papan nama" % len(ent),
          all(not s["over"] for s in ent))
    check("entrance: underlay hanya disc/text",
          all(set(o["k"] for o in s["underlay"]) <= {"disc", "text"}
              for s in ent))
    body = [s for s in scen if not s["state"]["has_renderer"]]
    check("badan generik: %d skenario punya poly mahkota" % len(body),
          all(any(o["k"] == "poly" for o in s["underlay"]) for s in body))
    hurt = [s for s in body if s["state"]["hurt_flash"]]
    check("hurt flash: badan + highlight putih (255,255,255)",
          all(any(o["k"] == "disc" and o["col"][:3] == [255, 255, 255]
                  and o["r"] == s["state"]["radius"] for o in s["underlay"])
              for s in hurt), "%d skenario" % len(hurt))
    bands = [o for s in scen for o in s["underlay"] if o["k"] == "band"]
    check("pita alpha tidak tumpang tindih (%d band)" % len(bands),
          all(o["ri"] < o["ro"] for o in bands))
    check("pita alpha: tiap band punya inner < outer dan alpha > 0",
          all(0 < o["col"][3] <= 255 for o in bands))
    texts = [o for s in scen for o in s["underlay"] + s["over"]
             if o["k"] == "text"]
    check("teks membawa metrik pygame (wh + ascent) — %d op" % len(texts),
          all(o["wh"][0] > 0 and o["wh"][1] > 0 and o["asc"] > 0
              for o in texts))

    print("\n%d OK, %d FAIL (%d op dibandingkan)" % (_pass, _fail, n_ops))
    return 1 if _fail else 0


if __name__ == "__main__":
    sys.exit(main())
