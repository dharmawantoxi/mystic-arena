extends RefCounted

## Python-oracle parity for hero_items.py: catalog/shop helpers, inventory
## getters, deterministic triggers, auras, on-hit effects and AI suggestions.

const STATE_MAP := {
	"blood_frenzy_timer": "blood_frenzy",
	"blood_frenzy_cd": "blood_frenzy_cd",
	"last_damage_timer": "last_damage",
	"guard_timer": "guard",
	"guard_cd": "guard_cd",
	"veil_timer": "veil",
	"veil_cd": "veil_cd",
	"chains_cd": "chains_cd",
	"rend_timer": "rend",
	"rend_cd": "rend_cd",
	"bash_cd": "bash_cd",
	"overwhelm_cd": "overwhelm_cd",
	"static_timer": "static",
	"static_cd": "static_cd",
	"static_tick": "static_tick",
	"thorn_timer": "thorn",
	"thorn_cd": "thorn_cd",
	"arctic_cd": "arctic_cd",
	"gale_timer": "gale",
	"gale_cd": "gale_cd",
	"pierce_bash_cd": "pierce_bash_cd",
	"searbrand_cd": "searbrand_cd",
	"arcane_cd": "arcane_cd",
	"fulgur_cd": "fulgur_cd",
	"hex_cd": "hex_cd",
	"rift_cd": "rift_cd",
	"pact_cd": "pact_cd",
	"vine_cd": "vine_cd",
	"ghost_timer": "ghost",
	"ghost_cd": "ghost_cd",
	"empower_charge": "empower_charge"
}


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/hero_items_parity.json", FileAccess.READ)
	runner.check(file != null, "items Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var data := CoreData.new()
	var items := data.items
	runner.check(items.valid(), "native hero items contract loads")
	runner.check(items.catalog.size() == 33, "items contract has 33 items")
	runner.check(items.page_count() == 6, "items contract has six class-aligned shop pages")
	runner.check(items.item_shop_order.size() == 33, "items shop order covers catalog")
	_roles(runner, items, oracle.role_cases)
	_classes(runner, items, oracle.class_cases)
	_mechanics(runner, items, oracle.mechanics)
	_getters(runner, items, oracle.getter_cases)
	_triggers(runner, items, oracle.trigger_cases)
	_auras(runner, data, oracle.aura_case)
	_on_hit(runner, items, oracle.on_hit_cases)
	_suggest(runner, items, oracle.suggest_cases)
	_shop_rules(runner, data)
	_runtime_modifiers(runner)
	var missing_path := "user://missing_items_%d.json" % Time.get_ticks_usec()
	var missing := HeroItems.new(missing_path)
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing items contract fails closed"
	)
	var invalid_core := CoreData.new(
		"res://data/core_data.json",
		HeroArchetypes.DEFAULT_PATH,
		HeroBalance.DEFAULT_PATH,
		missing_path
	)
	runner.check(not invalid_core.valid(), "CoreData rejects missing items contract")


static func _roles(runner, items: HeroItems, cases: Array) -> void:
	for row: Dictionary in cases:
		runner.check(
			items.is_magic_role(str(row.role)) == bool(row.magic),
			"items magic role: " + str(row.role)
		)


static func _classes(runner, items: HeroItems, cases: Dictionary) -> void:
	for item_id: String in cases:
		runner.check(items.item_class(item_id) == str(cases[item_id]), "items class: " + item_id)


static func _mechanics(runner, items: HeroItems, mechanics: Dictionary) -> void:
	for lang: String in mechanics:
		for item_id: String in mechanics[lang]:
			var actual := items.mechanics(item_id, lang)
			var expected: Array = mechanics[lang][item_id]
			var ok := actual.size() == expected.size()
			if ok:
				for index in range(actual.size()):
					var row: Dictionary = actual[index]
					var want: Array = expected[index]
					if str(row.kind) != str(want[0]) or str(row.text) != str(want[1]):
						ok = false
						break
			runner.check(ok, "items mechanics %s: %s" % [lang, item_id])


static func _make_hero(catalog: Dictionary, role: String, attack_range: float) -> BattleUnit:
	var hero := BattleUnit.new()
	hero.kind = BattleUnit.Kind.HERO
	hero.stats = {"role": role}
	hero.attack_range = attack_range
	hero.is_melee_hero = attack_range <= 80.0
	hero.base_hp = 1000
	hero.max_hp = 1000
	hero.hp = 1000
	hero.level = 1
	hero.team = "blue"
	hero.alive = true
	var inv := UnitInventory.new(catalog)
	inv.hero = hero
	hero.items = inv
	return hero


static func _getters(runner, items: HeroItems, cases: Array) -> void:
	var catalog := items.catalog.duplicate(true)
	catalog["fenrir_chain"]["on_attack"]["chance"] = 1.0
	catalog["abyss_breaker"]["bash"]["chance"] = 1.0
	for row: Dictionary in cases:
		var hero := _make_hero(catalog, str(row.role), float(row["range"]))
		var inv := hero.items
		for item_id: String in row["items"]:
			inv.add(item_id, hero.attack_range, hero.is_magic_hero())
		match str(row.name):
			"demon_maw":
				inv.set_timer("blood_frenzy", 120)
			"spectral":
				inv.set_timer("ghost", 90)
			"gale":
				inv.set_timer("gale", 90)
			"razor":
				inv.set_timer("thorn", 90)
			"runic":
				inv.set_timer("empower_charge", 0)
			"block_melee":
				inv.aura_guard_block = 40
		inv.aura_armor = 3
		inv.aura_attack_speed = 10
		inv.aura_armor_reduction = 1
		var actual := _getter_snapshot(inv)
		var expected: Dictionary = row.getters
		var ok := true
		for key: String in expected:
			if not _value_equal(actual.get(key), expected[key]):
				ok = false
				break
		runner.check(ok, "items getters: " + str(row.name))
		_release(hero)


static func _getter_snapshot(inv: UnitInventory) -> Dictionary:
	var cleave := inv.cleave()
	var block := inv.block_profile()
	var shred := inv.armor_shred()
	var chain := inv.on_attack_chain()
	var bash := inv.bash()
	return {
		"bonus_damage": inv.bonus_damage(),
		"bonus_hp": inv.bonus_hp(),
		"hp_pct": inv.hp_pct(),
		"armor": inv.armor(),
		"hp_regen": inv.hp_regen(),
		"max_hp": inv.max_hp(inv.hero.base_hp),
		"attack_speed_mult": inv.attack_speed_mult(),
		"lifesteal": inv.lifesteal(),
		"crit": inv.crit(),
		"cleave": null if cleave.is_empty() else cleave,
		"cooldown_reduction": inv.cooldown_reduction(),
		"spell_vamp": inv.spell_vamp(),
		"skill_amp": inv.skill_amp(),
		"evasion": inv.evasion(),
		"move_speed_pct": inv.move_speed_pct(),
		"heal_amp": inv.heal_amp(),
		"slow_resist": inv.slow_resist(),
		"range_bonus": inv.range_bonus(),
		"true_strike": inv.has_true_strike(),
		"reflect_pct": inv.reflect_pct(),
		"gale_as_bonus": inv.gale_as_bonus(),
		"block": null if block.is_empty() else block,
		"armor_shred": null if shred.is_empty() else shred,
		"on_attack_chain": null if chain.is_empty() else chain,
		"bash": null if bash.is_empty() else bash,
		"veiled": inv.is_veiled(),
		"guarding": inv.is_guarding(),
		"rend_crit": inv.rend_crit(),
	}


static func _triggers(runner, items: HeroItems, cases: Array) -> void:
	for row: Dictionary in cases:
		var sid := str(row.item)
		var catalog := items.catalog
		var magic := bool(catalog.get(sid, {}).get("magic_only", false))
		var hero := _make_hero(catalog, "Mage" if magic else "Fighter", 150.0 if magic else 70.0)
		hero.items.add(sid, hero.attack_range, magic)
		hero.hp = 200
		hero.max_hp = 1000
		var target := _make_target(Vector2(120, 0))
		var enemy := _make_target(Vector2(160, 0))
		hero.target = target
		if sid == "thunder_coil":
			hero.items.set_timer("static", 60)
			hero.items.set_timer("static_tick", 1)
		if sid == "runic_gavel":
			hero.items.set_timer("empower_charge", 5)
		var model := MatchModel.new()
		EntityItems.update(hero, [target, enemy], model)
		var ok := _near(hero.hp, float(row.hero_hp), 1e-6)
		ok = (
			ok
			and _near(hero.pos.x, float(row.hero_x), 1e-6)
			and _near(hero.pos.y, float(row.hero_y), 1e-6)
		)
		for source_key: String in STATE_MAP:
			if not row.after.has(source_key):
				continue
			var want := float(row.after[source_key])
			var got := float(hero.items.timer(STATE_MAP[source_key]))
			if source_key == "aura_guard_block":
				got = hero.items.aura_guard_block
			if not _near(got, want, 1e-6):
				ok = false
		var expected_damage := 0.0
		for hit: Array in row.target_damage:
			expected_damage += float(hit[0])
		ok = ok and _near(800.0 - target.hp, expected_damage, 1.0)
		if not (row.target_stuns as Array).is_empty():
			ok = ok and target.status.stun_timer > 0
		if not (row.target_silences as Array).is_empty():
			ok = ok and target.status.silence_timer > 0
		runner.check(ok, "items trigger: " + sid)
		model.clear_unit_refs()
		_release(hero)


static func _release(hero: BattleUnit) -> void:
	if hero == null:
		return
	if hero.items != null:
		hero.items.hero = null
		hero.items = null
	hero.world = null
	hero.target = null
	hero.follow_target = null
	hero.tactical_target = null
	hero.killed_by = null


static func _make_target(pos: Vector2) -> BattleUnit:
	var unit := BattleUnit.new()
	unit.kind = BattleUnit.Kind.MINION
	unit.team = "red"
	unit.pos = pos
	unit.max_hp = 800
	unit.hp = 800
	unit.alive = true
	return unit


static func _auras(runner, data: CoreData, expected: Dictionary) -> void:
	var model := MatchModel.new()
	model.data = data
	var specs := [
		["Tank", "blue", 0.0, ["steel_aegis"]],
		["Tank", "blue", 40.0, ["scarlet_bulwark"]],
		["Mage", "blue", 80.0, ["everfrost_guard", "solar_brand", "searbrand"]],
		["Fighter", "red", 120.0, []],
	]
	var heroes: Array[BattleUnit] = []
	for index in range(specs.size()):
		var spec: Array = specs[index]
		var hero := _make_hero(data.items.catalog, str(spec[0]), 70.0)
		hero.team = str(spec[1])
		hero.pos = Vector2(float(spec[2]), 0)
		for sid: String in spec[3]:
			hero.items.add(sid, hero.attack_range, hero.is_magic_hero())
		if index == 1:
			hero.items.set_timer("guard", 100)
			hero.max_hp = 2000
		heroes.append(hero)
	model.heroes.assign([heroes[0], heroes[1], heroes[2]])
	model.enemy_heroes.assign([heroes[3]])
	var minion := _make_target(Vector2(140, 0))
	minion.max_hp = 300
	minion.hp = 300
	var boss := _make_target(Vector2(160, 0))
	boss.kind = BattleUnit.Kind.BOSS
	boss.max_hp = 5000
	boss.hp = 5000
	model.minions.assign([minion])
	model.active_boss = boss
	EntityItems.update_auras(model)
	var ok := true
	for index in range(heroes.size()):
		var want: Dictionary = expected.heroes[index]
		var inv := heroes[index].items
		if (
			not _near(inv.aura_armor, float(want.aura_armor))
			or not _near(inv.aura_attack_speed, float(want.aura_as))
		):
			ok = false
		if (
			not _near(inv.aura_armor_reduction, float(want.aura_armor_reduction))
			or not _near(inv.aura_guard_block, float(want.aura_guard_block))
		):
			ok = false
	runner.check(ok, "items aura hero fields")
	runner.check(
		minion.status.anti_heal_amount > 0.0 and minion.status.burn_dps > 0.0,
		"items aura minion debuffs"
	)
	runner.check(
		boss.status.anti_heal_amount > 0.0 and boss.status.burn_dps > 0.0, "items aura boss debuffs"
	)
	model.clear_unit_refs()
	for hero: BattleUnit in heroes:
		_release(hero)


static func _on_hit(runner, items: HeroItems, cases: Array) -> void:
	var catalog := items.catalog.duplicate(true)
	for sid: String in ["fenrir_chain", "thunder_coil", "corroder", "basilisk_breath"]:
		if catalog[sid].has("on_attack"):
			catalog[sid]["on_attack"]["chance"] = 1.0
	for sid: String in ["abyss_breaker", "sundering_cudgel"]:
		catalog[sid]["bash"]["chance"] = 1.0
	catalog["basilisk_breath"]["multishot"]["chance"] = 1.0
	catalog["thunder_coil"]["active"]["proc_chance"] = 1.0
	for row: Dictionary in cases:
		var sid := str(row.item)
		var magic := bool(catalog.get(sid, {}).get("magic_only", false))
		var ranged := sid in ["basilisk_breath", "frostbound_eye"]
		var hero := _make_hero(catalog, "Mage" if magic else "Fighter", 150.0 if ranged else 70.0)
		hero.items.add(sid, hero.attack_range, magic)
		if sid == "runic_gavel":
			hero.items.set_timer("empower_charge", 0)
		hero.max_hp = hero.items.max_hp(1000)
		hero.hp = hero.max_hp
		var target := _make_target(Vector2(100, 0))
		var extra := _make_target(Vector2(140, 0))
		var model := MatchModel.new()
		model.rng.seed = 7
		EntityItems.on_basic_attack_hit(hero, target, 100.0, [target, extra], model)
		var ok := _near(hero.hp, float(row.hero_hp), 1.0)
		var expected_damage := 0.0
		for hit: Array in row.target_damage:
			expected_damage += float(hit[0])
		ok = ok and _near(800.0 - target.hp, expected_damage, 1.0)
		var expected_extra := 0.0
		for hit: Array in row.extra_damage:
			expected_extra += float(hit[0])
		ok = ok and _near(800.0 - extra.hp, expected_extra, 1.0)
		if not (row.target_stuns as Array).is_empty():
			ok = ok and target.status.stun_timer > 0
		runner.check(ok, "items on-hit: " + sid)
		model.clear_unit_refs()
		_release(hero)


static func _suggest(runner, items: HeroItems, cases: Array) -> void:
	for row: Dictionary in cases:
		var hero := _make_hero(items.catalog, str(row.role), float(row["range"]))
		var index := 0
		for owned: String in row.owned:
			if index < UnitInventory.MAX_SLOTS:
				hero.items.slots[index] = owned
				index += 1
		var got := hero.items.suggest_for(hero)
		var want := str(row.suggestion) if row.suggestion != null else ""
		runner.check(got == want, "items suggest: %s/%s" % [row.role, row.owned])
		_release(hero)


static func _shop_rules(runner, data: CoreData) -> void:
	var model := MatchModel.new()
	model.data = data
	model.gold = 100000
	var hero := BattleUnit.new()
	hero.world = model
	hero.setup_hero(data, "thorne", "blue", Vector2.ZERO)
	model.heroes.assign([hero])
	model.selected_hero = hero
	var cost := int(data.item("dead_edge").get("cost", 0))
	var gold := model.gold
	runner.check(
		model.buy_item("dead_edge") and hero.items.has("dead_edge"), "shop buys physical item"
	)
	runner.check(model.gold == gold - cost, "shop charges exact item cost")
	runner.check(not model.buy_item("astral_codex"), "shop rejects magic-only item for non-mage")
	hero.attack_range = 150.0
	hero.is_melee_hero = false
	runner.check(not model.buy_item("cleave_axe"), "shop rejects melee-only item for ranged hero")
	hero.attack_range = 70.0
	hero.is_melee_hero = true
	hero.alive = false
	var pending_before := hero.items.pending.size()
	runner.check(model.buy_item("dead_edge"), "shop queues forge delivery for dead hero")
	runner.check(hero.items.pending.size() == pending_before + 1, "dead hero purchase is pending")
	hero.respawn(data)
	runner.check(hero.items.pending.is_empty(), "respawn delivers pending forge items")
	gold = model.gold
	runner.check(model.drop_item(hero, "dead_edge") and hero.items.used() == 1, "shop drops item")
	runner.check(model.gold == gold, "item drop gives no refund")
	hero.items.add("holy_rapier", hero.attack_range, hero.is_magic_hero())
	runner.check(
		hero.items.clear_on_death() and not hero.items.has("holy_rapier"),
		"death drops only Holy Rapier"
	)
	model.clear_unit_refs()


static func _runtime_modifiers(runner) -> void:
	var catalog := {
		"amp": {"stats": {"heal_amp": 0.5, "slow_resist": 0.6, "skill_amp": 0.5}},
		"sundering_cudgel": {"stats": {}},
	}
	var hero := BattleUnit.new()
	hero.kind = BattleUnit.Kind.HERO
	hero.alive = true
	hero.max_hp = 1000
	hero.hp = 100
	hero.skill_damage = 100
	hero.items = UnitInventory.new(catalog)
	hero.items.hero = hero
	hero.items.add("amp")
	hero.heal(100)
	runner.check(_near(hero.hp, 250.0), "item heal amp modifies healing")
	hero.apply_debuff("slow", 1.0, 60)
	runner.check(_near(hero.status.slow_amount, 0.4), "item slow resist reduces slow")
	runner.check(_near(hero.kit_skill_damage(), 150.0), "item skill amp modifies skill damage")
	hero.status.apply("silence", 1.0, 30)
	var enemies: Array[BattleUnit] = []
	runner.check(not hero.cast_skill("q", enemies), "silence blocks skill cast")
	var defender := BattleUnit.new()
	defender.items = UnitInventory.new(catalog)
	defender.items.hero = defender
	defender.items.aura_guard_block = 40
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var blocked := EntityCombat.hero_pre_damage(defender, 100.0, "physical", null, rng)
	runner.check(_near(float(blocked.amount), 60.0), "aura guard block reduces damage")
	defender.items.set_timer("veil", 30)
	var veiled := EntityCombat.hero_pre_damage(defender, 100.0, "physical", null, rng)
	runner.check(bool(veiled.miss), "item veil causes miss")
	var attacker := BattleUnit.new()
	attacker.items = UnitInventory.new(catalog)
	attacker.items.hero = attacker
	attacker.items.add("sundering_cudgel")
	defender.items.set_timer("veil", 0)
	defender.items.set_timer("ghost", 30)
	defender.items.slots[0] = "spectral_charm"
	defender.items.catalog["spectral_charm"] = {"stats": {}}
	var struck := EntityCombat.hero_pre_damage(defender, 100.0, "physical", attacker, rng)
	runner.check(not bool(struck.miss), "item true strike bypasses evasion")
	_release(hero)
	_release(defender)
	_release(attacker)


static func _value_equal(actual: Variant, expected: Variant) -> bool:
	if expected == null:
		return actual == null
	if expected is Array and actual is Array:
		if actual.size() != expected.size():
			return false
		for index in range(actual.size()):
			if not _value_equal(actual[index], expected[index]):
				return false
		return true
	if expected is Dictionary and actual is Dictionary:
		if actual.size() != expected.size():
			return false
		for key: String in expected:
			if not actual.has(key) or not _value_equal(actual[key], expected[key]):
				return false
		return true
	if expected is float or expected is int:
		return _near(float(actual), float(expected), 1e-6)
	return actual == expected


static func _near(a: float, b: float, tol := 1e-6) -> bool:
	return absf(a - b) <= tol
