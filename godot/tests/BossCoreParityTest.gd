# BossCoreParityTest — Fase 6: paritas inti boss vs bosses/base_boss.py.
#
# Fixture `match_parity.json["boss_core"]` dievaluasi dari kelas Boss Pygame
# ASLI oleh tools/test_godot_match_parity.py (bukan salinan rumus Godot):
#   * data 216 boss (hp/damage/speed/range/attack_cooldown/radius/armor/MR +
#     ability/ability2/min_prefer distance + daftar smart-AI dari AST
#     Boss.update) — dibandingkan dengan isi bosses.json yang dibaca BossDB;
#   * nilai ENRAGED dihasilkan dengan benar-benar memanggil Boss.update()
#     pygame pada HP ambang (hp 50% true / 40% mini), jadi pengujian Godot
#     memakai oracle hasil Pygame, bukan rumus yang disalin.
#
# Di sini perilaku runtime Boss.gd diuji: resilience + anti-burst, entrance
# freeze, enrage/frenzy, tenacity slow/atk_slow, heal ability2 true boss,
# cleave serangan dasar, dan ability generik boss tanpa smart-AI.
#
# godot --headless --path godot res://tests/BossCoreParityTest.tscn --quit-after 300
# Require "[BossCoreParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const BossScene = preload("res://scenes/boss/Boss.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done: bool = false
## Semua pesan kegagalan dikumpulkan di sini supaya tercetak ke STDOUT pada
## akhir run (tail log CI langsung memuat alasannya — tidak bergantung pada
## anotasi ::error:: yang dipotong 400 karakter oleh workflow).
var _error_messages: Array[String] = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if not _fixture.has("boss_core"):
		push_error("[BossCoreParityTest] fixture boss_core belum ada — jalankan "
			+ "tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	GameManager.in_menu = true
	GameManager.state = "idle"
	_test_data_export_parity()
	await _test_node_behaviors()
	_finish()


## 1) bosses.json (yang dibaca BossDB → Boss.gd) cocok dengan oracle Pygame
## untuk SEMUA boss type.
func _test_data_export_parity() -> void:
	var rows: Array = _fixture["boss_core"]["bosses"]
	var checked := 0
	for row in rows:
		var bt := str(row["boss_type"])
		var s: Dictionary = BossDB.get_boss(bt)
		_expect(not s.is_empty(), "BossDB punya " + bt)
		if s.is_empty():
			continue
		_expect(int(s.get("hp", -1)) == int(row["hp"]), "%s hp" % bt)
		_expect(int(s.get("damage", -1)) == int(row["damage"]), "%s damage" % bt)
		_near(float(s.get("speed", -1)), float(row["speed"]), "%s speed" % bt)
		_expect(int(s.get("range", -1)) == int(row["range"]), "%s range" % bt)
		_expect(int(s.get("attack_cooldown", -1)) == int(row["attack_cooldown_frames"]),
			"%s attack_cooldown" % bt)
		_expect(int(s.get("radius", -1)) == int(row["radius"]), "%s radius" % bt)
		_expect(int(s.get("armor", -1)) == int(row["armor"]), "%s armor" % bt)
		_near(float(s.get("magic_resist", -1.0)), float(row["magic_resist"]),
			"%s magic_resist" % bt)
		_expect(str(s.get("boss_class", "")) == str(row["boss_class"]),
			"%s boss_class" % bt)
		_expect(int(s.get("ability_cooldown", -1)) == int(row["ability_cooldown_frames"]),
			"%s ability_cooldown" % bt)
		_expect(int(s.get("ability_damage", -1)) == int(row["ability_damage"]),
			"%s ability_damage" % bt)
		_expect(int(s.get("ability_range", -1)) == int(row["ability_range"]),
			"%s ability_range" % bt)
		_expect(int(s.get("ability2_cooldown", -1)) == int(row["ability2_cooldown_frames"]),
			"%s ability2_cooldown" % bt)
		_near(float(s.get("ability2_heal_pct", -1.0)), float(row["ability2_heal_pct"]),
			"%s ability2_heal_pct" % bt)
		_expect(int(s.get("min_distance", -1)) == int(row["min_distance"]),
			"%s min_distance" % bt)
		_expect(int(s.get("prefer_distance", -1)) == int(row["prefer_distance"]),
			"%s prefer_distance" % bt)
		checked += 1
	_expect(checked == rows.size(), "Semua baris boss terverifikasi (%d)" % rows.size())
	# Boss dengan smart-AI di Pygame tidak boleh jatuh ke ability generik.
	for bt in ["gornak", "morgath", "drakar", "abaddon", "krobellus"]:
		for row in rows:
			if str(row["boss_type"]) == bt:
				_expect(bool(row["uses_smart_ai"]) == (bt != "krobellus"),
					"%s uses_smart_ai flag" % bt)


## 2) Perilaku runtime Boss.gd (node asli, bukan data).
func _test_node_behaviors() -> void:
	await _test_stats_and_entrance()
	await _test_resilience_and_cap()
	await _test_enrage()
	await _test_tenacity()
	await _test_true_boss_heal()
	await _test_cleave_and_generic_ability()
	print("[BossCoreParityTest] %d checks" % _checks)


func _spawn_boss(boss_type: String, pos: Vector2):
	var boss = BossScene.instantiate()
	boss.boss_type = boss_type
	boss.team = "red"
	boss.position = pos
	add_child(boss)
	await get_tree().process_frame
	boss.set_physics_process(false)
	return boss


func _spawn_goblin(team: String, pos: Vector2):
	var m = MinionScene.instantiate()
	m.minion_type = "goblin"
	m.team = team
	m.lane = "mid"
	m.lane_path = PackedVector2Array()
	m.position = pos
	add_child(m)
	await get_tree().process_frame
	m.set_physics_process(false)
	return m


func _test_stats_and_entrance() -> void:
	var gornak = await _spawn_boss("gornak", Vector2(600, 360))
	var row := _row("gornak")
	_expect(int(gornak.max_hp) == int(row["hp"]), "gornak node max_hp")
	_expect(gornak.damage_reduction == 0.20, "gornak DR mini 20%")
	_near(gornak.armor, float(row["armor"]), "gornak node armor")
	_expect(gornak.has_smart_ai, "gornak pakai smart-AI (bukan ability generik)")
	_expect(not gornak.is_ranged_kiter(), "gornak bukan kiter ranged")
	# Entrance freeze: mini 120 frame (2 s). Godot headless men-tick physics
	# 1-7 frame selama add_child → process_frame, jadi beri toleransi kecil
	# (nilai awal persis 2.0 dibuktikan data export + entri test di bawah;
	# yang penting di sini boss masih dalam jendela entrance).
	_near(gornak.entrance_timer, 120.0 / 60.0, "gornak entrance 2 s (±auto-tick)", 0.35)
	var dummy = await _spawn_goblin("blue", Vector2(610, 360)) # dalam aggro+range
	gornak.set_physics_process(true)
	gornak._physics_process(0.1)
	_expect(gornak.entrance_timer > 0.0, "Entrance masih berjalan setelah 0,1 s")
	_expect(gornak.target == null, "Boss tidak aggro selama entrance")
	gornak.entrance_timer = 0.0
	gornak._physics_process(0.02) # frame normal: target harus terambil
	_expect(gornak.target != null and is_instance_valid(gornak.target),
		"Boss aggro setelah entrance habis (range + 100)")
	gornak.set_physics_process(false)
	gornak.queue_free()

	var morgath = await _spawn_boss("morgath", Vector2(400, 360))
	_expect(morgath.is_ranged_kiter(), "morgath kiter ranged dalam RANGED_KITE")
	var mrow := _row("morgath")
	_near(morgath.min_distance, float(mrow["min_distance"]),
		"morgath min_distance dari boss_data (%s)" % mrow["min_distance"])
	_near(morgath.prefer_distance, float(mrow["prefer_distance"]),
		"morgath prefer_distance dari boss_data")
	morgath.queue_free()


func _test_resilience_and_cap() -> void:
	# Mini boss: DR 20% + cap 12% max HP (base_boss.py 6025-6037).
	var gornak = await _spawn_boss("gornak", Vector2(300, 100))
	var row := _row("gornak")
	gornak.armor = 0.0
	gornak.magic_resist = 0.0
	var hp_before: float = gornak.hp
	var dealt := CombatSystem.apply_damage(gornak, 5000.0, "blue", "normal", null, "physical")
	var cap := int(gornak.max_hp * 0.12)
	_expect(dealt == float(cap), "Anti-burst cap mini = 12%% max HP (kena %d, cap %d)" % [int(dealt), cap])
	_expect(gornak.hp == hp_before - float(cap), "HP boss berkurang persis cap")
	gornak.hp = gornak.max_hp
	var dealt2 := CombatSystem.apply_damage(gornak, 100.0, "blue", "normal", null, "physical")
	_expect(dealt2 == float(int(100.0 * 0.8)), "DR mini 20%% tanpa cap (80 vs %d)" % int(dealt2))
	# True boss: DR 30% + cap 8%.
	var abaddon = await _spawn_boss("abaddon", Vector2(640, 100))
	abaddon.armor = 0.0
	abaddon.magic_resist = 0.0
	var hp2: float = abaddon.hp
	var dealt3 := CombatSystem.apply_damage(abaddon, 999999.0, "blue", "normal", null, "physical")
	var cap_t := int(abaddon.max_hp * 0.08)
	_expect(dealt3 == float(cap_t), "Anti-burst cap true = 8%% max HP (%d vs %d)" % [int(dealt3), cap_t])
	_expect(abaddon.hp == hp2 - float(cap_t), "HP true boss berkurang persis cap")
	gornak.queue_free()
	abaddon.queue_free()


func _test_enrage() -> void:
	# Mini boss frenzy di HP <= 40% — angka oracle dari update() Pygame.
	var gornak = await _spawn_boss("gornak", Vector2(300, 200))
	var row := _row("gornak")
	gornak.hp = gornak.max_hp * 0.40
	gornak._tick_enrage(1.0 / 60.0)
	_expect(gornak.is_enraged, "Frenzy mini terpicu di HP 40%%")
	_expect(gornak.damage == float(row["enraged_damage"]),
		"Damage mini setelah frenzy == oracle Pygame (%d vs %d)" % [int(gornak.damage), int(row["enraged_damage"])])
	_near(gornak.move_speed / 60.0, float(row["enraged_speed"]),
		"Speed mini setelah frenzy == oracle Pygame")
	_expect(int(gornak.attack_cooldown * 60.0) == int(row["enraged_attack_cd_frames"]),
		"Attack CD mini setelah frenzy (%d vs %d)" % [int(gornak.attack_cooldown * 60), int(row["enraged_attack_cd_frames"])])
	gornak.queue_free()

	# True boss enrage di HP <= 50%.
	var abaddon = await _spawn_boss("abaddon", Vector2(640, 200))
	var row2 := _row("abaddon")
	abaddon.hp = abaddon.max_hp * 0.50
	abaddon._tick_enrage(1.0 / 60.0)
	_expect(abaddon.is_enraged, "Enrage true terpicu di HP 50%%")
	_expect(abaddon.damage == float(row2["enraged_damage"]),
		"Damage true setelah enrage == oracle Pygame (%d vs %d)" % [int(abaddon.damage), int(row2["enraged_damage"])])
	_near(abaddon.move_speed / 60.0, float(row2["enraged_speed"]),
		"Speed true setelah enrage == oracle Pygame")
	abaddon.queue_free()


func _test_tenacity() -> void:
	var gornak = await _spawn_boss("gornak", Vector2(300, 300))
	# Slow dari Ice Tower: magnitude & durasi dipotong 50%, magnitude max 0.35
	gornak.status.apply_slow(0.5, 6.0)
	_near(gornak.status.slow_amount, 0.25, "Boss slow magnitude terpotong tenacity")
	_near(gornak.status.slow_timer, 3.0, "Boss slow durasi terpotong tenacity")
	gornak.status.apply_slow(0.9, 10.0)
	_expect(gornak.status.slow_amount <= 0.35 + 0.0001, "Slow boss tidak lebih dari 0.35")
	# atk_slow juga kena tenacity
	gornak.status.apply_attack_slow(0.6, 8.0)
	_expect(gornak.status.atk_slow_amount <= 0.35 + 0.0001, "atk_slow boss cap 0.35")
	_near(gornak.status.atk_slow_amount, 0.3, "atk_slow boss 0.6 -> 0.3")
	_near(gornak.status.atk_slow_timer, 4.0, "atk_slow boss durasi -> 4 s")
	# Stun boss dipotong 55% (BOSS_STUN_FACTOR 0.45)
	gornak.status.apply_stun(2.0)
	_near(gornak.status.stun_timer, 0.9, "Stun boss 2 s -> 0.9 s")
	gornak.queue_free()


func _test_true_boss_heal() -> void:
	var abaddon = await _spawn_boss("abaddon", Vector2(640, 300))
	var row := _row("abaddon")
	_expect(int(row["ability2_cooldown_frames"]) > 0, "Abaddon punya ability2")
	abaddon.hp = abaddon.max_hp * 0.20
	var before: float = abaddon.hp
	abaddon._use_heal_ability()
	var expected := int(abaddon.max_hp * float(row["ability2_heal_pct"]))
	_expect(abaddon.hp == before + float(expected),
		"Heal ability2 true boss = max_hp × %.2f (+%d)" % [float(row["ability2_heal_pct"]), expected])
	_near(abaddon.ability2_timer, float(row["ability2_cooldown_frames"]) / 60.0,
		"Cooldown ability2 true boss")
	abaddon.queue_free()


func _test_cleave_and_generic_ability() -> void:
	# Cleave: 40% damage ke musuh lain radius 80 dari boss.
	var gornak = await _spawn_boss("gornak", Vector2(100, 500))
	var target = await _spawn_goblin("blue", Vector2(150, 500))
	var neighbor = await _spawn_goblin("blue", Vector2(160, 500)) # dalam 80 px
	target.hp = target.max_hp
	neighbor.hp = neighbor.max_hp
	gornak.target = target
	var neighbor_before: float = neighbor.hp
	gornak.try_attack()
	_expect(neighbor.hp < neighbor_before, "Cleave splash melukai musuh lain radius 80")
	gornak.queue_free()
	target.queue_free()
	neighbor.queue_free()

	# Boss tanpa smart-AI memakai ability generik (cooldown/damage/range data).
	var krobellus = await _spawn_boss("krobellus", Vector2(400, 500))
	var row := _row("krobellus")
	_expect(not krobellus.has_smart_ai, "Krobellus tidak punya smart-AI pygame")
	_expect(int(row["ability_range"]) > 0, "Krobellus punya ability generik")
	var victim = await _spawn_goblin("blue", Vector2(430, 500))
	victim.hp = victim.max_hp
	var v_before: float = victim.hp
	krobellus.target = victim
	krobellus.attack_timer = 0.0
	krobellus.ability_timer = 0.0
	krobellus._after_attack() # cleave (tidak ada musuh lain) + ability generik
	_expect(krobellus.ability_active, "Ability generik mengaktifkan aura/state")
	_expect(victim.hp < v_before, "Ability generik melukai musuh dalam ability_range")
	krobellus.queue_free()
	victim.queue_free()


func _row(boss_type: String) -> Dictionary:
	for row in _fixture["boss_core"]["bosses"]:
		if str(row["boss_type"]) == boss_type:
			return row
	return {}


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		var line := "[BossCoreParityTest] %s: %.4f != %.4f" % [message, a, b]
		_error_messages.append(line)
		_failures += 1
		push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		var line := "[BossCoreParityTest] " + message
		_error_messages.append(line)
		_failures += 1
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
		print("[BossCoreParityTest] PASS: data export + inti boss (%d checks)" % _checks)
	else:
		# Cetak SETIAP kegagalan ke stdout (bukan hanya push_error) supaya tail
		# log CI memuat alasan lengkapnya — debug tidak butuh anotasi error.
		for msg in _error_messages:
			print(msg)
		push_error("[BossCoreParityTest] %d failures dari %d checks" % [_failures, _checks])
		print("[BossCoreParityTest] FAIL: %d failures dari %d checks" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
