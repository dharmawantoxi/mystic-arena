# BossSmartAIParityTest — paritas smart-AI Q/W/E/R 79 boss vs oracle Pygame.
#
# Fixture `match_parity.json["boss_smart_ai"]` dihasilkan tools/
# test_godot_match_parity.py dengan MENJALANKAN Boss.update pygame asli
# frame demi frame melawan probe deterministik (3 skenario × 79 boss:
# gerombolan + HP turun bertahap, duo HP rendah, target tunggal di tepi
# jangkauan). Tes ini memutar ulang skenario yang sama pada node Boss.gd
# asli (BossKit.gd hasil transpile) dan membandingkan jejak event per frame:
# cast skill, damage, heal, slow, kunci serangan, knockback, dash, enrage,
# facing, speed/damage buff, sampai state kit final.
#
# Serangan dasar dimatikan di KEDUA sisi (oracle & replay) — kadens dasar
# sudah diuji BossCoreParityTest; jejak ini mengisolasi perilaku kit.
#
# godot --headless --path godot res://tests/BossSmartAIParityTest.tscn --quit-after 1800
# Require "[BossSmartAIParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const BossScene = preload("res://scenes/boss/Boss.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
var _error_messages: Array[String] = []
var _boss_count: int = 0
var _event_checks: int = 0


## Status probe: shim perekam apply_slow (amount, durasi FRAME) — dipanggil
## Boss.gd.kit_apply_slow di titik yang sama dengan probe oracle pygame.
class ProbeStatus extends RefCounted:
	var slow_records: Array = []

	func apply_slow(amount: float, duration: float) -> void:
		slow_records.append([amount, duration * 60.0])

	func has_buff(_id: String) -> bool:
		return false

	func can_be_targeted() -> bool:
		return true

	func miss_chance(_is_physical: bool) -> float:
		return 0.0

	func incoming_mult() -> float:
		return 1.0

	func armor_delta() -> float:
		return 0.0


## Musuh dummy — antarmuka yang disentuh CombatSystem/BossKit:
## team/hp/max_hp/armor/magic_resist/is_dead/radius/attack_timer/move_speed/
## status/combat_timer. Group "minions" supaya ditemukan enemies_of().
class Probe extends Node2D:
	var team := "blue"
	var hp := 1000000000.0
	var max_hp := 1000000000.0
	var armor := 0.0
	var magic_resist := 0.0
	var is_dead := false
	var radius := 16.0
	var attack_timer := 0.0
	var move_speed := 120.0
	var combat_timer := 0.0
	var combat_reset := 5.0
	var status: ProbeStatus = ProbeStatus.new()


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not _fixture.has("boss_smart_ai"):
		push_error("[BossSmartAIParityTest] fixture boss_smart_ai belum ada — "
			+ "jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	for row in _fixture["boss_smart_ai"]["bosses"]:
		_test_boss(str(row["boss_type"]), row)
		if _failures > 40:
			_error_messages.append("[BossSmartAIParityTest] berhenti awal: "
				+ "terlalu banyak kegagalan")
			break
	_finish()


# ══════════════════════════════════════════════════════════
#  REPLAY SKENARIO
# ══════════════════════════════════════════════════════════

func _test_boss(boss_type: String, row: Dictionary) -> void:
	for sc_name in row["scenarios"]:
		var sc: Dictionary = row["scenarios"][sc_name]
		_replay_and_compare(boss_type, str(sc_name), sc)
	_boss_count += 1


## Putar ulang satu skenario pada node Boss asli dan bandingkan jejaknya.
func _replay_and_compare(boss_type: String, sc_name: String, sc: Dictionary) -> void:
	var boss = BossScene.instantiate()
	boss.boss_type = boss_type
	boss.team = "red"
	boss.position = Vector2(600, 400)
	add_child(boss) # _ready jalan sinkron: BossDB + kit DEFAULT + visual
	boss.set_physics_process(false)
	boss.entrance_timer = 0.0
	boss.attack_timer = 1.0e9 # matikan serangan dasar (sama seperti oracle)
	boss.status.clear()
	# Emulasi instance segar pygame: oracle membaca active_skill_timer via
	# getattr(..., -1) — belum ada atribut sebelum kit init-once berjalan.
	# DEFAULT_KIT men-seed 30; -1 membuat snapshot awal identik oracle
	# (kit_ready=false tetap; init block frame 0 menimpa nilai ini duluan).
	boss.kit["kit_ready"] = false
	boss.kit["active_skill_timer"] = -1

	var probes: Array = []
	for off in sc["probes"]:
		var p := Probe.new()
		p.position = Vector2(600.0 + float(off[0]), 400.0 + float(off[1]))
		p.add_to_group("minions")
		add_child(p)
		probes.append(p)

	# skrip HP oracle: [[frame, rasio], ...] atau mode string
	var hp_mode := ""
	var hp_map := {}
	var hp_raw = sc["hp_script"]
	if hp_raw is String:
		hp_mode = str(hp_raw)
	else:
		for pair in hp_raw:
			hp_map[int(pair[0])] = float(pair[1])

	var frames := int(sc["frames"])
	var events: Array = []
	var prev := _snapshot(boss, probes)

	for frame in range(frames):
		if hp_mode == "low":
			boss.hp = float(int(boss.max_hp * 0.28))
		elif hp_mode == "full":
			boss.hp = float(int(boss.max_hp * 1.0))
		elif hp_map.has(frame):
			boss.hp = float(int(boss.max_hp * hp_map[frame]))
		boss._physics_process(1.0 / 60.0)
		_diff(boss, probes, prev, frame, events)
		prev = _snapshot(boss, probes)

	_compare_events(boss_type, sc_name, sc["events"], events)
	_compare_final(boss_type, sc_name, sc["final"], boss, probes)

	for p in probes:
		p.queue_free()
	boss.queue_free()


func _snapshot(boss, probes: Array) -> Dictionary:
	var atk: Array = []
	var xy: Array = []
	var php: Array = []
	for p in probes:
		atk.append(p.attack_timer)
		xy.append(Vector2(p.global_position.x, p.global_position.y))
		php.append(p.hp)
	return {
		"hp": boss.hp,
		"pos": Vector2(boss.global_position.x, boss.global_position.y),
		"ast": float(boss.kit.get("active_skill_timer", -1)),
		"spd": boss.move_speed / 60.0,
		"dmg": boss.damage,
		"face": boss.facing,
		"enr": boss.is_enraged,
		"probe_hp": php,
		"probe_atk": atk,
		"probe_xy": xy,
	}


## Diff state per frame — CERMIN persis _run_smart_scenario pygame.
func _diff(boss, probes: Array, prev: Dictionary, frame: int, out: Array) -> void:
	if boss.hp != prev["hp"]:
		out.append(["bhp", frame, roundf(float(boss.hp), 3)])
	var pos: Vector2 = boss.global_position
	if absf(pos.x - prev["pos"].x) > 0.001 or absf(pos.y - prev["pos"].y) > 0.001:
		out.append(["bmove", frame, roundf(pos.x, 3), roundf(pos.y, 3)])
	var ast := float(boss.kit.get("active_skill_timer", -1))
	if ast > prev["ast"]:
		# nyxareth memakai angka combo (1..4); drakar/gorath merekam cast
		# null saat init-once menaikkan timer 0 — kanonialisasi supaya
		# JSON float 4.0 == int 4 dan null == null di kedua sisi.
		out.append(["cast", frame, _canon(boss.kit.get("active_skill", null))])
	if boss.move_speed / 60.0 != prev["spd"]:
		out.append(["bspd", frame, roundf(boss.move_speed / 60.0, 5)])
	if boss.damage != prev["dmg"]:
		out.append(["bdmg", frame, int(boss.damage)])
	if boss.facing != prev["face"]:
		out.append(["bface", frame, int(boss.facing)])
	if boss.is_enraged and not prev["enr"]:
		out.append(["enrage", frame])
	for i in probes.size():
		var p: Probe = probes[i]
		var d := float(prev["probe_hp"][i]) - p.hp
		if d > 0:
			out.append(["dmg", frame, i, roundf(d, 3)])
		if p.attack_timer != prev["probe_atk"][i]:
			out.append(["alock", frame, i, roundf(p.attack_timer * 60.0, 3)])
		var xy: Vector2 = prev["probe_xy"][i]
		if p.global_position.x != xy.x or p.global_position.y != xy.y:
			out.append(["emove", frame, i,
				roundf(p.global_position.x, 3), roundf(p.global_position.y, 3)])
		for rec in p.status.slow_records:
			out.append(["slow", frame, i, float(rec[0]), roundf(float(rec[1]), 3)])
		p.status.slow_records.clear()


# ══════════════════════════════════════════════════════════
#  PERBANDINGAN
# ══════════════════════════════════════════════════════════

## Bandingkan jejak event per frame. Urutan event DALAM satu frame tidak
## dinilai (urutan group node bisa berbeda) — di-bucket per frame lalu
## diurutkan secara deterministik.
func _compare_events(boss_type: String, sc_name: String,
		expected: Array, actual: Array) -> void:
	_checks += 1
	_event_checks += expected.size()
	var eb := _bucket(expected)
	var ab := _bucket(actual)
	var frames_e := eb.keys()
	frames_e.sort()
	var tag := "%s/%s" % [boss_type, sc_name]
	if eb.size() != ab.size():
		_fail(tag, "jumlah frame berbeda: oracle %d vs replay %d" % [eb.size(), ab.size()])
	for f in frames_e:
		var want: Array = eb[f]
		var got: Array = ab.get(f, [])
		var ws := _sorted_events(want)
		var gs := _sorted_events(got)
		if ws.size() != gs.size():
			_fail(tag, "frame %d: %d event oracle vs %d replay (%s vs %s)"
				% [f, ws.size(), gs.size(), str(ws), str(gs)])
			continue
		for i in ws.size():
			if not _event_eq(ws[i], gs[i]):
				_fail(tag, "frame %d: event beda: oracle %s vs replay %s"
					% [f, str(ws[i]), str(gs[i])])


func _bucket(events: Array) -> Dictionary:
	var out := {}
	for e in events:
		var f := int(e[1])
		if not out.has(f):
			out[f] = []
		out[f].append(e)
	return out


func _sorted_events(events: Array) -> Array:
	var out := events.duplicate()
	out.sort_custom(func(a, b): return _event_key(a) < _event_key(b))
	return out


func _event_key(e) -> String:
	var parts: Array = []
	for v in e:
		parts.append(str(v))
	return "|".join(parts)


func _event_eq(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	if str(a[0]) != str(b[0]) or int(a[1]) != int(b[1]):
		return false
	match str(a[0]):
		"bhp":
			return _near_v(a[2], b[2], 0.51)
		"dmg":
			return int(a[2]) == int(b[2]) and _near_v(a[3], b[3], 0.51)
		"bmove":
			return _near_v(a[2], b[2], 0.02) and _near_v(a[3], b[3], 0.02)
		"emove":
			return int(a[2]) == int(b[2]) \
				and _near_v(a[3], b[3], 0.02) and _near_v(a[4], b[4], 0.02)
		"alock":
			return int(a[2]) == int(b[2]) and _near_v(a[3], b[3], 0.51)
		"slow":
			return int(a[2]) == int(b[2]) \
				and _near_v(a[3], b[3], 0.0001) and _near_v(a[4], b[4], 0.51)
		"bspd":
			return _near_v(a[2], b[2], 0.0002)
		"bdmg", "bface":
			return int(a[2]) == int(b[2])
		"cast":
			return _canon(a[2]) == _canon(b[2])
		"enrage":
			return true
	return false


## Kanon label skill: null → "none", float bulat JSON → int string.
func _canon(v) -> String:
	if v == null:
		return "none"
	if v is float:
		return str(int(roundf(v))) if absf(v - roundf(v)) < 0.001 else str(v)
	return str(v)


func _compare_final(boss_type: String, sc_name: String, expected: Dictionary,
		boss, probes: Array) -> void:
	var tag := "%s/%s final" % [boss_type, sc_name]
	_near(float(expected["hp"]), float(boss.hp), tag + ".hp", 0.51)
	_near(float(expected["x"]), boss.global_position.x, tag + ".x", 0.02)
	_near(float(expected["y"]), boss.global_position.y, tag + ".y", 0.02)
	_expect(int(expected["damage"]) == int(boss.damage), tag + ".damage "
		+ "(%d vs %d)" % [int(expected["damage"]), int(boss.damage)])
	_near(float(expected["speed"]), boss.move_speed / 60.0, tag + ".speed", 0.0002)
	_expect(int(expected["direction"]) == boss.facing, tag + ".facing")
	_expect(bool(expected["is_enraged"]) == boss.is_enraged, tag + ".is_enraged")
	_near(float(expected["ability2_timer"]), boss.ability2_timer * 60.0,
		tag + ".ability2_timer", 0.51)
	for k in expected["kit"]:
		var want = expected["kit"][k]
		var got = boss.kit.get(k)
		# referensi probe oracle ("P<idx>") menunjuk node probe replay
		if want is String and str(want).begins_with("P") and str(want).length() > 1:
			var idx := int(str(want).substr(1))
			var ok := idx >= 0 and idx < probes.size() and probes[idx] == got
			_expect(ok, "%s.kit.%s == probe %d" % [tag, k, idx])
		elif want is float or (want is int and got is float):
			_near(float(want), float(got), "%s.kit.%s" % [tag, k], 0.51)
		elif want is Array:
			_expect(_array_eq(want, got), "%s.kit.%s (%s vs %s)"
				% [tag, k, str(want), str(got)])
		else:
			_expect(_same_variant(want, got), "%s.kit.%s (%s vs %s)"
				% [tag, k, str(want), str(got)])


func _same_variant(a, b) -> bool:
	if a == null or b == null:
		return a == null and b == null
	return str(a) == str(b) and typeof(a) == typeof(b)


## Array kit (mis. clones_positions): elemen demi elemen dengan toleransi
## float — str() Array bisa beda format antara JSON parse dan GDScript.
func _array_eq(want: Array, got) -> bool:
	if not (got is Array) or want.size() != got.size():
		return false
	for i in want.size():
		var w = want[i]
		var g = got[i]
		if w is Array or w is Dictionary:
			if not _array_eq(w, g):
				return false
		elif w is float or w is int:
			if not _near_v(w, g, 0.51):
				return false
		elif not _same_variant(w, g):
			return false
	return true


func _near_v(a, b, eps: float) -> bool:
	if a == null or b == null:
		return a == null and b == null
	return absf(float(a) - float(b)) <= eps


# ══════════════════════════════════════════════════════════
#  HELPER LAPORAN
# ══════════════════════════════════════════════════════════

func _fail(tag: String, message: String) -> void:
	_failures += 1
	var line := "[BossSmartAIParityTest] %s: %s" % [tag, message]
	_error_messages.append(line)
	if _error_messages.size() <= 60:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_failures += 1
		var line := "[BossSmartAIParityTest] %s: %.4f != %.4f" % [message, a, b]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[BossSmartAIParityTest] " + message
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _finish() -> void:
	if _done:
		return
	_done = true
	get_tree().paused = false
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		var n_scen: int = _fixture.get("boss_smart_ai", {}) \
			.get("scenario_names", []).size()
		print("[BossSmartAIParityTest] PASS: smart-AI %d boss × %d skenario "
			% [_boss_count, n_scen])
		print("[BossSmartAIParityTest] PASS: %d event + %d state kit dibandingkan"
			% [_event_checks, _checks])
		print("[BossSmartAIParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[BossSmartAIParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[BossSmartAIParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
