# TouchHudParityTest — FASE 23: TouchHUD (mobile/hud.py) terpasang & bekerja.
#
# BUKAN oracle pygame (perilaku tombol = data HudLayout yang SUDAH dikunci
# UiHudParityTest vs fixture touchhud): yang diuji di sini INTEGRASI yang
# selama ini hilang — node TouchHUD ada di HUD paling atas, geometri =
# kanon, matriks visibilitas + override panel + sembunyi-di-menu lewat
# sync produksi, tap -> signal hud_action, dan router Main
# (_apply_touch_action) mencapai efek pygame-nya (pause/skip/replay/
# next/menu/debug/back) termasuk guard-nya.
#
# godot --headless --path godot res://tests/TouchHudParityTest.tscn --quit-after 300
extends Node

const MainScene = preload("res://scenes/main.tscn")
## Urutan enum State MainMenu.gd: MAIN..PAUSE (dipakai int, tanpa class_name).
const MENU_STATE_MAIN := 0
const MENU_STATE_PAUSE := 7

var _failures: int = 0
var _main = null
var _hud: Control = null
var _menu = null
var _touch = null
var _taps: Array = []


## Cinematic palsu untuk uji watchdog: klaimnya bisa dinyalakan/dimatikan dan
## node ini MEMENUHI kontrak bukti-hidup Main._cine_live (benar-benar di tree
## + benar-benar memproses frame), supaya yang diuji adalah klaim basi dari
## node hidup — persis keluhan "SKIP menempel selama wave".
class FakeCine:
	extends Node

	var claim := false

	func _ready() -> void:
		add_to_group("cinematic")

	func _process(_delta: float) -> void:
		pass

	func cinematic_active() -> bool:
		return claim

	func skip_click() -> bool:
		claim = false
		return true


func _ready() -> void:
	_run.call_deferred()


func _record(action: String) -> void:
	_taps.append(action)


func _expect(cond: bool, message: String) -> void:
	if not cond:
		_failures += 1
		push_error("[TouchHudParityTest] FAIL: %s" % message)
		print("[TouchHudParityTest] FAIL: %s" % message)


func _step(label: String) -> void:
	print("[TouchHudParityTest] step: %s" % label)


func _center(action: String) -> Vector2:
	var d: Dictionary = _touch._buttons[action]
	return (d["rect"] as Rect2).get_center()


func _btn_visible(action: String) -> bool:
	var d: Dictionary = _touch._buttons[action]
	return bool(d["visible"])


func _run() -> void:
	_step("start")
	_main = MainScene.instantiate()
	add_child(_main)
	await get_tree().process_frame
	await get_tree().process_frame
	_hud = _main.find_child("HUD", true, false) as Control
	_menu = get_tree().get_first_node_in_group("main_menu")
	_touch = _hud.find_child("TouchHUD", true, false) if _hud != null else null
	_expect(_hud != null, "HUD ada")
	_expect(_menu != null, "MainMenu ada")
	_expect(_touch != null, "TouchHUD terpasang di HUD")
	if _hud == null or _menu == null or _touch == null:
		_finish()
		return
	# Deterministik: kunci viewport 16:9 (headless CI vs desktop).
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	MobileLayout.layout_changed.emit()
	await get_tree().process_frame

	_step("wiring+z-order")
	# Router produksi TERSAMBUNG (inilah yang selama ini hilang).
	var router := Callable(_main, "_apply_touch_action")
	_expect(_touch.is_connected("hud_action", router),
		"hud_action tersambung ke Main._apply_touch_action")
	# Paling atas: pygame menggambar hud.draw() TERAKHIR di STATE_GAME.
	var shop := _hud.find_child("ShopPanel", true, false)
	var popup := _hud.find_child("AchievementPopup", true, false)
	_expect(shop != null and popup != null, "ShopPanel + AchievementPopup ada")
	if shop != null and popup != null:
		_expect(_touch.get_index() > shop.get_index(),
			"TouchHUD di atas ShopPanel")
		_expect(_touch.get_index() > popup.get_index(),
			"TouchHUD di atas AchievementPopup")

	_step("geometri=kanon")
	# Node dibangun dari HudLayout.TOUCH_BUTTONS — buktikan per tombol +
	# area sentuh MIN_TAP 80 (paritas inflate hud.py).
	for action in HudLayout.TOUCH_BUTTONS:
		var spec: Dictionary = HudLayout.TOUCH_BUTTONS[action]
		_expect(_touch._buttons.has(action), "tombol %s ada" % action)
		if not _touch._buttons.has(action):
			continue
		var d: Dictionary = _touch._buttons[action]
		var r: Rect2 = d["rect"]
		var want: Array = spec["rect"]
		_expect(int(r.position.x) == int(want[0])
			and int(r.position.y) == int(want[1])
			and int(r.size.x) == int(want[2])
			and int(r.size.y) == int(want[3]),
			"rect %s = kanon (got %s want %s)" % [action, r, want])
		_expect(str(d["label"]) == str(spec["label"]),
			"label %s (got %s)" % [action, d["label"]])
		var hit: Rect2 = d["hit"]
		_expect(hit.size.x >= 80.0 and hit.size.y >= 80.0,
			"hit %s >= 80px (got %s)" % [action, hit.size])
		_expect(hit.encloses(r), "hit %s memuat rect" % action)

	_step("matriks visibilitas")
	# set_state_key = matriks MURNI (tanpa override panel — itu sync).
	_touch.show_debug_button = true
	for key in HudLayout.TOUCH_VISIBILITY:
		_touch.set_state_key(str(key))
		var want: Dictionary = HudLayout.touch_visibility(str(key))
		for action in HudLayout.TOUCH_BUTTONS:
			_expect(_btn_visible(str(action)) == bool(want.get(action, false)),
				"[%s] %s" % [key, action])

	_step("sembunyi di menu")
	# Boot = menu terbuka: pygame tak pernah menggambar hud di menu.
	_touch.sync_from_match()
	_expect(not _touch.visible, "TouchHUD sembunyi saat menu terbuka")

	_step("match+skip")
	var connector := get_tree().get_first_node_in_group("game_connector")
	_expect(connector != null, "connector ada")
	# Paritas _request_play (MainMenu): TUTUP menu dulu baru mulai match —
	# start_match langsung (ala BattleSmokeTest) membuat menu tetap terbuka
	# dan TouchHUD benar-benar sembunyi (bug harness, bukan produksi).
	_menu.close()
	_expect(not _menu.is_open(), "menu tertutup saat match dimulai")
	if connector != null and connector.has_method("start_match"):
		connector.start_match(1)
	else:
		GameManager.start_level(1, false)
	for _i in range(3):
		await get_tree().process_frame
	var intro = _main.get("_level_intro")
	_expect(is_instance_valid(intro) and intro.cinematic_active(),
		"intro aktif setelah start")
	_touch.sync_from_match()
	_expect(_touch.visible, "TouchHUD tampil di match")
	_expect(_btn_visible("skip"), "SKIP tampil saat intro")
	_expect(not _btn_visible("pause"), "pause sembunyi saat intro")
	# SKIP positif via router (paritas handle_skip SPACE).
	_main._apply_touch_action("skip")
	_expect(not get_tree().paused, "skip router membuka pause intro")
	_expect(not is_instance_valid(intro) or not intro.cinematic_active(),
		"skip router menyelesaikan intro")
	_touch.sync_from_match()
	_expect(_btn_visible("pause"), "pause tampil setelah intro")
	_expect(_btn_visible("debug"), "debug tampil (flag uji)")
	_expect(not _btn_visible("skip"), "SKIP hilang setelah intro")

	_step("watchdog cinematic")
	# Keluhan yang ditutup di sini: tombol SKIP menempel selama wave (PAUSE
	# hilang) karena sesuatu mengklaim "cinematic aktif" tanpa pernah lepas.
	# (1) Klaim dari node yang BERHENTI memproses frame = bukti hidupnya
	#     hilang -> Main menolaknya, HUD tidak boleh pindah ke matriks cine.
	var dead := FakeCine.new()
	dead.name = "DeadCine"
	_main.add_child(dead)
	dead.claim = true
	dead.set_process(false)
	_expect(not _main._cinematic_active(),
		"klaim cinematic node tak-diproses ditolak (bukti hidup)")
	_touch.sync_from_match()
	_expect(_btn_visible("pause") and not _btn_visible("skip"),
		"PAUSE tetap tampil saat klaim datang dari node mati")
	# (2) Node hidup + klaim aktif + tanpa pause = sah, tapi hanya sampai
	#     latch watchdog (CINE_WATCHDOG_SEC).
	dead.set_process(true)
	_expect(_main._cinematic_active(),
		"klaim node hidup yang memproses diterima")
	_touch.sync_from_match()
	_expect(_btn_visible("skip"), "SKIP tampil selama klaim cinematic sah")
	for _i in range(int(_touch.CINE_WATCHDOG_SEC) + 2):
		_touch.sync_from_match(1.0)
	_expect(bool(_touch._cine_stuck),
		"watchdog memutus + melatch klaim > %.0f dtk" % _touch.CINE_WATCHDOG_SEC)
	_expect(_btn_visible("pause") and not _btn_visible("skip"),
		"SKIP hilang + PAUSE kembali setelah watchdog memutus")
	# (3) Latch bertahan selama klaim masih ada: SKIP tidak boleh berkedip
	#     nyala lagi di wave yang sama (perilaku lama: putus-pasang berulang).
	for _i in range(3):
		_touch.sync_from_match(1.0)
	_expect(not _btn_visible("skip"), "SKIP tidak kembali selama klaim basi")
	# (4) Klaim benar-benar lepas -> latch reset setelah cooldown, jadi
	#     cinematic berikutnya (intro level, perayaan) tetap dapat SKIP.
	dead.claim = false
	_touch.sync_from_match(_touch.CINE_COOLDOWN_SEC + 0.1)
	_expect(not bool(_touch._cine_stuck),
		"latch lepas setelah %.0f dtk tanpa klaim" % _touch.CINE_COOLDOWN_SEC)
	dead.free()
	_touch.sync_from_match()
	_expect(_btn_visible("pause"), "PAUSE normal setelah watchdog selesai")

	_step("tap->signal")
	# Lepas router produksi selama uji tap (kalau tidak, tap pause
	# sungguhan mem-pause tree di tengah harness).
	if _touch.is_connected("hud_action", router):
		_touch.disconnect("hud_action", router)
	_touch.hud_action.connect(_record)
	_taps.clear()
	_touch._tap_at(_center("pause"))
	_touch._tap_at(_center("debug"))
	_touch._tap_at(_center("skip")) # tersembunyi -> diam
	_touch._tap_at(Vector2(5, 700)) # tanah kosong -> diam
	_expect(_taps == ["pause", "debug"],
		"tap pause+debug emit, tersembunyi/kosong diam (got %s)" % [_taps])
	_touch.disconnect("hud_action", _record)
	_touch.hud_action.connect(router)
	_expect(_touch.is_connected("hud_action", router), "router tersambung lagi")

	_step("overlay debug")
	_main._apply_touch_action("debug")
	var overlay := _hud.find_child("DebugOverlay", true, false) as Control
	_expect(overlay != null and overlay.visible, "debug ON menampilkan overlay")
	_main._apply_touch_action("debug")
	_expect(overlay != null and not overlay.visible, "debug OFF menyembunyikan")

	_step("guard router")
	# Di tengah playing, replay/next/menu diam total (tombolnya pun sembunyi).
	_main._apply_touch_action("replay")
	_main._apply_touch_action("next_level")
	_main._apply_touch_action("menu")
	_expect(GameManager.state == "playing" and not GameManager.in_menu
		and GameManager.level_number == 1, "guard playing diam")

	_step("pause+back")
	_main._apply_touch_action("pause")
	_expect(get_tree().paused, "pause router membekukan tree")
	_expect(_menu.is_open() and int(_menu.get("state")) == MENU_STATE_PAUSE,
		"pause router membuka menu PAUSE")
	_touch.sync_from_match()
	_expect(not _touch.visible, "TouchHUD sembunyi saat pause")
	# back dari PAUSE = resume (paritas menu.handle_key ESCAPE).
	_main._apply_touch_action("back")
	_expect(not get_tree().paused, "back dari PAUSE resume")
	_expect(not _menu.is_open(), "back dari PAUSE menutup menu")
	_touch.sync_from_match()
	_expect(_touch.visible, "TouchHUD tampil lagi setelah resume")

	_step("override panel")
	MobileLayout.viewport_size = Vector2(1624.0, 720.0)
	MobileLayout.layout_changed.emit()
	await get_tree().process_frame
	_expect(MobileLayout.has_side_panel(), "1624 punya rail")
	_touch.sync_from_match()
	_expect(_touch.visible, "node tetap tampil saat rail ada")
	_expect(not _btn_visible("pause"), "pause pindah ke rail (sembunyi)")
	_expect(not _btn_visible("debug"), "FPS hilang total saat rail ada")
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	MobileLayout.layout_changed.emit()
	await get_tree().process_frame
	_touch.sync_from_match()
	_expect(_btn_visible("pause"), "pause kembali di 16:9")

	_step("visibilitas usai match")
	GameManager.state = "victory"
	_touch.sync_from_match()
	_expect(_btn_visible("replay"), "REPLAY tampil saat victory")
	_expect(_btn_visible("next_level"), "NEXT tampil di level 1")
	_expect(_btn_visible("menu"), "MENU tampil saat victory")
	_expect(not _btn_visible("pause"), "pause hilang saat victory")
	GameManager.level_number = 54
	_touch.sync_from_match()
	_expect(not _btn_visible("next_level"), "NEXT hilang di level 54")
	GameManager.level_number = 1
	GameManager.state = "defeat"
	_touch.sync_from_match()
	_expect(_btn_visible("replay") and _btn_visible("menu"),
		"REPLAY+MENU tampil saat defeat")
	_expect(not _btn_visible("next_level"), "NEXT hilang saat defeat")
	GameManager.state = "playing"

	_step("replay positif")
	GameManager.state = "victory"
	_main._apply_touch_action("replay")
	for _i in range(3):
		await get_tree().process_frame
	_expect(GameManager.level_number == 1, "replay tetap level 1")
	_expect(GameManager.state == "playing", "replay masuk playing")
	var intro2 = _main.get("_level_intro")
	_expect(is_instance_valid(intro2) and intro2.cinematic_active(),
		"replay memutar intro lagi")
	_main._apply_touch_action("skip")
	_expect(not get_tree().paused, "skip setelah replay")

	_step("next positif")
	GameManager.state = "victory"
	_main._apply_touch_action("next_level")
	for _i in range(3):
		await get_tree().process_frame
	_expect(GameManager.level_number == 2, "next ke level 2")
	var intro3 = _main.get("_level_intro")
	_expect(is_instance_valid(intro3) and intro3.cinematic_active(),
		"next memutar intro level 2")
	_main._apply_touch_action("skip")
	_expect(not get_tree().paused, "skip setelah next")

	_step("menu positif")
	_main._apply_touch_action("menu")
	_expect(not GameManager.in_menu, "menu diabaikan saat playing")
	GameManager.state = "victory"
	_main._apply_touch_action("menu")
	_expect(GameManager.in_menu, "menu kembali in_menu")
	_expect(_menu.is_open() and int(_menu.get("state")) == MENU_STATE_MAIN,
		"menu kembali ke MAIN")
	_touch.sync_from_match()
	_expect(not _touch.visible, "TouchHUD sembunyi setelah ke menu")

	_finish()


func _finish() -> void:
	get_tree().paused = false
	GameManager.set_paused(false)
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	MobileLayout.layout_changed.emit()
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.level_number = 1
	if is_instance_valid(_main):
		_main.free()
	if _failures == 0:
		print("[TouchHudParityTest] PASS")
	else:
		push_error("TouchHudParityTest failures: %d" % _failures)
	get_tree().quit(0 if _failures == 0 else 1)
