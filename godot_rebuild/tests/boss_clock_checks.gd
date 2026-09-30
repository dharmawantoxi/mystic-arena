# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8e native suite: source entrance gate, animation clocks, one-shot
## mini/true enrage transition and enraged cooldown pulse.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const FIXTURE := "res://tests/fixtures/boss_clock_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("cases"), "boss clock fixture parses")
	if not fixture is Dictionary:
		return
	var cases: Array = fixture.cases
	_replay(check, cases, "mini_entrance", "gornak", 10000.0, 2, 0)
	_replay(check, cases, "mini_entrance_release", "gornak", 10000.0, 1, 0)
	_replay(check, cases, "mini_enrage_odd", "gornak", 4000.0, 0, 0)
	_replay(check, cases, "mini_enrage_slow", "gornak", 4000.0, 0, 0, 0.50)
	_replay(check, cases, "true_enrage_even", "abaddon", 5000.0, 0, 1)
	_replay_twice(check, cases, "mini_enrage_once", "gornak", 4000.0)
	_prototype_entrance_gate(check)


func _prototype_entrance_gate(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss("gornak")
	check.call(boss != null, "prototype clock boss spawns")
	if boss == null:
		return
	boss.entrance_timer = 2
	boss.timer = 0
	boss.position = Vector2(300, 500)
	boss.previous_position = boss.position
	boss.attack_range = 10000.0
	var before := boss.position
	world._step_active_boss()
	check.call(
		boss.entrance_timer == 1 and boss.basic_attack_seq == 0 and boss.position == before,
		"prototype entrance gate blocks movement and basic attack"
	)
	world._step_active_boss()
	check.call(
		boss.entrance_timer == 0 and boss.basic_attack_seq == 0,
		"prototype entrance gate releases only after the final entrance tick"
	)


func _boss(
	kind: String, hp_value: float, entrance: int, anim: int, slow_amount: float = 0.0
) -> BossState:
	var boss := BossState.new()
	var table := {
		"bosses":
		{
			kind:
			{
				"boss_class": "true" if kind == "abaddon" else "mini",
				"name": kind,
				"title": "clock",
				"max_hp": 10000,
				"damage": 100,
				"speed": 10.0,
				"attack_range": 50,
				"attack_cooldown": 30,
				"radius": 30,
				"gold_reward": 0,
				"ability_cooldown": 10,
				"ability_damage": 25,
				"ability_range": 50,
				"ability2_cooldown": 20,
				"ability2_heal_pct": 0.1,
				"armor": 0,
				"magic_resist": 0.0,
				"resist_profile": "balanced",
				"damage_reduction": 0.0,
				"max_damage_per_hit": 1000,
				"entrance_ticks": entrance,
				"entrance_text": "",
				"color": [0, 0, 0],
				"color_dark": [0, 0, 0],
				"entrance_color": [0, 0, 0]
			}
		},
		"rules":
		{
			"max_damage_per_hit_pct": {"mini": 0.12, "true": 0.08},
			"tenacity": 0.5,
			"cleave_radius": 80,
			"cleave_ratio": 0.4
		}
	}
	boss.setup(kind, PackedVector2Array(), table)
	boss.max_hp = 10000
	boss.hp = hp_value
	boss.speed_px_per_tick = 10.0
	boss.damage = 100
	boss.attack_cooldown = 30
	boss.entrance_timer = entrance
	boss.anim_time = anim
	boss.slow_amount = slow_amount
	boss.slow_timer = 1 if slow_amount > 0.0 else 0
	boss.hurt_flash_timer = 2
	boss.timer = 5
	boss.ability_timer = 7
	boss.ability2_timer = 9
	boss.ability_active = true
	boss.ability_active_timer = 4
	return boss


func _tick(boss: BossState) -> void:
	boss.advance_animation_clock()
	boss.begin_motion_tick()
	if boss.stun_timer > 0:
		return
	if not boss.advance_combat_clock():
		return
	boss.timer = maxi(0, boss.timer - 1)
	if boss.ability_timer > 0:
		boss.ability_timer -= 1
	if boss.ability2_timer > 0:
		boss.ability2_timer -= 1
	if boss.ability_active_timer > 0:
		boss.ability_active_timer -= 1
		if boss.ability_active_timer <= 0:
			boss.ability_active = false


func _fixture_case(cases: Array, label: String) -> Dictionary:
	for entry in cases:
		if String(entry.get("label", "")) == label:
			return entry.get("result", {})
	return {}


func _row(boss: BossState) -> Dictionary:
	return {
		"anim_time": boss.anim_time,
		"pulse": boss.pulse,
		"entrance_timer": boss.entrance_timer,
		"hurt_flash_timer": boss.hurt_flash_timer,
		"timer": boss.timer,
		"ability_timer": boss.ability_timer,
		"ability2_timer": boss.ability2_timer,
		"ability_active": boss.ability_active,
		"ability_active_timer": boss.ability_active_timer,
		"speed": boss.eff_speed(),
		"damage": boss.damage,
		"attack_cooldown": boss.attack_cooldown,
		"enrage_triggered": boss.enrage_triggered,
		"is_enraged": boss.is_enraged,
		"enrage_pulse": boss.enrage_pulse
	}


func _replay(
	check: Callable,
	cases: Array,
	label: String,
	kind: String,
	hp_value: float,
	entrance: int,
	anim: int,
	slow_amount: float = 0.0
) -> void:
	var boss := _boss(kind, hp_value, entrance, anim, slow_amount)
	_tick(boss)
	_compare_row(check, label, _row(boss), _fixture_case(cases, label))


func _replay_twice(
	check: Callable, cases: Array, label: String, kind: String, hp_value: float
) -> void:
	var boss := _boss(kind, hp_value, 0, 0)
	_tick(boss)
	_tick(boss)
	_compare_row(check, label, _row(boss), _fixture_case(cases, label))


func _compare_row(check: Callable, label: String, actual: Dictionary, expected: Dictionary) -> void:
	for key in expected:
		if actual.get(key) != expected.get(key):
			check.call(
				false,
				(
					"native clock parity: %s (%s actual=%s expected=%s)"
					% [label, String(key), str(actual.get(key)), str(expected.get(key))]
				)
			)
			return
	check.call(true, "native clock parity: %s" % label)
