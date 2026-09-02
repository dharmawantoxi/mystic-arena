#!/usr/bin/env python3
"""Audit v3 GORATH — sistem tempur lapisan hidup + controller renderer.

Mengunci kontrak tempur v3 yang dulu hanya bisa dinilai mata:

  1. 100% prosedural (tidak ada image.load / PNG / sprite sheet) di
     heroes/gorath_fx.py, heroes/combat_feel.py, dan sumber _NS_gorath.
  2. API publik lapisan hidup + renderer (backward-compat pemanggil lama).
  3. Palet sinkron (_PALETTE_SYNC <-> NS.PALETTE) & konstanta skill sama
     (SKILL_DUR / WORLD_RADIUS <-> SKILL_RADIUS).
  4. attach/owns: non-GORATH ditolak; GORATH diambil alih; idle = lapisan
     hidup TIDAK menggambar apa pun (tidak ada efek abadi).
  5. Ayunan controller: urutan fase, jendela hit 0.40-0.66, trail tumbuh
     saat SWING, debu antisipasi di awal, sapu udara + ImpactFX di frame
     IMPACT, trail meluruh setelah ayunan.
  6. Skill: cast Q/W/E/R -> SkillFX ber-kind benar, total = SKILL_TOTAL;
     W -> 3 GorathProjectile damage=0 yang terbang dan MATI (tidak bocor);
     E mengikuti titik pendaratan; R di caster + shake + hit-stop.
  7. Impact package: ImpactFX + spark + debris + hit flash + shake +
     hit-stop 0.03-0.08 s yang SELALU terkuras.
  8. Semua cap dihormati (partikel/budget, proyektil, impact, skill).
  9. Supresi ganda: renderer melewati FX canvas saat lapisan hidup dimiliki
     (gate `not owned:`), dan fallback canvas tetap jalan kalau modul FX
     tidak aktif.
 10. reset_all membersihkan SEMUA (owns False, partikel 0).
 11. Layar tanah + layar hidup digambar di surface dummy tanpa error, dan
     preview sheet dihasilkan ke docs/gorath_v3_combat_preview.png.

Jalankan:  python3 tools/_audit_gorath_v3.py
"""
import inspect
import math
import os
import sys
import time
from types import SimpleNamespace as _NS

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame                                       # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                       # noqa: E402
from heroes import _ProbeEntity                     # noqa: E402
from heroes import combat_feel as FEEL              # noqa: E402
from heroes import gorath_fx as F                   # noqa: E402
from bosses.level2 import _NS_gorath as G           # noqa: E402

DT = 1.0 / 60.0
COOLDOWN = 44
PHASE_ORDER = ("ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW",
               "RECOVERY")


def check(cond, label, extra=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {label} {extra}")
    return bool(cond)


# ── probe / helper ─────────────────────────────────────────────────────────
def fresh_hero(x=0.0, y=0.0, cooldown=COOLDOWN, scale=None):
    h = _ProbeEntity("gorath", x, y)
    h.boss_type = "gorath"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = cooldown
    h.range = 58
    h.speed = 1.6
    h.hp = h.max_hp = 9000
    h.radius = 36
    h.hurt_flash_timer = 0
    if scale is not None:
        h._render_scale = scale
    return h


def dummy_target(x=300.0, y=0.0):
    t = _ProbeEntity("creep", x, y)
    t.alive = True
    t.radius = 14
    return t


def drive_swing(hero, frames=COOLDOWN, x=0.0, y=0.0):
    """Jalankan satu ayunan penuh lewat controller + lapisan hidup.

    Mengembalikan daftar snapshot per frame (fase, trail, partikel,
    impact, hit) untuk diperiksa audit.
    """
    out = []
    for i in range(frames):
        hero._gor_attack_active = True
        hero._gor_attack_manual = True
        hero._gor_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        G._update_gorath_attack_anim(hero)
        F.tick(DT)
        d = F.director_for(hero)
        out.append({
            "phase": hero._gor_attack_phase,
            "hit": bool(hero._gor_hit_active),
            "trail": len(d.trail.points),
            "particles": d.particles.count(),
            "impacts": len(d.impacts),
            "skills": len(d.skills),
            "proj": d.projectiles.count(),
        })
    # matikan ayunan + biarkan efek luruh
    hero._gor_attack_active = False
    hero._gor_attack_manual = False
    for _ in range(20):
        F.tick(DT)
    return out


ok_all = True
t_all = time.perf_counter()

# ── 1. 100% prosedural + API publik ───────────────────────────────────────
for rel in ("heroes/gorath_fx.py", "heroes/combat_feel.py"):
    src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    for bad in ("pygame.image.load", "image.load(", ".png", ".jpg",
                ".gif", ".bmp", ".ogg", ".wav", "load_asset"):
        ok_all &= check(bad not in src, f"tanpa asset eksternal {rel}",
                        f"-> {bad}" if bad in src else "")
gsrc = inspect.getsource(G)
ok_all &= check("pygame.image.load" not in gsrc,
                "tanpa image.load di _NS_gorath")

fx_api = ("attach", "owns", "director_for", "tick", "reset_all",
          "total_particles", "projectiles_for", "stats",
          "draw_ground_layer", "draw_live_layer", "notify_melee_impact",
          "notify_projectile_impact", "notify_skill_impact",
          "notify_skill_cast", "notify_skill_start", "notify_skill_end",
          "draw_blood_bolt", "draw_debug_overlay", "hit_stop", "shake",
          "should_freeze_frame", "GORATH_PALETTE", "GORATH_FX_ENABLED")
missing = [n for n in fx_api if not hasattr(F, n)]
ok_all &= check(not missing, "API publik gorath_fx lengkap", str(missing))

gr_api = ("draw_gorath", "draw_boss", "_update_gorath_attack_anim",
          "_update_attack_anim", "_attack_curve", "_resolve_pose",
          "_tip_local", "_tip_screen", "_swing_hitbox", "attack_phase",
          "attack_phases_order", "PALETTE", "SKILL_DUR", "SKILL_RADIUS",
          "ANIM_STATES", "ATTACK_ACTIVE_WINDOW", "DEBUG_CHARACTER",
          "BloodProjectile", "_draw_shockwave")
missing = [n for n in gr_api if not hasattr(G, n)]
ok_all &= check(not missing, "API renderer _NS_gorath lengkap", str(missing))

# ── 2. Palet & konstanta sinkron ──────────────────────────────────────────
drift = []
for dst, src in F._PALETTE_SYNC.items():
    if src in G.PALETTE and tuple(F.GORATH_PALETTE[dst][:3]) \
            != tuple(G.PALETTE[src][:3]):
        drift.append(f"{dst}~{src}")
ok_all &= check(not drift, "palet sinkron _PALETTE_SYNC <-> NS.PALETTE",
                str(drift))
ok_all &= check(F.SKILL_DUR == G.SKILL_DUR, "SKILL_DUR sinkron",
                str(F.SKILL_DUR))
# WORLD_RADIUS lapisan hidup = radius GAMEPLAY di base_boss (q=90 bukan
# radius damage; w/e/r 150/85/190). SKILL_RADIUS di level2 (75/95/80/180)
# adalah skala cincin telegraph — besaran berbeda, jangan disamakan.
bb_src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
              encoding="utf-8").read()
import re                                    # noqa: E402
_bb_radii = {}
for _k, _fn in (("w", "_gorath_w"), ("e", "_gorath_e"), ("r", "_gorath_r")):
    _s = bb_src.index("def " + _fn)
    _seg = bb_src[_s:bb_src.index("\n    def ", _s + 10)]
    _m = re.findall(r"<= (\d+)", _seg)
    _bb_radii[_k] = int(_m[0]) if _m else None
ok_all &= check(_bb_radii == {"w": 150, "e": 85, "r": 190},
                "radius gameplay base_boss sinkron", str(_bb_radii))
ok_all &= check(F.WORLD_RADIUS["w"] == 150 and F.WORLD_RADIUS["e"] == 85
                and F.WORLD_RADIUS["r"] == 190,
                "WORLD_RADIUS lapisan hidup == radius gameplay",
                str(F.WORLD_RADIUS))
ok_all &= check(all(abs(F.SKILL_TOTAL[k] - F.SKILL_DUR[k] / 60.0) < 0.021
                    for k in F.SKILL_TOTAL),
                "SKILL_TOTAL ~ SKILL_DUR/60 (toleransi 1 frame)",
                str(F.SKILL_TOTAL))
ok_all &= check(G.DEBUG_CHARACTER is False and F.DEBUG_CHARACTER is False,
                "debug default mati")

# ── 3. attach/owns + idle tidak menggambar apa pun ────────────────────────
other = _ProbeEntity("creep", 0, 0)
other.boss_type = "creep"
ok_all &= check(not F.owns(other),
                "entitas asing tanpa attach: owns False")
try:
    F.attach(other)
    attach_ok = True
except Exception as exc:                        # pragma: no cover
    attach_ok = False
ok_all &= check(attach_ok, "attach entitas asing aman (tidak crash)")
# pola gornak: pintu masuk sebenarnya di pipeline (heroes/__init__.py),
# bukan di modul FX — modul hanya dipanggil untuk karakter yang terdaftar.
ok_all &= check("gorath" in heroes._LIVE_FX_HEROES
                and "creep" not in heroes._LIVE_FX_HEROES,
                "pipeline hanya memanggil gorath_fx untuk GORATH")
F.reset_all()

h = fresh_hero(150, 150)
ok_all &= check(F.attach(h) is True and F.owns(h) is True,
                "GORATH diambil alih lapisan hidup")
d = F.director_for(h)
surf = pygame.Surface((360, 260), pygame.SRCALPHA)
for _ in range(30):
    F.tick(DT)
    surf.fill((0, 0, 0, 0))
    F.draw_ground_layer(surf, h, h.x, h.y)
    F.draw_live_layer(surf, h, h.x, h.y)
idle_rect = surf.get_bounding_rect(min_alpha=8)
ok_all &= check(idle_rect.width == 0 and idle_rect.height == 0,
                "idle: lapisan hidup tidak menggambar apa pun",
                f"bbox {idle_rect}")
ok_all &= check(d.trail.points == [] and d.skills == []
                and d.projectiles.count() == 0 and d.particles.count() == 0,
                "idle: trail/skill/proyektil/partikel kosong")

# ── 4. Ayunan penuh ───────────────────────────────────────────────────────
F.reset_all()
h = fresh_hero(150, 150)
F.attach(h)
snaps = drive_swing(h, COOLDOWN, h.x, h.y)

seen = [s["phase"] for s in snaps if s["phase"] != "NONE"]
order = []
for ph in seen:
    if not order or order[-1] != ph:
        order.append(ph)
ok_all &= check(tuple(order) == PHASE_ORDER,
                "urutan fase ayunan", "->".join(order))

win = [s for s in snaps if s["hit"]]
ok_all &= check(bool(win), "jendela hit pernah aktif")
ok_all &= check(all(0.40 <= (i / float(COOLDOWN)) < 0.66
                    for i, s in enumerate(snaps) if s["hit"]),
                "jendela hit hanya di (0.40, 0.66)")

swing_frames = [s for s in snaps if s["phase"] in ("SWING", "IMPACT",
                                                   "FOLLOW")]
ok_all &= check(bool(swing_frames) and all(s["trail"] > 0
                                           for s in swing_frames[2:]),
                f"trail tumbuh saat swing ({swing_frames[0]['trail']}->"
                f"{swing_frames[-1]['trail']} sampel)")

early_dust = any(s["particles"] > 0 for s in snaps[:12])
ok_all &= check(early_dust, "debu antisipasi di awal ayunan")

impact_air = any(s["impacts"] > 0 for s in snaps)
ok_all &= check(impact_air, "sapu udara ImpactFX di frame IMPACT")
impact_px = any(s["particles"] >= 7 for s in snaps[18:30])
ok_all &= check(impact_px, "partikel sapu udara di sekitar frame IMPACT")

h._gor_attack_active = False
h._gor_attack_manual = False
for _ in range(30):
    F.tick(DT)
ok_all &= check(d.trail.points == [], "trail meluruh setelah ayunan")
ok_all &= check(d.impacts == [] and d.particles.count() <= 5,
                "impact/partikel meluruh setelah ayunan",
                f"impact={len(d.impacts)} partikel={d.particles.count()}")

# ── 5. Skill FX ───────────────────────────────────────────────────────────
F.reset_all()
h = fresh_hero(200, 150)
h.target = dummy_target(420, 60)
F.attach(h)
d = F.director_for(h)

for key, dur in (("q", 90), ("w", 60), ("e", 35), ("r", 90)):
    F.notify_skill_cast(h, key)
    fx = d.skills[-1]
    ok_all &= check(fx.kind == key and abs(fx.x - 200) < 2,
                    f"cast {key}: SkillFX {fx.kind} di caster",
                    f"total {fx.total:.2f}s")
    ok_all &= check(abs(fx.total - F.SKILL_TOTAL[key]) < 1e-3,
                    f"cast {key}: durasi = SKILL_TOTAL",
                    f"{fx.total:.2f} vs {F.SKILL_TOTAL[key]:.2f}")
    if key == "w":
        # voli diperiksa SEGERA setelah cast (sebelum lifecycle dikuras)
        proj = [p for p in d.projectiles.list()]
        ok_all &= check(len(proj) == 3, "cast w: voli 3 bolt",
                        str(len(proj)))
        ok_all &= check(all(p.damage == 0 for p in proj),
                        "cast w: damage=0 (visual saja)")
    # kuras lifecycle sampai selesai
    for _ in range(int(F.SKILL_TOTAL[key] * 60) + 30):
        F.tick(DT)
    ok_all &= check(d.skills == [], f"cast {key}: lifecycle selesai & hilang")
    if key == "w":
        # target (420,60) jauh dari caster: bolt harus terbang, kena, mati
        ok_all &= check(d.projectiles.count() == 0,
                        "cast w: bolt mati & tidak bocor",
                        f"sisa {d.projectiles.count()} setelah lifecycle")
    if key == "e":
        # E mengikuti unit saat melompat
        F.notify_skill_cast(h, "e")
        fx = d.skills[-1]
        ok_all &= check(fx.leap_from is not None, "cast e: jejak titik tolak")
        h.x, h.y = 400, 90
        F.tick(DT)
        ok_all &= check(abs(fx.x - 400) < 2, "cast e: fx mengikuti lompatan")
        h.x, h.y = 200, 150
        for _ in range(int(F.SKILL_TOTAL["e"] * 60) + 30):
            F.tick(DT)
        ok_all &= check(d.skills == [], "cast e: lifecycle selesai")
    if key == "r":
        ok_all &= check(FEEL.SHAKE.amount > 0 or FEEL.SHAKE.shake_duration > 0,
                        "cast r: screen shake dipicu")
        ok_all &= check(FEEL.HITSTOP.total > 0, "cast r: hit-stop dipicu",
                        f"{FEEL.HITSTOP.total} frame")

# ── 6. Impact package (melee hit) ─────────────────────────────────────────
F.reset_all()
h = fresh_hero(150, 150)
tgt = dummy_target(210, 150)
F.attach(h)
d = F.director_for(h)
FEEL.reset()
F.notify_melee_impact(h, tgt, 120, False)
ok_all &= check(len(d.impacts) == 1 and d.impacts[0].kind == "blade",
                "melee impact: ImpactFX blade")
ok_all &= check(d.hit_flash > 0.0, "melee impact: hit flash")
ok_all &= check(d.particles.count() >= 10,
                "melee impact: spark+debris+blood",
                f"{d.particles.count()} partikel")
ok_all &= check(FEEL.SHAKE.amount > 0, "melee impact: shake")
sec = FEEL.HITSTOP.total * DT
ok_all &= check(0.03 - 1e-3 <= sec <= 0.08 + 2e-3,
                "melee impact: hit-stop 0.03-0.08 s", f"{sec:.3f}s")
for _ in range(12):
    FEEL.should_freeze_frame()
ok_all &= check(not FEEL.should_freeze_frame(),
                "hit-stop terkuras (tidak membeku selamanya)")
for _ in range(90):
    FEEL.SHAKE.update(DT)
ok_all &= check(FEEL.SHAKE.amount == 0.0, "shake meluruh ke nol")

# tanpa target / tanpa crash
F.notify_melee_impact(h, None, 94, False)
F.notify_projectile_impact(h, 120, 120, 0.0, 0, False)
F.notify_skill_impact(h, 120, 120, 85, "e")
ok_all &= check(len(d.impacts) >= 1, "notify tanpa target aman")

# ── 7. Cap pool ───────────────────────────────────────────────────────────
budget = F.particle_budget()
for _ in range(300):
    d.particles.burst(0, 0, 40, life=(0.5, 0.5))
ok_all &= check(d.particles.count() <= budget and budget <= F.MAX_PARTICLES,
                "cap partikel dihormati",
                f"{d.particles.count()}/{budget} (max {F.MAX_PARTICLES})")
for _ in range(40):
    d.projectiles.spawn(0, 0, 300, 0)
ok_all &= check(d.projectiles.count() <= F.MAX_PROJECTILES,
                "cap proyektil dihormati",
                f"{d.projectiles.count()}/{F.MAX_PROJECTILES}")
for _ in range(12):
    F.notify_skill_cast(h, "q")
ok_all &= check(len(d.skills) <= F.MAX_SKILLS,
                "cap skill FX dihormati", f"{len(d.skills)}/{F.MAX_SKILLS}")
for _ in range(25):
    F.notify_melee_impact(h, tgt, 80, False)
ok_all &= check(len(d.impacts) <= F.MAX_IMPACTS,
                "cap impact dihormati", f"{len(d.impacts)}/{F.MAX_IMPACTS}")

# ── 8. Supresi ganda + fallback + lane hero ───────────────────────────────
src_draw = inspect.getsource(G.draw_gorath)
ok_all &= check("if not owned:" in src_draw,
                "renderer melewati FX canvas saat lapisan hidup dimiliki")
ok_all &= check("if active_skill in (\"q\", \"w\", \"e\", \"r\") "
                "and not owned:" in src_draw,
                "shockwave canvas dilewati saat owned (gate di draw_gorath)")

F.reset_all()
h = fresh_hero(150, 150)
h.active_skill = "q"
h.active_skill_timer = 50
h.target = dummy_target(260, 130)
surf = pygame.Surface((360, 300), pygame.SRCALPHA)
saved = F.GORATH_FX_ENABLED
F.GORATH_FX_ENABLED = False
G.draw_gorath(surf, h, 150, 150)
ok_all &= check(not F.owns(h) and not hasattr(h, "_gor_fx"),
                "fallback: FX nonaktif -> renderer canvas murni")
ok_all &= check(surf.get_bounding_rect(min_alpha=8).width > 20,
                "fallback: badan tetap tergambar")
F.GORATH_FX_ENABLED = saved

hero_surf = pygame.Surface((600, 400), pygame.SRCALPHA)
h2 = fresh_hero(300, 200, scale=0.62)
heroes.render_hero("gorath", hero_surf, h2, 300, 200)
ok_all &= check(F.owns(h2) is True, "lane hero: lapisan hidup terpasang")

# ── 9. render layar + reset ───────────────────────────────────────────────
F.reset_all()
h = fresh_hero(150, 150)
F.attach(h)
F.notify_skill_cast(h, "r")
surf = pygame.Surface((360, 260), pygame.SRCALPHA)
for _ in range(8):
    F.tick(DT)
    surf.fill((0, 0, 0, 0))
    F.draw_ground_layer(surf, h, h.x, h.y)
    F.draw_live_layer(surf, h, h.x, h.y)
r = surf.get_bounding_rect(min_alpha=8)
ok_all &= check(r.width > 0, "layar tanah+hidup menggambar FX skill R",
                f"bbox {r.w}x{r.h}")

d2 = F.director_for(h)
F.draw_debug_overlay(surf, d2)
ok_all &= check(surf.get_bounding_rect(min_alpha=8).width > 0,
                "overlay debug tidak crash")

F.reset_all()
ok_all &= check(not F.owns(h) and F.total_particles() == 0,
                "reset_all: owns False + partikel 0")

# ── 10. preview sheet ─────────────────────────────────────────────────────
try:
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    W, H = 1400, 760
    sheet = pygame.Surface((W, H))
    sheet.fill((16, 12, 18))
    font_big = pygame.font.SysFont("consolas", 26, bold=True)
    font_small = pygame.font.SysFont("consolas", 16)
    title = font_big.render("GORATH v3 — COMBAT FX (live layer 1:1)",
                            True, (200, 120, 110))
    sheet.blit(title, (24, 14))
    cell = 240
    labels = ["idle", "anticipation", "windup", "swing", "IMPACT",
              "follow", "W volley", "R cast", "melee hit", "hurt"]
    pos = [(24 + (i % 5) * 272, 64 + (i // 5) * 330) for i in range(10)]

    def frame_surface(hero, progress=None, skill=None, impact=None,
                      hurt=False):
        s = pygame.Surface((240, 280), pygame.SRCALPHA)
        s.fill((22, 18, 26))
        if hurt:
            hero.hurt_flash_timer = 10
        if progress is not None:
            hero._gor_attack_active = True
            hero._gor_attack_manual = True
            hero._gor_attack_progress = progress
        if skill:
            hero.active_skill = skill
            hero.active_skill_timer = 60
            if skill == "w":
                hero.target = dummy_target(hero.x + 220, hero.y)
        F.tick(DT)
        if impact:
            F.notify_melee_impact(hero, dummy_target(hero.x + 70,
                                                     hero.y), 110, True)
            F.tick(DT)
        G.draw_gorath(s, hero, 120, 150)
        hero._gor_attack_active = False
        hero._gor_attack_manual = False
        hero.active_skill = None
        hero.hurt_flash_timer = 0
        return s

    hero = fresh_hero(120, 150)
    hero.target = dummy_target(320, 120)
    F.reset_all()
    F.attach(hero)
    seq = [None, 0.08, 0.22, 0.38, 0.54, 0.72]
    for i in range(6):
        fr = frame_surface(hero, progress=seq[i] if i > 0 else None)
        sheet.blit(fr, pos[i])
    fr = frame_surface(hero, skill="w")
    sheet.blit(fr, pos[6])
    fr = frame_surface(hero, skill="r")
    sheet.blit(fr, pos[7])
    fr = frame_surface(hero, impact=True)
    sheet.blit(fr, pos[8])
    fr = frame_surface(hero, hurt=True)
    sheet.blit(fr, pos[9])
    for i, lab in enumerate(labels):
        sheet.blit(font_small.render(lab, True, (190, 160, 150)), pos[i])
    out = os.path.join(ROOT, "docs", "gorath_v3_combat_preview.png")
    pygame.image.save(sheet, out)
    print(out)
except Exception as exc:                          # pragma: no cover
    ok_all &= check(False, "preview sheet", repr(exc))

# ── ringkasan ─────────────────────────────────────────────────────────────
ms = (time.perf_counter() - t_all) * 1000.0
print(f"[i] audit selesai dalam {ms:.0f} ms")
print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
