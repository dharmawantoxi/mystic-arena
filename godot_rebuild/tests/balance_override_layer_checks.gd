extends RefCounted
## Layer 9c native suite: the explicit rebalance surface. The production
## override table carries the S1 starter catch-up directive (six starter
## kits, damage_mult 1.5: measured starter gap 5.67x -> 3.97x, target
## <= 4.0x), every live entry carries a doctrine reason, the pure entry
## reader is unit-tested with synthetic entries, and the production spawn
## wrapper applies the multiplier only on a world the playable flow opted in
## (`balance_overrides_enabled`), while the direct lab path stays parity.

const BalanceOverrides = preload("res://scripts/data/balance_overrides.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const STARTER_IDS := ["kaizen", "thorne", "grimjaw", "sylara", "vex", "zephyr"]
const STARTER_DAMAGE_MULT := 1.5
## S2: the 39 PHYSICAL|TANK boss heroes (audit identity grid, n=39).
const PHYSICAL_TANK_IDS := [
	"akaroth",
	"akirakumo",
	"akiraze",
	"aurelian",
	"azkharion",
	"broggmar",
	"brumhar",
	"cogsworth",
	"deidara",
	"garumenshi",
	"grimkor",
	"hitokage",
	"hollowbane",
	"kaelthys",
	"kaerinya",
	"kaerissa",
	"kagetsuka",
	"kairenji",
	"kaithros",
	"kaoruken",
	"karzhul",
	"korokai",
	"kyrenzai",
	"morvath",
	"obanai",
	"sasori",
	"solareth",
	"thoraz",
	"thorgaruk",
	"urgharun",
	"vaelmyrra",
	"vardrok",
	"verdanix",
	"vorthakul",
	"xareth",
	"yomigetsu",
	"zhaeris",
	"zhyrakaan",
	"zhyvrek"
]
const PHYSICAL_TANK_DAMAGE_MULT := 0.85
const Akaroth = preload("res://data/heroes/akaroth.tres")


func run(check: Callable) -> void:
	_table_checks(check)
	_reader_checks(check)
	_production_spawn_checks(check)


func _table_checks(check: Callable) -> void:
	check.call(
		BalanceOverrides.HERO_OVERRIDES.size() == STARTER_IDS.size() + PHYSICAL_TANK_IDS.size(),
		"the production override table holds exactly the S1 starter + S2 PHYSICAL|TANK entries"
	)
	check.call(
		PHYSICAL_TANK_IDS.size() == 39, "the S2 cell lists the 39 audited PHYSICAL|TANK heroes"
	)
	check.call(
		Array(BalanceOverrides.entries_without_reason()).is_empty(),
		"every override entry must carry a doctrine reason"
	)
	for hero_id in STARTER_IDS:
		check.call(
			BalanceOverrides.HERO_OVERRIDES.has(hero_id),
			"starter %s has an S1 catch-up entry" % hero_id
		)
		check.call(
			is_equal_approx(BalanceOverrides.damage_multiplier(hero_id), STARTER_DAMAGE_MULT),
			"starter %s carries the S1 damage multiplier 1.5" % hero_id
		)
		check.call(
			BalanceOverrides.hp_multiplier(hero_id) == 1.0,
			"starter %s keeps hp untouched by S1" % hero_id
		)
		var reason: String = String(BalanceOverrides.HERO_OVERRIDES[hero_id].get("reason", ""))
		check.call(
			reason.contains("5.67x -> 3.97x") and reason.contains("S1"),
			"starter %s reason records the measured before/after gap" % hero_id
		)
	for hero_id in PHYSICAL_TANK_IDS:
		check.call(
			BalanceOverrides.HERO_OVERRIDES.has(hero_id),
			"PHYSICAL|TANK %s has an S2 nerf entry" % hero_id
		)
		check.call(
			is_equal_approx(BalanceOverrides.damage_multiplier(hero_id), PHYSICAL_TANK_DAMAGE_MULT),
			"PHYSICAL|TANK %s carries the S2 damage multiplier 0.85" % hero_id
		)
		check.call(
			BalanceOverrides.hp_multiplier(hero_id) == 1.0,
			"PHYSICAL|TANK %s keeps hp untouched by S2" % hero_id
		)
		var tank_reason: String = String(BalanceOverrides.HERO_OVERRIDES[hero_id].get("reason", ""))
		check.call(
			tank_reason.contains("1.38 -> 1.25") and tank_reason.contains("S2"),
			"PHYSICAL|TANK %s reason records the measured before/after cell power" % hero_id
		)
	for hero_id in ["zharok", "abaddon", "unported_probe"]:
		check.call(
			(
				BalanceOverrides.damage_multiplier(hero_id) == 1.0
				and BalanceOverrides.hp_multiplier(hero_id) == 1.0
			),
			"non-starter %s keeps the default 1.0/1.0 multipliers" % hero_id
		)


func _reader_checks(check: Callable) -> void:
	check.call(
		BalanceOverrides.multiplier_from({}, "damage_mult") == 1.0,
		"a missing entry field falls back to 1.0"
	)
	check.call(
		is_equal_approx(
			BalanceOverrides.multiplier_from({"damage_mult": 1.25}, "damage_mult"), 1.25
		),
		"a synthetic damage multiplier reads back exactly"
	)
	check.call(
		is_equal_approx(BalanceOverrides.multiplier_from({"hp_mult": 2}, "hp_mult"), 2.0),
		"an integer multiplier field is accepted as a float"
	)
	check.call(
		BalanceOverrides.multiplier_from({"damage_mult": "wide"}, "damage_mult") == 1.0,
		"a non-numeric multiplier field falls back to 1.0"
	)
	check.call(
		BalanceOverrides.multiplier_from({"hp_mult": 0.0}, "hp_mult") == 1.0,
		"a zero multiplier is rejected back to 1.0"
	)
	check.call(
		BalanceOverrides.multiplier_from({"hp_mult": -1.5}, "hp_mult") == 1.0,
		"a negative multiplier is rejected back to 1.0"
	)
	check.call(
		BalanceOverrides.multiplier_from({"hp_mult": NAN}, "hp_mult") == 1.0,
		"a non-finite multiplier is rejected back to 1.0"
	)


func _production_spawn_checks(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var definition = Prototype.KAIZEN
	check.call(definition != null, "the kaizen definition preloads for the spawn probe")
	if definition == null:
		return
	check.call(
		not world.balance_overrides_enabled,
		"a directly built world leaves the rebalance table off (source-parity suites)"
	)
	var parity = world._spawn_production_hero(definition, world.BLUE, Vector2(100, 300))
	check.call(
		parity != null and parity.base_damage == definition.damage,
		"with the flag off the routed spawn keeps the .tres damage (fixture parity)"
	)
	world.balance_overrides_enabled = true
	var routed = world._spawn_production_hero(definition, world.BLUE, Vector2(200, 300))
	var direct = world.spawn_hero(definition, world.RED, Vector2(400, 300))
	check.call(routed != null and direct != null, "both spawn paths return a hero")
	if routed == null or direct == null:
		return
	var expected_damage := int(round(float(definition.damage) * STARTER_DAMAGE_MULT))
	check.call(expected_damage == 68, "kaizen's S1 production damage is 45 -> 68")
	check.call(
		routed.base_damage == expected_damage and routed.damage == expected_damage,
		"the routed production spawn applies the S1 damage multiplier at level 1"
	)
	check.call(
		(
			routed.base_hp == direct.base_hp
			and routed.max_hp == direct.max_hp
			and routed.hp == routed.max_hp
			and routed.skill_value == direct.skill_value
		),
		"the routed production spawn leaves hp and skill on the parity values at full HP"
	)
	check.call(
		(
			direct.base_damage == definition.damage
			and direct.damage == definition.damage
			and direct.base_hp == definition.max_hp
		),
		"the direct lab spawn still carries the untouched .tres parity stats"
	)
	var tank = world._spawn_production_hero(Akaroth, world.RED, Vector2(500, 300))
	check.call(
		tank != null and Akaroth.damage == 320 and tank.base_damage == 272 and tank.damage == 272,
		"akaroth's S2 production damage is 320 -> 272 (round(320 * 0.85))"
	)
	check.call(
		tank != null and tank.base_hp == Akaroth.max_hp and tank.hp == tank.max_hp,
		"akaroth's S2 spawn keeps hp on the parity value at full HP"
	)
