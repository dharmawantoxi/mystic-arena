extends RefCounted
## Screen shake, ported from `_render.py::ScreenShake`: keep the largest
## request, decay every tick, cut to zero below the source threshold, and draw
## a random integer offset inside +/- int(intensity).
## `tests/screen_shake_checks.gd` replays the source oracle fixture.
##
## NOTE: `prototype_battle.gd` preserves its 8-tick inline boss shake gate
## (`boss_presentation_offset()`) for `boss_presentation_checks.gd`, and routes
## `current_screen_shake_offset()` through `boss_presentation_offset()` during
## that gate before delegating to `effects.get_shake_offset()`.

const DECAY := 0.85
const CUTOFF := 0.5

var intensity := 0.0
var decay := DECAY
var enabled := true


func add_shake(value: float) -> void:
	if not enabled:
		return
	intensity = maxf(intensity, value)


func update() -> void:
	intensity *= decay
	if intensity < CUTOFF:
		intensity = 0.0


func get_offset() -> Vector2i:
	if intensity <= 0.0:
		return Vector2i.ZERO
	var limit := int(intensity)
	return Vector2i(randi_range(-limit, limit), randi_range(-limit, limit))
