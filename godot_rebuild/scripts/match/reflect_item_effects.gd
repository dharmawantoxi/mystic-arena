extends "res://scripts/match/item_effects.gd"
## Bus for Thornmail reflect: damage is dealt with source_id=-1 (no credit
## loop, matching the source Bristleback reflect precedent).

var world: Object = null
var defender_team: int = 0


func deal_damage(target_id: int, src_team: int, amount: int, _school: String = "magic") -> int:
	var attacker: Object = world.get_unit(target_id)
	if attacker == null:
		return 0
	# Layers 9i/9s: the Razor Carapace reflect calls
	# `source.take_damage(dmg, self.hero.team, "magic")` (`hero_items.py:2468`)
	# - three positional arguments, so the attacker runs with
	# `damage_type="magic"`, `source=None` and `school=None`. Layer 9i routed
	# the boss attacker that way (blind gate and kill credit already matched the
	# source, but `school="magic"` cut the payload by boss magic resist while
	# the source resolves no school at all). Layer 9s extends the same delivery
	# to minion and hero attackers: the declared magic school used to cut an
	# undead attacker's reflect by its 15% magic resist, and `_is_physical_hit`
	# saw a `"normal"` hit where the source sends `"magic"`. The declared
	# `_school` argument is the native bus convention - the source passes no
	# school at all, so every attacker runs school-free (`"neutral"`).
	world._deliver_hit(-1, src_team, attacker, amount, "neutral", attacker.position, "magic")
	return amount
