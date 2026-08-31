#!/usr/bin/env python3
"""Regresi visual untuk Grimjaw Procedural Masterwork v2.

Memastikan upgrade tidak kembali menjadi kumpulan body-part statis:
rig tunggal ~1.5x (telapak y=+70, mane api y=-106), flame blade
pose-driven (wind-up -> smear -> pendaratan), mask putih 5-band
ber-strip darah, portrait LOD, ambient FX ter-cache, skill Q/W/E/R
world-space, dan pose (idle/walk/attack/spin) semuanya dirender dari
kode tanpa PNG / sprite sheet / image.load.

Juga menjaga PARITAS keluarga masterwork: renderer lain yang sudah
di-upgrade ke standar v2 (termasuk Gorath di bosses/level2.py) wajib
punya kosakata FX yang sama - `_fx_scale` dengan cap 2.6, primitif
telegraph (`_spark_star`/`_chevron`/`_dashed_ring`/`_jagged_crack`),
surface statis ter-cache lewat `_static`, dan FX skill world-space.

Jalankan:  python3 tools/test_grimjaw_masterwork.py
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
from heroes._bundle import _NS_grimjaw as G


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(action="idle", progress=0.0):
    surface = pygame.Surface((260, 260), pygame.SRCALPHA)
    hero = _ProbeEntity("grimjaw", 130, 135)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if action == "attack":
        hero._gj_attack_progress = progress
        G._draw_grimjaw_attack(surface, hero, 130, 135)
    elif action == "spin":
        G._draw_grimjaw_body(surface, 130, 135, 1, 1.0, "spin",
                             spin_phase=2.0)
    elif action == "walk":
        G._draw_grimjaw_walk(surface, hero, 130, 135)
    else:
        G._draw_grimjaw_idle(surface, hero, 130, 135)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(G)
    assert "pygame.image.load" not in source
    assert callable(G._draw_grimjaw_elite)
    assert callable(G._draw_elite_flame_blade)
    assert callable(G._draw_elite_mask)
    assert callable(G._draw_elite_flame_mane)
    assert callable(G._draw_grimjaw_masterwork_details)
    assert callable(G._blade_angle)
    assert callable(G._blade_tip_local)
    # V2.1 shared FX vocabulary stays available for renderer audits.
    for helper in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
                   "_jagged_crack", "_tuft_points"):
        assert callable(getattr(G, helper)), helper
    # Body-part lama sudah benar-benar diganti satu rig.
    for old in ("_draw_torso", "_draw_pauldrons", "_draw_head_mask",
                "_draw_hair_back", "_draw_hair_front", "_draw_sword_arm",
                "_draw_left_arm", "_draw_muscular_arm", "_draw_fire_sword",
                "_draw_lower_body_flowing"):
        assert not hasattr(G, old), f"old part still present: {old}"


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.5)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert G.PALETTE["mask_light"] in palette       # white mask
    assert G.PALETTE["blood_mid"] in palette        # blood stripes
    assert G.PALETTE["gold_mid"] in palette         # pauldron trim / buckle
    assert G.PALETTE["red_mid"] in palette          # loincloth / chest panel
    assert G.PALETTE["fire_mid"] in palette         # flame blade
    assert G.PALETTE["fire_hot"] in palette         # blade hot core
    assert G.PALETTE["metal_light"] in palette      # boot / pauldron steel
    assert G.PALETTE["hair_mid"] in palette         # fire mane

    # Rig v2 ~1.5x: telapak +70, mane api ke -106 -> bbox jauh lebih tinggi.
    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 110 and rect.width >= 70
    # Rig besar v2 (1.5x) harus terlihat lebih tinggi dari rig lama (100px).
    assert rect.height >= 140, f"rig v2 harus tinggi (1.5x), dapat {rect.height}"
    # Telapak depan menapak di y=+68 (sol boot di +66..+69, anchor 135).
    foot = idle.get_at((130 + 14, 135 + 68))
    assert foot.a > 150, f"telapak harus menapak di +68, alpha={foot.a}"
    # Mata / mask ada di zona kepala (y sekitar -52..-40).
    eye = any(idle.get_at((130 + dx, 135 + dy)).a > 150
              for dx in range(0, 14) for dy in range(-52, -40))
    assert eye, "mata/mask tidak ada di posisi kepala"
    assert pygame.image.tobytes(idle, "RGBA") != \
        pygame.image.tobytes(attack, "RGBA")


def test_blade_geometry_is_pose_driven():
    """Blade pulls back during wind-up then releases forward with the arm."""
    idle_angle = G._blade_angle(1.2, "idle", 0.0)
    windup_angle = G._blade_angle(1.2, "attack", 0.1)
    release_angle = G._blade_angle(1.2, "attack", 0.65)
    idle_tip = G._blade_tip_local(1.2, "idle", 0.0)
    windup_tip = G._blade_tip_local(1.2, "attack", 0.1)
    release_tip = G._blade_tip_local(1.2, "attack", 0.65)
    # Blade sweeps forward: release reaches farther forward (+x is facing).
    assert release_tip[0] > idle_tip[0] + 8
    assert windup_tip[0] < release_tip[0]
    # Wind-up tucks the blade back/up compared with the forward release.
    assert windup_angle < release_angle

    rest = pygame.Surface((240, 220), pygame.SRCALPHA)
    swing = pygame.Surface((240, 220), pygame.SRCALPHA)
    G._draw_grimjaw_elite(rest, 115, 115, 1, 1.0, "idle", 0.0)
    G._draw_grimjaw_elite(swing, 115, 115, 1, 1.0, "attack", 0.65)
    assert pygame.image.tobytes(rest, "RGBA") != \
        pygame.image.tobytes(swing, "RGBA")


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((200, 200), pygame.SRCALPHA)
    portrait = pygame.Surface((200, 200), pygame.SRCALPHA)
    G._draw_grimjaw_elite(normal, 100, 100, 1, 1.0, "idle", 0.0,
                          detail=False)
    G._draw_grimjaw_elite(portrait, 100, 100, 1, 1.0, "idle", 0.0,
                          detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack mengubah sendi, mane, dan blade - bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((200, 200), pygame.SRCALPHA)
        G._draw_grimjaw_elite(surface, 100, 100, 1,
                              i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((260, 240), pygame.SRCALPHA)
        G._draw_grimjaw_elite(surface, 120, 115, 1,
                              i * 0.3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe.

    Timer memakai SKILL_VISUAL_DURATION (q=180, w=90, e=60, r=90), BUKAN
    timer gameplay - FX phase membaca active_skill_timer di rentang visual.
    """
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 100), ("w", 50), ("e", 35), ("r", 50)):
        hero = _ProbeEntity("grimjaw", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 260, 152)
        hero.target.alive = True
        surface = pygame.Surface((360, 300), pygame.SRCALPHA)
        render_hero("grimjaw", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 35 and rect.height > 35, skill


def test_skill_fx_are_world_space():
    """Efek skill TIDAK menyusut bersama sprite: kompensasi 1/_render_scale.

    Ring AOE Q (Blade Fury) harus berada di radius DUNIA skill_range=70
    dari hero, yaitu 70/_render_scale px di canvas. Di-render pada dua
    _render_scale (1.0 dan 0.45): sampling lingkaran di radius tersebut
    harus menemukan ring di keduanya. Tanpa kompensasi, pada fs=0.45
    ring akan menggambar di radius 70 px canvas (bukan 155) -> 0 hit.
    """
    import math as _m
    from heroes._bundle import _NS_grimjaw as G

    def render(fs):
        surf = pygame.Surface((760, 760), pygame.SRCALPHA)
        h = _ProbeEntity("grimjaw", 380, 420)
        h.pulse = 1.3
        h.active_skill = "q"          # Blade Fury, steady -> ring penuh
        h.active_skill_timer = 100    # progress 0.44 (fasa steady)
        h.skill_range = 70
        h.target = _ProbeEntity("dummy", 520, 405)
        h.target.alive = True
        h._render_scale = fs
        G.draw_grimjaw(surf, h, 380, 420)
        return surf

    def hits_at_radius(surf, r_px):
        cx, cy = 380, 420
        hits = 0
        for a in range(0, 360, 2):
            x = int(cx + _m.cos(_m.radians(a)) * r_px)
            y = int(cy + _m.sin(_m.radians(a)) * r_px)
            if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                    and surf.get_at((x, y)).a > 40:
                hits += 1
        return hits

    for fs in (1.0, 0.45):
        s = render(fs)
        r_px = int(70 / fs)           # 70 dunia -> px canvas
        n = hits_at_radius(s, r_px)
        assert n > 90, (f"ring AOE Q tidak di radius dunia 70 saat "
                        f"fs={fs} (dapat {n}/180 hit) -> bukan world-space")


# ── paritas keluarga masterwork ──────────────────────────────────
# (renderer, label) yang sudah dinaikkan ke standar Thorne v2 + FX v2.1.
def _family_namespaces():
    from bosses.level2 import _NS_gorath, _NS_razak
    from bosses.level3 import _NS_ancient_apparition
    return (("gorath", _NS_gorath), ("razak", _NS_razak),
            ("ancient_apparition", _NS_ancient_apparition))


def test_family_shares_fx_vocabulary():
    """Renderer masterwork lain memakai kosakata FX yang sama.

    Menjaga agar upgrade berikutnya tidak menciptakan dialek FX baru:
    setiap namespace v2 harus menyediakan helper yang sama seperti
    Thorne/Grimjaw, dan `_fx_scale` harus memakai cap 2.6 yang sama.
    """
    from types import SimpleNamespace

    required = ("_fx_scale", "_ring_r", "_spark_star", "_chevron",
                "_dashed_ring", "_jagged_crack", "_tuft_points",
                "_static", "_dither_dots", "_mix", "_hash01")
    for label, NS in _family_namespaces():
        for helper in required:
            assert callable(getattr(NS, helper, None)), \
                f"{label}: helper {helper} hilang"
        # world-space: 1.0 tanpa _render_scale, 1/scale dengan cap 2.6
        assert NS._fx_scale(SimpleNamespace()) == 1.0, label
        assert abs(NS._fx_scale(SimpleNamespace(_render_scale=0.5)) - 2.0) \
            < 1e-6, label
        assert abs(NS._fx_scale(SimpleNamespace(_render_scale=0.1)) - 2.6) \
            < 1e-6, f"{label}: cap _fx_scale bukan 2.6"


def test_family_skill_fx_are_world_space():
    """Telegraph keluarga digambar di radius DUNIA, bukan px canvas.

    Gorath: W=150, E=85, R=190 px dunia. Pada _render_scale=0.5 ring
    harus muncul di 2x radius tersebut dalam px canvas.
    """
    import math as _m
    from types import SimpleNamespace as _S

    from bosses.level2 import _NS_gorath as GOR

    def probe(skill, timer, W=1000):
        surf = pygame.Surface((W, W), pygame.SRCALPHA)
        cx = cy = W // 2
        b = _S(boss_type="gorath", boss_class="mini", x=float(cx),
               y=float(cy), direction=1, facing=1, pulse=1.3, timer=0,
               attack_cooldown=44, active_skill=skill,
               active_skill_timer=timer,
               target=_S(x=float(cx + 95), y=float(cy - 20), alive=True),
               hurt_flash_timer=0, alive=True, radius=36, range=58,
               _render_scale=0.5)
        GOR.draw_gorath(surf, b, cx, cy)
        return surf, cx, cy, b

    def hits(surf, r_px, cx, cy, tol=3):
        n = 0
        for a in range(0, 360, 2):
            ca, sa = _m.cos(_m.radians(a)), _m.sin(_m.radians(a))
            for dr in range(-tol, tol + 1):
                x, y = int(cx + ca * (r_px + dr)), int(cy + sa * (r_px + dr))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and surf.get_at((x, y)).a > 30:
                    n += 1
                    break
        return n

    # W: AOE 150 dunia, digambar di garis tanah caster
    s, cx, cy, _ = probe("w", 40)
    n = hits(s, 300, cx, cy + GOR.GROUND_DY - 8)
    assert n > 120, f"W: ring 150 dunia tidak world-space ({n}/180)"

    # E: AOE 85 dunia, digambar di TARGET
    s, cx, cy, b = probe("e", 24)
    tx, ty = GOR._target_position(b, cx, cy)
    n = hits(s, 170, tx, ty)
    assert n > 120, f"E: ring 85 dunia tidak world-space ({n}/180)"

    # R: AOE 190 dunia di caster
    s, cx, cy, _ = probe("r", 60)
    n = hits(s, 380, cx, cy + GOR.GROUND_DY)
    assert n > 100, f"R: ring 190 dunia tidak world-space ({n}/180)"


def test_razak_skill_fx_are_world_space():
    """Telegraph Razak digambar di radius DUNIA, bukan px canvas.

    Razak: Q=75 (target), W=95 (target), E=80 (caster), R=180 (caster)
    px dunia. Pada _render_scale=0.5 ring harus muncul di 2x radius
    tersebut dalam px canvas.
    """
    import math as _m
    from types import SimpleNamespace as _S

    from bosses.level2 import _NS_razak as RZ

    def probe(skill, timer, W=1000):
        surf = pygame.Surface((W, W), pygame.SRCALPHA)
        cx = cy = W // 2
        b = _S(boss_type="razak", boss_class="mini", x=float(cx),
               y=float(cy), direction=1, facing=1, pulse=1.3, timer=0,
               attack_cooldown=45, active_skill=skill,
               active_skill_timer=timer,
               target=_S(x=float(cx + 95), y=float(cy - 20), alive=True),
               hurt_flash_timer=0, alive=True, radius=34, range=55,
               _render_scale=0.5)
        RZ.draw_razak(surf, b, cx, cy)
        return surf, cx, cy, b

    def hits(surf, r_px, cx, cy, tol=4):
        n = 0
        for a in range(0, 360, 2):
            ca, sa = _m.cos(_m.radians(a)), _m.sin(_m.radians(a))
            for dr in range(-tol, tol + 1):
                x, y = int(cx + ca * (r_px + dr)), int(cy + sa * (r_px + dr))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and surf.get_at((x, y)).a > 30:
                    n += 1
                    break
        return n

    # Q: telegraph 75 dunia di TARGET
    s, cx, cy, b = probe("q", 30)
    tx, ty = RZ._target_position(b, cx, cy)
    n = hits(s, 150, tx, ty)
    assert n > 120, f"Q: ring 75 dunia tidak world-space ({n}/180)"

    # W: telegraph 95 dunia di TARGET
    s, cx, cy, b = probe("w", 30)
    tx, ty = RZ._target_position(b, cx, cy)
    n = hits(s, 190, tx, ty)
    assert n > 120, f"W: ring 95 dunia tidak world-space ({n}/180)"

    # E: ring pendaratan 80 dunia di CASTER
    s, cx, cy, _ = probe("e", 20)
    n = hits(s, 160, cx, cy + RZ.GROUND_DY)
    assert n > 120, f"E: ring 80 dunia tidak world-space ({n}/180)"

    # R: AOE 180 dunia di CASTER
    s, cx, cy, _ = probe("r", 60)
    n = hits(s, 360, cx, cy + RZ.GROUND_DY)
    assert n > 100, f"R: ring 180 dunia tidak world-space ({n}/180)"


def test_ancient_apparition_skill_fx_are_world_space():
    """Telegraph Ancient Apparition digambar di radius DUNIA, bukan px canvas.

    AA: Q=80 (target), R=80 (target) px dunia. Pada _render_scale=0.5 ring
    harus muncul di 2x radius tersebut (160 px) dalam px canvas.
    """
    import math as _m
    from types import SimpleNamespace as _S

    from bosses.level3 import _NS_ancient_apparition as AA

    def probe(skill, timer, W=1000):
        surf = pygame.Surface((W, W), pygame.SRCALPHA)
        cx = cy = W // 2
        b = _S(boss_type="ancient_apparition", boss_class="true", x=float(cx),
               y=float(cy), direction=1, facing=1, pulse=1.3, timer=0,
               attack_cooldown=50, active_skill=skill,
               active_skill_timer=timer,
               target=_S(x=float(cx + 95), y=float(cy - 20), alive=True),
               hurt_flash_timer=0, alive=True, radius=40, range=150,
               _render_scale=0.5)
        AA.draw_ancient_apparition(surf, b, cx, cy)
        return surf, cx, cy, b

    def hits(surf, r_px, cx, cy, tol=4):
        n = 0
        for a in range(0, 360, 2):
            ca, sa = _m.cos(_m.radians(a)), _m.sin(_m.radians(a))
            for dr in range(-tol, tol + 1):
                x, y = int(cx + ca * (r_px + dr)), int(cy + sa * (r_px + dr))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and surf.get_at((x, y)).a > 30:
                    n += 1
                    break
        return n

    # Q: telegraph 80 dunia di TARGET -> 160 px di canvas
    s, cx, cy, b = probe("q", 30)
    tx, ty = AA._target_position(b, cx, cy)
    n = hits(s, 160, tx, ty)
    assert n > 90, f"Q: ring 80 dunia tidak world-space ({n}/180)"

    # R: telegraph 80 dunia di TARGET -> 160 px di canvas
    s, cx, cy, b = probe("r", 70)
    tx, ty = AA._target_position(b, cx, cy)
    n = hits(s, 160, tx, ty)
    assert n > 90, f"R: ring 80 dunia tidak world-space ({n}/180)"


def test_ancient_apparition_skill_fx_have_three_phases():
    """Tiap skill Ancient Apparition punya 3 tahap terbaca (aktivasi/steady/akhir)."""
    from types import SimpleNamespace as _S

    from bosses.level3 import _NS_ancient_apparition as AA

    for skill, dur in AA.SKILL_DUR.items():
        sigs = set()
        for timer in (dur - 4, int(dur * 0.6), 6):
            surf = pygame.Surface((620, 620), pygame.SRCALPHA)
            b = _S(boss_type="ancient_apparition", boss_class="true", x=310.0, y=310.0,
                   direction=1, facing=1, pulse=1.3, timer=0,
                   attack_cooldown=50, active_skill=skill,
                   active_skill_timer=timer,
                   target=_S(x=430.0, y=290.0, alive=True),
                   hurt_flash_timer=0, alive=True, radius=40, range=150)
            AA.draw_ancient_apparition(surf, b, 310, 310)
            sigs.add(pygame.image.tobytes(surf, "RGBA"))
        assert len(sigs) == 3, \
            f"ancient_apparition {skill}: hanya {len(sigs)}/3 tahap FX yang berbeda"


def test_ancient_apparition_keeps_public_names():
    """Upgrade v2 tidak boleh memutus nama publik lama _NS_ancient_apparition."""
    from bosses.level3 import _NS_ancient_apparition as AA

    legacy = ("PALETTE", "HAS_AACIRCLE", "_clamp", "_aacircle", "_aaline",
              "_poly", "_ellipse", "_rect", "_target_position",
              "IceShardProjectile", "IceBoltProjectile", "FrostBeam",
              "_detect_moving", "_update_attack_anim", "_manage_projectiles",
              "_spawn_ice_shard", "_spawn_ice_bolt", "_spawn_frost_beam",
              "draw_apparition", "draw_ancient_apparition", "draw_boss",
              "_draw_aa_idle", "_draw_aa_walk", "_draw_aa_attack",
              "_draw_aa_casting", "_draw_aa_body", "_draw_aa_body_raw",
              "_masterwork_finish", "_draw_ice_skirt", "_draw_ice_torso",
              "_draw_aa_head", "_draw_ice_crown", "_draw_idle_arms",
              "_draw_casting_arms", "_draw_attack_arms",
              "_draw_ice_arm_segment", "_draw_ice_claw",
              "_draw_body_sparkles", "_draw_ice_wisps", "_draw_shadow",
              "_draw_frost_aura", "_draw_ground_frost", "_draw_cast_flash",
              "_draw_ice_vortex_ground", "_draw_ice_vortex",
              "_draw_cold_feet_ground", "_draw_cold_feet_spikes",
              "_handle_skill_projectiles", "_draw_snowflake",
              "_draw_ice_shard", "_draw_frost_crystal_spike")
    missing = [n for n in legacy if not hasattr(AA, n)]
    assert not missing, f"ancient_apparition: nama publik hilang -> {missing}"


def test_razak_skill_fx_have_three_phases():
    """Tiap skill Razak punya 3 tahap terbaca (aktivasi/steady/akhir)."""
    from types import SimpleNamespace as _S

    from bosses.level2 import _NS_razak as RZ

    for skill, dur in RZ.SKILL_DUR.items():
        sigs = set()
        for timer in (dur - 4, int(dur * 0.6), 6):
            surf = pygame.Surface((620, 620), pygame.SRCALPHA)
            b = _S(boss_type="razak", boss_class="mini", x=310.0, y=310.0,
                   direction=1, facing=1, pulse=1.3, timer=0,
                   attack_cooldown=45, active_skill=skill,
                   active_skill_timer=timer,
                   target=_S(x=430.0, y=290.0, alive=True),
                   hurt_flash_timer=0, alive=True, radius=34, range=55)
            RZ.draw_razak(surf, b, 310, 310)
            sigs.add(pygame.image.tobytes(surf, "RGBA"))
        assert len(sigs) == 3, \
            f"razak {skill}: hanya {len(sigs)}/3 tahap FX yang berbeda"


def test_razak_keeps_public_names():
    """Upgrade v2 tidak boleh memutus nama publik lama _NS_razak."""
    from bosses.level2 import _NS_razak as RZ

    legacy = ("PALETTE", "_clamp", "_aacircle", "_aaline", "_poly",
              "_ellipse", "_rect", "_target_position", "NapalmProjectile",
              "NapalmPatch", "_detect_moving", "_update_attack_anim",
              "_manage_projectiles", "_manage_projectiles_no_patches",
              "_spawn_napalm", "draw_razak", "draw_boss", "_draw_shockwave",
              "_draw_razak_idle", "_draw_razak_walk", "_draw_razak_attack",
              "_draw_razak_dashing", "_draw_razak_full_raw",
              "_draw_razak_full", "_draw_bat_wings", "_draw_bat_wings_front",
              "_draw_bat_body", "_draw_bat_head", "_draw_goblin_rider",
              "_draw_goblin_torso", "_draw_goblin_head", "_draw_fuel_tanks",
              "_draw_goblin_idle_arms", "_draw_goblin_gun_arms",
              "_draw_goblin_attack_arms", "_draw_goblin_arm",
              "_draw_flame_gun", "_draw_machete_held",
              "_draw_machete_swinging", "_draw_fire_wisps", "_draw_shadow",
              "_draw_fire_aura", "_draw_machete_swing_arc", "_draw_flame",
              "_draw_ember", "_draw_fire_ground_patch",
              "_draw_sticky_napalm", "_draw_flamebreak",
              "_draw_firestorm_ground", "_draw_firestorm")
    missing = [n for n in legacy if not hasattr(RZ, n)]
    assert not missing, f"razak: nama publik hilang -> {missing}"


def test_family_skill_fx_have_three_phases():
    """Tiap skill keluarga punya 3 tahap terbaca (aktivasi/steady/telegraph)."""
    from types import SimpleNamespace as _S

    from bosses.level2 import _NS_gorath as GOR

    for skill, dur in GOR.SKILL_DUR.items():
        sigs = set()
        for timer in (dur - 4, int(dur * 0.6), 6):
            surf = pygame.Surface((620, 620), pygame.SRCALPHA)
            b = _S(boss_type="gorath", boss_class="mini", x=310.0, y=310.0,
                   direction=1, facing=1, pulse=1.3, timer=0,
                   attack_cooldown=44, active_skill=skill,
                   active_skill_timer=timer,
                   target=_S(x=430.0, y=290.0, alive=True),
                   hurt_flash_timer=0, alive=True, radius=36, range=58)
            GOR.draw_gorath(surf, b, 310, 310)
            sigs.add(pygame.image.tobytes(surf, "RGBA"))
        assert len(sigs) == 3, \
            f"gorath {skill}: hanya {len(sigs)}/3 tahap FX yang berbeda"


def test_family_keeps_public_names():
    """Upgrade v2 tidak boleh memutus nama publik lama renderer keluarga."""
    from bosses.level2 import _NS_gorath as GOR

    legacy = ("PALETTE", "_clamp", "_aacircle", "_aaline", "_poly",
              "_ellipse", "_rect", "_target_position", "BloodProjectile",
              "_detect_moving", "_update_attack_anim", "_manage_projectiles",
              "_spawn_projectile", "draw_gorath", "draw_boss",
              "_draw_shockwave", "_draw_gorath_idle", "_draw_gorath_walk",
              "_draw_gorath_attack", "_draw_gorath_body_raw",
              "_draw_gorath_body", "_draw_shadow", "_draw_blood_aura",
              "_draw_ground_blood_pool", "_draw_blood_wisps",
              "_draw_blood_trail", "_draw_blade_swing_arc",
              "_draw_swing_impact", "_draw_bloodrage",
              "_draw_bloodrite_ground", "_draw_bloodrite", "_draw_thirst",
              "_draw_rupture_ground", "_draw_rupture", "_draw_loincloth",
              "_draw_torso", "_draw_shoulders", "_draw_gorath_head",
              "_draw_spiky_hair", "_draw_idle_arms", "_draw_attack_arms",
              "_draw_arm_segment", "_draw_hand", "_draw_curved_blade",
              "_draw_curved_blade_angled", "_draw_body_blood_drips")
    missing = [n for n in legacy if not hasattr(GOR, n)]
    assert not missing, f"gorath: nama publik hilang -> {missing}"


def test_family_rigs_are_procedural():
    """Tidak ada renderer keluarga yang memuat aset dari disk."""
    for label, NS in _family_namespaces():
        source = inspect.getsource(sys.modules[NS.__module__]) \
            if hasattr(NS, "__module__") else ""
        if not source:
            source = open(os.path.join(ROOT, "bosses", "level2.py")).read()
        assert "pygame.image.load" not in source, label


def test_silhouette_outline_exists():
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    G._draw_grimjaw_elite(surface, 100, 100, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark > 60


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_blade_geometry_is_pose_driven()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_skill_visuals_render_with_masterwork()
    test_skill_fx_are_world_space()
    test_silhouette_outline_exists()
    test_family_shares_fx_vocabulary()
    test_family_skill_fx_are_world_space()
    test_razak_skill_fx_are_world_space()
    test_ancient_apparition_skill_fx_are_world_space()
    test_family_skill_fx_have_three_phases()
    test_razak_skill_fx_have_three_phases()
    test_ancient_apparition_skill_fx_have_three_phases()
    test_family_keeps_public_names()
    test_razak_keeps_public_names()
    test_ancient_apparition_keeps_public_names()
    test_family_rigs_are_procedural()
    print("OK - Grimjaw masterwork v2: rig 1.5x, blade pose, portrait LOD, "
          "Q/W/E/R world-space, outline, dan 12 frame animasi tervalidasi")
    print("OK - paritas keluarga (gorath v2): kosakata FX, telegraph "
          "world-space W150/E85/R190, 3 tahap per skill, nama publik utuh")
    print("OK - paritas keluarga (razak v2): telegraph world-space "
          "Q75/W95/E80/R180, 3 tahap per skill, nama publik utuh")
    print("OK - paritas keluarga (ancient_apparition v2): telegraph world-space "
          "Q80/R80, 3 tahap per skill, nama publik utuh")
