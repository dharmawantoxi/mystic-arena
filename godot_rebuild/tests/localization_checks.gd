extends RefCounted
## Native tests for source language data, persistence, formatting, and fallback.

const Store = preload("res://scripts/settings/language_store.gd")
const CATALOG := "res://data/localization_catalog.json"
const CONTRACT := "res://tests/fixtures/localization_source_contract.json"
const TEST_PATH := "user://localization_native_test.json"


func run(check: Callable) -> void:
	var catalog = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	var contract = JSON.parse_string(FileAccess.get_file_as_string(CONTRACT))
	check.call(
		catalog is Dictionary and contract is Dictionary,
		"localization catalog and source contract fixtures parse"
	)
	if not catalog is Dictionary or not contract is Dictionary:
		return
	var language_order_matches: bool = (
		Store.LANGUAGES.size() == contract.languages.size()
		and Store.LANGUAGES.size() == catalog.languages.size()
	)
	if language_order_matches:
		for index in Store.LANGUAGES.size():
			language_order_matches = (
				language_order_matches
				and Store.LANGUAGES[index] == String(contract.languages[index])
				and Store.LANGUAGES[index] == String(catalog.languages[index])
			)
	check.call(
		Store.DEFAULT_LANGUAGE == String(contract.default_language) and language_order_matches,
		"native language default and cycle order match Python"
	)
	check.call(
		(
			catalog.language_labels == contract.language_labels
			and catalog.texts.id.size() == 224
			and catalog.texts.en.size() == 224
		),
		"runtime translation tables and labels are complete in both source languages"
	)
	check.call(
		(
			Store.decode_language('{"version":1,"language":"id"}') == "id"
			and Store.decode_language('{"version":1,"language":"en"}') == "en"
		),
		"native language decoder accepts the two source choices"
	)
	check.call(
		(
			Store.decode_language('{"version":1,"language":"fr"}') == Store.INVALID_LANGUAGE
			and Store.decode_language('{"version":"1","language":"en"}') == Store.INVALID_LANGUAGE
			and Store.decode_language("broken") == Store.INVALID_LANGUAGE
		),
		"native decoder rejects unsupported languages, malformed versions, and corruption"
	)

	_remove_test_files()
	check.call(Store.save_language("en", TEST_PATH), "language preference saves atomically")
	check.call(
		(
			Store.load_language(TEST_PATH) == "en"
			and not FileAccess.file_exists(TEST_PATH + ".tmp")
			and not FileAccess.file_exists(TEST_PATH + ".bak")
		),
		"committed language value reloads with no leftover transaction files"
	)
	check.call(not Store.save_language("fr", TEST_PATH), "invalid language cannot be saved")
	var corrupt := FileAccess.open(TEST_PATH, FileAccess.WRITE)
	corrupt.store_string("broken language setting")
	corrupt.close()
	check.call(
		not Store.save_language("id", TEST_PATH), "corrupt language preferences are protected"
	)
	check.call(
		FileAccess.get_file_as_string(TEST_PATH) == "broken language setting",
		"rejected language save leaves corrupt bytes unchanged"
	)
	_remove_test_files()
	var backup := FileAccess.open(TEST_PATH + ".bak", FileAccess.WRITE)
	backup.store_string("unfinished language transaction")
	backup.close()
	check.call(not Store.save_language("id", TEST_PATH), "unfinished language backup blocks writes")
	_remove_test_files()

	var tree := Engine.get_main_loop() as SceneTree
	var runtime: Variant = tree.root.get_node_or_null("Localization")
	check.call(runtime != null, "localization runtime autoload is available")
	if runtime == null:
		return
	var original_path: String = String(runtime.settings_path)
	runtime.load_settings(TEST_PATH)
	check.call(
		(
			runtime.language == "id"
			and runtime.get_language_label() == "Bahasa Indonesia"
			and runtime.translate("menu_play") == "MULAI GAME"
		),
		"missing preference loads source Indonesian default and translations"
	)
	check.call(
		(
			runtime.translate("queued", {"count": 4}) == "+4 antrean"
			and runtime.translate("unknown_localization_key") == "unknown_localization_key"
		),
		"named interpolation and missing-key fallback match localization.py"
	)
	check.call(runtime.set_language("en"), "runtime switches language and persists preference")
	check.call(
		(
			runtime.language == "en"
			and runtime.get_language_label() == "English"
			and runtime.translate("menu_play") == "PLAY GAME"
			and runtime.translate("queued", {"count": 4}) == "+4 queued"
			and Store.load_language(TEST_PATH) == "en"
		),
		"English change updates catalog lookup and stored language immediately"
	)
	check.call(not runtime.set_language("fr"), "runtime rejects a language outside Python choices")
	check.call(runtime.cycle_language(1), "language cycle wraps English to Indonesian")
	check.call(
		runtime.language == "id" and Store.load_language(TEST_PATH) == "id",
		"language cycle persists the wrapped selection"
	)
	runtime.load_settings(original_path)
	_remove_test_files()


func _remove_test_files() -> void:
	for path in [TEST_PATH, TEST_PATH + ".bak", TEST_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
