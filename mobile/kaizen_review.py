"""Optional in-game Kaizen preview overlay.

The renderer itself stays procedural and the review sheet is deliberately
opt-in.  This keeps the normal arena free of a static PNG while giving a
visual-review switch that works on both a wide mobile layout and desktop.

Enable at launch with ``MYSTIC_KAIZEN_REVIEW=1`` or toggle it with F9 on
Desktop. The sheet is loaded lazily so normal gameplay never pays for the
asset or its scaling.
"""

from __future__ import annotations

import os
from pathlib import Path

import pygame


_ASSET_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "review"
    / "kaizen_v1_anim_sheet.png"
)


def _env_enabled() -> bool:
    return os.environ.get("MYSTIC_KAIZEN_REVIEW", "0").strip().lower() in {
        "1", "true", "yes", "on"
    }


_enabled = _env_enabled()
_sheet = None
_scaled = {}
_warned_missing = False


def enabled() -> bool:
    """Return whether the optional review card is currently visible."""
    return _enabled


def set_enabled(value: bool) -> bool:
    """Set the review state and return the new value."""
    global _enabled
    _enabled = bool(value)
    return _enabled


def toggle() -> bool:
    """Toggle the review card (used by the desktop F9 shortcut)."""
    return set_enabled(not _enabled)


def asset_path() -> Path:
    """Expose the packaged review asset for diagnostics and tests."""
    return _ASSET_PATH


def _load_sheet():
    global _sheet, _warned_missing
    if _sheet is not None:
        return _sheet
    if not _ASSET_PATH.is_file():
        if not _warned_missing:
            print("[KAIZEN REVIEW] asset tidak ditemukan: %s" % _ASSET_PATH)
            _warned_missing = True
        return None
    try:
        # The source sheet has a deliberate opaque navy background.  Using
        # convert() keeps the blit cheap and avoids alpha fringes around the
        # pixel-art blocks when the preview is scaled with nearest-neighbour.
        _sheet = pygame.image.load(str(_ASSET_PATH)).convert()
    except (OSError, pygame.error) as exc:
        if not _warned_missing:
            print("[KAIZEN REVIEW] gagal memuat asset: %s" % exc)
            _warned_missing = True
        return None
    return _sheet


def _scaled_sheet(size):
    source = _load_sheet()
    if source is None:
        return None
    size = (max(1, int(size[0])), max(1, int(size[1])))
    cached = _scaled.get(size)
    if cached is None:
        # Nearest scaling is intentional: this is a pixel-art review card.
        cached = pygame.transform.scale(source, size)
        _scaled[size] = cached
    return cached


def _make_font(font_getter, size):
    if callable(font_getter):
        try:
            return font_getter(size, "body_bold")
        except Exception:
            pass
    try:
        return pygame.font.Font(None, size)
    except Exception:
        return None


def _layout(surface, panel_rect):
    """Return (card_rect, image_rect) in the destination's coordinates."""
    sw, sh = surface.get_size()

    # A real side panel is preferred, but a very narrow remainder is not a
    # useful review surface.  In that case place the card inside the right
    # edge of the logical arena instead of making the preview unreadable.
    use_panel = panel_rect is not None and panel_rect.width >= 250
    if use_panel:
        card_w = max(250, panel_rect.width - 16)
        card_h = min(236, max(208, sh - 92))
        card_x = panel_rect.x + (panel_rect.width - card_w) // 2
        card_y = panel_rect.y + 78
    else:
        card_w = min(348, max(250, sw // 3))
        card_h = 232
        card_x = max(8, sw - card_w - 14)
        card_y = 90

    # Leave room for title and a small footer while preserving the source
    # sheet's 1014:538 aspect ratio.
    inner_w = max(1, card_w - 20)
    inner_h = max(1, card_h - 54)
    source = _load_sheet()
    if source is None:
        return pygame.Rect(card_x, card_y, card_w, card_h), None
    ratio = source.get_width() / float(max(1, source.get_height()))
    image_w = min(inner_w, int(inner_h * ratio))
    image_h = max(1, int(image_w / ratio))
    image_x = card_x + (card_w - image_w) // 2
    image_y = card_y + 34 + max(0, (inner_h - image_h) // 2)
    return (
        pygame.Rect(card_x, card_y, card_w, card_h),
        pygame.Rect(image_x, image_y, image_w, image_h),
    )


def draw(surface, panel_rect=None, font_getter=None) -> bool:
    """Draw the Kaizen animation-sheet review card when enabled.

    ``surface`` is normally the full display surface when a right side panel
    exists, otherwise it is the logical arena surface.  The function is
    intentionally a no-op unless the review switch is enabled.
    """
    if not _enabled or surface is None:
        return False

    card_rect, image_rect = _layout(surface, panel_rect)
    if image_rect is None:
        return False

    # The card is drawn last so it remains readable over a busy combat frame.
    pygame.draw.rect(surface, (10, 13, 25), card_rect, border_radius=9)
    pygame.draw.rect(surface, (71, 119, 190), card_rect, 2, border_radius=9)
    pygame.draw.line(
        surface,
        (76, 205, 255),
        (card_rect.x + 10, card_rect.y + 29),
        (card_rect.right - 10, card_rect.y + 29),
        1,
    )

    title_font = _make_font(font_getter, 15)
    if title_font is not None:
        title = title_font.render("KAIZEN V1 REVIEW", True, (190, 225, 255))
        surface.blit(title, (card_rect.x + 10, card_rect.y + 8))

    preview = _scaled_sheet(image_rect.size)
    if preview is not None:
        surface.blit(preview, image_rect.topleft)
        pygame.draw.rect(surface, (43, 74, 117), image_rect, 1)

    footer_font = _make_font(font_getter, 11)
    if footer_font is not None:
        footer = footer_font.render("IDLE  •  WALK  •  ATTACK", True,
                                   (155, 175, 201))
        footer_rect = footer.get_rect(
            center=(card_rect.centerx, card_rect.bottom - 10)
        )
        surface.blit(footer, footer_rect)
    return True
