extends RefCounted
## Layer 9ao/9ao-2/9ao-3 native suite: the one-shot enrage screen-shake
## payload routes through the death-shake gate, and the fixture carries the
## authoritative 128-site source table (66 cast sites are wired; the
## remaining 60 stay a staged wiring roadmap).

const BossAI = preload("res://scripts/match/boss_ai.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const FIXTURE := "res://tests/fixtures/boss_shake_sites_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "shake site fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	_enrage_replay(check, "alchemist", "true", 0.4, 25)
	_enrage_replay(check, "morgath", "mini", 0.35, 15)
	_cast_shake_probes(check)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(int(shape.get("total_sites", 0)) == 128, "the source fires 128 shake sites")
	check.call(int(shape.get("method_count", 0)) == 113, "spread over 113 boss methods")
	check.call(
		int(shape.get("cast_sites_total", 0)) == 126, "the source fires 126 cast shake sites"
	)
	check.call(
		(
			int(shape.get("cast_sites_wired", 0)) == 66
			and int(shape.get("cast_sites_remaining", -1)) == 60
		),
		"the fifteen audited families wire 66 cast sites, 60 stay on the roadmap"
	)
	var enrage: Array = shape.get("enrage_sites", [])
	check.call(
		(
			enrage.size() == 2
			and String(enrage[0].get("class", "")) == "enrage_true"
			and int(enrage[0].get("intensity", 0)) == 25
			and String(enrage[1].get("class", "")) == "enrage_mini"
			and int(enrage[1].get("intensity", 0)) == 15
		),
		"the enrage transitions shake 25 (true) and 15 (mini)"
	)
	var wiring: Dictionary = shape.get("native_wiring", {})
	var wired := true
	for key in wiring:
		# `bool(...)` has no Array constructor in GDScript - fold only the
		# boolean pins here and compare the multiset separately.
		if String(key) == "native_cast_multiset":
			continue
		wired = wired and bool(wiring[key])
	check.call(wired, "the shake wiring pins all hold")
	# JSON numbers parse as floats in GDScript - normalize both sides to int
	# so the Array equality is exact.
	var multiset: Array = []
	for value in Array(wiring.get("native_cast_multiset", [])):
		multiset.append(int(value))
	multiset.sort()
	var expected_multiset: Array = []
	for row in fixture.get("rows", []):
		if String(row.get("class", "")) == "cast" and bool(row.get("wired", false)):
			# `_gorath_r` answers TWO smart-AI gates, so its native arm shakes
			# at the end of both R branches - expand each row by its source
			# helper call-site count.
			for _copy in range(int(row.get("native_occurrences", 1))):
				expected_multiset.append(int(row.get("intensity", 0)))
	expected_multiset.sort()
	check.call(
		multiset == expected_multiset,
		"the native shake intensity multiset equals the wired source rows"
	)
	var wired_rows := 0
	for row in fixture.get("rows", []):
		if bool(row.get("wired", false)):
			wired_rows += 1
	check.call(wired_rows == 68, "the two enrage sites plus the 66 family casts are wired")


func _cast_shake_probes(check: Callable) -> void:
	var enemies: Array[UnitState] = []
	# Chemical Rage cast shakes 12 (`_cast_e_chemical_rage:1347`).
	var world := Prototype.new()
	world.setup_arena()
	var alchemist := world._spawn_boss("alchemist")
	check.call(alchemist != null, "rage shake probe spawns")
	if alchemist != null:
		alchemist.hp = float(alchemist.max_hp) * 0.5
		BossAI._alchemist(world, alchemist, enemies, null, 999.0)
		check.call(alchemist.rage_active, "the rage cast fires in the shake probe")
		check.call(
			world.effects.screen_shake.intensity == 12.0,
			"the rage cast shakes the screen with intensity 12"
		)
	# Shukuchi geminate whiff shakes 8 (`_xirthalis_e:2313`).
	var whiff_world := Prototype.new()
	whiff_world.setup_arena()
	var xirthalis := whiff_world._spawn_boss("xirthalis")
	check.call(xirthalis != null, "whiff shake probe spawns")
	if xirthalis != null:
		BossAI._xirthalis(whiff_world, xirthalis, enemies, null, 200.0)
		check.call(
			whiff_world.effects.screen_shake.intensity == 8.0,
			"the geminate whiff shakes the screen with intensity 8"
		)
	# 9ao-3: gorath's low-self-HP R gate is the SECOND `_gorath_r` branch and
	# shakes 22 after the execute hit (`_gorath_r:3338`, called twice).
	var gorath_world := Prototype.new()
	gorath_world.setup_arena()
	var gorath := gorath_world._spawn_boss("gorath")
	check.call(gorath != null, "gorath shake probe spawns")
	if gorath != null:
		gorath.hp = float(gorath.max_hp) * 0.4
		gorath.q_timer = 1
		gorath.e_timer = 1
		BossAI._gorath(gorath_world, gorath, enemies, null, 999.0)
		check.call(gorath.r_timer > 0, "the low-HP execute branch fires in the shake probe")
		check.call(
			gorath_world.effects.screen_shake.intensity == 22.0,
			"the second gorath execute branch shakes the screen with intensity 22"
		)
	# 9ao-3: xerathis E is the arcane buff branch - the tail shake 10 lands
	# after the buff fields and the heal (`_xerathis_e:3593`).
	var arcane_world := Prototype.new()
	arcane_world.setup_arena()
	var xerathis := arcane_world._spawn_boss("xerathis")
	check.call(xerathis != null, "xerathis shake probe spawns")
	if xerathis != null:
		BossAI._xerathis(arcane_world, xerathis, enemies, null, 999.0)
		check.call(xerathis.arcane_buff_active, "the arcane buff cast fires in the shake probe")
		check.call(
			arcane_world.effects.screen_shake.intensity == 10.0,
			"the arcane buff cast shakes the screen with intensity 10"
		)


func _enrage_replay(
	check: Callable, boss_type: String, klass: String, hp_ratio: float, shake: int
) -> void:
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss(boss_type)
	check.call(boss != null, "enrage shake probe spawns: %s" % boss_type)
	if boss == null:
		return
	check.call(boss.boss_class == klass, "%s is a %s class boss" % [boss_type, klass])
	boss.entrance_timer = 0
	boss.hp = float(boss.max_hp) * hp_ratio
	boss.advance_combat_clock()
	check.call(boss.is_enraged, "the %s enrage transition fires" % boss_type)
	check.call(
		boss.enrage_fx_shake == shake, "%s stores the source %d shake payload" % [boss_type, shake]
	)
	world._present_boss_enrage_shake(boss)
	check.call(boss.enrage_fx_shake == 0, "the payload is one-shot: %s" % boss_type)
	check.call(
		world.effects.screen_shake.intensity == float(shake),
		"the effect manager receives the %s enrage shake" % boss_type
	)
	check.call(
		world.boss_screen_shake_intensity == float(shake) and world.boss_screen_shake_timer == 8,
		"the boss shake gate mirrors the death path: %s" % boss_type
	)
