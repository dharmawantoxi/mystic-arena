extends RefCounted
## Baked source hero bodies for all 222 roster heroes. `Hero.draw` keeps the HP bar,
## name badge and rings outside the atlas. Every hero has a blue source atlas; the six
## non-boss heroes have red sheets too. Red boss-heroes reuse `BossArt` at the source
## hero scale, avoiding duplicate images while retaining every animated pose.

const BossArt = preload("res://scripts/ui/boss_art.gd")
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
	return ROOT + name + ".webp"


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


static func _nearest_skill(rows: Dictionary, pose: String, facing: float) -> String:
	var parts := pose.split("_")
	if parts.size() != 3:
		return ""
	var prefix := "skill_%s_" % parts[1]
	var wanted := int(parts[2])
	var best := ""
	var best_distance := 1 << 30
	for candidate in rows:
		var key := String(candidate)
		var candidate_pose := key.get_slice(":", 0)
		if not candidate_pose.begins_with(prefix) or key != frame_key(candidate_pose, facing):
			continue
		var distance := absi(int(candidate_pose.substr(prefix.length())) - wanted)
		if distance < best_distance:
			best = key
			best_distance = distance
	return best


## The key to look up for `pose`: heroes whose renderer never reports movement have no
## walk poses (they show the idle pose), and an attack timer past the baked range uses
## the nearest earlier attack pose.
static func resolve(rows: Dictionary, pose: String, facing: float) -> String:
	var key := frame_key(pose, facing)
	if rows.has(key):
		return key
	if pose.begins_with("walk"):
		return resolve(rows, "idle" + pose.substr(4), facing)
	if pose.begins_with("skill_"):
		return _nearest_skill(rows, pose, facing)
	if pose.begins_with("atk"):
		var index := int(pose.substr(3)) - 1
		while index >= 0:
			var earlier := frame_key("atk%d" % index, facing)
			if rows.has(earlier):
				return earlier
			index -= 1
	return ""


static func _shared_boss_frame(
	hero_id: String, team: int, pose: String, facing_value: float
) -> Dictionary:
	var shared: Array = manifest().get("shared_red_bosses", [])
	if team == BLUE or not shared.has(hero_id):
		return {}
	var direction := 1 if facing_value >= 0.0 else -1
	var art := BossArt.frame(hero_id, direction, pose)
	if art.is_empty():
		return {}
	var facts := meta(hero_id)
	art["scale"] = float(facts.get("hero_scale", 1.0))
	return art


static func _boss_skill_frame(hero_id: String, pose: String, facing_value: float) -> Dictionary:
	var shared: Array = manifest().get("shared_red_bosses", [])
	if not shared.has(hero_id):
		return {}
	var row: Dictionary = BossArt.entries().get(hero_id, {})
	var skills: Dictionary = row.get("skills", {})
	if not skills.has(pose.get_slice("_", 1)):
		return {}
	var direction := 1 if facing_value >= 0.0 else -1
	var art := BossArt.frame(hero_id, direction, pose)
	if art.is_empty():
		return {}
	art["scale"] = float(meta(hero_id).get("hero_scale", 1.0))
	return art


## `{texture, src, anchor, scale, pose}` for a pose, or `{}` when not imported.
static func frame(hero_id: String, team: int, pose: String, facing: float) -> Dictionary:
	if pose.begins_with("skill_"):
		var skill_art := _boss_skill_frame(hero_id, pose, facing)
		if not skill_art.is_empty():
			return skill_art
	var name := atlas_name(hero_id, team)
	var listed := section("atlases")
	if not listed.has(name):
		if pose.begins_with("skill_"):
			return {}
		return _shared_boss_frame(hero_id, team, pose, facing)
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
		"scale": 1.0,
		"pose": key,
	}
