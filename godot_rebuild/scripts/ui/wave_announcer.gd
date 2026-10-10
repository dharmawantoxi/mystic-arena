extends RefCounted
## Big animated "WAVE n" banner, ported from `_render.py::WaveAnnouncer`.
##
## `announce()`/`update()` own the 120 tick lifetime; `get_offset_x()` and
## `get_alpha()` expose the three phase presentation curve the source computes
## inside `draw()` (slide in 0 → 0.2, hold 0.2 → 0.7, slide out 0.7 → 1).
## Left unported: the banner's gradient fill, gold border, diagonal decoration
## and text blits, which are pygame drawing rather than state.
##
## The easing helpers are duplicated from `popup_animation.gd` on purpose so
## each port stays standalone; both are verified against the same source
## functions by their own oracles.

const DURATION := 120
const SLIDE_IN_END := 0.2
const HOLD_END := 0.7
const SLIDE_IN_SPAN := 0.2
const SLIDE_OUT_SPAN := 0.3
const EASE_C1 := 1.70158

var active := false
var wave_num := 0
var timer := 0
var duration := DURATION


func announce(value: int) -> void:
	active = true
	wave_num = value
	timer = duration


func update() -> void:
	if not active:
		return
	timer -= 1
	if timer <= 0:
		active = false


func progress() -> float:
	return 1.0 - (float(timer) / float(duration))


func title() -> String:
	return "WAVE %d" % wave_num


func get_offset_x(screen_w: int) -> int:
	var elapsed := progress()
	if elapsed < SLIDE_IN_END:
		var slide := elapsed / SLIDE_IN_SPAN
		return -screen_w + int(float(screen_w) * _ease_out_back(slide))
	if elapsed < HOLD_END:
		return 0
	var slide_out := (elapsed - HOLD_END) / SLIDE_OUT_SPAN
	return int(float(screen_w) * _ease_in_back(slide_out))


func get_alpha() -> int:
	var elapsed := progress()
	if elapsed < SLIDE_IN_END:
		var slide := elapsed / SLIDE_IN_SPAN
		return int(255.0 * min(1.0, slide * 2.0))
	if elapsed < HOLD_END:
		return 255
	var slide_out := (elapsed - HOLD_END) / SLIDE_OUT_SPAN
	return int(255.0 * (1.0 - slide_out))


static func _ease_out_back(t: float) -> float:
	var c1 := EASE_C1
	var c3 := c1 + 1.0
	var t1 := t - 1.0
	return 1.0 + c3 * (t1 * t1 * t1) + c1 * (t1 * t1)


static func _ease_in_back(t: float) -> float:
	var c1 := EASE_C1
	var c3 := c1 + 1.0
	return c3 * t * t * t - c1 * t * t
