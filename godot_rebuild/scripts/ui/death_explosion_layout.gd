extends RefCounted
## Layer 9bg: the DRAW of `_render.py::DeathExplosion.draw()` as a pure op list.
##
## `ops()` replays the method against the ported state (`death_explosion.gd`
## already holds the flash timer and the sparks): the central flash, then every
## spark through `hit_particle_layout.gd`, in source order:
##   circle {center, radius, color, mult, width}.
## The flash is two discs on one SRCALPHA surface drawn WITHOUT blending, so the
## inner `size // 2` white disc overwrites the middle of the outer
## `(255, 255, 200)` disc; both sit on `int(x), int(y)`. `ring_inner` (a painter
## hint, not pinned) turns the outer disc into the annulus that remains.
## `death_explosion_draw_source_oracle.py` pins every op.

const HitParticleLayout = preload("res://scripts/ui/hit_particle_layout.gd")

const FLASH_RGB := [255, 255, 200]
const FLASH_PEAK_ALPHA := 200.0
const CORE_PEAK_ALPHA := 255.0


## Ops of one frame for a `death_explosion.gd` port.
static func ops(explosion) -> Array:
	var result: Array = []
	var flash: Dictionary = explosion.get_flash_state()
	var size: int = int(flash["size"])
	if int(flash["timer"]) > 0 and size > 0:
		var intensity: float = float(flash["intensity"])
		var at: Array = [int(explosion.x), int(explosion.y)]
		var core: int = int(floor(float(size) / 2.0))
		(
			result
			. append(
				{
					"kind": "circle",
					"center": at,
					"radius": size,
					"color":
					[FLASH_RGB[0], FLASH_RGB[1], FLASH_RGB[2], int(FLASH_PEAK_ALPHA * intensity)],
					"mult": 255,
					"width": 0,
					"ring_inner": core,
				}
			)
		)
		(
			result
			. append(
				{
					"kind": "circle",
					"center": at,
					"radius": core,
					"color": [255, 255, 255, int(CORE_PEAK_ALPHA * intensity)],
					"mult": 255,
					"width": 0,
				}
			)
		)
	for particle in explosion.particles:
		result.append_array(HitParticleLayout.ops(particle))
	return result
