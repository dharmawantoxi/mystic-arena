extends RefCounted
## Layer 9ch: port of `_render.py::_skip_button_label()` (module level, line 1604).
##
## pygame builds the label from the input mode instead of hardcoding it:
##
## ```python
## def _skip_button_label():
##     if platform_utils.TOUCH_MODE:          # Android build / forced touch
##         return 'TAP'
##     if __main__.game_instance.controller_mgr.is_controller_mode():
##         return controller_mgr.get_action_label('skip')   # 'A', 'Cross', ...
##     return 'SPACE'
## ```
##
## Two call sites use it: `BossDeathAnimation._draw_celebration()` (`"[%s] to
## continue"`, the only one that is reachable) and `BossIntroCinematic._draw_skip_hint()`
## (`"[%s] to skip"`, never called from `draw()` — dead, see the layer report).
##
## The cell that stayed behind: `boss_celebration_layout.gd` hardcoded `SKIP_LABEL :=
## "SPACE"`, so the Android build told the player to press a keyboard key. This module
## restores the source order (touch first, then controller, then keyboard) and the two
## layouts splice the label into the same `"[label] to action"` line pygame renders.

## `return 'TAP'` — `platform_utils.TOUCH_MODE` in the pygame source.
const TOUCH_LABEL := "TAP"
## The final `return 'SPACE'` fallback.
const KEYBOARD_LABEL := "SPACE"


## `_skip_button_label()`: touch mode wins over the controller, the controller wins
## over the keyboard. `controller_active` mirrors `controller_mgr.is_controller_mode()`
## and `controller_label` its `get_action_label('skip')` (empty means "no runtime").
static func label(
	touch_mode: bool,
	controller_active: bool = false,
	controller_label: String = "",
) -> String:
	if touch_mode:
		return TOUCH_LABEL
	if controller_active:
		var trimmed := controller_label.strip_edges()
		if not trimmed.is_empty():
			return trimmed
	return KEYBOARD_LABEL


## The full hint line both pygame call sites blit: `f"[{_skip_button_label()}] to
## {action}"` — the celebration uses `continue`, the dead intro hint uses `skip`.
static func hint(label_text: String, action: String) -> String:
	return "[%s] to %s" % [label_text, action]
