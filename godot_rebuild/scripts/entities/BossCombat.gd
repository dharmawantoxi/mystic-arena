class_name BossCombat
extends RefCounted

## Exact bosses/base_boss.py take_damage order: blind -> amp/shred -> school ->
## resilience -> per-hit cap -> floor 1. Unlike the generic unit path, the source
## boss method does not reject same-team burn or clamp before mitigation.


static func resolve_school(damage_type: String, source: BattleUnit, school: String) -> String:
	if school in ["physical", "magic"]:
		return school
	if damage_type in ["fire", "ice", "heal", "crit"]:
		return ""
	if source != null and source.dmg_school in ["physical", "magic"]:
		return source.dmg_school
	return ""


static func take_damage(
	unit: BattleUnit,
	amount: float,
	_from_team: String,
	damage_type: String,
	source: BattleUnit,
	school: String
) -> float:
	var damage := amount
	if damage_type == "normal" and damage > 0.0 and source != null:
		var true_strike := source.items != null and source.items.has_true_strike()
		if not true_strike and source.status.blind_timer > 0:
			var roll := unit.blind_roll_override
			if roll < 0.0:
				roll = unit.world.rng.randf() if unit.world != null else randf()
			if roll < source.status.blind_amount:
				return 0.0
	if damage > 0.0:
		if unit.status.dmg_amp_timer > 0:
			damage = float(HeroBalance.py_round(damage * (1.0 + unit.status.dmg_amp_amount)))
		var shred := unit.status.armor_shred_amount
		if damage_type != "fire" and shred > 0.0:
			damage = float(HeroBalance.py_round(damage * (1.0 + minf(1.0, shred * 0.06))))
	var resolved := resolve_school(damage_type, source, school)
	if damage > 0.0 and resolved == "physical" and unit.armor > 0.0:
		var reduction := unit.armor * 0.06 / (1.0 + unit.armor * 0.06)
		reduction = minf(0.60, maxf(0.0, reduction - unit.status.armor_shred_amount * 0.06))
		damage = maxf(1.0, float(HeroBalance.py_round(damage * (1.0 - reduction))))
	elif damage > 0.0 and resolved == "magic" and unit.magic_resist > 0.0:
		damage = maxf(1.0, float(HeroBalance.py_round(damage * (1.0 - unit.magic_resist))))
	var resilience := unit.damage_reduction
	if unit.defense_boost:
		resilience = maxf(resilience, 0.45)
	var effective := int(damage * (1.0 - resilience))
	effective = mini(effective, unit.max_damage_per_hit)
	effective = maxi(1, effective)
	unit.hp = unit.hp - effective
	unit.hurt_flash_timer = 8
	if source != null:
		source.damage_dealt += effective
	if unit.world != null:
		unit.world.add_damage_number(
			unit.pos + Vector2(0, -unit.radius - 10),
			effective,
			effective > unit.max_hp * 0.03,
			damage_type
		)
		unit.world.add_effect(unit.pos, "hit", unit.color, 6)
	if unit.hp <= 0.0:
		unit.hp = 0.0
		unit.alive = false
		unit.defeated = true
		unit.killed_by = source
		unit.status.clear()
		if unit.world != null:
			unit.world.add_effect(unit.pos, "death", unit.color, 48)
			unit.world.add_shake(28.0 if unit.boss_class == "true" else 20.0)
	return float(effective)
