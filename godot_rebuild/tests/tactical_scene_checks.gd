extends RefCounted
## Prototype scene lifecycle for the migrated tactical command layer.
##
## Proves the ported manager is actually wired into the playable scene: the
## source keys (G/F/T/C/B/D) and the side-panel style buttons reach the session
## queue, the queue reaches `TacticalCommandManager` before the tick, the orders
## move the real hero inside `step_tick`, a HOLD keeps re-issuing while a TAP
## keeps its 600-tick duration, pause releases every hold like `main.py`, and the
## view draws the gather marker / feedback banner without mutating state.

const Tactical = preload("res://scripts/match/tactical_commands.gd")


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var baseline := tree.get_node_count()
	app.start_prototype()
	await _settle(tree)
	var screen = app.current_screen
	var session = screen.simulation
	var world = session.world
	session.set_physics_process(false)
	var tactical = world.tactical
	var hero = world.blue_hero()
	check.call(hero != null and hero.alive, "tactical scene starts with a blue hero")
	check.call(tactical.world == world, "the match world owns the tactical manager")

	# ── the source side-panel box, with its visibility rules ──
	var bar = screen.get_node("HUD/TacticalBar")
	check.call(bar != null, "tactical command bar exists")
	check.call(bar.get_child_count() == 6, "bar holds the title and the five source orders")
	var gather_button = bar.get_node("TacticalGather")
	var tower_button = bar.get_node("TacticalProtectTower")
	var castle_button = bar.get_node("TacticalProtectCastle")
	var boss_button = bar.get_node("TacticalAttackBoss")
	var dealer_button = bar.get_node("TacticalAttackDamageDealer")
	screen._process(0.0)
	check.call(gather_button.visible and not gather_button.disabled, "GATHER is ready")
	check.call(castle_button.visible, "PROTECT CASTLE is ready")
	check.call(not boss_button.visible, "ATTACK BOSS stays hidden without a boss")
	check.call(
		not dealer_button.visible, "ATTACK DMG DEALER stays hidden without an AI-owned red hero"
	)
	check.call(
		gather_button.tooltip_text == "Semua hero kumpul & serang bersama",
		"panel tooltips copy the source description"
	)

	# ── keyboard TAP: full duration, source feedback and sound ──
	_key(screen, KEY_G, true)
	check.call(session.tactical_queue.size() == 1, "G queues one tactical hold")
	session._physics_process(1.0 / 60.0)
	check.call(tactical.active_command == Tactical.GATHER, "G issues GATHER inside the tick")
	check.call(
		tactical.feedback_text == "GATHER! 1 heroes regrouping!",
		"GATHER feedback text matches the source"
	)
	check.call(tactical.sound_history.has("ui_click"), "GATHER plays the source ui_click")
	check.call(
		tactical.has_gather_point and tactical.gather_point() == Vector2(640, 360),
		"a single hero gathers at the source map-center fallback"
	)
	check.call(hero.has_destination and hero.destination == Vector2(675, 360), "GATHER spread ring")
	_key(screen, KEY_G, false)
	session._physics_process(1.0 / 60.0)
	check.call(tactical.held_command.is_empty(), "the key release disarms the hold")
	check.call(
		tactical.command_timer == Tactical.COMMAND_TICKS - 1,
		"a tap keeps the full 600-tick duration"
	)

	# ── the view draws the marker and the banner without touching state ──
	var view = screen.get_node("Arena")
	var marker_before: int = tactical.gather_point_timer
	var feedback_before: int = tactical.feedback_timer
	check.call(tactical.marker_visible() and tactical.feedback_timer > 0, "marker and banner live")
	view.queue_redraw()
	await _settle(tree)
	check.call(
		tactical.gather_point_timer == marker_before and tactical.feedback_timer == feedback_before,
		"drawing the tactical marker and banner never mutates match state"
	)

	# ── HOLD: re-issued every 30 ticks so the duration never lapses ──
	_key(screen, KEY_C, true)
	session._physics_process(1.0 / 60.0)
	check.call(
		(
			tactical.active_command == Tactical.PROTECT_CASTLE
			and tactical.held_command == Tactical.PROTECT_CASTLE
		),
		"C holds PROTECT CASTLE"
	)
	check.call(
		tactical.status_text().ends_with("[HOLD]"), "get_status_text carries the source HOLD tag"
	)
	var sounds_before: int = tactical.sound_history.size()
	for _tick in range(120):
		session._physics_process(1.0 / 60.0)
	check.call(tactical.hold_elapsed == 121, "hold_elapsed counts every held tick")
	check.call(
		tactical.command_timer >= Tactical.COMMAND_TICKS - Tactical.COOLDOWN_MAX,
		"a held order is re-issued before its 600-tick duration lapses"
	)
	check.call(
		tactical.sound_history.size() == sounds_before,
		"silent HOLD refreshes never replay the order sound"
	)
	_key(screen, KEY_C, false)
	session._physics_process(1.0 / 60.0)
	check.call(
		tactical.held_command.is_empty() and tactical.command_timer <= Tactical.HOLD_RELEASE_TAIL,
		"releasing a long hold only keeps the 30-tick tail"
	)

	# ── the order really drives the hero inside step_tick ──
	hero.position = Vector2(640, 360)
	hero.has_destination = false
	var castle = world.nexuses[0]
	var before_walk: float = hero.position.distance_to(castle.position)
	_key(screen, KEY_C, true)
	for _tick in range(30):
		session._physics_process(1.0 / 60.0)
	check.call(
		hero.position.distance_to(castle.position) < before_walk,
		"PROTECT CASTLE walks the hero to the castle ring"
	)
	screen._process(0.0)
	check.call(
		String(castle_button.text).ends_with("HOLD"), "the held order is highlighted in the panel"
	)
	# Panel buttons are the mobile source path: press starts, release ends.
	castle_button.button_up.emit()
	session._physics_process(1.0 / 60.0)
	check.call(tactical.held_command.is_empty(), "the panel release disarms the hold")
	castle_button.button_down.emit()
	session._physics_process(1.0 / 60.0)
	check.call(
		tactical.held_command == Tactical.PROTECT_CASTLE, "the panel press starts a hold again"
	)
	_key(screen, KEY_C, false)
	session._physics_process(1.0 / 60.0)

	# ── refusal feedback, then the armed hold fires when the tower appears ──
	# Lapse the previous order first so the refusal is the only active state.
	tactical.command_timer = 1
	tactical.cooldown = 0
	session._physics_process(1.0 / 60.0)
	check.call(tactical.active_command.is_empty(), "the previous order lapsed")
	_key(screen, KEY_T, true)
	session._physics_process(1.0 / 60.0)
	check.call(
		tactical.active_command != Tactical.PROTECT_TOWER,
		"PROTECT TOWER is refused while no blue tower stands"
	)
	check.call(
		tactical.feedback_text == "No tower to protect!", "the source refusal feedback is shown"
	)
	check.call(
		tactical.held_command == Tactical.PROTECT_TOWER, "a refused order stays armed while held"
	)
	check.call(session.last_action.contains("belum"), "the HUD reports the refused order")
	check.call(tower_button.visible, "PROTECT TOWER stays visible while a blue hero lives")
	var slot := -1
	for entry in world.slots:
		if entry.team == 0 and entry.structure_id == -1:
			slot = entry.id
			break
	world.economy.gold[0] += 500
	check.call(world.build_tower(0, slot), "a blue tower is built for the protect proof")
	for _tick in range(20):
		session._physics_process(1.0 / 60.0)
	check.call(
		tactical.active_command == Tactical.PROTECT_TOWER,
		"the armed hold fires as soon as its precondition appears"
	)
	check.call(
		tactical.sound_history.back() == "ui_click",
		"the first successful refresh announces itself once"
	)
	check.call(
		tactical.command_target_id == world.get_slot(slot).structure_id,
		"PROTECT TOWER locks the only blue tower"
	)
	_key(screen, KEY_T, false)
	session._physics_process(1.0 / 60.0)

	# ── ATTACK BOSS through the real boss spawn path ──
	# The 30-tick cooldown is a source gate; clear it so this proof exercises the
	# boss branch instead of the pacing.
	tactical.cooldown = 0
	var boss_rows: Dictionary = world.boss_table.get("bosses", {})
	world.pending_mini_bosses.append({"wave": 1, "boss_type": String(boss_rows.keys()[0])})
	check.call(world._try_spawn_pending_mini_boss(), "a mini boss spawns for the attack order")
	screen._process(0.0)
	check.call(boss_button.visible and not boss_button.disabled, "ATTACK BOSS appears with a boss")
	_key(screen, KEY_B, true)
	session._physics_process(1.0 / 60.0)
	check.call(
		tactical.active_command == Tactical.ATTACK_BOSS, "B issues ATTACK BOSS on the live boss"
	)
	check.call(hero.follow_id == world.active_boss.id, "the hero locks the boss as follow target")
	check.call(tactical.sound_history.back() == "hero_skill", "ATTACK BOSS plays hero_skill")
	check.call(
		(
			tactical.feedback_text
			== "ATTACK BOSS! All heroes attack %s!" % world.active_boss.display_name
		),
		"ATTACK BOSS feedback names the boss"
	)
	_key(screen, KEY_B, false)
	session._physics_process(1.0 / 60.0)

	# ── pause releases every hold, exactly like main.py ──
	_key(screen, KEY_G, true)
	session._physics_process(1.0 / 60.0)
	check.call(tactical.held_command == Tactical.GATHER, "G is held before the pause")
	screen.pause_match()
	check.call(tactical.held_command.is_empty(), "pause releases every held order")
	check.call(session.tactical_queue.is_empty(), "pause drops queued tactical input")
	check.call(not session.request_tactical_hold(Tactical.GATHER), "pause refuses new orders")
	screen.resume_match()
	check.call(not tree.paused, "resume continues the match")

	# ── a finished match refuses orders ──
	world.winner = world.RED
	session._physics_process(1.0 / 60.0)
	check.call(
		not session.request_tactical_hold(Tactical.GATHER), "a finished match refuses orders"
	)
	check.call(
		not world.tactical_hold(Tactical.GATHER, Vector2.ZERO, false, -1, false, -1),
		"the world guard refuses an order after the result"
	)
	check.call(world.transaction_error == "finished", "the refusal names the finished match")
	var old_id: int = screen.get_instance_id()
	screen.get_node("%RestartButton").pressed.emit()
	await _settle(tree)
	check.call(not is_instance_id_valid(old_id), "the tactical scene is disposed on restart")
	var fresh = app.current_screen.simulation.world
	check.call(
		fresh.tactical.active_command.is_empty() and fresh.tactical.held_command.is_empty(),
		"restart resets the tactical manager"
	)
	app.show_menu()
	await _settle(tree)
	check.call(tree.get_node_count() == baseline, "tactical lifecycle leaves no orphan nodes")


func _key(screen: Node, keycode: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = keycode
	event.pressed = pressed
	screen._unhandled_input(event)


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
