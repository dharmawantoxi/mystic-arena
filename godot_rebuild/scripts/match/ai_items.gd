extends RefCounted
## AIPlayer item purchase adapter, port of AIPlayer._try_buy_item.
## Candidates are ALIVE AI-owned red heroes with a free slot, ordered by
## (kills, level) descending with a stable roster tie-break; the suggestion comes from
## hero_items and the price from the catalog metadata; the debit runs through
## the real match ledger with the live draft reserve.
## The source increments no counter here, so this adapter keeps none either.
## Scheduling stays with the AI controller; this adapter only selects and buys.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const HeroItems = preload("res://scripts/match/hero_items.gd")

var items := HeroItems.new()


func candidates(world: World) -> Array[int]:
	# Source filter: alive, has an inventory, used slots < MAX_ITEM_SLOTS.
	var rows: Array = []
	for unit in world._ai_roster():
		var hero := unit as World.HeroState
		if not hero.alive or hero.items.used_slots() >= hero.items.max_slots():
			continue
		rows.append({"id": hero.id, "kills": hero.kills, "level": hero.level, "seq": rows.size()})
	# Python sorts the tuple key (kills, level) reverse=True and stays stable.
	rows.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			if int(a["kills"]) != int(b["kills"]):
				return int(a["kills"]) > int(b["kills"])
			if int(a["level"]) != int(b["level"]):
				return int(a["level"]) > int(b["level"])
			return int(a["seq"]) < int(b["seq"])
	)
	var ids: Array[int] = []
	for row in rows:
		ids.append(int(row["id"]))
	return ids


func suggestion(world: World, entity_id: int) -> String:
	var hero := world.get_unit(entity_id) as World.HeroState
	if hero == null:
		return ""
	return items.suggest_item_for_hero(hero.settings().role, hero.attack_range, hero.items.owned())


func try_buy(world: World, draft: Draft, entity_id: int) -> bool:
	var item_id := suggestion(world, entity_id)
	if item_id == "":
		return false
	return world._buy_item_for(world.RED, entity_id, item_id, draft.reserve())


func try_buy_priority(world: World, draft: Draft) -> bool:
	# Source keeps scanning the next candidate while this one cannot pay.
	for entity_id in candidates(world):
		if try_buy(world, draft, entity_id):
			return true
	return false
