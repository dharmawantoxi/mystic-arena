"""Optional in-game Kaizen preview overlay.

The renderer itself stays procedural and the review sheets are deliberately
opt-in.  Normal arena frames therefore do not load or draw a static PNG, while
review mode shows both the body animation sheet and the Q/W/E/R skill sheet in
the right-side card area.

Enable at launch with ``MYSTIC_KAIZEN_REVIEW=1`` or toggle it with F9 on
Desktop.  Sheets are loaded lazily so normal gameplay never pays for them.
"""

from __future__ import annotations

import os
from pathlib import Path

import pygame


_REVIEW_DIR = Path(__file__).resolve().parents[1] / "assets" / "review"
_ASSET_PATH = _REVIEW_DIR / "kaizen_v1_anim_sheet.png"
_SKILL_ASSET_PATH = _REVIEW_DIR / "kaizen_v1_skill_sheet.png"


def _env_enabled() -> bool:
    return os.environ.get("MYSTIC_KAIZEN_REVIEW", "0").strip().lower() in {
        "1", "true", "yes", "on"
    }


_enabled = _env_enabled()
_sheets = {}
_scaled = {}
_warned_missing = set()


def enabled() -> bool:
    """Return whether the optional review cards are currently visible."""
    return _enabled


def set_enabled(value: bool) -> bool:
    """Set the review state and return the new value."""
    global _enabled
    _enabled = bool(value)
    return _enabled


def toggle() -> bool:
    """Toggle the review cards (used by the desktop F9 shortcut)."""
    return set_enabled(not _enabled)


def asset_path() -> Path:
    """Expose the packaged animation review asset for diagnostics/tests."""
    return _ASSET_PATH


def skill_asset_path() -> Path:
    """Expose the packaged Q/W/E/R skill review asset."""
    return _SKILL_ASSET_PATH


def _load_sheet(path: Path):
    key = str(path)
    cached = _sheets.get(key)
    if cached is not None:
        return cached
    if not path.is_file():
        if key not in _warned_missing:
            print("[KAIZEN REVIEW] asset tidak ditemukan: %s" % path)
            _warned_missing.add(key)
        return None
    try:
        # Both source sheets have opaque navy backgrounds.  convert() keeps
        # their blit cheap and avoids alpha fringes after nearest scaling.
        cached = pygame.image.load(str(path)).convert()
    except (OSError, pygame.error) as exc:
        if key not in _warned_missing:
            print("[KAIZEN REVIEW] gagal memuat asset: %s" % exc)
            _warned_missing.add(key)
        return None
    _sheets[key] = cached
    return cached


def _scaled_sheet(path: Path, size):
    source = _load_sheet(path)
    if source is None:
        return None
    size = (max(1, int(size[0])), max(1, int(size[1])))
    key = (str(path), size)
    cached = _scaled.get(key)
    if cached is None:
        # Nearest scaling is intentional: this is a pixel-art review card.
        cached = pygame.transform.scale(source, size)
        _scaled[key] = cached
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


def _card_layout(surface, panel_rect, card_index, source):
    """Return ``(card_rect, image_rect)`` for one stacked review card."""
    sw, sh = surface.get_size()
    gap = 10

    # A real side panel is preferred, but a very narrow remainder is not a
    # useful review surface.  In that case place the cards inside the right
    # edge of the logical arena instead of making the previews unreadable.
    use_panel = panel_rect is not None and panel_rect.width >= 250
    if use_panel:
        card_w = max(250, panel_rect.width - 16)
        card_h = min(250, max(190, (sh - 96 - gap) // 2))
        card_x = panel_rect.x + (panel_rect.width - card_w) // 2
        card_y = panel_rect.y + 78 + card_index * (card_h + gap)
    else:
        card_w = min(348, max(250, sw // 3))
        card_h = 250
        card_x = max(8, sw - card_w - 14)
        card_y = 90 + card_index * (card_h + gap)

    # Leave room for title/footer while preserving each source sheet's ratio.
    inner_w = max(1, card_w - 20)
    inner_h = max(1, card_h - 54)
    ratio = source.get_width() / float(max(1, source.get_height()))
    image_w = min(inner_w, int(inner_h * ratio))
    image_h = max(1, int(image_w / ratio))
    image_x = card_x + (card_w - image_w) // 2
    image_y = card_y + 34 + max(0, (inner_h - image_h) // 2)
    return (
        pygame.Rect(card_x, card_y, card_w, card_h),
        pygame.Rect(image_x, image_y, image_w, image_h),
    )


def _draw_card(surface, card_rect, image_rect, source_path, title, footer,
               font_getter):
    pygame.draw.rect(surface, (10, 13, 25), card_rect, border_radius=9)
    pygame.draw.rect(surface, (71, 119, 190), card_rect, 2, border_radius=9)
    pygame.draw.line(
        surface,
        (76, 205, 255),
        (card_rect.x + 10, card_rect.y + 29),
        (card_rect.right - 10, card_rect.y + 29),
        1,
    )

    title_font = _make_font(font_getter, 14)
    if title_font is not None:
        title_surf = title_font.render(title, True, (190, 225, 255))
        surface.blit(title_surf, (card_rect.x + 10, card_rect.y + 8))

    preview = _scaled_sheet(source_path, image_rect.size)
    if preview is not None:
        surface.blit(preview, image_rect.topleft)
        pygame.draw.rect(surface, (43, 74, 117), image_rect, 1)

    footer_font = _make_font(font_getter, 10)
    if footer_font is not None:
        footer_surf = footer_font.render(footer, True, (155, 175, 201))
        footer_rect = footer_surf.get_rect(
            center=(card_rect.centerx, card_rect.bottom - 10)
        )
        surface.blit(footer_surf, footer_rect)
    return preview is not None


def draw(surface, panel_rect=None, font_getter=None) -> bool:
    """Draw both Kaizen review sheets when the opt-in switch is enabled.

    ``surface`` is normally the full display surface when a right side panel
    exists, otherwise it is the logical arena surface.  The function is a
    no-op unless review mode is enabled.
    """
    if not _enabled or surface is None:
        return False

    drawn = False
    for index, (path, title, footer) in enumerate((
        (_ASSET_PATH, "KAIZEN V1 ANIMATION",
         "IDLE  •  WALK  •  ATTACK"),
        (_SKILL_ASSET_PATH, "KAIZEN V1 SKILLS",
         "Q DASH  •  W WALL  •  E SWEEP  •  R TORNADO"),
    )):
        source = _load_sheet(path)
        if source is None:
            continue
        card_rect, image_rect = _card_layout(
            surface, panel_rect, index, source)
        drawn = _draw_card(
            surface, card_rect, image_rect, path, title, footer,
            font_getter) or drawn
    return drawn
