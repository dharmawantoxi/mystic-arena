class_name BattleUnit
extends RefCounted

## Data-driven native combat unit for the migrated _core.Game loop.
## Bespoke hero/boss skill scripts and Pygame rig rendering are tracked gaps.
enum Kind { MINION, TOWER, CASTLE, HERO, BOSS }

var id := 0
var kind := Kind.MINION
var unit_type := "goblin"
var team := "blue"
var lane := "mid"
var display_name := "Unit"
var pos := Vector2.ZERO
var radius := 12.0
var alive := true
var max_hp := 100.0
var damage := 10.0
var attack_range := 30.0
var attack_cooldown := 45
var attack_timer := 0
var speed := 1.0
var gold_reward := 0
var armor := 0.0
var magic_resist := 0.0
var regen := 0.0
var level := 1
var tower_type := "archer"
var player_built := false
var shield := 0.0
var shield_max := 0.0
var shield_active := false
var shield_purchased := false
var free_shield_active := false
var castle_damage_reduction := 0.88
var no_damage_timer := 0
var regen_shield_active := false
var status := StatusEffects.new()
var items := UnitInventory.new()
var base_hp := 100.0
var base_damage := 10.0
var kills := 0
var deaths := 0
var damage_dealt := 0.0
var selected := false
var rewarded := false
var death_anim := 0
var respawn_timer := 0
var waypoint := 0
var path := PackedVector2Array()
var destination := Vector2.ZERO
var has_destination := false
var follow_target: BattleUnit
var tactical_target: BattleUnit
var tactical_move := Vector2.ZERO
var has_tactical_move := false
var is_retreating := false
var skill_cooldowns := {"q": 0, "w": 0, "e": 0, "r": 0}
var skill_max := {"q": 300, "w": 240, "e": 420, "r": 900}
var skill_damage := 70.0
var skill_range := 100.0
var color := Color.WHITE
var killed_by: BattleUnit
var boss_class := ""
var defeated := false
var stats: Dictionary = {}

var hp: float:
	get:
		return _hp
	set(value):
		_hp = status.modified_heal(_hp, value)

var _hp := 100.0


func setup_minion(
	data: CoreData,
	minion_type: String,
	team_name: String,
	lane_name: String,
	castle_level: int,
	lane_path: PackedVector2Array
) -> void:
	kind = Kind.MINION
	unit_type = minion_type
	team = team_name
	lane = lane_name
	path = lane_path
	stats = data.rule("MINION_TYPES", {}).get(minion_type, {})
	var nexus: Dictionary = data.rule("NEXUS_LEVELS", {}).get(
		str(castle_level), data.rule("NEXUS_LEVELS", {}).get("1", {})
	)
	var scale := float(nexus.get("minion_scale", 1.0))
	max_hp = int(float(stats.get("hp", 45)) * scale)
	_hp = max_hp
	damage = int(float(stats.get("damage", 5)) * scale)
	speed = float(stats.get("speed", 1.5)) * (1.0 + (scale - 1.0) * 0.3)
	attack_range = float(stats.get("range", 25))
	attack_cooldown = maxi(
		10, int(float(stats.get("attack_cooldown", 45)) / (1.0 + (scale - 1.0) * 0.2))
	)
	gold_reward = int(float(stats.get("gold_reward", 8)) * scale)
	radius = float(stats.get("radius", 9))
	regen = float(stats.get("regen", 0.0)) * scale
	armor = float(stats.get("armor", 0.0))
	magic_resist = float(stats.get("magic_resist", 0.0))
	display_name = str(stats.get("name", minion_type))
	color = data.color(stats.get("color"), Color.GREEN)
	if not path.is_empty():
		waypoint = 0 if team == "blue" else path.size() - 1
		pos = path[waypoint]


func setup_tower(
	data: CoreData, position: Vector2, team_name: String, lane_name: String, player := false
) -> void:
	kind = Kind.TOWER
	unit_type = "tower"
	team = team_name
	lane = lane_name
	pos = position
	player_built = player
	tower_type = "archer"
	level = 1
	radius = 22.0
	gold_reward = 100
	_apply_tower_stats(data)
	shield_max = max_hp * float(data.rule("TOWER_SHIELD_HP_RATIO", 0.4))
	shield = shield_max
	shield_active = bool(data.rule("TOWER_SHIELD_ENABLED", true))


func _apply_tower_stats(data: CoreData) -> void:
	var table: Dictionary = data.rule("TOWER_UPGRADE_PATHS", {}).get(tower_type, {})
	var row: Dictionary = table.get(
		str(level), data.rule("TOWER_UPGRADE_PATHS", {}).get("archer", {}).get("1", {})
	)
	max_hp = float(row.get("hp", 800)) * float(data.rule("TOWER_HP_MULTIPLIER", 2.5))
	_hp = max_hp
	damage = float(row.get("damage", 20))
	attack_range = float(row.get("range", 180))
	attack_cooldown = int(row.get("cd", 35))
	armor = float(row.get("armor", 2 + level))
	magic_resist = float(row.get("magic_resist", 0.0))
	display_name = str(data.rule("TOWER_TYPE_INFO", {}).get(tower_type, {}).get("name", tower_type))
	color = data.color(
		data.rule("TOWER_TYPE_COLORS", {}).get(tower_type, {}).get("main"), Color.GREEN
	)
	stats = row
	shield_max = max_hp * float(data.rule("TOWER_SHIELD_HP_RATIO", 0.4))
	shield = shield_max


func tower_upgrade_cost(data: CoreData, target_type := "") -> int:
	if level >= int(data.rule("TOWER_MAX_LEVEL", 6)):
		return 0
	var path_type := target_type if level == 1 and not target_type.is_empty() else tower_type
	var table: Dictionary = data.rule("TOWER_UPGRADE_PATHS", {}).get(path_type, {})
	return int(table.get(str(level + 1), {}).get("cost", 0))


func upgrade_tower(data: CoreData, target_type := "") -> bool:
	if level >= int(data.rule("TOWER_MAX_LEVEL", 6)):
		return false
	if level == 1:
		if target_type.is_empty() or not data.rule("TOWER_UPGRADE_PATHS", {}).has(target_type):
			return false
		tower_type = target_type
	level += 1
	_apply_tower_stats(data)
	return true


func sell_value(data: CoreData) -> int:
	if not player_built:
		return 0
	var total := 0
	var table: Dictionary = data.rule("TOWER_UPGRADE_PATHS", {}).get(tower_type, {})
	for lvl in range(2, level + 1):
		total += int(table.get(str(lvl), {}).get("cost", 0))
	if regen_shield_active:
		total += int(data.rule("TOWER_REGEN_SHIELD_COST", 850))
	return int(total * 0.5)


func can_activate_regen_shield(data: CoreData) -> bool:
	return (
		kind == Kind.TOWER
		and alive
		and bool(data.rule("TOWER_REGEN_SHIELD_ENABLED", true))
		and level >= int(data.rule("TOWER_REGEN_SHIELD_MIN_LEVEL", 4))
		and not regen_shield_active
	)


func activate_regen_shield(data: CoreData) -> bool:
	if not can_activate_regen_shield(data):
		return false
	regen_shield_active = true
	shield = shield_max
	return true


func setup_castle(data: CoreData, team_name: String, start_level: int) -> void:
	kind = Kind.CASTLE
	unit_type = "castle"
	team = team_name
	pos = (
		Vector2(float(data.rule("BLUE_BASE_X", 100)), float(data.rule("BLUE_BASE_Y", 620)))
		if team == "blue"
		else Vector2(float(data.rule("RED_BASE_X", 1180)), float(data.rule("RED_BASE_Y", 100)))
	)
	radius = float(data.rule("BASE_RADIUS", 45))
	level = clampi(start_level, 1, int(data.rule("MAX_NEXUS_LEVEL", 5)))
	castle_damage_reduction = float(data.rule("CASTLE_SHIELD_DAMAGE_REDUCTION", 0.88))
	_apply_castle_stats(data)
	display_name = str(data.rule("CASTLE_NAMES", {}).get(str(level), "Castle"))
	color = Color("4c8cff") if team == "blue" else Color("ff5c5c")
	free_shield_active = true
	shield_active = true
	shield_max = max_hp * float(data.rule("CASTLE_SHIELD_HP_RATIO", 1.0))
	shield = shield_max


func _apply_castle_stats(data: CoreData) -> void:
	var row: Dictionary = data.rule("NEXUS_LEVELS", {}).get(str(level), {})
	var old_max := max_hp
	var old_hp := _hp
	max_hp = float(row.get("hp", 4000))
	if old_max > 0:
		_hp = minf(max_hp, float(int(max_hp * (old_hp / old_max)) + int(max_hp - old_max) + 500))
	else:
		_hp = max_hp
	damage = float(row.get("damage", 35))
	attack_range = float(row.get("range", 150))
	attack_cooldown = int(row.get("attack_cooldown", 45))
	if shield_purchased:
		var ratio := shield / maxf(1.0, shield_max)
		shield_max = max_hp * float(data.rule("CASTLE_SHIELD_HP_RATIO", 1.0))
		shield = shield_max * ratio


func castle_upgrade_cost(data: CoreData) -> int:
	if level >= int(data.rule("MAX_NEXUS_LEVEL", 5)):
		return 0
	return int(data.rule("NEXUS_LEVELS", {}).get(str(level), {}).get("upgrade_cost", 0))


func upgrade_castle(data: CoreData) -> bool:
	if level >= int(data.rule("MAX_NEXUS_LEVEL", 5)):
		return false
	level += 1
	_apply_castle_stats(data)
	display_name = str(data.rule("CASTLE_NAMES", {}).get(str(level), "Castle"))
	return true


func set_wave(data: CoreData, wave: int) -> void:
	if kind != Kind.CASTLE:
		return
	free_shield_active = wave <= int(data.rule("CASTLE_SHIELD_FREE_WAVES", 10))
	if free_shield_active:
		shield_active = true
		shield_max = max_hp * float(data.rule("CASTLE_SHIELD_HP_RATIO", 1.0))
		shield = shield_max
	elif not shield_purchased:
		shield_active = false
		shield = 0.0


func activate_castle_shield(data: CoreData) -> bool:
	if (
		kind != Kind.CASTLE
		or free_shield_active
		or shield_purchased
		or not bool(data.rule("CASTLE_SHIELD_ENABLED", true))
	):
		return false
	shield_purchased = true
	shield_active = true
	shield_max = max_hp * float(data.rule("CASTLE_SHIELD_HP_RATIO", 1.0))
	shield = shield_max
	no_damage_timer = 0
	return true


func setup_hero(data: CoreData, hero_type: String, team_name: String, position: Vector2) -> void:
	kind = Kind.HERO
	unit_type = hero_type
	team = team_name
	pos = position
	stats = data.hero(hero_type)
	if stats.is_empty():
		stats = data.hero("kaizen")
	display_name = str(stats.get("name", hero_type))
	radius = 16.0
	base_hp = float(stats.get("hp", 550))
	base_damage = float(stats.get("damage", 35))
	speed = float(stats.get("speed", 1.5))
	attack_range = float(stats.get("range", 50))
	attack_cooldown = int(stats.get("attack_cooldown", 35))
	skill_damage = float(stats.get("skill_damage", 70))
	skill_range = float(stats.get("skill_range", 100))
	skill_max.q = int(stats.get("skill_cooldown", 300))
	color = data.color(stats.get("color"), Color.CYAN)
	items = UnitInventory.new(data.data.get("items", {}))
	_apply_hero_level(data)


func _apply_hero_level(data: CoreData) -> void:
	var row: Dictionary = data.rule("HERO_LEVELS", {}).get(str(level), {})
	var old_max := max_hp
	max_hp = int(base_hp * float(row.get("hp_mult", 1.0)))
	if items != null:
		max_hp = items.max_hp(max_hp)
	_hp = max_hp if old_max <= 0 else minf(max_hp, _hp + maxf(0.0, max_hp - old_max))
	damage = base_damage * float(row.get("dmg_mult", 1.0))
	if items != null:
		damage += items.bonus_damage()


func hero_upgrade_cost(data: CoreData) -> int:
	if level >= int(data.rule("MAX_HERO_LEVEL", 15)):
		return 0
	var cost := int(data.rule("HERO_LEVELS", {}).get(str(level), {}).get("upgrade_cost", 0))
	if bool(stats.get("is_boss_hero", false)):
		cost = int(cost * float(data.rule("BOSS_HERO_UPGRADE_COST_MULT", 1.6)))
	return cost


func upgrade_hero(data: CoreData) -> bool:
	if level >= int(data.rule("MAX_HERO_LEVEL", 15)):
		return false
	level += 1
	_apply_hero_level(data)
	return true


func setup_boss(data: CoreData, boss_type: String, lane_path: PackedVector2Array) -> void:
	kind = Kind.BOSS
	unit_type = boss_type
	team = "red"
	path = lane_path
	stats = data.boss(boss_type)
	display_name = str(stats.get("name", boss_type))
	boss_class = str(stats.get("boss_class", "mini"))
	max_hp = float(stats.get("hp", 3000))
	_hp = max_hp
	damage = float(stats.get("damage", 55))
	speed = float(stats.get("speed", 1.0))
	attack_range = float(stats.get("range", 50))
	attack_cooldown = int(stats.get("attack_cooldown", 40))
	gold_reward = int(stats.get("gold_reward", 350))
	radius = float(stats.get("radius", 30))
	armor = float(stats.get("armor", 0.0))
	magic_resist = float(stats.get("magic_resist", 0.0))
	color = data.color(stats.get("color"), Color.PURPLE)
	if not path.is_empty():
		pos = path[path.size() - 1]
		waypoint = path.size() - 1
	for key: String in ["q", "w", "e", "r"]:
		skill_max[key] = int(stats.get("skill_%s_cooldown" % key, 300))


func apply_scaling(hp_mult: float, damage_mult: float, speed_mult: float) -> void:
	max_hp = int(max_hp * hp_mult)
	_hp = max_hp
	damage = int(damage * damage_mult)
	speed *= speed_mult


func apply_debuff(kind_name: String, amount: float, duration: int, source_team := "") -> void:
	status.apply(kind_name, amount, duration, source_team)


func take_damage(
	amount: float, from_team: String, damage_type := "normal", source: BattleUnit = null
) -> float:
	if not alive or amount <= 0.0 or from_team == team:
		return 0.0
	var effective := amount
	if damage_type == "true":
		_hp = maxf(0.0, _hp - effective)
		no_damage_timer = 0
		if source != null:
			source.damage_dealt += effective
			killed_by = source
		if _hp <= 0.0:
			alive = false
			death_anim = 20
			if kind == Kind.BOSS:
				defeated = true
			if kind == Kind.HERO:
				deaths += 1
				items.clear_on_death()
			status.clear()
		return effective
	if damage_type == "physical" or damage_type == "projectile":
		var armor_value := (
			armor
			+ (items.armor() if kind == Kind.HERO and items != null else 0.0)
			- status.armor_shred_amount
		)
		if armor_value > 0:
			effective = maxf(
				1.0, round(effective * (1.0 - armor_value * 0.06 / (1.0 + armor_value * 0.06)))
			)
	elif damage_type == "magic" and magic_resist > 0:
		effective = maxf(1.0, round(effective * (1.0 - magic_resist)))
	if status.dmg_amp_timer > 0:
		effective *= 1.0 + status.dmg_amp_amount
	if kind == Kind.CASTLE and shield_active:
		if shield > 0.0:
			var absorbed := minf(shield, effective)
			shield -= absorbed
			effective -= absorbed
		if effective > 0.0:
			effective = float(int(effective * (1.0 - castle_damage_reduction)))
	elif shield_active and shield > 0.0:
		var absorbed := minf(shield, effective)
		shield -= absorbed
		effective -= absorbed
	_hp = maxf(0.0, _hp - effective)
	no_damage_timer = 0
	if source != null:
		source.damage_dealt += effective
		killed_by = source
	if _hp <= 0.0:
		alive = false
		death_anim = 20
		if kind == Kind.BOSS:
			defeated = true
		if kind == Kind.HERO:
			deaths += 1
			items.clear_on_death()
		status.clear()
	return effective


func heal(amount: float) -> void:
	if alive:
		hp = minf(max_hp, _hp + amount)


func tick_timers(data: CoreData) -> void:
	attack_timer = maxi(0, attack_timer - 1)
	for key: String in skill_cooldowns:
		skill_cooldowns[key] = maxi(0, int(skill_cooldowns[key]) - 1)
	var burn := status.tick()
	if burn > 0 and alive:
		take_damage(burn, status.burn_team if not status.burn_team.is_empty() else team, "fire")
	no_damage_timer += 1
	if alive and regen > 0.0:
		heal(regen)
	if kind == Kind.TOWER:
		if (
			regen_shield_active
			and no_damage_timer >= int(data.rule("TOWER_REGEN_SHIELD_DELAY", 180))
		):
			shield = minf(shield_max, shield + float(data.rule("TOWER_REGEN_SHIELD_RATE", 1.8)))
		if (
			bool(data.rule("TOWER_HP_REGEN_ENABLED", true))
			and no_damage_timer >= int(data.rule("TOWER_HP_REGEN_DELAY", 300))
		):
			var cap := max_hp * float(data.rule("TOWER_HP_REGEN_MAX_RATIO", 0.5))
			if _hp < cap:
				_hp = minf(cap, _hp + float(data.rule("TOWER_HP_REGEN_RATE", 0.3)))
	if (
		kind == Kind.CASTLE
		and shield_active
		and no_damage_timer >= int(data.rule("CASTLE_SHIELD_REGEN_DELAY", 120))
	):
		shield = minf(shield_max, shield + float(data.rule("CASTLE_SHIELD_REGEN_RATE", 3.5)))
	if kind == Kind.HERO and items != null:
		heal(items.hp_regen() / 60.0)


func move_toward_point(point: Vector2) -> void:
	destination = point
	has_destination = true
	follow_target = null
	is_retreating = false


func effective_speed() -> float:
	return status.effective_speed(
		speed, items.move_speed_pct() if kind == Kind.HERO and items != null else 0.0
	)


func effective_attack_cd() -> int:
	var base := attack_cooldown
	if kind == Kind.HERO and items != null:
		base = int(round(base / items.attack_speed_mult()))
	return status.effective_attack_cd(base)


func respawn(_data: CoreData) -> void:
	alive = true
	rewarded = false
	_hp = max_hp
	status.clear()
	pos = Vector2(160, 590) if team == "blue" else Vector2(1120, 130)
	destination = Vector2.ZERO
	has_destination = false
	follow_target = null
	tactical_target = null
	has_tactical_move = false
	if kind == Kind.HERO and items != null:
		items.deliver_pending(attack_range, is_magic_hero())


func is_magic_hero() -> bool:
	var role := str(stats.get("role", "")).to_lower()
	for keyword: String in ["mage", "caster", "sorcerer", "magic", "warlock", "necro"]:
		if keyword in role:
			return true
	return false


func cast_skill(key: String, enemies: Array[BattleUnit]) -> bool:
	if kind != Kind.HERO or not alive or status.stun_timer > 0 or not key in skill_cooldowns:
		return false
	if int(skill_cooldowns[key]) > 0:
		return false
	var target: BattleUnit = null
	var best := skill_range
	for enemy: BattleUnit in enemies:
		if enemy.alive and enemy.team != team:
			var dist := pos.distance_to(enemy.pos)
			if dist <= best:
				best = dist
				target = enemy
	if target == null:
		return false
	var mult: float = {"q": 1.0, "w": 0.65, "e": 0.85, "r": 1.8}[key]
	var amount: float = skill_damage * mult * (1.0 - status.skill_down_amount)
	target.take_damage(amount, team, "magic", self)
	if key == "e":
		heal(max_hp * 0.08)
	if key == "r":
		for enemy: BattleUnit in enemies:
			if (
				enemy != target
				and enemy.alive
				and enemy.team != team
				and enemy.pos.distance_to(target.pos) <= 80.0
			):
				enemy.take_damage(amount * 0.5, team, "magic", self)
	var cd := int(skill_max[key])
	if items != null:
		cd = int(round(cd * (1.0 - items.cooldown_reduction())))
	skill_cooldowns[key] = cd
	if items != null and items.spell_vamp() > 0.0:
		heal(skill_damage * items.spell_vamp())
	return true
