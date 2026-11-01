class_name FixedClock
extends RefCounted

## main.py's frame-based simulation, independent of the render frame rate.
const HZ := 60.0
const STEP := 1.0 / HZ
const MAX_CATCHUP := 4
const MAX_FRAME_DELTA := 0.250

var accumulator := 0.0
var capped_frames := 0
var total_steps := 0
var last_steps := 0


func advance(delta: float) -> int:
	accumulator += clampf(delta, 0.0, MAX_FRAME_DELTA)
	var steps := 0
	while accumulator >= STEP and steps < MAX_CATCHUP:
		accumulator -= STEP
		steps += 1
	if steps >= MAX_CATCHUP:
		accumulator = minf(accumulator * 0.5, STEP * 3.0)
		capped_frames += 1
	last_steps = steps
	total_steps += steps
	return steps


func reset() -> void:
	accumulator = 0.0
	last_steps = 0


func status() -> String:
	return "%dx/frame  mentok %d" % [last_steps, capped_frames]
