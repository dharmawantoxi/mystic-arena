# gdlint:disable=max-file-lines
extends RefCounted
## Layer 9ac native suite: source-free boss hits and the boss team guard.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/boss_sourceless_delivery_source.json"


class RollSpy:
	extends RefCounted
	var rolls := 0

	func roll() -> float:
		rolls += 1
		return 0.0


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("cases"), "sourceless boss fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	var world := Prototype.new()
	world.setup_arena()
	_rows(check, world, fixture)
	_team_guard(check, world, fixture)
	_lethal_control(check, world, fixture)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("signature_shape", {})
	check.call(
		(
			shape.get("signature", [])
			== ["self", "damage", "from_team", "damage_type", "source", "school"]
		),
		"source Boss.take_damage signature is the pinned five-argument shape"
	)
	check.call(
		int(shape.get("from_team_reads", -1)) == 0 and shape.get("team_comparisons", []) == [],
		"source Boss.take_damage never reads from_team and never filters teams"
	)
	check.call(
		(
			bool(shape.get("blind_needs_source", false))
			and bool(shape.get("blind_is_normal_only", false))
			and bool(shape.get("blind_draws_inside_guard", false))
		),
		"source blind block only runs for a sourced normal hit"
	)
	check.call(
		bool(shape.get("credits_source", false)) and bool(shape.get("killed_by_is_source", false)),
		"source crediting and _killed_by tail are pinned"
	)


func _rows(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	for entry in fixture.cases:
		var label := String(entry.get("name", "unknown"))
		if label == "team_variants":
			continue
		_replay_row(check, world, fixture, entry, label)


func _replay_row(
	check: Callable, world: Prototype, fixture: Dictionary, entry: Dictionary, label: String
) -> void:
	var expected: Dictionary = entry.get("expected", {})
	var stats: Dictionary = fixture.live_stats
	var kind := String(entry.get("kind", stats.mini.kind))
	if label == "armored_school_columns" or label == "fire_school_columns":
		kind = String(stats.true_boss.kind)
	var boss := _spawn(world, kind)
	if boss == null:
		check.call(false, "sourceless probe spawns: %s" % label)
		return
	var raw := int(stats.get("raw", 200))
	if label == "sourceless_lethal_hit":
		boss.hp = 50.0
	var spy := RollSpy.new()
	boss.blind_roll_override = spy.roll
	var before := boss.hp
	if label == "blinded_attacker_control":
		var hero = world.spawn_hero(Prototype.KAIZEN, world.BLUE, boss.position + Vector2(30, 0))
		hero.blind_amount = 1.0
		hero.blind_timer = 10
		var landed := world._deliver_hit(hero.id, world.BLUE, boss, raw, "neutral", boss.position)
		check.call(not landed, "blinded attacker misses the boss: %s" % label)
		check.call(spy.rolls == 1, "blinded attacker consumes exactly one blind draw")
		check.call(
			int(before - boss.hp) == int(expected.get("hp_loss", -1)),
			"blinded attacker hp delta matches source: %s" % label
		)
		return
	# The school-column rows carry one expected loss per school and deliver the
	# plain hit with no school, i.e. the `neutral` column.
	var column_row := not expected.has("hp_loss") and expected.has("neutral")
	var primary_loss := int(expected.get("hp_loss", expected.get("neutral", -1)))
	world._deliver_hit(-1, world.BLUE, boss, raw, "neutral", boss.position)
	check.call(
		int(before - boss.hp) == primary_loss, "sourceless hit payload matches source: %s" % label
	)
	check.call(spy.rolls == 0, "a source-free hit consumes no blind draw: %s" % label)
	check.call(boss.last_hit_source_id == -1, "sourceless hit keeps the sentinel: %s" % label)
	# The true-strike control is the only row whose source hit is credited, so
	# it asserts the credit instead of the unattributed default.
	if int(expected.get("credited", 0)) == 0:
		check.call(
			expected.get("killed_by", null) == null,
			"source fixture row stays unattributed: %s" % label
		)
	else:
		check.call(
			int(expected.get("credited", 0)) == int(expected.get("hp_loss", -1)),
			"source fixture row credits the attacker: %s" % label
		)
	if not column_row:
		return
	for school in expected.keys():
		var probe := _spawn(world, kind)
		if probe == null:
			continue
		var probe_before := probe.hp
		world._deliver_hit(-1, world.BLUE, probe, raw, String(school), probe.position)
		check.call(
			int(probe_before - probe.hp) == int(expected.get(school, -1)),
			"armoured school column matches source: %s %s" % [label, String(school)]
		)


func _team_guard(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var entry: Dictionary = {}
	for row in fixture.cases:
		if String(row.get("name", "")) == "team_variants":
			entry = row
	var expected: Dictionary = entry.get("expected", {})
	var losses: Array = expected.get("hp_losses", [])
	if losses.size() != 3:
		check.call(false, "team variant fixture carries three columns")
		return
	var enemy := _spawn(world, "gornak")
	var same := _spawn(world, "gornak")
	var source_free := _spawn(world, "gornak")
	if enemy == null or same == null or source_free == null:
		check.call(false, "team guard probes spawn")
		return
	var enemy_before := enemy.hp
	check.call(
		world._deliver_hit(-1, world.BLUE, enemy, 200, "neutral", enemy.position),
		"an enemy-team sourceless hit lands on the boss"
	)
	check.call(int(enemy_before - enemy.hp) == int(losses[0]), "enemy-team column matches source")
	var same_before := same.hp
	check.call(
		not world._deliver_hit(-1, world.RED, same, 200, "neutral", same.position),
		"the enemy-only guard still refuses a same-team hit without the flag"
	)
	check.call(is_equal_approx(same_before, same.hp), "refused hit leaves the boss untouched")
	var flagged_before := source_free.hp
	check.call(
		world._deliver_hit(
			-1, world.RED, source_free, 200, "neutral", source_free.position, "normal", true
		),
		"layer 9ac: ignore_team_guard now reaches the boss branch too"
	)
	check.call(
		int(flagged_before - source_free.hp) == int(losses[1]),
		"flagged same-team hit matches the source team column"
	)
	check.call(
		losses[0] == losses[1] and losses[1] == losses[2], "source team columns are identical"
	)
	var unit = world.spawn_unit(GOBLIN, world.RED, 0)
	if unit == null:
		return
	var unit_before: float = unit.hp
	check.call(
		world._deliver_hit(-1, world.RED, unit, 30, "neutral", unit.position, "normal", true),
		"unit branch keeps its 9z flag behavior"
	)
	check.call(unit.hp < unit_before, "flagged same-team tick damages the unit")


func _lethal_control(check: Callable, world: Prototype, fixture: Dictionary) -> void:
	var expected: Dictionary = {}
	for row in fixture.cases:
		if String(row.get("name", "")) == "sourceless_lethal_hit":
			expected = row.get("expected", {})
	var boss := _spawn(world, "gornak")
	if boss == null:
		check.call(false, "lethal sourceless probe spawns")
		return
	boss.hp = 50.0
	var unlocks_before := world.achievements_unlocked.size()
	world._deliver_hit(-1, world.BLUE, boss, 200, "neutral", boss.position)
	check.call(
		not boss.alive and boss.defeated and bool(expected.get("defeated", false)),
		"sourceless lethal hit retires the boss"
	)
	check.call(boss.last_hit_source_id == -1, "sourceless lethal hit keeps the sentinel")
	world._process_boss_kill(boss)
	check.call(
		(
			int(world.total_kills) == 0
			and int(world.miniboss_kill_count) == 0
			and world.achievements_unlocked.size() == unlocks_before
		),
		"sourceless lethal hit credits nobody"
	)


func _spawn(world: Prototype, kind: String) -> BossState:
	# Each probe needs its own live boss: `_spawn_boss` refuses to spawn while
	# one is active, so the registry slot is released first (the fixture rows
	# compare two or three bosses side by side).
	world.active_boss = null
	var boss: BossState = world._spawn_boss(kind)
	if boss == null:
		return null
	boss.entrance_timer = 0
	return boss
