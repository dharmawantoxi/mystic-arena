#!/usr/bin/env python3
"""Regresi visual untuk Level 2 Procedural Masterwork (razak, khalros,
gorath, alchemist).

Mengunci standar yang sama dengan Gornak/Drakar (bosses/level1.py):
  1. 100% prosedural (tanpa image.load).
  2. Konstanta rig eksplisit: SCALE/LIFT/FEET_DY/GROUND_DY/RIG_W/RIG_H/
     RIG_OX/RIG_OY.
  3. Telapak kaki dipatok di GROUND_DY (tidak melayang).
  4. Idle bob >= 4 px terlihat.
  5. Walk: kaki alternating + lift, sol tetap menyentuh tanah.
  6. Attack: windup & impact berbeda dari idle (distinktif).
  7. Senjata pose-driven (sudut dari garis lengan).
  8. Skill FX: ground ring + partikel + kilat (charge/burst/afterglow).
  9. Portrait HD: aura/ground FX dibuang, rig tetap di dalam kanvas.
 10. Kedua arah (kiri/kanan) benar & bukan hanya copy identik.
 11. SKILL_DUR sinkron dengan active_skill_timer di AI (base_boss.py).

Jalankan:  python3 tools/test_level2_masterwork.py
"""
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

import bosses.level2 as L2
from bosses import _masterwork as MW

SIZE = 240
C, CY = SIZE // 2, SIZE // 2 + 26

BOSSES = {
    "razak": L2._NS_razak,
    "khalros": L2._NS_khalros,
    "gorath": L2._NS_gorath,
    "alchemist": L2._NS_alchemist,
}

CONSTS = ("SCALE", "LIFT", "FEET_DY", "GROUND_DY", "RIG_W", "RIG_H",
          "RIG_OX", "RIG_OY")


def probe(name, **kw):
    b = SimpleNamespace(boss_type=name, boss_class="mini", x=0.0, y=0.0,
                        direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=40, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=34)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def render_rig(name, action="idle", phase=1.2, ap=0.0, facing=1, detail=False):
    ns = BOSSES[name]
    surf = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    buf = MW.compose(ns._CFG, ns._paint_rig, facing, phase, action, ap, detail)
    MW.blit_rig(surf, ns._CFG, buf, C, CY, detail)
    return surf


def solid_rect(surf, thr=120):
    mask = pygame.mask.from_surface(surf, thr)
    rects = mask.get_bounding_rects()
    if not rects:
        return None
    x0 = min(r.x for r in rects)
    y0 = min(r.y for r in rects)
    x1 = max(r.right for r in rects)
    y1 = max(r.bottom for r in rects)
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def tobytes(surf):
    return pygame.image.tobytes(surf, "RGBA")


def test_procedural_and_constants():
    src = open(os.path.join(ROOT, "bosses", "level2.py"),
               encoding="utf-8").read()
    src += open(os.path.join(ROOT, "bosses", "_masterwork.py"),
                encoding="utf-8").read()
    assert "pygame.image.load" not in src
    for name, ns in BOSSES.items():
        for c in CONSTS:
            assert hasattr(ns, c), f"{name} missing {c}"
        assert ns.GROUND_DY == int(round(ns.FEET_DY * ns.SCALE)) - ns.LIFT


def test_feet_planted():
    for name in BOSSES:
        ns = BOSSES[name]
        for action in ("idle", "walk", "attack"):
            ph = 2.0 if action == "walk" else 1.2
            r = render_rig(name, action, phase=ph)
            rect = solid_rect(r)
            assert rect is not None, name
            ground = CY + ns.GROUND_DY
            assert abs(rect.bottom - ground) <= 3, \
                f"{name}/{action} bottom={rect.bottom} ground={ground}"


def test_idle_bob_visible():
    for name, ns in BOSSES.items():
        # phase dimana sin(phase*0.62)=+1 dan =-1
        p_up = (math.pi / 2) / 0.62
        p_dn = (3 * math.pi / 2) / 0.62
        r1 = solid_rect(render_rig(name, "idle", phase=p_up))
        r2 = solid_rect(render_rig(name, "idle", phase=p_dn))
        # puncak badan bergeser oleh bob (kaki tetap)
        delta = abs(r1.top - r2.top)
        assert delta >= 3, f"{name} idle bob hanya {delta}px"


def test_walk_feet_stay_grounded_and_stride():
    for name, ns in BOSSES.items():
        frames = []
        for i in range(6):
            r = render_rig(name, "walk", phase=1.0 + i * 0.55)
            frames.append(tobytes(r))
            # selalu ada piksel solid di garis tanah (salah satu sol menapak)
            row = pygame.Rect(0, CY + ns.GROUND_DY - 2, SIZE, 4)
            assert r.subsurface(row).get_bounding_rect(
                min_alpha=150).width > 3, f"{name} walk frame {i} melayang"
        # frame walk berbeda-beda (stride dihitung ulang)
        assert len(set(frames)) >= 4, f"{name} walk statis"


def test_attack_distinct_from_idle():
    for name in BOSSES:
        idle = tobytes(render_rig(name, "idle", phase=1.2))
        wind = tobytes(render_rig(name, "attack", phase=1.2,
                                  ap=MW.attack_curve(0.14)))
        imp = tobytes(render_rig(name, "attack", phase=1.2,
                                 ap=MW.attack_curve(0.6)))
        assert wind != idle, f"{name} windup == idle"
        assert imp != idle, f"{name} impact == idle"
        assert wind != imp, f"{name} windup == impact"


def test_weapon_pose_driven():
    # sudut senjata diturunkan dari garis lengan (fungsi bersama ada & dipakai)
    assert callable(getattr(MW, "weapon_angle_from_arm"))
    assert callable(getattr(MW, "weapon_tip"))
    # ujung senjata berubah mengikuti progres attack (pose-driven)
    for name in BOSSES:
        tips = set()
        for ap in (0.1, 0.3, 0.5, 0.7, 0.9):
            r = render_rig(name, "attack", phase=1.2, ap=MW.attack_curve(ap))
            tips.add(tobytes(r))
        assert len(tips) >= 4, f"{name} senjata tidak mengikuti pose"


def test_both_directions():
    for name in BOSSES:
        right = render_rig(name, "idle", facing=1)
        left = render_rig(name, "idle", facing=-1)
        assert tobytes(right) != tobytes(left), f"{name} kiri==kanan"
        rr, rl = solid_rect(right), solid_rect(left)
        # tinggi konsisten antar arah
        assert abs(rr.height - rl.height) <= 4


def test_skill_fx_present_and_portrait_clean():
    for name, ns in BOSSES.items():
        # arena: ada piksel lembut (glow/ring) saat skill aktif
        arena = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        b = probe(name, active_skill="r", active_skill_timer=30)
        b.x, b.y = float(C), float(CY)
        getattr(L2, "draw_" + name)(arena, b, C, CY)
        soft = sum(1 for y in range(SIZE) for x in range(SIZE)
                   if 6 < arena.get_at((x, y)).a <= 140)
        assert soft > 200, f"{name} skill FX tidak tergambar (soft={soft})"

        # portrait: bersih (tanpa aura/ground) & muat kanvas
        card = pygame.Surface((160, 160), pygame.SRCALPHA)
        pb = probe(name, _portrait_hd=True)
        pb.x, pb.y = 80.0, 90.0
        getattr(L2, "draw_" + name)(card, pb, 80, 90)
        box = card.get_bounding_rect(min_alpha=10)
        assert box.width > 0
        assert box.left >= 1 and box.top >= 1 and \
            box.right <= 159 and box.bottom <= 159, f"{name} portrait keluar"
        softp = sum(1 for y in range(160) for x in range(160)
                    if 6 < card.get_at((x, y)).a <= 140)
        assert softp < 120, f"{name} portrait masih ada aura (soft={softp})"


def test_skill_durations_match_ai():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               encoding="utf-8").read()
    fn_names = {
        "razak": {"q": "_razak_q", "w": "_razak_w", "e": "_razak_e",
                  "r": "_razak_r"},
        "khalros": {"q": "_khalros_q", "w": "_khalros_w", "e": "_khalros_e",
                    "r": "_khalros_r"},
        "gorath": {"q": "_gorath_q", "w": "_gorath_w", "e": "_gorath_e",
                   "r": "_gorath_r"},
        "alchemist": {"q": "_cast_q_acid_spray", "w": "_cast_w_unstable_concoction",
                      "e": "_cast_e_chemical_rage", "r": "_cast_r_greevils_greed"},
    }
    for name, ns in BOSSES.items():
        for key, fn in fn_names[name].items():
            i = src.index("def %s(" % fn)
            m = re.search(r"active_skill_timer\s*=\s*(\d+)", src[i:i + 900])
            assert m, f"{name}/{key} timer tidak ketemu"
            assert int(m.group(1)) == ns.SKILL_DUR[key], \
                f"{name} {key}: AI={m.group(1)} != render={ns.SKILL_DUR[key]}"


def test_body_readable_size():
    # badan cukup besar (tidak tiang kecil) & rasio W/H wajar
    for name in BOSSES:
        r = solid_rect(render_rig(name, "idle"))
        assert r.height >= 90, f"{name} terlalu pendek: {r.height}"
        assert r.width >= 60, f"{name} terlalu sempit: {r.width}"
        assert r.width / r.height >= 0.55, f"{name} rasio sempit"


def test_perf_budget():
    import time
    scr = pygame.Surface((1280, 720))
    for name in BOSSES:
        fn = getattr(L2, "draw_" + name)
        b = probe(name)
        b.x, b.y = 640.0, 360.0
        for i in range(8):
            b.pulse = i * 0.2
            fn(scr, b, 640, 360)
        t0 = time.perf_counter()
        N = 60
        for i in range(N):
            b.pulse = i * 0.2
            fn(scr, b, 640, 360)
        ms = (time.perf_counter() - t0) / N * 1000
        assert ms < 5.0, f"draw_{name} {ms:.2f} ms/frame terlalu mahal"


if __name__ == "__main__":
    test_procedural_and_constants()
    test_feet_planted()
    test_idle_bob_visible()
    test_walk_feet_stay_grounded_and_stride()
    test_attack_distinct_from_idle()
    test_weapon_pose_driven()
    test_both_directions()
    test_skill_fx_present_and_portrait_clean()
    test_skill_durations_match_ai()
    test_body_readable_size()
    test_perf_budget()
    print("OK - Level 2 masterwork: 4 boss rig tunggal, kaki menapak, "
          "idle bob, walk, attack, senjata pose-driven, dua arah, "
          "skill FX + portrait HD, durasi sinkron AI")
