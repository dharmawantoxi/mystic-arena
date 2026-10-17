extends RefCounted
## Layer 9c: the ONLY native surface where deliberate rebalance deviations
## from the source-parity hero catalog may live (doctrine: BALANCE_CONTRACT.md,
## measured baseline: layer 9b, fixture `balance_baseline_ingame.json`).
##
## Measured baseline (layer 9b, `tools/balance_audit.py --ingame`): zero
## violations on every tool-enforced target (corr 0.535 <= 0.80, identity
## spread 1.64x >= 1.20, school ratio 1.000/1.001 inside 0.90..1.15, boss pref
## 1.49 >= 1.20, price spread 1.89x <= 2.20, pool power delta 1.000/1.000
## within 0.12). The entries below are the explicit user directives of
## 2026-10-16 on top of that baseline (see "Rebalance terarah" in
## BALANCE_CONTRACT.md); the source fixture is NOT regenerated because these
## overrides are native-only and the source audit cannot see them.
##
## S1 STARTER CATCH-UP (2026-10-16): the audit's starter-gap formula is
## dps = base_damage * 60 / attack_cooldown + skill_base * 60 / skill_cd, so a
## damage multiplier moves only the auto-attack share. Measured: unlock avg
## dps 486.1 vs starter avg 85.7 (gap 5.67x). Smallest round multiplier that
## reaches the <= 4.0x target over the six real starter kits (1.45 -> 4.12x,
## 1.49 -> 4.00x edge, 1.5 -> 3.97x) is 1.5: starter avg 122.5, gap 3.97x.
## Resulting production base_damage: kaizen 45 -> 68, thorne 41 -> 62,
## grimjaw 42 -> 63, sylara 57 -> 86, vex 43 -> 65, zephyr 34 -> 51
## (hp untouched; the lab spawn keeps the .tres values).
##
## S2 PHYSICAL|TANK NERF (2026-10-16): the audit's identity-grid power is
## 0.8 * avg_dps/median_dps + 0.2 * avg_ehp/median_ehp over the 216 boss
## heroes; the PHYSICAL|TANK cell (n=39) sat at 1.38, over the 1.25 prose cap.
## Re-running the audit math over the audit rows with a uniform multiplier on
## the cell (damage -> auto-attack share only, hp -> ehp linear) gives:
## damage_mult 0.90 -> 1.29, 0.86 -> 1.26, 0.85 -> 1.25; hp_mult alone needs
## 0.5 (corr collapses to -0.03) and mixes are not smaller. Chosen: the
## smallest uniform damage_mult that reaches the cap, 0.85 (cell avg dps
## 646.2 -> 571.0, ehp 3069 untouched). No new violations: identity spread
## 1.64x -> 1.47x (>= 1.20), corr 0.535 -> 0.484 (<= 0.80), school ratio
## mini/true 1.000/1.001 -> 1.045/1.094 (0.90..1.15), price spread 1.89x ->
## 1.85x (<= 2.20), pool dps delta 0.972 (within 0.12); the other cells stay
## within 0.01 of baseline.
##
## S3 TROLL REGEN, PRODUCTION ONLY (2026-10-16): the source Troll regen is
## 0.6 HP/tick (36 HP/s, COMBAT_CONTRACT.md) - above the 13-damage Orc's
## 13/60 ~ 0.217 dps-per-tick, so a Troll/Orc duel can never finish. The
## production wave path (`prototype_battle._spawn_match_minion`) swaps in a
## DUPLICATED definition with regen 0.15/tick (< 0.217, duels resolve; the
## nexus-tier scale still multiplies on top). The .tres and the combat lab
## (`minion_battle.spawn_unit` direct) stay at the 0.6 source parity.
##
## Entry contract (per hero id; every entry is pinned by
## `balance_override_layer_checks.gd`):
##   "damage_mult": float, default 1.0 - multiplies HeroState.base_damage
##   "hp_mult":     float, default 1.0 - multiplies HeroState.base_hp
##   "reason":      String, REQUIRED  - the metric moved + the rationale
## Adding an entry requires regenerating the 9b baseline fixture through
## `balance_baseline_source_oracle.py` semantics (before/after numbers in
## PETA) - never edit the fixture by hand.
##
## The combat lab (`minion_battle.gd::spawn_hero`) stays on the direct
## source-parity path; only production spawns route through
## `prototype_battle._spawn_production_hero`, which applies this table.

const MinionDefinition = preload("res://scripts/data/minion_definition.gd")

const STARTER_DAMAGE_MULT := 1.5
## Shared S1 reason prefix: metric moved + target, per the entry contract.
const S1_REASON := "S1 starter catch-up 2026-10-16: starter gap 5.67x -> 3.97x (target <= 4.0x)"

const PHYSICAL_TANK_DAMAGE_MULT := 0.85
## Shared S2 reason prefix: metric moved + cap, per the entry contract.
const S2_REASON := "S2 PHYSICAL|TANK nerf 2026-10-16: cell power 1.38 -> 1.25 (prose cap 1.25)"

const HERO_OVERRIDES: Dictionary = {
	"kaizen":
	{
		"damage_mult": STARTER_DAMAGE_MULT,
		"reason": S1_REASON + "; auto-attack damage 45 -> 68, hp untouched",
	},
	"thorne":
	{
		"damage_mult": STARTER_DAMAGE_MULT,
		"reason": S1_REASON + "; auto-attack damage 41 -> 62, hp untouched",
	},
	"grimjaw":
	{
		"damage_mult": STARTER_DAMAGE_MULT,
		"reason": S1_REASON + "; auto-attack damage 42 -> 63, hp untouched",
	},
	"sylara":
	{
		"damage_mult": STARTER_DAMAGE_MULT,
		"reason": S1_REASON + "; auto-attack damage 57 -> 86, hp untouched",
	},
	"vex":
	{
		"damage_mult": STARTER_DAMAGE_MULT,
		"reason": S1_REASON + "; auto-attack damage 43 -> 65, hp untouched",
	},
	"zephyr":
	{
		"damage_mult": STARTER_DAMAGE_MULT,
		"reason": S1_REASON + "; auto-attack damage 34 -> 51, hp untouched",
	},
	"akaroth":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 320 -> 272, hp untouched",
	},
	"akirakumo":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 480 -> 408, hp untouched",
	},
	"akiraze":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 316 -> 269, hp untouched",
	},
	"aurelian":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 370 -> 315, hp untouched",
	},
	"azkharion":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 280 -> 238, hp untouched",
	},
	"broggmar":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 329 -> 280, hp untouched",
	},
	"brumhar":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 320 -> 272, hp untouched",
	},
	"cogsworth":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 451 -> 383, hp untouched",
	},
	"deidara":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 422 -> 359, hp untouched",
	},
	"garumenshi":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 374 -> 318, hp untouched",
	},
	"grimkor":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 384 -> 326, hp untouched",
	},
	"hitokage":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 384 -> 326, hp untouched",
	},
	"hollowbane":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 518 -> 440, hp untouched",
	},
	"kaelthys":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 361 -> 307, hp untouched",
	},
	"kaerinya":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 336 -> 286, hp untouched",
	},
	"kaerissa":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 266 -> 226, hp untouched",
	},
	"kagetsuka":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 412 -> 350, hp untouched",
	},
	"kairenji":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 348 -> 296, hp untouched",
	},
	"kaithros":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 490 -> 417, hp untouched",
	},
	"kaoruken":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 365 -> 310, hp untouched",
	},
	"karzhul":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 352 -> 299, hp untouched",
	},
	"korokai":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 329 -> 280, hp untouched",
	},
	"kyrenzai":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 355 -> 302, hp untouched",
	},
	"morvath":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 374 -> 318, hp untouched",
	},
	"obanai":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 384 -> 326, hp untouched",
	},
	"sasori":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 388 -> 330, hp untouched",
	},
	"solareth":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 221 -> 188, hp untouched",
	},
	"thoraz":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 378 -> 321, hp untouched",
	},
	"thorgaruk":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 271 -> 230, hp untouched",
	},
	"urgharun":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 293 -> 249, hp untouched",
	},
	"vaelmyrra":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 235 -> 200, hp untouched",
	},
	"vardrok":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 312 -> 265, hp untouched",
	},
	"verdanix":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 320 -> 272, hp untouched",
	},
	"vorthakul":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 293 -> 249, hp untouched",
	},
	"xareth":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 293 -> 249, hp untouched",
	},
	"yomigetsu":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 470 -> 400, hp untouched",
	},
	"zhaeris":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 338 -> 287, hp untouched",
	},
	"zhyrakaan":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 261 -> 222, hp untouched",
	},
	"zhyvrek":
	{
		"damage_mult": PHYSICAL_TANK_DAMAGE_MULT,
		"reason": S2_REASON + "; auto-attack damage 271 -> 230, hp untouched",
	},
}

## Minion surface (per minion definition id): "regen_per_tick" float plus the
## REQUIRED "reason". Applied only by the production wave spawn.
const MINION_OVERRIDES: Dictionary = {
	"troll":
	{
		"regen_per_tick": 0.15,
		"reason":
		(
			"S3 troll regen 2026-10-16: production waves 0.6 -> 0.15 HP/tick "
			+ "(< orc dps 13/60 ~ 0.217 so duels resolve); lab/.tres stay 0.6"
		),
	},
}


## Pure entry reader (unit-testable with synthetic entries): returns the
## requested multiplier, falling back to 1.0 for missing or non-finite data.
static func multiplier_from(entry: Dictionary, key: String) -> float:
	var value = entry.get(key, 1.0)
	if typeof(value) != TYPE_FLOAT and typeof(value) != TYPE_INT:
		return 1.0
	var result := float(value)
	if not is_finite(result) or result <= 0.0:
		return 1.0
	return result


static func damage_multiplier(hero_id: String) -> float:
	return multiplier_from(HERO_OVERRIDES.get(hero_id, {}), "damage_mult")


static func hp_multiplier(hero_id: String) -> float:
	return multiplier_from(HERO_OVERRIDES.get(hero_id, {}), "hp_mult")


## Production minion definition: returns the SAME resource when no entry
## exists, otherwise a DUPLICATE with the overridden fields - the preloaded
## .tres / lab definition is never mutated (scaled_minion_definition pattern).
static func minion_definition_for(definition: MinionDefinition) -> MinionDefinition:
	if definition == null:
		return definition
	var entry: Dictionary = MINION_OVERRIDES.get(definition.id, {})
	if entry.is_empty():
		return definition
	var copy := definition.duplicate() as MinionDefinition
	var regen = entry.get("regen_per_tick", null)
	if (typeof(regen) == TYPE_FLOAT or typeof(regen) == TYPE_INT) and is_finite(float(regen)):
		copy.regen_per_tick = maxf(0.0, float(regen))
	return copy


## Doctrine helper: every entry must carry a non-empty reason. The layer
## suite runs this over the live table.
static func entries_without_reason() -> Array:
	var missing: Array = []
	for table in [HERO_OVERRIDES, MINION_OVERRIDES]:
		for entry_id in table:
			var entry: Dictionary = table[entry_id]
			var reason = entry.get("reason", "")
			if typeof(reason) != TYPE_STRING or String(reason).is_empty():
				missing.append(String(entry_id))
	missing.sort()
	return missing
