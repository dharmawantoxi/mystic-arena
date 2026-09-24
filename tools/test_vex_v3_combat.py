#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression test permanen untuk sistem tempur VEX v3.

Vex digambar lewat dua lapisan yang sengaja dipisah:

  * ``heroes/_bundle.py :: _NS_vex`` = badan/rig/pose masterwork v2,
    controller animasi serangan (``_update_attack_anim``), telegraph
    tanah, skill body besar (conduit Q / gerhana W / flux R), dan semua
    FALLBACK kalau modul FX tidak tersedia.
  * ``heroes/vex_fx.py``            = lapisan hidup 1:1 di luar sprite
    cache: arc ayunan staff dari histori posisi nyata, partikel, proyektil
    serpihan void, impact FX, spike crystal W, kurungan astral E, ledakan
    Essence Flux R, hit-stop, shake, overlay debug, dan animation
    controller cermin (state + prioritas + transisi).
  * ``heroes/combat_feel.py``       = bus SHARED (hit-stop + shake) yang
    dipakai Zephyr, Gornak, Grimjaw, Kaizen, dan Vex, jadi beberapa
    karakter memukul di frame yang sama tidak menumpuk freeze.

Uji ini mengunci kontrak yang gampang rusak saat orang lain menyentuh
salah satu dari ketiganya:

 1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di kedua modul.
 2. Palet + API publik (backward-compat untuk pemanggil lama).
 3. Controller animasi: fase, urutan, delta-time, jendela ayunan,
    prioritas state, dan progress serangan 60 Hz dari attack_timer.
 4. Ayunan berbasis busur (bukan lerp linear) + trail dari histori staff.
 5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
 6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
 7. Lifecycle skill FX (cast -> charge -> release -> area -> impact ->
    fade) dan pemicu gameplay (Q orb / W eclipse / E prison / R flux).
 8. Impact + screen shake + hit-stop yang SELALU terkuras (tidak ada efek
    abadi), dengan hit-stop di 0.03-0.08 s.
 9. Supresi ganda: saat lapisan hidup mengambil alih, renderer tidak
    menggambar smear ayunan di-canvas dua kali - dan sebaliknya fallback
    canvas tetap jalan kalau modul FX tidak dimuat.
10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_vex_v3_combat.py -q
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
from heroes import vex_fx as F                         # noqa: E402
from heroes._bundle import _NS_vex as G                # noqa: E402

DT = 1.0 / 60.0
SURF = pygame.Surface((720, 560), pygame.SRCALPHA)
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


def fresh_hero(x=200.0, y=200.0, cooldown=46):
    """Unit Vex minim dengan seluruh atribut yang dibaca renderer + FX."""
    h = _ProbeEntity("vex", x, y)
    h.direction = h.facing = 1
    h.alive = True
    h.pulse = 0.0
    h.timer = 0
    h.attack_timer = 0
    h.attack_cooldown = cooldown
    h.range = 130
    h.speed = 1.3
    h.hp = h.max_hp = 520
    h.radius = 16
    h.skill_damage = 95
    h.skill_range = 250
    h.target = None
    h._sanity_eclipse_active = False
    h._sanity_eclipse_timer = 0
    h._astral_prison_active = False
    h._astral_prison_timer = 0
    h._astral_prison_target = None
    h._essence_flux_active = False
    h._essence_flux_timer = 0
    h._vx_attack_active = False
    h._vx_attack_progress = 0.0
    h._render_scale = 0.62
    return h


def fresh_director(**kw):
    """Director yang TERDAFTAR (supaya notify_* memakai instance sama)."""
    h = fresh_hero(**kw)
    d = F.director_for(h)
    return h, d


def run_swing(h, d, frames=None):
    """Jalankan satu ayunan penuh lewat timeline attack_timer gameplay."""
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


def tick_timers(h, names=("_sanity_eclipse_timer", "_astral_prison_timer",
                          "_essence_flux_timer")):
    for n in names:
        v = int(getattr(h, n, 0) or 0)
        if v > 0:
            setattr(h, n, v - 1)


# ═══ 1. PROSEDURAL & API ══════════════════════════════════════════════════

def test_tidak_memuat_asset_eksternal():
    src = open(os.path.join(ROOT, "heroes", "vex_fx.py"),
               encoding="utf-8").read()
    for banned in ("image.load", "pygame.image", ".png", ".jpg",
                   ".gif", "sprite_sheet", "spritesheet"):
        assert banned not in src, "vex_fx.py memuat %r" % banned


def test_api_publik_lapisan_hidup():
    for name in ("VEX_PALETTE", "DEBUG_CHARACTER", "VEX_FX_ENABLED",
                 "MAX_PARTICLES", "MAX_PROJECTILES", "TRAIL_SAMPLES",
                 "MAX_IMPACTS", "MAX_SKILLS", "WORLD_RADIUS",
                 "SKILL_TOTAL", "SKILL_DUR",
                 "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
                 "VexProjectile", "ProjectileSystem", "SkillFX",
                 "VexFXDirector", "HITSTOP", "SHAKE",
                 "hit_stop", "shake", "should_freeze_frame",
                 "attack_phase", "ANIM_PRIORITY", "ATTACK_PHASES",
                 "render_scale", "staff_points", "swing_hitbox",
                 "draw_arcane_orb", "rotated_cached",
                 "glow_surface", "spark_surface", "ring_surface",
                 "ellipse_ring_surface", "ground_glow_surface",
                 "faceted_orb_surface", "rune_surface",
                 "crystal_shard_surface", "chevron_surface",
                 "dashed_ring_surface",
                 "director_for", "attach", "owns", "tick", "reset_all",
                 "total_particles", "total_projectiles",
                 "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast",
                 "notify_hurt", "draw_debug_overlay",
                 "clear_cache", "cache_size"):
        assert hasattr(F, name), "API hilang: %s" % name


def test_api_publik_renderer_tetap_ada():
    for name in ("PALETTE", "draw_vex", "draw_boss",
                 "ArcaneOrbProjectile", "AstralOrbProjectile",
                 "_orb_tip_local", "_staff_grip_local",
                 "_staff_butt_local", "_staff_orb_position",
                 "_attack_pose", "_draw_staff_smear",
                 "_update_attack_anim", "_manage_projectiles",
                 "_live_module", "_fx_live_owned", "_FX_LIVE",
                 "ATTACK_WINDUP_END", "ATTACK_SWING_END", "ATTACK_IMPACT",
                 "RIG_SCALE", "SKILL_VISUAL_DURATION"):
        assert hasattr(G, name), "API renderer hilang: %s" % name


def test_palet_kontrak_9_kunci():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.VEX_PALETTE
        col = F.VEX_PALETTE[key]
        assert len(col) == 3 and all(0 <= c <= 255 for c in col)


def test_palet_sinkron_dengan_renderer():
    F._sync_palette()
    assert tuple(F.P["fx_mid"]) == tuple(G.PALETTE["void_light"][:3])
    assert tuple(F.P["astral_mid"]) == tuple(G.PALETTE["astral_mid"][:3])


def test_debug_mode_ada_dan_mati_secara_default():
    assert F.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    assert F.HITSTOP is FEEL.HITSTOP
    assert F.SHAKE is FEEL.SHAKE
    assert F.FIXED_DT == FEEL.FIXED_DT


def test_vex_terdaftar_di_live_fx_pass():
    assert "vex" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS["vex"] == "heroes.vex_fx"
    mod = heroes._live_fx_module("vex")
    assert mod is F


def test_bentuk_bukan_lingkaran_polos():
    """Bahasa bentuk Vex: orb bersegi, rune, kristal, chevron, sabit."""
    orb = F.faceted_orb_surface(10, (255, 255, 255), (60, 200, 200),
                                (140, 240, 240), (220, 255, 255))
    assert orb.get_width() == orb.get_height() == 26
    alphas = pygame.surfarray.pixels_alpha(orb)
    filled = int((alphas > 40).sum())
    circle_area = math.pi * 10 * 10
    # segi-8 luasnya ~0.9 x lingkaran berdiameter sama -> bukan cakram penuh
    assert 0.55 * circle_area < filled < 1.20 * circle_area
    del alphas
    for maker in (F.rune_surface, F.chevron_surface,
                  F.crystal_shard_surface, F.dashed_ring_surface):
        assert maker is not None


# ═══ 2. ANIMATION CONTROLLER ═════════════════════════════════════════════

def test_urutan_fase_ayunan_lengkap():
    seen = []
    for i in range(101):
        ph = F.attack_phase(i / 100.0)
        if not seen or seen[-1] != ph:
            seen.append(ph)
    assert seen == PHASE_ORDER


def test_fase_sinkron_dengan_konstanta_renderer():
    assert abs(F.ATTACK_SWING_END - G.ATTACK_SWING_END) < 1e-6
    assert abs(F.ATTACK_IMPACT_POINT - G.ATTACK_IMPACT) < 1e-6
    assert F.attack_phase(G.ATTACK_WINDUP_END - 0.01) == "WINDUP"
    assert F.attack_phase(G.ATTACK_WINDUP_END + 0.01) == "SWING"


def test_progress_serangan_60hz_dari_attack_timer():
    h, d = fresh_director(cooldown=40)
    h.attack_timer = h.timer = 40
    d.update(DT)
    assert d._attack_live
    ps = []
    for _ in range(40):
        h.attack_timer -= 1
        h.timer = h.attack_timer
        d.update(DT)
        if not d._attack_live:
            break
        ps.append(d.attack_progress)
    assert all(b >= a for a, b in zip(ps, ps[1:]))
    assert ps[-1] >= 0.95
    assert not d._attack_live


def test_director_yang_dibuat_di_tengah_ayunan_tetep_jalan():
    """Unit yang muncul saat ayunan sudah berjalan tidak boleh beku."""
    h, d = fresh_director(cooldown=40)
    h.attack_timer = h.timer = 20        # sudah di tengah ayunan
    d.update(DT)
    assert d._attack_live
    assert d.attack_progress > 0.4


def test_prioritas_state_dan_kunci_death():
    for name in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST",
                 "SKILL", "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert name in F.ANIM_PRIORITY
    h, d = fresh_director()
    h.alive = False
    d.update(DT)
    assert d.state == "DEATH"
    h._is_dashing = True
    for _ in range(10):
        d.update(DT)
    assert d.state == "DEATH"


def test_state_skill_ultimate_paling_tinggi():
    h, d = fresh_director()
    h.active_skill = "r"
    d.update(DT)
    assert d.state == "SPECIAL"
    # transisi TURUN prioritas butuh state_time > 0.05 s (anti flicker)
    h.active_skill = "w"
    for _ in range(6):
        d.update(DT)
    assert d.state == "SKILL"
    h.active_skill = None
    h._essence_flux_timer = 30
    d.update(DT)
    assert d.state == "SPECIAL"


def test_hurt_terdeteksi_dari_hp():
    h, d = fresh_director()
    d.update(DT)
    h.hp -= 60
    d.update(DT)
    assert d.hit_flash > 0.0
    assert d.particles.count() > 0


def test_death_memicu_burst_sekali():
    _clear_feel()
    h, d = fresh_director()
    d.update(DT)
    h.alive = False
    d.update(DT)
    n1 = d.particles.count()
    assert n1 > 0
    d.update(DT)
    assert d.particles.count() <= n1 + 1


# ═══ 3. SWING & TRAIL ════════════════════════════════════════════════════

def test_orb_staff_mengikuti_busur_bukan_lerp():
    """Orb staff harus melengkung: deviasi dari garis lurus > ambang."""
    p0 = G._orb_tip_local(0.0, "attack", 0.30)
    p1 = G._orb_tip_local(0.0, "attack", 0.70)
    max_dev = 0.0
    for i in range(1, 20):
        t = 0.30 + 0.40 * i / 20.0
        px, py = G._orb_tip_local(0.0, "attack", t)
        lx = p0[0] + (p1[0] - p0[0]) * (i / 20.0)
        ly = p0[1] + (p1[1] - p0[1]) * (i / 20.0)
        max_dev = max(max_dev, math.hypot(px - lx, py - ly))
    assert max_dev > 4.0, "lintasan orb nyaris lurus (%.2f px)" % max_dev


def test_staff_points_layar_mengikuti_render_scale():
    h = fresh_hero()
    h._render_scale = 1.0
    (b1, g1, o1), _ = F.staff_points(h, progress=0.5)
    h._render_scale = 0.5
    (b2, g2, o2), _ = F.staff_points(h, progress=0.5)
    L1 = math.hypot(o1[0] - g1[0], o1[1] - g1[1])
    L2 = math.hypot(o2[0] - g2[0], o2[1] - g2[1])
    assert abs(L2 - L1 * 0.5) < 1.0
    # pangkal -> gagang -> orb harus segaris (satu batang staff)
    def cross(a, b, c):
        return ((b[0] - a[0]) * (c[1] - a[1])
                - (b[1] - a[1]) * (c[0] - a[0]))
    assert abs(cross(b1, g1, o1)) < 1.0


def test_trail_dibangun_dari_histori_dan_meluruh():
    tr = F.SwingTrail()
    for i in range(8):
        tr.push((100 + i * 4, 100), (140 + i * 4, 80))
    assert tr.active and len(tr.points) == 8
    tr.draw(SURF)
    for _ in range(60):
        tr.update(DT)
    assert not tr.active and not tr.points


def test_trail_diisi_lapisan_hidup_saat_swing():
    h, d = fresh_director(cooldown=46)
    h.attack_timer = h.timer = 46
    peak = 0
    released = False
    for _ in range(50):
        d.update(DT)
        peak = max(peak, len(d.trail.points))
        if d.impacts:
            released = True
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    assert peak >= 8, "trail tidak pernah terbangun (%d sample)" % peak
    assert released, "orb tidak pernah dilepas di titik IMPACT"
    # trail ikut memudar setelah ayunan selesai
    drain(d, 1.0)
    assert not d.trail.points


def test_trail_menempel_di_orb_staff():
    """Sample terakhir trail harus dekat dengan posisi orb saat itu."""
    h, d = fresh_director(cooldown=46)
    h._render_scale = 1.0
    h.attack_timer = h.timer = 46
    checked = False
    for _ in range(50):
        d.update(DT)
        # hanya diuji SELAMA swing: sample lama yang belum kedaluwarsa
        # tidak lagi mengikuti pose (itu wajar, itu inti "stored old pos").
        if (len(d.trail.points) >= 3
                and F.SWING_START <= d.attack_progress <= F.SWING_END):
            (_b, grip, orb), _a = F.staff_points(
                h, progress=d.attack_progress)
            tip = d.trail.points[-1][1]
            dist = math.hypot(tip.x - orb[0], tip.y - orb[1])
            # pita sengaja melewati orb ~30% panjang setengah staff
            # (outer = grip + 1.30 * (orb - grip)) supaya smear terbaca,
            # jadi batasnya diturunkan dari geometri, bukan angka ajaib.
            half = math.hypot(orb[0] - grip[0], orb[1] - grip[1])
            # pita sengaja melewati orb 30% panjang setengah staff
            # (outer = grip + 1.30 * (orb - grip)) + toleransi satu frame
            # karena sample terakhir dicatat sebelum pose digeser.
            batas = 0.30 * half + 12.0
            assert dist < batas, \
                "trail melenceng %.1f px dari orb (batas %.1f)" \
                % (dist, batas)
            checked = True
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    assert checked


def test_swing_hitbox_di_depan_karakter():
    h = fresh_hero()
    r = F.swing_hitbox(h)
    assert r.x >= h.x - 1 and r.width == h.range
    h.facing = h.direction = -1
    r2 = F.swing_hitbox(h)
    assert r2.x < h.x and r2.width == h.range


# ═══ 4. PARTICLE SYSTEM ══════════════════════════════════════════════════

def test_pool_dipakai_ulang_dan_cap_dihormati():
    ps = F.ParticleSystem(cap=8)
    for i in range(60):
        ps.spawn(10.0, 10.0, 1.0, 1.0, 0.4, 2.0, F.P["fx_light"])
    assert ps.count() == 8
    ps.update(DT)
    ps.clear()
    assert ps.count() == 0
    assert len(ps._pool) >= 8          # dikembalikan, bukan dibuang


def test_partikel_meluruh_tanpa_sisa():
    ps = F.ParticleSystem(cap=64)
    ps.burst(100.0, 100.0, 30, life=(0.1, 0.3))
    assert ps.count() > 0
    for _ in range(120):
        ps.update(DT)
    assert ps.count() == 0


def test_partikel_punya_kontrak_atribut_lengkap():
    p = F.Particle()
    for name in ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color"):
        assert hasattr(p, name), "atribut partikel hilang: %s" % name


def test_burst_menghormati_anggaran_kualitas():
    class _Q(object):
        particles = False
        particle_ratio = 0.0
        glow = True
        screen_shake = True
    import heroes.vex_fx as _f
    old = _f._quality
    try:
        _f._quality = lambda: _Q
        ps = F.ParticleSystem(cap=64)
        assert ps.burst(0.0, 0.0, 20) == 0
        assert ps.count() == 0
    finally:
        _f._quality = old


def test_semua_bentuk_partikel_bisa_digambar():
    ps = F.ParticleSystem(cap=64)
    for shape in ("pixel", "spark", "shard", "streak", "mote", "smoke",
                  "glow", "rune", "crystal"):
        ps.spawn(60.0, 60.0, 40.0, -20.0, 0.5, 3.0, F.P["fx_light"],
                 shape=shape, rotation=0.7, rotation_speed=4.0)
    ps.update(DT)
    for p in ps._live:
        p.draw(SURF)                    # tidak boleh raise


def test_ring_dan_stream():
    ps = F.ParticleSystem(cap=80)
    assert ps.ring(100.0, 100.0, 40.0, 12) > 0
    assert ps.ring(100.0, 100.0, 40.0, 12, inward=True, back=True) > 0
    assert ps.stream(0.0, 0.0, 80.0, 40.0, 8) > 0
    ps.update(DT)
    ps.draw(SURF, layer="back")
    ps.draw(SURF, layer="front")


# ═══ 5. PROJECTILE SYSTEM ════════════════════════════════════════════════

def test_basic_attack_melepaskan_orb_bertema_hero():
    """Serangan dasar Vex menembakkan orb void dari ujung staff ke target.

    Kontrak owner: "saya mau ada projectile saat melakukan basic
    attack, projectile nya menyesuaikan heronya" — director meluncurkan
    VexProjectile kind ``"orb"`` (glyph ``draw_arcane_orb``, identitas Vex)
    dari ujung staff di titik rilis ayunan.  Orb ini MURNI VISUAL
    (damage 0): damage tetap pakai jalur homing generik ``_entity``.
    """
    h, d = fresh_director()
    tgt = _ProbeEntity("dummy", 520.0, 200.0)
    tgt.radius = 16
    tgt.alive = True
    h.target = tgt
    run_swing(h, d)
    assert d.projectiles.count() == 1, \
        "basic attack harus meluncurkan tepat satu orb visual"
    orb = d.projectiles.projectiles[0]
    assert orb.kind == "orb"
    assert orb.damage == 0
    assert orb.target is tgt
    # Berangkat dari dekat orb staff (bukan titik acak dunia).
    (_b, _g, tip), _a = F.staff_points(h, progress=F.ATTACK_IMPACT_POINT)
    assert orb.spawn_pos.distance_to(
        pygame.Vector2(float(tip[0]), float(tip[1]))) < 40.0
    # Kecepatan awal mengarah ke target (bukan arah acak).
    dvec = pygame.Vector2(orb.target.x - orb.spawn_pos.x,
                          orb.target.y - orb.spawn_pos.y)
    assert dvec.length_squared() > 1.0
    assert abs(orb.velocity.angle_to(dvec)) < 45.0


def test_orb_basic_attack_tidak_diluncurkan_saat_skill_timer_aktif():
    """Ayunan skill tidak menambah orb basic attack (skill punya jalurnya)."""
    h, d = fresh_director()
    tgt = _ProbeEntity("dummy", 520.0, 200.0)
    tgt.radius = 16
    tgt.alive = True
    h.target = tgt
    h.skill_timer = 30
    run_swing(h, d)
    assert d.projectiles.count() == 0


def test_touchdown_orb_basic_attack_tanpa_paket_impact():
    """Arrival orb serangan dasar = percikan lembut saja (tanpa impact FX).

    Kontrak owner (tools/test_basic_attack_no_impact_fx.py): touchdown
    orb serangan dasar TIDAK boleh hit-stop, TIDAK boleh shake, dan
    TIDAK menambah ImpactFX.
    """
    SimpleClass = type("_TouchdownCmd", (), {})
    cmd = SimpleClass()
    cmd.hit_pos = pygame.Vector2(260.0, 200.0)

    h, d = fresh_director()
    before_impacts = len(d.impacts)
    _clear_feel()
    d._attack_orb_touchdown(cmd)
    assert len(d.impacts) == before_impacts
    assert FEEL.HITSTOP.frames == 0
    assert FEEL.SHAKE.shake_strength <= 0.0


def test_lifecycle_projectile_spawn_travel_hit_destroy():
    h, d = fresh_director()
    tgt = _ProbeEntity("vex", 420.0, 200.0)
    tgt.radius = 16
    tgt.alive = True
    pr = d.projectiles.spawn(200.0, 200.0, 420.0, 200.0, speed=400.0,
                             radius=6.0, kind="shard", target=tgt)
    assert pr is not None and pr.active
    assert pr.state == F.VexProjectile.STATE_TRAVEL
    hit = False
    for _ in range(120):
        d.projectiles.update(DT)
        if pr.state != F.VexProjectile.STATE_TRAVEL:
            hit = True
            break
    assert hit, "projectile tidak pernah mengenai target"
    # fase impact -> mati & dibuang
    for _ in range(60):
        d.projectiles.update(DT)
    assert pr.state == F.VexProjectile.STATE_DEAD
    assert d.projectiles.count() == 0


def test_projectile_punya_kontrak_atribut():
    pr = F.VexProjectile(0.0, 0.0, 100.0, 0.0)
    for name in ("position", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(pr, name), "atribut projectile hilang: %s" % name


def test_projectile_cap_dihormati():
    h, d = fresh_director()
    for i in range(F.MAX_PROJECTILES + 8):
        d.projectiles.spawn(0.0, 0.0, 100.0, 0.0, speed=50.0)
    assert d.projectiles.count() == F.MAX_PROJECTILES


def test_projectile_expire_tanpa_target():
    d = F.VexFXDirector(fresh_hero())
    pr = d.projectiles.spawn(0.0, 0.0, 400.0, 0.0, speed=40.0,
                             max_lifetime=0.4)
    for _ in range(120):
        d.projectiles.update(DT)
    assert pr.state == F.VexProjectile.STATE_DEAD
    assert d.projectiles.count() == 0


def test_projectile_digambar_tanpa_error():
    d = F.VexFXDirector(fresh_hero())
    d.projectiles.spawn(100.0, 100.0, 300.0, 140.0, speed=200.0,
                        radius=6.0, kind="shard")
    d.projectiles.spawn(100.0, 100.0, 300.0, 60.0, speed=200.0,
                        radius=6.0, kind="crystal")
    d.projectiles.spawn(100.0, 100.0, 300.0, 100.0, speed=200.0,
                        radius=7.0, kind="orb")
    for _ in range(8):
        d.projectiles.update(DT)
    d.projectiles.draw(SURF)


def test_draw_arcane_orb_prosedural_dan_berarah():
    a = pygame.Surface((120, 120), pygame.SRCALPHA)
    b = pygame.Surface((120, 120), pygame.SRCALPHA)
    F.draw_arcane_orb(a, 60, 60, 0.0, age=4, kind="attack", radius=8.0)
    F.draw_arcane_orb(b, 60, 60, math.pi, age=4, kind="skill", radius=8.0)
    na = int((pygame.surfarray.pixels_alpha(a) > 12).sum())
    nb = int((pygame.surfarray.pixels_alpha(b) > 12).sum())
    assert na > 100 and nb > 100
    # ekor mengarah ke belakang: piksel di belakang (kanan) untuk angle 0
    al = pygame.surfarray.pixels_alpha(a)
    depan = int((al[70:120, :] > 12).sum())
    belakang = int((al[0:50, :] > 12).sum())
    assert belakang > depan, "orb tidak memiliki ekor searah gerak"


# ═══ 6. SKILL FX ═════════════════════════════════════════════════════════

def test_skill_q_dari_active_skill():
    h, d = fresh_director()
    h.active_skill = "q"
    d.update(DT)
    assert len(d.skills) == 1 and d.skills[0].skill == "q"
    fx = d.skills[0]
    assert fx.phase() == "CAST"
    for _ in range(int(0.4 / DT)):
        d.update(DT)
    assert fx.impacted, "Q tidak pernah mencapai fase RELEASE"
    d.draw_ground(SURF)
    d.draw_front(SURF)


def test_skill_w_eclipse_berumur_panjang_dan_berdenyut():
    h, d = fresh_director()
    h._sanity_eclipse_timer = 180
    for _ in range(40):
        d.update(DT)
        tick_timers(h)
    assert any(s.skill == "w" for s in d.skills)
    fx = [s for s in d.skills if s.skill == "w"][0]
    assert fx._spikes, "eclipse tidak membangun spike"
    assert fx._tick_count >= 1, "eclipse tidak pernah tick damage"
    d.draw_ground(SURF)
    d.draw_front(SURF)
    # harus mati setelah durasinya habis (3.25 s)
    for _ in range(int(4.5 / DT)):
        d.update(DT)
    assert not any(s.skill == "w" for s in d.skills)


def test_skill_e_kurungan_mengikuti_target():
    h, d = fresh_director()
    tgt = _ProbeEntity("vex", 320.0, 200.0)
    h._astral_prison_target = tgt
    h._astral_prison_timer = 150
    for _ in range(30):
        d.update(DT)
        tick_timers(h)
    fx = [s for s in d.skills if s.skill == "e"]
    assert fx, "kurungan astral tidak pernah dibuat"
    assert abs(fx[0].x - tgt.x) < 2.0, "kurungan tidak menempel di target"
    tgt.x = 360.0
    d.update(DT)
    assert abs(fx[0].x - 360.0) < 2.0, "kurungan tidak mengikuti target"
    d.draw_ground(SURF)
    d.draw_front(SURF)


def test_skill_r_flux_meledak_dan_melempar_serpihan():
    _clear_feel()
    h, d = fresh_director()
    h._essence_flux_timer = 60
    for _ in range(46):
        d.update(DT)
        tick_timers(h)
    fx = [s for s in d.skills if s.skill == "r"]
    assert fx, "essence flux tidak pernah dibuat"
    assert fx[0].impacted, "flux tidak pernah meledak"
    assert d.projectiles.count() > 0, "flux tidak melempar serpihan"
    d.draw_ground(SURF)
    d.draw_front(SURF)
    # hit-stop & shake terasa
    assert FEEL.HITSTOP.frames >= 2


def test_semua_fase_lifecycle_skill():
    fx = F.SkillFX("w", 100.0, 100.0, F.ParticleSystem(16))
    seen = []
    for _ in range(int(F.SKILL_TOTAL["w"] / DT) + 2):
        if not fx.active:
            break
        ph = fx.phase()
        if not seen or seen[-1] != ph:
            seen.append(ph)
        fx.update(DT)
    assert seen == ["CAST", "CHARGE", "RELEASE", "AREA", "FADE"]
    assert not fx.active


def test_skill_tidak_hidup_selamanya():
    for sk, timer in (("w", 180), ("e", 150), ("r", 60)):
        h, d = fresh_director()
        if sk == "w":
            h._sanity_eclipse_timer = timer
        elif sk == "e":
            h._astral_prison_timer = timer
            h._astral_prison_target = _ProbeEntity("vex", 320.0, 200.0)
        else:
            h._essence_flux_timer = timer
        for i in range(timer + 60):
            d.update(DT)
            tick_timers(h)
        assert not d.skills, "skill %s tidak pernah dibersihkan" % sk
        h.alive = False          # hentikan emisi ambien (mote idle)
        drain(d, 4.0)
        assert d.particles.count() == 0


def test_skill_dibersihkan_waktu_timer_macet_di_mayat():
    """Pagar anti-beku: hero mati di tengah skill -> emisi berhenti."""
    h, d = fresh_director()
    h._sanity_eclipse_timer = 180
    for _ in range(20):
        d.update(DT)
    assert d.skills
    h.alive = False
    d.update(DT)
    # timer tidak pernah turun lagi -> setelah satu update FX dibuang
    for _ in range(4):
        d.update(DT)
    assert not d.skills


# ═══ 7. IMPACT / GAME FEEL ═══════════════════════════════════════════════

def test_impact_memicu_shake_dan_hitstop_terukur():
    _clear_feel()
    h, d = fresh_director()
    F.notify_projectile_impact(h, 260.0, 190.0, 0.0, 55, False)
    assert len(d.impacts) == 1
    assert FEEL.HITSTOP.frames >= 2
    assert FEEL.HITSTOP.frames <= FEEL.HITSTOP.MAX_FRAMES
    assert FEEL.SHAKE.shake_strength > 0.0
    assert FEEL.HITSTOP.MIN_SECONDS == 0.03
    assert FEEL.HITSTOP.MAX_SECONDS == 0.08
    d.draw_front(SURF)


def test_hitstop_dijepit_di_rentang_aman():
    _clear_feel()
    F.hit_stop(10.0)                 # sengaja keterlaluan
    assert 0.03 <= FEEL.HITSTOP.frames * F.FIXED_DT <= 0.09
    _clear_feel()
    F.hit_stop(0.0001)
    assert FEEL.HITSTOP.frames >= 2


def test_shake_meluruh_bertahap():
    _clear_feel()
    F.shake(9.0, 0.3)
    a0 = FEEL.SHAKE.amount
    FEEL.SHAKE.update(0.15)
    a1 = FEEL.SHAKE.amount
    FEEL.SHAKE.update(0.16)
    a2 = FEEL.SHAKE.amount
    assert a0 > a1 > a2
    assert a2 == 0.0


def test_impact_tidak_hidup_selamanya():
    h, d = fresh_director()
    F.notify_projectile_impact(h, 260.0, 190.0, 0.0, 55, False)
    h.alive = False
    drain(d, 4.0)
    assert not d.impacts
    assert d.particles.count() == 0


def test_semua_jenis_impact_bisa_digambar():
    for kind in ("orb", "astral", "spike", "flux", "crit"):
        fx = F.ImpactFX(120.0, 120.0, 0.4, 1.3, kind == "crit", kind)
        for _ in range(6):
            fx.update(DT)
            fx.draw(SURF)
        fx.draw(SURF)


def test_notify_melee_impact_tetap_ada_untuk_kompatibilitas():
    h, d = fresh_director()
    tgt = _ProbeEntity("vex", 260.0, 200.0)
    F.notify_melee_impact(h, tgt, 40, False)
    assert len(d.impacts) == 1
    F.notify_hurt(h, 0.3)
    assert d.hit_flash > 0.0
    F.notify_skill_cast(h, "q")
    assert any(s.skill == "q" for s in d.skills)
    F.notify_skill_impact(h, 300.0, 200.0, 120.0, "w")
    assert any(s.skill == "w" for s in d.skills)


# ═══ 8. SUPRESI GANDA (renderer vs lapisan hidup) ════════════════════════

def test_attach_menandai_unit_dan_owns():
    h = fresh_hero()
    assert F.attach(h) is True
    assert h._vx_live_fx is True
    assert h._skip_renderer_projectiles is True
    assert F.owns(h) is True


def test_release_membersihkan_penanda():
    h = fresh_hero()
    F.attach(h)
    d = F.director_for(h)
    F._release(d)
    assert getattr(h, "_vx_live_fx", False) is False
    assert getattr(h, "_skip_renderer_projectiles", False) is False
    assert F.owns(h) is False


def test_renderer_melewati_smear_saat_dimiliki_lapisan_hidup():
    h = fresh_hero()
    h._render_scale = 0.62
    canvas = pygame.Surface((360, 360), pygame.SRCALPHA)
    h._vx_attack_active = True
    h._vx_attack_progress = 0.5
    F.attach(h)
    G.draw_vex(canvas, h, 180, 180)
    assert G._FX_LIVE.v is True
    assert F.owns(h) is True


def test_fallback_canvas_tetap_jalan_tanpa_modul_fx():
    """Kalau lapisan hidup dimatikan, renderer menggambar smear sendiri."""
    h = fresh_hero()
    h._render_scale = 0.62
    h._vx_attack_active = True
    h._vx_attack_progress = 0.5
    h._vx_live_fx = False
    h._skip_renderer_projectiles = False
    try:
        h._vx_fx = None
    except Exception:
        pass
    canvas = pygame.Surface((360, 360), pygame.SRCALPHA)
    G.draw_vex(canvas, h, 180, 180)
    # tidak raise & canvas tetap terisi (rig + smear fallback)
    assert canvas.get_bounding_rect(min_alpha=8).width > 10


def test_renderer_projectiles_dilewati_saat_lapisan_hidup_aktif():
    h = fresh_hero()
    F.attach(h)
    assert h._skip_renderer_projectiles is True
    calls = {"n": 0}
    proj = G.ArcaneOrbProjectile(0, 0, 10, 10)

    def _boom(*a, **k):
        calls["n"] += 1
    proj.update = _boom
    h._vx_projectiles = [proj]
    G._manage_projectiles(h, pygame.Surface((40, 40), pygame.SRCALPHA), 0.0)
    assert calls["n"] == 0


# ═══ 9. DEBUG OVERLAY ════════════════════════════════════════════════════

def test_debug_overlay_tidak_crash():
    h, d = fresh_director(cooldown=40)
    h.attack_timer = h.timer = 40
    h._sanity_eclipse_timer = 90
    h._essence_flux_timer = 30
    h._astral_prison_timer = 60
    h._astral_prison_target = _ProbeEntity("vex", 260.0, 200.0)
    for _ in range(20):
        d.update(DT)
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    old = F.DEBUG_CHARACTER
    try:
        F.DEBUG_CHARACTER = True
        d.draw_front(SURF)
        F.draw_debug_overlay(SURF, d)
    finally:
        F.DEBUG_CHARACTER = old


def test_stats_dan_reset_all():
    h = fresh_hero()
    d = F.director_for(h)
    st = d.stats()
    for key in ("state", "phase", "attack_t", "particles",
                "projectiles", "impacts", "skills", "trail"):
        assert key in st
    F.reset_all()
    assert F.total_particles() == 0
    assert F.total_projectiles() == 0
    assert getattr(h, "_vx_fx", None) is None


def test_clear_cache():
    F.glow_surface(9, (10, 20, 30), 0.5)
    assert F.cache_size() > 0
    F.clear_cache()
    assert F.cache_size() == 0


def test_tick_tidak_maju_dua_kali_di_frame_yang_sama():
    h = fresh_hero()
    d = F.director_for(h)
    F.tick()                      # frame pertama: hanya mengisi stempel
    t1 = d.time
    F.tick()                      # milidetik yang sama -> dilewati
    assert d.time == t1


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
    # pada milidetik yang sama hanya director pertama yang boleh belum
    # punya stempel; sisanya tepat 0 atau 1 pembaruan
    assert all(m <= 1 for m in marks)
    assert sum(1 for m in marks if m == 1) <= 10


# ═══ 10. PERFORMA ════════════════════════════════════════════════════════

def test_lapisan_hidup_cukup_murah():
    """8 unit Vex bertempur penuh harus jauh di bawah budget 60 fps."""
    F.reset_all()
    _clear_feel()
    hs = []
    for i in range(8):
        h = fresh_hero(x=100.0 + (i % 4) * 150, y=120.0 + (i // 4) * 260,
                       cooldown=46)
        h.attack_timer = h.timer = 46
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
                h._sanity_eclipse_timer = 180
            if h._sanity_eclipse_timer > 0:
                h._sanity_eclipse_timer -= 1
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
    assert per_unit < 2.0, "lapisan hidup terlalu mahal: %.2f ms/unit" \
        % per_unit
    F.reset_all()


def test_tidak_ada_efek_abadi_setelah_pertarungan():
    F.reset_all()
    hs = []
    for i in range(4):
        h = fresh_hero(x=100.0 + i * 120, y=200.0)
        d = F.director_for(h)
        hs.append((h, d))
        h.attack_timer = h.timer = 46
        h._sanity_eclipse_timer = 180
        h._essence_flux_timer = 60
        h._astral_prison_timer = 150
        h._astral_prison_target = _ProbeEntity("vex", 300.0, 200.0)
    for i in range(400):
        for h, d in hs:
            tick_timers(h)
            if h.attack_timer > 0:
                h.attack_timer -= 1
                h.timer = h.attack_timer
            d.update(DT)
    for h, d in hs:
        h.alive = False          # hentikan emisi ambien (mote idle)
        drain(d, 6.0)
    for h, d in hs:
        assert d.particles.count() == 0
        assert d.projectiles.count() == 0
        assert not d.skills
        assert not d.impacts
        assert not d.trail.points
    assert F.total_particles() == 0
    F.reset_all()
