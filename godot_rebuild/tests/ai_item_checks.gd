extends RefCounted
## Native AI item metadata versus the real hero_items.ITEM_CATALOG exec.
## Metadata only: no stat effects, passives or Forge UI are ported here.

const World = preload("res://scripts/match/prototype_battle.gd")
const HeroItems = preload("res://scripts/match/hero_items.gd")
const Inventory = preload("res://scripts/match/hero_item_inventory.gd")
const AIItems = preload("res://scripts/match/ai_items.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const METADATA := "res://data/ai/item_catalog.json"
const FIXTURE := "res://tests/fixtures/ai_items_source.json"
# Source counts read from the executed ITEM_CATALOG (oracle asserts them too).
const ITEM_COUNT := 33
const MELEE_ONLY_COUNT := 1
const MAGIC_ONLY_COUNT := 8
const DROPS_ON_DEATH_COUNT := 1
# Fixture hero specs are (role, attack range) pairs of the starter kits.
const STAT_HEROES := {"Bruiser": "thorne", "Mage": "vex"}
const ROLE_HEROES := {
	"Assassin|70": "kaizen",
	"Bruiser|70": "thorne",
	"Fighter|70": "grimjaw",
	"Marksman|130": "sylara",
	"Mage|130": "vex",
	"Mage/Trickster|130": "zephyr",
}
# Getter names the oracle records, in source order.
const STAT_GETTERS := [
	"get_bonus_damage",
	"get_bonus_hp",
	"get_hp_pct",
	"get_armor",
	"get_hp_regen",
	"get_max_hp",
	"get_attack_speed_mult",
	"get_lifesteal_pct",
	"get_crit",
	"get_cleave",
	"get_cooldown_reduction",
	"get_spell_vamp",
	"get_skill_amp",
	"get_evasion",
	"get_move_speed_pct",
	"get_heal_amp",
	"get_slow_resist",
	"get_range_bonus",
	"has_true_strike",
	"get_reflect_pct",
	"get_gale_as_bonus",
	"get_block",
	"get_armor_shred",
	"get_on_attack_chain",
	"get_bash",
	"is_veiled",
	"is_guarding",
	"get_rend_crit",
]
# Six affordable non-magic items: parks the free red Kaizen out of the pool.
const PARK_ITEMS := [
	"cleave_axe",
	"dead_edge",
	"basilisk_breath",
	"gale_pike",
	"frostbound_eye",
	"sundering_cudgel",
]


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	_test_catalog(fixture.catalog, check)
	_test_magic_roles(fixture.magic_roles, check)
	_test_suggestions(fixture.suggestions, check)
	_test_pools(fixture.pools, check)
	_test_inventory(fixture.inventory, check)
	_test_hero_inventory(check)
	_test_purchases(fixture.purchases, check)
	_test_stats(fixture.stats, check)
	_test_stat_application(fixture.stat_application, check)
	_test_heal_amp(check)
	_test_deaths(fixture.deaths, check)


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
	var categories: Dictionary = data.categories
	var melee := 0
	var magic := 0
	var drops := 0
	var flat := 0
	for item_id in items:
		var entry: Dictionary = items[item_id]
		var label := String(item_id)
		check.call(String(entry.name) != "", "Item name must exist: " + label)
		# categories maps category id -> source CATEGORY_* constant name.
		check.call(categories.has(String(entry.category)), "Unknown category: " + label)
		check.call(
			String(categories[String(entry.category)]).begins_with("CATEGORY_"),
			"Category must keep its source constant name: " + label
		)
		check.call(int(entry.cost) > 0, "Item cost must be positive: " + label)
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


func _slot_values(values: Array) -> Array:
	var slots: Array = []
	for value in values:
		slots.append(null if value == null else String(value))
	return slots


func _apply(inventory: Inventory, op: Array) -> Variant:
	var op_name := String(op[0])
	if op_name == "add":
		return inventory.add(String(op[1]))
	if op_name == "remove":
		return inventory.remove(int(op[1]))
	if op_name == "count":
		return inventory.count(String(op[1]))
	if op_name == "has":
		return inventory.has(String(op[1]))
	if op_name == "used_slots":
		return inventory.used_slots()
	return inventory.clear_on_death()


func _expected_result(op: Array, value: Variant) -> Variant:
	var op_name := String(op[0])
	if op_name == "remove":
		# Source returns None for a refused drop, the id otherwise.
		return "" if value == null else String(value)
	if op_name == "count" or op_name == "used_slots":
		return int(value)
	return bool(value)


func _test_inventory(rows: Array, check: Callable) -> void:
	for row in rows:
		var spec: Dictionary = row.hero
		var inventory := Inventory.new()
		inventory.set_hero_gate(String(spec.role), float(spec.range))
		var label := "%s/%d" % [String(spec.role), int(spec.range)]
		check.call(inventory.max_slots() == 6, "AI inventory keeps six slots for " + label)
		for entry in row.log:
			var op: Array = entry.op
			# Typed Variant: _apply returns bool/int/String and `:=` from a
			# Variant is a parse error in this project.
			var result: Variant = _apply(inventory, op)
			check.call(
				result == _expected_result(op, entry.result),
				"AI inventory op %s must match source on %s" % [str(op), label]
			)
			check.call(
				inventory.slots == _slot_values(entry.slots),
				"AI inventory slots after %s on %s" % [str(op), label]
			)
			check.call(
				inventory.used_slots() == int(entry.used),
				"AI inventory used slots after %s on %s" % [str(op), label]
			)


func _test_hero_inventory(check: Callable) -> void:
	# Real domain: HeroState owns the inventory and refreshes the role/range
	# gate from its definition at spawn.
	var world := World.new()
	world.defender_enabled = false
	world.setup_arena()
	var melee := world.spawn_hero(World.KAIZEN, world.RED, Vector2(1000, 200))
	var mage := world.spawn_hero(World.VEX, world.RED, Vector2(1040, 240))
	var ranged := world.spawn_hero(World.SYLARA, world.RED, Vector2(1080, 280))
	check.call(melee != null and mage != null and ranged != null, "AI item heroes spawn")
	check.call(melee.items.max_slots() == 6, "Hero inventory owns six slots")
	check.call(melee.items.used_slots() == 0, "Hero inventory starts empty")
	check.call(
		melee.items.hero_role == "Assassin" and melee.items.hero_range == 70.0,
		"Hero inventory gate follows the definition"
	)
	check.call(
		melee.items.hero_base_hp == melee.base_hp and melee.items.hero_level == melee.level,
		"Hero inventory scaling follows the hero"
	)
	check.call(
		melee.items.hero_melee_flag == 1 and mage.items.hero_melee_flag == 0,
		"Hero inventory melee flag follows the source range < 110 rule"
	)
	check.call(
		int(melee.items.get_max_hp()) == int(melee.max_hp),
		"Empty inventory max HP equals the source level formula"
	)
	var max_hp := melee.max_hp
	var hp := melee.hp
	check.call(melee.items.add("cleave_axe"), "Melee hero equips the melee only item")
	check.call(not melee.items.add("astral_codex"), "Non-magic role cannot equip a magic only item")
	check.call(mage.items.add("astral_codex"), "Magic role equips the magic only item")
	check.call(not ranged.items.add("cleave_axe"), "Ranged hero cannot equip a melee only item")
	check.call(melee.items.owned() == ["cleave_axe"], "Hero inventory lists owned items")
	check.call(melee.items.count("cleave_axe") == 1, "Hero inventory counts an item once")
	check.call(
		melee.max_hp == max_hp and melee.hp == hp,
		"Item purchase must not change hero HP: stat effects are not ported"
	)
	# The same purchase DOES move source max HP, so the gap above is a known
	# limitation recorded by the oracle, not an accident.
	var source_start := 0
	var source_after := 0
	for row in JSON.parse_string(FileAccess.get_file_as_string(FIXTURE)).inventory:
		var spec: Dictionary = row.hero
		if String(spec.role) == "Bruiser":
			source_start = int(row.start[0])
			source_after = int(row.log[0].max_hp)
	check.call(
		source_after > source_start,
		"Source equip raises max HP, which this rebuild does not port yet"
	)
	check.call(melee.items.remove(0) == "cleave_axe", "Hero inventory drop returns the item id")
	check.call(melee.items.used_slots() == 0, "Hero inventory slot is empty after the drop")
	check.call(not melee.items.clear_on_death(), "Hero without a rapier drops nothing on death")
	check.call(mage.items.add("holy_rapier"), "Magic hero equips Holy Rapier")
	check.call(mage.items.clear_on_death(), "Holy Rapier is destroyed on death")
	check.call(not mage.items.has("holy_rapier"), "Holy Rapier is gone after death")
	check.call(
		mage.items.used_slots() == 1 and mage.items.has("astral_codex"),
		"Death only destroys the rapier, the other slot survives"
	)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.setup_arena()
	return world


func _fund(world: World, gold: int) -> void:
	world.economy = Economy.new()
	world.economy.gold[1] = gold
	world.economy.opening[1] = gold


func _draft(reserved: int) -> Draft:
	var draft := Draft.new()
	draft.purchase_target = "kaizen" if reserved > 0 else ""
	draft.purchase_target_cost = reserved
	return draft


func _nullable(value: Variant) -> String:
	return "" if value == null else String(value)


func _buy_heroes(world: World, specs: Array) -> Array[int]:
	# The free red Kaizen of setup_arena is not part of the source roster: fill
	# its six slots so the source candidate filter (used < MAX) drops it.
	for unit in world.units:
		if unit.is_hero and unit.team == 1:
			var parked := unit as World.HeroState
			for item_id in PARK_ITEMS:
				assert(parked.items.add(String(item_id)))
	var ids: Array[int] = []
	for index in range(specs.size()):
		var spec: Dictionary = specs[index]
		var key := "%s|%d" % [String(spec.role), int(spec.range)]
		var hero_type: String = ROLE_HEROES[key]
		var definition: Variant = World.PLAYABLE_AI_HEROES[hero_type]
		var hero := world.spawn_hero(definition, 1, Vector2(1000 + index * 40, 200))
		assert(hero != null)
		assert(hero.settings().role == String(spec.role), "fixture role must match the kit")
		assert(int(hero.attack_range) == int(spec.range), "fixture range must match the kit")
		for previous in range(1, int(spec.level)):
			world._upgrade_hero_for(1, hero.id, previous)
		hero.kills = int(spec.kills)
		if not bool(spec.alive):
			hero.alive = false
		for item_id in spec.owned:
			assert(hero.items.add(String(item_id)), "fixture pre-owned item refused")
		ids.append(hero.id)
	return ids


func _used(world: World, ids: Array[int]) -> Array:
	var used: Array = []
	for entity_id in ids:
		var hero := world.get_unit(entity_id) as World.HeroState
		used.append(hero.items.used_slots())
	return used


func _test_purchases(rows: Array, check: Callable) -> void:
	for row in rows:
		var world := _world()
		_fund(world, 1000000)
		var ids := _buy_heroes(world, row.heroes)
		_fund(world, int(row.gold))
		var draft := _draft(int(row.reserve))
		var buyer := AIItems.new()
		var used := _used(world, ids)
		var calls: Array = []
		var bought := 0
		while calls.size() <= ids.size() * 7:
			var success := buyer.try_buy_priority(world, draft)
			var entry := {"success": success, "gold": world.economy.gold[1], "tag": -1, "item": ""}
			if success:
				bought += 1
				for index in range(ids.size()):
					var hero := world.get_unit(ids[index]) as World.HeroState
					if hero.items.used_slots() > int(used[index]):
						used[index] = hero.items.used_slots()
						entry["tag"] = index
						entry["item"] = hero.items.owned()[-1]
			calls.append(entry)
			if not success:
				break
		var expected: Array = row.calls
		check.call(
			calls.size() == expected.size(),
			"AI item purchase call count must match source for gold %d" % int(row.gold)
		)
		for index in range(mini(calls.size(), expected.size())):
			var want: Dictionary = expected[index]
			var got: Dictionary = calls[index]
			check.call(
				bool(got.success) == bool(want.success), "AI item purchase success at " + str(index)
			)
			check.call(
				int(got.tag) == int(want.tag), "AI item purchase candidate order at " + str(index)
			)
			check.call(
				_nullable(got.item) == _nullable(want.item),
				"AI item purchase choice at " + str(index)
			)
			check.call(int(got.gold) == int(want.gold), "AI item purchase balance at " + str(index))
		check.call(world.economy.gold[1] == int(row.gold) - int(row.spent), "AI item exact spend")
		check.call(world.economy.is_balanced(), "AI item ledger invariant")
		var events := 0
		for event in world.recent_events:
			if String(event.kind) == "hero_item":
				events += 1
		check.call(events == bought, "AI item purchase records one ledger event")
		var slots: Array = []
		for entity_id in ids:
			var hero := world.get_unit(entity_id) as World.HeroState
			slots.append(hero.items.slots.duplicate())
		var want_slots: Array = []
		for value in row.slots:
			want_slots.append(_slot_values(value))
		check.call(slots == want_slots, "AI item final slots must match source")
		check.call(draft.reserve() == int(row.reserve), "AI item purchase keeps the draft reserve")


func _array_equal(actual: Variant, expected: Array) -> bool:
	if not actual is Array or (actual as Array).size() != expected.size():
		return false
	for index in range(expected.size()):
		if not _stat_equal((actual as Array)[index], expected[index]):
			return false
	return true


func _stat_equal(actual: Variant, expected: Variant) -> bool:
	# The fixture stores Python tuples as arrays and None as null.
	if expected == null or actual == null:
		return actual == null and expected == null
	if expected is Array:
		return _array_equal(actual, expected)
	if expected is Dictionary:
		return actual == expected
	if expected is bool:
		return bool(actual) == bool(expected)
	return float(actual) == float(expected)


func _test_stats(rows: Array, check: Callable) -> void:
	for row in rows:
		var spec: Dictionary = row.hero
		var inventory := Inventory.new()
		inventory.set_hero_gate(String(spec.role), float(spec.range))
		var melee_flag := -1
		if spec.is_melee_hero != null:
			melee_flag = 1 if bool(spec.is_melee_hero) else 0
		inventory.set_hero_scaling(int(spec.base_hp), int(spec.level), melee_flag)
		for item_id in row.loadout:
			assert(inventory.add(String(item_id)), "stat loadout refused an item")
		var values: Dictionary = row.values
		var label := "%s/%d %s" % [String(spec.role), int(spec.range), str(row.loadout)]
		check.call(inventory.slots == _slot_values(row.slots), "AI stat loadout slots: " + label)
		for getter in STAT_GETTERS:
			var key := String(getter)
			check.call(
				_stat_equal(inventory.call(key), values[key]),
				"AI item stat %s must match source: %s" % [key, label]
			)
		check.call(
			_stat_equal(inventory.consume_empower_strike(), values["empower_strike"]),
			"AI Runic Gavel empower strike must match source: " + label
		)
		check.call(
			_stat_equal(inventory.empower_charge, values["empower_charge"]),
			"AI Runic Gavel charge must match source: " + label
		)
		# Timers are inert in this layer: every timer-gated branch stays closed.
		check.call(
			(
				inventory.blood_frenzy_timer == 0
				and inventory.ghost_timer == 0
				and inventory.thorn_timer == 0
				and inventory.gale_timer == 0
				and inventory.veil_timer == 0
				and inventory.guard_timer == 0
				and inventory.rend_timer == 0
			),
			"AI item timers stay inert until the active/passive layer: " + label
		)


func _test_stat_application(rows: Array, check: Callable) -> void:
	for row in rows:
		var spec: Dictionary = row.hero
		var world := _world()
		var kit: String = STAT_HEROES[String(spec.role)]
		var hero := world.spawn_hero(World.PLAYABLE_AI_HEROES[kit], 1, Vector2(1000, 200))
		hero.base_hp = int(spec.base_hp)
		hero.level = int(spec.level)
		hero.apply_level_stats()
		hero.hp = hero.max_hp
		var label := "%s base %d lv %d" % [String(spec.role), int(spec.base_hp), int(spec.level)]
		check.call(
			int(hero.max_hp) == int(row.start[0]) and int(hero.hp) == int(row.start[1]),
			"AI item hero starts full at the source max HP: " + label
		)
		for entry in row.log:
			var op := String(entry.op)
			var parts := op.split(":")
			match parts[0]:
				"add":
					assert(hero.items.add(parts[1]), "stat application equip refused")
					hero.apply_item_change()
				"remove":
					hero.items.remove(int(parts[1]))
					hero.apply_item_change()
				"clear_on_death":
					hero.items.clear_on_death()
					hero.apply_item_change()
				_:
					assert(hero.upgrade(), "stat application upgrade refused")
			check.call(
				int(hero.max_hp) == int(entry.max_hp),
				"AI item max HP after %s must match source: %s" % [op, label]
			)
			check.call(
				int(hero.hp) == int(entry.hp),
				"AI item current HP after %s must match source: %s" % [op, label]
			)
			check.call(
				hero.heal_amp_amount == float(entry.heal_amp_amount),
				"AI item heal amp amount after %s must match source: %s" % [op, label]
			)
			check.call(
				hero.heal_amp_timer == int(entry.heal_amp_timer),
				"AI item heal amp timer after %s must match source: %s" % [op, label]
			)
			check.call(
				hero.items.slots == _slot_values(entry.slots),
				"AI item slots after %s must match source: %s" % [op, label]
			)


func _test_heal_amp(check: Callable) -> void:
	# Source hp setter: the cap is applied by the caller, the amp afterwards.
	var world := _world()
	var hero := world.spawn_hero(World.VEX, 1, Vector2(1000, 200))
	assert(hero.items.add("abyss_breaker"))
	hero.apply_item_change()
	check.call(is_equal_approx(hero.heal_amp_amount, 0.16), "Abyss Breaker grants 16% heal amp")
	check.call(hero.heal_amp_timer == 999999, "Item heal amp uses the source duration")
	hero.hp = hero.max_hp - 500.0
	hero.heal_hp(100.0)
	check.call(
		is_equal_approx(hero.hp, hero.max_hp - 500.0 + 116.0),
		"Heal amp must amplify incoming heals by 16%"
	)


func _test_deaths(rows: Array, check: Callable) -> void:
	for row in rows:
		var spec: Dictionary = row.hero
		var world := _world()
		var kit: String = STAT_HEROES[String(spec.role)]
		var hero := world.spawn_hero(World.PLAYABLE_AI_HEROES[kit], 1, Vector2(1000, 200))
		hero.base_hp = int(spec.base_hp)
		hero.level = int(spec.level)
		hero.apply_level_stats()
		hero.hp = hero.max_hp
		for item_id in row.loadout:
			assert(hero.items.add(String(item_id)), "death loadout refused an item")
		var killer: World.HeroState = null
		for unit in world.units:
			if unit.is_hero and unit.team == 0:
				killer = unit as World.HeroState
		check.call(
			hero.items.has("holy_rapier") == bool(row.dropped),
			"Rapier presence must match the source drop flag"
		)
		var max_hp := hero.max_hp
		world._on_hero_death(hero, killer.id)
		check.call(not hero.alive, "AI item hero dies from the match death hook")
		check.call(
			hero.items.slots == _slot_values(row.slots),
			"Death must destroy Holy Rapier and keep every other item"
		)
		check.call(hero.max_hp == max_hp, "Death must not recalculate hero max HP")
		check.call(
			int(row.max_hp) == int(row.max_hp_before), "Source death branch leaves max HP untouched"
		)
		check.call(killer.kills == 1, "Enemy hero last hit still credits one kill")
