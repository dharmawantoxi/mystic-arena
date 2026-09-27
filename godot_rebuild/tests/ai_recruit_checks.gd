extends RefCounted
## Numeric baselines for 222, real Kaizen/Thorne/Grimjaw/Sylara purchases; other kits pending.
## No unsupported hero may silently inherit Kaizen's kit.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Recruit = preload("res://scripts/match/ai_recruitment.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const THORNE = preload("res://data/heroes/thorne.tres")
const GRIMJAW = preload("res://data/heroes/grimjaw.tres")
const SYLARA = preload("res://data/heroes/sylara.tres")
const FIXTURE := "res://tests/fixtures/ai_recruit_source.json"
const STATS := "res://data/ai/hero_combat_stats.json"
const RECRUITMENT := "res://data/ai/recruitment.json"


func run(check: Callable) -> void:
	var fixture: Array = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture:
		_attempt(row, check)
	_catalog(check)
	_multi_roster(check)
	_guards(check)
	_pending_kits(check)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	return world


func _fund(world: World, amount: int) -> void:
	world.economy = Economy.new()
	world.economy.opening[1] = amount
	world.economy.gold[1] = amount


func _target(kind: String, cost: int) -> Draft:
	var draft := Draft.new()
	draft.level_number = 55
	draft.purchase_target = kind
	draft.purchase_target_cost = cost
	return draft


func _attempt(row: Dictionary, check: Callable) -> void:
	var world := _world()
	_fund(world, int(row.initial))
	var draft := _target(row.hero_type, int(row.price))
	var recruit := Recruit.new()
	check.call(recruit.try_buy(world, draft) == row.success, "Real starter buy source threshold")
	check.call(world.economy.gold[1] == row.balance, "Real recruit exact red debit")
	check.call(world.economy.gold[0] == 1000 and world.economy.is_balanced(), "Real recruit ledger")
	check.call(draft.total_heroes_bought == row.count, "Real recruit count after spawn")
	check.call(
		draft.reserve() == row.reserve and draft.purchase_target == row.target,
		"Real recruit persistent draft"
	)
	check.call(world.units.size() == int(row.success), "Real recruit registry count")
	if row.success:
		var hero := world.units[0] as World.HeroState
		var expected: Dictionary = row.hero
		check.call(
			hero.team == world.RED and hero.definition.id == expected.hero_type,
			"Real recruit identity"
		)
		check.call(world.get_unit(hero.id) == hero, "Real recruit ID registry")
		check.call(hero.position == Vector2(expected.x, expected.y), "Real recruit source offset")
		check.call(hero.max_hp == expected.max_hp and hero.hp == expected.hp, "Real recruit HP")
		check.call(
			hero.damage == expected.damage and hero.skill_value == expected.skill_damage,
			"Real recruit attack/skill"
		)
		check.call(
			hero.level == expected.level and hero.auto_cast_enabled == expected.auto_cast,
			"Real recruit flags"
		)
		check.call(
			not world._buy_ai_hero(row.hero_type, int(row.price), hero.position),
			"Real recruit cannot duplicate owned type"
		)
		check.call(
			world.economy.gold[1] == row.balance and world.economy.is_balanced(),
			"Duplicate buy does not debit"
		)


func _catalog(check: Callable) -> void:
	var stats: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(STATS))
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RECRUITMENT))
	check.call(
		stats.size() == 222 and stats.size() == metadata.catalog.size(),
		"222 numeric source baselines present"
	)
	for hero_type in metadata.catalog:
		check.call(stats.has(hero_type), "No missing source hero numeric baseline")
		if stats.has(hero_type):
			check.call(
				(
					int(stats[hero_type].cost) == int(metadata.catalog[hero_type].cost)
					and stats[hero_type].is_boss_hero == metadata.catalog[hero_type].is_boss_hero
				),
				"Combat/source summon price and boss classification"
			)
	check.call(stats.kaizen.base_hp == KAIZEN.max_hp, "Kaizen native/source HP")
	check.call(stats.kaizen.base_damage == KAIZEN.damage, "Kaizen native/source damage")
	check.call(stats.kaizen.cost == KAIZEN.cost, "Kaizen native/source price")
	check.call(stats.thorne.base_hp == THORNE.max_hp, "Thorne native/source HP")
	check.call(stats.thorne.base_damage == THORNE.damage, "Thorne native/source damage")
	check.call(stats.thorne.cost == THORNE.cost, "Thorne native/source price")
	check.call(stats.grimjaw.base_hp == GRIMJAW.max_hp, "Grimjaw native/source HP")
	check.call(stats.grimjaw.base_damage == GRIMJAW.damage, "Grimjaw native/source damage")
	check.call(stats.grimjaw.cost == GRIMJAW.cost, "Grimjaw native/source price")
	check.call(stats.sylara.base_hp == SYLARA.max_hp, "Sylara native/source HP")
	check.call(stats.sylara.base_damage == SYLARA.damage, "Sylara native/source damage")
	check.call(stats.sylara.cost == SYLARA.cost, "Sylara native/source price")


func _guards(check: Callable) -> void:
	var world := _world()
	_fund(world, 1000)
	var recruit := Recruit.new()
	var draft := _target("ancient_apparition", 800)
	check.call(not recruit.try_buy(world, draft), "Missing boss kit cannot spawn Kaizen")
	check.call(world.transaction_error == "kit", "Missing kit refusal is explicit")
	check.call(
		draft.purchase_target == "ancient_apparition" and draft.reserve() == 800,
		"Missing kit retains draft/reserve"
	)
	check.call(
		world.units.is_empty() and world.economy.gold[1] == 1000, "Missing kit has no effects"
	)
	check.call(
		not world._buy_ai_hero("ancient_apparition", 400, Vector2(1120, 90)),
		"Boss metadata is not a playable kit"
	)
	check.call(not world._buy_ai_hero("kaizen", 1, Vector2(1120, 90)), "Forged cost rejected")
	check.call(not world._buy_ai_hero("kaizen", 400, Vector2(1120, 130)), "Wrong offset rejected")
	check.call(not world._buy_ai_hero("kaizen", 400, Vector2.INF), "Non-finite position rejected")
	var bad_id := world._next_id
	world._by_id[bad_id] = world.units
	check.call(
		not world._buy_ai_hero("kaizen", 400, Vector2(1120, 90)), "Colliding registry ID rejected"
	)
	world._by_id.erase(bad_id)
	check.call(
		world._buy_ai_hero("kaizen", 400, Vector2(1120, 90)), "Real domain direct transaction"
	)
	var hero := world.units[0] as World.HeroState
	hero.alive = false
	check.call(
		not world._buy_ai_hero("kaizen", 400, Vector2(1120, 130)),
		"Dead owned hero still blocks duplicate"
	)
	world.winner = 0
	check.call(
		not recruit.try_buy(world, _target("ancient_apparition", 800)),
		"Finished match blocks draft"
	)
	check.call(
		not world._buy_ai_hero("kaizen", 400, Vector2(1120, 130)), "Finished match blocks purchase"
	)
	check.call(
		world.economy.gold[1] == 600 and world.economy.is_balanced(),
		"Failed purchases do not debit"
	)


func _multi_roster(check: Callable) -> void:
	var world := _world()
	_fund(world, 1000)
	var adapter := Recruit.new()
	var thorne := _target("thorne", 500)
	check.call(adapter.try_buy(world, thorne), "Thorne first paid summon")
	check.call(world.units[0].position == Vector2(1120, 90), "First red summon at Y90")
	var kaizen := _target("kaizen", 400)
	check.call(adapter.try_buy(world, kaizen), "Kaizen second paid summon")
	check.call(world.units[1].position == Vector2(1120, 130), "Second red summon at Y130")
	check.call(
		world.units[0].definition.id == "thorne" and world.units[1].definition.id == "kaizen",
		"Different real kits in red roster"
	)
	check.call(
		(
			world.economy.gold[1] == 100
			and world.economy.spent[1] == 900
			and world.economy.is_balanced()
		),
		"Two paid summons debit once each"
	)
	world.units[0].alive = false
	check.call(
		not world._buy_ai_hero("thorne", 500, Vector2(1120, 170)), "Dead Thorne remains owned"
	)
	var missing := _target("ancient_apparition", 800)
	world.economy.credit_kill(1, 1000)
	check.call(
		not adapter.try_buy(world, missing) and missing.reserve() == 800,
		"Unsupported boss kit keeps draft without debit"
	)
	var grimjaw := _target("grimjaw", 450)
	check.call(adapter.try_buy(world, grimjaw), "Grimjaw third real paid summon")
	check.call(
		world.units.size() == 3 and world.units[2].definition.id == "grimjaw",
		"Three distinct native kits"
	)
	check.call(world.units[2].position == Vector2(1120, 170), "Third red summon source offset")
	check.call(
		world.economy.gold[1] == 650 and world.economy.is_balanced(), "Third kit debits exact 450 G"
	)
	var sylara := _target("sylara", 380)
	check.call(adapter.try_buy(world, sylara), "Sylara fourth real paid summon")
	check.call(
		world.units.size() == 4 and world.units[3].definition.id == "sylara",
		"Four distinct native kits"
	)
	check.call(world.units[3].position == Vector2(1120, 210), "Fourth red summon source offset")
	check.call(
		world.economy.gold[1] == 270 and world.economy.is_balanced(),
		"Fourth kit debits exact 380 G"
	)


func _pending_kits(check: Callable) -> void:
	var world := _world()
	_fund(world, 100000)
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RECRUITMENT))
	for kind in metadata.catalog:
		if World.PLAYABLE_AI_HEROES.has(kind):
			continue
		check.call(
			not world._buy_ai_hero(kind, int(metadata.catalog[kind].cost), Vector2(1120, 90)),
			"Pending kit rejected: " + kind
		)
		check.call(
			world.transaction_error == "kit" and world.units.is_empty(),
			"No pending kit substitution"
		)
		check.call(
			world.economy.gold[1] == 100000 and world.economy.is_balanced(), "No pending debit"
		)
