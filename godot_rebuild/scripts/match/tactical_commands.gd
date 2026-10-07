# gdlint:disable=max-public-methods
extends RefCounted
## Port of `tactical_commands.py::TacticalCommandManager`: the player (blue)
## order layer GATHER / PROTECT TOWER / PROTECT CASTLE / ATTACK BOSS / ATTACK
## DAMAGE DEALER, including the HOLD mode driven by the desktop keys G/F/T/C/B/D
## (`_core.py::InputHandler.handle_key`/`handle_key_up`) and the mobile side
## panel (`mobile/hud.py::TACTICAL_ACTIONS`, `main.py` press/release tracking).
## `Game.update` calls `tactical.update()` after the reward pass and right
## before `self.ai.update(...)`.
##
## Nothing here is invented: timers, spreads, clamps, threat scores, feedback
## strings, sounds and every quirk (stale `command_target` on GATHER,
## `_try_gather_push` leaving `target`/`destination_auto` alone, the `9999`
## nearest-target seed, the boss counting double in `_count_enemies_near`) are
## copied. The world is duck-typed like `ai_hero_control.gd`: `is_running()`,
## `units`, `structures`, `nexuses`, `active_boss`, `wave_count`, `get_unit()`,
## `move_to(hero, point, auto)` and optionally `_ai_roster()` (= `game.ai.heroes`).
## Arithmetic runs in doubles and becomes a `Vector2` (f32) only at the final call.

const StructureState = preload("res://scripts/combat/structure_state.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const LaneLayout = preload("res://scripts/data/lane_layout.gd")

const GATHER := "gather"
const PROTECT_TOWER := "protect_tower"
const PROTECT_CASTLE := "protect_castle"
const ATTACK_BOSS := "attack_boss"
const ATTACK_DAMAGE_DEALER := "attack_damage_dealer"
const COMMANDS := [GATHER, PROTECT_TOWER, PROTECT_CASTLE, ATTACK_BOSS, ATTACK_DAMAGE_DEALER]
const BLUE := 0
const RED := 1
# tactical_commands.py module constants.
const HOLD_TAP_MAX_FRAMES := 20
const HOLD_RELEASE_TAIL := 30
const GATHER_PUSH_DELAY_FRAMES := 240
const COOLDOWN_MAX := 30
# `self.cooldown = max(self.cooldown, self.cooldown_max // 2)` on a failed issue.
const HOLD_RETRY_COOLDOWN := 15
const COMMAND_TICKS := 600
# `elif self.command_timer == 300:` - exactly half of the command duration.
const GATHER_PUSH_TIMER := 300
const MARKER_TICKS := 150
const FEEDBACK_TICKS := 180
const GATHER_ARRIVE_PX := 100.0
const GATHER_ARRIVED_RATIO := 0.6
const GATHER_MID_MIX := 0.35
const GATHER_MIN_X := 200.0
const GATHER_MAX_X := 1080.0
const GATHER_MIN_Y := 100.0
const GATHER_MAX_Y := 620.0
const GATHER_FALLBACK_X := 640.0
const GATHER_FALLBACK_Y := 360.0
const CASTLE_CLAMP_MIN_X := 50.0
const CASTLE_CLAMP_MAX_X := 1230.0
const CASTLE_CLAMP_MIN_Y := 50.0
const CASTLE_CLAMP_MAX_Y := 670.0
const ARENA_SIZE := Vector2(1280, 720)
const NEAREST_TARGET_SEED := 9999.0
const THREAT_SCAN_RADIUS := 220.0
const PROTECT_SCAN_RADIUS := 250.0
const CASTLE_SCAN_RADIUS := 300.0
const OUTER_TOWER_X := 400.0
const AUTO_CHECK_TICKS := 90
const AUTO_CASTLE_HP := 0.4
const AUTO_CASTLE_ENEMIES := 2
const AUTO_TOWER_HP := 0.6
const AUTO_TOWER_ENEMIES := 2
const AUTO_TOWER_SWARM := 4
const AUTO_BOSS_HP := 0.8
const AUTO_BOSS_WAVE := 11
const AUTO_BOSS_ROLL := 0.2
const NAME_LIMIT := 15
const SOUND_HISTORY_LIMIT := 16
const STATUS_WAITING := "menunggu syarat"  # get_status_text HOLD placeholder

var world: Object = null
# `game.selected_hero` and `game.mouse_x/mouse_y` are screen state, so the
# session pushes them in instead of the manager reaching into the scene.
var selected_hero_id := -1
var mouse_position := Vector2.ZERO

var active_command := ""
var command_timer := 0
var command_target_id := -1
var gather_x := 0.0
var gather_y := 0.0
var has_gather_point := false
var gather_point_timer := 0
var feedback_text := ""
var feedback_timer := 0
var feedback_color := Color(1, 1, 1)
var cooldown := 0

var held_command := ""
var hold_point := Vector2.ZERO
var hold_has_point := false
var hold_tower_id := -1
var hold_follow_mouse := false
var hold_elapsed := 0
var hold_has_fired := false
var gather_push_fired := false
var auto_check_timer := 0
# Source `_auto_evaluate_protect` rolls `random.random() < 0.2`. The native
# stream is seeded (or overridden) so replays and tests stay deterministic;
# the Godot stream is not claimed identical to CPython's Mersenne Twister.
var auto_roll_override: Callable
var auto_rng := RandomNumberGenerator.new()
# Parity seam for the migrated audio facade (`ui_click` / `hero_skill`, silent
# refreshes stay quiet). History is bounded so long matches do not grow it.
var sound_history: Array[String] = []


func bind(target_world: Object) -> void:
	world = target_world


func set_selected_hero(hero_id: int) -> void:
	selected_hero_id = hero_id


func set_mouse(point: Vector2) -> void:
	mouse_position = point


func seed_auto_roll(seed_value: int) -> void:
	auto_rng.seed = seed_value


func can_issue() -> bool:
	# `self.cooldown <= 0 and self.game.state == "playing"`.
	return cooldown <= 0 and world != null and world.is_running()


func hold_active() -> bool:
	return not held_command.is_empty()


func hold_start(
	command: String,
	point: Vector2 = Vector2.ZERO,
	has_point: bool = false,
	tower_id: int = -1,
	follow_mouse: bool = false
) -> bool:
	## Port of `hold_start`: issue now with full feedback, then let `update()`
	## re-issue silently every COOLDOWN_MAX ticks until `hold_end()`. A repeat
	## press of the same hold (key repeat / held panel button) is a no-op.
	if command not in COMMANDS:
		return false
	if command == held_command and hold_elapsed > 0:
		return true
	held_command = command
	hold_point = point
	hold_has_point = has_point
	hold_tower_id = tower_id
	hold_follow_mouse = follow_mouse
	hold_elapsed = 0
	hold_has_fired = false
	gather_push_fired = false
	var issued := issue_held(true)
	if issued:
		hold_has_fired = true
	return issued


func hold_end(command: String = "") -> void:
	## Port of `hold_end`: a TAP (< HOLD_TAP_MAX_FRAMES) keeps the normal 600
	## tick duration, a long HOLD stops being enforced and only keeps the
	## HOLD_RELEASE_TAIL tail. `command == ""` releases whatever is held.
	if held_command.is_empty():
		return
	if not command.is_empty() and command != held_command:
		return
	var elapsed := hold_elapsed
	held_command = ""
	hold_point = Vector2.ZERO
	hold_has_point = false
	hold_tower_id = -1
	hold_follow_mouse = false
	hold_elapsed = 0
	hold_has_fired = false
	if elapsed >= HOLD_TAP_MAX_FRAMES and command_timer > 0:
		command_timer = mini(command_timer, HOLD_RELEASE_TAIL)


func issue_held(loud: bool) -> bool:
	## Port of `_issue_held`. A GATHER hold that already pushed only re-locks the
	## enemy target (`_gather_hold_push`), never drags heroes back to the point.
	if held_command.is_empty():
		return false
	if held_command == GATHER and not loud and gather_push_fired:
		var pushed := gather_hold_push()
		cooldown = COOLDOWN_MAX
		return pushed
	var point := hold_point
	var has_point := hold_has_point
	if held_command == GATHER and hold_follow_mouse:
		if inside_arena(mouse_position):
			point = mouse_position
			has_point = true
		else:
			has_point = false
	var issued := issue(held_command, point, has_point, not loud)
	if not issued:
		cooldown = maxi(cooldown, HOLD_RETRY_COOLDOWN)
	return issued


func issue(command: String, point: Vector2, has_point: bool, silent: bool) -> bool:
	## Port of the `_issuers()` dispatch table.
	match command:
		GATHER:
			return command_gather(point, has_point, silent)
		PROTECT_TOWER:
			return command_protect_tower(hold_tower_id, silent)
		PROTECT_CASTLE:
			return command_protect_castle(silent)
		ATTACK_BOSS:
			return command_attack_boss(silent)
		ATTACK_DAMAGE_DEALER:
			return command_attack_damage_dealer(silent)
	return false


func command_gather(point: Vector2, has_point: bool, silent: bool) -> bool:
	## Port of `command_gather`. Source never resets `command_target` here, so a
	## stale protect/attack target survives a GATHER - kept on purpose.
	if not can_issue():
		return false
	var heroes := alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			set_feedback("No heroes alive!", Color8(255, 100, 100))
		return false
	var target_x := point.x
	var target_y := point.y
	if not has_point:
		var fallback := default_gather_point(heroes)
		target_x = fallback[0]
		target_y = fallback[1]
	active_command = GATHER
	command_timer = COMMAND_TICKS
	gather_x = target_x
	gather_y = target_y
	has_gather_point = true
	gather_point_timer = MARKER_TICKS
	cooldown = COOLDOWN_MAX
	if not silent:
		# A brand new GATHER re-arms the follow-up push; a silent HOLD refresh
		# must not cancel a push that already fired.
		gather_push_fired = false
	clear_hero_retreat(heroes)
	var count := heroes.size()
	for index in range(count):
		var hero: Object = heroes[index]
		var angle := (float(index) / float(maxi(1, count))) * TAU
		var spread := 35.0 + float(index % 3) * 15.0
		order_move(hero, target_x + cos(angle) * spread, target_y + sin(angle) * spread)
		hero.follow_id = -1
		clear_hero_target(hero)
	if not silent:
		play_sound("ui_click")
		set_feedback("GATHER! %d heroes regrouping!" % count, Color8(100, 220, 255))
	return true


func command_protect_tower(tower_id: int, silent: bool) -> bool:
	## Port of `command_protect_tower`: an explicit dead tower is dropped, then
	## the most threatened blue tower wins, then the (-x, hp) fallback.
	if not can_issue():
		return false
	var heroes := alive_blue_heroes()
	if heroes.size() < 1:
		if not silent:
			set_feedback("No heroes alive!", Color8(255, 100, 100))
		return false
	var target_tower: Object = world.get_unit(tower_id) if tower_id >= 0 else null
	if target_tower != null and not bool(target_tower.alive):
		target_tower = null
	if target_tower == null:
		target_tower = find_most_threatened_tower()
	if target_tower == null:
		var fallback := blue_towers()
		if fallback.is_empty():
			if not silent:
				set_feedback("No tower to protect!", Color8(255, 150, 100))
			return false
		fallback = sort_towers_front_first(fallback)
		target_tower = fallback[0]
	active_command = PROTECT_TOWER
	command_timer = COMMAND_TICKS
	command_target_id = int(target_tower.id)
	gather_x = float(target_tower.position.x)
	gather_y = float(target_tower.position.y)
	has_gather_point = true
	gather_point_timer = MARKER_TICKS
	cooldown = COOLDOWN_MAX
	var protectors := heroes
	if heroes.size() > 3:
		var ordered := sort_by_distance(heroes, target_tower.position)
		var threat := count_enemies_near(target_tower.position, PROTECT_SCAN_RADIUS)
		protectors = ordered.slice(0, 3 if threat >= 3 else 2)
	clear_hero_retreat(protectors)
	var sent := protectors.size()
	for index in range(sent):
		var hero: Object = protectors[index]
		var angle := (float(index) / float(sent)) * TAU if sent > 1 else 0.0
		var spread := 30.0 + float(index) * 10.0
		order_move(
			hero,
			float(target_tower.position.x) + cos(angle) * spread,
			float(target_tower.position.y) + sin(angle) * spread
		)
		hero.follow_id = -1
		clear_hero_target(hero)
	if not silent:
		play_sound("ui_click")
		set_feedback(
			"PROTECT TOWER! %d heroes defending %s!" % [sent, display_name_of(target_tower)],
			Color8(100, 255, 100)
		)
	return true


func command_protect_castle(silent: bool) -> bool:
	## Port of `command_protect_castle`: ring formation around the blue castle,
	## radius 80 + (i % 2) * 30, clamped inside the arena.
	if not can_issue():
		return false
	var heroes := alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			set_feedback("No heroes alive!", Color8(255, 100, 100))
		return false
	var castle: Object = blue_castle()
	if castle == null or not bool(castle.alive):
		if not silent:
			set_feedback("Castle destroyed!", Color8(255, 100, 100))
		return false
	active_command = PROTECT_CASTLE
	command_timer = COMMAND_TICKS
	command_target_id = int(castle.id)
	gather_x = float(castle.position.x)
	gather_y = float(castle.position.y)
	has_gather_point = true
	gather_point_timer = MARKER_TICKS
	cooldown = COOLDOWN_MAX
	clear_hero_retreat(heroes)
	var count := heroes.size()
	for index in range(count):
		var hero: Object = heroes[index]
		var angle := (float(index) / float(count)) * TAU
		var radius := 80.0 + float(index % 2) * 30.0
		var tx := clampf(
			float(castle.position.x) + cos(angle) * radius, CASTLE_CLAMP_MIN_X, CASTLE_CLAMP_MAX_X
		)
		var ty := clampf(
			float(castle.position.y) + sin(angle) * radius, CASTLE_CLAMP_MIN_Y, CASTLE_CLAMP_MAX_Y
		)
		order_move(hero, tx, ty)
		hero.follow_id = -1
		clear_hero_target(hero)
	if not silent:
		play_sound("ui_click")
		set_feedback("PROTECT CASTLE! %d heroes defending base!" % count, Color8(255, 220, 50))
	return true


func command_attack_boss(silent: bool) -> bool:
	## Port of `command_attack_boss`: every blue hero locks the active boss and
	## walks to a spread ring around it (destination first, then follow).
	if not can_issue():
		return false
	var heroes := alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			set_feedback("No heroes alive!", Color8(255, 100, 100))
		return false
	var boss: Object = world.get("active_boss")
	if boss == null or not bool(boss.alive):
		if not silent:
			set_feedback("No boss active!", Color8(255, 150, 100))
		return false
	active_command = ATTACK_BOSS
	command_timer = COMMAND_TICKS
	command_target_id = int(boss.id)
	gather_x = float(boss.position.x)
	gather_y = float(boss.position.y)
	has_gather_point = true
	gather_point_timer = MARKER_TICKS
	cooldown = COOLDOWN_MAX
	clear_hero_retreat(heroes)
	focus_on(heroes, boss)
	if not silent:
		play_sound("hero_skill")
		set_feedback(
			"ATTACK BOSS! All heroes attack %s!" % display_name_of(boss), Color8(255, 100, 100)
		)
	return true


func command_attack_damage_dealer(silent: bool) -> bool:
	## Port of `command_attack_damage_dealer`: focus the living red hero with the
	## highest accumulated `damage_dealt` (source `_entity.credit_hero_damage`).
	if not can_issue():
		return false
	var heroes := alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			set_feedback("No heroes alive!", Color8(255, 100, 100))
		return false
	var dealer: Object = find_enemy_damage_dealer()
	if dealer == null:
		if not silent:
			set_feedback("No enemy heroes!", Color8(255, 150, 100))
		return false
	active_command = ATTACK_DAMAGE_DEALER
	command_timer = COMMAND_TICKS
	command_target_id = int(dealer.id)
	gather_x = float(dealer.position.x)
	gather_y = float(dealer.position.y)
	has_gather_point = true
	gather_point_timer = MARKER_TICKS
	cooldown = COOLDOWN_MAX
	clear_hero_retreat(heroes)
	focus_on(heroes, dealer)
	if not silent:
		play_sound("hero_skill")
		set_feedback(
			(
				"ATTACK DAMAGE DEALER! Focus %s (%d dmg)!"
				% [display_name_of(dealer), int(dealer.damage_dealt)]
			),
			Color8(255, 130, 255)
		)
	return true


func update() -> void:
	## Port of `TacticalCommandManager.update`; the match world calls it once per
	## tick where `Game.update` does (after respawns, before the AI dispatch).
	if cooldown > 0:
		cooldown -= 1
	if command_timer > 0:
		command_timer -= 1
		if command_timer <= 0:
			active_command = ""
			command_target_id = -1
	if gather_point_timer > 0:
		gather_point_timer -= 1
		if gather_point_timer <= 0:
			has_gather_point = false
	if feedback_timer > 0:
		feedback_timer -= 1
	if not held_command.is_empty() and world != null and world.is_running():
		hold_elapsed += 1
		if cooldown <= 0:
			var refreshed := issue_held(false)
			if refreshed and not hold_has_fired:
				cooldown = 0
				issue_held(true)
			if refreshed:
				hold_has_fired = true
	if active_command == GATHER and has_gather_point:
		if held_command == GATHER:
			if not gather_push_fired and hold_elapsed >= GATHER_PUSH_DELAY_FRAMES:
				try_gather_push()
		elif command_timer == GATHER_PUSH_TIMER:
			try_gather_push()
	if active_command.is_empty() and cooldown <= 0:
		auto_check_timer += 1
		if auto_check_timer >= AUTO_CHECK_TICKS:
			auto_check_timer = 0
			auto_evaluate_protect()


func try_gather_push() -> bool:
	## Port of `_try_gather_push`: once 60% of the heroes arrive within
	## GATHER_ARRIVE_PX of the gather point, lock the nearest enemy. The source
	## only clears `destination` and sets `follow_target`; `target`,
	## `destination_auto` and `is_retreating` are deliberately untouched.
	var heroes := alive_blue_heroes()
	if heroes.is_empty() or not has_gather_point:
		return false
	var arrived := 0
	for entry in heroes:
		var hero: Object = entry
		if distance_to_gather(hero) < GATHER_ARRIVE_PX:
			arrived += 1
	if float(arrived) < float(heroes.size()) * GATHER_ARRIVED_RATIO:
		return false
	var target: Object = find_nearest_enemy_target(gather_point())
	if target == null:
		return false
	for entry in heroes:
		var hero: Object = entry
		hero.follow_id = int(target.id)
		hero.has_destination = false
	gather_push_fired = true
	set_feedback("GATHER ATTACK! %d heroes push together!" % heroes.size(), Color8(100, 220, 255))
	return true


func gather_hold_push() -> bool:
	## Port of `_gather_hold_push`: the HOLD refresh after a push re-locks the
	## enemy target; with no enemy left the heroes regroup silently.
	var heroes := alive_blue_heroes()
	if heroes.is_empty() or not has_gather_point:
		return false
	var target: Object = find_nearest_enemy_target(gather_point())
	if target == null:
		var point := gather_point()
		var has_point := true
		if hold_has_point:
			point = hold_point
		return command_gather(point, has_point, true)
	for entry in heroes:
		var hero: Object = entry
		hero.follow_id = int(target.id)
		hero.has_destination = false
		hero.destination_auto = false
		hero.is_retreating = false
		lock_hero_target(hero, target)
	command_timer = COMMAND_TICKS
	gather_point_timer = MARKER_TICKS
	return true


func auto_evaluate_protect() -> void:
	## Port of `_auto_evaluate_protect`: castle first, then the most threatened
	## tower, then a 20% boss focus roll from wave 11 onwards.
	if world == null or not world.is_running():
		return
	var castle: Object = blue_castle()
	if castle != null and bool(castle.alive):
		if (
			hp_ratio(castle) < AUTO_CASTLE_HP
			and count_enemies_near(castle.position, CASTLE_SCAN_RADIUS) >= AUTO_CASTLE_ENEMIES
		):
			command_protect_castle(false)
			return
	var threatened: Array = []
	var own_towers := blue_towers()
	for index in range(own_towers.size()):
		var tower: Object = own_towers[index]
		var near := count_enemies_near(tower.position, PROTECT_SCAN_RADIUS)
		var ratio := hp_ratio(tower)
		if ratio < AUTO_TOWER_HP and near >= AUTO_TOWER_ENEMIES:
			threatened.append([index, near, ratio, tower])
		elif near >= AUTO_TOWER_SWARM:
			threatened.append([index, near, ratio, tower])
	if not threatened.is_empty():
		threatened = sort_threatened(threatened)
		command_protect_tower(int(threatened[0][3].id), false)
		return
	var boss: Object = world.get("active_boss")
	if boss == null or not bool(boss.alive):
		return
	if hp_ratio(boss) >= AUTO_BOSS_HP:
		return
	if int(world.get("wave_count")) < AUTO_BOSS_WAVE:
		return
	if auto_roll() < AUTO_BOSS_ROLL:
		command_attack_boss(false)


func status_text() -> String:
	## Port of `get_status_text`, including the double space when a command has
	## no target and the armed-but-waiting HOLD line.
	var hold_tag := " [HOLD]" if hold_active() else ""
	if not active_command.is_empty():
		var target_name := ""
		var target: Object = world.get_unit(command_target_id) if world != null else null
		if target != null:
			target_name = display_name_of(target)
		return (
			"%s %s (%ds)%s"
			% [
				active_command.to_upper(),
				target_name,
				floori(float(command_timer) / 60.0),
				hold_tag,
			]
		)
	if hold_active():
		return "%s [HOLD] (%s)" % [held_command.to_upper(), STATUS_WAITING]
	return "No tactical command"


func command_color() -> Color:
	## Port of `_get_command_color`.
	match active_command:
		GATHER:
			return Color8(100, 220, 255)
		PROTECT_TOWER:
			return Color8(100, 255, 100)
		PROTECT_CASTLE:
			return Color8(255, 220, 50)
		ATTACK_BOSS:
			return Color8(255, 100, 100)
		ATTACK_DAMAGE_DEALER:
			return Color8(255, 130, 255)
	return Color8(255, 220, 100)


func marker_visible() -> bool:
	## Port of the `draw_world` gate: the marker only shows while its timer runs.
	return has_gather_point and gather_point_timer > 0


func marker_alpha() -> float:
	return clampf(float(gather_point_timer) / float(MARKER_TICKS), 0.0, 1.0)


func gather_point() -> Vector2:
	return Vector2(gather_x, gather_y)


func alive_blue_heroes() -> Array:
	## Port of `_get_alive_blue_heroes` (`game.heroes` is the blue roster).
	var heroes: Array = []
	for unit in world_units():
		if bool(unit.is_hero) and int(unit.team) == BLUE and bool(unit.alive):
			heroes.append(unit)
	return heroes


func clear_hero_retreat(heroes: Array) -> void:
	## Port of `_clear_hero_retreat`.
	for entry in heroes:
		var hero: Object = entry
		hero.is_retreating = false
		hero.destination_auto = false


func count_enemies_near(point: Vector2, radius: float) -> int:
	## Port of `_count_enemies_near`: red minions, AI-owned red heroes, and the
	## red boss counted twice.
	var count := 0
	for unit in world_units():
		if bool(unit.is_hero) or not bool(unit.alive) or int(unit.team) != RED:
			continue
		if distance(unit.position, point) <= radius:
			count += 1
	for entry in red_heroes():
		var hero: Object = entry
		if distance(hero.position, point) <= radius:
			count += 1
	var boss: Object = world.get("active_boss")
	if boss != null and bool(boss.alive) and int(boss.team) == RED:
		if distance(boss.position, point) <= radius:
			count += 2
	return count


func find_most_threatened_tower() -> Object:
	## Port of `_find_most_threatened_tower`: `enemies * 10 + (1 - hp) * 15`,
	## +2 for an outer tower (x < 400), stable descending sort, and the
	## lowest-HP tie-break when the best threat score is exactly zero.
	var towers := blue_towers()
	if towers.is_empty():
		return null
	var scored: Array = []
	for index in range(towers.size()):
		var tower: Object = towers[index]
		var near := count_enemies_near(tower.position, THREAT_SCAN_RADIUS)
		var score := float(near) * 10.0 + (1.0 - hp_ratio(tower)) * 15.0
		if float(tower.position.x) < OUTER_TOWER_X:
			score += 2.0
		scored.append([index, score, tower])
	scored = sort_scores_desc(scored)
	if float(scored[0][1]) == 0.0:
		var lowest := sort_by_hp_ratio(towers)
		return lowest[0]
	return scored[0][2]


func find_nearest_enemy_target(point: Vector2) -> Object:
	## Port of `_find_nearest_enemy_target`: boss first (no team check in the
	## source), then red towers, then AI red heroes; minions and the red castle
	## are only consulted while nothing bigger was found. Strict `<`, seeded at
	## 9999, so an equidistant later candidate never wins.
	var best: Object = null
	var best_dist := NEAREST_TARGET_SEED
	var boss: Object = world.get("active_boss")
	if boss != null and bool(boss.alive):
		var boss_dist := distance(boss.position, point)
		if boss_dist < best_dist:
			best_dist = boss_dist
			best = boss
	for tower in red_towers():
		var tower_dist := distance(tower.position, point)
		if tower_dist < best_dist:
			best_dist = tower_dist
			best = tower
	for entry in red_heroes():
		var hero: Object = entry
		var hero_dist := distance(hero.position, point)
		if hero_dist < best_dist:
			best_dist = hero_dist
			best = hero
	if best == null:
		for unit in world_units():
			if bool(unit.is_hero) or not bool(unit.alive) or int(unit.team) != RED:
				continue
			var minion_dist := distance(unit.position, point)
			if minion_dist < best_dist:
				best_dist = minion_dist
				best = unit
	if best == null:
		var bases: Variant = world.get("nexuses")
		if bases is Array and bases.size() > RED:
			var red_base: Object = bases[RED]
			if red_base != null and bool(red_base.alive):
				best = red_base
	return best


func find_enemy_damage_dealer() -> Object:
	## Port of `_find_enemy_damage_dealer`: Python `max` keeps the FIRST maximum.
	var best: Object = null
	var best_dealt := -1
	for entry in red_heroes():
		var hero: Object = entry
		var dealt := int(hero.damage_dealt)
		if dealt > best_dealt:
			best_dealt = dealt
			best = hero
	return best


func set_feedback(text: String, color: Color) -> void:
	## Port of `_set_feedback`. The source `ui.add_notification` is a no-op and
	## the damage-number effect is presentation, so only the banner state is
	## kept; the scene reads these fields each frame.
	feedback_text = text
	feedback_timer = FEEDBACK_TICKS
	feedback_color = color


func play_sound(sound: String) -> void:
	sound_history.append(sound)
	if sound_history.size() > SOUND_HISTORY_LIMIT:
		sound_history.pop_front()
	AudioRuntime.play(sound)


func auto_roll() -> float:
	if auto_roll_override.is_valid():
		return float(auto_roll_override.call())
	return auto_rng.randf()


func distance_to_gather(hero: Object) -> float:
	return distance(hero.position, gather_point())


func distance(left: Vector2, right: Vector2) -> float:
	## The source measures with `math.hypot` on doubles; `Vector2.distance_to`
	## would round in f32, so deltas are widened to doubles first.
	var dx := float(left.x) - float(right.x)
	var dy := float(left.y) - float(right.y)
	return sqrt(dx * dx + dy * dy)


func hp_ratio(unit: Object) -> float:
	## `hp / max(1, max_hp)` in the source; structures and the boss keep their
	## catalog maximum on the definition, heroes on their own field.
	var maximum: Variant = unit.get("max_hp")
	if maximum == null:
		var definition: Variant = unit.get("definition")
		maximum = definition.get("max_hp") if definition != null else 1
	return float(unit.hp) / maxf(1.0, float(maximum))


func display_name_of(unit: Object) -> String:
	## Source reads `getattr(target, 'name', str(target))[:15]`. The rebuild keeps
	## names on the definition, except for the boss which owns `display_name`.
	var name := ""
	var direct: Variant = unit.get("display_name")
	if direct != null and str(direct) != "":
		name = str(direct)
	else:
		var definition: Variant = unit.get("definition")
		if definition != null:
			name = str(definition.get("display_name"))
		else:
			name = str(unit)
	return name.substr(0, NAME_LIMIT)


func inside_arena(point: Vector2) -> bool:
	return point.x >= 0.0 and point.x < ARENA_SIZE.x and point.y >= 0.0 and point.y < ARENA_SIZE.y


func world_units() -> Array:
	var units: Variant = world.get("units")
	return units if units is Array else []


func blue_castle() -> Object:
	var bases: Variant = world.get("nexuses")
	if bases is Array and bases.size() > BLUE:
		return bases[BLUE]
	return null


func towers_of_team(team: int) -> Array:
	## `game.towers` holds towers only (castles live in `game.bases`), and the
	## source cleans dead towers out of the list every frame.
	var found: Array = []
	var structures: Variant = world.get("structures")
	if not (structures is Array):
		return found
	for entry in structures:
		var structure: Object = entry
		if structure == null or not bool(structure.alive) or int(structure.team) != team:
			continue
		if structure is StructureState:
			if (structure as StructureState).settings().structure_kind != "tower":
				continue
		found.append(structure)
	return found


func blue_towers() -> Array:
	return towers_of_team(BLUE)


func red_towers() -> Array:
	return towers_of_team(RED)


func red_heroes() -> Array:
	## `game.ai.heroes`, alive: the AI-owned red roster, not every red hero in
	## the world (the free mirrored Kaizen is not AI-owned, exactly as in the
	## source where `Game.heroes`/`ai.heroes` are separate lists).
	var roster: Array = []
	if world.has_method("_ai_roster"):
		roster = world.call("_ai_roster")
	else:
		for unit in world_units():
			if bool(unit.is_hero) and int(unit.team) == RED:
				roster.append(unit)
	var alive: Array = []
	for entry in roster:
		var hero: Object = entry
		if hero != null and bool(hero.alive):
			alive.append(hero)
	return alive


func default_gather_point(heroes: Array) -> Array:
	## Port of the GATHER point fallback chain: selected hero, then the average
	## position mixed 35% toward the red base and clamped, then map center.
	var selected: Object = world.get_unit(selected_hero_id) if world != null else null
	if (
		selected != null
		and bool(selected.alive)
		and int(selected.team) == BLUE
		and bool(selected.is_hero)
	):
		return [float(selected.position.x), float(selected.position.y)]
	if heroes.size() >= 2:
		var sum_x := 0.0
		var sum_y := 0.0
		for entry in heroes:
			var hero: Object = entry
			sum_x += float(hero.position.x)
			sum_y += float(hero.position.y)
		var avg_x := sum_x / float(heroes.size())
		var avg_y := sum_y / float(heroes.size())
		var mixed_x := avg_x * (1.0 - GATHER_MID_MIX) + LaneLayout.RED_BASE.x * GATHER_MID_MIX
		var mixed_y := avg_y * (1.0 - GATHER_MID_MIX) + LaneLayout.RED_BASE.y * GATHER_MID_MIX
		return [
			maxf(GATHER_MIN_X, minf(GATHER_MAX_X, mixed_x)),
			maxf(GATHER_MIN_Y, minf(GATHER_MAX_Y, mixed_y)),
		]
	return [GATHER_FALLBACK_X, GATHER_FALLBACK_Y]


func order_move(hero: Object, tx: float, ty: float) -> void:
	## `hero.move_to(x, y, auto=False)`: the source keeps double precision until
	## the assignment, so the Vector2 (f32) is built only here.
	world.move_to(hero, Vector2(tx, ty), false)


func focus_on(heroes: Array, target: Object) -> void:
	## Port of the ATTACK BOSS / ATTACK DAMAGE DEALER per-hero block: lock the
	## target, walk to a spread ring, then re-lock (move_to clears follow).
	var count := heroes.size()
	for index in range(count):
		var hero: Object = heroes[index]
		hero.follow_id = int(target.id)
		hero.has_destination = false
		hero.destination_auto = false
		lock_hero_target(hero, target)
		var angle := (float(index) / float(count)) * TAU
		var spread := float(hero.attack_range) * 0.5 + float(index) * 8.0
		order_move(
			hero,
			float(target.position.x) + cos(angle) * spread,
			float(target.position.y) + sin(angle) * spread
		)
		hero.follow_id = int(target.id)


func lock_hero_target(hero: Object, target: Object) -> void:
	hero.target_id = int(target.id)
	hero.target_struct = target if target is StructureState else null


func clear_hero_target(hero: Object) -> void:
	hero.target_id = -1
	hero.target_struct = null


func sort_by_distance(heroes: Array, point: Vector2) -> Array:
	## Python `sorted(..., key=hypot)` is stable; the index tie-break copies that.
	var ranked: Array = []
	for index in range(heroes.size()):
		var hero: Object = heroes[index]
		ranked.append([index, distance(hero.position, point), hero])
	ranked.sort_custom(_less_by_distance)
	var ordered: Array = []
	for entry in ranked:
		ordered.append(entry[2])
	return ordered


func _less_by_distance(left: Array, right: Array) -> bool:
	if float(left[1]) != float(right[1]):
		return float(left[1]) < float(right[1])
	return int(left[0]) < int(right[0])


func sort_towers_front_first(towers: Array) -> Array:
	## `blue_towers.sort(key=lambda t: (-t.x, t.hp / max(1, t.max_hp)))`, stable.
	var ranked: Array = []
	for index in range(towers.size()):
		var tower: Object = towers[index]
		ranked.append([index, float(tower.position.x), hp_ratio(tower), tower])
	ranked.sort_custom(_less_front_tower)
	var ordered: Array = []
	for entry in ranked:
		ordered.append(entry[3])
	return ordered


func _less_front_tower(left: Array, right: Array) -> bool:
	if float(left[1]) != float(right[1]):
		return float(left[1]) > float(right[1])
	if float(left[2]) != float(right[2]):
		return float(left[2]) < float(right[2])
	return int(left[0]) < int(right[0])


func sort_by_hp_ratio(towers: Array) -> Array:
	## `blue_towers.sort(key=lambda t: t.hp / max(1, t.max_hp))`, stable.
	var ranked: Array = []
	for index in range(towers.size()):
		var tower: Object = towers[index]
		ranked.append([index, hp_ratio(tower), tower])
	ranked.sort_custom(_less_hp_ratio)
	var ordered: Array = []
	for entry in ranked:
		ordered.append(entry[2])
	return ordered


func _less_hp_ratio(left: Array, right: Array) -> bool:
	if float(left[1]) != float(right[1]):
		return float(left[1]) < float(right[1])
	return int(left[0]) < int(right[0])


func sort_scores_desc(scored: Array) -> Array:
	## `scored.sort(key=lambda x: -x[0])`, stable.
	scored.sort_custom(_less_score_desc)
	return scored


func _less_score_desc(left: Array, right: Array) -> bool:
	if float(left[1]) != float(right[1]):
		return float(left[1]) > float(right[1])
	return int(left[0]) < int(right[0])


func sort_threatened(threatened: Array) -> Array:
	## `threatened.sort(key=lambda x: (-x[0], x[1]))` over (enemies, hp ratio).
	threatened.sort_custom(_less_threatened)
	return threatened


func _less_threatened(left: Array, right: Array) -> bool:
	if int(left[1]) != int(right[1]):
		return int(left[1]) > int(right[1])
	if float(left[2]) != float(right[2]):
		return float(left[2]) < float(right[2])
	return int(left[0]) < int(right[0])
