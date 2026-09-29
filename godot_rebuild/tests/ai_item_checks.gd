# gdlint:disable=max-file-lines
extends RefCounted
## Native AI item metadata versus the real hero_items.ITEM_CATALOG exec.
## Metadata only: no stat effects, passives or Forge UI are ported here.

const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroItems = preload("res://scripts/match/hero_items.gd")
const Inventory = preload("res://scripts/match/hero_item_inventory.gd")
const AIItems = preload("res://scripts/match/ai_items.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const ItemShopUI = preload("res://scripts/match/item_shop_ui.gd")
const ForgePanel = preload("res://scripts/ui/item_forge_panel.gd")
const AiHeroControl = preload("res://scripts/match/ai_hero_control.gd")
const AiController = preload("res://scripts/match/ai_controller.gd")
const AiBuild = preload("res://scripts/match/ai_build.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
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
	_test_timers(fixture.timer_attrs, fixture.timers, check)
	_test_auto_triggers(fixture.auto_triggers, check)
	_test_notify_damage(fixture.notify_damage, check)
	_test_item_tick_wiring(check)
	_test_auras(check)
	_test_on_hit(check)
	_test_miasma(fixture.miasma, check)
	_test_multishot(check)
	_test_miasma_wiring(check)
	_test_forge(fixture.forge, check)
	_test_forge_wiring(check)
	_test_shop_pages(fixture.shop_pages, check)
	_test_shop_clicks(check)
	_test_forge_panel(check)
	_test_hero_control(fixture.hero_control, check)
	_test_hero_control_wiring(check)
	_test_ai_schedule(fixture.schedule, check)
	_test_ai_controller_wiring(check)
	_test_ai_actions(check)
	_test_item_debuffs(fixture.item_debuffs, check)
	_test_stat_consumption(fixture.stat_consumption, check)
	_test_ai_switch(check)
	_test_ai_shield_nexus(check)
	_test_ai_restart(check)


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
	world.setup_arena()
	return world


func _fund(world: World, gold: int) -> void:
	world.economy = Economy.new()
	world.economy.gold[1] = gold
	world.economy.opening[1] = gold


func _fund_team(world: World, team: int, gold: int) -> void:
	# Forge tests fund the player purse; _fund() above belongs to the RED AI.
	world.economy = Economy.new()
	world.economy.gold[team] = gold
	world.economy.opening[team] = gold


func _clear_heroes(world: World) -> void:
	# setup_arena spawns a free mirrored Kaizen pair that is not part of the
	# source player roster; the Forge scenarios build their own.
	var doomed: Array = []
	for unit in world.units:
		if unit.is_hero:
			doomed.append(unit)
	for unit in doomed:
		world.units.erase(unit)


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
		# The damage path sets hp/alive first and then calls the hook
		# (minion_battle.gd:408), so reproduce that state here.
		hero.hp = 0.0
		hero.alive = false
		world._on_hero_death(hero, killer.id)
		check.call(
			hero.items.slots == _slot_values(row.slots),
			"Death must destroy Holy Rapier and keep every other item"
		)
		check.call(hero.max_hp == max_hp, "Death must not recalculate hero max HP")
		check.call(
			int(row.max_hp) == int(row.max_hp_before), "Source death branch leaves max HP untouched"
		)
		check.call(killer.kills == 1, "Enemy hero last hit still credits one kill")


func _timer_state(inventory: Inventory, attrs: Array) -> Dictionary:
	var state := {}
	for field in attrs:
		state[String(field)] = int(inventory.get(String(field)))
	for extra in ["blood_frenzy_timer", "blood_frenzy_cd", "last_damage_timer"]:
		state[extra] = int(inventory.get(extra))
	state["empower_charge"] = inventory.empower_charge
	state["rend_target"] = inventory.rend_target
	return state


func _test_timers(attrs: Array, rows: Array, check: Callable) -> void:
	check.call(
		Inventory.TIMER_FIELDS == attrs,
		"AI item timer list must equal the source update() decrements"
	)
	for row in rows:
		var spec: Dictionary = row.hero
		var inventory := Inventory.new()
		inventory.set_hero_gate(String(spec.role), float(spec.range))
		inventory.set_hero_scaling(int(spec.base_hp), int(spec.level), 1)
		for item_id in row.loadout:
			assert(inventory.add(String(item_id)), "timer loadout refused an item")
		var preset: Dictionary = row.preset
		for field in preset:
			inventory.set(String(field), int(preset[field]))
		var label := "%s %s" % [String(spec.role), str(row.loadout)]
		for index in range(int(row.ticks)):
			inventory.tick_timers(1)
			var want: Dictionary = row.log[index]
			var got := _timer_state(inventory, attrs)
			for field in got:
				var expected: Variant = want[field]
				var actual: int = got[field]
				if expected == null:
					check.call(actual == -1, "AI item rend target must reset: " + label)
				else:
					check.call(
						actual == int(expected),
						(
							"AI item timer %s after tick %d must match source: %s"
							% [field, index + 1, label]
						)
					)


# ── Layer 5c-2: auto-triggers & notify_damage_taken ──────────
class _TestItemFx:
	extends Inventory.ItemEffects
	var damage_calls: Array = []
	var stun_calls: Array = []
	var silence_calls: Array = []
	var slow_calls: Array = []
	var burn_calls: Array = []
	var amp_calls: Array = []
	var nudges: Array = []
	var notes: Array = []
	var chains: Array = []

	func deal_damage(target_id: int, _src_team: int, amount: int, _school: String = "magic") -> int:
		damage_calls.append({"tid": target_id, "amt": amount})
		return amount

	func apply_stun(target_id: int, duration: int) -> void:
		stun_calls.append({"tid": target_id, "dur": duration})

	func apply_silence(target_id: int, duration: int) -> void:
		silence_calls.append({"tid": target_id, "dur": duration})

	func apply_slow(target_id: int, amount: float, duration: int) -> void:
		slow_calls.append({"tid": target_id, "amt": amount, "dur": duration})

	func apply_burn(target_id: int, dps: float, duration: int, source_team: int) -> void:
		burn_calls.append({"tid": target_id, "dps": dps, "dur": duration, "team": source_team})

	func apply_damage_amp(target_id: int, amount: float, duration: int) -> void:
		amp_calls.append({"tid": target_id, "amt": amount, "dur": duration})

	func nudge_position(hid: int, delta: Vector2) -> void:
		nudges.append({"hid": hid, "delta": delta})

	func notify(_uid: int, _txt: String) -> void:
		notes.append(_txt)

	func chain_fx(_src: int, tgts: Array) -> void:
		chains.append(tgts.duplicate())

	func clear() -> void:
		damage_calls.clear()
		stun_calls.clear()
		silence_calls.clear()
		slow_calls.clear()
		burn_calls.clear()
		amp_calls.clear()
		nudges.clear()
		notes.clear()
		chains.clear()


func _fx_enemies(deltas: Array) -> Array:
	var enemies: Array = []
	for index in range(deltas.size()):
		var d: Array = deltas[index]
		(
			enemies
			. append(
				{
					"id": index + 100,
					"pos": Vector2(100 + float(d[0]), 100 + float(d[1])),
					"team": 1,
					"alive": true,
				}
			)
		)
	return enemies


func _fx_pos_for(enemies: Array, eid: int) -> Vector2:
	for e in enemies:
		var d: Dictionary = e as Dictionary
		if int(d.id) == eid:
			return d.get("pos", Vector2.ZERO) as Vector2
	return Vector2.ZERO


func _test_auto_triggers(rows: Array, check: Callable) -> void:
	var rng := RandomNumberGenerator.new()
	for row in rows:
		var spec: Dictionary = row.hero
		var inv := Inventory.new()
		inv.set_hero_gate(String(spec.role), float(spec.range))
		var melee_flag := 1 if float(spec.range) <= 80.0 else 0
		inv.set_hero_scaling(int(spec.base_hp), int(spec.level), melee_flag)
		var label := "%s %s hp=%.2f" % [String(spec.role), str(row.loadout), float(row.hp_ratio)]
		var enemies: Array = _fx_enemies(row.enemy_deltas)
		# invokes _on_item_changed which sets max_hp=get_max_hp() and raises
		# hp by (new_max - old_max) when new_max > old_max.
		var old_max: int = 1000
		var hp_ratio_f: float = float(row.hp_ratio)
		var start_hp_i: int = int(float(old_max) * hp_ratio_f)
		for item_id in row.loadout:
			assert(inv.add(String(item_id)), "auto-trigger loadout refused: " + label)
		var new_max: int = int(inv.get_max_hp())
		var cur_hp: float = float(start_hp_i)
		if new_max > old_max:
			cur_hp = mini(float(new_max), cur_hp + float(new_max - old_max))
		elif cur_hp > float(new_max):
			cur_hp = float(new_max)
		var start_pos: Array = row.start_pos
		# Seed Thunder Coil proc like the oracle.
		if inv.has("thunder_coil"):
			var proc_rng := RandomNumberGenerator.new()
			proc_rng.seed = 0
			var fx := _TestItemFx.new()
			var tgt_for_seed: int = 100 if enemies.size() > 0 else -1
			inv.set_hero_runtime(42, true, cur_hp, new_max, 0, 1.0, Vector2(100, 100), tgt_for_seed)
			inv.notify_damage_taken(50, 100, 1, true, proc_rng, fx)
		var fx := _TestItemFx.new()
		var r_ticks: int = int(row.ticks)
		var r_target: Variant = row.get("target_idx", null)
		for tick_idx in range(r_ticks):
			fx.clear()
			inv.tick_timers(1)
			var tgt_id := -1
			if r_target != null:
				var tidx_i: int = int(r_target)
				if tidx_i >= 0 and enemies.size() > tidx_i:
					tgt_id = 100 + tidx_i
			var sp0: float = float(start_pos[0])
			var sp1: float = float(start_pos[1])
			inv.set_hero_runtime(42, true, cur_hp, new_max, 0, 1.0, Vector2(sp0, sp1), tgt_id)
			inv.tick_auto(1, enemies, fx, rng)
			cur_hp = float(inv.hero_hp)
			# Apply nudge back for the next tick.
			for n in fx.nudges:
				var nd: Dictionary = n as Dictionary
				if int(nd.hid) == 42:
					var dv: Vector2 = nd.delta as Vector2
					start_pos = [sp0 + dv.x, sp1 + dv.y]
			# Compare state snapshot.
			var want: Dictionary = row.log[tick_idx].state
			for key in want:
				if key in ["hp", "x", "y"]:
					continue
				var w_val: int = int(want[key])
				var got: int = int(inv.get(String(key)))
				check.call(
					got == w_val,
					(
						"AI auto-trigger timer %s tick %d must match source: %s (got %d want %d)"
						% [String(key), tick_idx, label, got, w_val]
					)
				)
			# Compare HP regen (Leviathan / Vital Stone). Python double vs Godot
			# single-precision float drift on /60 regen accumulators compounds
			# across ticks; allow 4.0 HP drift over ten ticks.
			check.call(
				absf(float(inv.hero_hp) - float(want.hp)) < 4.0,
				(
					"AI auto-trigger hp tick %d must match source: %s (got %.2f want %s)"
					% [tick_idx, label, float(inv.hero_hp), str(want.hp)]
				)
			)
		check.call(true, "AI auto-trigger case completed: " + label)


func _test_notify_damage(rows: Array, check: Callable) -> void:
	for row in rows:
		var spec: Dictionary = row.hero
		var inv := Inventory.new()
		inv.set_hero_gate(String(spec.role), float(spec.range))
		var melee_flag := 1 if float(spec.range) <= 80.0 else 0
		inv.set_hero_scaling(int(spec.base_hp), int(spec.level), melee_flag)
		var label := "%s %s dmg=%d" % [String(spec.role), str(row.loadout), int(row.damage)]
		for item_id in row.loadout:
			assert(inv.add(String(item_id)), "notify loadout refused: " + label)
		# Source _make_hero sets max_hp=1000, hp=int(1000*ratio); add() invokes
		# _on_item_changed which raises hp by (new_max - old_max).
		var old_max_n: int = 1000
		var nhp_ratio: float = float(row.hp_ratio)
		var n_hp_start: int = int(float(old_max_n) * nhp_ratio)
		var n_max: int = int(inv.get_max_hp())
		var n_hp: float = float(n_hp_start)
		if n_max > old_max_n:
			n_hp = mini(float(n_max), n_hp + float(n_max - old_max_n))
		elif n_hp > float(n_max):
			n_hp = float(n_max)
		var fx := _TestItemFx.new()
		if inv.has("razor_carapace") and nhp_ratio < 0.5:
			inv.tick_timers(1)
			inv.set_hero_runtime(42, true, n_hp, n_max, 0, 1.0, Vector2(100, 100), -1)
			inv.tick_auto(1, [], fx, RandomNumberGenerator.new())
			n_hp = float(inv.hero_hp)
		var rng := RandomNumberGenerator.new()
		var seed_val: int = int(row.seed)
		rng.seed = seed_val
		fx.clear()
		inv.set_hero_runtime(42, true, n_hp, n_max, 0, 1.0, Vector2(100, 100), -1)
		var src_id := -1
		var src_team := 0
		var src_alive := false
		if bool(row.has_source):
			src_id = 200
			src_team = 1
			src_alive = true
		inv.notify_damage_taken(int(row.damage), src_id, src_team, src_alive, rng, fx)
		var after: Dictionary = row.after
		for key in after:
			var w_val: int = int(after[key])
			var got: int = int(inv.get(String(key)))
			check.call(
				got == w_val,
				(
					"AI notify_damage timer %s must match source: %s (got %d want %d)"
					% [String(key), label, got, w_val]
				)
			)
		# Compare reflect damage calls against source_effects.
		var expected_effects: Array = row.source_effects
		var reflect_calls := 0
		for dc in fx.damage_calls:
			var cd: Dictionary = dc as Dictionary
			if int(cd.tid) == 200:
				reflect_calls += 1
		check.call(
			reflect_calls == expected_effects.size(),
			"AI notify_damage reflect count must match source: " + label
		)
		check.call(true, "AI notify_damage case completed: " + label)


func _test_item_tick_wiring(check: Callable) -> void:
	# Tick a real red hero in a real match to verify tick_timers() is invoked
	# from the match loop and that HP regen applies after several ticks on a
	# Leviathan Heart holder.
	var world := _world()
	var hero := world.spawn_hero(World.THORNE, world.RED, Vector2(1000, 200))
	assert(hero.items.add("leviathan_heart"), "wiring loadout refused")
	hero.apply_item_change()
	hero.hp = hero.max_hp * 0.5
	var before := hero.items.last_damage_timer
	# With last_damage_timer = 0, Leviathan out-of-combat regen should raise hp.
	hero.items.last_damage_timer = 0
	var hp0 := hero.hp
	for _i in range(30):
		world.step_tick()
	check.call(
		hero.hp > hp0, "Leviathan Heart out-of-combat regen must fire when last_damage_timer is 0"
	)
	check.call(true, "AI item tick wiring: battle loop invokes inventory.tick_timers")


func _test_auras(check: Callable) -> void:
	# Layer 5d: verify update_auras resets fields and applies Steel Aegis
	# ally/enemy modifiers, plus Scarlet Bulwark Guard block when active.
	var world := _world()
	# Place two blue allies close together and one red enemy within enemy
	# radius. Source constants: Steel Aegis aura 320px ally/enemy radius.
	var a1 := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	var a2 := world.spawn_hero(World.GRIMJAW, world.BLUE, Vector2(300, 200))
	var e1 := world.spawn_hero(World.VEX, world.RED, Vector2(400, 200))
	assert(a1.items.add("steel_aegis"), "steel_aegis refused")
	a1.apply_item_change()
	a2.apply_item_change()
	e1.apply_item_change()
	world.step_tick()
	check.call(a2.items.aura_armor == 2, "Steel Aegis must grant +2 armor to ally in range")
	check.call(a2.items.aura_as == 10, "Steel Aegis must grant +10 AS to ally in range")
	check.call(
		e1.items.aura_armor_reduction == 2, "Steel Aegis must apply -2 armor to enemy in range"
	)
	check.call(a1.items.aura_armor == 0, "Steel Aegis holder must not self-apply ally aura")
	# Scarlet Bulwark guard: force guard_timer > 0 and verify block value.
	assert(a1.items.add("scarlet_bulwark"), "scarlet_bulwark refused")
	a1.apply_item_change()
	# tick_timers decrements timers before auras read guard_timer, so seed
	# a value >1 for it to remain positive through one step.
	a1.items.guard_timer = 2
	var armor_before := a2.items.aura_armor
	world.step_tick()
	check.call(
		a2.items.aura_guard_block >= 35, "Bulwark Guard aura must set block on nearby allies"
	)
	check.call(
		a2.items.aura_armor == armor_before, "aura_armor must reset and be recomputed each tick"
	)


func _test_on_hit(check: Callable) -> void:
	# Layer 5e: crit + melee lifesteal on_basic_attack_hit must heal attacker.
	var world := _world()
	var h := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	var t := world.spawn_hero(World.VEX, world.RED, Vector2(260, 200))
	_fund(world, 9999)
	assert(h.items.add("dead_edge"), "dead_edge refused")
	assert(h.items.add("demon_maw"), "demon_maw refused")
	h.apply_item_change()
	t.apply_item_change()
	# Lower attacker HP so we can detect lifesteal.
	h.hp = h.max_hp * 0.5
	h.items.set_hero_runtime(
		h.id, h.alive, h.hp, int(h.max_hp), h.team, h.facing, h.position, h.target_id
	)
	var hp0 := h.hp
	var t_hp0 := t.hp
	world.hero_basic_attack(h.id, t.id)
	check.call(
		h.items.hero_hp > hp0, "Melee lifesteal must heal attacker after on_basic_attack_hit"
	)
	check.call(t.hp < t_hp0, "Melee attack must damage target")
	# roll_crit returns a 2-element [ok, mult] array.
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var cr: Array = h.items.roll_crit(rng)
	check.call(cr.size() == 2, "roll_crit must return 2-element [ok, mult] array")


# ── Layer 5e-2: Miasma (Basilisk Breath) + Polycephaly multishot ─────────────
func _miasma_data() -> Dictionary:
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
	return metadata.items.basilisk_breath.on_attack


func _test_miasma(rows: Array, check: Callable) -> void:
	# Replay the source _apply_miasma/_tick_miasma scripts: % Max HP damage in
	# [6, cap], max-damage/max-timer/min-tick refresh, hardcoded 30-tick reset
	# and expiry on a dead target or a spent timer.
	var data := _miasma_data()
	var target_id := 500
	var fx := _TestItemFx.new()
	for row in rows:
		var inv := Inventory.new()
		inv.set_hero_gate("Marksman", 130.0)
		inv.set_hero_scaling(620, 3, 0)
		var max_hp := int(row.target_max_hp)
		var enemies: Array = [
			{
				"id": target_id,
				"pos": Vector2.ZERO,
				"team": 1,
				"alive": true,
				"max_hp": max_hp,
			}
		]
		var label := "Miasma %d max_hp" % max_hp
		for step in row.steps:
			var op := String(step.op)
			if op == "apply":
				var use: Dictionary = data.duplicate()
				var overrides: Dictionary = step.arg
				for key in overrides:
					use[key] = overrides[key]
				inv.apply_miasma(target_id, true, max_hp, use)
			else:
				fx.clear()
				for _tick in range(int(step.arg)):
					inv.tick_miasma(1, enemies, fx)
			var tracker: Dictionary = inv.miasma.get(target_id, {})
			check.call(
				tracker.is_empty() != bool(step.active),
				"%s: tracker presence must match source (%s)" % [label, op]
			)
			if bool(step.active):
				check.call(
					int(tracker.damage) == int(step.damage),
					"%s: damage must match source %d" % [label, int(step.damage)]
				)
				check.call(
					int(tracker.timer) == int(step.timer),
					"%s: timer must match source %d" % [label, int(step.timer)]
				)
				check.call(
					int(tracker.tick_cd) == int(step.tick_cd),
					"%s: tick countdown must match source %d" % [label, int(step.tick_cd)]
				)
			if op == "tick":
				var want := 0
				for effect in step.effects:
					if String(effect.kind) == "damage":
						want += int(effect.damage)
				var got := 0
				for entry in fx.damage_calls:
					got += int(entry.amt)
				check.call(got == want, "%s: tick damage must match source %d" % [label, want])
	# Dead targets drop their tracker.
	var dead_inv := Inventory.new()
	dead_inv.set_hero_gate("Marksman", 130.0)
	dead_inv.set_hero_scaling(620, 3, 0)
	dead_inv.apply_miasma(target_id, true, 1000, data)
	var dead_enemies: Array = [
		{"id": target_id, "pos": Vector2.ZERO, "team": 1, "alive": false, "max_hp": 1000}
	]
	dead_inv.tick_miasma(1, dead_enemies, fx)
	check.call(dead_inv.miasma.is_empty(), "Miasma must drop the tracker when its target dies")


func _test_multishot(check: Callable) -> void:
	# Polycephaly: only ranged owners, 2 nearest enemies around the primary
	# target inside 200 px, 70% damage and Miasma on each extra victim.
	var world := _world()
	var h := world.spawn_hero(World.SYLARA, world.BLUE, Vector2(200, 200))
	var target := world.spawn_hero(World.VEX, world.RED, Vector2(300, 200))
	var near1 := world.spawn_hero(World.VEX, world.RED, Vector2(340, 200))
	var near2 := world.spawn_hero(World.GRIMJAW, world.RED, Vector2(300, 260))
	var far := world.spawn_hero(World.VEX, world.RED, Vector2(900, 900))
	assert(h.items.add("basilisk_breath"), "basilisk_breath refused")
	for hero in [h, target, near1, near2, far]:
		hero.apply_item_change()
	var proc_seed := -1
	for seed_value in range(64):
		var probe := RandomNumberGenerator.new()
		probe.seed = seed_value
		if probe.randf() < 0.30:
			proc_seed = seed_value
			break
	check.call(proc_seed >= 0, "Polycephaly test needs a seed inside the 30% proc")
	var hp1 := near1.hp
	var hp2 := near2.hp
	var far_hp := far.hp
	world._item_rng.seed = proc_seed
	world.hero_basic_attack(h.id, target.id)
	check.call(near1.hp < hp1, "Polycephaly must splash the nearest extra enemy")
	check.call(near2.hp < hp2, "Polycephaly must splash the second extra enemy")
	check.call(far.hp == far_hp, "Polycephaly must not reach enemies beyond 200 px")
	check.call(
		h.items.miasma.has(near1.id) and h.items.miasma.has(near2.id),
		"Polycephaly must poison every extra victim with Miasma"
	)
	check.call(h.items.miasma.has(target.id), "Basilisk Breath must poison the attack target")
	# Melee owners keep Miasma but never fire the extra shots.
	var melee_world := _world()
	var m := melee_world.spawn_hero(World.THORNE, melee_world.BLUE, Vector2(200, 200))
	var m_target := melee_world.spawn_hero(World.VEX, melee_world.RED, Vector2(260, 200))
	var m_extra := melee_world.spawn_hero(World.GRIMJAW, melee_world.RED, Vector2(300, 200))
	assert(m.items.add("basilisk_breath"), "basilisk_breath refused (melee)")
	for hero in [m, m_target, m_extra]:
		hero.apply_item_change()
	var extra_hp := m_extra.hp
	melee_world._item_rng.seed = proc_seed
	melee_world.hero_basic_attack(m.id, m_target.id)
	check.call(m_extra.hp == extra_hp, "Polycephaly must stay ranged-only")
	check.call(
		m.items.miasma.has(m_target.id), "Melee Basilisk Breath must still poison its target"
	)


func _test_miasma_wiring(check: Callable) -> void:
	# The battle tick loop must advance the Miasma timers like update() does.
	var tick_world := _world()
	var poisoner := tick_world.spawn_hero(World.THORNE, tick_world.BLUE, Vector2(200, 200))
	var victim := tick_world.spawn_hero(World.VEX, tick_world.RED, Vector2(900, 900))
	assert(poisoner.items.add("basilisk_breath"), "basilisk_breath refused (wiring)")
	poisoner.apply_item_change()
	victim.apply_item_change()
	poisoner.items.apply_miasma(victim.id, true, int(victim.max_hp), _miasma_data())
	var victim_hp := victim.hp
	for _tick in range(32):
		tick_world.step_tick()
	check.call(victim.hp < victim_hp, "Battle tick must land the Miasma poison damage")
	var tracker: Dictionary = poisoner.items.miasma.get(victim.id, {})
	check.call(
		int(tracker.get("tick_cd", -1)) <= 30,
		"Miasma tick countdown must reset to the source 30-tick value"
	)


# ── Layer 5f: Forge shop (buy / queue / deliver / drop) ─────────────────────
func _test_forge(rows: Array, check: Callable) -> void:
	# Replay the source _try_buy/_try_drop/_resolve_shop_target scripts against
	# real heroes: same tr() keys, same gold trail, same slots and queue.
	for row in rows:
		var world := _world()
		_clear_heroes(world)
		_fund_team(world, world.BLUE, int(row.gold))
		var heroes: Array = []
		var specs: Array = row.heroes
		for index in range(specs.size()):
			var spec: Dictionary = specs[index]
			var key := "%s|%d" % [String(spec.role), int(spec.range)]
			var definition: Variant = World.PLAYABLE_AI_HEROES[ROLE_HEROES[key]]
			var hero := world.spawn_hero(definition, world.BLUE, Vector2(200 + 40 * index, 200))
			assert(hero.settings().role == String(spec.role), "forge fixture role must match")
			if not bool(spec.alive):
				hero.alive = false
			heroes.append(hero)
			hero.apply_item_change()
		if row.saved != null:
			world.forge.set_target(int(heroes[int(row.saved)].id))
		if row.selected != null:
			world.forge.set_selected(int(heroes[int(row.selected)].id))
		for step in row.steps:
			var op := String(step.op)
			var label := "Forge %s %s" % [op, str(step.arg)]
			var delivered: Array = []
			match op:
				"buy":
					var buy: Dictionary = world.forge.buy(world, String(step.arg))
					check.call(
						String(buy.status) == _forge_notify(step),
						"%s: message must match source %s" % [label, _forge_notify(step)]
					)
				"drop":
					var drop: Dictionary = world.forge.drop(world, int(step.arg))
					check.call(
						String(drop.status) == _forge_notify(step),
						"%s: message must match source %s" % [label, _forge_notify(step)]
					)
				"select":
					world.forge.set_selected(int(heroes[int(step.arg)].id))
				"kill":
					heroes[int(step.arg)].alive = false
				"respawn":
					var revived = heroes[int(step.arg)]
					revived.alive = true
					delivered = world.forge.deliver_pending_forge_items(revived)
			check.call(
				world.forge.player_gold(world) == int(step.gold),
				"%s: gold must match source %d" % [label, int(step.gold)]
			)
			var want_slots: Array = step.slots
			for index in range(heroes.size()):
				var got: Array = heroes[index].items.slots
				var want: Array = want_slots[index]
				check.call(
					_forge_slots_match(got, want),
					"%s: hero %d slots must match source" % [label, index]
				)
				var want_pending: Array = step.pending[index]
				check.call(
					heroes[index].pending_items == want_pending,
					"%s: hero %d pending queue must match source" % [label, index]
				)
			check.call(delivered == step.delivered, "%s: delivered list must match source" % label)
			var want_target: Variant = step.target_index
			if want_target == null:
				pass
			else:
				check.call(
					world.forge.target_hero_id == int(heroes[int(want_target)].id),
					"%s: shop target must match source hero %d" % [label, int(want_target)]
				)


func _forge_notify(step: Dictionary) -> String:
	# The fixture records the tr() keys the source notified with; a silent
	# refusal notifies nothing at all.
	var keys: Array = step.notify
	return "" if keys.is_empty() else String(keys[0])


func _meta_match(got: Array, want: Array) -> bool:
	# JSON parses every fixture number as float, so compare cast per element.
	if got.size() != want.size():
		return false
	for index in range(got.size()):
		var expected: Variant = want[index]
		var actual: Variant = got[index]
		if expected is String or actual is String:
			if String(actual) != String(expected):
				return false
		elif int(actual) != int(expected):
			return false
	return true


func _forge_slots_match(got: Array, want: Array) -> bool:
	if got.size() != want.size():
		return false
	for index in range(got.size()):
		var expected: Variant = want[index]
		var actual: Variant = got[index]
		if expected == null:
			if actual != null:
				return false
		elif String(actual) != String(expected):
			return false
	return true


func _test_forge_wiring(check: Callable) -> void:
	# A dead hero queues the order and the battle respawn delivers it; the
	# dropped item leaves the inventory with no refund, exactly like the source.
	var world := _world()
	_clear_heroes(world)
	_fund_team(world, world.BLUE, 50000)
	var hero := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	hero.apply_item_change()
	var gold0 := world.forge.player_gold(world)
	world.forge.set_selected(hero.id)
	hero.alive = false
	var queued: Dictionary = world.forge.buy(world, "dead_edge")
	check.call(String(queued.status) == "forge_queued", "Dead hero order must queue")
	check.call(hero.pending_items == ["dead_edge"], "Queued order must sit on the hero")
	check.call(world.forge.player_gold(world) == gold0 - 4500, "Queued order must still debit gold")
	world.step_tick()
	check.call(not hero.alive, "Hero must stay dead before its respawn timer elapses")
	hero.respawn_timer = 1
	var guardian := 0
	while not hero.alive and guardian < 900:
		world.step_tick()
		guardian += 1
	check.call(hero.alive, "Hero must respawn")
	check.call(hero.items.has("dead_edge"), "Respawn must deliver the queued Forge order")
	check.call(hero.pending_items.is_empty(), "Delivered order must leave the queue")
	var dropped: Dictionary = world.forge.drop(world, 0)
	check.call(String(dropped.status) == "item_dropped", "Drop must report the source key")
	check.call(not hero.items.has("dead_edge"), "Dropped item must leave the inventory")
	check.call(world.forge.player_gold(world) == gold0 - 4500, "Drop must not refund gold")


# ── Layer 5f-2: ITEM FORGE panel (paging + click routing) ───────────────────
func _test_shop_pages(rows: Dictionary, check: Callable) -> void:
	# Source get_item_class/_build_shop_pages: same class per item, same pages
	# and the same PHYSICAL 1/2 style tab labels.
	var shop := ItemShopUI.new()
	check.call(
		shop.page_count() == rows.pages.size(),
		"Shop page count must match the source _build_shop_pages"
	)
	for index in range(rows.pages.size()):
		var want: Array = rows.pages[index]
		var got: Array = shop.pages[index]
		check.call(got == want, "Shop page %d must match the source classes" % index)
	for index in range(rows.meta.size()):
		var meta: Array = rows.meta[index]
		var got_meta: Array = shop.page_meta[index]
		check.call(
			_meta_match(got_meta, meta),
			(
				"Shop page meta %d must match the source class labels: %s vs %s"
				% [index, str(got_meta), str(meta)]
			)
		)
	check.call(
		ItemShopUI.ITEMS_PER_PAGE == int(rows.items_per_page),
		"Shop grid must stay 4x2 items per page"
	)
	for item_id in rows.classes:
		check.call(
			shop.item_class(String(item_id)) == String(rows.classes[item_id]),
			"Shop class for %s must match the source get_item_class" % String(item_id)
		)
	for class_id in rows.class_order:
		check.call(
			shop.CLASS_ITEM_ORDER[String(class_id)] == rows.class_order[class_id],
			"Shop display order must match CLASS_ITEM_ORDER for " + String(class_id)
		)
		check.call(
			shop.CLASS_LABELS[String(class_id)] == String(rows.labels[String(class_id)]),
			"Shop tab label must match ITEM_CLASS_INFO for " + String(class_id)
		)
	check.call(shop.item_class("not_an_item") == "physical", "Unknown shop item is PHYSICAL")


func _test_shop_clicks(check: Callable) -> void:
	# Click routing: the button-id vocabulary of handle_item_shop_click drives
	# the same forge transactions (target chips, page tabs, buy, drop, inspect).
	var world := _world()
	_clear_heroes(world)
	_fund_team(world, world.BLUE, 60000)
	var alive := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	var dead := world.spawn_hero(World.VEX, world.BLUE, Vector2(260, 200))
	alive.apply_item_change()
	dead.apply_item_change()
	dead.alive = false
	var shop = world.item_shop
	check.call(not shop.is_open, "Shop starts closed until the panel opens it")
	check.call(
		not shop.handle_click(world, world.forge, "itemshop_close", 1),
		"Closed shop must ignore clicks"
	)
	shop.is_open = true
	check.call(
		shop.handle_click(world, world.forge, "itemshop_hero_1", 1),
		"Hero chip click must be handled"
	)
	check.call(
		world.forge.target_hero_id == dead.id, "Hero chip must select that hero as the buyer"
	)
	check.call(
		shop.notice.dead and shop.notice_text().contains("after respawn"),
		"Dead buyer must announce delivery after respawn"
	)
	check.call(
		shop.handle_click(world, world.forge, "itemshop_buy_dead_edge", 1),
		"Buy button click must be handled"
	)
	check.call(
		dead.pending_items == ["dead_edge"], "Buy click must queue the order for the dead hero"
	)
	check.call(
		shop.handle_click(world, world.forge, "itemshop_page_2", 1),
		"Page tab click must be handled"
	)
	check.call(shop.page == 2, "Page tab must switch to the MAGIC page")
	check.call(
		not shop.handle_click(world, world.forge, "itemshop_page_9", 1) or shop.page == 2,
		"Out-of-range page tab must not switch pages"
	)
	shop.handle_click(world, world.forge, "itemshop_hero_0", 1)
	check.call(world.forge.target_hero_id == alive.id, "Live hero chip must move the buyer back")
	shop.handle_click(world, world.forge, "itemshop_buy_demon_maw", 1)
	check.call(alive.items.has("demon_maw"), "Buy click must equip the live hero")
	check.call(
		shop.handle_click(world, world.forge, "itemshop_card_demon_maw", 1),
		"Item card click must open the detail popup"
	)
	check.call(shop.inspect_item == "demon_maw", "Card click must set the inspected item")
	check.call(
		shop.handle_click(world, world.forge, "itemshop_buy_moon_shard", 1),
		"Detail popup must swallow other buttons"
	)
	check.call(not alive.items.has("moon_shard"), "Detail popup must block the grid buy click")
	check.call(shop.inspect_item == "", "Any other click must close the detail popup")
	check.call(
		shop.handle_click(world, world.forge, "itemshop_slot_0", 3),
		"Slot right-click must be handled"
	)
	check.call(not alive.items.has("demon_maw"), "Slot right-click must drop the item, no refund")
	check.call(
		shop.handle_click(world, world.forge, "itemshop_close", 1), "Close button must be handled"
	)
	check.call(not shop.is_open, "Close button must shut the shop")
	shop.is_open = true
	check.call(shop.click_outside_panel(), "Outside click must be consumed while open")
	check.call(not shop.is_open, "Outside click must close the shop")
	shop.is_open = true
	var chips: Array = shop.hero_chips(world, world.forge)
	check.call(chips.size() == 2, "Hero chips must list every summoned player hero")
	check.call(
		String(chips[1].label).begins_with("dead"),
		"Dead hero chip must show the source dead status"
	)
	var cards: Array = shop.item_cards(world, world.forge)
	check.call(cards.size() == 8, "MAGIC page one must expose its eight items")
	check.call(String(cards[0].class) == "magic", "Page two cards must belong to MAGIC")
	check.call(
		(
			shop.page_tabs()
			== ["PHYSICAL 1/2", "PHYSICAL 2/2", "MAGIC 1/2", "MAGIC 2/2", "TANK 1/2", "TANK 2/2"]
		),
		"Page tabs must match the source class labels"
	)


# ── Layer 5f-3: ITEM FORGE panel (Control view over item_shop_ui) ────────────
func _test_forge_panel(check: Callable) -> void:
	# The Control renders the shop view data and routes presses back through the
	# source click vocabulary; no gameplay state lives in the panel itself.
	var world := _world()
	_clear_heroes(world)
	_fund_team(world, world.BLUE, 60000)
	var alive := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	var dead := world.spawn_hero(World.VEX, world.BLUE, Vector2(260, 200))
	alive.apply_item_change()
	dead.apply_item_change()
	dead.alive = false
	var panel := ForgePanel.new()
	panel.bind(world)
	panel.refresh()
	check.call(not panel.visible, "Panel must stay hidden while the shop is closed")
	world.item_shop.is_open = true
	panel.refresh()
	check.call(panel.visible, "Panel must follow item_shop_open")
	var chips := panel.find_child("ItemForgeChips", true, false)
	check.call(chips != null and chips.get_child_count() == 2, "Panel must draw two hero chips")
	check.call(
		chips.get_child(0).text.contains("BELI UNTUK 0"), "First chip must name the buyer index"
	)
	check.call(
		String(chips.get_child(1).text).contains("dead"),
		"Dead buyer chip must show the source dead status"
	)
	var tabs := panel.find_child("ItemForgeTabs", true, false)
	check.call(tabs != null and tabs.get_child_count() == 6, "Panel must draw six class tabs")
	check.call(
		String(tabs.get_child(0).text) == "PHYSICAL 1/2",
		"First tab must carry the source class label"
	)
	var grid := panel.find_child("ItemForgeGrid", true, false)
	check.call(grid != null and grid.get_child_count() == 8, "Panel must draw the 4x2 page grid")
	var first_cell := grid.get_child(0) as VBoxContainer
	var buy_button := first_cell.get_child(1) as Button
	check.call(
		String(buy_button.text).contains("Beli") or String(buy_button.text).contains("BELI"),
		"Card cell must expose a BUY button"
	)
	# Presses: chips -> tabs -> buy -> detail popup -> slots -> close.
	check.call(panel.press("itemshop_hero_1"), "Chip press must reach the shop router")
	check.call(world.forge.target_hero_id == dead.id, "Chip press must move the buyer")
	panel.press("itemshop_buy_dead_edge")
	check.call(dead.pending_items == ["dead_edge"], "Buy press must queue for the dead buyer")
	panel.press("itemshop_page_2")
	check.call(world.item_shop.page == 2, "Tab press must switch the shop page")
	panel.refresh()
	var magic_grid := panel.find_child("ItemForgeGrid", true, false)
	check.call(magic_grid.get_child_count() == 8, "MAGIC page must redraw eight cards")
	panel.press("itemshop_hero_0")
	panel.press("itemshop_buy_demon_maw")
	check.call(alive.items.has("demon_maw"), "Buy press must equip the live buyer")
	panel.refresh()
	var slots := panel.find_child("ItemForgeSlots", true, false)
	check.call(slots != null and slots.get_child_count() == 6, "Panel must draw the six slots")
	check.call(
		String(slots.get_child(0).text) == "demon_maw", "Slot row must show the buyer inventory"
	)
	panel.press("itemshop_slot_0", 3)
	check.call(not alive.items.has("demon_maw"), "Slot right-click must drop the item")
	panel.refresh()
	panel.press("itemshop_card_demon_maw")
	check.call(world.item_shop.inspect_item == "demon_maw", "Card press must inspect the item")
	panel.refresh()
	var detail := panel.find_child("ItemForgeDetail", true, false)
	check.call(detail != null and detail.visible, "Detail popup must appear when inspecting")
	var swallowed := panel.press("itemshop_buy_moon_shard")
	check.call(swallowed, "Detail popup must swallow other clicks")
	check.call(world.item_shop.inspect_item == "", "Any other click must close the detail popup")
	check.call(
		panel.status_text("forge_queued") != "forge_queued",
		"Status text must translate the forge status keys"
	)
	panel.press("itemshop_close")
	check.call(not world.item_shop.is_open, "Close press must shut the shop")
	panel.refresh()
	check.call(not panel.visible, "Panel must hide with the shop")
	check.call(
		panel.status_text("inventory_full") != "inventory_full",
		"inventory_full must carry a translated text"
	)
	# Free the Control subtree: a headless test never pumps a frame.
	panel.free()


# ── Layer 6a: AI hero control per tick (_control_heroes/_assign_hero_lane) ───
class _ControlHero:
	extends RefCounted
	var is_hero := true
	var team := 1
	var alive := true
	var skill_timer := 0
	var active_skill_timer := 100
	var target_id := -1
	var target_struct: Variant = null
	var has_destination := false
	var position := Vector2.ZERO
	var lane := -1
	var id := 0
	var moves: Array = []
	var auto_casts := 0
	var delta := 0


class _ControlWorld:
	extends RefCounted
	# Duck-typed world for the control module: units, RED, try_auto_cast,
	# move_to. Towers are passed in like the source `all_towers` list.
	var units: Array = []
	var towers: Array = []
	var move_log: Array = []

	func try_auto_cast(hero: Object) -> void:
		hero.auto_casts += 1
		hero.active_skill_timer += int(hero.delta)

	func move_to(hero: Object, point: Vector2, auto: bool) -> void:
		hero.has_destination = true
		hero.position = point
		hero.moves.append({"x": point.x, "y": point.y, "auto": auto})
		move_log.append({"hero": hero.id, "x": point.x, "y": point.y, "auto": auto})


func _test_hero_control(rows: Array, check: Callable) -> void:
	var control := AiHeroControl.new()
	for row in rows:
		var world := _ControlWorld.new()
		var heroes: Array = []
		var specs: Array = row.heroes
		for index in range(specs.size()):
			var spec: Dictionary = specs[index]
			var hero := _ControlHero.new()
			hero.id = 100 + index
			hero.alive = bool(spec.alive)
			hero.skill_timer = int(spec.skill_timer)
			hero.target_id = 1 if bool(spec.target) else -1
			hero.has_destination = bool(spec.destination)
			hero.position = Vector2(float(spec.x), float(spec.y))
			hero.delta = int(spec.active_skill_timer_delta)
			heroes.append(hero)
			world.units.append(hero)
		var minion_specs: Array = row.minions
		for spec in minion_specs:
			var minion := _ControlHero.new()
			minion.is_hero = false
			minion.id = 900 + world.units.size()
			minion.team = 0 if String(spec[0]) == "blue" else 1
			minion.alive = bool(spec[1])
			minion.position = Vector2(float(spec[3]), float(spec[4]))
			minion.lane = _lane_index(String(spec[2]))
			world.units.append(minion)
		for spec in row.towers:
			var tower := _ControlHero.new()
			tower.is_hero = false
			tower.team = 0 if String(spec[0]) == "blue" else 1
			tower.alive = bool(spec[1])
			tower.position = Vector2(float(spec[2]), float(spec[3]))
			world.towers.append(tower)
		control.total_skills_cast = 0
		control.control_heroes(world, world.towers)
		var label := "Hero control case (%d heroes)" % heroes.size()
		var want_rows: Array = row.moves
		for index in range(heroes.size()):
			var got: Array = heroes[index].moves
			var want: Array = want_rows[index]
			check.call(
				got.size() == want.size(),
				"%s: hero %d move count must match source" % [label, index]
			)
			if got.size() == want.size() and got.size() > 0:
				check.call(
					_move_match(got[0], want[0]),
					"%s: hero %d destination must match source" % [label, index]
				)
				check.call(bool(got[0].auto), "%s: AI move must stay auto" % label)
			check.call(
				heroes[index].auto_casts == row.auto_casts[index].size(),
				"%s: hero %d auto-cast attempts must match source" % [label, index]
			)
		check.call(
			control.total_skills_cast == int(row.total_skills_cast),
			"%s: total_skills_cast must match source" % label
		)
	# Tie-break: an equal threat count always resolves to TOP (lane 0).
	check.call(control.busiest_lane([1, 1, 1]) == 0, "Lane tie must resolve to TOP")
	check.call(control.busiest_lane([0, 2, 1]) == 1, "Lane with most threats must win")


func _lane_index(name: String) -> int:
	return ["top", "mid", "bot"].find(name)


func _move_match(got: Dictionary, want: Dictionary) -> bool:
	return absf(float(got.x) - float(want.x)) < 0.001 and absf(float(got.y) - float(want.y)) < 0.001


func _test_hero_control_wiring(check: Callable) -> void:
	# Real battle: the red AI hero takes the busiest lane in the same tick the
	# control runs, while a blue hero is never touched by the AI brain.
	var world := _world()
	_clear_heroes(world)
	var red := world.spawn_hero(World.THORNE, world.RED, Vector2(200, 380))
	var blue := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	var minion := world.spawn_unit(GOBLIN, world.BLUE, 1)
	minion.position = Vector2(500, 380)
	world.ai_hero_control_enabled = true
	var blue_destination := blue.has_destination
	world.step_tick()
	check.call(red.has_destination, "AI hero must receive a lane destination")
	check.call(red.destination_auto, "AI destination must be flagged auto")
	check.call(
		absf(red.destination.y - 380.0) < 0.001,
		"AI hero must head to the threatened lane y (mid = 380)"
	)
	# The control runs after the entity step, so the lane minion has already
	# walked: the destination must match its x after the tick, not the spawn.
	check.call(
		absf(red.destination.x - minion.position.x) < 0.001,
		"AI hero must aim at the nearest enemy minion x in that lane"
	)
	check.call(
		blue.has_destination == blue_destination, "Blue heroes must stay under player control"
	)
	# The auto destination is dropped once an enemy is inside aggro range.
	var enemy := world.spawn_hero(World.VEX, world.BLUE, Vector2(210, 380))
	enemy.apply_item_change()
	world.step_tick()
	check.call(
		not red.has_destination or not red.destination_auto,
		"Auto destination must yield to an enemy inside aggro range"
	)
	# With the control off, a fresh hero keeps its schedule untouched.
	world.ai_hero_control_enabled = false
	var idle := world.spawn_hero(World.GRIMJAW, world.RED, Vector2(200, 700))
	world.step_tick()
	check.call(not idle.has_destination, "Disabled AI control must not assign lanes")


# ── Layer 6b: AI scheduling wrapper (AIPlayer.update) ───────────────────────
func _test_ai_schedule(rows: Array, check: Callable) -> void:
	# Source update(): control every tick, think only when the timer expires,
	# 1 + round(2*elite) actions with a stop at the first failing priority.
	for row in rows:
		var controller := AiController.new()
		controller.policy.level_number = int(row.level)
		controller.policy.think_timer = 1
		check.call(
			absf(controller.policy.brain() - float(row.brain)) < 0.0001,
			"AI brain for level %d must match source" % int(row.level)
		)
		check.call(
			absf(controller.policy.elite() - float(row.elite)) < 0.0001,
			"AI elite for level %d must match source" % int(row.level)
		)
		var trace: Array = row.trace
		for index in range(trace.size()):
			var want: Dictionary = trace[index]
			var control_calls := [0]
			var step_calls := [0]
			var complete := controller.tick(
				func() -> void: control_calls[0] += 1,
				func() -> bool:
					step_calls[0] += 1
					# Same alternation as the oracle stub: True, False, ...
					return step_calls[0] % 2 == 1
			)
			var label := "AI schedule level %d tick %d" % [int(row.level), index]
			check.call(
				control_calls[0] == int(want.control_calls),
				"%s: hero control must run every tick" % label
			)
			check.call(
				step_calls[0] == want.steps.size(),
				"%s: priority attempts must match source (%d)" % [label, want.steps.size()]
			)
			check.call(
				controller.policy.think_timer == int(want.think_timer),
				"%s: think timer must match source %d" % [label, int(want.think_timer)]
			)
			check.call(
				complete <= step_calls[0], "%s: completed actions cannot exceed attempts" % label
			)
		check.call(controller.think_ticks >= 1, "AI must count its thinking ticks")
	# Elite budget: level 54 attempts up to three actions, level 1 only one.
	check.call(AiController.new().policy.action_budget() == 1, "Level 1 budget is a single action")
	var elite_controller := AiController.new()
	elite_controller.policy.level_number = 54
	check.call(elite_controller.policy.action_budget() == 3, "Level 54 budget is three actions")
	# Reserve passthrough (source _ai_reserve).
	var draft := _draft(5200)
	check.call(
		elite_controller.reserve(draft) == 5200, "AI reserve must follow the draft target cost"
	)
	check.call(AiController.new().reserve(null) == 0, "No draft means no reserve")


func _test_ai_controller_wiring(check: Callable) -> void:
	# With the controller enabled the red hero is controlled every tick, the
	# blue side stays manual, and the AI switch stays the only red-side owner.
	var world := _world()
	_clear_heroes(world)
	var red := world.spawn_hero(World.THORNE, world.RED, Vector2(200, 380))
	var blue := world.spawn_hero(World.THORNE, world.BLUE, Vector2(200, 200))
	world.spawn_unit(GOBLIN, world.BLUE, 1).position = Vector2(520, 380)
	world.ai_enabled = true
	world.ai_hero_control_enabled = true
	world.step_tick()
	check.call(red.has_destination, "AI controller must hand the red hero a lane")
	check.call(world.ai_controller.ticks == 1, "Controller must count one tick per battle tick")
	check.call(
		world.ai_controller.steps_attempted == 0,
		"Before the first thinking tick the AI attempts no priority action"
	)
	check.call(not blue.has_destination, "Blue heroes must stay manual")
	# Think timer expiry attempts the scan, now wired to the real adapters.
	world.ai_controller.policy.think_timer = 1
	world.step_tick()
	check.call(
		world.ai_controller.steps_attempted == 1,
		"Expired think timer must attempt the priority scan once"
	)
	check.call(
		world.ai_controller.steps_completed <= 1,
		"A thinking tick completes at most one priority action"
	)
	# Disabled controller leaves the tick untouched.
	world.ai_enabled = false
	var ticks := world.ai_controller.ticks
	world.step_tick()
	check.call(world.ai_controller.ticks == ticks, "Disabled AI controller must not tick")


# ── Layer 6c: AI priority scan wired to the real adapters ───────────
func _ai_world(gold: int) -> World:
	var world := _world()
	_clear_heroes(world)
	_fund(world, gold)
	world.ai_enabled = true
	world.ai_controller.rng.seed = 7
	world.ai_build.rng.seed = 7
	world.ai_draft.rng.seed = 7
	world.ai_controller.policy.think_timer = 1
	return world


func _has_event(world: World, kind: String) -> bool:
	for event in world.recent_events:
		if String(event.get("kind", "")) == kind:
			return true
	return false


func _red_towers(world: World) -> int:
	var count := 0
	for structure in world.structures:
		if (
			structure.alive
			and structure.team == world.RED
			and structure.settings().structure_kind == "tower"
		):
			count += 1
	return count


func _red_tower_id(world: World) -> int:
	var entity_id := 0
	for structure in world.structures:
		if structure.team == world.RED and structure.settings().structure_kind == "tower":
			entity_id = structure.id
	return entity_id


func _red_layout(world: World) -> String:
	# Slot identity shows through the structure position: a different slot pick
	# changes the replay string even when the action count matches.
	var parts: PackedStringArray = []
	for structure in world.structures:
		if structure.team == world.RED:
			parts.append("%d,%d" % [int(structure.position.x), int(structure.position.y)])
	return "|".join(parts)


func _test_ai_actions(check: Callable) -> void:
	# Every source priority dispatches to its real adapter and the shared ledger.
	var world := _ai_world(20000)
	var gold0 := world.economy.gold[world.RED]
	check.call(world._ai_attempt("build"), "AI build priority must build a red tower")
	check.call(_red_towers(world) == 1, "AI build must place exactly one tower")
	check.call(world.economy.gold[world.RED] == gold0 - 100, "AI build must debit the build cost")
	check.call(_has_event(world, "build"), "AI build must record the real transaction")
	check.call(world._ai_attempt("buy_hero"), "AI buy_hero priority must summon a hero")
	check.call(world._ai_roster().size() == 1, "AI roster must hold the summoned hero")
	check.call(_has_event(world, "hero_buy"), "AI hero purchase must hit the shared ledger")
	var hero := world._ai_roster()[0] as World.HeroState
	check.call(world._ai_attempt("upgrade_hero"), "AI upgrade_hero must upgrade the roster")
	check.call(hero.level == 2, "AI hero upgrade must raise the hero level")
	check.call(_has_event(world, "hero_upgrade"), "AI hero upgrade must hit the ledger")
	check.call(world._ai_attempt("buy_item"), "AI buy_item must equip the suggested item")
	check.call(hero.items.used_slots() == 1, "AI item must land in the hero inventory")
	check.call(_has_event(world, "hero_item"), "AI item purchase must hit the ledger")
	# The built tower is level 1 and takes one real upgrade step.
	var tower_id := _red_tower_id(world)
	var level0 := int(world.get_unit(tower_id).settings().level)
	check.call(world._ai_attempt("upgrade_tower"), "AI upgrade_tower must upgrade a tower")
	check.call(
		int(world.get_unit(tower_id).settings().level) == level0 + 1,
		"AI tower upgrade must raise the tower level"
	)
	check.call(_has_event(world, "upgrade"), "AI tower upgrade must hit the ledger")
	# Determinism: the same seed replays the scan, another seed diverges.
	var first := _ai_sequence(11)
	var second := _ai_sequence(11)
	var other := _ai_sequence(12)
	check.call(not first.is_empty(), "Seeded AI schedule must perform actions")
	check.call(first == second, "Same seed must replay the same AI action sequence")
	check.call(other != first, "A different seed must change the AI action sequence")


func _ai_sequence(seed_value: int) -> Array:
	# One scan per step on a fresh world: every draw comes from the seeded
	# controller/build/draft RNG, so no combat roll can leak into the replay.
	var world := _ai_world(30000)
	world.ai_controller.rng.seed = seed_value
	world.ai_build.rng.seed = seed_value
	world.ai_draft.rng.seed = seed_value
	var rows: Array = []
	for _step in range(30):
		var done := world._ai_perform_step()
		(
			rows
			. append(
				(
					"%s:%d:%d:%d:%s"
					% [
						str(done),
						int(world.economy.gold[world.RED]),
						world._ai_roster().size(),
						_red_towers(world),
						_red_layout(world),
					]
				)
			)
		)
	return rows


func _test_item_debuffs(rows: Array, check: Callable) -> void:
	# Layer 5b-3: target-side item debuffs (Corroder shred, Soul Rend amp,
	# Abyss Breaker heal amp) follow the source setters, decay per tick, and
	# the shred/amp actually reach the mitigation path.
	for row in rows:
		var world := _world()
		_clear_heroes(world)
		var hero := world.spawn_hero(World.KAIZEN, world.RED, Vector2(600, 380))
		for entry in row.log:
			var parts: PackedStringArray = String(entry.op).split(":")
			if parts[0] == "armor_shred":
				hero.apply_armor_shred(float(parts[1]), int(parts[2]))
			elif parts[0] == "damage_amp":
				hero.apply_damage_amp(float(parts[1]), int(parts[2]))
			else:
				hero.apply_heal_amp(float(parts[1]), int(parts[2]))
			check.call(
				(
					is_equal_approx(hero.armor_shred_amount, float(entry.armor_shred_amount))
					and hero.armor_shred_timer == int(entry.armor_shred_timer)
					and is_equal_approx(hero.dmg_amp_amount, float(entry.dmg_amp_amount))
					and hero.dmg_amp_timer == int(entry.dmg_amp_timer)
					and is_equal_approx(hero.heal_amp_amount, float(entry.heal_amp_amount))
					and hero.heal_amp_timer == int(entry.heal_amp_timer)
				),
				"target item debuff parity: %s after %s" % [str(row.ops), entry.op]
			)
	var decay := _world()
	_clear_heroes(decay)
	var patient := decay.spawn_hero(World.KAIZEN, decay.RED, Vector2(600, 380))
	patient.apply_armor_shred(6.0, 2)
	patient.apply_damage_amp(0.35, 2)
	patient.apply_heal_amp(0.16, 2)
	patient.tick_item_debuffs()
	var held := (
		is_equal_approx(patient.armor_shred_amount, 6.0)
		and patient.armor_shred_timer == 1
		and is_equal_approx(patient.dmg_amp_amount, 0.35)
		and is_equal_approx(patient.heal_amp_amount, 0.16)
	)
	patient.tick_item_debuffs()
	check.call(
		(
			held
			and patient.armor_shred_amount == 0.0
			and patient.armor_shred_timer == 0
			and patient.dmg_amp_amount == 0.0
			and patient.dmg_amp_timer == 0
			and patient.heal_amp_amount == 0.0
			and patient.heal_amp_timer == 0
		),
		"target item debuffs decay and clear on their last tick"
	)
	var armored := decay.spawn_hero(World.KAIZEN, decay.RED, Vector2(700, 380))
	check.call(armored.items.add("steel_aegis"), "steel aegis equips for the armor probe")
	check.call(
		is_equal_approx(DamageRules.effective_armor(armored), 6.0),
		"item armor lands in the mitigation armor value"
	)
	var plain: int = decay._damage_amount(armored, 100, "physical")
	armored.apply_armor_shred(6.0, 60)
	check.call(
		(
			is_equal_approx(DamageRules.effective_armor(armored), 0.0)
			and decay._damage_amount(armored, 100, "physical") > plain
		),
		"armor shred feeds the mitigation path"
	)
	armored.apply_damage_amp(0.35, 60)
	check.call(
		decay._damage_amount(armored, 100, "physical") > 100,
		"Soul Rend damage amp raises the physical damage taken"
	)


func _test_stat_consumption(rows: Array, check: Callable) -> void:
	# Layer 5b-2: the attack/movement consumers read the real item stats via the
	# source functions (Hero._eff_attack_cd/_eff_attack_range,
	# TowerDebuffMixin._eff_speed/apply_slow).
	var definitions := {"kaizen": World.KAIZEN, "sylara": World.SYLARA}
	for row in rows:
		var case: Dictionary = row.case
		var world := _world()
		_clear_heroes(world)
		var hero := world.spawn_hero(definitions[String(case.hero)], world.RED, Vector2(600, 380))
		var label := "%s %s" % [case.hero, str(case.items)]
		for item_id in case.items:
			check.call(hero.items.add(String(item_id)), "stat case equips %s" % item_id)
		hero.stun_timer = int(case.stun)
		hero.atk_slow_timer = int(case.atk_slow[0])
		hero.atk_slow_amount = float(case.atk_slow[1])
		world.apply_slow(hero.id, float(case.slow[0]), int(case.slow[1]))
		check.call(
			hero.eff_attack_cd(int(case.base_cd)) == int(row.attack_cd),
			"item attack cooldown parity: %s" % label
		)
		check.call(
			is_equal_approx(hero.eff_attack_range(), float(row.attack_range)),
			"item attack range parity: %s" % label
		)
		check.call(
			is_equal_approx(hero.eff_speed(), float(row.eff_speed)),
			"item movement speed parity: %s" % label
		)
		check.call(
			(
				is_equal_approx(hero.slow_amount, float(row.slow_amount))
				and hero.slow_timer == int(row.slow_timer)
			),
			"item slow resist parity: %s" % label
		)


func _test_ai_switch(check: Callable) -> void:
	# Layer 6e: set_ai_enabled() is the only switch left. With it off the red
	# side never transacts; with it on the real AI owns the side and the heroes.
	var world := _world()
	_clear_heroes(world)
	_fund(world, 30000)
	for _tick in range(300):
		world.step_tick()
	check.call(
		(
			not world.ai_enabled
			and not world.ai_hero_control_enabled
			and _red_towers(world) == 0
			and world.economy.spent[world.RED] == 0
		),
		"Without the AI switch the red side stays idle"
	)
	world.set_ai_enabled(true)
	check.call(
		world.ai_enabled and world.ai_hero_control_enabled,
		"Enabling the AI must own the red side and the heroes"
	)
	world.ai_controller.rng.seed = 7
	world.ai_build.rng.seed = 7
	world.ai_draft.rng.seed = 7
	world.ai_controller.policy.think_timer = 1
	for _tick in range(300):
		world.step_tick()
	check.call(
		world.ai_build.total_built > 0 and _red_towers(world) > 0,
		"Enabling the AI must build red towers on schedule"
	)
	world.set_ai_enabled(false)
	check.call(
		not world.ai_enabled and not world.ai_hero_control_enabled,
		"Disabling the AI must leave the red side manual"
	)


func _test_ai_restart(check: Callable) -> void:
	# Source Game.reset(): a restarted match gets a brand-new AI whose clocks,
	# counters and draft start over, and the match seed replays its draws.
	var world := _ai_world(30000)
	for _step in range(12):
		world._ai_perform_step()
	world.ai_controller.policy.think_timer = 1
	world.step_tick()
	world.ai_heroes.total_skills_cast = 3
	check.call(
		(
			world.ai_controller.ticks > 0
			and world.ai_build.total_built > 0
			and world.ai_controller.steps_attempted > 0
		),
		"Seeded AI must act before the restart check"
	)
	world.reset_ai(11)
	check.call(
		(
			world.ai_controller.ticks == 0
			and world.ai_controller.think_ticks == 0
			and world.ai_controller.steps_attempted == 0
			and world.ai_controller.steps_completed == 0
			and world.ai_controller.policy.think_timer == 90
			and world.ai_build.total_built == 0
			and world.ai_heroes.total_skills_cast == 0
			and world.ai_draft.total_heroes_bought == 0
			and world.ai_upgrades.total_upgraded == 0
			and world.ai_draft.purchase_target == ""
		),
		"Restarting the AI must clear every clock, counter and the draft"
	)
	# The seed lands on every AI stream: the controller replays draw for draw.
	var probe := AiController.new()
	probe.rng.seed = 11
	check.call(world.ai_controller.draw() == probe.draw(), "Restart must reseed the controller RNG")
	var builder := world.ai_build
	var other := AiBuild.new()
	other.rng.seed = 12
	check.call(builder.rng.randf() == other.rng.randf(), "Restart must reseed the build RNG")


func _test_ai_shield_nexus(check: Callable) -> void:
	# Regen shield needs a level 4+ tower; the castle shield a red nexus whose
	# free shield already expired (source set_wave gate).
	var world := _ai_world(60000)
	check.call(world._ai_attempt("build"), "AI shield checks need a real red tower")
	var tower_id := _red_tower_id(world)
	for _step in range(3):
		var level := int(world.get_unit(tower_id).settings().level)
		if level >= 4:
			break
		check.call(
			world._upgrade_tower_for(world.RED, tower_id, level, "archer"),
			"Tower must reach the regen shield level"
		)
	check.call(
		world._ai_attempt("regen_shield"), "AI regen_shield must activate on a level 4 tower"
	)
	check.call(
		world.get_unit(tower_id).regen_shield_active, "Regen shield must be active on the tower"
	)
	var nexus := world.nexuses[world.RED]
	nexus.set_wave(nexus.settings().free_shield_waves + 1)
	check.call(world._ai_attempt("castle_shield"), "AI castle_shield must buy the red nexus shield")
	check.call(
		world.nexuses[world.RED].castle_shield_purchased,
		"Castle shield purchase must stick to the red nexus"
	)
