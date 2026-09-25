extends Control
## New, deterministic decorative artwork. Not a port of a gameplay map.


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func _draw() -> void:
	var scale_factor := size / Vector2(1280, 720)
	draw_set_transform(Vector2.ZERO, 0.0, scale_factor)
	draw_rect(Rect2(0, 0, 1280, 720), Color("0b171e"))
	for index in range(18):
		var x := 470.0 + index * 55.0
		draw_line(Vector2(x, 0), Vector2(x - 280, 720), Color("14272d"), 1.0)
	var center := Vector2(947, 348)
	for radius in [125, 177, 220, 268]:
		draw_arc(center, radius, 0, TAU, 100, Color("29453e"), 1.0, true)
	for index in range(12):
		var angle := index * TAU / 12.0
		var direction := Vector2.from_angle(angle)
		draw_line(center + direction * 211, center + direction * 229, Color("b59e67"), 2, true)
	var diamond := PackedVector2Array(
		[
			center + Vector2(0, -160),
			center + Vector2(124, 0),
			center + Vector2(0, 160),
			center + Vector2(-124, 0),
			center + Vector2(0, -160)
		]
	)
	draw_colored_polygon(diamond.slice(0, 4), Color("122b30"))
	draw_polyline(diamond, Color("bda66f"), 2.0, true)
	# An abstract fortress, deliberately distinct from production castle art.
	for offset in [-62, 0, 62]:
		var height := 106.0 if offset == 0 else 65.0
		draw_rect(Rect2(center.x + offset - 16, center.y - height / 2, 32, height), Color("40756d"))
		draw_line(
			Vector2(center.x + offset - 16, center.y - height / 2),
			Vector2(center.x + offset + 16, center.y - height / 2),
			Color("cfbb83"),
			3
		)
	draw_circle(center + Vector2(0, -81), 6, Color("78d8c2"))
	for index in range(24):
		var point := Vector2(660 + (index * 137) % 590, 90 + (index * 89) % 560)
		draw_circle(point, 1.4, Color("66816e"))
	draw_set_transform(Vector2.ZERO)
