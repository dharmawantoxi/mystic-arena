extends RefCounted
## 9v: the Grimjaw R opening hit must land school-free. The source locks the
## target with `h.target.take_damage(int(h.skill_damage * 2.5), h.team)`
## (`hero_skills/_bundle.py::_NS_grimjaw_skills.cast_r`): no `source=`, no
## school, so `resolve_damage_school` returns `None` (`_entity.py:106-130`) and
## `credit_hero_damage(None, ...)` records nothing. The port already passed `-1`
## (no credit) but kept `hero.dmg_school` (`grimjaw.tres` = `"physical"`), so
## troll armour 2 cut 65 -> 58 and the archer tower armour 3 cut 65 -> 55.
##
## The rest of the kit is already paritas and pinned here as controls: the Blade
## Fury spin tick, the E cone and the Omnislash follow-ups all pass
## `source=self.hero` with `school=getattr(hero, "dmg_school", None)`, which is
## the native delivery; a hero victim keeps its armour cut in both columns
## because that branch is damage-type driven (layer 9l).
##
## The replay drives the production `cast_hero_r` / `cast_hero_q` / `cast_hero_e`
## + `_tick_hero` chain into `_deliver_hit`. The counterfactual column is proven
## through the live ladders (`DamageRules.minion_amount(..., "physical")`,
## `DamageRules.resolve(..., TOWER_ARMOR, 0.0, "physical")`,
## `DamageRules.item_aware_amount(...)`) because the pre-9v school only existed
## at the call site.

const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const GRIMJAW = preload("res://data/heroes/grimjaw.tres")
const TROLL = preload("res://data/minions/troll.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/grimjaw_skill_arm_source.json"
const ARMOR_ITEM := "steel_aegis"
const POS := Vector2(400.0, 380.0)
const TARGET_OFFSET := Vector2(60.0, 0.0)
const TOWER_OFFSET := Vector2(40.0, 0.0)
const TOWER_ARMOR := 3.0
const TICK_COUNT := 165
const SOURCED_HIT := 50
const R_MULTIPLIER := 2.5
const E_MULTIPLIER := 1.5


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the grimjaw skill arm fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the grimjaw skill arm fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_replay(fixture.cases, check)
	_sourced_credit(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		is_equal_approx(float(TROLL.armor), float(stats.get("troll_armor", -1.0))),
		"the troll armour is the fixture value"
	)
	check.call(
		(
			is_equal_approx(float(ARCHER.armor), TOWER_ARMOR)
			and is_equal_approx(float(ARCHER.armor), float(stats.get("tower_armor", -1.0)))
		),
		"the archer tower armour is the fixture value"
	)
	check.call(
		String(GRIMJAW.dmg_school) == String(stats.get("native_school", "")),
		"the fixture native school is the live Grimjaw dmg_school"
	)
	check.call(
		String(fixture.get("armor_item", "")) == ARMOR_ITEM,
		"the fixture armour item is Steel Aegis"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _arm_hit(data, check)
		if live.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			_matches(live, expected),
			"%s: the arm lands the source amount and credit (got %s)" % [label, live]
		)
		var legacy := _native_old_ladder(data)
		if legacy < 0:
			continue
		check.call(
			int(native_old.get("hp_loss", -2)) == legacy,
			"%s: the pre-9v physical school cuts the arm (got %s)" % [label, legacy]
		)
		if bool(data.get("expect_divergence", false)):
			check.call(
				int(expected.get("hp_loss", -1)) != legacy,
				"%s: the arm no longer matches the pre-9v column" % label
			)
		else:
			check.call(
				int(expected.get("hp_loss", -1)) == legacy,
				"%s: the control row is unchanged by the school fix" % label
			)
	check.call(replayed >= 5, "at least five fixture rows replay through the production path")


func _arm_hit(data: Dictionary, check: Callable) -> Dictionary:
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.spawn_hero(GRIMJAW, World.BLUE, POS)
	if hero == null:
		check.call(false, "%s: the Grimjaw hero spawns" % String(data.get("name", "?")))
		return {}
	var kind := String(data.get("victim_kind", "minion"))
	var victim: UnitState = null
	var structures: Array = []
	if kind == "tower":
		victim = world.spawn_structure(ARCHER, World.RED, POS + TOWER_OFFSET)
		if victim != null:
			# `spawn_structure` hands the tower a free shield (layer 9m); the row
			# measures the armour question, so clear it first.
			victim.shield = 0.0
			victim.free_shield_active = false
			victim.shield_active = false
			hero.target_struct = victim
		structures = [victim] if victim != null else []
	elif kind == "hero":
		victim = world.spawn_hero(World.VEX, World.RED, POS + TARGET_OFFSET)
		if victim != null and int(data.get("hero_armor", 0)) > 0:
			victim.items.add(ARMOR_ITEM)
		if victim != null:
			hero.target_id = victim.id
	else:
		victim = world.spawn_unit(TROLL, World.RED, 1)
		if victim != null:
			victim.position = POS + TARGET_OFFSET
			hero.target_id = victim.id
	if victim == null:
		check.call(false, "%s: the skill victim spawns" % String(data.get("name", "?")))
		return {}
	var hp_before: float = victim.hp
	var credit_before: int = hero.damage_dealt
	var key := String(data.get("key", "r"))
	var cast := false
	match key:
		"q":
			cast = world.cast_hero_q(hero.id, structures)
		"e":
			cast = world.cast_hero_e(hero.id, structures)
		_:
			cast = world.cast_hero_r(hero.id, structures)
	if not cast:
		check.call(false, "%s: the skill cast lands" % String(data.get("name", "?")))
		return {}
	for _tick in range(int(data.get("ticks", 0))):
		world._tick_hero(hero)
	var after: UnitState = world.get_unit(victim.id) as UnitState
	if after == null:
		check.call(false, "%s: the victim stays registered" % String(data.get("name", "?")))
		return {}
	return {
		"hp_loss": int(hp_before - after.hp),
		"credited_total": int(hero.damage_dealt - credit_before),
	}


func _native_old_ladder(data: Dictionary) -> int:
	var key := String(data.get("key", "r"))
	var payload := _payload(key)
	var kind := String(data.get("victim_kind", "minion"))
	if kind == "tower":
		return int(DamageRules.resolve(payload, TOWER_ARMOR, 0.0, "physical"))
	if kind == "hero":
		var world := World.new()
		world.setup_arena()
		var victim: UnitState = world.spawn_hero(World.VEX, World.RED, POS + TARGET_OFFSET)
		if victim == null:
			return -1
		if int(data.get("hero_armor", 0)) > 0:
			victim.items.add(ARMOR_ITEM)
		return DamageRules.item_aware_amount(victim, payload, "physical", "normal")
	var probe := World.new()
	probe.setup_arena()
	var minion: UnitState = probe.spawn_unit(TROLL, World.RED, 1)
	if minion == null:
		return -1
	var per_hit := DamageRules.minion_amount(minion, payload, "physical")
	if key == "q":
		var ticks := int(data.get("ticks", 0))
		return per_hit * int(ticks / 15)
	return per_hit


func _payload(key: String) -> int:
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.spawn_hero(GRIMJAW, World.BLUE, POS)
	if hero == null:
		return 0
	if key == "q":
		return hero.skill_damage()
	if key == "e":
		return int(hero.skill_damage() * E_MULTIPLIER)
	return int(hero.skill_damage() * R_MULTIPLIER)


func _sourced_credit(check: Callable) -> void:
	# The hero's own basic attack passes `source=self`, so a minion hit keeps
	# crediting the post-armour amount — that path must not change.
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var minion: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if hero == null or minion == null:
		check.call(false, "the sourced control minion spawns")
		return
	var expected := DamageRules.minion_amount(minion, SOURCED_HIT, "physical")
	var hp_before: float = minion.hp
	var credit_before: int = hero.damage_dealt
	var landed: bool = world._deliver_hit(
		hero.id, hero.team, minion, SOURCED_HIT, "physical", hero.position
	)
	check.call(landed, "the sourced control hit lands")
	check.call(
		int(hp_before - minion.hp) == expected, "a sourced hit is still cut by the minion armour"
	)
	check.call(
		int(hero.damage_dealt - credit_before) == expected,
		"a sourced hit still credits the dealing hero"
	)


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	if int(actual.get("hp_loss", -1)) != int(expected.get("hp_loss", -2)):
		return false
	return int(actual.get("credited_total", -1)) == int(expected.get("credited_total", -2))
