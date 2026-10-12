extends RefCounted
## 9q: the Cleave Axe splash must reach MINION and HERO victims with the source
## call shape of the cleave loop — `u.take_damage(splash, h.team)`
## (`hero_items.py:2504-2518`), no `source=` and no school. Layer 9e already
## routed the boss victim that way; the unit loop still delivered
## `_deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)`, so the
## minion armour cut the splash (45 of 50 on a troll) and the dealing hero was
## credited. A hero victim keeps its item armour (the source armour branch is
## damage-type driven, layer 9l) but must not be credited.
##
## The replay drives the real inventory cleave through the production bus into
## `_deliver_hit`; a legacy bus reproduces the pre-9q unit loop for the
## counterfactual column, and a sourced direct hit pins the credit path that
## must keep working.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const TROLL = preload("res://data/minions/troll.tres")
const UNDEAD = preload("res://data/minions/undead.tres")
const FIXTURE := "res://tests/fixtures/item_cleave_splash_source.json"
const CLEAVE_ITEM := "cleave_axe"
const ARMOR_ITEM := "steel_aegis"
const PRIMARY_POS := Vector2(400.0, 380.0)
const SPLASH_OFFSET := Vector2(50.0, 0.0)
const ROW_OFFSET := Vector2(0.0, 10.0)
const BASIC_DAMAGE := 100
const SOURCED_HIT := 50


class CleaveSplashBus:
	extends BattleItemEffects
	var legacy := false

	func cleave_splash(
		target_id: int, src_team: int, src_pos: Vector2, splash: int, radius: float
	) -> void:
		if not legacy:
			super.cleave_splash(target_id, src_team, src_pos, splash, radius)
			return
		# Pre-9q native unit loop: every splash carried the dealing hero as
		# source and the declared physical school.
		var center: Object = world.get_unit(target_id)
		if center == null:
			return
		var center_pos: Vector2 = center.position
		for u in world.units:
			if u == null or not u.alive or u.team == src_team or u.id == target_id:
				continue
			if center_pos.distance_to(u.position) <= radius:
				world._deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)


class CleaveSplashWorld:
	extends World
	var legacy_cleave := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := CleaveSplashBus.new()
		bus.world = self
		bus.legacy = legacy_cleave
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the cleave splash fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the cleave splash fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_sourced_credit(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		is_equal_approx(float(TROLL.armor), float(stats.get("troll_armor", -1.0))),
		"the troll armour is the fixture value"
	)
	check.call(
		is_equal_approx(float(UNDEAD.magic_resist), float(stats.get("undead_magic_resist", -1.0))),
		"the undead magic resist is the fixture value"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(int(shape.get("splash_calls", 0)) >= 1, "the source cleave call site is counted")
	check.call(
		int(shape.get("splash_calls_with_source_kwarg", -1)) == 0,
		"the source cleave call lands without a source keyword"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _cleave_hit(data, false, check)
		var legacy := _cleave_hit(data, true, check)
		if live.is_empty() or legacy.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			_matches(live, expected),
			"%s: the un-sourced splash lands the source amounts (got %s)" % [label, live]
		)
		check.call(
			_matches(legacy, native_old),
			"%s: the pre-9q counterfactual replays (got %s)" % [label, legacy]
		)
		check.call(
			int(live.get("total_credited", -1)) == 0,
			"%s: an un-sourced splash credits nobody" % label
		)
		check.call(
			not _same_result(live, legacy),
			"%s: the splash no longer matches the pre-9q column" % label
		)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _cleave_hit(data: Dictionary, legacy: bool, check: Callable) -> Dictionary:
	var world := CleaveSplashWorld.new()
	world.legacy_cleave = legacy
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var primary: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if hero == null or primary == null:
		check.call(
			false,
			(
				"%s: the cleave world spawns (hero=%s primary=%s)"
				% [String(data.get("name", "?")), hero != null, primary != null]
			)
		)
		return {}
	primary.position = PRIMARY_POS
	var specs: Array = data.get("victims", [])
	var victims: Array = []
	for index in range(specs.size()):
		var spec := String(specs[index])
		var spot := PRIMARY_POS + SPLASH_OFFSET + ROW_OFFSET * float(index)
		var victim: UnitState = null
		if spec.begins_with("hero"):
			victim = _hero_of_team(world, World.RED)
			if victim != null:
				victim.position = spot
				if spec.ends_with(":6"):
					victim.items.add(ARMOR_ITEM)
		elif spec == "undead":
			victim = world.spawn_unit(UNDEAD, World.RED, 1)
			if victim != null:
				victim.position = spot
		else:
			victim = world.spawn_unit(TROLL, World.RED, 1)
			if victim != null:
				victim.position = spot
		if victim == null:
			check.call(
				false, "%s: the splash victim %s spawns" % [String(data.get("name", "?")), spec]
			)
			return {}
		victims.append(victim)
	if not hero.items.add(CLEAVE_ITEM):
		check.call(false, "the cleave item %s is addable" % CLEAVE_ITEM)
		return {}
	var entry: Dictionary = hero.items.item(CLEAVE_ITEM)
	var passive: Dictionary = entry.get("passive", {})
	var pct := float(passive.get("cleave_pct", 0.0))
	var credit_before: int = hero.damage_dealt
	var before: Array = []
	for victim in victims:
		before.append(float(victim.hp))
	world._item_rng.seed = Prior.new()._seed_below(1.0)
	hero.items.on_basic_attack_hit(
		primary.id, BASIC_DAMAGE, [], world._item_rng, world._battle_item_effects(hero)
	)
	var hp_loss: Array = []
	for index in range(victims.size()):
		var after: UnitState = world.get_unit(int(victims[index].id)) as UnitState
		if after == null:
			check.call(
				false, "%s: a splash victim stays registered" % String(data.get("name", "?"))
			)
			return {}
		hp_loss.append(int(float(before[index]) - after.hp))
	return {
		"splash_damage": int(float(BASIC_DAMAGE) * pct),
		"hp_loss": hp_loss,
		"total_hp_loss": _sum(hp_loss),
		"total_credited": int(hero.damage_dealt - credit_before),
	}


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


func _hero_of_team(world: World, team: int) -> HeroState:
	for unit in world.units:
		var hero := unit as HeroState
		if hero != null and hero.is_hero and hero.team == team and hero.alive:
			return hero
	return null


func _sum(values: Array) -> int:
	var total := 0
	for value in values:
		total += int(value)
	return total


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	if int(actual.get("splash_damage", -1)) != int(expected.get("splash_damage", -2)):
		return false
	if int(actual.get("total_credited", -1)) != int(expected.get("total_credited", -2)):
		return false
	var left: Array = actual.get("hp_loss", [])
	var right: Array = expected.get("hp_loss", [])
	if left.size() != right.size():
		return false
	for index in range(left.size()):
		if int(left[index]) != int(right[index]):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	return _matches(left, right)
