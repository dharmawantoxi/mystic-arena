#!/usr/bin/env python3
# ============================================================
# Sheet review: Level 2 Masterwork - before vs after
# ------------------------------------------------------------
# Render boss Level 2 (Razak, Khalros, Gorath, Alchemist) dengan
# kode LAMA (commit HEAD) berdampingan dengan kode BARU, per aksi:
# idle, walk, attack (progress internal dipanggil langsung),
# dan keempat fase skill FX.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     /home/user/.venv/bin/python tools/_shot_level2_masterwork.py
# Output: docs/level2_masterwork_preview.png
# ============================================================
import importlib.util
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((8, 8))


def _load_mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


TMP_OLD = os.path.join(ROOT, "tools", "_out", "_level2_old_tmp.py")
os.makedirs(os.path.dirname(TMP_OLD), exist_ok=True)
with open(TMP_OLD, "w", encoding="utf-8") as f:
    f.write(subprocess.check_output(
        ["git", "-C", ROOT, "show", "HEAD:bosses/level2.py"]
    ).decode("utf-8"))

OLD = _load_mod(TMP_OLD, "level2_old")
NEW = _load_mod(os.path.join(ROOT, "bosses", "level2.py"), "level2_new")

KINDS = ("razak", "khalros", "gorath", "alchemist")
ENTRIES = {
    "razak": "draw_razak", "khalros": "draw_khalros",
    "gorath": "draw_gorath", "alchemist": "draw_alchemist",
}
NS = {k: f"_NS_{k}" for k in KINDS}
PRE = {"razak": "_razak", "khalros": "_khal",
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
        self.target = _T(x + 150, y + 6)
        self.rage_active = False
        self._kind = kind


W, H = 236, 196


def _render(mod, kind, mode, i, dur_key=None):
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    surf.fill((24, 27, 44))
    pygame.draw.line(surf, (66, 76, 66), (0, H - 52), (W, H - 52), 1)
    b = _Boss(kind, W // 2 - 40, H - 84)
    ns = getattr(mod, NS[kind])
    pre = PRE[kind]
    b.pulse = i * 1.05
    if mode == "walk":
        setattr(b, f"{pre}_last_x", b.x - 4 - i)
        setattr(b, f"{pre}_last_y", b.y)
        getattr(mod, ENTRIES[kind])(surf, b, b.x, b.y)
    elif mode == "attack":
        fn = getattr(ns, f"_draw_{kind if kind != 'alchemist' else 'alch'}_attack")
        setattr(b, f"{pre}_attack_progress", 0.15 + i * 0.115)
        fn(surf, b, b.x, b.y)
    elif mode.startswith("skill"):
        key = mode[6]
        b.active_skill = key
        dur = getattr(ns, "SKILL_DUR", {}).get(key, 60)
        b.active_skill_timer = max(1, dur - int((i + 1) * dur / 6))
        if kind in ("gorath", "alchemist") and key == "e":
            b.rage_active = True
        getattr(mod, ENTRIES[kind])(surf, b, b.x, b.y)
    else:  # idle
        getattr(mod, ENTRIES[kind])(surf, b, b.x, b.y)
    return surf


def _strip_pair(kind, mode, n=6, title=""):
    label = pygame.font.Font(None, 15).render(title, True, (255, 215, 140))
    pad = 2
    w = n * (W + pad) + pad
    h = 16 + (H + 24) * 2 + pad
    sheet = pygame.Surface((w, h))
    sheet.fill((14, 16, 24))
    sheet.blit(label, (4, 1))
    y = 17
    for row, tag in ((0, OLD), (1, NEW)):
        xs = pad
        for i in range(n):
            img = _render(tag, kind, mode, i)
            s = pygame.transform.smoothscale(img, (W // 2, H // 2))
            sheet.blit(s, (xs, y))
            xs += W // 2 + pad
        y += H // 2 + 22
        txt = "BEFORE" if row == 0 else "AFTER"
        sheet.blit(pygame.font.Font(None, 12).render(txt, True,
               (150, 160, 190)), (4, y - 18))
    return sheet


def main():
    sheets = []
    for kind in KINDS:
        rows = [
            (f"{kind.upper()} · idle + walk", "idle"),
            (f"{kind.upper()} · walk", "walk"),
            (f"{kind.upper()} · attack (progress 0.15->0.72)", "attack"),
        ]
        # satu sheet gabungan untuk skill: render 4 skill 6 fase
        sheets.append((kind, rows))

    per_kind = []
    for kind, rows in sheets:
        pair_sheets = [_strip_pair(kind, m, title=t) for t, m in rows]
        skill_sheets = [_strip_pair(kind, f"skill_{k}", 6,
                        title=f"{kind.upper()} · skill {k.upper()}")
                        for k in KEYS]
        all_s = pair_sheets + skill_sheets
        w = max(s.get_width() for s in all_s)
        h = sum(s.get_height() for s in all_s) + 8 * len(all_s)
        block = pygame.Surface((w, h))
        block.fill((10, 12, 18))
        y = 0
        for s in all_s:
            block.blit(s, (0, y))
            y += s.get_height() + 8
        per_kind.append(block)

    w = max(b.get_width() for b in per_kind)
    h = sum(b.get_height() for b in per_kind) + 40
    canvas = pygame.Surface((w, h))
    canvas.fill((8, 9, 14))
    y = 0
    for b in per_kind:
        canvas.blit(b, (0, y))
        y += b.get_height() + 10
    out = os.path.join(ROOT, "docs", "level2_masterwork_preview.png")
    pygame.image.save(canvas, out)
    print("saved:", out, canvas.get_size())
    os.remove(TMP_OLD)


if __name__ == "__main__":
    main()
