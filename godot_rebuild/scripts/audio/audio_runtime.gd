extends RefCounted
## Safe access to the AudioManager autoload from both normal scenes and the
## headless --script test runner, where project autoload names are not globals.


static func play(key: String) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return
	var manager: Node = tree.root.get_node_or_null("AudioManager")
	if manager != null and manager.has_method("play"):
		manager.call("play", key)
