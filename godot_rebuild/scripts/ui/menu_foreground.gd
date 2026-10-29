extends Control
## Source main-menu ornaments: the subtitle plate, pulse glow, and gold flourish.

const PANEL := Color8(21, 26, 48)
const EDGE_GOLD := Color8(176, 144, 82)
const GOLD := Color8(255, 205, 85)
const GOLD_BRIGHT := Color8(255, 233, 158)

var animation_time := 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func _process(delta: float) -> void:
	animation_time += maxf(delta, 0.0) * 60.0
	queue_redraw()


func _draw() -> void:
	var scale_factor := minf(size.x / 1280.0, size.y / 720.0)
	if scale_factor <= 0.0:
		return
	var origin := (size - Vector2(1280.0, 720.0) * scale_factor) * 0.5
	draw_set_transform(origin, 0.0, Vector2(scale_factor, scale_factor))

	var pulse := 0.5 + 0.5 * sin(animation_time * 0.02)
	var glow_alpha := 0.025 + pulse * 0.025
	for index in range(12, 0, -1):
		var radius := 34.0 + float(index) * 14.0
		draw_circle(
			Vector2(640.0, 124.0), radius, Color(1.0, 0.78, 0.30, glow_alpha / float(index))
		)

	var plate := Rect2(470.0, 190.0, 340.0, 48.0)
	draw_rect(plate, PANEL, true)
	draw_rect(plate, EDGE_GOLD, false, 1.0, true)
	_draw_corner_ticks(plate)

	var flourish_y := 286.0
	draw_line(Vector2(420.0, flourish_y), Vector2(622.0, flourish_y), EDGE_GOLD, 2.0, true)
	draw_line(Vector2(658.0, flourish_y), Vector2(860.0, flourish_y), EDGE_GOLD, 2.0, true)
	draw_colored_polygon(
		PackedVector2Array(
			[
				Vector2(632.0, flourish_y),
				Vector2(640.0, flourish_y - 7.0),
				Vector2(648.0, flourish_y),
				Vector2(640.0, flourish_y + 7.0),
			]
		),
		GOLD
	)
	draw_circle(Vector2(410.0, flourish_y), 3.0, GOLD_BRIGHT)
	draw_circle(Vector2(870.0, flourish_y), 3.0, GOLD_BRIGHT)
	draw_set_transform(Vector2.ZERO)


func _draw_corner_ticks(rect: Rect2) -> void:
	var inset := 5.0
	var length := 12.0
	for corner in [
		Vector2(rect.position.x + inset, rect.position.y + inset),
		Vector2(rect.end.x - inset, rect.position.y + inset),
		Vector2(rect.position.x + inset, rect.end.y - inset),
		Vector2(rect.end.x - inset, rect.end.y - inset),
	]:
		var direction_x := 1.0 if corner.x < rect.get_center().x else -1.0
		var direction_y := 1.0 if corner.y < rect.get_center().y else -1.0
		draw_line(corner, corner + Vector2(direction_x * length, 0.0), GOLD, 2.0, true)
		draw_line(corner, corner + Vector2(0.0, direction_y * length), GOLD, 2.0, true)
