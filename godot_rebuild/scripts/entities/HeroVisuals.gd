class_name HeroVisuals
extends RefCounted

## Native pose selection for the sampled heroes/ strips. Live procedural FX
## remain outside this contract. Skill strips sample a complete cast timeline.


static func animation(unit: BattleUnit) -> String:
	if unit.attack_anim_timer > 0:
		return "attack"
	return "walk" if unit.is_moving else "idle"


static func loop_frame(span: Array, frame: int, fps: float) -> int:
	return int(span[0]) + maxi(0, int(frame * fps / 60.0)) % maxi(1, int(span[1]))


static func skill_frame(span: Array, remaining: int, duration: int) -> int:
	var count := maxi(1, int(span[1]))
	var progress := clampf(1.0 - float(remaining) / maxi(1, duration), 0.0, 1.0)
	return int(span[0]) + mini(count - 1, int(progress * count))


static func attack_frame(span: Array, unit: BattleUnit) -> int:
	# Zephyr body and staff attachments share one cast-local attack timeline.
	return skill_frame(span, unit.attack_anim_timer, unit.attack_anim_duration)
