#!/usr/bin/env python3
"""Regresi visual untuk Vex Procedural Masterwork (versi V1 pixel-art).

Sejak rewrite V1 (heroes/vex_v1.py, pola Kaizen V1) rig masterwork bone-2D
digantikan sprite chibi pixel-art 48x48 @2.6x: hood + wajah shadow + mata
void, mahkota obsidian, jubah robek mengambang, dan staff dengan orb arcane
besar yang pose-driven.  Kontrak yang tetap dikunci di sini:

- 100% prosedural (tanpa PNG / sprite-sheet / image.load).
- Identitas material Vex lolos ke render akhir (swatch palette).
- Geometri staff pose-driven (jembatan vex_fx staff_points).
- Pose idle/walk/attack/skill/death semuanya animasi (bukan sticker).
- Skill FX world-space dengan kompensasi _render_scale.
- Namespace lama tetap warisan API (legacy callables resolve).

Jalankan:  python3 tools/test_vex_masterwork.py
"""
import inspect
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_vex as V

# Namespace vex sekarang subclass V1 dari namespace legacy: helper lama
# tetap resolve lewat pewarisan, jalur gambar digantikan V1.
from heroes.vex_v1 import install as _install_v1

_V1_CLS = V.__mro__[1] if len(V.__mro__) > 1 else V


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(action="idle", progress=0.0):
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    hero = _ProbeEntity("vex", 130, 140)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if action == "attack":
        hero._vx_attack_progress = progress
        V._draw_vex_attack(surface, hero, 130, 140)
    elif action == "walk":
        V._draw_vex_walk(surface, hero, 130, 140)
    else:
        V._draw_vex_idle(surface, hero, 130, 140)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(V)
    assert "pygame.image.load" not in source
    # Jalur gambar V1 (pixel ops + sprite assembler).
    assert callable(V._draw_vex_elite)
    assert callable(V._draw_vex_sprite)
    assert callable(V._make_pixel_ops)
    assert callable(V._draw_pixel_hood)
    assert callable(V._draw_pixel_staff)
    assert callable(V._draw_pixel_cape)
    assert callable(V._draw_pixel_hem)
    # Kontrak geometri + helper yang dikonsumsi lapisan FX hidup.
    assert callable(V._orb_tip_local)
    assert callable(V._staff_orb_position)
    assert callable(V._staff_grip_local)
    assert callable(V._staff_butt_local)
    assert callable(V._fx_scale)
    assert callable(V._ring_r)
    assert callable(V._spark_star)
    assert callable(V._chevron)
    assert callable(V._dashed_ring)
    assert callable(V._jagged_crack)
    assert callable(V._tuft_points)
    assert callable(V._draw_arcane_orb_telegraph)
    assert callable(V._draw_staff_swing_trail)
    # Namespace lama tetap resolve lewat pewarisan (API publik historis).
    assert callable(V._draw_elite_crown)
    assert callable(V._draw_elite_staff)
    assert callable(V._draw_elite_hood)
    assert callable(V._draw_vex_masterwork_details)
    assert callable(V._draw_staff_smear)
    # Skala V1: grid 48x48 pada 2.6x; helper lokal sudah canvas px
    # (RIG_SCALE netral 1.0, bukan 1.52 masterwork lama).
    assert abs(V.PIXEL_SCALE - 2.6) < 1e-9
    assert abs(V.RIG_SCALE - 1.0) < 1e-9
    # Timeline serangan identik dengan rig lama + sinkron vex_fx.
    assert (V.ATTACK_WINDUP_END, V.ATTACK_IMPACT, V.ATTACK_SWING_END) == \
        (0.28, 0.56, 0.66)


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.5)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert V.PALETTE["void_mid"] in palette      # hem/clasp glow trims
    assert V.PALETTE["void_light"] in palette    # orb face / crown tip
    assert V.PALETTE["void_hot"] in palette      # orb core / eye core
    assert V.PALETTE["robe_darkest"] in palette  # cape / hood shadow
    assert V.PALETTE["armor_mid"] in palette     # pauldron / hand plate
    assert V.PALETTE["staff_mid"] in palette     # staff shaft mid line
    assert V.PALETTE["crown_tip"] in palette     # bright glow tips

    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 110 and rect.width >= 70, (rect.width, rect.height)
    assert pygame.image.tobytes(idle, "RGBA") != \
        pygame.image.tobytes(attack, "RGBA")


def test_staff_geometry_is_pose_driven():
    """Staff orb pulls back during wind-up then releases forward with the arm."""
    idle_tip = V._orb_tip_local(1.2, "idle", 0.0)
    windup_tip = V._orb_tip_local(1.2, "attack", 0.2)
    release_tip = V._orb_tip_local(1.2, "attack", 0.6)
    # Orb sweeps forward on release: release reaches farther forward (+x).
    assert release_tip[0] > idle_tip[0] + 8
    assert windup_tip[0] < release_tip[0]

    rest = pygame.Surface((240, 240), pygame.SRCALPHA)
    swing = pygame.Surface((240, 240), pygame.SRCALPHA)
    V._draw_vex_elite(rest, 115, 120, 1, 1.0, "idle", 0.0)
    V._draw_vex_elite(swing, 115, 120, 1, 1.0, "attack", 0.6)
    assert pygame.image.tobytes(rest, "RGBA") != \
        pygame.image.tobytes(swing, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((220, 220), pygame.SRCALPHA)
    portrait = pygame.Surface((220, 220), pygame.SRCALPHA)
    V._draw_vex_elite(normal, 110, 110, 1, 1.0, "idle", 0.0, detail=False)
    V._draw_vex_elite(portrait, 110, 110, 1, 1.0, "idle", 0.0, detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack mengubah cape, hem, dan orb - bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((220, 240), pygame.SRCALPHA)
        V._draw_vex_elite(surface, 110, 115, 1,
                          i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) >= 5

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((260, 250), pygame.SRCALPHA)
        V._draw_vex_elite(surface, 120, 115, 1,
                          i * 0.3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe."""
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 35), ("w", 70), ("e", 45), ("r", 60)):
        hero = _ProbeEntity("vex", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 260, 152)
        hero.target.alive = True
        surface = pygame.Surface((420, 360), pygame.SRCALPHA)
        render_hero("vex", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 45 and rect.height > 45, skill


def test_skill_fx_are_world_space():
    """Sanity's Eclipse ground ring tetap terukur world-px via _ring_r."""
    import math as _m

    def render(fs):
        surf = pygame.Surface((760, 760), pygame.SRCALPHA)
        h = _ProbeEntity("vex", 380, 420)
        h.pulse = 1.3
        h.direction = h.facing = 1
        h.active_skill = "w"
        h.active_skill_timer = 50
        h.target = _ProbeEntity("dummy", 520, 420)
        h.target.alive = True
        h._render_scale = fs
        V.draw_vex(surf, h, 380, 420)
        return surf

    def hits_at_radius(surf, r_px):
        hits = 0
        cx, cy = 380, 420 + 44
        for a in range(0, 360, 2):
            x = int(cx + _m.cos(_m.radians(a)) * r_px)
            y = int(cy + _m.sin(_m.radians(a)) * r_px * .5)
            if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                    and surf.get_at((x, y)).a > 40:
                hits += 1
        return hits

    # Ground ring world radius = 55 (renderer world-space), squashed .5
    # seperti arena; ring harus mengikuti kompensasi 1/_render_scale.
    for fs in (1.0, 0.50):
        s = render(fs)
        r_px = int(55 / fs)
        n = hits_at_radius(s, r_px)
        assert n > 40, f"W ring tidak world-space pada fs={fs}: {n}/180"


def test_skill_state_changes_body():
    normal = pygame.Surface((280, 300), pygame.SRCALPHA)
    charged = pygame.Surface((280, 300), pygame.SRCALPHA)
    V._draw_vex_elite(normal, 140, 155, 1, 1.0, "idle", 0.0, False, None)
    V._draw_vex_elite(charged, 140, 155, 1, 1.0, "idle", 0.0, False, "r")
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(charged, "RGBA")


def test_silhouette_outline_exists():
    surface = pygame.Surface((220, 240), pygame.SRCALPHA)
    V._draw_vex_elite(surface, 110, 115, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark >= 30, f"selout siluet hilang ({dark})"


def test_v1_install_layering():
    """install() mengembalikan subclass dari namespace legacy yang diberi."""
    class _FakeLegacy:
        PALETTE = {"legacy_key": (1, 2, 3)}

    wrapped = _install_v1(_FakeLegacy)
    assert issubclass(wrapped, _FakeLegacy)
    assert wrapped.PALETTE["legacy_key"] == (1, 2, 3)
    # Kunci kritis live FX tetap ada meski base minimal.
    for key in ("void_mid", "void_light", "astral_mid", "staff_mid",
                "robe_mid", "armor_darkest"):
        assert key in wrapped.PALETTE


def test_basic_attack_spawn_orb_canvas_fallback():
    """Serangan dasar melepaskan orb arcane bertema hero di rilis ayunan.

    Permintaan owner: "saya mau ada projectile saat melakukan basic
    attack, projectile nya menyesuaikan heronya".  Jalur canvas (fallback
    tanpa FX live) harus spawn ArcaneOrbProjectile teal dari ujung staff
    menuju target — tanpa skill yang aktif sekalipun.
    """
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 240, 120)
    target.alive = True

    hero = _ProbeEntity("vex", 130, 140)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    hero.active_skill = None
    hero.target = target
    hero._vx_proj_spawned = False

    saved = V._FX_LIVE.v
    V._FX_LIVE.v = False          # paksa jalur canvas (tanpa FX live)
    try:
        # Sebelum titik rilis: belum ada orb.
        hero._vx_attack_progress = 0.30
        V._draw_vex_attack(surface, hero, 130, 140)
        assert len(getattr(hero, "_vx_projectiles", [])) == 0

        # Di jendela rilis (ap 0.5-0.6): orb arcane terbang ke target.
        hero._vx_attack_progress = 0.55
        V._draw_vex_attack(surface, hero, 130, 140)
        items = getattr(hero, "_vx_projectiles", [])
        assert len(items) == 1
        orb = items[0]
        assert type(orb) is V.ArcaneOrbProjectile   # teal arcane
        assert orb.target is target

        # Anti-dobel: frame rilis berikutnya tidak menambah orb.
        V._draw_vex_attack(surface, hero, 130, 140)
        assert len(getattr(hero, "_vx_projectiles", [])) == 1

        # Ayunan selesai: kunci rilis dibuka lagi untuk ayunan berikut.
        hero._vx_attack_progress = 0.95
        V._draw_vex_attack(surface, hero, 130, 140)
        assert hero._vx_proj_spawned is False

        # Saat FX live aktif, canvas TIDAK spawn (director pemiliknya).
        hero._vx_projectiles = []
        hero._vx_proj_spawned = False
        hero._vx_attack_progress = 0.55
        V._FX_LIVE.v = True
        V._draw_vex_attack(surface, hero, 130, 140)
        assert len(hero._vx_projectiles) == 0
    finally:
        V._FX_LIVE.v = saved


def test_skill_attack_masih_spawn_orb_saat_fx_live():
    """Skill E tetap melepaskan orb astral walau lapisan FX live aktif."""
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 240, 120)
    target.alive = True

    hero = _ProbeEntity("vex", 130, 140)
    hero.pulse = 1.0
    hero.direction = hero.facing = 1
    hero.active_skill = "e"
    hero.target = target
    hero._vx_proj_spawned = False

    saved = V._FX_LIVE.v
    V._FX_LIVE.v = True
    try:
        hero._vx_attack_progress = 0.55
        V._draw_vex_attack(surface, hero, 130, 140)
        items = getattr(hero, "_vx_projectiles", [])
        assert len(items) == 1
        assert type(items[0]) is V.AstralOrbProjectile   # ungu astral
    finally:
        V._FX_LIVE.v = saved


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_staff_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_skill_visuals_render_with_masterwork()
    test_skill_fx_are_world_space()
    test_skill_state_changes_body()
    test_silhouette_outline_exists()
    test_v1_install_layering()
    test_basic_attack_spawn_orb_canvas_fallback()
    test_skill_attack_masih_spawn_orb_saat_fx_live()
    print("SEMUA TEST VEX V1 MASTERWORK LULUS")
