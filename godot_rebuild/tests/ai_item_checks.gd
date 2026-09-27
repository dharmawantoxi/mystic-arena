extends RefCounted
## Native AI item metadata versus the real hero_items.ITEM_CATALOG exec.
## Metadata only: no stat effects, passives or Forge UI are ported here.

const HeroItems = preload("res://scripts/match/hero_items.gd")
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
	_test_magic_roles(fixture.magic_roles, check)
	_test_suggestions(fixture.suggestions, check)
	_test_pools(fixture.pools, check)


func _expected(row: Dictionary) -> String:
	# The source returns None when no pool entry survives the gates.
	return "" if row.suggestion == null else String(row.suggestion)


func _owned(values: Array) -> Array:
	var owned: Array = []
	for value in values:
		owned.append(String(value))
	return owned


func _test_magic_roles(rows: Array, check: Callable) -> void:
	for row in rows:
		var role: String = String(row.role)
		check.call(
			HeroItems.is_magic_hero(role) == bool(row.is_magic),
			"AI is_magic_hero must match source for role: " + role
		)
	check.call(not HeroItems.is_magic_hero("Anti-Mage"), "Anti-Mage is not a magic hero")
	check.call(HeroItems.is_magic_hero("Mage/Trickster"), "Mage/Trickster is a magic hero")


func _test_suggestions(rows: Array, check: Callable) -> void:
	var items := HeroItems.new()
	for row in rows:
		var role: String = String(row.role)
		var attack_range := float(row.range)
		var owned := _owned(row.owned)
		var suggested := items.suggest_item_for_hero(role, attack_range, owned)
		check.call(
			suggested == _expected(row),
			"AI suggestion for %s/%d must match source" % [role, int(attack_range)]
		)
		check.call(
			items.is_melee(attack_range) == (HeroItems.source_range(attack_range) <= 80.0),
			"AI melee range gate is 80 px"
		)
		if suggested != "":
			check.call(items.item_cost(suggested) > 0, "AI suggestion must exist in catalog")


func _test_pools(rows: Array, check: Callable) -> void:
	var items := HeroItems.new()
	for row in rows:
		var role: String = String(row.role)
		var attack_range := float(row.range)
		var order: Array = []
		var owned: Array = []
		while order.size() <= items.max_slots() + 40:
			var next_id := items.suggest_item_for_hero(role, attack_range, owned)
			if next_id == "":
				break
			order.append(next_id)
			owned.append(next_id)
		var expected: Array = []
		for value in row.order:
			expected.append(String(value))
		check.call(
			order == expected,
			"AI purchase order for %s/%d must match source pool" % [role, int(attack_range)]
		)
		check.call(
			items.suggest_item_for_hero(role, attack_range, expected) == "",
			"AI suggestion is empty once the whole pool is owned"
		)


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
