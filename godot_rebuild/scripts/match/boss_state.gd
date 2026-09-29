# gdlint:disable=max-file-lines,max-line-length,class-definitions-order
extends "res://scripts/combat/unit_state.gd"
## Layer 7d: Boss entity state (port of Boss.__init__, apply_scaling and tenacity
## debuff overrides in bosses/base_boss.py:345-555). Update/take_damage follow in
## later layers.

const Rounding = preload("res://scripts/combat/damage_rules.gd")
const FALLBACK_SPAWN := Vector2(1130.0, 100.0)
const BLUE_BASE_POS := Vector2(100.0, 620.0)
const RANGED_KITE_BOSSES := [
	"ancient_apparition",
	"morgath",
	"razak",
	"varkul",
	"xerathis",
	"nyzrak",
	"syrentha",
	"thalgryn",
	"nyxarath",
	"malzareth",
	"akashari",
	"vorenmarr"
]
const SMART_AI_BOSSES := [
	"abaddon",
	"alchemist",
	"ancient_apparition",
	"ignis_drachorn",
	"gornak",
	"morgath",
	"drakar",
	"razak",
	"khalros",
	"gorath",
	"varkul",
	"xerathis",
	"nyzrak",
	"zharok",
	"pyrenth",
	"vokrahn",
	"nyxara",
	"gravefang",
	"vhalzun",
	"kunkka",
	"gravewake",
	"syrentha",
	"thalgryn",
	"nyxarath",
	"vhorethzir",
	"vaerith",
	"xirthalis",
	"vhyssarion",
	"kenshiro",
	"khazan",
	"wiro",
	"naraka",
	"krognarr",
	"raz",
	"vraskhan",
	"aurethzar",
	"aeralith",
	"aurex",
	"nyxareva",
	"thalakryon",
	"aurelix",
	"aurelyssa",
	"vargrath",
	"nazulmor",
	"kaeldris",
	"pyraklos",
	"velmyrth",
	"solvarin",
	"malzareth",
	"akashari",
	"vorenmarr",
	"azureth",
	"luminar",
	"solara",
	"pyraethis",
	"auroth",
	"morvein",
	"thorvak",
	"yamako",
	"ignirus",
	"leoric",
	"shirotaka",
	"seiryukong",
	"kaelthorn",
	"solvanth",
	"xyrael",
	"nyxareth",
	"cryssalia",
	"kaelthar",
	"morkhaera",
	"aurelion",
	"akahime",
	"nyxthrael",
	"sylvantheros",
	"vaelindra",
	"astraelion",
	"morvaenthir",
	"thornvaegrim",
	"morthraxis"
]

var boss_type := ""
var name := ""
var title := ""
var boss_class := "mini"
var max_hp := 0
var damage := 0
var base_damage := 0
var _speed_value := 0.0
var speed: float:
	get:
		if slow_timer > 0:
			return _speed_value * (1.0 - slow_amount)
		return _speed_value
	set(value):
		_speed_value = value
var base_speed := 0.0
var range_px := 0
var attack_cooldown := 0
var radius := 0
var gold_reward := 0
var color: Array = []
var color_dark: Array = []
var ability_cooldown_max := 0
var _ability_damage_value := 0
var ability_damage: int:
	get:
		if skill_down_timer > 0:
			var factor := maxf(0.0, 1.0 - skill_down_amount)
			return Rounding.rounded_like_python(float(_ability_damage_value) * factor)
		return _ability_damage_value
	set(value):
		_ability_damage_value = value
var ability_range := 0
var entrance_text := ""
var entrance_color: Array = []
var ability2_cooldown_max := 0
var ability2_heal_pct := 0.0
var ability2_timer := 0
var lane_path := PackedVector2Array()
var direction := -1
var timer := 0
var ability_timer := 0
var defeated := false
var damage_reduction := 0.20
var tenacity := 0.50
var max_damage_per_hit := 0
var armor := 12
var magic_resist := 0.10
var resist_profile := "balanced"
var is_enraged := false
var enrage_triggered := false
var enrage_pulse := 0.0
var cleave_radius := 80
var cleave_ratio := 0.40
var hp_scaling_mult := 1.0
var dmg_scaling_mult := 1.0
var spd_scaling_mult := 1.0
var anim_time := 0
var pulse := 0.0
var hurt_flash_timer := 0
var entrance_timer := 120
var ability_active := false
var ability_active_timer := 0
var is_moving := false
var prev_position := Vector2.ZERO
var attack_lock_timer := 0
var kite_mode := "hold"
var stun_timer := 0
var defense_boost := false
var killed_by_source: Object = null
var pos_x := 0.0
var pos_y := 0.0
var prev_x := 0.0
var prev_y := 0.0
var attack_facing := 0
var basic_attack_seq := 0
var min_distance := 200
var prefer_distance := 280
var target_ref: Object = null


func _init(kind: String = "", path: Variant = PackedVector2Array(), stats: Dictionary = {}) -> void:
	boss_type = kind
	team = 1
	lane = 1
	name = String(stats.get("name", kind))
	title = String(stats.get("title", ""))
	boss_class = String(stats.get("boss_class", "mini"))
	max_hp = int(stats.get("hp", 0))
	hp = float(max_hp)
	damage = int(stats.get("damage", 0))
	base_damage = damage
	speed = float(stats.get("speed", 0.0))
	base_speed = _speed_value
	range_px = int(stats.get("range", 0))
	attack_cooldown = int(stats.get("attack_cooldown", 0))
	radius = int(stats.get("radius", 0))
	gold_reward = int(stats.get("gold_reward", 0))
	color = stats.get("color", []).duplicate()
	color_dark = stats.get("color_dark", []).duplicate()
	ability_cooldown_max = int(stats.get("ability_cooldown", 0))
	ability_damage = int(stats.get("ability_damage", 0))
	ability_range = int(stats.get("ability_range", 0))
	entrance_text = String(stats.get("entrance_text", ""))
	entrance_color = stats.get("entrance_color", []).duplicate()
	ability2_cooldown_max = int(stats.get("ability2_cooldown", 0))
	ability2_heal_pct = float(stats.get("ability2_heal_pct", 0.0))
	ability2_timer = 0
	lane_path = PackedVector2Array()
	if path is PackedVector2Array:
		lane_path = (path as PackedVector2Array).duplicate()
	elif path is Array:
		for point in path as Array:
			if point is Vector2:
				lane_path.append(point)
			elif point is Array and (point as Array).size() >= 2:
				lane_path.append(Vector2(float(point[0]), float(point[1])))
	if not lane_path.is_empty():
		position = lane_path[lane_path.size() - 1]
	else:
		position = FALLBACK_SPAWN
	pos_x = float(position.x)
	pos_y = float(position.y)
	waypoint_index = lane_path.size() - 1
	direction = -1
	alive = true
	timer = 0
	ability_timer = 0
	target_id = -1
	defeated = false
	var is_true := boss_class == "true"
	damage_reduction = 0.30 if is_true else 0.20
	tenacity = 0.50
	max_damage_per_hit = int(max_hp * (0.08 if is_true else 0.12))
	var def_armor := 18 if is_true else 12
	var def_mr := 0.20 if is_true else 0.10
	armor = clampi(int(stats.get("armor", def_armor)), 0, 40)
	magic_resist = clampf(float(stats.get("magic_resist", def_mr)), 0.0, 0.45)
	resist_profile = String(stats.get("resist_profile", "balanced"))
	is_enraged = false
	enrage_triggered = false
	enrage_pulse = 0.0
	cleave_radius = 80
	cleave_ratio = 0.40
	hp_scaling_mult = 1.0
	dmg_scaling_mult = 1.0
	spd_scaling_mult = 1.0
	anim_time = 0
	pulse = 0.0
	hurt_flash_timer = 0
	entrance_timer = 180 if is_true else 120
	ability_active = false
	ability_active_timer = 0
	is_moving = false
	prev_position = position
	prev_x = pos_x
	prev_y = pos_y
	attack_facing = 0
	basic_attack_seq = 0
	attack_lock_timer = 0
	kite_mode = "hold"
	min_distance = int(stats.get("min_distance", 200))
	prefer_distance = int(stats.get("prefer_distance", 280))
	target_ref = null
	burn_tick_cd = 30
	stun_timer = 0
	defense_boost = false
	killed_by_source = null


func apply_scaling(hp_mult: float = 1.0, dmg_mult: float = 1.0, spd_mult: float = 1.0) -> void:
	# Port of Boss.apply_scaling (bosses/base_boss.py:513).
	hp_scaling_mult = hp_mult
	dmg_scaling_mult = dmg_mult
	spd_scaling_mult = spd_mult
	max_hp = int(max_hp * hp_mult)
	hp = float(max_hp)
	damage = int(damage * dmg_mult)
	base_damage = damage
	ability_damage = int(ability_damage * dmg_mult)
	speed = speed * spd_mult
	base_speed = speed
	max_damage_per_hit = int(max_hp * (0.08 if boss_class == "true" else 0.12))


func apply_slow(amount: float, duration: int) -> void:
	# Port of Boss.apply_slow: 50% tenacity on magnitude and duration, 35% cap.
	if not alive:
		return
	var reduced_amount := minf(0.35, amount * (1.0 - tenacity))
	var reduced_duration := int(duration * (1.0 - tenacity))
	if reduced_amount > slow_amount or slow_timer < reduced_duration:
		slow_amount = reduced_amount
		slow_timer = reduced_duration


func apply_debuff(kind: String, amount: float, duration: int, source_team: int = -1) -> void:
	# Port of Boss.apply_debuff + TowerDebuffMixin.apply_debuff.
	if not alive:
		return
	if kind == "slow":
		apply_slow(amount, duration)
		return
	if kind == "atk_slow":
		amount = minf(0.35, amount * (1.0 - tenacity))
		duration = int(duration * (1.0 - tenacity))
		if amount > atk_slow_amount or atk_slow_timer < duration:
			atk_slow_amount = amount
			atk_slow_timer = duration
	elif kind == "skill_down":
		if amount > skill_down_amount or skill_down_timer < duration:
			skill_down_amount = amount
			skill_down_timer = duration
	elif kind == "anti_heal":
		if amount > anti_heal_amount or anti_heal_timer < duration:
			anti_heal_amount = amount
			anti_heal_timer = duration
	elif kind == "burn":
		if burn_timer <= 0:
			burn_dps = amount
			burn_accum = 0.0
			burn_tick_cd = 30
		else:
			burn_dps = maxf(burn_dps, amount)
		burn_timer = maxi(burn_timer, duration)
		if source_team >= 0:
			burn_team = source_team


func apply_stun(duration: int) -> void:
	# Port of TowerDebuffMixin.apply_stun for bosses (55% duration resist).
	if not alive:
		return
	var reduced := int(duration * 0.45)
	if reduced <= 0:
		return
	if reduced > stun_timer:
		stun_timer = reduced


func clear_tower_debuffs() -> void:
	# Port of TowerDebuffMixin.clear_tower_debuffs (_core.py:942).
	slow_amount = 0.0
	slow_timer = 0
	atk_slow_amount = 0.0
	atk_slow_timer = 0
	skill_down_amount = 0.0
	skill_down_timer = 0
	anti_heal_amount = 0.0
	anti_heal_timer = 0
	burn_dps = 0.0
	burn_timer = 0
	burn_accum = 0.0
	burn_tick_cd = 30
	burn_team = -1
	stun_timer = 0
	armor_shred_amount = 0.0
	armor_shred_timer = 0
	dmg_amp_amount = 0.0
	dmg_amp_timer = 0
	heal_amp_amount = 0.0
	heal_amp_timer = 0
	blind_amount = 0.0
	blind_timer = 0


func take_damage(
	raw_damage: int,
	_from_team: int = 0,
	damage_type: String = "normal",
	source: Object = null,
	school: String = "",
	rng: RandomNumberGenerator = null
) -> int:
	# Port of Boss.take_damage (bosses/base_boss.py:5978).
	if damage_type == "normal" and raw_damage > 0 and source != null:
		var true_strike := false
		var inv: Variant = source.get("items")
		if inv != null and inv.has_method("has_true_strike"):
			true_strike = bool(inv.has_true_strike())
		var b_timer := int(source.get("blind_timer") if source.get("blind_timer") != null else 0)
		var b_amount := float(
			source.get("blind_amount") if source.get("blind_amount") != null else 0.0
		)
		if not true_strike and b_timer > 0:
			var roll := rng.randf() if rng != null else randf()
			if roll < b_amount:
				return 0
	var dmg := raw_damage
	if dmg > 0:
		if dmg_amp_timer > 0:
			dmg = Rounding.rounded_like_python(float(dmg) * (1.0 + dmg_amp_amount))
		if damage_type != "fire" and armor_shred_amount > 0.0:
			dmg = Rounding.rounded_like_python(
				float(dmg) * (1.0 + minf(1.0, armor_shred_amount * 0.06))
			)
	var resolved_school := ""
	if not school.is_empty():
		if school in ["physical", "magic"]:
			resolved_school = school
	elif damage_type not in ["fire", "ice", "heal", "crit"] and source != null:
		var src_school: Variant = source.get("dmg_school")
		if src_school in ["physical", "magic"]:
			resolved_school = String(src_school)
	if dmg > 0 and resolved_school == "physical" and armor > 0:
		var red := float(armor) * 0.06 / (1.0 + float(armor) * 0.06)
		red = minf(0.60, maxf(0.0, red - armor_shred_amount * 0.06))
		dmg = maxi(1, Rounding.rounded_like_python(float(dmg) * (1.0 - red)))
	elif dmg > 0 and resolved_school == "magic" and magic_resist > 0.0:
		dmg = maxi(1, Rounding.rounded_like_python(float(dmg) * (1.0 - magic_resist)))
	var resilience := damage_reduction
	if defense_boost:
		resilience = maxf(resilience, 0.45)
	var effective_damage := int(float(dmg) * (1.0 - resilience))
	var cap := max_damage_per_hit if max_damage_per_hit > 0 else int(max_hp * 0.10)
	if effective_damage > cap:
		effective_damage = cap
	effective_damage = maxi(1, effective_damage)
	hp -= float(effective_damage)
	hurt_flash_timer = 8
	if hp <= 0.0:
		hp = 0.0
		alive = false
		defeated = true
		killed_by_source = source
		clear_tower_debuffs()
	return effective_damage


func set_pos(nx: float, ny: float) -> void:
	pos_x = nx
	pos_y = ny
	position = Vector2(nx, ny)


func set_hp_with_modifiers(value: float) -> void:
	# Port of TowerDebuffMixin.hp setter (_core.py:861): anti-heal and heal-amp
	# scale positive HP gains in that exact order.
	var next_val := value
	if next_val > hp and anti_heal_timer > 0:
		next_val = hp + (next_val - hp) * (1.0 - anti_heal_amount)
	if next_val > hp and heal_amp_timer > 0:
		next_val = hp + (next_val - hp) * (1.0 + heal_amp_amount)
	hp = next_val


func eff_attack_cd(base_cd: int) -> int:
	# Port of TowerDebuffMixin._eff_attack_cd (_core.py:974).
	if stun_timer > 0:
		return 9999
	if atk_slow_timer > 0:
		var factor := maxf(0.05, 1.0 - atk_slow_amount)
		return maxi(1, Rounding.rounded_like_python(float(base_cd) / factor))
	return base_cd


func tick_tower_debuffs() -> void:
	# Port of TowerDebuffMixin._tick_tower_debuffs (_core.py:983).
	if slow_timer > 0:
		slow_timer -= 1
		if slow_timer <= 0:
			slow_amount = 0.0
	if atk_slow_timer > 0:
		atk_slow_timer -= 1
		if atk_slow_timer <= 0:
			atk_slow_amount = 0.0
	if skill_down_timer > 0:
		skill_down_timer -= 1
		if skill_down_timer <= 0:
			skill_down_amount = 0.0
	if anti_heal_timer > 0:
		anti_heal_timer -= 1
		if anti_heal_timer <= 0:
			anti_heal_amount = 0.0
	if stun_timer > 0:
		stun_timer -= 1
	tick_item_debuffs()
	if burn_timer > 0:
		burn_timer -= 1
		burn_accum += burn_dps / 60.0
		burn_tick_cd -= 1
		if burn_tick_cd <= 0:
			burn_tick_cd = 30
			var dmg := int(burn_accum)
			if dmg > 0 and alive:
				burn_accum -= float(dmg)
				take_damage(dmg, burn_team if burn_team >= 0 else team, "fire")
		if burn_timer <= 0:
			burn_dps = 0.0
			burn_accum = 0.0


func _use_heal_ability() -> void:
	# Port of Boss._use_heal_ability (bosses/base_boss.py:5955).
	if ability2_cooldown_max <= 0:
		return
	ability2_timer = ability2_cooldown_max
	var heal_amount := int(max_hp * ability2_heal_pct)
	set_hp_with_modifiers(minf(float(max_hp), hp + float(heal_amount)))


func _face(dx: float, dy: float) -> void:
	# Port of Boss._face (bosses/base_boss.py:988).
	if attack_lock_timer > 0:
		if attack_facing != 0:
			direction = attack_facing
		return
	if absf(dx) < 0.35 * maxf(1e-6, absf(dy)):
		return
	direction = 1 if dx > 0.0 else -1


func _lane_target() -> Vector2:
	if not lane_path.is_empty() and waypoint_index >= 0 and waypoint_index < lane_path.size():
		return lane_path[waypoint_index]
	return BLUE_BASE_POS


func _advance_waypoint() -> bool:
	if lane_path.is_empty():
		return false
	waypoint_index -= 1
	return waypoint_index >= 0


func _move_forward() -> void:
	# Port of Boss._move_forward (bosses/base_boss.py:1015).
	var budget := float(speed)
	if budget <= 0.0:
		return
	var guard := 0
	while budget > 1e-3 and guard < 16:
		guard += 1
		var target_pt := _lane_target()
		var tx := float(target_pt.x)
		var ty := float(target_pt.y)
		var dx := tx - pos_x
		var dy := ty - pos_y
		var d := sqrt(dx * dx + dy * dy)
		var has_next := (not lane_path.is_empty()) and waypoint_index >= 0
		if d <= 1e-6:
			if not has_next:
				break
			_advance_waypoint()
			continue
		if d <= budget:
			set_pos(tx, ty)
			budget -= d
			_face(dx, dy)
			if has_next:
				_advance_waypoint()
			continue
		set_pos(pos_x + budget * dx / d, pos_y + budget * dy / d)
		_face(dx, dy)
		budget = 0.0


func _use_ability(enemies: Array, hit_cb: Callable) -> void:
	# Port of Boss._use_ability (bosses/base_boss.py:1073).
	ability_timer = ability_cooldown_max
	ability_active = true
	ability_active_timer = 60
	for enemy in enemies:
		var ex := float(enemy.position.x)
		var ey := float(enemy.position.y)
		var dist := sqrt((ex - pos_x) * (ex - pos_x) + (ey - pos_y) * (ey - pos_y))
		if dist <= float(ability_range):
			if hit_cb.is_valid():
				hit_cb.call(enemy, ability_damage, "neutral")
			if enemy.get("attack_timer") != null:
				enemy.attack_timer = maxi(int(enemy.attack_timer), 60)


func step_update(enemies: Array, hit_cb: Callable = Callable()) -> void:
	# Port of Boss.update (bosses/base_boss.py:567).
	if not alive:
		return
	anim_time += 1
	pulse += 0.1
	var moved := sqrt((pos_x - prev_x) * (pos_x - prev_x) + (pos_y - prev_y) * (pos_y - prev_y))
	prev_x = pos_x
	prev_y = pos_y
	prev_position = position
	is_moving = moved > 0.05
	if attack_lock_timer > 0:
		attack_lock_timer -= 1
		if attack_lock_timer <= 0:
			attack_facing = 0
	tick_tower_debuffs()
	if not alive:
		return
	if stun_timer > 0:
		return
	if hurt_flash_timer > 0:
		hurt_flash_timer -= 1
	if entrance_timer > 0:
		entrance_timer -= 1
		return
	if not enrage_triggered:
		if boss_class == "true" and hp <= float(max_hp) * 0.50:
			enrage_triggered = true
			is_enraged = true
			speed = speed * 1.25
			damage = int(damage * 1.25)
			attack_cooldown = maxi(18, int(attack_cooldown * 0.75))
		elif boss_class == "mini" and hp <= float(max_hp) * 0.40:
			enrage_triggered = true
			is_enraged = true
			speed = speed * 1.15
			damage = int(damage * 1.20)
			attack_cooldown = maxi(20, int(attack_cooldown * 0.80))
	if is_enraged:
		enrage_pulse += 0.08
		if anim_time % 2 == 0:
			if timer > 0:
				timer -= 1
			if ability_timer > 0:
				ability_timer -= 1
	if timer > 0:
		timer -= 1
	if ability_timer > 0:
		ability_timer -= 1
	if ability2_timer > 0:
		ability2_timer -= 1
	if ability_active_timer > 0:
		ability_active_timer -= 1
		if ability_active_timer <= 0:
			ability_active = false
	if boss_class == "true" and ability2_timer == 0:
		if hp < float(max_hp) * 0.30:
			_use_heal_ability()
	target_ref = null
	target_id = -1
	var best_dist := float(range_px + 100)
	for enemy in enemies:
		if enemy == null or not enemy.alive or enemy.team == team:
			continue
		var ex := float(enemy.position.x)
		var ey := float(enemy.position.y)
		var dist := sqrt((ex - pos_x) * (ex - pos_x) + (ey - pos_y) * (ey - pos_y))
		if dist < best_dist:
			best_dist = dist
			target_ref = enemy
			target_id = int(enemy.id)
	if target_ref != null:
		var tx := float(target_ref.position.x)
		var ty := float(target_ref.position.y)
		var dx := tx - pos_x
		var dy := ty - pos_y
		var dist := sqrt(dx * dx + dy * dy)
		if dist <= float(range_px):
			_face(dx, dy)
			if timer == 0:
				if hit_cb.is_valid():
					hit_cb.call(target_ref, damage, "physical")
				var cleave_dmg := int(damage * cleave_ratio)
				if cleave_dmg > 0:
					for near_e in enemies:
						if near_e == null or near_e == target_ref or not near_e.alive:
							continue
						var nx := float(near_e.position.x)
						var ny := float(near_e.position.y)
						var nd := sqrt((nx - pos_x) * (nx - pos_x) + (ny - pos_y) * (ny - pos_y))
						if nd <= float(cleave_radius) and hit_cb.is_valid():
							hit_cb.call(near_e, cleave_dmg, "neutral")
				timer = eff_attack_cd(attack_cooldown)
				attack_facing = direction
				basic_attack_seq += 1
				attack_lock_timer = mini(15, maxi(6, int(attack_cooldown / 3.0)))
			if boss_type not in SMART_AI_BOSSES and ability_timer == 0:
				_use_ability(enemies, hit_cb)
		else:
			var sp := float(speed)
			if boss_type in RANGED_KITE_BOSSES:
				var band := 12.0
				if dist > 0.0:
					if dist < float(min_distance):
						kite_mode = "back"
					elif dist > float(prefer_distance):
						kite_mode = "in"
					elif kite_mode == "back" and dist < float(min_distance) + band:
						pass
					elif kite_mode == "in" and dist > float(prefer_distance) - band:
						pass
					else:
						kite_mode = "hold"
				if dist > 0.0 and sp > 0.0 and kite_mode == "back":
					var step_back := minf(sp, maxf(0.0, (float(min_distance) + band) - dist))
					if step_back > 0.0:
						set_pos(pos_x - step_back * dx / dist, pos_y - step_back * dy / dist)
						_face(-dx, -dy)
				elif dist > 0.0 and sp > 0.0 and kite_mode == "in":
					var step_in := minf(sp, maxf(0.0, dist - (float(prefer_distance) - band)))
					if step_in > 0.0:
						set_pos(pos_x + step_in * dx / dist, pos_y + step_in * dy / dist)
						_face(dx, dy)
			else:
				if dist > 0.0 and sp > 0.0:
					var step_chase := minf(sp, dist)
					set_pos(pos_x + step_chase * dx / dist, pos_y + step_chase * dy / dist)
					_face(dx, dy)
	else:
		_move_forward()
