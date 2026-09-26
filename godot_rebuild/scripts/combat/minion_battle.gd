extends RefCounted
## Deterministic tier-1 minion combat lab. No Nodes, rendering, wall clock, or RNG.
## Sequential attacks resolve in stable spawn-ID order; a killed unit cannot act later that tick.

const Definition = preload("res://scripts/data/minion_definition.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const LaneLayout = preload("res://scripts/data/lane_layout.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const MAX_UNITS := 120
const MAX_EVENTS := 64
const BLUE := 0
const RED := 1

var paths: Array[PackedVector2Array] = LaneLayout.create_paths()
var units: Array[UnitState] = []
var tick_count := 0
var wave_count := 0
var kills: Array[int] = [0, 0]
var escaped: Array[int] = [0, 0]
# Audit counters only; this is NOT persistent player currency.
var credited_gold: Array[int] = [0, 0]
var recent_events: Array[Dictionary] = []
var _by_id: Dictionary = {}
var _next_id := 1


func spawn_unit(definition: Definition, team: int, lane: int) -> UnitState:
	if not is_running() or definition == null or not definition.is_valid():
		return null
	if (
		definition.speed_px_per_tick <= 0
		or team not in [BLUE, RED]
		or lane < 0
		or lane >= paths.size()
	):
		return null
	if units.size() >= MAX_UNITS:
		return null
	var unit := UnitState.new()
	unit.id = _next_id
	_next_id += 1
	unit.team = team
	unit.lane = lane
	unit.definition = definition
	unit.hp = definition.max_hp
	unit.waypoint_index = 0 if team == BLUE else paths[lane].size() - 1
	unit.position = paths[lane][unit.waypoint_index]
	unit.position.y += [-20.0, 0.0, 20.0][lane]
	unit.facing = 1.0 if team == BLUE else -1.0
	units.append(unit)
	_by_id[unit.id] = unit
	return unit


func spawn_wave(definition: Definition) -> bool:
	# Validate the whole request before modifying state: no half-spawned waves at the cap.
	if (
		not is_running()
		or definition == null
		or not definition.is_valid()
		or units.size() + 6 > MAX_UNITS
		or definition.speed_px_per_tick <= 0
	):
		return false
	for lane in range(3):
		spawn_unit(definition, BLUE, lane)
		spawn_unit(definition, RED, lane)
	wave_count += 1
	return true


func get_unit(id: int) -> UnitState:
	return _by_id.get(id) as UnitState


func is_running() -> bool:
	return true


func step_tick() -> void:
	if not is_running():
		return
	tick_count += 1
	for unit in units:
		if not is_running():
			break
		if not unit.alive:
			continue
		unit.cooldown_ticks = maxi(0, unit.cooldown_ticks - 1)
		_tick_burn(unit)
		if not unit.alive:
			continue
		unit.hp = minf(unit.definition.max_hp, unit.hp + unit.definition.regen_per_tick)
		var target := _find_target(unit)
		unit.target_id = target.id if target != null else -1
		if target == null:
			_follow_lane(unit)
		elif unit.position.distance_to(target.position) <= unit.definition.attack_range_px:
			if unit.cooldown_ticks == 0:
				apply_hit(unit.id, target.id)
		else:
			_move_toward(unit, target.position)
	_retire_dead()


func apply_hit(attacker_id: int, target_id: int, school: String = "physical") -> bool:
	var attacker := get_unit(attacker_id)
	var target := get_unit(target_id)
	if not is_running() or attacker == null or target == null:
		return false
	if not attacker.alive or not target.alive or attacker.cooldown_ticks > 0:
		return false
	if attacker.position.distance_to(target.position) > attacker.definition.attack_range_px:
		return false
	if not _deliver_hit(
		attacker.id, attacker.team, target, attacker.definition.damage, school, attacker.position
	):
		return false
	attacker.cooldown_ticks = attacker.definition.attack_cooldown_ticks
	attacker.facing = -1.0 if target.position.x < attacker.position.x else 1.0
	return true


func apply_burn(target_id: int, dps: float, duration: int, team: int) -> bool:
	# Port of TowerDebuffMixin.apply_debuff("burn"): structures have no
	# debuff API in the source, so only living enemy units accept burn.
	var target := get_unit(target_id)
	if not is_running() or target == null or target is StructureState:
		return false
	if not target.alive or target.team == team or dps <= 0 or duration <= 0:
		return false
	if target.burn_timer <= 0:
		target.burn_dps = dps
		target.burn_accum = 0.0
		target.burn_tick_cd = BURN_TICK_INTERVAL
	else:
		target.burn_dps = maxf(target.burn_dps, dps)
	target.burn_timer = maxi(target.burn_timer, duration)
	target.burn_team = team
	return true


func _tick_burn(unit: UnitState) -> void:
	# Port of the burn branch in _tick_tower_debuffs. Damage ticks every
	# 30 frames from a per-tick dps/60 accumulator with int truncation.
	# Credit follows the source victim-based rule: the victim's enemy.
	if unit.burn_timer <= 0:
		return
	unit.burn_timer -= 1
	unit.burn_accum += unit.burn_dps / BURN_TICKS_PER_SECOND
	unit.burn_tick_cd -= 1
	if unit.burn_tick_cd <= 0:
		unit.burn_tick_cd = BURN_TICK_INTERVAL
		var damage := int(unit.burn_accum)
		if damage > 0 and unit.alive:
			unit.burn_accum -= damage
			unit.hp = maxf(0, unit.hp - damage)
			_record(
				{
					"kind": "hit",
					"burn": true,
					"source_id": -1,
					"target_id": unit.id,
					"from": unit.position,
					"to": unit.position,
					"damage": damage
				}
			)
			if unit.hp <= 0:
				unit.alive = false
				_record({"kind": "death", "burn": true, "source_id": -1, "target_id": unit.id})
				_on_death(1 - unit.team, unit)
	if unit.burn_timer <= 0:
		unit.burn_dps = 0.0
		unit.burn_accum = 0.0


func _deliver_hit(
	source_id: int,
	source_team: int,
	target: UnitState,
	raw_damage: int,
	school: String,
	origin: Vector2
) -> bool:
	# Shared one-shot damage path for melee and projectile impacts. Visuals never call this.
	if not is_running() or target == null or not target.alive or source_team == target.team:
		return false
	if raw_damage <= 0 or school not in ["physical", "magic"]:
		return false
	var damage := _damage_amount(target, raw_damage, school)
	target.hp = maxf(0, target.hp - damage)
	_record(
		{
			"kind": "hit",
			"source_id": source_id,
			"target_id": target.id,
			"from": origin,
			"to": target.position,
			"damage": damage
		}
	)
	if target.hp <= 0:
		target.alive = false
		_record({"kind": "death", "source_id": source_id, "target_id": target.id})
		_on_death(source_team, target)
	return true


func _damage_amount(target: UnitState, raw_damage: int, school: String) -> float:
	return DamageRules.resolve(
		raw_damage, target.definition.armor, target.definition.magic_resist, school
	)


func _on_death(source_team: int, target: UnitState) -> void:
	kills[source_team] += 1
	credited_gold[source_team] += target.definition.gold_reward


func select_at(point: Vector2) -> int:
	var result := -1
	var best_distance := INF
	for unit in units:
		if not unit.alive:
			continue
		var distance := unit.position.distance_to(point)
		if distance <= maxf(20, unit.definition.radius_px + 8) and distance < best_distance:
			best_distance = distance
			result = unit.id
	return result


func _find_target(unit: UnitState) -> UnitState:
	var ordered: Array[UnitState] = []
	for candidate in units:
		if not candidate.alive or candidate.team == unit.team:
			continue
		ordered.append(candidate)
	return _select_ai_target(unit, ordered)


func _select_ai_target(unit: UnitState, ordered: Array[UnitState]) -> UnitState:
	# Port of Minion._find_target_smart 1-5. Stable ID order replaces the
	# spatial-hash order; ties keep the first candidate (strict < scans).
	var in_range: Array = []
	for candidate in ordered:
		var dist := unit.position.distance_to(candidate.position)
		if dist <= unit.definition.attack_range_px:
			in_range.append([candidate, dist])
	if in_range.is_empty():
		return _fallback_target(unit, ordered)
	var chosen: UnitState = null
	match unit.ai_level:
		2:
			chosen = _ai_same_lane(in_range, unit.lane)
		3:
			chosen = _lowest_hp(in_range)
		4:
			chosen = _ai_minion_or_nearest(in_range)
		5:
			chosen = _ai_siege_priority(in_range)
		_:
			chosen = _nearest(in_range)
	return chosen


func _fallback_target(unit: UnitState, ordered: Array[UnitState]) -> UnitState:
	var best: UnitState = null
	var best_dist := unit.definition.attack_range_px + 30.0
	for candidate in ordered:
		var dist := unit.position.distance_to(candidate.position)
		if dist < best_dist:
			best_dist = dist
			best = candidate
	return best


func _ai_same_lane(pairs: Array, lane: int) -> UnitState:
	for pair in pairs:
		var cand: UnitState = pair[0]
		if not (cand is StructureState) and cand.lane == lane:
			return cand
	return pairs[0][0] as UnitState


func _ai_minion_or_nearest(pairs: Array) -> UnitState:
	var minions: Array = []
	for pair in pairs:
		if not (pair[0] is StructureState):
			minions.append(pair)
	if not minions.is_empty():
		return _lowest_hp(minions)
	return _nearest(pairs)


func _ai_siege_priority(pairs: Array) -> UnitState:
	for pair in pairs:
		var cand: UnitState = pair[0]
		if cand.definition.max_hp >= 1500:
			return cand
	var towers: Array = []
	for pair in pairs:
		var cand := pair[0] as StructureState
		# Source checks hasattr(tower_kind), which Tower never sets;
		# observable behavior is identical because every tower is
		# already captured by the max_hp>=1500 branch above.
		if cand != null and cand.settings().structure_kind == "tower":
			towers.append(pair)
	if not towers.is_empty():
		return _lowest_hp(towers)
	var minions: Array = []
	for pair in pairs:
		if not (pair[0] is StructureState):
			minions.append(pair)
	if not minions.is_empty():
		return _lowest_hp(minions)
	return pairs[0][0] as UnitState


func _nearest(pairs: Array) -> UnitState:
	var best: UnitState = pairs[0][0]
	var best_dist: float = pairs[0][1]
	for pair in pairs:
		if pair[1] < best_dist:
			best_dist = pair[1]
			best = pair[0]
	return best


func _lowest_hp(pairs: Array) -> UnitState:
	var best: UnitState = pairs[0][0]
	for pair in pairs:
		var cand: UnitState = pair[0]
		if cand.hp < best.hp:
			best = cand
	return best


func _follow_lane(unit: UnitState) -> void:
	var path := paths[unit.lane]
	if unit.waypoint_index < 0 or unit.waypoint_index >= path.size():
		# Explicit lab boundary: retire at route end. Castle siege is NOT implemented yet.
		unit.alive = false
		escaped[unit.team] += 1
		_record({"kind": "exit", "target_id": unit.id})
		return
	var waypoint := path[unit.waypoint_index]
	if unit.position.distance_to(waypoint) < 15:
		unit.waypoint_index += 1 if unit.team == BLUE else -1
		return
	_move_toward(unit, waypoint)


func _move_toward(unit: UnitState, target: Vector2) -> void:
	var offset := target - unit.position
	if offset.length() <= 1.0:
		return
	if not is_zero_approx(offset.x):
		unit.facing = -1.0 if offset.x < 0 else 1.0
	unit.position += offset.normalized() * unit.definition.speed_px_per_tick


func _retire_dead() -> void:
	var survivors: Array[UnitState] = []
	for unit in units:
		if unit.alive:
			survivors.append(unit)
		else:
			_by_id.erase(unit.id)
	units = survivors
	for unit in units:
		if not _by_id.has(unit.target_id):
			unit.target_id = -1


func _record(event: Dictionary) -> void:
	event["tick"] = tick_count
	if recent_events.size() == MAX_EVENTS:
		recent_events.pop_front()
	recent_events.append(event)
