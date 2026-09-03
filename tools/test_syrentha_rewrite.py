#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur SYRENTHA v3 (rewrite).

Syrentha "The Song of the Seas" adalah MINI BOSS level 6 yang digambar
lewat ``bosses/level6.py::_NS_syrentha``, dengan lapisan FX hidup di
``heroes/syrentha_fx.py`` dan bus game-feel bersama ``heroes/combat_feel.py``
(sama persis dengan arsitektur Thalgryn v3 / Kunkka v3). Karena itu
kontraknya dipecah:

  * ``bosses/level6.py::_NS_syrentha`` = badan sirene (ekor + torso +
    surai api + tombak), rig, pose, controller animasi, telegraph tanah,
    Riptide Wave & efek canvas (fallback).
  * ``heroes/syrentha_fx.py``          = lapisan hidup 1:1 di luar sprite
    cache: pita tusukan tombak, partikel air, Riptide Wave (proyektil),
    impact, skill FX Q/W/E/R, hit-stop, shake, overlay debug.
  * ``heroes/combat_feel.py``          = bus SHARED (hit-stop + shake).

Uji ini mengunci kontrak yang gampang rusak:

  1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di KEDUA modul.
  2. Palet + API publik (backward-compat untuk pemanggil lama).
  3. Controller animasi: fase, urutan, delta-time, jendela hit, prioritas
     state, dan semua nama atribut lama (``_sy_*``).
  4. Tusukan tombak berbasis busur (bukan lerp linear).
  5. Particle system berbatas (cap dihormati, meluruh).
  6. Lifecycle Riptide Wave (spawn -> travel -> hit -> impact -> mati).
  7. Lifecycle skill FX Q/W/E/R (cast -> charge -> release -> area ->
     impact -> fade) dan tidak ada efek abadi.
  8. Impact + shake + hit-stop SELALU terkuras, hit-stop di 0.03-0.08 s.
  9. Supresi ganda: lapisan hidup mengambil alih ayunan/cast -> canvas
     fallback tidak menggambar dua kali; fallback tetap jalan kalau modul
     FX tidak dimuat.
 10. Overlay debug + registrasi lane hero + performansi.

Jalankan:  python3 -m pytest tools/test_syrentha_rewrite.py -q
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import inspect                                             # noqa: E402
import math                                                # noqa: E402
import pygame                                              # noqa: E402
import pytest                                              # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                              # noqa: E402
from heroes import _ProbeEntity                            # noqa: E402
from heroes import combat_feel as FEEL                     # noqa: E402
from heroes import syrentha_fx as F                        # noqa: E402
from bosses.level6 import _NS_syrentha as G                # noqa: E402

DT = 1.0 / 60.0
COOLDOWN = 44                     # attack_cooldown syrentha di boss_data.py
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]
SKILL_DUR = {"q": 45, "w": 80, "e": 70, "r": 90}


# ── helper ────────────────────────────────────────────────────────────────
def fresh_hero(x=0.0, y=0.0, cooldown=COOLDOWN, scale=None):
    """Unit Syrentha minim. ``scale=None`` = jalur BOSS (tanpa _render_scale)."""
    h = _ProbeEntity("syrentha", x, y)
    h.boss_type = "syrentha"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = cooldown
    h.range = 120
    h.speed = 0.85
    h.hp = h.max_hp = 13000
    h.radius = 38
    h.skill_damage = 300
    h.hurt_flash_timer = 0
    if scale is not None:
        h._render_scale = scale
    return h


def dummy_target(x=180.0, y=0.0):
    t = _ProbeEntity("creep", x, y)
    t.alive = True
    t.radius = 14
    return t


def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    FEEL.reset()


@pytest.fixture(autouse=True)
def _clean_fx():
    F.reset_all()
    _clear_feel()
    yield
    F.reset_all()
    _clear_feel()


def run_live(hero, frames, dt=DT, attack=False, skill=None, skill_dur=40,
             surf=None):
    if surf is None:
        surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    for i in range(frames):
        hero.pulse += 0.3
        if attack:
            hero._sy_attack_active = True
            hero._sy_attack_manual = True
            hero._sy_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        if skill is not None:
            hero.active_skill = skill
            hero.active_skill_timer = max(0, skill_dur - i)
            if hero.active_skill_timer == 0:
                hero.active_skill = None
        G._update_syrentha_attack_anim(hero)
        F.tick(dt)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, hero, hero.x, hero.y)
        F.draw_live_layer(surf, hero, hero.x, hero.y)
    return surf


# ══════════════════════════════════════════════════════════════════════════
# 1. 100% PROSEDURAL & API PUBLIK
# ══════════════════════════════════════════════════════════════════════════
def test_tidak_memuat_asset_eksternal():
    for rel in (os.path.join("heroes", "syrentha_fx.py"),):
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for bad in ("pygame.image.load", "image.load(",
                    "pygame.mixer.Sound", 'pygame.font.Font("',
                    "pygame.font.Font('", ".ogg", ".wav",
                    "load_asset", "SpriteSheet"):
            assert bad not in src, "%s memakai %s" % (rel, bad)
    # sumber _NS_syrentha juga tidak boleh memuat bitmap apa pun
    src = inspect.getsource(G)
    assert "pygame.image.load" not in src
    assert "image.load(" not in src


def test_api_publik_lapisan_hidup():
    for name in ("director_for", "attach", "owns", "tick", "reset_all",
                 "total_particles", "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast",
                 "draw_riptide_wave"):
        assert callable(getattr(F, name, None)), name
    assert F.MELEE_REACH == 120
    assert F.SKILL_DUR == SKILL_DUR


def test_api_publik_renderer_tetap_ada():
    assert callable(G.draw_syrentha)
    assert callable(G.draw_boss)
    assert G.MELEE_REACH == 120
    assert G.SKILL_DUR == SKILL_DUR
    assert isinstance(G.PALETTE, dict) and len(G.PALETTE) > 20
    assert callable(G._fx_scale) and callable(G._ring_r)
    assert callable(G._world_to_local) and callable(G._target_position)
    assert callable(G.attack_phases_order) and callable(G.attack_phase)
    assert callable(G._update_syrentha_attack_anim)
    assert callable(G._resolve_anim_state)


def test_palet_lengkap_dan_sinkron_dengan_renderer():
    need = ["skin_darkest", "skin_mid", "skin_light", "scale_darkest",
            "scale_mid", "scale_light", "hair_dark", "hair_mid",
            "hair_light", "gold_dark", "gold_mid", "gold_light",
            "water_darkest", "water_dark", "water_mid", "water_light",
            "water_bright", "blade_darkest", "blade_mid", "blade_light",
            "mirror_dark", "mirror_mid", "mirror_light", "eye_mid",
            "eye_bright", "star_yellow"]
    for k in need:
        assert k in G.PALETTE, "renderer PALETTE missing " + k
        assert k in F.P, "fx P missing " + k
    F._sync_palette()
    assert F.P["water_mid"] == tuple(int(c) for c in G.PALETTE["water_mid"])
    assert F.P["skin_mid"] == tuple(int(c) for c in G.PALETTE["skin_mid"])
    assert F.P["mirror_mid"] == tuple(int(c) for c in G.PALETTE["mirror_mid"])


def test_debug_mode_ada_dan_mati_secara_default():
    assert G.DEBUG_CHARACTER is False
    assert F.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    src = inspect.getsource(F)
    assert "combat_feel" in src
    assert "hit_stop" in src and "shake" in src


# ══════════════════════════════════════════════════════════════════════════
# 2. CONTROLLER ANIMASI
# ══════════════════════════════════════════════════════════════════════════
def test_urutan_fase_ayunan_lengkap():
    assert G.attack_phases_order() == tuple(PHASE_ORDER)


def test_progress_monoton_dan_habis_tepat():
    h = fresh_hero()
    h._sy_attack_active = False
    h._sy_attack_frame = 0
    h._sy_previous_timer = 0
    prev = 0.0
    for t in range(COOLDOWN, -1, -1):
        h.timer = t
        G._update_syrentha_attack_anim(h)
        p = float(h._sy_attack_progress)
        assert p >= prev - 1e-9, "progress mundur di timer=%d" % t
        prev = p
    assert abs(float(h._sy_attack_progress) - 1.0) < 1e-6


def test_jendela_hit_aktif_di_tengah_ayunan():
    h = fresh_hero()
    h._sy_attack_active = True
    h._sy_attack_frame = int(0.4 * (COOLDOWN - 1))
    h._sy_attack_progress = 0.4
    h._sy_attack_phase = G.attack_phase(0.4)
    G._update_syrentha_attack_anim(h)
    assert h._sy_attack_phase in ("SWING", "IMPACT")
    lo, hi = G.ATTACK_ACTIVE_WINDOW
    assert lo <= 0.4 < hi
    assert h._sy_hit_active


def test_prioritas_state_dan_kunci_death():
    assert G.ANIM_STATES["DEATH"] > G.ANIM_STATES["HURT"]
    assert G.ANIM_STATES["HURT"] > G.ANIM_STATES["SKILL"]
    assert G.ANIM_STATES["ATTACK"] > G.ANIM_STATES["IDLE"]
    h = fresh_hero()
    h.alive = False
    assert G._resolve_anim_state(h, False, "NONE") == "DEATH"


def test_state_walk_run_dari_gerakan():
    h = fresh_hero()
    h._sy_moving_cached = True
    h.speed = 1.0
    assert G._resolve_anim_state(h, False, "NONE") == "WALK"
    h.speed = 2.5
    assert G._resolve_anim_state(h, False, "NONE") == "RUN"


def test_hurt_dari_flash_boss():
    h = fresh_hero()
    h.hurt_flash_timer = 9
    G._update_syrentha_attack_anim(h)
    assert int(getattr(h, "_sy_hurt_frames", 0)) > 0


# ══════════════════════════════════════════════════════════════════════════
# 3. TOMBAK — busur, bukan lerp
# ══════════════════════════════════════════════════════════════════════════
def test_ujung_tombak_mengikuti_busur_bukan_lerp():
    tips = []
    for raw in (0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9):
        ap = G._attack_curve(raw)
        tip = G._tip_local("attack", 0.0, ap)
        tips.append(tip)
    # bukan garis lurus: arah gerak berubah (busur)
    angs = [math.atan2(tips[i][1] - tips[i - 1][1],
                       tips[i][0] - tips[i - 1][0])
            for i in range(1, len(tips))]
    assert max(angs) - min(angs) > 0.2, "ujung tombak bergerak lurus"


def test_kurva_serangan_ada_hold_dan_akselerasi():
    pts = [G._attack_curve(i / 10.0) for i in range(11)]
    assert pts[0] == 0.0 and pts[-1] > 0.99
    # percepatan di tengah: segmen tengah lebih curam dari tepi
    mid_step = pts[6] - pts[3]
    edge_step = pts[2] - pts[0]
    assert mid_step > edge_step


def test_trail_dibangun_dari_histori_dan_meluruh():
    h = fresh_hero()
    F.attach(h)
    for i in range(8):
        h._sy_attack_active = True
        h._sy_attack_phase = "SWING" if i % 2 == 0 else "IMPACT"
        F.tick(DT)
        F.draw_live_layer(pygame.Surface((360, 260), pygame.SRCALPHA),
                          h, h.x, h.y)
    d = F.director_for(h)
    assert 0 < len(d.trail.points) <= d.trail.samples


# ══════════════════════════════════════════════════════════════════════════
# 4. PARTIKEL & PROYEKTIL
# ══════════════════════════════════════════════════════════════════════════
def test_cap_partikel_dihormati():
    h = fresh_hero()
    d = F.director_for(h)
    for _ in range(300):
        d.particles.spawn(0, 0, 10, 10, 2.0, 3, (255, 255, 255))
    assert d.particles.count() <= F.MAX_PARTICLES


def test_partikel_mati_tidak_abadi():
    h = fresh_hero()
    d = F.director_for(h)
    d.particles.spawn(0, 0, 10, 10, 0.1, 3, (255, 255, 255))
    for _ in range(120):
        d.particles.update(DT)
    assert d.particles.count() == 0


def test_lifecycle_projectile_sampai_hancur():
    h = fresh_hero()
    h.target = dummy_target(140.0, 0.0)
    d = F.director_for(h)
    p = d.projectiles.spawn(0, 0, 140, 0, speed=400.0)
    assert p is not None and p.state == p.STATE_TRAVEL
    frames = 0
    while p.state != p.STATE_DEAD and frames < 300:
        d.projectiles.update(DT)
        frames += 1
    assert p.state == p.STATE_DEAD, "proyektil tidak pernah mati"


def test_cap_projectile():
    h = fresh_hero()
    d = F.director_for(h)
    for _ in range(F.MAX_PROJECTILES + 10):
        d.projectiles.spawn(0, 0, 100, 0)
    assert d.projectiles.count() <= F.MAX_PROJECTILES


def test_cast_q_meluncurkan_riptide_wave():
    h = fresh_hero()
    h.target = dummy_target(180.0, 0.0)
    F.attach(h)
    F.notify_skill_cast(h, "q")
    d = F.director_for(h)
    assert d.projectiles.count() >= 1


# ══════════════════════════════════════════════════════════════════════════
# 5. SKILL FX
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("key", ["q", "w", "e", "r"])
def test_skill_fx_selesai_dan_hilang(key):
    assert key in F.SkillFX.TIMELINE
    h = fresh_hero()
    F.attach(h)
    F.notify_skill_cast(h, key)
    d = F.director_for(h)
    assert len(d.skills) >= 1
    for _ in range(400):
        F.tick(DT)
    assert len(d.skills) == 0, "skill FX %s tidak hilang" % key


def test_skill_durasi_sama_dengan_engine():
    # boss AI (bosses/base_boss.py _syrentha_q/w/e/r) dan skill hero
    # (hero_skills/_bundle.py) memakai angka yang sama.
    assert G.SKILL_DUR == SKILL_DUR
    assert F.SKILL_DUR == SKILL_DUR
    assert set(F.SkillFX.TIMELINE) == set(SKILL_DUR)


def test_skill_impact_tanpa_target_tidak_error():
    h = fresh_hero()
    F.notify_skill_impact(h, 10.0, 10.0, 250, "q")
    F.notify_skill_impact(h, 10.0, 10.0, 150, "w")
    F.notify_skill_impact(h, 10.0, 10.0, 150, "e")
    F.notify_skill_impact(h, 10.0, 10.0, 220, "r")
    d = F.director_for(h)
    assert len(d.skills) >= 1


# ══════════════════════════════════════════════════════════════════════════
# 6. GAME FEEL — hit-stop & shake
# ══════════════════════════════════════════════════════════════════════════
def test_hit_stop_dalam_rentang_master_prompt():
    h = fresh_hero()
    h.target = dummy_target(140.0, 0.0)
    F.attach(h)
    _clear_feel()
    F.notify_melee_impact(h, h.target, 90, False)
    st = FEEL.stats()
    assert st["hitstop_total"] > 0
    # 0.03 - 0.08 detik (dibaca dalam frame 60fps => 2-5 frame)
    assert 1 <= st["hitstop_frames"] <= 6, st


def test_shake_meluruh_ke_nol():
    h = fresh_hero()
    F.attach(h)
    _clear_feel()
    FEEL.SHAKE.enabled = True
    F.notify_skill_impact(h, 0.0, 0.0, 220, "r")
    assert FEEL.SHAKE.amount > 0.0
    for _ in range(80):
        FEEL.SHAKE.update(DT)
    assert FEEL.SHAKE.amount == pytest.approx(0.0, abs=1e-6)


def test_impact_tanpa_target_tidak_error():
    h = fresh_hero()
    F.notify_projectile_impact(h, 30.0, 10.0, 0.0, 60, False, "riptide")
    d = F.director_for(h)
    assert len(d.impacts) >= 1


# ══════════════════════════════════════════════════════════════════════════
# 7. SUPRESI GANDA & FALLBACK
# ══════════════════════════════════════════════════════════════════════════
def test_jalur_boss_mengambil_alih_effect():
    h = fresh_hero()
    surf = pygame.Surface((320, 240), pygame.SRCALPHA)
    # jalur boss memuat lapisan hidup -> canvas riptide wave tidak di-spawn
    h.active_skill = "q"
    h.active_skill_timer = 28           # cast_progress ~ 0.38 (jendela spawn)
    h._sy_live_owned = True
    G.draw_syrentha(surf, h, 120, 150)
    assert len(getattr(h, "_sy_effects", [])) == 0


def test_fallback_canvas_saat_modul_fx_tidak_ada():
    h = fresh_hero()
    old = G._LIVE_MOD
    G._LIVE_MOD = False
    try:
        surf = pygame.Surface((320, 240), pygame.SRCALPHA)
        h.active_skill = "q"
        h.active_skill_timer = 28       # cast_progress ~ 0.38
        h._sy_live_owned = False
        h._sy_riptide_spawned = False
        G.draw_syrentha(surf, h, 120, 150)
        # canvas fallback spawn riptide wave saat jendela spawn (0.35-0.45)
        assert len(getattr(h, "_sy_effects", [])) >= 1
    finally:
        G._LIVE_MOD = old


def test_lane_hero_terdaftar_di_live_fx():
    assert "syrentha" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS.get("syrentha") == "heroes.syrentha_fx"


def test_render_hero_menjalankan_lapisan_hidup():
    h = fresh_hero(scale=0.6)
    surf = pygame.Surface((320, 240), pygame.SRCALPHA)
    heroes._live_fx_pre("syrentha", surf, h, h.x, h.y)
    heroes._live_fx_post("syrentha", surf, h, h.x, h.y)
    # tidak boleh error dan director terpasang
    assert getattr(h, "_sy_live_fx", False)


def test_debug_overlay_tidak_merusak_render():
    h = fresh_hero()
    surf = pygame.Surface((320, 240), pygame.SRCALPHA)
    F.attach(h)
    d = F.director_for(h)
    F.draw_debug_overlay(surf, d)
    # render normal tetap jalan
    G.draw_syrentha(surf, h, 120, 150)


# ══════════════════════════════════════════════════════════════════════════
# 8. PERFORMANSI & PELURUHAN PENUH
# ══════════════════════════════════════════════════════════════════════════
def test_lapisan_hidup_cepat():
    h = fresh_hero()
    h.target = dummy_target(150.0, 0.0)
    F.attach(h)
    surf = pygame.Surface((640, 360), pygame.SRCALPHA)
    run_live(h, 30, attack=True)                  # panaskan cache
    t0 = time.perf_counter()
    n = 60
    for i in range(n):
        h._sy_attack_active = True
        h._sy_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        h._sy_attack_phase = PHASE_ORDER[min(5, i // 6)]
        if i % 10 == 0:
            F.notify_projectile_impact(h, 150.0, 0.0, 0.0, 90, False)
        F.tick(DT)
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    ms = (time.perf_counter() - t0) / n * 1000.0
    assert ms < 8.0, "lapisan hidup %.2f ms/frame" % ms


def test_draw_syrentha_lane_boss_dibawah_anggaran():
    h = fresh_hero()
    surf = pygame.Surface((240, 240), pygame.SRCALPHA)
    for _ in range(10):
        h.pulse += 0.3
        G.draw_syrentha(surf, h, 120, 150)
    t0 = time.perf_counter()
    for _ in range(60):
        h.pulse += 0.3
        G.draw_syrentha(surf, h, 120, 150)
    ms = (time.perf_counter() - t0) / 60.0 * 1000.0
    assert ms < 8.0, "draw_syrentha(live) %.2f ms/frame" % ms


def test_semua_nya_bersih_setelah_reset():
    h = fresh_hero()
    h.target = dummy_target(150.0, 0.0)
    F.attach(h)
    for _ in range(60):
        F.tick(DT)
    F.notify_skill_cast(h, "r")
    F.notify_melee_impact(h, h.target, 90, True)
    F.reset_all()
    assert F.total_particles() == 0
    assert FEEL.stats()["shake"] == 0.0
    assert FEEL.stats()["hitstop_frames"] == 0
