extends "res://scripts/simulation/combat_session.gd"

const Structure = preload("res://scripts/combat/structure_state.gd")
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
		var balance_before: int = match_world.economy.gold[0]
		if command.kind == "build":
			accepted = match_world.build_tower(0, command.id)
			if accepted and selected_slot_id == command.id:
				selected_id = match_world.get_slot(command.id).structure_id
		elif command.kind == "upgrade":
			accepted = match_world.upgrade_tower(
				command.id, command.level, command.get("path", "archer")
			)
		elif command.kind == "nexus":
			accepted = match_world.upgrade_nexus(command.id, command.level)
		elif command.kind == "skill_q":
			accepted = match_world.cast_blue_q(command.id)
		elif command.kind == "skill_w":
			accepted = match_world._cast_blue_w(command.id)
		elif command.kind == "skill_e":
			accepted = match_world._cast_blue_e(command.id)
		elif command.kind == "skill_r":
			accepted = match_world._cast_blue_r(command.id)
		elif command.kind == "move":
			accepted = match_world.set_hero_destination(command.id, command.point)
		elif command.kind == "follow":
			accepted = match_world._set_hero_follow(command.id, command.target_id)
		else:
			accepted = match_world.sell_tower(0, command.id)
			if accepted and selected_id == command.id:
				selected_id = -1
		if accepted:
			if command.kind == "skill_q":
				last_action = "Kaizen memakai Steel Wind (Q)."
			elif command.kind == "skill_w":
				last_action = "Kaizen memakai Wind Wall (W)."
			elif command.kind == "skill_e":
				last_action = "Kaizen memakai Sweep (E)."
			elif command.kind == "skill_r":
				last_action = "Kaizen memakai Tornado (R)."
			elif command.kind == "move":
				last_action = "Kaizen menuju titik yang dipilih."
			elif command.kind == "follow":
				last_action = "Kaizen mengikuti musuh."
			else:
				var delta_gold: int = match_world.economy.gold[0] - balance_before
				var upgrade_label := "Archer ditingkatkan"
				if command.get("path") == "cannon":
					upgrade_label = "Cannon ditingkatkan"
				elif command.get("path") == "ice":
					upgrade_label = "Ice ditingkatkan"
				elif command.get("path") == "mage":
					upgrade_label = "Mage ditingkatkan"
				var action: String = {
					"build": "Archer dibangun",
					"sell": "Tower dijual",
					"upgrade": upgrade_label,
					"nexus": "Nexus ditingkatkan"
				}[command.kind]
				last_action = "%s: %+d G." % [action, delta_gold]
		else:
			var max_text := "Tower sudah level maksimum (6)."
			var stale_text := "Level tower sudah berubah; pilih upgrade kembali."
			if command.kind == "nexus":
				max_text = "Nexus sudah level maksimum (5)."
				stale_text = "Level nexus sudah berubah; pilih upgrade kembali."
			last_action = (
				{
					"finished": "Pertandingan sudah selesai.",
					"owner": "Pilih slot atau tower biru yang masih hidup.",
					"occupied": "Slot sudah terisi.",
					"gold": "Gold tidak cukup untuk transaksi ini.",
					"capacity": "Batas bangunan tercapai.",
					"stale": stale_text,
					"path": "Pilih jalur upgrade yang valid.",
					"max_level": max_text,
					"skill": "Q tidak siap atau tidak ada target."
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


func request_upgrade(entity_id: int, target_path: String = "archer") -> bool:
	var tower := world.get_unit(entity_id) as Structure
	if tower == null or not _queue("upgrade", entity_id):
		return false
	command.level = tower.settings().level
	command.path = target_path
	return true


func request_nexus_upgrade(entity_id: int) -> bool:
	var nexus := world.get_unit(entity_id) as Structure
	if nexus == null or not _queue("nexus", entity_id):
		return false
	command.level = nexus.settings().level
	return true


func request_skill_q(entity_id: int) -> bool:
	return _queue("skill_q", entity_id)


func request_skill_w(entity_id: int) -> bool:
	return _queue("skill_w", entity_id)


func request_skill_e(entity_id: int) -> bool:
	return _queue("skill_e", entity_id)


func request_skill_r(entity_id: int) -> bool:
	return _queue("skill_r", entity_id)


func request_hero_move(entity_id: int, point: Vector2) -> bool:
	if not _queue("move", entity_id):
		return false
	command.point = point
	return true


func request_hero_follow(entity_id: int, target_id: int) -> bool:
	if not _queue("follow", entity_id):
		return false
	command.target_id = target_id
	return true


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
