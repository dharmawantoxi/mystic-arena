extends RefCounted
## 9s: the Razor Carapace reflect must reach MINION and HERO attackers with the
## source call shape — `source.take_damage(dmg, self.hero.team, "magic")`
## (`hero_items.py:2468`), no `source=` and no school. Layer 9i routed the BOSS
## attacker with `"magic"`; a unit attacker still received the declared magic
## school with the `"normal"` type default, so an undead attacker's 15% magic
## resist cut the reflected payload (144 of the 170 sent) and `_is_physical_hit`
## (`_entity.py:92-103`) saw a physical hit where the source sends a magic one.
##
## The replay drives the real inventory `notify_damage_taken` through the
## production bus into `_deliver_hit`; a legacy bus reproduces the pre-9s
## delivery for the counterfactual column, and a thorn-inactive control pins the
## guard that must keep suppressing the reflect.

const ReflectItemEffects = preload("res://scripts/match/reflect_item_effects.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const TROLL = preload("res://data/minions/troll.tres")
const UNDEAD = preload("res://data/minions/undead.tres")
const FIXTURE := "res://tests/fixtures/item_reflect_unit_source.json"
const REFLECT_ITEM := "razor_carapace"
const ARMOR_ITEM := "steel_aegis"
const POS := Vector2(400.0, 380.0)
const ATTACKER_OFFSET := Vector2(20.0, 0.0)
const INCOMING_DAMAGE := 200
const REFLECT_SENT := 170
const THORN_ACTIVE_TICKS := 270
const SOURCED_HIT := 50


class ReflectUnitBus:
	extends ReflectItemEffects
	var legacy := false

	func deal_damage(target_id: int, src_team: int, amount: int, school: String = "magic") -> int:
		if not legacy:
			return super.deal_damage(target_id, src_team, amount, school)
		# Pre-9s native shape: the reflect kept the declared magic school and the
		# `"normal"` damage-type default for every attacker.
		var attacker: Object = world.get_unit(target_id)
		if attacker == null:
			return 0
		world._deliver_hit(-1, src_team, attacker, amount, school, attacker.position)
		return amount


class ReflectUnitWorld:
	extends World
	var legacy_reflect := false

	func _reflect_item_effects(defender_team: int) -> ReflectItemEffects:
		var bus := ReflectUnitBus.new()
		bus.world = self
		bus.legacy = legacy_reflect
		bus.defender_team = defender_team
		return bus


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the reflect unit fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the reflect unit fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_thorn_inactive_control(check)
	_sourced_credit(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		is_equal_approx(float(UNDEAD.magic_resist), float(stats.get("undead_magic_resist", -1.0))),
		"the undead magic resist is the fixture value"
	)
	check.call(
		is_equal_approx(float(TROLL.armor), float(stats.get("troll_armor", -1.0))),
		"the troll armour is the fixture value"
	)
	check.call(
		is_equal_approx(float(TROLL.magic_resist), float(stats.get("troll_magic_resist", -1.0))),
		"the troll magic resist is the fixture value"
	)
	check.call(
		(
			int(fixture.get("reflect_sent", -1)) == REFLECT_SENT
			and int(fixture.get("incoming_damage", -1)) == INCOMING_DAMAGE
		),
		"the fixture pins the 0.85 reflect of 200 incoming damage"
	)
	check.call(
		String(fixture.get("armor_item", "")) == ARMOR_ITEM,
		"the fixture armour item is Steel Aegis"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		int(shape.get("reflect_calls_with_magic_type", 0)) >= 1,
		"the source reflect call site is counted"
	)
	check.call(
		int(shape.get("reflect_calls_with_source_kwarg", -1)) == 0,
		"the source reflect call lands without a source keyword"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _reflect_hit(data, false, check)
		var legacy := _reflect_hit(data, true, check)
		if live.is_empty() or legacy.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			_matches(live, expected),
			"%s: the reflect lands the source amount and credit (got %s)" % [label, live]
		)
		check.call(
			_matches(legacy, native_old),
			"%s: the pre-9s counterfactual replays (got %s)" % [label, legacy]
		)
		if bool(data.get("expect_divergence", false)):
			check.call(
				not _same_result(live, legacy),
				"%s: the reflect no longer matches the pre-9s column" % label
			)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _reflect_hit(data: Dictionary, legacy: bool, check: Callable) -> Dictionary:
	var world := ReflectUnitWorld.new()
	world.legacy_reflect = legacy
	world.setup_arena()
	var victim: HeroState = world.blue_hero()
	var kind := String(data.get("attacker_kind", "troll"))
	var attacker: UnitState = null
	if kind == "hero":
		attacker = world.spawn_hero(World.VEX, World.RED, POS + ATTACKER_OFFSET)
		if attacker != null and int(data.get("hero_armor", 0)) > 0:
			attacker.items.add(ARMOR_ITEM)
	elif kind == "undead":
		attacker = world.spawn_unit(UNDEAD, World.RED, 1)
	else:
		attacker = world.spawn_unit(TROLL, World.RED, 1)
	if attacker != null:
		# The live stubs carry the definition HP (troll 320, undead 65); the
		# fixture models a durable attacker so the payload is not clamped by the
		# death of the victim, exactly like the oracle stub.
		attacker.hp = 1000.0
		# `UnitState.max_hp` is definition-derived and read-only, so only the
		# live hp is raised to keep the payload out of the death clamp.
	if victim == null or attacker == null:
		check.call(
			false,
			(
				"%s: the reflect world spawns (victim=%s attacker=%s)"
				% [String(data.get("name", "?")), victim != null, attacker != null]
			)
		)
		return {}
	if not victim.items.add(REFLECT_ITEM):
		check.call(false, "the reflect item %s is addable" % REFLECT_ITEM)
		return {}
	victim.items.thorn_timer = THORN_ACTIVE_TICKS
	var hp_before: float = attacker.hp
	var credit_before: int = victim.damage_dealt
	victim.items.notify_damage_taken(
		INCOMING_DAMAGE,
		attacker.id,
		attacker.team,
		attacker.alive,
		world._item_rng,
		world._reflect_item_effects(victim.team)
	)
	var after: UnitState = world.get_unit(attacker.id) as UnitState
	if after == null:
		check.call(false, "%s: the attacker stays registered" % String(data.get("name", "?")))
		return {}
	return {
		"hp_loss": int(hp_before - after.hp),
		"credited_total": int(victim.damage_dealt - credit_before),
	}


func _thorn_inactive_control(check: Callable) -> void:
	# Without the thorn window `get_reflect_pct()` returns 0, so nothing fires.
	var world := ReflectUnitWorld.new()
	world.setup_arena()
	var victim: HeroState = world.blue_hero()
	var attacker: UnitState = world.spawn_unit(UNDEAD, World.RED, 1)
	if victim == null or attacker == null:
		check.call(false, "the thorn-inactive control victim spawns")
		return
	victim.items.add(REFLECT_ITEM)
	victim.items.thorn_timer = 0
	var hp_before: float = attacker.hp
	victim.items.notify_damage_taken(
		INCOMING_DAMAGE,
		attacker.id,
		attacker.team,
		attacker.alive,
		world._item_rng,
		world._reflect_item_effects(victim.team)
	)
	check.call(attacker.hp == hp_before, "an expired thorn window reflects nothing")


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
	for key in ["hp_loss", "credited_total"]:
		if int(actual.get(key, -1)) != int(expected.get(key, -1)):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	return _matches(left, right)
