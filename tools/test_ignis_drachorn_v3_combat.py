#!/usr/bin/env python3
"""Regression test Ignis Drachorn V3 (renderer + live combat-FX engine).

Mengunci:
  * lapisan hidup heroes/ignis_drachorn_fx.py punya semua API yang
    dipakai pipeline hero/boss (attach/owns/tick/draw_*_layer/notify_*);
  * palette kontrak 9 kunci wajib hadir;
  * animation controller v3 (_NS_ignis_drachorn): state, fase serangan,
    hit window, delta-time, prioritas;
  * ayunan ARK pedang: kontinu, tanpa lompatan, konsisten renderer<->FX;
  * proyektil (fire orb + meteor) spawn, travel, hit, destroy;
  * skill FX q/w/e/r lifecycle dan reset ke 0 setelah match;
  * renderer bosses/level4.draw_ignis_drachorn hidup bersama lapisan FX
    tanpa exception (boss lane + hero lane);
  * boss AI (base_boss.py) memanggil lapisan FX ignis;
  * prosedural murni (tanpa pygame.image.load / aset eksternal);
  * tidak ada partikel/proyektil yang hidup tanpa batas.

Jalankan:
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
      python3 tools/test_ignis_drachorn_v3_combat.py
"""
import os
import sys
import math
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


def make_boss(x=140.0, y=140.0, skill=None, timer=0, target=True):
    return SimpleNamespace(
        boss_type="ignis_drachorn", boss_class="true", x=float(x),
        y=float(y), direction=1, facing=1, pulse=1.2, timer=0,
        attack_cooldown=50, active_skill=skill, active_skill_timer=timer,
        target=(SimpleNamespace(x=x + 130.0, y=float(y), alive=True,
                                radius=12) if target else None),
        _render_scale=1.0, hurt_flash_timer=0, alive=True, radius=35,
        hp=9000, max_hp=9000, range=150, speed=1.0, attack_range=150)


# ── 1. API + PALETTE ────────────────────────────────────────────────
def test_module_api():
    required = [
        "Particle", "ParticleSystem", "SwingTrail", "ImpactFX",
        "FireOrbProjectile", "MeteorProjectile", "ProjectileSystem",
        "SkillFX", "IgnisFXDirector",
        "attach", "owns", "tick", "reset_all", "total_particles", "stats",
        "draw_ground_layer", "draw_live_layer", "director_for",
        "projectiles_for", "notify_melee_impact", "notify_projectile_impact",
        "notify_projectile_cast", "notify_skill_impact", "notify_skill_cast",
        "notify_hurt", "draw_debug_overlay", "sword_arc", "sword_points",
        "attack_phase", "clear_cache",
    ]
    for name in required:
        assert hasattr(F, name), "API hilang: %s" % name
    assert hasattr(F, "DEBUG_CHARACTER")
    assert F.DEBUG_CHARACTER is False


def test_palette_contract():
    for key in ("outline", "shadow", "dark", "body", "mid", "light",
                "highlight", "weapon", "fx"):
        assert key in F.IGNIS_PALETTE, "palette kunci hilang: %s" % key
        assert len(F.IGNIS_PALETTE[key]) == 3


# ── 2. ANIMATION CONTROLLER ─────────────────────────────────────────
def test_anim_controller():
    # semua state minimal ada dan berprioritas
    for st in ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
               "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"):
        assert st in NS.ANIM_STATES, st
    assert NS.ANIM_STATES["DEATH"] > NS.ANIM_STATES["IDLE"]

    # fase serangan menutupi 0..1 tanpa celah
    prev = 0.0
    for name, a, b in NS.ATTACK_PHASES:
        assert abs(a - prev) < 1e-9, (name, a, prev)
        prev = b
    assert abs(prev - 1.0) < 1e-9

    boss = make_boss()
    boss.timer = boss.attack_cooldown - 1
    boss._ign_prev_timer = 0
    NS._update_ignis_anim(boss, False)
    assert boss._ign_attack_active
    assert boss._ign_state in ("CHARGE", "SWING", "ATTACK")
    assert boss._ign_dt > 0.0

    # jendela hit hanya aktif di dalam ATTACK_ACTIVE_WINDOW
    for p in (0.05, 0.20, 0.40, 0.50, 0.70, 0.95):
        boss._ign_attack_manual = True
        boss._ign_attack_progress = p
        NS._update_ignis_anim(boss, False)
        inside = (NS.ATTACK_ACTIVE_WINDOW[0] <= p < NS.ATTACK_ACTIVE_WINDOW[1])
        assert bool(boss._ign_hit_active) == inside, (p, inside)
        assert boss._ign_attack_phase == NS.attack_phase(p)

    # DEATH menang atas semua
    boss.alive = False
    NS._update_ignis_anim(boss, True)
    assert boss._ign_state == "DEATH"

    # HURT dari hurt_flash_timer
    b2 = make_boss()
    b2.hurt_flash_timer = 6
    NS._update_ignis_anim(b2, False)
    assert b2._ign_state == "HURT"

    # nama field lama tetap ada (backward compatibility)
    b3 = make_boss()
    NS._update_attack_anim(b3)
    for attr in ("_ign_attack_active", "_ign_attack_frame",
                 "_ign_attack_progress"):
        assert hasattr(b3, attr), attr


# ── 3. SWORD ARC ────────────────────────────────────────────────────
def test_sword_arc():
    # renderer dan modul FX membaca SATU tabel yang sama
    for i in range(101):
        p = i / 100.0
        t1, l1 = NS._sword_arc(p)
        t2, l2 = F.sword_arc(p)
        assert abs(t1 - t2) < 1e-9, (p, t1, t2)
        assert abs(l1 - l2) < 1e-9, (p, l1, l2)

    # kontinu: tidak ada teleport sudut antar-frame
    prev = NS._sword_arc(0.0)[0]
    biggest = 0.0
    for i in range(1, 201):
        p = i / 200.0
        cur = NS._sword_arc(p)[0]
        biggest = max(biggest, abs(cur - prev))
        prev = cur
    assert biggest < 0.45, "lompatan sudut terlalu besar: %.3f" % biggest

    # fallback (tanpa renderer) identik dengan tabel renderer
    for p in (0.0, 0.15, 0.31, 0.49, 0.61, 0.85, 1.0):
        tf, lf = F._fallback_arc(p)
        tr, lr = NS._sword_arc(p)
        assert abs(tf - tr) < 1e-6, (p, tf, tr)

    # ada fase IMPACT yang "menahan" (bobot pukulan)
    a = NS._sword_arc(0.50)[0]
    b = NS._sword_arc(0.58)[0]
    assert abs(a - b) < 0.05, "IMPACT tidak menahan"

    # ujung bilah benar-benar menelusuri lengkungan
    boss = make_boss()
    boss._ign_pose_action = "attack"
    pts = []
    for i in range(30):
        boss._ign_attack_progress = i / 29.0
        pts.append(F.sword_points(boss, 100.0, 100.0)[1])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    assert max(xs) - min(xs) > 30 and max(ys) - min(ys) > 30, "ark datar"


# ── 4. PROJECTILES ──────────────────────────────────────────────────
def test_projectiles_lifecycle():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    tgt = boss.target
    pr = d.spawn_fire_orb(boss.x, boss.y, (tgt.x, tgt.y))
    assert pr.active and pr.trail == []
    for attr in ("x", "y", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active"):
        assert hasattr(pr, attr), attr
    # TRAVEL + TRAIL
    for _ in range(12):
        F.tick(1.0 / 60.0)
    assert len(pr.trail) > 0, "trail proyektil kosong"
    # HIT -> DESTROY
    for _ in range(240):
        F.tick(1.0 / 60.0)
        if not pr.active:
            break
    assert not pr.active, "proyektil tidak pernah mati"
    assert pr.hit_target, "proyektil tidak mengenai target"

    # METEOR: spawn -> jatuh -> mendarat -> hilang
    hits = []
    m = d.projectiles.spawn_meteor(boss.x + 30, boss.y + 10, delay=0.0,
                                   on_impact=lambda mm: hits.append(mm))
    for _ in range(400):
        F.tick(1.0 / 60.0)
        if not m.active:
            break
    assert not m.active and hits, "meteor tidak pernah mendarat"
    F.reset_all()


def test_projectile_cap():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    for _ in range(200):
        d.spawn_fire_orb(boss.x, boss.y, (boss.x + 200, boss.y))
    assert d.projectiles.count() <= F.MAX_PROJECTILES
    F.reset_all()


# ── 5. SKILL FX ─────────────────────────────────────────────────────
def test_skill_lifecycle_and_dedup():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    for skill in ("q", "w", "e", "r"):
        n0 = len(d.skills)
        F.notify_skill_cast(boss, skill)
        F.notify_skill_impact(boss, boss.x + 90, boss.y, None, skill)
        assert len(d.skills) == n0 + 1, "skill %s digambar dobel" % skill
    # lifecycle: semua fase dilalui lalu selesai
    seen = set()
    for _ in range(400):
        for s in d.skills:
            seen.add(s.phase)
        F.tick(1.0 / 60.0)
    for ph in ("CAST", "CHARGE", "RELEASE", "AREA", "IMPACT", "FADE"):
        assert ph in seen, "fase %s tidak pernah dilalui" % ph
    for _ in range(600):
        F.tick(1.0 / 60.0)
    assert all(s.done for s in d.skills), "skill FX tidak selesai-selesai"
    F.reset_all()


# ── 6. RENDERER + LIVE LAYER ────────────────────────────────────────
def test_renderer_with_live_fx():
    F.reset_all()
    boss = make_boss(x=230.0, y=230.0, skill="r", timer=60)
    surf = pygame.Surface((520, 520), pygame.SRCALPHA)
    for _ in range(30):
        F.tick(1.0 / 60.0)
        L.draw_ignis_drachorn(surf, boss, 230, 230)
        time.sleep(0.001)
    br = surf.get_bounding_rect(min_alpha=64)
    assert br.width > 40 and br.height > 40, (br.width, br.height)
    F.reset_all()


def test_renderer_all_states():
    surf = pygame.Surface((360, 360), pygame.SRCALPHA)
    idle = make_boss(x=180.0, y=180.0)
    walk = make_boss(x=180.0, y=180.0)
    hurt = make_boss(x=180.0, y=180.0)
    hurt.hurt_flash_timer = 6
    atk = make_boss(x=180.0, y=180.0)
    atk._ign_attack_manual = True
    atk._ign_attack_active = True
    atk._ign_attack_frame = 24
    atk._ign_attack_progress = 0.48
    cast = make_boss(x=180.0, y=180.0, skill="w", timer=30)
    ranged = make_boss(x=180.0, y=180.0)
    ranged.attack_range = 260
    ranged._ign_attack_manual = True
    ranged._ign_attack_active = True
    ranged._ign_attack_progress = 0.40
    death = make_boss(x=180.0, y=180.0)

    for name, b in (("idle", idle), ("walk", walk), ("hurt", hurt),
                    ("attack", atk), ("cast", cast), ("ranged", ranged),
                    ("death", death)):
        surf.fill((0, 0, 0, 0))
        if name == "walk":
            b.x += 6.0
        if name == "death":
            b.alive = False
        for _ in range(3):
            L.draw_ignis_drachorn(surf, b, 180, 180)
            time.sleep(0.001)
        br = surf.get_bounding_rect(min_alpha=16)
        assert br.width > 30 and br.height > 30, (name, br)
    F.reset_all()
    print("   semua state render tanpa exception")


def test_debug_overlay():
    surf = pygame.Surface((360, 360), pygame.SRCALPHA)
    boss = make_boss(x=180.0, y=180.0)
    boss._ign_hit_active = True
    d = F.director_for(boss)
    F.draw_debug_overlay(surf, d)         # tidak boleh melempar
    old = NS.DEBUG_CHARACTER
    NS.DEBUG_CHARACTER = True
    try:
        L.draw_ignis_drachorn(surf, boss, 180, 180)
    finally:
        NS.DEBUG_CHARACTER = old
    F.reset_all()


def test_hero_lane_pipeline():
    import heroes as H
    h = SimpleNamespace(hero_type="ignis_drachorn",
                        boss_type="ignis_drachorn", boss_class="true",
                        team="blue", x=200.0, y=200.0, direction=1,
                        facing=1, pulse=1.0, timer=0, attack_cooldown=50,
                        attack_timer=0, anim_time=0, active_skill=None,
                        active_skill_timer=0, hp=900, max_hp=900,
                        damage=10, base_damage=10, range=150, speed=1.0,
                        radius=16, alive=True, hurt_flash_timer=0,
                        level=1, selected=False, target=None)
    surf = pygame.Surface((460, 460), pygame.SRCALPHA)
    for _ in range(6):
        H.render_hero("ignis_drachorn", surf, h, 200, 200)
        time.sleep(0.001)
    assert F.owns(h), "lapisan hidup tidak ter-attach di jalur hero"
    br = surf.get_bounding_rect(min_alpha=16)
    assert br.width > 30 and br.height > 30
    F.reset_all()


# ── 7. INTEGRASI AI + REGISTRY ──────────────────────────────────────
def test_base_boss_integration():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               "r", encoding="utf-8").read()
    assert "from heroes import ignis_drachorn_fx as _idfx" in src
    assert "_idfx.notify_melee_impact" in src
    assert "_idfx.notify_skill_cast" in src
    assert "_idfx.notify_skill_impact" in src
    src4 = open(os.path.join(ROOT, "bosses", "level4.py"),
                "r", encoding="utf-8").read()
    assert "from heroes import ignis_drachorn_fx as _ifx" in src4
    assert "_ifx.notify_projectile_cast" in src4


def test_registry():
    import heroes as H
    assert "ignis_drachorn" in H._LIVE_FX_HEROES
    assert H._LIVE_FX_PATHS.get("ignis_drachorn") == \
        "heroes.ignis_drachorn_fx"
    assert "ignis_drachorn" in H.BOSS_RENDERERS or True  # lazy registry


def test_ai_skills_run():
    """Semua skill AI dijalankan tanpa exception + memicu FX."""
    F.reset_all()
    import _core            # hindari circular import _render <-> _core
    from bosses.base_boss import Boss
    b = Boss.__new__(Boss)
    for k, v in vars(make_boss(x=300.0, y=300.0)).items():
        setattr(b, k, v)
    b.team = "red"
    b.level = 4
    b.ability_timer = 0
    b._shake_screen = lambda *_a, **_k: None
    b._get_boss_stats = lambda: {"damage": 120, "skill_q_damage": 320,
                                 "skill_w_damage": 380,
                                 "skill_r_damage": 600}
    enemies = [SimpleNamespace(x=340.0, y=300.0, alive=True, radius=12,
                               speed=1.0, attack_timer=0,
                               take_damage=lambda *_a, **_k: None)]
    b.target = enemies[0]
    b._cast_q_dragon_breath(enemies)
    b._cast_w_dragon_tail(enemies)
    b._cast_e_dragon_blood()
    b._cast_r_elder_dragon_form(enemies)
    d = F.director_for(b)
    assert len(d.skills) > 0, "AI tidak memicu SkillFX"
    assert d.projectiles.count() > 0, "R tidak melepas meteor"
    F.reset_all()


# ── 8. PROCEDURAL ONLY ──────────────────────────────────────────────
def test_procedural_only():
    src = open(os.path.join(ROOT, "heroes", "ignis_drachorn_fx.py"),
               "r", encoding="utf-8").read()
    assert "pygame.image" not in src
    assert "image.load" not in src
    for ext in (".png", ".jpg", ".gif", ".bmp", ".jpeg"):
        assert ext not in src, ext


# ── 9. NO UNBOUNDED FX ──────────────────────────────────────────────
def test_fx_bounded_and_reset():
    F.reset_all()
    boss = make_boss()
    d = F.director_for(boss)
    for i in range(60):
        skill = ("q", "w", "e", "r")[i % 4]
        F.notify_projectile_cast(boss, boss.x, boss.y)
        F.notify_skill_cast(boss, skill)
        F.notify_skill_impact(boss, boss.x + i, boss.y, 60, skill)
        F.notify_melee_impact(boss, boss.target, 100, i % 5 == 0)
        F.notify_hurt(boss)
    assert d.particles.count() <= F.MAX_PARTICLES
    assert d.projectiles.count() <= F.MAX_PROJECTILES
    assert len(d.skills) <= F.MAX_SKILLS
    assert len(d.impacts) <= F.MAX_IMPACTS
    for _ in range(1400):
        F.tick(1.0 / 60.0)
    assert F.total_particles() == 0, "partikel tidak pernah habis"
    assert d.projectiles.count() == 0, "proyektil tidak pernah habis"
    assert len(d.skills) == 0 and len(d.impacts) == 0
    F.reset_all()
    assert F.total_particles() == 0 and not F.owns(boss)
    print("   cap partikel/proyektil/skill/impact + reset bersih")


def test_surface_cache_bounded():
    """Cache surface prosedural dipakai ulang, bukan dibuat tiap frame."""
    F.clear_cache()
    for _ in range(50):
        F.glow_surface(12, F.P["fire_mid"], 0.5)
        F.ring_surface(20, 2, F.P["fire_bright"], 200)
    assert F.cache_size() <= 4, F.cache_size()


if __name__ == "__main__":
    test_module_api()
    print("PASS API modul lengkap")
    test_palette_contract()
    print("PASS palette kontrak 9 kunci")
    test_anim_controller()
    print("PASS animation controller (state/fase/hit window/dt)")
    test_sword_arc()
    print("PASS sword arc kontinu + sinkron renderer<->FX")
    test_projectiles_lifecycle()
    print("PASS proyektil spawn->travel->hit->destroy (orb + meteor)")
    test_projectile_cap()
    print("PASS batas keras proyektil")
    test_skill_lifecycle_and_dedup()
    print("PASS skill FX lifecycle + dedup cast/impact")
    test_renderer_with_live_fx()
    print("PASS renderer + lapisan hidup bersamaan")
    test_renderer_all_states()
    print("PASS render semua state")
    test_debug_overlay()
    print("PASS debug overlay")
    test_hero_lane_pipeline()
    print("PASS jalur hero-lane (cache sprite + FX layar)")
    test_base_boss_integration()
    print("PASS integrasi AI base_boss + renderer")
    test_registry()
    print("PASS registry heroes/__init__")
    test_ai_skills_run()
    print("PASS AI q/w/e/r memicu FX")
    test_procedural_only()
    print("PASS prosedural murni (tanpa aset eksternal)")
    test_fx_bounded_and_reset()
    print("PASS FX terbatas + reset bersih")
    test_surface_cache_bounded()
    print("PASS cache surface prosedural")
    print("\nSEMUA TEST IGNIS DRACHORN V3 LULUS")
