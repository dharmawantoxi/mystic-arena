class_name HeroLiveFx
extends RefCounted

## Native slices: Zephyr FX/state/trail plus Grimjaw foreground hurt streak/flash.
## No owner references survive here, no gameplay RNG or damage is modified.
var systems: Dictionary = {}
var impacts: Dictionary = {}
var hurts: Dictionary = {}
var grimjaw_hurts: Dictionary = {}
var skills: Dictionary = {}
var directors: Dictionary = {}
var visual_projectiles: Dictionary = {}
var budget := 1.0
var glow_enabled := true
var enabled := true
var last_ms := -1
var trails: Dictionary = {}
var trail_ms := -1
var fx_delta := 0.0


func configure(quality: Dictionary) -> void:
	enabled = bool(quality.get("particles", true))
	glow_enabled = bool(quality.get("glow", true))
	budget = clampf(float(quality.get("particle_ratio", 1.0)), 0.0, 1.0) if enabled else 0.0
	for system: ZephyrParticlePool in systems.values():
		system.budget = budget
		if system is GrimjawParticlePool:
			system.glow_enabled = glow_enabled
	if not enabled:
		trails.clear()
		impacts.clear()
		hurts.clear()
		grimjaw_hurts.clear()
		skills.clear()
		directors.clear()
		visual_projectiles.clear()


static func impact_recipe(power: float, critical: bool, angle: float) -> Array:
	ZephyrBolt.ensure_loaded()
	var colors := ZephyrBolt.palette
	if colors.is_empty():
		return []
	return [
		{
			"count": int(9 + 7 * minf(2.0, power)) + (6 if critical else 0),
			"options":
			{
				"speed": [120, 340],
				"life": [0.18, 0.44],
				"size": [2, 4],
				"colors": [colors.fx_white, colors.fx_hot, colors.fx_bright],
				"spread": 2.4,
				"direction": angle,
				"drag": 3.6,
				"shape": "streak"
			}
		},
		{
			"count": 6 + (4 if critical else 0),
			"options":
			{
				"speed": [70, 190],
				"life": [0.3, 0.65],
				"size": [2, 5],
				"colors": [colors.thorn_lit, colors.ash, colors.fx_light],
				"gravity": 480.0,
				"drag": 1.1,
				"shape": "shard",
				"rotation_speed": [-16.0, 16.0]
			}
		},
	]


func projectile_impact(
	owner: BattleUnit, position: Vector2, angle: float, damage: float, critical: bool
) -> void:
	if owner == null or owner.unit_type != "zephyr" or budget <= 0.0:
		return
	var key := owner.get_instance_id()
	if not systems.has(key):
		systems[key] = ZephyrParticlePool.new()
	var system: ZephyrParticlePool = systems[key]
	system.budget = budget
	var power := 0.7 + minf(1.6, damage / 45.0)
	if not impacts.has(key):
		impacts[key] = []
	var events: Array = impacts[key]
	if events.size() >= 8:
		events.pop_front()
	events.append(ZephyrImpact.new().spawn(position.x, position.y, angle, power, critical))
	for recipe: Dictionary in impact_recipe(power, critical, angle):
		system.burst(position.x, position.y, int(recipe.count), recipe.options)


func cast(owner: BattleUnit, key: String) -> void:
	if (
		owner == null
		or owner.unit_type not in ["zephyr", "grimjaw"]
		or not enabled
		or budget <= 0.0
	):
		return
	var id := owner.get_instance_id()
	if not skills.has(id):
		skills[id] = []
	var records: Array = skills[id]
	if owner.unit_type == "grimjaw":
		GrimjawSkill.ensure_grimjaw_loaded()
		if records.size() >= int(GrimjawSkill.grimjaw_config.director_limit):
			records.pop_front()
		var radius := owner.skill_range if key == "q" else 0.0
		records.append(GrimjawSkill.new().spawn(key, owner.pos.x, owner.pos.y + 16, radius))
	else:
		ZephyrSkill.ensure_loaded()
		if records.size() >= int(ZephyrSkill.config.director_limit):
			records.pop_front()
		records.append(ZephyrSkill.new().spawn(key, owner.pos.x, owner.pos.y + 18))


func _update_skills(dt: float) -> void:
	for id: int in skills.keys():
		var keep: Array = []
		for skill: ZephyrSkill in skills[id]:
			if not skill.update(dt):
				continue
			keep.append(skill)
			if skill.events.is_empty():
				continue
			if not systems.has(id):
				systems[id] = (
					GrimjawParticlePool.new() if skill is GrimjawSkill else ZephyrParticlePool.new()
				)
			var pool: ZephyrParticlePool = systems[id]
			pool.budget = budget
			if pool is GrimjawParticlePool:
				pool.glow_enabled = glow_enabled
			for event: Dictionary in skill.events:
				var a: Array = event.args
				if event.type == "burst":
					pool.burst(a[0], a[1], int(a[2]), event.options)
				else:
					pool.spawn(a[0], a[1], a[2], a[3], a[4], a[5], a[6], event.options)
		if keep.is_empty():
			skills.erase(id)
		else:
			skills[id] = keep


func spawn_visual_projectile(
	owner: BattleUnit, origin: Vector2, aim: Vector2, options: Dictionary = {}
) -> ZephyrVisualProjectile:
	if owner == null or owner.unit_type != "zephyr" or not enabled or budget <= 0.0:
		return null
	var key := owner.get_instance_id()
	if not visual_projectiles.has(key):
		visual_projectiles[key] = ZephyrVisualProjectileSystem.new()
	return visual_projectiles[key].spawn(origin.x, origin.y, aim.x, aim.y, options)


func _update_visual_projectiles(dt: float, targets: Array) -> void:
	var snapshots: Dictionary = {}
	for candidate: Variant in targets:
		if candidate is BattleUnit:
			snapshots[candidate.get_instance_id()] = {
				"alive": candidate.alive,
				"x": candidate.pos.x,
				"y": candidate.pos.y,
				"radius": candidate.radius
			}
	for key: int in visual_projectiles.keys():
		if not systems.has(key):
			systems[key] = ZephyrParticlePool.new()
		var pool: ZephyrParticlePool = systems[key]
		pool.budget = budget
		var manager: ZephyrVisualProjectileSystem = visual_projectiles[key]
		manager.update(dt, snapshots, pool)
		if manager.projectiles.is_empty():
			visual_projectiles.erase(key)


func update(feel: HeroCombatFeel, now_ms: int, owners: Array = [], targets: Array = []) -> void:
	# FixedClock can call the adapter multiple times during catch-up. Never
	# age particles twice for the same SDL-equivalent millisecond timestamp.
	if now_ms <= last_ms:
		return
	last_ms = now_ms
	var dt := feel.fx_dt(now_ms)
	fx_delta = dt
	_observe_hurt(owners, dt)
	_observe_grimjaw_hurt(owners, dt, feel)
	if dt <= 0.0:
		return
	for key: int in systems.keys():
		var system: ZephyrParticlePool = systems[key]
		system.update(dt)
		if system.live.is_empty() and not visual_projectiles.has(key):
			systems.erase(key)
	_update_visual_projectiles(dt, targets if not targets.is_empty() else owners)
	for key: int in impacts.keys():
		var keep: Array = []
		for impact: ZephyrImpact in impacts[key]:
			if impact.update(dt):
				keep.append(impact)
		if keep.is_empty():
			impacts.erase(key)
		else:
			impacts[key] = keep

	_update_skills(dt)


func _observe_hurt(owners: Array, dt: float) -> void:
	if not enabled or budget <= 0.0:
		hurts.clear()
		return
	var seen: Dictionary = {}
	for candidate: Variant in owners:
		if not candidate is BattleUnit or candidate.unit_type != "zephyr":
			continue
		var owner: BattleUnit = candidate
		var key := owner.get_instance_id()
		seen[key] = true
		if not hurts.has(key):
			hurts[key] = ZephyrHurt.new()
		var hurt: ZephyrHurt = hurts[key]
		if hurt.observe(owner.hp, owner.pos.x, owner.pos.y, dt):
			if not systems.has(key):
				systems[key] = ZephyrParticlePool.new()
			var system: ZephyrParticlePool = systems[key]
			system.budget = budget
			var recipe := ZephyrHurt.recipe()
			system.burst(owner.pos.x, owner.pos.y - 8, int(recipe.count), recipe.options)
	for key: int in hurts.keys():
		if not seen.has(key):
			hurts.erase(key)


func _observe_grimjaw_hurt(owners: Array, dt: float, feel: HeroCombatFeel) -> void:
	if not enabled or budget <= 0.0:
		grimjaw_hurts.clear()
		return
	var seen: Dictionary = {}
	for candidate: Variant in owners:
		if not candidate is BattleUnit or candidate.unit_type != "grimjaw":
			continue
		var owner: BattleUnit = candidate
		var key := owner.get_instance_id()
		seen[key] = true
		if not grimjaw_hurts.has(key):
			grimjaw_hurts[key] = GrimjawHurt.new()
		var hurt: GrimjawHurt = grimjaw_hurts[key]
		var damaged := hurt.observe(owner.hp, owner.pos.x, owner.pos.y, dt)
		var died := hurt.observe_death(owner.alive)
		if damaged or died:
			if not systems.has(key):
				systems[key] = GrimjawParticlePool.new()
			var system: ZephyrParticlePool = systems[key]
			system.budget = budget
			if system is GrimjawParticlePool:
				system.glow_enabled = glow_enabled
			if damaged:
				var recipe := GrimjawHurt.hurt_recipe()
				system.burst(owner.pos.x, owner.pos.y - 10, int(recipe.count), recipe.options)
			if died:
				GrimjawHurt.ensure_loaded()
				for recipe: Dictionary in GrimjawHurt.config.death_recipes:
					system.burst(
						owner.pos.x + recipe.offset[0],
						owner.pos.y + recipe.offset[1],
						int(recipe.count),
						recipe.options
					)
				for request: Array in GrimjawHurt.config.death_feedback:
					feel.shake(request[0], request[1])

	for key: int in grimjaw_hurts.keys():
		if not seen.has(key):
			grimjaw_hurts.erase(key)


func draw(canvas: CanvasItem) -> void:
	if not enabled:
		return
	for manager: ZephyrVisualProjectileSystem in visual_projectiles.values():
		manager.draw(canvas)
	for system: ZephyrParticlePool in systems.values():
		system.draw(canvas, "front")
	for records: Array in skills.values():
		for skill: ZephyrSkill in records:
			if skill is GrimjawSkill:
				skill.glow_allowed = glow_enabled
			ZephyrBolt.draw_shapes(canvas, skill.front_commands(maxf(0.35, budget)))
	for events: Array in impacts.values():
		for impact: ZephyrImpact in events:
			impact.draw(canvas)

	for hurt: ZephyrHurt in hurts.values():
		ZephyrBolt.draw_shapes(canvas, hurt.commands())

	for hurt: GrimjawHurt in grimjaw_hurts.values():
		ZephyrBolt.draw_shapes(canvas, hurt.commands())


func capture_trails(owners: Array, now_ms: int) -> void:
	# Called AFTER simulation so attachment selection agrees with the body
	# drawn this frame, but uses the same once-per-timestamp real FX delta.
	if now_ms != last_ms or now_ms <= trail_ms:
		return
	trail_ms = now_ms
	if not enabled or fx_delta <= 0.0:
		return
	_capture_directors(owners)
	var seen: Dictionary = {}
	ZephyrSwingTrail.ensure_loaded()
	var scale := float(ZephyrSwingTrail.config.get("hero_scale", 1.0))
	for candidate: Variant in owners:
		if not candidate is BattleUnit:
			continue
		var owner: BattleUnit = candidate
		var key := owner.get_instance_id()
		var pose := ZephyrSwingTrail.pose_index(owner)
		var anchor := ZephyrSwingTrail.attachment(
			pose, [owner.pos.x, owner.pos.y], owner.facing, scale
		)
		var swinging := bool(anchor.get("swinging", false))
		if swinging:
			if not trails.has(key):
				trails[key] = {"trail": ZephyrSwingTrail.new(), "swinging": false, "timer": -1}
			var record: Dictionary = trails[key]
			var trail: ZephyrSwingTrail = record.trail
			if not bool(record.swinging) or owner.attack_anim_timer > int(record.timer):
				trail.reset()
			trail.push(anchor.inner, anchor.outer)
		if trails.has(key):
			trails[key].swinging = swinging
			trails[key].timer = owner.attack_anim_timer
			seen[key] = true
	for key: int in trails.keys():
		var record: Dictionary = trails[key]
		if not seen.has(key):
			record.swinging = false
		var trail: ZephyrSwingTrail = record.trail
		trail.update(fx_delta)
		if trail.points.is_empty() and not bool(record.swinging):
			trails.erase(key)


func _capture_directors(owners: Array) -> void:
	var seen: Dictionary = {}
	for candidate: Variant in owners:
		if not candidate is BattleUnit:
			continue
		var owner: BattleUnit = candidate
		if owner.kind != BattleUnit.Kind.HERO or owner.unit_type != "zephyr":
			continue
		var key := owner.get_instance_id()
		seen[key] = true
		if not directors.has(key):
			directors[key] = ZephyrDirectorState.new()
		var director: ZephyrDirectorState = directors[key]
		var progress := 0.0
		if owner.attack_anim_duration > 0:
			progress = 1.0 - float(owner.attack_anim_timer) / owner.attack_anim_duration
		var flash := 0.0
		if hurts.has(key):
			flash = hurts[key].hit_flash
		director.update(
			fx_delta,
			{
				"alive": owner.alive,
				"hit_flash": flash,
				"active_skill": owner.active_skill,
				"_zp_attack_active": owner.attack_anim_timer > 0,
				"_zp_attack_progress": progress,
				"_moving_cached": owner.is_moving,
				"speed": owner.speed,
				"x": owner.pos.x,
				"y": owner.pos.y,
				"facing": owner.facing
			}
		)
		for recipe: Dictionary in director.bursts:
			if budget <= 0.0:
				continue
			if not systems.has(key):
				systems[key] = ZephyrParticlePool.new()
			var pool: ZephyrParticlePool = systems[key]
			pool.budget = budget
			pool.burst(recipe.position[0], recipe.position[1], int(recipe.count), recipe.options)
	for key: int in directors.keys():
		if not seen.has(key):
			directors.erase(key)


func draw_ground(canvas: CanvasItem) -> void:
	if not enabled:
		return
	for system: ZephyrParticlePool in systems.values():
		system.draw(canvas, "back")
	for records: Array in skills.values():
		for skill: ZephyrSkill in records:
			ZephyrBolt.draw_shapes(canvas, skill.ground_commands(maxf(0.35, budget)))


func draw_trails(canvas: CanvasItem) -> void:
	if not enabled:
		return
	for record: Dictionary in trails.values():
		var trail: ZephyrSwingTrail = record.trail
		trail.draw(canvas)


func clear() -> void:
	for system: ZephyrParticlePool in systems.values():
		system.clear()
	systems.clear()
	trails.clear()
	impacts.clear()
	hurts.clear()
	grimjaw_hurts.clear()
	skills.clear()
	directors.clear()
	visual_projectiles.clear()
	last_ms = -1
	trail_ms = -1
	fx_delta = 0.0
