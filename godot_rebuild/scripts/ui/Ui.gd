class_name Ui
extends RefCounted

## Active Godot UI facade. Palette/geometry now come from ui_theme.json via
## UiTheme; existing container layouts and hit-testing remain Godot-owned.
static var GOLD := UiTheme.color("gold")  # gdlint: ignore=class-variable-name
static var TEXT := UiTheme.color("text_white")  # gdlint: ignore=class-variable-name
static var MUTED := UiTheme.color("text_dim")  # gdlint: ignore=class-variable-name
static var PANEL := UiTheme.color("panel_fill")  # gdlint: ignore=class-variable-name
static var EDGE := UiTheme.color("edge_gold")  # gdlint: ignore=class-variable-name


static func font(title := false) -> Font:
	var path := (
		"res://assets/fonts/Cinzel.ttf" if title else "res://assets/fonts/Barlow-Regular.ttf"
	)
	if ResourceLoader.exists(path):
		return load(path)
	return ThemeDB.fallback_font


static func label(text: String, size := 22, color: Variant = null, title := false) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_override("font", font(title))
	node.add_theme_font_size_override("font_size", size)
	node.add_theme_color_override("font_color", TEXT if color == null else color)
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if title:
		apply_title_gradient(node)
	return node


static func apply_title_gradient(node: Label) -> void:
	if not UiTheme.ensure_loaded():
		return
	var shader := Shader.new()
	shader.code = """
shader_type canvas_item;
render_mode unshaded;
uniform vec4 top_color : source_color = vec4(1.0);
uniform vec4 bottom_color : source_color = vec4(1.0);
void fragment() {
	COLOR.rgb = mix(top_color.rgb, bottom_color.rgb, UV.y);
}
"""
	var material := ShaderMaterial.new()
	material.shader = shader
	material.set_shader_parameter("top_color", UiTheme.color("gold_bright"))
	material.set_shader_parameter(
		"bottom_color", UiTheme.rgb(UiTheme.value("text.outline_body_bottom"))
	)
	node.material = material
	node.add_theme_color_override(
		"font_outline_color", UiTheme.rgb(UiTheme.value("text.outline_color"))
	)
	node.add_theme_constant_override("outline_size", 2)


static func panel() -> PanelContainer:
	var node := UiThemePanel.new()
	var style := StyleBoxEmpty.new()
	style.content_margin_left = 30
	style.content_margin_right = 30
	style.content_margin_top = 26
	style.content_margin_bottom = 26
	node.add_theme_stylebox_override("panel", style)
	return node


static func button(text: String, primary := false) -> Button:
	var node := UiThemeButton.new()
	node.primary = primary
	node.text = text
	node.custom_minimum_size = Vector2(0, 52)
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	node.add_theme_font_override("font", font())
	node.add_theme_font_size_override("font_size", 21)
	return node


static func place(node: Control, rect: Rect2) -> Control:
	node.position = rect.position
	node.size = rect.size
	return node
