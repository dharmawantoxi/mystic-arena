# HeroSkillParityTest — paritas QWER seluruh kit hero (222 hero) vs oracle
# Pygame.
#
# Fixture `match_parity.json["hero_skills"]` (STRING JSON kompak) dihasilkan
# tools/test_godot_match_parity.py dengan menjalankan subset skill
# Hero.update pygame ASLI (cast skrip -> Q-- -> active_skill_timer -> WER--
# -> skills.update_timers -> hit harness 'fire' tiap 37f mulai f30) untuk
# SEMUA hero di katalog: 6 starter (grimjaw/kaizen/sylara/thorne/vex/zephyr)
# DAN 216 boss-hero lewat BossHeroSkills/_SKILL_REGISTRY/_fallback_cast —
# 4 skenario per hero (cluster / edge / combo / empty). Tes ini memutar ulang
# skenario yang sama pada node Hero.gd + HeroSkillKit.gd (hasil transpile
# tools/gen_hero_skill_kit.py) dan membandingkan jejak event per frame +
# state final (cooldown, active skill, state kit, kondisi probe).
#
# Probe = musuh dummy deterministik; damage dicatat sebagai DELTA HP probe
# (bukan hook) supaya jalur kit_hit MAUPUN reflect bristleback tercatat,
# persis seperti oracle. Serangan dasar & gerak TIDAK di-simulasikan (jalur
# itu dikunci GameplayParityTest/BattleSmokeTest); harness Hero.gd
# `skill_test_step()` adalah satu-satunya driver frame di sini.
#
# Batas cakupan yang sengaja (lihat docs/GODOT_PARITY.md):
#   - Guard windrun (RNG 75%) & shadow-realm TIDAK teruji penuh di harness
#     (damage 'fire' tidak fisik -> windrun tak consume roll; shadow realm
#     baru aktif saat Zephyr W dicast dan TERCATAT lewat bhp flat).
#   - Proyektil skill visual-only (kit_no_projectiles=true di replay).
#
# godot --headless --path godot res://tests/HeroSkillParityTest.tscn --quit-after 60
# Require "[HeroSkillParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HeroScene = preload("res://scenes/hero/Hero.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
var _error_messages: Array[String] = []
var _hero_count: int = 0
var _event_checks: int = 0


## Status probe: shim perekam apply_slow (amount, durasi FRAME) — dipanggil
## Hero.gd.kit_slow di titik yang sama dengan probe oracle pygame
## (_HeroProbe.apply_slow). Query defensif dinolkan: CombatSystem tidak boleh
## punya jalur mitigasi apa pun terhadap probe.
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

	func is_stunned() -> bool:
		return false


## Musuh dummy — antarmuka yang disentuh HeroSkillKit/CombatSystem:
## team/hp/max_hp/is_dead/radius/attack_timer(DETIK; oracle pakai FRAME dan
## jembatan kit_* mengonversi)/speed/status. TIDAK ikut group apa pun:
## hanya list `enemies` harness yang boleh melihatnya (persis oracle, yang
## mengirim `probes` sebagai all_units — bukan lewat registry global).
class Probe extends Node2D:
	var team := "red"
	var hp := 1000000000.0
	var max_hp := 1000000000.0
	var armor := 0.0
	var magic_resist := 0.0
	var is_dead := false
	var radius := 16.0
	var attack_timer := 0.0
	var speed := 2.0
	var combat_timer := 0.0
	var combat_reset := 5.0
	var status: ProbeStatus = ProbeStatus.new()
	var idx := 0


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if _fixture == null or not _fixture.has("hero_skills"):
		push_error("[HeroSkillParityTest] fixture hero_skills belum ada — "
			+ "jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	var hs: Dictionary = JSON.parse_string(str(_fixture["hero_skills"]))
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	for row in hs["heroes"]:
		_test_hero(str(row["hero_type"]), row)
		if _failures > 40:
			_error_messages.append("[HeroSkillParityTest] berhenti awal: "
				+ "terlalu banyak kegagalan")
			break
	_finish()


# ══════════════════════════════════════════════════════════
#  REPLAY SKENARIO
# ══════════════════════════════════════════════════════════

func _test_hero(hero_type: String, row: Dictionary) -> void:
	for sc_name in row["scenarios"]:
		_replay_and_compare(hero_type, str(sc_name), row["scenarios"][sc_name])
	_hero_count += 1


## Putar ulang satu skenario pada node Hero asli dan bandingkan jejaknya.
func _replay_and_compare(hero_type: String, sc_name: String, sc: Dictionary) -> void:
	var hero = HeroScene.instantiate()
	hero.hero_type = hero_type
	hero.team = "blue"
	hero.position = Vector2(600, 400)
	add_child(hero) # _ready sinkron: stat + kit DEFAULT + SkillBook facade
	hero.set_physics_process(false)
	# ── kondisi harness persis _run_hero_skill_scenario ──
	hero.auto_cast_enabled = false
	hero.attack_timer = 1.0e9        # basic attack tidak pernah ready
	hero.kit_no_projectiles = true   # proyektil visual-only (oracle: no-op)
	hero.armor = 0.0
	hero.magic_resist = 0.0
	hero.status.clear()

	var probes: Array = []
	for pair in sc["probes"]:
		var p := Probe.new()
		p.position = Vector2(600.0 + float(pair[0]), 400.0 + float(pair[1]))
		p.hp = float(sc["probe_hp0"])
		p.idx = probes.size()
		add_child(p)
		probes.append(p)
	if str(sc.get("hp_mode", "full")) == "low":
		# pin 28% SEKALI (bukan per-frame) — mirror oracle sebelum loop
		hero.hp = maxf(1.0, float(int(hero.max_hp * 0.28)))

	var cast_by_frame := {}
	for c in sc["casts"]:
		var f := int(c[0])
		if not cast_by_frame.has(f):
			cast_by_frame[f] = []
		cast_by_frame[f].append([str(c[1]), bool(c[2])])

	var frames := int(sc["frames"])
	var events: Array = []
	var prev := _snapshot(hero, probes)

	for frame in range(frames):
		var key := ""
		var force := false
		if cast_by_frame.has(frame):
			var cs: Array = cast_by_frame[frame]
			if cs.size() != 1:
				_fail(hero_type, "%s: %d cast di frame %d (fixture harus 1)"
					% [sc_name, cs.size(), frame])
			key = str(cs[0][0])
			force = bool(cs[0][1])
		var ok := hero.skill_test_step(frame, key, force, probes)
		if key != "":
			events.append(["attempt", frame, key, 1 if ok else 0])
		# probe mati (tak pernah terjadi pada hp 1e9/2.8e8 — mirror
		# _HeroProbe.take_damage yang men-set alive=False): sinkron sebelum
		# frame berikutnya supaya kit_enemies/alive-check identik oracle.
		for p in probes:
			if p.hp <= 0.0 and not p.is_dead:
				p.is_dead = true
		_diff(hero, probes, prev, frame, events)
		prev = _snapshot(hero, probes)

	_compare_events(hero_type, sc_name, sc["events"], events)
	_compare_final(hero_type, sc_name, sc["final"], hero, probes)

	# free() SEKARANG (bukan queue_free) — alasan sama seperti
	# BossSmartAIParityTest: _boot adalah satu panggilan sinkron; hero/probe
	# lama yang masih terdaftar di group/registry akan mencemari skenario
	# berikutnya. Bandingkan final SEBELUM free (kit menyimpan node refs).
	for p in probes:
		p.free()
	hero.free()


func _snapshot(hero, probes: Array) -> Dictionary:
	var atk: Array = []
	var xy: Array = []
	var php: Array = []
	for p in probes:
		atk.append(p.attack_timer * 60.0)
		xy.append(Vector2(p.global_position.x, p.global_position.y))
		php.append(p.hp)
	return {
		"hp": float(hero.hp),
		"x": float(hero.global_position.x),
		"y": float(hero.global_position.y),
		"ast": float(int(hero.active_skill_timer)),
		"ask": hero.active_skill,
		"spd": float(hero.move_speed) / 60.0,
		"dmg": int(hero.damage),
		"face": int(hero.facing),
		"atk": roundf(float(hero.attack_cooldown) * 60.0),
		"probe_hp": php,
		"probe_atk": atk,
		"probe_xy": xy,
	}


## Diff state per frame — CERMIN persis loop _run_hero_skill_scenario pygame.
## attack_cooldown/attack_timer dikonversi ke FRAME (unit oracle) lewat
## jembatan yang sama dengan kit; toleransi pembanding menyerap 1/fps.
func _diff(hero, probes: Array, prev: Dictionary, frame: int, out: Array) -> void:
	if float(hero.hp) != float(prev["hp"]):
		out.append(["bhp", frame, _round3(float(hero.hp))])
	var px := float(hero.global_position.x)
	var py := float(hero.global_position.y)
	if absf(px - float(prev["x"])) > 0.001 or absf(py - float(prev["y"])) > 0.001:
		out.append(["bmove", frame, _round3(px), _round3(py)])
	var ast := float(int(hero.active_skill_timer))
	if ast > float(prev["ast"]):
		out.append(["cast", frame, _canon(hero.active_skill)])
	var ask = hero.active_skill
	if _canon(ask) != _canon(prev["ask"]) and (ast > 0.0 or ask == null):
		out.append(["ask", frame, _canon(ask), int(ast)])
	if float(hero.move_speed) / 60.0 != float(prev["spd"]):
		out.append(["bspd", frame, _round5(float(hero.move_speed) / 60.0)])
	if int(hero.damage) != int(prev["dmg"]):
		out.append(["bdmg", frame, int(hero.damage)])
	var atk_f := roundf(float(hero.attack_cooldown) * 60.0)
	if int(atk_f) != int(float(prev["atk"])):
		out.append(["batk", frame, _round4(atk_f)])
	if int(hero.facing) != int(prev["face"]):
		out.append(["bface", frame, int(hero.facing)])
	for i in probes.size():
		var p: Probe = probes[i]
		var d := float(prev["probe_hp"][i]) - p.hp
		if d > 0.0:
			out.append(["dmg", frame, i, _round3(d)])
		if p.attack_timer * 60.0 != float(prev["probe_atk"][i]):
			out.append(["alock", frame, i, _round3(p.attack_timer * 60.0)])
		var xy: Vector2 = prev["probe_xy"][i]
		if p.global_position.x != xy.x or p.global_position.y != xy.y:
			out.append(["emove", frame, i,
				_round3(p.global_position.x), _round3(p.global_position.y)])
		for rec in p.status.slow_records:
			out.append(["slow", frame, i, float(rec[0]), _round3(float(rec[1]))])
		p.status.slow_records.clear()


# ══════════════════════════════════════════════════════════
#  PERBANDINGAN
# ══════════════════════════════════════════════════════════

## Urutan event DALAM satu frame tidak dinilai (group/iteration order boleh
## beda) — di-bucket per frame lalu diurutkan deterministik (pola boss test).
func _compare_events(hero_type: String, sc_name: String,
		expected: Array, actual: Array) -> void:
	_checks += 1
	_event_checks += expected.size()
	var eb := _bucket(expected)
	var ab := _bucket(actual)
	var frames_e := eb.keys()
	frames_e.sort()
	var tag := "%s/%s" % [hero_type, sc_name]
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
		"attempt":
			return str(a[2]) == str(b[2]) and int(a[3]) == int(b[3])
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
		"batk":
			return _near_v(a[2], b[2], 0.51)
		"bdmg", "bface":
			return int(a[2]) == int(b[2])
		"cast":
			return _canon(a[2]) == _canon(b[2])
		"ask":
			return _canon(a[2]) == _canon(b[2]) and int(a[3]) == int(b[3])
	return false


## Kanon label skill: null → "none"; JSON tak pernah memberi float di sini
## tapi jaga-jaga seperti _canon boss test.
func _canon(v) -> String:
	if v == null:
		return "none"
	if v is float:
		return str(int(roundf(v))) if absf(v - roundf(v)) < 0.001 else str(v)
	return str(v)


func _compare_final(hero_type: String, sc_name: String, expected: Dictionary,
		hero, probes: Array) -> void:
	var tag := "%s/%s final" % [hero_type, sc_name]
	_near(float(expected["hp"]), float(hero.hp), tag + ".hp", 0.51)
	_near(float(expected["x"]), float(hero.global_position.x), tag + ".x", 0.02)
	_near(float(expected["y"]), float(hero.global_position.y), tag + ".y", 0.02)
	_expect(int(expected["damage"]) == int(hero.damage), tag + ".damage "
		+ "(%d vs %d)" % [int(expected["damage"]), int(hero.damage)])
	_near(float(expected["speed"]), float(hero.move_speed) / 60.0,
		tag + ".speed", 0.0002)
	_near(float(expected["attack_cooldown"]),
		roundf(float(hero.attack_cooldown) * 60.0), tag + ".attack_cooldown", 0.51)
	_expect(int(expected["facing"]) == int(hero.facing), tag + ".facing")
	_expect(int(expected["skill_timer"]) == int(hero.skill_timer),
		tag + ".skill_timer (%d vs %d)" % [int(expected["skill_timer"]), int(hero.skill_timer)])
	_expect(int(expected["w_cooldown"]) == int(hero.w_cooldown),
		tag + ".w_cooldown (%d vs %d)" % [int(expected["w_cooldown"]), int(hero.w_cooldown)])
	_expect(int(expected["e_cooldown"]) == int(hero.e_cooldown),
		tag + ".e_cooldown (%d vs %d)" % [int(expected["e_cooldown"]), int(hero.e_cooldown)])
	_expect(int(expected["r_cooldown"]) == int(hero.r_cooldown),
		tag + ".r_cooldown (%d vs %d)" % [int(expected["r_cooldown"]), int(hero.r_cooldown)])
	_expect(_canon(expected["active_skill"]) == _canon(hero.active_skill),
		tag + ".active_skill (%s vs %s)" % [_canon(expected["active_skill"]),
			_canon(hero.active_skill)])
	_expect(int(expected["active_skill_timer"]) == int(hero.active_skill_timer),
		tag + ".active_skill_timer (%d vs %d)" % [int(expected["active_skill_timer"]),
			int(hero.active_skill_timer)])
	_expect(float(expected["hp_floor"]) == 1.0, tag + ".hp_floor")
	for k in expected["kit"]:
		var want = expected["kit"][k]
		var got = hero.kit.get(k)
		# referensi probe oracle ("P<idx>") menunjuk node probe replay
		if want is String and str(want).begins_with("P") and str(want).length() > 1:
			var idx := int(str(want).substr(1))
			var ok: bool = idx >= 0 and idx < probes.size() and probes[idx] == got
			_expect(ok, "%s.kit.%s == probe %d" % [tag, k, idx])
		elif want is float or (want is int and got is float):
			if got is float or got is int:
				_near(float(want), float(got), "%s.kit.%s" % [tag, k], 0.51)
			else:
				_expect(false, "%s.kit.%s: oracle %s (%s) vs Godot %s"
					% [tag, k, str(want), typeof(want), str(got)])
		elif want is Array:
			_expect(_array_eq(want, got), "%s.kit.%s (%s vs %s)"
				% [tag, k, str(want), str(got)])
		else:
			_expect(_same_variant(want, got), "%s.kit.%s (%s vs %s)"
				% [tag, k, str(want), str(got)])
	var pf: Array = expected["probe_final"]
	_expect(pf.size() == probes.size(), "%s.probe_final size (%d vs %d)"
		% [tag, pf.size(), probes.size()])
	for i in mini(pf.size(), probes.size()):
		var e: Array = pf[i]
		var p: Probe = probes[i]
		_near(float(e[0]), float(p.hp), "%s.probe_final.%d.hp" % [tag, i], 0.51)
		_near(float(e[1]), p.attack_timer * 60.0, "%s.probe_final.%d.atk" % [tag, i], 0.51)
		_near(float(e[2]), float(p.global_position.x), "%s.probe_final.%d.x" % [tag, i], 0.02)
		_near(float(e[3]), float(p.global_position.y), "%s.probe_final.%d.y" % [tag, i], 0.02)


func _same_variant(a, b) -> bool:
	if a == null or b == null:
		return a == null and b == null
	return str(a) == str(b) and typeof(a) == typeof(b)


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


func _round3(v: float) -> float:
	return snappedf(v, 0.001)


func _round4(v: float) -> float:
	return snappedf(v, 0.0001)


func _round5(v: float) -> float:
	return snappedf(v, 0.00001)


func _near_v(a, b, eps: float) -> bool:
	if a == null or b == null:
		return a == null and b == null
	return absf(float(a) - float(b)) <= eps


# ══════════════════════════════════════════════════════════
#  HELPER LAPORAN
# ══════════════════════════════════════════════════════════

func _fail(tag: String, message: String) -> void:
	_failures += 1
	var line := "[HeroSkillParityTest] %s: %s" % [tag, message]
	_error_messages.append(line)
	if _error_messages.size() <= 60:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_failures += 1
		var line := "[HeroSkillParityTest] %s: %.4f != %.4f" % [message, a, b]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[HeroSkillParityTest] " + message
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
		var n_scen: int = JSON.parse_string(
			str(_fixture.get("hero_skills", "{}"))).get("scenario_names", []).size()
		print("[HeroSkillParityTest] PASS: kit %d hero × %d skenario "
			% [_hero_count, n_scen])
		print("[HeroSkillParityTest] PASS: %d event + %d state dibandingkan"
			% [_event_checks, _checks])
		print("[HeroSkillParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[HeroSkillParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[HeroSkillParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
