extends RefCounted
## Layer 9bq5: urgharun's R/enrage ground FX as a pure op list.
##
## `bosses/level40.py::_NS_urgharun.draw_urgharun` keeps four layers: the fury aura and the
## ground ring, LAYER 2 - `_draw_enrage_ground` while `active_skill == "r"` (behind the
## body), the body pose, and LAYER 4 - `_draw_enrage_fx` (foreground, slice 9bq4). This
## layout owns LAYER 2 only.
##
## Ops use the `tests/draw_recorder.py` format, so `urgharun_enrage_ground_source_oracle.py`
## pins every one in source order:
##   * two pulsing ground rings. Each ring draws three nested outlines on the same rect
##     family - `fury_dark` 3 px, `fury_mid` 2 px inset by (3, 2), and `fury_light` 1 px
##     inset by (6, 4) - with `r = int(35 + i * 8 + sin(phase * 2) * 3)` and alpha
##     `_alpha(220 * pulse - i * 40)` where `pulse = sin(phase * 3) * 0.3 + 0.7`. All six
##     ellipses share the rect `(x - r, y + 40 - r // 3, r * 2, r * 2 // 3)`;
##   * ten runes on a 38 px circle squashed to 0.4 vertically around `y + 42`, each a 3x3
##     `fury_hot` square at alpha `_alpha(240 * pulse)` with a 1 px `fury_shine` core.
##
## Quirks kept:
##   * the function computes `progress` from `timer` and never reads it, so the layer is a
##     function of `phase` alone;
##   * the 1 px rune core uses the raw palette tuple, so its alpha stays 255 while the 3x3
##     square fades;
##   * `r` can drop to 32 when `sin(phase * 2)` is negative, and `r // 3` floors, so the
##     ring's vertical offset moves with its radius.

const BOSS_TYPE := "urgharun"
const SKILL := "r"
## The layer normalises the cast by its own 80 ticks before discarding the result.
const DURATION := 80
const RING_COUNT := 2
const RUNE_COUNT := 10
const RUNE_RADIUS := 38
const FURY_DARK := [130, 15, 15]
const FURY_MID := [230, 40, 40]
const FURY_LIGHT := [255, 110, 90]
const FURY_HOT := [255, 180, 140]
const FURY_SHINE := [255, 230, 200]


static func active(boss_type: String, active_skill: String) -> bool:
	return boss_type == BOSS_TYPE and active_skill == SKILL


## `_draw_enrage_ground(surface, boss, x, y, timer, phase)`: `timer` is the boss's
## `active_skill_timer`, `phase` its `pulse`, and `x`/`y` the int anchor `Boss.draw` hands
## to the renderer.
static func ops(x: int, y: int, timer: int, pulse: float) -> Array:
	@warning_ignore("unused_variable")
	var progress := clampf(1.0 - float(timer) / float(DURATION), 0.0, 1.0)
	var ring_pulse := sin(pulse * 3.0) * 0.3 + 0.7
	var out: Array = []
	for index in range(RING_COUNT):
		var radius := int(35.0 + float(index) * 8.0 + sin(pulse * 2.0) * 3.0)
		var alpha := _alpha(220.0 * ring_pulse - float(index) * 40.0)
		# `r // 3` floors and `r * 2 // 3` floors again; `r` stays positive.
		var top := y + 40 - floori(float(radius) / 3.0)
		var height := floori(float(radius * 2) / 3.0)
		var left := x - radius
		var width := radius * 2
		out.append(_ellipse([left, top, width, height], FURY_DARK, alpha, 3))
		out.append(_ellipse([left + 3, top + 2, width - 6, height - 4], FURY_MID, alpha, 2))
		out.append(_ellipse([left + 6, top + 4, width - 12, height - 8], FURY_LIGHT, alpha, 1))
	var rune_alpha := _alpha(240.0 * ring_pulse)
	for index in range(RUNE_COUNT):
		var angle := pulse * 0.4 + float(index) * PI / 5.0
		var rune_x := x + int(cos(angle) * float(RUNE_RADIUS))
		var rune_y := y + 42 + int(sin(angle) * float(RUNE_RADIUS) * 0.4)
		out.append(_rect([rune_x, rune_y, 3, 3], FURY_HOT, rune_alpha))
		out.append(_rect([rune_x, rune_y, 1, 1], FURY_SHINE, 255))
	return out


static func _alpha(value: float) -> int:
	return clampi(int(value), 0, 255)


static func _ellipse(rect: Array, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "ellipse",
		"rect": rect,
		"width": width,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}


static func _rect(rect: Array, rgb: Array, alpha: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": rect,
		"width": 0,
		"radius": 0,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}
