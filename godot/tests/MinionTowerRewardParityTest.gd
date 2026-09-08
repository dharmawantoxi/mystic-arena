# FASE 15 — seluruh daftar headless minion_tower_rewards direplay, bukan
# pemeriksaan subset / string sumber. Oracle = loop reward Game.update
# pygame ASLI (_core.py:2196-2227) + Minion/Hero/Tower betulan mati lewat
# take_damage asli + EffectManager.add_gold_popup/FloatingText ASLI.
#
# Godot: Main/HUD/Minion/Hero/Tower/Nexus/Boss SUNGGUHAN; transaksi kematian
# produksi (Minion.die → register_minion_death, Tower.die →
# register_tower_death + signal tower_destroyed → Main.red_towers_destroyed).
# Yang direplay per skenario:
#   - penerima reward = TIM KORBAN (minion/menara merah → gold+skor pemain,
#     biru → saldo AI), TERMASUK sumber netral/tanpa killer/tim sendiri;
#   - popup gold +nG kematian minion merah: posisi/nominal/urutan FIFO/
#     lifetime/gerak/scale + konsumsi RNG x_drift per situs (ParityRng
#     pola FASE 14); minion biru & MENARA tanpa popup (pygame tidak
#     membuatnya — dijajar snapshot floating + popup_events kosong);
#   - total_kills/combo/max_combo termasuk quirk max_combo dibaca SEBELUM
#     add_kill; red_towers_destroyed naik TEPAT SEKALI per menara merah;
#   - kunci anti pembayaran ganda: pukul mayat (take_damage guard is_dead),
#     die() ulang (guard), dan callback register_* dipanggil langsung —
#     flag reward_processed per instans menahan semuanya.
#
# Kill dieksekusi dalam URUTAN DEKLARASI unit (bukan urutan array kills):
# loop pygame membayar sesuai urutan daftar _core.py:2196/2218, bukan
# urutan pukulan dalam satu frame — antrean popup mengikuti daftar.
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
# Seperti MatchScoring/BossDeathReward, data+file save di-snapshot lalu
# dipulihkan di akhir. Piksel font/shadow/glow popup dan SFX BELUM diuji.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const NexusScene = preload("res://scenes/base/Nexus.tscn")
const BossScene = preload("res://scenes/boss/Boss.tscn")
const QueueScript = preload("res://scripts/utils/FloatingTextQueue.gd")
const FRAME := 1.0 / 60.0

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_before = null
var _main = null
var _units: Dictionary = {}
var _order: Dictionary = {}
var _sources: Dictionary = {}
var _gold_events: Array = []
var _popup_events: Array = []
var _pending_dead: Array = []
var _rolls: Array = []
var _consumed: Array = []
var _roll_pos := 0
var _rng_active := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_run.call_deferred()


func _run() -> void:
	_save_before = SaveManager.data.duplicate(true)
	if FileAccess.file_exists(SaveManager.SAVE_PATH):
		_save_file_before = FileAccess.get_file_as_string(SaveManager.SAVE_PATH)
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not (fixture is Dictionary) or not fixture.has("minion_tower_rewards"):
		_expect(false, "fixture minion_tower_rewards belum ada —"
			+ " jalankan tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["minion_tower_rewards"]
	_keys(_fx, ["fps", "initial", "sources", "max_floating", "scenarios"],
		"seksi fixture")
	_compare(GameManager.FPS, _fx["fps"], "FPS")
	_compare(QueueScript.MAX_FLOATING, _fx["max_floating"], "MAX_FLOATING")

	GameManager.set_process(false)
	GameManager.in_menu = false
	GameManager.state = "playing"
	GameManager.waves_enabled = false
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	_main._ai.set_process(false)
	_main.find_child("Containers", true, false).process_mode = \
		Node.PROCESS_MODE_DISABLED
	await get_tree().process_frame
	await get_tree().process_frame
	# Main yang hidup di luar menu otomatis memulai battle + intro level
	# yang MEMBEKUKAN SceneTree — GameManager._process pulih lebih awal.
	# Pola _clear_cinematics BossDeathRewardParityTest (FASE 14).
	_clear_cinematics()
	_expect(_main.find_child("WorldPopups", true, false) != null,
		"view popup map terpasang (FASE 14)")
	GameManager.gold_popup_added.connect(_on_gold_popup)
	GameManager.achievement_unlocked.connect(_on_popup)
	GameManager.world_popups.uniform_rng = _uniform

	for spec in _fx["scenarios"]:
		_test_scenario(spec)
	_rng_active = false

	_finish()


# ── Skenario penuh: snapshot rekursif + seluruh event + seluruh roll ──
func _test_scenario(spec: Dictionary) -> void:
	_keys(spec, ["name", "initial", "units", "steps"], "scenario")
	_reset(spec["initial"])
	_make_units(spec["units"])
	_make_sources()
	# Kill dieksekusi urutan DEKLARASI (loop pygame membayar per daftar).
	var kills_by_step: Array = []
	for step in spec["steps"]:
		_keys(step, ["kills", "frames", "snapshot"], "step")
		var ordered: Array = []
		for kill in step["kills"]:
			ordered.append([_order[str(kill["unit"])], kill])
		ordered.sort_custom(func(a, b): return a[0] < b[0])
		kills_by_step.append(ordered)
	var index := 0
	for step in spec["steps"]:
		_keys(step, ["kills", "frames", "snapshot"], "step")
		_begin_rolls(step["snapshot"]["rolls"])
		if index == 0:
			# Unit dead-on-spawn dibunuh DI SINI (bukan saat _make_units):
			# oracle pygame membayarnya di update pertama — di dalam langkah,
			# sesudah RNG popup di-pin, sebelum frame di-step. Popup-nya
			# lalu ke-tick pada frame yang sama persis seperti Game.update.
			for unit in _pending_dead:
				unit.die("")
			_pending_dead.clear()
		for pair in kills_by_step[index]:
			_run_kill(pair[1])
		for _f in range(int(step["frames"])):
			# Satu frame oracle = Game.update: countdown respawn hero +
			# tick combo (EffectManager) + tick popup. Blok income/passive
			# gold TIDAK ikut — oracle membekukannya dengan
			# GOLD_PER_SECOND=0 (pola MatchScoringParityTest FASE 13;
			# logika income sendiri terkunci GameplayParityTest/ai_income).
			GameManager._update_hero_respawns(FRAME)
			GameManager._tick_combo(FRAME)
			GameManager.world_popups.advance(FRAME)
		var tag := "%s/%d" % [spec["name"], index]
		_compare(_consumed, step["snapshot"]["rolls"], tag + " konsumsi RNG")
		_compare(_snapshot(), step["snapshot"], tag)
		# Snapshot lengkap sudah mengecek antrean + event; guard eksplisit
		# ini mencegah popup yang sudah dihapus dibuat ulang.
		for popup_event in _popup_events:
			_expect(popup_event[0] != "HERO SLAYER!", tag + " tanpa HERO SLAYER")
			_expect(popup_event[0] != "MINION BOSS SLAYER!"
				and popup_event[0] != "TRUE BOSS SLAYER!",
				tag + " tanpa popup SLAYER di klaster ini")
		index += 1
	_rng_active = false


func _reset(overrides: Dictionary = {}) -> void:
	_clear_case()
	var init: Dictionary = _fx["initial"].duplicate(true)
	init.merge(overrides, true)
	for key in ["gold", "score", "ai_gold", "total_kills", "max_combo"]:
		GameManager.set(key, int(init[key]))
	GameManager.gold_per_second = 0.0
	GameManager._gold_timer = 0.0
	GameManager._gold_income_milli = 0
	GameManager.wave_number = 0
	GameManager.combo.reset()
	GameManager._combo_accum = 0.0
	GameManager._hero_respawn_timers.clear()
	GameManager.state = "playing"
	GameManager.in_menu = false
	GameManager.set_paused(false)
	GameManager.is_replay = false
	GameManager.level_number = 1
	GameManager.world_popups.reset()
	# FX kontak hit (DamageNumber) diisolasi dari jejak klaster — persis
	# oracle pygame yang me-null-kan game_instance saat take_damage.
	# Tanpa ini damage number pukulan pembunuh masuk FIFO bersama popup
	# gold dan bisa menggeser/menggusur entri di anggaran 16 (interaksi
	# anggaran itu ranah FASE 14 shared_budget, bukan klaster reward).
	# Popup gold TIDAK membaca flag ini (dikunci skenario numbers_off).
	GameManager.world_popups.damage_numbers_enabled = false
	GameManager.world_popups.max_damage_numbers = \
		int(init["max_damage_numbers"])
	_main.red_towers_destroyed = int(init["red_towers_destroyed"])
	_main.true_boss_spawned = true
	_main.active_boss = null
	_main.pending_mini_bosses = []
	_gold_events.clear()
	_popup_events.clear()


func _make_units(units_spec: Array) -> void:
	_units.clear()
	_order.clear()
	var i := 0
	for uspec in units_spec:
		_allowed_keys(uspec, ["id", "kind", "team"],
			["type", "nexus_level", "tower_kind", "reward", "dead"],
			"unit spec")
		var unit = null
		match str(uspec["kind"]):
			"minion":
				unit = MinionScene.instantiate()
				unit.minion_type = str(uspec["type"])
				unit.team = str(uspec["team"])
				if uspec.has("nexus_level"):
					# stat_scale = minion_scale NEXUS_LEVELS pygame —
					# dibaca dari data Godot sendiri (drift terkunci
					# seksi minions GameplayParityTest), bukan fixture.
					unit.stat_scale = float(
						TowerDB.nexus_raw(int(uspec["nexus_level"]))
						.get("minion_scale", 1.0))
			"hero":
				unit = HeroScene.instantiate()
				unit.hero_type = str(uspec["type"])
				unit.team = str(uspec["team"])
			"tower":
				unit = TowerScene.instantiate()
				unit.team = str(uspec["team"])
				unit.tower_kind = str(uspec.get("tower_kind", "outer"))
			_:
				_expect(false, "jenis unit asing " + str(uspec["kind"]))
				continue
		unit.position = Vector2(220.5 + i * 240.25,
			300.25 + (i % 2) * 240.5)
		_main.find_child("Containers", true, false).add_child(unit)
		unit.set_physics_process(false)
		if uspec.has("reward"):
			# Nilai RUNTIME, bukan katalog (paritas oracle reward=N).
			unit.gold_reward = int(uspec["reward"])
		_units[str(uspec["id"])] = unit
		_order[str(uspec["id"])] = i
		if bool(uspec.get("dead", false)):
			# Mati sebelum frame pertama: oracle pygame menandai alive=False
			# lalu loop reward membayarnya di update pertama. die() ditunda
			# ke langkah pertama supaya RNG popup-nya ter-pin (snapshot step
			# 0 memang mengharapkan satu roll + satu event gold).
			_pending_dead.append(unit)
		i += 1


func _make_sources() -> void:
	for spec in _fx["sources"]:
		_allowed_keys(spec, ["id", "kind", "team", "x", "y"],
			["type", "dead"], "source")
		var unit = null
		match str(spec["kind"]):
			"hero":
				unit = HeroScene.instantiate()
				unit.hero_type = str(spec["type"])
			"minion":
				unit = MinionScene.instantiate()
				unit.minion_type = str(spec["type"])
			"tower":
				unit = TowerScene.instantiate()
			"nexus":
				unit = NexusScene.instantiate()
			"boss":
				unit = BossScene.instantiate()
				unit.boss_type = str(spec["type"])
			_:
				_expect(false, "jenis source asing " + str(spec["kind"]))
				continue
		unit.team = str(spec["team"])
		unit.position = Vector2(float(spec["x"]), float(spec["y"]))
		_main.find_child("Containers", true, false).add_child(unit)
		unit.set_physics_process(false)
		if str(spec["kind"]) == "hero":
			unit.kills = 4
			unit.is_dead = bool(spec.get("dead", false))
		_sources[str(spec["id"])] = unit


func _run_kill(kill: Dictionary) -> void:
	_allowed_keys(kill, ["unit"], ["by", "team", "dead", "repeat"], "kill")
	var victim = _units[str(kill["unit"])]
	var by = _sources.get(kill.get("by")) if kill.has("by") else null
	var from_team := ""
	if kill.has("team"):
		from_team = str(kill["team"])
	elif by != null:
		from_team = str(by.get("team"))
	if bool(kill.get("dead", false)):
		victim.die(from_team)
	else:
		victim.take_damage(1000000000.0, from_team, "normal", by)
	if bool(kill.get("repeat", false)):
		# Baterai anti pembayaran ganda tiga lapis: pukul mayat (guard
		# is_dead di take_damage), die() ulang (guard is_dead), dan
		# callback register_* dipanggil LANGSUNG (guard reward_processed).
		victim.take_damage(1000000000.0, from_team, "normal", by)
		victim.die(from_team)
		if "minion_type" in victim:
			GameManager.register_minion_death(victim)
		elif "tower_kind" in victim:
			GameManager.register_tower_death(victim)
		elif "hero_type" in victim:
			GameManager.register_hero_death(victim)


func _snapshot() -> Dictionary:
	var kills := {}
	var rewarded := {}
	for uid in _units:
		var unit = _units[uid]
		if "hero_type" in unit:
			kills[uid] = unit.kills
		rewarded[uid] = bool(unit.get("reward_processed"))
	for sid in _sources:
		var unit = _sources[sid]
		if "hero_type" in unit:
			kills[sid] = unit.kills
	return {
		"gold": GameManager.gold, "score": GameManager.score,
		"ai_gold": GameManager.ai_gold,
		"total_kills": GameManager.total_kills,
		"max_combo": GameManager.max_combo,
		"combo": {"count": GameManager.combo.count,
			"timer": GameManager.combo.timer,
			"last_combo": GameManager.combo.last_combo},
		"red_towers_destroyed": _main.red_towers_destroyed,
		"kills": kills,
		"rewarded": rewarded,
		"floating": GameManager.world_popups.floating_texts,
		"gold_events": _gold_events.duplicate(true),
		"popup_events": _popup_events.duplicate(true),
		"rolls": _consumed.duplicate(true),
	}


# ── Recorder event/RNG (tidak menggantikan gameplay) ──
func _on_gold_popup(x: float, y: float, amount: int) -> void:
	_gold_events.append([x, y, amount])


func _on_popup(title: String, description: String, icon: String) -> void:
	_popup_events.append([title, description, icon])


func _begin_rolls(rolls: Array) -> void:
	_rng_active = true
	_rolls = rolls
	_consumed = []
	_roll_pos = 0


func _uniform(a: float, b: float) -> float:
	if not _rng_active:
		return randf_range(a, b)
	if _roll_pos >= _rolls.size():
		_expect(false, "roll popup liar: uniform")
		return a
	var roll: Array = _rolls[_roll_pos]
	_compare(["uniform", a, b], roll.slice(0, 3), "situs/range RNG")
	var value := float(roll[3])
	_consumed.append(["uniform", a, b, value])
	_roll_pos += 1
	return value


## Cinematic (intro level/banner) memegang pause SceneTree — lepas supaya
## GameManager._process manual benar-benar men-tick combo/popup. Intro yang
## skip via finish() melepas pause-nya sendiri; sisanya di-free paksa.
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
	_main.red_towers_destroyed = 0
	GameManager._hero_respawn_timers.clear()
	GameManager.clear_selection()
	for group in ["heroes", "bosses", "minions", "towers", "nexus",
			"bullets", "skill_projectiles", "floating_text"]:
		for node in get_tree().get_nodes_in_group(group):
			node.free()
	for node in _main.find_child("FX", true, false).get_children():
		node.free()
	_units.clear()
	_sources.clear()
	_pending_dead.clear()
	GameManager.blue_nexus = null
	GameManager.red_nexus = null


# ── Recursive closed-world comparison; JSON numbers may be floats ──
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
	elif (actual is int or actual is float) and (wanted is int or wanted is float):
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
		print("[MinionTowerRewardParityTest] FAIL: " + message)
		push_error("[MinionTowerRewardParityTest] " + message)


func _finish() -> void:
	_rng_active = false
	GameManager.world_popups.uniform_rng = randf_range
	if GameManager.gold_popup_added.is_connected(_on_gold_popup):
		GameManager.gold_popup_added.disconnect(_on_gold_popup)
	if GameManager.achievement_unlocked.is_connected(_on_popup):
		GameManager.achievement_unlocked.disconnect(_on_popup)
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
		print("[MinionTowerRewardParityTest] PASS: %d checks reward minion+menara vs oracle pygame" % _checks)
	else:
		print("[MinionTowerRewardParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
