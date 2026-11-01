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
	for button: Button in [shop_button] + skill_buttons.values():
		if button.visible and button.get_rect().has_point(position):
			return "shop" if button == shop_button else button.text.to_lower()
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
	var index := 0
	for button: Button in skill_buttons.values():
		button.position = Vector2(safe.end.x - 422 + index * 94, safe.end.y - 98)
		index += 1
	for button: Button in tactical_buttons.values():
		button.position.x = safe.end.x - 220
		button.position.y = maxf(button.position.y, safe.position.y + 236)
	status.position = Vector2(left, safe.end.y - 28)
