class_name EntityCombat
extends RefCounted

## Damage-school resolution and defensive layers from _entity.py / base_boss.py.


static func resolve_school(
	target: BattleUnit, damage_type: String, source: BattleUnit, school: String
) -> String:
	if not school.is_empty():
		return school
	if damage_type in ["fire", "ice", "heal", "crit", "true"]:
		return ""
	if source != null and source.kind == BattleUnit.Kind.HERO:
		return source.dmg_school
	if damage_type == "magic":
		return "magic"
	if damage_type in ["physical", "projectile"]:
		return "physical"
	if damage_type == "normal" and target.kind == BattleUnit.Kind.HERO and source == null:
		return "physical"
	return ""


static func armor_reduction(armor_value: float) -> float:
	if armor_value <= 0.0:
		return 0.0
	return minf(0.60, armor_value * 0.06 / (1.0 + armor_value * 0.06))


static func hero_pre_damage(
	unit: BattleUnit, amount: float, school: String, source: BattleUnit, rng: RandomNumberGenerator
) -> Dictionary:
	var result := {"amount": amount, "miss": false, "reflect": 0.0, "reflect_source": source}
	var kit := unit.kit
	if bool(kit.get("shadow_realm_active", false)) or bool(kit.get("veil_active", false)):
		result.miss = true
		return result
	if unit.items != null and unit.items.has("tempest_vane") and unit.item_timer("veil") > 0:
		result.miss = true
		return result
	var physical := school == "physical"
	if physical and bool(kit.get("windrun_active", false)) and rng.randf() < 0.75:
		result.miss = true
		return result
	if physical and bool(kit.get("wind_wall_active", false)):
		result.miss = true
		result.reflect = amount
		return result
	var evasion := float(kit.get("evasion", 0.0))
	if unit.items != null:
		evasion += unit.items.sum_stat("evasion")
	var blind := 0.0
	if source != null:
		blind = source.status.blind_amount if source.status.blind_timer > 0 else 0.0
	var true_strike := source != null and bool(source.kit.get("true_strike_active", false))
	if physical and not true_strike and rng.randf() < clampf(evasion + blind, 0.0, 0.9):
		result.miss = true
		return result
	var block := 0.0
	if unit.items != null:
		block = unit.items.block_amount(source)
	if bool(kit.get("bristleback_active", false)):
		var reduction := 0.70 if physical else 0.85
		result.amount = amount * (1.0 - reduction)
		if source == null:
			result.reflect = amount * 0.25
		return result
	if block > 0.0:
		result.amount = maxf(0.0, amount - block)
	return result


static func boss_pre_damage(
	unit: BattleUnit, amount: float, school: String, source: BattleUnit
) -> float:
	var effective := amount
	if source != null and source.status.blind_timer > 0 and school == "physical":
		return 0.0
	if unit.status.dmg_amp_timer > 0:
		effective *= 1.0 + unit.status.dmg_amp_amount
	if school == "physical" and unit.armor > 0.0:
		# base_boss.py: compute raw armor reduction, subtract Corroder shred,
		# then clamp. Do not multiplicatively shrink armor like the hero path.
		var reduction := 1.0 - HeroArchetypes.physical_mitigation(unit.armor)
		reduction -= unit.status.armor_shred_amount * HeroArchetypes.ARMOR_FACTOR
		effective *= 1.0 - clampf(reduction, 0.0, 0.60)
	elif school == "magic" and unit.magic_resist > 0.0:
		effective *= 1.0 - minf(HeroArchetypes.MR_MAX, unit.magic_resist)
	var resilience := unit.damage_reduction
	if unit.defense_boost:
		resilience = maxf(resilience, 0.45)
	effective *= 1.0 - resilience
	if unit.max_damage_per_hit > 0:
		effective = minf(effective, float(unit.max_damage_per_hit))
	return maxf(0.0, effective)
