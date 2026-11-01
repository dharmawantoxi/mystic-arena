class_name Diagnostics
extends RefCounted

const COOLDOWN_MS := 2000
const LOG_PATH := "user://crash_log.txt"
var _last_log: Dictionary = {}


func report(kind: String, message: String, now_ms: int) -> bool:
	if now_ms - int(_last_log.get(kind, -COOLDOWN_MS)) < COOLDOWN_MS:
		return false
	_last_log[kind] = now_ms
	var text := (
		"\n===== %s | %s =====\n%s\n" % [Time.get_datetime_string_from_system(), kind, message]
	)
	push_error("[%s] %s" % [kind, message])
	var file := FileAccess.open(LOG_PATH, FileAccess.READ_WRITE)
	if file == null:
		file = FileAccess.open(LOG_PATH, FileAccess.WRITE)
	if file != null:
		file.seek_end()
		file.store_string(text)
	return true
