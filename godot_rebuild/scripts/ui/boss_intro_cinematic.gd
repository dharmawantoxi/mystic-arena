extends RefCounted
## Boss intro banner, ported from `_render.py::BossIntroCinematic`.
##
## A 100 tick strip at the top of the screen: the boss name and title, a tag
## (TRUE / MINI BOSS), and a bar that fills as the intro runs. The banner does
## not pause gameplay. `update()` counts down and reports the first tick (the
## source plays `nexus_hit` then). `handle_skip()` ends the banner on space,
## escape or a click. The getters expose the curves the source computes inside
## `draw()`: fade in over 12 ticks, fade out over the last 20, a cubic ease-out
## slide in from the left over 18 ticks, and the HP-bar fill that reaches full
## at 85% of the duration. `level_intro_screen_source_oracle.py`-style oracles
## read those locals off the real `draw()` with `sys.settrace`.
##
## Left unported: the banner's pygame drawing (corner ticks, rounded rects) and
## the boss silhouette and aura. The source's `_draw_boss_text`,
## `_draw_hp_preview` and `_draw_skip_hint` are never called from `draw()`, so
## they are not ported either.

const DURATION := 100
const FADE_IN_TICKS := 12
const FADE_OUT_TICKS := 20
const SLIDE_TICKS := 18
const SLIDE_DISTANCE := 640
const HP_SPAN := 0.85
const BANNER_MAX_W := 600
const BANNER_MARGIN := 40
const BANNER_H := 92
const BANNER_Y := 12
const BAR_W := 150
const BAR_H := 12
const DEFAULT_RGB := [150, 100, 200]
const DEFAULT_DARK_RGB := [75, 50, 100]

var active := true
var timer := DURATION
var sound_played := false
var screen_w := 1280
var screen_h := 720

var boss_name := ""
var boss_title := ""
var boss_class := "true"
var boss_color: Array = DEFAULT_RGB.duplicate()
var boss_color_dark: Array = DEFAULT_DARK_RGB.duplicate()
var entrance_color: Array = DEFAULT_RGB.duplicate()


## `boss` holds the boss's name, title, boss_class, color, color_dark and
## entrance_color (the attributes the source reads off the Boss object).
func setup(boss: Dictionary, width: int, height: int) -> void:
	screen_w = width
	screen_h = height
	boss_name = String(boss.get("name", ""))
	boss_title = String(boss.get("title", ""))
	boss_class = String(boss.get("boss_class", "true"))
	boss_color = _to_rgb(boss.get("color", null), DEFAULT_RGB)
	boss_color_dark = _to_rgb(boss.get("color_dark", null), DEFAULT_DARK_RGB)
	entrance_color = _to_rgb(boss.get("entrance_color", null), DEFAULT_RGB)


## Counts the intro down. Returns true on the first tick only, which is the tick
## the source plays the `nexus_hit` sound.
func update() -> bool:
	if not active:
		return false
	timer -= 1
	if timer <= 0:
		active = false
	if sound_played:
		return false
	sound_played = true
	return true


## Space, escape or a click ends the banner. Returns whether this input did it.
func handle_skip(keycode: int = -1, click: bool = false) -> bool:
	if not active:
		return false
	if keycode == KEY_SPACE or keycode == KEY_ESCAPE or click:
		active = false
		return true
	return false


func is_active() -> bool:
	return active


func get_elapsed() -> int:
	return DURATION - timer


func get_alpha() -> int:
	var elapsed := get_elapsed()
	if elapsed < FADE_IN_TICKS:
		return int(255.0 * float(elapsed) / float(FADE_IN_TICKS))
	if timer < FADE_OUT_TICKS:
		return int(255.0 * float(timer) / float(FADE_OUT_TICKS))
	return 255


func get_slide_progress() -> float:
	return minf(1.0, float(get_elapsed()) / float(SLIDE_TICKS))


## Horizontal offset of the banner while it slides in from the left.
func get_slide_offset() -> int:
	var progress := get_slide_progress()
	var eased := 1.0 - pow(1.0 - progress, 3.0)
	return int((1.0 - eased) * -float(SLIDE_DISTANCE))


func get_banner_width() -> int:
	return mini(BANNER_MAX_W, screen_w - BANNER_MARGIN)


func get_banner_x() -> int:
	var free_w := screen_w - get_banner_width()
	return int(float(free_w) / 2.0) + get_slide_offset()


func get_banner_y() -> int:
	return BANNER_Y


func get_background_alpha() -> int:
	return int(210.0 * float(get_alpha()) / 255.0)


func get_border_alpha() -> int:
	return get_alpha()


func get_entrance_color() -> Array:
	return entrance_color.duplicate()


func get_hp_progress() -> float:
	return minf(1.0, float(get_elapsed()) / (float(DURATION) * HP_SPAN))


func get_hp_fill_width() -> int:
	return int(float(BAR_W) * get_hp_progress())


## HP bar rectangle [x, y, w, h], parked at the right of the banner.
func get_hp_bar_rect() -> Array:
	var bar_x := get_banner_x() + get_banner_width() - BAR_W - 16
	var bar_y := BANNER_Y + int(float(BANNER_H) / 2.0) - int(float(BAR_H) / 2.0)
	return [bar_x, bar_y, BAR_W, BAR_H]


func get_tag() -> Dictionary:
	if boss_class == "true":
		return {"text": "TRUE BOSS", "color": [255, 90, 90]}
	return {"text": "MINI BOSS", "color": [255, 200, 100]}


static func _to_rgb(value: Variant, fallback: Array) -> Array:
	if not (value is Array) or value.size() < 3:
		return fallback.duplicate()
	return [int(value[0]), int(value[1]), int(value[2])]
