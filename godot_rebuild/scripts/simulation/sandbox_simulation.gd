extends Node
## A test probe, NOT a migrated hero. All movement belongs to the fixed tick.

const SPAWN := Vector2(220, 530)
const SPEED_PX_PER_TICK := 3.0
const WORLD_BOUNDS := Rect2(65, 130, 1150, 470)

var tick_count := 0
var probe_position := SPAWN
var move_target := SPAWN
var has_move_target := false
var is_selected := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _physics_process(_delta: float) -> void:
	step_tick()


func step_tick() -> void:
	tick_count += 1
	if not has_move_target:
		return
	probe_position = probe_position.move_toward(move_target, SPEED_PX_PER_TICK)
	if probe_position.is_equal_approx(move_target):
		has_move_target = false


func select_at(point: Vector2) -> void:
	is_selected = probe_position.distance_to(point) <= 32.0


func command_move(point: Vector2) -> bool:
	if not is_selected or not WORLD_BOUNDS.has_point(point):
		return false
	move_target = point
	has_move_target = not probe_position.is_equal_approx(point)
	return true


func cancel_pending_input() -> void:
	# Explicit pause/background policy for this sandbox: stop the pending move.
	has_move_target = false
	move_target = probe_position
