#!/usr/bin/env python3
"""Regresi visual untuk Kaizen PIXEL MASTERWORK v3 + SKILL FX / SWING / PROJECTILE.

Memastikan upgrade mengikuti standar Thorne v2/v2.1 (docs/AUDIT_ULANG_DARI_AWAL.md)
dan tidak kembali menjadi rig lama:

  - 100% prosedural (tanpa PNG / sprite-sheet / image.load).
  - Rig native ~1.5x (bbox idle >= 150 px tinggi, telapak +60, kepala -94).
  - Helper FX v2.1 tersedia (_fx_scale, _spark_star, _chevron, _dashed_ring,
    _jagged_crack, _tuft_points, _static, _aoe_marks).
  - Palet material sampai ke render akhir (saya lacquer, tabi, pauldron,
    hachimaki, eye iris).
  - Portrait LOD lebih kaya.
  - Animasi nyata: 12 frame walk/attack unik (bukan sticker translation),
    serangan 7 keyframe dengan frame IMPACT + smear berlapis.
  - Skill FX world-space: marker AOE angular E tepat 100 px dunia dan R 150 px
    dunia pada _render_scale apa pun (kompensasi 1/_render_scale, cap 2.6).
    Telegraph memakai tick radial + bracket, BUKAN cincin kontinu.
  - Outline selout ada di siluet.

Jalankan:  python3 tools/test_kaizen_masterwork.py
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
from heroes._bundle import _NS_kaizen as K
from types import SimpleNamespace as _NS


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(action="idle", progress=0.0):
    surface = pygame.Surface((300, 300), pygame.SRCALPHA)
    hero = _ProbeEntity("kaizen", 150, 155)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if action == "attack":
        hero._kz_attack_progress = progress
        hero._kz_attack_active = True
        hero.range = 40
        K._draw_kaizen_attack(surface, hero, 150, 155)
    elif action == "walk":
        K._draw_kaizen_walk(surface, hero, 150, 155)
    else:
        K._draw_kaizen_idle(surface, hero, 150, 155)
    return surface


def test_masterwork_is_procedural():
    source = inspect.getsource(K)
    assert "pygame.image.load" not in source
    assert callable(K._draw_kaizen_elite)
    assert callable(K._draw_elite_katana)
    # Kosakata FX v2.1 (standar Thorne) tersedia untuk audit renderer.
    for helper in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
                   "_jagged_crack", "_tuft_points", "_static", "_mix",
                   "_hash01", "_dither_dots", "_attack_pose", "_aoe_marks"):
        assert callable(getattr(K, helper)), helper
    # Body-part sticker lama tidak boleh kembali.
    for old in ("_draw_saya_back", "_draw_masterwork_details",
                "_draw_torso", "_draw_head", "_draw_hakama",
                "_draw_ponytail", "_draw_scarf_back", "_draw_scarf_front",
                "_draw_idle_arms", "_draw_attack_arms", "_draw_arm_segment",
                "_draw_hand", "_draw_katana_idle", "_draw_katana_swing",
                "_draw_katana_blade", "_draw_katana_handle",
                "_draw_swing_trail", "_draw_body_particles"):
        assert not hasattr(K, old), f"old part still present: {old}"


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.52)
    palette = colors(idle)

    # Swatch material eksak membuktikan lapisan sampai ke render akhir.
    assert (204, 211, 216) in palette       # tabi socks / kyahan
    assert K.PALETTE["saya_mid"] in palette         # lacquered saya
    assert K.PALETTE["gold_light"] in palette       # kojiri / tsuba
    assert K.PALETTE["cloth_high"] in palette       # piping jaket
    assert K.PALETTE["steel_shine"] in palette      # specular bilah
    assert K.PALETTE["scarf_high"] in palette       # scarf rim
    assert K.PALETTE["eye_iris_light"] in palette   # iris mata

    # Rig v2 ~1.5x: bbox idle jauh lebih besar dari rig lama (104x112).
    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 150 and rect.width >= 120, \
        f"rig v2 harus ~1.5x, dapat {rect.w}x{rect.h}"
    # Telapak depan menapak di sekitar +60 (anchor 155 -> y 215).
    foot = idle.get_at((150 + 17, 155 + 60))
    assert foot.a > 150, f"telapak harus menapak di +60, alpha={foot.a}"
    # Mata ada di zona kepala (y sekitar -72..-65).
    eye = any(idle.get_at((150 + dx, 155 + dy)).a > 150
              for dx in range(7, 13) for dy in range(-73, -64))
    assert eye, "mata tidak ada di posisi kepala"
    assert pygame.image.tobytes(idle, "RGBA") != \
        pygame.image.tobytes(attack, "RGBA")


def test_attack_keyframes_and_smear():
    """Serangan 7 keyframe: wind-up bersih, IMPACT punya smear + bintang."""
    # IMPACT (progress ~0.5) harus menghasilkan px putih sian (smear/star)
    # DI LUAR siluet badan (sisi kanan-depan).
    impact = render_pose("attack", 0.52)
    windup = render_pose("attack", 0.12)
    rest = render_pose("idle")

    def fx_pixels(surf):
        n = 0
        for y in range(0, surf.get_height(), 2):
            for x in range(0, surf.get_width(), 2):
                c = surf.get_at((x, y))
                if c.a > 120 and c.r > 200 and c.g > 230 and c.b > 240:
                    n += 1
        return n

    assert fx_pixels(impact) > fx_pixels(windup) + 3, \
        "frame IMPACT harus lebih terang (smear + bintang) dari wind-up"
    # 10 progres berbeda -> 9 pose unik (endpoint = loop closure).
    frames = set()
    for i in range(10):
        s = pygame.Surface((300, 300), pygame.SRCALPHA)
        K._draw_kaizen_elite(s, 150, 155, 1, 0.0, "attack", i / 9.0)
        frames.add(pygame.image.tobytes(s, "RGBA"))
    assert len(frames) == 9, f"dapat {len(frames)}/10 pose unik"
    # Sudut IMPACT < sudut release (ayunan maju), lewat _attack_pose.
    windup_angle = K._attack_pose(0.12)["angle"]
    impact_angle = K._attack_pose(0.54)["angle"]
    assert windup_angle < 0 < impact_angle, "ayunan harus melewati nol"
    assert pygame.image.tobytes(rest, "RGBA") != \
        pygame.image.tobytes(windup, "RGBA")


def test_katana_tip_is_full_length_from_actual_hand():
    """Live tip geometry must reach the complete cached pixel sword."""
    progress = 0.52
    pose = K._attack_pose(progress)
    tip = K._katana_tip_local(0.0, "attack", progress, attack_combo=0)
    hand = pose["hand"]
    distance = math.hypot(tip[0] - hand[0], tip[1] - hand[1])
    expected = K.BLADE_LEN + K._attack_extension(progress, 0) * K.PIXEL_SCALE
    assert abs(distance - expected) < 1e-6
    assert distance > 70.0, "katana live tip masih terlalu pendek"


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((300, 300), pygame.SRCALPHA)
    portrait = pygame.Surface((300, 300), pygame.SRCALPHA)
    K._draw_kaizen_elite(normal, 150, 155, 1, .8, "idle", 0.0, False)
    K._draw_kaizen_elite(portrait, 150, 155, 1, .8, "idle", 0.0, True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_rig_has_real_animation_frames():
    """Walk/attack mengubah sendi dan siluet, bukan sticker translation."""
    frames = set()
    for i in range(6):
        surface = pygame.Surface((300, 300), pygame.SRCALPHA)
        K._draw_kaizen_elite(surface, 150, 155, 1,
                             i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) == 6

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((300, 280), pygame.SRCALPHA)
        K._draw_kaizen_elite(surface, 150, 150, 1,
                             i * .3, "attack", i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe.

    Timer memakai SKILL_VISUAL_DURATION (q=60, w=90, e=60, r=100), BUKAN
    timer gameplay - FX phase membaca active_skill_timer di rentang visual.
    """
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 30), ("w", 50), ("e", 30), ("r", 50)):
        hero = _ProbeEntity("kaizen", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 290, 155)
        hero.target.alive = True
        surface = pygame.Surface((420, 320), pygame.SRCALPHA)
        render_hero("kaizen", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 40 and rect.height > 40, skill


def test_skill_fx_are_world_space():
    """Efek skill TIDAK menyusut bersama sprite: kompensasi 1/_render_scale.

    Marker AOE E (Sweep) versi ANGULAR (tick radial + bracket sudut, bukan
    cincin kontinu) tetap menandai radius DUNIA 100 dari hero, yaitu
    100/_render_scale px di canvas, di sekitar titik tanah (y + 30).
    Di-render pada dua _render_scale: sampling pita di sekitar radius
    tersebut harus menemukan spike marker di keduanya. Tanpa kompensasi,
    pada fs=0.5 marker akan menggambar di radius 100 px canvas (bukan 200)
    -> ~0 hit di pita 200.
    """
    def render(fs):
        surf = pygame.Surface((900, 900), pygame.SRCALPHA)
        h = _ProbeEntity("kaizen", 450, 500)
        h.pulse = 1.3
        h.active_skill = "e"          # Sweep -> marker jangkauan penuh
        h.active_skill_timer = 20     # progress 0.66 (masih telegraph)
        h.skill_range = 100
        h.target = _NS(x=590, y=485, alive=True)
        h._render_scale = fs
        K.draw_kaizen(surf, h, 450, 500)
        return surf

    def hits_in_band(surf, r_px, cx=450, cy=530, band=12):
        # pusat marker tanah = (x, y + 30)
        hits = 0
        for a in range(0, 360, 2):
            ca = math.cos(math.radians(a))
            sa = math.sin(math.radians(a))
            for dk in range(-band, band + 1):
                x = int(cx + ca * (r_px + dk))
                y = int(cy + sa * (r_px + dk))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and surf.get_at((x, y)).a > 40:
                    hits += 1
                    break
        return hits

    for fs in (1.0, 0.5):
        s = render(fs)
        r_px = int(100 / fs)           # 100 dunia -> px canvas
        n = hits_in_band(s, r_px)
        assert n > 10, (f"marker AOE E tidak di radius dunia 100 saat "
                        f"fs={fs} (dapat {n}/180 hit) -> bukan world-space")

    # R: tornado berbasis AOE 150 px dunia di sekitar caster.
    def render_r(fs):
        surf = pygame.Surface((1200, 1200), pygame.SRCALPHA)
        h = _ProbeEntity("kaizen", 600, 640)
        h.pulse = 1.3
        h.active_skill = "r"
        h.active_skill_timer = 30
        h.skill_range = 150
        h.target = _NS(x=740, y=625, alive=True)
        h._render_scale = fs
        K.draw_kaizen(surf, h, 600, 640)
        return surf

    for fs in (1.0, 0.5):
        s = render_r(fs)
        r_px = int(150 / fs)
        n = hits_in_band(s, r_px, cx=600, cy=670)
        assert n > 10, (f"marker AOE R tidak di radius dunia 150 saat "
                        f"fs={fs} (dapat {n}/180 hit)")


def test_skill_body_reaction_and_glow():
    """Badan ikut bereaksi ke state skill (W=gale, R=storm)."""
    plain = pygame.Surface((300, 300), pygame.SRCALPHA)
    gale = pygame.Surface((300, 300), pygame.SRCALPHA)
    storm = pygame.Surface((300, 300), pygame.SRCALPHA)
    K._draw_kaizen_elite(plain, 150, 155, 1, 1.1, "idle", 0.0,
                         False, False, False)
    K._draw_kaizen_elite(gale, 150, 155, 1, 1.1, "idle", 0.0,
                         False, True, False)
    K._draw_kaizen_elite(storm, 150, 155, 1, 1.1, "idle", 0.0,
                         False, False, True)
    base = pygame.image.tobytes(plain, "RGBA")
    assert pygame.image.tobytes(gale, "RGBA") != base
    assert pygame.image.tobytes(storm, "RGBA") != base


def test_silhouette_outline_exists():
    surface = pygame.Surface((300, 300), pygame.SRCALPHA)
    K._draw_kaizen_elite(surface, 150, 155, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark > 60, f"selout outline terlalu tipis: {dark}px"


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_attack_keyframes_and_smear()
    test_portrait_lod_is_distinct()
    test_rig_has_real_animation_frames()
    test_skill_visuals_render_with_masterwork()
    test_skill_fx_are_world_space()
    test_skill_body_reaction_and_glow()
    test_silhouette_outline_exists()
    print("OK - Kaizen masterwork v2: rig 1.5x, 7-keyframe attack + smear, "
          "portrait LOD, Q/W/E/R world-space, selout, dan 15 frame "
          "animasi tervalidasi")
