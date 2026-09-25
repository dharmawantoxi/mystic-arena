extends RefCounted
## Presentation only. No state, input, or gameplay dependencies.

const BODY_FONT = preload("res://assets/fonts/Barlow-Regular.ttf")
const STRONG_FONT = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const TITLE_FONT = preload("res://assets/fonts/Cinzel.ttf")
const INK := Color("e4ece8")
const MUTED := Color("96aaa9")
const GOLD := Color("d3b875")
const TEAL := Color("78d8c2")


static func panel(fill: Color, edge: Color, radius: int = 10) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = edge
	box.set_border_width_all(1)
	box.set_corner_radius_all(radius)
	box.content_margin_left = 22
	box.content_margin_right = 22
	box.content_margin_top = 14
	box.content_margin_bottom = 14
	return box


static func create_theme() -> Theme:
	var result := Theme.new()
	result.default_font = BODY_FONT
	result.default_font_size = 20
	result.set_color("font_color", "Label", INK)
	result.set_color("font_color", "Button", INK)
	result.set_color("font_hover_color", "Button", Color.WHITE)
	result.set_color("font_pressed_color", "Button", TEAL)
	result.set_font("font", "Button", STRONG_FONT)
	result.set_stylebox("normal", "Button", panel(Color("162d34"), Color("36514f")))
	result.set_stylebox("hover", "Button", panel(Color("25433f"), TEAL))
	result.set_stylebox("pressed", "Button", panel(Color("102823"), GOLD))
	var focus := panel(Color(0, 0, 0, 0), GOLD)
	focus.set_border_width_all(2)
	result.set_stylebox("focus", "Button", focus)
	result.set_stylebox("panel", "PanelContainer", panel(Color("10232bf2"), Color("314746")))
	return result


static func title(label: Label, font_size: int = 42) -> void:
	label.add_theme_font_override("font", TITLE_FONT)
	label.add_theme_font_size_override("font_size", font_size)


static func muted(label: Label) -> void:
	label.add_theme_color_override("font_color", MUTED)
