extends RefCounted
## Pygame save import driven through the real menu and save-slot panel.
## Headless: it clicks the same buttons a player clicks and reads the same cards.

const Import = preload("res://scripts/match/pygame_save_import.gd")
const Slots = preload("res://scripts/match/save_slot_store.gd")
const FIXTURE := "res://tests/fixtures/pygame_save_import_source.json"
const SLOT_TEMPLATE := "user://pygame_import_scene_slot_%d.json"
const STAGED_TEMPLATE := "user://pygame_import_scene_%d.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	_cleanup()
	app.slot_path_template = SLOT_TEMPLATE
	app.active_slot = 1
	var menu = app.current_screen
	check.call(
		menu.configure_slot_paths(SLOT_TEMPLATE, 1), "Import scene accepts isolated slot paths"
	)
	check.call(
		menu.configure_pygame_import_template(STAGED_TEMPLATE),
		"Import scene accepts isolated staged-file paths"
	)
	check.call(
		not menu.configure_pygame_import_template("user://no_index.json"),
		"A staged template without a slot index is refused"
	)
	check.call(
		menu.pygame_import_template.begins_with(STAGED_TEMPLATE.split("%d")[0]),
		"Refused template leaves the previous staged path active"
	)

	menu.get_node("%SaveGamesButton").pressed.emit()
	await _settle(tree)
	var panel = menu.get_node("SaveSlotPanel")
	check.call(panel.visible, "Main menu opens the save-slot chooser")
	check.call(panel._import_button != null, "Save panel exposes a Pygame import control")
	check.call(
		panel._import_status.text.contains("pygame_slot"),
		"Idle import state names the staged file to copy"
	)
	check.call(not panel._import_confirm.visible, "Import confirmation starts hidden")
	check.call(
		menu.get_node("%LevelChoice").is_item_disabled(1),
		"Menu starts with level two locked while save game one is empty"
	)

	panel._import_button.pressed.emit()
	check.call(panel._import_confirm.visible, "Import asks for confirmation before touching a save")
	panel._import_confirm_no.pressed.emit()
	check.call(
		not panel._import_confirm.visible and panel._import_status.text.contains("cancelled"),
		"Cancelled import closes the prompt and says nothing was written"
	)
	check.call(
		not Slots.slot_exists(1, SLOT_TEMPLATE), "Cancelled import leaves save game one empty"
	)

	panel._import_button.pressed.emit()
	panel._import_confirm_yes.pressed.emit()
	await _settle(tree)
	check.call(
		not Slots.slot_exists(1, SLOT_TEMPLATE), "Import without a staged file writes nothing"
	)
	check.call(
		panel._import_status.text.contains("No staged Pygame save"),
		"Missing staged file is explained in the panel"
	)

	var full := _case("full")
	var corrupt := "{broken"
	check.call(
		_write(Import.staged_path(1, STAGED_TEMPLATE), String(full.raw_text)),
		"A complete Pygame slot file is staged for save game one"
	)
	check.call(
		_write(Import.staged_path(2, STAGED_TEMPLATE), corrupt),
		"A corrupt Pygame slot file is staged for save game two"
	)
	var staged: Array = Import.staged_slots(STAGED_TEMPLATE)
	check.call(staged == [1, 2], "Both staged slots are discovered in order")
	panel._import_button.pressed.emit()
	panel._import_confirm_yes.pressed.emit()
	await _settle(tree)
	check.call(Slots.slot_exists(1, SLOT_TEMPLATE), "Staged Pygame save imports into save game one")
	var info := Slots.slot_info(1, SLOT_TEMPLATE)
	check.call(
		int(info.meta_gold) == 7250 and int(info.highest_level) == 4,
		"Imported save game carries the Pygame profile"
	)
	check.call(
		not Slots.slot_exists(2, SLOT_TEMPLATE), "Corrupt staged file never reaches a save game"
	)
	check.call(
		panel._import_status.text.contains("Slot 1 imported"), "Panel reports the imported slot"
	)
	check.call(
		panel._import_status.text.contains("Slot 2 refused"), "Panel reports the refused slot"
	)
	check.call(
		(
			panel._slot_labels[0].text.contains("Highest Level  4")
			and panel._slot_labels[1].text.contains("NEW GAME")
		),
		"Panel refreshes the imported card and keeps the refused one empty"
	)
	check.call(
		(
			FileAccess.get_file_as_string(Import.staged_path(1, STAGED_TEMPLATE))
			== String(full.raw_text)
		),
		"Import leaves the staged Pygame file untouched"
	)
	check.call(
		not menu.get_node("%LevelChoice").is_item_disabled(1),
		"Imported completion unlocks the next level in the menu"
	)
	check.call(
		menu.get_node("%DifficultyChoice").get_item_count() == 1,
		"Imported difficulty lock reaches the menu"
	)

	var legacy := _case("legacy_minimal")
	check.call(
		_write(Import.staged_path(1, STAGED_TEMPLATE), String(legacy.raw_text)),
		"A legacy Pygame slot file replaces the staged copy"
	)
	panel._import_button.pressed.emit()
	panel._import_confirm_yes.pressed.emit()
	await _settle(tree)
	check.call(
		int(Slots.slot_info(1, SLOT_TEMPLATE).meta_gold) == 410,
		"Repeated import replaces the same save game with the newer file"
	)
	check.call(
		menu.get_node("%LevelChoice").get_selected_id() == 1,
		"Re-imported cursor returns the menu to the legacy level"
	)
	check.call(
		menu.get_node("%DifficultyChoice").get_item_count() == 3,
		"A legacy slot without a difficulty lock reopens all difficulties"
	)

	Slots.delete_slot(1, SLOT_TEMPLATE)
	_delete_staged(1)
	panel._import_button.pressed.emit()
	panel._import_confirm_yes.pressed.emit()
	await _settle(tree)
	check.call(not Slots.slot_exists(1, SLOT_TEMPLATE), "A deleted save game is not recreated")
	check.call(
		panel._import_status.text.contains("Slot 2 refused"),
		"Only the remaining staged file is reported after the delete"
	)

	app.slot_path_template = Slots.PATH_TEMPLATE
	check.call(menu.configure_slot_paths(Slots.PATH_TEMPLATE, 1), "Restore production slot paths")
	check.call(
		menu.configure_pygame_import_template(Import.STAGED_TEMPLATE),
		"Restore production staged-file path"
	)
	panel.set_open(false)
	_cleanup()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "Pygame import scene leaves no orphan nodes")


func _case(case_name: String) -> Dictionary:
	var parsed: Variant = _parse(FileAccess.get_file_as_string(FIXTURE))
	if not (parsed is Dictionary):
		return {}
	for case in parsed.cases:
		if String(case.name) == case_name:
			return case
	return {}


func _parse(text: String) -> Variant:
	var decoder := JSON.new()
	if decoder.parse(text) != OK:
		return null
	return decoder.data


func _write(path: String, text: String) -> bool:
	if path.is_empty():
		return false
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(text)
	file.close()
	return FileAccess.get_file_as_string(path) == text


func _delete_staged(slot: int) -> void:
	var staged := Import.staged_path(slot, STAGED_TEMPLATE)
	for suffix in ["", ".bak", ".tmp"]:
		if not staged.is_empty() and FileAccess.file_exists(staged + suffix):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(staged + suffix))


func _cleanup() -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		Slots.delete_slot(slot, SLOT_TEMPLATE)
		_delete_staged(slot)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
