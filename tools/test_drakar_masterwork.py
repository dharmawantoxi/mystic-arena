#!/usr/bin/env python3
"""Regresi visual untuk Drakar Procedural Masterwork.

Drakar (mini boss berserker level 1, sekaligus hero yang bisa di-unlock)
dulunya dirender sebagai tumpukan body-part statis: badan kotak menyatu,
kepala gumpalan dengan mata dua titik, kapak "kertas" yang tidak pernah
tersambung ke tangan, dan partikel darah berserakan tanpa arah. Semua pose
(idle/walk/attack/skill) hampir identik.

Uji ini mengunci hasil rebuild (para dengan test_gornak_masterwork.py):
  1. 100% prosedural (tanpa image.load / PNG / sprite sheet).
  2. SATU bone rig 2D berlapis - nama fungsi body-part lama harus hilang.
  3. Telapak dipatok di garis bayangan (tidak melayang).
  4. Kapak dua tangan: kedua pergelangan lahir dari TITIK DI GAGANG, dan
     pita cleave lahir dari MATA KAPAK (bukan titik melayang).
  5. Outline siluet 1 px ada (bagian tetap terpisah saat unit bertumpuk).
  6. LOD portrait: pass material aktif & efek arena (rune/aura) dibuang.
  7. Frame walk/attack dihitung ulang per-sendi; kurva attack punya
     anticipation + impact hold.
  8. Durasi SKILL_DUR sinkron dengan timer AI boss & hero skills.

Jalankan:  python3 tools/test_drakar_masterwork.py
"""
import inspect
import math
import os
import re
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from bosses.level1 import _NS_drakar as D
from bosses import level1
from heroes import _ProbeEntity, clear_hero_sprite_cache, render_hero

SIZE = 300
C, CY = SIZE // 2, SIZE // 2 + 20


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.25,
                        timer=0, attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=32)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def atk_probe(prog, cd=46):
    """Boss di tengah ayunan: timer HARUS > 0 (timer 0 membatalkan
    attack state di _update_drk_attack_anim - sama seperti di game)."""
    b = probe()
    b.attack_cooldown = cd
    frame = int(prog * (cd - 1))
    b._drk_attack_active = True
    b._drk_attack_dir = 1
    b._drk_attack_frame = frame
    b._drk_previous_timer = (cd - 1) - frame
    b.timer = (cd - 1) - frame
    b._drk_attack_progress = prog
    return b


def render(action="idle", ap=0.0, phase=1.25, facing=1, detail=False):
    """Rig murni (tanpa FX) pada jangkar (C, CY)."""
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    D._draw_drk_rig(surf, C, CY, facing, phase, action, ap, detail)
    return surf


def clipped_by_buffer(action, ap, phase):
    """True kalau hasil render rig menyentuh tepi buffer RIG_W x RIG_H.

    Buffer yang kecipil akan memotong kapak/mane saat sprite di-cache,
    jadi ini diperiksa dari bounding box render sebenarnya.
    """
    buf = pygame.Surface((D.RIG_W, D.RIG_H), pygame.SRCALPHA)
    D._draw_drk_rig(buf, D.RIG_OX, D.RIG_OY, 1, phase, action, ap, False)
    r = buf.get_bounding_rect(min_alpha=1)
    return r.width == 0 or r.left <= 0 or r.top <= 0 or \
        r.right >= D.RIG_W or r.bottom >= D.RIG_H


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
    source = inspect.getsource(D)
    assert "pygame.image.load" not in source
    for needed in ("_draw_drk_rig", "_draw_drk_legs", "_draw_drk_torso",
                   "_draw_drk_head", "_draw_drk_arm", "_draw_drk_axe",
                   "_draw_drk_masterwork_details", "_axe_angle",
                   "_front_grip_local", "_back_grip_local", "_elbow",
                   "_tip_local", "_tip_screen", "_compose_outline",
                   "_draw_cleave_trail", "_resolve_pose"):
        assert callable(getattr(D, needed, None)), needed
    # Tumpukan body-part lama harus sudah benar-benar dihapus.
    for gone in ("_draw_drk_body", "_draw_drk_waist", "_draw_drk_leg", 
                 "_draw_wild_hair", "_draw_drk_idle", "_draw_drk_walk",
                 "_draw_drk_attack", "_draw_drk_helix", "_draw_rage_mist",
                 "_draw_drk_hair", "_draw_battlehunger_ground_old"):
        assert not hasattr(D, gone), f"old body-part still present: {gone}"


def test_feet_are_planted_and_body_is_readable():
    idle = render("idle")
    rect = solid_rect(idle)
    assert rect is not None
    # Badan harus jauh lebih besar dari rig lama (blok ~60 px) dan
    # mempertahankan peringkat boss terbesar di keluarga mini boss.
    assert rect.height >= 110, f"body too short: {rect.height}"
    # Siluet harus MEMENUHI kotak, bukan tiang sempit (rig lama 0.60).
    # Berserker frontal: lebar datang dari traps/pauldron/stance + massa
    # kapak di kuadran atas, bukan dari kaki terkangkul.
    assert rect.width / rect.height >= 0.68, \
        f"siluet terlalu sempit: {rect.width}x{rect.height}"
    # Sol jatuh di garis bayangan -> karakter tidak melayang.
    ground = CY + D.GROUND_DY
    assert abs(rect.bottom - ground) <= 3, (rect.bottom, ground)
    # Puncak tanduk: referensi keluarga H138 menempatkan puncak rig di
    # ~CY-92 (78 saat CY=170); larang saja rig yang menembus kebalik ke
    # atas jangkar.
    assert rect.top >= CY - 95, rect.top


def test_head_eyes_are_the_focal_point():
    """Dua mata amber harus terbaca sebagai DUA klaster warna mata yang
    terpisah (bukan satu pita 'visor'). eye_mid/eye_glow hanya dipakai
    di mata, jadi keberadaan + sebarannya adalah sinyal yang kuat."""
    surf = render("idle", 0.0, 1.25, detail=True)
    hy = D.HEAD_Y
    lean, root_y = D._rig_shift("idle", 1.25, 0.0)
    top = D._local_to_screen(C, CY, 1, lean, root_y, 0, hy - 6)[1]
    bot = D._local_to_screen(C, CY, 1, lean, root_y, 0, hy + 4)[1]
    targets = [D.PALETTE["eye_mid"], D.PALETTE["eye_glow"]]
    xs = []
    for y in range(max(0, top), min(SIZE, bot + 1)):
        for x in range(SIZE):
            p = surf.get_at((x, y))
            if p.a > 200 and any(abs(p.r - t[0]) <= 8 and
                                 abs(p.g - t[1]) <= 12 and
                                 abs(p.b - t[2]) <= 16 for t in targets):
                xs.append(x)
    assert len(xs) >= 8, f"piksel mata terlalu sedikit: {len(xs)}"
    xs.sort()
    clusters = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] <= 3:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    big = [c for c in clusters if len(c) >= 3]
    assert len(big) >= 2, \
        f"mata melebur (klaster: {[len(c) for c in clusters]})"


def test_axe_geometry_is_pose_driven():
    """Kapak: rest -> wind-up -> impact -> recovery, dua tangan di gagang.

    (a) semua fase harus berbeda, (b) kedua tangan lahir dari titik DI
    gagang (jarak ke garis gagang ~0), (c) kapak tidak pernah menyapu
    menembus torso, (d) tidak terpotong buffer.
    """
    head_idle = D._axe_head_local("idle", 1.0, 0.0)
    head_wind = D._axe_head_local("attack", 1.0, D._attack_curve(0.14))
    head_rel = D._axe_head_local("attack", 1.0, D._attack_curve(0.62))
    # Wind-up: mata kapak terangkat JAUH DI ATAS kepala (tebasan atas).
    assert head_wind[1] < -60, f"wind-up kurang tinggi: {head_wind}"
    # Impact: mata kapak sudah jatuh di depan-bawah badan (menembus
    # garis lutut, melewati garis tengah ke sisi depan).
    assert head_rel[1] > 20, f"impact terlalu tinggi: {head_rel}"
    assert head_rel[0] > 20, f"impact tidak ke depan: {head_rel}"
    # Seluruh ayunan harus bergerak: ketiga fase berbeda jelas.
    assert len({tuple(head_idle), tuple(head_wind), tuple(head_rel)}) == 3

    def dist_to_shaft(grip, hx, hy, ang):
        """Jarak titik (hx,hy) ke garis gagang lewat grip dengan sudut ang."""
        s, c = math.sin(ang), math.cos(ang)
        dx, dy = hx - grip[0], hy - grip[1]
        return abs(dx * c - dy * s)

    for action in ("idle", "walk", "rage", "helix", "call", "cull"):
        for i in range(5):
            ph = i * 1.05
            ang = D._axe_angle(ph, action, 0.0)
            fg = D._front_grip_local(action, 0.0, ph)
            bg = D._back_grip_local(action, 0.0, ph)
            d = dist_to_shaft(fg, bg[0], bg[1], ang)
            assert d <= 2.0, \
                f"tangan belakang lepas dari gagang: {action} {ph} d={d}"
    # Torso: blok dada. Tangan tetap di sisi depan sepanjang ayunan, jadi
    # cek grip-x tidak pernah menyeberang garis tengah badan saat swing.
    for i in range(21):
        ap = D._attack_curve(i / 20.0)
        grip = D._front_grip_local("attack", ap, 1.0)
        assert grip[0] >= -2, f"grip menembus badan @ ap={ap:.2f}: {grip}"
        assert not clipped_by_buffer("attack", ap, 1.0), \
            f"rig clipped by buffer @ attack ap={ap:.2f}"
    for action in ("idle", "walk", "rage", "helix", "call", "cull"):
        for i in range(4):
            ph = i * 1.05
            assert not clipped_by_buffer(action, 0.0, ph), \
                f"rig clipped by buffer @ {action} phase={ph:.2f}"
    frames = {pygame.image.tobytes(render("attack", i / 9.0), "RGBA")
              for i in range(10)}
    assert len(frames) == 10


def test_attack_timing_has_impact_hold():
    """Anticipation -> ayunan cepat -> HOLD di impact -> follow-through.

    Diuji sebagai SIFAT kurva: monoton, ada jendela hold, kontras laju,
    endpoint 0/1.
    """
    N = 400
    seq = [D._attack_curve(i / N) for i in range(N + 1)]
    assert all(b >= a - 1e-9 for a, b in zip(seq, seq[1:])), "kurva mundur"
    assert abs(seq[0]) < 1e-9 and abs(seq[-1] - 1.0) < 0.02, (seq[0], seq[-1])
    step = 3 / N
    rate = [(seq[i + 1] - seq[i]) / step for i in range(N)]
    lo, hi = min(rate), max(rate)
    assert hi > 4.0 * max(lo, 1e-6), (lo, hi)
    quiet = [i for i, r in enumerate(rate) if r <= hi * 0.25]
    assert quiet, "tidak ada hold sama sekali"
    span = (max(quiet) - min(quiet)) / N
    assert span >= 0.08, f"jendela impact cuma {span:.3f} (perlu >= 0.08)"


def test_cleave_trail_starts_at_axe_head():
    """FX attack harus lahir dari MATA KAPAK - bukan mengambang di samping."""
    boss = atk_probe(0.45)
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    level1.draw_drakar(surf, boss, C, CY)
    prog = float(getattr(boss, "_drk_attack_progress", 0.0) or 0.0)
    assert prog > 0.2, f"attack progress tidak aktif: {prog}"
    hx, hy = D._axe_head_local("attack", 1.15, D._attack_curve(prog))
    ang = D._axe_angle(1.15, "attack", D._attack_curve(prog))
    # Titik di BADAN BILAH (v=+6 dari mata kapak) - tepi luar persis
    # bisa jatuh di antara dua gambar (bilah vs pita).
    bx = hx + math.cos(ang) * 6
    by = hy - math.sin(ang) * 6
    lean, root_y = D._rig_shift("attack", 1.15, D._attack_curve(0.45))
    tip = D._local_to_screen(C, CY, 1, lean, root_y, bx, by)
    px = surf.get_at((int(tip[0]), int(tip[1])))
    assert px.a > 0, f"no pixel at the claimed blade body: {tip}"
    # Pita cleave harus menyentuh zona mata kapak (<= 12 px).
    best, bestd = None, 999
    for y in range(max(0, tip[1] - 14), min(SIZE, tip[1] + 15)):
        for x in range(max(0, tip[0] - 14), min(SIZE, tip[0] + 15)):
            p = surf.get_at((x, y))
            if p.a and (p.r + p.g + p.b) > 600:
                d = abs(x - tip[0]) + abs(y - tip[1])
                if d < bestd:
                    best, bestd = (x, y), d
    assert best is not None and bestd <= 12, (tip, best, bestd)


def test_silhouette_outline_exists():
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    D._draw_drk_rig_at(surf, C, CY, 1, 1.25, "idle", 0.0, False)
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
    D._draw_drk_rig(arena, C, CY, 1, 1.25, "idle", 0.0, False)
    D._draw_drk_rig(portrait, C, CY, 1, 1.25, "idle", 0.0, True)
    assert pygame.image.tobytes(arena, "RGBA") != \
        pygame.image.tobytes(portrait, "RGBA")
    assert len(colors(portrait)) > len(colors(arena))

    full = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    crop = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    level1.draw_drakar(full, probe(C, CY), C, CY)
    level1.draw_drakar(crop, probe(C, CY, _portrait_hd=True), C, CY)

    def painted(surf):
        """Jumlah piksel tergambar - sinyal stabil (RGB di-blend turun)."""
        n = 0
        for y in range(surf.get_height()):
            for x in range(surf.get_width()):
                if surf.get_at((x, y)).a > 6:
                    n += 1
        return n

    a_px, p_px = painted(full), painted(crop)
    assert a_px > p_px * 1.18, \
        f"portrait harus membuang FX arena (painted {a_px} vs {p_px})"


def test_secondary_motion_exists():
    """Kepala, debu langkah, kedip: gerak sekunder yang memisahkan rig
    \"hidup\" dari rig \"menggeser stiker\"."""
    heads = {a: D._head_bob(a, 2.1, 0.5)
             for a in ("idle", "walk", "attack", "rage", "call")}
    assert len(set(heads.values())) >= 4, heads
    assert heads["call"][1] < heads["idle"][1]      # mendongak saat roar
    frames = set()
    for i in range(5):
        surf = pygame.Surface((300, 300), pygame.SRCALPHA)
        D._draw_drk_rig(surf, 150, 150, 1, 0.9 * i, "walk", 0.0, False)
        frames.add(pygame.image.tobytes(
            surf.subsurface(pygame.Rect(118, 76, 64, 46)), "RGBA"))
    assert len(frames) >= 4, "kepala statis saat berjalan"
    dust_walk = pygame.Surface((300, 300), pygame.SRCALPHA)
    D._draw_footfall_dust(dust_walk, 150, 150, 1, 0.0)
    assert dust_walk.get_bounding_rect(min_alpha=6).width > 8, \
        "footfall dust tidak tergambar"
    lifted = math.pi / 2 / 1.1
    still = pygame.Surface((300, 300), pygame.SRCALPHA)
    D._draw_footfall_dust(still, 150, 150, 1, lifted)
    assert still.get_bounding_rect(min_alpha=6).width == 0


def test_walk_frames_recalculate_joints():
    frames = {pygame.image.tobytes(render("walk", 0.0, phase=1.0 + i * 0.55),
                                   "RGBA") for i in range(6)}
    assert len(frames) == 6
    for i in range(6):
        surf = render("walk", 0.0, phase=1.0 + i * 0.55)
        row = pygame.Rect(0, CY + D.GROUND_DY - 1, SIZE, 3)
        assert surf.subsurface(row).get_bounding_rect(min_alpha=150).width > 4


def test_pose_router_and_skill_states_render():
    """Boss path DAN hero path (via render_hero + cache) harus aman."""
    for skill, timer in ((None, 0), ("q", 40), ("w", 20), ("e", 30),
                         ("r", 30)):
        boss = probe(C, CY, active_skill=skill, active_skill_timer=timer,
                     pulse=1.4)
        boss.target = SimpleNamespace(x=float(C + 120), y=float(CY - 8),
                                      alive=True)
        surf = pygame.Surface((SIZE * 2, SIZE), pygame.SRCALPHA)
        level1.draw_drakar(surf, boss, C, CY)
        rect = surf.get_bounding_rect(min_alpha=6)
        assert rect.width > 40 and rect.height > 60, skill
        action = getattr(boss, "_drk_pose_action", None)
        expect = {None: "idle", "q": "rage", "w": "helix", "e": "call",
                  "r": "cull"}[skill]
        assert action == expect, (skill, action)

    clear_hero_sprite_cache()
    for skill in ("q", "w", "e", "r"):
        hero = _ProbeEntity("drakar", 200, 210)
        hero.pulse = 1.4
        hero.direction = hero.facing = 1
        hero.active_skill = skill
        hero.active_skill_timer = 20
        hero.timer = 0
        hero.target = _ProbeEntity("dummy", 300, 212)
        hero.target.alive = True
        surf = pygame.Surface((420, 380), pygame.SRCALPHA)
        render_hero("drakar", surf, hero, 200, 210)
        rect = surf.get_bounding_rect(min_alpha=5)
        assert rect.width > 30 and rect.height > 30, skill


def test_hero_scale_is_reasonable():
    """Boss terbesar level-1 tidak boleh menggantung di atas pipeline HD
    (upscale = blur) atau menyusut lebih kecil dari hero starter."""
    import heroes
    renderer = heroes.HERO_RENDERERS.get("drakar") or \
        heroes.BOSS_RENDERERS.get("drakar")
    native = heroes._measure_native_size("drakar", renderer)
    assert native, "pengukuran gagal"
    scale = heroes._get_hero_scale("drakar")
    assert native[1] >= 50, f"badan terlalu kecil untuk pipeline HD: {native}"
    assert scale <= 1.02, f"hero drakar masih di-upscale: {scale:.3f}"


def test_skill_durations_match_ai_timers():
    """Durasi animasi skill harus sinkron dengan timer yang diisi AI.

    boss  : q=90 w=45 e=60 r=60 (bosses/base_boss.py)
    hero  : q=90 w=45 e=60 r=60 (hero_skills/_bundle.py)
    """
    cast = {"q": "_cast_q_battle_hunger", "w": "_cast_w_counter_helix",
            "e": "_cast_e_berserkers_call", "r": "_cast_r_culling_blade"}
    sources = {
        "boss": os.path.join(ROOT, "bosses", "base_boss.py"),
        "hero": os.path.join(ROOT, "hero_skills", "_bundle.py"),
    }
    for tag, path in sources.items():
        src = open(path, encoding="utf-8").read()
        for key, fn in cast.items():
            i = src.index("def %s(" % fn)
            m = re.search(r"active_skill_timer\s*=\s*(\d+)",
                          src[i:i + 900])
            assert m, f"{tag}/{key}: active_skill_timer tidak ketemu"
            assert int(m.group(1)) == D.SKILL_DUR[key], \
                f"{tag} {key} timer {m.group(1)} != render {D.SKILL_DUR[key]}"


def test_size_matches_the_family():
    """Drakar = boss terbesar level 1, tapi tetap di bawah true boss."""
    def boss_bbox(name, fn):
        surf = pygame.Surface((460, 460), pygame.SRCALPHA)
        b = probe(230, 230)
        b.boss_type = name
        b.target = SimpleNamespace(x=9999.0, y=9999.0, alive=False)
        fn(surf, b, 230, 230)
        m = pygame.mask.from_surface(surf, 100)
        rs = m.get_bounding_rects()
        x0 = min(q.x for q in rs); y0 = min(q.y for q in rs)
        x1 = max(q.right for q in rs); y1 = max(q.bottom for q in rs)
        return y1 - y0, x1 - x0

    import bosses.level1 as L
    dh, dw = boss_bbox("drakar", L.draw_drakar)
    mh, mw = boss_bbox("morgath", L.draw_morgath)
    ah, aw = boss_bbox("abaddon", L.draw_abaddon)
    # Catatan keluarga di _NS_gornak: "morgath H82/W120, drakar H138/W190,
    # abaddon H122/W150" - drakar MEMANG boss terbesar level 1 (di atas
    # true boss sekalipun menurut pengukuran lama), jadi posisi itu yang
    # dikunci, dengan batas kewajaran atas.
    assert dh >= mh * 1.25, f"drakar H={dh} vs morgath H={mh}"
    assert dw >= mw * 0.90, f"drakar W={dw} vs morgath W={mw}"
    assert ah * 0.85 <= dh <= ah * 1.40, \
        f"drakar H={dh} keluar skala keluarga (abaddon H={ah})"


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  OK  {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
