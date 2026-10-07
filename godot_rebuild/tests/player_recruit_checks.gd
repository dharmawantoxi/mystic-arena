extends RefCounted
## Source-backed player Hero Shop domain checks.

const World = preload("res://scripts/match/prototype_battle.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const FIXTURE := "res://tests/fixtures/player_recruit_source.json"


func run(check: Callable) -> void:
	var rows: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(rows is Array and rows.size() == 8, "Player recruit source fixture loads")
	if rows is Array:
		for row in rows:
			_source_case(row, check)
	_playable_roster(check)
	_profile_and_guards(check)


func _source_case(row: Dictionary, check: Callable) -> void:
	var spec: Dictionary = row.input
	var world := World.new()
	world.economy = Economy.new()
	world.economy.gold[world.BLUE] = int(spec.gold)
	world.economy.opening[world.BLUE] = int(spec.gold)
	world.purchased_heroes.clear()
	for value in spec.unlocked:
		world.purchased_heroes.append(String(value))
	for entry in spec.get("owned", []):
		var definition = World.HERO_ROSTER[String(entry.id)]
		var hero = world.spawn_hero(definition, world.BLUE, Vector2.ZERO)
		hero.alive = bool(entry.get("alive", true))
		world.player_hero_ids.append(hero.id)
	var before := world.player_roster().size()
	world.buy_player_hero(String(spec.buy))
	var roster := world.player_roster()
	var owned: Array[String] = []
	for hero in roster:
		owned.append(String(hero.definition.id))
	check.call(owned == _strings(row.owned), row.label + ": player owned list matches source")
	check.call(world.economy.gold[world.BLUE] == int(row.gold), row.label + ": exact source debit")
	check.call(world.economy.is_balanced(), row.label + ": player ledger remains balanced")
	var receipts: Array = row.receipts
	check.call(roster.size() - before == receipts.size(), row.label + ": source spawn count")
	for index in range(receipts.size()):
		var hero = roster[before + index]
		var receipt: Dictionary = receipts[index]
		check.call(hero.definition.id == receipt.id, row.label + ": source kit identity")
		check.call(hero.team == world.BLUE, row.label + ": source player team")
		(
			check
			. call(
				hero.position == Vector2(receipt.position[0], receipt.position[1]),
				row.label + ": source shop spawn offset",
			)
		)
		check.call(hero.alive == receipt.alive, row.label + ": source alive state")


func _playable_roster(check: Callable) -> void:
	var world := World.new()
	check.call(
		world.configure_player_profile(
			{"purchased_heroes": world.STARTER_HEROES, "unlocked_bosses": []}
		),
		"Permanent starter unlocks configure before the playable arena"
	)
	check.call(world.setup_arena(), "Player recruit playable arena initializes")
	(
		check
		. call(
			(
				world.player_roster().size() == 1
				and world.player_roster()[0].definition.id == "kaizen"
			),
			"Free prototype Kaizen occupies source player roster slot",
		)
	)
	var initial := world.economy.gold[world.BLUE]
	check.call(world.buy_player_hero("thorne"), "Unlocked starter recruits in playable world")
	var thorne = world.player_roster()[1]
	check.call(thorne.definition.id == "thorne", "Player summon uses real Thorne kit")
	(
		check
		. call(
			(
				thorne.position == world.player_hero_spawn_position(1)
				and thorne.position == Vector2(420, 550)
			),
			"Second source roster slot spawns at radiant shop offset",
		)
	)
	check.call(
		world.economy.gold[world.BLUE] == initial - thorne.settings().cost,
		"Summon costs match gold"
	)
	world.player_roster()[0].alive = false
	check.call(not world.buy_player_hero("kaizen"), "Dead active hero still blocks duplicate")
	check.call(world.transaction_error == "owned", "Duplicate refusal is explicit")
	for hero_type in ["grimjaw", "sylara", "vex"]:
		world.economy.credit_kill(world.BLUE, 1000)
		check.call(world.buy_player_hero(hero_type), "Roster fills with real starter " + hero_type)
	check.call(
		world.player_roster().size() == world.MAX_HEROES_OWNED,
		"Player roster reaches source cap five"
	)
	world.economy.credit_kill(world.BLUE, 1000)
	check.call(not world.buy_player_hero("zephyr"), "Sixth player hero is rejected")
	check.call(world.transaction_error == "capacity", "Player cap refusal is explicit")
	check.call(world.economy.is_balanced(), "Full player roster preserves ledger")


func _profile_and_guards(check: Callable) -> void:
	var profile := World.new()
	(
		check
		. call(
			profile.configure_player_profile(
				{"purchased_heroes": ["gornak"], "unlocked_bosses": ["gornak"]}
			),
			"Saved boss unlock configures before setup",
		)
	)
	check.call(
		profile.purchased_heroes == ["kaizen", "gornak"],
		"Profile merges purchased boss with the source Kaizen auto-grant"
	)
	check.call(profile.setup_arena(), "Profile-configured arena starts")
	profile.economy.credit_kill(profile.BLUE, 2000)
	check.call(profile.buy_player_hero("gornak"), "Purchased boss kit recruits for the player")
	check.call(
		profile.player_roster().back().definition.id == "gornak", "Boss summon has exact identity"
	)
	check.call(
		not profile.configure_player_profile({}), "Live arena cannot replace permanent hero profile"
	)

	var invalid := World.new()
	(
		check
		. call(
			not invalid.configure_player_profile(
				{"purchased_heroes": ["missing"], "unlocked_bosses": []}
			),
			"Unknown profile hero is rejected",
		)
	)
	(
		check
		. call(
			not invalid.configure_player_profile(
				{"purchased_heroes": [], "unlocked_bosses": ["kaizen"]}
			),
			"Starter cannot forge a defeated-boss unlock",
		)
	)
	invalid.purchased_heroes = ["missing"]
	check.call(not invalid.buy_player_hero("missing"), "Unknown purchased kit cannot substitute")
	check.call(invalid.transaction_error == "kit", "Unknown player kit refusal is explicit")
	invalid.purchased_heroes = ["kaizen"]
	invalid.economy.gold[invalid.BLUE] = 10000
	invalid.economy.opening[invalid.BLUE] = 10000
	invalid._by_id[invalid._next_id] = invalid.units
	check.call(not invalid.buy_player_hero("kaizen"), "Colliding player entity ID is rejected")
	check.call(invalid.economy.gold[invalid.BLUE] == 10000, "Failed registry guard cannot debit")


func _strings(values: Array) -> Array[String]:
	var result: Array[String] = []
	for value in values:
		result.append(String(value))
	return result
