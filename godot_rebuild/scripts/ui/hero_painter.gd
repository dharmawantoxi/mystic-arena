extends RefCounted
## Layer 9bo: paints one hero the way `_entity.py::Hero.draw` does around the baked body:
## selection ellipse and range disc, ground shadow, the sprite, the 45x6 HP bar at
## `y - max(radius, sprite_top) - 6`, the name badge with level stars right above it and the
## skill cooldown strip under the feet. The caller passes its CanvasItem; every call happens
## inside that item's `_draw`.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const HeroArt = preload("res://scripts/ui/hero_art.gd")
const DebuffFxPainter = preload("res://scripts/ui/debuff_fx_painter.gd")
const HudFont = preload("res://assets/fonts/Barlow-SemiBold.ttf")
## `pygame.draw.ellipse(surface, (0, 0, 0, 100), ...)` on the display surface: pygame drops the
## alpha of a draw call on a surface without per-pixel alpha, so the source shadow is solid.
const SHADOW := Color(0, 0, 0)
const BAR_WIDTH := 45
const BAR_HEIGHT := 6
const NAME_SIZE := 14
const LEVEL_SIZE := 13
const GREEN := Color(50 / 255.0, 200 / 255.0, 50 / 255.0)
const YELLOW := Color(255 / 255.0, 220 / 255.0, 0 / 255.0)
const RED := Color(220 / 255.0, 50 / 255.0, 50 / 255.0)
const ORANGE := Color(255 / 255.0, 140 / 255.0, 0 / 255.0)
const DARK_GRAY := Color(60 / 255.0, 60 / 255.0, 70 / 255.0)
const BAR_BACK := Color(40 / 255.0, 0 / 255.0, 0 / 255.0)
const STAR := [
	Vector2(0, -3),
	Vector2(2, 0),
	Vector2(4, 0),
	Vector2(2, 2),
	Vector2(3, 5),
	Vector2(0, 3),
	Vector2(-3, 5),
	Vector2(-2, 2),
	Vector2(-4, 0),
	Vector2(-2, 0),
]


## Layer 9bq10: `debuff_ops` is the shared tower-debuff indicator `Hero.draw` paints after the
## ground shadow and before the body; the caller builds it from the live timers.
static func paint(
	canvas: CanvasItem, hero: HeroState, art: Dictionary, selected: bool, debuff_ops: Array = []
) -> void:
	var facts := HeroArt.meta(hero.definition.id)
	var radius := int(facts.get("radius", 16))
	var point := Vector2(int(hero.position.x), int(hero.position.y))
	if selected:
		_paint_selection(canvas, hero, point, radius)
	var shadow := Rect2(point.x - radius, point.y + radius - 4, radius * 2, 8)
	canvas.draw_colored_polygon(_ellipse(shadow), SHADOW)
	DebuffFxPainter.paint(canvas, debuff_ops)
	var src: Rect2 = art["src"]
	var scale := float(art.get("scale", 1.0))
	var corner := point - (art["anchor"] as Vector2) * scale
	canvas.draw_texture_rect_region(
		art["texture"] as Texture2D, Rect2(corner, src.size * scale), src
	)
	var anchor := int(point.y) - maxi(radius, int(facts.get("top_offset", radius))) - 6
	var left := int(point.x) - (BAR_WIDTH >> 1)
	_paint_health(canvas, hero, left, anchor)
	_paint_badge(canvas, hero, String(facts.get("name", "")), int(point.x), anchor)
	_paint_cooldown(canvas, hero, left, int(point.y) + radius + 8)


static func _team_color(hero: HeroState) -> Color:
	return Color("73cbbb") if hero.team == 0 else Color("d78579")


## The yellow ground ellipse and the translucent attack-range disc of a selected hero.
static func _paint_selection(
	canvas: CanvasItem, hero: HeroState, point: Vector2, radius: int
) -> void:
	var ink := _team_color(hero)
	canvas.draw_circle(point, hero.attack_range, Color(ink, 30.0 / 255.0))
	canvas.draw_arc(point, hero.attack_range, 0, TAU, 90, Color(ink, 100.0 / 255.0), 2.0, true)
	var ring := Rect2(point.x - radius - 3, point.y + radius - 6, (radius + 3) * 2, 10)
	var points := _ellipse(ring)
	points.append(points[0])
	canvas.draw_polyline(points, YELLOW, 2.0, true)


## The polygon `pygame.draw.ellipse` fills inside `rect`; the boss shadow shares it.
static func ellipse(rect: Rect2) -> PackedVector2Array:
	return _ellipse(rect)


static func _ellipse(rect: Rect2) -> PackedVector2Array:
	var points := PackedVector2Array()
	var center := rect.get_center()
	for step in range(28):
		var angle := TAU * float(step) / 28.0
		points.append(
			center + Vector2(cos(angle) * rect.size.x * 0.5, sin(angle) * rect.size.y * 0.5)
		)
	return points


static func _paint_health(canvas: CanvasItem, hero: HeroState, left: int, top: int) -> void:
	canvas.draw_rect(Rect2(left, top, BAR_WIDTH, BAR_HEIGHT), BAR_BACK)
	var ratio := clampf(hero.hp / maxf(1.0, hero.max_hp), 0.0, 1.0)
	var fill := int(float(BAR_WIDTH) * ratio)
	if fill > 0:
		var ink := GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
		canvas.draw_rect(Rect2(left, top, fill, BAR_HEIGHT), ink)
	var edge := Rect2(left + 0.5, top + 0.5, BAR_WIDTH - 1, BAR_HEIGHT - 1)
	canvas.draw_rect(edge, Color.WHITE, false, 1.0)


## `Hero._build_name_badge`: black name box with up to five stars above it, or one star and
## `x<level>` past level 5; sits 3 px above the HP bar.
static func _paint_badge(
	canvas: CanvasItem, hero: HeroState, text: String, center_x: int, bar_top: int
) -> void:
	var level := hero.level
	var name_size := HudFont.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, NAME_SIZE)
	var star_width := level * 10 if level <= 5 else 18
	var width := maxi(int(name_size.x), star_width) + 8
	var name_height := int(name_size.y) + 4
	var height := 12 + name_height
	var origin := Vector2(center_x - (width >> 1), bar_top - height - 3)
	var box := Rect2(origin.x, origin.y + height - name_height, width, name_height)
	canvas.draw_rect(box, Color.BLACK)
	var baseline := Vector2(
		box.position.x + (width - name_size.x) * 0.5,
		box.position.y + (name_height - name_size.y) * 0.5 + HudFont.get_ascent(NAME_SIZE)
	)
	canvas.draw_string(
		HudFont, baseline, text, HORIZONTAL_ALIGNMENT_LEFT, -1, NAME_SIZE, Color.WHITE
	)
	if level <= 5:
		for index in range(level):
			_paint_star(canvas, origin + Vector2((width >> 1) - (level - 1) * 5 + index * 10, 5))
		return
	var label := "x%d" % level
	var label_width := HudFont.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, LEVEL_SIZE).x
	var total := 9 + int(label_width)
	_paint_star(canvas, origin + Vector2((width >> 1) - (total >> 1) + 4, 5))
	var spot := origin + Vector2((width >> 1) - (total >> 1) + 11, HudFont.get_ascent(LEVEL_SIZE))
	canvas.draw_string(HudFont, spot, label, HORIZONTAL_ALIGNMENT_LEFT, -1, LEVEL_SIZE, YELLOW)


static func _paint_star(canvas: CanvasItem, center: Vector2) -> void:
	var points := PackedVector2Array()
	for offset in STAR:
		points.append(center + (offset as Vector2))
	canvas.draw_colored_polygon(points, YELLOW)


## Skill strip under the feet: orange fill while Q recharges, a full yellow bar when ready.
static func _paint_cooldown(canvas: CanvasItem, hero: HeroState, left: int, top: int) -> void:
	if hero.skill_timer > 0 and hero.skill_cd_max > 0:
		var ratio := 1.0 - float(hero.skill_timer) / float(hero.skill_cd_max)
		canvas.draw_rect(Rect2(left, top, BAR_WIDTH, 3), DARK_GRAY)
		canvas.draw_rect(Rect2(left, top, int(float(BAR_WIDTH) * ratio), 3), ORANGE)
		return
	canvas.draw_rect(Rect2(left, top, BAR_WIDTH, 3), YELLOW)
