extends RefCounted
## Data parity is checked by level_catalog_source_oracle.py; native checks
## verify the Godot loader, unlock gate and next-level boundary.

const Catalog = preload("res://scripts/match/level_catalog.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const Session = preload("res://scripts/simulation/prototype_session.gd")


func run(check: Callable) -> void:
	var completed: Array[int] = []
	check.call(Catalog.get_level_config(0).is_empty(), "No level zero")
	check.call(Catalog.get_level_config(55).is_empty(), "No level 55")
	check.call(Catalog.get_next_level(54) == -1, "Level 54 has no successor")
	check.call(not Catalog.is_level_unlocked(55, completed), "Unknown level is locked")
	for number in range(1, Catalog.COUNT + 1):
		var config: Dictionary = Catalog.get_level_config(number)
		check.call(int(config.get("level_number", -1)) == number, "Catalog number %d" % number)
		check.call(not String(config.get("name", "")).is_empty(), "Catalog name %d" % number)
		check.call(not String(config.get("true_boss", "")).is_empty(), "Catalog boss %d" % number)
		check.call(
			Catalog.is_level_unlocked(number, completed) == (number == 1),
			"Level %d locked until predecessor is completed" % number
		)
		if number > 1:
			completed.append(number - 1)
		check.call(Catalog.is_level_unlocked(number, completed), "Level %d unlocks" % number)
		if number < Catalog.COUNT:
			check.call(Catalog.get_next_level(number) == number + 1, "Next level %d" % number)
	var economy_rows: Variant = JSON.parse_string(
		FileAccess.get_file_as_string("res://tests/fixtures/level_economy_source.json")
	)
	check.call(economy_rows is Array and economy_rows.size() == 162, "Source economy fixture")
	if economy_rows is Array:
		for row in economy_rows:
			var preview := World.new()
			check.call(preview.configure_level(int(row.level)), "Configure economy source level")
			preview.set_difficulty(String(row.difficulty))
			check.call(
				(
					preview.economy.gold[0] == int(row.gold)
					and preview.economy.opening[0] == int(row.gold)
				),
				"Source starting gold L%d %s" % [int(row.level), String(row.difficulty)]
			)
			check.call(
				is_equal_approx(preview.economy.income_per_second, float(row.passive)),
				"Source passive rate L%d %s" % [int(row.level), String(row.difficulty)]
			)
	# Selection is transactional: a bad ID or a late call cannot replace a
	# configured encounter. The playable scene remains on the default level 1.
	var world := World.new()
	check.call(world.level_number == 1, "Prototype defaults to level 1")
	check.call(world.configure_level(54), "Level 54 can be configured before setup")
	check.call(
		(
			world.level_config == Catalog.get_level_config(54)
			and world.ai_controller.policy.level_number == 54
			and world.ai_draft.level_number == 54
		),
		"Selected config and both AI policies stay in sync"
	)
	check.call(not world.configure_level(55), "Unknown encounter rejected")
	check.call(world.level_number == 54, "Rejected level leaves selection unchanged")
	check.call(
		world.economy.gold[0] == 6300 and world.economy.opening[0] == 6300,
		"Level 54 normal opening gold includes source level bonus"
	)
	check.call(is_equal_approx(world.economy.income_per_second, 18.9), "Level 54 passive income")
	world.set_difficulty("hard")
	check.call(
		world.economy.gold[0] == 4725 and world.economy.opening[0] == 4725,
		"Hard level 54 opening gold"
	)
	check.call(
		is_equal_approx(world.economy.income_per_second, 14.175), "Hard level 54 passive rate"
	)
	check.call(world.economy.is_balanced(), "Configured opening ledger remains balanced")
	world.reset_ai(19)
	check.call(
		world.ai_controller.policy.level_number == 54 and world.ai_draft.level_number == 54,
		"AI reset restores the configured encounter level"
	)
	check.call(world.setup_arena(), "Configured encounter can initialize")
	world.set_difficulty("easy")
	check.call(
		world.economy.gold[0] == 4725 and world.economy.opening[0] == 4725,
		"Live difficulty change cannot retroactively replace the opening ledger"
	)
	check.call(not world.configure_level(2), "Live encounter cannot switch levels")
	check.call(world.level_number == 54, "Rejected live switch preserves level")
	var session := Session.new()
	check.call(session.configure_level(2, "hard"), "Session accepts level before arena setup")
	var selected := session.world as World
	check.call(
		(
			selected.level_number == 2
			and selected.difficulty == "hard"
			and selected.economy.gold[0] == 825
			and selected.ai_draft.level_number == 2
		),
		"Session forwards level and difficulty before entering tree"
	)
	check.call(selected.setup_arena(), "Selected session can initialize arena")
	check.call(not session.configure_level(3), "Session cannot change a running encounter")
	check.call(selected.level_number == 2, "Rejected session switch preserves level")
