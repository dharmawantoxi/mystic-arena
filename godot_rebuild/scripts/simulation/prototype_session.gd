extends "res://scripts/simulation/combat_session.gd"

const Prototype = preload("res://scripts/match/prototype_battle.gd")
var selected_slot_id := -1
var command: Dictionary = {}
var last_action := "Pilih slot biru, lalu bangun Archer (100 G)."


func _init() -> void:
	world = Prototype.new()
	pending_wave = -1


func _ready() -> void:
	super._ready()
	(world as Prototype).setup_arena()


func _physics_process(_delta: float) -> void:
	if not world.is_running():
		cancel_pending_input()
		return
	var match_world := world as Prototype
	if not command.is_empty():
		var accepted := false
		if command.kind == "build":
			accepted = match_world.build_tower(0, command.id)
			if accepted and selected_slot_id == command.id:
				selected_id = match_world.get_slot(command.id).structure_id
		else:
			accepted = match_world.sell_tower(0, command.id)
			if accepted and selected_id == command.id:
				selected_id = -1
		if accepted:
			last_action = (
				"Archer dibangun: −100 G." if command.kind == "build" else "Tower dijual: +50 G."
			)
		else:
			last_action = (
				{
					"finished": "Pertandingan sudah selesai.",
					"owner": "Pilih slot atau tower biru yang masih hidup.",
					"occupied": "Slot sudah terisi.",
					"gold": "Gold tidak cukup: Archer membutuhkan 100 G.",
					"capacity": "Batas bangunan tercapai."
				}
				. get(match_world.transaction_error, "Transaksi ditolak.")
			)
		command.clear()
	world.step_tick()
	if world.get_unit(selected_id) == null:
		selected_id = -1


func request_build(slot_id: int) -> bool:
	return _queue("build", slot_id)


func request_sell(entity_id: int) -> bool:
	return _queue("sell", entity_id)


func request_wave(_type_index: int) -> bool:
	return false


func select_at(point: Vector2) -> void:
	var match_world := world as Prototype
	selected_slot_id = match_world.slot_at(point)
	if selected_slot_id != -1:
		selected_id = match_world.get_slot(selected_slot_id).structure_id
	else:
		selected_id = world.select_at(point)


func cancel_pending_input() -> void:
	super.cancel_pending_input()
	command.clear()


func _queue(kind: String, id: int) -> bool:
	if get_tree().paused or not world.is_running() or not command.is_empty() or id < 0:
		return false
	# Capture the ID, not a mutable selection reference. Revalidate at execution time.
	command = {"kind": kind, "id": id}
	return true
