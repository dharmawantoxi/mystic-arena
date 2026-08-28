#!/usr/bin/env python3
"""Render review sheet untuk Drakar Procedural Masterwork.

Menghasilkan:
  - docs/drakar_masterwork_preview.png  (8 pose skill + barisan 1x arena)
  - docs/drakar_before_after.png        (rig lama dari git vs rig masterwork)
  - docs/drakar_portrait_preview.png    (LOD portrait Hero Shop)

Jalankan:  python3 tools/_shot_drakar_masterwork.py
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
from bosses import level1
from bosses.level1 import _NS_drakar as D

ACCENT = (246, 176, 146)
SUB = (170, 132, 122)
NOTE = (122, 104, 120)
PANEL = (13, 12, 24)
PANEL_EDGE = (128, 52, 52)
BG = (6, 7, 15)

CANVAS = 280
ANCHOR = (CANVAS // 2, CANVAS // 2 + 14)


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=0.0,
                        timer=0, attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=32)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def atk(prog):
    b = probe(pulse=1.15)
    b._drk_attack_active = True
    b._drk_attack_dir = 1
    b._drk_attack_frame = int(prog * 45)
    b._drk_previous_timer = 40
    b._drk_attack_progress = prog
    return b


def frame(boss, zoom=2.0, bg=(7, 8, 16)):
    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    surf.fill(bg + (255,))
    cx, cy = ANCHOR
    boss.x, boss.y = float(cx), float(cy)
    level1.draw_drakar(surf, boss, cx, cy)
    cw, ch = 170, 186
    rect = pygame.Rect(cx - cw // 2, cy - ch // 2 - 8, cw, ch)
    rect = rect.clip(surf.get_rect())
    out = surf.subsurface(rect).copy()
    return pygame.transform.scale(out, (int(rect.width * zoom),
                                        int(rect.height * zoom)))


font_title = pygame.font.Font(None, 46)
font_label = pygame.font.Font(None, 28)
font_small = pygame.font.Font(None, 20)

# ══════════════════════════════════════════════════════════════════
# Sheet 1 - pose utama + barisan ukuran arena sebenarnya
# ══════════════════════════════════════════════════════════════════
W, H = 1280, 1500
screen = pygame.Surface((W, H))
screen.fill(BG)
screen.blit(font_title.render("DRAKAR — PROCEDURAL MASTERWORK", True, ACCENT),
            (38, 18))
screen.blit(font_small.render(
    "100% code-drawn • tanpa PNG / sprite sheet • bone rig 2D berlapis + "
    "outline gelap 1 px • greataxe pose-driven (sudut kapak dari tabel pose)",
    True, SUB), (40, 66))

cases = [
    ("IDLE", probe(pulse=1.25)),
    ("WALK CYCLE", probe(pulse=2.35)),
    ("ATTACK — WIND-UP", atk(0.15)),
    ("ATTACK — CLEAVE", atk(0.45)),
    ("Q — BATTLE HUNGER", probe(pulse=1.2, active_skill="q",
                                active_skill_timer=60)),
    ("W — COUNTER HELIX", probe(pulse=1.2, active_skill="w",
                                active_skill_timer=25)),
    ("E — BERSERKER'S CALL", probe(pulse=1.2, active_skill="e",
                                    active_skill_timer=30)),
    ("R — CULLING BLADE", probe(pulse=1.2, active_skill="r",
                                active_skill_timer=30)),
]
tgt = SimpleNamespace(x=float(ANCHOR[0] + 84), y=float(ANCHOR[1] - 8),
                      alive=True)
for lab, b in cases[4:]:
    b.target = tgt

PX, PY, PW_, PH_ = 26, 100, 296, 466
notes = ("kapak istirahat di bahu;\nkaki menapak garis\nbayangan",
         "langkah dari sendi\nlutut & mata kaki;\nmane & pelt berayun",
         "wind-up: kapak diangkat\nke belakang-atas;\nlean menahan beban",
         "tebasan + pita cleave\nlhair dari MATA KAPAK\n(bukan busur melayang)",
         "orbit bara mengelilingi\ntorso; rig tetap subjek;\nmata membara",
         "piringan helix lahir\ndari sudut kapak;\ncincin tanah berputar",
         "roar: busur gelombang\ndari mulut; tanah\nretak radiasi",
         "charge -> sabit eksekusi\nlintasan mata kapak\n-> mekar di target")
for i, (label, boss) in enumerate(cases):
    r, c = divmod(i, 4)
    rect = pygame.Rect(PX + c * 310, PY + r * 480, PW_, PH_)
    pygame.draw.rect(screen, PANEL, rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_EDGE, rect, 1, border_radius=12)
    img = frame(boss)
    screen.blit(img, img.get_rect(center=(rect.centerx, rect.y + 210)))
    screen.blit(font_label.render(label, True, ACCENT), (rect.x + 14,
                                                          rect.y + 12))
    lines = notes[i].split("\n")
    for j, ln in enumerate(lines):
        screen.blit(font_small.render(ln, True, NOTE),
                    (rect.x + 14, rect.y + PH_ - 66 + j * 17))

# ── Barisan ukuran 1x (dengan garis tanah) - di bawah panel supaya
#    tidak pernah menumpuk catatan
row_y = 1180
screen.blit(font_label.render(
    "UKURAN ASLI 1x DI ARENA (urutan keluarga: gornak 119 < abaddon 122 < "
    "DRAKAR 138)", True, ACCENT), (38, row_y))
line_y = row_y + 120
pygame.draw.line(screen, (56, 60, 92), (38, line_y), (W - 38, line_y), 1)
labels = ["idle", "walk", "attack", "Q", "W", "E", "R", "hurt", "facing -1"]
states = [probe(pulse=1.25), probe(pulse=2.35), atk(0.45),
          probe(pulse=1.2, active_skill="q", active_skill_timer=60),
          probe(pulse=1.2, active_skill="w", active_skill_timer=25),
          probe(pulse=1.2, active_skill="e", active_skill_timer=30),
          probe(pulse=1.2, active_skill="r", active_skill_timer=30),
          probe(pulse=1.25, hurt_flash_timer=5),
          probe(pulse=1.25, direction=-1, facing=-1)]
states[6].target = SimpleNamespace(x=9999.0, y=9999.0, alive=False)
for i, (st, lab) in enumerate(zip(states, labels)):
    cx = 96 + i * 132
    st.x, st.y = float(cx), float(line_y - D.GROUND_DY)
    level1.draw_drakar(screen, st, cx, line_y - D.GROUND_DY)
    screen.blit(font_small.render(lab, True, SUB),
                (cx - font_small.size(lab)[0] // 2, line_y + 8))
screen.blit(font_small.render(
    "badan padat ~138 px (boss terbesar level 1) • bayangan per-telapak • "
    "outline gelap 1 px menjaga unit terpisah saat bertumpuk", True, NOTE),
    (38, line_y + 34))

pygame.image.save(screen, os.path.join(ROOT, "docs",
                                        "drakar_masterwork_preview.png"))
print("docs/drakar_masterwork_preview.png")

# ══════════════════════════════════════════════════════════════════
# Sheet 2 - sebelum / sesudah (rig lama dari git, zoom sama)
# ══════════════════════════════════════════════════════════════════
BASE_COMMIT = os.environ.get("DRAKAR_BEFORE_REF",
                             "c175e9c859792c900d6e722ac443df8713c095fb")


def load_old_namespace():
    try:
        src = subprocess.run(
            ["git", "-C", ROOT, "show", f"{BASE_COMMIT}:bosses/level1.py"],
            capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:
        print(f"[skip] renderer lama tidak tersedia ({exc})")
        return None
    # Ambil hanya blok namespace drakar + entry point-nya supaya eksekusi
    # modul sementara tidak mengulang seluruh file (yang kini berisi rig
    # baru dengan nama kelas yang sama).
    start = src.index("class _NS_drakar")
    end = src.index("class _NS_abaddon")
    block = src[start:end]
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write("import math\nimport pygame\n" + block)
        path = fh.name
    try:
        spec = importlib.util.spec_from_file_location("_drakar_before", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.unlink(path)


old_mod = load_old_namespace()

sheet = pygame.Surface((W, 790))
sheet.fill(BG)
sheet.blit(font_title.render("DRAKAR — SEBELUM / SESUDAH", True, ACCENT),
           (38, 18))
if old_mod is not None:
    old_cases = [("idle", dict(pulse=1.25)),
                 ("attack", dict(pulse=1.15, atk=True, prog=0.45)),
                 ("W helix", dict(pulse=1.2, active_skill="w",
                                  active_skill_timer=25)),
                 ("R culling", dict(pulse=1.2, active_skill="r",
                                    active_skill_timer=30))]
    for row, (NS, tag) in enumerate(((None, "SEBELUM — body-part statis"),
                                     (D, "SESUDAH — bone rig masterwork"))):
        y0 = 70 + row * 345
        sheet.blit(font_label.render(tag, True,
                                     (235, 130, 130) if row == 0 else ACCENT),
                   (40, y0))
        for i, (lab, st) in enumerate(old_cases):
            cx = 170 + i * 310          # posisi di SHEET
            lx, ly = 150, 180           # posisi di CANVAS pose
            atk_flag = st.pop("atk", False)
            prog = st.pop("prog", 0.0)
            b = probe(lx, ly, **st)
            if atk_flag:
                b._drk_attack_active = True
                b._drk_attack_progress = prog
                b._drk_previous_timer = 40
                b._drk_attack_dir = 1
                b._drk_attack_frame = int(prog * 45)
            surf = pygame.Surface((300, 340), pygame.SRCALPHA)
            surf.fill((7, 8, 16, 255))
            if row == 0:
                old_mod._NS_drakar.draw_drakar(surf, b, lx, ly)
            else:
                level1.draw_drakar(surf, b, lx, ly)
            crop_r = pygame.Rect(lx - 88, ly - 104, 176, 188)
            crop_r = crop_r.clip(surf.get_rect())
            out = surf.subsurface(crop_r).copy()
            zoom = 1.35
            out = pygame.transform.scale(out, (int(crop_r.width * zoom),
                                               int(crop_r.height * zoom)))
            sheet.blit(out, out.get_rect(center=(cx, y0 + 178)))
            sheet.blit(font_small.render(lab, True, SUB),
                       (cx - font_small.size(lab)[0] // 2, y0 + 288))
    sheet.blit(font_small.render(
        "kedua baris memakai faktor zoom yang sama - perbedaan ukuran & "
        "siluet adalah nyata, bukan efek crop", True, NOTE), (40, 758))
else:
    sheet.blit(font_small.render(
        "renderer lama tidak tersedia (butuh git object " + BASE_COMMIT + ")",
        True, NOTE), (40, 70))
pygame.image.save(sheet, os.path.join(ROOT, "docs", "drakar_before_after.png"))
print("docs/drakar_before_after.png")

# ══════════════════════════════════════════════════════════════════
# Sheet 3 - portrait LOD (Hero Shop)
# ══════════════════════════════════════════════════════════════════
sheet = pygame.Surface((W, 520))
sheet.fill(BG)
sheet.blit(font_title.render("DRAKAR — PORTRAIT LOD (HERO SHOP)", True,
                             ACCENT), (38, 18))
sheet.blit(font_small.render(
    "efek tanah/aura dibuang; konten dipusatkan ke bbox-nya sendiri; "
    "detail frekuensi tinggi (helai mane, serat, tato) hanya di LOD ini",
    True, SUB), (40, 66))
for i, pulse in enumerate((0.4, 1.25, 2.6)):
    b = probe(100, 120, pulse=pulse)
    b._portrait_hd = True
    canvas = pygame.Surface((200, 200), pygame.SRCALPHA)
    level1.draw_drakar(canvas, b, b.x, b.y)
    r = canvas.get_bounding_rect(min_alpha=1)
    crop = canvas.subsurface(r.clip(canvas.get_rect())).copy()
    scale = 300.0 / crop.get_height()
    card = pygame.transform.smoothscale(crop, (int(crop.get_width() * scale),
                                               int(crop.get_height() * scale)))
    cx = 260 + i * 380
    rect = card.get_rect(center=(cx, 300))
    pygame.draw.rect(sheet, PANEL, rect.inflate(28, 28), border_radius=12)
    pygame.draw.rect(sheet, PANEL_EDGE, rect.inflate(28, 28), 1,
                     border_radius=12)
    sheet.blit(card, rect)
    sheet.blit(font_small.render(f"pulse {pulse}", True, SUB),
               (cx - 40, rect.bottom + 18))
pygame.image.save(sheet, os.path.join(ROOT, "docs",
                                       "drakar_portrait_preview.png"))
print("docs/drakar_portrait_preview.png")
