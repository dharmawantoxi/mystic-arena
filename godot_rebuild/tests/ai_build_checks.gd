extends RefCounted
## Source fixture against world slots, registry, projectiles, upgrades and ledger.

const World = preload("res://scripts/match/prototype_battle.gd")
const Draft = preload("res://scripts/match/ai_draft.gd")
const Build = preload("res://scripts/match/ai_build.gd")
const Upgrades = preload("res://scripts/match/ai_upgrades.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/ai_build_source.json"

var chosen_path := "archer"
var slot_calls := 0
var type_calls := 0
var last_slot_size := 0
var observed_types: Array = []
var observed_weights: Array = []


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for row in fixture.attempts:
		_attempt(row, check)
	for row in fixture.levels:
		_level(row, check)
	for sample in fixture.sampling:
		check.call(
			Build.weighted_at(float(sample.draw)) == sample.chosen, "AI build weight boundary"
		)
	_guards(check)
	_picker(check)


func _world() -> World:
	var world := World.new()
	world.defender_enabled = false
	world.setup_arena()
	return world


func _draft(reserve: int) -> Draft:
	var draft := Draft.new()
	draft.purchase_target = "kaizen" if reserve > 0 else ""
	draft.purchase_target_cost = reserve
	return draft


func _fund(world: World, amount: int) -> void:
	world.economy = Economy.new()
	world.economy.gold[1] = amount
	world.economy.opening[1] = amount


func _last_slot(candidates: Array[int]) -> int:
	slot_calls += 1
	last_slot_size = candidates.size()
	return candidates.back()


func _path(types: Array, weights: Array) -> String:
	type_calls += 1
	observed_types = types.duplicate()
	observed_weights = weights.duplicate()
	return chosen_path


func _attempt(row: Dictionary, check: Callable) -> void:
	var world := _world()
	# Source's empty_slots input is mirrored by occupying other red slots;
	# real domain derives candidates from authoritative world, never a mock list.
	for index in range(9, 18 - int(row.empty)):
		world.slots[index].structure_id = 9999  # unavailable, not in registry
	_fund(world, int(row.gold))
	var draft := _draft(int(row.reserve))
	var build := Build.new()
	chosen_path = row.path
	build.slot_picker = _last_slot
	build.type_picker = _path
	slot_calls = 0
	type_calls = 0
	var before_size := world.structures.size()
	var success := build.try_build(world, draft)
	check.call(success == row.success, "AI build source attempt")
	check.call(build.total_built == int(row.count), "AI build count once on success")
	check.call(world.economy.gold[1] == int(row.after), "AI build 100 G debit")
	check.call(world.economy.gold[0] == 1000 and world.economy.is_balanced(), "AI build ledger")
	check.call(world.structures.size() == before_size + int(success), "AI build registry size")
	check.call(draft.reserve() == int(row.reserve), "AI build keeps draft reserve")
	check.call(
		slot_calls == int(success) and type_calls == int(success), "AI build no premature RNG"
	)
	if success:
		check.call(last_slot_size == int(row.empty), "AI build slot candidates")
		check.call(
			(
				observed_types == ["archer", "cannon", "ice", "mage"]
				and observed_weights == [0.35, 0.25, 0.20, 0.20]
			),
			"AI build ordered weighted type candidates"
		)
		var slot = world.slots[17]
		var tower := world.get_unit(slot.structure_id) as World.StructureState
		check.call(tower != null and tower.team == world.RED, "AI red tower registered")
		check.call(
			tower.settings().tower_path == row.identity and tower.settings().level == 1,
			"AI build path identity"
		)
		check.call(
			tower.position == slot.position and tower.lane == slot.lane,
			"AI build slot position/lane"
		)
		check.call(
			not build.try_build(world, draft) and build.total_built == 1,
			"AI failed repeat does not double debit"
		)


func _level(row: Dictionary, check: Callable) -> void:
	var world := _world()
	_fund(world, 1000)
	var build := Build.new()
	chosen_path = row.before.path
	build.slot_picker = _last_slot
	build.type_picker = _path
	check.call(build.try_build(world, _draft(0)), "AI build path for Lv1 fixture")
	var tower := world.get_unit(world.slots[17].structure_id) as World.StructureState
	var data = tower.settings()
	var expected: Dictionary = row.before
	for pair in [
		["tower_path", "path"],
		["level", "level"],
		["max_hp", "max_hp"],
		["damage", "damage"],
		["attack_range_px", "range"],
		["attack_cooldown_ticks", "cd"],
		["armor", "armor"],
		["shield_capacity", "shield_max"],
		["splash_radius_px", "splash"],
		["slow_amount", "slow"],
		["chain_count", "chain"]
	]:
		check.call(data.get(pair[0]) == expected[pair[1]], "AI Lv1 fallback stat " + pair[0])
	check.call(
		tower.hp == expected.hp and tower.shield == expected.shield, "AI Lv1 fresh HP/shield"
	)
	check.call(data.id == expected.path + "_level_1", "AI Lv1 path ID")
	check.call(
		ARCHER.tower_path == "archer" and ARCHER.id == "archer_level_1",
		"AI build does not mutate shared resource"
	)
	var target := world.spawn_unit(GOBLIN, world.BLUE, tower.lane)
	target.position = tower.position + Vector2(40, 0)
	check.call(world.fire_projectile(tower.id, target.id), "AI Lv1 fires from actual registry")
	var shot = world.projectiles.back()
	var kind: String = "normal" if expected.path == "archer" else expected.path
	check.call(
		shot.kind == kind and shot.damage == expected.shot.damage, "AI Lv1 shot kind and damage"
	)
	check.call(world.projectiles.size() == int(expected.shot.count), "AI Lv1 shot count")
	check.call(shot.splash_radius == expected.splash, "AI Lv1 no cannon splash")
	check.call(
		shot.slow_amount == expected.slow and shot.skill_down_amount == 0, "AI Lv1 no status debuff"
	)
	check.call(
		world._upgrade_target(1, data.tower_path, "cannon").upgrade_price == int(row.price),
		"AI Lv1 cannon quote regardless build path"
	)
	tower.hp = 1
	tower.shield = 0
	var upgrades := Upgrades.new()
	check.call(upgrades.try_tower(world, _draft(0), tower.id), "AI Lv1 preferred cannon upgrade")
	check.call(
		tower.settings().tower_path == row.after.path and tower.settings().level == row.after.level,
		"AI Lv1 upgrade chooses cannon"
	)
	check.call(
		(
			tower.hp == row.after.hp
			and tower.shield == row.after.shield
			and tower.settings().damage == row.after.damage
		),
		"AI Lv1 upgrade restores stats"
	)
	check.call(
		world.economy.gold[1] == 1000 - 100 - int(row.price) and world.economy.is_balanced(),
		"AI Lv1 build plus upgrade ledger"
	)


func _guards(check: Callable) -> void:
	var world := _world()
	var draft := _draft(400)
	var build := Build.new()
	build.slot_picker = _last_slot
	build.type_picker = _path
	chosen_path = "ice"
	_fund(world, 499)
	check.call(
		not build.try_build(world, draft) and build.total_built == 0, "AI build reserve minus one"
	)
	world.economy.gold[1] = 500
	world.economy.opening[1] = 500
	check.call(build.try_build(world, draft), "AI build reserve exact")
	check.call(
		world.economy.gold[1] == 400 and world.economy.is_balanced(), "AI build spends only cost"
	)
	world.economy.credit_kill(1, 1000)  # Ensure guards are exercised past the gold gate.
	check.call(
		not world.build_tower(0, 17) and not world._build_tower_for(1, 0, "ice"),
		"Build wrong owner"
	)
	check.call(not world._build_tower_for(1, 17, "ice"), "Build occupied slot")
	check.call(
		not world._build_tower_for(1, -1, "ice") and not world._build_tower_for(1, 99, "ice"),
		"Build invalid IDs"
	)
	check.call(
		not world._build_tower_for(-1, 9, "ice") and not world._build_tower_for(2, 9, "ice"),
		"Build invalid teams"
	)
	check.call(not world._build_tower_for(1, 9, "bad"), "Build invalid path")
	world.slots[9].id = 42
	check.call(
		not build.try_build(world, draft) or world.slots[9].structure_id == -1,
		"Build excludes corrupt slot ID"
	)
	check.call(not world._build_tower_for(1, 9, "ice"), "Build rejects mismatched slot ID")
	world.slots[9].id = 9
	# Reject invalid candidate or path before touching the wallet/registry.
	var bad := Build.new()
	bad.slot_picker = func(_candidates: Array[int]) -> int: return 777
	check.call(not bad.try_build(world, draft), "AI picker cannot build outside candidate slots")
	bad.slot_picker = _last_slot
	bad.type_picker = func(_types: Array, _weights: Array) -> String: return "unknown"
	check.call(not bad.try_build(world, draft), "AI picker cannot inject an unknown path")
	var old_id := world._next_id
	world._next_id = world.slots[17].structure_id
	check.call(not build.try_build(world, draft), "Build rejects colliding registry ID")
	world._next_id = old_id
	# Fill capacity using actual registered structures, leaving slot 9 empty.
	while world.structures.size() < world.structure_limit():
		world.spawn_structure(ARCHER, world.RED, Vector2(500, 340), 1)
	check.call(not build.try_build(world, draft), "AI build respects registered structure capacity")
	var wallet := world.economy.gold.duplicate()
	var spent := world.economy.spent.duplicate()
	world.winner = 0
	check.call(
		not build.try_build(world, draft) and not world._build_tower_for(1, 9, "mage"),
		"Finished match cannot build"
	)
	check.call(
		(
			world.economy.gold == wallet
			and world.economy.spent == spent
			and world.economy.is_balanced()
		),
		"Failed builds never debit"
	)
	check.call(
		ARCHER.tower_path == "archer" and ARCHER.id == "archer_level_1",
		"Shared resource remains immutable"
	)


func _picker(check: Callable) -> void:
	var world := _world()
	_fund(world, 1000)
	var build := Build.new()
	build.rng.seed = 17
	check.call(build.try_build(world, _draft(0)), "Seeded AI build chooses valid slot/path")
	var registered := 0
	for slot in world.slots:
		if slot.team == 1 and slot.structure_id != -1:
			registered += 1
			check.call(world.get_unit(slot.structure_id) != null, "Random slot in real registry")
	check.call(registered == 1 and build.total_built == 1, "Random build exactly one")
