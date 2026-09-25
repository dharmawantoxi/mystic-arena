extends Node2D
## Read-only presentation: disabling this entire node must not change battle results.

const Session = preload("res://scripts/simulation/combat_session.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Layout = preload("res://scripts/data/lane_layout.gd")
var session: Session


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("10252a"))
	for x in range(0, 1280, 40):
		draw_line(Vector2(x, 0), Vector2(x, 720), Color("172d31"))
	for y in range(0, 720, 40):
		draw_line(Vector2(0, y), Vector2(1280, y), Color("172d31"))
	if session == null:
		return
	for path in session.world.paths:
		draw_polyline(path, Color("314440"), 32, true)
		draw_polyline(path, Color("587160"), 1.5, true)
	_draw_base(Layout.BLUE_BASE, Color("73cbbb"))
	_draw_base(Layout.RED_BASE, Color("d78579"))
	for unit in session.world.units:
		_draw_unit(unit)
	for event in session.world.recent_events:
		if event.kind == "hit" and session.world.tick_count - int(event.tick) < 8:
			draw_line(event["from"], event["to"], Color("e7c98a"), 2, true)


func _draw_unit(unit: UnitState) -> void:
	var point := unit.position
	var radius := unit.definition.radius_px
	var color := Color("73cbbb") if unit.team == 0 else Color("d78579")
	if unit.id == session.selected_id:
		draw_arc(point, radius + 9, 0, TAU, 32, Color("f4d491"), 2, true)
	draw_circle(point + Vector2(0, 4), radius + 2, Color("071518"))
	draw_circle(point, radius, color.darkened(0.25))
	draw_arc(point, radius, 0, TAU, 24, color, 2, true)
	draw_line(point, point + Vector2(unit.facing * (radius + 7), 0), color, 3, true)
	var health := float(unit.hp) / unit.definition.max_hp
	draw_rect(Rect2(point + Vector2(-17, -radius - 11), Vector2(34, 4)), Color("071518"))
	draw_rect(Rect2(point + Vector2(-17, -radius - 11), Vector2(34 * health, 4)), color)


func _draw_base(point: Vector2, color: Color) -> void:
	draw_arc(point, 30, 0, TAU, 40, color, 2, true)
	draw_rect(Rect2(point - Vector2(14, 16), Vector2(28, 32)), color.darkened(0.4))
