extends RefCounted
## AIPlayer shield actions per candidate; no RNG roll or upgrade-counter increment.
## Regen candidates follow the source kills-descending stable order; scene
## scheduling still belongs to the pending AI controller.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Upgrades = preload("res://scripts/match/ai_upgrades.gd")


func try_regen(world: World, draft: Draft, entity_id: int) -> bool:
	return world._activate_regen_shield_for(world.RED, entity_id, draft.reserve())


func try_castle(world: World, draft: Draft, entity_id: int) -> bool:
	return world._activate_castle_shield_for(world.RED, entity_id, draft.reserve())


func regen_candidates(world: World) -> Array[int]:
	# Source uses every ALIVE own tower (max level included), keeps only the
	# ones eligible for a regen shield, then sorts by kills descending.
	var rows: Array = []
	for structure in world.structures:
		var tower := world._owned_tower(structure.id, world.RED)
		if tower == null or not tower.can_activate_regen_shield():
			continue
		rows.append({"id": tower.id, "kills": tower.kills, "seq": rows.size()})
	return Upgrades._stable_kills_descending(rows)


func try_regen_priority(world: World, draft: Draft) -> bool:
	for entity_id in regen_candidates(world):
		if try_regen(world, draft, entity_id):
			return true
	return false
