extends RefCounted
## Layer 9ci: port of `_system.py::FrustumCuller` (line 40).
##
## pygame skips an entity whose centre is farther than `MARGIN + radius` outside the
## fixed 1280x720 logical surface — a draw-side optimisation, not a gameplay rule:
## nothing is culled from the simulation, and a culled entity is off-screen anyway.
##
## The rebuild hands that culling to Godot's canvas culling (`CanvasItem` visibility is
## resolved by the render server), so this helper is the source rule kept executable and
## tested rather than a hot path; the report's deviation D1 records that mapping. It
## exists so a future view can call the exact source predicate instead of a paraphrase
## of the 80 px margin.

## `FrustumCuller.MARGIN`.
const MARGIN := 80
## `SCREEN_WIDTH` / `SCREEN_HEIGHT` from the `_core.py` settings block, kept as one
## vector so the constant names cannot shadow the settings drift guard.
const SCREEN_SIZE := Vector2(1280.0, 720.0)


## `FrustumCuller.is_visible(x, y, radius=30)`: inclusive on both edges.
static func is_visible(x: float, y: float, radius: float = 30.0) -> bool:
	var margin := float(MARGIN) + radius
	return (
		-margin <= x
		and x <= SCREEN_SIZE.x + margin
		and -margin <= y
		and y <= SCREEN_SIZE.y + margin
	)


## The margin the source adds to the entity radius (exposed for the checks).
static func cull_margin(radius: float) -> float:
	return float(MARGIN) + radius
