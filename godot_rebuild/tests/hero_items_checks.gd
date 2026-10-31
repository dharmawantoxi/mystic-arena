extends RefCounted
## Layer 9ck: `hero_items.py` (4133 lines) — the item catalog, the Forge panel
## and the inventory behaviours were ported across layers 5d..5f; this layer
## closes the file with an explicit classification of every symbol plus the
## detail-popup mechanics text.
##
## * the inventory: 3 classes, 32 module functions, 63 methods and 47 module
##   constants, indexed by the eight `# ====` banners of the source file;
## * the 98 callables/classes + 47 constants, each classified once as
##   `ported` (a native function carries it), `data` (baked table), `folded`
##   (absorbed by a different native structure), `deviation` or `dead`, with a
##   live file + token for everything except the documented specials;
## * the catalog routing: 33 items, 25 categories, six pages of eight items,
##   the two cross-class overrides and the MAGIC_ONLY list;
## * the detail-popup mechanics: the 65 field labels, 8 group labels, the
##   percentage/frame key sets, 157 value-format rows and the header/bullet
##   lines of all 33 items in both languages, rendered by `ItemMechanics`.
##
## Sync: python3 godot_rebuild/tests/hero_items_source_oracle.py --write

const ItemMechanics = preload("res://scripts/match/item_mechanics.gd")
const HeroItems = preload("res://scripts/match/hero_items.gd")
const ItemShopUI = preload("res://scripts/match/item_shop_ui.gd")
const FIXTURE := "res://tests/fixtures/hero_items_source.json"
const MECHANICS_DATA := "res://data/ui/item_mechanics.json"

const TOTALS := {
	"lines": 4133,
	"classes": 3,
	"functions": 32,
	"methods": 63,
	"assigns": 47,
	"symbols": 98,
}
const CLASS_METHODS := {
	"HeroItemInventory": 44,
	"HeroItemRenderer": 3,
	"ItemShopUI": 16,
}
const KINDS := {"data": 43, "dead": 3, "deviation": 3, "folded": 1, "ported": 95}
const SYMBOL_COUNT := 98
const ROW_COUNT := 145
const DEAD_SYMBOLS := [
	"HeroItemInventory.is_guarding",
	"HeroItemRenderer.slot_index_at",
	"_alive_player_heroes",
]
const DEVIATION_SYMBOLS := [
	"_get_game",
	"_ICON_CACHE",
	"_ITEMS_DIR",
]
const TARGET_SOURCE_ONLY := ["dead", "deviation"]
const ITEM_COUNT := 33
const MECH_LINE_COUNT := 600
const CATEGORY_COUNT := 25
const PAGE_COUNT := 6
const FIELD_LABEL_COUNT := 65
const GROUP_LABEL_COUNT := 8
const PCT_KEY_COUNT := 28
const FRAME_KEY_COUNT := 11
const MECH_GROUPS := [
	"stats", "passive", "active", "aura", "block", "on_attack", "multishot", "bash"
]
# Three `hp_regen` values are written as floats (2.0 / 3.0 / 6.0) in the
# catalog; JSON numbers lose the int/float distinction, so the popup prints
# them without the trailing ".0". Documented in HERO_ITEMS_FOLDER_MIGRATION.md.
const FLOAT_SUFFIX_DEVIATIONS := ["hp_regen|2.0", "hp_regen|3.0", "hp_regen|6.0"]
const SOUND_IDS := ["ui_buy", "ui_click", "ui_error"]


static func _json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


static func _target_text(target: String) -> String:
	var local := "res://" + target
	if not FileAccess.file_exists(local):
		return ""
	return FileAccess.get_file_as_string(local)


static func _page_key(page: Variant) -> String:
	# JSON numbers come back as floats, so pages are compared as text.
	var ids: Array[String] = []
	for item_id in (page as Array):
		ids.append(String(item_id))
	return "|".join(ids)


static func _meta_key(entry: Variant) -> String:
	var row: Array = entry as Array
	return "%s:%d:%d" % [String(row[0]), int(row[1]), int(row[2])]


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "the hero_items fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_catalog(check, data)
	_check_labels(check, data)
	_check_format(check, data)
	_check_mechanics(check, data)
	_check_magic(check, data)


## The file really is the 4133-line item module this layer claims.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var file: Dictionary = data["file"]
	for key in TOTALS:
		check.call(
			int(file.get(key, -1)) == int(TOTALS[key]),
			"hero_items %s is %d (got %s)" % [key, int(TOTALS[key]), str(file.get(key))]
		)
	check.call(String(file.get("file", "")) == "hero_items.py", "the oracle reads hero_items.py")
	var sections: Array = data["sections"]
	check.call(sections.size() == 8, "the source keeps its eight section banners")
	var previous := 0
	var ordered := true
	for raw in sections:
		var section: Dictionary = raw
		if int(section["line"]) <= previous:
			ordered = false
		previous = int(section["line"])
	check.call(ordered, "the section banners stay in file order")
	var methods: Dictionary = data["class_methods"]
	check.call(methods.size() == CLASS_METHODS.size(), "three classes are indexed")
	for name in CLASS_METHODS:
		check.call(
			(methods.get(name, []) as Array).size() == int(CLASS_METHODS[name]),
			"%s keeps %d methods" % [name, int(CLASS_METHODS[name])]
		)


## Every symbol of the file carries a kind and a live target + token.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	var rows: Dictionary = data["classification"]
	check.call(int(symbols["count"]) == SYMBOL_COUNT, "98 callables/classes are classified")
	check.call(rows.size() == ROW_COUNT, "the 47 module constants join the classification")
	check.call(
		(symbols["items"] as Array).size() == SYMBOL_COUNT,
		"the symbol list keeps its own count"
	)
	var kinds: Dictionary = symbols["kinds"]
	for kind in KINDS:
		check.call(
			int(kinds.get(kind, -1)) == int(KINDS[kind]),
			"kind %s counts %d (got %s)" % [kind, int(KINDS[kind]), str(kinds.get(kind))]
		)
	var broken: Array = []
	var untargeted: Array = []
	for symbol in rows:
		var row: Dictionary = rows[symbol]
		var target := String(row["target"])
		var token := String(row["token"])
		if target.is_empty() or token.is_empty():
			if not TARGET_SOURCE_ONLY.has(String(row["kind"])):
				untargeted.append(symbol)
			continue
		if not _target_text(target).contains(token):
			broken.append("%s -> %s" % [symbol, target])
	check.call(
		broken.is_empty(),
		"every classification token is present in its target (%s)" % str(broken.slice(0, 5))
	)
	check.call(
		untargeted.is_empty(),
		"only dead/deviation rows may skip a Godot target (%s)" % str(untargeted.slice(0, 5))
	)
	var dead: Array = symbols["dead"]
	dead.sort()
	var wanted_dead: Array = DEAD_SYMBOLS.duplicate()
	wanted_dead.sort()
	check.call(dead == wanted_dead, "the three uncalled methods stay named as dead")
	var deviations: Array = symbols["deviations"]
	deviations.sort()
	var wanted_deviations: Array = DEVIATION_SYMBOLS.duplicate()
	wanted_deviations.sort()
	check.call(
		deviations == wanted_deviations,
		"the three deviations stay named, not quietly dropped"
	)
	var sound_ids: Array = []
	for symbol in ["_play_buy", "_play_click", "_play_error"]:
		sound_ids.append(String((rows[symbol] as Dictionary)["token"]).replace("\"", ""))
	sound_ids.sort()
	var wanted_sounds: Array = SOUND_IDS.duplicate()
	wanted_sounds.sort()
	check.call(sound_ids == wanted_sounds, "the three SFX ids keep their source names")


## 33 items across three classes and six pages of eight.
func _check_catalog(check: Callable, data: Dictionary) -> void:
	var catalog: Dictionary = data["catalog"]
	var items: Dictionary = catalog["items"]
	check.call(items.size() == ITEM_COUNT, "the catalog holds 33 items")
	check.call(int(catalog["max_slots"]) == 6, "MAX_ITEM_SLOTS is 6")
	check.call(int(catalog["flat_cost"]) == 4500, "ITEM_FLAT_COST is 4500")
	check.call(int(catalog["items_per_page"]) == 8, "ITEMS_PER_PAGE is 8")
	var categories: Dictionary = {}
	for item_id in items:
		categories[String((items[item_id] as Dictionary)["category"])] = true
	check.call(categories.size() == CATEGORY_COUNT, "the 25 categories are represented")
	var shop := ItemShopUI.new()
	check.call(shop.page_count() == PAGE_COUNT, "the shop holds six pages")
	var wanted_pages: Array = catalog["pages"]
	var wanted_meta: Array = catalog["page_meta"]
	var pages_ok: bool = (shop.pages as Array).size() == wanted_pages.size()
	for index in mini((shop.pages as Array).size(), wanted_pages.size()):
		if _page_key(shop.pages[index]) != _page_key(wanted_pages[index]):
			pages_ok = false
	var meta_ok: bool = (shop.page_meta as Array).size() == wanted_meta.size()
	for index in mini((shop.page_meta as Array).size(), wanted_meta.size()):
		if _meta_key(shop.page_meta[index]) != _meta_key(wanted_meta[index]):
			meta_ok = false
	check.call(pages_ok and meta_ok, "the ported pages + class meta match the source")
	var order: Array = []
	for page in shop.pages:
		for item_id in page:
			order.append(String(item_id))
	check.call(
		order == Array(catalog["shop_order"]),
		"the flattened shop order still lists all 33 items"
	)
	var classes_ok := true
	for item_id in items:
		if shop.item_class(String(item_id)) != String((items[item_id] as Dictionary)["class"]):
			classes_ok = false
	check.call(classes_ok, "every item keeps its source class")
	var overrides: Dictionary = catalog["class_overrides"]
	check.call(overrides.size() == 2, "the two cross-class overrides stay explicit")
	var magic_only: Array = []
	for item_id in items:
		if bool((items[item_id] as Dictionary)["magic_only"]):
			magic_only.append(String(item_id))
	magic_only.sort()
	check.call(magic_only == Array(catalog["magic_only"]), "the MAGIC_ONLY list matches")


## The detail-popup label tables.
func _check_labels(check: Callable, data: Dictionary) -> void:
	var labels: Dictionary = data["labels"]
	var fields: Dictionary = labels["field"]
	check.call(ItemMechanics.FIELD_LABELS.size() == FIELD_LABEL_COUNT, "65 field labels")
	check.call(fields.size() == FIELD_LABEL_COUNT, "the fixture keeps 65 field labels")
	var missing: Array = []
	for key in fields:
		var wanted: Array = fields[key]
		var got: Array = ItemMechanics.FIELD_LABELS.get(key, [])
		if got.size() != 2 or String(got[0]) != String(wanted[0]) \
				or String(got[1]) != String(wanted[1]):
			missing.append(key)
	check.call(missing.is_empty(), "every field label matches both languages (%s)" % str(missing))
	var groups: Dictionary = labels["group"]
	check.call(ItemMechanics.GROUP_LABELS.size() == GROUP_LABEL_COUNT, "8 group labels")
	var group_broken: Array = []
	for key in groups:
		var wanted: Array = groups[key]
		var got: Array = ItemMechanics.GROUP_LABELS.get(key, [])
		if got.size() != 2 or String(got[0]) != String(wanted[0]) \
				or String(got[1]) != String(wanted[1]):
			group_broken.append(key)
	check.call(group_broken.is_empty(), "group labels match (%s)" % str(group_broken))
	check.call(Array(ItemMechanics.MECH_GROUPS) == MECH_GROUPS, "the group order is the source order")
	check.call(
		Array(ItemMechanics.PCT_KEYS).size() == PCT_KEY_COUNT,
		"28 keys render as percentages"
	)
	check.call(
		Array(ItemMechanics.FRAME_KEYS).size() == FRAME_KEY_COUNT,
		"11 keys render as seconds"
	)
	var pct_ok: bool = Array(ItemMechanics.PCT_KEYS) == Array(labels["pct"])
	var frame_ok: bool = Array(ItemMechanics.FRAME_KEYS) == Array(labels["frame"])
	check.call(pct_ok and frame_ok, "the percentage + frame sets match the source")


## `_fmt_mech_value` over every (key, value) pair the catalog uses.
func _check_format(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["format"]
	check.call(rows.size() == 157, "157 distinct value formats are replayed")
	var broken: Array = []
	var tolerated: Array = []
	for raw in rows:
		var row: Dictionary = raw
		var key := String(row["key"])
		var value: Variant = row["value"]
		var probe: Variant = float(value) if String(row["kind"]) == "float" else int(value)
		for language in [[false, "id"], [true, "en"]]:
			var en := bool(language[0])
			var wanted := String(row[language[1]])
			var got: String = ItemMechanics.fmt_value(key, probe, en)
			if got == wanted:
				continue
			if FLOAT_SUFFIX_DEVIATIONS.has("%s|%s" % [key, str(value)]):
				tolerated.append("%s %s" % [key, str(value)])
				continue
			broken.append("%s %s: %s != %s" % [key, str(value), got, wanted])
	check.call(broken.is_empty(), "every value formats like the source (%s)" % str(broken.slice(0, 4)))
	check.call(
		tolerated.size() == FLOAT_SUFFIX_DEVIATIONS.size() * 2,
		"only the three documented float suffixes differ (%d)" % tolerated.size()
	)


## `_build_item_mechanics` over all 33 items, both languages.
func _check_mechanics(check: Callable, data: Dictionary) -> void:
	var groups: Dictionary = _json(MECHANICS_DATA)
	check.call(groups.size() == ITEM_COUNT, "the baked mechanics table covers 33 items")
	var wanted: Dictionary = data["mechanics"]
	var broken: Array = []
	var count := 0
	for language in [["id", false], ["en", true]]:
		var key := String(language[0])
		var en := bool(language[1])
		var table: Dictionary = wanted[key]
		check.call(table.size() == ITEM_COUNT, "the fixture keeps %s lines for 33 items" % key)
		for item_id in table:
			var entry: Variant = groups.get(item_id, {})
			var built: Array = ItemMechanics.build(entry, en) if entry is Dictionary else []
			var expected: Array = table[item_id]
			count += expected.size()
			if built.size() != expected.size():
				broken.append("%s/%s size" % [item_id, key])
				continue
			for index in range(expected.size()):
				var want: Array = expected[index]
				var got: Array = built[index]
				if String(got[0]) != String(want[0]) or String(got[1]) != String(want[1]):
					broken.append("%s/%s:%d" % [item_id, key, index])
					break
	check.call(
		broken.is_empty(),
		"the mechanics headers + bullets match the source (%s)" % str(broken.slice(0, 4))
	)
	check.call(count == MECH_LINE_COUNT, "the replay covers all 600 mechanics lines (%d)" % count)
	var empty: Array = []
	for item_id in groups:
		if (groups[item_id] as Dictionary).is_empty():
			empty.append(item_id)
	check.call(empty.is_empty(), "every catalog item carries at least one group")


## The MAGIC_ONLY gate, including the "Anti-Mage" exception.
func _check_magic(check: Callable, data: Dictionary) -> void:
	var magic: Dictionary = data["magic"]
	var broken: Array = []
	for role in magic:
		if HeroItems.is_magic_hero(String(role)) != bool(magic[role]):
			broken.append(String(role))
	check.call(broken.is_empty(), "the magic role gate matches the source (%s)" % str(broken))
	check.call(not bool(magic.get("Anti-Mage", true)), "Anti-Mage stays excluded")
