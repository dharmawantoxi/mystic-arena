extends RefCounted
## Draft-to-world adapter. Only registered playable kits may be purchased.
## Deliberately does NOT substitute Kaizen for an unavailable hero kit.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")


func try_buy(world: World, draft: Draft) -> bool:
	if world == null or draft == null or not world.is_running():
		return false
	var owned: Array = []
	for unit in world._ai_roster():
		# Includes dead AI-owned heroes, but never a stale/non-authoritative receipt.
		if world.get_unit(unit.id) != unit or unit.definition == null:
			return false
		owned.append(unit.definition.id)
	return draft.try_buy(owned, world.economy.gold[world.RED], world._buy_ai_hero)
