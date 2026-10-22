extends RefCounted
## Layer 9bt: source-baked minion slash arcs and death animations. The PNG atlas is
## rendered by the original `_spawn_slash_effect`, `draw_slash_effects`, and
## `_draw_death_animation`; simple painters below remain for an unimported PNG.

const ROOT := "res://assets/art/minion_combat_fx/"
const MANIFEST := "res://data/art/minion_combat_fx.json"
const ANGLE_STEPS := 32
const SLASH_LIFE := 12
const DEATH_LIFE := 20
static var _manifest: Dictionary = {}
static var _textures: Dictionary = {}


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func atlases() -> Dictionary:
	var listed: Dictionary = manifest().get("atlases", {})
	return listed


static func atlas_path(type_id: String) -> String:
	return ROOT + type_id + ".png"


## The type atlas, or null when unknown or not imported yet.
static func atlas_texture(type_id: String) -> Texture2D:
	if not atlases().has(type_id):
		return null
	if not _textures.has(type_id):
		var texture: Texture2D = null
		var path := atlas_path(type_id)
		if ResourceLoader.exists(path):
			texture = load(path) as Texture2D
		_textures[type_id] = texture
	var cached: Variant = _textures[type_id]
	return cached as Texture2D


## `{texture, src, anchor, key}` or `{}` while the PNG is unavailable.
static func frame(type_id: String, key: String) -> Dictionary:
	var listed := atlases()
	if not listed.has(type_id):
		return {}
	var entry: Dictionary = listed[type_id]
	var rows: Dictionary = entry.get("frames", {})
	if not rows.has(key):
		return {}
	var texture := atlas_texture(type_id)
	if texture == null:
		return {}
	var row: Array = rows[key]
	return {
		"texture": texture,
		"src": Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3])),
		"anchor": Vector2(float(row[4]), float(row[5])),
		"key": key,
	}


static func angle_index(angle: float) -> int:
	var step := int(floor(fposmod(angle, TAU) * float(ANGLE_STEPS) / TAU + 0.5))
	return posmod(step, ANGLE_STEPS)


static func slash_frame(type_id: String, life: int, angle: float) -> Dictionary:
	if life <= 0:
		return {}
	var index := angle_index(angle)
	var key := "slash%02d:%02d" % [clampi(life, 1, SLASH_LIFE), index]
	return frame(type_id, key)


static func death_frame(type_id: String, life: int) -> Dictionary:
	if life <= 0:
		return {}
	return frame(type_id, "death%02d" % clampi(life, 1, DEATH_LIFE))


## Returns true when the source-baked PNG was drawn; otherwise the old vector fallback
## draws the same kind of effect and the caller can keep a baked-path counter.
static func draw_slash(
	canvas: CanvasItem, type_id: String, point: Vector2, life: int, angle: float
) -> bool:
	if life <= 0:
		return false
	var art := slash_frame(type_id, life, angle)
	if art.is_empty():
		_draw_slash_fallback(canvas, type_id, point, life, angle)
		return false
	var texture: Texture2D = art["texture"]
	var src: Rect2 = art["src"]
	var anchor: Vector2 = art["anchor"]
	var origin := point - anchor
	canvas.draw_texture_rect_region(texture, Rect2(origin, src.size), src, Color.WHITE)
	return true


static func draw_death(canvas: CanvasItem, type_id: String, point: Vector2, life: int) -> bool:
	if life <= 0:
		return false
	var art := death_frame(type_id, life)
	if art.is_empty():
		_draw_death_fallback(canvas, type_id, point, life)
		return false
	var texture: Texture2D = art["texture"]
	var src: Rect2 = art["src"]
	var anchor: Vector2 = art["anchor"]
	var origin := Vector2(int(point.x), int(point.y)) - anchor
	canvas.draw_texture_rect_region(texture, Rect2(origin, src.size), src, Color.WHITE)
	return true


static func _draw_slash_fallback(
	canvas: CanvasItem, type_id: String, point: Vector2, life: int, angle: float
) -> void:
	var progress := 1.0 - float(life) / float(SLASH_LIFE)
	var alpha := float(int(220.0 * float(life) / float(SLASH_LIFE))) / 255.0
	var distance := 18.0
	var listed := atlases()
	if listed.has(type_id):
		var entry: Dictionary = listed[type_id]
		distance = float(entry.get("slash_distance", distance))
	var radius := distance + progress * 6.0
	var points := PackedVector2Array()
	for index in range(7):
		var local_angle := angle - 0.55 + 1.1 * float(index) / 6.0
		points.append(point + Vector2(cos(local_angle), sin(local_angle)) * radius)
	canvas.draw_polyline(points, Color(1.0, 1.0, 1.0, alpha), 3.0, true)
	canvas.draw_polyline(points, Color(1.0, 230.0 / 255.0, 180.0 / 255.0, alpha), 1.0, true)


static func _draw_death_fallback(
	canvas: CanvasItem, type_id: String, point: Vector2, life: int
) -> void:
	var progress := 1.0 - float(life) / float(DEATH_LIFE)
	var alpha := int(float(life) / float(DEATH_LIFE) * 255.0)
	if alpha < 10:
		return
	var listed := atlases()
	var radius := 9.0
	if listed.has(type_id):
		var entry: Dictionary = listed[type_id]
		radius = float(entry.get("radius", radius))
	var center := Vector2(int(point.x), int(point.y))
	var fall := int(progress * 5.0)
	var scale := 1.0 - progress * 0.3
	canvas.draw_circle(center + Vector2(0, fall), radius * scale, Color8(50, 40, 40, alpha >> 1))
	if progress < 0.5:
		var red_alpha := clampi(int((0.5 - progress) * 300.0), 0, 200)
		canvas.draw_circle(
			center + Vector2(0, fall), radius * scale, Color8(255, 50, 50, red_alpha)
		)
	if progress < 0.7:
		var eye_alpha := clampi(int((0.7 - progress) * 400.0), 0, 255)
		var eye := Color8(255, 255, 255, eye_alpha)
		canvas.draw_line(center + Vector2(-6, fall - 2), center + Vector2(-2, fall + 2), eye, 1.0)
		canvas.draw_line(center + Vector2(-2, fall - 2), center + Vector2(-6, fall + 2), eye, 1.0)
		canvas.draw_line(center + Vector2(2, fall - 2), center + Vector2(6, fall + 2), eye, 1.0)
		canvas.draw_line(center + Vector2(6, fall - 2), center + Vector2(2, fall + 2), eye, 1.0)
