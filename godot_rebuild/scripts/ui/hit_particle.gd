extends RefCounted
## Hit spark, ported from `_render.py::HitParticle`. The update order and every
## constant mirror the source; `tests/hit_particle_checks.gd` replays the source
## oracle fixture to prove it. Presentation only: the sprite is owned by
## whoever draws it.

const GRAVITY := 0.15
const FRICTION := 0.95
const SPEED_MIN := 1.0
const SPEED_MAX := 3.0

var x := 0.0
var y := 0.0
var color := Color.WHITE
var vx := 0.0
var vy := 0.0
var lifetime := 0
var max_lifetime := 0
var size := 2
var alive := false
var gravity := GRAVITY


## NaN components ask for the random cone the source draws from
## `random.uniform`; the oracle pins the result so the suite can replay it.
func configure(
	pos_x: float,
	pos_y: float,
	tint: Color,
	velocity := Vector2(NAN, NAN),
	life: int = 15,
	particle_size: int = 2
) -> void:
	x = pos_x
	y = pos_y
	color = tint
	if is_nan(velocity.x) or is_nan(velocity.y):
		var angle := randf_range(0.0, TAU)
		var speed := randf_range(SPEED_MIN, SPEED_MAX)
		vx = cos(angle) * speed
		vy = sin(angle) * speed
	else:
		vx = velocity.x
		vy = velocity.y
	lifetime = life
	max_lifetime = life
	size = particle_size
	alive = true


func update() -> void:
	if not alive:
		return
	x += vx
	y += vy
	vy += gravity
	vx *= FRICTION
	lifetime -= 1
	if lifetime <= 0:
		alive = false


func alpha_ratio() -> float:
	return float(lifetime) / float(max_lifetime)


func alpha() -> int:
	return int(255.0 * alpha_ratio())


func current_size() -> int:
	return maxi(1, int(float(size) * alpha_ratio()))
