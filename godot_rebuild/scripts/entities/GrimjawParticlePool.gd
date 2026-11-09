class_name GrimjawParticlePool
extends ZephyrParticlePool

## Shared pool mechanics with Grimjaw factory/palette and source budget rule.
var glow_enabled := true

## Stream preserves the additional direct-spawn budget gate from source.


func _init() -> void:
	GrimjawHurt.ensure_loaded()
	cap = int(GrimjawHurt.config.capacity)


func _new_particle() -> ZephyrParticle:
	return GrimjawParticle.new()


func burst(px: float, py: float, requested: int, options: Dictionary = {}) -> int:
	var count := maxi(0, ZephyrSkill.python_round(requested * budget)) if budget > 0.0 else 0
	if count <= 0:
		return 0
	GrimjawHurt.ensure_loaded()
	var palette: Dictionary = GrimjawHurt.config.palette
	var settings := options.duplicate()
	if not settings.has("colors") or settings.colors == null or settings.colors.is_empty():
		settings.colors = [palette.fx_bright, palette.fx_light, palette.fx_hot]
	var original_budget := budget
	budget = 1.0
	var emitted := super.burst(px, py, count, settings)
	budget = original_budget
	return emitted


func stream(
	px: float, py: float, tx: float, ty: float, requested: int, options: Dictionary = {}
) -> int:
	var count := maxi(0, ZephyrSkill.python_round(requested * budget)) if budget > 0.0 else 0
	if count <= 0:
		return 0
	GrimjawHurt.ensure_loaded()
	var palette: Dictionary = GrimjawHurt.config.palette
	var selected: Variant = options.get("colors")
	var colors: Array = (
		selected
		if selected is Array and not selected.is_empty()
		else [palette.fx_light, palette.ember]
	)
	var seconds: Array = options.get("life", [0.3, 0.6])
	var extent: Array = options.get("size", [1, 3])
	var emitted := 0
	for i in count:
		var t := float(i) / maxi(1, count)
		var sx := px + (tx - px) * t + uniform(-4, 4)
		var sy := py + (ty - py) * t + uniform(-3, 3)
		var dx := tx - sx
		var dy := ty - sy
		var distance := maxf(1.0, sqrt(dx * dx + dy * dy))
		var speed := uniform(90, 200)
		var life := uniform(seconds[0], seconds[1])
		var size := uniform(extent[0], extent[1])
		var settings := {
			"drag": options.get("drag", 1.2),
			"shape": options.get("shape", "ember"),
			"color_end": palette.fx_dark,
			"rotation": random_value() * TAU,
			"rotation_speed": uniform(-6, 6)
		}
		if (
			spawn(
				sx,
				sy,
				dx / distance * speed,
				dy / distance * speed,
				life,
				size,
				colors[i % colors.size()],
				settings
			)
			!= null
		):
			emitted += 1
	return emitted


func draw(canvas: CanvasItem, layer := "") -> void:
	for particle: ZephyrParticle in live:
		if particle is GrimjawParticle:
			particle.glow_allowed = glow_enabled
	super.draw(canvas, layer)
