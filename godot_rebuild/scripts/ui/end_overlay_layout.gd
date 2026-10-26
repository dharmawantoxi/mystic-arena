extends RefCounted
## Layers 9bv5/9bv10: `Overlay.draw` (`ui_components/_bundle.py`) in both quality modes, the
## victory / defeat screen pygame paints over the frozen match. Pure op builder; the ops use the
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
##   * level unlock popup (victory, layer 9bv6): after `UNLOCK_DELAY` draw calls a 340 x 220
##     card slides in from x = cx + 220 + 400 (cubic ease over 30 calls, alpha over 15) with
##     the gold gradient (blitted twice around its glow), opened lock, LEVEL n + name, the next
##     true boss silhouette, a difficulty meter and the PLAY NEXT LEVEL button. pygame's timer
##     stops AT the delay, so in a real match the card stays 400 px right at alpha 0;
##   * action hint: keycap chips parsed from `[KEY] Desc` pairs centred on y = cy + 200;
##   * achievements: trophy icon + "N Achievements Unlocked!" on y = cy + 250.
## With `cheap_alpha` false the source instead uses `darken(..., 170)`, skips rays/title glow,
## draws two opaque outline rings and a solid stats panel (no shadow/gradient); sparkles remain.

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
const UNLOCK_DELAY := 90
const POPUP_SIZE := Vector2i(340, 220)

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
	var cheap_alpha := bool(state.get("cheap_alpha", true))
	var animation_time := int(state.get("animation_time", 0))
	var t := animation_time * 0.05
	if cheap_alpha:
		(
			_ops
			. append(
				{
					"kind": "end_gradient",
					"rect": [0, 0, 1280, 720],
					"color": BACKDROP.duplicate(),
					"rows": backdrop_rows(),
					"mult": 255,
				}
			)
		)
	else:
		_ops.append({"kind": "darken", "rect": [0, 0, 1280, 720], "alpha": 170})
	_section("_draw_rays")
	if cheap_alpha:
		_rays(color, t)
	_section("_draw_central_glow")
	if cheap_alpha:
		for radius in range(200, 50, -20):
			var alpha := int((200 - radius) / 200.0 * 60)
			_ops.append(_circle([CENTER.x, CENTER.y], radius, _rgba(color, alpha), 0))
	else:
		_ops.append(_circle([CENTER.x, CENTER.y], 120, _rgba(color, 255), 3))
		_ops.append(_circle([CENTER.x, CENTER.y], 190, _rgba(color, 255), 2))
	_section("_draw_title")
	_title(title, victory, animation_time, cheap_alpha)
	_section("_draw_sparkles")
	if victory:
		_sparkles(color, t)
	_section("_draw_stats")
	_stats(state.get("stats", [0, 0, 0, 0, 0, false, false]), color, ticks_msec, cheap_alpha)
	if victory:
		_section("_draw_level_unlock_popup")
		_unlock_popup(state.get("unlock", {}), ticks_msec)
	_section("_draw_action_hint")
	_action_hint(String(state.get("action", "")), t)
	_section("_draw_achievements")
	_achievements(int(state.get("achievements", 0)))


## The card's top-left for an unlock timer (`timer` already advanced by `_update_unlock_popup`).
static func popup_origin(timer: int) -> Vector2i:
	var elapsed := timer - UNLOCK_DELAY
	var offset_x := 0
	if elapsed < 30:
		var eased := 1 - pow(1 - elapsed / 30.0, 3)
		offset_x = int((1 - eased) * 400)
	return Vector2i(CENTER.x + 220 + offset_x, CENTER.y - 100)


## `g.ui_buttons['play_next_level']`: the PLAY NEXT LEVEL rect the source registers.
static func play_button_rect(timer: int) -> Rect2i:
	var origin := popup_origin(timer)
	return Rect2i(origin.x + 15, origin.y + POPUP_SIZE.y - 40, POPUP_SIZE.x - 30, 30)


## `unlock`: timer, level, name, hp_mult, difficulty, hover and boss {name, boss_class, color,
## entrance_color}; empty when no level was newly unlocked.
func _unlock_popup(unlock: Dictionary, ticks_msec: int) -> void:
	if unlock.is_empty() or int(unlock.get("timer", 0)) < UNLOCK_DELAY:
		return
	var elapsed := int(unlock.get("timer", 0)) - UNLOCK_DELAY
	var alpha := mini(255, int(255 * (elapsed / 15.0)))
	var origin := popup_origin(int(unlock.get("timer", 0)))
	var x := origin.x
	var y := origin.y
	_ops.append(_rect([x, y, POPUP_SIZE.x, POPUP_SIZE.y], [0, 0, 0, 150], 0, 12))
	_popup_card(x, y, alpha)
	var pulse := sin(ticks_msec * 0.005) * 0.3 + 0.7
	var glow := [255, 220, 100, int(80 * pulse * (alpha / 255.0))]
	_ops.append(_rect([x - 15, y - 15, POPUP_SIZE.x + 30, POPUP_SIZE.y + 30], glow, 0, 18))
	_popup_card(x, y, alpha)
	_popup_lock(x + 40, y + 30, ticks_msec)
	var shadow := _text("NEW LEVEL UNLOCKED!", 26, [0, 0, 0], [x + 66, y + 15])
	shadow["mult"] = 100
	_ops.append(shadow)
	_ops.append(_text("NEW LEVEL UNLOCKED!", 26, [255, 220, 100], [x + 65, y + 14]))
	_ops.append(
		_text("LEVEL %d" % int(unlock.get("level", 0)), 28, [255, 255, 255], [x + 65, y + 35])
	)
	_ops.append(_text(String(unlock.get("name", "")), 22, [200, 200, 220], [x + 65, y + 60]))
	_ops.append(_line([x + 15, y + 85], [x + POPUP_SIZE.x - 15, y + 85], [255, 220, 100, 255], 1))
	var boss: Dictionary = unlock.get("boss", {})
	_popup_boss(x + 55, y + 135, boss, ticks_msec)
	var entrance: Array = boss.get("entrance_color", [150, 100, 200])
	_ops.append(_text("FINAL BOSS", 18, [255, 100, 100], [x + 100, y + 100]))
	_ops.append(_text(String(boss.get("name", "???")), 28, entrance, [x + 100, y + 118]))
	_popup_difficulty(x + 100, y, unlock)
	_popup_button(int(unlock.get("timer", 0)), bool(unlock.get("hover", false)))


## The gold gradient card (220 rows) and its two borders, all at the slide alpha.
func _popup_card(x: int, y: int, alpha: int) -> void:
	for row in range(POPUP_SIZE.y):
		var t := row / float(POPUP_SIZE.y)
		var rgba := [int(40 + t * 20), int(30 + t * 15), int(10 + t * 5), alpha]
		_ops.append(_line([x, y + row], [x + POPUP_SIZE.x, y + row], rgba, 1))
	_ops.append(_rect([x, y, POPUP_SIZE.x, POPUP_SIZE.y], [255, 220, 100, alpha], 3, 12))
	_ops.append(
		_rect([x + 2, y + 2, POPUP_SIZE.x - 4, POPUP_SIZE.y - 4], [255, 250, 180, alpha], 1, 10)
	)


func _popup_lock(cx: int, cy: int, ticks_msec: int) -> void:
	_ops.append(_rect([cx - 8, cy - 2, 16, 14], [100, 100, 130, 255], 0, 2))
	_ops.append(_rect([cx - 8, cy - 2, 16, 14], [60, 60, 90, 255], 2, 2))
	var lock_arc := _arc([cx - 6, cy - 18, 12, 18], [100, 100, 130, 255], PI * 0.2, PI * 1.2)
	lock_arc["width"] = 3
	_ops.append(lock_arc)
	var keyhole := int(255 * (sin(ticks_msec * 0.008) * 0.3 + 0.7))
	_ops.append(_circle([cx, cy + 7], 3, [100, 255, 100, keyhole], 0))
	_ops.append(_circle([cx, cy + 7], 1, [255, 255, 255, keyhole], 0))


func _popup_boss(cx: int, cy: int, boss: Dictionary, ticks_msec: int) -> void:
	var entrance: Array = boss.get("entrance_color", [150, 100, 200])
	var aura_r := int(35 * (sin(ticks_msec * 0.004) * 0.3 + 0.7))
	for radius in range(aura_r, 5, -3):
		var alpha := int((aura_r - radius) * 3)
		if alpha > 0:
			_ops.append(_circle([cx, cy], radius, _rgba(entrance, alpha), 0))
	var outer := [[-15, -5], [-10, -20], [0, -25], [10, -20], [15, -5], [18, 10], [12, 22]]
	outer += [[-12, 22], [-18, 10]]
	var inner := [[-13, -5], [-9, -18], [0, -23], [9, -18], [13, -5], [16, 8], [10, 20]]
	inner += [[-10, 20], [-16, 8]]
	_ops.append(_polygon(_offset(outer, cx, cy), [0, 0, 0, 255]))
	_ops.append(_polygon(_offset(inner, cx, cy), _rgba(boss.get("color", [150, 100, 200]), 255)))
	var spikes := 5 if String(boss.get("boss_class", "true")) == "true" else 3
	for index in range(spikes):
		var sx := cx + (index - (spikes >> 1)) * 8
		_ops.append(_polygon([[sx - 3, cy - 25], [sx, cy - 33], [sx + 3, cy - 25]], [0, 0, 0, 255]))
	var eye_pulse := sin(ticks_msec * 0.008) * 0.3 + 0.7
	for eye_offset in [-6, 6]:
		var eye := [cx + eye_offset, cy - 12]
		for radius in range(4, 0, -1):
			var alpha := int(200 * eye_pulse - radius * 30)
			if alpha > 0:
				_ops.append(_circle(eye, radius, _rgba(entrance, alpha), 0))
		_ops.append(_circle(eye, 2, _rgba(entrance, 255), 0))
		_ops.append(_circle(eye, 1, [255, 255, 255, 255], 0))


## Difficulty label and the five-bar meter (`GameSettings().difficulty`, hard scales by HP).
func _popup_difficulty(x: int, popup_y: int, unlock: Dictionary) -> void:
	var difficulty := String(unlock.get("difficulty", "normal"))
	var label := "NORMAL"
	var level := 1
	var color := [100, 220, 150]
	if difficulty == "hard":
		label = "HARD"
		level = mini(5, maxi(1, int(float(unlock.get("hp_mult", 1.0)) * 2.5)))
		color = [255, 120, 100]
	elif difficulty == "easy":
		label = "EASY"
		color = [100, 210, 255]
	_ops.append(_text(label, 16, color, [x, popup_y + 145]))
	for index in range(5):
		var bar := [60, 60, 70, 255]
		if index < level:
			if index >= 3:
				bar = [255, 100, 80, 255]
			elif index >= 1:
				bar = [255, 200, 80, 255]
			else:
				bar = [100, 220, 100, 255]
		_ops.append(_rect([x + index * 14, popup_y + 160, 10, 8], bar, 0, 2))


func _popup_button(timer: int, hover: bool) -> void:
	var button := play_button_rect(timer)
	var box := [button.position.x, button.position.y, button.size.x, button.size.y]
	if hover:
		var glow := [box[0] - 5, box[1] - 5, box[2] + 10, box[3] + 10]
		_ops.append(_rect(glow, [100, 255, 100, 120], 0, 8))
	var fill := [40, 180, 60, 255] if hover else [30, 140, 50, 255]
	var edge := [150, 255, 150, 255] if hover else [100, 200, 100, 255]
	_ops.append(_rect(box, fill, 0, 6))
	_ops.append(_rect(box, edge, 2, 6))
	var label := "PLAY NEXT LEVEL"
	var total_w: int = 22 + 8 + int(_measure.call(label, 26).x)
	var start_x: int = box[0] + (int(box[2]) >> 1) - (total_w >> 1)
	var center_y: int = box[1] + (int(box[3]) >> 1)
	var cx := start_x + 9
	var s := 0.55
	var play := [[cx - 6 * s, center_y - 10 * s], [cx - 6 * s, center_y + 10 * s]]
	play.append([cx + 11 * s, center_y])
	_ops.append(_polygon(play, [255, 255, 255, 255]))
	_ops.append(_text(label, 26, [255, 255, 255], [start_x + 30, center_y - 12]))


static func _offset(points: Array, cx: int, cy: int) -> Array:
	var moved: Array = []
	for point in points:
		moved.append([cx + int(point[0]), cy + int(point[1])])
	return moved


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


func _title(title: String, victory: bool, animation_time: int, cheap_alpha: bool) -> void:
	var size := title_size(animation_time)
	if cheap_alpha:
		var glow := [255, 205, 90] if victory else [255, 90, 70]
		(
			_ops
			. append(
				{
					"kind": "radial",
					"rect": [CENTER.x - 380, CENTER.y - TITLE_Y - 95, 760, 190],
					"color": glow,
					"alpha": 48,
					"mult": 255,
				}
			)
		)
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


func _stats(stats: Array, color: Array, ticks_msec: int, cheap_alpha: bool) -> void:
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
	if cheap_alpha:
		_ops.append(shadow)
		_ops.append(_vgrad(panel, [30, 34, 58], [14, 16, 30], 10))
	else:
		_ops.append(_rect(panel, [18, 20, 34, 255], 0, 10))
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
