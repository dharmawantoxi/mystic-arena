extends RefCounted
## Kaizen-1 domain checks: spawn/levels/basic attack/Q combo/death,
## all expected values from fixtures/kaizen_source.json (real source).

const Battle = preload("res://scripts/combat/minion_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const ARCHER_L1 = preload("res://data/structures/archer_level_1.tres")

const BLUE := 0
const RED := 1
const FAT_HP := 100000.0


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/kaizen_source.json")
	)
	check.call(fixture is Dictionary, "kaizen fixture parses")
	if not fixture is Dictionary:
		return
	_identity(check, fixture["hero"])
	_levels(check, fixture["levels"])
	_skill_prop(check, fixture["skill_prop"])
	_eff(check, fixture["eff"])
	_basic(check, fixture["basic"])
	_q1(check, fixture["q1"])
	_q1_kill(check, fixture["q1_kill"])
	_q1_fizzle(check, fixture["q1_fizzle"])
	_q1_cooldown(check, fixture["q1_cooldown"])
	_q2(check, fixture["q2"])
	_quirk(check, fixture["q1"])
	_qtimers(check)
	_take(check, fixture["take"])
	_guards(check)


func _battle() -> Battle:
	return Battle.new()


func _hero(battle, x: float, y: float, team: int = BLUE):
	return battle.spawn_hero(KAIZEN, team, Vector2(x, y))


func _victim(battle, x: float, y: float, team: int, hp: float, definition = null):
	var goblin = definition if definition != null else GOBLIN
	var unit = battle.spawn_unit(goblin, team, 1)
	unit.position = Vector2(x, y)
	unit.hp = hp
	return unit


func _tower(x: float, y: float):
	var tower := StructureState.new()
	tower.id = 9001
	tower.team = RED
	tower.definition = ARCHER_L1
	tower.position = Vector2(x, y)
	tower.hp = ARCHER_L1.max_hp
	tower.shield = ARCHER_L1.shield_capacity
	tower.shield_max = ARCHER_L1.shield_capacity
	tower.shield_active = true
	tower.alive = true
	return tower


func _damage_sum(calls: Array) -> int:
	var total := 0
	for call in calls:
		total += int(call["damage"])
	return total


func _identity(check: Callable, expected: Dictionary) -> void:
	check.call(KAIZEN.is_valid(), "kaizen definition valid")
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	check.call(hero != null and hero.is_hero, "hero spawns flagged")
	check.call(hero.settings().display_name == str(expected["name"]), "hero name")
	check.call(hero.settings().title == str(expected["title"]), "hero title")
	check.call(hero.settings().role == str(expected["role"]), "hero role")
	check.call(hero.settings().cost == int(expected["catalog_cost"]), "hero cost")
	check.call(hero.settings().unlock_cost == int(expected["catalog_unlock_cost"]), "hero unlock")
	check.call(hero.level == int(expected["level"]), "hero level 1")
	check.call(hero.hp == float(expected["hp"]), "hero hp")
	check.call(hero.max_hp == float(expected["max_hp"]), "hero max hp")
	check.call(hero.damage == int(expected["damage"]), "hero damage")
	check.call(hero.skill_damage() == int(expected["skill_damage"]), "hero skill")
	check.call(hero.speed == float(expected["speed"]), "hero speed")
	check.call(hero.attack_range == float(expected["range"]), "hero range")
	check.call(hero.attack_cd_base == int(expected["attack_cd_base"]), "hero base cd")
	check.call(
		hero.eff_attack_cd(hero.attack_cd_base) == int(expected["attack_cd_prop"]), "hero eff cd"
	)
	check.call(hero.skill_cd_max == int(expected["skill_cooldown_max"]), "hero skill cd")
	check.call(hero.skill_range == float(expected["skill_range"]), "hero skill range")
	check.call(hero.dmg_school == str(expected["dmg_school"]), "hero school")
	check.call(hero.is_melee == bool(expected["is_melee_hero"]), "hero melee")
	check.call(hero.settings().radius_px == float(expected["radius"]), "hero radius")
	check.call(hero.facing == float(expected["facing"]), "blue hero faces right")
	check.call(hero.position == Vector2(500.0, 340.0), "hero spawn position")
	check.call(hero.target_id == -1 and hero.target_struct == null, "no target at spawn")
	check.call(hero.attack_timer == 0 and hero.skill_timer == 0, "timers zero at spawn")
	check.call(hero.deaths == 0 and hero.killed_by == -1, "no deaths at spawn")
	var qstate: Array = expected["q_state"]
	check.call(
		(
			hero.q_stack == int(qstate[0])
			and hero.q_reset_timer == int(qstate[1])
			and hero.is_dashing == bool(qstate[2])
			and hero.dash_timer == int(qstate[3])
			and hero.wind_wall_timer == int(qstate[4])
			and hero.ulti_active == bool(qstate[5])
			and hero.ulti_timer == int(qstate[6])
		),
		"q state zero at spawn"
	)
	var red = _hero(battle, 600.0, 340.0, RED)
	check.call(red.facing == -1.0, "red hero faces left")


func _levels(check: Callable, rows: Array) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	hero.hp = 1.0
	check.call(rows.size() == 15, "fifteen source levels")
	for row in rows:
		var level := int(row["level"])
		check.call(hero.level == level, "at source level %d" % level)
		check.call(hero.damage == int(row["damage"]), "level %d damage" % level)
		check.call(hero.skill_damage() == int(row["skill_damage"]), "level %d skill" % level)
		check.call(hero.max_hp == float(row["max_hp"]), "level %d max hp" % level)
		check.call(hero.upgrade_cost() == int(row["upgrade_cost"]), "level %d cost" % level)
		if level < 15:
			check.call(battle.upgrade_hero(hero.id), "level %d upgrades" % level)
			check.call(hero.hp == float(row["hp_after"]), "level %d keeps hp" % level)
		else:
			check.call(not battle.upgrade_hero(hero.id), "level 15 maxed")


func _skill_prop(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var cases: Dictionary = expected["cases"]
	check.call(hero.skill_damage() == int(cases["none"]), "skill unpenalized")
	# Explicit keys: str(1.0) is "1", not "1.0".
	for pair in [["0.2", 0.2], ["0.5", 0.5], ["1.0", 1.0]]:
		var probe = _hero(battle, 500.0, 340.0)
		probe.skill_down_amount = float(pair[1])
		probe.skill_down_timer = 60
		check.call(
			probe.skill_damage() == int(cases[str(pair[0])]), "skill at down %s" % str(pair[0])
		)


func _eff(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var cases: Dictionary = expected["attack_cd"]
	check.call(hero.eff_attack_cd(hero.attack_cd_base) == int(cases["none"]), "cd unslowed")
	for pair in [["0.15", 0.15], ["0.4", 0.4], ["1.0", 1.0]]:
		var probe = _hero(battle, 500.0, 340.0)
		check.call(battle.apply_atk_slow(probe.id, float(pair[1]), 60), "atk slow applies")
		check.call(
			probe.eff_attack_cd(probe.attack_cd_base) == int(cases["slow_" + str(pair[0])]),
			"cd at slow %s" % str(pair[0])
		)
	var stunned = _hero(battle, 500.0, 340.0)
	stunned.stun_timer = 30
	check.call(stunned.eff_attack_cd(stunned.attack_cd_base) == int(cases["stunned"]), "cd stunned")
	check.call(hero.eff_attack_range() == float(expected["attack_range"]), "eff range")


func _basic(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var tough := GOBLIN.duplicate() as Definition
	tough.magic_resist = 0.5
	var target = _victim(battle, 560.0, 340.0, RED, FAT_HP, tough)
	check.call(battle.hero_basic_attack(hero.id, target.id), "basic attack strikes")
	# Full damage through 0.5 magic resist proves the physical school.
	var hit: Dictionary = expected["hit"]
	check.call(target.hp == FAT_HP - _damage_sum(hit["calls"]), "basic attack damage")
	check.call(hero.attack_timer == int(expected["attack_timer"]), "basic sets timer")
	check.call(hero.facing == float(expected["facing"]), "basic faces right")
	check.call(hero.attack_seq == int(expected["seq"]), "basic sequence counts")
	check.call(hero.target_id == -1, "basic does not auto-target")
	check.call(not battle.hero_basic_attack(hero.id, target.id), "timer blocks basic")
	check.call(target.hp == FAT_HP - _damage_sum(hit["calls"]), "blocked basic harmless")
	check.call(hero.attack_timer == int(expected["blocked_timer"]), "blocked timer kept")
	var fresh = _hero(battle, 500.0, 340.0)
	var oob = _victim(battle, 571.0, 340.0, RED, FAT_HP)
	check.call(not battle.hero_basic_attack(fresh.id, oob.id), "range blocks basic")
	check.call(fresh.attack_timer == int(expected["out_of_range_timer"]), "oob timer kept")
	var corpse = _victim(battle, 560.0, 340.0, RED, FAT_HP)
	corpse.alive = false
	check.call(not battle.hero_basic_attack(fresh.id, corpse.id), "dead target blocks")
	var left = _hero(battle, 500.0, 340.0)
	var west = _victim(battle, 440.0, 340.0, RED, FAT_HP)
	check.call(battle.hero_basic_attack(left.id, west.id), "basic strikes left")
	check.call(left.facing == float(expected["facing_left"]), "basic faces left")
	var up = _hero(battle, 500.0, 340.0)
	var north = _victim(battle, 500.0, 300.0, RED, FAT_HP)
	check.call(battle.hero_basic_attack(up.id, north.id), "basic strikes above")
	check.call(up.facing == float(expected["facing_above"]), "zero dx keeps facing")


func _q_lineup(battle: Battle):
	var tough := GOBLIN.duplicate() as Definition
	tough.magic_resist = 0.5
	var units := [
		_victim(battle, 560.0, 340.0, RED, FAT_HP, tough),
		_victim(battle, 600.0, 340.0, RED, FAT_HP),
		_victim(battle, 610.0, 340.0, RED, FAT_HP),
		_victim(battle, 616.0, 340.0, RED, FAT_HP),
	]
	var dead = _victim(battle, 540.0, 340.0, RED, FAT_HP)
	dead.alive = false
	units.append(dead)
	units.append(_victim(battle, 560.0, 300.0, BLUE, FAT_HP))
	return units


func _q1(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var units: Array = _q_lineup(battle)
	var tower = _tower(560.0, 400.0)
	check.call(battle.cast_hero_q(hero.id, [tower]), "q1 casts")
	check.call(hero.skill_timer == int(expected["skill_timer"]), "q1 sets skill timer")
	check.call(hero.q_stack == int(expected["q_stack"]), "q1 sets stack")
	check.call(hero.q_reset_timer == int(expected["q_reset_timer"]), "q1 sets reset")
	check.call(hero.active_skill == str(expected["active_skill"]), "q1 visual key")
	check.call(hero.active_skill_timer == int(expected["active_skill_timer"]), "q1 visual timer")
	check.call(hero.target_id == units[0].id, "q1 acquires nearest")
	check.call(hero.position == Vector2(500.0, 340.0), "q1 holds position")
	var victims: Array = expected["victims"]
	for index in range(victims.size()):
		var want: Dictionary = victims[index]
		check.call(
			units[index].hp == FAT_HP - _damage_sum(want["calls"]), "q1 victim %s" % str(want["id"])
		)
	check.call(tower.hp == float(expected["tower_hp"]), "q1 tower hp kept")
	check.call(tower.shield == float(expected["tower_shield"]), "q1 tower shield soaks")


func _q1_kill(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var units: Array = _q_lineup(battle)
	var weak = _victim(battle, 550.0, 340.0, RED, 30.0)
	units.append(weak)
	check.call(battle.cast_hero_q(hero.id), "q1 casts into crowd")
	check.call(weak.alive == bool(expected["alive"]), "q1 kills the weak")
	check.call(weak.hp == float(expected["hp"]), "q1 weak hp zero")


func _q1_fizzle(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var far_foe = _victim(battle, 616.0, 340.0, RED, FAT_HP)
	check.call(not battle.cast_hero_q(hero.id), "q1 fizzles out of reach")
	check.call(hero.skill_timer == int(expected["skill_timer"]), "fizzle spares timer")
	check.call(hero.q_stack == int(expected["q_stack"]), "fizzle spares stack")
	check.call(far_foe.hp == FAT_HP, "fizzle harmless")


func _q1_cooldown(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	hero.skill_timer = 10
	var close = _victim(battle, 560.0, 340.0, RED, FAT_HP)
	check.call(not battle.cast_hero_q(hero.id), "q1 blocked on cooldown")
	check.call(hero.skill_timer == int(expected["skill_timer"]), "cooldown kept")
	check.call(close.hp == FAT_HP, "cooldown harmless")


func _q2(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var units: Array = _q_lineup(battle)
	var tower = _tower(560.0, 400.0)
	check.call(battle.cast_hero_q(hero.id, [tower]), "q1 opens combo")
	hero.skill_timer = 0
	check.call(battle.cast_hero_q(hero.id, [tower]), "q2 dash strike")
	var pos: Array = expected["pos"]
	check.call(
		hero.position.is_equal_approx(Vector2(float(pos[0]), float(pos[1]))), "q2 dashes 70 percent"
	)
	check.call(hero.is_dashing == bool(expected["is_dashing"]), "q2 dash flag")
	check.call(hero.dash_timer == int(expected["dash_timer"]), "q2 dash timer")
	check.call(hero.q_stack == int(expected["q_stack"]), "q2 clears stack")
	check.call(hero.q_reset_timer == int(expected["q_reset_timer"]), "q2 refreshes reset")
	check.call(hero.skill_timer == int(expected["skill_timer"]), "q2 re-timer")
	check.call(hero.target_id == units[0].id, "q2 keeps target")
	check.call(hero.active_skill == str(expected["active_skill"]), "q2 visual key")
	check.call(hero.active_skill_timer == int(expected["active_skill_timer"]), "q2 visual timer")
	var victims: Array = expected["victims"]
	for index in range(victims.size()):
		var want: Dictionary = victims[index]
		check.call(
			units[index].hp == FAT_HP - _damage_sum(want["calls"]), "q2 victim %s" % str(want["id"])
		)
	check.call(tower.hp == float(expected["tower_hp"]), "q2 tower hp kept")
	check.call(tower.shield == float(expected["tower_shield"]), "q2 tower shield soaks")


func _quirk(check: Callable, q1: Dictionary) -> void:
	# Source quirk: the 180-tick combo reset expires before the
	# 300-tick cooldown, so the follow-up cast is Q1 again. The real
	# update ticks both clocks; mirror that with full step_ticks.
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var units: Array = _q_lineup(battle)
	check.call(battle.cast_hero_q(hero.id), "quirk q1 opens")
	for _index in range(180):
		battle.step_tick()
	check.call(hero.q_stack == 0, "reset expires first")
	check.call(hero.skill_timer == int(q1["skill_timer"]) - 180, "cooldown still running")
	for _index in range(120):
		battle.step_tick()
	check.call(hero.skill_timer == 0, "cooldown finishes later")
	# Minions skirmish during the wait; pin the lineup so the
	# follow-up gate is deterministic.
	units[0].position = Vector2(560.0, 340.0)
	units[1].position = Vector2(600.0, 340.0)
	check.call(battle.cast_hero_q(hero.id), "follow-up still casts")
	check.call(hero.q_stack == 1, "follow-up is q1 again")


func _qtimers(check: Callable) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	_q_lineup(battle)
	check.call(battle.cast_hero_q(hero.id), "qtimers q1 opens")
	hero.skill_timer = 0
	check.call(battle.cast_hero_q(hero.id), "qtimers q2 lands")
	for _index in range(15):
		battle.step_tick()
	check.call(not hero.is_dashing, "dash flag clears")
	check.call(hero.dash_timer == 0, "dash timer clears")
	check.call(hero.q_stack == 0, "stack stays spent through dash")
	check.call(hero.q_reset_timer == 165, "reset ticks through dash")
	for _index in range(165):
		battle.step_tick()
	check.call(hero.q_stack == 0, "stack clears at reset")
	check.call(hero.q_reset_timer == 0, "reset clears")


func _take(check: Callable, expected: Dictionary) -> void:
	var battle := _battle()
	var hero = _hero(battle, 500.0, 340.0)
	var brutal := GOBLIN.duplicate() as Definition
	brutal.damage = 100
	var killer = _victim(battle, 520.0, 340.0, RED, FAT_HP, brutal)
	check.call(battle.apply_hit(killer.id, hero.id), "minion hits hero")
	check.call(hero.hp == float(expected["hp_after"]), "hero takes full hit")
	check.call(hero.alive == bool(expected["alive"]), "hero survives hit")
	hero.hp = 10.0
	check.call(battle.apply_slow(hero.id, 0.3, 60), "slow applies to hero")
	killer.cooldown_ticks = 0
	var gold_before: int = battle.credited_gold[RED]
	check.call(battle.apply_hit(killer.id, hero.id), "minion kills hero")
	var death: Dictionary = expected["death"]
	check.call(hero.alive == bool(death["alive"]), "hero dies")
	check.call(hero.hp == float(death["hp"]), "hero hp zero")
	check.call(hero.deaths == int(death["deaths"]), "hero deaths count")
	check.call(hero.killed_by == killer.id, "hero killer id")
	check.call(hero.slow_amount == 0.0 and hero.slow_timer == 0, "death clears slow")
	check.call(battle.credited_gold[RED] == gold_before, "no gold for hero kill")
	check.call(battle.get_unit(hero.id) == hero, "dead hero stays addressable")
	var doomed = _victim(battle, 600.0, 340.0, RED, 5.0)
	doomed.alive = false
	battle.step_tick()
	check.call(battle.get_unit(hero.id) == hero, "dead hero not retired")
	check.call(battle.get_unit(doomed.id) == null, "dead minion retired")
	var fresh := _battle()
	var overkill = _hero(fresh, 500.0, 340.0)
	var cannon := GOBLIN.duplicate() as Definition
	cannon.damage = 999999
	var executioner = _victim(fresh, 520.0, 340.0, RED, FAT_HP, cannon)
	check.call(fresh.apply_hit(executioner.id, overkill.id), "overkill lands")
	check.call(overkill.hp == float(expected["overkill_hp"]), "overkill hp zero")
	check.call(overkill.alive == bool(expected["overkill_alive"]), "overkill kills")


func _guards(check: Callable) -> void:
	var battle := _battle()
	check.call(battle.spawn_hero(null, BLUE, Vector2.ZERO) == null, "null definition refused")
	check.call(battle.spawn_hero(KAIZEN, 7, Vector2.ZERO) == null, "bad team refused")
	var high = battle.spawn_hero(KAIZEN, BLUE, Vector2.ZERO, 99)
	check.call(high.level == 15, "spawn clamps level high")
	var low = battle.spawn_hero(KAIZEN, BLUE, Vector2.ZERO, 0)
	check.call(low.level == 1, "spawn clamps level low")
	check.call(not battle.hero_basic_attack(4242, 4243), "basic rejects bad ids")
	check.call(not battle.cast_hero_q(4242), "cast rejects bad id")
	check.call(not battle.upgrade_hero(4242), "upgrade rejects bad id")
	var hero = _hero(battle, 500.0, 340.0)
	var ally = _victim(battle, 520.0, 340.0, BLUE, FAT_HP)
	check.call(not battle.hero_basic_attack(hero.id, ally.id), "basic refuses ally")
	check.call(ally.hp == FAT_HP, "refused basic harmless")
	check.call(hero.attack_timer == hero.attack_cd_base, "refused basic still winds up")
	hero.alive = false
	var foe = _victim(battle, 520.0, 340.0, RED, FAT_HP)
	check.call(not battle.hero_basic_attack(hero.id, foe.id), "dead hero cannot strike")
	check.call(not battle.cast_hero_q(hero.id), "dead hero cannot cast")
	var lonely = _hero(Battle.new(), 500.0, 340.0)
	check.call(lonely != null, "lonely hero spawns")
	var ready := _battle()
	var caster = _hero(ready, 500.0, 340.0)
	check.call(not ready.can_cast_hero_q(caster.id), "lonely Q has no target")
	_victim(ready, 530.0, 340.0, RED, FAT_HP)
	check.call(ready.can_cast_hero_q(caster.id), "live hero readies Q on foe")
