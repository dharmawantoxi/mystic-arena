# FASE 14 — seluruh daftar headless boss_death_rewards direplay, bukan
# pemeriksaan subset katalog / string sumber. Oracle = Game.update pygame
# asli + Boss.take_damage + EffectManager.add_gold_popup/FloatingText.
#
# Godot: Main/HUD/Boss/Hero/Minion/Tower/Nexus SUNGGUHAN, transaksi death
# produksi, write SaveManager sungguhan (disk dibandingkan sesudah close),
# callback duplicate, reset/menu, antrean popup + RNG per situs. Snapshot
# dibandingkan rekursif dengan himpunan key tertutup (key asing juga gagal).
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
# Seperti MatchScoringParityTest, data+file save juga dipulihkan di akhir.
# Piksel font/shadow/glow/komposit cinematic dan bunyi SFX BELUM diuji.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const BossScene = preload("res://scenes/boss/Boss.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const NexusScene = preload("res://scenes/base/Nexus.tscn")
const DamageNumberScene = preload("res://scenes/fx/DamageNumber.tscn")
const QueueScript = preload("res://scripts/utils/FloatingTextQueue.gd")
const FRAME := 1.0 / 60.0

var _fx: Dictionary = {}
var _failures := 0
var _checks := 0
var _save_before: Dictionary = {}
var _save_file_before = null
var _main = null
var _hud = null
var _popup = null
var _boss = null
var _units: Dictionary = {}
var _writes: Array = []
var _gold_events: Array = []
var _popup_events: Array = []
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
	if not (fixture is Dictionary) or not fixture.has("boss_death_rewards"):
		_expect(false, "fixture boss_death_rewards belum ada")
		_finish()
		return
	_fx = fixture["boss_death_rewards"]
	_keys(_fx, ["fps", "initial", "sources", "catalog", "scenarios",
		"max_floating", "popups", "shared_budget", "outcomes", "reset"], "seksi fixture")
	_compare(GameManager.FPS, _fx["fps"], "FPS")
	_compare(QueueScript.MAX_FLOATING, _fx["max_floating"], "MAX_FLOATING")

	GameManager.set_process(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.waves_enabled = false
	_main = MainScene.instantiate()
	add_child(_main)
	_main.set_process(false)
	_main._ai.set_process(false)
	_main.find_child("Containers", true, false).process_mode = Node.PROCESS_MODE_DISABLED
	await get_tree().process_frame
	_hud = _main.find_child("HUD", true, false)
	_popup = _hud.find_child("AchievementPopup", true, false)
	_popup.set_process(false) # driver 60Hz, signal frame kematian tetap aktif
	_expect(_main.find_child("WorldPopups", true, false) != null, "view popup map terpasang")
	_expect(_popup.process_mode == Node.PROCESS_MODE_PAUSABLE,
		"popup membeku saat cinematic/pause (bukan inherit ALWAYS Main)")
	SaveManager.saved.connect(_on_saved)
	GameManager.gold_popup_added.connect(_on_gold_popup)
	GameManager.achievement_unlocked.connect(_on_popup)
	GameManager.world_popups.uniform_rng = _uniform
	GameManager.world_popups.integer_rng = _integer

	_test_catalog()
	for spec in _fx["scenarios"]:
		_test_scenario(spec)
	_test_popup_queue()
	_test_shared_budget()
	_test_outcomes()
	await _test_reset_and_menu()
	_finish()


# ── 216 instans Boss asli: katalog tertutup + payout Game.update ──
func _test_catalog() -> void:
	var seen: Array = []
	_rng_active = false
	for row in _fx["catalog"]:
		_keys(row, ["boss_type", "name", "boss_class", "gold_reward",
			"scaled_gold_reward", "payout"], "catalog row")
		var bt := str(row["boss_type"])
		_expect(not seen.has(bt), "katalog tanpa duplikat " + bt)
		seen.append(bt)
		_reset({"unlocked_bosses": [bt]})
		_boss = _spawn_boss({"boss_type": bt})
		_compare(_boss.display_name, row["name"], bt + " name")
		_compare(_boss.boss_class, row["boss_class"], bt + " class")
		_compare(_boss.gold_reward, row["gold_reward"], bt + " reward field")
		_boss.apply_scaling(1.265, 1.21, 1.07)
		_compare(_boss.gold_reward, row["scaled_gold_reward"], bt + " reward hard")
		_boss.hp = 1.0
		_boss.take_damage(1000000000.0, "blue")
		_compare({"gold": GameManager.gold, "score": GameManager.score,
			"ai_gold": GameManager.ai_gold, "run": GameManager.bosses_defeated_this_run},
			row["payout"], bt + " payout")
		_expect(_boss.is_dead and _boss.defeated and _boss.reward_processed,
			bt + " transaksi kematian asli")
	var catalog_keys := BossDB.bosses.keys()
	catalog_keys.sort()
	seen.sort()
	_compare(seen, catalog_keys, "semua boss katalog harus direplay")


# ── Skenario penuh: nilai snapshot + SEMUA event + SEMUA roll ──
func _test_scenario(spec: Dictionary) -> void:
	_keys(spec, ["name", "initial", "steps"], "scenario")
	_reset(spec["initial"])
	_make_sources()
	var index := 0
	for step in spec["steps"]:
		_keys(step, ["action", "rolls", "snapshot"], "step")
		_begin_rolls(step["rolls"])
		_run_action(step["action"])
		var tag := "%s/%d" % [spec["name"], index]
		_compare(_consumed, step["rolls"], tag + " konsumsi RNG")
		_compare(_snapshot(), step["snapshot"], tag)
		# Snapshot lengkap sudah mengecek queue/current + event. Guard
		# eksplisit ini mencegah popup yang sudah dihapus dibuat ulang.
		for popup_event in _popup_events:
			_expect(popup_event[0] != "HERO SLAYER!", tag + " tanpa HERO SLAYER")
		index += 1
	_rng_active = false


func _reset(overrides: Dictionary = {}) -> void:
	_clear_case()
	var init: Dictionary = _fx["initial"].duplicate(true)
	init.merge(overrides, true)
	SaveManager.data = {
		"unlocked_heroes": init["purchased_heroes"].duplicate(),
		"unlocked_bosses": init["unlocked_bosses"].duplicate(),
		"meta_gold": init["meta_gold"], "sentinel": init["sentinel"].duplicate(true),
	}
	GameManager.bind_purchased_heroes(false)
	GameManager.bind_unlocked_bosses()
	for key in ["gold", "score", "ai_gold", "total_kills", "max_combo",
			"bosses_defeated_this_run", "miniboss_kill_count", "trueboss_kill_count"]:
		GameManager.set(key, int(init[key]))
	GameManager.bosses_defeated_this_match = init["bosses_defeated_this_match"].duplicate()
	GameManager.achievements_unlocked.clear()
	for id in init["achievements_unlocked"]:
		GameManager.achievements_unlocked[str(id)] = true
	GameManager.heroes_unlocked_this_match = []
	GameManager._hero_respawn_timers.clear()
	GameManager.gold_per_second = 0.0
	GameManager._gold_timer = 0.0
	GameManager._gold_income_milli = 0
	GameManager._meta_reward_granted = false
	GameManager.is_replay = false
	GameManager.level_number = 1
	GameManager.wave_number = 0
	GameManager.combo.reset()
	GameManager.combo.count = 3
	GameManager.combo.timer = 120
	GameManager.combo.last_combo = 2
	GameManager._combo_accum = 0.0
	GameManager.state = "playing"
	GameManager.in_menu = false
	GameManager.set_paused(false)
	GameManager.world_popups.reset()
	GameManager.world_popups.damage_numbers_enabled = bool(init["damage_numbers_enabled"])
	GameManager.world_popups.max_damage_numbers = int(init["max_damage_numbers"])
	_popup.reset()
	_writes.clear()
	_gold_events.clear()
	_popup_events.clear()


func _make_sources() -> void:
	for spec in _fx["sources"]:
		_allowed_keys(spec, ["id", "kind", "team"], ["type", "dead"], "source")
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
		unit.position = Vector2(200, 300)
		_main.find_child("Containers", true, false).add_child(unit)
		unit.set_physics_process(false)
		if str(spec["kind"]) == "hero":
			unit.kills = 4
			unit.is_dead = bool(spec.get("dead", false))
		_units[str(spec["id"])] = unit


func _spawn_boss(action: Dictionary):
	var boss = BossScene.instantiate()
	boss.boss_type = str(action["boss_type"])
	boss.team = str(action.get("boss_team", "red"))
	var pos: Array = action.get("position", [640.25, 360.75])
	boss.position = Vector2(float(pos[0]), float(pos[1]))
	GameManager.boss_container.add_child(boss)
	boss.set_physics_process(false)
	boss.entrance_timer = 1000000.0 / 60.0
	if action.has("scaling"):
		var mult: Array = action["scaling"]
		boss.apply_scaling(float(mult[0]), float(mult[1]), float(mult[2]))
	if action.has("reward"):
		boss.gold_reward = int(action["reward"])
	if action.has("alive"):
		boss.is_dead = not bool(action["alive"])
	if action.has("defeated"):
		boss.defeated = bool(action["defeated"])
	_main.active_boss = boss
	if action.has("pending"):
		_main.pending_mini_bosses = action["pending"].duplicate()
	return boss


func _run_action(action: Dictionary) -> void:
	_allowed_keys(action, ["op"], ["boss_type", "boss_team", "by", "position",
		"scaling", "reward", "alive", "defeated", "pending", "hp", "damage",
		"from_team", "frames"], "action")
	var op := str(action["op"])
	var count_before := GameManager.bosses_defeated_this_run
	if op == "spawn" or op == "kill":
		_clear_cinematics()
		_boss = _spawn_boss(action)
	if op in ["kill", "hit", "repeat_hit"]:
		if op != "repeat_hit":
			_boss.hp = float(action.get("hp", 1))
		var killer = _boss if action.get("by") == "self" else _units.get(action.get("by"))
		_boss.take_damage(float(action.get("damage", 1000000000.0)),
			str(action.get("from_team", "blue")), "normal", killer)
		# Ulangi callback MANAGER juga: node tetap hidup selama tween mati.
		# Tidak boleh mendobel gold/kill/popups/save/counter/tick efek.
		GameManager.register_boss_death(_boss)
		if op == "repeat_hit":
			_boss.die(killer)
	elif op == "hero_kill":
		var victim = HeroScene.instantiate()
		victim.hero_type = "vex"
		victim.team = "red"
		_main.find_child("Containers", true, false).add_child(victim)
		victim.set_physics_process(false)
		victim.hp = 1.0
		victim.take_damage(1000000000.0, "blue", "normal", _units["blue"])
	elif op == "clear_cinematic":
		_clear_cinematics()
	elif op not in ["spawn", "wait"]:
		_expect(false, "operasi fixture asing: " + op)

	# Blok guard defeated ikut diuji untuk input alive / !defeated.
	if is_instance_valid(_boss):
		GameManager.register_boss_death(_boss)
	var rewarded := GameManager.bosses_defeated_this_run > count_before
	for node in get_tree().get_nodes_in_group("cinematic"):
		node.set_process(false)
	for frame in range(int(action.get("frames", 1))):
		if frame == 0 and rewarded:
			# register_boss_death sudah menyelesaikan satu frame efek
			# SEBELUM BossDeathFX menahan gameplay, persis Game.update.
			continue
		var death = _death_fx()
		if death != null and death.death_active:
			death._process(FRAME)
			continue
		GameManager._process(FRAME)
		_popup.tick()


func _snapshot() -> Dictionary:
	var kills := {}
	for id in _units:
		var unit = _units[id]
		if "hero_type" in unit:
			kills[id] = unit.kills
	var ids := GameManager.achievements_unlocked.keys()
	ids.sort()
	var death = _death_fx()
	var active = _main.active_boss
	return {
		"gold": GameManager.gold, "score": GameManager.score, "ai_gold": GameManager.ai_gold,
		"bosses_defeated_this_run": GameManager.bosses_defeated_this_run,
		"bosses_defeated_this_match": GameManager.bosses_defeated_this_match,
		"unlocked_bosses": GameManager.unlocked_bosses,
		"purchased_heroes": GameManager.purchased_heroes,
		"miniboss_kill_count": GameManager.miniboss_kill_count,
		"trueboss_kill_count": GameManager.trueboss_kill_count,
		"achievements_unlocked": ids,
		"heroes_unlocked_this_match": GameManager.heroes_unlocked_this_match,
		"total_kills": GameManager.total_kills, "max_combo": GameManager.max_combo,
		"combo": {"count": GameManager.combo.count, "timer": GameManager.combo.timer,
			"last_combo": GameManager.combo.last_combo},
		"kills": kills,
		"achievement": {"current": _popup.current, "queue": _popup.queue, "timer": _popup.timer},
		"floating": GameManager.world_popups.floating_texts,
		"save": _save_projection(SaveManager.data), "writes": _writes,
		"gold_events": _gold_events, "popup_events": _popup_events,
		"active_boss": active.boss_type if is_instance_valid(active) else null,
		"pending": _main.pending_mini_bosses,
		"death_active": death != null and death.death_active,
	}


# ── Data + FIFO + overflow + gerak/expiry semua kasus popup ──
func _test_popup_queue() -> void:
	for spec in _fx["popups"]:
		_keys(spec, ["name", "enabled", "cap", "steps"], "popup case")
		var queue = QueueScript.new()
		queue.uniform_rng = _uniform
		queue.integer_rng = _integer
		queue.damage_numbers_enabled = bool(spec["enabled"])
		queue.max_damage_numbers = int(spec["cap"])
		var index := 0
		for step in spec["steps"]:
			_keys(step, ["action", "rolls", "floating"], "popup step")
			_begin_rolls(step["rolls"])
			var action: Dictionary = step["action"]
			match str(action["op"]):
				"gold":
					queue.add_gold_popup(float(action["x"]), float(action["y"]), int(action["amount"]))
				"gold_many":
					for i in range(int(action["count"])):
						queue.add_gold_popup(i, 200, i)
				"slayer":
					queue.add_slayer_text(float(action["x"]), float(action["y"]), str(action["text"]))
				"tick":
					for i in range(int(action["frames"])):
						# Dua half-frame membuktikan akumulator delta 60Hz,
						# bukan sekadar tick() yang benar tapi loop produksi salah.
						queue.advance(FRAME * 0.5)
						queue.advance(FRAME * 0.5)
				_:
					_expect(false, "operasi popup asing " + str(action["op"]))
			var tag := "%s/%d" % [spec["name"], index]
			_compare(_consumed, step["rolls"], tag + " RNG")
			_compare(queue.floating_texts, step["floating"], tag + " antrean lengkap")
			index += 1
	_rng_active = false


# ── DamageNumber node legacy bersaing dengan +G di FIFO YANG SAMA ──
func _test_shared_budget() -> void:
	_rng_active = false
	for row in _fx["shared_budget"]:
		_keys(row, ["name", "enabled", "cap", "steps"], "shared budget")
		_reset({"damage_numbers_enabled": row["enabled"], "max_damage_numbers": row["cap"]})
		var queue = GameManager.world_popups
		var legacy: Array = []
		for step in row["steps"]:
			_keys(step, ["op", "n", "texts"], "shared budget step")
			match str(step["op"]):
				"damage":
					for i in range(int(step["n"])):
						var number = DamageNumberScene.instantiate()
						number.setup("D%d" % i, false)
						_main.add_child(number)
						number.set_process(false)
						legacy.append(number)
				"gold":
					for i in range(int(step["n"])):
						GameManager.add_gold_popup(0, 0, i)
				"clear_damage":
					for number in legacy:
						if is_instance_valid(number):
							number.free()
					legacy.clear()
					queue.tick()
				_:
					_expect(false, "operasi shared budget asing " + str(step["op"]))
			_compare(queue.queued_texts(), step["texts"], str(row["name"]) + " FIFO lengkap")


# ── Defeat tetap menyimpan unlock boss; victory baru memberi hero gratis ──
func _test_outcomes() -> void:
	_rng_active = false
	for row in _fx["outcomes"]:
		_keys(row, ["victory", "bosses", "before", "after"], "outcome row")
		_reset()
		_make_sources()
		for bt in row["bosses"]:
			_run_action({"op": "kill", "boss_type": bt, "by": "blue"})
		var tag := "outcome victory=%s" % row["victory"]
		_compare(_outcome_state(), row["before"], tag + " sebelum castle jatuh")
		_clear_cinematics()
		GameManager.end_match(bool(row["victory"]))
		_compare(_outcome_state(), row["after"], tag + " sesudah end_match")
		SaveManager.load_save()
		_compare(_save_projection(SaveManager.data), row["after"]["save"], tag + " reload disk")


func _outcome_state() -> Dictionary:
	return {"gold": GameManager.gold, "score": GameManager.score,
		"run": GameManager.bosses_defeated_this_run,
		"match": GameManager.bosses_defeated_this_match,
		"save": _save_projection(SaveManager.data),
		"heroes_unlocked": GameManager.heroes_unlocked_this_match,
		"popup_events": _popup_events}


# ── Reset live lifecycle + tidak menghapus unlock saat kembali ke menu ──
func _test_reset_and_menu() -> void:
	_clear_case()
	var wanted: Dictionary = _fx["reset"]
	SaveManager.data = _save_before.duplicate(true)
	SaveManager.data["unlocked_bosses"] = wanted["unlocked_bosses"].duplicate()
	SaveManager.data["unlocked_heroes"] = wanted["purchased_heroes"].duplicate()
	GameManager.bosses_defeated_this_run = 8
	GameManager.miniboss_kill_count = 4
	GameManager.trueboss_kill_count = 4
	GameManager.achievements_unlocked = {"miniboss_kill_4": true, "trueboss_kill_4": true}
	GameManager.bosses_defeated_this_match = ["gornak", "abaddon"]
	GameManager.add_gold_popup(1, 2, 999)
	GameManager.unlock_achievement("STALE", "old match", "skull")
	GameManager.start_level(1)
	await get_tree().process_frame
	await get_tree().process_frame
	var got := {}
	for key in ["bosses_defeated_this_run", "bosses_defeated_this_match",
			"miniboss_kill_count", "trueboss_kill_count", "unlocked_bosses", "purchased_heroes"]:
		got[key] = GameManager.get(key)
	got["achievements_unlocked"] = GameManager.achievements_unlocked.keys()
	_compare(got, wanted, "reset dari Game.reset pygame")
	_expect(GameManager.world_popups.floating_texts.is_empty(), "reset membuang popup gold lama")
	_expect(_popup.queue.is_empty() and _popup.current == null, "reset membuang popup achievement lama")
	var saved_unlocks: Array = SaveManager.data["unlocked_bosses"].duplicate()
	GameManager.return_to_menu()
	_compare(SaveManager.data["unlocked_bosses"], saved_unlocks, "menu tidak clear unlock milik save")
	_expect(GameManager.unlocked_bosses.is_empty(), "menu melepas binding unlocked_bosses")
	GameManager.bind_unlocked_bosses()
	_compare(GameManager.unlocked_bosses, saved_unlocks, "match baru rebind unlock lama")


# ── Recorder file/event/RNG (tidak menggantikan gameplay) ──
func _save_projection(data: Dictionary) -> Dictionary:
	return {"unlocked_bosses": data.get("unlocked_bosses", []).duplicate(),
		"purchased_heroes": data.get("unlocked_heroes", []).duplicate(),
		"meta_gold": data.get("meta_gold", 0), "sentinel": data.get("sentinel")}


func _on_saved() -> void:
	var disk = JSON.parse_string(FileAccess.get_file_as_string(SaveManager.SAVE_PATH))
	_expect(disk is Dictionary, "save asli bisa dibaca kembali")
	if disk is Dictionary:
		_compare(_save_projection(disk), _save_projection(SaveManager.data), "save disk vs memory")
		_writes.append(_save_projection(disk))


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
	return _next_roll("uniform", a, b)


func _integer(a: int, b: int) -> int:
	if not _rng_active:
		return randi_range(a, b)
	return int(_next_roll("randint", a, b))


func _next_roll(kind: String, a: float, b: float) -> float:
	if _roll_pos >= _rolls.size():
		_expect(false, "roll popup liar: " + kind)
		return a
	var roll: Array = _rolls[_roll_pos]
	_compare([kind, a, b], roll.slice(0, 3), "situs/range RNG")
	var value := float(roll[3])
	_consumed.append([kind, a, b, value])
	_roll_pos += 1
	return value


func _death_fx():
	for node in get_tree().get_nodes_in_group("boss_death_fx"):
		if is_instance_valid(node) and not node.is_queued_for_deletion():
			return node
	return null


func _clear_cinematics() -> void:
	for node in get_tree().get_nodes_in_group("cinematic"):
		if node.has_method("finish"):
			node.finish()
		node.free()
	_main._level_intro = null
	_main._boss_banner = null
	get_tree().paused = false
	GameManager.set_paused(false)


func _clear_case() -> void:
	if not is_instance_valid(_main):
		return
	_clear_cinematics()
	_main.active_boss = null
	_main.pending_mini_bosses = []
	_main.true_boss_spawned = true
	_main.red_towers_destroyed = 0
	GameManager._hero_respawn_timers.clear()
	GameManager.clear_selection()
	for group in ["heroes", "bosses", "minions", "towers", "nexus", "bullets", "skill_projectiles", "floating_text"]:
		for node in get_tree().get_nodes_in_group(group):
			node.free()
	for node in _main.find_child("FX", true, false).get_children():
		node.free()
	_units.clear()
	_boss = null
	GameManager.blue_nexus = null
	GameManager.red_nexus = null


# ── Recursive closed-world comparison; JSON numbers may be floats ──
func _allowed_keys(dict: Dictionary, required: Array, optional: Array, tag: String) -> void:
	for key in required:
		_expect(dict.has(key), tag + " wajib punya " + str(key))
	for key in dict:
		_expect(required.has(key) or optional.has(key), tag + " key asing " + str(key))


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
		_expect(actual.size() == wanted.size(), "%s length %d != %d" % [tag, actual.size(), wanted.size()])
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
		print("[BossDeathRewardParityTest] FAIL: " + message)
		push_error("[BossDeathRewardParityTest] " + message)


func _finish() -> void:
	_rng_active = false
	GameManager.world_popups.uniform_rng = randf_range
	GameManager.world_popups.integer_rng = randi_range
	if SaveManager.saved.is_connected(_on_saved):
		SaveManager.saved.disconnect(_on_saved)
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
		print("[BossDeathRewardParityTest] PASS: %d checks reward boss vs oracle pygame" % _checks)
	else:
		print("[BossDeathRewardParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
