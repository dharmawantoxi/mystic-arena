# gdlint:disable=max-file-lines
extends RefCounted
## Layer 8f native suite: source entrance draw decisions and death effect
## retention after active boss registry retirement.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const FIXTURE := "res://tests/fixtures/boss_presentation_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(
		fixture is Dictionary and fixture.has("entrance") and fixture.has("death"),
		"boss presentation fixture parses"
	)
	if not fixture is Dictionary:
		return
	_check_entrance(check, fixture.entrance, "mini_full", "mini", 120, 120, 40, 7)
	_check_entrance(check, fixture.entrance, "mini_mid", "mini", 60, 120, 40, 7)
	_check_entrance(check, fixture.entrance, "true_full", "true", 180, 180, 60, 7)
	_check_entrance(check, fixture.entrance, "true_early", "true", 45, 180, 60, 7)
	_check_death(check, fixture.death, "mini_death", "gornak", 20)
	_check_death(check, fixture.death, "true_death", "abaddon", 28)


func _entry(rows: Array, label: String) -> Dictionary:
	for row in rows:
		if String(row.get("label", "")) == label:
			return row
	return {}


func _last_text(commands: Array) -> Dictionary:
	var result := {}
	for command in commands:
		if String(command.get("op", "")) == "text":
			result = command
	return result


func _circle(commands: Array) -> Dictionary:
	for command in commands:
		if String(command.get("op", "")) == "circle":
			return command
	return {}


func _check_entrance(
	check: Callable,
	rows: Array,
	label: String,
	boss_class: String,
	timer: int,
	maximum: int,
	radius: float,
	anim: int
) -> void:
	var boss := BossState.new()
	boss.boss_class = boss_class
	boss.entrance_timer = timer
	boss.entrance_ticks = maximum
	boss.radius = radius
	boss.anim_time = anim
	var state := boss.entrance_presentation_state()
	var source := _entry(rows, label)
	var commands: Array = source.get("commands", [])
	var circle := _circle(commands)
	var text := _last_text(commands)
	var has_circle := not circle.is_empty()
	var has_text := not text.is_empty()
	check.call(
		(int(state["aura_radius"]) > 0) == has_circle, "native entrance aura visibility: %s" % label
	)
	if has_circle:
		check.call(
			(
				int(state["aura_radius"]) == int(circle.get("radius", -1))
				and int(state["aura_alpha"]) == int(circle.get("color", [0, 0, 0, -1])[3])
			),
			"native entrance aura geometry: %s" % label
		)
	var announcement_matches := bool(state["text_visible"]) == has_text
	if has_text:
		announcement_matches = (
			announcement_matches and int(state["text_alpha"]) == int(text.get("alpha", -1))
		)
	check.call(announcement_matches, "native entrance announcement parity: %s" % label)


func _check_death(
	check: Callable, rows: Array, label: String, boss_type: String, shake: int
) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss(boss_type)
	check.call(boss != null, "presentation boss spawns: %s" % label)
	if boss == null:
		return
	boss.entrance_timer = 0
	boss.hp = float(boss.max_damage_per_hit)
	boss.alive = true
	boss.defeated = false
	var attacker: HeroState = null
	for unit in world.units:
		if unit is HeroState and unit.team == world.BLUE:
			attacker = unit as HeroState
			break
	check.call(attacker != null, "presentation death attacker exists: %s" % label)
	if attacker == null:
		return
	check.call(
		world._deliver_hit(attacker.id, world.BLUE, boss, 99999, "physical", boss.position),
		"presentation death hit lands: %s" % label
	)
	var source := _entry(rows, label)
	var source_shake := 0
	for effect in source.get("effects", []):
		if String(effect.get("name", "")) == "shake_screen":
			source_shake = int(effect.get("args", [0])[0])
	check.call(source_shake == shake, "source death shake fixture: %s" % label)
	check.call(world.boss_death_presentations.size() == 1, "death payload is queued: %s" % label)
	if world.boss_death_presentations.is_empty():
		return
	var snapshot: Dictionary = world.boss_death_presentations[0]
	check.call(
		(
			(not boss.alive)
			and boss.defeated
			and int(snapshot.get("timer", 0)) == 35
			and int(snapshot.get("flash_timer", 0)) == 8
			and int(snapshot.get("particle_count", 0)) == 25
			and int(snapshot.get("shake_intensity", 0)) == shake
			and world.boss_screen_shake_timer == 8
			and is_equal_approx(world.boss_screen_shake_intensity, float(shake))
		),
		"native death payload matches source effect contract: %s" % label
	)
	world._process_boss_result()
	check.call(
		world.active_boss == null and world.boss_death_presentations.size() == 1,
		"death presentation survives boss registry retirement: %s" % label
	)
	world._tick_boss_death_presentations()
	check.call(
		(
			int(world.boss_death_presentations[0].get("timer", 0)) == 34
			and int(world.boss_death_presentations[0].get("flash_timer", 0)) == 7
			and world.boss_screen_shake_timer == 7
		),
		"death presentation ticks independently: %s" % label
	)
