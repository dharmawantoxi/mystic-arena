extends RefCounted

## Exact pixel parity against lighting.py / pygame GENERIC smoothscale.
## Covers alpha masks, bbox, gradient resampling, blend order, cache bounds,
## fail-closed loading and the opt-in raw-sprite renderer path.


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/lighting_parity.json", FileAccess.READ)
	runner.check(file != null, "lighting Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var lighting := Lighting.new()
	runner.check(lighting.valid(), "native lighting contract loads")
	runner.check(lighting.light_dir == Vector2i(-1, -1), "lighting direction matches source")
	runner.check(lighting.rim_add == Vector3i(30, 26, 44), "lighting rim constants match source")
	runner.check(
		lighting.shade_mul == 168 and lighting.mask_alpha == 170, "lighting shade/mask constants"
	)
	_contours(runner, lighting, oracle.contour_cases)
	_gradients(runner, lighting, oracle.gradient_cases)
	_apply(runner, lighting, oracle.apply_cases)
	_cache(runner, lighting)
	_runtime_path(runner, lighting)
	var missing := Lighting.new("user://missing_lighting_%d.json" % Time.get_ticks_usec())
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing lighting contract fails closed"
	)
	lighting.clear_cache()


static func _image(row: Dictionary, field := "before_rgba") -> Image:
	var bytes := Marshalls.base64_to_raw(str(row[field]))
	return Image.create_from_data(int(row.width), int(row.height), false, Image.FORMAT_RGBA8, bytes)


static func _contours(runner, lighting: Lighting, cases: Array) -> void:
	for row: Dictionary in cases:
		var image := _image(row)
		var masks := lighting.contour_masks(image, int(row.alpha), int(row.band_width))
		var rim: Dictionary = row.rim
		var shade: Dictionary = row.shade
		var ok := true
		if str(rim.bits).is_empty():
			ok = masks.is_empty()
		else:
			ok = not masks.is_empty()
			if ok:
				ok = masks.rim == Marshalls.base64_to_raw(str(rim.bits))
				ok = ok and masks.shade == Marshalls.base64_to_raw(str(shade.bits))
				ok = ok and int(masks.rim_count) == int(rim.count)
				ok = ok and int(masks.shade_count) == int(shade.count)
		var box: Array = row.bbox
		ok = (
			ok
			and (
				lighting.bbox_of(image, int(row.alpha))
				== Rect2i(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
			)
		)
		runner.check(ok, "lighting contour/bbox: " + str(row.name))


static func _gradients(runner, lighting: Lighting, cases: Array) -> void:
	for row: Dictionary in cases:
		var size := Vector2i(int(row.width), int(row.height))
		var maps := lighting.gradient(
			size, {"dark": int(row.dark), "light": int(row.light), "sheen": int(row.sheen)}
		)
		var ok := not maps.is_empty()
		if ok:
			ok = _sha256(maps.mul) == str(row.mul_rgb_sha256)
			ok = ok and _sha256(maps.add) == str(row.add_rgb_sha256)
			ok = ok and _sample_eq(maps.mul, 0, row.mul_first)
			ok = ok and _sample_eq(maps.mul, maps.mul.size() - 3, row.mul_last)
			ok = ok and _sample_eq(maps.add, 0, row.add_first)
			ok = ok and _sample_eq(maps.add, maps.add.size() - 3, row.add_last)
		runner.check(
			ok,
			"lighting gradient %dx%d (%d/%d/%d)" % [size.x, size.y, row.dark, row.light, row.sheen]
		)


static func _apply(runner, lighting: Lighting, cases: Array) -> void:
	for row: Dictionary in cases:
		var image := _image(row)
		var options: Dictionary = row.options.duplicate(true)
		if options.has("box") and options.box is Array and options.box.size() == 4:
			var box: Array = options.box
			options.box = Rect2i(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
		lighting.apply_to_rig(image, bool(row.enabled), options)
		var expected := Marshalls.base64_to_raw(str(row.after_rgba))
		var ok := image.get_data() == expected
		var box_row: Array = row.bbox
		ok = (
			ok
			and (
				lighting.bbox_of(image)
				== Rect2i(int(box_row[0]), int(box_row[1]), int(box_row[2]), int(box_row[3]))
			)
		)
		runner.check(ok, "lighting pixels: " + str(row.name))


static func _cache(runner, lighting: Lighting) -> void:
	lighting.reset_gradient_cache()
	for index in range(90):
		lighting.gradient(Vector2i(3 + index, 3 + index % 9))
	runner.check(lighting.size_cache_size() <= 65, "lighting size cache is bounded")
	var before := lighting.size_cache_size()
	lighting.gradient(Vector2i(92, 11))
	runner.check(lighting.size_cache_size() == before, "lighting gradient cache hit does not grow")
	lighting.reset_gradient_cache()
	runner.check(lighting.size_cache_size() == 0, "lighting gradient cache resets")


static func _runtime_path(runner, lighting: Lighting) -> void:
	var image := Image.create(32, 32, false, Image.FORMAT_RGBA8)
	image.fill(Color(0, 0, 0, 0))
	image.fill_rect(Rect2i(6, 6, 20, 20), Color8(180, 130, 80, 255))
	var texture := ImageTexture.create_from_image(image)
	var expected := image.duplicate()
	lighting.apply(expected, {"gradient": false})
	EntityVisuals.configure(RenderQuality.preset("high"))
	var lit := EntityVisuals.lit_frame_texture(texture, Rect2(0, 0, 32, 32), {"gradient": false})
	runner.check(
		lit != null and lit.get_image().get_data() == expected.get_data(),
		"raw sprite runtime lighting matches CPU pass"
	)
	var cached := EntityVisuals.lit_frame_texture(texture, Rect2(0, 0, 32, 32), {"gradient": false})
	runner.check(cached == lit, "lit frame cache reuses texture")
	runner.check(
		EntityVisuals.lit_frame_texture(texture, Rect2(0, 0, 32, 32), {}, false) == null,
		"lighting kill switch bypasses processing"
	)
	runner.check(
		EntityVisuals._lighting_options({"lighting_baked": true}, "blue").is_empty(),
		"baked strips never get a second lighting pass"
	)
	var raw := EntityVisuals._lighting_options({"lighting_baked": false}, "blue")
	runner.check(bool(raw.get("enabled", false)), "raw imports opt into runtime lighting")
	EntityVisuals.configure(RenderQuality.preset("low"))
	runner.check(
		EntityVisuals.lit_textures.is_empty(), "quality change invalidates lit frame cache"
	)
	raw = EntityVisuals._lighting_options({"lighting_baked": false}, "blue")
	runner.check(not bool(raw.get("enabled", true)), "low quality disables hero lighting")
	EntityVisuals.configure(RenderQuality.preset("high"))
	EntityVisuals.clear_cache()


static func _sha256(bytes: PackedByteArray) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(bytes)
	return context.finish().hex_encode()


static func _sample_eq(bytes: PackedByteArray, offset: int, expected: Array) -> bool:
	return (
		int(bytes[offset]) == int(expected[0])
		and int(bytes[offset + 1]) == int(expected[1])
		and int(bytes[offset + 2]) == int(expected[2])
	)
