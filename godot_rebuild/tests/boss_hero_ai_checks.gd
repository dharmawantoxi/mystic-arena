extends RefCounted
## Source-oracle checks for boss-hero auto-cast target handoff.

const AiHeroControl = preload("res://scripts/match/ai_hero_control.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const GORNAK = preload("res://data/heroes/gornak.tres")
const FIXTURE := "res://tests/fixtures/boss_hero_ai_source.json"


class _Target:
	extends RefCounted
	var id := -1
	var team := 0
	var alive := true
	var is_hero := false
	var lane := -1
	var position := Vector2.ZERO


class _World:
	extends RefCounted
	var units: Array = []
	var towers: Array = []
	var nexuses: Array = []
	var active_boss: Object = null
	var auto_casts := 0
	var moves: Array = []

	func try_auto_cast(_hero: HeroState) -> void:
		auto_casts += 1

	func move_to(hero: HeroState, point: Vector2, auto: bool) -> void:
		hero.has_destination = true
		hero.destination = point
		hero.destination_auto = auto
		moves.append({"hero_id": hero.id, "point": point, "auto": auto})


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		fixture is Dictionary and fixture.get("boss_type") == "gornak" and fixture.has("cases"),
		"boss-hero target fixture parses"
	)
	if not fixture is Dictionary:
		return
	for row in fixture.cases:
		_replay_case(row, check)
	_starter_hero_unchanged(check)


func _replay_case(row: Dictionary, check: Callable) -> void:
	var input: Dictionary = row.get("input", {})
	var hero_spec: Dictionary = input.get("hero", {})
	var world := _World.new()
	var hero := HeroState.new()
	hero.id = int(hero_spec.get("id", 1))
	hero.team = 1
	hero.definition = GORNAK
	hero.alive = true
	hero.skill_timer = 0
	hero.position = Vector2(float(hero_spec.get("x", 0.0)), float(hero_spec.get("y", 0.0)))
	hero.skill_range = float(hero_spec.get("skill_range", 0.0))
	var initial_target: Variant = hero_spec.get("initial_target_id")
	hero.target_id = -1 if initial_target == null else int(initial_target)
	world.units.append(hero)
	for unit_spec in input.get("units", []):
		world.units.append(_target(unit_spec))
	var boss_spec: Variant = input.get("active_boss")
	if boss_spec is Dictionary:
		world.active_boss = _target(boss_spec)
	for tower_spec in input.get("towers", []):
		world.towers.append(_target(tower_spec))
	for base_spec in input.get("bases", []):
		world.nexuses.append(_target(base_spec))
	var control := AiHeroControl.new()
	control.control_heroes(world, world.towers)
	var expected: Variant = row.get("target_id")
	var expected_id := -1 if expected == null else int(expected)
	var label := String(row.get("label", "unknown"))
	check.call(hero.target_id == expected_id, "Gornak target matches source: %s" % label)
	check.call(world.auto_casts == 1, "Gornak auto-cast controller runs once: %s" % label)
	var expect_lane := bool(input.get("expects_lane_assignment", false))
	check.call(
		hero.has_destination == expect_lane,
		"Gornak lane handoff matches source target presence: %s" % label
	)
	if expect_lane:
		var move: Dictionary = world.moves.back()
		var lane_unit: Dictionary = input.units[0]
		check.call(
			(
				is_equal_approx(float(move.point.x), float(lane_unit.x))
				and is_equal_approx(float(move.point.y), 380.0)
			),
			"Gornak lane order follows the threatened lane: %s" % label
		)


func _target(spec: Dictionary) -> _Target:
	var result := _Target.new()
	result.id = int(spec.get("id", -1))
	result.team = 0 if String(spec.get("team", "blue")) == "blue" else 1
	result.alive = bool(spec.get("alive", true))
	result.lane = int(spec.get("lane", -1))
	result.position = Vector2(float(spec.get("x", 0.0)), float(spec.get("y", 0.0)))
	return result


func _starter_hero_unchanged(check: Callable) -> void:
	var world := _World.new()
	var starter := HeroState.new()
	starter.id = 100
	starter.team = 1
	starter.definition = preload("res://data/heroes/kaizen.tres")
	starter.position = Vector2(0, 0)
	starter.skill_range = 100.0
	world.units.append(starter)
	var enemy := _Target.new()
	enemy.id = 101
	enemy.team = 0
	enemy.position = Vector2(20, 0)
	world.units.append(enemy)
	AiHeroControl.new().control_heroes(world, world.towers)
	check.call(starter.target_id == -1, "Starter hero behavior stays out of the boss-only handoff")
