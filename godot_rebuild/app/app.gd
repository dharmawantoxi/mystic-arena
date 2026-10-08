extends Node
## Sole owner of screen lifetime. Transitions are deferred out of UI/input callbacks.

const MENU = preload("res://scenes/menu/MainMenu.tscn")
const PROTOTYPE = preload("res://scenes/prototype/PrototypeMatch.tscn")
const SIEGE = preload("res://scenes/siege/SiegeArena.tscn")
const COMBAT = preload("res://scenes/combat/MinionArena.tscn")
const MATCH = preload("res://scenes/match/Match.tscn")
const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const SaveSlotStore = preload("res://scripts/match/save_slot_store.gd")
const HeroUnlockStore = preload("res://scripts/match/hero_unlock_store.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")

var current_screen: Node
var transition_pending := false
var prototype_level := 1
var prototype_difficulty := "normal"
var prototype_is_replay := false
var active_slot := SaveSlotStore.get_current_slot()
var slot_path_template := SaveSlotStore.PATH_TEMPLATE
var progress_path := SaveSlotStore.current_path(slot_path_template)

@onready var screen_root: Control = $ScreenRoot


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	screen_root.theme = UI_THEME.create_theme()
	SaveSlotStore.set_current_slot(active_slot)
	SaveSlotStore.migrate_legacy(ProgressStore.PATH, slot_path_template)
	progress_path = SaveSlotStore.slot_path(active_slot, slot_path_template)
	_install_screen(MENU)


func show_menu() -> void:
	if is_instance_valid(current_screen) and current_screen.name == "PrototypeMatch":
		progress_path = String(current_screen.get("progress_path"))
		var selected := SaveSlotStore.slot_for_path(progress_path, slot_path_template)
		if selected > 0:
			active_slot = selected
			SaveSlotStore.set_current_slot(selected)
	_request_screen(MENU)


func start_prototype(level_number: int = 1, difficulty: String = "normal") -> void:
	if transition_pending:
		return
	if is_instance_valid(current_screen) and current_screen.name == "MainMenu":
		progress_path = String(current_screen.get("progress_path"))
	prototype_level = level_number
	prototype_difficulty = difficulty
	prototype_is_replay = false
	_request_screen(PROTOTYPE)


func _restart_prototype() -> void:
	prototype_is_replay = true
	_request_screen(PROTOTYPE)


func _start_next_prototype(level_number: int) -> void:
	if level_number != Catalog.get_next_level(prototype_level):
		return
	prototype_level = level_number
	prototype_is_replay = false
	_request_screen(PROTOTYPE)


func start_siege() -> void:
	_request_screen(SIEGE)


func start_combat() -> void:
	_request_screen(COMBAT)


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
	if scene == PROTOTYPE:
		# Configure encounter and permanent hero unlocks before the session's
		# _ready creates the arena and its authoritative player roster.
		# Keep this node dynamic: the PackedScene boundary only exposes Node,
		# while PrototypeSession owns these pre-tree configuration methods.
		current_screen.set("progress_path", progress_path)
		current_screen.set("slot_path_template", slot_path_template)
		current_screen.set("is_replay", prototype_is_replay)
		var session = current_screen.get_node("Simulation")
		var profile := HeroUnlockStore.bootstrap_state(ProgressStore.load_state(progress_path))
		if (
			not session.configure_level(prototype_level, prototype_difficulty)
			or not session.configure_player_profile(profile)
		):
			current_screen.free()
			current_screen = MENU.instantiate()
			scene = MENU
	if scene == MENU:
		current_screen.set("slot_path_template", slot_path_template)
		current_screen.set("active_slot", active_slot)
		current_screen.set("progress_path", progress_path)
	screen_root.add_child(current_screen)
	if scene == MENU:
		current_screen.connect("progress_slot_changed", _select_progress_slot)
		current_screen.connect("play_requested", start_match)
		current_screen.connect("combat_requested", start_combat)
		current_screen.connect("siege_requested", start_siege)
		current_screen.connect("prototype_requested", start_prototype)
		current_screen.connect("quit_requested", _quit)
	else:
		current_screen.connect("menu_requested", show_menu)
		if scene == PROTOTYPE:
			current_screen.connect("restart_requested", _restart_prototype)
			current_screen.connect("next_level_requested", _start_next_prototype)
		else:
			current_screen.connect("restart_requested", _request_screen.bind(scene))
	transition_pending = false


func _select_progress_slot(slot: int, path: String) -> void:
	if path != SaveSlotStore.slot_path(slot, slot_path_template):
		return
	if not SaveSlotStore.set_current_slot(slot):
		return
	active_slot = slot
	progress_path = path


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
