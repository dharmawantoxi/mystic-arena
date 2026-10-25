extends Control
## Layer 9bs: live two-speed fog and the source menu's 64 drifting ember/arcane particles.

const MenuBackdrop = preload("res://scripts/ui/menu_backdrop.gd")
const MenuAmbientLayout = preload("res://scripts/ui/menu_ambient_layout.gd")
const MENU_MANIFEST := "res://data/art/menu.json"
const FOG := "res://assets/art/menu/menu_fog.png"
const MAX_CATCH_UP_STEPS := 12

var animation_time := 0.0
var ambient_draws := 0
var fog_draws := 0
var particle_draws := 0
var _fog_texture: Texture2D
var _menu_manifest: Dictionary = {}
var _particles: Array[Dictionary] = []
var _rng := RandomNumberGenerator.new()
var _frame_accumulator := 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rng.randomize()
	_particles = MenuAmbientLayout.create_particles(_rng)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MENU_MANIFEST))
	if parsed is Dictionary:
		_menu_manifest = parsed
	if ResourceLoader.exists(FOG):
		_fog_texture = load(FOG) as Texture2D
	resized.connect(queue_redraw)
	queue_redraw()


func _process(delta: float) -> void:
	_frame_accumulator += maxf(0.0, delta) * 60.0
	var steps := mini(MAX_CATCH_UP_STEPS, int(_frame_accumulator))
	if steps <= 0:
		return
	_frame_accumulator -= float(steps)
	for _index in range(steps):
		animation_time += 1.0
		MenuAmbientLayout.advance(_particles, 1.0, Callable(self, "_random_wrap_x"))
	queue_redraw()


func particle_snapshot() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for particle in _particles:
		result.append(particle.duplicate(true))
	return result


func _draw() -> void:
	ambient_draws += 1
	fog_draws = 0
	particle_draws = 0
	var cover := MenuBackdrop.cover_rect(size)
	var factor := cover.size.x / MenuAmbientLayout.SOURCE_WIDTH
	draw_set_transform(cover.position, 0.0, Vector2(factor, factor))
	_draw_fog()
	_draw_particles()
	draw_set_transform(Vector2.ZERO)


func _draw_fog() -> void:
	if _fog_texture == null:
		return
	var fog: Dictionary = _menu_manifest.get("fog", {})
	var layers: Array = fog.get("layers", [])
	var frames: Dictionary = fog.get("frames", {})
	var source_size: Array = fog.get("source_size", [1500, 720])
	var width := int(source_size[0])
	var height := int(source_size[1])
	if width <= 0 or height <= 0:
		return
	for index in range(mini(layers.size(), 2)):
		var layer: Dictionary = layers[index]
		var frame_data: Array = frames.get("layer_%d" % index, [])
		if frame_data.size() != 4:
			continue
		var source := Rect2(
			float(frame_data[0]), float(frame_data[1]), float(frame_data[2]), float(frame_data[3])
		)
		var speed := float(layer.get("speed", 0.0))
		var alpha := (
			float(MenuAmbientLayout.fog_alpha(int(layer.get("alpha", 0)), animation_time, index))
			/ 255.0
		)
		var offset := MenuAmbientLayout.fog_offset(animation_time, speed, width)
		draw_texture_rect_region(
			_fog_texture,
			Rect2(-float(offset), 0.0, float(width), float(height)),
			source,
			Color(1.0, 1.0, 1.0, alpha)
		)
		draw_texture_rect_region(
			_fog_texture,
			Rect2(float(width - offset), 0.0, float(width), float(height)),
			source,
			Color(1.0, 1.0, 1.0, alpha)
		)
		fog_draws += 2


func _draw_particles() -> void:
	particle_draws = _particles.size()
	for particle in _particles:
		var size_px := int(particle.get("size", 1))
		var position := Vector2(
			int(float(particle.get("x", 0.0))), int(float(particle.get("y", 0.0)))
		)
		var rgb: Array = particle.get("color", [255, 255, 255])
		var alpha := MenuAmbientLayout.particle_alpha(particle, animation_time)
		var red := int(rgb[0])
		var green := int(rgb[1])
		var blue := int(rgb[2])
		draw_circle(
			position, float(size_px * 2), Color8(red, green, blue, alpha / 4), true, -1.0, false
		)
		draw_circle(position, float(size_px), Color8(red, green, blue, alpha), true, -1.0, false)


func _random_wrap_x() -> float:
	return _rng.randf_range(0.0, MenuAmbientLayout.SOURCE_WIDTH)
