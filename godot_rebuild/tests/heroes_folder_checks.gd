extends RefCounted
## Whole `heroes/` folder coverage, proven from the source inventory.
##
## `tests/fixtures/heroes_folder_source.json` is derived from the 34 Pygame
## modules by `tests/heroes_folder_source_oracle.py`. This suite asks the native
## project to account for every part of the folder:
##
## * the folder inventory itself (34 files, 101.262 lines, 27 live-FX modules,
##   4 `_v1` pixel-art renderers);
## * the 27-hero live-FX registry and the twelve entry points every director
##   exposes (`scripts/ui/hero_fx_bus.gd`);
## * the combat-load governor behind it (`scripts/settings/fx_governor.gd`):
##   smoothing 0.40, one free hero, exponent 1.5, floor 0.10, spawn tokens
##   140/18/10 with refund floors 56/10/5;
## * the quality presets those knobs read (particle ratio 0.20/0.40/0.70, pose
##   floors 12/8/4 and 6/4/3, ground budget 2/3/6, full render 3/4/8);
## * the two bus rules that matter: a frame is never skipped, and an exhausted
##   ground budget only skips the drawing, never `attach` + `tick`;
## * the renderer half, which is baked rather than scripted: `data/art/heroes.json`
##   carries the six `HERO_RENDERERS` starters, the 8 animation phases and a
##   `hero_scale` for every hero inside the source clamp (0.40-1.70) x 0.78;
## * `combat_feel.py`'s hit-stop, which the FX directors request through and
##   which the source clamps up to 0.03 s (2 frozen steps at 60 Hz).

const HeroFxBus = preload("res://scripts/ui/hero_fx_bus.gd")
const FxGovernor = preload("res://scripts/settings/fx_governor.gd")
const HitStopRuntime = preload("res://scripts/match/hit_stop_runtime.gd")
const Battle = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/heroes_folder_source.json"
const HERO_MANIFEST := "res://data/art/heroes.json"

## Source `HERO_GLOBAL_SCALE`: the measured scale is always multiplied by this.
const HERO_GLOBAL_SCALE := 0.78


## A live-FX director stand-in: counts every contract call the bus makes.
class FakeDirector:
	var attaches := 0
	var ticks := 0
	var grounds := 0
	var lives := 0
	var resets := 0
	var allow_attach := true

	func attach(_unit: Variant) -> bool:
		attaches += 1
		return allow_attach

	func tick() -> void:
		ticks += 1

	func draw_ground_layer(_unit: Variant) -> void:
		grounds += 1

	func draw_live_layer(_unit: Variant) -> void:
		lives += 1

	func reset_all() -> void:
		resets += 1


## Unit stand-in for the Object branch of the bus attribute reader.
class FakeUnit:
	var hero_type := ""
	var boss_type := ""
	var active_skill := ""
	var attack_timer := 0
	var timer := 0
	var alive := true
	var projectiles: Array = []
	var _portrait_hd := false

	func _init(kind: String = "kaizen") -> void:
		hero_type = kind


func run(check: Callable) -> void:
	var source := _fixture()
	check.call(not source.is_empty(), "The heroes/ inventory fixture parses")
	if source.is_empty():
		return
	_check_folder(check, source)
	_check_registry(check, source)
	_check_governor_constants(check, source)
	_check_presets(check, source)
	_check_governor_math(check, source)
	_check_tokens(check, source)
	_check_frame(check)
	_check_ground_budget(check)
	_check_busy(check)
	_check_quantum(check, source)
	_check_baked_art(check, source)
	_check_hit_stop(check, source)


func _fixture() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


func _manifest() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(HERO_MANIFEST))
	return parsed if parsed is Dictionary else {}


func _sorted(values: Array) -> Array:
	var copy := values.duplicate()
	copy.sort()
	return copy


func _check_folder(check: Callable, source: Dictionary) -> void:
	var folder: Dictionary = source.get("folder", {})
	check.call(int(folder.get("files", 0)) == 34, "heroes/ holds 34 Python modules")
	check.call(int(folder.get("lines", 0)) == 101262, "heroes/ is 101.262 source lines")
	check.call(int(folder.get("fx_modules", 0)) == 27, "27 of those modules are live-FX directors")
	check.call(int(folder.get("v1_modules", 0)) == 4, "4 of those modules are _v1 pixel-art renderers")
	var per_file: Dictionary = folder.get("per_file_lines", {})
	check.call(per_file.size() == 34, "Every module has a recorded line count")
	check.call(
		int(per_file.get("__init__.py", 0)) == 3374,
		"heroes/__init__.py is the 3.374-line bus"
	)
	check.call(
		int(per_file.get("_bundle.py", 0)) == 16769,
		"heroes/_bundle.py is the 16.769-line bundle"
	)
	check.call(
		int(per_file.get("combat_feel.py", 0)) == 311,
		"heroes/combat_feel.py is the 311-line feel layer"
	)
	var fx: Dictionary = source.get("fx", {})
	check.call(fx.size() == 27, "Every live-FX module has an entry in the fixture")
	var lines := 0
	var defs := 0
	for name in fx:
		lines += int(fx[name].get("lines", 0))
		defs += int(fx[name].get("defs", 0))
	check.call(
		lines > 60000 and defs > 1300,
		"The 27 FX modules carry %d lines / %d functions" % [lines, defs]
	)


func _check_registry(check: Callable, source: Dictionary) -> void:
	var live: Dictionary = source.get("live_fx", {})
	var heroes: Array = live.get("heroes", [])
	check.call(heroes.size() == 27, "The source live-FX registry lists 27 heroes")
	check.call(
		_sorted(HeroFxBus.LIVE_FX_HEROES) == _sorted(heroes),
		"The native bus registers exactly the source 27 live-FX heroes"
	)
	check.call(
		HeroFxBus.FX_CONTRACT == live.get("contract", []),
		"The native bus declares the twelve source director entry points"
	)
	var paths: Dictionary = live.get("paths", {})
	var missing := 0
	for hero_id in heroes:
		if not paths.has(hero_id):
			missing += 1
	check.call(missing == 0, "Every live-FX hero has a source module path")
	check.call(
		HeroFxBus.has_live_fx("kaizen") and not HeroFxBus.has_live_fx("thorne_squire"),
		"The bus accepts live-FX heroes only"
	)
	check.call(
		HeroFxBus.has_live_fx("boss_gornak") == false and HeroFxBus.has_live_fx("gornak"),
		"Boss live-FX heroes are registered by plain id"
	)
	var fx_rows: Dictionary = source.get("fx", {})
	var core_missing := 0
	var attach_missing := 0
	for name in fx_rows:
		var gaps: Array = fx_rows[name].get("missing_api", [])
		if gaps.has("tick") or gaps.has("draw_ground_layer") or gaps.has("draw_live_layer"):
			core_missing += 1
		if gaps.has("attach"):
			attach_missing += 1
	check.call(core_missing == 0, "All 27 source directors expose tick plus both draw layers")
	check.call(
		attach_missing == 1,
		"attach() is optional in the source (only zephyr_fx.py omits it)"
	)


func _check_governor_constants(check: Callable, source: Dictionary) -> void:
	var governor: Dictionary = source.get("governor", {})
	check.call(
		is_equal_approx(FxGovernor.LOAD_SMOOTH, float(governor.get("load_smooth", 0.0))),
		"The governor smooths the load at 0.40 per frame"
	)
	check.call(
		is_equal_approx(FxGovernor.BASE_HEROES, float(governor.get("base_heroes", 0.0))),
		"One hero fights at full FX intensity"
	)
	check.call(
		is_equal_approx(FxGovernor.LOAD_MIN, float(governor.get("load_min", 0.0))),
		"The load floor is 0.10, never zero"
	)
	check.call(
		is_equal_approx(FxGovernor.LOAD_EXP, float(governor.get("load_exp", 0.0))),
		"The falloff exponent is 1.5"
	)
	check.call(
		FxGovernor.PARTICLE_CAP == int(governor.get("particle_cap", 0))
		and FxGovernor.PROJECTILE_CAP == int(governor.get("projectile_cap", 0))
		and FxGovernor.SKILL_PROJECTILE_CAP == int(governor.get("skill_projectile_cap", 0)),
		"The spawn token caps are 140 / 18 / 10"
	)
	check.call(
		FxGovernor.PARTICLE_FLOOR == int(governor.get("particle_floor", 0))
		and FxGovernor.PROJECTILE_FLOOR == int(governor.get("projectile_floor", 0))
		and FxGovernor.SKILL_PROJECTILE_FLOOR == int(governor.get("skill_projectile_floor", 0)),
		"The token floors are 56 / 10 / 5"
	)
	check.call(
		bool(governor.get("tokens_gated", false)),
		"The source gates spawn tokens behind an explicit frame-loop flag"
	)


func _check_presets(check: Callable, source: Dictionary) -> void:
	var governor: Dictionary = source.get("governor", {})
	var ratios: Dictionary = governor.get("particle_ratio", {})
	var skill_floors: Dictionary = governor.get("skill_quant_floor", {})
	var atk_floors: Dictionary = governor.get("atk_quant_floor", {})
	var ground: Dictionary = governor.get("ground_budget", {})
	var renders: Dictionary = governor.get("max_hero_render", {})
	for level in ["low", "medium", "high"]:
		FxGovernor.set_quality(level)
		check.call(
			is_equal_approx(FxGovernor.base_particle_ratio(), float(ratios.get(level, 0.0))),
			"The %s preset particle ratio is %.2f" % [level, float(ratios.get(level, 0.0))]
		)
		check.call(
			FxGovernor.skill_quant(0, 1) == int(skill_floors.get(level, 0)),
			"The %s preset skill pose floor is %d" % [level, int(skill_floors.get(level, 0))]
		)
		check.call(
			FxGovernor.atk_quant() == int(atk_floors.get(level, 0)),
			"The %s preset attack pose floor is %d" % [level, int(atk_floors.get(level, 0))]
		)
		check.call(
			FxGovernor.ground_budget() == int(ground.get(level, 0)),
			"The %s preset ground FX budget is %d" % [level, int(ground.get(level, 0))]
		)
		check.call(
			FxGovernor.max_hero_render() == int(renders.get(level, 0)),
			"The %s preset full-render budget is %d" % [level, int(renders.get(level, 0))]
		)
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)


func _check_governor_math(check: Callable, source: Dictionary) -> void:
	var governor: Dictionary = source.get("governor", {})
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)
	FxGovernor.reset_fx_load()
	check.call(is_equal_approx(FxGovernor.fx_load(), 1.0), "A fresh governor runs at full intensity")
	check.call(not FxGovernor.tokens_active(), "Tokens stay inactive until the first frame tick")

	FxGovernor.set_fx_load(1)
	check.call(is_equal_approx(FxGovernor.fx_load(), 1.0), "One hero keeps the load at 1.0")
	var full := FxGovernor.tokens()
	check.call(
		int(full["particle"]) == FxGovernor.PARTICLE_CAP
		and int(full["projectile"]) == FxGovernor.PROJECTILE_CAP
		and int(full["skill_projectile"]) == FxGovernor.SKILL_PROJECTILE_CAP,
		"At load 1.0 the frame gets every spawn token: %s" % str(full)
	)

	FxGovernor.reset_fx_load()
	FxGovernor.set_fx_load(5)
	var target: float = maxf(
		float(governor.get("load_min", 0.1)),
		pow(float(governor.get("base_heroes", 1.0)) / 5.0, float(governor.get("load_exp", 1.5)))
	)
	var expected := 1.0 + (target - 1.0) * float(governor.get("load_smooth", 0.4))
	check.call(
		is_equal_approx(FxGovernor.fx_load(), expected),
		"Five heroes smooth the load to %.4f, not straight to the floor" % expected
	)
	var loaded := FxGovernor.tokens()
	var ratio := maxf(float(governor.get("load_min", 0.1)), expected)
	check.call(
		int(loaded["particle"]) == maxi(FxGovernor.PARTICLE_FLOOR, int(FxGovernor.PARTICLE_CAP * ratio)),
		"Five heroes cut the particle tokens to %s" % str(int(loaded["particle"]))
	)

	for _i in range(80):
		FxGovernor.set_fx_load(5)
	check.call(
		is_equal_approx(FxGovernor.fx_load(), float(governor.get("load_min", 0.1))),
		"Sustained five-hero combat settles on the 0.10 floor"
	)
	var floor_tokens := FxGovernor.tokens()
	check.call(
		int(floor_tokens["particle"]) == FxGovernor.PARTICLE_FLOOR
		and int(floor_tokens["skill_projectile"]) == FxGovernor.SKILL_PROJECTILE_FLOOR,
		"At the floor the token floors hold: %s" % str(floor_tokens)
	)
	check.call(
		FxGovernor.particle_ratio() >= 0.07,
		"Even at the floor the preset ratio keeps FX visible: %.3f" % FxGovernor.particle_ratio()
	)
	FxGovernor.reset_fx_load()


func _check_tokens(check: Callable, source: Dictionary) -> void:
	var governor: Dictionary = source.get("governor", {})
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)
	FxGovernor.reset_fx_load()
	FxGovernor.set_fx_load(9)
	var available := int(FxGovernor.tokens()["particle"])
	check.call(
		available == maxi(FxGovernor.PARTICLE_FLOOR, int(FxGovernor.PARTICLE_CAP * FxGovernor.fx_load())),
		"Nine heroes refill the particle tokens from the smoothed load: %d" % available
	)
	var granted := 0
	while FxGovernor.claim_particle():
		granted += 1
		if granted > FxGovernor.PARTICLE_CAP + 1:
			break
	check.call(
		granted == available,
		"Draining the particle budget grants exactly the %d tokens of this frame" % available
	)
	check.call(not FxGovernor.claim_particle(), "An exhausted particle budget refuses more spawns")
	FxGovernor.refund_particle()
	check.call(FxGovernor.claim_particle(), "Refunding a refused spawn hands the token back")

	var projectile := 0
	while FxGovernor.claim_projectile():
		projectile += 1
		if projectile > FxGovernor.PROJECTILE_CAP + 1:
			break
	check.call(projectile > 0, "Projectile tokens drain like the source")
	FxGovernor.refund_projectile()
	check.call(FxGovernor.claim_projectile(), "Projectile tokens refund too")

	var skills := 0
	while FxGovernor.allow_skill_projectile():
		skills += 1
		if skills > FxGovernor.SKILL_PROJECTILE_CAP + 1:
			break
	check.call(
		skills >= FxGovernor.SKILL_PROJECTILE_FLOOR,
		"Skill projectiles use the one-way gate (%d granted)" % skills
	)
	check.call(
		not FxGovernor.allow_skill_projectile(),
		"The skill gate has no refund, like the source"
	)

	FxGovernor.reset_fx_load()
	check.call(
		FxGovernor.claim_particle() and not FxGovernor.tokens_active(),
		"Outside the frame loop spawns are never starved"
	)
	check.call(
		bool(governor.get("tokens_gated", false)) and FxGovernor.PARTICLE_CAP == 140,
		"The token gate is the source 140-token process-wide budget"
	)


func _check_frame(check: Callable) -> void:
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)
	HeroFxBus.reset_all()
	var before := HeroFxBus.fx_frame()
	var busy := HeroFxBus.begin_fx_frame(3)
	check.call(busy == 3 and HeroFxBus.busy_count() == 3, "The bus records the frame's busy count")
	check.call(HeroFxBus.fx_frame() == before + 1, "Every frame advances the FX frame counter")
	check.call(
		HeroFxBus.ground_budget_left() == FxGovernor.ground_budget(),
		"A new frame refills the ground budget from the preset"
	)
	HeroFxBus.begin_fx_frame(-4)
	check.call(HeroFxBus.busy_count() == 0, "A negative busy count clamps to zero")
	check.call(
		FxGovernor.tokens_active(),
		"The bus turns the spawn token gate on for the frame"
	)


func _check_ground_budget(check: Callable) -> void:
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)
	HeroFxBus.reset_all()
	var director := FakeDirector.new()
	var drawn := {"ground": false}
	check.call(HeroFxBus.register("kaizen", director), "A live-FX hero accepts a director")
	check.call(
		not HeroFxBus.register("thorne_squire", director),
		"Unknown heroes cannot be registered"
	)
	check.call(
		not HeroFxBus.register("vex", null),
		"A null director is refused instead of silently disabling the hero"
	)

	HeroFxBus.begin_fx_frame(1)
	var unit := {"hero_type": "kaizen"}
	var budget := FxGovernor.ground_budget()
	check.call(HeroFxBus.draw_ground("kaizen", unit), "The ground layer draws while budget remains")
	check.call(
		director.attaches == 1 and director.ticks == 1 and director.grounds == 1,
		"A ground draw attaches, ticks and paints in that order"
	)
	check.call(
		HeroFxBus.ground_budget_left() == budget - 1,
		"One ground draw spends exactly one budget slot"
	)

	var portrait := {"hero_type": "kaizen", "_portrait_hd": true}
	check.call(
		not HeroFxBus.draw_ground("kaizen", portrait) and director.grounds == 1,
		"HD portrait rendering opts out of the world FX layer"
	)
	check.call(
		not HeroFxBus.draw_ground("abaddon", unit) and director.grounds == 1,
		"A hero without a director stays silent instead of drawing"
	)
	check.call(
		not HeroFxBus.draw_ground("not_a_hero", unit) and director.grounds == 1,
		"Non live-FX ids never reach the directors"
	)

	# Spend the rest of the budget, then prove the simulation keeps ticking.
	while HeroFxBus.ground_budget_left() > 0:
		HeroFxBus.draw_ground("kaizen", unit)
	var grounds_at_budget := director.grounds
	var ticks_at_budget := director.ticks
	check.call(HeroFxBus.ground_budget_left() == 0, "The ground budget can be exhausted")
	check.call(
		not HeroFxBus.draw_ground("kaizen", unit),
		"No ground layer is painted once the budget is gone"
	)
	check.call(
		director.grounds == grounds_at_budget,
		"An exhausted budget skips the painting"
	)
	check.call(
		director.ticks == ticks_at_budget + 1 and director.attaches > 1,
		"An exhausted budget still attaches and ticks, so the skill FX keeps running"
	)
	check.call(
		HeroFxBus.draw_live("kaizen", unit) and director.lives == 1,
		"The live layer is never budget limited"
	)

	var mark_ground := func(_unit: Variant) -> void:
		drawn["ground"] = true
	var noop_tick := func() -> void:
		pass
	var loose: Dictionary = {
		"tick": noop_tick,
		"draw_ground_layer": mark_ground,
	}
	drawn["ground"] = false
	HeroFxBus.register("vex", loose)
	HeroFxBus.begin_fx_frame(1)
	check.call(
		HeroFxBus.draw_ground("vex", {"hero_type": "vex"}) and bool(drawn["ground"]),
		"A director without attach() (the source zephyr case) still draws"
	)

	director.allow_attach = false
	check.call(
		not HeroFxBus.draw_live("kaizen", unit) and director.lives == 1,
		"A director that refuses the unit is not asked to draw"
	)

	FxGovernor.set_quality(FxGovernor.LEVEL_LOW)
	HeroFxBus.begin_fx_frame(1)
	check.call(
		HeroFxBus.ground_budget_left() == 2,
		"The LOW preset only lets two heroes paint ground FX: %d" % HeroFxBus.ground_budget_left()
	)
	HeroFxBus.set_ground_effects_enabled(false)
	HeroFxBus.begin_fx_frame(1)
	check.call(
		HeroFxBus.ground_budget_left() == HeroFxBus.GROUND_BUDGET_UNLIMITED,
		"The MYSTIC_FX_GROUND=0 switch lifts the budget entirely"
	)
	HeroFxBus.set_ground_effects_enabled(true)

	HeroFxBus.reset_all()
	check.call(director.resets == 1, "reset_all clears every registered director")
	check.call(
		HeroFxBus.fx_frame() == 0 and HeroFxBus.ground_budget_left() == 99,
		"reset_all rewinds the frame state"
	)
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)


func _check_busy(check: Callable) -> void:
	check.call(
		HeroFxBus.is_busy({"active_skill": "q"}),
		"Casting counts as producing FX"
	)
	check.call(
		HeroFxBus.is_busy({"attack_timer": 3}) and not HeroFxBus.is_busy({"attack_timer": 0}),
		"A hero mid attack swing counts as producing FX"
	)
	check.call(
		HeroFxBus.is_busy({"timer": 2}),
		"A boss attack timer counts the same way as a hero attack timer"
	)
	check.call(
		HeroFxBus.is_busy({"projectiles": [{"alive": true}, {"alive": false}]}),
		"A live projectile counts as producing FX"
	)
	check.call(
		not HeroFxBus.is_busy({"projectiles": [{"alive": false}]}),
		"A dead projectile does not"
	)
	check.call(not HeroFxBus.is_busy({}), "An idle unit produces no FX")

	var object_unit := FakeUnit.new("vex")
	object_unit.active_skill = "e"
	check.call(
		HeroFxBus.is_busy(object_unit),
		"Object units (HeroState) are read through the same attribute probe"
	)
	object_unit.active_skill = ""
	object_unit.attack_timer = 0
	check.call(not HeroFxBus.is_busy(object_unit), "A cleared Object unit is idle again")

	var units := [
		{"hero_type": "kaizen", "active_skill": "q"},
		{"hero_type": "vex"},
		{"hero_type": "goblin", "active_skill": "q"},
		{"hero_type": "sylara", "attack_timer": 2, "alive": false},
		{"hero_type": "zephyr", "attack_timer": 2},
		{"boss_type": "gornak", "timer": 1},
	]
	check.call(
		HeroFxBus.count_busy_fx_heroes(units) == 3,
		"Only alive live-FX units that are producing FX count toward the governor: %d"
		% HeroFxBus.count_busy_fx_heroes(units)
	)
	check.call(
		HeroFxBus.count_busy_fx_heroes([{"hero_type": "goblin", "active_skill": "q"}]) == 0,
		"Minions never load the hero FX governor"
	)
	check.call(
		HeroFxBus.LIVE_FX_HEROES.size() == 27
		and HeroFxBus.pending_heroes().size() == 27 - HeroFxBus.registered_count(),
		"The unit filter runs on the same 27-hero registry as the bus (%d pending)"
		% HeroFxBus.pending_heroes().size()
	)


func _check_quantum(check: Callable, source: Dictionary) -> void:
	var ladder: Dictionary = source.get("skill_quant_ladder", {})
	var thresholds: Array = ladder.get("thresholds", [])
	check.call(thresholds == [2, 4, 6], "The source pose ladder breaks at 2 / 4 / 6 busy units")
	var source_quant := int(source.get("renderers", {}).get("scale", {}).get("skill_quant", 0))
	check.call(
		source_quant == HeroFxBus.HERO_SKILL_QUANT,
		"The bus carries the source HERO_SKILL_QUANT (%d)" % HeroFxBus.HERO_SKILL_QUANT
	)

	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)
	HeroFxBus.begin_fx_frame(1)
	check.call(
		HeroFxBus.skill_quant() == HeroFxBus.HERO_SKILL_QUANT,
		"A quiet fight animates at HERO_SKILL_QUANT (6), like the source ladder"
	)
	HeroFxBus.begin_fx_frame(3)
	check.call(HeroFxBus.skill_quant() == 4, "Three busy heroes animate at quantum 4")
	HeroFxBus.begin_fx_frame(5)
	check.call(HeroFxBus.skill_quant() == 8, "Five busy heroes coarsen to quantum 8")
	HeroFxBus.begin_fx_frame(9)
	check.call(HeroFxBus.skill_quant() == 12, "A big wave coarsens to quantum 12")
	check.call(
		HeroFxBus.skill_quant() != HeroFxBus.atk_quant(),
		"Skill and attack quanta are separate ladders, as in the source"
	)

	FxGovernor.set_quality(FxGovernor.LEVEL_LOW)
	HeroFxBus.begin_fx_frame(1)
	check.call(
		HeroFxBus.skill_quant() == 12,
		"The LOW preset raises the floor to quantum 12 even in a quiet fight"
	)
	FxGovernor.set_quality(FxGovernor.LEVEL_HIGH)
	HeroFxBus.begin_fx_frame(1)
	HeroFxBus.reset_all()


func _check_baked_art(check: Callable, source: Dictionary) -> void:
	var manifest := _manifest()
	check.call(not manifest.is_empty(), "The baked hero atlas manifest loads")
	if manifest.is_empty():
		return
	var scale: Dictionary = source.get("renderers", {}).get("scale", {})
	var starters: Array = source.get("renderers", {}).get("heroes", [])
	check.call(
		_sorted(manifest.get("non_boss", [])) == _sorted(starters),
		"The six HERO_RENDERERS starters are the six baked non-boss atlases"
	)
	check.call(
		int(manifest.get("phases", 0)) == int(scale.get("anim_phases", 0)),
		"The atlas bakes the source's 8 animation phases"
	)
	check.call(
		int(manifest.get("heroes", []).size()) >= 222,
		"The atlas covers the whole hero roster (%d heroes)" % int(manifest.get("heroes", []).size())
	)

	# Documented deviation: the atlas is a fixed-granularity bake. Pygame picks
	# the pose quantum per frame from the busy count (4/6 above), Godot samples a
	# fixed 3 attack / 2 skill grid and keeps it for the whole match.
	check.call(
		int(manifest.get("atk_quant", 0)) == 3 and int(manifest.get("skill_quant", 0)) == 2,
		"The bake keeps the documented fixed quanta 3 / 2"
	)
	check.call(
		int(scale.get("atk_quant", 0)) == 4 or int(scale.get("skill_quant", 0)) == 6,
		"The source constants (atk 4 / skill 6) are recorded as the un-baked values"
	)

	var lo := float(scale.get("clamp_min", 0.0)) * HERO_GLOBAL_SCALE
	var hi := float(scale.get("clamp_max", 0.0)) * HERO_GLOBAL_SCALE
	var meta: Dictionary = manifest.get("meta", {})
	var outside := 0
	var missing_v1 := 0
	for hero_id in meta:
		var value := float(meta[hero_id].get("hero_scale", 0.0))
		if value <= 0.0 or value < lo - 0.0001 or value > hi + 0.0001:
			outside += 1
	for name in source.get("v1", {}):
		var hero_id := String(name).trim_suffix("_v1.py")
		if not meta.has(hero_id):
			missing_v1 += 1
	check.call(
		outside == 0,
		"Every baked hero_scale sits inside the source clamp 0.40-1.70 x 0.78: %d outside" % outside
	)
	check.call(
		missing_v1 == 0,
		"All four _v1 pixel-art renderers are baked into the manifest as hero_scale entries"
	)
	check.call(
		is_equal_approx(
			float(meta.get("kaizen", {}).get("hero_scale", 0.0)),
			0.4970588235294118
		),
		"Kaizen keeps the baked V1 renderer scale 0.4971"
	)


func _check_hit_stop(check: Callable, source: Dictionary) -> void:
	var feel: Dictionary = source.get("combat_feel", {})
	var hit_stop: Dictionary = feel.get("hit_stop", {})
	check.call(
		is_equal_approx(HitStopRuntime.MIN_SECONDS, float(hit_stop.get("MIN_SECONDS", 0.0)))
		and is_equal_approx(HitStopRuntime.MAX_SECONDS, float(hit_stop.get("MAX_SECONDS", 0.0))),
		"The native hit stop clamps to the source 0.03-0.08 s window"
	)
	check.call(
		HitStopRuntime.MAX_FRAMES == int(hit_stop.get("MAX_FRAMES", 0)),
		"The source caps a freeze at 5 simulation steps"
	)
	check.call(
		is_equal_approx(HitStopRuntime.FIXED_DT, float(feel.get("constants", {}).get("FIXED_DT", 0.0))),
		"Both sides convert seconds to frames at 1/60 s"
	)

	# The FX directors ask for less than the floor: kaizen Q 0.021 s, vex W 0.025 s.
	var runtime := HitStopRuntime.new()
	runtime.trigger(0.021)
	var frozen := 0
	while runtime.consume_frame():
		frozen += 1
		if frozen > HitStopRuntime.MAX_FRAMES + 1:
			break
	check.call(
		frozen == 2,
		"A 0.021 s FX request is clamped up to the 0.03 s floor = 2 frozen steps (%d)" % frozen
	)
	var long_runtime := HitStopRuntime.new()
	long_runtime.trigger(0.08)
	var long_frozen := 0
	while long_runtime.consume_frame():
		long_frozen += 1
		if long_frozen > HitStopRuntime.MAX_FRAMES + 1:
			break
	check.call(
		long_frozen == HitStopRuntime.MAX_FRAMES,
		"An 0.08 s request hits the 5-step cap (%d)" % long_frozen
	)

	# The four ported FX directors' own hit-stop requests live in the battle.
	var battle := Battle.new()
	check.call(
		battle.SOURCE_CAST_HIT_STOP_SECONDS.size() == 4,
		"The four ported FX directors contribute their hit-stop requests"
	)
	for hero_id in ["kaizen", "grimjaw", "sylara", "vex"]:
		check.call(
			battle.SOURCE_CAST_HIT_STOP_SECONDS.has(hero_id),
			"FX director requests are recorded for %s" % hero_id
		)
	var out_of_window := 0
	for hero_id in battle.SOURCE_CAST_HIT_STOP_SECONDS:
		var requests: Dictionary = battle.SOURCE_CAST_HIT_STOP_SECONDS[hero_id]
		for slot in requests:
			var seconds := float(requests[slot])
			if seconds <= 0.0 or seconds > float(hit_stop.get("MAX_SECONDS", 0.0)):
				out_of_window += 1
	check.call(
		out_of_window == 0,
		"Every recorded FX hit-stop request is a real sub-floor request the clamp lifts to 0.03 s"
	)
