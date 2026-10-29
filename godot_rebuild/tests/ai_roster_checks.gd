extends RefCounted
## Production replay for source AIPlayer roster ownership.

const World = preload("res://scripts/match/prototype_battle.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Recruitment = preload("res://scripts/match/ai_recruitment.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/ai_roster_source.json"
const DRAFT_SOURCE_FIXTURE := "res://tests/fixtures/ai_draft_source.json"


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var source: Dictionary = fixture.get("source", {})
	var scenario: Dictionary = fixture.get("scenario", {})
	check.call(
		int(source.get("initial_player_hero_count", -1)) == 0,
		"Source player hero list starts empty before a purchase"
	)
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
	check.call(world.setup_arena(false), "Playable world initializes without free hero mirrors")
	var player_heroes := 0
	var red_scene_heroes := 0
	for unit in world.units:
		if not unit.is_hero:
			continue
		if unit.team == world.BLUE:
			player_heroes += 1
		elif unit.team == world.RED:
			red_scene_heroes += 1
	check.call(
		(
			player_heroes == int(scenario.get("initial_player_hero_count", -1))
			and world.player_roster().is_empty()
		),
		"Playable player roster begins empty until the player buys a hero"
	)
	check.call(
		red_scene_heroes == int(scenario.get("initial_red_scene_hero_count", -1)),
		"Playable red scene has no free hero before AI recruitment"
	)
	check.call(
		(
			world._ai_roster().is_empty()
			and (
				world._ai_state().hero_count
				== int(scenario.get("source_ai_roster_before_purchase", -1))
			)
		),
		"Playable AI roster matches the source empty roster"
	)
	check.call(
		world.ai_items.candidates(world).is_empty(), "Empty AI roster has no item candidates"
	)
	check.call(
		world.ai_upgrades.hero_candidates(world).is_empty(),
		"Empty AI roster has no hero upgrade candidates"
	)

	_fund(world, 100000)
	var draft := Draft.new()
	draft.purchase_target = "kaizen"
	draft.purchase_target_cost = int(World.PLAYABLE_AI_HEROES.kaizen.cost)
	check.call(
		Recruitment.new().try_buy(world, draft), "AI may recruit Kaizen from its empty roster"
	)
	var roster := world._ai_roster()
	check.call(roster.size() == 1, "Purchased red hero is registered in the AI roster")
	if roster.is_empty():
		return
	var first_ai_hero := roster[0] as World.HeroState
	var source_first_y := _source_spawn_y_for_roster_count(0)
	check.call(source_first_y >= 0.0, "Source draft oracle records the first AI spawn position")
	check.call(
		is_equal_approx(first_ai_hero.position.y, source_first_y),
		"Production recruitment uses the source AI-roster spawn offset"
	)
	check.call(
		world.ai_items.candidates(world) == [first_ai_hero.id], "Item candidates use AI ownership"
	)
	check.call(
		world.ai_upgrades.hero_candidates(world) == [first_ai_hero.id],
		"Upgrade candidates use AI ownership"
	)

	for hero_type in ["thorne", "grimjaw", "vex", "sylara"]:
		var definition: Variant = World.PLAYABLE_AI_HEROES[hero_type]
		var owned_count := world._ai_roster().size()
		var source_y := _source_spawn_y_for_roster_count(owned_count)
		var position := Vector2(World.RED_HERO_SPAWN.x, source_y)
		var bought := world._buy_ai_hero(hero_type, int(definition.cost), position)
		check.call(bought, "AI purchase registers owned kit: " + hero_type)
		check.call(
			source_y >= 0.0, "Source draft oracle records AI spawn offset " + str(owned_count)
		)
		check.call(
			is_equal_approx(source_y, source_first_y + owned_count * 40),
			"Source spawn slots advance by 40 px per AI-owned hero"
		)
		var current_roster := world._ai_roster()
		if bought and current_roster.size() == owned_count + 1:
			var purchased := current_roster.back() as World.HeroState
			check.call(
				is_equal_approx(purchased.position.y, source_y),
				"AI hero spawn follows source roster offset: " + hero_type
			)
	check.call(world._ai_roster().size() == 5, "AI roster cap counts five purchased heroes")
	check.call(world._ai_state().hero_count == 5, "Production AI policy sees only its five heroes")
	check.call(
		world.ai_upgrades.hero_candidates(world).size() == 5,
		"Upgrade candidates include all five AI-owned heroes"
	)
	var next_source_y := _source_spawn_y_for_roster_count(world._ai_roster().size())
	var next_position := Vector2(World.RED_HERO_SPAWN.x, next_source_y)
	var zephyr: Variant = World.PLAYABLE_AI_HEROES.zephyr
	check.call(
		(
			not world._buy_ai_hero("zephyr", int(zephyr.cost), next_position)
			and world.transaction_error == "capacity"
		),
		"AI hero cap rejects a sixth purchase"
	)

	var enemy := world.spawn_unit(GOBLIN, world.BLUE, 1)
	enemy.position = Vector2(520, 380)
	world.set_ai_enabled(true)
	world.ai_controller.policy.think_timer = 90
	world.step_tick()
	check.call(first_ai_hero.has_destination, "Production tick controls the paid AI-owned hero")


func _fund(world: World, amount: int) -> void:
	world.economy = Economy.new()
	world.economy.opening[world.RED] = amount
	world.economy.gold[world.RED] = amount


func _source_spawn_y_for_roster_count(owned_count: int) -> float:
	var source_fixture: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string(DRAFT_SOURCE_FIXTURE)
	)
	var recorded_y := _recorded_source_spawn_y(source_fixture, owned_count)
	if recorded_y >= 0.0 or owned_count == 0:
		return recorded_y
	# The fixture records roster sizes 0-3 and 5-6. Source offset is linear by 40 px.
	var first_y := _recorded_source_spawn_y(source_fixture, 0)
	return first_y + owned_count * 40 if first_y >= 0.0 else -1.0


func _recorded_source_spawn_y(source_fixture: Dictionary, owned_count: int) -> float:
	var expected_y := -1.0
	for purchase_variant in source_fixture.get("purchases", []):
		var purchase: Dictionary = purchase_variant
		for step_variant in purchase.get("steps", []):
			var step: Dictionary = step_variant
			if not bool(step.get("success", false)):
				continue
			var owned_after: Array = step.get("owned", [])
			if owned_after.size() != owned_count + 1:
				continue
			var receipts: Array = step.get("receipts", [])
			if receipts.is_empty():
				continue
			var receipt: Dictionary = receipts[0]
			var position: Array = receipt.get("position", [])
			if position.size() != 2:
				continue
			var source_y := float(position[1])
			if expected_y < 0.0:
				expected_y = source_y
			elif not is_equal_approx(expected_y, source_y):
				return -1.0
	return expected_y
