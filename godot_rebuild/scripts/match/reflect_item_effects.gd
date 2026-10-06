extends "res://scripts/match/item_effects.gd"
## Bus for Thornmail reflect: damage is dealt with source_id=-1 (no credit
## loop, matching the source Bristleback reflect precedent).

const BossState = preload("res://scripts/match/boss_state.gd")

var world: Object = null
var defender_team: int = 0


func deal_damage(target_id: int, src_team: int, amount: int, school: String = "magic") -> int:
	var attacker: Object = world.get_unit(target_id)
	if attacker == null:
		return 0
	if attacker is BossState:
		# Layer 9i: the Razor Carapace reflect calls
		# `source.take_damage(dmg, self.hero.team, "magic")`
		# (`hero_items.py:2468`) - three positional arguments, so
		# `Boss.take_damage` runs with `damage_type="magic"` and
		# `source=None`. The bus used to deliver the `"normal"` damage-type
		# default with the declared magic school: the blind gate and the kill
		# credit already matched the source (no source on either side), but
		# `school="magic"` cut the reflected payload by boss magic resist
		# while the source resolves no school at all
		# (`resolve_damage_school('magic', None, None)` returns `None`,
		# `_entity.py:106-130`). Non-boss attackers keep the declared school
		# and the sourceless delivery below, exactly as before this layer.
		world._deliver_hit(-1, src_team, attacker, amount, "neutral", attacker.position, "magic")
		return amount
	world._deliver_hit(-1, src_team, attacker, amount, school, attacker.position)
	return amount
