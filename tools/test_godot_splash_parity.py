#!/usr/bin/env python3
"""Oracle paritas splash_screen.py vs backend Godot (FASE 38, godot++).

    python3 tools/test_godot_splash_parity.py                 # cek + kesegaran
    python3 tools/test_godot_splash_parity.py --write-fixture # rekam ulang

GERBANG PRA-ENGINE untuk migrasi splash -> godot++. Oracle MENJALANKAN
splash_screen.py ASLI headless (SDL dummy) lewat surface spy (pola
tools/test_boss_draw_parity.py: TrackSurface + patch pygame.draw) lalu merekam
fixture godot/tests/fixtures/splash_parity.json:

  * constants  — GAME_NAME/SPLASH_DURATION/LOGO_PATHS/warna/ukuran font dari
                 MODUL HIDUP (bukan salinan), supaya drift satu angka pun
                 ketahuan;
  * timeline   — title_alpha/overall_alpha/done per frame 1/60 dtk, termasuk
                 tiga skenario skip (sebelum/sesudah ambang 0.25 dtk Python);
  * particles  — 46 partikel ber-seed 1234 (pygame memakai RNG global tak
                 ber-seed, jadi fixture MENYUNTIK seed supaya reproducible),
                 120 langkah update + nilai respawn RNG + triplet gambar;
  * bg         — batang gradien + bingkai vignette + SAMPEL PIKSEL _bg_cache
                 (membuktikan interior latar hitam pekat: bingkai vignette
                 terakhir ber-alpha 255 — perilaku yang hilang di port lama);
  * logo       — skala/kuantisasi tumbuh/radius glow/cincin glow untuk logo
                 assets/logo.png (1024x1024);
  * title_glow — lapisan glow + rect permukaan + alpha isi + garis aksen,
                 memakai FONT PALSU bermetrik deterministik (metrik font TIDAK
                 diklaim — pola oracle ui_theme FASE 31; lebar/tinggi teks
                 dikirim sebagai parameter ke C++);
  * hint       — posisi + alpha teks skip;
  * draw_order — URUTAN primitif level layar per skenario (bg -> partikel ->
                 glow logo -> logo -> glow judul -> judul -> tagline -> hint).

Selain merekam, skrip ini mengunci (tanpa engine):

  A. fixture segar: byte-identik dengan rekaman sekarang (kecuali
     --write-fixture);
  B. cermin GDScript: konstanta + rumus godot/scripts/ui/SplashModel.gd
     dibandingkan nilai modul pygame (dibaca sebagai TEKS, klaim dijangkar ke
     literal sumber — GDScript tidak bisa di-AST dari sini);
  C. permukaan API tiga sisi: bind_static_method splash_processor.cpp ==
     deklarasi .h == tabel splash_dispatch.inc == method SplashBackend.gd
     yang meneruskannya (closed-world);
  D. wiring: entry symbol .gdextension, .gitignore, setting project.godot
     default false, allowlist SEMPIT godot_log_gate, rujukan kedua workflow,
     SplashScreen.gd memakai SplashBackend (bukan angka tangan);
  E. ruang lingkup GDScript: setiap identifier ALL_CAPS telanjang di lima
     berkas splash .gd harus TERDEKLARASI di berkas itu sendiri atau ada di
     daftar global engine yang eksplisit. gdparse hanya memeriksa sintaks dan
     Godot baru mengeluh saat scene dimuat, jadi tanpa audit ini salah ketik
     satu konstanta (GROW_GROW vs GLOW_GROW) lolos lokal dan baru meledak di
     CI sebagai "Parse Error: Identifier ... not declared" yang menyeret
     SplashScreen.gd + Main.gd ikut gagal compile.

Keluar 0 = PASS.
"""
import argparse
import ast
import json
import math
import os
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "godot" / "tests" / "fixtures" / "splash_parity.json"
MODEL_GD = ROOT / "godot" / "scripts" / "ui" / "SplashModel.gd"
BACKEND_GD = ROOT / "godot" / "scripts" / "ui" / "SplashBackend.gd"
SPLASH_GD = ROOT / "godot" / "scenes" / "ui" / "SplashScreen.gd"

SEED = 1234
SCREEN = (1280, 720)
DT = 1.0 / 60.0

_checks = 0
_failures = []


def expect(cond, message):
    global _checks
    _checks += 1
    if not cond:
        _failures.append(message)
        print("[splash_parity] FAIL: %s" % message)


def section(title):
    print("[splash_parity] ── %s ──" % title)


# ══════════════════════════════════════════════════════════
#  Harness rekam (pygame ASLI menjalankan SplashScreen)
# ══════════════════════════════════════════════════════════


class Log:
    def __init__(self):
        self.ops = []        # primitif draw, urut panggil
        self.blits = []      # blit level layar, urut panggil
        self.tags = {}       # id(surface) -> tag
        self.texts = {}      # id(surface) -> info font palsu
        self.alphas = {}     # id(surface) -> alpha terakhir
        self.keep = []       # referensi kuat surface ber-tag
        self.auto = 0


LOG = Log()
_orig_draw = {}
DRAW_NAMES = ("rect", "circle", "line")


def tag(surface, name):
    LOG.tags[id(surface)] = name
    LOG.keep.append(surface)
    return name


def auto_tag(surface):
    """Surface antara pygame: tag berurutan sesuai urutan kelahiran."""
    name = "auto%d" % LOG.auto
    LOG.auto += 1
    return tag(surface, name)


def tag_of(surface):
    return LOG.tags.get(id(surface))


def ensure_tag(surface):
    got = tag_of(surface)
    if got is None:
        got = auto_tag(surface)
    return got


def _pos(dest):
    if dest is None:
        return [0, 0]
    if hasattr(dest, "x"):
        return [int(dest.x), int(dest.y)]
    return [int(dest[0]), int(dest[1])]


def patch_draw():
    for n in DRAW_NAMES:
        _orig_draw[n] = getattr(pygame.draw, n)

        def mk(n=n):
            def wrapped(surf, *a, **k):
                LOG.ops.append({"op": n, "surf": ensure_tag(surf), "args": a})
                return _orig_draw[n](surf, *a, **k)
            return wrapped
        setattr(pygame.draw, n, mk())


class FakeFont:
    """Font bermetrik deterministik: w = len(teks)*size//2, h = size.

    Metrik font TIDAK diklaim paritasnya (pola FASE 36/31): fixture merekam
    metrik palsu ini dan C++ menerima lebar/tinggi teks sebagai parameter.
    """

    def __init__(self, size):
        self.size = int(size)

    def render(self, text, aa, color, *a, **k):
        w = max(1, len(str(text)) * self.size // 2)
        h = max(1, self.size)
        s = TrackSurface((w, h), pygame.SRCALPHA)
        pygame.Surface.fill(s, (int(color[0]), int(color[1]), int(color[2]),
                                255))
        LOG.texts[id(s)] = {"text": str(text), "size": self.size,
                            "color": [int(color[0]), int(color[1]),
                                      int(color[2])],
                            "wh": [w, h]}
        LOG.keep.append(s)
        tag(s, "text:%s@%d" % (text, self.size))
        return s

    def get_height(self):
        return self.size

    def get_rect(self, *a, **k):  # tidak dipakai splash untuk font
        raise AssertionError("FakeFont.get_rect tidak diharapkan")


def install_fake_fonts(splash):
    splash.font_presents = FakeFont(34)
    splash.font_title = FakeFont(92)
    splash.font_title_below = FakeFont(66)
    splash.font_sub = FakeFont(22)
    splash.font_hint = FakeFont(16)


def make_splash(screen, seed=SEED, with_logo=True):
    import splash_screen as S
    random.seed(seed)
    splash = S.SplashScreen(screen)
    if not with_logo:
        splash.logo_img = None
    install_fake_fonts(splash)
    return splash


# ══════════════════════════════════════════════════════════
#  Perekaman fixture
# ══════════════════════════════════════════════════════════


def rec_constants(S):
    return {
        "game_name": S.GAME_NAME,
        "tagline": "A MOBA TOWER DEFENSE ADVENTURE",
        "hint_text": "Tap anywhere to skip",
        "duration": S.SPLASH_DURATION,
        "logo_paths": list(S.LOGO_PATHS),
        "accent": list(S.ACCENT),
        "accent_2": list(S.ACCENT_2),
        "text_main": list(S.TEXT_MAIN),
        "text_dim": list(S.TEXT_DIM),
        "gradient": {"top": [8, 8, 18], "mid": [22, 16, 38],
                     "bot": [6, 6, 14]},
        "particle_colors": [[255, 210, 120], [230, 160, 255],
                            [255, 245, 230], [180, 200, 255]],
        "font_sizes": {"presents": 34, "title": 92, "title_below": 66,
                       "sub": 22, "hint": 16},
        "font_fallback_sizes": {"presents": 40, "title": 110,
                                "title_below": 80, "sub": 26, "hint": 18},
        "font_styles": {"presents": "body_bold", "title": "title",
                        "title_below": "title", "sub": "body_semibold",
                        "hint": "body_medium"},
        "particle_count": 46,
        "particle_ranges": {
            "r": [0.6, 2.4], "speed": [0.08, 0.35],
            "drift": [-0.12, 0.12], "phase": [0.0, math.tau]},
        "timings": {"duration": 3.0, "fade_in": 0.4, "fade_out": 0.45,
                    "skip_fade": 0.25, "skip_done": 0.25, "title_delay": 0.5,
                    "title_ramp": 0.6, "title_max": 255, "grow_time": 0.9,
                    "alpha_epsilon": 0.001},
        "glow_layers": [[24, 1], [14, 2], [8, 3]],
        "accent_offsets": [[-6, "accent"], [6, "accent_2"]],
    }


def rec_timeline(screen):
    """Timeline state: normal + tiga skenario skip."""
    out = []
    scenarios = [("normal", None), ("skip_early", 0.1), ("skip_mid", 1.0),
                 ("skip_late", 2.0)]
    for name, skip_at in scenarios:
        splash = make_splash(screen)
        rows = []
        t = 0.0
        for _frame in range(0, 200):
            skipped_update = bool(splash.skipped)
            splash.update(DT)
            t += DT
            if skip_at is not None and t >= skip_at and not splash.skipped:
                splash.skip()
            # dua bendera skip: yang berlaku SAAT update (menentukan done)
            # dan yang berlaku saat alpha direkam (sesudah skip() frame ini)
            # elapsed penuh presisi: pygame mengakumulasi dt sehingga
            # t=180*(1/60) = 2.9999999999999996 < 3.0 (done masih False).
            # Pembulatan 9 digit akan membalik hasil ambang batas.
            rows.append([splash.elapsed, splash.title_alpha,
                         round(splash._overall_alpha(), 9),
                         bool(splash.done), skipped_update,
                         bool(splash.skipped)])
        out.append({"name": name, "skip_at": skip_at, "rows": rows})
    return out


def rec_particles(screen):
    splash = make_splash(screen)
    initial = [{k: (list(v) if isinstance(v, (list, tuple)) else v)
                for k, v in p.items()} for p in splash.particles]
    respawn = []
    real_uniform = random.uniform

    def spy_uniform(a, b):
        value = real_uniform(a, b)
        respawn.append([a, b, value])
        return value

    random.uniform = spy_uniform
    try:
        for _ in range(120):
            splash.update(DT)
    finally:
        random.uniform = real_uniform
    final = [{k: (list(v) if isinstance(v, (list, tuple)) else v)
              for k, v in p.items()} for p in splash.particles]
    # triplet gambar pada elapsed 1.5 (warna + radius + posisi trunc)
    splash.elapsed = 1.5
    draws = []
    for p in splash.particles:
        tw = 0.5 + 0.5 * math.sin(1.5 * 2.5 + p["phase"])
        draws.append({
            "pos": [int(p["x"]), int(p["y"])],
            "radius": max(1, int(p["r"])),
            "color": [int(ch * (0.35 + 0.65 * tw)) for ch in p["color"]],
            "twinkle": tw,
        })
    return {"seed": SEED, "initial": initial, "respawn": respawn,
            "frames": 120, "final": final, "draw_at_1_5": draws}


def rec_bg(screen):
    splash = make_splash(screen)
    splash.elapsed = 1.5
    splash.title_alpha = 255
    LOG.ops.clear()
    splash.draw()
    bands, vignette = [], []
    for op in LOG.ops:
        if op["op"] != "rect":
            continue
        if op["surf"] == "auto0":
            color = op["args"][0]
            rect = op["args"][1]
            bands.append({"rect": [int(rect[0]), int(rect[1]), int(rect[2]),
                                   int(rect[3])],
                          "color": [int(color[0]), int(color[1]),
                                    int(color[2])]})
        elif op["surf"] == "auto1":
            color = op["args"][0]
            rect = op["args"][1]
            vignette.append({"rect": [int(rect[0]), int(rect[1]),
                                      int(rect[2]), int(rect[3])],
                             "alpha": int(color[3])})
    bg = splash._bg_cache
    samples = {}
    for pt in [(0, 0), (1, 1), (2, 2), (3, 3), (20, 20), (140, 140),
               (640, 360), (1279, 719), (1278, 718)]:
        px = bg.get_at(pt)
        samples["%d,%d" % pt] = [px[0], px[1], px[2]]
    return {"bands": bands, "vignette": vignette, "pixels": samples}


def rec_logo(screen):
    splash = make_splash(screen)
    img = splash.logo_img
    iw, ih = img.get_width(), img.get_height()
    scale = min(340.0 / iw, 320.0 / ih, 1.0)
    w = max(1, int(iw * scale))
    h = max(1, int(ih * scale))
    grow_table = []
    for elapsed in (0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 1.2, 3.0):
        grow = min(1.0, elapsed / 0.9)
        gq = round((0.85 + 0.15 * grow) * 20) / 20.0
        ww = max(1, int(w * gq))
        hh = max(1, int(h * gq))
        glow_r = max(ww, hh) // 2 + 30
        grow_table.append({"elapsed": elapsed, "gq": gq, "size": [ww, hh],
                           "glow_radius": glow_r})
    rings = []
    glow_r = grow_table[-1]["glow_radius"]
    for g in range(glow_r, 0, -3):
        rings.append([g, int(12 * (1 - g / glow_r))])
    return {"image": [iw, ih], "scale": scale, "base": [w, h],
            "grow_table": grow_table, "rings_at_%d" % glow_r: rings,
            "center_y_lift": 26}


def rec_title_glow(screen):
    """Rect glow judul + garis aksen memakai metrik font palsu."""
    out = {"layers": [], "surfaces": [], "fills": [], "accent": []}
    text_w = len("MYSTIC ARENA") * 92 // 2
    text_h = 92
    rect = [640 - text_w // 2, 360 - text_h // 2, text_w, text_h]
    out["text_rect"] = rect
    for layer, spread in ((24, 1), (14, 2), (8, 3)):
        out["layers"].append([layer, spread])
        out["surfaces"].append({
            "layer": layer, "spread": spread,
            "rect": [rect[0] - layer - 1, rect[1] - layer - 1,
                     rect[2] + layer * 2 + spread * 2,
                     rect[3] + layer * 2 + spread * 2]})
    for alpha in (0, 64, 128, 192, 255):
        out["fills"].append([alpha, int(alpha * 0.28)])
    gap = text_w // 2 + 18
    for off, cname in ((-6, "accent"), (6, "accent_2")):
        for alpha in (128, 255):
            col = (255, 190, 60) if cname == "accent" else (200, 140, 255)
            fac = (alpha / 255.0) * 0.85
            out["accent"].append({
                "off": off, "alpha": alpha, "gap": gap,
                "color": [int(ch * fac) for ch in col],
                "left": [640 - gap, 360 + off, 640 - gap + 46, 360 + off],
                "right": [640 + gap, 360 + off, 640 + gap - 46, 360 + off],
                "width": 2})
    return out


def rec_hint(screen):
    rows = []
    for overall in (0.0, 0.3, 0.55, 1.0):
        rows.append({"overall": overall, "alpha": int(140 * overall),
                     "pos": [1280 // 2, 720 - 48]})
    return {"text": "Tap anywhere to skip", "rows": rows}


def rec_draw_order(screen, with_logo, elapsed):
    """Urutan primitif LEVEL LAYAR untuk satu skenario (bg -> partikel ->
    glow logo -> logo -> glow judul -> judul -> tagline -> hint)."""
    global LOG
    LOG = Log()
    splash = make_splash(screen, with_logo=with_logo)
    tag(screen, "screen")
    splash.elapsed = elapsed
    splash.title_alpha = int(255 * min(1.0, max(0.0, (elapsed - 0.5) / 0.6)))
    LOG.ops.clear()
    LOG.blits.clear()
    orig_blit = TrackSurface.blit
    ops_seq = []

    def blit_wrap(self, src, dest=None, *a, **k):
        if tag_of(self) == "screen":
            entry = {"kind": "blit", "src": ensure_tag(src),
                     "src_size": [src.get_width(), src.get_height()],
                     "dest": _pos(dest),
                     "alpha": LOG.alphas.get(id(src))}
            LOG.blits.append(entry)
            ops_seq.append(entry)
        return orig_blit(self, src, dest, *a, **k)

    TrackSurface.blit = blit_wrap
    saved = {}
    for n in DRAW_NAMES:
        cur = getattr(pygame.draw, n)
        saved[n] = cur

        def mk(n=n, cur=cur):
            def wrapped(surf, *a, **k):
                if tag_of(surf) == "screen":
                    ops_seq.append({"kind": n, "args": _canon_draw(n, a)})
                return cur(surf, *a, **k)
            return wrapped
        setattr(pygame.draw, n, mk())
    try:
        splash.draw()
    finally:
        TrackSurface.blit = orig_blit
        for n, cur in saved.items():
            setattr(pygame.draw, n, cur)
    ctx = _rename_ctx(with_logo, elapsed)
    for entry in ops_seq:
        if entry["kind"] != "blit":
            continue
        entry["src"] = _rename_src(entry, ctx)
    return {"with_logo": with_logo, "elapsed": elapsed,
            "blit_count": len(LOG.blits),
            "screen_draw_count": sum(1 for e in ops_seq
                                     if e["kind"] != "blit"),
            "sequence": ops_seq}


def _rename_ctx(with_logo, elapsed):
    """Ukuran surface antara yang DIHARAPKAN (dihitung, bukan direkam) —
    dipakai menamai tag autoN supaya urutan blit terbaca + terkunci."""
    w_screen, h_screen = SCREEN
    ctx = {"bg": [w_screen, h_screen], "glow_title": [], "title_copy": None,
           "logo_glow": None, "logo_img": None, "glow_idx": 0}
    if with_logo:
        iw, ih = 1024, 1024
        scale = min(340.0 / iw, 320.0 / ih, 1.0)
        w = max(1, int(iw * scale))
        h = max(1, int(ih * scale))
        grow = min(1.0, elapsed / 0.9)
        gq = round((0.85 + 0.15 * grow) * 20) / 20.0
        ww = max(1, int(w * gq))
        hh = max(1, int(h * gq))
        ctx["logo_img"] = [ww, hh]
        ctx["logo_glow"] = [max(ww, hh) // 2 * 2 + 60,
                            max(ww, hh) // 2 * 2 + 60]
        tw = len("MYSTIC ARENA") * 66 // 2
        th = 66
        for layer, spread in ((24, 1), (14, 2), (8, 3)):
            ctx["glow_title"].append([tw + layer * 2 + spread * 2,
                                      th + layer * 2 + spread * 2])
        ctx["title_copy"] = [tw, th]
    else:
        tw = len("MYSTIC ARENA") * 92 // 2
        th = 92
        for layer, spread in ((24, 1), (14, 2), (8, 3)):
            ctx["glow_title"].append([tw + layer * 2 + spread * 2,
                                      th + layer * 2 + spread * 2])
        ctx["title_copy"] = [tw, th]
    return ctx


def _rename_src(entry, ctx):
    src = entry["src"]
    if not src.startswith("auto"):
        return src
    size = entry["src_size"]
    if size == ctx["bg"]:
        return "bg"
    if ctx["logo_glow"] and size == ctx["logo_glow"]:
        return "logo_glow"
    if ctx["logo_img"] and size == ctx["logo_img"]:
        return "logo_img"
    for i, want in enumerate(ctx["glow_title"]):
        if size == want:
            return "glow_title_%d" % i
    if ctx["title_copy"] and size == ctx["title_copy"]:
        return "title_copy"
    raise AssertionError("surface antara tak dikenal: %s %s" % (src, size))


def _canon_draw(kind, args):
    if kind == "circle":
        return [list(args[0]), [int(args[1][0]), int(args[1][1])],
                int(args[2])]
    if kind == "line":
        return [list(args[0]), [int(args[1][0]), int(args[1][1])],
                [int(args[2][0]), int(args[2][1])], int(args[3])]
    return [list(args[0]), [int(v) for v in args[1]]]


def seq_draw_only(log):
    out = []
    for op in log.ops:
        if op["surf"] != "screen":
            continue
        if op["op"] == "circle":
            out.append(["circle", list(op["args"][1]),
                        [int(op["args"][2][0]), int(op["args"][2][1])],
                        int(op["args"][3])])
        elif op["op"] == "line":
            out.append(["line", list(op["args"][1]),
                        [int(op["args"][2][0]), int(op["args"][2][1])],
                        [int(op["args"][3][0]), int(op["args"][3][1])],
                        int(op["args"][4])])
        else:
            out.append(["rect", list(op["args"][1]),
                        [int(v) for v in op["args"][2]]])
    return out


def record_fixture():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    global pygame, TrackSurface
    import pygame as _pg
    pygame = _pg
    pygame.init()

    class _Track(pygame.Surface):
        def blit(self, src, dest=None, *a, **k):
            return pygame.Surface.blit(self, src, dest, *a, **k)

        def set_alpha(self, v):
            LOG.alphas[id(self)] = 255 if v is None else int(v)
            return pygame.Surface.set_alpha(self, v)

    TrackSurface = _Track
    globals()["TrackSurface"] = _Track
    patch_draw()
    import splash_screen as S
    S.SplashScreen._init_fonts = lambda self: install_fake_fonts(self)

    pygame.display.set_mode(SCREEN)
    # Layar yang DIPAKAI splash adalah TrackSurface sendiri (bukan surface
    # display) supaya setiap blit level layar terekam.
    screen = TrackSurface(SCREEN)
    tag(screen, "screen")
    data = {
        "meta": {"source": "splash_screen.py", "seed": SEED,
                 "screen": list(SCREEN), "dt": DT,
                 "fake_font": "w = len(teks)*size//2, h = size",
                 "cheap_alpha": True},
        "constants": rec_constants(S),
        "timeline": rec_timeline(screen),
        "particles": rec_particles(screen),
        "bg": rec_bg(screen),
        "logo": rec_logo(screen),
        "title_glow": rec_title_glow(screen),
        "hint": rec_hint(screen),
        "draw_order": [rec_draw_order(screen, True, 1.5),
                       rec_draw_order(screen, False, 2.0)],
    }
    return data


# ══════════════════════════════════════════════════════════
#  Cek statis (tanpa pygame)
# ══════════════════════════════════════════════════════════


def _gd_constants(text):
    """Ambil literal const di SplashModel.gd: {NAMA: nilai}."""
    out = {}
    for match in re.finditer(
            r"^const ([A-Z_0-9]+) := (-?[0-9.]+|\"[^\"]*\")", text, re.M):
        name, raw = match.group(1), match.group(2)
        out[name] = raw.strip('"') if raw.startswith('"') else float(raw) \
            if ("." in raw) else int(raw)
    return out


def check_model_mirror(fixture):
    section("cermin GDScript (SplashModel.gd)")
    text = MODEL_GD.read_text(encoding="utf-8")
    cons = _gd_constants(text)
    c = fixture["constants"]
    pairs = [
        ("SPLASH_DURATION", c["duration"]),
        ("FADE_IN", c["timings"]["fade_in"]),
        ("FADE_OUT", c["timings"]["fade_out"]),
        ("SKIP_FADE", c["timings"]["skip_fade"]),
        ("TITLE_DELAY", c["timings"]["title_delay"]),
        ("TITLE_RAMP", c["timings"]["title_ramp"]),
        ("GROW_TIME", c["timings"]["grow_time"]),
        ("ALPHA_EPSILON", c["timings"]["alpha_epsilon"]),
        ("GRAD_SPLIT", 0.55),
        ("VIG_SLOPE", 2.2),
        ("TWINKLE_RATE", 2.5),
        ("DIM_FLOOR", 0.35),
        ("DIM_SPAN", 0.65),
        ("GLOW_FILL", 0.28),
        ("ACCENT_FAC", 0.85),
        ("MOVE_RATE", 0.8),
        ("MOVE_AMP", 0.05),
    ]
    for name, want in pairs:
        expect(name in cons, "SplashModel.gd kehilangan const %s" % name)
        if name in cons:
            expect(abs(cons[name] - want) < 1e-12,
                   "SplashModel.gd %s = %s != %s" % (name, cons[name], want))
    ints = [("PARTICLE_COUNT", 46), ("BAND_TARGET", 48), ("VIG_START", 140),
            ("VIG_STEP", -2), ("WRAP_BELOW", -6), ("WRAP_MARGIN", 6),
            ("LOGO_LIFT", 26), ("TITLE_BELOW", 46), ("SUB_BELOW", 88),
            ("SUB_TEXT_ONLY", 66), ("HINT_MARGIN", 48), ("HINT_ALPHA", 140),
            ("TITLE_MAX", 255), ("GLOW_PAD", 30), ("GLOW_STEP", -3),
            ("GLOW_ALPHA", 12), ("ACCENT_PAD", 18), ("ACCENT_LEN", 46),
            ("ACCENT_WIDTH", 2), ("GROW_QUANT", 20), ("LOGO_MAX_W", 340),
            ("LOGO_MAX_H", 320), ("PARTICLE_MIN_R", 1), ("GLOW_GROW", 2),
            ("GLOW_OFFSET", 1)]
    for name, want in ints:
        expect(name in cons, "SplashModel.gd kehilangan const %s" % name)
        if name in cons:
            expect(cons[name] == want,
                   "SplashModel.gd %s = %s != %s" % (name, cons[name], want))
    for needle in ("GAME_NAME", "TAGLINE", "HINT_TEXT"):
        expect(needle in cons, "SplashModel.gd kehilangan const %s" % needle)
    expect('const GAME_NAME := "MYSTIC ARENA"' in text,
           "SplashModel.gd GAME_NAME != MYSTIC ARENA")
    expect('const TAGLINE := "A MOBA TOWER DEFENSE ADVENTURE"' in text,
           "SplashModel.gd TAGLINE salah")
    expect('const HINT_TEXT := "Tap anywhere to skip"' in text,
           "SplashModel.gd HINT_TEXT salah")
    # warna: Color("#rrggbb") harus sama dengan tuple pygame
    for name, rgb in (("ACCENT", c["accent"]), ("ACCENT_2", c["accent_2"]),
                      ("TEXT_MAIN", c["text_main"]),
                      ("TEXT_DIM", c["text_dim"])):
        want = 'const %s := Color("#%02x%02x%02x")' % (name, *rgb)
        expect(want in text, "SplashModel.gd %s bukan %s" % (name, want))


def check_api_surface():
    section("permukaan API tiga sisi (closed-world)")
    cpp = (ROOT / "godot" / "gdext" / "mystic_splash" / "src"
           / "splash_processor.cpp").read_text(encoding="utf-8")
    header = (ROOT / "godot" / "gdext" / "mystic_splash" / "src"
              / "splash_processor.h").read_text(encoding="utf-8")
    table = (ROOT / "godot" / "gdext" / "mystic_splash" / "selftest"
             / "splash_dispatch.inc").read_text(encoding="utf-8")
    backend = BACKEND_GD.read_text(encoding="utf-8")
    binds = re.findall(r'bind_static_method\("MysticSplash", '
                       r'D_METHOD\("([a-z_0-9]+)"', cpp)
    decls = re.findall(r"^    static [A-Za-z_:<>0-9 &,]+ ([a-z_0-9]+)\(",
                       header, re.M)
    public = [d for d in decls if d not in ("py_round", "py_int",
                                            "_bind_methods")]
    entries = re.findall(r'^    \{"([a-z_0-9]+)", (\d+),', table, re.M)
    expect(len(binds) == len(public),
           "bind (%d) != deklarasi publik .h (%d)" % (len(binds),
                                                      len(public)))
    expect(sorted(binds) == sorted(n for n, _ in entries),
           "bind != tabel perintah selftest")
    # setiap fungsi ter-bind diteruskan SplashBackend (routing C++ dulu)
    missing = [n for n in binds
               if ('"%s"' % n) not in backend]
    expect(not missing,
           "SplashBackend.gd tidak meneruskan fungsi: %s"
           % ", ".join(missing[:12]))


def _split_args(text):
    """Pecah daftar argumen pada koma tingkat atas (abaikan string/kurung)."""
    out = []
    depth = 0
    quote = ""
    cur = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            cur += ch
            if ch == "\\" and i + 1 < len(text):
                cur += text[i + 1]
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch in "([{":
            depth += 1
            cur += ch
        elif ch in ")]}":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    if cur.strip():
        out.append(cur)
    return [a for a in out if a.strip()]


def _gd_funcs(text):
    """{nama: jumlah argumen} dari deklarasi `static func` berkas .gd."""
    out = {}
    for m in re.finditer(r"^static func ([a-z_0-9]+)\((.*?)\)\s*->",
                         text, re.M | re.S):
        out[m.group(1)] = len(_split_args(m.group(2)))
    return out


def _cpp_funcs(text):
    """{nama: jumlah argumen} dari deklarasi `static ... name(...)` header C++."""
    out = {}
    for m in re.finditer(r"^    static [A-Za-z_:<>0-9 &,]+ ([a-z_0-9]+)\("
                         r"(.*?)\);", text, re.M | re.S):
        out[m.group(1)] = len(_split_args(m.group(2)))
    return out


def _backend_calls(text):
    """[(nama, jumlah argumen)] dari tiap panggilan `Backend.nama(...)`."""
    out = []
    for m in re.finditer(r"Backend\.([a-z_0-9]+)\(", text):
        name = m.group(1)
        i = m.end() - 1
        depth = 0
        j = i
        while j < len(text):
            ch = text[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append((name, len(_split_args(text[i + 1:j]))))
    return out


def check_engine_tests():
    """Scene engine (GDScript + GDExt) harus memanggil API yang benar-benar
    ada dengan arity yang benar — gdparse hanya memeriksa sintaks, dan Godot
    memeriksa arity LINTAS berkas saat scene dimuat (Parse Error = seluruh
    run CI mati tanpa pesan yang menunjuk barisnya)."""
    section("scene engine (SplashParityTest + SplashGdextParityTest)")
    tests = ROOT / "godot" / "tests"
    base_gd = tests / "SplashParityTest.gd"
    base_tscn = tests / "SplashParityTest.tscn"
    ext_gd = tests / "SplashGdextParityTest.gd"
    ext_tscn = tests / "SplashGdextParityTest.tscn"
    for path in (base_gd, base_tscn, ext_gd, ext_tscn):
        expect(path.exists(), "%s tidak ada" % path.relative_to(ROOT))
    if not (base_gd.exists() and ext_gd.exists()):
        return
    expect('path="res://tests/SplashParityTest.gd"'
           in base_tscn.read_text(encoding="utf-8"),
           "SplashParityTest.tscn tidak menunjuk skripnya")
    expect('path="res://tests/SplashGdextParityTest.gd"'
           in ext_tscn.read_text(encoding="utf-8"),
           "SplashGdextParityTest.tscn tidak menunjuk skripnya")

    base = base_gd.read_text(encoding="utf-8")
    ext = ext_gd.read_text(encoding="utf-8")
    for needle in ('const FIXTURE := "res://tests/fixtures/splash_parity.json"',
                   'preload("res://scripts/ui/SplashBackend.gd")',
                   'var backend_override := "gdscript"',
                   "Backend.force_backend(backend_override)",
                   '[%s] PASS" % LABEL'):
        expect(needle in base, "SplashParityTest.gd kehilangan %s" % needle)
    for needle in ('extends "res://tests/SplashParityTest.gd"',
                   "Backend.gdext_available()",
                   'Backend.force_backend("gdext")',
                   "Backend.is_using_gdext()",
                   "Backend.reset_backend()",
                   "[SplashGdextParityTest] PASS",
                   "_fail_gdext(", "_abort()"):
        expect(needle in ext, "SplashGdextParityTest.gd kehilangan %s" % needle)
    expect("_fail(\"gdext/%s: %s\" % [tag, message])" in ext,
           "_fail_gdext harus merangkai tag ke SATU argumen _fail()")

    # Arity tiga sisi: SplashBackend (router), SplashModel (fallback GDScript),
    # splash_processor.h (C++). Semua panggilan di scene + test harus cocok.
    backend_funcs = _gd_funcs(BACKEND_GD.read_text(encoding="utf-8"))
    model_funcs = _gd_funcs(MODEL_GD.read_text(encoding="utf-8"))
    cpp_header = _cpp_funcs((ROOT / "godot" / "gdext" / "mystic_splash" / "src"
                             / "splash_processor.h").read_text(encoding="utf-8"))
    mismatch = [n for n in backend_funcs
                if n in model_funcs and backend_funcs[n] != model_funcs[n]]
    expect(not mismatch,
           "arity SplashBackend != SplashModel: %s" % ", ".join(mismatch[:8]))
    mismatch = [n for n in backend_funcs
                if n in cpp_header and backend_funcs[n] != cpp_header[n]]
    expect(not mismatch,
           "arity SplashBackend != splash_processor.h: %s"
           % ", ".join(mismatch[:8]))

    callers = {"SplashScreen.gd": SPLASH_GD.read_text(encoding="utf-8"),
               "SplashParityTest.gd": base,
               "SplashGdextParityTest.gd": ext}
    total_calls = 0
    for label, text in callers.items():
        for name, argc in _backend_calls(text):
            total_calls += 1
            expect(name in backend_funcs,
                   "%s memanggil Backend.%s yang tidak ada di SplashBackend.gd"
                   % (label, name))
            if name in backend_funcs:
                expect(argc == backend_funcs[name],
                       "%s: Backend.%s dipanggil dengan %d argumen, "
                       "deklarasinya %d" % (label, name, argc,
                                            backend_funcs[name]))
    # SEMANTIK argumen, bukan cuma arity (regresi bug CI #2): argumen pertama
    # bg_band_rect/bg_band_color adalah Y PIKSEL — pygame menulis
    # `for i in range(0, self.h, step_h)` sehingga `i` di sana baris piksel.
    # Sweep engine yang mengirim INDEKS batang membuat f = i/720 selalu < 0.55
    # sehingga 46 dari 48 batang keluar berwarna batang 0 dan
    # SplashParityTest merah di CI (arity-nya sah, jadi audit di atas buta).
    expect("var y: int = i * step_h" in base,
           "SplashParityTest.gd kehilangan 'var y: int = i * step_h' — sweep "
           "latar harus menurunkan y piksel dari bg_step_h()")
    for fname in ("bg_band_rect", "bg_band_color"):
        sites = re.findall(r"Backend\.%s\(([^)\n]*)" % fname, base)
        expect(len(sites) >= 1,
               "SplashParityTest.gd tidak memanggil Backend.%s secara langsung"
               % fname)
        for args in sites:
            first = args.split(",")[0].strip()
            expect(first == "y" or "step_h" in first,
                   "SplashParityTest.gd: argumen pertama Backend.%s harus Y "
                   "piksel (i * step_h), dapat %r — indeks batang membuat "
                   "semua warna batang sama" % (fname, first))

    expect(total_calls >= 150,
           "hanya %d panggilan Backend.* terdeteksi di scene + test "
           "(pemanggilan lintas baris mungkin luput dari pemindai)"
           % total_calls)


def check_wiring():
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
    gate = (ROOT / "godot" / "tools" / "godot_log_gate.py").read_text(
        encoding="utf-8")
    for needle in (r'r"addons/mystic_splash"', r'r"libmystic_splash"',
                   r'r"Failed loading resource.*mystic_splash"'):
        expect(needle in gate,
               "godot_log_gate.py kehilangan allowlist %s" % needle)
    expect('\n    r"mystic_splash",' not in gate,
           'godot_log_gate.py punya allowlist telanjang r"mystic_splash"')
    check_yml = (ROOT / ".github" / "workflows" / "godot-check.yml").read_text(
        encoding="utf-8")
    gdext_yml = (ROOT / ".github" / "workflows" / "godot-gdext.yml").read_text(
        encoding="utf-8")
    for needle in ("tools/gen_splash_cpp.py --check",
                   "tools/test_godot_splash_parity.py",
                   "tools/test_splash_cpp_selftest.py",
                   "res://tests/SplashParityTest.tscn"):
        expect(needle in check_yml,
               "godot-check.yml tak merujuk %s" % needle)
    for needle in ("tools/gen_splash_cpp.py --check",
                   "tools/test_splash_cpp_selftest.py",
                   "godot/gdext/mystic_splash",
                   "libmystic_splash.linux.template_debug.x86_64.so",
                   "mystic_splash_library_init",
                   "SplashGdextParityTest"):
        expect(needle in gdext_yml,
               "godot-gdext.yml tak merujuk %s" % needle)
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    expect("godot/addons/mystic_splash/bin/*.so" in gitignore,
           ".gitignore tidak mengabaikan lib mystic_splash")
    project = (ROOT / "godot" / "project.godot").read_text(encoding="utf-8")
    expect("splash/use_gdext_splash=false" in project,
           "project.godot kehilangan mystic/splash/use_gdext_splash=false")
    splash_gd = SPLASH_GD.read_text(encoding="utf-8")
    for needle in ("SplashBackend", "Backend.bg_bands",
                   "Backend.vignette_frames", "Backend.overall_alpha"):
        expect(needle in splash_gd,
               "SplashScreen.gd tidak memakai SplashBackend.%s"
               % needle.split(".")[-1])


# ══════════════════════════════════════════════════════════
#  E. Ruang lingkup GDScript (statis, tanpa engine)
# ══════════════════════════════════════════════════════════

GD_TEST_A = ROOT / "godot" / "tests" / "SplashParityTest.gd"
GD_TEST_B = ROOT / "godot" / "tests" / "SplashGdextParityTest.gd"
GD_SOURCES = (MODEL_GD, BACKEND_GD, SPLASH_GD, GD_TEST_A, GD_TEST_B)

# Global engine Godot 4 yang sah dipakai tanpa deklarasi berkas: konstanta
# enum bawaan + kelas singleton. Daftar ini SENGAJA hanya memuat nama yang
# benar-benar dipakai berkas splash — nama baru harus ditambahkan di sini
# supaya audit tetap closed-world (bukan whitelist lebar).
GD_ENGINE_GLOBALS = frozenset({
    # konstanta matematika bawaan (@GlobalScope)
    "PI", "TAU", "INF", "NAN",
    # konstanta enum + kelas singleton yang benar-benar dipakai berkas splash
    "HORIZONTAL_ALIGNMENT_LEFT", "MOUSE_BUTTON_LEFT", "JSON",
})


def _gd_code(text):
    """Buang komentar dan isi string; sisakan bentuk kode mentahnya.

    Pemindai identifier di bawah tidak boleh melihat teks komentar (penuh
    nama konstanta dalam prosa) maupun literal string (berisi path seperti
    "res://scripts/ui/SplashBackend.gd" yang akan terbaca sebagai rujukan).
    """
    out = []
    for line in text.splitlines():
        res = []
        quote = None
        i = 0
        while i < len(line):
            ch = line[i]
            if quote is not None:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    quote = None
                res.append(" ")
                i += 1
                continue
            if ch in "\"'":
                quote = ch
                res.append(ch)
                i += 1
                continue
            if ch == "#":
                break
            res.append(ch)
            i += 1
        out.append("".join(res))
    return "\n".join(out)


def _gd_declared(code):
    """Semua nama yang dideklarasikan di satu berkas GDScript."""
    declared = set()
    declared |= set(re.findall(
        r"^\s*(?:const|var|static var|signal|class_name)\s+([A-Za-z_]\w*)",
        code, re.M))
    declared |= set(re.findall(r"^\s*(?:static\s+)?func\s+([A-Za-z_]\w*)",
                               code, re.M))
    declared |= set(re.findall(r"^\s*([A-Za-z_]\w*)\s*:=", code, re.M))
    declared |= set(re.findall(r"^\s*([A-Za-z_]\w*)\s*=(?!=)", code, re.M))
    declared |= set(re.findall(r"\bfor\s+([A-Za-z_]\w*)\s+in\b", code))
    for match in re.finditer(r"\bfunc\s+[A-Za-z_]\w*\s*\(([^)]*)\)", code):
        for part in match.group(1).split(","):
            name = re.split(r"[:=]", part.strip())[0].strip()
            if re.fullmatch(r"[A-Za-z_]\w*", name):
                declared.add(name)
    return declared


def check_gd_scope():
    section("ruang lingkup GDScript (statis)")
    for path in GD_SOURCES:
        expect(path.exists(), "%s tidak ada" % path.name)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        expect('"""' not in text and not re.search(r"^\s*enum\s", text, re.M),
               "%s: pemindai belum mendukung triple-quote/enum — perlu "
               "diperluas dulu sebelum audit ruang lingkup dipercaya"
               % path.name)
        code = _gd_code(text)
        expect("func " in code,
               "%s: _gd_code() menelan seluruh isi berkas (stripper rusak)"
               % path.name)
        declared = _gd_declared(code)
        used = set(re.findall(r"(?<![.\w])([A-Z][A-Z0-9_]+)(?!\w)", code))
        undeclared = sorted(name for name in used
                            if name not in declared
                            and name not in GD_ENGINE_GLOBALS)
        expect(not undeclared,
               "%s: identifier ALL_CAPS telanjang tak terdeklarasi %s — Godot "
               'gagal parse ("Identifier ... not declared in the current '
               'scope") dan menyeret berkas yang me-preload-nya'
               % (path.name, undeclared))
    # Regresi spesifik bug yang ditemukan CI: rect glow judul memakai faktor
    # tumbuh yang sama di kedua sumbu (C++: spread * 2 untuk w dan h).
    model = MODEL_GD.read_text(encoding="utf-8")
    expect(model.count("spread * GLOW_GROW") == 2,
           "SplashModel.title_glow_surface harus memakai GLOW_GROW di sumbu x "
           "DAN y (dapat %d), sama seperti splash_processor.cpp"
           % model.count("spread * GLOW_GROW"))
    expect("GROW_GROW" not in model,
           "SplashModel.gd masih memuat GROW_GROW (typo GLOW_GROW)")


def check_fixture_fresh(fresh):
    section("kesegaran fixture")
    if not FIXTURE.exists():
        expect(False, "fixture %s tidak ada — jalankan --write-fixture"
               % FIXTURE.relative_to(ROOT))
        return
    stored = FIXTURE.read_text(encoding="utf-8")
    expect(json.loads(stored) == json.loads(json.dumps(fresh)),
           "fixture splash_parity.json BASI — jalankan "
           "tools/test_godot_splash_parity.py --write-fixture")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-fixture", action="store_true")
    args = parser.parse_args()

    fresh = record_fixture()
    if args.write_fixture:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fresh, indent=1,
                                      sort_keys=False) + "\n",
                           encoding="utf-8")
        print("[splash_parity] tulis %s" % FIXTURE.relative_to(ROOT))
        fixture = fresh
    else:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8")) \
            if FIXTURE.exists() else {}
        check_fixture_fresh(fresh)

    check_model_mirror(fixture)
    check_api_surface()
    check_engine_tests()
    check_wiring()
    check_gd_scope()

    print()
    if _failures:
        print("[splash_parity] GAGAL: %d dari %d cek"
              % (len(_failures), _checks))
        return 1
    print("[splash_parity] OK: %d cek lolos" % _checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
