extends RefCounted
## Layer 9br: the nine-patch UI skin baked from `ui_theme.py` (`bake/bake_ui_theme.py`) and
## the Theme built on it. The palette is pinned to the constants the source module defines.

const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const HeroShopCard = preload("res://scripts/ui/hero_shop_card.gd")
const CLEAR_COLOR := "rendering/environment/defaults/default_clear_color"
# Theme constant -> the ui_theme.py constant it must equal.
const PALETTE_PINS := {
	"INK": "TEXT_WHITE",
	"BODY": "TEXT_BODY",
	"MUTED": "TEXT_DIM",
	"FAINT": "TEXT_FAINT",
	"GOLD": "GOLD",
	"GOLD_TEXT": "GOLD_TEXT",
	"CYAN": "CYAN",
	"EDGE_GOLD": "EDGE_GOLD",
	"PANEL_FILL": "PANEL_FILL",
}


func run(check: Callable) -> void:
	var manifest := UiSkin.manifest()
	check.call(not manifest.is_empty(), "The UI skin manifest parses")
	_check_palette(check)
	_check_sheets(check, manifest)
	_check_buttons(check, manifest)
	_check_panel(check, manifest)
	_check_variations(check, manifest)
	_check_fallback(check)
	_check_users(check)


func _check_palette(check: Callable) -> void:
	var constants: Dictionary = UI_THEME.get_script_constant_map()
	var wrong: Array = []
	for key in PALETTE_PINS:
		var want := UiSkin.palette(PALETTE_PINS[key])
		var have: Color = constants.get(key, UiSkin.NO_COLOR)
		if not have.is_equal_approx(want):
			wrong.append(key)
	check.call(wrong.is_empty(), "Theme colours equal the ui_theme.py constants: %s" % str(wrong))
	check.call(UI_THEME.TEAL == UI_THEME.CYAN, "The older TEAL name is the source cyan")
	var table: Dictionary = UiSkin.manifest().get("palette", {})
	check.call(table.size() >= 30, "The bake recorded the source palette: %d" % table.size())
	var clear: Color = ProjectSettings.get_setting(CLEAR_COLOR)
	var deep := UiSkin.palette("BG_DEEP")
	var close := absf(clear.r - deep.r) < 0.001 and absf(clear.g - deep.g) < 0.001
	close = close and absf(clear.b - deep.b) < 0.001
	check.call(close, "The window clear colour is the source deep background")


func _check_sheets(check: Callable, manifest: Dictionary) -> void:
	var panels: Dictionary = manifest.get("panels", {})
	var pills: Dictionary = manifest.get("pills", {})
	_check_sheet(check, UiSkin.PANELS, panels)
	_check_sheet(check, UiSkin.PILLS, pills)
	var kinds: Array = pills.get("kinds", [])
	var states: Array = pills.get("states", [])
	var frames: Dictionary = pills.get("frames", {})
	check.call(kinds.size() == 8 and states.size() == 3, "Eight pill kinds in three states")
	check.call(frames.size() == 24, "A frame for every kind and state: %d" % frames.size())
	var colors: Dictionary = pills.get("colors", {})
	var listed := true
	for kind in kinds:
		listed = listed and colors.has(kind) and (colors[kind] as Dictionary).size() == 4
	check.call(listed, "Every pill kind recorded its fill, edge and text colours")
	check.call(panels.get("frames", {}).size() == 2, "Two panel frames: dialog and default border")
	var image := Image.load_from_file(UiSkin.PANELS)
	if image != null:
		var centre := image.get_pixel(40, 40)
		var ring := image.get_pixel(0, 40)
		check.call(centre.a == 1.0, "A panel is opaque inside")
		check.call(ring.a > 0.2 and ring.a < 0.7, "The panel shadow ring is translucent")
	var pill_image := Image.load_from_file(UiSkin.PILLS)
	if pill_image != null:
		check.call(
			pill_image.get_pixel(0, 0).a == 0.0, "A pill canvas is transparent at its corner"
		)
		check.call(pill_image.get_pixel(27, 24).a == 1.0, "A pill is opaque inside")


func _check_sheet(check: Callable, path: String, sheet: Dictionary) -> void:
	var size: Array = sheet.get("size", [0, 0])
	var image := Image.load_from_file(path)
	var decodes := image != null and image.get_size() == Vector2i(int(size[0]), int(size[1]))
	check.call(decodes, "%s decodes at its size" % path)
	var frames: Dictionary = sheet.get("frames", {})
	var inside := not frames.is_empty()
	for key in frames:
		var row: Array = frames[key]
		inside = inside and int(row[0]) + int(row[2]) <= int(size[0])
		inside = inside and int(row[1]) + int(row[3]) <= int(size[1])
	check.call(inside, "Every frame of %s lies inside the sheet" % path)


func _frame(manifest: Dictionary, sheet: String, key: String) -> Rect2:
	var row: Array = (manifest.get(sheet, {}) as Dictionary).get("frames", {}).get(
		key, [0, 0, 0, 0]
	)
	return Rect2(float(row[0]), float(row[1]), float(row[2]), float(row[3]))


func _check_buttons(check: Callable, manifest: Dictionary) -> void:
	var theme: Theme = UI_THEME.create_theme()
	var pills: Dictionary = manifest.get("pills", {})
	var margin: Array = pills.get("margin", [0, 0])
	var expand: Array = pills.get("expand", [0, 0])
	var normal := theme.get_stylebox("normal", "Button") as StyleBoxTexture
	check.call(normal != null, "Buttons are the nine-patch pill")
	if normal != null:
		var same_margin := normal.texture_margin_left == float(margin[0])
		same_margin = same_margin and normal.texture_margin_top == float(margin[1])
		check.call(same_margin, "The pill margins are the baked ones")
		check.call(normal.expand_margin_left == float(expand[0]), "The pill glow overlaps its rect")
		check.call(normal.expand_margin_top == float(expand[1]), "The glow also grows vertically")
		check.call(
			normal.region_rect == _frame(manifest, "pills", "neutral:normal"), "Neutral pill"
		)
		check.call(normal.texture == UiSkin.pills_texture(), "The pill sheet is the texture")
		var pad: Vector2 = UI_THEME.BUTTON_PAD
		check.call(normal.content_margin_left == pad.x, "A pill keeps the button padding")
	var states := {
		"hover": "neutral:hover",
		"pressed": "gold:hover",
		"disabled": "locked:disabled",
	}
	for state in states:
		var box := theme.get_stylebox(state, "Button") as StyleBoxTexture
		var want := _frame(manifest, "pills", states[state])
		check.call(
			box != null and box.region_rect == want, "Button %s is %s" % [state, states[state]]
		)
	var text := UiSkin.pill_color("neutral", "text")
	check.call(theme.get_color("font_color", "Button").is_equal_approx(text), "Neutral pill text")
	check.call(text.is_equal_approx(UI_THEME.BODY), "which is the source body text colour")
	var pressed := theme.get_color("font_pressed_color", "Button")
	check.call(pressed.is_equal_approx(UiSkin.pill_color("gold", "text")), "A press reads gold")
	var off := theme.get_color("font_disabled_color", "Button")
	check.call(off.is_equal_approx(UiSkin.palette("TEXT_FAINT")), "Disabled text is faint")


func _check_panel(check: Callable, manifest: Dictionary) -> void:
	var theme: Theme = UI_THEME.create_theme()
	var panels: Dictionary = manifest.get("panels", {})
	var box := theme.get_stylebox("panel", "PanelContainer") as StyleBoxTexture
	check.call(box != null, "Panels are the nine-patch dialog panel")
	if box == null:
		return
	var margin := float(panels.get("margin", 0))
	var edge := box.texture_margin_left == margin and box.texture_margin_bottom == margin
	check.call(edge, "The panel margins keep shadow, corners and gold ticks")
	check.call(box.expand_margin_right == float(panels.get("expand", 0)), "The shadow lies outside")
	check.call(
		box.region_rect == _frame(manifest, "panels", "panel_bold"), "The 2 px dialog border"
	)
	var pad: Vector2 = UI_THEME.PANEL_PAD
	check.call(
		box.content_margin_left == pad.x and box.content_margin_top == pad.y, "Panel padding"
	)
	var bar := theme.get_stylebox("background", "ProgressBar") as StyleBoxFlat
	check.call(bar != null and bar.border_color == UI_THEME.TRACK_LINE, "Bars use the hp_bar track")
	var grab := theme.get_stylebox("grabber_pressed", "VScrollBar") as StyleBoxFlat
	check.call(grab != null and grab.bg_color == UI_THEME.GOLD, "A held scroll thumb is gold")


func _check_variations(check: Callable, manifest: Dictionary) -> void:
	var theme: Theme = UI_THEME.create_theme()
	var variants: Dictionary = UI_THEME.PILL_VARIANTS
	var kinds: Array = (manifest.get("pills", {}) as Dictionary).get("kinds", [])
	check.call(variants.size() == 5, "Five coloured button variations")
	for variation in variants:
		var kind: String = variants[variation]
		check.call(kinds.has(kind), "%s is a pill kind of the source" % variation)
		var base := theme.get_type_variation_base(variation)
		check.call(base == &"Button", "%s extends Button" % variation)
		var box := theme.get_stylebox("normal", variation) as StyleBoxTexture
		var want := _frame(manifest, "pills", "%s:normal" % kind)
		check.call(box != null and box.region_rect == want, "%s is the %s pill" % [variation, kind])
		var text := theme.get_color("font_color", variation)
		check.call(
			text.is_equal_approx(UiSkin.pill_color(kind, "text")), "%s text colour" % variation
		)


func _check_fallback(check: Callable) -> void:
	var flat: Theme = UI_THEME.create_theme(false)
	var normal := flat.get_stylebox("normal", "Button") as StyleBoxFlat
	check.call(normal != null, "Without the sheets a Button keeps a flat pill")
	if normal != null:
		check.call(normal.border_width_left == 2, "The flat pill has the 2 px border")
		check.call(
			normal.border_color.is_equal_approx(UiSkin.pill_color("neutral", "edge")), "Edge"
		)
	var off := flat.get_stylebox("disabled", "Button") as StyleBoxFlat
	check.call(off != null and off.border_width_left == 1, "A disabled flat pill has a 1 px border")
	var panel := flat.get_stylebox("panel", "PanelContainer") as StyleBoxFlat
	check.call(
		panel != null and panel.border_width_top == 2, "The flat panel has the dialog border"
	)
	check.call(panel != null and panel.border_color == UI_THEME.EDGE_GOLD, "in the source gold")
	check.call(UiSkin.pill_box("neutral", "missing", Vector2.ZERO) == null, "Unknown state: no box")
	check.call(UiSkin.panel_box("missing", Vector2.ZERO) == null, "Unknown panel: no box")
	check.call(UiSkin.palette("NOT_A_COLOR") == UiSkin.NO_COLOR, "Unknown colour is magenta")


func _check_users(check: Callable) -> void:
	var card := HeroShopCard.new()
	var open := card.get_theme_stylebox("normal") as StyleBoxFlat
	var locked := card.get_theme_stylebox("disabled") as StyleBoxFlat
	var open_ok := open != null and open.bg_color.is_equal_approx(UiSkin.palette("OPEN_BG_TOP"))
	check.call(open_ok, "Hero shop rows use the open card colours")
	check.call(open != null and open.border_color == UiSkin.palette("OPEN_EDGE"), "open edge")
	var locked_ok := locked != null and locked.bg_color == UiSkin.palette("LOCKED_BG_TOP")
	check.call(locked_ok, "A locked row uses the locked card colours")
	card.free()
