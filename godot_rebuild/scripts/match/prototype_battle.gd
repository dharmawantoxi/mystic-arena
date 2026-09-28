# gdlint:disable=max-file-lines,max-line-length,class-definitions-order,unused-argument
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
const ItemEffects = preload("res://scripts/match/item_effects.gd")
const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const ReflectItemEffects = preload("res://scripts/match/reflect_item_effects.gd")
const ItemAuras = preload("res://scripts/match/item_auras.gd")
const MINIONS := {
	"goblin": preload("res://data/minions/goblin.tres"),
	"orc": preload("res://data/minions/orc.tres"),
	"troll": preload("res://data/minions/troll.tres"),
	"undead": preload("res://data/minions/undead.tres"),
	"dark_rider": preload("res://data/minions/dark_rider.tres")
}
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const THORNE = preload("res://data/heroes/thorne.tres")
const GRIMJAW = preload("res://data/heroes/grimjaw.tres")
const SYLARA = preload("res://data/heroes/sylara.tres")
const VEX = preload("res://data/heroes/vex.tres")
const ZEPHYR = preload("res://data/heroes/zephyr.tres")
const PLAYABLE_AI_HEROES = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
const HERO_SPAWN := Vector2(220, 540)
# Source AIPlayer: RED_BASE_X - 60, RED_BASE_Y + 30. Not a shop purchase.
const RED_HERO_SPAWN := Vector2(1120, 130)
const HERO_HUNT_RANGE := 900.0
const HERO_RETREAT_HP := 0.2
const HERO_HEAL_RATIO := 0.8
const HERO_BASE_HEAL := 3.0
const HERO_PASSIVE_HEAL := 0.15
const HERO_BASE_NEAR := 100.0

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
	# Free mirrored Kaizen pair. Not a catalog purchase, not AIPlayer.
	spawn_hero(KAIZEN, BLUE, HERO_SPAWN)
	spawn_hero(KAIZEN, RED, RED_HERO_SPAWN)
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
		_step_hero_act()
		_update_item_auras()


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
	# Existing player command and temporary defender remain plain Archer, no draft reserve.
	return _build_tower_for(team, slot_id, "archer")


func _build_tower_for(team: int, slot_id: int, path: String, reserve: int = 0) -> bool:
	transaction_error = ""
	var slot := get_slot(slot_id)
	if not is_running() or team not in [BLUE, RED]:
		transaction_error = "finished"
	elif slot == null or slot.id != slot_id or slot.team != team:
		transaction_error = "owner"
	elif slot.lane not in [0, 1, 2] or not slot.position.is_finite():
		transaction_error = "owner"
	elif slot.structure_id != -1:
		transaction_error = "occupied"
	elif path not in ["archer", "cannon", "ice", "mage"]:
		transaction_error = "path"
	elif economy.gold[team] < Economy.BUILD_COST + maxi(0, reserve):
		transaction_error = "gold"
	elif structures.size() >= structure_limit() or _next_id <= 0 or _by_id.has(_next_id):
		transaction_error = "capacity"
	if not transaction_error.is_empty():
		return false
	# Python constructs an Archer Lv1, then changes tower_type and reapplies
	# stats. Missing non-Archer Lv1 stats fall back to Archer Lv1, but path
	# identity (and thus projectile kind/muzzle and later upgrade) stays distinct.
	var definition: StructureDefinition = ARCHER
	if path != "archer":
		definition = ARCHER.duplicate() as StructureDefinition
		definition.id = path + "_level_1"
		definition.display_name = path.capitalize() + " Lv.1"
		definition.tower_path = path
	var tower := spawn_structure(definition, team, slot.position, slot.lane)
	if tower == null:
		transaction_error = "capacity"
		return false
	# No callbacks/await between validation and debit. Never put side effects in assert().
	economy.spend(team, Economy.BUILD_COST)
	slot.structure_id = tower.id
	_record({"kind": "build", "team": team, "slot_id": slot.id, "target_id": tower.id})
	return true


func _buy_ai_hero(hero_type: String, cost: int, pos: Vector2) -> bool:
	# Draft callback: synchronous atomic red purchase, not a UI command.
	# Unregistered catalog entries have metadata only, not native kits yet.
	transaction_error = ""
	var kit: HeroDefinition = PLAYABLE_AI_HEROES.get(hero_type) as HeroDefinition
	if not is_running():
		transaction_error = "finished"
	elif kit == null or kit.id != hero_type or cost != kit.cost or cost <= 0:
		transaction_error = "kit"
	elif not pos.is_finite():
		transaction_error = "position"
	elif economy.gold[RED] < cost:
		transaction_error = "gold"
	elif units.size() >= MAX_UNITS or _next_id <= 0 or _by_id.has(_next_id):
		transaction_error = "capacity"
	else:
		var count := 0
		for unit in units:
			if unit.is_hero and unit.team == RED:
				if get_unit(unit.id) != unit or unit.definition == null:
					transaction_error = "registry"
					break
				count += 1
				if unit.definition.id == hero_type:
					transaction_error = "owned"
					break
		if transaction_error.is_empty() and count >= 5:
			transaction_error = "capacity"
		elif transaction_error.is_empty() and pos != RED_HERO_SPAWN + Vector2(0, count * 40 - 40):
			transaction_error = "position"
	if not transaction_error.is_empty():
		return false
	var hero := spawn_hero(kit, RED, pos)
	if hero == null:
		transaction_error = "capacity"
		return false
	economy.spend(RED, cost)
	_record({"kind": "hero_buy", "team": RED, "target_id": hero.id, "hero_type": hero_type})
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
	economy.credit_sale(team, tower.sale_value())
	_record({"kind": "sale", "team": team, "target_id": entity_id})
	return true


func _on_death(source_team: int, target: UnitState) -> void:
	var before := credited_gold[source_team]
	super._on_death(source_team, target)
	economy.credit_kill(source_team, credited_gold[source_team] - before)
	if not is_running():
		scheduler.cancel()


func _on_hero_death(hero: HeroState, source_id: int) -> void:
	super._on_hero_death(hero, source_id)
	# Source Hero.take_damage death branch (_entity.py:4742): the inventory
	# destroys Holy Rapier for good. The source does not recalculate max HP
	# there and the rapier carries no HP stat, so HP math stays untouched.
	hero.items.clear_on_death()
	# Source Game._process_hero_kill: credit only when the last hit came from a
	# real enemy hero (not the victim, not a tower/minion/castle). No popup.
	var killer := get_unit(source_id) as HeroState
	if killer == null or killer == hero or killer.team == hero.team:
		return
	killer.kills += 1


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


func set_hero_destination(hero_id: int, point: Vector2) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	hero.has_destination = true
	hero.destination = point
	hero.follow_id = -1
	return true


func _set_hero_autocast(hero_id: int) -> bool:
	# Port of the source toggle_autocast button (v29): the flag can only
	# be forced true, there is no off path. Blue only, like other orders.
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	hero.auto_cast_enabled = true
	return true


func _set_hero_follow(hero_id: int, target_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	var target := get_unit(target_id)
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	elif target == null or not target.alive or target.team == BLUE or target.id == hero.id:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	hero.follow_id = target.id
	hero.has_destination = false
	return true


func _step_hero_act() -> void:
	# Port of Hero.update states 1–6 plus Game respawn. No items.
	var roster: Array = []
	for unit in units:
		if unit.is_hero:
			roster.append(unit)
	for entry in roster:
		_step_one_hero(entry as HeroState)


func _step_one_hero(hero: HeroState) -> void:
	if not hero.alive:
		_step_hero_respawn(hero)
	elif hero.stun_timer > 0 or hero.is_dashing:
		pass
	else:
		_hero_passive_heal(hero)
		_step_hero_auto_cast(hero)
		var ratio := hero.hp / maxf(1.0, hero.max_hp)
		if ratio < HERO_RETREAT_HP:
			hero.is_retreating = true
		if hero.is_retreating and ratio >= HERO_HEAL_RATIO:
			hero.is_retreating = false
		if hero.is_retreating:
			_step_hero_retreat(hero)
		elif hero.has_destination:
			_step_hero_destination(hero)
		elif _step_hero_follow(hero):
			pass
		else:
			var melee := _hero_pick_target(hero, hero.eff_attack_range(), true)
			if melee != null:
				if hero.attack_timer == 0:
					hero_basic_attack(hero.id, melee.id)
			else:
				var hunted := _hero_pick_target(hero, HERO_HUNT_RANGE, false)
				if hunted != null:
					_move_toward(hero, hunted.position)
				else:
					_move_toward(hero, _hero_push_point(hero))


func _step_hero_respawn(hero: HeroState) -> void:
	# Source: first sighting sets 600, then the same frame decrements.
	if hero.respawn_timer <= 0:
		hero.respawn_timer = 600
	hero.respawn_timer -= 1
	if hero.respawn_timer > 0:
		return
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
	hero.alive = true
	hero.hp = hero.max_hp
	hero.killed_by = -1
	hero.position = _hero_spawn_point(hero)
	hero.has_destination = false
	hero.follow_id = -1
	hero.skill_timer = 0
	# Source Hero.respawn clears Q timer, not universal W/E/R cooldowns.
	# Preserve the original Kaizen rebuild contract; new kits follow source.
	if hero.settings().id == "kaizen":
		hero.w_cooldown = 0
		hero.e_cooldown = 0
		hero.r_cooldown = 0
	if hero.settings().id in ["kaizen", "thorne", "grimjaw", "sylara"]:
		hero.attack_timer = 0
	hero.q_stack = 0
	hero.q_reset_timer = 0
	hero.wind_wall_timer = 0
	hero.ulti_active = false
	hero.ulti_timer = 0
	hero.active_skill = ""
	hero.active_skill_timer = 0
	hero.is_dashing = false
	hero.dash_timer = 0
	hero.stun_timer = 0
	hero.target_id = -1
	hero.target_struct = null
	hero.is_retreating = false
	hero.respawn_timer = 0


func _step_hero_auto_cast(hero: HeroState) -> void:
	# Port of Hero._try_auto_cast: every 20 ticks, only with a living
	# enemy inside skill_range. Priority R, then E (2+), W (HP < 40%), Q.
	if hero.auto_cast_enabled and hero.stun_timer <= 0:
		hero.auto_cast_check_timer -= 1
		if hero.auto_cast_check_timer <= 0:
			hero.auto_cast_check_timer = 20
			var nearby := _hero_skill_nearby(hero)
			if nearby > 0:
				var used := false
				if hero.r_cooldown <= 0:
					used = _cast_hero_r(hero.id, structures)
				if not used and hero.e_cooldown <= 0 and nearby >= 2:
					used = cast_hero_e(hero.id, structures)
				if not used and hero.w_cooldown <= 0 and hero.hp / maxf(1.0, hero.max_hp) < 0.4:
					used = cast_hero_w(hero.id)
				if not used and hero.skill_timer <= 0:
					cast_hero_q(hero.id, structures)


func _hero_skill_nearby(hero: HeroState) -> int:
	var reach: float = hero.skill_range
	var count := 0
	for unit in units:
		if not unit.alive or unit.team == hero.team or unit.id == hero.id:
			continue
		if hero.position.distance_to(unit.position) <= reach:
			count += 1
	for structure in structures:
		if not structure.alive or structure.team == hero.team:
			continue
		if hero.position.distance_to(structure.position) <= reach:
			count += 1
	return count


func _hero_passive_heal(hero: HeroState) -> void:
	if hero.hp < hero.max_hp:
		hero.heal_hp(HERO_PASSIVE_HEAL)


func _hero_home(hero: HeroState) -> Vector2:
	return LaneLayout.BLUE_BASE if hero.team == BLUE else LaneLayout.RED_BASE


func _hero_push_point(hero: HeroState) -> Vector2:
	return LaneLayout.RED_BASE if hero.team == BLUE else LaneLayout.BLUE_BASE


func _hero_spawn_point(hero: HeroState) -> Vector2:
	return HERO_SPAWN if hero.team == BLUE else RED_HERO_SPAWN


func _hero_near_own_base(hero: HeroState) -> bool:
	return hero.position.distance_to(_hero_home(hero)) < HERO_BASE_NEAR


func _step_hero_retreat(hero: HeroState) -> void:
	if _hero_near_own_base(hero):
		hero.heal_hp(HERO_BASE_HEAL)
	else:
		_move_toward(hero, _hero_home(hero))
	var melee := _hero_pick_target(hero, hero.eff_attack_range(), true)
	if melee != null and hero.attack_timer == 0:
		hero_basic_attack(hero.id, melee.id)


func _step_hero_destination(hero: HeroState) -> void:
	# Source: walk first, still swing if someone is in melee, then return
	# (hunt does not override a player click).
	var offset := hero.destination - hero.position
	var speed := _eff_speed(hero)
	if offset.length() <= speed:
		hero.position = hero.destination
		hero.has_destination = false
	else:
		_move_toward(hero, hero.destination)
	var melee := _hero_pick_target(hero, hero.eff_attack_range(), true)
	if melee != null and hero.attack_timer == 0:
		hero_basic_attack(hero.id, melee.id)


func _step_hero_follow(hero: HeroState) -> bool:
	if hero.follow_id < 0:
		return false
	var target := get_unit(hero.follow_id)
	if target == null or not target.alive or target.team == hero.team:
		hero.follow_id = -1
		return false
	var reach := hero.eff_attack_range()
	if hero.position.distance_to(target.position) <= reach:
		if hero.attack_timer == 0:
			hero_basic_attack(hero.id, target.id)
	else:
		_move_toward(hero, target.position)
	return true


func _hero_pick_target(hero: HeroState, reach: float, inclusive: bool) -> UnitState:
	var best: UnitState = null
	var best_dist := reach
	for unit in units:
		if not unit.alive or unit.team == hero.team or unit.id == hero.id:
			continue
		var distance := hero.position.distance_to(unit.position)
		if (distance <= best_dist) if inclusive else (distance < best_dist):
			best = unit
			best_dist = distance
	for structure in structures:
		if not structure.alive or structure.team == hero.team:
			continue
		var distance := hero.position.distance_to(structure.position)
		if (distance <= best_dist) if inclusive else (distance < best_dist):
			best = structure
			best_dist = distance
	return best


func upgrade_price(entity_id: int, target_path: String = "archer") -> int:
	var tower := _owned_tower(entity_id)
	if tower == null:
		return 0
	var level: int = tower.settings().level
	var path_now: String = tower.settings().tower_path
	var target: StructureDefinition = _upgrade_target(level, path_now, target_path)
	return target.upgrade_price if target != null else 0


func upgrade_tower(entity_id: int, expected_level: int, target_path: String = "archer") -> bool:
	return _upgrade_tower_for(BLUE, entity_id, expected_level, target_path)


func _upgrade_tower_for(
	team: int, entity_id: int, expected_level: int, target_path: String, reserve: int = 0
) -> bool:
	transaction_error = ""
	var tower := _owned_tower(entity_id, team)
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
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# Source resets HP/shield fully but retains cooldown, target, regen timer and in-flight shots.
	economy.spend(team, cost)
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
	return _upgrade_nexus_for(BLUE, entity_id, expected_level)


func _upgrade_nexus_for(team: int, entity_id: int, expected_level: int, reserve: int = 0) -> bool:
	transaction_error = ""
	var nexus := _owned_nexus(entity_id, team)
	var cost := 0
	if nexus != null and nexus.settings().level < NexusUpgrades.LEVELS.size():
		cost = NexusUpgrades.LEVELS[nexus.settings().level].upgrade_price
	if not is_running():
		transaction_error = "finished"
	elif nexus == null:
		transaction_error = "owner"
	elif nexus.settings().level != expected_level:
		transaction_error = "stale"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	economy.spend(team, cost)
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


func _owned_nexus(entity_id: int, team: int = BLUE) -> StructureState:
	if team not in [BLUE, RED]:
		return null
	var nexus := get_unit(entity_id) as StructureState
	if nexus == null or not nexus.alive or nexus.team != team:
		return null
	if nexus.settings().structure_kind != "nexus":
		return null
	if nexuses[team] == null or nexuses[team].id != entity_id:
		return null
	return nexus


func _owned_tower(entity_id: int, team: int = BLUE) -> StructureState:
	if team not in [BLUE, RED]:
		return null
	var tower := get_unit(entity_id) as StructureState
	if tower == null or not tower.alive or tower.team != team:
		return null
	if tower.settings().structure_kind != "tower":
		return null
	for slot in slots:
		if slot.team == team and slot.structure_id == entity_id:
			return tower
	return null


func blue_hero() -> HeroState:
	for unit in units:
		if unit.is_hero and unit.team == BLUE:
			return unit as HeroState
	return null


func blue_q_ready() -> bool:
	var hero := blue_hero()
	return hero != null and can_cast_hero_q(hero.id, structures)


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


func _cast_blue_w(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not cast_hero_w(hero.id):
		transaction_error = "skill"
		return false
	_record({"kind": "skill_w", "target_id": hero.id})
	return true


func _cast_blue_e(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not cast_hero_e(hero.id, structures):
		transaction_error = "skill"
		return false
	_record({"kind": "skill_e", "target_id": hero.id})
	return true


func _cast_blue_r(hero_id: int) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	if not is_running():
		transaction_error = "finished"
	elif hero == null or not hero.alive or hero.team != BLUE:
		transaction_error = "owner"
	if not transaction_error.is_empty():
		return false
	if not _cast_hero_r(hero.id, structures):
		transaction_error = "skill"
		return false
	_record({"kind": "skill_r", "target_id": hero.id})
	return true


func _upgrade_blue_hero(hero_id: int, expected_level: int) -> bool:
	return _upgrade_hero_for(BLUE, hero_id, expected_level)


func _upgrade_hero_for(team: int, hero_id: int, expected_level: int, reserve: int = 0) -> bool:
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	var cost := 0
	if hero != null:
		cost = hero.upgrade_cost()
	if not is_running():
		transaction_error = "finished"
	elif team not in [BLUE, RED] or hero == null or hero.team != team:
		transaction_error = "owner"
	elif team == BLUE and not hero.alive:
		transaction_error = "owner"
	elif hero.level != expected_level:
		transaction_error = "stale"
	elif cost <= 0:
		transaction_error = "max_level"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	economy.spend(team, cost)
	upgrade_hero(hero.id)
	_record({"kind": "hero_upgrade", "target_id": hero.id, "level": hero.level})
	return true


func _activate_regen_shield_for(team: int, entity_id: int, reserve: int = 0) -> bool:
	return _purchase_shield_for(team, entity_id, false, reserve)


func _activate_castle_shield_for(team: int, entity_id: int, reserve: int = 0) -> bool:
	return _purchase_shield_for(team, entity_id, true, reserve)


func _purchase_shield_for(team: int, entity_id: int, castle: bool, reserve: int) -> bool:
	transaction_error = ""
	var target := _owned_nexus(entity_id, team) if castle else _owned_tower(entity_id, team)
	var cost := StructureState.CASTLE_SHIELD_COST if castle else StructureState.REGEN_SHIELD_COST
	if not is_running():
		transaction_error = "finished"
	elif target == null:
		transaction_error = "owner"
	elif (
		not target.can_activate_castle_shield()
		if castle
		else not target.can_activate_regen_shield()
	):
		transaction_error = "shield"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# No await/callback between eligibility, activation and the ledger debit.
	if castle:
		target.activate_castle_shield()
	else:
		target.activate_regen_shield()
	economy.spend(team, cost)
	_record({"kind": "castle_shield" if castle else "regen_shield", "target_id": entity_id})
	return true


func _buy_item_for(team: int, hero_id: int, item_id: String, reserve: int = 0) -> bool:
	# Port of the AIPlayer._try_buy_item transaction half: eligibility, equip
	# and ledger debit stay atomic, price comes from the item catalog metadata.
	transaction_error = ""
	var hero := get_unit(hero_id) as HeroState
	var cost := 0
	if hero != null:
		cost = int(hero.items.item(item_id).get("cost", 0))
	if not is_running():
		transaction_error = "finished"
	elif team not in [BLUE, RED] or hero == null or hero.team != team:
		transaction_error = "owner"
	elif not hero.alive:
		transaction_error = "owner"
	elif item_id == "" or cost <= 0:
		transaction_error = "catalog"
	elif hero.items.used_slots() >= hero.items.max_slots():
		transaction_error = "slots"
	elif economy.gold[team] < cost + maxi(0, reserve):
		transaction_error = "gold"
	if not transaction_error.is_empty():
		return false
	# The melee_only/magic_only gate is the only way the equip can still fail.
	if not hero.items.add(item_id):
		transaction_error = "gate"
		return false
	# Source HeroItemInventory.add recalculates max HP and heal amp inline.
	hero.apply_item_change()
	economy.spend(team, cost)
	_record({"kind": "hero_item", "target_id": hero.id, "item": item_id, "cost": cost})
	return true


# ── Item wiring: 5c-2 tick_timers + auto-triggers + damage notify, 5d auras ──
var _item_rng := RandomNumberGenerator.new()
var item_auras := ItemAuras.new()


func _hero_enemy_list() -> Array:
	# Source _get_all_enemies returns alive enemies (units+towers+bases); this
	# rebuild only tracks units so far. Tower/base auras do not exist in the
	# source aura block either (it reads minions + heroes + the live boss).
	var enemies: Array = []
	for unit in units:
		if not unit.alive:
			continue
		(
			enemies
			. append(
				{
					"id": unit.id,
					"pos": unit.position,
					"team": unit.team,
					"alive": true,
				}
			)
		)
	return enemies


func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
	var bus := BattleItemEffects.new()
	bus.world = self
	bus.dealer_id = source_hero.id
	bus.dealer_team = source_hero.team
	bus.dealer_pos = source_hero.position
	return bus


func _reflect_item_effects(_defender_team: int) -> ReflectItemEffects:
	var bus := ReflectItemEffects.new()
	bus.world = self
	bus.defender_team = _defender_team
	return bus


func _aura_item_effects() -> BattleItemEffects:
	# Aura sends carry no dealer: the debuff source is the aura holder's team,
	# which the aura pass puts in the effect itself.
	var bus := BattleItemEffects.new()
	bus.world = self
	return bus


func _update_item_auras() -> void:
	# Port of the Game.update aura call (layer 5d): one pass per frame, after
	# every entity update, over all heroes and the whole unit list (minions,
	# heroes and boss heroes). Source _collect_all_units() reads the live game
	# instance; the rebuild hands that same list to ItemAuras directly.
	var heroes: Array[HeroState] = []
	for unit in units:
		if unit.is_hero:
			heroes.append(unit as HeroState)
	item_auras.update_auras(heroes, units, _aura_item_effects())


func _tick_hero_items(hero: HeroState) -> void:
	# Called every tick (dt=1) after skill ticks. First decrement timers
	# (tick_timers ported in 5c-1), then run auto-triggers.
	hero.items.tick_timers(1)
	(
		hero
		. items
		. set_hero_runtime(
			hero.id,
			hero.alive,
			hero.hp,
			int(hero.max_hp),
			hero.team,
			hero.facing,
			hero.position,
			hero.target_id,
		)
	)
	hero.items.tick_auto(1, _hero_enemy_list(), _battle_item_effects(hero), _item_rng)
	# Apply HP regen result back to hero.
	hero.hp = hero.items.hero_hp


func _notify_item_damage(source_id: int, source_team: int, target: Object, damage: int) -> void:
	# Port of the post-mitigation notify hook in Hero.take_damage. Only hero
	# targets carry an inventory.
	if not (target is HeroState) or damage <= 0:
		return
	var src_alive := false
	var src_team := source_team
	if source_id >= 0:
		var src: Object = get_unit(source_id)
		if src != null:
			src_alive = src.alive
	var h: HeroState = target as HeroState
	h.items.set_hero_runtime(
		h.id, h.alive, h.hp, int(h.max_hp), h.team, h.facing, h.position, h.target_id
	)
	h.items.notify_damage_taken(
		damage, source_id, src_team, src_alive, _item_rng, _reflect_item_effects(h.team)
	)
