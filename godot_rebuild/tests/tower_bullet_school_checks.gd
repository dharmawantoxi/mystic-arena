extends RefCounted
## 9w: structure bullets land school-free on every victim.
##
## `_entity.py::Bullet._on_hit` delivers the impact as
## `target.take_damage(self.damage, self.team, damage_type='projectile')` - no
## `source=`, no `school=` - so `resolve_damage_school` returns `None` for every
## victim of a tower/nexus shot: minion armour and `magic_resist` never cut the
## bolt, a hero keeps its damage-type-driven armour, and the Wind Wall gate
## (`_school != 'magic'`) walls a mage bolt too. `credit_hero_damage(None, ...)`
## records nothing in either column.
##
## The pre-9w native delivery handed the shooter's declared school
## (`"magic" if shot.kind == "mage" else "physical"`) to the target, so troll
## armour 2 cut archer bolts (20 -> 18), troll `magic_resist` 0.05 cut mage
## bolts (17 -> 16), the cannon splash was armoured (25 -> 22) and the Wind Wall
## pre-check let a mage bolt through a live wall (17 -> 0).
##
## The replay drives the production `fire_projectile` + `_update_projectiles`
## chain; the counterfactual column is proven live through
## `DamageRules.minion_amount(..., declared)`, `DamageRules.item_aware_amount`
## and the pre-check rule (`_hero_blocks_projectile` with the declared school).

const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const MAGE = preload("res://data/structures/mage_level_2.tres")
const CANNON = preload("res://data/structures/cannon_level_2.tres")
const TROLL = preload("res://data/minions/troll.tres")
const FIXTURE := "res://tests/fixtures/tower_bullet_school_source.json"
const ARMOR_ITEM := "steel_aegis"
const TOWER_POS := Vector2(400.0, 380.0)
const MAIN_POS := Vector2(490.0, 380.0)
const SPLASH_POS := Vector2(505.0, 380.0)
const SPLASH_FRACTION := 0.6
const MAX_TICKS := 40
const SOURCED_HIT := 50


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the tower bullet school fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the tower bullet school fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_live_stats(fixture, check)
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_sourced_credit(check)


func _live_stats(fixture: Dictionary, check: Callable) -> void:
	var stats: Dictionary = fixture.get("live_stats", {})
	check.call(
		(
			int(ARCHER.damage) == int(stats.get("archer_damage", -1))
			and int(MAGE.damage) == int(stats.get("mage_damage", -1))
			and int(CANNON.damage) == int(stats.get("cannon_damage", -1))
		),
		"the tower damages are the fixture values"
	)
	check.call(
		(
			int(TROLL.armor) == int(stats.get("troll_armor", -1))
			and is_equal_approx(
				float(TROLL.magic_resist), float(stats.get("troll_magic_resist", -1.0))
			)
		),
		"the troll armour and magic resist are the fixture values"
	)
	check.call(
		(
			String(fixture.get("armor_item", "")) == ARMOR_ITEM
			and is_equal_approx(float(fixture.get("splash_fraction", -1.0)), SPLASH_FRACTION)
		),
		"the fixture armour item and splash fraction are live values"
	)


func _shape(fixture: Dictionary, check: Callable) -> void:
	# Source shape: two `take_damage` calls under `Bullet`, both two-positional,
	# the impact carrying `damage_type='projectile'` and neither carrying a
	# `source=`/`school=` kwarg.
	var shape: Dictionary = fixture.get("shape", {})
	check.call(
		(
			int(shape.get("bullet_take_damage_calls", -1)) == 2
			and int(shape.get("bullet_two_positional", -1)) == 2
		),
		"the source Bullet impact and splash are two-positional calls"
	)
	check.call(
		(
			bool(shape.get("kind_only_projectile_type", false))
			and bool(shape.get("bullet_no_source_kwarg", false))
			and bool(shape.get("bullet_no_school_kwarg", false))
		),
		"the source impact carries only the projectile damage type"
	)
	check.call(
		(
			bool(shape.get("early_out_types", false))
			and bool(shape.get("hero_context_requires_target", false))
		),
		"the resolver keeps the type early-out and the hero-context gate"
	)
	# Native side: one resolved school for every victim, delivered and gated.
	var world := World.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(ARCHER, World.BLUE, TOWER_POS)
	var minion: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	var hero: HeroState = world.spawn_hero(World.VEX, World.RED, TOWER_POS + Vector2(60, 0))
	if tower == null or minion == null or hero == null:
		check.call(false, "the shape probes spawn")
		return
	check.call(
		(
			world._projectile_school(minion, "physical") == "neutral"
			and world._projectile_school(hero, "magic") == "neutral"
		),
		"the resolved projectile school is neutral for minion and hero victims"
	)
	hero.wind_wall_timer = 180
	check.call(
		(
			world._hero_blocks_projectile(hero, "neutral")
			and not world._hero_blocks_projectile(hero, "magic")
		),
		"the wind wall gate reads the resolved school, not the declared one"
	)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		replayed += 1
		var expected: Dictionary = data.get("expected", {})
		var native_old: Dictionary = data.get("native_old", {})
		var live := _bullet_hit(data, check)
		if live.is_empty():
			continue
		var label := String(data["name"])
		check.call(
			int(live.get("hp_loss", -1)) == int(expected.get("hp_loss", -2)),
			"%s: the bolt lands the source amount (got %s)" % [label, live.get("hp_loss")]
		)
		check.call(
			int(live.get("payload", -1)) == int(data.get("payload", -2)),
			"%s: the shot payload is the source tower damage" % label
		)
		check.call(
			int(live.get("credited_total", -1)) == int(expected.get("credited_total", -2)),
			"%s: the sourceless bolt records no credit" % label
		)
		check.call(
			String(live.get("delivered_school", "?")) == "neutral",
			"%s: the impact is delivered school-free" % label
		)
		var legacy := _native_old_ladder(data, live)
		if legacy < 0:
			continue
		check.call(
			int(native_old.get("hp_loss", -2)) == legacy,
			"%s: the pre-9w declared school cuts the bolt (got %s)" % [label, legacy]
		)
		if bool(data.get("expect_divergence", false)):
			check.call(
				int(expected.get("hp_loss", -1)) != legacy,
				"%s: the bolt no longer matches the pre-9w column" % label
			)
		else:
			check.call(
				int(expected.get("hp_loss", -1)) == legacy,
				"%s: the control row is unchanged by the school fix" % label
			)
	check.call(replayed >= 6, "at least six fixture rows replay through the production path")


func _bullet_hit(data: Dictionary, check: Callable) -> Dictionary:
	var world := World.new()
	world.setup_arena()
	var definition = _tower_definition(String(data.get("shot", "archer")))
	var tower: StructureState = world.spawn_structure(definition, World.BLUE, TOWER_POS)
	if tower == null:
		check.call(false, "%s: the tower spawns" % String(data.get("name", "?")))
		return {}
	var splash := String(data.get("shot", "")) == "cannon"
	var victim: UnitState = null
	var main: UnitState = null
	if String(data.get("victim_kind", "minion")) == "hero":
		victim = world.spawn_hero(World.VEX, World.RED, MAIN_POS)
		if victim != null and int(data.get("hero_armor", 0)) > 0:
			victim.items.add(ARMOR_ITEM)
		if victim != null and bool(data.get("wind_wall", false)):
			victim.wind_wall_timer = 180
	else:
		if splash:
			# The splash arm hits a secondary victim next to the main target;
			# measure the secondary one, exactly like `Bullet._on_hit`.
			main = world.spawn_unit(TROLL, World.RED, 1)
			victim = world.spawn_unit(TROLL, World.RED, 1)
			if main != null:
				main.position = MAIN_POS
			if victim != null:
				victim.position = SPLASH_POS
		else:
			victim = world.spawn_unit(TROLL, World.RED, 1)
			main = victim
			if victim != null:
				victim.position = MAIN_POS
	if victim == null or main == null:
		check.call(false, "%s: the bullet victims spawn" % String(data.get("name", "?")))
		return {}
	if victim is HeroState and not _hero_inside_range(tower, victim):
		check.call(
			false, "%s: the hero victim is inside the tower reach" % String(data.get("name", "?"))
		)
		return {}
	var hp_before: float = victim.hp
	var blue: HeroState = world.blue_hero()
	var credit_before := int(blue.damage_dealt) if blue != null else 0
	if not world.fire_projectile(tower.id, main.id):
		check.call(false, "%s: the tower fires" % String(data.get("name", "?")))
		return {}
	var shot = world.projectiles[0]
	var payload := int(shot.damage)
	var delivered := "neutral"
	for _tick in range(MAX_TICKS):
		if not shot.active:
			break
		delivered = world._projectile_school(victim, "magic" if shot.kind == "mage" else "physical")
		world._update_projectiles(tower)
	var after: UnitState = world.get_unit(victim.id) as UnitState
	if after == null:
		check.call(false, "%s: the victim stays registered" % String(data.get("name", "?")))
		return {}
	if splash:
		payload = int(float(payload) * SPLASH_FRACTION)
	return {
		"hp_loss": int(hp_before - after.hp),
		"payload": payload,
		"credited_total": (int(blue.damage_dealt) - credit_before) if blue != null else 0,
		"delivered_school": delivered,
	}


func _tower_definition(shot: String):
	if shot == "mage":
		return MAGE
	if shot == "cannon":
		return CANNON
	return ARCHER


func _hero_inside_range(tower: StructureState, hero: UnitState) -> bool:
	return tower.position.distance_to(hero.position) <= tower.definition.attack_range_px


func _native_old_ladder(data: Dictionary, live: Dictionary) -> int:
	var declared := String(data.get("declared", "physical"))
	var payload := int(live.get("payload", 0))
	if String(data.get("victim_kind", "minion")) == "hero":
		# Pre-9w native heroes first ran `_hero_blocks_projectile` with the
		# declared school; only what got past it entered the ladder with that
		# school.
		if bool(data.get("wind_wall", false)) and declared != "magic":
			return 0
		var world := World.new()
		world.setup_arena()
		var victim: UnitState = world.spawn_hero(World.VEX, World.RED, MAIN_POS)
		if victim == null:
			return -1
		if int(data.get("hero_armor", 0)) > 0:
			victim.items.add(ARMOR_ITEM)
		return DamageRules.item_aware_amount(victim, payload, declared, "projectile")
	var probe := World.new()
	probe.setup_arena()
	var minion: UnitState = probe.spawn_unit(TROLL, World.RED, 1)
	if minion == null:
		return -1
	return DamageRules.minion_amount(minion, payload, declared)


func _sourced_credit(check: Callable) -> void:
	# A hero basic attack still passes `source=self` with the declared school,
	# so it keeps crediting the post-armour amount — that path must not change.
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
	world._deliver_hit(hero.id, hero.team, minion, SOURCED_HIT, "physical", hero.position)
	check.call(
		int(hp_before - minion.hp) == expected, "a sourced hit is still cut by the minion armour"
	)
	check.call(
		int(hero.damage_dealt - credit_before) == expected,
		"a sourced hit still credits the dealing hero"
	)
