#!/usr/bin/env python3
"""Audit + preview sheet untuk Zharok renderer masterwork v2 + Skill FX.

Mengukur hal yang sebelumnya hanya bisa dinilai mata:
  - skala rig native (1.5x) & ukuran akhir di layar (pipeline bosses/ & heroes/)
  - bbox tiap pose, jumlah warna unik (arena vs portrait LOD)
  - keunikan frame antar siklus (bukan sticker translation)
  - waktu render per pose & per skill (budget cache-miss ~3.5 ms)
  - skill Q/W/E/R: world-space (kompensasi 1/_render_scale), mewah, terukur
      Q Strafe        = 250 px dunia (aim laser & reticle di target)
      W Skeleton Walk = 200 px dunia (burst shockwave & smoke cloak)
      E Death Pact    = 150 px dunia (pentagram & floating flaming skull)
      R Burning Army  = 220 px dunia (molten fissure cracks & 5 burning skulls)
  - piksel FX di LUAR siluet badan (skill benar-benar terlihat)

Menghasilkan:
  - docs/zharok_v2_review.png
  - docs/zharok_v2_anim_strip.png
  - docs/zharok_v2_in_game.png
  - docs/zharok_v2_skill_fx.png
  - docs/zharok_v2_before_after.png

Jalankan:  python3 tools/_audit_zharok_v2.py
"""
import importlib.util
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
from heroes import _ProbeEntity, render_hero
import bosses.level4 as L
from bosses.level4 import _NS_zharok as Z


# ────────────────────────────────────────────────────────────────────
# util
# ────────────────────────────────────────────────────────────────────
def colors_of(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def boss_probe(size=520, ax=None, ay=None, **kw):
    """Entity probe untuk draw_zharok (jangkar = ax, ay)."""
    ax = size // 2 if ax is None else ax
    ay = size // 2 if ay is None else ay
    b = _NS(boss_type="zharok", boss_class="mini", x=float(ax), y=float(ay),
            direction=1, facing=1, pulse=1.3, timer=0, attack_cooldown=40,
            active_skill=None, active_skill_timer=0, target=None,
            hurt_flash_timer=0, alive=True, radius=34, hp=7000, max_hp=7000,
            range=180)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def rig_frame(action="idle", phase=1.25, progress=0.0, facing=1,
              detail=False, stealth=False, size=340):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    Z._draw_zharok_body_raw(s, size // 2, size // 2, facing, phase, action,
                            progress, stealth=stealth, detail=detail)
    return s


def check(cond, msg, detail=""):
    tag = "PASS" if cond else "FAIL"
    pad = "." * max(2, 60 - len(msg))
    det = f"  ({detail})" if detail else ""
    print(f"  [{tag}] {msg} {pad}{det}")
    return bool(cond)


print("══════════════════════════════════════════════════════════════")
print(" AUDIT ZHAROK MASTERWORK v2 + SKILL FX v2.1")
print("══════════════════════════════════════════════════════════════")
ok_all = True

# ── 1. rig native 1.5x & ukuran layar ─────────────────────────────
raw_idle = rig_frame("idle")
bb = raw_idle.get_bounding_rect(min_alpha=8)
print(f"[i] bounding box rig native (idle): {bb.w}x{bb.h} px")
ok_all &= check(bb.h >= 110 and bb.w >= 50,
                "rig native di-author ~1.5x resolusi", f"{bb.w}x{bb.h} px")

# ukuran arena (setelah SCALE) sekelas keluarga mini boss level-4
arena_s = pygame.Surface((520, 520), pygame.SRCALPHA)
Z.draw_zharok(arena_s, boss_probe(), 260, 260)
ab = arena_s.get_bounding_rect(min_alpha=100)
print(f"[i] bounding box arena: {ab.w}x{ab.h} px")
ok_all &= check(ab.w <= 150 and ab.h <= 150,
                "ukuran arena sekelas mini boss (<150x150)", f"{ab.w}x{ab.h} px")
ok_all &= check(ab.w >= 50 and ab.h >= 50,
                "presence arena jelas (>=50x50)", f"{ab.w}x{ab.h} px")

# ── 2. pixel-art discipline ───────────────────────────────────────
nc = len(colors_of(raw_idle))
print(f"[i] warna unik rig native (idle): {nc}")
ok_all &= check(nc >= 40, "kepadatan warna native (ramp 4-8 band)", f"{nc} warna")

# cek swatch ramp PALETTE sampai ke render
got_c = colors_of(raw_idle)
ramp_keys = ("bone_darkest", "bone_mid", "bone_high", "fire_dark",
             "fire_bright", "fire_hot", "hood_darkest", "hood_mid",
             "leather_dark", "wood_mid", "gold_mid")
missing_sw = [k for k in ramp_keys if Z.PALETTE[k] not in got_c]
ok_all &= check(not missing_sw, "swatch material sampai ke render",
                f"hilang={missing_sw}" if missing_sw else "lengkap")

# selout: versi komposit punya outline hitam nyata
raw_comp = pygame.Surface((260, 260), pygame.SRCALPHA)
Z._draw_zharok_body_raw(raw_comp, 130, 140, 1, 1.0, "idle")
full_comp = pygame.Surface((260, 260), pygame.SRCALPHA)
Z._draw_zharok_body(full_comp, 130, 140, 1, 1.0, "idle")


def black_px(surf):
    return sum(1 for y in range(0, surf.get_height(), 2)
               for x in range(0, surf.get_width(), 2)
               if surf.get_at((x, y))[:3] == (0, 0, 0)
               and surf.get_at((x, y))[3] > 50)


b_raw, b_comp = black_px(raw_comp), black_px(full_comp)
ok_all &= check(b_comp > b_raw + 15, "selout outline siluet aktif",
                f"{b_raw} -> {b_comp} px")

# portrait LOD detail
det_idle = rig_frame("idle", detail=True)
pc = len(colors_of(det_idle))
ok_all &= check(pc > nc, "portrait LOD menambah micro-detail",
                f"raw={nc} detail={pc}")

# ── 3. living animations (bukan sticker) ───────────────────────────
idle_frames = {pygame.image.tobytes(rig_frame("idle", i * 0.52), "RGBA")
               for i in range(8)}
walk_frames = {pygame.image.tobytes(rig_frame("walk", i * 0.785), "RGBA")
               for i in range(8)}
atk_frames = {pygame.image.tobytes(rig_frame("attack", 1.0, i / 9.0), "RGBA")
              for i in range(10)}
ok_all &= check(len(idle_frames) == 8, "living idle (8 frame unik)",
                f"{len(idle_frames)}/8")
ok_all &= check(len(walk_frames) == 8, "walk foot solver (8 frame unik)",
                f"{len(walk_frames)}/8")
ok_all &= check(len(atk_frames) >= 9, "attack 7-keyframe pose",
                f"{len(atk_frames)}/10")

# attack timeline & frame IMPACT
pose_imp = Z._attack_pose(0.52)
ok_all &= check(pose_imp["impact"] > 0.9, "frame IMPACT pada ap=0.52",
                f"impact={pose_imp['impact']:.2f}")

# ── 4. benchmark render budget ───────────────────────────────────
def bench_med(fn, reps=7, n=20):
    fn()
    runs = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        runs.append((time.perf_counter() - t0) / n * 1000)
    runs.sort()
    return runs[len(runs) // 2]


scratch = pygame.Surface((520, 520), pygame.SRCALPHA)
pb = boss_probe(ax=260, ay=260)
t_idle = bench_med(lambda: Z.draw_zharok(scratch, pb, 260, 260))
pw = boss_probe(ax=260, ay=260)
pw._zh_last_x, pw._zh_last_y = 258.0, 260.0
t_walk = bench_med(lambda: Z.draw_zharok(scratch, pw, 260, 260))
pa = boss_probe(ax=260, ay=260, _zh_attack_active=True,
                _zh_attack_progress=0.52)
t_atk = bench_med(lambda: Z.draw_zharok(scratch, pa, 260, 260))
print(f"[i] render ms: idle={t_idle:.2f} walk={t_walk:.2f} attack={t_atk:.2f}")
ok_all &= check(max(t_idle, t_walk, t_atk) <= 3.5,
                "budget cache-miss pose dasar", f"{max(t_idle, t_walk, t_atk):.2f} ms")


# ── 5. skill FX: world-space, mewah, terukur ─────────────────────
def render_skill(skill, timer, fs=None, W=800, tdx=170, tdy=-30):
    s = pygame.Surface((W, W), pygame.SRCALPHA)
    cx, cy = W // 2, W // 2
    h = boss_probe(ax=cx, ay=cy, active_skill=skill, active_skill_timer=timer,
                   target=_NS(x=float(cx + tdx), y=float(cy + tdy),
                              alive=True))
    if fs is not None:
        h._render_scale = fs
    Z.draw_zharok(s, h, cx, cy)
    return s, cx, cy


def count_fx(s, cx, cy, rmin=0, rmax=10 ** 6):
    """Piksel api menyala (FX) di annulus [rmin, rmax] dari jangkar."""
    n = 0
    for y in range(0, s.get_height(), 2):
        for x in range(0, s.get_width(), 2):
            d = math.hypot(x - cx, y - cy)
            if rmin <= d <= rmax:
                c = s.get_at((x, y))
                if c.a > 40 and c[0] > 100 and c[0] > c[2] + 20:
                    n += 1
    return n


def hits_ring(s, r_px, cx, cy, tol=3):
    hits = total = 0
    for a in range(0, 360, 2):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        ok = False
        for dr in range(-tol, tol + 1):
            x = int(cx + ca * (r_px + dr))
            y = int(cy + sa * (r_px + dr))
            if 0 <= x < s.get_width() and 0 <= y < s.get_height() \
                    and s.get_at((x, y)).a > 30:
                ok = True
                break
        total += 1
        hits += 1 if ok else 0
    return hits, total


plain = pygame.Surface((900, 900), pygame.SRCALPHA)
Z.draw_zharok(plain, boss_probe(ax=450, ay=450), 450, 450)
body_bb = plain.get_bounding_rect(min_alpha=100)
BODY_R = max(body_bb.width, body_bb.height) / 2.0
print(f"[i] radius siluet badan (arena) ~= {BODY_R:.0f} px")

# Q Strafe: aim beam & volley chevrons
s, cx, cy = render_skill("q", 30, fs=0.5, W=900)
q_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(q_fx > 80, "Q: FX di luar siluet badan", f"{q_fx} px")

# W Skeleton Walk: smoke cloak & ash runes
s, cx, cy = render_skill("w", 20, fs=0.5, W=900)
w_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(w_fx > 80, "W: FX di luar siluet badan", f"{w_fx} px")

# E Death Pact: ring AOE 150 px dunia
s, cx, cy = render_skill("e", 30, fs=0.5, W=1000)
gy = cy + Z.GROUND_DY
hits, total = hits_ring(s, 300, cx, gy)
ok_all &= check(hits > 110,
                "E: ring AOE tepat 300px canvas (=150 dunia, fs=0.5)",
                f"{hits}/{total}")
e_fx = count_fx(s, cx, cy, BODY_R, 320)
ok_all &= check(e_fx > 100, "E: FX di luar siluet badan", f"{e_fx} px")

# R Burning Army: ring AOE 220 px dunia
s, cx, cy = render_skill("r", 40, fs=0.5, W=1000)
hits, total = hits_ring(s, 440, cx, gy)
ok_all &= check(hits > 110,
                "R: ring AOE tepat 440px canvas (=220 dunia, fs=0.5)",
                f"{hits}/{total}")
r_fx = count_fx(s, cx, cy, BODY_R, 400)
ok_all &= check(r_fx > 150, "R: FX di luar siluet badan", f"{r_fx} px")

# 3 tahap per skill berbeda
for skill, dur in Z.SKILL_DUR.items():
    sigs = set()
    for timer in (dur - 3, int(dur * 0.5), 4):
        ss, _, _ = render_skill(skill, timer, W=620)
        sigs.add(pygame.image.tobytes(ss, "RGBA"))
    ok_all &= check(len(sigs) == 3, f"{skill.upper()}: 3 tahap FX berbeda",
                    f"{len(sigs)}/3")

# durasi AI
AI = {"q": 50, "w": 40, "e": 60, "r": 80}
ok_all &= check(Z.SKILL_DUR == AI, "SKILL_DUR == durasi AI base_boss",
                str(Z.SKILL_DUR))
ok_all &= check(Z.SKILL_RADIUS == {"q": 250, "w": 200, "e": 150, "r": 220},
                "SKILL_RADIUS == radius gameplay", str(Z.SKILL_RADIUS))

# budget per skill
for skill, t in (("q", 30), ("w", 20), ("e", 30), ("r", 40)):
    surf = pygame.Surface((528, 528), pygame.SRCALPHA)
    hero = boss_probe(ax=264, ay=284, active_skill=skill,
                      active_skill_timer=t,
                      target=_NS(x=390.0, y=260.0, alive=True),
                      _render_scale=0.72)
    ms = bench_med(lambda: Z.draw_zharok(surf, hero, 264, 284), 20, 7)
    print(f"[i] skill {skill}: {ms:.2f} ms/frame (median, 528x528)")
    ok_all &= check(ms <= 3.5, f"skill {skill} dalam budget", f"{ms:.2f} ms")

# custom projectiles
arr = Z.FireArrow(100, 100, 300, 100)
for _ in range(5):
    arr.update()
ok_all &= check(len(arr.trail) > 0, "FireArrow memiliki trail", f"{len(arr.trail)} pts")

# tidak ada aset PNG
src = open(os.path.join(ROOT, "bosses", "level4.py")).read()
ok_all &= check("pygame.image.load" not in src,
                "100% prosedural (tanpa pygame.image.load)")


# ═══════════════════════ PREVIEW SHEETS ══════════════════════════
font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 30)
font_small = pygame.font.Font(None, 21)
ACCENT = (255, 160, 60)
SUB = (220, 180, 150)
EDGE = (180, 60, 20)


def draw_native(target, rect, native, zoom=1.0, dx=0, dy=0):
    if zoom != 1.0:
        native = pygame.transform.scale(
            native, (int(native.get_width() * zoom),
                     int(native.get_height() * zoom)))
    old = target.get_clip()
    target.set_clip(rect)
    target.blit(native, (rect.centerx - native.get_width() // 2 + dx,
                         rect.centery - native.get_height() // 2 + dy))
    target.set_clip(old)


# ── 1. review sheet ──
W, H = 1400, 860
sheet = pygame.Surface((W, H))
sheet.fill((16, 8, 8))
sheet.blit(font_title.render(
    "ZHAROK v2 - PIXEL MASTERWORK + SKILL FX", True, ACCENT), (36, 22))
sheet.blit(font_small.render(
    "100% prosedural • rig native 1.5x • bone ivory / hellfire / obsidian cloth • selout • "
    "archery 7-keyframe rig • FX world-space (_fx_scale cap 2.6) • Q=250 / W=200 / E=150 / R=220 px dunia",
    True, SUB), (38, 66))

cards = (
    ("IDLE / ALIVE", dict(action="idle", phase=1.25)),
    ("WALK / FOOT SOLVER", dict(action="walk", phase=2.4)),
    ("ATTACK (IMPACT 0.52)", dict(action="attack", phase=1.0, progress=.52)),
    ("E — DEATH PACT", dict(skill="e", timer=30)),
)
for i, (label, kw) in enumerate(cards):
    x = 28 + i * 340
    panel = pygame.Rect(x, 100, 322, 600)
    pygame.draw.rect(sheet, (34, 16, 12), panel, border_radius=12)
    pygame.draw.rect(sheet, EDGE, panel, 2, border_radius=12)
    sheet.blit(font_label.render(label, True, (255, 236, 220)), (x + 16, 116))
    native = pygame.Surface((340, 340), pygame.SRCALPHA)
    if "skill" in kw:
        h = boss_probe(ax=170, ay=190, active_skill=kw["skill"],
                       active_skill_timer=kw["timer"],
                       target=_NS(x=250.0, y=170.0, alive=True))
        Z.draw_zharok(native, h, 170, 190)
        draw_native(sheet, panel.inflate(-10, -66), native, 1.4, 0, 20)
    else:
        Z._draw_zharok_body_raw(native, 170, 190, 1, kw.get("phase", 0),
                                kw["action"], kw.get("progress", 0.0))
        draw_native(sheet, panel.inflate(-10, -66), native, 1.4, 0, 20)

notes = (
    "tengkorak berkerudung • bara jiwa dada",
    "solver kaki kerangka • jejak api",
    "tarikan busur berapi • smear arc + flash",
    "pentagram neraka • tengkorak raksasa",
)
for j, text in enumerate(notes):
    sheet.blit(font_small.render(text, True, (225, 175, 140)),
               (44 + j * 340, 712))
sheet.blit(font_small.render(
    f"rig native {bb.w}x{bb.h} px  •  bbox arena {ab.w}x{ab.h} px  •  "
    f"warna raw {nc} / detail {pc}  •  "
    f"idle {t_idle:.2f} ms / attack {t_atk:.2f} ms (cache-miss)",
    True, (190, 150, 130)), (44, 760))
out1 = os.path.join(ROOT, "docs", "zharok_v2_review.png")
pygame.image.save(sheet, out1)
print(out1)

# ── 2. animation strip ──
SW, SH = 1400, 900
strip = pygame.Surface((SW, SH))
strip.fill((16, 8, 8))
strip.blit(font_title.render("ZHAROK v2 - PROSEDURAL ANIMATION RIG", True,
                             ACCENT), (36, 22))
strip.blit(font_small.render(
    "tiap frame dihitung ulang dari sendi + fase + inersia kain tattered + "
    "archery solver; attack = 7 keyframe dengan frame IMPACT di ap=0.52",
    True, SUB), (38, 66))
rows = (("IDLE / FLAME FLICKER", 8, "idle"),
        ("WALK / SKELETON STRIDE", 8, "walk"),
        ("ATTACK / ARCHERY IMPACT", 10, "attack"))
for row, (label, count, action) in enumerate(rows):
    top = 108 + row * 262
    strip.blit(font_label.render(label, True, ACCENT), (36, top + 66))
    pygame.draw.line(strip, (150, 50, 20), (35, top + 100),
                     (1364, top + 100), 1)
    for i in range(count):
        native = pygame.Surface((190, 240), pygame.SRCALPHA)
        phase = i / count * math.tau
        progress = i / max(1, count - 1)
        Z._draw_zharok_body_raw(native, 95, 150, 1, phase, action, progress)
        fx = 190 + i * 118
        strip.blit(native, (fx, top - 20))
out2 = os.path.join(ROOT, "docs", "zharok_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

# ── 3. in-game size ──
GW, GH = 1200, 420
game = pygame.Surface((GW, GH))
game.fill((28, 22, 20))
for gy in range(0, GH, 40):
    pygame.draw.line(game, (36, 28, 24), (0, gy), (GW, gy), 1)
pygame.draw.line(game, (76, 54, 48), (0, 330), (GW, 330), 3)
game.blit(font_title.render(
    "UKURAN ASLI DI ARENA (pipeline cache hero + lighting + outline)", True,
    (255, 230, 210)), (30, 18))
poses = (
    ("idle", 0, 0.0, None), ("walk", 1.9, 0.0, None),
    ("attack", 0, 0.52, None), ("death_pact", 1.25, 0.0, "e"),
    ("burning_army", 1.25, 0.0, "r"),
)
xpos = 130
for i, (name, ph, prog, skill) in enumerate(poses):
    hero = _ProbeEntity("zharok", xpos, 300)
    hero.pulse = ph
    hero.team = "blue" if i % 2 == 0 else "red"
    if prog:
        hero._zh_attack_active = True
        hero._zh_attack_progress = prog
        hero.timer = 1
    if skill:
        hero.active_skill = skill
        hero.active_skill_timer = 30 if skill == "e" else 40
        hero.target = _ProbeEntity("dummy", xpos + 90, 292)
        hero.target.alive = True
    render_hero("zharok", game, hero, xpos, 300)
    game.blit(font_small.render(name, True, (230, 210, 190)),
              (xpos - 40, 330))
    xpos += 210
out3 = os.path.join(ROOT, "docs", "zharok_v2_in_game.png")
pygame.image.save(game, out3)
out3b = os.path.join(ROOT, "docs", "zharok_v2_ingame.png")
pygame.image.save(game, out3b)
print(out3)

# ── 4. skill FX sheet: 4 skill x 3 tahap ──
KW, KH = 1500, 1160
sk = pygame.Surface((KW, KH))
sk.fill((16, 8, 8))
sk.blit(font_title.render(
    "ZHAROK v2 - SKILL FX MEWAH (world-space, 100% prosedural)", True,
    ACCENT), (36, 22))
sk.blit(font_small.render(
    "Q Strafe (barrage, 50f) • W Skeleton Walk (stealth, 40f) • "
    "E Death Pact (AOE 150, 60f) • R Burning Army (inferno AOE 220, 80f) — "
    "tiap skill 3 tahap: AKTIVASI / STEADY / TELEGRAPH", True, SUB), (38, 66))

skill_cards = (
    ("Q - STRAFE", "q", (40, 16, 12),
     ((47, "aim target"), (28, "multishot"), (6, "impact"))),
    ("W - SKELETON WALK", "w", (32, 14, 20),
     ((37, "burst ash"), (20, "ghost veil"), (4, "emergence"))),
    ("E - DEATH PACT", "e", (44, 18, 14),
     ((56, "pentagram"), (32, "death skull"), (8, "soul blast"))),
    ("R - BURNING ARMY", "r", (48, 14, 12),
     ((76, "pillar & crack"), (44, "fissure skulls"), (10, "magma scorch"))),
)
for ci, (label, skill, panel_col, stages) in enumerate(skill_cards):
    col_x = 28 + ci * 368
    for si, (timer, stage) in enumerate(stages):
        y0 = 100 + si * 350
        panel = pygame.Rect(col_x, y0, 348, 330)
        pygame.draw.rect(sk, panel_col, panel, border_radius=12)
        pygame.draw.rect(sk, EDGE, panel, 2, border_radius=12)
        sk.blit(font_small.render(f"{label}  t={timer} ({stage})", True,
                                  (255, 236, 220)), (col_x + 14, y0 + 12))
        native = pygame.Surface((620, 620), pygame.SRCALPHA)
        h = boss_probe(ax=310, ay=330, active_skill=skill,
                       active_skill_timer=timer,
                       target=_NS(x=440.0, y=300.0, alive=True))
        Z.draw_zharok(native, h, 310, 330)
        scaled = pygame.transform.scale(native, (336, 336))
        old = sk.get_clip()
        sk.set_clip(panel.inflate(-6, -34))
        sk.blit(scaled, (col_x + 6, y0 + 30))
        sk.set_clip(old)
out4 = os.path.join(ROOT, "docs", "zharok_v2_skill_fx.png")
pygame.image.save(sk, out4)
out4b = os.path.join(ROOT, "docs", "zharok_v2_skills.png")
pygame.image.save(sk, out4b)
print(out4)

# ── 5. before / after (snapshot v1 di tools/_zharok_v1_snapshot.py) ──
def load_old_ns():
    path = os.path.join(ROOT, "tools", "_zharok_v1_snapshot.py")
    spec = importlib.util.spec_from_file_location("_zharok_v1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._NS_zharok


BW, BH = 1400, 720
ba = pygame.Surface((BW, BH))
ba.fill((16, 8, 8))
ba.blit(font_title.render(
    "ZHAROK — BEFORE (v1)  vs  AFTER (v2 masterwork + skill FX)", True,
    ACCENT), (36, 22))
ba.blit(font_small.render(
    "kiri: v1 geometri dasar   |   kanan: v2 masterwork (rig 1.5x, 55-warna palette, selout, "
    "archery timeline 7-keyframe + IMPACT, FX world-space Q250/W200/E150/R220)",
    True, SUB), (38, 66))

Old = None
try:
    Old = load_old_ns()
except Exception as e:
    print(f"[i] before/after dilewati: {e}")

if Old is not None:
    cols = (
        ("v1 - idle", None, None), ("v1 - attack", None, 0.52),
        ("v1 - R army", "r", None),
        ("v2 - idle", None, None), ("v2 - attack", None, 0.52),
        ("v2 - R army", "r", None),
    )
    for i, (label, skill, prog) in enumerate(cols):
        x = 24 + i * 228
        panel = pygame.Rect(x, 100, 216, 540)
        pygame.draw.rect(ba, (32, 14, 12), panel, border_radius=10)
        pygame.draw.rect(ba, EDGE, panel, 2, border_radius=10)
        ba.blit(font_small.render(label, True, (255, 236, 220)), (x + 12, 112))
        native = pygame.Surface((300, 300), pygame.SRCALPHA)
        NS = Old if i < 3 else Z
        h = boss_probe(ax=150, ay=160)
        if skill:
            h.active_skill = skill
            h.active_skill_timer = 40
            h.target = _NS(x=230.0, y=140.0, alive=True)
        if prog:
            h._zh_attack_active = True
            h._zh_attack_progress = prog
            h.timer = 40
        NS.draw_zharok(native, h, 150, 160)
        draw_native(ba, panel.inflate(-8, -40), native, 1.35, 0, 10)
    ba.blit(font_small.render(
        "kiri: v1 (tools/_zharok_v1_snapshot.py)   |   kanan: v2 (selout, "
        "dither, specular, 7-keyframe attack, FX world-space 3 tahap)",
        True, (220, 170, 150)), (24, 660))
    out5 = os.path.join(ROOT, "docs", "zharok_v2_before_after.png")
    pygame.image.save(ba, out5)
    print(out5)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
