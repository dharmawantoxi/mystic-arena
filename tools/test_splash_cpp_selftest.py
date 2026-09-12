#!/usr/bin/env python3
"""Self-test splash_processor.cpp di luar engine (butuh g++ saja, tanpa godot-cpp).

    python3 tools/test_splash_cpp_selftest.py

Menyalakan kode C++ hasil tools/gen_splash_cpp.py APA ADANYA lewat stub Variant
(godot/gdext/mystic_splash/selftest), lalu membandingkan balasannya dengan
oracle:

  * godot/tests/fixtures/splash_parity.json — direkam tools/
    test_godot_splash_parity.py dari splash_screen.py ASLI headless (surface
    spy): timeline fade/skip, 46 partikel ber-seed + 120 langkah update +
    triplet gambar, batang gradien + bingkai vignette + sampel piksel latar,
    geometri logo, lapisan glow judul + garis aksen, posisi/alpha hint;
  * cermin Python rumus di sini HANYA untuk semantik port Godot
    (overall_alpha_godot/is_done_godot) yang memang bukan perilaku pygame —
    keduanya dikunci A/B engine di tests/SplashGdextParityTest;
  * built-in Python: int() trunc, round() half-to-even, min/max/clamp.

Pola tools/test_ui_cpp_selftest.py (FASE 36). Sengaja jalan SEBELUM build
godot-cpp di CI: regresi model splash gagal cepat (±detik) dan murah.

Tiga invarian struktural ikut dikunci:

  * jumlah entri splash_dispatch.inc == bind_static_method di _bind_methods
    == deklarasi publik splash_processor.h;
  * setiap fungsi ter-bind WAJIB dipakai minimal satu perintah (closed-world);
  * module_names() == ["splash_screen"] dan api_signature() menyebut jumlah
    fungsi yang sama dengan tabel perintah.
"""
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SELFTEST = ROOT / "godot" / "gdext" / "mystic_splash" / "selftest"
SRC = ROOT / "godot" / "gdext" / "mystic_splash" / "src"
FIXTURE = ROOT / "godot" / "tests" / "fixtures" / "splash_parity.json"

DT = 1.0 / 60.0
TOL = 1e-6

_checks = 0
_failures = []


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[splash_selftest] FAIL: %s" % message)


def section(title):
    print("[splash_selftest] ── %s ──" % title)


# ══════════════════════════════════════════════════════════
#  Parser teks Variant (balasan protokol)
# ══════════════════════════════════════════════════════════


def _split_top(text, sep):
    out, cur, depth = [], [], 0
    for ch in text:
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur))
    return out


def _split_atoms(inner):
    raw = _split_top(inner, ",")
    out = []
    for part in raw:
        if out and not re.match(
                r"^(nil|bool:|int:|float:|str:|color:|v2:|rect:|v2s:|pc:|"
                r"array:|dict:|\[|\{)", part):
            out[-1] += "," + part
        else:
            out.append(part)
    return out


def _find_top_eq(part):
    depth = 0
    for i, ch in enumerate(part):
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        elif ch == "=" and depth == 0:
            return i
    raise ValueError("dict tanpa '=': %r" % part)


def parse_reply(text):
    if text is None:
        return None
    if text.startswith("error:"):
        return ("ERROR", text[6:])
    if text == "nil:null":
        return None
    if text.startswith("bool:"):
        return text[5:] == "true"
    if text.startswith("int:"):
        return int(text[4:])
    if text.startswith("float:"):
        return float(text[6:])
    if text.startswith("str:"):
        return text[4:]
    if text.startswith("color:"):
        return tuple(int(v) for v in text[6:].split(","))
    if text.startswith("v2:"):
        return tuple(float(v) for v in text[3:].split(","))
    if text.startswith("rect:"):
        return tuple(float(v) for v in text[5:].split(","))
    if text.startswith("array:["):
        inner = text[7:-1]
        return [parse_reply(p) for p in _split_atoms(inner)] if inner else []
    if text.startswith("dict:{"):
        inner = text[6:-1]
        out = {}
        for part in (_split_atoms(inner) if inner else []):
            eq = _find_top_eq(part)
            out[parse_reply(part[:eq])] = parse_reply(part[eq + 1:])
        return out
    raise ValueError("balasan tak dikenal: %r" % text[:80])


# ══════════════════════════════════════════════════════════
#  Encoding argumen ke teks protokol
# ══════════════════════════════════════════════════════════


def enc(value):
    if isinstance(value, bool):
        return "bool:true" if value else "bool:false"
    if isinstance(value, int):
        return "int:%d" % value
    if isinstance(value, float):
        return "float:%.17g" % value
    if isinstance(value, str):
        return "str:" + value
    if isinstance(value, tuple) and len(value) == 5 and value[0] == "c8":
        return "color:%d,%d,%d,%d" % value[1:]
    if isinstance(value, tuple) and len(value) == 2 and value[0] == "v2":
        return "v2:%.17g,%.17g" % value[1]
    if isinstance(value, tuple) and len(value) == 2 and value[0] == "rect":
        return "rect:%.17g,%.17g,%.17g,%.17g" % value[1]
    raise ValueError("tipe argumen tak didukung: %r" % (value,))


def c8(rgb, alpha=255):
    return ("c8", int(rgb[0]), int(rgb[1]), int(rgb[2]), int(alpha))


def v2(x, y):
    return ("v2", (float(x), float(y)))


def rect(x, y, w, h):
    return ("rect", (float(x), float(y), float(w), float(h)))


# ══════════════════════════════════════════════════════════
#  Pembanding
# ══════════════════════════════════════════════════════════


def close(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= TOL
    return a == b


def compare(cid, expected, got):
    if isinstance(expected, tuple) and expected and expected[0] == "c8":
        expected = list(expected[1:])
    if isinstance(expected, dict) and isinstance(got, dict):
        if set(expected) != set(got):
            expect(False, "%s: kunci dict beda: %s vs %s"
                   % (cid, sorted(expected), sorted(got)))
            return
        for key in expected:
            compare("%s.%s" % (cid, key), expected[key], got[key])
        return
    if isinstance(expected, list) and isinstance(got, list):
        if len(expected) != len(got):
            expect(False, "%s: panjang list %d != %d"
                   % (cid, len(expected), len(got)))
            return
        for i, (e, g) in enumerate(zip(expected, got)):
            compare("%s[%d]" % (cid, i), e, g)
        return
    if isinstance(expected, tuple):
        expected = list(expected)
    if isinstance(got, tuple):
        got = list(got)
    expect(close(expected, got),
           "%s: %r != %r" % (cid, expected, got))


# ══════════════════════════════════════════════════════════
#  Perintah uji
# ══════════════════════════════════════════════════════════


def build_commands(fx):
    cmds = []
    cid = 0

    def add(fn, args, expected):
        nonlocal cid
        cid += 1
        name = "c%05d" % cid
        cmds.append((name, fn, [enc(a) for a in args], expected))
        return name

    c = fx["constants"]
    t = c["timings"]

    # ── meta ──
    add("module_names", [], ["splash_screen"])
    add("api_signature", [], "splash_v1:1mod:62fn:")
    add("module_names_string", [], "splash_screen")
    add("game_name", [], c["game_name"])
    add("tagline", [], c["tagline"])
    add("hint_text", [], c["hint_text"])
    add("splash_duration", [], c["duration"])
    add("logo_paths", [], c["logo_paths"])
    add("accent", [], c8(c["accent"]))
    add("accent_2", [], c8(c["accent_2"]))
    add("text_main", [], c8(c["text_main"]))
    add("text_dim", [], c8(c["text_dim"]))
    add("gradient_stops", [], {"top": c8(c["gradient"]["top"]),
                               "mid": c8(c["gradient"]["mid"]),
                               "bot": c8(c["gradient"]["bot"])})
    add("particle_colors", [], [c8(p) for p in c["particle_colors"]])
    add("font_sizes", [], c["font_sizes"])
    add("font_fallback_sizes", [], c["font_fallback_sizes"])
    add("font_styles", [], c["font_styles"])
    add("particle_count", [], c["particle_count"])
    ranges = c["particle_ranges"]
    add("particle_ranges", [], {"r_lo": ranges["r"][0], "r_hi": ranges["r"][1],
                                "speed_lo": ranges["speed"][0],
                                "speed_hi": ranges["speed"][1],
                                "drift_lo": ranges["drift"][0],
                                "drift_hi": ranges["drift"][1],
                                "phase_lo": ranges["phase"][0],
                                "phase_hi": ranges["phase"][1]})
    add("timings", [], t)

    # ── timing & state dari timeline pygame ──
    for scen in fx["timeline"]:
        rows = scen["rows"]
        for idx in (0, 5, 20, 29, 30, 31, 40, 60, 90, 120, 150, 179, 180,
                    181, 199):
            row = rows[idx]
            elapsed, title_a, overall, done = row[0], row[1], row[2], row[3]
            # skip() hanya menyetel bendera; `done` baru dihitung update()
            # frame BERIKUTnya. Karena itu done memakai bendera saat update
            # (row[4]) sementara alpha memakai bendera saat direkam (row[5]).
            skipped_update = bool(row[4])
            skipped_alpha = bool(row[5])
            add("title_alpha", [elapsed], title_a)
            add("overall_alpha", [elapsed, skipped_alpha], overall)
            add("is_done", [elapsed, skipped_update], done)
            add("draw_visible", [overall], overall > t["alpha_epsilon"])
            # semantik port Godot (skip_t sejak skip) — cermin, bukan pygame
            skip_t = max(0.0, elapsed - (scen["skip_at"] or 0.0)) \
                if skipped_alpha else 0.0
            skip_t_u = max(0.0, elapsed - (scen["skip_at"] or 0.0)) \
                if skipped_update else 0.0
            if skipped_alpha:
                fade_out = max(0.0, 1.0 - skip_t / t["skip_fade"])
            else:
                fade_out = min(1.0, max(0.0, (t["duration"] - elapsed)
                                        / t["fade_out"]))
            done_g = (skip_t_u >= t["skip_done"]) if skipped_update \
                else (elapsed >= t["duration"])
            fade_in_v = min(1.0, elapsed / t["fade_in"])
            add("overall_alpha_godot", [elapsed, skipped_alpha, skip_t],
                max(0.0, min(1.0, fade_in_v * fade_out)))
            add("is_done_godot", [elapsed, skipped_update, skip_t_u], done_g)
            add("fade_in", [elapsed], fade_in_v)
            add("fade_out_normal", [elapsed],
                min(1.0, max(0.0, (t["duration"] - elapsed) / t["fade_out"])))
            add("fade_out_skip", [elapsed],
                max(0.0, 1.0 - elapsed / t["skip_fade"]))
            add("title_alpha_drawn", [title_a, overall],
                int(title_a * overall))

    # ── partikel: rantai 120 frame vs rekaman pygame ──
    part = fx["particles"]
    respawn = [r[2] for r in part["respawn"]]
    states = [dict(p) for p in part["initial"]]
    ri = 0
    for frame in range(part["frames"]):
        elapsed = (frame + 1) * DT
        for p in states:
            # cermin Python untuk tahu apakah wrap terjadi (respawn RNG
            # hanya dikonsumsi pygame saat wrap)
            ny = p["y"] - p["speed"]
            wrapped = ny < -6.0
            rx = 0.0
            if wrapped:
                rx = respawn[ri]
                ri += 1
            adv = add("particle_advance",
                      [p["x"], p["y"], p["speed"], p["drift"], p["phase"],
                       elapsed, 720.0, rx], None)
            p.setdefault("_advs", []).append(adv)
            p.setdefault("_wraps", []).append(wrapped)
            # cermin ikut melangkah supaya frame berikut memakai state benar
            p["x"] = rx if wrapped else (
                p["x"] + p["drift"]
                + math.sin(elapsed * 0.8 + p["phase"]) * 0.05)
            p["y"] = 726.0 if wrapped else ny
    # balasannya dibandingkan setelah run (butuh nilai C++ untuk rantai)
    chain = {"states": states, "frames": part["frames"],
             "final": part["final"]}
    # triplet gambar pada elapsed 1.5 (state SESUDAH 120 frame)
    draws = part["draw_at_1_5"]
    finals = part["final"]
    for i, draw in enumerate(draws):
        st = finals[i]
        add("particle_twinkle", [1.5, st["phase"]], draw["twinkle"])
        add("particle_draw_color", [c8(st["color"]), draw["twinkle"]],
            c8(draw["color"]))
        add("particle_draw_radius", [st["r"]], draw["radius"])
        add("particle_draw_pos", [st["x"], st["y"]],
            [float(draw["pos"][0]), float(draw["pos"][1])])
    for i, st in enumerate(finals[:8]):
        add("particle_move", [st["x"], st["y"], st["speed"], st["drift"],
                              st["phase"], 2.0],
            {"y": st["y"] - st["speed"],
             "x": st["x"] + st["drift"]
             + math.sin(2.0 * 0.8 + st["phase"]) * 0.05})
        add("particle_wrapped", [st["y"]], st["y"] < -6.0)
        add("particle_wrap_y", [720.0], 726.0)
        add("particle_channel", [200, 0.5], int(200 * (0.35 + 0.65 * 0.5)))

    # ── latar ──
    bg = fx["bg"]
    add("bg_step_h", [720], 15)
    add("bg_band_count", [720], len(bg["bands"]))
    add("bg_step_h", [769], 769 // 48)
    for row in bg["bands"]:
        i = row["rect"][1]
        add("bg_band_rect", [i, 15, 1280],
            [float(v) for v in row["rect"]])
        add("bg_band_color", [i, 720], c8(row["color"]))
    add("bg_bands", [1280, 720],
        [{"rect": [float(v) for v in r["rect"]], "color": c8(r["color"])}
         for r in bg["bands"]])
    add("vignette_frames", [1280, 720],
        [{"rect": [float(v) for v in r["rect"]], "alpha": r["alpha"]}
         for r in bg["vignette"]])

    # ── logo ──
    logo = fx["logo"]
    iw, ih = logo["image"]
    add("logo_scale", [iw, ih], logo["scale"])
    add("logo_base_size", [iw, ih], [float(logo["base"][0]),
                                     float(logo["base"][1])])
    for row in logo["grow_table"]:
        add("logo_grow_quant", [row["elapsed"]], row["gq"])
        add("logo_grow_size", [v2(*logo["base"]), row["gq"]],
            [float(row["size"][0]), float(row["size"][1])])
        add("logo_glow_radius", [row["size"][0], row["size"][1]],
            row["glow_radius"])
        add("logo_glow_rect", [640.0, 334.0, row["glow_radius"]],
            [640.0 - row["glow_radius"], 334.0 - row["glow_radius"],
             row["glow_radius"] * 2.0, row["glow_radius"] * 2.0])
    rings_key = [k for k in logo if k.startswith("rings_at_")][0]
    glow_r = int(rings_key.split("_")[-1])
    add("logo_glow_rings", [glow_r],
        [{"r": r[0], "alpha": r[1]} for r in logo[rings_key]])
    add("logo_center_y", [360.0, True], 360.0 - logo["center_y_lift"])
    add("logo_center_y", [360.0, False], 360.0)
    add("logo_offsets", [], {"logo_lift": 26, "title_below": 46,
                             "sub_below": 88, "sub_text_only": 66})
    add("content_center", [1280, 720], [640.0, 360.0])

    # ── glow judul + aksen ──
    tg = fx["title_glow"]
    add("title_glow_layers", [True],
        [{"layer": l[0], "spread": l[1]} for l in tg["layers"]])
    add("title_glow_layers", [False], [])
    tr = tg["text_rect"]
    text_rect = rect(*tr)
    for row in tg["surfaces"]:
        add("title_glow_surface", [text_rect, row["layer"], row["spread"]],
            [float(v) for v in row["rect"]])
    for alpha, fill in tg["fills"]:
        add("title_glow_fill", [alpha], fill)
    tw = tr[2]
    add("accent_gap", [tw], tg["accent"][0]["gap"])
    add("accent_lines", [255.0],
        [{"off": a["off"], "color": c8(a["color"]), "width": a["width"],
          "len": a["left"][2] - a["left"][0]}
         for a in tg["accent"] if a["alpha"] == 255])

    # ── hint ──
    for row in fx["hint"]["rows"]:
        add("hint_pos", [1280, 720], [float(row["pos"][0]),
                                      float(row["pos"][1])])
        add("hint_alpha", [row["overall"]], row["alpha"])
    return cmds, chain


# ══════════════════════════════════════════════════════════
#  Build + jalan
# ══════════════════════════════════════════════════════════


def find_compiler():
    for name in ("g++", "clang++", "c++"):
        path = shutil.which(name)
        if path:
            return path
    return None


def compile_selftest(compiler, out_path):
    cmd = [compiler, "-std=c++17", "-O0", "-Wall",
           "-I", str(SELFTEST), "-I", str(SELFTEST / "shim"),
           "-o", str(out_path), str(SELFTEST / "splash_selftest.cpp")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-4000:])
        return False
    return True


def run_binary(binary, cmds):
    lines = ["count\tcount", "bind\tbind"]
    for cid, fn, args, _expected in cmds:
        lines.append("\t".join([cid, "fn", fn] + args))
    proc = subprocess.run([str(binary)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-2000:])
        print(proc.stderr[-2000:])
        raise SystemExit("[splash_selftest] harness gagal jalan")
    replies = {}
    for line in proc.stdout.splitlines():
        cid, _, payload = line.partition("\t")
        replies[cid] = payload
    return replies


def structural_checks(replies, cmds):
    section("struktur (closed-world)")
    count = parse_reply(replies.get("count"))
    header = (SRC / "splash_processor.h").read_text(encoding="utf-8")
    cpp = (SRC / "splash_processor.cpp").read_text(encoding="utf-8")
    table = re.findall(r'^\s*\{"([a-z_0-9]+)", (\d+),',
                       (SELFTEST / "splash_dispatch.inc").read_text(
                           encoding="utf-8"), re.M)
    table_names = [name for name, _argc in table]
    binds = cpp.count('bind_static_method("MysticSplash"')
    decls = len(re.findall(r"^    static [A-Za-z_:<>0-9 &,]+ [a-z_0-9]+\(",
                           header, re.M)) - 3  # py_round/py_int/_bind_methods
    used = sorted(set(c[1] for c in cmds))
    expect(count == len(table_names),
           "count (%s) != entri tabel perintah (%d)" % (count,
                                                        len(table_names)))
    expect(count == binds, "tabel perintah (%s) != bind (%d)"
           % (count, binds))
    expect(binds == decls, "bind (%d) != deklarasi .h (%d)" % (binds, decls))
    missing = sorted(set(table_names) - set(used))
    expect(not missing, "fungsi belum diuji: %s" % ", ".join(missing))
    unknown = sorted(set(used) - set(table_names))
    expect(not unknown, "perintah di luar tabel: %s" % ", ".join(unknown))
    ids = [c[0] for c in cmds]
    expect(len(set(ids)) == len(ids), "id perintah duplikat")
    expect(parse_reply(replies.get("bind")) is None, "bind tidak nil")
    expect("splash_v1:1mod:%dfn:" % binds in cpp,
           "api_signature tidak menyebut %d fungsi" % binds)
    expect(parse_reply(replies.get("c00001")) == ["splash_screen"],
           "module_names bukan [splash_screen]")


def wiring_checks():
    section("wiring (statis)")
    ext = ROOT / "godot" / "gdext" / "mystic_splash"
    addon = ROOT / "godot" / "addons" / "mystic_splash"
    for needle, path in (("mystic_splash_library_init",
                          ext / "src" / "register_types.cpp"),
                         ("ClassDB::register_class<MysticSplash>()",
                          ext / "src" / "register_types.cpp"),
                         ("mystic_splash_library_init",
                          addon / "mystic_splash.gdextension"),
                         ('compatibility_minimum = "4.3"',
                          addon / "mystic_splash.gdextension"),
                         ("libmystic_splash.linux.template_debug.x86_64.so",
                          addon / "mystic_splash.gdextension"),
                         ("env", ext / "SConstruct"),
                         ("splash_dispatch.inc",
                          ext / "selftest" / "splash_selftest.cpp"),
                         ("MYSTIC_SPLASH_SELFTEST_GODOT_STUB_H",
                          ext / "selftest" / "godot_stub.hpp")):
        expect(path.exists() and needle in path.read_text(encoding="utf-8"),
               "%s tidak memuat/ada: %s" % (path.name, needle))
    expect((addon / "bin" / ".gitkeep").exists(),
           "addons/mystic_splash/bin/.gitkeep hilang")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    expect("godot/addons/mystic_splash/bin/*.so" in gitignore,
           ".gitignore tidak mengabaikan lib mystic_splash")


def godot_cpp_syntax_check(compiler):
    """Opsional: kalau ada checkout godot-cpp ASLI, kompilasi terhadap header
    aslinya + compile/link/strip .so probe (penangkap bug kelas API godot-cpp
    yang lolos stub — pola tools/test_ui_cpp_selftest.py)."""
    import os
    candidates = [os.environ.get("GODOT_CPP_DIR"),
                  str(ROOT / "godot" / "gdext" / "godot-cpp"),
                  "/tmp/godot-cpp"]
    for base in candidates:
        if not base:
            continue
        base_path = Path(base)
        if not (base_path / "include" / "godot_cpp" / "godot.hpp").exists():
            continue
        gen = base_path / "gen" / "include"
        if not (gen / "godot_cpp" / "classes" / "ref_counted.hpp").exists():
            print("[splash_selftest] godot-cpp di %s belum di-generate — "
                  "cek sintaks dilewati" % base)
            return
        cmd = [compiler, "-std=c++17", "-fsyntax-only",
               "-I", str(base_path / "include"), "-I", str(gen),
               "-I", str(base_path / "gdextension"),
               "-I", str(SRC), str(SRC / "splash_processor.cpp"),
               str(SRC / "register_types.cpp")]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        section("sintaks vs godot-cpp asli (%s)" % base)
        expect(proc.returncode == 0,
               "kompilasi terhadap header godot-cpp gagal: %s"
               % proc.stderr.strip().split("\n")[-1][:300])
        if proc.returncode != 0:
            print(proc.stderr[:2000])
            return
        nm = shutil.which("nm")
        if nm is None:
            print("[splash_selftest] `nm` tidak ada — cek symbol dilewati")
            return
        probe = Path("/tmp/splash_probe.so")
        cmd = [compiler, "-std=c++17", "-fPIC", "-fvisibility=hidden", "-O1",
               "-shared", "-I", str(base_path / "include"), "-I", str(gen),
               "-I", str(base_path / "gdextension"),
               "-I", str(SRC), str(SRC / "splash_processor.cpp"),
               str(SRC / "register_types.cpp"), "-o", str(probe)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        section("isi .so seperti langkah CI (compile+link+strip nyata)")
        expect(proc.returncode == 0,
               "compile+link .so probe gagal: %s"
               % proc.stderr.strip().split("\n")[-1][:300])
        if proc.returncode != 0:
            print(proc.stderr[:2000])
            return
        strip_bin = shutil.which("strip")
        if strip_bin is not None:
            subprocess.run([strip_bin, "-s", str(probe)], check=False)
        dynamic = subprocess.run([nm, "-D", "--defined-only", str(probe)],
                                 capture_output=True, text=True).stdout
        strings_bin = shutil.which("strings")
        if strings_bin is not None:
            blob = subprocess.run([strings_bin, "-a", str(probe)],
                                  capture_output=True).stdout.decode(
                                      "utf-8", "replace")
        else:
            blob = "\n".join(m.decode("ascii", "replace") for m in
                             re.findall(rb"[\x20-\x7e]{4,}",
                                        probe.read_bytes()))
        expect("mystic_splash_library_init" in dynamic,
               "entry symbol mystic_splash_library_init tidak diekspor")
        binds = (SRC / "splash_processor.cpp").read_text(
            encoding="utf-8").count('bind_static_method("MysticSplash"')
        expect("splash_v1:1mod:%dfn:" % binds in blob,
               "api_signature tidak ada di .so probe")
        expect("MysticSplash" in blob,
               "nama kelas MysticSplash tidak ada di .so probe")
        return
    section("sintaks vs godot-cpp asli (dilewati: tidak ada checkout)")


def main():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cmds, chain = build_commands(fx)

    compiler = find_compiler()
    if compiler is None:
        print("[splash_selftest] compiler C++ tidak ditemukan")
        return 1
    out = Path("/tmp/splash_selftest_bin")
    if not compile_selftest(compiler, out):
        expect(False, "splash_selftest.cpp gagal dikompilasi")
        return 1
    godot_cpp_syntax_check(compiler)
    replies = run_binary(out, cmds)
    structural_checks(replies, cmds)
    wiring_checks()

    section("nilai (C++ vs oracle pygame)")
    for cid, fn, _args, expected in cmds:
        if cid not in replies:
            expect(False, "%s (%s): tidak ada balasan" % (cid, fn))
            continue
        if expected is None:
            continue
        try:
            got = parse_reply(replies[cid])
        except Exception as exc:  # noqa: BLE001
            expect(False, "%s: balasan tak terparse (%s): %r"
                   % (cid, exc, replies[cid][:120]))
            continue
        if isinstance(got, tuple) and got and got[0] == "ERROR":
            expect(False, "%s (%s): %s" % (cid, fn, got[1]))
            continue
        try:
            compare("%s:%s" % (cid, fn), expected, got)
        except Exception as exc:  # noqa: BLE001
            expect(False, "%s: pembanding error (%s) atas %r"
                   % (cid, exc, replies[cid][:120]))

    section("rantai partikel 120 frame (C++ vs rekaman pygame)")
    states = chain["states"]
    for frame in range(chain["frames"]):
        for i, p in enumerate(states):
            cid = p["_advs"][frame]
            got = parse_reply(replies[cid])
            if not isinstance(got, dict):
                expect(False, "%s: advance bukan dict" % cid)
                continue
            if frame == 0 or frame == chain["frames"] - 1:
                expect(got.get("wrapped") == p["_wraps"][frame],
                       "%s: wrapped %s != %s" % (cid, got.get("wrapped"),
                                                 p["_wraps"][frame]))
            p["x"] = got.get("x", p["x"])
            p["y"] = got.get("y", p["y"])
    for i, want in enumerate(chain["final"]):
        got = states[i]
        expect(abs(got["x"] - want["x"]) <= 1e-6
               and abs(got["y"] - want["y"]) <= 1e-6,
               "partikel %d sesudah %d frame: (%.6f, %.6f) != (%.6f, %.6f)"
               % (i, chain["frames"], got["x"], got["y"], want["x"],
                  want["y"]))

    print()
    if _failures:
        print("[splash_selftest] GAGAL: %d dari %d cek"
              % (len(_failures), _checks))
        return 1
    print("[splash_selftest] OK: %d cek lolos (%d perintah, compiler=%s)"
          % (_checks, len(cmds), Path(compiler).name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
