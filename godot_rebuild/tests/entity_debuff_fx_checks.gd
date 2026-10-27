extends RefCounted
## Layer 9bq10: replays the fixture of `entity_debuff_fx_source_oracle.py` - the shared
## `TowerDebuffMixin._draw_tower_debuff_fx` recorded at the two `_entity.py` call sites - through
## `boss_debuff_fx_layout.gd`, and checks that the view builds the same ops from live timers.
## The fixture also carries an `ast` audit of `Hero.draw` / `Minion.draw`, so the argument list,
## the `include_rings` flag and the neighbouring statements stay pinned to the source.

const Layout = preload("res://scripts/ui/boss_debuff_fx_layout.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const MinionView = preload("res://scenes/combat/minion_view.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const FIXTURE := "res://tests/fixtures/entity_debuff_fx_source.json"
const COMPARED_KEYS := {
	"circle": ["center", "radius", "width", "color", "mult"],
	"ellipse": ["rect", "width", "color", "mult"],
	"rect": ["rect", "width", "radius", "color", "mult"],
}
const TOTAL_OPS := 54
const ANCHOR := 640
const ANCHOR_Y := 360


static func _value_equal(actual: Variant, expected: Variant) -> bool:
	if expected is Array:
		if not (actual is Array) or actual.size() != expected.size():
			return false
		for index in range(expected.size()):
			if not _value_equal(actual[index], expected[index]):
				return false
		return true
	if expected is float or expected is int:
		return (actual is float or actual is int) and absf(float(actual) - float(expected)) < 1e-6
	return str(actual) == str(expected)


static func _op_equal(actual: Dictionary, expected: Dictionary) -> bool:
	if str(actual.get("kind", "")) != str(expected.get("kind", "")):
		return false
	var keys: Array = COMPARED_KEYS.get(str(expected.get("kind", "")), [])
	for key_name in keys:
		if expected.has(key_name) != actual.has(key_name):
			return false
		if expected.has(key_name) and not _value_equal(actual[key_name], expected[key_name]):
			return false
	return true


static func _first_mismatch(actual: Array, expected: Array) -> int:
	for index in range(mini(actual.size(), expected.size())):
		if not _op_equal(actual[index], expected[index]):
			return index
	return -1 if actual.size() == expected.size() else mini(actual.size(), expected.size())


static func _report(label: String, actual: Array, expected: Array) -> String:
	var index := _first_mismatch(actual, expected)
	if index == -1:
		return "%s matches the source ops" % label
	var mine: Variant = actual[index] if index < actual.size() else {}
	var theirs: Variant = expected[index] if index < expected.size() else {}
	return (
		"%s differs at op %d/%d: %s vs source %s"
		% [label, index, expected.size(), str(mine), str(theirs)]
	)


static func _frame(frames: Array, label: String) -> Dictionary:
	for frame in frames:
		if String(frame["label"]) == label:
			return frame
	return {}


static func _from_frame(frame: Dictionary) -> Array:
	return Layout.ops(
		ANCHOR,
		ANCHOR_Y,
		int(frame["radius"]),
		int(frame["slow"]),
		int(frame["atk_slow"]),
		int(frame["skill_down"]),
		int(frame["anti_heal"]),
		int(frame["burn"]),
		float(frame["anim_time"]),
		bool(frame["include_rings"])
	)


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Entity debuff fixture parses")
	if not (data is Dictionary):
		return
	var total := 0
	for frame in data["frames"]:
		total += frame["ops"].size()
	check.call(
		int(data["frames"].size()) == 8 and total == TOTAL_OPS,
		"Entity debuff oracle pins 8 frames and %d draw ops (got %d)" % [TOTAL_OPS, total]
	)
	_check_call_sites(check, data)
	_check_frames(check, data)
	_check_shape(check, data)
	_check_hero_wiring(check, data)
	_check_minion_wiring(check, data)


func _check_call_sites(check: Callable, data: Dictionary) -> void:
	var hero: Dictionary = data["call_sites"]["Hero"]
	var minion: Dictionary = data["call_sites"]["Minion"]
	check.call(
		(
			hero["args"] == ["surface", "x", "y", "self.radius"]
			and hero["kwargs"].is_empty()
			and int(hero["radius"]) == 16
		),
		"`Hero.draw` feeds the indicator its own radius and the default ring flag"
	)
	check.call(
		(
			"self._draw_hero_shape(surface, x, y)" == String(hero["after"])
			and "self.radius * 2, 8" in String(hero["before"])
			and hero["before"].find("ellipse") != -1
		),
		"`Hero.draw` paints the indicator after the ground shadow, before the hero shape"
	)
	check.call(
		(
			minion["args"] == ["surface", "x", "y", "self.radius"]
			and String(minion["kwargs"].get("include_rings", "")) == "False"
		),
		"`Minion.draw` calls the indicator with `include_rings=False`"
	)
	check.call(
		(
			"self.slow_timer > 0" in String(minion["before"])
			and String(minion["after"]).find("render_minion") != -1
		),
		"`Minion.draw` paints the indicator after the ice aura, before the minion body"
	)


func _check_frames(check: Callable, data: Dictionary) -> void:
	for frame in data["frames"]:
		var actual: Array = []
		if bool(frame["alive"]):
			actual = _from_frame(frame)
		check.call(
			_first_mismatch(actual, frame["ops"]) == -1,
			_report("Entity debuff %s" % frame["label"], actual, frame["ops"])
		)


func _check_shape(check: Callable, data: Dictionary) -> void:
	var counts: Array = []
	for frame in data["frames"]:
		counts.append(frame["ops"].size())
	check.call(
		counts == [0, 3, 8, 17, 2, 8, 16, 0],
		"Only the active debuffs paint, and a hero radius stays 16 while a minion uses 9"
	)
	var hero_slow: Dictionary = _frame(data["frames"], "hero_slow_only")
	check.call(
		(
			str(hero_slow["ops"][0]["kind"]) == "ellipse"
			and int(hero_slow["ops"][0]["width"]) == 1
			and _value_equal(hero_slow["ops"][0]["rect"], [622, 369, 36, 10])
		),
		"`Hero.draw` keeps the 1 px slow ring around its 16 px body"
	)
	var minion_slow: Dictionary = _frame(data["frames"], "minion_slow_only_no_rings")
	check.call(
		(
			str(minion_slow["ops"][0]["kind"]) == "rect"
			and _value_equal(minion_slow["ops"][0]["rect"], [637, 380, 5, 5])
			and minion_slow["ops"].size() == 2
		),
		"`Minion.draw` drops the ring: only the slow pip pair remains"
	)
	var dead: Dictionary = _frame(data["frames"], "minion_dead_ignores_everything")
	check.call(
		int(dead["ops"].size()) == 0 and not bool(dead["alive"]),
		"A dead unit paints no indicator at all"
	)


func _check_hero_wiring(check: Callable, data: Dictionary) -> void:
	var view := PrototypeView.new()
	var hero := HeroState.new()
	hero.position = Vector2(ANCHOR, ANCHOR_Y)
	check.call(
		view.hero_debuff_draw_ops(hero, 0.0).is_empty(), "A clean hero paints no debuff indicator"
	)
	var all: Dictionary = _frame(data["frames"], "hero_all_debuffs")
	hero.slow_timer = int(all["slow"])
	hero.atk_slow_timer = int(all["atk_slow"])
	hero.skill_down_timer = int(all["skill_down"])
	hero.anti_heal_timer = int(all["anti_heal"])
	hero.burn_timer = int(all["burn"])
	var actual := view.hero_debuff_draw_ops(hero, float(all["anim_time"]))
	check.call(
		_first_mismatch(actual, all["ops"]) == -1, _report("Hero debuff wiring", actual, all["ops"])
	)
	hero.burn_timer = 0
	hero.anti_heal_timer = 0
	hero.skill_down_timer = 0
	hero.atk_slow_timer = 0
	check.call(
		view.hero_debuff_draw_ops(hero, 3.0).size() == 3,
		"Slow alone keeps the ring plus its own pip pair"
	)
	hero.slow_timer = 0
	check.call(
		view.hero_debuff_draw_ops(hero, 3.0).is_empty(), "Clearing the timers clears the indicator"
	)
	hero.alive = false
	hero.burn_timer = 20
	check.call(view.hero_debuff_draw_ops(hero, 0.0).is_empty(), "A dead hero paints no indicator")
	view.free()


func _check_minion_wiring(check: Callable, data: Dictionary) -> void:
	var view := MinionView.new()
	var unit := UnitState.new()
	unit.definition = GOBLIN
	unit.position = Vector2(ANCHOR, ANCHOR_Y)
	check.call(
		int(unit.definition.radius_px) == 9,
		"The minion definition keeps the radius the fixture recorded"
	)
	check.call(
		view.minion_debuff_draw_ops(unit, 0).is_empty(), "A clean minion paints no debuff indicator"
	)
	var all: Dictionary = _frame(data["frames"], "minion_all_debuffs")
	unit.slow_timer = int(all["slow"])
	unit.atk_slow_timer = int(all["atk_slow"])
	unit.skill_down_timer = int(all["skill_down"])
	unit.anti_heal_timer = int(all["anti_heal"])
	unit.burn_timer = int(all["burn"])
	var actual := view.minion_debuff_draw_ops(unit, int(all["anim_time"]))
	check.call(
		_first_mismatch(actual, all["ops"]) == -1,
		_report("Minion debuff wiring", actual, all["ops"])
	)
	unit.burn_timer = 0
	unit.anti_heal_timer = 0
	unit.skill_down_timer = 0
	unit.atk_slow_timer = 0
	var slow_only := view.minion_debuff_draw_ops(unit, 0)
	check.call(
		slow_only.size() == 2 and str(slow_only[0]["kind"]) == "rect",
		"The minion path never paints the slow ellipse"
	)
	unit.alive = false
	unit.burn_timer = 20
	check.call(view.minion_debuff_draw_ops(unit, 0).is_empty(), "A dead minion paints no indicator")
	view.free()
