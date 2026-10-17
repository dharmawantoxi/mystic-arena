extends RefCounted
## Layer 9aq: replays the `lighting.py` source oracle fixture through the
## native port. `sprite_lighting_source_oracle.py` runs the REAL source
## functions (`_canonical`, `contour_masks`) under a dict/set pygame shim, so
## the gradient grid and the rim / terminator pixel sets are not hand-written.
## The vector adapter is then checked against the same shapes.

const SpriteLighting = preload("res://scripts/ui/sprite_lighting.gd")
const FIXTURE := "res://tests/fixtures/sprite_lighting_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Sprite lighting fixture parses")
	if not (data is Dictionary):
		return
	_constant_checks(data, check)
	_gradient_checks(data, check)
	_mask_checks(data, check)
	_vector_checks(check)


func _constant_checks(data: Dictionary, check: Callable) -> void:
	var dir: Array = data["light_dir"]
	var rim: Array = data["rim_add"]
	check.call(
		SpriteLighting.LIGHT_DIR == Vector2i(int(dir[0]), int(dir[1])),
		"light comes from the source top-left direction"
	)
	check.call(
		SpriteLighting.RIM_ADD == Vector3i(int(rim[0]), int(rim[1]), int(rim[2])),
		"rim add matches the source RIM_ADD"
	)
	check.call(SpriteLighting.SHADE_MUL == int(data["shade_mul"]), "SHADE_MUL matches the source")
	check.call(
		is_equal_approx(SpriteLighting.BAND2_RATIO, float(data["band2_ratio"])),
		"BAND2_RATIO matches the source"
	)
	check.call(
		SpriteLighting.band2_mul() == int(data["band2_mul"]),
		"the second terminator band multiplier is the source 218"
	)
	check.call(
		SpriteLighting.MASK_ALPHA == int(data["mask_alpha"]), "MASK_ALPHA matches the source"
	)
	check.call(
		SpriteLighting.GRADIENT_ENABLED == bool(data["gradient_enabled"]),
		"GRADIENT_ENABLED matches the source"
	)
	check.call(
		(
			SpriteLighting.GRAD_DARK == int(data["grad_dark"])
			and SpriteLighting.GRAD_LIGHT == int(data["grad_light"])
			and SpriteLighting.GRAD_SHEEN == int(data["grad_sheen"])
			and SpriteLighting.GRAD_STEPS == int(data["grad_steps"])
		),
		"gradient dark/light/sheen/steps match the source"
	)
	check.call(SpriteLighting.MIN_SOLID == int(data["min_solid"]), "the 24-solid floor matches")


func _gradient_checks(data: Dictionary, check: Callable) -> void:
	var table := SpriteLighting.canonical_table()
	var mul: PackedInt32Array = table["mul"]
	var add: Array = table["add"]
	var want_mul: Array = data["canonical_mul"]
	var want_add: Array = data["canonical_add"]
	check.call(
		mul.size() == want_mul.size() and add.size() == want_add.size() and mul.size() == 784,
		"the canonical grid is 28x28 like the source"
	)
	var mismatches := 0
	for index in range(mini(mul.size(), want_mul.size())):
		if mul[index] != int(want_mul[index]):
			mismatches += 1
		var got: Array = add[index]
		var want: Array = want_add[index]
		if (
			int(got[0]) != int(want[0])
			or int(got[1]) != int(want[1])
			or int(got[2]) != int(want[2])
		):
			mismatches += 1
	check.call(mismatches == 0, "every canonical multiply/add cell matches the source grid")
	check.call(
		mul[0] == SpriteLighting.GRAD_LIGHT and mul[783] == SpriteLighting.GRAD_DARK,
		"the light corner is GRAD_LIGHT and the shadow corner is GRAD_DARK"
	)
	check.call(
		(
			is_equal_approx(SpriteLighting.gradient_t(0, 0), 1.0)
			and is_equal_approx(SpriteLighting.gradient_t(27, 27), 0.0)
			and is_equal_approx(SpriteLighting.gradient_t(27, 0), 0.5)
		),
		"gradient t runs 1 -> 0 along the light axis"
	)


func _cells(entries: Array) -> Dictionary:
	var out := {}
	for entry in entries:
		out[Vector2i(int(entry[0]), int(entry[1]))] = true
	return out


func _same_cells(got: Array, want: Variant) -> bool:
	if want == null:
		return got.is_empty()
	var expected := _cells(want)
	if got.size() != expected.size():
		return false
	for cell in got:
		if not expected.has(cell):
			return false
	return true


func _mask_checks(data: Dictionary, check: Callable) -> void:
	var shapes: Dictionary = data["shapes"]
	for name in ["square", "ell", "tiny"]:
		var shape: Dictionary = shapes[name]
		var cells := _cells(shape["cells"])
		check.call(
			cells.size() == int(shape["solid"]), "%s shape has the fixture solid count" % name
		)
		var contour := SpriteLighting.rim_shade_cells(cells)
		check.call(
			bool(contour["rejected"]) == bool(shape["rejected"]),
			"%s shape rejection matches contour_masks" % name
		)
		check.call(
			_same_cells(contour["rim"], shape["rim"]), "%s rim cells match the source" % name
		)
		check.call(
			_same_cells(contour["shade"], shape["shade"]), "%s shade cells match the source" % name
		)
		var outer := SpriteLighting.rim_shade_cells(cells, 2)
		check.call(
			_same_cells(outer["rim"], shape["outer_rim"]),
			"%s width-2 rim matches the source" % name
		)
		check.call(
			_same_cells(SpriteLighting.band2_cells(cells), shape["band2"]),
			"%s second terminator band matches the source" % name
		)


func _vector_checks(check: Callable) -> void:
	var square := PackedVector2Array(
		[Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
	)
	var edges := SpriteLighting.classify_edges(square)
	check.call(
		Array(edges["rim"]) == [0, 3] and Array(edges["shade"]) == [1, 2],
		"clockwise square: top/left edges face the light, right/bottom are shade"
	)
	var reversed := PackedVector2Array(
		[Vector2(0, 0), Vector2(0, 10), Vector2(10, 10), Vector2(10, 0)]
	)
	var flipped := SpriteLighting.classify_edges(reversed)
	check.call(
		Array(flipped["rim"]) == [0, 3] and Array(flipped["shade"]) == [1, 2],
		"the classification follows outward normals regardless of winding"
	)
	check.call(
		(
			SpriteLighting.inward_normal(square, 0).is_equal_approx(Vector2(0, 1))
			and SpriteLighting.inward_normal(square, 1).is_equal_approx(Vector2(-1, 0))
		),
		"inward normals point into the body"
	)
	check.call(
		(
			SpriteLighting.should_light(square)
			and not SpriteLighting.should_light(
				PackedVector2Array([Vector2(0, 0), Vector2(4, 0), Vector2(4, 5), Vector2(0, 5)])
			)
			and not SpriteLighting.should_light(PackedVector2Array([Vector2(0, 0), Vector2(1, 1)]))
		),
		"bodies under 24 px of area (the source solid floor) stay unlit"
	)
	var box := Rect2(0, 0, 10, 10)
	check.call(
		(
			is_equal_approx(SpriteLighting.point_t(Vector2(0, 0), box), 1.0)
			and is_equal_approx(SpriteLighting.point_t(Vector2(10, 10), box), 0.0)
			and is_equal_approx(SpriteLighting.point_t(Vector2(10, 0), box), 0.5)
		),
		"point_t mirrors the canonical grid over the reference box"
	)
	var base := Color8(100, 100, 100)
	var light := SpriteLighting.lit_color(base, 1.0)
	var dark := SpriteLighting.lit_color(base, 0.0)
	(
		check
		. call(
			(
				absf(light.r8 - 122) <= 1
				and absf(light.b8 - 127) <= 1
				and absf(dark.r8 - 80) <= 1
				and dark.b8 == dark.r8
				and is_equal_approx(light.a, base.a)
			),
			"lit colour at the light corner is base + sheen (22/22/27) and at the shadow corner base*205/255"
		)
	)
	var rim := SpriteLighting.rim_color(base)
	check.call(
		absf(rim.r8 - 130) <= 1 and absf(rim.g8 - 126) <= 1 and absf(rim.b8 - 144) <= 1,
		"rim colour is base + RIM_ADD"
	)
	var shade := SpriteLighting.shade_color(base)
	var band2 := SpriteLighting.shade_color(base, true)
	check.call(
		absf(shade.r8 - 66) <= 1 and absf(band2.r8 - 85) <= 1,
		"terminator bands multiply by 168/255 and 218/255"
	)
	var colors := SpriteLighting.vertex_colors(square, base, box)
	check.call(
		colors.size() == 4 and colors[0].is_equal_approx(light) and colors[2].is_equal_approx(dark),
		"vertex colours follow the gradient over the polygon box"
	)
	var ring := SpriteLighting.circle_points(Vector2(50, 50), 10.0, 32)
	check.call(
		(
			ring.size() == 32
			and ring[0].is_equal_approx(Vector2(60, 50))
			and SpriteLighting.should_light(ring)
		),
		"boss bodies get a 32-gon that enters the lighting pass"
	)
	var view_text := FileAccess.get_file_as_string("res://scenes/prototype/prototype_view.gd")
	check.call(
		(
			view_text.contains("_draw_lit_polygon(HeroMarker.silhouette(")
			and view_text.contains("_draw_lit_polygon(SpriteLighting.circle_points(point, radius)")
		),
		"the arena view routes hero silhouettes and boss bodies through the lighting pass"
	)
