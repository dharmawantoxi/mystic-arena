extends RefCounted
## The `settings.py` half of `_core.py` as data.
##
## `_core.py` merges eight pygame modules into one 10.281 line file. Its first block
## (lines 28-1296) is `settings.py`: 139 plain constants — the screen and top bar size, the
## colour palette, the tower/shield/regen numbers, the minion and economy tuning, the shop
## prices and the meta rewards. Nothing in that block is a class or a behaviour, so instead
## of hand-copying 139 names into GDScript (where every typo is a silent drift) the block is
## executed for real by `tests/core_source_oracle.py` and shipped as
## `data/core/settings.json`.
##
## Godot modules that already pin one of these numbers keep their own `const` (that is how
## the rebuild has been written so far); `tests/core_checks.gd` compares each of those
## against this file, so the JSON and the live constants can never disagree silently.
##
## Sync: python3 godot_rebuild/tests/core_source_oracle.py --write

const DATA_PATH := "res://data/core/settings.json"

static var _constants: Dictionary = {}
static var _loaded := false


## Parses the shipped document; returns the constant map (empty when the file is missing).
static func reload(path: String = DATA_PATH) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	var found: Variant = {}
	if parsed is Dictionary:
		found = (parsed as Dictionary).get("constants", {})
	_constants = found if found is Dictionary else {}
	_loaded = not _constants.is_empty()
	return _constants


## Every constant of the `settings.py` block, keyed by its pygame name.
static func all() -> Dictionary:
	if not _loaded:
		reload()
	return _constants


static func count() -> int:
	return all().size()


static func has(name: String) -> bool:
	return all().has(name)


static func names() -> PackedStringArray:
	var out := PackedStringArray(all().keys())
	out.sort()
	return out


static func value(name: String, fallback: Variant = null) -> Variant:
	var constants := all()
	if constants.has(name):
		return constants[name]
	return fallback


static func number(name: String, fallback: float = 0.0) -> float:
	var raw: Variant = value(name)
	if raw is int or raw is float:
		return float(raw)
	return fallback


static func integer(name: String, fallback: int = 0) -> int:
	var raw: Variant = value(name)
	if raw is int or raw is float:
		return int(raw)
	return fallback


static func flag(name: String, fallback: bool = false) -> bool:
	var raw: Variant = value(name)
	if raw is bool:
		return bool(raw)
	return fallback


static func text(name: String, fallback: String = "") -> String:
	var raw: Variant = value(name)
	if raw is String:
		return str(raw)
	return fallback


## `(r, g, b)` / `(r, g, b, a)` tuples become colours; everything else takes the fallback.
static func color(name: String, fallback: Color = Color.WHITE) -> Color:
	var raw: Variant = value(name)
	if not (raw is Array):
		return fallback
	var channels: Array = raw
	if channels.size() == 3:
		return Color8(int(channels[0]), int(channels[1]), int(channels[2]))
	if channels.size() == 4:
		return Color8(
			int(channels[0]), int(channels[1]), int(channels[2]), int(channels[3])
		)
	return fallback


static func list(name: String) -> Array:
	var raw: Variant = value(name)
	if raw is Array:
		return raw
	return []


static func block(name: String) -> Dictionary:
	var raw: Variant = value(name)
	if raw is Dictionary:
		return raw
	return {}
