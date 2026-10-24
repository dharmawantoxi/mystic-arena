extends RefCounted
## Source-ordered screen-space ops for DynamicRenderer (layer 9d0).
## The shared Python recorder flattens cached surfaces to these same primitives;
## `dynamic_map_painter.gd` turns them into native CanvasItem drawing.


static func ops(renderer, t: int) -> Array:
	var result: Array = []
	var low := String(renderer.quality.get("level", "high")) == "low"
	if bool(renderer.quality.get("fog", true)):
		result.append_array(_fog_ops(renderer))
	if not low:
		result.append_array(_river_ops(renderer, t))
		result.append_array(_shop_glow_ops(renderer, t))
	if bool(renderer.quality.get("floating_decor", true)):
		result.append_array(_shop_smoke_ops(renderer, t))
	if bool(renderer.quality.get("particles", true)):
		result.append_array(_particle_ops(renderer))
	if not low:
		result.append_array(torch_ops(renderer, t))
	result.append_array(_boss_ops(renderer, t))
	return result


static func _fog_ops(renderer) -> Array:
	var result: Array = []
	for value in renderer.fog_particles:
		var fog: Dictionary = value
		var color := _rgba(fog.get("color", [80, 60, 60, 30]))
		if (fog.get("color", []) as Array).size() == 3:
			color[3] = int(fog.get("alpha", 30))
		var size := int(fog["size"])
		var rect := [
			int(fog["x"]) - size, int(fog["y"]) - floori(float(size) / 2.0), size * 2, size
		]
		_ellipse(result, rect, color)
	return result


static func _river_ops(renderer, t: int) -> Array:
	var result: Array = []
	var glow: Array = renderer.theme.get("river_glow", [80, 150, 200])
	var foam: Array = renderer.theme.get("river_foam", [180, 210, 230])
	for index in range(renderer.river_points.size()):
		if index % 10 != 0:
			continue
		var pulse := (sin(float(t) * 0.05 + float(index)) + 1.0) / 2.0
		if pulse <= 0.5:
			continue
		var pq := roundf(pulse * 10.0) / 10.0
		var radius := maxi(1, int(pq * 4.0))
		var point: Array = renderer.river_points[index]
		_circle(result, point, radius * 2, _with_alpha(glow, int(150.0 * pq)))
		_circle(result, point, radius, _with_alpha(foam, int(200.0 * pq)))
	return result


static func _shop_glow_ops(renderer, t: int) -> Array:
	var result: Array = []
	for entry in [
		[renderer.radiant_shop_pos, "radiant"],
		[renderer.dire_shop_pos, "dire"],
	]:
		var point: Array = entry[0]
		var pulse := (sin(float(t) * 0.05) + 1.0) / 2.0
		var glow_radius := 45 + int(pulse * 8.0)
		var color := [100, 200, 255] if String(entry[1]) == "radiant" else [255, 80, 80]
		var center := [int(point[0]), int(point[1]) - 5]
		for radius in range(glow_radius, 15, -4):
			var alpha := int((glow_radius - radius) * 2)
			if alpha > 0:
				_circle(result, center, radius, _with_alpha(color, alpha))
	return result


static func _shop_smoke_ops(renderer, t: int) -> Array:
	var result: Array = []
	for point_value in [renderer.radiant_shop_pos, renderer.dire_shop_pos]:
		var point: Array = point_value
		var chimney_x := int(point[0]) + 19
		var chimney_y := int(point[1]) - 32
		for index in range(3):
			var phase := fmod(float(t) * 0.03 + float(index * 2), 6.0)
			var sy := chimney_y - int(phase * 8.0)
			var sx := chimney_x + int(sin(phase * 2.0 + float(index)) * 3.0)
			var size := 3 - int(phase / 2.0)
			if size > 0:
				var alpha := int(180.0 - phase * 25.0)
				if alpha > 0:
					var bucket := int(float(alpha) / 8.0) * 8
					_circle(result, [sx, sy], size * 2, [100, 100, 110, bucket])
					_circle(result, [sx, sy], size, [150, 150, 160, bucket])
	return result


static func _particle_ops(renderer) -> Array:
	var result: Array = []
	var particle_type := String(renderer.theme.get("particle_type", "firefly"))
	for value in renderer.particles:
		var particle: Dictionary = value
		var x := int(particle["x"])
		var y := int(particle["y"])
		var size := int(particle["size"])
		var color: Array = particle["color"]
		var phase := float(particle["phase"])
		if particle_type == "firefly":
			var brightness := (sin(phase) + 1.0) / 2.0
			if brightness < 0.3:
				continue
			if brightness > 0.7:
				var glow_radius := size + 2
				_circle(result, [x, y], glow_radius * 2, _with_alpha(color, 60))
				_circle(result, [x, y], glow_radius, _with_alpha(color, 120))
			_rect(result, [x, y, size, size], color)
			_rect(result, [x, y, 1, 1], [255, 255, 255])
		elif particle_type == "snow":
			_rect(result, [x, y, size + 1, size + 1], color)
			_rect(result, [x, y, 1, 1], [255, 255, 255])
			if size >= 2:
				_circle(result, [x + 1, y + 1], 2, _with_alpha(color, 80))
		elif particle_type == "sand":
			_rect(result, [x, y, size + 1, 1], color)
			_rect(result, [x - 1, y, 1, 1], color)
		elif particle_type == "ember":
			_rect(result, [x, y, size, size], color)
			_circle(result, [x + 1, y + 1], 3, _with_alpha(color, 100))
		elif particle_type == "acid":
			_circle(result, [x, y], maxi(1, size + 1), _rgba(color).slice(0, 3))
			_rect(result, [x, y - 1, 1, 1], [225, 255, 150])
		elif particle_type == "ash":
			_rect(result, [x, y, size + 1, size + 1], color)
			if sin(phase * 1.7) > 0.7:
				_rect(result, [x, y, 1, 1], [235, 100, 115])
		elif particle_type == "spirit":
			_ellipse(result, [x - 6, y - 6, 12, 14], _with_alpha(color, 35))
			_circle(result, [x, y - 1], 3, _with_alpha(color, 130))
			_circle(result, [x - 1, y - 2], 1, [220, 255, 240, 180])
	return result


static func torch_ops(renderer, t: int) -> Array:
	var result: Array = []
	var palette := _torch_palette(String(renderer.theme.get("name", "Forest")))
	for index in range(renderer.torch_stones.size()):
		var point: Array = renderer.torch_stones[index]
		var tx := int(point[0])
		var ty := int(point[1])
		var frame := (floori(float(t) / 6.0) + index) % 4
		_rect(result, [tx - 3, ty + 2, 6, 8], [12, 8, 12])
		_rect(result, [tx - 3, ty + 2, 6, 7], [55, 55, 65])
		_rect(result, [tx - 2, ty + 3, 4, 5], [95, 95, 105])
		_rect(result, [tx - 1, ty - 2, 2, 4], [12, 8, 12])
		_rect(result, [tx - 1, ty - 2, 2, 4], [60, 40, 20])
		if frame == 0:
			_flame_a(result, tx, ty - 2, palette)
		elif frame == 1 or frame == 3:
			_flame_b(result, tx, ty - 2, palette)
		else:
			_flame_c(result, tx, ty - 2, palette)
		var glow_size := 22 + (frame % 2) * 3
		for radius in range(glow_size, 0, -4):
			if 25 - radius > 0:
				_circle(result, [tx, ty - 6], radius, palette["glow"])
	return result


static func _torch_palette(theme_name: String) -> Dictionary:
	match theme_name:
		"Ice":
			return _palette(
				[30, 100, 180],
				[80, 160, 240],
				[150, 210, 255],
				[220, 245, 255],
				[100, 180, 255, 25]
			)
		"Desert":
			return _palette(
				[200, 100, 20],
				[255, 170, 40],
				[255, 220, 100],
				[255, 250, 200],
				[255, 200, 100, 25]
			)
		"Soulforged Expanse":
			return _palette(
				[5, 40, 60], [15, 100, 140], [55, 190, 230], [200, 250, 255], [55, 190, 230, 25]
			)
		"Radiant Expanse":
			return _palette(
				[130, 75, 15], [200, 130, 30], [255, 220, 100], [255, 245, 170], [255, 220, 100, 25]
			)
		"Abyssal Depths":
			return _palette(
				[5, 20, 45], [20, 70, 130], [110, 190, 220], [230, 250, 255], [110, 190, 220, 25]
			)
		"Eldritch Depths":
			return _palette(
				[5, 20, 30], [15, 60, 90], [40, 140, 180], [200, 250, 255], [40, 140, 180, 25]
			)
		"Silver Sanctum":
			return _palette(
				[110, 75, 15], [200, 150, 45], [250, 210, 100], [255, 245, 180], [250, 210, 100, 25]
			)
		"Eternal Flame":
			return _palette(
				[170, 60, 5], [240, 130, 20], [255, 200, 60], [255, 240, 130], [255, 200, 60, 25]
			)
		"Primordial Grove":
			return _palette(
				[20, 70, 25], [60, 155, 50], [130, 220, 100], [200, 255, 140], [130, 220, 100, 25]
			)
		"Celestial Peaks":
			return _palette(
				[95, 65, 20], [180, 130, 40], [240, 195, 80], [255, 250, 210], [240, 195, 80, 25]
			)
		"Cosmic Expanse":
			return _palette(
				[65, 20, 130], [135, 55, 220], [200, 130, 255], [235, 180, 255], [200, 130, 255, 25]
			)
		"Royal Citadel":
			return _palette(
				[115, 85, 20], [200, 155, 40], [245, 215, 95], [255, 245, 180], [245, 215, 95, 25]
			)
		"Violet Court":
			return _palette(
				[85, 20, 145], [170, 55, 230], [220, 130, 255], [245, 190, 255], [220, 130, 255, 25]
			)
		"Crimson Dominion":
			return _palette(
				[160, 25, 50], [220, 50, 90], [255, 90, 130], [255, 180, 200], [255, 90, 130, 25]
			)
		_:
			return _palette(
				[140, 40, 15], [220, 90, 25], [255, 180, 60], [255, 240, 150], [255, 180, 80, 25]
			)


static func _palette(d: Array, m: Array, l: Array, h: Array, glow: Array) -> Dictionary:
	return {"d": d, "m": m, "l": l, "h": h, "glow": glow}


static func _flame_a(result: Array, tx: int, ty: int, palette: Dictionary) -> void:
	_rect(result, [tx - 4, ty - 6, 8, 8], palette["d"])
	_rect(result, [tx - 3, ty - 10, 6, 4], palette["d"])
	_rect(result, [tx - 2, ty - 14, 4, 4], palette["d"])
	_rect(result, [tx - 3, ty - 5, 6, 6], palette["m"])
	_rect(result, [tx - 2, ty - 9, 4, 4], palette["m"])
	_rect(result, [tx - 2, ty - 4, 4, 4], palette["l"])
	_rect(result, [tx - 1, ty - 8, 2, 4], palette["l"])
	_rect(result, [tx - 1, ty - 3, 2, 2], palette["h"])


static func _flame_b(result: Array, tx: int, ty: int, palette: Dictionary) -> void:
	_rect(result, [tx - 4, ty - 7, 8, 8], palette["d"])
	_rect(result, [tx - 3, ty - 11, 6, 4], palette["d"])
	_rect(result, [tx - 3, ty - 6, 6, 6], palette["m"])
	_rect(result, [tx - 2, ty - 10, 4, 4], palette["m"])
	_rect(result, [tx - 2, ty - 5, 4, 4], palette["l"])
	_rect(result, [tx - 1, ty - 4, 2, 2], palette["h"])


static func _flame_c(result: Array, tx: int, ty: int, palette: Dictionary) -> void:
	_rect(result, [tx - 4, ty - 6, 8, 8], palette["d"])
	_rect(result, [tx - 3, ty - 10, 6, 4], palette["d"])
	_rect(result, [tx - 3, ty - 5, 6, 6], palette["m"])
	_rect(result, [tx - 2, ty - 4, 4, 4], palette["l"])
	_rect(result, [tx - 1, ty - 3, 2, 2], palette["h"])


static func _boss_ops(renderer, t: int) -> Array:
	var result: Array = []
	var identity := String(renderer.theme.get("boss_identity", ""))
	if String(renderer.theme.get("name", "")) == "Haunted Veil":
		identity = "krobellus"
	if identity == "abaddon":
		for index in range(mini(10, renderer.bones.size())):
			var entry: Array = renderer.bones[index]
			var phase := float(t) * 0.035 + float(index)
			var sx := int(float(entry[0]) + sin(phase) * 5.0)
			var sy := int(float(entry[1]) - 20.0 + sin(phase * 1.4) * 4.0)
			_circle(result, [sx, sy], 2, [200, 65, 85])
			_arc(result, [sx - 7, sy - 10, 14, 16], [117, 35, 65], 0.2, 2.8)
	elif identity == "alchemist":
		for index in range(mini(12, renderer.rocks_mossy.size())):
			var entry: Array = renderer.rocks_mossy[index]
			var phase := fmod(float(t) * 0.025 + float(index * 17), 55.0)
			var bx := int(float(entry[0]) + sin(float(t) * 0.03 + float(index)) * 4.0)
			var by := int(float(entry[1]) - 8.0 - phase)
			_circle(result, [bx, by], 2, [157, 230, 67], 1)
			if index % 3 == 0:
				_circle(result, [bx - 1, by - 1], 1, [225, 255, 150])
	elif identity == "ignis_drachorn":
		var points: Array = renderer.river_points
		for index in range(3, points.size(), 11):
			var point: Array = points[(index + int(float(t) * 0.025)) % points.size()]
			var rise := int(fmod(float(t) * 0.18 + float(index * 7), 18.0))
			var x := int(point[0])
			var y := int(point[1]) - rise
			_circle(result, [x, y], 2, [255, 145, 35])
			_line(result, [x, y], [x + 2, y - 5], [255, 230, 110])
	elif identity == "krobellus":
		for index in range(mini(10, renderer.gravestones.size())):
			var entry: Array = renderer.gravestones[index]
			var phase := float(t) * 0.025 + float(index) * 1.4
			var sx := int(float(entry[0]) + sin(phase) * 6.0)
			var sy := int(float(entry[1]) - 18.0 - (sin(phase * 0.8) + 1.0) * 3.0)
			_circle(result, [sx, sy], 2, [84, 230, 190])
			_arc(result, [sx - 8, sy - 10, 16, 16], [177, 88, 224], 0.2, 2.7)
	return result


static func _rect(result: Array, rect: Array, color: Array, width: int = 0) -> void:
	result.append(
		{
			"kind": "rect",
			"rect": _numbers(rect),
			"color": _rgba(color),
			"mult": 255,
			"width": width,
			"radius": 0
		}
	)


static func _circle(
	result: Array, center: Array, radius: int, color: Array, width: int = 0
) -> void:
	result.append(
		{
			"kind": "circle",
			"center": _numbers(center),
			"radius": radius,
			"color": _rgba(color),
			"mult": 255,
			"width": width
		}
	)


static func _ellipse(result: Array, rect: Array, color: Array, width: int = 0) -> void:
	result.append(
		{
			"kind": "ellipse",
			"rect": _numbers(rect),
			"color": _rgba(color),
			"mult": 255,
			"width": width
		}
	)


static func _line(result: Array, a: Array, b: Array, color: Array, width: int = 1) -> void:
	result.append(
		{
			"kind": "line",
			"a": _numbers(a),
			"b": _numbers(b),
			"color": _rgba(color),
			"mult": 255,
			"width": width
		}
	)


static func _arc(
	result: Array, rect: Array, color: Array, start: float, end: float, width: int = 1
) -> void:
	result.append(
		{
			"kind": "arc",
			"rect": _numbers(rect),
			"color": _rgba(color),
			"mult": 255,
			"width": width,
			"start": start,
			"end": end
		}
	)


static func _rgba(color: Array) -> Array:
	var result: Array = []
	for index in range(4):
		result.append(int(color[index]) if index < color.size() else 255)
	return result


static func _with_alpha(color: Array, alpha: int) -> Array:
	var result := _rgba(color)
	result[3] = alpha
	return result


static func _numbers(values: Array) -> Array:
	var result: Array = []
	for value in values:
		var number := float(value)
		result.append(int(number) if is_equal_approx(number, roundf(number)) else number)
	return result
