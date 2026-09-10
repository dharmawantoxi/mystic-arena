# ControllerRouter.gd — FASE 24: port blok routing controller di
# `main_desktop_legacy.py:146-320` (satu-satunya konsumen
# ControllerManager pygame: build Android `main.py:250` memasang
# `menu.controller_mgr = None`).
#
# Router ini menerjemahkan AKSI pad (confirm/cancel/skill_*/start/back/
# trigger/stick/dpad/scroll) menjadi panggilan ke JALUR PRODUKSI yang sama
# dengan keyboard/mouse — tidak ada logika gameplay di sini:
#
#   game.handle_key(K_q)        -> Main._on_key(InputEventKey Q)
#   game.handle_click(pos, 1)   -> Main._on_click(pos)
#   game.handle_click(pos, 3)   -> Main._on_right_click(pos)
#   game.handle_click(pos, 4/5) -> scroll toko (ShopPanel ScrollContainer)
#   menu.handle_click(pos, 1)   -> klik Control di bawah kursor virtual
#   menu.handle_key(ESCAPE)     -> MainMenu._handle_escape()
#   skip cinematic              -> Main._cinematic_click()
#   STATE_PAUSE + show_pause    -> Main._toggle_pause()
#   tactical.hold_end()         -> Main._tactical_release_all()
#   fps_counter.toggle()        -> HUD.toggle_debug_overlay()
#   next_level_requested        -> GameManager.next_level()
#   return_to_menu_requested    -> Main._on_menu_main_menu()
#
# Deviasi terdokumentasi:
#   * pygame punya dict `game.ui_buttons`/`menu.buttons` (id -> Rect) untuk
#     SNAP kursor (R3); Godot tidak punya registry itu — rect dibaca LANGSUNG
#     dari BaseButton yang terlihat di tree UI (`_ui_button_rects()`).
#     Harness paritas menyuntik `ui_buttons_override` supaya kasus snap
#     dibandingkan dengan rect yang sama seperti oracle pygame.
#   * pygame menutup UI berurutan shop -> build_popup -> popup -> hero ->
#     tower -> pause. Toko Godot terpadu (ShopPanel menampung menara/nexus/
#     slot/hero), jadi build_popup & popup melebur ke cabang shop; sisanya
#     (hero -> tower -> pause) tetap berurutan.
#   * pygame menggambar kursor virtual sendiri; Godot memakai
#     scenes/ui/VirtualCursor.gd (port draw_cursor) yang membaca node ini.
#
# Jejak produksi (`trace_enabled`) mengikuti pola `hold_trace` di
# TacticalCommands.gd: harness menyalakannya, produksi tidak terpengaruh.
extends Node

const STATE_SPLASH := "splash"
const STATE_MENU := "menu"
const STATE_GAME := "game"
const STATE_PAUSE := "pause"

## Scroll per layar (px) — paritas Menu.handle_click (_core.py:3897-3916)
## dan Game.handle_click (_core.py:2550-2559).
const SCROLL_LEVEL_SELECT := 60
const SCROLL_HERO_SHOP := 50
const SCROLL_GAME_SHOP := 50

## Lompatan kursor D-PAD — paritas main_desktop_legacy.py:180-205 (menu
## 150/300) dan :303-313 (game 80/100).
const MENU_JUMP_Y := 150
const MENU_JUMP_X := 300
const GAME_JUMP_Y := 80
const GAME_JUMP_X := 100

const SCREEN_W := 1280
const SCREEN_H := 720

var controller = null

## Harness paritas: rect tombol UI ter-script (pygame game.ui_buttons /
## menu.buttons). Kosong = baca dari tree UI produksi.
var ui_buttons_override: Dictionary = {}

## Harness paritas: jejak panggilan produksi. Entri = [nama, args...].
var trace_enabled := false
var trace: Array = []

## Harness paritas: paksa state ("" = deteksi dari produksi).
var state_override := ""


func _ready() -> void:
	add_to_group("controller_router")
	set_process(true)


func _process(_delta: float) -> void:
	tick_frame()


## Satu frame controller — paritas main_desktop_legacy.py:147-150
## (`controller.update()` lalu loop `get_pressed_actions()`).
func tick_frame() -> void:
	if controller == null or not is_instance_valid(controller):
		return
	if not controller.is_controller_mode() or not controller.connected:
		return
	controller.update()
	for action in controller.get_pressed_actions():
		route(str(action))


func reset_trace() -> void:
	trace.clear()


func _trace(entry: Array) -> void:
	if trace_enabled:
		trace.append(entry)


func _main():
	return get_parent()


func _main_menu():
	var m = _main()
	if m == null or not m.has_method("_main_menu"):
		return null
	return m._main_menu()


## State mesin paritas main_desktop_legacy.py (SPLASH/MENU/GAME/PAUSE).
func current_state() -> String:
	if state_override != "":
		return state_override
	var m = _main()
	if m != null and m.has_method("_splash_active") and m._splash_active():
		return STATE_SPLASH
	var menu = _main_menu()
	if menu != null and menu.is_open():
		return STATE_PAUSE if int(menu.state) == int(menu.State.PAUSE) \
			else STATE_MENU
	return STATE_GAME


func route(action: String) -> void:
	match current_state():
		STATE_SPLASH:
			_route_splash(action)
		STATE_MENU:
			_route_menu(action)
		STATE_PAUSE:
			_route_pause(action)
		_:
			_route_game(action)


# ══════════════════════════════════════════════════════════
#  SPLASH (main_desktop_legacy.py:154-157: tombol apa pun = skip)
# ══════════════════════════════════════════════════════════

## Jejak produksi di bawah memakai KOSAKATA PANGGILAN pygame
## (click/key/menu_click/menu_key/show_pause/hold_end/skip/fps_toggle/snap)
## supaya bisa dibandingkan 1:1 dengan oracle yang MENG-EXEC blok routing
## main_desktop_legacy.py apa adanya.
func _route_splash(_action: String) -> void:
	var m = _main()
	if m != null and m.has_method("_skip_splash"):
		_trace(["splash_skip"])
		m._skip_splash()


# ══════════════════════════════════════════════════════════
#  MENU (main_desktop_legacy.py:160-205)
# ══════════════════════════════════════════════════════════

func _route_menu(action: String) -> void:
	var menu = _main_menu()
	var pos := _cursor()
	match action:
		"confirm":
			_menu_click(pos, 1)
		"cancel", "back":
			_trace(["menu_key", "escape"])
			if menu != null and menu.has_method("_handle_escape"):
				menu._handle_escape()
		"stick_right":
			_snap_menu(menu)
		"stick_left":
			_trace(["fps_toggle"])
			_toggle_fps_overlay()
		"scroll_up":
			_menu_click(pos, 4)
		"scroll_down":
			_menu_click(pos, 5)
		"dpad_up":
			if _menu_is_scrollable(menu):
				_menu_click(pos, 4)
			else:
				controller.cursor_y = maxf(0.0, controller.cursor_y - MENU_JUMP_Y)
				_snap_menu(menu)
		"dpad_down":
			if _menu_is_scrollable(menu):
				_menu_click(pos, 5)
			else:
				controller.cursor_y = minf(float(SCREEN_H),
					controller.cursor_y + MENU_JUMP_Y)
				_snap_menu(menu)
		"dpad_left":
			controller.cursor_x = maxf(0.0, controller.cursor_x - MENU_JUMP_X)
			_snap_menu(menu)
		"dpad_right":
			controller.cursor_x = minf(float(SCREEN_W),
				controller.cursor_x + MENU_JUMP_X)
			_snap_menu(menu)


## Paritas menu.handle_click(pos, 1/4/5) — tombol 4/5 = roda gulir.
func _menu_click(pos: Vector2, button: int) -> void:
	_trace(["menu_click", int(pos.x), int(pos.y), button])
	if button == 1:
		_gui_click_at(pos)
	else:
		_gui_scroll_at(pos, -1 if button == 4 else 1)


## Paritas _snap_cursor_to_menu_button (main_desktop_legacy.py:13-18):
## guard `menu.buttons` kosong -> tidak ada snap sama sekali.
func _snap_menu(menu) -> void:
	var rects := _menu_button_rects(menu)
	if rects.is_empty():
		return
	_trace(["snap", "menu"])
	controller.snap_to_nearest_button(rects)


## Paritas _menu_is_scrollable (main_desktop_legacy.py:20-28).
func _menu_is_scrollable(menu) -> bool:
	if menu == null:
		return false
	return int(menu.state) == int(menu.State.HERO_SHOP) \
		or int(menu.state) == int(menu.State.LEVEL_SELECT)


# ══════════════════════════════════════════════════════════
#  PAUSE (main_desktop_legacy.py:314-320)
# ══════════════════════════════════════════════════════════

func _route_pause(action: String) -> void:
	var menu = _main_menu()
	match action:
		"confirm":
			_menu_click(_cursor(), 1)
		"cancel", "start", "back":
			# pygame menulis menu.action = "resume"; loop utama yang
			# mengeksekusinya. Jejaknya = ["menu_action", "resume"].
			_trace(["menu_action", "resume"])
			if menu != null and menu.has_method("_do_resume"):
				menu._do_resume()
		"stick_right":
			_snap_menu(menu)


# ══════════════════════════════════════════════════════════
#  GAME (main_desktop_legacy.py:207-313)
# ══════════════════════════════════════════════════════════

func _route_game(action: String) -> void:
	var m = _main()
	var pos := _cursor()
	match action:
		"confirm":
			# Cinematic skip dengan A (paritas :210-221).
			var kind := _cinematic_kind(m)
			if kind != "":
				_trace(["skip", kind])
				m._cinematic_click()
				return
			# Victory: A = PLAY NEXT LEVEL (paritas :224-231) — HANYA kalau
			# masih ada level berikutnya; kalau tidak, jatuh ke klik biasa
			# (pygame: `if next_lvl:` baru `continue`).
			if GameManager.state == "victory" \
					and GameManager.next_level_number() > 0:
				_trace(["next_level"])
				GameManager.next_level()
				controller.rumble(0.4, 10)
				return
			_game_click(pos, 1)
		"cancel":
			# Tutup UI berurutan, lalu pause (paritas :235-249).
			if GameManager.shop_open:
				_trace(["close_shop"])
				GameManager.close_shop()
			elif GameManager.selected_hero != null \
					and is_instance_valid(GameManager.selected_hero):
				_trace(["deselect_hero"])
				GameManager.clear_selection()
			elif GameManager.selected_tower != null \
					and is_instance_valid(GameManager.selected_tower):
				_trace(["deselect_tower"])
				GameManager.clear_selection()
			else:
				# Cabang cancel TANPA hold_end (paritas :246-249).
				_enter_pause(false)
		"skill_q":
			# Layar victory/defeat: X/Square = REPLAY (paritas :251-257) ->
			# yang dikirim R, bukan Q (jejak mengikuti tombol yang dikirim).
			if GameManager.state != "playing":
				_send_key(KEY_R, "r")
			else:
				_send_key(KEY_Q, "q")
			controller.rumble(0.4, 10)
		"skill_w":
			_send_key(KEY_W, "w")
			controller.rumble(0.4, 10)
		"skill_e":
			_send_key(KEY_E, "e")
			controller.rumble(0.4, 10)
		"skill_r":
			# Victory: RB/R1 = NEXT LEVEL (paritas :264-271) -> kirim N.
			if GameManager.state == "victory":
				_send_key(KEY_N, "n")
			else:
				_send_key(KEY_R, "r")
			controller.rumble(0.8, 20)
		"start":
			_enter_pause(true)
		"back":
			# VIEW/SELECT = menu utama setelah match usai (paritas :275-284).
			if GameManager.state != "playing":
				_trace(["return_to_menu"])
				if m != null and m.has_method("_on_menu_main_menu"):
					m._on_menu_main_menu()
			else:
				_enter_pause(true)
		"left_trigger":
			_send_key(KEY_H, "h")
		"right_trigger":
			_game_click(pos, 3)
		"stick_left":
			_trace(["fps_toggle"])
			_toggle_fps_overlay()
		"stick_right":
			# Paritas :288-292 — hanya kalau game.ui_buttons terisi.
			var rects := _game_button_rects()
			if not rects.is_empty():
				_trace(["snap", "game"])
				controller.snap_to_nearest_button(rects)
		"scroll_up":
			_game_click(pos, 4)
		"scroll_down":
			_game_click(pos, 5)
		"dpad_up":
			if GameManager.shop_open:
				_game_click(pos, 4)
			else:
				controller.cursor_y = maxf(0.0, controller.cursor_y - GAME_JUMP_Y)
		"dpad_down":
			if GameManager.shop_open:
				_game_click(pos, 5)
			else:
				controller.cursor_y = minf(float(SCREEN_H),
					controller.cursor_y + GAME_JUMP_Y)
		"dpad_left":
			controller.cursor_x = maxf(0.0, controller.cursor_x - GAME_JUMP_X)
		"dpad_right":
			controller.cursor_x = minf(float(SCREEN_W),
				controller.cursor_x + GAME_JUMP_X)


## Paritas game.handle_click(pos, 1/3/4/5).
func _game_click(pos: Vector2, button: int) -> void:
	var m = _main()
	_trace(["click", int(pos.x), int(pos.y), button])
	match button:
		1:
			if m != null and m.has_method("_on_click"):
				m._on_click(pos)
		3:
			if m != null and m.has_method("_on_right_click"):
				m._on_right_click(pos)
		_:
			_gui_scroll_at(pos, -1 if button == 4 else 1)


## Cinematic mana yang sedang aktif — nama yang sama dengan oracle
## (level_intro / boss_intro / boss_death).
func _cinematic_kind(m) -> String:
	if m == null or not m.has_method("_cinematic_kind"):
		return ""
	if not m.has_method("_cinematic_active") or not m._cinematic_active():
		return ""
	return str(m._cinematic_kind())


## STATE_PAUSE + menu.show_pause() (paritas main_desktop_legacy.py:246-249 /
## :272-274 / :281-284). URUTAN penting: show_pause dulu, hold_end belakangan
## — dan cabang `cancel` tidak memanggil hold_end sama sekali.
func _enter_pause(release_hold: bool) -> void:
	var m = _main()
	_trace(["show_pause"])
	if m != null and m.has_method("_toggle_pause"):
		m._toggle_pause()
	if release_hold and m != null and m.has_method("_tactical_release_all"):
		_trace(["hold_end"])
		m._tactical_release_all()


func _cursor() -> Vector2:
	return Vector2(float(controller.get_cursor_pos().x),
		float(controller.get_cursor_pos().y))


## KEYDOWN produksi (jalur yang sama dengan keyboard fisik). `name` = nama
## tombol pygame untuk jejak (oracle merekam pygame.key.name).
func _send_key(code: int, trace_name: String) -> void:
	_trace(["key", trace_name])
	var m = _main()
	if m == null or not m.has_method("_on_key"):
		return
	var ev := InputEventKey.new()
	ev.keycode = code
	ev.pressed = true
	m._on_key(ev)


func _toggle_fps_overlay() -> void:
	var hud = get_tree().get_first_node_in_group("hud") \
		if get_tree() != null else null
	if hud == null:
		hud = get_node_or_null(^"../../UI/HUD")
	if hud != null and hud.has_method("toggle_debug_overlay"):
		hud.toggle_debug_overlay()


# ══════════════════════════════════════════════════════════
#  JEMBATAN GUI (kursor virtual -> Control Godot)
# ══════════════════════════════════════════════════════════

## Klik kiri di posisi kursor = paritas handle_click(pos, 1): pygame
## menguji rect tombol lalu memanggil handler-nya; Godot menekan
## BaseButton yang benar-benar ada di bawah titik itu.
func _gui_click_at(pos: Vector2) -> void:
	var vp = get_viewport()
	if vp == null:
		return
	var node = vp.gui_find_control(pos)
	while node != null:
		if node is BaseButton:
			var btn := node as BaseButton
			if btn.visible and not btn.disabled:
				btn.pressed.emit()
			return
		node = node.get_parent()


## Scroll roda di posisi kursor — paritas handle_click(pos, 4/5): pygame
## menggeser offset list per layar (60/50/50 px) dan MENGABAIKAN scroll di
## layar tanpa list.
func _gui_scroll_at(pos: Vector2, direction: int) -> void:
	var amount := _scroll_amount(direction)
	if amount == 0:
		return
	var vp = get_viewport()
	if vp == null:
		return
	var node = vp.gui_find_control(pos)
	while node != null:
		if node is ScrollContainer:
			var sc := node as ScrollContainer
			var bar := sc.get_v_scroll_bar()
			if bar != null:
				bar.value = clampf(bar.value + float(amount),
					bar.min_value, bar.max_value)
			return
		node = node.get_parent()


func _scroll_amount(direction: int) -> int:
	var menu = _main_menu()
	if menu != null and menu.is_open():
		if int(menu.state) == int(menu.State.LEVEL_SELECT):
			return direction * SCROLL_LEVEL_SELECT
		if int(menu.state) == int(menu.State.HERO_SHOP):
			return direction * SCROLL_HERO_SHOP
		return 0
	if GameManager.shop_open:
		return direction * SCROLL_GAME_SHOP
	return 0


## Rect tombol UI yang bisa di-snap (paritas game.ui_buttons /
## menu.buttons). Urutan Dictionary = urutan tree, sama seperti urutan
## pengisian dict pygame saat draw.
func _menu_button_rects(menu) -> Dictionary:
	if not ui_buttons_override.is_empty():
		return ui_buttons_override
	var out: Dictionary = {}
	if menu == null or not is_instance_valid(menu):
		return out
	return _collect_buttons(menu, out)


func _game_button_rects() -> Dictionary:
	if not ui_buttons_override.is_empty():
		return ui_buttons_override
	var out: Dictionary = {}
	var hud = get_tree().get_first_node_in_group("hud") \
		if get_tree() != null else null
	if hud != null and is_instance_valid(hud):
		_collect_buttons(hud, out)
	return out


func _collect_buttons(root: Node, out: Dictionary) -> Dictionary:
	for child in root.get_children():
		if child is BaseButton:
			var btn := child as BaseButton
			if btn.visible and not btn.disabled:
				out[btn.get_path()] = Rect2(btn.global_position, btn.size)
		_collect_buttons(child, out)
	return out
