extends RefCounted
## Layer 9bq11: `bosses/base_boss.py::Boss._draw_entrance`, the aura and the wrapped title the
## boss paints on the tick it enters the arena. `Boss.draw` calls it instead of everything else
## while `entrance_timer > 0`, so no other layer of the boss exists on those frames.
##
##   progress = 1 - entrance_timer / max_timer
##   size     = int(radius * progress * 2)
##   size > 0 -> filled circle `(*entrance_color, clamp(int(200 * (1 - progress))))` at the boss
##              (the source builds a `size * 3` square surface, draws at its centre and blits it
##              at `x - size * 3 // 2`, which lands exactly on the boss)
##   entrance_timer > max_timer // 2 ->
##       pulse  = sin(anim_time * 0.2) * 0.3 + 0.7
##       alpha  = clamp(int(255 * pulse))
##       lines  = greedy word wrap of `entrance_text` at 1000 px using the font's own metrics
##       start_y = 84 - (len(lines) - 1) * 18, each line 34 px lower
##       per line: black shadow at `(rect.x + 2, rect.y + 2)` with
##                 `clamp(int(200 * pulse))`, then the text itself; both centred on
##                 `(SCREEN_WIDTH // 2, ly)` the way `get_rect(center=...)` does.
##
## Font metrics are the only thing this file cannot own, so `measure` is a Callable returning
## `Vector2(width, height)` for `(line, font_size)` - the view passes the real `Barlow-SemiBold`
## metrics and
## the suite passes the recording shim's `int(size * 0.55) x size`.

const SCREEN_WIDTH := 1280
const TEXT_MAX_WIDTH := 1000
const TEXT_START_Y := 84
const LINE_STEP := 34
const LINE_PACK := 18
const SHADOW_OFFSET := 2
const SHADOW_ALPHA := 200
const TEXT_ALPHA := 255
const AURA_ALPHA := 200
const TRUE_FONT_SIZE := 28
const BODY_FONT_SIZE := 24
const STYLE := "body_semibold"
const TRUE_ENTRANCE := 180
const BODY_ENTRANCE := 120
const SHADOW_COLOR := [0, 0, 0, 255]


## `max_timer` is the source's `180 if boss_class == "true" else 120`; `progress` is its
## `1 - entrance_timer / max_timer`.
static func progress(entrance_timer: int, max_timer: int) -> float:
	return 1.0 - float(entrance_timer) / float(max_timer)


static func aura_radius(radius: int, entrance_progress: float) -> int:
	return int(float(radius) * entrance_progress * 2.0)


static func aura_alpha(entrance_progress: float) -> int:
	return clampi(int(float(AURA_ALPHA) * (1.0 - entrance_progress)), 0, 255)


static func text_visible(entrance_timer: int, max_timer: int) -> bool:
	return entrance_timer > (max_timer >> 1)


## `max_entrance = 180 if is_true else 120`, the literal `Boss.draw` passes in.
static func max_entrance(is_true: bool) -> int:
	return TRUE_ENTRANCE if is_true else BODY_ENTRANCE


static func font_size(is_true: bool) -> int:
	return TRUE_FONT_SIZE if is_true else BODY_FONT_SIZE


## `pulse = sin(anim_time * 0.2) * 0.3 + 0.7`, clamped the way the source clamps the alphas.
static func pulse(anim_time: float) -> float:
	return sin(anim_time * 0.2) * 0.3 + 0.7


## One frame: the filled aura while it has a radius, then the shadow/text op of every wrapped
## line while `entrance_timer > max_timer // 2`.
static func ops(
	x: int,
	y: int,
	radius: int,
	entrance_timer: int,
	max_timer: int,
	entrance_color: Array,
	entrance_text: String,
	is_true: bool,
	anim_time: float,
	measure: Callable
) -> Array:
	var out: Array = []
	var entrance_progress := progress(entrance_timer, max_timer)
	var size := aura_radius(radius, entrance_progress)
	if size > 0:
		var ink: Array = [
			int(entrance_color[0]),
			int(entrance_color[1]),
			int(entrance_color[2]),
			aura_alpha(entrance_progress),
		]
		(
			out
			. append(
				{
					"kind": "circle",
					"center": [x, y],
					"radius": size,
					"width": 0,
					"mult": 255,
					"color": ink,
				}
			)
		)
	if not text_visible(entrance_timer, max_timer):
		return out
	var size_px := font_size(is_true)
	var beat := pulse(anim_time)
	var alpha := clampi(int(float(TEXT_ALPHA) * beat), 0, 255)
	var shadow := clampi(int(float(SHADOW_ALPHA) * beat), 0, 255)
	var lines: Array = wrap(entrance_text, size_px, measure)
	var start_y: int = TEXT_START_Y - (lines.size() - 1) * LINE_PACK
	var index := 0
	for line in lines:
		var ly: int = start_y + index * LINE_STEP
		var metrics: Vector2 = measure.call(line, size_px)
		var left: int = (SCREEN_WIDTH >> 1) - (int(metrics.x) >> 1)
		var top: int = ly - (int(metrics.y) >> 1)
		out.append(
			_text(line, size_px, SHADOW_COLOR, [left + SHADOW_OFFSET, top + SHADOW_OFFSET], shadow)
		)
		out.append(_text(line, size_px, entrance_color, [left, top], alpha))
		index += 1
	return out


## Greedy word wrap from the source: a word joins the current line while the trial line still
## measures at most 1000 px; any remaining word starts a new one.
static func wrap(text: String, size_px: int, measure: Callable) -> Array:
	var lines: Array = []
	var current := ""
	for word in text.split(" ", false):
		var trial: String = current + " " + word if not current.is_empty() else word
		var metrics: Vector2 = measure.call(trial, size_px)
		if metrics.x <= float(TEXT_MAX_WIDTH):
			current = trial
		else:
			if not current.is_empty():
				lines.append(current)
			current = word
	if not current.is_empty():
		lines.append(current)
	if lines.is_empty():
		lines.append(text)
	return lines


static func _text(line: String, size_px: int, rgb: Array, pos: Array, alpha: int) -> Dictionary:
	return {
		"kind": "text",
		"text": line,
		"size": size_px,
		"style": STYLE,
		"color": [int(rgb[0]), int(rgb[1]), int(rgb[2]), 255],
		"mult": alpha,
		"pos": [pos[0], pos[1]],
	}
