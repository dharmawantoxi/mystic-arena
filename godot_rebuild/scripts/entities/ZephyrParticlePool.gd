class_name ZephyrParticlePool
extends RefCounted

## Reusable bounded pool. Godot RNG is visual-only (never consumes match RNG).
## random_tape is an optional oracle input, not the production RNG algorithm.
var cap := 96
var budget := 1.0
var live: Array[ZephyrParticle] = []
var pool: Array[ZephyrParticle] = []
var rng := RandomNumberGenerator.new()
var random_tape: Array = []
var tape_index := 0


func _init() -> void:
	rng.randomize()


func random_value() -> float:
	if not random_tape.is_empty():
		var value := float(random_tape[tape_index % random_tape.size()])
		tape_index += 1
		return value
	return rng.randf()


func uniform(low: float, high: float) -> float:
	return low + (high - low) * random_value()


func spawn(
	x: float,
	y: float,
	vx: float,
	vy: float,
	life: float,
	size: float,
	color: Array,
	options: Dictionary = {},
	in_burst := false
) -> ZephyrParticle:
	if budget <= 0.0 or (budget < 1.0 and not in_burst and random_value() >= budget):
		return null
	if live.size() >= cap:
		return null
	var particle: ZephyrParticle = pool.pop_back() if not pool.is_empty() else _new_particle()
	particle.spawn(x, y, vx, vy, life, size, color, options)
	live.append(particle)
	return particle


func burst(x: float, y: float, requested: int, options: Dictionary = {}) -> int:
	if budget <= 0.0 or live.size() >= cap:
		return 0
	var count := maxi(0, requested)
	if budget < 1.0:
		if count > 1:
			count = maxi(1, int(count * budget))
		elif random_value() >= budget:
			return 0
	count = mini(count, cap - live.size())
	var speed: Array = options.get("speed", [60.0, 200.0])
	var life: Array = options.get("life", [0.25, 0.6])
	var size: Array = options.get("size", [2, 4])
	var rotation_speed: Array = options.get("rotation_speed", [0.0, 0.0])
	ZephyrBolt.ensure_loaded()
	var colors: Array = options.get(
		"colors",
		[
			ZephyrBolt.palette["fx_bright"],
			ZephyrBolt.palette["fx_light"],
			ZephyrBolt.palette["fx_hot"]
		]
	)
	if colors.is_empty():
		colors = [
			ZephyrBolt.palette["fx_bright"],
			ZephyrBolt.palette["fx_light"],
			ZephyrBolt.palette["fx_hot"]
		]
	for index in count:
		var angle := (
			float(options.get("direction", 0.0))
			+ (random_value() - 0.5) * float(options.get("spread", TAU))
		)
		var velocity := uniform(float(speed[0]), float(speed[1]))
		var seconds := uniform(float(life[0]), float(life[1]))
		var extent := uniform(float(size[0]), float(size[1]))
		var settings := {
			"back": options.get("back", false),
			"gravity": options.get("gravity", 0.0),
			"drag": options.get("drag", 2.0),
			"shape": options.get("shape", "pixel"),
			"additive": options.get("additive", false),
			"fade_pow": options.get("fade_pow", 1.0),
			"rotation": random_value() * TAU,
			"rotation_speed": uniform(float(rotation_speed[0]), float(rotation_speed[1])),
		}
		spawn(
			x,
			y,
			cos(angle) * velocity,
			sin(angle) * velocity,
			seconds,
			extent,
			colors[index % colors.size()],
			settings,
			true
		)
	return count


func update(dt: float) -> void:
	var keep: Array[ZephyrParticle] = []
	for particle: ZephyrParticle in live:
		if particle.update(dt):
			keep.append(particle)
		elif pool.size() < cap:
			pool.append(particle)
	live = keep


func clear() -> void:
	for particle: ZephyrParticle in live:
		particle.active = false
		pool.append(particle)
	live.clear()


func draw(canvas: CanvasItem, layer := "") -> void:
	for particle: ZephyrParticle in live:
		if layer == "back" and not particle.is_back():
			continue
		if layer == "front" and particle.is_back():
			continue
		ZephyrBolt.draw_shapes(canvas, particle.commands())


func _new_particle() -> ZephyrParticle:
	return ZephyrParticle.new()
