extends RefCounted
## Replays the `_render.py::HitParticle` source oracle fixture through the
## native port. `hit_particle_source_oracle.py` executes the real source class
## (pygame pre-render included) so these numbers are not hand-written.

const HitParticle = preload("res://scripts/ui/hit_particle.gd")
const FIXTURE := "res://tests/fixtures/hit_particle_source.json"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Hit particle fixture parses")
	if not (data is Dictionary):
		return
	var cases: Array = data["cases"]
	check.call(cases.size() == 3, "Source fixture covers the sampled cases")
	for entry in cases:
		_replay(entry as Dictionary, check)
	_random_cone(check)


func _replay(entry: Dictionary, check: Callable) -> void:
	var label: String = entry["name"]
	var config: Dictionary = entry["config"]
	var tint: Array = config["color"]
	var item := HitParticle.new()
	item.configure(
		float(config["x"]),
		float(config["y"]),
		Color8(int(tint[0]), int(tint[1]), int(tint[2])),
		Vector2(float(entry["vx"]), float(entry["vy"])),
		int(config["lifetime"]),
		int(config["size"])
	)
	check.call(
		is_equal_approx(item.gravity, float(entry["gravity"])), "Gravity matches source: %s" % label
	)
	var steps: Array = entry["steps"]
	for index in range(steps.size()):
		item.update()
		var expected: Array = steps[index]
		check.call(
			(
				is_equal_approx(item.x, float(expected[0]))
				and is_equal_approx(item.y, float(expected[1]))
				and is_equal_approx(item.vx, float(expected[2]))
				and is_equal_approx(item.vy, float(expected[3]))
			),
			"Motion matches source step %d: %s" % [index, label]
		)
		check.call(
			item.lifetime == int(expected[4]), "Lifetime matches step %d: %s" % [index, label]
		)
		check.call(
			item.alive == (int(expected[5]) == 1), "Alive matches step %d: %s" % [index, label]
		)
		check.call(item.alpha() == int(expected[6]), "Alpha matches step %d: %s" % [index, label])
		check.call(
			item.current_size() == int(expected[7]), "Size matches step %d: %s" % [index, label]
		)


## The fixture pins a seeded draw, so cover the cone itself separately.
func _random_cone(check: Callable) -> void:
	for _attempt in range(24):
		var item := HitParticle.new()
		item.configure(0.0, 0.0, Color.WHITE)
		var speed := Vector2(item.vx, item.vy).length()
		check.call(
			speed >= HitParticle.SPEED_MIN - 1e-6 and speed <= HitParticle.SPEED_MAX + 1e-6,
			"Random spark speed stays inside the source cone"
		)
