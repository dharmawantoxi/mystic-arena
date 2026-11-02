extends RefCounted

## Parity against the pygame oracle for splash_screen.py. RNG distribution is
## intentionally native; evolution tests inject the oracle's initial particles
## and respawn stream. Text layout uses fake-font metrics from the fixture.


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/splash_parity.json", FileAccess.READ)
	runner.check(file != null, "splash Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var model := SplashModel.new()
	runner.check(model.valid(), "native splash contract loads")
	runner.check(model.config.game_name == "MYSTIC ARENA", "splash title matches source")
	runner.check(model.config.hint_text == "Tap anywhere to skip", "splash hint matches source")
	_timeline(runner, oracle)
	_particles(runner, oracle)
	_background(runner, model, oracle)
	_layout(runner, model, oracle)
	_logo_glow(runner, model, oracle)
	_cache(runner, model)
	var missing := SplashModel.new("user://missing_splash_%d.json" % Time.get_ticks_usec())
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing splash contract fails closed"
	)
	SplashEffects.clear_cache()


static func _timeline(runner, oracle: Dictionary) -> void:
	var dt := float(oracle.dt)
	for scenario: Dictionary in oracle.timeline:
		var model := SplashModel.new()
		var ok: bool = true
		var skip_at: Variant = scenario.get("skip_at")
		for index in range(scenario.frames.size()):
			if (
				skip_at != null
				and float(index) * dt >= float(skip_at) - 0.000000000001
				and not model.skipped
			):
				model.skip()
			model.update(dt)
			var expected: Array = scenario.frames[index]
			ok = ok and runner.near(model.elapsed, float(expected[0]))
			ok = ok and model.title_alpha == int(expected[1])
			ok = ok and runner.near(model.overall_alpha(), float(expected[2]))
			ok = ok and _done_matches(model, bool(expected[3]))
			ok = ok and model.skipped == bool(expected[4])
		runner.check(ok, "splash timeline parity: " + str(scenario.name))


static func _done_matches(model: SplashModel, expected: bool) -> bool:
	if model.done == expected:
		return true
	# CPython and GDScript can land on opposite sides of an exact threshold
	# after repeated dt addition; allow only a sub-microsecond boundary window.
	return (
		absf(model.elapsed - model.f("skip_done")) < 0.000001
		or absf(model.elapsed - model.f("duration")) < 0.000001
	)


static func _particles(runner, oracle: Dictionary) -> void:
	var row: Dictionary = oracle.particles
	var model := SplashModel.new()
	model.particles = row.initial.duplicate(true)
	model.respawn_override = row.respawn.duplicate(true)
	for _frame in range(int(row.frames)):
		model.update(float(oracle.dt))
	var ok: bool = model.particles.size() == row.final.size()
	for index in range(mini(model.particles.size(), row.final.size())):
		var actual: Dictionary = model.particles[index]
		var expected: Dictionary = row.final[index]
		for key: String in ["x", "y", "speed", "drift", "phase"]:
			ok = ok and runner.near(float(actual[key]), float(expected[key]))
	runner.check(ok, "splash particle evolution parity")
	model.elapsed = 1.5
	ok = true
	for index in range(mini(model.particles.size(), row.draw_at_1_5.size())):
		var actual := model.particle_draw(model.particles[index])
		var expected: Dictionary = row.draw_at_1_5[index]
		var pos: Vector2i = actual.pos
		var color: Color = actual.color
		ok = ok and pos == Vector2i(int(expected.pos[0]), int(expected.pos[1]))
		ok = ok and int(actual.radius) == int(expected.radius)
		ok = ok and roundi(color.r * 255) == int(expected.color[0])
		ok = ok and roundi(color.g * 255) == int(expected.color[1])
		ok = ok and roundi(color.b * 255) == int(expected.color[2])
	runner.check(ok, "splash particle draw parity")


static func _background(runner, model: SplashModel, oracle: Dictionary) -> void:
	for row: Dictionary in oracle.background:
		var size := Vector2i(int(row.size[0]), int(row.size[1]))
		var texture := SplashEffects.background(model, size)
		var ok: bool = texture != null
		if ok:
			var image := texture.get_image()
			for sample: Dictionary in row.samples:
				var color := image.get_pixel(int(sample.pos[0]), int(sample.pos[1]))
				ok = ok and roundi(color.r * 255) == int(sample.rgb[0])
				ok = ok and roundi(color.g * 255) == int(sample.rgb[1])
				ok = ok and roundi(color.b * 255) == int(sample.rgb[2])
			if row.has("rgb_sha256"):
				ok = ok and _rgb_sha(image) == str(row.rgb_sha256)
		runner.check(ok, "splash background parity %dx%d" % [size.x, size.y])


static func _layout(runner, model: SplashModel, oracle: Dictionary) -> void:
	model.width = int(oracle.screen[0])
	model.height = int(oracle.screen[1])
	for row: Dictionary in oracle.layout_cases:
		model.elapsed = float(row.elapsed)
		model.title_alpha = int(row.title_alpha)
		var has_logo := bool(row.has_logo)
		var title_size := model.font_size("title_below") if has_logo else model.font_size("title")
		var title := _fake_size(str(model.config.game_name), title_size)
		var sub := _fake_size(str(model.config.tagline), model.font_size("sub"))
		var hint := _fake_size(str(model.config.hint_text), model.font_size("hint"))
		var geometry := model.layout(
			Vector2i(int(row.logo_source[0]), int(row.logo_source[1])), title, sub, hint, has_logo
		)
		var ok: bool = runner.near(model.overall_alpha(), float(row.overall_alpha))
		ok = ok and int(model.f("hint_alpha") * model.overall_alpha()) == int(row.hint_alpha)
		if not bool(row.drawn):
			ok = ok and model.overall_alpha() <= model.f("alpha_epsilon")
		else:
			if has_logo:
				ok = ok and geometry.logo_rect == _rect(row.logo_rect)
			if row.get("title_rect") != null:
				ok = ok and geometry.title_rect == _rect(row.title_rect)
			ok = ok and geometry.subtitle_rect == _rect(row.subtitle_rect)
			ok = ok and geometry.hint_rect == _rect(row.hint_rect)
			ok = (
				ok
				and _lines_equal(
					model.accent_lines(geometry.title_rect, model.title_alpha), row.accent_lines
				)
			)
			if row.has("title_glow_rects"):
				var glows: Array = model.title_glow_rects(geometry.title_rect)
				ok = ok and glows.size() == row.title_glow_rects.size()
				for index in range(mini(glows.size(), row.title_glow_rects.size())):
					ok = ok and glows[index] == _rect(row.title_glow_rects[index])
		runner.check(
			ok, "splash layout parity %s @ %.2f" % [str(row.logo_source), float(row.elapsed)]
		)


static func _logo_glow(runner, model: SplashModel, oracle: Dictionary) -> void:
	for row: Dictionary in oracle.logo_glow:
		var radius := int(row.radius)
		var texture := SplashEffects.logo_glow(model, radius)
		var ok: bool = texture != null
		if ok:
			var image := texture.get_image()
			for distance in range(radius):
				var alpha := roundi(image.get_pixel(radius + distance, radius).a * 255)
				ok = ok and alpha == int(row.alpha_profile[distance])
		runner.check(ok, "splash logo glow alpha parity r=%d" % radius)


static func _cache(runner, model: SplashModel) -> void:
	SplashEffects.clear_cache()
	var a := SplashEffects.background(model, Vector2i(64, 48))
	var b := SplashEffects.background(model, Vector2i(64, 48))
	runner.check(a != null and a == b, "splash background cache reuses texture")
	var image := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	image.fill(Color.WHITE)
	var frame_a := SplashEffects.logo_frame(image, Vector2i(4, 4))
	var frame_b := SplashEffects.logo_frame(image, Vector2i(4, 4))
	runner.check(frame_a != null and frame_a == frame_b, "splash logo frame cache reuses texture")
	runner.check(
		SplashModel.py_round(18.5) == 18 and SplashModel.py_round(19.5) == 20,
		"splash grow quantizer uses CPython half-to-even"
	)


static func _fake_size(text: String, size: int) -> Vector2i:
	return Vector2i(maxi(1, text.length() * size / 2), maxi(1, size))


static func _rect(row: Array) -> Rect2i:
	return Rect2i(int(row[0]), int(row[1]), int(row[2]), int(row[3]))


static func _lines_equal(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var a: Dictionary = actual[index]
		var e: Dictionary = expected[index]
		if a.start != Vector2(e.start[0], e.start[1]) or a.end != Vector2(e.end[0], e.end[1]):
			return false
		if a.width != int(e.width):
			return false
		var col: Color = a.color
		if roundi(col.r * 255) != int(e.color[0]) or roundi(col.g * 255) != int(e.color[1]):
			return false
		if roundi(col.b * 255) != int(e.color[2]):
			return false
	return true


static func _rgb_sha(image: Image) -> String:
	var rgba := image.get_data()
	var rgb := PackedByteArray()
	rgb.resize(rgba.size() / 4 * 3)
	for index in range(rgba.size() / 4):
		rgb[index * 3] = rgba[index * 4]
		rgb[index * 3 + 1] = rgba[index * 4 + 1]
		rgb[index * 3 + 2] = rgba[index * 4 + 2]
	return _sha256(rgb)


static func _sha256(bytes: PackedByteArray) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(bytes)
	return context.finish().hex_encode()
