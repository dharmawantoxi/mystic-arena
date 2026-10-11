extends RefCounted
## 9o: item-arm bonus damage must reach a TOWER/CASTLE with the source call
## shape of the arms themselves — `target.take_damage(amount, h.team[, "magic"])`
## (`hero_items.py:2542/2568/2589/2633/2648`), no `source=`. The structure
## ladders then run with `source=None` and `school=None`: `Tower.take_damage`
## never cuts the bonus with its armour, `credit_hero_damage(None, ...)` records
## nothing for the ATTACK DAMAGE DEALER picker, and `Castle.take_damage` still
## absorbs through the shield plus its 0.88 reduction.
##
## Before this layer the bus delivered those arms as
## `effects.deal_damage*(target_id, hero_team, amount, school)` with the dealing
## hero as `_deliver_hit` source, so the tower armour cut the bonus and the hero
## was credited. The replay drives the real inventory arm through the production
## bus into `_deliver_hit` -> `StructureState.absorb`; a legacy bus reproduces
## the pre-9o arguments for the counterfactual column, and a sourced direct hit
## pins the credit path that must keep working.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const NEXUS = preload("res://data/structures/nexus_level_1.tres")
const TROLL = preload("res://data/minions/troll.tres")
const FIXTURE := "res://tests/fixtures/item_structure_arm_source.json"
const BASIC_DAMAGE := 50
const STRUCTURE_POS := Vector2(400.0, 380.0)
const TOWER_ARMOR := 3.0
const CASTLE_SHIELD_MAX := 4000.0
const SOURCED_HIT := 50
const SOURCED_HIT_LOSS := 42
const MINION_ARM_FULL_HIT := 55
const MINION_ARM_ARMORED_HIT := 49


class StructArmBus:
	extends BattleItemEffects
	var legacy := false

	func deal_damage(
		target_id: int, source_team: int, amount: int, school: String = "magic"
	) -> int:
		if not legacy:
			return super.deal_damage(target_id, source_team, amount, school)
		# Pre-9o native shape: the arm carried the dealing hero as source.
		var tgt: Object = world.get_unit(target_id)
		if tgt == null:
			return 0
		world._deliver_hit(dealer_id, dealer_team, tgt, amount, school, dealer_pos)
		return amount

	func deal_damage_magic_sourceless(
		target_id: int, source_team: int, amount: int, school: String = "magic"
	) -> int:
		if not legacy:
			return super.deal_damage_magic_sourceless(target_id, source_team, amount, school)
		# Pre-9o shape of the magic arms: layer 9r moved them off `deal_damage`,
		# so the counterfactual replays the pre-9o arguments here.
		var tgt: Object = world.get_unit(target_id)
		if tgt == null:
			return 0
		world._deliver_hit(dealer_id, dealer_team, tgt, amount, school, dealer_pos)
		return amount


class StructArmWorld:
	extends World
	var legacy_arm := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := StructArmBus.new()
		bus.world = self
		bus.legacy = legacy_arm
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the structure arm fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the structure arm fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_replay(fixture.cases, check)
	_sourced_credit(check)
	_minion_fallback(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		is_equal_approx(float(ARCHER.armor), float(stats.get("tower_armor", -1.0))),
		"the archer tower armour is the fixture value"
	)
	check.call(
		is_equal_approx(float(NEXUS.shield_capacity), float(stats.get("castle_shield_max", -1.0))),
		"the nexus shield capacity is the fixture value"
	)
	check.call(
		is_equal_approx(
			float(NEXUS.shield_damage_reduction), float(stats.get("castle_reduction", -1.0))
		),
		"the nexus shield reduction is the fixture value"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _arm_hit(data, false, check)
		var legacy := _arm_hit(data, true, check)
		if live.is_empty() or legacy.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			_matches(live, expected),
			"%s: the arm lands the source amount and credit (got %s)" % [label, live]
		)
		check.call(
			_matches(legacy, native_old),
			"%s: the pre-9o counterfactual replays (got %s)" % [label, legacy]
		)
		check.call(
			not _same_result(live, legacy),
			"%s: the arm no longer matches the pre-9o column" % label
		)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _arm_hit(data: Dictionary, legacy: bool, check: Callable) -> Dictionary:
	var kind := String(data.get("structure_kind", "tower"))
	var world := StructArmWorld.new()
	world.legacy_arm = legacy
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	# `setup_arena` already spawned the red nexus, and `spawn_structure` refuses
	# a second nexus per team, so the castle rows reuse that live structure.
	var structure: StructureState = (
		world.spawn_structure(ARCHER, World.RED, STRUCTURE_POS)
		if kind == "tower"
		else world.nexuses[World.RED]
	)
	if hero == null or structure == null:
		check.call(
			false,
			(
				"%s: the arm victim spawns (hero=%s structure=%s)"
				% [String(data.get("name", "?")), hero != null, structure != null]
			)
		)
		return {}
	var item_id := String(data.get("item", ""))
	if not hero.items.add(item_id):
		check.call(false, "the arm item %s is addable" % item_id)
		return {}
	var shield_active := bool(data.get("castle_shield_active", true))
	structure.shield = float(data.get("castle_shield", 0.0))
	structure.shield_active = true if kind == "tower" else shield_active
	var entry: Dictionary = hero.items.item(item_id)
	var bash: Dictionary = entry.get("bash", {})
	var chance := float(bash.get("chance", 0.0))
	var hp_before: float = structure.hp
	var credit_before: int = hero.damage_dealt
	world._item_rng.seed = Prior.new()._seed_below(chance)
	hero.items.on_basic_attack_hit(
		structure.id, BASIC_DAMAGE, [], world._item_rng, world._battle_item_effects(hero)
	)
	structure = world.get_unit(structure.id) as StructureState
	return {
		"hp_loss": int(hp_before - structure.hp),
		"credited_total": int(hero.damage_dealt - credit_before),
	}


func _sourced_credit(check: Callable) -> void:
	# The hero's own basic attack passes `source=self`, so a tower hit keeps
	# crediting the post-armour amount — that path must not change.
	var world := _world()
	var hero: HeroState = world.blue_hero()
	var tower: StructureState = world.spawn_structure(ARCHER, World.RED, STRUCTURE_POS)
	if hero == null or tower == null:
		check.call(false, "the sourced control tower spawns")
		return
	tower.shield = 0.0
	var credit_before: int = hero.damage_dealt
	var hp_before: float = tower.hp
	var landed: bool = world._deliver_hit(
		hero.id, hero.team, tower, SOURCED_HIT, "physical", hero.position
	)
	check.call(landed, "the sourced control hit lands")
	check.call(
		int(hp_before - tower.hp) == SOURCED_HIT_LOSS,
		"a sourced basic hit is still cut by the tower armour"
	)
	check.call(
		int(hero.damage_dealt - credit_before) == SOURCED_HIT_LOSS,
		"a sourced basic hit still credits the hero"
	)


func _minion_fallback(check: Callable) -> void:
	# Layer 9p moved the unit victims onto the same sourceless route as the
	# structures of 9o, so `item_unit_arm_checks.gd` owns the minion/hero rows.
	# Here the old fallback control only proves the shared bus still lands the
	# full source amount without credit, while the sourced ladder keeps cutting.
	var world := _world()
	var hero: HeroState = world.blue_hero()
	var minion: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if hero == null or minion == null:
		check.call(false, "the unit arm fallback victim spawns")
		return
	check.call(
		(
			DamageRules.minion_amount(minion, MINION_ARM_FULL_HIT, "physical")
			== MINION_ARM_ARMORED_HIT
		),
		"the sourced minion ladder value is unchanged by 9p"
	)
	hero.items.add("abyss_breaker")
	var hp_before: float = minion.hp
	var credit_before: int = hero.damage_dealt
	world._item_rng.seed = Prior.new()._seed_below(1.0)
	hero.items.on_basic_attack_hit(
		minion.id, BASIC_DAMAGE, [], world._item_rng, world._battle_item_effects(hero)
	)
	check.call(
		int(hp_before - minion.hp) == MINION_ARM_FULL_HIT,
		"a 9p arm on a minion lands the full source amount"
	)
	check.call(int(hero.damage_dealt - credit_before) == 0, "a 9p arm on a minion credits nobody")


func _world() -> World:
	var world := World.new()
	world.setup_arena()
	return world


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	for key in ["hp_loss", "credited_total"]:
		if int(actual.get(key, -1)) != int(expected.get(key, -1)):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	return _matches(left, right)


func _hero_of_team(world: World, team: int) -> HeroState:
	for unit in world.units:
		var hero := unit as HeroState
		if hero != null and hero.is_hero and hero.team == team and hero.alive:
			return hero
	return null
