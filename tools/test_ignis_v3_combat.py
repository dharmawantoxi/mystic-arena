#!/usr/bin/env python3
"""Regression test IGNIS DRACHORN V3 (renderer + live combat-FX engine).

Mengunci:
  * lapisan hidup heroes/ignis_drachorn_fx.py punya semua API yang
    dipakai pipeline hero/boss (attach/owns/tick/draw_*_layer/notify_*);
  * palette kontrak 9 kunci wajib hadir (renderer DAN lapisan FX);
  * animation controller (_NS_ignis_drachorn): state, prioritas, fase
    serangan, hit window, delta-time;
  * ayunan ARK greatsword: kontinu, tanpa teleport, dan renderer <-> FX
    membaca SATU sumber geometri yang sama (sword_geometry);
  * proyektil (fire orb + meteor) spawn -> travel -> trail -> hit ->
    impact FX -> destroy;
  * skill FX q/w/e/r lifecycle penuh dan selesai dalam waktu terbatas;
  * renderer bosses/level4.draw_ignis_drachorn hidup bersama lapisan FX
    tanpa exception (boss lane + hero lane), semua pose;
  * boss AI (base_boss.py) memanggil lapisan FX ignis;
  * prosedural murni (tanpa pygame.image.load / aset gambar);
  * tidak ada partikel/proyektil/skill yang hidup tanpa batas;
  * boss lain di bundle level4 tidak ikut rusak.

Jalankan:
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
      python3 tools/test_ignis_v3_combat.py
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

from heroes import ignis_drachorn_fx as F
import bosses.level4 as L

NS = L._NS_ignis_drachorn


def make_boss(x=100.0, y=100.0, skill=None, timer=0, target=True,
              hero_lane=False):
    b = SimpleNamespace(
        boss_type="ignis_drachorn", boss_class="true", team="red",
        x=float(x), y=float(y), direction=1, facing=1, pulse=1.2,
        timer=0, attack_cooldown=42, attack_range=55, range=55,
        active_skill=skill, active_skill_timer=timer,
        target=(SimpleNamespace(x=x + 130.0, y=float(y), alive=True,
                                radius=12) if target else None),
        hurt_flash_timer=0, alive=True, radius=45,
        hp=25000, max_hp=25000, damage=120, speed=0.9)
    if hero_lane:
        b._render_scale = 1.0
    return b


# ── 1. API + PALETTE ────────────────────────────────────────────────
def test_module_api():
    required = [
        "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
        "Afterimage", "BaseProjectile", "FireOrbProjectile",
        "MeteorProjectile", "ProjectileSystem", "SkillFX",
        "IgnisFXDirector",
        "attach", "owns", "tick", "reset_all", "total_particles", "stats",
        "draw_ground_layer", "draw_live_layer", "director_for",
        "projectiles_for", "notify_melee_impact",
        "notify_projectile_impact", "notify_projectile_cast",
        "notify_skill_impact", "notify_skill_cast", "notify_hurt",
        "notify_death", "draw_debug_overlay", "IGNIS_PALETTE",
        "DEBUG_CHARACTER", "sword_arc", "sword_points", "pose_of",
        "attack_phase",
    ]
    for name in required:
        assert hasattr(F, name), "API hilang: ignis_drachorn_fx.%s" % name
    # renderer juga menjaga API lamanya (backward compatible)
    for name in ("PALETTE", "FireProjectile", "draw_ignis",
                 "draw_ignis_drachorn", "draw_boss", "_update_attack_anim",
                 "_manage_projectiles", "_spawn_fire_projectile",
                 "_target_position", "_draw_flame_puff",
                 "_draw_sword_swing_trail", "_draw_dragon_breath",
                 "_draw_elder_dragon_form", "sword_geometry"):
        assert hasattr(NS, name), "API renderer hilang: %s" % name
    assert callable(L.draw_ignis_drachorn)


def test_palette_contract():
    keys = {"outline", "shadow", "dark", "body", "mid", "light",
            "highlight", "weapon", "fx"}
    assert keys.issubset(F.IGNIS_PALETTE.keys()), "palette FX kurang kunci"
    assert keys.issubset(NS.PALETTE.keys()), "palette renderer kurang kunci"
    for k, v in F.IGNIS_PALETTE.items():
        assert len(v) == 3 and all(0 <= c <= 255 for c in v), k


# ── 2. ANIMATION CONTROLLER ─────────────────────────────────────────
def test_anim_controller():
    boss = make_boss()
    NS._update_ignis_anim(boss, moving=False)
    assert boss._ign_state == "IDLE", boss._ign_state

    boss._ign_speed = 0.5
    NS._update_ignis_anim(boss, moving=True)
    assert boss._ign_state == "WALK", boss._ign_state
    boss._ign_speed = 2.4
    NS._update_ignis_anim(boss, moving=True)
    assert boss._ign_state == "RUN", boss._ign_state

    boss.active_skill = "q"
    boss.active_skill_timer = 30
    NS._update_ignis_anim(boss, moving=False)
    assert boss._ign_state == "SKILL", boss._ign_state
    boss.active_skill = "r"
    NS._update_ignis_anim(boss, moving=False)
    assert boss._ign_state == "SPECIAL", boss._ign_state
    boss.active_skill = None

    boss.hurt_flash_timer = 6
    NS._update_ignis_anim(boss, moving=False)
    assert boss._ign_state == "HURT", boss._ign_state
    boss.hurt_flash_timer = 0

    boss.alive = False
    NS._update_ignis_anim(boss, moving=False)
    assert boss._ign_state == "DEATH", boss._ign_state
    boss.alive = True

    # prioritas: DEATH > HURT > SKILL > ATTACK > WALK > IDLE
    pr = NS.ANIM_STATES
    assert pr["DEATH"] > pr["HURT"] > pr["SKILL"] > pr["ATTACK"] \
        > pr["WALK"] > pr["IDLE"]

    # timeline serangan: timer engine menghitung MUNDUR lalu di-reset
    boss = make_boss()
    boss.timer = 1
    NS._update_ignis_anim(boss, moving=False)
    boss.timer = 42
    NS._update_ignis_anim(boss, moving=False)
    assert boss._ign_attack_active, "serangan tidak terdeteksi"
    phases = []
    for _ in range(40):
        NS._update_ignis_anim(boss, moving=False)
        phases.append(boss._ign_attack_phase)
        assert 0.0 < boss._ign_dt <= 0.05
    order = [p for i, p in enumerate(phases) if i == 0 or p != phases[i - 1]]
    order = [p for p in order if p != "NONE"]
    expected = ["ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW",
                "RECOVERY"]
    assert order == expected, order

    # fase & hit window konsisten dengan tabel
    names = set(n for n, _a, _b in NS.ATTACK_PHASES)
    for p in (0.0, 0.1, 0.2, 0.4, 0.55, 0.7, 0.9, 1.0):
        assert NS.attack_phase(p) in names
    assert NS.attack_phase(0.40) == "SWING"
    assert NS.attack_phase(0.55) == "IMPACT"
    assert NS.attack_phase(0.95) == "RECOVERY"
    lo, hi = NS.ATTACK_ACTIVE_WINDOW
    assert lo < NS.ATTACK_IMPACT_FRAME < hi
    # lapisan hidup membaca tabel fase yang sama
    for p in (0.05, 0.2, 0.4, 0.55, 0.7, 0.9):
        assert F.attack_phase(p) == NS.attack_phase(p)


# ── 3. SWORD ARC ────────────────────────────────────────────────────
def test_sword_arc_continuity():
    prev = None
    max_step = 0.0
    for i in range(201):
        theta, lift = NS._sword_arc(i / 200.0)
        assert -2.0 <= theta <= 3.2, theta
        assert 0.0 <= lift <= 1.0, lift
        if prev is not None:
            max_step = max(max_step, abs(theta - prev))
        prev = theta
    assert max_step < 0.30, max_step          # tanpa teleport senjata
    # mulai & selesai di titik istirahat yang sama (loop mulus)
    assert abs(NS._sword_arc(0.0)[0] - NS._sword_arc(1.0)[0]) < 1e-6
    # lapisan hidup membaca SUMBER YANG SAMA
    for p in (0.0, 0.12, 0.31, 0.52, 0.7, 0.93, 1.0):
        a = NS._sword_arc(p)
        b = F.sword_arc(p)
        assert abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9

    # geometri bilah: panjang konstan, grip & tip konsisten
    for p in (0.0, 0.25, 0.5, 0.75, 1.0):
        grip, tip, theta = NS.sword_geometry(1, "melee", 0.0, p)
        length = math.hypot(tip[0] - grip[0], tip[1] - grip[1])
        assert abs(length - NS.BLADE_LEN) < 1e-6, length
    # mirror facing
    g1, t1, _ = NS.sword_geometry(1, "melee", 0.0, 0.4)
    g2, t2, _ = NS.sword_geometry(-1, "melee", 0.0, 0.4)
    assert abs(g1[0] + g2[0]) < 1e-6 and abs(t1[0] + t2[0]) < 1e-6

    # trail lapisan hidup memakai geometri yang sama (skala layar 1:1)
    boss = make_boss()
    boss._ign_pose_action = "melee"
    boss._ign_attack_progress = 0.4
    boss._ign_phase = 0.0
    grip, tip = F.sword_points(boss, 200.0, 200.0)
    g, t, _ = NS.sword_geometry(1, "melee", 0.0, 0.4)
    assert abs(grip[0] - (200.0 + g[0])) < 1e-6
    assert abs(tip[1] - (200.0 + t[1])) < 1e-6


def test_swing_trail_records_history():
    F.reset_all()
    boss = make_boss()
    F.attach(boss)
    d = F.director_for(boss)
    boss._ign_pose_action = "melee"
    boss._ign_phase = 0.0
    for i in range(1, 30):
        boss._ign_attack_progress = i / 30.0
        d.sync(boss, 200.0, 200.0)
        d.update(1.0 / 60.0)
    assert len(d.trail.history) > 2, "trail tidak merekam posisi senjata"
    assert len(d.trail.history) <= F.TRAIL_SAMPLES
    # digambar ADDITIF, jadi diuji di surface opaque (seperti layar asli)
    surf = pygame.Surface((640, 480))
    surf.fill((0, 0, 0))
    d.trail.draw(surf)
    assert surf.get_bounding_rect().width > 0
    # trail meluruh sendiri (bukan efek abadi)
    for _ in range(120):
        d.update(1.0 / 60.0)
    assert len(d.trail.history) == 0
    F.reset_all()


# ── 4. PROJECTILES ──────────────────────────────────────────────────
def test_projectile_lifecycle():
    F.reset_all()
    boss = make_boss()
    assert F.attach(boss) and F.owns(boss)
    F.notify_projectile_cast(boss, boss.x, boss.y)
    projs = F.projectiles_for(boss)
    assert len(projs) == 1
    orb = projs[0]
    # kontrak atribut proyektil modular
    for attr in ("position", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(orb, attr), attr
    assert isinstance(orb.position, pygame.Vector2)
    assert isinstance(orb.velocity, pygame.Vector2)
    start = pygame.Vector2(orb.position)
    for _ in range(240):
        F.tick(1.0 / 60.0)
        if not orb.active:
            break
    assert not orb.active, "orb tidak pernah menghilang"
    assert orb.hit, "orb tidak pernah mengenai target"
    assert (start - orb.position).length() > 20.0, "orb tidak bergerak"
    assert len(orb.trail) > 2, "orb tidak punya trail"
    d = F.director_for(boss)
    assert len(d.projectiles.impacts) > 0, "impact FX tidak muncul"
    assert len(F.projectiles_for(boss)) == 0, "proyektil bocor"
    F.reset_all()


def test_meteor_projectile():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    m = d.projectiles.spawn_meteor(boss.x, boss.y, delay=0.0, radius=18)
    assert m.active and m.kind == "meteor"
    for _ in range(300):
        F.tick(1.0 / 60.0)
        if not m.active:
            break
    assert not m.active, "meteor tidak pernah mendarat"
    assert m.hit, "meteor mendarat tanpa impact"
    F.reset_all()


def test_projectile_cap():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    for _ in range(F.MAX_PROJECTILES + 12):
        d.projectiles.spawn_orb(boss.x, boss.y, boss.x + 400, boss.y)
    assert d.projectiles.count() <= F.MAX_PROJECTILES
    F.reset_all()


# ── 5. SKILL FX ─────────────────────────────────────────────────────
def test_skill_lifecycle_and_dedup():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    d.sync(boss, boss.x, boss.y)
    F.notify_skill_cast(boss, "q")
    F.notify_skill_impact(boss, boss.x + 100, boss.y, 140, "q")
    assert len([s for s in d.skills if s.skill == "q"]) == 1, \
        "cast+impact membuat SkillFX dobel"
    fx = d.skills[0]
    seen = set()
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)
    for _ in range(400):
        seen.add(fx.phase())
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
    for _ in range(400):
        F.tick(1.0 / 60.0)
        d.draw_ground(surf)
        d.draw_front(surf)
    assert len(d.skills) == 0, "skill FX abadi"
    F.reset_all()


def test_skill_radius_matches_gameplay():
    # radius FX = radius damage AI (base_boss)
    assert F.WORLD_RADIUS["q"] == 250.0
    assert F.WORLD_RADIUS["w"] == 130.0
    assert F.WORLD_RADIUS["r"] == 220.0
    assert F.SKILL_DUR == {"q": 45, "w": 40, "e": 60, "r": 90}
    assert NS.SKILL_DUR == F.SKILL_DUR


# ── 6. RENDERER + LIVE LAYER ────────────────────────────────────────
def test_renderer_with_live_fx():
    F.reset_all()
    boss = make_boss(skill="r", timer=60)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for _ in range(30):
        L.draw_ignis_drachorn(surf, boss, 350, 350)
        F.tick(1.0 / 60.0)
        time.sleep(0.001)
    br = surf.get_bounding_rect(min_alpha=64)
    assert br.width > 40 and br.height > 40, (br.width, br.height)
    assert F.owns(boss), "lapisan hidup tidak mengambil alih di boss lane"
    assert getattr(boss, "_ign_suppress_canvas_fx", False), \
        "fallback canvas tidak dimatikan padahal lapisan hidup aktif"
    F.reset_all()


def test_renderer_all_states():
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    cases = []
    cases.append(("idle", make_boss()))
    walk = make_boss()
    walk._ign_speed = 0.6
    cases.append(("walk", walk))
    hurt = make_boss()
    hurt.hurt_flash_timer = 6
    cases.append(("hurt", hurt))
    atk = make_boss()
    atk._ign_attack_active = True
    atk._ign_attack_frame = 18
    atk._ign_prev_timer = 40
    atk.timer = 39
    cases.append(("attack", atk))
    ranged = make_boss()
    ranged.attack_range = 180
    ranged._ign_attack_active = True
    ranged._ign_attack_frame = 12
    ranged._ign_prev_timer = 40
    ranged.timer = 39
    cases.append(("ranged", ranged))
    for skill in ("q", "w", "e", "r"):
        cases.append((skill, make_boss(skill=skill,
                                       timer=F.SKILL_DUR[skill])))
    dead = make_boss()
    dead.alive = False
    cases.append(("death", dead))

    for name, b in cases:
        surf.fill((0, 0, 0, 0))
        for _ in range(4):
            L.draw_ignis_drachorn(surf, b, 350, 350)
            F.tick(1.0 / 60.0)
            time.sleep(0.001)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 30 and br.height > 30, (name, br)
    F.reset_all()


def test_renderer_facing_and_portrait():
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for d in (1, -1):
        b = make_boss()
        b.direction = d
        surf.fill((0, 0, 0, 0))
        L.draw_ignis_drachorn(surf, b, 350, 350)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 30, d
    # portrait: lapisan hidup TIDAK ikut (potret harus statis)
    b = make_boss()
    b._portrait_hd = True
    surf.fill((0, 0, 0, 0))
    L.draw_ignis_drachorn(surf, b, 350, 350)
    assert not F.owns(b), "lapisan hidup ikut di potret HD"
    F.reset_all()


def test_hero_lane_pipeline():
    import heroes as H
    F.reset_all()
    h = SimpleNamespace(
        hero_type="ignis_drachorn", boss_type="ignis_drachorn",
        boss_class="true", team="blue", x=200.0, y=200.0, direction=1,
        facing=1, pulse=1.0, timer=0, attack_cooldown=42, attack_timer=0,
        anim_time=0, active_skill=None, active_skill_timer=0, hp=900,
        max_hp=900, damage=10, base_damage=10, range=55, attack_range=55,
        speed=1.0, radius=16, alive=True, hurt_flash_timer=0,
        _render_scale=1.2, target=None)
    surf = pygame.Surface((520, 520), pygame.SRCALPHA)
    for _ in range(8):
        H.render_hero("ignis_drachorn", surf, h, 260, 260)
        F.tick(1.0 / 60.0)
        time.sleep(0.001)
    assert F.owns(h), "lapisan hidup tidak ter-attach di jalur hero"
    br = surf.get_bounding_rect(min_alpha=16)
    assert br.width > 30 and br.height > 30
    F.reset_all()


def test_other_level4_bosses_still_draw():
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for name in ("zharok", "pyrenth", "vokrahn"):
        fn = getattr(L, "draw_" + name, None)
        if fn is None:
            continue
        b = make_boss()
        b.boss_type = name
        surf.fill((0, 0, 0, 0))
        fn(surf, b, 350, 350)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 20, name


# ── 7. DEBUG OVERLAY ────────────────────────────────────────────────
def test_debug_overlay():
    F.reset_all()
    boss = make_boss(skill="q", timer=30)
    d = F.director_for(boss)
    d.sync(boss, 300.0, 300.0)
    d.update(1.0 / 60.0)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    F.draw_debug_overlay(surf, d)
    assert surf.get_bounding_rect(min_alpha=1).width > 0
    # flag renderer juga ada dan default OFF
    assert F.DEBUG_CHARACTER is False
    assert NS.DEBUG_CHARACTER is False
    old = F.DEBUG_CHARACTER
    try:
        F.DEBUG_CHARACTER = True
        surf.fill((0, 0, 0, 0))
        L.draw_ignis_drachorn(surf, boss, 350, 350)
    finally:
        F.DEBUG_CHARACTER = old
    F.reset_all()


# ── 8. AI INTEGRATION (source check) ────────────────────────────────
def test_base_boss_integration():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    assert "from heroes import ignis_drachorn_fx as _ignfx" in src
    assert "_ignfx.notify_skill_cast" in src
    assert "_ignfx.notify_skill_impact" in src
    assert "_ignfx.notify_melee_impact" in src
    src4 = open(os.path.join(ROOT, "bosses", "level4.py"),
                "r", encoding="utf-8").read()
    assert "heroes import ignis_drachorn_fx" in src4
    assert "notify_projectile_cast" in src4
    assert "draw_live_layer" in src4


def test_registry():
    import heroes as H
    assert "ignis_drachorn" in H._LIVE_FX_HEROES
    assert H._LIVE_FX_PATHS.get("ignis_drachorn") == \
        "heroes.ignis_drachorn_fx"


# ── 9. PROCEDURAL ONLY ──────────────────────────────────────────────
def test_procedural_only():
    """Tidak boleh ada pemuatan aset gambar sama sekali.

    Yang dilarang adalah PEMANGGILAN loader; komentar/docstring yang
    menyebut nama fungsinya (untuk menjelaskan aturan ini) tetap boleh.
    """
    for rel in (("heroes", "ignis_drachorn_fx.py"),
                ("bosses", "level4.py")):
        src = open(os.path.join(ROOT, *rel), "r", encoding="utf-8").read()
        assert "pygame.image.load(" not in src, rel
        assert "image.frombuffer(" not in src, rel
        assert "image.fromstring(" not in src, rel
        assert "import PIL" not in src and "from PIL" not in src, rel
        for ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
            assert '"%s"' % ext not in src and "'%s'" % ext not in src, \
                (rel, ext)


# ── 10. PERFORMANCE / NO UNBOUNDED FX ───────────────────────────────
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
        F.notify_melee_impact(boss, boss.target, 120, False)
        F.notify_hurt(boss, 40)
        d.swing_done = False
        assert d.particles.count() <= F.MAX_PARTICLES
        assert d.projectiles.count() <= F.MAX_PROJECTILES
        assert len(d.skills) <= F.MAX_SKILLS
        assert len(d.impacts) <= F.MAX_IMPACTS
    for _ in range(1500):
        F.tick(1.0 / 60.0)
    assert F.total_particles() == 0, "partikel tidak pernah habis"
    assert d.projectiles.count() == 0, "proyektil tidak pernah habis"
    assert len(d.skills) == 0 and len(d.impacts) == 0
    F.reset_all()
    assert F.total_particles() == 0 and not F.owns(boss)


def test_cache_bounded():
    F.reset_all()
    boss = make_boss(skill="r", timer=90)
    surf = pygame.Surface((700, 700), pygame.SRCALPHA)
    for _ in range(90):
        L.draw_ignis_drachorn(surf, boss, 350, 350)
        F.tick(1.0 / 60.0)
    assert F.cache_size() <= 240, F.cache_size()
    F.reset_all()
    assert F.cache_size() == 0


def test_frame_budget():
    """60 frame penuh (badan + FX) harus jauh di bawah anggaran 16 ms."""
    F.reset_all()
    boss = make_boss(skill="r", timer=90)
    surf = pygame.Surface((900, 700), pygame.SRCALPHA)
    L.draw_ignis_drachorn(surf, boss, 450, 380)     # warm cache
    F.tick(1.0 / 60.0)
    t0 = time.perf_counter()
    for _ in range(60):
        surf.fill((0, 0, 0, 0))
        L.draw_ignis_drachorn(surf, boss, 450, 380)
        F.tick(1.0 / 60.0)
    ms = (time.perf_counter() - t0) * 1000.0 / 60.0
    assert ms < 16.0, "%.2f ms/frame terlalu berat" % ms
    print("   %.2f ms/frame (badan + lapisan FX, skill R aktif)" % ms)
    F.reset_all()


if __name__ == "__main__":
    test_module_api()
    print("PASS API modul + renderer lengkap (backward compatible)")
    test_palette_contract()
    print("PASS palette kontrak 9 kunci (renderer + FX)")
    test_anim_controller()
    print("PASS animation controller (state/prioritas/fase/hit window/dt)")
    test_sword_arc_continuity()
    print("PASS sword arc kontinu + satu sumber geometri renderer<->FX")
    test_swing_trail_records_history()
    print("PASS swing trail merekam histori senjata & meluruh")
    test_projectile_lifecycle()
    print("PASS fire orb spawn->travel->trail->hit->impact->destroy")
    test_meteor_projectile()
    print("PASS meteor ultimate jatuh & menghantam")
    test_projectile_cap()
    print("PASS batas keras proyektil")
    test_skill_lifecycle_and_dedup()
    print("PASS skill FX lifecycle 6 fase + dedup cast/impact")
    test_skill_radius_matches_gameplay()
    print("PASS radius & durasi skill sinkron dengan AI")
    test_renderer_with_live_fx()
    print("PASS renderer + lapisan hidup (boss lane)")
    test_renderer_all_states()
    print("PASS renderer semua pose (idle/walk/hurt/attack/ranged/q/w/e/r)")
    test_renderer_facing_and_portrait()
    print("PASS mirror facing + potret HD statis")
    test_hero_lane_pipeline()
    print("PASS hero-lane pipeline (render_hero + attach)")
    test_other_level4_bosses_still_draw()
    print("PASS boss lain di bundle level4 tidak rusak")
    test_debug_overlay()
    print("PASS overlay DEBUG_CHARACTER")
    test_base_boss_integration()
    print("PASS integrasi base_boss + bridge level4")
    test_registry()
    print("PASS registrasi heroes/__init__")
    test_procedural_only()
    print("PASS prosedural murni (tanpa image.load / aset gambar)")
    test_fx_bounded_and_reset()
    print("PASS tidak ada FX hidup tanpa batas")
    test_cache_bounded()
    print("PASS cache surface terbatas + bersih setelah reset")
    test_frame_budget()
    print("PASS anggaran frame")
    print("ALL IGNIS DRACHORN V3 COMBAT TESTS PASSED")
