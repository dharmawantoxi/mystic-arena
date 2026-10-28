extends RefCounted
## Layer 9bl: the tower clocks the source keeps on `Tower` (`shoot_flash_timer`) and the
## castle's flame flicker, rebuilt on the view side from what the simulation exposes.
## Read-only: it never writes to a structure.

const StructureState = preload("res://scripts/combat/structure_state.gd")
## `_shoot_archer` / `_shoot_ice` / `_shoot_mage` set 8, `_shoot_cannon` sets 10.
const FLASH_TICKS := 8
const CANNON_FLASH_TICKS := 10
const FLICKER_STEPS := 5
## Layer 9bv14: `Tower.upgrade` / `activate_regen_shield` set `upgrade_flash = 30`.
const UPGRADE_FLASH_TICKS := 30
var _entries: Dictionary = {}


static func flash_ticks(tower_path: String) -> int:
	return CANNON_FLASH_TICKS if tower_path == "cannon" else FLASH_TICKS


## `Tower._draw_tower_body`: `shoot_b = shoot_flash_timer // 3`.
static func shoot_b(flash: int) -> int:
	return floori(float(flash) / 3.0)


## `_draw_gate_torch`: `flicker = int((timer * 0.4 + offset) % 5)`; both torches share it.
static func flicker(tick: int) -> int:
	return int(float(tick) * 0.4) % FLICKER_STEPS


## Advance this structure's clocks to `tick`; returns `{flash}` in ticks.
func observe(structure: StructureState, tick: int) -> Dictionary:
	var data := structure.settings()
	var level := int(data.level)
	var regen := bool(structure.regen_shield_active)
	var entry: Dictionary = _entries.get(structure.id, {})
	if entry.is_empty():
		entry = {"tick": tick, "flash": 0, "upgrade_flash": 0, "level": level, "regen": regen}
	else:
		var elapsed := maxi(0, tick - int(entry["tick"]))
		entry["flash"] = maxi(0, int(entry["flash"]) - elapsed)
		entry["upgrade_flash"] = maxi(0, int(entry["upgrade_flash"]) - elapsed)
		# The source starts the flash when the shot is fired, i.e. the cooldown is set.
		if structure.cooldown_ticks > int(entry["cooldown"]):
			entry["flash"] = flash_ticks(data.tower_path)
		# `Tower.upgrade` and `activate_regen_shield` both re-arm the 30-tick upgrade flash.
		if level > int(entry["level"]) or (regen and not bool(entry["regen"])):
			entry["upgrade_flash"] = UPGRADE_FLASH_TICKS
		entry["level"] = level
		entry["regen"] = regen
		entry["tick"] = tick
	entry["cooldown"] = structure.cooldown_ticks
	_entries[structure.id] = entry
	return entry


func prune(structures: Array) -> void:
	if _entries.size() <= structures.size():
		return
	var live := {}
	for structure in structures:
		live[structure.id] = true
	for id in _entries.keys():
		if not live.has(id):
			_entries.erase(id)


func tracked() -> int:
	return _entries.size()
