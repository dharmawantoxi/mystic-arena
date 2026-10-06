# gdlint:disable=max-file-lines, max-public-methods
# gdlint:disable=max-public-methods
extends RefCounted
## Port of HeroItemInventory: six slots, the melee_only/magic_only gates,
## drop-on-death, the PURE stat aggregation getters, the timer state machine
## (tick_timers), and the auto-trigger half of update() plus
## notify_damage_taken() (layer 5c-2). The source instance lives on the hero
## as `hero.items`; the rebuild keeps one per HeroState. Effects dispatch
## through an ItemEffects callback bus so the inventory never references the
## battle layer directly.
##
## LIMITATION, NOT PARITY (layer 5c-2 scope):
## - `update_auras()` (5d) lives on the battle layer, not here.
## - Hero runtime state (hp/pos/alive/facing/target_id) must be refreshed via
##   set_hero_runtime() every tick before tick_auto(); the inventory keeps no
##   hero reference.
## - Layer 9b binds every match inventory to PrototypeBattle's shared,
##   target-keyed Miasma registry. Reapplication replaces source id/team while
##   retaining strongest damage, longest timer and shortest tick countdown.
## The source-side values are locked in `tests/fixtures/ai_items_source.json`
## ("auto_triggers", "notify_damage"), so this contract updates as each layer
## lands.

const HeroItems = preload("res://scripts/match/hero_items.gd")
const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const ItemEffects = preload("res://scripts/match/item_effects.gd")
const RAPIER := "holy_rapier"
# Source update() decrements exactly these, in this order.
const TIMER_FIELDS := [
	"guard_timer",
	"guard_cd",
	"veil_timer",
	"veil_cd",
	"chains_cd",
	"rend_timer",
	"rend_cd",
	"bash_cd",
	"overwhelm_cd",
	"static_timer",
	"static_cd",
	"static_tick",
	"thorn_timer",
	"thorn_cd",
	"arctic_cd",
	"gale_timer",
	"gale_cd",
	"pierce_bash_cd",
	"searbrand_cd",
	"arcane_cd",
	"fulgur_cd",
	"hex_cd",
	"rift_cd",
	"pact_cd",
	"vine_cd",
	"ghost_timer",
	"ghost_cd",
]

# Plain copies of the owner role/attack range/base HP/level (refreshed by
# HeroState). The source reads them from the hero on every call; copies keep
# hero and inventory free of a RefCounted reference cycle.
var hero_id := -1
var hero_role := ""
var hero_range := 0.0
var hero_base_hp := 0
var hero_level := 1
# -1 = unknown, so get_range_bonus falls back to the source `range < 110`
# heuristic (Hero.is_melee_hero is that same rule, _entity.py:3303).
var hero_melee_flag := -1
# Hero runtime state is refreshed by the battle caller before tick_auto().
# The inventory owns no hero reference.
var hero_alive := true
var hero_hp := 0.0
var hero_max_hp := 0
var hero_team := 0
var hero_facing := 1.0
var hero_position := Vector2.ZERO
var hero_target_id := -1
var catalog: Dictionary
var slots: Array = []
# Read by the getters below, never advanced in this layer (see header).
var aura_armor := 0
var aura_as := 0
var aura_armor_reduction := 0
var aura_guard_block := 0
var blood_frenzy_timer := 0
var ghost_timer := 0
var thorn_timer := 0
var gale_timer := 0
var veil_timer := 0
var veil_cd := 0
var guard_timer := 0
var rend_timer := 0
var empower_charge := 0
# Remaining timers the source update() decrements. Nothing but tick_timers
# moves them in this layer: the active/passive effects they gate (chain,
# static charge, arctic blast, miasma, auras) are layers 5d/5e.
var blood_frenzy_cd := 0
var last_damage_timer := 0
var guard_cd := 0
var chains_cd := 0
var rend_cd := 0
var static_timer := 0
var thorn_cd := 0
var bash_cd := 0
var overwhelm_cd := 0
var static_tick := 0
var static_cd := 0
var arctic_cd := 0
var gale_cd := 0
var pierce_bash_cd := 0
var searbrand_cd := 0
var arcane_cd := 0
var fulgur_cd := 0
var hex_cd := 0
var rift_cd := 0
var pact_cd := 0
var vine_cd := 0
var ghost_cd := 0
# Entity id of the Soul Rend target; -1 is the source None.
var rend_target := -1
# Layer 5e-2: Miasma trackers keyed by target id (damage, timer, tick_cd).
var miasma: Dictionary = {}


func _init(metadata: Dictionary = {}) -> void:
	if metadata.is_empty():
		catalog = JSON.parse_string(FileAccess.get_file_as_string(HeroItems.METADATA))
	else:
		catalog = metadata.duplicate(true)
	slots.resize(max_slots())
	# Source __init__ preloads the Runic Gavel charge whether or not it is owned.
	empower_charge = int(item("runic_gavel").get("passive", {}).get("charge_time", 0))


func set_hero_gate(role: String, attack_range: float) -> void:
	hero_role = role
	hero_range = attack_range


func set_hero_scaling(base_hp: int, level: int, melee_flag: int) -> void:
	hero_base_hp = base_hp
	hero_level = level
	hero_melee_flag = melee_flag


func set_hero_runtime(
	p_id: int,
	alive: bool,
	hp: float,
	max_hp: int,
	team: int,
	facing: float,
	pos: Vector2,
	target_id: int,
) -> void:
	hero_id = p_id
	hero_alive = alive
	hero_hp = hp
	hero_max_hp = max_hp
	hero_team = team
	hero_facing = facing
	hero_position = pos
	hero_target_id = target_id


func max_slots() -> int:
	return int(catalog.get("max_slots", 6))


func item(item_id: String) -> Dictionary:
	var items: Dictionary = catalog.get("items", {})
	return items.get(item_id, {})


func count(item_id: String) -> int:
	var total := 0
	for slot in slots:
		if slot == item_id:
			total += 1
	return total


func has(item_id: String) -> bool:
	return slots.has(item_id)


func used_slots() -> int:
	var used := 0
	for slot in slots:
		if slot != null:
			used += 1
	return used


func owned() -> Array:
	# Source builds `set(s for s in slots if s is not None)` before suggesting.
	var result: Array = []
	for slot in slots:
		if slot != null:
			result.append(String(slot))
	return result


func add(item_id: String) -> bool:
	# Fill the first empty slot. Source returns False on unknown id, on a
	# melee_only item for a ranged hero (`rng and rng > 80`, so range 0 passes)
	# and on a magic_only item for a non-magic role.
	var data := item(item_id)
	if data.is_empty():
		return false
	if bool(data.get("melee_only", false)) and hero_range > HeroItems.MELEE_RANGE_LIMIT:
		return false
	if bool(data.get("magic_only", false)) and not HeroItems.is_magic_hero(hero_role):
		return false
	for index in range(max_slots()):
		if slots[index] == null:
			slots[index] = item_id
			return true
	return false


func remove(slot_index: int) -> String:
	# Source drop: no gold refund. Returns the dropped id or an empty string.
	if slot_index < 0 or slot_index >= max_slots():
		return ""
	var old = slots[slot_index]
	if old == null:
		return ""
	slots[slot_index] = null
	return String(old)


func clear_on_death() -> bool:
	# Source: Holy Rapier is destroyed, never dropped on the ground.
	var dropped := false
	for index in range(max_slots()):
		if slots[index] == RAPIER:
			slots[index] = null
			dropped = true
	return dropped


# ── Agregasi stat (port getter murni) ─────────────────────────
func sum_stat(key: String) -> float:
	var total := 0.0
	for slot in slots:
		if slot == null:
			continue
		var stats: Dictionary = item(String(slot)).get("stats", {})
		total += float(stats.get(key, 0.0))
	return total


func level_hp_mult() -> float:
	var data: Dictionary = HeroDefinition.level_data(hero_level)
	return float(data["hp_mult"])


func is_melee_owner() -> bool:
	# Source get_range_bonus: explicit flag first, `range < 110` heuristic else.
	if hero_melee_flag >= 0:
		return hero_melee_flag == 1
	return hero_range < 110.0


func get_bonus_damage() -> float:
	return sum_stat("damage")


func get_bonus_hp() -> float:
	return sum_stat("hp")


func get_hp_pct() -> float:
	return sum_stat("hp_pct")


func get_armor() -> float:
	return sum_stat("armor") + float(aura_armor) - float(aura_armor_reduction)


func get_hp_regen() -> float:
	return sum_stat("hp_regen")


func get_max_hp() -> int:
	# Source: (base_hp * HERO_LEVELS hp_mult + item hp) * (1 + hp_pct).
	var base := int(float(hero_base_hp) * level_hp_mult())
	return int(float(base + get_bonus_hp()) * (1.0 + get_hp_pct()))


func get_attack_speed_mult() -> float:
	var total := sum_stat("attack_speed") + float(aura_as) + get_gale_as_bonus()
	return maxf(0.2, minf(2.5, 1.0 + total / 100.0))


func get_lifesteal_pct() -> float:
	var total := sum_stat("lifesteal")
	if blood_frenzy_timer > 0:
		total += 1.5
	return minf(1.75, total)


func get_crit() -> Array:
	# Source returns (chance, mult); the multiplier starts at 2.0.
	var chance := 0.0
	var mult := 2.0
	for slot in slots:
		if slot == null:
			continue
		var stats: Dictionary = item(String(slot)).get("stats", {})
		if stats.has("crit_chance"):
			chance = maxf(chance, float(stats["crit_chance"]))
			mult = maxf(mult, float(stats.get("crit_mult", 2.25)))
	return [chance, mult]


func get_cleave() -> Variant:
	for slot in slots:
		if slot == null:
			continue
		var passive: Dictionary = item(String(slot)).get("passive", {})
		if String(passive.get("name", "")) == "Cleave":
			return [float(passive["cleave_pct"]), float(passive["cleave_radius"])]
	return null


func get_cooldown_reduction() -> float:
	return minf(0.5, sum_stat("cooldown_reduction"))


func get_spell_vamp() -> float:
	return sum_stat("spell_vamp")


func get_skill_amp() -> float:
	return minf(0.5, sum_stat("skill_amp"))


func get_evasion() -> float:
	if ghost_timer > 0 and has("spectral_charm"):
		return 1.0
	return minf(0.5, sum_stat("evasion"))


func get_move_speed_pct() -> float:
	return minf(0.4, sum_stat("move_speed_pct"))


func get_heal_amp() -> float:
	return minf(0.5, sum_stat("heal_amp"))


func get_slow_resist() -> float:
	return minf(0.6, sum_stat("slow_resist"))


func get_range_bonus() -> float:
	if is_melee_owner():
		return 0.0
	return sum_stat("range_bonus")


func has_true_strike() -> bool:
	return has("sundering_cudgel")


func get_reflect_pct() -> float:
	if thorn_timer > 0 and has("razor_carapace"):
		return float(item("razor_carapace").get("active", {}).get("reflect_pct", 0.0))
	return 0.0


func get_gale_as_bonus() -> float:
	if gale_timer > 0 and has("gale_pike"):
		return float(item("gale_pike").get("active", {}).get("as_bonus", 0.0))
	return 0.0


func consume_empower_strike() -> int:
	if has("runic_gavel") and empower_charge <= 0:
		var passive: Dictionary = item("runic_gavel").get("passive", {})
		empower_charge = int(passive.get("charge_time", 0))
		return int(passive.get("damage", 0))
	return 0


func get_block() -> Variant:
	# Source: `rng or 100`, so range 0 counts as ranged here (unlike add()).
	var melee := HeroItems.source_range(hero_range) <= HeroItems.MELEE_RANGE_LIMIT
	var best: Variant = null
	for slot in slots:
		if slot == null:
			continue
		var block: Dictionary = item(String(slot)).get("block", {})
		if block.is_empty():
			continue
		var amount := float(block["melee_block"] if melee else block["ranged_block"])
		var chance := float(block["chance"])
		if best == null or chance > float(best[0]) or amount > float(best[1]):
			best = [chance, amount]
	return best


func get_armor_shred() -> Variant:
	for slot in slots:
		if slot == null:
			continue
		var passive: Dictionary = item(String(slot)).get("passive", {})
		if passive.has("armor_shred"):
			return [float(passive["armor_shred"]), float(passive.get("duration", 300))]
	return null


func get_on_attack_chain() -> Variant:
	# Source bugfix: only a real chain dict (chance + targets + radius + damage),
	# so Frostbite/Miasma on_attack blocks are never read as chain lightning.
	for slot in slots:
		if slot == null:
			continue
		var chain: Dictionary = item(String(slot)).get("on_attack", {})
		if (
			chain.has("chance")
			and chain.has("targets")
			and chain.has("radius")
			and chain.has("damage")
		):
			return chain
	return null


func get_bash() -> Variant:
	# Source bugfix: only Abyss Breaker, never Sundering Cudgel's bash block.
	if has("abyss_breaker"):
		return item("abyss_breaker").get("bash", {})
	return null


func is_veiled() -> bool:
	return veil_timer > 0


func is_guarding() -> bool:
	return guard_timer > 0


func get_rend_crit() -> Variant:
	if rend_timer > 0 and has("sanguine_thorn"):
		return float(item("sanguine_thorn").get("active", {}).get("crit_mult", 0.0))
	return null


func tick_timers(dt: int) -> void:
	# Port of the timer state machine at the top of HeroItemInventory.update:
	# pure decrements, the Soul Rend target reset and the Runic Gavel charge.
	# The effect half of update (auto-triggers, procs, miasma, auras) is not
	# ported, so nothing here damages or buffs anyone.
	if blood_frenzy_timer > 0:
		blood_frenzy_timer -= dt
	if blood_frenzy_cd > 0:
		blood_frenzy_cd -= dt
	if last_damage_timer > 0:
		last_damage_timer -= dt
	for field in TIMER_FIELDS:
		var value: int = get(field)
		if value > 0:
			set(field, value - dt)
	if rend_timer <= 0:
		rend_target = -1
	if has("runic_gavel") and empower_charge > 0:
		empower_charge = maxi(0, empower_charge - dt)


# ── Auto-trigger half of update (layer 5c-2) ─────────────────
func tick_auto(dt: int, enemies: Array, effects: ItemEffects, _rng: RandomNumberGenerator) -> void:
	# Port of the auto-trigger/HP-regen half of HeroItemInventory.update.
	# Caller must have invoked tick_timers(dt) AND refreshed hero runtime
	# state (set_hero_runtime) BEFORE this call.
	if not hero_alive or hero_max_hp <= 0:
		return
	var ratio := hero_hp / float(hero_max_hp)
	# Demon Maw: Blood Frenzy at HP < 35% (no hp_threshold key; hardcoded).
	if has("demon_maw") and blood_frenzy_cd <= 0 and ratio < 0.35:
		var act: Dictionary = item("demon_maw").get("active", {})
		blood_frenzy_timer = int(act.get("duration", 0))
		blood_frenzy_cd = int(act.get("cooldown", 0))
		effects.notify(hero_id, "BLOOD FRENZY!")
	# Tier II auto-triggers.
	# Scarlet Bulwark: Bulwark Guard at HP threshold.
	if has("scarlet_bulwark") and guard_cd <= 0:
		var act: Dictionary = item("scarlet_bulwark").get("active", {})
		if ratio < float(act.get("hp_threshold", 0.0)):
			guard_timer = int(act.get("duration", 0))
			guard_cd = int(act.get("cooldown", 0))
			effects.notify(hero_id, "BULWARK GUARD!")
	# Tempest Vane: Veil at HP threshold.
	if has("tempest_vane") and veil_cd <= 0:
		var act: Dictionary = item("tempest_vane").get("active", {})
		if ratio < float(act.get("hp_threshold", 0.0)):
			veil_timer = int(act.get("duration", 0))
			veil_cd = int(act.get("cooldown", 0))
			effects.notify(hero_id, "TEMPEST VEIL!")
	# Fenrir Chain: 2+ enemies in trigger_radius => root + damage.
	if has("fenrir_chain") and chains_cd <= 0 and enemies.size() > 0:
		var act: Dictionary = item("fenrir_chain").get("active", {})
		var trig_r := float(act.get("trigger_radius", 0.0))
		var root_r := float(act.get("root_radius", 0.0))
		var near_ids: Array = _nearby_enemies(enemies, trig_r)
		if near_ids.size() >= int(act.get("trigger_enemies", 99)):
			chains_cd = int(act.get("cooldown", 0))
			var root_dur := int(act.get("root_duration", 0))
			var dmg := int(act.get("damage", 0))
			var rooted: Array = []
			for eid in near_ids:
				var epos: Vector2 = _enemy_pos(enemies, eid)
				if hero_position.distance_to(epos) <= root_r:
					effects.apply_stun(eid, root_dur)
					if dmg > 0:
						# Layer 9h: source `e.take_damage(act["damage"], h.team,
						# "magic")` (`hero_items.py:2209`) omits `source=`.
						effects.deal_damage_magic_sourceless(eid, hero_team, dmg, "magic")
					rooted.append(eid)
			effects.notify(hero_id, "BINDING CHAINS!")
			effects.chain_fx(hero_id, rooted)
	# Sanguine Thorn: Soul Rend on current target.
	if has("sanguine_thorn") and rend_cd <= 0:
		var tgt_id := hero_target_id
		if tgt_id >= 0 and _enemy_alive(enemies, tgt_id):
			var act: Dictionary = item("sanguine_thorn").get("active", {})
			rend_timer = int(act.get("duration", 0))
			rend_cd = int(act.get("cooldown", 0))
			rend_target = tgt_id
			effects.apply_silence(tgt_id, int(act.get("duration", 0)))
			effects.apply_damage_amp(
				tgt_id, float(act.get("damage_amp", 0.0)), int(act.get("duration", 0))
			)
			effects.notify(tgt_id, "SOUL REND!")
	# Abyss Breaker: Overwhelm stun on target.
	if has("abyss_breaker") and overwhelm_cd <= 0:
		var tgt_id := hero_target_id
		if tgt_id >= 0 and _enemy_alive(enemies, tgt_id):
			var act: Dictionary = item("abyss_breaker").get("active", {})
			overwhelm_cd = int(act.get("cooldown", 0))
			effects.apply_stun(tgt_id, int(act.get("stun", 0)))
			effects.notify(tgt_id, "OVERWHELM!")
	# Thunder Coil: static zap tick.
	if static_timer > 0 and has("thunder_coil") and enemies.size() > 0:
		var act: Dictionary = item("thunder_coil").get("active", {})
		static_tick -= dt
		if static_tick <= 0:
			static_tick = int(act.get("tick", 0))
			var rad := float(act.get("radius", 0.0))
			var tgt_count := int(act.get("targets", 0))
			var dmg := int(act.get("damage", 0))
			var near_ids: Array = _nearby_enemies_sorted(enemies, rad)
			var zapped: Array = []
			for i in range(mini(near_ids.size(), tgt_count)):
				var eid: int = near_ids[i]
				if dmg > 0:
					# Layer 9h: source `e.take_damage(act["damage"], h.team,
					# "magic")` (`hero_items.py:2257`) omits `source=`.
					effects.deal_damage_magic_sourceless(eid, hero_team, dmg, "magic")
				zapped.append(eid)
			if zapped.size() > 0:
				effects.chain_fx(hero_id, zapped)
	# Razor Carapace: Thornmail at HP threshold.
	if has("razor_carapace") and thorn_cd <= 0:
		var act: Dictionary = item("razor_carapace").get("active", {})
		if ratio < float(act.get("hp_threshold", 0.0)):
			thorn_timer = int(act.get("duration", 0))
			thorn_cd = int(act.get("cooldown", 0))
			effects.notify(hero_id, "THORNMAIL!")
	# Everfrost Guard: Arctic Blast on 2+ nearby.
	if has("everfrost_guard") and arctic_cd <= 0 and enemies.size() > 0:
		var act: Dictionary = item("everfrost_guard").get("active", {})
		var rad := float(act.get("radius", 0.0))
		var near_ids: Array = _nearby_enemies(enemies, rad)
		if near_ids.size() >= int(act.get("trigger_enemies", 99)):
			arctic_cd = int(act.get("cooldown", 0))
			var dmg := int(act.get("damage", 0))
			var slow := float(act.get("slow", 0.0))
			var slow_dur := int(act.get("slow_duration", 0))
			var hit: Array = []
			for eid in near_ids:
				if dmg > 0:
					# Layer 9h: source `e.take_damage(act["damage"], h.team,
					# "magic")` (`hero_items.py:2286`) omits `source=`.
					effects.deal_damage_magic_sourceless(eid, hero_team, dmg, "magic")
				effects.apply_slow(eid, slow, slow_dur)
				hit.append(eid)
			effects.notify(hero_id, "ARCTIC BLAST!")
			effects.chain_fx(hero_id, hit)
	# Gale Pike: retreat dash at low HP.
	if has("gale_pike") and gale_cd <= 0:
		var act: Dictionary = item("gale_pike").get("active", {})
		if ratio < float(act.get("hp_threshold", 0.0)):
			gale_timer = int(act.get("duration", 0))
			gale_cd = int(act.get("cooldown", 0))
			var dash := float(act.get("dash_distance", 0.0))
			var delta := Vector2.ZERO
			var tgt_id := hero_target_id
			if tgt_id >= 0 and _enemy_alive(enemies, tgt_id):
				var tpos: Vector2 = _enemy_pos(enemies, tgt_id)
				var away := hero_position - tpos
				if away.length() > 0.001:
					delta = away.normalized() * dash
				else:
					delta = Vector2(-hero_facing, 0.0) * dash
			else:
				delta = Vector2(-hero_facing, 0.0) * dash
			effects.nudge_position(hero_id, delta)
			effects.notify(hero_id, "GALE LEAP!")
	# Searbrand: Brand Burst burn on 2+ nearby.
	if has("searbrand") and searbrand_cd <= 0 and enemies.size() > 0:
		var act: Dictionary = item("searbrand").get("active", {})
		var rad := float(act.get("radius", 0.0))
		var near_ids: Array = _nearby_enemies(enemies, rad)
		if near_ids.size() >= int(act.get("trigger_enemies", 99)):
			searbrand_cd = int(act.get("cooldown", 0))
			var dmg := int(act.get("damage", 0))
			var burn_dps_v := float(act.get("burn_dps", 0.0))
			var burn_dur := int(act.get("burn_duration", 0))
			var hit: Array = []
			for eid in near_ids:
				if dmg > 0:
					# Layer 9h: source `e.take_damage(act["damage"], h.team,
					# "magic")` (`hero_items.py:2329`) omits `source=`.
					effects.deal_damage_magic_sourceless(eid, hero_team, dmg, "magic")
				effects.apply_burn(eid, burn_dps_v, burn_dur, hero_team)
				hit.append(eid)
			effects.notify(hero_id, "BRAND BURST!")
			effects.chain_fx(hero_id, hit)
	# Astral Codex: Arcane Nova silence on 2+ nearby.
	if has("astral_codex") and arcane_cd <= 0 and enemies.size() > 0:
		var act: Dictionary = item("astral_codex").get("active", {})
		var rad := float(act.get("radius", 0.0))
		var near_ids: Array = _nearby_enemies(enemies, rad)
		if near_ids.size() >= int(act.get("trigger_enemies", 99)):
			arcane_cd = int(act.get("cooldown", 0))
			var dmg := int(act.get("damage", 0))
			var sil_dur := int(act.get("silence_duration", 0))
			var hit: Array = []
			for eid in near_ids:
				if dmg > 0:
					# Layer 9h: source `e.take_damage(act["damage"], h.team,
					# "magic")` (`hero_items.py:2358`) omits `source=`.
					effects.deal_damage_magic_sourceless(eid, hero_team, dmg, "magic")
				effects.apply_silence(eid, sil_dur)
				hit.append(eid)
			effects.notify(hero_id, "ARCANE NOVA!")
			effects.chain_fx(hero_id, hit)
	# Fulgur Scepter: Energy Blast on target.
	if has("fulgur_scepter") and fulgur_cd <= 0:
		var tgt_id := hero_target_id
		if tgt_id >= 0 and _enemy_alive(enemies, tgt_id):
			var act: Dictionary = item("fulgur_scepter").get("active", {})
			fulgur_cd = int(act.get("cooldown", 0))
			var dmg := int(act.get("damage", 0))
			if dmg > 0:
				# Layer 9h: source `tgt.take_damage(act["damage"], h.team,
				# "magic")` (`hero_items.py:2377`) omits `source=`.
				effects.deal_damage_magic_sourceless(tgt_id, hero_team, dmg, "magic")
			effects.notify(tgt_id, "ENERGY BLAST!")
	# Hex Idol: Hex (stun + silence) on target.
	if has("hex_idol") and hex_cd <= 0:
		var tgt_id := hero_target_id
		if tgt_id >= 0 and _enemy_alive(enemies, tgt_id):
			var act: Dictionary = item("hex_idol").get("active", {})
			hex_cd = int(act.get("cooldown", 0))
			effects.apply_stun(tgt_id, int(act.get("stun", 0)))
			effects.apply_silence(tgt_id, int(act.get("silence", 0)))
			effects.notify(tgt_id, "HEX!")
	# Rift Veil: Discord Field amp on 2+ nearby.
	if has("rift_veil") and rift_cd <= 0 and enemies.size() > 0:
		var act: Dictionary = item("rift_veil").get("active", {})
		var rad := float(act.get("radius", 0.0))
		var near_ids: Array = _nearby_enemies(enemies, rad)
		if near_ids.size() >= int(act.get("trigger_enemies", 99)):
			rift_cd = int(act.get("cooldown", 0))
			var amp := float(act.get("damage_amp", 0.0))
			var dur := int(act.get("duration", 0))
			for eid in near_ids:
				effects.apply_damage_amp(eid, amp, dur)
			effects.notify(hero_id, "DISCORD FIELD!")
			effects.chain_fx(hero_id, near_ids)
	# Vital Stone: Vitality Pact heal at low HP.
	if has("vital_stone") and pact_cd <= 0:
		var act: Dictionary = item("vital_stone").get("active", {})
		if ratio < float(act.get("hp_threshold", 0.0)):
			pact_cd = int(act.get("cooldown", 0))
			var heal_amt := int(float(hero_max_hp) * float(act.get("heal_pct", 0.0)))
			if heal_amt > 0:
				hero_hp = mini(float(hero_max_hp), hero_hp + float(heal_amt))
			effects.notify(hero_id, "VITALITY PACT!")
	# Spectral Charm: Spectral Form (evasion) at low HP.
	if has("spectral_charm") and ghost_cd <= 0:
		var act: Dictionary = item("spectral_charm").get("active", {})
		if ratio < float(act.get("hp_threshold", 0.0)):
			ghost_timer = int(act.get("duration", 0))
			ghost_cd = int(act.get("cooldown", 0))
			effects.notify(hero_id, "SPECTRAL FORM!")
	# HP regen (base + Leviathan out-of-combat).
	if hero_hp < float(hero_max_hp):
		var regen := get_hp_regen()
		if has("leviathan_heart"):
			var p: Dictionary = item("leviathan_heart").get("passive", {})
			if last_damage_timer <= 0:
				regen += float(hero_max_hp) * float(p.get("out_of_combat_regen_pct", 0.0)) / 60.0
		if regen > 0:
			hero_hp = mini(float(hero_max_hp), hero_hp + regen)


func notify_damage_taken(
	damage: int,
	source_id: int,
	source_team: int,
	source_alive: bool,
	rng: RandomNumberGenerator,
	effects: ItemEffects
) -> void:
	# Port of HeroItemInventory.notify_damage_taken: Leviathan combat timer,
	# Thunder Coil static proc chance, Razor Carapace thornmail reflect.
	# `damage` is post-mitigation (already subtracted hp by caller).
	if has("leviathan_heart"):
		var p: Dictionary = item("leviathan_heart").get("passive", {})
		last_damage_timer = int(p.get("combat_timeout", 0))
	if has("thunder_coil") and static_cd <= 0:
		var act: Dictionary = item("thunder_coil").get("active", {})
		if rng.randf() < float(act.get("proc_chance", 0.0)):
			static_timer = int(act.get("duration", 0))
			static_tick = int(act.get("tick", 0))
			static_cd = int(act.get("cooldown", 0))
			effects.notify(hero_id, "STATIC CHARGE!")
	var refl := get_reflect_pct()
	if refl > 0.0 and damage > 0 and source_id >= 0 and source_alive and source_team != hero_team:
		var dmg := int(float(damage) * refl)
		if dmg > 0:
			effects.deal_damage(source_id, hero_team, dmg, "magic")
			effects.notify(source_id, "-" + str(dmg))


# ── Enemy list helpers (enemies is an Array of {id,pos,team,alive}) ─────────
func _enemy_entry(enemies: Array, eid: int) -> Dictionary:
	for e in enemies:
		var d: Dictionary = e as Dictionary
		if int(d.get("id", -2)) == eid:
			return d
	return {}


func _enemy_pos(enemies: Array, eid: int) -> Vector2:
	return _enemy_entry(enemies, eid).get("pos", Vector2.ZERO) as Vector2


func _enemy_alive(enemies: Array, eid: int) -> bool:
	var entry: Dictionary = _enemy_entry(enemies, eid)
	return (
		not entry.is_empty()
		and bool(entry.get("alive", false))
		and int(entry.get("team", -1)) != hero_team
	)


# ── Layer 5e-2: Miasma poison (Basilisk Breath) ──────────────
func _is_ranged_hero() -> bool:
	# Source reads `hero.is_melee_hero` and falls back to the `range >= 110`
	# rule when the attribute is missing (Hero.is_melee_hero is < 110).
	if hero_melee_flag >= 0:
		return hero_melee_flag == 0
	return hero_range >= 110.0


func _miasma_damage(target_max_hp: int, data: Dictionary) -> int:
	# Source: int(target.max_hp * pct), clamped to [6, cap_damage].
	var raw := int(float(target_max_hp) * float(data.get("max_hp_pct_per_tick", 0.0)))
	return maxi(6, mini(int(data.get("cap_damage", 9999)), raw))


func apply_miasma(target_id: int, target_alive: bool, target_max_hp: int, data: Dictionary) -> void:
	# Port of _apply_miasma. The source bails on a dead/absent target; a
	# re-apply keeps the strongest damage, the longest timer and the shortest
	# tick countdown.
	if not target_alive or data.is_empty():
		return
	var dmg := _miasma_damage(target_max_hp, data)
	var prev: Dictionary = miasma.get(target_id, {})
	if prev.is_empty():
		miasma[target_id] = {
			"source_id": hero_id,
			"source_team": hero_team,
			"source_pos": hero_position,
			"damage": dmg,
			"timer": int(data.get("duration", 0)),
			"tick_cd": int(data.get("tick", 0)),
		}
		return
	prev["source_id"] = hero_id
	prev["source_team"] = hero_team
	prev["source_pos"] = hero_position
	prev["damage"] = maxi(int(prev["damage"]), dmg)
	prev["timer"] = maxi(int(prev["timer"]), int(data.get("duration", 0)))
	prev["tick_cd"] = mini(int(prev["tick_cd"]), int(data.get("tick", 0)))


func tick_miasma(dt: int, enemies: Array, effects: ItemEffects) -> void:
	# Port of _tick_miasma: decrement every tracker, land the poison damage when
	# the tick countdown expires (the source resets it to a hardcoded 30), and
	# drop a tracker when its target dies or its timer runs out.
	if miasma.is_empty():
		return
	var expired: Array = []
	for key in miasma.keys():
		var tgt_id: int = int(key)
		var entry: Dictionary = _enemy_entry(enemies, tgt_id)
		if entry.is_empty() or not bool(entry.get("alive", false)):
			expired.append(tgt_id)
			continue
		var m: Dictionary = miasma[tgt_id]
		m["timer"] = int(m["timer"]) - dt
		m["tick_cd"] = int(m["tick_cd"]) - dt
		if int(m["tick_cd"]) <= 0:
			m["tick_cd"] = 30
			var dmg: int = int(m["damage"])
			var source_id: int = int(m.get("source_id", hero_id))
			var source_team: int = int(m.get("source_team", hero_team))
			var source_pos: Vector2 = m.get("source_pos", hero_position) as Vector2
			if dmg > 0:
				effects.deal_damage_from(source_id, source_team, source_pos, tgt_id, dmg, "magic")
			effects.notify(tgt_id, "POISON")
		if int(m["timer"]) <= 0:
			expired.append(tgt_id)
	for key in expired:
		miasma.erase(key)


# ── Layer 5e: on-hit procs (roll_crit / basic & ranged attack hits) ──


func roll_crit(_rng: RandomNumberGenerator) -> Array:
	# Source returns (is_crit, mult). Soul Rend crit (rend_target) is handled
	# by the caller before this roll per source _do_attack.
	var crit: Array = get_crit()
	var chance: float = float(crit[0])
	var mult: float = float(crit[1])
	if chance <= 0.0:
		return [false, 1.0]
	if _rng.randf() < chance:
		return [true, mult]
	return [false, 1.0]


func on_basic_attack_hit(
	target_id: int, damage: int, enemies: Array, rng: RandomNumberGenerator, effects: ItemEffects
) -> void:
	# Port of on_basic_attack_hit (melee): lifesteal + _on_hit_common + cleave.
	if not hero_alive:
		return
	var ls: float = get_lifesteal_pct()
	if ls > 0.0 and damage > 0:
		hero_hp = mini(float(hero_max_hp), hero_hp + float(damage) * ls)
	_on_hit_common(target_id, damage, enemies, rng, effects)
	var cleave: Variant = get_cleave()
	if cleave != null and damage > 0:
		var pct: float = float(cleave[0])
		var radius: float = float(cleave[1])
		var splash: int = int(float(damage) * pct)
		if splash > 0:
			effects.cleave_splash(target_id, hero_team, hero_position, splash, radius)


func on_ranged_attack_hit(
	target_id: int, damage: int, enemies: Array, rng: RandomNumberGenerator, effects: ItemEffects
) -> void:
	# Port of on_ranged_attack_hit: on-hit common only (no lifesteal/cleave).
	if not hero_alive:
		return
	_on_hit_common(target_id, damage, enemies, rng, effects)


func _on_hit_common(
	target_id: int, damage: int, enemies: Array, rng: RandomNumberGenerator, effects: ItemEffects
) -> void:
	# Corroder: armor shred.
	var shred: Variant = get_armor_shred()
	if shred != null:
		effects.apply_armor_shred(target_id, float(shred[0]), int(shred[1]))
	# Abyss Breaker: Bash.
	var bash: Variant = get_bash()
	if bash != null and bash_cd <= 0:
		var bash_dict: Dictionary = bash as Dictionary
		if rng.randf() < float(bash_dict.get("chance", 0.0)):
			bash_cd = int(bash_dict.get("cooldown", 0))
			effects.apply_stun(target_id, int(bash_dict.get("stun", 0)))
			effects.deal_damage_sourceless(
				target_id, hero_team, int(bash_dict.get("damage", 0)), "physical"
			)
			effects.notify(target_id, "BASH!")
	# Fenrir Chain / Thunder Coil: arc chain.
	var chain: Variant = get_on_attack_chain()
	if chain != null:
		var ch: Dictionary = chain as Dictionary
		if float(ch.get("chance", 0.0)) > 0.0 and rng.randf() < float(ch["chance"]):
			var hit: Array = effects.chain_targets(
				target_id, hero_team, float(ch["radius"]), int(ch["targets"])
			)
			if hit.is_empty():
				hit = [target_id]
			for tid in hit:
				# Layer 9g: source `u.take_damage(chain["damage"], h.team,
				# "magic")` (`hero_items.py:2568`) omits `source=`.
				effects.deal_damage_magic_sourceless(
					int(tid), hero_team, int(ch["damage"]), "magic"
				)
			effects.chain_fx(hero_id, hit)
	if target_id < 0:
		return
	# Sundering Cudgel: Piercing Bash.
	if has("sundering_cudgel") and pierce_bash_cd <= 0:
		var pb: Dictionary = item("sundering_cudgel").get("bash", {})
		if rng.randf() < float(pb.get("chance", 0.0)):
			pierce_bash_cd = int(pb.get("cooldown", 0))
			effects.apply_stun(target_id, int(pb.get("stun", 0)))
			# Layer 9g: `target.take_damage(b["damage"], h.team, "magic")`
			# (`hero_items.py:2589`), no `source=`.
			effects.deal_damage_magic_sourceless(
				target_id, hero_team, int(pb.get("damage", 0)), "magic"
			)
			effects.notify(target_id, "PIERCE!")
	# Frostbound Eye: Frostbite (slow + atk_slow + anti_heal).
	if has("frostbound_eye"):
		var oa: Dictionary = item("frostbound_eye").get("on_attack", {})
		effects.apply_slow(target_id, float(oa.get("slow", 0.0)), int(oa.get("duration", 0)))
		effects.apply_atk_slow(
			target_id, float(oa.get("atk_slow", 0.0)), int(oa.get("duration", 0))
		)
		effects.apply_anti_heal(
			target_id, float(oa.get("anti_heal", 0.0)), int(oa.get("duration", 0))
		)
	# Basilisk Breath: Miasma (% max HP poison) plus Polycephaly extra shots.
	if has("basilisk_breath"):
		var oa: Dictionary = item("basilisk_breath").get("on_attack", {})
		var entry: Dictionary = _enemy_entry(enemies, target_id)
		apply_miasma(target_id, bool(entry.get("alive", false)), int(entry.get("max_hp", 0)), oa)
		var ms: Dictionary = item("basilisk_breath").get("multishot", {})
		if (
			not ms.is_empty()
			and _is_ranged_hero()
			and not entry.is_empty()
			and rng.randf() < float(ms.get("chance", 0.0))
		):
			var center: Vector2 = entry.get("pos", Vector2.ZERO) as Vector2
			var extras: Array = _nearby_enemies_sorted_from(
				enemies, center, float(ms.get("radius", 0.0)), target_id, true
			)
			var count: int = mini(extras.size(), int(ms.get("targets", 0)))
			var splash: int = int(float(damage) * float(ms.get("damage_pct", 0.0)))
			var hit: Array = []
			for index in range(count):
				var eid: int = int(extras[index])
				if splash > 0:
					# Layer 9g: `u.take_damage(dmg, h.team, "magic")`
					# (`hero_items.py:2633`), no `source=`.
					effects.deal_damage_magic_sourceless(eid, hero_team, splash, "magic")
				apply_miasma(
					eid,
					_enemy_alive(enemies, eid),
					int(_enemy_entry(enemies, eid).get("max_hp", 0)),
					oa
				)
				hit.append(eid)
			if hit.size() > 0:
				effects.chain_fx(hero_id, hit)
	# Runic Gavel: Empower Strike.
	if has("runic_gavel") and empower_charge <= 0:
		var bonus: int = consume_empower_strike()
		if bonus > 0:
			# Layer 9g: `target.take_damage(bonus, h.team, "magic")`
			# (`hero_items.py:2648`), no `source=`.
			effects.deal_damage_magic_sourceless(target_id, hero_team, bonus, "magic")
			effects.notify(target_id, "EMPOWER!")
	# Vine Rod: Entangle (root = 100% slow).
	if has("vine_rod") and vine_cd <= 0:
		var vr: Dictionary = item("vine_rod").get("on_attack", {})
		vine_cd = int(vr.get("cooldown", 0))
		effects.apply_slow(target_id, 1.0, int(vr.get("root_duration", 0)))
		effects.notify(target_id, "ROOT!")


func _nearby_enemies(enemies: Array, radius: float) -> Array:
	var ids: Array = []
	for e in enemies:
		var d: Dictionary = e as Dictionary
		if not bool(d.get("alive", false)):
			continue
		if int(d.get("team", -1)) == hero_team:
			continue
		var epos: Vector2 = d.get("pos", Vector2.ZERO) as Vector2
		if hero_position.distance_to(epos) <= radius:
			ids.append(int(d.get("id", -1)))
	return ids


func _nearby_enemies_sorted(enemies: Array, radius: float) -> Array:
	return _nearby_enemies_sorted_from(enemies, hero_position, radius, -1)


func _nearby_enemies_sorted_from(
	enemies: Array, center: Vector2, radius: float, exclude_id: int, exact_distance: bool = false
) -> Array:
	# Source sorts nearby by distance ascending; tie-break by insertion order
	# (sort_custom is not stable). Polycephaly measures from the hit target.
	var entries: Array = []
	for index in range(enemies.size()):
		var d: Dictionary = enemies[index] as Dictionary
		if not bool(d.get("alive", false)):
			continue
		if int(d.get("team", -1)) == hero_team:
			continue
		if int(d.get("id", -2)) == exclude_id:
			continue
		var epos: Vector2 = d.get("pos", Vector2.ZERO) as Vector2
		var dist := center.distance_to(epos)
		if dist <= radius:
			entries.append({"id": int(d.get("id", -1)), "dist": dist, "idx": index})
	# Python sort is stable: we approximate with (dist, idx) tuple key.
	entries.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			# Layer 9a: Polycephaly uses exact distance, stable only for real ties.
			if (
				(exact_distance and float(a.dist) != float(b.dist))
				or absf(float(a.dist) - float(b.dist)) > 0.001
			):
				return float(a.dist) < float(b.dist)
			return int(a.idx) < int(b.idx)
	)
	var ids: Array = []
	for entry in entries:
		ids.append(int(entry.id))
	return ids
