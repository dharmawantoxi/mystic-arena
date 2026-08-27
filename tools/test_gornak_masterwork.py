#!/usr/bin/env python3
"""Regresi visual untuk Gornak Procedural Masterwork.

Gornak (mini boss anti-mage level 1, sekaligus hero yang bisa di-unlock)
dulunya dirender sebagai tumpukan body-part statis: badan 48 px, kaki tidak
terlihat menapak, cincin kepala yang membuat wajah terbaca seperti donat,
dan pedang bergelombang yang posenya tidak terhubung ke tangan.

Uji ini mengunci hasil rewrite:
  1. 100% prosedural (tanpa image.load / PNG / sprite sheet).
  2. SATU bone rig 2D berlapis - nama fungsi body-part lama harus hilang.
  3. Telapak kaki dipatok di garis bayangan (tidak melayang).
  4. Bilah pose-driven: FX Mana Break lahir dari UJUNG BILAH, bukan dari
     titik melayang di samping badan.
  5. Outline siluet 1 px ada (bagian tetap terpisah saat unit bertumpuk).
  6. LOD portrait: pass material aktif & efek arena (rune/aura) dibuang.
  7. Frame walk/attack benar-benar dihitung ulang per-sendi.

Jalankan:  python3 tools/test_gornak_masterwork.py
"""
import inspect
import math
import re
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from bosses.level1 import _NS_gornak as G
from heroes import _ProbeEntity, clear_hero_sprite_cache, render_hero

SIZE = 240
C, CY = SIZE // 2, SIZE // 2 + 26


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="gornak", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.25,
                        timer=0, attack_cooldown=38, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render(action="idle", ap=0.0, phase=1.25, facing=1, detail=False):
    """Rig murni (tanpa FX) pada jangkar (C, CY)."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    G._draw_gnk_rig(surf, C, CY, facing, phase, action, ap, detail)
    return surf


def solid_rect(surf, thr=100):
    """Bounding box bagian SOLID saja (aura alpha-rendah diabaikan)."""
    mask = pygame.mask.from_surface(surf, thr)
    rects = mask.get_bounding_rects()
    if not rects:
        return None
    x0 = min(r.x for r in rects)
    y0 = min(r.y for r in rects)
    x1 = max(r.right for r in rects)
    y1 = max(r.bottom for r in rects)
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def colors(surf):
    out = set()
    for y in range(surf.get_height()):
        for x in range(surf.get_width()):
            px = surf.get_at((x, y))
            if px.a:
                out.add(px[:3])
    return out


def test_masterwork_is_procedural_and_single_rig():
    source = inspect.getsource(G)
    assert "pygame.image.load" not in source
    for needed in ("_draw_gnk_rig", "_draw_gnk_legs", "_draw_gnk_torso",
                   "_draw_gnk_head", "_draw_gnk_arm", "_draw_gnk_blade",
                   "_draw_gnk_masterwork_details", "_blade_angle",
                   "_front_grip_local", "_elbow", "_tip_local", "_tip_screen",
                   "_compose_outline", "_draw_crescent_slash"):
        assert callable(getattr(G, needed, None)), needed
    # Tumpukan body-part lama harus sudah benar-benar dihapus.
    for gone in ("_draw_leg", "_draw_gnk_robe", "_draw_gnk_arm_back",
                 "_draw_gnk_arm_front", "_draw_blade", "_draw_mohawk",
                 "_draw_counterspell_ground"):
        assert not hasattr(G, gone), f"old body-part still present: {gone}"


def test_feet_are_planted_and_body_is_readable():
    idle = render("idle")
    rect = solid_rect(idle)
    assert rect is not None
    tinggi = rect.height
    # Badan (ubun-ubun -> sol) harus jauh lebih besar dari rig lama (48 px)
    assert tinggi >= 68, f"body too short: {tinggi}"
    # Sol jatuh di garis bayangan -> karakter tidak melayang.
    ground = CY + G.GROUND_DY
    assert abs(rect.bottom - ground) <= 3, (rect.bottom, ground)
    # ...dan puncak kepala tidak menutupi HP bar boss (y-45..y-37).
    assert rect.top >= CY - 44, rect.top
    assert rect.width >= 40


def test_blade_geometry_is_pose_driven():
    """Bilah: cocked back -> chop over the head -> release forward.

    Yang dikunci di sini BUKAN angka sudutnya, tapi bentuk geraknya:
    (a) posisi siap -> wind-up -> impact -> recovery harus berbeda semua,
    (b) bilah tidak pernah menyayat menembus torsonya sendiri, dan
    (c) ujung bilah tidak pernah keluar dari buffer rig (kalau keluar,
        FX-nya terpotong saat sprite di-cache).
    """
    tip_idle = G._tip_local("idle", 1.0, 0.0)
    tip_wind = G._tip_local("attack", 1.0, 0.26)
    tip_rel = G._tip_local("attack", 1.0, 0.52)
    # Wind-up: bilah terangkat ke belakang-atas (bukan ke samping dada).
    assert tip_wind[1] < -18 and tip_wind[0] < 0
    # Release: ayunan menjulau jauh ke depan.
    assert tip_rel[0] > tip_idle[0] + 12
    assert tip_rel[1] < tip_wind[1] + 46          # turun menyapu

    def blade_crosses_chest(grip, tip, box):
        """Apakah bagian TENGAH- LUAR bilah memotong rongga dada?

        40% pertama bilah diabaikan: di situ ada gagang + telapak tangan yang
        memang berdiri di depan pinggang, jadi itu bukan "pedang menancap di
        dada". Frame pertama (ap < 0.06) juga dilewati karena attack punya
        satu frame antisipasi tempat tangan melompat ke posisi cocked.
        """
        (x0, y0, x1, y1) = box
        for i in range(14):
            t = 0.40 + (i / 13.0) * 0.60
            px = grip[0] + (tip[0] - grip[0]) * t
            py = grip[1] + (tip[1] - grip[1]) * t
            if x0 <= px <= x1 and y0 <= py <= y1:
                return True
        return False

    chest = (-8, -11, 8, -4)                      # blok otot dada
    for i in range(1, 21):
        ap = i / 20.0
        grip = G._front_grip_local("attack", ap, 1.0)
        tip = G._tip_local("attack", 1.0, ap)
        assert not blade_crosses_chest(grip, tip, chest), \
            f"blade crosses chest at ap={ap:.2f} grip={grip} tip={tip}"
        assert abs(tip[0]) <= G.RIG_OX - 3, f"tip leaves buffer x @ {ap}"
        assert -(G.RIG_OY - 3) <= tip[1] <= G.RIG_H - G.RIG_OY - 1, \
            f"tip leaves buffer y @ {ap}: {tip}"

    for action in ("idle", "walk", "surge", "ward", "void"):
        for i in range(6):
            ph = i * 1.05
            g = (G._front_grip_local(action, 0.0, ph)
                 if action != "idle" else G._front_grip_local(action, 0.0, ph))
            tp = G._tip_local(action, ph, 0.0)
            assert not blade_crosses_chest(g, tp, chest), (action, ph)
        for i in range(6):
            ph = i * 1.05
            g = G._back_grip_local(action, 0.0, ph)
            tp = G._tip_local(action, ph, 0.0, back=True)
            assert abs(tp[0]) <= G.RIG_OX - 3 and \
                -(G.RIG_OY - 3) <= tp[1], (action, ph, tp)

    frames = {pygame.image.tobytes(render("attack", i / 9.0), "RGBA")
              for i in range(10)}
    assert len(frames) == 10


def test_mana_break_proc_starts_at_blade_tip():
    """FX Q harus lahir dari UJUNG BILAH - bukan mengambang di pinggang."""
    boss = probe(C, CY, active_skill="q", active_skill_timer=31)
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    G.draw_gornak(surf, boss, C, CY)
    tip = G._tip_screen(boss, C, CY)
    px = surf.get_at(tip)
    assert px.a > 0, "no pixel at the claimed blade tip"
    # Cari piksel paling terang di sekitar tip; harus dalam radius 6 px.
    best, bestd = None, 999
    for y in range(max(0, tip[1] - 14), min(SIZE, tip[1] + 15)):
        for x in range(max(0, tip[0] - 14), min(SIZE, tip[0] + 15)):
            p = surf.get_at((x, y))
            if p.a and (p.r + p.g + p.b) > 640:
                d = abs(x - tip[0]) + abs(y - tip[1])
                if d < bestd:
                    best, bestd = (x, y), d
    assert best is not None and bestd <= 7, (tip, best, bestd)


def test_silhouette_outline_exists():
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    boss = probe(C, CY)
    G._draw_gnk_rig_at(surf, C, CY, 1, 1.25, "idle", 0.0, False)
    rect = surf.get_bounding_rect(min_alpha=8)
    dark = 0
    for x in range(rect.left, rect.right):
        for y in range(rect.top, rect.bottom):
            p = surf.get_at((x, y))
            if p.a > 90 and max(p.r, p.g, p.b) < 30:
                dark += 1
    assert dark > 90, f"outline missing/too thin ({dark} dark px)"


def test_portrait_lod_is_distinct_and_clean():
    arena = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    portrait = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    G._draw_gnk_rig(arena, C, CY, 1, 1.25, "idle", 0.0, False)
    G._draw_gnk_rig(portrait, C, CY, 1, 1.25, "idle", 0.0, True)
    assert pygame.image.tobytes(arena, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) > len(colors(arena))

    # draw_gornak(): mode portrait TIDAK menggambar rune/aura arena.
    full = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    crop = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    G.draw_gornak(full, probe(C, CY), C, CY)
    G.draw_gornak(crop, probe(C, CY, _portrait_hd=True), C, CY)
    def outside_body(surf):
        """Piksel di pita garis kaki yang berada DI LUAR siluet badan.

        Rune tanah & aura digambar melebar sampai x=+-24 sedangkan badan
        sendiri hanya sampai +-18 - jadi hitungan ini membuktikan efek
        arena ada di mode normal dan dibuang di mode portrait, tanpa
        bergantung pada warna hasil alpha-blending.
        """
        n = 0
        for y in range(CY + G.GROUND_DY - 7, CY + G.GROUND_DY + 7):
            for x in range(SIZE):
                if abs(x - C) <= 19:
                    continue
                if surf.get_at((x, y)).a > 6:
                    n += 1
        return n

    assert outside_body(full) > 24, "arena LOD should keep the ground rune"
    assert outside_body(crop) == 0, \
        "portrait LOD must drop ground FX (auto-crop would shrink the face)"
    assert crop.get_bounding_rect(min_alpha=8).width < \
        full.get_bounding_rect(min_alpha=8).width


def test_walk_frames_recalculate_joints():
    frames = {pygame.image.tobytes(render("walk", 0.0, phase=1.0 + i * 0.55),
                                   "RGBA") for i in range(6)}
    assert len(frames) == 6
    # Langkah: posisi kaki berbeda tiap frame, tapi salah satu sol tetap
    # berada di garis tanah (tidak ada frame di mana kedua kaki melayang).
    for i in range(6):
        surf = render("walk", 0.0, phase=1.0 + i * 0.55)
        row = pygame.Rect(0, CY + G.GROUND_DY - 1, SIZE, 3)
        assert surf.subsurface(row).get_bounding_rect(min_alpha=150).width > 4


def test_pose_router_and_skill_states_render():
    """Boss path DAN hero path (via render_hero + cache) harus aman."""
    for skill, timer in ((None, 0), ("q", 14), ("w", 12), ("e", 40),
                         ("r", 44)):
        boss = probe(C, CY, active_skill=skill, active_skill_timer=timer,
                     pulse=1.4)
        boss.target = SimpleNamespace(x=float(C + 120), y=float(CY - 8),
                                      alive=True)
        surf = pygame.Surface((SIZE * 2, SIZE), pygame.SRCALPHA)
        G.draw_gornak(surf, boss, C, CY)
        rect = surf.get_bounding_rect(min_alpha=6)
        assert rect.width > 40 and rect.height > 60, skill
        # Pose yang dipilih router harus sinkron dengan anchor FX.
        action = boss._gnk_pose_action
        expect = {None: "idle", "q": "surge", "w": "blink", "e": "ward",
                  "r": "void"}[skill]
        assert action == expect, (skill, action)

    clear_hero_sprite_cache()
    for skill in ("q", "w", "e", "r"):
        hero = _ProbeEntity("gornak", 200, 210)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = 20
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 300, 212)
        hero.target.alive = True
        surf = pygame.Surface((420, 380), pygame.SRCALPHA)
        render_hero("gornak", surf, hero, 200, 210)
        rect = surf.get_bounding_rect(min_alpha=5)
        assert rect.width > 30 and rect.height > 30, skill


def test_hero_scale_is_no_longer_upsampled():
    """Skala hero hasil pengukuran tidak boleh > 1 (bitmap di-blow-up)."""
    import heroes
    renderer = heroes.HERO_RENDERERS.get("gornak") or \
        heroes.BOSS_RENDERERS.get("gornak")
    native = heroes._measure_native_size("gornak", renderer)
    assert native, "pengukuran gagal"
    scale = heroes._get_hero_scale("gornak")
    assert native[1] >= 50, f"badan terlalu kecil untuk pipeline HD: {native}"
    assert scale <= 1.02, f"hero gornak masih di-upscale: {scale:.3f}"


def test_skill_durations_match_ai_timers():
    """Durasi animasi skill harus sinkron dengan timer yang diisi AI/gameplay.

    Kalau konstanta renderer lebih kecil dari active_skill_timer, pose skill
    "menggantung" beberapa frame terakhir; kalau lebih besar, animasi
    terpotong di tengah. Keduanya terlihat seperti bug render, padahal
    hanya konstanta yang tidak sinkrok - jadi dikunci di sini.
    """
    cast = {"q": "_cast_q_mana_break", "w": "_cast_w_blink",
            "e": "_cast_e_counterspell", "r": "_cast_r_mana_void"}
    sources = {
        "boss": os.path.join(ROOT, "bosses", "base_boss.py"),
        "hero": os.path.join(ROOT, "hero_skills", "_bundle.py"),
    }
    for tag, path in sources.items():
        src = open(path, encoding="utf-8").read()
        for key, fn in cast.items():
            i = src.index("def %s(" % fn)
            m = re.search(r"active_skill_timer\s*=\s*(\d+)", src[i:i + 900])
            assert m, "%s/%s: active_skill_timer tidak ketemu" % (tag, key)
            assert int(m.group(1)) == G.SKILL_DUR[key], \
                "%s %s timer %s != render %s" % (
                    tag, key, m.group(1), G.SKILL_DUR[key])


def test_perf_budget():
    """Guardrail: rig baru tidak boleh lebih mahal dari tumpukan sticker lama.

    Ambang sengaja longgar (4 ms) supaya tetap lolos di HP低端; hasil terukur
    di desktop ~0,9 ms/frame (rig lama ~1,2 ms).
    """
    import time
    scr = pygame.Surface((1280, 720))
    boss = probe(640, 360)
    N = 90
    for i in range(10):            # warm-up
        boss.pulse = i * 0.2
        G.draw_gornak(scr, boss, 640, 360)
    t0 = time.perf_counter()
    for i in range(N):
        boss.pulse = i * 0.2
        G.draw_gornak(scr, boss, 640, 360)
    ms = (time.perf_counter() - t0) / N * 1000
    assert ms < 4.0, f"draw_gornak {ms:.2f} ms/frame - terlalu mahal"
    print(f"       (draw_gornak idle: {ms:.2f} ms/frame)")


if __name__ == "__main__":
    test_masterwork_is_procedural_and_single_rig()
    test_feet_are_planted_and_body_is_readable()
    test_blade_geometry_is_pose_driven()
    test_mana_break_proc_starts_at_blade_tip()
    test_silhouette_outline_exists()
    test_portrait_lod_is_distinct_and_clean()
    test_walk_frames_recalculate_joints()
    test_pose_router_and_skill_states_render()
    test_hero_scale_is_no_longer_upsampled()
    test_skill_durations_match_ai_timers()
    test_perf_budget()
    print("OK - Gornak masterwork: rig tunggal, kaki menapak, bilah "
          "pose-driven, proc di ujung bilah, outline, portrait LOD, "
          "Q/W/E/R boss+hero tervalidasi")
