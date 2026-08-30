#!/usr/bin/env python3
"""Regresi visual untuk Gornak Pixel Masterwork v2 + Skill FX v2.1.

Gornak (mini boss anti-mage level 1, sekaligus hero yang bisa di-unlock)
dirender 100% prosedural mengikuti standar Thorne v2 / v2.1: ramp 4-5
band, selout, tuft, specular cluster, dither, dan FX world-space.

Uji ini mengunci hasil rewrite:
  1. 100% prosedural (tanpa image.load / PNG / sprite sheet).
  2. SATU bone rig 2D berlapis - nama fungsi body-part lama harus hilang.
  3. Telapak kaki dipatok di garis bayangan (tidak melayang).
  4. Bilah pose-driven: FX Mana Break lahir dari UJUNG BILAH, bukan dari
     titik melayang di samping badan.
  5. Outline siluet 1 px ada (bagian tetap terpisah saat unit bertumpuk).
  6. LOD portrait: pass material aktif & efek arena (rune/aura) dibuang.
  7. Frame walk/attack benar-benar dihitung ulang per-sendi.
  8. Kosakata FX v2.1 (_fx_scale, _spark_star, ...) tersedia.
  9. Telegraph E=100 / R=180 px dunia (kompensasi 1/_render_scale).

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


def clipped_by_buffer(action, ap, phase):
    """True kalau hasil render rig Menyentuh tepi buffer RIG_W x RIG_H.

    Buffer yang kecipil akan memotong bilah/jubah saat sprite di-cache
    (potongan hilang di kanan/kiri), jadi ini diperiksa dari bounding box
    render sebenarnya, bukan dari angka batas.
    """
    buf = pygame.Surface((G.RIG_W, G.RIG_H), pygame.SRCALPHA)
    G._draw_gnk_rig(buf, G.RIG_OX, G.RIG_OY, 1, phase, action, ap, False)
    r = buf.get_bounding_rect(min_alpha=1)
    return r.width == 0 or r.left <= 0 or r.top <= 0 or \
        r.right >= G.RIG_W or r.bottom >= G.RIG_H


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
                   "_compose_outline", "_draw_crescent_slash",
                   "_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
                   "_jagged_crack", "_tuft_points", "_static",
                   "_dither_dots", "_ring_r", "_world_to_local"):
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
    # Badan (ubun-ubun -> sol) harus jauh lebih besar dari rig lama (48 px)
    # dan segaris dengan keluarga mini boss (morgath 82, drakar 138).
    assert rect.height >= 100, f"body too short: {rect.height}"
    # Siluet harus MEMENUHI kotak, bukan tiang sempit: W/H keluarga
    # hero = 0.90-1.17 (rig lama gornak cuma 0.61).
    assert rect.width / rect.height >= 0.85, \
        f"siluet terlalu sempit: {rect.width}x{rect.height}"
    assert rect.width >= 96, rect.width
    # Sol jatuh di garis bayangan -> karakter tidak melayang.
    ground = CY + G.GROUND_DY
    assert abs(rect.bottom - ground) <= 3, (rect.bottom, ground)
    # Puncak krist mohawk tetap di atas HP bar tanpa membawa seluruh kepala
    # masuk ke pita bar (bar mini boss: y-45..y-37); LIFT menjaga wajah di
    # bawahnya.
    assert rect.top >= CY - 58, rect.top


def test_size_matches_the_family():
    """Ukuran Gornak = ukuran karakter lain (keluhan: terlalu kecil).

    Dua jalur diuji terhadap rujukan yang benar-benar dipakai pemain:
      * boss di arena: bbox badan padat dibandingkan morgath & drakar;
      * hero di lane/Hero Shop: hasil AKHIR (setelah auto-scale pipeline HD
        heroes/__init__.py) dibandingkan Grimjaw & Kaizen.
    """
    import heroes
    from heroes import _ProbeEntity, HERO_RENDERERS, BOSS_RENDERERS

    def hero_final(name):
        c = 200
        canvas = pygame.Surface((400, 400), pygame.SRCALPHA)
        h = _ProbeEntity(name, c, c)
        h.pulse = 1.35
        h.direction = 1
        h.team = "blue"
        rend = HERO_RENDERERS.get(name) or BOSS_RENDERERS.get(name)
        h._render_scale = 1.0
        rend(canvas, h, c, c)
        r = canvas.get_bounding_rect(min_alpha=100)
        sc = heroes._get_hero_scale(name)
        return int(r.height * sc), int(r.width * sc)

    gh, gw = hero_final("gornak")
    for sib in ("grimjaw", "kaizen"):
        sh, sw = hero_final(sib)
        assert abs(gh - sh) <= 0.14 * sh, f"hero gornak H={gh} vs {sib} H={sh}"
        assert abs(gw - sw) <= 0.18 * sw, f"hero gornak W={gw} vs {sib} W={sw}"
    # jangan ada yang di-upscale (bitmap di-blow-up = kabur)
    assert heroes._get_hero_scale("gornak") <= 1.02

    def boss_bbox(name, fn):
        surf = pygame.Surface((460, 460), pygame.SRCALPHA)
        b = probe(230, 230)
        b.boss_type = name
        fn(surf, b, 230, 230)
        m = pygame.mask.from_surface(surf, 100)
        rs = m.get_bounding_rects()
        x0 = min(q.x for q in rs); y0 = min(q.y for q in rs)
        x1 = max(q.right for q in rs); y1 = max(q.bottom for q in rs)
        return y1 - y0, x1 - x0

    import bosses.level1 as L
    gh2, gw2 = boss_bbox("gornak", L.draw_gornak)
    mh, mw = boss_bbox("morgath", L.draw_morgath)          # H82 W120
    dh, dw = boss_bbox("drakar", L.draw_drakar)             # H138 W190 (naga)
    ah, aw = boss_bbox("abaddon", L.draw_abaddon)           # true boss
    # Tidak boleh lagi jadi "tiang kecil" di samping mini boss lain:
    assert gh2 >= mh * 1.05, f"boss gornak H={gh2} vs morgath H={mh}"
    assert gh2 >= dh * 0.72, f"boss gornak H={gh2} vs drakar H={dh}"
    assert gw2 >= mw * 0.85, f"boss gornak W={gw2} vs morgath W={mw}"
    # ...tapi mini boss tetap lebih kecil dari true boss level yang sama.
    assert gh2 <= ah * 1.00, f"boss gornak H={gh2} >= true boss {ah}"
    assert gw2 <= aw * 1.00, f"boss gornak W={gw2} >= true boss {aw}"


def test_blade_geometry_is_pose_driven():
    """Bilah: cocked back -> chop over the head -> release forward.

    Yang dikunci di sini BUKAN angka sudutnya, tapi bentuk geraknya:
    (a) posisi siap -> wind-up -> impact -> recovery harus berbeda semua,
    (b) bilah tidak pernah menyayat menembus torsonya sendiri, dan
    (c) ujung bilah tidak pernah keluar dari buffer rig (kalau keluar,
        FX-nya terpotong saat sprite di-cache).
    """
    tip_idle = G._tip_local("idle", 1.0, 0.0)
    tip_wind = G._tip_local("attack", 1.0, G._attack_curve(0.14))
    tip_rel = G._tip_local("attack", 1.0, G._attack_curve(0.62))
    # Wind-up: kedua bilah terangkat TINGGI (di depan/ belakang wajah),
    # tidak pernah lewat datar setinggi dada.
    assert tip_wind[1] < -18
    assert tip_wind[1] < tip_idle[1] - 24
    # Impact: ayunan sudah turun jauh menyapu ke bawah-depan.
    assert tip_rel[1] > tip_idle[1] + 10
    assert tip_rel[1] > tip_wind[1] + 46

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
    assert not hasattr(G, "_blade_angle_legacy")
    for i in range(1, 21):
        ap = G._attack_curve(i / 20.0)
        grip = G._front_grip_local("attack", ap, 1.0)
        tip = G._tip_local("attack", 1.0, ap)
        assert not blade_crosses_chest(grip, tip, chest), \
            f"blade crosses chest at ap={ap:.2f} grip={grip} tip={tip}"
        # Tidak boleh terpotong oleh buffer rig: diperiksa langsung dari
        # bounding box hasil render (bukan dari angka batas asimetris).
        assert not clipped_by_buffer("attack", ap, 1.0), \
            f"rig clipped by buffer @ attack ap={ap:.2f}"

    for action in ("idle", "walk", "surge", "ward", "void"):
        for i in range(6):
            ph = i * 1.05
            g = (G._front_grip_local(action, 0.0, ph)
                 if action != "idle" else G._front_grip_local(action, 0.0, ph))
            tp = G._tip_local(action, ph, 0.0)
            assert not blade_crosses_chest(g, tp, chest), (action, ph)
        for i in range(4):
            ph = i * 1.05
            assert not clipped_by_buffer(action, 0.0, ph), \
                f"rig clipped by buffer @ {action} phase={ph:.2f}"

    frames = {pygame.image.tobytes(render("attack", i / 9.0), "RGBA")
              for i in range(10)}
    assert len(frames) == 10


def test_attack_timing_has_impact_hold():
    """Anticipation -> ayunan cepat -> HOLD di impact -> follow-through.

    Yang bikin serangan 2D terasa murah bukan jumlah frame, tapi tidak
    adanya freeze 1-2 frame di impact. Diuji sebagai SIFAT kurva (bukan
    angka segmen, supaya kurva masih boleh di-tune):
      * monoton naik  -> bilah tidak pernah terlihat mundur
      * ada jendela raw >= 0.10 yang pose-time-nya nyaris tidak bergerak
      * laju maksimum > 4x laju di jendela hold itu
      * endpoint 0 dan 1 (tidak ada snap di awal/akhir ayunan)
    """
    N = 400
    seq = [G._attack_curve(i / N) for i in range(N + 1)]
    assert all(b >= a - 1e-9 for a, b in zip(seq, seq[1:])), "kurva mundur"
    assert abs(seq[0]) < 1e-9 and abs(seq[-1] - 1.0) < 0.02, (seq[0], seq[-1])

    step = 3 / N                                   # ~3 frame @60fps
    rate = [(seq[i + 1] - seq[i]) / step for i in range(N)]
    lo, hi = min(rate), max(rate)
    assert hi > 4.0 * max(lo, 1e-6), (lo, hi)      # ada kontras cepat/lambat
    quiet = [i for i, r in enumerate(rate) if r <= hi * 0.25]
    assert quiet, "tidak ada hold sama sekali"
    span = (max(quiet) - min(quiet)) / N
    assert span >= 0.08, f"jendela impact cuma {span:.3f} (perlu >= 0.08)"


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
    def painted(surf):
        """Jumlah piksel tergambar (termasuk yang transparan tipis).

        Mode arena menambah aura + rune tanah + bayangan (permukaan besar
        alpha lembut); mode portrait hanya rig. Warna tidak dipakai sebagai
        acuan karena SRCALPHA di pygame menurunkan nilai RGB saat blending,
        jadi jumlah piksel adalah sinyal yang stabil.
        """
        n = 0
        for y in range(surf.get_height()):
            for x in range(surf.get_width()):
                if surf.get_at((x, y)).a > 6:
                    n += 1
        return n

    a_px, p_px = painted(full), painted(crop)
    # FX arena (aura + rune + shadow) menambah >18% piksel tergambar; kalau
    # someday ada yang menyalakannya lagi di mode portrait, rasio ini turun
    # ke ~1.0 dan test ini gagal.
    assert a_px > p_px * 1.18, \
        f"portrait harus membuang FX arena (painted {a_px} vs {p_px})"


def test_secondary_motion_exists():
    """Kepala, debu langkah, dan kedip: gerak sekunder yang memisahkan
    rig "hidup" dari rig "menggeser sticker".
    """
    # (a) offset kepala berbeda untuk idle / walk / attack / void
    heads = {a: G._head_bob(a, 2.1, 0.5)
             for a in ("idle", "walk", "attack", "void", "ward")}
    assert len(set(heads.values())) >= 4, heads
    # walk mengayunkan kepala berlawanan arah langkah
    assert heads["walk"][1] <= heads["idle"][1]
    # (b) kepala TIDAK direkat ke torso: head bob harus mengubah posisi
    # piksel wajah antar frame walk.
    frames = set()
    for i in range(5):
        surf = pygame.Surface((240, 240), pygame.SRCALPHA)
        G._draw_gnk_rig(surf, 120, 120, 1, 0.9 * i, "walk", 0.0, False)
        frames.add(pygame.image.tobytes(
            surf.subsurface(pygame.Rect(96, 60, 48, 34)), "RGBA"))
    assert len(frames) >= 4, "kepala statis saat berjalan"
    # (c) debu langkah hanya ada di walk, dan menghilang saat melayang
    dust_walk = pygame.Surface((240, 240), pygame.SRCALPHA)
    G._draw_footfall_dust(dust_walk, 120, 120, 1, 0.0)
    assert dust_walk.get_bounding_rect(min_alpha=6).width > 8, \
        "footfall dust tidak tergambar"
    # fase di mana telapak TERANGKAT (|sin(phase*1.15)| ~ 1) -> tidak boleh
    # ada debu, kalau tidak karakter meninggalkan jejak di udara.
    import math as _m
    lifted = _m.pi / 2 / 1.15
    still = pygame.Surface((240, 240), pygame.SRCALPHA)
    G._draw_footfall_dust(still, 120, 120, 1, lifted)
    assert still.get_bounding_rect(min_alpha=6).width == 0


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


def test_hero_visual_quality():
    """Kunci kualitas VISUAL jalur hero (bukan cuma ukuran).

    Empat hal yang dulu membuat Gornak-as-hero kalah dari grimjaw/kaizen:
      1. portrait Hero Shop terpotong di kanvas 160x160 (bilah depan keluar
         tepi) -> sekarang konten dipusatkan pada bbox-nya;
      2. wajah jadi blob tanpa fitur -> mata menyala harus benar-benar ada
         di kotak kepala;
      3. identitas warna hilang -> warna tema ungu harus ada DI BADAN
         (permata pelat/pauldron, rim light), bukan cuma di efek arena;
      4. kaki menyatu jadi satu tiang ungu -> di bawah loincloth harus ada
         DUA kolom padat terpisah.
    """
    # (1) portrait: tidak boleh menyentuh tepi kanvas 160x160
    canvas = pygame.Surface((160, 160), pygame.SRCALPHA)
    fake = probe(80, 90, _portrait_hd=True)
    G.draw_gornak(canvas, fake, 80, 90)
    box = canvas.get_bounding_rect(min_alpha=10)
    assert box.left >= 2 and box.top >= 2, box
    assert box.right <= 158 and box.bottom <= 158, box

    # (2) mata: piksel hangat-terang harus ADA DI KEPALA (pita atas crop),
    # bukan sekadar piksel terang di mana pun - bilah juga terang, tapi
    # blade_shine dingin (r == g) sedangkan mata hangat (r > g). Dicari
    # sebagai warna hasil blending, bukan swatch persih: mata digambar
    # aaline di atas rongga gelap sehingga nilainya tercampur.
    band_h = max(6, int(box.height * 0.42))
    eyes = 0
    for y in range(max(0, box.top), min(160, box.top + band_h)):
        for x in range(max(0, box.left), min(160, box.right)):
            px = canvas.get_at((x, y))
            if px.a > 120 and px.r >= 200 and px.b >= 200 \
                    and px.r - px.g >= 12 and px.g >= 130:
                eyes += 1
    assert eyes >= 2, f"tidak ada piksel mata di area kepala ({eyes})"

    # (3) warna tema DI BADAN (portrait = tanpa FX arena, jadi ini bukti
    #     identitas ungu melekat pada karakter)
    body_cols = colors(canvas)
    theme = {G.PALETTE["magic_hot"], G.PALETTE["magic_mid"],
             G.PALETTE["magic_light"], G.PALETTE["hair_light"],
             G.PALETTE["hair_shine"]}
    assert body_cols & theme, "ungu anti-sihir tidak terlihat pada badan"

    # (4) dua kaki terpisah: scan baris di bawah loincloth
    rig = render("idle", detail=True)
    row_y = CY + int(34 * G.SCALE)
    runs, inside = 0, False
    for x in range(rig.get_width()):
        solid = rig.get_at((x, row_y)).a > 150
        if solid and not inside:
            runs += 1
            inside = True
        elif not solid:
            inside = False
    assert runs >= 2, f"kaki menyatu jadi satu blok (runs={runs} @ y={row_y})"

    # (5) cakram cahaya + cincin tanah tetap ada di jalur arena/lane.
    # Dipantau lewat jumlah piksel alpha-LEMBUT: glow memang sengaja tipis,
    # jadi tidak terlihat dari bounding box (bilah lebih lebar dari aura).
    def soft_px(surf):
        return sum(1 for y in range(surf.get_height())
                   for x in range(surf.get_width())
                   if 6 < surf.get_at((x, y)).a <= 120)

    arena = pygame.Surface((260, 260), pygame.SRCALPHA)
    G.draw_gornak(arena, probe(130, 140), 130, 140)
    shop = pygame.Surface((260, 260), pygame.SRCALPHA)
    G.draw_gornak(shop, probe(130, 140, _portrait_hd=True), 130, 140)
    assert soft_px(arena) > 400, "glow/cakram ungu hilang di jalur arena"
    assert soft_px(shop) < 140, "mode portrait harus tetap bersih"



def test_skill_fx_are_world_space():
    """Telegraph E/R tidak menyusut bersama sprite: kompensasi 1/_render_scale.

    E Counterspell AOE 100 px dunia, R Mana Void AOE 180 px dunia di CASTER
    (bukan di target). Di-render pada fs=1.0 dan fs=0.5: sampling lingkaran
    di radius dunia/fs harus menemukan ring. Tanpa kompensasi, fs=0.5
    menggambar di radius 100/180 px canvas -> 0 hit.
    """
    def render(skill, timer, fs):
        W = 760
        surf = pygame.Surface((W, W), pygame.SRCALPHA)
        b = probe(W // 2, W // 2 + 40, active_skill=skill,
                  active_skill_timer=timer, _render_scale=fs, pulse=1.3)
        b.target = SimpleNamespace(x=float(W // 2 + 140),
                                   y=float(W // 2), alive=True)
        G.draw_gornak(surf, b, W // 2, W // 2 + 40)
        return surf

    def hits_at_radius(surf, cx, cy, r_px):
        n = 0
        for a in range(0, 360, 2):
            ok = False
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            for dr in (-2, -1, 0, 1, 2):
                x = int(cx + ca * (r_px + dr))
                y = int(cy + sa * (r_px + dr))
                if 0 <= x < surf.get_width() and 0 <= y < surf.get_height() \
                        and surf.get_at((x, y)).a > 30:
                    ok = True
                    break
            if ok:
                n += 1
        return n

    cx, cy = 380, 420
    for fs in (1.0, 0.5):
        s = render("e", 40, fs)
        n = hits_at_radius(s, cx, cy, int(100 / fs))
        assert n > 90, ("E ring AOE tidak di 100 px dunia saat fs=%s "
                        "(dapat %s/180)" % (fs, n))
        if fs < 1.0:
            n_wrong = hits_at_radius(s, cx, cy, 100)
            assert n_wrong < 40, ("E ring masih di radius sprite, bukan "
                                  "dunia (fs=%s hit@100=%s)" % (fs, n_wrong))

    for fs in (1.0, 0.5):
        s = render("r", 50, fs)
        n = hits_at_radius(s, cx, cy, int(180 / fs))
        assert n > 70, ("R ring AOE tidak di 180 px dunia (caster) saat "
                        "fs=%s (dapat %s/180)" % (fs, n))
        if fs < 1.0:
            n_wrong = hits_at_radius(s, cx, cy, 180)
            assert n_wrong < 40, ("R ring masih di radius sprite, bukan "
                                  "dunia (fs=%s hit@180=%s)" % (fs, n_wrong))


def test_perf_budget():
    """Guardrail: badan 1.3x lebih besar tidak boleh membuat frame time naik
    drastis. Ambang sengaja longgar (5 ms) supaya tetap lolos di HP rendah;
    hasil terukur di desktop ~1.3 ms/frame (rig lama ~1,2 ms)."""
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
    assert ms < 5.0, f"draw_gornak {ms:.2f} ms/frame - terlalu mahal"
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
    test_size_matches_the_family()
    test_hero_scale_is_no_longer_upsampled()
    test_skill_durations_match_ai_timers()
    test_hero_visual_quality()
    test_attack_timing_has_impact_hold()
    test_secondary_motion_exists()
    test_skill_fx_are_world_space()
    test_perf_budget()
    print("OK - Gornak masterwork v2: rig tunggal, kaki menapak, bilah "
          "pose-driven, proc di ujung bilah, outline, portrait LOD, "
          "Q/W/E/R world-space (E100/R180) tervalidasi")
