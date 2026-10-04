extends "res://scripts/match/item_effects.gd"
## Concrete bus bound to a prototype_battle world. Methods translate item
## effect calls into real _deliver_hit / debuff field mutations.

const HeroState = preload("res://scripts/combat/hero_state.gd")
var world: Object = null
var dealer_id: int = -1
var dealer_team: int = -1
var dealer_pos: Vector2 = Vector2.ZERO


func deal_damage(target_id: int, _source_team: int, amount: int, school: String = "magic") -> int:
	var tgt: Object = world.get_unit(target_id)
	if tgt == null:
		return 0
	world._deliver_hit(dealer_id, dealer_team, tgt, amount, school, dealer_pos)
	return amount


func apply_stun(target_id: int, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t is HeroState:
		(t as HeroState).stun_timer = maxi((t as HeroState).stun_timer, duration)
	elif t != null and t.has_method("apply_stun"):
		# Layer 8v: port of `_apply_stun_to(target, duration)` in
		# `hero_items.py` (`fn = getattr(target, "apply_stun", None)`). When an
		# item stun (Abyss Breaker Bash / Overwhelm, Fenrir Chain Binding
		# Chains, Sundering Cudgel Piercing Bash, or Hex Idol Hexcraft) targets
		# `active_boss`, delegate to `BossState.apply_stun(duration)` so the
		# 55% boss stun resistance (`int(duration * 0.45)`) lands on
		# `boss.stun_timer` and gates `_step_active_boss()`.
		t.apply_stun(duration)


func apply_silence(target_id: int, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	# Layer 8w: port of `_apply_silence_to(target, duration)` in
	# `hero_items.py` (`hero_items.py:2693-2697`). The source helper calls
	# `target.apply_debuff('atk_slow', 1.0, duration)` and then
	# `target.apply_debuff('skill_down', 1.0, duration)`, and `Boss` overrides
	# `apply_debuff` (`bosses/base_boss.py:540-552`): `atk_slow` is cut by boss
	# tenacity (`min(0.35, 1.0 * (1.0 - 0.50))` magnitude, `int(duration * 0.50)`
	# ticks) while `skill_down` keeps the raw payload, both stored with the
	# strongest-wins/longer-refresh rule. So every item silence proc
	# (`sanguine_thorn` Soul Rend, `astral_codex` Arcane Nova, `hex_idol`
	# Hexcraft) must run `BossState.apply_debuff` instead of writing fields.
	if t.has_method("apply_debuff"):
		t.apply_debuff("atk_slow", 1.0, duration)
		t.apply_debuff("skill_down", 1.0, duration)
		return
	# UnitState already carries atk_slow/skill_down fields.
	t.atk_slow_amount = 1.0
	t.atk_slow_timer = maxi(t.atk_slow_timer, duration)
	t.skill_down_amount = 1.0
	t.skill_down_timer = maxi(t.skill_down_timer, duration)


func apply_slow(target_id: int, amount: float, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	# Layer 8x: the source item slow arms call the target method directly -
	# `target.apply_slow(oa['slow'], oa['duration'])` Frostbound Frostbite
	# (`hero_items.py:2594-2595`), `target.apply_slow(1.0, vr['root_duration'])`
	# Vine Rod Entangle (`hero_items.py:2662`), and
	# `e.apply_slow(act['slow'], act['slow_duration'])` Everfrost Arctic Blast
	# (`hero_items.py:2290-2291`) - each behind `hasattr(target, 'apply_slow')`.
	# `Boss.apply_slow` (`bosses/base_boss.py:528-538`) cuts magnitude and
	# duration by tenacity 0.50 with a 0.35 magnitude cap and stores with the
	# amount-greater-or-longer-refresh rule, so a rooted/arctic-blasted boss must
	# not take the raw `UnitState` field write below.
	if t.has_method("apply_slow"):
		t.apply_slow(amount, duration)
		return
	t.slow_amount = maxf(t.slow_amount, amount)
	t.slow_timer = maxi(t.slow_timer, duration)


func apply_burn(target_id: int, dps: float, duration: int, source_team: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	t.burn_dps = maxf(t.burn_dps, dps)
	t.burn_timer = maxi(t.burn_timer, duration)
	t.burn_team = source_team


func apply_armor_shred(target_id: int, amount: float, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	t.apply_armor_shred(amount, duration)


func apply_damage_amp(target_id: int, amount: float, duration: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	t.apply_damage_amp(amount, duration)


func apply_atk_slow(target_id: int, amount: float, duration: int) -> void:
	# Layer 8x: Frostbound Frostbite applies its attack-speed slow through
	# `target.apply_debuff('atk_slow', oa['atk_slow'], oa['duration'])`
	# (`hero_items.py:2597-2599`), which for a boss is `Boss.apply_debuff`
	# (`bosses/base_boss.py:540-552`): tenacity 0.50 cuts the magnitude (cap
	# 0.35) and the duration before the `TowerDebuffMixin` store
	# (`_core.py:918-947`). Non-boss targets keep the world-level
	# strongest-wins store with the untempered payload.
	var t: Object = world.get_unit(target_id)
	if t != null and t.has_method("apply_debuff"):
		t.apply_debuff("atk_slow", amount, duration)
		return
	world.apply_atk_slow(target_id, amount, duration)


func apply_anti_heal(target_id: int, amount: float, duration: int) -> void:
	world.apply_anti_heal(target_id, amount, duration)


func cleave_splash(
	target_id: int, src_team: int, src_pos: Vector2, splash: int, radius: float
) -> void:
	var center: Object = world.get_unit(target_id)
	if center == null:
		return
	var center_pos: Vector2 = center.position
	for u in world.units:
		if u == null or not u.alive or u.team == src_team or u.id == target_id:
			continue
		if center_pos.distance_to(u.position) <= radius:
			world._deliver_hit(dealer_id, src_team, u, splash, "physical", src_pos)


func chain_targets(target_id: int, src_team: int, radius: float, count: int) -> Array:
	var tgt: Object = world.get_unit(target_id)
	if tgt == null or not tgt.alive:
		return []
	var center: Vector2 = tgt.position
	var hits: Array = [target_id]
	for u in world.units:
		if u == null or not u.alive or u.team == src_team or u.id == target_id:
			continue
		if center.distance_to(u.position) <= radius:
			hits.append(u.id)
			if hits.size() >= count:
				break
	return hits


func nudge_position(hid: int, delta: Vector2) -> void:
	var t: Object = world.get_unit(hid)
	if t != null:
		t.position += delta
