extends RefCounted
## Playable main-menu proof for permanent hero unlock, save reload and the
## hand-off into the in-match Hero Shop roster.

const Store = preload("res://scripts/match/level_progress_store.gd")
const TEST_PATH := "user://meta_hero_unlock_scene_test.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	_cleanup()
	var menu = app.current_screen
	app.progress_path = TEST_PATH
	menu.progress_path = TEST_PATH
	var open: Button = menu.get_node("%HeroShopButton")
	open.pressed.emit()
	await _settle(tree)
	var panel = menu.get_node("MetaHeroShop")
	check.call(panel.visible and panel.is_open, "Main menu opens permanent Hero Shop")
	check.call(panel._visible_ids().size() == 6, "Permanent shop exposes six source starters")
	var kaizen := _card(panel, "kaizen")
	var thorne := _card(panel, "thorne")
	check.call(
		kaizen != null and kaizen.disabled and kaizen.text.contains("OWNED"),
		"Source auto-granted Kaizen starts owned"
	)
	check.call(
		thorne != null and not thorne.disabled and thorne.text.contains("FREE"),
		"Unclaimed source starter is a free permanent unlock"
	)
	thorne.pressed.emit()
	await _settle(tree)
	var profile := Store.load_state(TEST_PATH)
	check.call(
		profile.meta_gold == 0 and profile.purchased_heroes == ["kaizen", "thorne"],
		"Free starter unlock saves without Hero Gold debit"
	)

	panel._mini_tab.pressed.emit()
	await _settle(tree)
	var gornak := _card(panel, "gornak")
	check.call(
		gornak != null and gornak.disabled and gornak.text.contains("LOCKED"),
		"Undefeated boss hero is locked in playable menu"
	)
	panel.set_open(false)
	profile["meta_gold"] = 4500
	profile["unlocked_bosses"] = ["gornak"]
	check.call(Store.save_state(profile, TEST_PATH), "Seed defeated boss and exact Hero Gold")
	open.pressed.emit()
	panel._mini_tab.pressed.emit()
	await _settle(tree)
	gornak = _card(panel, "gornak")
	check.call(
		gornak != null and not gornak.disabled and gornak.text.contains("4500 G"),
		"Defeated boss with exact Hero Gold is buyable"
	)
	gornak.pressed.emit()
	await _settle(tree)
	profile = Store.load_state(TEST_PATH)
	check.call(
		(
			profile.meta_gold == 0
			and profile.purchased_heroes == ["kaizen", "thorne", "gornak"]
			and profile.unlocked_bosses == ["gornak"]
		),
		"Boss unlock atomically debits and persists permanent ownership"
	)
	panel.set_open(false)

	menu.get_node("%PrototypeButton").pressed.emit()
	await _settle(tree)
	var screen = app.current_screen
	var world = screen.simulation.world
	check.call(
		world.purchased_heroes == ["kaizen", "thorne", "gornak"],
		"Saved permanent roster configures the playable match"
	)
	var match_shop = screen.get_node("HUD/HeroShop")
	check.call(
		match_shop._visible_ids() == ["thorne", "kaizen"],
		"In-match starter catalog exposes only permanent ownership"
	)
	match_shop.tab = "boss"
	check.call(
		match_shop._visible_ids() == ["gornak"],
		"Purchased boss becomes summonable in the in-match boss tab"
	)
	screen.get_node("%BackButton").pressed.emit()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "Permanent shop profile exits match cleanly")
	menu = app.current_screen
	open = menu.get_node("%HeroShopButton")
	open.pressed.emit()
	await _settle(tree)
	panel = menu.get_node("MetaHeroShop")
	check.call(
		panel.state.purchased_heroes == ["kaizen", "thorne", "gornak"],
		"Permanent Hero Shop reloads saved ownership after scene replacement"
	)
	panel.set_open(false)
	app.show_menu()
	await _settle(tree)
	app.progress_path = Store.PATH
	app.current_screen.progress_path = Store.PATH
	_cleanup()
	check.call(tree.get_node_count() == baseline, "Permanent Hero Shop leaves no orphan controls")


func _card(panel: Control, hero_type: String) -> Button:
	for child in panel._grid.get_children():
		var button := child as Button
		if button != null and button.tooltip_text == hero_type:
			return button
	return null


func _cleanup() -> void:
	for suffix in ["", ".tmp", ".bak"]:
		if FileAccess.file_exists(TEST_PATH + suffix):
			DirAccess.remove_absolute(TEST_PATH + suffix)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
