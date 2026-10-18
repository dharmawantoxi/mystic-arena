extends RefCounted
## Layer 9bd: the DRAW of `_render.py::BossIntroCinematic` as a pure op list.
##
## `ops()` replays `BossIntroCinematic.draw()` against the ported state
## (`boss_intro_cinematic.gd` already holds the fade, slide and bar curves) and
## returns dictionaries in source order: the rounded banner fill and border, the
## eight gold corner ticks (only above alpha 60), the tag / name / quoted title
## text, then the HP bar track, fill and outline:
##   rect {rect, color, mult, width, radius}; line {a, b, color, mult, width};
##   text {text, size, style, color, mult, pos}.
## `color` is RGBA 0..255 and `mult` the pygame surface alpha (255 = opaque).
## The source never measures a font here, so no metrics are needed. The HP bar
## goes straight onto the screen: unlike the banner it does not fade.
## `boss_intro_draw_source_oracle.py` pins every op.

const BossIntro = preload("res://scripts/ui/boss_intro_cinematic.gd")

const BANNER_RADIUS := 10
const BORDER_WIDTH := 2
const BG_RGB := [10, 10, 18]
const TICK_RGB := [255, 220, 120]
const TICK_LENGTH := 12
const TICK_WIDTH := 2
const TICK_INSET := 5
const TICK_MIN_ALPHA := 60
const TEXT_INSET := 14
const TAG_TOP := 8
const NAME_TOP := 26
const TITLE_TOP := 64
const TAG_SIZE := 24
const NAME_SIZE := 46
const TITLE_SIZE := 24
const BODY_STYLE := "body_medium"
const NAME_STYLE := "title"
const TITLE_RGB := [215, 215, 235]
const BAR_RADIUS := 5
const BAR_BACK_RGB := [40, 8, 12]
const BAR_OUTLINE_RGB := [255, 255, 255]
const BAR_OUTLINE_WIDTH := 1


## One frame of `draw()` for a `BossIntroCinematic` port; empty once inactive.
static func ops(intro) -> Array:
	var result: Array = []
	if not intro.is_active():
		return result
	var alpha: int = intro.get_alpha()
	var ink: Array = intro.get_entrance_color()
	var banner := [
		intro.get_banner_x(), intro.get_banner_y(), intro.get_banner_width(), BossIntro.BANNER_H
	]
	var back: int = intro.get_background_alpha()
	result.append(_rect_op(banner, _rgba(BG_RGB, back), 0, BANNER_RADIUS))
	result.append(_rect_op(banner, _rgba(ink, alpha), BORDER_WIDTH, BANNER_RADIUS))
	if alpha > TICK_MIN_ALPHA:
		result.append_array(_corner_ticks(banner))
	result.append_array(_text_ops(intro, banner, alpha, ink))
	result.append_array(_bar_ops(intro, ink))
	return result


## Mirror of `ui_theme.corner_ticks(rect, (255, 220, 120), 12, 2, 5)`.
static func _corner_ticks(box: Array) -> Array:
	var left: int = int(box[0]) + TICK_INSET
	var top: int = int(box[1]) + TICK_INSET
	var right: int = int(box[0]) + int(box[2]) - TICK_INSET
	var bottom: int = int(box[1]) + int(box[3]) - TICK_INSET
	var corners := [
		[left, top, 1, 1], [right, top, -1, 1], [left, bottom, 1, -1], [right, bottom, -1, -1]
	]
	var result: Array = []
	for corner in corners:
		var ax: int = corner[0]
		var ay: int = corner[1]
		var run: int = int(corner[2]) * TICK_LENGTH
		var rise: int = int(corner[3]) * TICK_LENGTH
		result.append(_line_op([ax, ay], [ax + run, ay]))
		result.append(_line_op([ax, ay], [ax, ay + rise]))
	return result


static func _text_ops(intro, box: Array, alpha: int, ink: Array) -> Array:
	var tag: Dictionary = intro.get_tag()
	var left: int = int(box[0]) + TEXT_INSET
	var top: int = int(box[1])
	var title: String = '"%s"' % intro.boss_title
	return [
		_text_op(
			String(tag["text"]), TAG_SIZE, BODY_STYLE, tag["color"], alpha, [left, top + TAG_TOP]
		),
		_text_op(intro.boss_name, NAME_SIZE, NAME_STYLE, ink, alpha, [left, top + NAME_TOP]),
		_text_op(title, TITLE_SIZE, BODY_STYLE, TITLE_RGB, alpha, [left, top + TITLE_TOP]),
	]


static func _bar_ops(intro, ink: Array) -> Array:
	var bar: Array = intro.get_hp_bar_rect()
	var fill: int = intro.get_hp_fill_width()
	var result: Array = [_rect_op(bar, _rgba(BAR_BACK_RGB, 255), 0, BAR_RADIUS)]
	if fill > 0:
		var filled := [bar[0], bar[1], fill, bar[3]]
		result.append(_rect_op(filled, _rgba(ink, 255), 0, BAR_RADIUS))
	result.append(_rect_op(bar, _rgba(BAR_OUTLINE_RGB, 255), BAR_OUTLINE_WIDTH, BAR_RADIUS))
	return result


static func _rgba(rgb: Array, alpha: int) -> Array:
	return [int(rgb[0]), int(rgb[1]), int(rgb[2]), alpha]


static func _rect_op(box: Array, color: Array, width: int, radius: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
		"color": color,
		"mult": 255,
		"width": width,
		"radius": radius,
	}


static func _line_op(from: Array, to: Array) -> Dictionary:
	return {
		"kind": "line",
		"a": from,
		"b": to,
		"color": _rgba(TICK_RGB, 255),
		"mult": 255,
		"width": TICK_WIDTH,
	}


static func _text_op(
	text: String, size: int, style: String, rgb: Array, alpha: int, at: Array
) -> Dictionary:
	return {
		"kind": "text",
		"text": text,
		"size": size,
		"style": style,
		"color": _rgba(rgb, 255),
		"mult": alpha,
		"pos": at,
	}
