# Headless regression Fase 5d (cinematic port _render.py):
#   1. Level intro muncul saat start_level + membekukan gameplay + skip SPACE,
#   2. Banner boss muncul saat mini boss turun + skip ESC,
#   3. Boss mati -> BossDeathFX pause (fase kematian) -> perayaan true boss
#      (BOSS DEFEATED! + gold reward) -> skip klik,
#   4. Mini boss mati tanpa perayaan, FX selesai sendiri tanpa sisa pause.
# godot --headless --path godot res://tests/CinematicTest.tscn --quit-after 240
# Require "[CinematicTest] PASS" dan tanpa SCRIPT ERROR / Parse Error.
extends Node

const MainScene = preload("res://scenes/main.tscn")

var _failures: int = 0
var _main = null
var _done: bool = false


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	_main = MainScene.instantiate()
	add_child(_main)
	await get_tree().process_frame
	await get_tree().process_frame

	var connector := get_tree().get_first_node_in_group("game_connector")
	_expect(connector != null, "GameManagerConnector harus ada")
	if connector != null and connector.has_method("start_match"):
		connector.start_match(1)
	else:
		GameManager.start_level(1, false)
	await _wait_frames(3)

	# ── 1. LEVEL INTRO ──
	var intro = _main.get("_level_intro")
	_expect(is_instance_valid(intro), "Level intro harus muncul setelah start_level")
	_expect(get_tree().paused, "Level intro harus membekukan gameplay")
	_expect(GameManager.is_paused, "Gold/wave harus ikut beku selama intro")
	if is_instance_valid(intro):
		# Tombol lain (mis. T) tidak boleh menutup intro — paritas handle_skip
		# pygame hanya menerima SPACE/ENTER/klik.
		var wrong := _key(KEY_T)
		_main._on_key(wrong)
		_expect(is_instance_valid(intro) and intro.cinematic_active(),
			"Intro tidak boleh skip oleh tombol selain SPACE/ENTER")
		_main._on_key(_key(KEY_SPACE))
	await _wait_frames(3)
	_expect(not get_tree().paused, "Skip intro harus melepas pause")
	_expect(not GameManager.is_paused, "Skip intro harus melepas is_paused")

	# ── 2. BANNER MINI BOSS ──
	_main.pending_mini_bosses.append("gornak")
	_main.active_boss = null
	_main._boss_tick(1.0 / 60.0)
	var banner = _main.get("_boss_banner")
	_expect(is_instance_valid(banner), "Banner harus muncul saat mini boss spawn")
	_expect(not get_tree().paused, "Banner boss TIDAK boleh pause gameplay")
	if is_instance_valid(banner):
		_expect(banner.boss_name == "Gornak", "Banner harus membaca nama bosses.json")
		_main._on_key(_key(KEY_ESCAPE))
		await _wait_frames(2)
		_expect(not is_instance_valid(banner) or not banner.cinematic_active(),
			"ESC harus menutup banner")
	# Bersihkan boss mini supaya tidak mengganggu tes kematian di bawah.
	if is_instance_valid(_main.active_boss):
		_main.active_boss.free()
		_main.active_boss = null

	# ── 3. KEMATIAN TRUE BOSS: fase kematian pause -> perayaan -> skip ──
	var boss = GameManager.spawn_boss("abaddon", "red", Vector2(640, 360))
	_expect(boss != null, "True boss harus bisa di-spawn")
	_expect(int(boss.gold_reward) == 1500,
		"gold_reward abaddon harus 1500 dari bosses.json")
	boss.hp = 1.0
	boss.take_damage(99999.0, "blue")
	var fx = _find_death_fx()
	_expect(fx != null, "BossDeathFX harus dibuat saat boss mati")
	_expect(get_tree().paused, "Fase kematian harus pause gameplay")
	if fx != null:
		# Selama fase kematian, skip klik TIDAK boleh menutup (paritas
		# handle_skip hanya aktif saat celebration).
		_expect(not fx.skip_click(), "Fase kematian tidak boleh bisa di-skip")
		var guard := 0
		while guard < 240 and is_instance_valid(fx) and fx.death_active:
			await get_tree().process_frame
			guard += 1
		_expect(is_instance_valid(fx) and fx.celebration_active,
			"True boss harus masuk fase perayaan setelah kematian")
		_expect(not get_tree().paused, "Perayaan tidak boleh pause gameplay")
		if is_instance_valid(fx) and fx.celebration_active:
			_expect(fx._label_reward.text.find("1500") >= 0,
				"Teks reward perayaan harus menampilkan gold_reward")
			fx.skip_click()
			await _wait_frames(2)
		_expect(not is_instance_valid(fx) or not fx.active,
			"Skip klik harus mengakhiri perayaan")
	_expect(not get_tree().paused, "Tidak boleh ada pause tersisa setelah perayaan")
	GameManager.set_paused(false)

	# ── 4. KEMATIAN MINI BOSS: tanpa perayaan, selesai sendiri ──
	var mini = GameManager.spawn_boss("gornak", "red", Vector2(700, 300))
	mini.hp = 1.0
	mini.take_damage(99999.0, "blue")
	var fx2 = _find_death_fx()
	_expect(fx2 != null, "BossDeathFX mini boss harus dibuat")
	if fx2 != null:
		_expect(not fx2.show_celebration, "Mini boss tidak punya perayaan")
		var guard2 := 0
		while guard2 < 180 and is_instance_valid(fx2):
			await get_tree().process_frame
			guard2 += 1
		_expect(not is_instance_valid(fx2), "FX mini boss harus selesai sendiri")
	_expect(not get_tree().paused, "Tidak boleh ada pause tersisa setelah mini boss")
	GameManager.set_paused(false)

	_finish()


func _find_death_fx():
	for n in get_tree().get_nodes_in_group("boss_death_fx"):
		if is_instance_valid(n):
			return n
	return null


func _key(code: Key) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = code
	ev.pressed = true
	return ev


func _wait_frames(n: int) -> void:
	for _i in range(n):
		await get_tree().process_frame


func _finish() -> void:
	if _done:
		return
	_done = true
	get_tree().paused = false
	GameManager.set_paused(false)
	if is_instance_valid(_main):
		_main.free()
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[CinematicTest] PASS: level intro, banner boss, death FX + perayaan")
	get_tree().quit(0 if _failures == 0 else 1)


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		push_error("[CinematicTest] " + message)
