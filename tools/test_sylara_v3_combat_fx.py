#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression test permanen untuk sistem tempur SYLARA v3.

Sylara digambar lewat dua lapisan yang sengaja dipisah:

  * ``heroes/_bundle.py :: _NS_sylara`` = badan/rig/pose masterwork v2,
    timeline serangan v3 (``_update_attack_anim``), pose busur
    (``_bow_pose_local`` / ``_bow_geometry``), sapuan berbasis busur
    (``_swing_arc_pose``), telegraph tanah, skill body Q/W/E/R, overlay
    debug rig, dan seluruh FALLBACK kalau modul FX tidak tersedia.
  * ``heroes/sylara_fx.py``           = lapisan hidup 1:1 di luar sprite
    cache: pita sapuan busur dari histori posisi nyata, particle system
    (daun/bulu/gust/debu/serpihan), proyektil panah angin dengan
    lifecycle penuh, impact FX, siklon Windrun, sulur Shackle, gale
    Powershot, hit-stop, shake, overlay debug, dan animation controller
    cermin (state + prioritas + transisi).
  * ``heroes/combat_feel.py``         = bus SHARED (hit-stop + shake)
    yang dipakai Zephyr, Gornak, Grimjaw, Kaizen, Vex, dan Sylara, jadi
    beberapa karakter memukul di frame yang sama tidak menumpuk freeze.

Uji ini mengunci kontrak yang gampang rusak saat orang lain menyentuh
salah satu dari ketiganya:

 1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di kedua modul.
 2. Palet + API publik (backward-compat untuk pemanggil lama).
 3. Controller animasi: fase, urutan, delta-time, jendela ayunan,
    prioritas state, dan progress serangan 60 Hz dari attack_timer.
 4. Ayunan berbasis busur (bukan lerp linear) + trail dari histori busur.
 5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
 6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
 7. Lifecycle skill FX (cast -> charge -> release -> area -> after ->
    fade) dan pemicu gameplay (Q focus fire / W windrun / E shackle /
    R powershot).
 8. Impact + screen shake + hit-stop yang SELALU terkuras (tidak ada efek
    abadi), dengan hit-stop di 0.03-0.08 s.
 9. Supresi ganda: saat lapisan hidup mengambil alih, renderer tidak
    menggambar trail sapuan di-canvas dua kali - dan sebaliknya fallback
    canvas tetap jalan kalau modul FX tidak dimuat.
10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_sylara_v3_combat_fx.py -q
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import math                                            # noqa: E402
import time                                            # noqa: E402

import pygame                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import pytest                                          # noqa: E402

import heroes                                          # noqa: E402
from heroes import _ProbeEntity                        # noqa: E402
from heroes import combat_feel as FEEL                 # noqa: E402
from heroes import sylara_fx as F                      # noqa: E402
from heroes._bundle import _NS_sylara as G             # noqa: E402

DT = 1.0 / 60.0
SURF = pygame.Surface((760, 600), pygame.SRCALPHA)
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


# ── helper ────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _isolate():
    """Bersihkan registry director + bus game-feel antar tes."""
    F.reset_all()
    _clear_feel()
    yield
    F.reset_all()
    _clear_feel()


def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()


def fresh_hero(x=300.0, y=300.0, cooldown=52, target_dist=300.0):
    """Unit Sylara minim dengan seluruh atribut yang dibaca renderer + FX."""
    h = _ProbeEntity("sylara", x, y)
    h.direction = h.facing = 1
    h.alive = True
    h.pulse = 0.0
    h.timer = 0
    h.attack_timer = 0
    h.attack_cooldown = cooldown
    h.range = 130
    h.speed = 1.5
    h.hp = h.max_hp = 470
    h.radius = 16
    h.skill_damage = 95
    h.skill_range = 180
    h.active_skill = None
    h.active_skill_timer = 0
    h._focus_fire_active = False
    h._focus_fire_timer = 0
    h._windrun_active = False
    h._windrun_timer = 0
    h._shackle_active = False
    h._shackle_timer = 0
    h._shackle_target = None
    h._powershot_charging = False
    h._powershot_timer = 0
    h._sy_attack_active = False
    h._sy_attack_progress = 0.0
    h._sy_swing_mode = False
    h._render_scale = 0.62
    if target_dist is not None:
        t = _ProbeEntity("sylara", x + target_dist, y)
        t.alive = True
        t.radius = 14
        t.hp = t.max_hp = 400
        h.target = t
    else:
        h.target = None
    return h


def fresh_director(**kw):
    """Director yang TERDAFTAR (supaya notify_* memakai instance sama)."""
    h = fresh_hero(**kw)
    return h, F.director_for(h)


def run_attack(h, d, frames=None):
    """Jalankan satu serangan penuh lewat timeline attack_timer gameplay."""
    cd = h.attack_cooldown
    h.attack_timer = h.timer = cd
    for _ in range(frames or cd + 4):
        d.update(DT)
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    return d


def drain(d, seconds=5.0):
    for _ in range(int(seconds / DT)):
        d.update(DT)


def tick_timers(h, names=("_focus_fire_timer", "_windrun_timer",
                          "_shackle_timer", "_powershot_timer")):
    for n in names:
        v = int(getattr(h, n, 0) or 0)
        if v > 0:
            setattr(h, n, v - 1)


# ═══ 1. PROSEDURAL & API ══════════════════════════════════════════════════

def test_tidak_memuat_asset_eksternal():
    src = open(os.path.join(ROOT, "heroes", "sylara_fx.py"),
               encoding="utf-8").read()
    for banned in ("image.load", "pygame.image", ".png", ".jpg",
                   ".gif", "sprite_sheet", "spritesheet"):
        assert banned not in src, "sylara_fx.py memuat %r" % banned


def test_api_publik_lapisan_hidup():
    for name in ("SYLARA_PALETTE", "DEBUG_CHARACTER", "SYLARA_FX_ENABLED",
                 "MAX_PARTICLES", "MAX_PROJECTILES", "TRAIL_SAMPLES",
                 "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
                 "SylaraProjectile", "ProjectileSystem", "SkillFX",
                 "SylaraFXDirector", "draw_wind_arrow", "draw_debug_overlay",
                 "director_for", "attach", "owns", "tick", "reset_all",
                 "total_particles", "total_projectiles",
                 "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast", "notify_hurt",
                 "hit_stop", "shake", "should_freeze_frame",
                 "attack_phase", "bow_points", "swing_hitbox",
                 "render_scale", "clear_cache", "cache_size"):
        assert hasattr(F, name), "API hilang: %s" % name


def test_api_publik_renderer_tetap_ada():
    """Nama lama yang dipakai tooling/dokumen tidak boleh hilang."""
    for name in ("draw_sylara", "PALETTE", "RIG_SCALE",
                 "SKILL_VISUAL_DURATION", "_attack_pose",
                 "_draw_elite_bow", "_draw_elite_arrow", "_bow_nock",
                 "_bow_point", "_bow_frame", "_update_attack_anim",
                 "_draw_sylara_body", "_draw_sylara_rig"):
        assert hasattr(G, name), "API renderer hilang: %s" % name


def test_api_v3_renderer_lengkap():
    for name in ("ATTACK_ANTICIPATION_END", "ATTACK_WINDUP_END",
                 "ATTACK_SWING_END", "ATTACK_IMPACT_END",
                 "ATTACK_FOLLOW_END", "ATTACK_IMPACT_FRAME",
                 "ATTACK_ACTIVE_WINDOW", "SWING_WINDOW", "SWING_RANGE",
                 "ANIM_STATES", "DEBUG_CHARACTER", "_swing_arc_pose",
                 "_bow_pose_local", "_bow_geometry", "_bow_grip_local",
                 "_bow_tip_local", "_bow_nock_local", "_bow_release_local",
                 "_bow_trail_samples", "_draw_bow_swing_trail",
                 "_resolve_anim_state", "_swing_hitbox", "_draw_debug",
                 "live_fx_ready"):
        assert hasattr(G, name), "API v3 renderer hilang: %s" % name


def test_palet_kontrak_9_kunci():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.SYLARA_PALETTE
        assert len(F.SYLARA_PALETTE[key]) == 3


def test_palet_sinkron_dengan_renderer():
    F._sync_palette()
    assert F.P["fx_mid"] == tuple(G.PALETTE["wind_mid"][:3])
    assert F.P["weapon"] == tuple(G.PALETTE["wood_mid"][:3])
    assert F.P["leaf_gold"] == tuple(G.PALETTE["leaf_gold"][:3])


def test_debug_mode_ada_dan_mati_secara_default():
    assert F.DEBUG_CHARACTER is False
    assert G.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    assert F.HITSTOP is FEEL.HITSTOP
    assert F.SHAKE is FEEL.SHAKE


def test_sylara_terdaftar_di_live_fx_pass():
    assert "sylara" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS["sylara"] == "heroes.sylara_fx"
    assert heroes._live_fx_module("sylara") is F


def test_pose_variant_masuk_cache_key():
    """Sapuan melee vs tembakan TIDAK boleh berbagi entri cache."""
    a = fresh_hero()
    b = fresh_hero()
    a.attack_timer = b.attack_timer = 30
    a._pose_variant = 0
    b._pose_variant = 1
    assert heroes._hero_cache_key("sylara", a) != \
        heroes._hero_cache_key("sylara", b)


def test_bentuk_bukan_lingkaran_polos():
    """Panah & partikel harus berarah, bukan bulatan simetris."""
    s = pygame.Surface((90, 90), pygame.SRCALPHA)
    F.draw_wind_arrow(s, 45, 45, 0.0, age=6, kind="arrow", radius=6)
    left = sum(s.get_at((x, y))[3] for x in range(0, 45)
               for y in range(30, 60))
    right = sum(s.get_at((x, y))[3] for x in range(46, 90)
                for y in range(30, 60))
    assert left > right * 1.25, "panah tidak berarah (simetris)"


# ═══ 2. ANIMATION CONTROLLER ══════════════════════════════════════════════

def test_urutan_fase_ayunan_lengkap():
    seen = []
    for i in range(101):
        ph = F.attack_phase(i / 100.0)
        if not seen or seen[-1] != ph:
            seen.append(ph)
    assert seen == PHASE_ORDER


def test_fase_sinkron_dengan_konstanta_renderer():
    assert F.ATTACK_IMPACT_POINT == pytest.approx(G.ATTACK_IMPACT_FRAME)
    assert F.ATTACK_SWING_END == pytest.approx(G.ATTACK_SWING_END)
    assert (F.SWING_START, F.SWING_END) == tuple(G.SWING_WINDOW)
    assert F.attack_phase(G.ATTACK_ANTICIPATION_END - 0.01) == \
        "ANTICIPATION"
    assert F.attack_phase(G.ATTACK_IMPACT_FRAME + 0.01) == "IMPACT" or \
        F.attack_phase(G.ATTACK_IMPACT_FRAME + 0.01) == "SWING"


def test_progress_serangan_60hz_dari_attack_timer():
    h, d = fresh_director(cooldown=52)
    h.attack_timer = h.timer = 52
    seq = []
    for _ in range(52):
        d.update(DT)
        seq.append(d.attack_progress)
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert seq[0] < 0.05 and seq[-1] > 0.9
    assert all(b >= a - 1e-6 for a, b in zip(seq, seq[1:])), \
        "progress serangan harus monoton naik"


def test_state_machine_melewati_charge_lalu_attack():
    h, d = fresh_director(cooldown=52)
    h.attack_timer = h.timer = 52
    states = []
    for _ in range(52):
        d.update(DT)
        if not states or states[-1] != d.state:
            states.append(d.state)
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert "CHARGE" in states
    assert "ATTACK" in states


def test_state_swing_saat_mode_melee():
    h, d = fresh_director(cooldown=52, target_dist=40.0)
    h._sy_swing_mode = True
    h.attack_timer = h.timer = 52
    states = set()
    for _ in range(52):
        d.update(DT)
        states.add(d.state)
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert "SWING" in states


def test_director_yang_dibuat_di_tengah_ayunan_tetep_jalan():
    h = fresh_hero()
    h.attack_timer = h.timer = 30
    d = F.director_for(h)
    d.update(DT)
    assert d._attack_live is True


def test_prioritas_state_dan_kunci_death():
    h, d = fresh_director()
    d.update(DT)
    assert d.state == "IDLE"
    h.alive = False
    d.update(DT)
    assert d.state == "DEATH"
    h.alive = True                       # revive tidak boleh dipercaya
    h.attack_timer = h.timer = 52
    for _ in range(6):
        d.update(DT)
    assert d.state in ("DEATH", "CHARGE", "ATTACK")


def test_state_special_untuk_ultimate():
    h, d = fresh_director()
    h.active_skill = "r"
    h.active_skill_timer = 60
    d.update(DT)
    assert d.state == "SPECIAL"
    assert F.ANIM_PRIORITY["SPECIAL"] > F.ANIM_PRIORITY["SKILL"]
    assert F.ANIM_PRIORITY["DEATH"] == max(F.ANIM_PRIORITY.values())


def test_state_run_saat_windrun():
    h, d = fresh_director()
    h._windrun_active = True
    d.update(DT)
    assert d.state == "RUN"


def test_semua_state_wajib_ada():
    for name in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                 "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert name in F.ANIM_PRIORITY, "state hilang: %s" % name


def test_hurt_terdeteksi_dari_hp():
    h, d = fresh_director()
    d.update(DT)
    h.hp -= 60
    d.update(DT)
    assert d.hit_flash > 0.0
    assert d.state == "HURT"


def test_death_memicu_burst_sekali():
    h, d = fresh_director()
    d.update(DT)
    h.alive = False
    d.update(DT)
    n = d.particles.count()
    assert n > 8
    d.update(DT)
    assert d.particles.count() <= n + 1


def test_resolve_anim_state_renderer():
    h = fresh_hero()
    h.alive = False
    assert G._resolve_anim_state(h, False, "IDLE") == "DEATH"
    h.alive = True
    assert G._resolve_anim_state(h, True, "IDLE") in ("ATTACK", "SWING")


# ═══ 3. AYUNAN BERBASIS BUSUR + TRAIL ════════════════════════════════════

def test_ayunan_mengikuti_busur_bukan_lerp():
    """Kecepatan sudut harus berubah (anticipation lambat, strike cepat)."""
    angs = [G._swing_arc_pose(i / 40.0)["angle"] for i in range(41)]
    steps = [angs[i + 1] - angs[i] for i in range(40)]
    assert max(steps) - min(steps) > 0.05, "ayunan masih lerp linear"
    # radius pivot ikut memanjang saat menghantam (bobot)
    rs = [G._swing_arc_pose(i / 40.0)["radius"] for i in range(41)]
    assert max(rs) > min(rs) + 6.0


def test_arc_menyapu_dari_belakang_ke_depan():
    """Wind-up mengangkat limb ke belakang, lalu menyapu ke depan."""
    rest = G._swing_arc_pose(0.0)["angle"]
    back = G._swing_arc_pose(G.ATTACK_WINDUP_END)["angle"]
    fwd = G._swing_arc_pose(G.ATTACK_FOLLOW_END)["angle"]
    assert back < rest, "tidak ada anticipation ke belakang"
    assert fwd > back, "sapuan tidak bergerak maju"
    assert fwd > G.SWING_ARC_MID


def test_bow_points_layar_mengikuti_render_scale():
    h = fresh_hero()
    h._render_scale = 0.62
    (g1, t1, _n1), _a = F.bow_points(h, progress=0.5)
    h._render_scale = 1.24
    (g2, t2, _n2), _a = F.bow_points(h, progress=0.5)
    d1 = math.hypot(t1[0] - h.x, t1[1] - h.y)
    d2 = math.hypot(t2[0] - h.x, t2[1] - h.y)
    assert d2 > d1 * 1.7, "geometri busur tidak ikut skala render"


def test_trail_dibangun_dari_histori_dan_meluruh():
    tr = F.SwingTrail(samples=6)
    for i in range(12):
        tr.push((i * 3.0, 40.0), (i * 3.0 + 22.0, 12.0))
    assert len(tr.points) == 6, "cap histori tidak dihormati"
    tr.draw(SURF)
    for _ in range(int(tr.life / DT) + 4):
        tr.update(DT)
    assert not tr.points and not tr.active


def test_trail_diisi_lapisan_hidup_saat_swing():
    h, d = fresh_director(cooldown=52)
    h.attack_timer = h.timer = 52
    best = 0
    for _ in range(52):
        d.update(DT)
        best = max(best, len(d.trail.points))
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert best >= 6, "trail tidak terisi dari histori busur"


def test_trail_menempel_di_limb_busur():
    """Sample trail harus dekat garis grip->tip, bukan mengambang."""
    h, d = fresh_director(cooldown=52)
    h.attack_timer = h.timer = 52
    for _ in range(24):
        d.update(DT)
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert d.trail.points
    base, tip, _age = d.trail.points[-1]
    (grip, btip, _nock), _a = F.bow_points(h, progress=d.attack_progress)
    limb = math.hypot(btip[0] - grip[0], btip[1] - grip[1])
    # pangkal pita berada di 30% limb, ujung di 122% limb
    assert math.hypot(base[0] - grip[0], base[1] - grip[1]) < limb * 0.6
    assert math.hypot(tip[0] - grip[0], tip[1] - grip[1]) > limb * 0.9


def test_swing_hitbox_di_depan_karakter():
    h = fresh_hero()
    h.facing = h.direction = 1
    r = F.swing_hitbox(h)
    assert r.left >= h.x - 1 and r.width == int(G.SWING_RANGE)
    h.facing = h.direction = -1
    r2 = F.swing_hitbox(h)
    assert r2.right <= h.x + 1


def test_hitbox_renderer_hanya_saat_jendela_hit_aktif():
    h = fresh_hero()
    h._sy_hit_active = False
    assert G._swing_hitbox(h, 100, 100) is None
    h._sy_hit_active = True
    rect = G._swing_hitbox(h, 100, 100)
    assert rect.width > 0 and rect.height > 0
    assert rect.left >= 100 - 1                     # menghadap kanan
    assert F.swing_hitbox(h).width == int(G.SWING_RANGE)


# ═══ 4. PARTICLE SYSTEM ══════════════════════════════════════════════════

def test_pool_dipakai_ulang_dan_cap_dihormati():
    ps = F.ParticleSystem(cap=20)
    ps.burst(50, 50, 500, life=(0.05, 0.06))
    assert ps.count() <= 20
    for _ in range(20):
        ps.update(DT)
    assert ps.count() == 0
    assert len(ps._pool) > 0, "pool tidak dipakai ulang"


def test_partikel_meluruh_tanpa_sisa():
    ps = F.ParticleSystem()
    ps.burst(60, 60, 30, life=(0.1, 0.3))
    for _ in range(60):
        ps.update(DT)
    assert ps.count() == 0
    assert not ps.alive()


def test_partikel_punya_kontrak_atribut_lengkap():
    p = F.Particle().spawn(1, 2, 3, 4, 0.5, 3, (10, 20, 30))
    for a in ("pos", "vel", "acc", "life", "max_life", "size", "rotation",
              "rotation_speed", "alpha", "gravity", "color", "active"):
        assert hasattr(p, a)


def test_burst_menghormati_anggaran_kualitas():
    ps = F.ParticleSystem()
    real = F.particle_budget
    try:
        F.particle_budget = lambda: 0.0
        assert ps.burst(10, 10, 40) == 0
        F.particle_budget = lambda: 0.5
        ps.clear()
        n = ps.burst(10, 10, 40, life=(1.0, 1.0))
        assert 15 <= n <= 25
    finally:
        F.particle_budget = real


def test_semua_bentuk_partikel_bisa_digambar():
    ps = F.ParticleSystem()
    for shape in ("pixel", "spark", "leaf", "feather", "streak", "gust",
                  "splinter", "smoke", "glow", "grass"):
        ps.clear()
        ps.spawn(120, 120, 30, -20, 0.5, 4, F.P["fx_light"], shape=shape)
        ps.update(DT)
        ps.draw(SURF)


def test_ring_dan_stream():
    ps = F.ParticleSystem()
    assert ps.ring(200, 200, 60, 12) > 0
    ps.clear()
    assert ps.stream(100, 100, 300, 120, 10) > 0
    ps.update(DT)
    ps.draw(SURF)


def test_partikel_daun_bergoyang_bukan_jatuh_lurus():
    p = F.Particle().spawn(0, 0, 0, 0, 1.0, 3, F.P["leaf_gold"],
                           shape="leaf", flutter=1.0)
    xs = []
    for _ in range(30):
        p.update(DT)
        xs.append(p.pos.x)
    assert max(xs) - min(xs) > 0.001


def test_lapisan_depan_belakang_terpisah():
    ps = F.ParticleSystem()
    ps.spawn(10, 10, 0, 0, 1.0, 3, F.P["dust"], back=True)
    ps.spawn(20, 20, 0, 0, 1.0, 3, F.P["fx_mid"], back=False)
    ps.draw(SURF, layer="back")
    ps.draw(SURF, layer="front")
    assert ps.count() == 2


# ═══ 5. PROJECTILE ═══════════════════════════════════════════════════════

def test_lifecycle_projectile_spawn_travel_hit_destroy():
    ps = F.ParticleSystem()
    sys_ = F.ProjectileSystem(ps)
    tgt = _ProbeEntity("sylara", 260.0, 200.0)
    tgt.alive = True
    tgt.radius = 14
    pr = sys_.spawn(100, 200, 260, 200, target=tgt, speed=400.0)
    assert pr.state == pr.STATE_TRAVEL
    x0 = pr.position.x
    for _ in range(6):
        sys_.update(DT)
    assert pr.position.x > x0 and pr.trail
    for _ in range(120):
        sys_.update(DT)
        if pr.state != pr.STATE_TRAVEL:
            break
    assert pr.state in (pr.STATE_IMPACT, pr.STATE_DEAD)
    for _ in range(30):
        sys_.update(DT)
    assert sys_.count() == 0


def test_projectile_punya_kontrak_atribut():
    pr = F.SylaraProjectile(0, 0, 10, 0)
    for a in ("position", "velocity", "speed", "damage", "lifetime",
              "target", "radius", "rotation", "trail", "particles",
              "active"):
        assert hasattr(pr, a)


def test_projectile_cap_dihormati():
    sys_ = F.ProjectileSystem(None, cap=3)
    for _ in range(10):
        sys_.spawn(0, 0, 100, 0)
    assert sys_.count() == 3


def test_projectile_expire_tanpa_target():
    sys_ = F.ProjectileSystem(F.ParticleSystem())
    sys_.spawn(0, 0, 100, 0, lifetime=0.2)
    for _ in range(60):
        sys_.update(DT)
    assert sys_.count() == 0


def test_projectile_homing_membelok_ke_target():
    tgt = _ProbeEntity("sylara", 300.0, 120.0)
    tgt.alive = True
    tgt.radius = 12
    pr = F.SylaraProjectile(0, 300, 300, 300, target=tgt, homing=6.0,
                            speed=300.0)
    for _ in range(20):
        pr.update(DT)
    assert pr.direction.y < -0.05, "homing tidak membelok"


def test_projectile_digambar_tanpa_error():
    ps = F.ParticleSystem()
    for kind in ("arrow", "gale", "vine"):
        pr = F.SylaraProjectile(100, 100, 300, 160, kind=kind,
                                particles=ps)
        for _ in range(8):
            pr.update(DT)
        pr.draw(SURF)


def test_draw_wind_arrow_prosedural_dan_berarah():
    s = pygame.Surface((100, 100), pygame.SRCALPHA)
    F.draw_wind_arrow(s, 50, 50, math.pi / 2, age=3, radius=6)
    up = sum(s.get_at((x, y))[3] for x in range(35, 65)
             for y in range(0, 50))
    dn = sum(s.get_at((x, y))[3] for x in range(35, 65)
             for y in range(51, 100))
    assert up > dn * 1.2


def test_release_panah_di_frame_impact():
    h, d = fresh_director(cooldown=52)
    h.attack_timer = h.timer = 52
    fired = 0
    for _ in range(52):
        d.update(DT)
        fired = max(fired, d.projectiles.count())
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert fired >= 1, "panah tidak pernah dilepas"
    assert d._arrow_released is True


def test_mode_sapuan_tidak_melepas_panah():
    h, d = fresh_director(cooldown=52, target_dist=40.0)
    h._sy_swing_mode = True
    h.attack_timer = h.timer = 52
    hit = 0
    for _ in range(52):
        d.update(DT)
        hit = max(hit, len(d.impacts))
        assert d.projectiles.count() == 0
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert hit >= 1, "sapuan melee tidak menghasilkan impact"


# ═══ 6. SKILL FX ═════════════════════════════════════════════════════════

def test_skill_q_dari_active_skill():
    h, d = fresh_director()
    h.active_skill = "q"
    h.active_skill_timer = 180
    d.update(DT)
    assert d.skills and d.skills[0].skill == "q"
    assert d.particles.count() > 0


def test_skill_w_windrun_dari_timer_gameplay():
    h, d = fresh_director()
    d.update(DT)
    h._windrun_active = True
    h._windrun_timer = 180
    d.update(DT)
    assert any(s.skill == "w" for s in d.skills)


def test_skill_e_mengikuti_target():
    h, d = fresh_director()
    tgt = h.target
    h._shackle_target = tgt
    h.active_skill = "e"
    h.active_skill_timer = 150
    d.update(DT)
    fx = [s for s in d.skills if s.skill == "e"][0]
    assert fx.target is tgt
    tgt.x += 60
    for _ in range(10):
        d.update(DT)
    d.draw_ground(SURF)
    d.draw_front(SURF)


def test_skill_r_powershot_melepas_gale():
    h, d = fresh_director()
    h.active_skill = "r"
    h.active_skill_timer = 60
    d.update(DT)
    fx = [s for s in d.skills if s.skill == "r"][0]
    for _ in range(int(F.SKILL_TOTAL["r"] * 0.7 / DT)):
        d.update(DT)
    assert fx._released is True
    assert d.projectiles.count() >= 3, "kerucut 5 panah tidak keluar"


def test_semua_fase_lifecycle_skill():
    ps = F.ParticleSystem()
    fx = F.SkillFX("q", 100, 100, ps, projectiles=F.ProjectileSystem(ps))
    seen = []
    while fx.active:
        fx.update(DT)
        if not seen or seen[-1] != fx.phase:
            seen.append(fx.phase)
    assert seen[:3] == ["CAST", "CHARGE", "RELEASE"]
    assert "AREA" in seen and "AFTER" in seen and "FADE" in seen


def test_skill_tidak_hidup_selamanya():
    h, d = fresh_director()
    for skill in ("q", "w", "e", "r"):
        h.active_skill = skill
        h.active_skill_timer = 180
        d.update(DT)
        h.active_skill = None
        drain(d, F.SKILL_TOTAL[skill] + 1.0)
        assert not d.skills, "skill %s tidak pernah mati" % skill


def test_skill_dibersihkan_waktu_timer_macet_di_mayat():
    h, d = fresh_director()
    h._shackle_timer = 150
    d.update(DT)
    assert d.skills
    h.alive = False
    for _ in range(6):
        d.update(DT)
    assert not d.skills


def test_semua_skill_bisa_digambar_dua_lapis():
    h, d = fresh_director()
    for skill in ("q", "w", "e", "r"):
        h.active_skill = skill
        h.active_skill_timer = 120
        d.update(DT)
        h.active_skill = None
        for _ in range(20):
            d.update(DT)
            d.draw_ground(SURF)
            d.draw_front(SURF)


# ═══ 7. IMPACT / SHAKE / HIT-STOP ════════════════════════════════════════

def test_impact_memicu_shake_dan_hitstop_terukur():
    h, d = fresh_director()
    _clear_feel()
    d.on_impact(h.x + 40, h.y, 0.0, 1.2, False, "arrow")
    assert FEEL.SHAKE.amount > 0.0
    assert FEEL.HITSTOP.frames > 0
    assert d.impacts and d.particles.count() > 5


def test_hitstop_dijepit_di_rentang_aman():
    _clear_feel()
    F.hit_stop(5.0)
    assert FEEL.HITSTOP.frames <= FEEL.HITSTOP.MAX_FRAMES
    _clear_feel()
    F.hit_stop(0.0001)
    assert FEEL.HITSTOP.frames >= 2


def test_shake_meluruh_bertahap():
    _clear_feel()
    F.shake(10.0, 0.3)
    a0 = FEEL.SHAKE.amount
    for _ in range(6):
        FEEL.SHAKE.update(DT)
    a1 = FEEL.SHAKE.amount
    assert 0.0 < a1 < a0
    for _ in range(60):
        FEEL.SHAKE.update(DT)
    assert FEEL.SHAKE.amount == 0.0


def test_impact_tidak_hidup_selamanya():
    h, d = fresh_director()
    for i in range(30):
        d.on_impact(h.x + i, h.y, 0.0, 1.0)
    assert len(d.impacts) <= F.MAX_IMPACTS
    drain(d, 3.0)
    assert not d.impacts


def test_semua_jenis_impact_bisa_digambar():
    for kind in ("arrow", "gale", "vine", "swing", "crit"):
        fx = F.ImpactFX(300, 300, 0.7, 1.3, kind == "crit", kind)
        while fx.active:
            fx.draw(SURF)
            fx.update(DT)


def test_notify_api_tetap_ada_untuk_kompatibilitas():
    h, d = fresh_director()
    F.notify_projectile_impact(h, h.x + 50, h.y, 0.3, 45, True)
    F.notify_melee_impact(h, h.target, 45, False)
    F.notify_skill_impact(h, h.x + 30, h.y, 120, "q")
    F.notify_skill_cast(h, "w")
    F.notify_hurt(h, 0.4)
    assert d.impacts or d.skills or d.particles.count()


# ═══ 8. SUPRESI GANDA (renderer vs lapisan hidup) ════════════════════════

def test_attach_menandai_unit_dan_owns():
    h = fresh_hero()
    assert F.owns(h) is False
    assert F.attach(h) is True
    assert F.owns(h) is True


def test_release_membersihkan_penanda():
    h = fresh_hero()
    F.attach(h)
    d = F.director_for(h)
    F._release(d)
    assert getattr(h, "_sy_fx", None) is None
    assert F.owns(h) is False


def test_renderer_melewati_trail_saat_dimiliki_lapisan_hidup():
    """Trail canvas hanya digambar kalau lapisan hidup TIDAK aktif."""
    h = fresh_hero(target_dist=40.0)
    h._sy_swing_mode = True
    calls = {"n": 0}
    real = G._draw_bow_swing_trail

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)
    try:
        G._draw_bow_swing_trail = spy
        surf = pygame.Surface((260, 240), pygame.SRCALPHA)
        h._sy_attack_progress = 0.5
        G._FX_LIVE.v = False
        G._draw_sylara_attack(surf, h, 130, 140)
        without = calls["n"]
        G._FX_LIVE.v = True
        G._draw_sylara_attack(surf, h, 130, 140)
        with_live = calls["n"] - without
    finally:
        G._draw_bow_swing_trail = real
        G._FX_LIVE.v = False
    assert without >= 1, "fallback canvas tidak pernah jalan"
    assert with_live == 0, "trail digambar dua kali (canvas + hidup)"


def test_fallback_canvas_tetap_jalan_tanpa_modul_fx():
    """Unit tanpa director harus tetap memakai jalur canvas lama."""
    h = fresh_hero()
    assert G._fx_live_owned(h) is False
    surf = pygame.Surface((260, 240), pygame.SRCALPHA)
    G._draw_sylara_body(surf, 130, 140, 1, 1.0, "attack", 0.5)
    assert surf.get_bounding_rect().width > 0


def test_render_hero_penuh_dengan_lapisan_hidup():
    h = fresh_hero()
    F.attach(h)
    surf = pygame.Surface((700, 600), pygame.SRCALPHA)
    h.attack_timer = h.timer = 52
    for _ in range(30):
        F.director_for(h).update(DT)
        heroes.render_hero("sylara", surf, h, 300, 300)
        h.attack_timer -= 1
        h.timer = h.attack_timer
    assert surf.get_bounding_rect().width > 0


# ═══ 9. DEBUG OVERLAY ════════════════════════════════════════════════════

def test_debug_overlay_tidak_crash():
    h, d = fresh_director(cooldown=40)
    h.attack_timer = h.timer = 40
    h._focus_fire_timer = 180
    h._windrun_timer = 180
    h._shackle_timer = 150
    h._shackle_target = h.target
    h._powershot_timer = 60
    for _ in range(20):
        d.update(DT)
        h.attack_timer -= 1
        h.timer = h.attack_timer
    old = F.DEBUG_CHARACTER
    try:
        F.DEBUG_CHARACTER = True
        d.draw_front(SURF)
        F.draw_debug_overlay(SURF, d)
    finally:
        F.DEBUG_CHARACTER = old


def test_debug_overlay_renderer_tidak_crash():
    h = fresh_hero()
    h._sy_state = "ATTACK"
    surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    G._draw_debug(surf, h, 200, 200, "ATTACK")


def test_stats_dan_reset_all():
    h = fresh_hero()
    d = F.director_for(h)
    st = d.stats()
    for key in ("state", "phase", "attack_t", "particles", "projectiles",
                "impacts", "skills", "trail"):
        assert key in st
    F.reset_all()
    assert F.total_particles() == 0
    assert F.total_projectiles() == 0
    assert getattr(h, "_sy_fx", None) is None


def test_clear_cache():
    F.glow_surface(9, (10, 20, 30), 0.5)
    assert F.cache_size() > 0
    F.clear_cache()
    assert F.cache_size() == 0


def test_tick_tidak_maju_dua_kali_di_frame_yang_sama():
    h = fresh_hero()
    d = F.director_for(h)
    # "Frame yang sama" ditentukan guard `now == _LAST_TICK_MS`, dan `now`
    # berasal dari pygame.time.get_ticks() yang resolusinya milidetik.
    # Kalau dua tick() kebetulan jatuh di sisi berbeda dari batas
    # milidetik, tick kedua sah dianggap frame BARU dan ikut maju --
    # test jadi gagal ~0.05% run tanpa ada yang salah di kodenya.
    # Patok jamnya supaya yang diuji benar-benar guard-nya.
    import pygame as _pg
    _real = _pg.time.get_ticks
    _pg.time.get_ticks = lambda: 100000
    try:
        F.tick()
        t1 = d.time
        F.tick()
        assert d.time == t1
    finally:
        _pg.time.get_ticks = _real


def test_advance_per_unit_bukan_kuadratik():
    """10 unit -> 10 pembaruan director per frame, bukan 10 x 10."""
    F.reset_all()
    hs = []
    for i in range(10):
        h = fresh_hero(x=100.0 + i * 40, y=200.0)
        hs.append((h, F.director_for(h)))
    marks = []
    for h, d in hs:
        before = d.frames
        F._advance(d)
        marks.append(d.frames - before)
    assert all(m <= 1 for m in marks)


# ═══ 10. PERFORMA ════════════════════════════════════════════════════════

def test_lapisan_hidup_cukup_murah():
    """8 unit Sylara bertempur penuh harus jauh di bawah budget 60 fps."""
    F.reset_all()
    _clear_feel()
    hs = []
    for i in range(8):
        h = fresh_hero(x=100.0 + (i % 4) * 150, y=120.0 + (i // 4) * 260,
                       cooldown=52)
        h.attack_timer = h.timer = 52
        hs.append((h, F.director_for(h)))
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)

    def step(i):
        for h, d in hs:
            if i % h.attack_cooldown == 0:
                h.attack_timer = h.timer = h.attack_cooldown
            if h.attack_timer > 0:
                h.attack_timer -= 1
                h.timer = h.attack_timer
            if i % 180 == 0:
                h._windrun_timer = 180
            if h._windrun_timer > 0:
                h._windrun_timer -= 1
            d.update(DT)
        surf.fill((0, 0, 0, 0))
        for _h, d in hs:
            d.draw_ground(surf)
        for _h, d in hs:
            d.draw_front(surf)

    for i in range(120):
        step(i)                       # warm-up (cache surface terisi)
    t0 = time.perf_counter()
    for i in range(180):
        step(i)
    el = (time.perf_counter() - t0) / 180.0 * 1000.0
    per_unit = el / 8.0
    assert per_unit < 2.5, "lapisan hidup terlalu mahal: %.2f ms/unit" \
        % per_unit
    F.reset_all()


def test_tidak_ada_efek_abadi_setelah_pertarungan():
    F.reset_all()
    hs = []
    for i in range(4):
        h = fresh_hero(x=100.0 + i * 120, y=200.0)
        d = F.director_for(h)
        hs.append((h, d))
        h.attack_timer = h.timer = 52
        h._focus_fire_timer = 180
        h._windrun_timer = 180
        h._shackle_timer = 150
        h._shackle_target = h.target
        h._powershot_timer = 60
    for _i in range(400):
        for h, d in hs:
            tick_timers(h)
            if h.attack_timer > 0:
                h.attack_timer -= 1
                h.timer = h.attack_timer
            d.update(DT)
    for h, d in hs:
        h.alive = False          # hentikan emisi ambien (daun idle)
        drain(d, 6.0)
    for h, d in hs:
        assert d.particles.count() == 0
        assert d.projectiles.count() == 0
        assert not d.skills
        assert not d.impacts
        assert not d.trail.points
    assert F.total_particles() == 0
    F.reset_all()


if __name__ == "__main__":                          # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))
