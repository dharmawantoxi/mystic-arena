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

const STARTER_DAMAGE_MULT := 1.5
## Shared S1 reason prefix: metric moved + target, per the entry contract.
const S1_REASON := "S1 starter catch-up 2026-10-16: starter gap 5.67x -> 3.97x (target <= 4.0x)"

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


## Doctrine helper: every entry must carry a non-empty reason. The layer
## suite runs this over the live table.
static func entries_without_reason() -> Array:
	var missing: Array = []
	for hero_id in HERO_OVERRIDES:
		var entry: Dictionary = HERO_OVERRIDES[hero_id]
		var reason = entry.get("reason", "")
		if typeof(reason) != TYPE_STRING or String(reason).is_empty():
			missing.append(String(hero_id))
	missing.sort()
	return missing
