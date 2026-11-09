class_name GrimjawSkill
extends ZephyrSkill

## Reuses scalar state/tape storage, not Zephyr emission formulas or visuals.
## Ground visuals and full cast/director effects remain pending.
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


func ground_commands(_detail := 1.0) -> Array:
	return []
