extends "res://scripts/match/item_effects.gd"
## Bus for Thornmail reflect: damage is dealt with source_id=-1 (no credit
## loop, matching the source Bristleback reflect precedent).

var world: Object = null
var defender_team: int = 0


func deal_damage(target_id: int, src_team: int, amount: int, school: String = "magic") -> int:
	var attacker: Object = world.get_unit(target_id)
	if attacker == null:
		return 0
	world._deliver_hit(-1, src_team, attacker, amount, school, attacker.position)
	return amount
