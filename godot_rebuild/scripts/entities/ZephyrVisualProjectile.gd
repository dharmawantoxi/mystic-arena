class_name ZephyrVisualProjectile
extends RefCounted

## Visual-only independent ZephyrProjectile. Never applies gameplay damage.
## Double arrays preserve source motion precision; targets are transient snapshots.
var position: Array = [0.0, 0.0]
var spawn_pos: Array = [0.0, 0.0]
var velocity: Array = [0.0, 0.0]
var hit_pos: Array = [0.0, 0.0]
var speed := 520.0
var damage := 0.0
var lifetime := 0.0
var max_lifetime := 2.6
var radius := 6.0
var rotation := 0.0
var trail: Array = []
var trail_life := 0.20
var active := true
var state := "travel"
var kind := "bolt"
var homing := 6.5
var impact_age := 0.0
var emit_acc := 0.0
var events: Array = []
var hits: Array = []
var target_id := 0
var random_tape: Array = []
var tape_index := 0
var rng := RandomNumberGenerator.new()


func spawn(
	x: float, y: float, tx: float, ty: float, options: Dictionary = {}
) -> ZephyrVisualProjectile:
	position = [x, y]
	spawn_pos = [x, y]
	hit_pos = [tx, ty]
	speed = float(options.get("speed", 520.0))
	damage = float(options.get("damage", 0.0))
	radius = float(options.get("radius", 6.0))
	homing = float(options.get("homing", 6.5))
	kind = str(options.get("kind", "bolt"))
	target_id = int(options.get("target_id", 0))
	var dx := tx - x
	var dy := ty - y
	if dx * dx + dy * dy < 1e-6:
		dx = 1.0
		dy = 0.0
	var length := sqrt(dx * dx + dy * dy)
	velocity = [dx / length * speed, dy / length * speed]
	rotation = atan2(velocity[1], velocity[0])
	lifetime = 0.0
	impact_age = 0.0
	emit_acc = 0.0
	active = true
	state = "travel"
	trail.clear()
	events.clear()
	hits.clear()
	tape_index = 0
	rng.randomize()
	return self


func random_value() -> float:
	if not random_tape.is_empty():
		var value := float(random_tape[tape_index % random_tape.size()])
		tape_index += 1
		return value
	return rng.randf()


func uniform(low: float, high: float) -> float:
	return low + (high - low) * random_value()


func kill(at: Variant = null) -> void:
	if state != "travel":
		return
	state = "impact"
	hit_pos = position.duplicate() if at == null else at.duplicate()
	impact_age = 0.0
	hits.append(hit_pos.duplicate())


func _age_trail(dt: float) -> void:
	var keep: Array = []
	for sample: Array in trail:
		sample[1] = float(sample[1]) + dt
		if float(sample[1]) < trail_life:
			keep.append(sample)
	trail = keep


func update(dt: float, target: Dictionary = {}, connected := true) -> bool:
	events.clear()
	hits.clear()
	if state == "dead":
		return false
	if state == "impact":
		impact_age += dt
		_age_trail(dt)
		if impact_age > 0.28 and trail.is_empty():
			state = "dead"
			active = false
			return false
		return true
	lifetime += dt
	if lifetime > max_lifetime:
		kill()
		return true
	var target_alive := bool(target.get("alive", false))
	if target_alive:
		var dx := float(target.x) - float(position[0])
		var dy := float(target.y) - float(position[1])
		var squared := dx * dx + dy * dy
		if squared > 1.0:
			var length := sqrt(squared)
			var k := minf(1.0, homing * dt)
			velocity[0] += (dx / length * speed - float(velocity[0])) * k
			velocity[1] += (dy / length * speed - float(velocity[1])) * k
			length = sqrt(
				float(velocity[0]) * float(velocity[0]) + float(velocity[1]) * float(velocity[1])
			)
			if length * length > 1e-6:
				velocity = [
					float(velocity[0]) / length * speed, float(velocity[1]) / length * speed
				]
	rotation = atan2(velocity[1], velocity[0])
	trail.append([position.duplicate(), 0.0])
	if trail.size() > 16:
		trail.pop_front()
	_age_trail(dt)
	position[0] += float(velocity[0]) * dt
	position[1] += float(velocity[1]) * dt
	if connected:
		emit_acc += dt
		if emit_acc >= 0.028:
			emit_acc = 0.0
			var angle := rotation + PI + (random_value() - 0.5) * 1.1
			var tail_speed := uniform(20, 70)
			var life := uniform(0.16, 0.34)
			var size := uniform(1.5, 3.0)
			ZephyrBolt.ensure_loaded()
			var p := ZephyrBolt.palette
			var rgb: Array = p.fx_bright if random_value() < 0.5 else p.ember
			events.append(
				{
					"args":
					[
						position[0],
						position[1],
						cos(angle) * tail_speed,
						sin(angle) * tail_speed,
						life,
						size,
						rgb
					],
					"options": {"color_end": p.fx_dark, "drag": 3.0, "shape": "pixel"}
				}
			)
	if target_alive:
		var hit_radius := radius + float(target.get("radius", 12))
		var dx := float(position[0]) - float(target.x)
		var dy := float(position[1]) - float(target.y)
		if dx * dx + dy * dy <= hit_radius * hit_radius:
			kill([target.x, target.y])
	return true


func snapshot() -> Dictionary:
	return {
		"position": position,
		"spawn_pos": spawn_pos,
		"velocity": velocity,
		"hit_pos": hit_pos,
		"speed": speed,
		"damage": damage,
		"lifetime": lifetime,
		"max_lifetime": max_lifetime,
		"radius": radius,
		"rotation": rotation,
		"trail": trail,
		"trail_life": trail_life,
		"active": active,
		"state": state,
		"kind": kind,
		"homing": homing,
		"_impact_age": impact_age,
		"_emit_acc": emit_acc
	}


func commands() -> Array:
	if not active:
		return []
	ZephyrBolt.ensure_loaded()
	var p := ZephyrBolt.palette
	var result: Array = []
	if trail.size() >= 2:
		var ux := cos(rotation + PI / 2.0)
		var uy := sin(rotation + PI / 2.0)
		var first: Array = []
		var second: Array = []
		var center: Array = []
		var min_x := INF
		var min_y := INF
		var max_x := -INF
		var max_y := -INF
		for i in trail.size():
			var sample: Array = trail[i]
			var pv: Array = sample[0]
			var fade := maxf(0.0, 1.0 - float(sample[1]) / trail_life)
			var width := radius * 0.85 * (float(i + 1) / trail.size()) * fade
			var a := [float(pv[0]) + ux * width, float(pv[1]) + uy * width]
			var b := [float(pv[0]) - ux * width, float(pv[1]) - uy * width]
			first.append([int(a[0]), int(a[1])])
			second.append([int(b[0]), int(b[1])])
			center.append([int(pv[0]), int(pv[1])])
			min_x = minf(min_x, minf(a[0], b[0]))
			min_y = minf(min_y, minf(a[1], b[1]))
			max_x = maxf(max_x, maxf(a[0], b[0]))
			max_y = maxf(max_y, maxf(a[1], b[1]))
		var width := int(max_x) - (int(min_x) - 3) + 6
		var height := int(max_y) - (int(min_y) - 3) + 6
		if width > 0 and width < 1200 and height > 0 and height < 1200:
			second.reverse()
			result.append(["polygon", [p.fx_mid[0], p.fx_mid[1], p.fx_mid[2], 120], first + second])
			result.append(
				["polyline", [p.fx_light[0], p.fx_light[1], p.fx_light[2], 170], center, 2]
			)
	if state != "impact":
		result.append_array(
			ZephyrBolt.commands_at(
				position[0], position[1], rotation, int(lifetime * 60), false, radius
			)
		)
	return result
