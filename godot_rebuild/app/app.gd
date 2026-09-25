extends Node
## Sole owner of screen lifetime. Transitions are deferred out of UI/input callbacks.

const MENU = preload("res://scenes/menu/MainMenu.tscn")
const MATCH = preload("res://scenes/match/Match.tscn")
const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")

var current_screen: Node
var transition_pending := false

@onready var screen_root: Control = $ScreenRoot


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	screen_root.theme = UI_THEME.create_theme()
	_install_screen(MENU)


func show_menu() -> void:
	_request_screen(MENU)


func start_match() -> void:
	_request_screen(MATCH)


func _request_screen(scene: PackedScene) -> void:
	if transition_pending:
		return
	transition_pending = true
	_install_screen.call_deferred(scene)


func _install_screen(scene: PackedScene) -> void:
	get_tree().paused = false
	if is_instance_valid(current_screen):
		screen_root.remove_child(current_screen)
		current_screen.queue_free()
	current_screen = scene.instantiate()
	screen_root.add_child(current_screen)
	if scene == MENU:
		current_screen.connect("play_requested", start_match)
		current_screen.connect("quit_requested", _quit)
	else:
		current_screen.connect("menu_requested", show_menu)
		current_screen.connect("restart_requested", start_match)
	transition_pending = false


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		if is_instance_valid(current_screen) and current_screen.has_method("pause_match"):
			current_screen.call("pause_match")


func _quit() -> void:
	get_tree().paused = false
	get_tree().quit()


func _exit_tree() -> void:
	# A paused match must not leak global pause state into another application/test scene.
	get_tree().paused = false
