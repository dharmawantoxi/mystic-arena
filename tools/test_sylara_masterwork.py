#!/usr/bin/env python3
"""Regresi visual untuk Sylara Procedural Masterwork (versi V1 pixel-art).

Sejak rewrite V1 (heroes/sylara_v1.py, pola Kaizen/Vex/Grimjaw V1) rig
masterwork bone-2D digantikan sprite chibi pixel-art 48x48 @2.6x: hood
runcing + crest tersapu, rambut merah Wind Ranger, korset hijau ber-strap
kulit, quiver + anak panah, dan busur recurve pose-driven yang ujungnya
benar-benar ditarik saat tembakan.  Kontrak yang dikunci di sini:

- 100% prosedural (tanpa PNG / sprite-sheet / image.load).
- Identitas material Sylara lolos ke render akhir (swatch palette).
- Geometri busur pose-driven (jembatan sylara_fx.bow_points).
- Pose idle/walk/attack/skill/death semuanya animasi (bukan sticker).
- Skill FX world-space (radius dunia via _ring_r) + kompensasi
  _render_scale.
- **Massa FX skill tidak pernah menutupi badan**: cakram isi & cincin
  mengembang digambar di lapisan tanah SEBELUM badan; lapisan depan hanya
  aksen ringan (spark tepi, streak sisi tubuh, flash kecil di senjata).
- Serangan dasar melepas panah angin visual (damage=0) dari nock; saat
  lapisan FX hidup aktif, canvas tidak dobel-spawn (kecuali skill).
- Namespace lama tetap warisan API (legacy callables resolve).

Jalankan:  python3 tools/test_sylara_masterwork.py
"""
import inspect
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import _ProbeEntity  # noqa: E402
from heroes._bundle import _NS_sylara as S  # noqa: E402

# Namespace sylara sekarang subclass V1 dari namespace legacy: helper lama
# tetap resolve lewat pewarisan, jalur gambar digantikan V1.
from heroes.sylara_v1 import install as _install_v1  # noqa: E402

try:
    from heroes import sylara_fx as _syfx  # noqa: E402
    _syfx.SYLARA_FX_ENABLED = False
except Exception:                          # pragma: no cover - tool minimal
    _syfx = None

# Demo/test ini memotret jalur CANVAS (rig + aksen in-canvas); lapisan
# hidup 60 fps dimatikan supaya hasilnya stabil.
S._LIVE_MOD = False

CORE_KEYS = ("hood_mid", "hood_dark", "cloth_mid", "leather_mid", "gold_mid",
             "hair_dark", "wood_mid", "skin_mid", "outline")
WIND_KEYS = ("wind_mid", "wind_light", "wind_bright", "leaf_gold")


def colors(surface):
    return {surface.get_at((x, y))[:3]
            for y in range(surface.get_height())
            for x in range(surface.get_width())
            if surface.get_at((x, y)).a}


def render_pose(action="idle", progress=0.0):
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    hero = _ProbeEntity("sylara", 130, 150)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    if action == "attack":
        S._draw_sylara_attack(surface, hero, 130, 150)
    else:
        S._draw_sylara_body(surface, 130, 150, 1, 1.25, action, progress,
                            detail=True)
    return surface


def _skill_unit(skill, timer, scale=1.0, x=380.0, y=340.0):
    hero = _ProbeEntity("sylara", x, y)
    hero.pulse = 1.4
    hero.direction = hero.facing = 1
    hero.active_skill = skill
    hero.active_skill_timer = timer
    hero._render_scale = scale
    hero._windrun_active = skill == "w"
    hero._windrun_timer = 60 if skill == "w" else 0
    hero._focus_fire_timer = 180 if skill == "q" else 0
    hero._powershot_timer = 60 if skill == "r" else 0
    hero.target = _ProbeEntity("dummy", 560.0, y)
    hero.target.alive = True
    hero._sy_projectiles = []
    return hero


# ═══ 1. PROSEDURAL & KONTRAK V1 ═══════════════════════════════════════════
def test_masterwork_is_procedural():
    source = inspect.getsource(S)
    assert "pygame.image.load" not in source
    # Jalur gambar V1 (pixel ops + sprite assembler).
    assert callable(S._draw_sylara_elite)
    assert callable(S._draw_sylara_sprite)
    assert callable(S._make_pixel_ops)
    assert callable(S._draw_pixel_hood)
    assert callable(S._draw_pixel_bow)
    assert callable(S._draw_pixel_cape)
    assert callable(S._draw_pixel_quiver)
    assert callable(S._draw_pixel_legs)
    assert callable(S._draw_pixel_arms)
    # Kontrak geometri busur + helper yang dikonsumsi lapisan FX hidup.
    assert callable(S._bow_geometry)
    assert callable(S._bow_grip_local)
    assert callable(S._bow_tip_local)
    assert callable(S._bow_nock_local)
    assert callable(S._bow_release_local)
    assert callable(S._bow_trail_samples)
    assert callable(S._bow_grip_position)
    assert callable(S._bow_release_position)
    assert callable(S._draw_bow_swing_trail)
    assert callable(S._fx_scale)
    assert callable(S._ring_r)
    assert callable(S._spark_star)
    assert callable(S._chevron)
    assert callable(S._dashed_ring)
    assert callable(S._jagged_crack)
    assert callable(S._tuft_points)
    assert callable(S._swing_hitbox)
    # Namespace lama tetap resolve lewat pewarisan (API publik historis).
    assert callable(S._draw_elite_bow)
    assert callable(S._draw_elite_arrow)
    assert callable(S._draw_sylara_masterwork_details)
    assert callable(S._draw_sylara_rig)
    assert callable(S.draw_boss)
    assert callable(S.draw_sylara)
    # Skala V1: grid 48x48 pada 2.6x; helper lokal sudah canvas px
    # (RIG_SCALE netral 1.0, bukan 1.52 masterwork lama).
    assert abs(S.PIXEL_SCALE - 2.6) < 1e-9
    assert abs(S.RIG_SCALE - 1.0) < 1e-9
    # Timeline serangan identik dengan rig lama + sinkron sylara_fx.
    assert (S.ATTACK_WINDUP_END, S.ATTACK_IMPACT_FRAME,
            S.ATTACK_SWING_END) == (0.26, 0.52, 0.58)
    assert S.SKILL_VISUAL_DURATION == {"q": 180, "w": 180, "e": 150,
                                       "r": 60}
    assert S.SWING_RANGE == 64.0


def test_material_details_and_pose():
    idle = render_pose("idle")
    attack = render_pose("attack", 0.52)
    palette = colors(idle)

    # Swatch identitas Sylara harus benar-benar sampai ke render akhir:
    # hood hijau, tunic, kulit, rambut merah, kayu busur, emas.
    idx = idle.get_bounding_rect(min_alpha=8)
    core = pygame.Surface((idx.width, idx.height), pygame.SRCALPHA)
    core.blit(idle, (0, 0), idx)
    core_colors = colors(core)
    for key in CORE_KEYS:
        assert tuple(S.PALETTE[key][:3]) in palette, \
            "swatch %s hilang dari render" % key
    assert len(core_colors) >= 30

    # Elemen tema angin/hutan hidup di lapisan FX (bukan material badan).
    scene = pygame.Surface((640, 640), pygame.SRCALPHA)
    hero = _skill_unit("w", 96, x=320.0, y=320.0)
    S.draw_sylara(scene, hero, 320, 320)
    scene_colors = colors(scene)
    for key in WIND_KEYS[:2]:
        assert tuple(S.PALETTE[key][:3]) in scene_colors, \
            "swatch FX %s hilang dari frame skill" % key

    assert idx.height >= 100 and idx.width >= 60, (idx.width, idx.height)
    assert pygame.image.tobytes(idle, "RGBA") != \
        pygame.image.tobytes(attack, "RGBA")


# ═══ 2. GEOMETRI BUSUR (JEMBATAN FX HIDUP) ════════════════════════════════
def test_bow_geometry_is_pose_driven():
    """Tali ditarik ke belakang saat wind-up, lalu panah maju saat rilis."""
    idle = S._bow_geometry(1.2, "idle", 0.0)
    windup = S._bow_geometry(1.2, "attack", 0.24)
    release = S._bow_geometry(1.2, "attack", 0.56)
    # Titik nock menarik ke arah badan saat draw bertambah.
    assert S._bow_geometry(1.2, "attack", 0.52)["nock"][0] < \
        idle["nock"][0]
    # Ujung mata panah melesat maju setelah rilis.
    assert release["arrow_tip"][0] > windup["arrow_tip"][0] + 4
    # Ujung limb busur ikut berubah saat draw (busur melentur).
    assert S._bow_geometry(1.2, "attack", 0.52)["tip_up"] != idle["tip_up"]

    rest = pygame.Surface((240, 240), pygame.SRCALPHA)
    draw = pygame.Surface((240, 240), pygame.SRCALPHA)
    S._draw_sylara_elite(rest, 115, 130, 1, 1.0, "idle", 0.0)
    S._draw_sylara_elite(draw, 115, 130, 1, 1.0, "attack", 0.5)
    assert pygame.image.tobytes(rest, "RGBA") != \
        pygame.image.tobytes(draw, "RGBA")


def test_bow_points_layar_mengikuti_render_scale():
    """bow_points (dipakai trail 60 fps) menempel di busur yang digambar."""
    if _syfx is None:                      # pragma: no cover
        return
    hero = _ProbeEntity("sylara", 300.0, 300.0)
    hero.pulse = 1.2
    hero.facing = hero.direction = 1
    hero._sy_attack_progress = 0.52
    hero._sy_attack_active = True
    hero._sy_swing_mode = False
    hero._render_scale = 1.0
    geo = S._bow_geometry(hero.pulse, "attack", 0.52)
    (grip, tip, nock), action = _syfx.bow_points(hero, progress=0.52)
    assert action == "attack"
    # Tanpa skala canvas, titik layar == titik geometri renderer.
    assert abs(grip[0] - (hero.x + geo["grip"][0])) < 1e-6
    assert abs(nock[1] - (hero.y + geo["nock"][1])) < 1e-6
    # Jarak nock->ujung limb sepanjang kayu busur (bukan titik ngawur).
    limb = math.hypot(tip[0] - grip[0], tip[1] - grip[1])
    assert limb > 12.0


# ═══ 3. ANIMASI NYATA (BUKAN STICKER) ═════════════════════════════════════
def test_rig_has_real_animation_frames():
    frames = set()
    for i in range(6):
        surface = pygame.Surface((220, 240), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 110, 130, 1, i * 1.047, "walk", 0.0)
        frames.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(frames) >= 5, "walk tidak beranimasi (%d frame unik)" % len(
        frames)

    attacks = set()
    for i in range(6):
        surface = pygame.Surface((260, 250), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 120, 135, 1, i * 0.3, "attack",
                             i / 5.0)
        attacks.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(attacks) == 6, "attack hanya %d frame unik" % len(attacks)

    death = set()
    for i in range(4):
        surface = pygame.Surface((260, 250), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 120, 135, 1, 1.0, "death", 0.0,
                             death_frame=i)
        death.add(pygame.image.tobytes(surface, "RGBA"))
    assert len(death) == 4, "death hanya %d frame unik" % len(death)


def test_skill_state_changes_body():
    """Skill mengubah POSE badan (bukan cuma menempel FX di atasnya)."""
    base = pygame.Surface((280, 300), pygame.SRCALPHA)
    S._draw_sylara_elite(base, 140, 155, 1, 1.0, "idle", 0.0)
    base_bytes = pygame.image.tobytes(base, "RGBA")
    for kwargs in ({"focus": True}, {"wind": True}, {"shackle": True},
                   {"powershot": True}):
        surface = pygame.Surface((280, 300), pygame.SRCALPHA)
        S._draw_sylara_elite(surface, 140, 155, 1, 1.0, "idle", 0.0,
                             **kwargs)
        assert pygame.image.tobytes(surface, "RGBA") != base_bytes, kwargs


def test_portrait_lod_is_distinct():
    ui_source = open(os.path.join(ROOT, "ui_components", "_bundle.py"),
                     encoding="utf-8").read()
    assert "fake._portrait_hd = True" in ui_source

    normal = pygame.Surface((220, 220), pygame.SRCALPHA)
    portrait = pygame.Surface((220, 220), pygame.SRCALPHA)
    S._draw_sylara_elite(normal, 110, 130, 1, 1.0, "idle", 0.0,
                         detail=False)
    S._draw_sylara_elite(portrait, 110, 130, 1, 1.0, "idle", 0.0,
                         detail=True)
    assert pygame.image.tobytes(normal, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) >= len(colors(normal))


def test_silhouette_outline_exists():
    surface = pygame.Surface((220, 240), pygame.SRCALPHA)
    S._draw_sylara_elite(surface, 110, 130, 1, 1.2, "idle", 0.0)
    rect = surface.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            c = surface.get_at((x, y))
            if c.a > 120 and max(c.r, c.g, c.b) < 24:
                dark += 1
    assert dark >= 30, "selout siluet hilang (%d)" % dark


# ═══ 4. FX SKILL: WORLD-SPACE & TIDAK MENUTUPI BADAN ══════════════════════
def test_skill_fx_are_world_space():
    """Halo rumput Windrun tetap diukur world-px (radius 70) via _ring_r."""
    def render(fs):
        surface = pygame.Surface((760, 700), pygame.SRCALPHA)
        hero = _skill_unit("w", 110, scale=fs)
        S.draw_sylara(surface, hero, 380, 340)
        return surface

    def hits_at_radius(surf, r_px, cy_off, squash):
        hits = 0
        cx, cy = 380, 340 + cy_off
        for a in range(0, 360, 2):
            x = int(cx + math.cos(math.radians(a)) * r_px)
            y = int(cy + math.sin(math.radians(a)) * r_px * squash)
            if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                    and surf.get_at((x, y)).a > 40:
                hits += 1
        return hits

    for fs in (1.0, 0.50):
        surface = render(fs)
        r_px = int(70 / fs)
        n = hits_at_radius(surface, r_px, S.GROUND_LOCAL, S.GROUND_SQUASH)
        assert n > 15, "W halo tidak world-space pada fs=%s: %d/180" % (fs, n)


def test_fx_massa_besar_tidak_menutupi_badan():
    """Kontrak owner: 'R FX tidak menutupi badan'.

    SEMUA massa besar (cakram isi, cincin mengembang) digambar di lapisan
    TANAH sebelum badan, jadi piksel badan yang digambar orkestrator harus
    UTUH di frame akhir — kecuali aksen ringan di sekitar senjata.
    """
    watched = ("_draw_sylara_body", "_draw_sylara_windrun",
               "_draw_sylara_attack", "_draw_sylara_idle",
               "_draw_sylara_walk", "_draw_sylara_hurt")
    real = {name: getattr(S, name) for name in watched}

    for skill, timer, action in (("q", 96, "focus"), ("w", 96, "windrun"),
                                 ("e", 70, "shackle"),
                                 ("r", 26, "powershot")):
        recorded = []

        def make_spy(name, fn):
            def spy(*args, **kwargs):
                recorded.append((name, args, dict(kwargs)))
                return fn(*args, **kwargs)
            return spy

        for name in watched:
            setattr(S, name, staticmethod(make_spy(name, real[name])))
        try:
            scene = pygame.Surface((640, 640), pygame.SRCALPHA)
            hero = _skill_unit(skill, timer, x=320.0, y=320.0)
            S.draw_sylara(scene, hero, 320, 320)
        finally:
            for name in watched:
                setattr(S, name, staticmethod(real[name]))

        assert recorded, "badan tidak digambar untuk skill %s" % skill
        # Panggilan badan TERLUAR (untuk Windrun = _draw_sylara_windrun,
        # yang juga memakai fase internal sendiri) digambar ulang ke
        # surface bersih dengan argumen identik.
        name, args, kwargs = recorded[0]
        reference = pygame.Surface((640, 640), pygame.SRCALPHA)
        real[name](reference, *args[1:], **kwargs)

        # Pusat aksen depan yang memang boleh menyentuh badan: grip busur.
        # args bisa (surface, x, y, ...) atau (surface, boss, x, y, ...):
        # dua nilai numerik pertama adalah posisi anchor canvas.
        nums = [a for a in args[1:] if isinstance(a, (int, float))]
        anchor_x, anchor_y = int(nums[0]), int(nums[1])
        gx, gy = S._bow_grip_position(anchor_x, anchor_y,
                                      getattr(hero, "direction", 1),
                                      float(getattr(hero, "pulse", 0.0)),
                                      action)
        bad = total = 0
        for x in range(640):
            for y in range(640):
                c = reference.get_at((x, y))
                if c.a < 200:
                    continue
                if math.hypot(x - gx, y - gy) < 26:
                    continue
                total += 1
                if scene.get_at((x, y))[:3] != c[:3]:
                    bad += 1
        assert total > 400, "badan tidak terukur untuk %s" % skill
        assert bad <= total * 0.01, \
            "%s: %d/%d piksel badan tertutup FX massa" % (skill, bad, total)


def test_massa_besar_digambar_sebelum_badan():
    """Urutan lapisan: GROUND (massa besar) -> BADAN -> aksen depan."""
    order = []
    watched = ("_draw_powershot_ground", "_draw_focus_fire_ground",
               "_draw_windrun_ground", "_draw_shackle_ground",
               "_draw_sylara_body", "_draw_powershot_charge",
               "_draw_focus_fire_effect", "_draw_windrun_effect",
               "_draw_shackle_effect")
    real = {name: getattr(S, name) for name in watched}

    def make_spy(name, fn):
        def spy(*args, **kwargs):
            order.append(name)
            return fn(*args, **kwargs)
        return spy

    for skill, timer, ground, front in (
            ("q", 96, "_draw_focus_fire_ground", "_draw_focus_fire_effect"),
            ("w", 96, "_draw_windrun_ground", "_draw_windrun_effect"),
            ("e", 70, "_draw_shackle_ground", "_draw_shackle_effect"),
            ("r", 26, "_draw_powershot_ground", "_draw_powershot_charge")):
        del order[:]
        for name in watched:
            setattr(S, name, staticmethod(make_spy(name, real[name])))
        try:
            surface = pygame.Surface((640, 640), pygame.SRCALPHA)
            hero = _skill_unit(skill, timer, x=320.0, y=320.0)
            S.draw_sylara(surface, hero, 320, 320)
        finally:
            for name in watched:
                setattr(S, name, staticmethod(real[name]))
        assert ground in order, "%s: lapisan tanah tidak digambar" % skill
        assert "_draw_sylara_body" in order or \
            "_draw_sylara_windrun" in order, "%s: badan tidak digambar" % skill
        body_i = order.index("_draw_sylara_body") \
            if "_draw_sylara_body" in order else order.index(
                "_draw_sylara_windrun")
        assert order.index(ground) < body_i, \
            "%s: massa tanah digambar SETELAH badan" % skill
        if front in order:
            assert order.index(front) > body_i, \
                "%s: aksen depan digambar SEBELUM badan" % skill


def test_massa_tanah_benar_benar_digambar():
    """Sisi positif kontrak: massa besar memang ada di bidang tanah."""
    for skill, timer in (("q", 96), ("w", 96), ("e", 70), ("r", 26)):
        surface = pygame.Surface((760, 700), pygame.SRCALPHA)
        hero = _skill_unit(skill, timer)
        S.draw_sylara(surface, hero, 380, 340)
        ground_y = int(340 + S.GROUND_LOCAL)
        mass = 0
        for x in range(60, 700, 2):
            for y in range(ground_y - 30, ground_y + 34, 2):
                if surface.get_at((x, y)).a > 40:
                    mass += 1
                    break
        assert mass > 20, "%s: tidak ada massa FX di bidang tanah" % skill


def test_skill_visuals_render_with_masterwork():
    """Q/W/E/R tetap muncul setelah body rewrite dan tetap cache-safe."""
    from heroes import render_hero, clear_hero_sprite_cache
    clear_hero_sprite_cache()
    for skill, timer in (("q", 35), ("w", 70), ("e", 45), ("r", 60)):
        hero = _ProbeEntity("sylara", 150, 150)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = timer
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 260, 152)
        hero.target.alive = True
        surface = pygame.Surface((420, 360), pygame.SRCALPHA)
        render_hero("sylara", surface, hero, 150, 150)
        rect = surface.get_bounding_rect(min_alpha=5)
        assert rect.width > 45 and rect.height > 45, skill


# ═══ 5. PROYEKTIL VISUAL SERANGAN DASAR ═══════════════════════════════════
def test_basic_attack_spawn_arrow_canvas_fallback():
    """Serangan dasar melepas panah angin bertema hero di titik rilis.

    Permintaan owner: proyektil visual bertema hero saat basic attack.
    Jalur canvas (fallback tanpa FX live) harus spawn WindBolt dari nock
    menuju target — murni visual (damage 0), tanpa skill aktif sekalipun.
    """
    surface = pygame.Surface((260, 280), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 240, 130)
    target.alive = True

    hero = _ProbeEntity("sylara", 130, 150)
    hero.pulse = 1.25
    hero.direction = hero.facing = 1
    hero.active_skill = None
    hero.target = target
    hero._sy_swing_mode = False
    hero._sy_shot_spawned = False

    saved = S._FX_LIVE.v
    S._FX_LIVE.v = False          # paksa jalur canvas (tanpa FX live)
    try:
        # Sebelum jendela rilis: belum ada panah.
        hero._sy_attack_progress = 0.30
        S._draw_sylara_attack(surface, hero, 130, 150)
        assert len(getattr(hero, "_sy_projectiles", [])) == 0

        # Di jendela rilis (ap 0.5-0.6): panah angin terbang ke target.
        hero._sy_attack_progress = 0.55
        S._draw_sylara_attack(surface, hero, 130, 150)
        items = getattr(hero, "_sy_projectiles", [])
        assert len(items) == 1
        bolt = items[0]
        assert isinstance(bolt, S.WindBolt)
        assert bolt.target is target
        assert bolt.damage == 0, "proyektil basic attack harus visual saja"

        # Anti-dobel: frame rilis berikutnya tidak menambah panah.
        S._draw_sylara_attack(surface, hero, 130, 150)
        assert len(getattr(hero, "_sy_projectiles", [])) == 1

        # Ayunan selesai: kunci rilis dibuka lagi untuk serangan berikut.
        hero._sy_attack_progress = 0.95
        S._draw_sylara_attack(surface, hero, 130, 150)
        assert hero._sy_shot_spawned is False

        # Saat FX live aktif, canvas TIDAK spawn (director pemiliknya).
        hero._sy_projectiles = []
        hero._sy_shot_spawned = False
        hero._sy_attack_progress = 0.55
        S._FX_LIVE.v = True
        S._draw_sylara_attack(surface, hero, 130, 150)
        assert len(hero._sy_projectiles) == 0

        # Sapuan melee (swing) tidak menembakkan panah.
        hero._sy_projectiles = []
        hero._sy_shot_spawned = False
        hero._sy_swing_mode = True
        S._FX_LIVE.v = False
        S._draw_sylara_attack(surface, hero, 130, 150)
        assert len(hero._sy_projectiles) == 0
    finally:
        S._FX_LIVE.v = saved


def test_skill_attack_masih_spawn_arrow_saat_fx_live():
    """Skill tetap melepas panahnya walau lapisan FX live aktif."""
    surface = pygame.Surface((280, 300), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 250, 140)
    target.alive = True

    hero = _ProbeEntity("sylara", 140, 150)
    hero.pulse = 1.0
    hero.direction = hero.facing = 1
    hero.active_skill = "e"
    hero.target = target
    hero._sy_swing_mode = False
    hero._sy_shot_spawned = False

    saved = S._FX_LIVE.v
    S._FX_LIVE.v = True
    try:
        hero._sy_attack_progress = 0.55
        S._draw_sylara_attack(surface, hero, 140, 150)
        items = getattr(hero, "_sy_projectiles", [])
        assert len(items) == 1
    finally:
        S._FX_LIVE.v = saved


def test_touchdown_panic_tanpa_impact_fx():
    """Touchdown panah visual hanya percikan lembut (tanpa hit-stop/shake)."""
    from heroes import combat_feel as FEEL
    surface = pygame.Surface((300, 300), pygame.SRCALPHA)
    target = _ProbeEntity("dummy", 260, 140)
    target.alive = True
    hero = _ProbeEntity("sylara", 140, 150)
    hero.pulse = 1.0
    hero.direction = hero.facing = 1
    hero.target = target
    hero._sy_projectiles = []

    saved = S._FX_LIVE.v
    S._FX_LIVE.v = False
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    try:
        S._spawn_basic_shot(hero, 140, 150)
        bolt = hero._sy_projectiles[0]
        bolt.speed = 40.0
        frames = 0
        while bolt.alive and frames < 60:
            bolt.update()
            bolt.draw(surface, 0.3)
            frames += 1
        assert not bolt.alive, "panah tidak pernah mendarat"
        for _ in range(12):
            bolt.draw(surface, 0.3)
            bolt.update()
        assert FEEL.HITSTOP.frames == 0
        assert FEEL.SHAKE.shake_strength == 0.0
    finally:
        S._FX_LIVE.v = saved
        FEEL.HITSTOP.clear()
        FEEL.SHAKE.clear()


# ═══ 6. LAYERING INSTALL (PARITAS KELUARGA V1) ════════════════════════════
def test_v1_install_layering():
    """install() mengembalikan subclass dari namespace legacy yang diberi."""
    class _FakeLegacy:
        PALETTE = {"legacy_key": (1, 2, 3)}

    wrapped = _install_v1(_FakeLegacy)
    assert issubclass(wrapped, _FakeLegacy)
    assert wrapped.PALETTE["legacy_key"] == (1, 2, 3)
    # Kunci kritis live FX tetap ada meski base minimal.
    for key in ("hood_mid", "cloth_mid", "leather_mid", "wood_mid",
                "wind_mid", "arrow_feather", "hair_dark"):
        assert key in wrapped.PALETTE


if __name__ == "__main__":
    test_masterwork_is_procedural()
    test_material_details_and_pose()
    test_bow_geometry_is_pose_driven()
    test_bow_points_layar_mengikuti_render_scale()
    test_rig_has_real_animation_frames()
    test_skill_state_changes_body()
    test_portrait_lod_is_distinct()
    test_silhouette_outline_exists()
    test_skill_fx_are_world_space()
    test_fx_massa_besar_tidak_menutupi_badan()
    test_massa_besar_digambar_sebelum_badan()
    test_massa_tanah_benar_benar_digambar()
    test_skill_visuals_render_with_masterwork()
    test_basic_attack_spawn_arrow_canvas_fallback()
    test_skill_attack_masih_spawn_arrow_saat_fx_live()
    test_touchdown_panic_tanpa_impact_fx()
    test_v1_install_layering()
    print("SEMUA TEST SYLARA V1 MASTERWORK LULUS")
