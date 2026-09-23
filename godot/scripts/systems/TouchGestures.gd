# TouchGestures.gd — port `mobile/touch.py` (TouchManager) 1:1 di sisi Godot.
#
# Penerjemah sentuh -> aksi game. Filosofi pygame dipertahankan utuh: kode
# game tidak dibongkar, sentuhan HANYA diterjemahkan:
#
#   TAP singkat          -> klik kiri      dispatch_button("tap")        == 1
#   TAHAN >= 450 ms       -> klik kanan     dispatch_button("long_press") == 3
#   GESER vertikal        -> notch scroll   dispatch_button("scroll")     == 4/5
#   GESER + lepas cepat   -> fling (inersia scroll)
#   DOUBLE TAP            -> TIDAK dipetakan (paritas `dispatch_to_game`:
#                            hanya tap / long_press / scroll yang punya aksi)
#
# KENAPA JALUR MOUSE ADALAH DEFAULT — alasan touch.py:69-84 dipertahankan
# apa adanya: SDL mengirim FINGERDOWN *dan* MOUSEBUTTONDOWN sintesis untuk
# sentuhan yang sama. Koordinat mouse sudah berada di ruang logis 1280x720
# (di Godot: pemetaan dilakukan `window/stretch/mode="canvas_items"`),
# sedangkan koordinat jari ternormalisasi ke jendela -> gampang meleset di
# tepi layar (tombol FPS/jeda). Jalur jari tetap diport untuk diagnostik dan
# dipaksa dengan `MYSTIC_USE_FINGER=1` — persis env var pygame.
#
# Siklus pakai (paritas main.py:342 + :401):
#   1. `feed_event(event)` untuk SETIAP InputEvent (pygame: process_event),
#   2. `update()` SEKALI per frame (long-press + inersia),
#   3. `collect()` mengambil antrean aksi frame itu (daftar dibalik, pygame:
#      `out = self._actions; self._actions = []`).
# Keputusan siapa yang menerima aksi (arena vs layar vs tombol HUD) ada di
# Main._dispatch_gesture — padanan `dispatch_to_game` / `dispatch_to_menu`.
#
# SEMUA angka ambang adalah kanon yang sama dengan C++
# `MysticMobile.touch_constants()` (dibangkitkan `tools/gen_mobile_cpp.py`
# dari AST `touch.py`): tiga backend (GDScript, C++, oracle Python) membaca
# angka yang sama. Dikunci `tools/test_godot_mobile_touch_parity.py` +
# `godot/tests/MobileTouchParityTest.tscn`.
extends Node
class_name TouchGestures

## ── Ambang batas (koordinat logis 1280x720) — touch.py:27-32 ──
const TAP_SLOP := 14
const LONG_PRESS_MS := 450
const DOUBLE_TAP_MS := 280
const SCROLL_STEP := 42
const FLING_FRICTION := 0.90
const FLING_MIN_SPEED := 0.6
## ── Literal mesin gesture (touch.py:206/226/236/258-259) — sama dengan
## kunci C++ supaya kedua backend tidak bisa drift sendiri-sendiri. ──
const DOUBLE_TAP_RADIUS_PX := 40
const FLING_ARM_SPEED := 4
const FLING_DIVISOR := 0.35
const FLING_MAX_STEPS := 3
const VELOCITY_KEEP := 0.6
const VELOCITY_NEW := 0.4

## Jenis aksi — komentar TouchAction.kind di touch.py:49-50.
const KIND_TAP := "tap"
const KIND_LONG_PRESS := "long_press"
const KIND_DOUBLE_TAP := "double_tap"
const KIND_DRAG := "drag"
const KIND_SCROLL := "scroll"
const KIND_RELEASE := "release"
const KIND_FLING := "fling"
const KIND_DOWN := "down"

## Kanon ambang (kunci: sama persis dengan MysticMobile.touch_constants()).
static func touch_constants() -> Dictionary:
	return {
		"tap_slop": TAP_SLOP,
		"long_press_ms": LONG_PRESS_MS,
		"double_tap_ms": DOUBLE_TAP_MS,
		"scroll_step": SCROLL_STEP,
		"fling_friction": FLING_FRICTION,
		"fling_min_speed": FLING_MIN_SPEED,
		"double_tap_radius_px": DOUBLE_TAP_RADIUS_PX,
		"fling_arm_speed": FLING_ARM_SPEED,
		"fling_divisor": FLING_DIVISOR,
		"fling_max_steps": FLING_MAX_STEPS,
		"velocity_keep": VELOCITY_KEEP,
		"velocity_new": VELOCITY_NEW,
	}


# ══════════════════════════════════════════════════════════
#  ATURAN MURNI — fungsi statis tanpa state, direplay tes
# ══════════════════════════════════════════════════════════

## touch.py:206 `tp.velocity = tp.velocity * 0.6 + dy * 0.4`
static func motion_velocity(prev_velocity: float, dy: float) -> float:
	return prev_velocity * VELOCITY_KEEP + dy * VELOCITY_NEW


## touch.py:211-212 `total > TAP_SLOP -> tp.moved = True` (geser di bawah
## ambang masih dianggap tap saat jari diangkat).
static func motion_exceeds_slop(total_dist: float) -> bool:
	return total_dist > float(TAP_SLOP)


## touch.py:217-222 SATU langkah loop scroll:
##   direction = -1 if scroll_accum > 0 else 1
##   scroll_accum -= SCROLL_STEP * (1 if scroll_accum > 0 else -1)
## Pemanggil mengulang selama `abs(accum) >= SCROLL_STEP` (di Godot:
## `while` di _motion, sama seperti pygame).
static func scroll_notch(accum: float) -> Dictionary:
	var direction := -1 if accum > 0.0 else 1
	var sub := float(SCROLL_STEP) * (1.0 if accum > 0.0 else -1.0)
	return {"direction": direction, "accum": accum - sub}


## touch.py:226-230 `dt < DOUBLE_TAP_MS and abs(dx) < 40 and abs(dy) < 40`
static func tap_is_double(dt_ms: float, dx: float, dy: float) -> bool:
	return dt_ms < float(DOUBLE_TAP_MS) \
		and absf(dx) < float(DOUBLE_TAP_RADIUS_PX) \
		and absf(dy) < float(DOUBLE_TAP_RADIUS_PX)


## touch.py:236 `elif tp.moved and abs(tp.velocity) > 4:`
static func release_is_fling(moved: bool, velocity: float) -> bool:
	return moved and absf(velocity) > float(FLING_ARM_SPEED)


## touch.py:258-259 `steps = int(abs(v) / (SCROLL_STEP * 0.35))` lalu
## `range(min(steps, 3))`. `int()` Python = truncasi ke nol; abs() menjamin
## non-negatif sehingga sama saja dengan floor.
static func fling_steps(velocity: float) -> int:
	var denom := float(SCROLL_STEP) * FLING_DIVISOR
	var steps := int(absf(velocity) / denom)
	return mini(steps, FLING_MAX_STEPS)


## touch.py:260 `value=-1 if self.fling_velocity > 0 else 1`
static func fling_direction(velocity: float) -> int:
	return -1 if velocity > 0.0 else 1


## touch.py:257 `self.fling_velocity *= FLING_FRICTION`
static func fling_decay(velocity: float) -> float:
	return velocity * FLING_FRICTION


## touch.py:256 `if abs(self.fling_velocity) > FLING_MIN_SPEED:` (di bawah
## itu inersia di-nol-kan, bukan dibiarkan menggantung).
static func fling_active(velocity: float) -> bool:
	return absf(velocity) > FLING_MIN_SPEED


## touch.py:251 `(now - tp.start_time) * 1000.0 >= LONG_PRESS_MS`
static func long_press_due(held_ms: float) -> bool:
	return held_ms >= float(LONG_PRESS_MS)


## touch.py:333-343 + :281-289 `dispatch_to_game` / `dispatch_to_menu`:
## tap -> klik kiri (1), long_press -> klik kanan (3),
## scroll -> 4 (naik, value<0) / 5 (turun). Aksi lain = 0 = tidak dipetakan.
## NOL berarti "tidak dikonsumsi", persis `return False` di pygame.
static func dispatch_button(kind: String, value: int = 0) -> int:
	if kind == KIND_TAP:
		return 1
	if kind == KIND_LONG_PRESS:
		return 3
	if kind == KIND_SCROLL:
		return 4 if value < 0 else 5
	return 0


# ══════════════════════════════════════════════════════════
#  STATE MESIN
# ══════════════════════════════════════════════════════════

## Peta titik aktif: touch id -> state (paritas `self.points` + TouchPoint
## __slots__: start_pos/pos/prev_pos/start_time/moved/long_fired/scroll_accum
## /velocity/claimed_by).
var points: Dictionary = {}
var enabled: bool = true
## true = baca InputEventScreenTouch/Drag dan BUANG mouse sintesis
## (MYSTIC_USE_FINGER=1), persis `use_finger_events` di touch.py.
var use_finger: bool = false
## Penghitung untuk layar diagnostik (touch.py:107 `self.counts`).
var counts: Dictionary = {"finger": 0, "mouse": 0, "tap": 0}
var last_raw: Variant = null
var last_logical: Variant = null
var fling_velocity: float = 0.0
var fling_pos: Vector2 = Vector2.ZERO
## Untuk highlight/hover (touch.py:113 `active_pos`; None saat jari lepas).
var active_pos: Variant = null
## Antrean aksi keluar (TouchAction di pygame).
var _actions: Array = []
var _last_tap_ms: float = 0.0
var _last_tap_pos: Vector2 = Vector2.ZERO
## Titikik seam tes: >= 0 = jam paksa (deterministik), < 0 = jam engine.
var time_ms_override: float = -1.0


func _ready() -> void:
	name = "TouchGestures"
	process_mode = Node.PROCESS_MODE_ALWAYS
	use_finger = OS.has_environment("MYSTIC_USE_FINGER") \
		and OS.get_environment("MYSTIC_USE_FINGER") == "1"


## Jam mesin gesture — padanan `time.perf_counter()` (detik) dalam MILISEKON
## supaya ambang 450/280 ms bisa dibandingkan langsung dengan pygame.
func now_ms() -> float:
	if time_ms_override >= 0.0:
		return time_ms_override
	return float(Time.get_ticks_usec()) / 1000.0


func _action(kind: String, pos: Vector2, delta: Vector2, value: float,
		tid: int) -> Dictionary:
	return {"kind": kind, "pos": pos, "delta": delta, "value": value,
		"touch_id": tid}


func _emit(kind: String, pos: Vector2, delta: Vector2 = Vector2.ZERO,
		value: float = 0.0, tid: int = 0) -> void:
	_actions.append(_action(kind, pos, delta, value, tid))


## touch.py:98-102 `collect()` — antrean diambil ALIH lalu dikosongkan.
func collect() -> Array:
	var out: Array = _actions
	_actions = []
	return out


## touch.py:296-299 `cancel()` — dibatalkan tanpa event release (app ke
## latar / pygame.QUIT): titik, inersia, DAN antrean dibuang.
func cancel() -> void:
	points.clear()
	fling_velocity = 0.0
	_actions.clear()
	# `active_pos` TIDAK dibuang: touch.py:265-268 hanya membersihkan points +
	# inersia + antrean, jadi highlight hover tetap pada posisi terakhir.


# ══════════════════════════════════════════════════════════
#  EVENT MASUK — padanan `process_event`
# ══════════════════════════════════════════════════════════

## Return true = event dikonsumsi lapisan ini (pygame: `if
## touch.process_event(event): continue` — event tidak dilihat handler lain).
func feed_event(event: InputEvent) -> bool:
	if not enabled:
		return false
	if use_finger:
		return _feed_finger(event)
	return _feed_mouse(event)


## Jalur MOUSE — dipakai desktop DAN Android (touch.py:155-180). Di Godot
## posisi event sudah berada di ruang logis viewport, jadi
## `plat.pointer_to_logical()` cukup menjadi `event.global_position`
## (stretch canvas_items yang memetakan jendela -> ruang 1280x720).
func _feed_mouse(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		# Dihitung dulu, tanpa memengaruhi logika (touch.py:127-132).
		counts["mouse"] = int(counts["mouse"]) + 1
		if mb.button_index == MOUSE_BUTTON_LEFT:
			last_raw = mb.global_position
			var pos := _to_logical(mb.global_position)
			last_logical = pos
			if mb.pressed:
				_down(0, pos)
			else:
				_up(0, pos)
			return true
		if mb.pressed and (mb.button_index == MOUSE_BUTTON_WHEEL_UP \
				or mb.button_index == MOUSE_BUTTON_WHEEL_DOWN):
			_emit(KIND_SCROLL, _to_logical(mb.global_position),
				Vector2.ZERO, -1 if mb.button_index == MOUSE_BUTTON_WHEEL_UP \
					else 1, 0)
			return true
		if mb.pressed and mb.button_index == MOUSE_BUTTON_RIGHT:
			_emit(KIND_LONG_PRESS, _to_logical(mb.global_position))
			return true
		return false
	if event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if mm.button_mask & MOUSE_BUTTON_MASK_LEFT:
			_motion(0, _to_logical(mm.global_position))
			return true
		return false
	return false


## Jalur FINGER (diagnostik / MYSTIC_USE_FINGER=1) — touch.py:135-153.
func _feed_finger(event: InputEvent) -> bool:
	if event is InputEventScreenTouch:
		counts["finger"] = int(counts["finger"]) + 1
		var st := event as InputEventScreenTouch
		var pos := _to_logical(st.global_position)
		if st.pressed:
			_down(touch_id_of(event), pos)
		else:
			_up(touch_id_of(event), pos)
		return true
	if event is InputEventScreenDrag:
		counts["finger"] = int(counts["finger"]) + 1
		var sd := event as InputEventScreenDrag
		_motion(touch_id_of(event), _to_logical(sd.global_position))
		return true
	if event is InputEventMouseButton or event is InputEventMouseMotion:
		# Buang mouse sintesis supaya tidak dobel (touch.py:148-151).
		return true
	return false


func _to_logical(at: Vector2) -> Vector2:
	return at


# ══════════════════════════════════════════════════════════
#  MESIN GESTURE — touch.py:186-264
# ══════════════════════════════════════════════════════════

func _down(tid: int, pos: Vector2) -> void:
	points[tid] = {
		"id": tid,
		"start_pos": pos,
		"pos": pos,
		"prev_pos": pos,
		"start_time": now_ms(),
		"moved": false,
		"long_fired": false,
		"scroll_accum": 0.0,
		"velocity": 0.0,
		"claimed_by": null,
	}
	active_pos = pos
	fling_velocity = 0.0
	_emit(KIND_DOWN, pos, Vector2.ZERO, 0, tid)


func _motion(tid: int, pos: Vector2) -> void:
	if not points.has(tid):
		return
	var tp: Dictionary = points[tid]
	var at: Vector2 = tp["pos"]
	var dx := pos.x - at.x
	var dy := pos.y - at.y
	tp["prev_pos"] = at
	tp["pos"] = pos
	active_pos = pos
	var start: Vector2 = tp["start_pos"]
	var total := sqrt((pos.x - start.x) * (pos.x - start.x) \
		+ (pos.y - start.y) * (pos.y - start.y))
	if motion_exceeds_slop(total):
		tp["moved"] = true
	if bool(tp["moved"]):
		tp["velocity"] = motion_velocity(float(tp["velocity"]), dy)
		_emit(KIND_DRAG, pos, Vector2(dx, dy), 0, tid)
		# Geser vertikal -> notch scroll untuk list panjang.
		var accum := float(tp["scroll_accum"]) + dy
		while absf(accum) >= float(SCROLL_STEP):
			var notch := scroll_notch(accum)
			accum = float(notch["accum"])
			_emit(KIND_SCROLL, pos, Vector2.ZERO, int(notch["direction"]),
				tid)
		tp["scroll_accum"] = accum


func _up(tid: int, pos: Vector2) -> void:
	if not points.has(tid):
		return
	var tp: Dictionary = points[tid]
	points.erase(tid)
	var held_ms := now_ms() - float(tp["start_time"])
	if not bool(tp["moved"]) and not bool(tp["long_fired"]):
		var now := now_ms()
		var last: Vector2 = _last_tap_pos
		var is_double := tap_is_double(now - _last_tap_ms, pos.x - last.x,
			pos.y - last.y)
		counts["tap"] = int(counts["tap"]) + 1
		if is_double:
			_emit(KIND_DOUBLE_TAP, pos, Vector2.ZERO, 0, tid)
			_last_tap_ms = 0.0
		else:
			_emit(KIND_TAP, pos, Vector2.ZERO, held_ms, tid)
			_last_tap_ms = now
			_last_tap_pos = pos
	elif release_is_fling(bool(tp["moved"]), float(tp["velocity"])):
		fling_velocity = float(tp["velocity"])
		fling_pos = pos
		_emit(KIND_FLING, pos, Vector2.ZERO, float(tp["velocity"]), tid)
	_emit(KIND_RELEASE, pos, Vector2.ZERO, 0, tid)
	if points.is_empty():
		active_pos = null


## Dipanggil tiap frame (touch.py:246-264): long-press + inersia scroll.
func update(now: float = -1.0) -> void:
	var t := now_ms() if now < 0.0 else now
	for tid in points.keys():
		var tp: Dictionary = points[tid]
		if bool(tp["long_fired"]) or bool(tp["moved"]):
			continue
		if long_press_due(t - float(tp["start_time"])):
			tp["long_fired"] = true
			_emit(KIND_LONG_PRESS, tp["pos"], Vector2.ZERO, 0, int(tid))
	# Inersia scroll setelah jari diangkat.
	if fling_active(fling_velocity):
		fling_velocity = fling_decay(fling_velocity)
		var steps := fling_steps(fling_velocity)
		for _i in steps:
			_emit(KIND_SCROLL, fling_pos, Vector2.ZERO,
				fling_direction(fling_velocity), 0)
	else:
		fling_velocity = 0.0


# ══════════════════════════════════════════════════════════
#  JEMBATAN KE API LAMA — padanan dispatch_to_game / dispatch_to_menu
# ══════════════════════════════════════════════════════════

## true = aksi punya pemetaan klik (tap/long_press/scroll) — paritas
## `return True` vs `return False` di dispatch_to_game/dispatch_to_menu.
## Touch id sebuah event. Jalur mouse SELALU id 0 (satu "jari virtual",
## persis touch.py:158 `_down(0, pos)`); jalur jari memakai `index` SDL/Godot.
static func touch_id_of(event: InputEvent) -> int:
	if event is InputEventScreenTouch:
		return int((event as InputEventScreenTouch).index)
	if event is InputEventScreenDrag:
		return int((event as InputEventScreenDrag).index)
	return 0


static func is_mapped(action: Dictionary) -> bool:
	return dispatch_button(str(action["kind"]),
		int(float(action["value"]))) != 0
