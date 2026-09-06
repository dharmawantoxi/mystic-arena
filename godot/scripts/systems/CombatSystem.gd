# CombatSystem.gd — Autoload, port dari _entity.py damage pipeline
# Terpusat, dipakai Hero/Boss/Tower/Minion take_damage
extends Node

func calc_damage(attacker: Node, defender: Node, base: float, school: String) -> float:
	var dmg = base
	# Item crit (Dead Edge) — port dari hero_items.HeroItemInventory.roll_crit
	if attacker.has_method("get_crit_mult"):
		var m = attacker.get_crit_mult()
		if m > 1.0 and randf() < attacker.get_crit_chance():
			dmg *= m
	# Soul Rend, etc.
	return dmg

func mitigate_damage(defender: Node, amount: float, school: String) -> float:
	var armor = 0.0
	var mr = 0.0
	if "armor" in defender:
		armor = defender.armor
	if "magic_resist" in defender:
		mr = defender.magic_resist
	# Item armor (Steel Aegis) + shred (Corroder)
	if defender.has_method("get_effective_armor"):
		armor = defender.get_effective_armor()
	return DamageSchool.mitigate(amount, armor, mr, school)
