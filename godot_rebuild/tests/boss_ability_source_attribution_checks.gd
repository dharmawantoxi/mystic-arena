# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8u native suite: `Boss._use_ability` and every `_smart_ai_*` /
## persistent ability `take_damage` call in `bosses/base_boss.py` omits
## `source=` (`source=None`), whereas only the primary basic attack in
## `Boss.update` passes `source=self`. `BossAI._hit` therefore delivers ability
## and skill hits with `source_id = -1`, so:
## 1. Attacker blind (`boss.blind_timer > 0`) does not make boss abilities miss.
## 2. Thorne's Bristleback still reduces incoming physical damage by 30%, but
##    does not reflect 25% damage back onto the boss.
## 3. `HeroItemInventory.notify_damage_taken` still resets Leviathan Heart's
##    `last_damage_timer = 300`, but does not reflect Razor Carapace Thornmail
##    damage onto the boss.
## 4. Lethal ability hits leave `hero.killed_by == -1`.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const THORNE = preload("res://data/heroes/thorne.tres")
const FIXTURE := "res://tests/fixtures/boss_ability_source_attribution.json"

const SOURCE_FLAGS := [
	"basic_attack_passes_source_self",
	"cleave_omits_source",
	"generic_ability_omits_source",
	"all_ability_take_damage_calls_omit_source",
	"hero_blind_requires_source",
	"bristleback_reflect_requires_source",
	"razor_carapace_reflect_requires_source",
	"hero_killed_by_requires_source"
]


class AttributionWorld:
	extends Prototype
	var inject_boss_source := false
	var reflect_hits: Array[int] = []
	var target_hit_sources: Array[int] = []
	var tracked_target_id := -1

	func _deliver_hit(
		source_id: int,
		source_team: int,
		target: UnitState,
		raw_damage: int,
		school: String,
		origin: Vector2,
		damage_type: String = "normal"
	) -> bool:
		if (
			target is BossState
			and source_id == -1
			and active_boss != null
			and source_team != active_boss.team
		):
			reflect_hits.append(raw_damage)
		var eff_source := source_id
		if (
			inject_boss_source
			and source_id == -1
			and active_boss != null
			and source_team == active_boss.team
		):
			eff_source = active_boss.id
		if target != null and target.id == tracked_target_id and raw_damage > 0:
			target_hit_sources.append(eff_source)
		return super._deliver_hit(
			eff_source, source_team, target, raw_damage, school, origin, damage_type
		)


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	var parsed: bool = fixture is Dictionary and fixture.has("source") and fixture.has("cases")
	if parsed:
		for flag in SOURCE_FLAGS:
			parsed = parsed and bool(fixture.source.get(flag, false))
	check.call(parsed, "boss ability source attribution fixture parses with every source flag")
	if not fixture is Dictionary:
		return
	_check_source_meta(check, fixture)
	_replay_cases(check, fixture)
	_live_match_contrasts(check)
	_persistent_ability_ticks(check)


func _check_source_meta(check: Callable, fixture: Dictionary) -> void:
	var src: Dictionary = fixture.get("source", {})
	(
		check
		. call(
			(
				int(src.get("ability_take_damage_call_count", 0)) == 177
				and int(src.get("razor_carapace_armor", 0)) == 12
				and is_equal_approx(float(src.get("razor_carapace_reflect_pct", 0.0)), 0.35)
				and int(src.get("leviathan_combat_timeout", 0)) == 300
			),
			"source metadata records all 177 source-omitted ability take_damage calls and item constants"
		)
	)


func _run_single_scenario(
	world: AttributionWorld, boss_type: String, scenario: String, inject_boss_source: bool
) -> Dictionary:
	world.units.clear()
	world.projectiles.clear()
	world.recent_events.clear()
	world.reflect_hits.clear()
	world.target_hit_sources.clear()
	world.inject_boss_source = inject_boss_source
	if world.active_boss != null:
		world._by_id.erase(world.active_boss.id)
		world.active_boss = null
	var boss: BossState = world._spawn_boss(boss_type)
	if boss == null:
		return {}
	boss.position = Vector2.ZERO
	boss.previous_position = boss.position
	boss.hp = float(boss.max_hp)
	boss.blind_timer = 30 if scenario == "blind_boss_ability_lands" else 0
	boss.blind_amount = 1.0 if scenario == "blind_boss_ability_lands" else 0.0

	var start_hp := 1 if scenario == "lethal_ability_preserves_uncredited_killed_by" else 10000
	var target: HeroState = world.spawn_hero(THORNE, world.BLUE, Vector2(20.0, 0.0))
	target.max_hp = 10000.0
	target.hp = float(start_hp)
	target.alive = true
	target.deaths = 0
	target.killed_by = -1
	target.attack_timer = 0
	target.bristleback_timer = 180 if scenario == "bristleback_mitigates_without_reflect" else 0
	if scenario == "razor_carapace_combat_timer_without_reflect":
		target.items.add("razor_carapace")
		target.items.add("leviathan_heart")
		target.items.thorn_timer = 180
		target.items.last_damage_timer = 0
		target.max_hp = 10000.0
		target.hp = float(start_hp)

	var ally: HeroState = world.spawn_hero(THORNE, world.BLUE, Vector2(30.0, 0.0))
	ally.max_hp = 10000.0
	ally.hp = 10000.0
	ally.alive = true
	ally.attack_timer = 0

	world.tracked_target_id = target.id
	var enemies: Array[UnitState] = [target, ally]
	var steps := 2 if boss_type in ["kunkka", "xerathis", "solvarin"] else 1
	var boss_hp_after_cast := int(boss.hp)
	for _step in range(steps):
		BossAI.tick(world, boss, enemies, target, 20.0)
		if world.reflect_hits.is_empty():
			boss_hp_after_cast = int(boss.hp)
	var attributed := false
	for src_id in world.target_hit_sources:
		if src_id == boss.id:
			attributed = true
			break
	var reflect_sum := 0
	for hit in world.reflect_hits:
		reflect_sum += hit
	return {
		"steps": steps,
		"skill": boss.active_skill,
		"target_hp": int(target.hp),
		"target_alive": target.alive,
		"target_deaths": target.deaths,
		"damage_taken": start_hp - int(target.hp),
		"boss_hp": boss_hp_after_cast,
		"last_damage_timer": target.items.last_damage_timer,
		"killed_by_boss": target.killed_by == boss.id,
		"hit_source_attributed": attributed,
		"reflect_count": world.reflect_hits.size(),
		"reflect_raw": reflect_sum
	}


func _matches_outcome(actual: Dictionary, expected: Dictionary) -> bool:
	for key in [
		"steps",
		"skill",
		"target_hp",
		"target_alive",
		"target_deaths",
		"damage_taken",
		"boss_hp",
		"last_damage_timer",
		"killed_by_boss",
		"hit_source_attributed",
		"reflect_count",
		"reflect_raw"
	]:
		if actual.get(key) != expected.get(key):
			return false
	return true


func _replay_cases(check: Callable, fixture: Dictionary) -> void:
	var cases: Array = fixture.get("cases", [])
	check.call(
		cases.size() == 864,
		"boss ability source attribution has four source cases for all 216 boss types"
	)
	var world := AttributionWorld.new()
	world.setup_arena()
	var counts := {}
	for entry in cases:
		var boss_type := String(entry.get("boss_type", ""))
		var scenario := String(entry.get("scenario", ""))
		var expected: Dictionary = entry.get("expected", {})
		var contrast: Dictionary = entry.get("expected_with_boss_source", {})
		counts[boss_type] = int(counts.get(boss_type, 0)) + 1
		var actual := _run_single_scenario(world, boss_type, scenario, false)
		var actual_contrast := _run_single_scenario(world, boss_type, scenario, true)
		check.call(
			_matches_outcome(actual, expected),
			"boss ability uncredited hit matches source expected: %s (%s)" % [boss_type, scenario]
		)
		check.call(
			_matches_outcome(actual_contrast, contrast),
			(
				"boss ability attributed contrast matches pre-layer behavior: %s (%s)"
				% [boss_type, scenario]
			)
		)
		check.call(
			actual != actual_contrast,
			"boss ability source attribution changes outcome on %s (%s)" % [boss_type, scenario]
		)
	for boss_type in counts:
		check.call(
			int(counts[boss_type]) == 4,
			"boss ability source attribution has four cases for %s" % boss_type
		)


func _live_match_contrasts(check: Callable) -> void:
	# 1. Blinded boss in live step_tick: basic attack misses while ability lands.
	var blind_world := Prototype.new()
	blind_world.setup_arena()
	blind_world.units.clear()
	var blind_boss: BossState = blind_world._spawn_boss("gornak")
	var blind_hero: HeroState = blind_world.spawn_hero(
		THORNE, blind_world.BLUE, Vector2(520.0, 340.0)
	)
	check.call(
		blind_boss != null and blind_hero != null, "live blinded-boss contrast entities spawn"
	)
	if blind_boss == null or blind_hero == null:
		return
	blind_boss.entrance_timer = 0
	blind_boss.position = Vector2(500.0, 340.0)
	blind_boss.previous_position = blind_boss.position
	blind_boss.blind_timer = 30
	blind_boss.blind_amount = 1.0
	blind_hero.max_hp = 10000.0
	blind_hero.hp = 10000.0
	blind_hero.attack_timer = 999
	blind_boss.q_timer = 999
	blind_boss.w_timer = 999
	blind_boss.e_timer = 999
	blind_boss.r_timer = 999
	blind_boss.timer = 0
	blind_world._step_active_boss()
	check.call(
		blind_hero.hp == 10000.0,
		"blinded boss basic attack misses in _step_active_boss because basic attack passes boss.id"
	)
	blind_boss.timer = 999
	blind_boss.q_timer = 0
	blind_world._step_active_boss()
	check.call(
		blind_hero.hp == 10000.0 - float(blind_boss.skill_q_damage),
		"blinded boss ability lands in _step_active_boss because BossAI._hit passes source_id -1"
	)

	# 2. Bristleback in live _step_active_boss: ability does not reflect, basic attack reflects.
	var bb_world := Prototype.new()
	bb_world.setup_arena()
	bb_world.units.clear()
	var bb_boss: BossState = bb_world._spawn_boss("gornak")
	var bb_hero: HeroState = bb_world.spawn_hero(THORNE, bb_world.BLUE, Vector2(520.0, 340.0))
	check.call(bb_boss != null and bb_hero != null, "live Bristleback contrast entities spawn")
	if bb_boss == null or bb_hero == null:
		return
	bb_boss.entrance_timer = 0
	bb_boss.position = Vector2(500.0, 340.0)
	bb_boss.previous_position = bb_boss.position
	bb_hero.max_hp = 10000.0
	bb_hero.hp = 10000.0
	bb_hero.bristleback_timer = 180
	bb_boss.timer = 999
	bb_boss.q_timer = 0
	bb_boss.w_timer = 999
	bb_boss.e_timer = 999
	bb_boss.r_timer = 999
	var boss_hp_before := bb_boss.hp
	bb_world._step_active_boss()
	check.call(
		bb_hero.hp < 10000.0 and bb_boss.hp == boss_hp_before,
		"live boss ability is mitigated by Bristleback without reflecting onto the boss"
	)
	bb_boss.timer = 0
	bb_boss.q_timer = 999
	bb_world._step_active_boss()
	check.call(
		bb_boss.hp < boss_hp_before,
		"live boss basic attack triggers Bristleback reflect onto the boss"
	)

	# 3. Lethal ability vs lethal basic attack killer attribution.
	var kill_world := Prototype.new()
	kill_world.setup_arena()
	kill_world.units.clear()
	var kill_boss: BossState = kill_world._spawn_boss("gornak")
	var ability_victim: HeroState = kill_world.spawn_hero(
		THORNE, kill_world.BLUE, Vector2(520.0, 340.0)
	)
	check.call(
		kill_boss != null and ability_victim != null, "live lethal attribution entities spawn"
	)
	if kill_boss == null or ability_victim == null:
		return
	kill_boss.entrance_timer = 0
	kill_boss.position = Vector2(500.0, 340.0)
	kill_boss.previous_position = kill_boss.position
	ability_victim.hp = 1.0
	kill_boss.timer = 999
	kill_boss.q_timer = 0
	kill_boss.w_timer = 999
	kill_boss.e_timer = 999
	kill_boss.r_timer = 999
	kill_world._step_active_boss()
	check.call(
		not ability_victim.alive and ability_victim.killed_by == -1,
		"lethal boss ability leaves hero.killed_by at -1"
	)
	var basic_victim: HeroState = kill_world.spawn_hero(
		THORNE, kill_world.BLUE, Vector2(520.0, 340.0)
	)
	basic_victim.hp = 1.0
	kill_boss.timer = 0
	kill_boss.q_timer = 999
	kill_world._step_active_boss()
	check.call(
		not basic_victim.alive and basic_victim.killed_by == kill_boss.id,
		"lethal boss basic attack attributes hero.killed_by to boss.id"
	)


func _persistent_ability_ticks(check: Callable) -> void:
	# Morgath Flux DoT + Tempest Double clone hit and Kunkka X-Mark delayed burst
	# also route through BossAI._hit with source_id -1.
	var world := AttributionWorld.new()
	world.setup_arena()
	world.units.clear()
	var morgath: BossState = world._spawn_boss("morgath")
	var target: HeroState = world.spawn_hero(THORNE, world.BLUE, Vector2(20.0, 0.0))
	check.call(morgath != null and target != null, "persistent ability tick entities spawn")
	if morgath == null or target == null:
		return
	morgath.position = Vector2.ZERO
	morgath.previous_position = morgath.position
	morgath.blind_timer = 30
	morgath.blind_amount = 1.0
	morgath.q_timer = 999
	morgath.w_timer = 999
	morgath.e_timer = 999
	morgath.r_timer = 999
	morgath.flux_target_id = target.id
	morgath.flux_active_timer = 31
	morgath.clones_active_timer = 41
	target.max_hp = 10000.0
	target.hp = 10000.0
	target.bristleback_timer = 180
	world.tracked_target_id = target.id
	var enemies: Array[UnitState] = [target]
	BossAI.tick(world, morgath, enemies, target, 20.0)
	check.call(
		(
			target.hp < 10000.0
			and world.target_hit_sources == [-1, -1]
			and world.reflect_hits.is_empty()
		),
		"Morgath Flux DoT and Tempest Double clone ticks deliver uncredited hits without reflect"
	)

	world.units.clear()
	world.target_hit_sources.clear()
	world.reflect_hits.clear()
	world._by_id.erase(morgath.id)
	world.active_boss = null
	var kunkka: BossState = world._spawn_boss("kunkka")
	var mark_target: HeroState = world.spawn_hero(THORNE, world.BLUE, Vector2(20.0, 0.0))
	if kunkka == null or mark_target == null:
		return
	kunkka.position = Vector2.ZERO
	kunkka.previous_position = kunkka.position
	kunkka.blind_timer = 30
	kunkka.blind_amount = 1.0
	kunkka.q_timer = 999
	kunkka.w_timer = 999
	kunkka.e_timer = 999
	kunkka.r_timer = 999
	kunkka.x_mark_target_id = mark_target.id
	kunkka.x_mark_timer = 1
	mark_target.max_hp = 10000.0
	mark_target.hp = 10000.0
	mark_target.bristleback_timer = 180
	world.tracked_target_id = mark_target.id
	var mark_enemies: Array[UnitState] = [mark_target]
	BossAI.tick(world, kunkka, mark_enemies, mark_target, 20.0)
	check.call(
		(
			mark_target.hp < 10000.0
			and world.target_hit_sources == [-1]
			and world.reflect_hits.is_empty()
		),
		"Kunkka X-Mark delayed burst delivers uncredited hit without reflect"
	)
