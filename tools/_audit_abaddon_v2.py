#!/usr/bin/env python3
"""Audit + preview sheet Abaddon v2 + Skill FX v2.1."""
import math, os, sys, time
from types import SimpleNamespace as _NS
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
from bosses.level1 import _NS_abaddon as A, draw_abaddon

def check(cond, label, extra=""):
    print(f"[{'OK ' if cond else 'FAIL'}] {label} {extra}")
    return cond

ok_all = True
for helper in ("_fx_scale", "_spark_star", "_chevron", "_dashed_ring",
               "_tuft_points", "_static", "_dither_dots", "_ring_r"):
    ok_all &= check(callable(getattr(A, helper, None)), f"helper {helper}")

scratch = pygame.Surface((460, 460), pygame.SRCALPHA)
probe = _NS(boss_type="abaddon", x=230.0, y=230.0, direction=1, facing=1,
            pulse=1.3, timer=0, attack_cooldown=50, active_skill=None,
            active_skill_timer=0, target=None, hurt_flash_timer=0,
            alive=True, radius=50, hp=1, max_hp=1)

def bench_med(fn, n=15, reps=5):
    fn()
    runs = []
    for _ in range(reps):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        runs.append((time.perf_counter() - t0) / n * 1000)
    runs.sort()
    return runs[len(runs)//2]

t_full = bench_med(lambda: A.draw_abaddon(scratch, probe, 230, 230))
print(f"[i] draw_abaddon {t_full:.2f} ms")
ok_all &= check(t_full <= 3.5, "budget cache-miss", f"{t_full:.2f} ms")

# skill presence
for skill, t in (("q", 30), ("w", 50), ("e", 25), ("r", 30)):
    s = pygame.Surface((460, 460), pygame.SRCALPHA)
    h = _NS(boss_type="abaddon", x=230.0, y=230.0, direction=1, pulse=1.2,
            timer=0, attack_cooldown=50, active_skill=skill,
            active_skill_timer=t, target=_NS(x=340, y=230, alive=True),
            hurt_flash_timer=0, alive=True, radius=50)
    A.draw_abaddon(s, h, 230, 230)
    n = sum(1 for y in range(0, 460, 4) for x in range(0, 460, 4)
            if s.get_at((x, y)).a > 40)
    ok_all &= check(n > 80, f"skill {skill} pixels", str(n))

os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
font_title = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 20)
W, H = 1400, 720
sheet = pygame.Surface((W, H)); sheet.fill((6, 7, 16))
sheet.blit(font_title.render("ABADDON v2 — PIXEL MASTERWORK + SKILL FX v2.1", True, (160, 250, 250)), (28, 18))
cards = (("IDLE", None, 0), ("WALK", None, 0), ("Q MIST COIL", "q", 28),
         ("W APHOTIC", "w", 50), ("E GALE", "e", 24), ("R DEATH SEVER", "r", 28))
for i, (lab, sk, tm) in enumerate(cards):
    x = 20 + (i % 6) * 228
    y = 80
    pygame.draw.rect(sheet, (18, 12, 32), (x, y, 216, 580), border_radius=10)
    sheet.blit(font_small.render(lab, True, (220, 240, 255)), (x + 10, y + 8))
    native = pygame.Surface((216, 540), pygame.SRCALPHA)
    h = _NS(boss_type="abaddon", x=108.0, y=280.0, direction=1, pulse=1.4 + i,
            timer=0, attack_cooldown=50, active_skill=sk, active_skill_timer=tm,
            target=_NS(x=160, y=270, alive=True), hurt_flash_timer=0,
            alive=True, radius=50)
    if lab == "WALK":
        h._ab_last_x = 100.0; h._ab_last_y = 280.0
    A.draw_abaddon(native, h, 108, 280)
    sheet.blit(native, (x, y + 32))
out = os.path.join(ROOT, "docs", "abaddon_v2_review.png")
pygame.image.save(sheet, out)
print(out)

# anim strip
strip = pygame.Surface((1400, 420)); strip.fill((6, 7, 16))
strip.blit(font_title.render("ABADDON v2 — IDLE / WALK / ATTACK", True, (160, 250, 250)), (24, 12))
for i in range(10):
    native = pygame.Surface((130, 180), pygame.SRCALPHA)
    h = _NS(boss_type="abaddon", x=65.0, y=110.0, direction=1, pulse=i * 0.4,
            timer=0, attack_cooldown=50, active_skill=None, active_skill_timer=0,
            target=None, hurt_flash_timer=0, alive=True, radius=50,
            _ab_attack_active=(i >= 6), _ab_attack_progress=(i-6)/4 if i>=6 else 0)
    A.draw_abaddon(native, h, 65, 110)
    strip.blit(native, (20 + i * 136, 70))
out2 = os.path.join(ROOT, "docs", "abaddon_v2_anim_strip.png")
pygame.image.save(strip, out2)
print(out2)

print("SEMUA CEK LOLOS" if ok_all else "ADA CEK GAGAL")
sys.exit(0 if ok_all else 1)
