extends "res://scripts/combat/unit_state.gd"
## Layer 9ae probe: no live item grants the 0.60 slow-resist cap (Abyss Breaker is
## 0.30), so the cap row of `item_slow_resist_source.json` runs the production
## `UnitState.apply_slow` against the resist the source cap would report.

var resist := 0.0


func slow_resist() -> float:
	return resist
