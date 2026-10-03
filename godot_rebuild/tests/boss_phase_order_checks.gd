# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8o: source Game.update runs living heroes before Boss.update. The
## source fixture keeps the resulting lethal/nonlethal and movement handoffs
## for four cases across every boss type; this suite replays those cases with
## the native live hero and BossState phases.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/boss_phase_order_source.json"
const BOSS_POSITION := Vector2(600.0, 300.0)
const PARKED := Vector2(5000.0, 5000.0)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("cases"), "boss phase order fixture parses")
	if not fixture is Dictionary or not fixture.has("cases"):
		return
	var source: Dictionary = fixture.get("source", {})
	check.call(
		(
			source.get("game_update_order", []) == ["heroes", "boss"]
			and source.get("speed_multiplier_update_order", []) == ["heroes", "boss"]
			and bool(source.get("boss_update_skips_dead", false))
		),
		"source hero and boss phase ordering is pinned for both Game update paths"
	)
	check.call(
		(
			float(source.get("boss_target_radius_add", -1.0)) == 100.0
			and bool(source.get("boss_target_radius_is_strict", false))
			and bool(source.get("boss_attack_range_is_inclusive", false))
		),
		"source boss target and attack boundaries are pinned for phase cases"
	)
	_replay_cases(check, fixture)


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "boss phase order has four source cases for all 216 boss types")
	var world := Prototype.new()
	world.setup_arena()
	for structure in world.structures:
		structure.position = PARKED
	for unit in world.units:
		world._by_id.erase(unit.id)
	world.units.clear()
	var hero: HeroState = world.spawn_hero(KAIZEN, world.BLUE, BOSS_POSITION)
	check.call(hero != null, "boss phase order live blue hero spawns")
	if hero == null:
		return

	var boss_counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		if world.active_boss != null:
			world._by_id.erase(world.active_boss.id)
			world.active_boss = null
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss phase order boss loads: %s" % boss_type)
		if boss == null:
			continue
		boss.team = world.RED
		boss.position = BOSS_POSITION
		boss.previous_position = BOSS_POSITION
		boss.attack_range = float(entry.get("boss_range", 80.0))
		boss.entrance_timer = 0
		boss.stun_timer = 0
		boss.timer = 0
		boss.ability_timer = 10000
		boss.ability2_timer = 10000
		boss.ability_active_timer = 0
		boss.attack_lock_timer = 0
		boss.basic_attack_seq = 0
		boss.target_id = -1
		boss.last_hit_source_id = -1
		boss.hp = 1.0 if String(entry.get("boss_hp_mode", "full")) == "one" else boss.max_hp

		hero.alive = true
		hero.hp = hero.max_hp
		hero.position = BOSS_POSITION + Vector2(float(entry.get("hero_start_dx", 0.0)), 0.0)
		hero.speed = float(entry.get("hero_speed", 0.0))
		hero.damage = int(entry.get("hero_damage", 0))
		hero.attack_timer = int(entry.get("hero_attack_timer", 0))
		hero.attack_seq = 0
		hero.auto_cast_enabled = false
		hero.is_retreating = false
		hero.follow_id = -1
		hero.has_destination = String(entry.get("hero_action", "")) in ["move_in", "move_out"]
		hero.destination_auto = false
		hero.destination = BOSS_POSITION + Vector2(float(entry.get("hero_end_dx", 0.0)), 0.0)
		hero.target_id = -1
		hero.target_struct = null
		hero.stun_timer = 0
		hero.slow_timer = 0
		hero.slow_amount = 0.0

		# These are the production match phases whose call order is fixed in
		# Prototype.step_tick and checked by validate_project.py.
		world._step_hero_act()
		world._step_active_boss()
		var expected_alive := bool(entry.get("expected_boss_alive", true))
		var expected_attacks := int(entry.get("expected_boss_attacks", -1))
		var expected_target := String(entry.get("expected_target", "none"))
		var expected_action := String(entry.get("expected_boss_action", ""))
		var actual_action := "skip_dead" if not boss.alive else "no_target"
		if boss.alive and boss.target_id == hero.id and boss.basic_attack_seq > 0:
			actual_action = "attack"
		elif boss.alive and boss.target_id == hero.id:
			actual_action = "chase"
		check.call(
			boss.alive == expected_alive and boss.basic_attack_seq == expected_attacks,
			"boss phase order alive/attack result matches source: %s (%s)" % [label, boss_type]
		)
		check.call(
			(
				(
					actual_action == "skip_dead"
					if expected_target == "none" and not expected_alive
					else true
				)
				and (boss.target_id == hero.id if expected_target == "hero" else boss.target_id < 0)
				and actual_action == expected_action
			),
			"boss phase order observes the hero's post-update state: %s (%s)" % [label, boss_type]
		)
		check.call(
			is_equal_approx(
				hero.position.x - BOSS_POSITION.x,
				float(entry.get("expected_hero_dx_after_update", 0.0))
			),
			"boss phase case hero position matches source order: %s (%s)" % [label, boss_type]
		)
		if String(entry.get("hero_action", "")) in ["lethal_hit", "nonlethal_hit"]:
			check.call(
				boss.last_hit_source_id == hero.id,
				"hero hit resolves before the source boss phase: %s (%s)" % [label, boss_type]
			)
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 4,
			"boss phase order has exactly four cases for %s" % boss_type
		)
