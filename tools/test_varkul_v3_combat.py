#!/usr/bin/env python3
"""Regression test Varkul V3 (renderer + live combat-FX engine).

Mengunci:
  * lapisan hidup heroes/varkul_fx.py punya semua API yang dipakai
    pipeline hero/boss (attach/owns/tick/draw_*_layer/notify_*);
  * palette kontrak 9 kunci wajib hadir;
  * animation controller V2 (_NS_varkul): state, fase serangan,
    hit window, delta-time, prioritas;
  * ayunan ARK staff: kontinu, tanpa lompatan, konsisten renderer<->FX;
  * proyektil (frost bolt + chain orb) spawn, travel, hit, destroy;
  * skill FX q/w/e/r lifecycle dan reset ke 0 setelah match;
  * renderer bosses/level3.draw_varkul hidup bersama lapisan FX tanpa
    exception (boss lane + hero lane);
  * boss AI (base_boss.py) memanggil lapisan FX varkul;
  * prosedural murni (tanpa pygame.image.load);
  * tidak ada partikel/proyektil yang hidup tanpa batas.

Jalankan: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_varkul_v3_combat.py
"""
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

from heroes import varkul_fx as F
import bosses.level3 as L


def make_boss(x=100.0, y=100.0, skill=None, timer=0, target=True):
    return SimpleNamespace(
        boss_type="varkul", boss_class="mini", x=float(x), y=float(y),
        direction=1, facing=1, pulse=1.2, timer=0, attack_cooldown=42,
        active_skill=skill, active_skill_timer=timer,
        target=(SimpleNamespace(x=220.0, y=100.0, alive=True,
                                radius=12) if target else None),
        _render_scale=1.0, hurt_flash_timer=0, alive=True, radius=35,
        hp=7500, max_hp=7500, range=100)


# ── 1. API + PALETTE ────────────────────────────────────────────────
def test_module_api():
    required = [
        "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
        "FrostBoltProjectile", "ChainFrostOrbProjectile",
        "ProjectileSystem", "SkillFX", "VarkulFXDirector",
        "attach", "owns", "tick", "reset_all", "total_particles", "stats",
        "draw_ground_layer", "draw_live_layer", "director_for",
        "projectiles_for", "notify_melee_impact", "notify_projectile_impact",
        "notify_projectile_cast", "notify_skill_impact", "notify_skill_cast",
        "notify_hurt", "draw_debug_overlay", "VARKUL_PALETTE",
        "DEBUG_CHARACTER", "staff_arc", "pose_of", "attack_phase",
    ]
    for name in required:
        assert hasattr(F, name), "API hilang: varkul_fx.%s" % name


def test_palette_contract():
    keys = {"outline", "shadow", "dark", "body", "mid", "light",
            "highlight", "weapon", "fx"}
    assert keys.issubset(F.VARKUL_PALETTE.keys())


# ── 2. ANIMATION CONTROLLER ─────────────────────────────────────────
def test_anim_controller():
    boss = make_boss()
    NS = L._NS_varkul
    # idle
    NS._update_varkul_anim(boss, moving=False)
    assert boss._vk_state == "IDLE"
    # walk
    boss.x += 1.0
    NS._update_varkul_anim(boss, moving=True)
    assert boss._vk_state == "WALK"
    # skill -> SKILL, r -> SPECIAL
    boss.active_skill = "q"
    boss.active_skill_timer = 30
    NS._update_varkul_anim(boss, moving=False)
    assert boss._vk_state == "SKILL", boss._vk_state
    boss.active_skill = "r"
    NS._update_varkul_anim(boss, moving=False)
    assert boss._vk_state == "SPECIAL", boss._vk_state
    boss.active_skill = None
    # hurt
    boss.hurt_flash_timer = 6
    NS._update_varkul_anim(boss, moving=False)
    assert boss._vk_state == "HURT", boss._vk_state
    boss.hurt_flash_timer = 0
    # attack: pemicu wrap timer tinggi -> rendah
    boss.timer = 42
    boss._vk_previous_timer = 1
    NS._update_varkul_anim(boss, moving=False)
    assert boss._vk_attack_active
    boss.timer = 40
    NS._update_varkul_anim(boss, moving=False)
    ph = boss._vk_attack_phase
    assert ph in ("ANTICIPATION", "WINDUP"), ph
    # fase & hit window konsisten dengan tabel
    for p in (0.0, 0.1, 0.2, 0.4, 0.5, 0.6, 0.8, 0.95):
        name = NS.attack_phase(p)
        assert name in dict((n, 1) for n, _a, _b in NS.ATTACK_PHASES)
    assert NS.attack_phase(0.45) == "SWING"
    assert NS.attack_phase(0.90) == "RECOVERY"
    # delta time terisi
    assert 0.0 < boss._vk_dt <= 0.05


# ── 3. STAFF ARC ────────────────────────────────────────────────────
def test_staff_arc():
    NS = L._NS_varkul
    prev = None
    max_step = 0.0
    for i in range(101):
        theta, lift = NS._staff_arc(i / 100.0)
        assert -1.3 <= theta <= 1.5, theta
        assert 0.0 <= lift <= 1.0, lift
        if prev is not None:
            max_step = max(max_step, abs(theta - prev))
        prev = theta
    # per langkah 1% progres, lompatan sudut wajar (tanpa teleport)
    assert max_step < 0.40, max_step
    # mulai dan selesai di netral
    assert abs(NS._staff_arc(0.0)[0]) < 0.01
    assert abs(NS._staff_arc(1.0)[0]) < 0.01
    # modul hidup membaca SUMBER YANG SAMA
    for p in (0.1, 0.35, 0.52, 0.7, 0.9):
        a = NS._staff_arc(p)
        b = F.staff_arc(p)
        assert abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6


# ── 4. PROJECTILES ──────────────────────────────────────────────────
def test_projectiles_lifecycle():
    boss = make_boss()
    assert F.attach(boss) and F.owns(boss)
    F.notify_projectile_cast(boss, boss.x, boss.y)
    projs = F.projectiles_for(boss)
    assert len(projs) == 1
    bolt = projs[0]
    assert bolt.active
    start = pygame.Vector2(bolt.x, bolt.y)
    for _ in range(240):
        F.tick(1.0 / 60.0)
        if not bolt.active:
            break
    assert not bolt.active, "bolt tidak pernah menghilang"
    assert bolt.hit_target, "bolt tidak pernah kena target"
    d = F.director_for(boss)
    assert len(d.impacts) > 0, "impact tidak muncul saat bolt kena"
    # chain orb: bounce lalu expire
    d.release_chain_frost(boss.x, boss.y)
    orb = F.projectiles_for(boss)[-1]
    bounces_seen = [0]
    for _ in range(400):
        F.tick(1.0 / 60.0)
        if not orb.active:
            break
    assert not orb.active
    assert len(F.projectiles_for(boss)) == 0, "proyektil bocor"


def test_projectile_cap():
    boss = make_boss()
    F.director_for(boss)
    d = F.director_for(boss)
    for i in range(F.MAX_PROJECTILES + 8):
        d.projectiles.spawn(boss.x, boss.y, boss.x + 100, boss.y,
                            target=None)
    assert d.projectiles.count() <= F.MAX_PROJECTILES


# ── 5. SKILL FX ─────────────────────────────────────────────────────
def test_skill_lifecycle_and_dedup():
    boss = make_boss()
    F.notify_skill_cast(boss, "q")
    F.notify_skill_impact(boss, 200.0, 100.0, 54, "q")
    d = F.director_for(boss)
    assert len([s for s in d.skills if s.skill == "q"]) == 1, \
        "cast+impact membuat SkillFX dobel"
    for skill in ("w", "e", "r"):
        F.notify_skill_cast(boss, skill)
        F.notify_skill_impact(boss, boss.x, boss.y, 60, skill)
    assert len(d.skills) <= F.MAX_SKILLS
    surf = pygame.Surface((320, 320), pygame.SRCALPHA)
    for _ in range(10):
        F.tick(1.0 / 60.0)
        d.draw_ground(surf)
        d.draw_front(surf, boss.x, boss.y)
    # semua skill selesai dalam waktu terbatas (tidak ada FX abadi)
    for _ in range(600):
        F.tick(1.0 / 60.0)
    assert all(s.done for s in d.skills), "skill FX tidak selesai-selseai"
    d.skills.clear()


# ── 6. RENDERER + LIVE LAYER ────────────────────────────────────────
def test_renderer_with_live_fx():
    boss = make_boss(skill="r", timer=50)
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    for _ in range(30):
        F.tick(1.0 / 60.0)
        L.draw_varkul(surf, boss, 230, 230)
        time.sleep(0.001)
    br = surf.get_bounding_rect(min_alpha=64)
    assert br.width > 40 and br.height > 40, (br.width, br.height)
    F.reset_all()


def test_renderer_all_states():
    NS = L._NS_varkul
    surf = pygame.Surface((320, 320), pygame.SRCALPHA)
    # idle / walk / hurt / attack / cast
    cases = [
        ("idle", make_boss()),
        ("walk", None),
        ("hurt", None),
        ("attack", None),
        ("cast", make_boss(skill="w", timer=30)),
    ]
    walk = make_boss()
    cases[1] = ("walk", walk)
    hurt = make_boss()
    hurt.hurt_flash_timer = 6
    cases[2] = ("hurt", hurt)
    atk = make_boss()
    atk._vk_attack_active = True
    atk._vk_attack_frame = 18
    atk._vk_attack_progress = 0.43
    atk._vk_attack_phase = NS.attack_phase(0.43)
    atk._vk_previous_timer = 99
    cases[3] = ("attack", atk)
    for name, b in cases:
        surf.fill((0, 0, 0, 0))
        for _ in range(3):
            L.draw_varkul(surf, b, 160, 160)
            time.sleep(0.001)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 30 and br.height > 30, (name, br)
    print("   semua state render tanpa exception")


def test_hero_lane_pipeline():
    import heroes as H
    h = SimpleNamespace(hero_type="varkul", boss_type="varkul",
                        boss_class="mini", team="blue", x=200.0, y=200.0,
                        direction=1, facing=1, pulse=1.0, timer=0,
                        attack_cooldown=42, attack_timer=0, anim_time=0,
                        active_skill=None, active_skill_timer=0, hp=900,
                        max_hp=900, damage=10, base_damage=10, range=100,
                        speed=1.0, radius=16, alive=True,
                        hurt_flash_timer=0, _render_scale=1.3)
    surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    for _ in range(6):
        H.render_hero("varkul", surf, h, 200, 200)
        time.sleep(0.001)
    assert F.owns(h), "lapisan hidup tidak ter-attach di jalur hero"
    br = surf.get_bounding_rect(min_alpha=16)
    assert br.width > 30 and br.height > 30
    F.reset_all()


# ── 7. AI INTEGRATION (source check) ────────────────────────────────
def test_base_boss_integration():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    assert "from heroes import varkul_fx as _vkfx" in src
    assert "_vkfx.notify_skill_impact" in src
    assert "_vkfx.notify_projectile_impact" in src
    src3 = open(os.path.join(ROOT, "bosses", "level3.py"),
                "r", encoding="utf-8").read()
    assert "from heroes import varkul_fx as _vfx" in src3
    assert "_vfx.notify_projectile_cast" in src3


def test_registry():
    import heroes as H
    assert "varkul" in H._LIVE_FX_HEROES
    assert H._LIVE_FX_PATHS.get("varkul") == "heroes.varkul_fx"


# ── 8. PROCEDURAL ONLY ──────────────────────────────────────────────
def test_procedural_only():
    src = open(os.path.join(ROOT, "heroes", "varkul_fx.py"),
               "r", encoding="utf-8").read()
    assert "pygame.image.load" not in src
    for ext in (".png", ".jpg", ".gif", ".bmp"):
        assert f'"{ext}"' not in src


# ── 9. NO UNBOUNDED FX ──────────────────────────────────────────────
def test_fx_bounded_and_reset():
    F.reset_all()          # buang state subtes sebelumnya
    boss = make_boss()
    d = F.director_for(boss)
    # spam semua jenis FX
    for i in range(60):
        F.notify_projectile_cast(boss, boss.x, boss.y)
        F.notify_skill_cast(boss, ("q", "w", "e", "r")[i % 4])
        F.notify_skill_impact(boss, boss.x + i, boss.y, 50,
                              ("q", "w", "e", "r")[i % 4])
        F.notify_hurt(boss)
    assert d.particles.count() <= F.MAX_PARTICLES
    assert d.projectiles.count() <= F.MAX_PROJECTILES
    assert len(d.skills) <= F.MAX_SKILLS
    assert len(d.impacts) <= F.MAX_IMPACTS
    # majoru waktu sampai semua mati
    for _ in range(1200):
        F.tick(1.0 / 60.0)
    assert F.total_particles() == 0, "partikel tidak pernah habis"
    assert d.projectiles.count() == 0, "proyektil tidak pernah habis"
    F.reset_all()
    assert F.total_particles() == 0 and not F.owns(boss)
    print("   cap partikel/proyektil/skill/impact + reset bersih")


if __name__ == "__main__":
    test_module_api()
    print("PASS API modul lengkap")
    test_palette_contract()
    print("PASS palette kontrak 9 kunci")
    test_anim_controller()
    print("PASS animation controller (state/fase/hit window/dt)")
    test_staff_arc()
    print("PASS staff arc kontinu + sinkron renderer<->FX")
    test_projectiles_lifecycle()
    print("PASS proyektil spawn->travel->hit->destroy (bolt + orb)")
    test_projectile_cap()
    print("PASS batas keras proyektil")
    test_skill_lifecycle_and_dedup()
    print("PASS skill FX lifecycle + dedup cast/impact")
    test_renderer_with_live_fx()
    print("PASS renderer + lapisan hidup (boss lane)")
    test_renderer_all_states()
    print("PASS renderer semua pose (idle/walk/hurt/attack/cast)")
    test_hero_lane_pipeline()
    print("PASS hero-lane pipeline (render_hero + attach)")
    test_base_boss_integration()
    print("PASS integrasi base_boss + level3 bridge")
    test_registry()
    print("PASS registrasi heroes/__init__")
    test_procedural_only()
    print("PASS prosedural murni (tanpa image.load)")
    test_fx_bounded_and_reset()
    print("PASS tidak ada FX hidup tanpa batas")
    print("ALL VARKUL V3 COMBAT TESTS PASSED")
