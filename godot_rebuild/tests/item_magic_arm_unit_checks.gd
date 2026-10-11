extends RefCounted
## 9r: the on-hit magic arms must reach MINION and HERO victims with the source
## call shape — the third positional argument of
## `u.take_damage(chain["damage"], h.team, "magic")` (`hero_items.py:2568`) and
## `target.take_damage(b["damage"], h.team, "magic")` (`:2589`) is the damage
## TYPE. Layer 9g routed the boss victim with `"magic"`; layers 9p/9q made the
## unit victims sourceless but still delivered the `"normal"` default, so a
## Windrun hero rolled the 75% miss gate and an evasive hero rolled Monarch
## Wings against an arm the source marks as magic. Both gates are
## `_is_physical_hit` driven (`_entity.py:92-103`), so `_hero_denies_hit` must
## read the damage type too, not the school alone.
##
## The replay drives the real inventory arm through the production bus into
## `_deliver_hit`; a legacy bus reproduces the pre-9r delivery and a legacy
## world reproduces the pre-9r windrun gate for the counterfactual column. A
## physical control pins that Windrun still rolls for real physical hits.

const BattleItemEffects = preload("res://scripts/match/battle_item_effects.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prior = preload("res://tests/boss_item_cleave_chain_checks.gd")
const TROLL = preload("res://data/minions/troll.tres")
const FIXTURE := "res://tests/fixtures/item_magic_arm_unit_source.json"
const EVASION_ITEM := "monarch_wings"
const ARMOR_ITEM := "steel_aegis"
const POS := Vector2(400.0, 380.0)
const VICTIM_OFFSET := Vector2(30.0, 0.0)
const BASIC_DAMAGE := 50
const WIND_RUN_ROLL := 0.1
const WIND_RUN_DURATION := 300
const SOURCED_HIT := 50
const SEED_SCAN_LIMIT := 4096


class MagicArmBus:
	extends BattleItemEffects
	var legacy := false

	func deal_damage_magic_sourceless(
		target_id: int, source_team: int, amount: int, school: String = "magic"
	) -> int:
		if not legacy:
			return super.deal_damage_magic_sourceless(target_id, source_team, amount, school)
		# Pre-9r body: the unit arm was delegated to `deal_damage`, which
		# delivered the sourceless neutral hit with the `"normal"` type default.
		var tgt: Object = world.get_unit(target_id)
		if tgt == null:
			return 0
		world._deliver_hit(-1, source_team, tgt, amount, "neutral", dealer_pos)
		return amount


class MagicArmWorld:
	extends World
	var legacy_arm := false
	var legacy_gate := false

	func _battle_item_effects(source_hero: HeroState) -> BattleItemEffects:
		var bus := MagicArmBus.new()
		bus.world = self
		bus.legacy = legacy_arm
		bus.dealer_id = source_hero.id
		bus.dealer_team = source_hero.team
		bus.dealer_pos = source_hero.position
		return bus

	func _hero_denies_hit(defender: HeroState, school: String, damage_type: String) -> bool:
		if not legacy_gate:
			return super._hero_denies_hit(defender, school, damage_type)
		# Pre-9r body: the windrun gate read the school only.
		if defender.shadow_realm_timer > 0:
			return true
		if damage_type == "projectile" and school != "magic" and defender.wind_wall_timer > 0:
			return true
		if defender.windrun_timer > 0 and school != "magic":
			var roll := (
				float(windrun_roll_override.call())
				if windrun_roll_override.is_valid()
				else windrun_rng.randf()
			)
			if roll < 0.75:
				return true
		return defender.items.is_veiled()


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the magic arm unit fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the magic arm unit fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_windrun_control(check)
	_sourced_credit(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		is_equal_approx(float(TROLL.armor), float(stats.get("troll_armor", -1.0))),
		"the troll armour is the fixture value"
	)
	check.call(
		String(fixture.get("evasion_item", "")) == EVASION_ITEM,
		"the fixture evasion item is Monarch Wings"
	)
	check.call(
		String(fixture.get("armor_item", "")) == ARMOR_ITEM,
		"the fixture armour item is Steel Aegis"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	var calls := int(shape.get("unit_arm_calls_with_magic_type", 0))
	check.call(calls >= 5, "the source magic-type arm call sites are counted")
	check.call(
		int(shape.get("calls_with_source_kwarg", -1)) == 0,
		"every magic-type arm call lands without a source keyword"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _arm_hit(data, false, check)
		var legacy := _arm_hit(data, true, check)
		if live.is_empty() or legacy.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			_matches(live, expected),
			"%s: the magic arm lands the source amount and credit (got %s)" % [label, live]
		)
		check.call(
			_matches(legacy, native_old),
			"%s: the pre-9r counterfactual replays (got %s)" % [label, legacy]
		)
		if bool(data.get("expect_divergence", false)):
			check.call(
				not _same_result(live, legacy),
				"%s: the magic arm no longer matches the pre-9r column" % label
			)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _arm_hit(data: Dictionary, legacy: bool, check: Callable) -> Dictionary:
	var world := MagicArmWorld.new()
	world.legacy_arm = legacy
	world.legacy_gate = legacy
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var arm := String(data.get("arm", "pierce_bash"))
	var victim: UnitState = null
	var primary: UnitState = null
	if arm == "chain":
		# The chain arm iterates `all_units` around the main target, so the
		# victim must be a nearby enemy — not the main target itself.
		primary = world.spawn_unit(TROLL, World.RED, 1)
		if primary != null:
			primary.position = POS
	if String(data.get("victim_kind", "minion")) == "hero":
		victim = world.spawn_hero(World.VEX, World.RED, POS + VICTIM_OFFSET)
		if victim != null and float(data.get("hero_armor", 0)) > 0.0:
			victim.items.add(ARMOR_ITEM)
		if victim != null and float(data.get("hero_evasion", 0.0)) > 0.0:
			victim.items.add(EVASION_ITEM)
		if victim != null and bool(data.get("hero_windrun", false)):
			victim.windrun_timer = WIND_RUN_DURATION
	else:
		victim = world.spawn_unit(TROLL, World.RED, 1)
		if victim != null:
			victim.position = POS + VICTIM_OFFSET
	if hero == null or victim == null or (primary == null and arm == "chain"):
		check.call(
			false,
			(
				"%s: the magic arm world spawns (hero=%s victim=%s primary=%s)"
				% [String(data.get("name", "?")), hero != null, victim != null, primary != null]
			)
		)
		return {}
	var item_id := String(data.get("item", ""))
	if not hero.items.add(item_id):
		check.call(false, "the arm item %s is addable" % item_id)
		return {}
	var entry: Dictionary = hero.items.item(item_id)
	var chance := _arm_chance(entry, arm)
	var evasion := float(data.get("hero_evasion", 0.0))
	if bool(data.get("hero_windrun", false)):
		world.windrun_roll_override = func() -> float: return WIND_RUN_ROLL
	var hp_before: float = victim.hp
	var credit_before: int = hero.damage_dealt
	world._item_rng.seed = (
		_seed_for(chance, evasion) if evasion > 0.0 else Prior.new()._seed_below(chance)
	)
	var target_id := int(primary.id) if primary != null and arm == "chain" else int(victim.id)
	hero.items.on_basic_attack_hit(
		target_id, BASIC_DAMAGE, [], world._item_rng, world._battle_item_effects(hero)
	)
	var after: UnitState = world.get_unit(victim.id) as UnitState
	if after == null:
		check.call(false, "%s: the victim stays registered" % String(data.get("name", "?")))
		return {}
	return {
		"hp_loss": int(hp_before - after.hp),
		"credited_total": int(hero.damage_dealt - credit_before),
	}


func _arm_chance(entry: Dictionary, arm: String) -> float:
	if arm == "chain":
		var chain: Dictionary = entry.get("on_attack", {})
		return float(chain.get("chance", 0.0))
	var bash: Dictionary = entry.get("bash", {})
	return float(bash.get("chance", 0.0))


func _seed_for(first: float, second: float) -> int:
	# Deterministic two-draw control: the first `randf()` fires the arm proc and
	# the second one satisfies the victim reaction roll of the legacy column.
	for seed_value in range(SEED_SCAN_LIMIT):
		var probe := RandomNumberGenerator.new()
		probe.seed = seed_value
		if probe.randf() < first and probe.randf() < second:
			return seed_value
	return 0


func _windrun_control(check: Callable) -> void:
	# The gate fix must keep the 75% miss for real physical hits and keep magic
	# SCHOOL hits landing, exactly like `_is_physical_hit`.
	var world := World.new()
	world.setup_arena()
	var attacker: HeroState = world.blue_hero()
	var defender: UnitState = world.spawn_hero(World.VEX, World.RED, POS)
	if attacker == null or defender == null:
		check.call(false, "the windrun control defender spawns")
		return
	defender.windrun_timer = WIND_RUN_DURATION
	world.windrun_roll_override = func() -> float: return WIND_RUN_ROLL
	var hp_before: float = defender.hp
	var landed: bool = world._deliver_hit(
		attacker.id, attacker.team, defender, 80, "physical", attacker.position
	)
	check.call(not landed, "a normal hit still rolls Windrun")
	check.call(defender.hp == hp_before, "the Windrun roll still blanks the hit")
	var magic_landed: bool = world._deliver_hit(
		attacker.id, attacker.team, defender, 80, "magic", attacker.position
	)
	check.call(magic_landed, "a magic-school hit bypasses Windrun")


func _sourced_credit(check: Callable) -> void:
	# The hero's own basic attack passes `source=self`, so a minion hit keeps
	# crediting the post-armour amount — that path must not change.
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var minion: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if hero == null or minion == null:
		check.call(false, "the sourced control minion spawns")
		return
	var expected := DamageRules.minion_amount(minion, SOURCED_HIT, "physical")
	var hp_before: float = minion.hp
	var credit_before: int = hero.damage_dealt
	var landed: bool = world._deliver_hit(
		hero.id, hero.team, minion, SOURCED_HIT, "physical", hero.position
	)
	check.call(landed, "the sourced control hit lands")
	check.call(
		int(hp_before - minion.hp) == expected, "a sourced hit is still cut by the minion armour"
	)
	check.call(
		int(hero.damage_dealt - credit_before) == expected,
		"a sourced hit still credits the dealing hero"
	)


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	# The fixture also records the source random draws; the native replay owns
	# its own RNG stream, so only the delivered amounts are compared.
	for key in ["hp_loss", "credited_total"]:
		if int(actual.get(key, -1)) != int(expected.get(key, -1)):
			return false
	return true


func _same_result(left: Dictionary, right: Dictionary) -> bool:
	return _matches(left, right)
