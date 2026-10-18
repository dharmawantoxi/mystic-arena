extends RefCounted
## Layer 9bp: baked source tower bullets. `_entity.py::_get_bullet_sprite` caches one sprite per
## key (type, team, angle bucket) and `Bullet.draw` blits it at `(int(x - ax), int(y - ay))`.
## Only the arrow ("normal") depends on its bearing: 16 buckets of the angle to its target.
## `bake/bake_bullet_atlas.py` renders the real function; the picker below is replayed in CI
## against the buckets the real function chose.

const SHEET := "res://assets/art/bullets/bullets.png"
const MANIFEST := "res://data/art/bullets.json"
const BLUE := 0
const BUCKETS := 16
static var _manifest: Dictionary = {}
static var _texture: Texture2D = null
static var _tried := false


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func frames() -> Dictionary:
	var sheet: Dictionary = manifest().get("sheet", {})
	var rows: Dictionary = sheet.get("frames", {})
	return rows


## `angle_k = (int(ang / (2 * pi) * 16) + 16) % 16` from `_get_bullet_sprite`.
static func bucket(bearing: float) -> int:
	return (int(bearing / TAU * float(BUCKETS)) + BUCKETS) % BUCKETS


static func frame_key(kind: String, team: int, bearing: float) -> String:
	var side := "blue" if team == BLUE else "red"
	if kind == "normal":
		return "normal:%s:%d" % [side, bucket(bearing)]
	return "%s:%s" % [kind, side]


static func texture() -> Texture2D:
	if not _tried:
		_tried = true
		if ResourceLoader.exists(SHEET):
			_texture = load(SHEET) as Texture2D
	return _texture


## `{texture, src, anchor}` for a bullet, or `{}` for an unknown kind or an unimported sheet.
static func frame(kind: String, team: int, bearing: float) -> Dictionary:
	var rows := frames()
	var key := frame_key(kind, team, bearing)
	var sheet := texture()
	if sheet == null or not rows.has(key):
		return {}
	var row: Array = rows[key]
	return {
		"texture": sheet,
		"src": Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3])),
		"anchor": Vector2(float(row[4]), float(row[5])),
	}
