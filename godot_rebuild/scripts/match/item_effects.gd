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


## Deal damage attributed to a stored effect owner rather than the ticking hero.
## Layer 9c: `damage_type` mirrors the third positional argument that the source
## passes to `Boss.take_damage`. Item damage is magic there, so a blinded owner
## cannot have its poison swallowed by the boss blind gate (plain hits only).
func deal_damage_from(
	_source_id: int,
	_source_team: int,
	_source_pos: Vector2,
	target_id: int,
	amount: int,
	school: String = "magic",
	_damage_type: String = "magic"
) -> int:
	return deal_damage(target_id, _source_team, amount, school)


## Deal damage with the source call shape that omits both `source=` and
## `school=`. Layer 9f: the Abyss Breaker Bash arm calls
## `target.take_damage(bash["damage"], h.team)` (`hero_items.py:2542`), two
## positional arguments, so a boss victim runs `Boss.take_damage` with
## `source=None` and `school=None`. Buses without a boss registry simply keep
## the declared school.
func deal_damage_sourceless(
	target_id: int, source_team: int, amount: int, school: String = "physical"
) -> int:
	return deal_damage(target_id, source_team, amount, school)


## Deal damage with the source call shape that omits `source=` but keeps the
## magic `damage_type`. Layer 9g: the on-hit magic arms call
## `target.take_damage(damage, h.team, "magic")` (`hero_items.py:2568, 2589,
## 2633, 2648`), three positional arguments, so a boss victim runs
## `Boss.take_damage` (`bosses/base_boss.py:5978`) with
## `damage_type="magic"`, `source=None`, `school=None`. Buses without a boss
## registry keep the declared school.
func deal_damage_magic_sourceless(
	target_id: int, source_team: int, amount: int, school: String = "magic"
) -> int:
	return deal_damage(target_id, source_team, amount, school)


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


## Apply atk-speed slow (percent, ticks).
func apply_atk_slow(_target_id: int, _amount: float, _duration: int) -> void:
	pass


## Apply anti-heal (percent, ticks).
func apply_anti_heal(_target_id: int, _amount: float, _duration: int) -> void:
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


## Cleave splash damage (melee only).
func cleave_splash(
	_target_id: int, _src_team: int, _src_pos: Vector2, _splash: int, _radius: float
) -> void:
	pass


## Return up to `count` enemy unit ids within radius of target.
func chain_targets(_target_id: int, _src_team: int, _radius: float, _count: int) -> Array:
	return []
