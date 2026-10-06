extends RefCounted
## Source level_data.get_level_config / is_level_unlocked / get_next_level.
## Catalog only: selecting these entries does not make levels 2-54 playable.

const COUNT := 54
const LEVEL_ONE := "res://data/levels/level_1.json"


static func get_level_config(number: int) -> Dictionary:
	if number < 1 or number > COUNT:
		return {}
	var path := LEVEL_ONE.get_base_dir().path_join("level_%d.json" % number)
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not (parsed is Dictionary):
		return {}
	var config: Dictionary = parsed
	if int(config.get("level_number", -1)) != number:
		return {}
	return config


static func is_level_unlocked(number: int, completed: Array[int]) -> bool:
	var config := get_level_config(number)
	if config.is_empty():
		return false
	var required: Variant = config.get("unlock_after_level")
	return required == null or int(required) in completed


static func get_next_level(current: int) -> int:
	var number := current + 1
	return number if not get_level_config(number).is_empty() else -1
