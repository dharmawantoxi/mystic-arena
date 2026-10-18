extends RefCounted
## Layer 9bl: baked source tower, castle and armor-crest sprites. `_entity.py` caches a
## tower body per key (type, team, level, facing, shoot flash // 3), draws the castle
## from one canvas scaled by 0.85 (gate-torch flames from level 4), and caches armor
## crests per (size, colour, ratio bucket, bright). `bake/bake_structure_atlas.py`
## drives that real code and packs the results.

const ROOT := "res://assets/art/structures/"
const MANIFEST := "res://data/art/structures.json"
const BLUE := 0
## Castle sprite size after the source's 0.85 smoothscale of its 180x160 canvas.
const CASTLE_WIDTH := 153
const CASTLE_HEIGHT := 136
## Source `y - 26` HP-bar fallback for a tower type without a `get_*_top_y` function.
const DEFAULT_TOP_Y := -26
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


static func team_name(team: int) -> String:
	return "blue" if team == BLUE else "red"


static func sheet_path(stem: String) -> String:
	return ROOT + stem + ".png"


static func sheet_texture(stem: String) -> Texture2D:
	if not _textures.has(stem):
		var texture: Texture2D = null
		if ResourceLoader.exists(sheet_path(stem)):
			texture = load(sheet_path(stem)) as Texture2D
		_textures[stem] = texture
	var cached: Variant = _textures[stem]
	return cached as Texture2D


## `{texture, src, anchor}` for `key` of one manifest entry, or `{}` without the art.
static func _frame(stem: String, entry: Dictionary, key: String) -> Dictionary:
	var rows: Dictionary = entry.get("frames", {})
	if not rows.has(key):
		return {}
	var texture := sheet_texture(stem)
	if texture == null:
		return {}
	var row: Array = rows[key]
	return {
		"texture": texture,
		"src": Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3])),
		"anchor": Vector2(float(row[4]), float(row[5])),
	}


static func tower_name(path_id: String, team: int, level: int) -> String:
	return "%s_%s_%d" % [path_id, team_name(team), level]


## One tower pose: `face` 1 when the target is to the right, `shoot_b` = flash // 3.
static func tower_frame(
	path_id: String, team: int, level: int, face: int, shoot_b: int
) -> Dictionary:
	var name := tower_name(path_id, team, level)
	var listed := section("towers")
	if not listed.has(name):
		return {}
	var entry: Dictionary = listed[name]
	return _frame("tower_" + name, entry, "%d:%d" % [face, shoot_b])


## Offset of the sprite's top above the tower origin (`get_*_top_y(0, 0, level)`).
static func tower_top_y(path_id: String, level: int) -> int:
	var levels: Dictionary = section("tower_top_y").get(path_id, {})
	return int(levels.get(str(level), DEFAULT_TOP_Y))


static func castle_name(team: int, level: int) -> String:
	return "%s_%d" % [team_name(team), clampi(level, 1, 5)]


## The castle for a nexus level; `flicker` 0..4 picks the gate-torch flame frame.
static func castle_frame(team: int, level: int, flicker: int) -> Dictionary:
	var name := castle_name(team, level)
	var listed := section("castles")
	if not listed.has(name):
		return {}
	var entry: Dictionary = listed[name]
	return _frame("castle_" + name, entry, str(flicker))


static func crest_bucket(ratio: float) -> int:
	return clampi(int(ratio * 10.0 + 0.5), 0, 10)


static func crest_frame(size: int, team: int, ratio: float, bright: bool) -> Dictionary:
	var key := "%d:%s:%d:%d" % [size, team_name(team), crest_bucket(ratio), 1 if bright else 0]
	return _frame("crests", section("crests"), key)
