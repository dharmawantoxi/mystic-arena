extends RefCounted

const Playable = preload("res://scenes/prototype/PrototypeMatch.tscn")
const Runtime = preload("res://scripts/simulation/game_speed_runtime.gd")
const Session = preload("res://scripts/simulation/prototype_session.gd")
const Store = preload("res://scripts/simulation/game_speed_store.gd")


func run(tree: SceneTree, check: Callable) -> void:
	var baseline_nodes := tree.get_node_count()
	var speed_runtime: Runtime = tree.root.get_node("GameSpeed")
	var old_speed: float = speed_runtime.speed
	var old_path: String = speed_runtime.settings_path
	var test_path := "user://game_speed_scene_%d.json" % Time.get_ticks_usec()
	speed_runtime.settings_path = test_path
	speed_runtime.set_speed(1.0)
	speed_runtime.reset_match_clock()

	var screen = Playable.instantiate()
	var session: Session = screen.get_node("Simulation")
	session.set_physics_process(false)
	tree.root.add_child(screen)
	await tree.process_frame
	var selector: OptionButton = screen.get_node("%GameSpeedSelector")
	var world = session.world
	check.call(selector.item_count == 4, "playable match exposes all source speed presets")
	check.call(selector.get_item_text(0) == "0.5x", "playable speed selector shows half speed")
	check.call(selector.get_item_text(3) == "2.0x", "playable speed selector shows double speed")

	selector.select(3)
	selector.item_selected.emit(3)
	check.call(speed_runtime.speed == 2.0, "scene selection applies 2x speed")
	check.call(Store.load_speed(test_path) == 2.0, "scene selection persists the global preference")
	var before := int(world.tick_count)
	session._physics_process(1.0 / 60.0)
	check.call(
		int(world.tick_count) - before == 2, "2x advances two authoritative simulation ticks"
	)

	selector.select(0)
	selector.item_selected.emit(0)
	speed_runtime.reset_match_clock()
	before = int(world.tick_count)
	session._physics_process(1.0 / 60.0)
	session._physics_process(1.0 / 60.0)
	check.call(int(world.tick_count) - before == 1, "0.5x advances one tick per two physics frames")

	selector.select(2)
	selector.item_selected.emit(2)
	before = int(world.tick_count)
	session._physics_process(1.0 / 60.0)
	check.call(
		int(world.tick_count) - before == 1,
		"source 1.5x integer-truncation behavior stays one tick"
	)
	check.call(selector.selected == 2, "speed selector remains synchronized with runtime")

	screen.queue_free()
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	check.call(tree.get_node_count() == baseline_nodes, "speed scene frees all match nodes")
	speed_runtime.speed = old_speed
	speed_runtime.settings_path = old_path
	speed_runtime.reset_match_clock()
	_remove(test_path)
	_remove(test_path + ".tmp")
	_remove(test_path + ".bak")


func _remove(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
