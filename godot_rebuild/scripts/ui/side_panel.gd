extends Control
## Layer 9as: the wide-screen RIGHT PANEL Control (`mobile/sidepanel.py`
## `SidePanel.draw` + `platform_utils._gambar_panel_samping`).
##
## The pure layout lives in `side_panel_layout.gd`; this node owns the stone
## backdrop, the 250 ms refresh cadence (the source rebuilds its text buffer
## four times a second, immediately on a state change or while a button
## press animation runs), the font measure and the touch routing. It only
## exists on screens with >= 120 px left of the 1280 px arena.

signal pause_requested
signal tactical_down(action: String)
signal tactical_up(action: String)

const Layout = preload("res://scripts/ui/side_panel_layout.gd")

const STONE_BASE := Color8(16, 14, 24)
const STONE_DARK := Color8(26, 23, 38)
const STONE := Color8(34, 30, 48)
const STONE_LINE := Color8(58, 50, 78)
const STONE_GOLD := Color8(150, 120, 60)
const BRICK_H := 34
const PRESS_DECAY := 0.12
const BUTTON_FILL := Color8(30, 27, 44)

var panel := Rect2i()
var snapshot: Dictionary = {}
var layout: Dictionary = {}
var press: Dictionary = {}
var popup_open := false
var _built_at := -1
var _state_key := ""
var _held_action := ""
var _bricks: Array = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE
	visible = false


## `platform_utils.create_display`: called with the full logical width.
func configure(full_width: int) -> void:
	var next := Layout.panel_rect(full_width)
	if next == panel and (visible == (panel.size.x > 0)):
		return
	panel = next
	visible = panel.size.x > 0
	position = Vector2(panel.position)
	size = Vector2(panel.size)
	layout = {}
	_built_at = -1
	_bricks = _build_bricks()
	queue_redraw()


func is_active() -> bool:
	return panel.size.x > 0


## `SidePanel.blocks`: screen point belongs to the panel.
func blocks(screen_pos: Vector2) -> bool:
	return is_active() and Layout.blocks(panel, Vector2i(screen_pos))


## Feed the per-frame game snapshot; rebuilds the draw list on the source
## cadence (`JEDA_SEGAR_MS`, state change, button animation).
func update_snapshot(next: Dictionary, now_ms: int = Time.get_ticks_msec()) -> void:
	if not is_active():
		return
	snapshot = next
	popup_open = bool(next.get("popup_open", false))
	if not Layout.in_gameplay(String(next.get("state", ""))):
		# `_bersihkan_panel`: outside gameplay everything is hidden.
		if not layout.is_empty() or not press.is_empty():
			layout = {}
			press = {}
			_built_at = -1
			queue_redraw()
		_state_key = String(next.get("state", ""))
		return
	var animating := false
	for value in press.values():
		if float(value) > 0.0:
			animating = true
	var state_key := String(next.get("state", ""))
	var need := layout.is_empty() or now_ms - _built_at >= Layout.REFRESH_MS or animating
	if not need and state_key != _state_key:
		need = true
	_state_key = state_key
	if not need:
		return
	var build_input := snapshot.duplicate()
	build_input["press"] = press.duplicate()
	layout = Layout.build(build_input, panel, _measure)
	for key in press.keys():
		press[key] = maxf(0.0, float(press[key]) - PRESS_DECAY)
	_built_at = now_ms
	queue_redraw()


func _measure(text: String, font_size: int) -> int:
	var font := get_theme_default_font()
	if font == null:
		return 7 * text.length()
	return int(ceilf(font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x))


func _build_bricks() -> Array:
	# `_gambar_panel_samping`: staggered brick rows clipped to the panel, the
	# shade chosen by (row + screen x) % 3, drawn once per layout.
	var bricks: Array = []
	if not is_active():
		return bricks
	var bw := maxi(28, panel.size.x / 4)
	var row := 0
	var y := -BRICK_H
	while y < panel.size.y + BRICK_H:
		var shift := (bw / 2) if (row % 2 == 1) else 0
		var x := panel.position.x - bw
		while x < panel.end.x + bw:
			var brick := Rect2i(x + shift + 1, y + 1, bw - 2, BRICK_H - 2).intersection(panel)
			if brick.size.x > 0 and brick.size.y > 0:
				var dark := (row + x) % 3 == 0
				(
					bricks
					. append(
						{
							"rect": Rect2i(brick.position - panel.position, brick.size),
							"color": STONE_DARK if dark else STONE,
						}
					)
				)
			x += bw
		y += BRICK_H
		row += 1
	return bricks


func _draw() -> void:
	if not is_active():
		return
	draw_rect(Rect2(Vector2.ZERO, Vector2(panel.size)), STONE_BASE)
	for brick in _bricks:
		draw_rect(Rect2(brick["rect"]), brick["color"])
		draw_rect(Rect2(brick["rect"]), STONE_LINE, false, 1.0)
	for index in range(20):
		var a := 1.0 - float(index) / 20.0
		var shade := Color8(int(16 * a), int(14 * a), int(24 * a))
		draw_line(Vector2(index + 0.5, 0), Vector2(index + 0.5, panel.size.y), shade, 1.0)
	draw_line(Vector2(1.5, 0), Vector2(1.5, panel.size.y), STONE_GOLD, 2.0)
	if layout.is_empty():
		return
	_draw_pause_button()
	for entry in layout["rects"]:
		_round_rect(entry["rect"], entry["color"], int(entry["width"]), int(entry["radius"]))
	for entry in layout["circles"]:
		draw_circle(Vector2(entry["center"]), float(entry["radius"]), entry["color"])
	var font := get_theme_default_font()
	if font == null:
		return
	for entry in layout["texts"]:
		var font_size := int(entry["size"])
		var pos: Vector2i = entry["pos"]
		var ascent := font.get_ascent(font_size)
		draw_string(
			font,
			Vector2(pos.x, pos.y + ascent),
			String(entry["text"]),
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			font_size,
			entry["color"]
		)


func _draw_pause_button() -> void:
	var button: Dictionary = layout["buttons"].get("pause", {})
	if button.is_empty() or not bool(button["visible"]):
		return
	var rect: Rect2i = button["rect"]
	var local := Rect2i(rect.position - panel.position, rect.size)
	var fill := BUTTON_FILL
	var anim := float(press.get("pause", 0.0))
	if anim > 0.0:
		var k := int(30.0 * anim)
		fill = Color8(30 + k, 27 + k, 44 + k)
	_round_rect(local, fill, 0, 10)
	_round_rect(local, Layout.EMAS, 2, 10)
	# Two bars 7x24 with a 7 px gap, like the source icon.
	var cx := local.position.x + local.size.x / 2
	var cy := local.position.y + local.size.y / 2
	for dx in [-(7 / 2) - 7, 7 / 2]:
		_round_rect(Rect2i(cx + dx, cy - 12, 7, 24), Layout.EMAS, 0, 2)


func _round_rect(rect: Rect2i, color: Color, width: int, radius: int) -> void:
	if rect.size.x <= 0 or rect.size.y <= 0:
		return
	var style := StyleBoxFlat.new()
	if width <= 0:
		style.bg_color = color
	else:
		style.bg_color = Color(0, 0, 0, 0)
		style.draw_center = false
		style.set_border_width_all(width)
		style.border_color = color
	style.set_corner_radius_all(radius)
	draw_style_box(style, Rect2(rect))


func _gui_input(event: InputEvent) -> void:
	var pressed := false
	var released := false
	var local := Vector2.ZERO
	if event is InputEventScreenTouch:
		pressed = event.pressed
		released = not event.pressed
		local = event.position
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		pressed = event.pressed
		released = not event.pressed
		local = event.position
	else:
		return
	accept_event()
	if pressed:
		_press_at(Vector2i(local) + panel.position)
	elif released and not _held_action.is_empty():
		var action := _held_action
		_held_action = ""
		tactical_up.emit(action)


## `SidePanel.hit_test` + `main.py` dispatch: pause toggles, tactical
## commands start on press and end on release.
func _press_at(screen_pos: Vector2i) -> String:
	if layout.is_empty():
		return ""
	var action := Layout.hit_test(layout["buttons"], screen_pos, popup_open)
	if action.is_empty():
		return ""
	press[action] = 1.0
	_built_at = -1
	if action == "pause":
		pause_requested.emit()
	else:
		_held_action = action
		tactical_down.emit(action)
	return action
