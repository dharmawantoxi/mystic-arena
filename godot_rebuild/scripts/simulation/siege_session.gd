extends "res://scripts/simulation/combat_session.gd"

const Siege = preload("res://scripts/combat/siege_battle.gd")
var pending_team_mode := -1


func _init() -> void:
	world = Siege.new()


func _ready() -> void:
	super._ready()
	(world as Siege).setup_arena()


func _physics_process(_delta: float) -> void:
	if not world.is_running():
		cancel_pending_input()
		return
	if pending_wave >= 0:
		last_request_failed = not (world as Siege).spawn_assault_wave(
			DEFINITIONS[pending_wave], pending_team_mode
		)
		pending_wave = -1
	world.step_tick()
	if world.get_unit(selected_id) == null:
		selected_id = -1


func request_wave(type_index: int) -> bool:
	return request_assault(type_index, -1)


func request_assault(type_index: int, team_mode: int) -> bool:
	if get_tree().paused or not world.is_running() or pending_wave >= 0:
		return false
	if type_index < 0 or type_index >= DEFINITIONS.size() or team_mode not in [-1, 0, 1]:
		return false
	var count := 6 if team_mode == -1 else 3
	if world.units.size() + count > Siege.MAX_UNITS:
		return false
	pending_wave = type_index
	pending_team_mode = team_mode
	last_request_failed = false
	return true


func cancel_pending_input() -> void:
	super.cancel_pending_input()
	pending_team_mode = -1
