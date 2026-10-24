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
	check.call(view.hero_anim.tracked() > 0, "Hero clocks were tracked while drawing")
	check.call(view.hero_projectile_draws > 0, "Source-baked hero projectiles were drawn")
	check.call(view.dynamic_map_draws > 0, "DynamicRenderer painted the live map")
	check.call(view.dynamic_map.draw_count > 0, "DynamicRenderer advanced and painted its state")
	if boss != null:
		check.call(view.boss_sprite_draws > 0, "The baked boss body was drawn")
	else:
		check.call(false, "The suite could not spawn a boss to draw")
	app.show_menu()
	await _settle(tree)


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


## Turn the boss each frame, flash it, and enrage it halfway so both facings, the hurt tint
## and the enrage label draw.
func _poke_boss(boss, frame: int) -> void:
	boss.direction = 1 if frame % 2 == 0 else -1
	boss.hurt_flash_timer = 4 if frame % 3 == 0 else 0
	boss.is_enraged = frame >= (FRAMES >> 1)


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
