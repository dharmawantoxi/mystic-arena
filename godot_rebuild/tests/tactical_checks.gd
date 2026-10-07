extends RefCounted
## Native replay of `tests/fixtures/tactical_source.json`.
##
## The fixture is produced by `tests/tactical_source_oracle.py`, which runs the
## REAL `tactical_commands.TacticalCommandManager` against stub entities. This
## suite rebuilds the same declarative world with the rebuild's own state
## classes, replays the same action list against
## `scripts/match/tactical_commands.gd` and compares every scalar exactly:
## command state and timers, per-hero destination/follow/target/retreat values,
## feedback text and colors, `get_status_text`, the sounds each order plays, and
## the AUTO-PROTECT decisions (including the boss counting double).
##
## `_entity.credit_hero_damage` (the ATTACK DAMAGE DEALER input) is checked both
## as the truncation table recorded by the oracle and through the real match
## damage path.

const Tactical = preload("res://scripts/match/tactical_commands.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const MinionDefinition = preload("res://scripts/data/minion_definition.gd")
const StructureDefinition = preload("res://scripts/data/structure_definition.gd")
const FIXTURE := "res://tests/fixtures/tactical_source.json"
const FALLBACK_PROBE_POINT := Vector2(640, 360)
const CASTLE_PROBE_RADIUS := 300.0


## Duck-typed stand-in for the match world: exactly the surface the ported
## manager reads (`is_running`, `units`, `structures`, `nexuses`, `active_boss`,
## `wave_count`, `get_unit`, `move_to`, `_ai_roster`).
class StubWorld:
	extends RefCounted
	var units: Array = []
	var structures: Array = []
	var nexuses: Array = [null, null]
	var active_boss: Object = null
	var wave_count := 1
	var running := true
	var registry: Dictionary = {}
	var ai_owned: Array = []
	var move_calls := 0

	func is_running() -> bool:
		return running

	func get_unit(id: int) -> Object:
		return registry.get(id, null)

	func move_to(hero: Object, point: Vector2, auto: bool) -> void:
		# `_entity.py::Hero.move_to`.
		move_calls += 1
		hero.has_destination = true
		hero.destination = point
		hero.destination_auto = auto
		hero.follow_id = -1
		hero.is_retreating = false

	func _ai_roster() -> Array:
		return ai_owned


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(not fixture.is_empty(), "Tactical fixture parses")
	_check_constants(check, fixture.get("constants", {}))
	_check_credit(check, fixture.get("credit", {}))
	var scenarios: Array = fixture.get("scenarios", [])
	check.call(scenarios.size() >= 58, "Tactical oracle covers every order branch")
	for entry in scenarios:
		_run_scenario(check, entry)


func _check_constants(check: Callable, constants: Dictionary) -> void:
	check.call(
		int(constants.get("hold_tap_max_frames", -1)) == Tactical.HOLD_TAP_MAX_FRAMES,
		"HOLD tap window is 20 ticks"
	)
	check.call(
		int(constants.get("hold_release_tail", -1)) == Tactical.HOLD_RELEASE_TAIL,
		"HOLD release tail is 30 ticks"
	)
	check.call(
		int(constants.get("gather_push_delay_frames", -1)) == Tactical.GATHER_PUSH_DELAY_FRAMES,
		"GATHER hold push delay is 240 ticks"
	)
	check.call(int(constants.get("cooldown_max", -1)) == Tactical.COOLDOWN_MAX, "Order cooldown 30")
	check.call(int(constants.get("command_ticks", -1)) == Tactical.COMMAND_TICKS, "Order lasts 600")
	check.call(int(constants.get("marker_ticks", -1)) == Tactical.MARKER_TICKS, "Marker lasts 150")
	check.call(
		int(constants.get("feedback_ticks", -1)) == Tactical.FEEDBACK_TICKS, "Feedback lasts 180"
	)
	check.call(int(constants.get("auto_check_ticks", -1)) == Tactical.AUTO_CHECK_TICKS, "Auto 90")
	check.call(
		is_equal_approx(float(constants.get("auto_boss_roll", -1.0)), Tactical.AUTO_BOSS_ROLL),
		"Auto boss roll threshold 0.2"
	)
	check.call(
		int(constants.get("auto_boss_wave", -1)) == Tactical.AUTO_BOSS_WAVE, "Auto boss wave"
	)
	var blue: Array = constants.get("blue_base", [])
	var red: Array = constants.get("red_base", [])
	check.call(
		(
			Vector2(float(blue[0]), float(blue[1])) == Tactical.LaneLayout.BLUE_BASE
			and Vector2(float(red[0]), float(red[1])) == Tactical.LaneLayout.RED_BASE
		),
		"Tactical bases match the source settings fallback"
	)
	var screen: Array = constants.get("screen", [])
	check.call(
		Vector2(float(screen[0]), float(screen[1])) == Tactical.ARENA_SIZE,
		"Tactical arena bounds match the source screen"
	)
	# The migrated audio facade has no per-call volume, so only the sound NAMES
	# are portable; the source volumes are recorded here as the contract.
	var volumes: Dictionary = constants.get("sound_volumes", {})
	check.call(
		(
			is_equal_approx(float(volumes.get("ui_click", 0.0)), 0.8)
			and is_equal_approx(float(volumes.get("hero_skill", 0.0)), 0.9)
		),
		"Source order volumes are ui_click 0.8 / hero_skill 0.9"
	)


func _check_credit(check: Callable, credit: Dictionary) -> void:
	## `_entity.credit_hero_damage` truncation table, replayed through the native
	## hook the match damage path calls.
	var world := Prototype.new()
	check.call(world.setup_arena(), "Credit world initializes")
	var dealer := world.blue_hero()
	check.call(dealer != null and dealer.damage_dealt == 0, "Heroes start with no credited damage")
	var amounts: Array = credit.get("amounts", [])
	var totals: Array = credit.get("totals", [])
	check.call(amounts.size() == totals.size(), "Credit fixture pairs amounts with totals")
	for index in range(amounts.size()):
		world._credit_damage_dealt(dealer.id, float(amounts[index]))
		check.call(
			dealer.damage_dealt == int(totals[index]),
			"credit_hero_damage truncation #%d" % (index + 1)
		)
	world._credit_damage_dealt(-1, 500.0)
	check.call(
		dealer.damage_dealt == int(totals[totals.size() - 1]),
		"An unknown source (source=None) credits nobody"
	)
	world._credit_damage_dealt(987654, 500.0)
	check.call(
		dealer.damage_dealt == int(totals[totals.size() - 1]),
		"A missing attacker id credits nobody"
	)
	check.call(
		int(credit.get("none_source_total", -1)) == 25,
		"Source keeps an untouched total when source is None"
	)
	check.call(
		int(credit.get("missing_attribute_total", -1)) == 9,
		"Source creates damage_dealt on demand and truncates"
	)

	# Integration: the shared damage path credits the post-mitigation amount.
	var live := Prototype.new()
	check.call(live.setup_arena(), "Damage-path world initializes")
	var attacker := live.blue_hero()
	var victim := live.spawn_unit(live.MINIONS["goblin"], live.RED, 1)
	victim.position = attacker.position + Vector2(20, 0)
	var before := victim.hp
	check.call(
		live.hero_basic_attack(attacker.id, victim.id), "Hero basic attack lands for credit proof"
	)
	var applied := before - victim.hp
	check.call(
		attacker.damage_dealt == int(applied) and attacker.damage_dealt > 0,
		"A landed hero hit credits its post-mitigation damage"
	)
	var second := live.spawn_unit(live.MINIONS["orc"], live.RED, 1)
	second.position = attacker.position + Vector2(20, 0)
	attacker.attack_timer = 0
	var first_total := attacker.damage_dealt
	check.call(live.hero_basic_attack(attacker.id, second.id), "Second hero hit lands")
	check.call(attacker.damage_dealt > first_total, "Credited damage accumulates across hits")
	# Burn DOT carries no source in either codebase, so it credits nobody. The
	# heroes are parked outside every hunt range so only the burn lands.
	for unit in live.units:
		if unit.is_hero:
			unit.position = Vector2(-9000, -9000)
	var burnt := live.spawn_unit(live.MINIONS["goblin"], live.RED, 2)
	var totals_before := _team_damage_totals(live)
	check.call(
		live.apply_burn(burnt.id, 8.0, 90, live.BLUE), "Burn is applied for the no-credit proof"
	)
	for _tick in range(35):
		live.step_tick()
	check.call(burnt.hp < float(burnt.definition.max_hp), "Burn damaged its victim")
	check.call(
		_team_damage_totals(live) == totals_before,
		"Sourceless burn damage credits no damage dealer"
	)


func _team_damage_totals(world: Prototype) -> int:
	var total := 0
	for unit in world.units:
		total += int(unit.damage_dealt)
	return total


func _run_scenario(check: Callable, scenario: Dictionary) -> void:
	var label := String(scenario.get("name", "?"))
	var world := _build_world(check, scenario.get("world", {}), label)
	var tactical := Tactical.new()
	tactical.bind(world)
	tactical.set_mouse(_spec_mouse(scenario.get("world", {})))
	tactical.set_selected_hero(int(_spec_selected(scenario.get("world", {}))))
	var returned: Array = []
	var trace: Array = []
	for action in scenario.get("actions", []):
		_apply(world, tactical, action, returned, trace)
	var expected_returned: Array = scenario.get("returned", [])
	check.call(
		returned.size() == expected_returned.size(), "Returned count matches source: " + label
	)
	for index in range(mini(returned.size(), expected_returned.size())):
		check.call(
			bool(returned[index]) == bool(expected_returned[index]),
			"hold_start result #%d matches source: %s" % [index + 1, label]
		)
	var expected_sounds: Array = scenario.get("sounds", [])
	check.call(
		Array(tactical.sound_history) == expected_sounds,
		"Order sounds match the source (silent refresh stays quiet): " + label
	)
	var expected_trace: Array = scenario.get("trace", [])
	check.call(trace.size() == expected_trace.size(), "Snapshot count matches source: " + label)
	for index in range(mini(trace.size(), expected_trace.size())):
		_check_state(check, expected_trace[index], trace[index], label + " trace#" + str(index + 1))
	_check_state(check, scenario.get("final", {}), _snapshot(tactical, world), label + " final")


func _spec_mouse(spec: Dictionary) -> Vector2:
	var mouse: Array = spec.get("mouse", [0, 0])
	return Vector2(float(mouse[0]), float(mouse[1]))


func _spec_selected(spec: Dictionary) -> int:
	var selected: Variant = spec.get("selected_hero")
	return -1 if selected == null else int(selected)


func _build_world(check: Callable, spec: Dictionary, label: String) -> StubWorld:
	var world := StubWorld.new()
	world.running = String(spec.get("state", "playing")) == "playing"
	world.wave_count = int(spec.get("wave", 1))
	for entry in spec.get("heroes", []):
		world.units.append(_make_hero(entry, Tactical.BLUE))
	for entry in spec.get("minions", []):
		world.units.append(_make_minion(entry))
	for entry in spec.get("towers", []):
		world.structures.append(_make_structure(entry, "tower"))
	var blue_castle: Variant = spec.get("blue_castle")
	if blue_castle != null:
		var castle := _make_structure(blue_castle, "nexus")
		world.structures.append(castle)
		world.nexuses[Tactical.BLUE] = castle
	var red_castle: Variant = spec.get("red_castle")
	if red_castle != null:
		var enemy := _make_structure(red_castle, "nexus")
		world.structures.append(enemy)
		world.nexuses[Tactical.RED] = enemy
	for entry in spec.get("enemy_heroes", []):
		var red_hero := _make_hero(entry, Tactical.RED)
		world.units.append(red_hero)
		world.ai_owned.append(red_hero)
	var boss_spec: Variant = spec.get("boss")
	if boss_spec != null:
		world.active_boss = _make_boss(boss_spec)
	for unit in world.units:
		world.registry[int(unit.id)] = unit
	for structure in world.structures:
		world.registry[int(structure.id)] = structure
	if world.active_boss != null:
		world.registry[int(world.active_boss.id)] = world.active_boss
	check.call(world.registry.size() > 0, "Scenario world is populated: " + label)
	return world


func _make_hero(spec: Dictionary, team: int) -> HeroState:
	var hero := HeroState.new()
	var data := HeroDefinition.new()
	data.id = "stub_%d" % int(spec.get("id", 0))
	data.display_name = String(spec.get("name", "hero"))
	data.max_hp = int(spec.get("max_hp", 1000))
	data.damage = 10
	data.attack_range_px = float(spec.get("range", 110))
	hero.definition = data
	hero.id = int(spec.get("id", 0))
	hero.team = team
	hero.position = Vector2(float(spec.get("x", 0)), float(spec.get("y", 0)))
	hero.hp = float(spec.get("hp", 1000))
	hero.max_hp = float(spec.get("max_hp", 1000))
	hero.alive = bool(spec.get("alive", true))
	hero.attack_range = float(spec.get("range", 110))
	hero.damage_dealt = int(spec.get("damage_dealt", 0))
	hero.is_retreating = bool(spec.get("is_retreating", false))
	return hero


func _make_minion(spec: Dictionary) -> UnitState:
	var minion := UnitState.new()
	var data := MinionDefinition.new()
	data.id = "stub_%d" % int(spec.get("id", 0))
	data.display_name = String(spec.get("name", "minion"))
	data.max_hp = int(spec.get("max_hp", 100))
	minion.definition = data
	minion.id = int(spec.get("id", 0))
	minion.team = Tactical.RED if String(spec.get("team", "red")) == "red" else Tactical.BLUE
	minion.position = Vector2(float(spec.get("x", 0)), float(spec.get("y", 0)))
	minion.hp = float(spec.get("hp", 100))
	minion.alive = bool(spec.get("alive", true))
	return minion


func _make_structure(spec: Dictionary, kind: String) -> StructureState:
	var structure := StructureState.new()
	var data := StructureDefinition.new()
	data.id = "stub_%d" % int(spec.get("id", 0))
	data.display_name = String(spec.get("name", kind))
	data.structure_kind = kind
	data.max_hp = int(spec.get("max_hp", 800))
	data.damage = 20
	data.level = 1
	structure.definition = data
	structure.id = int(spec.get("id", 0))
	structure.team = Tactical.RED if String(spec.get("team", "blue")) == "red" else Tactical.BLUE
	structure.position = Vector2(float(spec.get("x", 0)), float(spec.get("y", 0)))
	structure.hp = float(spec.get("hp", 800))
	structure.alive = bool(spec.get("alive", true))
	return structure


func _make_boss(spec: Dictionary) -> BossState:
	var boss := BossState.new()
	boss.id = int(spec.get("id", 0))
	boss.display_name = String(spec.get("name", "BOSS"))
	boss.team = Tactical.RED if String(spec.get("team", "red")) == "red" else Tactical.BLUE
	boss.position = Vector2(float(spec.get("x", 0)), float(spec.get("y", 0)))
	boss.hp = float(spec.get("hp", 8000))
	boss.max_hp = int(spec.get("max_hp", 8000))
	boss.alive = bool(spec.get("alive", true))
	return boss


func _apply(
	world: StubWorld, tactical: Tactical, action: Array, returned: Array, trace: Array
) -> void:
	var op := String(action[0])
	match op:
		"hold":
			returned.append(
				tactical.hold_start(
					String(action[1]),
					Vector2(float(action[2]), float(action[3])),
					bool(action[4]),
					int(action[5]),
					bool(action[6])
				)
			)
		"release":
			tactical.hold_end(String(action[1]))
		"update":
			for _tick in range(int(action[1])):
				tactical.update()
		"snapshot":
			trace.append(_snapshot(tactical, world))
		"mouse":
			tactical.set_mouse(Vector2(float(action[1]), float(action[2])))
		"select_hero":
			tactical.set_selected_hero(int(action[1]))
		"set_wave":
			world.wave_count = int(action[1])
		"state":
			world.running = String(action[1]) == "playing"
		"random":
			var roll := float(action[1])
			tactical.auto_roll_override = func() -> float: return roll
		"hp":
			world.get_unit(int(action[1])).hp = float(action[2])
		"move":
			world.get_unit(int(action[1])).position = Vector2(float(action[2]), float(action[3]))
		"kill":
			var victim: Object = world.get_unit(int(action[1]))
			victim.alive = false
			victim.hp = 0.0
		"damage":
			world.get_unit(int(action[1])).damage_dealt = int(action[2])
		"spawn_boss":
			world.active_boss = _make_boss(action[1])
			world.registry[int(world.active_boss.id)] = world.active_boss


func _snapshot(tactical: Tactical, world: StubWorld) -> Dictionary:
	var probe := tactical.gather_point() if tactical.has_gather_point else FALLBACK_PROBE_POINT
	var threatened := tactical.find_most_threatened_tower()
	var nearest := tactical.find_nearest_enemy_target(probe)
	var castle: Object = world.nexuses[Tactical.BLUE]
	return {
		"active_command": tactical.active_command,
		"command_timer": tactical.command_timer,
		"command_target": tactical.command_target_id,
		"gather_point":
		[tactical.gather_x, tactical.gather_y] if tactical.has_gather_point else null,
		"gather_point_timer": tactical.gather_point_timer,
		"cooldown": tactical.cooldown,
		"feedback_text": tactical.feedback_text,
		"feedback_timer": tactical.feedback_timer,
		"feedback_color": tactical.feedback_color,
		"command_color": tactical.command_color(),
		"status_text": tactical.status_text(),
		"held_command": tactical.held_command,
		"hold_elapsed": tactical.hold_elapsed,
		"hold_has_fired": tactical.hold_has_fired,
		"gather_push_fired": tactical.gather_push_fired,
		"auto_check_timer": tactical.auto_check_timer,
		"heroes": _entity_rows(Tactical.BLUE, world),
		"red_heroes": _entity_rows(Tactical.RED, world),
		"threatened_tower": -1 if threatened == null else int(threatened.id),
		"nearest_enemy": -1 if nearest == null else int(nearest.id),
		"enemies_near_castle":
		0 if castle == null else tactical.count_enemies_near(castle.position, CASTLE_PROBE_RADIUS),
	}


func _entity_rows(team: int, world: StubWorld) -> Array:
	# The source snapshots `game.heroes` / `game.ai.heroes` in list order, alive
	# or not, so walk the world roster instead of the manager's living subset.
	var rows: Array = []
	for unit in world.units:
		if not unit.is_hero or int(unit.team) != team:
			continue
		rows.append(_entity_row(unit))
	return rows


func _entity_row(unit: Object) -> Dictionary:
	return {
		"id": int(unit.id),
		"x": unit.position.x,
		"y": unit.position.y,
		"hp": unit.hp,
		"alive": bool(unit.alive),
		"destination":
		[unit.destination.x, unit.destination.y] if bool(unit.has_destination) else null,
		"destination_auto": bool(unit.destination_auto),
		"follow": int(unit.follow_id),
		"target": int(unit.target_id),
		"is_retreating": bool(unit.is_retreating),
		"damage_dealt": int(unit.damage_dealt),
	}


func _check_state(check: Callable, expected: Dictionary, actual: Dictionary, label: String) -> void:
	check.call(
		String(actual.get("active_command")) == _text(expected.get("active_command")),
		"active_command: " + label
	)
	check.call(
		int(actual.get("command_timer", -1)) == int(expected.get("command_timer", -2)),
		"command_timer: " + label
	)
	check.call(
		int(actual.get("command_target", -2)) == _id(expected.get("command_target")),
		"command_target: " + label
	)
	var gather: Variant = expected.get("gather_point")
	if gather == null:
		check.call(actual.get("gather_point") == null, "gather_point cleared: " + label)
	else:
		var point: Array = actual.get("gather_point")
		check.call(
			(
				point != null
				and float(point[0]) == float(gather[0])
				and float(point[1]) == float(gather[1])
			),
			"gather_point: " + label
		)
	check.call(
		int(actual.get("gather_point_timer", -1)) == int(expected.get("gather_point_timer", -2)),
		"gather_point_timer: " + label
	)
	check.call(
		int(actual.get("cooldown", -1)) == int(expected.get("cooldown", -2)), "cooldown: " + label
	)
	check.call(
		String(actual.get("feedback_text")) == String(expected.get("feedback_text", "?")),
		"feedback_text: " + label
	)
	check.call(
		int(actual.get("feedback_timer", -1)) == int(expected.get("feedback_timer", -2)),
		"feedback_timer: " + label
	)
	check.call(
		(
			actual.get("feedback_color") == _color(expected.get("feedback_color"))
			and actual.get("command_color") == _color(expected.get("command_color"))
		),
		"feedback/command colors: " + label
	)
	check.call(
		String(actual.get("status_text")) == String(expected.get("status_text", "?")),
		"status_text: " + label
	)
	check.call(
		String(actual.get("held_command")) == _text(expected.get("held_command")),
		"held_command: " + label
	)
	check.call(
		int(actual.get("hold_elapsed", -1)) == int(expected.get("hold_elapsed", -2)),
		"hold_elapsed: " + label
	)
	check.call(
		bool(actual.get("hold_has_fired")) == bool(expected.get("hold_has_fired", false)),
		"hold_has_fired: " + label
	)
	check.call(
		bool(actual.get("gather_push_fired")) == bool(expected.get("gather_push_fired", false)),
		"gather_push_fired: " + label
	)
	check.call(
		int(actual.get("auto_check_timer", -1)) == int(expected.get("auto_check_timer", -2)),
		"auto_check_timer: " + label
	)
	check.call(
		int(actual.get("threatened_tower", -2)) == _id(expected.get("threatened_tower")),
		"most threatened tower: " + label
	)
	check.call(
		int(actual.get("nearest_enemy", -2)) == _id(expected.get("nearest_enemy")),
		"nearest enemy target: " + label
	)
	check.call(
		int(actual.get("enemies_near_castle", -1)) == int(expected.get("enemies_near_castle", -2)),
		"enemies near castle: " + label
	)
	_check_rows(check, "heroes", expected, actual, label)
	_check_rows(check, "red_heroes", expected, actual, label)


func _check_rows(
	check: Callable, key: String, expected: Dictionary, actual: Dictionary, label: String
) -> void:
	var expected_rows: Array = expected.get(key, [])
	var actual_rows: Array = actual.get(key, [])
	check.call(actual_rows.size() == expected_rows.size(), "%s row count: %s" % [key, label])
	for index in range(mini(actual_rows.size(), expected_rows.size())):
		var want: Dictionary = expected_rows[index]
		var got: Dictionary = actual_rows[index]
		var row := "%s[%d] %s" % [key, index + 1, label]
		check.call(int(got.get("id", -1)) == int(want.get("id", -2)), "id: " + row)
		check.call(float(got.get("x", 0.0)) == float(want.get("x", 1.0)), "x: " + row)
		check.call(float(got.get("y", 0.0)) == float(want.get("y", 1.0)), "y: " + row)
		check.call(float(got.get("hp", 0.0)) == float(want.get("hp", 1.0)), "hp: " + row)
		check.call(bool(got.get("alive")) == bool(want.get("alive", false)), "alive: " + row)
		var want_destination: Variant = want.get("destination")
		if want_destination == null:
			check.call(got.get("destination") == null, "destination cleared: " + row)
		else:
			var got_destination: Array = got.get("destination")
			check.call(
				(
					got_destination != null
					and float(got_destination[0]) == float(want_destination[0])
					and float(got_destination[1]) == float(want_destination[1])
				),
				"destination: " + row
			)
		check.call(
			bool(got.get("destination_auto")) == bool(want.get("destination_auto", false)),
			"destination_auto: " + row
		)
		check.call(int(got.get("follow", -2)) == _id(want.get("follow")), "follow_target: " + row)
		check.call(int(got.get("target", -2)) == _id(want.get("target")), "target: " + row)
		check.call(
			bool(got.get("is_retreating")) == bool(want.get("is_retreating", false)),
			"is_retreating: " + row
		)
		check.call(
			int(got.get("damage_dealt", -1)) == int(want.get("damage_dealt", -2)),
			"damage_dealt: " + row
		)


func _text(value: Variant) -> String:
	return "" if value == null else String(value)


func _id(value: Variant) -> int:
	return -1 if value == null else int(value)


func _color(channels: Variant) -> Color:
	if channels == null:
		return Color.TRANSPARENT
	var rows: Array = channels
	return Color8(int(rows[0]), int(rows[1]), int(rows[2]))
