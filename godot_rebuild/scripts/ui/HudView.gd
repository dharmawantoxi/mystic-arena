class_name HudView
extends Control

signal action_pressed(action: String)

const TACTICAL_COMMANDS := [
	"gather", "protect_tower", "protect_castle", "attack_boss", "attack_damage_dealer"
]

var pause_button: Button
var debug_button: Button
var skip_button: Button
var status: Label
var tactical_buttons: Dictionary = {}
var skill_buttons: Dictionary = {}
var shop_button: Button
var item_button: Button
var tactical: TacticalCommands = null
var _tactical_font: Font = null


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	pause_button = Ui.button("II")
	pause_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pause_button.focus_mode = Control.FOCUS_NONE
	add_child(pause_button)
	Ui.place(pause_button, Rect2(22, 158, 64, 56))
	pause_button.tooltip_text = "Jeda • tahan untuk diagnostik"
	pause_button.pressed.connect(func() -> void: action_pressed.emit("pause"))
	debug_button = Ui.button("FPS")
	debug_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	debug_button.focus_mode = Control.FOCUS_NONE
	add_child(debug_button)
	Ui.place(debug_button, Rect2(100, 158, 76, 56))
	debug_button.pressed.connect(func() -> void: action_pressed.emit("debug"))
	skip_button = Ui.button("SKIP  >>", true)
	skip_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	skip_button.focus_mode = Control.FOCUS_NONE
	add_child(skip_button)
	Ui.place(skip_button, Rect2(1090, 638, 166, 58))
	skip_button.pressed.connect(func() -> void: action_pressed.emit("skip"))
	shop_button = _action_button("SHOP", "shop", Rect2(24, 632, 120, 64))
	item_button = _action_button("FORGE", "item_shop", Rect2(156, 632, 120, 64))
	var index := 0
	for skill: String in ["q", "w", "e", "r"]:
		skill_buttons[skill] = _action_button(
			skill.to_upper(), skill, Rect2(858 + index * 94, 622, 80, 74)
		)
		index += 1
	status = Ui.label("", 16, Ui.GOLD)
	add_child(status)
	Ui.place(status, Rect2(24, 680, 950, 28))


func sync_view(cinematic: bool, show_debug: bool, message: String, combat := false) -> void:
	pause_button.visible = not cinematic
	debug_button.visible = show_debug and not cinematic
	skip_button.visible = cinematic
	status.text = message
	shop_button.visible = combat and not cinematic
	item_button.visible = combat and not cinematic
	for button: Button in skill_buttons.values():
		button.visible = combat and not cinematic


func cancel() -> void:
	if pause_button != null:
		pause_button.button_pressed = false


func build_tactical_buttons() -> void:
	var labels := {
		"gather": "GATHER",
		"protect_tower": "PROTECT TOWER",
		"protect_castle": "PROTECT CASTLE",
		"attack_boss": "ATTACK BOSS",
		"attack_damage_dealer": "ATTACK DPS",
	}
	var index := 0
	for command: String in TACTICAL_COMMANDS:
		var button := Ui.button(labels[command])
		button.focus_mode = Control.FOCUS_NONE
		button.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(button)
		Ui.place(button, Rect2(1060, 246 + index * 64, 196, 52))
		button.visible = false
		tactical_buttons[command] = button
		index += 1


func hit_action(position: Vector2) -> String:
	for button: Button in [skip_button, debug_button, pause_button]:
		if button.visible and button.get_rect().has_point(position):
			if button == pause_button:
				return "pause"
			return "skip" if button == skip_button else "debug"
	for button: Button in [shop_button, item_button] + skill_buttons.values():
		if button.visible and button.get_rect().has_point(position):
			if button == shop_button:
				return "shop"
			if button == item_button:
				return "item_shop"
			return button.text.to_lower()
	for command: String in tactical_buttons:
		var button: Button = tactical_buttons[command]
		if button.visible and button.get_rect().has_point(position):
			return command
	return ""


func show_tactical_buttons(enabled: bool) -> void:
	for button: Button in tactical_buttons.values():
		button.visible = enabled


func _action_button(label: String, action: String, rect: Rect2) -> Button:
	var button := Ui.button(label)
	button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	button.focus_mode = Control.FOCUS_NONE
	add_child(button)
	Ui.place(button, rect)
	button.visible = false
	button.pressed.connect(func() -> void: action_pressed.emit(action))
	return button


func apply_safe_area(safe: Rect2) -> void:
	var left := maxf(22, safe.position.x + 6)
	var top := maxf(158, safe.position.y + 148)
	pause_button.position = Vector2(left, top)
	debug_button.position = Vector2(left + 78, top)
	skip_button.position = Vector2(safe.end.x - 180, safe.end.y - 82)
	shop_button.position = Vector2(left, safe.end.y - 88)
	item_button.position = Vector2(left + 132, safe.end.y - 88)
	var index := 0
	for button: Button in skill_buttons.values():
		button.position = Vector2(safe.end.x - 422 + index * 94, safe.end.y - 98)
		index += 1
	for button: Button in tactical_buttons.values():
		button.position.x = safe.end.x - 220
		button.position.y = maxf(button.position.y, safe.position.y + 236)
	status.position = Vector2(left, safe.end.y - 28)


func _process(_delta: float) -> void:
	if tactical != null:
		queue_redraw()


func _draw() -> void:
	if tactical == null or not tactical.valid():
		return
	_draw_tactical_world(tactical.world_draw_data())
	_draw_tactical_ui(tactical.ui_draw_data())


func _draw_tactical_world(data: Dictionary) -> void:
	if data.is_empty():
		return
	for line: Dictionary in data.get("lines", []):
		draw_line(
			Vector2(line.start[0], line.start[1]),
			Vector2(line.end[0], line.end[1]),
			_color(line.color),
			float(line.width)
		)
	for circle: Dictionary in data.get("circles", []):
		var center := Vector2(circle.center[0], circle.center[1])
		var color := _color(circle.color)
		if int(circle.width) > 0:
			draw_arc(center, float(circle.radius), 0.0, TAU, 48, color, float(circle.width))
		else:
			draw_circle(center, float(circle.radius), color)


func _draw_tactical_ui(data: Dictionary) -> void:
	if data.is_empty() or tactical.feedback_text.is_empty():
		return
	var font := _get_tactical_font()
	var font_size := int(tactical.cfg.draw_ui_font_size)
	var text := tactical.feedback_text
	var text_size := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	var inflate: Array = data.inflate
	var size := Vector2(text_size.x + float(inflate[0]), text_size.y + float(inflate[1]))
	var center := Vector2(data.center[0], data.center[1])
	var rect := Rect2(center - size * 0.5, size)
	var alpha := float(data.alpha) / 255.0
	var bg := Color(0, 0, 0, float(data.bg_alpha) / 255.0)
	draw_rect(rect, bg)
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0, 0, 0, 0)
	box.border_color = _color(
		[
			tactical.feedback_color[0],
			tactical.feedback_color[1],
			tactical.feedback_color[2],
			data.alpha
		]
	)
	box.set_border_width_all(int(data.border_width))
	box.set_corner_radius_all(int(data.border_radius))
	draw_style_box(box, rect)
	var text_pos := (
		rect.position
		+ Vector2(float(inflate[0]) * 0.5, float(inflate[1]) * 0.5 + font.get_ascent(font_size))
	)
	var shadow := Color(0, 0, 0, float(data.shadow_alpha) / 255.0)
	draw_string(
		font,
		text_pos + Vector2.ONE * float(data.shadow_offset),
		text,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		font_size,
		shadow
	)
	var col := _color(
		[
			tactical.feedback_color[0],
			tactical.feedback_color[1],
			tactical.feedback_color[2],
			data.alpha
		]
	)
	draw_string(font, text_pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, col)


func _get_tactical_font() -> Font:
	if _tactical_font != null:
		return _tactical_font
	var path := "res://assets/fonts/Barlow-Bold.ttf"
	if ResourceLoader.exists(path):
		_tactical_font = load(path) as Font
	if _tactical_font == null:
		_tactical_font = Ui.font(false)
	return _tactical_font


static func _color(row: Array) -> Color:
	var alpha := float(row[3]) / 255.0 if row.size() > 3 else 1.0
	return Color(float(row[0]) / 255.0, float(row[1]) / 255.0, float(row[2]) / 255.0, alpha)
