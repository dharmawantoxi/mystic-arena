# FASE 17 — seluruh daftar headless tactical_commands direplay, bukan subset /
# pemeriksaan string sumber. Oracle = TacticalCommandManager pygame ASLI
# (tactical_commands.py, 1051 baris, 28 fungsi) yang di-step manual per frame
# dengan unit betulan, tanpa Game.update penuh.
#
# Godot: Main/HUD/Hero/Minion/Tower/Nexus/Boss SUNGGUHAN dan perintah
# dijalankan lewat JALUR PRODUKSI: Main._tactical (TacticalCommands.gd,
# dibuat di Main._ready seperti _ai) + Hero.move_to/follow_target/target
# + GameManager (selected_hero, state, wave, owned_heroes, nexus).
# TIDAK ADA pemanggilan register_* manual dan TIDAK ADA set state taktik
# langsung: active_command/timer/cooldown/feedback/hold/push/auto boleh
# berubah HANYA sebagai akibat command_* / hold_* / update() produksi.
#
# Roll 20% auto-attack-boss (satu-satunya situs RNG modul, paritas
# tactical_commands.py::_auto_evaluate_protect) lewat ParityRng: harness
# memasang script fixture per skenario dan membandingkan yang terkonsumsi.
# Dua seed pygame wajib identik (guard sisi oracle).
#
# Snapshot closed-world per langkah: manager (20 key: perintah, timer,
# cooldown, gather_point, feedback, hold_*, push, auto_check_timer, warna,
# status, hold_args), hero biru (pos, alive, destination+auto, follow,
# target, retreat, range), semua unit + castle (pos, hp, max_hp, alive,
# team, name, damage_dealt), dan game (selected, mouse, wave, state).
#
# Jalur mati yang ikut dikunci: push gather ONE-SHOT tidak pernah picu
# (visual 150 frame kedaluwarsa sebelum timer sentuh 300); push hanya
# hidup via HOLD (hold_elapsed >= 240 + refresh tiap 30 frame).
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
# Data+file save di-snapshot lalu dipulihkan di akhir. Piksel dan SFX
# (lingkaran gather point, teks feedback, ui_click/hero_skill) BELUM
# TERUJI — yang dibandingkan hanya state taktik.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const NexusScene = preload("res://scenes/base/Nexus.tscn")
const BossScene = preload("res://scenes/boss/Boss.tscn")

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_before = null
var _main = null
var _units: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	if FileAccess.file_exists(SaveManager.SAVE_PATH):
		_save_file_before = FileAccess.get_file_as_string(SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("tactical_commands"):
		_expect(false, "fixture tactical_commands belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["tactical_commands"]
	_keys(_fx, ["fps", "constants", "command_colors", "scenarios"], "seksi fixture")
	_compare(GameManager.FPS, _fx["fps"], "FPS")

	GameManager.set_process(false)
	GameManager.in_menu = false
	GameManager.state = "playing"
	GameManager.waves_enabled = false
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	_main._ai.set_process(false)
	_main._tactical.set_physics_process(false)
	_main.find_child("Containers", true, false).process_mode = \
		Node.PROCESS_MODE_DISABLED

	await get_tree().process_frame
	await get_tree().process_frame
	# Main di luar menu otomatis memulai battle + intro level yang MEMBEKUKAN
	# SceneTree (pola _clear_cinematics FASE 14/15/16).
	_clear_cinematics()

	for spec in _fx["scenarios"]:
		_test_scenario(spec)

	_finish()


func _tactical():
	return _main._tactical if _main != null else null


# ══════════════════════════════════════════════════════════
#  SKENARIO
# ══════════════════════════════════════════════════════════

func _test_scenario(spec: Dictionary) -> void:
	_keys(spec, ["name", "units", "setup", "random_script", "random_consumed",
		"pre", "steps"], "scenario")
	var tag := str(spec["name"])
	_reset()
	_make_castles(spec.get("setup", {}))
	_make_units(spec["units"])
	_apply_setup(spec.get("setup", {}))

	# Snapshot PRA-aksi: setup Godot harus identik dengan oracle SEBELUM
	# apa pun terjadi, supaya kegagalan menunjuk ke setup, bukan taktik.
	_compare(_snapshot(), spec["pre"], tag + "/pre")

	ParityRng.begin(spec.get("random_script", []))
	var index := 0
	for step in spec["steps"]:
		_keys(step, ["action", "frames", "result", "snapshot"], "step")
		var res = _run_action(step["action"])
		for _f in range(int(step["frames"])):
			# Satu frame oracle = TacticalCommandManager.update() persis
			# satu panggilan (tanpa Game.update penuh).
			_tactical().update()
		_compare(res, step["result"], "%s/%d/result" % [tag, index])
		_compare(_snapshot(), step["snapshot"], "%s/%d" % [tag, index])
		index += 1
	_compare(ParityRng.end(), spec["random_consumed"],
		tag + "/random_consumed")

	# Guard eksplisit perilaku kunci (redundan dengan snapshot, tapi
	# menunjuk langsung ke semantik bila closed-world gagal).
	if tag == "gather_cooldown_state_gate":
		_compare(spec["steps"][1]["result"], false, tag + " cooldown memblokir")
		_compare(spec["steps"][3]["result"], false, tag + " victory memblokir")
		_compare(spec["steps"][5]["result"], true, tag + " post-cooldown bisa")
	elif tag == "hold_tap_short":
		_expect(float(spec["steps"][1]["snapshot"]["manager"]["command_timer"]) > 30.0,
			tag + " TAP tidak dipotong")
	elif tag == "hold_long_truncate":
		_compare(float(spec["steps"][1]["snapshot"]["manager"]["command_timer"]), 30.0,
			tag + " HOLD dipotong ke 30")
	elif tag == "gather_oneshot_push_dead_arrived":
		_compare(spec["steps"][spec["steps"].size() - 1]["snapshot"]["manager"]["gather_push_fired"],
			false, tag + " push one-shot mati")
	elif tag == "hold_gather_push_lock":
		_compare(spec["steps"][spec["steps"].size() - 2]["snapshot"]["manager"]["gather_push_fired"],
			true, tag + " push HOLD hidup")


# ══════════════════════════════════════════════════════════
#  SETUP
# ══════════════════════════════════════════════════════════

func _reset() -> void:
	_clear_case()
	GameManager.gold_per_second = 0.0
	GameManager._gold_timer = 0.0
	GameManager._gold_income_milli = 0
	GameManager.wave_number = 1
	GameManager.combo.reset()
	GameManager._combo_accum = 0.0
	GameManager._hero_respawn_timers.clear()
	GameManager.state = "playing"
	GameManager.in_menu = false
	GameManager.set_paused(false)
	GameManager.is_replay = false
	GameManager.level_number = 1
	# Input catch-up DI-PIN kosong, paritas `game.purchased_heroes = []`
	# di oracle (jebakan FASE 13/16: stat hero mengikuti sisa save).
	GameManager.purchased_heroes = []
	GameManager.world_popups.reset()
	GameManager.world_popups.damage_numbers_enabled = false
	GameManager.clear_selection()
	_main.red_towers_destroyed = 0
	_main.true_boss_spawned = true
	_main.active_boss = null
	_main.pending_mini_bosses = []
	_tactical().reset()
	_tactical().set_physics_process(false)
	# Paritas reset() oracle: mouse (0,0) sampai setup/op mengubahnya.
	_tactical().mouse_override = Vector2.ZERO


func _make_castles(setup: Dictionary) -> void:
	var consts: Dictionary = _fx["constants"]
	var blue_at: Array = consts["blue_base"]
	var red_at: Array = consts["red_base"]
	for entry in [["castle_blue", "blue", blue_at], ["castle_red", "red", red_at]]:
		var nexus = NexusScene.instantiate()
		nexus.team = str(entry[1])
		nexus.position = Vector2(float(entry[2][0]), float(entry[2][1]))
		_main.find_child("Containers", true, false).add_child(nexus)
		nexus.set_physics_process(false)
		nexus.attack_timer = 0.0
		_units[str(entry[0])] = nexus
	# castle_hp / castle_dead setup (kunci ancaman auto-protect & fallback).
	var hp_over: Dictionary = setup.get("castle_hp", {})
	for key in hp_over:
		_units[str(key)].hp = float(hp_over[key])
	for key in setup.get("castle_dead", []):
		_units[str(key)].is_dead = true
		_units[str(key)].hp = 0.0


func _make_units(units_spec: Array) -> void:
	for uspec in units_spec:
		_allowed_keys(uspec, ["id", "kind", "team", "x", "y"],
			["type", "hp", "dead", "retreating", "dest_auto", "dest",
			"damage_dealt", "lane", "nexus_level", "tower_kind", "tower_type"],
			"unit spec")
		var unit = null
		match str(uspec["kind"]):
			"hero":
				unit = HeroScene.instantiate()
				unit.hero_type = str(uspec["type"])
				unit.team = str(uspec["team"])
			"minion":
				unit = MinionScene.instantiate()
				unit.minion_type = str(uspec["type"])
				unit.team = str(uspec["team"])
			"tower":
				unit = TowerScene.instantiate()
				unit.team = str(uspec["team"])
				unit.tower_kind = str(uspec.get("tower_kind", "outer"))
			"boss":
				unit = BossScene.instantiate()
				unit.boss_type = str(uspec.get("type", "gornak"))
				unit.team = str(uspec["team"])
			_:
				_expect(false, "jenis unit asing " + str(uspec["kind"]))
				continue
		unit.position = Vector2(float(uspec["x"]), float(uspec["y"]))
		_main.find_child("Containers", true, false).add_child(unit)
		# Unit arena TIDAK di-update sendiri (process off): satu-satunya
		# yang di-step adalah TacticalCommands.update() — paritas oracle
		# yang tidak menjalankan Game.update penuh.
		unit.set_physics_process(false)
		match str(uspec["kind"]):
			"tower":
				unit.shield = 0.0
				if uspec.has("tower_type"):
					_expect(unit.upgrade(str(uspec["tower_type"])),
						"upgrade menara " + str(uspec["tower_type"]))
			"minion":
				unit.regen_per_second = 0.0
				unit.attack_timer = 0.0
			"boss":
				_main.active_boss = unit
			_:
				unit.attack_timer = 0.0
		if uspec.has("hp"):
			unit.hp = float(uspec["hp"])
		if uspec.has("damage_dealt"):
			unit.damage_dealt = float(uspec["damage_dealt"])
		if bool(uspec.get("dead", false)):
			unit.is_dead = true
			unit.hp = 0.0
		if uspec.has("retreating"):
			unit.is_retreating = bool(uspec["retreating"])
			unit.destination_auto = bool(uspec.get("dest_auto", false))
			if uspec.get("dest") != null:
				unit.destination = Vector2(float(uspec["dest"][0]),
					float(uspec["dest"][1]))
			else:
				unit.destination = Vector2.INF
		_units[str(uspec["id"])] = unit


func _apply_setup(setup: Dictionary) -> void:
	_allowed_keys(setup, [],
		["selected_hero", "selected_tower", "mouse", "wave", "state",
		"castle_hp", "castle_dead"], "setup")
	if setup.has("selected_hero"):
		GameManager.selected_hero = _units.get(str(setup["selected_hero"])) \
			if setup["selected_hero"] != null else null
	if setup.has("selected_tower"):
		GameManager.selected_tower = _units.get(str(setup["selected_tower"])) \
			if setup["selected_tower"] != null else null
	if setup.has("mouse"):
		_tactical().mouse_override = Vector2(float(setup["mouse"][0]),
			float(setup["mouse"][1]))
	if setup.has("wave"):
		GameManager.wave_number = int(setup["wave"])
	if setup.has("state"):
		GameManager.state = str(setup["state"])


# ══════════════════════════════════════════════════════════
#  AKSI (cermin run_action oracle)
# ══════════════════════════════════════════════════════════

func _run_action(action) -> Variant:
	if action == null:
		return null
	var op := str(action["op"])
	var tac = _tactical()
	match op:
		"gather":
			if action.get("x") == null or action.get("y") == null:
				return bool(tac.command_gather(INF, INF,
					bool(action.get("silent", false))))
			return bool(tac.command_gather(float(action["x"]),
				float(action["y"]), bool(action.get("silent", false))))
		"protect_tower":
			var tower = _units.get(str(action["tower"])) \
				if action.get("tower") != null else null
			return bool(tac.command_protect_tower(tower,
				bool(action.get("silent", false))))
		"protect_castle":
			return bool(tac.command_protect_castle(
				bool(action.get("silent", false))))
		"attack_boss":
			return bool(tac.command_attack_boss(
				bool(action.get("silent", false))))
		"attack_dealer":
			return bool(tac.command_attack_damage_dealer(
				bool(action.get("silent", false))))
		"hold_start":
			var args: Array = []
			for a in action.get("args", []):
				if a is String and _units.has(str(a)):
					args.append(_units[str(a)])
				else:
					args.append(a)
			return bool(tac.hold_start(str(action["name"]), args,
				bool(action.get("follow_mouse", false))))
		"hold_end":
			tac.hold_end(action.get("name"))
			return null
		"set_pos":
			_units[str(action["unit"])].position = Vector2(
				float(action["x"]), float(action["y"]))
			return null
		"set_hp":
			_units[str(action["unit"])].hp = float(action["hp"])
			return null
		"set_damage":
			_units[str(action["unit"])].damage_dealt = float(action["damage"])
			return null
		"set_mouse":
			tac.mouse_override = Vector2(float(action["x"]),
				float(action["y"]))
			return null
		"set_wave":
			GameManager.wave_number = int(action["n"])
			return null
		"set_state":
			GameManager.state = str(action["state"])
			return null
		"set_selected_hero":
			GameManager.selected_hero = _units.get(str(action["unit"])) \
				if action.get("unit") != null else null
			return null
		"set_selected_tower":
			GameManager.selected_tower = _units.get(str(action["unit"])) \
				if action.get("unit") != null else null
			return null
		"kill":
			var victim = _units[str(action["unit"])]
			victim.is_dead = true
			victim.hp = 0.0
			return null
		"revive":
			var unit = _units[str(action["unit"])]
			unit.is_dead = false
			if action.get("hp") != null:
				unit.hp = float(action["hp"])
			else:
				unit.hp = float(unit.get("max_hp"))
			if "boss_type" in unit and _main.active_boss != unit:
				_main.active_boss = unit
			return null
		"spawn_boss":
			var uid := str(action.get("unit", "boss0"))
			var boss = BossScene.instantiate()
			boss.boss_type = str(action.get("type", "gornak"))
			boss.team = str(action.get("team", "red"))
			boss.position = Vector2(float(action.get("x", 700.0)),
				float(action.get("y", 400.0)))
			_main.find_child("Containers", true, false).add_child(boss)
			boss.set_physics_process(false)
			if action.has("hp"):
				boss.hp = float(action["hp"])
			_units[uid] = boss
			_main.active_boss = boss
			return uid
		"helper_count":
			return int(tac._count_enemies_near(float(action["x"]),
				float(action["y"]), float(action["radius"])))
		"helper_nearest":
			return _uid_of(tac._find_nearest_enemy_target(
				float(action["x"]), float(action["y"])))
		"helper_threatened":
			return _uid_of(tac._find_most_threatened_tower())
		"helper_dealer":
			return _uid_of(tac._find_enemy_damage_dealer())
		"can_issue":
			return bool(tac.can_issue())
		_:
			_expect(false, "op asing " + op)
			return null


func _uid_of(node) -> Variant:
	if node == null or not is_instance_valid(node):
		return null
	for uid in _units:
		if _units[uid] == node:
			return uid
	_expect(false, "node tak dikenal di peta uid: " + str(node))
	return null


# ══════════════════════════════════════════════════════════
#  SNAPSHOT CLOSED-WORLD
# ══════════════════════════════════════════════════════════

func _snapshot() -> Dictionary:
	return {
		"manager": _manager_state(),
		"heroes": _hero_states(),
		"units": _unit_states(),
		"game": _game_state(),
	}


func _r4(v: float) -> float:
	return snappedf(float(v), 0.0001)


func _pt(p) -> Variant:
	if p == null:
		return null
	if p is Vector2 and p == Vector2.INF:
		return null
	if p is Vector2:
		return [_r4(p.x), _r4(p.y)]
	return [_r4(p[0]), _r4(p[1])]


func _col8(c: Color) -> Array:
	return [roundi(c.r * 255.0), roundi(c.g * 255.0), roundi(c.b * 255.0)]


func _manager_state() -> Dictionary:
	var tac = _tactical()
	var hold_args: Array = []
	for a in tac.hold_args:
		if a is Node:
			hold_args.append(_uid_of(a))
		else:
			hold_args.append(a)
	return {
		"active_command": tac.active_command,
		"command_timer": int(tac.command_timer),
		"command_target": _uid_of(tac.command_target),
		"command_origin": tac.command_origin,
		"cooldown": int(tac.cooldown),
		"gather_point": _pt(tac.gather_point),
		"gather_point_timer": int(tac.gather_point_timer),
		"feedback_text": str(tac.feedback_text),
		"feedback_timer": int(tac.feedback_timer),
		"feedback_color": _col8(tac.feedback_color),
		"held_command": tac.held_command,
		"hold_follow_mouse": bool(tac.hold_follow_mouse),
		"hold_elapsed": int(tac.hold_elapsed),
		"hold_has_fired": bool(tac.hold_has_fired),
		"gather_push_fired": bool(tac.gather_push_fired),
		"auto_check_timer": int(tac.auto_check_timer),
		"command_color": _col8(tac._get_command_color()),
		"status_text": str(tac.get_status_text()),
		"hold_args": hold_args,
		"hold_kwargs": (tac.hold_kwargs as Dictionary).duplicate(),
	}


func _hero_states() -> Dictionary:
	var out := {}
	for uid in _units:
		var unit = _units[uid]
		if not ("hero_type" in unit):
			continue
		if str(unit.get("team")) != "blue":
			continue
		out[uid] = {
			"x": _r4((unit as Node2D).position.x),
			"y": _r4((unit as Node2D).position.y),
			"alive": not bool(unit.get("is_dead")),
			"destination": _pt(unit.get("destination")),
			"destination_auto": bool(unit.get("destination_auto")),
			"follow_target": _uid_of(unit.get("follow_target")),
			"target": _uid_of(unit.get("target")),
			"is_retreating": bool(unit.get("is_retreating")),
			"range": float(unit.get("attack_range")),
		}
	return out


func _unit_states() -> Dictionary:
	var out := {}
	for uid in _units:
		var unit = _units[uid]
		var dealt := 0
		if "damage_dealt" in unit:
			dealt = int(float(unit.get("damage_dealt")))
		out[uid] = {
			"x": _r4((unit as Node2D).position.x),
			"y": _r4((unit as Node2D).position.y),
			"hp": float(unit.get("hp")),
			"max_hp": float(unit.get("max_hp")),
			"alive": not bool(unit.get("is_dead")),
			"team": str(unit.get("team")),
			"name": _tactical().target_name(unit),
			"damage_dealt": dealt,
		}
	return out


func _game_state() -> Dictionary:
	var m: Vector2 = _tactical()._mouse_pos()
	return {
		"selected_hero": _uid_of(GameManager.selected_hero),
		"selected_tower": _uid_of(GameManager.selected_tower),
		"mouse": [int(m.x), int(m.y)],
		"wave": int(GameManager.wave_number),
		"state": str(GameManager.state),
	}


# ══════════════════════════════════════════════════════════
#  BERSIHKAN
# ══════════════════════════════════════════════════════════

func _clear_cinematics() -> void:
	for node in get_tree().get_nodes_in_group("cinematic"):
		if is_instance_valid(node):
			if node.has_method("finish"):
				node.finish()
			node.free()
	if is_instance_valid(_main):
		_main._level_intro = null
		_main._boss_banner = null
	get_tree().paused = false
	GameManager.set_paused(false)


func _clear_case() -> void:
	if not is_instance_valid(_main):
		return
	Engine.time_scale = 1.0
	_clear_cinematics()
	_main.active_boss = null
	_main.pending_mini_bosses = []
	_main.true_boss_spawned = true
	GameManager._hero_respawn_timers.clear()
	GameManager.clear_selection()
	for group in ["heroes", "bosses", "minions", "towers", "nexus",
			"bullets", "skill_projectiles", "floating_text"]:
		for node in get_tree().get_nodes_in_group(group):
			node.free()
	for node in _main.find_child("FX", true, false).get_children():
		node.free()
	_units.clear()
	GameManager.blue_nexus = null
	GameManager.red_nexus = null


# ══════════════════════════════════════════════════════════
#  PERBANDINGAN CLOSED-WORLD
# ══════════════════════════════════════════════════════════

func _allowed_keys(dict: Dictionary, required: Array, optional: Array,
		tag: String) -> void:
	for key in required:
		_expect(dict.has(key), tag + " wajib punya " + str(key))
	for key in dict:
		_expect(required.has(key) or optional.has(key),
			tag + " key asing " + str(key))


func _keys(dict: Dictionary, wanted: Array, tag: String) -> void:
	var actual := dict.keys()
	actual.sort()
	var keys := wanted.duplicate()
	keys.sort()
	_compare(actual, keys, tag + " keys")


func _compare(actual, wanted, tag: String) -> void:
	if actual is Dictionary and wanted is Dictionary:
		_keys_only(actual, wanted, tag)
		for key in wanted:
			if actual.has(key):
				_compare(actual[key], wanted[key], tag + "/" + str(key))
	elif actual is Array and wanted is Array:
		_expect(actual.size() == wanted.size(),
			"%s length %d != %d" % [tag, actual.size(), wanted.size()])
		for i in range(mini(actual.size(), wanted.size())):
			_compare(actual[i], wanted[i], "%s/%d" % [tag, i])
	elif (actual is int or actual is float) \
			and (wanted is int or wanted is float):
		_expect(absf(float(actual) - float(wanted)) <= 0.000001,
			"%s: %s != %s" % [tag, actual, wanted])
	else:
		_expect(typeof(actual) == typeof(wanted) and actual == wanted,
			"%s: %s != %s" % [tag, actual, wanted])


func _keys_only(actual: Dictionary, wanted: Dictionary, tag: String) -> void:
	var a := actual.keys()
	var b := wanted.keys()
	a.sort()
	b.sort()
	_expect(a == b, "%s keys %s != %s" % [tag, a, b])


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		print("[TacticalCommandsParityTest] FAIL: " + message)
		push_error("[TacticalCommandsParityTest] " + message)


func _finish() -> void:
	_clear_case()
	if is_instance_valid(_main):
		_main.free()
	SaveManager.data = _save_before
	if _save_file_before == null:
		if FileAccess.file_exists(SaveManager.SAVE_PATH):
			DirAccess.remove_absolute(SaveManager.SAVE_PATH)
	else:
		var f := FileAccess.open(SaveManager.SAVE_PATH, FileAccess.WRITE)
		f.store_string(_save_file_before)
	GameManager.world_popups.reset()
	GameManager.world_popups.damage_numbers_enabled = true
	GameManager.bind_unlocked_bosses()
	GameManager.purchased_heroes = []
	GameManager.unlocked_bosses = []
	GameManager.bosses_defeated_this_match = []
	GameManager.set_process(true)
	GameManager.waves_enabled = true
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	get_tree().paused = false
	Engine.time_scale = 1.0
	if _failures == 0:
		print("[TacticalCommandsParityTest] PASS: %d checks perintah taktis vs oracle pygame" % _checks)
	else:
		print("[TacticalCommandsParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
