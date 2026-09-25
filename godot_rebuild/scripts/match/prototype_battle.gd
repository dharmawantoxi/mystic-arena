extends "res://scripts/combat/siege_battle.gd"
## Playable normal/level-1 subset. Wave/ledger/build rules are separate from the old manual labs.

const Upgrades = preload("res://scripts/match/archer_upgrades.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Scheduler = preload("res://scripts/match/wave_scheduler.gd")
const SlotLayout = preload("res://scripts/match/slot_layout.gd")
const Slot = preload("res://scripts/match/build_slot.gd")
const MINIONS := {
	"goblin": preload("res://data/minions/goblin.tres"),
	"orc": preload("res://data/minions/orc.tres"),
	"troll": preload("res://data/minions/troll.tres"),
	"undead": preload("res://data/minions/undead.tres"),
	"dark_rider": preload("res://data/minions/dark_rider.tres")
}

var economy := Economy.new()
var scheduler := Scheduler.new()
var slots: Array[Slot] = []
var transaction_error := ""
var defender_enabled := true
var _defender_built := 0


func _init() -> void:
	slots = SlotLayout.create(paths)


func structure_limit() -> int:
	return 20  # Nine slots per team plus two nexuses.


func setup_arena() -> bool:
	if _arena_initialized or not is_running() or not structures.is_empty() or not units.is_empty():
		return false
	_arena_initialized = true
	spawn_structure(NEXUS, BLUE, LaneLayout.BLUE_BASE)
	spawn_structure(NEXUS, RED, LaneLayout.RED_BASE)
	return true


func spawn_wave(_definition: Definition) -> bool:
	return false  # The scheduler, not a lab button, owns waves here.


func spawn_assault_wave(_definition: Definition, _team_mode: int) -> bool:
	return false


func step_tick() -> void:
	if not is_running():
		return
	# Input transactions are handled by the session before this method.
	economy.step_tick(wave_count)
	var field_clear := true
	for unit in units:
		if unit.alive:
			field_clear = false
			break
	var batch := scheduler.step_tick(field_clear, MAX_UNITS - units.size())
	wave_count = scheduler.wave
	if batch.started:
		for nexus in nexuses:
			if nexus != null:
				nexus.set_wave(wave_count)
	for spawn in batch.spawns:
		spawn_unit(MINIONS[spawn.kind], spawn.team, spawn.lane)
	super.step_tick()
	if is_running():
		_step_defender()


func get_slot(id: int) -> Slot:
	return slots[id] if id >= 0 and id < slots.size() else null


func slot_at(point: Vector2) -> int:
	var closest := -1
	var distance := 24.0
	for slot in slots:
		var candidate := point.distance_to(slot.position)
		if candidate < distance:
			closest = slot.id
			distance = candidate
	return closest


func build_tower(team: int, slot_id: int) -> bool:
	transaction_error = ""
	var slot := get_slot(slot_id)
	if not is_running() or team not in [BLUE, RED]:
		transaction_error = "finished"
	elif slot == null or slot.team != team:
		transaction_error = "owner"
	elif slot.structure_id != -1:
		transaction_error = "occupied"
	elif economy.gold[team] < Economy.BUILD_COST:
		transaction_error = "gold"
	elif structures.size() >= structure_limit():
		transaction_error = "capacity"
	if not transaction_error.is_empty():
		return false
	var tower := spawn_structure(ARCHER, team, slot.position, slot.lane)
	if tower == null:
		transaction_error = "capacity"
		return false
	# No callbacks/await occur between validation and debit. Never put a side effect in assert().
	economy.spend(team, Economy.BUILD_COST)
	slot.structure_id = tower.id
	_record({"kind": "build", "team": team, "slot_id": slot.id, "target_id": tower.id})
	return true


func sell_tower(team: int, entity_id: int) -> bool:
	transaction_error = ""
	var tower := get_unit(entity_id) as StructureState
	var slot: Slot = null
	for candidate in slots:
		if candidate.structure_id == entity_id:
			slot = candidate
	if not is_running():
		transaction_error = "finished"
	elif team != BLUE or tower == null or not tower.alive or tower.team != team:
		transaction_error = "owner"
	elif tower.settings().structure_kind != "tower" or slot == null or slot.team != team:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	# Selling is NOT a death: no kill event, enemy credit, or death rewards.
	tower.alive = false
	_retire_dead()
	var flying: Array[Projectile] = []
	for shot in projectiles:
		if shot.source_id == entity_id or shot.target_id == entity_id:
			shot.active = false
		else:
			flying.append(shot)
	projectiles = flying
	economy.credit_sale(team, tower.settings().sale_refund)
	_record({"kind": "sale", "team": team, "target_id": entity_id})
	return true


func _on_death(source_team: int, target: UnitState) -> void:
	var before := credited_gold[source_team]
	super._on_death(source_team, target)
	economy.credit_kill(source_team, credited_gold[source_team] - before)
	if not is_running():
		scheduler.cancel()


func _retire_dead() -> void:
	super._retire_dead()
	# Intentional fix: destroyed slots are released, not left permanently 'taken'.
	for slot in slots:
		var tower := get_unit(slot.structure_id)
		if tower == null or not tower.alive:
			slot.structure_id = -1


func _step_defender() -> void:
	# Explicit temporary opponent, NOT a port of AIPlayer: three paid Archer purchases.
	if not defender_enabled or _defender_built >= 3 or tick_count % 300 != 0:
		return
	if build_tower(RED, [11, 14, 17][_defender_built]):
		_defender_built += 1


func upgrade_price(entity_id: int) -> int:
	var tower := _owned_archer(entity_id)
	if tower == null or tower.settings().level >= Upgrades.LEVELS.size():
		return 0
	return Upgrades.LEVELS[tower.settings().level].upgrade_price


func upgrade_tower(entity_id: int, expected_level: int) -> bool:
	transaction_error = ""
	var tower := _owned_archer(entity_id)
	var cost := upgrade_price(entity_id)
	if not is_running():
		transaction_error = "finished"
	elif tower == null:
		transaction_error = "owner"
	elif tower.settings().level != expected_level:
		transaction_error = "stale"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[BLUE] < cost:
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# Source resets HP/shield fully but retains cooldown, target, regen timer and in-flight shots.
	economy.spend(BLUE, cost)
	tower.definition = Upgrades.LEVELS[expected_level]
	tower.hp = tower.definition.max_hp
	tower.shield = tower.settings().shield_capacity
	_record({"kind": "upgrade", "target_id": tower.id, "level": tower.settings().level})
	return true


func _owned_archer(entity_id: int) -> StructureState:
	var tower := get_unit(entity_id) as StructureState
	if tower == null or not tower.alive or tower.team != BLUE:
		return null
	if tower.settings().structure_kind != "tower":
		return null
	for slot in slots:
		if slot.team == BLUE and slot.structure_id == entity_id:
			return tower
	return null
