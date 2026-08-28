#!/usr/bin/env python3
"""Sheet pass visual jalur HERO untuk Gornak.

Membandingkan render Gornak-SEBAGAI-HERO lewat pipeline yang sama seperti
game (heroes.render_hero + sprite cache untuk lane, dan kanvas 160x160 ala
ui_components.HeroPortraits untuk Hero Shop), berdampingan dengan hero
masterwork lain. Panel "sebelum" dirender dari commit sebelum pass visual
(diambil via `git show`), jadi bisa dibangun ulang tanpa menyimpan salinan
kode lama di repo.

Jalankan:
  python3 tools/_shot_gornak_hero_pass.py
  GORNAK_HERO_BEFORE_REF=<sha> python3 tools/_shot_gornak_hero_pass.py
"""
import importlib.util
import math
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
import _core                                          # noqa: F401 (shim)
import heroes
from heroes import _ProbeEntity, render_hero, clear_hero_sprite_cache

BEFORE_REF = os.environ.get("GORNAK_HERO_BEFORE_REF", "HEAD~1")
ACCENT = (200, 168, 246)
SUB = (150, 128, 178)
PANEL = (11, 10, 24)
PANEL_EDGE = (86, 52, 128)


def load_boss_render(namespace_attr, ref=None):
    """Ambil class `_NS_gornak` dari repo saat ini, atau `git show <ref>`."""
    if ref:
        try:
            src = subprocess.run(
                ["git", "-C", ROOT, "show", f"{ref}:bosses/level1.py"],
                capture_output=True, check=True).stdout.decode("utf-8")
        except Exception as exc:
            print(f"[skip] ref {ref} tidak tersedia ({exc})")
            return None
        with tempfile.NamedTemporaryFile("w", suffix=".py",
                                         delete=False) as fh:
            fh.write(src)
            path = fh.name
        try:
            spec = importlib.util.spec_from_file_location("_gornak_prev",
                                                           path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, namespace_attr)
        finally:
            os.unlink(path)
    import bosses.level1 as cur
    return getattr(cur, namespace_attr)


def fake_boss(G, cx, cy, portrait=False, pulse=1.35):
    """Objek boss untuk draw_gornak() - sengaja eksplisit, bukan _ProbeEntity,
    supaya mode portrait/lane memakai jalur yang sama seperti game."""
    return SimpleNamespace(boss_type="gornak", boss_class="mini", x=float(cx),
                           y=float(cy), direction=1, facing=1, pulse=pulse,
                           timer=0, attack_cooldown=38, active_skill=None,
                           active_skill_timer=0, target=None,
                           _render_scale=1.0, hurt_flash_timer=0, alive=True,
                           radius=30, is_retreating=False,
                           _portrait_hd=portrait)


def lane_render(G, hero_type, size=300, zoom=3, portrait=False):
    """Lane: render_hero() + sprite cache + HD edge, sama seperti di game."""
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    if hero_type == "gornak" and G is not None:
        # jalur hero memakai BOSS_RENDERERS -> draw_gornak; dipanggil lewat
        # render_hero supaya cache & _finish_hd_sprite ikut teruji
        clear_hero_sprite_cache()
        heroes.BOSS_RENDERERS["gornak"] = G.draw_gornak
        h = _ProbeEntity("gornak", cx, cy)
        h.pulse = 1.35
        h.direction = 1
        h.team = "blue"
        render_hero("gornak", canvas, h, cx, cy)
    else:
        clear_hero_sprite_cache()
        h = _ProbeEntity(hero_type, cx, cy)
        h.pulse = 1.35
        h.direction = 1
        h.team = "blue"
        render_hero(hero_type, canvas, h, cx, cy)
    rect = canvas.get_bounding_rect(min_alpha=100).inflate(12, 12).clip(
        canvas.get_rect())
    img = canvas.subsurface(rect).copy()
    return pygame.transform.scale(img, (rect.w * zoom, rect.h * zoom)), rect


def shop_render(G, size=160, zoom=4):
    """Hero Shop: kanvas 160x160 + crop bbox, meniru HeroPortraits.

    Return (gambar, info). Kalau konten menyentuh tepi kanvas, itu berarti
    bilah/jubah TERPOTONG sebelum di-crop (bug yang diperbaiki pass visual),
    jadi kasusnya ditandai dan digambar garis merah di tepi tersebut.
    """
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 10
    if G is None:
        return pygame.Surface((1, 1), pygame.SRCALPHA), None
    G.draw_gornak(canvas, fake_boss(G, cx, cy, portrait=True), cx, cy)
    bbox = canvas.get_bounding_rect(min_alpha=10)
    clipped = [bbox.left <= 0, bbox.top <= 0,
               bbox.right >= size, bbox.bottom >= size]
    out = pygame.transform.scale(canvas, (size * zoom, size * zoom))
    pygame.draw.rect(out, (96, 70, 140),
                     (bbox.left * zoom, bbox.top * zoom,
                      bbox.width * zoom, bbox.height * zoom), 1)
    for hits, rect in ((clipped[0], pygame.Rect(0, 0, 3, out.get_height())),
                       (clipped[2], pygame.Rect(out.get_width() - 3, 0, 3,
                                                 out.get_height())),
                       (clipped[1], pygame.Rect(0, 0, out.get_width(), 3)),
                       (clipped[3], pygame.Rect(0, out.get_height() - 3,
                                                out.get_width(), 3))):
        if hits:
            pygame.draw.rect(out, (255, 70, 70), rect)
    info = ("%dx%dpx" % (bbox.width, bbox.height)) + (
        "  TERPOTONG" if any(clipped) else "  utuh")
    return out, info


def main():
    G_before = load_boss_render("_NS_gornak", BEFORE_REF)
    G_after = load_boss_render("_NS_gornak", None)
    if G_after is None:
        sys.exit(1)
    if G_before is None:
        print(f"[info] ref {BEFORE_REF} tidak ada; hanya panel 'sesudah'")

    f_title = pygame.font.Font(None, 28)
    f_lbl = pygame.font.Font(None, 20)
    W, H = 1280, 700
    s = pygame.Surface((W, H))
    s.fill((6, 7, 15))
    s.blit(f_title.render(
        "GORNAK - pass visual jalur HERO (zoom 3x; ukuran TIDAK diubah di "
        "pass ini)", True, ACCENT), (30, 16))

    cells = []
    if G_before is not None:
        img, r = lane_render(G_before, "gornak")
        cells.append(("SEBELUM · lane (render_hero + cache)", img,
                      "%dx%d px" % (r.width, r.height)))
    img, r = lane_render(G_after, "gornak")
    cells.append(("SESUDAH · lane", img, "%dx%d px" % (r.width, r.height)))
    if G_before is not None:
        img2, info2 = shop_render(G_before)
        cells.append(("SEBELUM · Hero Shop (canvas 160)", img2, info2))
    img2, info2 = shop_render(G_after)
    cells.append(("SESUDAH · Hero Shop (canvas 160)", img2, info2))
    img3, r3 = lane_render(None, "grimjaw")
    cells.append(("rujukan · grimjaw", img3, "%dx%d px" % (r3.width,
                                                           r3.height)))
    img4, r4 = lane_render(None, "kaizen")
    cells.append(("rujukan · kaizen", img4, "%dx%d px" % (r4.width,
                                                           r4.height)))

    CW, CH = 400, 292
    for i, (label, img, bbox) in enumerate(cells):
        col, row = i % 3, i // 3
        x, y = 26 + col * (CW + 14), 58 + row * (CH + 14)
        pygame.draw.rect(s, PANEL, (x, y, CW, CH), border_radius=8)
        pygame.draw.rect(s, PANEL_EDGE, (x, y, CW, CH), 1, border_radius=8)
        max_h = CH - 46
        if img.get_height() > max_h or img.get_width() > CW - 20:
            k = min(max_h / img.get_height(), (CW - 20) / img.get_width())
            img = pygame.transform.scale(img, (int(img.get_width() * k),
                                                int(img.get_height() * k)))
        s.blit(img, (x + (CW - img.get_width()) // 2,
                     y + 12 + (max_h - img.get_height()) // 2))
        txt = label if bbox is None else f"{label}  {bbox}"
        s.blit(f_lbl.render(txt, True, (232, 216, 255)), (x + 12,
                                                          y + CH - 26))

    s.blit(f_lbl.render(
        "keluarga hero (bbox final, alpha>=100): grimjaw 74x79 · kaizen "
        "75x82 · vex 76x84 · gornak 83x84 - ukuran sama, yang berubah "
        "hanya keterbacaan", True, SUB), (30, H - 34))

    out = os.path.join(ROOT, "docs", "gornak_hero_pass.png")
    pygame.image.save(s, out)
    print(out)


if __name__ == "__main__":
    main()
