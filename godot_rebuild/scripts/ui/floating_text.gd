extends RefCounted
## Floating damage numbers, ported from `_render.py::FloatingText`. The update
## order and every constant mirror the source; `tests/floating_text_checks.gd`
## replays the source oracle fixture to prove it. Presentation only: the text
## surface is owned by whoever draws it.

const FONT_SIZES := {"small": 14, "medium": 18, "large": 24, "huge": 32}
const DEFAULT_FONT_SIZE := 18

const SCALE_START := 0.3
const CRITICAL_TARGET := 1.2
const NORMAL_TARGET := 1.0
const VELOCITY_DECAY := 0.95
const SCALE_LERP := 0.3
const SCALE_SHRINK := 0.99
const ALPHA_WINDOW := 0.5
const DRIFT_RANGE := 0.3

var x := 0.0
var y := 0.0
var text := ""
var color := Color.WHITE
var velocity_x := 0.0
var velocity_y := 0.0
var lifetime := 0
var max_lifetime := 0
var alive := false
var critical := false
var font_size := DEFAULT_FONT_SIZE
var x_drift := 0.0
var scale := SCALE_START
var target_scale := NORMAL_TARGET


static func font_size_for(size: String) -> int:
	return int(FONT_SIZES.get(size, DEFAULT_FONT_SIZE))


## `drift` stays injectable so the source oracle fixture can pin the random
## horizontal drift the source draws from `random.uniform`.
func configure(
	pos_x: float,
	pos_y: float,
	value: String,
	tint: Color,
	size: String = "medium",
	velocity := Vector2(0.0, -2.0),
	life: int = 45,
	is_critical: bool = false,
	drift: float = NAN
) -> void:
	x = pos_x
	y = pos_y
	text = value
	color = tint
	velocity_x = velocity.x
	velocity_y = velocity.y
	lifetime = life
	max_lifetime = life
	alive = true
	critical = is_critical
	font_size = font_size_for(size)
	x_drift = drift if not is_nan(drift) else randf_range(-DRIFT_RANGE, DRIFT_RANGE)
	scale = SCALE_START
	target_scale = CRITICAL_TARGET if is_critical else NORMAL_TARGET


func update() -> void:
	if not alive:
		return
	x += velocity_x + x_drift
	y += velocity_y
	velocity_y *= VELOCITY_DECAY
	if scale < target_scale:
		scale += (target_scale - scale) * SCALE_LERP
	else:
		scale *= SCALE_SHRINK
	lifetime -= 1
	if lifetime <= 0:
		alive = false


func alpha_ratio() -> float:
	return minf(1.0, float(lifetime) / (float(max_lifetime) * ALPHA_WINDOW))


func alpha() -> int:
	return int(255.0 * alpha_ratio())
