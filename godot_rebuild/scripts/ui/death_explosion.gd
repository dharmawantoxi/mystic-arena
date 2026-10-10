extends RefCounted
## Death burst state, ported from `_render.py::DeathExplosion`.
##
## The source's `draw()` is intentionally not ported: callers can query the
## flash and particle state through getters and draw their own Godot vectors.
## The optional `particle_specs` argument is the fixture replay seam; when it
## is omitted, the source's random ranges are used directly.

const HitParticle = preload("res://scripts/ui/hit_particle.gd")

const FLASH_MAX := 8
const RED_COLORS := [[255, 100, 100], [255, 150, 100], [255, 200, 100]]
const BLUE_COLORS := [[100, 200, 255], [150, 220, 255], [200, 240, 255]]

var x := 0.0
var y := 0.0
var team := "red"
var burst_size := "medium"
var particles: Array = []
var particle_colors: Array = []
var flash_timer := 0
var flash_max := FLASH_MAX


## `particle_specs` replays the source oracle's already-created sparks. The
## empty case follows the source constructor's random particle creation.
func configure(
	pos_x: float,
	pos_y: float,
	particle_team: String = "red",
	particle_size: String = "medium",
	particle_specs: Array = []
) -> void:
	x = pos_x
	y = pos_y
	team = particle_team
	burst_size = particle_size
	particles.clear()
	particle_colors.clear()
	if particle_specs.is_empty():
		_spawn_random_particles()
	else:
		for spec_value in particle_specs:
			var spec: Dictionary = spec_value
			var color: Array = _to_rgb(spec.get("color", [255, 100, 100]))
			particles.append(
				_make_particle(
					color,
					Vector2(float(spec["vx"]), float(spec["vy"])),
					int(spec["lifetime"]),
					int(spec["size"])
				)
			)
			particle_colors.append(color)
	flash_timer = FLASH_MAX
	flash_max = FLASH_MAX


func update() -> void:
	for particle in particles:
		particle.update()
	var live_particles: Array = []
	var live_colors: Array = []
	for index in range(particles.size()):
		var particle: Variant = particles[index]
		if particle.alive:
			live_particles.append(particle)
			live_colors.append(particle_colors[index])
	particles = live_particles
	particle_colors = live_colors
	if flash_timer > 0:
		flash_timer -= 1


func is_alive() -> bool:
	return particles.size() > 0 or flash_timer > 0


func get_particle_count() -> int:
	return particles.size()


## State needed by presentation code without exposing the source draw body.
func get_particle_snapshot(index: int) -> Dictionary:
	var particle: Variant = particles[index]
	var tint: Array = particle_colors[index]
	return {
		"x": particle.x,
		"y": particle.y,
		"vx": particle.vx,
		"vy": particle.vy,
		"lifetime": particle.lifetime,
		"max_lifetime": particle.max_lifetime,
		"size": particle.size,
		"alive": particle.alive,
		"color": tint.duplicate(),
	}


## The central flash values are the locals used by the source draw method.
func get_flash_state() -> Dictionary:
	var intensity: float = 0.0
	if flash_timer > 0:
		intensity = float(flash_timer) / float(flash_max)
	return {
		"timer": flash_timer,
		"max": flash_max,
		"intensity": intensity,
		"size": int(20.0 * intensity) if flash_timer > 0 else 0,
	}


func _spawn_random_particles() -> void:
	var colors: Array = BLUE_COLORS if team == "blue" else RED_COLORS
	var particle_count: int = _particle_count(burst_size)
	var spark_range: Array = _spark_range(burst_size)
	for _index in range(particle_count):
		var angle: float = randf_range(0.0, TAU)
		var speed: float = randf_range(1.5, 4.0)
		var velocity: Vector2 = Vector2(cos(angle), sin(angle)) * speed
		var color: Array = colors[randi_range(0, colors.size() - 1)]
		var spark_size: int = randi_range(int(spark_range[0]), int(spark_range[1]))
		var lifetime: int = randi_range(20, 35)
		particles.append(_make_particle(color, velocity, lifetime, spark_size))
		particle_colors.append(color)


func _make_particle(color: Array, velocity: Vector2, lifetime: int, size: int) -> RefCounted:
	var particle = HitParticle.new()
	particle.configure(
		x, y, Color8(int(color[0]), int(color[1]), int(color[2])), velocity, lifetime, size
	)
	return particle


func _particle_count(size: String) -> int:
	if size == "small":
		return 8
	if size == "medium":
		return 15
	return 25


func _spark_range(size: String) -> Array:
	if size == "small":
		return [2, 4]
	if size == "medium":
		return [3, 5]
	return [4, 6]


func _to_rgb(value: Variant) -> Array:
	if value is Array and value.size() >= 3:
		return [int(value[0]), int(value[1]), int(value[2])]
	return RED_COLORS[0].duplicate()
