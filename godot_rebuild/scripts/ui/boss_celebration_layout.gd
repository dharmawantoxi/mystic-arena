extends RefCounted
## Layer 9be: the DRAW of `_render.py::BossDeathAnimation._draw_celebration()`
## (true boss only) as a pure op list.
##
## `ops()` replays the method against the ported state (`boss_death_animation.gd`
## already holds the overlay / bounce / reward / hint curves) and returns
## dictionaries in source order: the `darken` overlay, the gold victory tint,
## `BOSS DEFEATED!` with its shadow copies, the boss name with a drop shadow,
## the quoted title, the coin + gold reward + `HERO UNLOCKED!` block with two
## vector stars, six rotating sparkles and the pulsing skip hint:
##   darken {alpha, mult}; fill {rect, color, mult, blend};
##   circle {center, radius, color, mult, width}; line {a, b, color, mult, width};
##   text {text, size, style, color, mult, pos(top-left)}.
## `color` is RGBA 0..255 and `mult` the pygame surface alpha (255 = opaque).
## Text is centred with the `measure` callable (`text, size -> Vector2i`), so the
## oracle's fake font and the real font share one layout.
## `boss_celebration_draw_source_oracle.py` pins every op.

const LevelIntro = preload("res://scripts/ui/level_intro_layout.gd")
const SkipHint = preload("res://scripts/ui/skip_hint.gd")

## Layer 9ch: pygame asks `_skip_button_label()` per frame ("TAP" on touch, the
## controller button in controller mode, "SPACE" otherwise); `SKIP_LABEL` is only the
## keyboard fallback the caller may override through `ops(..., skip_label)`.
const SKIP_LABEL := "SPACE"
const TINT_RGBA := [80, 60, 20, 40]
const GOLD := [255, 220, 100]
const WHITE := [255, 255, 255]
const BLACK := [0, 0, 0]
const COIN_FILL := [255, 200, 50]
const COIN_EDGE := [200, 150, 30]
const COIN_MARK := [100, 60, 10]
const TITLE_RGB := [200, 200, 220]
const UNLOCK_RGB := [255, 180, 220]
const HINT_RGB := [200, 200, 200]
const HUGE_SIZE := 66
const BIG_SIZE := 46
const MEDIUM_SIZE := 32
const SMALL_SIZE := 24
const COIN_SIZE := 22
const TITLE_STYLE := "title"
const MEDIUM_STYLE := "body_semibold"
const SMALL_STYLE := "body_medium"
const COIN_STYLE := "body_bold"
const SHADOW_MAX_ALPHA := 80
const STAR_SCALE := 0.5
const STAR_STRIDES := [[1, 0], [0, 1], [1, 1], [1, -1]]
const SPARKLE_COUNT := 6
const SPARKLE_START := 0.4

var _ops: Array = []
var _measure: Callable
var _skip_label: String = SKIP_LABEL


## One frame of `draw()` for a `BossDeathAnimation` port (`ticks` is
## `pygame.time.get_ticks()`); empty unless the celebration is running.
static func ops(
	anim,
	ticks: int,
	measure: Callable,
	cheap_alpha: bool = true,
	skip_label: String = SKIP_LABEL,
) -> Array:
	var layout := new()
	layout._measure = measure
	layout._skip_label = skip_label
	layout._draw(anim, ticks, cheap_alpha)
	return layout._ops


func _draw(anim, ticks: int, cheap_alpha: bool) -> void:
	if not anim.celebration_active:
		return
	var visual: Dictionary = anim.get_celebration_visual_state(ticks)
	var overlay: int = clampi(int(visual["overlay_alpha"]), 0, 255)
	if overlay > 0:
		_ops.append({"kind": "darken", "alpha": overlay, "mult": 255})
	if bool(visual["tint_visible"]):
		(
			_ops
			. append(
				{
					"kind": "fill",
					"rect": [0, 0, int(anim.screen_w), int(anim.screen_h)],
					"color": TINT_RGBA.duplicate(),
					"mult": 255,
					"blend": 0,
				}
			)
		)
	var cx: int = _div(int(anim.screen_w), 2)
	var cy: int = _div(int(anim.screen_h), 2) - 50
	var alpha: int = int(visual["text_alpha"])
	var drop: int = int(visual["text_offset_y"])
	_headline(cx, cy + drop, alpha, cheap_alpha)
	_name_block(anim, cx, cy + drop, alpha)
	if bool(visual["reward_visible"]):
		_reward_block(anim, cx, cy, int(visual["reward_alpha"]))
	if float(visual["progress"]) > SPARKLE_START:
		_sparkles(cx, cy, ticks)
	if bool(visual["hint_visible"]):
		var hint: String = SkipHint.hint(_skip_label, "continue")
		var spot := _box(hint, SMALL_SIZE, cx, int(anim.screen_h) - 40)
		_text(hint, SMALL_SIZE, SMALL_STYLE, HINT_RGB, int(visual["hint_alpha"]), spot.position)


## `BOSS DEFEATED!`: black copies at offsets 6..1 (or one at 3), then the gold text.
func _headline(cx: int, cy: int, alpha: int, cheap_alpha: bool) -> void:
	var words := "BOSS DEFEATED!"
	var offsets: Array = [6, 5, 4, 3, 2, 1] if cheap_alpha else [3]
	for offset in offsets:
		var shadow := _box(words, HUGE_SIZE, cx + int(offset), cy - 40 + int(offset))
		_text(words, HUGE_SIZE, TITLE_STYLE, BLACK, mini(alpha, SHADOW_MAX_ALPHA), shadow.position)
	_text(words, HUGE_SIZE, TITLE_STYLE, GOLD, alpha, _box(words, HUGE_SIZE, cx, cy - 40).position)


func _name_block(anim, cx: int, cy: int, alpha: int) -> void:
	var boss_name: String = String(anim.boss_name)
	var spot := _box(boss_name, BIG_SIZE, cx, cy + 30)
	var shadow_at := spot.position + Vector2i(2, 2)
	_text(boss_name, BIG_SIZE, TITLE_STYLE, BLACK, _div(alpha, 2), shadow_at)
	_text(boss_name, BIG_SIZE, TITLE_STYLE, anim.entrance_color, alpha, spot.position)
	var quoted: String = '"%s"' % String(anim.boss_title)
	var title_spot := _box(quoted, MEDIUM_SIZE, cx, cy + 75)
	_text(quoted, MEDIUM_SIZE, MEDIUM_STYLE, TITLE_RGB, alpha, title_spot.position)


## Gold reward with its coin, then `HERO UNLOCKED!` flanked by two vector stars.
func _reward_block(anim, cx: int, cy: int, alpha: int) -> void:
	var reward: String = "+ %d GOLD" % int(anim.boss_gold_reward)
	var reward_box := _box(reward, MEDIUM_SIZE, cx, cy + 130)
	var coin := [reward_box.position.x - 30, reward_box.position.y + _div(reward_box.size.y, 2)]
	_circle(coin, 10, COIN_FILL, 0)
	_circle(coin, 10, COIN_EDGE, 2)
	var dollar_box := _box("$", COIN_SIZE, int(coin[0]), int(coin[1]))
	_text("$", COIN_SIZE, COIN_STYLE, COIN_MARK, 255, dollar_box.position)
	_text(reward, MEDIUM_SIZE, MEDIUM_STYLE, GOLD, alpha, reward_box.position)
	var unlock: String = LevelIntro.letter("HERO UNLOCKED!")
	var unlock_box := _box(unlock, SMALL_SIZE, cx, cy + 170)
	_text(unlock, SMALL_SIZE, SMALL_STYLE, UNLOCK_RGB, alpha, unlock_box.position)
	var star_ink := [
		int(255.0 * float(alpha) / 255.0),
		int(180.0 * float(alpha) / 255.0),
		int(220.0 * float(alpha) / 255.0),
	]
	_star(unlock_box.position.x - 18, cy + 170, star_ink)
	_star(unlock_box.position.x + unlock_box.size.x + 18, cy + 170, star_ink)


## `ui_theme.draw_icon(surface, "star", x, y, color, s=0.5)`.
func _star(x: int, y: int, rgb: Array) -> void:
	var reach: float = 8.0 * STAR_SCALE
	for stride in STAR_STRIDES:
		var run: float = float(stride[0]) * reach
		var rise: float = float(stride[1]) * reach
		(
			_ops
			. append(
				{
					"kind": "line",
					"a": [float(x) - run, float(y) - rise],
					"b": [float(x) + run, float(y) + rise],
					"color": _rgba(rgb),
					"mult": 255,
					"width": 2,
				}
			)
		)
	_circle([x, y], 3.0 * STAR_SCALE, rgb, 0)


func _sparkles(cx: int, cy: int, ticks: int) -> void:
	for index in range(SPARKLE_COUNT):
		var angle: float = float(ticks) * 0.001 + float(index) * PI / 3.0
		var sx: int = cx + int(cos(angle) * 220.0)
		var sy: int = cy + int(sin(angle) * 60.0)
		var pulse: float = sin(float(ticks) * 0.005 + float(index)) * 0.3 + 0.7
		_circle([sx, sy], int(4.0 * pulse), GOLD, 0)
		_circle([sx, sy], int(2.0 * pulse), WHITE, 0)


# ── op helpers ─────────────────────────────────────────────────────────────
## Python `//` (floor division) without the integer-division warning.
static func _div(value: int, divisor: int) -> int:
	return int(floor(float(value) / float(divisor)))


static func _rgba(rgb: Array, alpha: int = 255) -> Array:
	return [int(rgb[0]), int(rgb[1]), int(rgb[2]), alpha]


## `surface.get_rect(center=(cx, cy))` for the text surface of `text`.
func _box(text: String, size: int, cx: int, cy: int) -> Rect2i:
	var measured: Vector2i = _measure.call(text, size)
	return Rect2i(cx - _div(measured.x, 2), cy - _div(measured.y, 2), measured.x, measured.y)


func _text(text: String, size: int, style: String, rgb: Array, mult: int, at: Vector2i) -> void:
	(
		_ops
		. append(
			{
				"kind": "text",
				"text": text,
				"size": size,
				"style": style,
				"color": _rgba(rgb),
				"mult": mult,
				"pos": [at.x, at.y],
			}
		)
	)


func _circle(center: Array, radius: float, rgb: Array, width: int) -> void:
	(
		_ops
		. append(
			{
				"kind": "circle",
				"center": center,
				"radius": radius,
				"color": _rgba(rgb),
				"mult": 255,
				"width": width,
			}
		)
	)
