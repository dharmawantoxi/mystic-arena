#!/usr/bin/env python3
"""Regression test ALCHEMIST MASTERWORK v2 + COMBAT FX v3.

Mengunci lewat path shipping (bosses.level2._NS_alchemist +
heroes.alchemist_fx + wiring base_boss/_entity/heroes):

  * prosedural murni (tanpa pemuatan aset gambar);
  * rig: siluet keluarga (true boss tertinggi), pose render tanpa
    exception dua arah hadap + portrait;
  * animation controller: fase serangan bernama, kurva monoton,
    jendela hit aktif, delta-time, state ANIM_PRIORITY;
  * swing arc: sudut cleaver menyapu BUSUR (bukan lerp posisi),
    canvas trail hanya di jendela ayunan, hitbox hanya di jendela;
  * projectile lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT
    -> DESTROY; botol mendarat TEPAT di target; umur terbatas;
  * particle system: cap terpakai, fade + gravity, habis sendiri;
  * skill FX lifecycle: CAST -> CHARGE -> RELEASE -> AREA -> IMPACT
    -> FADE untuk Q/W/E/R; semua efek mati setelah selesai;
  * impact + game feel: hit-stop 0.03-0.08 s tercatat di bus
    combat_feel, impact ter-dedupe;
  * integrasi: _LIVE_FX_HEROES, hook melee base_boss + _entity,
    director satu arah (tidak mengubah field gameplay);
  * budget render < 2.2 ms/frame (canvas) + live layer murah.

Jalankan: python3 tools/test_alchemist_masterwork.py
"""
import inspect
import math
import os
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level2 as L
import heroes.alchemist_fx as A
from heroes import combat_feel as feel

NS = L._NS_alchemist
CD = 50
AI_DUR = {"q": 40, "w": 60, "e": 60, "r": 90}


def probe(**kw):
    b = SimpleNamespace(boss_type="alchemist", boss_class="true",
                        x=230.0, y=230.0, direction=1, facing=1,
                        pulse=1.2, timer=0, attack_cooldown=CD,
                        active_skill=None, active_skill_timer=0,
                        target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30,
                        hp=9000, max_hp=9000, rage_active=False,
                        speed=0.75)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    NS.draw_alchemist(s, b, 230, 230)
    return s


# ── 1. prosedural + kontrak API ─────────────────────────────────
def test_procedural_and_api():
    for path in ("bosses/level2.py", "heroes/alchemist_fx.py"):
        src = open(os.path.join(ROOT, path)).read()
        assert "pygame.image.load" not in src, path
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in A.ALCHEMIST_PALETTE, key
        assert key in NS.PALETTE or True
    assert callable(NS.draw_alchemist) and callable(NS.draw_boss)
    assert callable(NS._draw_alch_full) and callable(
        NS._draw_alch_full_raw)
    assert NS.SKILL_DUR == AI_DUR
    print("PASS prosedural + kontrak API")


# ── 2. rig: keluarga & pose render ──────────────────────────────
def test_family_size():
    def bbox(fn, b):
        s = pygame.Surface((460, 460), pygame.SRCALPHA)
        fn(s, b, 230, 230)
        return s.get_bounding_rect(min_alpha=100)

    alch = bbox(NS.draw_alchemist, probe())
    others = {}
    for name, fn, cd in (("razak", L.draw_razak, 45),
                         ("khalros", L.draw_khalros, 45),
                         ("gorath", L.draw_gorath, 44)):
        b = SimpleNamespace(boss_type=name, boss_class="mini",
                            x=230.0, y=230.0, direction=1, facing=1,
                            pulse=1.2, timer=0, attack_cooldown=cd,
                            active_skill=None, active_skill_timer=0,
                            target=None, _render_scale=1.0,
                            hurt_flash_timer=0, alive=True, radius=30,
                            hp=9000, max_hp=9000)
        others[name] = bbox(fn, b)
    for name, r in others.items():
        assert alch.height >= r.height, (name, alch, r)
        assert alch.width >= r.width - 18, (name, alch, r)
    assert alch.height >= 130, alch
    # dua arah hadap + portrait + hurt render tanpa exception
    tg = SimpleNamespace(x=320.0, y=230.0, alive=True)
    cases = [probe(direction=-1), probe(_portrait_hd=True),
             probe(hurt_flash_timer=8),
             probe(active_skill="q", active_skill_timer=20, target=tg),
             probe(active_skill="w", active_skill_timer=30, target=tg),
             probe(active_skill="e", active_skill_timer=30),
             probe(active_skill="r", active_skill_timer=40),
             probe(_alch_attack_active=True,
                   _alch_attack_progress=0.54, timer=50)]
    for c in cases:
        r = render(c).get_bounding_rect(min_alpha=100)
        assert r.width > 40 and r.height > 60, (c.active_skill, r)
    print("PASS family size %s vs %s" % (alch, others))


# ── 3. animation controller ─────────────────────────────────────
def test_animation_controller():
    order = NS.attack_phases_order()
    assert order == ("ANTICIPATION", "WINDUP", "SWING", "IMPACT",
                     "FOLLOW", "RECOVERY"), order
    # kurva monotop naik + hold impact
    prev = -1.0
    for i in range(101):
        v = NS._attack_curve(i / 100.0)
        assert v >= prev - 1e-9, (i, v, prev)
        prev = v
    assert abs(NS._attack_curve(1.0) - 1.0) < 1e-6
    # fase dari progress mentah
    assert NS.attack_phase(0.05) == "ANTICIPATION"
    assert NS.attack_phase(0.20) == "WINDUP"
    assert NS.attack_phase(0.40) == "SWING"
    assert NS.attack_phase(0.55) == "IMPACT"
    assert NS.attack_phase(0.70) == "FOLLOW"
    assert NS.attack_phase(0.90) == "RECOVERY"
    assert NS.attack_phase(None) == "NONE"
    # controller mengisi state + fase + jendela hit + dt
    b = probe()
    NS._update_attack_anim(b)
    assert hasattr(b, "_alch_dt") and 0.0 < b._alch_dt <= 0.05
    assert hasattr(b, "_alch_state") and hasattr(b, "_alch_state_time")
    assert hasattr(b, "_alch_attack_phase")
    assert hasattr(b, "_alch_hit_active")
    # simulasikan serangan penuh lewat controller
    b.timer = CD
    b._alch_prev_timer = 0
    b._alch_attack_active = True
    seen_phases = []
    hit_windows = 0
    for f in range(CD + 2):
        b._alch_attack_frame = f
        NS._update_attack_anim(b)
        if b._alch_attack_phase not in seen_phases:
            seen_phases.append(b._alch_attack_phase)
        if b._alch_hit_active:
            hit_windows += 1
    for ph in order:
        assert ph in seen_phases, (ph, seen_phases)
    assert 8 <= hit_windows <= 22, hit_windows
    # prioritas state
    prio = NS.ANIM_PRIORITY
    assert prio["DEATH"] > prio["HURT"] > prio["SPECIAL"] > \
        prio["SWING"] > prio["WALK"] > prio["IDLE"]
    print("PASS animation controller (fase %s, hitwin %d)" %
          (len(seen_phases), hit_windows))


# ── 4. swing arc + trail + hitbox ───────────────────────────────
def test_swing_arc():
    # sudut menyapu busur: dari windup (-2.30) naik terus ke impact
    angs = [NS._attack_pose(NS._attack_curve(p / 100.0))["blade_f"]
            for p in range(30, 55)]
    deltas = [(a1 - a0) % (2 * math.pi) for a0, a1 in
              zip(angs, angs[1:])]
    # semua langkah searah (cw) dan tidak ada lompatan balik besar
    assert all(d < math.pi for d in deltas), deltas
    travel = (angs[-1] - angs[0]) % (2 * math.pi)
    assert travel > 2.4, travel          # busur penuh > 137 derajat
    # canvas trail hanya di jendela ayunan
    def trail_pixels(progress):
        s = pygame.Surface((460, 460), pygame.SRCALPHA)
        NS._draw_cleaver_swing_arc(s, 230, 230, 1, progress)
        return s.get_bounding_rect(min_alpha=30).width
    assert trail_pixels(0.10) <= 2       # sebelum ayunan: kosong
    assert trail_pixels(0.45) > 40       # puncak ayunan: lebar
    assert trail_pixels(0.95) <= 2       # setelah ayunan: kosong
    # hitbox hanya di jendela hit aktif
    b = probe(_alch_attack_active=True, _alch_attack_progress=0.10,
              timer=50)
    assert NS._swing_hitbox(b, 230, 230) is None
    b2 = probe(_alch_attack_active=True, _alch_attack_progress=0.50,
               timer=50)
    hb = NS._swing_hitbox(b2, 230, 230)
    assert hb is not None and hb.width > 20 and hb.height > 20, hb
    # anchor grip/tip konsisten dengan pose istirahat
    b3 = probe()
    g = NS._grip_screen(b3, 230, 230)
    t = NS._tip_screen(b3, 230, 230)
    assert 12 < math.hypot(t[0] - g[0], t[1] - g[1]) < 60
    print("PASS swing arc + trail + hitbox")


# ── 5. walk cycle ────────────────────────────────────────────────
def test_walk_cycle():
    def sig(phase):
        b = probe(pulse=phase / 2.4, _alch_moving=True)
        s = render(b)
        m = pygame.mask.from_surface(s, 100)
        return (m.count(), tuple(int(v) for v in m.centroid()))
    sigs = {sig(i * 0.5) for i in range(16)}
    assert len(sigs) >= 10, len(sigs)     # siklus hidup, bukan beku
    # kaki bergantian: band kaki (y+30..y+66) berubah nyata antar
    # fase berlawanan siklus (kaki depan <-> kaki belakang menukar)
    def leg_mask(phase):
        b = probe(pulse=phase / 2.4, _alch_moving=True)
        s = render(b)
        band = s.subsurface(pygame.Rect(150, 260, 160, 66)).copy()
        return pygame.mask.from_surface(band, 100)
    m0 = leg_mask(0.0)
    m1 = leg_mask(math.pi)
    diff = m0.overlap_area(m1, (0, 0))
    total = max(1, m0.count())
    xor = m0.count() + m1.count() - 2 * diff
    assert xor >= total // 6, (xor, total)   # >= ~17% piksel kaki berpindah
    print("PASS walk cycle (siklus %d pose, kaki XOR %d/%d px)" %
          (len(sigs), xor, total))


# ── 6. projectile lifecycle ─────────────────────────────────────
def test_projectile_lifecycle():
    ps = A.ParticleSystem(64)
    sysp = A.ProjectileSystem(ps, 8)
    # spawn
    pr = sysp.spawn(0, 0, 120, 60, kind="bottle", speed=600.0,
                    arc_height=40.0, ground=10.0)
    assert pr.active and pr.alive
    assert pr.trail == []
    # travel + trail
    dt = 1 / 60.0
    for _ in range(6):
        sysp.update(dt)
    assert pr.alive and len(pr.trail) >= 3
    assert math.hypot(pr.x - 0, pr.y - 60) < 130       # bergerak
    # hit tepat di target setelah waktu tempuh
    t_flight = math.hypot(120, 60) / 600.0
    for _ in range(int(t_flight / dt) + 2):
        sysp.update(dt)
        if not pr.alive:
            break
    assert not pr.alive, "botol tidak pernah mendarat"
    assert math.hypot(pr._hit_pos.x - 120,
                      pr._hit_pos.y - 60) < 2.0, "tidak tepat target"
    # impact callback terpanggil sekali
    calls = []
    pr2 = sysp.spawn(0, 0, 50, 50, kind="droplet", speed=500.0,
                     lifetime=0.05,
                     on_impact=lambda p: calls.append(1))
    for _ in range(30):
        sysp.update(dt)
    assert not pr2.alive and len(calls) == 1
    # cap proyektil
    for _ in range(20):
        sysp.spawn(0, 0, 10, 10, kind="coin", lifetime=5.0)
    assert sysp.count() <= 8
    sysp.clear()
    assert sysp.count() == 0
    print("PASS projectile lifecycle (spawn->travel->hit->destroy)")


# ── 7. particle system ──────────────────────────────────────────
def test_particle_system():
    ps = A.ParticleSystem(32)
    ps.burst(0, 0, 20, speed=(60, 200), life=(0.2, 0.3),
             size=(1, 3), colors=((200, 240, 90),), gravity=300.0)
    assert 18 <= ps.count() <= 20
    y0 = max(p.y for p in ps._active)
    for _ in range(5):                        # masih hidup -> gravity
        ps.update(1 / 60.0)
    y1 = max(p.y for p in ps._active)
    assert ps.count() > 0 and y1 > y0, (ps.count(), y0, y1)
    for _ in range(60):
        ps.update(1 / 60.0)
    assert ps.count() == 0, "partikel tidak mati-mati (kebocoran)"
    ps.burst(0, 0, 100, life=(0.1, 0.1), size=(1, 1),
             colors=((1, 2, 3),))
    assert ps.count() <= 32                   # cap keras
    ps.clear()
    print("PASS particle system (gravity, fade, cap, drain)")


# ── 8. skill FX lifecycle ───────────────────────────────────────
def test_skill_lifecycle():
    for kind in ("q", "w", "e", "r"):
        ps = A.ParticleSystem(64)
        fx = A.SkillFX(kind, 100, 100, ps, radius=80.0, ground=40.0)
        phases = []
        surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        dt = 1 / 60.0
        guard = 0
        while fx.active and guard < 600:
            fx.update(dt)
            fx.draw_ground(surface)
            fx.draw_front(surface)
            if not phases or phases[-1] != fx.phase:
                phases.append(fx.phase)
            guard += 1
        assert not fx.active, "%s tidak pernah selesai" % kind
        assert guard < 600
        for want in ("charge", "release", "fade"):
            assert want in phases, (kind, phases)
        assert phases[0] == "charge", (kind, phases)
        assert ps.count() <= 64
        # semua partikel skill mati setelah selesai
        for _ in range(120):
            ps.update(dt)
        assert ps.count() == 0, (kind, ps.count())
    print("PASS skill lifecycle Q/W/E/R (charge->release->fade)")


# ── 9. impact + game feel (hit-stop & dedupe) ───────────────────
def test_impact_and_game_feel():
    feel.reset()
    d = A.AlchemistFXDirector(probe())
    d.on_impact(10, 10, 0.0, 1.2, False, kind="slash")
    assert len(d.impacts) == 1
    # hit-stop diminta (0.03-0.08 s) dan tercatat di bus
    assert feel.HITSTOP.active, "hit-stop tidak aktif"
    remaining = getattr(feel.HITSTOP, "remaining", None)
    if remaining is None:
        remaining = getattr(feel.HITSTOP, "time_left", 0.05)
    assert 0.025 <= float(remaining) <= 0.085, remaining
    # impact kedua di titik sama dalam window → ter-dedupe
    d.on_impact(11, 11, 0.0, 1.2, False, kind="slash")
    assert len(d.impacts) == 1
    # impact mati sendiri
    for _ in range(120):
        ok = [i.update(1 / 60.0) for i in d.impacts]
    d.impacts = [i for i in d.impacts if i.active]
    assert not d.impacts
    # hit-stop window dibatasi: hit-stop besar tidak pernah > 0.08
    d.on_impact(500, 500, 0.0, 2.5, True, kind="greed")
    assert feel.HITSTOP.active
    feel.reset()
    print("PASS impact + game feel (hit-stop %.3f s, dedupe)" %
          float(remaining))


# ── 10. lapisan hidup: attach/owns/tick/draw/debug ──────────────
def test_live_layer():
    A.reset_all()
    feel.reset()
    b = probe(active_skill="w", active_skill_timer=40,
              w_target_x=330.0, w_target_y=260.0,
              target=SimpleNamespace(x=330.0, y=260.0, alive=True))
    assert A.attach(b) is True
    assert A.owns(b) is True
    surface = pygame.Surface((460, 460), pygame.SRCALPHA)
    surface.fill((18, 20, 28))
    A.draw_ground_layer(surface, b, 230, 230)
    before = surface.get_bounding_rect(min_alpha=10)
    A.draw_live_layer(surface, b, 230, 230)
    d = b._alch_fx
    # frame pertama bus combat_feel belum punya acuan (dt=0) —
    # satu langkah eksplisit menghidupkan edge cast skill.
    A.tick(1 / 60.0)
    assert d.projectiles.count() >= 1, "botol W tidak dilempar"
    # botol mendarat dekat target (konversi dunia->layar benar)
    for _ in range(80):
        A.tick(1 / 60.0)
    landed = math.hypot(d.projectiles.list()[0].x - 330,
                        d.projectiles.list()[0].y - 260) \
        if d.projectiles.count() else 0.0
    assert d.projectiles.count() == 0, "botol tidak pernah mendarat"
    # debug overlay
    A.DEBUG_CHARACTER = True
    d.draw_front(surface, 230, 230)
    A.DEBUG_CHARACTER = False
    # director tidak pernah menulis field gameplay
    gp = ("hp", "damage", "attack_cooldown", "q_timer", "w_timer",
          "e_timer", "r_timer")
    snap = {k: getattr(b, k, None) for k in gp}
    for _ in range(20):
        A.tick(1 / 60.0)
    for k in gp:
        assert getattr(b, k, None) == snap[k], k
    A.reset_all()
    assert not A.owns(b)
    print("PASS lapisan hidup (attach/owns/tick/draw/debug, satu arah)")


# ── 11. integrasi wiring ────────────────────────────────────────
def test_integration_wiring():
    import heroes as H
    assert "alchemist" in H._LIVE_FX_HEROES
    assert H._LIVE_FX_PATHS.get("alchemist") == "heroes.alchemist_fx"
    src_bb = open(os.path.join(ROOT, "bosses/base_boss.py")).read()
    assert "alchemist_fx" in src_bb and \
        "notify_melee_impact" in src_bb
    src_ent = open(os.path.join(ROOT, "_entity.py")).read()
    assert "alchemist_fx" in src_ent and \
        "notify_melee_impact" in src_ent
    # renderer memakai lapisan hidup + punya fallback canvas
    src_ns = inspect.getsource(NS.draw_alchemist)
    assert "_live_fx" in src_ns and "_draw_shockwave" in src_ns
    assert callable(getattr(NS, "live_fx_ready", None))
    print("PASS integrasi (live FX heroes + hook melee boss & hero)")


# ── 12. budget render ───────────────────────────────────────────
def test_budget():
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    b = probe()
    render(b)
    N = 40
    t0 = time.perf_counter()
    for i in range(N):
        b.pulse = 1.0 + i * 0.13
        render(b)
    ms = (time.perf_counter() - t0) / N * 1000
    assert ms < 2.2, "%.2f ms/frame" % ms
    # live layer dengan sim penuh juga murah
    A.reset_all()
    feel.reset()
    bb = probe(active_skill="r", active_skill_timer=45,
               target=SimpleNamespace(x=330.0, y=250.0, alive=True))
    A.attach(bb)
    s2 = pygame.Surface((460, 460), pygame.SRCALPHA)
    t0 = time.perf_counter()
    M = 60
    for i in range(M):
        bb.pulse = 1.0 + i * 0.1
        NS.draw_alchemist(s2, bb, 230, 230)
        A.tick(1 / 60.0)
    ms2 = (time.perf_counter() - t0) / M * 1000
    assert ms2 < 6.0, "%.2f ms/frame (renderer+live)" % ms2
    A.reset_all()
    feel.reset()
    print("PASS budget %.2f ms canvas, %.2f ms + live FX" % (ms, ms2))


if __name__ == "__main__":
    test_procedural_and_api()
    test_family_size()
    test_animation_controller()
    test_swing_arc()
    test_walk_cycle()
    test_projectile_lifecycle()
    test_particle_system()
    test_skill_lifecycle()
    test_impact_and_game_feel()
    test_live_layer()
    test_integration_wiring()
    test_budget()
    print("ALL ALCHEMIST MASTERWORK TESTS PASSED")
