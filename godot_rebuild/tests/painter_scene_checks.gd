extends RefCounted
## Layer 9bn: the painters run for real. `queue_redraw` defers `_draw` to the end of the
## frame, so the frames the scene suites already wait for draw the PrototypeView; this
## suite proves it with a draw counter, then fills the real PrototypeMatch scene with
## every kind of thing the baked art covers (all minion types on both teams, towers of
## each path, a selected tower and slot, a slowed and a wounded minion, fired towers) and
## lets a few dozen frames draw. A script error in any painter prints `SCRIPT ERROR`,
## which the native step fails on, so this is the first time those painters are exercised.

const MINIONS := "res://data/minions/"
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
	var towers := _towers(world)
	check.call(towers.size() >= 3, "The match holds blue towers to draw: %d" % towers.size())
	if not towers.is_empty():
		session.selected_id = towers[0].id
	session.selected_slot_id = _free_slot(world)
	var hero = null
	if not world.player_hero_ids.is_empty():
		hero = world.get_unit(int(world.player_hero_ids[0]))
	var drawn_before: int = view.draw_count
	for frame in range(FRAMES):
		for _tick in range(TICKS_PER_FRAME):
			world.step_tick()
		_poke(world, towers, frame)
		if hero != null:
			_poke_hero(session, hero, towers, frame)
		await tree.process_frame
	check.call(
		view.draw_count >= drawn_before + (FRAMES >> 1),
		"The populated match drew %d frames" % (view.draw_count - drawn_before)
	)
	check.call(view.minion_anim.tracked() > 0, "Minion clocks were tracked while drawing")
	check.call(view.structure_anim.tracked() > 0, "Structure clocks were tracked while drawing")
	check.call(view.hero_anim.tracked() > 0, "Hero clocks were tracked while drawing")
	app.show_menu()
	await _settle(tree)


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
