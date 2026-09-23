#!/usr/bin/env python3
"""test_boss_draw_parity — ORACLE pygame untuk lapisan overlay Boss.draw().

FASE 32 memport ``bosses/base_boss.py:6124-6430`` (Boss.draw: entrance, aura
ability/enrage/true boss, bayangan, indikator debuff menara ``_core.py:1037``,
badan generik, HP bar, papan nama) ke ``godot/scripts/render/BossOverlay.gd``
+ ``godot/scenes/boss/BossPlate.gd``.

Berkas ini MENJALANKAN pygame ASLI (headless, SDL dummy) dan:

  1. merekam setiap primitif gambar yang dipakai ``Boss.draw`` (draw.circle /
     ellipse / rect / polygon, blit surface antara, render+set_alpha teks);
  2. mengonversi rekaman itu ke OP KANONIK — kosakata gambar yang sama dengan
     BossOverlay.gd (disc / band / ring / ellipse / rect / poly / text);
  3. MEMVERIFIKASI konversi dengan piksel: op kanonik digambar ulang ke surface
     kosong memakai semantik pygame (overwrite di tujuan, blend hanya lewat
     blit surface SRCALPHA) dan hasilnya harus IDENTIK piksel-per-piksel
     dengan render asli — jadi tidak ada op yang hilang, bergeser, atau
     berubah alpha/warna/urutan;
  4. memverifikasi semantik PITA ALPHA aura (``pygame.draw.circle`` MENIMPA,
     ``CanvasItem.draw_circle`` Godot MEM-BLEND) dengan profil alpha terukur
     dari render sungguhan, dan memastikan model naif "N draw_circle
     bertumpuk" MEMANG meleset;
  5. menulis ``godot/tests/fixtures/boss_draw.json`` yang diputar ulang
     ``godot/tests/BossDrawParityTest.tscn`` (Godot headless) di CI.

Badan boss TIDAK ikut direkam: renderer per boss (bosses/level1..54.py)
diganti strip bake sejak Fase 2b/5, jadi ``heroes.render_boss`` dinetralkan
(mengaku sudah menggambar) dan ``_get_boss_draw_func`` dikembalikan None untuk
skenario badan generik. Yang diuji di sini persis permukaan yang diport.

Jalankan:  python3 tools/test_boss_draw_parity.py
Butuh:      pygame / pygame-ce (CI memasangnya). Tidak butuh Godot.
"""
import argparse
import json
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame                                    # noqa: E402
import _core                                     # noqa: E402,F401  (alias settings)
import bosses.base_boss as bb                    # noqa: E402
import bosses.boss_data as boss_data             # noqa: E402
import heroes                                    # noqa: E402
from _render import get_font as real_get_font    # noqa: E402

SCREEN_W, SCREEN_H = 1280, 720
FIXTURE = os.path.join(ROOT, "godot", "tests", "fixtures", "boss_draw.json")
DRAW_NAMES = ("circle", "ellipse", "rect", "polygon", "line")
BAR_BG = [40, 0, 0]


def _NOOP_RENDERER(*_a, **_k):
    """Pengganti renderer per boss: badan = strip bake (Fase 5), bukan op."""
    return None
PLATE_BG = [0, 0, 0]
SHADOW_COL = [0, 0, 0, 120]

_pass = 0
_fail = 0
WRITE_FIXTURE = False


def check(name, cond, detail=""):
    global _pass, _fail
    if cond:
        _pass += 1
    else:
        _fail += 1
        print("  FAIL %s%s" % (name, (" - " + detail) if detail else ""))


def section(title):
    print("\n== %s ==" % title)


# ═══════════════════════════════════════════════════════════════════
# Harness rekam (pygame ASLI menjalankan Boss.draw)
# ═══════════════════════════════════════════════════════════════════

class Log:
    def __init__(self):
        self.ops = []          # semua primitif, urut panggil
        self.renders = {}      # id(surface teks) -> info render
        self.alphas = {}       # id(surface teks) -> alpha set_alpha
        # Referensi KUAT ke setiap surface yang id()-nya dipakai sebagai kunci:
        # tanpa ini CPython bisa mendaur ulang alamat surface teks yang sudah
        # dibebaskan dan dua blit berbeda akan membaca info render yang sama.
        self.keep = []
        self.metrics = {}      # "teks|ukuran|gaya" -> [w, h, ascent]
        self.screen_id = None


LOG = Log()
_orig_draw = {}


def _pos(dest):
    if dest is None:
        return [0, 0]
    if isinstance(dest, pygame.Rect):
        return [int(dest.x), int(dest.y)]
    return [int(dest[0]), int(dest[1])]


class TrackSurface(pygame.Surface):
    """Surface layar + surface teks: merekam blit & set_alpha.

    Surface antara milik pygame (aura, glow) TIDAK dibungkus: yang dibutuhkan
    hanya (a) primitif yang digambar di atasnya — terekam lewat patch
    pygame.draw, dan (b) blit-nya ke layar — terekam di sini.
    """

    def blit(self, src, dest=None, *a, **k):
        LOG.ops.append({"op": "blit", "surf": id(self), "src": id(src),
                        "dest": _pos(dest),
                        "src_size": [src.get_width(), src.get_height()]})
        return pygame.Surface.blit(self, src, dest, *a, **k)

    def set_alpha(self, v):
        LOG.alphas[id(self)] = 255 if v is None else int(v)
        return pygame.Surface.set_alpha(self, v)


class FontWrap:
    """Bungkus font pygame: rekam teks, ukuran, gaya, metrik, dan ascent."""

    def __init__(self, f, size, style):
        self.f = f
        self.size_px = int(size)
        self.style = str(style)

    def _key(self, text):
        return "%s|%d|%s" % (text, self.size_px, self.style)

    def render(self, text, aa, color, *a, **k):
        s = self.f.render(text, aa, color, *a, **k)
        t = TrackSurface(s.get_size(), pygame.SRCALPHA)
        pygame.Surface.blit(t, s, (0, 0))
        col = tuple(color) if isinstance(color, (tuple, list)) else (0, 0, 0)
        LOG.renders[id(t)] = {
            "text": text, "size": self.size_px, "style": self.style,
            "color": [int(col[0]), int(col[1]), int(col[2])],
            "wh": [int(s.get_width()), int(s.get_height())],
            "ascent": int(self.f.get_ascent()),
        }
        LOG.metrics[self._key(text)] = [int(s.get_width()),
                                        int(s.get_height()),
                                        int(self.f.get_ascent())]
        LOG.keep.append(t)
        return t

    def size(self, text):
        v = self.f.size(text)
        # Wrap teks entrance mengukur setiap prefix kata: metriknya harus ikut
        # ke fixture supaya BossOverlay.wrap_entrance memutus baris sama.
        LOG.metrics.setdefault(self._key(text),
                               [int(v[0]), int(self.f.get_height()),
                                int(self.f.get_ascent())])
        return v

    def get_height(self):
        return self.f.get_height()

    def get_ascent(self):
        return self.f.get_ascent()

    def get_linesize(self):
        return self.f.get_linesize()

    def __getattr__(self, name):
        return getattr(self.f, name)


def patch():
    for n in DRAW_NAMES:
        _orig_draw[n] = getattr(pygame.draw, n)

        def mk(n=n):
            def wrapped(surf, *a, **k):
                LOG.ops.append({"op": n, "surf": id(surf), "args": a, "kw": k})
                return _orig_draw[n](surf, *a, **k)
            return wrapped
        setattr(pygame.draw, n, mk())
    bb.get_font = lambda size, style="body", bold=False: FontWrap(
        real_get_font(size, style, bold), size, style)
    # Badan boss = strip bake (Fase 5): render_boss mengaku sudah menggambar
    # supaya tidak ada op badan/probe cache yang mencemari rekaman overlay.
    heroes.render_boss = lambda *a, **k: True


def boot():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1))
    patch()


# ═══════════════════════════════════════════════════════════════════
# Op kanonik (kosakata BossOverlay.gd)
# ═══════════════════════════════════════════════════════════════════

def _col(c):
    c = tuple(c)
    return [int(c[0]), int(c[1]), int(c[2])] + ([int(c[3])] if len(c) > 3 else [255])


def _rect(r, dx=0, dy=0):
    if isinstance(r, pygame.Rect):
        x, y, w, h = r.x, r.y, r.width, r.height
    else:
        x, y, w, h = r[0], r[1], r[2], r[3]
    return [int(x) + dx, int(y) + dy, int(w), int(h)]


def _map(o, dx, dy, grp):
    """Satu primitif pygame -> op kanonik, digeser (dx, dy)."""
    n, a, kw = o["op"], o["args"], o["kw"]
    if n == "circle":
        c = [int(a[1][0]) + dx, int(a[1][1]) + dy]
        w = int(a[3]) if len(a) > 3 else int(kw.get("width", 0))
        if w > 0:
            return {"k": "ring", "c": c, "r": int(a[2]), "w": float(w),
                    "col": _col(a[0]), "_grp": grp}
        return {"k": "disc", "c": c, "r": int(a[2]), "col": _col(a[0]),
                "_grp": grp}
    if n == "ellipse":
        w = int(a[2]) if len(a) > 2 else int(kw.get("width", 0))
        return {"k": "ellipse", "rect": _rect(a[1], dx, dy), "col": _col(a[0]),
                "w": w, "_grp": grp}
    if n == "rect":
        w = int(a[2]) if len(a) > 2 else int(kw.get("width", 0))
        br = int(kw.get("border_radius", 0))
        if br == 0 and len(a) > 4:
            br = int(a[4])
        return {"k": "rect", "rect": _rect(a[1], dx, dy), "col": _col(a[0]),
                "w": w, "radius": br, "_grp": grp}
    if n == "polygon":
        w = int(a[2]) if len(a) > 2 else int(kw.get("width", 0))
        if w != 0:
            raise AssertionError("polygon bergaris tidak dipakai Boss.draw")
        return {"k": "poly", "col": _col(a[0]), "_grp": grp,
                "pts": [[int(p[0]) + dx, int(p[1]) + dy] for p in a[1]]}
    raise AssertionError("primitif tak dikenal: %s" % n)


def collapse_bands(ops):
    """Lingkaran ISI sepusat, RGB sama, digambar besar->kecil di surface
    SRCALPHA: pygame MENIMPA, jadi hasilnya PITA alpha rata (inner < d <=
    outer). Godot draw_circle MEM-BLEND, sehingga BossOverlay mengekspresikan
    run ini sebagai op `band` yang tidak saling menimpa.
    """
    out = []
    i = 0
    while i < len(ops):
        o = ops[i]
        if o["k"] != "disc":
            out.append(o)
            i += 1
            continue
        j = i + 1
        while (j < len(ops) and ops[j]["k"] == "disc"
               and ops[j]["c"] == o["c"]
               and ops[j]["col"][:3] == o["col"][:3]
               and ops[j]["r"] < ops[j - 1]["r"]):
            j += 1
        run = ops[i:j]
        if len(run) < 2:
            out.append(o)
            i += 1
            continue
        for n_i, d in enumerate(run):
            inner = run[n_i + 1]["r"] if n_i + 1 < len(run) else 0
            out.append({"k": "band", "c": list(d["c"]), "ri": int(inner),
                        "ro": int(d["r"]), "col": list(d["col"]),
                        "_grp": d["_grp"]})
        i = j
    return out


def canon(log):
    """Log rekaman -> daftar op kanonik urut gambar (koordinat layar/dunia)."""
    per_surf = {}
    for o in log.ops:
        if o["op"] in DRAW_NAMES:
            per_surf.setdefault(o["surf"], []).append(o)
    out = []
    gid = 0
    for o in log.ops:
        if o["op"] == "blit":
            if o["surf"] != log.screen_id:
                continue                      # blit internal harness
            src = o["src"]
            if src in log.renders:
                info = log.renders[src]
                alpha = log.alphas.get(src, 255)
                out.append({
                    "k": "text", "text": info["text"], "size": info["size"],
                    "style": info["style"],
                    "col": list(info["color"]) + [int(alpha)],
                    "anchor": "topleft", "pos": list(o["dest"]),
                    "wh": list(info["wh"]), "asc": info["ascent"],
                    "_grp": None,
                })
            elif src in per_surf:
                gid += 1
                dx, dy = int(o["dest"][0]), int(o["dest"][1])
                mapped = [_map(x, dx, dy, gid) for x in per_surf[src]]
                out.extend(collapse_bands(mapped))
            else:
                raise AssertionError(
                    "blit tak dikenal (badan boss harus dinetralkan): "
                    "src_size=%s dest=%s" % (o["src_size"], o["dest"]))
        elif o["op"] in DRAW_NAMES and o["surf"] == log.screen_id:
            out.append(_map(o, 0, 0, None))
        elif o["op"] in DRAW_NAMES:
            pass                                # digambar di surface antara
        else:
            raise AssertionError("op tak dikenal: %s" % o["op"])
    return out


def strip(ops):
    """Buang kunci internal oracle sebelum masuk fixture."""
    return [{k: v for k, v in o.items() if not k.startswith("_")} for o in ops]


# ═══════════════════════════════════════════════════════════════════
# Eksekutor ulang (verifikasi piksel konversi)
# ═══════════════════════════════════════════════════════════════════

def _draw_op(surf, o, expand_bands=False):
    k, col = o["k"], tuple(o["col"])
    if k == "disc":
        pygame.draw.circle(surf, col, tuple(o["c"]), int(o["r"]))
    elif k == "ring":
        pygame.draw.circle(surf, col, tuple(o["c"]), int(o["r"]),
                           int(round(o["w"])))
    elif k == "band":
        if not expand_bands:
            raise AssertionError("band di luar kelompok surface antara")
        # Kembalikan ke bentuk pygame: lingkaran ISI radius luar, digambar
        # berurutan luar->dalam sehingga yang lebih kecil MENIMPA pusatnya.
        pygame.draw.circle(surf, col, tuple(o["c"]), int(o["ro"]))
    elif k == "ellipse":
        pygame.draw.ellipse(surf, col, tuple(o["rect"]), int(o["w"]))
    elif k == "rect":
        br = int(o.get("radius", 0))
        if br:
            pygame.draw.rect(surf, col, tuple(o["rect"]), int(o["w"]),
                             border_radius=br)
        else:
            pygame.draw.rect(surf, col, tuple(o["rect"]), int(o["w"]))
    elif k == "poly":
        pygame.draw.polygon(surf, col, [tuple(p) for p in o["pts"]])
    elif k == "text":
        f = real_get_font(int(o["size"]), str(o["style"]))
        t = f.render(o["text"], True, col[:3])
        if len(col) > 3 and int(col[3]) < 255:
            t.set_alpha(int(col[3]))
        surf.blit(t, tuple(o["pos"]))
    else:
        raise AssertionError("op kanonik tak dikenal: %s" % k)


def reexec(ops, surf):
    """Gambar op kanonik dengan semantik pygame.

    Op `_grp=None` digambar langsung ke tujuan (pygame MENIMPA, alpha warna
    ikut tertulis apa adanya). Op berkelompok berasal dari satu surface antara
    pygame: digambar ke surface SRCALPHA lalu di-blit SEKALI (src-over), sama
    seperti blit aslinya — ini yang membuat pita alpha aura benar.
    """
    i = 0
    while i < len(ops):
        grp = ops[i].get("_grp")
        if grp is None:
            _draw_op(surf, ops[i])
            i += 1
            continue
        j = i
        while j < len(ops) and ops[j].get("_grp") == grp:
            j += 1
        tmp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for o in ops[i:j]:
            _draw_op(tmp, o, expand_bands=True)
        surf.blit(tmp, (0, 0))
        i = j


def rgba_bytes(surf):
    fn = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
    return fn(surf, "RGBA")


def first_diff(a, b, w):
    for i in range(0, min(len(a), len(b)), 4):
        if a[i:i + 4] != b[i:i + 4]:
            px = (i // 4) % w
            py = (i // 4) // w
            return (px, py, tuple(a[i:i + 4]), tuple(b[i:i + 4]))
    return None


# ═══════════════════════════════════════════════════════════════════
# State (masukan BossOverlay.gd) + pemisah lapisan
# ═══════════════════════════════════════════════════════════════════

def state_of(b, has_renderer):
    is_true = b.boss_class == "true"
    return {
        "x": int(b.x),
        "y": int(b.y),
        "radius": int(b.radius),
        "boss_class": str(b.boss_class),
        "name": str(b.name),
        "hp": float(b.hp),
        "max_hp": float(b.max_hp),
        "color": _col(b.color)[:3],
        "color_dark": _col(b.color_dark)[:3],
        "entrance_color": _col(b.entrance_color)[:3],
        # 0 = tidak ada entri BOSS_LABEL_TOP -> BossOverlay jatuh ke `radius`
        # (paritas `BOSS_LABEL_TOP.get(boss_type, r)` base_boss.py:6223).
        "label_top": int(bb.BOSS_LABEL_TOP.get(b.boss_type, 0)),
        "has_renderer": bool(has_renderer),
        "hurt_flash": bool(getattr(b, "hurt_flash_timer", 0) > 0),
        "anim_time": int(b.anim_time),
        "pulse": float(getattr(b, "pulse", 0.0)),
        "enrage_pulse": float(getattr(b, "enrage_pulse", 0.0)),
        "is_enraged": bool(getattr(b, "is_enraged", False)),
        "ability_active": bool(getattr(b, "ability_active", False)),
        "ability_range": float(getattr(b, "ability_range", 0.0)),
        "entrance_timer": int(b.entrance_timer),
        "entrance_max": 180 if is_true else 120,
        "entrance_text": str(getattr(b, "entrance_text", "")),
        "screen_w": SCREEN_W,
        "debuff": {
            "slow": bool(getattr(b, "slow_timer", 0) > 0),
            "atk_slow": bool(getattr(b, "atk_slow_timer", 0) > 0),
            "skill_down": bool(getattr(b, "skill_down_timer", 0) > 0),
            "anti_heal": bool(getattr(b, "anti_heal_timer", 0) > 0),
            "burn": bool(getattr(b, "burn_timer", 0) > 0),
        },
    }


def head_top(state):
    """base_boss.py:6219-6223."""
    r = state["radius"]
    if not state["has_renderer"]:
        return r + 12
    return max(int(state["label_top"] or r), r)


def bar_geom(state):
    is_true = state["boss_class"] == "true"
    bar_w = 70 if is_true else 60
    bar_h = 10 if is_true else 8
    bx = state["x"] - bar_w // 2
    by = state["y"] - head_top(state) - 6 - bar_h
    return bx, by, bar_w, bar_h


def split_layers(state, ops, name):
    """Pisahkan lapisan BAWAH badan (aura/bayangan/debuff/badan generik) dari
    lapisan ATAS badan (HP bar + papan nama) — pemisah = rect bg HP bar.
    """
    if state["entrance_timer"] > 0:
        check("%s: entrance eksklusif (tanpa bar/papan nama)" % name,
              all(o["k"] in ("disc", "band", "text") for o in ops),
              str([o["k"] for o in ops]))
        return ops, []
    bx, by, bar_w, bar_h = bar_geom(state)
    want = {"k": "rect", "rect": [bx, by, bar_w, bar_h],
            "col": BAR_BG + [255], "w": 0, "radius": 0}
    idx = None
    for i, o in enumerate(ops):
        if (o["k"] == "rect" and o["rect"] == want["rect"]
                and o["col"] == want["col"] and o["w"] == 0
                and int(o.get("radius", 0)) == 0):
            idx = i
            break
    check("%s: HP bar bg di geometri terhitung %s" % (name, want["rect"]),
          idx is not None, "tidak ditemukan")
    if idx is None:
        return ops, []
    return ops[:idx], ops[idx:]


# ═══════════════════════════════════════════════════════════════════
# Menjalankan satu skenario
# ═══════════════════════════════════════════════════════════════════

def make_boss(boss_type):
    b = bb.Boss(boss_type)
    b.x, b.y = 600.0, 400.0
    return b


def run(name, boss_type, mutate, has_renderer=True):
    """Render satu skenario, rekam, konversi, verifikasi piksel."""
    global LOG
    LOG = Log()
    bb._BOSS_AURA_CACHE.clear()      # cache aura mengkuantisasi fase sinus
    bb._BOSS_AURA_PIXELS[0] = 0      # -> bangun ulang dengan pulse eksak
    # has_renderer=True: `_draw_fn` bukan None (jadi head_top memakai
    # BOSS_LABEL_TOP) tetapi heroes.render_boss di atas sudah dinetralkan
    # sehingga badan tidak meninggalkan op apa pun.
    bb._get_boss_draw_func = (lambda bt: _NOOP_RENDERER) if has_renderer \
        else (lambda bt: None)
    b = make_boss(boss_type)
    mutate(b)
    screen = TrackSurface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    LOG.screen_id = id(screen)
    b.draw(screen)
    ops = canon(LOG)
    state = state_of(b, has_renderer)
    state["metrics"] = dict(LOG.metrics)

    # ── verifikasi piksel: op kanonik == render pygame asli ──
    again = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    reexec(ops, again)
    ra, rb = rgba_bytes(screen), rgba_bytes(again)
    if ra == rb:
        check("%s: round-trip piksel identik (%d op)" % (name, len(ops)), True)
    else:
        d = first_diff(ra, rb, SCREEN_W)
        check("%s: round-trip piksel identik (%d op)" % (name, len(ops)),
              False, "beda pertama di %s" % (d,))

    under, over = split_layers(state, ops, name)
    return {
        "name": name,
        "boss_type": boss_type,
        "state": state,
        "underlay": strip(under),
        "over": strip(over),
        "_ops": ops,
        "_screen": screen,
        "_boss": b,
    }


# ═══════════════════════════════════════════════════════════════════
# Profil alpha radial (cermin BossOverlay.radial_profile)
# ═══════════════════════════════════════════════════════════════════

def model_profile(ops, center, max_d):
    prof = [0] * (max_d + 1)
    for o in ops:
        if o["k"] not in ("band", "disc", "ring") or list(o["c"]) != list(center):
            continue
        alpha = int(o["col"][3])
        if o["k"] == "band":
            for d in range(max_d + 1):
                # ri <= 0 = cakram penuh (menutup d = 0), selain itu
                # pita menutup inner < d <= outer.
                if d <= o["ro"] and (d > o["ri"] or o["ri"] <= 0):
                    prof[d] = alpha
        elif o["k"] == "disc":
            for d in range(max_d + 1):
                if d <= o["r"]:
                    prof[d] = alpha
        else:
            hw = o["w"] / 2.0
            for d in range(max_d + 1):
                if abs(d - o["r"]) <= hw:
                    prof[d] = alpha
    return prof


def naive_stack_profile(ops, center, max_d):
    """Model port NAIF: setiap lingkaran isi di-blend (draw_circle Godot)."""
    prof = [0.0] * (max_d + 1)
    for o in ops:
        if o["k"] != "band" or list(o["c"]) != list(center):
            continue
        a = int(o["col"][3]) / 255.0
        for d in range(max_d + 1):
            if d <= o["ro"]:
                prof[d] = prof[d] + a * (1.0 - prof[d])
    return [int(round(x * 255)) for x in prof]


def measured_profile(surf, center, max_d):
    return [surf.get_at((center[0] + d, center[1]))[3] for d in range(max_d + 1)]


def check_aura_ray(scen, label, max_d=None):
    """Sinar +x dari pusat boss harus murni aura (bayangan di bawah, bar di
    atas, badan dinetralkan) -> profil terukur == model pita BossOverlay."""
    state = scen["state"]
    c = [state["x"], state["y"]]
    aura_ops = [o for o in scen["_ops"]
                if o["k"] in ("band", "ring") and list(o["c"]) == c]
    if not aura_ops:
        check("%s: ada op aura" % label, False, "tidak ada band/ring sepusat")
        return
    r_max = max(int(o.get("ro", o.get("r", 0))) for o in aura_ops)
    n = max_d or (r_max + 3)
    got = measured_profile(scen["_screen"], c, n)
    want = model_profile(aura_ops, c, n)
    # Raster pygame bisa meleset 1 px di tepi pita; alpha-nya harus sama.
    tol = 1
    worst = 0
    bad_at = -1
    for d in range(n + 1):
        if abs(got[d] - want[d]) > tol and not _edge_of_band(aura_ops, d):
            if abs(got[d] - want[d]) > worst:
                worst = abs(got[d] - want[d])
                bad_at = d
    check("%s: profil alpha sinar +x == model pita" % label, worst == 0,
          "beda %d di d=%d (ukur %s vs model %s)"
          % (worst, bad_at, got[max(0, bad_at - 1):bad_at + 2],
             want[max(0, bad_at - 1):bad_at + 2]))
    check("%s: alpha pusat %d (bukan hasil blend)" % (label, want[0]),
          got[0] == want[0], "ukur %d vs model %d" % (got[0], want[0]))
    naive = naive_stack_profile(aura_ops, c, n)
    if any(o["k"] == "band" for o in aura_ops):
        # Port naif (draw_circle bertumpuk) selalu lebih pekat di pusat; kalau
        # alpha pygame sudah besar, blend-nya jenuh mendekati 255 sehingga
        # rasio 2x tidak tercapai -> pakai selisih absolut + relatif.
        gap = naive[0] - want[0]
        check("%s: model naif (blend) MELESET dari pygame" % label,
              want[0] == 0 or gap >= max(8, int(want[0] * 0.25)),
              "naif %d vs pygame %d (selisih %d)" % (naive[0], want[0], gap))
    check("%s: tepi luar transparan" % label, got[n] == 0 and want[n] == 0,
          "ukur %d model %d" % (got[n], want[n]))


def _edge_of_band(ops, d):
    for o in ops:
        if o["k"] == "band" and d in (o["ri"], o["ro"], o["ro"] + 1):
            return True
        if o["k"] == "ring" and abs(d - o["r"]) <= o["w"]:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# Urutan lapisan
# ═══════════════════════════════════════════════════════════════════

def first_index(ops, pred):
    for i, o in enumerate(ops):
        if pred(o):
            return i
    return None


def check_order(scen):
    """Urutan pygame: ability aura -> enrage -> true -> bayangan -> debuff ->
    badan generik -> HP bar -> papan nama (base_boss.py:6124-6276)."""
    name, state, ops = scen["name"], scen["state"], scen["_ops"]
    if state["entrance_timer"] > 0:
        # ENTRANCE: pygame `return` setelah _draw_entrance (base_boss.py:6135)
        # -> hanya cakram entrance + teks, tanpa aura/bayangan/bar/papan nama.
        kinds = sorted(set(o["k"] for o in ops))
        check("%s: entrance hanya disc/band/text" % name,
              set(kinds) <= {"disc", "band", "text"}, str(kinds))
        check("%s: entrance tanpa lapisan badan" % name,
              not any(o["k"] in ("ellipse", "rect", "poly", "ring")
                      for o in ops))
        return
    marks = []
    if state["ability_active"]:
        i = first_index(ops, lambda o: o["k"] == "band"
                        and o["col"][:3] == state["entrance_color"]
                        and o["ro"] > state["radius"] + 20)
        marks.append(("ability", i))
    if state["is_enraged"]:
        enr = [255, 50, 40] if state["boss_class"] == "true" else [255, 140, 30]
        i = first_index(ops, lambda o: o["k"] == "ring" and o["col"][:3] == enr)
        marks.append(("enrage", i))
    if state["boss_class"] == "true":
        i = first_index(ops, lambda o: o["k"] == "band"
                        and o["col"][:3] == state["color"]
                        and o["ro"] == state["radius"] + 15 - 2)
        marks.append(("true", i))
    i = first_index(ops, lambda o: o["k"] == "ellipse" and o["col"] == SHADOW_COL)
    marks.append(("shadow", i))
    if any(state["debuff"].values()):
        i = first_index(ops, lambda o: (
            o["k"] == "ellipse" and o["col"][:3] == [150, 220, 255])
            or (o["k"] == "disc" and o["col"][:3] == [255, 140, 40])
            or (o["k"] == "rect" and o["col"][:3] == [10, 10, 14]))
        marks.append(("debuff", i))
    if not state["has_renderer"]:
        i = first_index(ops, lambda o: o["k"] == "disc"
                        and o["col"][:3] == [0, 0, 0]
                        and o["r"] == state["radius"] + 2)
        marks.append(("body", i))
    if state["entrance_timer"] <= 0:
        bx, by, bw, bh = bar_geom(state)
        i = first_index(ops, lambda o: o["k"] == "rect"
                        and o["rect"] == [bx, by, bw, bh]
                        and o["col"][:3] == BAR_BG)
        marks.append(("bar", i))
        i = first_index(ops, lambda o: o["k"] == "rect"
                        and int(o.get("radius", 0)) == 3
                        and o["col"][:3] == PLATE_BG)
        marks.append(("plate", i))
        i = first_index(ops, lambda o: o["k"] == "text")
        marks.append(("label", i))
    missing = [m for m, i in marks if i is None]
    check("%s: semua penanda lapisan ditemukan %s" % (name, [m for m, _ in marks]),
          not missing, "hilang %s" % missing)
    idx = [i for _, i in marks if i is not None]
    check("%s: urutan lapisan naik %s" % (name, [m for m, _ in marks]),
          idx == sorted(idx), str(list(zip([m for m, _ in marks], idx))))


# ═══════════════════════════════════════════════════════════════════
# Skenario
# ═══════════════════════════════════════════════════════════════════

def no_entrance(b):
    b.entrance_timer = 0


def all_debuffs(b):
    b.entrance_timer = 0
    b.slow_timer = 60
    b.atk_slow_timer = 60
    b.skill_down_timer = 60
    b.anti_heal_timer = 60
    b.burn_timer = 60
    b.anim_time = 7


def widest_entrance_text():
    """Boss dengan entrance_text terlebar (menguji wrap 1000 px)."""
    best, best_w = None, -1
    for k, v in boss_data.get_all_boss_types().items():
        is_true = v.get("boss_class") == "true"
        f = real_get_font(28 if is_true else 24, "body_semibold")
        w = f.size(str(v.get("entrance_text", "")))[0]
        if w > best_w:
            best, best_w = k, w
    return best, best_w


def scenarios():
    """(nama, tipe boss, mutasi, has_renderer)."""
    wide, _w = widest_entrance_text()
    out = [
        # ── ENTRANCE (jalur eksklusif: pygame `return` setelahnya) ──
        ("entrance_mini_full", "gornak", lambda b: None, True),
        ("entrance_mini_half", "gornak",
         lambda b: setattr(b, "entrance_timer", 60), True),
        ("entrance_mini_text_edge", "gornak",
         lambda b: (setattr(b, "entrance_timer", 61),
                    setattr(b, "anim_time", 7)), True),
        ("entrance_mini_last", "gornak",
         lambda b: setattr(b, "entrance_timer", 1), True),
        ("entrance_true_full", "abaddon", lambda b: None, True),
        ("entrance_true_mid", "abaddon",
         lambda b: (setattr(b, "entrance_timer", 100),
                    setattr(b, "anim_time", 24)), True),
        ("entrance_widest_text", wide,
         lambda b: setattr(b, "anim_time", 3), True),
        # ── AURA ──
        ("aura_ability_0", "gornak",
         lambda b: (no_entrance(b), setattr(b, "ability_active", True)), True),
        ("aura_ability_7", "gornak",
         lambda b: (no_entrance(b), setattr(b, "ability_active", True),
                    setattr(b, "anim_time", 7)), True),
        ("aura_ability_min", "gornak",
         lambda b: (no_entrance(b), setattr(b, "ability_active", True),
                    setattr(b, "anim_time", 24)), True),
        ("aura_ability_true", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "ability_active", True),
                    setattr(b, "anim_time", 11)), True),
        ("aura_enrage_mini", "gornak",
         lambda b: (no_entrance(b), setattr(b, "is_enraged", True),
                    setattr(b, "enrage_pulse", 1.0),
                    setattr(b, "hp", b.max_hp * 0.3)), True),
        ("aura_enrage_mini0", "gornak",
         lambda b: (no_entrance(b), setattr(b, "is_enraged", True)), True),
        ("aura_enrage_true", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "is_enraged", True),
                    setattr(b, "enrage_pulse", 2.0),
                    setattr(b, "hp", b.max_hp * 0.2)), True),
        ("aura_true_0", "abaddon", no_entrance, True),
        ("aura_true_max", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "pulse", math.pi / 2)), True),
        ("aura_true_min", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "pulse", math.pi * 1.5)), True),
        ("aura_all_three", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "ability_active", True),
                    setattr(b, "anim_time", 5),
                    setattr(b, "is_enraged", True),
                    setattr(b, "enrage_pulse", 0.7),
                    setattr(b, "hp", b.max_hp * 0.4)), True),
        # ── DEBUFF MENARA ──
        ("debuff_slow", "gornak",
         lambda b: (no_entrance(b), setattr(b, "slow_timer", 60)), True),
        ("debuff_burn", "gornak",
         lambda b: (no_entrance(b), setattr(b, "burn_timer", 60),
                    setattr(b, "anim_time", 7)), True),
        ("debuff_burn_flick1", "gornak",
         lambda b: (no_entrance(b), setattr(b, "burn_timer", 60)), True),
        ("debuff_all", "abaddon", all_debuffs, True),
        ("debuff_pips_two", "gornak",
         lambda b: (no_entrance(b), setattr(b, "skill_down_timer", 30),
                    setattr(b, "anti_heal_timer", 30)), True),
        # ── HP BAR + PAPAN NAMA ──
        ("plate_mini_full", "gornak", no_entrance, True),
        ("plate_mini_mid", "gornak",
         lambda b: (no_entrance(b), setattr(b, "hp", b.max_hp * 0.4)), True),
        ("plate_mini_low", "gornak",
         lambda b: (no_entrance(b), setattr(b, "hp", b.max_hp * 0.1),
                    setattr(b, "is_enraged", True)), True),
        ("plate_fill_zero", "gornak",
         lambda b: (no_entrance(b), setattr(b, "hp", 1.0)), True),
        ("plate_true_full", "abaddon", no_entrance, True),
        ("plate_true_enraged", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "is_enraged", True),
                    setattr(b, "hp", b.max_hp * 0.45)), True),
        ("plate_clamp_left", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "x", 8.0)), True),
        ("plate_clamp_right", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "x", 1275.0)), True),
        ("plate_clamp_left_mini", "gornak",
         lambda b: (no_entrance(b), setattr(b, "x", 2.0)), True),
        # ── BADAN GENERIK (tanpa strip bake) ──
        ("generic_mini", "gornak", no_entrance, False),
        ("generic_true", "abaddon", no_entrance, False),
        ("generic_hurt_mini", "gornak",
         lambda b: (no_entrance(b), setattr(b, "hurt_flash_timer", 5)), False),
        ("generic_hurt_true", "abaddon",
         lambda b: (no_entrance(b), setattr(b, "hurt_flash_timer", 5),
                    setattr(b, "is_enraged", True)), False),
        ("generic_debuff", "gornak", all_debuffs, False),
    ]
    # ── sampel lintas data: radius/label_top/kelas berbeda ──
    types = sorted(boss_data.get_all_boss_types().keys())
    for i, t in enumerate(types[::18]):
        out.append(("sample_%02d_%s" % (i, t), t, no_entrance, True))
    return out


# ═══════════════════════════════════════════════════════════════════
# Pemeriksaan data (bukan per skenario)
# ═══════════════════════════════════════════════════════════════════

def check_data():
    section("Data: BOSS_LABEL_TOP + wrap teks entrance")
    allb = boss_data.get_all_boss_types()
    missing = [k for k in allb if k not in bb.BOSS_LABEL_TOP]
    check("BOSS_LABEL_TOP menutup %d boss" % len(allb), not missing,
          "tanpa entri: %s" % missing[:8])
    extra = [k for k in bb.BOSS_LABEL_TOP if k not in allb]
    check("BOSS_LABEL_TOP tidak punya entri liar", not extra, str(extra[:8]))
    small = [k for k, v in allb.items()
             if k in bb.BOSS_LABEL_TOP
             and bb.BOSS_LABEL_TOP[k] < int(v.get("radius", 30))]
    check("ada boss dengan label_top < radius (max() dipakai)", bool(small),
          "tidak ada: cabang max() tak pernah teruji")
    over = []
    for k, v in allb.items():
        is_true = v.get("boss_class") == "true"
        f = real_get_font(28 if is_true else 24, "body_semibold")
        txt = str(v.get("entrance_text", ""))
        if not txt:
            over.append(k)
        for line in _wrap(f, txt):
            if f.size(line)[0] > 1000:
                over.append("%s:%d" % (k, f.size(line)[0]))
    check("semua entrance_text <= 1000 px per baris & tidak kosong",
          not over, str(over[:6]))


def _wrap(font, text):
    lines, cur = [], ""
    for w in text.split(" "):
        trial = (cur + " " + w).strip()
        if font.size(trial)[0] <= 1000:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def check_entrance_wrap_forced():
    """Wrap multi-baris: teks panjang sintetis (data asli tidak pernah lewat
    1000 px, jadi cabang `else` di base_boss.py:6406 butuh masukan paksa)."""
    section("Entrance: wrap multi-baris (teks paksa)")
    global LOG
    LOG = Log()
    bb._BOSS_AURA_CACHE.clear()
    bb._BOSS_AURA_PIXELS[0] = 0
    bb._get_boss_draw_func = lambda bt: _NOOP_RENDERER
    b = make_boss("abaddon")
    b.entrance_text = ("THE LORD OF AVERNUS RIDES FORTH AND THE SKY ITSELF "
                       "SHALL REMEMBER THIS NAME FOR A THOUSAND YEARS "
                       "AGAIN AND AGAIN UNTIL THE LAST STAR FALLS") * 4
    b.anim_time = 3
    screen = TrackSurface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    LOG.screen_id = id(screen)
    b.draw(screen)
    ops = canon(LOG)
    state = state_of(b, True)
    state["metrics"] = dict(LOG.metrics)
    again = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    reexec(ops, again)
    check("wrap paksa: round-trip piksel identik",
          rgba_bytes(screen) == rgba_bytes(again))
    texts = [o for o in ops if o["k"] == "text"]
    lines = len(texts) // 2
    check("wrap paksa: lebih dari satu baris", lines > 1, "%d baris" % lines)
    check("wrap paksa: bayangan hitam lebih dulu, lalu teks (offset +2/+2)",
          all(texts[i]["col"][:3] == [0, 0, 0]
              and texts[i + 1]["pos"][0] - texts[i]["pos"][0] == -2
              and texts[i + 1]["pos"][1] - texts[i]["pos"][1] == -2
              for i in range(0, len(texts), 2)),
          "urutan/offset salah")
    mains = texts[1::2]
    ys = [o["pos"][1] for o in mains]
    steps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    h = mains[0]["wh"][1]
    start_y = 84 - (lines - 1) * 18
    check("wrap paksa: jarak antar baris 34 px", all(s == 34 for s in steps),
          "steps=%s" % steps[:6])
    check("wrap paksa: baris pertama di start_y - h//2 (%d)" % (start_y - h // 2),
          ys[0] == start_y - h // 2, "y=%d" % ys[0])
    check("wrap paksa: semua baris di tengah layar (x = 640 - w//2)",
          all(o["pos"][0] == 640 - o["wh"][0] // 2 for o in mains),
          str([(o["pos"][0], o["wh"][0]) for o in mains[:3]]))
    under, over = split_layers(state, ops, "wrap paksa")
    return {"name": "entrance_wrap_forced", "boss_type": "abaddon",
            "state": state, "underlay": strip(under), "over": strip(over),
            "_ops": ops, "_screen": screen, "_boss": b}


# ═══════════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════════

def main():
    boot()
    print("pygame %s | Boss.draw base_boss.py:6124-6430 + _core.py:1037-1085"
          % pygame.version.ver)

    check_data()

    section("Skenario draw (rekam -> op kanonik -> verifikasi piksel)")
    results = []
    for name, bt, mutate, has_rend in scenarios():
        scen = run(name, bt, mutate, has_rend)
        check_order(scen)
        results.append(scen)

    forced = check_entrance_wrap_forced()
    results.append(forced)

    section("Profil alpha aura (sinar +x dari pusat, render sungguhan)")
    for scen in results:
        if scen["name"] in ("aura_ability_0", "aura_ability_7",
                            "aura_ability_min", "aura_enrage_mini",
                            "aura_enrage_mini0",
                            "aura_true_0", "aura_true_max", "aura_true_min"):
            check_aura_ray(scen, scen["name"])

    section("Statistik fixture")
    n_ops = sum(len(s["underlay"]) + len(s["over"]) for s in results)
    kinds = {}
    for s in results:
        for o in s["underlay"] + s["over"]:
            kinds[o["k"]] = kinds.get(o["k"], 0) + 1
    print("  %d skenario, %d op, jenis: %s"
          % (len(results), n_ops, dict(sorted(kinds.items()))))
    for need in ("disc", "band", "ring", "ellipse", "rect", "poly", "text"):
        check("semua jenis op terpakai: %s" % need, kinds.get(need, 0) > 0,
              "0 op")

    fixture = {
        "meta": {
            "generated_by": "tools/test_boss_draw_parity.py",
            "source": ["bosses/base_boss.py:6124-6430 (Boss.draw)",
                       "bosses/base_boss.py:6277-6375 (aura enrage/generic/true)",
                       "bosses/base_boss.py:6376-6430 (_draw_entrance)",
                       "_core.py:1037-1085 (_draw_tower_debuff_fx)"],
            "target": ["godot/scripts/render/BossOverlay.gd",
                       "godot/scenes/boss/BossPlate.gd",
                       "godot/scenes/boss/Boss.gd (overlay_state)"],
            "pygame": pygame.version.ver,
            "screen": [SCREEN_W, SCREEN_H],
            "scenarios": len(results),
            "ops": n_ops,
            "note": (
                "Op = kosakata gambar BossOverlay.gd, koordinat dunia/layar "
                "pygame (arena 1280x720 == layar). Warna [r,g,b,a] 0..255. "
                "`band` = pita alpha anulus inner < d <= outer (pygame "
                "draw.circle MENIMPA, bukan blend). `underlay` digambar node "
                "Boss (di bawah badan), `over` oleh BossPlate (di atas badan). "
                "state.metrics = metrik teks pygame (lebar/tinggi/ascent) yang "
                "disuntik ke BossOverlay supaya geometri teks dibandingkan "
                "dengan angka pygame, bukan metrik HarfBuzz Godot. Badan boss "
                "TIDAK direkam (strip bake Fase 5); skenario has_renderer=false "
                "merekam _draw_generic_body. Alpha bayangan (0,0,0,120) adalah "
                "nilai SUMBER pygame: di layar nyata pygame (surface tanpa "
                "SRCALPHA) alpha itu dibuang sehingga bayangan tampil hitam "
                "pekat, sedangkan kanvas Godot selalu blend - deviasi piksel "
                "yang dicatat di docs/AUDIT_ULANG_DARI_AWAL.md."),
        },
        "scenarios": [
            {"name": s["name"], "boss_type": s["boss_type"], "state": s["state"],
             "underlay": s["underlay"], "over": s["over"]}
            for s in results
        ],
    }
    payload = json.dumps(fixture, ensure_ascii=False, indent=1,
                         sort_keys=False) + "\n"

    section("Fixture (harus segar terhadap pygame ASLI)")
    if WRITE_FIXTURE:
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        with open(FIXTURE, "w", encoding="utf-8") as f:
            f.write(payload)
        print("  fixture ditulis -> %s (%d KB)"
              % (os.path.relpath(FIXTURE, ROOT), len(payload) // 1024))
    elif not os.path.exists(FIXTURE):
        check("fixture ada", False,
              "%s hilang - jalankan: python3 tools/test_boss_draw_parity.py"
              " --write-fixture" % os.path.relpath(FIXTURE, ROOT))
    else:
        current = open(FIXTURE, encoding="utf-8").read()
        if current == payload:
            check("fixture segar (%d skenario, %d op)"
                  % (len(results), n_ops), True)
        else:
            stale = _stale_scenarios(current, fixture)
            check("fixture segar (%d skenario, %d op)"
                  % (len(results), n_ops), False,
                  "basi terhadap Boss.draw pygame (skenario: %s) - "
                  "regenerasi: python3 tools/test_boss_draw_parity.py"
                  " --write-fixture" % (stale or "format/meta"))
    print("\n%d OK, %d FAIL" % (_pass, _fail))
    return 1 if _fail else 0


def _stale_scenarios(current, fresh):
    """Nama skenario yang berbeda antara fixture di-commit dan hasil baru."""
    try:
        stored = json.loads(current)
    except ValueError:
        return "json rusak"
    out = []
    got = {s["name"]: s for s in stored.get("scenarios", [])}
    for s in fresh["scenarios"]:
        old = got.get(s["name"])
        if old is None:
            out.append("%s (baru)" % s["name"])
            continue
        for key in ("state", "underlay", "over"):
            if old.get(key) != s[key]:
                out.append("%s.%s" % (s["name"], key))
    for name in got:
        if name not in {s["name"] for s in fresh["scenarios"]}:
            out.append("%s (hilang)" % name)
    return ", ".join(out[:8]) + (" ..." if len(out) > 8 else "")


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description=__doc__)
    _parser.add_argument("--write-fixture", action="store_true",
                         help="tulis ulang godot/tests/fixtures/boss_draw.json")
    WRITE_FIXTURE = _parser.parse_args().write_fixture
    sys.exit(main())
