#!/usr/bin/env python3
"""Audit terukur + lembar preview untuk GORNAK v3 (combat / game feel).

Memisahkan mana yang milik renderer (`bosses/level1.py::_NS_gornak`) dan
mana yang milik lapisan hidup (`heroes/gornak_fx.py`), lalu MENGUKUR
kontraknya: busur ayunan, trail dari histori bilah, lifecycle proyektil,
lifecycle skill FX, paket impact (flash/spark/debris/shake/hit-stop),
peluruhan efek (tidak ada yang abadi), ukuran cache, dan budget waktu.

Menghasilkan (di ``docs/``):
  gornak_v3_swing_strip.png  — 12 frame ayunan (badan + trail bilah hidup)
  gornak_v3_projectile.png   — bolt Mana Break: normal / crit / sudut
  gornak_v3_impact.png       — timeline impact FX (flash-shock-debris-spark)
  gornak_v3_skillfx.png      — lifecycle SkillFX Q/W/E/R
  gornak_v3_feel.png         — kurva hit-stop + peluruhan shake + timeline fase
  gornak_v3_ingame.png       — komposit arena: sprite cache + lapisan FX hidup
  gornak_v3_debug.png        — overlay DEBUG_CHARACTER (hitbox/hurtbox/state)

Jalankan:  python3 tools/_audit_gornak_v3.py
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import inspect                                            # noqa: E402
import math                                               # noqa: E402
import statistics                                         # noqa: E402
import pygame                                             # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                             # noqa: E402
from heroes import _ProbeEntity                           # noqa: E402
from heroes import combat_feel as FEEL                    # noqa: E402
from heroes import gornak_fx as F                          # noqa: E402
from bosses.level1 import _NS_gornak as G                  # noqa: E402

DOCS = os.path.join(ROOT, "docs")
BG = (20, 14, 28)
BG2 = (30, 20, 42)
OK = 0
FAIL = 0
DT = 1.0 / 60.0
COOLDOWN = 38                    # attack_cooldown di boss_data


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
        pygame.draw.line(s, (tint[0] + 5, tint[1] + 3, tint[2] + 6),
                         (0, y), (w, y))
    return s


def label(surf, text, x, y, col=(232, 206, 250)):
    font = pygame.font.Font(None, 17)
    surf.blit(font.render(text, True, col), (x, y))


def hero_at(x, y, **kw):
    h = _ProbeEntity("gornak", x, y)
    h.boss_type = "gornak"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 38
    h.timer = 0
    h.range = 60
    h.speed = 1.6
    h.hp = h.max_hp = 800
    h.radius = 16
    h.skill_damage = 180
    h.skill_range = 180
    h.hurt_flash_timer = 0
    h.blink_from_x = h.blink_from_y = 0
    h.mana_void_x = h.mana_void_y = 0
    for k, v in kw.items():
        setattr(h, k, v)
    return h


def manual_attack(h, progress):
    """Pose serangan yang digerakkan pemanggil (mode alat preview)."""
    h._gnk_attack_active = True
    h._gnk_attack_manual = True
    h._gnk_attack_progress = progress
    G._update_gnk_attack_anim(h)


def phase_name(ap):
    return G.attack_phase(ap)


# ───────────────────────────────────────────────────────────────────────────
# 1.  SWING STRIP — busur + trail dua bilah
# ───────────────────────────────────────────────────────────────────────────
def sheet_swing():
    cols, cw, ch = 6, 200, 250
    sheet = panel(cols * cw, ch * 2 + 26)
    label(sheet, "GORNAK v3 - SWING ARC + TRAIL DUA BILAH (anticipation - "
                 "windup - swing - impact - follow - recovery)", 8, 6)
    h = hero_at(120.0, 190.0)
    F.reset_all()
    F.attach(h)
    d = F.director_for(h)
    d.trail.reset()
    for i in range(12):
        ap = i / 11.0
        manual_attack(h, ap)
        h.pulse += 0.6
        F.tick(DT)
        cell = pygame.Surface((cw, ch), pygame.SRCALPHA)
        # draw_gornak pada lane boss sudah memanggil lapisan hidup
        # (ground + live) dari dalam -> tidak perlu digambar lagi di sini,
        # kalau dobel trail-nya terbaca dua kali lebih tebal.
        G.draw_gornak(cell, h, cw // 2, ch - 58)
        sheet.blit(cell, ((i % cols) * cw, 22 + (i // cols) * ch))
        label(sheet, "%.2f  %s  trail %d" % (ap, phase_name(ap),
              len(d.trail.points)), (i % cols) * cw + 6,
              24 + (i // cols) * ch)
    p = os.path.join(DOCS, "gornak_v3_swing_strip.png")
    pygame.image.save(sheet, p)
    F.reset_all()
    return p


# ───────────────────────────────────────────────────────────────────────────
# 2.  PROJECTILE — Mana Break
# ───────────────────────────────────────────────────────────────────────────
def sheet_projectile():
    sheet = panel(940, 330)
    label(sheet, "GORNAK v3 - PROJECTILE: core + glow + bentuk berarah + "
                 "rotasi + trail + partikel (bukan lingkaran polos)", 8, 6)
    for i in range(6):
        ang = i * math.pi / 3
        F.draw_mana_bolt(sheet, 90 + i * 150, 96, ang, age=i * 7)
        label(sheet, "%.0f deg" % math.degrees(ang), 66 + i * 150, 136)
    for i in range(6):
        ang = i * math.pi / 3
        F.draw_mana_bolt(sheet, 90 + i * 150, 200, ang, age=i * 7,
                         crit=True, radius=8.5)
    label(sheet, "CRIT (ramp kuning-putih + pecahan ekstra)", 8, 232)

    ps = F.ParticleSystem()
    sysm = F.ProjectileSystem(ps)
    pr = sysm.spawn(60, 300, 900, 288, speed=F.BOLT_SPEED, damage=0,
                    radius=7.0, kind="mana", particles=ps)
    for _ in range(26):
        sysm.update(DT)
        ps.update(DT)
    sysm.draw(sheet)
    ps.draw(sheet)
    label(sheet, "trail + after-image setelah 26 frame", 60, 318)
    p = os.path.join(DOCS, "gornak_v3_projectile.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 3.  IMPACT FX
# ───────────────────────────────────────────────────────────────────────────
def sheet_impact():
    sheet = panel(980, 240)
    label(sheet, "GORNAK v3 - IMPACT: flash + shockwave + slash fragment + "
                 "spark + debris  (t = 0.00 .. 0.30 s)", 8, 6)
    for i in range(6):
        x = 90 + i * 160
        fx = F.ImpactFX(x, 130, angle=-0.35, power=1.45, crit=(i % 3 == 2),
                        kind="blade", ground=34.0, seed=i)
        for _ in range(i * 3):
            fx.update(DT)
        fx.draw(sheet)
        label(sheet, "t=%.2fs" % (i * 3 * DT), x - 24, 200)
    p = os.path.join(DOCS, "gornak_v3_impact.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 4.  SKILL FX lifecycle
# ───────────────────────────────────────────────────────────────────────────
def sheet_skill():
    sheet = panel(980, 470)
    label(sheet, "GORNAK v3 - SKILL FX: CAST -> CHARGE -> RELEASE -> "
                 "TRAVEL/AREA -> IMPACT -> AFTER -> FADE", 8, 6)
    keys = ("q", "w", "e", "r")
    names = {"q": "Q Mana Break", "w": "W Blink", "e": "E Counterspell",
             "r": "R Mana Void"}
    for row, k in enumerate(keys):
        ps = F.ParticleSystem(140)
        total = F.SKILL_TOTAL[k]
        steps = 6
        for col in range(steps):
            fx = F.SkillFX(k, 90 + col * 150, 70 + row * 110, ps,
                           aim=(90 + col * 150 + 120, 66 + row * 110),
                           ground=26.0)
            t = total * (col + 0.5) / steps
            for _ in range(int(t / DT)):
                fx.update(DT)
                ps.update(DT)
            fx.draw_ground(sheet)
            fx.draw_front(sheet)
        label(sheet, "%s  (phase %s)" % (names[k], fx.phase),
              8, 52 + row * 110, F.GORNAK_PALETTE["fx_bright"][:3])
    p = os.path.join(DOCS, "gornak_v3_skillfx.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 5.  GAME FEEL — kurva hit-stop & peluruhan shake
# ───────────────────────────────────────────────────────────────────────────
def sheet_feel():
    W, H = 980, 300
    sheet = panel(W, H)
    label(sheet, "GORNAK v3 - GAME FEEL: hit-stop (bar) + peluruhan shake "
                 "(kurva) + timeline fase ayunan", 8, 6)
    # timeline fase
    t0 = 26
    for i in range(60):
        ph = phase_name(i / 60.0)
        col = {"ANTICIPATION": (86, 52, 120), "WINDUP": (120, 74, 168),
               "SWING": (236, 200, 92), "IMPACT": (255, 120, 60),
               "FOLLOW": (120, 74, 168), "RECOVERY": (60, 40, 84)}[ph]
        pygame.draw.rect(sheet, col, (16 + i * 15.4, t0, 15, 16))
    label(sheet, "1 siklus serangan 38 frame (kurva _attack_curve)",
          16, t0 + 20)

    # hit-stop: 1 bar per frame beku
    FEEL.reset()
    FEEL.hit_stop(0.07)
    y = 76
    frames = 0
    while FEEL.should_freeze_frame():
        frames += 1
    label(sheet, "hit-stop diminta 0.07s -> %d frame simulasi dibekukan "
                 "(cap %d); frame GAMBAR tetap jalan, FX melambat 0.18x"
          % (frames, FEEL.HITSTOP.MAX_FRAMES), 16, y, (255, 226, 150))
    for i in range(frames):
        pygame.draw.rect(sheet, (255, 150, 60), (16 + i * 22, y + 18, 20, 10))

    # kurva peluruhan shake (frame-based, seperti di bus)
    FEEL.reset()
    FEEL.SHAKE.enabled = True
    FEEL.shake(9.0, 0.34, forward_to_camera=False)
    pts = []
    for i in range(40):
        FEEL.SHAKE.update(DT)
        pts.append(FEEL.SHAKE.amount)
    ox, oy, sc = 16, 250, 4.6
    pygame.draw.line(sheet, (90, 70, 120), (ox, oy - 40), (ox + 40 * sc, oy))
    pygame.draw.line(sheet, (90, 70, 120), (ox, oy), (ox + 40 * sc, oy))
    for i in range(1, 40):
        pygame.draw.line(sheet, (200, 170, 255),
                         (ox + (i - 1) * sc, oy - int(pts[i - 1] * 4)),
                         (ox + i * sc, oy - int(pts[i] * 4)), 2)
    label(sheet, "shake 9.0/0.34s meluruh 0 dalam %d frame (nol = nol "
                 "betul, tidak ada ekor)" % next(
                     (i for i, v in enumerate(pts) if v <= 0.0), -1),
          240, oy - 40, (200, 170, 255))
    FEEL.reset()
    p = os.path.join(DOCS, "gornak_v3_feel.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 6.  IN-GAME: sprite cache + lapisan hidup
# ───────────────────────────────────────────────────────────────────────────
def sheet_ingame():
    PW, PH = 480, 320
    # momen dipilih dengan memperhitungkan kuantisasi cache lane hero
    # (pose maju tiap 2 frame di sana), jadi "SWING + TRAIL" jatuh di
    # frame tempat fase SWING benar-benar sudah tercatat controller.
    moments = ((18, "WINDUP"), (28, "SWING + TRAIL"),
               (36, "IMPACT + SHAKE"), (48, "AFTERMATH"))
    sheet = panel(PW * 2, PH * 2 + 26, (24, 18, 38))
    label(sheet, "GORNAK v3 - IN-GAME: sprite cache (lane hero) + lapisan FX "
                 "hidup 1:1 (ground / trail / bolt / impact)", 8, 6,
          (220, 255, 220))
    h = hero_at(150.0, 200.0, _render_scale=0.72)
    tgt = _ProbeEntity("dummy", 380.0, 196.0)
    tgt.alive = True
    tgt.radius = 18
    h.target = tgt
    F.reset_all()
    heroes.clear_hero_sprite_cache()
    F.attach(h)
    d = F.director_for(h)
    d.clear()

    # satu siklus penuh = cooldown 38 frame, timer turun -> controller
    # mendeteksi EDGE serangan dari sini (sama seperti game sebenarnya)
    seq = [0] * 2 + list(range(h.attack_cooldown, 0, -1))
    want = dict(moments)
    shots = {}
    for frame in range(56):
        h.timer = seq[frame % len(seq)]
        h.pulse += 0.06
        if frame == 26:
            d.spawn_mana_break(h.x, h.y, (tgt.x, tgt.y))
        if frame == 35:
            F.notify_melee_impact(h, tgt, 120, True)
        # Langkah FX eksplisit: tanpa ini, harness yang berputar lebih cepat
        # dari 1 ms membuat combat_feel.frame_dt() mengembalikan 0.0 (belum
        # ada frame acuan) dan trail tidak pernah tercatat.
        F.tick(DT)
        FEEL.frame_dt()
        cell = panel(PW, PH, (24, 18, 38))
        for i in range(170):
            pygame.draw.rect(cell, (32, 24, 48),
                             ((i * 97) % PW, (i * 53) % PH, 3, 2))
        pygame.draw.line(cell, (58, 44, 78), (0, 262), (PW, 262), 2)
        heroes.render_hero("gornak", cell, h, 150, 200)
        pygame.draw.circle(cell, (150, 60, 60), (int(tgt.x), int(tgt.y)),
                           18, 2)
        if frame in want:
            shots[frame] = (cell, dict(d.stats()))
    for idx, (frame, name) in enumerate(moments):
        cell, st = shots[frame]
        sheet.blit(cell, ((idx % 2) * PW, 22 + (idx // 2) * PH))
        label(sheet, "%s  | particles %d  trail %d  proj %d  impacts %d"
              % (name, st["particles"], st["trail"], st["projectiles"],
                 st["impacts"]),
              (idx % 2) * PW + 6, 26 + (idx // 2) * PH + PH - 14)
    p = os.path.join(DOCS, "gornak_v3_ingame.png")
    pygame.image.save(sheet, p)
    # aftermath: tidak boleh ada sisa efek
    for _ in range(420):
        h.timer = 0
        G._update_gnk_attack_anim(h)
        F.tick(DT)
    leftovers = F.total_particles()
    check("aftermath bersih (0 partikel setelah 420 frame)",
          leftovers == 0, "sisa %d" % leftovers)
    F.reset_all()
    heroes.clear_hero_sprite_cache()
    return p


# ───────────────────────────────────────────────────────────────────────────
# 7.  DEBUG OVERLAY
# ───────────────────────────────────────────────────────────────────────────
def sheet_debug():
    sheet = panel(560, 320, BG2)
    label(sheet, "GORNAK v3 - DEBUG_CHARACTER: hurtbox, jangkauan, hitbox "
                 "ayunan, proyektil, state/frame, FPS, partikel", 8, 6)
    before = G.DEBUG_CHARACTER
    G.DEBUG_CHARACTER = True
    try:
        h = hero_at(150.0, 210.0)
        manual_attack(h, 0.52)
        F.reset_all()
        F.attach(h)
        d = F.director_for(h)
        d.spawn_mana_break(h.x, h.y, (420.0, 200.0))
        for _ in range(4):
            F.tick(DT)
            G.draw_gornak(sheet, h, 150, 210)
        pygame.draw.rect(sheet, (70, 55, 90), (330, 90, 190, 130), 1)
        label(sheet, "lane BOSS: lapisan hidup ikut digambar (proyektil "
                     "dilingkari)", 330, 230, (200, 170, 255))
    finally:
        G.DEBUG_CHARACTER = before
    F.reset_all()
    p = os.path.join(DOCS, "gornak_v3_debug.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# AUDIT
# ───────────────────────────────────────────────────────────────────────────
def audit():
    print("\n=== GORNAK v3 AUDIT (combat / game feel) ===\n")

    # 1. prosedural murni
    src = inspect.getsource(F)
    src_g = inspect.getsource(G)
    banned = ("pygame.image.load", "image.load(", "load_extended",
              "pygame.image.frombytes(", "fromstring(", "array")
    hits = [b for b in banned if b in src or b in src_g]
    check("tanpa asset eksternal", not hits, hits or "0 pemanggilan")

    # 2. palet
    need = ("outline", "shadow", "dark", "body", "mid", "light", "highlight",
            "weapon", "fx")
    check("palet lengkap", all(k in F.GORNAK_PALETTE for k in need),
          "%d kunci" % len(F.GORNAK_PALETTE))
    drift = [dst for dst, src in sorted(F._PALETTE_SYNC.items())
             if src in G.PALETTE
             and tuple(F.P[dst][:3]) != tuple(G.PALETTE[src][:3])]
    check("palet lapisan hidup = palet renderer (tanpa drift)", not drift,
          "sinkron %d/%d kunci" % (len(F._PALETTE_SYNC) - len(drift),
                                   len(F._PALETTE_SYNC)))

    # 3. fase ayunan
    ph = [phase_name(i / 120.0) for i in range(121)]
    uniq = []
    for p in ph:
        if not uniq or uniq[-1] != p:
            uniq.append(p)
    check("6 fase hadir & berurutan", uniq == list(G.attack_phases_order()),
          " ".join(uniq))

    # 4. busur, bukan lerp
    n = 40
    pts = [pygame.Vector2(G._tip_local("attack", 0.0, G._attack_curve(
        i / float(n)))) for i in range(n + 1)]
    a, b = pts[0], pts[-1]
    dev = max((p - a.lerp(b, i / float(n))).length() for i, p in enumerate(pts))
    check("bilah bergerak di busur (deviasi > 20 px)", dev > 20,
          "%.1f px" % dev)
    steps = [(q - p).length() for p, q in zip(pts, pts[1:])]
    jump = max(steps)
    pop = max((steps[i] - 3.0 * steps[i - 1]) for i in range(1, len(steps)))
    check("tidak ada pop satu-frame dari pose tahan", pop < 8.0,
          "max step %.1f px, loncatan terbesar +%.1f" % (jump, pop))

    # 5. jendela hit
    lo, hi = G.ATTACK_ACTIVE_WINDOW
    check("jendela hit di tengah ayunan", 0.3 < lo < hi < 0.72,
          "%.2f..%.2f" % (lo, hi))
    h = hero_at(0.0, 0.0)
    snaps = []
    h._gnk_previous_timer = 0
    for step in range(COOLDOWN, -1, -1):
        h.timer = step
        G._update_gnk_attack_anim(h)
        snaps.append((bool(h._gnk_hit_active), h._gnk_attack_phase,
                      h._gnk_state, h._gnk_attack_progress))
    check("state machine menghasilkan SWING", "SWING" in {s[2] for s in snaps},
          " ".join(sorted({s[2] for s in snaps})))
    on = [s for s in snaps if s[0]]
    lo, hi = G.ATTACK_ACTIVE_WINDOW
    check("hit aktif hanya di dalam jendela",
          bool(on) and all(lo - 1e-6 <= s[3] < hi + 1e-6 and
                           s[1] in ("SWING", "IMPACT", "FOLLOW") for s in on),
          "%d frame, progress %.2f..%.2f" % (
              len(on), min(s[3] for s in on), max(s[3] for s in on))
          if on else "tidak ada frame hit")
    check("hit window ditutup sebelum recovery",
          all(s[1] != "RECOVERY" for s in on))

    # 6. controller: dt & nama lama
    h2 = hero_at(0.0, 0.0)
    G._update_gnk_attack_anim(h2)
    old = ("_gnk_attack_active", "_gnk_attack_frame", "_gnk_attack_progress",
           "_gnk_previous_timer")
    check("atribut lama tetap diisi", all(hasattr(h2, o) for o in old),
          ", ".join(o.lstrip("_") for o in old))
    check("delta-time tersedia untuk FX", 0.0 < h2._gnk_dt <= 0.05,
          "%.4f s" % h2._gnk_dt)

    # 7. trail
    trail = F.SwingTrail()
    for i in range(F.TRAIL_SAMPLES + 6):
        trail.push(pygame.Vector2(10 + i, 20), pygame.Vector2(40 + i, 5),
                   pygame.Vector2(6 - i, 22), pygame.Vector2(-24 - i, 8))
        trail.update(DT)
    check("trail dibatasi TRAIL_SAMPLES", len(trail.points) <= F.TRAIL_SAMPLES,
          "%d sampel" % len(trail.points))
    for _ in range(40):
        trail.update(DT)
    check("trail meluruh habis", not trail.points)

    # 8. particle bounds
    ps = F.ParticleSystem(F.MAX_PARTICLES)
    for i in range(900):
        ps.spawn(0.0, 0.0, 1.0, 1.0, 0.4, 2, F.P["fx_light"])
    check("cap partikel dihormati", ps.count() <= F.MAX_PARTICLES,
          "%d / %d (drop %d)" % (ps.count(), F.MAX_PARTICLES, ps.dropped))
    for _ in range(60):
        ps.update(DT)
    check("partikel habis (tidak abadi)", ps.count() == 0)

    # 9. projectile lifecycle
    h3 = hero_at(200.0, 200.0, target=hero_at(500.0, 198.0))
    h3.target.alive = True
    F.reset_all()
    F.attach(h3)
    d3 = F.director_for(h3)
    g, tip = F.blade_points(h3, h3.x, h3.y, False)
    pr = d3.spawn_mana_break(h3.x, h3.y, (h3.target.x, h3.target.y))
    check("bolt lahir di ujung bilah",
          pr is not None and (pygame.Vector2(pr.spawn_pos) - tip).length()
          <= 10.0, "dist %.1f px" % (
              (pygame.Vector2(pr.spawn_pos) - tip).length()))
    states = {pr.state}
    for _ in range(140):
        d3.update(DT, h3.x, h3.y)
        if d3.projectiles.count():
            states.add(d3.projectiles.list()[0].state)
    check("lifecycle travel -> impact -> mati",
          pr.STATE_TRAVEL in states and d3.projectiles.count() == 0,
          " ".join(sorted(states)))
    check("damage proyektil visual = 0 (damage tetap milik skill system)",
          pr.damage == 0)

    # 10. skill lifecycle
    for k in ("q", "w", "e", "r"):
        h4 = hero_at(200.0, 200.0)
        F.attach(h4)
        d4 = F.director_for(h4)
        d4.on_cast(200.0, 200.0, k)
        for _ in range(int(F.SKILL_TOTAL[k] / DT) + 40):
            d4.update(DT, 200.0, 200.0)
        check("SkillFX %s dibuang setelah lifecycle" % k, not d4.skills)
    F.reset_all()

    # 11. pusat R di pusat void, bukan di badan
    h5 = hero_at(300.0, 200.0)
    F.attach(h5)
    d5 = F.director_for(h5)
    h5.active_skill, h5.active_skill_timer = "r", 90
    h5.mana_void_x, h5.mana_void_y = 210.0, 250.0
    for i in range(60):
        h5.active_skill_timer = 90 - i
        F.tick(DT)
    check("impact R memakai pusat AOE dunia",
          d5.void_screen is not None
          and abs(d5.void_screen[0] - (300.0 + 210.0 - 300.0)) < 2.0,
          str(d5.void_screen))
    F.reset_all()

    # 12. impact -> hit-stop dalam rentang master prompt
    h6 = hero_at(200.0, 200.0, target=hero_at(320.0, 198.0))
    h6.target.alive = True
    F.attach(h6)
    d6 = F.director_for(h6)
    FEEL.reset()
    F.notify_melee_impact(h6, h6.target, 140, True)
    frames = FEEL.HITSTOP.total
    check("hit-stop terkuantisasi 2..5 frame (= 0.033-0.083 s)",
          2 <= frames <= FEEL.HITSTOP.MAX_FRAMES, "%d frame" % frames)
    check("permintaan berlebihan diklem ke MAX_SECONDS",
          (FEEL.reset(), FEEL.hit_stop(9.0), FEEL.HITSTOP.total
           <= FEEL.HITSTOP.MAX_FRAMES)[2],
          "MAX_SECONDS = %.2f s" % FEEL.HITSTOP.MAX_SECONDS)
    FEEL.reset()
    check("permintaan sangat kecil tetap 2 frame (terasa)",
          (FEEL.hit_stop(0.0001), FEEL.HITSTOP.total >= 2)[1],
          "%d frame" % FEEL.HITSTOP.total)
    check("impact memicu paket feedback (flash+shock+spark+debris)",
          len(d6.impacts) == 1 and d6.particles.count() > 12,
          "impacts %d, partikel %d" % (len(d6.impacts),
                                       d6.particles.count()))
    FEEL.reset()
    F.reset_all()

    # 13. shake selalu terkuras & sekali per frame
    FEEL.SHAKE.enabled = True
    F.shake(8.0, 0.3)
    for _ in range(60):
        FEEL.SHAKE.update(DT)
    check("shake kembali ke 0", FEEL.SHAKE.amount == 0.0)
    FEEL.reset()

    # 14. bus dibagikan (Zephyr & Gornak)
    from heroes import zephyr_fx as ZF
    check("satu bus hit-stop/shake untuk semua karakter",
          ZF.HITSTOP is FEEL.HITSTOP and ZF.SHAKE is FEEL.SHAKE)
    core = open(os.path.join(ROOT, "_core.py"), encoding="utf-8").read()
    i = core.index("HIT STOP (game feel)")
    gate = core[i:i + 700]
    check("Game.update membekukan lewat bus SHARED",
          "combat_feel" in gate and "zephyr_fx" not in gate,
          "gate: heroes.combat_feel.should_freeze_frame()")

    # 15. supresi ganda di lane boss
    calls = {"c": 0, "g": 0, "p": 0}
    rc, rg = G._draw_crescent_slash, G._draw_manabreak_ground
    rp = G._draw_manabreak_foreground
    G._draw_crescent_slash = staticmethod(
        lambda *a, **k: calls.__setitem__("c", calls["c"] + 1))
    G._draw_manabreak_ground = staticmethod(
        lambda *a, **k: calls.__setitem__("g", calls["g"] + 1))
    G._draw_manabreak_foreground = staticmethod(
        lambda *a, **k: calls.__setitem__("p", calls["p"] + 1))
    try:
        surf = pygame.Surface((240, 240), pygame.SRCALPHA)
        # (a) ayunan murni: pita harus diambil alih lapisan hidup
        ha = hero_at(120.0, 190.0)
        manual_attack(ha, 0.5)
        F.reset_all()
        G.draw_gornak(surf, ha, 120, 190)
        check("pita ayunan TIDAK digambar 2x di lane boss",
              calls["c"] == 0 and F.owns(ha),
              "renderer %d kali, lapisan hidup ambil alih" % calls["c"])
        # (b) cast Q: telegraph tanah tetap milik renderer, proc foreground
        #     digantikan bolt hidup
        hq = hero_at(120.0, 190.0, active_skill="q", active_skill_timer=30)
        G.draw_gornak(surf, hq, 120, 190)
        check("telegraph tanah TETAP digambar renderer", calls["g"] == 1)
        check("proc foreground di-canvas digantikan bolt hidup",
              calls["p"] == 0)
        # (c) fallback: modul FX tidak tersedia -> renderer gambar sendiri
        lm, G._LIVE_MOD = G._LIVE_MOD, False
        calls["c"] = calls["p"] = calls["g"] = 0
        G.draw_gornak(surf, ha, 120, 190)
        G.draw_gornak(surf, hq, 120, 190)
        check("fallback canvas aktif saat modul FX absen",
              calls["c"] == 1 and calls["p"] == 1 and calls["g"] == 1,
              "crescent %d, proc %d, ground %d"
              % (calls["c"], calls["p"], calls["g"]))
        G._LIVE_MOD = lm
    finally:
        G._draw_crescent_slash, G._draw_manabreak_ground = rc, rg
        G._draw_manabreak_foreground = rp
    F.reset_all()

    # 16. render order lapisan (ground -> sprite -> live)
    h8 = hero_at(140.0, 200.0)
    F.attach(h8)
    d8 = F.director_for(h8)
    for i in range(10):
        manual_attack(h8, 0.32 + i * 0.03)
        F.tick(DT)
    ground = pygame.Surface((280, 280), pygame.SRCALPHA)
    F.draw_ground_layer(ground, h8, 140, 200)
    live = pygame.Surface((280, 280), pygame.SRCALPHA)
    F.draw_live_layer(live, h8, 140, 200)
    check("ground layer & live layer keduanya berisi",
          ground.get_bounding_rect(min_alpha=4).width > 0
          and live.get_bounding_rect(min_alpha=4).width > 0,
          "ground %s / live %s" % (ground.get_bounding_rect(min_alpha=4),
                                    live.get_bounding_rect(min_alpha=4)))
    F.reset_all()

    # 17. budget waktu
    def bench(h, n=40):
        surf = pygame.Surface((640, 400), pygame.SRCALPHA)
        runs = []
        for _ in range(5):
            t0 = time.perf_counter()
            for i in range(n):
                manual_attack(h, (i % COOLDOWN) / float(COOLDOWN))
                h.pulse += 0.2
                F.tick(DT)
                surf.fill((0, 0, 0, 0))
                F.draw_ground_layer(surf, h, h.x, h.y)
                G.draw_gornak(surf, h, 120, 200)
                F.draw_live_layer(surf, h, 120, 200)
            runs.append((time.perf_counter() - t0) / n * 1000)
        return statistics.median(runs)

    h9 = hero_at(120.0, 200.0, target=hero_at(320.0, 198.0))
    h9.target.alive = True
    F.reset_all()
    F.attach(h9)
    d9 = F.director_for(h9)
    bench(h9)                                   # warm-up cache
    for i in range(10):
        F.notify_melee_impact(h9, h9.target, 120, True)
        F.tick(DT)
    ms = bench(h9)
    check("satu frame penuh (renderer + live FX) < 5 ms", ms < 5.0,
          "%.2f ms (median)" % ms)
    check("cache surface di bawah batas", F.cache_size() <= F._SURF_CACHE_MAX,
          "%d / %d entri" % (F.cache_size(), F._SURF_CACHE_MAX))
    check("partikel dalam cap saat ramai",
          F.total_particles() <= F.MAX_PARTICLES, "%d" % F.total_particles())
    F.reset_all()

    # 18. API lama renderer utuh
    legacy = ("draw_gornak", "_draw_gnk_rig", "_draw_gnk_rig_at",
              "_draw_gnk_legs", "_draw_gnk_torso", "_draw_gnk_head",
              "_draw_gnk_arm", "_draw_gnk_arm_back" if hasattr(
                  G, "_draw_gnk_arm_back") else "_draw_gnk_arm",
              "_draw_gnk_blade", "_draw_gnk_masterwork_details",
              "_draw_gnk_idle", "_draw_gnk_walk", "_draw_gnk_attack",
              "_draw_gnk_blink", "_draw_gnk_cape_back", "_draw_gnk_pauldrons",
              "_draw_gnk_belt", "_draw_gnk_weave", "_draw_gnk_rimlight",
              "_draw_crescent_slash", "_draw_manabreak_ground",
              "_draw_manabreak_foreground", "_draw_cast_shockwave",
              "_draw_footfall_dust", "_draw_anti_magic_field",
              "_draw_ground_rune", "_draw_blink_ground",
              "_draw_counterspell_foreground", "_draw_manavoid_ground",
              "_draw_manavoid_foreground", "_draw_shadow", "_resolve_pose",
              "_update_gnk_attack_anim", "_skill_progress",
              "_target_position", "_detect_moving", "_attack_curve",
              "_blade_angle", "_arm_chain", "_elbow", "_blade_len",
              "_head_bob", "_rig_shift", "_tip_local", "_tip_screen",
              "_front_grip_local", "_back_grip_local", "_local_to_screen",
              "_arcane_seal", "_seal_plate", "_compose_outline", "_fx_scale",
              "_ring_r", "PALETTE", "SKILL_DUR", "ACTIONS", "ANIM_STATES",
              "ATTACK_PHASES", "ATTACK_ACTIVE_WINDOW", "DEBUG_CHARACTER",
              "live_fx_ready", "GROUND_DY", "FEET_DY", "RIG_W", "RIG_H",
              "SCALE")
    missing = [n for n in legacy if not hasattr(G, n)]
    check("API renderer lama utuh", not missing, missing or
          "%d/%d" % (len(legacy), len(legacy)))

    # 19. debug mode
    check("DEBUG_CHARACTER ada & mati secara default",
          G.DEBUG_CHARACTER is False and F.DEBUG_CHARACTER is False)
    dbg = inspect.getsource(G._draw_gnk_debug)
    check("overlay debug lengkap (hitbox/hurtbox/range/state/FPS/partikel)",
          all(t in dbg for t in ("_swing_hitbox", "radius", "range",
                                 "_gnk_state", "fps", "particles")))

    # 20. integrasi engine
    ent = open(os.path.join(ROOT, "_entity.py"), encoding="utf-8").read()
    bb = open(os.path.join(ROOT, "bosses", "base_boss.py"),
              encoding="utf-8").read()
    check("Hero._do_attack -> notify_melee_impact (gornak saja)",
          "gornak_fx.notify_melee_impact" in ent.replace("as _gfx\n", "")
          or "_gfx.notify_melee_impact" in ent)
    check("Boss melee -> notify_melee_impact (boss_type gornak)",
          "_gfx.notify_melee_impact" in bb)
    init = open(os.path.join(ROOT, "heroes", "__init__.py"),
                encoding="utf-8").read()
    check("gornak terdaftar di _LIVE_FX_HEROES",
          '"gornak"' in init.split("_LIVE_FX_HEROES")[1][:60])


def main():
    audit()
    print("\n=== PREVIEW SHEETS ===")
    outs = [sheet_swing(), sheet_projectile(), sheet_impact(),
            sheet_skill(), sheet_feel(), sheet_ingame(), sheet_debug()]
    for p in outs:
        print("  %-44s %4d KB" % (os.path.basename(p),
                                  os.path.getsize(p) // 1024))
    print("\n=== HASIL: %d ok / %d gagal ===" % (OK, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
