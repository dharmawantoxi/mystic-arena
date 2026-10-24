extends Node2D
## Read-only presentation: disabling this entire node must not change battle results.

const Session = preload("res://scripts/simulation/combat_session.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Layout = preload("res://scripts/data/lane_layout.gd")
const MinionArt = preload("res://scripts/ui/minion_art.gd")
const MinionAnim = preload("res://scripts/ui/minion_anim.gd")
const MinionCombatFxArt = preload("res://scripts/ui/minion_combat_fx_art.gd")
# Source `apply_hurt_flash` lifts every channel by 90 for 8 ticks; a multiply is the
# closest a baked sprite can get.
const HURT_TINT := Color(1.6, 1.6, 1.6)
var session: Session
# Empty in the laboratory/siege. Prototype supplies source terrain colors.
var terrain_palette: Dictionary = {}
var terrain_river: PackedVector2Array = PackedVector2Array()
var river_texture: Texture2D
var lane_texture: Texture2D
var wall_texture: Texture2D
var terrain_texture: Texture2D
## True when `terrain_texture` is the baked source base (layer 9bj2), which already
## holds the river and the lanes, so neither is painted again over it.
var baked_static_base := false
var minion_anim := MinionAnim.new()
var minion_slash_draws := 0
var minion_death_draws := 0
var _minion_death_animations: Array[Dictionary] = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if terrain_texture != null:
		draw_texture(terrain_texture, Vector2.ZERO)
	else:
		if terrain_palette.is_empty():
			draw_rect(Rect2(0, 0, 1280, 720), Color("10252a"))
		else:
			# Fallback without a cached source texture.
			draw_rect(Rect2(0, 0, 640, 720), terrain_palette["radiant_grass_1"])
			draw_rect(Rect2(640, 0, 640, 720), terrain_palette["dire_earth_1"])
			draw_rect(Rect2(600, 0, 80, 720), terrain_palette["transition_1"])
		for x in range(0, 1280, 40):
			var grid := Color("172d31")
			if not terrain_palette.is_empty():
				grid = (
					terrain_palette["radiant_grass_2"]
					if x < 640
					else terrain_palette["dire_earth_2"]
				)
				grid = grid.darkened(0.12)
			draw_line(Vector2(x, 0), Vector2(x, 720), grid)
		for y in range(0, 720, 40):
			if terrain_palette.is_empty():
				draw_line(Vector2(0, y), Vector2(1280, y), Color("172d31"))
			else:
				draw_line(
					Vector2(0, y),
					Vector2(640, y),
					terrain_palette["radiant_grass_2"].darkened(0.12)
				)
				draw_line(
					Vector2(640, y),
					Vector2(1280, y),
					terrain_palette["dire_earth_2"].darkened(0.12)
				)
	if session == null:
		return
	# Layers 2-3: the baked source base (9bj2) already holds the river and lanes.
	if not baked_static_base:
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
	_draw_map_decor()
	if wall_texture != null:
		draw_texture(wall_texture, Vector2.ZERO)
	_draw_map_dynamic()
	_draw_map_overlay()
	_draw_base(Layout.BLUE_BASE, Color("73cbbb"))
	_draw_base(Layout.RED_BASE, Color("d78579"))
	_draw_structures()
	_minion_death_animations.append_array(
		minion_anim.take_death_snapshots(session.world.recent_events)
	)
	minion_anim.prune(session.world.units)
	for unit in session.world.units:
		_draw_unit(unit)
	_draw_minion_death_animations()
	for event in session.world.recent_events:
		if event.kind == "hit" and session.world.tick_count - int(event.tick) < 8:
			draw_line(event["from"], event["to"], Color("e7c98a"), 2, true)


## Hook for the towers and castles: `Game.draw` paints them before the minions and
## heroes, so units walk over them.
func _draw_structures() -> void:
	pass


## Hook for the source's decoration and shop layers (map layers 4-5): painted over
## the lanes and under the border wall, like `MapRenderer._render_static_map`.
func _draw_map_decor() -> void:
	pass


## Hook for the source DynamicRenderer: after the completed static map and
## before the ambient tint, exactly like `MapRenderer.draw`.
func _draw_map_dynamic() -> void:
	pass


## Hook for the layer the source paints over the finished map, under the units
## (the prototype draws its ambient tint here).
func _draw_map_overlay() -> void:
	pass


func _draw_unit(unit: UnitState) -> void:
	if not unit.is_hero and _draw_minion_sprite(unit):
		return
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


## Layer 9bk: the baked source sprite for a minion, with the live parts the source draws
## outside its sprite cache (slow aura, HP bar). False when the art is unavailable, so
## the plain circle above still draws.
func _draw_minion_sprite(unit: UnitState) -> bool:
	var clocks := minion_anim.observe(unit, session.world.tick_count, _minion_target_position(unit))
	var pose := MinionAnim.pose_key(
		int(clocks["attack"]), bool(clocks["moving"]), float(clocks["walk"]), int(clocks["anim"])
	)
	var art := MinionArt.frame(unit.definition.id, unit.team, unit.nexus_level, pose, unit.facing)
	if art.is_empty():
		return false
	var point := Vector2(int(unit.position.x), int(unit.position.y))
	var radius := int(unit.definition.radius_px)
	if unit.id == session.selected_id:
		draw_arc(point, radius + 9, 0, TAU, 32, Color("f4d491"), 2, true)
	if unit.slow_timer > 0:
		_draw_minion_slow(point, radius, int(clocks["anim"]))
	var src: Rect2 = art["src"]
	var tint := HURT_TINT if int(clocks["hurt"]) > 0 else Color.WHITE
	var corner := point - (art["anchor"] as Vector2)
	draw_texture_rect_region(art["texture"] as Texture2D, Rect2(corner, src.size), src, tint)
	var slash_life := int(clocks["slash_life"])
	if (
		slash_life > 0
		and MinionCombatFxArt.draw_slash(
			self, unit.definition.id, point, slash_life, float(clocks["slash_angle"])
		)
	):
		minion_slash_draws += 1
	_draw_minion_hp_bar(unit, point)
	return true


## `minions/_bundle.py::draw_hp_bar`: 4 px bar, team-coloured back and border, fill by tier.
func _draw_minion_hp_bar(unit: UnitState, point: Vector2) -> void:
	var radius := int(unit.definition.radius_px)
	var width := radius * 2 + 6
	var left := int(point.x) - (width >> 1)
	var top := int(point.y) - radius - 18
	var ratio := clampf(unit.hp / maxf(1.0, float(unit.definition.max_hp)), 0.0, 1.0)
	var blue := unit.team == 0
	var back := Color8(12, 22, 44) if blue else Color8(44, 12, 10)
	var edge := Color8(90, 165, 255) if blue else Color8(255, 95, 85)
	draw_rect(Rect2(left, top, width, 4), back)
	var fill := int(float(width) * ratio)
	if fill > 0:
		var ink := Color8(70, 200, 80)
		if ratio <= 0.3:
			ink = Color8(215, 60, 55)
		elif ratio <= 0.6:
			ink = Color8(225, 190, 60)
		draw_rect(Rect2(left, top, fill, 4), ink)
	draw_rect(Rect2(left + 0.5, top + 0.5, width - 1, 3), edge, false, 1.0)


## `minions/_bundle.py::draw_slow_effect` as `Minion.draw` inlines it: a pale disc and
## three ice specks orbiting the body.
func _draw_minion_slow(point: Vector2, radius: int, anim: int) -> void:
	draw_circle(point, radius + 2, Color8(150, 220, 255, 80))
	for index in range(3):
		var angle := float(anim) * 0.1 + float(index) * 2.0
		var offset := Vector2(int(cos(angle) * (radius + 3)), int(sin(angle) * (radius + 3)))
		draw_rect(Rect2(point + offset, Vector2(2, 2)), Color8(200, 240, 255))


## Prefer the live target; a just-recorded hit retains its coordinates when it dies
## and the simulation removes it from `world.units` before the next draw.
func _minion_target_position(unit: UnitState) -> Vector2:
	var target := session.world.get_unit(unit.target_id)
	if target != null and target.alive:
		return target.position
	for event in session.world.recent_events:
		if String(event.get("kind", "")) != "hit":
			continue
		var from_value: Variant = event.get("from", Vector2.INF)
		var to_value: Variant = event.get("to", Vector2.INF)
		if typeof(from_value) != TYPE_VECTOR2 or typeof(to_value) != TYPE_VECTOR2:
			continue
		var origin: Vector2 = from_value
		if origin.distance_to(unit.position) <= 1.0:
			return to_value as Vector2
	return Vector2.INF


func _draw_minion_death_animations() -> void:
	var remaining: Array[Dictionary] = []
	for animation in _minion_death_animations:
		var life := int(animation.get("life", 0))
		if life <= 0:
			continue
		var point: Vector2 = animation["position"]
		if MinionCombatFxArt.draw_death(self, String(animation["type"]), point, life):
			minion_death_draws += 1
		animation["life"] = life - 1
		if int(animation["life"]) > 0:
			remaining.append(animation)
	_minion_death_animations = remaining
