#!/usr/bin/env python3
"""Regresi visual untuk Morgath Procedural Masterwork.

Morgath (Arc Warden mini boss level 1, sekaligus hero yang bisa di-unlock)
dulunya dirender sebagai tumpukan body-part kecil: badan padat HANYA
35x55 px (terukur alpha>=1) di samping Gornak 115x121 dan Drakar 138x190 -
orb kepala sebesar kacang, jubah tiang sempit, dan beam lahir dari angka
lepas (x+18, y-2) yang tidak menempel di tangan.

Uji ini mengunci hasil rewrite:
  1. 100% prosedural (tanpa image.load / PNG / sprite sheet).
  2. SATU bone rig 2D berlapis - fungsi body-part lama harus hilang.
  3. Badan padat sekelas keluarga mini boss (>= gornak*0.75), tapi
     tetap lebih kecil dari true boss Abaddon.
  4. Hem jubah dipatok di garis bayangan (GROUND_DY) di semua pose:
     karakter tidak melayang.
  5. Beam petir lahir dari telapak cast (MOR_MUZZLE), bukan titik lepas.
  6. Siluet tidak pernah terpotong buffer rig di pose/frame mana pun.
  7. Outline siluet 1 px ada; LOD portrait membuang FX dan memusatkan diri.
  8. Jalur hero (render_hero + beam pass) tetap sinkron cooldown animasi.

Jalankan:  python3 tools/test_morgath_masterwork.py
"""
import inspect
import math
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
from bosses.level1 import _NS_morgath as M
from bosses import level1 as L

SIZE = 260
C, CY = SIZE // 2, SIZE // 2


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="morgath", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.25,
                        timer=0, attack_cooldown=48, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=51)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render_rig(action="idle", ap=0.0, phase=1.25, facing=1, detail=False):
    """Rig murni (tanpa FX) pada jangkar (C, CY)."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    M._draw_mor_rig(surf, C, CY, facing, phase, action, ap, detail)
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


def pixel_sig(surf):
    return surf.get_view("2").raw if hasattr(surf, "get_view") else None


def test_masterwork_is_procedural_and_single_rig():
    source = inspect.getsource(M)
    assert "pygame.image.load" not in source
    for needed in ("_draw_mor_rig", "_draw_mor_rig_at", "_resolve_mor_pose",
                   "_mor_attack_curve", "_cast_hand_local",
                   "_back_hand_local", "_mor_elbow", "_mor_shift",
                   "_muzzle_offset_world", "_mor_draw_cape",
                   "_mor_draw_skirt", "_mor_draw_torso", "_mor_draw_head",
                   "_mor_draw_arm_cast", "_mor_draw_arm_back",
                   "_mor_draw_pauldron", "_mor_draw_belt",
                   "_mor_draw_boots"):
        assert callable(getattr(M, needed, None)), needed
    # Tumpukan body-part lama harus sudah benar-benar dihapus.
    for gone in ("_draw_mor_body", "_draw_mor_cape", "_draw_mor_legs",
                 "_draw_leg", "_draw_mor_robe", "_draw_mor_torso",
                 "_draw_mor_arm_front", "_draw_mor_head",
                 "_draw_crystal_orb", "_mor_attack_pose"):
        assert not hasattr(M, gone), f"old body-part still present: {gone}"
    # Konversi koordinat beam lama (angka lepas) harus hilang dari source.
    assert "start_x = x + facing * int(round(18 * inv))" not in source


def test_dense_body_matches_boss_family():
    """Badan padat Morgath sekelas Gornak & jauh di atas versi lama (55px)."""
    rect = solid_rect(render_rig("idle"))
    assert rect is not None
    # Versi lama: 35x55. Rewrite: ~105 px padat (SATU skala 0.76 untuk
    # boss & lane, pola Thorne/Gornak v2) - di bawah gornak H~119
    # (kontrak keluarga gornak >= 1.05x morgath) & di atas rig lama 2x.
    assert 92 <= rect.height <= 110, f"H padat di luar band: {rect.height}"
    assert rect.width >= 50, f"silluet too slim: {rect.width}x{rect.height}"
    # Caster berjubah: proporsi tinggi, tapi bukan tiang (lama 0.64).
    assert rect.width / rect.height >= 0.42, rect.width / rect.height
    # Hem jubah jatuh di garis bayangan -> tidak melayang.
    ground = CY + M.GROUND_DY
    assert abs(rect.bottom - ground) <= 3, (rect.bottom, ground)
    # Orb/wajah tetap di bawah HP bar mini boss (r=51 -> bar y-66..y-58).
    assert rect.top >= CY - 62, rect.top
    assert rect.top < CY - 40, "pucuk harus di atas torso (siluet tinggi)"


def test_feet_planted_in_every_pose():
    ground = CY + M.GROUND_DY
    for action, ap in (("idle", 0.0), ("walk", 0.0), ("attack", 0.95),
                       ("point", 0.0), ("channel", 0.0), ("erect", 0.0)):
        for phase in (0.0, 0.9, 1.8, 2.7):
            rect = solid_rect(render_rig(action, ap, phase))
            assert rect is not None, (action, phase)
            assert abs(rect.bottom - ground) <= 3, \
                f"{action} ph={phase}: hem melayang (bottom={rect.bottom}, ground={ground})"


def test_no_buffer_clipping_any_pose():
    """Buffer yang kepangkas memotong jubah/antena saat sprite di-cache."""
    for action, ap in (("idle", 0.0), ("walk", 0.0), ("attack", 0.2),
                       ("attack", 0.6), ("attack", 0.95), ("point", 0.0),
                       ("channel", 0.0), ("erect", 0.0), ("ascend", 0.0)):
        for phase in (0.0, 0.5, 1.2, 2.4):
            buf = pygame.Surface((M.RIG_W, M.RIG_H), pygame.SRCALPHA)
            M._draw_mor_rig(buf, M.RIG_OX, M.RIG_OY, 1, phase, action, ap,
                            False)
            r = buf.get_bounding_rect(min_alpha=1)
            assert r.width > 0
            assert r.left > 1 and r.top > 1 and \
                r.right < M.RIG_W - 1 and r.bottom < M.RIG_H - 1, \
                f"clipped: {action} ap={ap} ph={phase} -> {r}"


def test_poses_are_actually_distinct():
    """Walk/attack/skill harus benar-benar dihitung ulang per-sendi."""
    base = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    imgs = {}
    for name, (action, ap) in {"idle": ("idle", 0.0),
                               "walk": ("walk", 0.0),
                               "attack": ("attack", 0.95),
                               "point": ("point", 0.0),
                               "channel": ("channel", 0.0),
                               "erect": ("erect", 0.0),
                               "ascend": ("ascend", 0.0)}.items():
        s = render_rig(action, ap, 1.25)
        imgs[name] = pygame.image.tostring(s, "RGBA")
    keys = list(imgs)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            assert imgs[keys[i]] != imgs[keys[j]], \
                f"pose {keys[i]} identik dengan {keys[j]}"
    # Walk harus berubah sepanjang siklus langkah.
    w0 = pygame.image.tostring(render_rig("walk", 0.0, 0.0), "RGBA")
    w1 = pygame.image.tostring(render_rig("walk", 0.0, 1.4), "RGBA")
    assert w0 != w1, "walk tidak beranimasi sepanjang phase"


def test_beam_is_born_from_the_palm():
    """Beam mulai di muzzle rig dan tidak menggambar sebelum waktunya."""
    mdx, mdy = M._muzzle_offset_world()
    # Muzzle dunia harus = telapak cast saat thrust penuh (sinkron rig).
    hand = M._cast_hand_local("attack", 0.95, 1.0)
    assert abs(hand[0] - M.MOR_MUZZLE[0]) <= 1.0
    assert abs(hand[1] - M.MOR_MUZZLE[1]) <= 1.0
    assert 24 <= mdx <= 46, mdx          # di luar badan, di depan muka
    assert -34 <= mdy <= -16, mdy        # setinggi dada/depan hood

    x, y = 200.0, 200.0
    boss = probe(x, y)
    boss.target = SimpleNamespace(x=x + 180, y=y + 12, alive=True)
    boss._mor_attack_dir = 1
    boss._mor_attack_target = (180, 12)

    # Sebelum 0.55: tidak ada piksel beam sama sekali.
    s0 = pygame.Surface((460, 300), pygame.SRCALPHA)
    M._draw_lightning_projectile(s0, boss, int(x), int(y), 0.3)
    assert s0.get_bounding_rect(min_alpha=8).width == 0

    # Sesudahnya: beam harus LEBIH DEKAT ke muzzle daripada ke dada.
    s1 = pygame.Surface((460, 300), pygame.SRCALPHA)
    M._draw_lightning_projectile(s1, boss, int(x), int(y), 0.75)
    rect = s1.get_bounding_rect(min_alpha=8)
    assert rect.width > 30, f"beam terlalu pendek: {rect}"
    muz = (x + mdx, y + mdy)
    dist = max(0.0, math.hypot(max(rect.left - muz[0], 0,
                                   muz[0] - rect.right),
                               max(rect.top - muz[1], 0,
                                   muz[1] - rect.bottom)))
    assert dist <= 4, f"beam tidak menempel di telapak: jarak {dist}px"


def test_beam_tetap_muncul_saat_timer_renderer_basi():
    """Beam basic attack tidak boleh bergantung pada previous timer render.

    Jika Morgath sempat tidak digambar/off-screen, previous timer di
    renderer bisa tertinggal pada nilai > 1.  Event _basic_attack_seq dari
    engine harus tetap menyalakan state attack dan beam di frame saat unit
    kembali tergambar.
    """
    x, y = 200, 180
    boss = probe(x, y)
    boss.target = SimpleNamespace(x=x + 180, y=y, alive=True)
    boss._mor_previous_timer = 18       # nilai basi dari serangan lama
    boss._basic_attack_seq = 1          # serangan baru sudah dilepas engine
    boss.timer = 20                     # progress > 0.55 untuk cooldown 48
    boss._beam_pass_only = True
    s = pygame.Surface((460, 300), pygame.SRCALPHA)
    M.draw_morgath(s, boss, x, y)
    assert boss._mor_attack_active
    assert boss._mor_attack_progress > 0.55
    assert s.get_bounding_rect(min_alpha=8).width > 30


def test_beam_controller_idempoten_saat_dipanggil_ganda():
    """Cache/probe/beam pass boleh memanggil controller lebih dari sekali."""
    boss = probe(200, 180)
    boss._basic_attack_seq = 1
    boss.timer = boss.attack_cooldown
    M._update_mor_attack_anim(boss)
    assert boss._mor_attack_frame == 0
    M._update_mor_attack_anim(boss)
    assert boss._mor_attack_frame == 0
    boss.timer = boss.attack_cooldown - 1
    M._update_mor_attack_anim(boss)
    assert boss._mor_attack_frame == 1
    M._update_mor_attack_anim(boss)
    assert boss._mor_attack_frame == 1


def test_outline_silhouette_present():
    """Outline 1 px gelap: bagian boss tetap terpisah saat menumpuk."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    M._draw_mor_rig_at(surf, C, CY, 1, 1.25, "idle", 0.0, False)
    rect = solid_rect(surf)
    assert rect is not None
    # Outline = piksel hitam pekat (<=12) opaque yang bersebelahan dengan
    # piksel TRANSPARAN (tepi luar siluet). Isi badan tidak ada yang
    # sehitam ini: nada tergelap palet robe_darkest=(12,8,25) > ambang.
    edge_hits = 0
    for px in range(rect.left, rect.right):
        for py in range(rect.top, rect.bottom):
            c = surf.get_at((px, py))
            if c.a >= 200 and c.r <= 10 and c.g <= 10 and c.b <= 10:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    qx, qy = px + dx, py + dy
                    if 0 <= qx < SIZE and 0 <= qy < SIZE and \
                            surf.get_at((qx, qy)).a == 0:
                        edge_hits += 1
                        break
    assert edge_hits >= 8, f"outline siluet tidak terdeteksi ({edge_hits})"


def test_attack_curve_shape():
    """Anticipation -> thrust -> impact hold -> release, monoton naik."""
    prev = 0.0
    for i in range(101):
        ap = M._mor_attack_curve(i / 100.0)
        assert ap >= prev - 1e-9, f"kurva mundur di {i}: {ap} < {prev}"
        prev = ap
    assert M._mor_attack_curve(0.0) == 0.0
    assert abs(M._mor_attack_curve(1.0) - 1.0) < 1e-6
    # Di progres mentah 0.55 (beam mulai), telapak sudah hampir penuh.
    assert M._mor_attack_curve(0.55) >= 0.70


def test_portrait_lod_is_centered_without_ground_fx():
    boss = probe(0, 0, _portrait_hd=True)
    # Hapus marker lane supaya pass cahaya portrait tetap jalan
    # (Hero Shop tidak men-set _render_scale).
    del boss._render_scale
    surf = pygame.Surface((220, 220), pygame.SRCALPHA)
    M.draw_morgath(surf, boss, 110, 110)
    rect = solid_rect(surf)
    assert rect is not None
    # Konten terpusat pada jangkar (auto-crop Hero Shop penuh wajah).
    assert abs(rect.centerx - 110) <= 8, rect
    assert abs(rect.centery - 110) <= 10, rect
    # FX tanah (rune selebar ~110 px) dibuang di mode portrait: lebar
    # konten hanya dari badan + pecahan orbit (~70 px), bukan rune.
    assert rect.width <= 84, f"rune/aura bocor ke portrait: W={rect.width}"


def test_hero_lane_render_and_beam_pass():
    """Jalur hero: render_hero (cache+scale) & beam pass skala dunia."""
    import heroes
    from heroes import _ProbeEntity, HERO_RENDERERS, BOSS_RENDERERS

    c = 200
    rend = HERO_RENDERERS.get("morgath") or BOSS_RENDERERS.get("morgath")
    assert rend is not None

    # Skala hasil normalisasi TIDAK boleh meng-upscale (kabur); badan
    # final di layar = HERO_TARGET_HEIGHT * HERO_GLOBAL_SCALE (kontrak
    # pipeline - semua hero masterwork mendarat di ~51 px di lane).
    sc = heroes._get_hero_scale("morgath")
    assert sc <= 1.02, f"morgath di-upscale {sc}"
    assert 0.45 <= sc <= 0.95, f"skala di luar band keluarga: {sc}"

    # Render jalur PENUH (canvas -> smoothscale -> pass HD/outline),
    # lalu ukur badan final dengan semantik yang sama seperti
    # _measure_native_size (buang FX tanah di bawah garis kaki,
    # ambang alpha 100) - ini ukuran yang benar-benar terlihat.
    h = _ProbeEntity("morgath", c, c)
    h.pulse = 1.35
    h.direction = 1
    h.team = "blue"
    final = pygame.Surface((400, 400), pygame.SRCALPHA)
    heroes.render_hero("morgath", final, h, c, c)
    body_line = c + 16
    final.fill((0, 0, 0, 0), (0, body_line, 400, 400 - body_line))
    r = final.get_bounding_rect(min_alpha=100)
    assert r.height >= 40, f"badan final hilang: {r}"
    assert 45 <= r.height <= 62, f"final body H = {r.height}"

    # Beam pass (skala dunia, setelah body ter-blit): tidak crash & menggambar
    h2 = probe(c, c)
    h2._beam_pass_only = True
    h2._mor_attack_active = True
    h2.timer = 14
    h2._mor_previous_timer = 17
    h2._mor_attack_dir = 1
    h2._mor_attack_target = (200, 0)
    h2.target = SimpleNamespace(x=c + 200, y=c, alive=True)
    beam_canvas = pygame.Surface((400, 400), pygame.SRCALPHA)
    M.draw_morgath(beam_canvas, h2, c, c)
    assert beam_canvas.get_bounding_rect(min_alpha=8).width > 20


def test_skill_fx_still_wired():
    """FX lama (rune/aura/4 skill + clone) tetap terpasang di entry point."""
    base = pygame.Surface((460, 460), pygame.SRCALPHA)
    b0 = probe(230, 230, pulse=0.8)
    L.draw_morgath(base, b0, 230, 230)
    base_px = len(pygame.mask.from_surface(base, 20).get_bounding_rects())
    for skill in ("q", "w", "e", "r"):
        s = pygame.Surface((460, 460), pygame.SRCALPHA)
        b = probe(230, 230, pulse=0.8, active_skill=skill,
                  active_skill_timer=40)
        L.draw_morgath(s, b, 230, 230)
        # clone tempest menambah siluet kedua di kiri pada "r"
        mask = pygame.mask.from_surface(s, 20)
        count = mask.count()
        base_count = pygame.mask.from_surface(base, 20).count()
        assert count != base_count or skill != "r", "FX skill r hilang"
        if skill == "r":
            left = mask.get_bounding_rects()
            xs = [q.x for q in left]
            assert min(xs) < 200, "clone tempest tidak muncul di sisi belakang"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK  - {fn.__name__}")
    print("\nSEMUA TES MORGATH MASTERWORK LULUS ✓")
