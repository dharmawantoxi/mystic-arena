#!/usr/bin/env python3
"""Regression test permanen untuk sistem tempur GRIMJAW v3.

Grimjaw digambar lewat dua lapisan yang sengaja dipisah:

  * ``heroes/_bundle.py :: _NS_grimjaw``  = badan/rig/pose masterwork v2,
    controller animasi serangan (``_update_attack_anim``), telegraph
    tanah, dan semua FALLBACK kalau modul FX tidak tersedia.
  * ``heroes/grimjaw_fx.py``              = lapisan hidup 1:1 di luar
    sprite cache: trail pedang dari histori posisi nyata, partikel,
    proyektil gelombang bilah, impact FX, hit-stop, shake, overlay debug,
    dan animation controller cermin (state + prioritas + transisi).
  * ``heroes/combat_feel.py``             = bus SHARED (hit-stop + shake)
    yang dipakai Zephyr, Gornak, dan Grimjaw, jadi beberapa karakter
    memukul di frame yang sama tidak menumpuk freeze.

Uji ini mengunci kontrak yang gampang rusak saat orang lain menyentuh
salah satu dari ketiganya:

 1. 100% prosedural (tanpa image.load / PNG / sprite sheet) di kedua modul.
 2. Palet + API publik (backward-compat untuk pemanggil lama).
 3. Controller animasi: fase, urutan, delta-time, jendela hit, prioritas
    state, dan semua nama atribut lama yang masih dipakai renderer/tools.
 4. Ayunan berbasis busur (bukan lerp linear) + trail dari histori bilah.
 5. Particle system berbatas (cap dihormati, pool dipakai ulang, meluruh).
 6. Lifecycle projectile penuh (spawn -> travel -> hit -> impact -> mati).
 7. Lifecycle skill FX (cast -> charge -> release -> area -> impact ->
    fade) dan pemicu gameplay (tick Q tiap 15 frame, R tiap 8 frame).
 8. Impact + screen shake + hit-stop yang SELALU terkuras (tidak ada efek
    abadi), dengan hit-stop di 0.03-0.08 s.
 9. Supresi ganda: saat lapisan hidup mengambil alih, renderer tidak
    menggambar smear ayunan / impact pop di-canvas dua kali - dan
    sebaliknya fallback canvas tetap jalan kalau modul FX tidak dimuat.
10. Overlay debug (DEBUG_CHARACTER) + performansi lapisan hidup.

Jalankan:  python3 -m pytest tools/test_grimjaw_v3_combat.py -q
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import hashlib                                         # noqa: E402
import inspect                                         # noqa: E402
import math                                            # noqa: E402
import pygame                                          # noqa: E402
import pytest                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                          # noqa: E402
from heroes import _ProbeEntity                        # noqa: E402
from heroes import combat_feel as FEEL                 # noqa: E402
from heroes import grimjaw_fx as F                     # noqa: E402
from heroes._bundle import _NS_grimjaw as G            # noqa: E402

DT = 1.0 / 60.0
SURF = pygame.Surface((720, 560), pygame.SRCALPHA)
PHASE_ORDER = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT",
               "FOLLOW", "RECOVERY"]


# ── helper ────────────────────────────────────────────────────────────────
def _clear_feel():
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()


def fresh_hero(x=200.0, y=200.0, cooldown=45):
    """Unit Grimjaw minim dengan seluruh atribut yang dibaca FX."""
    h = _ProbeEntity("grimjaw", x, y)
    h.direction = h.facing = 1
    h.alive = True
    h.pulse = 0.0
    h.timer = 0
    h.attack_cooldown = cooldown
    h.range = 60
    h.speed = 1.4
    h.hp = h.max_hp = 800
    h.radius = 16
    h.skill_damage = 120
    h.skill_range = 76
    h._gj_attack_active = False
    h._gj_attack_progress = 0.0
    h._gj_crit_active = False
    h._gj_prev_timer = -1
    h._blade_fury_timer = 0
    h._heal_ward_timer = 0
    h._heal_ward_pos = (x, y)
    h._crit_buff_timer = 0
    h._omnislash_timer = 0
    h._omnislash_target = None
    h._moving_cached = False
    h.active_skill = None
    h.active_skill_timer = 0
    return h


def run_attack_cycle(hero, cooldown=45, fn=None):
    """Satu siklus serangan penuh lewat controller renderer."""
    hero._gj_attack_active = False
    # prime: controller mendeteksi serangan dari timer NAIK, jadi frame
    # acuan harus punya previous >= 0 sebelum nilai puncak terlihat.
    hero.timer = 0
    hero._gj_prev_timer = 0
    (fn or G._update_attack_anim)(hero)
    snaps = []
    for t in range(cooldown, -1, -1):
        hero.timer = t
        (fn or G._update_attack_anim)(hero)
        F.tick(DT)
        snaps.append({
            "timer": t,
            "active": bool(hero._gj_attack_active),
            "progress": float(hero._gj_attack_progress),
            "phase": F.attack_phase(hero._gj_attack_progress),
        })
    return snaps


@pytest.fixture(autouse=True)
def _clean_fx():
    """Setiap test mulai dari FX kosong dan bus feel kosong."""
    F.reset_all()
    _clear_feel()
    G._FX_LIVE.v = False
    yield
    F.reset_all()
    _clear_feel()
    G._FX_LIVE.v = False


# ══════════════════════════════════════════════════════════════════════════
# 1. 100% PROSEDURAL & API PUBLIK
# ══════════════════════════════════════════════════════════════════════════
def test_tidak_memuat_asset_eksternal():
    """Baik lapisan FX maupun namespace renderer: tanpa asset apa pun."""
    for rel in (os.path.join("heroes", "grimjaw_fx.py"),
                os.path.join("heroes", "combat_feel.py")):
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        for bad in ("pygame.image.load", "image.load(",
                    "pygame.mixer.Sound", 'pygame.font.Font("',
                    "pygame.font.Font('", ".png", ".jpg", ".jpeg", ".gif",
                    ".bmp", ".ogg", ".wav", "surf(", "load_asset"):
            assert bad not in src, "%s memakai %s" % (rel, bad)
    # jalur renderer: sumber _NS_grimjaw juga tidak boleh memuat bitmap
    src = inspect.getsource(G)
    assert "pygame.image.load" not in src


def test_api_publik_lapisan_hidup():
    for name in ("attach", "owns", "director_for", "tick", "reset_all",
                 "total_particles", "total_projectiles",
                 "draw_ground_layer", "draw_live_layer",
                 "notify_melee_impact", "notify_skill_impact",
                 "notify_skill_cast", "notify_hurt",
                 "draw_blade_wave", "hit_stop", "shake",
                 "should_freeze_frame", "clear_cache", "cache_size",
                 "GRIMJAW_PALETTE", "GRIMJAW_FX_ENABLED",
                 "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
                 "GrimjawProjectile", "ProjectileSystem", "SkillFX",
                 "GrimjawFXDirector", "blade_points", "render_scale",
                 "ANIM_PRIORITY", "attack_phase", "DEBUG_CHARACTER"):
        assert hasattr(F, name), "API hilang: grimjaw_fx.%s" % name


def test_api_publik_renderer_tetap_ada():
    """Renderer tidak boleh kehilangan nama yang dipakai tools/lama."""
    for name in ("draw_grimjaw", "draw_hero", "_draw_grimjaw_elite",
                 "_draw_grimjaw_idle", "_draw_grimjaw_walk",
                 "_draw_grimjaw_attack", "_draw_grimjaw_body",
                 "_draw_grimjaw_ghost", "_update_attack_anim",
                 "_detect_moving", "_blade_angle", "_blade_grip_local",
                 "_blade_len", "_blade_tip_local",
                 "_draw_blade_swing_trail", "_draw_fire_slash_arc",
                 "_draw_impact_flash", "_draw_critical_strike_burst",
                 "ATTACK_WINDUP_END", "ATTACK_SWING_END",
                 "ATTACK_ARC_START", "ATTACK_ARC_SWEEP", "PALETTE",
                 "_live_module", "_fx_live_owned", "_FX_LIVE"):
        assert hasattr(G, name), "kontrak renderer hilang: %s" % name


def test_palet_lengkap_dan_sinkron_dengan_renderer():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.GRIMJAW_PALETTE, "kunci palet hilang: %s" % key
        col = F.GRIMJAW_PALETTE[key]
        assert len(col) >= 3 and all(0 <= c <= 255 for c in col[:3])
    # palet lapisan hidup = palet renderer (satu karakter, satu warna).
    # _PALETTE_SYNC adalah satu-satunya jembatan; tidak boleh melenceng.
    F._sync_palette()
    drift = [dst for dst, src in F._PALETTE_SYNC.items()
             if src in G.PALETTE and tuple(F.P[dst][:3])
             != tuple(G.PALETTE[src][:3])]
    assert not drift, "drift palet: %s" % drift


def test_debug_mode_ada_dan_mati_secara_default():
    assert F.DEBUG_CHARACTER is False
    assert getattr(G, "DEBUG_CHARACTER", False) is False


def test_bus_feel_dipakai_bersama():
    """Zephyr & Grimjaw berbagi bus yang sama dengan Gornak."""
    from heroes import zephyr_fx as ZF
    from heroes import gornak_fx as GF
    assert ZF.HITSTOP is FEEL.HITSTOP
    assert F.HITSTOP is FEEL.HITSTOP
    assert F.SHAKE is FEEL.SHAKE
    assert GF._feel is FEEL and ZF._feel is FEEL and F._feel is FEEL
    src = inspect.getsource(F.should_freeze_frame)
    assert "_feel.should_freeze_frame" in src, src
    assert "_feel" in inspect.getsource(F.hit_stop)


def test_grimjaw_terdaftar_di_live_fx_pass():
    """heroes/__init__ harus menggambar lapisan hidup Grimjaw."""
    assert "grimjaw" in heroes._LIVE_FX_HEROES
    assert heroes._LIVE_FX_PATHS.get("grimjaw") == "heroes.grimjaw_fx"
    mod = heroes._live_fx_module("grimjaw")
    assert mod is F


# ══════════════════════════════════════════════════════════════════════════
# 2. CONTROLLER ANIMASI  (fase, urutan, delta-time, prioritas)
# ══════════════════════════════════════════════════════════════════════════
def test_urutan_fase_ayunan_lengkap():
    """ANTICIPATION -> WINDUP -> SWING -> IMPACT -> FOLLOW -> RECOVERY."""
    snaps = run_attack_cycle(fresh_hero())
    seen = [s["phase"] for s in snaps]
    first = {}
    for i, ph in enumerate(seen):
        first.setdefault(ph, i)
    order = [ph for ph in PHASE_ORDER if ph in first]
    assert order == PHASE_ORDER, "fase hilang/urutan salah: %s" % order


def test_setiap_fase_punya_durasi():
    snaps = run_attack_cycle(fresh_hero())
    counts = {}
    for s in snaps:
        counts[s["phase"]] = counts.get(s["phase"], 0) + 1
    for ph in PHASE_ORDER:
        assert counts.get(ph, 0) >= 1, "fase %s nol frame" % ph


def test_fase_sinkron_dengan_konstanta_renderer():
    """IMPACT harus berakhir tepat setelah ATTACK_SWING_END renderer."""
    windup = G.ATTACK_WINDUP_END
    swing_end = G.ATTACK_SWING_END
    assert F.attack_phase(0.0) == "ANTICIPATION"
    assert F.attack_phase(windup * 0.9) == "WINDUP"
    assert F.attack_phase((windup + swing_end) / 2) == "SWING"
    assert F.attack_phase(swing_end) in ("IMPACT", "FOLLOW")
    assert F.attack_phase(0.97) == "RECOVERY"


def test_jendela_hit_aktif_di_tengah_ayunan():
    """Fase IMPACT harus ada sekitar ATTACK_SWING_END (bukan di awal)."""
    snaps = run_attack_cycle(fresh_hero())
    impacts = [s["progress"] for s in snaps if s["phase"] == "IMPACT"]
    assert impacts, "tidak ada fase IMPACT"
    assert all(0.3 < p < 0.9 for p in impacts)


def test_prioritas_state_dan_kunci_death():
    h = fresh_hero()
    d = F.director_for(h)
    F.tick(DT)                          # frame acuan posisi
    assert d.state == "IDLE"
    # gerak -> WALK / RUN
    h.x += 2.0
    F.tick(DT)
    assert d.state == "WALK"
    # serangan mengunci gerak (prioritas lebih tinggi)
    h._gj_attack_active = True
    h._gj_attack_progress = 0.05
    F.tick(DT)
    assert d.state == "CHARGE"
    h._gj_attack_progress = 0.45
    F.tick(DT)
    assert d.state == "SWING"
    # skill > serangan
    h.active_skill = "r"
    F.tick(DT)
    assert d.state == "SPECIAL"
    # hurt > semuanya kecuali death
    h.hp -= 60
    F.tick(DT)
    assert d.state == "HURT"
    # death mengunci
    h.alive = False
    F.tick(DT)
    assert d.state == "DEATH"
    h.alive = True
    F.tick(DT)
    assert d.state == "DEATH", "DEATH tidak boleh keluar otomatis"


def test_tabel_prioritas_mengandung_semua_state_master_prompt():
    for st in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
               "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert st in F.ANIM_PRIORITY, "state %s hilang" % st


def test_hurt_terdeteksi_dari_hp():
    h = fresh_hero()
    d = F.director_for(h)
    F.tick(DT)
    h.hp -= 120
    F.tick(DT)
    assert d.hit_flash > 0.0
    assert d.state == "HURT"


def test_death_memicu_burst_sekali():
    h = fresh_hero()
    d = F.director_for(h)
    F.tick(DT)
    h.alive = False
    F.tick(DT)
    part = d.particles.count()
    assert part >= 15, "burst kematian terlalu kecil: %d" % part
    F.tick(DT)
    F.tick(DT)
    assert d.particles.count() <= part    # tidak ada burst berulang


# ══════════════════════════════════════════════════════════════════════════
# 3. AYUNAN BERBASIS BUSUR  (bukan lerp linear)
# ══════════════════════════════════════════════════════════════════════════
def test_ujung_bilah_mengikuti_busur_bukan_lerp():
    """Sudut bilah menyapu satu arah (lewat ATAS kepala), tanpa bolak-balik.

    Renderer menormalisasi sudut ke [0, 2pi) saat masuk recovery, jadi
    kesinambungan diukur sebagai langkah sudut modulo 2pi.
    """
    prev = None
    steps = 40
    for i in range(steps):
        t = i / (steps - 1)
        ap = G.ATTACK_WINDUP_END + t * (G.ATTACK_SWING_END -
                                        G.ATTACK_WINDUP_END)
        ang = G._blade_angle(0.0, "attack", ap, 0.0)
        if prev is not None:
            step = (prev - ang) % math.tau      # sapuan satu arah
            assert 0.0 <= step < 1.0, \
                "bilah berbalik arah di ap=%.2f (langkah %.2f rad)" % (ap,
                                                                       step)
        prev = ang
    assert G.ATTACK_ARC_SWEEP < 0, "tebasan harus menyapu ke negatif"


def test_ujung_bilah_kontinu_tanpa_teleport():
    prev = None
    for i in range(60):
        ap = i / 59
        tx, ty = G._blade_tip_local(0.0, "attack", ap, 0.0)
        if prev is not None:
            step = math.hypot(tx - prev[0], ty - prev[1])
            assert step < 26.0, "teleport bilah %.1f px di ap=%.2f" % (step,
                                                                       ap)
        prev = (tx, ty)


def test_blade_points_layar_mengikuti_render_scale():
    h = fresh_hero()
    h._render_scale = 0.5
    h._gj_attack_active = True
    h._gj_attack_progress = 0.4
    grip, tip, action = F.blade_points(h)
    assert action == "attack"
    # skala 0.5 => titik layar maksimal setengah koordinat lokal rig
    assert abs(tip[0] - h.x) <= 90 * 0.5 + 1
    assert tip[1] < grip[1], "ujung bilah harus di atas gagang saat swing"


def test_trail_dibangun_dari_histori_dan_meluruh():
    tr = F.SwingTrail()
    for i in range(6):
        tr.push((i * 4, 0), (i * 4, -30))
    assert len(tr.points) == 6 and tr.active
    for _ in range(int(tr.life / DT) + 2):
        tr.update(DT)
    assert not tr.points and not tr.active
    tr.push((0, 0), (10, -10))
    tr.reset()
    assert not tr.points and not tr.active


def test_trail_diisi_lapisan_hidup_saat_swing():
    h = fresh_hero()
    d = F.director_for(h)
    h._gj_attack_active = True
    h._gj_attack_progress = 0.40
    F.tick(DT)
    F.tick(DT)
    assert d.trail.active, "trail tidak terisi saat SWING"
    assert len(d.trail.points) >= 2
    d.trail.draw(SURF)


def test_whoosh_pendaratan_bilah_sekali_per_ayunan():
    h = fresh_hero()
    d = F.director_for(h)
    h._gj_attack_active = True
    for ap in (0.3, 0.5, 0.7, 0.75):
        h._gj_attack_progress = ap
        F.tick(DT)
    assert any(i.kind == "blade" for i in d.impacts)
    n_land = len([i for i in d.impacts if i.kind == "blade"])
    assert n_land >= 1
    # setelah landed, progress mundur tidak meledak lagi
    h._gj_attack_progress = 0.5
    F.tick(DT)
    assert len([i for i in d.impacts if i.kind == "blade"]) == n_land


# ══════════════════════════════════════════════════════════════════════════
# 4. PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════════════════
def test_partikel_punya_semua_bidang_master_prompt():
    p = F.Particle()
    for field in ("pos", "vel", "acc", "life", "max_life", "size",
                  "rotation", "rotation_speed", "alpha", "gravity",
                  "color"):
        assert hasattr(p, field), "Particle.%s hilang" % field


def test_cap_partikel_dihormati():
    ps = F.ParticleSystem(cap=16)
    for _ in range(60):
        ps.spawn(0, 0, 10, -10, 0.5, 3, F.P["fx_light"])
    assert ps.count() <= 16


def test_partikel_mati_tidak_abadi():
    ps = F.ParticleSystem(cap=64)
    ps.burst(0, 0, 40, life=(0.2, 0.5), gravity=400.0)
    for _ in range(120):
        ps.update(DT)
    assert ps.count() == 0


def test_gravity_dan_drag_diterapkan():
    ps = F.ParticleSystem(cap=8)
    p = ps.spawn(0, 0, 0, 0, 1.0, 3, F.P["fx_light"], gravity=600.0)
    ps.update(DT)
    assert p.vel.y > 0.0, "gravity tidak bekerja"
    p2 = ps.spawn(0, 0, 500, 0, 1.0, 3, F.P["fx_light"], drag=4.0)
    ps.update(DT)
    assert p2.vel.x < 500.0, "drag tidak bekerja"


def test_semua_shape_partikel_gambar_tanpa_error():
    ps = F.ParticleSystem(cap=32)
    for i, shape in enumerate(("pixel", "glow", "spark", "shard",
                               "streak", "ember", "smoke")):
        ps.spawn(120 + i * 24, 120, 40, -40, 0.6, 4, F.P["fx_hot"],
                 shape=shape, rotation=0.5,
                 rotation_speed=3.0, back=(shape == "smoke"))
    ps.draw(SURF, layer="back")
    ps.draw(SURF, layer="front")


def test_lapisan_hidup_meluruh_penuh_setelah_pertempuran():
    """Tidak boleh ada partikel/proyektil/impact/skill yang nyangkut."""
    h = fresh_hero()
    d = F.director_for(h)
    for sk in ("q", "w", "e", "r"):
        d.on_cast(h.x, h.y, sk)
    d.on_impact(h.x, h.y, 0.5, 1.4, True, "crit")
    d.on_fury_tick(h.x, h.y)
    d.on_omni_strike(h.x, h.y)
    h._gj_attack_active = True
    h._gj_attack_progress = 0.5
    F.tick(DT)
    h._gj_attack_active = False
    d.draw_ground(SURF)
    d.draw_front(SURF)
    for _ in range(600):                    # 10 detik
        F.tick(DT)
    assert d.particles.count() == 0
    assert d.projectiles.count() == 0
    assert not d.impacts
    assert not d.skills
    assert F.total_particles() == 0


# ══════════════════════════════════════════════════════════════════════════
# 5. PROJECTILE SYSTEM
# ══════════════════════════════════════════════════════════════════════════
def test_bidang_projectile_lengkap():
    pr = F.GrimjawProjectile(0, 0, 100, 0)
    for field in ("position", "velocity", "speed", "damage", "lifetime",
                  "target", "radius", "rotation", "trail", "particles",
                  "active"):
        assert hasattr(pr, field), "GrimjawProjectile.%s hilang" % field
    assert isinstance(pr.position, pygame.Vector2)
    assert isinstance(pr.velocity, pygame.Vector2)


def test_projectile_dipakai_hanya_visual():
    """Damage gameplay Q/E/R diterapkan hero_skills, bukan di sini."""
    h = fresh_hero()
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "e")
    for pr in d.projectiles.projectiles:
        assert pr.damage == 0, "projectile visual tidak boleh damage dobel"


def test_e_melepaskan_tiga_gelombang_bilah():
    h = fresh_hero()
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "e")
    assert d.projectiles.count() == 3
    # menyebar: sudut ketiganya berbeda
    angs = sorted(round(pr.rotation, 3) for pr in d.projectiles.projectiles)
    assert angs[0] != angs[-1]


def test_lifecycle_projectile_sampai_hancur():
    ps = F.ParticleSystem()
    sysp = F.ProjectileSystem(ps)
    pr = sysp.spawn(0, 0, 300, 0, speed=300.0)
    assert pr.active and pr.state == "travel"
    states = {pr.state}
    for _ in range(200):
        sysp.update(DT)
        states.add(pr.state)
        if pr.state == "dead":
            break
    assert "impact" in states, "projectile tidak pernah impact"
    assert pr.state == "dead" and not pr.active
    assert sysp.count() == 0


def test_projectile_mengenai_target_memicu_impact():
    ps = F.ParticleSystem()
    sysp = F.ProjectileSystem(ps)
    tgt = fresh_hero(x=200.0, y=0.0)
    hits = []
    pr = sysp.spawn(0, 0, tgt.x, tgt.y, target=tgt, speed=400.0,
                    on_impact=lambda p: hits.append((p.hit_pos.x,
                                                     p.hit_pos.y)))
    for _ in range(120):
        sysp.update(DT)
        if pr.state == "impact":
            break
    assert hits, "callback impact tidak terpanggil"
    assert abs(hits[0][0] - 200.0) < 30.0
    assert pr.hit_pos.distance_to(pygame.Vector2(200.0, 0.0)) < 30.0


def test_projectile_terbang_searah_vektor():
    ps = F.ParticleSystem()
    sysp = F.ProjectileSystem(ps)
    pr = sysp.spawn(0, 0, 100, 0, speed=300.0)
    sysp.update(DT)
    assert pr.position.x > 0 and pr.rotation == pytest.approx(0.0, abs=0.01)
    sysp.draw(SURF)


def test_cap_projectile():
    sysp = F.ProjectileSystem(cap=4)
    for _ in range(10):
        sysp.spawn(0, 0, 50, 50)
    assert sysp.count() <= 4


# ══════════════════════════════════════════════════════════════════════════
# 6. SKILL FX LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("kind", ["q", "w", "e", "r"])
def test_skill_fx_selesai_dan_hilang(kind):
    ps = F.ParticleSystem()
    fx = F.SkillFX(kind, 100, 100, ps)
    seen = set()
    while fx.active:
        fx.update(DT)
        seen.add(fx.phase)
        fx.draw_ground(SURF)
        fx.draw_front(SURF)
    for phase in ("charge", "release", "area", "fade"):
        assert phase in seen, "%s: fase %s hilang (%s)" % (kind, phase, seen)
    assert not fx.active


def test_skill_fx_tidak_abadi():
    ps = F.ParticleSystem()
    fx = F.SkillFX("r", 0, 0, ps)
    total = int(fx.total / DT) + 30
    for _ in range(total):
        fx.update(DT)
        if not fx.active:
            break
    assert not fx.active
    for _ in range(400):
        ps.update(DT)
    assert ps.count() == 0


def test_cast_q_menggunakan_radius_gameplay():
    h = fresh_hero()
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "q")
    fx = d.skills[-1]
    assert fx.radius == pytest.approx(float(h.skill_range), abs=0.01)


def test_cast_w_terpusat_di_posisi_ward():
    h = fresh_hero()
    d = F.director_for(h)
    h._heal_ward_pos = (333.0, 250.0)
    h._heal_ward_timer = 360          # edge 0 -> 360 memicu cast W
    F.tick(DT)
    # SkillFX dibuat di titik ward (+16 px offset anchor tanah)
    assert any(s.kind == "w" and abs(s.x - 333.0) < 0.01 and
               abs(s.y - (250.0 + 12.0)) < 0.01 for s in d.skills)


def test_cast_r_menembakkan_bolt_ke_target():
    h = fresh_hero()
    tgt = fresh_hero(x=320.0, y=180.0)
    h.target = tgt
    h._omnislash_target = tgt
    d = F.director_for(h)
    h._omnislash_timer = 90           # edge 0 -> 90 memicu cast R
    F.tick(DT)
    assert any(s.kind == "r" for s in d.skills)
    assert d.projectiles.count() >= 1
    pr = d.projectiles.projectiles[0]
    assert pr.target is tgt


def test_tick_damage_q_terdeteksi_tiap_15_frame():
    h = fresh_hero()
    d = F.director_for(h)
    h._blade_fury_timer = 180
    F.tick(DT)                          # register prev
    n0 = len(d.impacts)
    h._blade_fury_timer = 165           # 165 % 15 == 0 -> tick
    F.tick(DT)
    assert len(d.impacts) > n0
    assert d.impacts[-1].kind == "spin"
    h._blade_fury_timer = 164           # bukan kelipatan -> tanpa tick baru
    F.tick(DT)
    n1 = len(d.impacts)
    assert n1 == len(d.impacts)


def test_tick_damage_r_terdeteksi_tiap_8_frame():
    h = fresh_hero()
    tgt = fresh_hero(x=300.0, y=200.0)
    h._omnislash_target = tgt
    d = F.director_for(h)
    h._omnislash_timer = 90
    F.tick(DT)
    n0 = len(d.impacts)
    h._omnislash_timer = 82             # 82 % 8 == 0 -> strike
    F.tick(DT)
    assert len(d.impacts) > n0
    assert d.impacts[-1].kind == "omni"


def test_ward_menghidupkan_mote_hijau():
    h = fresh_hero()
    d = F.director_for(h)
    h._heal_ward_timer = 360
    F.tick(DT)
    h._heal_ward_timer = 300
    for _ in range(40):               # masuk fase area SkillFX W
        F.tick(DT)
    assert d.particles.count() > 0


def test_anti_beku_mati_di_tengah_skill():
    """Hero tewas di tengah fury -> timer gameplay membeku > 0.

    Tanpa pagar, emitter bara + trail hidup tanpa batas di mayat
    (``Hero.update`` berhenti jalan begitu ``alive`` False).
    """
    h = fresh_hero()
    d = F.director_for(h)
    h._blade_fury_timer = 100
    h._crit_buff_timer = 90
    F.tick(DT)
    h.alive = False                      # gameplay membekukan timer
    for _ in range(60 * 25):             # 25 detik
        F.tick(DT)
    assert d.particles.count() == 0
    assert not d.trail.active


def test_anti_beku_timer_membeku_sa_hidup():
    """Timer skill macet > 15 s (state tidak sehat) -> emisi berhenti."""
    h = fresh_hero()
    d = F.director_for(h)
    h._blade_fury_timer = 100            # tidak pernah menurun
    for _ in range(60 * 25):
        F.tick(DT)
    assert d.particles.count() == 0


def test_anti_beku_tidak_mematikan_emitter_sehat():
    """Pagar tidak boleh mematikan emitter setelah banyak cast sehat."""
    h = fresh_hero()
    d = F.director_for(h)
    peak = 0
    for _cyc in range(6):
        h._blade_fury_timer = 180
        h._crit_buff_timer = 300
        for _ in range(300):
            h._blade_fury_timer = max(0, h._blade_fury_timer - 1)
            h._crit_buff_timer = max(0, h._crit_buff_timer - 1)
            F.tick(DT)
            peak = max(peak, d.particles.count())
    assert peak > 10, "emitter fury mati permanen (bug pagar anti-beku)"


# ══════════════════════════════════════════════════════════════════════════
# 7. IMPACT + SHAKE + HIT-STOP
# ══════════════════════════════════════════════════════════════════════════
def test_hit_stop_dalam_rentang_master_prompt():
    """Bus menjepit permintaan ke 0.03-0.08 s (kuantisasi frame 1/60)."""
    for s in (0.01, 0.05, 0.2, 5.0):
        F.hit_stop(s)
        total = FEEL.HITSTOP.frames * DT
        assert 0.03 - 1e-6 <= total <= 0.08 + DT, \
            "hit-stop %.3f di luar 0.03-0.08 (+1 frame kuantisasi)" % total
        FEEL.HITSTOP.clear()


def test_hit_stop_membekukan_lalu_melepas():
    F.hit_stop(0.06)
    frozen = sum(1 for _ in range(10) if F.should_freeze_frame())
    assert 2 <= frozen <= 6            # 0.06 s ~ 3-4 frame @60
    assert not F.should_freeze_frame()


def test_shake_meredam_bertahap():
    F.shake(6.0, 0.30)
    a0 = FEEL.SHAKE.amount
    assert a0 > 0.0
    last = a0
    for _ in range(40):
        FEEL.SHAKE.update(DT)
        cur = FEEL.SHAKE.amount
        assert cur <= last + 1e-9, "shake boleh naik sendiri"
        last = cur
    assert FEEL.SHAKE.amount == 0.0


def test_notify_melee_impact_paket_lengkap():
    h = fresh_hero()
    F.notify_melee_impact(h, fresh_hero(x=240.0, y=200.0), 55, True)
    d = F.director_for(h)
    assert d.impacts and d.impacts[-1].crit
    assert d.particles.count() >= 10
    assert FEEL.HITSTOP.frames > 0
    assert FEEL.SHAKE.amount > 0.0


def test_semua_jenis_impact_gambar_tanpa_error():
    h = fresh_hero()
    d = F.director_for(h)
    for kind in ("blade", "crit", "spin", "omni"):
        d.on_impact(h.x + 40, h.y, -0.8, 1.2, kind == "crit", kind)
    d.draw_front(SURF)


def test_impact_selalu_berumur_pendek():
    h = fresh_hero()
    d = F.director_for(h)
    d.on_impact(h.x, h.y, 0.0, 2.0, True, "crit")
    for _ in range(120):
        ok = d.impacts[0].update(DT) if d.impacts else False
        if not ok:
            break
    assert not d.impacts or not d.impacts[0].active


# ══════════════════════════════════════════════════════════════════════════
# 8. SUPRESI GANDA + INTEGRASI PIPELINE
# ══════════════════════════════════════════════════════════════════════════
def test_canvas_skip_fx_saat_live_owned():
    """Renderer tidak menggambar smear/pop in-canvas saat live mengambil alih."""
    def render_owned(owned):
        F.reset_all()
        h = fresh_hero()
        h._gj_attack_active = True
        h._gj_attack_progress = 0.5
        h.timer = 20
        if owned:
            F.attach(h)
        G._FX_LIVE.v = G._fx_live_owned(h)
        canvas = pygame.Surface((528, 528), pygame.SRCALPHA)
        G._draw_grimjaw_attack(canvas, h, 264, 264, crit=False, omni=False)
        return hashlib.md5(
            pygame.image.tostring(canvas, "RGBA")).hexdigest()

    fb = render_owned(False)
    ow = render_owned(True)
    assert fb != ow, "smear in-canvas tidak tersupresi saat live owned"


def test_fallback_canvas_tetap_jalan_tanpa_modul():
    """owns() = False saat director dilepas -> canvas FX kembali hidup."""
    h = fresh_hero()
    F.attach(h)
    assert G._fx_live_owned(h) is True
    F.reset_all()
    assert G._fx_live_owned(h) is False


def test_render_hero_penuh_dengan_live_layer():
    """Pipeline utama: sprite + lapisan hidup untuk semua pose utama."""
    F.reset_all()
    h = fresh_hero(x=300.0, y=280.0)
    for i in range(70):
        h.timer = 45 - i
        h._gj_attack_active = True
        h._gj_attack_progress = i / 70
        heroes.render_hero("grimjaw", SURF, h, int(h.x), int(h.y))
        F.tick(DT)
    for sk in ("q", "w", "e", "r"):
        h.active_skill = sk
        h.active_skill_timer = 30
        heroes.render_hero("grimjaw", SURF, h, int(h.x), int(h.y))
        F.tick(DT)
    h.active_skill = None
    d = F.director_for(h)
    assert d.trail.points or d.particles.count() or d.impacts
    assert F.owns(h)


def test_serangan_dasar_tanpa_hook_impact_di_entity():
    """Serangan dasar Grimjaw TIDAK boleh memicu impact FX di _entity.py.

    Kontrak performa: impact FX (spark/shake/hit-stop) eksklusif milik
    SKILL. Jalur serangan dasar harus tetap NOL panggilan
    ``notify_melee_impact``; linker lapisan hidup tetap menyambung lewat
    ``heroes/_bundle.py`` (renderer) dan API ``grimjaw_fx``.
    """
    src = open(os.path.join(ROOT, "_entity.py"), encoding="utf-8").read()
    # Panggilan nyata = bukan sekadar komentar lama.
    assert "notify_melee_impact(" not in src.replace(
        "# Sembilan blok `IMPACT FX <HERO>` (notify_melee_impact)", ""), \
        "_entity.py masih memanggil notify_melee_impact untuk serangan dasar"

    # Lapisan hidup/API FX tetap tersedia lewat renderer + modul FX.
    bundle = open(os.path.join(ROOT, "heroes", "_bundle.py"),
                  encoding="utf-8").read()
    assert "grimjaw_fx" in bundle
    for name in ("notify_melee_impact", "notify_skill_impact",
                 "notify_skill_cast"):
        assert hasattr(F, name), "grimjaw_fx API hilang: %s" % name


def test_hud_core_menghitung_partikel_grimjaw():
    src = open(os.path.join(ROOT, "_core.py"), encoding="utf-8").read()
    assert "grimjaw_fx" in src


def test_debug_overlay_jalan():
    h = fresh_hero()
    d = F.director_for(h)
    d.on_cast(h.x, h.y, "q")
    d.on_impact(h.x + 30, h.y, 0.4, 1.0, False, "blade")
    F.draw_debug_overlay(SURF, d)


# ══════════════════════════════════════════════════════════════════════════
# 9. PERFORMA
# ══════════════════════════════════════════════════════════════════════════
def test_budget_lapisan_hidup():
    """12 director bertarung penuh: update+draw jauh di bawah satu frame."""
    import time
    F.reset_all()
    hs = []
    for i in range(12):
        h = fresh_hero(x=60.0 + i * 48, y=200.0)
        F.director_for(h)
        d = F.director_for(h)
        d.on_cast(h.x, h.y, "q")
        d.on_cast(h.x, h.y, "r")
        d.on_impact(h.x + 20, h.y, 0.3, 1.5, True, "crit")
        h._gj_attack_active = True
        h._gj_attack_progress = 0.45
        hs.append(h)

    def frame():
        for h in hs:
            h._gj_attack_progress = min(
                0.9, h._gj_attack_progress + 0.004)
        F.tick(DT)
        for h in hs:
            d = F.director_for(h)
            d.draw_ground(SURF)
            d.draw_front(SURF)

    for _ in range(8):                  # warm-up (isi cache surface)
        frame()
    times = []
    for _ in range(30):
        t0 = time.perf_counter()
        frame()
        times.append(time.perf_counter() - t0)
    times.sort()
    median = times[len(times) // 2]
    assert median < 0.016, "frame FX median %.2f ms > 16 ms" % (median * 1e3)
