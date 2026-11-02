class_name UiThemeButton
extends Button

## Container-safe wrapper around the source button renderer. The hit rectangle
## stays owned by Godot's layout; the pure component preserves hover inflation.
var primary := false


func _ready() -> void:
	flat = true
	for state: String in ["normal", "hover", "pressed", "focus", "disabled"]:
		add_theme_stylebox_override(state, StyleBoxEmpty.new())
	for color_name: String in [
		"font_color",
		"font_hover_color",
		"font_pressed_color",
		"font_focus_color",
		"font_disabled_color"
	]:
		add_theme_color_override(color_name, Color.TRANSPARENT)
	mouse_entered.connect(queue_redraw)
	mouse_exited.connect(queue_redraw)
	focus_entered.connect(queue_redraw)
	focus_exited.connect(queue_redraw)
	pressed.connect(queue_redraw)
	resized.connect(queue_redraw)


func _draw() -> void:
	if not UiTheme.ensure_loaded() or size.x <= 0 or size.y <= 0:
		return
	var font := Ui.font()
	var font_size := get_theme_font_size("font_size")
	var accent: Array = UiTheme.palette.get("gold" if primary else "cyan", [255, 205, 85])
	var hover := is_hovered() or has_focus() or button_pressed
	var data := UiThemeComponents.button(
		"",
		text,
		size.x / 2.0,
		size.y / 2.0,
		accent,
		font_size,
		UiThemeText.font_measure(font, font_size),
		{"w": int(size.x), "h": int(size.y), "hover": hover, "letter_gap": false}
	)
	UiThemeDraw.render(self, data.ops, font, font_size)
