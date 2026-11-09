class_name ZephyrSwingTrail
extends RefCounted

## Native SwingTrail lifecycle and three-pass command geometry. Staff anchors
## are sampled from the Python rig at the exact baked attack pose progress.
static var config: Dictionary = {}
static var config_loaded := false
var samples := 7
var points: Array = []
var color_edge: Array = []
var color_core: Array = []
var life := 0.26
var width_boost := 1.0
var active := false


static func ensure_loaded() -> void:
	if config_loaded:
		return
	config_loaded = true
	var file := FileAccess.open("res://data/zephyr_trail.json", FileAccess.READ)
	if file != null:
		var parsed: Variant = JSON.parse_string(file.get_as_text())
		if parsed is Dictionary:
			config = parsed


func _init() -> void:
	ensure_loaded()
	if config.is_empty():
		return
	var defaults: Dictionary = config.defaults
	samples = int(defaults.samples)
	life = float(defaults.life)
	width_boost = float(defaults.width_boost)
	color_edge = defaults.color_edge.duplicate()
	color_core = defaults.color_core.duplicate()


func reset() -> void:
	points.clear()
	active = false


func push(grip: Array, tip: Array) -> void:
	points.append([grip.duplicate(), tip.duplicate(), 0.0])
	if points.size() > samples:
		points.pop_front()
	active = true


func update(dt: float) -> void:
	if points.is_empty():
		active = false
		return
	var keep: Array = []
	for point: Array in points:
		point[2] = float(point[2]) + dt
		if float(point[2]) < life:
			keep.append(point)
	points = keep
	if points.is_empty():
		active = false


func snapshot() -> Dictionary:
	return {
		"samples": samples,
		"points": points.duplicate(true),
		"color_edge": color_edge,
		"color_core": color_core,
		"life": life,
		"width_boost": width_boost,
		"active": active
	}


static func _point(point: Array) -> Array:
	return [int(point[0]), int(point[1])]


static func _middle(grip: Array, tip: Array) -> Array:
	return [
		float(grip[0]) + (float(tip[0]) - float(grip[0])) * 0.5,
		float(grip[1]) + (float(tip[1]) - float(grip[1])) * 0.5
	]


func commands() -> Array:
	var count := points.size()
	if count < 2 or color_edge.is_empty() or color_core.is_empty():
		return []
	var min_x := INF
	var max_x := -INF
	var min_y := INF
	var max_y := -INF
	for point: Array in points:
		for endpoint: Array in [point[0], point[1]]:
			min_x = minf(min_x, float(endpoint[0]))
			max_x = maxf(max_x, float(endpoint[0]))
			min_y = minf(min_y, float(endpoint[1]))
			max_y = maxf(max_y, float(endpoint[1]))
	var width := int(max_x) - int(min_x) + 12
	var height := int(max_y) - int(min_y) + 12
	if width <= 0 or height <= 0 or width > 1400 or height > 1400:
		return []
	ZephyrBolt.ensure_loaded()
	var white: Array = ZephyrBolt.palette.get("fx_white", [255, 242, 252])
	var result: Array = []
	# Keep the Python order: ALL ribbon bodies, then ALL cores, then tips.
	for layer in 3:
		for index in range(count - 1):
			var first: Array = points[index]
			var second: Array = points[index + 1]
			var fade := maxf(0.0, 1.0 - float(first[2]) / life)
			var weight := float(index + 1) / count
			weight *= weight
			var base := [150, 215, 235]
			var threshold := [4, 6, 8]
			var opacity := int(
				float(base[layer]) * weight * fade * (width_boost if layer == 0 else 1.0)
			)
			if opacity <= int(threshold[layer]):
				continue
			var rgb: Array = color_edge if layer == 0 else (color_core if layer == 1 else white)
			var rgba := [rgb[0], rgb[1], rgb[2], opacity]
			if layer == 0:
				result.append(
					[
						"polygon",
						rgba,
						[_point(first[0]), _point(first[1]), _point(second[1]), _point(second[0])]
					]
				)
			elif layer == 1:
				result.append(
					[
						"polygon",
						rgba,
						[
							_point(_middle(first[0], first[1])),
							_point(first[1]),
							_point(second[1]),
							_point(_middle(second[0], second[1]))
						]
					]
				)
			else:
				result.append(["line", rgba, _point(first[1]), _point(second[1]), 2])
	return result


static func attachment(index: int, position: Array, facing: int, scale: float) -> Dictionary:
	ensure_loaded()
	var anchors: Array = config.get("attachments", [])
	if index < 0 or index >= anchors.size():
		return {}
	var sample: Dictionary = anchors[index]
	var flip := -1.0 if facing < 0 else 1.0
	return {
		"inner":
		[
			float(position[0]) + float(sample.inner[0]) * flip * scale,
			float(position[1]) + float(sample.inner[1]) * scale
		],
		"outer":
		[
			float(position[0]) + float(sample.outer[0]) * flip * scale,
			float(position[1]) + float(sample.outer[1]) * scale
		],
		"swinging": bool(sample.swinging)
	}


static func pose_index(unit: BattleUnit) -> int:
	ensure_loaded()
	if (
		config.is_empty()
		or not unit.alive
		or unit.kind != BattleUnit.Kind.HERO
		or unit.unit_type != "zephyr"
	):
		return -1
	if unit.attack_anim_timer <= 0 or (unit.active_skill != null and str(unit.active_skill) != ""):
		return -1
	return HeroVisuals.attack_frame([0, config.attachments.size()], unit)


func draw(canvas: CanvasItem) -> void:
	ZephyrBolt.draw_shapes(canvas, commands())
