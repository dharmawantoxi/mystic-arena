extends Control

signal prototype_requested(level_number: int, difficulty: String)
signal siege_requested
signal combat_requested
signal play_requested
signal quit_requested

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const HeroUnlockStore = preload("res://scripts/match/hero_unlock_store.gd")
const MetaHeroShopPanel = preload("res://scripts/ui/meta_hero_shop_panel.gd")

var progress_path := ProgressStore.PATH
var unlock_store := HeroUnlockStore.new()
var hero_shop_panel: MetaHeroShopPanel


func _ready() -> void:
	theme = UI_THEME.create_theme()
	UI_THEME.title(%Title, 56)
	UI_THEME.muted(%Subtitle)
	UI_THEME.muted(%Scope)
	%PlayButton.pressed.connect(func() -> void: _click_and_emit(play_requested))
	%QuitButton.pressed.connect(func() -> void: _click_and_emit(quit_requested))
	%CombatButton.pressed.connect(func() -> void: _click_and_emit(combat_requested))
	%SiegeButton.pressed.connect(func() -> void: _click_and_emit(siege_requested))
	%PrototypeButton.pressed.connect(func() -> void: _click_and_start())
	%HeroShopButton.pressed.connect(_open_hero_shop)
	_build_hero_shop()
	refresh_levels()
	%PrototypeButton.grab_focus()


func _click_and_emit(signal_value: Signal) -> void:
	AudioRuntime.play("ui_click")
	signal_value.emit()


func _click_and_start() -> void:
	AudioRuntime.play("ui_click")
	_start_selected_level()


func _build_hero_shop() -> void:
	hero_shop_panel = MetaHeroShopPanel.new()
	hero_shop_panel.name = "MetaHeroShop"
	hero_shop_panel.unlock_requested.connect(_unlock_hero)
	add_child(hero_shop_panel)


func _open_hero_shop() -> void:
	AudioRuntime.play("ui_click")
	var profile := unlock_store.bootstrap_state(ProgressStore.load_state(progress_path))
	hero_shop_panel.open_with_state(profile)


func _unlock_hero(hero_type: String) -> void:
	var before := unlock_store.bootstrap_state(ProgressStore.load_state(progress_path))
	var result := unlock_store.try_unlock(before, hero_type)
	if not String(result.error).is_empty():
		AudioRuntime.play("ui_error")
		hero_shop_panel.show_error(String(result.error))
		return
	if not ProgressStore.save_state(result.state, progress_path):
		AudioRuntime.play("ui_error")
		hero_shop_panel.show_error("save")
		return
	AudioRuntime.play("ui_buy")
	var item := unlock_store.entry(hero_type)
	var suffix := " gratis"
	if int(result.cost) > 0:
		suffix = " seharga %d Hero Gold" % int(result.cost)
	hero_shop_panel.apply_state(
		result.state, "%s dibuka%s." % [item.definition.display_name, suffix]
	)


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
