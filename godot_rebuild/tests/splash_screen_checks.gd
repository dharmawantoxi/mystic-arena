extends RefCounted
## Layer 9at: replays the `splash_screen.py` source oracle fixture through
## the native timeline. `splash_screen_source_oracle.py` runs the REAL
## `SplashScreen` under a recording pygame shim, so the fades, the baked
## background, the particle motion, the logo growth and the layout numbers
## below all come from the source.

const Timeline = preload("res://scripts/ui/splash_timeline.gd")
const FIXTURE := "res://tests/fixtures/splash_screen_source.json"
## The oracle's pygame fallback fonts: real size -> fake size, 0.55*size px
## per glyph, height = size.
const FAKE_SIZE := {92: 110, 66: 80, 22: 26, 16: 18}


static func _measure(text: String, font_size: int) -> Vector2i:
	var fake := int(FAKE_SIZE.get(font_size, font_size))
	return Vector2i(int(float(fake) * 0.55) * text.length(), fake)


static func _color(values: Array) -> Color:
	return Color8(int(values[0]), int(values[1]), int(values[2]))


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Splash fixture parses")
	if not (data is Dictionary):
		return
	_constant_checks(data, check)
	_timeline_checks(data, check)
	_background_checks(data, check)
	_particle_checks(data, check)
	_logo_checks(data, check)
	_layout_checks(data, check)


func _constant_checks(data: Dictionary, check: Callable) -> void:
	check.call(Timeline.GAME_NAME == String(data["game_name"]), "game name matches")
	check.call(is_equal_approx(Timeline.DURATION, float(data["duration"])), "duration is 3 s")
	check.call(Timeline.SUBTITLE == String(data["subtitle"]), "subtitle matches")
	check.call(Timeline.HINT == String(data["hint"]), "hint matches")
	var colors: Dictionary = data["colors"]
	check.call(Timeline.ACCENT == _color(colors["ACCENT"]), "ACCENT matches")
	check.call(Timeline.ACCENT_2 == _color(colors["ACCENT_2"]), "ACCENT_2 matches")
	check.call(Timeline.TEXT_MAIN == _color(colors["TEXT_MAIN"]), "TEXT_MAIN matches")
	check.call(Timeline.TEXT_DIM == _color(colors["TEXT_DIM"]), "TEXT_DIM matches")
	check.call(Timeline.PARTICLE_COUNT == int(data["particle_count"]), "46 particles")
	var palette: Array = data["particle_palette"]
	for index in range(palette.size()):
		check.call(
			Timeline.PARTICLE_PALETTE[index] == _color(palette[index]),
			"particle palette %d matches" % index
		)


func _timeline_checks(data: Dictionary, check: Callable) -> void:
	for sample_value in data["timeline"]:
		var sample: Dictionary = sample_value
		var t := float(sample["elapsed"])
		var tag := "t=%.3f " % t
		check.call(
			Timeline.title_alpha(t) == int(sample["title_alpha"]), tag + "title alpha matches"
		)
		check.call(
			absf(Timeline.overall_alpha(t, false) - float(sample["overall_alpha"])) < 1e-5,
			tag + "overall alpha matches"
		)
		check.call(Timeline.is_done(t, false) == bool(sample["done"]), tag + "done flag matches")
	check.call(int(data["done_frame"]) == 181, "3 s at 60 Hz ends on frame 181")
	for sample_value in data["skip_timeline"]:
		var sample: Dictionary = sample_value
		var t := float(sample["elapsed"])
		check.call(
			absf(Timeline.overall_alpha(t, true) - float(sample["overall_alpha"])) < 1e-5,
			"skip alpha at t=%.3f matches" % t
		)
		check.call(not Timeline.is_done(t, true) or t >= 0.25, "skip done rule")
	var skip_done: Dictionary = data["skip_done"]
	check.call(
		Timeline.is_done(float(skip_done["elapsed"]), true),
		"a late skip finishes on the next frame"
	)
	check.call(
		not Timeline.is_done(0.2, true) and Timeline.is_done(0.25, true), "skip ends at 0.25 s"
	)


func _background_checks(data: Dictionary, check: Callable) -> void:
	var rows: Array = Timeline.gradient_rows(1280, 720)
	var expected_rows: Array = data["gradient"]
	check.call(rows.size() == expected_rows.size(), "gradient has the source row count")
	for index in range(mini(rows.size(), expected_rows.size())):
		var want: Dictionary = expected_rows[index]
		var got: Dictionary = rows[index]
		var r: Array = want["rect"]
		var same: bool = (
			got["rect"] == Rect2i(int(r[0]), int(r[1]), int(r[2]), int(r[3]))
			and got["color"] == _color(want["color"])
		)
		check.call(same, "gradient row %d matches" % index)
	var rings: Array = Timeline.vignette_rings()
	var expected_rings: Array = data["vignette"]
	check.call(rings.size() == expected_rings.size(), "vignette ring count matches")
	for index in range(mini(rings.size(), expected_rings.size())):
		var want: Dictionary = expected_rings[index]
		var got: Dictionary = rings[index]
		check.call(
			int(got["inset"]) == int(want["inset"]) and int(got["alpha"]) == int(want["alpha"]),
			"vignette ring %d matches" % index
		)
	# pygame.draw.rect overwrites: the inset-2 ring (alpha 255) is the last
	# one drawn over every pixel at least 2 px from the edge.
	check.call(
		(
			Timeline.vignette_alpha(0) == 0
			and Timeline.vignette_alpha(1) == 0
			and Timeline.vignette_alpha(2) == 255
			and Timeline.vignette_alpha(140) == 255
			and Timeline.vignette_alpha(360) == 255
		),
		"vignette replaces pixels like pygame.draw.rect (2 px gradient border)"
	)


func _particle_checks(data: Dictionary, check: Callable) -> void:
	var particles: Array = []
	for p_value in data["particles_initial"]:
		var p: Dictionary = p_value
		(
			particles
			. append(
				{
					"x": float(p["x"]),
					"y": float(p["y"]),
					"r": float(p["r"]),
					"speed": float(p["speed"]),
					"drift": float(p["drift"]),
					"phase": float(p["phase"]),
					"color": _color(p["color"]),
				}
			)
		)
	var frames := int(data["particles_after_frames"])
	var elapsed := 0.0
	for _frame in range(frames):
		elapsed += 1.0 / 60.0
		Timeline.step_particles(particles, elapsed, 1280.0, 720.0, null)
	var expected: Array = data["particles_after"]
	var max_error := 0.0
	for index in range(expected.size()):
		var want: Dictionary = expected[index]
		var got: Dictionary = particles[index]
		max_error = maxf(max_error, absf(float(got["x"]) - float(want["x"])))
		max_error = maxf(max_error, absf(float(got["y"]) - float(want["y"])))
	check.call(
		max_error < 1e-4, "particle motion after %d frames matches (err %.6f)" % [frames, max_error]
	)
	# Twinkle colour / radius of the drawn particles at a sampled frame.
	for sample_value in data["timeline"]:
		var sample: Dictionary = sample_value
		if not sample.has("particles") or absf(float(sample["elapsed"]) - 0.1) > 1e-6:
			continue
		var drawn: Array = sample["particles"]
		var initial: Array = data["particles_initial"]
		var ok := true
		for index in range(drawn.size()):
			var p0: Dictionary = initial[index]
			var fake := {
				"phase": float(p0["phase"]), "color": _color(p0["color"]), "r": float(p0["r"])
			}
			var want: Dictionary = drawn[index]
			if Timeline.particle_color(fake, 0.1) != _color(want["color"]):
				ok = false
			if Timeline.particle_radius(fake) != int(want["radius"]):
				ok = false
		check.call(ok, "particle twinkle colours and radii match at t=0.1")


func _logo_checks(data: Dictionary, check: Callable) -> void:
	var px := int(data["logo_px"])
	var scaled: Array = data["logo_scaled"]
	check.call(
		Timeline.logo_scaled_size(Vector2i(px, px)) == Vector2i(int(scaled[0]), int(scaled[1])),
		"1024 px logo fits the 340x320 box"
	)
	check.call(
		Timeline.logo_scaled_size(Vector2i(200, 100)) == Vector2i(200, 100),
		"small logo not upscaled"
	)
	for sample_value in data["logo_grow"]:
		var sample: Dictionary = sample_value
		var gq := Timeline.logo_grow(float(sample["elapsed"]))
		var size: Array = sample["size"]
		check.call(
			(
				is_equal_approx(gq, float(sample["gq"]))
				and (
					Timeline.logo_grown_size(Vector2i(320, 320), gq)
					== Vector2i(int(size[0]), int(size[1]))
				)
			),
			"logo grow at t=%.2f matches" % float(sample["elapsed"])
		)
	check.call(
		Timeline.glow_radius(Vector2i(320, 320)) == int(data["logo_glow_radius"]),
		"glow radius matches"
	)
	var rings: Array = Timeline.glow_rings(Vector2i(320, 320))
	var expected: Array = data["logo_glow"]
	check.call(rings.size() == expected.size(), "glow ring count matches")
	for index in range(mini(rings.size(), expected.size())):
		var want: Dictionary = expected[index]
		var got: Dictionary = rings[index]
		check.call(
			int(got["g"]) == int(want["g"]) and int(got["alpha"]) == int(want["alpha"]),
			"glow ring %d matches" % index
		)


func _layout_checks(data: Dictionary, check: Callable) -> void:
	for sample_value in data["timeline"]:
		var sample: Dictionary = sample_value
		if not bool(sample["drawn"]):
			continue
		var t := float(sample["elapsed"])
		var frame: Dictionary = Timeline.layout(t, false, 1280, 720, Vector2i(320, 320), _measure)
		var tag := "logo frame t=%.3f " % t
		_text_checks(frame, sample, tag, check)
		var images: Array = sample["images"]
		# images[1] is the grown logo (images[0] its glow surface).
		var logo: Dictionary = images[1]
		var logo_rect: Rect2i = frame["logo_rect"]
		check.call(
			(
				logo_rect.size == Vector2i(int(logo["size"][0]), int(logo["size"][1]))
				and logo_rect.position == Vector2i(int(logo["pos"][0]), int(logo["pos"][1]))
				and int(frame["logo_alpha"]) == int(logo["alpha"])
			),
			tag + "logo rect and alpha match"
		)
		var glow: Dictionary = images[0]
		check.call(
			(
				int(glow["size"][0]) == 2 * int(frame["glow_radius"])
				and (
					int(glow["pos"][0])
					== int((frame["glow_center"] as Vector2i).x) - int(frame["glow_radius"])
				)
			),
			tag + "logo glow surface matches"
		)
		if images.size() >= 6:
			var title: Dictionary = images[5]
			var title_rect: Rect2i = frame["title_rect"]
			check.call(
				(
					title_rect.position == Vector2i(int(title["pos"][0]), int(title["pos"][1]))
					and int(title["alpha"]) == int(frame["title_alpha"])
				),
				tag + "title rect under the logo matches"
			)
		_line_checks(frame, sample, tag, check)
	var plain: Dictionary = data["plain_frame"]
	var frame: Dictionary = Timeline.layout(
		float(plain["elapsed"]), false, 1280, 720, Vector2i.ZERO, _measure
	)
	check.call(
		not bool(frame["has_logo"]) and int(frame["title_size"]) == 92,
		"plain splash uses the 92 px title"
	)
	_text_checks(frame, plain, "plain frame ", check)
	_line_checks(frame, plain, "plain frame ", check)


func _text_checks(frame: Dictionary, sample: Dictionary, tag: String, check: Callable) -> void:
	for text_value in sample["texts"]:
		var text: Dictionary = text_value
		var rect: Rect2i = (
			frame["sub_rect"] if String(text["text"]) == Timeline.SUBTITLE else frame["hint_rect"]
		)
		var alpha: int = (
			int(frame["title_alpha"])
			if String(text["text"]) == Timeline.SUBTITLE
			else int(frame["hint_alpha"])
		)
		check.call(
			(
				rect.position == Vector2i(int(text["pos"][0]), int(text["pos"][1]))
				and alpha == int(text["alpha"])
			),
			tag + "text '%s' position/alpha match" % text["text"]
		)


func _line_checks(frame: Dictionary, sample: Dictionary, tag: String, check: Callable) -> void:
	var lines: Array = sample["lines"]
	var got: Array = frame["lines"]
	check.call(got.size() == lines.size(), tag + "title line count matches")
	for index in range(mini(got.size(), lines.size())):
		var want: Dictionary = lines[index]
		var line: Dictionary = got[index]
		var same: bool = (
			line["a"] == Vector2i(int(want["a"][0]), int(want["a"][1]))
			and line["b"] == Vector2i(int(want["b"][0]), int(want["b"][1]))
			and line["color"] == _color(want["color"])
		)
		check.call(same, tag + "title line %d matches" % index)
