class_name BossParity
extends RefCounted

## Closed-world parity for the bosses/ folder: catalog normalization, 216 boss
## init/enrage rows, 79 smart-AI traces, controller scenarios and combat order.


class Probe:
	extends BattleUnit
	var idx := 0
	var events: Array = []
	var frame := [0]
	var record_damage := true

	func take_damage(
		amount: float,
		_from_team: String,
		_damage_type := "normal",
		_source: BattleUnit = null,
		_school := ""
	) -> float:
		hp -= amount
		if record_damage:
			events.append(["dmg", frame[0], idx, BossParity._round(amount, 3)])
		if hp <= 0.0:
			alive = false
		return amount

	func apply_debuff(kind_name: String, amount: float, duration: int, source_team := "") -> void:
		if kind_name == "slow":
			events.append(["slow", frame[0], idx, amount, float(duration)])
		status.apply(kind_name, amount, duration, source_team)


class Model:
	extends RefCounted
	var data := CoreData.new()
	var minions: Array = []
	var towers: Array = []
	var blue_base := BattleUnit.new()
	var red_base := BattleUnit.new()
	var rng := RandomNumberGenerator.new()

	func _init() -> void:
		blue_base.alive = false
		red_base.alive = false
		blue_base.pos = Vector2(100, 620)
		red_base.pos = Vector2(1180, 100)
		rng.seed = 1701

	func all_units() -> Array:
		return minions

	func add_shake(_amount: float) -> void:
		pass

	func add_popup(_pos: Vector2, _text: String, _color: Color) -> void:
		pass

	func add_effect(_pos: Vector2, _type: String, _color: Color, _radius: int) -> void:
		pass

	func add_damage_number(_pos: Vector2, _amount: int, _crit: bool, _type: String) -> void:
		pass


static func run(runner) -> void:
	var file := FileAccess.open("res://tests/fixtures/bosses_parity.json", FileAccess.READ)
	runner.check(file != null, "bosses Python oracle fixture exists")
	if file == null:
		return
	var oracle: Dictionary = JSON.parse_string(file.get_as_text())
	var data := CoreData.new()
	runner.check(data.valid() and data.bosses.valid(), "boss catalog loads and matches core")
	_normalization(runner, data, oracle.normalization)
	_runtime(runner, data, oracle.runtime)
	_smart(runner, data, oracle.smart_ai)
	_controller(runner, data, oracle.controller)
	_combat(runner, data, oracle.combat)
	var missing := BossCatalog.new("user://missing_bosses_%d.json" % Time.get_ticks_usec())
	runner.check(
		not missing.valid() and not missing.load_error.is_empty(),
		"missing boss catalog fails closed"
	)
	var invalid_core := CoreData.new(
		"res://data/core_data.json",
		HeroArchetypes.DEFAULT_PATH,
		HeroBalance.DEFAULT_PATH,
		HeroItems.DEFAULT_PATH,
		Localization.DEFAULT_PATH,
		"user://missing_bosses_core.json"
	)
	runner.check(not invalid_core.valid(), "CoreData rejects missing boss catalog")


static func _normalization(runner, data: CoreData, oracle: Dictionary) -> void:
	var normalized := data.bosses.normalize(data.data.levels)
	var ok := true
	for kind: String in ["mini", "true"]:
		for key: String in oracle.final[kind]:
			if not _equal(normalized[kind][key], oracle.final[kind][key]):
				ok = false
	runner.check(ok, "boss pristine->final normalization covers 216 rows")
	for row: Dictionary in oracle.trend:
		var fit := BossCatalog.trend(row.values)
		runner.check(
			_near(fit.x, float(row.a)) and _near(fit.y, float(row.b)), "boss hero-unlock trend fit"
		)
	for row: Array in oracle.slots:
		runner.check(BossCatalog.slot_of_wave(int(row[0])) == str(row[1]), "boss wave slot")
	runner.check(data.bosses.renderer("morvaeth2").module == "level42", "boss renderer alias index")
	runner.check(data.bosses.label_top("abaddon", 30) == 63, "boss label top anchor")


static func _runtime(runner, data: CoreData, oracle: Dictionary) -> void:
	var model := Model.new()
	var ok := true
	var enrage_ok := true
	for row: Dictionary in oracle.bosses:
		var boss := BattleUnit.new()
		boss.world = model
		boss.setup_boss(data, str(row.boss_type), PackedVector2Array())
		var fields := {
			"boss_class": boss.boss_class,
			"hp": boss.max_hp,
			"damage": boss.damage,
			"speed": boss.speed,
			"range": boss.attack_range,
			"attack_cooldown_frames": boss.attack_cooldown,
			"radius": boss.radius,
			"armor": boss.armor,
			"magic_resist": boss.magic_resist,
			"damage_reduction": boss.damage_reduction,
			"max_damage_per_hit": boss.max_damage_per_hit,
			"tenacity": boss.tenacity,
			"entrance_frames": boss.entrance_timer,
			"cleave_radius": boss.cleave_radius,
			"cleave_ratio": boss.cleave_ratio,
			"ability_cooldown_frames": boss.ability_cooldown_max,
			"ability_damage": boss.ability_damage,
			"ability_range": boss.ability_range,
			"ability2_cooldown_frames": boss.ability2_cooldown_max,
			"ability2_heal_pct": boss.ability2_heal_pct,
			"uses_smart_ai": data.bosses.has_smart_ai(boss.unit_type),
		}
		for field: String in fields:
			if not _equal(fields[field], row[field]):
				ok = false
		boss.entrance_timer = 0
		boss.hp = int(boss.max_hp * (0.50 if boss.boss_class == "true" else 0.40))
		BossController.update(model, boss)
		if (
			not boss.is_enraged
			or not _near(boss.speed, float(row.enraged_speed))
			or not _equal(boss.damage, row.enraged_damage)
			or not _equal(boss.attack_cooldown, row.enraged_attack_cd_frames)
		):
			enrage_ok = false
		boss.target = null
		boss.world = null
	runner.check(ok, "boss init stats parity: 216 rows")
	runner.check(enrage_ok, "boss enrage parity: 216 rows")
	runner.check(int(oracle.smart_ai_count) == 79, "boss smart-AI dispatch count")


static func _smart(runner, data: CoreData, oracle: Dictionary) -> void:
	for row: Dictionary in oracle.bosses:
		for scenario: String in row.scenarios:
			_smart_case(runner, data, str(row.boss_type), scenario, row.scenarios[scenario])


static func _smart_case(
	runner, data: CoreData, boss_type: String, name: String, case: Dictionary
) -> void:
	var model := Model.new()
	var boss := BattleUnit.new()
	boss.world = model
	boss.setup_boss(data, boss_type, PackedVector2Array())
	boss.pos = Vector2(600, 400)
	boss.prev_pos = boss.pos
	boss.entrance_timer = 0
	boss.attack_timer = 1000000000
	boss.active_skill_timer = -1
	var probes: Array = []
	var events: Array = []
	var frame := [0]
	for i in range(case.probes.size()):
		var probe := Probe.new()
		probe.idx = i
		probe.events = events
		probe.frame = frame
		probe.record_damage = false
		probe.kind = BattleUnit.Kind.MINION
		probe.team = "blue"
		probe.pos = Vector2(600 + float(case.probes[i][0]), 400 + float(case.probes[i][1]))
		probe.hp = 1e9
		probe.max_hp = 1e9
		probe.speed = 2.0
		probes.append(probe)
		model.minions.append(probe)
	var hp_script: Dictionary = {}
	if case.hp_script is String:
		var ratio := 0.28 if case.hp_script == "low" else 1.0
		for f in range(int(case.frames)):
			hp_script[f] = ratio
	else:
		for pair: Array in case.hp_script:
			hp_script[int(pair[0])] = float(pair[1])
	var got: Array = []
	var prev := _smart_snapshot(boss, probes)
	for f in range(int(case.frames)):
		frame[0] = f
		if hp_script.has(f):
			boss.hp = int(boss.max_hp * float(hp_script[f]))
		BossController.update(model, boss)
		var now := _smart_snapshot(boss, probes)
		_diff_events(got, prev, now, f, probes)
		prev = now
	got.append_array(events)
	var expected := _bucket(case.events)
	var actual := _bucket(got)
	var ok := _equal(actual, expected)
	var final: Dictionary = case.final
	ok = (
		ok
		and _near(boss.hp, float(final.hp))
		and _near(boss.pos.x, float(final.x))
		and _near(boss.pos.y, float(final.y))
		and _equal(boss.damage, final.damage)
		and _near(boss.speed, float(final.speed))
		and _equal(boss.facing, final.direction)
		and _equal(boss.is_enraged, final.is_enraged)
		and _equal(boss.ability2_timer, final.ability2_timer)
	)
	for key: String in final.kit:
		var want: Variant = final.kit[key]
		var have: Variant = boss.kit.get(key) if boss.kit.has(key) else boss.get(key)
		if have == null and boss.kit.has(key):
			have = boss.kit[key]
		if want is String and str(want).begins_with("P"):
			var idx := int(str(want).substr(1))
			ok = ok and have == probes[idx]
		else:
			ok = ok and _equal(have, want)
	runner.check(ok, "boss smart-AI parity: %s/%s" % [boss_type, name])
	for probe: BattleUnit in probes:
		probe.world = null
	boss.target = null
	boss.world = null


static func _smart_snapshot(boss: BattleUnit, probes: Array) -> Dictionary:
	var rows: Array = []
	for probe: BattleUnit in probes:
		rows.append({"hp": probe.hp, "atk": probe.attack_timer, "x": probe.pos.x, "y": probe.pos.y})
	return {
		"hp": boss.hp,
		"x": boss.pos.x,
		"y": boss.pos.y,
		"spd": boss.speed,
		"dmg": boss.damage,
		"dir": boss.facing,
		"enr": boss.is_enraged,
		"ast": boss.active_skill_timer,
		"skill": boss.active_skill,
		"kit_skill": boss.kit.get("active_skill"),
		"probes": rows
	}


static func _diff_events(
	out: Array, prev: Dictionary, now: Dictionary, frame: int, probes: Array
) -> void:
	if not _near(float(now.hp), float(prev.hp)):
		out.append(["bhp", frame, _round(float(now.hp), 3)])
	if absf(float(now.x) - float(prev.x)) > 0.001 or absf(float(now.y) - float(prev.y)) > 0.001:
		out.append(["bmove", frame, _round(float(now.x), 3), _round(float(now.y), 3)])
	if int(now.ast) > int(prev.ast):
		out.append(["cast", frame, now.kit_skill])
	if not _near(float(now.spd), float(prev.spd)):
		out.append(["bspd", frame, _round(float(now.spd), 5)])
	if not _equal(now.dmg, prev.dmg):
		out.append(["bdmg", frame, int(now.dmg)])
	if not _equal(now.dir, prev.dir):
		out.append(["bface", frame, int(now.dir)])
	if bool(now.enr) and not bool(prev.enr):
		out.append(["enrage", frame])
	for i in range(probes.size()):
		var p: Dictionary = now.probes[i]
		var q: Dictionary = prev.probes[i]
		var d := float(q.hp) - float(p.hp)
		if d > 0.0:
			out.append(["dmg", frame, i, _round(d, 3)])
		if not _near(float(p.atk), float(q.atk)):
			out.append(["alock", frame, i, _round(float(p.atk), 3)])
		if not _near(float(p.x), float(q.x)) or not _near(float(p.y), float(q.y)):
			out.append(["emove", frame, i, _round(float(p.x), 3), _round(float(p.y), 3)])


static func _bucket(events: Array) -> Dictionary:
	var out: Dictionary = {}
	for event: Array in events:
		var kind := str(event[0])
		var frame := int(event[1])
		var key := "%s:%d" % [kind, frame]
		if not out.has(key):
			out[key] = []
		out[key].append(event.slice(2))
	for key: String in out:
		out[key].sort()
	return out


static func _controller(runner, data: CoreData, cases: Array) -> void:
	for case: Dictionary in cases:
		var model := Model.new()
		var boss := BattleUnit.new()
		boss.world = model
		boss.setup_boss(data, str(case.boss_type), PackedVector2Array())
		boss.pos = Vector2(600, 400)
		boss.prev_pos = boss.pos
		var probes: Array = []
		var events: Array = []
		var frame := [0]
		var scenario := str(case.scenario)
		if scenario == "basic":
			boss.entrance_timer = 0
			probes = _make_probes(model, [[30, 0], [60, 20]], events, frame)
		elif scenario == "kite":
			boss.entrance_timer = 0
			probes = _make_probes(model, [[230, 0]], events, frame)
		elif scenario == "stun":
			boss.entrance_timer = 0
			boss.apply_debuff("stun", 1.0, 40)
			probes = _make_probes(model, [[30, 0], [60, 20]], events, frame)
		elif scenario == "lane":
			boss.entrance_timer = 0
			boss.path = PackedVector2Array(
				[Vector2(100, 620), Vector2(400, 400), Vector2(600, 400)]
			)
			boss.waypoint = 2
		elif scenario == "heal":
			boss.entrance_timer = 0
			boss.hp = int(boss.max_hp * 0.2)
		var ok := true
		for f in range(int(case.frames)):
			frame[0] = f
			BossController.update(model, boss)
			var snap := _controller_snapshot(boss, probes)
			if not _controller_equal(snap, case.steps[f]):
				ok = false
		ok = ok and _equal(_bucket(events), _bucket(case.events))
		runner.check(ok, "boss controller parity: %s/%s" % [case.boss_type, scenario])
		boss.target = null
		boss.world = null
		for probe: BattleUnit in probes:
			probe.world = null


static func _make_probes(model: Model, offsets: Array, events: Array, frame: Array) -> Array:
	var probes: Array = []
	for i in range(offsets.size()):
		var probe := Probe.new()
		probe.idx = i
		probe.events = events
		probe.frame = frame
		probe.record_damage = true
		probe.kind = BattleUnit.Kind.MINION
		probe.team = "blue"
		probe.pos = Vector2(600 + float(offsets[i][0]), 400 + float(offsets[i][1]))
		probe.hp = 1e9
		probe.max_hp = 1e9
		probe.speed = 2.0
		probes.append(probe)
		model.minions.append(probe)
	return probes


static func _controller_snapshot(boss: BattleUnit, probes: Array) -> Dictionary:
	var rows: Array = []
	for probe: BattleUnit in probes:
		rows.append(
			{
				"hp": _round(probe.hp, 3),
				"x": _round(probe.pos.x, 2),
				"y": _round(probe.pos.y, 2),
				"attack_timer": _round(float(probe.attack_timer), 3),
				"slow_amount": probe.status.slow_amount,
				"slow_timer": probe.status.slow_timer
			}
		)
	var target = null
	if boss.target != null and boss.target is Probe:
		target = boss.target.idx
	return {
		"hp": _round(boss.hp, 3),
		"x": _round(boss.pos.x, 2),
		"y": _round(boss.pos.y, 2),
		"damage": int(boss.damage),
		"speed": _round(boss.speed, 6),
		"facing": boss.facing,
		"enraged": boss.is_enraged,
		"attack_timer": boss.attack_timer,
		"ability_timer": boss.ability_timer,
		"ability2_timer": boss.ability2_timer,
		"entrance_timer": boss.entrance_timer,
		"stun_timer": boss.status.stun_timer,
		"moving": boss.is_moving,
		"target": target,
		"probes": rows
	}


static func _controller_equal(a: Dictionary, b: Dictionary) -> bool:
	# Godot Vector2 is float32; the pygame oracle uses float64. Allow 0.02 px
	# positional drift over a 90-120 frame trace while keeping timers/HP exact.
	for key: String in b:
		if key in ["x", "y"]:
			if absf(float(a.get(key, 0)) - float(b[key])) > 0.02:
				return false
		elif key == "probes":
			var pa: Array = a.get(key, [])
			var pb: Array = b[key]
			if pa.size() != pb.size():
				return false
			for i in range(pa.size()):
				for field: String in pb[i]:
					if field in ["x", "y"]:
						if absf(float(pa[i].get(field, 0)) - float(pb[i][field])) > 0.02:
							return false
					elif not _equal(pa[i].get(field), pb[i][field]):
						return false
		elif not _equal(a.get(key), b[key]):
			return false
	return true


static func _combat(runner, data: CoreData, cases: Array) -> void:
	for case: Dictionary in cases:
		var model := Model.new()
		var boss := BattleUnit.new()
		boss.world = model
		boss.setup_boss(data, str(case.boss_type), PackedVector2Array())
		boss.entrance_timer = 0
		boss.max_damage_per_hit = int(case.cap_override)
		boss.status.armor_shred_amount = float(case.shred)
		boss.status.armor_shred_timer = 100 if float(case.shred) > 0.0 else 0
		boss.status.dmg_amp_amount = float(case.amp)
		boss.status.dmg_amp_timer = 100 if float(case.amp) > 0.0 else 0
		boss.defense_boost = bool(case.defense)
		boss.blind_roll_override = float(case.roll)
		var source := BattleUnit.new()
		source.items.catalog = data.items.catalog
		source.kind = BattleUnit.Kind.HERO
		source.team = "blue"
		source.status.blind_timer = 100
		source.status.blind_amount = 0.5
		if bool(case.true_strike):
			source.items.add("sundering_cudgel", source.attack_range, false)
		var before := boss.hp
		boss.take_damage(
			float(case.amount), "blue", str(case.damage_type), source, str(case.school)
		)
		var expected: Dictionary = case.expected
		var ok := (
			_near(boss.hp, float(expected.hp))
			and _near(before - boss.hp, float(expected.dealt))
			and _equal(boss.alive, expected.alive)
			and _equal(boss.defeated, expected.defeated)
			and _near(source.damage_dealt, float(expected.source_dealt))
			and _equal(boss.hurt_flash_timer, expected.hurt_flash)
		)
		runner.check(ok, "boss combat parity: " + str(case.name))
		boss.target = null
		boss.world = null
		source.world = null


static func _round(value: float, digits: int) -> float:
	return HeroBalance.py_round_n(value, digits)


static func _near(a: float, b: float) -> bool:
	return absf(a - b) < 0.0001


static func _equal(a: Variant, b: Variant) -> bool:
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
		for i in range(a.size()):
			if not _equal(a[i], b[i]):
				return false
		return true
	if (a is float or a is int) and (b is float or b is int):
		return absf(float(a) - float(b)) < 0.0001
	return a == b
