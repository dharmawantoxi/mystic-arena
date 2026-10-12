extends RefCounted
## 9u: the Sylara skill arms must reach their victims school-free — every damage
## call in `hero_skills/_bundle.py::_NS_sylara_skills` passes the team only
## (`e.take_damage(int(h.skill_damage * ...), h.team)`), so `resolve_damage_school`
## returns `None` (`_entity.py:106-130`): the mineon armour/magic resist never
## cuts the skill and a tower victim keeps its armour out of the hit. The port
## sent `hero.dmg_school` (`sylara.tres` = `"physical"`), so a troll attacker ate
## an armour cut the source never applies and a tower victim lost 10 extra hp on
## the E shackle.
##
## The replay drives the production `cast_hero_q` / `cast_hero_e` / `_tick_hero`
## chain into `_deliver_hit`; the counterfactual column is proven through the
## live ladders (`DamageRules.minion_amount(..., "physical")` for minions and
## `DamageRules.resolve(..., TOWER_ARMOR, 0.0, "physical")` for the tower) because
## the pre-9u school only existed at the call site. The E stun gate follows the
## source `hasattr(target, 'attack_timer')` check, so a tower victim is left
## untouched instead of writing an unknown property.

const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const SYLARA = preload("res://data/heroes/sylara.tres")
const TROLL = preload("res://data/minions/troll.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/sylara_skill_arm_source.json"
const POS := Vector2(400.0, 380.0)
const LINE_OFFSET := Vector2(60.0, 0.0)
const SHACKLE_OFFSET := Vector2(100.0, 0.0)
const TOWER_ARMOR := 3.0
const TICK_COUNT := 15
const SOURCED_HIT := 50


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the sylara skill arm fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the sylara skill arm fixture parses")
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
		is_equal_approx(float(TROLL.magic_resist), float(stats.get("troll_magic_resist", -1.0))),
		"the troll magic resist is the fixture value"
	)
	check.call(
		is_equal_approx(float(ARCHER.armor), TOWER_ARMOR),
		"the archer tower armour is the fixture value"
	)
	check.call(
		(
			is_equal_approx(float(SYLARA.dmg_school.length()), 8.0)
			and String(SYLARA.dmg_school) == String(stats.get("native_school", ""))
		),
		"the fixture native school is the live Sylara dmg_school"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	var calls := int(shape.get("sylara_take_damage_calls", 0))
	check.call(calls >= 4, "the Sylara skill damage call sites are counted")
	check.call(
		int(shape.get("sylara_calls_with_two_positional_args", -1)) == calls,
		"every Sylara damage call passes the team only"
	)
	check.call(
		(
			int(shape.get("sylara_calls_with_school_kwarg", -1)) == 0
			and int(shape.get("sylara_calls_with_source_kwarg", -1)) == 0
		),
		"no Sylara damage call passes a school or a source"
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
			(int(live.get("hp_loss", -1)) > 0) == (int(expected.get("hp_loss", 0)) > 0),
			"%s: the arm lands damage like the source row" % label
		)
		check.call(
			_matches(live, expected),
			"%s: the school-free arm lands the source amount (got %s)" % [label, live]
		)
		check.call(
			int(live.get("credited_total", -1)) == 0,
			"%s: the un-sourced skill credits nobody" % label
		)
		if int(data.get("ticks", 0)) > 0:
			# Two payloads (initial hit + chain tick): only the divergence is
			# pinned, the ladder counterfactual belongs to the single-payload rows.
			check.call(
				int(native_old.get("hp_loss", -1)) != int(expected.get("hp_loss", -2)),
				"%s: the pre-9u physical school cuts the two-payload row" % label
			)
		else:
			var legacy := _native_old_ladder(data, live)
			check.call(
				legacy == int(native_old.get("hp_loss", -2)),
				"%s: the pre-9u physical school cuts the arm (got %s)" % [label, legacy]
			)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _native_old_ladder(data: Dictionary, live: Dictionary) -> int:
	var payloads: Array = live.get("payloads", [])
	if payloads.is_empty():
		return -1
	if String(data.get("victim_kind", "minion")) == "tower":
		return int(DamageRules.resolve(int(payloads[0]), TOWER_ARMOR, 0.0, "physical"))
	return _troll_ladder(int(payloads[0]))


func _troll_ladder(payload: int) -> int:
	# The pre-9u school ran the minion ladder with `"physical"`: armour cut.
	var world := World.new()
	world.setup_arena()
	var minion: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if minion == null:
		return -1
	return DamageRules.minion_amount(minion, payload, "physical")


func _arm_hit(data: Dictionary, check: Callable) -> Dictionary:
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.spawn_hero(SYLARA, World.BLUE, POS)
	if hero == null:
		check.call(false, "%s: the Sylara hero spawns" % String(data.get("name", "?")))
		return {}
	var kind := String(data.get("victim_kind", "minion"))
	var offset := LINE_OFFSET if String(data.get("key", "e")) == "q" else SHACKLE_OFFSET
	var victim: UnitState = null
	var structures: Array = []
	if kind == "tower":
		victim = world.spawn_structure(ARCHER, World.RED, POS + offset)
		if victim != null:
			# `spawn_structure` hands the tower a free shield (layer 9m); the row
			# measures the armour question, so clear it first.
			victim.shield = 0.0
			victim.free_shield_active = false
			victim.shield_active = false
		structures = [victim] if victim != null else []
	else:
		victim = world.spawn_unit(TROLL, World.RED, 1)
		if victim != null:
			victim.position = POS + offset
	if victim == null:
		check.call(false, "%s: the skill victim spawns" % String(data.get("name", "?")))
		return {}
	hero.target_id = victim.id
	var hp_before: float = victim.hp
	var credit_before: int = hero.damage_dealt
	var key := String(data.get("key", "e"))
	var cast := false
	if key == "q":
		cast = world.cast_hero_q(hero.id, structures)
	else:
		cast = world.cast_hero_e(hero.id, structures)
	if not cast:
		check.call(false, "%s: the skill cast lands" % String(data.get("name", "?")))
		return {}
	var payload: int = int(hero.skill_damage() * 0.7) if key == "e" else int(hero.skill_damage())
	var after: UnitState = world.get_unit(victim.id) as UnitState
	if after == null:
		check.call(false, "%s: the victim stays registered" % String(data.get("name", "?")))
		return {}
	var before_tick: float = after.hp
	for _tick in range(int(data.get("ticks", 0))):
		world._tick_hero(hero)
	return {
		"hp_loss": int(hp_before - after.hp),
		"credited_total": int(hero.damage_dealt - credit_before),
		"payloads": [payload],
		"tick_loss": int(before_tick - after.hp),
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


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	if int(actual.get("hp_loss", -1)) != int(expected.get("hp_loss", -2)):
		return false
	return int(actual.get("credited_total", -1)) == int(expected.get("credited_total", -2))
