extends RefCounted
## Replays the `_render.py::BossIntroCinematic` source oracle fixture through the
## native port. `boss_intro_cinematic_source_oracle.py` runs the real `draw()`
## under a pygame shim and reads the fade, slide, HP-bar and tag values off the
## frame with `settrace`, and records the banner rectangles the shim sees. So
## the numbers below are the source's, not a copy of its formulas.

const BossIntroCinematic = preload("res://scripts/ui/boss_intro_cinematic.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const FIXTURE := "res://tests/fixtures/boss_intro_cinematic_source.json"

const KEY_BY_NAME := {"space": KEY_SPACE, "escape": KEY_ESCAPE, "letter_a": KEY_A}


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Boss intro fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed

	_check_constants(check, data)
	_check_timeline(check, data)
	_check_skips(check, data)
	_check_bosses(check, data)
	_check_literals(check)
	_check_runtime_wiring(check)


func _check_constants(check: Callable, data: Dictionary) -> void:
	var duration: int = int(data["duration"])
	check.call(duration == BossIntroCinematic.DURATION, "Boss intro duration matches source")
	var fade_in: int = int(data["fade_in_ticks"])
	check.call(fade_in == BossIntroCinematic.FADE_IN_TICKS, "Boss intro fade-in matches source")
	var fade_out: int = int(data["fade_out_ticks"])
	check.call(fade_out == BossIntroCinematic.FADE_OUT_TICKS, "Boss intro fade-out matches source")
	var slide: int = int(data["slide_ticks"])
	check.call(slide == BossIntroCinematic.SLIDE_TICKS, "Boss intro slide length matches source")
	var hp_span: float = float(data["hp_span"])
	check.call(
		is_equal_approx(hp_span, BossIntroCinematic.HP_SPAN), "Boss intro HP span matches source"
	)


func _check_timeline(check: Callable, data: Dictionary) -> void:
	var card := BossIntroCinematic.new()
	card.setup(data["timeline_boss_snapshot"], 1280, 720)
	var sound: Array = data["sound_on_first_update"]
	var timeline: Array = data["timeline"]
	var sound_ok := true
	var drift := -1
	for index in range(timeline.size()):
		var row: Dictionary = timeline[index]
		var sound_now: bool = card.update()
		if index == 0 and sound_now != bool(sound[0]):
			sound_ok = false
		if index > 0 and sound_now:
			sound_ok = false
		if not _tick_matches(card, row):
			drift = index
			break
	check.call(sound_ok, "Boss intro sound is requested on the first tick only")
	if drift >= 0:
		check.call(false, "Boss intro timeline drifted from source at tick %d" % (drift + 1))
		return
	check.call(true, "Boss intro replays %d source ticks exactly" % timeline.size())
	check.call(not card.is_active(), "Boss intro retires when the timer runs out")


func _tick_matches(card, row: Dictionary) -> bool:
	if card.timer != int(row["timer"]) or card.is_active() != bool(row["active"]):
		return false
	if not card.is_active():
		return true
	return _visual_matches(card, row)


func _visual_matches(card, row: Dictionary) -> bool:
	var tag: Dictionary = card.get_tag()
	var banner_ok: bool = (
		card.get_slide_offset() == int(row["x_offset"])
		and card.get_banner_x() == int(row["banner_x"])
		and card.get_banner_y() == int(row["banner_y"])
		and card.get_banner_width() == int(row["banner_w"])
	)
	var fade_ok: bool = (
		card.get_alpha() == int(row["alpha"])
		and card.get_background_alpha() == int(row["bg_alpha"])
		and card.get_border_alpha() == int(row["border_alpha"])
	)
	var bar_ok: bool = (
		card.get_hp_fill_width() == int(row["fill"])
		and card.get_hp_bar_rect() == _ints(row["hp_bar"])
		and card.get_entrance_color() == _ints(row["border_rgb"])
	)
	var tag_ok: bool = (
		String(tag["text"]) == String(row["tag_text"]) and tag["color"] == _ints(row["tag_color"])
	)
	return banner_ok and fade_ok and bar_ok and tag_ok


func _check_skips(check: Callable, data: Dictionary) -> void:
	var skips: Array = data["skips"]
	var all_ok := true
	for row in skips:
		var entry: Array = row
		var card := BossIntroCinematic.new()
		card.setup(data["timeline_boss_snapshot"], 1280, 720)
		for _tick in range(50):
			card.update()
		var name := String(entry[0])
		var result := false
		if name == "inactive":
			card.active = false
			result = card.handle_skip(KEY_SPACE)
		elif name == "click":
			result = card.handle_skip(-1, true)
		else:
			result = card.handle_skip(KEY_BY_NAME[name])
		if result != bool(entry[1]) or card.is_active() != bool(entry[2]):
			all_ok = false
	check.call(
		all_ok, "Boss intro skip inputs match source (space, escape, click, other key, inactive)"
	)


func _check_bosses(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["bosses"]
	var failures := 0
	var first_failure := ""
	var sample_count := 0
	for raw in rows:
		var entry: Dictionary = raw
		var card := BossIntroCinematic.new()
		card.setup(entry["boss"], 1280, 720)
		var samples: Array = entry["samples"]
		var next_sample := 0
		for tick in range(1, int(data["duration"]) + 1):
			card.update()
			if next_sample >= samples.size():
				break
			var sample: Array = samples[next_sample]
			if int(sample[0]) != tick:
				continue
			next_sample += 1
			sample_count += 1
			if not _sample_matches(card, sample):
				failures += 1
				if first_failure == "":
					first_failure = String(entry["key"]) + " @ tick %d" % tick
				break
	if failures > 0:
		check.call(false, "Boss intro drifted in %d bosses, first %s" % [failures, first_failure])
		return
	check.call(
		true, "Boss intro matches source for %d bosses (%d samples)" % [rows.size(), sample_count]
	)


func _sample_matches(card, sample: Array) -> bool:
	if card.timer != int(sample[1]):
		return false
	return (
		card.get_alpha() == int(sample[2])
		and card.get_slide_offset() == int(sample[3])
		and card.get_banner_x() == int(sample[4])
		and card.get_background_alpha() == int(sample[5])
		and card.get_hp_fill_width() == int(sample[6])
	)


func _check_literals(check: Callable) -> void:
	var card := BossIntroCinematic.new()
	card.setup({"name": "Literal", "title": "Test", "boss_class": "mini"}, 1280, 720)
	check.call(card.get_tag()["text"] == "MINI BOSS", "Mini boss tag reads MINI BOSS")
	check.call(card.get_banner_width() == 600, "Banner is capped at 600 px")
	check.call(card.get_slide_offset() == -640, "Slide starts 640 px to the left")
	var narrow := BossIntroCinematic.new()
	narrow.setup({"name": "Narrow", "title": "Test"}, 500, 300)
	check.call(narrow.get_banner_width() == 460, "Banner shrinks to fit a narrow screen")
	check.call(narrow.get_tag()["text"] == "TRUE BOSS", "Boss class defaults to TRUE BOSS")


func _check_runtime_wiring(check: Callable) -> void:
	var world := Prototype.new()
	world.setup_arena()
	check.call(
		world.boss_intro == null and not bool(world.boss_intro_state().get("active", true)),
		"Prototype starts without an active boss intro cinematic"
	)
	var mini := world._spawn_boss("gornak")
	check.call(
		(
			mini != null
			and world.boss_intro != null
			and world.boss_intro.is_active()
			and world.boss_intro.boss_name == mini.display_name
			and world.boss_intro.boss_class == "mini"
			and String(world.boss_intro_state().get("tag", {}).get("text", "")) == "MINI BOSS"
		),
		"Spawning a mini-boss configures BossIntroCinematic on Prototype"
	)
	world.step_tick()
	var session := PrototypeSession.new()
	session.world = world
	var view := PrototypeView.new()
	view.session = session
	check.call(
		(
			world.boss_intro.timer == BossIntroCinematic.DURATION - 1
			and world.boss_intro.sound_played
			and int(world.boss_intro_state().get("elapsed", 0)) == 1
			and int(view.overlay_draw_summary().get("boss_intro_border_alpha", 0)) > 0
			and not String(world.boss_intro_state().get("boss_title", "")).is_empty()
		),
		"Prototype.step_tick advances BossIntroCinematic and arms first-tick sound and border alpha"
	)
	view.free()
	session.free()
	check.call(
		world.skip_boss_intro(KEY_SPACE) and not world.boss_intro.is_active(),
		"Prototype.skip_boss_intro ends the active boss intro cinematic"
	)
	world.active_boss = null
	var true_boss := world._spawn_boss("abaddon")
	check.call(
		(
			true_boss != null
			and world.boss_intro != null
			and world.boss_intro.is_active()
			and world.boss_intro.boss_class == "true"
			and String(world.boss_intro_state().get("tag", {}).get("text", "")) == "TRUE BOSS"
		),
		"Spawning a true boss reconfigures BossIntroCinematic with TRUE BOSS tag"
	)
	check.call(
		world.skip_boss_intro(-1, true) and not bool(world.boss_intro_state().get("active", true)),
		"Prototype.skip_boss_intro supports click dismissal"
	)


func _ints(value: Variant) -> Array:
	var source: Array = value
	var out: Array = []
	for item in source:
		out.append(int(item))
	return out
