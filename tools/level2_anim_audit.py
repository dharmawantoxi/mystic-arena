#!/usr/bin/env python3
# ============================================================
# Audit: animasi boss Level 2 (Razak, Khalros, Gorath, Alchemist)
# ------------------------------------------------------------
# Render strip frame per aksi (idle / walk / attack) dan per skill
# (Q/W/E/R) dari kode bosses/level2.py ASLI, di atas panggung uji
# 1 lawan 1, lalu simpan PNG untuk inspeksi visual + cek error.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     /home/user/.venv/bin/python tools/level2_anim_audit.py
# ============================================================
import math
import os
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

STAGE_W, STAGE_H = 200, 170


class _FakeTarget:
    alive = True

    def __init__(self, x, y):
        self.x = x
        self.y = y


class _FakeBoss:
    """Tiru permukaan (surface) Boss untuk jalur render murni."""

    def __init__(self, kind, x, y):
        self.x = x
        self.y = y
        self.pulse = 0.0
        self.direction = 1
        self.timer = 0
        self.attack_cooldown = 45
        self.active_skill = None
        self.active_skill_timer = 0
        self.target = _FakeTarget(x + 120, y + 8)
        self._kind = kind

    def clone(self):
        """Salinan state-render (flag persisten TIDAK dibagikan)."""
        b = _FakeBoss(self._kind, self.x, self.y)
        b.pulse = self.pulse
        b.direction = self.direction
        b.timer = self.timer
        b.attack_cooldown = self.attack_cooldown
        b.active_skill = self.active_skill
        b.active_skill_timer = self.active_skill_timer
        return b


DRAWS = {
    "razak": L2.draw_razak,
    "khalros": L2.draw_khalros,
    "gorath": L2.draw_gorath,
    "alchemist": L2.draw_alchemist,
}

# Durasi AI (base_boss.py) sebagai ground truth untuk progress FX
import bosses.level2 as _L2
AI_DUR = {
    "razak": _L2._NS_razak.SKILL_DUR,
    "khalros": _L2._NS_khalros.SKILL_DUR,
    "gorath": _L2._NS_gorath.SKILL_DUR,
    "alchemist": _L2._NS_alchemist.SKILL_DUR,
}


def _font(size):
    return pygame.font.SysFont("dejavusans", size, bold=True)


def _label(sheet, text, x, y, size=14, color=(235, 235, 235)):
    surf = _font(size).render(text, True, color)
    sheet.blit(surf, (x, y))


def render_strip(kind, n, setup):
    """setup(boss, i) set state per frame; return Surface strip."""
    pad = 4
    strip = pygame.Surface((n * (STAGE_W + pad) + pad, STAGE_H + 22), pygame.SRCALPHA)
    strip.fill((18, 20, 30))
    for i in range(n):
        frame = pygame.Surface((STAGE_W, STAGE_H), pygame.SRCALPHA)
        frame.fill((24, 28, 42))
        pygame.draw.line(frame, (60, 70, 60), (0, STAGE_H - 34),
                         (STAGE_W, STAGE_H - 34), 1)
        boss = _FakeBoss(kind, STAGE_W // 2, STAGE_H - 60)
        setup(boss, i)
        try:
            DRAWS[kind](frame, boss, boss.x, boss.y)
        except Exception as exc:  # catat crash per frame
            err = _font(11).render(f"ERR: {exc}"[:30], True, (255, 80, 80))
            frame.blit(err, (4, 4))
            print(f"  !! {kind} frame {i}: {type(exc).__name__}: {exc}")
        strip.blit(frame, (pad + i * (STAGE_W + pad), 20))
        _label(strip, f"{i}", pad + i * (STAGE_W + pad) + 4, 4, 12, (160, 170, 190))
    return strip


def setup_idle(boss, i):
    boss.pulse = i * math.tau / 8


_MOVE_PREFIX = {"razak": "_razak", "khalros": "_khal",
                "gorath": "_gor", "alchemist": "_alch"}


def setup_walk(boss, i):
    boss.pulse = i * 1.1
    boss.x += math.sin(boss.pulse) * 2
    pre = _MOVE_PREFIX[boss._kind]
    # seed posisi sebelumnya agar _detect_moving() -> True
    setattr(boss, f"{pre}_last_x", boss.x - 4)
    setattr(boss, f"{pre}_last_y", boss.y)


def setup_attack(boss, i):
    boss._kind = boss._kind  # noqa
    boss.pulse = i * 0.4
    cd = 45
    prog = i / 8.0
    # Simulasikan state yang dibangun _update_attack_anim
    pre = {
        "razak": "_razak", "khalros": "_khal",
        "gorath": "_gor", "alchemist": "_alch",
    }[boss._kind]
    setattr(boss, f"{pre}_attack_active", True)
    setattr(boss, f"{pre}_attack_progress", prog)
    boss.timer = cd


def make_skill_setup(kind, key, n):
    dur = AI_DUR[kind][key]

    def setup(boss, i):
        boss.pulse = i * 0.7
        boss.active_skill = key
        # timer mundur dari durasi -> 1 (seperti engine)
        boss.active_skill_timer = max(1, int(dur - (i + 1) * (dur / n)))
    return setup


def main():
    out = os.path.join(ROOT, "tools", "_out")
    os.makedirs(out, exist_ok=True)
    rows_total = []
    for kind in ("razak", "khalros", "gorath", "alchemist"):
        rows = [
            (f"{kind.upper()} IDLE", render_strip(kind, 8, setup_idle)),
            (f"{kind.upper()} WALK", render_strip(kind, 8, setup_walk)),
            (f"{kind.upper()} ATTACK", render_strip(kind, 9, setup_attack)),
        ]
        for key in ("q", "w", "e", "r"):
            rows.append((f"{kind.upper()} SKILL {key.upper()} (AI dur {AI_DUR[kind][key]})",
                         render_strip(kind, 8, make_skill_setup(kind, key, 8))))
        rows_total.extend(rows)

    w = max(s.get_width() for _, s in rows_total)
    h = sum(s.get_height() for _, s in rows_total) + 6 * len(rows_total)
    canvas = pygame.Surface((w, h))
    canvas.fill((10, 12, 18))
    y = 0
    prev_kind = None
    for title, strip in rows_total:
        kind = title.split()[0].lower()
        if kind != prev_kind:
            tt = _font(18).render(f"== {kind.upper()} ==", True, (255, 220, 140))
            canvas.blit(tt, (6, y + 2))
            y += 26
            prev_kind = kind
        _label(canvas, title, 8, y + 2, 13, (255, 210, 130))
        canvas.blit(strip, (0, y + 18))
        y += strip.get_height() + 6
    path = os.path.join(out, "level2_anim_audit.png")
    pygame.image.save(canvas, path)
    print("saved:", path, canvas.get_size())


if __name__ == "__main__":
    main()
