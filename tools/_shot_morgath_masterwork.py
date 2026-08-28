#!/usr/bin/env python3
"""Render review sheet untuk Morgath Procedural Masterwork.

Menghasilkan:
  - docs/morgath_masterwork_preview.png  (7 pose skill + barisan 1x arena)
  - docs/morgath_before_after.png        (rig lama 35x55 vs rig masterwork)
  - docs/morgath_portrait_preview.png    (LOD portrait Hero Shop)

Jalankan:  python3 tools/_shot_morgath_masterwork.py
"""
import math
import os
import subprocess
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
from bosses import level1

BG = (7, 8, 16)
PANEL = (12, 13, 26)
PANEL_EDGE = (60, 68, 120)
ACCENT = (140, 190, 250)
SUB = (120, 130, 170)
NOTE = (96, 100, 130)

CANVAS = 240
ANCHOR = (CANVAS // 2, CANVAS // 2 + 10)


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="morgath", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=0.0,
                        timer=0, attack_cooldown=48, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=51)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def frame(boss, renderer=None, zoom=2.0, rig_only=False):
    """Render ke canvas 240 lalu crop di sekitar jangkar + zoom nearest."""
    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    if rig_only:
        M._draw_mor_rig(surf, ANCHOR[0], ANCHOR[1], 1, boss.pulse,
                        rig_only, getattr(boss, "_ap", 0.0), False)
    else:
        (renderer or level1.draw_morgath)(surf, boss, *ANCHOR)
    cw, ch = 150, 128
    crop = surf.subsurface(pygame.Rect(ANCHOR[0] - cw // 2,
                                       ANCHOR[1] - 92, cw, ch)).copy()
    return pygame.transform.scale(crop, (int(cw * zoom), int(ch * zoom)))


def dense(surf, thr=100):
    mask = pygame.mask.from_surface(surf, thr)
    rs = mask.get_bounding_rects()
    if not rs:
        return None
    x0 = min(r.x for r in rs); y0 = min(r.y for r in rs)
    x1 = max(r.right for r in rs); y1 = max(r.bottom for r in rs)
    return pygame.Rect(x0, y0, x1 - x0, y1 - y0)


def label(draw_surf, font, small, x, y, title, lines):
    pygame.draw.rect(draw_surf, PANEL_EDGE, (x, y, 204, 316), 1)
    pygame.draw.rect(draw_surf, PANEL, (x + 1, y + 1, 202, 314))
    draw_surf.blit(font.render(title, True, ACCENT), (x + 8, y + 6))


def old_renderer():
    """Renderer morgath LAMA dari commit dasar (untuk before/after)."""
    base = subprocess.run(
        ["git", "show", "b882c9f4ad0eceee8b79385120c5babdf9b81d8d:bosses/level1.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tmp = os.path.join(ROOT, "tools", "_old_level1_snapshot.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    import importlib.util
    spec = importlib.util.spec_from_file_location("_old_level1", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod.draw_morgath


def make_preview(docs):
    font = pygame.font.Font(None, 20)
    small = pygame.font.Font(None, 16)
    sheet = pygame.Surface((4 * 212 + 8, 2 * 330 + 190))
    sheet.fill(BG)

    poses = [
        ("idle", probe(pulse=0.7), None),
        ("walk", probe(pulse=0.45), None),
        ("attack thrust", probe(timer=22), "attack"),
        ("Q Spark Wraith", probe(active_skill="q", active_skill_timer=38,
                                 pulse=0.7), None),
        ("W Flux", probe(active_skill="w", active_skill_timer=30,
                         pulse=0.7), None),
        ("E Magnetic Field", probe(active_skill="e", active_skill_timer=50,
                                   pulse=0.7), None),
        ("R Tempest (clone+aftermath)", probe(active_skill="r", active_skill_timer=46,
                                   pulse=0.7), None),
        ("beam flight", probe(timer=10), "beam"),
    ]
    for i, (title, boss, mode) in enumerate(poses):
        col, rowi = i % 4, i // 4
        x, y = 8 + col * 212, 8 + rowi * 330
        pygame.draw.rect(sheet, PANEL_EDGE, (x, y, 204, 316), 1)
        pygame.draw.rect(sheet, PANEL, (x + 1, y + 1, 202, 314))
        sheet.blit(font.render(title, True, ACCENT), (x + 8, y + 6))
        if mode == "attack":
            boss._mor_attack_active = True
            boss.timer = 22
            boss._mor_previous_timer = 26
            boss._mor_attack_dir = 1
            boss._mor_attack_target = (200, 0)
            boss.target = SimpleNamespace(x=boss.x + 200, y=boss.y, alive=True)
        elif mode == "beam":
            boss._mor_attack_active = True
            boss.timer = 8
            boss._mor_previous_timer = 12
            boss._mor_attack_dir = 1
            boss._mor_attack_target = (190, -14)
            boss.target = SimpleNamespace(x=boss.x + 190,
                                          y=boss.y - 14, alive=True)
        img = frame(boss)
        sheet.blit(img, (x + 102 - img.get_width() // 2,
                         y + 170 - img.get_height() // 2))

    # Barisan 1x (ukuran arena sesungguhnya) + penggaris
    base_y = 2 * 330 + 20
    sheet.blit(font.render(
        "ukuran arena 1x (boss, tanpa zoom) - badan padat ~49x84 px; "
        "rujukan keluarga: gornak H119, drakar H138, abaddon H122",
        True, SUB), (12, base_y))
    xs = 40
    for i, ph in enumerate((0.0, 0.9, 1.8, 2.7)):
        boss = probe(pulse=ph)
        img = frame(boss, zoom=1.0)
        sheet.blit(img, (xs, base_y + 22))
        xs += img.get_width() + 26
    sheet.blit(small.render(
        "hem jubah dipatok di garis tanah (GROUND_DY); beam lahir dari "
        "telapak cast; antena arc = tell charge serangan",
        True, NOTE), (12, base_y + 148))

    out = os.path.join(docs, "morgath_masterwork_preview.png")
    pygame.image.save(sheet, out)
    return out


def make_before_after(docs, old_draw):
    font = pygame.font.Font(None, 22)
    small = pygame.font.Font(None, 16)
    sheet = pygame.Surface((560, 420))
    sheet.fill(BG)

    # BEFORE: renderer dari commit dasar
    surf_old = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    old_draw(surf_old, probe(pulse=0.7), *ANCHOR)
    r_old = dense(surf_old)
    img_old = pygame.transform.scale(
        surf_old.subsurface(pygame.Rect(ANCHOR[0] - 45, ANCHOR[1] - 50,
                                        90, 108)).copy(), (270, 324))

    # AFTER: rig masterwork
    surf_new = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    level1.draw_morgath(surf_new, probe(pulse=0.7), *ANCHOR)
    r_new = dense(surf_new)
    img_new = pygame.transform.scale(
        surf_new.subsurface(pygame.Rect(ANCHOR[0] - 45, ANCHOR[1] - 56,
                                        90, 108)).copy(), (270, 324))

    sheet.blit(font.render("SEBELUM (tumpukan body-part)", True,
                           (250, 120, 120)), (20, 12))
    sheet.blit(img_old, (20, 40))
    sheet.blit(small.render(f"bbox+FX ~{r_old.width}x{r_old.height}",
                            True, NOTE), (20, 372))
    sheet.blit(small.render("badan padat 35x55; orb r=6; beam titik lepas",
                            True, NOTE), (20, 388))
    sheet.blit(font.render("SESUDAH (bone rig masterwork)", True,
                           (140, 230, 160)), (290, 12))
    sheet.blit(img_new, (290, 40))
    sheet.blit(small.render(f"bbox+FX ~{r_new.width}x{r_new.height}",
                            True, NOTE), (290, 372))
    sheet.blit(small.render("badan padat ~49x84; orb r=9 + shard orbit",
                            True, NOTE), (290, 388))
    sheet.blit(small.render("jubah A-line menapak; beam dari telapak",
                            True, NOTE), (290, 404))

    out = os.path.join(docs, "morgath_before_after.png")
    pygame.image.save(sheet, out)
    return out


def make_portrait(docs):
    font = pygame.font.Font(None, 20)
    sheet = pygame.Surface((300, 300))
    sheet.fill(BG)
    boss = probe(pulse=0.7, _portrait_hd=True)
    del boss._render_scale          # Hero Shop tidak men-set _render_scale
    pc = pygame.Surface((160, 160), pygame.SRCALPHA)
    level1.draw_morgath(pc, boss, 80, 80)
    big = pygame.transform.scale(pc, (240, 240))
    sheet.blit(big, (30, 10))
    sheet.blit(font.render("portrait LOD (Hero Shop): FX arena dibuang",
                           True, SUB), (10, 258))
    out = os.path.join(docs, "morgath_portrait_preview.png")
    pygame.image.save(sheet, out)
    return out


if __name__ == "__main__":
    docs = os.path.join(ROOT, "docs")
    os.makedirs(docs, exist_ok=True)
    print("sheet :", make_preview(docs))
    print("diff  :", make_before_after(docs, old_renderer()))
    print("potret:", make_portrait(docs))
