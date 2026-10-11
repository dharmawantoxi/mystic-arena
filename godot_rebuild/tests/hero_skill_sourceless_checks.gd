extends RefCounted
## 9m: Thorne's Viscous Nose (Q) is a SOURCELESS hit in the source.
## `hero_skills/_bundle.py::_NS_thorne_skills.cast_q` (`:4563-4609`) sprays a
## 60 px / 60-degree cone and runs `e.take_damage(int(h.skill_damage * 0.8),
## h.team)` (`:4601`) plus `self._apply_slow(e, 0.4, 180)` (`:4603`) - no
## `source=`, no school, no `damage_type`. So the victim ladder sees
## `source=None` / `_school=None`: the hit is never credited to
## `hero.damage_dealt` (the ATTACK DAMAGE DEALER picker), the attacker's true
## strike/blind is not consulted, and a non-hero victim takes it raw (no armor).
##
## The native arm used to send `hero.id` with `hero.dmg_school`, which credited
## the caster and let a physical school cut minion/tower armor. This suite
## replays the sealed `hero_skill_sourceless_source.json` fixture (both columns
## executed from the real `Hero.take_damage` and `Tower.take_damage`) through
## the production `ThorneSkills.cast(world, hero, "q", structures)`.

const World = preload("res://scripts/match/prototype_battle.gd")
const DamageRules = preload("res://scripts/combat/damage_rules.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const THORNE = preload("res://data/heroes/thorne.tres")
const TROLL = preload("res://data/minions/troll.tres")
const ARCHER = preload("res://data/structures/archer_level_1.tres")
const STEEL_AEGIS := "steel_aegis"
const FIXTURE := "res://tests/fixtures/hero_skill_sourceless_source.json"
const SOURCE_FLAGS := [
	"take_damage_has_two_positional_args",
	"take_damage_passes_no_source",
	"take_damage_passes_no_school",
	"damage_multiplier_is_0_8",
	"cone_length_is_60",
	"cone_half_angle_is_30_degrees",
	"slow_is_0_4_for_180_ticks",
]


func run(check: Callable) -> void:
	check.call(FileAccess.file_exists(FIXTURE), "the sourceless skill fixture is committed")
	if not FileAccess.file_exists(FIXTURE):
		return
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "the sourceless skill fixture parses")
	if fixture is not Dictionary:
		return
	_shape(fixture, check)
	_arm(fixture, check)
	_replay(fixture.cases, check)
	_cone_and_slow(check)


func _shape(fixture: Dictionary, check: Callable) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	for flag in SOURCE_FLAGS:
		check.call(bool(shape.get(flag, false)), "source arm shape present: %s" % flag)
	var arm: Dictionary = fixture.get("arm", {})
	check.call(float(arm.get("multiplier", 0.0)) == 0.8, "the arm multiplies skill damage by 0.8")
	check.call(int(arm.get("skill_base", 0)) == 70, "the arm records Thorne's skill base")
	var record: Array = arm.get("record", [])
	check.call(record.size() >= 1, "the executed arm hit at least one victim")
	if record.is_empty():
		return
	var first: Dictionary = record[0]
	check.call(not bool(first.get("source", true)), "the executed arm sends no source")
	check.call(first.get("school") == null, "the executed arm sends no school")
	check.call(
		String(first.get("damage_type", "")) == "normal",
		"the executed arm keeps damage_type normal"
	)


func _arm(fixture: Dictionary, check: Callable) -> void:
	# The cone geometry the arm recorded: behind/outside/far victims are skipped.
	var arm: Dictionary = fixture.get("arm", {})
	var targets: Array = arm.get("hit_targets", [])
	check.call("unit_in_cone" in targets, "the cone hits the unit in front")
	check.call("structure_in_cone" in targets, "the cone hits a structure in front")
	check.call(not ("unit_behind" in targets), "the cone skips a unit behind the hero")
	check.call(
		not ("unit_outside_cone" in targets),
		"the cone skips a unit outside the 30 degree half angle"
	)
	check.call(not ("unit_too_far" in targets), "the cone skips a unit beyond 60 px")


func _replay(rows: Array, check: Callable) -> void:
	var replayed := 0
	for row in rows:
		var data: Dictionary = row as Dictionary
		var label := String(data["name"])
		var raw := int(data["raw_damage"])
		match String(data.get("victim", "")):
			"hero":
				replayed += 1
				_hero_victim(check, data, label, raw)
			"tower":
				replayed += 1
				_tower_victim(check, data, label, raw)
	check.call(replayed >= 4, "every fixture row replays through the production cast")


func _hero_victim(check: Callable, data: Dictionary, label: String, raw: int) -> void:
	var world := _world()
	var thorne := _thorne(world)
	var victim: HeroState = _hero_of_team(world, World.RED)
	if thorne == null or victim == null:
		return
	if int(data.get("item_armor", 0)) > 0:
		check.call(victim.items.add(STEEL_AEGIS), "%s: the armour item is addable" % label)
	victim.position = thorne.position + Vector2(40.0, 0.0)
	var expected: Dictionary = data["expected"]
	var native_old: Dictionary = data["native_old"]
	var hp_before: float = victim.hp
	var credit_before: int = thorne.damage_dealt
	check.call(
		world.cast_hero_q(thorne.id, world.structures), "%s: the production cast fires" % label
	)
	var loss := int(hp_before - victim.hp)
	check.call(
		loss == int(expected["hp_loss"]),
		"%s: the victim loses %d" % [label, int(expected["hp_loss"])]
	)
	check.call(
		thorne.damage_dealt == credit_before,
		"%s: a sourceless skill hit is not credited to the caster" % label
	)
	check.call(
		(
			int(native_old["hp_loss"]) == int(expected["hp_loss"])
			and int(native_old["credits"][0][1]) == int(expected["hp_loss"])
		),
		"%s: the pre-9m column only differed by the credit" % label
	)
	# Counterfactual: the same hit WITH the caster as source is credited, which is
	# exactly the pre-9m behaviour this layer removed.
	var hp_after: float = victim.hp
	var landed := world._deliver_hit(
		thorne.id, thorne.team, victim, raw, thorne.dmg_school, thorne.position
	)
	check.call(
		landed and thorne.damage_dealt > credit_before and victim.hp < hp_after,
		"%s: an attributed hit would still credit the caster" % label
	)


func _tower_victim(check: Callable, data: Dictionary, label: String, raw: int) -> void:
	# The fixture's tower rows pin an armour value; the arena tower carries its
	# own, so the assertion is the school gate itself: sourceless lands raw,
	# a physical school would cut it by the tower's armour.
	var world := _world()
	var thorne := _thorne(world)
	var tower: StructureState = world.spawn_structure(ARCHER, World.RED, Vector2(400.0, 380.0))
	if thorne == null or tower == null:
		check.call(false, "%s: the control tower spawns" % label)
		return
	var armor := float(tower.definition.armor)
	var physical := DamageRules.resolve(
		raw, armor, float(tower.definition.magic_resist), "physical"
	)
	check.call(
		armor > 0.0 and physical < raw,
		"%s: the control tower armour can cut a physical hit" % label
	)
	tower.position = thorne.position + Vector2(40.0, 0.0)
	# `spawn_structure` hands a fresh tower the free shield, which would swallow
	# the hit before HP; the fixture rows measure HP damage, so drop it first.
	tower.shield = 0
	tower.free_shield_active = false
	tower.shield_active = false
	var hp_before: float = tower.hp
	var credit_before: int = thorne.damage_dealt
	var cast_ok: bool = world.cast_hero_q(thorne.id, world.structures)
	var loss := int(hp_before - tower.hp)
	check.call(cast_ok, "%s: the production cast fires" % label)
	(
		check
		. call(
			loss == int(data["expected"]["hp_loss"]),
			(
				"%s: structure loss %d (sourceless expected %d, physical %d, raw %d, armor %.1f)"
				% [
					label,
					loss,
					int(data["expected"]["hp_loss"]),
					physical,
					raw,
					armor,
				]
			)
		)
	)
	check.call(
		loss != physical, "%s: no school mitigation is applied to a sourceless skill hit" % label
	)
	check.call(
		thorne.damage_dealt == credit_before,
		"%s: a structure hit is not credited to the caster" % label
	)


func _cone_and_slow(check: Callable) -> void:
	var world := _world()
	var thorne := _thorne(world)
	var raw := int(thorne.skill_damage() * 0.8)
	var troll = world.spawn_unit(TROLL, World.RED, 1)
	var behind = world.spawn_unit(TROLL, World.RED, 1)
	if troll == null or behind == null:
		check.call(false, "the cone control units spawn")
		return
	troll.position = thorne.position + Vector2(40.0, 0.0)
	behind.position = thorne.position - Vector2(40.0, 0.0)
	var troll_hp: float = troll.hp
	var behind_hp: float = behind.hp
	check.call(world.cast_hero_q(thorne.id, world.structures), "the cone control cast fires")
	check.call(
		int(troll_hp - troll.hp) == raw,
		"a sourceless skill hit ignores minion armour (%d raw)" % raw
	)
	check.call(behind.hp == behind_hp, "a unit behind the hero takes no cone damage")
	check.call(
		troll.slow_timer > 0 and is_equal_approx(troll.slow_amount, 0.4), "the cone slows its unit"
	)
	check.call(behind.slow_timer == 0, "a unit behind the hero is not slowed")
	check.call(thorne.damage_dealt == 0, "the whole cone leaves the caster credit at zero")


func _world() -> World:
	var world := World.new()
	world.setup_arena()
	return world


func _thorne(world: World) -> HeroState:
	# The arena spawns a mirrored Kaizen pair; Thorne is spawned for the cast.
	var thorne := world.spawn_hero(THORNE, World.BLUE, Vector2(500.0, 380.0))
	if thorne != null:
		# Pin the kit value the fixture was generated from (skill base 70).
		thorne.skill_value = 70
		thorne.skill_down_timer = 0
		thorne.facing = 1.0
	return thorne


func _hero_of_team(world: World, team: int) -> HeroState:
	for unit in world.units:
		var hero := unit as HeroState
		if hero != null and hero.is_hero and hero.team == team and hero.alive:
			return hero
	return null
