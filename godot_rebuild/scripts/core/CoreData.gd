class_name CoreData
extends RefCounted

## Native access to data exported from _core.py and its pure data modules.
var data: Dictionary = {}
var archetypes: HeroArchetypes
var load_error := ""


func _init(
	path := "res://data/core_data.json", archetype_path := HeroArchetypes.DEFAULT_PATH
) -> void:
	archetypes = HeroArchetypes.new(archetype_path)
	if not archetypes.valid():
		load_error = archetypes.load_error
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		load_error = "Invalid core data JSON"
		return
	data = parsed


func valid() -> bool:
	return load_error.is_empty() and archetypes.valid() and data.get("schema", 0) == 1


func rule(key: String, fallback: Variant = null) -> Variant:
	return data.get("rules", {}).get(key, fallback)


func level(number: int) -> Dictionary:
	for row: Dictionary in data.get("levels", []):
		if int(row.get("level_number", 0)) == number:
			return row
	return {}


func hero(hero_type: String) -> Dictionary:
	return data.get("heroes", {}).get(hero_type, {})


func boss(boss_type: String) -> Dictionary:
	var bosses: Dictionary = data.get("bosses", {})
	if bosses.get("mini", {}).has(boss_type):
		return bosses.mini[boss_type]
	return bosses.get("true", {}).get(boss_type, {})


func item(item_id: String) -> Dictionary:
	return data.get("items", {}).get(item_id, {})


func lane(name: String) -> PackedVector2Array:
	var result := PackedVector2Array()
	for point: Array in data.get("lanes", {}).get(name, []):
		result.append(Vector2(float(point[0]), float(point[1])))
	return result


func color(value: Variant, fallback := Color.WHITE) -> Color:
	if value is Array and value.size() >= 3:
		return Color(float(value[0]) / 255.0, float(value[1]) / 255.0, float(value[2]) / 255.0)
	return fallback


func text(key: String, language := "id", args: Dictionary = {}) -> String:
	var table: Dictionary = data.get("localization", {}).get(language, {})
	var value := str(table.get(key, data.get("localization", {}).get("id", {}).get(key, key)))
	for arg: String in args:
		value = value.replace("{%s}" % arg, str(args[arg]))
	return value
