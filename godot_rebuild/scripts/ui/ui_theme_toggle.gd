extends Button
## Source `ui_theme.toggle()` switch: baked gradient/knob, live native caption and signal.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const ON_TEXT := Color8(210, 255, 220)

var _caption: Label
var _last_pressed := false


func _ready() -> void:
	toggle_mode = true
	custom_minimum_size = Vector2(60.0, 26.0)
	for color_name in [
		"font_color",
		"font_hover_color",
		"font_pressed_color",
		"font_hover_pressed_color",
		"font_focus_color",
		"font_disabled_color",
	]:
		add_theme_color_override(color_name, Color(1.0, 1.0, 1.0, 0.0))
	_setup_styleboxes()
	_caption = Label.new()
	_caption.name = "ToggleCaption"
	_caption.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_caption.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_caption.add_theme_font_override("font", UI_THEME.STRONG_FONT)
	_caption.add_theme_font_size_override("font_size", 12)
	add_child(_caption)
	toggled.connect(_on_toggled)
	resized.connect(_layout_caption)
	_sync_caption(true)
	_layout_caption()


func set_value(value: bool) -> void:
	set_pressed_no_signal(value)
	_sync_caption(true)


func _setup_styleboxes() -> void:
	var off: StyleBox = UiSkin.toggle_box("off")
	var off_hover: StyleBox = UiSkin.toggle_box("off_hover")
	var on: StyleBox = UiSkin.toggle_box("on")
	var on_hover: StyleBox = UiSkin.toggle_box("on_hover")
	if off == null:
		off = _flat_toggle(Color8(74, 78, 100), Color8(120, 126, 150))
	if off_hover == null:
		off_hover = _flat_toggle(Color8(92, 96, 118), Color8(150, 156, 180))
	if on == null:
		on = _flat_toggle(Color8(70, 190, 96), Color8(120, 235, 145))
	if on_hover == null:
		on_hover = _flat_toggle(Color8(92, 214, 118), Color8(160, 255, 180))
	add_theme_stylebox_override("normal", off)
	add_theme_stylebox_override("hover", off_hover)
	add_theme_stylebox_override("pressed", on)
	add_theme_stylebox_override("hover_pressed", on_hover)
	add_theme_stylebox_override("disabled", off)
	var focus := StyleBoxFlat.new()
	focus.draw_center = false
	focus.border_color = UI_THEME.GOLD
	focus.set_border_width_all(2)
	focus.set_corner_radius_all(13)
	add_theme_stylebox_override("focus", focus)


func _flat_toggle(fill: Color, edge: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = edge
	box.set_border_width_all(2)
	box.set_corner_radius_all(13)
	return box


func _on_toggled(_value: bool) -> void:
	_sync_caption(true)


func _sync_caption(force: bool) -> void:
	if not is_instance_valid(_caption):
		return
	if force or _last_pressed != button_pressed:
		_caption.text = "ON" if button_pressed else "OFF"
		_caption.add_theme_color_override(
			"font_color", ON_TEXT if button_pressed else UI_THEME.BODY
		)
		_last_pressed = button_pressed
	_layout_caption()


func _layout_caption() -> void:
	if not is_instance_valid(_caption):
		return
	_caption.position = Vector2(-8.0 if button_pressed else 8.0, 0.0)
	_caption.size = size
