extends RefCounted
## Layer 9bo: baked source hero bodies. `heroes/__init__.py::render_hero` caches one cropped
## body per key (type, team, level, facing, idle | attack, phase | timer // 3, moving) and
## `Hero.draw` paints the HP bar, name badge and rings around it. Level never changes the
## body (identical pixels at levels 1, 3, 8, 15), so one set serves every level.
## `bake/bake_hero_atlas.py` drives the real `Hero.draw` and packs one atlas per (hero, team).

const ROOT := "res://assets/art/heroes/"
const MANIFEST := "res://data/art/heroes.json"
const BLUE := 0
const ATK_QUANT := 3
static var _manifest: Dictionary = {}
static var _textures: Dictionary = {}


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func section(name: String) -> Dictionary:
	var listed: Dictionary = manifest().get(name, {})
	return listed


## Source facts about a baked hero (`name`, `radius`, `top_offset`, `cooldown`), or `{}`.
static func meta(hero_id: String) -> Dictionary:
	var listed := section("meta")
	if not listed.has(hero_id):
		return {}
	var row: Dictionary = listed[hero_id]
	return row


static func has_hero(hero_id: String) -> bool:
	return section("meta").has(hero_id)


static func team_name(team: int) -> String:
	return "blue" if team == BLUE else "red"


static func atlas_name(hero_id: String, team: int) -> String:
	return "%s_%s" % [hero_id, team_name(team)]


static func atlas_path(name: String) -> String:
	return ROOT + name + ".png"


static func atlas_texture(name: String) -> Texture2D:
	if not section("atlases").has(name):
		return null
	if not _textures.has(name):
		var texture: Texture2D = null
		if ResourceLoader.exists(atlas_path(name)):
			texture = load(atlas_path(name)) as Texture2D
		_textures[name] = texture
	var cached: Variant = _textures[name]
	return cached as Texture2D


static func frame_key(pose: String, facing: float) -> String:
	return "%s:%d" % [pose, 1 if facing >= 0.0 else -1]


## The key to look up for `pose`: heroes whose renderer never reports movement have no
## walk poses (they show the idle pose), and an attack timer past the baked range uses
## the nearest earlier attack pose.
static func resolve(rows: Dictionary, pose: String, facing: float) -> String:
	var key := frame_key(pose, facing)
	if rows.has(key):
		return key
	if pose.begins_with("walk"):
		return resolve(rows, "idle" + pose.substr(4), facing)
	if pose.begins_with("atk"):
		var index := int(pose.substr(3)) - 1
		while index >= 0:
			var earlier := frame_key("atk%d" % index, facing)
			if rows.has(earlier):
				return earlier
			index -= 1
	return ""


## `{texture, src, anchor}` for a pose, or `{}` when the hero is not baked or not imported.
static func frame(hero_id: String, team: int, pose: String, facing: float) -> Dictionary:
	var name := atlas_name(hero_id, team)
	var listed := section("atlases")
	if not listed.has(name):
		return {}
	var entry: Dictionary = listed[name]
	var rows: Dictionary = entry["frames"]
	var key := resolve(rows, pose, facing)
	if key.is_empty():
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
