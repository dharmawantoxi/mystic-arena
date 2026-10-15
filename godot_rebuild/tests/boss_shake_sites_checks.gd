extends RefCounted
## Layer 9ao native suite: the one-shot enrage screen-shake payload routes
## through the death-shake gate, and the fixture carries the authoritative
## 128-site source table (the 126 cast sites remain a staged wiring roadmap).

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/boss_shake_sites_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("rows"), "shake site fixture parses")
	if not fixture is Dictionary:
		return
	_shape_check(check, fixture)
	_enrage_replay(check, "alchemist", "true", 0.4, 25)
	_enrage_replay(check, "morgath", "mini", 0.35, 15)


func _shape_check(check: Callable, fixture: Dictionary) -> void:
	var shape: Dictionary = fixture.get("shape", {})
	check.call(int(shape.get("total_sites", 0)) == 128, "the source fires 128 shake sites")
	check.call(int(shape.get("method_count", 0)) == 113, "spread over 113 boss methods")
	check.call(
		int(shape.get("cast_sites_total", 0)) == 126,
		"126 cast sites stay on the staged wiring roadmap"
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
		wired = wired and bool(wiring[key])
	check.call(wired, "the enrage shake payload is wired end to end")
	var wired_rows := 0
	for row in fixture.get("rows", []):
		if bool(row.get("wired", false)):
			wired_rows += 1
	check.call(wired_rows == 2, "exactly the two enrage sites are wired so far")


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
