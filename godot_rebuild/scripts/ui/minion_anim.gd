extends RefCounted
## Layer 9bk: the animation clocks the source keeps on `Minion` (`anim_time`,
## `walk_cycle`, `is_moving`, `attack_anim_timer`, `hurt_flash_timer`), rebuilt on the
## view side from what the simulation already exposes. Read-only: it never writes to a
## unit, so disabling the view cannot change a result.

const UnitState = preload("res://scripts/combat/unit_state.gd")
const ATTACK_ANIM_MAX := 24
const HURT_FLASH_TICKS := 8
const SLASH_LIFE := 12
const DEATH_LIFE := 20
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
## Attack/move clocks plus `slash_life` and `slash_angle` for source minion effects.
func observe(unit: UnitState, tick: int, target_position: Vector2 = Vector2.INF) -> Dictionary:
	var entry: Dictionary = _entries.get(unit.id, {})
	if entry.is_empty():
		var type_id := "goblin"
		var radius := 9.0
		if unit.definition != null:
			type_id = unit.definition.id
			radius = float(unit.definition.radius_px)
		entry = {
			"tick": tick,
			"attack": 0,
			"moving": false,
			"walk": 0.0,
			"anim": 0,
			"hurt": 0,
			"slash_life": 0,
			"slash_angle": 0.0,
			"target_pos": Vector2.INF,
			"target_id": unit.target_id,
			"type": type_id,
			"radius": radius,
			"team": unit.team,
			"level": unit.nexus_level,
		}
	else:
		_advance(entry, unit, tick, target_position)
	if target_position.is_finite():
		entry["target_pos"] = target_position
	entry["target_id"] = unit.target_id
	entry["pos"] = unit.position
	entry["hp"] = unit.hp
	entry["cooldown"] = unit.cooldown_ticks
	_entries[unit.id] = entry
	return entry


func _advance(entry: Dictionary, unit: UnitState, tick: int, target_position: Vector2) -> void:
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
	entry["slash_life"] = maxi(0, int(entry["slash_life"]) - elapsed)
	if unit.target_id >= 0 and unit.target_id != int(entry["target_id"]):
		entry["target_pos"] = Vector2.INF
	# The source starts the slash with the same cooldown transition as its attack.
	if unit.cooldown_ticks > int(entry["cooldown"]):
		entry["attack"] = ATTACK_ANIM_MAX
		entry["slash_life"] = SLASH_LIFE
		var aim: Vector2 = target_position
		if not aim.is_finite():
			aim = entry["target_pos"] as Vector2
		if aim.is_finite() and aim.distance_squared_to(unit.position) > 0.0001:
			entry["slash_angle"] = (aim - unit.position).angle()
		else:
			entry["slash_angle"] = PI if unit.facing < 0.0 else 0.0
	if unit.hp < float(entry["hp"]):
		entry["hurt"] = HURT_FLASH_TICKS
	entry["tick"] = tick


## Capture source-like death snapshots before the simulation retires dead minions. Hit
## events carry the exact target position, which is more current than the last draw.
func take_death_snapshots(events: Array) -> Array[Dictionary]:
	var hit_positions: Dictionary = {}
	for raw_event in events:
		if not (raw_event is Dictionary):
			continue
		var hit_event: Dictionary = raw_event
		if (
			String(hit_event.get("kind", "")) == "hit"
			and typeof(hit_event.get("to")) == TYPE_VECTOR2
		):
			hit_positions[int(hit_event.get("target_id", -1))] = hit_event["to"]
	var snapshots: Array[Dictionary] = []
	for raw_event in events:
		if not (raw_event is Dictionary):
			continue
		var death_event: Dictionary = raw_event
		if String(death_event.get("kind", "")) != "death":
			continue
		var id := int(death_event.get("target_id", -1))
		if not _entries.has(id):
			continue
		var entry: Dictionary = _entries[id]
		var point: Vector2 = entry["pos"] as Vector2
		if hit_positions.has(id):
			point = hit_positions[id] as Vector2
		(
			snapshots
			. append(
				{
					"id": id,
					"type": String(entry["type"]),
					"position": point,
					"life": DEATH_LIFE,
				}
			)
		)
		_entries.erase(id)
	return snapshots


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
