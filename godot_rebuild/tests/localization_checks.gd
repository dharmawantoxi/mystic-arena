extends RefCounted
## Native tests for source language data, persistence, formatting, and fallback.

const Store = preload("res://scripts/settings/language_store.gd")
const LocalizationText = preload("res://scripts/settings/localization_text.gd")
const ItemShop = preload("res://scripts/match/item_shop_ui.gd")
const CATALOG := "res://data/localization_catalog.json"
const CONTRACT := "res://tests/fixtures/localization_source_contract.json"
const TRANSLATE_FIXTURE := "res://tests/fixtures/localization_translate_source.json"
const PANEL_SCRIPT := "res://scripts/ui/item_forge_panel.gd"
const SHOP_SCRIPT := "res://scripts/match/item_shop_ui.gd"
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
	_localization_matrix(check, runtime)
	_shop_copy(check, runtime)
	runtime.load_settings(original_path)
	_remove_test_files()


func _localization_matrix(check: Callable, runtime: Variant) -> void:
	# Source localization.py is executed by the oracle; this replay proves the
	# native runtime renders the same 224x2 strings and tr() edge behaviour.
	var fixture: Variant = JSON.parse_string(FileAccess.get_file_as_string(TRANSLATE_FIXTURE))
	check.call(fixture is Dictionary, "python tr() render fixture parses")
	if not fixture is Dictionary:
		return
	var values: Dictionary = {}
	for key in fixture.values:
		var raw: Variant = fixture.values[key]
		values[key] = int(raw) if typeof(raw) == TYPE_FLOAT else raw
	var mismatches: Array = []
	for language in fixture.languages:
		if not runtime.set_language(String(language)):
			mismatches.append("language:" + String(language))
			continue
		var expected: Dictionary = fixture.renders[String(language)]
		for key in expected:
			if runtime.translate(String(key), values) != String(expected[key]):
				mismatches.append("%s/%s" % [language, key])
	check.call(
		mismatches.is_empty(),
		"translate() reproduces every source tr() render: %s" % str(mismatches.slice(0, 3))
	)
	var edges: Dictionary = fixture.edges
	check.call(
		(
			runtime.translate("queued", {"count": true}) == String(edges.bool_value)
			and runtime.translate("queued", {"count": 4.0}) == String(edges.float_value)
			and runtime.translate("menu_play", {"page": 9}) == String(edges.extra_value)
			and runtime.translate(String(edges.unknown_key)) == String(edges.unknown_key)
		),
		"bool, float, surplus values and unknown keys match Python tr()"
	)
	var raw_missing: Array = []
	for language in edges.missing_value:
		runtime.set_language(String(language))
		if runtime.translate("queued") != String(edges.missing_value[language]):
			raw_missing.append(language)
	check.call(raw_missing.is_empty(), "a missing value keeps the raw tr() template")
	var percent: Dictionary = edges.percent_template
	var percent_missing: Array = []
	for language in percent.renders:
		runtime.set_language(String(language))
		if runtime.translate(String(percent.key), values) != String(percent.renders[language]):
			percent_missing.append(language)
	check.call(percent_missing.is_empty(), "percent templates stay untouched like tr()")
	runtime.set_language("en")
	var labels: Dictionary = fixture.labels
	check.call(
		(
			runtime.get_language() == "en"
			and runtime.get_language_label("id") == String(labels.id)
			and runtime.get_language_label("en") == String(labels.en)
			and runtime.get_language_label("xx") == String(labels.unknown)
			and runtime.get_language_label("") == String(labels.empty)
			and runtime.get_language_label() == String(labels.empty)
		),
		"get_language() and get_language_label() mirror localization.py"
	)
	check.call(
		(
			not runtime.set_language("fr")
			and runtime.get_language() == "en"
			and Store.decode_language('{"version": 1, "language": "fr"}') == "id"
			and String(edges.invalid_language.after) == "id"
		),
		"unknown codes are rejected while stored preferences fall back to Indonesian"
	)
	runtime.set_language("id")


func _shop_copy(check: Callable, runtime: Variant) -> void:
	# ITEM FORGE copy must come from the same tr() keys as hero_items.py.
	var tree := Engine.get_main_loop() as SceneTree
	var host := Node.new()
	tree.root.add_child(host)
	runtime.set_language("id")
	var indonesian_dead: String = LocalizationText.translate(host, "dead", "dead")
	runtime.set_language("en")
	var english_dead: String = LocalizationText.translate(host, "dead", "dead")
	check.call(
		(
			indonesian_dead == "MATI"
			and english_dead == "DEAD"
			and LocalizationText.translate(null, "dead", "dead") == "dead"
			and LocalizationText.translate(null, "queued", "+{count} queue", {"count": 2}) == "+2 queue"
		),
		"panel tr() bridge follows the runtime and falls back without one"
	)
	var suffix: String = LocalizationText.translate(host, "delivery_after_respawn", "(x)")
	var shop: Object = ItemShop.new()
	shop.notice = {"hero_id": 2, "dead": true}
	var dead_notice: String = String(shop.notice_text(suffix))
	shop.notice = {"hero_id": 2, "dead": false}
	check.call(
		(
			dead_notice == "BUY FOR: hero 2 (delivered after respawn)"
			and String(shop.notice_text(suffix)) == "BUY FOR: hero 2"
		),
		"BUY FOR notice localises its respawn suffix like the source"
	)
	var panel_source := FileAccess.get_file_as_string(PANEL_SCRIPT)
	var shop_source := FileAccess.get_file_as_string(SHOP_SCRIPT)
	var tokens := [
		"_text(\"item_card_detail_hint\")",
		"_text(\"shop_no_hero_banner\")",
		"_text(\"shop_no_hero_yet\")",
		"_text(\"item_detail_owned\"",
		"_text(\"item_detail_description\")",
		"_text(\"item_detail_stats\")",
		"_text(\"item_detail_flavor\")",
		"_text(\"item_detail_close_hint\")",
		"_text(\"delivery_after_respawn\")",
		"_text(\"item_inventory_hint\")",
		"_text(\"queued\"",
		"hero_chips(world, forge(), localizer)",
	]
	var absent: Array = []
	for token in tokens:
		if panel_source.find(String(token)) < 0:
			absent.append(token)
	check.call(absent.is_empty(), "ITEM FORGE copy routes through tr() keys: %s" % str(absent))
	check.call(
		(
			shop_source.find("_text(localizer, \"dead\"") >= 0
			and shop_source.find("_text(localizer, \"queued\"") >= 0
			and shop_source.find("func hero_chips(world: Object, forge: Object, localizer: Object = null)")
			>= 0
		),
		"hero chips localise dead and queued through the injected runtime"
	)
	host.queue_free()


func _remove_test_files() -> void:
	for path in [TEST_PATH, TEST_PATH + ".bak", TEST_PATH + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
