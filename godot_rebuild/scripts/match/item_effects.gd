extends RefCounted
## Callback bus passed to HeroItemInventory.tick_auto() so the pure inventory
## never reaches back into the battle layer. Each method mirrors one Python
## helper in hero_items.py; the battle layer translates the call into real
## _deliver_hit / debuff / movement mutations.
##
## Layer 5c-2 scope: auto-triggers, notify_damage_taken (reflect), HP regen
## and tick wiring. Auras (5d) and on-hit procs (5e) extend this bus later.


## Deal magic damage to target from source_team. Returns the post-mitigation
## damage actually applied (used by Thornmail reflect validation).
func deal_damage(
	_target_id: int, _source_team: int, _amount: int, _school: String = "magic"
) -> int:
	return 0


## Apply a stun for `duration` ticks.
func apply_stun(_target_id: int, _duration: int) -> void:
	pass


## Apply silence (atk_slow + skill_down 100%) for `duration` ticks.
func apply_silence(_target_id: int, _duration: int) -> void:
	pass


## Apply a slow (percent, ticks).
func apply_slow(_target_id: int, _amount: float, _duration: int) -> void:
	pass


## Apply a burn DoT.
func apply_burn(_target_id: int, _dps: float, _duration: int, _source_team: int) -> void:
	pass


## Apply damage amp (multiplier fraction, ticks).
func apply_damage_amp(_target_id: int, _amount: float, _duration: int) -> void:
	pass


## Apply armor shred.
func apply_armor_shred(_target_id: int, _amount: float, _duration: int) -> void:
	pass


## Move a hero by the given delta (Gale Pike retreat).
func nudge_position(_hero_id: int, _delta: Vector2) -> void:
	pass


## Floating notification text (no-op in headless tests).
func notify(_unit_id: int, _text: String) -> void:
	pass


## Chain-lightning visual between source and targets (no-op in tests).
func chain_fx(_source_id: int, _target_ids: Array) -> void:
	pass
