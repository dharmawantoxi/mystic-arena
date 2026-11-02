extends RefCounted

## Closed-world parity against tactical_commands.py. Replays the pygame oracle
## scenarios (real TacticalCommandManager + real pygame units) on BattleUnit and
## compares manager/hero/unit snapshots, plus draw_world/draw_ui geometry.


class FakeModel:
	extends RefCounted
	var heroes: Array = []
	var enemy_heroes: Array = []
	var towers: Array = []
	var minions: Array = []
	var blue_base := BattleUnit.new()
	var red_base := BattleUnit.new()
	var active_boss: BattleUnit = null
	var selected_hero: BattleUnit = null
	var selected_tower: BattleUnit = null
	var mouse_x := 0.0
	var mouse_y := 0.0
	var wave_number := 1
	var state := "playing"


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/tactical_parity.json", FileAccess.READ)
	runner.check(file != null, "tactical Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var manager := TacticalCommands.new()
	runner.check(manager.valid(), "native tactical contract loads")
	runner.check(manager.cfg.command_duration == 600, "tactical command duration matches source")
	runner.check(manager.cfg.hold_tap_max_frames == 20, "tactical tap threshold matches source")
	for scenario: Dictionary in oracle.scenarios:
		_scenario(runner, manager, scenario)
	_draw_world(runner, manager, oracle.draw.world)
	_draw_ui(runner, manager, oracle.draw.ui)
	var missing := TacticalCommands.new("user://missing_tactical_%d.json" % Time.get_ticks_usec())
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing tactical contract fails closed"
	)


static func _scenario(runner, manager: TacticalCommands, scenario: Dictionary) -> void:
	var units: Dictionary = {}
	var model := _build_model(scenario, units)
	manager.reset()
	manager.attach(model)
	manager.random_script = scenario.get("random_script", []).duplicate()
	var ok := _equal(_snapshot(manager, model, units), scenario.pre)
	for step: Dictionary in scenario.steps:
		var result: Variant = _action(manager, model, units, step.get("action"), step.snapshot)
		for _frame in range(int(step.frames)):
			manager.update()
		ok = ok and _equal(result, step.result)
		ok = ok and _equal(_snapshot(manager, model, units), step.snapshot)
	runner.check(ok, "tactical scenario parity: " + str(scenario.name))
	manager.reset()
	manager.attach(null)
	for unit: BattleUnit in units.values():
		unit.follow_target = null
		unit.target = null
		unit.tactical_target = null
	model.selected_hero = null
	model.selected_tower = null
	model.active_boss = null


static func _build_model(scenario: Dictionary, units: Dictionary) -> FakeModel:
	var model := FakeModel.new()
	var pre: Dictionary = scenario.pre
	_setup_base(model.blue_base, pre.units.get("castle_blue", {}), "blue")
	_setup_base(model.red_base, pre.units.get("castle_red", {}), "red")
	units["castle_blue"] = model.blue_base
	units["castle_red"] = model.red_base
	for spec: Dictionary in scenario.get("units", []):
		var uid := str(spec.id)
		var unit := BattleUnit.new()
		var expected: Dictionary = pre.units.get(uid, {})
		unit.unit_type = str(spec.get("type", ""))
		unit.display_name = str(expected.get("name", uid))
		unit.team = str(spec.get("team", "blue"))
		unit.pos = Vector2(float(spec.get("x", 0)), float(spec.get("y", 0)))
		if spec.get("dest") != null:
			unit.destination = Vector2(float(spec.dest[0]), float(spec.dest[1]))
			unit.has_destination = true
		unit.destination_auto = bool(spec.get("dest_auto", false))
		unit.is_retreating = bool(spec.get("retreating", false))
		unit.max_hp = float(expected.get("max_hp", 100))
		unit.hp = float(expected.get("hp", unit.max_hp))
		unit.alive = bool(expected.get("alive", true))
		unit.damage_dealt = float(expected.get("damage_dealt", 0))
		match str(spec.kind):
			"hero":
				unit.kind = BattleUnit.Kind.HERO
				if pre.heroes.has(uid):
					unit.attack_range = float(pre.heroes[uid].range)
				if unit.team == "blue":
					model.heroes.append(unit)
				else:
					model.enemy_heroes.append(unit)
			"minion":
				unit.kind = BattleUnit.Kind.MINION
				model.minions.append(unit)
			"tower":
				unit.kind = BattleUnit.Kind.TOWER
				model.towers.append(unit)
			"boss":
				unit.kind = BattleUnit.Kind.BOSS
				model.active_boss = unit
		units[uid] = unit
	var setup: Dictionary = scenario.get("setup", {})
	model.selected_hero = units.get(setup.get("selected_hero"))
	model.selected_tower = units.get(setup.get("selected_tower"))
	if setup.has("mouse"):
		model.mouse_x = float(setup.mouse[0])
		model.mouse_y = float(setup.mouse[1])
	model.wave_number = int(setup.get("wave", 1))
	model.state = str(setup.get("state", "playing"))
	for key: String in setup.get("castle_hp", {}):
		var base: BattleUnit = model.blue_base if key == "castle_blue" else model.red_base
		base.hp = float(setup.castle_hp[key])
	for key: String in setup.get("castle_dead", []):
		var base: BattleUnit = model.blue_base if key == "castle_blue" else model.red_base
		base.alive = false
		base.hp = 0
	return model


static func _setup_base(base: BattleUnit, expected: Dictionary, team: String) -> void:
	base.kind = BattleUnit.Kind.CASTLE
	base.team = team
	base.display_name = str(expected.get("name", "Castle"))
	base.pos = Vector2(float(expected.get("x", 0)), float(expected.get("y", 0)))
	base.max_hp = float(expected.get("max_hp", 100))
	base.hp = float(expected.get("hp", base.max_hp))
	base.alive = bool(expected.get("alive", true))


static func _action(
	manager: TacticalCommands,
	model: FakeModel,
	units: Dictionary,
	action: Variant,
	expected: Dictionary
) -> Variant:
	if action == null:
		return null
	var op := str(action.op)
	match op:
		"gather":
			return manager.command_gather(
				action.get("x"), action.get("y"), bool(action.get("silent", false))
			)
		"protect_tower":
			return manager.command_protect_tower(
				units.get(action.get("tower")), bool(action.get("silent", false))
			)
		"protect_castle":
			return manager.command_protect_castle(bool(action.get("silent", false)))
		"attack_boss":
			return manager.command_attack_boss(bool(action.get("silent", false)))
		"attack_dealer":
			return manager.command_attack_damage_dealer(bool(action.get("silent", false)))
		"hold_start":
			var args: Array = []
			for value: Variant in action.get("args", []):
				args.append(units.get(value) if value is String and units.has(value) else value)
			return manager.hold_start(
				str(action.name), args, bool(action.get("follow_mouse", false))
			)
		"hold_end":
			var end_name: Variant = action.get("name")
			manager.hold_end("" if end_name == null else str(end_name))
			return null
		"set_pos":
			var unit: BattleUnit = units[action.unit]
			unit.pos = Vector2(float(action.x), float(action.y))
			return null
		"set_hp":
			_unit_or_base(model, units, str(action.unit)).hp = float(action.hp)
			return null
		"set_damage":
			var unit: BattleUnit = units[action.unit]
			unit.damage_dealt = float(action.damage)
			return null
		"set_mouse":
			model.mouse_x = float(action.x)
			model.mouse_y = float(action.y)
			return null
		"set_wave":
			model.wave_number = int(action.n)
			return null
		"set_state":
			model.state = str(action.state)
			return null
		"set_selected_hero":
			model.selected_hero = units.get(action.get("unit"))
			return null
		"set_selected_tower":
			model.selected_tower = units.get(action.get("unit"))
			return null
		"kill":
			var unit := _unit_or_base(model, units, str(action.unit))
			unit.alive = false
			unit.hp = 0
			return null
		"revive":
			var unit := _unit_or_base(model, units, str(action.unit))
			unit.alive = true
			unit.hp = float(action.get("hp", unit.max_hp))
			if unit.kind == BattleUnit.Kind.BOSS:
				model.active_boss = unit
			return null
		"spawn_boss":
			var uid := str(action.get("unit", "boss0"))
			var unit := BattleUnit.new()
			var expected_unit: Dictionary = expected.units.get(uid, {})
			unit.kind = BattleUnit.Kind.BOSS
			unit.team = str(action.get("team", "red"))
			unit.pos = Vector2(float(action.get("x", 700)), float(action.get("y", 400)))
			unit.display_name = str(expected_unit.get("name", uid))
			unit.max_hp = float(expected_unit.get("max_hp", 10000))
			unit.hp = float(action.get("hp", unit.max_hp))
			units[uid] = unit
			model.active_boss = unit
			return uid
		"helper_count":
			return TacticalTargeting.count_enemies_near(
				model, float(action.x), float(action.y), float(action.radius)
			)
		"helper_nearest":
			return _uid(
				units,
				TacticalTargeting.nearest_enemy_target(
					model, manager.cfg, float(action.x), float(action.y)
				)
			)
		"helper_threatened":
			return _uid(units, TacticalTargeting.most_threatened_tower(model, manager.cfg))
		"helper_dealer":
			return _uid(units, TacticalTargeting.enemy_damage_dealer(model))
		"can_issue":
			return manager.can_issue()
	return null


static func _unit_or_base(model: FakeModel, units: Dictionary, uid: String) -> BattleUnit:
	if uid == "castle_blue":
		return model.blue_base
	if uid == "castle_red":
		return model.red_base
	return units[uid]


static func _snapshot(manager: TacticalCommands, model: FakeModel, units: Dictionary) -> Dictionary:
	var heroes: Dictionary = {}
	for uid: String in units:
		var unit: BattleUnit = units[uid]
		if unit.kind == BattleUnit.Kind.HERO and unit.team == "blue":
			heroes[uid] = {
				"x": _r4(unit.pos.x),
				"y": _r4(unit.pos.y),
				"alive": unit.alive,
				"destination":
				(
					[_r4(unit.destination.x), _r4(unit.destination.y)]
					if unit.has_destination
					else null
				),
				"destination_auto": unit.destination_auto,
				"follow_target": _uid(units, unit.follow_target),
				"target": _uid(units, unit.target),
				"is_retreating": unit.is_retreating,
				"range": unit.range,
			}
	var all_units: Dictionary = {}
	for uid: String in units:
		var unit: BattleUnit = units[uid]
		all_units[uid] = {
			"x": _r4(unit.pos.x),
			"y": _r4(unit.pos.y),
			"hp": unit.hp,
			"max_hp": unit.max_hp,
			"alive": unit.alive,
			"team": unit.team,
			"name": unit.display_name,
			"damage_dealt": int(unit.damage_dealt),
		}
	var hold_args: Array = []
	for value: Variant in manager.hold_args:
		hold_args.append(_uid(units, value) if value is BattleUnit else value)
	return {
		"manager":
		{
			"active_command":
			manager.active_command if not manager.active_command.is_empty() else null,
			"command_timer": manager.command_timer,
			"command_target": _uid(units, manager.command_target),
			"command_origin": manager.command_origin,
			"cooldown": manager.cooldown,
			"gather_point":
			(
				[_r4(manager.gather_point.x), _r4(manager.gather_point.y)]
				if manager.gather_point != null
				else null
			),
			"gather_point_timer": manager.gather_point_timer,
			"feedback_text": manager.feedback_text,
			"feedback_timer": manager.feedback_timer,
			"feedback_color": manager.feedback_color,
			"held_command": manager.held_command if not manager.held_command.is_empty() else null,
			"hold_follow_mouse": manager.hold_follow_mouse,
			"hold_elapsed": manager.hold_elapsed,
			"hold_has_fired": manager._hold_has_fired,
			"gather_push_fired": manager._gather_push_fired,
			"auto_check_timer": manager._auto_check_timer,
			"command_color": manager.command_color(),
			"status_text": manager.status_text(),
			"hold_args": hold_args,
			"hold_kwargs": manager.hold_kwargs,
		},
		"heroes": heroes,
		"units": all_units,
		"game":
		{
			"selected_hero": _uid(units, model.selected_hero),
			"selected_tower": _uid(units, model.selected_tower),
			"mouse": [int(model.mouse_x), int(model.mouse_y)],
			"wave": model.wave_number,
			"state": model.state,
		},
	}


static func _draw_world(runner, manager: TacticalCommands, cases: Array) -> void:
	var heroes: Array = []
	for pos: Array in [[300.0, 300.0], [700.0, 400.0]]:
		var hero := BattleUnit.new()
		hero.kind = BattleUnit.Kind.HERO
		hero.pos = Vector2(pos[0], pos[1])
		heroes.append(hero)
	for row: Dictionary in cases:
		var data := TacticalDraw.world_data(
			manager.cfg, "gather", Vector2(500, 400), int(row.timer), heroes, int(row.ticks)
		)
		var expected_circles: Array = []
		for circle: Dictionary in row.circles:
			var normalized: Dictionary = circle.duplicate(true)
			var color: Array = normalized.color.duplicate()
			if color.size() == 3:
				color.append(255)
			normalized.color = color
			expected_circles.append(normalized)
		var ok := (
			_equal(data.get("circles", []), expected_circles)
			and _equal(data.get("lines", []), row.lines)
		)
		runner.check(ok, "tactical draw_world parity timer=%d" % int(row.timer))


static func _draw_ui(runner, manager: TacticalCommands, cases: Array) -> void:
	for row: Dictionary in cases:
		var data := TacticalDraw.ui_data(manager.cfg, int(row.timer))
		var blits: Array = row.blits
		var text: Dictionary = blits[blits.size() - 1]
		var shadow: Dictionary = blits[1]
		var border: Dictionary = row.rects[0]
		var center := [
			int(text.pos[0]) + int(text.size[0]) / 2, int(text.pos[1]) + int(text.size[1]) / 2
		]
		var ok := int(data.alpha) == int(text.alpha) and int(data.shadow_alpha) == int(shadow.alpha)
		ok = (
			ok
			and int(data.border_width) == int(border.width)
			and int(data.border_radius) == int(border.radius)
		)
		ok = ok and _equal(data.center, center)
		runner.check(ok, "tactical draw_ui parity timer=%d" % int(row.timer))


static func _uid(units: Dictionary, unit: Variant) -> Variant:
	if unit == null or not unit is BattleUnit:
		return null
	for uid: String in units:
		if units[uid] == unit:
			return uid
	return null


static func _r4(value: float) -> float:
	return roundf(value * 10000.0) / 10000.0


static func _equal(a: Variant, b: Variant) -> bool:
	if a == null or b == null:
		return a == b
	if a is bool or b is bool:
		return a == b
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for key: Variant in a:
			if not b.has(key) or not _equal(a[key], b[key]):
				return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for index in range(a.size()):
			if not _equal(a[index], b[index]):
				return false
		return true
	if (a is int or a is float) and (b is int or b is float):
		return absf(float(a) - float(b)) <= 0.0001
	return a == b
