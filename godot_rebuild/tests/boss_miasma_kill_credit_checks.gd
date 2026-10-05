extends RefCounted
## 9d: a Miasma tick must use the source Boss.take_damage call shape, which
## omits `source`; a lethal tick cannot award the Basilisk Breath owner a boss
## kill. The replay runs hero_basic_attack -> live item registry ->
## _tick_auras_and_items -> BattleItemEffects -> _deliver_hit -> BossState and
## then the production boss-result pass. A legacy bus preserves the post-9c
## source ID to prove the old native kill-credit counterfactual.

const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const KAIZEN = preload("res://data/heroes/kaizen.tres")
const FIXTURE := "res://tests/fixtures/boss_miasma_kill_credit_source.json"

const BASIC_DAMAGE := 50
const TICK_FRAMES := 30
const GAP_SCENARIOS := ["miasma_lethal_blue_owner", "miasma_lethal_red_owner"]
const RESULT_FIELDS := [
	"miasma_damage",
	"tick_damage",
	"boss_hp_loss_from_tick",
	"boss_alive_after_tick",
	"boss_alive_after_schedule",
	"owner_kills",
	"miniboss_kill_count",
	"trueboss_kill_count",
]


class MiasmaKillCreditBus:
	extends BattleItemEffects
	var legacy := false

	func deal_damage_from(
		source_id: int,
		source_team: int,
		source_pos: Vector2,
		target_id: int,
		amount: int,
		school: String = "magic",
		damage_type: String = "magic"
	) -> int:
		if legacy:
			return _legacy_deal_damage_from(
				source_id, source_team, source_pos, target_id, amount, school, damage_type
			)
		return super.deal_damage_from(
			source_id, source_team, source_pos, target_id, amount, school, damage_type
		)

	func _legacy_deal_damage_from(
		source_id: int,
		source_team: int,
		source_pos: Vector2,
		target_id: int,
		amount: int,
		school: String,
		damage_type: String
	) -> int:
		# Pre-9d (post-9c) behavior: preserve the stored owner as `source`, while
		# keeping the fixed magic damage_type so the 9c blind gate stays closed.
		var target: Object = world.get_unit(target_id)
		if target == null:
			return 0
		var origin := source_pos
		var source: Object = world.get_unit(source_id)
		if source != null:
			var current_pos: Variant = source.get("position")
			if current_pos is Vector2:
				origin = current_pos
		world._deliver_hit(source_id, source_team, target, amount, school, origin, damage_type)
		return amount


class MiasmaKillCreditWorld:
	extends Prior.CleaveChainWorld
	var legacy_miasma := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		_bind_miasma_registry(source_hero)
		source_hero.items.miasma = _miasma_registry
		var bus := MiasmaKillCreditBus.new()
		bus.world = self
		bus.legacy = legacy_miasma
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "9d Miasma kill-credit fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	var cases: Array = fixture.get("cases", [])
	check.call(cases.size() == 864, "9d has four kill-credit cases for all 216 boss types")
	if cases.size() != 864:
		return
	_check_source_shape(check, fixture)
	var helper := Prior.new()
	var world := MiasmaKillCreditWorld.new()
	world.setup_arena()
	for row: Dictionary in cases:
		var expected: Dictionary = _replay(check, helper, world, row, false)
		var expected_fixture: Dictionary = row.get("expected", {})
		check.call(_matches(expected, expected_fixture), "9d source Miasma outcome " + _label(row))
		world.legacy_miasma = true
		var native_old: Dictionary = _replay(check, helper, world, row, true)
		var native_old_fixture: Dictionary = row.get("native_old", {})
		check.call(
			_matches(native_old, native_old_fixture),
			"9d pre-slice native kill-credit counterfactual " + _label(row)
		)
		var gap: bool = GAP_SCENARIOS.has(String(row.get("scenario", "")))
		check.call(
			(not _same_result(expected, native_old)) == gap,
			"9d source/native divergence is limited to lethal Miasma " + _label(row)
		)
		if gap:
			check.call(
				(
					int(expected.get("owner_kills", -1)) == 0
					and int(native_old.get("owner_kills", -1)) == 1
				),
				"9d lethal Miasma must not credit its stored owner " + _label(row)
			)
		elif String(row.get("scenario", "")) == "miasma_nonlethal_then_hero_lethal":
			check.call(
				(
					int(expected.get("owner_kills", -1)) == 1
					and int(native_old.get("owner_kills", -1)) == 1
				),
				"9d direct lethal hero strike still receives boss kill credit " + _label(row)
			)
	_helper_reset(helper, world)


func _replay(
	check: Callable, helper: Prior, world: MiasmaKillCreditWorld, row: Dictionary, legacy: bool
) -> Dictionary:
	helper._reset_world(world, false)
	world.legacy_miasma = legacy
	world._miasma_registry.clear()
	world.deliveries = {}
	world.hit_order = []
	world.recent_events.clear()

	var boss: BossState = world._spawn_boss(String(row.get("boss_type", "")))
	if boss == null:
		check.call(false, "9d boss data loads " + _label(row))
		return {}
	var boss_team := _team(String(row.get("boss_team", "red")), world)
	boss.team = boss_team
	boss.position = Vector2(700.0, 300.0)
	boss.previous_position = boss.position
	boss.entrance_timer = 0
	boss.timer = 0
	var owner_team := _team(String(row.get("owner_team", "blue")), world)
	var hero := world.spawn_hero(KAIZEN, owner_team, boss.position + Vector2(-40.0, 0.0))
	if hero == null:
		check.call(false, "9d Miasma owner spawns " + _label(row))
		return {}
	hero.position = boss.position + Vector2(-40.0, 0.0)
	hero.target_id = boss.id
	hero.attack_timer = 0
	hero.items.hero_melee_flag = 1
	hero.items.hero_range = 70.0
	check.call(hero.items.add("basilisk_breath"), "9d equip Basilisk Breath " + _label(row))
	check.call(
		world.hero_basic_attack(hero.id, boss.id),
		"9d real hero attack applies Basilisk Breath to the boss " + _label(row)
	)

	var tracker: Dictionary = world._miasma_registry.get(int(boss.id), {})
	var miasma_damage := int(tracker.get("damage", 0))
	check.call(miasma_damage > 0, "9d on-hit creates a live boss Miasma tracker " + _label(row))
	boss.hp = float(row.get("boss_hp_before_tick", 1))
	world.deliveries = {}
	var hp_before_tick := boss.hp
	for _frame in range(TICK_FRAMES):
		world._tick_auras_and_items()
	var boss_deliveries: Array = world.deliveries.get(int(boss.id), [])
	var tick_damage := 0
	if not boss_deliveries.is_empty():
		tick_damage = int((boss_deliveries[0] as Array)[0])
	var hp_loss := int(roundf(hp_before_tick - boss.hp))
	var alive_after_tick := boss.alive

	if String(row.get("mode", "")) == "hero_followup":
		hero.attack_timer = 0
		boss.hp = 1.0
		check.call(
			world.hero_basic_attack(hero.id, boss.id),
			"9d direct follow-up hero strike uses the real attack path " + _label(row)
		)
	world._process_boss_result()
	return {
		"miasma_damage": miasma_damage,
		"tick_damage": tick_damage,
		"boss_hp_loss_from_tick": hp_loss,
		"boss_alive_after_tick": alive_after_tick,
		"boss_alive_after_schedule": boss.alive,
		"owner_kills": hero.kills,
		"miniboss_kill_count": world.miniboss_kill_count,
		"trueboss_kill_count": world.trueboss_kill_count,
		"last_hit_source_id": boss.last_hit_source_id,
		"owner_id": hero.id,
	}


func _team(team_name: String, world: MiasmaKillCreditWorld) -> int:
	return world.BLUE if team_name == "blue" else world.RED


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	for field: String in RESULT_FIELDS:
		if not actual.has(field) or not expected.has(field):
			return false
		var value: Variant = expected[field]
		if value is bool:
			if bool(actual[field]) != bool(value):
				return false
		elif int(actual[field]) != int(value):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	for field: String in RESULT_FIELDS:
		if left.get(field) != right.get(field):
			return false
	return true


func _check_source_shape(check: Callable, fixture: Dictionary) -> void:
	var source: Dictionary = fixture.get("source", {})
	var shape: Dictionary = source.get("ast_shape", {})
	var flags := [
		"miasma_tick_calls_magic_without_source",
		"boss_stores_source_only_in_lethal_branch",
		"boss_kill_pass_reads_killed_by",
		"boss_kill_pass_requires_hero",
	]
	var valid := shape.size() == flags.size()
	for flag: String in flags:
		valid = valid and bool(shape.get(flag, false))
	check.call(
		(
			valid
			and String(source.get("miasma_damage_type", "")) == "magic"
			and source.get("miasma_source_argument") == null
			and int(source.get("first_tick_frames", 0)) == TICK_FRAMES
		),
		"9d Python AST proves magic Miasma omits the Boss.take_damage source"
	)
	check.call(
		int(fixture.get("boss_type_count", 0)) == 216 and int(fixture.get("case_count", 0)) == 864,
		"9d fixture contains four counterfactual cases for every boss type"
	)


func _helper_reset(helper: Prior, world: MiasmaKillCreditWorld) -> void:
	helper._reset_world(world, false)
	world._miasma_registry.clear()


func _label(row: Dictionary) -> String:
	return String(row.get("boss_type", "")) + "/" + String(row.get("scenario", ""))
