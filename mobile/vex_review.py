"""Optional in-game Vex preview overlay.

Same idea as ``mobile/kaizen_review.py`` but for the Vex V1 pixel-art
renderer: the renderer itself stays procedural and the review sheets are
deliberately opt-in, so normal arena frames never load or draw a static PNG.
In review mode both the body animation sheet and the Q/W/E/R skill sheet are
shown in the right-side card area.  The card layout engine is shared with
``mobile/kaizen_review`` so both overlays always look identical.

Enable at launch with ``MYSTIC_VEX_REVIEW=1`` or toggle it with F10 on
Desktop.  Sheets are loaded lazily so normal gameplay never pays for them.
"""

from __future__ import annotations

import os
from pathlib import Path

import pygame

from mobile import kaizen_review as _layout


_REVIEW_DIR = Path(__file__).resolve().parents[1] / "assets" / "review"
_ASSET_PATH = _REVIEW_DIR / "vex_v1_anim_sheet.png"
_SKILL_ASSET_PATH = _REVIEW_DIR / "vex_v1_skill_sheet.png"


def _env_enabled() -> bool:
    return os.environ.get("MYSTIC_VEX_REVIEW", "0").strip().lower() in {
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
    """Toggle the review cards (used by the desktop F10 shortcut)."""
    return set_enabled(not _enabled)


def asset_path() -> Path:
    """Expose the packaged animation review asset for diagnostics/tests."""
    return _ASSET_PATH


def skill_asset_path() -> Path:
    """Expose the packaged Q/W/E/R skill review asset for diagnostics/tests."""
    return _SKILL_ASSET_PATH


def _load_sheet(path: Path):
    key = str(path)
    cached = _sheets.get(key)
    if cached is not None:
        return cached
    if not path.is_file():
        if key not in _warned_missing:
            print("[VEX REVIEW] asset tidak ditemukan: %s" % path)
            _warned_missing.add(key)
        return None
    try:
        # Both source sheets have opaque backgrounds.  convert() keeps their
        # blit cheap and avoids alpha fringes after nearest scaling.
        cached = pygame.image.load(str(path)).convert()
    except (OSError, pygame.error) as exc:
        if key not in _warned_missing:
            print("[VEX REVIEW] gagal memuat asset: %s" % exc)
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


def draw(surface, panel_rect=None, font_getter=None) -> bool:
    """Draw both Vex review sheets when the opt-in switch is enabled.

    ``surface`` is normally the full display surface when a right side panel
    exists, otherwise it is the logical arena surface.  The function is a
    no-op unless review mode is enabled.
    """
    if not _enabled or surface is None:
        return False

    # Rebind the layout helper's caches locally so Kaizen and Vex previews
    # do not share sheet/scaled entries (paths differ, so this is only a
    # defensive copy of the kaizen drawing routine).
    def _draw(source_path, card_rect, image_rect, title, footer, fg):
        pygame.draw.rect(surface, (10, 9, 21), card_rect, border_radius=9)
        pygame.draw.rect(surface, (122, 82, 190), card_rect, 2,
                         border_radius=9)
        pygame.draw.line(
            surface,
            (132, 235, 226),
            (card_rect.x + 10, card_rect.y + 29),
            (card_rect.right - 10, card_rect.y + 29),
            1,
        )
        title_font = _layout._make_font(fg, 14)
        if title_font is not None:
            surface.blit(title_font.render(title, True, (198, 238, 232)),
                         (card_rect.x + 10, card_rect.y + 8))
        preview = _scaled_sheet(source_path, image_rect.size)
        if preview is not None:
            surface.blit(preview, image_rect.topleft)
            pygame.draw.rect(surface, (70, 52, 118), image_rect, 1)
        footer_font = _layout._make_font(fg, 10)
        if footer_font is not None:
            footer_surf = footer_font.render(footer, True, (160, 176, 198))
            footer_rect = footer_surf.get_rect(
                center=(card_rect.centerx, card_rect.bottom - 10))
            surface.blit(footer_surf, footer_rect)
        return preview is not None

    drawn = False
    for index, (path, title, footer) in enumerate((
        (_ASSET_PATH, "VEX V1 ANIMATION",
         "IDLE  \u2022  WALK  \u2022  ATTACK"),
        (_SKILL_ASSET_PATH, "VEX V1 SKILLS",
         "Q ORB  \u2022  W ECLIPSE  \u2022  E PRISON  \u2022  R FLUX"),
    )):
        source = _load_sheet(path)
        if source is None:
            continue
        card_rect, image_rect = _layout._card_layout(
            surface, panel_rect, index, source)
        drawn = _draw(path, card_rect, image_rect, title, footer,
                      font_getter) or drawn
    return drawn
