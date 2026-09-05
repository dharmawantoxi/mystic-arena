#!/usr/bin/env python3
"""Regression test RAZAK FULL REWRITE v4 (render + animasi + FX hidup).

Mengunci lewat path shipping:
  * RENDER   — semua state tergambar tanpa exception, bbox memadai, tidak
               ada flicker (frame idle berubah tapi tidak pernah kosong).
  * ANIMASI  — fase serangan ANTICIPATION->RECOVERY berurutan; jendela
               hit aktif di SWING/IMPACT.
  * ATTACK   — busur machete monoton, trail canvas fallback di jendela
               aktif, tanpa ImpactFX pada basic attack.
  * PROJECTILE (lapisan hidup) — spawn -> travel -> trail -> hit/impact
               -> destroy; tidak ada yang hidup melampaui lifetime.
  * SKILL FX (lapisan hidup) — q/w/e/r lifecycle penuh + cleanup; durasi
               ter sinkron dengan timer AI (40/50/35/90).
  * GAME FEEL — hit-stop di dalam jendela 0.03-0.08 s; shake memudar.
  * INTEGRASI— jalur boss (draw_razak + live layer) & jalur hero
               (render_hero melewati _LIVE_FX_HEROES); reset_all
               mengembalikan semuanya ke nol.
  * KONTRAK  — SCALE=0.62, GROUND_DY=52, PIXEL=2, SKILL_RADIUS
               q75/w95/e80/r180; re-export dari bosses.level2.
  * PERF     — idle < 3.5 ms/frame; FX tick+draw < 6.0 ms/frame.

Jalankan: python3 tools/test_razak_rewrite.py
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
import bosses.razak_v4 as R4
import heroes.razak_fx as FX
import heroes  # heroes/__init__.py — pipeline sprite + live FX

NS = L._NS_razak
P = FX.RAZAK_PALETTE
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


def probe(**kw):
    b = SimpleNamespace(boss_type="razak", boss_class="mini", x=230.0,
                        y=230.0, direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=45, active_skill=None,
                        active_skill_timer=0, target=None,
                        _render_scale=1.0, hurt_flash_timer=0, alive=True,
                        radius=30, hp=9000, max_hp=9000, team="red",
                        hero_type="razak", damage=88, speed=1.6, range=60)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    L.draw_razak(s, b, 230, 230)
    return s


def bbox(s, alpha=100):
    return s.get_bounding_rect(min_alpha=alpha)


# ===================================================================
# 1. RENDER — semua state
# ===================================================================
def test_render_all_states():
    tg = SimpleNamespace(x=330.0, y=230.0, alive=True)
    cases = {
        "idle": probe(),
        "walk": probe(_razak_last_x=226.0, _razak_last_y=230.0),
        "attack": probe(_razak_attack_active=True, _razak_attack_progress=0.5),
        "cast_q": probe(active_skill="q", active_skill_timer=30, target=tg),
        "cast_w": probe(active_skill="w", active_skill_timer=30, target=tg),
        "cast_e": probe(active_skill="e", active_skill_timer=20, target=tg),
        "cast_r": probe(active_skill="r", active_skill_timer=40, target=tg),
        "hit": probe(hurt_flash_timer=6),
        "mirror": probe(direction=-1, facing=-1),
    }
    for name, b in cases.items():
        s = render(b)
        r = bbox(s)
        assert r.width > 60 and r.height > 60, (name, r)
    print("PASS render semua state (idle/walk/attack/cast/hit/mirror)")


def test_render_no_flicker():
    """Idle beranimasi tapi TIDAK PERNAH kosong di antara frame."""
    b = probe()
    for i in range(30):
        b.pulse = i * 0.2
        s = render(b)
        r = bbox(s)
        assert r.width > 60 and r.height > 60, (i, r)
    print("PASS tanpa flicker (30 frame idle tidak pernah kosong)")


# ===================================================================
# 2. ANIMATION CONTROLLER
# ===================================================================
def test_attack_phases_ordered():
    seen = []
    for i in range(101):
        name = NS.attack_phase(i / 100.0)
        if not seen or seen[-1] != name:
            seen.append(name)
    assert seen == PHASE_ORDER, seen
    assert FX.attack_phase(0.40) == "SWING"
    assert FX.attack_phase(0.55) == "IMPACT"
    assert tuple(FX.ATTACK_PHASES) == tuple(NS.ATTACK_PHASES)
    print("PASS fase serangan (ANTICIPATION->RECOVERY, sinkron FX)")


def test_animation_transitions_visual():
    """Attack -> recovery -> idle tanpa exception di tepi fase."""
    for ap in (0.0, 0.08, 0.09, 0.29, 0.30, 0.49, 0.50, 0.61, 0.62,
               0.79, 0.80, 1.0):
        b = probe(_razak_attack_active=True, _razak_attack_progress=ap)
        s = render(b)
        assert bbox(s).width > 60, ap
    print("PASS transisi antar-fase serangan (tepi semua segmen)")


# ===================================================================
# 3. ATTACK — arc, jendela aktif, trail
# ===================================================================
def test_attack_arc_quality():
    prev = None
    for i in range(41):
        ap = 0.30 + i * (0.20 / 40)
        pose = NS._attack_pose(ap)
        ang = pose["arm_a"]
        if prev is not None:
            assert ang - prev > -0.05, (ap, ang, prev)
            assert ang - prev < 1.2, (ap, ang - prev)
        prev = ang
    assert prev > 0.0, prev
    print("PASS arc serangan (machete wind-up -> strike monoton)")


def test_attack_trail_canvas():
    """Fallback trail canvas tergambar pada jendela aktif, tidak di luar."""
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    NS._draw_machete_swing_arc(s, 230, 230, 1, 0.50)
    assert bbox(s, 20).width > 40
    s2 = pygame.Surface((460, 460), pygame.SRCALPHA)
    NS._draw_machete_swing_arc(s2, 230, 230, 1, 0.90)
    assert bbox(s2, 20).height <= 2
    print("PASS trail sapuan canvas (aktif di jendela, mati di luar)")


def test_swing_hitbox():
    b = probe(_razak_attack_active=True, _razak_attack_progress=0.50)
    hb = NS._swing_hitbox(b, 230, 230)
    assert hb is not None and hb.width > 10 and hb.height > 10
    b2 = probe(_razak_attack_active=True, _razak_attack_progress=0.10)
    assert NS._swing_hitbox(b2, 230, 230) is None
    print("PASS geometri machete + jendela hitbox aktif")


# ===================================================================
# 4. PROJECTILE SYSTEM (lapisan hidup)
# ===================================================================
def test_projectile_lifecycle():
    ps = FX.ParticleSystem(64)
    syst = FX.ProjectileSystem(ps, 8)
    pr = syst.spawn(100.0, 100.0, 200.0, 100.0, speed=FX.NAPALM_SPEED,
                    radius=6.0, lifetime=2.0)
    assert pr.active and syst.count() == 1
    surf = pygame.Surface((300, 220), pygame.SRCALPHA)
    saw_body = False
    for i in range(130):
        syst.update(1 / 60.0)
        syst.draw(surf)
        if pr.active and len(pr.trail) > 2:
            saw_body = True
    assert not pr.active and syst.count() == 0
    assert saw_body
    print("PASS projectile lifecycle (spawn->travel->trail->hit->destroy)")


# ===================================================================
# 5. SKILL FX (lapisan hidup) — lifecycle + cleanup
# ===================================================================
def test_skill_fx_lifecycle():
    for kind, dur in (("q", 40), ("w", 50), ("e", 35), ("r", 90)):
        ps = FX.ParticleSystem(96)
        fx = FX.SkillFX(kind, 200.0, 200.0, ps, aim=(320.0, 180.0))
        surf = pygame.Surface((460, 300), pygame.SRCALPHA)
        frames = int(max(FX.SKILL_TOTAL[kind] * 60, dur) + 20)
        for i in range(frames):
            fx.update(1 / 60.0)
            fx.draw_ground(surf)
            fx.draw_front(surf)
        assert not fx.active, (kind, fx.age, fx.total)
        for i in range(240):
            ps.update(1 / 60.0)
        assert ps.count() == 0, (kind, ps.count())
    print("PASS skill FX q/w/e/r lifecycle (cast->charge->release->fade)")


# ===================================================================
# 6. GAME FEEL — hit stop & shake
# ===================================================================
def test_game_feel():
    if FX._feel is not None:
        for s in (0.005, 0.2, 0.05):
            FX.hit_stop(s)
            try:
                left = FX._feel.HITSTOP.left
                assert 0.029 <= left <= 0.081, left
            except AttributeError:
                fr = FX._feel.HITSTOP.frames
                assert 2 <= fr <= 5, fr
    sh = FX._feel.ScreenShake() if FX._feel is not None else None
    if sh is not None:
        sh.add(5, 0.2)
        sh.add(2, 0.1)
        assert sh.shake_strength <= 5.0 + 1e-6
        a0 = sh.amount
        for _ in range(40):
            sh.update(1 / 60.0)
        assert sh.amount < a0
    d = FX.RazakFXDirector(probe())
    for i in range(20):
        d.on_impact(230 + i, 230, 0.0, 1.0)
    assert len(d.impacts) <= FX.MAX_IMPACTS
    print("PASS game feel (hit-stop 0.03-0.08 s, shake meluruh, budget)")


# ===================================================================
# 7. INTEGRASI — jalur boss (live layer) & jalur hero (render_hero)
# ===================================================================
def test_boss_path_live_layer():
    FX.reset_all()
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    tgt = SimpleNamespace(x=340.0, y=240.0, alive=True, radius=16)
    b = probe(target=tgt)
    for i in range(70):
        ap = i / 70.0
        b._razak_attack_active = True
        b._razak_attack_progress = ap
        b.pulse += 0.05
        FX.tick(1 / 60.0)
        L.draw_razak(surf, b, 230, 230)
    assert FX.owns(b)
    d = FX.director_for(b)
    assert d.trail.active() if hasattr(d.trail, "active") else True
    b._razak_attack_active = False
    b.active_skill = "q"
    for t in range(40, 0, -1):
        b.active_skill_timer = t
        FX.tick(1 / 60.0)
        L.draw_razak(surf, b, 230, 230)
    b.active_skill = None
    for i in range(400):
        FX.tick(1 / 60.0)
    d = FX.director_for(b)
    assert d.projectiles.count() == 0
    assert not d.skills
    assert not d.impacts
    FX.reset_all()
    assert not FX.owns(b)
    print("PASS jalur boss: live layer aktif, FX drain, reset bersih")


def test_hero_pipeline_path():
    """render_hero('razak') — canvas di-cache + live layer 1:1 di layar."""
    FX.reset_all()
    heroes._HERO_CACHE_ENABLED = False
    try:
        h = probe(x=200.0, y=200.0)
        h.facing = 1
        h._moving_cached = False
        surf = pygame.Surface((460, 400), pygame.SRCALPHA)
        for i in range(40):
            h.pulse += 0.05
            heroes.render_hero("razak", surf, h, 200, 200)
        assert FX.owns(h) or getattr(h, "_razak_live_fx", False)
    finally:
        heroes._HERO_CACHE_ENABLED = True
    h2 = probe(x=200.0, y=200.0)
    h2._skip_renderer_projectiles = True
    canvas = pygame.Surface((300, 300), pygame.SRCALPHA)
    L.draw_razak(canvas, h2, 150, 150)
    assert bbox(canvas).width > 60
    FX.reset_all()
    print("PASS jalur hero: render_hero + live layer, canvas pass bersih")


def test_palette_contract():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in P, key
        assert len(P[key]) == 3
    FX._sync_palette()
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert len(P[key]) == 3
    print("PASS kontrak palette 9 kunci")


# ===================================================================
# 8. KONTRAK v4 — constants, re-export, public names
# ===================================================================
def test_v4_constants_locked():
    assert NS is R4._NS_razak
    assert NS.SCALE == 0.62
    assert NS.GROUND_DY == 52
    assert NS.PIXEL == 2
    assert NS.RIG_W == 176 and NS.RIG_H == 152
    assert NS.SKILL_DUR == {"q": 40, "w": 50, "e": 35, "r": 90}
    assert NS.SKILL_RADIUS == {"q": 75, "w": 95, "e": 80, "r": 180}
    assert abs(NS._fx_scale(SimpleNamespace(_render_scale=0.5)) - 2.0) < 1e-6
    assert abs(NS._fx_scale(SimpleNamespace(_render_scale=0.1)) - 2.6) < 1e-6
    print("PASS konstanta v4 (SCALE/GROUND_DY/PIXEL/SKILL_DUR/RADIUS)")


def test_public_names():
    for name in ("draw_razak", "draw_boss", "NapalmProjectile", "NapalmPatch",
                 "_draw_razak_full", "_draw_razak_full_raw", "_draw_shadow",
                 "_draw_sticky_napalm", "_draw_flamebreak", "_draw_firestorm",
                 "_draw_shockwave", "attack_phase", "live_fx_ready"):
        assert hasattr(NS, name), name
    print("PASS nama publik _NS_razak utuh")


def test_khalros_gorath_alchemist_untouched():
    assert hasattr(L, "_NS_khalros") and hasattr(L, "draw_khalros")
    assert hasattr(L, "_NS_gorath") and hasattr(L, "draw_gorath")
    assert hasattr(L, "_NS_alchemist") and hasattr(L, "draw_alchemist")
    src = inspect.getsource(L)
    assert "class _NS_khalros" in src
    assert "class _NS_gorath" in src
    assert "class _NS_alchemist" in src
    assert "class _NS_razak" not in src
    print("PASS khalros/gorath/alchemist tidak disentuh")


# ===================================================================
# 9. PERFORMANCE
# ===================================================================
def test_performance():
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    b = probe()
    for i in range(20):
        b.pulse = 1.0 + i * 0.13
        L.draw_razak(surf, b, 230, 230)
    N = 40
    t0 = time.perf_counter()
    for i in range(N):
        b.pulse = 1.0 + i * 0.13
        L.draw_razak(surf, b, 230, 230)
    dt = (time.perf_counter() - t0) / N * 1000
    assert dt < 3.5, dt
    print(f"    renderer idle: {dt:.2f} ms/frame (budget 3.5)")

    FX.reset_all()
    screen = pygame.Surface((460, 460), pygame.SRCALPHA)
    tgt = SimpleNamespace(x=340.0, y=240.0, alive=True, radius=16)
    b2 = probe(target=tgt)
    b2._razak_attack_active = True
    b2._razak_attack_progress = 0.5
    b2.active_skill = "r"
    b2.active_skill_timer = 20
    for i in range(10):
        FX.tick(1 / 60.0)
        L.draw_razak(screen, b2, 230, 230)
    t0 = time.perf_counter()
    M = 40
    for i in range(M):
        b2.pulse += 0.05
        FX.tick(1 / 60.0)
        L.draw_razak(screen, b2, 230, 230)
    dt2 = (time.perf_counter() - t0) / M * 1000
    assert dt2 < 6.0, dt2
    print(f"    FX penuh (swing+R): {dt2:.2f} ms/frame (budget 6.0)")
    FX.reset_all()
    print("PASS performance")


def test_procedural_only():
    for mod in (L, R4, FX):
        src = inspect.getsource(mod)
        assert "pygame.image.load" not in src
    print("PASS prosedural murni (tanpa image.load)")


if __name__ == "__main__":
    test_render_all_states()
    test_render_no_flicker()
    test_attack_phases_ordered()
    test_animation_transitions_visual()
    test_attack_arc_quality()
    test_attack_trail_canvas()
    test_swing_hitbox()
    test_projectile_lifecycle()
    test_skill_fx_lifecycle()
    test_game_feel()
    test_boss_path_live_layer()
    test_hero_pipeline_path()
    test_palette_contract()
    test_v4_constants_locked()
    test_public_names()
    test_khalros_gorath_alchemist_untouched()
    test_performance()
    test_procedural_only()
    print("ALL RAZAK REWRITE TESTS PASSED")
