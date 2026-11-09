class_name EntityProjectiles
extends RefCounted

## Homing projectiles and tower bullets migrated from _entity.Bullet/Hero.
const BULLET_SPEED := 8.0
const BULLET_RADIUS := 4.0
const HERO_SPEED := 9.5
const HERO_MAX := 6
const HERO_MAX_AGE := 72
const HERO_DEAD_AGE := 36
const HERO_MAX_DIST := 380.0


static func spawn_tower(
	model: RefCounted,
	owner: BattleUnit,
	target: BattleUnit,
	bullet_type: String,
	origin: Vector2,
	special: Dictionary = {}
) -> void:
	if target == null or not target.alive:
		return
	(
		model
		. projectiles
		. append(
			{
				"kind": "tower",
				"bullet_type": bullet_type,
				"pos": origin,
				"origin": origin,
				"target": target,
				"last_target": target.pos,
				"damage": owner.damage,
				"team": owner.team,
				"speed": BULLET_SPEED,
				"special": special,
				"source": owner,
				"age": 0,
				"alive": true,
				"hit_applied": false,
				"angle": (target.pos - origin).angle(),
			}
		)
	)


static func spawn_hero(
	model: RefCounted,
	owner: BattleUnit,
	target: BattleUnit,
	damage: float,
	is_crit := false,
	speed := HERO_SPEED,
	is_skill := false
) -> void:
	if target == null or not target.alive:
		return
	var own: Array[Dictionary] = []
	for proj: Dictionary in model.projectiles:
		if proj.get("source") == owner and proj.get("kind") == "hero":
			own.append(proj)
	if own.size() >= HERO_MAX:
		var drop: Dictionary = own[0]
		for proj: Dictionary in own:
			if bool(proj.get("is_skill", false)):
				drop = proj
				break
		drop["alive"] = false
	var origin := owner.pos + Vector2(0, -5)
	var aim := target.pos + Vector2(0, -5)
	(
		model
		. projectiles
		. append(
			{
				"kind": "hero",
				"bullet_type": "magic" if owner.dmg_school == "magic" else "arrow",
				"pos": origin,
				"origin": origin,
				"target": target,
				"last_target": aim,
				"damage": damage,
				"team": owner.team,
				"speed": speed,
				"source": owner,
				"school": owner.dmg_school,
				"is_crit": is_crit,
				"is_skill": is_skill,
				"age": 0,
				"alive": true,
				"hit_applied": false,
				"angle": (aim - origin).angle(),
				"color": owner.color,
			}
		)
	)


static func update(model: RefCounted) -> void:
	var keep: Array[Dictionary] = []
	for proj: Dictionary in model.projectiles:
		if not bool(proj.get("alive", false)):
			continue
		proj["age"] = int(proj.get("age", 0)) + 1
		var target: BattleUnit = proj.get("target")
		var target_alive := target != null and target.alive
		var aim: Vector2 = proj.get("last_target", proj.pos)
		if target_alive:
			aim = target.pos
			proj["last_target"] = aim
		elif proj.kind == "tower":
			continue
		if proj.kind == "hero":
			if int(proj.age) > HERO_MAX_AGE:
				continue
			if not target_alive and int(proj.age) > HERO_DEAD_AGE:
				continue
			if Vector2(proj.origin).distance_to(proj.pos) > HERO_MAX_DIST:
				continue
		var pos: Vector2 = proj.pos
		var delta := aim - pos
		var dist := delta.length()
		if dist > 0.0:
			proj["angle"] = delta.angle()
		var hit_radius := BULLET_RADIUS if proj.kind == "tower" else 5.0
		if dist < float(proj.speed) + hit_radius:
			if proj.kind == "hero" and bool(proj.get("hit_applied", false)):
				continue
			proj["pos"] = aim
			proj["hit_applied"] = true
			if target_alive:
				_hit(model, proj, target)
			if proj.kind == "tower":
				continue
			keep.append(proj)
		else:
			proj["pos"] = pos + delta / dist * float(proj.speed)
			keep.append(proj)
	model.projectiles = keep


static func _hit(model: RefCounted, proj: Dictionary, target: BattleUnit) -> void:
	var source: BattleUnit = proj.get("source")
	if proj.kind == "hero":
		# Python explicitly suppresses all basic-attack impact feedback.
		if source != null and bool(proj.get("is_skill", false)):
			model.hero_fx.projectile_impact(
				source,
				target.pos,
				float(proj.get("angle", 0.0)),
				float(proj.damage),
				bool(proj.get("is_crit", false))
			)
			HeroFeedback.projectile_hit(
				model.feel, source.unit_type, float(proj.damage), bool(proj.get("is_crit", false))
			)
		if float(proj.damage) > 0.0:
			var dealt := target.take_damage(
				float(proj.damage),
				str(proj.team),
				"projectile",
				source,
				str(proj.get("school", ""))
			)
			if source != null and source.items != null and not bool(proj.get("is_skill", false)):
				EntityItems.on_ranged_attack_hit(
					source, target, dealt, model.enemies_of(str(proj.team)), model
				)
			model.add_effect(
				target.pos, "CRIT!" if bool(proj.get("is_crit", false)) else "", Color.WHITE, 18
			)
		return
	var bullet_type := str(proj.get("bullet_type", "normal"))
	var dealt := target.take_damage(float(proj.damage), str(proj.team), "projectile", source)
	model.add_damage_number(target.pos, int(dealt), false, "normal")
	var special: Dictionary = proj.get("special", {})
	var enemies: Array[BattleUnit] = model.enemies_of(str(proj.team))
	if bullet_type == "cannon":
		var burn := float(special.get("burn_dps", 0))
		if burn > 0:
			target.apply_debuff("burn", burn, int(special.get("burn_duration", 0)), str(proj.team))
		var radius := float(special.get("splash", 40))
		for unit: BattleUnit in enemies:
			if unit != target and unit.pos.distance_to(target.pos) <= radius:
				unit.take_damage(int(float(proj.damage) * 0.6), str(proj.team), "normal", source)
				if burn > 0:
					unit.apply_debuff(
						"burn", burn, int(special.get("burn_duration", 0)), str(proj.team)
					)
	elif bullet_type == "ice":
		var slow := float(special.get("slow", 0.2))
		var duration := int(special.get("slow_duration", 90))
		target.apply_debuff("slow", slow, duration)
		var atk_slow := float(special.get("atk_slow", 0))
		if atk_slow > 0:
			target.apply_debuff("atk_slow", atk_slow, duration)
		var aoe := float(special.get("slow_aoe", 0))
		if aoe > 0:
			for unit: BattleUnit in enemies:
				if unit != target and unit.pos.distance_to(target.pos) <= aoe:
					unit.apply_debuff("slow", slow, duration)
					if atk_slow > 0:
						unit.apply_debuff("atk_slow", atk_slow, duration)
	elif bullet_type == "mage":
		var duration := int(special.get("debuff_duration", 120))
		var skill_down := float(special.get("skill_down", 0))
		var anti_heal := float(special.get("anti_heal", 0))
		if skill_down > 0:
			target.apply_debuff("skill_down", skill_down, duration)
		if anti_heal > 0:
			target.apply_debuff("anti_heal", anti_heal, duration)
	model.add_effect(target.pos, "", Color("ffd27a"), 10)
