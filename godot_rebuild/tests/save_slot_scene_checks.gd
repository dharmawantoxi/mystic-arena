extends RefCounted
## End-to-end save-slot selection, profile handoff, result commit and explicit delete.

const Slots = preload("res://scripts/match/save_slot_store.gd")
const TEST_TEMPLATE := "user://save_slot_scene_%d.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	_cleanup()
	app.slot_path_template = TEST_TEMPLATE
	app.active_slot = 1
	var menu = app.current_screen
	check.call(menu.configure_slot_paths(TEST_TEMPLATE, 1), "Menu accepts isolated slot paths")
	check.call(
		app.progress_path == Slots.slot_path(1, TEST_TEMPLATE) and app.active_slot == 1,
		"App owns the selected save-slot path"
	)

	var slot_one := _state(100, [1], 1, ["kaizen"], "normal")
	var slot_two := _state(250, [1], 2, ["kaizen", "thorne"], null)
	check.call(
		Slots.save_state(slot_one, 1, 1_700_000_000.0, TEST_TEMPLATE),
		"Scene fixture writes slot one"
	)
	check.call(
		Slots.save_state(slot_two, 2, 1_700_000_010.0, TEST_TEMPLATE),
		"Scene fixture writes slot two"
	)
	menu.refresh_levels()
	menu.get_node("%SaveGamesButton").pressed.emit()
	await _settle(tree)
	var panel = menu.get_node("SaveSlotPanel")
	check.call(panel.visible, "Main menu opens the real save-slot chooser")
	check.call(
		panel._slot_buttons.size() == 3 and panel._delete_buttons.size() == 3,
		"Save-slot chooser exposes all three source slots"
	)
	check.call(
		(
			panel._slot_labels[0].text.contains("Highest Level  1")
			and panel._slot_labels[1].text.contains("Hero Gold  250")
			and panel._slot_labels[2].text.contains("NEW GAME")
		),
		"Slot cards distinguish both profiles and an empty slot"
	)

	panel._slot_buttons[1].pressed.emit()
	await _settle(tree)
	check.call(
		(
			app.active_slot == 2
			and app.progress_path == Slots.slot_path(2, TEST_TEMPLATE)
			and menu.progress_path == app.progress_path
		),
		"Selecting slot two atomically reroutes menu and app progression"
	)
	check.call(
		menu.get_node("%LevelChoice").get_selected_id() == 2,
		"Selected slot restores its last-played unlocked level"
	)
	menu.get_node("%HeroShopButton").pressed.emit()
	await _settle(tree)
	var hero_shop = menu.get_node("MetaHeroShop")
	check.call(
		hero_shop.state.purchased_heroes == ["kaizen", "thorne"],
		"Permanent Hero Shop reads only the selected slot roster"
	)
	hero_shop.set_open(false)

	var difficulty: OptionButton = menu.get_node("%DifficultyChoice")
	difficulty.select(2)  # Hard; source locks this on the first level launch.
	menu.get_node("%PrototypeButton").pressed.emit()
	await _settle(tree)
	var screen = app.current_screen
	var world = screen.simulation.world
	check.call(
		(
			screen.progress_path == Slots.slot_path(2, TEST_TEMPLATE)
			and screen.slot_path_template == TEST_TEMPLATE
			and world.level_number == 2
			and world.difficulty == "hard"
		),
		"Selected slot and first-run difficulty reach the playable match"
	)
	check.call(
		world.purchased_heroes == ["kaizen", "thorne"],
		"Playable player roster comes from slot two only"
	)
	var locked := Slots.load_state(2, TEST_TEMPLATE)
	check.call(
		locked.run_difficulty == "hard",
		"First level launch persists the source run-difficulty lock"
	)

	world.winner = world.BLUE
	screen._save_result()
	var slot_two_after := Slots.load_state(2, TEST_TEMPLATE)
	var slot_one_after := Slots.load_state(1, TEST_TEMPLATE)
	check.call(
		(
			2 in slot_two_after.completed_levels
			and slot_two_after.meta_gold == 3250
			and slot_two_after.purchased_heroes == ["kaizen", "thorne"]
		),
		"Level result commits reward and profile to the active slot"
	)
	check.call(
		slot_one_after.meta_gold == 100 and slot_one_after.completed_levels == [1],
		"Active-slot result cannot mutate another save game"
	)

	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	menu = app.current_screen
	check.call(
		menu.active_slot == 2 and menu.progress_path == Slots.slot_path(2, TEST_TEMPLATE),
		"Returning to menu retains active-slot ownership"
	)
	menu.get_node("%SaveGamesButton").pressed.emit()
	await _settle(tree)
	panel = menu.get_node("SaveSlotPanel")
	panel._delete_buttons[1].pressed.emit()
	check.call(
		panel.pending_delete == 2 and panel._confirm.visible,
		"Delete requires the source confirmation boundary"
	)
	panel._confirm_yes.pressed.emit()
	await _settle(tree)
	check.call(
		not Slots.slot_exists(2, TEST_TEMPLATE) and panel._slot_labels[1].text.contains("NEW GAME"),
		"Confirmed delete clears only slot two and refreshes its card"
	)
	check.call(Slots.slot_exists(1, TEST_TEMPLATE), "Deleting active slot leaves slot one intact")

	var corrupt_path := Slots.slot_path(3, TEST_TEMPLATE)
	var corrupt := FileAccess.open(corrupt_path, FileAccess.WRITE)
	if corrupt != null:
		corrupt.store_string("{broken")
		corrupt.close()
	panel.refresh_slots(Slots.all_slot_info(TEST_TEMPLATE), menu.active_slot)
	check.call(
		(
			panel._slot_buttons[2].disabled
			and not panel._delete_buttons[2].disabled
			and panel._slot_labels[2].text.contains("CORRUPT")
		),
		"Corrupt slot is blocked until an explicit UI delete"
	)
	panel._delete_buttons[2].pressed.emit()
	panel._confirm_no.pressed.emit()
	check.call(FileAccess.file_exists(corrupt_path), "Cancel preserves corrupt slot for recovery")
	panel._delete_buttons[2].pressed.emit()
	panel._confirm_yes.pressed.emit()
	check.call(not FileAccess.file_exists(corrupt_path), "Confirmed delete clears corrupt slot")

	panel._slot_buttons[0].pressed.emit()
	await _settle(tree)
	check.call(
		(
			app.active_slot == 1
			and app.progress_path == Slots.slot_path(1, TEST_TEMPLATE)
			and menu.get_node("%DifficultyChoice").get_item_count() == 1
		),
		"Selecting slot one restores its independent difficulty lock"
	)
	app.slot_path_template = Slots.PATH_TEMPLATE
	check.call(menu.configure_slot_paths(Slots.PATH_TEMPLATE, 1), "Restore production slot paths")
	panel.set_open(false)
	_cleanup()
	await _settle(tree)
	check.call(
		tree.get_node_count() == baseline, "Save-slot scene lifecycle leaves no orphan nodes"
	)


func _state(
	gold: int, completed: Array, last_level: int, purchased: Array, difficulty: Variant
) -> Dictionary:
	return {
		"meta_gold": gold,
		"completed_levels": completed,
		"replay_reward_counts": {},
		"last_played_level": last_level,
		"purchased_heroes": purchased,
		"unlocked_bosses": [],
		"run_difficulty": difficulty,
	}


func _cleanup() -> void:
	for slot in range(1, Slots.SLOT_COUNT + 1):
		Slots.delete_slot(slot, TEST_TEMPLATE)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
