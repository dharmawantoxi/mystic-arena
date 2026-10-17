extends RefCounted
## Layer 9av: the DRAW of `_render.py::LevelIntroScreen` as a pure op list.
##
## `ops()` replays `draw()` / `_draw_level_info` / `_draw_boss_preview` /
## `_draw_boss_silhouette` / `_draw_space_prompt` (mobile `cheap_alpha` path)
## and returns dictionaries in source order:
##   darken {alpha}; fill/rect {rect, color, width, radius}; circle {center,
##   radius, width}; line {a, b, width}; polygon {points}; text {text, size,
##   color, mult, pos, w, h}.
## `color` is RGBA 0..255, `mult` the pygame surface alpha the op was blitted
## with (255 = opaque). Text metrics come from the `measure` callable
## (`text, size -> Vector2i`) so the oracle's fake font and the real font share
## the same layout code. `level_intro_draw_source_oracle.py` pins every op.

const FADE_IN := 30
const THEME_TINTS := {
	"desert": [100, 60, 20],
	"ice": [40, 80, 130],
	"ocean": [30, 70, 120],
	"abyss": [40, 10, 10],
	"nethervenom": [25, 55, 15],
	"spectral": [15, 50, 55],
	"sundered": [70, 30, 8],
	"empyrean": [70, 55, 15],
	"solaris": [85, 50, 10],
	"abysstide": [10, 50, 50],
	"crimsonmatriarch": [60, 10, 15],
	"astral": [15, 25, 60],
	"shadowchain": [45, 12, 60],
	"frostveil": [25, 45, 85],
	"warshade": [10, 40, 48],
	"outlaw": [80, 45, 35],
	"hexbound": [55, 25, 75],
	"voidbound": [45, 18, 70],
	"earthborn": [45, 55, 25],
	"heartbane": [60, 18, 55],
	"sunfist": [80, 55, 12],
	"voidwing": [45, 15, 65],
	"crimsondevourer": [60, 10, 15],
	"elementweave": [55, 30, 75],
	"tempest": [20, 40, 90],
	"sawmill": [70, 45, 18],
	"croweye": [55, 12, 18],
	"crystalstorm": [30, 45, 85],
	"eternalwarlord": [70, 15, 20],
	"explosiveart": [70, 18, 18],
	"sandshadow": [85, 35, 22],
	"emberweaver": [95, 28, 22],
	"skyfury": [70, 45, 20],
}
const FOREST_TINT := [20, 40, 20]
const GOLD := [255, 220, 100]
const TICK_GOLD := [255, 220, 120]
const ICON_INK := [10, 12, 22]
const WARNING_TEXT := "PREPARE FOR BATTLE"

var _ops: Array = []
var _measure: Callable


## Source fade: `int(255 * timer / 30)` until frame 30, then 255.
static func fade_alpha(timer: int) -> int:
	if timer < FADE_IN:
		return int(255.0 * (float(timer) / float(FADE_IN)))
	return 255


static func theme_tint(map_theme: String) -> Array:
	return THEME_TINTS.get(map_theme, FOREST_TINT)


## `ui_theme.letter`: manual letter spacing.
static func letter(text: String, gap: String = " ") -> String:
	var parts := PackedStringArray()
	for character in text:
		parts.append(character)
	return gap.join(parts)


## Full frame. `state` is `Prototype.level_intro_state()` (+ boss colours),
## `timer` the intro frame counter, `ticks_ms` `pygame.time.get_ticks()`.
static func ops(
	state: Dictionary, timer: int, ticks_ms: int, measure: Callable, screen: Vector2i
) -> Array:
	var layout := new()
	layout._measure = measure
	layout._draw(state, timer, ticks_ms, screen.x, screen.y)
	return layout._ops


func _draw(state: Dictionary, timer: int, ticks: int, w: int, h: int) -> void:
	var alpha := fade_alpha(timer)
	_ops.append({"kind": "darken", "alpha": mini(255, alpha + 30), "mult": 255})
	var tint := theme_tint(String(state.get("map_theme", "forest")))
	(
		_ops
		. append(
			{
				"kind": "fill",
				"rect": [0, 0, w, h],
				"color": [tint[0], tint[1], tint[2], int(30.0 * (float(alpha) / 255.0))],
				"mult": 255,
				"blend": 0,
			}
		)
	)
	for index in range(60):
		_rect([index, index, w - index * 2, h - index * 2], [0, 0, 0, index * 3], 1, 0, alpha)
	var divider_x := _div(w, 2)
	_line([divider_x, 100], [divider_x, h - 100], [100, 100, 130, alpha], 2)
	for index in range(3):
		var y := 250 + index * 200
		_polygon(
			[
				[divider_x, y - 8],
				[divider_x + 8, y],
				[divider_x, y + 8],
				[divider_x - 8, y],
			],
			_rgba(GOLD)
		)
	_level_info(state, alpha, w)
	_boss_preview(state, alpha, ticks, w, h)
	if timer > FADE_IN:
		_space_prompt(String(state.get("prompt_text", "PRESS SPACE TO BEGIN")), ticks, w, h)


func _level_info(state: Dictionary, alpha: int, w: int) -> void:
	var cx := _div(w, 4)
	var cy_start := 130
	_text_centered("LEVEL", 32, [180, 200, 220], alpha, cx, cy_start)
	var number := str(int(state.get("level_num", 1)))
	for offset in range(6, 0, -1):
		_text_centered(
			number, 200, [0, 0, 0], mini(alpha, 60), cx + offset, cy_start + 100 + offset
		)
	_text_centered(number, 200, GOLD, alpha, cx, cy_start + 100)
	var line_y := cy_start + 220
	_line([cx - 150, line_y], [cx + 150, line_y], _rgba(GOLD, alpha), 2)
	_line([cx - 100, line_y + 3], [cx + 100, line_y + 3], [255, 255, 200, alpha], 1)
	var level_name := String(state.get("level_name", ""))
	_text_centered(level_name, 46, [0, 0, 0], _div(alpha, 2), cx + 2, cy_start + 260 + 2)
	_text_centered(level_name, 46, [240, 240, 250], alpha, cx, cy_start + 260)
	_text_centered(
		String(state.get("level_desc", "")), 24, [180, 200, 220], alpha, cx, cy_start + 310
	)
	var diff_y := cy_start + 370
	var difficulty := String(state.get("difficulty_id", "normal"))
	var diff_title := "DIFFICULTY: NORMAL"
	var diff_level := 1
	var diff_color := [100, 220, 150]
	if difficulty == "hard":
		diff_title = "DIFFICULTY: HARD"
		diff_level = mini(5, maxi(1, int(float(state.get("hp_mult", 1.0)) * 2.5)))
		diff_color = [255, 120, 100]
	elif difficulty == "easy":
		diff_title = "DIFFICULTY: EASY"
		diff_color = [100, 210, 255]
	_text_centered(diff_title, 20, diff_color, alpha, cx, diff_y)
	var bar_start_x := cx - _div(5 * 22, 2)
	for index in range(5):
		var bar_col := [60, 60, 70]
		if index < diff_level:
			if index >= 3:
				bar_col = [255, 100, 80]
			elif index >= 1:
				bar_col = [255, 200, 80]
			else:
				bar_col = [100, 220, 100]
		_rect([bar_start_x + index * 22, diff_y + 20, 18, 10], _rgba(bar_col, alpha), 0, 2, 255)
	var reward_y := cy_start + 430
	_text_centered("VICTORY REWARD", 20, [150, 170, 190], alpha, cx, reward_y)
	_coin(cx - 60, reward_y + 30)
	_text_at(
		String(state.get("reward_text", "")), 32, GOLD, alpha, cx - 60 + 18, reward_y + 30 - 12
	)
	var start_y := reward_y + 78
	_text_centered("STARTING GOLD", 20, [150, 170, 190], alpha, cx, start_y)
	_coin(cx - 60, start_y + 30)
	_text_at(
		String(state.get("starting_gold_text", "")),
		32,
		GOLD,
		alpha,
		cx - 60 + 18,
		start_y + 30 - 12
	)
	_text_centered(
		String(state.get("passive_text", "")), 20, [196, 241, 168], alpha, cx, start_y + 58
	)


func _coin(x: int, y: int) -> void:
	_circle([x, y], 12, [255, 200, 50, 255], 0)
	_circle([x, y], 12, [200, 150, 30, 255], 2)
	_text_centered("$", 24, [100, 60, 10], 255, x, y)


func _boss_preview(state: Dictionary, alpha: int, ticks: int, w: int, h: int) -> void:
	var cx := _div(w * 3, 4)
	var cy := _div(h, 2)
	_text_centered("FINAL BOSS", 32, [255, 100, 100], alpha, cx, 130)
	var is_true := String(state.get("boss_class", "true")) == "true"
	var tag_text := "TRUE BOSS" if is_true else "MINI BOSS"
	var tag_color := [255, 80, 80] if is_true else [255, 200, 100]
	var tag_size: Vector2i = _measure.call(tag_text, 24)
	var tag_x := cx - _div(tag_size.x, 2)
	var tag_y := 165 - _div(tag_size.y, 2)
	var bg := [tag_x - 15, tag_y - 4, tag_size.x + 30, tag_size.y + 8]
	_rect(bg, _rgba(tag_color, _div(alpha, 4)), 0, 6, 255)
	_rect(bg, _rgba(tag_color, alpha), 2, 6, 255)
	_text_op(tag_text, 24, tag_color, alpha, tag_x, tag_y, tag_size)
	var entrance: Array = state.get("boss_entrance_color", [150, 100, 200])
	var dark: Array = state.get("boss_color_dark", [75, 50, 100])
	_silhouette(cx, cy - 20, alpha, ticks, entrance, dark, is_true)
	var name_y := cy + 180
	var boss_name := String(state.get("boss_name", ""))
	for offset in range(5, 0, -1):
		_text_centered(boss_name, 46, [0, 0, 0], mini(alpha, 80), cx + offset, name_y + offset)
	_text_centered(boss_name, 46, entrance, alpha, cx, name_y)
	var title_text := '"%s"' % String(state.get("boss_title", ""))
	var title_size: Vector2i = _measure.call(title_text, 32)
	var title_x := cx - _div(title_size.x, 2)
	var title_y := name_y + 45 - _div(title_size.y, 2)
	_text_op(title_text, 32, [0, 0, 0], _div(alpha, 2), title_x + 2, title_y + 2, title_size)
	_text_op(title_text, 32, [200, 200, 220], alpha, title_x, title_y, title_size)
	var pulse := sin(float(ticks) * 0.005) * 0.3 + 0.7
	var warning := letter(WARNING_TEXT)
	var warning_size: Vector2i = _measure.call(warning, 24)
	var warning_x := cx - _div(warning_size.x, 2)
	var warning_y := name_y + 95 - _div(warning_size.y, 2)
	_text_op(
		warning, 24, [255, 110, 100], int(float(alpha) * pulse), warning_x, warning_y, warning_size
	)
	var icon_col := [int(255.0 * pulse), int(100.0 * pulse), int(90.0 * pulse)]
	for side_x in [warning_x - 22, warning_x + warning_size.x + 22]:
		_warn_icon(float(side_x), float(name_y + 95), icon_col, 0.6)


## `ui_theme.draw_icon(surf, "warn", cx, cy, color, s)`.
func _warn_icon(cx: float, cy: float, color: Array, s: float) -> void:
	_polygon(
		[[cx, cy - 9.0 * s], [cx + 10.0 * s, cy + 8.0 * s], [cx - 10.0 * s, cy + 8.0 * s]],
		_rgba(color)
	)
	_line([cx, cy - 4.0 * s], [cx, cy + 2.0 * s], _rgba(ICON_INK), 2)
	_circle([cx, cy + 5.0 * s], 1.5 * s, _rgba(ICON_INK), 0)


func _silhouette(
	cx: int, cy: int, alpha: int, ticks: int, entrance: Array, dark: Array, is_true: bool
) -> void:
	var aura_pulse := sin(float(ticks) * 0.003) * 0.3 + 0.7
	var aura_r := int(140.0 * aura_pulse)
	var radius := aura_r
	while radius > 20:
		var aura_alpha := int(float(aura_r - radius) * 1.5 * (float(alpha) / 255.0))
		if aura_alpha > 0:
			var ring := _circle([cx, cy], radius, _rgba(entrance, aura_alpha), 0)
			ring["ring_inner"] = maxi(radius - 6, 0) if radius - 6 > 20 else 0
		radius -= 6
	var ray_alpha := int(50.0 * (float(alpha) / 255.0))
	for index in range(12):
		var angle := float(index) * PI * 2.0 / 12.0 + float(ticks) * 0.0005
		var sx := cx + int(cos(angle) * 90.0)
		var sy := cy + int(sin(angle) * 90.0)
		var ex := cx + int(cos(angle) * 180.0)
		var ey := cy + int(sin(angle) * 180.0)
		_line([sx, sy], [ex, ey], _rgba(entrance, ray_alpha), 3)
	var body := [
		[cx - 55, cy - 20],
		[cx - 35, cy - 75],
		[cx, cy - 95],
		[cx + 35, cy - 75],
		[cx + 55, cy - 20],
		[cx + 65, cy + 35],
		[cx + 45, cy + 85],
		[cx - 45, cy + 85],
		[cx - 65, cy + 35],
	]
	var shadow: Array = []
	for point in body:
		shadow.append([point[0] + 3, point[1] + 3])
	_polygon(shadow, [0, 0, 0, _div(alpha, 2)])
	_polygon(body, [0, 0, 0, alpha])
	_polygon(
		[
			[cx - 50, cy - 15],
			[cx - 30, cy - 70],
			[cx, cy - 90],
			[cx + 30, cy - 70],
			[cx + 50, cy - 15],
			[cx + 60, cy + 30],
			[cx + 40, cy + 80],
			[cx - 40, cy + 80],
			[cx - 60, cy + 30],
		],
		_rgba(dark, _div(alpha, 3))
	)
	var spikes := 5 if is_true else 3
	for index in range(spikes):
		var spike_x := (cx - 40 + index * 20) if spikes == 5 else (cx - 20 + index * 20)
		var spike_y := cy - 95
		var height := 25 + (index % 2) * 10
		_polygon(
			[[spike_x - 6, spike_y], [spike_x, spike_y - height], [spike_x + 6, spike_y]],
			[0, 0, 0, alpha]
		)
	var eye_pulse := sin(float(ticks) * 0.008) * 0.3 + 0.7
	for eye_x in [cx - 20, cx + 20]:
		var glow := 12
		while glow > 0:
			var a := int(200.0 * eye_pulse * (float(alpha) / 255.0) - float(glow * 12))
			if a > 0:
				var ring := _circle([eye_x, cy - 40], glow, _rgba(entrance, a), 0)
				ring["ring_inner"] = glow - 2
			glow -= 2
		var eye_alpha := int(255.0 * (float(alpha) / 255.0))
		_circle([eye_x, cy - 50], 5, _rgba(entrance, eye_alpha), 0)
		_circle([eye_x, cy - 50], 2, [255, 255, 255, eye_alpha], 0)


func _space_prompt(prompt: String, ticks: int, w: int, h: int) -> void:
	var pulse := sin(float(ticks) * 0.005) * 0.3 + 0.7
	var prompt_y := h - 60
	var cx := _div(w, 2)
	var bar_w := 400
	var bar_h := 45
	var bar_x := cx - _div(bar_w, 2)
	var bar_y := prompt_y - _div(bar_h, 2)
	_rect([bar_x, bar_y, bar_w, bar_h], [0, 0, 0, int(150.0 * pulse)], 0, 10, 255)
	_rect([bar_x, bar_y, bar_w, bar_h], _rgba(GOLD, int(220.0 * pulse)), 2, 10, 255)
	if pulse > 0.5:
		_corner_ticks(bar_x, bar_y, bar_w, bar_h, _rgba(TICK_GOLD), 10, 2, 4)
	var size: Vector2i = _measure.call(prompt, 32)
	var px := cx - _div(size.x, 2)
	var py := prompt_y - _div(size.y, 2)
	_text_op(prompt, 32, [0, 0, 0], int(150.0 * pulse), px + 2, py + 2, size)
	_text_op(prompt, 32, GOLD, int(255.0 * pulse), px, py, size)
	var arrow_offset := int(sin(float(ticks) * 0.005) * 5.0)
	var left := bar_x - 30 - arrow_offset
	_polygon(
		[[left, prompt_y], [left + 15, prompt_y - 10], [left + 15, prompt_y + 10]], _rgba(GOLD)
	)
	var right := bar_x + bar_w + 15 + arrow_offset
	_polygon(
		[[right, prompt_y], [right - 15, prompt_y - 10], [right - 15, prompt_y + 10]], _rgba(GOLD)
	)


## `ui_theme.corner_ticks`.
func _corner_ticks(
	x: int, y: int, w: int, h: int, color: Array, length: int, width: int, inset: int
) -> void:
	var corners := [
		[x + inset, y + inset, 1, 1],
		[x + w - inset, y + inset, -1, 1],
		[x + inset, y + h - inset, 1, -1],
		[x + w - inset, y + h - inset, -1, -1],
	]
	for corner in corners:
		var ax: int = corner[0]
		var ay: int = corner[1]
		_line([ax, ay], [ax + corner[2] * length, ay], color, width)
		_line([ax, ay], [ax, ay + corner[3] * length], color, width)


# ── op helpers ─────────────────────────────────────────────────────────────
## Python `//` (floor division) without the integer-division warning.
static func _div(value: int, divisor: int) -> int:
	return int(floor(float(value) / float(divisor)))


static func _rgba(rgb: Array, alpha: int = 255) -> Array:
	return [int(rgb[0]), int(rgb[1]), int(rgb[2]), alpha]


func _rect(rect: Array, color: Array, width: int, radius: int, mult: int) -> void:
	_ops.append(
		{
			"kind": "rect",
			"rect": rect,
			"color": color,
			"mult": mult,
			"width": width,
			"radius": radius
		}
	)


func _circle(center: Array, radius: float, color: Array, width: int) -> Dictionary:
	var op := {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"color": color,
		"mult": 255,
		"width": width
	}
	_ops.append(op)
	return op


func _line(a: Array, b: Array, color: Array, width: int) -> void:
	_ops.append({"kind": "line", "a": a, "b": b, "color": color, "mult": 255, "width": width})


func _polygon(points: Array, color: Array) -> void:
	_ops.append({"kind": "polygon", "points": points, "color": color, "mult": 255, "width": 0})


func _text_centered(text: String, size: int, rgb: Array, mult: int, cx: int, cy: int) -> void:
	var measured: Vector2i = _measure.call(text, size)
	_text_op(text, size, rgb, mult, cx - _div(measured.x, 2), cy - _div(measured.y, 2), measured)


func _text_at(text: String, size: int, rgb: Array, mult: int, x: int, y: int) -> void:
	_text_op(text, size, rgb, mult, x, y, _measure.call(text, size))


func _text_op(
	text: String, size: int, rgb: Array, mult: int, x: int, y: int, measured: Vector2i
) -> void:
	(
		_ops
		. append(
			{
				"kind": "text",
				"text": text,
				"size": size,
				"color": _rgba(rgb),
				"mult": mult,
				"pos": [x, y],
				"w": measured.x,
				"h": measured.y,
			}
		)
	)
