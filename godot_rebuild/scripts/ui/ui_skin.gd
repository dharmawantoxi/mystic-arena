extends RefCounted
## Layer 9br: the nine-patch skin baked from `ui_theme.py` (`bake/bake_ui_theme.py`).
## `panel()` and `pill()` were drawn by the real pygame code onto transparent canvases;
## here they become `StyleBoxTexture`s cut from two sheets. A getter returns null while
## its sheet is not imported, so the caller keeps its flat fallback.

const PANELS := "res://assets/art/ui/panels.png"
const PILLS := "res://assets/art/ui/pills.png"
const MANIFEST := "res://data/art/ui_theme.json"
const NEUTRAL := "neutral"
const NO_COLOR := Color(1.0, 0.0, 1.0)
static var _manifest: Dictionary = {}
static var _panels: Texture2D = null
static var _pills: Texture2D = null


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


## A colour constant of `ui_theme.py` (for example "GOLD" or "TEXT_BODY").
static func palette(key: String) -> Color:
	var table: Dictionary = manifest().get("palette", {})
	if not table.has(key):
		return NO_COLOR
	return _color(table[key])


## `top`, `bottom`, `edge` or `text` colour of a `pill()` kind.
static func pill_color(kind: String, part: String) -> Color:
	var pills: Dictionary = manifest().get("pills", {})
	var colors: Dictionary = pills.get("colors", {})
	var row: Dictionary = colors.get(kind, colors.get(NEUTRAL, {}))
	if not row.has(part):
		return NO_COLOR
	return _color(row[part])


static func panels_texture() -> Texture2D:
	if _panels == null and ResourceLoader.exists(PANELS):
		_panels = load(PANELS) as Texture2D
	return _panels


static func pills_texture() -> Texture2D:
	if _pills == null and ResourceLoader.exists(PILLS):
		_pills = load(PILLS) as Texture2D
	return _pills


## Nine-patch panel (`panel_bold` = dialog border, `panel` = default border) or null.
static func panel_box(key: String, content: Vector2) -> StyleBoxTexture:
	var sheet: Dictionary = manifest().get("panels", {})
	var frames: Dictionary = sheet.get("frames", {})
	if not frames.has(key) or panels_texture() == null:
		return null
	var margin := float(sheet.get("margin", 20))
	var expand := float(sheet.get("expand", 4))
	return _box(
		panels_texture(), frames[key], Vector2(margin, margin), Vector2(expand, expand), content
	)


## Nine-patch pill for a kind and state (`normal`, `hover`, `disabled`) or null.
static func pill_box(kind: String, state: String, content: Vector2) -> StyleBoxTexture:
	var sheet: Dictionary = manifest().get("pills", {})
	var frames: Dictionary = sheet.get("frames", {})
	var key := "%s:%s" % [kind, state]
	if not frames.has(key) or pills_texture() == null:
		return null
	var margin: Array = sheet.get("margin", [23, 20])
	var expand: Array = sheet.get("expand", [15, 12])
	var margins := Vector2(float(margin[0]), float(margin[1]))
	var grow := Vector2(float(expand[0]), float(expand[1]))
	return _box(pills_texture(), frames[key], margins, grow, content)


static func _color(row: Array) -> Color:
	return Color8(int(row[0]), int(row[1]), int(row[2]))


static func _box(
	texture: Texture2D, row: Array, margin: Vector2, expand: Vector2, content: Vector2
) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	box.texture = texture
	box.region_rect = Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3]))
	box.texture_margin_left = margin.x
	box.texture_margin_right = margin.x
	box.texture_margin_top = margin.y
	box.texture_margin_bottom = margin.y
	box.expand_margin_left = expand.x
	box.expand_margin_right = expand.x
	box.expand_margin_top = expand.y
	box.expand_margin_bottom = expand.y
	box.content_margin_left = content.x
	box.content_margin_right = content.x
	box.content_margin_top = content.y
	box.content_margin_bottom = content.y
	return box
