# gdlint:disable=max-public-methods
extends "res://scripts/combat/unit_state.gd"
## Layer 8a/8c/8e: source Boss entity core, lane combat and entrance/enrage clocks.
##
## Ports the scalar identity/stats of `Boss.__init__`, `apply_scaling`, the
## tenacity slow/atk_slow rule, the `TowerDebuffMixin` stun cut and the numeric
## tail of `take_damage` (item amp/shred, school mitigation, inherent
## resilience, anti-burst cap, defeat flag). Boss stats come from
## `data/bosses/boss_stats.json`, rendered from the source tables by
## `tests/boss_core_source_oracle.py`.
##
## Not ported here (next layer): intro/defeat presentation and the remaining
## match UI wiring.

const MinionDefinition = preload("res://scripts/data/minion_definition.gd")
const Damage = preload("res://scripts/combat/damage_rules.gd")
const LaneLayout = preload("res://scripts/data/lane_layout.gd")

var boss_type := ""
var display_name := ""
var title := ""
var boss_class := "mini"
var rules: Dictionary = {}

var max_hp := 0
var damage := 0
var base_damage := 0
var speed_px_per_tick := 0.0
var base_speed := 0.0
var attack_range := 0.0
var attack_cooldown := 0
var radius := 0.0
var gold_reward := 0
var armor := 0
var magic_resist := 0.0
var resist_profile := "balanced"
var damage_reduction := 0.0
var max_damage_per_hit := 0
var max_damage_per_hit_pct := 0.0
var entrance_ticks := 0
var entrance_text := ""
var ability_cooldown := 0
var ability_damage_value := 0
var ability_range := 0.0
var ability2_cooldown := 0
var ability2_heal_pct := 0.0
var skill_q_damage := 0
var skill_w_damage := 0
var skill_e_damage := 0
var skill_r_damage := 0
var skill_w_shield := 0
var skill_q_cooldown := 0
var skill_w_cooldown := 0
var skill_e_cooldown := 0
var skill_r_cooldown := 0
var color := Color.BLACK
var color_dark := Color.BLACK
var entrance_color := Color.BLACK

# Source Boss state (Boss.__init__): clocks, bookkeeping and flags.
var timer := 0
var ability_timer := 0
var ability2_timer := 0
var ability_active := false
var ability_active_timer := 0
var hurt_flash_timer := 0
var entrance_timer := 0
var anim_time := 0
var pulse := 0.0
var enrage_triggered := false
var enrage_pulse := 0.0
var defeated := false
var defense_boost := false
var stun_timer := 0
var cleave_radius := 0.0
var cleave_ratio := 0.0
var hp_scaling_mult := 1.0
var dmg_scaling_mult := 1.0
var spd_scaling_mult := 1.0
var direction := -1
var lane_path := PackedVector2Array()
# Layer 8c motion/attack state. The source renderer consumes the movement
# cache and the attack edge; presentation itself remains a later layer.
var is_moving := false
var moving_cached := false
var previous_position := Vector2.ZERO
var attack_facing := 0.0
var attack_lock_timer := 0
var basic_attack_seq := 0
var last_hit_source_id := -1
# Layer 8d source smart-ability state. These fields are gameplay state; the
# renderer may consume active_skill later, but presentation is not here.
var q_timer := 0
var w_timer := 0
var e_timer := 0
var r_timer := 0
var active_skill := ""
var active_skill_timer := 0
var rage_active := false
var rage_timer := 0
var is_enraged := false
var defense_timer := 0
var flux_target_id := -1
var flux_active_timer := 0
var clones_active_timer := 0
var clones_positions: Array[Vector2] = []
var blink_from := Vector2.ZERO
var blink_to := Vector2.ZERO
var mana_void_origin := Vector2.ZERO
# Source Boss.speed property reads `tenacity` (0.50 for every boss).
var tenacity := 0.50
# Injectable draw so tests can replay the recorded source roll.
var blind_roll_override: Callable
var rng := RandomNumberGenerator.new()


func setup(boss_type_value: String, lane_path: PackedVector2Array, table: Dictionary) -> bool:
	var rows: Dictionary = table.get("bosses", {})
	var stats: Dictionary = rows.get(boss_type_value, {})
	if stats.is_empty():
		return false
	boss_type = boss_type_value
	rules = table.get("rules", {})
	boss_class = String(stats["boss_class"])
	display_name = String(stats["name"])
	title = String(stats["title"])
	max_hp = int(stats["max_hp"])
	hp = float(max_hp)
	damage = int(stats["damage"])
	base_damage = damage
	speed_px_per_tick = float(stats["speed"])
	base_speed = speed_px_per_tick
	attack_range = float(stats["attack_range"])
	attack_cooldown = int(stats["attack_cooldown"])
	radius = float(stats["radius"])
	gold_reward = int(stats["gold_reward"])
	ability_cooldown = int(stats["ability_cooldown"])
	ability_damage_value = int(stats["ability_damage"])
	ability_range = float(stats["ability_range"])
	ability2_cooldown = int(stats["ability2_cooldown"])
	ability2_heal_pct = float(stats["ability2_heal_pct"])
	skill_q_damage = int(stats.get("skill_q_damage", 0))
	skill_w_damage = int(stats.get("skill_w_damage", 0))
	skill_e_damage = int(stats.get("skill_e_damage", 0))
	skill_r_damage = int(stats.get("skill_r_damage", 0))
	skill_w_shield = int(stats.get("skill_w_shield", 0))
	skill_q_cooldown = int(stats.get("skill_q_cooldown", 0))
	skill_w_cooldown = int(stats.get("skill_w_cooldown", 0))
	skill_e_cooldown = int(stats.get("skill_e_cooldown", 0))
	skill_r_cooldown = int(stats.get("skill_r_cooldown", 0))
	armor = int(stats["armor"])
	magic_resist = float(stats["magic_resist"])
	resist_profile = String(stats["resist_profile"])
	damage_reduction = float(stats["damage_reduction"])
	var cap_pct: Dictionary = rules.get("max_damage_per_hit_pct", {})
	max_damage_per_hit_pct = float(cap_pct.get(boss_class, 0.0))
	tenacity = float(rules.get("tenacity", 0.50))
	cleave_radius = float(rules.get("cleave_radius", 0))
	cleave_ratio = float(rules.get("cleave_ratio", 0))
	max_damage_per_hit = int(max_hp * max_damage_per_hit_pct)
	entrance_ticks = int(stats["entrance_ticks"])
	entrance_timer = entrance_ticks
	entrance_text = String(stats["entrance_text"])
	_set_colors(stats)
	team = 1  # Source Boss.__init__: team = "red".
	rebuild_definition()
	direction = -1
	facing = -1.0
	self.lane_path = lane_path.duplicate()
	# Source position: the last waypoint of the (mid) lane path, else
	# (RED_BASE_X - 50, RED_BASE_Y) = (1130, 100) with waypoint_index -1.
	if lane_path.size() > 0:
		position = lane_path[lane_path.size() - 1]
		waypoint_index = lane_path.size() - 1
	else:
		var fallback: Array = rules.get("fallback_position", [1130.0, 100.0])
		position = Vector2(float(fallback[0]), float(fallback[1]))
		waypoint_index = -1
	previous_position = position
	# Source Boss.__init__ ends with _init_tower_debuffs(), which is also what
	# clear_tower_debuffs() re-runs (burn_tick_cd starts at the burn interval).
	clear_tower_debuffs()
	return true


func _set_colors(stats: Dictionary) -> void:
	color = _color_of(stats.get("color", [0, 0, 0]))
	color_dark = _color_of(stats.get("color_dark", [0, 0, 0]))
	entrance_color = _color_of(stats.get("entrance_color", [0, 0, 0]))


static func _color_of(values: Array) -> Color:
	return Color8(int(values[0]), int(values[1]), int(values[2]))


func _definition_for() -> MinionDefinition:
	# Shared helpers (damage rules, radius, kill reward) read a Definition, so
	# the boss mirrors its scalars there. Not spawnable through spawn_unit.
	var built := MinionDefinition.new()
	built.id = boss_type
	built.display_name = display_name
	built.max_hp = max_hp
	built.damage = damage
	built.speed_px_per_tick = speed_px_per_tick
	built.attack_range_px = attack_range
	built.attack_cooldown_ticks = attack_cooldown
	built.gold_reward = gold_reward
	built.radius_px = radius
	built.armor = float(armor)
	built.magic_resist = magic_resist
	return built


func rebuild_definition() -> void:
	definition = _definition_for()


func advance_animation_clock() -> void:
	# Source Boss.update advances these renderer-facing clocks before stun and
	# entrance gating. Presentation consumes them in the following layer.
	anim_time += 1
	pulse += 0.1


func advance_combat_clock() -> bool:
	# Port of the source entrance gate and one-shot enrage/frenzy transition.
	# Return false while the boss is entering, so no movement, attack, heal or
	# smart ability is consumed on those ticks.
	if hurt_flash_timer > 0:
		hurt_flash_timer -= 1
	if entrance_timer > 0:
		entrance_timer -= 1
		return false
	if not enrage_triggered:
		if boss_class == "true" and hp <= float(max_hp) * 0.50:
			enrage_triggered = true
			is_enraged = true
			# Source writes through the speed property, so an active slow is
			# included once before the new base speed is stored.
			speed_px_per_tick = eff_speed() * 1.25
			damage = int(float(damage) * 1.25)
			attack_cooldown = maxi(18, int(float(attack_cooldown) * 0.75))
		elif boss_class == "mini" and hp <= float(max_hp) * 0.40:
			enrage_triggered = true
			is_enraged = true
			# Match the source speed property's getter/setter path under slow.
			speed_px_per_tick = eff_speed() * 1.15
			damage = int(float(damage) * 1.20)
			attack_cooldown = maxi(20, int(float(attack_cooldown) * 0.80))
		if enrage_triggered:
			rebuild_definition()
	if is_enraged:
		enrage_pulse += 0.08
		# Source enrage recovers the ordinary and generic ability clocks twice
		# on even animation ticks; the regular match tick performs the second
		# decrement after this method returns.
		if anim_time % 2 == 0:
			timer = maxi(0, timer - 1)
			ability_timer = maxi(0, ability_timer - 1)
	return true


func begin_motion_tick() -> void:
	# Source Boss.update measures real displacement before this frame's move;
	# the cached flag is what the later renderer will read for WALK/IDLE.
	var moved := position.distance_to(previous_position)
	previous_position = position
	is_moving = moved > 0.05
	moving_cached = is_moving
	if attack_lock_timer > 0:
		attack_lock_timer -= 1
		if attack_lock_timer <= 0:
			attack_facing = 0.0


func face_motion(dx: float, dy: float) -> void:
	# Port of Boss._face: an attack lock wins, and near-vertical travel does
	# not flap the horizontal sprite direction.
	if attack_lock_timer > 0:
		if absf(attack_facing) > 0.5:
			direction = int(attack_facing)
			facing = attack_facing
		return
	if absf(dx) < 0.35 * maxf(0.000001, absf(dy)):
		return
	direction = 1 if dx > 0.0 else -1
	facing = float(direction)


func lane_target() -> Vector2:
	# Port of Boss._lane_target: red starts at the last point and walks the
	# path backwards toward the blue base.
	if lane_path.size() > 0 and waypoint_index >= 0 and waypoint_index < lane_path.size():
		return lane_path[waypoint_index]
	return LaneLayout.BLUE_BASE


func advance_waypoint() -> bool:
	if lane_path.is_empty():
		return false
	waypoint_index -= 1
	return waypoint_index >= 0


func move_forward() -> void:
	# Port of the source budgeted waypoint walk: leftover speed crosses more
	# than one waypoint in a single tick, with no artificial stall frame.
	var budget := eff_speed()
	if budget <= 0.0:
		return
	var guard := 0
	while budget > 0.001 and guard < 16:
		guard += 1
		var target := lane_target()
		var offset := target - position
		var distance := offset.length()
		var has_next := not lane_path.is_empty() and waypoint_index >= 0
		if distance <= 0.000001:
			if not has_next:
				break
			advance_waypoint()
			continue
		if distance <= budget:
			position = target
			budget -= distance
			face_motion(offset.x, offset.y)
			if has_next:
				advance_waypoint()
			continue
		position += offset / distance * budget
		face_motion(offset.x, offset.y)
		budget = 0.0


func move_toward(target: Vector2) -> void:
	# Source chase branch clamps speed to the remaining distance.
	var offset := target - position
	var distance := offset.length()
	var speed := eff_speed()
	if distance <= 0.0 or speed <= 0.0:
		return
	var step := minf(speed, distance)
	position += offset / distance * step
	face_motion(offset.x, offset.y)


func effective_attack_cooldown() -> int:
	# Port of TowerDebuffMixin._eff_attack_cd used by Boss.update.
	if stun_timer > 0:
		return 9999
	if atk_slow_timer <= 0:
		return attack_cooldown
	var factor := maxf(0.05, 1.0 - atk_slow_amount)
	return maxi(1, Damage.rounded_like_python(float(attack_cooldown) / factor))


func eff_speed() -> float:
	# Port of Boss.speed: every movement point slows while slow_timer runs.
	var value := speed_px_per_tick
	if slow_timer > 0:
		value = value * (1.0 - slow_amount)
	return value


func eff_ability_damage() -> int:
	# Port of Boss.ability_damage: skill_down (Mage tower) cuts the value.
	if skill_down_timer > 0:
		var factor := maxf(0.0, 1.0 - skill_down_amount)
		return Damage.rounded_like_python(float(ability_damage_value) * factor)
	return ability_damage_value


func apply_scaling(hp_mult: float = 1.0, dmg_mult: float = 1.0, spd_mult: float = 1.0) -> void:
	# Port of Boss.apply_scaling (hard-mode difficulty).
	hp_scaling_mult = hp_mult
	dmg_scaling_mult = dmg_mult
	spd_scaling_mult = spd_mult
	max_hp = int(max_hp * hp_mult)
	hp = float(max_hp)
	damage = int(damage * dmg_mult)
	base_damage = damage
	ability_damage_value = int(ability_damage_value * dmg_mult)
	speed_px_per_tick = speed_px_per_tick * spd_mult
	base_speed = speed_px_per_tick
	max_damage_per_hit = int(max_hp * max_damage_per_hit_pct)
	rebuild_definition()


func apply_slow(amount: float, duration: int) -> void:
	# Port of Boss.apply_slow: tenacity halves magnitude and duration, and the
	# magnitude is capped at 0.35.
	if not alive:
		return
	var reduced_amount := minf(0.35, amount * (1.0 - tenacity))
	var reduced_duration := int(float(duration) * (1.0 - tenacity))
	if reduced_amount > slow_amount or slow_timer < reduced_duration:
		slow_amount = reduced_amount
		slow_timer = reduced_duration


func apply_debuff(kind: String, amount: float, duration: int, source_team: int = -1) -> void:
	# Port of Boss.apply_debuff: tenacity only cuts atk_slow, then the
	# TowerDebuffMixin store rules apply.
	if not alive:
		return
	if kind == "slow":
		apply_slow(amount, duration)
		return
	var stored_amount := amount
	var stored_duration := duration
	if kind == "atk_slow":
		stored_amount = minf(0.35, amount * (1.0 - tenacity))
		stored_duration = int(float(duration) * (1.0 - tenacity))
	store_debuff(kind, stored_amount, stored_duration, source_team)


func store_debuff(kind: String, amount: float, duration: int, source_team: int = -1) -> void:
	# Port of the TowerDebuffMixin.apply_debuff store: strongest wins, a longer
	# duration refreshes both fields.
	match kind:
		"atk_slow":
			if amount > atk_slow_amount or atk_slow_timer < duration:
				atk_slow_amount = amount
				atk_slow_timer = duration
		"skill_down":
			if amount > skill_down_amount or skill_down_timer < duration:
				skill_down_amount = amount
				skill_down_timer = duration
		"anti_heal":
			if amount > anti_heal_amount or anti_heal_timer < duration:
				anti_heal_amount = amount
				anti_heal_timer = duration
		"burn":
			if burn_timer <= 0:
				burn_dps = amount
				burn_accum = 0.0
				burn_tick_cd = int(rules.get("burn_tick", 30))
			else:
				burn_dps = maxf(burn_dps, amount)
			burn_timer = maxi(burn_timer, duration)
			if source_team >= 0:
				burn_team = source_team


func apply_stun(duration: int) -> void:
	# Port of TowerDebuffMixin.apply_stun (Boss does not override it): a boss
	# resists 55% of the stun duration so it cannot be stun-locked.
	if not alive:
		return
	var reduced := int(float(duration) * 0.45)
	if reduced <= 0:
		return
	if reduced > stun_timer:
		stun_timer = reduced


func clear_tower_debuffs() -> void:
	# Port of TowerDebuffMixin.clear_tower_debuffs -> _init_tower_debuffs.
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
	burn_tick_cd = int(rules.get("burn_tick", 30))
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


func blind_roll() -> float:
	if blind_roll_override.is_valid():
		return float(blind_roll_override.call())
	return rng.randf()


func true_strike_of(source: Object) -> bool:
	# Source reads `source.items.has_true_strike()` inside a try/except.
	if source == null:
		return false
	var inventory: Variant = source.get("items")
	if inventory == null:
		return false
	var holder: Object = inventory
	if holder == null or not holder.has_method("has_true_strike"):
		return false
	return bool(holder.call("has_true_strike"))


func blind_live(source: Object, damage_type: String) -> bool:
	# Port of the blind block at the top of Boss.take_damage: only plain
	# ("normal") hits from a live attacker whose blind (Solar Brand) is running
	# can miss, and an itemized true strike pierces the blind.
	if damage_type != "normal":
		return false
	if source == null:
		return false
	var blind_timer: int = int(source.get("blind_timer"))
	if blind_timer <= 0:
		return false
	return not true_strike_of(source)


func take_damage(
	source: Object, raw_damage: int, damage_type: String = "normal", school: String = "neutral"
) -> int:
	# Port of the numeric tail of Boss.take_damage. Returns the damage applied,
	# or -1 when the source would return before touching hp (blind miss).
	# Presentation hooks (damage numbers, particles, shake, death FX) and the
	# kill attribution helper are out of scope for this layer.
	if source != null and raw_damage > 0 and blind_live(source, damage_type):
		if blind_roll() < float(source.get("blind_amount")):
			return -1
	var damage := raw_damage
	if damage > 0:
		if dmg_amp_timer > 0:
			damage = Damage.rounded_like_python(float(damage) * (1.0 + dmg_amp_amount))
		if damage_type != "fire" and armor_shred_amount > 0.0:
			damage = Damage.rounded_like_python(
				float(damage) * (1.0 + minf(1.0, armor_shred_amount * 0.06))
			)
	if damage > 0 and school == "physical" and armor > 0:
		var reduction := float(armor) * 0.06 / (1.0 + float(armor) * 0.06)
		reduction = minf(0.60, maxf(0.0, reduction - armor_shred_amount * 0.06))
		damage = maxi(1, Damage.rounded_like_python(float(damage) * (1.0 - reduction)))
	elif damage > 0 and school == "magic" and magic_resist > 0.0:
		damage = maxi(1, Damage.rounded_like_python(float(damage) * (1.0 - magic_resist)))
	var resilience := damage_reduction
	if defense_boost:
		resilience = maxf(resilience, 0.45)
	var effective := int(float(damage) * (1.0 - resilience))
	if effective > max_damage_per_hit:
		effective = max_damage_per_hit
	effective = maxi(1, effective)
	hp = maxf(0.0, hp - float(effective))
	hurt_flash_timer = 8
	if hp <= 0.0:
		hp = 0.0
		alive = false
		defeated = true
		clear_tower_debuffs()
	return effective
