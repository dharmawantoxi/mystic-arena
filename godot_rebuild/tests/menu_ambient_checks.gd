extends RefCounted
## Source-replay checks for the baked fog atlas and live menu particle timeline (9bs).

const MenuAmbientLayout = preload("res://scripts/ui/menu_ambient_layout.gd")
const FOG := "res://assets/art/menu/menu_fog.png"
const MANIFEST := "res://data/art/menu.json"
const FIXTURE := "res://tests/fixtures/menu_ambient_source.json"

var _wrap_values: Array = []
var _wrap_index := 0


func run(check: Callable) -> void:
	var menu_data: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	check.call(menu_data is Dictionary, "The source menu ambience manifest parses")
	if not menu_data is Dictionary:
		return
	var fog: Dictionary = menu_data.get("fog", {})
	var fog_size: Array = fog.get("size", [0, 0])
	var source_size: Array = fog.get("source_size", [])
	var fog_frames: Dictionary = fog.get("frames", {})
	var image := Image.load_from_file(FOG)
	check.call(
		image != null and image.get_size() == Vector2i(int(fog_size[0]), int(fog_size[1])),
		"The baked two-layer source fog atlas decodes at its manifest size"
	)
	check.call(
		(
			_same_integer_values(fog_size, [3000, 720])
			and _same_integer_values(source_size, [1500, 720])
			and fog_frames.size() == 2
		),
		"Each parallax layer is a source-sized 1500 by 720 frame"
	)
	var layers: Array = fog.get("layers", [])
	check.call(
		(
			layers.size() == 2
			and is_equal_approx(float(layers[0].speed), 0.35)
			and is_equal_approx(float(layers[1].speed), 0.6)
			and int(layers[0].alpha) == 26
			and int(layers[1].alpha) == 18
		),
		"The manifest keeps both source parallax speeds and alpha levels"
	)
	if image != null:
		var lit_pixels := 0
		for y in range(0, image.get_height(), 8):
			for x in range(0, image.get_width(), 8):
				if image.get_pixel(x, y).a > 0.0:
					lit_pixels += 1
		check.call(
			image.get_pixel(0, 0).a == 0.0 and lit_pixels > 50,
			"Fog stays translucent over the baked scene"
		)
	_check_fixture(check)


func _check_fixture(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "The source particle replay fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	var initial: Array = fixture.get("initial_particles", [])
	var particles: Array = []
	var valid := initial.size() == MenuAmbientLayout.PARTICLE_COUNT
	for entry in initial:
		if not entry is Dictionary:
			valid = false
			continue
		var particle: Dictionary = entry
		var kind := String(particle.get("kind", ""))
		var x := float(particle.get("x", -1.0))
		var y := float(particle.get("y", -1.0))
		var rgb: Array = particle.get("color", [])
		valid = valid and kind in ["ember", "arcane"]
		valid = valid and x >= 0.0 and x <= 1280.0 and y >= 0.0 and y <= 720.0
		valid = valid and rgb.size() == 3 and int(particle.get("size", 0)) in [1, 2, 3]
		valid = valid and float(particle.get("ph", -1.0)) >= 0.0
		particles.append(particle.duplicate(true))
	check.call(valid, "The seeded source initialization creates 64 bounded ember/arcane particles")
	if not valid:
		return

	var draw: Dictionary = fixture.get("draw", {})
	var first_three: Array = draw.get("first_three_particles", [])
	var draw_match := int(draw.get("fog_layers", 0)) == 2
	draw_match = draw_match and int(draw.get("particle_circle_ops", 0)) == 128
	draw_match = draw_match and first_three.size() == 6
	for index in range(mini(3, int(first_three.size() / 2))):
		var particle: Dictionary = particles[index]
		var alpha := MenuAmbientLayout.particle_alpha(particle, float(draw.get("tick", 0)))
		var rgb: Array = particle.color
		var position := [int(float(particle.x)), int(float(particle.y))]
		for ring in range(2):
			var operation: Dictionary = first_three[index * 2 + ring]
			var expected_radius := int(particle.size) * (2 if ring == 0 else 1)
			var expected_alpha := int(alpha / 4) if ring == 0 else alpha
			var center: Array = operation.get("center", [])
			var color: Array = operation.get("color", [])
			var expected_color := [int(rgb[0]), int(rgb[1]), int(rgb[2]), expected_alpha]
			draw_match = draw_match and operation.get("kind", "") == "circle"
			draw_match = draw_match and _same_integer_values(center, position)
			draw_match = draw_match and int(operation.get("radius", -1)) == expected_radius
			draw_match = draw_match and _same_integer_values(color, expected_color)
	check.call(
		draw_match, "The source draw oracle pins both glow circles for the first three particles"
	)

	var updates: Array = fixture.get("update_wrap_x", [])
	var snapshots: Dictionary = {}
	for snapshot in fixture.get("snapshots", []):
		snapshots[int(snapshot.tick)] = snapshot.particles
	var motion_match := updates.size() == 800
	for tick in range(updates.size()):
		_wrap_values = updates[tick]
		_wrap_index = 0
		var wraps := MenuAmbientLayout.advance(particles, 1.0, Callable(self, "_next_wrap_x"))
		motion_match = (
			motion_match and wraps == _wrap_values.size() and _wrap_index == _wrap_values.size()
		)
		var source_tick := tick + 1
		if snapshots.has(source_tick):
			motion_match = motion_match and _same_particles(particles, snapshots[source_tick])
	check.call(motion_match, "The GDScript particle motion and wrap RNG replay source ticks 1–800")
	check.call(
		(
			MenuAmbientLayout.fog_offset(60.0, 0.35, 1500) == 21
			and MenuAmbientLayout.fog_offset(60.0, 0.6, 1500) == 36
			and MenuAmbientLayout.fog_alpha(26, 0.0, 0) == 26
		),
		"Fog scroll and pulse use the source tick equations"
	)


func _next_wrap_x() -> float:
	if _wrap_index >= _wrap_values.size():
		return -1000.0
	var result := float(_wrap_values[_wrap_index])
	_wrap_index += 1
	return result


func _same_integer_values(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		if int(actual[index]) != int(expected[index]):
			return false
	return true


func _same_particles(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var left: Dictionary = actual[index]
		var right: Dictionary = expected[index]
		for key in ["kind", "size", "color", "alpha"]:
			if left.get(key) != right.get(key):
				return false
		for key in ["x", "y", "vx", "vy", "ph"]:
			if not is_equal_approx(float(left.get(key, 0.0)), float(right.get(key, 0.0))):
				return false
	return true


func run_scene(tree: SceneTree, menu: Node, check: Callable) -> void:
	var ambient := menu.get_node_or_null("Ambient") as Control
	check.call(ambient != null, "MainMenu owns a dedicated ambient overlay")
	if ambient == null:
		return
	check.call(
		ambient.mouse_filter == Control.MOUSE_FILTER_IGNORE, "Ambient art never blocks menu input"
	)
	var before := float(ambient.get("animation_time"))
	for _frame in range(4):
		await tree.process_frame
	check.call(
		float(ambient.get("animation_time")) > before,
		"Fog and particles advance on the menu timeline"
	)
	check.call(int(ambient.get("ambient_draws")) > 0, "The live menu overlay draws")
	check.call(int(ambient.get("fog_draws")) == 4, "Both fog layers draw two wrapped copies")
	check.call(
		int(ambient.get("particle_draws")) == MenuAmbientLayout.PARTICLE_COUNT,
		"All 64 source particles are live"
	)
