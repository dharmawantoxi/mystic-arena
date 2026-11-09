class_name GrimjawHurt
extends ZephyrHurt

## Shared HP observer math, independently source-tested against Grimjaw.
## Only on_hurt foreground streaks and flash; not full Grimjaw particles/director.
static var config: Dictionary = {}
var was_alive := true


static func ensure_loaded() -> void:
	if config.is_empty():
		var file := FileAccess.open("res://data/grimjaw_hurt.json", FileAccess.READ)
		if file != null:
			config = JSON.parse_string(file.get_as_text())


static func hurt_recipe() -> Dictionary:
	ensure_loaded()
	return config.recipe


static func budget_count(budget: float) -> int:
	if budget <= 0.0:
		return 0
	return maxi(0, ZephyrSkill.python_round(int(hurt_recipe().count) * budget))


func commands() -> Array:
	if hit_flash <= 0.0:
		return []
	ensure_loaded()
	var rgb: Array = config.palette.fx_hot
	var radius := int(18 + 26 * (hit_flash / 0.16))
	var power := hit_flash / 0.16 * 0.7
	return glow_commands(radius, rgb, power, [int(x) - radius, int(y) - radius - 6])


static func glow_commands(radius: int, rgb: Array, power: float, origin: Array) -> Array:
	radius = maxi(2, radius)
	var result: Array = []
	var bands := [0.22, 0.45, 0.70, 1.0]
	for i in bands.size():
		var f: float = bands[i]
		var k := power * f
		if k <= 0.004:
			continue
		var r := maxi(1, int(radius * (1.05 - 0.75 * f)))
		var dx := 0
		var dy := 0
		if radius >= 7:
			dx = ZephyrSkill.python_round((ZephyrSkill.hash01(radius * 31 + i * 7) - 0.5) * 2)
			dy = ZephyrSkill.python_round((ZephyrSkill.hash01(radius * 57 + i * 13) - 0.5) * 2)
		result.append(
			[
				"circle",
				[int(rgb[0] * k), int(rgb[1] * k), int(rgb[2] * k), mini(255, int(255 * k))],
				[origin[0] + radius + 1 + dx, origin[1] + radius + 1 + dy],
				r
			]
		)
	return result


func observe_death(alive: bool) -> bool:
	var died := was_alive and not alive
	was_alive = alive
	return died
