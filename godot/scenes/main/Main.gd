# Main.gd — akar dari scenes/main.tscn
#
# Kenapa file ini ada: main.tscn sebelumnya tidak punya script root sama sekali.
# GameManagerConnector hanya menyambungkan container + memanggil start_level(),
# dan GameManager.start_level() hanya print + emit signal. Tidak ada satu node pun
# yang punya visual -> viewport menampilkan clear color (0.04, 0.04, 0.07) yang
# kelihatan sebagai "layar hitam" saat F5.
#
# Tugas Main.gd sekarang (port sisi "Game" dari _core.py yang butuh pengetahuan
# layout map — GameManager tetap memegang state, Main yang memegang medan):
#   1. membingkai kamera ke arena 1280x720,
#   2. menukar tema map dari levels.json["map_theme"],
#   3. spawn 2 NEXUS (Radiant/Dire) -> match bisa MENANG/KALAH, dengan level
#      castle awal dari levels.json (starting_castle_level / castle_start_level
#      — paritas _core.py:1504-1508),
#   4. bangun 18 SLOT menara dari lane path (paritas
#      Game._generate_build_slots_from_lanes) + menggambarnya,
#   5. mulai dengan roster kosong; pemain/AI membeli hero dengan gold,
#   6. jadwal mini boss diacak sesuai difficulty; true boss
#      setelah 6 menara Dire hancur (paritas _core.py 2089), keduanya kena
#      enemy scaling hard mode saat spawn (paritas _core.py 1822/2097),
#   7. AI tim red membangun/meng-upgrade menara memakai GameManager.ai_gold,
#   8. input: klik = pilih unit/slot, QWER = skill, H = toko,
#      G/F/T/C/B/D = perintah taktis hold (FASE 18, paritas InputHandler
#      pygame) + panel TACTICAL COMMANDS di HUD,
#      ENTER setelah menang = LANJUT LEVEL BERIKUTNYA (kalah = ulang),
#      R = replay, ESC setelah menang/kalah = menu utama, P/ESC = menu PAUSE,
#      kontrol demo hanya aktif bila enable_debug_controls diaktifkan.
extends Node2D

## Urutan lane saat membuat slot bangun (paritas pygame: top, mid, bot)
const LANE_ORDER: Array = ["top", "mid", "bot"]
## Fraksi posisi sepanjang lane path — angka persis dari _core.py 1660-1676
const LANE_SLOT_PCT := {
	"top": {"blue": [0.15, 0.30, 0.45], "red": [0.85, 0.70, 0.55]},
	"mid": {"blue": [0.10, 0.25, 0.40], "red": [0.90, 0.75, 0.60]},
	"bot": {"blue": [0.15, 0.30, 0.45], "red": [0.85, 0.70, 0.55]},
}
## Menara Dire yang harus hancur sebelum true boss turun (paritas _core.py 2089)
const TRUE_BOSS_TOWER_KILLS := 6

## true = kamera mengikuti pusat pertempuran, false = kamera diam membingkai arena
@export var camera_follows_action: bool = false
## Debug tidak boleh mengubah match normal tanpa sengaja.
@export var enable_debug_controls: bool = false

var _arena_map = null
var _camera: Camera2D = null
## Node2D khusus menggambar slot bangun (anak Main digambar SETELAH Main, jadi
## _draw() milik Main sendiri akan tertutup ArenaMap)
var _slot_layer: Node2D = null
## AIPlayer telur (port _entity.AIPlayer — dibuat di _ready, dikelola sendiri)
var _ai = null
## Perintah taktis tim biru (port tactical_commands — dibuat di _ready,
## dikelola sendiri via _physics_process 60 Hz)
var _tactical = null
# FASE 24 — lapisan gamepad (dibuat di _ready, dipakai _process/UI).
var _controller = null
var _router = null
## Pemicu UI FASE 18 — port InputHandler pygame (_core.py):
## KEYDOWN G/F/T/C/B/D -> hold_start, KEYUP -> hold_end.
## G dan F dua tuts untuk perintah yang sama (gather).
const TACTICAL_KEY_TO_COMMAND := {
	KEY_G: "gather",
	KEY_F: "gather",
	KEY_T: "protect_tower",
	KEY_C: "protect_castle",
	KEY_B: "attack_boss",
	KEY_D: "attack_damage_dealer",
}
var _slot_redraw_timer: float = 0.0
var _slot_pulse: float = 0.0
## Penghitung frame untuk jadwal bangun ulang SpatialGrid (paritas
## `animation_time % 2 == 0` di `_core.py:2009`).
var _grid_tick: int = 0
## FX world-space FASE 26 (port `_render.EffectManager`): percikan/ledakan +
## panah jalur lane saat wave dimulai. Dibuat di `_ready`, data percikannya
## milik `GameManager.spark_fx` (satu EffectManager global seperti pygame).
var _spark_layer = null
var _path_preview = null
## Overlay FPS (port `_system.FPSCounter`, panel jalur desktop LEGACY) —
## CanvasLayer sendiri supaya tampil di ATAS menu/pause, sama seperti pygame
## yang mem-blit-nya setelah semua state di `main_desktop_legacy.py:455`.
## Bukan lagi target F8 (lihat catatan di `_build_touch_layer`).
var _fps_counter = null
## CanvasLayer tempat panel FpsCounter + overlay debug tinggal (dibuat
## runtime, BUKAN node .tscn — karena itu dipegang lewat variabel ini, bukan
## lewat path get_node: `godot/tools/check_refs.py` menuntut path literal ada
## di scene).
var _debug_layer: CanvasLayer = null
## ── LAPISAN SENTUH (port `mobile/touch.py` + `mobile/debug.py`, 2026-09-23) ──
## Mesin gesture: tap (lepas), TAHAN 450 ms (klik kanan / overlay debug),
## drag, notch scroll, fling. Main memasok event dari `_input` dan
## memanen antreannya tiap frame di `_process` — persis siklus
## `touch.process_event()` (main.py:364) + `touch.collect()` (main.py:401).
var _gestures = null
## Overlay debug 4 mode (OFF/RINGKAS/LENGKAP/GRAFIK) — target tombol FPS,
## F8, dan tahan-tombol-jeda. Hidupnya di CanvasLayer DebugLayer yang sama
## dengan FpsCounter karena pygame menggambar overlay DI LUAR dispatch state.
var _debug_overlay = null
## touch id -> true bila press-nya TIDAK lolos ke arena (ditangkap Control).
## Padanan `claimed` main.py:421: sentuhan yang diklaim UI tidak diteruskan
## ke `handle_click`. Klaim dipasang di `_input`, DILEPAS di
## `_unhandled_input` (event yang selamat dari GUI), dan dibersihkan lagi
## saat aksi "release" didistribusikan.
var _press_claim: Dictionary = {}

## Jadwal boss level ini (port Game.pending_mini_bosses / true_boss_spawned)
var pending_mini_bosses: Array = []
var mini_boss_schedule: Dictionary = {}
var active_boss = null
var red_towers_destroyed: int = 0
var true_boss_spawned: bool = false

## Cinematic aktif (Fase 5d — port efek _render.py): intro level membekukan
## gameplay, banner boss & perayaan kematian tidak. Urutan cek skip = urutan
## pygame Game.handle_key (_core.py:2674-2686): level_intro -> boss_intro
## -> boss_death celebration. Referensi eksplisit supaya prioritas deterministik.
var _level_intro = null
var _boss_banner = null

func _enter_tree():
	# _enter_tree (bukan _ready): parent didahulukan, jadi kita tetap kebagian
	# signal level_started walau Connector memanggil start_level() di _ready()-nya.
	_connect_once(GameManager.level_started, _on_level_started)
	_connect_once(GameManager.wave_started, _on_wave_started)
	_connect_once(GameManager.boss_defeated, _on_boss_defeated)
	_connect_once(GameManager.game_over, _on_game_over)
	_connect_once(GameManager.tower_destroyed, _on_tower_destroyed)
	_connect_once(GameManager.selection_changed, _on_selection_changed)
	add_to_group("main")

func _exit_tree():
	# GameManager itu autoload -> umurnya lebih panjang dari scene. Putuskan supaya
	# reload scene tidak meninggalkan connection ganda / dangling reference.
	for pair in [[GameManager.level_started, _on_level_started],
			[GameManager.wave_started, _on_wave_started],
			[GameManager.boss_defeated, _on_boss_defeated],
			[GameManager.game_over, _on_game_over],
			[GameManager.tower_destroyed, _on_tower_destroyed],
			[GameManager.selection_changed, _on_selection_changed]]:
		var sig: Signal = pair[0]
		if sig.is_connected(pair[1]):
			sig.disconnect(pair[1])

static func _connect_once(sig: Signal, p_callable: Callable) -> void:
	if not sig.is_connected(p_callable):
		sig.connect(p_callable)

func _ready():
	_arena_map = get_node_or_null(^"ArenaMap")
	_camera = get_node_or_null(^"Camera2D")
	# Grup "camera" dibaca Boss._shake (screen shake) lewat call_group —
	# tanpa mendaftarkan di sini, semua screen shake pygame menjadi no-op.
	if _camera != null:
		_camera.add_to_group("camera")
	_frame_camera()
	_build_slot_layer()
	var popups = preload("res://scenes/fx/WorldPopups.gd").new()
	popups.name = "WorldPopups"
	add_child(popups)
	_build_fx_layers()
	_build_fps_counter()
	_build_touch_layer()
	# Sambungkan sinyal menu utama (node UI/MainMenu siap lebih dulu karena
	# anak diproses sebelum parent; koneksi di sini juga aman diulang).
	var menu = _main_menu()
	if menu != null:
		_connect_once(menu.play_requested, _on_menu_play)
		_connect_once(menu.resume_requested, _on_menu_resume)
		_connect_once(menu.main_menu_requested, _on_menu_main_menu)
		_connect_once(menu.menu_coverage_changed, _apply_menu_coverage)
		# Emit pertama terjadi di MainMenu._ready (sebelum koneksi di atas),
		# jadi sinkronkan state saat ini SEKARANG — kalau dilewatkan, boot
		# menampilkan arena+HUD di belakang/sebelah layar menu (berantakan).
		_apply_menu_coverage(menu.is_open(), menu.state == menu.State.PAUSE)
	# FASE 23 — tombol sentuh (port mobile/hud.apply_hud_action): HUD._ready
	# (anak) jalan SEBELUM Main._ready (induk), jadi TouchHUD sudah ada di
	# grup saat koneksi ini dipasang.
	var touch = get_tree().get_first_node_in_group("touch_hud")
	if touch != null and touch.has_signal("hud_action") \
			and not touch.is_connected("hud_action", _apply_touch_action):
		touch.connect("hud_action", _apply_touch_action)
	# Tetap dapat kunci walau SceneTree di-pause (P/ESC). Karena anak men-inherit,
	# node yang mensimulasikan unit harus dipaksa PAUSABLE supaya get_tree().paused
	# sungguh-sungguh membekukan hero/minion.
	process_mode = Node.PROCESS_MODE_ALWAYS
	for path in ["Containers", "ArenaMap"]:
		var node := get_node_or_null(path)
		if node != null:
			node.process_mode = Node.PROCESS_MODE_PAUSABLE
	if _slot_layer != null:
		_slot_layer.process_mode = Node.PROCESS_MODE_PAUSABLE
	# AIPlayer Dire (port penuh _entity.AIPlayer): auto-reset lewat signal
	# level_started, self-managed via _process — Main tidak lagi punya _ai_tick.
	_ai = preload("res://scripts/systems/AIPlayer.gd").new()
	_ai.name = "AIPlayer"
	add_child(_ai)
	_ai.process_mode = Node.PROCESS_MODE_PAUSABLE
	# Perintah taktis (FASE 17): self-managed via _physics_process, baca
	# Main.active_boss dari induknya — pola yang sama dengan _ai.
	_tactical = preload("res://scripts/systems/TacticalCommands.gd").new()
	_tactical.name = "TacticalCommands"
	add_child(_tactical)
	_tactical.process_mode = Node.PROCESS_MODE_PAUSABLE
	# FASE 24 — LAPISAN GAMEPAD (port controller_manager.py + routing
	# main_desktop_legacy.py). Keduanya ALWAYS: pygame merutekan pad di SEMUA
	# state (splash/menu/game/pause), jadi kalau ikut PAUSABLE tombol pad
	# tidak bisa membuka atau menutup pause. Aksi gameplay tetap beku karena
	# router memeriksa state sendiri (branch STATE_GAME).
	_controller = preload("res://scripts/systems/ControllerManager.gd").new()
	_controller.name = "ControllerManager"
	add_child(_controller)
	_controller.process_mode = Node.PROCESS_MODE_ALWAYS
	_router = preload("res://scripts/systems/ControllerRouter.gd").new()
	_router.name = "ControllerRouter"
	_router.controller = _controller
	add_child(_router)
	_router.process_mode = Node.PROCESS_MODE_ALWAYS
	# Kursor virtual digambar paling atas CanvasLayer UI (paritas blit
	# terakhir _render.py:1615) dan ikut membaca mode controller.
	var ui_layer = get_node_or_null(^"UI")
	if ui_layer != null:
		var pad_cursor = preload("res://scenes/ui/VirtualCursor.gd").new()
		pad_cursor.name = "VirtualCursor"
		pad_cursor.manager = _controller
		ui_layer.add_child(pad_cursor)
	if menu != null:
		menu.controller_mgr = _controller
	# Splash boot (STATE_SPLASH main.py) — paling akhir supaya ia benar-benar
	# menutupi menu utama yang sudah siap di belakangnya.
	_maybe_show_splash()


## Paritas STATE_SPLASH (main.py:130-131, 405-412): splash tampil PALING
## AWAL saat aplikasi mulai; selama ia aktif, klik/tombol apa pun hanya
## melewatinya dan tidak sampai ke menu — klik ditahan view splash
## (`MOUSE_FILTER_STOP` + `_gui_input`), tombol ditandai handled oleh
## `SplashScreen._unhandled_input`, persis cabang STATE_SPLASH pygame yang
## tidak pernah memanggil dispatch_to_menu.
##
## DILEWATI di headless (`godot --headless`, termasuk CI): splash adalah
## layar presentasi 3 detik tanpa efek gameplay, sementara harness tes
## mengirim input sintetis beberapa frame setelah boot — kalau ikut tampil,
## semua input itu tertelan. `MYSTIC_NO_SPLASH=1` meniadakannya tanpa
## menyentuh kode (berguna saat debugging boot).
func _maybe_show_splash() -> void:
	if AppShell.headless():
		return
	if OS.has_environment("MYSTIC_NO_SPLASH") \
			and OS.get_environment("MYSTIC_NO_SPLASH") == "1":
		return
	var splash = preload("res://scenes/ui/SplashScreen.gd").new()
	splash.name = "SplashScreen"
	add_child(splash)
	if not splash.is_connected("finished", _on_splash_finished):
		splash.connect("finished", _on_splash_finished)
	print("[Main] SPLASH — klik / tombol apa pun untuk melewati")


func _on_splash_finished() -> void:
	print("[Main] SPLASH selesai — menu utama")

## Overlay FPS (port `_system.FPSCounter`). Dipasang di CanvasLayer SENDIRI,
## bukan di dalam HUD: pygame mem-blit panel ini setelah semua state digambar
## (`main_desktop_legacy.py:455-456`), jadi ia tetap tampil di atas menu,
## splash, dan pause — tempat HUD justru disembunyikan.
func _build_fps_counter() -> void:
	if _fps_counter != null and is_instance_valid(_fps_counter):
		return
	var layer := CanvasLayer.new()
	layer.name = "DebugLayer"
	# di atas CanvasLayer UI (HUD/toko) supaya tidak tertutup panel
	layer.layer = 200
	layer.process_mode = Node.PROCESS_MODE_ALWAYS
	var counter := preload("res://scenes/ui/FpsCounter.gd").new()
	counter.name = "FpsCounter"
	layer.add_child(counter)
	add_child(layer)
	_debug_layer = layer
	_fps_counter = counter


## Panel `_system.py` (jalur desktop LEGACY pygame). Bukan target F8 maupun
## tombol FPS lagi — keduanya kini mengiklusi `DebugOverlay` 4 mode, persis
## `main.py:370` + `main.py:407-413`. FpsCounter tetap bisa dibuka dari kode
## (tests/SystemPerfParityTest); return node-nya supaya tes headless bisa
## membaca `display_fps`/`fps_history` tanpa cari nama node.
func toggle_fps_counter():
	if _fps_counter == null or not is_instance_valid(_fps_counter):
		_build_fps_counter()
	_fps_counter.toggle()
	return _fps_counter


# ══════════════════════════════════════════════════════════
#  LAPISAN SENTUH + OVERLAY DEBUG 4 MODE
#  (port mobile/touch.py TouchManager + mobile/debug.py DebugOverlay,
#   dirangkai seperti main.py: touch.update() -> collect() -> dispatch)
# ══════════════════════════════════════════════════════════

## Mesin gesture + overlay debug. Dipasang di CanvasLayer DebugLayer yang
## SAMA dengan FpsCounter (layer 200, PROCESS_MODE_ALWAYS): overlay debug
## pygame digambar SESUDAH semua state (`main.py:615-617`), jadi ia harus
## tetap tampil di atas splash/menu/pause tempat HUD disembunyikan.
func _build_touch_layer() -> void:
	if _gestures == null or not is_instance_valid(_gestures):
		var g := preload("res://scripts/systems/TouchGestures.gd").new()
		g.name = "TouchGestures"
		add_child(g)
		_gestures = g
	_build_debug_overlay()
	if _debug_overlay != null and is_instance_valid(_debug_overlay):
		_debug_overlay.bind_gestures(_gestures)


func _build_debug_overlay() -> void:
	if _debug_overlay != null and is_instance_valid(_debug_overlay):
		return
	if _debug_layer == null or not is_instance_valid(_debug_layer):
		_build_fps_counter()
	var layer := _debug_layer
	if layer == null or not is_instance_valid(layer):
		push_warning("[Main] DebugLayer tidak ada - overlay debug dilewati")
		return
	var ov := preload("res://scenes/ui/DebugOverlay.gd").new()
	ov.name = "DebugOverlay"
	layer.add_child(ov)
	_debug_overlay = ov


## Dibaca HUD (rute tombol FPS + pad) lewat `has_method("debug_overlay")`.
func debug_overlay():
	_build_debug_overlay()
	return _debug_overlay


## Padanan `DebugOverlay.toggle()` — mengembalikan mode baru (0..3) supaya
## pemanggil/tes tidak perlu mengintip properti node.
func toggle_debug_overlay() -> int:
	_build_debug_overlay()
	return int(_debug_overlay.toggle())


func debug_mode() -> int:
	if _debug_overlay == null or not is_instance_valid(_debug_overlay):
		return DebugOverlay.MODE_OFF
	return int(_debug_overlay.mode)


## SETIAP event dilihat mesin gesture, SEBELUM GUI dan sebelum
## `_unhandled_input` — paritas main.py:364 (`touch.process_event(event)`
## dijalankan lebih dulu, dan event yang dikonsumsi tidak dilihat siapa pun).
## Godot tidak boleh menelan event di sini: Control (tombol, ScrollContainer,
## dialog) harus tetap kebagian, jadi mesin hanya MENGAMATI.
func _input(event: InputEvent) -> void:
	if _gestures == null or not is_instance_valid(_gestures):
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			# Diduga diklaim UI dulu; `_unhandled_input` melepas dugaan ini
			# kalau press-nya benar-benar lolos ke arena.
			_press_claim[TouchGestures.touch_id_of(event)] = true
	_gestures.feed_event(event)


## Panen aksi (paritas `touch.update()` main.py:342 + `for action in
## touch.collect()` main.py:401). Di Called sebelum cek `paused`: mesin harus
## tetap hidup saat tree dibekukan, persis pygame yang mendispatch sentuhan
## juga di STATE_PAUSE (ke menu).
func _drain_gestures() -> void:
	if _gestures == null or not is_instance_valid(_gestures):
		return
	var t0 := Time.get_ticks_usec()
	_gestures.update()
	for action in _gestures.collect():
		_dispatch_gesture(action as Dictionary)
	if _debug_overlay != null and is_instance_valid(_debug_overlay):
		# Fase "event" padanan `frame_timer.start("event")` main.py:337 —
		# di Godot yang terukur adalah biaya lapisan gesture + overlay.
		_debug_overlay.note_event(
			float(Time.get_ticks_usec() - t0) / 1000.0)


func _dispatch_gesture(action: Dictionary) -> bool:
	# true = aksi sudah dikonsumsi (padanan `return True` pada
	# `dispatch_to_game` touch.py:306-321 dan `continue` di main.py:404-413;
	# `return False` = aksi tidak punya efek, persis `dispatch_to_game` untuk
	# kind yang tidak dipetakan / game=None).
	var kind := str(action["kind"])
	var tid := int(action["touch_id"])
	var pos: Vector2 = action["pos"]
	if kind == TouchGestures.KIND_RELEASE:
		_press_claim.erase(tid)
		return false
	if kind == TouchGestures.KIND_DOWN:
		return false
	if kind == TouchGestures.KIND_DRAG \
			or kind == TouchGestures.KIND_SCROLL \
			or kind == TouchGestures.KIND_FLING \
			or kind == TouchGestures.KIND_DOUBLE_TAP:
		# DEVIASI tercatat, bukan kelupaan: menggulir daftar panjang (hero
		# shop, keypad voucher) di Godot dilakukan ScrollContainer secara
		# NATIF (mouse wheel + seretan sentuh + inersia engine), jadi notch
		# scroll dan fling pygame sengaja tidak diteruskan ke arena.
		# `double_tap` memang tidak punya aksi di pygame:
		# `dispatch_to_game` hanya memetakan tap / long_press / scroll.
		return false
	var claimed := bool(_press_claim.get(tid, false))
	if kind == TouchGestures.KIND_TAP:
		if claimed:
			return false
		# Klik saat cinematic = skip + ditelan (paritas `Game.handle_click`
		# _core.py:2563-2575: intro diperiksa SEBELUM InputHandler).
		if _cinematic_click():
			return true
		_on_click(pos)
		return true
	if kind == TouchGestures.KIND_LONG_PRESS:
		# main.py:404-413 — dicek SEBELUM filter claimed, karena sentuhan ke
		# tombol jeda sudah diklaim HUD sejak "down".
		if _pause_button_holds(pos):
			toggle_debug_overlay()
			MobileLayout.vibrate(30)
			return true
		if claimed:
			return false
		# Klik kanan fisik pun lewat jalur ini: pygame memetakan
		# MOUSEBUTTONDOWN(3) ke long_press, jadi TIDAK ada cabang kanan lagi
		# di `_unhandled_input` (kalau ada, satu klik jadi dua aksi).
		_on_right_click(pos)
		return true
	return false


## Padanan cabang `long_press` main.py:407-411: tombol jeda TouchHUD ATAU
## tombol jeda rail kanan (saat panel tersedia), hanya di dalam match.
func _pause_button_holds(pos: Vector2) -> bool:
	if GameManager.in_menu or get_tree().paused:
		return false
	var touch = get_tree().get_first_node_in_group("touch_hud")
	if touch != null and is_instance_valid(touch) \
			and touch.has_method("contains_button") \
			and bool(touch.call("contains_button", "pause", pos)):
		return true
	var side = find_child("SidePanel", true, false)
	if side != null and is_instance_valid(side) \
			and side.has_method("rail_active") \
			and bool(side.call("rail_active")) \
			and side.has_method("rail_pause_contains") \
			and bool(side.call("rail_pause_contains", pos)):
		return true
	return false


func _build_slot_layer() -> void:
	_slot_layer = Node2D.new()
	_slot_layer.name = "SlotLayer"
	# di atas map (ArenaMap z 0), di bawah unit
	_slot_layer.z_index = 1
	# CanvasItem punya signal `draw` -> gambar slot tanpa perlu subclass baru
	_slot_layer.draw.connect(_draw_slots)
	add_child(_slot_layer)

# ══════════════════════════════════════════════════════════
#  LEVEL / BATTLE
# ══════════════════════════════════════════════════════════

func _on_level_started(level_num: int) -> void:
	var lv: Dictionary = BossDB.get_level(level_num)
	if not lv.is_empty() and _arena_map != null and _arena_map.has_method("apply_theme"):
		_arena_map.apply_theme(str(lv.get("map_theme", "forest")))
	# call_deferred: pastikan seluruh _ready (termasuk container si Connector) selesai
	_start_battle.call_deferred()

func _start_battle() -> void:
	# Jaga-jaga: battle baru tidak boleh mulai dalam keadaan beku (mis. level
	# diganti saat cinematic kematian masih memegang pause).
	get_tree().paused = false
	GameManager.set_paused(false)
	_clear_field()
	_reset_boss_schedule()
	_spawn_nexuses()
	_generate_build_slots()
	# Game.reset pygame membuat self.heroes dan self.ai.heroes KOSONG.
	# Unlock meta berarti boleh DIBELI, bukan otomatis hadir di arena.
	GameManager.clear_selection()
	GameManager.close_shop()
	_on_selection_changed()
	print("[Main] battle siap: roster kosong, 2 nexus, %d slot menara" % GameManager.build_slots.size())
	_show_level_intro()

## Layar intro split-screen sebelum battle (paritas LevelIntroScreen dibuat di
## Game.reset _core.py:1608): gameplay beku sampai SPACE/ENTER/klik.
func _show_level_intro() -> void:
	if GameManager.in_menu:
		return
	var lv: Dictionary = BossDB.get_level(GameManager.level_number)
	if lv.is_empty():
		return
	var intro = preload("res://scenes/ui/LevelIntro.gd").new()
	intro.setup(lv, GameManager.level_number)
	add_child(intro)
	intro.take_pause_ownership()
	_level_intro = intro
	get_tree().paused = true
	GameManager.set_paused(true)
	# HUD disinkronkan SEKETIKA (PAUSE tersembunyi selama intro), bukan satu
	# frame sesudahnya. Tombol SKIP sudah dimatikan permanen di gerbang
	# visibilitas TouchHUD; cinematic tetap dilewati SPACE/ENTER/klik.
	_touch_hud_resync()
	print("[Main] LEVEL INTRO — SPACE/ENTER/klik untuk mulai")

## `free()` langsung (bukan `queue_free()`): arena harus sudah bersih SEBELUM
## unit baru di-spawn pada frame yang sama; seleksi/roster tidak boleh
## menemukan unit match lama yang masih menunggu dihapus di akhir frame.
## Aman karena _start_battle selalu jalan dari deferred call / input / timer,
## tidak pernah dari dalam _physics_process unit.
func _clear_field() -> void:
	for group in ["heroes", "bosses", "minions", "towers", "nexus", "bullets",
			"skill_projectiles"]:
		for n in get_tree().get_nodes_in_group(group):
			if is_instance_valid(n):
				n.free()
	_free_cinematics()
	GameManager.blue_nexus = null
	GameManager.red_nexus = null
	GameManager.clear_selection()
	if is_instance_valid(_tactical):
		_tactical.reset()

## Buang semua cinematic aktif (intro level / banner boss / FX kematian).
## finish() melepas pause kalau cinematic itu yang memegangnya, jadi arena
## baru tidak pernah mulai dalam keadaan beku.
func _free_cinematics() -> void:
	for n in get_tree().get_nodes_in_group("cinematic"):
		if is_instance_valid(n) and n.has_method("finish"):
			n.finish()
		elif is_instance_valid(n):
			n.free()
	_level_intro = null
	_boss_banner = null
	# HUD ikut disinkronkan SEKETIKA: tanpa ini PAUSE tetap tersembunyi sampai
	# tick _process TouchHUD berikutnya walau cinematic-nya sudah dibuang di
	# frame ini.
	_touch_hud_resync()

func _reset_boss_schedule() -> void:
	pending_mini_bosses.clear()
	mini_boss_schedule = _roll_mini_boss_schedule()
	active_boss = null
	red_towers_destroyed = 0
	true_boss_spawned = false
	# Timer AI TIDAK di-reset di sini: AIPlayer self-managed dan mereset diri
	# lewat signal level_started (AIPlayer._on_level_started -> reset()).
	# Memaksa reset dari sini juga akan menghapus draft _hero_purchase_target
	# yang justru harus bertahan sampai gold cukup.

## Nexus = kondisi menang/kalah (paritas Castle di _entity.py).
## Level castle awal dibaca levels.json (paritas _core.py:1504-1508):
##   blue : starting_castle_level (bonus pemain)
##   red  : castle_start_level HANYA kalau enemy scaling aktif (hard),
##          selain itu 1 — di easy/normal menara nexus merah polos.
func _spawn_nexuses() -> void:
	var lv: Dictionary = BossDB.get_level(GameManager.level_number)
	var blue_start := clampi(int(lv.get("starting_castle_level", 1)), 1, TowerDB.nexus_max_level())
	var red_start := 1
	if GameManager.enemy_scaling_enabled:
		red_start = clampi(int(lv.get("castle_start_level", 1)), 1, TowerDB.nexus_max_level())
	for team in ["blue", "red"]:
		var nexus = GameManager.spawn_nexus(team, _base_center(team))
		# Naikkan level SEBELUM register (stat level + shield shield wave 0
		# dihitung di _ready/_apply_level_stats, jadi upgrade dulu = stat final).
		var target := blue_start if team == "blue" else red_start
		while int(nexus.get("level")) < target and nexus.has_method("upgrade"):
			nexus.upgrade()
		GameManager.register_nexus(nexus)
	if blue_start > 1 or red_start > 1:
		print("[Main] castle awal: Radiant Lv%d · Dire Lv%d" % [blue_start, red_start])

## Slot bangun menara: 3 lane x 3 slot x 2 tim = 18 slot
func _generate_build_slots() -> void:
	GameManager.clear_build_slots()
	if _arena_map == null or not _arena_map.has_method("get_lane_path"):
		return
	for lane in LANE_ORDER:
		var path: PackedVector2Array = _arena_map.get_lane_path(str(lane))
		if path.size() == 0:
			continue
		var pct_table: Dictionary = LANE_SLOT_PCT.get(str(lane), {})
		for team in ["blue", "red"]:
			for pct in pct_table.get(team, []):
				var idx := clampi(int(path.size() * float(pct)), 0, path.size() - 1)
				GameManager.add_build_slot(path[idx], str(team), str(lane))

## Dua lapisan FX world-space (port `_render.py:622-623` + `:788-789`).
## SparkLayer membaca `GameManager.spark_fx`; PathPreview memegang state-nya
## sendiri karena jalur lane dibaca dari ArenaMap milik scene ini.
func _build_fx_layers() -> void:
	_spark_layer = preload("res://scenes/fx/SparkLayer.gd").new()
	_spark_layer.name = "SparkLayer"
	add_child(_spark_layer)
	_path_preview = preload("res://scenes/fx/PathPreview.gd").new()
	_path_preview.name = "PathPreview"
	add_child(_path_preview)


## Urutan lane persis `_core.py:1756-1762`: top, mid, bot.
const PREVIEW_LANES: Array = ["top", "mid", "bot"]


func _show_path_preview() -> void:
	if _path_preview == null or _arena_map == null \
			or not _arena_map.has_method("get_lane_path"):
		return
	var lanes: Array = []
	for lane in PREVIEW_LANES:
		lanes.append(_arena_map.get_lane_path(str(lane)))
	_path_preview.show_paths(lanes)


func _on_wave_started(wave_num: int) -> void:
	# GameManager menguras antrean minion setiap 20 frame, bukan sekaligus.
	_queue_mini_boss(wave_num)
	# Panah merah di sepanjang lane selama 2 detik (paritas
	# `effects.show_path_preview(lane_paths)` `_core.py:1762`, dipanggil tepat
	# setelah announce_wave di blok wave-start pygame).
	_show_path_preview()


## Game._roll_mini_boss_schedule: tipe/urutan boss tetap, wave unik diacak.
func _roll_mini_boss_schedule() -> Dictionary:
	var cfg: Dictionary = BossDB.get_level(GameManager.level_number)
	var source: Dictionary = cfg.get("mini_bosses", {})
	var bosses := source.values()
	var low := 20 if GameManager.difficulty == "easy" else 11
	var high := 40 if GameManager.difficulty == "easy" else 30
	if high - low + 1 < bosses.size():
		high = low + bosses.size() * 5
	var waves := range(low, high + 1)
	waves.shuffle()
	waves.resize(bosses.size())
	waves.sort()
	var schedule: Dictionary = {}
	for i in range(bosses.size()):
		schedule[str(waves[i])] = bosses[i]
	return schedule


## Mini boss level ini masuk antrean begitu wave-nya lewat (paritas _core 1745)
func _queue_mini_boss(wave_num: int) -> void:
	var mini := mini_boss_schedule
	var key := str(wave_num)
	if not mini.has(key):
		return
	var boss_type := str(mini[key])
	if boss_type.is_empty() or pending_mini_bosses.has(boss_type):
		return
	pending_mini_bosses.append(boss_type)
	print("[Main] mini boss %s masuk antrean (wave %d)" % [boss_type, wave_num])

## Konsumsi event boss mati tepat sekali, sebelum cinematic menahan
## gameplay. Pending mini berikutnya turun di frame yang sama seperti
## Game._try_spawn_pending_mini_boss di ekor blok defeated pygame.
func _on_boss_defeated(boss: Node) -> void:
	if active_boss != boss:
		return
	active_boss = null
	if not pending_mini_bosses.is_empty():
		_boss_tick(0.0)


func _boss_tick(_delta: float) -> void:
	if GameManager.state != "playing":
		return
	if active_boss != null:
		if not is_instance_valid(active_boss) or bool(active_boss.get("is_dead")):
			active_boss = null
		else:
			return # satu boss aktif pada satu waktu, sama seperti pygame
	if not pending_mini_bosses.is_empty():
		var boss_type: String = pending_mini_bosses.pop_front()
		active_boss = GameManager.spawn_boss(boss_type, "red",
			_boss_spawn_point())
		# ENEMY SCALING (Hard only) — paritas _core.py:1822-1823
		if GameManager.enemy_scaling_enabled:
			active_boss.apply_scaling(GameManager.enemy_hp_mult,
				GameManager.enemy_damage_mult, GameManager.enemy_speed_mult)
		_show_boss_banner(boss_type) # paritas BossIntroCinematic _core.py:1826
		print("[Main] MINI BOSS %s turun ke mid lane%s" % [boss_type,
			" (scaling x%.2f)" % GameManager.enemy_hp_mult if GameManager.enemy_scaling_enabled else ""])
		return
	if not true_boss_spawned and red_towers_destroyed >= TRUE_BOSS_TOWER_KILLS:
		var lv: Dictionary = BossDB.get_level(GameManager.level_number)
		var true_boss := str(lv.get("true_boss", ""))
		if true_boss.is_empty():
			return
		active_boss = GameManager.spawn_boss(true_boss, "red",
			_boss_spawn_point())
		# ENEMY SCALING (Hard only) — paritas _core.py:2097-2098
		if GameManager.enemy_scaling_enabled:
			active_boss.apply_scaling(GameManager.enemy_hp_mult,
				GameManager.enemy_damage_mult, GameManager.enemy_speed_mult)
		true_boss_spawned = true
		_show_boss_banner(true_boss) # paritas BossIntroCinematic _core.py:2105
		print("[Main] TRUE BOSS %s turun (%d menara Dire hancur)" % [
			true_boss, red_towers_destroyed])

## Banner nama boss meluncur dari atas (paritas BossIntroCinematic
## _render.py:2152): 100 frame, gameplay TIDAK pause, skip SPACE/ESC/klik.
func _show_boss_banner(boss_type: String) -> void:
	if is_instance_valid(_boss_banner):
		_boss_banner.finish()
	var banner = preload("res://scenes/ui/BossIntroBanner.gd").new()
	banner.setup(BossDB.get_boss(boss_type))
	add_child(banner)
	_boss_banner = banner
	# Sama seperti intro: HUD disinkronkan seketika (PAUSE tersembunyi selama
	# banner). Tombol SKIP sudah dimatikan permanen di TouchHUD.
	_touch_hud_resync()

# ══════════════════════════════════════════════════════════
#  POSISI
# ══════════════════════════════════════════════════════════

func _base_center(team: String) -> Vector2:
	if _arena_map != null and _arena_map.has_method("get_own_base"):
		return _arena_map.get_own_base(team)
	return Vector2(150, 590) if team == "blue" else Vector2(1130, 130)

func _boss_spawn_point() -> Vector2:
	if _arena_map != null:
		var path: PackedVector2Array = _arena_map.get_lane_path("mid")
		if not path.is_empty():
			return path[path.size() - 1]
	return _base_center("red")

# ══════════════════════════════════════════════════════════
#  KAMERA
# ══════════════════════════════════════════════════════════

func _frame_camera() -> void:
	if _camera == null:
		return
	var size := _arena_size()
	# Viewport selalu berpusat di kamera -> pusatkan ke arena, lalu kunci limit
	# supaya kamera tidak bisa keluar dari map.
	_camera.position = size / 2.0
	_camera.limit_left = 0
	_camera.limit_top = 0
	_camera.limit_right = int(size.x)
	_camera.limit_bottom = int(size.y)
	_camera.reset_smoothing()

## ArenaMap.arena_size, dengan fallback — `.get()` dipakai (bukan `"x" in node`)
## supaya tidak bergantung pada operator `in` untuk Object.
func _arena_size() -> Vector2:
	if _arena_map != null:
		var got = _arena_map.get("arena_size")
		if got is Vector2:
			return got
	return Vector2(1280, 720)

func _process(delta: float) -> void:
	# Sentuhan dipanen PALING AWAL, sebelum cabang mana pun (pygame: event +
	# dispatch mendahului update/draw, main.py:337-479).
	_drain_gestures()
	# Main PROCESS_MODE_ALWAYS (supaya P/ESC bisa resume) -> jadwal boss, AI, dan
	# redraw slot harus ikut beku saat pause. AI Dire dijalankan oleh node
	# AIPlayer sendiri (PROCESS_MODE_PAUSABLE).
	if get_tree().paused:
		return
	_boss_tick(delta)
	_slot_pulse += delta
	# redraw slot 10x/detik: cukup halus untuk pulse, jauh lebih murah dari 60fps
	_slot_redraw_timer += delta
	if _slot_layer != null and _slot_redraw_timer >= 0.1:
		_slot_redraw_timer = 0.0
		_slot_layer.queue_redraw()
	# ── SPATIAL GRID (port _system.py:147-167, dijadwalkan _core.py:2009-2013) ──
	# pygame membangun ulang grid hanya pada frame GENAP, jadi hasil kueri boleh
	# basi satu frame (bucket-nya saja; posisi yang dibandingkan tetap live
	# karena grid menyimpan referensi unit). Frame gasal/luar-match sengaja tidak
	# membangun: CombatSystem lalu jatuh ke scan langsung, bukan ke grid basi.
	_grid_tick += 1
	if _grid_tick % CombatSystem.GRID_REBUILD_EVERY == 0:
		CombatSystem.update_spatial_grid_from_tree()
	if camera_follows_action and not get_tree().paused:
		_follow_action()

func _follow_action() -> void:
	if _camera == null:
		return
	var center := Vector2.ZERO
	var n := 0
	for hero in get_tree().get_nodes_in_group("heroes"):
		if is_instance_valid(hero) and not hero.is_dead:
			center += hero.global_position
			n += 1
	if n == 0:
		return
	var size := _arena_size()
	var focus := center / float(n)
	_camera.global_position = focus.clamp(
		Vector2(size.x / 2.0 - 120.0, size.y / 2.0 - 60.0),
		Vector2(size.x / 2.0 + 120.0, size.y / 2.0 + 60.0))

# ══════════════════════════════════════════════════════════
#  GAMBAR SLOT BANGUN
# ══════════════════════════════════════════════════════════

# ── Warna marker slot — port 1:1 ui_components BuildSlots ──
# (_render_blue_slot_surface / _render_red_slot_surface pygame:
#  platform batu berlapis + tanda plus menyala + chip harga "100G";
#  slot merah = segel gelap bertanda X.)
const SLOT_PLAT_DARK := Color(80.0 / 255.0, 80.0 / 255.0, 90.0 / 255.0)
const SLOT_PLAT_MID := Color(120.0 / 255.0, 120.0 / 255.0, 130.0 / 255.0)
const SLOT_PLAT_TOP := Color(160.0 / 255.0, 160.0 / 255.0, 170.0 / 255.0)
const SLOT_PLAT_RIM := Color(100.0 / 255.0, 100.0 / 255.0, 110.0 / 255.0)
const SLOT_PLAT_INNER := Color(140.0 / 255.0, 140.0 / 255.0, 150.0 / 255.0)
const SLOT_PLAT_SHINE := Color(180.0 / 255.0, 180.0 / 255.0, 190.0 / 255.0)
const SLOT_GLOW := Color(100.0 / 255.0, 200.0 / 255.0, 255.0 / 255.0, 0.24)
const SLOT_PLUS_DARK := Color(30.0 / 255.0, 60.0 / 255.0, 120.0 / 255.0)
const SLOT_PLUS_FILL := Color(100.0 / 255.0, 200.0 / 255.0, 255.0 / 255.0)
const SLOT_PLUS_SHINE := Color(200.0 / 255.0, 240.0 / 255.0, 255.0 / 255.0)
const SLOT_RED_DARK := Color(60.0 / 255.0, 20.0 / 255.0, 20.0 / 255.0)
const SLOT_RED_MID := Color(100.0 / 255.0, 40.0 / 255.0, 40.0 / 255.0)
const SLOT_RED_CORE := Color(140.0 / 255.0, 60.0 / 255.0, 60.0 / 255.0)
const SLOT_RED_X := Color(200.0 / 255.0, 80.0 / 255.0, 80.0 / 255.0)
const SLOT_GOLD := Color(1.0, 0.87, 0.35)
## Chip harga di bawah slot biru — dibuat sekali lalu dipakai ulang.
var _slot_chip_style: StyleBoxFlat = null

func _draw_slots() -> void:
	if _slot_layer == null:
		return
	# Pulse bilangan bulat -2..2 (pygame: int(sin(t*0.08)*2)) — mendorong
	# ukuran tanda plus dan radius glow pelan-pelan.
	var pk := int(round(sin(_slot_pulse * 2.6) * 2.0))
	var pulse := 0.5 + 0.5 * sin(_slot_pulse * 3.2)
	for i in range(GameManager.build_slots.size()):
		var s: Dictionary = GameManager.build_slots[i]
		if bool(s["taken"]):
			continue # menara yang berdiri sudah menggambar dirinya sendiri
		var pos: Vector2 = s["pos"]
		if str(s["team"]) == "blue":
			_draw_blue_slot(pos, pk)
		else:
			_draw_red_slot(pos)
		if i == GameManager.selected_slot:
			_draw_slot_selected(pos, pulse)


## Slot biru (interaktif): platform batu bulat berlapis + plus menyala +
## chip harga — geometri persis _render_blue_slot_surface pygame (surface
## 40x38 di-blit di (sx-20, sy-17) → offset platform (0, +5), plus (0, -1)).
func _draw_blue_slot(pos: Vector2, pk: int) -> void:
	var d := _slot_layer
	var plat := pos + Vector2(0.0, 5.0)   # pusat platform batu
	var core := pos + Vector2(0.0, 3.0)   # pusat pola dalam + glow
	# Bayangan tanah (ellipse 36x8 di bawah platform)
	d.draw_colored_polygon(_slot_ellipse(pos + Vector2(0.0, 16.0), 18.0, 4.0),
		Color(0, 0, 0, 100.0 / 255.0))
	# Platform batu — tiga lingkaran bertumpuk (rim gelap → terang)
	d.draw_circle(plat, 16.0, SLOT_PLAT_DARK)
	d.draw_circle(pos + Vector2(0.0, 4.0), 15.0, SLOT_PLAT_MID)
	d.draw_circle(core, 13.0, SLOT_PLAT_TOP)
	d.draw_arc(core, 13.0, 0.0, TAU, 26, SLOT_PLAT_RIM, 1.0)
	# Pola dalam (lingkaran ganda + kilau kiri-atas)
	d.draw_circle(core, 10.0, SLOT_PLAT_INNER)
	d.draw_circle(pos + Vector2(-2.0, 1.0), 5.0, SLOT_PLAT_SHINE)
	# Glow biru berdenyut (radius ikut pulse pygame 15 + pk)
	d.draw_circle(core, 15.0 + float(pk), SLOT_GLOW)
	# Tanda plus: outline gelap → isi cyan → kilau (plus_size = 8 + pk)
	var ps := 8 + pk
	var half := int(ps * 0.5)
	d.draw_rect(Rect2(pos + Vector2(-half - 1.0, -2.0), Vector2(ps + 2.0, 4.0)),
		SLOT_PLUS_DARK, true)
	d.draw_rect(Rect2(pos + Vector2(-2.0, -half - 1.0), Vector2(4.0, ps + 2.0)),
		SLOT_PLUS_DARK, true)
	d.draw_rect(Rect2(pos + Vector2(-half, -1.0), Vector2(ps, 2.0)),
		SLOT_PLUS_FILL, true)
	d.draw_rect(Rect2(pos + Vector2(-1.0, -half), Vector2(2.0, ps)),
		SLOT_PLUS_FILL, true)
	d.draw_rect(Rect2(pos + Vector2(-half, -1.0), Vector2(half, 1.0)),
		SLOT_PLUS_SHINE, true)
	d.draw_rect(Rect2(pos + Vector2(-1.0, -half), Vector2(1.0, half)),
		SLOT_PLUS_SHINE, true)
	# Chip harga "100G" (36x14, radius 3, border emas — persis pygame)
	var chip := Rect2(pos + Vector2(-18.0, 17.0), Vector2(36.0, 14.0))
	d.draw_style_box(_chip_style(), chip)
	var txt := "%dG" % TowerDB.build_cost()
	var font := UiTheme.body_bold()
	var ts: Vector2 = font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12)
	d.draw_string(font,
		Vector2(chip.position.x + (chip.size.x - ts.x) * 0.5,
			chip.position.y + chip.size.y * 0.5 + font.get_ascent(12) * 0.5 - 0.5),
		txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, UiTheme.GOLD_TEXT)


## Slot merah (visual saja): segel gelap bertanda X — port
## _render_red_slot_surface pygame.
func _draw_red_slot(pos: Vector2) -> void:
	var d := _slot_layer
	var core := pos + Vector2(0.0, 3.0)
	d.draw_circle(core, 10.0, SLOT_RED_DARK)
	d.draw_circle(core, 9.0, SLOT_RED_MID)
	d.draw_circle(pos + Vector2(-1.0, 2.0), 6.0, SLOT_RED_CORE)
	d.draw_line(pos + Vector2(-3.0, -1.0), pos + Vector2(3.0, 5.0), SLOT_RED_X, 1.0)
	d.draw_line(pos + Vector2(3.0, -1.0), pos + Vector2(-3.0, 5.0), SLOT_RED_X, 1.0)


## Ring seleksi slot: glow emas + cincin putus yang berputar pelan.
func _draw_slot_selected(pos: Vector2, pulse: float) -> void:
	var d := _slot_layer
	var plat := pos + Vector2(0.0, 3.0)
	d.draw_circle(plat, 20.0, Color(SLOT_GOLD.r, SLOT_GOLD.g, SLOT_GOLD.b,
		0.12 + 0.10 * pulse))
	var rot := _slot_pulse * 1.1
	for k in range(8):
		var a0 := rot + TAU * float(k) / 8.0
		d.draw_arc(plat, 21.0, a0, a0 + 0.42, 6, SLOT_GOLD, 2.0)


## Ellipse poligon (16 segmen) — padanan pygame.draw.ellipse untuk bayangan
## tanah slot (Godot tidak punya draw_ellipse).
func _slot_ellipse(center: Vector2, rx: float, ry: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(16):
		var a := TAU * float(i) / 16.0
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	return pts


## StyleBox chip harga (dibuat malas sekali, dipakai semua slot biru).
func _chip_style() -> StyleBoxFlat:
	if _slot_chip_style == null:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0.85)
		sb.border_color = UiTheme.GOLD
		sb.set_border_width_all(1)
		sb.set_corner_radius_all(3)
		_slot_chip_style = sb
	return _slot_chip_style

# ══════════════════════════════════════════════════════════
#  SELEKSI (klik) + INPUT
# ══════════════════════════════════════════════════════════

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			# TIDAK ada klik di sini lagi. pygame: klik kiri lahir dari aksi
			# "tap" — yaitu saat tombol DILEPAS (touch.py `_up`), bukan saat
			# ditekan; penekanannya hanya membuat titik sentuh. Di Godot jalur
			# itu kini ditangani `_dispatch_gesture`, dan satu-satunya tugas
			# cabang ini adalah mencatat "press ini lolos dari UI" -> klaim
			# `claimed` dilepas supaya tap-nya sampai ke arena.
			_press_claim.erase(TouchGestures.touch_id_of(event))
			return
		if mb.pressed and mb.button_index == MOUSE_BUTTON_RIGHT:
			# Klik kanan fisik dipetakan mesin gesture ke long_press (persis
			# touch.py:173-175) dan didispatch dari sana — dua tempat = klik
			# dobel.
			return
		return
	if event is InputEventKey:
		_on_key(event as InputEventKey)

## BUKTI HIDUP klaim cinematic. Node yang sudah keluar tree — atau yang
## berhenti memproses frame — tidak akan pernah memanggil finish()-nya
## sendiri, jadi klaim "cinematic aktif"-nya basi selamanya. Inilah jalur
## yang membuat PAUSE menghilang selama wave: HUD membaca klaim node mati,
## mengunci matriks game_playing_cine, dan PAUSE tidak pernah kembali.
## Cinematic produksi (LevelIntro / BossIntroBanner / BossDeathFX) semuanya
## ber-_process dengan PROCESS_MODE_ALWAYS, jadi syarat ini tidak pernah
## menolak cinematic sungguhan — hanya klaim yang tidak bisa dipertanggung-
## jawabkan.
static func _cine_live(n) -> bool:
	# URUTAN WAJIB: is_instance_valid() LEBIH DULU. Godot menolak operator `is`
	# pada instance yang sudah dibebaskan ("SCRIPT ERROR: Left operand of 'is'
	# is a previously freed instance") — dan justru node cinematic yang baru
	# saja di-free (intro selesai -> queue_free, referensi Main belum di-null)
	# adalah kasus yang paling sering lewat sini tiap frame.
	if not is_instance_valid(n):
		return false
	if not (n is Node):
		return false
	var node := n as Node
	if not node.is_inside_tree():
		return false
	# Mengimplementasikan _process tetapi tidak diproses = tidak mungkin
	# menyelesaikan dirinya sendiri (hitung mundurnya tidak berjalan).
	if node.has_method("_process") and not node.is_processing():
		return false
	return true


## Klaim intro level. Intro MEMBEKUKAN gameplay (_show_level_intro memasang
## get_tree().paused bersamaan dengan intro-nya, dan LevelIntro memegang
## pause lewat take_pause_ownership), jadi klaim intro TANPA tree pause =
## klaim basi: pause-nya sudah dilepas (atau tak pernah dipegang) sementara
## flag intro masih menyala.
func _level_intro_claims() -> bool:
	if not _cine_live(_level_intro):
		return false
	if not _level_intro.cinematic_active():
		return false
	return get_tree().paused


## true = tree beku karena INTRO LEVEL yang memegang pause-nya (bukan menu
## pause). Dibaca _toggle_pause supaya ESC/P selama intro tidak mencuri
## pause milik intro (dan meninggalkan HUD di matriks cinematic).
func _intro_owns_pause() -> bool:
	if not _level_intro_claims():
		return false
	return bool(_level_intro.get("_owns_pause"))


## Klaim banner boss (±1,7 dtk, tidak pernah membekukan gameplay).
func _boss_banner_claims() -> bool:
	return _cine_live(_boss_banner) and _boss_banner.cinematic_active()


## Cinematic grup ("cinematic") pertama yang klaimnya masih hidup — jalur
## perayaan kematian boss (BossDeathFX mendaftar ke grup itu).
func _cine_fx_live():
	for fx in get_tree().get_nodes_in_group("cinematic"):
		if _cine_live(fx) and fx.has_method("cinematic_active") \
				and fx.cinematic_active():
			return fx
	return null


## Klaim cinematic node itu masih hidup DAN masih menyala. Beda dengan
## _cine_live (bukti hidup saja): di sini klaimnya ikut dibaca, supaya
## referensi ke cinematic yang sudah selesai (finish() -> queue_free) bisa
## dibuang pada frame yang sama — bukan menunggu instance-nya benar-benar
## dibebaskan di akhir frame.
static func _cine_claim_alive(n) -> bool:
	# is_instance_valid() WAJIB lebih dulu (lihat catatan _cine_live):
	# operator `is` pada instance yang sudah dibebaskan = SCRIPT ERROR.
	if not is_instance_valid(n):
		return false
	if not (n is Node):
		return false
	var node := n as Node
	if not node.is_inside_tree():
		return false
	if not node.has_method("cinematic_active"):
		return false
	return bool(node.call("cinematic_active"))


## Buang referensi cinematic yang SUDAH selesai. queue_free() baru bekerja di
## akhir frame, jadi antara finish() dan pembebasannya `_level_intro` /
## `_boss_banner` masih menunjuk node yang klaimnya sudah mati. Selama itu
## rantai skip masih menyapa node tersebut dan HUD masih membaca sisa klaim —
## inilah yang membuat PAUSE terlihat "tertinggal" (tetap tersembunyi)
## setelah cinematic ditutup. Dipanggil di semua jalur skip + pembacaan
## klaim.
func _drop_finished_cine_refs() -> void:
	if _level_intro != null and not _cine_claim_alive(_level_intro):
		_level_intro = null
	if _boss_banner != null and not _cine_claim_alive(_boss_banner):
		_boss_banner = null


## Sinkronkan TouchHUD SEKETIKA, tanpa menunggu tick _process berikutnya.
## TouchHUD menghitung matriks tombolnya (PAUSE tersembunyi saat cinematic)
## dari klaim cinematic sekali per frame. Kalau cinematic berubah di dalam
## penanganan input (ESC/klik/skip) dan HUD baru menyusul di frame
## berikutnya, PAUSE tetap tersembunyi lebih lama dari seharusnya — dan pada
## jalur ESC tertinggal selamanya, karena state terakhir HUD terlanjur
## dihitung dari klaim yang sudah basi. Resync di sini membuat PAUSE kembali
## BERSAMAAN dengan usainya intro.
func _touch_hud_resync() -> void:
	var tree := get_tree()
	if tree == null:
		return
	var touch = tree.get_first_node_in_group("touch_hud")
	if touch == null or not is_instance_valid(touch):
		return
	if touch.has_method("sync_from_match"):
		touch.call("sync_from_match")


## Skip cinematic lewat klik, urutan paritas pygame: level intro -> banner
## boss -> perayaan kematian boss.
func _cinematic_click() -> bool:
	_drop_finished_cine_refs()
	var consumed := false
	if _level_intro_claims():
		consumed = bool(_level_intro.skip_click())
	elif _boss_banner_claims():
		consumed = bool(_boss_banner.skip_click())
	else:
		var fx = _cine_fx_live()
		if fx != null and fx.has_method("skip_click"):
			consumed = bool(fx.skip_click())
	if consumed:
		_drop_finished_cine_refs()
		_touch_hud_resync()
	return consumed

## STATE_SPLASH pygame (main_desktop_legacy.py:154-157): selama layar
## splash tampil, tombol pad APA PUN hanya melewatinya. Node splash
## mendaftar ke grup "splash" (scenes/ui/SplashScreen.gd).
func _splash_active() -> bool:
	for node in get_tree().get_nodes_in_group("splash"):
		if is_instance_valid(node) and node.has_method("is_done") \
				and not node.is_done():
			return true
	return false


func _skip_splash() -> void:
	for node in get_tree().get_nodes_in_group("splash"):
		if is_instance_valid(node) and node.has_method("skip"):
			node.skip()


## Cinematic mana yang aktif, dengan nama yang sama seperti pygame
## (level_intro / boss_intro / boss_death) — dibaca ControllerRouter untuk
## jejak paritas aksi `confirm` (main_desktop_legacy.py:210-221).
func _cinematic_kind() -> String:
	if _level_intro_claims():
		return "level_intro"
	if _boss_banner_claims():
		return "boss_intro"
	if _cine_fx_live() != null:
		return "boss_death"
	return ""


## Rantai yang SAMA dengan _cinematic_click/_cinematic_key, tanpa efek
## samping — dibaca TouchHUD tiap frame untuk memilih matriks tombol
## (PAUSE tersembunyi saat cinematic; paritas _cinematic_active main.py:
## intro/boss_intro + celebration).
func _cinematic_active() -> bool:
	# Referensi cinematic yang klaimnya sudah mati dibuang DULU: kalau tidak,
	# pembacaan ini (dipanggil TouchHUD tiap frame) masih bisa melihat sisa
	# klaim node yang sudah finish() tapi belum dibebaskan.
	_drop_finished_cine_refs()
	return _level_intro_claims() or _boss_banner_claims() \
		or _cine_fx_live() != null

## Skip cinematic lewat tombol; true = event dikonsumsi (jangan lanjut ke
## pause/gameplay). Tombol yang tidak diterima cinematic jatuh ke handler
## normal — paritas handle_skip pygame mengembalikan False untuk tombol lain.
func _cinematic_key(key: InputEventKey) -> bool:
	_drop_finished_cine_refs()
	var consumed := false
	if _level_intro_claims():
		consumed = bool(_level_intro.skip_key(key))
	elif _boss_banner_claims():
		consumed = bool(_boss_banner.skip_key(key))
	else:
		var fx = _cine_fx_live()
		if fx != null and fx.has_method("skip_key"):
			consumed = bool(fx.skip_key(key))
	if consumed:
		_drop_finished_cine_refs()
		_touch_hud_resync()
	return consumed

func _on_key(key: InputEventKey) -> void:
	# KEYUP: lepas tactical command yang sedang di-hold lewat tuts
	# G/F/T/C/B/D (paritas InputHandler.handle_key_up _core.py:8458-8472 —
	# TANPA gate state: release tetap dirutekan walau match sudah usai).
	if not key.pressed:
		_on_key_release(key)
		return
	if key.echo:
		return
	# F8 = FPS COUNTER di SEMUA state (paritas `main_desktop_legacy.py:98-100`:
	# ditangani SEBELUM dispatch state splash/menu/game/pause dan tombolnya
	# sengaja TIDAK ditelan, jadi state di bawahnya tetap melihat F8).
	if key.keycode == KEY_F8:
		# Paritas main.py:369-370 — di entry HIDUP, F8 mengsiklus overlay
		# debug 4 mode (`mobile/debug.py`), BUKAN panel FPS legacy.
		# `toggle_fps_counter()` (panel `_system.FPSCounter`) tetap ada untuk
		# harness/tes dan bisa dipanggil dari skrip console.
		toggle_debug_overlay()
	# Cinematic dicek SEBELUM pause/gameplay (paritas Game.handle_key
	# _core.py:2673-2686): ESC saat banner/perayaan = skip, bukan menu pause.
	if _cinematic_key(key):
		return
	var menu = _main_menu()
	# P/ESC dicek paling awal: justru dibutuhkan untuk RESUME saat tree di-pause
	if key.keycode == KEY_P or key.keycode == KEY_ESCAPE:
		if GameManager.shop_open:
			GameManager.close_shop()
		elif menu != null and menu.is_open():
			# menu PAUSE menangani ESC sendiri (resume / kembali)
			return
		elif key.keycode == KEY_ESCAPE and GameManager.state != "playing" \
				and not GameManager.in_menu:
			# ESC setelah menang/kalah -> menu utama (paritas handle_key
			# _core.py:8333-8336: return_to_menu_requested).
			_on_menu_main_menu()
		else:
			_toggle_pause()
		return
	# Menu utama terbuka -> semua input gameplay milik menu (pygame memisahkan
	# STATE_MENU / STATE_GAME di main.py).
	if menu != null and menu.is_open():
		return
	if get_tree().paused:
		return # sisa aksi adalah aksi gameplay -> ikut beku
	# ── SETELAH MATCH USAI: paritas InputHandler.handle_key _core.py:8320-8336 ──
	# ENTER: victory -> level berikutnya (main.py:566), defeat -> ulang level.
	# R: replay level yang sama. ESC/P sudah ditangani di atas -> menu utama.
	if GameManager.state != "playing":
		if key.keycode == KEY_ENTER or key.keycode == KEY_KP_ENTER \
				or key.is_action_pressed("restart_match"):
			if GameManager.state == "victory":
				if not GameManager.next_level():
					GameManager.restart_match() # level terakhir: tinggal replay
			else:
				GameManager.restart_match()
			return
		if key.keycode == KEY_R:
			GameManager.restart_match()
			return
		# N: victory -> level berikut (tak ada = diam); defeat -> diam.
		# Paritas victory_L1_n (next=true) vs victory_L54_n/defeat (false).
		if key.keycode == KEY_N and GameManager.state == "victory":
			GameManager.next_level()
			return
	# ── PERINTAH TAKTIS (FASE 18): paritas InputHandler.handle_key
	# _core.py:8343-8396 — blok taktis HANYA saat state "playing", dan
	# G/F/T/C/B/D return SEBELUM skill QWER (pygame: cabang elif berantai).
	# HOTKEY gather MEMAKAI posisi mouse + follow_mouse (beda dari tombol
	# panel yang gather tanpa posisi).
	if GameManager.state == "playing" and _tactical_hotkey(key.keycode):
		return
	# Skill hero terpilih — action sudah ada di project.godot (Q/W/E/R)
	if key.is_action_pressed("skill_q"):
		_cast_skill("q")
		return
	if key.is_action_pressed("skill_w"):
		_cast_skill("w")
		return
	if key.is_action_pressed("skill_e"):
		_cast_skill("e")
		return
	if key.is_action_pressed("skill_r"):
		_cast_skill("r")
		return
	if key.is_action_pressed("toggle_shop"):
		GameManager.toggle_shop()
		print("[Main] toko %s" % ("dibuka (H)" if GameManager.shop_open else "ditutup"))
		return
	if not enable_debug_controls:
		return
	if key.is_action_pressed("cycle_difficulty"):
		print("[Main] difficulty -> %s" % GameManager.cycle_difficulty())
		return
	if key.is_action_pressed("debug_respawn"):
		# restart penuh: gold, wave, state menang/kalah, nexus, dan slot direset
		GameManager.restart_match()
		return
	match key.keycode:
		KEY_T:
			_cycle_theme()
		KEY_SPACE:
			_buy_random_hero()

func _cast_skill(slot_key: String) -> void:
	var h = GameManager.selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		print("[Main] pilih hero Radiant dulu (klik) sebelum memakai skill %s" % slot_key.to_upper())
		return
	if str(h.get("team")) != "blue":
		return
	if h.has_method("cast_" + slot_key):
		h.call("cast_" + slot_key)

# ══════════════════════════════════════════════════════════
#  PERINTAH TAKTIS — PEMICU INPUT (FASE 18)
#  Port _core.py InputHandler.handle_key/handle_key_up + mobile/hud.py
#  apply_hud_action + cabang release/pause/APP_BG main.py. Manajer
#  (TacticalCommands.gd) tetap satu-satunya pemilik state taktis.
# ══════════════════════════════════════════════════════════

## KEYDOWN taktis (paritas InputHandler.handle_key _core.py:8343-8396):
##   G/F -> gather di posisi mouse bila kursor di dalam layar, else gather
##          default (follow_mouse=True di keduanya)
##   T    -> protect_tower dengan selected_tower BIRU bila ada, else auto
##   C/B/D -> protect_castle / attack_boss / attack_damage_dealer polos
## Return true = tuts taktis (event dikonsumsi, jangan lanjut ke skill).
func _tactical_hotkey(code: int) -> bool:
	if _tactical == null or not is_instance_valid(_tactical):
		return false
	var cmd = TACTICAL_KEY_TO_COMMAND.get(code)
	if cmd == null:
		return false
	match int(code):
		KEY_G, KEY_F:
			# Posisi mouse dibaca dari sumber yang sama dengan yang dipakai
			# manajer saat menerbitkan ulang (pygame: g.mouse_x/mouse_y).
			var m: Vector2 = _tactical._mouse_pos()
			if m.x >= 0.0 and m.x < 1280.0 and m.y >= 0.0 and m.y < 720.0:
				_tactical.hold_start("gather", [m.x, m.y], true)
			else:
				_tactical.hold_start("gather", [], true)
		KEY_T:
			var t = GameManager.selected_tower
			if t != null and is_instance_valid(t) and str(t.get("team")) == "blue":
				_tactical.hold_start("protect_tower", [t])
			else:
				_tactical.hold_start("protect_tower")
		KEY_C:
			_tactical.hold_start("protect_castle")
		KEY_B:
			_tactical.hold_start("attack_boss")
		KEY_D:
			_tactical.hold_start("attack_damage_dealer")
	return true

## KEYUP taktis (paritas InputHandler.handle_key_up _core.py:8440-8472):
## tanpa gate state — release tetap dirutekan (hold_end nama yang tidak
## cocok = no-op di manajer, sama seperti pygame).
func _on_key_release(key: InputEventKey) -> void:
	if GameManager.in_menu:
		return # paritas main.py: KEYUP hanya dirutekan di STATE_GAME
	if _tactical == null or not is_instance_valid(_tactical):
		return
	var cmd = TACTICAL_KEY_TO_COMMAND.get(key.keycode)
	if cmd != null:
		_tactical.hold_end(cmd)

## Tekan tombol panel perintah (paritas mobile/hud.apply_hud_action):
## gather TANPA posisi mouse; protect_tower pakai selected_tower biru.
func _tactical_panel_press(cmd_name: String) -> bool:
	if _tactical == null or not is_instance_valid(_tactical):
		return false
	if cmd_name == "protect_tower":
		var t = GameManager.selected_tower
		if t != null and is_instance_valid(t) and str(t.get("team")) == "blue":
			return bool(_tactical.hold_start("protect_tower", [t]))
		return bool(_tactical.hold_start("protect_tower"))
	if cmd_name == "gather":
		return bool(_tactical.hold_start("gather"))
	return bool(_tactical.hold_start(cmd_name))

## Lepas tombol panel perintah (paritas cabang release main.py:483-487 —
## hold_end(nama) berdasar sentuhan yang menekan).
func _tactical_panel_release(cmd_name: String) -> void:
	if _tactical == null or not is_instance_valid(_tactical):
		return
	_tactical.hold_end(cmd_name)

## Lepas SEMUA hold (paritas main.py:479-486 pause + APP_BG: hold "nyangkut"
## tidak boleh tetap aktif setelah KEYUP/release-nya jatuh di layar lain).
func _tactical_release_all() -> void:
	if _tactical == null or not is_instance_valid(_tactical):
		return
	_tactical.hold_end()
	var bar = get_tree().get_first_node_in_group("tactical_bar") \
		if get_tree() != null else null
	if bar != null and is_instance_valid(bar) and bar.has_method("release_all"):
		bar.call("release_all")

func _notification(what: int) -> void:
	# APP_BG pygame (main.py:348-360): aplikasi ke latar membatalkan semua
	# sentuhan tanpa event release -> lepas semua hold agar tidak nyangkut.
	if what == NOTIFICATION_APPLICATION_PAUSED:
		_tactical_release_all()

# ══════════════════════════════════════════════════════════
#  AKSI HUD SENTUH (FASE 23 — port mobile/hud.apply_hud_action)
# ══════════════════════════════════════════════════════════

## Terjemahkan tap tombol TouchHUD (signal hud_action, disambung di
## _ready) — paritas apply_hud_action (mobile/hud.py:296-339). Tombol hanya
## terlihat saat aksinya valid (matriks HudLayout.TOUCH_VISIBILITY), jadi
## guard di bawah hanya pengaman jalur programatik, bukan perilaku UI.
## (Perintah taktis TACTICAL_ACTIONS bukan urusan fungsi ini: di pygame
## maupun Godot, tombolnya milik side panel / TacticalBar — FASE 18.)
func _apply_touch_action(action: String) -> void:
	match action:
		"pause":
			# request_pause dihormati hanya di STATE_GAME (main.py:477);
			# saat menu pause SUDAH terbuka, abaikan (main.py:479).
			if GameManager.in_menu:
				return
			var menu = _main_menu()
			if menu != null and menu.is_open():
				return
			_toggle_pause()
		"debug":
			var hud = get_node_or_null(^"UI/HUD")
			if hud != null and hud.has_method("toggle_debug_overlay"):
				hud.toggle_debug_overlay()
		"skip":
			# handle_skip(SPACE) ke level_intro/boss_intro/boss_death —
			# rantai prioritas yang sama dengan klik cinematic di atas.
			# Tombolnya sendiri sudah dimatikan di TouchHUD (tidak pernah
			# digambar); cabang ini tetap ada sebagai padanan penuh
			# apply_hud_action pygame.
			if GameManager.in_menu:
				return
			_cinematic_click()
		"replay":
			if GameManager.in_menu or GameManager.state == "playing":
				return
			GameManager.restart_match()
		"next_level":
			if GameManager.state != "victory":
				return
			GameManager.next_level()
		"menu":
			if GameManager.in_menu or GameManager.state == "playing":
				return
			_on_menu_main_menu()
		"back":
			# Tombol back tak pernah tampil (sync pygame tak pernah
			# menyalakannya), tapi aksinya tetap diterjemahkan penuh:
			# menu.handle_key(ESCAPE).
			var back_menu = _main_menu()
			if back_menu != null and back_menu.is_open() \
					and back_menu.has_method("_handle_escape"):
				back_menu._handle_escape()

func _on_click(pos: Vector2) -> void:
	if GameManager.state != "playing" or get_tree().paused:
		return
	# Prioritas klik paritas _handle_left_click (_core.py:7811-7879):
	# BANGUNAN TOKO -> slot -> nexus -> hero biru -> perintah hero ->
	# menara biru -> deselect.
	# (1) Bangunan toko di map (paritas get_clicked_shop _render.py:246-260):
	# Radiant = ITEM FORGE (tab ITEM), Dire = HERO SHOP (tab HERO).
	if _arena_map != null and _arena_map.has_method("get_clicked_shop"):
		# Tipe eksplisit: _arena_map tak bertipe sehingga pemanggilannya
		# dinamis dan `:=` tidak bisa infer (Parse Error di Godot 4.3).
		var which: String = _arena_map.get_clicked_shop(pos)
		if which != "":
			_open_shop_tab(which)
			return
	var slot_idx := _pick_slot(pos)
	if slot_idx >= 0:
		GameManager.select_slot_index(slot_idx)
		GameManager.open_shop()
		return
	var nx = _pick_in_group("nexus", pos, 0.0)
	if nx != null:
		GameManager.select_nexus(nx)
		if str(nx.get("team")) == "blue":
			GameManager.open_shop()
		return
	var h = _pick_in_group("heroes", pos, 10.0)
	if h != null and str(h.get("team")) == "blue":
		GameManager.select_hero(h)
		return
	# Hero hidup terpilih: klik menara biru = pindah pilihan ke menara,
	# sisanya (termasuk klik musuh — Godot tak punya follow_target, aggro
	# otomatis mengambil alih) = MOVE, hero tetap dipilih.
	var sel = GameManager.selected_hero
	if sel != null and is_instance_valid(sel) and not bool(sel.get("is_dead")):
		var bt = _pick_in_group("towers", pos, 12.0)
		if bt != null and str(bt.get("team")) == "blue":
			GameManager.select_tower(bt)
			GameManager.open_shop()
			return
		if sel.has_method("set_destination"):
			sel.set_destination(pos, false)
		return
	var t = _pick_in_group("towers", pos, 12.0)
	if t != null and str(t.get("team")) == "blue":
		GameManager.select_tower(t)
		GameManager.open_shop()
		return
	GameManager.clear_selection()
	GameManager.close_shop()


## Buka toko pada tab tertentu (dipakai bangunan toko di map). Kalau toko
## sudah terbuka di tab lain, tutup dulu baru buka — open_shop() memang
## no-op (tanpa emit) saat sudah terbuka, jadi tanpa reset tab tidak
## berpindah. SFX ui_click 0.5 = paritas call site pygame.
func _open_shop_tab(tab_id: String) -> void:
	if GameManager.shop_open:
		GameManager.close_shop()
	GameManager.requested_shop_tab = tab_id
	GameManager.open_shop()
	AudioManager.play_sfx("ui_click", 0.5)

## Klik kanan: tutup toko + gerakkan hero terpilih (paritas
## _handle_right_click: close_popup + move_to kalau hero hidup).
func _on_right_click(pos: Vector2) -> void:
	if GameManager.state != "playing" or get_tree().paused:
		return
	GameManager.close_shop()
	var sel = GameManager.selected_hero
	if sel != null and is_instance_valid(sel) and not bool(sel.get("is_dead")) \
			and sel.has_method("set_destination"):
		sel.set_destination(pos, false)

## Unit terdekat dalam radius klik. `pad` menambah radius bawaan unit.
func _pick_in_group(group: String, pos: Vector2, pad: float):
	var best = null
	var best_dist := 1e9
	for n in get_tree().get_nodes_in_group(group):
		if not is_instance_valid(n) or bool(n.get("is_dead")):
			continue
		var node := n as Node2D
		if node == null:
			continue
		var r := float(n.get("radius")) if n.get("radius") != null else 16.0
		var d := pos.distance_to(node.global_position)
		if d <= maxf(8.0, r + pad) and d < best_dist:
			best_dist = d
			best = n
	return best

func _pick_slot(pos: Vector2) -> int:
	var best := -1
	var best_dist := 1e9
	var reach := maxf(20.0, TowerDB.slot_size() + 8.0)
	for i in range(GameManager.build_slots.size()):
		var s: Dictionary = GameManager.build_slots[i]
		if bool(s["taken"]):
			continue # slot terisi -> kliknya ditangkap menara
		var d: float = pos.distance_to(s["pos"])
		if d <= reach and d < best_dist:
			best_dist = d
			best = i
	return best

## Sinkronkan flag `selected` di unit + highlight slot tiap kali pilihan berubah
func _on_selection_changed() -> void:
	var hero = GameManager.selected_hero
	if hero != null and not is_instance_valid(hero):
		hero = null
		GameManager.selected_hero = null
	for h in get_tree().get_nodes_in_group("heroes"):
		if not is_instance_valid(h) or not h.has_method("set_selected"):
			continue
		var is_pick: bool = (h == hero)
		h.set_selected(is_pick)
		if "player_controlled" in h:
			h.player_controlled = is_pick and str(h.get("team")) == "blue"
	for t in get_tree().get_nodes_in_group("towers"):
		if is_instance_valid(t) and "selected" in t:
			t.selected = (t == GameManager.selected_tower)
	for n in get_tree().get_nodes_in_group("nexus"):
		if is_instance_valid(n) and "selected" in n:
			n.selected = (n == GameManager.selected_nexus)
	if _slot_layer != null:
		_slot_layer.queue_redraw()

# ══════════════════════════════════════════════════════════
#  EVENT PERTANDINGAN
# ══════════════════════════════════════════════════════════

func _on_tower_destroyed(tower: Node, _killer_team: String) -> void:
	if tower == null or not is_instance_valid(tower):
		return
	# Slot kembali kosong supaya bisa dibangun ulang (paritas pygame)
	for s in GameManager.build_slots:
		if s.get("tower") == tower:
			s["taken"] = false
			s["tower"] = null
	if GameManager.selected_tower == tower:
		GameManager.clear_selection()
	if str(tower.get("team")) == "red":
		# FASE 15: counter syarat true boss (>= 6) naik TEPAT SEKALI per
		# menara merah mati — signal ini hanya dipancarkan Tower.die() yang
		# ter-guard is_dead, satu-nya jalur kematian menara; reward gold/
		# skornya dibayar GameManager.register_tower_death (cabang TIM
		# KORBAN _core.py:2218-2227) di transaksi yang sama frame-nya.
		red_towers_destroyed += 1
		print("[Main] menara Dire hancur: %d/%d menuju true boss" % [
			red_towers_destroyed, TRUE_BOSS_TOWER_KILLS])

func _on_game_over(victory: bool) -> void:
	GameManager.clear_selection()
	GameManager.close_shop()
	var nxt := GameManager.next_level_number()
	if victory and nxt > 0:
		print("[Main] MENANG — ENTER lanjut level %d · R ulang · ESC menu" % nxt)
	else:
		print("[Main] %s — ENTER/R ulang level · ESC menu" % ("MENANG" if victory else "KALAH"))

# ═══ debug / util ═══

## P/ESC sekarang membuka MENU PAUSE (paritas MenuState.PAUSE pygame:
## RESUME / SETTINGS / MAIN MENU / QUIT, _core.py:6930), bukan sekadar
## membekukan tree tanpa antarmuka.
func _toggle_pause() -> void:
	var menu = _main_menu()
	# PAUSE MILIK INTRO LEVEL bukan milik menu. Intro membekukan tree lewat
	# take_pause_ownership dan hanya melepasnya lewat finish(); kalau ESC/P
	# dibiarkan "resume" di sini, tree jalan lagi sementara intro masih
	# tampil dan masih mengklaim cinematic — matriks HUD tinggal di
	# game_playing_cine, jadi PAUSE tidak pernah kembali.
	# ESC saat intro: tidak mencuri pause, tidak mengubah apa pun.
	if _intro_owns_pause():
		return
	if get_tree().paused:
		# sudah pause (via menu) -> resume
		get_tree().paused = false
		GameManager.set_paused(false)
		AudioManager.pause_bgm(false)
		AudioManager.pause_ambient(false)
		if menu != null:
			menu.close()
		return
	# Paritas main.py:475-486: pause terjadi saat tuts/tombol masih ditahan
	# -> KEYUP/release-nya jatuh di layar pause dan tidak pernah sampai,
	# jadi semua hold taktis dilepas sekarang (tidak "nyangkut" setelah
	# lanjut).
	_tactical_release_all()
	get_tree().paused = true
	GameManager.set_paused(true)
	AudioManager.pause_bgm(true)
	# Ambient ikut dibekukan bersama BGM: pygame tidak punya menu pause yang
	# menyisakan suara hutan, dan tanpa ini loop tetap berbunyi saat tree pause.
	AudioManager.pause_ambient(true)
	if menu != null:
		menu.open_pause()
	print("[Main] PAUSE — menu pause terbuka")

## Node MainMenu hidup di UI/MainMenu (dibangun dari kode; lihat MainMenu.gd).
## Dicari lewat grup supaya scene lain pun bisa memasang menu tanpa path kaku.
func _main_menu():
	var menu = get_tree().get_first_node_in_group("main_menu")
	if menu != null and is_instance_valid(menu):
		return menu
	return get_node_or_null(^"UI/MainMenu")

func _on_menu_play(level_num: int) -> void:
	# Mulai match dari LEVEL_SELECT. Connector dipakai supaya starting_level
	# (property yang dulu hardcoded 1) mengikuti pilihan pemain.
	get_tree().paused = false
	GameManager.set_paused(false)
	var connector := get_tree().get_first_node_in_group("game_connector")
	if connector != null and connector.has_method("start_match"):
		connector.start_match(level_num)
	else:
		GameManager.start_level(level_num, false)

func _on_menu_resume() -> void:
	get_tree().paused = false
	GameManager.set_paused(false)
	AudioManager.pause_bgm(false)
	AudioManager.pause_ambient(false)
	print("[Main] RESUME")

func _on_menu_main_menu() -> void:
	# Paritas return_to_menu_requested (main.py:582-586): match dibuang,
	# arena dibersihkan, state balik "idle", menu tampil di MAIN.
	# Dipanggil dari: tombol PAUSE "MENU UTAMA", ESC setelah menang/kalah,
	# dan tombol "MENU UTAMA" di panel game-over HUD (lewat grup "main").
	get_tree().paused = false
	GameManager.set_paused(false)
	GameManager.return_to_menu()
	_clear_field()
	_reset_boss_schedule()
	var menu = _main_menu()
	if menu != null and menu.has_method("show_main"):
		menu.show_main()
	print("[Main] kembali ke menu utama")

## Menu non-PAUSE menutupi layar PENUH: arena, unit, slot, dan HUD
## disembunyikan sehingga tidak ada kemungkinan layout "menu di samping
## arena". PAUSE = arena BEKU tetap kelihatan di belakang dim menu
## (paritas pygame: pause menggambar frame game terakhir + overlay).
func _apply_menu_coverage(covers: bool, is_pause: bool) -> void:
	# Non-PAUSE: sembunyikan total. PAUSE: arena + HUD tetap tampil,
	# menu hanya menambah lapisan dim gelap di atasnya.
	var game_visible := not covers or is_pause
	for path in [^"ArenaMap", ^"FX"]:
		var n := get_node_or_null(path)
		if n != null:
			n.visible = game_visible
	# "Containers" adalah Node polos (TIDAK punya properti visible) —
	# sembunyikan anak-anaknya (Towers/Minions/Heroes/Bosses, semua
	# Node2D) satu per satu.
	var containers := get_node_or_null(^"Containers")
	if containers != null:
		for child in containers.get_children():
			child.visible = game_visible
	if _slot_layer != null:
		_slot_layer.visible = game_visible
	var hud := get_node_or_null(^"UI/HUD")
	if hud != null:
		hud.visible = game_visible

func _cycle_theme() -> void:
	if _arena_map == null or not _arena_map.has_method("cycle_theme"):
		return
	print("[Main] tema map -> %s" % _arena_map.cycle_theme())

func _buy_random_hero() -> void:
	var types: Array = SaveManager.data.get("unlocked_heroes", [])
	if types.is_empty():
		return
	var pick: String = types[randi() % types.size()]
	if GameManager.try_buy_hero(pick):
		return
	print("[Main] gagal beli %s (gold %d)" % [pick, GameManager.gold])
