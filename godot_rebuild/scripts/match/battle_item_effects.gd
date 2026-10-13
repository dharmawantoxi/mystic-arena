extends "res://scripts/match/item_effects.gd"
## Concrete bus bound to a prototype_battle world. Methods translate item
## effect calls into real _deliver_hit / debuff field mutations.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
var world: Object = null
var dealer_id: int = -1
var dealer_team: int = -1
var dealer_pos: Vector2 = Vector2.ZERO


func deal_damage(target_id: int, _source_team: int, amount: int, _school: String = "magic") -> int:
	var tgt: Object = world.get_unit(target_id)
	if tgt == null:
		return 0
	# Layers 9o/9p: every source item arm lands the bonus on the basic-attack
	# target as `target.take_damage(amount, h.team[, "magic"])`
	# (`hero_items.py:2542/2568/2589/2633/2648`), with no `source=`. 9o routed
	# tower/castle victims that way; 9p extends the same route to the unit
	# victims. `Minion.take_damage` / `Hero.take_damage` therefore run with
	# `source=None` and `school=None`: the minion armour and magic resist never
	# cut the arm (the resolver returns None), a hero victim keeps its item
	# armour only because the source armour branch is damage-type driven
	# (`_entity.py` `Hero.take_damage`, layer 9l), and
	# `credit_hero_damage(None, ...)` records nothing.
	world._deliver_hit(-1, dealer_team, tgt, amount, "neutral", dealer_pos)
	return amount


## Layer 9c: `damage_type` is forwarded to `_deliver_hit` so the hit reaches
## `BossState.take_damage` as magic, not as the "normal" default that arms
## `BossState.blind_live` against the (possibly blinded) stored owner.
func deal_damage_from(
	source_id: int,
	source_team: int,
	source_pos: Vector2,
	target_id: int,
	amount: int,
	school: String = "magic",
	damage_type: String = "magic"
) -> int:
	var tgt: Object = world.get_unit(target_id)
	if tgt == null:
		return 0
	var origin := source_pos
	var source: Object = world.get_unit(source_id)
	if source != null:
		var current_pos: Variant = source.get("position")
		if current_pos is Vector2:
			origin = current_pos
	if not (tgt is BossState):
		# Layer 9aa: for every non-boss victim the source call is
		# `tgt.take_damage(m["damage"], team, "magic")` (`hero_items.py:223-227`) -
		# three positional arguments, no `source=`. The hit is therefore
		# SOURCELESS and team-filter-free: it never credits the poison owner's
		# `damage_dealt`, never reflects back through the victim's Razor Carapace
		# or Bristleback, and a lethal tick leaves `killed_by` unset. The native
		# bus used to pass the owner id, which did all three.
		world._deliver_hit(-1, source_team, tgt, amount, school, origin, damage_type, true)
		return amount
	var landed: bool = world._deliver_hit(
		source_id, source_team, tgt, amount, school, origin, damage_type
	)
	if landed:
		# Layer 9d: `_tick_miasma` calls `Boss.take_damage(damage, team, "magic")`
		# with no `source=`. The active boss keeps the stored owner ID purely as
		# the native hit-event replay handle (9b pins it) and flags the tick so
		# `_process_boss_kill` cannot credit that owner. The school it receives is
		# the sourceless `"neutral"` the source resolves.
		(tgt as BossState).last_hit_is_miasma_tick = true
	return amount


func deal_damage_sourceless(
	target_id: int, source_team: int, amount: int, school: String = "physical"
) -> int:
	# Layer 9f: `_on_hit_common` lands the Abyss Breaker Bash with
	# `target.take_damage(bash["damage"], h.team)` (`hero_items.py:2542`). For the
	# active boss that means `Boss.take_damage(damage, from_team)`: the Solar
	# Brand blind block is skipped (it needs `source is not None`),
	# `resolve_damage_school('normal', None, None)` returns `None` so boss armor
	# never cuts the bonus damage, and a lethal bash leaves `_killed_by = None`
	# so `Game._process_boss_kill` credits nobody. Regular victims keep the
	# declared school and the dealing hero as source, exactly as before.
	# Layer 9p: the non-boss fallback now runs the same sourceless route
	# (`deal_damage` delivers `-1` + `neutral` to minion and hero victims too).
	var tgt: Object = world.get_unit(target_id)
	if tgt == null:
		return 0
	if tgt is BossState:
		world._deliver_hit(-1, source_team, tgt, amount, "neutral", dealer_pos)
		return amount
	return deal_damage(target_id, source_team, amount, school)


func deal_damage_magic_sourceless(
	target_id: int, source_team: int, amount: int, _school: String = "magic"
) -> int:
	# Layer 9g: the on-hit magic arms (arc chain `hero_items.py:2568`,
	# Sundering Cudgel Piercing Bash `:2589`, Polycephaly multishot `:2633`,
	# Runic Gavel Empower Strike `:2648`) call
	# `take_damage(damage, h.team, "magic")` - three positional arguments, so
	# `Boss.take_damage` runs with `damage_type="magic"` and `source=None`. The
	# native bus used to send those arms through `deal_damage`, which delivered
	# `damage_type="normal"` with the dealing hero as source: the Solar Brand
	# blind gate swallowed the hit for a blinded owner, `school="magic"` cut it
	# by boss magic resist while the source resolves no school at all
	# (`resolve_damage_school('magic', None, None)` returns `None`,
	# `_entity.py:106-130`), and a lethal hit credited the owner with the kill.
	# Layer 9r: the unit victims take the same source shape - the third
	# positional argument `"magic"` is the damage type, so minion and hero
	# victims must receive `damage_type="magic"` as well. The declared `school`
	# argument is the native bus convention: the source passes no school at all,
	# so every victim runs school-free ("neutral"). `_deliver_hit` turns
	# that into the source `_is_physical_hit` gates (`_entity.py:92-103`): a
	# Windrun hero never rolls its 75% miss chance and an evasive hero never
	# rolls Monarch Wings against these arms, exactly like the source.
	var tgt: Object = world.get_unit(target_id)
	if tgt == null:
		return 0
	world._deliver_hit(-1, source_team, tgt, amount, "neutral", dealer_pos, "magic")
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
	# Layer 9af: heroes and minions carry the source mixin too, so their silence
	# runs the same `apply_debuff` store the boss arm just used - the world level
	# stores implement exactly that rule (alive guard, amount-greater-or-longer
	# refresh). The raw write kept here before forced `1.0` into the amount even
	# when the victim already carried a stronger-but-shorter or
	# weaker-but-longer clock (measured: 0.9/200 + silence 60 -> source 1.0/60,
	# old 1.0/200) and it silenced towers, which never join the mixin
	# (`_entity.py` gives it to Hero/Minion/Boss only), while the world stores
	# refuse structures exactly like the source `AttributeError` path.
	world.apply_atk_slow(target_id, 1.0, duration)
	world.apply_skill_down(target_id, 1.0, duration)


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
	#
	# Layer 9ae: `UnitState.apply_slow` now carries the same mixin method for
	# every other victim (alive guard, item slow resist, amount-or-timer
	# refresh), so the delegation below reaches heroes, minions and structures
	# too instead of only the boss.
	if t.has_method("apply_slow"):
		t.apply_slow(amount, duration)
		return
	t.slow_amount = maxf(t.slow_amount, amount)
	t.slow_timer = maxi(t.slow_timer, duration)


func apply_burn(target_id: int, dps: float, duration: int, source_team: int) -> void:
	var t: Object = world.get_unit(target_id)
	if t == null:
		return
	# Layer 8y: every item burn arm calls `u.apply_debuff('burn', ...)` in the
	# source (Searbrand Brand Burst, `hero_items.py:614-622`), so a boss target
	# must run `BossState.apply_debuff` -> `store_debuff`
	# (`boss_state.gd:527-540`): a fresh burn on a boss whose previous burn
	# already expired resets `burn_accum` and `burn_tick_cd` to
	# `rules.burn_tick` and only follows a real team id for `burn_team`.
	# The raw field write below kept the stale tick clock of the expired burn,
	# so the first tick fired early and burned for a different amount
	# (measured: int(22/60 * 23) = 8 damage at frame 23 instead of none).
	if t.has_method("apply_debuff"):
		t.apply_debuff("burn", dps, duration, source_team)
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
	# Layer 9ad: every source anti-heal arm calls `u.apply_debuff('anti_heal',
	# ...)` polymorphically - Frostbound Frostbite (`hero_items.py:2597-2599`),
	# Everfrost Freezing Aura (`hero_items.py:2843-2844`) and Searbrand
	# Cauterize (`hero_items.py:2869-2870`) - so a boss target now runs
	# `Boss.apply_debuff` (`bosses/base_boss.py:540-552`). That override only
	# cuts `slow` (through `Boss.apply_slow`) and `atk_slow` by tenacity 0.50,
	# so the boss value for `anti_heal` stays the raw payload - the shape
	# matches the source call and 9ad pins both columns (1.00/180 stays
	# 1.00/180, unlike the atk_slow arm at 8w).
	var t: Object = world.get_unit(target_id)
	if t != null and t.has_method("apply_debuff"):
		t.apply_debuff("anti_heal", amount, duration)
		return
	world.apply_anti_heal(target_id, amount, duration)


func _onhit_boss(src_team: int, target_id: int) -> Object:
	# Layer 8z: the boss arm of the source on-hit candidate list. The melee call
	# site builds `_all_units = list(gi.minions) + list(gi.get_all_heroes())` and
	# appends the living boss (`_all_units.append(gi.active_boss)`,
	# `_entity.py:4401-4410`); the ranged call site uses
	# `Hero._collect_onhit_units()` (`_entity.py:4215-4232`), which appends it the
	# same way. Cleave (`hero_items.py:2504-2518`) and arc chain
	# (`hero_items.py:2552-2560`) iterate that list, so the boss is a legal
	# secondary target. The native registry never holds the boss (`active_boss`
	# only lives in `_by_id`), so the `world.units` scan alone skipped it.
	var boss: Object = world.active_boss
	if boss == null or not boss.alive or boss.team == src_team:
		return null
	if int(boss.id) == target_id:
		return null
	return boss


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
			# Layer 9q: the source splash is `u.take_damage(splash, h.team)`
			# (`hero_items.py:2516`), so every unit victim runs school-free: the
			# minion armour never cuts the splash and `credit_hero_damage(None, ...)`
			# records nothing. A hero victim keeps its item armour (damage-type
			# driven branch, layer 9l). Layer 9e already routed the boss victim
			# of this loop that way.
			world._deliver_hit(-1, src_team, u, splash, "neutral", src_pos)
	# Source cleave radius gate is inclusive (`if d <= radius:`) and measured
	# from the main target, exactly like the unit loop above.
	var boss: Object = _onhit_boss(src_team, target_id)
	if boss != null and center_pos.distance_to(boss.position) <= radius:
		# Layer 9e: the source splash is `u.take_damage(splash, h.team)`
		# (`hero_items.py:2516`) - two positional arguments, so `Boss.take_damage`
		# runs with `source=None` and `school=None`. That skips the Solar Brand
		# blind block (it needs `source is not None`), makes
		# `resolve_damage_school('normal', None, None)` return `None` so boss armor
		# never cuts the splash, and leaves `_killed_by = None` on a lethal hit so
		# `Game._process_boss_kill` credits nobody. Layer 9q moved the unit loop
		# above onto the same sourceless route, so both branches now agree.
		world._deliver_hit(-1, src_team, boss, splash, "neutral", src_pos)


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
	# The source appends the boss last (`all_units` ends with `active_boss`) and
	# checks `len(hit) >= chain["targets"]` after every candidate, so full slots
	# end the scan before the boss is ever examined.
	if hits.size() >= count:
		return hits
	var boss: Object = _onhit_boss(src_team, target_id)
	if boss != null and center.distance_to(boss.position) <= radius:
		hits.append(int(boss.id))
	return hits


func nudge_position(hid: int, delta: Vector2) -> void:
	var t: Object = world.get_unit(hid)
	if t != null:
		t.position += delta


func notify(unit_id: int, text: String) -> void:
	if world == null or world.get("effects") == null:
		return
	var target: Object = world.get_unit(unit_id)
	var pos: Vector2 = target.position if target != null else dealer_pos
	world.effects.add_damage_number(pos.x, pos.y - 25.0, text, false, "magic")
