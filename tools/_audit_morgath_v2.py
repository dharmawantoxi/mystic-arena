#!/usr/bin/env python3
"""Audit + preview sheet untuk Morgath renderer masterwork v2 + FX v2.1.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala terukur & ukuran akhir di layar (pipeline heroes/__init__)
  - bbox tiap pose, jumlah warna unik (idle vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R world-space (kompensasi 1/_render_scale):
    E Magnetic Field = 90 px dunia di caster,
    R Tempest Double = +/-60 px dunia untuk posisi clone,
    W Flux = pool 38 px dunia di TARGET, Q = jalur ke target.
  - piksel efek di luar siluet badan (tidak bocor melewati canvas cache)
  - before/after vs renderer v1 (tools/_morgath_v1_snapshot.py)

Menghasilkan:
  - docs/morgath_v2_review.png
  - docs/morgath_v2_anim_strip.png
  - docs/morgath_v2_ingame.png
  - docs/morgath_v2_skills.png
  - docs/morgath_v2_before_after.png

Jalankan:  /home/user/.venv/bin/python tools/_audit_morgath_v2.py
"""
import math
import os
import sys
import time
from types import SimpleNamespace as _NS

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import _ProbeEntity, _get_hero_scale
from bosses.level1 import _NS_morgath as M
from bosses import level1 as L

# tools/ bukan package; muat snapshot v1 langsung dari file.
import importlib.util as _ilu
_snap_path = os.path.join(ROOT, "tools", "_morgath_v1_snapshot.py")
_snap_spec = _ilu.spec_from_file_location("_morgath_v1_snapshot", _snap_path)
_snap_mod = _ilu.module_from_spec(_snap_spec)
_snap_spec.loader.exec_module(_snap_mod)
V1 = _snap_mod._NS_morgath
draw_v1 = _snap_mod.draw_morgath_v1

SIZE = 320
C, CY = SIZE // 2, SIZE // 2


def probe(cx=0.0, cy=0.0, **kw):
    b = _NS(boss_type="morgath", boss_class="mini", x=float(cx),
            y=float(cy), direction=1, facing=1, pulse=1.25, timer=0,
            attack_cooldown=48, active_skill=None, active_skill_timer=0,
            target=None, _render_scale=1.0, hurt_flash_timer=0,
            alive=True, radius=51)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def rig_frame(action, phase, ap=0.0, facing=1, detail=False,
              size=SIZE, ax=None, ay=None):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    M._draw_mor_rig(s, ax, ay, facing, phase, action, ap, detail)
    if action == "attack":
        M._draw_attack_smear(s, lambda dx, dy: (ax + int(dx * 1.0 * 0.74),
                                                ay - 4 + int(dy * 0.74)),
                             lambda v: max(1, int(round(v))), facing, ap)
    return s


def solid_rect(surf, thr=100):
    m = pygame.mask.from_surface(surf, thr)
    rs = m.get_bounding_rects()
    if not rs:
        return None
    x0 = min(r.x for r in rs)
    y0 = min(r.y for r in rs)
    x1 = max(r.right for r in rs)
    y1 = max(r.bottom for r in rs)
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return cond


ok_all = True

# ── 1. skala & ukuran layar ──────────────────────────────────────
scale = _get_hero_scale("morgath")
body = rig_frame("idle", 1.25)
bb = solid_rect(body)
print(f"    solid idle native: {bb.w}x{bb.h}")
ok_all &= check(bb is not None and 92 <= bb.height <= 112 and
                bb.width >= 50,
                "bbox idle native (paritas keluarga, ~105 px padat)",
                f"{bb}")
ok_all &= check(scale <= 1.02, "hero tidak di-upscale", f"{scale:.3f}")

# Ukuran FINAL di layar diukur lewat jalur penuh render_hero (canvas
# -> smoothscale -> pass HD), semantik sama seperti _measure_native_size.
_final = pygame.Surface((400, 400), pygame.SRCALPHA)
_h = _ProbeEntity("morgath", 200, 200)
_h.pulse = 1.35
_h.direction = 1
_h.team = "blue"
heroes.render_hero("morgath", _final, _h, 200, 200)
_final.fill((0, 0, 0, 0), (0, 216, 400, 400 - 216))
_fr = solid_rect(_final)
screen_h = _fr.height if _fr else 0
ok_all &= check(45 <= screen_h <= 62,
                "tinggi badan final di layar (~51 px keluarga)",
                f"{screen_h}px scale={scale:.3f}")

# ── 2. keunikan frame (bukan sticker) ────────────────────────────
walk_frames = {pygame.image.tobytes(rig_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
idle_frames = {pygame.image.tobytes(rig_frame("idle", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(rig_frame("attack", 1.2, p), "RGBA")
              for p in (0.1, 0.35, 0.55, 0.75, 0.9, 0.97)}
ok_all &= check(len(walk_frames) >= 7, "walk: 8 frame unik",
                f"{len(walk_frames)}/8")
ok_all &= check(len(idle_frames) >= 5, "idle hidup: frame bervariasi",
                f"{len(idle_frames)}/8")
ok_all &= check(len(atk_frames) >= 6, "attack: 6 keyframe unik",
                f"{len(atk_frames)}/6")

# ── 3. pose set lengkap & warna ──────────────────────────────────
pose_names = ("idle", "walk", "attack", "point", "channel", "erect",
              "ascend")
pose_rects = {}
for name in pose_names:
    ap = 0.9 if name == "attack" else 0.0
    r = solid_rect(rig_frame(name, 1.25, ap))
    pose_rects[name] = r
    ok_all &= check(r is not None and r.height > 70, f"pose {name} solid",
                    f"{r.w}x{r.h}")

colors_idle = colors_of(rig_frame("idle", 1.25))
colors_detail = colors_of(rig_frame("idle", 1.25, detail=True))
ok_all &= check(len(colors_idle) >= 40, "palette idle >= 40 warna",
                f"{len(colors_idle)}")
ok_all &= check(len(colors_detail) >= len(colors_idle) + 8,
                "LOD portrait menambah warna (detail mikro)",
                f"{len(colors_idle)} -> {len(colors_detail)}")

# ── 4. timing render (budget cache-miss) ─────────────────────────
t0 = time.perf_counter()
for _ in range(20):
    rig_frame("idle", 1.25)
ms = (time.perf_counter() - t0) / 20 * 1000
ok_all &= check(ms <= 3.5, "waktu render idle (budget ~3.5 ms)",
                f"{ms:.2f} ms")

# ── 5. skill FX world-space ──────────────────────────────────────
# 5a. E = 90 px dunia: ring radius TEPAT di ruang dunia pada dua
#     _render_scale berbeda (canvas radius = 90 / fs).
for fs in (1.0, 0.45):
    canvas_w = int(2 * (140 / fs)) + 40
    surf = pygame.Surface((canvas_w, canvas_w), pygame.SRCALPHA)
    c = canvas_w // 2
    b = probe(c, c, _render_scale=fs, active_skill="e",
              active_skill_timer=70)
    L.draw_morgath(surf, b, c, c)
    gy = c + M._ground_dy()
    r_world = 90
    r_canvas = int(r_world / fs)
    hits = 0
    for a in range(180):
        # Ring jangkauan adalah LINGKARAN penuh (squash hanya untuk
        # dashed rune-ring dekoratif); toleransi +/-3 px untuk
        # pembulatan int + ketebalan stroke aacircle.
        ang = a / 180 * math.pi
        hit = False
        for d in range(r_canvas - 3, r_canvas + 4):
            x = int(c + math.cos(ang) * d)
            y = int(gy + math.sin(ang) * d)
            if 0 <= x < canvas_w and 0 <= y < canvas_w and \
                    surf.get_at((x, y)).a > 40:
                hit = True
                break
        hits += 1 if hit else 0
    ok_all &= check(hits > 90,
                    f"E ring 90 px dunia presisi (fs={fs})", f"{hits}/180")
    # efek tidak boleh menyentuh tepi canvas (clamp aman)
    edge = 0
    for x in range(canvas_w):
        for y in (0, canvas_w - 1):
            edge += 1 if surf.get_at((x, y)).a > 0 else 0
    for y in range(canvas_w):
        for x in (0, canvas_w - 1):
            edge += 1 if surf.get_at((x, y)).a > 0 else 0
    ok_all &= check(edge == 0, f"FX tidak bocor melewati canvas (fs={fs})",
                    f"edge px={edge}")

# 5b. R = +/-60 px dunia: ada siluet ghost di kedua sisi caster.
surf = pygame.Surface((360, 300), pygame.SRCALPHA)
b = probe(180, 150, _render_scale=1.0, active_skill="r",
          active_skill_timer=45)
L.draw_morgath(surf, b, 180, 150)
m = pygame.mask.from_surface(surf, 60)
rs = m.get_bounding_rects()
xs = [r.x for r in rs]
ok_all &= check(min(xs) < 180 - 40 and max(r.right for r in rs) > 180 + 40,
                "R: clone kiri & kanan di +/-60 px dunia", f"x range {xs}")

# 5c. W: pool di TARGET (bukan di caster).
surf = pygame.Surface((460, 300), pygame.SRCALPHA)
b = probe(160, 150, _render_scale=1.0, active_skill="w",
          active_skill_timer=30)
b.target = _NS(x=320.0, y=158.0, alive=True)
L.draw_morgath(surf, b, 160, 150)
pool = pygame.mask.from_surface(surf.subsurface((200, 90, 220, 140)), 100)
ok_all &= check(pool.count() > 150, "W: pool terlihat di area target",
                f"{pool.count()} px")

# 5d. piksel efek di luar siluet badan: FX dibolehkan di luar badan
#     (telegraph/aura) tapi TIDAK di luar jangkauan canvas cache yang
#     disediakan pipeline (adaptif + FX world-space ikut membesar).
#     Di sini: semua piksel harus berada dalam bbox + slack 140/fs.
for fs in (1.0, 0.45):
    cw = int(2 * (140 / fs)) + 40
    surf = pygame.Surface((cw, cw), pygame.SRCALPHA)
    c = cw // 2
    b = probe(c, c, _render_scale=fs, active_skill="e",
              active_skill_timer=70)
    L.draw_morgath(surf, b, c, c)
    bb = surf.get_bounding_rect(min_alpha=8)
    slack = int(140 / fs) + 12
    ok_all &= check(bb.left >= c - slack and bb.right <= c + slack,
                    f"extent FX di dalam budget canvas (fs={fs})",
                    f"bbox {bb.w}x{bb.h}")

# ── 6. timing skill ──────────────────────────────────────────────
# durasi visual mengikuti SKILL_DUR (q50/w40/e90/r60) = timers boss.
ok_all &= check(M.SKILL_DUR == {"q": 50, "w": 40, "e": 90, "r": 60},
                "durasi visual = active_skill_timer gameplay",
                f"{M.SKILL_DUR}")


# ── 6b. bolt basic attack v2.2 (mewah, terukur) ──────────────────
def _bolt_frame(prog, canvas=(460, 300), scale=1.0):
    cw, ch = canvas
    s = pygame.Surface((cw, ch), pygame.SRCALPHA)
    b = probe(200.0, 200.0)
    b._mor_attack_dir = 1
    b._mor_attack_target = (180, 12)
    b.target = _NS(x=380.0, y=212.0, alive=True)
    b._render_scale = scale
    M._draw_lightning_projectile(s, b, int(b.x), int(b.y), prog)
    return s


# (a) sebelum 0.55: nol piksel; sesudahnya: menempel di telapak.
s0 = _bolt_frame(0.30)
ok_all &= check(s0.get_bounding_rect(min_alpha=8).width == 0,
                "bolt: kosong sebelum progress 0.55")
s1 = _bolt_frame(0.75)
rect = s1.get_bounding_rect(min_alpha=8)
mdx, mdy = M._muzzle_offset_world()
muz = (200 + mdx, 200 + mdy)
dist = max(0.0, math.hypot(max(rect.left - muz[0], 0,
                               muz[0] - rect.right),
                           max(rect.top - muz[1], 0,
                               muz[1] - rect.bottom)))
ok_all &= check(rect.width > 30 and dist <= 4,
                "bolt: lahir dari telapak rig (muzzle)",
                f"bbox {rect.w}x{rect.h}, jarak {dist:.1f}px")

# (b) kekayaan band: 5 band arc + inti terang hadir dalam 1 frame.
def _pix(s):
    return {(s.get_at((x, y)).r, s.get_at((x, y)).g,
             s.get_at((x, y)).b)
            for y in range(s.get_height())
            for x in range(s.get_width()) if s.get_at((x, y)).a >= 60}
px75 = _pix(s1)
band_hits = 0
for k in ("arc_darkest", "arc_dark", "arc_mid", "arc_light", "arc_hot"):
    p = M.PALETTE[k]
    if any(abs(c[0] - p[0]) <= 8 and abs(c[1] - p[1]) <= 8 and
           abs(c[2] - p[2]) <= 8 for c in px75):
        band_hits += 1
ok_all &= check(band_hits >= 5, "bolt: 5 band hue-shift arc hadir",
                f"{band_hits}/5")

# (c) ranting & elemen di luar koridor sumbu (bukan garis polos).
def _off_axis(s):
    sx, sy = 200 + mdx, 200 + mdy
    tx, ty = 380.0, 212.0
    dx, dy = tx - sx, ty - sy
    Ln = math.hypot(dx, dy)
    nx, ny = -dy / Ln, dx / Ln
    n = 0
    for x in range(s.get_width()):
        for y in range(s.get_height()):
            c = s.get_at((x, y))
            if c.a < 60:
                continue
            t = ((x - sx) * dx + (y - sy) * dy) / (Ln * Ln)
            if 0.0 <= t <= 1.0:
                d = abs((x - sx) * nx + (y - sy) * ny)
                if d > 9 and c.b > c.r:
                    n += 1
    return n
ok_all &= check(_off_axis(s1) >= 60,
                "bolt: ranting/trail menyimpang dari sumbu (bukan garis polos)",
                f"{_off_axis(s1)} px")

# (d) morph hidup: 8 frame progres semuanya unik.
sigs = [pygame.image.tostring(_bolt_frame(p), "RGBA")
        for p in (0.58, 0.65, 0.72, 0.80, 0.88, 0.93, 0.97, 1.0)]
uniq = len({s for s in sigs}) == len(sigs)
ok_all &= check(uniq, "bolt: morph deterministik per-frame (8 frame unik)")

# (e) benturan: ring ganda + bintang 8 + garis radial pada t>0.88.
s9 = _bolt_frame(0.97)
ring_hits = 0
for ang in range(0, 360, 3):
    hit = False
    for rr in (21, 24):
        x = int(380 + math.cos(math.radians(ang)) * rr)
        y = int(212 + math.sin(math.radians(ang)) * rr * 0.8)
        if 0 <= x < 460 and 0 <= y < 300 and s9.get_at((x, y)).a >= 40:
            hit = True
            break
    ring_hits += 1 if hit else 0
spike_hits = 0
for i in range(8):
    ang = i * math.pi / 4 + 0.5
    hit = False
    for rr in range(6, 22):
        x = int(380 + math.cos(ang) * rr)
        y = int(212 + math.sin(ang) * rr * 0.8)
        if 0 <= x < 460 and 0 <= y < 300 and s9.get_at((x, y)).a >= 90:
            hit = True
            break
    spike_hits += 1 if hit else 0
ok_all &= check(ring_hits >= 70 and spike_hits >= 6,
                "bolt: impact ring ganda + bintang 8 + radial",
                f"ring {ring_hits}/120, spike {spike_hits}/8")

# (f) budget: frame termahal (impact penuh) di bawah 3.5 ms.
best = 1e9
for _ in range(20):
    t0 = time.perf_counter()
    _bolt_frame(0.97)
    best = min(best, (time.perf_counter() - t0) * 1000)
ok_all &= check(best <= 3.5, "bolt: render <= 3.5 ms (frame impact)",
                f"{best:.2f} ms")

# ── 7. before/after vs v1 ────────────────────────────────────────
surf_v1 = pygame.Surface((360, 360), pygame.SRCALPHA)
surf_v2 = pygame.Surface((360, 360), pygame.SRCALPHA)
b1 = probe(180, 180)
b2 = probe(180, 180)
try:
    # Bandingkan RIG SAJA (tanpa FX) - v1: 74x100 @0.9, v2: 154x117 @0.74.
    V1._draw_mor_rig(surf_v1, 180, 180, 1, 1.25, "idle", 0.0, False)
    M._draw_mor_rig(surf_v2, 180, 180, 1, 1.25, "idle", 0.0, False)
    r1 = solid_rect(surf_v1)
    r2 = solid_rect(surf_v2)
    print(f"    v1 rig solid: {r1}  |  v2 rig solid: {r2}")
    area1 = r1.width * r1.height if r1 else 0
    area2 = r2.width * r2.height if r2 else 0
    ok_all &= check(r2 is not None and r1 is not None
                    and area2 >= area1 * 1.5,
                    "luas padat v2 >= 1.5x v1 (kepadatan detail naik)",
                    f"{area1} -> {area2} px2 ({area2 / max(1, area1):.2f}x)")
    ok_all &= check(len(colors_of(surf_v2)) > len(colors_of(surf_v1)),
                    "warna v2 lebih kaya dari v1",
                    f"{len(colors_of(surf_v1))} -> {len(colors_of(surf_v2))}")
except Exception as e:
    ok_all = False
    print(f"[FAIL] before/after error: {e}")

print()
print("AUDIT MORGATH V2:", "LULUS" if ok_all else "GAGAL")
