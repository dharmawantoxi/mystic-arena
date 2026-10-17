extends RefCounted
## Port of `lighting.py` (layer 9aq): the source's per-sprite lighting pass.
##
## The source derives everything from the sprite alpha mask with the light
## coming from the top-left (`LIGHT_DIR = (-1, -1)`):
##   * directional gradient over the sprite box (`_canonical`: RGB multiply
##     GRAD_DARK..GRAD_LIGHT plus a specular ADD of GRAD_SHEEN * t^2.2),
##   * rim light: contour pixels facing the light, RGB-ADD `RIM_ADD`,
##   * terminator: contour pixels facing away, RGB-MULT `SHADE_MUL`, with a
##     second 1 px band at `BAND2_RATIO` strength,
##   * sprites under 24 solid pixels are left untouched (`contour_masks`).
##
## godot_rebuild draws vectors, so this module keeps the MASK MATH exact
## (`rim_shade_cells`, `canonical_table` - pinned cell-for-cell against the
## oracle fixture) and adds a vector adapter the prototype view uses:
## per-vertex gradient colours (`lit_color`) and per-edge rim / terminator
## classification by outward normal (`classify_edges`). Procedural rendering
## stays asset-free - this is shading, not art.

## Light direction (x, y) in pixels; (-1, -1) = top-left.
const LIGHT_DIR := Vector2i(-1, -1)
const RIM_ADD := Vector3i(30, 26, 44)
const SHADE_MUL := 168
const BAND2_RATIO := 0.42
const MASK_ALPHA := 170
const GRADIENT_ENABLED := true
const GRAD_DARK := 205
const GRAD_LIGHT := 255
const GRAD_SHEEN := 22
const GRAD_STEPS := 28
## `contour_masks`: `solid.count() < 24` -> sprite too small, no lighting.
const MIN_SOLID := 24


## Source `_canonical`: t = 1 at the light corner, 0 at the shadow corner.
static func gradient_t(gx: int, gy: int, steps: int = GRAD_STEPS) -> float:
	var ax := absi(LIGHT_DIR.x)
	var ay := absi(LIGHT_DIR.y)
	var span := float((steps - 1) * (ax + ay))
	var t := 1.0 - float(gx * ax + gy * ay) / maxf(1.0, span)
	return clampf(t, 0.0, 1.0)


## Multiply value for a gradient position (0..255, source rounds half-up).
static func gradient_mul(t: float, dark: int = GRAD_DARK, light: int = GRAD_LIGHT) -> int:
	return int(round(float(dark) + float(light - dark) * t))


## Specular ADD (r, g, b) for a gradient position; blue runs 1.25x.
static func gradient_add(t: float, sheen: int = GRAD_SHEEN) -> Vector3i:
	var k := int(round(float(sheen) * pow(t, 2.2)))
	return Vector3i(k, k, int(float(k) * 1.25))


## The full canonical grid, row-major (gy outer, gx inner) like the fixture.
static func canonical_table(
	dark: int = GRAD_DARK, light: int = GRAD_LIGHT, sheen: int = GRAD_SHEEN
) -> Dictionary:
	var mul := PackedInt32Array()
	var add: Array = []
	for gy in range(GRAD_STEPS):
		for gx in range(GRAD_STEPS):
			var t := gradient_t(gx, gy)
			mul.append(gradient_mul(t, dark, light))
			var k := gradient_add(t, sheen)
			add.append([k.x, k.y, k.z])
	return {"mul": mul, "add": add}


## Second terminator band multiplier: 255 - (255 - SHADE_MUL) * BAND2_RATIO.
static func band2_mul(shade_mul: int = SHADE_MUL) -> int:
	var neutral := clampi(shade_mul, 0, 255)
	return clampi(int(255.0 - (255.0 - float(neutral)) * BAND2_RATIO), 0, 255)


## Exact mask math of `contour_masks`: cells is a Dictionary keyed by
## Vector2i. rim = cells - shift(cells, +s); shade = cells - shift(cells, -s).
static func rim_shade_cells(cells: Dictionary, width: int = 1) -> Dictionary:
	if cells.size() < MIN_SOLID:
		return {"rim": [], "shade": [], "rejected": true}
	var shift := Vector2i(absi(LIGHT_DIR.x) * width, absi(LIGHT_DIR.y) * width)
	var rim: Array = []
	var shade: Array = []
	for cell in cells:
		if not cells.has(cell - shift):
			rim.append(cell)
		if not cells.has(cell + shift):
			shade.append(cell)
	rim.sort()
	shade.sort()
	return {"rim": rim, "shade": shade, "rejected": false}


## Source `apply` two-band terminator: the width-2 shade minus the width-1 shade.
static func band2_cells(cells: Dictionary) -> Array:
	var deep := rim_shade_cells(cells, 1)
	var inner := rim_shade_cells(cells, 2)
	if bool(deep["rejected"]):
		return []
	var out: Array = []
	for cell in inner["shade"]:
		if not deep["shade"].has(cell):
			out.append(cell)
	out.sort()
	return out


## Vector adapter -----------------------------------------------------------


## Continuous gradient position of a point inside its reference box (the
## source smoothscales the canonical grid over the box).
static func point_t(point: Vector2, box: Rect2) -> float:
	var ax := float(absi(LIGHT_DIR.x))
	var ay := float(absi(LIGHT_DIR.y))
	var fx := clampf((point.x - box.position.x) / maxf(1.0, box.size.x), 0.0, 1.0)
	var fy := clampf((point.y - box.position.y) / maxf(1.0, box.size.y), 0.0, 1.0)
	return clampf(1.0 - (fx * ax + fy * ay) / maxf(1.0, ax + ay), 0.0, 1.0)


## RGB multiply + specular add of the gradient at `t`; alpha is untouched.
static func lit_color(base: Color, t: float) -> Color:
	if not GRADIENT_ENABLED:
		return base
	var mul := float(gradient_mul(t)) / 255.0
	var add := gradient_add(t)
	return Color(
		clampf(base.r * mul + float(add.x) / 255.0, 0.0, 1.0),
		clampf(base.g * mul + float(add.y) / 255.0, 0.0, 1.0),
		clampf(base.b * mul + float(add.z) / 255.0, 0.0, 1.0),
		base.a
	)


## Rim light: RGB-ADD `RIM_ADD`.
static func rim_color(base: Color) -> Color:
	return Color(
		clampf(base.r + float(RIM_ADD.x) / 255.0, 0.0, 1.0),
		clampf(base.g + float(RIM_ADD.y) / 255.0, 0.0, 1.0),
		clampf(base.b + float(RIM_ADD.z) / 255.0, 0.0, 1.0),
		base.a
	)


## Terminator: RGB-MULT `SHADE_MUL` (band 1) or `band2_mul()` (band 2).
static func shade_color(base: Color, second_band: bool = false) -> Color:
	var mul := float(band2_mul() if second_band else SHADE_MUL) / 255.0
	return Color(base.r * mul, base.g * mul, base.b * mul, base.a)


static func polygon_area(points: PackedVector2Array) -> float:
	var twice := 0.0
	for index in range(points.size()):
		var a := points[index]
		var b := points[(index + 1) % points.size()]
		twice += a.x * b.y - b.x * a.y
	return absf(twice) * 0.5


## Vector mirror of the 24-solid-pixel floor: polygons covering less area
## than 24 px (or degenerate ones) are drawn flat, like the source sprite.
static func should_light(points: PackedVector2Array) -> bool:
	return points.size() >= 3 and polygon_area(points) >= float(MIN_SOLID)


## Per-edge classification by outward normal: edges whose outward normal
## points toward the light (dot with -LIGHT_DIR > 0) are rim edges, edges
## facing away are shade edges. Returns {"rim": [i...], "shade": [i...]}
## where i is the index of the edge starting at points[i].
static func classify_edges(points: PackedVector2Array) -> Dictionary:
	var rim: Array = []
	var shade: Array = []
	if points.size() < 3:
		return {"rim": rim, "shade": shade}
	var signed := 0.0
	for index in range(points.size()):
		var a := points[index]
		var b := points[(index + 1) % points.size()]
		signed += a.x * b.y - b.x * a.y
	# LIGHT_DIR is where the light COMES FROM (top-left), so it already points
	# from the body toward the light.
	var toward_light := Vector2(LIGHT_DIR)
	for index in range(points.size()):
		var a := points[index]
		var b := points[(index + 1) % points.size()]
		var edge := b - a
		if edge.length_squared() <= 0.0:
			continue
		# Outward normal for the polygon's actual winding (screen y down: positive
		# shoelace area = visually clockwise, outward = (dy, -dx)).
		var normal := Vector2(edge.y, -edge.x) if signed > 0.0 else Vector2(-edge.y, edge.x)
		var facing := normal.normalized().dot(toward_light.normalized())
		if facing > 0.0001:
			rim.append(index)
		elif facing < -0.0001:
			shade.append(index)
	return {"rim": rim, "shade": shade}


## Inward unit normal of edge i, used to offset the second terminator band.
static func inward_normal(points: PackedVector2Array, index: int) -> Vector2:
	var signed := 0.0
	for cursor in range(points.size()):
		var a := points[cursor]
		var b := points[(cursor + 1) % points.size()]
		signed += a.x * b.y - b.x * a.y
	var a := points[index]
	var b := points[(index + 1) % points.size()]
	var edge := b - a
	if edge.length_squared() <= 0.0:
		return Vector2.ZERO
	var outward := Vector2(edge.y, -edge.x) if signed > 0.0 else Vector2(-edge.y, edge.x)
	return -outward.normalized()


## Per-vertex colours for `CanvasItem.draw_polygon`.
static func vertex_colors(points: PackedVector2Array, base: Color, box: Rect2) -> PackedColorArray:
	var colors := PackedColorArray()
	for point in points:
		colors.append(lit_color(base, point_t(point, box)))
	return colors


## Regular polygon approximation so circles (boss bodies) share the pass.
static func circle_points(center: Vector2, radius: float, segments: int = 32) -> PackedVector2Array:
	var points := PackedVector2Array()
	for index in range(segments):
		var angle := TAU * float(index) / float(segments)
		points.append(center + Vector2(cos(angle), sin(angle)) * radius)
	return points
