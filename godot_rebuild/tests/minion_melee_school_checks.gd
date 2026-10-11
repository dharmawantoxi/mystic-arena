extends RefCounted
## 9x: the minion basic attack is school-free.
##
## `_entity.py::Minion.update` attacks with
## `self.target.take_damage(self.damage, self.team)` - two positional arguments,
## no `source=`, no school, no `damage_type` - so `resolve_damage_school`
## returns `None` for every victim: tower/nexus armour never cuts a minion
## melee hit, minion armour and `magic_resist` never cut it, the boss
## mitigation never cuts it, nothing is credited, the caster's blind is not
## consulted and `notify_damage_taken(source=None)` never reflects it back.
##
## The pre-9x native `apply_hit` handed `attacker.id` plus the declared
## `"physical"` school to `_deliver_hit`, so tower armour 3 cut an orc hit
## 13 -> 11, troll armour 2 cut it 13 -> 12, gornak's armour cut it, and a hero
## holding an armed Razor Carapace reflected 85% back to the minion. A **hero**
## attacker keeps the source `Hero` melee shape (`source=self` plus the declared
## school), so that branch is pinned as a control.

const Siege = preload("res://scripts/combat/siege_battle.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const ORC = preload("res://data/minions/orc.tres")
const TROLL = preload("res://data/minions/troll.tres")
const FIXTURE := "res://tests/fixtures/minion_melee_school_source.json"
const ARMOR_ITEM := "steel_aegis"
const REFLECT_ITEM := "razor_carapace"
const LIVE_BOSS := "gornak"
const POS := Vector2(600.0, 500.0)
const MELEE_GAP := 25.0


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the minion melee school fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the minion melee school fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_boss_row(fixture, check)
	_controls(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		(
			int(ORC.damage) == int(stats.get("orc_damage", -1))
			and is_equal_approx(
				float(ORC.attack_range_px), float(stats.get("orc_attack_range_px", -1.0))
			)
		),
		"the orc damage and reach are the fixture values"
	)
	check.call(
		(
			int(ARCHER.armor) == int(stats.get("tower_armor", -1))
			and int(TROLL.armor) == int(stats.get("troll_armor", -1))
			and is_equal_approx(
				float(TROLL.magic_resist), float(stats.get("troll_magic_resist", -1.0))
			)
		),
		"the tower and troll mitigation stats are the fixture values"
	)
	check.call(
		String(fixture.get("armor_item", "")) == ARMOR_ITEM,
		"the fixture armour item is Steel Aegis"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			int(shape.get("minion_take_damage_calls", -1)) == 1
			and int(shape.get("minion_two_positional_bare", -1)) == 1
			and int(shape.get("minion_sourced_calls", -1)) == 0
		),
		"the source minion attack is a bare two-positional call"
	)
	check.call(
		(
			bool(shape.get("minion_attack_source_line", false))
			and int(shape.get("hero_sourced_calls", -1)) >= 1
		),
		"the hero contrast keeps its sourced melee call"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _melee_hit(data, check)
		if live.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			int(live.get("hp_loss", -1)) == int(expected.get("hp_loss", -2)),
			"%s: the melee hit lands the source amount (got %s)" % [label, live.get("hp_loss")]
		)
		check.call(
			int(live.get("credited_total", -1)) == int(expected.get("credited_total", -2)),
			"%s: the sourceless hit records no credit" % label
		)
		var legacy := int(live.get("legacy_hp_loss", -1))
		check.call(
			legacy == int(native_old.get("hp_loss", -2)),
			"%s: the pre-9x declared school cuts the hit (got %s)" % [label, legacy]
		)
		if bool(data.get("expect_divergence", false)):
			check.call(
				int(expected.get("hp_loss", -1)) != legacy,
				"%s: the hit no longer matches the pre-9x column" % label
			)
		else:
			check.call(
				int(expected.get("hp_loss", -1)) == legacy,
				"%s: the control row is unchanged by the school fix" % label
			)
	check.call(replayed >= 3, "at least three fixture rows replay through the production path")


func _melee_hit(data: Dictionary, check: Callable) -> Dictionary:
	var kind := String(data.get("victim_kind", "minion"))
	var world := Siege.new()
	world.setup_arena()
	var victim: UnitState = null
	if kind == "tower":
		victim = world.spawn_structure(ARCHER, World.RED, POS)
		if victim != null:
			# The structure spawn hands the tower a free shield; the row only
			# measures the armour/school question.
			victim.shield = 0.0
			victim.shield_active = false
			victim.free_shield_active = false
	elif kind == "hero":
		# `prototype_battle.gd` extends `siege_battle.gd`, so the match world
		# runs the same `apply_hit` under test while providing heroes.
		world = World.new()
		world.setup_arena()
		victim = world.spawn_hero(World.VEX, World.RED, POS)
		if victim != null and int(data.get("hero_armor", 0)) > 0:
			victim.items.add(ARMOR_ITEM)
	else:
		victim = world.spawn_unit(TROLL, World.RED, 1)
		if victim != null:
			victim.position = POS
	if victim == null:
		check.call(false, "%s: the melee victim spawns" % String(data.get("name", "?")))
		return {}
	var attacker: UnitState = world.spawn_unit(ORC, World.BLUE, 1)
	if attacker == null:
		check.call(false, "%s: the minion attacker spawns" % String(data.get("name", "?")))
		return {}
	attacker.cooldown_ticks = 0
	attacker.position = victim.position + Vector2(MELEE_GAP, 0)
	var hp_before: float = victim.hp
	var credit_before := 0
	if victim is HeroState:
		credit_before = (victim as HeroState).damage_dealt
	if not world.apply_hit(attacker.id, victim.id):
		check.call(false, "%s: the minion hit lands" % String(data.get("name", "?")))
		return {}
	var after: UnitState = world.get_unit(victim.id) as UnitState
	if after == null:
		check.call(false, "%s: the victim stays registered" % String(data.get("name", "?")))
		return {}
	var payload := int(ORC.damage)
	var legacy := 0
	if kind == "tower":
		legacy = int(world._damage_amount(after, payload, "physical"))
	elif kind == "hero":
		legacy = int(DamageRules.item_aware_amount(after, payload, "physical", "normal"))
	else:
		legacy = int(DamageRules.minion_amount(after, payload, "physical"))
	return {
		"hp_loss": int(hp_before - after.hp),
		"credited_total":
		(int((victim as HeroState).damage_dealt) - credit_before) if victim is HeroState else 0,
		"legacy_hp_loss": legacy,
	}


func _boss_row(fixture: Dictionary, check: Callable) -> void:
	# The boss ladder is its own port, so the boss divergence is proven live
	# instead of through the source oracle: the same minion hit delivered with
	# the pre-9x `"physical"` school cuts armour, the sourceless one does not.
	var stats: Dictionary = fixture.get("live_stats", {})
	var payload := int(stats.get("orc_damage", 0))
	var live := _boss_hp_loss(payload, "live", check)
	var neutral := _boss_hp_loss(payload, "neutral", check)
	var legacy := _boss_hp_loss(payload, "physical", check)
	if live < 0 or neutral < 0 or legacy < 0:
		return
	check.call(
		live == neutral,
		"the minion attack lands the sourceless boss amount (%s vs %s)" % [live, neutral]
	)
	check.call(
		legacy < neutral,
		"the pre-9x physical school cuts the boss armour (%s vs %s)" % [legacy, neutral]
	)


func _boss_hp_loss(payload: int, mode: String, check: Callable) -> int:
	var world := World.new()
	world.setup_arena()
	var boss: BossState = world._spawn_boss(LIVE_BOSS)
	if boss == null:
		check.call(false, "the live boss spawns")
		return -1
	var orc: UnitState = world.spawn_unit(ORC, World.BLUE, 1)
	if orc == null:
		check.call(false, "the boss attacker spawns")
		return -1
	orc.cooldown_ticks = 0
	orc.position = boss.position + Vector2(MELEE_GAP, 0)
	var hp_before: float = boss.hp
	if mode == "live":
		world.apply_hit(orc.id, boss.id)
	elif mode == "neutral":
		world._deliver_hit(-1, orc.team, boss, payload, "neutral", orc.position)
	else:
		world._deliver_hit(orc.id, orc.team, boss, payload, "physical", orc.position)
	return int(hp_before - boss.hp)


func _controls(check: Callable) -> void:
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.spawn_hero(World.VEX, World.RED, POS)
	if hero == null:
		check.call(false, "the control hero spawns")
		return
	hero.items.add(ARMOR_ITEM)
	hero.items.add(REFLECT_ITEM)
	hero.items.thorn_timer = 100
	var orc: UnitState = world.spawn_unit(ORC, World.BLUE, 1)
	if orc == null:
		check.call(false, "the control minion spawns")
		return
	orc.cooldown_ticks = 0
	orc.position = hero.position + Vector2(MELEE_GAP, 0)
	var hero_before: float = hero.hp
	var orc_before: float = orc.hp
	check.call(world.apply_hit(orc.id, hero.id), "the armed minion hit lands")
	check.call(
		int(hero_before - hero.hp) == DamageRules.hero_amount(hero, int(ORC.damage), "normal"),
		"the hero keeps its damage-type-driven armour"
	)
	check.call(
		is_equal_approx(orc.hp, orc_before), "the sourceless hit never reflects back to the minion"
	)
	# A hero attacker through the same utility keeps the sourced shape and still
	# credits the post-armour amount.
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	var attacker: HeroState = world.blue_hero()
	if attacker == null or troll == null:
		check.call(false, "the hero attacker control spawns")
		return
	troll.position = attacker.position + Vector2(MELEE_GAP, 0)
	attacker.cooldown_ticks = 0
	var credit_before: int = attacker.damage_dealt
	var troll_before: float = troll.hp
	check.call(world.apply_hit(attacker.id, troll.id), "the hero melee hit lands")
	var expected := DamageRules.minion_amount(troll, int(attacker.definition.damage), "physical")
	check.call(
		int(troll_before - troll.hp) == expected,
		"a hero attacker is still cut by the minion armour"
	)
	check.call(
		int(attacker.damage_dealt - credit_before) == expected,
		"a hero attacker still credits the dealing hero"
	)
