class_name EntityItems
extends RefCounted

## Native runtime port of hero_items.HeroItemInventory.update/on-hit, miasma,
## and update_auras. Deterministic triggers follow the Python order; RNG procs
## use the match RNG so replays stay seeded.
static var miasma: Dictionary = {}


static func clear() -> void:
	miasma.clear()


static func update(hero: BattleUnit, enemies: Array[BattleUnit], model: RefCounted) -> void:
	if hero.items == null or not hero.alive:
		return
	var inv := hero.items
	inv.tick_timers(1)
	tick_miasma(1)
	var ratio := hero.hp / maxf(1.0, hero.max_hp)
	if inv.has("demon_maw") and inv.timer("blood_frenzy_cd") <= 0:
		if hero.max_hp > 0 and ratio < 0.35:
			var act: Dictionary = inv.catalog.demon_maw.active
			inv.set_timer("blood_frenzy", int(act.duration))
			inv.set_timer("blood_frenzy_cd", int(act.cooldown))
	if hero.max_hp <= 0:
		return
	_auto_hp(hero, "scarlet_bulwark", "guard", ratio, model)
	_auto_hp(hero, "tempest_vane", "veil", ratio, model)
	_near_trigger(hero, enemies, "fenrir_chain", "chains", model)
	_target_debuff(hero, "sanguine_thorn", "rend", model)
	if (
		inv.has("sanguine_thorn")
		and inv.timer("rend_cd") == int(inv.catalog.sanguine_thorn.active.cooldown)
	):
		var target := hero.target
		if target != null and target.alive and target.team != hero.team:
			var act: Dictionary = inv.catalog.sanguine_thorn.active
			inv.state["rend_target"] = target
			target.apply_debuff("silence", 1.0, int(act.duration))
			target.apply_debuff("dmg_amp", float(act.damage_amp), int(act.duration))
			_popup(model, target.pos, "SOUL REND!", inv.catalog.sanguine_thorn.glow)
	if inv.has("abyss_breaker") and inv.timer("overwhelm_cd") <= 0:
		var target := hero.target
		if target != null and target.alive and target.team != hero.team:
			var act: Dictionary = inv.catalog.abyss_breaker.active
			inv.set_timer("overwhelm_cd", int(act.cooldown))
			target.apply_debuff("stun", 1.0, int(act.stun))
			_popup(model, target.pos, "OVERWHELM!", inv.catalog.abyss_breaker.glow)
	if inv.has("thunder_coil") and inv.timer("static") > 0:
		inv.set_timer("static_tick", inv.timer("static_tick") - 1)
		if inv.timer("static_tick") <= 0:
			var act: Dictionary = inv.catalog.thunder_coil.active
			inv.set_timer("static_tick", int(act.tick))
			_chain(hero, enemies, float(act.damage), int(act.targets), float(act.radius), model)
	_auto_hp(hero, "razor_carapace", "thorn", ratio, model)
	_near_trigger(hero, enemies, "everfrost_guard", "arctic", model)
	if inv.has("gale_pike") and inv.timer("gale_cd") <= 0:
		var act: Dictionary = inv.catalog.gale_pike.active
		if ratio < float(act.hp_threshold):
			inv.set_timer("gale", int(act.duration))
			inv.set_timer("gale_cd", int(act.cooldown))
			var target := hero.target
			if target != null and target.alive:
				hero.pos += (hero.pos - target.pos).normalized() * float(act.dash_distance)
			else:
				hero.pos.x -= hero.facing * float(act.dash_distance)
			_popup(model, hero.pos, "GALE LEAP!", inv.catalog.gale_pike.glow)
	_near_trigger(hero, enemies, "searbrand", "searbrand", model)
	_near_trigger(hero, enemies, "astral_codex", "arcane", model)
	if inv.has("fulgur_scepter") and inv.timer("fulgur_cd") <= 0:
		var target := hero.target
		if target != null and target.alive and target.team != hero.team:
			var act: Dictionary = inv.catalog.fulgur_scepter.active
			inv.set_timer("fulgur_cd", int(act.cooldown))
			_deal(target, float(act.damage), hero, model)
			_popup(model, target.pos, "ENERGY BLAST!", inv.catalog.fulgur_scepter.glow)
	if inv.has("hex_idol") and inv.timer("hex_cd") <= 0:
		var target := hero.target
		if target != null and target.alive and target.team != hero.team:
			var act: Dictionary = inv.catalog.hex_idol.active
			inv.set_timer("hex_cd", int(act.cooldown))
			target.apply_debuff("stun", 1.0, int(act.stun))
			target.apply_debuff("silence", 1.0, int(act.silence))
			_popup(model, target.pos, "HEX!", inv.catalog.hex_idol.glow)
	_near_trigger(hero, enemies, "rift_veil", "rift", model)
	if inv.has("vital_stone") and inv.timer("pact_cd") <= 0:
		var act: Dictionary = inv.catalog.vital_stone.active
		if ratio < float(act.hp_threshold):
			inv.set_timer("pact_cd", int(act.cooldown))
			var heal := int(hero.max_hp * float(act.heal_pct))
			hero.hp = minf(hero.max_hp, hero.hp + heal)
			_popup(model, hero.pos, "VITALITY PACT!", inv.catalog.vital_stone.glow)
	_auto_hp(hero, "spectral_charm", "ghost", ratio, model)
	_regen(hero)


static func _auto_hp(
	hero: BattleUnit, item_id: String, timer: String, ratio: float, model: RefCounted
) -> void:
	var inv := hero.items
	if not inv.has(item_id) or inv.timer(timer + "_cd") > 0:
		return
	var act: Dictionary = inv.catalog.get(item_id, {}).get("active", {})
	if act.is_empty() or ratio >= float(act.get("hp_threshold", 0.0)):
		return
	inv.set_timer(timer, int(act.duration))
	inv.set_timer(timer + "_cd", int(act.cooldown))
	_popup(
		model,
		hero.pos,
		str(act.get("name", item_id)).to_upper(),
		inv.catalog.get(item_id, {}).get("glow", [255, 255, 255])
	)


static func _target_debuff(
	hero: BattleUnit, item_id: String, timer: String, _model: RefCounted
) -> void:
	var inv := hero.items
	if not inv.has(item_id) or inv.timer(timer + "_cd") > 0:
		return
	var target := hero.target
	if target == null or not target.alive or target.team == hero.team:
		return
	var act: Dictionary = inv.catalog.get(item_id, {}).get("active", {})
	inv.set_timer(timer, int(act.duration))
	inv.set_timer(timer + "_cd", int(act.cooldown))


static func _near_trigger(
	hero: BattleUnit, enemies: Array[BattleUnit], item_id: String, timer: String, model: RefCounted
) -> void:
	var inv := hero.items
	if not inv.has(item_id) or inv.timer(timer + "_cd") > 0:
		return
	var act: Dictionary = inv.catalog.get(item_id, {}).get("active", {})
	if act.is_empty():
		return
	var radius := float(act.get("trigger_radius", act.get("radius", 220)))
	var near := _near(hero, enemies, radius)
	if near.size() < int(act.get("trigger_enemies", 2)):
		return
	inv.set_timer(timer + "_cd", int(act.cooldown))
	for enemy: BattleUnit in near:
		_deal(enemy, float(act.get("damage", 0)), hero, model)
		if (
			item_id == "fenrir_chain"
			and hero.pos.distance_to(enemy.pos) <= float(act.get("root_radius", radius))
		):
			enemy.apply_debuff("stun", 1.0, int(act.get("root_duration", 72)))
		elif item_id == "everfrost_guard":
			enemy.apply_debuff(
				"slow", float(act.get("slow", 0.4)), int(act.get("slow_duration", 120))
			)
		elif item_id == "searbrand":
			enemy.apply_debuff(
				"burn",
				float(act.get("burn_dps", 20)),
				int(act.get("burn_duration", 180)),
				hero.team
			)
		elif item_id == "astral_codex":
			enemy.apply_debuff("silence", 1.0, int(act.get("silence_duration", 90)))
		elif item_id == "rift_veil":
			enemy.apply_debuff(
				"dmg_amp", float(act.get("damage_amp", 0.0)), int(act.get("duration", 180))
			)
	_popup(
		model,
		hero.pos,
		str(act.get("name", item_id)).to_upper(),
		inv.catalog.get(item_id, {}).get("glow", [255, 255, 255])
	)
	if item_id != "rift_veil":
		_chain_fx(model, hero, near, inv.catalog.get(item_id, {}).get("color", [255, 230, 128]))


static func _regen(hero: BattleUnit) -> void:
	var inv := hero.items
	if not hero.alive or hero.max_hp <= 0 or hero.hp >= hero.max_hp:
		return
	var regen := inv.hp_regen()
	if inv.has("leviathan_heart"):
		var passive: Dictionary = inv.catalog.leviathan_heart.passive
		if inv.timer("last_damage") <= 0:
			regen += hero.max_hp * float(passive.out_of_combat_regen_pct) / 60.0
	if regen > 0.0:
		hero.hp = minf(hero.max_hp, hero.hp + regen)


static func notify_damage_taken(
	hero: BattleUnit,
	rng: RandomNumberGenerator,
	damage: float,
	source: BattleUnit,
	model: RefCounted
) -> void:
	var inv := hero.items
	if inv == null:
		return
	if inv.has("leviathan_heart"):
		inv.set_timer("last_damage", int(inv.catalog.leviathan_heart.passive.combat_timeout))
	if inv.has("thunder_coil") and inv.timer("static_cd") <= 0:
		var act: Dictionary = inv.catalog.thunder_coil.active
		if rng.randf() < float(act.proc_chance):
			inv.set_timer("static", int(act.duration))
			inv.set_timer("static_tick", int(act.tick))
			inv.set_timer("static_cd", int(act.cooldown))
			_popup(model, hero.pos, "STATIC CHARGE!", inv.catalog.thunder_coil.glow)
	var reflect := inv.reflect_pct()
	if (
		reflect > 0.0
		and damage > 0.0
		and source != null
		and source.alive
		and source.team != hero.team
	):
		var dealt := int(damage * reflect)
		if dealt > 0:
			_deal(source, dealt, hero, model)
			_popup(model, source.pos, "-%d" % dealt, inv.catalog.razor_carapace.glow)


static func on_basic_attack_hit(
	hero: BattleUnit,
	target: BattleUnit,
	damage: float,
	all_units: Array[BattleUnit],
	model: RefCounted
) -> void:
	if hero.items == null or not hero.alive:
		return
	var inv := hero.items
	var ls := inv.lifesteal()
	if ls > 0.0 and damage > 0.0:
		hero.hp = minf(hero.max_hp, hero.hp + damage * ls)
	_on_hit_common(hero, target, damage, all_units, model)
	var cleave := inv.cleave()
	if not cleave.is_empty() and damage > 0.0:
		var splash := int(damage * float(cleave[0]))
		if splash > 0:
			for unit: BattleUnit in all_units:
				if unit == target or not unit.alive or unit.team == hero.team:
					continue
				if unit.pos.distance_to(target.pos) <= float(cleave[1]):
					unit.take_damage(splash, hero.team, "normal", hero)


static func on_ranged_attack_hit(
	hero: BattleUnit,
	target: BattleUnit,
	damage: float,
	all_units: Array[BattleUnit],
	model: RefCounted
) -> void:
	if hero.items == null or not hero.alive:
		return
	_on_hit_common(hero, target, damage, all_units, model)


static func on_attack(
	hero: BattleUnit,
	target: BattleUnit,
	damage: float,
	enemies: Array[BattleUnit],
	model: RefCounted
) -> void:
	on_basic_attack_hit(hero, target, damage, enemies, model)


static func _on_hit_common(
	hero: BattleUnit,
	target: BattleUnit,
	damage: float,
	all_units: Array[BattleUnit],
	model: RefCounted
) -> void:
	var inv := hero.items
	var rng: RandomNumberGenerator = model.rng
	var shred := inv.armor_shred()
	if not shred.is_empty() and target != null:
		target.apply_debuff("armor_shred", float(shred[0]), int(shred[1]))
	var bash := inv.bash()
	if not bash.is_empty() and inv.timer("bash_cd") <= 0 and target != null and target.alive:
		if rng.randf() < float(bash.chance):
			inv.set_timer("bash_cd", int(bash.cooldown))
			target.apply_debuff("stun", 1.0, int(bash.stun))
			target.take_damage(float(bash.damage), hero.team, "normal", hero)
			_popup(model, target.pos, "BASH!", inv.catalog.abyss_breaker.glow)
	var chain := inv.on_attack_chain()
	if (
		not chain.is_empty()
		and float(chain.get("chance", 0)) > 0.0
		and target != null
		and rng.randf() < float(chain.chance)
	):
		var hit: Array[BattleUnit] = []
		if target.alive:
			hit.append(target)
		for unit: BattleUnit in all_units:
			if unit == target or not unit.alive or unit.team == hero.team:
				continue
			if unit.pos.distance_to(target.pos) <= float(chain.radius):
				hit.append(unit)
			if hit.size() >= int(chain.targets):
				break
		for unit: BattleUnit in hit:
			_deal(unit, float(chain.damage), hero, model)
		if not hit.is_empty():
			var color_id := "thunder_coil" if inv.has("thunder_coil") else "fenrir_chain"
			_chain_fx(model, hero, hit, inv.catalog.get(color_id, {}).get("color", [255, 230, 128]))
	if target == null or not target.alive:
		return
	if inv.has("sundering_cudgel") and inv.timer("pierce_bash_cd") <= 0:
		var cudgel: Dictionary = inv.catalog.sundering_cudgel.bash
		if rng.randf() < float(cudgel.chance):
			inv.set_timer("pierce_bash_cd", int(cudgel.cooldown))
			target.apply_debuff("stun", 1.0, int(cudgel.stun))
			_deal(target, float(cudgel.damage), hero, model)
			_popup(model, target.pos, "PIERCE!", inv.catalog.sundering_cudgel.glow)
	if inv.has("frostbound_eye"):
		var frost: Dictionary = inv.catalog.frostbound_eye.on_attack
		target.apply_debuff("slow", float(frost.slow), int(frost.duration))
		target.apply_debuff("atk_slow", float(frost.atk_slow), int(frost.duration))
		target.apply_debuff("anti_heal", float(frost.anti_heal), int(frost.duration))
	if inv.has("basilisk_breath"):
		var poison: Dictionary = inv.catalog.basilisk_breath.on_attack
		apply_miasma(target, hero, poison)
		var multishot: Dictionary = inv.catalog.basilisk_breath.multishot
		if not hero.is_melee_hero and rng.randf() < float(multishot.chance):
			var extras: Array[BattleUnit] = []
			for unit: BattleUnit in all_units:
				if unit == target or not unit.alive or unit.team == hero.team:
					continue
				if unit.pos.distance_to(target.pos) <= float(multishot.radius):
					extras.append(unit)
			extras.sort_custom(
				func(a: BattleUnit, b: BattleUnit) -> bool:
					return target.pos.distance_to(a.pos) < target.pos.distance_to(b.pos)
			)
			var shot := 0
			for unit: BattleUnit in extras:
				if shot >= int(multishot.targets):
					break
				_deal(unit, int(damage * float(multishot.damage_pct)), hero, model)
				apply_miasma(unit, hero, poison)
				shot += 1
			if not extras.is_empty():
				_chain_fx(
					model,
					hero,
					extras.slice(0, int(multishot.targets)),
					inv.catalog.basilisk_breath.color
				)
	if inv.has("runic_gavel") and inv.timer("empower_charge") <= 0:
		var bonus := inv.consume_empower_strike()
		if bonus > 0.0:
			_deal(target, bonus, hero, model)
			_popup(model, target.pos, "EMPOWER!", inv.catalog.runic_gavel.glow)
	if inv.has("vine_rod") and inv.timer("vine_cd") <= 0:
		var vine: Dictionary = inv.catalog.vine_rod.on_attack
		inv.set_timer("vine_cd", int(vine.cooldown))
		target.apply_debuff("slow", 1.0, int(vine.root_duration))
		_popup(model, target.pos, "ROOT!", inv.catalog.vine_rod.glow)


static func apply_miasma(target: BattleUnit, source: BattleUnit, data: Dictionary) -> void:
	if target == null or not target.alive:
		return
	var key := target.get_instance_id()
	var damage := maxi(
		6,
		mini(
			int(data.get("cap_damage", 9999)), int(target.max_hp * float(data.max_hp_pct_per_tick))
		)
	)
	if not miasma.has(key):
		miasma[key] = {
			"target": target,
			"source": source,
			"damage": damage,
			"timer": int(data.duration),
			"tick_cd": int(data.tick)
		}
	else:
		var prev: Dictionary = miasma[key]
		prev["source"] = source
		prev["damage"] = maxi(int(prev.damage), damage)
		prev["timer"] = maxi(int(prev.timer), int(data.duration))
		prev["tick_cd"] = mini(int(prev.tick_cd), int(data.tick))


static func tick_miasma(dt := 1) -> void:
	if miasma.is_empty():
		return
	var expired: Array = []
	for key: Variant in miasma:
		var row: Dictionary = miasma[key]
		var target: BattleUnit = row.target
		if target == null or not target.alive:
			expired.append(key)
			continue
		row["timer"] = int(row.timer) - dt
		row["tick_cd"] = int(row.tick_cd) - dt
		if int(row.tick_cd) <= 0:
			row["tick_cd"] = 30
			var source: BattleUnit = row.source
			target.take_damage(
				float(row.damage), source.team if source != null else "", "magic", source
			)
		if int(row.timer) <= 0:
			expired.append(key)
	for key: Variant in expired:
		miasma.erase(key)


static func update_auras(model: RefCounted) -> void:
	var heroes: Array[BattleUnit] = []
	heroes.append_array(model.heroes)
	heroes.append_array(model.enemy_heroes)
	for hero: BattleUnit in heroes:
		if hero.items == null:
			continue
		hero.items.aura_armor = 0.0
		hero.items.aura_attack_speed = 0.0
		hero.items.aura_armor_reduction = 0.0
		hero.items.aura_guard_block = 0.0
	var units: Array[BattleUnit] = []
	units.append_array(heroes)
	units.append_array(model.minions)
	if model.active_boss != null and model.active_boss.alive:
		units.append(model.active_boss)
	var guards: Array[BattleUnit] = []
	var frost: Array[BattleUnit] = []
	var solar: Array[BattleUnit] = []
	var sear: Array[BattleUnit] = []
	var aegis: Array[BattleUnit] = []
	for hero: BattleUnit in heroes:
		if not hero.alive or hero.items == null:
			continue
		if hero.items.has("scarlet_bulwark") and hero.items.timer("guard") > 0:
			guards.append(hero)
		if hero.items.has("everfrost_guard"):
			frost.append(hero)
		if hero.items.has("solar_brand"):
			solar.append(hero)
		if hero.items.has("searbrand"):
			sear.append(hero)
		if hero.items.has("steel_aegis"):
			aegis.append(hero)
	if not guards.is_empty():
		var act: Dictionary = model.data.item("scarlet_bulwark").active
		for hero: BattleUnit in heroes:
			if not hero.alive or hero.items == null:
				continue
			for source: BattleUnit in guards:
				if (
					source.team != hero.team
					or source.pos.distance_to(hero.pos) > float(act.ally_radius)
				):
					continue
				var block := int(act.base_block) + int(source.max_hp * float(act.max_hp_block_pct))
				hero.items.aura_guard_block = maxf(hero.items.aura_guard_block, block)
	_aura_debuffs(model, units, frost, solar, sear)
	if aegis.is_empty():
		return
	var aura: Dictionary = model.data.item("steel_aegis").aura
	for hero: BattleUnit in heroes:
		if not hero.alive or hero.items == null:
			continue
		for source: BattleUnit in aegis:
			if source == hero:
				continue
			var dist := source.pos.distance_to(hero.pos)
			if hero.team == source.team:
				if dist <= float(aura.ally_radius):
					hero.items.aura_armor += float(aura.ally_armor)
					hero.items.aura_attack_speed += float(aura.ally_attack_speed)
			elif dist <= float(aura.enemy_radius):
				hero.items.aura_armor_reduction += float(aura.enemy_armor_reduction)


static func _aura_debuffs(
	model: RefCounted,
	units: Array[BattleUnit],
	frost: Array[BattleUnit],
	solar: Array[BattleUnit],
	sear: Array[BattleUnit]
) -> void:
	if frost.is_empty() and solar.is_empty() and sear.is_empty():
		return
	var f: Dictionary = model.data.item("everfrost_guard").aura
	var s: Dictionary = model.data.item("solar_brand").aura
	var se: Dictionary = model.data.item("searbrand").aura
	for unit: BattleUnit in units:
		if not unit.alive:
			continue
		for source: BattleUnit in frost:
			if (
				unit.team != source.team
				and source.pos.distance_to(unit.pos) <= float(f.enemy_radius)
			):
				unit.apply_debuff("atk_slow", float(f.enemy_atk_slow), 30)
				unit.apply_debuff("anti_heal", float(f.enemy_anti_heal), 30)
				break
		for source: BattleUnit in solar:
			if (
				unit.team != source.team
				and source.pos.distance_to(unit.pos) <= float(s.enemy_radius)
			):
				unit.apply_debuff("burn", float(s.burn_dps), 30, source.team)
				unit.apply_debuff("blind", float(s.blind), 30)
				break
		for source: BattleUnit in sear:
			if (
				unit.team != source.team
				and source.pos.distance_to(unit.pos) <= float(se.enemy_radius)
			):
				unit.apply_debuff("anti_heal", float(se.enemy_anti_heal), 30)
				unit.apply_debuff("burn", float(se.burn_dps), 30, source.team)
				break


static func _near(hero: BattleUnit, enemies: Array[BattleUnit], radius: float) -> Array[BattleUnit]:
	var out: Array[BattleUnit] = []
	for enemy: BattleUnit in enemies:
		if enemy.alive and enemy.pos.distance_to(hero.pos) <= radius:
			out.append(enemy)
	return out


static func _chain(
	hero: BattleUnit,
	enemies: Array[BattleUnit],
	damage: float,
	targets: int,
	radius: float,
	model: RefCounted
) -> void:
	var near := _near(hero, enemies, radius)
	near.sort_custom(
		func(a: BattleUnit, b: BattleUnit) -> bool:
			return hero.pos.distance_to(a.pos) < hero.pos.distance_to(b.pos)
	)
	var hit := near.slice(0, targets)
	for enemy: BattleUnit in hit:
		_deal(enemy, damage, hero, model)
	if not hit.is_empty():
		_chain_fx(model, hero, hit, [255, 230, 128])


static func _deal(target: BattleUnit, amount: float, hero: BattleUnit, _model: RefCounted) -> void:
	if amount > 0.0:
		target.take_damage(amount, hero.team, "magic", hero)


static func _popup(model: RefCounted, pos: Vector2, text: String, color: Variant) -> void:
	if model.has_method("add_popup"):
		model.add_popup(pos, text, _color(color))


static func _chain_fx(
	model: RefCounted, hero: BattleUnit, targets: Array[BattleUnit], color: Variant
) -> void:
	if model.has_method("add_effect"):
		for target: BattleUnit in targets:
			model.add_effect(target.pos, "chain", _color(color), 12)
		if not targets.is_empty():
			model.add_effect(hero.pos, "chain", _color(color), 12)


static func _color(value: Variant) -> Color:
	if value is Color:
		return value
	if value is Array and value.size() >= 3:
		return Color(float(value[0]) / 255.0, float(value[1]) / 255.0, float(value[2]) / 255.0)
	return Color.WHITE
