extends RefCounted
## Layer 9bv8: the selected-hero panel (`HeroPanel.draw`) and its six inventory slots.
## The source's cached gradients / radial glows / shadow are kept as one op each;
## pygame primitives (rects, lines, text and procedural item icons) stay in source order.

const PANEL_W := 280
const PANEL_H := 276
const SCREEN_H := 720
const PANEL_X := 20
const TITLE_SIZE := 24
const TINY_SIZE := 20
const SKILL_SIZE := 38
const SKILL_GAP := 10
const ITEM_SIZE := 30
const ITEM_GAP := 4
const ITEM_COUNT := 6
const ITEM_ROW_W := ITEM_SIZE * ITEM_COUNT + ITEM_GAP * (ITEM_COUNT - 1)
const ITEM_ICON_SIZE := 26
const DEFAULT_HERO_COLOR := [115, 203, 187]
const PANEL_TOP := [30, 37, 66]
const PANEL_FILL := [21, 26, 48]
const GOLD := [255, 205, 85]
const GOLD_TEXT := [255, 220, 110]
const TEXT_WHITE := [240, 244, 255]
const TEXT_BODY := [198, 207, 230]
const TEXT_DIM := [132, 142, 170]
const SLATE := [148, 158, 188]
const WHITE := [255, 255, 255]
const RED := [220, 50, 50]

var _ops: Array = []
var _state: Dictionary = {}
var _measure: Callable
var _cheap_alpha := true
var _ticks_msec := 0


## `state` is the display-only snapshot supplied by PrototypeScreen. `measure` is the
## same font-metric callback used by the other screen-space layouts.
static func ops(
	state: Dictionary, measure: Callable = Callable(), cheap_alpha: bool = true, ticks_msec: int = 0
) -> Array:
	if state.is_empty() or not bool(state.get("alive", true)):
		return []
	var layout := new()
	layout._state = state
	layout._measure = measure
	layout._cheap_alpha = cheap_alpha
	layout._ticks_msec = ticks_msec
	layout._draw()
	return layout._ops


## Fallback is the source's bottom-left anchor; the optional point is the mobile helper's
## `panel_pos_bawah(280, 276)` result, recorded by the source oracle.
static func origin(state: Dictionary) -> Vector2i:
	var supplied: Variant = state.get("panel_pos", null)
	if supplied is Array and supplied.size() >= 2:
		return Vector2i(int(supplied[0]), int(supplied[1]))
	if supplied is Vector2i:
		return supplied
	return Vector2i(PANEL_X, SCREEN_H - PANEL_H - 20)


## Exact geometry of `mobile.platform_utils.panel_pos_bawah(280, 276)` for the wide-screen dock.
static func mobile_panel_origin(panel: Rect2i) -> Variant:
	if panel.size.x <= 0 or PANEL_W > panel.size.x - 8:
		return null
	var x := panel.position.x + int((panel.size.x - PANEL_W) / 2)
	var y := panel.position.y + 430
	var bottom := panel.position.y + panel.size.y
	if y + PANEL_H > bottom - 120:
		y = maxi(panel.position.y + 8, bottom - 120 - PANEL_H)
	return Vector2i(x, y)


static func panel_rect(state: Dictionary) -> Rect2i:
	return Rect2i(origin(state), Vector2i(PANEL_W, PANEL_H))


static func close_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	return Rect2i(at + Vector2i(PANEL_W - 26, 6), Vector2i(22, 22))


static func autocast_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	return Rect2i(at + Vector2i(10, 118), Vector2i(PANEL_W - 20, 22))


static func item_slot_rect(state: Dictionary, index: int) -> Rect2i:
	var at := origin(state)
	var start_x := at.x + int((PANEL_W - ITEM_ROW_W) / 2)
	return Rect2i(
		Vector2i(start_x + index * (ITEM_SIZE + ITEM_GAP), at.y + 148),
		Vector2i(ITEM_SIZE, ITEM_SIZE)
	)


static func item_shop_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	return Rect2i(at + Vector2i(10, 186), Vector2i(PANEL_W - 20, 22))


static func upgrade_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	return Rect2i(at + Vector2i(10, 214), Vector2i(PANEL_W - 20, 22))


func _draw() -> void:
	var at := origin(_state)
	var px := at.x
	var py := at.y
	var hero_color := _rgb(_state.get("color", DEFAULT_HERO_COLOR), DEFAULT_HERO_COLOR)
	_panel(px, py, hero_color)
	_title(px, py)
	_close_button(px, py)
	_hp_bar(px, py)
	_skill_slots(px, py, hero_color)
	_autocast_toggle(px, py)
	_item_slots(px, py)
	_item_shop_button(px, py)
	_upgrade_button(px, py)


func _panel(px: int, py: int, hero_color: Array) -> void:
	var border := [
		mini(255, int(hero_color[0]) + 30),
		mini(255, int(hero_color[1]) + 30),
		mini(255, int(hero_color[2]) + 30),
	]
	if _cheap_alpha:
		_ops.append(_shadow(PANEL_W, PANEL_H, 12, 110, px - 4, py - 4))
		_ops.append(_vgrad([px, py, PANEL_W, PANEL_H], PANEL_TOP, [12, 15, 30], 12))
	else:
		_ops.append(_rect([px + 3, py + 4, PANEL_W, PANEL_H], [6, 7, 14, 255], 0, 12))
		_ops.append(_rect([px, py, PANEL_W, PANEL_H], PANEL_FILL, 0, 12))
	_ops.append(_rect([px, py, PANEL_W, PANEL_H], border, 2, 12))
	_corner_ticks(px, py, PANEL_W, PANEL_H, GOLD, 11)


func _title(px: int, py: int) -> void:
	var title := String(_state.get("name", ""))
	var title_max_w := PANEL_W - 84
	if _measure_text(title, TITLE_SIZE).x > title_max_w:
		title = _fit_ellipsis(title, title_max_w)
	var title_metrics := _measure_text(title, TITLE_SIZE)
	_ops.append(_text(title, TITLE_SIZE, TEXT_WHITE, [px + 12, py + 10], "body_medium"))
	var level := int(_state.get("level", 1))
	var level_text := "Lv.%d" % level
	var level_metrics := _measure_text(level_text, 16)
	_ops.append(
		_text(
			level_text,
			16,
			GOLD_TEXT,
			[px + 14 + title_metrics.x, py + 18 - int(level_metrics.y / 2)],
			"body_bold"
		)
	)


func _close_button(px: int, py: int) -> void:
	var rect := Rect2i(Vector2i(px + PANEL_W - 26, py + 6), Vector2i(22, 22))
	var mouse := _mouse()
	var hover := rect.has_point(mouse)
	if hover:
		_ops.append(_rect(_box(rect), [255, 60, 60], 0, 3))
		_ops.append(_rect(_box(rect), WHITE, 2, 3))
	else:
		_ops.append(_rect(_box(rect), RED, 0, 3))
		_ops.append(_rect(_box(rect), WHITE, 1, 3))
	var metrics := _measure_text("X", 28)
	var center := Vector2i(
		rect.position.x + int(rect.size.x / 2), rect.position.y + int(rect.size.y / 2)
	)
	_ops.append(
		_text(
			"X",
			28,
			WHITE,
			[center.x - int(metrics.x / 2), center.y - int(metrics.y / 2)],
			"body_semibold"
		)
	)


func _hp_bar(px: int, py: int) -> void:
	var hp := float(_state.get("hp", 0.0))
	var max_hp := float(_state.get("max_hp", 0.0))
	var ratio := hp / max_hp if max_hp != 0.0 else 0.0
	var bar_color := [120, 220, 120]
	if ratio <= 0.5:
		bar_color = [255, 200, 80] if ratio > 0.25 else [255, 100, 100]
	var x := px + 12
	var y := py + 34
	var width := PANEL_W - 24
	var height := 8
	_ops.append(_rect([x, y, width, height], [16, 18, 30], 0, height / 2))
	var fill_width := int(width * clampf(ratio, 0.0, 1.0))
	if fill_width > 3:
		if _cheap_alpha:
			var light := [
				mini(255, int(bar_color[0]) + 50),
				mini(255, int(bar_color[1]) + 50),
				mini(255, int(bar_color[2]) + 50),
			]
			_ops.append(_vgrad([x, y, fill_width, height], light, bar_color, height / 2))
		else:
			_ops.append(_rect([x, y, fill_width, height], bar_color, 0, height / 2))
	_ops.append(_rect([x, y, width, height], [86, 92, 120], 1, height / 2))
	var hp_text := "%d/%s" % [int(hp), str(int(max_hp))]
	_ops.append(_text(hp_text, TINY_SIZE, [200, 200, 200], [x, y + 12], "body"))


func _skill_slots(px: int, py: int, hero_color: Array) -> void:
	var cooldowns: Array = _state.get("cooldowns", [0, 0, 0, 0])
	var cooldown_max: Array = _state.get("cooldown_max", [180, 240, 420, 900])
	var keys: Array = _state.get("skill_labels", ["Q", "W", "E", "R"])
	var colors: Array = [hero_color, [100, 200, 255], [100, 255, 100], [255, 100, 100]]
	var y := py + 66
	var start_x := px + 14
	var auto_cast := bool(_state.get("auto_cast", false))
	for index in range(4):
		var cooldown := int(cooldowns[index]) if index < cooldowns.size() else 0
		var maximum := int(cooldown_max[index]) if index < cooldown_max.size() else 1
		var label: String = (
			String(keys[index]) if index < keys.size() else String(["Q", "W", "E", "R"][index])
		)
		var x := start_x + index * (SKILL_SIZE + SKILL_GAP)
		_draw_skill_slot(x, y, label, cooldown, maximum, colors[index], index == 3, auto_cast)


func _draw_skill_slot(
	x: int,
	y: int,
	key_letter: String,
	cooldown: int,
	cooldown_max: int,
	color: Array,
	is_ultimate: bool,
	is_auto: bool
) -> void:
	var ready := cooldown <= 0
	var bg := [30, 34, 58] if ready else [24, 27, 46]
	_ops.append(_rect([x, y, SKILL_SIZE, SKILL_SIZE], bg, 0, 6))
	if ready and _cheap_alpha:
		_ops.append(_radial([x - 8, y - 8, SKILL_SIZE + 16, SKILL_SIZE + 16], color, 44))
	if not ready:
		var ratio := float(cooldown) / float(cooldown_max) if cooldown_max != 0 else 0.0
		var cd_height := int(SKILL_SIZE * ratio)
		_ops.append(_fill([x, y + (SKILL_SIZE - cd_height), SKILL_SIZE, cd_height], [0, 0, 0, 190]))
		var seconds := int(cooldown / 60) + 1
		var label := str(seconds)
		var metrics := _measure_text(label, 20)
		var center := Vector2i(x + int(SKILL_SIZE / 2), y + int(SKILL_SIZE / 2))
		var text_pos := [center.x - int(metrics.x / 2), center.y - int(metrics.y / 2)]
		_ops.append(_text(label, 20, [0, 0, 0], [text_pos[0] + 1, text_pos[1] + 1], "body_bold"))
		_ops.append(_text(label, 20, WHITE, text_pos, "body_bold"))
	var border := [110, 116, 142]
	var border_width := 1
	if is_auto:
		var pulse := sin(float(_ticks_msec) * 0.008) * 0.3 + 0.7
		border = [int(100 + 80 * pulse), int(255 * (0.8 + 0.2 * pulse)), int(100 + 80 * pulse)]
		border_width = 2
	elif ready and is_ultimate:
		border = GOLD
		border_width = 2
	elif ready:
		border = [
			mini(255, int(color[0]) + 60),
			mini(255, int(color[1]) + 60),
			mini(255, int(color[2]) + 60),
		]
		border_width = 2
	_ops.append(_rect([x, y, SKILL_SIZE, SKILL_SIZE], border, border_width, 6))
	var fsize := 14 if key_letter.length() <= 2 else (12 if key_letter.length() <= 4 else 10)
	var key_metrics := _measure_text(key_letter, fsize)
	var badge_w := key_metrics.x + 6
	var badge := Rect2i(
		Vector2i(x + SKILL_SIZE - badge_w - 2, y + SKILL_SIZE - 13), Vector2i(badge_w, 11)
	)
	_ops.append(_rect(_box(badge), [10, 12, 22], 0, 3))
	var badge_center := Vector2i(
		badge.position.x + int(badge.size.x / 2), badge.position.y + int(badge.size.y / 2)
	)
	_ops.append(
		_text(
			key_letter,
			fsize,
			[220, 226, 245],
			[badge_center.x - int(key_metrics.x / 2), badge_center.y - int(key_metrics.y / 2)],
			"body_bold"
		)
	)


func _autocast_toggle(px: int, py: int) -> void:
	var rect := Rect2i(Vector2i(px + 10, py + 118), Vector2i(PANEL_W - 20, 22))
	var is_auto := bool(_state.get("auto_cast", false))
	var top := [64, 180, 88] if is_auto else [74, 78, 100]
	var bottom := [34, 116, 58] if is_auto else [44, 48, 68]
	var edge := [120, 235, 145] if is_auto else [120, 126, 150]
	var text_color := [222, 255, 232] if is_auto else TEXT_BODY
	if _cheap_alpha:
		_ops.append(_vgrad(_box(rect), top, bottom, rect.size.y / 2))
	else:
		_ops.append(_rect(_box(rect), top, 0, rect.size.y / 2))
	_ops.append(_rect(_box(rect), edge, 1, rect.size.y / 2))
	var icon_color := [255, 240, 160] if is_auto else [150, 158, 188]
	_bolt_icon(px + 28, rect.position.y + rect.size.y / 2, icon_color, 0.6)
	var label := "AUTO-CAST ON" if is_auto else "AUTO-CAST OFF"
	var metrics := _measure_text(label, 15)
	var center := Vector2i(
		rect.position.x + int(rect.size.x / 2) + 10, rect.position.y + int(rect.size.y / 2)
	)
	_ops.append(
		_text(
			label,
			15,
			text_color,
			[center.x - int(metrics.x / 2), center.y - int(metrics.y / 2)],
			"body_bold"
		)
	)


func _item_slots(px: int, py: int) -> void:
	var items: Array = _state.get("items", [])
	var start_x := px + int((PANEL_W - ITEM_ROW_W) / 2)
	var y := py + 148
	for index in range(ITEM_COUNT):
		var rect := Rect2i(
			Vector2i(start_x + index * (ITEM_SIZE + ITEM_GAP), y), Vector2i(ITEM_SIZE, ITEM_SIZE)
		)
		_ops.append(_rect(_box(rect), [14, 17, 30], 0, 5))
		var raw: Variant = items[index] if index < items.size() else {}
		var item: Dictionary = raw if raw is Dictionary else {}
		var item_id := String(item.get("id", ""))
		var occupied := not item.is_empty() and not item_id.is_empty()
		var border := [66, 74, 104]
		if occupied:
			var color := _rgb(item.get("color", [66, 74, 104]), [66, 74, 104])
			var glow := _rgb(item.get("glow", color), color)
			border = color
			if bool(item.get("active", false)):
				_ops.append(
					_rect(
						[rect.position.x - 3, rect.position.y - 3, ITEM_SIZE + 6, ITEM_SIZE + 6],
						[glow[0], glow[1], glow[2], 130],
						0,
						6
					)
				)
			_draw_item_icon(rect, item, color, glow)
			if item_id == "demon_maw" and int(item.get("cooldown", 0)) > 0:
				var cooldown_h := int(ITEM_SIZE * float(item["cooldown"]) / 1500.0)
				_ops.append(
					_fill(
						[
							rect.position.x,
							rect.position.y + ITEM_SIZE - cooldown_h,
							ITEM_SIZE,
							cooldown_h
						],
						[0, 0, 0, 150]
					)
				)
		_ops.append(_rect(_box(rect), border, 2 if occupied else 1, 5))


func _draw_item_icon(rect: Rect2i, item: Dictionary, color: Array, glow: Array) -> void:
	var icon_x := rect.position.x + 2
	var icon_y := rect.position.y + 2
	_ops.append(
		_rect([icon_x + 2, icon_y + 2, ITEM_ICON_SIZE - 4, ITEM_ICON_SIZE - 4], color, 0, 6)
	)
	_ops.append(_rect([icon_x + 2, icon_y + 2, ITEM_ICON_SIZE - 4, ITEM_ICON_SIZE - 4], glow, 2, 6))
	var label := String(item.get("name", item.get("id", ""))).left(5)
	var metrics := _measure_text(label, 16)
	var text_pos := [
		icon_x + int(ITEM_ICON_SIZE / 2) - int(metrics.x / 2),
		icon_y + int(ITEM_ICON_SIZE / 2) - int(metrics.y / 2),
	]
	_ops.append(_text(label, 16, WHITE, text_pos, "body_semibold"))


func _item_shop_button(px: int, py: int) -> void:
	var items: Array = _state.get("items", [])
	var used := 0
	for item in items:
		if item is Dictionary and not item.is_empty() and not String(item.get("id", "")).is_empty():
			used += 1
	var label := "ITEM FORGE  (%d/%d)" % [used, ITEM_COUNT]
	var rect := Rect2i(Vector2i(px + 10, py + 186), Vector2i(PANEL_W - 20, 22))
	_pill(label, rect, "violet", "hero_open_items", "", rect.has_point(_mouse()))


func _upgrade_button(px: int, py: int) -> void:
	var level := int(_state.get("level", 1))
	var max_level := int(_state.get("max_level", 15))
	if level < max_level:
		var cost := int(_state.get("upgrade_cost", 0))
		var can_upgrade := int(_state.get("gold", 0)) >= cost
		var mouse := _mouse()
		var rect := Rect2i(Vector2i(px + 10, py + 214), Vector2i(PANEL_W - 20, 22))
		var hover := can_upgrade and rect.has_point(mouse)
		_pill(
			"UPGRADE HERO (%dG)" % cost,
			rect,
			"gold" if can_upgrade else "locked",
			"popup_upgrade_hero",
			"plus",
			hover
		)
	else:
		var label := _letter("MAX LEVEL")
		var metrics := _measure_text(label, 18)
		_ops.append(
			_text(
				label,
				18,
				GOLD_TEXT,
				[px + int(PANEL_W / 2) - int(metrics.x / 2), py + 214 + 11 - int(metrics.y / 2)],
				"body_bold"
			)
		)


func _pill(
	label: String, rect: Rect2i, kind: String, _button_id: String, icon: String, hover: bool
) -> void:
	var top: Array
	var bottom: Array
	var edge: Array
	var text_color: Array
	match kind:
		"violet":
			top = [74, 48, 118]
			bottom = [44, 28, 78]
			edge = [196, 150, 255]
			text_color = [226, 205, 255]
		"gold":
			top = [86, 66, 22]
			bottom = [52, 40, 14]
			edge = GOLD
			text_color = GOLD_TEXT
		_:
			top = [48, 50, 66]
			bottom = [30, 32, 44]
			edge = SLATE
			text_color = TEXT_DIM
	if hover:
		top = _tint(top, 18)
		bottom = _tint(bottom, 14)
	if _cheap_alpha:
		_ops.append(_vgrad(_box(rect), top, bottom, 7))
	else:
		_ops.append(_rect(_box(rect), top, 0, 7))
	_ops.append(_rect(_box(rect), edge, 2, 7))
	if hover and _cheap_alpha:
		_ops.append(
			_radial(
				[rect.position.x - 15, rect.position.y - 12, rect.size.x + 30, rect.size.y + 24],
				edge,
				66
			)
		)
	var center_x := rect.position.x + int(rect.size.x / 2)
	if not icon.is_empty():
		_draw_icon(icon, rect.position.x + 22, rect.position.y + rect.size.y / 2, edge, 0.8)
		center_x = rect.position.x + 22 + int((rect.size.x - 22) / 2)
	var words := label
	var metrics := _measure_text(words, 16)
	var font_size := 16
	if label.begins_with("UPGRADE HERO"):
		font_size = 16
	elif label.begins_with("ITEM FORGE"):
		font_size = 16
	metrics = _measure_text(words, font_size)
	var center_y := rect.position.y + int(rect.size.y / 2)
	var text_pos := [center_x - int(metrics.x / 2), center_y - int(metrics.y / 2)]
	_ops.append(
		_text(words, font_size, [5, 6, 12], [text_pos[0] + 2, text_pos[1] + 2], "body_bold")
	)
	_ops.append(_text(words, font_size, text_color, text_pos, "body_bold"))


func _bolt_icon(cx: float, cy: float, color: Array, scale: float) -> void:
	(
		_ops
		. append(
			{
				"kind": "polygon",
				"points":
				[
					[_num(cx + 2.0 * scale), _num(cy - 10.0 * scale)],
					[_num(cx - 6.0 * scale), _num(cy + 1.0 * scale)],
					[_num(cx - 1.0 * scale), _num(cy + 1.0 * scale)],
					[_num(cx - 3.0 * scale), _num(cy + 10.0 * scale)],
					[_num(cx + 6.0 * scale), _num(cy - 1.0 * scale)],
					[_num(cx + 1.0 * scale), _num(cy - 1.0 * scale)],
				],
				"color": _rgba(color, 255),
				"mult": 255,
				"width": 0,
			}
		)
	)


func _draw_icon(name: String, cx: float, cy: float, color: Array, scale: float) -> void:
	if name == "plus":
		_ops.append(
			_line(
				[_num(cx - 6.0 * scale), _num(cy)],
				[_num(cx + 6.0 * scale), _num(cy)],
				_rgba(color, 255),
				3
			)
		)
		_ops.append(
			_line(
				[_num(cx), _num(cy - 6.0 * scale)],
				[_num(cx), _num(cy + 6.0 * scale)],
				_rgba(color, 255),
				3
			)
		)


func _corner_ticks(px: int, py: int, width: int, height: int, color: Array, length: int) -> void:
	var corners: Array = [
		[px + 2, py + 2, 1, 1],
		[px + width - 2, py + 2, -1, 1],
		[px + 2, py + height - 2, 1, -1],
		[px + width - 2, py + height - 2, -1, -1],
	]
	for corner in corners:
		var cx := int(corner[0])
		var cy := int(corner[1])
		var sx := int(corner[2])
		var sy := int(corner[3])
		_ops.append(_line([cx, cy], [cx + sx * length, cy], _rgba(color, 255), 2))
		_ops.append(_line([cx, cy], [cx, cy + sy * length], _rgba(color, 255), 2))


func _fit_ellipsis(text: String, max_width: int) -> String:
	var shortened := text
	while shortened.length() > 1:
		var candidate := shortened.left(shortened.length() - 1)
		if _measure_text(candidate + "...", TITLE_SIZE).x <= max_width:
			return candidate + "..."
		shortened = candidate
	return "..."


func _measure_text(text: String, size: int) -> Vector2i:
	if _measure.is_valid():
		var measured: Variant = _measure.call(text, size)
		return Vector2i(measured)
	return Vector2i(int(float(size) * 0.55) * text.length(), size)


func _mouse() -> Vector2i:
	var value: Variant = _state.get("mouse", Vector2i.ZERO)
	if value is Array and value.size() >= 2:
		return Vector2i(int(value[0]), int(value[1]))
	if value is Vector2i:
		return value
	return Vector2i.ZERO


func _letter(text: String) -> String:
	var out := ""
	for index in range(text.length()):
		if index > 0:
			out += " "
		out += text.substr(index, 1)
	return out


func _tint(color: Array, bias: int) -> Array:
	return [
		mini(255, int(color[0]) + bias),
		mini(255, int(color[1]) + bias),
		mini(255, int(color[2]) + bias)
	]


func _rgb(value: Variant, fallback: Array) -> Array:
	if value is Array and value.size() >= 3:
		return [int(value[0]), int(value[1]), int(value[2])]
	if value is Color:
		return [int(value.r8), int(value.g8), int(value.b8)]
	return fallback.duplicate()


func _box(rect: Rect2i) -> Array:
	return [rect.position.x, rect.position.y, rect.size.x, rect.size.y]


func _text(words: String, size: int, color: Array, pos: Array, style: String) -> Dictionary:
	return {
		"kind": "text",
		"text": words,
		"size": size,
		"style": style,
		"color": _rgba(color, 255),
		"mult": 255,
		"pos": pos,
	}


func _rect(box: Array, color: Array, width: int, radius: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": box.duplicate(),
		"color": _rgba(color, int(color[3]) if color.size() > 3 else 255),
		"mult": 255,
		"width": width,
		"radius": radius,
	}


func _fill(box: Array, color: Array) -> Dictionary:
	return {
		"kind": "fill",
		"rect": box.duplicate(),
		"color": color.duplicate(),
		"mult": 255,
		"blend": 0,
	}


func _line(a: Array, b: Array, color: Array, width: int) -> Dictionary:
	return {"kind": "line", "a": a, "b": b, "color": color, "mult": 255, "width": width}


func _vgrad(box: Array, top: Array, bottom: Array, radius: int) -> Dictionary:
	return {
		"kind": "vgrad",
		"rect": box.duplicate(),
		"top": top.duplicate(),
		"bottom": bottom.duplicate(),
		"radius": radius,
		"mult": 255,
	}


func _shadow(width: int, height: int, radius: int, alpha: int, x: int, y: int) -> Dictionary:
	return {
		"kind": "shadow",
		"rect": [x, y, width + 8, height + 8],
		"radius": radius,
		"alpha": alpha,
		"mult": 255,
	}


func _radial(box: Array, color: Array, alpha: int) -> Dictionary:
	var opacity := int(float(alpha) / 8.0) * 8
	opacity = maxi(4, mini(120, opacity))
	return {
		"kind": "radial",
		"rect": box.duplicate(),
		"color": color.duplicate(),
		"alpha": opacity,
		"mult": 255,
	}


func _rgba(color: Array, alpha: int) -> Array:
	return [int(color[0]), int(color[1]), int(color[2]), alpha]


func _num(value: float) -> Variant:
	if is_equal_approx(value, roundf(value)):
		return int(roundf(value))
	return value
