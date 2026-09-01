#!/usr/bin/env python3
"""Audit terukur + lembar preview untuk ZEPHYR v3 (combat / game feel).

Menghasilkan (di ``docs/``):
  zephyr_v3_swing_strip.png    — 12 frame ayunan busur + weapon trail
  zephyr_v3_projectile.png     — bolt prosedural: normal, crit, sudut
  zephyr_v3_impact.png         — timeline impact FX (flash/shock/debris)
  zephyr_v3_skillfx.png        — lifecycle SkillFX Q/W/E/R
  zephyr_v3_ingame.png         — komposit arena: hero + lapisan FX hidup

Jalankan:  python3 tools/_audit_zephyr_v3.py
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import math                                                   # noqa: E402
import pygame                                                 # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                                 # noqa: E402
from heroes import _ProbeEntity                               # noqa: E402
from heroes._bundle import _NS_zephyr as Z                    # noqa: E402
from heroes import zephyr_fx as F                             # noqa: E402

DOCS = os.path.join(ROOT, "docs")
BG = (18, 14, 26)
BG2 = (26, 20, 36)
OK = 0
FAIL = 0


def check(label, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1
        print("  [ok]   %-46s %s" % (label, detail))
    else:
        FAIL += 1
        print("  [FAIL] %-46s %s" % (label, detail))


def panel(w, h, tint=BG):
    s = pygame.Surface((w, h))
    s.fill(tint)
    for y in range(0, h, 6):
        pygame.draw.line(s, (tint[0] + 4, tint[1] + 3, tint[2] + 5),
                         (0, y), (w, y))
    return s


def label(surf, text, x, y, col=(230, 200, 240)):
    font = pygame.font.Font(None, 17)
    surf.blit(font.render(text, True, col), (x, y))


def fresh_hero(x=0, y=0):
    h = _ProbeEntity("zephyr", x, y)
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 30
    h.range = 130
    h.speed = 1.6
    return h


# ───────────────────────────────────────────────────────────────────────────
# 1.  SWING STRIP  — busur + trail
# ───────────────────────────────────────────────────────────────────────────
def sheet_swing():
    cols, cw, ch = 6, 210, 240
    sheet = panel(cols * cw, ch * 2 + 26)
    label(sheet, "ZEPHYR v3 — SWING ARC + WEAPON TRAIL "
                 "(anticipation - windup - swing - impact - follow - recovery)",
          8, 6)
    for i in range(12):
        ap = i / 11.0
        cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
        Z._draw_zephyr_elite(cell, cw // 2 - 10, ch - 74, 1, 1.2,
                             "attack", ap)
        sheet.blit(cell, ((i % cols) * cw, 22 + (i // cols) * ch))
        label(sheet, "%.2f  %s" % (ap, _phase_name(ap)),
              (i % cols) * cw + 6, 24 + (i // cols) * ch)
    pygame.image.save(sheet, os.path.join(DOCS, "zephyr_v3_swing_strip.png"))
    return sheet


def _phase_name(ap):
    if ap < Z.ATTACK_ANTICIPATION_END:
        return "ANTICIPATION"
    if ap < Z.ATTACK_WINDUP_END:
        return "WINDUP"
    if ap < Z.ATTACK_SWING_END:
        return "SWING"
    if ap < Z.ATTACK_IMPACT_END:
        return "IMPACT"
    if ap < Z.ATTACK_FOLLOW_END:
        return "FOLLOW"
    return "RECOVERY"


# ───────────────────────────────────────────────────────────────────────────
# 2.  PROJECTILE
# ───────────────────────────────────────────────────────────────────────────
def sheet_projectile():
    sheet = panel(900, 300)
    label(sheet, "ZEPHYR v3 — PROJECTILE: core + glow + directional shape "
                 "+ thorns + rotation + trail", 8, 6)
    for i in range(6):
        ang = i * math.pi / 3
        F.draw_bolt(sheet, 90 + i * 140, 100, ang, age=i * 9)
        label(sheet, "%.0f deg" % math.degrees(ang), 66 + i * 140, 140)
    for i in range(6):
        ang = i * math.pi / 3
        F.draw_bolt(sheet, 90 + i * 140, 220, ang, age=i * 9, crit=True,
                    radius=7.5)
    label(sheet, "CRIT (gold ramp)", 8, 250)

    # ZephyrProjectile penuh (dengan trail hidup)
    ps = F.ParticleSystem()
    pr = F.ZephyrProjectile(40, 275, 860, 275, speed=600, particles=ps)
    for _ in range(26):
        pr.update(1 / 60.0)
        ps.update(1 / 60.0)
    pr.draw(sheet)
    ps.draw(sheet)
    pygame.image.save(sheet, os.path.join(DOCS, "zephyr_v3_projectile.png"))
    return sheet, pr, ps


# ───────────────────────────────────────────────────────────────────────────
# 3.  IMPACT FX
# ───────────────────────────────────────────────────────────────────────────
def sheet_impact():
    sheet = panel(960, 220)
    label(sheet, "ZEPHYR v3 — IMPACT: flash + shockwave + slash fragment "
                 "+ spark + debris (t = 0.00 .. 0.30 s)", 8, 6)
    for i in range(6):
        fx = F.ImpactFX(90 + i * 155, 120, angle=-0.35, power=1.4,
                        crit=(i % 3 == 2))
        for _ in range(i * 3):
            fx.update(1 / 60.0)
        fx.draw(sheet)
        label(sheet, "t=%.2fs" % (i * 3 / 60.0), 66 + i * 155, 190)
    pygame.image.save(sheet, os.path.join(DOCS, "zephyr_v3_impact.png"))
    return sheet


# ───────────────────────────────────────────────────────────────────────────
# 4.  SKILL FX LIFECYCLE
# ───────────────────────────────────────────────────────────────────────────
def sheet_skill():
    kinds = ("q", "w", "e", "r")
    cw, ch = 240, 240
    sheet = panel(cw * 4, ch + 26)
    label(sheet, "ZEPHYR v3 — SKILL FX LIFECYCLE  "
                 "(cast - charge - release - area - impact - fade)", 8, 6)
    for i, k in enumerate(kinds):
        ps = F.ParticleSystem()
        fx = F.SkillFX(k, cw // 2, 150, ps)
        # maju ke tengah fase AREA supaya semua lapisan terlihat
        target = fx.t_release + (fx.t_area - fx.t_release) * 0.35
        while fx.age < target:
            fx.update(1 / 60.0)
            ps.update(1 / 60.0)
        cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
        fx.draw_ground(cell)
        ps.draw(cell, layer="back")
        fx.draw_front(cell)
        ps.draw(cell, layer="front")
        sheet.blit(cell, (i * cw, 22))
        label(sheet, "%s  phase=%s  r=%d" % (k.upper(), fx.phase,
                                             int(fx.radius)),
              i * cw + 8, 26)
    pygame.image.save(sheet, os.path.join(DOCS, "zephyr_v3_skillfx.png"))
    return sheet


# ───────────────────────────────────────────────────────────────────────────
# 5.  IN-GAME COMPOSITE
# ───────────────────────────────────────────────────────────────────────────
def sheet_ingame():
    """Filmstrip 4 momen: windup, swing+trail, impact, aftermath."""
    PW, PH = 470, 300
    moments = ((14, "WINDUP"), (22, "SWING + TRAIL"),
               (34, "IMPACT + SHAKE"), (46, "AFTERMATH"))
    sheet = panel(PW * 2, PH * 2 + 26, (24, 40, 26))
    label(sheet, "ZEPHYR v3 — IN-GAME: sprite cache + live FX layer "
                 "(ground fx / trail / projectile / particles / impact)",
          8, 6, (220, 255, 220))

    hero = fresh_hero(120, 190)
    tgt = _ProbeEntity("dummy", 340, 186)
    tgt.alive = True
    tgt.radius = 18
    hero.target = tgt
    d = F.director_for(hero)
    for coll in (d.particles.clear, d.projectiles.clear, d.impacts.clear,
                 d.skills.clear, d.trail.reset):
        coll()

    seq = [0] * 2 + list(range(30, 0, -1))
    want = dict(moments)
    shots = {}
    for frame in range(50):
        # attack_timer adalah sumber kebenaran: render_hero menyalinnya
        # ke .timer lewat _adapt_hero_to_boss()
        hero.attack_timer = hero.timer = seq[frame % len(seq)]
        hero.pulse += 0.06
        Z._update_attack_anim(hero)
        if frame == 20:
            d.projectiles.spawn(hero.x + 26, hero.y - 22, tgt.x, tgt.y,
                                target=tgt, damage=27, speed=300)
        if frame == 33:
            d.on_impact(tgt.x, tgt.y, 0.05, 1.5, True)
        d.update(1 / 60.0)
        F.SHAKE.update(1 / 60.0)
        if frame in want:
            cell = panel(PW, PH, (24, 40, 26))
            for i in range(160):
                pygame.draw.rect(cell, (30, 52, 32),
                                 ((i * 97) % PW, (i * 53) % PH, 3, 2))
            d.draw_ground(cell)
            heroes.render_hero("zephyr", cell, hero,
                               int(hero.x), int(hero.y))
            d.draw_front(cell)
            pygame.draw.circle(cell, (60, 30, 40),
                               (int(tgt.x), int(tgt.y)), 18)
            pygame.draw.circle(cell, (140, 60, 80),
                               (int(tgt.x), int(tgt.y)), 18, 2)
            label(cell, "%s  ap=%.2f  shake=%.1f" % (
                want[frame], hero._zp_attack_progress, F.SHAKE.amount),
                6, 6, (230, 255, 230))
            shots[frame] = cell

    for i, (fr, _n) in enumerate(moments):
        cell = shots.get(fr)
        if cell:
            sheet.blit(cell, ((i % 2) * PW, 22 + (i // 2) * PH))
    pygame.image.save(sheet, os.path.join(DOCS, "zephyr_v3_ingame.png"))
    return sheet, d


# ───────────────────────────────────────────────────────────────────────────
# AUDIT
# ───────────────────────────────────────────────────────────────────────────
def audit():
    print("\n=== ZEPHYR v3 AUDIT ===\n")

    # 1. prosedural murni
    import inspect
    src = inspect.getsource(F)
    src_rig = inspect.getsource(Z)
    banned = ("pygame.image.load", "image.load(", "load_extended",
              "pygame.image.frombytes(")
    hits = [b for b in banned if b in src or b in src_rig]
    check("tanpa asset eksternal", not hits, hits or "0 pemanggilan")

    # 2. busur ayunan benar-benar melengkung
    pts = [Z._staff_tip_local(0.0, "attack", i / 24.0) for i in range(25)]
    # simpangan dari garis lurus start->end harus signifikan
    x0, y0 = pts[0]
    x1, y1 = pts[-1]
    dev = 0
    for i, (px, py) in enumerate(pts):
        t = i / 24.0
        lx = x0 + (x1 - x0) * t
        ly = y0 + (y1 - y0) * t
        dev = max(dev, math.hypot(px - lx, py - ly))
    check("swing berbasis busur (bukan lerp lurus)", dev > 20,
          "deviasi maks %.1f px" % dev)

    # 3. fase serangan lengkap
    phases = {_phase_name(i / 60.0) for i in range(61)}
    check("6 fase serangan hadir", len(phases) == 6, sorted(phases))

    # 4. hit window
    lo, hi = Z.ATTACK_ACTIVE_WINDOW
    check("jendela hit aktif masuk akal", 0.3 < lo < hi < 0.7,
          "%.2f..%.2f" % (lo, hi))

    # 5. trail menghasilkan piksel
    a = pygame.Surface((240, 240), pygame.SRCALPHA)
    b = pygame.Surface((240, 240), pygame.SRCALPHA)

    def pt(dx, dy):
        return (120 + dx, 160 + dy)
    Z._draw_staff_swing_trail(a, pt, 1.2, 0.50)
    check("weapon trail menggambar sesuatu",
          a.get_bounding_rect(min_alpha=4).width > 20,
          str(a.get_bounding_rect(min_alpha=4)))
    Z._draw_staff_swing_trail(b, pt, 1.2, 0.44)
    check("trail berubah mengikuti progress",
          pygame.image.tobytes(a, "RGBA") != pygame.image.tobytes(b, "RGBA"))

    # 6. trail tidak muncul di luar ayunan
    c = pygame.Surface((240, 240), pygame.SRCALPHA)
    Z._draw_staff_swing_trail(c, pt, 1.2, 0.05)
    check("trail mati di fase anticipation",
          c.get_bounding_rect(min_alpha=4).width == 0)

    # 7. particle system: pooling + cap
    ps = F.ParticleSystem(cap=40)
    ps.burst(50, 50, 500)
    check("particle cap dihormati", ps.count() <= 40, ps.count())
    for _ in range(400):
        ps.update(1 / 60.0)
    check("partikel habis (tidak abadi)", ps.count() == 0, ps.count())
    check("pool dipakai ulang", len(ps._pool) > 0, len(ps._pool))

    # 8. projectile lifecycle
    tgt = _ProbeEntity("dummy", 300, 100)
    tgt.alive = True
    tgt.radius = 14
    sys_p = F.ProjectileSystem(F.ParticleSystem())
    pr = sys_p.spawn(50, 100, 300, 100, target=tgt, speed=400)
    states = []
    for _ in range(200):
        sys_p.update(1 / 60.0)
        states.append(pr.state)
    check("projectile: travel -> impact -> dead",
          "travel" in states and "impact" in states and "dead" in states)
    check("projectile dibersihkan", sys_p.count() == 0, sys_p.count())

    # 9. projectile homing
    tgt2 = _ProbeEntity("dummy", 300, 100)
    tgt2.alive = True
    tgt2.radius = 12
    p2 = F.ZephyrProjectile(50, 100, 300, 100, speed=300, target=tgt2)
    for _ in range(20):
        tgt2.y += 3
        p2.update(1 / 60.0)
    check("projectile homing ke target bergerak", p2.velocity.y > 5,
          "vy=%.1f" % p2.velocity.y)

    # 10. impact fx berumur pendek
    fx = F.ImpactFX(10, 10, power=2.0)
    n = 0
    while fx.update(1 / 60.0) and n < 600:
        n += 1
    check("impact fx selesai < 1 s", n < 60, "%d frame" % n)

    # 11. hit stop dalam rentang 0.03-0.08 s
    F.HITSTOP.frames = 0
    F.hit_stop(0.5)
    fr = F.HITSTOP.frames
    check("hit-stop dijepit <= 0.08 s", fr <= 5, "%d frame" % fr)
    F.HITSTOP.frames = 0
    F.hit_stop(0.001)
    check("hit-stop minimal >= 0.03 s", F.HITSTOP.frames >= 2,
          "%d frame" % F.HITSTOP.frames)
    frames = 0
    while F.should_freeze_frame():
        frames += 1
    check("hit-stop selalu habis", frames <= 5 and not F.HITSTOP.active,
          "%d frame beku" % frames)

    # 12. screen shake meredam
    F.SHAKE.shake_strength = 0.0
    F.SHAKE.shake_duration = 0.0
    F.SHAKE._max_duration = 0.0001
    F.SHAKE.add(10.0, 0.3)
    a0 = F.SHAKE.amount
    for _ in range(9):
        F.SHAKE.update(1 / 60.0)
    a1 = F.SHAKE.amount
    for _ in range(60):
        F.SHAKE.update(1 / 60.0)
    check("shake meredam bertahap lalu nol",
          a0 > a1 > 0 and F.SHAKE.amount == 0.0,
          "%.1f -> %.1f -> 0" % (a0, a1))

    # 13. skill fx lifecycle lengkap
    for k in "qwer":
        ps2 = F.ParticleSystem()
        fx = F.SkillFX(k, 100, 100, ps2)
        seen = set()
        n = 0
        while fx.update(1 / 60.0) and n < 1200:
            seen.add(fx.phase)
            n += 1
        check("skill %s: charge/release/area/impact/fade" % k.upper(),
              {"charge", "release", "area", "impact", "fade"} <= seen,
              sorted(seen))
        check("skill %s selesai (tidak abadi)" % k.upper(), n < 400,
              "%d frame" % n)

    # 14. animation controller
    h = fresh_hero(100, 100)
    seq = [0] * 2 + list(range(30, 0, -1)) + [0] * 3
    seen_phase = set()
    seen_state = set()
    for t in seq:
        h.timer = t
        Z._update_attack_anim(h)
        seen_phase.add(h._zp_attack_phase)
        seen_state.add(h._zp_state)
    check("controller melewati semua fase",
          {"ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW",
           "RECOVERY"} <= seen_phase, sorted(seen_phase))
    check("state machine: IDLE/CHARGE/SWING/ATTACK",
          {"IDLE", "CHARGE", "SWING", "ATTACK"} <= seen_state,
          sorted(seen_state))
    check("delta-time tersedia", hasattr(h, "_zp_dt") and 0 < h._zp_dt < 0.05,
          "%.4f" % h._zp_dt)

    # 15. hitbox hanya saat jendela aktif
    h.timer = 30
    Z._update_attack_anim(h)
    h._zp_attack_progress = 0.50
    h._zp_hit_active = True
    box = Z._swing_hitbox(h, 100, 100)
    check("hitbox ayunan ada saat aktif", box is not None and box.width > 30)
    h._zp_hit_active = False
    check("hitbox hilang di luar jendela",
          Z._swing_hitbox(h, 100, 100) is None)

    # 16. budget waktu
    hero = fresh_hero(300, 240)
    tgt3 = _ProbeEntity("dummy", 420, 240)
    tgt3.alive = True
    hero.target = tgt3
    d = F.director_for(hero)
    d.particles.clear()
    d.projectiles.clear()
    for _ in range(4):
        d.particles.burst(300, 240, 40)
        d.projectiles.spawn(300, 240, 420, 240, target=tgt3)
    d.impacts.append(F.ImpactFX(420, 240, 0.2, 1.6, True))
    d.skills.append(F.SkillFX("r", 300, 250, d.particles))
    canvas = pygame.Surface((900, 600), pygame.SRCALPHA)
    times = []
    for _ in range(40):
        canvas.fill((0, 0, 0, 0))
        t0 = time.perf_counter()
        d.update(1 / 60.0)
        d.draw_ground(canvas)
        d.draw_front(canvas)
        times.append((time.perf_counter() - t0) * 1000.0)
    times.sort()
    med = times[len(times) // 2]
    check("lapisan FX penuh < 3.5 ms", med < 3.5, "%.2f ms" % med)

    # 17. surface cache aktif
    before = F.cache_size()
    for _ in range(30):
        F.glow_surface(12, F.P["fx_mid"])
        F.ring_surface(20, 3, F.P["fx_light"])
        F.spark_surface(8, F.P["fx_hot"])
    check("surface glow/ring/spark di-cache",
          F.cache_size() - before <= 3,
          "+%d entri" % (F.cache_size() - before))

    # 18. kompatibilitas nama publik lama
    legacy = ("draw_zephyr", "draw_boss", "_draw_zephyr_idle",
              "_draw_zephyr_walk", "_draw_zephyr_attack",
              "_draw_zephyr_body", "_draw_zephyr_rig",
              "_draw_zephyr_elite", "_draw_zephyr_crown",
              "_draw_elite_wings", "_draw_elite_staff",
              "_draw_zephyr_masterwork_details", "_staff_tip_local",
              "_staff_orb_position", "_detect_moving",
              "_update_attack_anim", "_manage_projectiles",
              "_spawn_magic_bolt", "_spawn_casket",
              "MagicBoltProjectile", "CasketProjectile", "PALETTE",
              "SKILL_VISUAL_DURATION", "ATTACK_WINDUP_END",
              "ATTACK_SWING_END", "ATTACK_ARC_START", "ATTACK_ARC_SWEEP",
              "ATTACK_ARC_END")
    missing = [n for n in legacy if not hasattr(Z, n)]
    check("API lama utuh", not missing, missing or "28/28")

    # 19. palette karakter lengkap
    need = ("outline", "shadow", "dark", "body", "mid", "light",
            "highlight", "weapon", "fx")
    check("palette karakter lengkap",
          all(k in F.ZEPHYR_PALETTE for k in need))

    # 20. debug mode
    check("DEBUG_CHARACTER tersedia",
          hasattr(F, "DEBUG_CHARACTER") and hasattr(Z, "DEBUG_CHARACTER"))


def main():
    audit()
    print("\n=== PREVIEW SHEETS ===")
    sheet_swing()
    sheet_projectile()
    sheet_impact()
    sheet_skill()
    sheet_ingame()
    for n in ("swing_strip", "projectile", "impact", "skillfx", "ingame"):
        p = os.path.join(DOCS, "zephyr_v3_%s.png" % n)
        print("  docs/zephyr_v3_%s.png  (%d KB)" %
              (n, os.path.getsize(p) // 1024))
    print("\n=== HASIL: %d ok / %d gagal ===" % (OK, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
