extends "res://scenes/combat/minion_view.gd"

const Siege = preload("res://scripts/combat/siege_battle.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")
const StructureArt = preload("res://scripts/ui/structure_art.gd")
const StructureAnim = preload("res://scripts/ui/structure_anim.gd")
const BulletArt = preload("res://scripts/ui/bullet_art.gd")
const HudFont = preload("res://assets/fonts/Barlow-SemiBold.ttf")
## `_entity.py` bar colours: SHIELD_COLOR_*, CASTLE_SHIELD_COLOR_*, GREEN / YELLOW / RED.
const TOWER_SHIELD_BLUE := Color(100 / 255.0, 180 / 255.0, 255 / 255.0)
const TOWER_SHIELD_RED := Color(255 / 255.0, 100 / 255.0, 100 / 255.0)
const CASTLE_SHIELD_BLUE := Color(100 / 255.0, 200 / 255.0, 255 / 255.0)
const CASTLE_SHIELD_RED := Color(255 / 255.0, 120 / 255.0, 120 / 255.0)
const BAR_BACK_SHIELD := Color(30 / 255.0, 30 / 255.0, 50 / 255.0)
const BAR_BACK_HP := Color(40 / 255.0, 0 / 255.0, 0 / 255.0)
const BAR_GREEN := Color(50 / 255.0, 200 / 255.0, 50 / 255.0)
const BAR_YELLOW := Color(255 / 255.0, 220 / 255.0, 0 / 255.0)
const BAR_RED := Color(220 / 255.0, 50 / 255.0, 50 / 255.0)
const BADGE_YELLOW := Color(255 / 255.0, 220 / 255.0, 0 / 255.0)
const TOWER_BAR_WIDTH := 44
const TOWER_BAR_HEIGHT := 5
var structure_anim := StructureAnim.new()


func _draw() -> void:
	super._draw()
	if session == null:
		return
	var world := session.world as Siege
	for shot in world.projectiles:
		if shot.active:
			_draw_shot(world, shot)


## Layer 9bp: `Bullet.draw` - the baked sprite blitted at `(int(x - ax), int(y - ay))`, the
## arrow turned toward its target. The old dot draws when the sheet is not imported.
func _draw_shot(world: Siege, shot) -> void:
	var bearing := 0.0
	if shot.kind == "normal":
		var target := world.get_unit(shot.target_id)
		if target != null and target.alive:
			bearing = (target.position - shot.position).angle()
	var art := BulletArt.frame(shot.kind, shot.team, bearing)
	if art.is_empty():
		var color := Color("c0f3dc") if shot.team == 0 else Color("ffd1af")
		draw_circle(shot.position, 4, color)
		return
	var src: Rect2 = art["src"]
	var anchor: Vector2 = art["anchor"]
	var corner := Vector2(int(shot.position.x - anchor.x), int(shot.position.y - anchor.y))
	draw_texture_rect_region(art["texture"] as Texture2D, Rect2(corner, src.size), src)


func _draw_structures() -> void:
	var world := session.world as Siege
	structure_anim.prune(world.structures)
	for structure in world.structures:
		_draw_structure(structure)


func _draw_base(_point: Vector2, _color: Color) -> void:
	# The siege uses real structure states rather than the minion lab's decorative bases.
	pass


func _draw_structure(structure: Structure) -> void:
	if not _draw_structure_art(structure):
		_draw_structure_plain(structure)


## Layer 9bl: the baked source sprite plus the live parts `Tower.draw` / `Castle.draw`
## paint around it. False when the art is unavailable, so the plain boxes still draw.
func _draw_structure_art(structure: Structure) -> bool:
	var data := structure.settings()
	var tick: int = session.world.tick_count
	var art: Dictionary = {}
	var nexus := data.structure_kind == "nexus"
	if nexus:
		art = StructureArt.castle_frame(structure.team, data.level, StructureAnim.flicker(tick))
	else:
		var flash := int(structure_anim.observe(structure, tick)["flash"])
		art = StructureArt.tower_frame(
			data.tower_path,
			structure.team,
			data.level,
			_target_is_right(structure),
			StructureAnim.shoot_b(flash)
		)
	if art.is_empty():
		return false
	_draw_structure_selection(structure, data)
	var src: Rect2 = art["src"]
	var corner := structure.position - (art["anchor"] as Vector2)
	corner = Vector2(int(corner.x), int(corner.y))
	draw_texture_rect_region(art["texture"] as Texture2D, Rect2(corner, src.size), src)
	if nexus:
		_draw_castle_extras(structure, corner)
	else:
		_draw_tower_extras(structure, data, tick)
	return true


## `Tower._draw_tower_body`: the sprite faces right when its living target is to the right.
func _target_is_right(structure: Structure) -> int:
	if structure.target_id == -1:
		return 0
	var target := session.world.get_unit(structure.target_id)
	if target != null and target.alive and target.position.x > structure.position.x:
		return 1
	return 0


func _draw_structure_selection(structure: Structure, data) -> void:
	if structure.id != session.selected_id:
		return
	var color := Color("73cbbb") if structure.team == 0 else Color("d78579")
	draw_arc(structure.position, data.attack_range_px, 0, TAU, 90, Color(color, 0.4), 1.5, true)
	draw_arc(structure.position, data.radius_px + 8, 0, TAU, 40, Color("f4d491"), 2, true)


func _blit_art(art: Dictionary, anchor_point: Vector2) -> void:
	var src: Rect2 = art["src"]
	var corner := anchor_point - (art["anchor"] as Vector2)
	corner = Vector2(int(corner.x), int(corner.y))
	draw_texture_rect_region(art["texture"] as Texture2D, Rect2(corner, src.size), src)


## `Tower.draw`: armor crest, shield bar over HP bar, level badge, regen plus.
func _draw_tower_extras(structure: Structure, data, tick: int) -> void:
	var x := int(structure.position.x)
	var y := int(structure.position.y)
	var blue := structure.team == 0
	var shield_ratio := 0.0
	if structure.shield_max > 0.0:
		shield_ratio = clampf(structure.shield / structure.shield_max, 0.0, 1.0)
	if structure.shield > 0.0:
		var crest := StructureArt.crest_frame(14, structure.team, shield_ratio, false)
		if not crest.is_empty():
			_blit_art(crest, Vector2(x + 26, y - 28 - data.level))
	var left := x - (TOWER_BAR_WIDTH >> 1)
	var top := y + StructureArt.tower_top_y(data.tower_path, data.level) - 14
	var shield_top := top - TOWER_BAR_HEIGHT - 2
	var shield_ink := TOWER_SHIELD_BLUE if blue else TOWER_SHIELD_RED
	_draw_source_bar(left, shield_top, shield_ratio, BAR_BACK_SHIELD, shield_ink, 80)
	var hp_ratio := clampf(structure.hp / maxf(1.0, float(data.max_hp)), 0.0, 1.0)
	var hp_ink := BAR_GREEN
	if hp_ratio <= 0.3:
		hp_ink = BAR_RED
	elif hp_ratio <= 0.6:
		hp_ink = BAR_YELLOW
	_draw_source_bar(left, top, hp_ratio, BAR_BACK_HP, hp_ink, 60)
	_draw_level_badge(str(data.level), left, top)
	var hurt := structure.hp < float(data.max_hp) or structure.shield < structure.shield_max
	if structure.no_damage_ticks >= data.shield_regen_delay_ticks and hurt:
		_draw_regen_plus(left + TOWER_BAR_WIDTH + 2, top, tick)


## One 44x5 bar: back, fill, a lighter top half, then a 1 px black border.
func _draw_source_bar(
	left: int, top: int, ratio: float, back: Color, ink: Color, shine_lift: int
) -> void:
	draw_rect(Rect2(left, top, TOWER_BAR_WIDTH, TOWER_BAR_HEIGHT), back)
	var fill := int(float(TOWER_BAR_WIDTH) * ratio)
	if fill > 0:
		draw_rect(Rect2(left, top, fill, TOWER_BAR_HEIGHT), ink)
		var lift := float(shine_lift) / 255.0
		var shine := Color(
			minf(1.0, ink.r + lift), minf(1.0, ink.g + lift), minf(1.0, ink.b + lift)
		)
		draw_rect(Rect2(left, top, fill, maxi(1, TOWER_BAR_HEIGHT >> 1)), shine)
	var edge := Rect2(left + 0.5, top + 0.5, TOWER_BAR_WIDTH - 1, TOWER_BAR_HEIGHT - 1)
	draw_rect(edge, Color.BLACK, false, 1.0)


## The level number in a black box with a yellow border, flush left of the bars.
func _draw_level_badge(text: String, bar_left: int, bar_top: int) -> void:
	var text_size := HudFont.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 14)
	var width := maxi(12, int(text_size.x) + 6)
	var height := maxi(TOWER_BAR_HEIGHT + 2, int(text_size.y) + 2)
	var left := bar_left - width - 2
	var top := bar_top + ((TOWER_BAR_HEIGHT - height) >> 1)
	draw_rect(Rect2(left, top, width, height), Color.BLACK)
	draw_rect(Rect2(left + 0.5, top + 0.5, width - 1, height - 1), BADGE_YELLOW, false, 1.0)
	var baseline := Vector2(
		left + (width - text_size.x) * 0.5,
		top + (height - text_size.y) * 0.5 + HudFont.get_ascent(14)
	)
	draw_string(HudFont, baseline, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, BADGE_YELLOW)


## `Tower._draw_regen_indicator`: a small pulsing green plus beside the HP bar.
func _draw_regen_plus(left: int, top: int, tick: int) -> void:
	var plus := Color8(100, 255, 100)
	var pulse := int(sin(float(tick) * 0.2) * 2.0) + 2
	var size := 3 + (pulse >> 1)
	draw_rect(Rect2(left + size - 1, top - (size >> 1), 2, size + 2), plus)
	draw_rect(Rect2(left + (size >> 1) - 1, top + (size >> 1) - 1, size + 2, 2), plus)
	draw_rect(Rect2(left + size, top, 1, 1), Color8(200, 255, 200))


## `Castle.draw`: the shield crest above the sprite, then the 60x6 shield bar and label.
func _draw_castle_extras(structure: Structure, corner: Vector2) -> void:
	if not structure.shield_active:
		return
	var ratio := 0.0
	if structure.shield_max > 0.0:
		ratio = clampf(structure.shield / structure.shield_max, 0.0, 1.0)
	if structure.shield > 0.0:
		var bob := int(sin(float(session.world.tick_count) * 0.05 * 1.2) * 2.0)
		var crest := StructureArt.crest_frame(18, structure.team, ratio, false)
		if not crest.is_empty():
			_blit_art(
				crest, Vector2(corner.x + (StructureArt.CASTLE_WIDTH >> 1), corner.y - 10 + bob)
			)
	if structure.shield_max <= 0.0:
		return
	var ink := CASTLE_SHIELD_BLUE if structure.team == 0 else CASTLE_SHIELD_RED
	var left := int(structure.position.x) - 30
	var top := int(structure.position.y) - 80
	_draw_pill(Rect2(left, top, 60, 6), BAR_BACK_SHIELD)
	var fill := int(60.0 * ratio)
	if fill > 0:
		_draw_pill(Rect2(left, top, fill, 6), ink)
	draw_rect(Rect2(left + 0.5, top + 0.5, 59, 5), Color.BLACK, false, 1.0)
	var label := "SHIELD %d%%" % int(ratio * 100.0)
	var ascent := HudFont.get_ascent(10)
	var spot := Vector2(left, top - 12 + ascent)
	draw_string(HudFont, spot, label, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color8(200, 220, 255))


## A fully rounded bar (`border_radius=3` on a 6 px bar), clamped for short fills.
func _draw_pill(rect: Rect2, color: Color) -> void:
	var radius := minf(3.0, minf(rect.size.x, rect.size.y) * 0.5)
	if rect.size.x <= radius * 2.0:
		draw_rect(rect, color)
		return
	draw_rect(
		Rect2(rect.position.x + radius, rect.position.y, rect.size.x - radius * 2.0, rect.size.y),
		color
	)
	var mid := rect.position.y + rect.size.y * 0.5
	draw_circle(Vector2(rect.position.x + radius, mid), radius, color)
	draw_circle(Vector2(rect.position.x + rect.size.x - radius, mid), radius, color)


func _draw_structure_plain(structure: Structure) -> void:
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
	for tier in range(data.level):
		draw_circle(point + Vector2((tier - (data.level - 1) * 0.5) * 6, 9), 2, color)
	var width := radius * 2
	var health := structure.hp / data.max_hp
	var shield := structure.shield / maxf(1, structure.shield_max)
	draw_rect(Rect2(point + Vector2(-radius, -radius - 22), Vector2(width, 5)), Color("08171c"))
	draw_rect(Rect2(point + Vector2(-radius, -radius - 22), Vector2(width * health, 5)), color)
	if structure.shield_active:
		draw_rect(Rect2(point + Vector2(-radius, -radius - 15), Vector2(width, 3)), Color("08171c"))
		draw_rect(
			Rect2(point + Vector2(-radius, -radius - 15), Vector2(width * shield, 3)),
			Color("92c7ff")
		)
