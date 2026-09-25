extends Node2D
## Decorative placeholder. Lanes below are NOT production navigation data.

const Simulation = preload("res://scripts/simulation/sandbox_simulation.gd")
var simulation: Simulation


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("0b191e"))
	for x in range(40, 1280, 40):
		draw_line(Vector2(x, 100), Vector2(x, 620), Color("142a2e"), 1.0)
	for y in range(100, 621, 40):
		draw_line(Vector2(40, y), Vector2(1240, y), Color("142a2e"), 1.0)
	var lanes: Array[PackedVector2Array] = [
		PackedVector2Array(
			[Vector2(120, 550), Vector2(220, 240), Vector2(430, 180), Vector2(1150, 180)]
		),
		PackedVector2Array(
			[Vector2(120, 550), Vector2(460, 430), Vector2(780, 320), Vector2(1150, 180)]
		),
		PackedVector2Array(
			[Vector2(120, 550), Vector2(870, 550), Vector2(1070, 490), Vector2(1150, 180)]
		)
	]
	for lane in lanes:
		draw_polyline(lane, Color("263c3a"), 32.0, true)
		draw_polyline(lane, Color("3a5147"), 2.0, true)
	for point in [
		Vector2(350, 262),
		Vector2(535, 365),
		Vector2(790, 495),
		Vector2(765, 215),
		Vector2(895, 338),
		Vector2(980, 505)
	]:
		draw_arc(point, 19, 0, TAU, 32, Color("658077"), 1.5, true)
		draw_line(point - Vector2(5, 0), point + Vector2(5, 0), Color("658077"), 1.5)
		draw_line(point - Vector2(0, 5), point + Vector2(0, 5), Color("658077"), 1.5)
	_draw_base(Vector2(120, 550), Color("73cbbb"))
	_draw_base(Vector2(1150, 180), Color("d78579"))
	if not is_instance_valid(simulation):
		return
	var point := simulation.probe_position
	if simulation.has_move_target:
		draw_line(point, simulation.move_target, Color("698d7b"), 1.0, true)
		draw_arc(simulation.move_target, 10, 0, TAU, 24, Color("d3b875"), 2.0, true)
	if simulation.is_selected:
		draw_arc(point, 26, 0, TAU, 40, Color("d3b875"), 2.0, true)
	draw_circle(point + Vector2(0, 8), 16, Color("081215"))
	draw_colored_polygon(
		PackedVector2Array(
			[
				point + Vector2(0, -18),
				point + Vector2(13, 10),
				point + Vector2(0, 5),
				point + Vector2(-13, 10)
			]
		),
		Color("85e3ce")
	)
	draw_circle(point, 3, Color("e1fff4"))


func _draw_base(point: Vector2, color: Color) -> void:
	draw_circle(point, 37, Color("172c32"))
	draw_arc(point, 37, 0, TAU, 48, color, 2.0, true)
	draw_rect(Rect2(point - Vector2(16, 18), Vector2(32, 36)), color.darkened(0.35))
	for offset in [-15, 0, 15]:
		draw_rect(Rect2(point + Vector2(offset - 4, -25), Vector2(8, 15)), color)
