extends RefCounted
## 9b: replay Basilisk Breath reapplication against each active boss through
## hero_basic_attack -> inventory on-hit -> shared Miasma registry, then tick
## through the prototype's real per-hero item update path.

const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const FIXTURE := "res://tests/fixtures/boss_miasma_source.json"


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var fixture: Dictionary = parsed if parsed is Dictionary else {}
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "9b four Miasma cases for 216 bosses")
	if cases.size() != 864:
		return
	var helper := Prior.new()
	var world := Prior.CleaveChainWorld.new()
	for row: Dictionary in cases:
		helper._reset_world(world, false)
		world._miasma_registry.clear()
		var spawned: Array = helper._spawn_case_units(
			world, String(row.get("boss_type", "")), {"boss_offset": 0.0, "minion_offsets": []}
		)
		check.call(spawned.size() == 4, "9b active boss setup")
		if spawned.size() != 4:
			continue
		var boss: Prior.BossState = spawned[0]
		var hero_a: Prior.HeroState = spawned[1]
		var hero_b: Prior.HeroState = world.spawn_hero(
			Prior.KAIZEN, world.BLUE, boss.position + Vector2(-50.0, 0.0)
		)
		check.call(hero_b != null, "9b second hero setup")
		if hero_b == null:
			continue
		_prepare_attacker(hero_a, boss)
		_prepare_attacker(hero_b, boss)
		check.call(hero_a.items.add("basilisk_breath"), "9b equip first Basilisk")
		check.call(hero_b.items.add("basilisk_breath"), "9b equip second Basilisk")
		check.call(
			world.hero_basic_attack(hero_a.id, boss.id), "9b first hero applies Miasma on boss hit"
		)
		var pre_frames: int = int(row.get("pre_frames", 0))
		for _frame in range(pre_frames):
			world._tick_auras_and_items()
		check.call(
			world.hero_basic_attack(hero_b.id, boss.id),
			"9b second hero reapplies Miasma on boss hit"
		)

		var expected: Dictionary = row.get("expected", {})
		var expected_tracker: Dictionary = expected.get("tracker", {})
		var tracker: Dictionary = world._miasma_registry.get(int(boss.id), {})
		var owner_a_view: Dictionary = hero_a.items.miasma.get(int(boss.id), {})
		var owner_b_view: Dictionary = hero_b.items.miasma.get(int(boss.id), {})
		check.call(
			world._miasma_registry.size() == 1 and int(expected_tracker.get("count", 0)) == 1,
			"9b one target-keyed tracker after cross-hero reapply"
		)
		check.call(
			(
				int(tracker.get("source_id", -1)) == int(hero_b.id)
				and int(owner_a_view.get("source_id", -1)) == int(hero_b.id)
				and int(owner_b_view.get("source_id", -1)) == int(hero_b.id)
			),
			"9b both inventories observe last-applier source"
		)
		check.call(
			(
				int(tracker.get("damage", -1)) == int(expected_tracker.get("damage", -2))
				and int(tracker.get("timer", -1)) == int(expected_tracker.get("timer", -2))
				and int(tracker.get("tick_cd", -1)) == int(expected_tracker.get("tick_cd", -2))
			),
			"9b strongest damage, longest timer and shortest tick countdown merge"
		)

		_clear_damage_log(world)
		if bool(row.get("reapplying_hero_dies", false)):
			hero_b.alive = false
			hero_b.hp = 0.0
		var actual_events: Array = []
		var boss_delivery_count := 0
		var observe_frames: int = int(row.get("observe_frames", 0))
		for frame in range(1, observe_frames + 1):
			world._tick_auras_and_items()
			var deliveries: Array = world.deliveries.get(int(boss.id), [])
			while boss_delivery_count < deliveries.size():
				var delivery: Array = deliveries[boss_delivery_count]
				var source_id: int = int(boss.last_hit_source_id)
				actual_events.append(
					[frame, _owner_label(source_id, hero_a.id, hero_b.id), int(delivery[0])]
				)
				boss_delivery_count += 1
		var expected_events: Array = expected.get("events", [])
		check.call(
			_events_match(actual_events, expected_events),
			(
				"9b source event replay "
				+ String(row.get("boss_type", ""))
				+ "/"
				+ String(row.get("scenario", ""))
			)
		)
		var native_old: Dictionary = row.get("native_old", {})
		check.call(
			(
				int(native_old.get("tracker_count", 0)) == 2
				and not _events_match(expected_events, native_old.get("events", []))
			),
			"9b fixture retains differing pre-fix per-inventory counterfactual"
		)
		helper._reset_world(world, false)
		world._miasma_registry.clear()
	world._miasma_registry.clear()


func _prepare_attacker(hero: Prior.HeroState, boss: Prior.BossState) -> void:
	hero.position = boss.position + Vector2(-40.0, 0.0)
	hero.target_id = int(boss.id)
	hero.attack_timer = 0
	hero.items.hero_melee_flag = 1
	hero.items.hero_range = 70.0


func _clear_damage_log(world: Prior.CleaveChainWorld) -> void:
	world.deliveries = {}
	world.hit_order = []
	world.recent_events.clear()


func _owner_label(source_id: int, hero_a_id: int, hero_b_id: int) -> String:
	if source_id == hero_a_id:
		return "hero_a"
	if source_id == hero_b_id:
		return "hero_b"
	return "unknown"


func _events_match(actual: Array, expected: Array) -> bool:
	if actual.size() != expected.size():
		return false
	for index in range(actual.size()):
		var actual_row: Array = actual[index]
		var expected_row: Array = expected[index]
		if (
			int(actual_row[0]) != int(expected_row[0])
			or String(actual_row[1]) != String(expected_row[1])
			or int(actual_row[2]) != int(expected_row[2])
		):
			return false
	return true
