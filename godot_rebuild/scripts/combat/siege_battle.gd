extends "res://scripts/combat/minion_battle.gd"
## Tier-1 siege laboratory. Reuses minion simulation and one authoritative damage path.

const StructureDefinition = preload("res://scripts/data/structure_definition.gd")
const Projectile = preload("res://scripts/combat/projectile_state.gd")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const NEXUS = preload("res://data/structures/nexus_level_1.tres")
const MAX_STRUCTURES := 16
const MAX_PROJECTILES := 256
# One selected position per lane/team from _core.BLUE_TOWERS / RED_TOWERS.
# Cannon muzzle rows per level 1-6: [tower_h, forward barrel pixels].
# Derived from towers/_bundle.py LEVEL_CONFIGS + get_cannon_muzzle_position
# with recoil 0 (the source recoil branch is unreachable at fire time).
const CANNON_MUZZLE := [[38, 17], [42, 17], [46, 18], [52, 20], [56, 15], [62, 22]]
# Ice crystal rows per level 1-6: tower_h from towers/_bundle.py LEVEL_CONFIGS.
const ICE_CRYSTAL := [40, 44, 48, 54, 58, 64]
# Mage crystal rows per level 1-6: tower_h from towers/_bundle.py LEVEL_CONFIGS.
const MAGE_CRYSTAL := [45, 48, 52, 56, 60, 66]
const BLUE_POSITIONS := [Vector2(200, 180), Vector2(500, 340), Vector2(640, 640)]
const RED_POSITIONS := [Vector2(650, 90), Vector2(780, 400), Vector2(1090, 550)]

var structures: Array[StructureState] = []
var projectiles: Array[Projectile] = []
var tower_kills: Array[int] = [0, 0]
var nexuses: Array[StructureState] = [null, null]
var winner := -1
var _next_projectile_id := 1
var _arena_initialized := false


func is_running() -> bool:
	return winner == -1


func setup_arena() -> bool:
	if not is_running() or _arena_initialized or not structures.is_empty() or not units.is_empty():
		return false
	_arena_initialized = true
	for lane in range(3):
		spawn_structure(ARCHER, BLUE, BLUE_POSITIONS[lane], lane)
		spawn_structure(ARCHER, RED, RED_POSITIONS[lane], lane)
	spawn_structure(NEXUS, BLUE, LaneLayout.BLUE_BASE)
	spawn_structure(NEXUS, RED, LaneLayout.RED_BASE)
	return true


func structure_limit() -> int:
	return MAX_STRUCTURES


func spawn_structure(
	data: StructureDefinition, team: int, at: Vector2, lane: int = -1
) -> StructureState:
	if not is_running() or data == null or not data.is_valid() or team not in [BLUE, RED]:
		return null
	if structures.size() >= structure_limit() or not at.is_finite():
		return null
	if data.structure_kind == "nexus" and nexuses[team] != null:
		return null
	var structure := StructureState.new()
	structure.id = _next_id
	_next_id += 1
	structure.team = team
	structure.lane = lane
	structure.position = at
	structure.definition = data
	structure.hp = data.max_hp
	structure.shield_max = data.shield_capacity
	structure.shield = data.shield_capacity
	structure.castle_shield_purchased = false
	structure.free_shield_active = true
	structure.set_wave(wave_count)
	structures.append(structure)
	_by_id[structure.id] = structure
	if data.structure_kind == "nexus":
		nexuses[team] = structure
	return structure


func spawn_wave(definition: Definition) -> bool:
	return spawn_assault_wave(definition, -1)


func spawn_assault_wave(definition: Definition, team_mode: int) -> bool:
	# -1 = both teams, 0 = blue, 1 = red. Laboratory control, not production economy.
	if not is_running() or definition == null or not definition.is_valid():
		return false
	if team_mode not in [-1, BLUE, RED] or definition.speed_px_per_tick <= 0:
		return false
	var count := 6 if team_mode == -1 else 3
	if units.size() + count > MAX_UNITS:
		return false
	for lane in range(3):
		if team_mode in [-1, BLUE]:
			spawn_unit(definition, BLUE, lane)
		if team_mode in [-1, RED]:
			spawn_unit(definition, RED, lane)
	wave_count += 1
	for nexus in nexuses:
		if nexus != null:
			nexus.set_wave(wave_count)
	return true


func step_tick() -> void:
	if not is_running():
		return
	# Source order: minions, towers, then nexuses. Each structure updates old bullets before firing.
	super.step_tick()
	for kind in ["tower", "nexus"]:
		for structure in structures:
			if not is_running():
				break
			if not structure.alive or structure.settings().structure_kind != kind:
				continue
			structure.cooldown_ticks = maxi(0, structure.cooldown_ticks - 1)
			structure.tick_regen()
			_update_projectiles(structure)
			var target := _structure_target(structure)
			structure.target_id = target.id if target != null else -1
			if target != null and structure.cooldown_ticks == 0:
				fire_projectile(structure.id, target.id)
	_retire_dead()
	var flying: Array[Projectile] = []
	for shot in projectiles:
		var owner := get_unit(shot.source_id)
		var target := get_unit(shot.target_id)
		if shot.active and owner != null and owner.alive and target != null and target.alive:
			flying.append(shot)
		else:
			shot.active = false
	projectiles = flying


func apply_hit(attacker_id: int, target_id: int, school: String = "physical") -> bool:
	# A structure must fire a projectile; never allow an instant parallel damage path.
	if get_unit(attacker_id) is StructureState:
		return false
	return super.apply_hit(attacker_id, target_id, school)


func fire_projectile(source_id: int, target_id: int) -> bool:
	var source := get_unit(source_id) as StructureState
	var target := get_unit(target_id)
	if not is_running() or source == null or target == null or target is StructureState:
		return false
	if not source.alive or not target.alive or source.team == target.team:
		return false
	if source.cooldown_ticks > 0 or projectiles.size() >= MAX_PROJECTILES:
		return false
	if source.position.distance_to(target.position) > source.definition.attack_range_px:
		return false
	# Reserve the entire volley before mutation: never a partially emitted paid upgrade attack.
	var is_mage := source.settings().tower_path == "mage"
	var count := source.settings().chain_count if is_mage else source.settings().volley_count
	if projectiles.size() + count > MAX_PROJECTILES:
		return false
	var targets: Array[UnitState] = [target]
	for candidate in units:
		if targets.size() >= count:
			break
		if candidate == target or not candidate.alive or candidate.team == source.team:
			continue
		if source.position.distance_to(candidate.position) <= source.definition.attack_range_px:
			targets.append(candidate)
	# Archer refills missing shots with the main target; mage fires fewer
	# bolts instead. All mage bolts share the main-target muzzle point.
	if not is_mage:
		while targets.size() < count:
			targets.append(target)
	var offsets := [Vector2.ZERO]
	if not is_mage:
		if count == 2:
			offsets = [Vector2(-5, 0), Vector2(5, 0)]
		elif count == 3:
			offsets = [Vector2(-7, 2), Vector2(0, -1), Vector2(7, 2)]
	var muzzle := muzzle_position(source, target.position)
	for index in range(targets.size()):
		var shot := Projectile.new()
		shot.id = _next_projectile_id
		_next_projectile_id += 1
		shot.source_id = source.id
		shot.target_id = targets[index].id
		shot.team = source.team
		shot.damage = source.definition.damage
		shot.speed = source.settings().projectile_speed_px_per_tick
		shot.hit_radius = source.settings().projectile_hit_radius_px
		shot.position = muzzle if is_mage else muzzle + offsets[index]
		if source.settings().tower_path == "cannon":
			shot.kind = "cannon"
			shot.splash_radius = source.settings().splash_radius_px
			shot.burn_dps = source.settings().burn_dps
			shot.burn_duration = source.settings().burn_duration_ticks
		elif source.settings().tower_path == "ice":
			shot.kind = "ice"
			shot.slow_amount = source.settings().slow_amount
			shot.slow_duration = source.settings().slow_duration_ticks
			shot.atk_slow_amount = source.settings().atk_slow_amount
			shot.slow_aoe = source.settings().slow_aoe_px
		elif is_mage:
			shot.kind = "mage"
			shot.skill_down_amount = source.settings().skill_down_amount
			shot.anti_heal_amount = source.settings().anti_heal_amount
			shot.debuff_duration = source.settings().debuff_duration_ticks
		projectiles.append(shot)
	source.cooldown_ticks = source.definition.attack_cooldown_ticks
	return true


func muzzle_position(source: StructureState, target: Vector2) -> Vector2:
	if source.settings().structure_kind == "nexus":
		return source.position + Vector2(0, -25)
	if source.settings().tower_path == "cannon":
		# Exact source helper order: float scale, then Python-style int truncation.
		var row: Array = CANNON_MUZZLE[clampi(source.settings().level, 1, 6) - 1]
		var face := 1.0 if target.x > source.position.x else -1.0
		var center_y := 153.0 - float(row[0]) - 5.0 - 2.0 - 7.0
		var muzzle_x := source.position.x + float(row[1]) * face * 0.7
		var muzzle_y := source.position.y - 94.0 + center_y * 0.7
		return Vector2(int(muzzle_x), int(muzzle_y))
	if source.settings().tower_path == "ice":
		# Crystal helper, then a 5px aim offset. Angle math stays in
		# 64-bit doubles so the result matches CPython bit-for-bit.
		var tower_h: int = ICE_CRYSTAL[clampi(source.settings().level, 1, 6) - 1]
		var crystal := Vector2(
			int(source.position.x), int(source.position.y - 94.0 + (143.0 - tower_h) * 0.7)
		)
		var aim := atan2(
			float(target.y) - float(source.position.y), float(target.x) - float(source.position.x)
		)
		return Vector2(float(crystal.x) + cos(aim) * 5.0, float(crystal.y) + sin(aim) * 5.0)
	if source.settings().tower_path == "mage":
		# Mage crystal helper, then a 5px aim offset. Angle math stays
		# in 64-bit doubles so the result matches CPython bit-for-bit.
		var tower_h: int = MAGE_CRYSTAL[clampi(source.settings().level, 1, 6) - 1]
		var crystal := Vector2(
			int(source.position.x), int(source.position.y - 94.0 + (138.0 - tower_h) * 0.7)
		)
		var aim := atan2(
			float(target.y) - float(source.position.y), float(target.x) - float(source.position.x)
		)
		return Vector2(float(crystal.x) + cos(aim) * 5.0, float(crystal.y) + sin(aim) * 5.0)
	# Exact source bow helper: scalar doubles before Python-style int truncation.
	var side := 7.0 if target.x > source.position.x else -7.0
	return Vector2(
		int(float(source.position.x) + side * 0.7),
		int(float(source.position.y) - 94.0 + (142.0 - source.settings().bow_platform_height) * 0.7)
	)


func select_at(point: Vector2) -> int:
	var id := super.select_at(point)
	var chosen := get_unit(id)
	var best := point.distance_to(chosen.position) if chosen != null else INF
	for structure in structures:
		var distance := point.distance_to(structure.position)
		if structure.alive and distance <= structure.definition.radius_px + 8 and distance < best:
			id = structure.id
			best = distance
	return id


func _find_target(unit: UnitState) -> UnitState:
	# Both arrays are ID-sorted; merge once for stable global spawn order.
	var ordered: Array[UnitState] = []
	var ui := 0
	var si := 0
	while ui < units.size() or si < structures.size():
		var cand: UnitState = null
		if si >= structures.size() or (ui < units.size() and units[ui].id < structures[si].id):
			cand = units[ui]
			ui += 1
		else:
			cand = structures[si]
			si += 1
		if not cand.alive or cand.team == unit.team:
			continue
		ordered.append(cand)
	return _select_ai_target(unit, ordered)


func _follow_lane(unit: UnitState) -> void:
	if unit.waypoint_index >= 0 and unit.waypoint_index < paths[unit.lane].size():
		super._follow_lane(unit)
		return
	# Unlike the original lab, route endpoints continue toward the enemy nexus.
	var nexus := nexuses[1 - unit.team]
	if nexus != null and nexus.alive:
		_move_toward(unit, nexus.position)


func _damage_amount(target: UnitState, raw_damage: int, school: String) -> float:
	if target is StructureState:
		return (target as StructureState).absorb(raw_damage, school)
	return super._damage_amount(target, raw_damage, school)


func _on_death(source_team: int, target: UnitState) -> void:
	if not target is StructureState:
		super._on_death(source_team, target)
		return
	var structure := target as StructureState
	if structure.settings().structure_kind == "tower":
		tower_kills[source_team] += 1
		credited_gold[source_team] += structure.definition.gold_reward
	else:
		winner = source_team
		for shot in projectiles:
			shot.active = false
		projectiles.clear()
		_record({"kind": "victory", "team": winner, "target_id": target.id})


func _structure_target(structure: StructureState) -> UnitState:
	var target: UnitState = null
	var best := structure.definition.attack_range_px
	for candidate in units:
		if not candidate.alive or candidate.team == structure.team:
			continue
		var distance := structure.position.distance_to(candidate.position)
		# Source tower/castle uses <=: later stable ID wins exact ties.
		if distance <= best:
			best = distance
			target = candidate
	return target


func _update_projectiles(source: StructureState) -> void:
	for shot in projectiles:
		if not shot.active or shot.source_id != source.id:
			continue
		var target := get_unit(shot.target_id)
		shot.ttl_ticks -= 1
		if target == null or not target.alive or shot.ttl_ticks <= 0:
			shot.active = false
			continue
		var offset := target.position - shot.position
		if offset.length() < shot.speed + shot.hit_radius:
			# Deactivate BEFORE delivery: duplicate updates cannot apply the hit again.
			shot.active = false
			_deliver_hit(shot.source_id, shot.team, target, shot.damage, "physical", shot.position)
			if shot.kind == "cannon":
				_cannon_impact(shot, target)
			elif shot.kind == "ice":
				_ice_impact(shot, target)
			elif shot.kind == "mage":
				_mage_impact(shot, target)
		else:
			shot.position += offset.normalized() * shot.speed


func _cannon_impact(shot: Projectile, main: UnitState) -> void:
	# Port of Bullet._on_hit "cannon": burn the main target, then 60%
	# splash + burn to enemy units within radius of the impact point.
	# Source all_units never contains structures, so towers take no splash.
	if main.alive and shot.burn_dps > 0:
		apply_burn(main.id, shot.burn_dps, shot.burn_duration, shot.team)
	if shot.splash_radius <= 0:
		return
	var splash_damage := int(float(shot.damage) * 0.6)
	if splash_damage <= 0:
		return
	for victim in units:
		if victim == main or victim.team == shot.team or not victim.alive:
			continue
		if victim.position.distance_to(main.position) > shot.splash_radius:
			continue
		_deliver_hit(shot.source_id, shot.team, victim, splash_damage, "physical", shot.position)
		if victim.alive and shot.burn_dps > 0:
			apply_burn(victim.id, shot.burn_dps, shot.burn_duration, shot.team)


func _ice_impact(shot: Projectile, main: UnitState) -> void:
	# Port of Bullet._on_hit "ice": slow + attack-slow the main target,
	# then (level 6 only) the same slows, without damage, to enemy units
	# within slow_aoe of the impact point.
	if main.alive:
		apply_slow(main.id, shot.slow_amount, shot.slow_duration)
		if shot.atk_slow_amount > 0:
			apply_atk_slow(main.id, shot.atk_slow_amount, shot.slow_duration)
	if shot.slow_aoe <= 0:
		return
	for victim in units:
		if victim == main or victim.team == shot.team or not victim.alive:
			continue
		if victim.position.distance_to(main.position) > shot.slow_aoe:
			continue
		apply_slow(victim.id, shot.slow_amount, shot.slow_duration)
		if shot.atk_slow_amount > 0:
			apply_atk_slow(victim.id, shot.atk_slow_amount, shot.slow_duration)


func _mage_impact(shot: Projectile, main: UnitState) -> void:
	# Port of Bullet._on_hit "mage": skill-down + anti-heal the main
	# target only. Each chain bolt is a separate projectile, so every
	# chain victim runs this once.
	if main.alive:
		if shot.skill_down_amount > 0:
			apply_skill_down(main.id, shot.skill_down_amount, shot.debuff_duration)
		if shot.anti_heal_amount > 0:
			apply_anti_heal(main.id, shot.anti_heal_amount, shot.debuff_duration)


func _retire_dead() -> void:
	super._retire_dead()
	var standing: Array[StructureState] = []
	for structure in structures:
		if structure.alive:
			standing.append(structure)
		else:
			_by_id.erase(structure.id)
	structures = standing
	for entity in units + structures:
		var target := get_unit(entity.target_id)
		if target == null or not target.alive:
			entity.target_id = -1
