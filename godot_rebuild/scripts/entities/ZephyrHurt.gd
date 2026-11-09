class_name ZephyrHurt
extends RefCounted

## Director HP-observation/hit-flash slice. No hero reference or gameplay feedback.
var last_hp: Variant = null
var hit_flash := 0.0
var x := 0.0
var y := 0.0


func observe(hp: float, px: float, py: float, dt: float) -> bool:
	x = px
	y = py
	var hurt := last_hp != null and hp < float(last_hp) - 0.01
	last_hp = hp
	if hurt:
		hit_flash = 0.16
	if hit_flash > 0.0:
		hit_flash = maxf(0.0, hit_flash - dt)
	return hurt


static func recipe() -> Dictionary:
	ZephyrBolt.ensure_loaded()
	return {
		"count": 3,
		"options":
		{
			"speed": [80, 210],
			"life": [0.2, 0.4],
			"size": [2, 4],
			"colors": [ZephyrBolt.palette.fx_light, ZephyrBolt.palette.highlight],
			"drag": 3.0,
			"shape": "streak"
		}
	}


func commands() -> Array:
	if hit_flash <= 0.0:
		return []
	ZephyrBolt.ensure_loaded()
	var rgb: Array = ZephyrBolt.palette.highlight
	var radius := int(18 + 26 * (hit_flash / 0.16))
	return [
		[
			"glow",
			[rgb[0], rgb[1], rgb[2], 255],
			[int(x) - radius, int(y) - radius - 6],
			radius,
			hit_flash / 0.16 * 0.7
		]
	]
