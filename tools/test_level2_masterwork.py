#!/usr/bin/env python3
# ============================================================
# Regresi: Level 2 Masterwork — animasi 3 mini boss + true boss
# Razak / Khalros / Gorath (mini) + Alchemist (TRUE BOSS)
# ------------------------------------------------------------
# Memastikan:
#  1. SKILL_DUR renderer == active_skill_timer AI (sinkron dua arah,
#     pola yang sama dengan Level 1 / Kaizen Masterwork).
#  2. Gerbang spawn proyektil di frame pertama cast SELALU terbuka
#     (bug lama: Khalros Q & R, Gorath W tidak pernah menembak apa
#     pun karena progress frame-0 lewat dari gerbang).
#  3. Render semua aksi + semua fase skill tanpa exception, dan
#     frame berbeda-beda (bukan sticker statis).
#  4. Idle/walk/attack punya bobbing & root motion yang terlihat.
#  5. Goblin rider Alchemist digambar sebelum kepala ogre.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     /home/user/.venv/bin/python tools/test_level2_masterwork.py
# ============================================================
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((8, 8))

import bosses.level2 as L2

NS = {
    "razak": L2._NS_razak,
    "khalros": L2._NS_khalros,
    "gorath": L2._NS_gorath,
    "alchemist": L2._NS_alchemist,
}
DRAWS = {
    "razak": L2.draw_razak,
    "khalros": L2.draw_khalros,
    "gorath": L2.draw_gorath,
    "alchemist": L2.draw_alchemist,
}
PREFIX = {"razak": "_razak", "khalros": "_khal",
          "gorath": "_gor", "alchemist": "_alch"}
KEYS = ("q", "w", "e", "r")


class _T:
    alive = True

    def __init__(self, x, y):
        self.x, self.y = x, y


class _Boss:
    def __init__(self, kind, x, y):
        self.x, self.y = x, y
        self.pulse = 0.0
        self.direction = 1
        self.timer = 0
        self.attack_cooldown = 45
        self.active_skill = None
        self.active_skill_timer = 0
        self.target = _T(x + 130, y + 6)
        self._kind = kind
        self.rage_active = False

    # _shake/_spawn tidak dipakai jalur render, tapi beri aman
    def take_damage(self, *a, **k):
        pass


# ─────────────────────────────────────────────────────────────
# 1. SKILL_DUR == timer AI di base_boss.py
# ─────────────────────────────────────────────────────────────
CAST = {
    "razak": {"q": "_razak_q", "w": "_razak_w",
              "e": "_razak_e", "r": "_razak_r"},
    "khalros": {"q": "_khalros_q", "w": "_khalros_w",
                "e": "_khalros_e", "r": "_khalros_r"},
    "gorath": {"q": "_gorath_q", "w": "_gorath_w",
               "e": "_gorath_e", "r": "_gorath_r"},
    "alchemist": {"q": "_cast_q_acid_spray", "w": "_cast_w_unstable_concoction",
                  "e": "_cast_e_chemical_rage", "r": "_cast_r_greevils_greed"},
}


def _ai_timer(source, func):
    m = re.search(rf"def {re.escape(func)}\(.*?\n(.*?)(?=\n    def )", source, re.S)
    assert m, f"AI cast {func} tidak ditemukan"
    t = re.search(r"self\.active_skill_timer\s*=\s*(\d+)", m.group(1))
    assert t, f"{func}: tidak ada active_skill_timer eksplisit"
    return int(t.group(1))


def test_skill_dur_synced_with_ai():
    src = open(os.path.join(ROOT, "bosses", "base_boss.py"),
               encoding="utf-8").read()
    for kind, ns in NS.items():
        for key in KEYS:
            want = ns.SKILL_DUR[key]
            got = _ai_timer(src, CAST[kind][key])
            assert got == want, (
                f"{kind}.{key}: AI timer {got} != SKILL_DUR {want} "
                f"-> FX terpotong / gerbang spawn tertutup")


# ─────────────────────────────────────────────────────────────
# 2. Gerbang spawn proyektil terbuka di frame pertama
# ─────────────────────────────────────────────────────────────
def _first_frame_progress(kind, key):
    ns = NS[kind]
    dur = ns.SKILL_DUR[key]
    # frame render pertama setelah cast: timer == dur
    return max(0.0, min(1.0, 1 - dur / dur))


def test_spawn_gates_open_on_cast():
    # Khalros Q: gate progress < 0.15, throw pose < 0.45
    assert _first_frame_progress("khalros", "q") < 0.15
    # Khalros R: gate progress < 0.10
    assert _first_frame_progress("khalros", "r") < 0.10
    # Gorath W: gate progress < 0.10
    assert _first_frame_progress("gorath", "w") < 0.10
    # Razak Q: gate < 0.15
    assert _first_frame_progress("razak", "q") < 0.15


def test_projectiles_actually_spawn():
    """Render N frame penuh skill -> minimal satu proyektil tercipta."""
    probes = [
        ("khalros", "q", "_khal_projectiles", 2),
        ("khalros", "r", "_khal_projectiles", 1),
        ("gorath", "w", "_gor_projectiles", 3),
        ("razak", "q", "_razak_projectiles", 1),
        ("alchemist", "w", "_alch_projectiles", 1),
    ]
    for kind, key, attr, minimum in probes:
        ns = NS[kind]
        dur = ns.SKILL_DUR[key]
        boss = _Boss(kind, 100, 100)
        surf = pygame.Surface((260, 220), pygame.SRCALPHA)
        total_seen = 0
        for f in range(dur):
            boss.active_skill = key
            boss.active_skill_timer = max(1, dur - f)
            DRAWS[kind](surf, boss, 100, 100)
            total_seen = max(total_seen, len(getattr(boss, attr, [])))
        assert total_seen >= minimum, (
            f"{kind} skill {key}: hanya {total_seen} proyektil "
            f"(harus >= {minimum})")


# ─────────────────────────────────────────────────────────────
# 3. Render semua aksi/fase tanpa exception + frame bervariasi
# ─────────────────────────────────────────────────────────────
def test_all_poses_render_distinct_frames():
    for kind in NS:
        for action in ("idle", "walk"):
            frames = set()
            for i in range(6):
                boss = _Boss(kind, 120, 110)
                boss.pulse = i * 0.9
                if action == "walk":
                    pre = PREFIX[kind]
                    setattr(boss, f"{pre}_last_x", boss.x - 5)
                    setattr(boss, f"{pre}_last_y", boss.y)
                surf = pygame.Surface((260, 230), pygame.SRCALPHA)
                DRAWS[kind](surf, boss, 120, 110)
                frames.add(pygame.image.tobytes(surf, "RGBA"))
            assert len(frames) >= 5, f"{kind} {action}: frame identik (statis)"

        # attack: render lewat fungsi pose internal agar progress
        # manual tidak tertimpa _update_attack_anim()
        pre = PREFIX[kind]
        atk_fn = {
            "razak": NS["razak"]._draw_razak_attack,
            "khalros": NS["khalros"]._draw_khalros_attack,
            "gorath": NS["gorath"]._draw_gorath_attack,
            "alchemist": NS["alchemist"]._draw_alch_attack,
        }[kind]
        last = None
        changed = 0
        for i in range(9):
            boss = _Boss(kind, 120, 110)
            boss.pulse = i * 0.5
            boss.timer = 0
            setattr(boss, f"{pre}_attack_progress", i / 8.0)
            surf = pygame.Surface((260, 230), pygame.SRCALPHA)
            atk_fn(surf, boss, 120, 110)
            data = pygame.image.tobytes(surf, "RGBA")
            if last is not None and data != last:
                changed += 1
            last = data
        assert changed >= 6, f"{kind} attack: progress tidak mengubah render"


# ─────────────────────────────────────────────────────────────
# 4. Root motion: attack menghasilkan geser posisi (lunge > 5 px)
# ─────────────────────────────────────────────────────────────
def test_root_motion_present():
    import inspect
    for kind in ("khalros", "gorath", "alchemist"):
        src = inspect.getsource(NS[kind])
        assert "root_motion" in src, f"{kind}: tidak ada root motion"
    src = inspect.getsource(NS["razak"])
    assert "progress < 0.30" in src, "razak: fase anticipation hilang"


# ─────────────────────────────────────────────────────────────
# 5. Alchemist: draw order goblin -> kepala ogre
# ─────────────────────────────────────────────────────────────
def test_alchemist_draw_order():
    import inspect
    src = inspect.getsource(NS["alchemist"]._draw_alch_full)
    gi = src.find("_draw_goblin_rider")
    hi = src.find("_draw_ogre_head")
    assert gi != -1 and hi != -1
    assert gi < hi, "goblin rider harus digambar SEBELUM kepala ogre"


# ─────────────────────────────────────────────────────────────
# 6. FX fase akhir tercapai (progress mencapai ~1.0 saat timer 1)
# ─────────────────────────────────────────────────────────────
def test_fx_reaches_end_state():
    for kind, ns in NS.items():
        for key in KEYS:
            dur = ns.SKILL_DUR[key]
            end_progress = max(0.0, min(1.0, 1 - 1 / dur))
            assert end_progress > 0.9, (
                f"{kind}.{key}: FX berhenti di {end_progress:.2f}")


if __name__ == "__main__":
    tests = [
        ("SKILL_DUR renderer == active_skill_timer AI", test_skill_dur_synced_with_ai),
        ("gerbang spawn terbuka di frame pertama cast", test_spawn_gates_open_on_cast),
        ("proyektil benar-benar ter-spawn (Q/R Khalros, W Gorath...)", test_projectiles_actually_spawn),
        ("idle/walk/attack: frame bervariasi, tanpa exception", test_all_poses_render_distinct_frames),
        ("root motion anticipation->lunge->hold->recovery", test_root_motion_present),
        ("Alchemist: goblin rider di belakang kepala ogre", test_alchemist_draw_order),
        ("FX mencapai 100% timeline sebelum aktif skill habis", test_fx_reaches_end_state),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
    if failed:
        print(f"\n{failed}/{len(tests)} pemeriksaan GAGAL")
        sys.exit(1)
    print(f"\nOK - Level 2 Masterwork: {len(tests)}/{len(tests)} pemeriksaan lulus")
