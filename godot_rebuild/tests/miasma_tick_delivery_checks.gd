extends RefCounted
## 9aa: the Miasma tick is a sourceless `take_damage(damage, team, "magic")`.
##
## `hero_items.py::_tick_miasma` (`:209-234`) lands the poison with
## `tgt.take_damage(m["damage"], team, "magic")` - three positional arguments
## and no `source=` - so `resolve_damage_school('magic', None, None, ...)`
## returns `None` (`_entity.py:106-130`) and the victim takes the tick with NO
## school mitigation: tower armour and magic resist, minion `magic_resist` and
## boss magic resist never cut it. The non-fire branches still run (hero armour,
## the passive block roll, the Soul Rend amp, the Corroder shred bonus, the
## veil gate), but nothing is credited, `notify_damage_taken(source=None)` never
## reflects through Razor Carapace, and a lethal tick leaves `killed_by` unset.
##
## The native bus passed the live owner as source plus `school="magic"`, which
## credited the owner, cut magic resist everywhere, reflected through the
## victim's thornmail and attributed kills. This suite replays the sealed
## `miasma_tick_delivery_source.json` fixture - both columns executed from the
## real `Hero.take_damage` / `Minion.take_damage` / `Tower.take_damage` -
## through production `items.apply_miasma` + `items.tick_miasma` (the hero and
## minion rows) and through the production bus branch
## `battle_item_effects.deal_damage_from` for the structure row, because
## `world._hero_enemy_list()` still carries units only (pre-existing gap, out of
## this slice's scope).

const World = preload("res://scripts/match/prototype_battle.gd")
const Siege = preload("res://scripts/combat/siege_battle.gd")
const Bus = preload("res://scripts/match/battle_item_effects.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const TROLL = preload("res://data/minions/troll.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const FIXTURE := "res://tests/fixtures/miasma_tick_delivery_source.json"
const ARMOR_ITEM := "steel_aegis"
const BLOCK_ITEM := "scarlet_bulwark"
const REFLECT_ITEM := "razor_carapace"
const LIVE_BOSS := "gornak"
const POS := Vector2(600.0, 500.0)
const GAP := 60.0
const FAR := Vector2(400.0, 0.0)
# The tracker the fixture's 30-damage tick comes from: 3% of 1000 max hp, cap 60.
const PAYLOAD := 30
const TRACKER_MAX_HP := 1000
const TRACKER_DATA := {"max_hp_pct_per_tick": 0.03, "cap_damage": 60, "duration": 180, "tick": 1}
const TICK_RESET := 30


class RollSpy:
	extends RefCounted
	var calls := 0
	var value := 0.5

	func roll() -> float:
		calls += 1
		return value


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the miasma tick fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "the miasma tick fixture parses")
	if not parsed is Dictionary:
		return
	var fixture: Dictionary = parsed
	_shape(fixture, check)
	var stats: Dictionary = fixture.get("live_stats", {})
	_live_stats(stats, check)
	_replay(fixture.get("cases", []), check)
	_controls(check)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("tick_shape", {})
	check.call(
		(
			int(shape.get("take_damage_calls", -1)) == 2
			and bool(shape.get("primary_three_positional_args", false))
			and bool(shape.get("third_arg_is_magic", false))
			and bool(shape.get("damage_is_tracker", false))
			and bool(shape.get("team_is_source_team", false))
			and bool(shape.get("no_source_keyword", false))
			and bool(shape.get("no_school_keyword", false))
			and bool(shape.get("fallback_two_positional", false))
		),
		"the source miasma tick is a sourceless three-positional magic call"
	)
	check.call(
		(
			bool(shape.get("tick_reset_is_30", false))
			and bool(shape.get("drains_timer_and_tick_cd", false))
			and bool(shape.get("expires_dead_or_spent", false))
			and bool(shape.get("keep_alive_guard", false))
			and bool(shape.get("team_from_stored_source", false))
		),
		"the source keeps the hardcoded 30-tick reset and the expiry rules"
	)
	var hero_shape: Dictionary = fixture.get("hero_shape", {})
	check.call(
		(
			int(hero_shape.get("non_fire_guard_count", -1)) == 0
			and bool(hero_shape.get("armor_keys_on_damage_type", false))
			and bool(hero_shape.get("block_inside_non_fire", false))
		),
		"the hero ladder keeps the armour and block branches outside the fire guard"
	)
	var resolution: Dictionary = fixture.get("live_stats", {}).get("school_resolution", {})
	var unresolved := true
	for key in resolution.keys():
		if resolution[key] != null:
			unresolved = false
	check.call(unresolved, "the sourceless tick resolves no school for any victim kind")


func _live_stats(stats: Dictionary, check: Callable) -> void:
	check.call(
		int(stats.get("payload", -1)) == PAYLOAD, "the fixture payload is the 30-damage tick"
	)
	var world := World.new()
	world.setup_arena()
	var hero: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS)
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if hero == null or troll == null:
		check.call(false, "the fixture control units spawn")
		return
	check.call(hero.items.add(ARMOR_ITEM), "the fixture armour item equips")
	check.call(
		int(hero.items.get_armor()) == int(stats.get("armor", -1)),
		"the fixture armour value is the live catalog value"
	)
	check.call(
		(
			int(troll.definition.armor) == int(stats.get("troll_armor", -1))
			and is_equal_approx(
				float(troll.definition.magic_resist), float(stats.get("troll_magic_resist", -1.0))
			)
		),
		"the fixture minion mitigation stats are the live catalog values"
	)
	# Control for the unresolved school: the SAME payload sent with the magic
	# school the pre-9aa bridge used is cut by the troll magic_resist.
	var schooled := World.new()
	schooled.setup_arena()
	var victim: UnitState = schooled.spawn_unit(TROLL, World.RED, 1)
	check.call(victim != null, "the school control victim spawns")
	if victim == null:
		return
	victim.position = POS
	var hp_before: float = victim.hp
	schooled._deliver_hit(-1, World.BLUE, victim, PAYLOAD, "magic", POS, "magic")
	check.call(
		int(hp_before - victim.hp) < PAYLOAD,
		"the magic school would cut the minion tick (%d)" % int(hp_before - victim.hp)
	)
	check.call(schooled.get_unit(victim.id) == victim, "the fixture world resolves victims by id")


func _replay(rows: Array, check: Callable) -> void:
	var seen := 0
	for row in rows:
		var data: Dictionary = row
		var label := String(data.get("name", ""))
		var expected: Dictionary = data.get("expected", {})
		var old: Dictionary = data.get("native_old", {})
		seen += 1
		match label:
			"miasma_tick_on_troll", "miasma_tick_on_shredded_troll":
				_troll_row(label, data, expected, old, check)
			"miasma_tick_on_tower":
				_tower_row(label, expected, old, check)
			_:
				_hero_row(label, data, expected, old, check)
	check.call(seen >= 7, "every fixture row replays through the poison tick")


func _tick(owner: HeroState, victim: UnitState, world: World) -> void:
	# One production poison tick: the item arms the tracker, the battle loop
	# runs the countdown and the bus lands the hit.
	owner.items.apply_miasma(victim.id, true, TRACKER_MAX_HP, TRACKER_DATA)
	owner.items.tick_miasma(1, world._hero_enemy_list(), world._battle_item_effects(owner))


func _diverges(
	label: String, expected: Dictionary, old: Dictionary, loss: int, check: Callable
) -> void:
	if int(old.get("hp_loss", -2)) != int(expected.get("hp_loss", -1)):
		check.call(
			loss != int(old.get("hp_loss", -2)), "%s: the pre-9aa column is divergent" % label
		)
	else:
		check.call(
			loss == int(old.get("hp_loss", -2)), "%s: the control row keeps both columns" % label
		)


func _hero_row(
	label: String, data: Dictionary, expected: Dictionary, old: Dictionary, check: Callable
) -> void:
	var case: Dictionary = data.get("case", {})
	var world := World.new()
	world.setup_arena()
	var victim: HeroState = world.spawn_hero(World.VEX, World.RED, POS)
	if victim == null:
		check.call(false, "%s: the victim spawns" % label)
		return
	var owner: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS + FAR)
	if owner == null:
		check.call(false, "%s: the poison owner spawns" % label)
		return
	var spy := RollSpy.new()
	world.block_roll_override = Callable(spy, "roll")
	_arm(victim, case, check, label)
	check.call(
		int(victim.items.get_armor()) == int(case.get("armor", 0)),
		"%s: the live victim armour is the fixture value" % label
	)
	var credit_before: int = owner.damage_dealt
	var kills_before: int = world.kills[World.BLUE]
	var hp_before: float = victim.hp
	_tick(owner, victim, world)
	var loss := int(hp_before - victim.hp)
	check.call(loss == int(expected.get("hp_loss", -1)), "%s: the tick lands %d" % [label, loss])
	_diverges(label, expected, old, loss, check)
	check.call(
		(
			owner.damage_dealt == credit_before
			and world.kills[World.BLUE] == kills_before
			and int(expected.get("credited_total", -1)) == 0
		),
		"%s: a sourceless tick credits nobody" % label
	)
	var draws := int(expected.get("random_draws", -1))
	check.call(spy.calls == draws, "%s: the tick consumes %d block roll(s)" % [label, draws])
	check.call(
		int(owner.items.miasma.get(victim.id, {}).get("tick_cd", -1)) == TICK_RESET,
		"%s: the tracker resets the countdown to the source 30" % label
	)


func _arm(victim: HeroState, case: Dictionary, check: Callable, label: String) -> void:
	# The block row carries the armour stat of the block item itself
	# (`scarlet_bulwark` has armour 6), so only the armour-only row equips the
	# Aegis; the live total is asserted against the fixture afterwards.
	if int(case.get("armor", 0)) > 0 and not bool(case.get("armor_from_block_item", false)):
		check.call(victim.items.add(ARMOR_ITEM), "%s: the armour item equips" % label)
	if case.get("block") != null:
		check.call(victim.items.add(BLOCK_ITEM), "%s: the block item equips" % label)
	if bool(case.get("veil", false)):
		victim.items.veil_timer = 30
	victim.hp = victim.max_hp


func _troll_row(
	label: String, data: Dictionary, expected: Dictionary, old: Dictionary, check: Callable
) -> void:
	var case: Dictionary = data.get("case", {})
	var world := World.new()
	world.setup_arena()
	var troll: UnitState = world.spawn_unit(TROLL, World.RED, 1)
	if troll == null:
		check.call(false, "%s: the minion victim spawns" % label)
		return
	troll.position = POS
	if float(case.get("shred", 0.0)) > 0.0:
		troll.armor_shred_amount = float(case["shred"])
	var owner: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS + Vector2(GAP, 0.0))
	if owner == null:
		check.call(false, "%s: the poison owner spawns" % label)
		return
	var credit_before: int = owner.damage_dealt
	var hp_before: float = troll.hp
	_tick(owner, troll, world)
	var loss := int(hp_before - troll.hp)
	check.call(loss == int(expected.get("hp_loss", -1)), "%s: the tick lands %d" % [label, loss])
	_diverges(label, expected, old, loss, check)
	check.call(loss >= PAYLOAD, "%s: no school means no magic-resist cut" % label)
	check.call(owner.damage_dealt == credit_before, "%s: the minion tick credits nobody" % label)


func _tower_row(label: String, expected: Dictionary, old: Dictionary, check: Callable) -> void:
	# The tracker list carries units only, so the structure row drives the
	# production bus branch (`deal_damage_from`) directly with the same tracker
	# payload the source tick delivers.
	var world := Siege.new()
	world.setup_arena()
	var tower: StructureState = world.spawn_structure(ARCHER, World.RED, POS)
	if tower == null:
		check.call(false, "%s: the tower victim spawns" % label)
		return
	tower.shield = 0.0
	tower.free_shield_active = false
	tower.shield_active = false
	var owner: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS + Vector2(GAP, 0.0))
	if owner == null:
		check.call(false, "%s: the poison owner spawns" % label)
		return
	var bus := Bus.new()
	bus.world = world
	bus.dealer_id = owner.id
	bus.dealer_team = owner.team
	bus.dealer_pos = owner.position
	var credit_before: int = owner.damage_dealt
	var hp_before: float = tower.hp
	var landed: int = bus.deal_damage_from(
		owner.id, owner.team, owner.position, tower.id, PAYLOAD, "neutral", "magic"
	)
	var loss := int(hp_before - tower.hp)
	check.call(
		landed == PAYLOAD and loss == int(expected.get("hp_loss", -1)),
		"%s: the bus lands the sourceless tick (%d, landed %d)" % [label, loss, landed]
	)
	_diverges(label, expected, old, loss, check)
	check.call(
		(
			owner.damage_dealt == credit_before
			and world.kills[World.BLUE] == 0
			and int(old.get("credited_total", -1)) > 0
		),
		"%s: the sourceless tick never credits the pre-9aa amount" % label
	)
	# Control: the same payload sourced through `_deliver_hit` still credits.
	var sourced: bool = world._deliver_hit(
		owner.id, owner.team, tower, PAYLOAD, "neutral", owner.position, "magic"
	)
	check.call(
		(
			landed == PAYLOAD
			and sourced
			and owner.damage_dealt > credit_before
			and int(expected.get("credited_total", -1)) == 0
		),
		"%s: only the sourced bridge credits the owner" % label
	)


func _controls(check: Callable) -> void:
	# A lethal tick leaves no killer id: the source `take_damage` carries no
	# source, and `_entity.py` only writes `_killed_by` when one is present.
	var world := World.new()
	world.setup_arena()
	var doomed: HeroState = world.spawn_hero(World.VEX, World.RED, POS)
	var owner: HeroState = world.spawn_hero(World.VEX, World.BLUE, POS + FAR)
	if doomed == null or owner == null:
		check.call(false, "the lethal control heroes spawn")
		return
	doomed.hp = 1.0
	_tick(owner, doomed, world)
	check.call(
		not doomed.alive and doomed.killed_by == -1, "a lethal sourceless tick leaves no killer id"
	)
	# An armed Razor Carapace never reflects the sourceless tick.
	var reflect_world := World.new()
	reflect_world.setup_arena()
	var defender: HeroState = reflect_world.spawn_hero(World.VEX, World.RED, POS)
	var poisoner: HeroState = reflect_world.spawn_hero(World.VEX, World.BLUE, POS + FAR)
	if defender == null or poisoner == null:
		check.call(false, "the reflect control heroes spawn")
		return
	check.call(defender.items.add(REFLECT_ITEM), "the reflect control equips Razor Carapace")
	defender.items.thorn_timer = 100
	var poisoner_before: float = poisoner.hp
	_tick(poisoner, defender, reflect_world)
	check.call(
		(
			is_equal_approx(poisoner.hp, poisoner_before)
			and defender.hp < defender.max_hp
			and reflect_world.kills[World.RED] == 0
		),
		"the sourceless tick never reflects back to the poison owner"
	)
	# Control: the same bus with the owner as `source_id` still credits the
	# owner - that pre-9aa bridge is the only thing this slice changed.
	var credit_world := World.new()
	credit_world.setup_arena()
	var troll: UnitState = credit_world.spawn_unit(TROLL, World.RED, 1)
	var burner: HeroState = credit_world.spawn_hero(World.VEX, World.BLUE, POS + Vector2(GAP, 0.0))
	if troll == null or burner == null:
		check.call(false, "the credit control spawns")
		return
	troll.position = POS
	credit_world._deliver_hit(burner.id, burner.team, troll, PAYLOAD, "neutral", POS, "magic")
	check.call(
		burner.damage_dealt == PAYLOAD,
		"only the sourced bridge credits the owner (%d)" % burner.damage_dealt
	)
	# The boss keeps the native replay handle (9b/9d) while landing the
	# sourceless amount: its magic resist no longer cuts the tick.
	var boss_world := World.new()
	boss_world.setup_arena()
	var boss: BossState = boss_world._spawn_boss(LIVE_BOSS)
	var boss_poisoner: HeroState = boss_world.spawn_hero(World.VEX, World.BLUE, POS)
	if boss == null or boss_poisoner == null:
		check.call(false, "the boss control spawns")
		return
	check.call(float(boss.magic_resist) > 0.0, "the fixture boss carries a magic resist to skip")
	var boss_before: float = boss.hp
	_tick(boss_poisoner, boss, boss_world)
	var live_loss := int(roundf(boss_before - boss.hp))
	check.call(
		boss.last_hit_is_miasma_tick and boss.last_hit_source_id == boss_poisoner.id,
		"the boss tick keeps the 9b replay handle"
	)
	var neutral := _boss_delivery(boss_world, boss_poisoner, boss, "neutral")
	var magic := _boss_delivery(boss_world, boss_poisoner, boss, "magic")
	check.call(
		live_loss == neutral,
		"the boss tick lands the sourceless amount (%d vs %d)" % [live_loss, neutral]
	)
	check.call(
		magic < neutral, "the magic school would cut the boss tick (%d vs %d)" % [magic, neutral]
	)


func _boss_delivery(world: World, poisoner: HeroState, boss: BossState, school: String) -> int:
	# Same boss and same seated state: only the school column differs.
	var before: float = boss.hp
	world._deliver_hit(
		poisoner.id, poisoner.team, boss, PAYLOAD, school, poisoner.position, "magic"
	)
	var loss := int(roundf(before - boss.hp))
	boss.hp = before
	return loss
