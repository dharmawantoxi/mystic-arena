#!/usr/bin/env python3
"""Regresi visual untuk Grimjaw Procedural Masterwork (versi V1 pixel-art).

Sejak rewrite V1 (heroes/grimjaw_v1.py, pola Kaizen/Vex V1) rig doodle
masterwork digantikan sprite chibi pixel-art 48x48 @2.6x: mane api
pose-driven, mask juggernaut putih ber-strip darah, torso V-taper +
sash + harness, dan flame blade yang geometrinya TETAP memakai fungsi
pose legacy (jembatan grimjaw_fx blade_points).  Kontrak yang dikunci:

- 100% prosedural (tanpa PNG / sprite-sheet / image.load).
- Identitas material Grimjaw lolos ke render akhir (swatch palette).
- Geometri blade pose-driven (atas -> bawah, warisan legacy).
- Pose idle/walk/attack/spin/hurt/death semuanya animasi (bukan sticker).
- Skill FX world-space dengan kompensasi _render_scale.
- Basic attack melepas gelombang api visual (damage=0, tanpa impact FX).
- Namespace lama tetap warisan API (legacy callables resolve).

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

# Namespace grimjaw sekarang subclass V1 dari namespace legacy: helper dan
# geometri lama tetap resolve lewat pewarisan, jalur gambar digantikan V1.
from heroes.grimjaw_v1 import install as _install_v1


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
    # Jalur gambar V1 (pixel ops + sprite assembler + layer Grimjaw).
    assert callable(G._draw_grimjaw_elite)
    assert callable(G._draw_grimjaw_sprite)
    assert callable(G._make_pixel_ops)
    assert callable(G._draw_pixel_mane_back)
    assert callable(G._draw_pixel_mask)
    assert callable(G._draw_pixel_blade)
    assert callable(G._draw_pixel_torso)
    assert callable(G._draw_pixel_legs)
    # Kontrak geometri + helper yang dikonsumsi lapisan FX hidup.
    assert callable(G._blade_angle)
    assert callable(G._blade_grip_local)
    assert callable(G._blade_tip_local)
    assert callable(G._blade_tip_position)
    assert callable(G._attack_pose)
    assert callable(G._fx_scale)
    assert callable(G._ring_r)
    assert callable(G._spark_star)
    assert callable(G._chevron)
    assert callable(G._dashed_ring)
    assert callable(G._jagged_crack)
    assert callable(G._tuft_points)
    assert callable(G._aoe_marks)
    assert callable(G._draw_blade_fury_ground)
    assert callable(G._draw_fire_slash_arc)
    assert callable(G._draw_blade_swing_trail)
    # Namespace lama tetap resolve lewat pewarisan (API publik historis).
    assert callable(G._draw_elite_flame_blade)
    assert callable(G._draw_elite_mask)
    assert callable(G._draw_elite_flame_mane)
    assert callable(G._draw_elite_mane_front)
    assert callable(G._draw_grimjaw_masterwork_details)
    assert callable(G._draw_grimjaw_blade_fury)
    assert callable(G._draw_grimjaw_omnislash)
    assert callable(G.draw_hero)
    # Skala V1: grid 48x48 pada 2.6x; helper lokal sudah canvas px
    # (RIG_SCALE netral 1.0).
    assert abs(G.PIXEL_SCALE - 2.6) < 1e-9
    assert abs(G.RIG_SCALE - 1.0) < 1e-9
    # Timeline serangan identik dengan rig lama + sinkron grimjaw_fx.
    assert (G.ATTACK_WINDUP_END, G.ATTACK_SWING_END) == (0.25, 0.62)
    assert (G.ATTACK_ARC_START, G.ATTACK_ARC_SWEEP,
            G.ATTACK_ARC_END) == (-2.30, -3.05, -5.35)


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.5)
    palette = colors(idle)

    # Exact swatches prove material layers reach the final arena render.
    assert G.PALETTE["mask_light"] in palette       # white mask
    assert G.PALETTE["blood_mid"] in palette        # blood stripes
    assert G.PALETTE["gold_mid"] in palette         # pauldron trim / buckle
    assert G.PALETTE["red_mid"] in palette          # sash / loincloth
    assert G.PALETTE["fire_mid"] in palette         # blade teeth
    assert G.PALETTE["fire_light"] in palette       # blade teeth hot
    assert G.PALETTE["metal_light"] in palette      # pauldron / shin steel
    assert G.PALETTE["hair_mid"] in palette         # fire mane

    # Rig V1: telapak +70, mane api ke -105 -> bbox jauh lebih tinggi.
    rect = idle.get_bounding_rect(min_alpha=8)
    assert rect.height >= 110 and rect.width >= 70
    assert rect.height >= 140, f"rig V1 harus tinggi, dapat {rect.height}"
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
    # Wind-up tucks the blade back/up compared with the forward release,
    # dan pose idle memang beda dari kedua fase ayunan itu (kalau sama,
    # sudut bilah tidak benar-benar digerakkan pose).
    assert windup_angle < release_angle
    assert idle_angle != windup_angle
    assert idle_angle != release_angle

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

    spins = set()
    for i in range(6):
        surface = pygame.Surface((260, 240), pygame.SRCALPHA)
        G._draw_grimjaw_elite(surface, 120, 115, 1,
                              0.6 + i * 0.35, "spin", 0.0,
                              spin_phase=i * 2.1)
        spins.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(spins) == 6


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe.

    Timer memakai SKILL_VISUAL_DURATION (q=118, w=59, e=39, r=59),
    BUKAN timer gameplay - FX phase membaca active_skill_timer di
    rentang visual.
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

    Marker AOE Q (Blade Fury) versi ANGULAR (tick radial + bracket sudut,
    bukan cincin kontinu) tetap menandai radius DUNIA skill_range=70 dari
    hero, yaitu 70/_render_scale px di canvas. Di-render pada dua
    _render_scale (1.0 dan 0.45): sampling pita di sekitar radius tersebut
    harus menemukan spike marker di keduanya. Tanpa kompensasi, pada
    fs=0.45 marker akan menggambar di radius 70 px canvas (bukan 155)
    -> ~0 hit hangat di pita 155.
    """
    import math as _m

    def warm(c):
        return c.a > 80 and c[0] > 140 and c[0] - c[2] > 70 and c[1] < 230

    def render(fs):
        surf = pygame.Surface((760, 760), pygame.SRCALPHA)
        h = _ProbeEntity("grimjaw", 380, 420)
        h.pulse = 1.3
        h.active_skill = "q"          # Blade Fury, steady -> marker penuh
        h.active_skill_timer = 100    # progress visual 0.15
        h.skill_range = 70
        h.target = _ProbeEntity("dummy", 520, 405)
        h.target.alive = True
        h._render_scale = fs
        G.draw_grimjaw(surf, h, 380, 420)
        return surf

    def warm_hits_in_band(surf, r_px, band=12):
        cx, cy = 380, 420
        hits = 0
        for a in range(0, 360, 2):
            ca, sa = _m.cos(_m.radians(a)), _m.sin(_m.radians(a))
            for dk in range(-band, band + 1):
                x = int(cx + ca * (r_px + dk))
                y = int(cy + sa * (r_px + dk))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and warm(surf.get_at((x, y))):
                    hits += 1
                    break
        return hits

    for fs in (1.0, 0.45):
        s = render(fs)
        r_px = int(70 / fs)           # 70 dunia -> px canvas
        n = warm_hits_in_band(s, r_px)
        assert n > 10, (f"marker AOE Q tidak di radius dunia 70 saat "
                        f"fs={fs} (dapat {n}/180 hit) -> bukan world-space")


def test_skill_state_changes_body():
    normal = pygame.Surface((280, 300), pygame.SRCALPHA)
    charged = pygame.Surface((280, 300), pygame.SRCALPHA)
    G._draw_grimjaw_body(normal, 140, 155, 1, 1.0, "idle", 0, 0, False,
                         skill_state=None)
    G._draw_grimjaw_body(charged, 140, 155, 1, 1.0, "idle", 0, 0, False,
                         skill_state="r")
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(charged, "RGBA")


def test_v1_install_layering():
    """install() mengembalikan subclass dari namespace legacy yang diberi."""
    class _FakeLegacy:
        PALETTE = {"legacy_key": (1, 2, 3)}

    wrapped = _install_v1(_FakeLegacy)
    assert issubclass(wrapped, _FakeLegacy)
    assert wrapped.PALETTE["legacy_key"] == (1, 2, 3)
    # Kunci kritis live FX tetap ada meski base minimal.
    for key in ("fire_mid", "fire_light", "fire_hot", "fire_core",
                "metal_light", "armor_mid", "armor_darkest", "rage_mid",
                "heal_mid", "gold_light", "blood_mid", "white",
                "shadow_deep"):
        assert key in wrapped.PALETTE


def test_basic_attack_spawn_wave_canvas_fallback():
    """Serangan dasar melepas gelombang api dari ujung bilah di rilis.

    Permintaan owner: "saya mau ada projectile saat melakukan basic
    attack, projectile nya menyesuaikan heronya".  Grimjaw melee: ayunan
    melepas FlameWaveProjectile (busur api pendek) dari ujung pedang
    menuju target - murni visual (damage=0, tanpa impact FX).  Tidak
    seperti hero ranged, canvas SELALU spawn walau FX live aktif karena
    lapisan hidup melee tidak punya proyektil basic-attack sendiri.
    """
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 240, 120)
    target.alive = True

    hero = _ProbeEntity("grimjaw", 130, 140)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    hero.active_skill = None
    hero.target = target
    hero._gj_proj_spawned = False

    saved = G._FX_LIVE.v
    G._FX_LIVE.v = False          # paksa jalur canvas (tanpa FX live)
    try:
        # Sebelum titik rilis: belum ada gelombang.
        hero._gj_attack_progress = 0.30
        G._draw_grimjaw_attack(surface, hero, 130, 140)
        assert len(getattr(hero, "_gj_projectiles", [])) == 0

        # Di jendela rilis (ap 0.5-0.6): busur api terbang ke target.
        hero._gj_attack_progress = 0.55
        G._draw_grimjaw_attack(surface, hero, 130, 140)
        items = getattr(hero, "_gj_projectiles", [])
        assert len(items) == 1
        wave = items[0]
        assert type(wave) is G.FlameWaveProjectile
        assert wave.target is target
        assert wave.damage == 0

        # Anti-dobel: frame rilis berikutnya tidak menambah gelombang.
        G._draw_grimjaw_attack(surface, hero, 130, 140)
        assert len(getattr(hero, "_gj_projectiles", [])) == 1

        # Ayunan selesai: kunci rilis dibuka lagi untuk ayunan berikut.
        hero._gj_attack_progress = 0.95
        G._draw_grimjaw_attack(surface, hero, 130, 140)
        assert hero._gj_proj_spawned is False

        # Melee: canvas tetap spawn walau FX live aktif (tak ada dobel).
        hero._gj_projectiles = []
        hero._gj_proj_spawned = False
        hero._gj_attack_progress = 0.55
        G._FX_LIVE.v = True
        G._draw_grimjaw_attack(surface, hero, 130, 140)
        assert len(hero._gj_projectiles) == 1
    finally:
        G._FX_LIVE.v = saved


def test_crit_attack_spawn_crit_wave():
    """Serangan crit melepas gelombang emas (bukan api biasa)."""
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 240, 120)
    target.alive = True

    hero = _ProbeEntity("grimjaw", 130, 140)
    hero.pulse = 1.0
    hero.direction = hero.facing = 1
    hero.active_skill = "e"
    hero.target = target
    hero._gj_proj_spawned = False

    saved = G._FX_LIVE.v
    G._FX_LIVE.v = False
    try:
        hero._gj_attack_progress = 0.55
        G._draw_grimjaw_attack(surface, hero, 130, 140, crit=True)
        items = getattr(hero, "_gj_projectiles", [])
        assert len(items) == 1
        assert type(items[0]) is G.CritWaveProjectile
        assert items[0].damage == 0
    finally:
        G._FX_LIVE.v = saved


# ── paritas keluarga masterwork ──────────────────────────────────
# (renderer, label) yang sudah dinaikkan ke standar Thorne v2 + FX v2.1.
def _family_namespaces():
    from bosses.level2 import _NS_gorath, _NS_razak
    from heroes._bundle import _NS_sylara
    return (("gorath", _NS_gorath), ("razak", _NS_razak),
            ("sylara", _NS_sylara))


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


def test_razak_skill_fx_have_three_phases():
    """Tiap skill Razak punya 3 tahap terbaca (aktivasi/steady/akhir)."""
    from types import SimpleNamespace as _S

    from bosses.level2 import _NS_razak as RZ

    # Lapisan hidup Razak (heroes/razak_fx.py) maju memakai jam NYATA:
    # draw_ground_layer() memanggil tick() tanpa dt, dan tick() meminta
    # combat_feel.fx_dt(). Dua hal karena itu bisa membuat test ini
    # lulus/gagal tergantung kecepatan mesin, bukan tergantung kode:
    #
    #   1. hit-stop bocor. Test sebelumnya (mis.
    #      test_skill_visuals_render_with_masterwork) memicu hit_stop()
    #      sebagai umpan balik benturan; hit-stop meluruh menurut waktu
    #      nyata (~0.045-0.08 s). Kalau test ini keburu jalan sebelum
    #      luruh, fx_dt() anjlok ke ~0.00075 s.
    #   2. tiga render bisa selesai dalam 1 milidetik SDL yang sama,
    #      sehingga dt antar-fase = 0 dan FX tidak sempat maju.
    #
    # Dua-duanya membuat ketiga snapshot nyaris sama. Jadi: bersihkan
    # bus + registry FX dulu, lalu majukan waktu FX dengan dt EKSPLISIT
    # supaya yang diuji murni progres tahap skill.
    try:
        from heroes import combat_feel as _feel
    except Exception:
        _feel = None
    try:
        from heroes import razak_fx as _rfx
    except Exception:
        _rfx = None

    # Patok jam FX ke 1/60 s per frame selama test ini. draw_ground_layer()
    # memanggil tick() sendiri, jadi mematok tick() adalah satu-satunya cara
    # melepas render dari jam dinding sepenuhnya.
    _orig_tick = getattr(_rfx, "tick", None) if _rfx is not None else None
    if _orig_tick is not None:
        _rfx.tick = lambda dt=None: _orig_tick(1.0 / 60.0)

    try:
        for skill, dur in RZ.SKILL_DUR.items():
            if _feel is not None:
                _feel.reset()
            if _rfx is not None:
                _rfx.reset_all()
            sigs = set()
            for timer in (dur - 4, int(dur * 0.6), 6):
                surf = pygame.Surface((620, 620), pygame.SRCALPHA)
                b = _S(boss_type="razak", boss_class="mini", x=310.0,
                       y=310.0, direction=1, facing=1, pulse=1.3, timer=0,
                       attack_cooldown=45, active_skill=skill,
                       active_skill_timer=timer,
                       target=_S(x=430.0, y=290.0, alive=True),
                       hurt_flash_timer=0, alive=True, radius=34, range=55)
                RZ.draw_razak(surf, b, 310, 310)
                sigs.add(pygame.image.tobytes(surf, "RGBA"))
            assert len(sigs) == 3, \
                f"razak {skill}: hanya {len(sigs)}/3 tahap FX yang berbeda"
    finally:
        if _orig_tick is not None:
            _rfx.tick = _orig_tick
        if _feel is not None:
            _feel.reset()
        if _rfx is not None:
            _rfx.reset_all()


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
    test_skill_state_changes_body()
    test_v1_install_layering()
    test_basic_attack_spawn_wave_canvas_fallback()
    test_crit_attack_spawn_crit_wave()
    test_silhouette_outline_exists()
    test_family_shares_fx_vocabulary()
    test_family_skill_fx_are_world_space()
    test_razak_skill_fx_are_world_space()
    test_family_skill_fx_have_three_phases()
    test_razak_skill_fx_have_three_phases()
    test_family_keeps_public_names()
    test_razak_keeps_public_names()
    test_family_rigs_are_procedural()
    print("OK - Grimjaw masterwork V1: rig pixel 48x48, blade pose, "
          "portrait LOD, Q/W/E/R world-space, wave basic-attack, outline, "
          "dan frame animasi tervalidasi")
    print("OK - paritas keluarga (gorath v2): kosakata FX, telegraph "
          "world-space W150/E85/R190, 3 tahap per skill, nama publik utuh")
    print("OK - paritas keluarga (razak v2): telegraph world-space "
          "Q75/W95/E80/R180, 3 tahap per skill, nama publik utuh")
