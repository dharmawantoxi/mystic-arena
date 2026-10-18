extends RefCounted
## Layer 9bf: the DRAW of `_render.py::BossDeathAnimation._draw_death_sequence()`
## as a pure op list.
##
## `ops()` replays the method against the ported state (`boss_death_animation.gd`
## already holds the flash, wave and dissolve values, the fragments and the
## rising particles) and returns dictionaries in source order: the additive white
## flash, each explosion wave (rings + core), the two-tone body, the rotated
## square fragments with their edge and the glowing rising particles:
##   flash {alpha, mult}; circle {center, radius, color, mult, width};
##   polygon {points, color, mult, width}.
## `color` is RGBA 0..255 and `mult` the pygame surface alpha (255 = opaque).
## pygame draws onto the temp SRCALPHA surfaces WITHOUT blending, so later discs
## overwrite earlier ones. The layout keeps every source call and adds two hints
## for the painter (not part of the pinned keys): `covered` marks a ring or disc
## that a later disc hides completely, and `ring_inner` turns a disc into the
## annulus the overwrite leaves behind.
## `boss_death_sequence_draw_source_oracle.py` pins every op.

const WAVE_CORE_INSET := 15
const WAVE_RING_STEP := 3
const WAVE_RING_SPAN := 20
const FRAGMENT_MIN_ALPHA := 10
const RISING_MIN_ALPHA := 10
const RISING_PEAK_ALPHA := 200.0
const RING_WIDTH := 3

var _ops: Array = []


## One frame of `draw()`'s death phase for a `BossDeathAnimation` port.
static func ops(anim) -> Array:
	var layout := new()
	layout._draw(anim)
	return layout._ops


func _draw(anim) -> void:
	if not anim.active:
		return
	var visual: Dictionary = anim.get_death_visual_state()
	var flash: int = int(visual["flash_alpha"])
	if flash > 0:
		_ops.append({"kind": "flash", "alpha": mini(flash, 255), "mult": 255})
	var at: Array = [int(anim.boss_x), int(anim.boss_y)]
	for wave in visual["waves"]:
		_wave(at, wave)
	if bool(visual["body_visible"]):
		_body(anim, at, int(visual["dissolve_size"]), int(visual["dissolve_alpha"]))
	for fragment in anim.fragments:
		_fragment(anim, fragment)
	for particle in anim.rising_particles:
		_rising(particle)


## Rings from `radius` inwards in steps of 3, then the half-alpha core. The temp
## surface is 4 px larger than the radius, so the whole wave sits 2 px off.
func _wave(at: Array, wave: Dictionary) -> void:
	var radius: int = int(wave["radius"])
	var alpha: int = int(wave["alpha"])
	var rgb: Array = wave["color"]
	var center: Array = [int(at[0]) + 2, int(at[1]) + 2]
	var core: int = maxi(1, radius - WAVE_CORE_INSET)
	for ring in range(radius, maxi(0, radius - WAVE_RING_SPAN), -WAVE_RING_STEP):
		var ring_alpha: int = int(float(alpha) * (float(ring) / float(radius)))
		var op := _circle(center, ring, _rgba(rgb, ring_alpha), RING_WIDTH)
		op["covered"] = ring <= core
	_circle(center, core, _rgba(rgb, _div(alpha, 2)), 0)


## Boss colour disc with the entrance-colour core drawn over its middle.
func _body(anim, at: Array, size: int, alpha: int) -> void:
	var outer := _circle(at, size, _rgba(anim.boss_color, alpha), 0)
	outer["ring_inner"] = _div(size, 2)
	_circle(at, _div(size, 2), _rgba(anim.entrance_color, _div(alpha, 2)), 0)


func _fragment(anim, fragment: Dictionary) -> void:
	var life: int = int(fragment["life"])
	if life <= 0:
		return
	var alpha: int = int(255.0 * (float(life) / float(fragment["max_life"])))
	if alpha < FRAGMENT_MIN_ALPHA:
		return
	var size: int = int(fragment["size"])
	var half: int = _div(size * 3, 2)
	var shift: int = int(fragment["x"]) - half
	var lift: int = int(fragment["y"]) - half
	var cos_r: float = cos(float(fragment["rotation"]))
	var sin_r: float = sin(float(fragment["rotation"]))
	var corners := [[-size, -size], [size, -size], [size, size], [-size, size]]
	var points: Array = []
	for corner in corners:
		var rx: float = float(corner[0]) * cos_r - float(corner[1]) * sin_r
		var ry: float = float(corner[0]) * sin_r + float(corner[1]) * cos_r
		points.append([float(half) + rx + float(shift), float(half) + ry + float(lift)])
	_polygon(points, _rgba(fragment["color"], alpha), 0)
	_polygon(points, _rgba(anim.entrance_color, alpha), 1)


## Radial glow (discs from `size + 2` down to 1, each overwriting the last) plus
## a white 1 px core.
func _rising(particle: Dictionary) -> void:
	var life: int = int(particle["life"])
	if life <= 0:
		return
	var alpha: int = int(RISING_PEAK_ALPHA * (float(life) / float(particle["max_life"])))
	if alpha < RISING_MIN_ALPHA:
		return
	var size: int = int(particle["size"])
	var at: Array = [int(particle["x"]), int(particle["y"])]
	for ring in range(size + 2, 0, -1):
		var glow: int = int(float(alpha) * (1.0 - float(ring) / float(size + 2)))
		var op := _circle(at, ring, _rgba(particle["color"], glow), 0)
		op["ring_inner"] = ring - 1
		op["covered"] = ring == 1
	_circle(at, 1, _rgba([255, 255, 255], alpha), 0)


# ── op helpers ─────────────────────────────────────────────────────────────
## Python `//` (floor division) without the integer-division warning.
static func _div(value: int, divisor: int) -> int:
	return int(floor(float(value) / float(divisor)))


static func _rgba(rgb: Array, alpha: int) -> Array:
	return [int(rgb[0]), int(rgb[1]), int(rgb[2]), alpha]


func _circle(center: Array, radius: int, color: Array, width: int) -> Dictionary:
	var op := {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"color": color,
		"mult": 255,
		"width": width,
	}
	_ops.append(op)
	return op


func _polygon(points: Array, color: Array, width: int) -> void:
	_ops.append({"kind": "polygon", "points": points, "color": color, "mult": 255, "width": width})
