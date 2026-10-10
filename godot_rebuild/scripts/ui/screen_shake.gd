extends RefCounted
## Screen shake, ported from `_render.py::ScreenShake`: keep the largest
## request, decay every tick, cut to zero below the source threshold, and draw
## a random integer offset inside +/- int(intensity).
## `tests/screen_shake_checks.gd` replays the source oracle fixture.
##
## NOTE: `prototype_battle.gd` still carries its own inline boss shake, which
## adds an 8-tick gate and uses a cos/sin phase instead of a random offset.
## That gate is locked by boss_presentation_checks.gd, so it is deliberately
## left alone; see PETA_SISA_MIGRASI.md.

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
