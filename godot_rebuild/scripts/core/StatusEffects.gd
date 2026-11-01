class_name StatusEffects
extends RefCounted

## Port of TowerDebuffMixin: strongest effect wins, duration refreshes.
const BURN_TICK := 30
const FPS := 60.0
var slow_amount := 0.0
var slow_timer := 0
var atk_slow_amount := 0.0
var atk_slow_timer := 0
var skill_down_amount := 0.0
var skill_down_timer := 0
var anti_heal_amount := 0.0
var anti_heal_timer := 0
var burn_dps := 0.0
var burn_timer := 0
var burn_accum := 0.0
var burn_tick_cd := BURN_TICK
var burn_team := ""
var stun_timer := 0
var silence_timer := 0
var armor_shred_amount := 0.0
var armor_shred_timer := 0
var dmg_amp_amount := 0.0
var dmg_amp_timer := 0
var heal_amp_amount := 0.0
var heal_amp_timer := 0
var blind_amount := 0.0
var blind_timer := 0


func apply(kind: String, amount: float, duration: int, source_team := "") -> void:
	match kind:
		"slow":
			if amount > slow_amount or slow_timer < duration:
				slow_amount = amount
				slow_timer = duration
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
				burn_tick_cd = BURN_TICK
			else:
				burn_dps = maxf(burn_dps, amount)
			burn_timer = maxi(burn_timer, duration)
			if not source_team.is_empty():
				burn_team = source_team
		"stun":
			stun_timer = maxi(stun_timer, duration)
		"silence":
			silence_timer = maxi(silence_timer, duration)
		"armor_shred":
			if amount > armor_shred_amount or armor_shred_timer < duration:
				armor_shred_amount = amount
				armor_shred_timer = duration
		"dmg_amp":
			if amount > dmg_amp_amount or dmg_amp_timer < duration:
				dmg_amp_amount = amount
				dmg_amp_timer = duration
		"heal_amp":
			if amount > heal_amp_amount or heal_amp_timer < duration:
				heal_amp_amount = amount
				heal_amp_timer = duration
		"blind":
			if amount > blind_amount or blind_timer < duration:
				blind_amount = amount
				blind_timer = duration


func modified_heal(old_hp: float, new_hp: float) -> float:
	if new_hp <= old_hp:
		return new_hp
	var value := new_hp
	if anti_heal_timer > 0:
		value = old_hp + (value - old_hp) * (1.0 - anti_heal_amount)
	if heal_amp_timer > 0:
		value = old_hp + (value - old_hp) * (1.0 + heal_amp_amount)
	return value


func effective_speed(base: float, move_bonus := 0.0) -> float:
	if stun_timer > 0:
		return 0.0
	var speed := base * (1.0 + move_bonus)
	if slow_timer > 0:
		speed *= 1.0 - slow_amount
	return speed


func effective_attack_cd(base_cd: int) -> int:
	if stun_timer > 0:
		return 9999
	if atk_slow_timer > 0:
		return maxi(1, int(round(base_cd / maxf(0.05, 1.0 - atk_slow_amount))))
	return base_cd


func tick() -> int:
	var burn_damage := 0
	slow_timer = maxi(0, slow_timer - 1)
	if slow_timer == 0:
		slow_amount = 0.0
	atk_slow_timer = maxi(0, atk_slow_timer - 1)
	if atk_slow_timer == 0:
		atk_slow_amount = 0.0
	skill_down_timer = maxi(0, skill_down_timer - 1)
	if skill_down_timer == 0:
		skill_down_amount = 0.0
	anti_heal_timer = maxi(0, anti_heal_timer - 1)
	if anti_heal_timer == 0:
		anti_heal_amount = 0.0
	stun_timer = maxi(0, stun_timer - 1)
	silence_timer = maxi(0, silence_timer - 1)
	armor_shred_timer = maxi(0, armor_shred_timer - 1)
	if armor_shred_timer == 0:
		armor_shred_amount = 0.0
	dmg_amp_timer = maxi(0, dmg_amp_timer - 1)
	if dmg_amp_timer == 0:
		dmg_amp_amount = 0.0
	heal_amp_timer = maxi(0, heal_amp_timer - 1)
	if heal_amp_timer == 0:
		heal_amp_amount = 0.0
	blind_timer = maxi(0, blind_timer - 1)
	if blind_timer == 0:
		blind_amount = 0.0
	if burn_timer > 0:
		burn_timer -= 1
		burn_accum += burn_dps / FPS
		burn_tick_cd -= 1
		if burn_tick_cd <= 0:
			burn_tick_cd = BURN_TICK
			burn_damage = int(burn_accum)
			burn_accum -= burn_damage
		if burn_timer <= 0:
			burn_dps = 0.0
			burn_accum = 0.0
	return burn_damage


func clear() -> void:
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
	burn_tick_cd = BURN_TICK
	burn_team = ""
	stun_timer = 0
	armor_shred_amount = 0.0
	armor_shred_timer = 0
	dmg_amp_amount = 0.0
	dmg_amp_timer = 0
	heal_amp_amount = 0.0
	heal_amp_timer = 0
	blind_amount = 0.0
	blind_timer = 0
