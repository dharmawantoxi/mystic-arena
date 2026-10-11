# gdlint:disable=max-file-lines
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
	draw_set_transform(world.current_screen_shake_offset(), 0.0, Vector2.ONE)
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
	_draw_path_preview(world)
	_draw_world_effects(world)
	var hero := world.get_unit(match_session.selected_id) as HeroState
	if hero != null and hero.team == world.BLUE and hero.has_destination:
		var mark := hero.destination
		var color := Color("f4d491")
		draw_arc(mark, 8, 0, TAU, 20, color, 1.5, true)
		draw_line(mark - Vector2(5, 5), mark + Vector2(5, 5), color, 1.5, true)
		draw_line(mark + Vector2(-5, 5), mark + Vector2(5, -5), color, 1.5, true)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	_draw_wave_announcer(world)
	_draw_combo_counter(world)
	_draw_achievement_popup(world)
	_draw_boss_intro(world)
	_draw_boss_celebration(world)
	_draw_level_intro(world)


func overlay_draw_summary() -> Dictionary:
	if session == null:
		return {}
	var world := session.world as Prototype
	var intro := world.level_intro_state()
	var b_intro := world.boss_intro_state()
	var b_death := world.boss_death_state()
	return {
		"floating_texts": world.effects.floating_texts.size(),
		"particles": world.effects.particles.size(),
		"explosions": world.effects.explosions.size(),
		"path_preview_active": world.effects.path_preview.active,
		"wave_announcer_active": world.effects.wave_announcer.active,
		"combo_visible": world.effects.combo_counter.display_scale > 0.0,
		"achievement_showing": world.effects.achievement.is_showing(),
		"level_intro_active": bool(intro.get("active", false)),
		"boss_intro_active": bool(b_intro.get("active", false)),
		"boss_death_active": bool(b_death.get("death_active", false)),
		"boss_celebration_active": bool(b_death.get("celebration_active", false)),
		"screen_shake_active":
		(
			world.effects.screen_shake.intensity > 0.0
			or (world.boss_screen_shake_timer > 0 and world.boss_screen_shake_intensity > 0.0)
		),
	}


func _draw_path_preview(world: Prototype) -> void:
	var preview = world.effects.path_preview
	if preview == null or not preview.active:
		return
	var base_alpha: int = preview.get_alpha()
	if base_alpha <= 0:
		return
	for lane_value in preview.paths:
		var lane: Array = lane_value
		for index in range(lane.size()):
			var raw: Variant = lane[index]
			var pt := (
				Vector2(float((raw as Array)[0]), float((raw as Array)[1]))
				if raw is Array
				else (raw as Vector2)
			)
			var pulse: int = preview.pulse_index(index, float(world.tick_count))
			var radius := float(preview.arrow_size(pulse))
			var alpha := clampf(float(preview.arrow_alpha(base_alpha, pulse)) / 255.0, 0.0, 1.0)
			if radius > 0.0 and alpha > 0.0:
				draw_circle(pt, radius, Color(1.0, 0.86, 0.39, alpha))


func _draw_world_effects(world: Prototype) -> void:
	for explosion in world.effects.explosions:
		if not explosion.is_alive():
			continue
		var flash: Dictionary = explosion.get_flash_state()
		var f_size := float(flash.get("size", 0))
		var f_intensity := clampf(float(flash.get("intensity", 0.0)), 0.0, 1.0)
		var center := Vector2(float(explosion.x), float(explosion.y))
		if f_size > 0.0 and f_intensity > 0.0:
			draw_circle(center, f_size, Color(1.0, 1.0, 0.78, 0.78 * f_intensity))
			draw_circle(center, f_size * 0.5, Color(1.0, 1.0, 1.0, f_intensity))
		for spark in explosion.particles:
			if not spark.alive:
				continue
			var s_alpha := clampf(float(spark.alpha()) / 255.0, 0.0, 1.0)
			var s_size := float(spark.current_size())
			if s_size > 0.0 and s_alpha > 0.0:
				draw_circle(Vector2(spark.x, spark.y), s_size, Color(spark.color, s_alpha))
	_draw_boss_death_sequence(world)
	for particle in world.effects.particles:
		if not particle.alive:
			continue
		var p_alpha := clampf(float(particle.alpha()) / 255.0, 0.0, 1.0)
		var p_size := float(particle.current_size())
		if p_size > 0.0 and p_alpha > 0.0:
			draw_circle(Vector2(particle.x, particle.y), p_size, Color(particle.color, p_alpha))
	for item in world.effects.floating_texts:
		if not item.alive or String(item.text).is_empty():
			continue
		var t_alpha := clampf(float(item.alpha()) / 255.0, 0.0, 1.0)
		var f_size := maxi(8, int(round(float(item.font_size) * float(item.scale))))
		if t_alpha > 0.0:
			draw_string(
				BossFont,
				Vector2(float(item.x) - 80.0, float(item.y)),
				String(item.text),
				HORIZONTAL_ALIGNMENT_CENTER,
				160.0,
				f_size,
				Color(item.color, t_alpha)
			)


func _draw_boss_death_sequence(world: Prototype) -> void:
	if world.boss_death == null or not world.boss_death.is_death_active():
		return
	var anim = world.boss_death
	var center := Vector2(float(anim.boss_x), float(anim.boss_y))
	var visual: Dictionary = anim.get_death_visual_state()
	for wave_value in visual.get("waves", []):
		var wave: Dictionary = wave_value
		var w_radius := float(wave.get("radius", 0))
		var w_alpha := clampf(float(wave.get("alpha", 0)) / 255.0, 0.0, 1.0)
		var w_rgb: Array = wave.get("color", [255, 220, 150])
		if w_radius > 0.0 and w_alpha > 0.0 and w_rgb.size() >= 3:
			var w_col := Color8(int(w_rgb[0]), int(w_rgb[1]), int(w_rgb[2]))
			draw_arc(center, w_radius, 0.0, TAU, 48, Color(w_col, w_alpha), 3.0, true)
	if bool(visual.get("body_visible", false)):
		var d_size := float(visual.get("dissolve_size", 0))
		var d_alpha := clampf(float(visual.get("dissolve_alpha", 0)) / 255.0, 0.0, 1.0)
		var b_rgb: Array = anim.boss_color
		if d_size > 0.0 and d_alpha > 0.0 and b_rgb.size() >= 3:
			var b_col := Color8(int(b_rgb[0]), int(b_rgb[1]), int(b_rgb[2]))
			draw_circle(center, d_size, Color(b_col, d_alpha))
	for fragment_value in anim.fragments:
		var frag: Dictionary = fragment_value
		var f_life := int(frag.get("life", 0))
		var f_max := maxi(1, int(frag.get("max_life", 60)))
		if f_life <= 0:
			continue
		var f_alpha := clampf(float(f_life) / float(f_max), 0.0, 1.0)
		var f_rgb: Array = frag.get("color", [180, 90, 80])
		var f_col := Color8(int(f_rgb[0]), int(f_rgb[1]), int(f_rgb[2]))
		draw_circle(
			Vector2(float(frag.get("x", 0.0)), float(frag.get("y", 0.0))),
			float(frag.get("size", 4)),
			Color(f_col, f_alpha)
		)
	for rising_value in anim.rising_particles:
		var rising: Dictionary = rising_value
		var r_life := int(rising.get("life", 0))
		var r_max := maxi(1, int(rising.get("max_life", 100)))
		if r_life <= 0:
			continue
		var r_alpha := clampf(float(r_life) / float(r_max), 0.0, 1.0)
		var r_rgb: Array = rising.get("color", [255, 220, 150])
		var r_col := Color8(int(r_rgb[0]), int(r_rgb[1]), int(r_rgb[2]))
		draw_circle(
			Vector2(float(rising.get("x", 0.0)), float(rising.get("y", 0.0))),
			float(rising.get("size", 3)),
			Color(r_col, r_alpha)
		)


func _draw_wave_announcer(world: Prototype) -> void:
	var announcer = world.effects.wave_announcer
	if announcer == null or not announcer.active:
		return
	var alpha := clampf(float(announcer.get_alpha()) / 255.0, 0.0, 1.0)
	if alpha <= 0.0:
		return
	var offset_x := float(announcer.get_offset_x(1280))
	var rect := Rect2(Vector2(440.0 + offset_x, 150.0), Vector2(400.0, 64.0))
	draw_rect(rect, Color(0.05, 0.08, 0.12, 0.82 * alpha))
	draw_rect(rect, Color(0.96, 0.83, 0.57, alpha), false, 2.0)
	draw_string(
		BossFont,
		Vector2(rect.position.x, rect.position.y + 42.0),
		announcer.title(),
		HORIZONTAL_ALIGNMENT_CENTER,
		rect.size.x,
		30,
		Color(0.96, 0.83, 0.57, alpha)
	)


func _draw_combo_counter(world: Prototype) -> void:
	var combo = world.effects.combo_counter
	if combo == null or combo.display_scale <= 0.0:
		return
	var shown_count: int = combo.count if combo.count > 0 else combo.last_combo
	if shown_count < 2:
		return
	var alpha := clampf(float(combo.display_scale), 0.0, 1.0)
	var ink := Color.WHITE if combo.color_flash > 0 else Color(1.0, 0.82, 0.31)
	var font_size := maxi(12, int(round(22.0 * clampf(float(combo.display_scale), 0.5, 1.5))))
	draw_string(
		BossFont,
		Vector2(1020.0, 160.0),
		"%d HIT COMBO" % shown_count,
		HORIZONTAL_ALIGNMENT_RIGHT,
		220.0,
		font_size,
		Color(ink, alpha)
	)


func _draw_achievement_popup(world: Prototype) -> void:
	var popup = world.effects.achievement
	if popup == null or not popup.is_showing():
		return
	var alpha := clampf(float(popup.get_alpha()) / 255.0, 0.0, 1.0)
	if alpha <= 0.0:
		return
	var rect := Rect2(
		Vector2(float(popup.panel_x(1280)), float(popup.panel_y())),
		Vector2(float(popup.PANEL_W), float(popup.PANEL_H))
	)
	draw_rect(rect, Color(0.06, 0.09, 0.14, 0.90 * alpha))
	draw_rect(rect, Color(0.96, 0.83, 0.57, alpha), false, 2.0)
	var title := String(popup.current.get("title", ""))
	var desc := String(popup.current.get("description", ""))
	if not title.is_empty():
		draw_string(
			BossFont,
			rect.position + Vector2(14.0, 26.0),
			title,
			HORIZONTAL_ALIGNMENT_LEFT,
			rect.size.x - 28.0,
			16,
			Color(1.0, 0.88, 0.45, alpha)
		)
	if not desc.is_empty():
		draw_string(
			BossFont,
			rect.position + Vector2(14.0, 46.0),
			desc,
			HORIZONTAL_ALIGNMENT_LEFT,
			rect.size.x - 28.0,
			13,
			Color(0.85, 0.90, 0.95, alpha)
		)


func _draw_boss_intro(world: Prototype) -> void:
	var intro := world.boss_intro_state()
	if not bool(intro.get("active", false)):
		return
	var alpha := clampf(float(intro.get("alpha", 0)) / 255.0, 0.0, 1.0)
	var bg_alpha := clampf(float(intro.get("background_alpha", 0)) / 255.0, 0.0, 1.0)
	if alpha <= 0.0:
		return
	var rect := Rect2(
		Vector2(float(intro.get("banner_x", 340)), float(intro.get("banner_y", 12))),
		Vector2(float(intro.get("banner_width", 600)), 92.0)
	)
	var border_rgb: Array = intro.get("entrance_color", [150, 100, 200])
	var border_col := Color8(int(border_rgb[0]), int(border_rgb[1]), int(border_rgb[2]))
	draw_rect(rect, Color(0.04, 0.05, 0.08, bg_alpha))
	draw_rect(rect, Color(border_col, alpha), false, 2.0)
	var tag: Dictionary = intro.get("tag", {})
	var header := "%s · %s" % [String(tag.get("text", "BOSS")), String(intro.get("boss_name", ""))]
	draw_string(
		BossFont,
		rect.position + Vector2(18.0, 34.0),
		header,
		HORIZONTAL_ALIGNMENT_LEFT,
		rect.size.x - 200.0,
		20,
		Color(border_col, alpha)
	)
	var bar: Array = intro.get("hp_bar_rect", [0, 0, 150, 12])
	var bar_rect := Rect2(
		Vector2(float(bar[0]), float(bar[1])), Vector2(float(bar[2]), float(bar[3]))
	)
	draw_rect(bar_rect, Color(0.15, 0.05, 0.05, alpha))
	var fill_w := float(intro.get("hp_fill_width", 0))
	if fill_w > 0.0:
		draw_rect(
			Rect2(bar_rect.position, Vector2(fill_w, bar_rect.size.y)),
			Color(0.90, 0.25, 0.25, alpha)
		)


func _draw_boss_celebration(world: Prototype) -> void:
	var death := world.boss_death_state()
	if bool(death.get("death_active", false)):
		var d_visual: Dictionary = death.get("death_visual", {})
		if bool(d_visual.get("flash_visible", false)):
			var flash_alpha := clampf(float(d_visual.get("flash_alpha", 0)) / 255.0, 0.0, 1.0)
			if flash_alpha > 0.0:
				draw_rect(
					Rect2(Vector2.ZERO, Vector2(1280.0, 720.0)), Color(1.0, 1.0, 1.0, flash_alpha)
				)
	if not bool(death.get("celebration_active", false)):
		return
	var visual: Dictionary = death.get("celebration_visual", {})
	if not bool(visual.get("visible", false)):
		return
	var text_alpha := clampf(float(visual.get("text_alpha", 0)) / 255.0, 0.0, 1.0)
	if text_alpha <= 0.0:
		return
	var offset_y := float(visual.get("text_offset_y", 0))
	draw_string(
		BossFont,
		Vector2(240.0, 260.0 + offset_y),
		"%s DEFEATED!" % String(death.get("boss_name", "BOSS")).to_upper(),
		HORIZONTAL_ALIGNMENT_CENTER,
		800.0,
		32,
		Color(1.0, 0.86, 0.38, text_alpha)
	)


func _draw_level_intro(world: Prototype) -> void:
	var intro := world.level_intro_state()
	if not bool(intro.get("active", false)):
		return
	var alpha := clampf(float(intro.get("fade_alpha", 0)) / 255.0, 0.0, 1.0)
	if alpha <= 0.0:
		return
	var card := Rect2(Vector2(320.0, 160.0), Vector2(640.0, 360.0))
	draw_rect(card, Color(0.03, 0.05, 0.08, 0.86 * alpha))
	draw_rect(card, Color(0.95, 0.82, 0.52, alpha), false, 2.0)
	draw_string(
		BossFont,
		card.position + Vector2(24.0, 52.0),
		"LEVEL %d · %s" % [int(intro.get("level_num", 1)), String(intro.get("level_name", ""))],
		HORIZONTAL_ALIGNMENT_CENTER,
		card.size.x - 48.0,
		26,
		Color(0.95, 0.82, 0.52, alpha)
	)
	var warning := String(intro.get("warning_text", ""))
	if not warning.is_empty():
		draw_string(
			BossFont,
			card.position + Vector2(24.0, 100.0),
			warning,
			HORIZONTAL_ALIGNMENT_CENTER,
			card.size.x - 48.0,
			18,
			Color(1.0, 0.45, 0.40, alpha)
		)
	if bool(intro.get("show_prompt", false)):
		var prompt := String(intro.get("prompt_text", ""))
		if not prompt.is_empty():
			draw_string(
				BossFont,
				card.position + Vector2(24.0, 320.0),
				prompt,
				HORIZONTAL_ALIGNMENT_CENTER,
				card.size.x - 48.0,
				18,
				Color(0.85, 0.92, 0.98, alpha)
			)


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
			var from: Vector2 = hero.position + delta * (float(segment) * 0.33)
			var to: Vector2 = hero.position + delta * (float(segment) * 0.33 + 0.18)
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
	draw_colored_polygon(HeroMarker.silhouette(point, radius, hero.definition.id), fill)
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
