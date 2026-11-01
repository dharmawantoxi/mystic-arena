class_name BattleUnit
extends RefCounted

## Native combat unit for _core.Game and _entity.py.
## Bespoke skills are transpiled into entities/generated; visuals use baked strips.
enum Kind { MINION, TOWER, CASTLE, HERO, BOSS }

const HeroSkillKit = preload("res://scripts/entities/generated/HeroSkillKit.gd")
const BossKit = preload("res://scripts/entities/generated/BossKit.gd")

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
var world: RefCounted
var kit: Dictionary = {}
var item_state: Dictionary = {}
var target: BattleUnit
var facing := 1
var pulse := 0.0
var anim_time := 0
var is_moving := false
var attack_anim_timer := 0
var hurt_flash_timer := 0
var spawn_anim := 20
var upgrade_flash := 0
var shoot_flash_timer := 0
var active_skill := ""
var active_skill_timer := 0
var auto_cast_enabled := true
var auto_cast_check_timer := 0
var destination_auto := false
var hunt_range := 900.0
var aggro_range := 250.0
var retreat_hp_ratio := 0.20
var heal_target_ratio := 0.80
var base_heal_rate := 3.0
var passive_heal_rate := 0.15
var dmg_school := "physical"
var is_melee_hero := false
var ai_level := 1
var tower_kind := "outer"
var nexus_level := 1
var base_speed := 1.0
var ability_timer := 0
var ability_cooldown_max := 240
var ability_damage := 100.0
var ability_range := 150.0
var ability2_timer := 0
var ability2_cooldown_max := 0
var ability2_heal_pct := 0.0
var entrance_timer := 0
var is_enraged := false
var enrage_triggered := false
var damage_reduction := 0.20
var max_damage_per_hit := 0
var tenacity := 0.50
var defense_boost := false
var defense_timer := 0
var cleave_radius := 80.0
var cleave_ratio := 0.40
var basic_attack_seq := 0
var attack_facing := 1
var attack_lock_timer := 0
var kite_mode := "hold"
var projectiles: Array[Dictionary] = []
var bullets: Array[Dictionary] = []

var hp: float:
	get:
		return _hp
	set(value):
		_hp = status.modified_heal(_hp, value)

var hero_type: String:
	get:
		return unit_type
	set(value):
		unit_type = value

var range: float:
	get:
		return attack_range
	set(value):
		attack_range = value

var skill_data: Dictionary:
	get:
		return stats

var move_speed: float:
	get:
		return speed * 60.0
	set(value):
		speed = value / 60.0
		base_speed = speed

var attack_cooldown_seconds: float:
	get:
		return float(attack_cooldown) / 60.0
	set(value):
		attack_cooldown = maxi(1, int(round(value * 60.0)))

var skill_timer: int:
	get:
		return int(skill_cooldowns.get("q", 0))
	set(value):
		skill_cooldowns["q"] = value

var w_cooldown: int:
	get:
		return int(skill_cooldowns.get("w", 0))
	set(value):
		skill_cooldowns["w"] = value

var e_cooldown: int:
	get:
		return int(skill_cooldowns.get("e", 0))
	set(value):
		skill_cooldowns["e"] = value

var r_cooldown: int:
	get:
		return int(skill_cooldowns.get("r", 0))
	set(value):
		skill_cooldowns["r"] = value

var skill_cooldown_max: int:
	get:
		return int(skill_max.get("q", 300))
	set(value):
		skill_max["q"] = value

var w_cooldown_max: int:
	get:
		return int(skill_max.get("w", 240))
	set(value):
		skill_max["w"] = value

var e_cooldown_max: int:
	get:
		return int(skill_max.get("e", 420))
	set(value):
		skill_max["e"] = value

var r_cooldown_max: int:
	get:
		return int(skill_max.get("r", 900))
	set(value):
		skill_max["r"] = value

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


func can_activate_castle_shield(data: CoreData) -> bool:
	return (
		kind == Kind.CASTLE
		and not free_shield_active
		and not shield_purchased
		and bool(data.rule("CASTLE_SHIELD_ENABLED", true))
	)


func activate_castle_shield(data: CoreData) -> bool:
	if not can_activate_castle_shield(data):
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
	is_melee_hero = attack_range <= 80.0
	if is_melee_hero:
		attack_range = clampf(attack_range, 50.0, 80.0)
		base_hp *= 1.15
		base_damage *= 1.20
		speed *= 1.18
		attack_cooldown = int(attack_cooldown * 0.88)
	else:
		attack_range = clampf(attack_range, 120.0, 220.0)
	base_speed = speed
	dmg_school = "magic" if is_magic_hero() else "physical"
	_apply_hero_level(data)
	HeroSkillKit.init_state(self)


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
	base_damage = damage
	base_speed = speed
	ability_cooldown_max = int(stats.get("ability_cooldown", 240))
	ability_timer = ability_cooldown_max
	ability_damage = float(stats.get("ability_damage", 100))
	ability_range = float(stats.get("ability_range", 150))
	entrance_timer = 180 if boss_class == "true" else 120
	damage_reduction = 0.30 if boss_class == "true" else 0.20
	max_damage_per_hit = int(max_hp * (0.08 if boss_class == "true" else 0.12))
	kit = BossKit.DEFAULT_KIT.duplicate(true)
	kit["kit_ready"] = false


func apply_scaling(hp_mult: float, damage_mult: float, speed_mult: float) -> void:
	max_hp = int(max_hp * hp_mult)
	_hp = max_hp
	damage = int(damage * damage_mult)
	base_damage = damage
	ability_damage *= damage_mult
	speed *= speed_mult
	base_speed = speed
	max_damage_per_hit = int(max_hp * (0.08 if boss_class == "true" else 0.12))


func apply_debuff(kind_name: String, amount: float, duration: int, source_team := "") -> void:
	if kind == Kind.BOSS and kind_name in ["slow", "atk_slow"]:
		amount = minf(0.35, amount * (1.0 - tenacity))
		duration = int(duration * (1.0 - tenacity))
	status.apply(kind_name, amount, duration, source_team)


func item_timer(key: String) -> int:
	return int(item_state.get(key, 0))


func take_damage(
	amount: float,
	from_team: String,
	damage_type := "normal",
	source: BattleUnit = null,
	school := ""
) -> float:
	if not alive or amount <= 0.0 or from_team == team:
		return 0.0
	var resolved := EntityCombat.resolve_school(self, damage_type, source, school)
	var effective := amount
	if kind == Kind.HERO:
		var rng := RandomNumberGenerator.new()
		if world != null:
			rng = world.rng
		else:
			rng.randomize()
		var defense := EntityCombat.hero_pre_damage(self, amount, resolved, source, rng)
		if bool(defense.miss):
			if float(defense.reflect) > 0.0 and source != null:
				source.take_damage(float(defense.reflect), team, "true", self)
			return 0.0
		effective = float(defense.amount)
		if float(defense.reflect) > 0.0 and source != null:
			source.take_damage(float(defense.reflect), team, "true", self)
	elif kind == Kind.BOSS:
		effective = EntityCombat.boss_pre_damage(self, amount, resolved, source)
		hurt_flash_timer = 8
	if damage_type == "true":
		_apply_hp_loss(effective, source)
		return effective
	if resolved == "physical":
		var armor_value := (
			armor
			+ (items.armor() if kind == Kind.HERO and items != null else 0.0)
			- status.armor_shred_amount
		)
		effective = maxf(1.0, round(effective * (1.0 - EntityCombat.armor_reduction(armor_value))))
	elif resolved == "magic" and magic_resist > 0:
		effective = maxf(1.0, round(effective * (1.0 - minf(0.60, magic_resist))))
	if status.dmg_amp_timer > 0 and kind != Kind.BOSS:
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
	_apply_hp_loss(effective, source)
	return effective


func _apply_hp_loss(effective: float, source: BattleUnit) -> void:
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
			if items != null:
				items.clear_on_death()
		status.clear()


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


func cast_skill(key: String, _enemies: Array[BattleUnit]) -> bool:
	if kind != Kind.HERO or not alive or status.stun_timer > 0 or not key in skill_cooldowns:
		return false
	if int(skill_cooldowns[key]) > 0:
		return false
	if world == null:
		return false
	var towers: Array = world.towers
	var bases: Array = [world.blue_base, world.red_base]
	var ok := false
	match key:
		"q":
			ok = HeroSkillKit.cast_q(self, world.all_units(), towers, bases)
		"w":
			ok = HeroSkillKit.cast_w(self, world.all_units(), towers, bases)
		"e":
			ok = HeroSkillKit.cast_e(self, world.all_units(), towers, bases)
		"r":
			ok = HeroSkillKit.cast_r(self, world.all_units(), towers, bases)
	if ok:
		if items != null and items.cooldown_reduction() > 0.0:
			skill_cooldowns[key] = int(
				round(int(skill_cooldowns[key]) * (1.0 - items.cooldown_reduction()))
			)
		if items != null and items.spell_vamp() > 0.0:
			heal(skill_damage * items.spell_vamp())
	return ok


func kit_enemies(units: Array, towers: Array, bases: Array) -> Array:
	var result: Array = []
	for group: Array in [units, towers, bases]:
		for unit: Variant in group:
			if unit is BattleUnit and unit.alive and unit.team != team:
				result.append(unit)
	return result


func kit_skill_damage() -> int:
	var amp := 1.0 + (status.dmg_amp_amount if status.dmg_amp_timer > 0 else 0.0)
	return int(round(skill_damage * amp * (1.0 - status.skill_down_amount)))


func kit_catalog_all() -> Dictionary:
	return world.data.data.get("heroes", {}) if world != null else {}


func kit_hero_levels() -> Dictionary:
	return world.data.rule("HERO_LEVELS", {}) if world != null else {}


func kit_hit(
	enemy: BattleUnit, dmg: float, from_team: String, source: BattleUnit, school: String
) -> void:
	if enemy != null:
		enemy.take_damage(dmg, from_team, "magic", source, school)


func kit_slow(enemy: BattleUnit, amount: float, frames: int) -> void:
	if enemy != null:
		enemy.apply_debuff("slow", amount, frames)


func kit_lock(enemy: BattleUnit, frames: float) -> void:
	if enemy != null:
		enemy.attack_timer = maxi(enemy.attack_timer, int(frames))


func kit_atk_timer(enemy: BattleUnit) -> int:
	return enemy.attack_timer if enemy != null else 0


func kit_has_atk_timer(_enemy: BattleUnit) -> bool:
	return true


func kit_has_hp(_enemy: BattleUnit) -> bool:
	return true


func kit_unit_alive(enemy: BattleUnit) -> bool:
	return enemy != null and enemy.alive


func kit_has_slow(_enemy: BattleUnit) -> bool:
	return true


func _shake(amount: float) -> void:
	kit_shake(amount)


func _callout(text: String, callout_color: Variant = Color.WHITE) -> void:
	kit_popup(text, callout_color if callout_color is Color else Color.WHITE)


func kit_shake(amount: float) -> void:
	if world != null:
		world.add_shake(amount)


func kit_sound(_volume: float) -> void:
	if world != null:
		world.add_effect(pos, "sound", color, 8)


func kit_popup(text: String, popup_color: Color) -> void:
	if world != null:
		world.add_popup(pos, text, popup_color)


func kit_skill_proj(enemy: BattleUnit) -> void:
	if world != null:
		EntityProjectiles.spawn_hero(world, self, enemy, 0.0, false, 13.0, true)


func kit_fx_cast(skill: String) -> void:
	active_skill = skill
	active_skill_timer = 60
	if world != null:
		world.add_effect(pos, "cast_" + skill, color, 40)


func kit_fx_impact(x: float, y: float, radius: float, skill: String) -> void:
	if world != null:
		world.add_effect(Vector2(x, y), "impact_" + skill, color, int(radius))


func kit_get_stats() -> Dictionary:
	var result := stats.duplicate(true)
	var mult := 1.0 - status.skill_down_amount
	if is_enraged:
		mult *= 1.25
	for key: String in result:
		if "damage" in key and result[key] is float:
			result[key] = float(result[key]) * mult
	return result


func kit_stats_full() -> Dictionary:
	return stats


func kit_skill_hit(enemy: BattleUnit, dmg: float) -> void:
	if enemy != null:
		enemy.take_damage(dmg, team, "magic", self)


func kit_apply_slow(enemy: BattleUnit, amount: float, frames: int) -> void:
	kit_slow(enemy, amount, frames)


func kit_lock_attack(enemy: BattleUnit, frames: float) -> void:
	kit_lock(enemy, frames)


func kit_can_move(_enemy: BattleUnit) -> bool:
	return true
