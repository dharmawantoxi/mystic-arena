extends RefCounted
## Layer 9bm: baked source build-slot markers. `BuildSlots.draw` blits one cached 40x38
## surface per empty slot at `(x - 20, y - 17)`: the blue slot in five glow-pulse
## variants (`int(round(sin(animation_time * 0.08) * 2))` = -2..2) and one static red
## slot. `bake/bake_slot_atlas.py` renders them with the real `BuildSlots` code.

const SHEET := "res://assets/art/slots/slots.png"
const MANIFEST := "res://data/art/slots.json"
const BLUE := 0
const PULSE_SPEED := 0.08
static var _manifest: Dictionary = {}
static var _texture: Texture2D = null


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func frames() -> Dictionary:
	var sheet: Dictionary = manifest().get("sheet", {})
	var listed: Dictionary = sheet.get("frames", {})
	return listed


## `pk = int(round(sin(animation_time * 0.08) * 2))`, with the tick as the clock.
static func pulse(tick: int) -> int:
	return clampi(roundi(sin(float(tick) * PULSE_SPEED) * 2.0), -2, 2)


static func frame_key(team: int, tick: int) -> String:
	if team == BLUE:
		return "blue:%d" % pulse(tick)
	return "red"


static func texture() -> Texture2D:
	if _texture == null and ResourceLoader.exists(SHEET):
		_texture = load(SHEET) as Texture2D
	return _texture


## `{texture, src, anchor}` for a slot, or `{}` when the sheet is not imported.
static func frame(team: int, tick: int) -> Dictionary:
	var rows := frames()
	var key := frame_key(team, tick)
	if not rows.has(key) or texture() == null:
		return {}
	var row: Array = rows[key]
	return {
		"texture": texture(),
		"src": Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3])),
		"anchor": Vector2(float(row[4]), float(row[5])),
	}
