# DamageSchool.gd — Port dari _entity.py resolve_damage_school + armor/magic_resist
extends RefCounted
class_name DamageSchool

# Di pygame: _is_physical_hit + resolve_damage_school
# Di Godot: static helpers dipakai CombatSystem

static func resolve(school: String, dmg_type: String, source) -> String:
	if school in ["physical","magic"]:
		return school
	if dmg_type in ["fire","ice","heal","crit"]:
		return ""
	if source and "dmg_school" in source:
		var s = source.dmg_school
		if s in ["physical","magic"]:
			return s
	return ""

static func is_physical_hit(dmg_type: String, school: String) -> bool:
	if dmg_type not in ["normal","projectile"]:
		return false
	return school != "magic"

static func mitigate(amount: float, armor: float, magic_resist: float, school: String) -> float:
	if school == "physical" and armor != 0:
		if armor > 0:
			var red = armor * 0.06 / (1.0 + armor * 0.06)
			return max(1.0, round(amount * (1.0 - red)))
		else:
			var bonus = min(1.0, -armor * 0.06)
			return round(amount * (1.0 + bonus))
	elif school == "magic" and magic_resist > 0:
		return max(1.0, round(amount * (1.0 - magic_resist)))
	return amount
