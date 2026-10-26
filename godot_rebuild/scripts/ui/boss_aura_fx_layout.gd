extends RefCounted
## Layer 9bq7: the cached aura block of `bosses/base_boss.py::Boss.draw`.
##
## `Boss.draw` paints three concentric-ring auras around the boss anchor, in this order:
##   ABILITY AURA   filled rings while `ability_active`, colour `entrance_color`,
##                  radius `int(ability_range * pulse)`, ring `range(aura_r, aura_r - 20, -3)`,
##                  alpha `int((aura_r - ar) * 8 * pulse)` capped at 255;
##   ENRAGE AURA    two-pixel outline rings while `is_enraged`,
##                  radius `radius + int(14 * pulse)`, ring
##                  `range(aura_r, max(5, aura_r - 18), -3)`,
##                  alpha `int((aura_r - r) * 12 * pulse)` capped at 200, colour
##                  `(255, 50, 40)` for a true boss else `(255, 140, 30)`;
##   TRUE AURA      filled rings for `boss_class == "true"` only, radius `radius + 15`,
##                  ring `range(aura_r, aura_r - 15, -2)`,
##                  alpha `int((aura_r - r) * 5 * pulse)` capped at 255 in the boss colour.
## Each one allocates its own surface and blits it so the surface centre lands on the anchor,
## which is why every op below is already in screen space around the int `(x, y)`.
##
## The source keeps these surfaces in `_BOSS_AURA_CACHE` (keyed on radius bucket + a quantised
## `_aura_phase`). The cache is a pure optimisation - the pixels are identical because alpha and
## geometry only depend on the radius, not on the bucket - so the builder emits the ops directly
## and lets the view redraw them.
##
## Pulse clocks are the source's own: `sin(anim_time * 0.2) * 0.3 + 0.7` for the ability aura,
## `sin(enrage_pulse) * 0.3 + 0.7` for the enrage aura (enrage_pulse is a ticking counter, not
## an angle) and `sin(pulse) * 0.3 + 0.7` for the true-boss aura.

## Source colours for the enrage ring: red for a true boss, amber for everything else.
const ENRAGE_TRUE := [255, 50, 40]
const ENRAGE_NORMAL := [255, 140, 30]
## The innermost enrage ring never shrinks below this radius (`max(5, aura_r - 18)`).
const ENRAGE_MIN_RADIUS := 5


## ABILITY AURA. `entrance_rgb` is the boss `entrance_color` as three 0..255 channels.
static func ability_aura_ops(
	x: int, y: int, ability_range: float, anim_time: int, entrance_rgb: Array
) -> Array:
	var pulse := sin(float(anim_time) * 0.2) * 0.3 + 0.7
	var aura_radius := int(ability_range * pulse)
	var out: Array = []
	for radius in range(aura_radius, aura_radius - 20, -3):
		# The source would be handed a negative radius here; that never happens for a real
		# ability_range, and Godot's draw_circle needs a positive one.
		if radius <= 0:
			continue
		var alpha := clampi(int(float(aura_radius - radius) * 8.0 * pulse), 0, 255)
		if alpha > 0:
			out.append(_circle([x, y], radius, entrance_rgb, alpha, 0))
	return out


## ENRAGE / FRENZY AURA. `enrage_pulse` is `boss.enrage_pulse` (a ticking counter).
static func enrage_aura_ops(
	x: int, y: int, radius: int, enrage_pulse: float, is_true: bool
) -> Array:
	var pulse := sin(enrage_pulse) * 0.3 + 0.7
	var aura_radius := radius + int(14.0 * pulse)
	var color: Array = ENRAGE_TRUE if is_true else ENRAGE_NORMAL
	var out: Array = []
	for offset in range(aura_radius, maxi(ENRAGE_MIN_RADIUS, aura_radius - 18), -3):
		var alpha := clampi(int(float(aura_radius - offset) * 12.0 * pulse), 0, 200)
		if alpha > 0:
			out.append(_circle([x, y], offset, color, alpha, 2))
	return out


## TRUE BOSS AURA. Only painted when `boss_class == "true"`; `rgb` is the boss body colour.
static func true_boss_aura_ops(x: int, y: int, radius: int, phase: float, rgb: Array) -> Array:
	var pulse := sin(phase) * 0.3 + 0.7
	var aura_radius := radius + 15
	var out: Array = []
	for offset in range(aura_radius, aura_radius - 15, -2):
		var alpha := clampi(int(float(aura_radius - offset) * 5.0 * pulse), 0, 255)
		if alpha > 0:
			out.append(_circle([x, y], offset, rgb, alpha, 0))
	return out


## `Color` -> three 0..255 channels, the shape the recorded ops carry.
static func rgb8(color: Color) -> Array:
	return [int(round(color.r * 255.0)), int(round(color.g * 255.0)), int(round(color.b * 255.0))]


static func _circle(center: Array, radius: int, rgb: Array, alpha: int, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"width": width,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], alpha],
	}
