extends "res://scenes/siege/siege_view.gd"

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroMarker = preload("res://scripts/ui/hero_marker.gd")
const BossFont = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const TerrainPalette = preload("res://scripts/ui/terrain_palette.gd")
const RiverTiles = preload("res://scripts/ui/river_tiles.gd")
const LaneTiles = preload("res://scripts/ui/lane_tiles.gd")
const WallTiles = preload("res://scripts/ui/wall_tiles.gd")
const TerrainTiles = preload("res://scripts/ui/terrain_tiles.gd")
var cached_river_theme := ""


func _draw() -> void:
	if session == null:
		super._draw()
		return
	var world := session.world as Prototype
	terrain_palette = TerrainPalette.for_level(world.level_config)
	terrain_river = TerrainPalette.river_path()
	var map_theme: String = String(world.level_config.get("map_theme", "forest"))
	if river_texture == null or cached_river_theme != map_theme:
		terrain_texture = ImageTexture.create_from_image(TerrainTiles.raster(terrain_palette))
		river_texture = ImageTexture.create_from_image(RiverTiles.raster(terrain_palette))
		lane_texture = ImageTexture.create_from_image(LaneTiles.raster(terrain_palette))
		if wall_texture == null:
			wall_texture = ImageTexture.create_from_image(WallTiles.raster())
		cached_river_theme = map_theme
	draw_set_transform(world.boss_presentation_offset(), 0.0, Vector2.ONE)
	super._draw()
	var match_session := session as PrototypeSession
	for arrow in world.hero_projectiles:
		var ink := Color("73cbbb") if arrow.team == 0 else Color("d78579")
		draw_circle(arrow.position, 3, ink)
	for snapshot in world.boss_death_presentations:
		_draw_boss_death(snapshot)
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
	_draw_tactical(world)
	var hero := world.get_unit(match_session.selected_id) as HeroState
	if hero != null and hero.team == world.BLUE and hero.has_destination:
		var mark := hero.destination
		var color := Color("f4d491")
		draw_arc(mark, 8, 0, TAU, 20, color, 1.5, true)
		draw_line(mark - Vector2(5, 5), mark + Vector2(5, 5), color, 1.5, true)
		draw_line(mark + Vector2(-5, 5), mark + Vector2(5, -5), color, 1.5, true)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_tactical(world: Prototype) -> void:
	var tactical = world.tactical
	if not tactical.gather_point_active or tactical.gather_point_timer <= 0:
		return
	var point: Vector2 = tactical.gather_point
	var fade := clampf(float(tactical.gather_point_timer) / 150.0, 0.0, 1.0)
	var pulse := (sin(float(world.tick_count) * 0.133) * 0.3 + 0.7) * fade
	var color: Color = tactical.command_color()
	for radius in range(50, 20, -8):
		var alpha := float(50 - radius) * 4.0 * pulse / 255.0
		if alpha > 0.0:
			draw_arc(point, radius, 0, TAU, 40, Color(color, alpha), 2, true)
	draw_circle(point, 6, color)
	draw_circle(point, 2, Color.WHITE)
	if tactical.active_command not in ["gather", "protect_castle", "attack_boss", "protect_tower"]:
		return
	for hero in world.player_roster():
		if not hero.alive:
			continue
		var delta: Vector2 = point - hero.position
		if delta.length() <= 80.0:
			continue
		for segment in range(3):
			var from := hero.position + delta * (float(segment) * 0.33)
			var to := hero.position + delta * (float(segment) * 0.33 + 0.18)
			draw_line(from, to, Color(color, 120.0 * pulse / 255.0), 2, true)


func _draw_unit(unit: UnitState) -> void:
	if unit is BossState:
		_draw_boss(unit as BossState)
		return
	if not unit.is_hero:
		super._draw_unit(unit)
		return
	var hero := unit as HeroState
	var point := hero.position
	var radius := hero.settings().radius_px
	var team_color := Color("73cbbb") if hero.team == 0 else Color("d78579")
	var fill := HeroMarker.fill(hero.definition.id)
	if hero.id == session.selected_id:
		draw_arc(point, radius + 12, 0, TAU, 36, Color("f4d491"), 2, true)
	# Team outline, stable ID polygon, and facing eye are intentionally basic.
	draw_circle(point + Vector2(0, 4), radius + 5, Color("071518"))
	draw_circle(point, radius + 5, team_color)
	draw_colored_polygon(HeroMarker.body(point, radius, hero.definition.id), fill)
	draw_circle(point + Vector2(hero.facing * 5, -2), 3, Color("e1fff4"))
	draw_line(point, point + Vector2(hero.facing * (radius + 10), 0), team_color, 2, true)
	var health := float(hero.hp) / maxf(1.0, hero.max_hp)
	draw_rect(Rect2(point + Vector2(-17, -radius - 14), Vector2(34, 4)), Color("071518"))
	draw_rect(Rect2(point + Vector2(-17, -radius - 14), Vector2(34 * health, 4)), team_color)


func _draw_boss(boss: BossState) -> void:
	var point := boss.position
	var radius := boss.radius
	var is_true := boss.boss_class == "true"
	if boss.entrance_timer > 0:
		_draw_boss_entrance(boss)
		return
	if boss.ability_active:
		var ability_pulse := sin(float(boss.anim_time) * 0.2) * 0.3 + 0.7
		var ability_radius := boss.ability_range * ability_pulse
		draw_arc(point, ability_radius, 0, TAU, 48, Color(boss.entrance_color, 0.30), 3, true)
	if boss.is_enraged:
		var enrage_pulse := sin(boss.enrage_pulse) * 0.3 + 0.7
		var enrage_radius := radius + 14.0 * enrage_pulse
		var enrage_color := Color("ff3228") if is_true else Color("ff8c1e")
		draw_arc(point, enrage_radius, 0, TAU, 48, Color(enrage_color, 0.65), 3, true)
	if is_true:
		var true_pulse := sin(boss.pulse) * 0.3 + 0.7
		draw_arc(point, radius + 15.0, 0, TAU, 48, Color(boss.color, 0.28 * true_pulse), 4, true)

	# Shadow and generic body are the Godot presentation fallback for all 216
	# source boss IDs; gameplay and the source entrance/enrage states stay shared.
	draw_circle(point + Vector2(0, radius + 3), radius + 3, Color("071518", 0.65))
	var body_color := Color.WHITE if boss.hurt_flash_timer > 0 else boss.color
	draw_circle(point, radius, body_color)
	draw_arc(point, radius, 0, TAU, 32, boss.color_dark, 3, true)
	var highlight := body_color.lightened(0.20)
	draw_circle(
		point - Vector2(radius * 0.30, radius * 0.30), radius * 0.42, Color(highlight, 0.55)
	)

	var crown_count := 7 if is_true else 5
	var crown_color := Color("ff6464") if is_true else Color("ffc832")
	for index in range(crown_count):
		var angle := PI + float(index - crown_count / 2) * 0.25
		var crown_point := point + Vector2(cos(angle), sin(angle)) * (radius + 3.0)
		var crown_tip := crown_point + Vector2(0, -8 if is_true else -6)
		draw_colored_polygon(
			PackedVector2Array(
				[crown_point + Vector2(-2, 0), crown_tip, crown_point + Vector2(2, 0)]
			),
			crown_color
		)
	var eye_color := Color("64c8ff") if is_true else Color("ff3232")
	for side in [-1.0, 1.0]:
		var eye := point + Vector2(side * radius * 0.33, -radius * 0.25)
		draw_circle(eye, 4, Color.BLACK)
		draw_circle(eye, 2, eye_color)
	draw_line(point, point + Vector2(boss.direction * (radius + 8.0), 0), eye_color, 3, true)

	var bar_width := 70.0 if is_true else 60.0
	var bar_height := 10.0 if is_true else 8.0
	var bar_position := point + Vector2(-bar_width * 0.5, -radius - 16.0)
	var health := clampf(float(boss.hp) / maxf(1.0, float(boss.max_hp)), 0.0, 1.0)
	draw_rect(Rect2(bar_position, Vector2(bar_width, bar_height)), Color("280000"))
	var health_color := Color("64dc64") if health > 0.5 else Color("f0dc3c")
	if health <= 0.25:
		health_color = Color("f03c3c")
	draw_rect(Rect2(bar_position, Vector2(bar_width * health, bar_height)), health_color)
	var border := (
		Color("ff3c3c") if boss.is_enraged else (Color("ff6464") if is_true else Color("ffc832"))
	)
	draw_rect(Rect2(bar_position, Vector2(bar_width, bar_height)), border, false, 1.0)
	var prefix := "TRUE BOSS" if is_true else "BOSS"
	var tag := " [ENRAGED]" if is_true else " [FRENZY]"
	var suffix := tag if boss.is_enraged else ""
	var label := "%s: %s%s" % [prefix, boss.display_name, suffix]
	draw_string(
		BossFont,
		Vector2(point.x - 190.0, bar_position.y - 3.0),
		label,
		HORIZONTAL_ALIGNMENT_CENTER,
		380.0,
		18 if is_true else 16,
		border
	)


func _draw_boss_entrance(boss: BossState) -> void:
	var state := boss.entrance_presentation_state()
	var size := int(state["aura_radius"])
	if size > 0:
		var alpha := float(state["aura_alpha"]) / 255.0
		draw_circle(boss.position, size, Color(boss.entrance_color, alpha))
	if bool(state["text_visible"]):
		draw_string(
			BossFont,
			Vector2(180, 100),
			boss.entrance_text,
			HORIZONTAL_ALIGNMENT_CENTER,
			920,
			28 if boss.boss_class == "true" else 24,
			Color(boss.entrance_color, float(state["text_alpha"]) / 255.0)
		)


func _draw_boss_death(snapshot: Dictionary) -> void:
	var point: Vector2 = snapshot.get("position", Vector2.ZERO)
	var timer := int(snapshot.get("timer", 0))
	var maximum := maxf(1.0, float(snapshot.get("max_timer", 35)))
	var age := maximum - float(timer)
	var flash_timer := int(snapshot.get("flash_timer", 0))
	var flash_maximum := maxf(1.0, float(snapshot.get("flash_max", 8)))
	if flash_timer > 0:
		var intensity := float(flash_timer) / flash_maximum
		draw_circle(point, 20.0 * intensity, Color(1.0, 1.0, 0.78, 0.78 * intensity))
		draw_circle(point, 10.0 * intensity, Color(1.0, 1.0, 1.0, intensity))
	var particle_count := maxi(1, int(snapshot.get("particle_count", 25)))
	var particle_min := float(snapshot.get("particle_min", 4))
	var particle_max := float(snapshot.get("particle_max", 6))
	var fade := clampf(float(timer) / maximum, 0.0, 1.0)
	for index in range(particle_count):
		var fraction := float(index) / float(particle_count)
		var angle := TAU * fraction + age * 0.035
		var speed := lerpf(1.5, 4.0, fmod(float(index) * 0.618, 1.0))
		var offset := Vector2(cos(angle), sin(angle)) * speed * age
		var spark_size := lerpf(particle_min, particle_max, fmod(float(index) * 0.37, 1.0))
		var spark_color := Color("ff6464") if index % 3 == 0 else Color("ffbe64")
		draw_circle(point + offset, spark_size * maxf(0.2, fade), Color(spark_color, fade))
