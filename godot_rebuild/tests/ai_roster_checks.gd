extends RefCounted
## Production replay for source AIPlayer roster ownership.

const World = preload("res://scripts/match/prototype_battle.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Recruitment = preload("res://scripts/match/ai_recruitment.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/ai_roster_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var source: Dictionary = fixture.get("source", {})
	var scenario: Dictionary = fixture.get("scenario", {})
	check.call(int(source.get("initial_ai_hero_count", -1)) == 0, "Source AI roster starts empty")
	check.call(
		bool(source.get("hero_cap_uses_ai_roster", false)), "Source hero cap reads AI roster"
	)
	check.call(bool(source.get("control_uses_ai_roster", false)), "Source control walks AI roster")
	check.call(
		bool(source.get("purchase_registers_ai_hero", false)), "Source purchases join AI roster"
	)
	check.call(
		bool(source.get("game_rosters_are_separate", false)), "Game keeps hero rosters separate"
	)
	_test_production_world(scenario, check)


func _test_production_world(scenario: Dictionary, check: Callable) -> void:
	var world := World.new()
	check.call(world.setup_arena(), "Production world initializes the mirrored hero pair")
	var free_red: World.HeroState = null
	for unit in world.units:
		if unit.is_hero and unit.team == world.RED:
			free_red = unit as World.HeroState
			break
	check.call(free_red != null, "Production setup has a free red mirrored Kaizen")
	if free_red == null:
		return
	check.call(free_red.definition.id == "kaizen", "Free red mirror identity remains Kaizen")
	check.call(
		world._red_hero_count() == int(scenario.get("free_red_scene_heroes", -1)),
		"Native counterfactual sees the prototype's free red hero"
	)
	check.call(
		int(scenario.get("native_old_ai_roster_before_purchase", -1)) == 1,
		"Old team-scan would count the free red mirror"
	)
	check.call(
		(
			world._ai_roster().is_empty()
			and (
				world._ai_state().hero_count
				== int(scenario.get("source_ai_roster_before_purchase", -1))
			)
		),
		"Production AI roster matches the source empty roster"
	)
	check.call(not world._ai_roster().has(free_red), "Free red Kaizen is not an AI-owned hero")
	check.call(
		world.ai_items.candidates(world).is_empty(), "Free mirror is not an AI item candidate"
	)
	check.call(
		world.ai_upgrades.hero_candidates(world).is_empty(),
		"Free mirror is not an AI upgrade candidate"
	)

	_fund(world, 100000)
	var draft := Draft.new()
	draft.purchase_target = "kaizen"
	draft.purchase_target_cost = int(World.PLAYABLE_AI_HEROES.kaizen.cost)
	check.call(
		Recruitment.new().try_buy(world, draft), "AI may buy Kaizen absent from its own roster"
	)
	var roster := world._ai_roster()
	check.call(roster.size() == 1, "Paid red hero is registered in the AI roster")
	if roster.is_empty():
		return
	var first_ai_hero := roster[0] as World.HeroState
	check.call(first_ai_hero.id != free_red.id, "Paid Kaizen stays distinct from the free mirror")
	check.call(
		world.ai_items.candidates(world) == [first_ai_hero.id], "Item candidates use AI ownership"
	)
	check.call(
		world.ai_upgrades.hero_candidates(world) == [first_ai_hero.id],
		"Upgrade candidates use AI ownership"
	)

	for hero_type in ["thorne", "grimjaw", "vex", "sylara"]:
		var definition: Variant = World.PLAYABLE_AI_HEROES[hero_type]
		var position := World.RED_HERO_SPAWN + Vector2(0, world._red_hero_count() * 40 - 40)
		check.call(
			world._buy_ai_hero(hero_type, int(definition.cost), position),
			"AI purchase registers owned kit: " + hero_type
		)
	check.call(world._ai_roster().size() == 5, "AI roster cap counts five purchased heroes")
	check.call(world._ai_state().hero_count == 5, "Production AI policy sees only its five heroes")
	check.call(
		world.ai_upgrades.hero_candidates(world).size() == 5,
		"Free mirror stays outside the complete upgrade roster"
	)
	var next_position := World.RED_HERO_SPAWN + Vector2(0, world._red_hero_count() * 40 - 40)
	var zephyr: Variant = World.PLAYABLE_AI_HEROES.zephyr
	check.call(
		(
			not world._buy_ai_hero("zephyr", int(zephyr.cost), next_position)
			and world.transaction_error == "capacity"
		),
		"Free mirror does not consume an AI hero-cap slot"
	)

	var enemy := world.spawn_unit(GOBLIN, world.BLUE, 1)
	enemy.position = Vector2(520, 380)
	world.set_ai_enabled(true)
	world.ai_controller.policy.think_timer = 90
	world.step_tick()
	check.call(first_ai_hero.has_destination, "Production tick controls the paid AI-owned hero")
	check.call(
		not free_red.has_destination, "Production tick leaves the free red mirror uncontrolled"
	)


func _fund(world: World, amount: int) -> void:
	world.economy = Economy.new()
	world.economy.opening[world.RED] = amount
	world.economy.gold[world.RED] = amount
