# In-game visual audit: level intro, Godot 4.7.2 vs Pygame

Layer 9cs. Scope: the first player-facing frame of a match — the level intro screen — as
drawn by `_render.py::LevelIntroScreen` (oracle) and by
`godot_rebuild/scenes/prototype/prototype_view.gd::_draw_level_intro`.

Static only: this audit compares the **source render** (Pygame, executed here) against a
**Godot 4.7.2 screenshot** supplied from a desktop run. No Godot binary runs in this
environment, so nothing below claims that the patched build was executed; the two fixes are
argued from the source of both implementations and guarded statically in
`tests/validate_project.py`.

## Evidence

`docs/screenshots/parity/level-intro-pygame-vs-godot.png`

* top — `LevelIntroScreen`, level 1 (`The Fallen Realm`, boss `Abaddon`), frame 46, rendered
  by Pygame at **1624x720** (the same window the Godot capture used);
* bottom — the Godot capture, game area cropped to 1624x720 (window chrome and the open
  `PERMAINAN DIJEDA` dialog removed so the intro below it is visible).

Reproduce the oracle frame:

```bash
python3 -m venv /tmp/pgv && /tmp/pgv/bin/pip install -q pygame-ce pillow
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /tmp/pgv/bin/python - <<'PY'
import os, sys
ROOT = "/home/user/mystic-arena"; sys.path.insert(0, ROOT); os.chdir(ROOT)
import pygame; pygame.init()
import _core, _render                      # _core first: _render imports it back
from _render import LevelIntroScreen
level = {"level_number": 1, "name": "The Fallen Realm",
         "description": "Face Abaddon, the Lord of Avernus", "enemy_hp_mult": 1.0,
         "enemy_damage_mult": 1.0, "meta_gold_reward_win": 3000, "map_theme": "forest",
         "true_boss": "abaddon", "starting_gold": 1000}
W, H = 1624, 720
screen = pygame.display.set_mode((W, H))
intro = LevelIntroScreen(level, W, H)
for _ in range(46):                        # FADE_IN is 30; the prompt appears after it
    intro.update()
screen.fill((10, 12, 26))
intro.draw(screen)
pygame.image.save(screen, "/tmp/pg_intro_1624.png")
PY
```

## What the capture proves

1. **The intro geometry is already right, the canvas is not.**
   Every op in the Godot frame lands on the same pixel as the oracle's *1280x720* layout
   (LEVEL baseline 120, name 390, difficulty 500, gold 620 and 660, prompt 660, divider
   x=640). The two screens disagree because the oracle lays out for `screen_w = 1624` while
   Godot laid out for 1280 and then painted that 1280 wide result into a 1624 wide canvas:
   the divider sits at x=640 instead of 812 and the right 344 px stay empty.
2. **The font faces were missing.** `level_intro_layout.gd::_text_op` never wrote a `style`
   key, `prototype_view.gd` therefore fell back to `BossFont` (Barlow-SemiBold) for every
   string, and the oracle's Cinzel titling face (`title_font`) plus the three body faces
   never reached the intro. Compare `THE FALLEN REALM` (oracle: small-caps title face,
   ~480 px wide at 46 px) with `The Fallen Realm` (capture: Barlow, ~355 px wide).
3. **The intro is dimmed by the pause dialog, not by the intro.** The capture was taken in
   the paused state; the whole frame (aura included) sits at roughly a third of the oracle's
   brightness, which is the dim layer of the pause overlay. No intro-side brightness bug is
   proven by this frame.
4. **Godot-only chrome is stacked on top of it**: the `HUD/TopBar` button row and the
   `migration_status` readout (`Boss: belum muncul | AI ON · H0 · build 2 · upgrade 1`).
   Neither has a counterpart in the source, and the top bar overlaps the intro's own top
   block.

## Fixed in 9cs

| # | Finding | Fix |
|---|---------|-----|
| F1 | Intro / boss cinematics laid out on the fixed `MapRenderer.MAP_WIDTH/HEIGHT` (1280x720) canvas while the window is 1624x720 (`window/stretch/aspect="expand"`) | `Prototype.screen_size` (default 1280x720) now feeds `LevelIntroScreen.setup`, `BossIntroCinematic.setup` and `BossDeathAnimation.setup`; `prototype_view.gd::_sync_screen_size` pushes the live canvas size every frame, and `Prototype.set_screen_size` re-lays out an active intro (the source reads `screen_w/screen_h` on every frame too). The map itself keeps 1280x720, exactly like `MapRenderer.map_width = SCREEN_WIDTH`. |
| F2 | Every intro string drawn in Barlow-SemiBold | `prototype_view.gd::_intro_style` recovers the source face from the op size — `>= 46` → `title` (`title_font`), `>= 32` → `body_semibold`, `>= 24` → `body_medium`, else `body`; `_intro_font` is used by both the text op and `_measure_intro_text`, so centred ops land where the oracle puts them. |

## Right dock (side panel) — layer 9ct

`docs/screenshots/parity/mobile-dock-pygame-vs-godot.png` compares the source mobile
composition at 1624x720 with the same canvas on the Godot side.

* top — Pygame drawing the real `Game` into a 1280x720 subsurface of a 1624x720 surface,
  with `mobile.sidepanel.SidePanel` mounted on the 344 px right dock: PAUSE, STATUS
  (gold / level / wave / difficulty), the hero list with its skill pips, and the five
  tactical commands. The arena itself carries no HUD panel.
* bottom — the Godot capture on the same canvas, annotated with the live scene geometry:
  `TacticalPanel` at 1032..1264 and `BottomBar` at 16..1264 both sit **inside** the arena,
  while the 344 px dock strip stays empty.

Cause: `prototype_screen.gd::_layout_side_panel()` passed the viewport width only when
`_is_mobile_device()` was true, so a desktop run always configured the dock with 1280 and
`SidePanelLayout.panel_rect(1280)` returned an empty rect — the dock existed but was never
mounted. The source mounts it from the **surface width**, not the device class:

```python
sisa = max(0, surface.get_width() - LOGICAL_WIDTH)   # platform_utils.create_display
if sisa >= 120:                                      # panel sementara sisa >= 120 px
    _display_state["panel"] = pygame.Rect(LOGICAL_WIDTH, 0, sisa, LOGICAL_HEIGHT)
```

### Fixed in 9ct

| # | Change |
|---|--------|
| F5 | `side_panel.configure(viewport_width)` — the dock is mounted whenever the canvas leaves at least 120 px beside the 1280 arena, so the 1624x720 desktop window gets the same dock as the Android surface (and a 1280x720 window still gets none). |
| F6 | A mounted dock suppresses the desktop composition on any device: `TopBar` (title, gold, wave, speed, pause, back, tactical and command-dock toggles), the AI/QA toggle, the forge button, the `migration_status` readout, `TacticalPanel`, the mobile pause circle and the `HeroCommands` row all step aside. |
| F7 | `Commands` / `Paths` (sell, upgrade, regen shield) are the one thing the dock cannot yet render, because the tapped-tower popup still has no state builder (D2). `_apply_dock_command_bar` keeps that bar as the stand-in and shows it **only while a blue tower is selected**, instead of permanently covering the bottom of the map. |
| F8 | The dock steps aside for the level intro and the boss cinematics (`side_panel.visible = not _cinematic_active(world)`), matching the source, which does not call `sidepanel.draw` during them. |

### Open after 9ct

| # | Finding |
|---|---------|
| D2 | The tapped-tower popup (`TowerPopupLayout`) has no state builder in the playable screen and no press routing, so tower upgrade / sell / regen shield still depend on the Godot stand-in bar (F7). Closing D2 retires that bar. |
| D8 | Dock content parity was not verified here: the stone backdrop, the 250 ms refresh cadence, combo/kill notifications and the “notifikasi dihapus” state all come from `mobile/sidepanel.py` and are covered only by `tests/side_panel_source_oracle.py` plus the native `side_panel_checks.gd`. |
| D9 | On a 1280 px window (no dock) the desktop chrome stays as it was, including the `migration_status` readout; the source has no such window at all. |

## Open findings (registered, not fixed here)

| # | Finding | Note |
|---|---------|------|
| D5 | `HUD/TopBar` (Item / Hero / AI:ON / Jeda / Taktik / Kontrol / Menu) and the `migration_status` label are Godot-only. | Narrowed by 9ct: both are hidden whenever the dock is mounted (any device). They only remain in the 1280 px window, where the source has no dock either. |
| D6 | Pause overlay is a themed `Control` dialog (`Permainan Dijeda` + 3 buttons) instead of `_core.py::_draw_pause_menu` (400x400 centred panel, `PAUSED` title at `title_font(56)`, `MODE: EASY/NORMAL/HARD` badge with `LOCKED`, divider, 4 buttons 300x48: RESUME / SETTINGS / MAIN MENU / QUIT GAME with icons). The dim layer it adds has no source counterpart. | Needs a `PauseMenuLayout` op list + drawn port, plus the SETTINGS submenu route. |
| D7 | Intro under the top bar: the intro is drawn in the arena layer while `HUD/TopBar` is a `CanvasLayer(layer = 10)` panel, so the bar stays visible over the intro. | Fixed whenever the dock is mounted (the bar is hidden and the dock clears itself during cinematics, 9ct/F8); still open in the 1280 px window. |

## Not claimed

* The patched build was not executed here; F1/F2 are argued from source and guarded by
  `tests/validate_project.py` (block 9cs).
* D5–D7 are open. Pixel parity of the in-game frame is **not** established.
