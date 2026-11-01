class_name DevMode
extends RefCounted

## Developer mode port. Cheats require debug build or MYSTIC_DEV=1 and F1.
var enabled := false
var panel_open := false
var show_debug := false
var god_mode := false
var allowed := false


func _init() -> void:
	allowed = OS.is_debug_build() or OS.get_environment("MYSTIC_DEV") == "1"


func handle_hotkey(key: Key, model: MatchModel) -> bool:
	if not allowed:
		return false
	if key == KEY_F1:
		enabled = not enabled
		return true
	if key == KEY_F2:
		panel_open = not panel_open
		return true
	if key == KEY_F3:
		show_debug = not show_debug
		return true
	if not enabled or model == null or model.state != "playing":
		return false
	match key:
		KEY_F5:
			model.gold += 500
		KEY_F6:
			model.gold += 2000
		KEY_F7:
			model.gold += 10000
		KEY_F8:
			model.ai_gold += 2000
		KEY_F9:
			model.wave_timer = 0
		KEY_F10:
			for tower: BattleUnit in model.towers:
				if tower.team == "blue":
					while tower.level < int(model.data.rule("TOWER_MAX_LEVEL", 6)):
						tower.upgrade_tower(model.data, "cannon" if tower.level == 1 else "")
		KEY_F11:
			while model.blue_base.level < int(model.data.rule("MAX_NEXUS_LEVEL", 5)):
				model.blue_base.upgrade_castle(model.data)
		KEY_F12:
			for hero: BattleUnit in model.heroes:
				while hero.level < int(model.data.rule("MAX_HERO_LEVEL", 15)):
					hero.upgrade_hero(model.data)
		KEY_K:
			for unit: BattleUnit in model.all_units():
				if unit.team == "red":
					unit.take_damage(unit.max_hp + unit.shield + 1, "blue", "true", null)
		KEY_G:
			god_mode = not god_mode
			if god_mode:
				model.blue_base.max_hp = 999999
				model.blue_base.hp = 999999
			else:
				model.blue_base._apply_castle_stats(model.data)
		KEY_V:
			model.red_base.take_damage(
				model.red_base.max_hp + model.red_base.shield + 1, "blue", "true", null
			)
		KEY_L:
			model.blue_base.take_damage(
				model.blue_base.max_hp + model.blue_base.shield + 1, "red", "true", null
			)
		_:
			return false
	return true


func debug_lines(model: MatchModel) -> Array[String]:
	var lines: Array[String] = []
	if model == null:
		return lines
	lines.append("DEV MODE: %s" % ("ON" if enabled else "OFF"))
	lines.append("Wave: %d  State: %s" % [model.wave_number, model.state])
	lines.append("Minions: %d  Towers: %d" % [model.minions.size(), model.towers.size()])
	lines.append("Heroes: %d / %d" % [model.heroes.size(), model.enemy_heroes.size()])
	lines.append("Gold: %d  AI: %d" % [model.gold, model.ai_gold])
	lines.append("Kills: %d  Combo: %d" % [model.total_kills, model.max_combo])
	lines.append("Blue HP: %d/%d" % [int(model.blue_base.hp), int(model.blue_base.max_hp)])
	lines.append("Red HP: %d/%d" % [int(model.red_base.hp), int(model.red_base.max_hp)])
	lines.append("Red towers destroyed: %d" % model.red_towers_destroyed)
	lines.append("True boss spawned: %s" % str(model.true_boss_spawned))
	return lines
