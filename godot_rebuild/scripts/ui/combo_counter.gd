extends RefCounted
## Kill combo tracker, ported from `_render.py::ComboCounter`: each kill
## refreshes a 120 tick window, pops the display scale and flashes the colour;
## expiry records the combo then fades the panel out.
##
## The source's `add_kill` also pushes a tier banner to a Python-only side
## panel (`from mobile import sidepanel`) inside a try/except. That side
## effect is deliberately not ported; `tier_for` exposes the same thresholds
## for whoever renders them.

const MAX_TIMER := 120
const FLASH_TICKS := 20
const POP_SCALE := 1.3
const POP_LERP := 0.3
const SETTLE_LERP := 0.15
const FADE_MUL := 0.85
const FADE_CUTOFF := 0.05

var count := 0
var timer := 0
var max_timer := MAX_TIMER
var display_scale := 0.0
var target_scale := 1.0
var color_flash := 0
var last_combo := 0


func add_kill() -> void:
	count += 1
	timer = max_timer
	target_scale = POP_SCALE
	color_flash = FLASH_TICKS


func update() -> void:
	if timer > 0:
		timer -= 1
		if timer <= 0:
			last_combo = count
			count = 0
	if count > 0:
		if display_scale < target_scale:
			display_scale += (target_scale - display_scale) * POP_LERP
		else:
			target_scale = 1.0
			display_scale += (1.0 - display_scale) * SETTLE_LERP
	else:
		display_scale *= FADE_MUL
		if display_scale < FADE_CUTOFF:
			display_scale = 0.0
	if color_flash > 0:
		color_flash -= 1


## Tier banner for an exact combo count. Returns an empty dictionary when
## the source would announce nothing — the thresholds are `==`, not `>=`,
## so a count of 7 announces nothing at all.
static func tier_for(value: int) -> Dictionary:
	match value:
		3:
			return {"label": "COMBO x3", "color": Color8(255, 255, 255)}
		5:
			return {"label": "KILLING SPREE!", "color": Color8(100, 255, 100)}
		10:
			return {"label": "RAMPAGE!", "color": Color8(255, 200, 50)}
		15:
			return {"label": "UNSTOPPABLE!", "color": Color8(255, 100, 50)}
		20:
			return {"label": "GODLIKE!", "color": Color8(255, 50, 50)}
	return {}
