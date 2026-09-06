class_name CameraRig
extends Camera2D
## Smooth-follow camera that adds screen-shake on demand.
##
## Reads [member GameFeel.get_shake_offset] every frame and applies it as a
## small offset on top of the smooth-follow position. The shake decays
## naturally through the [GameFeel] autoload.

@export var follow_speed: float = 8.0
@export var look_ahead: float = 60.0

## Target to follow (usually the player).
var target: Node2D = null

## Smoothed position.
var _smooth_pos: Vector2 = Vector2.ZERO


func _ready() -> void:
	_smooth_pos = global_position if target == null else target.global_position
	# Read flash requests from the game-feel singleton.
	GameFeel.flash_requested.connect(_on_flash_requested)


func _process(delta: float) -> void:
	if target == null or not is_instance_valid(target):
		return
	# Look-ahead: shift the camera slightly in the direction the target is
	# facing, so the player can see more of what's in front of them.
	var facing := Vector2(1, 0)
	if target.has_method("get") and target.get("facing") != null:
		facing.x = float(target.get("facing"))
	var desired := target.global_position + facing * look_ahead
	_smooth_pos = _smooth_pos.lerp(desired, clampf(follow_speed * delta, 0.0, 1.0))
	var shake := GameFeel.get_shake_offset()
	global_position = _smooth_pos + shake


func _on_flash_requested(color: Color, duration: float) -> void:
	# A simple overlay flash using a CanvasLayer. We instantiate a one-shot
	# ColorRect that fades out.
	var layer := CanvasLayer.new()
	layer.layer = 100
	get_tree().current_scene.add_child(layer)
	var rect := ColorRect.new()
	rect.color = color
	rect.anchor_right = 1.0
	rect.anchor_bottom = 1.0
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(rect)
	var tween := create_tween()
	tween.tween_property(rect, "color:a", 0.0, duration)
	tween.tween_callback(func ():
		layer.queue_free())
