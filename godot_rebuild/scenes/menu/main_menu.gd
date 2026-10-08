extends Control

signal prototype_requested(level_number: int, difficulty: String)
signal siege_requested
signal combat_requested
signal play_requested
signal quit_requested
signal progress_slot_changed(slot: int, path: String)

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const LevelStats = preload("res://scripts/match/level_stats.gd")
const HeroUnlockStore = preload("res://scripts/match/hero_unlock_store.gd")
const SaveSlotStore = preload("res://scripts/match/save_slot_store.gd")
const MetaHeroShopPanel = preload("res://scripts/ui/meta_hero_shop_panel.gd")
const SaveSlotPanel = preload("res://scripts/ui/save_slot_panel.gd")

var slot_path_template := SaveSlotStore.PATH_TEMPLATE
var progress_path := SaveSlotStore.current_path(slot_path_template)
var active_slot := SaveSlotStore.get_current_slot()
var hero_shop_panel: MetaHeroShopPanel
var save_slot_panel: SaveSlotPanel


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
	%SaveGamesButton.pressed.connect(_open_save_slots)
	%LevelChoice.item_selected.connect(_update_level_stats_label)
	var selected_from_path := SaveSlotStore.slot_for_path(progress_path, slot_path_template)
	if selected_from_path > 0:
		active_slot = selected_from_path
		SaveSlotStore.set_current_slot(active_slot)
	_build_hero_shop()
	_build_save_slots()
	_update_active_slot_label()
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
	var profile := HeroUnlockStore.bootstrap_state(ProgressStore.load_state(progress_path))
	hero_shop_panel.open_with_state(profile)


func _build_save_slots() -> void:
	save_slot_panel = SaveSlotPanel.new()
	save_slot_panel.name = "SaveSlotPanel"
	save_slot_panel.slot_requested.connect(_select_save_slot)
	save_slot_panel.delete_requested.connect(_delete_save_slot)
	add_child(save_slot_panel)
	var cloud := get_tree().root.get_node_or_null("CloudSave")
	if cloud != null:
		cloud.call("configure_native_paths", slot_path_template)
		if (
			cloud.has_signal("restore_available")
			and not cloud.is_connected("restore_available", _on_cloud_restore_available)
		):
			cloud.connect("restore_available", _on_cloud_restore_available)
		if (
			cloud.has_signal("restored")
			and not cloud.is_connected("restored", refresh_after_cloud_restore)
		):
			cloud.connect("restored", refresh_after_cloud_restore)
		var pending: Dictionary = cloud.call("get_pending_restore")
		if pending.has("payload"):
			var local_slots_empty := true
			for slot in range(1, SaveSlotStore.SLOT_COUNT + 1):
				var path := SaveSlotStore.slot_path(slot, slot_path_template)
				if (
					SaveSlotStore.slot_exists(slot, slot_path_template)
					or FileAccess.file_exists(path + ".tmp")
				):
					local_slots_empty = false
					break
			if local_slots_empty:
				_on_cloud_restore_available(pending.payload, pending.summary)
			else:
				cloud.call("dismiss_restore_prompt")


func _on_cloud_restore_available(payload: Dictionary, summary: Dictionary) -> void:
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)
	save_slot_panel.show_cloud_restore_prompt(payload, summary)


func refresh_after_cloud_restore() -> void:
	progress_path = SaveSlotStore.slot_path(active_slot, slot_path_template)
	_update_active_slot_label()
	refresh_levels()
	if save_slot_panel != null:
		save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)


func _open_save_slots() -> void:
	AudioRuntime.play("ui_click")
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	save_slot_panel.open_with_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)


func _select_save_slot(slot: int) -> void:
	if not SaveSlotStore.set_current_slot(slot):
		AudioRuntime.play("ui_error")
		return
	active_slot = slot
	progress_path = SaveSlotStore.slot_path(slot, slot_path_template)
	_update_active_slot_label()
	refresh_levels()
	save_slot_panel.set_open(false)
	progress_slot_changed.emit(slot, progress_path)
	AudioRuntime.play("ui_click")


func _delete_save_slot(slot: int) -> void:
	if not SaveSlotStore.delete_slot(slot, slot_path_template):
		AudioRuntime.play("ui_error")
	else:
		AudioRuntime.play("ui_click")
	if slot == active_slot:
		refresh_levels()
	save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)


func _update_active_slot_label() -> void:
	%ActiveSlotLabel.text = "SAVE GAME %d" % active_slot


func configure_slot_paths(path_template: String, slot: int = 1) -> bool:
	if not path_template.contains("%d") or not SaveSlotStore.set_current_slot(slot):
		return false
	slot_path_template = path_template
	active_slot = slot
	progress_path = SaveSlotStore.slot_path(slot, path_template)
	var cloud := get_tree().root.get_node_or_null("CloudSave")
	if cloud != null:
		cloud.call("configure_native_paths", slot_path_template)
	if is_node_ready():
		_update_active_slot_label()
		refresh_levels()
		if save_slot_panel != null and save_slot_panel.visible:
			save_slot_panel.refresh_slots(
				SaveSlotStore.all_slot_info(slot_path_template), active_slot
			)
	progress_slot_changed.emit(slot, progress_path)
	return true


func _unlock_hero(hero_type: String) -> void:
	var before := HeroUnlockStore.bootstrap_state(ProgressStore.load_state(progress_path))
	var result := HeroUnlockStore.try_unlock(before, hero_type)
	if not String(result.error).is_empty():
		AudioRuntime.play("ui_error")
		hero_shop_panel.show_error(String(result.error))
		return
	if not SaveSlotStore.save_path(result.state, progress_path, -1.0, slot_path_template):
		AudioRuntime.play("ui_error")
		hero_shop_panel.show_error("save")
		return
	AudioRuntime.play("ui_buy")
	var item := HeroUnlockStore.entry(hero_type)
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
	_update_level_stats_label()


func _update_level_stats_label(_index: int = -1) -> void:
	var level_number: int = %LevelChoice.get_selected_id()
	var stats := LevelStats.get_level_stats(ProgressStore.load_state(progress_path), level_number)
	var attempts := int(stats.total_attempts)
	if attempts <= 0:
		%LevelStatsLabel.text = "NO STATS YET"
		return
	var wins := int(stats.wins)
	var win_rate := int((float(wins) / float(attempts)) * 100.0)
	%LevelStatsLabel.text = (
		"BEST %d  ·  TIME %s  ·  %dW/%d  ·  %d%%"
		% [
			int(stats.best_score),
			LevelStats.format_time(int(stats.best_time_seconds)),
			wins,
			attempts,
			win_rate,
		]
	)


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
	if locked == "":
		progress = HeroUnlockStore.bootstrap_state(progress)
		progress["run_difficulty"] = difficulty
		if not SaveSlotStore.save_path(progress, progress_path, -1.0, slot_path_template):
			AudioRuntime.play("ui_error")
			return
	prototype_requested.emit(number, difficulty)
