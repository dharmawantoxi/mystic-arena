class_name ZephyrImpact
extends RefCounted

## Native ImpactFX lifecycle and primitive/helper commands. Ellipse/spark are
## semantic helper descriptors; CanvasItem rasterization/RGB_ADD parity is not
## claimed. Python's two unbound-k radial loops were corrected before porting.
var x := 0.0
var y := 0.0
var angle := 0.0
var power := 1.0
var age := 0.0
var duration := 0.44
var critical := false
var active := false
var color: Array = []
var kind := "magic"


func spawn(
	px: float, py: float, direction := 0.0, strength := 1.0, crit := false, impact_kind := "magic"
) -> ZephyrImpact:
	x = px
	y = py
	angle = direction
	power = maxf(0.35, strength)
	age = 0.0
	duration = 0.34 + 0.10 * minf(2.0, power)
	critical = crit
	kind = impact_kind
	active = true
	ZephyrBolt.ensure_loaded()
	color = ZephyrBolt.palette.get("gold" if crit else "fx_hot", []).duplicate()
	return self


func update(dt: float) -> bool:
	age += dt
	if age >= duration:
		active = false
	return active


func snapshot() -> Dictionary:
	return {
		"x": x,
		"y": y,
		"angle": angle,
		"power": power,
		"age": age,
		"duration": duration,
		"crit": critical,
		"active": active,
		"color": color,
		"kind": kind
	}


static func _rgba(rgb: Array, opacity := 255) -> Array:
	return [rgb[0], rgb[1], rgb[2], opacity]


static func _mix(first: Array, second: Array, fraction: float) -> Array:
	var t := clampf(fraction, 0.0, 1.0)
	return [
		int(first[0] + (second[0] - first[0]) * t),
		int(first[1] + (second[1] - first[1]) * t),
		int(first[2] + (second[2] - first[2]) * t)
	]


func commands() -> Array:
	if not active or color.is_empty():
		return []
	var palette := ZephyrBolt.palette
	var result: Array = []
	var t := age / duration
	var inv := 1.0 - t
	var px := int(x)
	var py := int(y)
	var ca := cos(angle)
	var sa := sin(angle)
	if t < 0.22:
		var ft := 1.0 - t / 0.22
		var radius := int(int((5 + 9 * power) * (0.5 + 0.5 * ft)) / 2) * 2 + 2
		result.append(
			["glow", _rgba(palette.fx_hot), [px - radius, py - radius], radius, 0.55 * ft]
		)
		var length := (16 + 34 * power) * ft
		for index in 4:
			var direction := angle + index * PI / 4.0
			var extent := length if index % 2 == 0 else length * 0.42
			result.append(
				[
					"line",
					_rgba(palette.fx_white, int(240 * ft)),
					[px, py],
					[px + int(cos(direction) * extent), py + int(sin(direction) * extent)],
					3 if index % 2 == 0 else 1
				]
			)
	var radius := int(int((8 + 46 * power) * (0.25 + 1.05 * t)) / 3) * 3
	var thickness := maxi(1, int(4 * inv * power))
	var opacity := int(215 * inv * inv)
	if opacity > 6 and radius > 4:
		result.append(
			[
				"ellipse",
				_rgba(palette.fx_light, opacity),
				[px, py],
				radius,
				maxi(3, int(radius * 0.62)),
				thickness,
				rad_to_deg(angle)
			]
		)
		var inner := int(radius * 0.58)
		if inner > 4:
			result.append(
				[
					"ellipse",
					_rgba(color, int(opacity * 0.75)),
					[px, py],
					inner,
					maxi(2, int(inner * 0.7)),
					maxi(1, thickness - 1),
					rad_to_deg(angle)
				]
			)
	if t < 0.6:
		var strength := 1.0 - t / 0.6
		var start_radius := int((6 + 20 * power) * (0.3 + 1.1 * t))
		for index in 4:
			var direction := angle + index * PI / 4.0 + 0.19
			var extent := (7 + 15 * power) * strength * (1.0 if index % 2 else 0.55)
			result.append(
				[
					"line",
					_rgba(_mix(palette.fx_dark, palette.fx_bright, strength)),
					[
						px + int(cos(direction) * start_radius),
						py + int(sin(direction) * start_radius)
					],
					[
						px + int(cos(direction) * (start_radius + extent)),
						py + int(sin(direction) * (start_radius + extent))
					],
					2 if index % 2 else 1
				]
			)
	if t < 0.55:
		var strength := 1.0 - t / 0.55
		var span := 0.55 + 0.5 * power
		var base_radius := int(12 + 30 * power * (0.4 + t))
		for index: int in [-1, 0, 1]:
			var start := angle - span / 2 + index * 0.12
			var end := start + span
			var extent := base_radius - absi(index) * 5
			result.append(
				[
					"arc",
					_rgba(
						palette.fx_white if index == 0 else palette.fx_bright, int(225 * strength)
					),
					[px - extent, py - extent, extent * 2, extent * 2],
					-end,
					-start,
					3 if index == 0 else 2
				]
			)
	if t < 0.42:
		var strength := 1.0 - t / 0.42
		var size := int(int((5 + 9 * power) * (0.5 + 0.5 * strength)) / 2) * 2 + 2
		result.append(
			[
				"spark",
				_rgba(color, int(255 * strength)),
				[px - size - int(ca * 2), py - size - int(sa * 2)],
				size
			]
		)
	return result


func draw(canvas: CanvasItem) -> void:
	ZephyrBolt.draw_shapes(canvas, commands())
