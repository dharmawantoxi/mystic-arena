extends Control

signal prototype_requested(level_number: int, difficulty: String)
signal siege_requested
signal combat_requested
signal play_requested
signal quit_requested

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")

var progress_path := ProgressStore.PATH


func _ready() -> void:
	theme = UI_THEME.create_theme()
	UI_THEME.title(%Title, 56)
	UI_THEME.muted(%Subtitle)
	UI_THEME.muted(%Scope)
	%PlayButton.pressed.connect(func() -> void: play_requested.emit())
	%QuitButton.pressed.connect(func() -> void: quit_requested.emit())
	%CombatButton.pressed.connect(func() -> void: combat_requested.emit())
	%SiegeButton.pressed.connect(func() -> void: siege_requested.emit())
	%PrototypeButton.pressed.connect(_start_selected_level)
	refresh_levels()
	%PrototypeButton.grab_focus()


func refresh_levels() -> void:
	var progress := ProgressStore.load_state(progress_path)
	var completed: Array[int] = []
	for value in progress.get("completed_levels", []):
		completed.append(int(value))
	%LevelChoice.clear()
	for number in range(1, Catalog.COUNT + 1):
		var config := Catalog.get_level_config(number)
		%LevelChoice.add_item("%02d · %s" % [number, String(config.get("name", "?"))], number)
		%LevelChoice.set_item_disabled(number - 1, not Catalog.is_level_unlocked(number, completed))
	var selected := int(progress.get("last_played_level", 1))
	if not Catalog.is_level_unlocked(selected, completed):
		selected = 1
	%LevelChoice.select(selected - 1)
	%DifficultyChoice.clear()
	var lock_value: Variant = progress.get("run_difficulty")
	var locked := "" if lock_value == null else String(lock_value)
	for label in ["easy", "normal", "hard"]:
		if locked == "" or locked == label:
			%DifficultyChoice.add_item(label.capitalize())
			%DifficultyChoice.set_item_metadata(%DifficultyChoice.item_count - 1, label)
	%DifficultyChoice.select(0)
	if locked == "":
		%DifficultyChoice.select(1)  # Normal default.


func _start_selected_level() -> void:
	var number: int = %LevelChoice.get_selected_id()
	var progress := ProgressStore.load_state(progress_path)
	var completed: Array[int] = []
	for value in progress.get("completed_levels", []):
		completed.append(int(value))
	if not Catalog.is_level_unlocked(number, completed):
		return
	var difficulty := String(%DifficultyChoice.get_selected_metadata())
	var lock_value: Variant = progress.get("run_difficulty")
	var locked := "" if lock_value == null else String(lock_value)
	if difficulty not in ["easy", "normal", "hard"] or (locked != "" and locked != difficulty):
		return
	prototype_requested.emit(number, difficulty)
