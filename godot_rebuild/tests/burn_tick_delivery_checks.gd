extends RefCounted
## 9z: the burn tick is a fire hit through the victim's `take_damage` ladder.
##
## `_core.py::TowerDebuffMixin._tick_tower_debuffs` runs
## `self.take_damage(dmg, self.burn_team or self.team, "fire")` once per
## `TOWER_DEBUFF_BURN_TICK` (30) frames - three positional arguments, no
## `source=`, no `school=` - so the victim runs its WHOLE ladder: a veiled or
## shadow-realm hero takes nothing, the Soul Rend amp applies, the damage block
## section is skipped because the source nests it inside the non-fire branch
## (`_entity.py:4644-4675`), Bristleback keeps 30%, `notify_damage_taken` fires
## with `source=None`, and nobody is credited.
##
## The native `_tick_burn` used to subtract hp directly (with a hand-rolled
## shadow-realm zero), which skipped every one of those gates. This suite
## replays the sealed `burn_tick_delivery_source.json` fixture - both columns
## executed from the real `Hero.take_damage` / `Minion.take_damage` - through
## the production `world.apply_burn` plus `world._tick_burn`.

const World = preload("res://scripts/match/prototype_battle.gd")
const Siege = preload("res://scripts/combat/siege_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const TROLL = preload("res://data/minions/troll.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/burn_tick_delivery_source.json"
const BLOCK_ITEM := "scarlet_bulwark"
const POS := Vector2(600.0, 500.0)
const TEAM := World.BLUE


class DrawSpy:
	extends RefCounted
	var calls := 0
	var value := 0.1

	func roll() -> float:
		calls += 1
		return value


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the burn tick fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the burn tick fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_shape(fixture, check)
	var stats: Dictionary = fixture.get("live_stats", {})
	_live_stats(stats, check)
	_replay(fixture.get("cases", []), stats, check)
	_controls(stats, check)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("burn_shape", {})
	check.call(
		(
			int(shape.get("take_damage_calls", -1)) == 1
			and bool(shape.get("three_positional_args", false))
			and bool(shape.get("third_arg_is_fire", false))
			and bool(shape.get("team_is_burn_team_or_team", false))
			and bool(shape.get("no_source_keyword", false))
			and bool(shape.get("no_school_keyword", false))
		),
		"the source burn tick is a sourceless fire take_damage call"
	)
	check.call(
		(
			bool(shape.get("accum_drained_before", false))
			and bool(shape.get("guarded_by_alive", false))
		),
		"the source drains the accumulator before the alive-guarded call"
	)
	var hero_shape: Dictionary = fixture.get("hero_fire_shape", {})
	check.call(
		(
			bool(hero_shape.get("block_roll_inside_non_fire", false))
			and bool(hero_shape.get("keep_is_not_magic_gated", false))
		),
		"the source nests the block in the non-fire branch and keeps Bristleback outside"
	)


func _live_stats(stats: Dictionary, check: Callable) -> void:
	check.call(
		(
			int(World.BURN_TICK_INTERVAL) == int(stats.get("tick_frames", -1))
			and is_equal_approx(World.BURN_TICKS_PER_SECOND, float(stats.get("dps", -1.0)))
		),
		"the native burn clock matches the source constants"
	)
	var world := World.new()
	world.setup_arena()
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	check.call(troll != null, "the burn control victim spawns")
	if troll == null:
		return
	check.call(
		(
			int(troll.definition.armor) == int(stats.get("troll_armor", -1))
			and is_equal_approx(
				float(troll.definition.magic_resist), float(stats.get("troll_magic_resist", -1.0))
			)
		),
		"the fixture mitigation stats are the live catalog values"
	)


func _replay(rows: Array, stats: Dictionary, check: Callable) -> void:
	var seen := 0
	for row in rows:
		var data: Dictionary = row
		var label := String(data.get("name", ""))
		var expected: Dictionary = data.get("expected", {})
		var old: Dictionary = data.get("native_old", {})
		seen += 1
		if label == "burn_tick_on_troll":
			_troll_row(label, expected, old, stats, check)
		else:
			_hero_row(label, data, expected, old, stats, check)
	check.call(seen >= 6, "every fixture row replays through the burn branch")


func _burn(world: World, target: UnitState, stats: Dictionary) -> void:
	world.apply_burn(
		target.id, float(stats.get("dps", 60.0)), int(stats.get("tick_frames", 30)), TEAM
	)
	for _tick in range(int(stats.get("tick_frames", 30))):
		world._tick_burn(target)


func _troll_row(
	label: String, expected: Dictionary, old: Dictionary, stats: Dictionary, check: Callable
) -> void:
	var world := Siege.new()
	world.setup_arena()
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if troll == null:
		check.call(false, "%s: the victim spawns" % label)
		return
	troll.position = POS
	var hp_before: float = troll.hp
	var kills_before: int = world.kills[TEAM]
	_burn(world, troll, stats)
	var loss := int(hp_before - troll.hp)
	check.call(
		loss == int(expected.get("hp_loss", -1)),
		"%s: fire lands the source amount (%d)" % [label, loss]
	)
	check.call(
		loss == int(old.get("hp_loss", -2)) and world.kills[TEAM] == kills_before,
		"%s: the minion control is unchanged and credits nobody" % label
	)


func _hero_row(
	label: String,
	data: Dictionary,
	expected: Dictionary,
	old: Dictionary,
	stats: Dictionary,
	check: Callable
) -> void:
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.spawn_hero(World.VEX, World.RED, POS)
	if hero == null:
		check.call(false, "%s: the hero victim spawns" % label)
		return
	var burner: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS + Vector2(400.0, 0.0))
	if burner == null:
		check.call(false, "%s: the observer spawns" % label)
		return
	var spy := DrawSpy.new()
	world.block_roll_override = Callable(spy, "roll")
	var case: Dictionary = data.get("case", {})
	_arm(hero, case, check, label)
	var credit_before: int = burner.damage_dealt
	var kills_before: int = world.kills[TEAM]
	var hp_before: float = hero.hp
	_burn(world, hero, stats)
	var loss := int(hp_before - hero.hp)
	check.call(
		loss == int(expected.get("hp_loss", -1)),
		"%s: the fire tick lands the source amount (%d)" % [label, loss]
	)
	check.call(
		burner.damage_dealt == credit_before and world.kills[TEAM] == kills_before,
		"%s: a sourceless tick credits nobody" % label
	)
	if int(old.get("hp_loss", -2)) != int(expected.get("hp_loss", -1)):
		check.call(
			loss != int(old.get("hp_loss", -2)), "%s: the raw column is now divergent" % label
		)
	else:
		check.call(
			loss == int(old.get("hp_loss", -2)), "%s: the control row keeps the raw column" % label
		)
	if case.get("block") != null:
		check.call(spy.calls == 0, "%s: fire never rolls the passive block" % label)
	elif bool(case.get("veil", false)) or bool(case.get("shadow_realm", false)):
		check.call(spy.calls == 0, "%s: an immune hero consumes no roll at all" % label)


func _arm(hero: HeroState, case: Dictionary, check: Callable, label: String) -> void:
	if case.get("block") != null:
		check.call(hero.items.add(BLOCK_ITEM), "%s: the block item equips" % label)
	if int(case.get("dmg_amp_timer", 0)) > 0:
		hero.dmg_amp_timer = int(case["dmg_amp_timer"])
		hero.dmg_amp_amount = float(case.get("dmg_amp_amount", 0.0))
	if bool(case.get("bristleback", false)):
		hero.bristleback_timer = 30
	if bool(case.get("veil", false)):
		hero.items.veil_timer = 30
	if bool(case.get("shadow_realm", false)):
		hero.shadow_realm_timer = 30
	hero.hp = hero.max_hp


func _controls(stats: Dictionary, check: Callable) -> void:
	# Structures never burn, and the pre-9z numbers still describe the minion
	# ladder (fire skips armour, magic_resist and the Corroder bonus, while a
	# school-free normal hit keeps the bonus).
	var siege := Siege.new()
	siege.setup_arena()
	var tower: StructureState = siege.spawn_structure(ARCHER, World.RED, POS)
	check.call(tower != null, "the structure control spawns")
	if tower != null:
		check.call(not siege.apply_burn(tower.id, 8.0, 120, TEAM), "structures still cannot burn")
	var world := World.new()
	world.setup_arena()
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	check.call(troll != null, "the shred control victim spawns")
	if troll == null:
		return
	troll.position = POS
	troll.armor_shred_amount = 5.0
	var hp_before: float = troll.hp
	_burn(world, troll, stats)
	var fire_loss := int(hp_before - troll.hp)
	hp_before = troll.hp
	world._deliver_hit(-1, TEAM, troll, 30, "neutral", POS, "normal")
	var normal_loss := int(hp_before - troll.hp)
	check.call(fire_loss == 30, "the fire tick skips the Corroder bonus (%d)" % fire_loss)
	check.call(
		normal_loss == 39, "a school-free normal hit keeps the Corroder bonus (%d)" % normal_loss
	)
	# A block item plus an armed roll proves the gate is the fire branch: the
	# same hero and the same spy consume a roll for a normal hit.
	var match_world := World.new()
	match_world.setup_arena()
	var hero: HeroState = match_world.spawn_hero(World.VEX, World.RED, POS)
	check.call(hero != null, "the block control hero spawns")
	if hero == null:
		return
	check.call(hero.items.add(BLOCK_ITEM), "the block control hero arms the item")
	var spy := DrawSpy.new()
	match_world.block_roll_override = Callable(spy, "roll")
	hp_before = hero.hp
	match_world._deliver_hit(-1, TEAM, hero, 30, "neutral", POS, "normal")
	check.call(spy.calls == 1, "a non-fire hit consumes the block roll")
	check.call(int(hp_before - hero.hp) < 30, "a non-fire hit is cut by the passive block")
