class_name ZephyrParticle
extends RefCounted

## Native Particle motion from heroes/zephyr_fx.py. Scalar doubles avoid
## accumulating float32 Vector2 drift. All five shapes emit native commands;
## helper rasterization/additive blending and full director parity remain pending.
var x := 0.0
var y := 0.0
var vx := 0.0
var vy := 0.0
var ax := 0.0
var ay := 0.0
var life := 0.0
var max_life := 1.0
var size := 2.0
var rotation := 0.0
var rotation_speed := 0.0
var alpha := 255
var gravity := 0.0
var color: Array = []
var color_end: Variant = null
var shape := "pixel"
var drag := 0.0
var additive := false
var active := false
var fade_pow := 1.0


func spawn(
	px: float,
	py: float,
	speed_x: float,
	speed_y: float,
	seconds: float,
	particle_size: float,
	rgb: Array,
	options: Dictionary = {}
) -> ZephyrParticle:
	x = px
	y = py
	vx = speed_x
	vy = speed_y
	ax = float(options.get("ax", 0.0))
	ay = float(options.get("ay", 0.0))
	life = maxf(0.02, seconds)
	max_life = life
	size = particle_size
	color = rgb.duplicate()
	color_end = options.get("color_end")
	gravity = float(options.get("gravity", 0.0))
	drag = float(options.get("drag", 0.0))
	rotation = float(options.get("rotation", 0.0))
	rotation_speed = float(options.get("rotation_speed", 0.0))
	alpha = int(options.get("alpha", 255))
	shape = str(options.get("shape", "pixel"))
	additive = bool(options.get("additive", false))
	fade_pow = float(options.get("fade_pow", 1.0))
	active = true
	return self


func update(dt: float) -> bool:
	life -= dt
	if life <= 0.0:
		active = false
		return false
	vx += ax * dt
	vy += (ay + gravity) * dt
	if drag != 0.0:
		var damp := maxf(0.0, 1.0 - drag * dt)
		vx *= damp
		vy *= damp
	x += vx * dt
	y += vy * dt
	rotation += rotation_speed * dt
	return true


func snapshot() -> Dictionary:
	return {
		"pos": [x, y],
		"vel": [vx, vy],
		"acc": [ax, ay],
		"life": life,
		"max_life": max_life,
		"size": size,
		"rotation": rotation,
		"rotation_speed": rotation_speed,
		"alpha": alpha,
		"gravity": gravity,
		"color": color,
		"color_end": color_end,
		"shape": shape,
		"drag": drag,
		"additive": additive,
		"active": active,
		"fade_pow": fade_pow,
	}


func commands() -> Array:
	if not active:
		return []
	var fade := pow(life / max_life, fade_pow)
	var opacity := int(alpha * fade)
	if opacity <= 3:
		return []
	var rgb := color.duplicate()
	if color_end is Array:
		for index in 3:
			rgb[index] = int(
				float(color_end[index]) + (float(color[index]) - float(color_end[index])) * fade
			)
	var rgba := [rgb[0], rgb[1], rgb[2], opacity]
	var px := int(x)
	var py := int(y)
	var extent := maxi(1, int(size * (0.35 + 0.65 * fade)))
	if shape == "glow":
		# The source ignores alpha after the early-out: power depends on fade.
		var power := float("%.2f" % (0.9 * fade))
		return [
			[
				"glow",
				[rgb[0], rgb[1], rgb[2], 255],
				[px - extent * 2, py - extent * 2],
				extent * 2,
				power
			]
		]
	if shape == "spark":
		return [["spark", rgba, [px - extent - 1, py - extent - 1], extent + 1]]
	if shape == "streak":
		var speed := sqrt(vx * vx + vy * vy)
		if speed < 0.01:
			return []
		var length := maxi(2, int(extent * 2 + speed * 0.02))
		return [
			[
				"line",
				rgba,
				[px, py],
				[px - int(vx / speed * length), py - int(vy / speed * length)],
				maxi(1, int(extent / 2))
			]
		]
	if shape == "shard":
		var ca := cos(rotation)
		var sa := sin(rotation)
		var width := maxi(1, int(extent / 2))
		var points: Array = []
		# Python -h // 2 floors toward minus infinity, not toward zero.
		for point: Array in [
			[extent, 0], [-width, width], [int(floor(-extent / 2.0)), 0], [-width, -width]
		]:
			points.append(
				[px + int(point[0] * ca - point[1] * sa), py + int(point[0] * sa + point[1] * ca)]
			)
		return [["polygon", rgba, points]]
	# Python falls back to chunky pixels for any unrecognized shape.
	var result: Array = [
		["rect", rgba, [px - int(extent / 2) + 1, py - int(extent / 2) + 1, extent, extent]]
	]
	if extent >= 3:
		var white := white_color()
		result.append(
			[
				"rect",
				[white[0], white[1], white[2], mini(255, opacity + 40)],
				[
					px - int(extent / 2) + 1,
					py - int(extent / 2) + 1,
					maxi(1, int(extent / 2)),
					maxi(1, int(extent / 2))
				]
			]
		)
	return result


func white_color() -> Array:
	ZephyrBolt.ensure_loaded()
	return ZephyrBolt.palette.get("fx_white", [255, 242, 252])


func is_back() -> bool:
	return false
