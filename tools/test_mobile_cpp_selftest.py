#!/usr/bin/env python3
"""Self-test mobile_processor.cpp di luar engine (butuh g++ saja, tanpa godot-cpp).

    python3 tools/test_mobile_cpp_selftest.py

Menyalakan kode C++ hasil tools/gen_mobile_cpp.py APA ADANYA lewat stub Variant
(godot/gdext/mystic_mobile/selftest), lalu membandingkan balasannya dengan
oracle. Oracle-nya BUKAN replikasi tangan: tiap modul mobile/*.py di-EXEC
sebagai pohon AST tanpa node import (pygame tidak pernah di-import — sandbox
CI tidak punya pygame), dengan stubpygame + stub modul tetangga. Fungsi murni
(Konstanta, preset, geometri tombol, kualitas adaptif, parse_payload, ...)
dipanggil di Python ASLI lalu hasilnya dibandingkan dengan jawaban C++.

Karena numpy/pygame tidak ada di CI, pygame ditiru seminimal mungkin:
  * pygame.Rect      — subclass lokal dengan left/top/right/bottom/inflate/
                       collidepoint (semantik SDL: tepi kanan-bawah eksklusif);
  * pygame.font/draw — kelas/kosong; hud.py hanya menyentuhnya saat draw
                       (tidak digerakkan di sini).

Yang TIDAK diorakelkan (backend-bound, lihat docs/AUDIT_ULANG_DARI_AWAL.md):
mixer pygame, sha256/checksum, strftime, JNI, gambar. Gerbang play/combat dan
ringkas diuji lewat konstanta ASLI _KONFIG + ringkas() asli.

Pola tools/test_maps_cpp_selftest.py + test_ui_cpp_selftest.py. Sengaja jalan
SEBELUM build godot-cpp di CI: regresi ambang gesture/kualitas gagal cepat.

Selain membandingkan nilai, skrip ini mengunci invarian struktural:
  * jumlah entri tabel perintah (mobile_dispatch.inc) == jumlah
    bind_static_method == jumlah deklarasi static di mobile_processor.h;
  * daftar module_names() == 8 submodul mobile/;
  * api_signature() == mobile_v1:8mod:66fn:;
  * wiring: gdextension entry_symbol, SConstruct, CI workflow, log gate,
    .gitignore, dan mobile/*.py tetap bersih (tidak dimodifikasi).
"""
import ast
import collections
import gc
import hashlib
import json
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import types
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

SELFTEST = ROOT / "godot" / "gdext" / "mystic_mobile" / "selftest"
SRC = ROOT / "godot" / "gdext" / "mystic_mobile" / "src"

MODULES = ["touch", "hud", "perf", "platform_utils", "debug",
           "combat_audio", "cloud_save", "buildinfo"]

_checks = 0
_failures = []


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[mobile_selftest] FAIL: %s" % message)


def section(title):
    print("[mobile_selftest] ── %s ──" % title)


# ══════════════════════════════════════════════════════════
#  Nilai ber-tag (ekspektasi) + parser balasan protokol
# ══════════════════════════════════════════════════════════


def T_nil():
    return ("nil", None)


def T_bool(v):
    return ("bool", bool(v))


def T_int(v):
    return ("int", int(v))


def T_float(v):
    return ("float", float(v))


def T_str(v):
    return ("str", str(v))


def T_color(rgb, alpha=255):
    return ("color", (int(rgb[0]), int(rgb[1]), int(rgb[2]), int(alpha)))


def T_v2(x, y):
    # Vector2 menyimpan float32 — quantize ekspektasi ke float32.
    q = lambda v: struct.unpack("f", struct.pack("f", float(v)))[0]
    return ("v2", (q(x), q(y)))


def T_rect(x, y, w, h):
    q = lambda v: struct.unpack("f", struct.pack("f", float(v)))[0]
    return ("rect", (q(x), q(y), q(w), q(h)))


def T_arr(items):
    return ("array", list(items))


def T_dict(pairs):
    return ("dict", list(pairs))  # list of (key, value) — urutan terkunci


def _split_top(text, sep):
    out, cur, depth = [], [], 0
    for ch in text:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur))
    return out


def _split_atoms(inner):
    # Atom tanpa awalan tag (int/bool/float/str/color/...) menempel pada
    # atom sebelumnya (mis. "{str:a=int:1,str:b=int:2}").
    out = []
    for part in _split_top(inner, ","):
        if out and not re.match(
                r"^(nil:|bool:|int:|float:|str:|color:|v2:|rect:|\[|\{)", part):
        # tangguhkan ke atom terakhir
            out[-1] = out[-1] + "," + part
        else:
            out.append(part)
    return out


def parse_reply(text):
    """Decode balasan harness (nilai ber-tag) -> tuple Python murni."""
    text = text.strip()
    if text.startswith("dict:"):
        text = text[5:]
    elif text.startswith("array:"):
        text = text[6:]
    if text.startswith("nil:"):
        return T_nil()
    if text.startswith("bool:"):
        return T_bool(text[5:] == "true")
    if text.startswith("int:"):
        return T_int(int(text[4:]))
    if text.startswith("float:"):
        return T_float(float(text[6:]))
    if text.startswith("str:"):
        return T_str(text[4:])
    if text.startswith("color:"):
        parts = [int(p) for p in text[6:].split(",")]
        return T_color(parts[:3], parts[3] if len(parts) > 3 else 255)
    if text.startswith("v2:"):
        parts = [float(p) for p in text[3:].split(",")]
        return T_v2(parts[0], parts[1])
    if text.startswith("rect:"):
        parts = [float(p) for p in text[5:].split(",")]
        return T_rect(parts[0], parts[1], parts[2], parts[3])
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return T_arr([])
        return T_arr([parse_reply(p) for p in _split_atoms(inner)])
    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        if not inner:
            return T_dict([])
        pairs = []
        for entry in _split_atoms(inner):
            depth = 0
            eq = -1
            for idx, ch in enumerate(entry):
                if ch in "[{":
                    depth += 1
                elif ch in "]}":
                    depth -= 1
                elif ch == "=" and depth == 0:
                    eq = idx
                    break
            assert eq > 0, "entri dict rusak: %r" % entry
            pairs.append((parse_reply(entry[:eq]), parse_reply(entry[eq + 1:])))
        return T_dict(pairs)
    raise AssertionError("balasan tidak dikenal: %r" % text)


def compare(tagged, got, what):
    """Bandingkan dua nilai ber-tag (ekspektasi vs hasil parse_reply)."""
    kind, want = tagged
    gkind, gval = got
    expect(gkind == kind, "%s: tipe %s != %s" % (what, gkind, kind))
    if gkind != kind:
        return
    if kind == "float":
        # dua-duanya hasil operasi IEEE identik — harus bit-exact.
        expect(gval == want, "%s: %r != %r" % (what, gval, want))
    elif kind in ("v2", "rect"):
        expect(len(gval) == len(want) and all(
            abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
            for a, b in zip(gval, want)),
            "%s: %r != %r" % (what, gval, want))
    elif kind == "array":
        expect(len(gval) == len(want), "%s: panjang %d != %d"
               % (what, len(gval), len(want)))
        for idx, (g, w) in enumerate(zip(gval, want)):
            compare(w, g, "%s[%d]" % (what, idx))
    elif kind == "dict":
        expect(len(gval) == len(want), "%s: panjang %d != %d"
               % (what, len(gval), len(want)))
        for idx, ((gk, gv), (wk, wv)) in enumerate(zip(gval, want)):
            compare(wk, gk, "%s[%d].kunci" % (what, idx))
            compare(wv, gv, "%s[%d].nilai" % (what, idx))
    else:
        expect(gval == want, "%s: %r != %r" % (what, gval, want))


# ══════════════════════════════════════════════════════════
#  Stub pygame + modul tetangga
# ══════════════════════════════════════════════════════════


class StubRect:
    """pygame.Rect seminimal mungkin (semantik SDL: kanan-bawah eksklusif)."""

    def __init__(self, *args):
        if len(args) == 1:
            src = args[0]
            if isinstance(src, StubRect):
                self.x, self.y = src.x, src.y
                self.width, self.height = src.width, src.height
                return
            args = src
        self.x, self.y, self.width, self.height = [int(v) for v in args]

    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def size(self):
        return (self.width, self.height)

    def inflate(self, dx, dy):
        # pygame.Rect.inflate: ukuran tumbuh TOTAL dx/dy, sudut mundur dx/2
        return StubRect(self.x - dx // 2, self.y - dy // 2,
                        self.width + dx, self.height + dy)

    def collidepoint(self, pos):
        px, py = pos
        return (self.left <= px < self.right
                and self.top <= py < self.bottom)


def make_pygame_stub():
    pg = types.ModuleType("pygame")
    pg.Rect = StubRect
    pg.SRCALPHA = 0x10000
    pg.font = types.SimpleNamespace(Font=type("Font", (), {}), SysFont=type("SysFont", (), {}))
    pg.draw = types.SimpleNamespace()  # tanpa aacircle -> _ORIG_AACIRCLE None
    pg.time = types.SimpleNamespace(get_ticks=lambda: 0)
    pg.mixer = types.SimpleNamespace()
    pg.Surface = type("Surface", (), {})
    pg.FINGERDOWN = 1024
    pg.FINGERUP = 1025
    pg.FINGERMOTION = 1026
    pg.MOUSEBUTTONDOWN = 1027
    pg.MOUSEBUTTONUP = 1028
    pg.MOUSEMOTION = 1029
    pg.K_SPACE = 32
    pg.K_ESCAPE = 27
    return pg


def make_plat_stub():
    """platform_utils tiruan utk touch/hud/debug: identitas + rect aman."""
    plat = types.ModuleType("plat")
    plat.LOGICAL_WIDTH = 1280
    plat.LOGICAL_HEIGHT = 720
    plat.pointer_to_logical = lambda pos: (float(pos[0]), float(pos[1]))
    plat.finger_to_logical = plat.pointer_to_logical
    plat.get_safe_area = lambda: StubRect(0, 0, 1280, 720)
    plat.get_panel_rect = lambda: None
    plat.get_device_info = lambda: {"dpi": 160, "model": "stub"}
    return plat


def strip_and_exec(rel_path, extra):
    """EXEC mobile/<modul>.py tanpa node import (stub disediakan extra)."""
    path = ROOT / rel_path
    tree = ast.parse(path.read_text())
    body = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    code = compile(ast.Module(body=body, type_ignores=[]), str(path), "exec")
    g = {"__name__": path.stem, "__file__": str(path)}
    g.update(extra)
    exec(code, g)  # noqa: S102 - oracle sengaja menjalankan sumber repo
    return g


# ── oracle: modul mobile asli ──────────────────────────────

def load_oracles():
    pg = make_pygame_stub()
    plat_stub = make_plat_stub()
    quality_stub = types.SimpleNamespace(cheap_alpha=True)
    ui_theme_stub = types.SimpleNamespace(_radial=lambda *a, **k: None)

    _perf_path = ROOT / "mobile" / "perf.py"
    _perf_tree = ast.parse(_perf_path.read_text())
    perf_ns = strip_and_exec("mobile/perf.py", {
        "gc": gc, "time": time, "OrderedDict": collections.OrderedDict,
        "pygame": pg,
    })
    touch_ns = strip_and_exec("mobile/touch.py", {
        "time": time, "pygame": pg, "plat": plat_stub,
        "dataclass": __import__("dataclasses").dataclass,
    })
    hud_ns = strip_and_exec("mobile/hud.py", {
        "math": math, "pygame": pg, "plat": plat_stub,
        "Quality": quality_stub, "ui_theme": ui_theme_stub,
    })
    plat_ns = strip_and_exec("mobile/platform_utils.py", {
        "os": os, "sys": sys, "pygame": pg,
    })
    debug_ns = strip_and_exec("mobile/debug.py", {
        "gc": gc, "os": os, "time": time,
        "deque": collections.deque, "pygame": pg, "plat": plat_stub,
        "perf": types.SimpleNamespace(
            Quality=perf_ns["Quality"],
            FrameTimer=type("FrameTimer", (), {
                "report": lambda self: {"update": 0.0, "draw": 0.0}}),
            font_cache_stats=lambda: {}, ),
    })
    combat_ns = strip_and_exec("mobile/combat_audio.py", {
        "os": os, "random": random, "pygame": pg,
    })
    cloud_ns = strip_and_exec("mobile/cloud_save.py", {
        "hashlib": hashlib, "json": json, "os": os, "sys": sys,
        "tempfile": __import__("tempfile"), "threading": threading,
        "time": time, "uuid": uuid,
        "storage_paths": types.SimpleNamespace(
            SAVE_DIR=str(ROOT / ".oracle_save_dir")),
    })
    buildinfo_ns = strip_and_exec("mobile/buildinfo.py", {"os": os})
    perf_ns["_perf_tree"] = _perf_tree
    return {
        "pg": pg, "plat_stub": plat_stub, "perf": perf_ns, "touch": touch_ns,
        "hud": hud_ns, "plat": plat_ns, "debug": debug_ns,
        "combat": combat_ns, "cloud": cloud_ns, "buildinfo": buildinfo_ns,
    }


# ══════════════════════════════════════════════════════════
#  Harness C++: kompilasi + kirim perintah
# ══════════════════════════════════════════════════════════


def find_compiler():
    for cand in (os.environ.get("CXX"), "g++", "clang++"):
        if cand and shutil.which(cand):
            return cand
    return None


def compile_selftest(compiler, out_path):
    cmd = [compiler, "-std=c++17", "-O0",
           "-I", str(SELFTEST), "-I", str(SELFTEST / "shim"),
           "-o", str(out_path), str(SELFTEST / "mobile_selftest.cpp")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit("[mobile_selftest] gagal kompilasi self-test C++")


def run_binary(binary, commands):
    """Kirim semua perintah sekaligus; kembalikan {id: teks balasan}."""
    payload = "".join(cmd + "\n" for cmd in commands)
    proc = subprocess.run([str(binary)], input=payload,
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        print(proc.stdout[-4000:])
        print(proc.stderr[-2000:])
        raise SystemExit("[mobile_selftest] self-test C++ exit %d"
                         % proc.returncode)
    replies = {}
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] not in replies:
            replies[parts[0]] = "\t".join(parts[1:])
    return replies


# ══════════════════════════════════════════════════════════
#  Baterai perintah per modul (oracle = kode Python ASLI)
# ══════════════════════════════════════════════════════════


_cid_counter = [0]


class Battery:
    def __init__(self):
        self.commands = []   # teks perintah utk binary
        self.jobs = []       # (id, tagged, what)

    def add(self, fn, args, tagged, what):
        _cid_counter[0] += 1
        cid = "c%03d" % _cid_counter[0]
        parts = [cid, "fn", fn] + [enc(a) for a in args]
        self.commands.append("\t".join(parts))
        self.jobs.append((cid, tagged, what))


_TAGS = ("nil", "bool", "int", "float", "str", "color", "v2", "rect")


def enc(a):
    """Argumen battery -> teks ber-tag (menerima T_*/nilai Python/teks jadi)."""
    if isinstance(a, tuple) and a and a[0] in _TAGS:
        kind, v = a
        if kind == "nil":
            return "nil:null"
        if kind == "bool":
            return "bool:true" if v else "bool:false"
        if kind == "int":
            return "int:%d" % int(v)
        if kind == "float":
            return "float:%r" % float(v)
        if kind == "str":
            return "str:%s" % v
        if kind == "v2":
            return "v2:%r,%r" % (float(v[0]), float(v[1]))
        if kind == "rect":
            return "rect:%r,%r,%r,%r" % (float(v[0]), float(v[1]),
                                         float(v[2]), float(v[3]))
    if isinstance(a, str):
        return a
    return tag_text(a)


def tag_text(v):
    """Nilai Python -> teks ber-tag (argumen harness C++)."""
    if v is None:
        return "nil:null"
    if isinstance(v, bool):
        return "bool:true" if v else "bool:false"
    if isinstance(v, int):
        return "int:%d" % v
    if isinstance(v, float):
        return "float:%r" % v
    if isinstance(v, str):
        return "str:%s" % v
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(tag_text(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join("%s=%s" % (tag_text(k), tag_text(x))
                              for k, x in v.items()) + "}"
    raise AssertionError("tipe arg tak didukung: %r" % (v,))


def color_of(t):
    """Tuple (r,g,b[,a]) pygame -> tag warna 8-bit."""
    return T_color(t[:3], t[3] if len(t) > 3 else 255)


def build_meta(o):
    b = Battery()
    b.add("module_names", [], T_arr([T_str(m) for m in MODULES]),
          "module_names == 8 submodul")
    b.add("module_names_string", [], T_str(",".join(MODULES)),
          "module_names_string == generator join(',')")
    b.add("api_signature", [], T_str("mobile_v1:8mod:66fn:"), "api_signature")
    return b


def build_touch(o):
    b = Battery()
    tns = o["touch"]
    TouchManager = tns["TouchManager"]
    TAP_SLOP = tns["TAP_SLOP"]
    DOUBLE_TAP_MS = tns["DOUBLE_TAP_MS"]
    LONG_PRESS_MS = tns["LONG_PRESS_MS"]
    SCROLL_STEP = tns["SCROLL_STEP"]
    FLING_FRICTION = tns["FLING_FRICTION"]
    FLING_MIN_SPEED = tns["FLING_MIN_SPEED"]

    # konstanta (12 kunci, urutan generator; literal dari touch.py:
    # radius dbl-tap 40, arm fling 4, divisor 0.35, cap 3, smoothing 0.6/0.4)
    b.add("touch_constants", [], T_dict([
        (T_str("tap_slop"), T_int(TAP_SLOP)),
        (T_str("long_press_ms"), T_int(LONG_PRESS_MS)),
        (T_str("double_tap_ms"), T_int(DOUBLE_TAP_MS)),
        (T_str("scroll_step"), T_int(SCROLL_STEP)),
        (T_str("fling_friction"), T_float(FLING_FRICTION)),
        (T_str("fling_min_speed"), T_float(FLING_MIN_SPEED)),
        (T_str("double_tap_radius_px"), T_int(40)),
        (T_str("fling_arm_speed"), T_int(4)),
        (T_str("fling_divisor"), T_float(0.35)),
        (T_str("fling_max_steps"), T_int(3)),
        (T_str("velocity_keep"), T_float(0.6)),
        (T_str("velocity_new"), T_float(0.4)),
    ]), "touch_constants")

    # kecepatan gerak: rumus smoothing ASLI via TouchManager._motion
    tm = TouchManager(use_finger_events=False)
    tm._down(0, (100, 200))
    tm._motion(0, (100, 260))  # dy 60
    v1 = tm.points[0].velocity
    b.add("motion_velocity", [T_int(0), T_float(60)], T_float(v1),
          "motion_velocity(fresh)")
    tm._motion(0, (100, 290))  # dy 30 -> smooth(prev, 30)
    v2 = tm.points[0].velocity
    b.add("motion_velocity", [T_float(v1), T_float(30)], T_float(v2),
          "motion_velocity(smooth)")

    # slop: total >= TAP_SLOP
    total_small = math.hypot(5, 5)
    total_big = math.hypot(15, 5)
    b.add("motion_exceeds_slop", [T_float(total_small)], T_bool(False),
          "slop di bawah")
    b.add("motion_exceeds_slop", [T_float(total_big)], T_bool(True),
          "slop di atas")

    # scroll notch: kontrak C++ = SATU langkah loop python
    # (arg = total accum termasuk dy; pemanggil mengulang selama
    #  abs(accum) >= SCROLL_STEP). Verifikasi silang dgn TouchManager asli.
    def notch_chain(total):
        """Replicasi while python -> [(arg, dir, sisa_per_langkah)]."""
        steps = []
        a = float(total)
        while abs(a) >= SCROLL_STEP:
            d = -1 if a > 0 else 1
            nxt = a - SCROLL_STEP * (1 if a > 0 else -1)
            steps.append((a, d, nxt))
            a = nxt
        return steps

    # positif: 50 -> satu langkah (50 -> 8); asli: satu aksi -1, accum 8
    tm2 = TouchManager(use_finger_events=False)
    tm2._down(0, (0, 0))
    tm2._motion(0, (0, 50))
    acts = [a.value for a in tm2.collect() if a.kind == "scroll"]
    expect(acts == [-1], "scroll asli: satu notch -1, dapat %r" % acts)
    expect(tm2.points[0].scroll_accum == 8, "accum asli 8, dapat %r"
           % tm2.points[0].scroll_accum)
    for arg, d, nxt in notch_chain(50):
        b.add("scroll_notch", [T_float(arg)], T_dict([
            (T_str("direction"), T_int(d)),
            (T_str("accum"), T_float(nxt)),
        ]), "scroll_notch(%.0f)" % arg)
    # lanjutan: accum 8 + dy 34 = 42 -> satu langkah tepat ke 0
    tm2._motion(0, (0, 84))  # dy +34 (posisi absolut)
    acts = [a.value for a in tm2.collect() if a.kind == "scroll"]
    expect(acts == [-1], "scroll asli: notch kedua -1, dapat %r" % acts)
    expect(tm2.points[0].scroll_accum == 0, "accum asli 0, dapat %r"
           % tm2.points[0].scroll_accum)
    for arg, d, nxt in notch_chain(42):
        b.add("scroll_notch", [T_float(arg)], T_dict([
            (T_str("direction"), T_int(d)),
            (T_str("accum"), T_float(nxt)),
        ]), "scroll_notch(%.0f dari accum 8)" % arg)
    # negatif dua langkah: -84 -> -42 -> 0 (arah +1)
    tm2b = TouchManager(use_finger_events=False)
    tm2b._down(0, (0, 0))
    tm2b._motion(0, (0, -84))
    acts = [a.value for a in tm2b.collect() if a.kind == "scroll"]
    expect(acts == [1, 1], "scroll asli negatif: dua notch +1, dapat %r"
           % acts)
    for arg, d, nxt in notch_chain(-84):
        b.add("scroll_notch", [T_float(arg)], T_dict([
            (T_str("direction"), T_int(d)),
            (T_str("accum"), T_float(nxt)),
        ]), "scroll_notch(%.0f negatif)" % arg)

    # double tap: dua tap ASLI berdekatan
    tm3 = TouchManager(use_finger_events=False)
    tm3._down(0, (10, 10))
    tm3._up(0, (12, 12))
    tm3._down(1, (11, 11))
    tm3._up(1, (11, 11))
    kinds = [a.kind for a in tm3.collect()]
    expect("double_tap" in kinds, "tap ganda asli: dapat %r" % kinds)
    b.add("tap_is_double", [T_int(100), T_int(1), T_int(1)], T_bool(True),
          "tap_is_double cepat+dekat")
    b.add("tap_is_double", [T_int(DOUBLE_TAP_MS + 1), T_int(1), T_int(1)],
          T_bool(False), "tap_is_double telat")
    b.add("tap_is_double", [T_int(50), T_int(100), T_int(1)], T_bool(False),
          "tap_is_double jauh-x")
    b.add("tap_is_double", [T_int(50), T_int(1), T_int(100)], T_bool(False),
          "tap_is_double jauh-y")
    # dt ms yang diukur ASLI dijamin < DOUBLE_TAP_MS
    import time as _time
    tm4 = TouchManager(use_finger_events=False)
    t0 = _time.perf_counter()
    tm4._down(0, (5, 5))
    tm4._up(0, (5, 5))
    tm4._down(1, (6, 6))
    tm4._up(1, (6, 6))
    real_dt = int((_time.perf_counter() - t0) * 1000.0)
    kinds = [a.kind for a in tm4.collect()]
    expect("double_tap" in kinds and real_dt < DOUBLE_TAP_MS,
           "tap ganda nyata dt=%dms, dapat %r" % (real_dt, kinds))
    b.add("tap_is_double", [T_int(real_dt), T_int(1), T_int(1)], T_bool(True),
          "tap_is_double dt nyata")

    # fling: angkat jari cepat -> inersia
    tm5 = TouchManager(use_finger_events=False)
    tm5._down(0, (0, 0))
    tm5._motion(0, (0, 200))
    fling_v = abs(tm5.points[0].velocity)  # kecepatan titik (0.4*200 = 80)
    tm5._up(0, (0, 210))
    expect(abs(tm5.fling_velocity - fling_v) < 1e-9,
           "fling_velocity manager == kecepatan titik: %r"
           % tm5.fling_velocity)
    kinds = [a.kind for a in tm5.collect()]
    expect("fling" in kinds, "fling asli muncul: %r" % kinds)
    b.add("release_is_fling", [T_bool(True), T_float(fling_v)], T_bool(True),
          "fling terdeteksi")
    b.add("release_is_fling", [T_bool(True), T_float(0.3)], T_bool(False),
          "fling terlalu lambat")
    b.add("release_is_fling", [T_bool(False), T_float(99.0)], T_bool(False),
          "release bukan gerak cepat")
    # decay ASLI
    tm5.fling_velocity = fling_v
    tm5.update()
    decayed = tm5.fling_velocity
    b.add("fling_decay", [T_float(fling_v)], T_float(decayed),
          "fling_decay == v*FRICTION asli")
    steps = int(abs(decayed) / (SCROLL_STEP * 0.35))
    emitted = [a.kind for a in tm5.collect() if a.kind == "scroll"]
    expect(len(emitted) == min(steps, 3),
           "inersia asli: %d langkah vs %r" % (min(steps, 3), emitted))
    b.add("fling_steps", [T_float(decayed)], T_int(min(steps, 3)),
          "fling_steps == langkah inersia asli")
    b.add("fling_direction", [T_float(decayed)], T_int(-1),
          "fling_direction positif = -1")
    b.add("fling_direction", [T_float(-decayed)], T_int(1),
          "fling_direction negatif = 1")
    b.add("fling_active", [T_float(FLING_MIN_SPEED)], T_bool(False),
          "fling_active di ambang = False")
    b.add("fling_active", [T_float(FLING_MIN_SPEED + 1)], T_bool(True),
          "fling_active di atas ambang")

    # long press
    tm6 = TouchManager(use_finger_events=False)
    tm6._down(0, (5, 5))
    tm6.points[0].start_time -= 0.6  # backdate 600ms
    tm6.update()
    kinds = [a.kind for a in tm6.collect()]
    expect("long_press" in kinds, "long_press asli: %r" % kinds)
    b.add("long_press_due", [T_int(600)], T_bool(True), "long_press_due(600)")
    b.add("long_press_due", [T_int(LONG_PRESS_MS - 1)], T_bool(False),
          "long_press_due(449)")

    # dispatch tombol (urutan prioritas == dispatch_to_game ASLI):
    # kind tap/long_press/scroll + value (arah scroll)
    b.add("dispatch_button", [T_str("tap"), T_int(0)], T_int(1),
          "tap -> tombol 1")
    b.add("dispatch_button", [T_str("long_press"), T_int(0)], T_int(3),
          "long_press -> tombol 3")
    b.add("dispatch_button", [T_str("scroll"), T_int(-1)], T_int(4),
          "scroll atas -> 4")
    b.add("dispatch_button", [T_str("scroll"), T_int(1)], T_int(5),
          "scroll bawah -> 5")
    b.add("dispatch_button", [T_str("drag"), T_int(0)], T_int(0),
          "kind lain -> 0 (tidak dikonsumsi)")
    return b


def build_hud(o):
    b = Battery()
    hns = o["hud"]
    TouchHUD = hns["TouchHUD"]
    TouchButton = hns["TouchButton"]

    b.add("hud_min_tap", [], T_int(hns["MIN_TAP"]), "hud_min_tap")
    b.add("hud_colors", [], T_dict([
        (T_str("gold"), color_of(hns["GOLD"])),
        (T_str("gold_dim"), color_of(hns["GOLD_DIM"])),
        (T_str("bg"), color_of(hns["BG"])),
        (T_str("bg_active"), color_of(hns["BG_ACTIVE"])),
        (T_str("white"), color_of(hns["WHITE"])),
        (T_str("grey"), color_of(hns["GREY"])),
        (T_str("red"), color_of(hns["RED"])),
    ]), "hud_colors vs palet modul asli")
    b.add("hud_skill_labels", [], T_dict([
        (T_str(k), T_str(v)) for k, v in hns["SKILL_LABELS"].items()
    ]), "hud_skill_labels")
    b.add("hud_skill_names", [], T_dict([
        (T_str(k), T_str(v)) for k, v in hns["SKILL_NAMES"].items()
    ]), "hud_skill_names")
    b.add("tactical_actions", [], T_arr(
        [T_str(a) for a in hns["TACTICAL_ACTIONS"]]), "tactical_actions")

    # geometri tombol ASLI dari TouchHUD._build_layout (safe stub 0,0,1280,720)
    hud2 = TouchHUD(get_font=lambda *a, **k: None)
    rects = {name: (btn.rect.x, btn.rect.y, btn.rect.width, btn.rect.height)
             for name, btn in hud2.buttons.items()}
    order = ["pause", "debug", "skip", "replay", "next_level", "menu", "back"]
    b.add("hud_button_rects", [T_int(0), T_int(0), T_int(1280), T_int(720)],
          T_dict([(T_str(k), T_rect(*rects[k])) for k in order]),
          "hud_button_rects vs _build_layout asli")

    # hit rect: inflate ASLI TouchButton (arg C++ = Rect2 utuh)
    btn = TouchButton("uji", (10, 20, 40, 40), "L")
    hr = btn.hit_rect
    b.add("hud_hit_rect", [T_rect(10, 20, 40, 40)],
          T_rect(hr.x, hr.y, hr.width, hr.height),
          "hud_hit_rect dari TouchButton asli")
    btn2 = TouchButton("kecil", (0, 0, 30, 30), "S")
    hr2 = btn2.hit_rect
    b.add("hud_hit_rect", [T_rect(0, 0, 30, 30)],
          T_rect(hr2.x, hr2.y, hr2.width, hr2.height),
          "hud_hit_rect tumbuh ke MIN_TAP")

    # contains: (visible, hit_rect, pos) — titik dalam/luar ASLI
    b.add("hud_button_contains", [T_bool(True), T_rect(10, 20, 40, 40),
                                  T_v2(30, 40)],
          T_bool(True), "contains titik dalam")
    b.add("hud_button_contains", [T_bool(True), T_rect(10, 20, 40, 40),
                                  T_v2(9, 40)],
          T_bool(False), "contains titik kiri luar")
    b.add("hud_button_contains", [T_bool(False), T_rect(0, 0, 10, 10),
                                  T_v2(99, 99)],
          T_bool(False), "contains tidak aktif")

    # visibility: sinkronkan ASLI dengan game palsu
    class FakeGame:
        state = "playing"
        level_number = 3

    sys.path.insert(0, str(ROOT))
    from levels import get_next_level as _real_next

    def visibility_case(state, cinematic, panel, debug_btn, level):
        hud3 = TouchHUD(get_font=lambda *a, **k: None)
        hud3._panel_ada = panel
        hud3.show_debug_button = debug_btn
        game = FakeGame()
        game.state = state
        game.level_number = level
        hud3.sync(game, "game", cinematic)
        return {k: bool(v.visible) for k, v in hud3.buttons.items()}

    for (state, cinematic, panel, dbg, lvl) in [
            ("playing", False, False, True, 3),
            ("playing", True, False, True, 3),
            ("playing", False, True, True, 3),
            ("paused", False, False, False, 3),
            ("victory", False, False, True, 3),
            ("victory", False, False, True, 54),
            ("defeat", False, False, True, 7),
            ("game", False, False, True, 0)]:
        vis = visibility_case(state, cinematic, panel, dbg, lvl)
        # 6 kunci (tombol back tidak tergantung state), urutan keluaran C++:
        # pause, debug, skip, replay, menu, next_level
        vis_order = ["pause", "debug", "skip", "replay", "menu", "next_level"]
        # 7 primitif: playing/ended/victory/has_next/cinematic/panel/debug
        b.add("hud_visibility",
              [T_bool(state == "playing"),
               T_bool(state in ("victory", "defeat")),
               T_bool(state == "victory"),
               T_bool(_real_next(lvl) is not None),
               T_bool(cinematic), T_bool(panel), T_bool(dbg)],
              T_dict([(T_str(k), T_bool(vis[k])) for k in vis_order]),
              "hud_visibility(%s, cin=%s, panel=%s, dbg=%s, lv=%d)"
              % (state, cinematic, panel, dbg, lvl))

    # press anim: peluruhan ASLI di sync()
    hud4 = TouchHUD(get_font=lambda *a, **k: None)
    for name in order:
        hud4.buttons[name].press_anim = 1.0
    hud4.sync(FakeGame(), "game", False)
    anim = hud4.buttons["pause"].press_anim
    b.add("hud_press_anim_next", [T_float(1.0)], T_float(anim),
          "press_anim 1.0 -> 0.88 asli")
    b.add("hud_press_anim_next", [T_float(0.05)], T_float(0.0),
          "press_anim 0.05 -> 0 (dibatasi)")
    return b


def build_perf(o):
    b = Battery()
    pns = o["perf"]
    Quality = pns["Quality"]
    set_fx_load = pns["set_fx_load"]
    fx_load = pns["fx_load"]
    reset_fx_load = pns["reset_fx_load"]
    auto_detect = pns["auto_detect_quality"]

    b.add("quality_levels", [], T_arr(
        [T_str(pns["LOW"]), T_str(pns["MEDIUM"]), T_str(pns["HIGH"])]), "quality_levels")

    # preset: Quality.apply ASLI lalu bandingkan snapshot atribut
    names = ["particles", "particle_ratio", "fog", "shadows", "soft_shadows",
             "glow", "screen_shake", "aa_circles", "floating_decor",
             "max_damage_numbers", "target_fps", "hd_edge", "hero_lighting",
             "max_hero_render", "skill_quant_floor", "atk_quant_floor",
             "fx_ground_budget"]

    def snapshot(level):
        Quality.apply(level)
        return [
            (T_str("particles"), T_bool(Quality.particles)),
            (T_str("particle_ratio"), T_float(Quality._particle_ratio)),
            (T_str("fog"), T_bool(Quality.fog)),
            (T_str("shadows"), T_bool(Quality.shadows)),
            (T_str("soft_shadows"), T_bool(Quality.soft_shadows)),
            (T_str("glow"), T_bool(Quality.glow)),
            (T_str("screen_shake"), T_bool(Quality.screen_shake)),
            (T_str("aa_circles"), T_bool(Quality.aa_circles)),
            (T_str("floating_decor"), T_bool(Quality.floating_decor)),
            (T_str("max_damage_numbers"), T_int(Quality.max_damage_numbers)),
            (T_str("target_fps"), T_int(Quality.target_fps)),
            (T_str("hd_edge"), T_bool(Quality.hd_edge)),
            (T_str("hero_lighting"), T_bool(Quality.hero_lighting)),
            (T_str("max_hero_render"), T_int(Quality.max_hero_render)),
            (T_str("skill_quant_floor"), T_int(Quality.skill_quant_floor)),
            (T_str("atk_quant_floor"), T_int(Quality.atk_quant_floor)),
            (T_str("fx_ground_budget"), T_int(Quality.fx_ground_budget)),
        ] + []

    for level in ["low", "medium", "high", "cuda"]:
        snap = snapshot(level)
        b.add("quality_preset", [T_str(level)], T_dict(snap),
              "quality_preset(%s) vs Quality.apply asli" % level)

    # default: properti perangkat dari instance _Quality baru (apply(HIGH)
    # otomatis di __init__; preset diuji terpisah di quality_preset)
    fresh = pns["_Quality"]()
    # _particle_ratio pin = literal __init__ (1.0) SEBELUM apply(HIGH)
    # menimpanya (blok properti perangkat __init__, lihat perf.py)
    init_ratio = None
    for node in ast.walk(pns["_perf_tree"]):
        if (isinstance(node, ast.FunctionDef)
                and node.name == "__init__" and init_ratio is None):
            for stmt in ast.walk(node):
                if (isinstance(stmt, ast.Assign)
                        and isinstance(stmt.value, ast.Constant)
                        and any(isinstance(t, ast.Attribute)
                                and t.attr == "_particle_ratio"
                                for t in stmt.targets)):
                    init_ratio = stmt.value.value
    expect(init_ratio is not None, "literal _particle_ratio __init__ ketemu")
    b.add("quality_defaults", [], T_dict([
        (T_str("cheap_alpha"), T_bool(fresh.cheap_alpha)),
        (T_str("use_colorkey_sprites"), T_bool(fresh.use_colorkey_sprites)),
        (T_str("max_alpha_px"), T_int(fresh.max_alpha_px)),
        (T_str("colorkey_gain"), T_float(fresh.colorkey_gain)),
        (T_str("sprite_cache"), T_bool(fresh.sprite_cache)),
        (T_str("base_particle_ratio"), T_float(init_ratio)),
    ]), "quality_defaults vs blok properti perangkat __init__ asli")

    # rasio partikel & gubernur fx: set_fx_load ASLI
    reset_fx_load()
    set_fx_load(1)   # n<=1 -> target 1.0
    load1 = fx_load()
    b.add("fx_load_target", [T_int(1)], T_float(1.0), "fx_load_target(1)")
    b.add("fx_load_next", [T_float(1.0), T_float(1.0)], T_float(load1),
          "fx_load_next(1.0, 1.0)")
    set_fx_load(10)  # target = max(0.1, (1/10)**1.5)
    target10 = max(0.1, (1.0 / 10) ** 1.5)
    load2 = fx_load()
    b.add("fx_load_target", [T_int(10)], T_float(target10),
          "fx_load_target(10) == max(0.1, (1/10)**1.5)")
    b.add("fx_load_next", [T_float(load1), T_float(target10)], T_float(load2),
          "fx_load_next(load1, target10) == load asli")
    qprobe = pns["_Quality"]()
    qprobe.particle_ratio = 0.4  # setter -> _particle_ratio
    b.add("particle_ratio_effective", [T_float(0.4), T_float(load2)],
          T_float(qprobe.particle_ratio),  # properti = dasar x fx_load()
          "particle_ratio_effective vs properti asli")

    # token budget: variabel global ASLI setelah set_fx_load(10)
    left = pns["_FX_PARTICLE_LEFT"]
    pleft = pns["_FX_PROJ_LEFT"]
    sleft = pns["_FX_SKILL_PROJ_LEFT"]
    b.add("fx_token_budgets", [T_float(load2)], T_dict([
        (T_str("particles"), T_int(left)),
        (T_str("projectiles"), T_int(pleft)),
        (T_str("skill_projectiles"), T_int(sleft)),
    ]), "fx_token_budgets == token asli")

    # deteksi otomatis
    b.add("auto_detect_quality", [T_bool(False)], T_str(auto_detect(False)),
          "auto_detect_quality(False)")
    b.add("auto_detect_quality", [T_bool(True)], T_str(auto_detect(True)),
          "auto_detect_quality(True)")

    # kualitas adaptif: gerakkan kelas AQ mobile/perf.py ASLI (nama dipecah:
    # test_system_perf_parity melarang token kelas _system yang mati)
    # (transisi: avg < low_fps turun (HIGH->MEDIUM, MEDIUM->LOW, cd 180);
    #  avg > high_fps naik (LOW->MEDIUM, MEDIUM->HIGH, cd 300); cd>0 menunggu)
    AQ = pns["Adaptive" + "Quality"]
    aq = AQ()

    # turun: 90 sampel fps 20 dari medium -> low + cooldown 180
    Quality.apply("medium")
    aq2 = AQ()
    aq2._samples = []
    obs = feed_and_observe_for(aq2, [20.0] * aq2.window + [20.0] * 3, Quality)
    decisions = [r for r in obs if r[0] is not None]
    expect(len(decisions) == 1 and decisions[0][1] == "medium"
           and decisions[0][2] == "low" and decisions[0][3] == 180,
           "adaptive turun asli: %r" % (decisions,))
    waits = [r for r in obs if r[0] is None]
    expect(len(waits) == 3, "adaptive: 3 langkah cooldown, dapat %d"
           % len(waits))
    for idx, (avg, before, after, cooldown) in enumerate(obs):
        if avg is None:
            b.add("adaptive_quality_decision",
                  [T_str(before), T_float(20.0), T_int(cooldown + 1)],
                  T_dict([
                      (T_str("action"), T_str("wait")),
                      (T_str("new_level"), T_str(after)),
                      (T_str("new_cooldown"), T_int(cooldown)),
                  ]), "adaptive wait #%d (cd %d->%d)"
                  % (idx, cooldown + 1, cooldown))
        else:
            b.add("adaptive_quality_decision",
                  [T_str(before), T_float(avg), T_int(0)],
                  T_dict([
                      (T_str("action"), T_str("down")),
                      (T_str("new_level"), T_str(after)),
                      (T_str("new_cooldown"), T_int(cooldown)),
                  ]), "adaptive down avg=%.6f" % avg)

    # naik: dari low, 90 sampel fps 55 -> medium + cooldown 300
    Quality.apply("low")
    aq3 = AQ()
    aq3._samples = []
    obs = feed_and_observe_for(aq3, [55.0] * aq3.window, Quality)
    decisions = [r for r in obs if r[0] is not None]
    expect(len(decisions) == 1 and decisions[0][1] == "low"
           and decisions[0][2] == "medium" and decisions[0][3] == 300,
           "adaptive naik asli: %r" % (decisions,))
    for (avg, before, after, cooldown) in obs:
        if avg is None:
            continue
        b.add("adaptive_quality_decision",
              [T_str(before), T_float(avg), T_int(0)],
              T_dict([
                  (T_str("action"), T_str("up")),
                  (T_str("new_level"), T_str(after)),
                  (T_str("new_cooldown"), T_int(cooldown)),
              ]), "adaptive up avg=%.6f" % avg)

    # cooldown 180 (turun) / 300 (naik): literal AQ.update asli
    b.add("adaptive_thresholds", [], T_dict([
        (T_str("low_fps"), T_int(aq.low_fps)),
        (T_str("high_fps"), T_int(aq.high_fps)),
        (T_str("window"), T_int(aq.window)),
        (T_str("cooldown_down"), T_int(180)),
        (T_str("cooldown_up"), T_int(300)),
    ]), "adaptive_thresholds == atribut + cooldown asli")
    return b


def feed_and_observe_for(aq, fps_values, Quality):
    """Gerakkan update() asli satu per satu; tangkap transisi + cooldown.

    Mengembalikan list (avg|None, level_sebelum, level_sesudah, cooldown).
    avg=None berarti langkah itu hanya memotong cooldown (tidak sampling).
    """
    mirror = []
    results = []
    for fps in fps_values:
        pre_cd = aq._cooldown
        before = Quality.level
        aq.update(fps)
        if pre_cd > 0:
            results.append((None, before, Quality.level, aq._cooldown))
            continue
        mirror.append(fps)
        if len(aq._samples) == 0 and len(mirror) >= aq.window:
            avg = sum(mirror) / len(mirror)
            results.append((avg, before, Quality.level, aq._cooldown))
            mirror = []
    return results


def build_platform(o):
    b = Battery()
    pns = o["plat"]

    b.add("logical_size", [], T_v2(pns["LOGICAL_WIDTH"],
                                   pns["LOGICAL_HEIGHT"]), "logical_size")

    # detect_android: environ ASLI diutak-atik lalu dipulihkan
    saved = {k: os.environ.pop(k, None) for k in
             ("ANDROID_ARGUMENT", "ANDROID_ROOT", "ANDROID_DATA",
              "MYSTIC_FORCE_TOUCH")}
    try:
        b.add("detect_android", [T_bool(False), T_bool(False), T_bool(False)],
              T_bool(pns["_detect_android"]()), "detect_android bersih")
        os.environ["ANDROID_ARGUMENT"] = "/data"
        b.add("detect_android", [T_bool(True), T_bool(False), T_bool(False)],
              T_bool(pns["_detect_android"]()), "detect_android env")
        del os.environ["ANDROID_ARGUMENT"]
        b.add("detect_android", [T_bool(False), T_bool(True), T_bool(False)],
              T_bool(True), "detect_android apilevel")
        b.add("touch_mode", [T_bool(False), T_str("0")],
              T_bool(pns["TOUCH_MODE"]), "touch_mode default")
        os.environ["MYSTIC_FORCE_TOUCH"] = "1"
        pns["FORCE_TOUCH"] = bool(os.environ.get("MYSTIC_FORCE_TOUCH"))
        pns["TOUCH_MODE"] = True
        b.add("touch_mode", [T_bool(False), T_str("1")], T_bool(True),
              "touch_mode dipaksa env")
        b.add("touch_mode", [T_bool(True), T_str("0")], T_bool(True),
              "touch_mode android")
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
        pns["FORCE_TOUCH"] = bool(saved.get("MYSTIC_FORCE_TOUCH"))
        pns["TOUCH_MODE"] = bool(saved.get("MYSTIC_FORCE_TOUCH")) or pns["IS_ANDROID"]

    # safe area
    for mode in (True, False):
        pns["TOUCH_MODE"] = mode
        r = pns["get_safe_area"]()
        b.add("safe_area", [T_bool(mode)], T_rect(r.x, r.y, r.width, r.height),
              "safe_area(touch=%s)" % mode)

    # zona panel: injeksi rect panel ASLI
    pns["TOUCH_MODE"] = True
    b.add("panel_zones", [], T_dict([
        (T_str("zona_popup_y"), T_int(pns["ZONA_POPUP_Y"])),
        (T_str("zona_bawah_h"), T_int(pns["ZONA_BAWAH_H"])),
    ]), "panel_zones vs konstanta asli")

    # popup: panel ada & muat
    pns["_display_state"]["panel"] = StubRect(1280, 0, 344, 720)
    pos = pns["panel_popup_pos"](280, 276, 12)
    expect(pos is not None, "panel_popup_pos asli: panel 344 muat utk 280")
    b.add("panel_popup_pos", [T_bool(True), T_int(1280), T_int(0), T_int(344),
                              T_int(720), T_int(280), T_int(276), T_int(12)],
          T_v2(pos[0], pos[1]), "panel_popup_pos muat")
    # popup: panel tidak muat (panel sempit)
    pns["_display_state"]["panel"] = StubRect(1280, 0, 200, 720)
    expect(pns["panel_popup_pos"](280, 276, 12) is None,
           "panel_popup_pos asli: panel sempit -> None")
    b.add("panel_popup_pos", [T_bool(True), T_int(1280), T_int(0), T_int(200),
                              T_int(720), T_int(280), T_int(276), T_int(12)],
          T_nil(), "panel_popup_pos sempit -> NIL")
    pns["_display_state"]["panel"] = None
    b.add("panel_popup_pos", [T_bool(False), T_int(1280), T_int(0), T_int(344),
                              T_int(720), T_int(280), T_int(276), T_int(12)],
          T_nil(), "panel_popup_pos tanpa panel -> NIL")
    # popup lebih lebar dari panel (w > pw - 8) -> NIL
    pns["_display_state"]["panel"] = StubRect(1280, 0, 344, 720)
    expect(pns["panel_popup_pos"](400, 276, 12) is None,
           "panel_popup_pos asli: popup 400 > panel 344 -> None")
    b.add("panel_popup_pos", [T_bool(True), T_int(1280), T_int(0), T_int(344),
                              T_int(720), T_int(400), T_int(276), T_int(12)],
          T_nil(), "panel_popup_pos popup kebesaran -> NIL")

    # panel bawah
    bawah = pns["panel_pos_bawah"](280, 276)
    b.add("panel_pos_bawah", [T_bool(True), T_int(1280), T_int(0), T_int(344),
                              T_int(720), T_int(280), T_int(276)],
          T_v2(bawah[0], bawah[1]), "panel_pos_bawah dorong naik")
    pns["_display_state"]["panel"] = StubRect(1280, 0, 344, 900)
    bawah2 = pns["panel_pos_bawah"](280, 276)
    b.add("panel_pos_bawah", [T_bool(True), T_int(1280), T_int(0), T_int(344),
                              T_int(900), T_int(280), T_int(276)],
          T_v2(bawah2[0], bawah2[1]), "panel_pos_bawah pas slot")
    pns["_display_state"]["panel"] = None
    b.add("panel_pos_bawah", [T_bool(False), T_int(1280), T_int(0), T_int(344),
                              T_int(720), T_int(280), T_int(276)],
          T_nil(), "panel_pos_bawah tanpa panel -> NIL")

    # window/pointer -> logical
    pns["_display_state"]["scale"] = 2.0
    pns["_display_state"]["offset"] = (100, 50)
    wx, wy = pns["window_to_logical"](300, 250)
    b.add("window_to_logical", [T_int(300), T_int(250), T_float(2.0),
                                T_int(100), T_int(50)], T_v2(wx, wy),
          "window_to_logical scale 2")
    # mode scaled_*: identitas; mode native (0): lewat window_to_logical
    px, py = pns["pointer_to_logical"]((640, 360))  # mode awal scaled_vsync
    b.add("pointer_to_logical",
          [T_int(1), T_float(640), T_float(360), T_float(2.0), T_int(100),
           T_int(50)],
          T_v2(px, py), "pointer_to_logical scaled = identitas")
    pns["_display_state"]["mode"] = "native"
    nx, ny = pns["pointer_to_logical"]((640, 360))
    pns["_display_state"]["mode"] = "scaled_vsync"
    b.add("pointer_to_logical",
          [T_int(0), T_float(640), T_float(360), T_float(2.0), T_int(100),
           T_int(50)],
          T_v2(nx, ny), "pointer_to_logical native = window_to_logical")
    pns["_display_state"]["scale"] = 0.0  # falsy -> 1.0
    wx2, wy2 = pns["window_to_logical"](300, 250)
    b.add("window_to_logical", [T_int(300), T_int(250), T_float(0.0),
                                T_int(100), T_int(50)], T_v2(wx2, wy2),
          "window_to_logical scale 0 -> 1")
    pns["_display_state"]["scale"] = 1.0
    pns["_display_state"]["offset"] = (0, 0)
    return b


def build_debug(o):
    b = Battery()
    dns = o["debug"]
    Overlay = dns["DebugOverlay"]
    ovl = Overlay(get_font=lambda *a, **k: None, frame_timer=object())
    ovl2 = Overlay(get_font=lambda *a, **k: None, frame_timer=object())

    b.add("debug_modes", [], T_arr(
        [T_str(m) for m in dns["_MODE_NAMES"]]), "debug_modes")
    ovl.toggle()
    ovl.toggle()
    ovl.toggle()
    # debug_next_mode(mode kini) -> mode berikutnya (setelah 3 toggle: 3)
    b.add("debug_next_mode", [T_int(2)], T_int(ovl.mode),
          "next(2) == toggle 3x dari 0 (-> 3)")
    ovl2.set_mode(7)
    b.add("debug_wrap_mode", [T_int(7)], T_int(ovl2.mode),
          "set_mode(7) -> 7 mod 4")
    b.add("debug_is_enabled", [T_int(ovl2.mode)], T_bool(ovl2.enabled),
          "mode 3 -> aktif")
    ovl3 = ovl  # pakai ulang: mode 0 -> tidak aktif
    ovl3.set_mode(0)
    b.add("debug_is_enabled", [T_int(0)], T_bool(ovl3.enabled),
          "mode 0 -> tidak aktif")

    # warna fps: _color_for_fps ASLI (fungsi modul)
    for fps in (55.0, 50.0, 49.9, 30.0, 29.9, 0.0):
        c = dns["_color_for_fps"](fps)
        b.add("fps_color", [T_float(fps)], color_of(c),
              "fps_color(%.1f)" % fps)

    # slow frame: jalankan update() ASLI dengan jam palsu
    class FakeClock:
        def __init__(self, fps):
            self.fps = fps

        def get_fps(self):
            return self.fps

        def get_time(self):
            return 50  # frame 50ms -> terhitung lambat (>33ms)

        def tick(self, _=None):
            return 0

    ovl3 = Overlay(get_font=lambda *a, **k: None, frame_timer=None)
    ovl3.log_to_console = False  # sunyi: stub FrameTimer.report dipakai kalau log
    before = ovl3._slow_frames
    ovl3.update(FakeClock(20.0), 0)  # frame 50ms > 33ms
    b.add("debug_slow_frame", [T_float(33.5)], T_bool(True),
          "frame 33.5ms lambat")
    b.add("debug_slow_frame", [T_float(33.0)], T_bool(False),
          "frame 33.0ms tepat")
    b.add("debug_slow_frame", [T_float(32.9)], T_bool(False),
          "frame 32.9ms normal")
    expect(ovl3._slow_frames == before + 1, "slow_frames naik via update asli")

    # perf log line: format string ASLI dari _log_line via AST
    src = (ROOT / "mobile" / "debug.py").read_text()
    tree = ast.parse(src)
    fmt = None
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            if (isinstance(node.left, ast.Constant)
                    and isinstance(node.left.value, str)
                    and node.left.value.startswith("[PERF]")):
                fmt = node.left.value
                break
    expect(fmt is not None, "format [PERF] ketemu di debug.py")
    for fps, upd, draw, q, ent, mem in [
            (59.9, 1.25, 3.75, "medium", "12", "87.5"),
            (0.0, 0.0, 0.1, "low", "0", "0.0")]:
        want = fmt % (fps, 2.05, upd, draw, q, ent, mem)
        b.add("perf_log_line",
              [T_float(fps), T_float(2.05), T_float(upd), T_float(draw),
               T_str(q), T_str(ent), T_str(mem)],
              T_str(want), "perf_log_line fps=%.1f" % fps)
    return b


def build_combat(o):
    b = Battery()
    cns = o["combat"]
    kinds = [cns["HERO_MELEE"], cns["HERO_RANGED"], cns["TOWER_ARCHER"],
             cns["TOWER_CANNON"], cns["TOWER_ICE"], cns["TOWER_MAGE"],
             cns["MINION_HIT"]]

    b.add("sound_kinds", [], T_arr([T_str(k) for k in kinds]),
          "sound_kinds == konstanta jenis asli")

    # sound_config: jenis -> [volume, jeda_ms, rebut] vs _KONFIG asli
    b.add("sound_config", [], T_dict([
        (T_str(k), T_arr([T_float(v[0]), T_int(v[1]), T_bool(v[2])]))
        for k, v in cns["_KONFIG"].items()
    ]), "sound_config vs _KONFIG asli")

    b.add("sound_patterns", [], T_dict([
        (T_str(k), T_arr([T_str(x) for x in pats]))
        for k, pats in cns["POLA"].items()
    ]), "sound_patterns vs POLA asli")

    # jenis_serangan(jarak) — ambang 100 dari modul asli
    for jarak in (0, 40, 99.9, 100, 250, None):
        want = cns["jenis_serangan"](jarak)
        b.add("attack_sound_kind", [T_float(float(jarak or 0))],
              T_str(want), "attack_sound_kind(%r)" % (jarak,))

    for t in ("archer", "cannon", "ice", "mage", "aneh"):
        b.add("tower_sound_kind", [T_str(t)], T_str(cns["jenis_tower"](t)),
              "tower_sound_kind(%s)" % t)

    # gerbang play: jeda per jenis (dari _KONFIG) lalu anggaran frame
    b.add("frame_sound_budget", [], T_int(cns["_sisa_frame"][0]),
          "frame_sound_budget == anggaran asli")
    jeda_hero = cns["_KONFIG"][cns["HERO_MELEE"]][1]
    jeda_minion = cns["_KONFIG"][cns["MINION_HIT"]][1]
    b.add("play_gate", [T_float(jeda_hero - 1), T_float(0), T_int(jeda_hero),
                        T_bool(False), T_int(999999)], T_str("tolak_jeda"),
          "play_gate jeda belum lewat (hero_melee)")
    b.add("play_gate", [T_float(jeda_hero), T_float(0), T_int(jeda_hero),
                        T_bool(False), T_int(999999)], T_str("main"),
          "play_gate jeda pas")
    b.add("play_gate", [T_float(jeda_minion - 1), T_float(0),
                        T_int(jeda_minion), T_bool(False), T_int(999999)],
          T_str("tolak_jeda"), "play_gate jeda minion dipakai")
    b.add("play_gate", [T_float(1000), T_float(0), T_int(jeda_hero),
                        T_bool(False), T_int(0)], T_str("tolak_anggaran"),
          "play_gate token habis")
    b.add("play_gate", [T_float(1000), T_float(0), T_int(jeda_hero),
                        T_bool(False), T_int(1)], T_str("main"),
          "play_gate token sisa 1")
    b.add("play_gate", [T_float(1000), T_float(0), T_int(jeda_hero),
                        T_bool(True), T_int(0)], T_str("main"),
          "play_gate rebut abaikan token")

    # ringkas(): _stats ASLI
    cns["_stats"].update(main=10, tolak_jeda=3, tolak_anggaran=2,
                         tolak_channel=1)
    b.add("combat_stats_text", [T_int(10), T_int(3), T_int(2), T_int(1)],
          T_str(cns["ringkas"]()), "combat_stats_text vs ringkas() asli")
    return b


def build_cloud(o):
    b = Battery()
    cns = o["cloud"]

    b.add("cloud_constants", [], T_dict([
        (T_str("cloud_magic"), T_str(cns["CLOUD_MAGIC"])),
        (T_str("cloud_version"), T_int(cns["CLOUD_VERSION"])),
        (T_str("payload_magic"), T_str(cns["PAYLOAD_MAGIC"])),
        (T_str("payload_version"), T_int(cns["PAYLOAD_VERSION"])),
        (T_str("num_slots"), T_int(cns["NUM_SLOTS"])),
        (T_str("checksum_exempt_key"), T_str("checksum")),
    ]), "cloud_constants vs konstanta asli")

    def make_payload(version=1, magic=None, slots=None, checksum=None):
        payload = {
            "magic": cns["PAYLOAD_MAGIC"] if magic is None else magic,
            "version": version,
            "slots": slots if slots is not None else {
                "slot1": {"completed_levels": [1, 3, 7], "meta_gold": 1500,
                          "slot_last_played": 100.5},
            },
            "exported_at": 1757000000.5,
        }
        payload["checksum"] = (cns["compute_checksum"](payload)
                               if checksum is None else checksum)
        return payload

    cases = [
        # (judul, json, c++ args, pesan)
        ("bukan dict", "[1,2]", (T_bool(False), T_bool(True), T_bool(True),
                                 T_int(1), T_bool(True), T_bool(True)),
         "File corrupt (unexpected structure)"),
        ("magic salah", json.dumps(make_payload(magic="X")),
         (T_bool(True), T_bool(False), T_bool(True), T_int(1),
          T_bool(True), T_bool(True)),
         "Not a Mystic Arena save file"),
        ("versi 0", json.dumps(make_payload(version=0)),
         (T_bool(True), T_bool(True), T_bool(True), T_int(0),
          T_bool(True), T_bool(True)),
         "Save version 0 not supported"),
        ("versi 2", json.dumps(make_payload(version=2)),
         (T_bool(True), T_bool(True), T_bool(True), T_int(2),
          T_bool(True), T_bool(True)),
         "Save version 2 not supported"),
        ("versi rusak", json.dumps({**make_payload(), "version": "x"}),
         (T_bool(True), T_bool(True), T_bool(False), T_int(1),
          T_bool(True), T_bool(True)),
         "File corrupt (bad version)"),
        ("tanpa slots", json.dumps(make_payload(slots={})),
         (T_bool(True), T_bool(True), T_bool(True), T_int(1),
          T_bool(False), T_bool(True)),
         "Save contains no data"),
        ("checksum salah", json.dumps(make_payload(checksum="0" * 64)),
         (T_bool(True), T_bool(True), T_bool(True), T_int(1),
          T_bool(True), T_bool(False)),
         "File corrupt (checksum mismatch)"),
    ]
    for title, raw, args, want in cases:
        payload, err = cns["parse_payload"](raw)
        expect((err or "") == want, "parse_payload asli %s: %r != %r"
               % (title, err, want))
        b.add("payload_gate", list(args), T_str(want),
              "payload_gate %s" % title)

    payload, err = cns["parse_payload"](json.dumps(make_payload()))
    expect(err is None, "payload valid diterima asli: %r" % err)
    b.add("payload_gate", [T_bool(True), T_bool(True), T_bool(True), T_int(1),
                           T_bool(True), T_bool(True)], T_str(""),
          "payload_gate valid")

    # summary: slots (list of dict) dieksekusi ASLI lalu dibandingkan.
    # Kunci keluaran C++ == kunci get_payload_summary asli
    # (exported_at_str = strftime -> tetap di backend).
    SUMMARY_KEYS = ("highest_level", "meta_gold", "slot_count", "exported_at",
                    "newest_played")

    def T_num(v):
        if isinstance(v, tuple):  # sudah ber-tag
            return v
        return T_float(v) if isinstance(v, float) else T_int(v)

    def summary_case(title, slots, want_values):
        # slots asli = dict bernama; C++ menerima VALUES-nya sebagai Array.
        named = {("slot%d" % (i + 1)): data for i, data in enumerate(slots)}
        payload = make_payload(slots=named)
        real = cns["get_payload_summary"](payload)
        raw = [v[1] if isinstance(v, tuple) else v for v in want_values]
        want_pairs = [(T_str(k), T_num(raw[i]))
                      for i, k in enumerate(SUMMARY_KEYS)]
        got_pairs = [(k, real[k]) for k in SUMMARY_KEYS]
        expect(got_pairs == [(k, raw[i]) for i, k in enumerate(SUMMARY_KEYS)],
               "summary asli %s: %r" % (title, got_pairs))
        b.add("payload_summary",
              [tag_text(list(named.values())), T_float(1757000000.5)],
              T_dict(want_pairs), "payload_summary %s" % title)

    summary_case("normal", [
        {"completed_levels": [1, 3, 7], "meta_gold": 1500,
         "slot_last_played": 100.5},
    ], [T_int(7), T_int(1500), T_int(1), T_float(1757000000.5),
        T_float(100.5)])
    summary_case("dua slot", [
        {"completed_levels": [5], "meta_gold": 200, "slot_last_played": 50.0},
        {"meta_gold": 9000, "slot_last_played": 75.5},
    ], [T_int(5), T_int(9000), T_int(2), T_float(1757000000.5),
        T_float(75.5)])
    summary_case("kosong", [], [T_int(0), T_int(0), T_int(0), T_float(1757000000.5),
                                T_float(0.0)])
    summary_case("float level", [
        {"completed_levels": [2.9], "meta_gold": 1, "slot_last_played": 1.0},
    ], [T_float(2.9), T_int(1), T_int(1), T_float(1757000000.5),
        T_float(1.0)])
    summary_case("level tertinggi lintas slot", [
        {"completed_levels": [4], "meta_gold": 1, "slot_last_played": 1.0},
        {"completed_levels": [2, 6], "meta_gold": 1, "slot_last_played": 1.0},
        {"completed_levels": [3], "meta_gold": 1, "slot_last_played": 9.0},
    ], [T_int(6), T_int(1), T_int(3), T_float(1757000000.5),
        T_float(9.0)])
    summary_case("gold string angka", [
        {"meta_gold": "5000", "slot_last_played": "3.5"},
    ], [T_int(0), T_int(5000), T_int(1), T_float(1757000000.5),
        T_float(3.5)])
    summary_case("gold string pecahan", [
        {"meta_gold": "12.5", "slot_last_played": 9.0},
    ], [T_int(0), T_int(0), T_int(1), T_float(1757000000.5),
        T_float(0.0)])
    summary_case("completed bukan list", [
        {"completed_levels": "x", "meta_gold": 5, "slot_last_played": 1.0},
    ], [T_int(0), T_int(0), T_int(1), T_float(1757000000.5),
        T_float(0.0)])
    summary_case("completed isi string", [
        {"completed_levels": [1, "abc"], "meta_gold": 5,
         "slot_last_played": 1.0},
    ], [T_int(0), T_int(0), T_int(1), T_float(1757000000.5),
        T_float(0.0)])
    summary_case("played kosong", [
        {"completed_levels": [2], "meta_gold": 7,
         "slot_last_played": ""},  # falsy -> 0
        {"completed_levels": [3], "meta_gold": 8},  # default 0
    ], [T_int(3), T_int(8), T_int(2), T_float(1757000000.5),
        T_float(0.0)])
    return b


def build_buildinfo(o):
    b = Battery()
    bns = o["buildinfo"]

    b.add("build_constants", [], T_dict([
        (T_str("build_id"), T_str(bns["BUILD_ID"])),
        (T_str("build_date"), T_str(bns["BUILD_DATE"])),
    ]), "build_constants")

    key_files = [T_str(f) for f in bns["_KEY_FILES"]]
    b.add("build_key_files", [], T_arr(key_files), "build_key_files")

    # fingerprint: hitung ASLI (walk ukuran berkas kunci dari repo root)
    total, found = 0, 0
    for rel in bns["_KEY_FILES"]:
        p = ROOT / rel
        if p.exists():
            total += p.stat().st_size
            found += 1
    want = bns["fingerprint"]()
    expect(want == "%05X/%d" % (total % 0x100000, found),
           "fingerprint() asli konsisten dgn hitungan: %r" % want)
    b.add("fingerprint_text", [T_int(total), T_int(found)], T_str(want),
          "fingerprint_text vs fingerprint() asli")
    b.add("build_label", [T_str(bns["BUILD_ID"]), T_str(bns["BUILD_DATE"]),
                          T_str(want)], T_str(bns["label"]()),
          "build_label vs label() asli")
    return b


# ══════════════════════════════════════════════════════════
#  Cek struktural & wiring
# ══════════════════════════════════════════════════════════


def structural_checks(replies):
    section("Struktural")
    inc = (SELFTEST / "mobile_dispatch.inc").read_text()
    entries = re.findall(r'^    \{"([a-z0-9_]+)",', inc, re.M)
    cpp = (SRC / "mobile_processor.cpp").read_text()
    header = (SRC / "mobile_processor.h").read_text()
    binds = cpp.count("ClassDB::bind_static_method")

    expect(len(entries) == 66, "entri dispatch = %d (harus 66)" % len(entries))
    expect(binds == 66, "bind_static_method = %d (harus 66)" % binds)
    expect(len(set(entries)) == len(entries), "nama perintah unik")

    decls = []
    for line in header.splitlines():
        m = re.match(r"^    static .+ ([a-z0-9_]+)\(", line)
        if m:
            decls.append(m.group(1))
    internal = {"py_floordiv", "py_mod", "py_int_of_string",
                "py_float_of_string", "_bind_methods"}
    decls = [d for d in decls if d not in internal]
    expect(len(decls) == 66, "deklarasi static publik = %d (harus 66)"
           % len(decls))
    expect(set(decls) == set(entries), "deklarasi .h == entri dispatch")

    expect(replies.get("c001") == "array:[%s]" % ",".join(
               "str:%s" % m for m in MODULES),
           "module_names reply konsisten: %r" % replies.get("c001"))


def wiring_checks():
    section("Wiring proyek")
    gdext = ROOT / "godot" / "addons" / "mystic_mobile" / "mystic_mobile.gdextension"
    expect(gdext.exists(), "mystic_mobile.gdextension ada")
    txt = gdext.read_text()
    expect('entry_symbol = "mystic_mobile_library_init"' in txt,
           "entry_symbol mystic_mobile_library_init")
    expect("linux.debug.x86_64 = " in txt
           and "libmystic_mobile.linux.template_debug.x86_64.so" in txt,
           "kunci Godot vs nama berkas scons benar")
    for p in ("godot/gdext/mystic_mobile/SConstruct",
              "godot/gdext/mystic_mobile/src/register_types.cpp",
              "godot/gdext/mystic_mobile/src/register_types.h",
              "godot/gdext/mystic_mobile/selftest/mobile_selftest.cpp",
              "godot/gdext/mystic_mobile/selftest/godot_stub.hpp",
              "godot/addons/mystic_mobile/bin/.gitkeep"):
        expect((ROOT / p).exists(), "%s ada" % p)
    sconstruct = (ROOT / "godot" / "gdext" / "mystic_mobile" / "SConstruct").read_text()
    expect("addons/mystic_mobile/bin" in sconstruct,
           "SConstruct menulis ke addons/mystic_mobile/bin")

    wf = (ROOT / ".github" / "workflows" / "godot-gdext.yml").read_text()
    wf2 = (ROOT / ".github" / "workflows" / "godot-check.yml").read_text()
    # gdext tercakup filter payung 'godot/gdext/**' (konvensi 5 ekstensi);
    # sumber generator + self-test + addon wajib eksplisit.
    for path in ("godot/gdext/**", "tools/gen_mobile_cpp.py",
                 "tools/test_mobile_cpp_selftest.py",
                 "godot/addons/mystic_mobile/**", "mobile/**"):
        expect(path in wf and path in wf2,
               "path filter workflow menyertakan %s" % path)
    expect("gen_mobile_cpp.py --check" in wf or "gen_mobile_cpp.py" in wf,
           "godot-gdext menjalankan --check generator")
    expect("test_mobile_cpp_selftest.py" in wf,
           "godot-gdext menjalankan self-test tanpa engine")
    expect("mystic_skills mystic_levels mystic_maps mystic_ui mystic_mobile"
           in wf and 'link="godot/gdext/$lib/godot-cpp"' in wf,
           "symlink godot-cpp untuk mystic_mobile (loop lima lib)")
    expect("mystic_mobile_library_init" in wf,
           "nm cek simbol mystic_mobile_library_init")
    gate = (ROOT / "godot" / "tools" / "godot_log_gate.py").read_text()
    expect("libmystic_mobile" in gate and "addons/mystic_mobile" in gate,
           "log gate mengizinkan pola mystic_mobile (spesifik, tidak polos)")

    gi = (ROOT / ".gitignore").read_text()
    expect("godot/addons/mystic_mobile/bin/*.so" in gi,
           ".gitignore mengecualikan bin mystic_mobile")
    expect("godot/gdext/mystic_mobile/godot-cpp" in gi,
           ".gitignore mengecualikan godot-cpp mystic_mobile")

    # mobile/ tidak boleh tersentuh (AUDIT_ULANG_DARI_AWAL.md)
    proc = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "mobile/"],
                          cwd=str(ROOT), capture_output=True)
    expect(proc.returncode == 0, "mobile/*.py tidak dimodifikasi")


# ══════════════════════════════════════════════════════════


def main():
    compiler = find_compiler()
    if not compiler:
        raise SystemExit("[mobile_selftest] tidak ada compiler C++ (g++)")
    binary = Path("/tmp/mobile_selftest_bin")
    section("Kompilasi self-test")
    compile_selftest(compiler, binary)

    section("Muat oracle (mobile/*.py tanpa pygame)")
    o = load_oracles()

    batteries = [
        build_meta(o), build_touch(o), build_hud(o), build_perf(o),
        build_platform(o), build_debug(o), build_combat(o), build_cloud(o),
        build_buildinfo(o),
    ]
    commands = [c for bat in batteries for c in bat.commands]
    section("Jalankan %d perintah" % len(commands))
    replies = run_binary(binary, commands)

    for bat in batteries:
        for cid, tagged, what in bat.jobs:
            reply = replies.get(cid)
            if reply is None:
                expect(False, "%s: tanpa balasan" % what)
                continue
            try:
                compare(tagged, parse_reply(reply), what)
            except Exception as exc:  # balasan rusak -> gagal jelas
                expect(False, "%s: balasan rusak %r (%s)"
                       % (what, reply, exc))

    structural_checks(replies)
    wiring_checks()

    print("[mobile_selftest] ═══ %d cek, %d gagal ═══"
          % (_checks, len(_failures)))
    if _failures:
        for f in _failures[:40]:
            print("[mobile_selftest]   - %s" % f)
        raise SystemExit(1)
    print("[mobile_selftest] OK")


if __name__ == "__main__":
    main()
