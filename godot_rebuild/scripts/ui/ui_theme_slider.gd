extends Control
## Source `ui_theme.slider()` track, gold gradient fill and radial hover glow.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const UiSkin = preload("res://scripts/ui/ui_skin.gd")
static var _fill_texture: GradientTexture2D

var value := 0.0:
	set(next_value):
		value = clampf(next_value, 0.0, 1.0)
		queue_redraw()
var _knob_hover := false


func _ready() -> void:
	custom_minimum_size = Vector2(80.0, 24.0)
	mouse_filter = Control.MOUSE_FILTER_PASS
	mouse_entered.connect(_on_mouse_entered)
	mouse_exited.connect(_on_mouse_exited)
	resized.connect(queue_redraw)


func _draw() -> void:
	if size.x <= 0.0 or size.y <= 0.0:
		return
	var track_width := size.x
	var track_height := 8.0
	var track_y := (size.y - track_height) * 0.5
	var track_rect := Rect2(0.0, track_y, track_width, track_height)
	var track := StyleBoxFlat.new()
	track.bg_color = Color8(34, 38, 58)
	track.set_corner_radius_all(4)
	draw_style_box(track, track_rect)

	var fill_width := int(track_width * clampf(value, 0.0, 1.0))
	if fill_width > 4:
		draw_texture_rect(
			_fill_gradient(), Rect2(0.0, track_y, float(fill_width), track_height), false
		)
	var border := StyleBoxFlat.new()
	border.draw_center = false
	border.border_color = Color8(120, 110, 86)
	border.set_border_width_all(1)
	border.set_corner_radius_all(4)
	draw_style_box(border, track_rect)

	var knob_x := float(fill_width)
	var knob_y := track_y + track_height * 0.5
	if _knob_hover:
		var glow := UiSkin.slider_glow_texture()
		if glow != null:
			draw_texture(glow, Vector2(knob_x - 18.0, knob_y - 18.0))
	draw_circle(Vector2(knob_x, knob_y), 11.0, Color8(12, 14, 24))
	draw_circle(Vector2(knob_x, knob_y), 8.0, Color8(245, 248, 255))
	draw_arc(Vector2(knob_x, knob_y), 8.0, 0.0, TAU, 48, UI_THEME.GOLD, 2.0, true)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_update_knob_hover(event.position)


func _on_mouse_entered() -> void:
	_update_knob_hover(get_local_mouse_position())


func _on_mouse_exited() -> void:
	_knob_hover = false
	queue_redraw()


func _update_knob_hover(pointer: Vector2) -> void:
	var track_y := (size.y - 8.0) * 0.5
	var knob := Vector2(float(int(size.x * value)), track_y + 4.0)
	var next_hover := pointer.distance_to(knob) <= 11.0
	if next_hover != _knob_hover:
		_knob_hover = next_hover
		queue_redraw()


static func _fill_gradient() -> GradientTexture2D:
	if _fill_texture == null:
		var gradient := Gradient.new()
		gradient.colors = [UI_THEME.GOLD_BRIGHT, Color8(196, 138, 40)]
		var texture := GradientTexture2D.new()
		texture.width = 1
		texture.height = 8
		texture.fill_from = Vector2(0.0, 0.0)
		texture.fill_to = Vector2(0.0, 1.0)
		texture.gradient = gradient
		_fill_texture = texture
	return _fill_texture
