extends RefCounted
## Cast feedback of the source `BaseSkill` (`hero_skills/_bundle.py:141-152`,
## `:297-323`): every successful `cast_*` ends in `_trigger_{q,w,e,r}_cooldown`,
## which after the cooldown and the visual duration calls `_shake_screen` and
## `_play_skill_sound`. Both are global: the shake fires for either team, the
## sound only for the blue one.
##
## The intensities are per call site, not per slot:
##
## * `BaseSkill` defaults 8/5/6/15, which five of the six starter kits pass;
## * `ThorneSkills` passes 6 for Q and 8 for E (the source swaps the pair);
## * `BossHeroSkills.cast_*` passes 10/8/8/15 for all 216 boss heroes, so a boss
##   hero played by the player shakes differently from a starter.
##
## Volumes are the `_play_skill_sound(volume=...)` defaults 0.7/0.6/0.7/1.0,
## folded by the sound manager as master*sfx*volume_mult like the source.

const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")

const BLUE := 0
const SOUND := "hero_skill"

## `BaseSkill._trigger_*_cooldown(shake_amount=...)` defaults.
const DEFAULT_SHAKE := {"q": 8, "w": 5, "e": 6, "r": 15}
## `BossHeroSkills.cast_q/w/e/r` pass their own amounts to `_generic_cast`.
const BOSS_SHAKE := {"q": 10, "w": 8, "e": 8, "r": 15}
## Starter kits name their amount per call; only thorne deviates from the base.
const STARTER_SHAKE := {
	"kaizen": {"q": 8, "w": 5, "e": 6, "r": 15},
	"grimjaw": {"q": 8, "w": 5, "e": 6, "r": 15},
	"sylara": {"q": 8, "w": 5, "e": 6, "r": 15},
	"thorne": {"q": 6, "w": 5, "e": 8, "r": 15},
	"vex": {"q": 8, "w": 5, "e": 6, "r": 15},
	"zephyr": {"q": 8, "w": 5, "e": 6, "r": 15},
}
## `_play_skill_sound(volume=...)` of the four triggers.
const VOLUME := {"q": 0.7, "w": 0.6, "e": 0.7, "r": 1.0}


## The shake the source applies for this hero and slot.
static func shake_for(hero, key: String) -> int:
	if hero == null:
		return 0
	var definition = hero.settings()
	var hero_id := String(definition.id)
	if STARTER_SHAKE.has(hero_id):
		return int((STARTER_SHAKE[hero_id] as Dictionary).get(key, 0))
	if bool(definition.is_boss_hero):
		return int(BOSS_SHAKE.get(key, 0))
	return int(DEFAULT_SHAKE.get(key, 0))


## The `volume_mult` the source passes to `SoundManager.play`.
static func volume_for(key: String) -> float:
	return float(VOLUME.get(key, 0.0))


## Plays the same two effects the source trigger does and reports them, so a
## headless suite can assert the choice without an audio device.
static func apply(world, hero, key: String) -> Dictionary:
	var result := {"shake": 0, "volume": 0.0, "sound": false}
	if hero == null:
		return result
	var intensity := shake_for(hero, key)
	result["shake"] = intensity
	if world != null and intensity > 0:
		var effects = world.get("effects")
		if effects != null and effects.has_method("shake_screen"):
			effects.shake_screen(float(intensity))
	if int(hero.team) != BLUE:
		return result
	var volume := volume_for(key)
	result["volume"] = volume
	result["sound"] = AudioRuntime.play_scaled(SOUND, volume)
	return result
