extends RefCounted
## Lane path preview, ported from `_render.py::PathPreview`.
##
## `show()`/`update()` own the 120 tick lifetime and clear the stored lanes on
## expiry. `get_alpha()` reproduces the fade in / hold / fade out curve the
## source computes inside `draw()`, and the dash helpers reproduce the moving
## dash phase and the per-arrow pulse that picks a size and an alpha.
##
## `arrow_points()` translates the source's triangle offsets out of its 20x20
## pygame surface and back into world coordinates, preserving Python floor
## division for negative half-vectors.

const DURATION := 120
const FADE_IN := 20
const FADE_OUT := 40
const MAX_ALPHA := 200
const DASH_PERIOD := 20
const DASH_SPEED := 2
const PULSE_STRIDE := 8
const PULSE_DIVISOR := 5
const PULSE_STEPS := 4
const ARROW_BIG := 8
const ARROW_SMALL := 5

var active := false
var paths: Array = []
var timer := 0
var duration := DURATION


func show(lane_paths: Array) -> void:
	active = true
	paths = lane_paths
	timer = duration


func update() -> void:
	if not active:
		return
	timer -= 1
	if timer <= 0:
		active = false
		paths = []


## Fades in over the first 20 ticks, holds, then fades out over the last 40.
## The source returns early once this reaches 0, so callers should too.
func get_alpha() -> int:
	if timer > duration - FADE_IN:
		return int(float(MAX_ALPHA) * (float(duration - timer) / float(FADE_IN)))
	if timer < FADE_OUT:
		return int(float(MAX_ALPHA) * (float(timer) / float(FADE_OUT)))
	return MAX_ALPHA


static func dash_offset(animation_time: float) -> int:
	return int(animation_time * float(DASH_SPEED)) % DASH_PERIOD


static func pulse_index(point_index: int, animation_time: float) -> int:
	return (point_index / PULSE_STRIDE + dash_offset(animation_time) / PULSE_DIVISOR) % PULSE_STEPS


static func arrow_size(pulse: int) -> int:
	return ARROW_BIG if pulse == 0 else ARROW_SMALL


static func arrow_alpha(base_alpha: int, pulse: int) -> int:
	return base_alpha if pulse == 0 else base_alpha / 2


## Reproduces source points after `blit(arrow_surf, (int(x)-10, int(y)-10))`.
static func arrow_points(
	point: Vector2, next_point: Vector2, arrow_size_value: int
) -> PackedVector2Array:
	var direction := next_point - point
	var distance := direction.length()
	if distance == 0.0:
		distance = 1.0
		direction = Vector2.ZERO
	else:
		direction /= distance
	var cos_a := direction.x
	var sin_a := direction.y
	var half := float(arrow_size_value)
	var nose := Vector2(10 + int(cos_a * half), 10 + int(sin_a * half))
	var left := Vector2(
		10 + int(floor(-cos_a * half / 2.0) - floor(sin_a * half / 2.0)),
		10 + int(floor(-sin_a * half / 2.0) + floor(cos_a * half / 2.0))
	)
	var right := Vector2(
		10 + int(floor(-cos_a * half / 2.0) + floor(sin_a * half / 2.0)),
		10 + int(floor(-sin_a * half / 2.0) - floor(cos_a * half / 2.0))
	)
	var blit_origin := Vector2(int(point.x) - 10, int(point.y) - 10)
	return PackedVector2Array([blit_origin + nose, blit_origin + left, blit_origin + right])
