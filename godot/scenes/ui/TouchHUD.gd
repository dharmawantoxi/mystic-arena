# TouchHUD.gd — HUD sentuh (port mobile/hud.py TouchHUD 1:1).
#
# Tombol layar pengganti keyboard: PAUSE (II) + FPS di kiri atas bawah
# panel gold, SKIP saat cinematic, REPLAY / NEXT LEVEL / MENU setelah
# match usai, BACK di menu. Geometri & visibilitas = kanon HudLayout
# (TOUCH_BUTTONS / TOUCH_VISIBILITY) yang dikunci UiHudParityTest.
#
# Aksi diteruskan sebagai signal `hud_action(action)`; Main.gd
# menerjemahkannya (paritas apply_hud_action): pause, debug, skip,
# replay, next_level, menu, back.
extends Control
class_name TouchHUD

signal hud_action(action: String)

const BG := Color(16.0 / 255.0, 14.0 / 255.0, 22.0 / 255.0, 205.0 / 255.0)
const BG_ACTIVE := Color(60.0 / 255.0, 48.0 / 255.0, 20.0 / 255.0,
	235.0 / 255.0)
const BTN_WHITE := Color("#ebebf5")
const BTN_GREY := Color("#787887")
const BTN_GOLD := Color("#ffc846")
const BTN_GOLD_DIM := Color("#967628")

var _buttons: Dictionary = {}
var _state_key: String = "menu"
var show_debug_button: bool = true


func _ready() -> void:
	name = "TouchHUD"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build_layout()
	# TouchHUD digambar manual (satu _draw) — bukan kumpulan Button,
	# supaya glow + cincin ganda + capsule highlight identik pygame.
	var view := _TouchView.new(self)
	view.set_anchors_preset(Control.PRESET_FULL_RECT)
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(view)
	_sync_visibility()


func _build_layout() -> void:
	# Geometri persis HudLayout.TOUCH_BUTTONS (+ warna & font pygame).
	_add_button("pause", Rect2(22, 76, 52, 52), "II", "round", BTN_GOLD,
		22)
	_add_button("debug", Rect2(106, 76, 52, 52), "FPS", "round",
		Color("#78c8ff"), 16)
	_add_button("skip", Rect2(1110, 646, 160, 58), "SKIP  >>", "capsule",
		BTN_GOLD, 20)
	_add_button("replay", Rect2(330, 620, 165, 62), "REPLAY", "capsule",
		BTN_GOLD, 20)
	_add_button("next_level", Rect2(525, 620, 200, 62), "NEXT LEVEL",
		"capsule", Color("#78e68c"), 18)
	_add_button("menu", Rect2(755, 620, 165, 62), "MENU", "capsule",
		BTN_GOLD, 22)
	_add_button("back", Rect2(8, 6, 104, 58), "< BACK", "capsule",
		BTN_GOLD, 20)


func _add_button(action: String, rect: Rect2, label: String, shape: String,
		color: Color, font_size: int) -> void:
	# Area sentuh diperlonggar (paritas inflate 24 + MIN_TAP 80).
	var hit := rect.grow(12.0)
	if hit.size.x < 80.0 or hit.size.y < 80.0:
		hit = rect.grow_individual(
			maxf(0.0, (80.0 - rect.size.x) * 0.5), maxf(0.0,
				(80.0 - rect.size.y) * 0.5),
			maxf(0.0, (80.0 - rect.size.x) * 0.5),
			maxf(0.0, (80.0 - rect.size.y) * 0.5))
	_buttons[action] = {"rect": rect, "hit": hit, "label": label,
		"shape": shape, "color": color, "font_size": font_size,
		"visible": false, "enabled": true, "press_anim": 0.0}


## Kunci visibilitas dari state (paritas TouchHUD.sync + matriks fixture).
func set_state_key(state_key: String) -> void:
	_state_key = state_key
	_sync_visibility()
	queue_redraw()


func _sync_visibility() -> void:
	var vis: Dictionary = HudLayout.touch_visibility(_state_key)
	for action in _buttons:
		var d: Dictionary = _buttons[action]
		d["visible"] = bool(vis.get(action, false))
	# Tombol debug bisa disembunyikan permanen (paritas show_debug_button).
	if not show_debug_button and _buttons.has("debug"):
		(_buttons["debug"] as Dictionary)["visible"] = false


func _process(delta: float) -> void:
	var dirty := false
	for action in _buttons:
		var d: Dictionary = _buttons[action]
		if float(d["press_anim"]) > 0.0:
			d["press_anim"] = maxf(0.0,
				float(d["press_anim"]) - delta * 7.2)
			dirty = true
	if dirty:
		queue_redraw()


func _gui_input(event: InputEvent) -> void:
	# Root IGNORE — input ditangani di _input global (di bawah).
	pass


func _input(event: InputEvent) -> void:
	if not visible:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			_tap_at(get_global_mouse_position())
	elif event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			_tap_at(st.position * _touch_scale())


func _touch_scale() -> Vector2:
	# Posisi sentuh dalam piksel viewport -> koordinat logis 1280x720.
	var vp := get_viewport_rect().size
	return Vector2(1280.0 / maxf(1.0, vp.x), 720.0 / maxf(1.0, vp.y))


func _tap_at(logical_pos: Vector2) -> void:
	# Urutan terbalik (tombol terakhir = paling atas) — paritas hit_test.
	var keys := _buttons.keys()
	keys.reverse()
	for action in keys:
		var d: Dictionary = _buttons[action]
		if not bool(d["visible"]):
			continue
		if (d["hit"] as Rect2).has_point(logical_pos):
			d["press_anim"] = 1.0
			queue_redraw()
			hud_action.emit(str(action))
			get_viewport().set_input_as_handled()
			return


func is_visible_button(action: String) -> bool:
	if not _buttons.has(action):
		return false
	return bool((_buttons[action] as Dictionary)["visible"])


# ── View (gambar manual 1:1 pygame) ──

class _TouchView extends Control:
	var hud: TouchHUD

	func _init(h: TouchHUD) -> void:
		hud = h
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		if hud == null or size.x <= 0.0:
			return
		draw_set_transform(Vector2.ZERO, 0.0,
			Vector2(size.x / 1280.0, size.y / 720.0))
		for action in hud._buttons:
			var d: Dictionary = hud._buttons[action]
			if not bool(d["visible"]):
				continue
			if str(d["shape"]) == "round":
				_draw_round(d)
			else:
				_draw_capsule(d)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	func _draw_round(d: Dictionary) -> void:
		var rect: Rect2 = d["rect"]
		var c := rect.get_center()
		var r := rect.size.x * 0.5
		var col: Color = d["color"]
		var ring := col if bool(d["enabled"]) else TouchHUD.BTN_GREY
		var press := int(float(d["press_anim"]) * 3.0)
		# Glow lembut di belakang tombol.
		UiTheme.draw_glow(self, Rect2(c.x - r - 22, c.y - r - 22,
			r * 2 + 44, r * 2 + 44), col, 46.0 / 255.0, 8)
		var base := TouchHUD.BG_ACTIVE if float(d["press_anim"]) > 0.0 \
			else TouchHUD.BG
		draw_circle(c, r, base)
		draw_arc(c, r, 0, TAU, 40, ring, 3.0)
		# Cincin dalam halus (identitas premium).
		draw_arc(c, r - 6.0, 0, TAU, 36, Color.WHITE, 1.0)
		var font := UiTheme.body_bold()
		var txt_col := TouchHUD.BTN_WHITE if bool(d["enabled"]) \
			else Color("#aaaab4")
		UiTheme.draw_text_centered(self, font, str(d["label"]),
			int(d["font_size"]) + press, txt_col, c + Vector2(0, -2),
			false)

	func _draw_capsule(d: Dictionary) -> void:
		var rect: Rect2 = d["rect"]
		var radius := rect.size.y * 0.5
		var col: Color = d["color"]
		var ring := col if bool(d["enabled"]) else TouchHUD.BTN_GREY
		UiTheme.draw_glow(self, rect.grow(Vector2(18, 14)), col,
			40.0 / 255.0, 8)
		var base := TouchHUD.BG_ACTIVE if float(d["press_anim"]) > 0.0 \
			else TouchHUD.BG
		UiTheme.draw_rr(self, rect, base, radius)
		UiTheme.draw_rr_outline(self, rect, ring, radius, 2.0)
		# Sorot tepi atas (kedalaman).
		draw_line(Vector2(rect.position.x + rect.size.x * 0.25,
			rect.position.y + 2),
			Vector2(rect.position.x + rect.size.x * 0.75,
				rect.position.y + 2), Color.WHITE, 1.0)
		var font := UiTheme.body_bold()
		var txt_col := TouchHUD.BTN_WHITE if bool(d["enabled"]) \
			else Color("#aaaab4")
		UiTheme.draw_text_centered(self, font, str(d["label"]),
			int(d["font_size"]), txt_col, rect.get_center(), false)
