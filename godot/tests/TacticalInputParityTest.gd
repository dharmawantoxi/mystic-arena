# FASE 18 — PEMICU UI perintah taktis vs oracle jalur INPUT pygame (seksi
# fixture tactical_input). python tools/test_godot_match_parity.py   (freshness)
# godot --headless --path godot res://tests/TacticalInputParityTest.tscn --quit-after 600
#
# FASE 17 mengunci MANAJER taktik; tes ini mengunci BAGAIMANA input sampai
# ke manajer itu. Dua permukaan pemicu, keduanya direplay lewat JALUR
# PRODUKSI Godot — TIDAK ADA pemanggilan TacticalCommands.hold_start/hold_end
# langsung dari harness:
#
#   * HOTKEY  : InputEventKey (pressed=true/false) dikirim ke
#              Main._unhandled_input -> _on_key / _on_key_release —
#              paritas Game.handle_key / handle_key_up pygame. Hotkey gather
#              memakai posisi mouse + follow_mouse; T memakai selected_tower
#              biru; KEYDOWN digate state "playing", KEYUP tanpa gate.
#   * PANEL   : tombol TacticalBar (HUD) — signal button_down produksi
#              (gate visible/disabled = _gambar_tactical pygame) dan rute
#              pelepasan klik kiri TacticalBar._input (paritas cabang
#              release claimed-touch main.py). Pause = Main._tactical_release_all
#              (paritas hold_end() tanpa nama + held_tac.clear()).
#
# Yang dibandingkan per langkah:
#   calls    : jejak hold_start/hold_end manajer via hook hold_trace (pola
#              harness mouse_override — produksi tetap berjalan normal),
#              dinormalisasi (unit -> uid). Argumen inilah bukti binding.
#   snapshot : closed-world — manager (15 key) + hero biru (pos/alive/
#              follow/target) + game (selected/mouse/state) + panel
#              (visibilitas 5 tombol, mirror _gambar_tactical pygame).
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
# Data+file save di-snapshot lalu dipulihkan di akhir. Piksel panel (chip
# HOLD, warna tombol, font sidepanel) dan SFX BELUM TERUJI.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const NexusScene = preload("res://scenes/base/Nexus.tscn")
const BossScene = preload("res://scenes/boss/Boss.tscn")

## Paritas KEYMAP oracle (pygame K_g/K_f/... = konstanta Godot).
const KEYMAP := {
	"g": KEY_G,
	"f": KEY_F,
	"t": KEY_T,
	"c": KEY_C,
	"b": KEY_B,
	"d": KEY_D,
	"q": KEY_Q,
}

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_before = null
var _main = null
var _bar = null
var _units: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	if FileAccess.file_exists(SaveManager.SAVE_PATH):
		_save_file_before = FileAccess.get_file_as_string(SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("tactical_input"):
		_expect(false, "fixture tactical_input belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["tactical_input"]
	_keys(_fx, ["fps", "scenarios"], "seksi fixture")
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
	# Menu utama default terlihat (MainMenu._ready -> _show(MAIN)); tutup
	# supaya input gameplay tidak tertelan (paritas STATE_GAME pygame).
	var menu = _main._main_menu()
	if menu != null:
		menu.close()

	await get_tree().process_frame
	await get_tree().process_frame
	# Main di luar menu otomatis memulai battle + intro level yang MEMBEKUKAN
	# SceneTree (pola _clear_cinematics FASE 14-17).
	_clear_cinematics()
	var hud = _main.find_child("HUD", true, false)
	_bar = hud.find_child("TacticalBar", true, false)
	_expect(_bar != null, "TacticalBar ada di HUD")

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
	_make_castles()
	_make_units(spec["units"])
	_apply_setup(spec.get("setup", {}))

	# Snapshot PRA-aksi: setup Godot harus identik dengan oracle SEBELUM
	# apa pun terjadi (termasuk visibilitas tombol panel).
	_compare(_snapshot(), spec["pre"], tag + "/pre")

	ParityRng.begin(spec.get("random_script", []))
	var index := 0
	for step in spec["steps"]:
		_keys(step, ["action", "frames", "calls", "snapshot"], "step")
		_run_action(step["action"])
		for _f in range(int(step["frames"])):
			# Satu frame oracle = TacticalCommandManager.update() persis
			# satu panggilan (tanpa Game.update penuh).
			_tactical().update()
		_compare(_drain_calls(), step["calls"], "%s/%d/calls" % [tag, index])
		_compare(_snapshot(), step["snapshot"], "%s/%d" % [tag, index])
		index += 1
	_compare(ParityRng.end(), spec["random_consumed"],
		tag + "/random_consumed")


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
	GameManager.purchased_heroes = []
	GameManager.world_popups.reset()
	GameManager.world_popups.damage_numbers_enabled = false
	GameManager.clear_selection()
	GameManager.close_shop()
	GameManager.selected_slot = -1
	_main.red_towers_destroyed = 0
	_main.true_boss_spawned = true
	_main.active_boss = null
	_main.pending_mini_bosses = []
	_tactical().reset()
	_tactical().set_physics_process(false)
	_tactical().hold_trace_enabled = true
	# Paritas reset() oracle: mouse (0,0) sampai setup/op mengubahnya.
	_tactical().mouse_override = Vector2.ZERO
	if _bar != null:
		_bar.release_all()


## Castle biru/merah (paritas Game.reset pygame: Castle(BLUE_BASE)/
## Castle(RED_BASE) — tactical_commands BLUE/RED_BASE). command_protect_castle
## butuh nexus biru hidup; _uid_of(command_target) butuh keduanya di peta uid.
func _make_castles() -> void:
	for entry in [["castle_blue", "blue", Vector2(100, 620)],
			["castle_red", "red", Vector2(1180, 100)]]:
		var nexus = NexusScene.instantiate()
		nexus.team = str(entry[1])
		nexus.position = entry[2]
		_main.find_child("Containers", true, false).add_child(nexus)
		nexus.set_physics_process(false)
		nexus.attack_timer = 0.0
		_units[str(entry[0])] = nexus


func _make_units(units_spec: Array) -> void:
	for uspec in units_spec:
		_allowed_keys(uspec, ["id", "kind", "team", "x", "y"],
			["type", "hp", "dead", "damage_dealt", "lane", "nexus_level",
				"tower_kind", "tower_type"], "unit spec")
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
		# Unit arena TIDAK di-update sendiri (process off) — paritas oracle
		# yang hanya men-step game.tactical.update().
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
		_units[str(uspec["id"])] = unit


func _apply_setup(setup: Dictionary) -> void:
	_allowed_keys(setup, [], ["selected_hero", "selected_tower", "mouse",
		"state"], "setup")
	if setup.has("selected_hero"):
		GameManager.selected_hero = _units.get(str(setup["selected_hero"])) \
			if setup["selected_hero"] != null else null
	if setup.has("selected_tower"):
		GameManager.selected_tower = _units.get(str(setup["selected_tower"])) \
			if setup["selected_tower"] != null else null
	if setup.has("mouse"):
		_tactical().mouse_override = Vector2(float(setup["mouse"][0]),
			float(setup["mouse"][1]))
	if setup.has("state"):
		GameManager.state = str(setup["state"])


# ══════════════════════════════════════════════════════════
#  AKSI — JALUR PRODUKSI (cermin run_action oracle)
# ══════════════════════════════════════════════════════════

func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _keyup(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = false
	return event


func _run_action(action) -> void:
	if action == null:
		return
	var op := str(action["op"])
	match op:
		"key_down":
			# Jalur produksi lengkap: main.py KEYDOWN -> Game.handle_key.
			_main._unhandled_input(_key(int(KEYMAP[str(action["key"])])))
		"key_up":
			# Jalur produksi: main.py KEYUP -> Game.handle_key_up (tanpa
			# gate state — paritas InputHandler.handle_key_up).
			_main._unhandled_input(_keyup(int(KEYMAP[str(action["key"])])))
		"panel_down":
			# Jalur produksi: sentuhan tombol panel — gate visible/disabled
			# (mirror hit_test + btn.visible pygame) LALU signal button_down
			# yang tersambung ke Main._tactical_panel_press.
			if _bar == null:
				return
			_bar._refresh()
			var btn: Button = _bar._buttons.get(str(action["action"]))
			if btn != null and btn.visible and not btn.disabled:
				btn.button_down.emit()
		"panel_up":
			# Jalur produksi: pelepasan klik kiri dirutekan TacticalBar._input
			# (paritas cabang release claimed-touch main.py — tidak peduli
			# apa yang kini ada di bawah kursor).
			if _bar == null:
				return
			var ev := InputEventMouseButton.new()
			ev.button_index = MOUSE_BUTTON_LEFT
			ev.pressed = false
			_bar._input(ev)
		"pause_release":
			# Pernyataan yang sama dijalankan _toggle_pause saat membekukan
			# game (paritas main.py:479-486: hold_end() + held_tac.clear()).
			_main._tactical_release_all()
		"set_mouse":
			_tactical().mouse_override = Vector2(float(action["x"]),
				float(action["y"]))
		"set_state":
			GameManager.state = str(action["state"])
		"set_selected_hero":
			GameManager.selected_hero = _units.get(str(action["unit"])) \
				if action.get("unit") != null else null
		"set_selected_tower":
			GameManager.selected_tower = _units.get(str(action["unit"])) \
				if action.get("unit") != null else null
		"kill":
			var victim = _units[str(action["unit"])]
			victim.is_dead = true
			victim.hp = 0.0
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
		_:
			_expect(false, "op asing " + op)


## Jejak hold_start/hold_end produksi (hook hold_trace) — ambil & kosongkan,
# dinormalisasi: argumen Node (tower) -> uid agar bisa dibandingkan JSON.
func _drain_calls() -> Array:
	var out: Array = []
	for entry in _tactical().hold_trace:
		if str(entry[0]) == "hold_start":
			var args: Array = []
			for a in entry[2]:
				if a is Node:
					args.append(_uid_of(a))
				else:
					args.append(a)
			out.append(["hold_start", entry[1], args,
				bool(entry[3]), entry[4]])
		else:
			out.append(["hold_end", entry[1]])
	_tactical().hold_trace.clear()
	return out


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
	if _bar != null:
		_bar._refresh()
	return {
		"manager": _manager_state(),
		"heroes": _hero_states(),
		"game": _game_state(),
		"panel": _bar.panel_available() if _bar != null else {},
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
	return {
		"active_command": tac.active_command,
		"command_timer": int(tac.command_timer),
		"command_target": _uid_of(tac.command_target),
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
			"follow_target": _uid_of(unit.get("follow_target")),
			"target": _uid_of(unit.get("target")),
		}
	return out


func _game_state() -> Dictionary:
	var m: Vector2 = _tactical()._mouse_pos()
	return {
		"selected_hero": _uid_of(GameManager.selected_hero),
		"selected_tower": _uid_of(GameManager.selected_tower),
		"mouse": [int(m.x), int(m.y)],
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
	GameManager.close_shop()
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
		print("[TacticalInputParityTest] FAIL: " + message)
		push_error("[TacticalInputParityTest] " + message)


func _finish() -> void:
	_clear_case()
	if is_instance_valid(_main):
		if is_instance_valid(_main._tactical):
			_main._tactical.hold_trace_enabled = false
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
		print("[TacticalInputParityTest] PASS: %d checks pemicu UI taktis vs oracle pygame" % _checks)
	else:
		print("[TacticalInputParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
