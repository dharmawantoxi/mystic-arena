extends RefCounted
## Layer 9bq4: urgharun's R/enrage foreground FX as a pure op list.
##
## `bosses/level40.py::_NS_urgharun.draw_urgharun` keeps four layers: the fury aura and
## ground ring, the skill ground FX (`_draw_enrage_ground`, out of scope here), the body
## pose, and LAYER 4 - `_draw_enrage_fx` while `active_skill == "r"`. `Boss.draw` paints
## the HP bar and the name plate AFTER the renderer, so this foreground layer sits over
## the body and under the bar.
##
## Ops use the `tests/draw_recorder.py` format, so `urgharun_enrage_fx_source_oracle.py`
## pins every one in source order:
##   * ten rising flame teardrops - `fury_dark` circle r=3, `fury_mid` r=2 and
##     `fury_light` r=1 on the same x (stacked upward), then a 1 px `fury_hot` and a
##     1 px `fury_shine` spark above them;
##   * a decaying aura ring, `range(38, 32, -1)`, stroked 1 px in `fury_light` with
##     alpha `180 * aura_pulse * (38 - r) / 6`;
##   * six rising embers, alternating 35 px left/right of the boss, each a 2x2
##     `fury_hot` rect with a 1 px `fury_shine` core on its top-left pixel.
##
## Quirks kept:
##   * the function computes `progress` from `timer` and never reads it, so the layer is
##     a function of `pulse` alone - the elapsed cast time changes nothing;
##   * `flame_h` is computed and unused too;
##   * the source draws into the SRCALPHA boss sprite canvas (`heroes._boss_get_canvas`),
##     so these alpha values survive as pixel alpha. `pygame.draw` writes alpha instead of
##     blending it, so overlapping shapes in this layer replace each other rather than
##     accumulate; the view replays them with normal blending.

const BOSS_TYPE := "urgharun"
const SKILL := "r"
## The layer normalises the cast by its own 80 ticks before discarding the result.
const DURATION := 80
const FLAME_COUNT := 10
const FLAME_RADIUS := 32
const AURA_TOP := 38
const AURA_BOTTOM := 32
const AURA_STEPS := 6
const EMBER_COUNT := 6
const FURY_DARK := [130, 15, 15]
const FURY_MID := [230, 40, 40]
const FURY_LIGHT := [255, 110, 90]
const FURY_HOT := [255, 180, 140]
const FURY_SHINE := [255, 230, 200]


static func active(boss_type: String, active_skill: String) -> bool:
	return boss_type == BOSS_TYPE and active_skill == SKILL


## `_draw_enrage_fx(surface, boss, x, y, timer, pulse)`: `timer` is the boss's
## `active_skill_timer`, `pulse` its `pulse`, and `x`/`y` the int anchor `Boss.draw` hands
## to the renderer.
static func ops(x: int, y: int, timer: int, pulse: float) -> Array:
	# The source keeps this normalisation for symmetry with `_draw_enrage_ground`; nothing
	# in the layer reads it. Written out so the unused-timer quirk stays visible.
	@warning_ignore("unused_variable")
	var progress := clampf(1.0 - float(timer) / float(DURATION), 0.0, 1.0)
	var out: Array = []
	for index in range(FLAME_COUNT):
		var angle := pulse * 0.5 + float(index) * PI / 5.0
		var flame_x := x + int(cos(angle) * float(FLAME_RADIUS))
		var flame_y_base := y + int(sin(angle) * float(FLAME_RADIUS) * 0.5)
		# Python's float `%` keeps the divisor's sign, as `fposmod` does.
		var flame_t := fposmod(pulse * 0.6 + float(index) * 0.15, 1.0)
		var flame_y := flame_y_base - int(flame_t * 20.0)
		var alpha := _alpha(220.0 * (1.0 - flame_t))
		out.append(_circle([flame_x, flame_y], 3, FURY_DARK, alpha, 0))
		out.append(_circle([flame_x, flame_y - 1], 2, FURY_MID, alpha, 0))
		out.append(_circle([flame_x, flame_y - 2], 1, FURY_LIGHT, alpha, 0))
		out.append(_rect([flame_x, flame_y - 3, 1, 1], FURY_HOT, alpha))
		out.append(_rect([flame_x, flame_y - 4, 1, 1], FURY_SHINE, alpha))
	var aura_pulse := sin(pulse * 4.0) * 0.3 + 0.7
	for radius in range(AURA_TOP, AURA_BOTTOM, -1):
		var alpha := _alpha(180.0 * aura_pulse * float(AURA_TOP - radius) / float(AURA_STEPS))
		out.append(_circle([x, y], radius, FURY_LIGHT, alpha, 1))
	for index in range(EMBER_COUNT):
		var ember_t := fposmod(pulse * 0.8 + float(index) * 0.15, 1.0)
		var side := 35 if index % 2 == 0 else -35
		var ember_x := x + side + int(sin(pulse + float(index)) * 15.0)
		var ember_y := y + 20 - int(ember_t * 40.0)
		var alpha := _alpha(240.0 * (1.0 - ember_t))
		out.append(_rect([ember_x, ember_y, 2, 2], FURY_HOT, alpha))
		out.append(_rect([ember_x, ember_y, 1, 1], FURY_SHINE, alpha))
	return out


static func _alpha(value: float) -> int:
	return clampi(int(value), 0, 255)


static func _circle(center: Array, radius: int, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
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
