#!/usr/bin/env python3
"""Audit terukur + lembar preview untuk RAZAK v3 (combat / game feel).

Memisahkan mana yang milik renderer (`bosses/level2.py::_NS_razak`) dan
mana yang milik lapisan hidup (`heroes/razak_fx.py`), lalu MENGUKUR
kontraknya: busur machete api, trail dari histori bilah, lifecycle
molotov napalm, lifecycle SkillFX Q/W/E/R, paket impact
(flash/spark/debris/shake/hit-stop), peluruhan efek (tidak ada yang
abadi), supresi ganda renderer/lapisan hidup, ukuran cache, dan budget
waktu.

Menghasilkan (di ``docs/``):
  razak_v3_swing_strip.png  — 12 frame ayunan (badan + trail api hidup)
  razak_v3_projectile.png   — molotov napalm: travel / trail / arc
  razak_v3_impact.png       — timeline impact FX (flash-shock-debris-spark)
  razak_v3_skillfx.png      — lifecycle SkillFX Q/W/E/R
  razak_v3_feel.png         — kurva hit-stop + peluruhan shake + timeline fase
  razak_v3_ingame.png       — komposit arena: sprite cache + lapisan FX hidup
  razak_v3_debug.png        — overlay DEBUG_CHARACTER (hitbox/hurtbox/state)

Jalankan:  python3 tools/_audit_razak_v3.py
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
from heroes import razak_fx as F                          # noqa: E402
from bosses.level2 import _NS_razak as G                  # noqa: E402

DOCS = os.path.join(ROOT, "docs")
BG = (24, 14, 16)
BG2 = (36, 20, 22)
OK = 0
FAIL = 0
DT = 1.0 / 60.0
COOLDOWN = 45                    # attack_cooldown razak di boss_data.py


# ───────────────────────────────────────────────────────────────────────────
# helper
# ───────────────────────────────────────────────────────────────────────────
def check(label, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1
        print("  [ok]   %-46s %s" % (label, detail))
    else:
        FAIL += 1
        print("  [FAIL] %-46s %s" % (label, detail))


def panel(w, h, tint=BG):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(tint)
    return s


def label(surf, text, x, y, col=(244, 216, 150)):
    font = pygame.font.Font(None, 16)
    img = font.render(text, True, col)
    surf.blit(img, (x, y))


def hero_at(x, y, **kw):
    h = _ProbeEntity("razak", x, y)
    h.boss_type = "razak"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = COOLDOWN
    h.timer = 0
    h.range = 130
    h.speed = 1.6
    h.hp = h.max_hp = 2800
    h.radius = 18
    h.skill_damage = 180
    h.skill_range = 220
    h.hurt_flash_timer = 0
    h._razak_moving = False
    for k, v in kw.items():
        setattr(h, k, v)
    return h


def manual_attack(h, progress):
    """Pose serangan yang digerakkan pemanggil (mode alat preview)."""
    h._razak_attack_active = True
    h._razak_attack_frame = int(progress * (COOLDOWN - 1))
    h._razak_attack_progress = min(1.0, max(0.0, float(progress)))
    h._razak_attack_phase = G.attack_phase(h._razak_attack_progress)


def phase_name(ap):
    return G.attack_phase(ap)


# ───────────────────────────────────────────────────────────────────────────
# 1.  SWING STRIP — busur + trail
# ───────────────────────────────────────────────────────────────────────────
def sheet_swing():
    cols, cw, ch = 6, 210, 250
    sheet = panel(cols * cw, ch * 2 + 26)
    label(sheet, "RAZAK v3 - SWING ARC + TRAIL API (anticipation - windup - "
                 "swing - impact - follow - recovery)", 8, 6)
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
        # draw_razak pada lane boss sudah memanggil lapisan hidup
        # (ground + live) dari dalam -> tidak perlu digambar lagi di sini,
        # kalau dobel trail-nya terbaca dua kali lebih tebal.
        G.draw_razak(cell, h, cw // 2, ch - 58)
        sheet.blit(cell, ((i % cols) * cw, 22 + (i // cols) * ch))
        label(sheet, "%.2f  %s  trail %d" % (ap, phase_name(ap),
              len(d.trail.samples)), (i % cols) * cw + 6,
              24 + (i // cols) * ch)
    p = os.path.join(DOCS, "razak_v3_swing_strip.png")
    pygame.image.save(sheet, p)
    F.reset_all()
    return p


# ───────────────────────────────────────────────────────────────────────────
# 2.  PROJECTILE — molotov napalm
# ───────────────────────────────────────────────────────────────────────────
def sheet_projectile():
    sheet = panel(980, 340)
    label(sheet, "RAZAK v3 - PROJECTILE: botol kuningan berputar + sumbu "
                 "menyala + trail asap->api + arc parabolik", 8, 6)
    ps = F.ParticleSystem()
    sysm = F.ProjectileSystem(ps, cap=6)
    pr = sysm.spawn(60, 300, 900, 280, speed=F.NAPALM_SPEED, damage=0,
                    radius=8.0, kind="napalm", particles=ps,
                    arc_height=F.NAPALM_ARC)
    for _ in range(26):
        sysm.update(DT)
        ps.update(DT)
    sysm.draw(sheet)
    ps.draw(sheet)
    label(sheet, "travel + trail setelah 26 frame (arc %.0f px)"
          % F.NAPALM_ARC, 60, 320)

    # tiga fase: spawn / mid / near-hit
    for i, t in enumerate((4, 12, 22)):
        ps2 = F.ParticleSystem()
        sysm2 = F.ProjectileSystem(ps2, cap=3)
        pr2 = sysm2.spawn(150 + i * 280, 60, 250 + i * 280, 120,
                          speed=F.NAPALM_SPEED, damage=0,
                          radius=8.0, kind="napalm", particles=ps2,
                          arc_height=F.NAPALM_ARC)
        for _ in range(t):
            sysm2.update(DT)
            ps2.update(DT)
        sysm2.draw(sheet)
        ps2.draw(sheet)
        label(sheet, "t=%d frame state=%s" % (t, pr2.state),
              130 + i * 280, 150)
    p = os.path.join(DOCS, "razak_v3_projectile.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 3.  IMPACT FX
# ───────────────────────────────────────────────────────────────────────────
def sheet_impact():
    sheet = panel(980, 240)
    label(sheet, "RAZAK v3 - IMPACT: flash + shockwave + slash fragment + "
                 "spark + debris  (t = 0.00 .. 0.30 s)", 8, 6)
    for i in range(6):
        x = 90 + i * 160
        fx = F.ImpactFX(x, 130, angle=-0.25, power=1.45, crit=(i % 3 == 2),
                        kind="slash", ground=52.0, seed=i)
        for _ in range(i * 3):
            fx.update(DT)
        fx.draw(sheet)
        label(sheet, "t=%.2fs" % (i * 3 * DT), x - 24, 190)
    p = os.path.join(DOCS, "razak_v3_impact.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 4.  SKILL FX lifecycle
# ───────────────────────────────────────────────────────────────────────────
def sheet_skill():
    sheet = panel(980, 470)
    label(sheet, "RAZAK v3 - SKILL FX: CAST -> CHARGE -> RELEASE -> "
                 "TRAVEL/AREA -> IMPACT -> FADE", 8, 6)
    keys = ("q", "w", "e", "r")
    names = {"q": "Q Sticky Napalm", "w": "W Flamebreak",
             "e": "E Firefly Dash", "r": "R Firestorm"}
    for row, k in enumerate(keys):
        ps = F.ParticleSystem(140)
        total = F.SKILL_TOTAL[k]
        steps = 6
        for col in range(steps):
            fx = F.SkillFX(k, 90 + col * 150, 70 + row * 110, ps,
                           aim=(90 + col * 150 + 120, 66 + row * 110),
                           ground=52.0)
            t = total * (col + 0.5) / steps
            for _ in range(int(t / DT)):
                fx.update(DT)
                ps.update(DT)
            fx.draw_ground(sheet)
            fx.draw_front(sheet)
        label(sheet, "%s  (phase %s)" % (names[k], fx.phase),
              8, 52 + row * 110, F.RAZAK_PALETTE["fire_glow"][:3])
    p = os.path.join(DOCS, "razak_v3_skillfx.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 5.  GAME FEEL — kurva hit-stop & peluruhan shake
# ───────────────────────────────────────────────────────────────────────────
def sheet_feel():
    W, H = 980, 300
    sheet = panel(W, H)
    label(sheet, "RAZAK v3 - GAME FEEL: hit-stop (bar) + peluruhan shake "
                 "(kurva) + timeline fase ayunan", 8, 6)
    # timeline fase (60 sample 0..1)
    t0 = 26
    for i in range(60):
        ph = phase_name(i / 60.0)
        col = {"ANTICIPATION": (86, 40, 24), "WINDUP": (140, 60, 16),
               "SWING": (236, 150, 40), "IMPACT": (255, 90, 30),
               "FOLLOW": (140, 60, 16), "RECOVERY": (60, 28, 16)}[ph]
        pygame.draw.rect(sheet, col, (16 + i * 15.4, t0, 15, 16))
    label(sheet, "1 siklus serangan %d frame (keyframe _attack_pose)"
          % COOLDOWN, 16, t0 + 20)

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
    pygame.draw.line(sheet, (90, 50, 60), (ox, oy - 40), (ox + 40 * sc, oy))
    pygame.draw.line(sheet, (90, 50, 60), (ox, oy), (ox + 40 * sc, oy))
    for i in range(1, 40):
        pygame.draw.line(sheet, (255, 170, 120),
                         (ox + (i - 1) * sc, oy - int(pts[i - 1] * 4)),
                         (ox + i * sc, oy - int(pts[i] * 4)), 2)
    label(sheet, "shake 9.0/0.34s meluruh 0 dalam %d frame (nol = nol "
                 "betul, tidak ada ekor)" % next(
                     (i for i, v in enumerate(pts) if v <= 0.0), -1),
          240, oy - 40, (255, 170, 120))
    FEEL.reset()
    p = os.path.join(DOCS, "razak_v3_feel.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# 6.  IN-GAME: sprite cache + lapisan hidup
# ───────────────────────────────────────────────────────────────────────────
def sheet_ingame():
    PW, PH = 480, 320
    moments = ((18, "WINDUP"), (28, "SWING + TRAIL"),
               (36, "IMPACT + SHAKE"), (50, "AFTERMATH"))
    sheet = panel(PW * 2, PH * 2 + 26, (28, 18, 20))
    label(sheet, "RAZAK v3 - IN-GAME: sprite cache (lane hero) + lapisan FX "
                 "hidup 1:1 (ground / trail / napalm / impact)", 8, 6,
          (244, 216, 150))
    h = hero_at(150.0, 200.0, _render_scale=0.75)
    tgt = _ProbeEntity("dummy", 390.0, 198.0)
    tgt.alive = True
    tgt.radius = 16
    h.target = tgt
    F.reset_all()
    heroes.clear_hero_sprite_cache()
    F.attach(h)
    d = F.director_for(h)
    d.clear()

    # satu siklus penuh = cooldown 45 frame, timer turun -> controller
    # mendeteksi EDGE serangan dari sini (sama seperti game sebenarnya)
    seq = [0] * 2 + list(range(h.attack_cooldown, 0, -1))
    want = dict(moments)
    shots = {}
    for frame in range(64):
        h.timer = seq[frame % len(seq)]
        h.pulse += 0.06
        if frame == 26:
            F.notify_skill_cast(h, "w")
        if frame == 35:
            F.notify_melee_impact(h, tgt, 140, True)
        F.tick(DT)
        FEEL.frame_dt()
        cell = panel(PW, PH, (28, 18, 20))
        for i in range(170):
            pygame.draw.rect(cell, (40, 26, 30),
                             ((i * 97) % PW, (i * 53) % PH, 3, 2))
        pygame.draw.line(cell, (66, 40, 46), (0, 262), (PW, 262), 2)
        heroes.render_hero("razak", cell, h, 150, 200)
        pygame.draw.circle(cell, (190, 80, 70), (int(tgt.x), int(tgt.y)),
                           16, 2)
        if frame in want:
            shots[frame] = (cell, dict(d.stats()))
    for idx, (frame, name) in enumerate(moments):
        cell, st = shots[frame]
        sheet.blit(cell, ((idx % 2) * PW, 22 + (idx // 2) * PH))
        label(sheet, "%s  | particles %d  trail %d  proj %d  impacts %d"
              % (name, st["particles"], st["trail"], st["projectiles"],
                 st["impacts"]),
              (idx % 2) * PW + 6, 26 + (idx // 2) * PH + PH - 14)
    p = os.path.join(DOCS, "razak_v3_ingame.png")
    pygame.image.save(sheet, p)
    # aftermath: tidak boleh ada sisa efek
    for _ in range(420):
        h.timer = 0
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
    label(sheet, "RAZAK v3 - DEBUG_CHARACTER: hurtbox, jangkauan, hitbox "
                 "ayunan, proyektil, state/frame, FPS, partikel", 8, 6)
    before = F.DEBUG_CHARACTER
    F.DEBUG_CHARACTER = True
    try:
        h = hero_at(150.0, 210.0)
        manual_attack(h, 0.52)
        F.reset_all()
        F.attach(h)
        d = F.director_for(h)
        d.spawn_napalm(230.0, 200.0, 430.0, 196.0)
        for _ in range(4):
            F.tick(DT)
            G.draw_razak(sheet, h, 150, 210)
        label(sheet, "lane BOSS: lapisan hidup ikut digambar (proyektil "
                     "dilingkari)", 330, 230, (200, 170, 255))
    finally:
        F.DEBUG_CHARACTER = before
    F.reset_all()
    p = os.path.join(DOCS, "razak_v3_debug.png")
    pygame.image.save(sheet, p)
    return p


# ───────────────────────────────────────────────────────────────────────────
# AUDIT
# ───────────────────────────────────────────────────────────────────────────
def audit():
    print("\n=== RAZAK v3 AUDIT (combat / game feel) ===\n")

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
    check("palet lengkap", all(k in F.RAZAK_PALETTE for k in need),
          "%d kunci" % len(F.RAZAK_PALETTE))
    F._sync_palette()
    drift = [dst for dst, src in sorted(F._PALETTE_SYNC.items())
             if src in G.PALETTE
             and tuple(F.P[dst][:3]) != tuple(G.PALETTE[src][:3])]
    check("palet lapisan hidup = palet renderer (tanpa drift)", not drift,
          "sinkron %d/%d kunci" % (len(F._PALETTE_SYNC) - len(drift),
                                   len(F._PALETTE_SYNC)))

    # 3. fase ayunan
    uniq = []
    for i in range(121):
        p = phase_name(i / 120.0)
        if not uniq or uniq[-1] != p:
            uniq.append(p)
    check("6 fase hadir & berurutan",
          uniq == [n for n, _a, _b in G.ATTACK_PHASES], " ".join(uniq))

    # 4. busur, bukan lerp — ujung bilah bergerak di busur > 12 px
    n = 40
    pts = [pygame.Vector2(G._machete_tip_local("attack", 0.0,
                                               i / float(n), 1))
           for i in range(n + 1)]
    a, b = pts[0], pts[-1]
    dev = max((p - a.lerp(b, i / float(n))).length()
              for i, p in enumerate(pts))
    check("bilah bergerak di busur (deviasi > 12 px)", dev > 12,
          "%.1f px" % dev)
    steps = [(q - p).length() for p, q in zip(pts, pts[1:])]
    jump = max(steps)
    pop = max((steps[i] - 3.0 * steps[i - 1])
              for i in range(1, len(steps)))
    check("tidak ada pop satu-frame dari pose tahan", pop < 8.0,
          "max step %.1f px, loncatan terbesar +%.1f" % (jump, pop))

    # 5. jendela hit & hitbox
    h = hero_at(0.0, 0.0)
    h._razak_attack_active = True
    h._razak_attack_progress = 0.5
    hb = G._swing_hitbox(h, h.x, h.y)
    check("hitbox ayunan ada di tengah ayunan",
          hb is not None and hb.width > 10 and hb.height > 10,
          "%s" % (hb,))
    h._razak_attack_progress = 0.0
    check("hitbox tutup sebelum recovery",
          G._swing_hitbox(h, h.x, h.y) is None)
    h._razak_attack_active = False
    check("hitbox tutup saat idle",
          G._swing_hitbox(h, h.x, h.y) is None)

    # 6. controller: dt & nama lama
    h2 = hero_at(0.0, 0.0)
    h2.timer = COOLDOWN
    h2._razak_prev_timer = 0
    G._update_attack_anim(h2)
    old = ("_razak_attack_active", "_razak_attack_frame",
           "_razak_attack_progress", "_razak_prev_timer")
    check("atribut lama tetap diisi", all(hasattr(h2, o) for o in old),
          ", ".join(o.lstrip("_") for o in old))
    check("delta-time tersedia untuk FX", 0.0 < h2._razak_dt <= 0.05,
          "%.4f s" % h2._razak_dt)

    # 7. trail
    trail = F.SwingTrail()
    for i in range(F.TRAIL_SAMPLES + 6):
        trail.push(pygame.Vector2(10 + i, 20),
                   pygame.Vector2(40 + i, 5))
        trail.update(DT)
    check("trail dibatasi TRAIL_SAMPLES",
          len(trail.samples) <= F.TRAIL_SAMPLES,
          "%d sampel" % len(trail.samples))
    for _ in range(40):
        trail.update(DT)
    check("trail meluruh habis", not trail.samples)

    # 8. particle bounds
    ps = F.ParticleSystem(F.MAX_PARTICLES)
    for i in range(900):
        ps.spawn(0.0, 0.0, 1.0, 1.0, 0.4, 2, F.P["fire_hot"])
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
    gun = F.gun_end(h3, h3.x, h3.y)
    pr = d3.spawn_napalm(gun.x, gun.y, h3.target.x, h3.target.y)
    check("napalm lahir di moncong flamethrower",
          pr is not None and
          (pygame.Vector2(pr.position) - gun).length() <= 26.0,
          "dist %.1f px" % (pygame.Vector2(pr.position) - gun).length())
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

    # 11. pusat Q di target (bukan badan); E landing di posisi baru
    h5 = hero_at(300.0, 200.0)
    F.attach(h5)
    d5 = F.director_for(h5)
    h5.target = hero_at(520.0, 210.0)
    h5.target.alive = True
    F.notify_skill_impact(h5, 520.0, 210.0, 75, "q")
    qfx = None
    for s in d5.skills:
        if s.kind == "q":
            qfx = s
    check("impact Q memakai pusat target dunia",
          qfx is not None and abs(qfx.x - 520.0) < 2.0,
          str((qfx.x, qfx.y) if qfx else None))
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
    check("impact memicu paket feedback (flash+spark+debris+shock)",
          len(d6.impacts) == 1 and d6.particles.count() > 12,
          "impacts %d, partikel %d" % (len(d6.impacts),
                                       d6.particles.count()))
    FEEL.reset()
    F.reset_all()

    # 13. shake selalu terkuras & bus dibagikan
    FEEL.SHAKE.enabled = True
    F.shake(8.0, 0.3)
    for _ in range(60):
        FEEL.SHAKE.update(DT)
    check("shake kembali ke 0", FEEL.SHAKE.amount == 0.0)
    FEEL.reset()
    from heroes import zephyr_fx as ZF
    check("satu bus hit-stop/shake untuk semua karakter",
          ZF.HITSTOP is FEEL.HITSTOP and ZF.SHAKE is FEEL.SHAKE)
    core = open(os.path.join(ROOT, "_core.py"), encoding="utf-8").read()
    i = core.index("HIT STOP (game feel)")
    gate = core[i:i + 700]
    check("Game.update membekukan lewat bus SHARED",
          "combat_feel" in gate and "zephyr_fx" not in gate,
          "gate: heroes.combat_feel.should_freeze_frame()")

    # 14. supresi ganda di lane boss
    calls = {"a": 0, "g": 0, "f": 0, "p": 0}
    ra, rg = G._draw_machete_swing_arc, G._draw_napalm_ground
    rf, rp = G._draw_sticky_napalm, G._manage_projectiles_no_patches
    G._draw_machete_swing_arc = staticmethod(
        lambda *a, **k: calls.__setitem__("a", calls["a"] + 1))
    G._draw_napalm_ground = staticmethod(
        lambda *a, **k: calls.__setitem__("g", calls["g"] + 1))
    G._draw_sticky_napalm = staticmethod(
        lambda *a, **k: calls.__setitem__("f", calls["f"] + 1))
    G._manage_projectiles_no_patches = staticmethod(
        lambda *a, **k: calls.__setitem__("p", calls["p"] + 1))
    try:
        surf = pygame.Surface((240, 240), pygame.SRCALPHA)
        ha = hero_at(120.0, 190.0)
        manual_attack(ha, 0.5)
        F.reset_all()
        G.draw_razak(surf, ha, 120, 190)
        check("pita ayunan TIDAK digambar 2x di lane boss",
              calls["a"] == 0 and F.owns(ha),
              "renderer %d kali, lapisan hidup ambil alih" % calls["a"])
        hq = hero_at(120.0, 190.0, active_skill="q",
                     active_skill_timer=30, target=hero_at(320, 190))
        hq.target.alive = True
        hq._razak_attack_active = False
        G.draw_razak(surf, hq, 120, 190)
        check("telegraph tanah TETAP digambar renderer", calls["g"] == 1)
        check("foreground napalm & proyektil canvas digantikan lapisan hidup",
              calls["f"] == 0 and calls["p"] == 0)
        lm, G._LIVE_MOD = G._LIVE_MOD, False
        calls["a"] = calls["f"] = calls["g"] = calls["p"] = 0
        G.draw_razak(surf, ha, 120, 190)
        G.draw_razak(surf, hq, 120, 190)
        # dua draw boss = dua kali lintasan proyektil fallback; yang
        # penting pita, telegraph, dan manager canvas semuanya hidup.
        check("fallback canvas aktif saat modul FX absen",
              calls["a"] == 1 and calls["g"] == 1 and calls["p"] >= 1,
              "arc %d, ground %d, proj %d" % (calls["a"], calls["g"],
                                              calls["p"]))
        G._LIVE_MOD = lm
    finally:
        G._draw_machete_swing_arc = ra
        G._draw_napalm_ground = rg
        G._draw_sticky_napalm = rf
        G._manage_projectiles_no_patches = rp
    F.reset_all()

    # 15. render order lapisan (ground -> sprite -> live)
    h8 = hero_at(140.0, 200.0)
    F.attach(h8)
    d8 = F.director_for(h8)
    for i in range(10):
        manual_attack(h8, 0.30 + i * 0.03)
        F.tick(DT)
    ground = pygame.Surface((280, 280), pygame.SRCALPHA)
    F.draw_ground_layer(ground, h8, 140, 200)
    live = pygame.Surface((280, 280), pygame.SRCALPHA)
    F.draw_live_layer(live, h8, 140, 200)
    check("ground layer & live layer keduanya berisi",
          ground.get_bounding_rect(min_alpha=4).width > 0
          and live.get_bounding_rect(min_alpha=4).width > 0,
          "trail %d, ground %s / live %s" % (
              len(d8.trail.samples),
              ground.get_bounding_rect(min_alpha=4),
              live.get_bounding_rect(min_alpha=4)))
    F.reset_all()

    # 16. budget waktu
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
                G.draw_razak(surf, h, 120, 200)
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
    check("satu frame penuh (renderer + live FX) < 8 ms", ms < 8.0,
          "%.2f ms (median)" % ms)
    check("cache surface di bawah batas",
          F.cache_size() <= F._SURF_MAX,
          "%d / %d entri" % (F.cache_size(), F._SURF_MAX))
    check("partikel dalam cap saat ramai",
          F.total_particles() <= F.MAX_PARTICLES, "%d" % F.total_particles())
    F.reset_all()

    # 17. API lama renderer utuh
    legacy = ("draw_razak", "draw_boss", "NapalmProjectile", "NapalmPatch",
              "_resolve_pose", "_update_attack_anim", "_attack_pose",
              "attack_phase", "_machete_grip_local", "_machete_tip_local",
              "_gun_end_local", "_grip_screen", "_tip_screen",
              "_gun_end_screen", "_swing_hitbox", "_spawn_napalm",
              "_manage_projectiles", "_manage_projectiles_no_patches",
              "_draw_machete_swing_arc", "_draw_shockwave", "_fx_scale",
              "_detect_moving", "_draw_fire_aura", "_draw_napalm_ground",
              "_draw_flamebreak_ground", "_draw_firefly_ground",
              "_draw_firestorm_ground", "_draw_sticky_napalm",
              "_draw_flamebreak", "_draw_firestorm", "_draw_razak_full",
              "_draw_razak_full_raw", "_draw_razak_idle", "_draw_razak_walk",
              "_draw_razak_attack", "_draw_razak_dashing", "_local",
              "_local_to_screen", "_body_offset", "_raw_shift",
              "PALETTE", "SKILL_DUR", "SKILL_RADIUS", "ATTACK_PHASES",
              "ATTACK_WINDUP_END", "ATTACK_SWING_END", "DEBUG_CHARACTER",
              "live_fx_ready", "GROUND_DY", "RIG_W", "RIG_H", "SCALE",
              "MACHETE_LEN", "MACHETE_ARM_LEN")
    missing = [n for n in legacy if not hasattr(G, n)]
    check("API renderer lama utuh", not missing, missing or
          "%d/%d" % (len(legacy), len(legacy)))

    # 18. debug mode
    check("DEBUG_CHARACTER ada & mati secara default",
          G.DEBUG_CHARACTER is False and F.DEBUG_CHARACTER is False)
    dbg = inspect.getsource(F.draw_debug_overlay)
    check("overlay debug lengkap (hitbox/hurtbox/range/state/fps/partikel)",
          all(t in dbg for t in ("_swing_hitbox", "radius", "range",
                                 "state", "fps", "particles")))

    # 19. integrasi engine
    ent = open(os.path.join(ROOT, "_entity.py"), encoding="utf-8").read()
    bb = open(os.path.join(ROOT, "bosses", "base_boss.py"),
              encoding="utf-8").read()
    check("Hero._do_attack -> notify_melee_impact (razak)",
          "razak_fx.notify_melee_impact" in ent
          or "_rfx.notify_melee_impact" in ent)
    check("proyektil hero -> notify_projectile_impact (razak)",
          "_rfx.notify_projectile_impact" in ent)
    check("Boss melee -> notify_melee_impact (boss_type razak)",
          "_rfx.notify_melee_impact" in bb)
    check("Boss skill -> notify_skill_impact (razak)",
          "_rfx.notify_skill_impact" in bb)
    init = open(os.path.join(ROOT, "heroes", "__init__.py"),
                encoding="utf-8").read()
    seg = init.split("_LIVE_FX_HEROES")[1].split("}", 1)[0]
    check("razak terdaftar di _LIVE_FX_HEROES", '"razak"' in seg,
          seg.replace("\n", " ").strip())
    check("razak terdaftar di _LIVE_FX_PATHS",
          '"razak": "heroes.razak_fx"' in init)


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
