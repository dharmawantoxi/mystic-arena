extends RefCounted
## AIPlayer._try_build_tower only. Scheduler's 150 G gate belongs to ai_policy.gd.
## No scene calls this adapter until the full AIPlayer controller is ready.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const COST := 100
const TYPES := ["archer", "cannon", "ice", "mage"]
const WEIGHTS := [0.35, 0.25, 0.20, 0.20]

var total_built := 0
var rng := RandomNumberGenerator.new()
# Injectable synchronous pickers for testing boundaries and RNG consumption.
var slot_picker: Callable = _pick_slot
var type_picker: Callable = _pick_type


func try_build(world: World, draft: Draft) -> bool:
	if world == null or draft == null or not world.is_running():
		return false
	var available: Array[int] = []
	for slot in world.slots:
		if (
			slot != null
			and slot.team == world.RED
			and slot.id >= 0
			and world.get_slot(slot.id) == slot
			and slot.structure_id == -1
			and slot.lane in [0, 1, 2]
			and slot.position.is_finite()
		):
			available.append(slot.id)
	if available.is_empty() or world.economy.gold[world.RED] < COST + draft.reserve():
		return false
	var slot_id: int = slot_picker.call(available)
	if slot_id not in available:
		return false
	var path: String = type_picker.call(TYPES, WEIGHTS)
	if path not in TYPES:
		return false
	if not world._build_tower_for(world.RED, slot_id, path, draft.reserve()):
		return false
	total_built += 1
	return true


func _pick_slot(available: Array[int]) -> int:
	return available[rng.randi_range(0, available.size() - 1)]


func _pick_type(_types: Array, _weights: Array) -> String:
	return weighted_at(rng.randf())


static func weighted_at(roll: float) -> String:
	var boundary := 0.0
	for index in range(TYPES.size()):
		boundary += float(WEIGHTS[index])
		if roll < boundary:
			return TYPES[index]
	return TYPES.back()
