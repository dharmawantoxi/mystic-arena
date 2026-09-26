extends "res://scripts/combat/siege_battle.gd"
## Playable normal/level-1 subset. Wave/ledger/build rules are separate from the old manual labs.

const Upgrades = preload("res://scripts/match/archer_upgrades.gd")
const CannonUpgrades = preload("res://scripts/match/cannon_upgrades.gd")
const IceUpgrades = preload("res://scripts/match/ice_upgrades.gd")
const MageUpgrades = preload("res://scripts/match/mage_upgrades.gd")
const NexusUpgrades = preload("res://scripts/match/nexus_upgrades.gd")
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
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const HERO_SPAWN := Vector2(220, 540)

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
	# Kaizen-1 only: one free blue hero. Not a catalog purchase.
	spawn_hero(KAIZEN, BLUE, HERO_SPAWN)
	return true


func spawn_wave(_definition: Definition) -> bool:
	return false  # The scheduler, not a lab button, owns waves here.


func spawn_assault_wave(_definition: Definition, _team_mode: int) -> bool:
	return false


func spawn_unit(definition: Definition, team: int, lane: int) -> UnitState:
	if team not in [BLUE, RED]:
		return super.spawn_unit(definition, team, lane)
	var current := nexus_level(team)
	if current <= 1:
		var plain := super.spawn_unit(definition, team, lane)
		if plain != null:
			plain.ai_level = 1
		return plain
	var scaled := scaled_minion_definition(definition, current)
	if scaled == null:
		return null
	var unit := super.spawn_unit(scaled, team, lane)
	if unit != null:
		unit.ai_level = NexusUpgrades.MINION_AI[current - 1]
	return unit


func scaled_minion_definition(base: Definition, nexus_level: int) -> Definition:
	if base == null or nexus_level <= 1:
		return base
	if nexus_level < 1 or nexus_level > NexusUpgrades.MINION_SCALES.size():
		return null
	var scale: float = NexusUpgrades.MINION_SCALES[nexus_level - 1]
	var copy := base.duplicate() as Definition
	copy.max_hp = int(base.max_hp * scale)
	copy.damage = int(base.damage * scale)
	copy.speed_px_per_tick = base.speed_px_per_tick * (1.0 + (scale - 1.0) * 0.3)
	var haste := 1.0 + (scale - 1.0) * 0.2
	copy.attack_cooldown_ticks = maxi(10, int(base.attack_cooldown_ticks / haste))
	copy.gold_reward = int(base.gold_reward * scale)
	copy.regen_per_tick = base.regen_per_tick * scale
	return copy


func nexus_level(team: int) -> int:
	if team not in [BLUE, RED] or nexuses[team] == null:
		return 1
	return nexuses[team].settings().level


func step_tick() -> void:
	if not is_running():
		return
	# Input transactions are handled by the session before this method.
	economy.step_tick(wave_count)
	# Source wave gate ignores heroes; only living minions hold the field.
	var field_clear := living_minion_count() == 0
	var batch := scheduler.step_tick(
		field_clear, MAX_UNITS - units.size(), nexus_level(BLUE), nexus_level(RED)
	)
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


func upgrade_price(entity_id: int, target_path: String = "archer") -> int:
	var tower := _owned_tower(entity_id)
	if tower == null:
		return 0
	var level: int = tower.settings().level
	var path_now: String = tower.settings().tower_path
	var target: StructureDefinition = _upgrade_target(level, path_now, target_path)
	return target.upgrade_price if target != null else 0


func upgrade_tower(entity_id: int, expected_level: int, target_path: String = "archer") -> bool:
	transaction_error = ""
	var tower := _owned_tower(entity_id)
	var target: StructureDefinition = null
	if tower != null:
		target = _upgrade_target(tower.settings().level, tower.settings().tower_path, target_path)
	var cost := target.upgrade_price if target != null else 0
	if not is_running():
		transaction_error = "finished"
	elif tower == null:
		transaction_error = "owner"
	elif tower.settings().level != expected_level:
		transaction_error = "stale"
	elif tower.settings().level == 1 and target == null:
		transaction_error = "path"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[BLUE] < cost:
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# Source resets HP/shield fully but retains cooldown, target, regen timer and in-flight shots.
	economy.spend(BLUE, cost)
	tower.definition = target
	tower.hp = tower.definition.max_hp
	tower.shield_max = tower.settings().shield_capacity
	tower.shield = tower.settings().shield_capacity
	_record({"kind": "upgrade", "target_id": tower.id, "level": tower.settings().level})
	return true


func _upgrade_target(current: int, current_path: String, target_path: String):
	# Source: level 1 requires an explicit valid path; later levels ignore
	# the argument and keep their path. Cannon, Ice and Mage start at level 2.
	if current < 1 or current >= 6:
		return null
	var path := current_path
	if current == 1:
		if target_path not in ["archer", "cannon", "ice", "mage"]:
			return null
		path = target_path
	if path == "cannon":
		return CannonUpgrades.LEVELS.get(current + 1) as StructureDefinition
	if path == "ice":
		return IceUpgrades.LEVELS.get(current + 1) as StructureDefinition
	if path == "mage":
		return MageUpgrades.LEVELS.get(current + 1) as StructureDefinition
	return Upgrades.LEVELS[current] as StructureDefinition


func nexus_upgrade_price(entity_id: int) -> int:
	var nexus := _owned_nexus(entity_id)
	if nexus == null or nexus.settings().level >= NexusUpgrades.LEVELS.size():
		return 0
	return NexusUpgrades.LEVELS[nexus.settings().level].upgrade_price


func upgrade_nexus(entity_id: int, expected_level: int) -> bool:
	transaction_error = ""
	var nexus := _owned_nexus(entity_id)
	var cost := nexus_upgrade_price(entity_id)
	if not is_running():
		transaction_error = "finished"
	elif nexus == null:
		transaction_error = "owner"
	elif nexus.settings().level != expected_level:
		transaction_error = "stale"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[BLUE] < cost:
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	economy.spend(BLUE, cost)
	var old_max: int = nexus.definition.max_hp
	var old_hp: float = nexus.hp
	var target = NexusUpgrades.LEVELS[expected_level]
	var new_max: int = target.max_hp
	var ratio := old_hp / float(old_max)
	var healed := int(new_max * ratio) + (new_max - old_max)
	nexus.definition = target
	nexus.hp = mini(new_max, healed + 500)
	if nexus.castle_shield_purchased:
		var old_shield_max := maxf(1.0, nexus.shield_max)
		var shield_ratio := clampf(nexus.shield / old_shield_max, 0.0, 1.0)
		nexus.shield_max = target.shield_capacity
		nexus.shield = int(nexus.shield_max * shield_ratio)
	_record({"kind": "nexus_upgrade", "target_id": nexus.id, "level": nexus.settings().level})
	return true


func _owned_nexus(entity_id: int) -> StructureState:
	var nexus := get_unit(entity_id) as StructureState
	if nexus == null or not nexus.alive or nexus.team != BLUE:
		return null
	if nexus.settings().structure_kind != "nexus":
		return null
	if nexuses[BLUE] == null or nexuses[BLUE].id != entity_id:
		return null
	return nexus


func _owned_tower(entity_id: int) -> StructureState:
	var tower := get_unit(entity_id) as StructureState
	if tower == null or not tower.alive or tower.team != BLUE:
		return null
	if tower.settings().structure_kind != "tower":
		return null
	for slot in slots:
		if slot.team == BLUE and slot.structure_id == entity_id:
			return tower
	return null


func blue_hero() -> HeroState:
	for unit in units:
		if unit.is_hero and unit.team == BLUE:
			return unit as HeroState
	return null


func cast_blue_q(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not cast_hero_q(hero.id, structures):
		transaction_error = "skill"
		return false
	_record({"kind": "skill_q", "target_id": hero.id})
	return true
