extends RefCounted
## Layer 9bo: the clocks the source keeps on `Hero` for its sprite cache, rebuilt on the view
## side: `pulse` (+0.1 per tick) and "moving" (`_detect_moving`: |dx| + |dy| > 0.3 per tick).
## The attack timer is the simulation's own `HeroState.attack_timer`. Read-only.

const HeroState = preload("res://scripts/combat/hero_state.gd")
const PULSE_STEP := 0.1
const MOVE_EPSILON := 0.3
const PHASES := 8
const ATK_QUANT := 3
const SKILL_QUANT := 2
var _entries: Dictionary = {}


## `heroes/__init__.py::_hero_cache_key` pose part as an atlas pose name: an active
## skill wins, then attacking `timer // 3`, else `int(pulse * 2) % 8` walk or idle.
static func pose_key(
	attack_timer: int,
	moving: bool,
	pulse: float,
	active_skill: String = "",
	active_skill_timer: int = 0
) -> String:
	if not active_skill.is_empty():
		return (
			"skill_%s_%d" % [active_skill, floori(float(active_skill_timer) / float(SKILL_QUANT))]
		)
	if attack_timer > 0:
		return "atk%d" % floori(float(attack_timer) / float(ATK_QUANT))
	return "%s%d" % ["walk" if moving else "idle", int(pulse * 2.0) % PHASES]


## Advance this hero's clocks to `tick`; returns `{pulse, moving}`.
func observe(hero: HeroState, tick: int) -> Dictionary:
	var entry: Dictionary = _entries.get(hero.id, {})
	if entry.is_empty():
		entry = {"tick": tick, "pulse": 0.0, "moving": false}
	else:
		var elapsed := maxi(0, tick - int(entry["tick"]))
		if elapsed > 0:
			var last: Vector2 = entry["pos"]
			var delta := absf(hero.position.x - last.x) + absf(hero.position.y - last.y)
			entry["moving"] = delta > MOVE_EPSILON * float(elapsed)
			entry["pulse"] = float(entry["pulse"]) + PULSE_STEP * float(elapsed)
			entry["tick"] = tick
	entry["pos"] = hero.position
	_entries[hero.id] = entry
	return entry


func prune(units: Array) -> void:
	if _entries.size() <= units.size():
		return
	var live := {}
	for unit in units:
		live[unit.id] = true
	for id in _entries.keys():
		if not live.has(id):
			_entries.erase(id)


func tracked() -> int:
	return _entries.size()
