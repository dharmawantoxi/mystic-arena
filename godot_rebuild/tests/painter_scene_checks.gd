extends RefCounted
## Layer 9bn: the painters run for real. `queue_redraw` defers `_draw` to the end of the
## frame, so the frames the scene suites already wait for draw the PrototypeView; this
## suite proves it with a draw counter, then fills the real PrototypeMatch scene with
## every kind of thing the baked art covers (all minion types on both teams, towers of
## each path, selected towers/slots, slowed/wounded minions, slash/death frames, and fired towers)
## lets a few dozen frames draw. A script error in any painter prints `SCRIPT ERROR`,
## which the native step fails on, so this is the first time those painters are exercised.

const Projectile = preload("res://scripts/combat/projectile_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const MINIONS := "res://data/minions/"
const SHOT_KINDS := ["normal", "cannon", "ice", "mage"]
const BOSS_TYPE := "abaddon"
const TYPES := ["goblin", "orc", "troll", "undead", "dark_rider"]
const PATHS := ["cannon", "ice", "mage"]
const FRAMES := 16
const TICKS_PER_FRAME := 6


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var view = screen.get_node("Arena")
	var world = session.world
	session.set_physics_process(false)
	var first_draw: int = view.draw_count
	await _settle(tree)
	check.call(view.draw_count > first_draw, "PrototypeView._draw runs in the headless scene")
	if view.draw_count <= first_draw:
		app.show_menu()
		await _settle(tree)
		return
	world.economy.gold[0] = 90000
	_populate(world)
	var fx_pair := _seed_minion_fx(world)
	var towers := _towers(world)
	check.call(towers.size() >= 3, "The match holds blue towers to draw: %d" % towers.size())
	if not towers.is_empty():
		session.selected_id = towers[0].id
	session.selected_slot_id = _free_slot(world)
	_seed_shots(world, towers)
	var boss = _seed_boss(world)
	var hero = null
	if not world.player_hero_ids.is_empty():
		hero = world.get_unit(int(world.player_hero_ids[0]))
	var projectile_seeded := _seed_hero_projectile(world, hero)
	check.call(projectile_seeded, "The painter fixture seeds a hero projectile")
	await _settle(tree)
	var fx_kill_landed := false
	if fx_pair.size() == 2:
		var striker = fx_pair[0]
		var victim = fx_pair[1]
		victim.hp = 1.0
		fx_kill_landed = world.apply_hit(striker.id, victim.id)
		if fx_kill_landed:
			world.step_tick()
	check.call(fx_kill_landed, "The painter fixture lands a minion-killing swing")
	var drawn_before: int = view.draw_count
	for frame in range(FRAMES):
		for _tick in range(TICKS_PER_FRAME):
			world.step_tick()
		_poke(world, towers, frame)
		if hero != null:
			_poke_hero(session, hero, towers, frame)
		if boss != null:
			_poke_boss(boss, frame)
		await tree.process_frame
	check.call(
		view.draw_count >= drawn_before + (FRAMES >> 1),
		"The populated match drew %d frames" % (view.draw_count - drawn_before)
	)
	check.call(view.minion_anim.tracked() > 0, "Minion clocks were tracked while drawing")
	check.call(view.minion_slash_draws > 0, "The source-baked minion slash path was drawn")
	check.call(view.minion_death_draws > 0, "The source-baked minion death path was drawn")
	check.call(view.structure_anim.tracked() > 0, "Structure clocks were tracked while drawing")
	check.call(view.tower_fx_draws > 0, "Source tower FX ops reached the painter")
	check.call(view.tower_range_fx_draws > 0, "The selected tower painted its source range circles")
	check.call(view.tower_muzzle_fx_draws > 0, "A firing archer painted its source muzzle glow")
	check.call(view.hero_anim.tracked() > 0, "Hero clocks were tracked while drawing")
	check.call(view.hero_projectile_draws > 0, "Source-baked hero projectiles were drawn")
	check.call(view.dynamic_map_draws > 0, "DynamicRenderer painted the live map")
	check.call(view.dynamic_map.draw_count > 0, "DynamicRenderer advanced and painted its state")
	if boss != null:
		check.call(view.boss_sprite_draws > 0, "The baked boss body was drawn")
		var painted: Array = view.boss_pose_draws.keys()
		check.call(
			painted.any(func(pose): return String(pose).begins_with("atk")),
			"Boss attack poses drew"
		)
		check.call(
			painted.any(func(pose): return String(pose).begins_with("skill_q_")),
			"Boss Q skill poses drew"
		)
		check.call(
			painted.any(func(pose): return String(pose).begins_with("skill_w_")),
			"Boss W skill poses drew"
		)
		await _check_realm(tree, view, boss, check)
		await _check_urgharun_enrage(tree, view, boss, check)
		await _check_boss_auras(tree, view, boss, check)
		await _check_urgharun_basic_attack(tree, view, boss, check)
		await _check_boss_debuff_fx(tree, view, boss, check)
		await _check_fallback_debuff_fx(tree, view, world, hero, check)
	else:
		check.call(false, "The suite could not spawn a boss to draw")
	app.show_menu()
	await _settle(tree)


## Layer 9bq3: the live scene paints nyxareth's screen-wide ultimate realm under the body,
## and no other boss skill paints one. The boss only wears nyxareth's type for these frames;
## no tick runs, so its AI never sees the swap.
func _check_realm(tree: SceneTree, view, boss, check: Callable) -> void:
	check.call(view.boss_screen_layer_draws == 0, "No other boss skill painted a screen-wide layer")
	var source_type: String = boss.boss_type
	boss.boss_type = "nyxareth"
	boss.timer = 0
	boss.active_skill = "4"
	boss.active_skill_timer = 60
	var painted_before: int = view.boss_screen_layer_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_screen_layer_draws > painted_before:
			break
	check.call(
		view.boss_screen_layer_draws > painted_before,
		"Nyxareth's ultimate painted its screen-wide realm"
	)
	check.call(
		view.boss_pose_draws.keys().any(func(pose): return String(pose).begins_with("skill_4_")),
		"Nyxareth's baked ultimate pose drew under the realm"
	)
	boss.boss_type = source_type
	boss.active_skill = ""
	boss.active_skill_timer = 0


## Layer 9bq4/9bq5: the live scene paints urgharun's R ground layer under its baked body and
## its foreground enrage layer over it, on every phase of the source cast window. The boss
## only wears urgharun's type for these frames; no tick runs, so its AI never sees the swap.
func _check_urgharun_enrage(tree: SceneTree, view, boss, check: Callable) -> void:
	check.call(
		(
			view.boss_enrage_fx_draws == 0
			and view.boss_enrage_ground_draws == 0
			and view.boss_aura_fx_draws == 0
			and view.boss_skill_ground_draws == 0
			and view.boss_skill_fg_draws == 0
			and view.boss_basic_attack_fg_draws == 0
			and view.boss_debuff_fx_draws == 0
		),
		"No other boss skill painted an urgharun FX layer"
	)
	var source_type: String = boss.boss_type
	var source_skill: String = boss.active_skill
	var source_timer: int = boss.active_skill_timer
	boss.boss_type = "urgharun"
	boss.timer = 0
	# Layer 9bq6: LAYER 1 (fury aura + ground ring) draws on every urgharun frame, casting or
	# not, and the Q cast adds its ground rings and debris.
	boss.active_skill = ""
	var aura_before: int = view.boss_aura_fx_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_aura_fx_draws > aura_before:
			break
	check.call(
		view.boss_aura_fx_draws > aura_before,
		"Urgharun painted its fury aura and ground ring without a cast"
	)
	check.call(view.boss_aura_fx_ops > 0, "The LAYER 1 ops reached the painter")
	boss.active_skill = "q"
	var q_ground_before: int = view.boss_skill_ground_draws
	var q_fg_before: int = view.boss_skill_fg_draws
	for phase in [55, 30, 12, 1]:
		boss.active_skill_timer = int(phase)
		for _frame in range(4):
			await tree.process_frame
			if view.boss_skill_fg_draws > q_fg_before:
				break
	check.call(
		view.boss_skill_ground_draws > q_ground_before,
		"Urgharun's Q painted its ground shockwave layer"
	)
	check.call(
		view.boss_skill_fg_draws > q_fg_before and view.boss_skill_fg_ops > 0,
		"Urgharun's Q painted its debris foreground layer"
	)
	boss.active_skill = "r"
	var phases := [80, 60, 40, 20, 1]
	var painted := 0
	var ground_painted := 0
	var op_deltas: Array = []
	var ground_deltas: Array = []
	for phase in phases:
		boss.active_skill_timer = int(phase)
		var draws_before: int = view.boss_enrage_fx_draws
		var ops_before: int = view.boss_enrage_fx_ops
		var ground_before: int = view.boss_enrage_ground_draws
		var ground_ops_before: int = view.boss_enrage_ground_ops
		for _frame in range(6):
			await tree.process_frame
			if view.boss_enrage_fx_draws > draws_before:
				break
		if view.boss_enrage_fx_draws > draws_before:
			painted += 1
			op_deltas.append(view.boss_enrage_fx_ops - ops_before)
		if view.boss_enrage_ground_draws > ground_before:
			ground_painted += 1
			ground_deltas.append(view.boss_enrage_ground_ops - ground_ops_before)
	check.call(
		painted == phases.size(),
		"Urgharun's R painted its enrage layer on %d/%d cast phases" % [painted, phases.size()]
	)
	check.call(
		(
			op_deltas.size() == phases.size()
			and op_deltas.all(func(count): return int(count) > 0 and int(count) % 68 == 0)
		),
		"The live layer carries the source's 68 ops at every cast phase"
	)
	check.call(
		ground_painted == phases.size(),
		(
			"Urgharun's R painted its ground layer on %d/%d cast phases"
			% [ground_painted, phases.size()]
		)
	)
	check.call(
		(
			ground_deltas.size() == phases.size()
			and ground_deltas.all(func(count): return int(count) > 0 and int(count) % 26 == 0)
		),
		"The live ground layer carries the source's 26 ops at every cast phase"
	)
	boss.boss_type = source_type
	boss.active_skill = source_skill
	boss.active_skill_timer = source_timer


## Layer 9bq7: the live scene paints the three cached `Boss.draw` auras - the ability aura while
## `ability_active`, the enrage aura once `is_enraged` and the extra true-boss aura - and each one
## stays off while its source gate is closed. No tick runs, so the sim never sees the swaps.
func _check_boss_auras(tree: SceneTree, view, boss, check: Callable) -> void:
	var source_class: String = boss.boss_class
	var source_range: float = boss.ability_range
	var source_entrance: Color = boss.entrance_color
	var source_ability: bool = boss.ability_active
	var source_enraged: bool = boss.is_enraged
	var source_enrage_pulse: float = boss.enrage_pulse
	boss.ability_active = false
	var ability_closed: int = view.boss_ability_aura_draws
	for _frame in range(4):
		await tree.process_frame
	check.call(
		view.boss_ability_aura_draws == ability_closed,
		"No ability aura painted while the ability gate was closed"
	)
	boss.ability_active = true
	boss.ability_range = 350.0
	boss.entrance_color = Color8(255, 200, 130)
	var ability_before: int = view.boss_ability_aura_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_ability_aura_draws > ability_before:
			break
	check.call(
		view.boss_ability_aura_draws > ability_before and view.boss_ability_aura_ops > 0,
		"The ability aura painted its entrance-coloured rings"
	)
	boss.ability_active = source_ability
	boss.ability_range = source_range
	boss.entrance_color = source_entrance
	boss.is_enraged = false
	var enrage_closed: int = view.boss_enrage_aura_draws
	for _frame in range(4):
		await tree.process_frame
	check.call(
		view.boss_enrage_aura_draws == enrage_closed,
		"No enrage aura painted before the enrage transition"
	)
	boss.is_enraged = true
	boss.enrage_pulse = 0.0
	var enrage_before: int = view.boss_enrage_aura_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_enrage_aura_draws > enrage_before:
			break
	check.call(
		view.boss_enrage_aura_draws > enrage_before and view.boss_enrage_aura_ops > 0,
		"The enrage aura painted its width-2 rings"
	)
	boss.is_enraged = source_enraged
	boss.enrage_pulse = source_enrage_pulse
	boss.boss_class = "mini"
	var true_closed: int = view.boss_true_aura_draws
	for _frame in range(4):
		await tree.process_frame
	check.call(view.boss_true_aura_draws == true_closed, "Only a true boss paints the extra aura")
	boss.boss_class = "true"
	var true_before: int = view.boss_true_aura_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_true_aura_draws > true_before:
			break
	check.call(
		view.boss_true_aura_draws > true_before and view.boss_true_aura_ops > 0,
		"The true-boss aura painted its filled rings"
	)
	boss.boss_class = source_class


## Layer 9bq8: the live scene arms urgharun's swing clock from `boss.timer`/`attack_cooldown`
## and paints `_draw_basic_attack_fx` while no skill is casting - the source gate is
## `attacking and not active_skill`. No tick runs, so the boss keeps the timer set here.
func _check_urgharun_basic_attack(tree: SceneTree, view, boss, check: Callable) -> void:
	var source_type: String = boss.boss_type
	var source_skill: String = boss.active_skill
	var source_timer: int = boss.timer
	var source_cooldown: int = boss.attack_cooldown
	boss.boss_type = "urgharun"
	boss.active_skill = ""
	boss.attack_cooldown = 38
	# `near_max = timer >= cooldown - 1` arms the swing on the next painted frame.
	boss.timer = 37
	var draws_before: int = view.boss_basic_attack_fg_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_basic_attack_fg_draws > draws_before:
			break
	check.call(
		view.boss_basic_attack_fg_draws > draws_before,
		"Urgharun's armed basic attack painted its claw-swing layer"
	)
	check.call(view.boss_basic_attack_fg_ops > 0, "The basic-attack ops reached the painter")
	# The clock keeps ticking during a cast (the source advances it before choosing a pose) but
	# the FX layer is gated on `not active_skill`.
	boss.active_skill = "q"
	boss.active_skill_timer = 30
	var gated_before: int = view.boss_basic_attack_fg_draws
	for _frame in range(4):
		await tree.process_frame
	check.call(
		view.boss_basic_attack_fg_draws == gated_before,
		"A skill cast suppresses the basic-attack FX in the live scene"
	)
	boss.boss_type = source_type
	boss.active_skill = source_skill
	boss.timer = source_timer
	boss.attack_cooldown = source_cooldown


## Layer 9bq9: the live scene paints the debuff indicator (`Boss.draw` slot after the auras) as
## soon as one debuff timer runs, and stops once every timer is cleared.
func _check_boss_debuff_fx(tree: SceneTree, view, boss, check: Callable) -> void:
	var source_slow: int = boss.slow_timer
	var source_atk_slow: int = boss.atk_slow_timer
	var source_skill_down: int = boss.skill_down_timer
	var source_anti_heal: int = boss.anti_heal_timer
	var source_burn: int = boss.burn_timer
	boss.slow_timer = 0
	boss.atk_slow_timer = 0
	boss.skill_down_timer = 0
	boss.anti_heal_timer = 0
	boss.burn_timer = 0
	var clean_before: int = view.boss_debuff_fx_draws
	for _frame in range(4):
		await tree.process_frame
	check.call(
		view.boss_debuff_fx_draws == clean_before, "An undebuffed boss painted no debuff indicator"
	)
	boss.slow_timer = 30
	boss.burn_timer = 20
	var debuffed_before: int = view.boss_debuff_fx_draws
	for _frame in range(6):
		await tree.process_frame
		if view.boss_debuff_fx_draws > debuffed_before:
			break
	check.call(
		view.boss_debuff_fx_draws > debuffed_before,
		"A slowed and burning boss painted its debuff indicator"
	)
	check.call(view.boss_debuff_fx_ops > 0, "The debuff ops reached the painter")
	boss.slow_timer = source_slow
	boss.atk_slow_timer = source_atk_slow
	boss.skill_down_timer = source_skill_down
	boss.anti_heal_timer = source_anti_heal
	boss.burn_timer = source_burn


## Layer 9bv13: with the atlas import forced off, the marker hero and plain-circle minion
## still paint the source tower-debuff indicator from their live timers.
func _check_fallback_debuff_fx(tree: SceneTree, view, world, hero, check: Callable) -> void:
	var saved: Array = []
	var minion = null
	for unit in world.units:
		(
			saved
			. append(
				[
					unit,
					unit.slow_timer,
					unit.atk_slow_timer,
					unit.skill_down_timer,
					unit.anti_heal_timer,
					unit.burn_timer,
				]
			)
		)
		unit.slow_timer = 0
		unit.atk_slow_timer = 0
		unit.skill_down_timer = 0
		unit.anti_heal_timer = 0
		unit.burn_timer = 0
		if minion == null and not unit.is_hero and unit.alive:
			minion = unit
	var chosen_hero = hero
	if chosen_hero == null:
		for unit in world.units:
			if unit.is_hero and unit.alive:
				chosen_hero = unit
				break
	var ready: bool = chosen_hero != null and minion != null and bool(chosen_hero.alive)
	check.call(ready, "The fallback scene has one live hero and one live minion")
	if ready:
		chosen_hero.slow_timer = 30
		chosen_hero.burn_timer = 20
		minion.slow_timer = 30
		minion.burn_timer = 20
		var hero_before: int = view.hero_debuff_fx_draws
		var minion_before: int = view.minion_debuff_fx_draws
		view.force_art_fallback = true
		for _frame in range(6):
			await tree.process_frame
			if (
				view.hero_debuff_fx_draws > hero_before
				and view.minion_debuff_fx_draws > minion_before
			):
				break
		check.call(
			view.hero_debuff_fx_draws > hero_before,
			"A marker hero painted the source debuff indicator"
		)
		check.call(
			view.minion_debuff_fx_draws > minion_before,
			"A plain-circle minion painted the source debuff indicator"
		)
		view.force_art_fallback = false
	for row in saved:
		var unit = row[0]
		unit.slow_timer = row[1]
		unit.atk_slow_timer = row[2]
		unit.skill_down_timer = row[3]
		unit.anti_heal_timer = row[4]
		unit.burn_timer = row[5]


func _seed_hero_projectile(world, hero) -> bool:
	if hero == null:
		return false
	var shooter: HeroState = hero as HeroState
	if shooter == null or not shooter.alive:
		return false
	var target = null
	for unit in world.units:
		if unit.alive and unit.team != shooter.team:
			target = unit
			break
	if target == null:
		return false
	world.hero_projectiles.clear()
	var origin: Vector2 = shooter.position + Vector2(0, -5)
	var projectile: Dictionary = {
		"source_id": shooter.id,
		"target_id": target.id,
		"team": shooter.team,
		"school": shooter.dmg_school,
		"hero_type": shooter.settings().id,
		"damage": int(shooter.damage),
		"is_crit": true,
		"position": origin,
		"origin": origin,
		"last_target": target.position,
		"age": 24,
		"impact": false,
		"active": true,
	}
	world.hero_projectiles.append(projectile)
	return true


func _seed_minion_fx(world) -> Array:
	var blue = null
	var red = null
	for unit in world.units:
		if unit.is_hero or not unit.alive:
			continue
		if unit.team == 0 and blue == null:
			blue = unit
		elif unit.team == 1 and red == null:
			red = unit
		if blue != null and red != null:
			break
	if blue == null or red == null:
		return []
	blue.position = Vector2(500, 360)
	red.position = Vector2(510, 360)
	blue.target_id = red.id
	red.target_id = blue.id
	blue.cooldown_ticks = 0
	red.cooldown_ticks = 0
	return [blue, red]


func _populate(world) -> void:
	for type_id in TYPES:
		var definition := load(MINIONS + type_id + ".tres")
		for team in [0, 1]:
			world.spawn_unit(definition, team, 1)
	var built := 0
	for slot in world.slots:
		if slot.team == 0 and slot.structure_id == -1 and built < 4:
			if world.build_tower(0, slot.id, "archer"):
				built += 1
	var index := 0
	for tower in _towers(world):
		if index < PATHS.size():
			world.upgrade_tower(tower.id, 1, PATHS[index])
		index += 1


## One shot of each bullet kind, both teams' colours, far enough from a red minion to stay in
## flight for several frames, so the baked bullets draw even when no tower has a target yet.
func _seed_shots(world, towers: Array) -> void:
	var target = null
	for unit in world.units:
		if unit.team == 1 and not unit.is_hero and unit.alive:
			target = unit
			break
	if towers.is_empty() or target == null:
		return
	for index in range(SHOT_KINDS.size()):
		var shot := Projectile.new()
		shot.id = 9000 + index
		shot.source_id = towers[0].id
		shot.target_id = target.id
		shot.team = index % 2
		shot.damage = 1
		shot.kind = SHOT_KINDS[index]
		shot.position = target.position + Vector2(-170.0 - 25.0 * index, -90.0 + 60.0 * index)
		world.projectiles.append(shot)


## A true boss past its entrance, so its baked body, bar and name plate draw.
func _seed_boss(world):
	var boss = world._spawn_boss(BOSS_TYPE)
	if boss != null:
		boss.entrance_timer = 0
	return boss


## Turn the boss and exercise idle/walk, attack and two source smart-skill families.
func _poke_boss(boss, frame: int) -> void:
	boss.direction = 1 if frame % 2 == 0 else -1
	boss.hurt_flash_timer = 4 if frame % 3 == 0 else 0
	boss.is_enraged = frame >= (FRAMES >> 1)
	boss.active_skill = ""
	boss.active_skill_timer = 0
	boss.timer = 0
	boss.moving_cached = frame < 4 and frame % 2 == 1
	if frame >= 4 and frame < 8:
		boss.timer = 30 - frame
	elif frame >= 8 and frame < 12:
		boss.active_skill = "q"
		boss.active_skill_timer = 30 - (frame - 8) * 6
	elif frame >= 12:
		boss.active_skill = "w"
		boss.active_skill_timer = 90 - (frame - 12) * 15


func _towers(world) -> Array:
	var found: Array = []
	for structure in world.structures:
		if structure.settings().structure_kind == "tower" and structure.team == 0:
			found.append(structure)
	return found


func _free_slot(world) -> int:
	for slot in world.slots:
		if slot.structure_id == -1:
			return slot.id
	return -1


## Wound and slow a minion and fire the towers so the hurt, slow and flash paths draw.
func _poke(world, towers: Array, frame: int) -> void:
	for unit in world.units:
		if not unit.is_hero and unit.alive:
			unit.slow_timer = 60 if frame % 2 == 0 else 0
			unit.hp = maxf(1.0, unit.hp - 1.0)
			unit.cooldown_ticks = 0 if frame % 3 == 0 else 20
	for tower in towers:
		tower.cooldown_ticks = 0 if frame % 4 == 0 else 30


## Select the hero on odd frames (ring and range disc), swing it, and pass level 5 halfway so
## both badge layouts (stars, then `x7`) draw.
func _poke_hero(session, hero, towers: Array, frame: int) -> void:
	session.selected_id = hero.id if frame % 2 == 1 or towers.is_empty() else towers[0].id
	hero.level = 7 if frame >= (FRAMES >> 1) else 1
	hero.attack_timer = 14 if frame % 3 == 0 else hero.attack_timer


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
