extends RefCounted

## Native pose selection, including cast restart independent of global frame.


static func run(runner) -> void:
	var unit := BattleUnit.new()
	runner.check(HeroVisuals.animation(unit) == "idle", "hero idle pose")
	unit.is_moving = true
	runner.check(HeroVisuals.animation(unit) == "walk", "hero walk pose")
	unit.attack_anim_timer = 3
	runner.check(HeroVisuals.animation(unit) == "attack", "hero attack overrides walk")
	runner.check(HeroVisuals.loop_frame([8, 8], 80, 6.0) == 8, "hero walk loops")
	runner.check(HeroVisuals.skill_frame([12, 6], 60, 60) == 12, "cast starts at first pose")
	runner.check(HeroVisuals.skill_frame([12, 6], 30, 60) == 15, "cast midpoint pose")
	runner.check(HeroVisuals.skill_frame([12, 6], 0, 60) == 17, "cast ends without wrapping")
	runner.check(HeroVisuals.skill_frame([12, 6], -5, 60) == 17, "expired cast clamps")
	runner.check(HeroVisuals.skill_frame([12, 6], 90, 60) == 12, "cast overflow clamps")
	unit.active_skill = "q"
	unit.active_skill_timer = 180
	unit.active_skill_timer = 90
	runner.check(unit.active_skill_duration == 180, "cast remembers original duration")
	unit.active_skill = "w"
	unit.active_skill_timer = 40
	runner.check(unit.active_skill_duration == 40, "new skill resets duration")
	unit.attack_anim_timer = 0
	unit.attack_anim_timer = 18
	runner.check(
		HeroVisuals.attack_frame([16, 8], unit) == 16, "Zephyr attack starts at first pose"
	)
	unit.attack_anim_timer = 9
	runner.check(unit.attack_anim_duration == 18, "attack duration survives timer decrements")
	runner.check(HeroVisuals.attack_frame([16, 8], unit) == 20, "Zephyr attack midpoint pose")
	unit.attack_anim_timer = 1
	runner.check(
		HeroVisuals.attack_frame([16, 8], unit) == 23, "Zephyr attack last pose without wrapping"
	)
