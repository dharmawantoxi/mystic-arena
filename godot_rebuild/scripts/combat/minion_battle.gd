extends RefCounted
## Deterministic tier-1 minion combat lab. No Nodes, rendering, wall clock, or RNG.
## Sequential attacks resolve in stable spawn-ID order; a killed unit cannot act later that tick.

const Definition = preload("res://scripts/data/minion_definition.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const LaneLayout = preload("res://scripts/data/lane_layout.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const MAX_UNITS := 120
const MAX_EVENTS := 64
const BLUE := 0
const RED := 1
const BURN_TICK_INTERVAL := 30
const BURN_TICKS_PER_SECOND := 60.0

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


func living_minion_count() -> int:
	var count := 0
	for unit in units:
		if unit.alive and not unit.is_hero:
			count += 1
	return count


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
		if unit.is_hero:
			# Heroes tick their own timers + shared debuffs. No lane
			# march, no AI orders, no passive heal in Kaizen-1.
			_tick_hero(unit as HeroState)
			_tick_debuffs(unit)
			_tick_burn(unit)
			continue
		unit.cooldown_ticks = maxi(0, unit.cooldown_ticks - 1)
		_tick_debuffs(unit)
		_tick_burn(unit)
		if not unit.alive:
			continue
		var capped := minf(unit.definition.max_hp, unit.hp + unit.definition.regen_per_tick)
		if capped > unit.hp and unit.anti_heal_timer > 0:
			unit.hp = unit.hp + (capped - unit.hp) * (1.0 - unit.anti_heal_amount)
		else:
			unit.hp = capped
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
	attacker.cooldown_ticks = _eff_attack_cd(attacker)
	attacker.facing = -1.0 if target.position.x < attacker.position.x else 1.0
	return true


func apply_burn(target_id: int, dps: float, duration: int, team: int) -> bool:
	# Port of TowerDebuffMixin.apply_debuff("burn"): structures have no
	# debuff API in the source, so only living units accept burn. The
	# source performs no team check; credit stays victim-based instead.
	var target := get_unit(target_id)
	if not is_running() or target == null or target is StructureState:
		return false
	if not target.alive or dps <= 0 or duration <= 0:
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
				if unit.is_hero:
					_on_hero_death(unit as HeroState, -1)
	if unit.burn_timer <= 0:
		unit.burn_dps = 0.0
		unit.burn_accum = 0.0


func apply_slow(target_id: int, amount: float, duration: int) -> bool:
	# Port of Minion.apply_slow: the stronger amount wins, but a longer
	# duration refreshes both fields even when weaker. Structures have no
	# slow API in the source (Castle.apply_slow is pass).
	var target := get_unit(target_id)
	if not is_running() or target == null or target is StructureState:
		return false
	if not target.alive or amount <= 0 or duration <= 0:
		return false
	if amount > target.slow_amount or target.slow_timer < duration:
		target.slow_amount = amount
		target.slow_timer = duration
	return true


func apply_atk_slow(target_id: int, amount: float, duration: int) -> bool:
	# Port of TowerDebuffMixin.apply_debuff("atk_slow").
	var target := get_unit(target_id)
	if not is_running() or target == null or target is StructureState:
		return false
	if not target.alive or amount <= 0 or duration <= 0:
		return false
	if amount > target.atk_slow_amount or target.atk_slow_timer < duration:
		target.atk_slow_amount = amount
		target.atk_slow_timer = duration
	return true


func apply_skill_down(target_id: int, amount: float, duration: int) -> bool:
	# Port of TowerDebuffMixin.apply_debuff("skill_down"). Minions have
	# no skills, so this only stores state; Hero.skill_damage reads it.
	var target := get_unit(target_id)
	if not is_running() or target == null or target is StructureState:
		return false
	if not target.alive or amount <= 0 or duration <= 0:
		return false
	if amount > target.skill_down_amount or target.skill_down_timer < duration:
		target.skill_down_amount = amount
		target.skill_down_timer = duration
	return true


func apply_anti_heal(target_id: int, amount: float, duration: int) -> bool:
	# Port of TowerDebuffMixin.apply_debuff("anti_heal"). The HP gain
	# scaling lives in the regen step, mirroring the source hp setter.
	var target := get_unit(target_id)
	if not is_running() or target == null or target is StructureState:
		return false
	if not target.alive or amount <= 0 or duration <= 0:
		return false
	if amount > target.anti_heal_amount or target.anti_heal_timer < duration:
		target.anti_heal_amount = amount
		target.anti_heal_timer = duration
	return true


func _tick_debuffs(unit: UnitState) -> void:
	if unit.slow_timer > 0:
		unit.slow_timer -= 1
		if unit.slow_timer <= 0:
			unit.slow_amount = 0.0
	if unit.atk_slow_timer > 0:
		unit.atk_slow_timer -= 1
		if unit.atk_slow_timer <= 0:
			unit.atk_slow_amount = 0.0
	if unit.skill_down_timer > 0:
		unit.skill_down_timer -= 1
		if unit.skill_down_timer <= 0:
			unit.skill_down_amount = 0.0
	if unit.anti_heal_timer > 0:
		unit.anti_heal_timer -= 1
		if unit.anti_heal_timer <= 0:
			unit.anti_heal_amount = 0.0


func _eff_speed(unit: UnitState) -> float:
	var speed: float = unit.definition.speed_px_per_tick
	if unit.slow_timer > 0:
		speed *= 1.0 - unit.slow_amount
	return speed


func _eff_attack_cd(unit: UnitState) -> int:
	if unit.atk_slow_timer <= 0:
		return unit.definition.attack_cooldown_ticks
	var factor := maxf(0.05, 1.0 - unit.atk_slow_amount)
	return maxi(1, DamageRules.rounded_like_python(unit.definition.attack_cooldown_ticks / factor))


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
		if target.is_hero:
			_on_hero_death(target as HeroState, source_id)
	return true


func _damage_amount(target: UnitState, raw_damage: int, school: String) -> float:
	if target is StructureState:
		# Structures absorb through armor + shield. Previously only the
		# siege override did this; hero AOE needs it at this level too.
		return (target as StructureState).absorb(raw_damage, school)
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
	unit.position += offset.normalized() * _eff_speed(unit)


func _retire_dead() -> void:
	var survivors: Array[UnitState] = []
	for unit in units:
		# Dead heroes stay addressable (death inspection now, respawn
		# later); only dead minions are retired.
		if unit.alive or unit.is_hero:
			survivors.append(unit)
		else:
			_by_id.erase(unit.id)
	units = survivors
	for unit in units:
		if not _by_id.has(unit.target_id):
			unit.target_id = -1
		if unit.is_hero:
			var hero := unit as HeroState
			if hero.target_struct != null and not hero.target_struct.alive:
				hero.target_struct = null


func spawn_hero(definition: HeroDefinition, team: int, pos: Vector2, level: int = 1) -> HeroState:
	if not is_running() or definition == null or not definition.is_valid():
		return null
	if team not in [BLUE, RED]:
		return null
	if units.size() >= MAX_UNITS:
		return null
	var hero := HeroState.new()
	hero.id = _next_id
	_next_id += 1
	hero.team = team
	hero.lane = -1
	hero.definition = definition
	hero.level = clampi(level, 1, HeroDefinition.MAX_HERO_LEVEL)
	hero.base_hp = definition.max_hp
	hero.base_damage = definition.damage
	hero.skill_base = definition.base_skill
	hero.speed = definition.speed_px_per_tick
	hero.attack_range = definition.attack_range_px
	hero.attack_cd_base = definition.attack_cooldown_ticks
	hero.skill_cd_max = definition.skill_cooldown_max
	hero.skill_range = definition.skill_range_px
	hero.dmg_school = definition.dmg_school
	hero.is_melee = definition.is_melee
	hero.w_cooldown_max = definition.w_cooldown_max
	hero.e_cooldown_max = definition.e_cooldown_max
	hero.r_cooldown_max = definition.r_cooldown_max
	hero.apply_level_stats()
	hero.hp = hero.max_hp
	hero.position = pos
	hero.facing = 1.0 if team == BLUE else -1.0
	hero.attack_facing = hero.facing
	units.append(hero)
	_by_id[hero.id] = hero
	return hero


func hero_basic_attack(hero_id: int, target_id: int) -> bool:
	# Port of Hero._do_attack (melee path, empty inventory). Guards,
	# facing lock, sequence count, and timer order match the source.
	var hero := get_unit(hero_id) as HeroState
	var target := get_unit(target_id)
	if not is_running() or hero == null or target == null:
		return false
	if not hero.alive or not target.alive:
		return false
	if hero.stun_timer > 0:
		return false
	if hero.position.distance_to(target.position) > hero.eff_attack_range():
		return false
	if hero.attack_timer != 0:
		return false
	var dx := target.position.x - hero.position.x
	if dx != 0.0:
		hero.facing = 1.0 if dx > 0.0 else -1.0
	hero.attack_facing = hero.facing
	hero.attack_seq += 1
	hero.attack_timer = hero.eff_attack_cd(hero.attack_cd_base)
	# Same-team delivery is refused here; the source lacks the team
	# check but can never aim at allies (AI targets enemies only).
	return _deliver_hit(hero.id, hero.team, target, hero.damage, hero.dmg_school, hero.position)


func upgrade_hero(hero_id: int) -> bool:
	var hero := get_unit(hero_id) as HeroState
	if hero == null:
		return false
	return hero.upgrade()


func _can_cast_hero_e(hero_id: int, structures: Array = []) -> bool:
	var hero := get_unit(hero_id) as HeroState
	if not is_running() or hero == null or not hero.alive:
		return false
	if hero.e_cooldown > 0:
		return false
	return _has_q_target(hero, structures)


func cast_hero_e(hero_id: int, structures: Array = []) -> bool:
	# Port of KaizenSkills.cast_e: Sweep AOE 100px, skill * 1.0, needs a target.
	var hero := get_unit(hero_id) as HeroState
	if not is_running() or hero == null or not hero.alive:
		return false
	if hero.e_cooldown > 0:
		return false
	if not _has_q_target(hero, structures):
		return false
	_deal_hero_aoe(hero, hero.position, 100.0, hero.skill_damage(), structures)
	hero.e_cooldown = hero.e_cooldown_max
	hero.active_skill = "e"
	hero.active_skill_timer = 60
	return true


func _can_cast_hero_w(hero_id: int) -> bool:
	var hero := get_unit(hero_id) as HeroState
	if not is_running() or hero == null or not hero.alive:
		return false
	return hero.w_cooldown <= 0


func cast_hero_w(hero_id: int) -> bool:
	# Port of KaizenSkills.cast_w: self Wind Wall, no target gate.
	var hero := get_unit(hero_id) as HeroState
	if not _can_cast_hero_w(hero_id):
		return false
	hero.wind_wall_timer = 180
	hero.w_cooldown = hero.w_cooldown_max
	hero.active_skill = "w"
	hero.active_skill_timer = 90
	return true


func can_cast_hero_q(hero_id: int, structures: Array = []) -> bool:
	var hero := get_unit(hero_id) as HeroState
	if not is_running() or hero == null or not hero.alive:
		return false
	if hero.skill_timer > 0:
		return false
	return _has_q_target(hero, structures)


func cast_hero_q(hero_id: int, structures: Array = []) -> bool:
	# Port of KaizenSkills.cast_q: Q1 Steel Wind at stack 0, Q2 Dash
	# Strike at stack 1. Structures (towers, then bases) mirror the
	# source all_towers/all_bases arguments.
	var hero := get_unit(hero_id) as HeroState
	if not is_running() or hero == null or not hero.alive:
		return false
	if hero.skill_timer > 0:
		return false
	if not _has_q_target(hero, structures):
		return false
	if hero.q_stack == 0:
		_deal_hero_aoe(hero, hero.position, hero.skill_range, hero.skill_damage(), structures)
		hero.q_stack = 1
	else:
		_cast_dash_strike(hero, structures)
		hero.q_stack = 0
	var data := hero.settings()
	hero.q_reset_timer = data.q_reset_ticks
	hero.skill_timer = hero.skill_cd_max
	hero.active_skill = "q"
	hero.active_skill_timer = data.q_visual_ticks
	return true


func _has_q_target(hero: HeroState, structures: Array) -> bool:
	# Port of BaseSkill._has_target/_acquire_target: keep a valid
	# current target, else nearest enemy in reach; ties keep the LAST
	# candidate (source `<=` scan), units before structures.
	var data := hero.settings()
	var reach := maxf(hero.attack_range, hero.skill_range) * data.q_reach_slack
	if hero.target_id >= 0:
		var current := get_unit(hero.target_id)
		if (
			current != null
			and current.alive
			and current.team != hero.team
			and hero.position.distance_to(current.position) <= reach
		):
			hero.target_struct = null
			return true
	if hero.target_struct != null:
		var kept := hero.target_struct
		if (
			kept.alive
			and kept.team != hero.team
			and hero.position.distance_to(kept.position) <= reach
		):
			return true
	var best_unit: UnitState = null
	var best_struct: StructureState = null
	var best_dist := reach
	for unit in units:
		if not unit.alive or unit.team == hero.team:
			continue
		var unit_dist := hero.position.distance_to(unit.position)
		if unit_dist <= best_dist:
			best_unit = unit
			best_struct = null
			best_dist = unit_dist
	for entry in structures:
		var structure := entry as StructureState
		if structure == null or not structure.alive or structure.team == hero.team:
			continue
		var struct_dist := hero.position.distance_to(structure.position)
		if struct_dist <= best_dist:
			best_unit = null
			best_struct = structure
			best_dist = struct_dist
	if best_unit == null and best_struct == null:
		return false
	if best_unit != null:
		hero.target_id = best_unit.id
		hero.target_struct = null
	else:
		hero.target_id = -1
		hero.target_struct = best_struct
	return true


func _deal_hero_aoe(
	hero: HeroState, center: Vector2, radius: float, raw_damage: int, structures: Array
) -> void:
	# Port of BaseSkill._deal_aoe_damage: every living enemy at most
	# `radius` from center takes int(skill * mult) with hero school.
	# Zero raw damage is a no-op in both codebases (0 never kills).
	if raw_damage <= 0:
		return
	for unit in units:
		if not unit.alive or unit.team == hero.team:
			continue
		if center.distance_to(unit.position) <= radius:
			_deliver_hit(hero.id, hero.team, unit, raw_damage, hero.dmg_school, center)
	for entry in structures:
		var structure := entry as StructureState
		if structure == null or not structure.alive or structure.team == hero.team:
			continue
		if center.distance_to(structure.position) <= radius:
			_deliver_hit(hero.id, hero.team, structure, raw_damage, hero.dmg_school, center)


func _cast_dash_strike(hero: HeroState, structures: Array) -> void:
	var data := hero.settings()
	var dest := hero.position
	if hero.target_id >= 0:
		var target := get_unit(hero.target_id)
		if target != null:
			dest = target.position
	elif hero.target_struct != null:
		dest = hero.target_struct.position
	var delta := dest - hero.position
	# The source divides by distance with no zero guard (unreachable:
	# radii keep units apart); the guard below only avoids a crash.
	if delta.length() > 0.0:
		hero.position += delta * 0.7
	hero.is_dashing = true
	hero.dash_timer = data.q_dash_ticks
	_deal_hero_aoe(
		hero, hero.position, data.q2_radius_px, int(hero.skill_damage() * data.q2_mult), structures
	)


func _tick_hero(hero: HeroState) -> void:
	if hero.attack_timer > 0:
		hero.attack_timer -= 1
	if hero.skill_timer > 0:
		hero.skill_timer -= 1
	if hero.w_cooldown > 0:
		hero.w_cooldown -= 1
	if hero.e_cooldown > 0:
		hero.e_cooldown -= 1
	if hero.r_cooldown > 0:
		hero.r_cooldown -= 1
	if hero.active_skill_timer > 0:
		hero.active_skill_timer -= 1
		if hero.active_skill_timer <= 0:
			hero.active_skill = ""
	if hero.q_reset_timer > 0:
		hero.q_reset_timer -= 1
		if hero.q_reset_timer <= 0:
			hero.q_stack = 0
	if hero.dash_timer > 0:
		hero.dash_timer -= 1
		if hero.dash_timer <= 0:
			hero.is_dashing = false
	if hero.wind_wall_timer > 0:
		hero.wind_wall_timer -= 1
	if hero.ulti_timer > 0:
		hero.ulti_timer -= 1
		if hero.ulti_timer <= 0:
			hero.ulti_active = false
	if hero.stun_timer > 0:
		hero.stun_timer -= 1


func _on_hero_death(hero: HeroState, source_id: int) -> void:
	# Port of the Hero.take_damage death branch: deaths+1, killer id,
	# and a full debuff clear. No gold is credited (hero definitions
	# carry gold_reward 0, locked by kaizen_checks).
	hero.deaths += 1
	hero.killed_by = source_id
	hero.slow_amount = 0.0
	hero.slow_timer = 0
	hero.atk_slow_amount = 0.0
	hero.atk_slow_timer = 0
	hero.skill_down_amount = 0.0
	hero.skill_down_timer = 0
	hero.anti_heal_amount = 0.0
	hero.anti_heal_timer = 0
	hero.burn_dps = 0.0
	hero.burn_timer = 0
	hero.burn_accum = 0.0
	hero.burn_tick_cd = 0
	hero.burn_team = -1
	hero.stun_timer = 0


func _record(event: Dictionary) -> void:
	event["tick"] = tick_count
	if recent_events.size() == MAX_EVENTS:
		recent_events.pop_front()
	recent_events.append(event)
