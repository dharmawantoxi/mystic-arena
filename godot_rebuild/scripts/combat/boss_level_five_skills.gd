extends RefCounted
## Boss level 5: Krobellus (L5 True Boss) + Vhalzun (L5 mini boss unlock).
## Exact ports of BossHeroSkills._cast_{q,w,e,r}_krobellus_* and
## _cast_{q,w,e,r}_vhalzun_* from hero_skills/_bundle.py. Both IDs own four
## registry methods, so they never join the 150-ID `_fallback_cast` group.
const BossCommon = preload("res://scripts/combat/boss_skill_common.gd")
const Common = preload("res://scripts/combat/skill_common.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const IDS := ["krobellus", "vhalzun"]
# Source: BaseSkill._trigger_*_cooldown runs AFTER the recipe body, so the
# final active_skill_timer is _get_visual_duration(key), never the value the
# recipe assigned. BossHeroSkills.BOSS_HERO_VISUAL_DURATION overrides vhalzun
# (60/80/60/100); krobellus keeps _DEFAULT_VISUAL_DURATION (60/90/60/100).
const VISUAL := {
	"krobellus": {"q": 60, "w": 90, "e": 60, "r": 100},
	"vhalzun": {"q": 60, "w": 80, "e": 60, "r": 100}
}
# Exact recipe radii, locked by the oracle edges. 0.0 = single-target slot.
const RADIUS := {
	"krobellus": {"q": 150.0, "w": 120.0, "e": 0.0, "r": 200.0},
	"vhalzun": {"q": 130.0, "w": 150.0, "e": 0.0, "r": 150.0}
}
# W is the only slot that touches an enemy attack clock (max, never shortens).
const SILENCE_TICKS := {"krobellus": 75, "vhalzun": 60}


static func can_cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not Common.ready(world, hero, key) or hero.settings().id not in IDS:
		return false
	return BossCommon.can_cast(world, hero, key, structures)


static func cast(world, hero: HeroState, key: String, structures: Array) -> bool:
	if not can_cast(world, hero, key, structures):
		return false
	var target = Common.current(world, hero)
	match hero.settings().id:
		"krobellus":
			_krobellus(world, hero, target, key, structures)
		"vhalzun":
			_vhalzun(world, hero, target, key, structures)
	Common.trigger(hero, key, VISUAL[hero.settings().id][key])
	return true


static func _krobellus(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# _cast_q_krobellus_exorcism: radial 150, 1.5*skill, no clock/slow.
			_radial(world, hero, structures, "q", 1.5)
		"w":
			# _cast_w_krobellus_silence: radial 120, 1.0*skill + attack clock 75.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= RADIUS["krobellus"]["w"]:
					Common.hit(world, hero, enemy, 1.0)
					Common.stun(enemy, SILENCE_TICKS["krobellus"])
		"e":
			# _cast_e_krobellus_siphon(h): target 1.3*skill, self heal 0.5*skill.
			if target == null:
				return
			Common.hit(world, hero, target, 1.3)
			hero.heal_hp(int(hero.skill_damage() * 0.5))
		"r":
			# _cast_r_krobellus_crypt: radial 200, 2.5*skill + heal 15% max_hp.
			_radial(world, hero, structures, "r", 2.5)
			hero.heal_hp(int(hero.max_hp * 0.15))


static func _vhalzun(world, hero: HeroState, target, key: String, structures: Array) -> void:
	match key:
		"q":
			# _cast_q_vhalzun_death_pulse: radial 130, 1.5*skill.
			_radial(world, hero, structures, "q", 1.5)
		"w":
			# _cast_w_vhalzun_heartstopper: radial 150, 1.0*skill + clock 60.
			for enemy in Common.enemies(world, hero, structures):
				if hero.position.distance_to(enemy.position) <= RADIUS["vhalzun"]["w"]:
					Common.hit(world, hero, enemy, 1.0)
					Common.stun(enemy, SILENCE_TICKS["vhalzun"])
		"e":
			# _cast_e_vhalzun_reapers_scythe: single target 1.8*skill, no heal.
			if target == null:
				return
			Common.hit(world, hero, target, 1.8)
		"r":
			# _cast_r_vhalzun_ghost_shroud: radial 150, 1.4*skill + heal 18% max_hp.
			_radial(world, hero, structures, "r", 1.4)
			hero.heal_hp(int(hero.max_hp * 0.18))


static func _radial(
	world, hero: HeroState, structures: Array, key: String, multiplier: float
) -> void:
	var radius: float = RADIUS[hero.settings().id][key]
	for enemy in Common.enemies(world, hero, structures):
		if hero.position.distance_to(enemy.position) <= radius:
			Common.hit(world, hero, enemy, multiplier)

## No per-frame source state: BossHeroSkills.update_timers only ticks
## rage/defense/vortex/flux/clones/dragon fields and neither level-5 recipe
## sets one of them, so the shared boss timers stay 0 (oracle traces lock it).
