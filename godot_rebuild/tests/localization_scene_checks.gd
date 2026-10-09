extends RefCounted
## Exercises language cycling and live relabeling through MainMenu and a real match.

const Store = preload("res://scripts/settings/language_store.gd")
const TEST_PATH := "user://localization_scene_test.json"


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var localization: Variant = tree.root.get_node_or_null("Localization")
	check.call(localization != null, "playable app owns the source localization runtime")
	if localization == null:
		return
	var original_path := String(localization.settings_path)
	_remove_test_files()
	localization.load_settings(TEST_PATH)
	localization.emit_signal("language_changed", String(localization.language))

	var menu = app.current_screen
	var panel: Control = menu.get("audio_settings_panel")
	check.call(
		menu.name == "MainMenu" and panel != null,
		"language scene test starts at the playable MainMenu settings surface"
	)
	if panel == null:
		_restore(localization, original_path)
		return
	check.call(
		(
			menu.get_node("%SettingsButton").text == "PENGATURAN (SETTINGS)"
			and menu.get_node("%PlayButton").text == "MULAI GAME"
		),
		"Indonesian catalog is applied to live menu actions"
	)
	menu.get_node("%SettingsButton").pressed.emit()
	await _settle(tree)
	var title := panel.find_child("SettingsTitle", true, false) as Label
	var language_label := panel.find_child("LanguageLabel", true, false) as Label
	var language_value := panel.find_child("LanguageValue", true, false) as Label
	var master_label := panel.find_child("MasterLabel", true, false) as Label
	var next := panel.find_child("LanguageNext", true, false) as Button
	var previous := panel.find_child("LanguagePrevious", true, false) as Button
	check.call(
		(
			panel.visible
			and title != null
			and language_label != null
			and language_value != null
			and master_label != null
			and next != null
			and previous != null
		),
		"settings panel exposes persisted language and translated labels"
	)
	if title == null or language_label == null or language_value == null or master_label == null:
		_restore(localization, original_path)
		return
	check.call(
		(
			title.text == "PENGATURAN"
			and language_label.text == "Bahasa"
			and language_value.text == "Bahasa Indonesia"
			and master_label.text == "Volume Master"
		),
		"Indonesian language is reflected in settings title, selector, and audio labels"
	)
	if next != null:
		next.pressed.emit()
	check.call(
		(
			localization.language == "en"
			and Store.load_language(TEST_PATH) == "en"
			and title.text == "SETTINGS"
			and language_label.text == "Language"
			and language_value.text == "English"
			and master_label.text == "Master Volume"
			and menu.get_node("%SettingsButton").text == "SETTINGS"
			and menu.get_node("%PlayButton").text == "PLAY GAME"
		),
		"language next persists English and refreshes the visible app UI immediately"
	)
	var close_button := panel.find_child("CloseButton", true, false) as Button
	if close_button != null:
		close_button.pressed.emit()
	app.start_prototype()
	await _settle(tree)
	check.call(
		(
			app.current_screen.name == "PrototypeMatch"
			and localization.translate("menu_back") == "BACK"
			and Store.load_language(TEST_PATH) == "en"
		),
		"English preference remains active after entering playable combat"
	)
	app.show_menu()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "localized match returns to MainMenu")
	var menu_after_match = app.current_screen
	var panel_after_match: Control = menu_after_match.get("audio_settings_panel")
	check.call(panel_after_match != null, "return menu recreates a language-aware settings panel")
	if panel_after_match == null:
		_restore(localization, original_path)
		return
	menu_after_match.get_node("%SettingsButton").pressed.emit()
	await _settle(tree)
	var english_value := panel_after_match.find_child("LanguageValue", true, false) as Label
	var previous_after_match := (
		panel_after_match.find_child("LanguagePrevious", true, false) as Button
	)
	if previous_after_match != null:
		previous_after_match.pressed.emit()
	check.call(
		(
			localization.language == "id"
			and Store.load_language(TEST_PATH) == "id"
			and english_value != null
			and english_value.text == "Bahasa Indonesia"
		),
		"previous control wraps to Indonesian and persists after returning from a match"
	)
	var close_after_match := panel_after_match.find_child("CloseButton", true, false) as Button
	if close_after_match != null:
		close_after_match.pressed.emit()
	_restore(localization, original_path)


func _restore(localization: Variant, path: String) -> void:
	localization.load_settings(path)
	localization.emit_signal("language_changed", String(localization.language))
	_remove_test_files()


func _remove_test_files() -> void:
	for path in [TEST_PATH, TEST_PATH + ".bak", TEST_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
