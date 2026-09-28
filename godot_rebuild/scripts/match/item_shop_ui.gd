extends RefCounted
## Port of the ITEM FORGE panel half of hero_items.py (layer 5f-2): the paging
## `get_item_class`/`_build_shop_pages`/`CLASS_ITEM_ORDER` builds, the panel
## state (`item_shop_open`, `itemshop_page`, `itemshop_inspect_item`) and the
## click routing of `handle_item_shop_click` (button-id vocabulary
## `itemshop_close` / `_hero_` / `_page_` / `_buy_` / `_slot_` / `_card_` /
## `_detail_close_`).
##
## NOT ported here, by design: pygame geometry (`PANEL_W/H`, rects, hit tests),
## fonts/colors and localization. The panel therefore exposes view data
## (`hero_chips()`, `item_cards()`, `page_tabs()`) for a Control to draw, a
## `click_outside_panel()` hook for the one geometry rule the source keeps
## (`item_shop_open = False`), and message keys instead of `tr()` strings
## ("dead", "Lv.N", "BUY FOR").

const METADATA := "res://data/ai/item_catalog.json"
const CLASS_PHYSICAL := "physical"
const CLASS_MAGIC := "magic"
const CLASS_TANK := "tank"
const ITEMS_PER_PAGE := 8
# Source ITEM_CLASS_INFO: class id -> tab label (colors stay in the theme).
const CLASS_LABELS := {
	CLASS_PHYSICAL: "PHYSICAL",
	CLASS_MAGIC: "MAGIC",
	CLASS_TANK: "TANK",
}
# Source _ITEM_CLASS_OVERRIDES: cross-class items decided one by one.
const CLASS_OVERRIDES := {
	"tempest_vane": CLASS_TANK,
	"abyss_breaker": CLASS_TANK,
}
# Source _MAP_CATEGORY_TO_CLASS.
const CATEGORY_TO_CLASS := {
	"caster": CLASS_MAGIC,
	"arcane": CLASS_MAGIC,
	"mystic": CLASS_MAGIC,
	"tank": CLASS_TANK,
	"guard": CLASS_TANK,
	"thorn": CLASS_TANK,
	"frost": CLASS_TANK,
	"inferno": CLASS_TANK,
	"as_armor": CLASS_TANK,
	"mortal": CLASS_TANK,
}
# Source CLASS_ITEM_ORDER, verbatim (comments there describe the classes).
const CLASS_ITEM_ORDER := {
	CLASS_PHYSICAL:
	[
		"dead_edge",
		"holy_rapier",
		"demon_maw",
		"cleave_axe",
		"moon_shard",
		"monarch_wings",
		"corroder",
		"fenrir_chain",
		"sanguine_thorn",
		"thunder_coil",
		"sundering_cudgel",
		"frostbound_eye",
		"gale_pike",
		"basilisk_breath",
	],
	CLASS_MAGIC:
	[
		"octarine_core",
		"runic_gavel",
		"astral_codex",
		"sage_scepter",
		"fulgur_scepter",
		"hex_idol",
		"rift_veil",
		"vital_stone",
		"vine_rod",
		"spectral_charm",
	],
	CLASS_TANK:
	[
		"leviathan_heart",
		"steel_aegis",
		"scarlet_bulwark",
		"tempest_vane",
		"abyss_breaker",
		"razor_carapace",
		"everfrost_guard",
		"solar_brand",
		"searbrand",
	],
}

# Button-id vocabulary of the click router, in source dispatch order.
const CLICK_PREFIXES := [
	"itemshop_hero_",
	"itemshop_page_",
	"itemshop_buy_",
	"itemshop_slot_",
	"itemshop_card_",
]
# Source `game.item_shop_open` / `itemshop_page` / `itemshop_inspect_item`.
var is_open := false
var page := 0
var inspect_item := ""
# Last "BUY FOR" announcement: {hero_id, dead} (source notifies a tr() text).
var notice: Dictionary = {}
var pages: Array = []
var page_meta: Array = []


func _init() -> void:
	_build_shop_pages()


func _catalog() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
	return {} if parsed == null else parsed


func item_class(item_id: String) -> String:
	# Port of get_item_class: unknown items fall back to PHYSICAL.
	var items: Dictionary = _catalog().get("items", {})
	if not items.has(item_id):
		return CLASS_PHYSICAL
	if CLASS_OVERRIDES.has(item_id):
		return String(CLASS_OVERRIDES[item_id])
	var data: Dictionary = items[item_id]
	if bool(data.get("magic_only", false)):
		return CLASS_MAGIC
	return String(CATEGORY_TO_CLASS.get(String(data.get("category", "")), CLASS_PHYSICAL))


func _build_shop_pages() -> void:
	# Port of _build_shop_pages: each class gets whole pages of ITEMS_PER_PAGE.
	pages = []
	page_meta = []
	for class_id in [CLASS_PHYSICAL, CLASS_MAGIC, CLASS_TANK]:
		var ids: Array = CLASS_ITEM_ORDER[class_id]
		var count: int = maxi(1, int(ceil(float(ids.size()) / float(ITEMS_PER_PAGE))))
		for index in range(count):
			var start := index * ITEMS_PER_PAGE
			pages.append(ids.slice(start, start + ITEMS_PER_PAGE))
			page_meta.append([class_id, index + 1, count])


func page_count() -> int:
	return pages.size()


func current_page_items() -> Array:
	var index := page
	if index < 0 or index >= pages.size():
		index = 0
	return pages[index]


func page_tabs() -> Array:
	# Source tab label: "PHYSICAL 1/2", colored by class in the theme.
	var tabs: Array = []
	for entry in page_meta:
		var class_id := String(entry[0])
		tabs.append("%s %d/%d" % [String(CLASS_LABELS[class_id]), int(entry[1]), int(entry[2])])
	return tabs


func hero_chips(world: Object, forge: Object) -> Array:
	# Source chip line 2: "dead"/"Lv.N", "Item used/max" and a queued suffix.
	var chips: Array = []
	var heroes: Array = forge._player_heroes(world)
	for index in range(heroes.size()):
		var hero: Object = heroes[index]
		var used: int = hero.items.used_slots()
		var queued: int = hero.pending_items.size()
		var status := "dead" if not bool(hero.alive) else "Lv.%d" % int(hero.level)
		var label := "%s  Item %d/%d" % [status, used, hero.items.max_slots()]
		if queued > 0:
			label += "  +%d queued" % queued
		(
			chips
			. append(
				{
					"index": index,
					"hero_id": int(hero.id),
					"alive": bool(hero.alive),
					"level": int(hero.level),
					"used": used,
					"max_slots": hero.items.max_slots(),
					"queued": queued,
					"status": status,
					"label": label,
					"is_target": int(hero.id) == int(forge.target_hero_id),
				}
			)
		)
	return chips


func item_cards(world: Object, forge: Object) -> Array:
	# Grid entries of the current page; `owned` mirrors the source card badge.
	var hero: Object = forge.resolve_target(forge._player_heroes(world))
	var items: Dictionary = _catalog().get("items", {})
	var cards: Array = []
	for item_id in current_page_items():
		var data: Dictionary = items.get(String(item_id), {})
		var cost := int(data.get("cost", 0))
		(
			cards
			. append(
				{
					"id": String(item_id),
					"name": String(data.get("name", item_id)),
					"class": item_class(String(item_id)),
					"cost": cost,
					"affordable": forge.player_gold(world) >= cost,
					"owned": hero != null and hero.items.has(String(item_id)),
				}
			)
		)
	return cards


func handle_click(world: Object, forge: Object, button_id: String, button: int) -> bool:
	# Port of handle_item_shop_click's routing (no hit tests: the Control that
	# draws the panel already resolved which button id was pressed).
	if not is_open:
		return false
	if inspect_item != "" and _catalog().get("items", {}).has(inspect_item):
		return _handle_inspect_click(button_id)
	if button_id == "itemshop_close":
		is_open = false
		return true
	for prefix in CLICK_PREFIXES:
		if not button_id.begins_with(String(prefix)):
			continue
		_dispatch(world, forge, String(prefix), button_id, button)
		return true
	return false


func _handle_inspect_click(button_id: String) -> bool:
	# Detail popup: the two close buttons act, a click inside the detail box is
	# held (the Control checks that rect), anything else only closes the popup.
	if button_id == "itemshop_detail_hold":
		return true
	if button_id != "itemshop_detail_close" and button_id != "itemshop_close":
		inspect_item = ""
		return true
	inspect_item = ""
	if button_id == "itemshop_close":
		is_open = false
	return true


func _dispatch(
	world: Object, forge: Object, prefix: String, button_id: String, button: int
) -> void:
	if prefix == "itemshop_hero_":
		var index := _parse_suffix(button_id, prefix)
		var heroes: Array = forge._player_heroes(world)
		if index >= 0 and index < heroes.size():
			var hero: Object = heroes[index]
			forge.set_target(int(hero.id))
			notice = {"hero_id": int(hero.id), "dead": not bool(hero.alive)}
	elif prefix == "itemshop_page_":
		var wanted := _parse_suffix(button_id, prefix)
		if wanted >= 0 and wanted < page_count():
			page = wanted
	elif prefix == "itemshop_buy_":
		forge.buy(world, button_id.replace(prefix, ""))
	elif prefix == "itemshop_slot_":
		_slot_click(world, forge, button_id, button)
	else:
		# itemshop_card_: open the detail popup for that item.
		inspect_item = button_id.replace(prefix, "")


func _slot_click(world: Object, forge: Object, button_id: String, button: int) -> void:
	var slot := _parse_suffix(button_id, "itemshop_slot_")
	var shop_hero: Object = forge._shop_hero(world)
	if shop_hero == null or slot < 0 or slot >= shop_hero.items.max_slots():
		return
	if button == 3:
		# Hold / right click on a slot drops the item (source: no refund).
		forge.drop(world, slot)
	elif button == 1 and shop_hero.items.slots[slot] != null:
		# Tap a filled slot to inspect the item; empty slots stay inert.
		inspect_item = String(shop_hero.items.slots[slot])


func click_outside_panel() -> bool:
	# Source: a left click outside the panel rect closes the shop.
	if not is_open:
		return false
	is_open = false
	return true


func notice_text() -> String:
	# Source notification: "BUY FOR: <name>" plus a respawn suffix for a dead
	# target. The rebuild has no hero display name, so the id stands in.
	if notice.is_empty():
		return ""
	var text := "BUY FOR: hero %d" % int(notice.get("hero_id", -1))
	if bool(notice.get("dead", false)):
		text += " (delivery after respawn)"
	return text


func _parse_suffix(button_id: String, prefix: String) -> int:
	var raw := button_id.replace(prefix, "")
	return int(raw) if raw.is_valid_int() else -1
