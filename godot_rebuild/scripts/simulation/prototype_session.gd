extends "res://scripts/simulation/combat_session.gd"

const Structure = preload("res://scripts/combat/structure_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
## One seed for the whole red AI: a restarted prototype match replays.
const AI_MATCH_SEED := 20260929
## A press and its release can land inside one tick, so tactical input keeps its
## own ordered queue instead of the single-slot build/upgrade command.
const TACTICAL_QUEUE_LIMIT := 8
var selected_slot_id := -1
var command: Dictionary = {}
var tactical_queue: Array[Dictionary] = []
var mouse_position := Vector2.ZERO
var last_action := "Pilih slot biru, lalu bangun Archer (100 G)."


func _init() -> void:
	world = Prototype.new()
	pending_wave = -1


## Selection must happen before the node enters the tree (_ready sets up the
## arena). The public playable menu deliberately still creates level 1.
func configure_level(number: int, target_difficulty: String = "normal") -> bool:
	if not (world as Prototype).configure_level(number):
		return false
	(world as Prototype).set_difficulty(target_difficulty)
	return true


func _ready() -> void:
	super._ready()
	var match_world := world as Prototype
	match_world.setup_arena()
	# Layer 6d: the real AI owns the red side in the scene (layer 6e removed the
	# temporary defender) and every AI stream is seeded, so the match is
	# reproducible.
	match_world.reset_ai(AI_MATCH_SEED)
	match_world.set_ai_enabled(true)


func _physics_process(_delta: float) -> void:
	if not world.is_running():
		cancel_pending_input()
		return
	var match_world := world as Prototype
	match_world.set_tactical_mouse(mouse_position)
	_drain_tactical(match_world)
	if not command.is_empty():
		var accepted := false
		var balance_before: int = match_world.economy.gold[0]
		var autocast_was_on := false
		if command.kind == "autocast":
			var caster := match_world.get_unit(command.id) as HeroState
			autocast_was_on = caster != null and caster.auto_cast_enabled
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
		elif command.kind == "hero_upgrade":
			accepted = match_world._upgrade_blue_hero(command.id, command.level)
		elif command.kind == "autocast":
			accepted = match_world._set_hero_autocast(command.id)
		elif command.kind == "move":
			accepted = match_world.set_hero_destination(command.id, command.point)
		elif command.kind == "follow":
			accepted = match_world._set_hero_follow(command.id, command.target_id)
		else:
			accepted = match_world.sell_tower(0, command.id)
			if accepted and selected_id == command.id:
				selected_id = -1
		if accepted:
			var delta_gold: int = match_world.economy.gold[0] - balance_before
			if command.kind == "skill_q":
				last_action = "Kaizen memakai Steel Wind (Q)."
			elif command.kind == "skill_w":
				last_action = "Kaizen memakai Wind Wall (W)."
			elif command.kind == "skill_e":
				last_action = "Kaizen memakai Sweep (E)."
			elif command.kind == "skill_r":
				last_action = "Kaizen memakai Tornado (R)."
			elif command.kind == "hero_upgrade":
				last_action = "Kaizen naik level: %+d G." % delta_gold
			elif command.kind == "autocast":
				last_action = (
					"Auto-cast diaktifkan." if not autocast_was_on else "Auto-cast sudah aktif."
				)
			elif command.kind == "move":
				last_action = "Kaizen menuju titik yang dipilih."
			elif command.kind == "follow":
				last_action = "Kaizen mengikuti musuh."
			else:
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
			if command.kind == "hero_upgrade":
				max_text = "Hero sudah level maksimum (15)."
				stale_text = "Level hero sudah berubah; pilih upgrade kembali."
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


func request_autocast(entity_id: int) -> bool:
	# Source v29: pressing can only force auto-cast ON (no off path).
	return _queue("autocast", entity_id)


func request_hero_upgrade(entity_id: int) -> bool:
	var match_world := world as Prototype
	var hero: HeroState = match_world.blue_hero()
	if hero == null or hero.id != entity_id or not _queue("hero_upgrade", entity_id):
		return false
	command.level = hero.level
	return true


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


func request_tactical_hold(
	command_name: String,
	point: Vector2 = Vector2.ZERO,
	has_point: bool = false,
	follow_mouse: bool = false
) -> bool:
	## Port of the KEYDOWN / panel-press path (`_core.py::handle_key`,
	## `mobile/hud.py::apply_hud_action`): the order is issued through
	## `hold_start`, so it stays enforced until the key or finger is released.
	if not _tactical_gate():
		return false
	(
		tactical_queue
		. append(
			{
				"kind": "hold",
				"command": command_name,
				"point": point,
				"has_point": has_point,
				"tower_id": _selected_blue_tower_id(),
				"follow_mouse": follow_mouse,
			}
		)
	)
	return true


func request_tactical_release(command_name: String = "") -> bool:
	## Port of KEYUP / touch release -> `tactical.hold_end(name)`.
	if not _tactical_gate():
		return false
	tactical_queue.append({"kind": "release", "command": command_name})
	return true


func set_mouse_position(point: Vector2) -> void:
	mouse_position = point


func _tactical_gate() -> bool:
	# Tactical input is match input: it is refused while paused or finished, and
	# `cancel_pending_input()` releases the holds like `main.py` does on pause.
	if get_tree().paused or not world.is_running():
		return false
	return tactical_queue.size() < TACTICAL_QUEUE_LIMIT


func _selected_blue_tower_id() -> int:
	# `_core.py` passes `g.selected_tower` to PROTECT TOWER only when it is blue.
	var tower := world.get_unit(selected_id) as Structure
	if tower == null or not tower.alive or tower.team != 0:
		return -1
	if tower.settings().structure_kind != "tower":
		return -1
	return tower.id


func _drain_tactical(match_world: Prototype) -> void:
	# Source dispatches tactical input before `Game.update`, so the queue runs
	# before the tick and before the single-slot build/upgrade command.
	for entry in tactical_queue:
		if String(entry.kind) == "hold":
			match_world.tactical_hold(
				String(entry.command),
				entry.point,
				bool(entry.has_point),
				int(entry.tower_id),
				bool(entry.follow_mouse),
				selected_id
			)
			if match_world.tactical.active_command == String(entry.command):
				last_action = match_world.tactical.status_text()
			else:
				# Armed but refused (no boss / no tower / cooldown): the source
				# reports it through the feedback banner, the HUD echoes it.
				last_action = "Perintah %s belum bisa diterbitkan." % String(entry.command)
		else:
			match_world.tactical_release(String(entry.command))
	tactical_queue.clear()


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
	tactical_queue.clear()
	# `main.py` releases every held order when it pauses or backgrounds, so a
	# hold can never survive the pause overlay and re-fire on resume.
	(world as Prototype).tactical.hold_end()


func _queue(kind: String, id: int) -> bool:
	if get_tree().paused or not world.is_running() or not command.is_empty() or id < 0:
		return false
	# Capture the ID, not a mutable selection reference. Revalidate at execution time.
	command = {"kind": kind, "id": id}
	return true
