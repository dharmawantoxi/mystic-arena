class_name KaizenSkillQ
extends SkillBase
## Kaizen's Q — Steel Wind → Dash Strike (alternating combo).
##
## The first press fires a wide AOE slash in front of the character. The
## second press within the combo window dashes through the target and slashes
## everything in a 80 px radius along the path.
##
## The combo resets if the player does not press Q again within
## [member combo_window] seconds.

## Range of the Q1 AOE (in front of the hero).
@export var q1_range: float = 90.0
## Range of the Q2 AOE (centered on the hero, post-dash).
@export var q2_radius: float = 80.0
## Distance the dash covers in pixels.
@export var q2_dash_distance: float = 200.0
## Speed of the dash in px/s.
@export var q2_dash_speed: float = 1200.0
## Multiplier on the character's damage for Q1.
@export var q1_damage_mult: float = 1.0
## Multiplier for Q2.
@export var q2_damage_mult: float = 1.5
## Window during which the second press counts as Q2.
@export var combo_window: float = 3.0
## Stun duration applied to enemies hit by Q2.
@export var q2_stun: float = 0.5

## 0 = next press is Q1; 1 = next press is Q2.
var _stack: int = 0
## Countdown until the combo resets to Q1.
var _combo_timer: float = 0.0

## Cached target direction captured when Q2 fires. Used by the dash tween.
var _dash_target: Node = null


func tick(delta: float) -> void:
	super.tick(delta)
	if _combo_timer > 0.0:
		_combo_timer = max(0.0, _combo_timer - delta)
		if _combo_timer <= 0.0:
			_stack = 0


func try_cast(cast_pos: Vector2 = Vector2.ZERO) -> bool:
	if cooldown_remaining > 0.0:
		return false
	if is_casting or is_active:
		return false
	# Q1 has no target requirement (auto-aim), Q2 needs a target.
	if _stack == 1 and (owner_character == null or owner_character.target == null):
		# No target — fall back to Q1, do not consume the combo.
		_stack = 0
	# Acquire a target if the character doesn't have one (for Q2).
	if _stack == 1 and owner_character != null and owner_character.target == null:
		owner_character.target = _find_nearest_enemy()
	if _stack == 1 and (owner_character == null or owner_character.target == null):
		# Still no target — abort, don't burn cooldown.
		return false
	# Cool — fire.
	_combo_timer = combo_window
	if _stack == 0:
		_cast_q1()
		_stack = 1
	else:
		_cast_q2()
		_stack = 0
		_combo_timer = 0.0
	# Both variants set a short active window during which animation plays.
	# Cooldown is the same.
	cooldown_remaining = cooldown_max
	cooldown_set.emit(self, cooldown_max)
	return true


func _cast_q1() -> void:
	# Q1 = Steel Wind: damage in a forward arc of q1_range, mult 1.0.
	# We use a short cast window so the sword anim plays before the hit lands.
	cast_timer = 0.18
	is_casting = true
	cast_started.emit(self)
	# Hit at the END of the cast window — scheduled by the timer.
	var t := get_tree().create_timer(cast_timer, false, false)
	t.timeout.connect(_q1_impact)


func _cast_q2() -> void:
	# Q2 = Dash Strike: dash to target + 80-radius AOE on impact.
	# Lock the character during the dash.
	cast_timer = 0.22
	is_casting = true
	cast_started.emit(self)
	owner_character.stunned = true
	var t := get_tree().create_timer(cast_timer, false, false)
	t.timeout.connect(_q2_dash_and_slash)


func _q1_impact() -> void:
	is_casting = false
	# Forward direction in world space.
	var dir := Vector2(owner_character.facing, 0)
	# Damage all enemies in front of the character within range.
	var origin := owner_character.global_position
	var dmg := int(owner_character.damage * q1_damage_mult)
	_apply_arc_damage(origin, dir, q1_range, _deg_to_rad(120.0), dmg)
	# Visual.
	VFXManager.spawn(&"kaizen_q1_slash", origin, dir.angle(), 0.4)
	GameFeel.shake(0)


func _q2_dash_and_slash() -> void:
	is_casting = false
	if owner_character == null:
		return
	# Resolve target. If it's gone, cancel.
	var tgt := owner_character.target
	if tgt == null or not is_instance_valid(tgt):
		owner_character.stunned = false
		return
	# Dash: tween position from current to (current + dir * dist), clamped
	# to the target's position if it's closer than q2_dash_distance.
	var from_pos := owner_character.global_position
	var to_target := tgt.global_position
	var raw_dir := to_target - from_pos
	var dist_to_target := raw_dir.length()
	var actual_dist: float = min(q2_dash_distance, dist_to_target)
	var dir := raw_dir.normalized() if dist_to_target > 0.001 else Vector2(owner_character.facing, 0)
	var dash_end := from_pos + dir * actual_dist
	# We use a manual kinematic dash via tween so collision doesn't fight us.
	var tween := owner_character.create_tween()
	tween.set_trans(Tween.TRANS_QUART)
	tween.set_ease(Tween.EASE_OUT)
	tween.tween_property(owner_character, "global_position", dash_end, actual_dist / q2_dash_speed)
	tween.finished.connect(_q2_impact.bind(dash_end, dir))


func _q2_impact(dash_end: Vector2, dir: Vector2) -> void:
	owner_character.stunned = false
	# Damage everything in q2_radius around the dash end.
	var dmg := int(owner_character.damage * q2_damage_mult)
	_apply_circle_damage(dash_end, q2_radius, dmg, q2_stun)
	# Visual.
	VFXManager.spawn(&"kaizen_q2_slash", dash_end, dir.angle(), 0.4)
	GameFeel.shake(2)
	GameFeel.hit_stop(0.05)


# ---------------------------------------------------------------------------
# Damage helpers
# ---------------------------------------------------------------------------

func _apply_arc_damage(origin: Vector2, dir: Vector2, range: float, half_arc: float, amount: int) -> int:
	var enemies := _enemies_in_range(origin, range)
	var total := 0
	for e in enemies:
		var to_e: Vector2 = e.global_position - origin
		var d := to_e.length()
		if d < 0.001:
			continue
		var n := to_e / d
		var cos_a := n.dot(dir)
		if cos_a >= cos(half_arc):
			var actual := owner_character.deal_damage(e, amount)
			total += actual
			ParticlePool.spawn(e.global_position, actual, false, "skill")
	return total


func _apply_circle_damage(origin: Vector2, radius: float, amount: int, stun: float = 0.0) -> int:
	var enemies := _enemies_in_range(origin, radius)
	var total := 0
	for e in enemies:
		var actual := owner_character.deal_damage(e, amount)
		total += actual
		ParticlePool.spawn(e.global_position, actual, false, "skill")
		if stun > 0.0 and e.has_method("apply_stun"):
			e.call("apply_stun", stun)
	return total


func _enemies_in_range(origin: Vector2, range: float) -> Array:
	var tree := get_tree()
	var result: Array = []
	for c in tree.get_nodes_in_group("enemies"):
		if c is Node2D and is_instance_valid(c):
			var d := (c as Node2D).global_position.distance_to(origin)
			if d <= range:
				result.append(c)
	return result


func _find_nearest_enemy() -> Node:
	if owner_character == null:
		return null
	var best: Node = null
	var best_d := INF
	for c in get_tree().get_nodes_in_group("enemies"):
		if c is Node2D and is_instance_valid(c):
			var d := (c as Node2D).global_position.distance_to(owner_character.global_position)
			if d < best_d:
				best_d = d
				best = c
	return best


func _deg_to_rad(deg: float) -> float:
	return deg * PI / 180.0
