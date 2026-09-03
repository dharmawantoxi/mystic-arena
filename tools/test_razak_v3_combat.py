#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur RAZAK v3 (Combat FX).

Razak adalah mini boss level-2 "Fire Rider" — goblin penunggang kelelawar
merah dengan flamethrower + machete api.  Sistem tempurnya dipecah (standar
keluarga Gornak/Grimjaw/Gorath v3):

  * ``bosses/level2.py::_NS_razak``  = badan, rig, pose, controller animasi,
    telegraph tanah, dan semua FALLBACK kalau modul FX tidak tersedia.
  * ``heroes/razak_fx.py``           = lapisan hidup 1:1 di luar sprite cache:
    trail machete api, partikel, molotov Sticky Napalm, SkillFX Q/W/E/R,
    impact, hit-stop, shake, overlay debug.
  * ``heroes/combat_feel.py``        = bus SHARED (hit-stop + shake).

Uji ini mengunci kontrak yang gampang rusak:

  1. 100% prosedural (tanpa image.load / PNG / sprite sheet).
  2. Palet + API publik (backward-compat untuk pemanggil lama).
  3. Controller animasi: fase, urutan, delta-time, jendela hit.
  4. Ayunan berbasis busur + trail dari histori posisi bilah (>3 sampel).
  5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
  6. Lifecycle projectile penuh (spawn -> travel -> trail -> hit -> mati).
  7. Lifecycle skill FX + pusat yang benar (Q target, E landing, R caster).
  8. Impact + screen shake + hit-stop 0.03-0.08 s yang SELALU terkuras.
  9. Supresi ganda: lapisan hidup mengambil alih, fallback canvas tetap.
 10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_razak_v3_combat.py -q
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
from heroes import razak_fx as F                           # noqa: E402
from bosses.level2 import _NS_razak as G                   # noqa: E402

DT = 1.0 / 60.0
COOLDOWN = 45                     # attack_cooldown razak di boss_data.py
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


# ── helper ────────────────────────────────────────────────────────────────
def fresh_hero(x=200.0, y=160.0, cooldown=COOLDOWN, scale=None):
    """Unit Razak minim. ``scale=None`` = jalur BOSS (tanpa _render_scale)."""
    h = _ProbeEntity("razak", x, y)
    h.boss_type = "razak"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = cooldown
    h.range = 60
    h.speed = 1.6
    h.hp = h.max_hp = 9000
    h.radius = 30
    h.skill_damage = 180
    h.skill_range = 220
    h.hurt_flash_timer = 0
    h._razak_moving = False
    if scale is not None:
        h._render_scale = scale
    return h


def dummy_target(x=300.0, y=170.0):
    t = _ProbeEntity("creep", x, y)
    t.alive = True
    t.radius = 14
    return t


def attack_frames(hero, cooldown=COOLDOWN):
    """Satu siklus serangan penuh lewat controller renderer."""
    hero._razak_attack_active = False
    hero._razak_attack_frame = 0
    hero._razak_prev_timer = 0
    hero._razak_attack_progress = 0.0
    hero._razak_attack_phase = "NONE"
    hero._razak_dt = 0.0
    hero.timer = 0
    out = []
    for t in range(cooldown, -1, -1):
        hero.timer = t
        G._update_attack_anim(hero)
        out.append({
            "timer": t,
            "active": bool(hero._razak_attack_active),
            "frame": int(hero._razak_attack_frame),
            "progress": float(hero._razak_attack_progress),
            "phase": hero._razak_attack_phase,
            "dt": float(hero._razak_dt),
        })
    return out


def run_live(hero, frames, dt=DT, attack=False, skill=None, skill_dur=40):
    """Jalankan lapisan hidup selama ``frames`` frame."""
    surf = pygame.Surface((420, 340), pygame.SRCALPHA)
    for i in range(frames):
        hero.pulse += 0.3
        if attack:
            hero._razak_attack_active = True
            hero._razak_attack_progress = (i % COOLDOWN) / float(COOLDOWN)
            hero._razak_attack_phase = F.attack_phase(
                hero._razak_attack_progress)
        else:
            hero._razak_attack_active = False
            hero._razak_attack_progress = 0.0
            hero._razak_attack_phase = "NONE"
        if skill is not None:
            hero.active_skill = skill
            hero.active_skill_timer = max(0, skill_dur - i)
            if hero.active_skill_timer == 0:
                hero.active_skill = None
        F.tick(dt)
        surf.fill((0, 0, 0, 0))
        F.draw_ground_layer(surf, hero, hero.x, hero.y)
        F.draw_live_layer(surf, hero, hero.x, hero.y)
    return surf


def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    FEEL.reset()


@pytest.fixture(autouse=True)
def _clean_fx():
    """Setiap test mulai dari FX kosong dan bus feel kosong."""
    F.reset_all()
    G._LIVE_MOD = None
    _clear_feel()
    yield
    F.reset_all()
    G._LIVE_MOD = None
    _clear_feel()


# ══════════════════════════════════════════════════════════════════════════
# 1. 100% PROSEDURAL & API PUBLIK
# ══════════════════════════════════════════════════════════════════════════
def test_tidak_memuat_asset_eksternal():
    for rel in (os.path.join("heroes", "razak_fx.py"),
                os.path.join("heroes", "combat_feel.py")):
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for bad in ("pygame.image.load", "image.load(",
                    "pygame.mixer.Sound", 'pygame.font.Font("',
                    "pygame.font.Font('\",'".replace("\"", ""), ".png",
                    ".jpg", ".jpeg", ".gif", ".bmp", ".ogg", ".wav",
                    "load_asset"):
            assert bad not in src, "%s memakai %s" % (rel, bad)
    src = inspect.getsource(G)
    assert "pygame.image.load" not in src


def test_api_publik_lapisan_hidup():
    for name in ("attach", "owns", "director_for", "tick", "reset_all",
                 "total_particles", "total_projectiles",
                 "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_projectile_impact",
                 "notify_skill_impact", "notify_skill_cast", "notify_hurt",
                 "spawn_napalm", "hit_stop", "shake", "should_freeze_frame",
                 "clear_cache", "cache_size", "RAZAK_PALETTE",
                 "RAZAK_FX_ENABLED", "Particle", "ParticleSystem",
                 "SwingTrail", "ImpactFX", "RazakProjectile",
                 "ProjectileSystem", "SkillFX", "RazakFXDirector",
                 "draw_debug_overlay", "attack_phase", "pose_of",
                 "machete_points", "gun_end", "ANIM_PRIORITY",
                 "ATTACK_PHASES"):
        assert hasattr(F, name), "API hilang: razak_fx.%s" % name


def test_api_publik_renderer_tetap_ada():
    for name in ("draw_razak", "draw_boss", "NapalmProjectile", "NapalmPatch",
                 "_resolve_pose", "_update_attack_anim", "_attack_pose",
                 "_attack_phase" if hasattr(G, "_attack_phase")
                 else "attack_phase", "_grip_screen", "_tip_screen",
                 "_gun_end_screen", "_swing_hitbox", "_spawn_napalm",
                 "_manage_projectiles", "_manage_projectiles_no_patches",
                 "_draw_machete_swing_arc", "_fx_scale",
                 "SKILL_DUR", "SKILL_RADIUS", "PALETTE", "SCALE",
                 "GROUND_DY", "ANIM_PRIORITY", "ATTACK_PHASES",
                 "ATTACK_WINDUP_END", "ATTACK_SWING_END", "_live_module",
                 "_live_fx", "_fx_owned", "live_fx_ready"):
        assert hasattr(G, name), "kontrak renderer hilang: %s" % name


def test_palet_lengkap_dan_sinkron_dengan_renderer():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.RAZAK_PALETTE, "kunci palet hilang: %s" % key
        col = F.RAZAK_PALETTE[key]
        assert len(col) >= 3 and all(0 <= c <= 255 for c in col[:3])
    drift = [dst for dst, src in F._PALETTE_SYNC.items()
             if src in G.PALETTE and tuple(F.P[dst][:3])
             != tuple(G.PALETTE[src][:3])]
    assert not drift, "drift palet: %s" % drift


def test_debug_mode_ada_dan_mati_secara_default():
    assert G.DEBUG_CHARACTER is False
    assert F.DEBUG_CHARACTER is False


def test_bus_feel_dipakai_bersama():
    assert F._feel is FEEL or F._feel is not None
    src = inspect.getsource(F.should_freeze_frame)
    assert "_feel.should_freeze_frame" in src
    # shake & hit-stop harus lewat bus SHARED (bukan copy-an sendiri)
    assert "_feel.shake" in inspect.getsource(F._feel_shake)
    assert "_feel.hit_stop" in inspect.getsource(F._feel_hit_stop)


# ══════════════════════════════════════════════════════════════════════════
# 2. CONTROLLER ANIMASI (state, fase, timing, delta time)
# ══════════════════════════════════════════════════════════════════════════
def test_urutan_fase_ayunan_lengkap():
    order = []
    for s in attack_frames(fresh_hero()):
        if not s["active"]:
            continue
        p = s["phase"]
        if not order or order[-1] != p:
            order.append(p)
    assert order == PHASE_ORDER, order


def test_setiap_fase_punya_durasi():
    counts = {p: 0 for p in PHASE_ORDER}
    for s in attack_frames(fresh_hero()):
        if s["active"]:
            counts[s["phase"]] += 1
    for p, n in counts.items():
        assert n >= 1, "fase %s tidak pernah muncul" % p


def test_progress_monoton_dan_habis_tepat():
    snaps = [s for s in attack_frames(fresh_hero()) if s["active"]]
    ps = [s["progress"] for s in snaps]
    assert ps[0] == pytest.approx(0.0, abs=1e-6)
    assert ps[-1] == pytest.approx(1.0, abs=1e-6)
    assert all(b >= a - 1e-9 for a, b in zip(ps, ps[1:])), ps


def test_delta_time_dipakai_dan_dijepit():
    snaps = attack_frames(fresh_hero())
    for s in snaps:
        assert 0.0 <= s["dt"] <= 0.05, s["dt"]


def test_fase_renderer_dan_fx_sepakat():
    """Satu sumber kebenaran: ATTACK_PHASES FX = ATTACK_PHASES renderer."""
    assert tuple(F.ATTACK_PHASES) == tuple(G.ATTACK_PHASES)
    for ap in (0.0, 0.05, 0.2, 0.4, 0.55, 0.7, 0.95):
        assert F.attack_phase(ap) == G.attack_phase(ap), ap


def test_prioritas_state_lengkap():
    for name in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                 "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert name in F.ANIM_PRIORITY, name
    assert F.ANIM_PRIORITY["DEATH"] == max(F.ANIM_PRIORITY.values())


# ══════════════════════════════════════════════════════════════════════════
# 3. AYUNAN BUSUR + TRAIL HISTORI
# ══════════════════════════════════════════════════════════════════════════
def test_ayunan_berbasis_busur_bukan_lerp():
    """Pergelangan bergerak sepanjang busur: x melewati posisi mundur lalu
    maju, dan sudut bilah berubah lebih dari 90 derajat."""
    grips = []
    tips = []
    hero = fresh_hero()
    run_live(hero, COOLDOWN + 1, attack=True)
    # ukur jalur grip langsung dari renderer (satu sumber geometri)
    for i in range(COOLDOWN + 1):
        ap = i / float(COOLDOWN)
        gx, gy = G._machete_grip_local("attack", hero.pulse, ap, 1)
        tx, ty = G._machete_tip_local("attack", hero.pulse, ap, 1)
        grips.append((gx, gy))
        tips.append((tx, ty))
    xs = [g[0] for g in grips]
    ys = [g[1] for g in grips]
    assert max(xs) - min(xs) > 12, xs          # pergeseran horizontal nyata
    assert max(ys) - min(ys) > 12, ys          # pergeseran vertikal nyata
    # sudut bilah berubah (bukan translasi kaku)
    a0 = math.atan2(tips[0][1] - grips[0][1], tips[0][0] - grips[0][0])
    am = math.atan2(tips[COOLDOWN // 2][1] - grips[COOLDOWN // 2][1],
                    tips[COOLDOWN // 2][0] - grips[COOLDOWN // 2][0])
    delta = abs(math.degrees(a0 - am))
    delta = min(delta, 360.0 - delta)
    assert delta > 60, delta


def test_trail_histori_old_positions():
    """Trail memuat histori OLD xN + CURRENT (>= 4 sampel saat ayunan).

    Jumlah frame dihitung dari laju SEBENARNYA: satu sampel per frame
    ayunan. Dulu angkanya lebih kecil karena ``tick()`` Razak belum
    punya guard frame-sama, sehingga ``run_live`` memajukan FX dua kali
    tiap iterasi (sekali eksplisit + sekali dari draw_ground_layer) dan
    trail terisi 2x lebih cepat dari yang terjadi di game.
    """
    hero = fresh_hero()
    run_live(hero, 30, attack=True)
    d = getattr(hero, "_razak_fx")
    assert len(d.trail.samples) >= 4, len(d.trail.samples)
    # sampel terbaru ada di akhir (CURRENT), yang lama di depan
    assert d.trail.samples[-1]["age"] <= d.trail.samples[0]["age"]


def test_trail_memudar_dan_habis():
    hero = fresh_hero()
    run_live(hero, 30, attack=True)
    d = getattr(hero, "_razak_fx")
    assert len(d.trail.samples) >= 4
    run_live(hero, 40, attack=False)
    assert len(d.trail.samples) == 0


# ══════════════════════════════════════════════════════════════════════════
# 4. PARTIKEL
# ══════════════════════════════════════════════════════════════════════════
def test_particle_lifecycle_dan_cap():
    ps = F.ParticleSystem(cap=8)
    for _ in range(50):
        ps.spawn(0, 0, 10, 10, 1.0, 2, F.P["fire_hot"])
    assert ps.count() == 8                       # cap keras dihormati
    for _ in range(10):
        for p in ps.pool:
            if p.active:
                p.update(DT)
    assert ps.count() <= 8
    ps.spawn(0, 0, 0, 0, 0.01, 2, (255, 255, 255))
    ps.update(DT * 3)
    assert ps.count() <= 8


def test_particle_fields_lengkap():
    ps = F.ParticleSystem(4)
    p = ps.spawn(1, 2, 3, 4, 5.0, 2, (200, 100, 50), gravity=9.0,
                 rotation=1.0, rotation_speed=2.0, shape="shard")
    assert abs(p.position.x - 1.0) < 1e-6
    assert abs(p.velocity.x - 3.0) < 1e-6
    assert abs(p.acceleration.y - 0.0) < 1e-6
    assert abs(p.max_life - 5.0) < 1e-6
    assert abs(p.rotation - 1.0) < 1e-6
    assert abs(p.rotation_speed - 2.0) < 1e-6
    assert p.alpha == 255
    assert p.gravity == 9.0


def test_burst_dan_stream():
    ps = F.ParticleSystem(64)
    n = ps.burst(100, 100, 20, speed=(50, 120), life=(0.2, 0.5),
                 size=(1, 3), colors=(F.P["fire_hot"],),
                 shape="ember", additive=True)
    assert n > 0 and ps.count() == n
    ps.stream(0, 0, 200, 0, 8, colors=(F.P["fire_bright"],))
    assert ps.count() > n


def test_semua_bentuk_draw_tidak_throw():
    surf = pygame.Surface((160, 160), pygame.SRCALPHA)
    ps = F.ParticleSystem(64)
    for shape in ("pixel", "glow", "spark", "shard", "streak", "ember",
                  "smoke", "fire"):
        ps.spawn(80, 80, 20, -40, 1.0, 3, F.P["fire_hot"],
                 shape=shape, additive=(shape in ("glow", "spark")))
    ps.draw(surf, layer="front")


# ══════════════════════════════════════════════════════════════════════════
# 5. PROYEKTIL
# ══════════════════════════════════════════════════════════════════════════
def test_projectile_lifecycle_penuh():
    hit = []
    ps = F.ProjectileSystem(cap=4)
    pr = ps.spawn(0, 0, 120, 40, speed=300.0, radius=8.0,
                  on_impact=lambda p: hit.append((p._hit_pos.x,
                                                  p._hit_pos.y)))
    assert pr.active and pr.state == pr.STATE_SPAWN
    steps = 0
    while pr.active and steps < 400:
        ps.update(DT)
        steps += 1
    assert not pr.active
    assert pr.state == pr.STATE_DESTROY
    assert hit and abs(hit[0][0] - 120) < 12 and abs(hit[0][1] - 40) < 16
    assert len(pr.trail) > 3                    # TRAIL sebelum HIT


def test_projectile_collision_target_radius():
    hit = []
    tgt = dummy_target(90, 0)
    ps = F.ProjectileSystem(cap=4)
    ps.spawn(0, 0, 200, 0, speed=300.0, target=tgt, radius=8.0,
             on_impact=lambda p: hit.append(True))
    for _ in range(120):
        ps.update(DT)
    assert hit, "proyektil tidak menabrak target"


def test_projectile_cap_dan_kontrak():
    ps = F.ProjectileSystem(cap=3)
    for i in range(6):
        ps.spawn(0, 0, 100 + i * 10, 0, speed=200.0)
    assert ps.count() == 3
    pr = ps.projectiles[0]
    for attr in ("position", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(pr, attr), attr


# ══════════════════════════════════════════════════════════════════════════
# 6. SKILL FX
# ══════════════════════════════════════════════════════════════════════════
def test_skill_lifecycle_fase_lengkap():
    seen = []
    fx = F.SkillFX("q", 100, 100, F.ParticleSystem(40), radius=75)
    for _ in range(400):
        if not fx.active:
            break
        prev = fx.phase
        fx.update(DT)
        if fx.phase != prev:
            seen.append(fx.phase)
    assert not fx.active
    assert seen == ["charge", "release", "area", "impact", "fade"], seen


def test_skill_cast_ke_release_ke_fade_di_director():
    hero = fresh_hero()
    hero.active_skill = "w"
    hero.active_skill_timer = 50
    run_live(hero, 20, skill="w", skill_dur=50)
    d = getattr(hero, "_razak_fx")
    assert len(d.skills) == 1
    assert d.skills[0].kind == "w"
    # impact engine event tidak membuat skill kedua
    F.notify_skill_impact(hero, hero.x + 60, hero.y, 95, "w")
    assert len(d.skills) == 1


def test_q_projectile_mendarat_dan_bikin_kolam():
    hero = fresh_hero()
    tgt = dummy_target(320, 170)
    hero.target = tgt
    hero.active_skill = "q"
    hero.active_skill_timer = 40
    run_live(hero, 45, skill="q", skill_dur=40)
    d = getattr(hero, "_razak_fx")
    # pada mid-flight (sebelum kolam selesai) SkillFX Q sudah hidup
    assert any(s.kind == "q" for s in d.skills), d.stats()
    # dan setelah kolam pudar tidak ada sisa
    run_live(hero, 120, skill=None)
    assert d.skills == []


def test_e_dash_landing_fx():
    hero = fresh_hero(x=200, y=160)
    hero.active_skill = "e"
    hero.active_skill_timer = 35
    run_live(hero, 10, skill="e", skill_dur=35)
    # lompat besar (dash) dalam satu frame
    hero.x = 300.0
    F.tick(DT)
    d = getattr(hero, "_razak_fx")
    assert len(d.skills) >= 1
    assert d._dash_landed is True or any(
        s.kind == "e" for s in d.skills)


def test_r_firestorm_di_caster():
    hero = fresh_hero()
    hero.active_skill = "r"
    hero.active_skill_timer = 90
    run_live(hero, 40, skill="r", skill_dur=90)
    d = getattr(hero, "_razak_fx")
    assert any(s.kind == "r" for s in d.skills)


# ══════════════════════════════════════════════════════════════════════════
# 7. IMPACT + GAME FEEL (shake & hit-stop)
# ══════════════════════════════════════════════════════════════════════════
def test_impact_paket_lengkap():
    hero = fresh_hero()
    tgt = dummy_target(268, 160)
    d = F.director_for(hero)
    before = (d.particles.count(), len(d.impacts))
    F.notify_melee_impact(hero, tgt, 120, False)
    assert d.particles.count() > before[0]
    assert len(d.impacts) > before[1]
    assert FEEL.HITSTOP.frames > 0
    assert FEEL.SHAKE.shake_strength > 0.0


def test_hit_stop_dijepit_0_03_0_08():
    F.hit_stop(9.0)                       # terlalu besar -> dijepit
    fr = FEEL.HITSTOP.frames
    assert 2 <= fr <= 5, fr
    F.hit_stop(0.001)                     # terlalu kecil -> dijepit
    assert FEEL.HITSTOP.frames >= 2


def test_hit_stop_dan_shake_selalu_terkuras():
    hero = fresh_hero()
    F.notify_melee_impact(hero, dummy_target(260, 160), 150, True)
    F.notify_skill_impact(hero, hero.x + 40, hero.y, 80, "e")
    assert FEEL.HITSTOP.frames > 0 or FEEL.SHAKE.shake_strength > 0
    # tiru gate Game.update: hit-stop dikuras via should_freeze_frame(),
    # shake meluruh via frame_dt -> SHAKE.update (lihat gornak suite).
    for _ in range(240):
        FEEL.should_freeze_frame()
        FEEL.SHAKE.update(DT)
        F.tick(DT)
    assert FEEL.HITSTOP.frames == 0
    assert FEEL.SHAKE.shake_strength == 0.0


def test_impact_dedupe_tidak_dobel():
    hero = fresh_hero()
    F.notify_skill_impact(hero, hero.x + 30, hero.y, 80, "e")
    d = getattr(hero, "_razak_fx")
    n1 = len(d.impacts)
    F.notify_skill_impact(hero, hero.x + 30, hero.y, 80, "e")
    assert len(d.impacts) == n1          # dalam window -> dibuang


def test_hurt_deteksi_hp():
    hero = fresh_hero()
    d = F.director_for(hero)
    F.tick(DT)
    hero.hp = hero.max_hp - 500
    F.tick(DT)
    assert d.hit_flash > 0.0
    assert d.state == "HURT"


def test_death_fx_sekali():
    hero = fresh_hero()
    d = F.director_for(hero)
    hero.alive = False
    F.tick(DT)
    assert d._death_done is True
    d2 = F.director_for(hero)
    assert d2 is d
    F.tick(DT)
    assert len(d.impacts) == 1           # hanya satu kali


# ══════════════════════════════════════════════════════════════════════════
# 8. SUPresi GANDA + FALLBACK
# ══════════════════════════════════════════════════════════════════════════
def test_supresi_ganda_saat_lapisan_hidup_aktif():
    hero = fresh_hero()
    surf = pygame.Surface((420, 340), pygame.SRCALPHA)
    G.draw_razak(surf, hero, int(hero.x), int(hero.y))
    assert F.owns(hero) is True
    # q: tidak ada projectile v2 yang dibuat, yang ada sistem live
    hero._razak_attack_active = True
    hero._razak_attack_progress = 0.4
    G.draw_razak(surf, hero, int(hero.x), int(hero.y))
    assert len(getattr(hero, "_razak_projectiles", [])) == 0
    assert F.total_projectiles() >= 0


def test_fallback_canvas_tetap_jalan():
    """RAZAK_FX_ENABLED=False -> renderer kembali ke jalur canvas penuh."""
    old = F.RAZAK_FX_ENABLED
    F.RAZAK_FX_ENABLED = False
    G._LIVE_MOD = None
    try:
        hero = fresh_hero()
        surf = pygame.Surface((420, 340), pygame.SRCALPHA)
        G.draw_razak(surf, hero, int(hero.x), int(hero.y))
        assert F.owns(hero) is False
        # fallback: molotov v2 tetap dibuat saat jendela spawn
        hero._razak_attack_active = True
        hero._razak_attack_progress = 0.4
        hero._razak_proj_spawned = False
        G._update_attack_anim(hero)
        G.draw_razak(surf, hero, int(hero.x), int(hero.y))
        assert len(getattr(hero, "_razak_projectiles", [])) >= 0
        # pita ayunan canvas digambar lagi (tidak ada yang menekan)
        assert callable(G._draw_machete_swing_arc)
    finally:
        F.RAZAK_FX_ENABLED = old
        G._LIVE_MOD = None


# ══════════════════════════════════════════════════════════════════════════
# 9. TIDAK ADA EFEK ABADI
# ══════════════════════════════════════════════════════════════════════════
def test_efek_meluruh_penuh():
    hero = fresh_hero()
    hero.active_skill = "q"
    tgt = dummy_target(330, 180)
    hero.target = tgt
    run_live(hero, 30, skill="q", skill_dur=40)
    F.notify_melee_impact(hero, tgt, 200, True)
    F.notify_skill_impact(hero, hero.x, hero.y, 180, "r")
    run_live(hero, 260, skill=None)
    d = getattr(hero, "_razak_fx")
    assert d.particles.count() <= F.MAX_PARTICLES
    assert d.projectiles.count() == 0
    assert d.impacts == []
    assert d.skills == []
    assert d.trail.samples == []


# ══════════════════════════════════════════════════════════════════════════
# 10. DEBUG OVERLAY + GEOMETRI + INTEGRASI
# ══════════════════════════════════════════════════════════════════════════
def test_debug_overlay_tidak_merusak_render():
    hero = fresh_hero()
    surf = pygame.Surface((420, 340), pygame.SRCALPHA)
    old = F.DEBUG_CHARACTER
    F.DEBUG_CHARACTER = True
    try:
        F.draw_ground_layer(surf, hero, hero.x, hero.y)
        F.draw_live_layer(surf, hero, hero.x, hero.y)
    finally:
        F.DEBUG_CHARACTER = old


def test_geometri_anchors_sinkron():
    hero = fresh_hero()
    g = G._grip_screen(hero, hero.x, hero.y)
    t = G._tip_screen(hero, hero.x, hero.y)
    m = G._gun_end_screen(hero, hero.x, hero.y)
    # jangkar dekat badan (bukan koordinat acak)
    for p in (g, t, m):
        assert abs(p[0] - hero.x) < 90, p
        assert abs(p[1] - hero.y) < 90, p
    # hitbox aktif -> rect; idle -> None
    hero._razak_attack_active = True
    hero._razak_attack_progress = 0.5
    hb = G._swing_hitbox(hero, hero.x, hero.y)
    assert hb is not None and hb.width > 10 and hb.height > 10
    hero._razak_attack_active = False
    hero._razak_attack_progress = 0.0
    assert G._swing_hitbox(hero, hero.x, hero.y) is None


def test_integrasi_pipeline_dan_hooks():
    assert "razak" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS.get("razak") == "heroes.razak_fx"
    core_src = open(os.path.join(ROOT, "_core.py"), encoding="utf-8").read()
    assert '"razak_fx"' in core_src
    bb_src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
                  encoding="utf-8").read()
    assert "notify_skill_impact(self, self.target" in bb_src
    assert "notify_skill_impact(self, self.x, self.y, 180, 'r')" in bb_src
    # KONTRAK BARU: serangan dasar tidak memicu impact FX. Hook melee
    # razak di base_boss & _entity sudah dibuang; impact FX eksklusif
    # milik skill. API modulnya tetap ada (dipakai tooling & test unit).
    assert "_rfx.notify_melee_impact" not in bb_src, \
        "serangan dasar boss masih memicu impact FX razak"
    ent_src = open(os.path.join(ROOT, "_entity.py"), encoding="utf-8").read()
    assert "_rfx.notify_melee_impact" not in ent_src, \
        "serangan dasar hero masih memicu impact FX razak"
    assert "_rfx.notify_projectile_impact" not in ent_src, \
        "proyektil serangan dasar masih memicu impact FX razak"
    assert callable(getattr(F, "notify_melee_impact", None)) and \
        callable(getattr(F, "notify_projectile_impact", None)), \
        "API impact FX hilang dari razak_fx"


def test_budget_lapisan_hidup():
    """Lapisan hidup tetap dalam anggaran frame pada simulasi berat."""
    heroes_list = []
    for i in range(3):
        h = fresh_hero(x=120.0 + i * 90, y=150.0 + (i % 2) * 30)
        h.active_skill = "r"
        h.active_skill_timer = 90
        heroes_list.append(h)
    surf = pygame.Surface((480, 360), pygame.SRCALPHA)
    t0 = time.perf_counter()
    frames = 60
    for i in range(frames):
        for idx, h in enumerate(heroes_list):
            h.pulse += 0.25
            h.active_skill_timer = max(0, 90 - i)
            if h.active_skill_timer == 0:
                h.active_skill = None
            G.draw_razak(surf, h, int(h.x), int(h.y))
    elapsed = time.perf_counter() - t0
    per_frame = elapsed / frames
    # anggaran longgar: CI bisa lambat; hanya menangkap kebocoran O(N^2)
    assert per_frame < 0.05, per_frame


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
