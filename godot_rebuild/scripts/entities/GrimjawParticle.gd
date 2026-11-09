class_name GrimjawParticle
extends ZephyrParticle

## Grimjaw particle primitive geometry; not additive/raster pixel parity.
var back := false
var glow_allowed := true


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
	super.spawn(px, py, speed_x, speed_y, seconds, particle_size, rgb, options)
	back = bool(options.get("back", false))
	return self


func is_back() -> bool:
	return back


func white_color() -> Array:
	GrimjawHurt.ensure_loaded()
	return GrimjawHurt.config.palette.fx_white


func snapshot() -> Dictionary:
	var result := super.snapshot()
	result.back = back
	return result


func commands() -> Array:
	if not active:
		return []
	if shape not in ["ember", "smoke", "glow", "spark"]:
		return super.commands()
	var fade := pow(life / max_life, fade_pow)
	var opacity := int(alpha * fade)
	if opacity <= 3:
		return []
	var rgb := color.duplicate()
	if color_end is Array:
		rgb = _mix_rgb(color_end, color, fade)
	var px := int(x)
	var py := int(y)
	var extent := maxi(1, int(size * (0.35 + 0.65 * fade)))
	GrimjawHurt.ensure_loaded()
	var palette: Dictionary = GrimjawHurt.config.palette
	if shape == "glow":
		if not glow_allowed:
			extent = maxi(1, int(extent / 2))
		return GrimjawHurt.glow_commands(
			extent * 2, rgb, float("%.2f" % (0.9 * fade)), [px - extent * 2, py - extent * 2]
		)
	if shape == "spark":
		return spark_commands(extent + 1, rgb, opacity, [px - extent - 1, py - extent - 1])
	if shape == "ember":
		var flicker := 0.72 + 0.28 * sin(rotation * 6.0)
		var height := maxi(1, int(extent * flicker))
		var width := maxi(1, int(extent * 0.6))
		var dark := _mix_rgb(rgb, palette.fx_darkest, 0.4)
		return [
			[
				"polygon",
				[dark[0], dark[1], dark[2], int(opacity * 0.8)],
				[[px, py - height], [px + width, py], [px, py + height], [px - width, py]]
			],
			[
				"polygon",
				[rgb[0], rgb[1], rgb[2], opacity],
				[
					[px, py - int(height / 2)],
					[px + int(width / 2), py],
					[px, py + int(height / 2)],
					[px - int(width / 2), py]
				]
			]
		]
	var radius := maxi(2, extent)
	var light := _mix_rgb(rgb, palette.fx_white, 0.15)
	return [
		["circle", [rgb[0], rgb[1], rgb[2], int(opacity * 0.5)], [px, py], radius],
		[
			"circle",
			[light[0], light[1], light[2], int(opacity * 0.25)],
			[px - int(radius / 3), py - int(radius / 3)],
			maxi(1, int(radius / 2))
		]
	]


static func _mix_rgb(first: Array, second: Array, t: float) -> Array:
	return [
		int(first[0] + (second[0] - first[0]) * t),
		int(first[1] + (second[1] - first[1]) * t),
		int(first[2] + (second[2] - first[2]) * t)
	]


static func spark_commands(extent: int, rgb: Array, opacity: int, origin: Array) -> Array:
	extent = maxi(3, extent)
	var cx := int(origin[0]) + extent
	var cy := int(origin[1]) + extent
	var result: Array = []
	for i in 5:
		var angle := i * TAU / 5.0 + ZephyrSkill.hash01(extent * 31 + i) * 0.6
		var length := extent * (0.65 + 0.35 * ZephyrSkill.hash01(extent * 17 + i * 7))
		result.append(
			[
				"line",
				[rgb[0], rgb[1], rgb[2], 235.0 * opacity / 255.0],
				[cx, cy],
				[cx + int(cos(angle) * length), cy + int(sin(angle) * length)],
				2 if i % 2 == 0 else 1
			]
		)
	result.append(["circle", [255, 255, 255, opacity], [cx, cy], maxi(1, int(extent / 4))])
	return result
