extends RefCounted
## Layer 9bg: the DRAW of `_render.py::HitParticle.draw()` as a pure op list.
##
## The source blits a pre-rendered sprite: a colour disc of radius `base` with a
## white core of `max(1, base // 2)` that OVERWRITES its middle (pygame does not
## blend on SRCALPHA surfaces). The sprite is scaled to `max(1, int(size * life
## ratio))` and blitted at `int(x), int(y)` with surface alpha `int(255 * ratio)`.
## `ops()` returns the two circles in source order:
##   circle {center, radius, color, mult, width}.
## `color` is RGBA 0..255 and `mult` the pygame surface alpha (255 = opaque).
## Painter hints (not pinned): `ring_inner` turns the colour disc into the annulus
## the white core leaves behind, and `covered` marks a disc the core hides entirely.
## `death_explosion_draw_source_oracle.py` pins every op.


## Ops of one frame for a `hit_particle.gd` port; empty for a dead spark.
static func ops(particle) -> Array:
	if not particle.alive:
		return []
	var ratio: float = float(particle.lifetime) / float(particle.max_lifetime)
	var alpha: int = int(255.0 * ratio)
	var scaled: int = maxi(1, int(float(particle.size) * ratio))
	if alpha <= 0 or scaled <= 0:
		return []
	var base: int = maxi(1, int(particle.size))
	var core: int = maxi(1, _div(base, 2))
	var factor: float = float(scaled * 3) / float(base * 3)
	var half: int = _div(base * 3, 2)
	var center: Array = [
		float(half) * factor + float(int(particle.x) - _div(scaled * 3, 2)),
		float(half) * factor + float(int(particle.y) - _div(scaled * 3, 2)),
	]
	var rgb: Color = particle.color
	var outer_radius: float = float(base) * factor
	var core_radius: float = float(core) * factor
	return [
		{
			"kind": "circle",
			"center": center,
			"radius": outer_radius,
			"color": [rgb.r8, rgb.g8, rgb.b8, 255],
			"mult": alpha,
			"width": 0,
			"ring_inner": core_radius,
			"covered": core >= base,
		},
		{
			"kind": "circle",
			"center": center,
			"radius": core_radius,
			"color": [255, 255, 255, 255],
			"mult": alpha,
			"width": 0,
		},
	]


## Python `//` (floor division) without the integer-division warning.
static func _div(value: int, divisor: int) -> int:
	return int(floor(float(value) / float(divisor)))
