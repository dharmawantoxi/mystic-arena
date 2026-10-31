extends RefCounted
## Layers 9aq + 9cl: replays the `lighting.py` source oracle fixture through the
## native port. `sprite_lighting_source_oracle.py` runs the REAL source
## functions (`_canonical`, `contour_masks`, `_sized`, `apply`, `_bbox_of`)
## under a pygame shim with real `Mask.to_surface` / `blit` blend modes, so the
## gradient grid, the rim / terminator pixel sets and the finished pass are not
## hand-written. 9cl adds the bitmap pipeline replay (`apply`, `bbox_of`,
## `sized_grid`, `reset_gradient_cache`, `apply_to_rig`) and the 21-symbol
## classification of the module.

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
	_inventory_checks(data, check)
	_pipeline_checks(data, check)


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


## Layer 9cl: every symbol of the 239-line module carries a kind and a live
## target + token; only the dropped canonical cache may skip a Godot target.
func _inventory_checks(data: Dictionary, check: Callable) -> void:
	var inventory: Dictionary = data["inventory"]
	var file: Dictionary = inventory["file"]
	check.call(
		(
			String(file["file"]) == "lighting.py"
			and int(file["lines"]) == 239
			and int(file["functions"]) == 8
			and int(file["assigns"]) == 12
			and int(file["imports"]) == 1
			and int(file["symbols"]) == 21
		),
		"lighting.py stays 239 lines with 8 functions, 12 constants and one import"
	)
	check.call(
		(int(inventory["symbols"]["count"]) == 21
			and inventory["symbols"]["kinds"] == {"data": 10, "deviation": 1,
				"folded": 1, "ported": 9}),
		"all 21 symbols carry a kind"
	)
	var broken: Array = []
	var untargeted: Array = []
	for symbol in inventory["classification"]:
		var row: Dictionary = inventory["classification"][symbol]
		var target := String(row["target"])
		var token := String(row["token"])
		if target.is_empty() or token.is_empty():
			if String(row["kind"]) != "deviation" and String(row["kind"]) != "dead":
				untargeted.append(symbol)
			continue
		var local := "res://" + target
		if not FileAccess.file_exists(local):
			broken.append("%s -> %s" % [symbol, target])
		elif not FileAccess.get_file_as_string(local).contains(token):
			broken.append("%s -> %s" % [symbol, target])
	check.call(broken.is_empty(), "every lighting token lives in its target (%s)" % str(broken))
	check.call(
		untargeted.is_empty(),
		"only the dropped canonical cache skips a Godot target (%s)" % str(untargeted)
	)
	check.call(
		Array(inventory["deviations"]) == ["_CANON_CACHE"],
		"the dropped canonical cache stays named as a deviation"
	)


func _image_from(case: Dictionary) -> Image:
	var image := Image.create(
		int(case["width"]), int(case["height"]), false, Image.FORMAT_RGBA8
	)
	var fill := Color8(200, 120, 80, 255)
	for raw in case["cells"]:
		var cell: Array = raw
		image.set_pixel(int(cell[0]), int(cell[1]), fill)
	return image


func _compare_pixels(image: Image, expected: Array) -> int:
	var mismatches := 0
	if expected.size() == 0:
		return 0
	for raw in expected:
		var row: Array = raw
		var color := image.get_pixel(int(row[0]), int(row[1]))
		if (
			int(color.r8) != int(row[2])
			or int(color.g8) != int(row[3])
			or int(color.b8) != int(row[4])
		):
			mismatches += 1
	return mismatches


## The finished `apply()` pass, the guards, `bbox_of` and the grid sampler.
func _pipeline_checks(data: Dictionary, check: Callable) -> void:
	var cases: Dictionary = data["apply"]
	var gradient: Dictionary = cases["gradient28"]
	var wide := _image_from(gradient)
	SpriteLighting.apply(wide)
	check.call(
		_compare_pixels(wide, gradient["output"]) == 0,
		"the 28x28 pass reproduces the source gradient + rim + terminator pixels"
	)
	check.call(
		wide.get_data().size() == int(gradient["width"]) * int(gradient["height"]) * 4,
		"the pass keeps the RGBA buffer size"
	)
	var alpha_kept := true
	for y in range(int(gradient["height"])):
		for x in range(int(gradient["width"])):
			if wide.get_pixel(x, y).a8 != 255:
				alpha_kept = false
	check.call(alpha_kept, "apply only touches RGB (alpha survives)")

	var flat_case: Dictionary = cases["flat12"]
	var flat := _image_from(flat_case)
	SpriteLighting.apply(flat, SpriteLighting.RIM_ADD, SpriteLighting.SHADE_MUL, true,
		SpriteLighting.MASK_ALPHA, false)
	check.call(
		_compare_pixels(flat, flat_case["output"]) == 0,
		"with the gradient off the two-band terminator + rim match the source"
	)

	var boxed_case: Dictionary = cases["box28"]
	var boxed := _image_from(boxed_case)
	var box: Array = boxed_case["box"]
	SpriteLighting.apply(
		boxed,
		SpriteLighting.RIM_ADD,
		SpriteLighting.SHADE_MUL,
		true,
		SpriteLighting.MASK_ALPHA,
		true,
		Rect2i(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
	)
	check.call(
		_compare_pixels(boxed, boxed_case["output"]) == 0,
		"a 28x28 reference box lights only its own corner, like the source `box`"
	)
	check.call(
		boxed.get_pixel(35, 35).is_equal_approx(Color8(200, 120, 80, 255)),
		"pixels outside the reference box keep the base colour"
	)

	for name in ["guard_thin", "guard_empty", "guard_tiny"]:
		var case: Dictionary = cases[name]
		var image := _image_from(case)
		SpriteLighting.apply(image)
		check.call(
			_compare_pixels(image, case["output"]) == 0
			and _compare_pixels(image, case["input"]) == 0,
			"%s stays untouched like the source" % name
		)

	var bbox: Dictionary = data["bbox"]
	var shapes: Dictionary = data["shapes"]
	for name in ["square", "ell", "tiny"]:
		var shape: Dictionary = shapes[name]
		var image := Image.create(
			int(shape["width"]), int(shape["height"]), false, Image.FORMAT_RGBA8
		)
		var fill := Color8(200, 120, 80, 255)
		for raw in shape["cells"]:
			var cell: Array = raw
			image.set_pixel(int(cell[0]), int(cell[1]), fill)
		var measured := SpriteLighting.bbox_of(image)
		var want: Array = bbox[name]
		check.call(
			(
				measured.position == Vector2i(int(want[0]), int(want[1]))
				and measured.size == Vector2i(int(want[2]), int(want[3]))
			),
			"%s solid bbox matches the source _bbox_of" % name
		)
	var blank := Image.create(12, 12, false, Image.FORMAT_RGBA8)
	check.call(
		SpriteLighting.bbox_of(blank) == Rect2i(),
		"a sprite with no solid pixel has no bbox"
	)

	var sized: Dictionary = data["sized_identity"]
	var canonical := SpriteLighting.canonical_table()
	var mul: PackedInt32Array = canonical["mul"]
	var grid_28: PackedInt32Array = SpriteLighting.sized_grid(28, 28)["mul"]
	var identity := true
	for index in range(16):
		if int(grid_28[index]) != int(mul[index]) or int(grid_28[index]) != int(sized["grid_28"][index]):
			identity = false
	check.call(identity, "a 28x28 box needs no resample (the source identity case)")
	var grid_12: PackedInt32Array = SpriteLighting.sized_grid(12, 12)["mul"]
	var sampled := true
	for index in range(16):
		if int(grid_12[index]) != int(sized["grid_12"][index]):
			sampled = false
	check.call(sampled, "the box sampler reproduces the pinned canonical cells")
	SpriteLighting.reset_gradient_cache()
	var again: PackedInt32Array = SpriteLighting.sized_grid(12, 12)["mul"]
	check.call(
		again == grid_12,
		"reset_gradient_cache drops the cache and the rebuilt grid is identical"
	)

	var rig := _image_from(flat_case)
	var untouched := rig.get_data()
	var disabled := SpriteLighting.apply_to_rig(rig, false)
	check.call(
		disabled == rig and rig.get_data() == untouched,
		"apply_to_rig with enabled=false is a no-op"
	)
	SpriteLighting.apply_to_rig(rig, true)
	check.call(
		_compare_pixels(rig, flat_case["output"]) == 0,
		"apply_to_rig with enabled=true runs the same pass"
	)
