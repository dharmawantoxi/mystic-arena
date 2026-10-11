extends RefCounted
## Full-match integration for the real AIPlayer port: the open item in
## AI_CONTRACT.md ("uji integrasi penuh"). The adapter suites lock one module
## each; this one runs whole production matches, so the schedule, the draft
## reserve, the shared ledger and the roster cap are observed together, tick by
## tick, on the same world the playable scene uses.
##
## Bounds: no policy, balance, UI or Python source is changed here. The suite
## only exercises what already ships and locks the invariants a single adapter
## test cannot see (live reserve after every non-hero purchase, hero purchases
## clearing the target, a resolved match freezing the AI clock and purse).

const World = preload("res://scripts/match/prototype_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")

# PrototypeSession.AI_MATCH_SEED style: one seed drives every AI stream.
const MATCH_SEED := 20261011
# Waves delayed far past the decision window leave the seeded AI stream as the
# only RNG in play, so two identical worlds must agree tick for tick.
const QUIET_TICKS := 1800
const QUIET_WAVE_DELAY := 4000
# A full live match at level 1 needs waves, combat gold and several think ticks.
const MATCH_TICKS := 4200
# Live window with the purse pre-funded, so recruit/item/tower-upgrade families
# fire inside a bounded run; the adapter path and the ledger are untouched.
const FUNDED_TICKS := 3000
const FUNDED_GOLD := 30000
const IDLE_TICKS := 600
const ELITE_TICKS := 1200
const FREEZE_TICKS := 120
const ROSTER_CAP := 5
const ELITE_LEVEL := 54


func run(check: Callable) -> void:
	_quiet_decision_replay(check)
	_full_match(check)
	_funded_match(check)
	_switch_off(check)
	_elite_hard(check)


func _armed_world(level: int, difficulty: String, seed_value: int) -> World:
	# Same order as PrototypeSession: level and difficulty before the arena, then
	# the seeded AI owns the red side from the first tick.
	var world := World.new()
	world.configure_level(level)
	world.set_difficulty(difficulty)
	world.setup_arena()
	world.reset_ai(seed_value)
	world.set_ai_enabled(true)
	return world


func _quiet_decision_replay(check: Callable) -> void:
	var first := _armed_world(1, "normal", MATCH_SEED)
	var second := _armed_world(1, "normal", MATCH_SEED)
	first.scheduler.remaining_ticks = QUIET_WAVE_DELAY
	second.scheduler.remaining_ticks = QUIET_WAVE_DELAY
	for _tick in range(QUIET_TICKS):
		first.step_tick()
	var fingerprint: String = JSON.stringify(_ai_fingerprint(first))
	for _tick in range(QUIET_TICKS):
		second.step_tick()
	check.call(first.wave_count == 0, "the quiet window never reaches a wave")
	check.call(
		first.ai_controller.ticks == QUIET_TICKS,
		"the AI controller is dispatched on every production tick"
	)
	check.call(first.ai_build.total_built > 0, "the seeded AI builds before any wave")
	check.call(
		JSON.stringify(_ai_fingerprint(second)) == fingerprint,
		"the same match seed replays every AI decision and build exactly"
	)
	check.call(
		first.economy.is_balanced() and second.economy.is_balanced(),
		"both quiet-window ledgers reconcile"
	)


func _full_match(check: Callable) -> void:
	var world := _armed_world(1, "normal", MATCH_SEED)
	var gold_before: int = world.economy.gold[World.RED]
	var roster_before: int = world._ai_roster().size()
	var negative_gold := 0
	var cap_breaches := 0
	var reserve_breaches := 0
	var target_leaks := 0
	var recruits := 0
	var draft_target_ticks := 0
	for _tick in range(MATCH_TICKS):
		world.step_tick()
		var gold_after: int = world.economy.gold[World.RED]
		var roster_after: int = world._ai_roster().size()
		var reserve_after: int = world.ai_controller.reserve(world.ai_draft)
		if gold_after < 0:
			negative_gold += 1
		if roster_after > ROSTER_CAP:
			cap_breaches += 1
		if reserve_after > 0:
			draft_target_ticks += 1
		if gold_after < gold_before:
			if roster_after > roster_before:
				# A successful recruit clears the persistent draft target, so the
				# reserve is zero again at the end of that same tick.
				recruits += 1
				if reserve_after != 0:
					target_leaks += 1
			elif gold_after < reserve_after:
				# Source gate: gold >= cost + _ai_reserve() before every non-hero
				# purchase, so the live reserve survives the transaction.
				reserve_breaches += 1
		gold_before = gold_after
		roster_before = roster_after
	check.call(negative_gold == 0, "the red purse never goes negative in a live match")
	check.call(cap_breaches == 0, "the AI never owns more than five heroes")
	check.call(
		reserve_breaches == 0, "every non-hero purchase keeps the live hero draft reserve intact"
	)
	check.call(target_leaks == 0, "a successful recruit clears the draft target")
	check.call(
		draft_target_ticks > 0,
		"the AI saves for a hero draft instead of dropping an unaffordable target"
	)
	# The tick that resolves the match can bump the match clock without
	# dispatching the AI, so a live window tolerates exactly that one tick.
	check.call(
		(world.tick_count - world.ai_controller.ticks) in [0, 1],
		"the AI clock follows the match clock tick for tick"
	)
	check.call(world.wave_count > 0, "scheduled waves reach the field")
	check.call(
		world.ai_build.total_built > 0 and _red_towers(world) > 0,
		"the AI builds real red towers on the shared ledger"
	)
	check.call(
		world.economy.spent[World.RED] > 0 and world.economy.is_balanced(),
		"the AI spends the shared ledger and it reconciles"
	)
	check.call(
		world.economy.earned[World.RED] > 0,
		"red towers and units earn kill gold exactly like the player side"
	)
	check.call(recruits == world.ai_draft.total_heroes_bought, "every recruit is counted once")


func _funded_match(check: Callable) -> void:
	# The purse is pre-funded the way a long match's income would fill it; every
	# purchase still runs through the real adapters and the shared ledger.
	var world := _armed_world(1, "normal", MATCH_SEED + 1)
	world.economy.opening[World.RED] = FUNDED_GOLD
	world.economy.gold[World.RED] = FUNDED_GOLD
	for _tick in range(FUNDED_TICKS):
		world.step_tick()
	check.call(
		(
			world.ai_build.total_built > 0
			and world.ai_draft.total_heroes_bought > 0
			and world._ai_roster().size() > 0
		),
		"the live AI builds towers and recruits heroes into an empty roster"
	)
	check.call(
		(
			world.ai_upgrades.total_upgraded > 0
			and _ai_item_slots(world) > 0
			and world.economy.spent[World.RED] > 0
		),
		"the live AI upgrades towers and buys items through the real adapters"
	)
	check.call(
		world.ai_heroes.total_skills_cast > 0,
		"AI heroes cast through the shared auto-cast path inside a real match"
	)
	check.call(
		world._ai_roster().size() <= ROSTER_CAP and world.economy.is_balanced(),
		"the funded live match keeps the roster cap and reconciles the ledger"
	)
	_finish_match(check, world)


func _finish_match(check: Callable, world: World) -> void:
	# The funded window can already have produced a result; only force the win
	# (source-style: drop the shield, leave one HP) when the match is still live.
	if world.is_running():
		_force_red_win(world)
	check.call(world.winner == World.RED, "a live AI match resolves in the AI's favour")
	var gold_at_result: int = world.economy.gold[World.RED]
	var ai_ticks_at_result: int = world.ai_controller.ticks
	var built_at_result: int = world.ai_build.total_built
	for _tick in range(FREEZE_TICKS):
		world.step_tick()
	check.call(
		(
			world.ai_controller.ticks == ai_ticks_at_result
			and world.ai_build.total_built == built_at_result
			and world.economy.gold[World.RED] == gold_at_result
		),
		"the resolved match freezes the AI clock, counters and purse"
	)
	check.call(world.economy.is_balanced(), "the resolved match still reconciles the ledger")


func _force_red_win(world: World) -> void:
	# Same shape as the existing result tests: strip the shield, leave one HP and
	# let a red unit land the blow through the production damage path.
	var nexus = world.nexuses[World.BLUE]
	nexus.shield_active = false
	nexus.shield = 0
	nexus.hp = 1
	var attacker: UnitState = _red_attacker(world)
	if attacker == null:
		return
	attacker.position = nexus.position - Vector2(20, 0)
	world.apply_hit(attacker.id, nexus.id)


func _red_attacker(world: World) -> UnitState:
	# A funded live match can sit at the unit cap, so reuse a red unit when one
	# exists and only spawn a free one when the field is empty.
	for unit in world.units:
		if unit.alive and unit.team == World.RED:
			return unit
	return world.spawn_unit(GOBLIN, World.RED, 1)


func _switch_off(check: Callable) -> void:
	var world := World.new()
	world.configure_level(1)
	world.setup_arena()
	for _tick in range(IDLE_TICKS):
		world.step_tick()
	check.call(
		not world.ai_enabled and world.ai_controller.ticks == 0,
		"the AI switch starts off and the controller stays idle"
	)
	check.call(
		(
			world.ai_build.total_built == 0
			and world.economy.spent[World.RED] == 0
			and _red_towers(world) == 0
		),
		"with the switch off the red side never transacts"
	)
	check.call(world.economy.is_balanced(), "an idle red side still reconciles the ledger")


func _elite_hard(check: Callable) -> void:
	var world := _armed_world(ELITE_LEVEL, "hard", MATCH_SEED + 2)
	check.call(
		(
			world.difficulty == "hard"
			and world.enemy_scaling_enabled
			and world.enemy_hp_mult > 1.0
			and world.enemy_damage_mult > 1.0
		),
		"hard mode scales the enemy side while the AI plays red"
	)
	check.call(
		(
			world.ai_controller.policy.interval() == 9
			and world.ai_controller.policy.action_budget() == 3
		),
		"level 54 reaches the elite schedule: nine-tick think, three actions"
	)
	var negative_gold := 0
	for _tick in range(ELITE_TICKS):
		world.step_tick()
		if world.economy.gold[World.RED] < 0:
			negative_gold += 1
	check.call(negative_gold == 0, "the elite AI purse never goes negative")
	check.call(
		world.ai_build.total_built > 0 and world.economy.spent[World.RED] > 0,
		"the elite AI transacts under hard-mode scaling"
	)
	check.call(
		world.ai_controller.steps_attempted > world.ai_controller.think_ticks,
		"elite think ticks chain more than one priority"
	)
	check.call(
		world.economy.is_balanced() and world.ai_controller.ticks == world.tick_count,
		"the elite hard-mode match reconciles and stays on the match clock"
	)


func _ai_fingerprint(world: World) -> Dictionary:
	return {
		"gold": world.economy.gold[World.RED],
		"spent": world.economy.spent[World.RED],
		"earned": world.economy.earned[World.RED],
		"built": world.ai_build.total_built,
		"upgraded": world.ai_upgrades.total_upgraded,
		"nexus_upgrades": world.ai_upgrades.total_nexus_upgrades,
		"hero_upgrades": world.ai_upgrades.total_hero_upgrades,
		"recruited": world.ai_draft.total_heroes_bought,
		"casts": world.ai_heroes.total_skills_cast,
		"roster": _ai_roster_ids(world),
		"towers": _red_tower_fingerprint(world),
		"target": world.ai_draft.purchase_target,
		"target_cost": world.ai_draft.purchase_target_cost,
		"think_timer": world.ai_controller.policy.think_timer,
		"think_ticks": world.ai_controller.think_ticks,
		"attempts": world.ai_controller.steps_attempted,
		"completed": world.ai_controller.steps_completed,
	}


func _ai_roster_ids(world: World) -> Array[int]:
	var ids: Array[int] = []
	for unit in world._ai_roster():
		var hero: HeroState = unit as HeroState
		if hero != null:
			ids.append(hero.id)
	return ids


func _red_tower_fingerprint(world: World) -> Array:
	var rows: Array = []
	for structure in world.structures:
		if not structure.alive or structure.team != World.RED:
			continue
		if structure.settings().structure_kind != "tower":
			continue
		(
			rows
			. append(
				[
					structure.id,
					structure.hp,
					structure.shield,
					structure.cooldown_ticks,
					structure.settings().level,
					int(structure.position.x),
					int(structure.position.y),
				]
			)
		)
	return rows


func _red_towers(world: World) -> int:
	var count := 0
	for structure in world.structures:
		if not structure.alive or structure.team != World.RED:
			continue
		if structure.settings().structure_kind == "tower":
			count += 1
	return count


func _ai_item_slots(world: World) -> int:
	var slots := 0
	for unit in world._ai_roster():
		var hero: HeroState = unit as HeroState
		if hero != null:
			slots += hero.items.used_slots()
	return slots
