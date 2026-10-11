extends RefCounted
## 9p: the un-sourced item arms must reach MINION and HERO victims with the
## source call shape of the arms themselves — `target.take_damage(amount,
## h.team[, "magic"])` (`hero_items.py:2542/2568/2589/2633/2648`), no `source=`.
## Layer 9o routed tower/castle victims that way; this suite pins the unit
## victims, whose ladders live in `Minion.take_damage` (`_entity.py:5795`) and
## `Hero.take_damage`.
##
## `deal_damage(target_id, hero_team, amount, school)` used to forward the
## dealing hero as `_deliver_hit` source together with the declared school, so a
## minion arm was cut by its armour/magic resist (49 / 47 instead of 55) and the
## dealing hero was credited. A hero victim keeps its item armour (the source
## armour branch is damage-type driven, layer 9l) but must not be credited. The
## replay drives the real inventory arm through the production bus into
## `_deliver_hit`; a legacy bus reproduces the pre-9p arguments for the
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
const FIXTURE := "res://tests/fixtures/item_unit_arm_source.json"
const ARMOR_ITEM := "steel_aegis"
const POS := Vector2(400.0, 380.0)
const BASIC_DAMAGE := 50
const SOURCED_HIT := 50


class UnitArmBus:
	extends BattleItemEffects
	var legacy := false
	var legacy_school := "physical"

	func deal_damage(
		target_id: int, source_team: int, amount: int, _school: String = "magic"
	) -> int:
		if not legacy:
			return super.deal_damage(target_id, source_team, amount, _school)
		# Pre-9p native shape: the arm carried the dealing hero as source and the
		# declared school for every victim.
		var tgt: Object = world.get_unit(target_id)
		if tgt == null:
			return 0
		world._deliver_hit(dealer_id, dealer_team, tgt, amount, legacy_school, dealer_pos)
		return amount


class UnitArmWorld:
	extends World
	var legacy_arm := false
	var legacy_school := "physical"

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := UnitArmBus.new()
		bus.world = self
		bus.legacy = legacy_arm
		bus.legacy_school = legacy_school
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the unit arm fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the unit arm fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_sourced_credit(check)
	_hero_armor_still_applies(check)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	var calls := int(shape.get("arm_take_damage_calls", 0))
	check.call(calls >= 5, "the source arm call sites are counted")
	check.call(
		int(shape.get("arm_calls_without_source_kwarg", -1)) == calls,
		"every arm call site lands without a source keyword"
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
			"%s: the un-sourced arm lands the source amount and credit (got %s)" % [label, live]
		)
		check.call(
			_matches(legacy, native_old),
			"%s: the pre-9p counterfactual replays (got %s)" % [label, legacy]
		)
		check.call(
			not _same_result(live, legacy),
			"%s: the arm no longer matches the pre-9p column" % label
		)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _arm_hit(data: Dictionary, legacy: bool, check: Callable) -> Dictionary:
	var world := UnitArmWorld.new()
	world.legacy_arm = legacy
	world.legacy_school = String(data.get("native_school", "physical"))
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var kind := String(data.get("victim_kind", "minion"))
	var victim: UnitState = null
	if kind == "hero":
		victim = world.spawn_hero(World.VEX, World.RED, POS)
		if victim != null and int(data.get("hero_armor", 0)) > 0:
			victim.items.add(ARMOR_ITEM)
	elif int(data.get("minion_armor", 0)) > 0:
		victim = world.spawn_unit(TROLL, World.RED, 1)
	else:
		victim = world.spawn_unit(UNDEAD, World.RED, 1)
	if hero == null or victim == null:
		check.call(
			false,
			(
				"%s: the unit arm victim spawns (hero=%s victim=%s)"
				% [String(data.get("name", "?")), hero != null, victim != null]
			)
		)
		return {}
	var item_id := String(data.get("item", ""))
	if not hero.items.add(item_id):
		check.call(false, "the arm item %s is addable" % item_id)
		return {}
	var entry: Dictionary = hero.items.item(item_id)
	var bash: Dictionary = entry.get("bash", {})
	var chance := float(bash.get("chance", 0.0))
	var hp_before: float = victim.hp
	var credit_before: int = hero.damage_dealt
	world._item_rng.seed = Prior.new()._seed_below(chance)
	hero.items.on_basic_attack_hit(
		victim.id, BASIC_DAMAGE, [], world._item_rng, world._battle_item_effects(hero)
	)
	var after: UnitState = world.get_unit(victim.id) as UnitState
	if after == null:
		check.call(false, "%s: the victim stays registered" % String(data.get("name", "?")))
		return {}
	return {
		"hp_loss": int(hp_before - after.hp),
		"credited_total": int(hero.damage_dealt - credit_before),
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


func _hero_armor_still_applies(check: Callable) -> void:
	# Layer 9l control: a sourceless arm on a hero keeps the item armour cut.
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var victim: UnitState = world.spawn_hero(World.VEX, World.RED, POS)
	if hero == null or victim == null:
		check.call(false, "the hero armour control victim spawns")
		return
	victim.items.add(ARMOR_ITEM)
	var expected := DamageRules.item_aware_amount(victim, 55, "neutral", "normal")
	var hp_before: float = victim.hp
	world._deliver_hit(-1, hero.team, victim, 55, "neutral", hero.position)
	check.call(
		int(hp_before - victim.hp) == expected,
		"a sourceless arm on a hero still runs the item armour ladder"
	)


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	for key in ["hp_loss", "credited_total"]:
		if int(actual.get(key, -1)) != int(expected.get(key, -1)):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	return _matches(left, right)
