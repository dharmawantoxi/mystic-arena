extends RefCounted

## Keep the main runner bounded as native hero migration suites grow.
const HeroVisualsTests := preload("res://tests/HeroVisualsTest.gd")
const HeroFeelTests := preload("res://tests/HeroCombatFeelTest.gd")
const HeroFeedbackTests := preload("res://tests/HeroFeedbackTest.gd")
const ZephyrBoltTests := preload("res://tests/ZephyrBoltTest.gd")
const ZephyrParticlesTests := preload("res://tests/ZephyrParticlesTest.gd")
const ZephyrTrailTests := preload("res://tests/ZephyrTrailTest.gd")
const GrimjawSkillTests := preload("res://tests/GrimjawSkillTest.gd")
const GrimjawHurtTests := preload("res://tests/GrimjawHurtTest.gd")
const ZephyrVisualProjectileTests := preload("res://tests/ZephyrVisualProjectileTest.gd")
const ZephyrDirectorTests := preload("res://tests/ZephyrDirectorTest.gd")
const ZephyrSkillTests := preload("res://tests/ZephyrSkillTest.gd")
const ZephyrImpactTests := preload("res://tests/ZephyrImpactTest.gd")


static func run(runner) -> void:
	HeroVisualsTests.run(runner)
	HeroFeelTests.run(runner)
	HeroFeedbackTests.run(runner)
	ZephyrBoltTests.run(runner)
	ZephyrParticlesTests.run(runner)
	ZephyrTrailTests.run(runner)
	GrimjawSkillTests.run(runner)
	GrimjawHurtTests.run(runner)
	ZephyrVisualProjectileTests.run(runner)
	ZephyrDirectorTests.run(runner)
	ZephyrSkillTests.run(runner)
	ZephyrImpactTests.run(runner)
