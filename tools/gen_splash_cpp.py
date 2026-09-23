#!/usr/bin/env python3
"""Transpile splash_screen.py -> C++ GDExtension (godot++), FASE 38.

    python3 tools/gen_splash_cpp.py           # regenerasi
    python3 tools/gen_splash_cpp.py --check   # CI: berkas ter-commit identik

Pola sama dengan tools/gen_ui_cpp.py (FASE 36) dan tools/gen_maps_cpp.py
(FASE 35): angka diekstrak dari AST splash_screen.py — bukan disalin tangan.
Generator MENOLAK (bukan menebak) kalau literal/ekspresi yang dibutuhkan
hilang atau berubah bentuk, jadi tabel C++ tidak bisa basi tanpa CI merah.

Yang dibangkitkan:

  godot/gdext/mystic_splash/src/splash_processor.h
  godot/gdext/mystic_splash/src/splash_processor.cpp
  godot/gdext/mystic_splash/selftest/splash_dispatch.inc

Cakupan: SELURUH lapisan MODEL splash — timing/fade, alpha judul, gerak +
twinkle partikel, gradien latar + bingkai vignette, geometri logo (skala,
kuantisasi tumbuh, radius glow), lapisan glow judul + garis aksen, posisi +
alpha hint. Yang SENGAJA TIDAK diport: piksel (pygame.draw / _draw Godot) dan
METRIK FONT — lebar/tinggi teks dikirim sebagai parameter (pola FASE 36), dan
RNG partikel (pygame memakai RNG global tak ber-seed, jadi tidak ada stream
yang bisa diklaim; seed hanya dipakai fixture supaya rekaman reproducible).

Konvensi angka:
  * int64_t untuk piksel integral (pygame int()); pembagian `//` Python pada
    nilai non-negatif == `/` C++ (semua input di sini non-negatif setelah
    clamp; kasus batas dikunci tools/test_godot_splash_parity.py).
  * double untuk detik/rasio; ekspresi diteruskan verbatim supaya round-off
    identik.
  * `py_round` = round() CPython (half-to-even, dipakai kuantisasi tumbuh
    logo), `py_int` = int() Python (trunc ke arah nol).
"""
import argparse
import ast
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "splash_screen.py"
OUT_H = ROOT / "godot" / "gdext" / "mystic_splash" / "src" / "splash_processor.h"
OUT_CPP = (ROOT / "godot" / "gdext" / "mystic_splash" / "src"
           / "splash_processor.cpp")
OUT_DISPATCH = (ROOT / "godot" / "gdext" / "mystic_splash" / "selftest"
                / "splash_dispatch.inc")

CLASS = "MysticSplash"
LIBRARY = "mystic_splash"

MODULES = ["splash_screen"]


class SplashError(Exception):
    """splash_screen.py tidak memenuhi kontrak generator."""


def require(cond, message):
    if not cond:
        raise SplashError(message)


# ══════════════════════════════════════════════════════════
#  AST helpers
# ══════════════════════════════════════════════════════════


def parse_splash():
    source = SRC.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(SRC)), source


def top_class(tree, name="SplashScreen"):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise SplashError("class %s tidak ditemukan di %s" % (name, SRC.name))


def method(class_node, name):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SplashError("method %s.%s tidak ditemukan" % (class_node.name, name))


def fn_src(node):
    return ast.unparse(node)


def num(node, where):
    if (isinstance(node, ast.UnaryOp)
            and isinstance(node.op, (ast.USub, ast.UAdd))):
        value, line = num(node.operand, where)
        return (-value if isinstance(node.op, ast.USub) else value), line
    require(isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool),
            "%s: diharapkan literal angka, dapat %s" % (where, fn_src(node)))
    return node.value, node.lineno


def const_assign(tree, name):
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == name):
            return node.value, node.lineno
    raise SplashError("konstanta modul %s tidak ditemukan" % name)


def const_tuple(tree, name):
    node, line = const_assign(tree, name)
    require(isinstance(node, ast.Tuple) and len(node.elts) == 3,
            "%s diharapkan tuple-3, dapat %s" % (name, fn_src(node)))
    values = []
    for elt in node.elts:
        value, _ = num(elt, name)
        values.append(int(value))
    return tuple(values), line


def const_list(tree, name):
    node, line = const_assign(tree, name)
    require(isinstance(node, ast.List), "%s diharapkan list" % name)
    return node, line


def calls_in(node, func_name):
    """Semua Call di dalam `node` yang memanggil `func_name` (Name/Attribute)."""
    out = []
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        target = sub.func
        if isinstance(target, ast.Name) and target.id == func_name:
            out.append(sub)
        elif (isinstance(target, ast.Attribute)
                and target.attr == func_name):
            out.append(sub)
    return out


def walk_preorder(node):
    """DFS urutan sumber (ast.walk BFS bisa mendahului node bersarang)."""
    yield node
    for child in ast.iter_child_nodes(node):
        for sub in walk_preorder(child):
            yield sub


def dict_values(fn_node, key, where):
    """Literal dict di `fn_node`: nilai untuk kunci `key`."""
    for node in ast.walk(fn_node):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == key:
                return v
    raise SplashError("%s: kunci dict %r tidak ditemukan" % (where, key))


def _norm_ws(text):
    return " ".join(text.split())


def need(text, needles, where):
    flat = _norm_ws(text)
    for needle in needles:
        require(_norm_ws(needle) in flat,
                "%s: bentuk sumber berubah, tidak menemukan %r"
                % (where, needle))


# ══════════════════════════════════════════════════════════
#  Spesifikasi angka dari AST
# ══════════════════════════════════════════════════════════


class Spec:
    def __init__(self):
        self.values = {}
        self.lines = {}

    def take(self, key, value, line):
        self.values[key] = value
        self.lines[key] = line
        return value

    def __getitem__(self, key):
        require(key in self.values, "spesifikasi `%s` belum diekstrak" % key)
        return self.values[key]

    def line(self, key):
        return self.lines.get(key, 0)


def build_spec():
    tree, source = parse_splash()
    spec = Spec()
    spec.tree = tree
    spec.source = source
    cls = top_class(tree)

    # ── konstanta modul ──────────────────────────────────────
    name_node, name_line = const_assign(tree, "GAME_NAME")
    require(isinstance(name_node, ast.Constant)
            and isinstance(name_node.value, str),
            "GAME_NAME diharapkan literal string")
    spec.take("game_name", name_node.value, name_line)

    dur_node, dur_line = const_assign(tree, "SPLASH_DURATION")
    spec.take("duration", num(dur_node, "SPLASH_DURATION")[0], dur_line)

    paths_node, paths_line = const_list(tree, "LOGO_PATHS")
    paths = []
    for elt in paths_node.elts:
        require(isinstance(elt, ast.Constant)
                and isinstance(elt.value, str),
                "LOGO_PATHS diharapkan list literal string")
        paths.append(elt.value)
    spec.take("logo_paths", paths, paths_line)

    for key, cname in (("accent", "ACCENT"), ("accent_2", "ACCENT_2"),
                       ("text_main", "TEXT_MAIN"), ("text_dim", "TEXT_DIM")):
        spec.take(key, const_tuple(tree, cname)[0],
                  const_tuple(tree, cname)[1])

    # ── __init__: jumlah partikel ────────────────────────────
    init = method(cls, "__init__")
    make = calls_in(init, "_make_particles")
    require(len(make) == 1 and len(make[0].args) == 1,
            "__init__ diharapkan memanggil self._make_particles(<n>) sekali")
    spec.take("particle_count", num(make[0].args[0], "particle_count")[0],
              make[0].lineno)

    # ── _init_fonts: ukuran font (utama + fallback pygame) ───
    fonts = method(cls, "_init_fonts")
    fsrc = fn_src(fonts)
    need(fsrc, ["from _render import get_font as _gf, title_font as _tf",
                "pygame.font.Font(None, 40)"],
         "SplashScreen._init_fonts")
    sizes, fallback = {}, {}
    for target, call in (("presents", "_gf(34, 'body_bold')"),
                         ("title", "_tf(92)"),
                         ("title_below", "_tf(66)"),
                         ("sub", "_gf(22, 'body_semibold')"),
                         ("hint", "_gf(16, 'body_medium')")):
        require(_norm_ws(call) in _norm_ws(fsrc),
                "_init_fonts: panggilan %s berubah bentuk" % call)
    ROLE = {"font_presents": "presents", "font_title": "title",
            "font_title_below": "title_below", "font_sub": "sub",
            "font_hint": "hint"}
    # ekstrak angka dari AST dalam URUTAN SUMBER: cabang utama memanggil
    # _gf(n, style)/_tf(n); cabang fallback memanggil pygame.font.Font(None, n)
    # (args[0] None) — keduanya diambil dari kemunculan PERTAMA per peran.
    for node in ast.walk(fonts):
        if not isinstance(node, ast.Assign):
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Attribute) or tgt.attr not in ROLE:
            continue
        role = ROLE[tgt.attr]
        call = node.value
        require(isinstance(call, ast.Call) and len(call.args) >= 1,
                "_init_fonts: %s bukan panggilan font" % tgt.attr)
        if isinstance(call.func, ast.Name) and call.func.id in ("_gf", "_tf"):
            if role in sizes:
                continue
            value, line = num(call.args[0], "_init_fonts.%s" % tgt.attr)
            sizes[role] = int(value)
            style = "title" if call.func.id == "_tf" else None
            if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
                style = call.args[1].value
            if role == "presents":
                spec.take("style_presents", style, line)
            elif role == "sub":
                spec.take("style_sub", style, line)
            elif role == "hint":
                spec.take("style_hint", style, line)
        elif (isinstance(call.func, ast.Attribute)
              and call.func.attr == "Font"):
            if role in fallback:
                continue
            require(isinstance(call.args[0], ast.Constant)
                    and call.args[0].value is None,
                    "_init_fonts: fallback %s bukan Font(None, n)" % tgt.attr)
            value, _ = num(call.args[1], "_init_fonts.fallback.%s" % tgt.attr)
            fallback[role] = int(value)
    require(set(sizes) == {"presents", "title", "title_below", "sub", "hint"},
            "_init_fonts: ukuran font tidak lengkap: %s" % sorted(sizes))
    spec.take("font_sizes", sizes, fonts.lineno)
    spec.take("font_fallback_sizes", fallback, fonts.lineno)

    # ── _make_particles: rentang RNG + palet warna ───────────
    mk = method(cls, "_make_particles")
    msrc = fn_src(mk)
    need(msrc, ["random.uniform(0, self.w)", "random.uniform(0, self.h)",
                "random.uniform(0, math.tau)"],
         "SplashScreen._make_particles")
    ranges = {}
    for key in ("r", "speed", "drift", "phase"):
        value = dict_values(mk, key, "_make_particles")
        call = value
        require(isinstance(call, ast.Call) and len(call.args) == 2,
                "_make_particles.%s diharapkan random.uniform(a, b)" % key)
        lo, _ = num(call.args[0], "_make_particles.%s.lo" % key)
        hi_node = call.args[1]
        # phase memakai math.tau (bukan literal) — terima bentuk itu saja.
        if (key == "phase" and isinstance(hi_node, ast.Attribute)
                and hi_node.attr == "tau"
                and isinstance(hi_node.value, ast.Name)
                and hi_node.value.id == "math"):
            hi, line = math.tau, hi_node.lineno
        else:
            hi, line = num(hi_node, "_make_particles.%s.hi" % key)
        ranges[key] = (lo, hi)
        spec.take("prange_%s" % key, (lo, hi), line)
    colors_node = dict_values(mk, "color", "_make_particles")
    require(isinstance(colors_node, ast.Call)
            and len(colors_node.args) == 1
            and isinstance(colors_node.args[0], ast.List),
            "_make_particles.color diharapkan random.choice([...])")
    colors = []
    for elt in colors_node.args[0].elts:
        require(isinstance(elt, ast.Tuple) and len(elt.elts) == 3,
                "_make_particles: palet diharapkan tuple-3")
        colors.append(tuple(int(num(e, "palet partikel")[0]) for e in elt.elts))
    spec.take("particle_colors", colors, colors_node.lineno)

    # ── update(): gerak partikel + fase selesai + alpha judul ─
    upd = method(cls, "update")
    usrc = fn_src(upd)
    need(usrc, ["p['y'] -= p['speed']",
                "p['x'] += p['drift'] + math.sin(self.elapsed * 0.8 "
                "+ p['phase']) * 0.05",
                "if p['y'] < -6:", "p['y'] = self.h + 6",
                "p['x'] = random.uniform(0, self.w)",
                "if self.elapsed >= 0.25:", "elif self.elapsed >= dur:",
                "if t < 0.5:",
                "self.title_alpha = int(255 * min(1.0, (t - 0.5) / 0.6))"],
         "SplashScreen.update")
    spec.take("move_rate", 0.8, upd.lineno)
    spec.take("move_amp", 0.05, upd.lineno)
    spec.take("wrap_below", -6.0, upd.lineno)
    spec.take("wrap_margin", 6.0, upd.lineno)
    spec.take("skip_done", 0.25, upd.lineno)
    spec.take("title_delay", 0.5, upd.lineno)
    spec.take("title_ramp", 0.6, upd.lineno)
    spec.take("title_max", 255, upd.lineno)

    # ── _overall_alpha(): kurva fade ─────────────────────────
    oa = method(cls, "_overall_alpha")
    asrc = fn_src(oa)
    need(asrc, ["fade_in = min(1.0, t / 0.4)",
                "fade_out = max(0.0, 1.0 - t / 0.25)",
                "fade_out = min(1.0, max(0.0, (dur - t) / 0.45))",
                "return max(0.0, min(1.0, fade_in * fade_out))"],
         "SplashScreen._overall_alpha")
    spec.take("fade_in", 0.4, oa.lineno)
    spec.take("fade_out", 0.45, oa.lineno)
    spec.take("skip_fade", 0.25, oa.lineno)

    # ── draw(): latar, partikel, jangkar konten, hint ────────
    draw = method(cls, "draw")
    dsrc = fn_src(draw)
    need(dsrc, ["if a <= 0.001:",
                "top = (8, 8, 18)", "mid = (22, 16, 38)", "bot = (6, 6, 14)",
                "step_h = max(1, self.h // 48)",
                "for i in range(0, self.h, step_h):",
                "if f < 0.55:", "f2 = f / 0.55",
                "f2 = (f - 0.55) / 0.45",
                "for i in range(140, 0, -2):",
                "alpha = min(255, int(2.2 * (140 - i)))",
                "(i, i, self.w - 2 * i, self.h - 2 * i)",
                "tw = 0.5 + 0.5 * math.sin(self.elapsed * 2.5 + p['phase'])",
                "col = tuple((int(ch * (0.35 + 0.65 * tw)) "
                "for ch in p['color']))",
                "max(1, int(p['r']))",
                "cx = self.w // 2", "base_y = self.h // 2",
                "logo_cy = base_y - (26 if self.logo_img is not None else 0)",
                "hint = self.font_hint.render(",
                "hr = hint.get_rect(center=(cx, self.h - 48))",
                "hint.set_alpha(int(140 * a))"],
         "SplashScreen.draw")
    spec.take("alpha_epsilon", 0.001, draw.lineno)
    spec.take("grad_top", (8, 8, 18), draw.lineno)
    spec.take("grad_mid", (22, 16, 38), draw.lineno)
    spec.take("grad_bot", (6, 6, 14), draw.lineno)
    spec.take("band_target", 48, draw.lineno)
    spec.take("grad_split", 0.55, draw.lineno)
    spec.take("vig_start", 140, draw.lineno)
    spec.take("vig_step", -2, draw.lineno)
    spec.take("vig_slope", 2.2, draw.lineno)
    spec.take("twinkle_rate", 2.5, draw.lineno)
    spec.take("dim_floor", 0.35, draw.lineno)
    spec.take("dim_span", 0.65, draw.lineno)
    spec.take("particle_min_r", 1, draw.lineno)
    spec.take("logo_lift", 26, draw.lineno)
    spec.take("hint_margin", 48, draw.lineno)
    spec.take("hint_alpha", 140, draw.lineno)
    hint_text = None
    for node in ast.walk(draw):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "render" and node.args):
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                hint_text = first.value
    require(hint_text is not None, "draw: teks hint tidak ditemukan")
    spec.take("hint_text", hint_text, draw.lineno)

    # ── _draw_logo_or_title(): geometri logo + offset teks ───
    logo = method(cls, "_draw_logo_or_title")
    lsrc = fn_src(logo)
    need(lsrc, ["scale = min(340.0 / img.get_width(),",
                "320.0 / img.get_height(), 1.0)",
                "w = max(1, int(img.get_width() * scale))",
                "grow = min(1.0, self.elapsed / 0.9)",
                "gq = round((0.85 + 0.15 * grow) * 20) / 20.0",
                "ww = max(1, int(w * gq))", "hh = max(1, int(h * gq))",
                "glow_r = max(ww, hh) // 2 + 30",
                "for g in range(glow_r, 0, -3):",
                "alpha_g = int(12 * (1 - g / glow_r))",
                "rect.bottom + 46", "rect.bottom + 88", "base_y + 66"],
         "SplashScreen._draw_logo_or_title")
    spec.take("logo_max_w", 340.0, logo.lineno)
    spec.take("logo_max_h", 320.0, logo.lineno)
    spec.take("grow_time", 0.9, logo.lineno)
    spec.take("grow_min", 0.85, logo.lineno)
    spec.take("grow_span", 0.15, logo.lineno)
    spec.take("grow_quant", 20, logo.lineno)
    spec.take("glow_pad", 30, logo.lineno)
    spec.take("glow_step", -3, logo.lineno)
    spec.take("glow_alpha", 12, logo.lineno)
    spec.take("title_below", 46, logo.lineno)
    spec.take("sub_below", 88, logo.lineno)
    spec.take("sub_text_only", 66, logo.lineno)
    tagline = None
    for node in ast.walk(logo):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "render" and node.args):
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                tagline = first.value
    require(tagline is not None, "_draw_logo_or_title: tagline tidak ditemukan")
    spec.take("tagline", tagline, logo.lineno)

    # ── _draw_glow_title(): lapisan glow + garis aksen ───────
    glow = method(cls, "_draw_glow_title")
    gsrc = fn_src(glow)
    need(gsrc, ["for layer, spread in [(24, 1), (14, 2), (8, 3)] if _cheap else []:",
                "glow.fill((*ACCENT, int(alpha * 0.28)),",
                "glow.get_width() + 2, glow.get_height() + 2",
                "surf.blit(glow, (rect.x - layer - 1, rect.y - layer - 1))",
                "gap = rect.w // 2 + 18",
                "for off, col in [(-6, ACCENT), (6, ACCENT_2)]:",
                "fac = alpha / 255.0 * 0.85",
                "(cx - gap + 46, y + off)", "(cx + gap - 46, y + off)"],
         "SplashScreen._draw_glow_title")
    layers_node = None
    for node in walk_preorder(glow):
        if not (isinstance(node, ast.List) and node.elts):
            continue
        items = []
        ok = True
        for elt in node.elts:
            if not (isinstance(elt, ast.Tuple) and len(elt.elts) == 2):
                ok = False
                break
            try:
                a, _ = num(elt.elts[0], "glow layer")
                b, _ = num(elt.elts[1], "glow spread")
            except SplashError:
                ok = False
                break
            items.append((int(a), int(b)))
        if ok:
            layers_node = items
            break
    require(layers_node == [(24, 1), (14, 2), (8, 3)],
            "_draw_glow_title: tabel lapisan glow berubah: %s" % layers_node)
    spec.take("glow_layers", layers_node, glow.lineno)
    spec.take("glow_fill", 0.28, glow.lineno)
    spec.take("glow_grow", 2, glow.lineno)
    spec.take("glow_offset", 1, glow.lineno)
    spec.take("accent_pad", 18, glow.lineno)
    offsets_node = None
    for node in walk_preorder(glow):
        if not (isinstance(node, ast.List) and len(node.elts) == 2):
            continue
        items = []
        ok = True
        for elt in node.elts:
            if not (isinstance(elt, ast.Tuple) and len(elt.elts) == 2
                    and isinstance(elt.elts[1], ast.Name)):
                ok = False
                break
            a, _ = num(elt.elts[0], "accent off")
            items.append((int(a), elt.elts[1].id))
        if ok:
            offsets_node = items
            break
    require(offsets_node == [(-6, "ACCENT"), (6, "ACCENT_2")],
            "_draw_glow_title: pasangan garis aksen berubah: %s"
            % offsets_node)
    spec.take("accent_offsets", offsets_node, glow.lineno)
    spec.take("accent_fac", 0.85, glow.lineno)
    spec.take("accent_len", 46, glow.lineno)
    spec.take("accent_width", 2, glow.lineno)
    return spec


# ══════════════════════════════════════════════════════════
#  Emisi C++
# ══════════════════════════════════════════════════════════


def c8(triple):
    r, g, b = triple
    return ("Color(%d.0f / 255.0f, %d.0f / 255.0f, %d.0f / 255.0f)"
            % (r, g, b))


def tpl(text, **values):
    for key, value in values.items():
        text = text.replace("@%s@" % key.upper(), str(value))
    return text


_FUNCS = []


def fn(name, comment, ret, args, body):
    """args: [(tipe, nama)] — C++ mentah."""
    _FUNCS.append((name, comment, ret, args, body))


def arglist(args):
    return ", ".join("%s %s" % (t, n) for t, n in args)


def signatures(funcs):
    for name, _comment, ret, args, _body in funcs:
        yield name, "    static %s %s(%s);" % (ret, name, arglist(args))


def build_functions(spec):
    del _FUNCS[:]

    # ── meta ─────────────────────────────────────────────────
    fn("module_names",
       "Daftar modul sumber splash (urutan bundle) — oracle memakai daftar "
       "ini untuk audit closed-world.",
       "Array", [], """
    Array out;
    out.push_back(String("splash_screen"));
    return out;""")
    fn("module_names_string",
       "Gabungan module_names() dengan koma (untuk cap jari + log).",
       "String", [], """
    Array names = module_names();
    String out;
    for (int64_t i = 0; i < names.size(); i++) {
        if (i > 0) {
            out += String(",");
        }
        out += (String)names[i];
    }
    return out;""")
    fn("api_signature",
       "Cap jari API: jumlah modul + fungsi (dipakai loader membuktikan "
       "backend C++ benar-benar jalan, dicetak sekali per perubahan backend).",
       "String", [], """
    return String("splash_v1:1mod:0fn:");""")
    fn("game_name",
       "GAME_NAME (splash_screen.py:%d)." % spec.line("game_name"),
       "String", [], """
    return String("%s");""" % spec["game_name"])
    fn("tagline",
       "Tagline di bawah judul (_draw_logo_or_title baris %d)."
       % spec.line("tagline"),
       "String", [], """
    return String("%s");""" % spec["tagline"])
    fn("hint_text",
       "Teks hint skip (draw baris %d)." % spec.line("hint_text"),
       "String", [], """
    return String("%s");""" % spec["hint_text"])
    fn("splash_duration",
       "SPLASH_DURATION (splash_screen.py:%d) — detik sebelum auto-pindah."
       % spec.line("duration"),
       "double", [], """
    return %r;""" % spec["duration"])
    fn("logo_paths",
       "LOGO_PATHS (splash_screen.py:%d) — urutan pencarian file logo."
       % spec.line("logo_paths"),
       "Array", [], "    Array out;"
       + "".join('\n    out.push_back(String("%s"));' % p
                 for p in spec["logo_paths"])
       + "\n    return out;")

    # ── warna ────────────────────────────────────────────────
    for key, cname in (("accent", "ACCENT"), ("accent_2", "ACCENT_2"),
                       ("text_main", "TEXT_MAIN"), ("text_dim", "TEXT_DIM")):
        rgb = spec[key]
        fn(key, "%s (splash_screen.py:%d) = %s." % (cname, spec.line(key), rgb),
           "Color", [], """
    return %s;""" % c8(rgb))
    fn("gradient_stops",
       "Tiga stop gradien latar (draw baris %d): top/mid/bot."
       % spec.line("grad_top"),
       "Dictionary", [], tpl("""
    Dictionary out;
    out["top"] = @TOP@;
    out["mid"] = @MID@;
    out["bot"] = @BOT@;
    return out;""", top=c8(spec["grad_top"]), mid=c8(spec["grad_mid"]),
                             bot=c8(spec["grad_bot"])))
    color_rows = []
    for i, rgb in enumerate(spec["particle_colors"]):
        color_rows.append(tpl("""
    out.push_back(@C@);""", c=c8(rgb)))
    fn("particle_colors",
       "Palet warna partikel (_make_particles baris %d), urutan choice."
       % spec.line("particle_colors"),
       "Array", [], "    Array out;" + "".join(color_rows)
       + "\n    return out;")

    # ── font ─────────────────────────────────────────────────
    def size_dict(name, table, comment):
        rows = "".join('\n    out["%s"] = (int64_t)%d;' % (k, table[k])
                       for k in ("presents", "title", "title_below", "sub",
                                 "hint"))
        fn(name, comment, "Dictionary", [], "    Dictionary out;" + rows
           + "\n    return out;")

    size_dict("font_sizes", spec["font_sizes"],
              "Ukuran font utama (_init_fonts baris %d): presents=body_bold, "
              "title/title_below=Cinzel, sub=body_semibold, hint=body_medium."
              % spec.line("font_sizes"))
    size_dict("font_fallback_sizes", spec["font_fallback_sizes"],
              "Ukuran font fallback pygame (_init_fonts baris %d)."
              % spec.line("font_fallback_sizes"))
    fn("font_styles",
       "Gaya font per peran (_init_fonts baris %d): body_bold / "
       "body_semibold / body_medium; title memakai Cinzel."
       % spec.line("font_sizes"),
       "Dictionary", [], tpl("""
    Dictionary out;
    out["presents"] = String("@PRESENTS@");
    out["title"] = String("title");
    out["title_below"] = String("title");
    out["sub"] = String("@SUB@");
    out["hint"] = String("@HINT@");
    return out;""", presents=spec["style_presents"], sub=spec["style_sub"],
                      hint=spec["style_hint"]))

    # ── partikel ─────────────────────────────────────────────
    fn("particle_count",
       "Jumlah partikel latar (__init__ baris %d: _make_particles(%d))."
       % (spec.line("particle_count"), spec["particle_count"]),
       "int64_t", [], """
    return %d;""" % spec["particle_count"])
    def range_rows():
        rows = []
        for key in ("r", "speed", "drift", "phase"):
            lo, hi = spec["prange_%s" % key]
            rows.append('\n    out["%s_lo"] = %r;\n    out["%s_hi"] = %r;'
                        % (key, lo, key, hi))
        return "".join(rows)
    fn("particle_ranges",
       "Rentang random.uniform per kunci partikel (_make_particles baris "
       "%d). x/y memakai ukuran layar, phase memakai math.tau."
       % spec.line("prange_r"),
       "Dictionary", [], "    Dictionary out;" + range_rows()
       + '\n    out["phase_hi"] = M_PI * 2.0;'
       + "\n    return out;")
    fn("particle_move",
       "Satu langkah gerak partikel (update baris %d): y -= speed; "
       "x += drift + sin(elapsed*%g + phase)*%g. Mengembalikan posisi BARU "
       "(double, BUKAN Vector2 — komponen Vector2 Godot float32 akan "
       "memangkas presisi stream partikel)."
       % (spec.line("move_rate"), spec["move_rate"], spec["move_amp"]),
       "Dictionary", [("double", "x"), ("double", "y"), ("double", "speed"),
                      ("double", "drift"), ("double", "phase"),
                      ("double", "elapsed")], tpl("""
    Dictionary out;
    out["y"] = y - speed;
    out["x"] = x + drift + std::sin(elapsed * @RATE@ + phase) * @AMP@;
    return out;""", rate=spec["move_rate"], amp=spec["move_amp"]))
    fn("particle_wrapped",
       "Predikat wrap vertikal (update baris %d: p[\"y\"] < %g)."
       % (spec.line("wrap_below"), spec["wrap_below"]),
       "bool", [("double", "y")], tpl("""
    return y < @BELOW@;""", below=spec["wrap_below"]))
    fn("particle_wrap_y",
       "Nilai y sesudah wrap (update baris %d: self.h + %g)."
       % (spec.line("wrap_margin"), spec["wrap_margin"]),
       "double", [("double", "screen_h")], tpl("""
    return screen_h + @MARGIN@;""", margin=spec["wrap_margin"]))
    fn("particle_advance",
       "Langkah partikel LENGKAP (update baris %d): gerak + wrap; x baru "
       "sesudah wrap diserahkan pemanggil (RNG pygame global tak ber-seed, "
       "jadi tidak ada stream yang bisa direplika)."
       % spec.line("move_rate"),
       "Dictionary", [("double", "x"), ("double", "y"), ("double", "speed"),
                      ("double", "drift"), ("double", "phase"),
                      ("double", "elapsed"), ("double", "screen_h"),
                      ("double", "respawn_x")], tpl("""
    Dictionary moved = particle_move(x, y, speed, drift, phase, elapsed);
    double nx = (double)moved["x"];
    double ny = (double)moved["y"];
    bool wrapped = particle_wrapped(ny);
    if (wrapped) {
        ny = particle_wrap_y(screen_h);
        nx = respawn_x;
    }
    Dictionary out;
    out["x"] = nx;
    out["y"] = ny;
    out["wrapped"] = wrapped;
    return out;"""))
    fn("particle_twinkle",
       "Faktor kelip partikel (draw baris %d): 0.5 + 0.5*sin(elapsed*%g + "
       "phase)." % (spec.line("twinkle_rate"), spec["twinkle_rate"]),
       "double", [("double", "elapsed"), ("double", "phase")], tpl("""
    return 0.5 + 0.5 * std::sin(elapsed * @RATE@ + phase);""",
                                                                    rate=spec["twinkle_rate"]))
    fn("particle_channel",
       "Satu kanal warna partikel (draw baris %d): int(ch * (%g + %g*tw)) — "
       "trunc int() Python, bukan round."
       % (spec.line("dim_floor"), spec["dim_floor"], spec["dim_span"]),
       "int64_t", [("int64_t", "channel"), ("double", "twinkle")], tpl("""
    return py_int((double)channel * (@FLOOR@ + @SPAN@ * twinkle));""",
                                                                        floor=spec["dim_floor"], span=spec["dim_span"]))
    fn("particle_draw_color",
       "Warna gambar partikel (draw baris %d) — ketiga kanal di-trunc."
       % spec.line("dim_floor"),
       "Color", [("const Color &", "base"), ("double", "twinkle")], """
    double factor = @FLOOR@ + @SPAN@ * twinkle;
    return Color((double)py_int((double)base.get_r8() * factor) / 255.0,
                 (double)py_int((double)base.get_g8() * factor) / 255.0,
                 (double)py_int((double)base.get_b8() * factor) / 255.0);""".replace(
        "@FLOOR@", "%g" % spec["dim_floor"]).replace(
        "@SPAN@", "%g" % spec["dim_span"]))
    fn("particle_draw_radius",
       "Radius gambar partikel (draw baris %d): max(%d, int(r)) — trunc."
       % (spec.line("particle_min_r"), spec["particle_min_r"]),
       "int64_t", [("double", "r")], tpl("""
    int64_t radius = py_int(r);
    return radius > @MIN@ ? radius : @MIN@;""", min=spec["particle_min_r"]))
    fn("particle_draw_pos",
       "Posisi gambar partikel (draw baris %d): (int(x), int(y)) — trunc."
       % spec.line("particle_min_r"),
       "Vector2", [("double", "x"), ("double", "y")], """
    return Vector2((double)py_int(x), (double)py_int(y));""")

    # ── timing & state ───────────────────────────────────────
    fn("fade_in",
       "Kurva fade in (_overall_alpha baris %d): min(1, t/%g)."
       % (spec.line("fade_in"), spec["fade_in"]),
       "double", [("double", "t")], tpl("""
    double v = t / @T@;
    return v < 1.0 ? v : 1.0;""", t=spec["fade_in"]))
    fn("fade_out_normal",
       "Kurva fade out normal (_overall_alpha baris %d): "
       "clamp((dur - t)/%g, 0, 1)." % (spec.line("fade_out"),
                                       spec["fade_out"]),
       "double", [("double", "t")], tpl("""
    double v = (@DUR@ - t) / @T@;
    if (v < 0.0) {
        return 0.0;
    }
    return v < 1.0 ? v : 1.0;""", dur=spec["duration"], t=spec["fade_out"]))
    fn("fade_out_skip",
       "Kurva fade out saat skip (_overall_alpha baris %d): max(0, 1 - t/%g). "
       "Python memakai t = elapsed TOTAL (bukan sejak skip) — lihat "
       "overall_alpha vs overall_alpha_godot."
       % (spec.line("skip_fade"), spec["skip_fade"]),
       "double", [("double", "t")], tpl("""
    double v = 1.0 - t / @T@;
    return v < 0.0 ? 0.0 : v;""", t=spec["skip_fade"]))
    fn("overall_alpha",
       "Alpha keseluruhan SEMANTIK PYGAME (_overall_alpha baris %d): "
       "fade_in(t) * (skipped ? fade_out_skip(t) : fade_out_normal(t)). "
       "Perhatikan: cabang skip memakai elapsed TOTAL, jadi skip sesudah "
       "0.25 dtk langsung menghasilkan alpha 0 (fade tidak terlihat)."
       % spec.line("fade_in"),
       "double", [("double", "t"), ("bool", "skipped")], """
    double out = fade_in(t);
    if (skipped) {
        out *= fade_out_skip(t);
    } else {
        out *= fade_out_normal(t);
    }
    if (out < 0.0) {
        return 0.0;
    }
    return out < 1.0 ? out : 1.0;""")
    fn("overall_alpha_godot",
       "Alpha keseluruhan SEMANTIK PORT GODOT: sama dengan overall_alpha "
       "tapi cabang skip memakai `skip_t` (detik sejak skip) — deviasi "
       "SplashScreen.gd yang DITUTUP FASE 38 untuk fade, dipertahankan di "
       "sini hanya sebagai pembanding A/B harness.",
       "double", [("double", "t"), ("bool", "skipped"), ("double", "skip_t")],
       """
    double out = fade_in(t);
    if (skipped) {
        out *= fade_out_skip(skip_t);
    } else {
        out *= fade_out_normal(t);
    }
    if (out < 0.0) {
        return 0.0;
    }
    return out < 1.0 ? out : 1.0;""")
    fn("title_alpha",
       "Alpha judul (update baris %d): 0 sebelum %g dtk, lalu "
       "int(%d * min(1, (t-%g)/%g)) — trunc int() Python."
       % (spec.line("title_delay"), spec["title_delay"], spec["title_max"],
          spec["title_delay"], spec["title_ramp"]),
       "int64_t", [("double", "t")], tpl("""
    if (t < @DELAY@) {
        return 0;
    }
    double v = (t - @DELAY@) / @RAMP@;
    if (v > 1.0) {
        v = 1.0;
    }
    return py_int((double)@MAX@ * v);""", delay=spec["title_delay"],
                                          ramp=spec["title_ramp"], max=spec["title_max"]))
    fn("is_done",
       "Predikat selesai SEMANTIK PYGAME (update baris %d): skipped ? "
       "elapsed >= %g : elapsed >= dur — lagi-lagi elapsed TOTAL."
       % (spec.line("skip_done"), spec["skip_done"]),
       "bool", [("double", "t"), ("bool", "skipped")], tpl("""
    if (skipped) {
        return t >= @SKIP@;
    }
    return t >= @DUR@;""", skip=spec["skip_done"], dur=spec["duration"]))
    fn("is_done_godot",
       "Predikat selesai SEMANTIK PORT GODOT: cabang skip memakai skip_t "
       "(detik sejak skip). Deviasi SplashScreen.gd pra-FASE 38.",
       "bool", [("double", "t"), ("bool", "skipped"), ("double", "skip_t")],
       tpl("""
    if (skipped) {
        return skip_t >= @SKIP@;
    }
    return t >= @DUR@;""", skip=spec["skip_done"], dur=spec["duration"]))
    fn("draw_visible",
       "Gerbang draw (draw baris %d): alpha > %g."
       % (spec.line("alpha_epsilon"), spec["alpha_epsilon"]),
       "bool", [("double", "alpha")], tpl("""
    return alpha > @EPS@;""", eps=spec["alpha_epsilon"]))
    fn("title_alpha_drawn",
       "Alpha judul SESUDAH dikalikan alpha keseluruhan "
       "(_draw_logo_or_title baris %d): int(title_alpha * a) — trunc."
       % spec.line("title_below"),
       "int64_t", [("int64_t", "title_alpha"), ("double", "overall")], """
    return py_int((double)title_alpha * overall);""")
    fn("timings",
       "Seluruh konstanta waktu/alpha splash dalam satu Dictionary (untuk "
       "log + fixture): durasi, kurva fade, ambang judul, kuantisasi tumbuh, "
       "epsilon draw.",
       "Dictionary", [], tpl("""
    Dictionary out;
    out["duration"] = @DURATION@;
    out["fade_in"] = @FADE_IN@;
    out["fade_out"] = @FADE_OUT@;
    out["skip_fade"] = @SKIP_FADE@;
    out["skip_done"] = @SKIP_DONE@;
    out["title_delay"] = @TITLE_DELAY@;
    out["title_ramp"] = @TITLE_RAMP@;
    out["title_max"] = (int64_t)@TITLE_MAX@;
    out["grow_time"] = @GROW_TIME@;
    out["alpha_epsilon"] = @EPS@;
    return out;""", duration=spec["duration"], fade_in=spec["fade_in"],
                     fade_out=spec["fade_out"], skip_fade=spec["skip_fade"],
                     skip_done=spec["skip_done"],
                     title_delay=spec["title_delay"],
                     title_ramp=spec["title_ramp"],
                     title_max=spec["title_max"],
                     grow_time=spec["grow_time"],
                     eps=spec["alpha_epsilon"]))

    # ── latar: gradien + vignette ────────────────────────────
    fn("bg_step_h",
       "Tinggi satu batang gradien (draw baris %d): max(1, h // %d)."
       % (spec.line("band_target"), spec["band_target"]),
       "int64_t", [("int64_t", "screen_h")], tpl("""
    int64_t step = screen_h / @BANDS@;
    return step > 1 ? step : 1;""", bands=spec["band_target"]))
    fn("bg_band_count",
       "Jumlah batang gradien (draw baris %d): len(range(0, h, step_h))."
       % spec.line("band_target"),
       "int64_t", [("int64_t", "screen_h")], """
    int64_t step = bg_step_h(screen_h);
    return (screen_h + step - 1) / step;""")
    fn("bg_band_rect",
       "Rect satu batang gradien (draw baris %d): (0, i, w, step_h)."
       % spec.line("band_target"),
       "Rect2", [("int64_t", "i"), ("int64_t", "step_h"),
                 ("int64_t", "screen_w")], """
    return Rect2((double)0, (double)i, (double)screen_w, (double)step_h);""")
    fn("bg_band_color",
       "Warna satu batang gradien (draw baris %d): f = i/h; dua segmen lerp "
       "top->mid (f<%g) lalu mid->bot, kanal di-trunc int() Python."
       % (spec.line("grad_split"), spec["grad_split"]),
       "Color", [("int64_t", "i"), ("int64_t", "screen_h")], tpl("""
    double f = (double)i / (double)screen_h;
    int64_t top[3] = {@TR@};
    int64_t mid[3] = {@MR@};
    int64_t bot[3] = {@BR@};
    double f2;
    const int64_t *from;
    const int64_t *to;
    if (f < @SPLIT@) {
        f2 = f / @SPLIT@;
        from = top;
        to = mid;
    } else {
        f2 = (f - @SPLIT@) / @REST@;
        from = mid;
        to = bot;
    }
    return Color((double)py_int((double)from[0]
                    + ((double)to[0] - (double)from[0]) * f2) / 255.0,
                 (double)py_int((double)from[1]
                    + ((double)to[1] - (double)from[1]) * f2) / 255.0,
                 (double)py_int((double)from[2]
                    + ((double)to[2] - (double)from[2]) * f2) / 255.0);""",
        tr=", ".join(str(v) for v in spec["grad_top"]),
        mr=", ".join(str(v) for v in spec["grad_mid"]),
        br=", ".join(str(v) for v in spec["grad_bot"]),
        split=spec["grad_split"], rest=round(1.0 - spec["grad_split"], 10)))
    fn("bg_bands",
       "SELURUH batang gradien (rect + warna) untuk satu ukuran layar — "
       "dipakai renderer Godot memanggang latar SEKALI (paritas _bg_cache "
       "pygame, draw baris %d)." % spec.line("band_target"),
       "Array", [("int64_t", "screen_w"), ("int64_t", "screen_h")], """
    Array out;
    int64_t step = bg_step_h(screen_h);
    for (int64_t i = 0; i < screen_h; i += step) {
        Dictionary row;
        row["rect"] = bg_band_rect(i, step, screen_w);
        row["color"] = bg_band_color(i, screen_h);
        out.push_back(row);
    }
    return out;""")
    fn("vignette_frames",
       "SELURUH bingkai vignette (draw baris %d): i dari %d turun %d; alpha "
       "= min(255, int(%g*(%d-i))) lalu rect (i, i, w-2i, h-2i). Bingkai "
       "TERAKHIR (i=%d..%d) ber-alpha 255 sehingga interior latar pygame "
       "hitam pekat — perilaku yang dulu hilang di port Godot."
       % (spec.line("vig_start"), spec["vig_start"], abs(spec["vig_step"]),
          spec["vig_slope"], spec["vig_start"],
          2 - spec["vig_step"], 2),
       "Array", [("int64_t", "screen_w"), ("int64_t", "screen_h")], tpl("""
    Array out;
    for (int64_t i = @START@; i > 0; i += @STEP@) {
        int64_t alpha = py_int(@SLOPE@ * (double)(@START@ - i));
        if (alpha > 255) {
            alpha = 255;
        }
        Dictionary row;
        row["rect"] = Rect2((double)i, (double)i,
                            (double)(screen_w - 2 * i),
                            (double)(screen_h - 2 * i));
        row["alpha"] = alpha;
        out.push_back(row);
    }
    return out;""", start=spec["vig_start"], step=spec["vig_step"],
                    slope=spec["vig_slope"]))

    # ── jangkar konten + geometri logo ───────────────────────
    fn("content_center",
       "Jangkar konten (draw baris %d): (w // 2, h // 2)."
       % spec.line("logo_lift"),
       "Vector2", [("int64_t", "screen_w"), ("int64_t", "screen_h")], """
    return Vector2((double)(screen_w / 2), (double)(screen_h / 2));""")
    fn("logo_center_y",
       "Titik tengah logo (draw baris %d): base_y - (%d kalau ada logo)."
       % (spec.line("logo_lift"), spec["logo_lift"]),
       "double", [("double", "base_y"), ("bool", "has_logo")], tpl("""
    return has_logo ? base_y - @LIFT@ : base_y;""",
                                                                    lift=spec["logo_lift"]))
    fn("logo_scale",
       "Skala logo (baris %d): min(%g/w, %g/h, 1.0)."
       % (spec.line("logo_max_w"), spec["logo_max_w"], spec["logo_max_h"]),
       "double", [("int64_t", "img_w"), ("int64_t", "img_h")], tpl("""
    double s = @W@ / (double)img_w;
    double h = @H@ / (double)img_h;
    if (h < s) {
        s = h;
    }
    return s < 1.0 ? s : 1.0;""", w=spec["logo_max_w"], h=spec["logo_max_h"]))
    fn("logo_base_size",
       "Ukuran dasar logo sesudah skala (baris %d): max(1, int(dim*scale))."
       % spec.line("logo_max_w"),
       "Vector2", [("int64_t", "img_w"), ("int64_t", "img_h")], """
    double s = logo_scale(img_w, img_h);
    int64_t w = py_int((double)img_w * s);
    int64_t h = py_int((double)img_h * s);
    return Vector2((double)(w > 1 ? w : 1), (double)(h > 1 ? h : 1));""")
    fn("logo_grow_quant",
       "Kuantisasi tumbuh logo (baris %d): round((%g + %g*grow) * %d) / %d — "
       "round() CPython half-to-even, supaya animasi tumbuh hanya memakai "
       "sedikit ukuran tekstur (cache)."
       % (spec.line("grow_min"), spec["grow_min"], spec["grow_span"],
          spec["grow_quant"], spec["grow_quant"]),
       "double", [("double", "elapsed")], tpl("""
    double grow = elapsed / @TIME@;
    if (grow > 1.0) {
        grow = 1.0;
    }
    double raw = (@MIN@ + @SPAN@ * grow) * @Q@;
    return (double)py_round(raw) / (double)@Q@;""", time=spec["grow_time"],
                                                min=spec["grow_min"], span=spec["grow_span"],
                                                q=spec["grow_quant"]))
    fn("logo_grow_size",
       "Ukuran logo pada kuantisasi tumbuh (baris %d): max(1, int(dim*gq))."
       % spec.line("grow_min"),
       "Vector2", [("const Vector2 &", "base"), ("double", "gq")], """
    int64_t w = py_int((double)base.x * gq);
    int64_t h = py_int((double)base.y * gq);
    return Vector2((double)(w > 1 ? w : 1), (double)(h > 1 ? h : 1));""")
    fn("logo_glow_radius",
       "Radius glow emas di belakang logo (baris %d): max(ww, hh) // 2 + %d."
       % (spec.line("glow_pad"), spec["glow_pad"]),
       "int64_t", [("int64_t", "ww"), ("int64_t", "hh")], tpl("""
    int64_t m = ww > hh ? ww : hh;
    return m / 2 + @PAD@;""", pad=spec["glow_pad"]))
    fn("logo_glow_rect",
       "Rect glow logo (baris %d): persegi 2*glow_r berpusat (cx, cy).",
       "Rect2", [("double", "cx"), ("double", "cy"), ("int64_t", "glow_r")],
       """
    return Rect2(cx - (double)glow_r, cy - (double)glow_r,
                 (double)(glow_r * 2), (double)(glow_r * 2));""")
    fn("logo_glow_rings",
       "Cincin glow logo (baris %d): g dari glow_r turun %d; alpha = "
       "int(%d * (1 - g/glow_r)) — trunc."
       % (spec.line("glow_step"), spec["glow_step"], spec["glow_alpha"]),
       "Array", [("int64_t", "glow_r")], tpl("""
    Array out;
    for (int64_t g = glow_r; g > 0; g += @STEP@) {
        Dictionary row;
        row["r"] = g;
        row["alpha"] = py_int((double)@ALPHA@
                              * (1.0 - (double)g / (double)glow_r));
        out.push_back(row);
    }
    return out;""", step=spec["glow_step"], alpha=spec["glow_alpha"]))
    fn("logo_offsets",
       "Offset vertikal teks cabang logo vs cabang teks-saja (baris %d): "
       "judul rect.bottom+%d, tagline rect.bottom+%d, tagline cabang teks "
       "base_y+%d." % (spec.line("title_below"), spec["title_below"],
                       spec["sub_below"], spec["sub_text_only"]),
       "Dictionary", [], tpl("""
    Dictionary out;
    out["logo_lift"] = (int64_t)@LIFT@;
    out["title_below"] = (int64_t)@TITLE@;
    out["sub_below"] = (int64_t)@SUB@;
    out["sub_text_only"] = (int64_t)@TEXTONLY@;
    return out;""", lift=spec["logo_lift"], title=spec["title_below"],
                     sub=spec["sub_below"], textonly=spec["sub_text_only"]))

    # ── glow judul + garis aksen ─────────────────────────────
    layer_rows = "".join(tpl("""
    Dictionary l@I@;
    l@I@["layer"] = (int64_t)@LAYER@;
    l@I@["spread"] = (int64_t)@SPREAD@;
    out.push_back(l@I@);""", i=i, layer=layer, spread=spread)
        for i, (layer, spread) in enumerate(spec["glow_layers"]))
    fn("title_glow_layers",
       "Lapisan glow judul saat jalur murah (baris %d): [(24,1),(14,2),"
       "(8,3)]; kosong kalau jalur mahal (mobile.perf.Quality.cheap_alpha "
       "False)." % spec.line("glow_layers"),
       "Array", [("bool", "cheap")], """
    Array out;
    if (!cheap) {
        return out;
    }%s
    return out;""" % layer_rows)
    fn("title_glow_surface",
       "Rect permukaan glow judul SESUDAH smoothscale (baris %d): posisi "
       "(rect.x - layer - %d, rect.y - layer - %d), ukuran bertambah "
       "2*layer + 2*spread." % (spec.line("glow_grow"),
                                spec["glow_offset"], spec["glow_offset"]),
       "Rect2", [("const Rect2 &", "text_rect"), ("int64_t", "layer"),
                 ("int64_t", "spread")], tpl("""
    double x = text_rect.position.x - (double)layer - @OFF@;
    double y = text_rect.position.y - (double)layer - @OFF@;
    double w = text_rect.size.x + (double)(layer * 2) + (double)(spread * @GROW@);
    double h = text_rect.size.y + (double)(layer * 2) + (double)(spread * @GROW@);
    return Rect2(x, y, w, h);""", off=spec["glow_offset"],
                                              grow=spec["glow_grow"]))
    fn("title_glow_fill",
       "Alpha isi glow judul (baris %d): int(alpha * %g) — trunc."
       % (spec.line("glow_fill"), spec["glow_fill"]),
       "int64_t", [("double", "alpha")], tpl("""
    return py_int(alpha * @FILL@);""", fill=spec["glow_fill"]))
    fn("accent_gap",
       "Jarak garis aksen dari tengah judul (baris %d): rect.w // 2 + %d."
       % (spec.line("accent_pad"), spec["accent_pad"]),
       "int64_t", [("int64_t", "text_w")], tpl("""
    return text_w / 2 + @PAD@;""", pad=spec["accent_pad"]))
    accent_rows = "".join(tpl("""
    {
        Color col = @COLOR@;
        double fac = (alpha / 255.0) * @FAC@;
        Color lc((double)py_int((double)col.get_r8() * fac) / 255.0,
                 (double)py_int((double)col.get_g8() * fac) / 255.0,
                 (double)py_int((double)col.get_b8() * fac) / 255.0);
        Dictionary row;
        row["off"] = (int64_t)@OFF@;
        row["color"] = lc;
        row["width"] = (int64_t)@WIDTH@;
        row["len"] = (int64_t)@LEN@;
        out.push_back(row);
    }""", color=c8(spec["accent"] if cname == "ACCENT" else spec["accent_2"]),
          off=off, fac=spec["accent_fac"], width=spec["accent_width"],
          len=spec["accent_len"])
        for off, cname in spec["accent_offsets"])
    fn("accent_lines",
       "Spesifikasi garis aksen kiri-kanan judul (baris %d): off -6 emas / "
       "+6 ungu, warna dikalikan (alpha/255)*%g lalu trunc; panjang %d, "
       "lebar %d. Posisi ujung dihitung renderer dari gap = accent_gap()."
       % (spec.line("accent_offsets"), spec["accent_fac"],
          spec["accent_len"], spec["accent_width"]),
       "Array", [("double", "alpha")], """
    Array out;%s
    return out;""" % accent_rows)

    # ── hint ─────────────────────────────────────────────────
    fn("hint_pos",
       "Titik tengah teks hint (draw baris %d): (w // 2, h - %d)."
       % (spec.line("hint_margin"), spec["hint_margin"]),
       "Vector2", [("int64_t", "screen_w"), ("int64_t", "screen_h")], tpl("""
    return Vector2((double)(screen_w / 2),
                   (double)(screen_h - @MARGIN@));""",
                                                                           margin=spec["hint_margin"]))
    fn("hint_alpha",
       "Alpha teks hint (draw baris %d): int(%d * a) — trunc."
       % (spec.line("hint_alpha"), spec["hint_alpha"]),
       "int64_t", [("double", "overall")], tpl("""
    return py_int((double)@A@ * overall);""", a=spec["hint_alpha"]))
    return _FUNCS


CPP_HEAD = '''#include "splash_processor.h"

#include <godot_cpp/core/class_db.hpp>

#include <cmath>

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : splash_screen.py
// Generator : tools/gen_splash_cpp.py
// Regenerasi: python3 tools/gen_splash_cpp.py
// Cek CI    : python3 tools/gen_splash_cpp.py --check
//
// Setiap fungsi menyebut baris sumber Python yang direplikasi. Angka yang
// diekstrak generator datang dari AST (bukan salinan tangan); perilakunya
// dikunci oracle pygame + self-test tanpa engine.

namespace godot {

// Replika round() CPython: half-to-even (round(2.5) == 2, round(-2.5) == -2).
// Dipakai kuantisasi tumbuh logo: round((0.85 + 0.15*grow) * 20) / 20.0.
int64_t MysticSplash::py_round(double value) {
    double floored = std::floor(value);
    double diff = value - floored;
    if (diff > 0.5) {
        return (int64_t)(floored + 1.0);
    }
    if (diff < 0.5) {
        return (int64_t)floored;
    }
    int64_t parity = (int64_t)floored;
    return (parity % 2 == 0) ? parity : parity + 1;
}

// Replika int() CPython: trunc ke arah nol (bukan floor, bukan round).
// Dipakai SEMUA kanal warna/alpha/koordinat splash: int(255 * min(...)),
// int(ch * (0.35 + 0.65*tw)), int(140 * a), int(alpha * 0.28), int(x).
int64_t MysticSplash::py_int(double value) {
    return (int64_t)value;
}

'''

CPP_TAIL = '''
void MysticSplash::_bind_methods() {
%s
}

} // namespace godot
'''


def emit_h(funcs):
    decls = "\n".join(decl for _n, decl in signatures(funcs))
    return """#ifndef MYSTIC_SPLASH_PROCESSOR_H
#define MYSTIC_SPLASH_PROCESSOR_H

// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : splash_screen.py (splashscreen pembuka: logo + judul)
// Generator : tools/gen_splash_cpp.py (AST Python -> C++, bukan terjemahan
//             tangan)
// Regenerasi: python3 tools/gen_splash_cpp.py
// Cek CI    : python3 tools/gen_splash_cpp.py --check
// Desain    : docs/AUDIT_ULANG_DARI_AWAL.md
//
// Port splash_screen.py ke Godot C++ GDExtension: lapisan MODEL (timing +
// fade, alpha judul, gerak/twinkle partikel, gradien + vignette latar,
// geometri logo, glow judul + garis aksen, posisi/alpha hint). Renderer
// piksel (pygame.draw / _draw Godot) tidak diport dan memanggil angka dari
// sini; metrik font diterima sebagai parameter (pola FASE 36).

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/color.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/rect2.hpp>
#include <godot_cpp/variant/string.hpp>
#include <godot_cpp/variant/variant.hpp>
#include <godot_cpp/variant/vector2.hpp>
#include <cstdint>

namespace godot {

class MysticSplash : public RefCounted {
    GDCLASS(MysticSplash, RefCounted);

public:
%s

    // ── helper internal (dipakai fungsi ter-bind; TIDAK di-bind) ──
    static int64_t py_round(double value);
    static int64_t py_int(double value);

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_SPLASH_PROCESSOR_H
""" % decls


def emit_cpp(funcs):
    parts = [CPP_HEAD]
    for name, comment, ret, args, body in funcs:
        cpp_sig = "%s %s::%s(%s) {" % (ret, CLASS, name, arglist(args))
        parts.append("// %s\n%s\n%s\n}\n\n" % (comment, cpp_sig, body))
    binds = "\n".join(
        '    ClassDB::bind_static_method("%s", D_METHOD("%s"%s), &%s::%s);'
        % (CLASS, name, "".join(', "%s"' % a[1] for a in args), CLASS, name)
        for name, _c, _r, args, _b in funcs)
    parts.append(CPP_TAIL % binds)
    return "".join(parts)


# Tipe argumen C++ -> fungsi konverter Variant di harness self-test.
ARG_CONVERT = {
    "int64_t": "to_int",
    "double": "to_double",
    "bool": "to_bool",
    "const String &": "to_string",
    "const Color &": "to_color",
    "const Vector2 &": "to_vector2",
    "const Rect2 &": "to_rect2",
    "const Array &": "to_array",
    "const Dictionary &": "to_dict",
}


def emit_dispatch(funcs):
    """Tabel perintah harness self-test: satu entri per fungsi ter-bind.

    Ditulis generator supaya setiap fungsi baru WAJIB punya perintah — tidak
    ada cabang `if (cmd == ...)` yang bisa lupa diperbarui. Harness
    (splash_selftest.cpp) hanya menyediakan parser Variant + konverter tipe.
    """
    lines = [
        "// ═══ GENERATED — JANGAN SUNTING TANGAN ═══",
        "// Tabel perintah self-test untuk SELURUH API MysticSplash (%d "
        "fungsi)." % len(funcs),
        "// Dibangkitkan tools/gen_splash_cpp.py bersama splash_processor."
        "{h,cpp};",
        "// diperiksa ulang oleh tools/test_splash_cpp_selftest.py "
        "(closed-world:",
        "// jumlah entri == jumlah bind_static_method di _bind_methods).",
        "",
        "// {nama, jumlah argumen, pemanggil}",
    ]
    for name, _comment, ret, args, _body in funcs:
        conv = []
        for i, (atype, _aname) in enumerate(args):
            if atype not in ARG_CONVERT:
                raise SplashError(
                    "%s: tipe argumen belum punya konverter self-test: %s"
                    % (name, atype))
            conv.append("%s(a[%d], e)" % (ARG_CONVERT[atype], i))
        call = "MysticSplash::%s(%s)" % (name, ", ".join(conv))
        lines.append(
            '    {"%s", %d, [](const std::vector<Variant> &a, '
            'std::string &e) -> Variant {' % (name, len(args)))
        lines.append("        (void)a; (void)e;")
        lines.append("        return Variant(%s);" % call)
        lines.append("    }},")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="CI: berkas ter-commit harus identik")
    args = parser.parse_args()

    spec = build_spec()
    funcs = build_functions(spec)
    # api_signature menyebut jumlah fungsi — hitung ulang setelah daftar
    # lengkap (indeks pertama build_functions memuat placeholder 0).
    total = len(funcs)
    funcs = [(name, comment,
              ret.replace("splash_v1:1mod:0fn:", "splash_v1:1mod:%dfn:" % total),
              args,
              body.replace("splash_v1:1mod:0fn:",
                           "splash_v1:1mod:%dfn:" % total))
             for name, comment, ret, args, body in funcs]
    header = emit_h(funcs)
    cpp = emit_cpp(funcs)
    dispatch = emit_dispatch(funcs)

    if args.check:
        ok = True
        for path, expected in ((OUT_H, header), (OUT_CPP, cpp),
                               (OUT_DISPATCH, dispatch)):
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                print("[gen_splash_cpp] BEDA: %s" % path.relative_to(ROOT))
                ok = False
        if not ok:
            print("[gen_splash_cpp] jalankan: python3 "
                  "tools/gen_splash_cpp.py")
            return 1
        print("[gen_splash_cpp] --check OK (%d fungsi)" % len(funcs))
        return 0

    for path in (OUT_H, OUT_CPP, OUT_DISPATCH):
        path.parent.mkdir(parents=True, exist_ok=True)
    OUT_H.write_text(header, encoding="utf-8")
    OUT_CPP.write_text(cpp, encoding="utf-8")
    OUT_DISPATCH.write_text(dispatch, encoding="utf-8")
    print("[gen_splash_cpp] tulis %s" % OUT_H.relative_to(ROOT))
    print("[gen_splash_cpp] tulis %s (%d fungsi)"
          % (OUT_CPP.relative_to(ROOT), len(funcs)))
    print("[gen_splash_cpp] tulis %s" % OUT_DISPATCH.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
