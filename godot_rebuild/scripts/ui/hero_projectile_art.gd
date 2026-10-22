extends RefCounted
## Source-baked hero projectile frames from `_entity.Hero._draw_projectile`.

const MANIFEST_PATH := "res://data/art/hero_projectiles.json"
const TEXTURE_PREFIX := "res://assets/art/hero_projectiles/"
const DEFAULT_CELL_SIZE := 64
const ATLAS_COLUMNS := 64
const COLUMN_SHIFT := 6
const DIRECTION_STEPS := 32

var draw_count := 0
var _manifest: Dictionary = {}
var _textures: Dictionary = {}


func _init() -> void:
	if not FileAccess.file_exists(MANIFEST_PATH):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
	if parsed is Dictionary:
		_manifest = parsed


func manifest_data() -> Dictionary:
	return _manifest.duplicate(true)


func frame_for(hero_type: String, age: int, angle: float, damage: int, is_crit: bool) -> Dictionary:
	if _manifest.is_empty():
		return {}
	var atlas_name := _style_for(hero_type, damage, is_crit)
	var atlases: Dictionary = _manifest.get("atlases", {})
	var atlas: Dictionary = atlases.get(atlas_name, {})
	if atlas.is_empty():
		return {}
	var frame_index := -1
	if atlas_name == "generic":
		var hero_frames: Dictionary = atlas.get("hero_frames", {})
		var variants: Dictionary = hero_frames.get(hero_type, {})
		var variant_name := "crit" if is_crit else "normal"
		frame_index = int(variants.get(variant_name, -1))
	else:
		var age_frames := int(atlas.get("age_frames", 1))
		var direction_count := int(atlas.get("directions", 1))
		var frame_age := clampi(age, 0, age_frames - 1)
		var direction_index := 0
		if direction_count > 1:
			direction_index = _direction_index(angle)
		frame_index = frame_age * direction_count + direction_index
	if frame_index < 0 or frame_index >= int(atlas.get("frames", 0)):
		return {}
	return {"atlas": atlas_name, "index": frame_index}


func draw(
	canvas: CanvasItem,
	hero_type: String,
	position: Vector2,
	angle: float,
	age: int,
	damage: int,
	is_crit: bool
) -> bool:
	var frame := frame_for(hero_type, age, angle, damage, is_crit)
	if frame.is_empty():
		return false
	var atlas_name: String = String(frame["atlas"])
	var atlases: Dictionary = _manifest.get("atlases", {})
	var atlas: Dictionary = atlases.get(atlas_name, {})
	var texture: Texture2D = _texture(atlas_name, atlas)
	if texture == null:
		return false
	var index: int = int(frame["index"])
	var cell_size := int(atlas.get("cell", DEFAULT_CELL_SIZE))
	var column := index & (ATLAS_COLUMNS - 1)
	var row := index >> COLUMN_SHIFT
	var source := Rect2(column * cell_size, row * cell_size, cell_size, cell_size)
	var size := Vector2(cell_size, cell_size)
	canvas.draw_texture_rect_region(texture, Rect2(position - size * 0.5, size), source)
	draw_count += 1
	return true


func _style_for(hero_type: String, damage: int, is_crit: bool) -> String:
	match hero_type:
		"sylara":
			return "sylara"
		"vex":
			return "vex_skill" if damage <= 0 else "vex_attack"
		"zephyr":
			return "zephyr_crit" if is_crit else "zephyr_basic"
		"morgath":
			return "morgath"
		"ancient_apparition":
			return "ancient_apparition"
		_:
			return "generic"


func _direction_index(angle: float) -> int:
	var turns := fposmod(angle, TAU) / TAU
	return int(floor(turns * float(DIRECTION_STEPS) + 0.5)) % DIRECTION_STEPS


func _texture(atlas_name: String, atlas: Dictionary) -> Texture2D:
	if _textures.has(atlas_name):
		return _textures[atlas_name] as Texture2D
	var file_name := String(atlas.get("file", ""))
	if file_name.is_empty():
		return null
	var path := TEXTURE_PREFIX + file_name
	if not ResourceLoader.exists(path):
		return null
	var loaded: Texture2D = ResourceLoader.load(path) as Texture2D
	if loaded != null:
		_textures[atlas_name] = loaded
	return loaded
