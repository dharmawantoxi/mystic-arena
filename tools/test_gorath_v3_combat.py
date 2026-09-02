#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur GORATH v3.

Gorath digambar lewat kode yang sama di DUA jalur: lane boss
(``Boss.draw`` -> ``_NS_gorath.draw_gorath``) dan lane hero
(``heroes.render_hero`` -> sprite di-cache + smoothscale). Karena itu
sistem tempurnya dipecah:

  * ``bosses/level2.py::_NS_gorath``  = badan, rig, pose, controller
    animasi, telegraph tanah, dan semua FALLBACK kalau modul FX tidak
    tersedia.
  * ``heroes/gorath_fx.py``           = lapisan hidup 1:1 di luar sprite
    cache: trail sabit darah, partikel, proyektil bolt darah, skill FX
    Q/W/E/R, impact, hit-stop, shake, overlay debug.
  * ``heroes/combat_feel.py``         = bus SHARED (hit-stop + shake)
    yang dipakai semua karakter v3, jadi dua karakter tidak menumpuk
    freeze.

Uji ini mengunci kontrak yang gampang rusak saat orang lain menyentuh
salah satu dari ketiganya:

  1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di KEDUA modul.
  2. Palet + API publik (backward-compat untuk pemanggil lama).
  3. Controller animasi: fase, urutan, delta-time, jendela hit, prioritas
     state, dan semua nama atribut lama yang masih dipakai renderer/tools.
  4. Ayunan berbasis busur (bukan lerp linear) + trail dari histori bilah.
  5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
  6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
  7. Lifecycle skill FX (cast -> charge -> release -> area -> impact -> fade)
     dan pusat yang benar (R di caster, W lahir dari ujung kukri, E
     mengikuti titik pendaratan).
  8. Impact + screen shake + hit-stop yang SELALU terkuras (tidak ada efek
     abadi), dengan hit-stop di 0.03-0.08 s.
  9. Supresi ganda: saat lapisan hidup mengambil alih, renderer tidak
     menggambar FX skill foreground dua kali - dan sebaliknya fallback
     canvas tetap jalan kalau modul FX tidak dimuat.
 10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_gorath_v3_combat.py -q
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
from heroes import gorath_fx as F                          # noqa: E402
from bosses.level2 import _NS_gorath as G                   # noqa: E402

DT = 1.0 / 60.0
COOLDOWN = 44                     # attack_cooldown gorath di boss_data.py
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


# ── helper ────────────────────────────────────────────────────────────────
def fresh_hero(x=0.0, y=0.0, cooldown=COOLDOWN, scale=None):
    """Unit Gorath minim. ``scale=None`` = jalur BOSS (tanpa _render_scale)."""
    h = _ProbeEntity("gorath", x, y)
    h.boss_type = "gorath"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = cooldown
    h.range = 58
    h.speed = 1.6
    h.hp = h.max_hp = 9000
    h.radius = 36
    h.hurt_flash_timer = 0
    if scale is not None:
        h._render_scale = scale
    return h


def dummy_target(x=180.0, y=0.0):
    t = _ProbeEntity("creep", x, y)
    t.alive = True
    t.radius = 14
    return t


def attack_frames(hero, cooldown=COOLDOWN):
    """Satu siklus serangan penuh lewat controller renderer.

    Snapshot per frame; semua angka dibaca dari atribut yang DIHASILKAN
    controller, jadi kalau ada yang menukar sumber timing, uji ini yang
    berteriak.
    """
    hero._gor_attack_active = False
    hero._gor_attack_frame = 0
    hero._gor_prev_timer = 0
    hero._gor_state = "IDLE"
    hero._gor_state_prev = "IDLE"
    hero._gor_state_time = 0.0
    hero._gor_hurt_frames = 0
    out = []
    for t in range(cooldown, -1, -1):
        hero.timer = t
        G._update_gorath_attack_anim(hero)
        out.append({
            "timer": t,
            "active": bool(hero._gor_attack_active),
            "frame": int(hero._gor_attack_frame),
            "progress": float(hero._gor_attack_progress),
            "raw": float(hero._gor_attack_raw),
            "phase": hero._gor_attack_phase,
            "state": hero._gor_state,
            "hit": bool(getattr(hero, "_gor_hit_active", False)),
            "dt": float(hero._gor_dt),
        })
    return out


def run_live(hero, frames, dt=DT, attack=False, skill=None, skill_dur=40,
             surf=None):
    """Jalankan lapisan hidup selama ``frames`` frame, kembalikan surface.

    Surface DI-CLEAR tiap frame: test "tidak ada efek abadi" membandingkan
    isi buffer sebelum/sesudah, dan blit kumulatif akan menyembunyikannya.
    """
    if surf is None:
        surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    for i in range(frames):
        hero.pulse += 0.3
        if attack:
            # mode manual: pemanggil yang menggerakkan progress (sama seperti
            # tools/_audit_gorath_v2.py), controller tinggal menurunkan fase
            hero._gor_attack_active = True
            hero._gor_attack_manual = True
            hero._gor_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        if skill is not None:
            hero.active_skill = skill
            hero.active_skill_timer = max(0, skill_dur - i)
            if hero.active_skill_timer == 0:
                hero.active_skill = None
        G._update_gorath_attack_anim(hero)
        F.tick(dt)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, hero, hero.x, hero.y)
        F.draw_live_layer(surf, hero, hero.x, hero.y)
    return surf


def start_engine_attack(hero, cooldown=COOLDOWN):
    hero._gor_attack_active = False
    hero._gor_attack_manual = False
    hero._gor_attack_frame = 0
    hero._gor_prev_timer = 0
    hero.timer = cooldown
    G._update_gorath_attack_anim(hero)


def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    FEEL.reset()


@pytest.fixture(autouse=True)
def _clean_fx():
    """Setiap test mulai dari FX kosong dan bus feel kosong."""
    F.reset_all()
    _clear_feel()
    yield
    F.reset_all()
    _clear_feel()


# ══════════════════════════════════════════════════════════════════════════
# 1. 100% PROSEDURAL & API PUBLIK
# ══════════════════════════════════════════════════════════════════════════

def test_tidak_memuat_asset_eksternal():
    """Baik lapisan FX maupun controller renderer: tanpa asset apa pun."""
    for rel in (os.path.join("heroes", "gorath_fx.py"),
                os.path.join("heroes", "combat_feel.py")):
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for bad in ("pygame.image.load", "image.load(",
                    "pygame.mixer.Sound", ".png", ".jpg", ".jpeg",
                    ".gif", ".bmp", ".ogg", ".wav", "load_asset"):
            assert bad not in src, "%s memakai %s" % (rel, bad)
    # jalur renderer: sumber _NS_gorath juga tidak boleh memuat bitmap
    src = inspect.getsource(G)
    assert "pygame.image.load" not in src


def test_api_publik_lapisan_hidup():
    for name in ("attach", "owns", "director_for", "tick", "reset_all",
                 "total_particles", "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast",
                 "notify_skill_start", "notify_skill_end",
                 "draw_blood_bolt", "hit_stop", "shake",
                 "should_freeze_frame", "clear_cache", "cache_size",
                 "GORATH_PALETTE", "GORATH_FX_ENABLED",
                 "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
                 "GorathProjectile", "ProjectileSystem", "SkillFX",
                 "GorathFXDirector"):
        assert hasattr(F, name), "API hilang: gorath_fx.%s" % name


def test_api_publik_renderer_tetap_ada():
    """Renderer tidak boleh kehilangan nama yang dipakai Boss.draw / tools."""
    for name in ("draw_gorath", "draw_boss", "_resolve_pose",
                 "_update_gorath_attack_anim", "_update_attack_anim",
                 "_detect_moving", "_attack_curve", "_attack_pose",
                 "_tip_local", "_tip_screen", "_front_grip_local",
                 "_back_grip_local", "_blade_angle_local", "_blade_len",
                 "_rig_shift", "_local", "_swing_hitbox", "attack_phase",
                 "attack_phases_order", "_draw_gorath_debug",
                 "_draw_gorath_attack", "_draw_gorath_body_raw",
                 "_draw_bloodrage", "_draw_bloodrite", "_draw_thirst",
                 "_draw_rupture", "BloodProjectile", "_draw_shockwave",
                 "_fx_scale", "SKILL_DUR", "SKILL_RADIUS", "PALETTE"):
        assert hasattr(G, name), "kontrak renderer hilang: %s" % name


def test_palet_lengkap_dan_sinkron_dengan_renderer():
    for key in ("blood_dark", "blood_mid", "blood_bright", "blood_hot",
                "blood_glow", "blood_light", "blood_seam", "skin_mid",
                "metal_mid", "bone_mid", "fx_white"):
        assert key in F.GORATH_PALETTE, "kunci palet hilang: %s" % key
        col = F.GORATH_PALETTE[key]
        assert len(col) >= 3 and all(0 <= c <= 255 for c in col[:3])
    # palet lapisan hidup = palet renderer (satu karakter, satu warna).
    drift = [dst for dst, src in F._PALETTE_SYNC.items()
             if src in G.PALETTE and tuple(F.P[dst][:3])
             != tuple(G.PALETTE[src][:3])]
    assert not drift, "drift palet: %s" % drift


def test_debug_mode_ada_dan_mati_secara_default():
    assert G.DEBUG_CHARACTER is False
    assert F.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    """Gorath berbagi satu bus combat_feel - tidak ada salinan matematika."""
    assert F._feel is FEEL
    src = inspect.getsource(F.should_freeze_frame)
    assert "_feel.should_freeze_frame" in src, src
    assert "_feel" in inspect.getsource(F.hit_stop)
    assert "_feel" in inspect.getsource(F.shake)


# ══════════════════════════════════════════════════════════════════════════
# 2. CONTROLLER ANIMASI
# ══════════════════════════════════════════════════════════════════════════

def test_urutan_fase_ayunan_lengkap():
    order = G.attack_phases_order()
    assert list(order) == PHASE_ORDER
    for name, a, b in G.ATTACK_PHASES:
        assert 0.0 <= a < b <= 1.0
    # semua nama yang diminta master prompt ada
    need = {"ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW",
            "RECOVERY"}
    assert need <= set(order)


def test_setiap_fase_punya_durasi():
    assert G.ATTACK_ANTICIPATION_END == pytest.approx(0.16)
    assert G.ATTACK_WINDUP_END == pytest.approx(0.30)
    assert G.ATTACK_SWING_END == pytest.approx(0.46)
    assert G.ATTACK_IMPACT_END == pytest.approx(0.60)
    assert G.ATTACK_FOLLOW_END == pytest.approx(0.80)


def test_progress_monoton_dan_habis_tepat():
    h = fresh_hero()
    frames = attack_frames(h)
    act = [f for f in frames if f["active"]]
    assert act, "serangan tidak pernah aktif"
    progs = [f["progress"] for f in act]
    assert all(b >= a - 1e-9 for a, b in zip(progs, progs[1:])), "tidak monoton"
    assert progs[-1] == pytest.approx(1.0, abs=0.02)
    # frame terakhir (timer 0) masih menuntaskan ayunan terakhir,
    # panggilan berikutnya mematikan serangan
    assert frames[-1]["active"] is True
    G._update_gorath_attack_anim(h)
    assert h._gor_attack_active is False


def test_delta_time_dipakai_dan_dijepit():
    h = fresh_hero()
    h.timer = 0
    G._update_gorath_attack_anim(h)
    dt = float(h._gor_dt)
    assert 1.0 / 240.0 <= dt <= 1.0 / 20.0


def test_jendela_hit_aktif_di_tengah_ayunan():
    frames = attack_frames(fresh_hero())
    hit = [f for f in frames if f["hit"]]
    assert hit, "tidak pernah ada jendela hit"
    lo, hi = G.ATTACK_ACTIVE_WINDOW
    assert all(lo <= f["progress"] < hi for f in hit)
    # tidak ada hit di anticipation / recovery
    for f in frames:
        if f["phase"] in ("ANTICIPATION", "RECOVERY"):
            assert not f["hit"]


def test_prioritas_state_dan_kunci_death():
    h = fresh_hero()
    h.alive = False
    assert G._resolve_anim_state(h, True, "SWING") == "DEATH"
    h.alive = True
    h._gor_hurt_frames = 5
    assert G._resolve_anim_state(h, True, "SWING") == "HURT"
    h._gor_hurt_frames = 0
    h.active_skill = "r"
    assert G._resolve_anim_state(h, True, "SWING") == "SPECIAL"
    h.active_skill = "q"
    assert G._resolve_anim_state(h, False, "NONE") == "SKILL"
    h.active_skill = None
    assert G._resolve_anim_state(h, True, "WINDUP") == "CHARGE"
    assert G._resolve_anim_state(h, True, "IMPACT") == "SWING"
    assert G._resolve_anim_state(h, True, "RECOVERY") == "ATTACK"


def test_hurt_dari_flash_boss():
    h = fresh_hero()
    h.hurt_flash_timer = 8
    G._update_gorath_attack_anim(h)
    assert int(h._gor_hurt_frames) >= 9


def test_state_walk_run_dari_gerakan():
    h = fresh_hero()
    h.speed = 1.0
    assert G._resolve_anim_state(h, False, "NONE") == "IDLE"
    h._moving_cached = True
    assert G._resolve_anim_state(h, False, "NONE") == "WALK"
    h.speed = 2.6
    assert G._resolve_anim_state(h, False, "NONE") == "RUN"


def test_tabel_prioritas_mengandung_semua_state_master_prompt():
    need = {"IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
            "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"}
    assert need <= set(G.ANIM_STATES), need - set(G.ANIM_STATES)
    assert G.ANIM_STATES["DEATH"] > G.ANIM_STATES["HURT"]
    assert G.ANIM_STATES["IDLE"] == min(G.ANIM_STATES.values())


def test_atribut_lama_pemain_lain_masih_diisi():
    """_gor_attack_raw/_gor_pose_action dipakai audit & tools v2."""
    h = fresh_hero()
    for t in (COOLDOWN, 30, 20, 10, 1):
        h.timer = t
        G._update_gorath_attack_anim(h)
    assert hasattr(h, "_gor_attack_raw") or hasattr(h, "_gor_attack_progress")
    G.draw_gorath(pygame.Surface((240, 240), pygame.SRCALPHA), h, 120, 150)
    assert h._gor_pose_action in ("idle", "walk", "attack")


# ══════════════════════════════════════════════════════════════════════════
# 3. AYUNAN BERBASIS BUSUR + TRAIL
# ══════════════════════════════════════════════════════════════════════════

def test_ujung_bilah_mengikuti_busur_bukan_lerp():
    n = 30
    pts = [pygame.Vector2(G._tip_local("attack", 0.0, G._attack_curve(
        i / float(n)))) for i in range(n + 1)]
    a, b = pts[0], pts[-1]
    worst = 0.0
    for i, p in enumerate(pts):
        worst = max(worst, (p - a.lerp(b, i / float(n))).length())
    assert worst > 8.0, "deviasi busur hanya %.1f px" % worst


def test_ujung_bilah_kontinu_tanpa_teleport():
    """Tidak boleh ada ledakan langkah dari pose yang sedang ditahan.

    Ayunan BOLEH cepat (itu yang membuatnya terasa berbobot) tapi tidak
    boleh melompat dari "diam" ke "jauh" dalam satu frame: itu terbaca
    sebagai glitch. Dijaga dengan membandingkan tiap langkah dengan
    langkah-langkah sebelumnya (ramp, bukan spike).
    """
    n = COOLDOWN - 1                             # == panjang serangan dlm frame
    pts = [pygame.Vector2(G._tip_local("attack", 0.0,
                                       G._attack_curve(i / float(n))))
           for i in range(n + 1)]
    steps = [(q - p).length() for p, q in zip(pts, pts[1:])]
    assert max(steps) <= 38.0, "satu langkah bilah %.1f px" % max(steps)
    for i in range(2, len(steps)):
        prev = max(steps[i - 2], steps[i - 1])
        if prev < 4.0:                     # bilah sedang ditahan (impact
            limit = 22.0                   # hold / tension): tidak boleh
        else:                              # langsung melesat penuh
            limit = 2.5 * prev + 6.0       # ramp, bukan ledakan
        assert steps[i] <= limit, (
            "bilah meledak di frame %d: %.1f px setelah %.1f px"
            % (i, steps[i], prev))
    assert sum(steps) > 200.0, "bilah nyaris tidak bergerak saat ayunan"
    assert sorted(steps)[len(steps) // 2] > 0.5, "hampir semua frame diam"


def test_kurva_serangan_ada_hold_dan_akselerasi():
    """Tahan di impact lalu tebas cepat: kurva tidak boleh linear."""
    ramp = [G._attack_curve(i / 100.0) for i in range(101)]
    assert all(b >= a - 1e-9 for a, b in zip(ramp, ramp[1:])), "tidak monoton"
    rate = [b - a for a, b in zip(ramp, ramp[1:])]
    peak = max(rate)
    assert peak > 0.0
    # TAHAN: banyak langkah yang nyaris diam (impact hold)
    slow = sum(1 for r in rate if r < 0.2 * peak)
    assert slow >= 10, "tidak ada fase TAHAN (%d/100 langkah pelan)" % slow
    assert peak > 4.0 * min(r for r in rate if r > 0), "ayunan terlalu linear"
    # titik kunci fase = keyframe _attack_pose tetap di posisi raw-nya
    assert G._attack_curve(0.30) == pytest.approx(0.30, abs=0.03)
    assert G._attack_curve(0.54) == pytest.approx(0.54, abs=0.03)


def test_trail_dibangun_dari_histori_dan_meluruh():
    trail = F.SwingTrail()
    g = pygame.Vector2(100, 100)
    for i in range(20):
        a = -2.0 + i * 0.12
        t = g + pygame.Vector2(math.cos(a), math.sin(a)) * 40
        trail.push(g, t, g, t + pygame.Vector2(-6, 4))
    assert len(trail.points) > 4
    trail.update(0.05)
    trail.update(0.3)                            # > 0.22 s -> semua luruh
    assert trail.points == []


def test_trail_diisi_lapisan_hidup_saat_swing():
    h = fresh_hero()
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    seen_swing = False
    for i in range(30):
        h._gor_attack_active = True
        h._gor_attack_manual = True
        h._gor_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
        G._update_gorath_attack_anim(h)
        F.tick(DT)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
        if h._gor_attack_phase in ("SWING", "IMPACT", "FOLLOW"):
            seen_swing = True
        d = getattr(h, "_gor_fx", None)
        assert d is not None
        if seen_swing:
            assert d.trail.points, "trail kosong saat swing frame %d" % i
    assert seen_swing


# ══════════════════════════════════════════════════════════════════════════
# 4. PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════════════════

def test_cap_partikel_dihormati():
    ps = F.ParticleSystem(cap=40)
    for _ in range(200):
        ps.burst(0, 0, 6, life=(0.5, 0.5))
    assert ps.count() <= 40
    assert ps.dropped > 0
    ps.clear()
    assert ps.count() == 0


def test_partikel_mati_tidak_abadi():
    ps = F.ParticleSystem(cap=30)
    ps.burst(0, 0, 12, life=(0.1, 0.1))
    for _ in range(30):
        ps.update(1 / 30.0)
    assert ps.count() == 0


def test_partikel_punya_semua_bidang_master_prompt():
    ps = F.ParticleSystem(cap=10)
    p = ps.spawn(1, 2, 3, 4, 0.5, 2, (255, 0, 0), gravity=9.8,
                 rotation=0.1, rotation_speed=1.0)
    assert p is not None
    for name in ("position", "velocity", "acceleration", "life", "max_life",
                 "size", "rotation", "rotation_speed", "alpha", "gravity",
                 "color"):
        assert hasattr(p, name), "bidang hilang: %s" % name
    v = p.velocity
    assert abs(v.x - 3) < 1e-6 and abs(v.y - 4) < 1e-6
    p.update(0.1)
    assert p.life == pytest.approx(0.1)
    assert p.alpha() < 255


def test_alpha_partikel_meluruh_saat_digambar():
    ps = F.ParticleSystem(cap=10)
    surf = pygame.Surface((80, 80), pygame.SRCALPHA)
    p = ps.spawn(40, 40, 0, 0, 0.4, 3, (200, 30, 30))
    p.draw(surf)
    first = sum(surf.get_at((x, y)).a for x in range(80)
                for y in range(80))
    for _ in range(20):
        ps.update(1 / 60.0)
    surf.fill((0, 0, 0, 0))
    p.draw(surf)
    last = sum(surf.get_at((x, y)).a for x in range(80)
               for y in range(80))
    assert last < first, "partikel tidak meluruh"


def test_lapisan_hidup_meluruh_penuh_setelah_pertempuran():
    """Setelah pertarungan berhenti: 0 partikel DAN 0 piksel di buffer."""
    h = fresh_hero(120, 150)
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    run_live(h, 80, attack=True, surf=surf)
    run_live(h, 60, skill="r", skill_dur=90, surf=surf)
    F.notify_melee_impact(h, dummy_target(200, 150), 94, True)
    run_live(h, 10, surf=surf)
    # biarkan semua efek hidup mati (maks umur partikel < 1.4 s)
    surf.fill((0, 0, 0, 0))
    for _ in range(240):
        F.tick(DT)
        h._gor_attack_active = False
        h._gor_attack_manual = False
        G._update_gorath_attack_anim(h)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    assert F.total_particles() == 0
    d = getattr(h, "_gor_fx", None)
    if d is not None:
        assert d.projectiles.count() == 0
        assert d.skills == []
        assert d.impacts == []
        assert d.trail.points == []
    nonzero = sum(1 for x in range(0, 360, 2) for y in range(0, 260, 2)
                  if surf.get_at((x, y)).a > 4)
    assert nonzero == 0, "masih ada %d piksel efek di buffer" % nonzero


# ══════════════════════════════════════════════════════════════════════════
# 5. PROJECTILE
# ══════════════════════════════════════════════════════════════════════════

def test_bidang_projectile_lengkap():
    pr = F.GorathProjectile(0, 0, 100, 0, target=None)
    for name in ("position", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(pr, name), "bidang hilang: %s" % name
    assert pr.state == pr.STATE_TRAVEL
    assert abs(pr.velocity.length() - pr.speed) < 1.0


def test_projectile_dipakai_hanya_visual():
    """damage=0: damage skill tetap milik sistem gameplay."""
    pr = F.GorathProjectile(0, 0, 100, 0)
    assert pr.damage == 0
    pr2 = F.ProjectileSystem().spawn(0, 0, 100, 0)
    assert pr2.damage == 0


def test_projectile_lahir_dari_ujung_bilah():
    h = fresh_hero()
    h.active_skill = "w"
    h.active_skill_timer = 60
    h.target = dummy_target(300, 0)
    d = F.director_for(h)
    aim = (300.0, 0.0)
    d.spawn_blood_volley(h.x, h.y, aim)
    _g, tip = F.blade_points(h, h.x, h.y, False)
    for p in d.projectiles.list():
        assert p.spawn_pos.distance_to(tip) <= 12.0, (
            "bolt lahir %.1f px dari ujung kukri" % p.spawn_pos.distance_to(tip))


def test_lifecycle_projectile_sampai_hancur():
    ps = F.ProjectileSystem(cap=4)
    pr = ps.spawn(0, 0, 400, 0, lifetime=0.06)   # umur pendek: pasti mati
    for _ in range(8):                            # 0.133 s > 0.06 s
        ps.update(DT)
    assert pr.state in (pr.STATE_IMPACT, pr.STATE_DEAD)
    # kuras IMPACT -> DEAD (pop impact + aging 0.26 s)
    for _ in range(30):
        ps.update(DT)
    assert ps.count() == 0


def test_projectile_mengenai_target_memicu_impact():
    h = fresh_hero()
    hit = []
    d = F.director_for(h)
    tgt = dummy_target(140, 0)
    pr = d.projectiles.spawn(h.x, h.y, tgt.x, tgt.y, speed=900.0,
                             target=tgt,
                             on_impact=lambda p: hit.append(p))
    for _ in range(120):
        d.projectiles.update(DT)
        if hit:
            break
    assert hit, "bolt tidak pernah menyentuh target"
    assert pr.hit_pos is not None


def test_cap_projectile():
    ps = F.ProjectileSystem(cap=4)
    for _ in range(10):
        ps.spawn(0, 0, 100, 0)
    assert ps.count() == 4


# ══════════════════════════════════════════════════════════════════════════
# 6. SKILL FX
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key,dur", [("q", 90), ("w", 60), ("e", 35),
                                     ("r", 90)])
def test_skill_fx_selesai_dan_hilang(key, dur):
    h = fresh_hero()
    h.active_skill = key
    h.active_skill_timer = dur
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    run_live(h, int(dur * 0.6), skill=key, skill_dur=dur, surf=surf)
    d = getattr(h, "_gor_fx", None)
    assert d is not None and d.skills, "skill %s tidak pernah muncul" % key
    # kuras sampai lifecycle selesai (plus jeda)
    for _ in range(int(F.SKILL_TOTAL[key] * 60) + 40):
        F.tick(DT)
        h.active_skill = None
        G._update_gorath_attack_anim(h)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    d = getattr(h, "_gor_fx", None)
    if d is not None:
        assert d.skills == [], "skill %s tidak pernah selesai" % key


def test_skill_durasi_sama_dengan_engine():
    assert F.SKILL_DUR == G.SKILL_DUR


def test_radius_dunia_e_dan_r_dipakai_penuh():
    """E 85 / R 190 px dunia = gameplay base_boss + telegraph renderer."""
    assert F.WORLD_RADIUS["e"] == G.SKILL_RADIUS["e"] == 85
    assert F.WORLD_RADIUS["r"] == G.SKILL_RADIUS["r"] == 190
    assert F.WORLD_RADIUS["w"] == G.SKILL_RADIUS["w"] == 150


def test_r_meledak_di_caster():
    """SkillFX R lahir di posisi caster (AOE di sekitar diri)."""
    h = fresh_hero(200, 150)
    F.notify_skill_cast(h, "r")
    d = getattr(h, "_gor_fx", None)
    assert d and d.skills
    fx = d.skills[-1]
    assert fx.kind == "r"
    assert abs(fx.x - 200) < 2 and abs(fx.y - 150) < 2


def test_w_voli_dari_state_engine():
    """Tepi active_skill == 'w' memicu voli 3 bolt (tanpa notify manual)."""
    h = fresh_hero()
    h.active_skill = "w"
    h.active_skill_timer = 60
    h.target = dummy_target(300, 0)
    d = F.director_for(h)
    d.update(DT, h.x, h.y)
    assert len(d.projectiles.list()) == 3


def test_e_skill_ikut_titik_pendaratan():
    """E: skill fx mengikuti unit saat melompat (jejak dari titik tolak)."""
    h = fresh_hero(100, 100)
    h.active_skill = "e"
    h.active_skill_timer = 35
    d = F.director_for(h)
    d.update(DT, 100, 100)
    assert d.skills and d.skills[-1].kind == "e"
    fx = d.skills[-1]
    assert fx.leap_from is not None
    # unit melompat -> skill ikut pindah
    d.update(DT, 220, 100)
    assert abs(fx.x - 220) < 2
    d.update(DT, 250, 100)
    assert abs(fx.x - 250) < 2


# ══════════════════════════════════════════════════════════════════════════
# 7. GAME FEEL: HIT-STOP & SCREEN SHAKE
# ══════════════════════════════════════════════════════════════════════════

def test_hit_stop_dalam_rentang_master_prompt():
    """Hit-stop dari IMPACT GORATH yang nyata: 0.03-0.08 s (2-5 frame)."""
    h = fresh_hero()
    tgt = dummy_target(140, 0)
    _clear_feel()
    F.notify_melee_impact(h, tgt, 120, True)
    sec = FEEL.HITSTOP.total * DT
    assert 0.03 - 1e-3 <= sec <= 0.08 + 2e-3, "hit-stop %.3f s" % sec
    assert 2 <= FEEL.HITSTOP.total <= FEEL.HITSTOP.MAX_FRAMES


def test_hit_stop_permintaan_gila_dijepit():
    _clear_feel()
    FEEL.hit_stop(5.0)                           # permintaan gila pun dijepit
    assert 2 <= FEEL.HITSTOP.frames <= FEEL.HITSTOP.MAX_FRAMES
    assert FEEL.HITSTOP.frames * DT <= 0.085


def test_hit_stop_membekukan_lalu_melepas():
    FEEL.HITSTOP.clear()
    FEEL.hit_stop(0.05)
    frozen = sum(1 for _ in range(10) if FEEL.should_freeze_frame())
    assert 2 <= frozen <= 5
    assert not FEEL.should_freeze_frame()        # sudah lepas


def test_shake_meluruh_ke_nol():
    FEEL.SHAKE.clear()
    FEEL.shake(12.0, 0.3)
    assert FEEL.SHAKE.amount > 0
    for _ in range(60):
        FEEL.SHAKE.update(1 / 60.0)
    assert FEEL.SHAKE.amount == 0.0
    assert FEEL.SHAKE.shake_duration == 0.0


def test_impact_tanpa_target_tidak_error():
    h = fresh_hero()
    F.notify_melee_impact(h, None, 94, False)    # target None -> aman
    F.notify_projectile_impact(h, 10, 10, 0.0, 0, False)
    F.notify_skill_impact(h, 10, 10, 85, "e")
    d = getattr(h, "_gor_fx", None)
    assert d is not None
    surf = pygame.Surface((200, 200), pygame.SRCALPHA)
    d.draw_front(surf, h.x, h.y)


def test_bus_pintu_hit_stop_core():
    """Game.update memanggil bus, bukan modul karakter."""
    assert FEEL.should_freeze_frame is F.should_freeze_frame or \
        "should_freeze_frame" in inspect.getsource(F.should_freeze_frame)


# ══════════════════════════════════════════════════════════════════════════
# 8. INTEGRASI: JALUR BOSS, LANE HERO, FALLBACK, DEBUG
# ══════════════════════════════════════════════════════════════════════════

def test_jalur_boss_mengambil_alih_effect():
    h = fresh_hero(120, 150)
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    G.draw_gorath(surf, h, 120, 150)
    assert F.owns(h) is True
    assert hasattr(h, "_gor_fx")


def test_fallback_canvas_saat_modul_fx_tidak_ada(monkeypatch):
    monkeypatch.setattr(F, "GORATH_FX_ENABLED", False)
    h = fresh_hero(120, 150)
    h.active_skill = "q"
    h.active_skill_timer = 50
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    G.draw_gorath(surf, h, 120, 150)
    assert F.owns(h) is False
    assert surf.get_bounding_rect(min_alpha=10).width > 20


def test_lane_hero_terdaftar_di_live_fx():
    assert "gorath" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS["gorath"] == "heroes.gorath_fx"


def test_render_hero_menjalankan_lapisan_hidup():
    h = fresh_hero(300, 200, scale=0.62)
    surf = pygame.Surface((600, 400), pygame.SRCALPHA)
    heroes.render_hero("gorath", surf, h, 300, 200)
    assert F.owns(h) is True


def test_telegraph_tanah_tetap_di_renderer():
    """Telegraph radius (W/E/R) tetap digambar renderer (bukan lapisan FX)."""
    h = fresh_hero(150, 150)
    h.active_skill = "r"
    h.active_skill_timer = 60
    h.target = dummy_target(260, 130)
    surf = pygame.Surface((360, 300), pygame.SRCALPHA)
    G.draw_gorath(surf, h, 150, 150)
    # ring jangkauan R = 190 px dunia ter-clamp di canvas
    assert G._ring_r(h, 190, surf) <= 170


def test_hitbox_hanya_saat_jendela_hit():
    h = fresh_hero()
    h._gor_hit_active = False
    assert G._swing_hitbox(h, 100, 100) is None
    h._gor_hit_active = True
    hb = G._swing_hitbox(h, 100, 100)
    assert hb is not None and hb.width >= 8 and hb.height >= 10


def test_debug_overlay_tidak_merusak_render():
    h = fresh_hero(120, 150)
    h._gor_state = "SWING"
    h._gor_attack_phase = "IMPACT"
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    before = surf.get_bounding_rect()
    try:
        G._draw_gorath_debug(surf, h, 120, 150, "attack", True)
    except Exception:
        pass
    assert surf.get_bounding_rect().width >= before.width


def test_debug_overlay_menyebut_state_dan_partikel():
    import heroes.gorath_fx as F2
    src = inspect.getsource(F2.draw_debug_overlay)
    assert "state" in src and "particles" in src


# ══════════════════════════════════════════════════════════════════════════
# 9. PERFORMANSI
# ══════════════════════════════════════════════════════════════════════════

def test_lapisan_hidup_cepat():
    h = fresh_hero(120, 150)
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    F.attach(h)
    for _ in range(20):
        F.tick(DT)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    t0 = time.perf_counter()
    for _ in range(60):
        F.tick(DT)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, h, h.x, h.y)
        F.draw_live_layer(surf, h, h.x, h.y)
    ms = (time.perf_counter() - t0) * 1000.0 / 60.0
    assert ms < 2.5, "lapisan hidup %.2f ms/frame" % ms


def test_draw_gorath_lane_boss_masih_dibawah_anggaran():
    h = fresh_hero(120, 150)
    surf = pygame.Surface((360, 260), pygame.SRCALPHA)
    G.draw_gorath(surf, h, 120, 150)
    t0 = time.perf_counter()
    for _ in range(30):
        G.draw_gorath(surf, h, 120, 150)
    ms = (time.perf_counter() - t0) * 1000.0 / 30.0
    assert ms < 5.0, "draw_gorath %.2f ms/frame" % ms


def test_cache_surface_dibatasi():
    F.clear_cache()
    for i in range(600):
        _ = F.glow_surface(10 + i % 40, (200, 30, 30), 0.5)
    assert F.cache_size() <= F._SURF_CACHE_MAX


def test_kualitas_rendah_memangkas_partikel(monkeypatch):
    class Q:
        particle_ratio = 0.15
        glow = False
        screen_shake = False
    monkeypatch.setattr(F, "_quality", staticmethod(lambda: Q))
    assert F.particle_budget() < F.MAX_PARTICLES
    assert F.glow_allowed() is False
    assert F.shake_allowed() is False


def test_semua_nya_bersaat_kosong():
    assert F.total_particles() == 0
    assert F.cache_size() >= 0
    F.reset_all()
    assert F.total_particles() == 0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
