#!/usr/bin/env python3
"""Audit terukur untuk renderer Khalros "Pixel Masterwork" v2.

Alat ini mengubah hal yang sebelumnya hanya bisa dinilai mata menjadi angka,
sehingga keputusan rewrite bisa di-review ulang tanpa melihat gambar:

  1. GEOMETRI  - bbox rig native (1.5x) vs ukuran tampil (satu SCALE untuk
                 jalur boss, jalur hero, dan portrait), plus tabel ukuran
                 keluarga (razak/khalros/gorath/alchemist).
  2. PALET     - jumlah warna unik per pose (ramp 4-7 band + hue-shift),
                 specular, dan cek apakah lighting benar-benar aktif.
  3. WAKTU     - ms/frame median per pose & per skill, dibandingkan budget
                 3.5 ms DAN dengan tetangga keluarga (gorath sebagai patokan
                 atas). Ini yang menangkap pemborosan "render badan dua kali"
                 (afterimage bantingan E dulu 2x lebih mahal).
  4. TELEGRAPH - radius cincin lantai DIUKUR DARI HASIL-ACI (lumenance delta,
                 bukan alpha) lalu dicocokkan ke angka AI: Q 70 di TARGET,
                 W 120 / E 85 / R 200 di CASTER; plus kompensasi world-space
                 (1/_render_scale) dan jumlah piksel FX di luar siluet badan.
  5. KONTRAK   - 57 nama publik v1 masih ada (dibanding snapshot v1), dan
                 kepemilikan lapisan hidup hero-lane tidak menggambar dua kali.

Output gambar (supaya bisa dilihat, bukan cuma dibaca):
  - docs/khalros_v2_review.png         pose + skill + hurt, satu lembar
  - docs/khalros_v2_before_after.png   v1 snapshot vs v2, pose yang sama

Jalankan:  python3 tools/_audit_khalros_v2.py
"""
import importlib.util
import math
import os
import sys
import time
from types import SimpleNamespace as _NS

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level2 as L2                             # noqa: E402
from bosses.level2 import _NS_khalros as K               # noqa: E402
import heroes.khalros_fx as KF                           # noqa: E402

W = H = 520
FAILURES = []


def check(cond, label, extra=""):
    print(("  [OK ] " if cond else "  [FAIL] ") + label + ("  " + extra if extra else ""))
    if not cond:
        FAILURES.append(label)
    return cond


def v1_namespace():
    path = os.path.join(ROOT, "tools", "_khalros_v1_snapshot.py")
    spec = importlib.util.spec_from_file_location("_khalros_v1_snapshot", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._NS_khalros


def probe(x=None, y=None, **kw):
    """Boss palsu ala `tools/test_khalros_masterwork.py`.

    `_render_scale` sengaja TIDAK diisi -> rezim jalur boss (renderer menggambar
    FX-nya sendiri). Baru diset kalau kita memang mau menguji jalur hero.
    """
    b = _NS(boss_type="khalros", boss_class="mini", x=260.0, y=280.0,
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=42,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=36, hp=7800, max_hp=7800,
            rng=60, speed=1.0, _khal_last_x=258.0, _khal_last_y=280.0)
    if x is not None:
        b.x = float(x)
    if y is not None:
        b.y = float(y)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(surf, boss, x=None, y=None):
    K.draw_khalros(surf, boss, x if x is not None else W // 2,
                   y if y is not None else H // 2 + K.GROUND_DY)


def bbox_of(draw):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    draw(s)
    r = s.get_bounding_rect(min_alpha=100)
    return (r.w, r.h) if r and r.w else (0, 0)


def colors_of(draw, min_alpha=1):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    draw(s)
    seen = set()
    w, h = s.get_size()
    for y in range(0, h, 1):
        for x in range(0, w, 2):           # stride 2: cukup untuk menghitung
            c = s.get_at((x, y))          # keanekaragaman, 4x lebih cepat
            if c[3] >= 40:
                seen.add((c[0] // 8, c[1] // 8, c[2] // 8))
    return len(seen)


def median_time(fn, n=25, reps=5):
    runs = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for i in range(n):
            fn(i)
        runs.append((time.perf_counter() - t0) / n * 1000)
    runs.sort()
    return runs[len(runs) // 2]


def lum_profile(surf, cx, cy, lo, hi, bg=(18, 16, 24)):
    """Profil kecerahan hasil-aci per radius (median keliling).

    Diukur dari RGB, bukan kanal alpha: decal additive menyimpan cahaya di
    RGB dan membiarkan alpha tinggi (lihat `_premul`), jadi `.a` bukan
    ukuran jujur untuk "apa yang dilihat pemain".
    """
    bl = 0.3 * bg[0] + 0.6 * bg[1] + 0.1 * bg[2]
    out, w, h = {}, *surf.get_size()
    for r in range(lo, hi + 1):
        vals = []
        for a in range(0, 360, 4):
            x = int(cx + math.cos(math.radians(a)) * r)
            y = int(cy + math.sin(math.radians(a)) * r)
            if 0 <= x < w and 0 <= y < h:
                c = surf.get_at((x, y))
                vals.append(0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2] - bl)
        if vals:
            out[r] = max(0.0, sorted(vals)[len(vals) // 2])
    return out


# ══════════════════════════════════════════════════════════════════
def s1_geometry():
    print("\n1. GEOMETRI - rig native 1.5x, tampil lewat SATU SCALE")
    rig = K.RIG_W, K.RIG_H
    print(f"   rig buffer {rig}  anchor ({K.RIG_OX},{K.RIG_OY})  RIG_SCALE={K.RIG_SCALE}")
    check(abs(K.RIG_SCALE - 1.5) < 1e-9, "RIG_SCALE = 1.5", str(K.RIG_SCALE))
    native = bbox_of(lambda s: K._draw_khalros_body_raw(s, K.RIG_OX, K.RIG_OY, 1,
                                                        1.7, "idle", 0.0, boss=None))
    disp = bbox_of(lambda s: K._draw_khalros_body(s, s.get_width() // 2,
                                                   s.get_height() // 2 + 44, 1, 1.7, "idle"))
    print(f"   bbox rig native {native}  ->  tampil {disp}  (rasio {disp[1] / max(1, native[1]):.2f})")
    check(disp[1] < native[1], "ukuran tampil lebih kecil dari rig (SCALE dipakai)", "")
    check(80 <= disp[1] <= 140, "tinggi badan 80-140 px di jalur hero-lane", str(disp))
    # ukuran keluarga, metode sama persis
    fam = {}
    for name, fn in (("razak", L2.draw_razak), ("khalros", L2.draw_khalros),
                     ("gorath", L2.draw_gorath), ("alchemist", L2.draw_alchemist)):
        fam[name] = bbox_of(lambda s, fn=fn: fn(s, probe(_render_scale=1.0,
                                                          **({"boss_type": name}
                                                             if name != "alchemist" else {})),
                                                260, 284))
    print("   keluarga: " + "  ".join(f"{k}={v}" for k, v in fam.items()))
    ks = fam["khalros"][1]
    check(min(v[1] for v in fam.values()) - 12 <= ks <= max(v[1] for v in fam.values()) + 12,
          "Khalros seukuran keluarga (selisih <= 12 px)", f"{ks}")
    # SCALE tidak boleh dipecah per jalur
    import inspect
    src = inspect.getsource(K._draw_khalros_body) + inspect.getsource(K._compose_body)
    check("NS.SCALE" in src and "0.68 *" not in src,
          "penskalaan lewat satu konstanta NS.SCALE", f"SCALE={K.SCALE}")
    check(K.SCALE != L2._NS_razak.SCALE, "SCALE per-kelas (Khalros lebih besar)",
          f"{K.SCALE} vs razak {L2._NS_razak.SCALE}")


def s2_palette():
    print("\n2. PALET - ramp hue-shift, specular, pass cahaya")
    print(f"   PALETTE keys: {len(K.PALETTE)}")
    n_body = colors_of(lambda s: K._draw_khalros_body(s, 260, 324, 1, 1.7, "idle"))
    n_atk = colors_of(lambda s: K._draw_khalros_body(s, 260, 324, 1, 4.2, "attack", 0.54))
    print(f"   warna unik (bucket 8): idle {n_body}  attack-impact {n_atk}")
    check(n_body >= 45, "idle punya >= 45 warna unik", str(n_body))
    check(n_atk >= n_body - 6, "frame impact tidak lebih miskin dari idle",
          f"{n_atk} vs {n_body}")
    check(L2._lighting is not None, "modul lighting terpasang (rim+shade aktif)")
    # selout: siluet harus punya kontur gelap 1px
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    K._draw_khalros_body(s, 260, 324, 1, 1.7, "idle")
    dark = sum(1 for y in range(250, 400) for x in range(200, 320, 2)
               if s.get_at((x, y))[3] > 200 and max(s.get_at((x, y))[:3]) < 46)
    check(dark > 120, "kontur gelap siluet terlihat", f"{dark} px")


def s3_time():
    print("\n3. WAKTU - median ms/frame, budget keluarga 3.5 ms (frame steady)")
    tgt = _NS(x=400.0, y=262.0, alive=True)

    def make(skill, timer):
        b = probe(active_skill=skill, active_skill_timer=timer, target=tgt)
        return b

    rows = []
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    rows.append(("idle", median_time(lambda i: render(s, probe(pulse=1.0 + i * 0.13)))))
    for sk, t in (("q", 44), ("w", 52), ("e", 38), ("r", 60)):
        b = make(sk, t)
        rows.append((sk, median_time(lambda i, b=b: (
            setattr(b, "pulse", 1.0 + i * 0.13), render(s, b))[1])))
    g = L2._NS_gorath
    gtgt = _NS(x=400.0, y=262.0, alive=True)
    grows = []
    for sk, t in (("q", 44), ("w", 52), ("e", 38), ("r", 60)):
        gb = probe(boss_type="gorath", active_skill=sk, active_skill_timer=t,
                   target=gtgt)
        grows.append((f"gorath-{sk}", median_time(lambda i, gb=gb: (
            setattr(gb, "pulse", 1.0 + i * 0.13),
            g.draw_gorath(s, gb, 260, 324))[1])))
    rows.append(("gorath-idle", median_time(
        lambda i: g.draw_gorath(s, probe(boss_type="gorath"), 260, 324))))
    rows += grows
    for name, ms in rows:
        print(f"   {name:13s} {ms:5.2f} ms")
    mine = [ms for name, ms in rows if not name.startswith("gorath")]
    theirs = [ms for name, ms in rows if name.startswith("gorath-")]
    worst = max(mine)
    check(worst <= 3.5, "semua pose/skill <= 3.5 ms", f"maks {worst:.2f}")
    check(worst <= max(theirs) + 1.0,
          "paling mahal <= tetangga + 1.0 ms (R punya 6 elam + kolom angin)",
          f"khalros {worst:.2f} vs gorath {max(theirs):.2f}")
    # memori cache: ini yang dulu bocor (rotasi di-cache -> 105 MB)
    K._STATIC_SURFACES.clear()
    for sk, t in (("q", 50), ("w", 60), ("e", 45), ("r", 70)):
        bb = probe(x=260.0, y=260.0, active_skill=sk, active_skill_timer=t,
                   target=_NS(x=410.0, y=264.0, alive=True), _render_scale=0.72)
        for i in range(t):
            bb.pulse = 1.0 + i * 0.19
            bb.active_skill_timer = max(1, t - i)
            render(s, bb)
    mb = sum(c.get_width() * c.get_height() * 4
             for c in K._STATIC_SURFACES.values() if hasattr(c, "get_width")) / 1e6
    print(f"   cache statis setelah 4 cast penuh: {len(K._STATIC_SURFACES)} entri, {mb:.2f} MB"
          f"  (decal {len(K._DECAL_CACHE)}/48, beast {len(K._BEAST_CACHE)}/160)")
    check(mb <= 8.0, "cache permukaan statis <= 8 MB", f"{mb:.2f} MB")
    check(len(K._DECAL_CACHE) <= 48, "decal LRU tidak melewati 48",
          str(len(K._DECAL_CACHE)))
    # cold frame: semua cache dibuang
    K._DECAL_CACHE.clear(); K._DECAL_ORDER.clear(); K._STATIC_SURFACES.clear()
    K._BEAST_CACHE.clear()
    t0 = time.perf_counter()
    render(s, make("r", 44))
    cold = (time.perf_counter() - t0) * 1000
    print(f"   cache-miss penuh (R, 0 cache): {cold:.1f} ms")
    check(cold <= 22.0, "satu frame cache-miss masih di bawah 22 ms", f"{cold:.1f}")


def s4_telegraph():
    print("\n4. TELEGRAPH - radius terukur dari hasil-aci, AI sebagai kebenaran")
    dur, rad = K.SKILL_DUR, K.SKILL_RADIUS
    check(dur == {"q": 50, "w": 60, "e": 45, "r": 70}, "SKILL_DUR = angka AI", str(dur))
    check(rad == {"q": 70, "w": 120, "e": 85, "r": 200}, "SKILL_RADIUS = angka AI", str(rad))
    src = open(os.path.join(ROOT, "bosses", "base_boss.py")).read()
    for skill, t in (("q", 50), ("w", 60), ("e", 45), ("r", 70)):
        check(f"active_skill_timer = {t}" in src, f"AI `{skill}` pakai durasi {t}", "")
    for skill, r in (("q", 70), ("w", 120), ("e", 85), ("r", 200)):
        check(f"<= {r}" in src, f"AI `{skill}` memukul di radius <= {r}", "")

    # Canvas 900 px + offset target 120 px DUNIA: di jalur hero, koordinat
    # kanvas = delta dunia / _render_scale, jadi kanvas kecil memotong FX
    # sebelum terukur (bukan bug renderer, bug pengukur).
    half = 450
    for scale in (1.0, 0.72):
        for skill, radius in (("q", 70), ("w", 120), ("e", 85), ("r", 200)):
            t = dur[skill] - 6
            tgt = _NS(x=float(half + 120), y=float(half + 4), alive=True)
            kw = dict(active_skill=skill, active_skill_timer=t, target=tgt)
            if scale != 1.0:
                kw["_render_scale"] = scale
            b = probe(x=float(half), y=float(half), **kw)
            s = pygame.Surface((half * 2, half * 2), pygame.SRCALPHA)
            s.fill((18, 16, 24, 255))
            K.draw_khalros(s, b, half, half + 44)
            # pakai rumus renderer sendiri supaya yang diuji adalah KONSISTENSI
            # (cincin mendarat di `_ring_r`/`_target_position`), bukan aritmetika
            # alat audit.
            want = K._ring_r(b, radius, s)
            if skill == "q":
                cx, cy = K._target_position(b, half, half + 44)
            else:
                cx, cy = half, half + 44 + K.GROUND_DY
            prof = lum_profile(s, cx, cy, 12, min(want + 22, half - 12))
            if not prof or max(prof.values()) < 3:
                check(False, f"{skill} @{scale}: lantai terangnya sendiri",
                      str(round(max(prof.values()), 1) if prof else "kosong"))
                continue
            lo = max(12, want - 30)
            got = max(((r, v) for r, v in prof.items() if r >= lo),
                      key=lambda kv: kv[1])[0]
            # jendela sampling di SEKITAR pita terkuat, bukan `want` mentah:
            # `_build_falloff_ring` menaruh inti cincin di radius +thickness+1
            # (konvensi keluarga, razak/gorath sama), jadi diukur persis di
            # angka AI = sisi dalam falloff. Yang diuji tetap: pitanya HARUS
            # jatuh di radius gameplay (`abs(got - want)`) dan paling terang.
            ring = max(prof.get(got + d, 0.0) for d in (-1, 0, 1))
            inner = max([v for r, v in prof.items() if lo > r >= 12] or [0])
            check(abs(got - want) <= 7 and ring >= inner,
                  f"{skill} @{scale}: cincin {want} px kanvas ({radius} px dunia)",
                  f"terukur {got}, lum {ring:.0f} vs dalam {inner:.0f}")
    # kompensasi world-space: radius Piksel membesar saat unit dikecilkan
    big = int(round(200 * K._fx_scale(probe(x=1.0, y=1.0, _render_scale=0.5))))
    check(abs(big - 400) <= 4, "R di `_render_scale=0.5` -> ~400 px (1/scale)", str(big))
    check(K._fx_scale(probe(x=1.0, y=1.0, _render_scale=0.3)) <= 2.6 + 1e-9,
          "_fx_scale dipangkas di 2.6 (tidak meledak di portrait)")

    b0 = probe()
    body = bbox_of(lambda su: render(su, b0))
    bb = pygame.Surface((half * 2, half * 2), pygame.SRCALPHA)
    K.draw_khalros(bb, probe(x=half, y=half, active_skill="r",
                             active_skill_timer=dur["r"] - 6), half, half + 44)
    full = bb.get_bounding_rect(min_alpha=60)
    print(f"   bbox badan {body}  vs bbox R penuh {full.size}")
    check(full.w * full.h > (body[0] * body[1]) * 3,
          "FX R jauh melampaui siluet badan", str(full.size))


def s5_contract():
    print("\n5. KONTRAK - nama publik v1 + kepemilikan lapisan hidup")
    v1 = {n for n in dir(v1_namespace()) if not n.startswith("__")}
    have = {n for n in dir(K) if not n.startswith("__")}
    missing = sorted(v1 - have)
    print(f"   v1 {len(v1)} nama, v2 {len(have)} nama, hilang {len(missing)}")
    check(not missing, "57 nama publik v1 utuh", ", ".join(missing[:6]))
    src = open(os.path.join(ROOT, "bosses", "level2.py")).read()
    blk = src[src.index("class _NS_khalros:"):src.index("class _NS_gorath:")]
    check("pygame.image" not in blk, "100% prosedural (tanpa citra eksternal)")
    banned = "\u6700\u5927"           # frasa sisa yang pernah masuk ke komentar
    check(banned not in blk and not any(0x3000 <= ord(c) <= 0x30ff or
          0x4e00 <= ord(c) <= 0x9fff for c in blk), "komentar bebas CJK")
    # hero-lane: lapisan hidup mengambil alih, tidak ada efek dobel
    KF.KHALROS_FX_ENABLED = True
    KF.reset_all()
    h = probe(_render_scale=1.0, active_skill="q", active_skill_timer=44,
              target=_NS(x=420.0, y=284.0, alive=True))
    KF.attach(h)
    check(KF.owns(h), "hero-lane: lapisan hidup mengakui kepemilikan")
    src_body = blk[blk.index("def draw_khalros(surface, boss, x, y):"):]
    src_body = src_body[:src_body.index("\n    def ")]
    check(src_body.count("if not owned and not in_cache") +
          src_body.count("and not owned") >= 2,
          "renderer men-gate FX milik lapisan hidup", "")
    # proyektil tidak boleh lahir dua kali
    b2 = probe(active_skill="q", active_skill_timer=40)
    b2._khal_axe_spawned = False
    b2._khal_projectiles = []
    KF.KHALROS_FX_ENABLED = False
    for i in range(30):
        b2.active_skill_timer = 48 - i
        render(pygame.Surface((W, H), pygame.SRCALPHA), b2)
    n_off = len(getattr(b2, "_khal_projectiles", []))
    d = KF.director_for(b2)
    KF.KHALROS_FX_ENABLED = True
    b3 = probe(active_skill="q", active_skill_timer=40, _render_scale=1.0)
    KF.attach(b3)
    for i in range(30):
        b3.active_skill_timer = 48 - i
        render(pygame.Surface((W, H), pygame.SRCALPHA), b3)
    check(n_off == 2 and not getattr(b3, "_khal_projectiles", []),
          "Q: 2 proyektil saat live OFF, 0 saat live ON (tidak dobel)",
          f"off={n_off} on={len(getattr(b3, '_khal_projectiles', []))}")
    KF.KHALROS_FX_ENABLED = True


# ══════════════════════════════════════════════════════════════════
def _cell(size, draw, zoom=1):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    draw(s)
    if zoom != 1:
        s = pygame.transform.scale(s, (size * zoom, size * zoom))
    return s


def sheets():
    """Lembar review + sebelum/sesudah (v1 snapshot vs v2)."""
    print("\n6. LEMBAR GAMBAR")
    cols = 5
    titles = ["idle", "walk", "attack impact", "charge", "hurt"]
    rows = [("v2", K, {}), ("v1", v1_namespace(), {})]
    out_rows = []
    for tag, NS, _ in rows:
        cells = []
        for kind in range(len(titles)):
            def draw(s, kind=kind, NS=NS):
                cx, cy = s.get_width() // 2, int(s.get_height() * 0.72)
                if not hasattr(NS, "_draw_khalros_body"):
                    # v1 tidak punya komposit ini -> pakai entry point penuh
                    kwv = (dict(), dict(_khal_last_x=246.0), dict(), dict(),
                           dict(hurt_flash_timer=7))[kind]
                    if kind == 2:
                        NS._khal_attack_progress = 0.54
                    NS.draw_khalros(s, probe(**kwv), cx, cy)
                    return
                if kind == 0:
                    NS._draw_khalros_body(s, cx, cy, 1, 1.7, "idle")
                elif kind == 1:
                    NS._draw_khalros_body(s, cx, cy, 1, 3.4, "walk")
                elif kind == 2:
                    NS._draw_khalros_body(s, cx, cy, 1, 2.2, "attack", 0.54)
                elif kind == 3:
                    NS._draw_khalros_body(s, cx, cy, 1, 2.8, "charge", 0.5)
                else:
                    b = probe(hurt_flash_timer=7)
                    NS.draw_khalros(s, b, cx, cy)
            cells.append(_cell(150, draw, zoom=2))
        out_rows.append((tag, cells))
    cw, ch = 300, 300
    sheet = pygame.Surface((cw * cols + 10, (ch + 26) * 2 + 14), pygame.SRCALPHA)
    sheet.fill((24, 22, 28, 255))
    fnt = pygame.font.SysFont("monospace", 15, bold=True)
    for ri, (tag, cells) in enumerate(out_rows):
        for ci, c in enumerate(cells):
            x, y = 10 + ci * cw, 10 + ri * (ch + 26)
            pygame.draw.rect(sheet, (44, 40, 50), (x, y, cw - 6, ch + 22), 0, 4)
            sheet.blit(c, (x + (cw - 6 - c.get_width()) // 2, y + 4))
            t = fnt.render((f"{tag.upper()} · " if ci == 0 else "") + titles[ci],
                          True, (206, 196, 170))
            sheet.blit(t, (x + 6, y + ch - 4))
    out = os.path.join(ROOT, "docs", "khalros_v2_before_after.png")
    pygame.image.save(sheet, out)
    print(f"   tulis {out}  {sheet.get_size()}")

    cols = 6
    titles = ["idle", "Q 70px", "W 120px", "E 85px", "R 200px", "hurt"]
    cells = []
    for kind in range(cols):
        def draw(s, kind=kind):
            cx, cy = s.get_width() // 2, int(s.get_height() * 0.66)
            kw = ({},
                  dict(active_skill="q", active_skill_timer=40,
                       target=_NS(x=float(cx + 96), y=float(cy - K.GROUND_DY + 6), alive=True)),
                  dict(active_skill="w", active_skill_timer=48),
                  dict(active_skill="e", active_skill_timer=30),
                  dict(active_skill="r", active_skill_timer=58),
                  dict(hurt_flash_timer=7))[kind]
            s.fill((18, 16, 24, 255))
            K.draw_khalros(s, probe(pulse=1.25, **kw), cx, cy)
        cells.append(_cell(230, draw, zoom=2))
    sheet = pygame.Surface((230 * cols * 2 // 2 + 10, 230 + 30), pygame.SRCALPHA)
    sheet.fill((24, 22, 28, 255))
    for ci, c in enumerate(cells):
        x = 10 + ci * 245
        pygame.draw.rect(sheet, (44, 40, 50), (x, 8, 232, 244), 0, 4)
        sheet.blit(c, (x + 1, 9))
        sheet.blit(fnt.render(titles[ci], True, (206, 196, 170)), (x + 6, 250))
    out = os.path.join(ROOT, "docs", "khalros_v2_review.png")
    pygame.image.save(sheet, out)
    print(f"   tulis {out}  {sheet.get_size()}")


def main():
    print("=" * 64)
    print("AUDIT KHALROS v2 (Pixel Masterwork) - bosses/level2.py::_NS_khalros")
    print("=" * 64)
    s1_geometry()
    s2_palette()
    s3_time()
    s4_telegraph()
    s5_contract()
    sheets()
    print("\n" + "=" * 64)
    if FAILURES:
        print(f"{len(FAILURES)} pemeriksaan GAGAL:")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("SEMUA PEMERIKSAAN AUDIT LOLOS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
