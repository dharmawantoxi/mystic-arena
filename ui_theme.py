"""
ui_theme.py — design system Mystic Arena (menu & dialog)

Satu sumber kebenaran untuk tampilan menu: palet warna, teks
(gradasi/letter-spacing/ellipsis), permukaan cache (gradasi, glow,
bayangan), ikon vektor, dan komponen siap pakai (panel, tombol,
chip, toggle, slider, tab, header section, judul layar).

Aturan:
  * Semua fungsi gambar menerima `screen` (permukaan tujuan) dan,
    untuk komponen interaktif, `btns` (dict id -> Rect) supaya
    hit-test di Menu.handle_click tetap satu jalur.
  * Efek alpha yang mahal (glow, shadow lembut) dicek terhadap
    `mobile.perf.Quality.cheap_alpha` — di perangkat lambat efeknya
    digantikan bentuk solid murah.
  * Permukaan yang bisa di-cache disimpan di dict modul (kunci =
    ukuran + warna + radius). Cache dibatasi ratusan permukaan
    kecil; aman untuk RAM.
  * Modul ini TIDAK boleh mengimpor _core/_render di level modul
    (circular import). Font selalu diterima sebagai parameter.
"""

import pygame

# ═══════════════════════════════════════════════════════════
# PALET (dark-fantasy: midnight + gold + aksen team)
# ═══════════════════════════════════════════════════════════

# Dasar
BG_DEEP        = (9, 12, 26)
PANEL_TOP      = (30, 37, 66)
PANEL_BOTTOM   = (17, 21, 40)
PANEL_FILL     = (21, 26, 48)

# Emas (warna identitas)
GOLD           = (255, 205, 85)
GOLD_BRIGHT    = (255, 233, 158)
GOLD_DEEP      = (158, 116, 40)
GOLD_TEXT      = (255, 220, 110)
EDGE_GOLD      = (176, 144, 82)    # border panel/tombol default
EDGE_GOLD_DIM  = (104, 92, 66)

# Aksen
CYAN           = (110, 195, 255)
CYAN_SOFT      = (165, 220, 255)
VIOLET         = (176, 138, 255)
ORANGE         = (255, 168, 96)
GREEN          = (112, 226, 132)
GREEN_DEEP     = (34, 116, 58)
RED            = (255, 108, 108)
RED_DEEP       = (132, 44, 44)
SLATE          = (148, 158, 188)

# Teks
TEXT_WHITE     = (240, 244, 255)
TEXT_BODY      = (198, 207, 230)
TEXT_DIM       = (132, 142, 170)
TEXT_FAINT     = (96, 106, 136)

# Status (kartu/level)
LOCKED_BG_TOP    = (30, 28, 40)
LOCKED_BG_BOTTOM = (20, 19, 29)
LOCKED_EDGE      = (84, 86, 110)
DONE_BG_TOP      = (26, 44, 36)
DONE_BG_BOTTOM   = (17, 30, 24)
DONE_EDGE        = (86, 178, 112)
OPEN_BG_TOP      = (28, 38, 64)
OPEN_BG_BOTTOM   = (18, 24, 44)
OPEN_EDGE        = (96, 152, 214)


def cheap_alpha():
    """True kalau perangkat sanggup alpha-blit (PC cepat)."""
    try:
        from mobile.perf import Quality
        return Quality.cheap_alpha
    except Exception:
        return True


# ═══════════════════════════════════════════════════════════
# CACHE PERMUKAAN
# ═══════════════════════════════════════════════════════════

_GRAD_CACHE = {}
_GLOW_CACHE = {}
_SHADOW_CACHE = {}


def clear_caches():
    _GRAD_CACHE.clear()
    _GLOW_CACHE.clear()
    _SHADOW_CACHE.clear()


def _vgrad(w, h, top, bottom, radius=0):
    """Permukaan gradasi vertikal (cached)."""
    w = max(2, int(w))
    h = max(2, int(h))
    key = (w, h, top, bottom, radius)
    surf = _GRAD_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pygame.draw.line(surf, (r, g, b, 255), (0, y), (w, y))
        if radius:
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255),
                             (0, 0, w, h), border_radius=radius)
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _GRAD_CACHE[key] = surf
    return surf


def _shadow(w, h, radius=12, alpha=110, spread=4):
    """Bayangan lembut (cached). Dibuat dari surface kecil lalu
    smoothscale supaya halus tanpa per-piksel loop besar."""
    w = max(2, int(w) + spread * 2)
    h = max(2, int(h) + spread * 2)
    key = (w, h, radius, alpha)
    surf = _SHADOW_CACHE.get(key)
    if surf is None:
        sw, sh = max(4, w // 8), max(4, h // 8)
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(small, (0, 0, 0, alpha), (0, 0, sw, sh),
                         border_radius=max(1, radius // 8))
        surf = pygame.transform.smoothscale(small, (w, h))
        _SHADOW_CACHE[key] = surf
    return surf


def _radial(w, h, color, alpha):
    """Glow radial elips (cached)."""
    w = max(8, int(w))
    h = max(8, int(h))
    # Kunci alpha dibulatkan kelipatan 8 agar cache tidak meledak.
    a = max(4, min(120, int(alpha) // 8 * 8))
    key = (w, h, color, a)
    surf = _GLOW_CACHE.get(key)
    if surf is None:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w / 2, h / 2
        maxd = math_hyp(cx, cy)
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                d = math_hyp(x - cx, y - cy) / maxd
                if d < 1:
                    aa = int(a * (1 - d) ** 2)
                    if aa > 0:
                        pygame.draw.rect(surf, (*color, aa),
                                         (x, y, 2, 2))
        _GLOW_CACHE[key] = surf
    return surf


def math_hyp(x, y):
    return (x * x + y * y) ** 0.5


# ═══════════════════════════════════════════════════════════
# TEKS
# ═══════════════════════════════════════════════════════════

_GRAD_TEXT_CACHE = {}


def letter(text, gap=" "):
    """Letter-spacing manual (pygame tidak punya tracking)."""
    return gap.join(list(text))


def fit_ellipsis(font, text, max_w):
    """Truncate dengan elipsis yang benar (tanpa titik menggantung)."""
    text = str(text)
    if font.size(text)[0] <= max_w:
        return text
    ell = "…" if _has_glyph(font, "…") else "..."
    while len(text) > 1:
        cand = text[:-1]
        if font.size(cand + ell)[0] <= max_w:
            return cand + ell
        text = cand
    return ell


def _has_glyph(font, ch):
    try:
        a = font.render(ch, True, (255, 255, 255))
        b = font.render("￀", True, (255, 255, 255))  # pasti tidak ada
        return pygame.image.tobytes(a, "RGBA") != \
            pygame.image.tobytes(b, "RGBA")
    except Exception:
        return False


def draw_text(screen, font, text, color, center=None, topleft=None,
              shadow=True, offset=(2, 2)):
    """Teks dengan bayangan gelap tipis (murah: 2 blit)."""
    surf = font.render(text, True, color)
    if shadow:
        sh = font.render(text, True, (5, 6, 12))
        if center is not None:
            rect = surf.get_rect(center=center)
            screen.blit(sh, (rect.x + offset[0], rect.y + offset[1]))
        else:
            screen.blit(sh, (topleft[0] + offset[0],
                             topleft[1] + offset[1]))
    if center is not None:
        screen.blit(surf, surf.get_rect(center=center))
    else:
        screen.blit(surf, topleft)
    return surf


def gradient_text(font, text, top, bottom):
    """Teks gradasi vertikal (cached per font+teks+warna)."""
    key = (font, text, top, bottom)
    surf = _GRAD_TEXT_CACHE.get(key)
    if surf is None:
        base = font.render(text, True, (255, 255, 255))
        h = max(1, base.get_height())
        grad = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            pygame.draw.line(grad, (r, g, b, 255), (0, y),
                             (base.get_width(), y))
        grad.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf = grad
        if len(_GRAD_TEXT_CACHE) > 400:
            _GRAD_TEXT_CACHE.clear()
        _GRAD_TEXT_CACHE[key] = surf
    return surf


def outline_text(screen, font, text, color, center, outline=(8, 9, 18),
                 width=2, body_top=None, body_bottom=None):
    """Teks tebal dengan outline gelap 8 arah (cache tidak perlu:
    hanya 9 blit dari 1 render). body_top/body_bottom override gradasi
    emas default (mis. merah untuk layar DEFEAT)."""
    out = font.render(text, True, outline)
    rect = out.get_rect(center=center)
    if cheap_alpha():
        for dx, dy in ((-width, 0), (width, 0), (0, -width), (0, width),
                       (-width, -width), (width, width),
                       (-width, width), (width, -width)):
            screen.blit(out, (rect.x + dx, rect.y + dy))
    else:
        for dx, dy in ((-width, 0), (width, 0), (0, -width), (0, width)):
            screen.blit(out, (rect.x + dx, rect.y + dy))
    if body_top is None or body_bottom is None:
        body = gradient_text(font, text, GOLD_BRIGHT, (196, 138, 40))
    else:
        body = gradient_text(font, text, body_top, body_bottom)
    screen.blit(body, rect)
    return rect


# ═══════════════════════════════════════════════════════════
# IKON VEKTOR (menggantikan emoji yang tidak ada di font Barlow)
# ═══════════════════════════════════════════════════════════

def draw_icon(surf, name, cx, cy, color, s=1.0):
    """Ikon vektor skala s (s=1 -> ~16 px). cx/cy = pusat."""
    if name == "play":
        pygame.draw.polygon(surf, color,
                            [(cx - 6 * s, cy - 10 * s),
                             (cx - 6 * s, cy + 10 * s),
                             (cx + 11 * s, cy)])
    elif name == "continue":
        pygame.draw.polygon(surf, color,
                            [(cx - 11 * s, cy - 9 * s),
                             (cx - 11 * s, cy + 9 * s),
                             (cx - 1 * s, cy)])
        pygame.draw.polygon(surf, color,
                            [(cx, cy - 9 * s),
                             (cx, cy + 9 * s),
                             (cx + 11 * s, cy)])
    elif name == "coin":
        pygame.draw.circle(surf, (255, 205, 66), (cx, cy), 9 * s)
        pygame.draw.circle(surf, (190, 140, 32), (cx, cy), 9 * s, 2)
        pygame.draw.circle(surf, (230, 175, 50), (cx, cy), 5 * s)
        pygame.draw.line(surf, (190, 140, 32),
                         (cx, cy - 3.5 * s), (cx, cy + 3.5 * s), 2)
    elif name == "pad":
        pygame.draw.rect(surf, color,
                         (cx - 12 * s, cy - 7 * s, 24 * s, 15 * s),
                         border_radius=int(7 * s))
        pygame.draw.circle(surf, (10, 12, 22), (cx - 6 * s, cy), 2 * s)
        pygame.draw.circle(surf, (10, 12, 22),
                           (cx + 5 * s, cy + 2 * s), 2 * s)
    elif name == "help":
        # Tanda tanya digambar manual (hook atas + ekor + titik)
        r = 5.5 * s
        pygame.draw.arc(surf, color,
                        (cx - r, cy - 9 * s, 2 * r, 2 * r),
                        3.4, 6.9, 2)
        pygame.draw.line(surf, color,
                         (cx + 4.5 * s, cy - 0.3 * s),
                         (cx, cy + 2.5 * s), 2)
        pygame.draw.circle(surf, color, (cx, cy + 6.5 * s), 1.6 * s)
    elif name == "gear":
        pygame.draw.circle(surf, color, (cx, cy), 7 * s, 2)
        for i in range(6):
            import math as _m
            a = i * _m.pi / 3
            x1 = cx + _m.cos(a) * 7 * s
            y1 = cy + _m.sin(a) * 7 * s
            x2 = cx + _m.cos(a) * 11 * s
            y2 = cy + _m.sin(a) * 11 * s
            pygame.draw.line(surf, color, (x1, y1), (x2, y2), 2)
    elif name == "star":
        for (dx, dy) in ((1, 0), (0, 1), (1, 1), (1, -1)):
            pygame.draw.line(surf, color,
                             (cx - dx * 8 * s, cy - dy * 8 * s),
                             (cx + dx * 8 * s, cy + dy * 8 * s), 2)
        pygame.draw.circle(surf, color, (cx, cy), 3 * s)
    elif name == "quit":
        pygame.draw.line(surf, color,
                         (cx - 7 * s, cy - 7 * s), (cx + 7 * s, cy + 7 * s),
                         3)
        pygame.draw.line(surf, color,
                         (cx + 7 * s, cy - 7 * s), (cx - 7 * s, cy + 7 * s),
                         3)
    elif name == "lock":
        bw, bh = 14 * s, 11 * s
        bx, by = cx - bw / 2, cy - bh / 2 + 2 * s
        pygame.draw.rect(surf, color,
                         (bx, by, bw, bh), border_radius=int(3 * s))
        pygame.draw.arc(surf, color,
                        (bx + bw * 0.2, by - 8 * s, bw * 0.6, 12 * s),
                        3.14, 6.28, 2)
        pygame.draw.circle(surf, (10, 12, 22), (cx, by + bh * 0.45),
                           2 * s)
    elif name == "speaker":
        pygame.draw.rect(surf, color,
                         (cx - 9 * s, cy - 3 * s, 5 * s, 6 * s))
        pygame.draw.polygon(surf, color,
                            [(cx - 4 * s, cy - 3 * s),
                             (cx + 1 * s, cy - 8 * s),
                             (cx + 1 * s, cy + 8 * s),
                             (cx - 4 * s, cy + 3 * s)])
        pygame.draw.arc(surf, color,
                        (cx + 1 * s, cy - 7 * s, 12 * s, 14 * s),
                        -1.0, 1.0, 2)
        pygame.draw.arc(surf, color,
                        (cx + 2 * s, cy - 10 * s, 16 * s, 20 * s),
                        -0.9, 0.9, 2)
    elif name == "swords":
        pygame.draw.line(surf, color,
                         (cx - 8 * s, cy - 8 * s), (cx + 8 * s, cy + 8 * s),
                         3)
        pygame.draw.line(surf, color,
                         (cx + 8 * s, cy - 8 * s), (cx - 8 * s, cy + 8 * s),
                         3)
        pygame.draw.line(surf, (10, 12, 22),
                         (cx - 9 * s, cy + 5 * s),
                         (cx - 5 * s, cy + 9 * s), 3)
        pygame.draw.line(surf, (10, 12, 22),
                         (cx + 9 * s, cy + 5 * s),
                         (cx + 5 * s, cy + 9 * s), 3)
        pygame.draw.circle(surf, color, (cx, cy), 2.5 * s)
    elif name == "monitor":
        pygame.draw.rect(surf, color,
                         (cx - 9 * s, cy - 7 * s, 18 * s, 12 * s), 2)
        pygame.draw.line(surf, color, (cx, cy + 5 * s),
                         (cx, cy + 9 * s), 2)
        pygame.draw.line(surf, color, (cx - 5 * s, cy + 9 * s),
                         (cx + 5 * s, cy + 9 * s), 2)
    elif name == "cloud":
        pygame.draw.circle(surf, color, (cx - 5 * s, cy + 2 * s), 5 * s)
        pygame.draw.circle(surf, color, (cx, cy - 3 * s), 6 * s)
        pygame.draw.circle(surf, color, (cx + 6 * s, cy + 2 * s), 5 * s)
        pygame.draw.rect(surf, color,
                         (cx - 5 * s, cy + 2 * s, 11 * s, 4 * s))
    elif name == "warn":
        pygame.draw.polygon(surf, color,
                            [(cx, cy - 9 * s),
                             (cx + 10 * s, cy + 8 * s),
                             (cx - 10 * s, cy + 8 * s)])
        pygame.draw.line(surf, (10, 12, 22), (cx, cy - 4 * s),
                         (cx, cy + 2 * s), 2)
        pygame.draw.circle(surf, (10, 12, 22), (cx, cy + 5 * s), 1.5 * s)
    elif name == "heart":
        r = 4.2 * s
        pygame.draw.circle(surf, color, (cx - r, cy - r * 0.4), r)
        pygame.draw.circle(surf, color, (cx + r, cy - r * 0.4), r)
        pygame.draw.polygon(surf, color,
                            [(cx - r * 1.85, cy),
                             (cx + r * 1.85, cy),
                             (cx, cy + r * 2.1)])
    elif name == "check":
        pygame.draw.line(surf, color,
                         (cx - 7 * s, cy), (cx - 2 * s, cy + 5 * s), 3)
        pygame.draw.line(surf, color,
                         (cx - 2 * s, cy + 5 * s), (cx + 7 * s, cy - 5 * s),
                         3)
    elif name == "back":
        pygame.draw.line(surf, color,
                         (cx + 4 * s, cy - 7 * s), (cx - 5 * s, cy), 3)
        pygame.draw.line(surf, color,
                         (cx - 5 * s, cy), (cx + 4 * s, cy + 7 * s), 3)
    elif name in ("chevron_l", "chevron_r"):
        d = -1 if name == "chevron_l" else 1
        pygame.draw.line(surf, color,
                         (cx + 4 * s * d, cy - 6 * s),
                         (cx - 4 * s * d, cy), 3)
        pygame.draw.line(surf, color,
                         (cx - 4 * s * d, cy),
                         (cx + 4 * s * d, cy + 6 * s), 3)
    elif name == "plus":
        pygame.draw.line(surf, color, (cx - 6 * s, cy),
                         (cx + 6 * s, cy), 3)
        pygame.draw.line(surf, color, (cx, cy - 6 * s),
                         (cx, cy + 6 * s), 3)
    elif name == "minus":
        pygame.draw.line(surf, color, (cx - 6 * s, cy),
                         (cx + 6 * s, cy), 3)
    elif name == "skull":
        pygame.draw.circle(surf, color, (cx, cy - 2.5 * s), 6.5 * s)
        pygame.draw.rect(surf, color,
                         (cx - 3.5 * s, cy + 2.5 * s, 7 * s, 5 * s),
                         border_radius=2)
        pygame.draw.circle(surf, (10, 12, 22), (cx - 2.6 * s, cy - 3.5 * s),
                           2 * s)
        pygame.draw.circle(surf, (10, 12, 22), (cx + 2.6 * s, cy - 3.5 * s),
                           2 * s)
    elif name == "bolt":
        pygame.draw.polygon(surf, color,
                            [(cx + 2 * s, cy - 10 * s),
                             (cx - 6 * s, cy + 1 * s),
                             (cx - 1 * s, cy + 1 * s),
                             (cx - 3 * s, cy + 10 * s),
                             (cx + 6 * s, cy - 1 * s),
                             (cx + 1 * s, cy - 1 * s)])
    elif name == "crown":
        pygame.draw.polygon(surf, color,
                            [(cx - 9 * s, cy + 6 * s),
                             (cx - 9 * s, cy - 4 * s),
                             (cx - 4 * s, cy + 1 * s),
                             (cx, cy - 7 * s),
                             (cx + 4 * s, cy + 1 * s),
                             (cx + 9 * s, cy - 4 * s),
                             (cx + 9 * s, cy + 6 * s)])
    elif name == "gem":
        pygame.draw.polygon(surf, color,
                            [(cx, cy - 8 * s), (cx + 7 * s, cy - 2 * s),
                             (cx, cy + 8 * s), (cx - 7 * s, cy - 2 * s)])
        pygame.draw.line(surf, (255, 255, 255),
                         (cx - 7 * s, cy - 2 * s),
                         (cx + 7 * s, cy - 2 * s), 1)
    elif name == "trophy":
        # Piala: mangkuk + kaki + pegangan
        pygame.draw.polygon(surf, color,
                            [(cx - 7 * s, cy - 8 * s),
                             (cx + 7 * s, cy - 8 * s),
                             (cx + 5 * s, cy),
                             (cx, cy + 4 * s),
                             (cx - 5 * s, cy)])
        pygame.draw.line(surf, color, (cx, cy + 4 * s),
                         (cx, cy + 7 * s), 2)
        pygame.draw.line(surf, color, (cx - 5 * s, cy + 9 * s),
                         (cx + 5 * s, cy + 9 * s), 2)
        pygame.draw.arc(surf, color,
                        (cx - 10 * s, cy - 8 * s, 5 * s, 7 * s),
                        1.4, 4.6, 2)
        pygame.draw.arc(surf, color,
                        (cx + 5 * s, cy - 8 * s, 5 * s, 7 * s),
                        -1.4, 1.6, 2)
    elif name == "shield":
        pygame.draw.polygon(surf, color,
                            [(cx, cy - 9 * s), (cx + 8 * s, cy - 5 * s),
                             (cx + 8 * s, cy + 3 * s),
                             (cx, cy + 9 * s),
                             (cx - 8 * s, cy + 3 * s),
                             (cx - 8 * s, cy - 5 * s)])
    elif name == "upload":
        pygame.draw.line(surf, color, (cx, cy + 8 * s),
                         (cx, cy - 6 * s), 2)
        pygame.draw.polygon(surf, color,
                            [(cx - 5 * s, cy - 2 * s),
                             (cx + 5 * s, cy - 2 * s),
                             (cx, cy - 8 * s)])
        pygame.draw.line(surf, color,
                         (cx - 7 * s, cy + 8 * s),
                         (cx + 7 * s, cy + 8 * s), 2)
    elif name == "download":
        pygame.draw.line(surf, color, (cx, cy - 8 * s),
                         (cx, cy + 6 * s), 2)
        pygame.draw.polygon(surf, color,
                            [(cx - 5 * s, cy + 2 * s),
                             (cx + 5 * s, cy + 2 * s),
                             (cx, cy + 8 * s)])
        pygame.draw.line(surf, color,
                         (cx - 7 * s, cy + 8 * s),
                         (cx + 7 * s, cy + 8 * s), 2)


# ═══════════════════════════════════════════════════════════
# KOMPONEN
# ═══════════════════════════════════════════════════════════

def corner_ticks(screen, rect, color, length=11, width=2, inset=2):
    """Tanda sudut emas — identitas visual Mystic Arena."""
    pts = [
        (rect.x + inset, rect.y + inset, 1, 1),
        (rect.right - inset, rect.y + inset, -1, 1),
        (rect.x + inset, rect.bottom - inset, 1, -1),
        (rect.right - inset, rect.bottom - inset, -1, -1),
    ]
    for (ax, ay, dx, dy) in pts:
        pygame.draw.line(screen, color,
                         (ax, ay), (ax + dx * length, ay), width)
        pygame.draw.line(screen, color,
                         (ax, ay), (ax, ay + dy * length), width)


def panel(screen, rect, border=EDGE_GOLD, fill_top=PANEL_TOP,
          fill_bottom=PANEL_BOTTOM, ticks=True, shadow=True,
          border_w=1):
    """Panel kaca gelap: gradasi + border + sudut emas + bayangan."""
    r = pygame.Rect(rect)
    if shadow and cheap_alpha():
        sh = _shadow(r.w, r.h, radius=12)
        screen.blit(sh, (r.x - 4, r.y - 4))
    elif shadow:
        pygame.draw.rect(screen, (6, 7, 14), r.move(3, 4),
                         border_radius=12)
    if cheap_alpha():
        screen.blit(_vgrad(r.w, r.h, fill_top, fill_bottom, radius=12),
                    (r.x, r.y))
    else:
        pygame.draw.rect(screen, PANEL_FILL, r, border_radius=12)
    pygame.draw.rect(screen, border, r, border_w, border_radius=12)
    if ticks:
        corner_ticks(screen, r, GOLD)


def panel_solid(screen, rect, border=EDGE_GOLD):
    """Panel untuk konteks murah (tanpa alpha sama sekali)."""
    r = pygame.Rect(rect)
    pygame.draw.rect(screen, PANEL_FILL, r, border_radius=12)
    pygame.draw.rect(screen, border, r, 1, border_radius=12)
    corner_ticks(screen, r, GOLD)


def button(screen, btns, bid, label, cx, cy, accent, font,
           w=300, h=50, icon=None, hover=False, font_size=None,
           letter_gap=True):
    """Tombol menu utama (premium): gradasi, aksen kiri, ikon
    badge, sudut emas, glow hover.

    `font_size` meng-override `font` bila diisi.
    Rect interaktif DITAMBAH 9px x 4px saat hover (perilaku lama
    dipertahankan supaya hit-test tidak berubah).
    """
    base = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    rect = base.inflate(18, 8) if hover else base

    # Glow hover
    if hover:
        if cheap_alpha():
            glow = _radial(rect.w + 44, rect.h + 36, accent, 74)
            screen.blit(glow, (rect.x - 22, rect.y - 18))
        else:
            pygame.draw.rect(screen, accent,
                             rect.inflate(10, 10), 2, border_radius=14)

    # Bayangan
    if cheap_alpha():
        screen.blit(_shadow(rect.w, rect.h, radius=12, alpha=110,
                            spread=4),
                    (rect.x - 2, rect.y - 2))

    # Panel tombol
    top = (44, 52, 86) if hover else (34, 41, 70)
    bot = (24, 29, 52) if hover else (17, 21, 38)
    if cheap_alpha():
        screen.blit(_vgrad(rect.w, rect.h, top, bot, radius=12),
                    (rect.x, rect.y))
    else:
        pygame.draw.rect(screen, top, rect, border_radius=12)
    # Sorot tepi atas
    pygame.draw.line(screen, (255, 255, 255),
                     (rect.x + 12, rect.y + 1),
                     (rect.right - 12, rect.y + 1), 1)

    # Aksen kiri (warna identitas)
    pygame.draw.rect(screen, accent,
                     (rect.x + 6, rect.y + 10, 4, rect.h - 20),
                     border_radius=2)
    if cheap_alpha():
        pygame.draw.rect(screen, (*accent, 70),
                         (rect.x + 4, rect.y + 8, 8, rect.h - 16),
                         border_radius=3)

    # Border
    bcol = accent if hover else EDGE_GOLD
    pygame.draw.rect(screen, bcol, rect,
                     2 if hover else 1, border_radius=12)

    # Sudut emas
    corner_ticks(screen, rect, GOLD)

    # Ikon badge
    if icon is not None:
        ic_x = rect.x + 34
        ic_y = rect.centery
        pygame.draw.circle(screen, (12, 14, 26), (ic_x, ic_y), 17)
        pygame.draw.circle(screen, accent, (ic_x, ic_y), 17, 2)
        draw_icon(screen, icon, ic_x, ic_y, accent, s=0.9)

    # Label
    if font_size:
        from _core import get_font as _gf
        font = _gf(font_size, "body_bold")
    text = letter(label) if letter_gap else label
    if icon is not None:
        # Clamp posisi label: jangan menimpa badge ikon dan jangan
        # keluar tepi kanan tombol (dulu label di-center +14px saja
        # sehingga tombol sempit membuat ikon bertabrakan dgn teks).
        tw = font.size(text)[0]
        left_min = rect.x + 56
        right_max = rect.right - 10
        text_cx = base.x + w // 2 + 14
        if text_cx - tw / 2 < left_min:
            text_cx = left_min + tw / 2
        if text_cx + tw / 2 > right_max:
            text_cx = right_max - tw / 2
        if text_cx - tw / 2 < left_min:
            text_cx = (left_min + right_max) / 2
    else:
        text_cx = rect.centerx
    draw_text(screen, font, text, TEXT_WHITE,
              center=(text_cx, rect.centery))

    btns[bid] = rect
    return rect


def pill(screen, btns, bid, label, rect, kind, font, hover=False,
         enabled=True, icon=None, letter_gap=True):
    """Tombol aksi kecil (PLAY / UNLOCK / BACK / dsb).

    kind: 'gold' | 'success' | 'danger' | 'locked' | 'owned'
          | 'neutral'
    """
    r = pygame.Rect(rect)
    colors = {
        "gold":    ((86, 66, 22), (52, 40, 14), GOLD, GOLD_TEXT),
        "success": ((38, 122, 60), (22, 74, 36), GREEN, (214, 255, 222)),
        "danger":  ((122, 42, 42), (74, 26, 26), RED, (255, 214, 214)),
        "locked":  ((48, 50, 66), (30, 32, 44), SLATE, TEXT_DIM),
        "owned":   ((34, 96, 48), (20, 56, 30), GREEN, (190, 250, 200)),
        "neutral": ((52, 58, 84), (30, 35, 56), SLATE, TEXT_BODY),
        "violet":  ((74, 48, 118), (44, 28, 78), (196, 150, 255),
                    (226, 205, 255)),
        "cyan":    ((36, 84, 110), (22, 52, 72), (140, 214, 255),
                    (205, 240, 255)),
    }
    top, bot, edge, tcol = colors.get(kind, colors["neutral"])
    if hover and enabled:
        top = tuple(min(255, c + 18) for c in top)
        bot = tuple(min(255, c + 14) for c in bot)

    if cheap_alpha():
        screen.blit(_vgrad(r.w, r.h, top, bot, radius=7), (r.x, r.y))
    else:
        pygame.draw.rect(screen, top, r, border_radius=7)
    pygame.draw.rect(screen, edge, r, 2 if enabled else 1, border_radius=7)
    if hover and enabled and cheap_alpha():
        screen.blit(_radial(r.w + 30, r.h + 24, edge, 66),
                    (r.x - 15, r.y - 12))

    cx = r.centerx
    if icon:
        draw_icon(screen, icon, r.x + 22, r.centery, edge, s=0.8)
        cx = r.x + 22 + (r.w - 22) // 2
    draw_text(screen, font,
              letter(label) if letter_gap else label,
              tcol if enabled else TEXT_FAINT, center=(cx, r.centery))
    if enabled:
        btns[bid] = r
    return r


def chip(screen, pos, text, accent, font, icon=None, icon_color=None,
         value=None, value_color=None, align="left"):
    """Chip status auto-size (icon + label + nilai opsional).

    pos: topleft (align='left') atau topright (align='right').
    Mengembalikan Rect chip yang digambar.
    """
    spaced = letter(text)
    total_w = 26
    if icon:
        total_w += 22
    total_w += font.size(spaced)[0]
    if value is not None:
        total_w += 10 + font.size(value)[0]
    h = 30
    if align == "right":
        x = pos[0] - total_w
    else:
        x = pos[0]
    r = pygame.Rect(x, pos[1], total_w, h)

    if cheap_alpha():
        screen.blit(_vgrad(r.w, h, (32, 38, 64), (18, 22, 40),
                           radius=h // 2), (r.x, r.y))
    else:
        pygame.draw.rect(screen, (22, 26, 46), r, border_radius=h // 2)
    pygame.draw.rect(screen, accent, r, 1, border_radius=h // 2)

    ix = r.x + 14
    iy = r.centery
    if icon:
        draw_icon(screen, icon, ix, iy, icon_color or accent, s=0.75)
        ix += 22
    draw_text(screen, font, spaced, TEXT_BODY,
              topleft=(ix, r.y + 7), shadow=False)
    ix += font.size(spaced)[0]
    if value is not None:
        ix += 10
        draw_text(screen, font, value, value_color or accent,
                  topleft=(ix, r.y + 7), shadow=False)
    return r


def section_header(screen, x, y, title, icon_name, color,
                   font, rule_w=240):
    """Header section: ikon + judul letter-spaced + garis hairline."""
    draw_icon(screen, icon_name, x + 10, y + 11, color, s=0.9)
    draw_text(screen, font, letter(title), color,
              topleft=(x + 28, y), shadow=False)
    tw = font.size(title)[0] + 28
    pygame.draw.line(screen, color, (x + tw + 14, y + 14),
                     (x + tw + 14 + rule_w, y + 14), 1)
    pygame.draw.line(screen, (*_dim(color),), (x + 28, y + 26),
                     (x + tw + 14, y + 26), 1)
    return y + 34


def _dim(color, f=0.55):
    return tuple(int(c * f) for c in color)


def toggle(screen, btns, bid, rect, is_on, font, hover=False):
    """Toggle pill ON/OFF."""
    r = pygame.Rect(rect)
    if is_on:
        top = (70, 190, 96) if not hover else (92, 214, 118)
        bot = (34, 116, 58) if not hover else (46, 138, 70)
        edge = (120, 235, 145) if not hover else (160, 255, 180)
    else:
        top = (74, 78, 100) if not hover else (92, 96, 118)
        bot = (44, 48, 68) if not hover else (56, 60, 80)
        edge = (120, 126, 150) if not hover else (150, 156, 180)
    if cheap_alpha():
        screen.blit(_vgrad(r.w, r.h, top, bot, radius=r.h // 2),
                    (r.x, r.y))
    else:
        pygame.draw.rect(screen, top, r, border_radius=r.h // 2)
    pygame.draw.rect(screen, edge, r, 2, border_radius=r.h // 2)

    knob = 18
    kx = r.right - knob - 6 if is_on else r.x + 6
    ky = r.centery
    pygame.draw.circle(screen, (12, 14, 24), (kx + 1, ky + 2), knob // 2)
    pygame.draw.circle(screen, (245, 248, 255), (kx, ky), knob // 2)
    pygame.draw.circle(screen, edge, (kx, ky), knob // 2, 1)

    lab = "ON" if is_on else "OFF"
    lx = r.x + r.w // 2 + (0 if is_on else 0)
    # Label di sisi berlawanan knob
    if is_on:
        lx = r.x + r.w // 2 - 8
    else:
        lx = r.x + r.w // 2 + 8
    draw_text(screen, font, lab,
              (210, 255, 220) if is_on else TEXT_BODY,
              center=(lx, ky), shadow=False)
    btns[bid] = r
    return r


def slider(screen, x, y, w, value, knob_hover=False):
    """Slider volume: track + isi emas + knob. Mengembalikan
    posisi knob (x) supaya pemanggil bisa meletakkan tombol +/-.
    """
    track_h = 8
    bar = pygame.Rect(x, y, w, track_h)
    pygame.draw.rect(screen, (34, 38, 58), bar, border_radius=4)
    fill_w = int(w * max(0.0, min(1.0, value)))
    if fill_w > 4:
        if cheap_alpha():
            screen.blit(_vgrad(fill_w, track_h, GOLD_BRIGHT,
                               (196, 138, 40), radius=4),
                        (x, y))
        else:
            pygame.draw.rect(screen, GOLD, (x, y, fill_w, track_h),
                             border_radius=4)
    pygame.draw.rect(screen, (120, 110, 86), bar, 1, border_radius=4)

    kx = x + fill_w
    ky = y + track_h // 2
    if knob_hover and cheap_alpha():
        screen.blit(_radial(36, 36, GOLD, 80), (kx - 18, ky - 18))
    pygame.draw.circle(screen, (12, 14, 24), (kx, ky), 11)
    pygame.draw.circle(screen, (245, 248, 255), (kx, ky), 8)
    pygame.draw.circle(screen, GOLD, (kx, ky), 8, 2)
    return kx


def option_cycler(screen, btns, id_base, label, value, x, y, width,
                  label_font, value_font, hover=None):
    """Setting opsi: label + kotak nilai (lebar menyesuaikan teks)
    + tombol chevron < >. Mengembalikan y berikutnya (y + 30)."""
    draw_text(screen, label_font, label, TEXT_BODY,
              topleft=(x, y + 10), shadow=False)

    # Lebar kotak mengikuti teks (perbaikan: label bahasa panjang
    # dulu terpotong karena lebar kotak tetap 140 px).
    vw = max(110, value_font.size(value)[0] + 26)
    vw = min(vw, width - 66)
    vh = 30
    vx = x + width - vw - 56
    vy = y + 7
    box = pygame.Rect(vx, vy, vw, vh)

    box_hover = hover in (id_base + "_prev", id_base + "_next")
    if cheap_alpha():
        screen.blit(_vgrad(box.w, box.h, (40, 48, 80), (20, 24, 44),
                           radius=6), (box.x, box.y))
    else:
        pygame.draw.rect(screen, (28, 34, 58), box, border_radius=6)
    pygame.draw.rect(screen, EDGE_GOLD if box_hover else (96, 106, 138),
                     box, 1, border_radius=6)
    draw_text(screen, value_font, value, GOLD_TEXT,
              center=box.center, shadow=False)

    for side, bid, icon in (("l", id_base + "_prev", "chevron_l"),
                            ("r", id_base + "_next", "chevron_r")):
        bw = 24
        bx = box.x - bw - 6 if side == "l" else box.right + 6
        b = pygame.Rect(bx, vy, bw, vh)
        bh = hover == bid
        top = (64, 74, 110) if bh else (42, 48, 74)
        if cheap_alpha():
            screen.blit(_vgrad(bw, vh, top, (26, 30, 52), radius=6),
                        (b.x, b.y))
        else:
            pygame.draw.rect(screen, top, b, border_radius=6)
        pygame.draw.rect(screen, (150, 160, 196) if bh else (96, 106, 138),
                         b, 1, border_radius=6)
        draw_icon(screen, icon, b.centerx, b.centery,
                  (200, 210, 240), s=0.6)
        btns[bid] = b
    return vy + vh


def tab_width(font, label, min_w=150):
    """Lebar tab auto (mengikuti teks letter-spaced)."""
    return max(min_w, font.size(letter(label))[0] + 36)


def tab(screen, btns, bid, rect, label, accent, font, active,
        hover=False):
    """Tab kategori (hero shop)."""
    r = pygame.Rect(rect)
    if active:
        top = (46, 56, 92)
        bot = (26, 32, 58)
        if cheap_alpha():
            screen.blit(_vgrad(r.w, r.h, top, bot, radius=8),
                        (r.x, r.y))
        else:
            pygame.draw.rect(screen, top, r, border_radius=8)
        pygame.draw.rect(screen, accent, r, 2, border_radius=8)
        pygame.draw.rect(screen, accent,
                         (r.x + 8, r.bottom - 4, r.w - 16, 3),
                         border_radius=1)
        tcol = accent
    else:
        top = (34, 39, 62) if hover else (22, 26, 44)
        bot = (20, 24, 42) if hover else (15, 18, 32)
        if cheap_alpha():
            screen.blit(_vgrad(r.w, r.h, top, bot, radius=8),
                        (r.x, r.y))
        else:
            pygame.draw.rect(screen, top, r, border_radius=8)
        pygame.draw.rect(screen, (120, 130, 160) if hover
                         else (72, 80, 106), r, 1, border_radius=8)
        tcol = TEXT_BODY if hover else TEXT_DIM
    draw_text(screen, font, letter(label), tcol,
              center=r.center, shadow=False)
    btns[bid] = r
    return r


def screen_title(screen, text, cx, y, glow=True, sub=None,
                 sub_color=CYAN_SOFT, ornament=True):
    """Judul layar seragam: Cinzel gradasi emas + glow radial +
    ornamen (garis - wajik - garis). `sub` = subtitle plate.
    `ornament=False` kalau ada elemen UI tepat di bawah judul."""
    from _core import title_font
    tf = title_font(64)
    if glow and cheap_alpha():
        screen.blit(_radial(620, 150, (255, 205, 90), 46),
                    (cx - 310, y - 62))
    outline_text(screen, tf, text, None, center=(cx, y))

    if ornament:
        fy = y + 52
        pygame.draw.line(screen, EDGE_GOLD, (cx - 220, fy),
                         (cx - 18, fy), 2)
        pygame.draw.line(screen, EDGE_GOLD, (cx + 18, fy),
                         (cx + 220, fy), 2)
        pygame.draw.polygon(screen, GOLD,
                            [(cx - 8, fy), (cx, fy - 7),
                             (cx + 8, fy), (cx, fy + 7)])
        pygame.draw.circle(screen, GOLD_BRIGHT, (cx - 230, fy), 3)
        pygame.draw.circle(screen, GOLD_BRIGHT, (cx + 230, fy), 3)

    if sub:
        from _core import get_font
        sf = get_font(30, "body_semibold")
        sub_surf = sf.render(letter(sub), True, sub_color)
        plate = pygame.Rect(cx - (sub_surf.get_width() + 56) // 2,
                            fy + 12,
                            sub_surf.get_width() + 56, 44)
        if cheap_alpha():
            screen.blit(_vgrad(plate.w, plate.h, (26, 32, 58),
                               (14, 18, 34), radius=10),
                        (plate.x, plate.y))
        else:
            pygame.draw.rect(screen, (16, 20, 38), plate,
                             border_radius=10)
        pygame.draw.rect(screen, EDGE_GOLD, plate, 1, border_radius=10)
        corner_ticks(screen, plate, GOLD, length=8, width=1, inset=3)
        screen.blit(sub_surf, sub_surf.get_rect(center=plate.center))


def back_button(screen, btns, bid, cx, y, hover=False, font=None):
    """Tombol BACK seragam (kecil, netral, ikon panah)."""
    from _core import get_font
    if font is None:
        font = get_font(26, "body_semibold")
    w, h = 200, 42
    r = pygame.Rect(cx - w // 2, y - h // 2, w, h)
    pill(screen, btns, bid, "BACK", r, "neutral", font, hover=hover,
         icon="back")
    return r


def scroll_indicator(screen, x, y, height, scroll_pos, max_scroll,
                     width=6):
    """Indikator scroll ramping."""
    track = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (28, 32, 52), track, border_radius=3)
    if max_scroll > 0:
        ratio = height / (height + max_scroll)
        thumb_h = max(18, int(height * ratio))
        thumb_y = y + int((height - thumb_h) * (scroll_pos / max_scroll))
        if cheap_alpha():
            screen.blit(_vgrad(width, thumb_h, GOLD_BRIGHT,
                               (196, 138, 40), radius=3),
                        (x, thumb_y))
        else:
            pygame.draw.rect(screen, GOLD,
                             (x, thumb_y, width, thumb_h),
                             border_radius=3)
    return track


def hp_bar(screen, x, y, w, h, ratio, color=GREEN):
    """Bar HP/mana premium: track gelap + isi gradasi + border."""
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, (16, 18, 30), r, border_radius=h // 2)
    fw = int(w * max(0.0, min(1.0, ratio)))
    if fw > 3:
        light = tuple(min(255, c + 50) for c in color)
        if cheap_alpha():
            screen.blit(_vgrad(fw, h, light, color, radius=h // 2),
                        (x, y))
        else:
            pygame.draw.rect(screen, color, (x, y, fw, h),
                             border_radius=h // 2)
    pygame.draw.rect(screen, (86, 92, 120), r, 1, border_radius=h // 2)


def progress_bar(screen, x, y, w, frac, color=GOLD, h=8):
    """Bar progres emas."""
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, (30, 34, 54), r, border_radius=h // 2)
    fw = int(w * max(0.0, min(1.0, frac)))
    if fw > 3:
        if cheap_alpha():
            screen.blit(_vgrad(fw, h, tuple(min(255, c + 40)
                                            for c in color), color,
                               radius=h // 2), (x, y))
        else:
            pygame.draw.rect(screen, color, (x, y, fw, h),
                             border_radius=h // 2)
    pygame.draw.rect(screen, (96, 96, 126), r, 1, border_radius=h // 2)
