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
## `apply` / `contour_masks`: a sprite 2 px wide or tall is never lit.
const MIN_SIZE := 2
## Source `_SIZE_CACHE` is bounded: it clears once it grows past 64 sizes.
const SIZE_CACHE_LIMIT := 64

## Source `_CANON_CACHE` / `_SIZE_CACHE`. The canonical grid is cheap to
## rebuild, so only the resampled boxes are memoised (see D1).
static var _size_cache: Dictionary = {}


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


## Bitmap pipeline (source `_sized` / `contour_masks` / `apply` / `_bbox_of`)


## Source `_sized`: the canonical grid resampled to the box size. The port
## samples the 28x28 grid bilinearly (exact identity at 28x28) instead of
## pygame `smoothscale` - see D2 in the migration report.
static func sized_grid(
	w: int,
	h: int,
	dark: int = GRAD_DARK,
	light: int = GRAD_LIGHT,
	sheen: int = GRAD_SHEEN
) -> Dictionary:
	var key := "%d:%d:%d:%d:%d" % [w, h, dark, light, sheen]
	if _size_cache.has(key):
		return _size_cache[key]
	if _size_cache.size() > SIZE_CACHE_LIMIT:
		_size_cache.clear()
	var grid := canonical_table(dark, light, sheen)
	var mul_src: PackedInt32Array = grid["mul"]
	var add_src: Array = grid["add"]
	var mul := PackedInt32Array()
	var add: Array = []
	mul.resize(w * h)
	for y in range(h):
		var row := _axis(y, h)
		var y0 := int(row.x)
		var y1 := int(row.y)
		var fy := row.z
		for x in range(w):
			var col := _axis(x, w)
			var x0 := int(col.x)
			var x1 := int(col.y)
			var fx := col.z
			var idx00: int = y0 * GRAD_STEPS + x0
			var idx01: int = y0 * GRAD_STEPS + x1
			var idx10: int = y1 * GRAD_STEPS + x0
			var idx11: int = y1 * GRAD_STEPS + x1
			var top := lerpf(float(mul_src[idx00]), float(mul_src[idx01]), fx)
			var bottom := lerpf(float(mul_src[idx10]), float(mul_src[idx11]), fx)
			mul[y * w + x] = int(roundf(lerpf(top, bottom, fy)))
			var rgb := [0, 0, 0]
			for channel in range(3):
				var a00 := float((add_src[idx00] as Array)[channel])
				var a01 := float((add_src[idx01] as Array)[channel])
				var a10 := float((add_src[idx10] as Array)[channel])
				var a11 := float((add_src[idx11] as Array)[channel])
				rgb[channel] = int(
					roundf(lerpf(lerpf(a00, a01, fx), lerpf(a10, a11, fx), fy))
				)
			add.append(rgb)
	var result := {"mul": mul, "add": add}
	_size_cache[key] = result
	return result


## Browser of the canonical axis: (index0, index1, fraction).
static func _axis(index: int, size: int) -> Vector3:
	var src := (float(index) + 0.5) * float(GRAD_STEPS) / float(size) - 0.5
	var low := int(floorf(src))
	var a := clampi(low, 0, GRAD_STEPS - 1)
	var b := clampi(low + 1, 0, GRAD_STEPS - 1)
	return Vector3(float(a), float(b), src - float(low))


## Source `reset_gradient_cache`: drop the resampled grids.
static func reset_gradient_cache() -> void:
	_size_cache.clear()


## Source `pygame.mask.from_surface(surface, alpha)`: alpha above the
## threshold joins the mask.
static func mask_cells(image: Image, alpha: int = MASK_ALPHA) -> Dictionary:
	var cells := {}
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			if image.get_pixel(x, y).a8 > alpha:
				cells[Vector2i(x, y)] = true
	return cells


## Source `contour_masks`: rim / shade / second band of an alpha mask, with
## the size and 24-solid-pixel guards of the source.
static func contour_masks(image: Image, alpha: int = MASK_ALPHA) -> Dictionary:
	if image.get_width() <= MIN_SIZE or image.get_height() <= MIN_SIZE:
		return {"rim": [], "shade": [], "band2": [], "rejected": true}
	var cells := mask_cells(image, alpha)
	if cells.size() < MIN_SOLID:
		return {"rim": [], "shade": [], "band2": [], "rejected": true}
	var deep := rim_shade_cells(cells, 1)
	var wide := rim_shade_cells(cells, 2)
	var second: Array = []
	for cell in wide["shade"]:
		if not (deep["shade"] as Array).has(cell):
			second.append(cell)
	return {
		"rim": deep["rim"],
		"shade": deep["shade"],
		"band2": second,
		"rejected": false,
	}


## Source `_bbox_of`: bounding box of the solid pixels, empty rect when none.
static func bbox_of(image: Image, alpha: int = MASK_ALPHA) -> Rect2i:
	var cells := mask_cells(image, alpha)
	if cells.is_empty():
		return Rect2i()
	var min_x := 1 << 30
	var min_y := 1 << 30
	var max_x := -1
	var max_y := -1
	for cell in cells:
		min_x = mini(min_x, cell.x)
		min_y = mini(min_y, cell.y)
		max_x = maxi(max_x, cell.x)
		max_y = maxi(max_y, cell.y)
	return Rect2i(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)


## Source `apply`: directional gradient over the reference box, two-band
## terminator on the shadow contour, rim light on the light contour. Only RGB
## is touched (`BLEND_RGB_*`); alpha survives untouched, like the source.
static func apply(
	image: Image,
	rim_add: Vector3i = RIM_ADD,
	shade_mul: int = SHADE_MUL,
	two_band: bool = true,
	alpha: int = MASK_ALPHA,
	gradient: bool = GRADIENT_ENABLED,
	box: Rect2i = Rect2i()
) -> Image:
	if image.get_format() != Image.FORMAT_RGBA8:
		image.convert(Image.FORMAT_RGBA8)
	var w := image.get_width()
	var h := image.get_height()
	if w <= MIN_SIZE or h <= MIN_SIZE:
		return image
	var masks := contour_masks(image, alpha)
	if bool(masks["rejected"]):
		return image
	var data := image.get_data()
	if gradient:
		var bx := 0
		var by := 0
		var bw := w
		var bh := h
		if box.size.x > 0 and box.size.y > 0:
			bx = clampi(box.position.x, 0, w)
			by = clampi(box.position.y, 0, h)
			bw = mini(box.size.x, w - bx)
			bh = mini(box.size.y, h - by)
		bw = maxi(2, bw)
		bh = maxi(2, bh)
		if bw > 2 and bh > 2:
			var grid := sized_grid(bw, bh)
			var mul: PackedInt32Array = grid["mul"]
			var add: Array = grid["add"]
			for gy in range(bh):
				for gx in range(bw):
					var index := gy * bw + gx
					var base := ((by + gy) * w + (bx + gx)) * 4
					var factor: int = mul[index]
					var extra: Array = add[index]
					for channel in range(3):
						var value: int = data[base + channel] * factor / 255
						data[base + channel] = clampi(value + int(extra[channel]), 0, 255)
	var neutral := clampi(shade_mul, 0, 255)
	var second := band2_mul(neutral)
	for cell in masks["shade"]:
		var index := (int(cell.y) * w + int(cell.x)) * 4
		for channel in range(3):
			data[index + channel] = int(data[index + channel]) * neutral / 255
	if two_band:
		for cell in masks["band2"]:
			var index := (int(cell.y) * w + int(cell.x)) * 4
			for channel in range(3):
				data[index + channel] = int(data[index + channel]) * second / 255
	var rim := [rim_add.x, rim_add.y, rim_add.z]
	for cell in masks["rim"]:
		var index := (int(cell.y) * w + int(cell.x)) * 4
		for channel in range(3):
			data[index + channel] = clampi(
				int(data[index + channel]) + int(rim[channel]), 0, 255
			)
	image.set_data(w, h, false, Image.FORMAT_RGBA8, data)
	return image


## Source `apply_to_rig`: never lets the pass fail a render.
static func apply_to_rig(
	image: Image,
	enabled: bool = true,
	rim_add: Vector3i = RIM_ADD,
	shade_mul: int = SHADE_MUL
) -> Image:
	if not enabled:
		return image
	return apply(image, rim_add, shade_mul)
