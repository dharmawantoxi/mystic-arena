extends RefCounted
## Presentation only. No state, input, or gameplay dependencies.
## Layer 9br: palette, panels and buttons follow `ui_theme.py` (nine-patches from `UiSkin`).

const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const BODY_FONT = preload("res://assets/fonts/Barlow-Regular.ttf")
const STRONG_FONT = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const TITLE_FONT = preload("res://assets/fonts/Cinzel.ttf")
# Colour constants of ui_theme.py. tests/ui_skin_checks.gd and validate_project.py pin each
# one to the value the source module defines.
const INK := Color8(240, 244, 255)  # TEXT_WHITE
const BODY := Color8(198, 207, 230)  # TEXT_BODY
const MUTED := Color8(132, 142, 170)  # TEXT_DIM
const FAINT := Color8(96, 106, 136)  # TEXT_FAINT
const GOLD := Color8(255, 205, 85)  # GOLD
const GOLD_TEXT := Color8(255, 220, 110)  # GOLD_TEXT
const GOLD_BRIGHT := Color8(255, 233, 158)  # GOLD_BRIGHT
const CYAN := Color8(110, 195, 255)  # CYAN
const TEAL := CYAN  # the older name: callers use it as the hover accent
const EDGE_GOLD := Color8(176, 144, 82)  # EDGE_GOLD
const PANEL_FILL := Color8(21, 26, 48)  # PANEL_FILL
const TRACK := Color8(16, 18, 30)  # hp_bar track
const TRACK_LINE := Color8(86, 92, 120)  # hp_bar border
const SCROLL_TRACK := Color8(28, 32, 52)  # scroll_indicator track
const HOVER_FILL := Color8(44, 52, 86)  # button() hover fill
const GOLD_MID := Color8(225, 185, 99)  # mid of GOLD_BRIGHT -> (196, 138, 40)
const TITLE_OUTLINE := Color8(8, 9, 18)  # outline_text outline
const BUTTON_PAD := Vector2(14, 8)
const PANEL_PAD := Vector2(22, 14)
const PILL_RADIUS := 7
const PANEL_RADIUS := 12
const NEUTRAL := "neutral"
# Button type variations: theme_type_variation name -> ui_theme.pill kind.
const PILL_VARIANTS := {
	"GoldButton": "gold",
	"SuccessButton": "success",
	"DangerButton": "danger",
	"CyanButton": "cyan",
	"VioletButton": "violet",
}


static func panel(fill: Color, edge: Color, radius: int = 10) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = edge
	box.set_border_width_all(1)
	box.set_corner_radius_all(radius)
	box.content_margin_left = PANEL_PAD.x
	box.content_margin_right = PANEL_PAD.x
	box.content_margin_top = PANEL_PAD.y
	box.content_margin_bottom = PANEL_PAD.y
	return box


## `use_skin = false` forces the flat fallback (also what an un-imported sheet gives).
static func create_theme(use_skin: bool = true) -> Theme:
	var result := Theme.new()
	result.default_font = BODY_FONT
	result.default_font_size = 20
	result.set_color("font_color", "Label", INK)
	_style_button(result, "Button", NEUTRAL, use_skin)
	for variation in PILL_VARIANTS:
		var kind: String = PILL_VARIANTS[variation]
		result.set_type_variation(variation, "Button")
		_style_button(result, variation, kind, use_skin)
	result.set_stylebox("panel", "PanelContainer", panel_style(use_skin))
	_style_bars(result)
	_style_popup(result)
	return result


## The dialog panel of `ui_theme.panel`: nine-patch, or a flat box with the same colours.
static func panel_style(use_skin: bool = true) -> StyleBox:
	var skin: StyleBox = null
	if use_skin:
		skin = UiSkin.panel_box("panel_bold", PANEL_PAD)
	if skin != null:
		return skin
	var flat := panel(PANEL_FILL, EDGE_GOLD, PANEL_RADIUS)
	flat.set_border_width_all(2)
	return flat


## One `ui_theme.pill` state as a nine-patch, or a flat box with the same colours.
static func pill_style(kind: String, state: String, use_skin: bool = true) -> StyleBox:
	var skin: StyleBox = null
	if use_skin:
		skin = UiSkin.pill_box(kind, state, BUTTON_PAD)
	if skin != null:
		return skin
	var box := StyleBoxFlat.new()
	box.bg_color = UiSkin.pill_color(kind, "top")
	if state == "hover":
		box.bg_color = box.bg_color.lightened(0.12)
	box.border_color = UiSkin.pill_color(kind, "edge")
	box.set_border_width_all(1 if state == "disabled" else 2)
	box.set_corner_radius_all(PILL_RADIUS)
	box.content_margin_left = BUTTON_PAD.x
	box.content_margin_right = BUTTON_PAD.x
	box.content_margin_top = BUTTON_PAD.y
	box.content_margin_bottom = BUTTON_PAD.y
	return box


## `ui_theme.outline_text`: the gold gradient body (its mid colour here) inside a 2 px dark outline.
static func title(label: Label, font_size: int = 42) -> void:
	label.add_theme_font_override("font", TITLE_FONT)
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", GOLD_MID)
	label.add_theme_color_override("font_outline_color", TITLE_OUTLINE)
	label.add_theme_constant_override("outline_size", 2)


static func muted(label: Label) -> void:
	label.add_theme_color_override("font_color", MUTED)


## Normal / hover / pressed / disabled / focus of a button type for a `pill` kind. A hover
## keeps the text colour (as `pill()` does); a press reads as the gold pill.
static func _style_button(result: Theme, type_name: String, kind: String, use_skin: bool) -> void:
	var text := UiSkin.pill_color(kind, "text")
	if kind == NEUTRAL:
		text = BODY
	result.set_font("font", type_name, STRONG_FONT)
	for item in ["font_color", "font_hover_color", "font_focus_color"]:
		result.set_color(item, type_name, text)
	result.set_color("font_pressed_color", type_name, GOLD_TEXT)
	result.set_color("font_hover_pressed_color", type_name, GOLD_TEXT)
	result.set_color("font_disabled_color", type_name, FAINT)
	result.set_stylebox("normal", type_name, pill_style(kind, "normal", use_skin))
	result.set_stylebox("hover", type_name, pill_style(kind, "hover", use_skin))
	result.set_stylebox("pressed", type_name, pill_style("gold", "hover", use_skin))
	result.set_stylebox("disabled", type_name, pill_style("locked", "disabled", use_skin))
	var focus := StyleBoxFlat.new()
	focus.draw_center = false
	focus.border_color = GOLD
	focus.set_border_width_all(2)
	focus.set_corner_radius_all(PILL_RADIUS)
	result.set_stylebox("focus", type_name, focus)


## `hp_bar` / `progress_bar` and `scroll_indicator` colours for the Godot bar controls.
static func _style_bars(result: Theme) -> void:
	var track := panel(TRACK, TRACK_LINE, 4)
	track.content_margin_left = 0.0
	track.content_margin_right = 0.0
	track.content_margin_top = 0.0
	track.content_margin_bottom = 0.0
	result.set_stylebox("background", "ProgressBar", track)
	var fill := StyleBoxFlat.new()
	fill.bg_color = GOLD
	fill.set_corner_radius_all(4)
	result.set_stylebox("fill", "ProgressBar", fill)
	var lane := StyleBoxFlat.new()
	lane.bg_color = SCROLL_TRACK
	lane.set_corner_radius_all(3)
	for bar in ["VScrollBar", "HScrollBar"]:
		result.set_stylebox("scroll", bar, lane)
		result.set_stylebox("grabber", bar, _grabber(GOLD_MID))
		result.set_stylebox("grabber_highlight", bar, _grabber(GOLD_BRIGHT))
		result.set_stylebox("grabber_pressed", bar, _grabber(GOLD))


static func _grabber(color: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = color
	box.set_corner_radius_all(3)
	return box


## Drop-down lists (OptionButton) use the dialog colours.
static func _style_popup(result: Theme) -> void:
	var back := panel(PANEL_FILL, EDGE_GOLD, 8)
	back.content_margin_left = 6.0
	back.content_margin_right = 6.0
	back.content_margin_top = 6.0
	back.content_margin_bottom = 6.0
	result.set_stylebox("panel", "PopupMenu", back)
	var hover := StyleBoxFlat.new()
	hover.bg_color = HOVER_FILL
	hover.set_corner_radius_all(4)
	result.set_stylebox("hover", "PopupMenu", hover)
	result.set_color("font_color", "PopupMenu", BODY)
	result.set_color("font_hover_color", "PopupMenu", INK)
	result.set_color("font_disabled_color", "PopupMenu", FAINT)
