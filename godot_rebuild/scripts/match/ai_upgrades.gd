extends RefCounted
## Per-candidate AIPlayer upgrades against the real match domain and ledger.
## Candidate ordering is the source kills-descending stable order; automatic
## scene scheduling remains pending.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const PREFERRED_PATHS := ["cannon", "ice", "archer", "mage"]
const TOWER_MAX_LEVEL := 6
const MAX_HERO_LEVEL := 15

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


func tower_candidates(world: World) -> Array[int]:
	# Source _ai_step my_towers: own alive towers that can still upgrade, in
	# world order, then _try_upgrade_tower_new sorts by kills descending.
	var rows: Array = []
	for structure in world.structures:
		var tower := world._owned_tower(structure.id, world.RED)
		if tower == null or tower.settings().level >= TOWER_MAX_LEVEL:
			continue
		rows.append({"id": tower.id, "kills": tower.kills, "seq": rows.size()})
	return _stable_kills_descending(rows)


func hero_candidates(world: World) -> Array[int]:
	# Source _try_upgrade_hero: own heroes below max level, dead ones included,
	# in roster order, sorted by kills descending (Python sort is stable).
	var rows: Array = []
	for unit in world.units:
		if not unit.is_hero or unit.team != world.RED:
			continue
		var hero := unit as World.HeroState
		if hero.level >= MAX_HERO_LEVEL:
			continue
		rows.append({"id": hero.id, "kills": hero.kills, "seq": rows.size()})
	return _stable_kills_descending(rows)


func try_tower_priority(world: World, draft: Draft) -> bool:
	# Source keeps scanning the next candidate when this one is unaffordable.
	for entity_id in tower_candidates(world):
		if try_tower(world, draft, entity_id):
			return true
	return false


func try_hero_priority(world: World, draft: Draft) -> bool:
	for entity_id in hero_candidates(world):
		if try_hero(world, draft, entity_id):
			return true
	return false


static func _stable_kills_descending(rows: Array) -> Array[int]:
	# Godot sort_custom is not stable, so ties fall back to the original index.
	rows.sort_custom(
		func(a: Dictionary, b: Dictionary) -> bool:
			if int(a["kills"]) != int(b["kills"]):
				return int(a["kills"]) > int(b["kills"])
			return int(a["seq"]) < int(b["seq"])
	)
	var order: Array[int] = []
	for row in rows:
		order.append(int(row["id"]))
	return order
