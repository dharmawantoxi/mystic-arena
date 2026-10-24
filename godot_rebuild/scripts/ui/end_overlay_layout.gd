extends RefCounted
## Layer 9bv5: `Overlay.draw` (`ui_components/_bundle.py`, cheap-alpha branch), the victory /
## defeat screen pygame paints over the frozen match. Pure op builder; the ops use the
## `draw_recorder.py` shapes (plus one op per cached surface) so
## `tests/end_overlay_draw_source_oracle.py` can pin them. Every helper is preceded by a
## `section` op, like the oracle's wrapped methods.
##
##   * backdrop: one (10, 10, 20, a) row per y, a = int(180 * (1 - |y - 360| / 360 * 0.3));
##   * rays: 12 (color, 30) triangles, angle i / 12 * TAU + t * 0.3, length 400 + sin(t + i) * 50,
##     30 px half width, t = animation_time * 0.05 (frozen once the match ends, as in pygame);
##   * glow: circles r = 200..60 step -20 with alpha int((200 - r) / 200 * 60);
##   * title: `_radial(760, 190)` at (cx - 380, cy - 275), alpha 54 -> 48, and the Cinzel
##     `outline_text` (3 px outline, gold or red gradient) centred on (cx, cy - 180), size
##     int(round(88 * (sin(2t) * 0.04 + 1) / 4) * 4);
##   * sparkles (victory): 8 dots on an ellipse around the title;
##   * stats: 500 x 214 panel at (cx - 250, cy - 100) with shadow, gradient, 2 px border, gold
##     corner ticks and five rows (label left, value right-aligned at x + 480, NEW BEST badge);
##   * level unlock popup (victory): `UNLOCK_POPUP` marker until layer 9bv6 ports it;
##   * action hint: keycap chips parsed from `[KEY] Desc` pairs centred on y = cy + 200;
##   * achievements: trophy icon + "N Achievements Unlocked!" on y = cy + 250.

const GoldHudLayout = preload("res://scripts/ui/gold_hud_layout.gd")

## `Game.draw`: GOLD for `VICTORY! LV.n`, RED for `DEFEAT LV.n`.
const VICTORY_COLOR := [255, 200, 50]
const DEFEAT_COLOR := [220, 50, 50]
const CENTER := Vector2i(640, 360)
const BACKDROP := [10, 10, 20]
const TITLE_Y := 180
const PANEL_SIZE := Vector2i(500, 214)
const GOLD_BRIGHT := [255, 233, 158]
const STATS_LABEL := [180, 180, 200]
const BEST_VALUE := [255, 220, 100]
const KEY_TEXT := [255, 235, 140]
const DESC_TEXT := [205, 210, 225]
const PLAIN_TEXT := [150, 156, 180]
const TROPHY := [255, 220, 50]
const BADGE_INK := [80, 40, 0]
const UNLOCK_POPUP := {"kind": "unlock_popup"}

var _ops: Array = []
var _measure: Callable
var _title_measure: Callable


## `state`: title, victory, color, action, animation_time, achievements and stats
## `[score, seconds, waves, kills, combo, new_best_score, new_best_time]`. `title_measure`
## measures the Cinzel title (defaults to `measure`, as the oracle's one fake font does).
static func ops(
	state: Dictionary, measure: Callable, ticks_msec: int, title_measure: Callable = Callable()
) -> Array:
	var layout := new()
	layout._measure = measure
	layout._title_measure = title_measure if title_measure.is_valid() else measure
	layout._draw(state, ticks_msec)
	return layout._ops


static func backdrop_rows() -> Array:
	var rows: Array = []
	for row in range(720):
		rows.append(int(180 * (1 - absf(row - 360.0) / 360.0 * 0.3)))
	return rows


static func title_size(animation_time: int) -> int:
	var t := animation_time * 0.05
	var pulse := sin(t * 2) * 0.04 + 1.0
	return clampi(int(roundf(88 * pulse / 4) * 4), 8, 220)


## `Game.draw`'s action line for the victory / defeat overlay.
static func action_text(victory: bool, has_next: bool, labels: Dictionary) -> String:
	var next_label := String(labels.get("next_level", "N"))
	var replay := String(labels.get("replay", "R"))
	var menu := String(labels.get("to_menu", "ESC"))
	if not victory:
		return "[%s] Retry  [%s] Menu" % [replay, menu]
	if has_next:
		return "[%s] Next Level  [%s] Replay  [%s] Menu" % [next_label, replay, menu]
	return "[%s] Replay  [%s] Menu  (You cleared all levels!)" % [replay, menu]


func _draw(state: Dictionary, ticks_msec: int) -> void:
	var color: Array = state.get("color", [255, 200, 50])
	var title := String(state.get("title", ""))
	var victory := bool(state.get("victory", false))
	var t := int(state.get("animation_time", 0)) * 0.05
	var gradient := {
		"kind": "end_gradient",
		"rect": [0, 0, 1280, 720],
		"color": BACKDROP.duplicate(),
		"rows": backdrop_rows(),
		"mult": 255,
	}
	_ops.append(gradient)
	_section("_draw_rays")
	_rays(color, t)
	_section("_draw_central_glow")
	for radius in range(200, 50, -20):
		var alpha := int((200 - radius) / 200.0 * 60)
		_ops.append(_circle([CENTER.x, CENTER.y], radius, _rgba(color, alpha), 0))
	_section("_draw_title")
	_title(title, victory, int(state.get("animation_time", 0)))
	_section("_draw_sparkles")
	if victory:
		_sparkles(color, t)
	_section("_draw_stats")
	_stats(state.get("stats", [0, 0, 0, 0, 0, false, false]), color, ticks_msec)
	if victory:
		_section("_draw_level_unlock_popup")
		_ops.append(UNLOCK_POPUP.duplicate())
	_section("_draw_action_hint")
	_action_hint(String(state.get("action", "")), t)
	_section("_draw_achievements")
	_achievements(int(state.get("achievements", 0)))


func _rays(color: Array, t: float) -> void:
	for index in range(12):
		var angle := (index / 12.0) * PI * 2 + t * 0.3
		var ray_len := 400 + sin(t + index) * 50
		var end_x := CENTER.x + cos(angle) * ray_len
		var end_y := CENTER.y + sin(angle) * ray_len
		var perp := angle + PI / 2
		var p1 := [end_x + cos(perp) * 30, end_y + sin(perp) * 30]
		var p2 := [end_x - cos(perp) * 30, end_y - sin(perp) * 30]
		var points := [[CENTER.x, CENTER.y], p1, p2]
		_ops.append(_polygon(points, _rgba(color, 30)))


func _title(title: String, victory: bool, animation_time: int) -> void:
	var size := title_size(animation_time)
	var glow := [255, 205, 90] if victory else [255, 90, 70]
	var radial := {
		"kind": "radial",
		"rect": [CENTER.x - 380, CENTER.y - TITLE_Y - 95, 760, 190],
		"color": glow,
		"alpha": 48,
		"mult": 255,
	}
	_ops.append(radial)
	var metrics: Vector2i = _title_measure.call(title, size)
	var outline := {
		"kind": "outline_text",
		"text": title,
		"size": size,
		"style": "title",
		"pos": [CENTER.x - (metrics.x >> 1), CENTER.y - TITLE_Y - (metrics.y >> 1)],
		"outline": [8, 9, 18],
		"width": 3,
		"top": [255, 242, 175] if victory else [255, 175, 150],
		"bottom": [196, 138, 40] if victory else [178, 45, 45],
		"mult": 255,
	}
	_ops.append(outline)


func _sparkles(color: Array, t: float) -> void:
	for index in range(8):
		var angle := t + index * PI / 4
		var dist := 100 + sin(t + index) * 20
		var at := [int(CENTER.x + cos(angle) * dist), int(CENTER.y - TITLE_Y + sin(angle) * 30)]
		_ops.append(_circle(at, 3, [255, 255, 200, 255], 0))
		_ops.append(_circle(at, 2, _rgba(color, 255), 0))


func _stats(stats: Array, color: Array, ticks_msec: int) -> void:
	var seconds := int(stats[1])
	var rows := [
		["Final Score", GoldHudLayout.gold_text(int(stats[0])), bool(stats[5])],
		["Match Time", "%d:%02d" % [floori(seconds / 60.0), seconds % 60], bool(stats[6])],
		["Waves Survived", str(int(stats[2])), false],
		["Total Kills", str(int(stats[3])), false],
		["Max Combo", "x%d" % int(stats[4]), false],
	]
	var px := CENTER.x - (PANEL_SIZE.x >> 1)
	var py := CENTER.y - 100
	var panel := [px, py, PANEL_SIZE.x, rows.size() * 38 + 24]
	var shadow := {
		"kind": "shadow",
		"rect": [px - 3, py - 3, panel[2] + 8, panel[3] + 8],
		"radius": 10,
		"alpha": 160,
		"mult": 255,
	}
	_ops.append(shadow)
	_ops.append(_vgrad(panel, [30, 34, 58], [14, 16, 30], 10))
	_ops.append(_rect(panel, _rgba(color, 255), 2, 10))
	_corner_ticks(panel, GOLD_BRIGHT, 14)
	for index in range(rows.size()):
		var row: Array = rows[index]
		var y: int = py + 15 + index * 32
		_ops.append(_text(String(row[0]), 22, STATS_LABEL, [px + 20, y]))
		if bool(row[2]):
			_badge(px + (PANEL_SIZE.x >> 1) - 30, y - 3, ticks_msec)
		var value := String(row[1])
		var value_color: Array = BEST_VALUE if bool(row[2]) else color
		var width: int = _measure.call(value, 30).x
		_ops.append(_text(value, 30, value_color, [px + PANEL_SIZE.x - 20 - width, y - 2]))


## NEW BEST: a 118 x 22 SRCALPHA badge (gold rows + 2 px border at the pulse alpha), the star
## icon and the centred label.
func _badge(x: int, y: int, ticks_msec: int) -> void:
	var pulse := sin(ticks_msec * 0.008) * 0.3 + 0.7
	var alpha := int(255 * pulse)
	for row in range(22):
		var t := row / 22.0
		var rgba := [int(200 + t * 55), int(150 + t * 70), int(30 + t * 30), alpha]
		_ops.append(_line([x, y + row], [x + 118, y + row], rgba, 1))
	_ops.append(_rect([x, y, 118, 22], [255, 255, 200, alpha], 2, 4))
	_star(x + 12, y + 11, 0.45, BADGE_INK)
	var label := "NEW BEST!"
	var metrics: Vector2i = _measure.call(label, 18)
	var cx := x + 59 + 10
	_ops.append(_text(label, 18, BADGE_INK, [cx - (metrics.x >> 1), y + 11 - (metrics.y >> 1)]))


func _action_hint(action: String, t: float) -> void:
	var action_y := CENTER.y + 200
	var pairs := RegEx.create_from_string("\\[([^\\]]+)\\]\\s*([^[\\]]*)")
	var items: Array = []
	var total_w := 0
	for found in pairs.search_all(action):
		var key := found.get_string(1)
		var desc := found.get_string(2).strip_edges()
		var key_w: int = _measure.call(key, 22).x
		var width := key_w + 14
		if not desc.is_empty():
			width += 6 + int(_measure.call(desc, 22).x)
		items.append([key, desc, key_w])
		total_w += width + 16
	var plain := pairs.sub(action, "", true).strip_edges()
	if not plain.is_empty():
		total_w += int(_measure.call(plain, 22).x) + 16
	total_w = maxi(0, total_w - 16)
	var pulse := int(sin(t * 3) * 30 + 140)
	var border := [pulse, pulse + 10, pulse + 35, 255]
	var font_h: int = _measure.call("", 22).y
	var x := CENTER.x - (total_w >> 1)
	for item in items:
		var key_w: int = int(item[2]) + 14
		var key_h := font_h + 8
		var key_y := action_y - (key_h >> 1)
		var keycap := {
			"kind": "fill",
			"rect": [x, key_y, key_w, key_h],
			"color": [10, 12, 24, 160],
			"mult": 255,
			"blend": 0,
		}
		_ops.append(keycap)
		_ops.append(_rect([x, key_y, key_w, key_h], [48, 52, 70, 255], 0, 6))
		_ops.append(_rect([x, key_y, key_w, key_h], border, 1, 6))
		_ops.append(_text(String(item[0]), 22, KEY_TEXT, [x + 7, action_y - (font_h >> 1)]))
		x += key_w
		var desc := String(item[1])
		if not desc.is_empty():
			_ops.append(_text(desc, 22, DESC_TEXT, [x + 6, action_y - (font_h >> 1)]))
			x += 6 + int(_measure.call(desc, 22).x)
		x += 16
	if not plain.is_empty():
		_ops.append(_text(plain, 22, PLAIN_TEXT, [x, action_y - (font_h >> 1)]))


func _achievements(count: int) -> void:
	if count <= 0:
		return
	var y := CENTER.y + 250
	var label := "%d Achievements Unlocked!" % count
	var metrics: Vector2i = _measure.call(label, 20)
	var x := CENTER.x - ((26 + metrics.x) >> 1)
	_trophy(x + 11, y, 0.7, TROPHY)
	_ops.append(_text(label, 20, TROPHY, [x + 26, y - 9]))


## `ui_theme.corner_ticks(rect, color, length)` with width 2 and inset 2.
func _corner_ticks(box: Array, color: Array, length: int) -> void:
	var right: int = int(box[0]) + int(box[2])
	var bottom: int = int(box[1]) + int(box[3])
	var corners := [
		[int(box[0]) + 2, int(box[1]) + 2, 1, 1],
		[right - 2, int(box[1]) + 2, -1, 1],
		[int(box[0]) + 2, bottom - 2, 1, -1],
		[right - 2, bottom - 2, -1, -1],
	]
	for corner in corners:
		var a := [corner[0], corner[1]]
		_ops.append(_line(a, [corner[0] + corner[2] * length, corner[1]], _rgba(color, 255), 2))
		_ops.append(_line(a, [corner[0], corner[1] + corner[3] * length], _rgba(color, 255), 2))


## `ui_theme.draw_icon(surf, "star", cx, cy, color, s)`.
func _star(cx: int, cy: int, s: float, color: Array) -> void:
	for step in [[1, 0], [0, 1], [1, 1], [1, -1]]:
		var a := [cx - step[0] * 8 * s, cy - step[1] * 8 * s]
		var b := [cx + step[0] * 8 * s, cy + step[1] * 8 * s]
		_ops.append(_line(a, b, _rgba(color, 255), 2))
	_ops.append(_circle([cx, cy], 3 * s, _rgba(color, 255), 0))


## `ui_theme.draw_icon(surf, "trophy", cx, cy, color, s)`; arc rects truncate like `Rect()`.
func _trophy(cx: int, cy: int, s: float, color: Array) -> void:
	var rgba := _rgba(color, 255)
	var cup := [
		[cx - 7 * s, cy - 8 * s],
		[cx + 7 * s, cy - 8 * s],
		[cx + 5 * s, cy],
		[cx, cy + 4 * s],
		[cx - 5 * s, cy],
	]
	_ops.append(_polygon(cup, rgba))
	_ops.append(_line([cx, cy + 4 * s], [cx, cy + 7 * s], rgba, 2))
	_ops.append(_line([cx - 5 * s, cy + 9 * s], [cx + 5 * s, cy + 9 * s], rgba, 2))
	var left := [int(cx - 10 * s), int(cy - 8 * s), int(5 * s), int(7 * s)]
	var right := [int(cx + 5 * s), int(cy - 8 * s), int(5 * s), int(7 * s)]
	_ops.append(_arc(left, rgba, 1.4, 4.6))
	_ops.append(_arc(right, rgba, -1.4, 1.6))


func _section(name: String) -> void:
	_ops.append({"kind": "section", "name": name})


static func _rgba(color: Array, alpha: int) -> Array:
	return [int(color[0]), int(color[1]), int(color[2]), alpha]


static func _circle(center: Array, radius: float, rgba: Array, width: int) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"color": rgba,
		"mult": 255,
		"width": width,
	}


static func _polygon(points: Array, rgba: Array) -> Dictionary:
	return {"kind": "polygon", "points": points, "color": rgba, "mult": 255, "width": 0}


static func _line(a: Array, b: Array, rgba: Array, width: int) -> Dictionary:
	return {"kind": "line", "a": a, "b": b, "color": rgba, "mult": 255, "width": width}


static func _arc(box: Array, rgba: Array, start: float, end: float) -> Dictionary:
	return {
		"kind": "arc",
		"rect": box,
		"color": rgba,
		"mult": 255,
		"width": 2,
		"start": start,
		"end": end,
	}


static func _rect(box: Array, rgba: Array, width: int, radius: int) -> Dictionary:
	return {
		"kind": "rect",
		"rect": box.duplicate(),
		"color": rgba,
		"mult": 255,
		"width": width,
		"radius": radius,
	}


static func _vgrad(box: Array, top: Array, bottom: Array, radius: int) -> Dictionary:
	return {
		"kind": "vgrad",
		"rect": box.duplicate(),
		"top": top,
		"bottom": bottom,
		"radius": radius,
		"mult": 255,
	}


static func _text(words: String, size: int, color: Array, pos: Array) -> Dictionary:
	return {
		"kind": "text",
		"text": words,
		"size": size,
		"style": "body_semibold",
		"color": _rgba(color, 255),
		"mult": 255,
		"pos": pos,
	}
