extends Node
## Scene adapter: changes to the simulation are consumed only on physics ticks.

const Battle = preload("res://scripts/combat/minion_battle.gd")
const Definition = preload("res://scripts/data/minion_definition.gd")
const DEFINITIONS: Array[Definition] = [
	preload("res://data/minions/goblin.tres"),
	preload("res://data/minions/orc.tres"),
	preload("res://data/minions/troll.tres"),
	preload("res://data/minions/undead.tres"),
	preload("res://data/minions/dark_rider.tres")
]

var world := Battle.new()
var selected_id := -1
var pending_wave := 0
var last_request_failed := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _physics_process(_delta: float) -> void:
	if pending_wave >= 0:
		last_request_failed = not world.spawn_wave(DEFINITIONS[pending_wave])
		pending_wave = -1
	world.step_tick()
	if world.get_unit(selected_id) == null:
		selected_id = -1


func request_wave(type_index: int) -> bool:
	if get_tree().paused or pending_wave >= 0:
		return false
	if type_index < 0 or type_index >= DEFINITIONS.size():
		return false
	if world.units.size() + 6 > Battle.MAX_UNITS:
		return false
	pending_wave = type_index
	last_request_failed = false
	return true


func cancel_pending_input() -> void:
	pending_wave = -1
