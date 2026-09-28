extends "res://scripts/match/item_effects.gd"
## Concrete bus bound to a prototype_battle world. Methods translate item
## effect calls into real _deliver_hit / debuff field mutations.

const HeroState = preload("res://scripts/combat/hero_state.gd")
var world: Object = null
var dealer_id: int = -1
var dealer_team: int = -1
var dealer_pos: Vector2 = Vector2.ZERO


func deal_damage(target_id: int, _source_team: int, amount: int, school: String = "magic") -> int:
	var tgt: Object = world.get_unit(target_id)
	if tgt == null:
		return 0
	world._deliver_hit(dealer_id, dealer_team, tgt, amount, school, dealer_pos)
	return amount


func apply_stun(target_id: int, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t is HeroState:
		(t as HeroState).stun_timer = maxi((t as HeroState).stun_timer, duration)


func apply_silence(target_id: int, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	# UnitState already carries atk_slow/skill_down fields.
	t.atk_slow_amount = 1.0
	t.atk_slow_timer = maxi(t.atk_slow_timer, duration)
	t.skill_down_amount = 1.0
	t.skill_down_timer = maxi(t.skill_down_timer, duration)


func apply_slow(target_id: int, amount: float, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	t.slow_amount = maxf(t.slow_amount, amount)
	t.slow_timer = maxi(t.slow_timer, duration)


func apply_burn(target_id: int, dps: float, duration: int, source_team: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	t.burn_dps = maxf(t.burn_dps, dps)
	t.burn_timer = maxi(t.burn_timer, duration)
	t.burn_team = source_team


func nudge_position(hid: int, delta: Vector2) -> void:
	var t: Object = world.get_unit(hid)
	if t != null:
		t.position += delta
