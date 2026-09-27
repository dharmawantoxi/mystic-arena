extends RefCounted
## Boss level 3 recipes: Ancient Apparition + Nyzrak.
## Exact source BossHeroSkills.* ports, not _fallback_cast.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["ancient_apparition", "nyzrak"]
const VISUAL := {
	"ancient_apparition": {"q": 60, "w": 45, "e": 50, "r": 90},
	"nyzrak": {"q": 50, "w": 50, "e": 70, "r": 90}
}


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
			_aa(world, hero, target, key, structures)
		"nyzrak":
			_nyz(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _aa(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Vortex at target, else x+100. Timer 180, initial burst 0.6*skill r80.
			if target != null:
				hero.vortex_origin = target.position
			else:
				hero.vortex_origin = hero.position + Vector2(100, 0)
			hero.vortex_timer = 180
			for enemy in Common.enemies(world, hero, structures):
				if hero.vortex_origin.distance_to(enemy.position) <= 80:
					Common.hit(world, hero, enemy, 0.6)
		"w":
			if target == null:
				return
			var dir: Vector2 = (target.position - hero.position).normalized()
			var max_range := 400.0
			var width := 30.0
			for enemy in Common.enemies(world, hero, structures):
				var ex: float = enemy.position.x - hero.position.x
				var ey: float = enemy.position.y - hero.position.y
				var proj: float = ex * dir.x + ey * dir.y
				if proj > 0 and proj < max_range:
					var perp: float = absf(ex * -dir.y + ey * dir.x)
					if perp < width:
						Common.hit(world, hero, enemy, 1.5)
						world.apply_slow(enemy.id, 0.6, 180)
		"e":
			if target == null:
				return
			Common.hit(world, hero, target, 2.5)
			Common.stun(target, 90)
		"r":
			if target == null:
				return
			var dir: Vector2 = (target.position - hero.position).normalized()
			var max_range := 500.0
			var width := 60.0
			for enemy in Common.enemies(world, hero, structures):
				var ex: float = enemy.position.x - hero.position.x
				var ey: float = enemy.position.y - hero.position.y
				var proj: float = ex * dir.x + ey * dir.y
				if proj > 0 and proj < max_range:
					var perp: float = absf(ex * -dir.y + ey * dir.x)
					if perp < width:
						Common.hit(world, hero, enemy, 3.0)
						world.apply_slow(enemy.id, 0.7, 240)


static func _nyz(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# Arctic Burn: beam 240 width 26 from hero towards target, damage 1.2 slow 0.4 120.
			var dir: Vector2
			if target != null:
				dir = (target.position - hero.position).normalized()
			else:
				dir = Vector2(1, 0)
			var max_range := 240.0
			var width := 26.0
			for enemy in Common.enemies(world, hero, structures):
				var ex: float = enemy.position.x - hero.position.x
				var ey: float = enemy.position.y - hero.position.y
				var proj: float = ex * dir.x + ey * dir.y
				if proj > 0 and proj < max_range:
					var perp: float = absf(ex * -dir.y + ey * dir.x)
					if perp < width:
						Common.hit(world, hero, enemy, 1.2)
						world.apply_slow(enemy.id, 0.4, 120)
		"w":
			var origin: Vector2 = target.position if target != null else hero.position
			for enemy in Common.enemies(world, hero, structures):
				if origin.distance_to(enemy.position) <= 80:
					Common.hit(world, hero, enemy, 1.0)
					world.apply_slow(enemy.id, 0.3, 60)
		"e":
			if target == null:
				return
			Common.hit(world, hero, target, 1.1)
			Common.stun(target, 90)
			world.apply_slow(target.id, 0.7, 180)
		"r":
			hero.shield_active = true
			hero.shield_timer = 240
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= 200:
					Common.hit(world, hero, enemy, 2.0)
					world.apply_slow(enemy.id, 0.5, 180)
			hero.heal_hp(int(hero.max_hp * 0.15))


static func tick(world, hero: HeroState, structures: Array) -> void:
	# Ancient Apparition vortex DOT: every 20 ticks damage 0.3 + slow 0.5 60 within 80.
	# Source BossHeroSkills.update_timers decrements vortex timer and DOTs every 20.
	if hero.vortex_timer > 0:
		hero.vortex_timer -= 1
		if hero.vortex_timer % 20 == 0:
			for enemy in Common.enemies(world, hero, structures):
				if hero.vortex_origin.distance_to(enemy.position) <= 80:
					Common.hit(world, hero, enemy, 0.3)
					world.apply_slow(enemy.id, 0.5, 60)
	# Nyzrak shield: source hero sets shield_active True timer 240 but update_timers
	# does NOT decrement it (quirk). Audit shows no mitigation consumer for
	# shield_active in Hero — do not invent shield absorption, do not expire.
	# Preserve exact source behavior: timer stays 240, active stays True.
