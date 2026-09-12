#!/usr/bin/env python3
"""Oracle paritas map_components/_bundle.py vs backend Godot (FASE 35).

Gerbang statis pra-engine untuk migrasi map -> godot++: membandingkan SUMBER
KEBENARAN (_bundle.py, dibaca sebagai AST + dieksekusi murni-tanpa-pygame)
terhadap TIGA artefak turunan:

  1. godot/data/themes_raw.json   (tools/convert_to_godot.py --map-raw)
  2. godot/scripts/core/MapDB.gd  (backend GDScript; dibaca sebagai TEKS —
     GDScript tidak bisa di-AST dari sini, jadi klaimnya dijangkar ke teks
     sumber + cermin Python yang dieksekusi)
  3. godot/gdext/mystic_maps/src/maps_processor.{h,cpp}
     (tools/gen_maps_cpp.py; cukup --check + jangkar literal — perilaku C++
     sudah dibuktikan tools/test_maps_cpp_selftest.py: 19.834 cek)

Cakupan (gagal = CI merah):
  A. JSON setia: 54 nama + urutan, kunci per tema + urutan, nilai daun.
  B. KEY_KINDS MapDB.gd == skema AST (closed-world: kunci baru = merah).
  C. THEME_KEY_MAP + THEME_DECOR_FLAGS MapDB.gd == konstanta converter.
  D. Waypoint lane/river MapDB.gd == AST (dievaluasi di 2 ukuran, termasuk
     dimensi ganjil) + smoothness [10, 8, 10, 10] + urutan top,mid,bot.
  E. Struktur DecorationGenerator dua-sisi: AST bundle == tabel harapan ==
     teks MapDB.gd (attempts, batas randint, opsi choice, sisi, min_lane,
     while landmark, loop obor, seed 42 di ketiga sisi + akhir re-seed).
  F. Algoritma PyMt (cermin Python dari teks GDScript) se-stream dengan
     random.Random(42): 500 getrandbits + 500 randint + literal wajib ada di
     ketiga sisi.
  G. round_half_even cermin == round() bawaan pada sapuan + domain aktual;
     _round_nd cermin == round(x, 3/4) pada domain aktual.
  H. derive_palette cermin == fungsi converter ASLI (fog + extras) untuk
     SEMUA 54 tema, termasuk URUTAN kunci entry.
  I. gen_maps_cpp.py --check (tabel C++ regenerable dari AST saat ini).
  J. Permukaan API: MapDB.gd <-> MapDBLoader.gd <-> bind C++ konsisten;
     derive_palette/ theme_palette terbukti GDScript-only; literal banner
     satu-baris; setting project.godot.
  K. themes.json segar: cermin derive == berkas repo (independence check
     juga dijalankan ulang di engine test).
  L. Fixture engine godot/tests/fixtures/map_data.json: dibangun dari oracle
     Python (katalog + baterai + lane/river/dekor); byte-identik atau FAIL.
     Regenerasi HANYA bila _bundle.py berubah: --write-fixture.
  M. Wiring closed-world: ArenaMap -> MapDBLoader (tanpa sisa port lama),
     scene engine test + arity _fail, .gdextension, .gitignore, kedua
     workflow merujuk artefak maps.

Keluar 0 = PASS; selain itu FAIL + daftar kegagalan.
"""

import ast
import json
import math
import os
import random
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

import gen_maps_cpp as gen  # noqa: E402
from test_maps_cpp_selftest import load_oracle  # noqa: E402
import convert_to_godot as conv  # noqa: E402 (impor aman: hanya json/os/sys)

FAILURES = []
CHECKS = [0]


def expect(cond, message):
    CHECKS[0] += 1
    if not cond:
        FAILURES.append(message)


def section(title):
    print("── %s ──" % title, flush=True)


BUNDLE_SRC = (ROOT / "map_components" / "_bundle.py").read_text(encoding="utf-8")
MAPDB_SRC = (ROOT / "godot" / "scripts" / "core" / "MapDB.gd").read_text(encoding="utf-8")
LOADER_SRC = (ROOT / "godot" / "scripts" / "core" / "MapDBLoader.gd").read_text(encoding="utf-8")
CPP_SRC = (ROOT / "godot" / "gdext" / "mystic_maps" / "src" / "maps_processor.cpp").read_text(
    encoding="utf-8")


# ══════════════════════════════════════════════════════════
#  A. themes_raw.json setia 1:1 dengan AST
# ══════════════════════════════════════════════════════════

def check_raw_json(palettes, ordered):
    section("A. themes_raw.json setia")
    path = ROOT / "godot" / "data" / "themes_raw.json"
    expect(path.exists(), "A: %s tidak ada — jalankan convert_to_godot.py --map-raw" % path)
    if not path.exists():
        return
    doc = json.loads(path.read_text(encoding="utf-8"))
    expect(doc.get("tile_size") == 16, "A: tile_size=%r, harap 16" % doc.get("tile_size"))
    raw_pal = doc.get("palettes", {})
    for name, rgb, _ in palettes:
        if name == "TILE_SIZE":
            continue
        expect(name in raw_pal, "A: palet %s hilang dari JSON" % name)
        if name in raw_pal:
            got = raw_pal[name]
            expect(isinstance(got, list) and len(got) == 3, "A: palet %s bentuk %r" % (name, got))
            if isinstance(got, list) and len(got) == 3:
                expect([float(c) for c in got] == [float(c) for c in rgb],
                       "A: palet %s=%r, AST=%r" % (name, got, rgb))
    raw_themes = doc.get("themes", {})
    expect(list(raw_themes.keys()) == [key for _c, key, _r in ordered],
           "A: urutan/nama 54 tema JSON != AST")
    for _const, key, row in ordered:
        if key not in raw_themes:
            expect(False, "A: tema %s hilang dari JSON" % key)
            continue
        got = raw_themes[key]
        expect(list(got.keys()) == list(row.keys()),
               "A: %s urutan kunci JSON != AST (json=%d ast=%d)"
               % (key, len(got), len(row)))
        for k, v in row.items():
            if k not in got:
                expect(False, "A: %s.%s hilang dari JSON" % (key, k))
                continue
            g = got[k]
            if v is None:
                expect(g is None, "A: %s.%s=%r, AST None" % (key, k, g))
            elif isinstance(v, bool):
                expect(g is True or g is False, "A: %s.%s=%r bukan bool" % (key, k, g))
                expect(bool(g) == v, "A: %s.%s=%r, AST=%r" % (key, k, g, v))
            elif isinstance(v, int):
                expect(isinstance(g, (int, float)) and not isinstance(g, bool)
                       and float(g) == float(v),
                       "A: %s.%s=%r, AST=%r" % (key, k, g, v))
            elif isinstance(v, str):
                expect(g == v, "A: %s.%s=%r, AST=%r" % (key, k, g, v))
            elif isinstance(v, tuple):
                expect(isinstance(g, list) and len(g) == len(v)
                       and [float(c) for c in g] == [float(c) for c in v],
                       "A: %s.%s=%r, AST=%r" % (key, k, g, v))
            elif isinstance(v, list):
                expect(isinstance(g, list) and len(g) == len(v),
                       "A: %s.%s panjang %r vs %r" % (key, k, g, v))
                if isinstance(g, list) and len(g) == len(v):
                    for i, (ge, ve) in enumerate(zip(g, v)):
                        expect([float(c) for c in ge] == [float(c) for c in ve],
                               "A: %s.%s[%d]=%r, AST=%r" % (key, k, i, ge, ve))
    print("   themes=%d palettes=%d tile=%s" % (
        len(raw_themes), len(raw_pal), doc.get("tile_size")))


# ══════════════════════════════════════════════════════════
#  B. KEY_KINDS == skema AST (closed-world)
# ══════════════════════════════════════════════════════════

def _gd_string_dict(block):
    return dict(re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', block))


def check_key_kinds(ordered):
    section("B. KEY_KINDS closed-world")
    m = re.search(r"const KEY_KINDS := \{(.*?)\n\}", MAPDB_SRC, re.S)
    expect(m is not None, "B: blok KEY_KINDS tidak ketemu di MapDB.gd")
    if m is None:
        return
    kinds = _gd_string_dict(m.group(1))
    _keys, schema = gen.build_schema(ordered)
    expect_schema = {}
    nullable = set()
    for _c, _k, row in ordered:
        for k, v in row.items():
            if v is None:
                nullable.add(k)
    for k, kind in schema.items():
        # Generator MELEBUR None (ambient_tint forest) menjadi color4, tapi
        # GDScript harus tahu null itu legal — "color4?" = color4-atau-null.
        if k in nullable and kind == "color4":
            expect_schema[k] = "color4?"
        else:
            expect_schema[k] = kind
            if k in nullable:
                expect(False, "B: %s nullable tapi kind %s (tak dikenal)" % (k, kind))
    expect(set(kinds) == set(expect_schema),
           "B: kunci KEY_KINDS != union AST (hanya-gd=%s hanya-ast=%s)"
           % (sorted(set(kinds) - set(expect_schema)),
              sorted(set(expect_schema) - set(kinds))))
    for k in sorted(set(kinds) & set(expect_schema)):
        expect(kinds[k] == expect_schema[k],
               "B: %s kind gd=%s ast=%s" % (k, kinds[k], expect_schema[k]))
    print("   keys=%d (nullable=%s)" % (len(kinds), sorted(nullable)))


# ══════════════════════════════════════════════════════════
#  C. KEY_MAP + FLAGS == konstanta converter
# ══════════════════════════════════════════════════════════

def check_key_map():
    section("C. THEME_KEY_MAP + THEME_DECOR_FLAGS")
    m = re.search(r"const THEME_KEY_MAP := \{(.*?)\n\}", MAPDB_SRC, re.S)
    expect(m is not None, "C: THEME_KEY_MAP tidak ketemu di MapDB.gd")
    if m is not None:
        got = _gd_string_dict(m.group(1))
        expect(got == conv.THEME_KEY_MAP,
               "C: THEME_KEY_MAP gd != converter (beda=%s)"
               % [k for k in set(got) | set(conv.THEME_KEY_MAP)
                  if got.get(k) != conv.THEME_KEY_MAP.get(k)][:5])
        expect(list(got.keys()) == list(conv.THEME_KEY_MAP.keys()),
               "C: urutan THEME_KEY_MAP gd != converter")
    m = re.search(r"const THEME_DECOR_FLAGS := \[(.*?)\n\]", MAPDB_SRC, re.S)
    expect(m is not None, "C: THEME_DECOR_FLAGS tidak ketemu di MapDB.gd")
    if m is not None:
        got = re.findall(r'"([^"]+)"', m.group(1))
        expect(got == conv.THEME_DECOR_FLAGS,
               "C: THEME_DECOR_FLAGS gd=%s converter=%s" % (got, conv.THEME_DECOR_FLAGS))
    print("   keymap=%d flags=%d" % (len(conv.THEME_KEY_MAP), len(conv.THEME_DECOR_FLAGS)))


# ══════════════════════════════════════════════════════════
#  D. Waypoint + smoothness + urutan lane
# ══════════════════════════════════════════════════════════

def _gd_waypoints(block):
    return re.findall(r"Vector2\(([^,]+?),([^)]+?)\)", block)


def _ast_paths():
    """Waypoint generate_lanes/generate_river dari AST: [(nama, [(xs, ys)],
    smoothness)] urutan assignment + urutan return + (river_pts, smooth).

    Independen dari gen.parse_paths (dipakai untuk validasi silang)."""
    tree = ast.parse(BUNDLE_SRC)
    ns = [n for n in ast.walk(tree)
          if isinstance(n, ast.ClassDef) and n.name == "_NS_generators"][0]
    pg = [n for n in ns.body
          if isinstance(n, ast.ClassDef) and n.name == "PathGenerator"][0]
    lanes, order, river = [], None, None
    for item in pg.body:
        if not (isinstance(item, ast.FunctionDef)
                and item.name in ("generate_lanes", "generate_river")):
            continue
        for stmt in ast.walk(item):
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                    and isinstance(stmt.targets[0], ast.Name) \
                    and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if len(call.args) != 1 or not isinstance(call.args[0], ast.List):
                    continue
                smooth = [kw.value.value for kw in call.keywords
                          if kw.arg == "smoothness"][0]
                pts = []
                for elt in call.args[0].elts:
                    pts.append((_norm(ast.get_source_segment(BUNDLE_SRC, elt.elts[0])),
                                _norm(ast.get_source_segment(BUNDLE_SRC, elt.elts[1]))))
                lanes.append((stmt.targets[0].id, pts, smooth))
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Tuple):
                order = [e.id for e in stmt.value.elts]
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call) \
                    and item.name == "generate_river":
                call = stmt.value
                smooth = [kw.value.value for kw in call.keywords
                          if kw.arg == "smoothness"][0]
                river = ([(_norm(ast.get_source_segment(BUNDLE_SRC, e.elts[0])),
                             _norm(ast.get_source_segment(BUNDLE_SRC, e.elts[1])))
                            for e in call.args[0].elts], smooth)
    by_name = {n: (p, s) for n, p, s in lanes}
    return [(n, by_name[n][0], by_name[n][1]) for n in order], river


def _expr_norm(expr):
    # Samakan dialek: Python `//` vs GDScript `/` (keduanya trunc di wilayah
    # non-negatif — seluruh koordinat waypoint non-negatif), spasi hilang.
    return _norm(expr).replace("//", "/")


def check_waypoints(pathgen):
    section("D. waypoint + smoothness")
    lanes_ast, river_ast = _ast_paths()
    # Validasi silang terhadap parse generator C++ (kontrak ganda).
    _ns = [n for n in ast.walk(ast.parse(BUNDLE_SRC))
           if isinstance(n, ast.ClassDef) and n.name == "_NS_generators"][0]
    _pg = [n for n in _ns.body
           if isinstance(n, ast.ClassDef) and n.name == "PathGenerator"][0]
    glanes, griver = gen.parse_paths(_pg)
    expect([(n, len(p), s) for n, p, s in lanes_ast]
           == [(n, len(p), s) for n, p, s in glanes],
           "D: parse lokal != gen.parse_paths (lanes)")
    expect(len(river_ast[0]) == len(griver[0]) and river_ast[1] == griver[1],
           "D: parse lokal != gen.parse_paths (river)")
    lan_block = MAPDB_SRC.split("static func generate_lanes")[1].split(
        "static func generate_river")[0]
    riv_block = MAPDB_SRC.split("static func generate_river")[1].split(
        "class PyMt")[0]
    blocks = re.findall(r"PackedVector2Array\(\[(.*?)\]\)", lan_block, re.S)
    expect(len(blocks) == 3, "D: blok lane gd=%d, harap 3" % len(blocks))
    rblocks = re.findall(r"PackedVector2Array\(\[(.*?)\]\)", riv_block, re.S)
    expect(len(rblocks) == 1, "D: blok river gd=%d, harap 1" % len(rblocks))
    # Urutan DEFINISI gd (top,bot,mid) != urutan RETURN ast (top,mid,bot) —
    # pasangkan berdasarkan NAMA var, bukan posisi.
    gd_by_name = dict(re.findall(r"var (\w+) := PackedVector2Array\(\[(.*?)\]\)",
                                 lan_block, re.S))
    expect(set(gd_by_name) == {n for n, _p, _s in lanes_ast},
           "D: nama blok gd=%s ast=%s"
           % (sorted(gd_by_name), [n for n, _p, _s in lanes_ast]))
    if len(blocks) == 3 and len(rblocks) == 1 \
            and set(gd_by_name) == {n for n, _p, _s in lanes_ast}:
        for (name, awp, _s) in lanes_ast:
            blk = gd_by_name[name]
            pts = _gd_waypoints(blk)
            expect(len(pts) == len(awp),
                   "D: %s waypoint gd=%d ast=%d" % (name, len(pts), len(awp)))
            for i, ((xs, ys), (ax, ay)) in enumerate(zip(pts, awp)):
                expect((_expr_norm(xs), _expr_norm(ys)) == (_expr_norm(ax), _expr_norm(ay)),
                       "D: %s[%d] gd=(%s,%s) ast=(%s,%s)"
                       % (name, i, xs.strip(), ys.strip(), ax, ay))
        pts = _gd_waypoints(rblocks[0])
        expect(len(pts) == len(river_ast[0]),
               "D: river waypoint gd=%d ast=%d" % (len(pts), len(river_ast[0])))
        for i, ((xs, ys), (ax, ay)) in enumerate(zip(pts, river_ast[0])):
            expect((_expr_norm(xs), _expr_norm(ys)) == (_expr_norm(ax), _expr_norm(ay)),
                   "D: river[%d] gd=(%s,%s) ast=(%s,%s)"
                   % (i, xs.strip(), ys.strip(), ax, ay))
    print("   lanes=%s river=%d smooth=%s/%d" % (
        [(n, len(p)) for n, p, _s in lanes_ast], len(river_ast[0]),
        [s for _n, _p, s in lanes_ast], river_ast[1]))
    # Smoothness + urutan return GDScript.
    calls = re.findall(r"make_curved_path\((\w+),\s*(\d+)\)", lan_block)
    expect([(n, int(s)) for n, s in calls]
           == [(n, s) for n, _p, s in lanes_ast],
           "D: smoothness lane gd=%s ast=%s"
           % (calls, [(n, s) for n, _p, s in lanes_ast]))
    ret = re.search(r"return \{\s*\"top\":.*?\"mid\":.*?\"bot\":", lan_block, re.S)
    expect(ret is not None, "D: urutan return lane gd != top,mid,bot")
    calls = re.findall(r"make_curved_path\((\w+),\s*(\d+)\)", riv_block)
    expect(calls == [("pts", str(river_ast[1]))],
           "D: smoothness river gd=%s, harap %d" % (calls, river_ast[1]))


# ══════════════════════════════════════════════════════════
#  E. Struktur DecorationGenerator dua-sisi
# ══════════════════════════════════════════════════════════

# Tabel harapan — dibaca DARI bundle saat FASE 35 ditulis, lalu dikunci di
# sini. Setiap edit generate_all di _bundle.py HARUS memperbarui tabel ini +
# MapDB.gd + generator C++ bersamaan (test gagal di KETIGA sisi kalau lupa).
# Dua dialek: AST memakai atribut self.* inline, GDScript memakai lokal
# nx/ny/nx2/ny2 (kesetaraannya diaser terpisah di E2).
EXPECTED_ATTEMPTS = [45, 35, 12, 15, 12, 10, 15, 25, 20, 20, 20, 8]
_W3 = "self.map_w//TILE_SIZE-3"
_H3 = "self.map_h//TILE_SIZE-3"
_W2 = "self.map_w//TILE_SIZE-2"
_H2 = "self.map_h//TILE_SIZE-2"
EXPECTED_XY_AST = [("2", _W3), ("2", _H3), ("2", _W3), ("2", _H3),
                   ("3", _W3), ("3", _H3), ("3", _W3), ("3", _H3),
                   ("3", _W3), ("3", _H3), ("3", _W3), ("3", _H3),
                   ("3", _W3), ("3", _H3), ("3", _W3), ("3", _H3),
                   ("2", _W2), ("2", _H2), ("2", _W2), ("2", _H2),
                   ("3", _W3), ("3", _H3), ("3", _W3), ("3", _H3),
                   ("3", _W3), ("3", _H3)]
EXPECTED_XY_GD = [(a, b.replace("self.map_w//TILE_SIZE-3", "nx")
                   .replace("self.map_h//TILE_SIZE-3", "ny")
                   .replace("self.map_w//TILE_SIZE-2", "nx2")
                   .replace("self.map_h//TILE_SIZE-2", "ny2"))
                  for a, b in EXPECTED_XY_AST]
EXPECTED_SIZE_RANDINT = [("8", "14"), ("6", "12")]
EXPECTED_CHOICE_N = [3, 5, 3, 3, 3, 3, 3, 2, 4, 4]
# Daftar opsi di SUMBER: 11 (jamur punya DUA daftar untuk SATU situs choice
# if/else) — situs choice_idx GDScript tetap 10.
EXPECTED_OPTION_LENS = [3, 5, 3, 3, 3, 3, 3, 3, 2, 4, 4]
EXPECTED_OPTIONS = [
    "[16,20,24]", "[0,0,1,1,2]", "[14,18,22]",
    '["pillar","arch","wall"]', '["skull","rib","skeleton"]',
    "[(140,30,30),(100,20,60),(80,40,80)]",
    "[(60,80,150),(100,60,130),(140,50,100)]",
    "[12,16,20]", "[12,16]",
    "[CRYSTAL_BLUE_L,(150,100,200),(100,200,150),(255,200,100)]",
    "[0,1,2,3]",
]
EXPECTED_MIN_LANE = [50] * 5 + [60] + [50] * 6 + [74]
EXPECTED_SIDE = ["R", "D", "D", "R", "D", "D", "D", "R", "R", "R", "D"]
EXPECTED_CATS = ["dark_trees", "dead_trees", "gravestones", "crystals_blue",
                 "crystals_red", "ancient_ruins", "bones", "mushrooms_dark",
                 "rocks_mossy", "dark_bushes", "glow_flowers", "spike_traps",
                 "torch_stones", "boss_landmarks"]


def _gen_all_fn():
    tree = ast.parse(BUNDLE_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "generate_all":
            # generate_all DecorationGenerator (bukan DynamicRenderer).
            src = ast.get_source_segment(BUNDLE_SRC, node)
            if "boss_landmarks" in src and "torch_stones" in src:
                return node, src
    raise AssertionError("E: generate_all dekor tidak ketemu")


def _norm(seg):
    return re.sub(r"\s+", "", seg)


def _ordered_calls(fn, attr):
    out = []
    for node in sorted(ast.walk(fn), key=lambda n: getattr(n, "lineno", 0)):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == attr:
            out.append(node)
    return out


def check_decor_ast():
    section("E1. struktur AST bundle == tabel")
    fn, src = _gen_all_fn()
    fors = [n for n in fn.body if isinstance(n, ast.For)]
    attempts = []
    for f in fors:
        it = f.iter
        if isinstance(it, ast.Call) and getattr(it.func, "id", "") == "range":
            args = [ast.get_source_segment(BUNDLE_SRC, a) for a in it.args]
            attempts.append(_norm(",".join(args)))
    range_fors = [a for a in attempts if re.fullmatch(r"\d+", a)]
    torch_fors = [a for a in attempts if not re.fullmatch(r"\d+", a)]
    expect([int(a) for a in range_fors] == EXPECTED_ATTEMPTS,
           "E1: attempts AST=%s harap=%s" % (range_fors, EXPECTED_ATTEMPTS))
    expect(torch_fors == ["120,self.map_w-80,200", "120,self.map_h-80,200"],
           "E1: loop obor AST=%s" % (torch_fors,))
    # randint(x, y) + crystal sizes, urutan sumber.
    rands = [tuple(_norm(ast.get_source_segment(BUNDLE_SRC, a)) for a in c.args)
             for c in _ordered_calls(fn, "randint")]
    xy = [(a, b) for a, b in rands if "TILE_SIZE" in b]
    sizes = [(a, b) for a, b in rands if "TILE_SIZE" not in b]
    expect(xy == EXPECTED_XY_AST, "E1: randint xy AST=%s" % (xy,))
    expect(sizes == EXPECTED_SIZE_RANDINT, "E1: randint ukuran AST=%s" % (sizes,))
    # Opsi choice: arg List dari tiap random.choice, urutan sumber.
    opts = []
    for c in _ordered_calls(fn, "choice"):
        expect(len(c.args) == 1 and isinstance(c.args[0], ast.List),
               "E1: choice non-list di baris %d" % getattr(c, "lineno", 0))
        if len(c.args) == 1 and isinstance(c.args[0], ast.List):
            opts.append(_norm(ast.get_source_segment(BUNDLE_SRC, c.args[0]))
                        .replace("'", '"'))
    expect(opts == EXPECTED_OPTIONS, "E1: opsi AST=%s" % (opts,))
    expect([(4 if "CRYSTAL" in o else len(ast.literal_eval(o)))
                for o in opts] == EXPECTED_OPTION_LENS,
           "E1: panjang opsi != %s" % (EXPECTED_OPTION_LENS,))
    # min_lane: keyword per panggilan, default dari signature _is_valid.
    tree = ast.parse(BUNDLE_SRC)
    dec = [n for n in ast.walk(tree)
           if isinstance(n, ast.ClassDef) and n.name == "DecorationGenerator"][0]
    valid = [n for n in dec.body
             if isinstance(n, ast.FunctionDef) and n.name == "_is_valid"][0]
    default_min = valid.args.defaults[-1].value
    expect(default_min == 50, "E1: default min_lane=%r, harap 50" % default_min)
    mins = []
    for c in _ordered_calls(fn, "_is_valid"):
        kw = [k.value.value for k in c.keywords if k.arg == "min_lane"]
        mins.append(kw[0] if kw else default_min)
    expect(mins == EXPECTED_MIN_LANE, "E1: min_lane AST=%s" % (mins,))
    # Sisi radiant/dire, urutan sumber.
    sides = []
    for node in sorted(ast.walk(fn), key=lambda n: getattr(n, "lineno", 0)):
        if isinstance(node, ast.Call):
            fnname = getattr(node.func, "attr", "") or getattr(node.func, "id", "")
            if fnname == "_is_radiant":
                sides.append("R")
            elif fnname == "_is_dire":
                sides.append("D")
    expect(sides == EXPECTED_SIDE, "E1: sisi AST=%s" % (sides,))
    # while landmark: len(data[...])<30 AND attempts<240 sebaris.
    whiles = [n for n in fn.body if isinstance(n, ast.While)]
    expect(len(whiles) == 1, "E1: while=%d, harap 1" % len(whiles))
    if whiles:
        w = whiles[0]
        test = _norm(ast.get_source_segment(BUNDLE_SRC, w.test)).replace("'", '"')
        expect(test == 'len(data["boss_landmarks"])<30andlandmark_attempts<240',
               "E1: while test=%s" % test)
        wsrc = _norm(ast.get_source_segment(BUNDLE_SRC, w))
        expect("landmark_attempts+=1" in wsrc, "E1: increment hilang")
    # Urutan kunci dict data.
    m = re.search(r"data = \{(.*?)\n            \}", src, re.S)
    expect(m is not None, "E1: literal data tidak ketemu")
    if m:
        cats = re.findall(r"'(\w+)': \[\]", m.group(1))
        expect(cats == EXPECTED_CATS, "E1: kategori AST=%s" % (cats,))
    # Seed: random.seed(42) di generate_all + random.seed() penutup.
    expect("random.seed(42)" in _norm(src), "E1: random.seed(42) hilang")
    expect(re.search(r"random\.seed\(\)", src) is not None,
           "E1: random.seed() penutup hilang")
    print("   attempts=%s choice=%d sides=%s" % (
        EXPECTED_ATTEMPTS, len(opts), "".join(EXPECTED_SIDE)))


def check_decor_gd(palettes):
    section("E2. teks MapDB.gd == tabel")
    gd = MAPDB_SRC.split("static func generate_decorations")[1].split(
        "static func derive_palette")[0]
    pal = {n: (tuple(v) if isinstance(v, tuple) else v)
           for n, v, _ in palettes}
    expect(pal.get("CRYSTAL_BLUE_L") == (100, 170, 240),
           "E2: CRYSTAL_BLUE_L AST=%r" % (pal.get("CRYSTAL_BLUE_L"),))
    m = re.search(r"var cols := \[Color8\((\d+),\s*(\d+),\s*(\d+)\)", gd)
    expect(m is not None and (int(m.group(1)), int(m.group(2)), int(m.group(3)))
           == pal.get("CRYSTAL_BLUE_L"),
           "E2: literal inline cols[0] != CRYSTAL_BLUE_L AST")
    # Lokal nx/ny/nx2/ny2 = map_w//TILE_SIZE-3/-2 (ts == TILE_SIZE, diaser di A).
    for var, expr in (("nx", "map_w/ts-3"), ("nx2", "map_w/ts-2"),
                      ("ny", "map_h/ts-3"), ("ny2", "map_h/ts-2")):
        m = re.search(r"var %s := (.*?)\n" % var, gd)
        expect(m is not None and _norm(m.group(1)) == expr,
               "E2: %s=%s, harap %s"
               % (var, m.group(1).strip() if m else None, expr))
    expect("var ts := tile_size()" in gd, "E2: ts=tile_size() hilang")
    attempts = [int(n) for n in re.findall(r"for _attempt in range\((\d+)\)", gd)]
    expect(attempts == EXPECTED_ATTEMPTS, "E2: attempts gd=%s" % (attempts,))
    rands = re.findall(r"rng\.randint\(([^,]+?),\s*([^)]+?)\)", gd)
    rands = [(a.strip(), b.strip()) for a, b in rands]
    xy = [(a, b) for a, b in rands if b in ("nx", "ny", "nx2", "ny2")]
    sizes = [(a, b) for a, b in rands if b not in ("nx", "ny", "nx2", "ny2")]
    expect(xy == EXPECTED_XY_GD, "E2: randint xy gd=%s" % (xy,))
    expect(sizes == EXPECTED_SIZE_RANDINT, "E2: randint ukuran gd=%s" % (sizes,))
    ns = [int(n) for n in re.findall(r"rng\.choice_idx\((\d+)\)", gd)]
    expect(ns == EXPECTED_CHOICE_N, "E2: choice gd=%s" % (ns,))
    # Opsi: `var <opsi> := [...]` — Color8(a,b,c)->(a,b,c), spasi hilang.
    opts = []
    for m in re.finditer(
            r"var (sizes|variants|types|dire|radiant|cols) := \[([^\]]*)\]", gd):
        o = re.sub(r"Color8\(([^)]+)\)", lambda t: "(%s)" % t.group(1), m.group(2))
        o = re.sub(r"\s+", "", o).replace("'", '"')
        # CRYSTAL_BLUE_L di-inline sebagai literal di GDScript.
        o = o.replace("(100,170,240)", "CRYSTAL_BLUE_L", 1) \
            if m.group(1) == "cols" else o
        opts.append("[%s]" % o)
    expect(opts == EXPECTED_OPTIONS, "E2: opsi gd=%s" % (opts,))
    mins = [float(n) for n in re.findall(r"_is_valid_spot\(.*?,\s*([\d.]+)\)", gd)]
    expect(mins == [float(v) for v in EXPECTED_MIN_LANE],
           "E2: min_lane gd=%s" % (mins,))
    sides = ["R" if "radiant" in m else "D"
             for m in re.findall(r"_is_(?:radiant|dire)\(", gd)]
    expect(sides == EXPECTED_SIDE, "E2: sisi gd=%s" % (sides,))
    w = re.search(r"while (.*?):", gd)
    expect(w is not None and _norm(w.group(1))
           == "boss_landmarks.size()<30andlandmark_attempts<240",
           "E2: while gd=%s" % (w.group(1) if w else None))
    torch = re.findall(r"for [xy] in range\((.*?)\)", gd)
    expect([_norm(t) for t in torch] == ["120,map_w-80,200", "120,map_h-80,200"],
           "E2: loop obor gd=%s" % (torch,))
    apps = re.findall(r"torch_stones\.append\(\[(.*?)\]\)", gd)
    expect([_norm(a) for a in apps]
           == ["x,32", "x,map_h-32", "32,y", "map_w-32,y"],
           "E2: append obor gd=%s" % (apps,))
    cats = re.findall(r'^\s*"(\w+)": \w+,?\s*$', gd, re.M)
    expect(cats == EXPECTED_CATS, "E2: kategori gd=%s" % (cats,))
    expect("rng.seed_int(42)" in gd, "E2: seed_int(42) hilang")
    expect("seed_int(42)" in CPP_SRC, "E2: seed C++ hilang")
    print("   attempts=%s choice=%s" % (attempts, ns))


def check_validators():
    section("E3. validator + ambang")
    tree = ast.parse(BUNDLE_SRC)
    dec = [n for n in ast.walk(tree)
           if isinstance(n, ast.ClassDef) and n.name == "DecorationGenerator"][0]
    fns = {n.name: _norm(ast.get_source_segment(BUNDLE_SRC, n))
           for n in dec.body if isinstance(n, ast.FunctionDef)}
    # _is_valid: river 25 eksplisit, base/shop tanpa arg (default).
    expect("self._too_close_to_river(x,y,25)" in fns["_is_valid"],
           "E3: _is_valid tidak memanggil river(25)")
    expect("self._too_close_to_base(x,y)" in fns["_is_valid"],
           "E3: _is_valid tidak memanggil base()")
    expect("self._too_close_to_shop(x,y)" in fns["_is_valid"],
           "E3: _is_valid tidak memanggil shop()")
    expect("min_dist=70" in fns["_too_close_to_shop"],
           "E3: default shop != 70")
    # Bug base direplika: lingkaran-1 berpusat (120,120).
    expect("self.map_h-120-(self.map_h-y))<120" in fns["_too_close_to_base"],
           "E3: bug base lingkaran-1 berubah")
    expect("x-(self.map_w-120),y-120)<120" in fns["_too_close_to_base"],
           "E3: base lingkaran-2 berubah")
    # Ambang sisi: 200 + (map_h-400)*x/map_w, ±20.
    for name, op in (("_is_radiant", "+20"), ("_is_dire", "-20")):
        expect("200+(self.map_h-400)*x/self.map_w" in fns[name],
               "E3: %s threshold berubah" % name)
        expect(op in fns[name].split("return")[1], "E3: %s %s hilang" % (name, op))
    # Sisi GDScript: literal yang sama.
    gd = MAPDB_SRC
    expect("200.0+float((map_h-400)*x)/float(map_w)" in _norm(gd),
           "E3: gd threshold berubah")
    expect("threshold_y(x,map_w,map_h)+20.0" in _norm(gd), "E3: gd +20 hilang")
    expect("threshold_y(x,map_w,map_h)-20.0" in _norm(gd), "E3: gd -20 hilang")
    expect("_too_close_to_river(river_points,x,y,25.0)" in _norm(gd),
           "E3: gd river 25 hilang")
    expect("_too_close_to_shop(shop_positions,x,y,70.0)" in _norm(gd),
           "E3: gd shop 70 hilang")
    expect("float(map_h-120-(map_h-y)),0.0,0.0)<120.0" in _norm(gd),
           "E3: gd bug base hilang")
    expect("float(x-(map_w-120)),float(y-120),0.0,0.0)<120.0" in _norm(gd),
           "E3: gd base-2 hilang")
    print("   river=25 shop=70 base=120x2 threshold=200+-20")


# ══════════════════════════════════════════════════════════
#  F. Algoritma PyMt se-stream dengan CPython
# ══════════════════════════════════════════════════════════

class MirrorMt:
    """Transkripsi Python dari kelas PyMt MapDB.gd — op-per-op sama."""

    N, M = 624, 397
    MATRIX_A, UPPER_MASK, LOWER_MASK, MASK_32 = (
        0x9908b0df, 0x80000000, 0x7fffffff, 0xFFFFFFFF)

    def __init__(self):
        self.mt = [0] * self.N
        self.mti = 0

    def init_genrand(self, s):
        self.mt[0] = s & self.MASK_32
        self.mti = 1
        while self.mti < self.N:
            self.mt[self.mti] = (1812433253 * (
                self.mt[self.mti - 1] ^ (self.mt[self.mti - 1] >> 30))
                + self.mti) & self.MASK_32
            self.mti += 1

    def init_by_array(self, init_key, key_length):
        self.init_genrand(19650218)
        i, j = 1, 0
        k = self.N if self.N > key_length else key_length
        while k > 0:
            # (mt[i] ^ suku) + key + j — kurung luar WAJIB (`^` < `+`).
            self.mt[i] = ((self.mt[i] ^ (
                (self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) * 1664525))
                + init_key[j] + j) & self.MASK_32
            i += 1
            j += 1
            if i >= self.N:
                self.mt[0] = self.mt[self.N - 1]
                i = 1
            if j >= key_length:
                j = 0
            k -= 1
        k = self.N - 1
        while k > 0:
            # (mt[i] ^ suku) - i — kurung luar WAJIB (`^` < `-`).
            self.mt[i] = ((self.mt[i] ^ (
                (self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) * 1566083941))
                - i) & self.MASK_32
            i += 1
            if i >= self.N:
                self.mt[0] = self.mt[self.N - 1]
                i = 1
            k -= 1
        self.mt[0] = 0x80000000

    def seed_int(self, n):
        self.init_by_array([n & self.MASK_32], 1)

    def genrand_int32(self):
        if self.mti >= self.N:
            kk = 0
            while kk < self.N - self.M:
                y = (self.mt[kk] & self.UPPER_MASK) | (
                    self.mt[kk + 1] & self.LOWER_MASK)
                self.mt[kk] = self.mt[kk + self.M] ^ (y >> 1) ^ (
                    0 if y % 2 == 0 else self.MATRIX_A)
                kk += 1
            while kk < self.N - 1:
                y = (self.mt[kk] & self.UPPER_MASK) | (
                    self.mt[kk + 1] & self.LOWER_MASK)
                self.mt[kk] = self.mt[kk + (self.M - self.N)] ^ (
                    y >> 1) ^ (0 if y % 2 == 0 else self.MATRIX_A)
                kk += 1
            y = (self.mt[self.N - 1] & self.UPPER_MASK) | (
                self.mt[0] & self.LOWER_MASK)
            self.mt[self.N - 1] = self.mt[self.M - 1] ^ (y >> 1) ^ (
                0 if y % 2 == 0 else self.MATRIX_A)
            self.mti = 0
        y = self.mt[self.mti]
        self.mti += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= y >> 18
        return y & self.MASK_32

    def getrandbits(self, k):
        words = (k + 31) // 32
        r = 0
        for _i in range(words):
            r = (r << 32) | self.genrand_int32()
        r >>= words * 32 - k
        return r

    def randbelow(self, n):
        k = n.bit_length()
        r = self.getrandbits(k)
        while r >= n:
            r = self.getrandbits(k)
        return r

    def randint(self, a, b):
        return a + self.randbelow(b - a + 1)


MT_LITERALS = ["624", "397", "0x9908b0df", "0x80000000", "0x7fffffff",
               "0xFFFFFFFF", "1812433253", "19650218", "1664525",
               "1566083941", "0x9d2c5680", "0xefc60000"]


def check_mt():
    section("F. stream MT19937 + literal")
    for lit in MT_LITERALS:
        expect(lit in MAPDB_SRC, "F: literal %s hilang dari MapDB.gd" % lit)
        # C++ memakai huruf kecil + sufiks UL (0xffffffffUL) — samakan huruf.
        expect(lit.lower() in CPP_SRC.lower(),
               "F: literal %s hilang dari maps_processor.cpp" % lit)
    ref = random.Random(42)
    mir = MirrorMt()
    mir.seed_int(42)
    expect(mir.genrand_int32() == ref.getrandbits(32) == 2746317213,
           "F: draw pertama != 2746317213 (init_by_array?)")
    bad = 0
    for _i in range(499):
        if mir.genrand_int32() != ref.getrandbits(32):
            bad += 1
    expect(bad == 0, "F: %d/499 draw getrandbits meleset" % bad)
    ref = random.Random(42)
    mir = MirrorMt()
    mir.seed_int(42)
    bad = 0
    for i in range(500):
        a = 2 + (i % 5)
        b = a + 10 + (i % 70)
        if mir.randint(a, b) != ref.randint(a, b):
            bad += 1
    expect(bad == 0, "F: %d/500 randint meleset" % bad)
    # choice_idx == _randbelow(len): sampling tanpa replacement konsisten.
    ref = random.Random(42)
    mir = MirrorMt()
    mir.seed_int(42)
    opts = ["pillar", "arch", "wall"]
    bad = sum(1 for _i in range(200)
              if opts[mir.randbelow(len(opts))] != ref.choice(opts))
    expect(bad == 0, "F: %d/200 choice meleset" % bad)
    print("   draw0=2746317213 getrandbits=500 randint=500 choice=200")


# ══════════════════════════════════════════════════════════
#  G. round_half_even + _round_nd cermin
# ══════════════════════════════════════════════════════════

def m_round_half_even(x):
    f = math.floor(x)
    d = x - f
    if d < 0.5:
        return f
    if d > 0.5:
        return f + 1.0
    return f if int(f) % 2 == 0 else f + 1.0


def m_round_nd(x, nd):
    """Transkripsi MapDB._round_nd (limb IEEE-754 eksak).

    struct.pack/unpack = pasangan encode_double/decode_u64 GDScript;
    statement lainnya op-per-op sama (int Python tak terbatas, tapi seluruh
    nilai intermediate < 2^46 — muat int64 GDScript, diaser di bawah).
    """
    scale = 10 ** nd
    if x <= 0.0 or x >= 2.0:
        m = float(scale)
        return m_round_half_even(x * m) / m
    bits = struct.unpack("<Q", struct.pack("<d", x))[0]
    mant = bits & 0xFFFFFFFFFFFFF
    exp = (bits >> 52) & 0x7FF
    if exp == 0:
        m, e = mant, -1074
    else:
        m, e = mant | 0x10000000000000, exp - 1075
    s = -e
    if s < 32 or s > 60:
        mf = float(scale)
        return m_round_half_even(x * mf) / mf
    hi = m >> 32
    lo = m & 0xFFFFFFFF
    lo_s = lo * scale
    hi_p = hi * scale + (lo_s >> 32)
    assert hi * scale < 2**36 and lo_s < 2**46 and hi_p < 2**36, \
        "limb meluap int64"
    lo_p = lo_s & 0xFFFFFFFF
    k = s - 32
    q = hi_p >> k
    t = 1 << (k - 1)
    alo = hi_p & ((1 << k) - 1)
    up = False
    if alo < t:
        up = False
    elif alo > t:
        up = True
    elif lo_p != 0 or (q & 1) != 0:
        up = True
    if up:
        q += 1
    return float(q) / float(scale)


def check_rounding(ordered):
    section("G. bankir cermin == round()")
    bad = 0
    total = 0
    for i in range(0, 300):
        for f in (0.0, 0.25, 0.5, 0.75, 0.499999999, 0.500000001):
            x = i + f
            total += 1
            if m_round_half_even(x) != float(round(x)):
                bad += 1
    # Kasus .5 AKTUAL dari derivasi (desimal News — dihitung di H).
    expect(bad == 0, "G: %d/%d round_half_even != round()" % (bad, total))
    # Domain aktual: kumpulkan semua input pembulatan dari converter.
    alphas, energies, mixes = set(), set(), set()
    for _c, _k, row in ordered:
        fog = row.get("fog_color", (80, 60, 60, 30))
        a = fog[3] if isinstance(fog, (tuple, list)) and len(fog) > 3 else 30
        alphas.add(float(a) / 255.0)
        g3, g4 = row["radiant_grass_3"], row["radiant_grass_4"]
        lum = max(conv._lum(g3), conv._lum(g4))
        energies.add(max(0.55, min(1.25, 0.55 + 0.75 * lum)))
        for ch in row["radiant_grass_1"][:3]:
            v = float(ch)
            mixes.add(v * (1.0 + -0.10))
        for ch in row["path_stone_2"][:3]:
            v = float(ch)
            mixes.add(v + (255.0 - v) * 0.08)
        samples = [row["radiant_grass_3"], row["radiant_grass_4"],
                   row["dire_earth_3"], row["path_stone_3"], row["river_glow"]]
        avg = [sum(s[i] for s in samples) / 5.0 for i in range(3)]
        peak = max(1.0, float(max(avg)))
        for v in avg:
            mixes.add((1.0 - (1.0 - v / peak) * 0.45) * 255.0)
        tint = row.get("ambient_tint")
        if isinstance(tint, (tuple, list)) and len(tint) >= 4:
            aa = min(0.35, (float(tint[3]) / 255.0) * 3.0)
            for i in range(3):
                mixes.add(255.0 - (255.0 - float(tint[i])) * aa)
    bad = sum(1 for x in alphas if m_round_nd(x, 4) != round(x, 4))
    expect(bad == 0, "G: %d/%d fog_alpha _round_nd != round(x,4)" % (bad, len(alphas)))
    bad = sum(1 for x in energies if m_round_nd(x, 3) != round(x, 3))
    expect(bad == 0, "G: %d/%d energy _round_nd != round(x,3)" % (bad, len(energies)))
    bad = sum(1 for x in mixes if m_round_half_even(x) != float(round(x)))
    expect(bad == 0, "G: %d/%d mix-channel != round()" % (bad, len(mixes)))
    # Kasus di mana bankir BENAR-BENAR penting (round() != half-away):
    halves = sum(1 for x in mixes
                 if float(round(x)) != math.floor(x + 0.5))
    # Bukti sapuan: algoritme limb eksak == round() untuk 20.000 nilai acak
    # (seed tetap) di seluruh domain + tetangga batas desimal. Kalau
    # implementasi GDScript menyimpang, engine test (royal.energy=1.169)
    # menangkapnya — royal memang kasus batas yang ditemukan oracle ini.
    rng = random.Random(20260912)
    sweep_bad = 0
    sweep_n = 0
    for nd in (3, 4):
        for _i in range(10000):
            x = rng.uniform(0.05, 1.3)
            sweep_n += 1
            if m_round_nd(x, nd) != round(x, nd):
                sweep_bad += 1
                if sweep_bad < 4:
                    FAILURES.append("G: sapuan x=%.17g nd=%d cermin=%r round=%r"
                                    % (x, nd, m_round_nd(x, nd), round(x, nd)))
        for base in range(50, 1300):
            x = base / 1000.0
            for dx in (-2e-13, -1e-16, 0.0, 1e-16, 2e-13):
                sweep_n += 1
                if m_round_nd(x + dx, nd) != round(x + dx, nd):
                    sweep_bad += 1
    expect(sweep_bad == 0, "G: %d/%d sapuan _round_nd != round()" % (sweep_bad, sweep_n))
    print("   sweep=%d fog=%d energy=%d mix=%d (bankir-penting: %d, sapuan=%d)"
          % (total, len(alphas), len(energies), len(mixes), halves, sweep_n))


# ══════════════════════════════════════════════════════════
#  H. derive_palette cermin == converter asli (54 tema)
# ══════════════════════════════════════════════════════════

def _hex3(rgb):
    return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])


def m_mix_chan(ch, amount):
    v = float(ch)
    if amount >= 0.0:
        v = v + (255.0 - v) * amount
    else:
        v = v * (1.0 + amount)
    return int(m_round_half_even(max(0.0, min(255.0, v))))


def m_lum(rgb):
    return (0.299 * float(rgb[0]) + 0.587 * float(rgb[1])
            + 0.114 * float(rgb[2])) / 255.0


def m_derive(theme_key, raw):
    """Transkripsi Python dari MapDB.derive_palette — Color jadi tuple,
    urutan statement sama, hex di-render seperti _hex."""
    out = {}
    out["name"] = str(raw.get("name", theme_key))
    for src, dst in conv.THEME_KEY_MAP.items():
        col = raw.get(src, (255, 0, 255))
        out[dst] = _hex3(col)
    for flag in conv.THEME_DECOR_FLAGS:
        out[flag] = bool(raw.get(flag, False))
    out["particle_type"] = str(raw.get("particle_type", "ash"))
    out["particle_count"] = int(raw.get("particle_count", 40))
    fog = raw.get("fog_color", (80, 60, 60, 30))
    if not (isinstance(fog, (tuple, list)) and len(fog) >= 3):
        fog = (80, 60, 60, 30)
    out["fog_enabled"] = bool(raw.get("fog_enabled", True))
    out["fog_color"] = _hex3(fog)
    out["fog_alpha"] = m_round_nd(float(fog[3]) / 255.0, 4)
    out["fog_count"] = int(raw.get("fog_count", 15))
    grass1 = raw.get("radiant_grass_1", (255, 0, 255))
    out["tree"] = _hex3(tuple(m_mix_chan(c, -0.10) for c in grass1[:3]))
    out["tree_light"] = _hex3(raw.get("radiant_moss", (255, 0, 255)))
    out["stone"] = _hex3(tuple(
        m_mix_chan(c, 0.08) for c in raw.get("path_stone_2", (255, 0, 255))[:3]))
    samples = [raw.get("radiant_grass_3", (0, 0, 0)),
               raw.get("radiant_grass_4", (0, 0, 0)),
               raw.get("dire_earth_3", (0, 0, 0)),
               raw.get("path_stone_3", (0, 0, 0)),
               raw.get("river_glow", (0, 0, 0))]
    avg = [sum(s[i] for s in samples) / 5.0 for i in range(3)]
    peak = max(1.0, max(avg))
    light = []
    for i in range(3):
        norm = avg[i] / peak
        lv = 1.0 - (1.0 - norm) * 0.45
        light.append(int(m_round_half_even(max(0.0, min(255.0, lv * 255.0)))))
    out["light"] = _hex3(light)
    g3 = raw.get("radiant_grass_3", (0, 0, 0))
    g4 = raw.get("radiant_grass_4", (0, 0, 0))
    bright = max(m_lum(g3), m_lum(g4))
    out["energy"] = m_round_nd(max(0.55, min(1.25, 0.55 + 0.75 * bright)), 3)
    tint = raw.get("ambient_tint")
    mod = [255, 255, 255]
    if isinstance(tint, (tuple, list)) and len(tint) >= 4:
        a = min(0.35, float(tint[3]) / 255.0 * 3.0)
        mod = [int(m_round_half_even(255.0 - (255.0 - float(tint[i])) * a))
               for i in range(3)]
    out["modulate"] = _hex3(mod)
    return out


def check_derive(ordered):
    section("H. derive cermin == converter (54 tema)")
    n_leaf = 0
    for _const, key, row in ordered:
        exp = {"name": str(row.get("name", key))}
        for src, dst in conv.THEME_KEY_MAP.items():
            exp[dst] = conv._hex(row[src], "#345c37") if src in row else None
            if src not in row:
                expect(False, "H: %s kehilangan %s" % (key, src))
        for flag in conv.THEME_DECOR_FLAGS:
            exp[flag] = bool(row.get(flag, False))
        exp["particle_type"] = str(row.get("particle_type", "ash"))
        exp["particle_count"] = int(row.get("particle_count", 40))
        conv._fog_from_theme(row, exp)
        conv._derive_theme_extras(row, exp)
        got = m_derive(key, row)
        expect(list(got.keys()) == list(exp.keys()),
               "H: %s urutan kunci derive != converter" % key)
        for k in exp:
            n_leaf += 1
            e, g = exp[k], got.get(k, "<hilang>")
            if isinstance(e, float):
                expect(isinstance(g, float) and g == e,
                       "H: %s.%s=%r, converter=%r" % (key, k, g, e))
            else:
                expect(g == e, "H: %s.%s=%r, converter=%r" % (key, k, g, e))
    print("   tema=54 daun=%d" % n_leaf)


# ══════════════════════════════════════════════════════════
#  I. gen_maps_cpp.py --check
# ══════════════════════════════════════════════════════════

def check_gen():
    section("I. gen_maps_cpp --check")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_maps_cpp.py"),
                        "--check"], capture_output=True, text=True, cwd=str(ROOT))
    expect(r.returncode == 0,
           "I: gen_maps_cpp.py --check rc=%d: %s" % (r.returncode, r.stderr[-500:]))
    print("   rc=%d" % r.returncode)


# ══════════════════════════════════════════════════════════
#  J. Permukaan API tiga sisi
# ══════════════════════════════════════════════════════════

EXPECTED_API = ["reload", "tile_size", "palettes", "theme_names",
                "theme_count", "build_theme", "theme_index", "get_theme",
                "all_themes", "catalog_signature", "make_curved_path",
                "generate_lanes", "generate_river", "generate_decorations",
                "round_half_even", "derive_palette"]
# round_half_even = helper internal (dipakai derive_palette saja).
# reload/derive_palette/theme_palette = GDScript-only (C++ tidak punya cache
# JSON; derivasi palet satu implementasi backend-agnostik) — loader TIDAK
# BOLEH memanggil _gdext_ready untuknya.
LOADER_SKIPS = ["round_half_even"]
GDSCRIPT_ONLY = ["derive_palette", "theme_palette", "reload"]
EXPECTED_BINDS = ["tile_size", "palettes", "theme_names", "theme_count",
                  "get_theme", "all_themes", "catalog_signature",
                  "make_curved_path", "generate_lanes", "generate_river",
                  "generate_decorations", "build_theme", "theme_index"]


def _loader_body(name):
    parts = LOADER_SRC.split("static func %s(" % name)
    if len(parts) < 2:
        return None
    return parts[1].split("\nstatic func ")[0]


def check_api():
    section("J. permukaan API")
    gd_pub = [n for n in re.findall(r"^static func (\w+)\(", MAPDB_SRC, re.M)
              if not n.startswith("_")]
    expect(gd_pub == EXPECTED_API, "J: API MapDB.gd=%s" % (gd_pub,))
    for name in EXPECTED_API + ["theme_palette"]:
        if name in LOADER_SKIPS:
            expect(_loader_body(name) is None,
                   "J: loader.%s tak terduga (helper internal)" % name)
            continue
        expect(_loader_body(name) is not None,
               "J: loader tidak membungkus %s" % name)
    binds = re.findall(r'bind_static_method\("MysticMaps", D_METHOD\("(\w+)"',
                       CPP_SRC)
    expect(binds == EXPECTED_BINDS, "J: bind C++=%s" % (binds,))
    for name in GDSCRIPT_ONLY:
        body = _loader_body(name)
        # theme_palette mendelegasikan ke loader.derive_palette (tanpa prefix
        # MapDBGD — pemanggilan static seberkas), dua lainnya ke MapDBGD.
        ok_via = "derive_palette" if name == "theme_palette" else "MapDBGD"
        expect(body is not None and "_gdext_ready" not in body
               and ok_via in body,
               "J: loader.%s harus GDScript-only" % name)
    for name in EXPECTED_BINDS:
        body = _loader_body(name)
        expect(body is not None and '_gdext_ready("%s")' % name in body,
               "J: loader.%s tidak mencoba jalur C++ dulu" % name)
    # Manajemen backend + literal.
    for name in ("gdext_available", "force_backend", "reset_backend",
                 "backend_name", "is_using_gdext", "reload"):
        expect(re.search(r"^static func %s\(" % name, LOADER_SRC, re.M)
               is not None, "J: loader.%s hilang" % name)
    expect('const GDEXT_CLASS := "MysticMaps"' in LOADER_SRC,
           "J: GDEXT_CLASS != MysticMaps")
    expect('const SETTING := "mystic/maps/use_gdext_maps"' in LOADER_SRC,
           "J: SETTING != mystic/maps/use_gdext_maps")
    banner = [ln for ln in LOADER_SRC.splitlines()
              if "GDExtension MysticMaps aktif" in ln
              and not ln.strip().startswith("#")]
    expect(len(banner) == 1
           and '"[MapDBLoader] GDExtension MysticMaps aktif "' in banner[0],
           "J: banner gdext harus SATU literal utuh (%d baris)" % len(banner))
    proj = (ROOT / "godot" / "project.godot").read_text(encoding="utf-8")
    expect("maps/use_gdext_maps=false" in proj,
           "J: project.godot belum punya maps/use_gdext_maps=false")
    print("   api=%d binds=%d" % (len(EXPECTED_API), len(binds)))


# ══════════════════════════════════════════════════════════
#  K. themes.json segar (cermin vs berkas repo)
# ══════════════════════════════════════════════════════════

def check_themes_json(ordered):
    section("K. themes.json segar")
    path = ROOT / "godot" / "data" / "themes.json"
    expect(path.exists(), "K: %s tidak ada" % path)
    if not path.exists():
        return
    doc = json.loads(path.read_text(encoding="utf-8"))
    themes = doc.get("themes", {})
    expect(len(themes) == 54, "K: themes.json punya %d tema" % len(themes))
    expect(doc.get("fallback") == "forest", "K: fallback=%r" % doc.get("fallback"))
    n = 0
    for _const, key, row in ordered:
        if key not in themes:
            expect(False, "K: %s hilang dari themes.json" % key)
            continue
        got = m_derive(key, row)
        for k, e in got.items():
            n += 1
            g = themes[key].get(k, "<hilang>")
            if isinstance(e, float):
                expect(isinstance(g, float) and g == e,
                       "K: %s.%s json=%r cermin=%r (berkas basi?)" % (key, k, g, e))
            else:
                expect(g == e,
                       "K: %s.%s json=%r cermin=%r (berkas basi?)" % (key, k, g, e))
    print("   daun=%d" % n)


# ══════════════════════════════════════════════════════════
#  L. Fixture engine (oracle Python -> map_data.json)
# ══════════════════════════════════════════════════════════

FIXTURE = ROOT / "godot" / "tests" / "fixtures" / "map_data.json"
# Posisi toko paritas _render.py:107-108 == ArenaMap radiant/dire_shop_pos.
FIXTURE_SHOPS = [(340, 540), (940, 180)]
FIXTURE_SIZES = [(1280, 720), (1025, 769)]

CURVE_CASES = [
    ("empty", [], 10),
    ("singleton", [(5, 7)], 8),
    ("hline", [(0, 0), (10, 0)], 4),
    ("corner", [(0, 0), (0, 10), (10, 10), (10, 20)], 6),
    ("diag3", [(100, 100), (200, 200), (300, 100)], 5),
]


def _jval(value):
    if isinstance(value, (tuple, list)):
        return [_jval(v) for v in value]
    return value


def map_signature(ordered):
    total = sum(len(row) for _c, _k, row in ordered)
    return "%d:%s-%s:%d" % (len(ordered), ordered[0][1], ordered[-1][1], total)


def build_fixture(ordered, ns, palettes):
    PathGen = ns.PathGenerator
    DecoGen = ns.DecorationGenerator
    _keys, schema = gen.build_schema(ordered)
    nullable = {k for _c, _k, row in ordered for k, v in row.items() if v is None}
    key_kinds = {k: ("color4?" if k in nullable and kind == "color4" else kind)
                 for k, kind in schema.items()}
    catalog = []
    for _const, key, row in ordered:
        catalog.append({
            "name": key,
            "keys": list(row.keys()),
            "types": {k: key_kinds[k] for k in row},
            "values": {k: _jval(v) for k, v in row.items()},
        })
    curve_battery = []
    for name, wps, smooth in CURVE_CASES:
        got = PathGen.make_curved_path([tuple(p) for p in wps], smooth)
        curve_battery.append({
            "name": name, "waypoints": [list(p) for p in wps],
            "smoothness": smooth, "points": [list(p) for p in got],
        })
    lanes_fx, river_fx = {}, {}
    for w, h in FIXTURE_SIZES:
        top, mid, bot = PathGen.generate_lanes(w, h)
        lanes_fx["%dx%d" % (w, h)] = {
            "top": [list(p) for p in top],
            "mid": [list(p) for p in mid],
            "bot": [list(p) for p in bot],
        }
        river_fx["%dx%d" % (w, h)] = [
            list(p) for p in PathGen.generate_river(w, h)]
    decor_fx = {}
    w, h = FIXTURE_SIZES[0]
    top, mid, bot = PathGen.generate_lanes(w, h)
    river = PathGen.generate_river(w, h)
    # Urutan konkatenasi paritas _render.py: top + bot + mid.
    lane_all = list(top) + list(bot) + list(mid)
    for shopset, sname in ((FIXTURE_SHOPS, "shops"), ([], "no_shops")):
        data = DecoGen(w, h, lane_all, list(river),
                       list(shopset)).generate_all()
        decor_fx[sname] = {k: _jval(v) for k, v in data.items()}
    return {
        "source": {
            "module": "map_components/_bundle.py",
            "generated_by": "tools/test_godot_map_data_parity.py --write-fixture",
            "theme_count": len(ordered),
            "catalog_signature": map_signature(ordered),
            "tile_size": 16,
            "key_kinds": key_kinds,
            "notes": [
                "Semua angka di fixture ini sampai ke Godot sebagai FLOAT "
                "(JSON.parse_string Godot 4.3 tidak punya cabang bilangan "
                "bulat - core/io/json.cpp:341). Warna [r,g,b] dibaca "
                "per-komponen (int di kedua backend); kind tiap kunci tema "
                "ada di `types` tiap baris + `key_kinds`.",
                "generate_lanes Python mengembalikan TUPLE (top, mid, bot); "
                "KEDUA backend Godot mengembalikan Dictionary "
                "{top,mid,bot} (normalisasi yang dikunci fixture ini + "
                "tools/test_maps_cpp_selftest.py).",
                "lane_points dekor = top+bot+mid (urutan _render.py), river "
                "terpisah, shops [(340,540),(940,180)] paritas _render.py + "
                "ArenaMap; varian no_shops mengunci cabang jarak-toko.",
                "get_theme tak dikenal -> baris forest (paritas "
                "THEMES.get); build_theme di luar jangkauan -> {}.",
                "DEVIASI TERDOKUMENTASI: Python mengembalikan objek tema "
                "live (bisa dimutasi); kedua backend Godot mengembalikan "
                "Dictionary SEGAR tiap panggilan — engine test mengunci "
                "isolasi mutasi ini.",
            ],
        },
        "theme_names": [key for _c, key, _r in ordered],
        "catalog": catalog,
        "theme_index_battery": [[key, i] for i, (_c, key, _r)
                                in enumerate(ordered)]
        + [["no-such-theme", -1], ["", -1]],
        "get_theme_battery": [["forest", "forest"], ["haunted", "haunted"],
                              ["hollowbane", "hollowbane"],
                              ["no-such-theme", "forest"], ["", "forest"]],
        "build_theme_battery": [[0, "forest"], [53, "hollowbane"],
                                [-1, "empty"], [54, "empty"], [99, "empty"]],
        "curve_battery": curve_battery,
        "lanes": lanes_fx,
        "river": river_fx,
        "decor": decor_fx,
        "decor_shops": [list(s) for s in FIXTURE_SHOPS],
        "decor_size": [w, h],
        "palettes": {n: list(v) for n, v, _ in palettes if n != "TILE_SIZE"},
        "tile_size": [v for n, v, _ in palettes if n == "TILE_SIZE"][0],
    }


def check_fixture(ordered, ns, palettes, write):
    section("L. fixture engine (oracle Python)")
    fixture = build_fixture(ordered, ns, palettes)
    expect(fixture["source"]["catalog_signature"] == "54:forest-hollowbane:2984",
           "L: signature=%s" % fixture["source"]["catalog_signature"])
    expect(fixture["tile_size"] == 16, "L: tile_size=%r" % fixture["tile_size"])
    expect(len(fixture["palettes"]) == len(palettes) - 1,
           "L: palet fixture=%d" % len(fixture["palettes"]))
    lanes = fixture["lanes"]["1280x720"]
    expect([len(lanes[k]) for k in ("top", "mid", "bot")] == [111, 65, 101],
           "L: ukuran lane 1280x720=%s" % [len(lanes[k]) for k in lanes])
    expect(len(fixture["river"]["1280x720"]) == 61, "L: river != 61 titik")
    expect(len(fixture["lanes"]["1025x769"]["mid"]) == 65,
           "L: mid 1025x769 != 65 titik")
    for sname in ("shops", "no_shops"):
        cats = fixture["decor"][sname]
        expect(list(cats.keys()) == EXPECTED_CATS,
               "L: kategori %s=%s" % (sname, list(cats.keys())))
        n = sum(len(v) for v in cats.values())
        expect(n > 100, "L: dekor %s hanya %d entri" % (sname, n))
        expect(len(cats["torch_stones"]) == 18,
               "L: obor %s=%d, harap 18" % (sname, len(cats["torch_stones"])))
    n_empty = sum(1 for c in fixture["curve_battery"] if not c["points"])
    expect(n_empty == 1, "L: kasus kurva kosong=%d, harap 1" % n_empty)
    payload = json.dumps(fixture, indent=2, ensure_ascii=False,
                         sort_keys=False) + "\n"
    if write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(payload, encoding="utf-8")
        print("  ditulis %s (%d KB)" % (FIXTURE.relative_to(ROOT), len(payload) // 1024))
        return
    if not FIXTURE.exists():
        expect(False, "%s tidak ada — jalankan "
                      "tools/test_godot_map_data_parity.py --write-fixture"
               % FIXTURE.relative_to(ROOT))
        return
    current = FIXTURE.read_text(encoding="utf-8")
    expect(current == payload,
           "L: fixture %s BASI (_bundle.py berubah tanpa fixture diperbarui) "
           "— jalankan tools/test_godot_map_data_parity.py --write-fixture"
           % FIXTURE.relative_to(ROOT))
    print("  fixture segar: %d tema, %d kasus kurva, %d+%d titik lane/river, "
          "dekor %d+%d entri" % (
              len(fixture["catalog"]), len(fixture["curve_battery"]),
              sum(len(v) for v in fixture["lanes"]["1280x720"].values()),
              len(fixture["river"]["1280x720"]),
              sum(len(v) for v in fixture["decor"]["shops"].values()),
              sum(len(v) for v in fixture["decor"]["no_shops"].values())))


# ══════════════════════════════════════════════════════════
#  M. Wiring closed-world (ArenaMap + engine test + paket + CI)
# ══════════════════════════════════════════════════════════

def check_wiring():
    section("M. wiring closed-world")
    arena = (ROOT / "godot" / "scenes" / "map" / "ArenaMap.gd").read_text(
        encoding="utf-8")
    # ArenaMap lewat loader — tidak ada duplikat logika data.
    expect('preload("res://scripts/core/MapDBLoader.gd")' in arena,
           "M: ArenaMap tidak preload MapDBLoader")
    for call in ("MapDB.theme_names()", "MapDB.theme_palette(",
                 "MapDB.generate_lanes(", "MapDB.generate_river(",
                 "MapDB.backend_name()"):
        expect(call in arena, "M: ArenaMap tidak memanggil %s" % call)
    for dead in ("_curved_path", "_colors_from", "THEMES_JSON",
                 '"themes.json"', "PackedVector2Array([\n\t\t\t\tVector2(90"):
        expect(dead not in arena, "M: sisa port lama di ArenaMap: %s" % dead)
    # Toko ArenaMap == _render.py (sumber posisi shop_positions dekor).
    expect("Vector2(340, 540)" in arena and "Vector2(940, 180)" in arena,
           "M: shop ArenaMap != (340,540)/(940,180)")
    expect("self.radiant_shop_pos = (340, 540)" in BUNDLE_SRC
           or "(340, 540)" in (ROOT / "_render.py").read_text(encoding="utf-8"),
           "M: anchor _render.py berubah")
    render = (ROOT / "_render.py").read_text(encoding="utf-8")
    expect("self.radiant_shop_pos = (340, 540)" in render
           and "self.dire_shop_pos = (940, 180)" in render,
           "M: shop _render.py != (340,540)/(940,180)")
    # Override kurasi 4 tema utuh.
    expect('for k in ["modulate", "light", "energy"]:' in arena,
           "M: loop override kurasi hilang dari ArenaMap")
    # Engine test: berkas + referensi scene + arity _fail.
    base = ROOT / "godot" / "tests" / "MapDataParityTest.gd"
    gdext = ROOT / "godot" / "tests" / "MapDataGdextParityTest.gd"
    expect(base.exists() and gdext.exists(), "M: berkas engine test hilang")
    for tscn, gd in (("MapDataParityTest", "MapDataParityTest.gd"),
                     ("MapDataGdextParityTest", "MapDataGdextParityTest.gd")):
        text = (ROOT / "godot" / "tests" / (tscn + ".tscn")).read_text(
            encoding="utf-8")
        expect("res://tests/%s" % gd in text, "M: %s tak merujuk %s" % (tscn, gd))
    gtext = gdext.read_text(encoding="utf-8")
    expect('extends "res://tests/MapDataParityTest.gd"' in gtext,
           "M: Gdext test tidak extends base")
    expect(len(re.findall(r"^\s*_fail\(", gtext, re.M)) == 1
           and '_fail("gdext/%s: %s" % [tag, message])' in gtext,
           "M: _fail_gdext harus SATU panggilan _fail 1-argumen")
    # Paket GDExt: entry symbol + mapping linux debug.
    ext = (ROOT / "godot" / "addons" / "mystic_maps"
           / "mystic_maps.gdextension").read_text(encoding="utf-8")
    expect('entry_symbol = "mystic_maps_library_init"' in ext,
           "M: entry_symbol .gdextension salah")
    expect("linux.debug.x86_64" in ext
           and "libmystic_maps.linux.template_debug.x86_64.so" in ext,
           "M: mapping linux.debug.x86_64 hilang")
    expect((ROOT / "godot" / "addons" / "mystic_maps" / "bin"
            / ".gitkeep").exists(), "M: addons bin/.gitkeep hilang")
    # .gitignore menutup output build + symlink godot-cpp.
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pat in ("godot/addons/mystic_maps/bin/*.so",
                "godot/gdext/mystic_maps/godot-cpp"):
        expect(pat in gi, "M: .gitignore tidak menutup %s" % pat)
    # Kedua workflow merujuk artefak maps (filter paths + langkah uji).
    check = (ROOT / ".github" / "workflows" / "godot-check.yml").read_text(
        encoding="utf-8")
    gdext_yml = (ROOT / ".github" / "workflows" / "godot-gdext.yml").read_text(
        encoding="utf-8")
    for needle in ("tools/test_godot_map_data_parity.py",
                   "tools/gen_maps_cpp.py",
                   "res://tests/MapDataParityTest.tscn",
                   "[MapDataParityTest] PASS"):
        expect(needle in check, "M: godot-check.yml tak merujuk %s" % needle)
    for needle in ("tools/test_maps_cpp_selftest.py",
                   "mystic_maps_library_init",
                   "res://tests/MapDataGdextParityTest.tscn",
                   "[MapDataGdextParityTest] PASS",
                   "GDExtension MysticMaps aktif",
                   "for lib in mystic_skills mystic_levels mystic_maps"):
        expect(needle in gdext_yml,
               "M: godot-gdext.yml tak merujuk %s" % needle)
    print("   arenamap + 2 scene + gdextension + gitignore + 2 workflow")


def main():
    palettes, ordered, pathgen = load_oracle()
    print("oracle: %d palet, %d tema (%s ... %s)"
          % (len(palettes), len(ordered), ordered[0][1], ordered[-1][1]), flush=True)
    check_raw_json(palettes, ordered)
    check_key_kinds(ordered)
    check_key_map()
    check_waypoints(pathgen)
    check_decor_ast()
    check_decor_gd(palettes)
    check_validators()
    check_mt()
    check_rounding(ordered)
    check_derive(ordered)
    check_gen()
    check_api()
    check_themes_json(ordered)
    check_fixture(ordered, pathgen, palettes, "--write-fixture" in sys.argv)
    check_wiring()
    print("═" * 60)
    print("checks=%d failures=%d" % (CHECKS[0], len(FAILURES)))
    for f in FAILURES[:40]:
        print("FAIL " + f)
    if FAILURES:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
