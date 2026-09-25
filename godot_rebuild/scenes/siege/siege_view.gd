extends "res://scenes/combat/minion_view.gd"

const Siege = preload("res://scripts/combat/siege_battle.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")


func _draw() -> void:
	super._draw()
	if session == null:
		return
	var world := session.world as Siege
	for structure in world.structures:
		_draw_structure(structure)
	for shot in world.projectiles:
		if shot.active:
			var color := Color("c0f3dc") if shot.team == 0 else Color("ffd1af")
			draw_circle(shot.position, 4, color)


func _draw_base(_point: Vector2, _color: Color) -> void:
	# The siege uses real structure states rather than the minion lab's decorative bases.
	pass


func _draw_structure(structure: Structure) -> void:
	var point := structure.position
	var data := structure.settings()
	var radius := data.radius_px
	var color := Color("73cbbb") if structure.team == 0 else Color("d78579")
	if structure.id == session.selected_id:
		draw_arc(point, data.attack_range_px, 0, TAU, 90, Color(color, 0.4), 1.5, true)
		draw_arc(point, radius + 8, 0, TAU, 40, Color("f4d491"), 2, true)
	draw_circle(point + Vector2(0, 4), radius, Color("08171c"))
	draw_rect(
		Rect2(point - Vector2(radius * 0.65, radius), Vector2(radius * 1.3, radius * 1.5)),
		color.darkened(0.4)
	)
	for offset in [-1, 0, 1]:
		draw_rect(
			Rect2(point + Vector2(offset * radius * 0.5 - 4, -radius - 8), Vector2(8, 14)), color
		)
	var width := radius * 2
	var health := structure.hp / data.max_hp
	var shield := structure.shield / maxf(1, data.shield_capacity)
	draw_rect(Rect2(point + Vector2(-radius, -radius - 22), Vector2(width, 5)), Color("08171c"))
	draw_rect(Rect2(point + Vector2(-radius, -radius - 22), Vector2(width * health, 5)), color)
	if structure.shield_active:
		draw_rect(Rect2(point + Vector2(-radius, -radius - 15), Vector2(width, 3)), Color("08171c"))
		draw_rect(
			Rect2(point + Vector2(-radius, -radius - 15), Vector2(width * shield, 3)),
			Color("92c7ff")
		)
