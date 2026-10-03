# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8l native suite: source `Game._process_boss_kill` attribution for the
## active boss. Only a real enemy hero landing the lethal hit is credited; the
## mini/true boss counters only advance for a blue killer. The source oracle
## executes the real `Boss.take_damage` death branch plus the real
## `_killer_is_hero`/`_process_boss_kill`/`_unlock_achievement` methods.
##
## The achievement banner is presentation and stays outside this port, so the
## fixture's achievement payload is only used to prove the counter value is the
## one the source would have put into `miniboss_kill_N`/`trueboss_kill_N`.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/boss_kill_credit_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		fixture is Dictionary and fixture.has("killer_cases"), "boss kill credit fixture parses"
	)
	if not fixture is Dictionary:
		return
	_replay_killer_cases(check, fixture)
	_match_step_handoff(check)
	_source_omitted_and_non_hero_handoff(check)
	_dead_killer_still_credited(check)
	_retirement_guards_counter(check)


func _world() -> Prototype:
	var world := Prototype.new()
	world.setup_arena()
	return world


func _team_of(entry: Dictionary, world: Prototype) -> int:
	# The fixture stores `killer_team: null` for the source-omitted case, and
	# JSON null survives Dictionary.get(), so compare the raw Variant.
	return world.BLUE if entry.get("killer_team") == "blue" else world.RED


func _killer_of(world: Prototype, entry: Dictionary) -> UnitState:
	# Source shapes: a Hero carries `hero_type`+`skills`, a Minion/Tower carries
	# neither, and `source=None` is how cleave splash and the burn tick call.
	var kind: Variant = entry.get("killer_kind", "none")
	var team := _team_of(entry, world)
	if kind == "hero":
		return world.spawn_hero(KAIZEN, team, Vector2(620.0, 300.0))
	if kind == "minion":
		return world.spawn_unit(GOBLIN, team, 0)
	return null


func _kills_of(killer: UnitState) -> int:
	if killer is HeroState:
		return (killer as HeroState).kills
	return 0


func _replay_killer_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("killer_cases", [])
	check.call(cases.size() == 864, "boss kill credit has four source cases for all 216 boss types")
	var world := _world()
	var boss_counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var label := String(entry.get("label", "unknown"))
		boss_counts[boss_type] = int(boss_counts.get(boss_type, 0)) + 1
		world.units.clear()
		world.active_boss = null
		world.recent_events.clear()
		world.miniboss_kill_count = 0
		world.trueboss_kill_count = 0
		var boss: BossState = world._spawn_boss(boss_type)
		check.call(boss != null, "boss kill credit data loads: %s" % boss_type)
		if boss == null:
			continue
		boss.team = world.RED
		boss.position = Vector2(700.0, 300.0)
		boss.previous_position = boss.position
		var killer := _killer_of(world, entry)
		boss.last_hit_source_id = killer.id if killer != null else -1
		var before := _kills_of(killer)
		boss.hp = 0.0
		boss.alive = false
		boss.defeated = true
		world._process_boss_result()
		var expected_kills := int(entry.get("credited_kills", 0))
		check.call(
			_kills_of(killer) - before == expected_kills,
			"boss kill credit matches source: %s (%s)" % [label, boss_type]
		)
		check.call(
			(
				world.miniboss_kill_count == int(entry.get("miniboss_kill_count", 0))
				and world.trueboss_kill_count == int(entry.get("trueboss_kill_count", 0))
			),
			"boss kill counters match source: %s (%s)" % [label, boss_type]
		)
		var achievement = entry.get("achievement")
		if achievement != null:
			# Source builds `miniboss_kill_N` / `trueboss_kill_N` from the counter
			# it just advanced, so the counter is the id's numeric suffix.
			var achievement_id := String(achievement.get("achievement_id", ""))
			var suffix := achievement_id.get_slice("_", 2)
			var counter := (
				world.trueboss_kill_count
				if String(entry.get("boss_class", "mini")) == "true"
				else world.miniboss_kill_count
			)
			check.call(
				suffix == str(counter),
				"boss kill counter matches the source achievement id: %s" % boss_type
			)
		else:
			check.call(
				(
					world.miniboss_kill_count == 0
					and world.trueboss_kill_count == 0
					and _kills_of(killer) == before
				),
				"uncredited boss death stays out of the source counters: %s" % label
			)
	for boss_type in boss_counts:
		check.call(
			int(boss_counts[boss_type]) == 4,
			"boss kill credit has exactly four cases for %s" % boss_type
		)


func _match_step_handoff(check: Callable) -> void:
	var world := _world()
	world.units.clear()
	world.recent_events.clear()
	world.active_boss = null
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "boss kill credit handoff boss spawns")
	if boss == null:
		return
	boss.team = world.RED
	boss.position = Vector2(700.0, 300.0)
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.hp = 10.0
	var hero := world.spawn_hero(KAIZEN, world.BLUE, Vector2(690.0, 300.0))
	check.call(hero != null, "boss killer hero spawns")
	if hero == null:
		return
	world._deliver_hit(hero.id, world.BLUE, boss, 100, "physical", hero.position)
	check.call(not boss.alive and boss.defeated, "lethal hero hit defeats the active boss")
	check.call(
		boss.last_hit_source_id == hero.id,
		"lethal hero hit preserves the source id for the death pass"
	)
	world.step_tick()
	check.call(hero.kills == 1, "match step credits the hero that slew the mini boss")
	check.call(
		(
			world.miniboss_kill_count == 1
			and world.trueboss_kill_count == 0
			and world.boss_rewards.size() == 1
		),
		"mini boss counter advances exactly once with the reward"
	)
	world._process_boss_result()
	check.call(
		hero.kills == 1 and world.miniboss_kill_count == 1 and world.boss_rewards.size() == 1,
		"retired boss cannot credit a second kill"
	)


func _source_omitted_and_non_hero_handoff(check: Callable) -> void:
	var world := _world()
	var boss: BossState = world._spawn_boss("gornak")
	check.call(boss != null, "boss kill credit cleave boss spawns")
	if boss == null:
		return
	boss.team = world.RED
	boss.position = Vector2(700.0, 300.0)
	boss.entrance_timer = 0
	boss.hp = 10.0
	world._deliver_hit(-1, world.BLUE, boss, 100, "neutral", boss.position)
	check.call(not boss.alive, "source-omitted lethal hit defeats the boss")
	check.call(boss.last_hit_source_id == -1, "source-omitted lethal hit keeps no attacker")
	world._process_boss_result()
	check.call(
		world.miniboss_kill_count == 0 and world.trueboss_kill_count == 0,
		"cleave-style lethal hit credits no boss kill"
	)
	world.recent_events.clear()
	var minion_killer := world.spawn_unit(GOBLIN, world.BLUE, 0)
	check.call(minion_killer != null, "non-hero killer spawns for the credit boundary")
	if minion_killer == null:
		return
	var second: BossState = world._spawn_boss("morgath")
	check.call(second != null, "non-hero killer boss spawns")
	if second == null:
		return
	second.team = world.RED
	second.position = Vector2(700.0, 300.0)
	second.hp = 10.0
	world._deliver_hit(minion_killer.id, world.BLUE, second, 100, "physical", second.position)
	check.call(not second.alive, "non-hero lethal hit defeats the boss")
	check.call(
		second.last_hit_source_id == minion_killer.id,
		"non-hero lethal hit is preserved as the attacker id"
	)
	world._process_boss_result()
	check.call(
		world.miniboss_kill_count == 0,
		"minion lethal hit credits neither kills nor the boss counter"
	)


func _dead_killer_still_credited(check: Callable) -> void:
	# Source `_killer_is_hero` never reads `alive`, and the native registry keeps
	# dead heroes addressable, so a killer that dies before the death pass still
	# takes the credit.
	var world := _world()
	world.units.clear()
	world.recent_events.clear()
	world.active_boss = null
	var boss: BossState = world._spawn_boss("drakar")
	check.call(boss != null, "dead killer boss spawns")
	if boss == null:
		return
	boss.team = world.RED
	boss.position = Vector2(700.0, 300.0)
	boss.entrance_timer = 0
	boss.hp = 10.0
	var hero := world.spawn_hero(KAIZEN, world.BLUE, Vector2(690.0, 300.0))
	if hero == null:
		return
	world._deliver_hit(hero.id, world.BLUE, boss, 100, "physical", hero.position)
	hero.alive = false
	world.step_tick()
	check.call(
		world.get_unit(hero.id) == hero, "dead hero stays addressable in the source-shaped registry"
	)
	check.call(hero.kills == 1, "dead hero still takes the credit it earned")


func _retirement_guards_counter(check: Callable) -> void:
	var world := _world()
	var boss: BossState = world._spawn_boss("abaddon")
	check.call(boss != null and boss.boss_class == "true", "true boss spawns for the counter path")
	if boss == null:
		return
	boss.team = world.RED
	boss.position = Vector2(700.0, 300.0)
	boss.entrance_timer = 0
	boss.hp = 10.0
	var hero := world.spawn_hero(KAIZEN, world.BLUE, Vector2(690.0, 300.0))
	if hero == null:
		return
	world._deliver_hit(hero.id, world.BLUE, boss, 100, "physical", hero.position)
	world._process_boss_result()
	check.call(
		world.trueboss_kill_count == 1 and world.miniboss_kill_count == 0,
		"true boss death advances only the true boss counter"
	)
	check.call(world.active_boss == null, "boss death retires the active slot")
