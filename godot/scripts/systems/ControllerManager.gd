# ControllerManager.gd — FASE 24: port 1:1 `controller_manager.py`
# (_core.py:9299-10234 — ControllerManager + InputMode + peta tombol +
# label/hint). Lapisan gamepad versi pygame ini sebelumnya TIDAK ADA di
# Godot (lihat komentar lama di HUD._build_hint_bar: "Godot belum punya
# lapisan input gamepad"), sehingga hint bar, kursor virtual, dan seluruh
# routing tombol pad tidak bisa diport.
#
# Apa yang port persis (nilai/urutan/aturan sama):
#   * LAZY INIT + deteksi tipe (xbox/ps/generic) dari NAMA + GUID dengan
#     daftar kata kunci yang sama (ROG Ally / Steam Deck / 8BitDo / ...),
#     lalu fallback layout "buttons >= 11 AND axes >= 4" -> xbox.
#   * Kursor virtual: speed 12 -> 25 dengan kurva magnitude^1.5, deadzone
#     0.25, clamp 0..1280 / 0..720 (SCREEN_WIDTH/HEIGHT pygame).
#   * get_pressed_actions(): tepi tombol (edge detect), D-PAD fresh +
#     auto-repeat (delay 22 frame, rate 5), trigger > 0.5, dan scroll
#     stick kanan (accum 0.55, deadzone 0.18, step 1.0, guard 8 tick) —
#     URUTAN aksi yang dikembalikan pun sama (penting: routing pygame
#     memproses aksi berurutan dalam satu frame).
#   * _resolve_scroll_axis(): mapped -> kandidat (3,2,4,5), lewati axis
#     yang mentok |v| > 0.95 (ciri trigger idle), hasil di-cache.
#   * rumble(intensity, frames): durasi_ms = int(frames * 16.67) lalu
#     stop otomatis saat timer habis di update().
#   * Tabel LABEL (_LABELS xbox/ps/generic), _KEY_LABELS, ACTION_BINDINGS,
#     get_button_label / get_action_label / get_hints (7 konteks).
#   * find_ui_button_at_cursor / snap_to_nearest_button (jarak ke CENTER,
#     tie-break urutan kamus = urutan pertama yang lebih kecil).
#
# Deviasi terdokumentasi (mesin, bukan perilaku):
#   1. pygame membaca tombol/axis MENTAH per vendor (XBOX_MAP/PS_MAP/
#      GENERIC_MAP); Godot menormalkan semua pad lewat SDL, jadi cukup
#      SATU peta berisi indeks SDL (A=0 B=1 X=2 Y=3 BACK=4 START=6 L3=7
#      R3=8 LB=9 RB=10 DPAD=11..14, axis 0..5). Ketiga tipe tetap ada
#      karena LABEL tombolnya berbeda (A/B/X/Y vs X/O/SQUARE/TRIANGLE).
#   2. pygame membaca D-PAD dari joystick.get_hat(0); Godot menerimanya
#      sebagai 4 tombol (JOY_BUTTON_DPAD_*), jadi `_device_hat()`
#      MENYINTESIS vektor hat (x = kanan-kiri, y = atas-bawah) dari empat
#      tombol itu. Algoritma fresh+repeat di bawah tidak berubah.
#   3. pygame punya get_numbuttons()/get_numaxes(); Godot tidak
#      mengeksposnya. `_device_button_count`/`_device_axis_count` memakai
#      `Input.is_joy_known()` (terpetakan SDL = 21 tombol / 6 axis =
#      JOY_BUTTON_SDL_MAX / JOY_AXIS_SDL_MAX, tak dikenal = 0/0) sehingga
#      aturan fallback ">= 11 tombol & >= 4 axis" tetap dieksekusi apa
#      adanya (harness paritas mengunci aturan itu dengan angka ter-script).
#   4. pygame Joystick.rumble(low, high, ms) -> Godot
#      Input.start_joy_vibration(device, weak, strong, detik):
#      low-frequency (kuat) = strong_magnitude, high-frequency (lemah) =
#      weak_magnitude. Nilai intensitas & durasi (ms) identik pygame.
#
# JEMBATAN PERANGKAT: semua pembacaan perangkat lewat `_device_*` dan
# bisa diganti perangkat TER-SCRIPT lewat `scripted_device` (pola
# mouse_override / ParityRng di repo ini). Produksi tidak terpengaruh.
extends Node

const SCREEN_W := 1280
const SCREEN_H := 720

## Paritas InputMode (_core.py:9313).
const MODE_KEYBOARD := "keyboard"
const MODE_CONTROLLER := "controller"

## Peta tombol SDL — padanan XBOX_MAP/PS_MAP/GENERIC_MAP pygame setelah
## normalisasi Godot (lihat deviasi 1 di header).
const BUTTON_MAP := {
	"name": "SDL",
	"confirm": JOY_BUTTON_A,
	"cancel": JOY_BUTTON_B,
	"skill_q": JOY_BUTTON_X,
	"skill_w": JOY_BUTTON_Y,
	"skill_e": JOY_BUTTON_LEFT_SHOULDER,
	"skill_r": JOY_BUTTON_RIGHT_SHOULDER,
	"start": JOY_BUTTON_START,
	"back": JOY_BUTTON_BACK,
	"stick_left": JOY_BUTTON_LEFT_STICK,
	"stick_right": JOY_BUTTON_RIGHT_STICK,
	"left_stick_x": JOY_AXIS_LEFT_X,
	"left_stick_y": JOY_AXIS_LEFT_Y,
	"right_stick_x": JOY_AXIS_RIGHT_X,
	"right_stick_y": JOY_AXIS_RIGHT_Y,
	"left_trigger": JOY_AXIS_TRIGGER_LEFT,
	"right_trigger": JOY_AXIS_TRIGGER_RIGHT,
}

## Urutan tepi tombol yang dikembalikan get_pressed_actions — paritas
## urutan kunci dict `btn_actions` pygame (_core.py:9637-9650).
const BUTTON_ACTION_ORDER: Array = [
	"confirm", "cancel", "skill_q", "skill_w", "skill_e", "skill_r",
	"start", "back", "stick_left", "stick_right",
]

const XBOX_KEYWORDS: Array = [
	"xbox", "xinput", "x-box", "microsoft",
	"x360", "360", "xone", "xb1",
	"rog", "asus", "ally",
	"steam", "valve",
	"gamesir", "razer", "8bitdo",
	"logitech", "thrustmaster",
]

const PS_KEYWORDS: Array = [
	"playstation", "ps4", "ps5", "ps3",
	"dualshock", "dualsense", "sony",
	"wireless controller",
]

## Label tombol per tipe — port _LABELS (_core.py:9996-10035).
const LABELS := {
	"xbox": {
		"confirm": "A", "cancel": "B",
		"skill_q": "X", "skill_w": "Y",
		"skill_e": "LB", "skill_r": "RB",
		"start": "MENU", "back": "VIEW",
		"left_trigger": "LT", "right_trigger": "RT",
		"stick_left": "L3", "stick_right": "R3",
		"dpad": "D-PAD", "left_stick": "L-STICK",
		"right_stick": "R-STICK",
	},
	"ps": {
		"confirm": "X", "cancel": "O",
		"skill_q": "SQUARE", "skill_w": "TRIANGLE",
		"skill_e": "L1", "skill_r": "R1",
		"start": "OPTIONS", "back": "SHARE",
		"left_trigger": "L2", "right_trigger": "R2",
		"stick_left": "L3", "stick_right": "R3",
		"dpad": "D-PAD", "left_stick": "L-STICK",
		"right_stick": "R-STICK",
	},
	"generic": {
		"confirm": "BTN1", "cancel": "BTN2",
		"skill_q": "BTN3", "skill_w": "BTN4",
		"skill_e": "L1", "skill_r": "R1",
		"start": "START", "back": "SELECT",
		"left_trigger": "L2", "right_trigger": "R2",
		"stick_left": "L3", "stick_right": "R3",
		"dpad": "D-PAD", "left_stick": "L-STICK",
		"right_stick": "R-STICK",
	},
}

## Label keyboard/mouse untuk aksi yang sama — port _KEY_LABELS
## (_core.py:10038-10047).
const KEY_LABELS := {
	"confirm": "CLICK", "cancel": "ESC",
	"skill_q": "Q", "skill_w": "W",
	"skill_e": "E", "skill_r": "R",
	"start": "ESC", "back": "ESC",
	"left_trigger": "H", "right_trigger": "R-CLICK",
	"stick_left": "F8", "stick_right": "TAB",
	"dpad": "ARROWS", "left_stick": "MOUSE",
	"right_stick": "WHEEL",
	"replay": "R", "next_level": "N",
	"skip": "SPACE", "shop": "H",
}

## Aksi gameplay -> tombol — port ACTION_BINDINGS (_core.py:10051-10065).
const ACTION_BINDINGS := {
	"skip": "confirm",
	"shop": "left_trigger",
	"move_hero": "right_trigger",
	"select": "confirm",
	"back": "cancel",
	"pause": "start",
	"to_menu": "back",
	"replay": "skill_q",
	"next_level": "skill_r",
	"fps": "stick_left",
	"snap": "stick_right",
	"scroll": "right_stick",
	"cursor": "left_stick",
}

## Harness paritas: perangkat TER-SCRIPT. null = perangkat nyata
## (singleton Input). Bentuk:
##   {"ids": [0], "names": {0: "Xbox Wireless Controller"},
##    "guids": {0: "03000000..."}, "buttons": {0: {0: true}},
##    "axes": {0: {0: 0.5}}, "hats": {0: [1, 0]},
##    "button_count": {0: 21}, "axis_count": {0: 6},
##    "rumble": []   # diisi manajer: [weak, strong, durasi_ms]
##    "stop_rumble": 0}
var scripted_device = null

var initialized := false
var active_mode: String = MODE_KEYBOARD
var device_id: int = -1
var controller_type = null
var button_map: Dictionary = {}
var connected := false

# Kursor virtual
var cursor_x: float = SCREEN_W / 2
var cursor_y: float = SCREEN_H / 2
var cursor_speed: float = 12.0
var cursor_max_speed: float = 25.0
var cursor_acceleration: float = 1.5
var cursor_visible := false
var deadzone: float = 0.25

# Edge detection tombol
var _prev_buttons: Dictionary = {}
var _prev_hat := Vector2i.ZERO
var _left_trigger_pressed := false
var _right_trigger_pressed := false
var _rumble_timer := 0

# D-pad auto-repeat
var _hat_hold_frames := 0
var _hat_repeat_dir := Vector2i.ZERO
var hat_repeat_delay := 22
var hat_repeat_rate := 5

# Right stick = scroll
var _scroll_accum: float = 0.0
var scroll_step: float = 1.0
var scroll_speed: float = 0.55
var scroll_deadzone: float = 0.18
var _scroll_axis = null


func _ready() -> void:
	add_to_group("controller")


# ═══════════════════════════════════════
#  JEMBATAN PERANGKAT
# ═══════════════════════════════════════

func _device_ids() -> Array:
	if scripted_device != null:
		return scripted_device.get("ids", [])
	return Input.get_connected_joypads()


func _device_name(id: int) -> String:
	if scripted_device != null:
		return str(scripted_device.get("names", {}).get(id, ""))
	return Input.get_joy_name(id)


func _device_guid(id: int) -> String:
	if scripted_device != null:
		return str(scripted_device.get("guids", {}).get(id, ""))
	return Input.get_joy_guid(id)


func _device_button_count(id: int) -> int:
	if scripted_device != null:
		return int(scripted_device.get("button_count", {}).get(id, 0))
	# Deviasi 3: Godot tidak mengekspos jumlah tombol mentah.
	return JOY_BUTTON_SDL_MAX if Input.is_joy_known(id) else 0


func _device_axis_count(id: int) -> int:
	if scripted_device != null:
		return int(scripted_device.get("axis_count", {}).get(id, 0))
	return JOY_AXIS_SDL_MAX if Input.is_joy_known(id) else 0


func _device_button(id: int, index: int) -> bool:
	if scripted_device != null:
		return bool(scripted_device.get("buttons", {}).get(id, {}).get(index, false))
	return Input.is_joy_button_pressed(id, index)


func _device_axis(id: int, index: int) -> float:
	if scripted_device != null:
		return float(scripted_device.get("axes", {}).get(id, {}).get(index, 0.0))
	return Input.get_joy_axis(id, index)


## Deviasi 2: D-PAD Godot = 4 tombol; sintesis vektor hat pygame
## (x = kanan-kiri, y = atas-bawah) supaya algoritma repeat identik.
func _device_hat(id: int) -> Vector2i:
	if scripted_device != null:
		var h = scripted_device.get("hats", {}).get(id, null)
		if h == null:
			return Vector2i.ZERO
		return Vector2i(int(h[0]), int(h[1]))
	var x := 0
	var y := 0
	if Input.is_joy_button_pressed(id, JOY_BUTTON_DPAD_RIGHT):
		x += 1
	if Input.is_joy_button_pressed(id, JOY_BUTTON_DPAD_LEFT):
		x -= 1
	if Input.is_joy_button_pressed(id, JOY_BUTTON_DPAD_UP):
		y += 1
	if Input.is_joy_button_pressed(id, JOY_BUTTON_DPAD_DOWN):
		y -= 1
	return Vector2i(x, y)


func _device_hat_count(id: int) -> int:
	if scripted_device != null:
		return int(scripted_device.get("hat_count", {}).get(id, 1))
	return 1 if _device_ids().has(id) else 0


func _device_start_rumble(weak: float, strong: float, duration_ms: int) -> void:
	if scripted_device != null:
		# Urutan mengikuti pygame Joystick.rumble(low, high, ms) supaya
		# jejak bisa dibandingkan 1:1 dengan oracle.
		scripted_device["rumble"].append(
			[_round6(strong), _round6(weak), duration_ms])
		return
	if device_id < 0:
		return
	Input.start_joy_vibration(device_id, weak, strong, duration_ms / 1000.0)


func _device_stop_rumble() -> void:
	if scripted_device != null:
		scripted_device["stop_rumble"] = \
			int(scripted_device.get("stop_rumble", 0)) + 1
		return
	if device_id < 0:
		return
	Input.stop_joy_vibration(device_id)


# ═══════════════════════════════════════
#  LAZY INIT (hanya saat dibutuhkan)
# ═══════════════════════════════════════

## Paritas init_joystick (_core.py:9403-9416).
func init_joystick() -> bool:
	if initialized:
		return connected
	initialized = true
	_scan_controllers()
	return connected


## Paritas _scan_controllers (_core.py:9418-9497): deteksi tipe dari nama +
## GUID + fallback layout, lalu reset tabel edge-detect tombol.
func _scan_controllers() -> void:
	var ids := _device_ids()
	if ids.is_empty():
		connected = false
		device_id = -1
		return

	device_id = int(ids[0])
	connected = true

	var raw_name := _device_name(device_id)
	var name_lower := raw_name.to_lower()
	var guid := _device_guid(device_id).to_lower()

	var num_buttons := _device_button_count(device_id)
	var num_axes := _device_axis_count(device_id)

	print("[CONTROLLER] Found: %s" % raw_name)
	print("[CONTROLLER] GUID: %s" % guid)
	print("[CONTROLLER] Buttons: %d, Axes: %d" % [num_buttons, num_axes])

	var is_xbox := false
	for kw in XBOX_KEYWORDS:
		if name_lower.find(str(kw)) >= 0:
			is_xbox = true
			break
	var is_ps := false
	for kw in PS_KEYWORDS:
		if name_lower.find(str(kw)) >= 0:
			is_ps = true
			break
	var is_xinput_guid := guid.find("xinput") >= 0 or guid.find("78696e70") >= 0

	if is_ps and not is_xbox:
		controller_type = "ps"
		print("[CONTROLLER] Type: PlayStation")
	elif is_xbox or is_xinput_guid:
		controller_type = "xbox"
		print("[CONTROLLER] Type: Xbox/XInput")
	else:
		if num_buttons >= 11 and num_axes >= 4:
			controller_type = "xbox"
			print("[CONTROLLER] Type: Xbox (auto-detected by layout)")
		else:
			controller_type = "generic"
			print("[CONTROLLER] Type: Generic")
	button_map = BUTTON_MAP.duplicate()

	_prev_buttons = {}
	for i in range(num_buttons):
		_prev_buttons[i] = false
	_prev_hat = Vector2i.ZERO
	_left_trigger_pressed = false
	_right_trigger_pressed = false
	_scroll_axis = null
	_scroll_accum = 0.0


## Paritas debug_print (_core.py:9500-9532).
func debug_print() -> void:
	if not connected or device_id < 0:
		print("[CONTROLLER DEBUG] No controller connected")
		return
	print("==================================================")
	print("[CONTROLLER DEBUG]")
	print("  Name: %s" % _device_name(device_id))
	print("  GUID: %s" % _device_guid(device_id))
	print("  Buttons: %d" % _device_button_count(device_id))
	print("  Axes: %d" % _device_axis_count(device_id))
	print("  Hats: %d" % _device_hat_count(device_id))
	print("  Detected as: %s" % str(controller_type))
	print("  Mode: %s" % active_mode)
	print("==================================================")


## Paritas rescan (_core.py:9535-9550).
func rescan() -> void:
	if not initialized:
		init_joystick()
		return
	initialized = true
	_scan_controllers()


# ═══════════════════════════════════════
#  MODE SWITCHING
# ═══════════════════════════════════════

## Paritas set_mode (_core.py:9552-9570).
func set_mode(mode: String) -> bool:
	if mode == MODE_CONTROLLER:
		if not init_joystick():
			print("[CONTROLLER] No controller found!")
			return false
		active_mode = MODE_CONTROLLER
		cursor_visible = true
		cursor_x = SCREEN_W / 2
		cursor_y = SCREEN_H / 2
		print("[INPUT] Controller mode (%s)" % str(controller_type))
		return true
	active_mode = MODE_KEYBOARD
	cursor_visible = false
	print("[INPUT] Keyboard mode")
	return true


func is_controller_mode() -> bool:
	return active_mode == MODE_CONTROLLER


# ═══════════════════════════════════════
#  UPDATE (HANYA saat controller mode)
# ═══════════════════════════════════════

## Paritas update (_core.py:9579-9625): timer rumble lalu kursor dengan
## kurva akselerasi.
func update() -> void:
	if active_mode != MODE_CONTROLLER:
		return
	if not connected or device_id < 0:
		return

	if _rumble_timer > 0:
		_rumble_timer -= 1
		if _rumble_timer <= 0:
			_device_stop_rumble()

	var axis_x := _device_axis(device_id, int(button_map["left_stick_x"]))
	var axis_y := _device_axis(device_id, int(button_map["left_stick_y"]))
	if absf(axis_x) < deadzone:
		axis_x = 0.0
	if absf(axis_y) < deadzone:
		axis_y = 0.0

	var magnitude := sqrt(axis_x * axis_x + axis_y * axis_y)
	if magnitude > 0.0:
		var speed := cursor_speed + (cursor_max_speed - cursor_speed) \
			* pow(magnitude, cursor_acceleration)
		cursor_x += axis_x * speed
		cursor_y += axis_y * speed

	cursor_x = clampf(cursor_x, 0.0, float(SCREEN_W))
	cursor_y = clampf(cursor_y, 0.0, float(SCREEN_H))


# ═══════════════════════════════════════
#  GET PRESSED ACTIONS
# ═══════════════════════════════════════

## Paritas get_pressed_actions (_core.py:9627-9751). URUTAN aksi = urutan
## dict pygame: tombol (sesuai BUTTON_ACTION_ORDER) -> dpad fresh -> dpad
## repeat -> trigger kiri/kanan -> scroll.
func get_pressed_actions() -> Array:
	if active_mode != MODE_CONTROLLER:
		return []
	if not connected or device_id < 0:
		return []

	var actions: Array = []
	var num_buttons := _device_button_count(device_id)

	for action in BUTTON_ACTION_ORDER:
		var btn_id: int = int(button_map.get(action, -1))
		if btn_id < 0 or btn_id >= num_buttons:
			continue
		var current := _device_button(device_id, btn_id)
		var prev := bool(_prev_buttons.get(btn_id, false))
		if current and not prev:
			actions.append(action)
		_prev_buttons[btn_id] = current

	if _device_hat_count(device_id) > 0:
		var hat := _device_hat(device_id)

		var fresh: Array = []
		if hat.y == 1 and _prev_hat.y != 1:
			fresh.append("dpad_up")
		if hat.y == -1 and _prev_hat.y != -1:
			fresh.append("dpad_down")
		if hat.x == -1 and _prev_hat.x != -1:
			fresh.append("dpad_left")
		if hat.x == 1 and _prev_hat.x != 1:
			fresh.append("dpad_right")
		for f in fresh:
			actions.append(f)

		if hat == Vector2i.ZERO:
			_hat_hold_frames = 0
			_hat_repeat_dir = Vector2i.ZERO
		else:
			if hat != _hat_repeat_dir:
				_hat_repeat_dir = hat
				_hat_hold_frames = 0
			else:
				_hat_hold_frames += 1
				var past := _hat_hold_frames - hat_repeat_delay
				if past >= 0 and past % hat_repeat_rate == 0:
					if hat.y == 1:
						actions.append("dpad_up")
					elif hat.y == -1:
						actions.append("dpad_down")
					if hat.x == -1:
						actions.append("dpad_left")
					elif hat.x == 1:
						actions.append("dpad_right")

		_prev_hat = hat

	var num_axes := _device_axis_count(device_id)
	var lt: int = int(button_map.get("left_trigger", -1))
	var rt: int = int(button_map.get("right_trigger", -1))

	if lt >= 0 and lt < num_axes:
		var lt_pressed := _device_axis(device_id, lt) > 0.5
		if lt_pressed and not _left_trigger_pressed:
			actions.append("left_trigger")
		_left_trigger_pressed = lt_pressed

	if rt >= 0 and rt < num_axes:
		var rt_pressed := _device_axis(device_id, rt) > 0.5
		if rt_pressed and not _right_trigger_pressed:
			actions.append("right_trigger")
		_right_trigger_pressed = rt_pressed

	var rsy = _resolve_scroll_axis(num_axes)
	if rsy != null:
		var axis := _device_axis(device_id, int(rsy))
		if absf(axis) > scroll_deadzone:
			_scroll_accum += axis * scroll_speed
			var guard := 0
			while _scroll_accum >= scroll_step and guard < 8:
				actions.append("scroll_down")
				_scroll_accum -= scroll_step
				guard += 1
			guard = 0
			while _scroll_accum <= -scroll_step and guard < 8:
				actions.append("scroll_up")
				_scroll_accum += scroll_step
				guard += 1
		else:
			_scroll_accum = 0.0

	return actions


## Paritas _resolve_scroll_axis (_core.py:9754-9811).
func _resolve_scroll_axis(num_axes: int):
	if _scroll_axis != null:
		return _scroll_axis

	var lx: int = int(button_map.get("left_stick_x", -99))
	var ly: int = int(button_map.get("left_stick_y", -99))
	var mapped: int = int(button_map.get("right_stick_y", -1))

	var candidates: Array = [mapped]
	for c in [3, 2, 4, 5]:
		if c != mapped:
			candidates.append(c)

	for idx in candidates:
		var val = _read_axis_candidate(int(idx), num_axes, lx, ly)
		if val == null:
			continue
		if absf(float(val)) > 0.95:
			continue
		if absf(float(val)) > scroll_deadzone:
			_scroll_axis = int(idx)
			if int(idx) != mapped:
				print("[CONTROLLER] Scroll axis terdeteksi: axis %d" % int(idx))
			return int(idx)

	var rest = _read_axis_candidate(mapped, num_axes, lx, ly)
	if rest != null and absf(float(rest)) <= 0.95:
		return mapped
	return null


func _read_axis_candidate(idx: int, num_axes: int, lx: int, ly: int):
	if idx < 0 or idx >= num_axes:
		return null
	if idx == lx or idx == ly:
		return null
	return _device_axis(device_id, idx)


func _round6(v: float) -> float:
	return round(v * 1000000.0) / 1000000.0


func get_cursor_pos() -> Vector2i:
	return Vector2i(int(cursor_x), int(cursor_y))


# ═══════════════════════════════════════
#  RUMBLE
# ═══════════════════════════════════════

## Paritas rumble (_core.py:9820-9835): durasi_ms = int(frames * 16.67).
func rumble(intensity: float = 0.5, duration_frames: int = 15) -> void:
	if not connected or device_id < 0:
		return
	if active_mode != MODE_CONTROLLER:
		return
	var duration_ms := int(duration_frames * 16.67)
	# pygame rumble(low, high, ms) -> Godot weak=high, strong=low (deviasi 4).
	_device_start_rumble(intensity * 0.7, intensity, duration_ms)
	_rumble_timer = duration_frames


# ═══════════════════════════════════════
#  UI TARGET (hover + snap)
# ═══════════════════════════════════════

## Paritas find_ui_button_at_cursor (_core.py:9936-9956). `ui_buttons` =
## Dictionary nama -> Rect2 (pygame: dict id -> Rect).
func find_ui_button_at_cursor(ui_buttons: Dictionary):
	if not is_controller_mode():
		return null
	var c := get_cursor_pos()
	for btn_id in ui_buttons:
		var rect: Rect2 = ui_buttons[btn_id]
		if rect.has_point(Vector2(float(c.x), float(c.y))):
			return rect
	return null


## Paritas snap_to_nearest_button (_core.py:9958-9987): jarak ke CENTER,
## strictly-less-than sehingga tie-break = entri pertama.
func snap_to_nearest_button(ui_buttons: Dictionary) -> void:
	if not is_controller_mode() or ui_buttons.is_empty():
		return
	var c := get_cursor_pos()
	var nearest_rect = null
	var nearest_dist := INF
	for btn_id in ui_buttons:
		var rect: Rect2 = ui_buttons[btn_id]
		var center := rect.get_center()
		var dist := Vector2(float(c.x), float(c.y)).distance_to(center)
		if dist < nearest_dist:
			nearest_dist = dist
			nearest_rect = rect
	if nearest_rect != null:
		cursor_x = float(int(nearest_rect.get_center().x))
		cursor_y = float(int(nearest_rect.get_center().y))


# ═══════════════════════════════════════
#  INFO
# ═══════════════════════════════════════

## Paritas get_controller_info (_core.py:9989-9995).
func get_controller_info() -> Dictionary:
	if not connected:
		return {"connected": false, "name": "None", "type": "none"}
	# `type` dikembalikan apa adanya (null sebelum deteksi) — oracle pygame
	# menyimpan controller_type mentah, jadi str() di sini akan mengubah
	# None menjadi "<null>".
	return {
		"connected": true,
		"name": _device_name(device_id),
		"type": controller_type,
	}


# ══════════════════════════════════════
#  BUTTON LABELS & HINTS
# ══════════════════════════════════════

## Paritas get_button_label (_core.py:10068-10082).
func get_button_label(action: String) -> String:
	if not is_controller_mode():
		return str(KEY_LABELS.get(action, "?"))
	var ctype := str(controller_type) if controller_type != null else "generic"
	var table: Dictionary = LABELS.get(ctype, LABELS["generic"])
	if table.has(action):
		return str(table[action])
	return str(KEY_LABELS.get(action, "?"))


## Paritas get_action_label (_core.py:10084-10100).
func get_action_label(gameplay_action: String) -> String:
	if not is_controller_mode():
		if KEY_LABELS.has(gameplay_action):
			return str(KEY_LABELS[gameplay_action])
		var fallback_btn: String = str(ACTION_BINDINGS.get(gameplay_action, ""))
		return str(KEY_LABELS.get(fallback_btn, "?"))
	var btn: String = str(ACTION_BINDINGS.get(gameplay_action, ""))
	if not ACTION_BINDINGS.has(gameplay_action):
		return "?"
	return get_button_label(btn)


## Paritas get_hints (_core.py:10102-10163). Return Array dari [label, desc].
func get_hints(context: String = "game") -> Array:
	match context:
		"cinematic":
			return [[get_action_label("skip"), "Skip"]]
		"menu":
			return [
				[get_action_label("select"), "Select"],
				[get_action_label("back"), "Back"],
				[get_button_label("dpad"), "Navigate"],
			]
		"pause":
			return [
				[get_action_label("select"), "Select"],
				[get_action_label("pause"), "Resume"],
			]
		"shop":
			if is_controller_mode():
				return [
					[get_action_label("select"), "Buy"],
					[get_action_label("back"), "Close"],
					[get_button_label("right_stick") + "/" \
						+ get_button_label("dpad"), "Scroll"],
					[get_action_label("snap"), "Snap"],
				]
			return [
				[get_action_label("select"), "Buy"],
				[get_action_label("back"), "Close"],
				[get_action_label("scroll"), "Scroll"],
				[get_action_label("snap"), "Snap"],
			]
		"victory":
			return [
				[get_action_label("next_level"), "Next Level"],
				[get_action_label("replay"), "Replay"],
				[get_action_label("to_menu"), "Menu"],
			]
		"defeat":
			return [
				[get_action_label("replay"), "Replay"],
				[get_action_label("to_menu"), "Menu"],
			]
	return [
		[get_button_label("skill_q"), "Q"],
		[get_button_label("skill_w"), "W"],
		[get_button_label("skill_e"), "E"],
		[get_button_label("skill_r"), "R"],
		[get_action_label("shop"), "Shop"],
		[get_action_label("move_hero"), "Move Hero"],
		[get_action_label("pause"), "Pause"],
	]


## Toggle input mode — paritas Menu._toggle_input_mode (_core.py:7630-7647)
## yang dipanggil tombol INPUT di menu utama.
func toggle_input_mode() -> bool:
	if is_controller_mode():
		return set_mode(MODE_KEYBOARD)
	if connected:
		return set_mode(MODE_CONTROLLER)
	rescan()
	if connected:
		return set_mode(MODE_CONTROLLER)
	print("[INPUT] No controller detected!")
	return false


## Label tombol INPUT di menu — paritas Menu.draw (_core.py:3825-3843).
func input_mode_label() -> String:
	if is_controller_mode():
		return "INPUT: %s CONTROLLER" % str(get_controller_info()["type"]).to_upper()
	return "INPUT: KEYBOARD + MOUSE"
