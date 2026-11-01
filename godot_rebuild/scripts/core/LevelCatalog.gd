class_name LevelCatalog
extends RefCounted

## Generated from Python's level metadata; contains no combat implementation.
var entries: Array[Dictionary] = []


func _init() -> void:
	var file := FileAccess.open("res://data/levels.json", FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Array:
		return
	for item: Variant in parsed:
		if item is Dictionary and item.has("level_number") and item.has("name"):
			entries.append(item)
	entries.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool: return a.level_number < b.level_number
	)


func contains(level: int) -> bool:
	return entries.any(func(entry: Dictionary) -> bool: return int(entry.level_number) == level)


func next_after(level: int) -> int:
	for index in range(entries.size()):
		if int(entries[index].level_number) == level:
			return int(entries[index + 1].level_number) if index + 1 < entries.size() else 0
	return 0


func name_of(level: int) -> String:
	for entry: Dictionary in entries:
		if int(entry.level_number) == level:
			return str(entry.name)
	return "Level %d" % level
