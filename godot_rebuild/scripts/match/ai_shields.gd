extends RefCounted
## AIPlayer shield actions per candidate; no RNG roll or upgrade-counter increment.
## Kill-priority ordering and scene scheduling belong to the pending AI controller.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")


func try_regen(world: World, draft: Draft, entity_id: int) -> bool:
	return world._activate_regen_shield_for(world.RED, entity_id, draft.reserve())


func try_castle(world: World, draft: Draft, entity_id: int) -> bool:
	return world._activate_castle_shield_for(world.RED, entity_id, draft.reserve())
