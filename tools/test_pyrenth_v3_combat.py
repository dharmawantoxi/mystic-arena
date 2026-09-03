#!/usr/bin/env python3
"""Regression test PYRENTH V3 (renderer + live combat-FX engine).

Mengunci kontrak yang dibangun di dokumen docs/PYRENTH_V3_COMBAT_FX.md:

  * lapisan hidup heroes/pyrenth_fx.py punya semua API yang dipakai
    pipeline hero/boss (attach/owns/tick/draw_*_layer/notify_*);
  * palette karakter dipakai konsisten renderer <-> lapisan FX;
  * animation controller (_NS_pyrenth): state (12), prioritas, fase
    serangan, hit window, delta time;
  * busur: BLADE_ARC kontinu tanpa teleport, dan renderer <-> FX
    membaca SATU sumber geometri yang sama (blade_geometry);
  * dash (skill E): offset visual 80 px dari SATU fungsi
    (_NS_pyrenth._lunge_offset, dikonversi ke basis waktu FX);
  * proyektil modular (chaos bolt + chaos brand): spawn -> travel ->
    trail -> hit -> impact FX -> destroy, dengan kontrak atribut penuh;
  * skill FX q/w/e/r lifecycle 6 tahap dan selesai dalam waktu terbatas;
  * renderer bosses/level4.draw_pyrenth hidup bersama lapisan FX tanpa
    exception (boss lane + hero lane), semua pose;
  * telegraph AoE W/R = LINGKARAN di radius dunia 220 (sama persis
    dengan radius damage AI di base_boss.py);
  * boss AI (base_boss.py) memanggil lapisan FX pyrenth;
  * game feel: hit-stop 0.03-0.08 s + screen shake meluruh;
  * prosedural murni (tanpa pygame.image.load / aset gambar);
  * tidak ada partikel/proyektil/skill/afterimage yang hidup tanpa batas;
  * boss lain di bundle level4 tidak ikut rusak.

Jalankan:
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
      python3 tools/test_pyrenth_v3_combat.py

(Lingkungan sandbox tanpa pygame terpasang:
  python3 -m pip install --break-system-packages pygame)
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

from heroes import pyrenth_fx as F
from heroes import combat_feel as CF
import bosses.level4 as L

NS = L._NS_pyrenth


def make_boss(x=100.0, y=100.0, skill=None, timer=0, target=True,
              target_dist=200.0):
    b = SimpleNamespace(
        boss_type="pyrenth", boss_class="mini", team="red",
        x=float(x), y=float(y), direction=1, facing=1, pulse=1.2,
        timer=0, attack_cooldown=44, attack_range=55, range=55,
        active_skill=skill, active_skill_timer=timer,
        target=(SimpleNamespace(x=x + float(target_dist), y=float(y),
                                alive=True, radius=12) if target else None),
        hurt_flash_timer=0, alive=True, radius=34,
        hp=5000, max_hp=5000, damage=100, speed=1.0)
    return b


def warm(surface, boss, x=350, y=350, frames=4):
    for _ in range(frames):
        L.draw_pyrenth(surface, boss, x, y)
        F.tick(1.0 / 60.0)
        time.sleep(0.001)


# ── 1. API + PALETTE ────────────────────────────────────────────────
def test_module_api():
    required = [
        "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
        "Afterimage", "BaseProjectile", "DoomBoltProjectile",
        "SoulEmberProjectile", "ProjectileSystem", "SkillFX",
        "PyrenthFXDirector",
        "attach", "owns", "recently_drawn", "tick", "reset_all",
        "total_particles", "stats", "draw_ground_layer", "draw_live_layer",
        "director_for", "projectiles_for", "notify_melee_impact",
        "notify_projectile_impact", "notify_projectile_cast",
        "notify_skill_impact", "notify_skill_cast", "notify_hurt",
        "notify_death", "draw_debug_overlay", "clear_cache", "cache_size",
        "PYRENTH_PALETTE", "DEBUG_CHARACTER", "PYRENTH_FX_ENABLED",
        "blade_arc", "attack_phase", "skill_phase",
        "blade_points", "blade_tip", "blade_angle", "launch_point",
        "lunge_offset", "pose_of", "render_scale", "body_scale",
        "target_point", "ring_radius", "particle_budget", "glow_allowed",
        "glow_surface", "ring_surface", "blit_add", "spark_star",
        "chevron", "taper_lane",
        "WORLD_RADIUS", "SKILL_DUR", "SKILL_TOTAL", "SKILL_PHASES",
        "ATTACK_PHASES", "ATTACK_ACTIVE_WINDOW", "ATTACK_IMPACT_FRAME",
        "BLADE_ARC",
        "MAX_PARTICLES", "MAX_PROJECTILES", "MAX_SKILLS", "MAX_IMPACTS",
        "MAX_AFTERIMAGES", "MAX_DIRECTORS", "TRAIL_SAMPLES", "_CACHE_CAP",
    ]
    for name in required:
        assert hasattr(F, name), "API hilang: pyrenth_fx.%s" % name
    for name in F.__all__:
        assert hasattr(F, name), "__all__ menyebut %s yang tidak ada" % name

    # renderer v2/v3: API lama tetap utuh (backward compatible)
    for name in ("PALETTE", "SKILL_DUR", "SKILL_RADIUS", "DoomChain",
                 "InfernalArc", "draw_pyrenth", "draw_boss",
                 "_update_attack_anim", "_manage_projectiles",
                 "_spawn_doom_chain", "_spawn_infernal_arc", "_target_position",
                 "_fx_scale" if hasattr(NS, "_fx_scale") else "GROUND_DY",
                 "_live_module", "live_fx_ready", "_draw_sword_swing_arc",
                 "_draw_swing_impact", "_draw_sword_swing_arc",
                 # v3
                 "DEBUG_CHARACTER", "ANIM_STATES", "ATTACK_PHASES",
                 "ATTACK_ACTIVE_WINDOW", "ATTACK_IMPACT_FRAME",
                 "MELEE_REACH", "_BLADE_HALF", "BLADE_ARC",
                 "attack_phase", "attack_phases_order",
                 "_blade_lift", "_blade_arc", "blade_geometry",
                 "_lunge_offset", "_update_pyr_anim", "_resolve_pose_pyr",
                 "_draw_pyr_body", "_draw_pyr_body_raw",
                 "_draw_pyrenth_debug", "_last_rig", "draw_boss"):
        assert hasattr(NS, name), "API renderer hilang: _NS_pyrenth.%s" % name
    assert callable(L.draw_pyrenth)
    assert callable(NS.draw_boss)


def test_palette_contract():
    """Palet karakter dipakai KONSISTEN di renderer dan lapisan FX."""
    bands = (
        # kulit demon
        "skin_darkest", "skin_dark", "skin_mid", "skin_light",
        "skin_high", "skin_shine",
        # lengan cakar
        "arm_darkest", "arm_dark", "arm_mid", "arm_light", "arm_shine",
        # batu lebur (identitas Pyrenth, menggantikan chaos_* Vokrahn)
        "molten_darkest", "molten_dark", "molten_mid", "molten_bright",
        "molten_hot", "molten_glow",
        # api pedang
        "fire_darkest", "fire_dark", "fire_mid", "fire_bright",
        "fire_hot", "fire_glow", "fire_white",
        # jiwa (Devour) — menggantikan smoke_* Vokrahn
        "soul_dark", "soul_mid", "soul_light", "soul_glow",
        # kain, sayap, tanduk
        "cape_darkest", "cape_dark", "cape_mid",
        "horse_darkest", "horse_dark", "horse_mid", "horse_light",
        "mane_darkest", "mane_dark", "mane_mid", "mane_bright",
        "mane_hot",
        # logam & emas
        "metal_darkest", "metal_dark", "metal_mid", "metal_edge",
        "metal_light", "metal_shine",
        "gold_dark", "gold_mid", "gold_light",
        "eye_dark", "eye_bright", "eye_hot",
        "outline", "shadow", "shadow_deep", "dark", "body", "mid",
        "light", "highlight", "weapon", "fx",
    )
    for k in bands:
        assert k in F.PYRENTH_PALETTE, "palet FX kurang kunci %s" % k
    for k, v in F.PYRENTH_PALETTE.items():
        assert len(v) == 3 and all(0 <= c <= 255 for c in v), k
    # sinkronisasi: kunci yang dipetakan HARUS ada di palet renderer
    for fx_key, rend_key in F._PALETTE_SYNC.items():
        assert fx_key in F.PYRENTH_PALETTE, fx_key
        assert rend_key in NS.PALETTE, \
            "palet renderer kurang kunci %s (dipetakan dari %s)" % (
                rend_key, fx_key)
    # setelah sinkron, warna kerja FX == warna renderer
    F._sync_palette()
    for fx_key, rend_key in F._PALETTE_SYNC.items():
        assert tuple(F.P[fx_key]) == tuple(NS.PALETTE[rend_key]), fx_key


# ── 2. ANIMATION CONTROLLER ─────────────────────────────────────────
def test_anim_controller():
    boss = make_boss()
    NS._update_pyr_anim(boss, moving=False)
    assert boss._pyr_state == "IDLE", boss._pyr_state

    boss._pyr_speed = 0.5
    NS._update_pyr_anim(boss, moving=True)
    assert boss._pyr_state == "WALK", boss._pyr_state
    boss._pyr_speed = 2.4
    NS._update_pyr_anim(boss, moving=True)
    assert boss._pyr_state == "RUN", boss._pyr_state
    boss._pyr_speed = 0.0

    boss.active_skill = "q"
    boss.active_skill_timer = 25
    NS._update_pyr_anim(boss, moving=False)
    assert boss._pyr_state == "SKILL", boss._pyr_state
    boss.active_skill = "r"
    NS._update_pyr_anim(boss, moving=False)
    assert boss._pyr_state == "SPECIAL", boss._pyr_state
    boss.active_skill = None
    boss.active_skill_timer = 0

    boss.hurt_flash_timer = 6
    NS._update_pyr_anim(boss, moving=False)
    assert boss._pyr_state == "HURT", boss._pyr_state
    boss.hurt_flash_timer = 0

    boss.alive = False
    NS._update_pyr_anim(boss, moving=False)
    assert boss._pyr_state == "DEATH", boss._pyr_state
    boss.alive = True

    # 12 state master semuanya ada; prioritas benar
    pr = NS.ANIM_STATES
    for name in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                 "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert name in pr, "state wajib hilang: %s" % name
    assert pr["DEATH"] > pr["HURT"] > pr["HIT"] > pr["SPECIAL"] \
        > pr["SKILL"] > pr["SWING"] > pr["ATTACK"] \
        > pr["CAST"] >= pr["CHARGE"] > pr["WALK"] > pr["IDLE"]

    # timeline serangan: timer engine di-reset (melonjak naik) = mulai
    boss = make_boss()
    boss.timer = 44
    NS._update_pyr_anim(boss, moving=False)
    assert boss._pyr_attack_active, "serangan tidak terdeteksi"
    phases = []
    for _ in range(46):
        NS._update_pyr_anim(boss, moving=False)
        phases.append(boss._pyr_attack_phase)
        assert 0.0 < boss._pyr_dt <= 0.05
    order = [p for i, p in enumerate(phases)
             if i == 0 or p != phases[i - 1]]
    order = [p for p in order if p != "NONE"]
    assert order == list(NS.attack_phases_order()), order

    # fase & hit window konsisten dengan tabel
    names = set(n for n, _a, _b in NS.ATTACK_PHASES)
    for p in (0.0, 0.1, 0.2, 0.4, 0.52, 0.7, 0.9, 1.0):
        assert NS.attack_phase(p) in names
    lo, hi = NS.ATTACK_ACTIVE_WINDOW
    assert 0.0 < lo < NS.ATTACK_IMPACT_FRAME < hi < 1.0
    assert NS.attack_phase(NS.ATTACK_IMPACT_FRAME) == "IMPACT"
    assert NS.attack_phase(0.95) == "RECOVERY"
    # lapisan hidup membaca tabel fase yang SAMA
    assert F.ATTACK_PHASES == NS.ATTACK_PHASES
    assert F.ATTACK_ACTIVE_WINDOW == NS.ATTACK_ACTIVE_WINDOW
    assert F.ATTACK_IMPACT_FRAME == NS.ATTACK_IMPACT_FRAME
    for p in (0.05, 0.2, 0.4, 0.52, 0.7, 0.9):
        assert F.attack_phase(p) == NS.attack_phase(p)


def test_always_melee():
    """Pyrenth SELALU melee (greatsword) — ayunan, bukan bidikan."""
    boss = make_boss()
    boss.timer = 44
    NS._update_pyr_anim(boss)
    seen = set()
    for _ in range(40):
        NS._update_pyr_anim(boss)
        seen.add(boss._pyr_state)
    assert "SWING" in seen, "ayunan besar tidak pernah terjadi (%s)" % seen
    assert "CAST" not in seen, \
        "pyrenth tidak menembak: state CAST muncul (%s)" % seen


# ── 3. SWORD ARC / GEOMETRI SENJATA ─────────────────────────────────
def test_blade_arc_continuity():
    prev = None
    max_step = 0.0
    for i in range(201):
        phi, lift = NS._blade_arc(i / 200.0)
        assert -3.6 <= phi <= 3.6, phi
        assert -0.2 <= lift <= 1.0, lift
        if prev is not None:
            max_step = max(max_step, abs(phi - prev))
        prev = phi
    # langkah maksimum ~0.31 rad per 1/200 progres (ayunan overhead) —
    # kecil sekali; bilah mustahil teleport
    assert max_step < 0.35, "senjata teleport: langkah %.3f rad" % max_step
    # mulai & selesai di titik istirahat yang sama (loop mulus)
    assert abs(NS._blade_arc(0.0)[0] - NS._blade_arc(1.0)[0]) < 1e-6
    # lapisan hidup membaca SUMBER YANG SAMA
    for p in (0.0, 0.12, 0.31, 0.52, 0.7, 0.93, 1.0):
        a = NS._blade_arc(p)
        b = F.blade_arc(p)
        assert abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9
    # tabel fallback identik (kalau renderer tak bisa diimpor)
    assert F.BLADE_ARC == NS.BLADE_ARC, \
        "tabel BLADE_ARC FX menyimpang dari renderer"


def test_blade_geometry_single_source():
    # panjang bilah konstan di semua pose (tidak melar/menyusut)
    L_half = NS._BLADE_HALF
    for action in ("idle", "walk", "swing", "attack", "cast", "skill",
                   "hurt", "death", "q_cast", "w_cast", "e_cast", "r_cast"):
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            grip, tip, lo, phi = NS.blade_geometry(1, action, 0.0, p)
            length = math.hypot(tip[0] - grip[0], tip[1] - grip[1])
            assert abs(length - L_half) < 1e-6, (action, p, length)
            length2 = math.hypot(lo[0] - grip[0], lo[1] - grip[1])
            assert abs(length2 - L_half * 0.55) < 1e-6, (action, p)
            assert isinstance(phi, float)
    # mirror facing
    g1, t1, _l1, _t = NS.blade_geometry(1, "swing", 0.0, 0.4)
    g2, t2, _l2, _t2 = NS.blade_geometry(-1, "swing", 0.0, 0.4)
    assert abs(g1[0] + g2[0]) < 1e-6 and abs(t1[0] + t2[0]) < 1e-6
    assert abs(g1[1] - g2[1]) < 1e-6 and abs(t1[1] - t2[1]) < 1e-6

    # lapisan hidup memakai geometri yang sama (skala layar 1:1).
    # NOTE: set pose SETELAH draw (draw mem-rewrite _pyr_pose_action).
    boss = make_boss()
    surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    L.draw_pyrenth(surf, boss, 200.0, 200.0)
    boss._pyr_pose_action = "swing"
    boss._pyr_attack_progress = 0.4
    boss._pyr_phase = 0.0
    grip, tip, lo = F.blade_points(boss, 200.0, 200.0)
    g, t, l4, _t = NS.blade_geometry(1, "swing", 0.0, 0.4)
    assert abs(grip[0] - (200.0 + g[0])) < 1e-6
    assert abs(grip[1] - (200.0 + g[1])) < 1e-6
    assert abs(tip[0] - (200.0 + t[0])) < 1e-6
    assert abs(tip[1] - (200.0 + t[1])) < 1e-6
    assert abs(lo[0] - (200.0 + l4[0])) < 1e-6
    # sudut pedang konsisten dengan titik-titiknya
    ang = F.blade_angle(boss, 200.0, 200.0)
    assert abs(ang - math.atan2(tip[1] - lo[1], tip[0] - lo[0])) < 1e-9
    F.reset_all()


def test_lunge_offset_bridge():
    """FX harus membaca offset dash renderer dengan konversi basis
    waktu yang benar: t(FX 0..1 atas umur penuh) -> engine 0..1,
    di mana engine selesai di t = ENGINE_SPAN (sisanya = ekor AFTER)."""
    span = F.SkillFX.ENGINE_SPAN
    assert 0.5 < span < 1.0, span
    for p in (0.0, 0.15, 0.302, 0.4, 0.55, 0.605, 0.7, 0.85, 1.0):
        fx = F.lunge_offset(None, p * span)
        rn = NS._lunge_offset(p)
        assert abs(fx - rn) < 1e-9, (p, fx, rn)
    # puncak 46 px di tengah lunge, 0 saat engine selesai
    peak = max(F.lunge_offset(None, i / 200.0 * span) for i in range(201))
    assert abs(peak - 46.0) < 1e-6, peak
    assert abs(NS._lunge_offset(1.0)) < 1e-9
    # setelah engine selesai, FX tetap diam di posisi awal (tidak
    # "kembali" di ekor AFTER: badan sudah di posisi logisnya)
    assert F.lunge_offset(None, 1.0) == 0.0


# ── 4. SWING TRAIL ──────────────────────────────────────────────────
def test_swing_trail_records_history():
    F.reset_all()
    boss = make_boss(target_dist=40.0)
    F.attach(boss)
    d = F.director_for(boss)
    boss._pyr_pose_action = "swing"
    boss._pyr_attack_progress = 0.0
    for i in range(1, 30):
        boss._pyr_attack_progress = i / 30.0
        d.sync(boss, 200.0, 200.0)
        d.update(1.0 / 60.0)
    assert len(d.trail.history) > 2, "trail tidak merekam posisi senjata"
    assert len(d.trail.history) <= F.TRAIL_SAMPLES, "trail tak terbatas"
    # digambar ADDITIF, jadi diuji di surface opaque (seperti layar asli)
    surf = pygame.Surface((640, 480))
    surf.fill((0, 0, 0))
    d.trail.draw(surf)
    assert surf.get_bounding_rect().width > 0, "trail tidak terlihat"
    # trail meluruh sendiri (bukan efek abadi)
    for _ in range(180):
        d.update(1.0 / 60.0)
    assert len(d.trail.history) == 0, "trail abadi"
    F.reset_all()


# ── 5. PARTICLE SYSTEM ──────────────────────────────────────────────
def test_particle_contract():
    ps = F.ParticleSystem(32)
    p = ps.spawn(10.0, 20.0, vx=30.0, vy=-40.0, ay=90.0, life=0.5,
                 size=3.0, color=F.P["ember"])
    for attr in ("position", "velocity", "acceleration", "life", "max_life",
                 "size", "rotation", "rotation_speed", "alpha", "gravity",
                 "color"):
        assert hasattr(p, attr), "atribut partikel hilang: %s" % attr
    assert isinstance(p.position, pygame.Vector2)
    assert isinstance(p.velocity, pygame.Vector2)
    assert isinstance(p.acceleration, pygame.Vector2)
    y0 = p.position.y
    ps.update(1.0 / 60.0)
    assert p.position.y != y0, "partikel tidak bergerak"
    # fade: alpha turun seiring umur
    a0 = p.draw_alpha()
    for _ in range(20):
        ps.update(1.0 / 60.0)
    assert p.draw_alpha() < a0 or not p.active, "partikel tidak memudar"
    # gravity benar-benar dipakai
    g = F.ParticleSystem(8)
    q = g.spawn(0.0, 0.0, vx=0.0, vy=0.0, life=2.0, gravity=200.0)
    g.update(0.5)
    assert q.velocity.y > 0.0, "gravity tidak diterapkan"
    # burst + spread + directional
    ps.burst(0.0, 0.0, 12, direction=0.0, spread=0.8,
             speed=(50.0, 120.0), life=(0.3, 0.6), size=(2.0, 4.0),
             colors=(F.P["fire_hot"], F.P["ember"]), gravity=180.0)
    assert ps.count() <= 32, "cap partikel dilanggar"
    for _ in range(400):
        ps.update(1.0 / 60.0)
    assert ps.count() == 0, "partikel tidak pernah habis"


def test_particle_cap_is_hard():
    ps = F.ParticleSystem(24)
    for _ in range(500):
        ps.spawn(0.0, 0.0, life=99.0)
        assert ps.count() <= 24


# ── 6. PROJECTILES ──────────────────────────────────────────────────
def test_doom_lifecycle():
    F.reset_all()
    boss = make_boss()
    assert F.attach(boss) and F.owns(boss)
    F.notify_projectile_cast(boss, boss.x, boss.y)
    projs = F.projectiles_for(boss)
    assert len(projs) == 1
    bolt = projs[0]
    # kontrak atribut proyektil modular
    for attr in ("position", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(bolt, attr), attr
    assert isinstance(bolt.position, pygame.Vector2)
    assert isinstance(bolt.velocity, pygame.Vector2)
    assert bolt.speed > 0.0 and bolt.lifetime > 0.0
    start = pygame.Vector2(bolt.position)
    for _ in range(300):
        F.tick(1.0 / 60.0)
        if not bolt.active:
            break
    assert not bolt.active, "chaos bolt tidak pernah menghilang"
    assert bolt.hit, "chaos bolt tidak pernah mengenai target"
    assert (start - bolt.position).length() > 20.0, "bolt tidak bergerak"
    assert len(bolt.trail) > 2, "bolt tidak punya trail"
    d = F.director_for(boss)
    assert len(d.projectiles.impacts) > 0, "impact FX tidak muncul"
    assert len(F.projectiles_for(boss)) == 0, "proyektil bocor"
    F.reset_all()


def test_doom_is_not_a_plain_circle():
    """Bolt harus punya bentuk terarah + rotasi, bukan bulatan polos."""
    F.reset_all()
    d = F.PyrenthFXDirector()
    a = d.projectiles.spawn_doom(100.0, 100.0, 400.0, 100.0)
    b = d.projectiles.spawn_doom(100.0, 100.0, 100.0, 400.0)
    for _ in range(10):
        d.projectiles.update(1.0 / 60.0)
    assert abs(a.rotation - b.rotation) > 0.5, \
        "rotasi tidak mengikuti arah terbang"

    def bbox(pr):
        s = pygame.Surface((360, 360), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        pr.trail.clear()                 # ukur badan bolt, bukan jejaknya
        pr.position = pygame.Vector2(180.0, 180.0)
        pr.draw(s)
        return s.get_bounding_rect(min_alpha=40)
    ra, rb = bbox(a), bbox(b)
    assert ra.width > 0 and rb.width > 0, "proyektil tidak tergambar"
    assert (ra.width, ra.height) != (rb.width, rb.height), \
        "siluet proyektil identik di dua arah -> masih lingkaran polos"
    F.reset_all()


def test_soul_ember_projectile():
    F.reset_all()
    d = F.PyrenthFXDirector()
    br = d.projectiles.spawn_ember(100.0, 100.0, 100.0 + 260.0, 100.0)
    assert br.active and br.kind == "ember"
    for _ in range(400):
        d.update(1.0 / 60.0)
        if not br.active:
            break
    assert not br.active, "soul ember tidak pernah selesai"
    assert len(br.trail) > 2, "soul ember tidak punya trail"
    F.reset_all()


def test_projectile_cap():
    F.reset_all()
    d = F.PyrenthFXDirector()
    for _ in range(F.MAX_PROJECTILES + 20):
        d.projectiles.spawn_doom(0.0, 0.0, 400.0, 0.0)
    assert d.projectiles.count() <= F.MAX_PROJECTILES
    F.reset_all()


# ── 7. SKILL FX ─────────────────────────────────────────────────────
def test_skill_lifecycle_and_dedup():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    d.sync(boss, boss.x, boss.y)
    F.notify_skill_cast(boss, "q")
    F.notify_skill_impact(boss, boss.x + 100, boss.y, 60, "q")
    assert len([s for s in d.skills if s.skill == "q"]) == 1, \
        "cast+impact membuat SkillFX dobel"
    fx = d.skills[0]
    seen = set()
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)
    for _ in range(500):
        seen.add(fx.phase)
        F.tick(1.0 / 60.0)
        d.draw_ground(surf)
        d.draw_front(surf)
        if not fx.active:
            break
    assert not fx.active, "skill FX tidak selesai-selesai"
    for want in ("CAST", "CHARGE", "RELEASE", "AREA", "IMPACT", "AFTER"):
        assert want in seen, "fase %s tidak pernah terjadi (%s)" % (want,
                                                                    seen)
    # w / e / r juga hidup penuh lalu mati
    for skill in ("w", "e", "r"):
        F.notify_skill_cast(boss, skill)
        F.notify_skill_impact(boss, boss.x, boss.y, None, skill)
        assert len(d.skills) <= F.MAX_SKILLS
    for _ in range(600):
        F.tick(1.0 / 60.0)
        d.draw_ground(surf)
        d.draw_front(surf)
    assert len(d.skills) == 0, "skill FX abadi"
    F.reset_all()


def test_skill_phase_table():
    for t, want in ((0.00, "CAST"), (0.10, "CAST"), (0.25, "CHARGE"),
                    (0.40, "RELEASE"), (0.60, "AREA"), (0.80, "IMPACT"),
                    (0.95, "AFTER"), (1.00, "AFTER")):
        assert F.skill_phase(t) == want, (t, F.skill_phase(t))


def test_skill_radius_matches_gameplay():
    """Radius & durasi FX = radius & durasi damage AI (base_boss)."""
    assert F.WORLD_RADIUS == {"q": 200.0, "w": 200.0, "e": 180.0,
                              "r": 220.0}
    assert F.SKILL_DUR == {"q": 50, "w": 40, "e": 60, "r": 70}
    assert NS.SKILL_DUR == F.SKILL_DUR
    for k, v in F.WORLD_RADIUS.items():
        assert float(NS.SKILL_RADIUS[k]) == v, k
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    zone = src[src.index("def _cast_pyrenth_q"):
               src.index("def _smart_ai_vokrahn")]
    # durasi cast di AI HARUS sama persis dengan SKILL_DUR renderer/FX
    for key in ("q", "w", "e", "r"):
        assert "self.active_skill_timer = %d" % F.SKILL_DUR[key] in zone, key
    # radius damage AI E=180, R=220 (dipakai telegraph FX)
    assert "<= 180" in zone, "radius damage AI E tidak lagi 180"
    assert "<= 220" in zone, "radius damage AI R tidak lagi 220"


def test_engine_progress_drives_skill_fx():
    """Lifecycle FX dikunci ke timer engine, bukan hanya akumulasi dt.

    Kalau progres FX hanya bergantung dt, satu frame terisolasi jauh di
    tengah skill akan selalu digambar di radius 0.
    """
    F.reset_all()
    boss = make_boss(skill="e", timer=NS.SKILL_DUR["e"])
    d = F.director_for(boss)
    d.sync(boss, 300.0, 300.0)
    fx = d.skills[0]
    assert fx.age < 0.05
    # frame tunggal jauh di tengah skill -> FX harus ikut melompat
    boss.active_skill_timer = 12          # ~80% selesai
    d.sync(boss, 300.0, 300.0)
    assert fx.age > 0.5 * fx.total, "set_engine_progress tidak terpasang"
    assert fx.phase in ("AREA", "IMPACT", "AFTER"), fx.phase
    # tidak pernah mundur
    a = fx.age
    boss.active_skill_timer = 55
    d.sync(boss, 300.0, 300.0)
    assert fx.age >= a, "progres FX mundur"
    F.reset_all()


# ── 8. AOE TELEGRAPH = LINGKARAN DI RADIUS DAMAGE ───────────────────
def _hits_ring(surf, radius, cx, cy, samples=180, tol=7):
    """Berapa banyak arah yang punya piksel terang di jarak `radius`."""
    hit = 0
    w, h = surf.get_size()
    for i in range(samples):
        a = 2.0 * math.pi * i / samples
        for dr in range(-tol, tol + 1):
            x = int(cx + math.cos(a) * (radius + dr))
            y = int(cy + math.sin(a) * (radius + dr))
            if 0 <= x < w and 0 <= y < h:
                r, g, b = surf.get_at((x, y))[:3]
                if r + g + b > 90:
                    hit += 1
                    break
    return hit


def test_aoe_telegraph_is_a_true_circle():
    """E (180) & R (220) HARUS punya cincin lingkaran di radius dunia.

    Ini kontrak gameplay: pemain membaca radius damage dari cincin.
    Elips perspektif hanya boleh jadi dekorasi tambahan, bukan pengganti.
    Jangkar cincin = y + 10 (garis dasar sprite di skala 1).
    """
    F.reset_all()
    for skill in ("e", "r"):
        boss = make_boss(x=0.0, y=0.0, skill=skill,
                         timer=int(NS.SKILL_DUR[skill] * 0.45),
                         target=False)
        surf = pygame.Surface((1100, 1100))
        surf.fill((0, 0, 0))
        cx = cy = 550
        F.draw_ground_layer(surf, boss, cx, cy)
        F.tick(1.0 / 60.0)
        F.draw_ground_layer(surf, boss, cx, cy)
        F.draw_live_layer(surf, boss, cx, cy)
        rad = F.WORLD_RADIUS[skill]
        n = _hits_ring(surf, rad, cx, cy + 10)
        assert n > 110, "%s: cincin AoE %d dunia meleset (%d/180)" % (
            skill.upper(), rad, n)
    F.reset_all()


def test_skill_shapes_are_not_all_circles():
    """Q = koridor bidik memanjang, bukan sekadar lingkaran."""
    F.reset_all()
    boss = make_boss(x=0.0, y=0.0, skill="q", timer=25)
    surf = pygame.Surface((900, 900), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    F.draw_ground_layer(surf, boss, 450, 450)
    F.tick(1.0 / 60.0)
    F.draw_ground_layer(surf, boss, 450, 450)
    br = surf.get_bounding_rect(min_alpha=24)
    assert br.width > br.height * 1.25, \
        "koridor bidik Q tidak memanjang ke arah target (%s)" % (br,)
    F.reset_all()


# ── 9. RENDERER + LIVE LAYER ────────────────────────────────────────
def test_renderer_with_live_fx():
    F.reset_all()
    boss = make_boss(skill="r", timer=40)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    warm(surf, boss, frames=30)
    br = surf.get_bounding_rect(min_alpha=64)
    assert br.width > 40 and br.height > 40, (br.width, br.height)
    assert F.owns(boss), "lapisan hidup tidak mengambil alih di boss lane"
    assert getattr(boss, "_pyr_suppress_canvas_fx", False), \
        "fallback canvas tidak dimatikan padahal lapisan hidup aktif"
    F.reset_all()


def test_renderer_all_states():
    surf = pygame.Surface((760, 760), pygame.SRCALPHA)
    cases = [("idle", make_boss())]
    walk = make_boss()
    walk._pyr_speed = 0.6
    cases.append(("walk", walk))
    run = make_boss()
    run._pyr_speed = 2.5
    cases.append(("run", run))
    hurt = make_boss()
    hurt.hurt_flash_timer = 6
    cases.append(("hurt", hurt))
    atk = make_boss()
    atk._pyr_attack_active = True
    atk._pyr_attack_frame = 14
    atk._pyr_prev_timer = 44
    atk.timer = 43
    cases.append(("attack", atk))
    for skill in ("q", "w", "e", "r"):
        cases.append((skill, make_boss(skill=skill,
                                       timer=NS.SKILL_DUR[skill] // 2)))
    dead = make_boss()
    dead.alive = False
    cases.append(("death", dead))

    for name, b in cases:
        surf.fill((0, 0, 0, 0))
        warm(surf, b, 380, 380, frames=4)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 30 and br.height > 30, (name, br)
    F.reset_all()


def test_renderer_facing_and_portrait():
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for d in (1, -1):
        b = make_boss()
        b.direction = d
        surf.fill((0, 0, 0, 0))
        L.draw_pyrenth(surf, b, 350, 350)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 30, d
    # portrait: lapisan hidup TIDAK ikut (potret harus statis)
    b = make_boss()
    b._portrait_hd = True
    surf.fill((0, 0, 0, 0))
    L.draw_pyrenth(surf, b, 350, 350)
    assert not F.owns(b), "lapisan hidup ikut di potret HD"
    F.reset_all()


def test_canvas_fallback_when_nobody_draws_live_layer():
    """Kalau tidak ada yang menggambar lapisan hidup, FX canvas tetap
    hidup — karakter tidak boleh kehilangan efek diam-diam."""
    F.reset_all()
    b = make_boss(skill="e", timer=25)
    b._render_scale = 0.5                 # lane hero (lapisan hidup off)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    L.draw_pyrenth(surf, b, 350, 350)
    assert not getattr(b, "_pyr_suppress_canvas_fx", False), \
        "fallback canvas dimatikan padahal lapisan hidup tidak digambar"
    assert surf.get_bounding_rect(min_alpha=16).width > 40
    F.reset_all()


def test_hero_lane_pipeline():
    import heroes as H
    F.reset_all()
    h = SimpleNamespace(
        hero_type="pyrenth", boss_type="pyrenth", boss_class="mini",
        team="blue", x=200.0, y=200.0, direction=1, facing=1, pulse=1.0,
        timer=0, attack_cooldown=44, attack_timer=0, anim_time=0,
        active_skill=None, active_skill_timer=0, hp=880, max_hp=880,
        damage=10, base_damage=10, range=55, attack_range=55,
        speed=1.0, radius=16, alive=True, hurt_flash_timer=0,
        _render_scale=1.2, target=None)
    surf = pygame.Surface((560, 560), pygame.SRCALPHA)
    for _ in range(8):
        H.render_hero("pyrenth", surf, h, 280, 280)
        F.tick(1.0 / 60.0)
        time.sleep(0.001)
    assert F.owns(h), "lapisan hidup tidak ter-attach di jalur hero"
    assert F.recently_drawn(h), "lapisan hidup tidak digambar di jalur hero"
    br = surf.get_bounding_rect(min_alpha=16)
    assert br.width > 30 and br.height > 30
    F.reset_all()


def test_other_level4_bosses_still_draw():
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for name in ("pyrenth", "pyrenth", "ignis_drachorn"):
        fn = getattr(L, "draw_" + name, None)
        if fn is None:
            continue
        b = make_boss()
        b.boss_type = name
        surf.fill((0, 0, 0, 0))
        fn(surf, b, 350, 350)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 20, name


def test_additive_blit_respects_alpha():
    """Glow additif harus MELURUH, bukan jadi cakram warna penuh.

    `BLEND_RGB_ADD`/`BLEND_RGBA_ADD` menambahkan kanal warna tanpa
    melihat alpha, jadi decal bergradien yang langsung ditambahkan akan
    muncul sebagai piringan pekat bertepi keras. `F.blit_add`
    memperbaikinya dengan premultiply. Tes ini mengunci perbaikan itu.
    """
    NS.PALETTE  # pastikan palet renderer terbaca
    R = 120
    glow = F.glow_surface(R, F.P["molten_bright"], power=1.0)
    c = glow.get_size()[0] // 2          # pusat decal
    surf = pygame.Surface((400, 400))
    surf.fill((0, 0, 0))
    F.blit_add(surf, glow, (200 - c, 200 - c))

    def lum(x, y):
        r, g, b = surf.get_at((x, y))[:3]
        return r + g + b

    center = lum(200, 200)
    mid = lum(200 + 60, 200)
    edge = lum(200 + 112, 200)
    assert center > 120, "glow tidak tergambar sama sekali (%d)" % center
    assert mid < center * 0.92, \
        "glow tidak meluruh dari inti ke tengah (%d -> %d)" % (center, mid)
    assert edge < center * 0.55, \
        "tepi glow masih pekat -> cakram bertepi keras (%d vs %d)" % (
            edge, center)
    # di luar radius tidak boleh ada apa pun
    assert lum(200 + 160, 200) == 0, "glow bocor ke luar radiusnya"

    # decal-nya sendiri harus menulis cakupan alpha (dipakai hero-lane
    # kalau suatu hari dikomposit ke canvas SRCALPHA); pada surface
    # opaque di pipeline riil, BLEND_RGB_ADD sudah cukup.
    assert glow.get_at((c, c)).a > 30, "decal glow tidak menulis alpha"
    assert glow.get_at((c + R, c)).a < 30, "alpha glow bocor ke tepi"


def test_afterimages_bounded():
    """Lunge R (Infernal Blade) meninggalkan afterimage (dari rig
    tersimpan) yang terbatas jumlahnya dan meluruh sendiri."""
    F.reset_all()
    b = make_boss(skill="r", timer=40)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    # rig harus tersimpan dulu (afterimage = salinan surface rig)
    L.draw_pyrenth(surf, b, 350, 350)
    d = F.director_for(b)
    d.sync(b, 350.0, 350.0)
    peak = 0
    for _ in range(80):
        F.tick(1.0 / 60.0)
        d.sync(b, 350.0, 350.0)
        peak = max(peak, len(d.afterimages))
        assert len(d.afterimages) <= F.MAX_AFTERIMAGES
    assert peak >= 1, "lunge R tidak meninggalkan afterimage"
    for _ in range(300):
        F.tick(1.0 / 60.0)
    assert len(d.afterimages) == 0, "afterimage abadi"
    F.reset_all()


def test_cache_bounded():
    F.reset_all()
    F.clear_cache()
    boss = make_boss(skill="r", timer=40)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for _ in range(90):
        L.draw_pyrenth(surf, boss, 350, 350)
        F.tick(1.0 / 60.0)
    assert F.cache_size() <= F._CACHE_CAP, F.cache_size()
    F.reset_all()
    assert F.cache_size() == 0


# ── 10. GAME FEEL (hit stop + shake) ────────────────────────────────
def test_hit_stop_and_shake():
    F.reset_all()
    CF.reset()
    boss = make_boss(target_dist=40.0)
    F.attach(boss)
    F.director_for(boss).sync(boss, 300.0, 300.0)
    F.notify_melee_impact(boss, boss.target, 100, True)
    # hit-stop hidup, dan durasinya berada di jendela 0.03 - 0.08 s
    assert CF.HITSTOP.active, "benturan berat tanpa hit-stop"
    secs = CF.HITSTOP.frames * CF.FIXED_DT
    assert CF.HIT_STOP_MIN - 1e-9 <= secs <= CF.HIT_STOP_MAX + 1e-9, secs
    frozen = 0
    for _ in range(30):
        if CF.should_freeze_frame():
            frozen += 1
    assert frozen == CF.HITSTOP.total or frozen > 0
    assert not CF.HITSTOP.active, "hit-stop tidak pernah selesai"

    # screen shake meluruh sampai nol
    CF.reset()
    CF.shake(14.0, 0.3, forward_to_camera=False)
    a0 = CF.amount()
    assert a0 > 0.0, "shake tidak pernah menyala"
    for _ in range(180):
        CF.tick()
        CF.SHAKE.update(1.0 / 60.0)
    a1 = CF.amount()
    assert a1 < a0 and a1 <= 0.01, "screen shake tidak meluruh (%.4f)" % a1
    CF.reset()
    F.reset_all()


def test_impact_flash_uses_transparent_surface():
    F.reset_all()
    d = F.PyrenthFXDirector()
    d.add_impact(200.0, 200.0, kind="melee", power=1.0)
    assert len(d.impacts) == 1
    surf = pygame.Surface((400, 400))
    surf.fill((0, 0, 0))
    d.impacts[0].draw(surf)
    assert surf.get_bounding_rect().width > 0, "flash tidak terlihat"
    for _ in range(180):
        d.update(1.0 / 60.0)
    assert len(d.impacts) == 0, "impact FX abadi"
    F.reset_all()


# ── 11. DEBUG OVERLAY ───────────────────────────────────────────────
def test_debug_overlay():
    F.reset_all()
    boss = make_boss(skill="q", timer=30)
    d = F.director_for(boss)
    d.sync(boss, 300.0, 300.0)
    d.update(1.0 / 60.0)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    F.draw_debug_overlay(surf, d)
    assert surf.get_bounding_rect(min_alpha=1).width > 0
    # flag renderer & FX ada dan default OFF
    assert F.DEBUG_CHARACTER is False
    assert NS.DEBUG_CHARACTER is False
    old_f, old_n = F.DEBUG_CHARACTER, NS.DEBUG_CHARACTER
    try:
        F.DEBUG_CHARACTER = True
        NS.DEBUG_CHARACTER = True
        surf.fill((0, 0, 0, 0))
        L.draw_pyrenth(surf, boss, 350, 350)
        assert surf.get_bounding_rect(min_alpha=1).width > 0
    finally:
        F.DEBUG_CHARACTER = old_f
        NS.DEBUG_CHARACTER = old_n
    F.reset_all()


# ── 12. INTEGRASI AI + REGISTRY ─────────────────────────────────────
def test_base_boss_integration():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    assert "_pyrfx.notify_skill_cast" in src
    assert "_pyrfx.notify_skill_impact" in src
    for skill in ("'q'", "'w'", "'e'", "'r'"):
        assert "_pyrfx.notify_skill_cast(self, %s)" % skill in src, skill
    # KONTRAK BARU: serangan dasar tidak memicu impact FX; hook melee
    # pyrenth di base_boss sudah dibuang. API modulnya tetap ada.
    assert "_pyrfx.notify_melee_impact" not in src, \
        "serangan dasar boss masih memicu impact FX pyrenth"
    assert callable(getattr(F, "notify_melee_impact", None)), \
        "API notify_melee_impact hilang dari pyrenth_fx"
    src4 = open(os.path.join(ROOT, "bosses", "level4.py"),
                "r", encoding="utf-8").read()
    assert "heroes import pyrenth_fx as mod" in src4
    assert "draw_live_layer" in src4


def test_registry():
    import re
    import heroes as H
    assert "pyrenth" in H._LIVE_FX_HEROES
    assert H._LIVE_FX_PATHS.get("pyrenth") == "heroes.pyrenth_fx"
    # plat nama: jangkar harus di ATAS puncak rig v3 (tanduk ~-78 px).
    # (base_boss diimpor sebagai TEKS — modulnya butuh settings.py yang
    #  hanya ada di lingkungan runtime game, bukan di checkout ini.)
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    m = re.search(r'BOSS_LABEL_TOP\s*=\s*\{[^}]*"pyrenth":\s*(\d+)', src,
                  re.S)
    assert m, "BOSS_LABEL_TOP tidak punya entri pyrenth"
    anchor = int(m.group(1))
    # jangkar HARUS di atas puncak rig v3 yang diukur langsung dari
    # piksel (tanduk), bukan angka hafalan.
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    top = 0
    for i in range(24):
        surf.fill((0, 0, 0, 0))
        NS._draw_pyr_body(surf, 350, 350, 1, i * 0.3, "idle")
        r = surf.get_bounding_rect(min_alpha=1)
        top = max(top, 350 - r.top)
    assert anchor >= top + 8, \
        "BOSS_LABEL_TOP pyrenth (%d) terlalu rendah, puncak rig %d" % (
            anchor, top)


# ── 13. PROSEDURAL MURNI ────────────────────────────────────────────
def test_procedural_only():
    """Tidak boleh ada pemuatan aset gambar sama sekali.

    Yang dilarang adalah PEMANGGILAN loader; komentar/docstring yang
    menyebut nama fungsinya (untuk menjelaskan aturan ini) tetap boleh.
    """
    for rel in (("heroes", "pyrenth_fx.py"), ("bosses", "level4.py")):
        src = open(os.path.join(ROOT, *rel), "r", encoding="utf-8").read()
        assert "pygame.image.load(" not in src, rel
        assert "image.frombuffer(" not in src, rel
        assert "image.fromstring(" not in src, rel
        assert "import PIL" not in src and "from PIL" not in src, rel
        for ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
            assert '"%s"' % ext not in src and "'%s'" % ext not in src, \
                (rel, ext)


# ── 14. PERFORMANCE / NO UNBOUNDED FX ───────────────────────────────
def test_fx_bounded_and_reset():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    d.sync(boss, 300.0, 300.0)
    for i in range(80):
        skill = ("q", "w", "e", "r")[i % 4]
        F.notify_projectile_cast(boss, 300.0, 300.0)
        F.notify_skill_cast(boss, skill)
        F.notify_skill_impact(boss, 300.0 + i, 300.0, None, skill)
        F.notify_melee_impact(boss, boss.target, 100, False)
        F.notify_hurt(boss, 40)
        d.attack_active = False
        assert d.particles.count() <= F.MAX_PARTICLES
        assert d.projectiles.count() <= F.MAX_PROJECTILES
        assert len(d.skills) <= F.MAX_SKILLS
        assert len(d.impacts) <= F.MAX_IMPACTS
        assert len(d.afterimages) <= F.MAX_AFTERIMAGES
    for _ in range(2000):
        F.tick(1.0 / 60.0)
    assert F.total_particles() == 0, "partikel tidak pernah habis"
    assert d.projectiles.count() == 0, "proyektil tidak pernah habis"
    assert len(d.skills) == 0 and len(d.impacts) == 0
    st = F.stats()
    assert isinstance(st, dict) and "particles" in st
    F.reset_all()
    assert F.total_particles() == 0 and not F.owns(boss)


def test_director_pool_bounded():
    F.reset_all()
    bosses = [make_boss() for _ in range(F.MAX_DIRECTORS + 15)]
    for b in bosses:
        F.attach(b)
    assert len(F._DIRECTORS) <= F.MAX_DIRECTORS, len(F._DIRECTORS)
    F.reset_all()


def test_frame_budget():
    """60 frame penuh (badan + FX) harus jauh di bawah anggaran 16 ms."""
    F.reset_all()
    boss = make_boss(skill="r", timer=40)
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)
    L.draw_pyrenth(surf, boss, 450, 380)          # warm cache
    F.tick(1.0 / 60.0)
    t0 = time.perf_counter()
    for _ in range(60):
        surf.fill((0, 0, 0, 0))
        L.draw_pyrenth(surf, boss, 450, 380)
        F.tick(1.0 / 60.0)
    ms = (time.perf_counter() - t0) * 1000.0 / 60.0
    assert ms < 16.0, "%.2f ms/frame terlalu berat" % ms
    print("   %.2f ms/frame (badan + lapisan FX, skill R aktif)" % ms)
    F.reset_all()


TESTS = [
    test_module_api,
    test_palette_contract,
    test_anim_controller,
    test_always_melee,
    test_blade_arc_continuity,
    test_blade_geometry_single_source,
    test_lunge_offset_bridge,
    test_swing_trail_records_history,
    test_particle_contract,
    test_particle_cap_is_hard,
    test_doom_lifecycle,
    test_doom_is_not_a_plain_circle,
    test_soul_ember_projectile,
    test_projectile_cap,
    test_skill_lifecycle_and_dedup,
    test_skill_phase_table,
    test_skill_radius_matches_gameplay,
    test_engine_progress_drives_skill_fx,
    test_aoe_telegraph_is_a_true_circle,
    test_skill_shapes_are_not_all_circles,
    test_renderer_with_live_fx,
    test_renderer_all_states,
    test_renderer_facing_and_portrait,
    test_canvas_fallback_when_nobody_draws_live_layer,
    test_hero_lane_pipeline,
    test_other_level4_bosses_still_draw,
    test_additive_blit_respects_alpha,
    test_afterimages_bounded,
    test_cache_bounded,
    test_hit_stop_and_shake,
    test_impact_flash_uses_transparent_surface,
    test_debug_overlay,
    test_base_boss_integration,
    test_registry,
    test_procedural_only,
    test_fx_bounded_and_reset,
    test_director_pool_bounded,
    test_frame_budget,
]


if __name__ == "__main__":
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print("PASS  %s" % fn.__name__)
        except AssertionError as e:
            failed += 1
            print("FAIL  %s: %s" % (fn.__name__, e))
        except Exception as e:                      # noqa: BLE001
            failed += 1
            print("ERROR %s: %r" % (fn.__name__, e))
    print()
    if failed:
        print("%d/%d test GAGAL" % (failed, len(TESTS)))
        sys.exit(1)
    print("SEMUA %d TEST PYRENTH V3 LULUS" % len(TESTS))
