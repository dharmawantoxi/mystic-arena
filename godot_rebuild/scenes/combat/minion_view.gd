extends Node2D
## Read-only presentation: disabling this entire node must not change battle results.

const Session = preload("res://scripts/simulation/combat_session.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Layout = preload("res://scripts/data/lane_layout.gd")
var session: Session
# Empty in the laboratory/siege. Prototype supplies source terrain colors.
var terrain_palette: Dictionary = {}
var terrain_river: PackedVector2Array = PackedVector2Array()
var river_texture: Texture2D
var lane_texture: Texture2D
var wall_texture: Texture2D


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if terrain_palette.is_empty():
		draw_rect(Rect2(0, 0, 1280, 720), Color("10252a"))
	else:
		# The map is still procedural: only source terrain palette has moved.
		draw_rect(Rect2(0, 0, 640, 720), terrain_palette["radiant_grass_1"])
		draw_rect(Rect2(640, 0, 640, 720), terrain_palette["dire_earth_1"])
		draw_rect(Rect2(600, 0, 80, 720), terrain_palette["transition_1"])
	for x in range(0, 1280, 40):
		var grid := Color("172d31")
		if not terrain_palette.is_empty():
			grid = (
				terrain_palette["radiant_grass_2"] if x < 640 else terrain_palette["dire_earth_2"]
			)
			grid = grid.darkened(0.12)
		draw_line(Vector2(x, 0), Vector2(x, 720), grid)
	for y in range(0, 720, 40):
		if terrain_palette.is_empty():
			draw_line(Vector2(0, y), Vector2(1280, y), Color("172d31"))
		else:
			draw_line(
				Vector2(0, y), Vector2(640, y), terrain_palette["radiant_grass_2"].darkened(0.12)
			)
			draw_line(
				Vector2(640, y), Vector2(1280, y), terrain_palette["dire_earth_2"].darkened(0.12)
			)
	if session == null:
		return
	if river_texture != null:
		draw_texture(river_texture, Vector2.ZERO)
	elif terrain_river.size() > 1 and not terrain_palette.is_empty():
		# Fallback for an unavailable cached texture, not the primary path.
		draw_polyline(terrain_river, terrain_palette["river_mid"], 44, true)
		draw_polyline(terrain_river, terrain_palette["river_deep"], 32, true)
	if lane_texture != null:
		draw_texture(lane_texture, Vector2.ZERO)
	else:
		for path in session.world.paths:
			var stone := Color("314440")
			var edge := Color("587160")
			if not terrain_palette.is_empty():
				stone = terrain_palette["path_stone_1"]
				edge = terrain_palette["path_stone_3"]
			draw_polyline(path, stone, 32, true)
			draw_polyline(path, edge, 1.5, true)
	if wall_texture != null:
		draw_texture(wall_texture, Vector2.ZERO)
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
