extends RefCounted
## 9t: the Bristleback reflect must reach its attacker with the source call
## shape — `_src.take_damage(max(1, int(damage * 0.25)), self.team, source=None)`
## (`_entity.py:4697-4711`), two positional arguments plus an explicit
## `source=None`, so the attacker runs with `damage_type="normal"` and
## `school=None`. The production `_deliver_hit` reflect sent the declared
## physical school, so an armoured attacker (troll, armor 2) ate an armour cut
## the source never applies (31 of the 35 reflected) and the delivered hit
## carried a school `_is_physical_hit` (`_entity.py:92-103`) never sees there.
##
## The live column drives the real production `_deliver_hit` with an active
## Bristleback; the counterfactual replays the pre-9t delivery
## (`_deliver_hit(-1, team, atk, payload, "physical", position)`) with the
## payload recomputed from the fixture keep/reflect constants.

const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const TROLL = preload("res://data/minions/troll.tres")
const UNDEAD = preload("res://data/minions/undead.tres")
const FIXTURE := "res://tests/fixtures/hero_bristleback_reflect_source.json"
const ARMOR_ITEM := "steel_aegis"
const POS := Vector2(400.0, 380.0)
const ATTACKER_OFFSET := Vector2(20.0, 0.0)
const BRISTLEBACK_ACTIVE := 300
const SOURCED_HIT := 50


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the bristleback reflect fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the bristleback reflect fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_shape(fixture, check)
	_replay(fixture, check)
	_inactive_control(fixture, check)
	_sourced_credit(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		is_equal_approx(float(TROLL.armor), float(stats.get("troll_armor", -1.0))),
		"the troll armour is the fixture value"
	)
	check.call(
		is_equal_approx(float(TROLL.magic_resist), float(stats.get("troll_magic_resist", -1.0))),
		"the troll magic resist is the fixture value"
	)
	check.call(
		is_equal_approx(float(UNDEAD.magic_resist), float(stats.get("undead_magic_resist", -1.0))),
		"the undead magic resist is the fixture value"
	)
	check.call(
		is_equal_approx(float(fixture.get("reflect_pct", -1.0)), 0.25),
		"the fixture pins the 25% reflect"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			int(shape.get("reflect_calls", 0)) >= 1
			and (
				int(shape.get("reflect_calls_with_source_kwarg_is_none", 0))
				== int(shape.get("reflect_calls", -1))
			)
		),
		"every source reflect call passes source=None"
	)
	check.call(
		int(shape.get("reflect_calls_with_school_kwarg", -1)) == 0,
		"the source reflect call passes no school"
	)


func _replay(fixture: Dictionary, check: Callable) -> void:
	var rows: Array = fixture.get("cases", [])
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _live_reflect(fixture, data, check)
		var legacy := _legacy_reflect(fixture, data, check)
		if live.is_empty() or legacy.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			_matches(live, expected),
			"%s: the reflect lands the source amount and credit (got %s)" % [label, live]
		)
		check.call(
			_matches(legacy, native_old),
			"%s: the pre-9t counterfactual replays (got %s)" % [label, legacy]
		)
		if bool(data.get("expect_divergence", false)):
			check.call(
				int(live.get("attacker_hp_loss", -1)) != int(legacy.get("attacker_hp_loss", -2)),
				"%s: the reflect no longer matches the pre-9t column" % label
			)
	check.call(replayed >= 4, "at least four fixture rows replay through the production path")


func _live_reflect(fixture: Dictionary, data: Dictionary, check: Callable) -> Dictionary:
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var attacker: UnitState = _spawn_attacker(world, data)
	if hero == null or attacker == null:
		check.call(
			false,
			(
				"%s: the bristleback world spawns (hero=%s attacker=%s)"
				% [String(data.get("name", "?")), hero != null, attacker != null]
			)
		)
		return {}
	hero.bristleback_timer = BRISTLEBACK_ACTIVE
	var attacker_hp_before: float = attacker.hp
	var hero_hp_before: float = hero.hp
	var credit_before: int = hero.damage_dealt
	world._deliver_hit(
		attacker.id,
		attacker.team,
		hero,
		int(fixture.get("incoming_damage", 0)),
		String(data.get("incoming_school", "physical")),
		attacker.position
	)
	var attacker_after: UnitState = world.get_unit(attacker.id) as UnitState
	if attacker_after == null:
		check.call(false, "%s: the attacker stays registered" % String(data.get("name", "?")))
		return {}
	return {
		"attacker_hp_loss": int(attacker_hp_before - attacker_after.hp),
		"defender_hp_loss": int(hero_hp_before - hero.hp),
		"credited_total": int(hero.damage_dealt - credit_before),
	}


func _legacy_reflect(fixture: Dictionary, data: Dictionary, check: Callable) -> Dictionary:
	# Pre-9t delivery: the bus handed the payload to the attacker with the
	# declared physical school and no source.
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var attacker: UnitState = _spawn_attacker(world, data)
	if hero == null or attacker == null:
		check.call(
			false,
			(
				"%s: the legacy world spawns (hero=%s attacker=%s)"
				% [String(data.get("name", "?")), hero != null, attacker != null]
			)
		)
		return {}
	var payload := _payload(fixture, data)
	var attacker_hp_before: float = attacker.hp
	world._deliver_hit(-1, hero.team, attacker, payload, "physical", POS)
	var attacker_after: UnitState = world.get_unit(attacker.id) as UnitState
	if attacker_after == null:
		check.call(
			false, "%s: the legacy attacker stays registered" % String(data.get("name", "?"))
		)
		return {}
	return {
		"attacker_hp_loss": int(attacker_hp_before - attacker_after.hp),
		"defender_hp_loss": 0,
		"credited_total": 0,
	}


func _payload(fixture: Dictionary, data: Dictionary) -> int:
	var incoming := int(fixture.get("incoming_damage", 0))
	var keep := (
		float(fixture.get("keep_magic", 0.85))
		if String(data.get("incoming_school", "physical")) == "magic"
		else float(fixture.get("keep_physical", 0.70))
	)
	var landed := maxi(1, DamageRules.rounded_like_python(float(incoming) * keep))
	return maxi(1, int(float(landed) * float(fixture.get("reflect_pct", 0.25))))


func _inactive_control(fixture: Dictionary, check: Callable) -> void:
	# Without an active Bristleback the hero takes the incoming hit and nothing
	# is reflected.
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.blue_hero()
	var attacker: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if hero == null or attacker == null:
		check.call(false, "the inactive bristleback control spawns")
		return
	hero.bristleback_timer = 0
	var attacker_hp_before: float = attacker.hp
	world._deliver_hit(
		attacker.id,
		attacker.team,
		hero,
		int(fixture.get("incoming_damage", 0)),
		"physical",
		attacker.position
	)
	check.call(attacker.hp == attacker_hp_before, "an inactive Bristleback reflects nothing")


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


func _spawn_attacker(world: World, data: Dictionary) -> UnitState:
	var kind := String(data.get("attacker_kind", "troll"))
	if kind == "hero":
		var attacker: UnitState = world.spawn_hero(World.VEX, World.RED, POS + ATTACKER_OFFSET)
		if attacker != null and int(data.get("hero_armor", 0)) > 0:
			attacker.items.add(ARMOR_ITEM)
		return attacker
	var definition := UNDEAD if kind == "undead" else TROLL
	var minion: UnitState = world.spawn_unit(definition, World.RED, 1)
	if minion != null:
		minion.position = POS + ATTACKER_OFFSET
	return minion


func _matches(actual: Dictionary, expected: Dictionary) -> bool:
	# The pre-9t column is replayed through `_deliver_hit` directly, so it only
	# carries the reflected attacker loss; compare the keys the row defines.
	for key in expected.keys():
		if int(actual.get(key, -1)) != int(expected.get(key, -1)):
			return false
	return true
