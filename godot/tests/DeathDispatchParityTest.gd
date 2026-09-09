# FASE 16 — seluruh daftar headless death_dispatch direplay, bukan subset /
# pemeriksaan string sumber. Oracle = jalur SERANGAN NYATA pygame
# (Tower._shoot -> Bullet._on_hit, Hero._do_attack melee & proyektil,
# Minion.update, skill/kit) + loop reward Game.update (_core.py:2196-2235).
#
# pytest oracle menandai mati di take_damage dan membayar di frame berikutnya;
# Godot membayar LANGSUNG di CombatSystem.apply_damage langkah 10
# (_dispatch_death). Karena itu yang dibandingkan adalah state SETELAH loop
# reward pygame berjalan — kedua model wajib berakhir di titik yang sama.
#
# Godot: Main/HUD/Hero/Minion/Tower SUNGGUHAN, dan serangan dijalankan lewat
# JALUR PRODUKSI, bukan take_damage(1e9):
#   tower_bullet  Tower._shoot(CombatSystem) -> TowerBullet._physics_process
#                 -> _on_hit -> apply_damage(..., source=null)
#   hero_melee    Hero.try_attack() -> apply_damage(instan, source=hero)
#   hero_ranged   Hero.try_attack() -> TowerBullet proyektil (source=hero)
#   minion_attack Minion.try_attack() -> apply_damage(source=null)
#   skill/direct  CombatSystem.apply_damage langsung (jalur kit/DoT)
#
# TIDAK ADA panggilan register_minion_death / register_tower_death /
# register_hero_death manual, dan TIDAK ADA pemanggilan die() langsung:
# reward boleh muncul HANYA sebagai akibat dispatch. `_run_kill` pola
# MinionTowerRewardParityTest (FASE 15) sengaja TIDAK dipakai — jalur itu
# memanggil take_damage(1e9)+die() dan karena itu melewati dispatch yang
# justru sedang diuji di sini.
#
# Snapshot per unit HANYA dead/hp/rewarded/team — tanpa identitas pembunuh,
# karena Tower.die(killer_team, _killer) memang MEMBUANG killer di Godot.
# Atribusi kill dibaca terpisah dari hasil akhirnya (hero.kills).
#
# Jalankan dengan XDG_DATA_HOME=$(mktemp -d) agar user:// TERISOLASI.
# Data+file save di-snapshot lalu dipulihkan di akhir. Piksel dan SFX
# (damage number, ledakan cannon, suara menara hancur) BELUM TERUJI.
extends Node

const FIXTURE := "res://tests/fixtures/match_parity.json"
const MainScene = preload("res://scenes/main.tscn")
const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const FRAME := 1.0 / 60.0

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
	if not (fixture is Dictionary) or not fixture.has("death_dispatch"):
		_expect(false, "fixture death_dispatch belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_finish()
		return
	_fx = fixture["death_dispatch"]
	_keys(_fx, ["fps", "initial", "scenarios"], "seksi fixture")
	_compare(GameManager.FPS, _fx["fps"], "FPS")
	_expect(CombatSystem.death_dispatch_enabled,
		"dispatch kematian harus AKTIF di harness ini (default produksi)")

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
	# Main di luar menu otomatis memulai battle + intro level yang MEMBEKUKAN
	# SceneTree (pola _clear_cinematics FASE 14/15).
	_clear_cinematics()

	for spec in _fx["scenarios"]:
		_test_scenario(spec)

	_finish()


# ══════════════════════════════════════════════════════════
#  SKENARIO
# ══════════════════════════════════════════════════════════

func _test_scenario(spec: Dictionary) -> void:
	_keys(spec, ["name", "initial", "units", "attack", "pre", "expect_death",
		"steps"], "scenario")
	var tag := str(spec["name"])
	_reset(spec["initial"])
	_make_units(spec["units"])

	# Snapshot PRA-serangan: setup Godot harus identik dengan oracle SEBELUM
	# apa pun terjadi, supaya kegagalan menunjuk ke setup, bukan ke dispatch.
	_compare(_snapshot(), spec["pre"], tag + "/pre")

	_run_attack(spec["attack"])
	var index := 0
	for step in spec["steps"]:
		_keys(step, ["frames", "attack", "snapshot"], "step")
		if step["attack"] != null:
			# Pukulan lanjutan (mis. memukul mayat lagi) — oracle merekamnya
			# di langkah ini, jadi dieksekusi sebelum frame di-step.
			_run_attack(step["attack"])
		for _f in range(int(step["frames"])):
			# Satu frame oracle = Game.update: countdown respawn hero + tick
			# combo + tick antrean popup. Income gold dibekukan oracle lewat
			# GOLD_PER_SECOND=0 (pola MatchScoring FASE 13).
			GameManager._update_hero_respawns(FRAME)
			GameManager._tick_combo(FRAME)
			GameManager.world_popups.advance(FRAME)
		_compare(_snapshot(), step["snapshot"], "%s/%d" % [tag, index])
		index += 1

	# Guard eksplisit sisi negatif: skenario tanpa kematian tidak boleh
	# membayar apa pun, walau damage-nya besar.
	var last: Dictionary = spec["steps"][spec["steps"].size() - 1]["snapshot"]
	if not bool(spec["expect_death"]):
		for uid in last["units"]:
			_expect(not bool(last["units"][uid]["dead"]),
				tag + " guard: " + uid + " tidak boleh mati")
			_expect(not bool(last["units"][uid]["rewarded"]),
				tag + " guard: " + uid + " tidak boleh dibayar")
		_expect(int(last["total_kills"]) == int(_fx["initial"]["total_kills"]),
			tag + " guard: total_kills diam")
		_expect(int(last["red_towers_destroyed"])
			== int(_fx["initial"]["red_towers_destroyed"]),
			tag + " guard: red_towers_destroyed diam")
	else:
		var died := 0
		for uid in last["units"]:
			if bool(last["units"][uid]["dead"]):
				died += 1
				_expect(bool(last["units"][uid]["rewarded"]),
					tag + ": " + uid + " mati harus dibayar tepat sekali")
		_expect(died > 0, tag + ": harus ada unit mati")

	# Bukti "source peluru = None": peluru menara tidak pernah memberi kill
	# credit, dan tidak pernah memantulkan Bristleback ke menaranya.
	if str(spec["attack"]["kind"]) == "tower_bullet":
		_compare(_hero_kills(), spec["pre"]["hero_kills"],
			tag + " tanpa kill credit dari peluru")
		var shooter = _units[str(spec["attack"]["by"])]
		if is_instance_valid(shooter):
			_compare(shooter.hp, float(spec["pre"]["units"]
				[str(spec["attack"]["by"])]["hp"]),
				tag + " HP penembak utuh (tanpa reflect)")


# ══════════════════════════════════════════════════════════
#  SETUP
# ══════════════════════════════════════════════════════════

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
	# FX kontak hit diisolasi dari klaster ini (oracle pygame tidak
	# membandingkan damage number di sini). Popup gold tetap hidup.
	GameManager.world_popups.damage_numbers_enabled = false
	_main.red_towers_destroyed = int(init["red_towers_destroyed"])
	_main.true_boss_spawned = true
	_main.active_boss = null
	_main.pending_mini_bosses = []


func _make_units(units_spec: Array) -> void:
	_units.clear()
	for uspec in units_spec:
		_allowed_keys(uspec, ["id", "kind", "team", "x", "y"],
			["type", "hp", "tower_kind", "tower_type", "bristleback", "arena"],
			"unit spec")
		var unit = null
		match str(uspec["kind"]):
			"minion":
				unit = MinionScene.instantiate()
				unit.minion_type = str(uspec["type"])
				unit.team = str(uspec["team"])
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
		unit.position = Vector2(float(uspec["x"]), float(uspec["y"]))
		_main.find_child("Containers", true, false).add_child(unit)
		# Unit arena TIDAK di-update sendiri (process off): satu-satunya
		# damage dalam sebuah skenario adalah damage yang di-script.
		unit.set_physics_process(false)
		if str(uspec["kind"]) == "tower":
			# Oracle men-set shield = 0 supaya mitigasi sekolah menara yang
			# diuji, bukan lapisan shield (paritas harness FASE 16).
			unit.shield = 0.0
			if uspec.has("tower_type"):
				# Lewat upgrade() ASLI: cannon/ice baru punya splash & slow
				# di LEVEL 2 (TOWER_UPGRADE_PATHS / TowerDB).
				_expect(unit.upgrade(str(uspec["tower_type"])),
					"upgrade menara " + str(uspec["tower_type"]))
		elif str(uspec["kind"]) == "minion":
			# Oracle membekukan regen minion (paritas harness FASE 16).
			unit.regen_per_second = 0.0
			unit.attack_timer = 0.0
		else:
			unit.attack_timer = 0.0
			if bool(uspec.get("bristleback", false)):
				unit.kit["_bristleback_active"] = true
		if uspec.has("hp"):
			unit.hp = float(uspec["hp"])
		_units[str(uspec["id"])] = unit


# ══════════════════════════════════════════════════════════
#  JALUR SERANGAN NYATA (bukan take_damage 1e9)
# ══════════════════════════════════════════════════════════

func _run_attack(atk: Dictionary) -> void:
	_allowed_keys(atk, ["kind", "target"],
		["by", "source", "amount", "from_team", "dmg_type", "school"], "attack")
	var tgt = _units[str(atk["target"])]
	match str(atk["kind"]):
		"tower_bullet":
			var tw = _units[str(atk["by"])]
			tw.attack_timer = 0.0
			tw.target = tgt
			var d: Vector2 = tgt.global_position - tw.global_position
			tw.angle = atan2(d.y, d.x)
			# _shoot PRODUKSI: membuat TowerBullet dengan source = null
			# (paritas Bullet._on_hit pygame tanpa source).
			tw._shoot(CombatSystem)
			_fly_bullets()
			tw.target = null
		"hero_melee":
			var hero = _units[str(atk["by"])]
			_expect(bool(hero.is_melee_hero),
				str(atk["by"]) + " harus hero melee")
			hero.attack_timer = 0.0
			hero.target = tgt
			hero.try_attack()
		"hero_ranged":
			var hero = _units[str(atk["by"])]
			_expect(not bool(hero.is_melee_hero),
				str(atk["by"]) + " harus hero ranged")
			hero.attack_timer = 0.0
			hero.target = tgt
			hero.try_attack()
			_fly_bullets()
		"minion_attack":
			var minion = _units[str(atk["by"])]
			minion.attack_timer = 0.0
			minion.target = tgt
			minion.try_attack()
			_fly_bullets()
		"skill", "direct":
			var src = null
			if atk.get("source") != null:
				src = _units[str(atk["source"])]
			var school := ""
			if atk.get("school") != null:
				school = str(atk["school"])
			# Jalur yang dipakai skill hero / DoT / cleave / reflect:
			# apply_damage langsung, dispatch tetap jalan dari langkah 10.
			CombatSystem.apply_damage(tgt, float(atk["amount"]),
				str(atk.get("from_team", "")), str(atk.get("dmg_type",
				"normal")), src, school)
		_:
			_expect(false, "jenis serangan asing " + str(atk["kind"]))


## Terbangkan peluru/proyektil sampai semuanya mendarat. `_physics_process`
## dipanggil manual supaya deterministik (tanpa bergantung jumlah frame nyata)
## — fungsinya tetap fungsi produksi yang sama, jadi `_on_hit` (damage,
## splash cannon, slow ice, dispatch kematian) benar-benar dijalankan.
func _fly_bullets() -> void:
	for _i in range(1200):
		var pending: Array = []
		for b in get_tree().get_nodes_in_group("bullets"):
			if is_instance_valid(b) and not (b as Node).is_queued_for_deletion():
				pending.append(b)
		if pending.is_empty():
			return
		for b in pending:
			(b as Node2D)._physics_process(FRAME)
	_expect(false, "proyektil tidak pernah mendarat")


# ══════════════════════════════════════════════════════════
#  SNAPSHOT
# ══════════════════════════════════════════════════════════

func _snapshot() -> Dictionary:
	return {
		"gold": GameManager.gold, "score": GameManager.score,
		"ai_gold": GameManager.ai_gold,
		"total_kills": GameManager.total_kills,
		"max_combo": GameManager.max_combo,
		"combo": {"count": GameManager.combo.count,
			"timer": GameManager.combo.timer,
			"last_combo": GameManager.combo.last_combo},
		"red_towers_destroyed": _main.red_towers_destroyed,
		"units": _unit_states(), "hero_kills": _hero_kills(),
	}


## dead/hp/rewarded/team SAJA — identitas pembunuh sengaja tidak direkam
## (Tower.die membuang killer di Godot).
func _unit_states() -> Dictionary:
	var out := {}
	for uid in _units:
		var unit = _units[uid]
		out[uid] = {"dead": bool(unit.is_dead), "hp": float(unit.hp),
			"rewarded": bool(unit.reward_processed),
			"team": str(unit.team)}
	return out


func _hero_kills() -> Dictionary:
	var out := {}
	for uid in _units:
		var unit = _units[uid]
		if "hero_type" in unit:
			out[uid] = int(unit.kills)
	return out


# ══════════════════════════════════════════════════════════
#  BERSIHKAN
# ══════════════════════════════════════════════════════════

## Cinematic (intro level/banner) memegang pause SceneTree — lepas supaya
## langkah frame manual benar-benar men-tick combo/popup (pola FASE 14/15).
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
	# `free()` (bukan queue_free) supaya peluru skenario sebelumnya benar-benar
	# hilang dari grup "bullets" sebelum skenario berikutnya dihitung.
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
		print("[DeathDispatchParityTest] FAIL: " + message)
		push_error("[DeathDispatchParityTest] " + message)


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
		print("[DeathDispatchParityTest] PASS: %d checks dispatch kematian vs oracle pygame" % _checks)
	else:
		print("[DeathDispatchParityTest] FAIL: %d/%d checks gagal" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
