# gdlint:disable=max-file-lines
extends "res://scenes/siege/siege_view.gd"

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroMarker = preload("res://scripts/ui/hero_marker.gd")
const PathPreview = preload("res://scripts/ui/path_preview.gd")
const SpriteLighting = preload("res://scripts/ui/sprite_lighting.gd")
const BossFont = preload("res://assets/fonts/Barlow-SemiBold.ttf")
const LevelIntroLayout = preload("res://scripts/ui/level_intro_layout.gd")
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
	_draw_kill_feed(world)
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
	var c_vis: Dictionary = b_death.get("celebration_visual", {})
	return {
		"floating_texts": world.effects.floating_texts.size(),
		"particles": world.effects.particles.size(),
		"explosions": world.effects.explosions.size(),
		"kill_feed_count": world.effects.kill_feed.entries.size(),
		"path_preview_active": world.effects.path_preview.active,
		"wave_announcer_active": world.effects.wave_announcer.active,
		"combo_visible": world.effects.combo_counter.display_scale > 0.0,
		"achievement_showing": world.effects.achievement.is_showing(),
		"achievement_glow_active":
		(
			world.effects.achievement.is_showing()
			and int(world.effects.achievement.get_glow_alpha()) > 0
		),
		"level_intro_active": bool(intro.get("active", false)),
		"level_intro_show_prompt": bool(intro.get("show_prompt", false)),
		"boss_intro_active": bool(b_intro.get("active", false)),
		"boss_intro_border_alpha": int(b_intro.get("border_alpha", 0)),
		"boss_death_active": bool(b_death.get("death_active", false)),
		"boss_celebration_active": bool(b_death.get("celebration_active", false)),
		"boss_celebration_reward_visible": bool(c_vis.get("reward_visible", false)),
		"boss_celebration_hint_visible": bool(c_vis.get("hint_visible", false)),
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
		if lane.size() < 2:
			continue
		for index in range(0, lane.size() - 1, 8):
			var raw: Variant = lane[index]
			var point := _path_point(raw)
			var next_point := Vector2(point.x + 1.0, point.y)
			if index + 4 < lane.size():
				next_point = _path_point(lane[index + 4])
			var pulse: int = preview.pulse_index(index, float(world.tick_count))
			var size: int = preview.arrow_size(pulse)
			var alpha: int = preview.arrow_alpha(base_alpha, pulse)
			var points := PathPreview.arrow_points(point, next_point, size)
			draw_colored_polygon(points, Color8(255, 100, 100, alpha))


func _path_point(raw: Variant) -> Vector2:
	if raw is Array:
		var pair: Array = raw
		return Vector2(float(pair[0]), float(pair[1]))
	return raw as Vector2


func _draw_world_effects(world: Prototype) -> void:
	for explosion in world.effects.explosions:
		if not explosion.is_alive():
			continue
		var flash: Dictionary = explosion.get_flash_state()
		var f_size: float = float(flash.get("size", 0))
		var f_intensity: float = clampf(float(flash.get("intensity", 0.0)), 0.0, 1.0)
		var center := Vector2(float(explosion.x), float(explosion.y))
		if f_size > 0.0 and f_intensity > 0.0:
			draw_circle(center, f_size, Color(1.0, 1.0, 0.78, 0.78 * f_intensity))
			draw_circle(center, f_size * 0.5, Color(1.0, 1.0, 1.0, f_intensity))
		for spark in explosion.particles:
			if not spark.alive:
				continue
			var s_alpha: float = clampf(float(spark.alpha()) / 255.0, 0.0, 1.0)
			var s_size: float = float(spark.current_size())
			if s_size > 0.0 and s_alpha > 0.0:
				draw_circle(Vector2(spark.x, spark.y), s_size, Color(spark.color, s_alpha))
	_draw_boss_death_sequence(world)
	for particle in world.effects.particles:
		if not particle.alive:
			continue
		var p_alpha := clampf(float(particle.alpha()) / 255.0, 0.0, 1.0)
		var p_size := float(particle.current_size())
		if p_size > 0.0 and p_alpha > 0.0:
			var particle_center := Vector2(int(particle.x), int(particle.y))
			draw_circle(particle_center, p_size, Color(particle.color, p_alpha))
			draw_circle(particle_center, particle.core_radius(), Color(1.0, 1.0, 1.0, p_alpha))
	for item in world.effects.floating_texts:
		if not item.alive or String(item.text).is_empty():
			continue
		var draw_state: Dictionary = item.presentation_state()
		if draw_state.is_empty():
			continue
		var center_values: Array = draw_state["center"]
		var shadow_values: Array = draw_state["shadow_center"]
		var center := Vector2(float(center_values[0]), float(center_values[1]))
		var shadow_center := Vector2(float(shadow_values[0]), float(shadow_values[1]))
		var text_value: String = String(draw_state["text"])
		var font_size: int = int(draw_state["font_size"])
		var text_metrics: Vector2 = BossFont.get_string_size(
			text_value, HORIZONTAL_ALIGNMENT_LEFT, -1.0, font_size
		)
		var baseline_offset := (
			(BossFont.get_ascent(font_size) - BossFont.get_descent(font_size)) * 0.5
		)
		var shadow_color_values: Array = draw_state["shadow_color"]
		var shadow_color := Color8(
			int(shadow_color_values[0]),
			int(shadow_color_values[1]),
			int(shadow_color_values[2]),
			int(draw_state["shadow_alpha"])
		)
		draw_string(
			BossFont,
			Vector2(shadow_center.x - text_metrics.x * 0.5, shadow_center.y + baseline_offset),
			text_value,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1.0,
			font_size,
			shadow_color
		)
		var text_alpha := float(draw_state["alpha"]) / 255.0
		var text_color := Color(item.color, text_alpha)
		if bool(item.critical):
			draw_string(
				BossFont,
				Vector2(center.x - text_metrics.x * 0.5 + 0.35, center.y + baseline_offset),
				text_value,
				HORIZONTAL_ALIGNMENT_LEFT,
				-1.0,
				font_size,
				text_color
			)
		draw_string(
			BossFont,
			Vector2(center.x - text_metrics.x * 0.5, center.y + baseline_offset),
			text_value,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1.0,
			font_size,
			text_color
		)


func _draw_boss_death_sequence(world: Prototype) -> void:
	if world.boss_death == null or not world.boss_death.is_death_active():
		return
	var anim = world.boss_death
	var center := Vector2(float(anim.boss_x), float(anim.boss_y))
	var visual: Dictionary = anim.get_death_visual_state()
	for wave_value in visual.get("waves", []):
		var wave: Dictionary = wave_value
		var w_radius: float = float(wave.get("radius", 0))
		var w_alpha: float = clampf(float(wave.get("alpha", 0)) / 255.0, 0.0, 1.0)
		var w_rgb: Array = wave.get("color", [255, 220, 150])
		if w_radius > 0.0 and w_alpha > 0.0 and w_rgb.size() >= 3:
			var w_col: Color = Color8(int(w_rgb[0]), int(w_rgb[1]), int(w_rgb[2]))
			draw_arc(center, w_radius, 0.0, TAU, 48, Color(w_col, w_alpha), 3.0, true)
	if bool(visual.get("body_visible", false)):
		var d_size: float = float(visual.get("dissolve_size", 0))
		var d_alpha: float = clampf(float(visual.get("dissolve_alpha", 0)) / 255.0, 0.0, 1.0)
		var b_rgb: Array = anim.boss_color
		if d_size > 0.0 and d_alpha > 0.0 and b_rgb.size() >= 3:
			var b_col: Color = Color8(int(b_rgb[0]), int(b_rgb[1]), int(b_rgb[2]))
			draw_circle(center, d_size, Color(b_col, d_alpha))
	for fragment_value in anim.fragments:
		var frag: Dictionary = fragment_value
		var f_life: int = int(frag.get("life", 0))
		var f_max: int = maxi(1, int(frag.get("max_life", 60)))
		if f_life <= 0:
			continue
		var f_alpha: float = clampf(float(f_life) / float(f_max), 0.0, 1.0)
		var f_rgb: Array = frag.get("color", [180, 90, 80])
		var f_col: Color = Color8(int(f_rgb[0]), int(f_rgb[1]), int(f_rgb[2]))
		draw_circle(
			Vector2(float(frag.get("x", 0.0)), float(frag.get("y", 0.0))),
			float(frag.get("size", 4)),
			Color(f_col, f_alpha)
		)
	for rising_value in anim.rising_particles:
		var rising: Dictionary = rising_value
		var r_life: int = int(rising.get("life", 0))
		var r_max: int = maxi(1, int(rising.get("max_life", 100)))
		if r_life <= 0:
			continue
		var r_alpha: float = clampf(float(r_life) / float(r_max), 0.0, 1.0)
		var r_rgb: Array = rising.get("color", [255, 220, 150])
		var r_col: Color = Color8(int(r_rgb[0]), int(r_rgb[1]), int(r_rgb[2]))
		draw_circle(
			Vector2(float(rising.get("x", 0.0)), float(rising.get("y", 0.0))),
			float(rising.get("size", 3)),
			Color(r_col, r_alpha)
		)


func _draw_wave_announcer(world: Prototype) -> void:
	var announcer = world.effects.wave_announcer
	if announcer == null or not announcer.active:
		return
	var alpha_i: int = announcer.get_alpha()
	if alpha_i <= 0:
		return
	var alpha := clampf(float(alpha_i) / 255.0, 0.0, 1.0)
	var viewport_size: Vector2 = get_viewport_rect().size
	var rect: Rect2 = announcer.visual_rect(int(viewport_size.x), int(viewport_size.y))
	var center_x := rect.get_center().x
	var center_y := rect.get_center().y
	for row in range(80):
		var grad_alpha := int(float(alpha_i) * (1.0 - absf(float(row) - 40.0) / 40.0 * 0.3))
		draw_rect(
			Rect2(rect.position + Vector2(0.0, float(row)), Vector2(400.0, 1.0)),
			Color8(16, 20, 40, grad_alpha)
		)
	draw_rect(rect, Color8(255, 220, 50, alpha_i), false, 3.0)
	draw_rect(rect.grow(-2.0), Color8(255, 250, 180, alpha_i), false, 1.0)
	for stripe in range(0, 400, 10):
		draw_line(
			rect.position + Vector2(float(stripe), 0.0),
			rect.position + Vector2(float(stripe + 10), 80.0),
			Color8(255, 220, 50, alpha_i / 4),
			1.0,
			true
		)
	if alpha_i > 60:
		_draw_gold_corner_ticks(rect, alpha)
	var title: String = announcer.title()
	var title_y := center_y + 8.0
	draw_string(
		BossFont,
		Vector2(rect.position.x + 2.0, title_y + 2.0),
		title,
		HORIZONTAL_ALIGNMENT_CENTER,
		rect.size.x,
		46,
		Color(0.03, 0.03, 0.06, minf(200.0 / 255.0, alpha))
	)
	draw_string(
		BossFont,
		Vector2(rect.position.x, title_y),
		title,
		HORIZONTAL_ALIGNMENT_CENTER,
		rect.size.x,
		46,
		Color(1.0, 0.88, 0.52, alpha)
	)
	draw_string(
		BossFont,
		Vector2(rect.position.x, center_y + 31.0),
		"E N E M I E S   I N C O M I N G",
		HORIZONTAL_ALIGNMENT_CENTER,
		rect.size.x,
		22,
		Color(0.78, 0.78, 0.86, alpha)
	)


func _draw_gold_corner_ticks(rect: Rect2, alpha: float) -> void:
	var left := rect.position.x + 5.0
	var right := rect.end.x - 5.0
	var top := rect.position.y + 5.0
	var bottom := rect.end.y - 5.0
	var ink := Color(1.0, 0.86, 0.47, alpha)
	for x_sign in [-1.0, 1.0]:
		for y_sign in [-1.0, 1.0]:
			var x := left if x_sign < 0.0 else right
			var y := top if y_sign < 0.0 else bottom
			draw_line(Vector2(x, y), Vector2(x - x_sign * 12.0, y), ink, 2.0, true)
			draw_line(Vector2(x, y), Vector2(x, y - y_sign * 12.0), ink, 2.0, true)


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


func _draw_kill_feed(world: Prototype) -> void:
	var feed = world.effects.kill_feed
	if feed == null or feed.entries.is_empty():
		return
	for entry_value in feed.entries:
		var entry: Dictionary = entry_value
		var life: int = int(entry.get("lifetime", 0))
		var max_life: int = maxi(1, int(entry.get("max_lifetime", 180)))
		if life <= 0:
			continue
		var alpha: float = clampf(float(life) / (float(max_life) * 0.35), 0.0, 1.0)
		var y_pos: float = 96.0 + float(entry.get("y_offset", 0.0))
		var tint: Color = entry.get("color", Color.WHITE) as Color
		draw_string(
			BossFont,
			Vector2(980.0, y_pos),
			String(entry.get("text", "")),
			HORIZONTAL_ALIGNMENT_RIGHT,
			270.0,
			14,
			Color(tint, alpha)
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
	var glow_raw: int = int(popup.get_glow_alpha())
	if glow_raw > 0:
		var glow_alpha: float = clampf(float(glow_raw) / 255.0, 0.0, 1.0)
		draw_rect(rect.grow(4.0), Color(1.0, 0.88, 0.45, glow_alpha), false, 3.0)
	draw_rect(rect, Color(0.06, 0.09, 0.14, 0.90 * alpha))
	draw_rect(rect, Color(0.96, 0.83, 0.57, alpha), false, 2.0)
	var icon_type := String(popup.current.get("icon_type", "star"))
	var icon_center := rect.position + Vector2(15.0, 30.0)
	var icon_ops: Array = popup.icon_ops(icon_type, icon_center, int(popup.get_alpha()))
	_draw_achievement_icon(icon_ops)
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


func _draw_achievement_icon(ops: Array) -> void:
	for value in ops:
		var op: Dictionary = value
		var color_values: Array = op.get("color", [255, 255, 255, 255])
		var ink := Color8(
			int(color_values[0]), int(color_values[1]), int(color_values[2]), int(color_values[3])
		)
		match String(op.get("type", "")):
			"circle":
				var center_values: Array = op["center"]
				var center := Vector2(float(center_values[0]), float(center_values[1]))
				var radius := float(op["radius"])
				var circle_width := int(op["width"])
				if circle_width == 0:
					draw_circle(center, radius, ink)
				else:
					draw_arc(center, radius, 0.0, TAU, 36, ink, float(circle_width), true)
			"rect":
				var bounds: Array = op["rect"]
				draw_rect(
					Rect2(
						Vector2(float(bounds[0]), float(bounds[1])),
						Vector2(float(bounds[2]), float(bounds[3]))
					),
					ink
				)
			"polygon":
				var raw_points: Array = op["points"]
				var points := PackedVector2Array()
				for point_value in raw_points:
					var point: Array = point_value
					points.append(Vector2(float(point[0]), float(point[1])))
				var polygon_width := int(op["width"])
				if polygon_width == 0:
					draw_colored_polygon(points, ink)
				else:
					points.append(points[0])
					draw_polyline(points, ink, float(polygon_width), true)
			"text":
				var text_center: Array = op["center"]
				draw_string(
					BossFont,
					Vector2(float(text_center[0]) - 10.0, float(text_center[1]) + 7.0),
					String(op["text"]),
					HORIZONTAL_ALIGNMENT_CENTER,
					20.0,
					int(op["size"]),
					ink
				)


func _draw_boss_intro(world: Prototype) -> void:
	var intro := world.boss_intro_state()
	if not bool(intro.get("active", false)):
		return
	var alpha := clampf(float(intro.get("alpha", 0)) / 255.0, 0.0, 1.0)
	var bg_alpha := clampf(float(intro.get("background_alpha", 0)) / 255.0, 0.0, 1.0)
	var border_alpha: float = clampf(float(intro.get("border_alpha", 0)) / 255.0, 0.0, 1.0)
	if alpha <= 0.0:
		return
	var rect := Rect2(
		Vector2(float(intro.get("banner_x", 340)), float(intro.get("banner_y", 12))),
		Vector2(float(intro.get("banner_width", 600)), 92.0)
	)
	var border_rgb: Array = intro.get("entrance_color", [150, 100, 200])
	var border_col := Color8(int(border_rgb[0]), int(border_rgb[1]), int(border_rgb[2]))
	draw_rect(rect, Color(0.04, 0.05, 0.08, bg_alpha))
	if border_alpha > 0.0:
		draw_rect(rect, Color(border_col, border_alpha), false, 2.0)
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
	var subtitle: String = String(intro.get("boss_title", ""))
	if not subtitle.is_empty():
		draw_string(
			BossFont,
			rect.position + Vector2(18.0, 56.0),
			subtitle,
			HORIZONTAL_ALIGNMENT_LEFT,
			rect.size.x - 200.0,
			14,
			Color(0.84, 0.88, 0.94, alpha)
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
			var flash_alpha: float = clampf(float(d_visual.get("flash_alpha", 0)) / 255.0, 0.0, 1.0)
			if flash_alpha > 0.0:
				draw_rect(
					Rect2(Vector2.ZERO, Vector2(1280.0, 720.0)), Color(1.0, 1.0, 1.0, flash_alpha)
				)
	if not bool(death.get("celebration_active", false)):
		return
	var visual: Dictionary = death.get("celebration_visual", {})
	if not bool(visual.get("visible", false)):
		return
	var overlay_alpha: float = clampf(float(visual.get("overlay_alpha", 0)) / 255.0, 0.0, 1.0)
	if overlay_alpha > 0.0:
		draw_rect(
			Rect2(Vector2.ZERO, Vector2(1280.0, 720.0)), Color(0.02, 0.03, 0.06, overlay_alpha)
		)
	var text_alpha: float = clampf(float(visual.get("text_alpha", 0)) / 255.0, 0.0, 1.0)
	if text_alpha <= 0.0:
		return
	var offset_y: float = float(visual.get("text_offset_y", 0))
	draw_string(
		BossFont,
		Vector2(240.0, 260.0 + offset_y),
		"%s DEFEATED!" % String(death.get("boss_name", "BOSS")).to_upper(),
		HORIZONTAL_ALIGNMENT_CENTER,
		800.0,
		32,
		Color(1.0, 0.86, 0.38, text_alpha)
	)
	var boss_title: String = String(death.get("boss_title", ""))
	if not boss_title.is_empty():
		draw_string(
			BossFont,
			Vector2(240.0, 294.0 + offset_y),
			boss_title,
			HORIZONTAL_ALIGNMENT_CENTER,
			800.0,
			18,
			Color(0.85, 0.90, 0.96, text_alpha)
		)
	if bool(visual.get("reward_visible", false)):
		var reward_alpha: float = clampf(float(visual.get("reward_alpha", 0)) / 255.0, 0.0, 1.0)
		if reward_alpha > 0.0:
			draw_string(
				BossFont,
				Vector2(240.0, 340.0),
				"+%d GOLD REWARD" % int(death.get("gold_reward", 0)),
				HORIZONTAL_ALIGNMENT_CENTER,
				800.0,
				22,
				Color(1.0, 0.88, 0.35, reward_alpha)
			)
	if bool(visual.get("hint_visible", false)):
		var hint_alpha: float = clampf(float(visual.get("hint_alpha", 0)) / 255.0, 0.0, 1.0)
		if hint_alpha > 0.0:
			draw_string(
				BossFont,
				Vector2(240.0, 420.0),
				"PRESS SPACE OR ESC TO CONTINUE",
				HORIZONTAL_ALIGNMENT_CENTER,
				800.0,
				16,
				Color(0.82, 0.88, 0.94, hint_alpha)
			)


func _draw_level_intro(world: Prototype) -> void:
	var intro := world.level_intro_state()
	if not bool(intro.get("active", false)):
		return
	var ops := LevelIntroLayout.ops(
		intro,
		int(intro.get("timer", 0)),
		Time.get_ticks_msec(),
		_measure_intro_text,
		Vector2i(int(intro.get("screen_w", 1280)), int(intro.get("screen_h", 720)))
	)
	for op in ops:
		_draw_intro_op(op)


## Layer 9av: real font metrics for the level intro layout (the oracle uses a
## 0.55*size fake; the layout code is shared).
func _measure_intro_text(text: String, font_size: int) -> Vector2i:
	var measured := BossFont.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	return Vector2i(int(measured.x), font_size)


static func _intro_color(op: Dictionary) -> Color:
	var rgba: Array = op.get("color", [255, 255, 255, 255])
	var alpha := float(rgba[3]) * float(op.get("mult", 255)) / 255.0
	return Color(
		float(rgba[0]) / 255.0, float(rgba[1]) / 255.0, float(rgba[2]) / 255.0, alpha / 255.0
	)


## Renders one `LevelIntroLayout` op. pygame draws onto SRCALPHA surfaces
## WITHOUT blending, so the aura / eye-glow discs are rendered as the annuli
## (`ring_inner`) the overwrite sequence leaves behind.
func _draw_intro_op(op: Dictionary) -> void:
	var kind := String(op.get("kind", ""))
	var color := _intro_color(op)
	match kind:
		"darken":
			var alpha := float(op.get("alpha", 0)) / 255.0
			draw_rect(Rect2(Vector2.ZERO, Vector2(1280.0, 720.0)), Color(0.0, 0.0, 0.0, alpha))
		"fill", "rect":
			var box: Array = op.get("rect", [0, 0, 0, 0])
			var rect := Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
			var width := int(op.get("width", 0))
			if color.a <= 0.0:
				return
			if width > 0:
				draw_rect(rect, color, false, float(width))
			else:
				draw_rect(rect, color)
		"circle":
			var center: Array = op.get("center", [0, 0])
			var at := Vector2(float(center[0]), float(center[1]))
			var radius := float(op.get("radius", 1))
			var width := int(op.get("width", 0))
			if color.a <= 0.0:
				return
			if width > 0:
				draw_arc(at, radius - float(width) * 0.5, 0.0, TAU, 48, color, float(width), true)
			elif op.has("ring_inner") and float(op.get("ring_inner", 0)) > 0.0:
				var inner := float(op.get("ring_inner", 0))
				draw_arc(at, (radius + inner) * 0.5, 0.0, TAU, 64, color, radius - inner, true)
			else:
				draw_circle(at, radius, color)
		"line":
			var a: Array = op.get("a", [0, 0])
			var b: Array = op.get("b", [0, 0])
			if color.a <= 0.0:
				return
			draw_line(
				Vector2(float(a[0]), float(a[1])),
				Vector2(float(b[0]), float(b[1])),
				color,
				float(op.get("width", 1))
			)
		"polygon":
			var points := PackedVector2Array()
			for point in op.get("points", []):
				points.append(Vector2(float(point[0]), float(point[1])))
			if color.a > 0.0 and points.size() >= 3:
				draw_colored_polygon(points, color)
		"text":
			var pos: Array = op.get("pos", [0, 0])
			var font_size := int(op.get("size", 16))
			if color.a <= 0.0:
				return
			var ascent := BossFont.get_ascent(font_size)
			draw_string(
				BossFont,
				Vector2(float(pos[0]), float(pos[1]) + ascent),
				String(op.get("text", "")),
				HORIZONTAL_ALIGNMENT_LEFT,
				-1,
				font_size,
				color
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
	_draw_lit_polygon(HeroMarker.silhouette(point, radius, hero.definition.id), fill)
	draw_circle(point + Vector2(hero.facing * 5, -2), 3, Color("e1fff4"))
	draw_line(point, point + Vector2(hero.facing * (radius + 10), 0), team_color, 2, true)
	var health := float(hero.hp) / maxf(1.0, hero.max_hp)
	draw_rect(Rect2(point + Vector2(-17, -radius - 14), Vector2(34, 4)), Color("071518"))
	draw_rect(Rect2(point + Vector2(-17, -radius - 14), Vector2(34 * health, 4)), team_color)


## Layer 9aq: `lighting.py` pass on a vector body - directional gradient over
## the polygon's own box (the hero path lights the tight crop), 1 px rim on
## the light-facing edges, two-band terminator on the shadow edges. Bodies
## under the source's 24-solid-pixel floor stay flat, exactly like the source.
func _draw_lit_polygon(points: PackedVector2Array, fill: Color) -> void:
	if not SpriteLighting.should_light(points):
		draw_colored_polygon(points, fill)
		return
	var box := Rect2(points[0], Vector2.ZERO)
	for point in points:
		box = box.expand(point)
	draw_polygon(points, SpriteLighting.vertex_colors(points, fill, box))
	var edges := SpriteLighting.classify_edges(points)
	var shade := SpriteLighting.shade_color(fill)
	var band2 := SpriteLighting.shade_color(fill, true)
	for index in edges["shade"]:
		var a := points[index]
		var b := points[(index + 1) % points.size()]
		var inward := SpriteLighting.inward_normal(points, index)
		draw_line(a + inward * 0.5, b + inward * 0.5, shade, 1.0)
		draw_line(a + inward * 1.5, b + inward * 1.5, band2, 1.0)
	var rim := SpriteLighting.rim_color(fill)
	for index in edges["rim"]:
		var a := points[index]
		var b := points[(index + 1) % points.size()]
		var inward := SpriteLighting.inward_normal(points, index)
		draw_line(a + inward * 0.5, b + inward * 0.5, rim, 1.0)


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
	_draw_lit_polygon(SpriteLighting.circle_points(point, radius), body_color)
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
