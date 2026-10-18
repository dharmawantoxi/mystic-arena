extends RefCounted
## Layer 9bq: baked source boss bodies. `Boss.draw` paints auras, a ground shadow, the body (the
## sprite `heroes._boss_render_sprite_fast` caches per `_boss_cache_key`), then the HP bar and name
## plate above the sprite top (`BOSS_LABEL_TOP`). `bake/bake_boss_atlas.py` bakes the standing
## pose, phase 0, in both facings for each of the 216 bosses (one PNG per boss, crops side by side).

const ROOT := "res://assets/art/bosses/"
const MANIFEST := "res://data/art/bosses.json"
static var _manifest: Dictionary = {}
static var _textures: Dictionary = {}


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func entries() -> Dictionary:
	var listed: Dictionary = manifest().get("bosses", {})
	return listed


static func has_boss(boss_type: String) -> bool:
	return entries().has(boss_type)


static func path_for(boss_type: String) -> String:
	return ROOT + boss_type + ".png"


## `_boss_cache_key`: `facing = 1 if int(direction or -1) >= 0 else -1`, i.e. only a positive
## direction faces right.
static func facing(direction: int) -> int:
	return 1 if direction > 0 else -1


static func texture(boss_type: String) -> Texture2D:
	if not has_boss(boss_type):
		return null
	if not _textures.has(boss_type):
		var loaded: Texture2D = null
		if ResourceLoader.exists(path_for(boss_type)):
			loaded = load(path_for(boss_type)) as Texture2D
		_textures[boss_type] = loaded
	var cached: Variant = _textures[boss_type]
	return cached as Texture2D


## `Boss.draw`: `head_top = max(int(BOSS_LABEL_TOP.get(boss_type, r)), r)`.
static func label_top(boss_type: String, radius: int) -> int:
	var row: Dictionary = entries().get(boss_type, {})
	return maxi(int(row.get("label_top", radius)), radius)


## `{texture, src, anchor}` for the boss body, or `{}` when it is not baked or not imported.
static func frame(boss_type: String, direction: int) -> Dictionary:
	var sheet := texture(boss_type)
	if sheet == null:
		return {}
	var row: Dictionary = entries()[boss_type]
	var frames: Dictionary = row["frames"]
	var cell: Array = frames[str(facing(direction))]
	return {
		"texture": sheet,
		"src": Rect2(float(cell[0]), float(cell[1]), float(cell[2]), float(cell[3])),
		"anchor": Vector2(float(cell[4]), float(cell[5])),
	}
