extends Node
## Applies adaptive quality targets to the live render-FPS limiter.

signal quality_changed(level: String, target_fps: int)

const Controller = preload("res://scripts/settings/adaptive_quality_controller.gd")
const LOW_TARGET_FPS := 30
const NORMAL_TARGET_FPS := 60

var controller = Controller.new()
var quality_level := Controller.HIGH
var target_fps := NORMAL_TARGET_FPS
var touch_mode := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	touch_mode = OS.has_feature("android")
	controller.configure(Controller.LOW if touch_mode else Controller.HIGH)
	_apply_quality()


func _process(_delta: float) -> void:
	update_fps(Engine.get_frames_per_second())


func update_fps(fps: float) -> void:
	var previous_level: String = controller.level
	controller.update(fps)
	if controller.level != previous_level:
		_apply_quality()


func apply_quality(level: String) -> bool:
	if level not in [Controller.LOW, Controller.MEDIUM, Controller.HIGH]:
		return false
	controller.level = level
	_apply_quality()
	return true


func _apply_quality() -> void:
	quality_level = controller.level
	target_fps = LOW_TARGET_FPS if quality_level == Controller.LOW else NORMAL_TARGET_FPS
	var tree := Engine.get_main_loop() as SceneTree
	if tree != null and tree.root != null:
		var frame_limiter := tree.root.get_node_or_null("FrameRateLimit")
		if frame_limiter != null:
			frame_limiter.call("set_quality_target_fps", target_fps)
	quality_changed.emit(quality_level, target_fps)
