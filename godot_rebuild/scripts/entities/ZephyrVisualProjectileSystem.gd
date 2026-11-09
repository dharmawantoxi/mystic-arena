class_name ZephyrVisualProjectileSystem
extends RefCounted

## Independent visual manager, not EntityProjectiles gameplay replacement.
var cap := 0
var projectiles: Array[ZephyrVisualProjectile] = []
var hits: Array = []


func _init() -> void:
	var file := FileAccess.open("res://data/zephyr_projectile.json", FileAccess.READ)
	if file != null:
		var config: Dictionary = JSON.parse_string(file.get_as_text())
		cap = int(config.capacity)


func spawn(
	x: float, y: float, tx: float, ty: float, options: Dictionary = {}
) -> ZephyrVisualProjectile:
	if projectiles.size() >= cap:
		return null
	var projectile := ZephyrVisualProjectile.new().spawn(x, y, tx, ty, options)
	projectiles.append(projectile)
	return projectile


func update(dt: float, targets: Dictionary = {}, particles: ZephyrParticlePool = null) -> void:
	hits.clear()
	var keep: Array[ZephyrVisualProjectile] = []
	for projectile: ZephyrVisualProjectile in projectiles:
		var alive := projectile.update(dt, targets.get(projectile.target_id, {}), particles != null)
		hits.append_array(projectile.hits)
		if particles != null:
			for event: Dictionary in projectile.events:
				var a: Array = event.args
				particles.spawn(a[0], a[1], a[2], a[3], a[4], a[5], a[6], event.options)
		if alive:
			keep.append(projectile)
	projectiles = keep


func draw(canvas: CanvasItem) -> void:
	for projectile: ZephyrVisualProjectile in projectiles:
		ZephyrBolt.draw_shapes(canvas, projectile.commands())


func clear() -> void:
	projectiles.clear()
	hits.clear()
