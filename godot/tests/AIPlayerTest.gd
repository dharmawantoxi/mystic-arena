# Headless regression for AIPlayer compilation, minion lanes, and lane targeting.
# Run after importing the project:
# godot --headless --path godot res://tests/AIPlayerTest.tscn --quit-after 120
# Success requires the PASS line below and no SCRIPT ERROR / Parse Error logs.
extends Node

const MainScene = preload("res://scenes/main.tscn")
const AIPlayerScript = preload("res://scripts/systems/AIPlayer.gd")

var _failures: int = 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	# Stay in the menu: no combat frames, level progression, or save writes.
	GameManager.in_menu = true
	GameManager.state = "idle"
	var main = MainScene.instantiate()
	add_child(main)
	var ai = main.get("_ai")
	_expect(is_instance_valid(ai), "Main._ready must instantiate AIPlayer")
	if not is_instance_valid(ai):
		main.free()
		get_tree().quit(1)
		return
	_expect(ai.get_script() == AIPlayerScript, "Main must use the AIPlayer script")

	_test_spawn_lanes(main)
	var hero = GameManager.spawn_hero("grimjaw", "red", Vector2(1000, 380))
	ai._assign_hero_lane(hero)
	_expect(not hero.has_destination(), "Empty battlefield must leave the hero idle")
	for lane in ["top", "mid", "bot"]:
		_test_lane_targeting(ai, hero, lane)

	# With no lane threats, keep the existing nearest-blue-tower fallback.
	GameManager.spawn_tower("blue", Vector2(100, 380))
	GameManager.spawn_tower("blue", Vector2(500, 380))
	GameManager.spawn_tower("red", Vector2(990, 380))
	hero.clear_destination()
	ai._assign_hero_lane(hero)
	_expect(hero.destination == Vector2(560, 380), "Stop 60px from the nearest blue tower")
	_expect(hero.destination_auto, "Tower fallback must remain an automatic destination")

	main.free()
	if _failures == 0:
		print("[AIPlayerTest] PASS: startup, spawn lanes, and lane targeting")
	get_tree().quit(0 if _failures == 0 else 1)


func _test_spawn_lanes(main) -> void:
	# Existing callers keep the fourth positional argument as the stat multiplier.
	var minion = GameManager.spawn_minion("goblin", "blue", Vector2.ZERO, 2.0)
	_expect(str(minion.get("lane")) == "mid", "Default minion lane must be mid")
	_expect(float(minion.get("stat_scale")) == 2.0, "Stat multiplier must remain compatible")
	minion.free()

	main._on_wave_started(1)
	var expected_lanes := ["mid", "top", "bot"]
	var counts := {"blue": 0, "red": 0}
	for m in get_tree().get_nodes_in_group("minions"):
		var team := str(m.get("team"))
		var index := int(counts[team])
		_expect(str(m.get("lane")) == expected_lanes[index % expected_lanes.size()],
			"Wave must preserve the spawn lane for %s minion %d" % [team, index])
		counts[team] = index + 1
	for team in counts:
		_expect(int(counts[team]) == GameManager.wave_composition(1).size(),
			"Wave must spawn the full %s roster" % team)
	_clear_minions()


func _test_lane_targeting(ai, hero, lane: String) -> void:
	var y := float(AIPlayerScript.LANE_Y[lane])
	var other_lane := "mid" if lane == "top" else "top"
	_spawn_minion(lane, Vector2(200, y))
	var nearest := _spawn_minion(lane, Vector2(700, y))
	# A closer enemy in a quieter lane must not override the busiest lane.
	_spawn_minion(other_lane, Vector2(990, 380))
	# Allies and dead enemies must not inflate the other lane's threat count.
	for i in range(3):
		_spawn_minion(other_lane, Vector2(900 + i, 380), "red")
		_spawn_minion(other_lane, Vector2(950 + i, 380)).set("is_dead", true)
	# Nor may closer allies/dead enemies become the destination in the chosen lane.
	_spawn_minion(lane, Vector2(990, y), "red")
	_spawn_minion(lane, Vector2(980, y)).set("is_dead", true)
	_spawn_minion("unknown", Vector2(995, 380))
	hero.clear_destination()
	ai._assign_hero_lane(hero)
	_expect(hero.destination == nearest.global_position,
		"Must choose the nearest live blue minion in the busiest lane: %s" % lane)
	_expect(hero.destination_auto, "Lane assignment must remain automatic")
	_clear_minions()


func _spawn_minion(lane: String, pos: Vector2, team: String = "blue") -> Node2D:
	return GameManager.spawn_minion("goblin", team, pos, 1.0, lane)


func _clear_minions() -> void:
	for minion in get_tree().get_nodes_in_group("minions"):
		minion.free()


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error("[AIPlayerTest] " + message)
