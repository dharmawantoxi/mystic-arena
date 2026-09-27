extends RefCounted
## Boss level 4: Ignis Drachorn.
## Exact source BossHeroSkills.* ports.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["ignis_drachorn"]
const VISUAL := {"ignis_drachorn": {"q": 60, "w": 90, "e": 60, "r": 100}}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match key:
		"q":
			_q(world, hero, target, structures)
		"w":
			_w(world, hero, structures)
		"e":
			_e(world, hero)
		"r":
			_r(world, hero, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _q(world, hero: HeroState, target, structures: Array) -> void:
	# Dragon Breath cone 250 width 60 scaled 0.3+proj/max*0.7 dmg1.6 stun 45 (attack_timer)
	if target == null:
		return
	var dir: Vector2 = (target.position - hero.position).normalized()
	if dir == Vector2.ZERO:
		return
	var max_range := 250.0
	var cone_width := 60.0
	for enemy in Common.enemies(world, hero, structures):
		var ex: float = enemy.position.x - hero.position.x
		var ey: float = enemy.position.y - hero.position.y
		var proj: float = ex * dir.x + ey * dir.y
		if proj > 0 and proj < max_range:
			var perp: float = absf(ex * -dir.y + ey * dir.x)
			var allowed: float = cone_width * (0.3 + proj / max_range * 0.7)
			if perp < allowed:
				Common.hit(world, hero, enemy, 1.6)
				Common.stun(enemy, 45)


static func _w(world, hero: HeroState, structures: Array) -> void:
	# Dragon Tail 360 AOE 130 dmg1.9 stun60
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= 130:
			Common.hit(world, hero, enemy, 1.9)
			Common.stun(enemy, 60)


static func _e(_world, hero: HeroState) -> void:
	# Dragon Blood buff 480 + damage 1.3*base + heal 20%
	hero.dragon_blood_active = true
	hero.dragon_blood_timer = 480
	var base: int = hero.settings().catalog_damage
	hero.damage = int(base * 1.3)
	hero.heal_hp(int(hero.max_hp * 0.20))


static func _r(world, hero: HeroState, structures: Array) -> void:
	# Elder Dragon Form 600 timer, damage 1.8*base, AOE 220 dmg3.0 stun90 heal25%
	hero.dragon_form_active = true
	hero.dragon_form_timer = 600
	var base: int = hero.settings().catalog_damage
	hero.damage = int(base * 1.8)
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= 220:
			Common.hit(world, hero, enemy, 3.0)
			Common.stun(enemy, 90)
	hero.heal_hp(int(hero.max_hp * 0.25))


static func tick(_world, hero: HeroState, _structures: Array) -> void:
	# Source update_timers: dragon_form decrements and resets damage
	# on expiry; dragon_blood decrements but does NOT reset (quirk).
	if hero.dragon_form_active:
		hero.dragon_form_timer -= 1
		if hero.dragon_form_timer <= 0:
			hero.dragon_form_active = false
			hero.damage = hero.settings().catalog_damage
	if hero.dragon_blood_active:
		hero.dragon_blood_timer -= 1
		if hero.dragon_blood_timer <= 0:
			hero.dragon_blood_active = false
			# Intentionally do NOT reset damage — source quirk: only dragon_form resets
