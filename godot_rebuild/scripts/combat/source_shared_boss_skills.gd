extends RefCounted
## Port of the REAL source BossHeroSkills._fallback_cast for a closed audited list.
## NEVER a fallback for missing native kits. Source recipe membership is CI-locked.
const Common = preload("res://scripts/combat/skill_common.gd")
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Membership = preload("res://scripts/data/source_shared_boss_ids.gd")
const IDS = Membership.IDS


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if hero == null or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var mult: float = {"q": 1.0, "w": 1.2, "e": 1.5, "r": 2.5}[key]
	if key in ["q", "w"]:
		Common.hit(world, hero, Common.current(world, hero), mult, true)
	else:
		var radius := 150.0 if key == "e" else 200.0
		for enemy in Common.enemies(world, hero, structures):
			if hero.position.distance_to(enemy.position) <= radius:
				Common.hit(world, hero, enemy, mult, true)
	# _generic_cast triggers BaseSkill cooldown AFTER the source fallback:
	# source fallback's temporary visual=40 is overwritten by these durations.
	Common.trigger(hero, key, {"q": 60, "w": 90, "e": 60, "r": 100}[key])
	return true
