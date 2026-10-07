extends RefCounted
## Safe access to the AudioManager autoload from both normal scenes and the
## headless `--script` test runner, where project autoload names are NOT global
## identifiers. A domain script that names `AudioManager` directly fails to load
## in that runner, and every inner class extending it silently degrades to
## RefCounted (the native suite then crashes in `_super_implicit_constructor`).
## Gameplay code calls `AudioRuntime.play(key)`; the real facade keeps owning
## streams, volumes and the enabled flag.


static func play(key: String) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return
	var manager: Node = tree.root.get_node_or_null("AudioManager")
	if manager != null and manager.has_method("play"):
		manager.call("play", key)
