#!/usr/bin/env python3
"""Regresi visual untuk Sylara Procedural Masterwork v2.

Memastikan upgrade tidak kembali menjadi kumpulan body-part statis:
rig tunggal ~1.52x (telapak y=+61, puncak hood y=-76), busur recurve
pose-driven (wind-up -> IMPACT release -> recover), 7-keyframe attack,
portrait LOD, skill Q/W/E/R world-space, dan pose (idle/walk/attack/
windrun) semuanya dirender dari kode tanpa PNG / sprite sheet /
image.load.

Jalankan:  python3 tools/test_sylara_masterwork.py
"""
import inspect
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from heroes import _ProbeEntity
from heroes._bundle import _NS_sylara as S


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(attack=False):
    surface = pygame.Surface((320, 320), pygame.SRCALPHA)
    hero = _ProbeEntity("sylara", 160, 165)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if attack:
        hero._sy_attack_progress = .52
        hero._sy_attack_active = True
        hero.range = 220
        S._draw_sylara_attack(surface, hero, 160, 165)
    else:
        S._draw_sylara_idle(surface, hero, 160, 165)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(S)
    assert "pygame.image.load" not in source
    assert callable(S._draw_sylara_elite)
    assert callable(S._draw_sylara_rig)
    assert callable(S._draw_elite_bow)
    assert callable(S._draw_elite_arrow)
    assert callable(S._draw_sylara_masterwork_details)
    assert callable(S._attack_pose)
    assert callable(S._dither_dots)
    assert abs(S.RIG_SCALE - 1.52) < 1e-6
    # V2.1 shared FX vocabulary stays available for renderer audits.
    for helper in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
                   "_jagged_crack", "_tuft_points", "_static", "_mix",
                   "_hash01"):
        assert callable(getattr(S, helper)), helper
    # rig lama (torso/quiver/hood terpisah) sudah dihapus, bukan disisakan
    assert not hasattr(S, "_draw_head_hood")
    assert not hasattr(S, "_draw_idle_arms")
    assert not hasattr(S, "_draw_bow_idle")


def test_material_details_and_pose():
    idle = render_pose(False)
    attack = render_pose(True)
    palette = colors(idle)

    # Exact material swatches prove these layers reached the final render.
    assert S.PALETTE["gold_light"] in palette        # gesper sabuk
    assert S.PALETTE["gold_shine"] in palette        # kilau gesper
    assert S.PALETTE["hair_shine"] in palette        # kilau rambut
    assert S.PALETTE["hair_high"] in palette         # specular rambut
    assert S.PALETTE["leather_light"] in palette     # boot / sarung tangan
    assert S.PALETTE["leather_high"] in palette      # highlight boot
    assert S.PALETTE["eye_iris_light"] in palette    # mata hijau
    assert S.PALETTE["string_shine"] in palette      # tali busur
    assert S.PALETTE["cloak_high"] in palette        # rim cape
    assert S.PALETTE["leaf_gold"] in palette         # daun idle

    rect = idle.get_bounding_rect(min_alpha=8)
    # Rig v2 ~1.52x: telapak +61, hood ke -76 -> bbox jauh lebih tinggi.
    assert rect.height >= 130 and rect.width >= 70, (rect.width, rect.height)
    # Telapak depan menapak di y=+61 (sol boot, anchor 165).
    foot = idle.get_at((160 + int(9 * S.RIG_SCALE), 165 + int(40 * S.RIG_SCALE)))
    assert foot.a > 150, f"telapak harus menapak di +61, alpha={foot.a}"
    # Mata / hood ada di zona kepala (y sekitar -76..-45).
    eye = any(idle.get_at((160 + dx, 165 + dy)).a > 150
              for dx in range(0, 24) for dy in range(-80, -45))
    assert eye, "mata/hood tidak ada di posisi kepala"
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(attack, "RGBA")


def test_bow_geometry_is_pose_driven():
    """Nock bergerak mundur mengikuti tarikan; busur bukan sticker."""
    rest = S._bow_nock((16, -6), .2, 0.0)
    drawn = S._bow_nock((16, -6), .2, 1.0)
    assert drawn[0] < rest[0] - 8

    slack = pygame.Surface((200, 200), pygame.SRCALPHA)
    taut = pygame.Surface((200, 200), pygame.SRCALPHA)
    S._draw_elite_bow(slack, lambda dx, dy: (int(100 + dx), int(100 + dy)),
                      1, (16, -6), .2, 0.0, 1.0)
    S._draw_elite_bow(taut, lambda dx, dy: (int(100 + dx), int(100 + dy)),
                      1, (16, -6), .2, 1.0, 1.0)
    assert pygame.image.tobytes(slack, "RGBA") != pygame.image.tobytes(taut, "RGBA")
    # anak panah hanya muncul saat tali ditarik
    assert S.PALETTE["arrow_feather"] in colors(taut)
    assert S.PALETTE["arrow_feather"] not in colors(slack)

    # 7-keyframe: wind-up mundur, IMPACT lean maju.
    windup = S._attack_pose(0.20)
    impact = S._attack_pose(0.52)
    restp = S._attack_pose(0.00)
    recov = S._attack_pose(1.00)
    assert windup["lean"] < restp["lean"]
    assert impact["lean"] > restp["lean"] + 4
    assert impact["flare"] > 1.15
    assert recov["bob"] == restp["bob"] and recov["lean"] == restp["lean"]


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((280, 280), pygame.SRCALPHA)
    portrait = pygame.Surface((280, 280), pygame.SRCALPHA)
    S._draw_sylara_elite(normal, 140, 140, 1, .8, "idle", 0.0, detail=False)
    S._draw_sylara_elite(portrait, 140, 140, 1, .8, "idle", 0.0, detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack harus mengubah sendi dan siluet, bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((280, 280), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 140, 140, 1, i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(10):
        surface = pygame.Surface((300, 280), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 150, 140, 1, i * .3, "attack", i / 9.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) >= 9, f"attack 7-keyframe hanya {len(attacks)} pose unik"

    # windrun adalah pose tersendiri, bukan idle yang digeser
    idle = pygame.Surface((280, 280), pygame.SRCALPHA)
    dash = pygame.Surface((280, 280), pygame.SRCALPHA)
    S._draw_sylara_elite(idle, 140, 140, 1, 1.2, "idle", 0.0)
    S._draw_sylara_elite(dash, 140, 140, 1, 1.2, "windrun", 0.0)
    assert pygame.image.tobytes(idle, "RGBA") != pygame.image.tobytes(dash, "RGBA")


def test_silhouette_outline_exists():
    """Outline gelap 1 px ala sprite referensi membungkus rig."""
    surface = pygame.Surface((280, 280), pygame.SRCALPHA)
    S._draw_sylara_elite(surface, 140, 140, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark > 60


def test_has_worldspace_skill_fx_helpers():
    """Helper FX world-space v2.1 ada di namespace sylara."""
    for name in ("_fx_scale", "_ring_r", "_spark_star", "_chevron",
                 "_dashed_ring", "_jagged_crack", "_tuft_points",
                 "_static", "_dither_dots", "SKILL_VISUAL_DURATION"):
        assert callable(getattr(S, name, None)) or name == "SKILL_VISUAL_DURATION", name
    assert S.SKILL_VISUAL_DURATION == {"q": 180, "w": 180, "e": 150, "r": 60}
    # kompensasi: fs = 1/_render_scale (cap 2.6)
    h = _ProbeEntity("sylara", 120, 125)
    assert S._fx_scale(h) == 1.0
    h._render_scale = 0.5
    assert S._fx_scale(h) == 2.0
    h._render_scale = 0.2
    assert S._fx_scale(h) == 2.6
    h._render_scale = 0.1
    assert S._fx_scale(h) == 2.6


def _render_skill(skill, timer, fs=None, size=760):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    hero = _ProbeEntity("sylara", size // 2, size // 2 + 40)
    hero.pulse = 1.3
    hero.direction = hero.facing = 1
    hero.active_skill = skill
    hero.active_skill_timer = timer
    hero.range = 220
    hero.skill_range = 200 if skill == "q" else 70
    hero.target = _ProbeEntity("dummy", size // 2 + 140, size // 2)
    hero.target.alive = True
    if fs:
        hero._render_scale = fs
    S.draw_sylara(surf, hero, size // 2, size // 2 + 40)
    return surf


def _count(surface, matcher, rmin, rmax, cx=None, cy=None):
    cx = surface.get_width() // 2 if cx is None else cx
    cy = surface.get_height() // 2 + 40 if cy is None else cy
    n = 0
    for y in range(0, surface.get_height(), 2):
        for x in range(0, surface.get_width(), 2):
            r = math.hypot(x - cx, y - cy)
            if rmin <= r <= rmax:
                c = surface.get_at((x, y))
                if c.a > 100 and matcher(c):
                    n += 1
    return n


def test_skill_fx_worldspace_and_3phase():
    """FX skill keluar dari siluet badan & kompensasi _render_scale."""
    _wind = lambda c: c[1] > 110 and c[1] > c[0] and c[1] > c[2]

    # Unscaled (fs=1): ring windrun di ~70 canvas px dari pusat.
    s0 = _render_skill("w", 90, fs=None, size=760)
    # Scaled (fs=0.5): ring harus MENGEMBANG ke ~140 canvas px.
    s1 = _render_skill("w", 90, fs=0.5, size=760)

    near0 = _count(s0, _wind, 55, 85)
    near1 = _count(s1, _wind, 55, 85)
    far1 = _count(s1, _wind, 95, 160)
    assert far1 > 30, f"ring world-space tidak mengembang (far={far1})"
    assert far1 > near1 * .4, f"kompensasi tak cukup (far={far1}, near={near1})"

    # W ring tepat di radius dunia 70 (canvas 140 saat fs=0.5).
    def hits_at_radius(surf, r_px, cx, cy, tol=4):
        n = 0
        for a in range(0, 360, 2):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            for dr in range(-tol, tol + 1):
                x = int(cx + ca * (r_px + dr))
                y = int(cy + sa * (r_px + dr))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and surf.get_at((x, y)).a > 30:
                    n += 1
                    break
        return n

    n = hits_at_radius(s1, 140, 380, 420 + 14)
    assert n > 80, f"W: ring 70 dunia tidak world-space ({n}/180)"

    # R Powershot: orb/cahaya hijau aktif di sekitar bow.
    s2 = _render_skill("r", 30, size=760)
    assert _count(s2, _wind, 20, 90) > 30, "powershot charge aura hilang"

    # Q Focus Fire: ring AOE jangkauan hadir di luar badan.
    s3 = _render_skill("q", 90, size=760)
    assert _count(s3, _wind, 55, 160) > 40, "focus fire ground ring hilang"

    # 3 tahap FX berbeda per skill.
    for skill, dur in S.SKILL_VISUAL_DURATION.items():
        sigs = set()
        for timer in (dur - 4, int(dur * 0.55), 8):
            surf = _render_skill(skill, timer, size=620)
            sigs.add(pygame.image.tobytes(surf, "RGBA"))
        assert len(sigs) == 3, f"sylara {skill}: hanya {len(sigs)}/3 tahap FX"


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe."""
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 100), ("w", 90), ("e", 80), ("r", 30)):
        hero = _ProbeEntity("sylara", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.range = 220
        hero.target = _ProbeEntity("dummy", 260, 152)
        hero.target.alive = True
        surface = pygame.Surface((360, 300), pygame.SRCALPHA)
        render_hero("sylara", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 35 and rect.height > 35, skill


def test_body_reacts_to_skill_state():
    """Badan berubah saat skill aktif (bukan sekadar sticker FX)."""
    base = pygame.Surface((320, 320), pygame.SRCALPHA)
    focus = pygame.Surface((320, 320), pygame.SRCALPHA)
    wind = pygame.Surface((320, 320), pygame.SRCALPHA)
    S._draw_sylara_elite(base, 160, 160, 1, 1.2, "idle", 0.0)
    S._draw_sylara_elite(focus, 160, 160, 1, 1.2, "idle", 0.0, focus=True)
    S._draw_sylara_elite(wind, 160, 160, 1, 1.2, "idle", 0.0, wind=True)
    assert pygame.image.tobytes(base, "RGBA") != pygame.image.tobytes(focus, "RGBA")
    assert pygame.image.tobytes(base, "RGBA") != pygame.image.tobytes(wind, "RGBA")


def test_keeps_public_names():
    """Upgrade v2 tidak boleh memutus nama publik lama _NS_sylara."""
    legacy = (
        "PALETTE", "draw_sylara", "draw_boss",
        "_draw_sylara_idle", "_draw_sylara_walk", "_draw_sylara_attack",
        "_draw_sylara_windrun", "_draw_sylara_body", "_draw_sylara_rig",
        "_draw_sylara_elite", "_draw_sylara_masterwork_details",
        "_draw_elite_bow", "_draw_elite_arrow", "_bow_frame", "_bow_point",
        "_bow_nock", "_draw_bow_release_flash", "_draw_powershot_charge",
        "_draw_windrun_ground", "_draw_windrun_trail",
        "_draw_shackle_ground", "_draw_focus_fire_ground",
        "_draw_focus_fire_effect", "_draw_wind_aura", "_draw_wind_platform",
        "_draw_ranger_silhouette_glow", "_draw_floating_wind", "_draw_leaf",
        "_draw_shadow", "_manage_projectiles", "_spawn_arrow",
        "_spawn_shackle", "_spawn_focus_fire_volley", "_detect_moving",
        "_update_attack_anim", "_world_to_local", "_target_position",
        "WindArrowProjectile", "ShackleProjectile",
        "RIG_W", "RIG_H", "RIG_OX", "RIG_OY", "HAS_AACIRCLE",
        "SKILL_VISUAL_DURATION", "RIG_SCALE",
    )
    missing = [n for n in legacy if not hasattr(S, n)]
    assert not missing, f"sylara: nama publik hilang -> {missing}"


def test_skill_fx_are_sylara_not_thorne():
    """Skill FX memakai kosakata ranger, bukan rune/retakan/X-slash Thorne."""
    import inspect as _ins
    for name in ("_draw_focus_fire_ground", "_draw_focus_fire_effect",
                 "_draw_windrun_ground", "_draw_windrun_trail",
                 "_draw_shackle_ground", "_draw_powershot_charge",
                 "_draw_bow_release_flash"):
        src = _ins.getsource(getattr(S, name))
        for banned in ("_drk_rune_ring", "_drk_cracks", "_drk_crescent",
                       "_drk_shock", "_drk_orb", "_jagged_crack"):
            assert banned not in src, f"{name} masih meniru {banned}"
        assert "_sy_" in src or name == "_draw_bow_release_flash"


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_bow_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_silhouette_outline_exists()
    test_has_worldspace_skill_fx_helpers()
    test_skill_fx_worldspace_and_3phase()
    test_skill_visuals_render_with_masterwork()
    test_body_reacts_to_skill_state()
    test_keeps_public_names()
    test_skill_fx_are_sylara_not_thorne()
    print("OK - Sylara masterwork v2: rig 1.52x, busur pose, 7-keyframe IMPACT, "
          "portrait LOD, Q/W/E/R world-space khas ranger, outline, animasi")
