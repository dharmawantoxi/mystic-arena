extends RefCounted
## Port of `main.py::_log_frame_error` (layer 9cn).
##
## pygame wraps every simulation step and every draw call in `try/except` and, on
## failure, writes the traceback to stdout **and** appends it to `crash_log.txt`
## in the writable directory — rate-limited to one entry per kind every
## `_FRAME_ERR_COOLDOWN` (2.0 s) so a repeating error does not flood logcat.
##
## GDScript has no `try/except` for engine errors, so this module ports the part
## that is portable and observable: the rate limiter, the exact header format and
## the append-only log file. Callers are the places where the shell would have
## caught an exception anyway (a screen that failed to configure, a save that
## failed to load) — see `docs/MAIN_ENTRYPOINT_MIGRATION.md` D1.

## `_FRAME_ERR_COOLDOWN = 2.0` in the source.
const COOLDOWN_SECONDS := 2.0
## `os.path.join(plat.get_writable_dir(), "crash_log.txt")`.
const LOG_NAME := "crash_log.txt"

## `_FRAME_ERR_LAST = {"update": 0.0, "draw": 0.0}` — kind -> last write time.
var last_written: Dictionary = {}
var log_path := "user://crash_log.txt"


func _init(path: String = "user://crash_log.txt") -> void:
	log_path = path


## `"[FRAME ERROR:%s]\n%s" % (kind, traceback.format_exc())`.
static func text(kind: String, message: String) -> String:
	return "[FRAME ERROR:%s]\n%s" % [kind, message]


## `"\n===== %s =====\n%s" % (time.strftime(...), text)`.
static func section(stamp: String, kind: String, message: String) -> String:
	return "\n===== %s =====\n%s" % [stamp, text(kind, message)]


## True when `kind` is still inside its 2 s cooldown at `now` (seconds).
func throttled(kind: String, now: float) -> bool:
	var previous: float = float(last_written.get(kind, 0.0))
	return now - previous < COOLDOWN_SECONDS


## Records one entry. Returns false when the cooldown swallowed it or the file
## could not be opened, which is how the source behaves (it only prints/writes).
func record(
	kind: String, message: String, now: float, stamp: String = "", directory: String = ""
) -> bool:
	if throttled(kind, now):
		return false
	last_written[kind] = now
	var stamp_text := stamp if not stamp.is_empty() else timestamp()
	var payload := text(kind, message)
	print(payload)
	var path := log_path
	if not directory.is_empty():
		path = directory.path_join(LOG_NAME)
	var file := FileAccess.open(path, FileAccess.READ_WRITE)
	if file == null:
		return false
	file.seek_end()
	file.store_string(section(stamp_text, kind, message))
	file.close()
	return true


## `time.strftime("%Y-%m-%d %H:%M:%S")` on the wall clock. Live calls read the
## local clock like Python (`get_datetime_dict_from_system`); an explicit
## timestamp is interpreted as UTC so tests stay deterministic (D2).
static func timestamp(now_unix: int = -1) -> String:
	var parts: Dictionary
	if now_unix < 0:
		parts = Time.get_datetime_dict_from_system()
	else:
		parts = Time.get_datetime_dict_from_unix_time(now_unix)
	return "%04d-%02d-%02d %02d:%02d:%02d" % [
		int(parts.year),
		int(parts.month),
		int(parts.day),
		int(parts.hour),
		int(parts.minute),
		int(parts.second),
	]


## Whole log contents, or "" when nothing was written yet.
func read_log() -> String:
	if not FileAccess.file_exists(log_path):
		return ""
	return FileAccess.get_file_as_string(log_path)


## Source starts with an empty table, so the first write of every kind passes
## even at `now = 0.0` only when the source would also pass (`0 - 0 < 2.0` is
## true, so the source swallows it too). `reset` keeps the native tests honest.
func reset() -> void:
	last_written.clear()
