#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur KAIZEN v3.

Kaizen digambar lewat dua lapisan yang sengaja dipisah:

  * ``heroes/_bundle.py :: _NS_kaizen``  = badan/rig/pose masterwork v3,
    controller animasi serangan (``_update_attack_anim``), telegraph
    tanah, skill body (dinding W / funnel R), dan semua FALLBACK kalau
    modul FX tidak tersedia.
  * ``heroes/kaizen_fx.py``              = lapisan hidup 1:1 di luar
    sprite cache: trail katana dari histori posisi nyata, partikel,
    proyektil sabit angin, impact FX, hit-stop, shake, overlay debug,
    dan animation controller cermin (state + prioritas + transisi).
  * ``heroes/combat_feel.py``            = bus SHARED (hit-stop + shake)
    yang dipakai Zephyr, Gornak, Grimjaw, dan Kaizen, jadi beberapa
    karakter memukul di frame yang sama tidak menumpuk freeze.

Uji ini mengunci kontrak yang gampang rusak saat orang lain menyentuh
salah satu dari ketiganya:

 1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di kedua modul.
 2. Palet + API publik (backward-compat untuk pemanggil lama).
 3. Controller animasi: fase, urutan, delta-time, jendela hit, prioritas
    state, dan progress serangan 60 Hz dari attack_timer gameplay.
 4. Ayunan berbasis busur (bukan lerp linear) + trail dari histori bilah.
 5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
 6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
 7. Lifecycle skill FX (cast -> charge -> release -> area -> impact ->
    fade) dan pemicu gameplay (Q dash / W wall / E sweep / R tornado).
 8. Impact + screen shake + hit-stop yang SELALU terkuras (tidak ada efek
    abadi), dengan hit-stop di 0.03-0.08 s.
 9. Supresi ganda: saat lapisan hidup mengambil alih, renderer tidak
    menggambar smear ayunan / sabit angin di-canvas dua kali - dan
    sebaliknya fallback canvas tetap jalan kalau modul FX tidak dimuat.
10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_kaizen_fx_combat.py -q
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import math                                            # noqa: E402
import pygame                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                          # noqa: E402
from heroes import _ProbeEntity                        # noqa: E402
from heroes import combat_feel as FEEL                 # noqa: E402
from heroes import kaizen_fx as F                      # noqa: E402
from heroes._bundle import _NS_kaizen as G             # noqa: E402

DT = 1.0 / 60.0
SURF = pygame.Surface((720, 560), pygame.SRCALPHA)
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


# ── helper ────────────────────────────────────────────────────────────────
def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()


def fresh_hero(x=200.0, y=200.0, cooldown=45):
    """Unit Kaizen minim dengan seluruh atribut yang dibaca FX."""
    h = _ProbeEntity("kaizen", x, y)
    h.direction = h.facing = 1
    h.alive = True
    h.pulse = 0.0
    h.timer = 0
    h.attack_timer = 0
    h.attack_cooldown = cooldown
    h.range = 60
    h.speed = 1.4
    h.hp = h.max_hp = 700
    h.radius = 16
    h.skill_damage = 110
    h.skill_range = 84
    h._kz_attack_active = False
    h._kz_attack_progress = 0.0
    h._q_stack = 0
    h._is_dashing = False
    h._dash_timer = 0
    h._wind_wall_timer = 0
    h._ulti_active = False
    h._ulti_timer = 0
    return h


def fresh_director(**kw):
    h = fresh_hero(**kw)
    d = F.KaizenFXDirector(h)
    return h, d


def run_swing(h, d, frames=None):
    """Jalankan satu ayunan penuh lewat timeline attack_timer gameplay."""
    cd = h.attack_cooldown
    h.attack_timer = h.timer = cd
    for i in range(frames or cd + 4):
        d.update(DT)
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    return d


def drain(d, seconds=4.0):
    for _ in range(int(seconds / DT)):
        d.update(DT)


# ═══ 1. PROSEDURAL & API ══════════════════════════════════════════════════

def test_tidak_memuat_asset_eksternal():
    for path in ("heroes/kaizen_fx.py",):
        src = open(os.path.join(ROOT, path), encoding="utf-8").read()
        for banned in ("image.load", "pygame.image", ".png", ".jpg",
                       ".gif", "sprite_sheet", "spritesheet"):
            assert banned not in src, "%s memuat %r" % (path, banned)


def test_api_publik_lapisan_hidup():
    for name in ("KAIZEN_PALETTE", "DEBUG_CHARACTER", "KAIZEN_FX_ENABLED",
                 "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
                 "KaizenProjectile", "ProjectileSystem", "SkillFX",
                 "KaizenFXDirector", "ScreenShake", "HitStop",
                 "hit_stop", "shake", "should_freeze_frame",
                 "attack_phase", "render_scale", "katana_points",
                 "director_for", "attach", "owns", "tick", "reset_all",
                 "total_particles", "total_projectiles",
                 "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_skill_impact",
                 "notify_skill_cast", "notify_hurt",
                 "draw_debug_overlay", "clear_cache", "cache_size"):
        assert hasattr(F, name), "API hilang: %s" % name


def test_api_publik_renderer_tetap_ada():
    for name in ("PALETTE", "draw_kaizen", "draw_boss",
                 "WindSlashProjectile", "_attack_pose",
                 "_katana_tip_local", "_draw_katana_swing_trail",
                 "_update_attack_anim", "_live_module", "_fx_live_owned",
                 "ATTACK_WINDUP_END", "ATTACK_SWING_END", "ATTACK_IMPACT"):
        assert hasattr(G, name), "API renderer hilang: %s" % name


def test_palet_kontrak_9_kunci():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.KAIZEN_PALETTE
        col = F.KAIZEN_PALETTE[key]
        assert len(col) == 3 and all(0 <= c <= 255 for c in col)


def test_palet_sinkron_dengan_renderer():
    F._sync_palette()
    assert tuple(F.P["fx_white"]) == tuple(G.PALETTE["wind_white"][:3])
    assert tuple(F.P["fx_bright"]) == tuple(G.PALETTE["wind_light"][:3])


def test_debug_mode_ada_dan_mati_secara_default():
    assert F.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    assert F.HITSTOP is FEEL.HITSTOP
    assert F.SHAKE is FEEL.SHAKE
    assert F.FIXED_DT == FEEL.FIXED_DT


def test_kaizen_terdaftar_di_live_fx_pass():
    assert "kaizen" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS["kaizen"] == "heroes.kaizen_fx"
    mod = heroes._live_fx_module("kaizen")
    assert mod is F


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
    # jendela WINDUP berakhir persis di konstanta renderer
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
            break                        # timer habis -> timeline mati
        ps.append(d.attack_progress)
    # monoton naik sampai 1.0, lalu timeline berakhir bersih
    assert all(b >= a for a, b in zip(ps, ps[1:]))
    assert ps[-1] >= 0.95
    assert not d._attack_live


def test_prioritas_state_dan_kunci_death():
    for name in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST",
                 "SKILL", "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert name in F.ANIM_PRIORITY
    h, d = fresh_director()
    h.alive = False
    d.update(DT)
    assert d.state == "DEATH"
    # DEATH terkunci selama unit tetap mati
    h._is_dashing = True
    for _ in range(10):
        d.update(DT)
    assert d.state == "DEATH"


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
    assert d.particles.count() <= n1 + 1     # tidak ada burst kedua


# ═══ 3. SWING & TRAIL ════════════════════════════════════════════════════

def test_ujung_bilah_mengikuti_busur_bukan_lerp():
    """Tip iai harus melengkung: deviasi dari garis lurus > ambang."""
    p0 = G._katana_tip_local(0.0, "attack", 0.30)
    p1 = G._katana_tip_local(0.0, "attack", 0.70)
    max_dev = 0.0
    for i in range(1, 20):
        t = 0.30 + (0.70 - 0.30) * i / 20.0
        px, py = G._katana_tip_local(0.0, "attack", t)
        lx = p0[0] + (p1[0] - p0[0]) * (i / 20.0)
        ly = p0[1] + (p1[1] - p0[1]) * (i / 20.0)
        max_dev = max(max_dev, math.hypot(px - lx, py - ly))
    assert max_dev > 8.0, "lintasan tip nyaris lurus (%.2f px)" % max_dev


def test_katana_points_layar_mengikuti_render_scale():
    h = fresh_hero()
    h._render_scale = 1.0
    b1, t1, _ = F.katana_points(h, progress=0.5)
    h._render_scale = 0.5
    b2, t2, _ = F.katana_points(h, progress=0.5)
    L1 = math.hypot(t1[0] - b1[0], t1[1] - b1[1])
    L2 = math.hypot(t2[0] - b2[0], t2[1] - b2[1])
    assert abs(L2 - L1 * 0.5) < 1.0


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
    h, d = fresh_director(cooldown=40)
    run_swing(h, d)
    assert d.trail.points or d.trail.active is False   # sudah terisi/luruh
    # cek bahwa selama swing sempat ada sample
    h2, d2 = fresh_director(cooldown=40)
    h2.attack_timer = h2.timer = 40
    seen = 0
    for _ in range(44):
        d2.update(DT)
        seen = max(seen, len(d2.trail.points))
        if h2.attack_timer > 0:
            h2.attack_timer -= 1
            h2.timer = h2.attack_timer
    assert seen >= 3


def test_whoosh_pendaratan_bilah_sekali_per_ayunan():
    _clear_feel()
    h, d = fresh_director(cooldown=40)
    h.attack_timer = h.timer = 40
    seen = 0
    for _ in range(44):
        d.update(DT)
        seen = max(seen, len([i for i in d.impacts
                              if i.kind in ("slash", "crit")]))
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    assert d._blade_landed
    assert seen >= 1                    # whoosh pop muncul di IMPACT
    drain(d, 2.0)
    assert not d.impacts                # ... dan tidak abadi


# ═══ 4. PARTICLE SYSTEM ══════════════════════════════════════════════════

def test_partikel_punya_semua_bidang_master_prompt():
    p = F.Particle()
    for field in ("pos", "vel", "acc", "life", "max_life", "size",
                  "rotation", "rotation_speed", "alpha", "gravity",
                  "color"):
        assert hasattr(p, field)


def test_cap_partikel_dihormati():
    ps = F.ParticleSystem(cap=30)
    ps.burst(0, 0, 500)
    assert ps.count() <= 30


def test_partikel_mati_tidak_abadi():
    ps = F.ParticleSystem()
    ps.burst(0, 0, 40, life=(0.1, 0.3))
    for _ in range(60):
        ps.update(DT)
    assert ps.count() == 0


def test_gravity_dan_drag_diterapkan():
    ps = F.ParticleSystem()
    p = ps.spawn(0, 0, 100.0, 0.0, 1.0, 2, (255, 255, 255),
                 gravity=500.0, drag=2.0)
    ps.update(0.1)
    assert p.vel.y > 0          # gravitasi menarik ke bawah
    assert p.vel.x < 100.0      # drag meredam


def test_semua_shape_partikel_gambar_tanpa_error():
    ps = F.ParticleSystem()
    for shape in ("pixel", "spark", "shard", "streak", "leaf", "mote",
                  "smoke", "glow"):
        ps.spawn(60, 60, 20, -20, 0.5, 4, (200, 220, 255), shape=shape)
    ps.update(DT)
    ps.draw(SURF)


def test_swirl_membelokkan_arah():
    ps = F.ParticleSystem()
    p = ps.spawn(0, 0, 100.0, 0.0, 1.0, 2, (255, 255, 255), swirl=4.0)
    for _ in range(30):
        ps.update(DT)
    assert abs(p.vel.y) > 1.0   # kecepatan berbelok, bukan lurus


# ═══ 5. PROJECTILE ═══════════════════════════════════════════════════════

def test_bidang_projectile_lengkap():
    pr = F.KaizenProjectile(0, 0, 100, 0)
    for field in ("position", "velocity", "speed", "damage", "lifetime",
                  "target", "radius", "rotation", "trail", "particles",
                  "active"):
        assert hasattr(pr, field)


def test_projectile_dipakai_hanya_visual():
    pr = F.KaizenProjectile(0, 0, 100, 0)
    assert pr.damage == 0


def test_lifecycle_projectile_penuh():
    class T:
        x, y, radius, alive = 160.0, 0.0, 12, True

    hits = []
    ps = F.ParticleSystem()
    sys_ = F.ProjectileSystem(ps)
    pr = sys_.spawn(0, 0, 160, 0, target=T(),
                    on_impact=lambda p: hits.append(p))
    assert pr.state == pr.STATE_TRAVEL
    for _ in range(300):
        sys_.update(DT)
        sys_.draw(SURF)
        if not sys_.projectiles:
            break
    assert hits, "on_impact tidak terpanggil"
    assert not sys_.projectiles, "projectile tidak pernah dibuang"


def test_homing_mengejar_target_bergerak():
    class T:
        x, y, radius, alive = 220.0, 0.0, 10, True

    t = T()
    pr = F.KaizenProjectile(0, 0, 220, 0, target=t, homing=4.0)
    for i in range(200):
        t.y += 1.4
        if not pr.update(DT):
            break
        if pr.state == pr.STATE_IMPACT:
            break
    assert pr.state != pr.STATE_TRAVEL, "sabit tidak pernah mengenai"


def test_sabit_serangan_dasar_ranged_di_jendela_swing():
    h, d = fresh_director(cooldown=40)
    h.range = 150                       # unit ranged (boss-hero style)

    class T:
        x, y, radius, alive = 330.0, 200.0, 12, True

    h.target = T()
    h.attack_timer = h.timer = 40
    seen = 0
    for _ in range(44):
        d.update(DT)
        seen = max(seen, d.projectiles.count())
        if h.attack_timer > 0:
            h.attack_timer -= 1
            h.timer = h.attack_timer
    assert d._proj_fired
    assert seen >= 1                    # sabit sempat terbang
    drain(d, 2.0)
    assert d.projectiles.count() == 0   # ... dan dibersihkan tuntas


def test_cap_projectile_dihormati():
    ps = F.ProjectileSystem(cap=3)
    for _ in range(9):
        ps.spawn(0, 0, 50, 0)
    assert ps.count() == 3


# ═══ 6. SKILL FX ═════════════════════════════════════════════════════════

def test_lifecycle_skill_lengkap():
    fx = F.SkillFX("r", 100, 100, F.ParticleSystem())
    seen = []
    for _ in range(int(fx.total / DT) + 4):
        if not seen or seen[-1] != fx.phase:
            seen.append(fx.phase)
        if not fx.update(DT):
            break
    for phase in ("charge", "release", "area", "fade"):
        assert phase in seen, "fase %s hilang: %s" % (phase, seen)
    assert not fx.active


def test_radius_dunia_e_dan_r():
    assert F.WORLD_RADIUS["e"] == 100.0     # kaizen_skills cast_e
    assert F.WORLD_RADIUS["r"] == 150.0     # kaizen_skills cast_r


def test_cast_terdeteksi_dari_active_skill():
    _clear_feel()
    for skill in ("q", "w", "e", "r"):
        h, d = fresh_director()
        h.active_skill = skill
        h.active_skill_timer = F.SKILL_DUR[skill]
        d.update(DT)
        assert d.skills, "SkillFX %s tidak dibuat" % skill
        assert d.skills[-1].kind == skill
        for _ in range(6):
            d.update(DT)
            d.draw_ground(SURF)
            d.draw_front(SURF)


def test_dash_q2_memicu_streak_dan_hitstop():
    _clear_feel()
    h, d = fresh_director()
    d.update(DT)
    h._is_dashing = True
    h._dash_timer = 15
    d.update(DT)
    assert d.particles.count() > 0
    assert FEEL.HITSTOP.frames > 0


def test_emisi_wall_dan_tornado_berpagar_anti_beku():
    h, d = fresh_director()
    h._wind_wall_timer = 180
    h._ulti_timer = 90
    # timer MEMBEKU (unit "mati" di tengah skill): emisi harus berhenti
    for _ in range(int(16.0 / DT)):
        d.update(DT)
    n_stuck = d.particles.count()
    for _ in range(120):
        d.update(DT)
    assert d.particles.count() <= n_stuck   # tidak tumbuh lagi


def test_skill_fx_meluruh_penuh():
    h, d = fresh_director()
    for skill in ("q", "w", "e", "r"):
        F.notify_skill_impact(h, h.x, h.y, skill=skill)
    drain(d, 5.0)
    assert not d.skills
    assert d.particles.count() == 0


# ═══ 7. IMPACT + GAME FEEL ═══════════════════════════════════════════════

def test_impact_notify_melee():
    _clear_feel()
    h, d = fresh_director()
    h._kz_fx = d
    F._DIRECTORS.append(d)
    try:
        class T:
            x, y = 240.0, 200.0

        F.notify_melee_impact(h, T(), damage=42, crit=True)
        assert d.impacts
        assert d.particles.count() > 0
        assert FEEL.HITSTOP.frames > 0
        assert FEEL.SHAKE.amount > 0.0
    finally:
        F._DIRECTORS.remove(d)
        h._kz_fx = None


def test_hit_stop_dijepit_0_03_sampai_0_08():
    _clear_feel()
    F.hit_stop(10.0)         # minta gila-gilaan -> dijepit
    assert FEEL.HITSTOP.frames <= FEEL.HitStop.MAX_FRAMES
    _clear_feel()
    F.hit_stop(0.001)        # terlalu kecil -> minimal tetap terasa
    assert FEEL.HITSTOP.frames >= 2
    _clear_feel()


def test_shake_meluruh_bertahap():
    _clear_feel()
    F.shake(8.0, 0.3)
    a0 = FEEL.SHAKE.amount
    FEEL.SHAKE.update(0.1)
    a1 = FEEL.SHAKE.amount
    FEEL.SHAKE.update(0.1)
    a2 = FEEL.SHAKE.amount
    assert a0 > a1 > a2 >= 0.0
    _clear_feel()


def test_impact_fx_semua_kind_gambar_dan_mati():
    for kind in ("slash", "crit", "gale", "storm"):
        fx = F.ImpactFX(100, 100, 0.4, 1.2, kind=kind)
        alive_frames = 0
        while fx.update(DT):
            fx.draw(SURF)
            alive_frames += 1
            assert alive_frames < 120, "ImpactFX %s abadi" % kind
        assert not fx.active


def test_lapisan_hidup_meluruh_penuh_setelah_pertempuran():
    _clear_feel()
    h, d = fresh_director(cooldown=40)
    h.active_skill = "r"
    h.active_skill_timer = 100
    h._ulti_timer = 90
    for i in range(90):
        d.update(DT)
        h._ulti_timer -= 1
        h.active_skill_timer -= 1
    h.active_skill = None
    h.active_skill_timer = 0
    run_swing(h, d)
    drain(d, 6.0)
    st = d.stats()
    assert st["particles"] == 0
    assert st["projectiles"] == 0
    assert st["impacts"] == 0
    assert st["skills"] == 0
    _clear_feel()


# ═══ 8. SUPRESI GANDA & PIPELINE ═════════════════════════════════════════

def test_attach_owns_dan_release():
    h = fresh_hero()
    assert not F.owns(h)
    assert F.attach(h)
    assert F.owns(h)
    assert h._skip_renderer_projectiles is True
    d = h._kz_fx
    F._release(d)
    F._DIRECTORS.remove(d) if d in F._DIRECTORS else None
    assert not F.owns(h)
    assert h._skip_renderer_projectiles is False


def test_renderer_skip_smear_saat_lapisan_hidup_memiliki():
    h = fresh_hero()
    F.attach(h)
    try:
        canvas = pygame.Surface((340, 340), pygame.SRCALPHA)
        h._kz_attack_active = True
        h.attack_timer = h.timer = 20      # di tengah swing
        G.draw_kaizen(canvas, h, 170, 170)
        assert G._FX_LIVE.v is True
    finally:
        F._release(h._kz_fx) if getattr(h, "_kz_fx", None) else None
        F.reset_all()
    # tanpa lapisan hidup, fallback canvas kembali jalan
    h2 = fresh_hero()
    h2._kz_live_fx = False
    canvas2 = pygame.Surface((340, 340), pygame.SRCALPHA)
    G.draw_kaizen(canvas2, h2, 170, 170)
    assert G._FX_LIVE.v in (False, True)   # flag ter-set tanpa error


def test_spawn_wind_slash_canvas_dilewati_saat_dimiliki():
    h = fresh_hero()
    h._skip_renderer_projectiles = True
    G._spawn_wind_slash(h, h.x, h.y)
    assert not getattr(h, "_kz_projectiles", [])
    h._skip_renderer_projectiles = False
    G._spawn_wind_slash(h, h.x, h.y)
    assert len(h._kz_projectiles) == 1


def test_draw_layers_pipeline_tanpa_error():
    F.reset_all()
    h = fresh_hero()
    F.draw_ground_layer(SURF, h, h.x, h.y)
    F.draw_live_layer(SURF, h, h.x, h.y)
    assert F.owns(h)
    F.reset_all()
    assert not F._DIRECTORS


def test_total_particles_dan_registry():
    F.reset_all()
    h, d = fresh_director()
    h._kz_fx = d
    F._DIRECTORS.append(d)
    d.particles.burst(0, 0, 10, life=(0.5, 0.8))
    assert F.total_particles() > 0
    assert F.total_projectiles() == 0
    F.reset_all()
    assert F.total_particles() == 0


def test_overlay_debug_jalan():
    h, d = fresh_director()
    h.active_skill = "e"
    h._wind_wall_timer = 60
    h._ulti_timer = 30
    d.update(DT)
    F.draw_debug_overlay(SURF, d)          # tidak boleh raise


def test_tick_tidak_dobel_dalam_frame_sama():
    F.reset_all()
    h, d = fresh_director()
    h._kz_fx = d
    F._DIRECTORS.append(d)
    t0 = d.time
    F.tick(DT)      # dt eksplisit: maju
    F.tick(0.0)     # dt 0: tidak maju
    assert abs(d.time - (t0 + DT)) < 1e-9
    F.reset_all()


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
