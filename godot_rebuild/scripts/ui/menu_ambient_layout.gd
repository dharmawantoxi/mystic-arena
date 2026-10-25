extends RefCounted
## Source-replay helpers for `_core.py` Menu ambient fog and its 64 ember/arcane particles.

const SOURCE_WIDTH := 1280.0
const SOURCE_HEIGHT := 720.0
const EMBER_COLORS := [[255, 190, 80], [255, 220, 120], [255, 150, 50], [255, 235, 160]]
const ARCANE_COLORS := [[160, 130, 255], [120, 190, 255], [230, 180, 255], [140, 220, 255]]
const PARTICLE_COUNT := 64


static func create_particles(rng: RandomNumberGenerator) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for _index in range(PARTICLE_COUNT):
		var kind := "ember" if rng.randf() < 0.55 else "arcane"
		var colors: Array = EMBER_COLORS if kind == "ember" else ARCANE_COLORS
		var color: Array = colors[rng.randi_range(0, colors.size() - 1)]
		if kind == "ember":
			(
				result
				. append(
					{
						"kind": kind,
						"x": rng.randf_range(0.0, SOURCE_WIDTH),
						"y": rng.randf_range(SOURCE_HEIGHT * 0.4, SOURCE_HEIGHT),
						"vx": rng.randf_range(-0.35, 0.35),
						"vy": rng.randf_range(-0.9, -0.35),
						"size": rng.randi_range(1, 3),
						"color": color.duplicate(),
						"alpha": rng.randi_range(80, 180),
						"ph": rng.randf_range(0.0, 6.28),
					}
				)
			)
		else:
			(
				result
				. append(
					{
						"kind": kind,
						"x": rng.randf_range(0.0, SOURCE_WIDTH),
						"y": rng.randf_range(0.0, SOURCE_HEIGHT),
						"vx": rng.randf_range(-0.2, 0.2),
						"vy": rng.randf_range(-0.35, -0.05),
						"size": rng.randi_range(1, 2),
						"color": color.duplicate(),
						"alpha": rng.randi_range(60, 150),
						"ph": rng.randf_range(0.0, 6.28),
					}
				)
			)
	return result


## One source `_update_particles()` tick. `random_x` is called only for a y-wrap.
static func advance(particles: Array, frames: float, random_x: Callable) -> int:
	var wraps := 0
	for entry in particles:
		if not entry is Dictionary:
			continue
		var particle: Dictionary = entry
		var kind := String(particle.get("kind", "ember"))
		var x := float(particle.get("x", 0.0))
		var y := float(particle.get("y", 0.0))
		var phase := float(particle.get("ph", 0.0))
		if kind == "arcane":
			x += (float(particle.get("vx", 0.0)) + sin(phase) * 0.08) * frames
			phase += 0.01 * frames
			particle["ph"] = phase
		else:
			x += float(particle.get("vx", 0.0)) * frames
		y += float(particle.get("vy", 0.0)) * frames
		if y < -10.0:
			y = SOURCE_HEIGHT + 10.0
			x = float(random_x.call()) if random_x.is_valid() else 0.0
			wraps += 1
		if x < -10.0:
			x = SOURCE_WIDTH + 10.0
		elif x > SOURCE_WIDTH + 10.0:
			x = -10.0
		particle["x"] = x
		particle["y"] = y
	return wraps


static func fog_offset(tick: float, speed: float, width: int) -> int:
	if width <= 0:
		return 0
	return int(fposmod(tick * speed, float(width)))


static func fog_alpha(base: int, tick: float, layer_index: int) -> int:
	return clampi(base + int(5.0 * sin(tick * 0.008 + layer_index * 2.0)), 8, 80)


static func particle_alpha(particle: Dictionary, tick: float) -> int:
	var alpha := int(particle.get("alpha", 0))
	if String(particle.get("kind", "ember")) == "ember":
		alpha = int(alpha * (0.75 + 0.25 * sin(tick * 0.05 + float(particle.get("ph", 0.0)))))
	return alpha
