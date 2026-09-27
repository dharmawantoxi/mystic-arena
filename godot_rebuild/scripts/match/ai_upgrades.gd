extends RefCounted
## Per-candidate AIPlayer upgrades against the real match domain and ledger.
## Candidate ordering/kill-priority and automatic scene scheduling remain pending.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const PREFERRED_PATHS := ["cannon", "ice", "archer", "mage"]

var total_upgraded := 0
var total_nexus_upgrades := 0
var total_hero_upgrades := 0


func try_tower(world: World, draft: Draft, entity_id: int) -> bool:
	var tower := world._owned_tower(entity_id, world.RED)
	if tower == null:
		return false
	var current := tower.settings().level
	var paths: Array = PREFERRED_PATHS if current == 1 else [tower.settings().tower_path]
	for path in paths:
		if world._upgrade_tower_for(world.RED, entity_id, current, path, draft.reserve()):
			total_upgraded += 1
			return true
	return false


func try_nexus(world: World, draft: Draft, entity_id: int) -> bool:
	var nexus := world._owned_nexus(entity_id, world.RED)
	if nexus == null:
		return false
	if not world._upgrade_nexus_for(world.RED, entity_id, nexus.settings().level, draft.reserve()):
		return false
	total_nexus_upgrades += 1
	return true


func try_hero(world: World, draft: Draft, entity_id: int) -> bool:
	var hero := world.get_unit(entity_id) as World.HeroState
	if hero == null or hero.team != world.RED:
		return false
	# Source _try_upgrade_hero does not exclude dead/respawning owned heroes.
	if not world._upgrade_hero_for(world.RED, entity_id, hero.level, draft.reserve()):
		return false
	total_hero_upgrades += 1
	return true
