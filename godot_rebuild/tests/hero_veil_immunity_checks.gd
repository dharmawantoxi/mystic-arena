extends RefCounted
## 9j: Tempest Veil must protect its owner. Source `Hero.take_damage`
## (`_entity.py:4589-4599`) returns on `items.is_veiled()` right after
## Shadow Realm / Windrun / Wind Wall and before the evasion block, school
## mitigation, `credit_hero_damage` and every reactive hook, so a veiled hero
## takes no damage from any source. `Hero.update` (`:3799`) folds the same flag
## into `_disabled`, so auto-cast is skipped while the veil holds (the AI path
## is not gated: `AIPlayer._control_heroes` calls the shared auto-cast itself).
##
## Before this layer the rebuild read `is_veiled()` only for the hero's own
## attack (`prototype_battle.hero_basic_attack`), so Tempest Veil muted the
## owner while leaving it fully damageable. This suite replays the sealed
## `test/fixtures/hero_veil_immunity_source.json` fixture through the
## production `_deliver_hit`, then drives the outgoing gates and veil expiry.

const World = preload("res://scripts/match/prototype_battle.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/hero_veil_immunity_source.json"
const VEIL_SHAPE_FLAGS := [
	"veil_gate_requires_positive_damage",
	"veil_gate_reads_is_veiled",
	"veil_gate_precedes_evasion_block",
	"update_gate_disables_autocast_while_veiled",
	"do_attack_gate_disables_attacks_while_veiled",
	"is_veiled_is_veil_timer_positive",
	"take_damage_gate_returns_before_mitigation",
]
const SOURCE_SCHOOLS := ["physical", "magic"]


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the veil fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "the veil fixture parses")
	if fixture is not Dictionary:
		return
	_shape(fixture, check)
	_replay(fixture.cases, check)
	_reactive_hooks(check)
	_outgoing_gates(check)
	_expiry(check)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	for flag in VEIL_SHAPE_FLAGS:
		check.call(bool(shape.get(flag, false)), "source veil gate present: %s" % flag)


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		var expected: Dictionary = data.get("expected", {})
		var school: Variant = expected.get("school")
		# Native `_deliver_hit` validates the resolved school string and the
		# replay only mirrors rows whose ladder reaches a school mitigation
		# path without seeding item stats (armor/evasion come from items).
		if school == null or String(school) not in SOURCE_SCHOOLS:
			continue
		if int(data.get("damage", 0)) <= 0:
			continue
		if float(data.get("evasion", 0.0)) > 0.0 or int(data.get("armor", 0)) != 0:
			continue
		replayed += 1
		var world := _world()
		var defender: HeroState = world.blue_hero()
		var attacker: HeroState = _hero_of_team(world, World.RED)
		_apply_case(world, defender, data)
		var hp_before: float = defender.hp
		var dealt_before: int = attacker.damage_dealt
		var landed: bool = world._deliver_hit(
			attacker.id,
			attacker.team,
			defender,
			int(data["damage"]),
			String(school),
			attacker.position,
			String(data.get("damage_type", "normal"))
		)
		var hp_loss := int(hp_before - defender.hp)
		check.call(
			hp_loss == int(expected["hp_loss"]),
			"%s: veil ladder deals %d damage" % [String(data["name"]), int(expected["hp_loss"])]
		)
		check.call(
			landed == (int(expected["hp_loss"]) > 0),
			"%s: landed flag follows the source ladder" % String(data["name"])
		)
		check.call(
			attacker.damage_dealt - dealt_before == int(expected["hp_loss"]),
			"%s: attacker credit follows the source" % String(data["name"])
		)
		# Divergence is only observable where the pre-9j column actually landed
		# damage; rows with their own blocker (Wind Wall, Shadow Realm, Windrun)
		# already read zero in both columns.
		if int(data["native_old"]["hp_loss"]) > 0:
			check.call(
				hp_loss != int(data["native_old"]["hp_loss"]),
				"%s: the veil column no longer equals the pre-9j column" % String(data["name"])
			)
	check.call(replayed >= 8, "at least eight fixture rows replay through the production path")


func _apply_case(world: World, defender: HeroState, data: Dictionary) -> void:
	defender.items.veil_timer = 30 if bool(data.get("veil", false)) else 0
	defender.bristleback_timer = 30 if bool(data.get("bristleback", false)) else 0
	defender.shadow_realm_timer = 30 if bool(data.get("shadow_realm", false)) else 0
	defender.wind_wall_timer = 30 if bool(data.get("wind_wall", false)) else 0
	defender.windrun_timer = 30 if bool(data.get("windrun", false)) else 0
	if bool(data.get("windrun", false)):
		# Source Windrun rolls before the veil gate; pin it so the replay stays
		# deterministic without claiming the source RNG stream.
		world.windrun_roll_override = func() -> float: return 0.01


func _reactive_hooks(check: Callable) -> void:
	# Source: the veil return sits before Bristleback and before
	# `notify_damage_taken`, so a veiled hero reflects nothing and credits
	# nobody. Both halves are driven through the production path.
	var veiled := _world()
	var veiled_defender: HeroState = veiled.blue_hero()
	var veiled_attacker: HeroState = _hero_of_team(veiled, World.RED)
	veiled_defender.items.veil_timer = 60
	veiled_defender.bristleback_timer = 60
	var attacker_hp: float = veiled_attacker.hp
	veiled._deliver_hit(
		veiled_attacker.id,
		veiled_attacker.team,
		veiled_defender,
		200,
		"physical",
		veiled_attacker.position
	)
	check.call(veiled_defender.hp == veiled_defender.max_hp, "a veiled hero takes no damage")
	check.call(
		veiled_attacker.hp == attacker_hp and veiled_defender.bristleback_timer == 60,
		"a veiled hero reflects no Bristleback damage and credits nobody"
	)
	check.call(veiled_attacker.damage_dealt == 0, "a veiled hero credits no damage dealer")
	# Control: the same hit lands once the veil is gone.
	var open_world := _world()
	var open_defender: HeroState = open_world.blue_hero()
	var open_attacker: HeroState = _hero_of_team(open_world, World.RED)
	open_defender.bristleback_timer = 60
	var control_hp: float = open_attacker.hp
	open_world._deliver_hit(
		open_attacker.id, open_attacker.team, open_defender, 200, "physical", open_attacker.position
	)
	check.call(open_defender.hp < open_defender.max_hp, "without the veil the hit lands")
	check.call(
		control_hp - open_attacker.hp == 35.0,
		"without the veil Bristleback reflects 25% of the mitigated 140 damage"
	)
	check.call(open_attacker.damage_dealt == 140, "without the veil the attacker is credited")
	# Non-positive raw damage never reaches the hero ladder: the shared
	# `_deliver_hit` guard rejects it before the veil gate (source
	# `credit_hero_damage(source, 0)` is unreachable here), which is a
	# pre-existing lab rule and not part of the veil gap.
	var zero := _world()
	var zero_defender: HeroState = zero.blue_hero()
	var zero_attacker: HeroState = _hero_of_team(zero, World.RED)
	check.call(
		not zero._deliver_hit(
			zero_attacker.id,
			zero_attacker.team,
			zero_defender,
			0,
			"physical",
			zero_attacker.position
		),
		"non-positive damage is rejected before the veil ladder"
	)


func _outgoing_gates(check: Callable) -> void:
	# `_entity.py:4241` (`_do_attack`) and `:3799` (`Hero.update` `_disabled`).
	var world := _world()
	var hero: HeroState = world.blue_hero()
	var foe: HeroState = _hero_of_team(world, World.RED)
	foe.position = hero.position + Vector2(20, 0)
	hero.attack_timer = 0
	hero.items.veil_timer = 60
	check.call(
		not world.hero_basic_attack(hero.id, foe.id), "a veiled hero cannot launch a basic attack"
	)
	hero.auto_cast_enabled = true
	hero.auto_cast_check_timer = 1
	world._step_hero_auto_cast(hero)
	check.call(
		hero.auto_cast_check_timer == 1, "a veiled hero does not advance its auto-cast check timer"
	)
	hero.items.veil_timer = 0
	world._step_hero_auto_cast(hero)
	check.call(
		hero.auto_cast_check_timer == 20, "without the veil the auto-cast check timer runs again"
	)
	check.call(world.hero_basic_attack(hero.id, foe.id), "without the veil the basic attack lands")
	# The AI path must stay ungated: the source controller calls the shared
	# auto-cast itself, veil or not.
	var ai_world := _world()
	var ai_hero: HeroState = ai_world.blue_hero()
	var ai_foe: HeroState = _hero_of_team(ai_world, World.RED)
	ai_foe.position = ai_hero.position + Vector2(40, 0)
	ai_hero.items.veil_timer = 60
	ai_hero.r_cooldown = 0
	ai_hero.skill_timer = 0
	ai_world.try_auto_cast(ai_hero)
	check.call(
		ai_hero.active_skill_timer > 0 or ai_hero.r_cooldown > 0,
		"the shared AI auto-cast still fires while the veil holds"
	)


func _expiry(check: Callable) -> void:
	var world := _world()
	var hero: HeroState = world.blue_hero()
	var foe: HeroState = _hero_of_team(world, World.RED)
	hero.items.veil_timer = 2
	world._deliver_hit(foe.id, foe.team, hero, 200, "physical", foe.position)
	check.call(hero.hp == hero.max_hp, "the veil blocks the first hit")
	for _tick in range(3):
		world.step_tick()
	check.call(hero.items.veil_timer == 0, "the veil timer runs out with the item clock")
	var hp_before: float = hero.hp
	world._deliver_hit(foe.id, foe.team, hero, 200, "physical", foe.position)
	check.call(hero.hp < hp_before, "after expiry the hero is damageable again")


func _world() -> World:
	var world := World.new()
	world.setup_arena()
	return world


func _hero_of_team(world: World, team: int) -> HeroState:
	for unit in world.units:
		var hero := unit as HeroState
		if hero != null and hero.is_hero and hero.team == team and hero.alive:
			return hero
	return null
