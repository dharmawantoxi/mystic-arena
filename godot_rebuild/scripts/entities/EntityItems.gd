class_name EntityItems
extends RefCounted

## Runtime item triggers migrated from hero_items.HeroItemInventory.update.
const TIMERS := [
	"blood_frenzy",
	"guard",
	"veil",
	"chains",
	"rend",
	"bash",
	"overwhelm",
	"static",
	"static_tick",
	"thorn",
	"arctic",
	"gale",
	"pierce_bash",
	"searbrand",
	"arcane",
	"fulgur",
	"hex",
	"rift",
	"pact",
	"vine",
	"ghost"
]


static func update(hero: BattleUnit, enemies: Array[BattleUnit], model: RefCounted) -> void:
	if hero.items == null or not hero.alive:
		return
	for key: String in TIMERS:
		var cd_key := key + "_cd"
		if int(hero.item_state.get(key, 0)) > 0:
			hero.item_state[key] = int(hero.item_state[key]) - 1
		if int(hero.item_state.get(cd_key, 0)) > 0:
			hero.item_state[cd_key] = int(hero.item_state[cd_key]) - 1
	var ratio := hero.hp / maxf(1.0, hero.max_hp)
	_auto_hp(hero, "demon_maw", "blood_frenzy", ratio, model)
	_auto_hp(hero, "scarlet_bulwark", "guard", ratio, model)
	_auto_hp(hero, "tempest_vane", "veil", ratio, model)
	_auto_hp(hero, "razor_carapace", "thorn", ratio, model)
	_auto_hp(hero, "gale_pike", "gale", ratio, model)
	if (
		hero.items.has("gale_pike")
		and hero.item_timer("gale") == int(hero.items.catalog.gale_pike.active.duration)
	):
		var act: Dictionary = hero.items.catalog.gale_pike.active
		var target := hero.target
		if target != null and target.alive:
			hero.pos += (hero.pos - target.pos).normalized() * float(act.dash_distance)
		else:
			hero.pos.x -= hero.facing * float(act.dash_distance)
	_near_trigger(hero, enemies, "fenrir_chain", "chains", model)
	_near_trigger(hero, enemies, "everfrost_guard", "arctic", model)
	_near_trigger(hero, enemies, "searbrand", "searbrand", model)
	if hero.items.has("thunder_coil") and hero.item_timer("static") > 0:
		hero.item_state["static_tick"] = int(hero.item_state.get("static_tick", 0)) - 1
		if int(hero.item_state.static_tick) <= 0:
			var act: Dictionary = hero.items.catalog.thunder_coil.active
			hero.item_state["static_tick"] = int(act.tick)
			_chain(hero, enemies, float(act.damage), int(act.targets), float(act.radius), model)
	if hero.items.has("sanguine_thorn") and hero.item_timer("rend_cd") <= 0:
		var target := hero.target
		if target != null and target.alive and target.team != hero.team:
			var act: Dictionary = hero.items.catalog.sanguine_thorn.active
			hero.item_state["rend"] = int(act.duration)
			hero.item_state["rend_cd"] = int(act.cooldown)
			target.apply_debuff("dmg_amp", float(act.damage_amp), int(act.duration))
	if hero.items.has("abyss_breaker") and hero.item_timer("overwhelm_cd") <= 0:
		var target := hero.target
		if target != null and target.alive and target.team != hero.team:
			var act: Dictionary = hero.items.catalog.abyss_breaker.active
			hero.item_state["overwhelm_cd"] = int(act.cooldown)
			target.apply_debuff("stun", 1.0, int(act.stun))


static func _auto_hp(
	hero: BattleUnit, item_id: String, timer: String, ratio: float, model: RefCounted
) -> void:
	if not hero.items.has(item_id) or hero.item_timer(timer + "_cd") > 0:
		return
	var act: Dictionary = hero.items.catalog.get(item_id, {}).get("active", {})
	if act.is_empty() or ratio >= float(act.get("hp_threshold", 0.0)):
		return
	hero.item_state[timer] = int(act.duration)
	hero.item_state[timer + "_cd"] = int(act.cooldown)
	model.add_popup(hero.pos, str(act.get("name", item_id)).to_upper(), hero.color)


static func _near_trigger(
	hero: BattleUnit, enemies: Array[BattleUnit], item_id: String, timer: String, model: RefCounted
) -> void:
	if not hero.items.has(item_id) or hero.item_timer(timer + "_cd") > 0:
		return
	var act: Dictionary = hero.items.catalog.get(item_id, {}).get("active", {})
	if act.is_empty():
		return
	var radius := float(act.get("trigger_radius", act.get("radius", 220)))
	var near: Array[BattleUnit] = []
	for enemy: BattleUnit in enemies:
		if enemy.alive and enemy.pos.distance_to(hero.pos) <= radius:
			near.append(enemy)
	if near.size() < int(act.get("trigger_enemies", 2)):
		return
	hero.item_state[timer + "_cd"] = int(act.cooldown)
	for enemy: BattleUnit in near:
		enemy.take_damage(float(act.get("damage", 0)), hero.team, "magic", hero)
		if (
			item_id == "fenrir_chain"
			and enemy.pos.distance_to(hero.pos) <= float(act.get("root_radius", radius))
		):
			enemy.apply_debuff("stun", 1.0, int(act.get("root_duration", 72)))
		if item_id == "everfrost_guard":
			enemy.apply_debuff(
				"slow", float(act.get("slow", 0.4)), int(act.get("slow_duration", 120))
			)
		if item_id == "searbrand":
			enemy.apply_debuff(
				"burn",
				float(act.get("burn_dps", 20)),
				int(act.get("burn_duration", 180)),
				hero.team
			)
	model.add_popup(hero.pos, str(act.get("name", item_id)).to_upper(), hero.color)


static func on_attack(
	hero: BattleUnit,
	target: BattleUnit,
	damage: float,
	enemies: Array[BattleUnit],
	model: RefCounted
) -> void:
	if hero.items == null:
		return
	if hero.items.has("cleave_axe") and hero.is_melee_hero:
		var passive: Dictionary = hero.items.catalog.cleave_axe.passive
		for enemy: BattleUnit in enemies:
			if (
				enemy != target
				and enemy.alive
				and enemy.pos.distance_to(target.pos) <= float(passive.cleave_radius)
			):
				enemy.take_damage(damage * float(passive.cleave_pct), hero.team, "physical", hero)
	for item_id: String in ["fenrir_chain", "thunder_coil", "corroder", "basilisk_breath"]:
		if not hero.items.has(item_id):
			continue
		var on_hit: Dictionary = hero.items.catalog.get(item_id, {}).get("on_attack", {})
		if on_hit.is_empty() or model.rng.randf() >= float(on_hit.get("chance", 0.0)):
			continue
		_chain(
			hero,
			enemies,
			float(on_hit.get("damage", 0)),
			int(on_hit.get("targets", 3)),
			float(on_hit.get("radius", 240)),
			model
		)
		if item_id == "corroder":
			target.apply_debuff(
				"armor_shred", float(on_hit.get("armor_shred", 2)), int(on_hit.get("duration", 180))
			)
		if item_id == "basilisk_breath":
			target.apply_debuff(
				"burn",
				float(on_hit.get("poison_dps", 15)),
				int(on_hit.get("duration", 180)),
				hero.team
			)
	if hero.items.has("thunder_coil") and hero.item_timer("static_cd") <= 0:
		var act: Dictionary = hero.items.catalog.thunder_coil.active
		if model.rng.randf() < float(act.get("proc_chance", 0.2)):
			hero.item_state["static"] = int(act.duration)
			hero.item_state["static_cd"] = int(act.cooldown)
			hero.item_state["static_tick"] = int(act.tick)


static func _chain(
	hero: BattleUnit,
	enemies: Array[BattleUnit],
	damage: float,
	targets: int,
	radius: float,
	model: RefCounted
) -> void:
	var near: Array[BattleUnit] = []
	for enemy: BattleUnit in enemies:
		if enemy.alive and enemy.pos.distance_to(hero.pos) <= radius:
			near.append(enemy)
	near.sort_custom(
		func(a: BattleUnit, b: BattleUnit) -> bool:
			return hero.pos.distance_to(a.pos) < hero.pos.distance_to(b.pos)
	)
	for index in range(mini(targets, near.size())):
		near[index].take_damage(damage, hero.team, "magic", hero)
		model.add_effect(near[index].pos, "chain", Color("ffe680"), 12)
