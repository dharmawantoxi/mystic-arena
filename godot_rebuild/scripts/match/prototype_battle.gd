# gdlint:disable=max-file-lines,max-line-length,class-definitions-order,unused-argument,max-public-methods
extends "res://scripts/combat/siege_battle.gd"
## Playable normal/level-1 subset. Wave/ledger/build rules are separate from the old manual labs.

const Upgrades = preload("res://scripts/match/archer_upgrades.gd")
const CannonUpgrades = preload("res://scripts/match/cannon_upgrades.gd")
const IceUpgrades = preload("res://scripts/match/ice_upgrades.gd")
const MageUpgrades = preload("res://scripts/match/mage_upgrades.gd")
const NexusUpgrades = preload("res://scripts/match/nexus_upgrades.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Forge = preload("res://scripts/match/forge.gd")
const AiHeroControl = preload("res://scripts/match/ai_hero_control.gd")
const AiController = preload("res://scripts/match/ai_controller.gd")
const AiBuild = preload("res://scripts/match/ai_build.gd")
const AiRecruitment = preload("res://scripts/match/ai_recruitment.gd")
const AiUpgrades = preload("res://scripts/match/ai_upgrades.gd")
const AiItems = preload("res://scripts/match/ai_items.gd")
const AiShields = preload("res://scripts/match/ai_shields.gd")
const AiDraft = preload("res://scripts/match/ai_draft.gd")
const ItemShopUI = preload("res://scripts/match/item_shop_ui.gd")
const Scheduler = preload("res://scripts/match/wave_scheduler.gd")
const SlotLayout = preload("res://scripts/match/slot_layout.gd")
const Slot = preload("res://scripts/match/build_slot.gd")
const ItemEffects = preload("res://scripts/match/item_effects.gd")
const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const ReflectItemEffects = preload("res://scripts/match/reflect_item_effects.gd")
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
# Layer 5f: Forge shop transactions (buy for a dead hero queues the order).
var forge := Forge.new()
# Layer 5f-2: ITEM FORGE panel state + click routing (drawing lives in the UI).
var item_shop := ItemShopUI.new()
# Layer 6a: per-tick AI hero control. The AI controller is not wired into the
# playable scene yet, so this stays off unless a caller asks for it.
var ai_heroes := AiHeroControl.new()
# Layer 6b: scheduling wrapper (source AIPlayer.update). Layer 6e: set_ai_enabled()
# is the only switch; with it off the red side stays idle.
var ai_controller := AiController.new()
var ai_enabled := false
var ai_hero_control_enabled := false
# Layer 6c: the action adapters and the persistent draft target the red side.
var ai_draft := AiDraft.new()
var ai_build := AiBuild.new()
var ai_recruitment := AiRecruitment.new()
var ai_upgrades := AiUpgrades.new()
var ai_items := AiItems.new()
var ai_shields := AiShields.new()
# Source Hero.aggro_range: an auto destination is abandoned inside this radius.
const HERO_AGGRO_RANGE := 250.0
var scheduler := Scheduler.new()
var slots: Array[Slot] = []
var transaction_error := ""


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
		# Source update_waves: the AI castle auto-levels while the wave starts.
		_auto_scale_ai_castle()
	for spawn in batch.spawns:
		spawn_unit(MINIONS[spawn.kind], spawn.team, spawn.lane)
	super.step_tick()
	if is_running():
		_tick_auras_and_items()
		_tick_item_debuffs()
		_step_hero_act()
		# Source Game.update runs the AI right after the entity loop.
		_step_ai_heroes()
		_step_ai()


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
	# Existing player command remains plain Archer, no draft reserve.
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
	hero.destination_auto = false
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
		if hero.has_destination and hero.destination_auto and hero_aggro_target(hero) != null:
			# Source: an AI destination yields to an enemy in aggro range in
			# the same frame; a manual destination is obeyed in full.
			hero.has_destination = false
			hero.destination_auto = false
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
	# Layer 5f (source Hero.respawn -> deliver_pending_forge_items): Forge
	# orders placed while the hero was dead land in the inventory now.
	forge.deliver_pending_forge_items(hero)


func try_auto_cast(hero: HeroState) -> void:
	# Port of Hero._try_auto_cast: only with a living enemy inside skill_range.
	# Priority R, then E (2+), W (HP < 40%), Q. The AI path calls this directly
	# (source _control_heroes), while the player path adds its own gating in
	# _step_hero_auto_cast.
	var nearby := _hero_skill_nearby(hero)
	if nearby <= 0:
		return
	var used := false
	if hero.r_cooldown <= 0:
		used = _cast_hero_r(hero.id, structures)
	if not used and hero.e_cooldown <= 0 and nearby >= 2:
		used = cast_hero_e(hero.id, structures)
	if not used and hero.w_cooldown <= 0 and hero.hp / maxf(1.0, hero.max_hp) < 0.4:
		used = cast_hero_w(hero.id)
	if not used and hero.skill_timer <= 0:
		used = cast_hero_q(hero.id, structures)
	if used:
		hero.spell_vamp_heal()


func _step_hero_auto_cast(hero: HeroState) -> void:
	# Player auto-cast: every 20 ticks, opt-in flag and no stun.
	if hero.auto_cast_enabled and hero.stun_timer <= 0:
		hero.auto_cast_check_timer -= 1
		if hero.auto_cast_check_timer <= 0:
			hero.auto_cast_check_timer = 20
			try_auto_cast(hero)


func move_to(hero: HeroState, point: Vector2, auto: bool) -> void:
	# Port of Hero.move_to: a new destination cancels follow and retreat.
	hero.has_destination = true
	hero.destination = point
	hero.destination_auto = auto
	hero.follow_id = -1
	hero.is_retreating = false


func hero_aggro_target(hero: HeroState) -> UnitState:
	# Port of Hero._find_aggro_target: nearest enemy inside HERO_AGGRO_RANGE
	# (the source updates on `<=`, so an equidistant later unit wins).
	var best: UnitState = null
	var best_dist := HERO_AGGRO_RANGE
	for unit in units:
		if not unit.alive or unit.team == hero.team or unit.id == hero.id:
			continue
		var dist := hero.position.distance_to(unit.position)
		if dist <= best_dist:
			best_dist = dist
			best = unit
	return best


func _tick_item_debuffs() -> void:
	# Layer 5b-3: every unit decays its target-side item debuffs once per tick
	# (source TowerDebuffMixin._tick_tower_debuffs).
	for unit in units:
		unit.tick_item_debuffs()


func apply_slow(target_id: int, amount: float, duration: int) -> bool:
	# Layer 5b-2: port of TowerDebuffMixin.apply_slow's item gate — slow resist
	# (Abyss Breaker) scales the incoming slow before the strongest-wins store.
	var target := get_unit(target_id)
	if target is HeroState:
		var resist := (target as HeroState).items.get_slow_resist()
		if resist > 0.0:
			amount *= 1.0 - resist
	return super.apply_slow(target_id, amount, duration)


func set_ai_enabled(enabled: bool) -> void:
	# Layer 6e: single switch for the match. The real AI owns the red side and
	# the red heroes; with the switch off (a test or scene that wants a manual
	# red side) no red transaction ever happens.
	ai_enabled = enabled
	ai_hero_control_enabled = enabled


func reset_ai(seed_value: int = -1) -> void:
	# Source Game.reset() constructs a new AIPlayer: think clock, adapter
	# counters, hero-skill counter and the persistent draft all return to their
	# opening state. One seed drives every AI stream so a restart replays.
	ai_controller.reset(seed_value)
	ai_heroes.total_skills_cast = 0
	ai_build.total_built = 0
	ai_upgrades.total_upgraded = 0
	ai_upgrades.total_nexus_upgrades = 0
	ai_upgrades.total_hero_upgrades = 0
	ai_draft.purchase_target = ""
	ai_draft.purchase_target_cost = 0
	ai_draft.total_heroes_bought = 0
	ai_draft.source_levels = {}
	if seed_value >= 0:
		ai_build.rng.seed = seed_value + 1
		ai_draft.rng.seed = seed_value + 2


func _step_ai() -> void:
	# Source Game.update: the AI runs once per tick, right after the entities.
	if not ai_enabled:
		return
	ai_controller.tick(Callable(self, "_step_ai_heroes"), Callable(self, "_ai_perform_step"))


func _ai_perform_step() -> bool:
	# Source _ai_step: one ordered priority scan. Gates and rolls live in
	# ai_policy.choose_step; every action goes through the real ledger adapter.
	return ai_controller.policy.choose_step(
		_ai_state(), Callable(self, "_ai_attempt"), Callable(ai_controller, "draw")
	)


func _ai_state() -> Dictionary:
	# Source _ai_step locals: empty build slots, purse, full roster (dead heroes
	# included), own living towers that can still upgrade, and own living towers.
	return {
		"empty_slots": _ai_empty_slots(),
		"gold": economy.gold[RED],
		"hero_count": _ai_roster().size(),
		"upgradeable_towers": ai_upgrades.tower_candidates(self).size(),
		"living_towers": _ai_living_towers().size(),
	}


func _ai_empty_slots() -> int:
	var count := 0
	for slot in slots:
		if slot != null and slot.team == RED and slot.structure_id == -1 and slot.lane in [0, 1, 2]:
			count += 1
	return count


func _ai_roster() -> Array:
	var heroes: Array = []
	for unit in units:
		if unit.is_hero and unit.team == RED:
			heroes.append(unit)
	return heroes


func _ai_living_towers() -> Array:
	var towers: Array = []
	for structure in structures:
		if (
			structure.alive
			and structure.team == RED
			and structure.settings().structure_kind == "tower"
		):
			towers.append(structure)
	return towers


func _ai_attempt(step: String) -> bool:
	# Adapter per source priority; a false answer moves the scan to the next
	# priority, exactly like the source returning from _ai_step.
	var done := false
	if step == "build":
		done = ai_build.try_build(self, ai_draft)
	elif step == "buy_hero":
		done = ai_recruitment.try_buy(self, ai_draft)
	elif step == "upgrade_hero":
		done = ai_upgrades.try_hero_priority(self, ai_draft)
	elif step == "buy_item":
		done = ai_items.try_buy_priority(self, ai_draft)
	elif step == "upgrade_tower":
		done = ai_upgrades.try_tower_priority(self, ai_draft)
	elif step == "regen_shield":
		done = ai_shields.try_regen_priority(self, ai_draft)
	elif step == "castle_shield" or step == "upgrade_nexus":
		done = _ai_nexus_attempt(step)
	return done


func _ai_nexus_attempt(kind: String) -> bool:
	# Source passes my_nexus to both shield and upgrade actions; a destroyed
	# nexus simply fails the action.
	var nexus := nexuses[RED]
	if nexus == null or not nexus.alive:
		return false
	if kind == "castle_shield":
		return ai_shields.try_castle(self, ai_draft, nexus.id)
	return ai_upgrades.try_nexus(self, ai_draft, nexus.id)


func _step_ai_heroes() -> void:
	if not ai_hero_control_enabled:
		return
	var towers: Array = []
	for structure in structures:
		if structure.alive and structure.settings().structure_kind == "tower":
			towers.append(structure)
	ai_heroes.control_heroes(self, towers)


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


func _deliver_hit(
	source_id: int,
	source_team: int,
	target: UnitState,
	raw_damage: int,
	school: String,
	origin: Vector2,
	damage_type: String = "normal"
) -> bool:
	# Layer 5b-4: port of the evasion/true-strike gate of Hero.take_damage.
	# Source `_school` is `resolve_damage_school`, which reads the attacker's
	# `dmg_school` first, so the incoming school is the right handle here.
	if (
		target is HeroState
		and _evaded(source_id, target as HeroState, raw_damage, school, damage_type)
	):
		return false
	return super._deliver_hit(
		source_id, source_team, target, raw_damage, school, origin, damage_type
	)


func _evaded(
	source_id: int, defender: HeroState, raw_damage: int, school: String, damage_type: String
) -> bool:
	# Source `_is_physical_hit`: only normal/projectile hits that are not magic
	# can miss. Blind (Solar Brand aura) has no setter in the source either, so
	# only evasion and true strike are live here.
	var physical := damage_type in ["normal", "projectile"] and school != "magic"
	if not physical or raw_damage <= 0:
		return false
	var attacker := get_unit(source_id)
	if attacker is HeroState and (attacker as HeroState).items.has_true_strike():
		return false
	var chance := defender.items.get_evasion()
	# Source: blind lives on the ATTACKER and shares one roll with evasion.
	if attacker != null and attacker.blind_timer > 0:
		chance = maxf(chance, attacker.blind_amount)
	return chance > 0.0 and _item_rng.randf() < chance


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
	_apply_nexus_stats(nexus, target)
	_record({"kind": "nexus_upgrade", "target_id": nexus.id, "level": nexus.settings().level})
	return true


func _apply_nexus_stats(nexus: StructureState, target: StructureDefinition) -> void:
	# Port of Castle._apply_level_stats (and the tail of the paid upgrade):
	# the new HP keeps the old ratio plus the flat margin, and a purchased
	# castle shield keeps its percentage while the capacity follows the HP.
	var old_max: int = nexus.definition.max_hp
	var old_hp: float = nexus.hp
	var new_max: int = target.max_hp
	var ratio := old_hp / float(maxi(1, old_max))
	nexus.definition = target
	nexus.hp = mini(new_max, int(new_max * ratio) + (new_max - old_max) + 500)
	if nexus.castle_shield_purchased:
		var old_shield_max := maxf(1.0, nexus.shield_max)
		var shield_ratio := clampf(nexus.shield / old_shield_max, 0.0, 1.0)
		nexus.shield_max = target.shield_capacity
		nexus.shield = int(nexus.shield_max * shield_ratio)


func _auto_scale_ai_castle() -> void:
	# Port of Game._auto_scale_ai_castle: with every new wave the AI castle
	# levels on the source schedule (4/7/10/13 -> 2/3/4/5). The upgrade is
	# free — the source only calls Castle.upgrade(), which never touches gold;
	# the player still pays for its own nexus upgrades.
	var target_level := 1
	if wave_count >= 4:
		target_level = 2
	if wave_count >= 7:
		target_level = 3
	if wave_count >= 10:
		target_level = 4
	if wave_count >= 13:
		target_level = 5
	var nexus := nexuses[RED]
	while (
		nexus != null
		and nexus.alive
		and nexus.settings().level < target_level
		and nexus.settings().level < NexusUpgrades.LEVELS.size()
	):
		_apply_nexus_stats(nexus, NexusUpgrades.LEVELS[nexus.settings().level])


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
	hero.spell_vamp_heal()
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
	hero.spell_vamp_heal()
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
	hero.spell_vamp_heal()
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
	hero.spell_vamp_heal()
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


# ── Item wiring (layer 5c-2): tick_timers + auto-triggers + damage notify ──
# ── Item wiring (layer 5c-2): tick_timers + auto-triggers + damage notify ──
var _item_rng := RandomNumberGenerator.new()


func _hero_enemy_list() -> Array:
	# Source _get_all_enemies returns alive enemies (units+towers+bases); this
	# rebuild only tracks units so far (towers/bases are StructureState and
	# included later by 5d auras).
	var enemies: Array = []
	for unit in units:
		if not unit.alive:
			continue
		# Layer 5e-3: heroes carry their scaled max_hp, minions their
		# definition max_hp (source minion.max_hp), so Miasma uses the real
		# % Max HP damage instead of falling to its 6-damage floor.
		var raw_max: Variant = unit.get("max_hp")
		if raw_max == null:
			raw_max = unit.definition.max_hp
		(
			enemies
			. append(
				{
					"id": unit.id,
					"pos": unit.position,
					"team": unit.team,
					"alive": true,
					"max_hp": 0 if raw_max == null else int(raw_max),
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
	var enemies: Array = _hero_enemy_list()
	hero.items.tick_miasma(1, enemies, _battle_item_effects(hero))
	hero.items.tick_auto(1, enemies, _battle_item_effects(hero), _item_rng)
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


# ── Layer 5d: aura + update_auras (hero_items.py ~2760) ──
const AURA_DEBUFF_DURATION := 30


func _tick_auras_and_items() -> void:
	# Source calls update_auras() once per frame from Game.update, then each
	# hero's tick timers/auto-triggers advance. Minions are exposed through
	# the live unit list so Everfrost/Solar/Sear auras can reach them.
	_update_auras()
	for unit in units:
		if (unit is HeroState) and unit.alive:
			_tick_hero_items(unit as HeroState)


func _collect_all_units() -> Array:
	# Source _collect_all_units: all living heroes + minions + boss. This
	# rebuild tracks no boss yet, so units alone is sufficient.
	var out: Array = []
	for unit in units:
		if unit != null and unit.alive:
			out.append(unit)
	return out


func _update_auras() -> void:
	# Reset aura fields on every hero inventory first.
	var all_heroes: Array = []
	for unit in units:
		if (unit is HeroState) and unit.alive:
			var h: HeroState = unit as HeroState
			all_heroes.append(h)
			h.items.aura_armor = 0
			h.items.aura_as = 0
			h.items.aura_armor_reduction = 0
			h.items.aura_guard_block = 0

	# ── Scarlet Bulwark: Bulwark Guard ally aura (active-gated) ──
	var guards: Array = []
	var guard_active: Dictionary = _aura_catalog("scarlet_bulwark").get("active", {})
	var g_radius := float(guard_active.get("ally_radius", 0))
	var g_base := float(guard_active.get("base_block", 0))
	var g_hp_pct := float(guard_active.get("max_hp_block_pct", 0.0))
	for h in all_heroes:
		if h.items.has("scarlet_bulwark") and h.items.guard_timer > 0:
			guards.append(h)
	for h in all_heroes:
		for src in guards:
			if src.team != h.team:
				continue
			if src.position.distance_to(h.position) <= g_radius:
				var blk: int = int(g_base + int(src.max_hp) * g_hp_pct)
				if blk > h.items.aura_guard_block:
					h.items.aura_guard_block = blk

	# ── Everfrost / Solar Brand / Searbrand enemy unit auras ──
	var frost_src: Array = []
	var solar_src: Array = []
	var sear_src: Array = []
	for h in all_heroes:
		if h.items.has("everfrost_guard"):
			frost_src.append(h)
		if h.items.has("solar_brand"):
			solar_src.append(h)
		if h.items.has("searbrand"):
			sear_src.append(h)
	if not (frost_src.is_empty() and solar_src.is_empty() and sear_src.is_empty()):
		var f_cat: Dictionary = _aura_catalog("everfrost_guard").get("aura", {})
		var s_cat: Dictionary = _aura_catalog("solar_brand").get("aura", {})
		var se_cat: Dictionary = _aura_catalog("searbrand").get("aura", {})
		var f_r := float(f_cat.get("enemy_radius", 0))
		var f_as := float(f_cat.get("enemy_atk_slow", 0.0))
		var f_heal := float(f_cat.get("enemy_anti_heal", 0.0))
		var s_r := float(s_cat.get("enemy_radius", 0))
		var s_burn := float(s_cat.get("burn_dps", 0.0))
		var s_blind := float(s_cat.get("blind", 0.0))
		var se_r := float(se_cat.get("enemy_radius", 0))
		var se_heal := float(se_cat.get("enemy_anti_heal", 0.0))
		var se_burn := float(se_cat.get("burn_dps", 0.0))
		for u in _collect_all_units():
			if u is HeroState and (u as HeroState).shadow_realm_timer > 0:
				continue
			for src in frost_src:
				if u.team == src.team:
					continue
				if src.position.distance_to(u.position) <= f_r:
					apply_atk_slow(u.id, f_as, AURA_DEBUFF_DURATION)
					apply_anti_heal(u.id, f_heal, AURA_DEBUFF_DURATION)
					break
			for src in solar_src:
				if u.team == src.team:
					continue
				if src.position.distance_to(u.position) <= s_r:
					apply_burn(u.id, s_burn, AURA_DEBUFF_DURATION, src.team)
					# Source Scorched Earth also blinds: incoming physical
					# hits of the unit inside the aura can miss.
					u.apply_miss_chance(s_blind, AURA_DEBUFF_DURATION)
					break
			for src in sear_src:
				if u.team == src.team:
					continue
				if src.position.distance_to(u.position) <= se_r:
					apply_anti_heal(u.id, se_heal, AURA_DEBUFF_DURATION)
					apply_burn(u.id, se_burn, AURA_DEBUFF_DURATION, src.team)
					break

	_aura_steel_aegis(all_heroes)


func _aura_steel_aegis(all_heroes: Array) -> void:
	var sources: Array = []
	for h in all_heroes:
		if h.items.has("steel_aegis"):
			sources.append(h)
	if sources.is_empty():
		return
	var data: Dictionary = _aura_catalog("steel_aegis").get("aura", {})
	var ally_r := float(data.get("ally_radius", 0))
	var enemy_r := float(data.get("enemy_radius", 0))
	var a_armor: int = int(data.get("ally_armor", 0))
	var a_as: int = int(data.get("ally_attack_speed", 0))
	var e_red: int = int(data.get("enemy_armor_reduction", 0))
	for h in all_heroes:
		for src in sources:
			if src == h:
				continue
			var d: float = src.position.distance_to(h.position)
			if h.team == src.team:
				if d <= ally_r:
					h.items.aura_armor += a_armor
					h.items.aura_as += a_as
			else:
				if d <= enemy_r:
					h.items.aura_armor_reduction += e_red


func _aura_catalog(item_id: String) -> Dictionary:
	# Aura/active sub-tables live on the shared catalog already loaded into
	# each inventory; any alive hero's inventory returns the same dict.
	if units.is_empty():
		return {}
	for unit in units:
		if unit is HeroState:
			return (unit as HeroState).items.item(item_id)
	return {}


# ── Layer 5e: on-hit wiring (crit + lifesteal + cleave + on-hit procs) ──


func hero_basic_attack(hero_id: int, target_id: int) -> bool:
	# Override parent to apply item crit, bonus damage, ranged lifesteal and
	# melee/ranged on-hit procs. Base validation/cooldown/timers mirror the
	# parent; we patch the raw damage and add post-hit callbacks.
	var hero: HeroState = get_unit(hero_id) as HeroState
	var target: Object = get_unit(target_id)
	if not is_running() or hero == null or target == null:
		return false
	if not hero.alive or not target.alive:
		return false
	if hero.stun_timer > 0 or hero.items.is_veiled():
		return false
	if hero.position.distance_to(target.position) > hero.eff_attack_range():
		return false
	if hero.attack_timer != 0:
		return false
	var dx: float = target.position.x - hero.position.x
	if dx != 0.0:
		hero.facing = 1.0 if dx > 0.0 else -1.0
	hero.attack_facing = hero.facing
	hero.attack_seq += 1
	hero.attack_timer = hero.eff_attack_cd(hero.attack_cd_base)
	var raw: int = hero.damage + int(hero.items.get_bonus_damage())
	if hero.settings().id == "grimjaw" and hero.grimjaw_crit_timer > 0:
		raw *= 2
	hero.items.set_hero_runtime(
		hero.id,
		hero.alive,
		hero.hp,
		int(hero.max_hp),
		hero.team,
		hero.facing,
		hero.position,
		hero.target_id
	)
	var is_crit := false
	var rend: Variant = hero.items.get_rend_crit()
	if rend != null and target.id == hero.items.rend_target:
		raw = int(float(raw) * float(rend))
		is_crit = true
	if not is_crit:
		var cr: Array = hero.items.roll_crit(_item_rng)
		if bool(cr[0]):
			raw = int(float(raw) * float(cr[1]))
			is_crit = true
	var bus := _battle_item_effects(hero)
	if not hero.is_melee and hero.settings().id != "morgath":
		_hero_ranged_spawn(hero, target, raw)
		var ls: float = hero.items.get_lifesteal_pct()
		if ls > 0.0:
			hero.hp = minf(hero.max_hp, hero.hp + float(raw) * ls)
		hero.items.on_ranged_attack_hit(target.id, raw, _hero_enemy_list(), _item_rng, bus)
	else:
		var landed := _deliver_hit(hero.id, hero.team, target, raw, hero.dmg_school, hero.position)
		if landed and target.alive:
			hero.items.on_basic_attack_hit(target.id, raw, _hero_enemy_list(), _item_rng, bus)
	hero.hp = hero.items.hero_hp
	return true


func _hero_ranged_spawn(hero: HeroState, target: Object, damage: int) -> void:
	HeroProjectiles.spawn(hero_projectiles, hero, target, damage)
