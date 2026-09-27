extends RefCounted
## BossHeroSkills registry recipes for the two level-three unlocks ONLY.
## Not _fallback_cast; unported boss IDs remain rejected.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const Shapes = preload("res://scripts/combat/boss_recipe_shapes.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["ancient_apparition", "nyzrak"]
# Source BOSS_HERO_VISUAL_DURATION; every other ID keeps BaseSkill defaults.
const VISUAL := {"nyzrak": {"q": 50, "w": 50, "e": 70, "r": 90}}
const DEFAULT_VISUAL := {"q": 60, "w": 90, "e": 60, "r": 100}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match hero.settings().id:
		"ancient_apparition":
			_apparition(world, hero, target, key, structures)
		"nyzrak":
			_nyzrak(world, hero, target, key, structures)
	# Source generic cooldown trigger overwrites each recipe's visual duration.
	Common.trigger(hero, key, VISUAL.get(hero.settings().id, DEFAULT_VISUAL)[key])
	return true


static func tick(world, hero: HeroState, structures: Array) -> void:
	# Real BossHeroSkills.update_timers vortex DOT. Only Ancient Apparition's
	# recipe arms it, so it stays inert for every other boss ID.
	if hero.vortex_active_timer <= 0:
		return
	hero.vortex_active_timer -= 1
	if hero.vortex_active_timer % 20 == 0:
		Shapes.burst(world, hero, structures, hero.vortex, 80.0, 0.3, 0.5, 60)


static func _apparition(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			hero.vortex = target.position if target != null else hero.position + Vector2(100, 0)
			hero.vortex_active_timer = 180
			Shapes.burst(world, hero, structures, hero.vortex, 80.0, 0.6)
		"w":
			var direction := Shapes.line(
				world, hero, structures, target, 400.0, 30.0, 1.5, 0.6, 180
			)
			# The source keeps its previous direction when the recipe returns early.
			if direction != Vector2.ZERO:
				hero.w_dir = direction
		"e":
			if target != null:
				Common.hit(world, hero, target, 2.5)
				Common.stun(target, 90)
		"r":
			var direction := Shapes.line(
				world, hero, structures, target, 500.0, 60.0, 3.0, 0.7, 240
			)
			if direction != Vector2.ZERO:
				hero.r_dir = direction


static func _nyzrak(world, hero: HeroState, target, key: String, structures: Array) -> void:
	var origin: Vector2 = target.position if target != null else hero.position
	match key:
		"q":
			Shapes.beam(world, hero, structures, origin, 240.0, 26.0, 1.2, 0.4, 120)
		"w":
			Shapes.burst(world, hero, structures, origin, 80.0, 1.0, 0.3, 60)
		"e":
			if target != null:
				Common.hit(world, hero, target, 1.1)
				Common.stun(target, 90)
				world.apply_slow(target.id, 0.7, 180)
		"r":
			# Source flags only: Hero has no shield pool, absorb or mitigation
			# consumer, so this grants nothing. Recorded, never invented.
			hero.shield_active = true
			hero.shield_timer = 240
			Shapes.burst(world, hero, structures, hero.position, 200.0, 2.0, 0.5, 180)
			Shapes.heal(hero, int(hero.max_hp * 0.15))
