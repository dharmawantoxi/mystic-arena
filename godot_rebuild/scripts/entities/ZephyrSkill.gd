class_name ZephyrSkill
extends RefCounted

## Native SkillFX lifecycle/emissions and ground/front command geometry.
static var config: Dictionary = {}
var kind := "q"
var x := 0.0
var y := 0.0
var radius := 60.0
var age := 0.0
var t_charge := 0.0
var t_release := 0.0
var t_area := 0.0
var t_impact := 0.0
var total := 0.0
var active := true
var phase := "cast"
var released := false
var impacted := false
var emit_time := 0.0
var visual_seed := 0
var events: Array = []
var random_tape: Array = []
var tape_index := 0
var rng := RandomNumberGenerator.new()


static func ensure_loaded() -> void:
	if config.is_empty():
		var file := FileAccess.open("res://data/zephyr_skill.json", FileAccess.READ)
		if file != null:
			config = JSON.parse_string(file.get_as_text())
			for key: String in config.timeline_f64:
				var values: Array = []
				for bits: String in config.timeline_f64[key]:
					values.append(bits.hex_decode().decode_double(0))
				config.timeline[key] = values


func spawn(
	key: String, px: float, py: float, custom_radius := 0.0, seed_value := -1
) -> ZephyrSkill:
	ensure_loaded()
	kind = key if config.timeline.has(key) else "q"
	x = px
	y = py
	radius = custom_radius if custom_radius != 0.0 else float(config.radius[kind])
	var timeline: Array = config.timeline[kind]
	t_charge = float(timeline[0])
	t_release = t_charge + float(timeline[1])
	t_area = t_release + float(timeline[2])
	t_impact = t_area + float(timeline[3])
	total = t_impact + float(timeline[4])
	age = 0.0
	active = true
	phase = "cast"
	released = false
	impacted = false
	emit_time = 0.0
	events.clear()
	tape_index = 0
	rng.randomize()
	visual_seed = seed_value if seed_value >= 0 else rng.randi_range(0, 9999)
	return self


func random_value() -> float:
	if not random_tape.is_empty():
		var result := float(random_tape[tape_index % random_tape.size()])
		tape_index += 1
		return result
	return rng.randf()


func uniform(low: float, high: float) -> float:
	return low + (high - low) * random_value()


func snapshot() -> Dictionary:
	return {
		"kind": kind,
		"x": x,
		"y": y,
		"radius": radius,
		"age": age,
		"t_charge": t_charge,
		"t_release": t_release,
		"t_area": t_area,
		"t_impact": t_impact,
		"total": total,
		"active": active,
		"phase": phase,
		"_released": released,
		"_impacted": impacted,
		"_emit": emit_time,
		"seed": visual_seed
	}


func update(dt: float, connected := true) -> bool:
	events.clear()
	age += dt
	if age < t_charge:
		phase = "charge"
	elif age < t_release:
		phase = "release"
	elif age < t_area:
		phase = "area"
	elif age < t_impact:
		phase = "impact"
	else:
		phase = "fade"
	if age >= total:
		active = false
		return false
	if not connected:
		return true
	ZephyrBolt.ensure_loaded()
	var p := ZephyrBolt.palette
	if phase == "charge":
		emit_time += dt
		if emit_time >= 0.035:
			emit_time = 0.0
			var angle := random_value() * TAU
			var rr := radius * uniform(0.7, 1.15)
			var size := uniform(1.5, 3.0)
			events.append(
				{
					"type": "spawn",
					"args":
					[
						x + cos(angle) * rr,
						y + sin(angle) * rr * 0.45,
						-cos(angle) * rr * 1.6,
						-sin(angle) * rr * 0.75,
						0.42,
						size,
						p.fx_bright
					],
					"options": {"color_end": p.fx_dark, "shape": "pixel", "fade_pow": 0.6}
				}
			)
	elif phase == "release" and not released:
		released = true
		events.append(
			{
				"type": "burst",
				"args": [x, y, 8],
				"options":
				{
					"speed": [120, 320],
					"life": [0.24, 0.55],
					"size": [2, 4],
					"colors": [p.fx_white, p.fx_hot, p.fx_light],
					"drag": 3.2,
					"shape": "streak"
				}
			}
		)
		events.append(
			{
				"type": "burst",
				"args": [x, y + 6, 4],
				"options":
				{
					"speed": [50, 150],
					"life": [0.4, 0.8],
					"size": [2, 5],
					"colors": [p.ash, p.smoke],
					"gravity": -40.0,
					"drag": 1.6,
					"shape": "pixel"
				}
			}
		)
	elif phase == "area":
		emit_time += dt
		if emit_time >= 0.06:
			emit_time = 0.0
			var angle := random_value() * TAU
			var rr := radius * uniform(0.2, 1.0)
			var vx := uniform(-14, 14)
			var vy := uniform(-46, -18)
			var life := uniform(0.5, 1.0)
			var size := uniform(1.5, 3.0)
			events.append(
				{
					"type": "spawn",
					"args":
					[x + cos(angle) * rr, y + sin(angle) * rr * 0.42, vx, vy, life, size, p.ember],
					"options": {"color_end": p.fx_dark, "drag": 0.6, "shape": "pixel"}
				}
			)
	elif phase == "impact" and not impacted:
		impacted = true
		events.append(
			{
				"type": "burst",
				"args": [x, y, 7],
				"options":
				{
					"speed": [90, 260],
					"life": [0.3, 0.62],
					"size": [2, 5],
					"colors": [p.thorn_lit, p.fx_light, p.ash],
					"gravity": 420.0,
					"drag": 1.0,
					"shape": "shard",
					"rotation_speed": [-14.0, 14.0]
				}
			}
		)
	return true


static func python_round(value: float) -> int:
	# Python rounds exact ties to even, unlike Godot roundi.
	var low := floori(value)
	var fraction := value - low
	if fraction == 0.5:
		return low if low % 2 == 0 else low + 1
	return low if fraction < 0.5 else low + 1


func front_commands(detail := 1.0) -> Array:
	if not active:
		return []
	ZephyrBolt.ensure_loaded()
	var p := ZephyrBolt.palette
	var tint: Array = config.tint[kind]
	var px := int(x)
	var py := int(y)
	var result: Array = []
	if phase == "release":
		var t := (age - t_charge) / maxf(0.001, t_release - t_charge)
		var r := int(radius * (0.4 + 1.1 * t))
		result.append(
			[
				"glow",
				[p.fx_white[0], p.fx_white[1], p.fx_white[2], 255],
				[px - r, py - r],
				int(floor(r / 3.0)) * 3,
				float("%.2f" % (0.8 * (1.0 - t)))
			]
		)
		result.append(_ring_command(r, maxi(1, int(5 * (1.0 - t))), tint[1], int(230 * (1.0 - t))))
	elif phase == "area":
		var t := (age - t_release) / maxf(0.001, t_area - t_release)
		for k in 2:
			var speed := 2.3 if k == 0 else -1.6
			var rr := int(radius * (0.55 + 0.22 * k))
			var rgb: Array = tint[k]
			var opacity := int(150 - 60 * t)
			if opacity <= 5:
				continue
			var marks := maxi(3, python_round((8 + k * 4) * (0.4 + 0.6 * detail)))
			for i in marks:
				var angle := age * speed + i * TAU / marks
				var mx := int(px + cos(angle) * rr)
				var my := int(py - 6 + sin(angle) * rr * 0.55)
				var size := 3 if i % 2 else 2
				result.append(
					[
						"polygon",
						[rgb[0], rgb[1], rgb[2], opacity],
						[
							[mx, my - size - 2],
							[mx + size + 1, my],
							[mx, my + size + 1],
							[mx - size - 1, my]
						]
					]
				)
	elif phase == "impact":
		var t := (age - t_area) / maxf(0.001, t_impact - t_area)
		var r := int(radius * (0.6 + 0.9 * t))
		result.append(
			_ring_command(r, maxi(1, int(6 * (1.0 - t))), p.fx_white, int(220 * (1.0 - t)))
		)
	return result


func _ring_command(r: int, thickness: int, rgb: Array, opacity: int) -> Array:
	# ring_surface's centered bitmap cancels its padding on blit.
	return [
		"circle",
		[rgb[0], rgb[1], rgb[2], opacity],
		[int(x), int(y)],
		maxi(3, r),
		maxi(1, thickness)
	]


static func hash01(value: int) -> float:
	var h := (value * 2654435761) & 0xFFFFFFFF
	h = h ^ (h >> 16)
	return float(h & 0xFFFF) / 65535.0


func ground_commands(detail := 1.0) -> Array:
	# Source constructor-only cast can produce alpha > 255; wait for first update.
	if not active or phase == "cast":
		return []
	ZephyrBolt.ensure_loaded()
	var tint: Array = config.tint[kind]
	var result: Array = []
	var t_all := minf(1.0, age / total)
	var haze := int(floor(int(radius * (0.9 + 0.25 * sin(age * 4.0))) / 8.0)) * 8
	var power := python_round(0.30 * (1.0 - absf(t_all - 0.35) * 1.4) / 0.05) * 0.05
	if power > 0.02 and haze >= 8:
		var steps := clampi(int(haze / 2), 4, 12)
		for i in range(steps, 0, -1):
			var t := float(i) / steps
			var rx := maxi(2, int(haze * t))
			var ry := maxi(1, int(haze * t * 0.5))
			var k := power * pow(1.0 - t, 1.5)
			if k <= 0.004:
				continue
			var rgb: Array = tint[0]
			result.append(
				[
					"oval",
					[int(rgb[0] * k), int(rgb[1] * k), int(rgb[2] * k), mini(255, int(255 * k))],
					[int(x) - rx, int(y) - ry, rx * 2, ry * 2],
					0
				]
			)
	if phase == "charge":
		var t := age / t_charge
		_ground_ring(
			result,
			int(radius * (1.25 - 0.25 * t)),
			tint[0],
			int(120 + 90 * t),
			true,
			t * 6.0,
			detail
		)
	elif phase == "release" or phase == "area":
		var t := minf(1.0, (age - t_charge) / maxf(0.001, t_area - t_charge))
		_ground_ring(result, int(radius), tint[0], int(200 - 90 * t), false, 0.0, detail)
		_ground_ring(result, int(radius * 0.66), tint[1], int(160 - 70 * t), true, -t * 5.0, detail)
		_ground_cracks(result, tint[1], int(170 * (1.0 - t)), detail)
	else:
		var t := minf(1.0, (age - t_area) / maxf(0.001, total - t_area))
		_ground_ring(
			result,
			int(radius * (1.0 + 0.35 * t)),
			tint[1],
			int(150 * (1.0 - t)),
			false,
			0.0,
			detail
		)
	return result


func _ground_ring(
	result: Array, r: int, rgb: Array, opacity: int, dashed: bool, rotation: float, detail: float
) -> void:
	if opacity <= 5 or r <= 3:
		return
	var rgba := [rgb[0], rgb[1], rgb[2], opacity]
	var cx := r + 4
	var cy := int((int(r * 0.9) + 8) / 2)
	if not dashed:
		var box := [int(x) - r, int(y) - int(r * 0.42), r * 2, int(r * 0.84)]
		result.append(["oval", rgba, box, 3])
		var white: Array = ZephyrBolt.palette.fx_white
		result.append(
			[
				"oval",
				[white[0], white[1], white[2], int(opacity / 3)],
				[box[0] + 3, box[1] + 1, box[2] - 6, box[3] - 3],
				1
			]
		)
	else:
		var segments := clampi(int(16 * detail), 8, 16)
		for i in segments:
			if i % 2 and segments >= 10 and detail >= 0.55:
				continue
			var angle := i * TAU / segments + rotation
			var first := [
				int(cx + cos(angle) * r) + int(x) - cx,
				int(cy + sin(angle) * r * 0.42) + int(y) - cy
			]
			var second := [
				int(cx + cos(angle + 0.26) * r) + int(x) - cx,
				int(cy + sin(angle + 0.26) * r * 0.42) + int(y) - cy
			]
			result.append(["line", rgba, first, second, 3])


func _ground_cracks(result: Array, rgb: Array, opacity: int, detail: float) -> void:
	# Source deliberately draws opaque RGB lines; alpha only gates the draw.
	if opacity <= 6:
		return
	var cracks := clampi(python_round(5 * detail), 2, 5)
	var segments := clampi(python_round(4 * detail), 2, 4)
	for i in cracks:
		var angle := hash01(visual_seed + i * 31) * TAU
		var length := radius * (0.55 + hash01(visual_seed + i * 77) * 0.5)
		var px := x
		var py := y
		for segment in segments:
			angle += (hash01(visual_seed + i * 13 + segment) - 0.5) * 0.9
			var nx := px + cos(angle) * (length / segments)
			var ny := py + sin(angle) * (length / segments) * 0.42
			result.append(
				[
					"line",
					[rgb[0], rgb[1], rgb[2], 255],
					[int(px), int(py)],
					[int(nx), int(ny)],
					maxi(1, 3 - segment)
				]
			)
			px = nx
			py = ny
