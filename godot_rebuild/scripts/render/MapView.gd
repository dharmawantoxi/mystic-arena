class_name MapView
extends RefCounted

## Native _render.MapRenderer + map_components.DynamicRenderer.
## Static terrain/decor/lanes/shops are the 54 baked 1280x720 PNGs produced by
## tools/convert_to_godot.py --maps-png. Dynamic particles/fog/river runes/shop
## glow/torch flames are redrawn natively each fixed tick from themes_raw.json.
const MAP_SIZE := Vector2(1280, 720)
const SHOP_SIZE := 60.0
const RADIANT_SHOP := Vector2(340, 540)
const DIRE_SHOP := Vector2(940, 180)
const THEMES_PATH := "res://data/themes_raw.json"
const BAKES_PATH := "res://data/map_bakes.json"
static var _themes: Dictionary = {}
static var _bakes: Dictionary = {}
var theme_name := "forest"
var theme: Dictionary = {}
var texture: Texture2D
var quality: Dictionary = RenderQuality.preset("high")
var particles: Array[Dictionary] = []
var fog: Array[Dictionary] = []
var river: PackedVector2Array = PackedVector2Array()
var torches: Array = []
var rng := RandomNumberGenerator.new()
var missing_texture := false


static func load_tables() -> void:
	if _themes.is_empty():
		_themes = _read_json(THEMES_PATH).get("themes", {})
	if _bakes.is_empty():
		_bakes = _read_json(BAKES_PATH).get("maps", {})


static func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


static func theme_names() -> Array:
	load_tables()
	return _themes.keys()


static func color_of(value: Variant, fallback := Color.WHITE) -> Color:
	if value is Array and value.size() >= 3:
		var alpha := float(value[3]) / 255.0 if value.size() > 3 else 1.0
		return Color(
			float(value[0]) / 255.0, float(value[1]) / 255.0, float(value[2]) / 255.0, alpha
		)
	return fallback


func configure(theme_key: String, data: CoreData, quality_preset: Dictionary) -> void:
	load_tables()
	theme_name = theme_key if _themes.has(theme_key) else "forest"
	theme = _themes.get(theme_name, {})
	quality = quality_preset
	rng.seed = hash(theme_name) + 42
	var entry: Dictionary = _bakes.get(theme_name, {})
	texture = _load_texture(str(entry.get("file", "")))
	missing_texture = texture == null
	river = data.lane("river")
	torches = entry.get("torch_stones", [])
	_init_particles()
	_init_fog()


func _load_texture(path: String) -> Texture2D:
	if path.is_empty():
		return null
	if ResourceLoader.exists(path):
		var resource := load(path)
		if resource is Texture2D:
			return resource
	var image := Image.new()
	if image.load(path) == OK:
		return ImageTexture.create_from_image(image)
	return null


func _init_particles() -> void:
	particles.clear()
	if not bool(quality.get("particles", true)):
		return
	var count := int(theme.get("particle_count", 30))
	count = maxi(4, int(count * float(quality.get("particle_ratio", 1.0))))
	var kind := str(theme.get("particle_type", "firefly"))
	var radiant: Array = theme.get("particle_colors_radiant", [[100, 200, 255]])
	var dire: Array = theme.get("particle_colors_dire", [[255, 100, 50]])
	for index in range(count):
		var pos := Vector2(rng.randf_range(50, 1230), rng.randf_range(50, 670))
		var palette := radiant if pos.y > 360 else dire
		var color := color_of(palette[rng.randi_range(0, palette.size() - 1)])
		var velocity := Vector2.ZERO
		var size := rng.randi_range(1, 3)
		match kind:
			"snow":
				velocity = Vector2(rng.randf_range(-0.3, 0.3), rng.randf_range(0.3, 0.8))
			"sand":
				velocity = Vector2(rng.randf_range(0.5, 1.5), rng.randf_range(-0.2, 0.2))
			"ember":
				velocity = Vector2(rng.randf_range(-0.3, 0.3), rng.randf_range(-0.8, -0.3))
			"acid":
				velocity = Vector2(rng.randf_range(-0.15, 0.15), rng.randf_range(-0.45, -0.15))
				size = [1, 2, 2][rng.randi_range(0, 2)]
			"ash":
				velocity = Vector2(rng.randf_range(-0.22, 0.22), rng.randf_range(0.18, 0.55))
				size = [1, 1, 2][rng.randi_range(0, 2)]
			"spirit":
				velocity = Vector2(rng.randf_range(-0.16, 0.16), rng.randf_range(-0.55, -0.20))
				size = [1, 2, 2][rng.randi_range(0, 2)]
			_:
				velocity = Vector2(rng.randf_range(-0.2, 0.2), rng.randf_range(-0.2, 0.2))
		particles.append(
			{"pos": pos, "vel": velocity, "color": color, "size": size, "phase": rng.randf() * TAU}
		)


func _init_fog() -> void:
	fog.clear()
	if not bool(theme.get("fog_enabled", false)) or not bool(quality.get("fog", true)):
		return
	var count := int(theme.get("fog_count", 15))
	for index in range(count):
		(
			fog
			. append(
				{
					"pos": Vector2(rng.randf_range(0, 1280), rng.randf_range(0, 720)),
					"size": rng.randi_range(60, 140),
					"speed": rng.randf_range(0.1, 0.4),
					"color": color_of(theme.get("fog_color", [80, 60, 60, 30])),
				}
			)
		)


func update(_frame: int) -> void:
	var kind := str(theme.get("particle_type", "firefly"))
	for particle: Dictionary in particles:
		var pos: Vector2 = particle.pos
		var vel: Vector2 = particle.vel
		pos += vel
		particle.phase = float(particle.phase) + 0.05
		if kind in ["acid", "spirit"] and pos.y < 28:
			pos = Vector2(rng.randf_range(30, 1250), 690)
		elif kind == "ash" and pos.y > 700:
			pos = Vector2(rng.randf_range(30, 1250), 28)
		else:
			pos.x = wrapf(pos.x, 20, 1260)
			pos.y = wrapf(pos.y, 20, 700)
		if kind in ["acid", "ash", "spirit"]:
			pos.x += sin(float(particle.phase)) * 0.18
		particle.pos = pos
	for cloud: Dictionary in fog:
		var pos: Vector2 = cloud.pos
		pos.x = wrapf(pos.x + float(cloud.speed), -150, 1430)
		cloud.pos = pos


func ambient_modulate() -> Color:
	var tint: Variant = theme.get("ambient_tint", null)
	if tint == null:
		return Color.WHITE
	var color := color_of(tint)
	return Color(
		1.0 - (1.0 - color.r) * color.a,
		1.0 - (1.0 - color.g) * color.a,
		1.0 - (1.0 - color.b) * color.a,
		1.0
	)


func draw_static(canvas: CanvasItem) -> void:
	if texture != null:
		canvas.draw_texture_rect(texture, Rect2(Vector2.ZERO, MAP_SIZE), false, ambient_modulate())
	else:
		canvas.draw_rect(Rect2(Vector2.ZERO, MAP_SIZE), Color("101820"))


func draw_dynamic(canvas: CanvasItem, frame: int) -> void:
	_draw_fog(canvas)
	if str(quality.get("level", "high")) != "low":
		_draw_river(canvas, frame)
		_draw_shop_glow(canvas, frame)
	if bool(quality.get("floating_decor", true)):
		_draw_shop_smoke(canvas, frame)
	if bool(quality.get("particles", true)):
		_draw_particles(canvas)
	if str(quality.get("level", "high")) != "low":
		_draw_torches(canvas, frame)


func _draw_fog(canvas: CanvasItem) -> void:
	for cloud: Dictionary in fog:
		var size := float(cloud.size)
		var color: Color = cloud.color
		RenderCache.draw_glow(
			canvas, cloud.pos, size, Color(color.r, color.g, color.b, color.a * 0.5)
		)


func _draw_river(canvas: CanvasItem, frame: int) -> void:
	if river.size() < 2:
		return
	var glow := color_of(theme.get("river_glow", [80, 150, 200]))
	var foam := color_of(theme.get("river_foam", [180, 210, 230]))
	for index in range(0, river.size(), 10):
		var pulse := (sin(frame * 0.05 + index) + 1.0) * 0.5
		if pulse <= 0.5:
			continue
		var radius := maxf(1.0, pulse * 4.0)
		var pos := river[index]
		canvas.draw_circle(pos, radius * 2.0, Color(glow.r, glow.g, glow.b, 0.59 * pulse))
		canvas.draw_circle(pos, radius, Color(foam.r, foam.g, foam.b, 0.78 * pulse))


func _draw_shop_glow(canvas: CanvasItem, frame: int) -> void:
	var pulse := (sin(frame * 0.05) + 1.0) * 0.5
	var radius := 45.0 + pulse * 8.0
	RenderCache.draw_glow(
		canvas, RADIANT_SHOP + Vector2(0, -5), radius, Color(0.39, 0.78, 1.0, 0.35)
	)
	RenderCache.draw_glow(canvas, DIRE_SHOP + Vector2(0, -5), radius, Color(1.0, 0.31, 0.31, 0.35))


func _draw_shop_smoke(canvas: CanvasItem, frame: int) -> void:
	for shop: Vector2 in [RADIANT_SHOP, DIRE_SHOP]:
		var chimney := shop + Vector2(19, -32)
		for index in range(3):
			var phase := fmod(frame * 0.03 + index * 2.0, 6.0)
			var pos := chimney + Vector2(sin(phase * 2.0 + index) * 3.0, -phase * 8.0)
			var size := 3.0 - floorf(phase / 2.0)
			if size > 0:
				canvas.draw_circle(
					pos, size * 2.0, Color(0.4, 0.4, 0.43, (180.0 - phase * 25.0) / 255.0)
				)


func _draw_particles(canvas: CanvasItem) -> void:
	var kind := str(theme.get("particle_type", "firefly"))
	for particle: Dictionary in particles:
		var pos: Vector2 = particle.pos
		var color: Color = particle.color
		var size := float(particle.size)
		var phase := float(particle.phase)
		match kind:
			"firefly":
				var brightness := (sin(phase) + 1.0) * 0.5
				if brightness < 0.3:
					continue
				if brightness > 0.7:
					RenderCache.draw_glow(
						canvas, pos, (size + 2.0) * 2.0, Color(color.r, color.g, color.b, 0.47)
					)
				canvas.draw_circle(pos, size, Color(color.r, color.g, color.b, brightness))
			"snow":
				canvas.draw_circle(pos, size, Color(color.r, color.g, color.b, 0.8))
			"sand":
				canvas.draw_rect(
					Rect2(pos, Vector2(size + 1, 1)), Color(color.r, color.g, color.b, 0.6)
				)
			"ember":
				canvas.draw_circle(pos, size, Color(color.r, color.g, color.b, 0.9))
			"acid":
				canvas.draw_circle(pos, size + 1.0, color)
				canvas.draw_rect(Rect2(pos + Vector2(0, -1), Vector2.ONE), Color(0.88, 1.0, 0.59))
			"ash":
				canvas.draw_rect(Rect2(pos, Vector2(size + 1, size + 1)), color)
				if sin(phase * 1.7) > 0.7:
					canvas.draw_rect(Rect2(pos, Vector2.ONE), Color(0.92, 0.39, 0.45))
			"spirit":
				RenderCache.draw_glow(canvas, pos, 8.0, Color(color.r, color.g, color.b, 0.5))
				canvas.draw_circle(pos, 3.0, Color(color.r, color.g, color.b, 0.51))
			_:
				canvas.draw_circle(pos, size, color)


func _draw_torches(canvas: CanvasItem, frame: int) -> void:
	var identity := str(theme.get("boss_identity", ""))
	var flame := Color(1.0, 0.55, 0.2)
	if identity == "morthraxis":
		flame = Color(1.0, 0.35, 0.51)
	for index in range(torches.size()):
		var anchor: Array = torches[index]
		var pos := Vector2(float(anchor[0]), float(anchor[1]) - 6.0)
		var flicker := (frame / 6 + index) % 4
		var radius := 5.0 + float(flicker % 2) * 2.0
		RenderCache.draw_glow(
			canvas, pos, 22.0 + float(flicker % 2) * 3.0, Color(flame.r, flame.g, flame.b, 0.1)
		)
		canvas.draw_circle(pos, radius, flame)
		canvas.draw_circle(pos + Vector2(0, -2), radius * 0.45, Color(1.0, 0.9, 0.6))


func shop_at(pos: Vector2) -> String:
	if Rect2(RADIANT_SHOP - Vector2.ONE * SHOP_SIZE * 0.5, Vector2.ONE * SHOP_SIZE).has_point(pos):
		return "item"
	if Rect2(DIRE_SHOP - Vector2.ONE * SHOP_SIZE * 0.5, Vector2.ONE * SHOP_SIZE).has_point(pos):
		return "hero"
	return ""


func is_click_on_shop(pos: Vector2) -> bool:
	return not shop_at(pos).is_empty()


func get_lane_path(data: CoreData, lane: String) -> PackedVector2Array:
	return data.lane(lane)


func get_shop_positions() -> Dictionary:
	return {"radiant": RADIANT_SHOP, "dire": DIRE_SHOP, "size": SHOP_SIZE}


func particle_count() -> int:
	return particles.size()
