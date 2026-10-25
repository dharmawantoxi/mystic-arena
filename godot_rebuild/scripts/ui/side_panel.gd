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
signal overlay_pressed(screen_position: Vector2i, button_index: int)

const Layout = preload("res://scripts/ui/side_panel_layout.gd")
const BuildPopupLayout = preload("res://scripts/ui/build_popup_layout.gd")
const HeroPanelLayout = preload("res://scripts/ui/hero_panel_layout.gd")
const HeroPanelFont = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const BuildPopupBodyFont = preload("res://assets/fonts/Barlow-Regular.ttf")
const BuildPopupTitleFont = preload("res://assets/fonts/Cinzel.ttf")

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
var _hero_panel_round_box := StyleBoxFlat.new()
var _hero_panel_shadow_box := StyleBoxFlat.new()
var _hero_panel_radial_textures: Dictionary = {}


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
	var previous_hero_state: Dictionary = snapshot.get("hero_panel_state", {})
	var next_hero_state: Dictionary = next.get("hero_panel_state", {})
	var previous_build_state: Dictionary = snapshot.get("build_popup_state", {})
	var next_build_state: Dictionary = next.get("build_popup_state", {})
	var overlay_active := (
		not previous_hero_state.is_empty()
		or not next_hero_state.is_empty()
		or not previous_build_state.is_empty()
		or not next_build_state.is_empty()
	)
	snapshot = next
	if overlay_active:
		queue_redraw()
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
		_draw_build_popup_overlay()
		_draw_hero_panel_overlay()
		return
	_draw_pause_button()
	for entry in layout["rects"]:
		_round_rect(entry["rect"], entry["color"], int(entry["width"]), int(entry["radius"]))
	for entry in layout["circles"]:
		draw_circle(Vector2(entry["center"]), float(entry["radius"]), entry["color"])
	var font := get_theme_default_font()
	if font == null:
		_draw_build_popup_overlay()
		_draw_hero_panel_overlay()
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
	_draw_build_popup_overlay()
	_draw_hero_panel_overlay()


func _draw_build_popup_overlay() -> void:
	var state: Dictionary = snapshot.get("build_popup_state", {})
	if (
		state.is_empty()
		or not state.has("panel_pos")
		or String(snapshot.get("state", "")) != "playing"
	):
		return
	var panel_pos: Array = state["panel_pos"]
	if panel_pos.size() < 2 or int(panel_pos[0]) < panel.position.x:
		return
	var mouse := Vector2i(get_viewport().get_mouse_position())
	var draw_state := state.duplicate(true)
	draw_state["mouse"] = mouse
	var metrics := Callable(self, "_measure_build_popup")
	var ellipsis := "..."
	if BuildPopupBodyFont.has_char(0x2026):
		ellipsis = "…"
	var ops := BuildPopupLayout.ops(
		draw_state, metrics, bool(draw_state.get("cheap_alpha", true)), ellipsis
	)
	draw_set_transform(-Vector2(panel.position), 0.0, Vector2.ONE)
	for op in ops:
		var kind := String(op.get("kind", ""))
		if kind == "section":
			continue
		if kind == "outline_text":
			_draw_build_popup_title(op)
		elif kind == "text":
			_draw_build_popup_text(op)
		else:
			_draw_hero_panel_op(op)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _measure_build_popup(text: String, font_size: int) -> Vector2i:
	var font: Font = BuildPopupTitleFont
	if font_size == 17:
		font = BuildPopupBodyFont
	elif font_size != 30:
		font = HeroPanelFont
	var measured := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	return Vector2i(int(measured.x), font_size)


func _draw_build_popup_text(op: Dictionary) -> void:
	var pos: Array = op.get("pos", [0, 0])
	var size := int(op.get("size", 16))
	var text := String(op.get("text", ""))
	var style := String(op.get("style", ""))
	var font: Font = BuildPopupBodyFont if style == "body_medium" else HeroPanelFont
	draw_string(
		font,
		Vector2(float(pos[0]), float(pos[1]) + font.get_ascent(size)),
		text,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		size,
		_hero_panel_op_color(op)
	)


func _draw_build_popup_title(op: Dictionary) -> void:
	var pos: Array = op.get("pos", [0, 0])
	var size := int(op.get("size", 30))
	var width := float(op.get("width", 2))
	var text := String(op.get("text", ""))
	var base := Vector2(float(pos[0]), float(pos[1]) + BuildPopupTitleFont.get_ascent(size))
	var ink: Array = op.get("outline", [8, 9, 18])
	var outline := Color8(int(ink[0]), int(ink[1]), int(ink[2]))
	var offsets := [
		Vector2(-width, 0),
		Vector2(width, 0),
		Vector2(0, -width),
		Vector2(0, width),
		Vector2(-width, -width),
		Vector2(width, width),
		Vector2(-width, width),
		Vector2(width, -width),
	]
	for offset in offsets:
		draw_string(
			BuildPopupTitleFont, base + offset, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, outline
		)
	var top: Array = op.get("top", [255, 255, 255])
	var bottom: Array = op.get("bottom", [255, 255, 255])
	var body := Color8(
		int((int(top[0]) + int(bottom[0])) * 0.5),
		int((int(top[1]) + int(bottom[1])) * 0.5),
		int((int(top[2]) + int(bottom[2])) * 0.5)
	)
	draw_string(BuildPopupTitleFont, base, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, body)


func _draw_hero_panel_overlay() -> void:
	var state: Dictionary = snapshot.get("hero_panel_state", {})
	if state.is_empty() or not state.has("panel_pos"):
		return
	var panel_pos: Array = state["panel_pos"]
	if panel_pos.size() < 2 or int(panel_pos[0]) < panel.position.x:
		return
	var mouse := Vector2i(get_viewport().get_mouse_position())
	var draw_state := state.duplicate(true)
	draw_state["mouse"] = mouse
	var metrics := Callable(self, "_measure_hero_panel")
	var ops := HeroPanelLayout.ops(
		draw_state, metrics, bool(draw_state.get("cheap_alpha", true)), Time.get_ticks_msec()
	)
	draw_set_transform(-Vector2(panel.position), 0.0, Vector2.ONE)
	for op in ops:
		_draw_hero_panel_op(op)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _measure_hero_panel(text: String, font_size: int) -> Vector2i:
	var measured := HeroPanelFont.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	return Vector2i(int(measured.x), font_size)


func _draw_hero_panel_op(op: Dictionary) -> void:
	var kind := String(op.get("kind", ""))
	if kind == "radial":
		_draw_hero_panel_radial(op)
		return
	if kind == "shadow":
		var shadow_box: Array = op.get("rect", [0, 0, 0, 0])
		_hero_panel_shadow_box.bg_color = Color(
			0.0, 0.0, 0.0, float(op.get("alpha", 110)) / 255.0 * 0.5
		)
		_hero_panel_shadow_box.set_corner_radius_all(int(op.get("radius", 12)) + 4)
		_hero_panel_shadow_box.shadow_color = Color(0.0, 0.0, 0.0, 0.25)
		_hero_panel_shadow_box.shadow_size = 4
		draw_style_box(
			_hero_panel_shadow_box,
			Rect2(
				float(shadow_box[0]),
				float(shadow_box[1]),
				float(shadow_box[2]),
				float(shadow_box[3])
			)
		)
		return
	if kind == "vgrad":
		_draw_hero_panel_vgrad(op)
		return
	if kind == "text":
		var pos: Array = op.get("pos", [0, 0])
		var font_size := int(op.get("size", 16))
		draw_string(
			HeroPanelFont,
			Vector2(float(pos[0]), float(pos[1]) + HeroPanelFont.get_ascent(font_size)),
			String(op.get("text", "")),
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			font_size,
			_hero_panel_op_color(op)
		)
		return
	if kind == "line":
		var a: Array = op.get("a", [0, 0])
		var b: Array = op.get("b", [0, 0])
		draw_line(
			Vector2(float(a[0]), float(a[1])),
			Vector2(float(b[0]), float(b[1])),
			_hero_panel_op_color(op),
			float(op.get("width", 1))
		)
		return
	if kind == "circle":
		var center: Array = op.get("center", [0, 0])
		var radius := float(op.get("radius", 1))
		var circle_width := int(op.get("width", 0))
		var circle_color := _hero_panel_op_color(op)
		if circle_width > 0:
			draw_arc(
				Vector2(float(center[0]), float(center[1])),
				radius - float(circle_width) * 0.5,
				0.0,
				TAU,
				48,
				circle_color,
				float(circle_width),
				true
			)
		else:
			draw_circle(Vector2(float(center[0]), float(center[1])), radius, circle_color)
	elif kind == "polygon":
		var points := PackedVector2Array()
		for point in op.get("points", []):
			points.append(Vector2(float(point[0]), float(point[1])))
		if points.size() >= 3:
			draw_colored_polygon(points, _hero_panel_op_color(op))
	elif kind == "fill" or kind == "rect":
		var box: Array = op.get("rect", [0, 0, 0, 0])
		var rect := Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
		var rect_color := _hero_panel_op_color(op)
		if kind == "fill":
			draw_rect(rect, rect_color)
		else:
			var rect_width := int(op.get("width", 0))
			_hero_panel_round_box.anti_aliasing = false
			_hero_panel_round_box.set_corner_radius_all(int(op.get("radius", 0)))
			_hero_panel_round_box.draw_center = rect_width == 0
			_hero_panel_round_box.bg_color = rect_color
			_hero_panel_round_box.set_border_width_all(rect_width)
			_hero_panel_round_box.border_color = rect_color
			draw_style_box(_hero_panel_round_box, rect)


func _hero_panel_op_color(op: Dictionary) -> Color:
	var rgba: Array = op.get("color", [255, 255, 255, 255])
	var color_alpha := float(rgba[3]) if rgba.size() > 3 else 255.0
	var alpha := color_alpha * float(op.get("mult", 255)) / 65025.0
	return Color(float(rgba[0]) / 255.0, float(rgba[1]) / 255.0, float(rgba[2]) / 255.0, alpha)


func _draw_hero_panel_radial(op: Dictionary) -> void:
	var box: Array = op.get("rect", [0, 0, 8, 8])
	var rgb: Array = op.get("color", [255, 255, 255])
	var alpha := float(op.get("alpha", 0)) / 255.0
	var key := "%s/%d" % [str(rgb), int(op.get("alpha", 0))]
	if not _hero_panel_radial_textures.has(key):
		var gradient := Gradient.new()
		var offsets := PackedFloat32Array()
		var colors := PackedColorArray()
		for step in range(5):
			var distance := float(step) / 4.0
			offsets.append(distance)
			var color := Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
			color.a = alpha * pow(1.0 - distance, 2.0)
			colors.append(color)
		gradient.offsets = offsets
		gradient.colors = colors
		var texture := GradientTexture2D.new()
		texture.gradient = gradient
		texture.fill = GradientTexture2D.FILL_RADIAL
		texture.fill_from = Vector2(0.5, 0.5)
		texture.fill_to = Vector2(1.0, 0.5)
		texture.width = 128
		texture.height = 128
		_hero_panel_radial_textures[key] = texture
	var width := float(box[2])
	var height := float(box[3])
	var scale_to_texture := 128.0 / sqrt(width * width + height * height)
	var region := Rect2(
		64.0 - width * 0.5 * scale_to_texture,
		64.0 - height * 0.5 * scale_to_texture,
		width * scale_to_texture,
		height * scale_to_texture
	)
	draw_texture_rect_region(
		_hero_panel_radial_textures[key], Rect2(float(box[0]), float(box[1]), width, height), region
	)


func _draw_hero_panel_vgrad(op: Dictionary) -> void:
	var box: Array = op.get("rect", [0, 0, 0, 0])
	var top: Array = op.get("top", [0, 0, 0])
	var bottom: Array = op.get("bottom", [0, 0, 0])
	var width := float(box[2])
	var height := int(box[3])
	var radius := float(op.get("radius", 0))
	for row in range(height):
		var t := float(row) / float(maxi(1, height - 1))
		var color := Color8(
			int(top[0] + (bottom[0] - top[0]) * t),
			int(top[1] + (bottom[1] - top[1]) * t),
			int(top[2] + (bottom[2] - top[2]) * t)
		)
		var inset := 0.0
		var from_edge := minf(float(row) + 0.5, float(height) - float(row) - 0.5)
		if radius > 0.0 and from_edge < radius:
			var rise := radius - from_edge
			inset = roundf(radius - sqrt(maxf(0.0, radius * radius - rise * rise)))
		if width - inset * 2.0 > 0.0:
			draw_rect(
				Rect2(float(box[0]) + inset, float(box[1]) + row, width - inset * 2.0, 1.0), color
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
	var button_index := MOUSE_BUTTON_LEFT
	if event is InputEventScreenTouch:
		pressed = event.pressed
		released = not event.pressed
		local = event.position
	elif event is InputEventMouseButton:
		var mouse := event as InputEventMouseButton
		if mouse.button_index not in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			return
		button_index = mouse.button_index
		if button_index == MOUSE_BUTTON_RIGHT and not popup_open:
			return
		pressed = mouse.pressed
		released = not mouse.pressed
		local = mouse.position
	else:
		return
	accept_event()
	if pressed:
		var screen_position := Vector2i(local) + panel.position
		var action := _press_at(screen_position) if button_index == MOUSE_BUTTON_LEFT else ""
		if action.is_empty() and popup_open:
			overlay_pressed.emit(screen_position, button_index)
	elif released and button_index == MOUSE_BUTTON_LEFT and not _held_action.is_empty():
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
