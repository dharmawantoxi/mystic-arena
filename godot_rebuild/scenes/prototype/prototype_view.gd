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
const KillFeedLayout = preload("res://scripts/ui/kill_feed_layout.gd")
const ComboCounterLayout = preload("res://scripts/ui/combo_counter_layout.gd")
const BossIntroLayout = preload("res://scripts/ui/boss_intro_layout.gd")
const BossCelebrationLayout = preload("res://scripts/ui/boss_celebration_layout.gd")
const BossDeathSequenceLayout = preload("res://scripts/ui/boss_death_sequence_layout.gd")
const HitParticleLayout = preload("res://scripts/ui/hit_particle_layout.gd")
const DeathExplosionLayout = preload("res://scripts/ui/death_explosion_layout.gd")
const MapTintLayout = preload("res://scripts/ui/map_tint_layout.gd")
const MapArt = preload("res://scripts/ui/map_art.gd")
const DynamicMapRenderer = preload("res://scripts/ui/dynamic_map_renderer.gd")
const SlotArt = preload("res://scripts/ui/slot_art.gd")
const HeroArt = preload("res://scripts/ui/hero_art.gd")
const HeroAnim = preload("res://scripts/ui/hero_anim.gd")
const HeroPainter = preload("res://scripts/ui/hero_painter.gd")
const BossArt = preload("res://scripts/ui/boss_art.gd")
const BossAnim = preload("res://scripts/ui/boss_anim.gd")
const NyxarethRealmLayout = preload("res://scripts/ui/nyxareth_realm_layout.gd")
const TacticalLayout = preload("res://scripts/ui/tactical_layout.gd")
const GoldHudLayout = preload("res://scripts/ui/gold_hud_layout.gd")
const ShopHintLayout = preload("res://scripts/ui/shop_hint_layout.gd")
const TerrainPalette = preload("res://scripts/ui/terrain_palette.gd")
const RiverTiles = preload("res://scripts/ui/river_tiles.gd")
const LaneTiles = preload("res://scripts/ui/lane_tiles.gd")
const WallTiles = preload("res://scripts/ui/wall_tiles.gd")
const TerrainTiles = preload("res://scripts/ui/terrain_tiles.gd")
const HeroProjectileArtScript = preload("res://scripts/ui/hero_projectile_art.gd")
const HUD_SCREEN_W := 1280
## Layer 9bi: paint order of the world-space layers (`EffectManager.draw` = path
## preview then the effects, then `tactical.draw_world`) and of the screen overlays
## (`Game.draw`: boss intro, then `effects.draw_ui` = wave announcer and achievement,
## level intro, and the boss death animation last). The combo counter and kill feed
## are never drawn by the source; they keep their slot between announcer and popup.
const WORLD_LAYER_ORDER := ["path_preview", "effects", "tactical"]
const OVERLAY_ORDER := [
	"shop_hints",
	"gold_hud",
	"boss_intro",
	"wave_announcer",
	"combo_counter",
	"kill_feed",
	"achievement",
	"tactical_feedback",
	"level_intro",
	"boss_death",
]
var cached_river_theme := ""
## Counts real `_draw` calls so the headless scene suite can prove the painters run.
var draw_count := 0
var hero_anim := HeroAnim.new()
var hero_projectile_art = HeroProjectileArtScript.new()
## Source-baked projectile painter calls proven by the scene suite.
var hero_projectile_draws := 0
## Baked boss bodies drawn so far; the painter suite proves the sprite path runs.
var boss_sprite_draws := 0
## Resolved source keyframes painted by the live scene, including attack and skill poses.
var boss_pose_draws: Dictionary = {}
## Screen-wide boss skill layers painted under the body (nyxareth's ultimate, layer 9bq3).
var boss_screen_layer_draws := 0
## The tactical banner border (layer 9bi2): 2 px, 6 px corners, drawn inside its box.
var tactical_border := StyleBoxFlat.new()
## Layer 9bv2: pygame skips `_draw_gold_hud` while the wide-screen side panel shows the
## gold; the screen clears this flag then.
var gold_hud_visible := true
## Gold HUD paints so far; the scene suite proves the chip reaches `_draw`.
var gold_hud_draws := 0
## Rounded chip/badge fills and borders (pygame `draw.rect(..., border_radius=r)`).
var hud_round_box := StyleBoxFlat.new()
var dynamic_map := DynamicMapRenderer.new()
## Real DynamicRenderer paints; the scene suite proves this reaches `_draw`.
var dynamic_map_draws := 0


func _draw() -> void:
	draw_count += 1
	if session == null:
		super._draw()
		return
	var world := session.world as Prototype
	terrain_palette = TerrainPalette.for_level(world.level_config)
	terrain_river = TerrainPalette.river_path()
	var map_theme: String = String(world.level_config.get("map_theme", "forest"))
	if cached_river_theme != map_theme:
		cache_static_map(map_theme)
	draw_set_transform(world.current_screen_shake_offset(), 0.0, Vector2.ONE)
	super._draw()
	var match_session := session as PrototypeSession
	for arrow in world.hero_projectiles:
		if not bool(arrow.get("active", true)):
			continue
		var heading: Vector2 = arrow.last_target - arrow.position
		if heading.length_squared() < 0.001:
			heading = arrow.position - arrow.origin
		var angle := heading.angle() if heading.length_squared() >= 0.001 else 0.0
		var drawn := bool(
			hero_projectile_art.call(
				"draw",
				self,
				String(arrow.get("hero_type", "")),
				arrow.position,
				angle,
				int(arrow.get("age", 0)),
				int(arrow.get("damage", 1)),
				bool(arrow.get("is_crit", false))
			)
		)
		if drawn:
			hero_projectile_draws += 1
		else:
			var ink := Color("73cbbb") if arrow.team == 0 else Color("d78579")
			draw_circle(arrow.position, 3, ink)
	# `Game.draw` paints the boss after every hero ("di luar hero loop"). The registry never
	# holds the boss (`active_boss` only lives in `_by_id`), so `_draw_unit` cannot reach it.
	var live_boss: BossState = world.active_boss
	if live_boss != null and live_boss.alive:
		_draw_boss(live_boss)
	for snapshot in world.boss_death_presentations:
		_draw_boss_death(snapshot)
	for layer in WORLD_LAYER_ORDER:
		_draw_world_layer(String(layer), world)
	var hero := world.get_unit(match_session.selected_id) as HeroState
	if hero != null and hero.team == world.BLUE and hero.has_destination:
		var mark := hero.destination
		var color := Color("f4d491")
		draw_arc(mark, 8, 0, TAU, 20, color, 1.5, true)
		draw_line(mark - Vector2(5, 5), mark + Vector2(5, 5), color, 1.5, true)
		draw_line(mark + Vector2(-5, 5), mark + Vector2(5, -5), color, 1.5, true)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	for layer in OVERLAY_ORDER:
		_draw_overlay_layer(String(layer), world)


## Layer 9bm: `Game.draw` paints the build slots right after the map and BEFORE the towers
## and units. The marker is the baked source sprite (`SlotArt`); the selection preview
## (range disc and arc) is the rebuild's own and stays.
func _draw_structures() -> void:
	hero_anim.prune(session.world.units)
	_draw_build_slots(session.world as Prototype)
	super._draw_structures()


func _draw_build_slots(world: Prototype) -> void:
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
		var art := SlotArt.frame(slot.team, world.tick_count)
		if art.is_empty():
			_draw_slot_outline(slot.position, color, selected)
			continue
		var src: Rect2 = art["src"]
		var corner := slot.position - (art["anchor"] as Vector2)
		corner = Vector2(int(corner.x), int(corner.y))
		draw_texture_rect_region(art["texture"] as Texture2D, Rect2(corner, src.size), src)


## The rebuild's plain marker, used only while the baked sheet is unavailable.
func _draw_slot_outline(point: Vector2, color: Color, selected: bool) -> void:
	draw_arc(point, 19, 0, TAU, 36, Color(color, 0.95 if selected else 0.5), 2, true)
	draw_line(point - Vector2(6, 0), point + Vector2(6, 0), color, 2, true)
	draw_line(point - Vector2(0, 6), point + Vector2(0, 6), color, 2, true)


## Layer 9bj2: cache the theme's static map layers. The baked source base (terrain,
## river and lanes, `bake/bake_map_base.py`) replaces the native tile rasters and the
## baked border wall replaces `WallTiles`; either falls back to the native raster when
## its PNG is not imported, so a fresh checkout still draws a map.
func cache_static_map(map_theme: String) -> void:
	if terrain_palette.is_empty():
		terrain_palette = TerrainPalette.for_theme(map_theme)
	var base := MapArt.base_texture(map_theme)
	baked_static_base = base != null
	if baked_static_base:
		terrain_texture = base
		river_texture = null
		lane_texture = null
	else:
		terrain_texture = ImageTexture.create_from_image(TerrainTiles.raster(terrain_palette))
		river_texture = ImageTexture.create_from_image(RiverTiles.raster(terrain_palette))
		lane_texture = ImageTexture.create_from_image(LaneTiles.raster(terrain_palette))
	var wall := MapArt.wall_texture()
	if wall != null:
		wall_texture = wall
	elif wall_texture == null:
		wall_texture = ImageTexture.create_from_image(WallTiles.raster())
	cached_river_theme = map_theme


## Layer 9bj: the baked decorations and shop buildings of the current theme.
func _draw_map_decor() -> void:
	var overlay := MapArt.overlay_texture(cached_river_theme)
	if overlay != null:
		draw_texture(overlay, Vector2.ZERO)


## Layer 9d0: source DynamicRenderer between the static map and ambient tint.
func _draw_map_dynamic() -> void:
	if dynamic_map.theme_name != cached_river_theme:
		dynamic_map.configure(cached_river_theme)
	var world := session.world as Prototype
	dynamic_map.draw(self, world.tick_count)
	dynamic_map_draws += 1


## Layer 9bh: the ambient tint `MapRenderer.draw()` lays over the map, under the
## units. The base view calls this hook right after the cached map layers.
func _draw_map_overlay() -> void:
	for op in map_tint_draw_ops(session.world as Prototype):
		_draw_intro_op(op)


func map_tint_draw_ops(world: Prototype) -> Array:
	return MapTintLayout.ops(String(world.level_config.get("map_theme", "forest")))


func world_layer_order() -> Array:
	return WORLD_LAYER_ORDER.duplicate()


func overlay_paint_order() -> Array:
	return OVERLAY_ORDER.duplicate()


func _draw_world_layer(layer: String, world: Prototype) -> void:
	match layer:
		"path_preview":
			_draw_path_preview(world)
		"effects":
			_draw_world_effects(world)
		"tactical":
			_draw_tactical(world)


func _draw_overlay_layer(layer: String, world: Prototype) -> void:
	match layer:
		"boss_intro":
			_draw_boss_intro(world)
		"wave_announcer":
			_draw_wave_announcer(world)
		"combo_counter":
			_draw_combo_counter(world)
		"kill_feed":
			_draw_kill_feed(world)
		"achievement":
			_draw_achievement_popup(world)
		"shop_hints":
			_draw_shop_hints(world)
		"gold_hud":
			_draw_gold_hud(world)
		"tactical_feedback":
			_draw_tactical_feedback(world)
		"level_intro":
			_draw_level_intro(world)
		"boss_death":
			_draw_boss_death_animation(world)


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
		for op in DeathExplosionLayout.ops(explosion):
			_draw_death_op(op)
	for particle in world.effects.particles:
		for op in HitParticleLayout.ops(particle):
			_draw_death_op(op)
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


## Layer 9bc: the ops `ComboCounter.draw()` paints this frame, measured with the
## real font (the oracle uses a 0.55*size fake; the layout code is shared).
func combo_counter_draw_ops(world: Prototype) -> Array:
	var counter = world.effects.combo_counter
	if counter == null:
		return []
	var state := ComboCounterLayout.state_of(counter)
	return ComboCounterLayout.ops(state, HUD_SCREEN_W, _measure_hud_text)


func _draw_combo_counter(world: Prototype) -> void:
	for op in combo_counter_draw_ops(world):
		_draw_intro_op(op)


## Layer 9bb: the ops `KillFeed.draw()` paints this frame, measured with the
## real font (the oracle uses a 0.55*size fake; the layout code is shared).
func kill_feed_draw_ops(world: Prototype) -> Array:
	var feed = world.effects.kill_feed
	if feed == null:
		return []
	return KillFeedLayout.ops(feed.entries, HUD_SCREEN_W, _measure_hud_text)


func _draw_kill_feed(world: Prototype) -> void:
	for op in kill_feed_draw_ops(world):
		_draw_kill_feed_op(op)


func _measure_hud_text(text: String, font_size: int) -> Vector2i:
	var measured := BossFont.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	return Vector2i(ceili(measured.x), ceili(BossFont.get_height(font_size)))


## Backing box and text reuse the level-intro op painter; the border is a
## rounded outline. pygame strokes a border INSIDE its rect while Godot centres
## the stroke on the path, so the path is pulled in by half the stroke width.
func _draw_kill_feed_op(op: Dictionary) -> void:
	if String(op.get("kind", "")) != "rect":
		_draw_intro_op(op)
		return
	var box: Array = op["rect"]
	var rect := Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
	var width := float(op["width"])
	var inset := width * 0.5
	_draw_achievement_outline(
		rect.grow(-inset), float(op["radius"]) - inset, _intro_color(op), width
	)


func _draw_achievement_popup(world: Prototype) -> void:
	var popup = world.effects.achievement
	if popup == null or not popup.is_showing():
		return
	var alpha: int = clampi(int(popup.get_alpha()), 0, 255)
	if alpha <= 0:
		return
	var rect := Rect2(
		Vector2(float(popup.panel_x(1280)), float(popup.panel_y())),
		Vector2(float(popup.PANEL_W), float(popup.PANEL_H))
	)
	for row in range(int(rect.size.y)):
		var grad := 20 + int(float(row) * 0.3)
		var ink := Color8(grad, grad, floori(float(grad) / 2.0), alpha)
		draw_line(
			Vector2(rect.position.x, rect.position.y + row),
			Vector2(rect.end.x, rect.position.y + row),
			ink,
			1.0,
			true
		)
	_draw_achievement_outline(rect, 6.0, Color8(255, 220, 50, alpha), 3.0)
	_draw_achievement_outline(rect.grow(-2.0), 5.0, Color8(255, 250, 180, alpha), 1.0)
	if alpha > 60:
		_draw_achievement_ticks(rect, Color8(255, 220, 50, 255))
	var icon_type := String(popup.current.get("icon_type", "star"))
	var icon_center := rect.position + Vector2(15.0, 30.0)
	var icon_ops: Array = popup.icon_ops(icon_type, icon_center, alpha)
	_draw_achievement_icon(icon_ops)
	var title := String(popup.current.get("title", ""))
	var desc := String(popup.current.get("description", ""))
	var text_x := rect.position.x + 55.0
	var text_width := rect.size.x - 65.0
	_draw_achievement_label(
		"A C H I E V E M E N T",
		text_x,
		rect.position.y + 7.0,
		16,
		Color8(255, 220, 50, alpha),
		text_width
	)
	if not title.is_empty():
		_draw_achievement_label(
			title, text_x, rect.position.y + 24.0, 22, Color8(255, 255, 255, alpha), text_width
		)
	if not desc.is_empty():
		_draw_achievement_label(
			desc, text_x, rect.position.y + 45.0, 17, Color8(205, 210, 225, alpha), text_width
		)
	var glow_raw: int = int(popup.get_glow_alpha())
	if glow_raw > 0:
		var glow_rect := Rect2(rect.position - Vector2(10.0, 10.0), rect.size + Vector2(20.0, 20.0))
		var glow_points := _achievement_rounded_points(glow_rect, 10.0)
		draw_colored_polygon(glow_points, Color8(255, 220, 50, clampi(glow_raw, 0, 255)))


func _achievement_rounded_points(rect: Rect2, radius: float) -> PackedVector2Array:
	var points := PackedVector2Array()
	var centers := [
		Vector2(rect.position.x + radius, rect.position.y + radius),
		Vector2(rect.end.x - radius, rect.position.y + radius),
		Vector2(rect.end.x - radius, rect.end.y - radius),
		Vector2(rect.position.x + radius, rect.end.y - radius),
	]
	var starts := [180.0, 270.0, 0.0, 90.0]
	for corner in range(4):
		for sample in range(5):
			var angle := deg_to_rad(float(starts[corner]) + float(sample) * 22.5)
			points.append(centers[corner] + Vector2(cos(angle), sin(angle)) * radius)
	return points


func _draw_achievement_outline(rect: Rect2, radius: float, ink: Color, width: float) -> void:
	var points := _achievement_rounded_points(rect, radius)
	points.append(points[0])
	draw_polyline(points, ink, width, true)


func _draw_achievement_ticks(rect: Rect2, ink: Color) -> void:
	var anchors := [
		Vector2(rect.position.x + 4.0, rect.position.y + 4.0),
		Vector2(rect.end.x - 4.0, rect.position.y + 4.0),
		Vector2(rect.position.x + 4.0, rect.end.y - 4.0),
		Vector2(rect.end.x - 4.0, rect.end.y - 4.0),
	]
	for index in range(4):
		var anchor: Vector2 = anchors[index]
		var x_dir := 1.0 if index == 0 or index == 2 else -1.0
		var y_dir := 1.0 if index < 2 else -1.0
		draw_line(anchor, anchor + Vector2(x_dir * 10.0, 0.0), ink, 2.0, true)
		draw_line(anchor, anchor + Vector2(0.0, y_dir * 10.0), ink, 2.0, true)


func _draw_achievement_label(
	text: String, x: float, top: float, size: int, ink: Color, max_width: float
) -> void:
	var font := BossFont
	var shown := _fit_achievement_label(text, size, max_width)
	var ascent := font.get_ascent(size)
	draw_string(font, Vector2(x, top + ascent), shown, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, ink)


func _fit_achievement_label(text: String, size: int, max_width: float) -> String:
	var font := BossFont
	if font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size).x <= max_width:
		return text
	var clipped := text
	while clipped.length() > 1:
		clipped = clipped.substr(0, clipped.length() - 1)
		var candidate := clipped + "…"
		if font.get_string_size(candidate, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size).x <= max_width:
			return candidate
	return "…"


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


## Layer 9bd: the ops `BossIntroCinematic.draw()` paints this frame. The source
## blits its text at fixed offsets, so the layout needs no font metrics.
func boss_intro_draw_ops(world: Prototype) -> Array:
	var intro = world.boss_intro
	if intro == null:
		return []
	return BossIntroLayout.ops(intro)


func _draw_boss_intro(world: Prototype) -> void:
	for op in boss_intro_draw_ops(world):
		_draw_banner_op(op)


## Banner and HP bar ops: a rounded rect with width 0 is a filled polygon, a
## stroked one reuses the kill-feed inset outline, and lines, text and square
## rects go through the level-intro painter.
func _draw_banner_op(op: Dictionary) -> void:
	var is_rect := String(op.get("kind", "")) == "rect"
	if not is_rect or int(op.get("radius", 0)) <= 0:
		_draw_intro_op(op)
	elif int(op.get("width", 0)) > 0:
		_draw_kill_feed_op(op)
	else:
		_fill_rounded_op(op)


func _fill_rounded_op(op: Dictionary) -> void:
	var color := _intro_color(op)
	if color.a <= 0.0:
		return
	var box: Array = op["rect"]
	var rect := Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
	# pygame clamps the radius to the shorter side. Keep the arcs from meeting so
	# the polygon stays simple, and fall back to a plain rect for slivers.
	var radius := minf(float(op["radius"]), (minf(rect.size.x, rect.size.y) - 1.0) * 0.5)
	if radius < 1.0:
		draw_rect(rect, color)
		return
	draw_colored_polygon(_achievement_rounded_points(rect, radius), color)


## `boss_death.draw()` runs LAST in the source, in screen space (after the shake
## and above every HUD layer): the death phase, then the celebration.
func _draw_boss_death_animation(world: Prototype) -> void:
	for op in boss_death_draw_ops(world):
		_draw_death_op(op)
	for op in boss_celebration_draw_ops(world):
		_draw_intro_op(op)


## Layer 9bg: ops of one explosion (flash discs, then its sparks) / one spark.
func death_explosion_draw_ops(explosion) -> Array:
	return DeathExplosionLayout.ops(explosion)


func hit_particle_draw_ops(particle) -> Array:
	return HitParticleLayout.ops(particle)


## Layer 9bf: the `_draw_death_sequence()` op list.
func boss_death_draw_ops(world: Prototype) -> Array:
	var anim = world.boss_death
	if anim == null:
		return []
	return BossDeathSequenceLayout.ops(anim)


## Death sequence ops. `flash` is additive in the source; it is approximated with
## an alpha blend. A ring wider than its radius is a filled disc in pygame, a
## `covered` ring or disc is hidden by a later one, and a polygon with a width is
## the 1 px edge of the fragment.
func _draw_death_op(op: Dictionary) -> void:
	var kind := String(op.get("kind", ""))
	if kind == "flash":
		var alpha := clampf(float(op.get("alpha", 0)) / 255.0, 0.0, 1.0)
		draw_rect(Rect2(Vector2.ZERO, Vector2(1280.0, 720.0)), Color(1.0, 1.0, 1.0, alpha))
	elif kind == "polygon" and int(op.get("width", 0)) > 0:
		_draw_polygon_edge(op)
	elif kind == "circle" and bool(op.get("covered", false)):
		return
	elif kind == "circle" and int(op.get("width", 0)) > int(op.get("radius", 0)):
		var filled: Dictionary = op.duplicate()
		filled["width"] = 0
		_draw_intro_op(filled)
	else:
		_draw_intro_op(op)


func _draw_polygon_edge(op: Dictionary) -> void:
	var color := _intro_color(op)
	var points := PackedVector2Array()
	for point in op.get("points", []):
		points.append(Vector2(float(point[0]), float(point[1])))
	if color.a <= 0.0 or points.size() < 3:
		return
	points.append(points[0])
	draw_polyline(points, color, float(op.get("width", 1)))


## Layer 9be: the `_draw_celebration()` op list. `ticks` defaults to the engine
## clock and `measure` to the real HUD font; the checks pass the oracle's.
func boss_celebration_draw_ops(
	world: Prototype, ticks: int = -1, measure: Callable = Callable()
) -> Array:
	var anim = world.boss_death
	if anim == null:
		return []
	var clock: int = ticks if ticks >= 0 else Time.get_ticks_msec()
	var metrics: Callable = _measure_intro_text
	if measure.is_valid():
		metrics = measure
	return BossCelebrationLayout.ops(anim, clock, metrics)


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


## Layer 9bv2: `Game._draw_gold_hud`, the gold chip and mode badge at the top-left, painted
## unshaken before the boss banner like the source UI pass.
func _draw_gold_hud(world: Prototype) -> void:
	if not gold_hud_visible:
		return
	gold_hud_draws += 1
	for op in gold_hud_draw_ops(world):
		_draw_hud_op(op)


## Layer 9bv3: `ShopHints.draw`, the ITEM FORGE / HERO SHOP pills that open the source UI pass
## (unshaken, before the gold HUD). The world tick count stands in for `animation_time`.
func _draw_shop_hints(world: Prototype) -> void:
	for op in shop_hint_draw_ops(world):
		_draw_hud_op(op)


func shop_hint_draw_ops(world: Prototype, measure: Callable = Callable()) -> Array:
	var metrics: Callable = _measure_intro_text
	if measure.is_valid():
		metrics = measure
	return ShopHintLayout.ops(int(world.tick_count), metrics)


## Paints one source HUD op: `_vgrad` fills, rounded `draw.rect`s, then the shared painter.
func _draw_hud_op(op: Dictionary) -> void:
	match String(op.get("kind", "")):
		"vgrad":
			_draw_vgrad_op(op)
		"rect":
			_draw_round_rect_op(op)
		_:
			_draw_intro_op(op)


## `measure` defaults to the real HUD font; the checks pass the oracle's.
func gold_hud_draw_ops(world: Prototype, measure: Callable = Callable()) -> Array:
	var metrics: Callable = _measure_intro_text
	if measure.is_valid():
		metrics = measure
	return GoldHudLayout.ops(
		int(world.economy.gold[0]),
		float(world.economy.income_per_second),
		String(world.difficulty),
		metrics
	)


## `ui_theme._vgrad`: one row per pixel, `int(top + (bottom - top) * y / (h - 1))`, masked by
## the rounded rect (each row is inset by the corner circle).
func _draw_vgrad_op(op: Dictionary) -> void:
	var box: Array = op.get("rect", [0, 0, 0, 0])
	var top: Array = op.get("top", [0, 0, 0])
	var bottom: Array = op.get("bottom", [0, 0, 0])
	var width := float(box[2])
	var height := int(box[3])
	var radius := float(op.get("radius", 0))
	for row in range(height):
		var t := float(row) / float(maxi(1, height - 1))
		var color := Color8(
			int(top[0] + (bottom[0] - top[0]) * t),
			int(top[1] + (bottom[1] - top[1]) * t),
			int(top[2] + (bottom[2] - top[2]) * t)
		)
		var inset := 0.0
		var from_edge := minf(float(row) + 0.5, float(height) - float(row) - 0.5)
		if radius > 0.0 and from_edge < radius:
			var rise := radius - from_edge
			inset = roundf(radius - sqrt(maxf(0.0, radius * radius - rise * rise)))
		if width - inset * 2.0 > 0.0:
			draw_rect(
				Rect2(float(box[0]) + inset, float(box[1]) + row, width - inset * 2.0, 1.0), color
			)


## A pygame rounded `draw.rect`: filled when `width` is 0, else a border drawn inside.
func _draw_round_rect_op(op: Dictionary) -> void:
	var box: Array = op.get("rect", [0, 0, 0, 0])
	var rgba: Array = op.get("color", [0, 0, 0, 255])
	var color := Color8(int(rgba[0]), int(rgba[1]), int(rgba[2]))
	var width := int(op.get("width", 0))
	hud_round_box.anti_aliasing = false
	hud_round_box.set_corner_radius_all(int(op.get("radius", 0)))
	hud_round_box.draw_center = width == 0
	hud_round_box.bg_color = color
	hud_round_box.set_border_width_all(width)
	hud_round_box.border_color = color
	draw_style_box(hud_round_box, Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3])))


## Layer 9bi2: `TacticalCommandManager.draw_world`, the gather marker and hero dashes.
## Every op is a `pygame.draw` call on the alpha-less render surface, so it is solid.
func _draw_tactical(world: Prototype) -> void:
	for op in tactical_world_draw_ops(world):
		_draw_solid_op(op)


## `ticks` defaults to the engine wall clock, as the source pulses with `get_ticks()`.
func tactical_world_draw_ops(world: Prototype, ticks: int = -1) -> Array:
	var tactical = world.tactical
	var heroes: Array = []
	for hero in world.player_roster():
		if hero.alive:
			heroes.append(hero.position)
	var clock: int = ticks if ticks >= 0 else Time.get_ticks_msec()
	return TacticalLayout.world_ops(
		String(tactical.active_command),
		tactical.gather_point,
		bool(tactical.gather_point_active),
		int(tactical.gather_point_timer),
		clock,
		heroes
	)


## Layer 9bi2: `TacticalCommandManager.draw_ui`, the feedback banner. `measure` defaults to
## the real HUD font; the checks pass the oracle's.
func tactical_feedback_draw_ops(world: Prototype, measure: Callable = Callable()) -> Array:
	var tactical = world.tactical
	var metrics: Callable = _measure_intro_text
	if measure.is_valid():
		metrics = measure
	var color: Color = tactical.feedback_color
	return TacticalLayout.feedback_ops(
		String(tactical.feedback_text),
		[color.r8, color.g8, color.b8],
		int(tactical.feedback_timer),
		metrics
	)


## The box and both texts fade through their alpha; the border is a `pygame.draw.rect` on
## the alpha-less screen, so it stays solid while the banner shows.
func _draw_tactical_feedback(world: Prototype) -> void:
	for op in tactical_feedback_draw_ops(world):
		if String(op.get("kind", "")) != "rect":
			_draw_intro_op(op)
			continue
		var box: Array = op.get("rect", [0, 0, 0, 0])
		var rgba: Array = op.get("color", [255, 255, 255, 255])
		tactical_border.draw_center = false
		tactical_border.set_border_width_all(int(op.get("width", 2)))
		tactical_border.set_corner_radius_all(int(op.get("radius", 6)))
		tactical_border.border_color = Color8(int(rgba[0]), int(rgba[1]), int(rgba[2]))
		draw_style_box(
			tactical_border, Rect2(float(box[0]), float(box[1]), float(box[2]), float(box[3]))
		)


## A `pygame.draw` op on the XRGB render surface: same colour, alpha dropped.
func _draw_solid_op(op: Dictionary) -> void:
	var rgba: Array = op.get("color", [255, 255, 255, 255])
	var solid := op.duplicate()
	solid["color"] = [rgba[0], rgba[1], rgba[2], 255]
	solid["mult"] = 255
	_draw_intro_op(solid)


func _draw_unit(unit: UnitState) -> void:
	if unit is BossState:
		_draw_boss(unit as BossState)
		return
	if not unit.is_hero:
		super._draw_unit(unit)
		return
	var hero := unit as HeroState
	if _draw_hero_sprite(hero):
		return
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


## Layer 9bo: the baked source body of a kit hero with the live parts `Hero.draw` paints
## around it. False when the hero is not baked or its sheet is not imported, so the marker
## above still draws.
func _draw_hero_sprite(hero: HeroState) -> bool:
	var clocks := hero_anim.observe(hero, session.world.tick_count)
	var moving := bool(clocks["moving"])
	var pulse := float(clocks["pulse"])
	var pose := HeroAnim.pose_key(
		hero.attack_timer, moving, pulse, hero.active_skill, hero.active_skill_timer
	)
	var art := HeroArt.frame(hero.definition.id, hero.team, pose, hero.facing)
	if art.is_empty() and not hero.active_skill.is_empty():
		# A renderer without a special skill body keeps its normal source animation.
		pose = HeroAnim.pose_key(hero.attack_timer, moving, pulse)
		art = HeroArt.frame(hero.definition.id, hero.team, pose, hero.facing)
	if art.is_empty():
		return false
	HeroPainter.paint(self, hero, art, hero.id == session.selected_id)
	return true


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
	# Layer 9bq3: the source paints nyxareth's ultimate realm inside its draw function, over
	# everything drawn before the boss and under the body (the baked atlas leaves it out).
	var realm_ops := nyxareth_realm_draw_ops(boss)
	if not realm_ops.is_empty():
		boss_screen_layer_draws += 1
		for op in realm_ops:
			_draw_realm_op(op)

	var bar_width := 70.0 if is_true else 60.0
	var bar_height := 10.0 if is_true else 8.0
	var bar_top := point.y - radius - 16.0
	var pose := BossAnim.from_boss(boss)
	var art := BossArt.frame(boss.boss_type, boss.direction, pose)
	if art.is_empty():
		_draw_boss_plain(boss)
	else:
		_draw_boss_sprite(boss, art)
		# `Boss.draw`: the bar sits 6 px above the sprite top (`BOSS_LABEL_TOP`).
		var head_top := float(BossArt.label_top(boss.boss_type, int(radius)))
		bar_top = point.y - head_top - 6.0 - bar_height
	var bar_position := Vector2(point.x - bar_width * 0.5, bar_top)
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


## Layer 9bq3: `_draw_astro_realm_bg` ops while nyxareth's ultimate "4" runs, from the live
## skill timer and pulse; empty for every other boss and skill.
func nyxareth_realm_draw_ops(boss: BossState) -> Array:
	if not NyxarethRealmLayout.active(boss.boss_type, boss.active_skill):
		return []
	return NyxarethRealmLayout.ops(
		boss.active_skill_timer, boss.pulse, NyxarethRealmLayout.SCREEN_SIZE
	)


## The cosmic layer is an SRCALPHA surface blitted onto the screen, so it blends; the stars
## are `pygame.draw` calls straight onto the alpha-less render surface, which keeps their
## colour and drops the alpha.
func _draw_realm_op(op: Dictionary) -> void:
	if String(op.get("kind", "")) != "rect" or not NyxarethRealmLayout.OPAQUE_STARS:
		_draw_intro_op(op)
		return
	var rgba: Array = op.get("color", [255, 255, 255, 255])
	var solid := op.duplicate()
	solid["color"] = [rgba[0], rgba[1], rgba[2], 255]
	solid["mult"] = 255
	_draw_intro_op(solid)


## The Godot fallback body for a boss whose sheet is not baked or not imported.
func _draw_boss_plain(boss: BossState) -> void:
	var point := boss.position
	var radius := boss.radius
	var is_true := boss.boss_class == "true"
	# Gameplay and the source entrance/enrage states stay shared with the baked body.
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


## Layer 9bq: `Boss.draw` after the auras - the solid ground shadow, then the baked body at
## `(int(x) - ax, int(y) - ay)`. A fresh hit brightens the body like the minion sprites.
func _draw_boss_sprite(boss: BossState, art: Dictionary) -> void:
	boss_sprite_draws += 1
	var pose := String(art.get("pose", ""))
	boss_pose_draws[pose] = int(boss_pose_draws.get(pose, 0)) + 1
	var x := int(boss.position.x)
	var y := int(boss.position.y)
	var radius := int(boss.radius)
	var shadow_width := radius * 2 + (10 if boss.boss_class == "true" else 0)
	var shadow := Rect2(x - (shadow_width >> 1), y + radius - 5, shadow_width, 12)
	draw_colored_polygon(HeroPainter.ellipse(shadow), HeroPainter.SHADOW)
	var src: Rect2 = art["src"]
	var anchor: Vector2 = art["anchor"]
	var tint := Color(1.6, 1.6, 1.6) if boss.hurt_flash_timer > 0 else Color.WHITE
	var corner := Vector2(x, y) - anchor
	draw_texture_rect_region(art["texture"] as Texture2D, Rect2(corner, src.size), src, tint)


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
