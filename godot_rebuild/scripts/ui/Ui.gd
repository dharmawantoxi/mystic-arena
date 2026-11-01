class_name Ui
extends RefCounted

const GOLD := Color("e7bd69")
const TEXT := Color("eee9df")
const MUTED := Color("a49caf")
const PANEL := Color("141321")
const EDGE := Color("40374c")


static func font(title := false) -> Font:
	var path := (
		"res://assets/fonts/Cinzel.ttf" if title else "res://assets/fonts/Barlow-Regular.ttf"
	)
	if ResourceLoader.exists(path):
		return load(path)
	return ThemeDB.fallback_font


static func label(text: String, size := 22, color := TEXT, title := false) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_override("font", font(title))
	node.add_theme_font_size_override("font_size", size)
	node.add_theme_color_override("font_color", color)
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return node


static func panel() -> PanelContainer:
	var node := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = PANEL
	style.border_color = EDGE
	style.set_border_width_all(1)
	style.set_corner_radius_all(14)
	style.content_margin_left = 30
	style.content_margin_right = 30
	style.content_margin_top = 26
	style.content_margin_bottom = 26
	node.add_theme_stylebox_override("panel", style)
	return node


static func button(text: String, primary := false) -> Button:
	var node := Button.new()
	node.text = text
	node.custom_minimum_size = Vector2(0, 52)
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	node.add_theme_font_override("font", font())
	node.add_theme_font_size_override("font_size", 21)
	node.add_theme_color_override("font_color", GOLD if primary else TEXT)
	for state: String in ["normal", "hover", "pressed", "focus"]:
		var style := StyleBoxFlat.new()
		style.bg_color = Color("302638") if state != "normal" else Color("1c1929")
		style.border_color = GOLD if primary or state == "focus" else EDGE
		style.set_border_width_all(1)
		style.set_corner_radius_all(7)
		style.content_margin_left = 18
		style.content_margin_right = 18
		node.add_theme_stylebox_override(state, style)
	return node


static func place(node: Control, rect: Rect2) -> Control:
	node.position = rect.position
	node.size = rect.size
	return node
