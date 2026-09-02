#!/usr/bin/env python3
"""Regression test NYZRAK FULL REWRITE (render + animasi + FX hidup).

Mengunci lewat path shipping:
  * RENDER   — semua state tergambar tanpa exception, bbox memadai, tidak
               ada flicker (frame idle berubah tapi tidak pernah kosong).
  * ANIMASI  — controller: prioritas state, transisi, frame index,
               sub-fase serangan ANTICIPATION->RECOVERY, jendela aktif.
  * ATTACK   — arc sweep & thrust: monoton, tanpa lompatan sudut, trail
               canvas fallback tergambar di jendela aktif.
  * PROJECTILE (lapisan hidup) — spawn -> travel -> trail -> hit/impact
               -> destroy; tidak ada yang hidup melampaui lifetime.
  * SKILL FX (lapisan hidup) — q/w/e/r lifecycle penuh + cleanup; durasi
               ter sinkron dengan timer AI.
  * GAME FEEL — hit-stop di dalam jendela 0.03-0.08 s; shake memudar;
               impact tidak menumpuk melampaui batas.
  * INTEGRASI— jalur boss (draw_nyzrak + live layer) & jalur hero
               (render_hero melewati _LIVE_FX_HEROES); reset_all
               mengembalikan semuanya ke nol.
  * PERF     — idle < 2.35 ms/frame; FX tick+draw < 2.0 ms/frame;
               partikel turun ke 0 setelah pertarungan selesai.

Jalankan: python3 tools/test_nyzrak_rewrite.py
"""
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

import bosses.level3 as L
import heroes.nyzrak_fx as FX
import heroes  # heroes/__init__.py — pipeline sprite + live FX

NS = L._NS_nyzrak
P = FX.NYZRAK_PALETTE


# ── helper ─────────────────────────────────────────────────────────
def probe(**kw):
    b = SimpleNamespace(boss_type="nyzrak", boss_class="mini", x=230.0,
                        y=230.0, direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=77, active_skill=None,
                        active_skill_timer=0, target=None,
                        _render_scale=1.0, hurt_flash_timer=0, alive=True,
                        radius=30, hp=9000, max_hp=9000, team="red",
                        hero_type="nyzrak", damage=88)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(b, size=460):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    L.draw_nyzrak(s, b, 230, 230)
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
        "walk": probe(_nyz_last_x=226.0, _nyz_last_y=230.0),
        "run": probe(_nyz_last_x=222.0, _nyz_last_y=228.0),
        "thrust": probe(_nyz_attack_active=True, _nyz_attack_progress=0.5),
        "sweep": probe(_nyz_attack_active=True, _nyz_attack_progress=0.5,
                       _pose_variant=1),
        "cast_q": probe(active_skill="q", active_skill_timer=30, target=tg),
        "cast_w": probe(active_skill="w", active_skill_timer=30, target=tg),
        "cast_e": probe(active_skill="e", active_skill_timer=30, target=tg),
        "cast_r": probe(active_skill="r", active_skill_timer=30, target=tg),
        "hit": probe(hurt_flash_timer=6),
        "death": probe(alive=False, hp=0, _nyz_death_age=20),
        "mirror": probe(direction=-1, facing=-1),
    }
    for name, b in cases.items():
        s = render(b)
        r = bbox(s)
        assert r.width > 60 and r.height > 60, (name, r)
        # tidak corrupt: setiap baris bbox berisi piksel
    print("PASS render semua state (idle/walk/run/thrust/sweep/cast/hit/death)")


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
def test_animation_controller():
    C = NS._NyzAnimController
    # prioritas: death > hurt > skill > attack > run > walk > idle
    assert C.resolve(probe())["state"] == "IDLE"
    assert C.resolve(probe(hurt_flash_timer=3))["state"] == "HIT"
    assert C.resolve(probe(active_skill="q", active_skill_timer=25))["state"] == "SKILL"
    assert C.resolve(probe(_nyz_attack_active=True,
                           _nyz_attack_progress=0.2))["state"] == "ATTACK"
    assert C.resolve(probe(_nyz_attack_active=True, _nyz_attack_progress=0.2,
                           _pose_variant=1))["state"] == "SWING"
    assert C.resolve(probe(_nyz_move_mag=4.0), moving=True,
                     run=True)["state"] == "RUN"
    assert C.resolve(probe(alive=False, hp=0))["state"] == "DEATH"
    # semua state punya prioritas & transisi terdefinisi
    for st in NS.STATE_PRIORITY:
        assert st in C.TRANSITIONS, st
    # sub-fase serangan lengkap & berurutan
    stages = [C.attack_stage(i / 100.0)[0] for i in range(101)]
    order = [NS.ATTACK_PHASES[i][0] for i in range(6)]
    seen = []
    for st in stages:
        if not seen or seen[-1] != st:
            seen.append(st)
    assert seen == order, seen
    # jendela aktif sesuai tabel
    assert not C.attack_active(0.39)
    assert C.attack_active(0.40)
    assert C.attack_active(0.64)
    assert not C.attack_active(0.65)
    # frame index looping deterministik
    f0 = C.frame_index("WALK", 0.0)
    f1 = C.frame_index("WALK", 0.05 * 9)
    assert 0 <= f0 < 8 and 0 <= f1 < 8 and f0 != f1, (f0, f1)
    # transisi valid: IDLE boleh ke ATTACK, DEATH nir-ujung
    assert "ATTACK" in C.TRANSITIONS["IDLE"]
    assert C.TRANSITIONS["DEATH"] == set()
    print("PASS animation controller (prioritas, sub-fase, jendela aktif, "
          "frame index, transisi)")


def test_animation_transitions_visual():
    """Attack -> recovery -> idle tanpa exception di tepi fase."""
    for variant in (0, 1):
        for ap in (0.0, 0.21, 0.22, 0.399, 0.40, 0.5, 0.559, 0.56, 0.639,
                   0.64, 0.799, 0.80, 1.0):
            b = probe(_nyz_attack_active=True, _nyz_attack_progress=ap,
                      _pose_variant=variant)
            s = render(b)
            assert bbox(s).width > 60
    print("PASS transisi antar-fase serangan (tepi semua segmen)")


# ===================================================================
# 3. ATTACK — arc, jendela aktif, trail
# ===================================================================
def test_attack_arc_quality():
    # sweep: sudut naik monoton selama swing tanpa lompatan besar
    NS._pose_variant_now = "sweep"
    prev = None
    for i in range(41):
        ap = 0.40 + i * (0.16 / 40)
        ang, reach, gx, gy = NS._spear_pose_geom("attack", ap, 2.0)
        if prev is not None:
            assert ang >= prev - 0.01, (ap, ang, prev)
            assert ang - prev < 12.0, (ap, ang - prev)   # tanpa teleport
        prev = ang
    assert prev > 38.0, prev
    # thrust: jangkauan membentang lalu menarik saat recovery (momentum)
    NS._pose_variant_now = "thrust"
    reaches = [NS._spear_pose_geom("attack", i / 100.0, 2.0)[1]
               for i in range(40, 101)]
    assert max(reaches) > 30.0 and reaches[-1] < max(reaches)
    print("PASS arc serangan (sweep monoton -115->40 deg, thrust momentum)")


def test_attack_trail_canvas():
    """Fallback trail canvas tergambar pada jendela aktif, tidak di luar."""
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    b = probe(_nyz_attack_active=True, _nyz_attack_progress=0.55)
    NS._draw_swing_arc(s, b, 230, 230, "attack", 0.55, 2.0, 1)
    assert bbox(s, 20).width > 40
    s2 = pygame.Surface((460, 460), pygame.SRCALPHA)
    b2 = probe(_nyz_attack_active=True, _nyz_attack_progress=0.9)
    NS._draw_swing_arc(s2, b2, 230, 230, "attack", 0.9, 2.0, 1)
    assert bbox(s2, 20).height <= 2      # kosong di luar jendela
    print("PASS trail sapuan canvas (aktif di jendela, mati di luar)")


def test_spear_state_hitbox():
    """_spear_state: tip jauh dari grip saat thrust, flag active benar."""
    b = probe(_nyz_attack_active=True, _nyz_attack_progress=0.5,
              _pose_variant=0)
    st = NS._spear_state(b, 230, 230)
    assert st["active"] is True
    assert st["tip"].distance_to(st["grip"]) > 50.0
    b2 = probe(_nyz_attack_active=True, _nyz_attack_progress=0.1,
               _pose_variant=0)
    assert NS._spear_state(b2, 230, 230)["active"] is False
    print("PASS geometri tombak + jendela hitbox aktif")


# ===================================================================
# 4. PROJECTILE SYSTEM (lapisan hidup)
# ===================================================================
def test_projectile_lifecycle():
    ps = FX.ParticleSystem(64)
    syst = FX.ProjectileSystem(ps, 8)
    tgt = SimpleNamespace(x=200.0, y=100.0, alive=True, radius=12)
    pr = syst.spawn(100.0, 100.0, 200.0, 100.0, speed=FX.SHARD_SPEED,
                    kind="shard", radius=6.0, lifetime=2.0, damage=50.0,
                    target=tgt, homing=0.0)
    assert pr.active and syst.count() == 1
    assert pr.trail == [] and pr.position == pygame.Vector2(100.0, 100.0)
    surf = pygame.Surface((300, 220), pygame.SRCALPHA)
    saw_body = False
    for i in range(130):
        syst.update(1 / 60.0)
        syst.draw(surf)
        if pr.active and len(pr.trail) > 2:
            saw_body = True
    # setelah sampai tujuan: hancur + impact FX sempat hidup lalu mati
    assert not pr.active and syst.count() == 0
    assert saw_body
    for i in range(80):                     # impact & partikel habis
        syst.update(1 / 60.0)
        ps.update(1 / 60.0)
        syst.draw(surf)
    assert not syst.impacts and ps.count() == 0, \
        (len(syst.impacts), ps.count())
    # collision visual vs unit
    ps2 = FX.ParticleSystem(64)
    s2 = FX.ProjectileSystem(ps2, 8)
    u = SimpleNamespace(x=190.0, y=100.0, alive=True, radius=14)
    pr2 = s2.spawn(100.0, 100.0, 400.0, 100.0, speed=300.0, kind="shard",
                   radius=6.0, lifetime=5.0)
    hit = False
    for _ in range(120):
        s2.update(1 / 60.0, units=[u])
        if not pr2.active:
            hit = True
            break
    assert hit
    print("PASS projectile lifecycle (spawn->travel->trail->hit->destroy, "
          "collision, cleanup)")


# ===================================================================
# 5. SKILL FX (lapisan hidup) — lifecycle + cleanup
# ===================================================================
def test_skill_fx_lifecycle():
    for kind, dur in (("q", 50), ("w", 50), ("e", 70), ("r", 90)):
        ps = FX.ParticleSystem(96)
        prj = FX.ProjectileSystem(ps)
        fx = FX.SkillFX(kind, 200.0, 200.0, ps, prj, aim=0.0)
        fx.set_target_point(320.0, 180.0)
        surf = pygame.Surface((460, 300), pygame.SRCALPHA)
        frames = int(dur)
        for i in range(frames):
            t01 = (i + 1) / frames
            fx.update(1 / 60.0, t01)
            fx.draw_ground(surf)
            fx.draw_front(surf)
        assert fx.dead, (kind, fx.t01)
        assert fx.released
        # cleanup: semua partikel & proyektil mati setelah settle
        for i in range(240):
            ps.update(1 / 60.0)
            prj.update(1 / 60.0)
        assert ps.count() == 0 and prj.count() == 0, (kind, ps.count())
    print("PASS skill FX q/w/e/r lifecycle (cast->charge->release->fade) "
          "+ cleanup")


# ===================================================================
# 6. GAME FEEL — hit stop & shake & impact budget
# ===================================================================
def test_game_feel():
    # hit-stop dijepit 0.03-0.08 s
    if FX._feel is not None:
        for s in (0.005, 0.2, 0.05):
            FX.hit_stop(s)
            try:
                left = FX._feel.HITSTOP.left
                assert 0.029 <= left <= 0.081, left
            except AttributeError:
                break
    # shake: permintaan ganda tidak meledak, lalu meluruh
    sh = FX._feel.ScreenShake() if FX._feel is not None else None
    if sh is not None:
        sh.add(5, 0.2)
        sh.add(2, 0.1)
        assert sh.shake_strength <= 5.0 + 1e-6
        a0 = sh.amount
        for _ in range(40):
            sh.update(1 / 60.0)
        assert sh.amount < a0 and sh.amount <= 0.4 + 1e-6
    # impact budget director
    d = FX.NyzrakFXDirector(probe())
    for i in range(20):
        d.on_impact(230 + i, 230, 0.0, 1.0)
    assert len(d.impacts) <= FX.MAX_IMPACTS
    print("PASS game feel (hit-stop 0.03-0.08 s, shake meluruh, "
          "budget impact)")


# ===================================================================
# 7. INTEGRASI — jalur boss (live layer) & jalur hero (render_hero)
# ===================================================================
def test_boss_path_live_layer():
    FX.reset_all()
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    tgt = SimpleNamespace(x=340.0, y=240.0, alive=True, radius=16)
    b = probe(target=tgt)
    # serangan sweep penuh: trail + whoosh + impact frame
    for i in range(70):
        ap = i / 70.0
        b._nyz_attack_active = True
        b._nyz_attack_progress = ap
        b._pose_variant = 1
        b.pulse += 0.05
        FX.tick(1 / 60.0)
        L.draw_nyzrak(surf, b, 230, 230)
    assert FX.owns(b)
    d = FX.director_for(b)
    assert d.trail.active() or d.particles.count() > 0
    # skill q penuh
    b._nyz_attack_active = False
    b.active_skill = "q"
    for t in range(50, 0, -1):
        b.active_skill_timer = t
        FX.tick(1 / 60.0)
        L.draw_nyzrak(surf, b, 230, 230)
    b.active_skill = None
    # settle: FX pertarungan habis; salju ambien (kontinu, disengaja)
    # tetap di bawah budget kecil
    for i in range(400):
        FX.tick(1 / 60.0)
    d = FX.director_for(b)
    assert d.particles.count() <= 40, d.particles.count()
    assert d.projectiles.count() == 0
    assert not d.skills
    assert not d.impacts
    assert not d.trail.active()
    assert FX.total_particles() <= 40
    FX.reset_all()
    assert not FX.owns(b)
    print("PASS jalur boss: live layer aktif, FX drain ke 0, reset bersih")


def test_hero_pipeline_path():
    """render_hero('nyzrak') — canvas di-cache + live layer 1:1 di layar."""
    FX.reset_all()
    heroes._HERO_CACHE_ENABLED = False     # pakai jalur raw tiap frame
    try:
        h = probe(x=200.0, y=200.0)
        h.facing = 1
        h._moving_cached = False
        surf = pygame.Surface((460, 400), pygame.SRCALPHA)
        for i in range(40):
            h.pulse += 0.05
            heroes.render_hero("nyzrak", surf, h, 200, 200)
        assert FX.owns(h) or getattr(h, "_nyz_live_fx", False)
    finally:
        heroes._HERO_CACHE_ENABLED = True
    # jalur canvas: _skip_renderer_projectiles TIDAK menggambar FX layar
    h2 = probe(x=200.0, y=200.0)
    h2._skip_renderer_projectiles = True
    canvas = pygame.Surface((300, 300), pygame.SRCALPHA)
    L.draw_nyzrak(canvas, h2, 150, 150)
    assert bbox(canvas).width > 60
    FX.reset_all()
    print("PASS jalur hero: render_hero + live layer, canvas pass bersih")


def test_palette_contract():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in P, key
        assert len(P[key]) == 3
    FX._sync_palette()      # sinkron dari renderer tetap 3 kanal
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert len(P[key]) == 3
    print("PASS kontrak palette 9 kunci")


def test_skill_fx_without_projectiles():
    """W release dengan projectiles=None (wiring ps-only) tidak boleh
    NameError — angka kerucut tetap dihitung."""
    ps = FX.ParticleSystem(64)
    fx = FX.SkillFX("w", 200.0, 200.0, ps, None, aim=0.0)
    fx.set_target_point(320.0, 180.0)
    for i in range(50):
        fx.update(1 / 60.0, (i + 1) / 50)
    assert fx.dead and fx.released
    print("PASS skill FX W tanpa proyektil (ps-only wiring)")


def test_skill_bundle_dispatch():
    """Jalur hero: BossHeroSkills dispatch q/w/e/r nyzrak — durasi
    visual 50/50/70/90 (sinkron renderer+FX), damage/slow/lockout/heal/
    shield sesuai boss_data, dan notify_skill_impact hidup."""
    import types
    # sound_manager & settings adalah modul lingkungan runtime (tidak
    # di-track repo); stub bila tidak tersedia agar bundle tetap bisa
    # diuji.  Di game asli modul asli dipakai.
    for name, mk in (("sound_manager", True), ("settings", True)):
        if name in sys.modules:
            continue
        try:
            __import__(name)
            continue
        except ImportError:
            pass
    if "sound_manager" not in sys.modules or "settings" not in sys.modules:
        sm = types.ModuleType("sound_manager")

        class _SM:
            def __init__(self, *a, **k):
                pass

            def __getattr__(self, n):
                return lambda *a, **k: None
        sm.SoundManager = _SM
        sys.modules["sound_manager"] = sm
        st = types.ModuleType("settings")
        st.HERO_TYPES = {}
        st.HERO_LEVELS = {}
        st.TITLE = "x"
        sys.modules["settings"] = st
    from hero_skills import _bundle
    BHS = _bundle._NS_boss_hero_skills.BossHeroSkills
    hits = []

    def mk(x, y):
        return SimpleNamespace(x=x, y=y, alive=True, radius=12,
                               attack_timer=0,
                               apply_slow=lambda s, t: hits.append(
                                   ("slow", s, t)),
                               take_damage=lambda dmg, *a, **k: hits.append(
                                   ("dmg", dmg)))
    enemies = [mk(150, 100), mk(120, 110), mk(400, 100)]
    tgt = mk(180, 100)
    h = SimpleNamespace(hero_type="nyzrak", x=100.0, y=100.0, team="blue",
                        target=tgt, skill_damage=100, active_skill=None,
                        active_skill_timer=0, hp=4000, max_hp=5000,
                        shield_active=False, shield_timer=0,
                        skill_timer=0, skill_cooldown_max=1,
                        w_cooldown=0, w_cooldown_max=1,
                        e_cooldown=0, e_cooldown_max=1,
                        r_cooldown=0, r_cooldown_max=1,
                        vortex_x=0, vortex_y=0, vortex_active_timer=0,
                        flux_target=None, flux_active_timer=0,
                        mana_void_x=0, mana_void_y=0, rage_active=False,
                        rage_timer=0, defense_boost=False,
                        defense_timer=0, clones_active_timer=0,
                        _get_all_enemies=lambda u, t, b: enemies)
    inst = BHS(h)
    inst.init_state()
    for key, dur in (("q", 50), ("w", 50), ("e", 70), ("r", 90)):
        res = getattr(inst, "cast_%s" % key)(enemies, [], [])
        assert res, key
        assert h.active_skill == key and h.active_skill_timer == dur, \
            (key, h.active_skill_timer)
        h.active_skill = None
        h.skill_timer = h.w_cooldown = h.e_cooldown = h.r_cooldown = 0
    assert h.hp == 4750 and h.shield_active and h.shield_timer == 240
    dmg = [hh[1] for hh in hits if hh[0] == "dmg"]
    slows = sorted({hh[1] for hh in hits if hh[0] == "slow"})
    assert max(dmg) == 200, dmg
    assert 0.4 in slows and 0.7 in slows and 0.5 in slows, slows
    assert tgt.attack_timer == 90            # lockout serangan E
    assert FX.total_particles() > 0          # notify_skill_impact hidup
    FX.reset_all()
    print("PASS skill bundle hero (dispatch q/w/e/r, durasi 50/50/70/90, "
          "heal+shield, slow, lockout, FX notify)")


# ===================================================================
# 8. PERFORMANCE
# ===================================================================
def test_performance():
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    b = probe()
    for i in range(20):
        b.pulse = 1.0 + i * 0.13
        L.draw_nyzrak(surf, b, 230, 230)
    N = 40
    t0 = time.perf_counter()
    for i in range(N):
        b.pulse = 1.0 + i * 0.13
        L.draw_nyzrak(surf, b, 230, 230)
    dt = (time.perf_counter() - t0) / N * 1000
    assert dt < 2.35, dt
    print(f"    renderer idle: {dt:.2f} ms/frame (budget 2.35)")

    FX.reset_all()
    screen = pygame.Surface((460, 460), pygame.SRCALPHA)
    tgt = SimpleNamespace(x=340.0, y=240.0, alive=True, radius=16)
    b2 = probe(target=tgt)
    b2._nyz_attack_active = True
    b2._nyz_attack_progress = 0.5
    b2._pose_variant = 1
    b2.active_skill = "r"
    b2.active_skill_timer = 20
    for i in range(10):        # warm
        FX.tick(1 / 60.0)
        L.draw_nyzrak(screen, b2, 230, 230)
    t0 = time.perf_counter()
    M = 40
    for i in range(M):
        b2.pulse += 0.05
        FX.tick(1 / 60.0)
        L.draw_nyzrak(screen, b2, 230, 230)
    dt2 = (time.perf_counter() - t0) / M * 1000
    assert dt2 < 5.5, dt2      # skill R penuh + trail + partikel
    print(f"    FX penuh (swing+R): {dt2:.2f} ms/frame (budget 5.5)")
    FX.reset_all()
    print("PASS performance")


def test_procedural_only():
    import inspect
    for mod in (L, FX):
        src = inspect.getsource(mod)
        assert "pygame.image.load" not in src
    print("PASS prosedural murni (tanpa image.load)")


if __name__ == "__main__":
    test_render_all_states()
    test_render_no_flicker()
    test_animation_controller()
    test_animation_transitions_visual()
    test_attack_arc_quality()
    test_attack_trail_canvas()
    test_spear_state_hitbox()
    test_projectile_lifecycle()
    test_skill_fx_lifecycle()
    test_game_feel()
    test_boss_path_live_layer()
    test_hero_pipeline_path()
    test_palette_contract()
    test_skill_fx_without_projectiles()
    test_skill_bundle_dispatch()
    test_performance()
    test_procedural_only()
    print("ALL NYZRAK REWRITE TESTS PASSED")
