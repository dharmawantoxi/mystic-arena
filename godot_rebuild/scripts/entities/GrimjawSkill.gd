class_name GrimjawSkill
extends ZephyrSkill

## Reuses scalar state/tape storage, not Zephyr emission formulas or visuals.
## Full cast/director orchestration remains pending.
static var grimjaw_config: Dictionary = {}
var col_a: Array = []
var col_b: Array = []
var glow_allowed := true
var facing := 1


static func ensure_grimjaw_loaded() -> void:
	if grimjaw_config.is_empty():
		var file := FileAccess.open("res://data/grimjaw_skill.json", FileAccess.READ)
		if file != null:
			grimjaw_config = JSON.parse_string(file.get_as_text())
			for key: String in grimjaw_config.timeline_f64:
				var values: Array = []
				for bits: String in grimjaw_config.timeline_f64[key]:
					values.append(bits.hex_decode().decode_double(0))
				grimjaw_config.timeline[key] = values


func spawn(
	key: String, px: float, py: float, custom_radius := 0.0, seed_value := -1
) -> ZephyrSkill:
	ensure_grimjaw_loaded()
	kind = key if grimjaw_config.timeline.has(key) else "q"
	x = px
	y = py
	radius = custom_radius if custom_radius != 0.0 else float(grimjaw_config.radius[kind])
	var tl: Array = grimjaw_config.timeline[kind]
	t_charge = float(tl[0])
	t_release = t_charge + float(tl[1])
	t_area = t_release + float(tl[2])
	t_impact = t_area + float(tl[3])
	total = t_impact + float(tl[4])
	col_a = grimjaw_config.colors[kind][0]
	col_b = grimjaw_config.colors[kind][1]
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


func snapshot() -> Dictionary:
	var result := super.snapshot()
	result.col_a = col_a
	result.col_b = col_b
	return result


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
	var p: Dictionary = grimjaw_config.palette
	if phase == "charge":
		emit_time += dt
		if emit_time >= 0.034:
			emit_time = 0.0
			var angle := random_value() * TAU
			var rr := radius * uniform(0.7, 1.15)
			var size := uniform(1.5, 3.0)
			var rotation := random_value() * TAU
			var spin := uniform(-8, 8)
			_emit_spawn(
				[
					x + cos(angle) * rr,
					y + sin(angle) * rr * 0.45,
					-cos(angle) * rr * 1.7,
					-sin(angle) * rr * 0.8,
					0.42,
					size,
					col_b if kind != "w" else p.heal_light
				],
				{
					"color_end": col_a,
					"shape": "ember" if kind != "w" else "pixel",
					"fade_pow": 0.6,
					"rotation": rotation,
					"rotation_speed": spin
				}
			)
	elif phase == "release" and not released:
		released = true
		if kind == "w":
			_emit_burst(
				[x, y, 5],
				{
					"speed": [40, 120],
					"life": [0.4, 0.8],
					"size": [2, 4],
					"colors": [p.heal_mid, p.heal_light, p.heal_core],
					"drag": 2.2,
					"shape": "pixel",
					"gravity": -30.0
				}
			)
		else:
			_emit_burst(
				[x, y, 8],
				{
					"speed": [130, 330],
					"life": [0.24, 0.55],
					"size": [2, 4],
					"colors": [p.fx_white, col_b, p.fx_light],
					"drag": 3.2,
					"shape": "streak",
					"direction": 0.0,
					"spread": TAU
				}
			)
			_emit_burst(
				[x, y + 6, 4],
				{
					"speed": [50, 150],
					"life": [0.4, 0.8],
					"size": [2, 5],
					"colors": [p.ash, p.smoke],
					"gravity": -40.0,
					"drag": 1.6,
					"shape": "smoke",
					"back": true
				}
			)
	elif phase == "area":
		emit_time += dt
		var interval := 0.07 if kind == "w" else 0.06 if kind == "r" else 0.05
		if emit_time >= interval:
			emit_time = 0.0
			_area_emit(p)
	elif phase == "impact" and not impacted:
		impacted = true
		if kind != "w":
			_emit_burst(
				[x, y, 7],
				{
					"speed": [90, 260],
					"life": [0.3, 0.62],
					"size": [2, 5],
					"colors": [col_b, p.fx_light, p.ash],
					"gravity": 420.0,
					"drag": 1.0,
					"shape": "shard",
					"rotation_speed": [-14.0, 14.0]
				}
			)
	return true


func _area_emit(p: Dictionary) -> void:
	if kind == "e":
		var f := uniform(-1, 1)
		var sy := y - uniform(2, 20)
		var vx := f * uniform(60, 190)
		var vy := -uniform(10, 60)
		var life := uniform(0.3, 0.6)
		var size := uniform(1.5, 3.0)
		var rotation := random_value() * TAU
		var spin := uniform(-9, 9)
		_emit_spawn(
			[x + f * 10, sy, vx, vy, life, size, p.gold_hot],
			{
				"color_end": p.blood,
				"drag": 2.0,
				"shape": "ember",
				"rotation": rotation,
				"rotation_speed": spin
			}
		)
		return
	var angle := random_value() * TAU
	var rr := (
		radius
		* uniform(
			0.3 if kind == "q" else 0.2 if kind == "w" else 0.4,
			1.0 if kind == "q" else 0.95 if kind == "w" else 0.9
		)
	)
	if kind == "q":
		var vy := -uniform(40, 110)
		var life := uniform(0.5, 1.0)
		var size := uniform(1.5, 3.0)
		var rotation := random_value() * TAU
		var spin := uniform(-10, 10)
		_emit_spawn(
			[
				x + cos(angle) * rr,
				y + sin(angle) * rr * 0.42,
				-sin(angle) * 60,
				vy,
				life,
				size,
				p.ember
			],
			{
				"color_end": p.fx_dark,
				"drag": 0.6,
				"shape": "ember",
				"rotation": rotation,
				"rotation_speed": spin
			}
		)
	elif kind == "w":
		var vx := uniform(-8, 8)
		var vy := -uniform(24, 52)
		var life := uniform(0.6, 1.2)
		var size := uniform(1.5, 3.0)
		_emit_spawn(
			[x + cos(angle) * rr, y + sin(angle) * rr * 0.4, vx, vy, life, size, p.heal_light],
			{"color_end": p.heal_dark, "drag": 0.4, "shape": "pixel"}
		)
	else:
		var vx := cos(angle + 1.57) * uniform(90, 190)
		var vy := sin(angle + 1.57) * uniform(60, 120) - 40
		var life := uniform(0.4, 0.8)
		var size := uniform(2, 4)
		var spin := -14.0 if random_value() < 0.5 else 14.0
		_emit_spawn(
			[x + cos(angle) * rr, y + sin(angle) * rr * 0.5 - 10, vx, vy, life, size, p.rage_light],
			{
				"color_end": p.rage_dark,
				"drag": 1.6,
				"shape": "shard",
				"rotation": angle,
				"rotation_speed": spin
			}
		)


func _emit_spawn(args: Array, options: Dictionary) -> void:
	events.append({"type": "spawn", "args": args, "options": options})


func _emit_burst(args: Array, options: Dictionary) -> void:
	events.append({"type": "burst", "args": args, "options": options})


func front_commands(detail := 1.0) -> Array:
	if not active:
		return []
	var p: Dictionary = grimjaw_config.palette
	var result: Array = []
	var px := int(x)
	var py := int(y)
	if phase == "release":
		var t := (age - t_charge) / maxf(0.001, t_release - t_charge)
		var r := int(radius * (0.4 + 1.1 * t))
		if glow_allowed:
			result.append_array(
				GrimjawHurt.glow_commands(
					int(floor(r / 3.0)) * 3,
					p.fx_white,
					float("%.2f" % (0.8 * (1.0 - t))),
					[px - r, py - r]
				)
			)
		result.append_array(
			_doodle_ring(r, maxi(1, int(5 * (1.0 - t))), col_b, int(230 * (1.0 - t)))
		)
	elif phase == "area":
		var t := (age - t_release) / maxf(0.001, t_area - t_release)
		if kind == "e":
			var direction := 1.0 if facing >= 0 else -1.0
			var count := clampi(python_round(4 * detail), 2, 4)
			for i in count:
				var progress := fposmod(t * 1.6 + i * 0.25, 1.0)
				var dx := int(direction * (14 + progress * radius))
				var dy := -8 - int((1.0 - progress) * 10)
				var opacity := int(210 * (1.0 - progress) * (0.4 + 0.6 * t))
				if opacity <= 6:
					continue
				var cx := px + dx
				var cy := py + dy
				var width := 6 + i
				result.append(
					[
						"polygon_outline",
						[col_b[0], col_b[1], col_b[2], opacity],
						[
							[cx + direction * 7, cy],
							[cx - direction * 3, cy - width],
							[cx - direction, cy],
							[cx - direction * 3, cy + width]
						],
						2
					]
				)
		else:
			for k in 2:
				var rr := int(radius * (0.55 + 0.22 * k))
				var rgb := col_a if k == 0 else col_b
				var opacity := int(150 - 60 * t)
				if opacity <= 5:
					continue
				var marks := maxi(3, python_round((8 + k * 4) * (0.4 + 0.6 * detail)))
				var rotation := age * (2.3 if k == 0 else -1.6)
				for i in marks:
					var angle := rotation + i * TAU / marks
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
		result.append_array(
			_doodle_ring(r, maxi(1, int(6 * (1.0 - t))), p.fx_white, int(220 * (1.0 - t)))
		)
	return result


func _doodle_ring(r: int, thickness: int, rgb: Array, opacity: int) -> Array:
	r = maxi(3, r)
	thickness = maxi(1, thickness)
	var center := r + thickness + 3
	var count := clampi(int(r / 3), 10, 22)
	var points: Array = []
	var second: Array = []
	for i in count:
		var angle := i * TAU / count
		var wobble := 1.0 + (hash01(r * 13 + i * 7) - 0.5) * minf(0.09, 3.0 / maxi(4, r))
		var mx := int(center + cos(angle) * r * wobble + 0.5) + int(x) - center
		var my := int(center + sin(angle) * r * wobble + 0.5) + int(y) - center
		points.append([mx, my])
		second.append([mx + (1 if i % 2 else -1), my])
	points.append(points[0].duplicate())
	var result: Array = [
		["polyline", [rgb[0], rgb[1], rgb[2], opacity], points, maxi(1, int(thickness * 0.8))]
	]
	if r >= 8:
		second.append(second[0].duplicate())
		result.append(["polyline", [rgb[0], rgb[1], rgb[2], 127.0 * opacity / 255.0], second, 1])
	return result


func ground_commands(detail := 1.0) -> Array:
	if not active:
		return []
	var tint := [col_a, col_b]
	var result: Array = []
	var t_all := minf(1.0, age / total)
	var haze := int(floor(int(radius * (0.9 + 0.25 * sin(age * 4.0))) / 8.0)) * 8
	var power := python_round(0.30 * (1.0 - absf(t_all - 0.35) * 1.4) / 0.05) * 0.05
	if power > 0.02 and haze >= 8 and glow_allowed:
		for bi in 3:
			var f: float = [0.30, 0.58, 1.0][bi]
			var k := power * f
			if k <= 0.004:
				continue
			var rx := maxi(2, int(haze * f))
			var ry := maxi(1, int(haze * f * 0.5))
			var dy := python_round((hash01(haze * 23 + bi * 5) - 0.5) * 2)
			result.append(
				[
					"oval",
					[
						int(col_a[0] * k),
						int(col_a[1] * k),
						int(col_a[2] * k),
						mini(255, int(255 * k))
					],
					[int(x) - rx, int(y) - ry + dy, rx * 2, ry * 2],
					0
				]
			)
		for k in 3:
			var sx := int((haze * 2 + 4) * (0.30 + 0.20 * k)) + int(x) - haze - 2
			var length := int(haze * (0.22 + 0.10 * hash01(haze * 7 + k)))
			var yy := int(y) + int((hash01(haze * 11 + k * 3) - 0.5) * haze * 0.6)
			result.append(
				[
					"line",
					[
						int(col_a[0] * power),
						int(col_a[1] * power),
						int(col_a[2] * power),
						mini(255, int(190 * power))
					],
					[sx, yy],
					[sx + length, yy + 1],
					1
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
		if kind != "w":
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
		var white: Array = grimjaw_config.palette.fx_white
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
			if i % 2 and detail >= 0.55:
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
