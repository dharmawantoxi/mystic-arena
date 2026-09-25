extends "res://scenes/siege/siege_view.gd"

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")


func _draw() -> void:
	super._draw()
	if session == null:
		return
	var world := session.world as Prototype
	var match_session := session as PrototypeSession
	for slot in world.slots:
		if slot.structure_id != -1:
			continue
		var color := Color("73cbbb") if slot.team == 0 else Color("d78579")
		var selected := slot.id == match_session.selected_slot_id
		if selected:
			draw_circle(slot.position, 23, Color(color, 0.12))
			draw_arc(
				slot.position,
				world.ARCHER.attack_range_px,
				0,
				TAU,
				90,
				Color(color, 0.3),
				1.5,
				true
			)
		draw_arc(slot.position, 19, 0, TAU, 36, Color(color, 0.95 if selected else 0.5), 2, true)
		draw_line(slot.position - Vector2(6, 0), slot.position + Vector2(6, 0), color, 2, true)
		draw_line(slot.position - Vector2(0, 6), slot.position + Vector2(0, 6), color, 2, true)
