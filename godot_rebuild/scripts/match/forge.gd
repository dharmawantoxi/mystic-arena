extends RefCounted
## Port of the hero_items.py Forge shop transaction half (layer 5f):
## `_resolve_shop_target`, `_try_buy`, `_try_drop`, `pending_forge_items` and
## `deliver_pending_forge_items`. The source keeps the pending queue on the hero
## (`hero._pending_forge_items`); the rebuild mirrors that with
## `HeroState.pending_items`, so a queued order follows its owner across
## respawn. No drawing/input here: the source ItemShopUI owns the panel.
##
## Messages are the source `tr()` keys, returned instead of notifications
## because the rebuild has no localization layer: "forge_purchase",
## "forge_queued", "inventory_full", "magic_only_denied", "item_dropped" and
## "no_hero". A silent refusal (unknown item, not enough gold, melee gate,
## failed equip) returns "" like the source's bare `return`.
##
## The AI purchase path stays in `prototype_battle._buy_item_for` (alive owners
## only, reserve aware); this shop half is what the player panel drives.

const HeroItems = preload("res://scripts/match/hero_items.gd")

# Source `game.heroes` is the player roster only; BLUE is the player side here.
var player_team := 0
# Source `game.itemshop_target_hero` / `game.selected_hero`: entity ids, -1 for
# None. `set_target()`/`set_selected()` take hero ids, not objects, so this
# module never holds a hero reference.
var target_hero_id := -1
var selected_hero_id := -1
# Every transaction, newest last: {op, item, hero_id, status, gold, queued}.
var history: Array = []


func set_target(hero_id: int) -> void:
	target_hero_id = hero_id


func set_selected(hero_id: int) -> void:
	selected_hero_id = hero_id


func resolve_target(heroes: Array) -> Object:
	# Port of _resolve_shop_target: saved target -> selected -> first alive ->
	# first hero (dead or alive). `heroes` is the summoned roster in source
	# order, dead heroes included.
	if heroes.is_empty():
		return null
	for hero in heroes:
		if _id_of(hero) == target_hero_id and target_hero_id >= 0:
			return hero
	for hero in heroes:
		if _id_of(hero) == selected_hero_id and selected_hero_id >= 0:
			return hero
	for hero in heroes:
		if bool(hero.get("alive")):
			return hero
	return heroes[0]


func pending_forge_items(hero: Object) -> Array:
	# Source shape: the queue is created lazily on the hero and stays there.
	return hero.pending_items


func deliver_pending_forge_items(hero: Object) -> Array:
	# Port of deliver_pending_forge_items: called right after respawn, delivers
	# while the inventory accepts; anything that does not fit stays queued.
	var delivered: Array = []
	while not hero.pending_items.is_empty() and hero.items.add(String(hero.pending_items[0])):
		delivered.append(String(hero.pending_items.pop_front()))
	if not delivered.is_empty():
		# Source `add()` runs _on_item_changed inline: max HP and heal amp.
		hero.apply_item_change()
	return delivered


func buy(world: Object, item_id: String) -> Dictionary:
	# Port of _try_buy: resolve the target, gate catalog/gold/slots/role, then
	# equip a living hero or queue the order for a dead one, and only then debit
	# the player's gold. `world` is the battle (units, economy, notifications).
	var hero: Object = resolve_target(_player_heroes(world))
	var result := {
		"ok": false,
		"status": "",
		"item": item_id,
		"hero_id": -1,
		"cost": 0,
		"queued": false,
	}
	if hero == null:
		result["status"] = "no_hero"
		_record(world, "buy", item_id, -1, "no_hero", 0, false)
		return result
	var data: Dictionary = hero.items.item(item_id)
	var cost := int(data.get("cost", 0))
	result["hero_id"] = int(hero.id)
	result["cost"] = cost
	# Silent refusals, exactly the source's bare `return`s: unknown item and a
	# purse that cannot pay.
	if data.is_empty() or player_gold(world) < cost:
		return result
	# Queued orders count against the cap, like the source.
	if hero.items.used_slots() + hero.pending_items.size() >= hero.items.max_slots():
		result["status"] = "inventory_full"
		_record(world, "buy", item_id, hero.id, "inventory_full", 0, false)
		return result
	if not _gates_pass(hero, data):
		if bool(data.get("magic_only", false)):
			result["status"] = "magic_only_denied"
			_record(world, "buy", item_id, hero.id, "magic_only_denied", 0, false)
		return result
	if bool(hero.alive):
		if not hero.items.add(item_id):
			return result
		hero.apply_item_change()
		result["status"] = "forge_purchase"
	else:
		hero.pending_items.append(item_id)
		result["status"] = "forge_queued"
		result["queued"] = true
	result["ok"] = true
	world.economy.spend(player_team, cost)
	target_hero_id = int(hero.id)
	_record(world, "buy", item_id, hero.id, String(result["status"]), cost, bool(result["queued"]))
	return result


func _gates_pass(hero: Object, data: Dictionary) -> bool:
	# Source order: melee_only first (always silent), then magic_only, which
	# notifies magic_only_denied.
	if bool(data.get("melee_only", false)) and float(hero.attack_range) > 80.0:
		return false
	if bool(data.get("magic_only", false)) and not HeroItems.is_magic_hero(hero.settings().role):
		return false
	return true


func drop(world: Object, slot_index: int) -> Dictionary:
	# Port of _try_drop: the shop target (or the resolved default) loses the
	# item; the source refunds nothing.
	var hero: Object = _shop_hero(world)
	var result := {"ok": false, "status": "", "item": "", "hero_id": -1}
	if hero == null:
		return result
	var dropped := String(hero.items.remove(slot_index))
	if dropped == "":
		return result
	hero.apply_item_change()
	result["ok"] = true
	result["status"] = "item_dropped"
	result["item"] = dropped
	result["hero_id"] = int(hero.id)
	_record(world, "drop", dropped, hero.id, "item_dropped", 0, false)
	return result


func player_gold(world: Object) -> int:
	# Source `game.gold` is the player's purse, not a per-team ledger.
	return world.economy.gold[player_team]


func _shop_hero(world: Object) -> Object:
	# Source: the saved itemshop target when it is still summoned, otherwise the
	# resolved default (selected -> first alive -> first hero).
	var heroes: Array = _player_heroes(world)
	for hero in heroes:
		if int(hero.id) == target_hero_id and target_hero_id >= 0:
			return hero
	return resolve_target(heroes)


func _player_heroes(world: Object) -> Array:
	# Source _player_heroes: every summoned hero of the player, dead ones
	# included (game.heroes never holds enemy heroes).
	var heroes: Array = []
	for unit in world.units:
		if unit.is_hero and int(unit.team) == player_team:
			heroes.append(unit)
	return heroes


func _id_of(hero: Object) -> int:
	return int(hero.id)


func _record(
	world: Object,
	op: String,
	item_id: String,
	hero_id: int,
	status: String,
	cost: int,
	queued: bool
) -> void:
	(
		history
		. append(
			{
				"op": op,
				"item": item_id,
				"hero_id": hero_id,
				"status": status,
				"cost": cost,
				"queued": queued,
				"gold": player_gold(world),
			}
		)
	)
