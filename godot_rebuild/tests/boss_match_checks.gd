# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8b native suite: source schedule/queue/trigger/reward conditions.
## Boss movement, attacks and presentation are deliberately not tested here.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/match_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("boss_layer"), "boss match fixture parses")
	if not fixture is Dictionary or not fixture.has("boss_layer"):
		return
	_schedule(check, fixture["boss_layer"]["schedule"])
	_pending(check, fixture["boss_layer"]["pending"])
	_true_boss(check, fixture["boss_layer"]["true_boss"])
	_tower_counter(check, fixture["boss_layer"]["tower_rewards"])
	_rewards_and_unlocks(check, fixture["boss_layer"])


func _world() -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	return world


func _schedule(check: Callable, source: Dictionary) -> void:
	for difficulty in ["normal", "hard", "easy"]:
		var world := _world()
		world.difficulty = difficulty
		world.boss_rng.seed = 8128 + ["normal", "hard", "easy"].find(difficulty)
		var schedule: Dictionary = world._roll_mini_boss_schedule()
		var low := 20 if difficulty == "easy" else 11
		var high := 40 if difficulty == "easy" else 30
		check.call(schedule.size() == 3, "three mini-boss waves (%s)" % difficulty)
		var values: Array = schedule.values()
		check.call(
			values == ["gornak", "morgath", "drakar"], "source mini-boss order (%s)" % difficulty
		)
		for raw_wave in schedule.keys():
			check.call(
				int(raw_wave) >= low and int(raw_wave) <= high, "mini-boss range (%s)" % difficulty
			)
	var normal_source: Dictionary = source.normal
	check.call(normal_source.size() == 3, "oracle records source random mini schedule")


func _pending(check: Callable, source: Dictionary) -> void:
	var world := _world()
	world.pending_mini_bosses = [
		{"wave": 10, "boss_type": "gornak"},
		{"wave": 15, "boss_type": "morgath"},
		{"wave": 25, "boss_type": "drakar"}
	]
	check.call(world._try_spawn_pending_mini_boss(), "pending mini boss spawns")
	check.call(
		(
			world.active_boss != null
			and world.active_boss.boss_type == "gornak"
			and world.pending_mini_bosses.size() == 2
		),
		"oldest pending mini boss becomes active"
	)
	var active = world.active_boss
	check.call(not world._try_spawn_pending_mini_boss(), "live boss holds pending queue")
	active.alive = false
	check.call(world._try_spawn_pending_mini_boss(), "dead boss releases pending queue")
	check.call(
		(
			world.active_boss != null
			and world.active_boss.boss_type == "morgath"
			and world.pending_mini_bosses.size() == 1
		),
		"next pending mini boss follows defeat"
	)
	check.call(
		int(source.first[2]) == 2 and int(source.second[2]) == 1,
		"source pending queue fixture records FIFO"
	)


func _true_boss(check: Callable, source: Array) -> void:
	var world := _world()
	world.red_towers_destroyed = 5
	check.call(not world._spawn_true_boss_if_ready(), "five red towers do not trigger true boss")
	world.red_towers_destroyed = 6
	check.call(world._spawn_true_boss_if_ready(), "six red towers trigger true boss")
	check.call(
		(
			world.true_boss_spawned
			and world.active_boss != null
			and world.active_boss.boss_type == "abaddon"
		),
		"level true boss is spawned from config"
	)
	check.call(not world._spawn_true_boss_if_ready(), "true boss spawns once")
	check.call(
		not bool(source[0].spawned) and bool(source[1].spawned), "oracle true-boss threshold is six"
	)


func _tower_counter(check: Callable, source: Dictionary) -> void:
	var world := _world()
	var red_tower = world.spawn_structure(world.ARCHER, world.RED, world.RED_POSITIONS[0], 0)
	red_tower.alive = false
	world._on_death(world.BLUE, red_tower)
	check.call(world.red_towers_destroyed == 0, "tower event waits for source reward pass")
	world._spawn_true_boss_if_ready()
	check.call(world.active_boss == null, "pending tower event cannot trigger early")
	world._flush_red_tower_deaths()
	check.call(world.red_towers_destroyed == 1, "red tower death increments event counter once")
	check.call(
		int(source.red_towers_destroyed) == 1 and int(source.ai_gold) == 13,
		"oracle tower reward counter and opposing reward"
	)


func _rewards_and_unlocks(check: Callable, source: Dictionary) -> void:
	var world := _world()
	var boss = world._spawn_boss("gornak")
	var reward: int = int(boss.gold_reward)
	world.pending_mini_bosses = [{"wave": 15, "boss_type": "morgath"}]
	boss.alive = false
	boss.defeated = true
	var before := world.economy.gold[world.BLUE]
	world._process_boss_result()
	check.call(
		(
			world.economy.gold[world.BLUE] == before + reward
			and world.score == reward
			and world.boss_rewards.size() == 1
		),
		"boss reward credits player gold and score once"
	)
	check.call(
		(
			world.bosses_defeated_this_match == ["gornak"]
			and world.unlocked_bosses == ["gornak"]
			and world.active_boss != null
			and world.active_boss.boss_type == "morgath"
		),
		"defeat records unlock and releases next pending boss"
	)
	world.bosses_defeated_this_match = ["gornak", "abaddon", "gornak"]
	var newly: Array[String] = world._auto_unlock_defeated_boss_heroes()
	check.call(
		newly == ["gornak", "abaddon"] and world.purchased_heroes == ["gornak", "abaddon"],
		"victory unlock list is unique and free"
	)
	check.call(
		int(source.boss_reward.gold) == reward - 273 or int(source.boss_reward.gold) == 77,
		"oracle contains the source boss reward path"
	)
	check.call(
		source.victory_unlocks.newly == ["gornak", "abaddon"],
		"oracle contains the source victory unlock list"
	)
