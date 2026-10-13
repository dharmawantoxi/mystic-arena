# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ai native suite: the store's non-positive guard is measured, unreachable.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/debuff_payload_reach_source.json"

const FIELDS := {
	"slow": ["slow_amount", "slow_timer"],
	"atk_slow": ["atk_slow_amount", "atk_slow_timer"],
	"skill_down": ["skill_down_amount", "skill_down_timer"],
	"anti_heal": ["anti_heal_amount", "anti_heal_timer"],
}

const GATED := {"anti_heal": 1, "atk_slow": 2, "burn": 3, "skill_down": 1, "slow": 3}
const UNGATED := {"None": 1, "anti_heal": 3, "atk_slow": 3, "burn": 2, "skill_down": 1, "slow": 44}
const ARMS := {
	"apply_anti_heal": 4,
	"apply_atk_slow": 5,
	"apply_burn": 5,
	"apply_skill_down": 2,
	"apply_slow": 94,
}


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "debuff payload fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	var world := Prototype.new()
	world.setup_arena()
	for row in fixture.rows:
		_replay_row(check, world, row)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	var minimums: Dictionary = shape.get("min_payload", {})
	var positive := not minimums.is_empty()
	for key in minimums:
		if float(minimums[key]) <= 0.0:
			positive = false
	check.call(
		positive and float(shape.get("min_call_literal", 0.0)) > 0.0,
		"every source payload literal is positive"
	)
	var emission: Dictionary = shape.get("emission", {})
	check.call(
		(
			_same_counts(emission.get("gated", {}), GATED)
			and _same_counts(emission.get("ungated", {}), UNGATED)
		),
		"the source arm gates match the pinned census"
	)
	check.call(
		(
			int(emission.get("burn_sites", -1)) == 5
			and (
				int(emission.get("burn_sites", -1))
				== int(emission.get("burn_with_source_team", -2))
			)
		),
		"all five source burn sites pass a source team"
	)
	var native: Dictionary = shape.get("native", {})
	check.call(
		_same_counts(native.get("arms", {}), ARMS), "the native arm census matches the source"
	)
	check.call(
		Array(native.get("non_positive_arms", [])).is_empty(),
		"no native arm passes a non-positive payload"
	)
	var guarded: Dictionary = native.get("store_guarded", {})
	var all_guarded := guarded.size() == 5
	for method in guarded:
		if not bool(guarded[method]):
			all_guarded = false
	check.call(all_guarded, "every world store method keeps its non-positive guard")
	check.call(fixture.rows.size() == 32, "the fixture keeps its 32 rows")


func _replay_row(check: Callable, world: Prototype, row: Dictionary) -> void:
	var label := String(row.get("name", "unknown"))
	var kind := String(row.get("kind", "slow"))
	var victim: UnitState = world.spawn_unit(GOBLIN, world.RED, 0)
	if victim == null:
		check.call(false, "debuff victim spawns: %s" % label)
		return
	_reset_store(victim)
	var accepted: Array = row.get("accepted", [])
	var index := 0
	for step in row.get("input", []):
		var applied := _apply_step(world, victim, kind, step)
		var wanted := index < accepted.size() and bool(accepted[index])
		check.call(applied == wanted, "store verdict matches the row: %s step %d" % [label, index])
		index += 1
	check.call(
		_store_matches(victim, kind, row.get("expected", {})),
		"stored state matches the native column: %s" % label
	)
	var source_rule: Dictionary = row.get("source_rule", {})
	if row.get("divergence") == null:
		check.call(
			_store_matches(victim, kind, source_rule),
			"the source rule and the native store agree: %s" % label
		)
	else:
		check.call(
			not _store_matches(victim, kind, source_rule),
			"a documented unreachable divergence stays visible: %s" % label
		)


func _apply_step(world: Prototype, victim: UnitState, kind: String, step: Dictionary) -> bool:
	var amount := float(step.get("amount", 0.0))
	var duration := int(step.get("duration", 0))
	match kind:
		"slow":
			return world.apply_slow(victim.id, amount, duration)
		"atk_slow":
			return world.apply_atk_slow(victim.id, amount, duration)
		"skill_down":
			return world.apply_skill_down(victim.id, amount, duration)
		"anti_heal":
			return world.apply_anti_heal(victim.id, amount, duration)
		"burn":
			return world.apply_burn(victim.id, amount, duration, int(step.get("team", 0)))
	return false


func _reset_store(victim: UnitState) -> void:
	# The fixture's native column starts from "nothing stored"; `burn_team` -1 is
	# the source's `burn_team or self.team` fallback with no team credited yet.
	victim.slow_amount = 0.0
	victim.slow_timer = 0
	victim.atk_slow_amount = 0.0
	victim.atk_slow_timer = 0
	victim.skill_down_amount = 0.0
	victim.skill_down_timer = 0
	victim.anti_heal_amount = 0.0
	victim.anti_heal_timer = 0
	victim.burn_dps = 0.0
	victim.burn_timer = 0
	victim.burn_team = -1


func _store_matches(victim: UnitState, kind: String, column: Dictionary) -> bool:
	if kind == "burn":
		return (
			is_equal_approx(victim.burn_dps, float(column.get("dps", -1.0)))
			and victim.burn_timer == int(column.get("timer", -1))
			and victim.burn_team == int(column.get("team", -2))
		)
	var fields: Array = FIELDS.get(kind, [])
	if fields.size() != 2:
		return false
	return (
		is_equal_approx(victim.get(String(fields[0])), float(column.get("amount", -1.0)))
		and int(victim.get(String(fields[1]))) == int(column.get("timer", -1))
	)


func _same_counts(actual: Dictionary, expected: Dictionary) -> bool:
	if actual.size() != expected.size():
		return false
	for key in expected:
		if not actual.has(key) or int(actual[key]) != int(expected[key]):
			return false
	return true
