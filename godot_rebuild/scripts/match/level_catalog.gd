extends RefCounted
## Source `levels/level_data.py`: `ALL_LEVELS`, `get_level_config`,
## `get_level_count`, `is_level_unlocked` and `get_next_level`.
## Catalog only: selecting these entries does not make levels 2-54 playable.
##
## Deviations from the source helpers, both deliberate:
## * the source returns `None` for "no such level" / "no next level"; here
##   `get_level_config` returns an empty `Dictionary` and `get_next_level`
##   returns `-1`, so callers never have to type-check a `Variant`;
## * the source hands out the *same* mutable dict on every call; here every call
##   re-reads the JSON, so a caller cannot corrupt the catalog.

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


## Source `get_level_count()`: the number of entries in `ALL_LEVELS`.
static func count() -> int:
	return COUNT


## Source `ALL_LEVELS`, in order. Not cached: the source list is a module
## constant, but re-reading keeps the catalog stateless.
static func all_configs() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for number in range(1, COUNT + 1):
		var config := get_level_config(number)
		if not config.is_empty():
			out.append(config)
	return out


## Source `is_level_unlocked`: an unknown level is locked, `unlock_after_level`
## of `null` means always unlocked, anything else needs that level completed.
static func is_level_unlocked(number: int, completed: Array) -> bool:
	var config := get_level_config(number)
	if config.is_empty():
		return false
	var required: Variant = config.get("unlock_after_level")
	return required == null or completed.has(int(required))


static func get_next_level(current: int) -> int:
	var number := current + 1
	return number if not get_level_config(number).is_empty() else -1
