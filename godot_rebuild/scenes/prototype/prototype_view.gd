extends "res://scenes/siege/siege_view.gd"

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")


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


func _draw_unit(unit: UnitState) -> void:
	if not unit.is_hero:
		super._draw_unit(unit)
		return
	var hero := unit as HeroState
	var point := hero.position
	var radius := hero.settings().radius_px
	var color := Color("73cbbb") if hero.team == 0 else Color("d78579")
	if hero.id == session.selected_id:
		draw_arc(point, radius + 12, 0, TAU, 36, Color("f4d491"), 2, true)
	draw_circle(point + Vector2(0, 4), radius + 3, Color("071518"))
	draw_colored_polygon(
		PackedVector2Array(
			[
				point + Vector2(0, -radius - 4),
				point + Vector2(radius + 4, 0),
				point + Vector2(0, radius + 4),
				point + Vector2(-radius - 4, 0)
			]
		),
		color.darkened(0.15)
	)
	draw_line(point, point + Vector2(hero.facing * (radius + 10), 0), color, 3, true)
	var health := float(hero.hp) / maxf(1.0, hero.max_hp)
	draw_rect(Rect2(point + Vector2(-17, -radius - 14), Vector2(34, 4)), Color("071518"))
	draw_rect(Rect2(point + Vector2(-17, -radius - 14), Vector2(34 * health, 4)), color)
