extends RefCounted
## Langkah 3: baca data level dari JSON.

static func load_level(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("[LevelDB] File tidak ada: " + path)
		return {}
	var text: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("[LevelDB] JSON rusak: " + path)
		return {}
	return parsed
