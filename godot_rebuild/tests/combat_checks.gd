extends RefCounted
## Domain tests independent of SceneTree or visual nodes.

const Battle = preload("res://scripts/combat/minion_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const Damage = preload("res://scripts/combat/damage_rules.gd")
const Session = preload("res://scripts/simulation/combat_session.gd")
const Layout = preload("res://scripts/data/lane_layout.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const TROLL = preload("res://data/minions/troll.tres")


func run(check: Callable) -> void:
	_source_fixtures(check)
	_damage(check)
	_movement(check)
	_target_and_cooldown(check)
	_death_and_credit(check)
	_capacity_and_regen(check)
	_deterministic_soak(check)


func _source_fixtures(check: Callable) -> void:
	var lanes = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/lanes_source.json")
	)
	var stats = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/minion_source.json")
	)
	check.call(lanes is Dictionary and stats is Dictionary, "source fixtures parse")
	if not lanes is Dictionary or not stats is Dictionary:
		return
	var paths := Layout.create_paths()
	for lane_index in range(3):
		var expected: Array = lanes[Layout.NAMES[lane_index]]
		check.call(paths[lane_index].size() == expected.size(), "lane point count matches Python")
		if paths[lane_index].size() != expected.size():
			continue
		for point_index in range(expected.size()):
			var pair: Array = expected[point_index]
			check.call(
				paths[lane_index][point_index] == Vector2(pair[0], pair[1]),
				"Python lane %s point %d" % [Layout.NAMES[lane_index], point_index]
			)
	var field_map := {
		"name": "display_name",
		"hp": "max_hp",
		"damage": "damage",
		"speed": "speed_px_per_tick",
		"range": "attack_range_px",
		"attack_cooldown": "attack_cooldown_ticks",
		"gold_reward": "gold_reward",
		"radius": "radius_px",
		"regen": "regen_per_tick",
		"armor": "armor",
		"magic_resist": "magic_resist"
	}
	check.call(Session.DEFINITIONS.size() == stats.size(), "all five tier-1 definitions present")
	for definition in Session.DEFINITIONS:
		check.call(definition.is_valid(), "definition valid: " + definition.id)
		for source_key in field_map:
			var expected = stats[definition.id].get(source_key, 0)
			check.call(
				definition.get(field_map[source_key]) == expected,
				"source stat %s.%s" % [definition.id, source_key]
			)


func _damage(check: Callable) -> void:
	check.call(Damage.resolve(5, 0, 0, "physical") == 5, "unmitigated physical damage")
	check.call(Damage.resolve(5, 2, 0, "physical") == 4, "positive armor mitigation")
	check.call(Damage.resolve(10, -5, 0, "physical") == 13, "negative armor amplification")
	check.call(Damage.resolve(10, -100, 0, "physical") == 20, "negative armor amplification cap")
	check.call(Damage.resolve(5, 99, 0.5, "magic") == 2, "magic ignores armor, Python ties-to-even")
	check.call(Damage.resolve(7, 0, 0.5, "magic") == 4, "Python half rounding upward to even")
	check.call(Damage.resolve(5, 0, 1.0, "magic") == 1, "minimum positive damage matches source")
	check.call(Damage.resolve(0, 100, 1, "physical") == 0, "zero damage is not promoted to one")
	check.call(Damage.resolve(-5, 0, 0, "physical") == 0, "negative damage cannot heal")
	check.call(Damage.resolve(5, 0, 0, "typo") == 0, "unknown school cannot silently hit")


func _movement(check: Callable) -> void:
	var battle := Battle.new()
	battle.paths[1] = PackedVector2Array([Vector2.ZERO, Vector2(120, 0)])
	var blue := battle.spawn_unit(GOBLIN, 0, 1)
	var red := battle.spawn_unit(GOBLIN, 1, 1)
	check.call(blue.waypoint_index == 0 and red.waypoint_index == 1, "opposite path directions")
	battle.step_tick()
	check.call(
		blue.position == Vector2.ZERO and red.position == Vector2(120, 0),
		"source threshold advances index without moving that tick"
	)
	battle.step_tick()
	check.call(
		blue.position == Vector2(1.5, 0) and red.position == Vector2(118.5, 0),
		"tier-1 movement uses pixels per tick, not render delta"
	)
	var fresh := Battle.new()
	check.call(fresh.paths[1][0] == Vector2(170, 550), "path mutations isolated per world")
	var solo := Battle.new()
	solo.paths[1] = PackedVector2Array([Vector2.ZERO, Vector2(20, 0)])
	var runner := solo.spawn_unit(GOBLIN, 0, 1)
	for tick in range(30):
		solo.step_tick()
	check.call(
		solo.units.is_empty() and solo.get_unit(runner.id) == null, "route exit retires unit"
	)
	check.call(solo.escaped == [1, 0] and solo.kills == [0, 0], "route exit is not a kill")
	check.call(solo.credited_gold == [0, 0], "route exit cannot award kill credit")


func _target_and_cooldown(check: Callable) -> void:
	var battle := Battle.new()
	var blue := battle.spawn_unit(GOBLIN, 0, 1)
	var red := battle.spawn_unit(GOBLIN, 1, 1)
	blue.position = Vector2(100, 100)
	red.position = Vector2(120, 100)
	battle.step_tick()
	check.call(red.hp == 40 and blue.hp == 40, "both living units attack once in range")
	check.call(blue.cooldown_ticks == 45, "attack starts source cooldown")
	check.call(not battle.apply_hit(blue.id, red.id), "duplicate hit blocked by cooldown")
	for tick in range(44):
		battle.step_tick()
	check.call(red.hp == 40 and blue.cooldown_ticks == 1, "no early cooldown hit")
	battle.step_tick()
	check.call(red.hp == 35 and blue.cooldown_ticks == 45, "next attack exactly 45 ticks later")
	var ties := Battle.new()
	blue = ties.spawn_unit(GOBLIN, 0, 1)
	red = ties.spawn_unit(GOBLIN, 1, 1)
	var other := ties.spawn_unit(GOBLIN, 1, 1)
	blue.position = Vector2(100, 100)
	red.position = Vector2(120, 100)
	other.position = Vector2(80, 100)
	ties.step_tick()
	check.call(blue.target_id == red.id, "equal-distance targets resolve by stable spawn ID")
	check.call(other.hp == 45, "one attack cannot damage two targets")
	check.call(not ties.apply_hit(red.id, other.id), "friendly fire rejected")
	blue.cooldown_ticks = 0
	red.position = Vector2(1000, 100)
	check.call(not ties.apply_hit(blue.id, red.id), "out-of-range hit rejected")


func _death_and_credit(check: Callable) -> void:
	var battle := Battle.new()
	var blue := battle.spawn_unit(GOBLIN, 0, 1)
	var second_blue := battle.spawn_unit(GOBLIN, 0, 1)
	var red := battle.spawn_unit(GOBLIN, 1, 1)
	blue.position = Vector2(100, 100)
	second_blue.position = blue.position
	red.position = Vector2(110, 100)
	blue.hp = 5
	red.hp = 5
	battle.step_tick()
	check.call(red.hp == 0 and not red.alive, "lethal damage sets dead state and clamps HP")
	check.call(blue.hp == 5, "unit killed earlier this tick cannot retaliate")
	check.call(
		battle.kills == [1, 0] and battle.credited_gold == [8, 0], "death credits exactly once"
	)
	check.call(
		battle.get_unit(red.id) == null and battle.units.size() == 2, "dead registry entry removed"
	)
	check.call(
		blue.target_id == -1 and second_blue.target_id == -1, "dead target references cleared"
	)
	check.call(
		not battle.apply_hit(second_blue.id, red.id), "second attacker cannot hit retired target"
	)
	battle.step_tick()
	check.call(battle.credited_gold == [8, 0], "later tick cannot duplicate reward")
	var death_count := 0
	for event in battle.recent_events:
		if event.kind == "death":
			death_count += 1
	check.call(death_count == 1, "single death event")


func _capacity_and_regen(check: Callable) -> void:
	var battle := Battle.new()
	for wave in range(20):
		check.call(battle.spawn_wave(GOBLIN), "wave within cap accepted")
	check.call(battle.units.size() == 120, "bounded unit count")
	check.call(not battle.spawn_wave(GOBLIN), "wave over cap rejected atomically")
	check.call(
		battle.units.size() == 120 and battle.wave_count == 20, "rejection leaves state intact"
	)
	var invalid := Definition.new()
	invalid.max_hp = 0
	var fresh := Battle.new()
	check.call(
		not fresh.spawn_wave(invalid) and fresh.units.is_empty(),
		"invalid data cannot partially spawn"
	)
	check.call(fresh.spawn_unit(GOBLIN, 9, 1) == null, "invalid team rejected")
	check.call(fresh.spawn_unit(GOBLIN, 0, 3) == null, "invalid lane rejected")
	var troll := fresh.spawn_unit(TROLL, 0, 1)
	troll.hp = 319.8
	fresh.step_tick()
	check.call(troll.hp == 320, "regen clamps at max HP")
	troll.hp = 100
	fresh.step_tick()
	check.call(is_equal_approx(troll.hp, 100.6), "regen retains source per-tick unit")
	var another := fresh.spawn_unit(TROLL, 0, 1)
	check.call(another.hp == 320 and TROLL.max_hp == 320, "HP is not shared resource state")


func _deterministic_soak(check: Callable) -> void:
	var first := Battle.new()
	var second := Battle.new()
	for tick in range(2400):
		if tick % 300 == 0:
			var definition: Definition = Session.DEFINITIONS[(tick / 300) % 2]
			first.spawn_wave(definition)
			second.spawn_wave(definition)
		first.step_tick()
		second.step_tick()
		if tick % 120 == 0:
			check.call(
				_snapshot(first) == _snapshot(second), "repeatable deterministic tick %d" % tick
			)
	check.call(first.kills[0] + first.kills[1] > 0, "real lane traversal leads to combat/deaths")
	check.call(first.recent_events.size() <= Battle.MAX_EVENTS, "event history stays bounded")
	check.call(first.units.size() <= Battle.MAX_UNITS, "soak respects unit cap")


func _snapshot(battle: Battle) -> Array:
	var state: Array = [
		battle.tick_count, battle.kills.duplicate(), battle.credited_gold.duplicate()
	]
	for unit in battle.units:
		state.append([unit.id, unit.position, unit.hp, unit.cooldown_ticks, unit.target_id])
	return state
