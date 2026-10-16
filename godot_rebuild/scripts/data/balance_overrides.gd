extends RefCounted
## Layer 9c: the ONLY native surface where deliberate rebalance deviations
## from the source-parity hero catalog may live (doctrine: BALANCE_CONTRACT.md,
## measured baseline: layer 9b, fixture `balance_baseline_ingame.json`).
##
## The production table is EMPTY BY DECISION: the project's own ingame audit
## (`tools/balance_audit.py --ingame`) reports zero violations on every
## tool-enforced target (corr 0.535 <= 0.80, identity spread 1.64x >= 1.20,
## school ratio 1.000/1.001 inside 0.90..1.15, boss pref 1.49 >= 1.20, price
## spread 1.89x <= 2.20, pool power delta 1.000/1.000 within 0.12). The
## prose-band deviations (MAGIC|CARRY and MAGIC|FIGHTER power 0.84, one tick
## under the 0.85 prose floor; PHYSICAL|TANK 1.38 over the 1.25 prose cap)
## are the accepted trade of the source 2026-08-30 balance pass, whose own
## stated result is the 1.6x identity spread. Moving pooled numbers without a
## playtest directive would be opinion, not measurement - so this layer ships
## as tested, documented machinery that a future directive lands in.
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

const HERO_OVERRIDES: Dictionary = {}


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
## suite runs this over the live table (trivially true while empty).
static func entries_without_reason() -> Array:
	var missing: Array = []
	for hero_id in HERO_OVERRIDES:
		var entry: Dictionary = HERO_OVERRIDES[hero_id]
		var reason = entry.get("reason", "")
		if typeof(reason) != TYPE_STRING or String(reason).is_empty():
			missing.append(String(hero_id))
	missing.sort()
	return missing
