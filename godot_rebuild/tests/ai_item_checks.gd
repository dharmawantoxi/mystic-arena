extends RefCounted
## Native AI item metadata versus the real hero_items.ITEM_CATALOG exec.
## Metadata only: no stat effects, passives or Forge UI are ported here.

const METADATA := "res://data/ai/item_catalog.json"
const FIXTURE := "res://tests/fixtures/ai_items_source.json"
# Source counts read from the executed ITEM_CATALOG (oracle asserts them too).
const ITEM_COUNT := 33
const MELEE_ONLY_COUNT := 1
const MAGIC_ONLY_COUNT := 8
const DROPS_ON_DEATH_COUNT := 1


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	_test_catalog(fixture.catalog, check)


func _test_catalog(expected: Dictionary, check: Callable) -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
	check.call(data == expected, "AI item catalog matches the source ITEM_CATALOG metadata")
	check.call(int(data.max_slots) == 6, "Source MAX_ITEM_SLOTS is six")
	check.call(int(data.flat_cost) == 4500, "Source ITEM_FLAT_COST is 4500")
	var items: Dictionary = data.items
	check.call(items.size() == ITEM_COUNT, "Source ITEM_CATALOG holds 33 items")
	var melee := 0
	var magic := 0
	var drops := 0
	var flat := 0
	for item_id in items:
		var entry: Dictionary = items[item_id]
		check.call(String(entry.name) != "", "Item name must exist: " + item_id)
		check.call((entry.category as String) in data.categories, "Unknown category: " + item_id)
		check.call(int(entry.cost) > 0, "Item cost must be positive: " + item_id)
		if bool(entry.melee_only):
			melee += 1
		if bool(entry.magic_only):
			magic += 1
		if bool(entry.drops_on_death):
			drops += 1
		if int(entry.cost) == int(data.flat_cost):
			flat += 1
	check.call(melee == MELEE_ONLY_COUNT, "Exactly one source item is melee only")
	check.call(magic == MAGIC_ONLY_COUNT, "Eight source items are magic only")
	check.call(drops == DROPS_ON_DEATH_COUNT, "Only Holy Rapier drops on death")
	check.call(flat < ITEM_COUNT, "Not every source item uses the flat price")
	check.call(bool(items.cleave_axe.melee_only), "Cleave Axe is melee only")
	check.call(bool(items.astral_codex.magic_only), "Astral Codex is magic only")
	check.call(bool(items.holy_rapier.drops_on_death), "Holy Rapier is lost on death")
