extends RefCounted
## Safe access to the AudioManager autoload from both normal scenes and the
## headless --script test runner, where project autoload names are not globals.


static func _manager() -> Node:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return null
	return tree.root.get_node_or_null("AudioManager")


static func play(key: String) -> void:
	var manager := _manager()
	if manager != null and manager.has_method("play"):
		manager.call("play", key)


static func get_volume(channel: String) -> float:
	var manager := _manager()
	if manager == null or not manager.has_method("get_volume"):
		return -1.0
	return float(manager.call("get_volume", channel))


static func adjust_volume(channel: String, delta: float) -> bool:
	var manager := _manager()
	if manager == null or not manager.has_method("adjust_volume"):
		return false
	return bool(manager.call("adjust_volume", channel, delta))
