extends RefCounted
## Layer 9br: source-baked `ui_theme.py` panels, pills and controls. Nine-patches are cut from
## manifest frames; a missing imported sheet returns null so flat theme fallbacks remain safe.

const PANELS := "res://assets/art/ui/panels.png"
const PILLS := "res://assets/art/ui/pills.png"
const BUTTONS := "res://assets/art/ui/buttons.png"
const TABS := "res://assets/art/ui/tabs.png"
const TOGGLES := "res://assets/art/ui/toggles.png"
const ICONS := "res://assets/art/ui/icons.png"
const SLIDER_GLOW := "res://assets/art/ui/slider_glow.png"
const MANIFEST := "res://data/art/ui_theme.json"
const NEUTRAL := "neutral"
const NO_COLOR := Color(1.0, 0.0, 1.0)
static var _manifest: Dictionary = {}
static var _panels: Texture2D = null
static var _pills: Texture2D = null
static var _buttons: Texture2D = null
static var _tabs: Texture2D = null
static var _toggles: Texture2D = null
static var _icons: Texture2D = null
static var _slider_glow: Texture2D = null


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


static func button_accent(key: String) -> Color:
	return _accent("buttons", key)


static func tab_accent(key: String) -> Color:
	return _accent("tabs", key)


static func _accent(sheet_name: String, key: String) -> Color:
	var controls: Dictionary = manifest().get("controls", {})
	var sheet: Dictionary = controls.get(sheet_name, {})
	var accents: Dictionary = sheet.get("accents", {})
	return _color(accents[key]) if accents.has(key) else NO_COLOR


static func panels_texture() -> Texture2D:
	if _panels == null and ResourceLoader.exists(PANELS):
		_panels = load(PANELS) as Texture2D
	return _panels


static func pills_texture() -> Texture2D:
	if _pills == null and ResourceLoader.exists(PILLS):
		_pills = load(PILLS) as Texture2D
	return _pills


static func buttons_texture() -> Texture2D:
	if _buttons == null and ResourceLoader.exists(BUTTONS):
		_buttons = load(BUTTONS) as Texture2D
	return _buttons


static func tabs_texture() -> Texture2D:
	if _tabs == null and ResourceLoader.exists(TABS):
		_tabs = load(TABS) as Texture2D
	return _tabs


static func toggles_texture() -> Texture2D:
	if _toggles == null and ResourceLoader.exists(TOGGLES):
		_toggles = load(TOGGLES) as Texture2D
	return _toggles


static func icons_texture() -> Texture2D:
	if _icons == null and ResourceLoader.exists(ICONS):
		_icons = load(ICONS) as Texture2D
	return _icons


static func slider_glow_texture() -> Texture2D:
	if _slider_glow == null and ResourceLoader.exists(SLIDER_GLOW):
		_slider_glow = load(SLIDER_GLOW) as Texture2D
	return _slider_glow


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
	return _box(
		pills_texture(),
		frames[key],
		Vector2(float(margin[0]), float(margin[1])),
		Vector2(float(expand[0]), float(expand[1])),
		content
	)


## Main-menu `button()` background in the source accent; the hover frame carries its glow.
static func button_box(
	style: String, state: String, content: Vector2 = Vector2.ZERO
) -> StyleBoxTexture:
	var controls: Dictionary = manifest().get("controls", {})
	var sheet: Dictionary = controls.get("buttons", {})
	var frames: Dictionary = sheet.get("frames", {})
	var key := "%s:%s" % [style, state]
	if not frames.has(key) or buttons_texture() == null:
		return null
	var margins: Dictionary = sheet.get("margins", {})
	var expands: Dictionary = sheet.get("expands", {})
	var margin: Array = margins.get(state, [0, 0])
	var expand: Array = expands.get(state, [0, 0])
	return _box(
		buttons_texture(),
		frames[key],
		Vector2(float(margin[0]), float(margin[1])),
		Vector2(float(expand[0]), float(expand[1])),
		content
	)


## Source `tab()` active/inactive/hover variants, with source-specific accent colours.
static func tab_box(
	style: String, state: String, content: Vector2 = Vector2.ZERO
) -> StyleBoxTexture:
	var controls: Dictionary = manifest().get("controls", {})
	var sheet: Dictionary = controls.get("tabs", {})
	var frames: Dictionary = sheet.get("frames", {})
	var key := "%s:%s" % [style, state]
	if not frames.has(key) or tabs_texture() == null:
		return null
	var margin: Array = sheet.get("margin", [0, 0])
	var expand: Array = sheet.get("expand", [0, 0])
	return _box(
		tabs_texture(),
		frames[key],
		Vector2(float(margin[0]), float(margin[1])),
		Vector2(float(expand[0]), float(expand[1])),
		content
	)


## Toggle background (`off`, `off_hover`, `on`, `on_hover`); label is kept live in Godot.
static func toggle_box(state: String, content: Vector2 = Vector2.ZERO) -> StyleBoxTexture:
	var controls: Dictionary = manifest().get("controls", {})
	var sheet: Dictionary = controls.get("toggles", {})
	var frames: Dictionary = sheet.get("frames", {})
	if not frames.has(state) or toggles_texture() == null:
		return null
	var margin: Array = sheet.get("margin", [0, 0])
	var expand: Array = sheet.get("expand", [0, 0])
	return _box(
		toggles_texture(),
		frames[state],
		Vector2(float(margin[0]), float(margin[1])),
		Vector2(float(expand[0]), float(expand[1])),
		content
	)


static func icon_frame(name: String) -> Rect2:
	var controls: Dictionary = manifest().get("controls", {})
	var sheet: Dictionary = controls.get("icons", {})
	var frames: Dictionary = sheet.get("frames", {})
	if not frames.has(name):
		return Rect2()
	var row: Array = frames[name]
	return Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3]))


static func control_sheet_size(name: String) -> Vector2i:
	var controls: Dictionary = manifest().get("controls", {})
	var sheet: Dictionary = controls.get(name, {})
	var size: Array = sheet.get("size", [0, 0])
	return Vector2i(int(size[0]), int(size[1]))


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
