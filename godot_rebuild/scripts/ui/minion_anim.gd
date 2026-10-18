extends RefCounted
## Layer 9bk: the animation clocks the source keeps on `Minion` (`anim_time`,
## `walk_cycle`, `is_moving`, `attack_anim_timer`, `hurt_flash_timer`), rebuilt on the
## view side from what the simulation already exposes. Read-only: it never writes to a
## unit, so disabling the view cannot change a result.

const UnitState = preload("res://scripts/combat/unit_state.gd")
const ATTACK_ANIM_MAX := 24
const HURT_FLASH_TICKS := 8
const WALK_STEP := 0.25
const MOVE_EPSILON := 0.1
const WALK_POSES := 8
const IDLE_POSES := 4
var _entries: Dictionary = {}


## `minions/_bundle.py::_minion_cache_key` pose part, as an atlas pose name: attack
## `atk // 2`, else walking `int(2 * walk_cycle) % 8`, else idle `int(0.05 * t) % 4`.
static func pose_key(attack: int, moving: bool, walk_cycle: float, anim_time: int) -> String:
	if attack > 0:
		return "atk%d" % (attack >> 1)
	if moving:
		return "walk%d" % (int(walk_cycle * 2.0) % WALK_POSES)
	return "idle%d" % (int(float(anim_time) * 0.05) % IDLE_POSES)


## Advance this unit's clocks to `tick` and return them:
## `{attack, moving, walk, anim, hurt}` (ticks, bool, cycles, ticks, ticks).
func observe(unit: UnitState, tick: int) -> Dictionary:
	var entry: Dictionary = _entries.get(unit.id, {})
	if entry.is_empty():
		entry = {"tick": tick, "attack": 0, "moving": false, "walk": 0.0, "anim": 0, "hurt": 0}
	else:
		_advance(entry, unit, tick)
	entry["pos"] = unit.position
	entry["hp"] = unit.hp
	entry["cooldown"] = unit.cooldown_ticks
	_entries[unit.id] = entry
	return entry


func _advance(entry: Dictionary, unit: UnitState, tick: int) -> void:
	var elapsed := maxi(0, tick - int(entry["tick"]))
	if elapsed == 0:
		return
	var travelled := unit.position.distance_to(entry["pos"] as Vector2)
	var moving := travelled / float(elapsed) > MOVE_EPSILON
	entry["moving"] = moving
	if moving:
		entry["walk"] = float(entry["walk"]) + WALK_STEP * float(elapsed)
	entry["anim"] = int(entry["anim"]) + elapsed
	entry["attack"] = maxi(0, int(entry["attack"]) - elapsed)
	entry["hurt"] = maxi(0, int(entry["hurt"]) - elapsed)
	# The source starts the swing when the attack lands, i.e. when the cooldown is set.
	if unit.cooldown_ticks > int(entry["cooldown"]):
		entry["attack"] = ATTACK_ANIM_MAX
	if unit.hp < float(entry["hp"]):
		entry["hurt"] = HURT_FLASH_TICKS
	entry["tick"] = tick


## Forget units that left the field so the table cannot grow without bound.
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
