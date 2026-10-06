extends RefCounted
## Production match replay: AI hero control is dispatched once per world tick.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/ai_control_tick_source.json"


class ControlSpy:
	extends RefCounted
	var calls := 0

	func control_heroes(_world: Object, _towers: Array) -> void:
		calls += 1


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var source: Dictionary = fixture.get("source", {})
	var cases: Array = fixture.get("cases", [])
	check.call(
		int(source.get("ai_player_update_control_calls", 0)) == 1,
		"Python AIPlayer.update controls heroes once"
	)
	check.call(
		int(source.get("game_update_ai_calls", 0)) == 1,
		"Python Game.update dispatches AIPlayer.update once"
	)
	check.call(cases.size() == 2, "AI control replay covers wait and think-expiry ticks")
	for row: Dictionary in cases:
		var world := Prototype.new()
		check.call(world.setup_arena(), "Production world initializes for AI tick replay")
		world.economy.gold[world.RED] = 0
		var spy := ControlSpy.new()
		world.ai_heroes = spy
		world.set_ai_enabled(true)
		world.ai_controller.policy.think_timer = int(row.think_timer_before)
		world.step_tick()
		var expected: Dictionary = row.expected
		var native_old: Dictionary = row.native_old
		var label := String(row.scenario)
		check.call(
			spy.calls == int(expected.control_calls),
			"Production step_tick dispatches AI hero control once: " + label
		)
		check.call(
			spy.calls != int(native_old.control_calls),
			"Production replay diverges from the duplicate pre-slice dispatch: " + label
		)
		check.call(world.ai_controller.ticks == 1, "AI scheduler advances once: " + label)
		check.call(
			world.ai_controller.policy.think_timer == int(expected.think_timer_after),
			"AI scheduler clock remains source-aligned: " + label
		)

	# Preserve the separate control-only seam used by callers that deliberately
	# enable hero control without enabling scheduled economy actions.
	var control_only_world := Prototype.new()
	check.call(control_only_world.setup_arena(), "Control-only world initializes")
	var control_only_spy := ControlSpy.new()
	control_only_world.ai_heroes = control_only_spy
	control_only_world.ai_hero_control_enabled = true
	control_only_world.step_tick()
	check.call(
		control_only_spy.calls == 1,
		"Standalone AI hero control still runs once when the controller is disabled"
	)
