class_name TacticalCommands
extends RefCounted

## Native port of tactical_commands.py. Frame-based (60 fps) hold/tap manager;
## constants come only from data/tactical.json. Python is never used at runtime.
signal feedback(text: String, color: Color)
signal sound(name: String, volume: float)
signal effect(kind: String, data: Dictionary)

const DEFAULT_PATH := "res://data/tactical.json"
const COMMANDS := [
	"gather", "protect_tower", "protect_castle", "attack_boss", "attack_damage_dealer"
]
var cfg: Dictionary = {}
var load_error := ""
var random_script: Array = []
var active_command := ""
var command_timer := 0
var command_target: BattleUnit = null
var command_origin: Variant = null
var feedback_timer := 0
var feedback_text := ""
var feedback_color: Array = [255, 255, 255]
var cooldown := 0
var cooldown_max := 30
var gather_point: Variant = null
var gather_point_timer := 0
var held_command := ""
var hold_args: Array = []
var hold_kwargs: Dictionary = {}
var hold_follow_mouse := false
var hold_elapsed := 0
var _hold_has_fired := false
var _gather_push_fired := false
var _auto_check_timer := 0
var _rng := RandomNumberGenerator.new()
var _game_ref: WeakRef = null
var game: RefCounted:  # gdlint: ignore=class-definitions-order
	get:
		return _game_ref.get_ref() as RefCounted if _game_ref != null else null


func _init(path := DEFAULT_PATH) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		load_error = "Cannot open %s" % path
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary or int(parsed.get("schema", 0)) != 1:
		load_error = "Invalid tactical contract"
		return
	if str(parsed.get("source", "")) != "tactical_commands.py":
		load_error = "Unsupported tactical source"
		return
	cfg = parsed.get("config", {})
	if not cfg.has("command_duration") or not cfg.has("cooldown_max"):
		load_error = "Tactical contract missing required fields"
		return
	cooldown_max = int(cfg.cooldown_max)
	_rng.randomize()


func _g(key: String, default: Variant = null) -> Variant:
	if game == null:
		return default
	var value: Variant = game.get(key)
	return default if value == null else value


func valid() -> bool:
	return load_error.is_empty()


func attach(model: RefCounted) -> void:
	_game_ref = weakref(model) if model != null else null


func reset() -> void:
	active_command = ""
	command_timer = 0
	command_target = null
	command_origin = null
	feedback_timer = 0
	feedback_text = ""
	feedback_color = [255, 255, 255]
	cooldown = 0
	gather_point = null
	gather_point_timer = 0
	held_command = ""
	hold_args = []
	hold_kwargs = {}
	hold_follow_mouse = false
	hold_elapsed = 0
	_hold_has_fired = false
	_gather_push_fired = false
	_auto_check_timer = 0


func release_all() -> void:
	hold_end()


func can_issue() -> bool:
	return cooldown <= 0 and game != null and str(_g("state", "")) == "playing"


func hold_start(
	name: String, args: Array = [], follow_mouse := false, kwargs: Dictionary = {}
) -> bool:
	if name not in COMMANDS:
		return false
	if name == held_command and hold_elapsed > 0:
		return true
	held_command = name
	hold_args = args.duplicate()
	hold_kwargs = kwargs.duplicate()
	hold_follow_mouse = follow_mouse
	hold_elapsed = 0
	_hold_has_fired = false
	_gather_push_fired = false
	var ok := _issue_held(true)
	if ok:
		_hold_has_fired = true
	return ok


func hold_end(name := "") -> void:
	if held_command.is_empty():
		return
	if not name.is_empty() and name != held_command:
		return
	var elapsed := hold_elapsed
	held_command = ""
	hold_args = []
	hold_kwargs = {}
	hold_follow_mouse = false
	hold_elapsed = 0
	_hold_has_fired = false
	if elapsed >= int(cfg.hold_tap_max_frames) and command_timer > 0:
		command_timer = mini(command_timer, int(cfg.hold_release_tail))


func hold_active() -> bool:
	return not held_command.is_empty()


func update(model: RefCounted = null) -> void:
	if model != null:
		attach(model)
	if not valid() or game == null:
		return
	if cooldown > 0:
		cooldown -= 1
	if command_timer > 0:
		command_timer -= 1
		if command_timer <= 0:
			active_command = ""
			command_target = null
	if gather_point_timer > 0:
		gather_point_timer -= 1
		if gather_point_timer <= 0:
			gather_point = null
	if feedback_timer > 0:
		feedback_timer -= 1
	_update_hold()
	_update_gather_followup()
	_update_auto_protect()


func command_gather(gather_x: Variant = null, gather_y: Variant = null, silent := false) -> bool:
	if not can_issue():
		return false
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", cfg.feedback_no_heroes)
		return false
	var point := _gather_default_point(heroes)
	if gather_x != null and gather_y != null:
		point = Vector2(float(gather_x), float(gather_y))
	active_command = "gather"
	command_timer = int(cfg.command_duration)
	gather_point = point
	gather_point_timer = int(cfg.gather_point_duration)
	cooldown = cooldown_max
	if not silent:
		_gather_push_fired = false
	TacticalTargeting.clear_retreat(heroes)
	for index in range(heroes.size()):
		var hero := heroes[index]
		var angle := (float(index) / maxi(1, heroes.size())) * TAU
		var spread := (
			int(cfg.gather_spread_base)
			+ (index % int(cfg.gather_spread_mod)) * int(cfg.gather_spread_step)
		)
		TacticalTargeting.move_to(hero, point + Vector2(cos(angle), sin(angle)) * spread)
		hero.follow_target = null
		hero.target = null
	if not silent:
		sound.emit(str(cfg.sound_ui_click), float(cfg.sound_ui_click_volume))
		_set_feedback("GATHER! %d heroes regrouping!" % heroes.size(), cfg.feedback_gather)
		effect.emit("death", {"pos": point, "team": "blue", "size": "small"})
	return true


func command_protect_tower(tower: BattleUnit = null, silent := false) -> bool:
	if not can_issue():
		return false
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", cfg.feedback_no_heroes)
		return false
	var target := tower
	if target != null and not target.alive:
		target = null
	if target == null:
		target = TacticalTargeting.most_threatened_tower(game, cfg)
	if target == null:
		target = _fallback_tower()
	if target == null:
		if not silent:
			_set_feedback("No tower to protect!", cfg.feedback_missing)
		return false
	active_command = "protect_tower"
	command_timer = int(cfg.command_duration)
	command_target = target
	gather_point = target.pos
	gather_point_timer = int(cfg.gather_point_duration)
	cooldown = cooldown_max
	var protectors := _protect_tower_protectors(heroes, target)
	TacticalTargeting.clear_retreat(protectors)
	for index in range(protectors.size()):
		var hero := protectors[index]
		var angle := (float(index) / protectors.size()) * TAU if protectors.size() > 1 else 0.0
		var spread := (
			int(cfg.protect_tower_spread_base) + index * int(cfg.protect_tower_spread_step)
		)
		TacticalTargeting.move_to(hero, target.pos + Vector2(cos(angle), sin(angle)) * spread)
		hero.follow_target = null
		hero.target = null
	if not silent:
		sound.emit(str(cfg.sound_ui_click), float(cfg.sound_ui_click_volume))
		_set_feedback(
			"PROTECT TOWER! %d heroes defending %s!" % [protectors.size(), target.display_name],
			cfg.feedback_protect_tower
		)
	return true


func command_protect_castle(silent := false) -> bool:
	if not can_issue():
		return false
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", cfg.feedback_no_heroes)
		return false
	var castle: BattleUnit = _g("blue_base")
	if castle == null or not castle.alive:
		if not silent:
			_set_feedback("Castle destroyed!", cfg.feedback_no_heroes)
		return false
	active_command = "protect_castle"
	command_timer = int(cfg.command_duration)
	command_target = castle
	gather_point = castle.pos
	gather_point_timer = int(cfg.gather_point_duration)
	cooldown = cooldown_max
	TacticalTargeting.clear_retreat(heroes)
	for index in range(heroes.size()):
		var hero := heroes[index]
		var angle := (float(index) / heroes.size()) * TAU
		var radius := (
			int(cfg.castle_radius_base)
			+ (index % int(cfg.castle_radius_mod)) * int(cfg.castle_radius_step)
		)
		var point := castle.pos + Vector2(cos(angle), sin(angle)) * radius
		point.x = clampf(point.x, float(cfg.castle_clamp_x[0]), float(cfg.castle_clamp_x[1]))
		point.y = clampf(point.y, float(cfg.castle_clamp_y[0]), float(cfg.castle_clamp_y[1]))
		TacticalTargeting.move_to(hero, point)
		hero.follow_target = null
		hero.target = null
	if not silent:
		sound.emit(str(cfg.sound_ui_click), float(cfg.sound_ui_click_volume))
		_set_feedback(
			"PROTECT CASTLE! %d heroes defending base!" % heroes.size(), cfg.feedback_protect_castle
		)
		effect.emit("death", {"pos": castle.pos, "team": "blue", "size": "small"})
	return true


func command_attack_boss(silent := false) -> bool:
	if not can_issue():
		return false
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", cfg.feedback_no_heroes)
		return false
	var boss: BattleUnit = _g("active_boss")
	if boss == null or not boss.alive:
		if not silent:
			_set_feedback("No boss active!", cfg.feedback_missing)
		return false
	_attack_target(
		heroes,
		boss,
		"attack_boss",
		boss.display_name,
		"ATTACK BOSS! All heroes attack %s!" % boss.display_name,
		cfg.feedback_attack_boss,
		silent
	)
	return true


func command_attack_damage_dealer(silent := false) -> bool:
	if not can_issue():
		return false
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", cfg.feedback_no_heroes)
		return false
	var dealer := TacticalTargeting.enemy_damage_dealer(game)
	if dealer == null:
		if not silent:
			_set_feedback("No enemy heroes!", cfg.feedback_missing)
		return false
	var message := (
		"ATTACK DAMAGE DEALER! Focus %s (%d dmg)!" % [dealer.display_name, int(dealer.damage_dealt)]
	)
	_attack_target(
		heroes,
		dealer,
		"attack_damage_dealer",
		dealer.display_name,
		message,
		cfg.feedback_attack_dealer,
		silent
	)
	return true


func status_text() -> String:
	var target_name := ""
	if command_target != null:
		target_name = command_target.display_name.left(int(cfg.status_target_chars))
	return TacticalDraw.status_text(cfg, active_command, target_name, command_timer, held_command)


func command_color() -> Array:
	return TacticalDraw.command_color(cfg, active_command)


func world_draw_data(ticks_ms := -1) -> Dictionary:
	var ticks := Time.get_ticks_msec() if ticks_ms < 0 else ticks_ms
	return TacticalDraw.world_data(
		cfg,
		active_command,
		gather_point,
		gather_point_timer,
		TacticalTargeting.alive_blue_heroes(game) if game != null else [],
		ticks
	)


func ui_draw_data() -> Dictionary:
	return TacticalDraw.ui_data(cfg, feedback_timer)


func _issue_held(loud: bool) -> bool:
	if held_command.is_empty():
		return false
	if held_command == "gather" and not loud and _gather_push_fired:
		var ok := _gather_hold_push()
		cooldown = cooldown_max
		return ok
	var args := hold_args.duplicate()
	if held_command == "gather" and hold_follow_mouse:
		var mx := float(_g("mouse_x", 0))
		var my := float(_g("mouse_y", 0))
		if mx >= 0 and mx < float(cfg.screen[0]) and my >= 0 and my < float(cfg.screen[1]):
			args = [mx, my]
		else:
			args = []
	var ok := false
	match held_command:
		"gather":
			ok = command_gather(
				args[0] if args.size() > 0 else null, args[1] if args.size() > 1 else null, not loud
			)
		"protect_tower":
			ok = command_protect_tower(args[0] if args.size() > 0 else null, not loud)
		"protect_castle":
			ok = command_protect_castle(not loud)
		"attack_boss":
			ok = command_attack_boss(not loud)
		"attack_damage_dealer":
			ok = command_attack_damage_dealer(not loud)
	if not ok:
		cooldown = maxi(cooldown, cooldown_max / 2)
	return ok


func _update_hold() -> void:
	if held_command.is_empty() or str(_g("state", "")) != "playing":
		return
	hold_elapsed += 1
	if cooldown <= 0:
		var ok := _issue_held(false)
		if ok and not _hold_has_fired:
			cooldown = 0
			_issue_held(true)
		if ok:
			_hold_has_fired = true


func _update_gather_followup() -> void:
	if active_command != "gather" or gather_point == null:
		return
	if held_command == "gather":
		if not _gather_push_fired and hold_elapsed >= int(cfg.gather_push_delay_frames):
			_try_gather_push()
	elif command_timer == int(cfg.gather_push_timer):
		_try_gather_push()


func _update_auto_protect() -> void:
	if not active_command.is_empty() or cooldown > 0:
		return
	_auto_check_timer += 1
	if _auto_check_timer >= int(cfg.auto_interval):
		_auto_check_timer = 0
		_auto_evaluate_protect()


func _gather_default_point(heroes: Array[BattleUnit]) -> Vector2:
	var selected: BattleUnit = _g("selected_hero")
	if selected != null and selected.alive and selected.team == "blue":
		return selected.pos
	if heroes.size() >= 2:
		var average := Vector2.ZERO
		for hero: BattleUnit in heroes:
			average += hero.pos
		average /= heroes.size()
		var red := Vector2(float(cfg.red_base[0]), float(cfg.red_base[1]))
		var mix := float(cfg.gather_mid_mix)
		var point := average * (1.0 - mix) + red * mix
		point.x = clampf(point.x, float(cfg.gather_clamp_x[0]), float(cfg.gather_clamp_x[1]))
		point.y = clampf(point.y, float(cfg.gather_clamp_y[0]), float(cfg.gather_clamp_y[1]))
		return point
	return Vector2(float(cfg.gather_single[0]), float(cfg.gather_single[1]))


func _fallback_tower() -> BattleUnit:
	var blue_towers: Array[BattleUnit] = []
	for unit: Variant in _g("towers", []):
		if unit is BattleUnit and unit.team == "blue" and unit.alive:
			blue_towers.append(unit)
	if blue_towers.is_empty():
		return null
	var rows: Array[Dictionary] = []
	for index in range(blue_towers.size()):
		var tower := blue_towers[index]
		rows.append(
			{
				"tower": tower,
				"x": tower.pos.x,
				"hp": tower.hp / maxf(1.0, tower.max_hp),
				"index": index
			}
		)
	TacticalTargeting._insertion_sort(
		rows,
		func(a: Dictionary, b: Dictionary) -> bool:
			if a.x != b.x:
				return a.x > b.x
			if a.hp != b.hp:
				return a.hp < b.hp
			return a.index < b.index
	)
	return rows[0].tower


func _protect_tower_protectors(heroes: Array[BattleUnit], target: BattleUnit) -> Array[BattleUnit]:
	if heroes.size() <= int(cfg.protect_tower_small_roster):
		return heroes
	var sorted := TacticalTargeting.sorted_heroes_by_distance(heroes, target.pos)
	var threat := TacticalTargeting.count_enemies_near(
		game, target.pos.x, target.pos.y, float(cfg.protect_tower_threat_radius)
	)
	var count := (
		int(cfg.protect_tower_send_count)
		if threat >= int(cfg.protect_tower_send_threshold)
		else int(cfg.protect_tower_base_count)
	)
	var out: Array[BattleUnit] = []
	for index in range(mini(count, sorted.size())):
		out.append(sorted[index])
	return out


func _attack_target(
	heroes: Array[BattleUnit],
	target: BattleUnit,
	command: String,
	_target_name: String,
	message: String,
	color: Array,
	silent: bool
) -> void:
	active_command = command
	command_timer = int(cfg.command_duration)
	command_target = target
	gather_point = target.pos
	gather_point_timer = int(cfg.gather_point_duration)
	cooldown = cooldown_max
	TacticalTargeting.clear_retreat(heroes)
	for index in range(heroes.size()):
		var hero := heroes[index]
		hero.follow_target = target
		TacticalTargeting.clear_destination(hero)
		hero.destination_auto = false
		hero.target = target
		var angle := (float(index) / heroes.size()) * TAU
		var spread := (
			hero.range * float(cfg.attack_spread_range_mult) + index * int(cfg.attack_spread_step)
		)
		TacticalTargeting.move_to(hero, target.pos + Vector2(cos(angle), sin(angle)) * spread)
		hero.follow_target = target
	if not silent:
		sound.emit(str(cfg.sound_hero_skill), float(cfg.sound_hero_skill_volume))
		_set_feedback(message, color)


func _gather_hold_push() -> bool:
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty() or gather_point == null:
		return false
	var point: Vector2 = gather_point
	var target := TacticalTargeting.nearest_enemy_target(game, cfg, point.x, point.y)
	if target == null:
		var args := hold_args if not hold_args.is_empty() else [point.x, point.y]
		return command_gather(args[0], args[1], true)
	for hero: BattleUnit in heroes:
		hero.follow_target = target
		TacticalTargeting.clear_destination(hero)
		hero.destination_auto = false
		hero.is_retreating = false
		hero.target = target
	command_timer = int(cfg.command_duration)
	gather_point_timer = int(cfg.gather_point_duration)
	return true


func _try_gather_push() -> bool:
	var heroes := TacticalTargeting.alive_blue_heroes(game)
	if heroes.is_empty() or gather_point == null:
		return false
	var point: Vector2 = gather_point
	var arrived := 0
	for hero: BattleUnit in heroes:
		if hero.pos.distance_to(point) < float(cfg.gather_arrive_radius):
			arrived += 1
	if float(arrived) < heroes.size() * float(cfg.gather_arrive_ratio):
		return false
	var target := TacticalTargeting.nearest_enemy_target(game, cfg, point.x, point.y)
	if target == null:
		return false
	for hero: BattleUnit in heroes:
		hero.follow_target = target
		hero.has_destination = false
		hero.destination = Vector2.ZERO
	_gather_push_fired = true
	_set_feedback("GATHER ATTACK! %d heroes push together!" % heroes.size(), cfg.feedback_gather)
	return true


func _auto_evaluate_protect() -> void:
	if str(_g("state", "")) != "playing":
		return
	var castle: BattleUnit = _g("blue_base")
	if castle != null and castle.alive:
		var hp_ratio := castle.hp / maxf(1.0, castle.max_hp)
		var enemies := TacticalTargeting.count_enemies_near(
			game, castle.pos.x, castle.pos.y, float(cfg.auto_castle_radius)
		)
		if hp_ratio < float(cfg.auto_castle_hp) and enemies >= int(cfg.auto_castle_enemies):
			command_protect_castle()
			return
	var threatened: Array[Dictionary] = []
	var index := 0
	for unit: Variant in _g("towers", []):
		if unit is BattleUnit and unit.team == "blue" and unit.alive:
			var tower: BattleUnit = unit
			var hp_ratio := tower.hp / maxf(1.0, tower.max_hp)
			var enemies := TacticalTargeting.count_enemies_near(
				game, tower.pos.x, tower.pos.y, float(cfg.auto_tower_radius)
			)
			if (
				(hp_ratio < float(cfg.auto_tower_hp) and enemies >= int(cfg.auto_tower_enemies))
				or enemies >= int(cfg.auto_tower_swarm)
			):
				threatened.append(
					{"enemies": enemies, "hp": hp_ratio, "tower": tower, "index": index}
				)
			index += 1
	if not threatened.is_empty():
		TacticalTargeting._insertion_sort(
			threatened,
			func(a: Dictionary, b: Dictionary) -> bool:
				if a.enemies != b.enemies:
					return a.enemies > b.enemies
				if a.hp != b.hp:
					return a.hp < b.hp
				return a.index < b.index
		)
		command_protect_tower(threatened[0].tower)
		return
	var boss: BattleUnit = _g("active_boss")
	if boss != null and boss.alive:
		var boss_hp := boss.hp / maxf(1.0, boss.max_hp)
		if (
			boss_hp < float(cfg.auto_boss_hp)
			and int(_g("wave_number", 0)) >= int(cfg.auto_boss_wave)
		):
			if _random_value() < float(cfg.auto_boss_chance):
				command_attack_boss()


func _random_value() -> float:
	if not random_script.is_empty():
		return float(random_script.pop_front())
	return _rng.randf()


func _set_feedback(text: String, color: Array) -> void:
	feedback_text = text
	feedback_timer = int(cfg.feedback_duration)
	feedback_color = color.duplicate()
	feedback.emit(
		text, Color(float(color[0]) / 255.0, float(color[1]) / 255.0, float(color[2]) / 255.0)
	)
	effect.emit("damage_number", {"pos": Vector2(640, 100), "text": text, "critical": true})
