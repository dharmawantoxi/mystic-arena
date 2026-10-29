extends Button
## Layer 9br: main-menu buttons and hero-shop tabs backed by the real ui_theme.py frames.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const UiSkin = preload("res://scripts/ui/ui_skin.gd")
const IconBadge = preload("res://scripts/ui/source_icon_badge.gd")

@export_enum("button", "tab") var source_kind := "button"
@export var source_style_key := "play"
@export var icon_name := ""
@export_range(8, 48, 1) var label_font_size := 18

var _label: Label
var _badge: Control
var _last_text := "\u0000"
var _last_size := Vector2(-1.0, -1.0)
var _last_color := Color(1.0, 0.0, 1.0)


func _ready() -> void:
	if source_kind == "tab":
		toggle_mode = true
	_setup_styleboxes()
	for color_name in [
		"font_color",
		"font_hover_color",
		"font_pressed_color",
		"font_hover_pressed_color",
		"font_focus_color",
		"font_disabled_color",
	]:
		add_theme_color_override(color_name, Color(1.0, 1.0, 1.0, 0.0))
	add_theme_font_override("font", UI_THEME.STRONG_FONT)
	add_theme_font_size_override("font_size", label_font_size)
	_label = Label.new()
	_label.name = "SourceLabel"
	_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.add_theme_font_override("font", UI_THEME.STRONG_FONT)
	_label.add_theme_font_size_override("font_size", label_font_size)
	_label.add_theme_color_override("font_color", UI_THEME.INK)
	_label.add_theme_color_override("font_shadow_color", Color(0.02, 0.025, 0.05, 0.9))
	_label.add_theme_constant_override("shadow_offset_x", 2)
	_label.add_theme_constant_override("shadow_offset_y", 2)
	add_child(_label)
	if source_kind == "button" and not icon_name.is_empty():
		var accent := UiSkin.button_accent(source_style_key)
		if accent == UiSkin.NO_COLOR:
			accent = UI_THEME.GOLD
		_badge = IconBadge.new()
		_badge.name = "SourceIconBadge"
		_badge.set("icon_name", icon_name)
		_badge.set("accent", accent)
		_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_badge)
	resized.connect(_layout_source_children)
	_sync_label(true)
	_layout_source_children()


func _process(_delta: float) -> void:
	_sync_label(false)


func set_source_active(active: bool) -> void:
	if source_kind != "tab":
		return
	if not toggle_mode:
		toggle_mode = true
	set_pressed_no_signal(active)
	_sync_label(true)


func set_label_font_size(value: int) -> void:
	label_font_size = maxi(8, value)
	add_theme_font_size_override("font_size", label_font_size)
	if is_instance_valid(_label):
		_label.add_theme_font_size_override("font_size", label_font_size)
		_last_size = Vector2(-1.0, -1.0)
		_layout_source_children()


func _setup_styleboxes() -> void:
	var normal: StyleBox = null
	var hover: StyleBox = null
	var active: StyleBox = null
	if source_kind == "tab":
		normal = UiSkin.tab_box(source_style_key, "inactive")
		hover = UiSkin.tab_box(source_style_key, "hover")
		active = UiSkin.tab_box(source_style_key, "active")
	else:
		normal = UiSkin.button_box(source_style_key, "normal")
		hover = UiSkin.button_box(source_style_key, "hover")
		active = normal
	if normal == null:
		normal = UI_THEME.pill_style("neutral", "normal", false)
	if hover == null:
		hover = UI_THEME.pill_style("neutral", "hover", false)
	if active == null:
		active = normal
	add_theme_stylebox_override("normal", normal)
	add_theme_stylebox_override("hover", hover)
	add_theme_stylebox_override("pressed", active)
	add_theme_stylebox_override("hover_pressed", active)
	add_theme_stylebox_override("disabled", normal)
	var focus := StyleBoxFlat.new()
	focus.draw_center = false
	focus.border_color = _accent_color()
	focus.set_border_width_all(2)
	focus.set_corner_radius_all(8)
	add_theme_stylebox_override("focus", focus)


func _sync_label(force: bool) -> void:
	if not is_instance_valid(_label):
		return
	var display := _spaced(text) if source_kind == "tab" else text
	if force or display != _last_text:
		_label.text = display
		_last_text = display
		_last_size = Vector2(-1.0, -1.0)
	var color := UI_THEME.INK
	if source_kind == "tab":
		if button_pressed:
			color = _accent_color()
		elif is_hovered():
			color = UI_THEME.BODY
		else:
			color = UI_THEME.MUTED
	if force or not color.is_equal_approx(_last_color):
		_label.add_theme_color_override("font_color", color)
		_last_color = color
	_layout_source_children()


func _layout_source_children() -> void:
	if not is_instance_valid(_label):
		return
	if _last_size == size and not _last_size.x < 0.0:
		return
	_last_size = size
	_label.position = Vector2.ZERO
	_label.size = size
	if source_kind == "button" and is_instance_valid(_badge):
		_badge.position = Vector2(17.0, (size.y - 34.0) * 0.5)
		_badge.size = Vector2(34.0, 34.0)
		var label_text := text
		var text_width := (
			UI_THEME
			. STRONG_FONT
			. get_string_size(label_text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, label_font_size)
			. x
		)
		var center_x := size.x * 0.5 + 14.0
		var left_min := 56.0
		var right_max := size.x - 10.0
		if center_x - text_width * 0.5 < left_min:
			center_x = left_min + text_width * 0.5
		if center_x + text_width * 0.5 > right_max:
			center_x = right_max - text_width * 0.5
		if center_x - text_width * 0.5 < left_min:
			center_x = (left_min + right_max) * 0.5
		_label.position.x = center_x - size.x * 0.5


func _accent_color() -> Color:
	var color := (
		UiSkin.tab_accent(source_style_key)
		if source_kind == "tab"
		else UiSkin.button_accent(source_style_key)
	)
	return UI_THEME.GOLD if color == UiSkin.NO_COLOR else color


func _spaced(value: String) -> String:
	var result := ""
	for index in range(value.length()):
		if index > 0:
			result += " "
		result += value.substr(index, 1)
	return result
