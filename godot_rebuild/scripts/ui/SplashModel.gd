class_name SplashModel
extends RefCounted

## Native port of splash_screen.py timing/particles/layout. The generated JSON
## contract is the only source of numeric constants; no Python at runtime.
const DEFAULT_PATH := "res://data/splash.json"
const TITLE_EPS := 0.00001
var config: Dictionary = {}
var font_files: Dictionary = {}
var cheap_alpha_default := true
var source_sha := ""
var load_error := ""
var width := 1280
var height := 720
var elapsed := 0.0
var skipped := false
var done := false
var title_alpha := 0
var particles: Array = []
var respawn_override: Array = []
var _rng := RandomNumberGenerator.new()


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		load_error = "Invalid splash JSON"
		return
	if int(parsed.get("schema", 0)) != 1 or str(parsed.get("source", "")) != "splash_screen.py":
		load_error = "Unsupported splash contract"
		return
	config = parsed.get("config", {})
	source_sha = str(parsed.get("source_sha256", ""))
	font_files = parsed.get("font_files", {})
	cheap_alpha_default = bool(parsed.get("cheap_alpha_default", true))
	if not config.has("duration") or not config.has("particle_count"):
		load_error = "Splash contract missing required fields"
		return
	_rng.seed = int(parsed.get("particle_seed", 1234))
	make_particles()


func valid() -> bool:
	return load_error.is_empty()


func f(key: String) -> float:
	return float(config.get(key, 0.0))


func i(key: String) -> int:
	return int(config.get(key, 0))


func text(key: String) -> String:
	return str(config.get(key, ""))


func font_size(role: String) -> int:
	var sizes: Dictionary = config.get("font_sizes", {})
	var fallback: Dictionary = config.get("font_fallback_sizes", {})
	return int(sizes.get(role, fallback.get(role, 16)))


func color(key: String, alpha := 1.0) -> Color:
	var row: Array = config.get(key, [255, 255, 255])
	return Color(float(row[0]) / 255.0, float(row[1]) / 255.0, float(row[2]) / 255.0, alpha)


func resize(size: Vector2i) -> void:
	if size.x <= 0 or size.y <= 0:
		return
	if size.x == width and size.y == height:
		return
	width = size.x
	height = size.y
	make_particles()


func make_particles() -> void:
	particles.clear()
	var ranges := {
		"r": config.get("prange_r", [0.6, 2.4]),
		"speed": config.get("prange_speed", [0.08, 0.35]),
		"drift": config.get("prange_drift", [-0.12, 0.12]),
		"phase": config.get("prange_phase", [0.0, TAU]),
	}
	var palette: Array = config.get("particle_colors", [[255, 210, 120]])
	for _index in range(i("particle_count")):
		var row := {}
		row["x"] = _rng.randf_range(0, width)
		row["y"] = _rng.randf_range(0, height)
		for key: String in ranges:
			var bounds: Array = ranges[key]
			row[key] = _rng.randf_range(float(bounds[0]), float(bounds[1]))
		row["color"] = palette[_rng.randi_range(0, palette.size() - 1)]
		particles.append(row)


func skip() -> void:
	if not done:
		skipped = true


func update(dt: float) -> void:
	elapsed += dt
	for particle: Dictionary in particles:
		particle["y"] = float(particle.y) - float(particle.speed)
		particle["x"] = (
			float(particle.x)
			+ float(particle.drift)
			+ sin(elapsed * f("move_rate") + float(particle.phase)) * f("move_amp")
		)
		if float(particle.y) < f("wrap_below"):
			particle["y"] = height + f("wrap_margin")
			if not respawn_override.is_empty():
				particle["x"] = float(respawn_override.pop_front())
			else:
				particle["x"] = _rng.randf_range(0, width)
	if skipped:
		done = elapsed >= f("skip_done")
	else:
		done = elapsed >= f("duration")
	if elapsed < f("title_delay"):
		title_alpha = 0
	else:
		title_alpha = int(
			f("title_max") * min(1.0, (elapsed - f("title_delay")) / f("title_ramp")) + TITLE_EPS
		)


func overall_alpha() -> float:
	var fade_in := minf(1.0, elapsed / f("fade_in"))
	var fade_out: float
	if skipped:
		fade_out = maxf(0.0, 1.0 - elapsed / f("skip_fade"))
	else:
		fade_out = minf(1.0, maxf(0.0, (f("duration") - elapsed) / f("fade_out")))
	return maxf(0.0, minf(1.0, fade_in * fade_out))


func particle_draw(particle: Dictionary) -> Dictionary:
	var tw := 0.5 + 0.5 * sin(elapsed * f("twinkle_rate") + float(particle.phase))
	var factor := f("dim_floor") + f("dim_span") * tw
	var rgb: Array = particle.color
	return {
		"pos": Vector2i(int(particle.x), int(particle.y)),
		"radius": maxi(i("particle_min_r"), int(particle.r)),
		"color":
		Color(
			int(float(rgb[0]) * factor) / 255.0,
			int(float(rgb[1]) * factor) / 255.0,
			int(float(rgb[2]) * factor) / 255.0,
			1.0
		),
	}


func logo_geometry(source_size: Vector2i, at := -1.0) -> Dictionary:
	var t := elapsed if at < 0.0 else at
	if source_size.x <= 0 or source_size.y <= 0:
		return {}
	var scale := minf(minf(f("logo_max_w") / source_size.x, f("logo_max_h") / source_size.y), 1.0)
	var base := Vector2i(maxi(1, int(source_size.x * scale)), maxi(1, int(source_size.y * scale)))
	var grow := minf(1.0, t / f("grow_time"))
	var gq := py_round((f("grow_min") + f("grow_span") * grow) * f("grow_quant")) / f("grow_quant")
	var size := Vector2i(maxi(1, int(base.x * gq)), maxi(1, int(base.y * gq)))
	return {
		"base": base,
		"gq": gq,
		"size": size,
		"glow_radius": maxi(size.x, size.y) / 2 + i("glow_pad")
	}


func layout(
	logo_source: Vector2i,
	title_size: Vector2i,
	sub_size: Vector2i,
	hint_size: Vector2i,
	has_logo: bool
) -> Dictionary:
	var cx := width / 2
	var base_y := height / 2
	var result := {"hint_rect": _center_rect(hint_size, Vector2i(cx, height - i("hint_margin")))}
	if has_logo:
		var geo := logo_geometry(logo_source)
		var logo_size: Vector2i = geo.size
		var logo_rect := _center_rect(logo_size, Vector2i(cx, base_y - i("logo_lift")))
		result["logo_rect"] = logo_rect
		result["title_rect"] = _center_rect(
			title_size, Vector2i(cx, logo_rect.end.y + i("title_below"))
		)
		result["subtitle_rect"] = _center_rect(
			sub_size, Vector2i(cx, logo_rect.end.y + i("sub_below"))
		)
	else:
		result["title_rect"] = _center_rect(title_size, Vector2i(cx, base_y))
		result["subtitle_rect"] = _center_rect(sub_size, Vector2i(cx, base_y + i("sub_text_only")))
	return result


func accent_lines(title_rect: Rect2i, alpha: int) -> Array:
	if alpha <= 0:
		return []
	var cx := width / 2
	var gap := title_rect.size.x / 2 + i("accent_pad")
	var y := title_rect.position.y + title_rect.size.y / 2
	var lines := []
	for row: Array in config.get("accent_offsets", []):
		var off := int(row[0])
		var base: Array = config.get("accent" if str(row[1]) == "ACCENT" else "accent_2")
		var fac := (float(alpha) / 255.0) * f("accent_fac")
		var line_color := Color8(
			int(float(base[0]) * fac), int(float(base[1]) * fac), int(float(base[2]) * fac), 255
		)
		lines.append(
			{
				"start": Vector2(cx - gap, y + off),
				"end": Vector2(cx - gap + i("accent_len"), y + off),
				"color": line_color,
				"width": i("accent_width")
			}
		)
		lines.append(
			{
				"start": Vector2(cx + gap, y + off),
				"end": Vector2(cx + gap - i("accent_len"), y + off),
				"color": line_color,
				"width": i("accent_width")
			}
		)
	return lines


func title_glow_rects(rect: Rect2i) -> Array:
	var out := []
	for row: Array in config.get("glow_layers", []):
		var layer := int(row[0])
		var spread := int(row[1])
		out.append(
			Rect2i(
				rect.position - Vector2i(layer + i("glow_offset"), layer + i("glow_offset")),
				(
					rect.size
					+ Vector2i(
						2 * layer + spread * i("glow_grow"), 2 * layer + spread * i("glow_grow")
					)
				)
			)
		)
	return out


static func py_round(value: float) -> int:
	var lower := floorf(value)
	var fraction := value - lower
	if is_equal_approx(fraction, 0.5):
		return int(lower) if int(lower) % 2 == 0 else int(lower) + 1
	return int(roundf(value))


static func _center_rect(size: Vector2i, center: Vector2i) -> Rect2i:
	return Rect2i(center.x - size.x / 2, center.y - size.y / 2, size.x, size.y)
