# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8g native suite: Boss debuff clocks, burn damage, and hp heal modifiers.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/boss_debuff_clock_source.json"

const COMPARE_FIELDS := [
	"slow_amount",
	"slow_timer",
	"atk_slow_amount",
	"atk_slow_timer",
	"skill_down_amount",
	"skill_down_timer",
	"anti_heal_amount",
	"anti_heal_timer",
	"stun_timer",
	"armor_shred_amount",
	"armor_shred_timer",
	"dmg_amp_amount",
	"dmg_amp_timer",
	"heal_amp_amount",
	"heal_amp_timer",
	"blind_amount",
	"blind_timer",
	"burn_dps",
	"burn_timer",
	"burn_accum",
	"burn_tick_cd"
]
const FLOAT_FIELDS := [
	"slow_amount",
	"atk_slow_amount",
	"skill_down_amount",
	"anti_heal_amount",
	"armor_shred_amount",
	"dmg_amp_amount",
	"heal_amp_amount",
	"blind_amount",
	"burn_dps",
	"burn_accum"
]


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		fixture is Dictionary and fixture.has("cases") and fixture.has("hp_writes"),
		"boss debuff clock fixture parses"
	)
	if not fixture is Dictionary:
		return
	var world := Prototype.new()
	world.setup_arena()
	for entry in fixture.cases:
		_replay_case(check, world, entry)
	for entry in fixture.hp_writes:
		_replay_hp_write(check, world, entry)
	_match_tick_order(check, world)
	_burn_damage_and_retirement(check)
	_unit_burn_attribution(check)
	_boss_heal_paths(check)


func _replay_case(check: Callable, world: Prototype, entry: Dictionary) -> void:
	var label := String(entry.get("label", "unknown"))
	var boss := _boss(world, "gornak")
	var input: Dictionary = entry.get("input", {})
	_apply_state(boss, input)
	var damage_ticks: Array[int] = []
	var damage_teams: Array[int] = []
	for _tick in range(int(entry.get("ticks", 1))):
		var burn_from_team := boss.burn_source_team()
		var burn_damage: int = boss.tick_tower_debuffs()
		if burn_damage > 0:
			damage_ticks.append(burn_damage)
			damage_teams.append(burn_from_team)
	var result: Dictionary = entry.get("result", {})
	var expected_state: Dictionary = result.get("state", {})
	for field in COMPARE_FIELDS:
		var actual: Variant = boss.get(field)
		var expected: Variant = expected_state.get(field)
		var matches: bool = false
		if String(field) in FLOAT_FIELDS:
			matches = is_equal_approx(float(actual), float(expected))
		else:
			matches = actual == expected
		check.call(matches, "boss debuff clock parity: %s (%s)" % [label, String(field)])
	var expected_damage: Array[int] = []
	var expected_teams: Array[int] = []
	for damage_call in result.get("damage_calls", []):
		expected_damage.append(int(damage_call.get("damage", 0)))
		expected_teams.append(_source_team_code(String(damage_call.get("from_team", ""))))
	check.call(
		damage_ticks == expected_damage, "boss debuff burn tick payload matches source: %s" % label
	)
	check.call(
		damage_teams == expected_teams,
		"boss debuff burn team attribution matches source: %s" % label
	)


func _replay_hp_write(check: Callable, world: Prototype, entry: Dictionary) -> void:
	var boss := _boss(world, "gornak")
	boss.hp = float(entry.get("previous", 0.0))
	boss.anti_heal_amount = float(entry.get("anti_heal", 0.0))
	boss.anti_heal_timer = int(entry.get("anti_heal_timer", 0))
	boss.heal_amp_amount = float(entry.get("heal_amp", 0.0))
	boss.heal_amp_timer = int(entry.get("heal_amp_timer", 0))
	boss.set_hp_value(float(entry.get("requested", 0.0)))
	check.call(
		is_equal_approx(boss.hp, float(entry.get("result", 0.0))),
		"boss hp setter parity: %s" % String(entry.get("label", "unknown"))
	)


func _match_tick_order(check: Callable, world: Prototype) -> void:
	var boss := world._spawn_boss("gornak")
	check.call(boss != null, "boss debuff integration boss spawns")
	if boss == null:
		return
	boss.entrance_timer = 1
	boss.stun_timer = 1
	boss.slow_amount = 0.3
	boss.slow_timer = 1
	boss.blind_amount = 0.2
	boss.blind_timer = 2
	boss.burn_dps = 60.0
	boss.burn_timer = 2
	boss.burn_accum = 0.0
	boss.burn_tick_cd = 1
	var hp_before := boss.hp
	world._step_active_boss()
	check.call(
		boss.stun_timer == 0 and boss.slow_timer == 0 and boss.slow_amount == 0.0,
		"Boss debuffs tick before stun and entrance gates"
	)
	check.call(
		boss.entrance_timer == 0 and boss.basic_attack_seq == 0,
		"last entrance tick still gates boss movement and attack"
	)
	check.call(is_equal_approx(boss.hp, hp_before - 1.0), "boss burn uses native damage mitigation")
	check.call(
		boss.last_damage_from_team == world.RED,
		"boss burn without a source team falls back to the boss team"
	)
	check.call(
		boss.burn_timer == 1 and boss.burn_tick_cd == 30 and boss.blind_timer == 1,
		"boss burn and item-debuff clocks advance once before gates"
	)
	world._tick_item_debuffs()
	check.call(boss.blind_timer == 1, "global item-debuff pass does not tick BossState twice")


func _burn_damage_and_retirement(check: Callable) -> void:
	var world := _world()
	var boss := world._spawn_boss("gornak")
	check.call(boss != null, "burn death probe boss spawns")
	if boss == null:
		return
	boss.hp = 1.0
	boss.entrance_timer = 1
	boss.burn_dps = 60.0
	boss.burn_timer = 2
	boss.burn_tick_cd = 1
	boss.burn_team = world.BLUE
	world._step_active_boss()
	check.call(not boss.alive and boss.defeated, "burn can defeat an active boss")
	check.call(
		boss.last_damage_from_team == world.BLUE,
		"lethal boss burn retains its attacking team's attribution"
	)
	check.call(
		world.boss_death_presentations.size() == 1,
		"burn defeat queues the existing boss death snapshot once"
	)
	world._process_boss_result()
	check.call(
		world.active_boss == null and world.boss_rewards.size() == 1,
		"burn defeat retires boss and commits one source reward"
	)


func _unit_burn_attribution(check: Callable) -> void:
	var world := _world()
	var victim := world.spawn_unit(GOBLIN, world.BLUE, 1)
	check.call(victim != null, "unit burn attribution victim spawns")
	if victim == null:
		return
	victim.hp = 1.0
	check.call(
		world.apply_burn(victim.id, 60.0, 30, world.BLUE),
		"same-team unit burn can be assigned without target-team filtering"
	)
	victim.burn_tick_cd = 1
	world._tick_burn(victim)
	check.call(not victim.alive, "unit burn applies its lethal tick")
	check.call(
		world.kills[world.BLUE] == 1 and world.kills[world.RED] == 0,
		"unit burn death is credited to burn_team rather than inferred enemy team"
	)


func _boss_heal_paths(check: Callable) -> void:
	var world := _world()
	var boss := world._spawn_boss("abaddon")
	check.call(boss != null, "true-boss anti-heal probe spawns")
	if boss == null:
		return
	boss.hp = float(boss.max_hp) * 0.2
	boss.anti_heal_amount = 0.5
	boss.anti_heal_timer = 10
	boss.ability2_timer = 0
	var before := boss.hp
	var raw_heal := int(float(boss.max_hp) * boss.ability2_heal_pct)
	BossAI._heal_ability_if_ready(boss)
	check.call(
		is_equal_approx(boss.hp, before + float(raw_heal) * 0.5),
		"true-boss heal is reduced by active anti-heal"
	)
	var before_skill_heal := boss.hp
	BossAI._heal(boss, 0.1)
	check.call(
		is_equal_approx(boss.hp, before_skill_heal + float(int(float(boss.max_hp) * 0.1)) * 0.5),
		"smart-AI heal helper honors anti-heal"
	)


func _source_team_code(team: String) -> int:
	if team == "blue":
		return 0
	if team == "red":
		return 1
	return -1


func _world() -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	return world


func _boss(world: Prototype, kind: String) -> BossState:
	var boss := BossState.new()
	boss.setup(kind, PackedVector2Array(), world.boss_table)
	return boss


func _apply_state(boss: BossState, state: Dictionary) -> void:
	boss.hp = float(state.get("hp", 100000.0))
	for field in state:
		if field == "hp":
			continue
		if field == "burn_team":
			var source_team: Variant = state[field]
			boss.burn_team = -1
			if source_team == "blue":
				boss.burn_team = 0
			elif source_team == "red":
				boss.burn_team = 1
			continue
		boss.set(String(field), state[field])
