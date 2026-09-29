# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8a native suite: Boss entity core against the source oracle fixture.
## Entity-only checks; the match spawn/schedule wiring is a later layer.

const BossState = preload("res://scripts/match/boss_state.gd")
const LaneLayout = preload("res://scripts/data/lane_layout.gd")
const FIXTURE := "res://tests/fixtures/boss_core_source.json"
const DATA := "res://data/bosses/boss_stats.json"


class BlindStub:
	extends RefCounted
	var team := 1
	var alive := true
	var blind_timer := 0
	var blind_amount := 0.0
	var items: Variant = null


class InventoryStub:
	extends RefCounted
	var true_strike := false

	func has_true_strike() -> bool:
		return true_strike


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var table = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	check.call(fixture is Dictionary and table is Dictionary, "boss core fixtures parse")
	if not fixture is Dictionary or not table is Dictionary:
		return
	check.call(table == fixture["data"], "boss stats data equals the source fixture")
	_rows(check, fixture, table)
	_positions(check, fixture, table)
	_scaling(check, fixture, table)
	_debuffs(check, fixture, table)
	_damage(check, fixture, table)
	_blind(check, fixture, table)
	_defeat(check, fixture, table)


func _boss_of(boss_type: String, table: Dictionary, lane_path: PackedVector2Array) -> BossState:
	var boss := BossState.new()
	var ok := boss.setup(boss_type, lane_path, table)
	return boss if ok else null


func _mid() -> PackedVector2Array:
	return LaneLayout.create_paths()[1]


func _rows(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var rows: Dictionary = fixture["data"]["bosses"]
	var mid := _mid()
	var seen := 0
	for boss_type in rows:
		var row: Dictionary = rows[boss_type]
		var boss := _boss_of(boss_type, table, mid)
		check.call(boss != null, "boss %s constructs" % boss_type)
		if boss == null:
			continue
		seen += 1
		check.call(
			boss.display_name == row["name"] and boss.title == row["title"],
			"boss %s identity" % boss_type
		)
		check.call(boss.boss_class == row["boss_class"], "boss %s class" % boss_type)
		check.call(
			boss.max_hp == int(row["max_hp"]) and boss.hp == float(row["max_hp"]),
			"boss %s max hp" % boss_type
		)
		check.call(
			boss.damage == int(row["damage"]) and boss.base_damage == int(row["damage"]),
			"boss %s damage" % boss_type
		)
		check.call(
			(
				is_equal_approx(boss.speed_px_per_tick, float(row["speed"]))
				and is_equal_approx(boss.eff_speed(), float(row["speed"]))
			),
			"boss %s speed" % boss_type
		)
		check.call(
			(
				boss.attack_range == float(row["attack_range"])
				and boss.attack_cooldown == int(row["attack_cooldown"])
			),
			"boss %s attack profile" % boss_type
		)
		check.call(
			boss.radius == float(row["radius"]) and boss.gold_reward == int(row["gold_reward"]),
			"boss %s reward and radius" % boss_type
		)
		check.call(
			(
				boss.ability_cooldown == int(row["ability_cooldown"])
				and boss.ability_damage_value == int(row["ability_damage"])
				and boss.ability_range == float(row["ability_range"])
			),
			"boss %s ability stats" % boss_type
		)
		check.call(
			(
				boss.ability2_cooldown == int(row["ability2_cooldown"])
				and is_equal_approx(boss.ability2_heal_pct, float(row["ability2_heal_pct"]))
			),
			"boss %s true-boss ability" % boss_type
		)
		check.call(
			(
				boss.armor == int(row["armor"])
				and is_equal_approx(boss.magic_resist, float(row["magic_resist"]))
				and boss.resist_profile == row["resist_profile"]
			),
			"boss %s resistances" % boss_type
		)
		check.call(
			(
				is_equal_approx(boss.damage_reduction, float(row["damage_reduction"]))
				and boss.max_damage_per_hit == int(row["max_damage_per_hit"])
			),
			"boss %s resilience and burst cap" % boss_type
		)
		check.call(
			(
				boss.entrance_ticks == int(row["entrance_ticks"])
				and boss.entrance_timer == int(row["entrance_ticks"])
				and boss.entrance_text == row["entrance_text"]
			),
			"boss %s entrance" % boss_type
		)
		check.call(
			(
				boss.color.r8 == int(row["color"][0])
				and boss.color.g8 == int(row["color"][1])
				and boss.color.b8 == int(row["color"][2])
			),
			"boss %s color" % boss_type
		)
		check.call(
			(
				boss.color_dark.r8 == int(row["color_dark"][0])
				and boss.entrance_color.r8 == int(row["entrance_color"][0])
			),
			"boss %s palette" % boss_type
		)
		check.call(
			boss.team == 1 and boss.alive and not boss.defeated and boss.direction == -1,
			"boss %s starts red and alive" % boss_type
		)
		check.call(
			(
				boss.definition.max_hp == boss.max_hp
				and boss.definition.damage == boss.damage
				and is_equal_approx(boss.definition.armor, float(boss.armor))
				and boss.definition.gold_reward == boss.gold_reward
			),
			"boss %s definition mirrors stats" % boss_type
		)
	check.call(seen == 216, "all 216 source boss types construct")


func _positions(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var mid := _mid()
	for boss_type in fixture["positions"]:
		var row: Dictionary = fixture["positions"][boss_type]
		var boss := _boss_of(boss_type, table, mid)
		var fallback := _boss_of(boss_type, table, PackedVector2Array())
		check.call(boss != null and fallback != null, "boss %s position cases" % boss_type)
		if boss == null or fallback == null:
			continue
		check.call(
			(
				boss.position == Vector2(float(row["path"][0]), float(row["path"][1]))
				and boss.waypoint_index == int(row["waypoint_index"])
				and boss.direction == int(row["direction"])
			),
			"boss %s mid-lane anchor" % boss_type
		)
		check.call(
			(
				fallback.position == Vector2(float(row["fallback"][0]), float(row["fallback"][1]))
				and fallback.waypoint_index == int(row["fallback_waypoint_index"])
			),
			"boss %s fallback anchor" % boss_type
		)


func _scaling(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var mid := _mid()
	for case in fixture["scaling"]:
		var boss := _boss_of(case["type"], table, mid)
		check.call(boss != null, "scaling case %s" % case["type"])
		if boss == null:
			continue
		boss.apply_scaling(float(case["hp_mult"]), float(case["dmg_mult"]), float(case["spd_mult"]))
		check.call(
			boss.max_hp == int(case["max_hp"]) and boss.hp == float(case["hp"]),
			"scaled %s hp" % case["type"]
		)
		check.call(
			boss.damage == int(case["damage"]) and boss.base_damage == int(case["base_damage"]),
			"scaled %s damage" % case["type"]
		)
		check.call(
			boss.ability_damage_value == int(case["ability_damage"]),
			"scaled %s ability damage" % case["type"]
		)
		check.call(
			(
				is_equal_approx(boss.eff_speed(), float(case["speed"]))
				and is_equal_approx(boss.base_speed, float(case["base_speed"]))
			),
			"scaled %s speed" % case["type"]
		)
		check.call(
			boss.max_damage_per_hit == int(case["max_damage_per_hit"]),
			"scaled %s burst cap" % case["type"]
		)
		check.call(
			(
				is_equal_approx(boss.hp_scaling_mult, float(case["hp_scaling_mult"]))
				and is_equal_approx(boss.dmg_scaling_mult, float(case["dmg_scaling_mult"]))
				and is_equal_approx(boss.spd_scaling_mult, float(case["spd_scaling_mult"]))
			),
			"scaled %s multipliers" % case["type"]
		)
		check.call(
			boss.definition.max_hp == boss.max_hp and boss.definition.damage == boss.damage,
			"scaled %s definition refresh" % case["type"]
		)


func _debuffs(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var mid := _mid()
	for entry in fixture["debuff_runs"]:
		var boss := _boss_of(entry["type"], table, mid)
		check.call(boss != null, "debuff run %s" % entry["type"])
		if boss == null:
			continue
		var ops: Array = entry["ops"]
		var snapshots: Array = entry["snapshots"]
		for index in range(ops.size()):
			var op: Dictionary = ops[index]
			var args: Array = op["args"]
			var label := "%s op %d %s" % [entry["type"], index, op["call"]]
			match op["call"]:
				"apply_slow":
					boss.apply_slow(float(args[0]), int(args[1]))
				"apply_debuff":
					var source_team := int(args[3]) if args.size() > 3 else -1
					boss.apply_debuff(String(args[0]), float(args[1]), int(args[2]), source_team)
				"apply_stun":
					boss.apply_stun(int(args[0]))
				"clear_tower_debuffs":
					boss.clear_tower_debuffs()
			_snapshot(check, boss, snapshots[index], label)


func _snapshot(check: Callable, boss: BossState, row: Dictionary, label: String) -> void:
	check.call(is_equal_approx(boss.slow_amount, float(row["slow_amount"])), label + " slow amount")
	check.call(boss.slow_timer == int(row["slow_timer"]), label + " slow timer")
	check.call(is_equal_approx(boss.eff_speed(), float(row["eff_speed"])), label + " eff speed")
	check.call(
		(
			is_equal_approx(boss.atk_slow_amount, float(row["atk_slow_amount"]))
			and boss.atk_slow_timer == int(row["atk_slow_timer"])
		),
		label + " atk slow"
	)
	check.call(
		(
			is_equal_approx(boss.skill_down_amount, float(row["skill_down_amount"]))
			and boss.skill_down_timer == int(row["skill_down_timer"])
			and boss.eff_ability_damage() == int(row["ability_damage"])
		),
		label + " skill down"
	)
	check.call(
		(
			is_equal_approx(boss.anti_heal_amount, float(row["anti_heal_amount"]))
			and boss.anti_heal_timer == int(row["anti_heal_timer"])
		),
		label + " anti heal"
	)
	check.call(
		(
			is_equal_approx(boss.burn_dps, float(row["burn_dps"]))
			and boss.burn_timer == int(row["burn_timer"])
			and is_equal_approx(boss.burn_accum, float(row["burn_accum"]))
			and boss.burn_tick_cd == int(row["burn_tick_cd"])
			and (boss.burn_team >= 0) == bool(row["burn_team_set"])
		),
		label + " burn"
	)
	check.call(boss.stun_timer == int(row["stun_timer"]), label + " stun")
	check.call(
		(
			is_equal_approx(boss.armor_shred_amount, float(row["armor_shred_amount"]))
			and boss.armor_shred_timer == int(row["armor_shred_timer"])
		),
		label + " shred"
	)
	check.call(
		(
			is_equal_approx(boss.dmg_amp_amount, float(row["dmg_amp_amount"]))
			and boss.dmg_amp_timer == int(row["dmg_amp_timer"])
		),
		label + " amp"
	)
	check.call(
		(
			is_equal_approx(boss.blind_amount, float(row["blind_amount"]))
			and boss.blind_timer == int(row["blind_timer"])
		),
		label + " blind"
	)


func _damage(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var mid := _mid()
	for case in fixture["damage"]:
		var boss := _boss_of(case["type"], table, mid)
		check.call(boss != null, "damage case %s" % case["type"])
		if boss == null:
			continue
		if case["amp"] != null:
			boss.apply_damage_amp(float(case["amp"]), 300)
		if case["shred"] != null:
			boss.apply_armor_shred(float(case["shred"]), 300)
		var school := "neutral" if case["school"] == null else String(case["school"])
		var dealt := boss.take_damage(null, int(case["raw"]), String(case["damage_type"]), school)
		var label := "%s dmg %d %s" % [case["type"], int(case["raw"]), String(school)]
		check.call(dealt == int(case["dealt"]), label + " dealt")
		check.call(
			(
				boss.hp == float(case["hp_after"])
				and boss.alive == bool(case["alive"])
				and boss.defeated == bool(case["defeated"])
			),
			label + " hp state"
		)
		check.call(boss.hurt_flash_timer == int(case["hurt_flash_timer"]), label + " hurt flash")


func _blind(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var mid := _mid()
	for case in fixture["blind"]:
		var boss := _boss_of(case["type"], table, mid)
		check.call(boss != null, "blind case %s" % case["type"])
		if boss == null:
			continue
		var stub := BlindStub.new()
		stub.blind_timer = int(case["blind_timer"])
		stub.blind_amount = float(case["blind_amount"])
		if bool(case["true_strike"]):
			var inventory := InventoryStub.new()
			inventory.true_strike = true
			stub.items = inventory
		var roll := float(case["roll"])
		boss.blind_roll_override = func() -> float: return roll
		var dealt := boss.take_damage(stub, 100, "normal", "physical")
		# -1 is the source's early return (blind miss): no hp moved.
		var applied := 0 if dealt < 0 else dealt
		var label := "%s blind %s" % [case["type"], str(case["blind_amount"])]
		check.call(applied == int(case["dealt"]), label + " dealt")
		check.call(boss.hp == float(case["hp_after"]), label + " hp")


func _defeat(check: Callable, fixture: Dictionary, table: Dictionary) -> void:
	var mid := _mid()
	for case in fixture["defeat"]:
		var boss := _boss_of(case["type"], table, mid)
		check.call(boss != null, "defeat case %s" % case["type"])
		if boss == null:
			continue
		boss.hp = float(case["hp_before"])
		boss.apply_slow(0.5, 60)
		boss.apply_debuff("burn", 12, 300, 1)
		boss.take_damage(null, 40, "physical", "physical")
		check.call(
			boss.hp == float(case["hp_after"]) and not boss.alive and boss.defeated,
			"%s killing blow" % case["type"]
		)
		check.call(
			boss.hurt_flash_timer == int(case["hurt_flash_timer"]),
			"%s death hurt flash" % case["type"]
		)
		_snapshot(check, boss, case["cleared"], "%s dead" % case["type"])
