extends RefCounted
## Source `_boss_cache_key` pose selection for the baked animated boss bodies.
## BossState owns the gameplay clocks; this read-only helper only names their atlas pose.

const BossArt = preload("res://scripts/ui/boss_art.gd")
const PHASES := 8


static func pose_key(
	boss_type: String,
	timer: int,
	active_skill: String,
	active_skill_timer: int,
	moving: bool,
	pulse: float
) -> String:
	var facts: Dictionary = BossArt.entries().get(boss_type, {})
	if not active_skill.is_empty():
		var skill_quant := maxi(1, int(facts.get("skill_quant", 1)))
		return (
			"skill_%s_%d" % [active_skill, floori(float(active_skill_timer) / float(skill_quant))]
		)
	if timer > 0:
		var attack_quant := maxi(1, int(facts.get("attack_quant", 1)))
		return "atk%d" % floori(float(timer) / float(attack_quant))
	return "%s%d" % ["walk" if moving else "idle", int(pulse * 2.0) % PHASES]


static func from_boss(boss) -> String:
	return pose_key(
		boss.boss_type,
		boss.timer,
		boss.active_skill,
		boss.active_skill_timer,
		boss.moving_cached,
		boss.pulse
	)
