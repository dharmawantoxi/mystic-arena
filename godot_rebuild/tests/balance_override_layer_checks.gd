extends RefCounted
## Layer 9c native suite: the explicit rebalance surface is machinery-only.
## The production override table is EMPTY BY DECISION (measured 9b baseline:
## zero audit violations), the pure entry reader is unit-tested with synthetic
## entries, every live entry must carry a doctrine reason, and the production
## spawn wrapper is an exact no-op against the direct source-parity path.

const BalanceOverrides = preload("res://scripts/data/balance_overrides.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")


func run(check: Callable) -> void:
	_table_checks(check)
	_reader_checks(check)
	_noop_spawn_checks(check)


func _table_checks(check: Callable) -> void:
	check.call(
		BalanceOverrides.HERO_OVERRIDES.is_empty(),
		"the production override table stays empty until a measured directive lands"
	)
	check.call(
		Array(BalanceOverrides.entries_without_reason()).is_empty(),
		"every override entry must carry a doctrine reason"
	)
	for hero_id in ["kaizen", "thorne", "zharok", "unported_probe"]:
		check.call(
			(
				BalanceOverrides.damage_multiplier(hero_id) == 1.0
				and BalanceOverrides.hp_multiplier(hero_id) == 1.0
			),
			"hero %s keeps the default 1.0/1.0 multipliers" % hero_id
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


func _noop_spawn_checks(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var definition = Prototype.KAIZEN
	check.call(definition != null, "the kaizen definition preloads for the spawn probe")
	if definition == null:
		return
	var routed = world._spawn_production_hero(definition, world.BLUE, Vector2(200, 300))
	var direct = world.spawn_hero(definition, world.RED, Vector2(400, 300))
	check.call(routed != null and direct != null, "both spawn paths return a hero")
	if routed == null or direct == null:
		return
	check.call(
		(
			routed.base_hp == direct.base_hp
			and routed.base_damage == direct.base_damage
			and routed.damage == direct.damage
			and routed.max_hp == direct.max_hp
			and routed.hp == direct.hp
			and routed.skill_value == direct.skill_value
		),
		"the routed production spawn is stat-identical to the direct parity spawn"
	)
	check.call(
		(
			routed.base_damage == definition.damage
			and routed.base_hp == definition.max_hp
			and routed.hp == routed.max_hp
		),
		"the routed spawn still carries the untouched .tres parity stats at full HP"
	)
