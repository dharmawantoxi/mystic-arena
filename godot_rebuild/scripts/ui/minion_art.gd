extends RefCounted
## Layer 9bk: baked source minion sprites. `minions/_bundle.py::cached_minion_draw`
## renders each body once per key (type, team, nexus level, pose, direction, ...) and
## blits the cropped result; `bake/bake_minion_atlas.py` drives the real
## `Minion.draw` for those keys and packs them, one atlas per (type, team, level).

const ROOT := "res://assets/art/minions/"
const MANIFEST := "res://data/art/minions.json"
const BLUE := 0
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


static func team_name(team: int) -> String:
	return "blue" if team == BLUE else "red"


static func atlas_name(type_id: String, team: int, level: int) -> String:
	return "%s_%s_%d" % [type_id, team_name(team), clampi(level, 1, 5)]


static func atlas_path(name: String) -> String:
	return ROOT + name + ".png"


## The atlas image, or null when it is unknown or not imported yet.
static func atlas_texture(name: String) -> Texture2D:
	if not atlases().has(name):
		return null
	if not _textures.has(name):
		var texture: Texture2D = null
		if ResourceLoader.exists(atlas_path(name)):
			texture = load(atlas_path(name)) as Texture2D
		_textures[name] = texture
	var cached: Variant = _textures[name]
	return cached as Texture2D


## Frame key as the atlas stores it, e.g. `walk3:-1` (pose, then direction).
static func frame_key(pose: String, facing: float) -> String:
	return "%s:%d" % [pose, 1 if facing >= 0.0 else -1]


## `{texture, src, anchor}` for one pose, or `{}` when the art is unavailable. Blit
## `src` at `position - anchor`, like the source's `surface.blit(sprite, (x - ax, y - ay))`.
static func frame(
	type_id: String, team: int, level: int, pose: String, facing: float
) -> Dictionary:
	var name := atlas_name(type_id, team, level)
	var listed := atlases()
	if not listed.has(name):
		return {}
	var entry: Dictionary = listed[name]
	var rows: Dictionary = entry["frames"]
	var key := frame_key(pose, facing)
	if not rows.has(key):
		return {}
	var texture := atlas_texture(name)
	if texture == null:
		return {}
	var row: Array = rows[key]
	return {
		"texture": texture,
		"src": Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3])),
		"anchor": Vector2(float(row[4]), float(row[5])),
	}
