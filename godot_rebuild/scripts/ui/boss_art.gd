extends RefCounted
## Animated source boss bodies from `bake/bake_boss_atlas.py`: eight idle phases,
## walk/attack keyframes and source smart-skill keyframes in lossless WebP sheets.
## `Boss.draw` keeps auras, shadow, HP bar and name plate outside the body atlas.

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
	return ROOT + boss_type + ".webp"


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


static func frame_key(pose: String, facing_value: int) -> String:
	return "%s:%d" % [pose, facing_value]


static func _pose_parts(pose: String) -> Array:
	if pose.begins_with("skill_"):
		var parts := pose.split("_")
		if parts.size() == 3:
			return ["skill_" + parts[1], int(parts[2])]
		return ["", 0]
	var index := 0
	while index < pose.length() and not pose[index].is_valid_int():
		index += 1
	if index == pose.length():
		return [pose, 0]
	return [pose.substr(0, index), int(pose.substr(index))]


static func _nearest(rows: Dictionary, pose: String, facing_value: int) -> String:
	var wanted := _pose_parts(pose)
	var best := ""
	var best_distance := 1 << 30
	for candidate in rows:
		var key := String(candidate)
		if not key.ends_with(":%d" % facing_value):
			continue
		var parts := _pose_parts(key.get_slice(":", 0))
		if parts[0] != wanted[0]:
			continue
		var distance := absi(int(parts[1]) - int(wanted[1]))
		if distance < best_distance:
			best = key
			best_distance = distance
	return best


static func resolve(rows: Dictionary, pose: String, facing_value: int) -> String:
	var key := frame_key(pose, facing_value)
	if rows.has(key):
		return key
	if pose.begins_with("walk"):
		var idle := frame_key("idle" + pose.substr(4), facing_value)
		if rows.has(idle):
			return idle
	var nearest := _nearest(rows, pose, facing_value)
	if not nearest.is_empty():
		return nearest
	var fallback := frame_key("idle0", facing_value)
	return fallback if rows.has(fallback) else ""


## `{texture, src, anchor, pose}` for a source keyframe, or `{}` when not imported.
static func frame(boss_type: String, direction: int, pose: String = "idle0") -> Dictionary:
	var sheet := texture(boss_type)
	if sheet == null:
		return {}
	var row: Dictionary = entries()[boss_type]
	var frames: Dictionary = row["frames"]
	var key := resolve(frames, pose, facing(direction))
	if key.is_empty():
		return {}
	var cell: Array = frames[key]
	return {
		"texture": sheet,
		"src": Rect2(float(cell[0]), float(cell[1]), float(cell[2]), float(cell[3])),
		"anchor": Vector2(float(cell[4]), float(cell[5])),
		"pose": key,
	}
