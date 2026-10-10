extends RefCounted
## Replays the `_render.py::LevelIntroScreen` source oracle fixture through
## the native port. `level_intro_screen_source_oracle.py` runs the real class
## headless (pygame/mobile.perf/_core shims) and reads the draw-time locals
## with `settrace`, so the fade ramp, theme tints, difficulty branches and
## fallback numbers are the source's, not re-implementations.

const LevelIntroScreen = preload("res://scripts/ui/level_intro_screen.gd")
const FIXTURE := "res://tests/fixtures/level_intro_screen_source.json"

const ACTIVE := 0
const TIMER := 1
const FADE := 2
const TINT_ALPHA := 3


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Level intro fixture parses")
	if not (data is Dictionary):
		return

	var info: Dictionary = data["info"]
	var boss_data: Dictionary = {
		"name": str(info["boss_name"]),
		"title": str(info["boss_title"]),
		"color": info["boss_color"],
		"color_dark": info["boss_color_dark"],
		"entrance_color": info["boss_entrance_color"],
		"boss_class": str(info["boss_class"]),
	}
	var intro := _spawn(data, boss_data)
	check.call(
		intro.fade_in_duration == int(info["fade_in_duration"]),
		"Fade-in duration matches the source (30 ticks)"
	)
	check.call(
		_intro_matches_info(intro, info), "Cached level and boss info match the source cache"
	)
	check.call(intro.sound_requests.is_empty(), "No sound before the first update")

	_replay_steps(check, data, intro)
	_replay_skip(check, data)
	_replay_layout(check, data, boss_data)
	_replay_difficulty(check, data, boss_data)
	_replay_themes(check, data)


func _spawn(data: Dictionary, boss_data: Dictionary) -> LevelIntroScreen:
	var config: Dictionary = data["level_config"]
	return LevelIntroScreen.new(config, int(data["screen_w"]), int(data["screen_h"]), boss_data)


func _intro_matches_info(intro: LevelIntroScreen, info: Dictionary) -> bool:
	return (
		intro.level_num == int(info["level_num"])
		and intro.level_name == str(info["level_name"])
		and intro.level_desc == str(info["level_desc"])
		and is_equal_approx(intro.hp_mult, float(info["hp_mult"]))
		and is_equal_approx(intro.dmg_mult, float(info["dmg_mult"]))
		and intro.reward == int(info["reward"])
		and intro.map_theme == str(info["map_theme"])
		and intro.boss_type == str(info["boss_type"])
		and intro.boss_name == str(info["boss_name"])
		and intro.boss_title == str(info["boss_title"])
		and _rgb_eq(intro.boss_color, info["boss_color"])
		and _rgb_eq(intro.boss_color_dark, info["boss_color_dark"])
		and _rgb_eq(intro.boss_entrance_color, info["boss_entrance_color"])
		and intro.boss_class == str(info["boss_class"])
	)


func _replay_steps(check: Callable, data: Dictionary, intro: LevelIntroScreen) -> void:
	var steps: Array = data["steps"]
	check.call(steps.size() == 42, "Source fixture keeps 40 live ticks + 2 idle ticks")

	for index in range(steps.size()):
		var expected: Array = steps[index]
		if int(expected[ACTIVE]) == 0 and intro.active:
			# The oracle skipped with spacebar right here (end of tick 40).
			if not intro.handle_skip(intro.KEY_SPACE):
				check.call(false, "Level intro spacebar skip rejected at step %d" % index)
				return
		intro.update()
		if int(expected[ACTIVE]) == 0:
			if intro.active or intro.timer != int(expected[TIMER]):
				check.call(false, "Level intro step %d should be idle" % index)
				return
			check.call(
				not intro.is_prompt_visible(),
				"Skipped intro never shows the prompt (step %d)" % index
			)
			continue
		if not intro.active or intro.timer != int(expected[TIMER]):
			check.call(false, "Level intro step %d drifted on the timer" % index)
			return
		if intro.get_fade_alpha() != int(expected[FADE]):
			check.call(false, "Level intro fade drifted at step %d" % index)
			return
		if intro.get_theme_tint_alpha() != int(expected[TINT_ALPHA]):
			check.call(false, "Level intro tint alpha drifted at step %d" % index)
			return
		if intro.get_darken_alpha() != mini(255, int(expected[FADE]) + 30):
			check.call(false, "Level intro darken alpha drifted at step %d" % index)
			return

	check.call(true, "Level intro replays %d source ticks exactly" % steps.size())
	check.call(intro.get_fade_alpha() == 255, "Fade saturates at exactly 255 once the ramp is done")
	check.call(intro.is_prompt_visible(), "Prompt appears once the fade-in is done")


func _replay_skip(check: Callable, data: Dictionary) -> void:
	var probes: Array = data["skip"]
	check.call(probes.size() == 7, "Source fixture keeps 7 skip probes")
	for probe in probes:
		var label := str(probe[0])
		var intro := _spawn(data, {})
		var returned := false
		match label:
			"space":
				returned = intro.handle_skip(intro.KEY_SPACE)
			"return":
				returned = intro.handle_skip(intro.KEY_RETURN)
			"other_key":
				returned = intro.handle_skip(999)
			"click":
				returned = intro.handle_skip(-1, true)
			"no_args":
				returned = intro.handle_skip()
			"inactive_guard":
				intro.handle_skip(intro.KEY_SPACE)
				returned = intro.handle_skip(intro.KEY_SPACE)
			"returned_by_main_skip":
				returned = intro.handle_skip(intro.KEY_SPACE)
		if returned != bool(probe[1]) or intro.is_active() != bool(probe[2]):
			check.call(false, "Skip probe '%s' drifted from the source" % label)
			return
	check.call(true, "Skip matrix replays the source exactly")


func _replay_layout(check: Callable, data: Dictionary, boss_data: Dictionary) -> void:
	var layout: Dictionary = data["layout"]
	var intro := _spawn(data, boss_data)
	for _tick in range(100):
		intro.update()

	check.call(intro.divider_x() == int(layout["divider_x"]), "Divider x matches the source")
	check.call(intro.level_cx() == int(layout["level_cx"]), "Level column cx matches the source")
	check.call(intro.boss_cx() == int(layout["boss_cx"]), "Boss column cx matches the source")
	check.call(
		intro.get_crown_spike_count() == int(layout["crown_spikes"]),
		"Crown spike count matches the source"
	)

	var tag: Dictionary = intro.get_boss_tag()
	var expected_tag: Array = layout["tag"]
	if str(tag["text"]) != str(expected_tag[0]) or not _rgb_eq(tag["color"], expected_tag[1]):
		check.call(false, "Boss tag drifted from the source")
		return

	var diamonds: Array = layout["diamonds"]
	for index in range(diamonds.size()):
		var expected: Array = diamonds[index]
		if intro.divider_x() != int(expected[0]) or intro.get_diamond_y(index) != int(expected[1]):
			check.call(false, "Diamond %d drifted from the source" % index)
			return
	check.call(diamonds.size() == 3, "Three divider diamonds at y 250/450/650")

	var spikes := int(layout["crown_spikes"])
	for index in range(spikes):
		var expected_x := intro.get_crown_spike_x(index, intro.boss_cx())
		var source_x := intro.boss_cx() - 40 + index * 20
		if expected_x != source_x:
			check.call(false, "Crown spike %d drifted from the source" % index)
			return
	check.call(true, "Layout replays the source exactly")


func _replay_difficulty(check: Callable, data: Dictionary, boss_data: Dictionary) -> void:
	var difficulties: Dictionary = data["difficulty"]
	for key in difficulties:
		var expected: Dictionary = difficulties[key]
		var intro := _spawn(data, boss_data)
		intro.difficulty = str(key)

		var info := intro.get_difficulty_info()
		if (
			str(info["title"]) != str(expected["title"])
			or int(info["level"]) != int(expected["level"])
			or not _rgb_eq(info["color"], expected["color"])
		):
			check.call(false, "Difficulty %s info drifted from the source" % key)
			return

		var bars: Array = expected["bars"]
		for bar in bars:
			var index := int(bar[0])
			if (
				intro.get_bar_x(index) != int(bar[1])
				or intro.get_bar_y() != int(bar[2])
				or not _rgb_eq(intro.get_bar_color(index), bar[3])
			):
				check.call(false, "Difficulty %s bar %d drifted" % [key, index])
				return

		if intro.get_starting_gold() != int(expected["starting_gold"]):
			check.call(false, "Difficulty %s starting gold drifted" % key)
			return
		if intro.get_passive_label() != str(expected["income"]):
			check.call(false, "Difficulty %s income label drifted" % key)
			return
	check.call(true, "Difficulty branches replay the source exactly")


func _replay_themes(check: Callable, data: Dictionary) -> void:
	var themes: Dictionary = data["themes"]
	for key in themes:
		var expected: Array = themes[key]
		var config: Dictionary = data["level_config"]
		config["map_theme"] = str(key)
		var intro := LevelIntroScreen.new(config, int(data["screen_w"]), int(data["screen_h"]), {})
		for _tick in range(100):
			intro.update()
		var tint := intro.get_theme_tint()
		if not _rgb_eq(tint, expected) or intro.get_theme_tint_alpha() != int(expected[3]):
			check.call(false, "Theme tint %s drifted from the source" % key)
			return
	check.call(themes.size() == 35, "All 34 source themes + forest fallback locked")
	check.call(true, "Theme tints replay the source exactly")


func _rgb_eq(color: Color, expected: Variant) -> bool:
	if not (expected is Array) or expected.size() < 3:
		return false
	return (
		color.r8 == int(expected[0])
		and color.g8 == int(expected[1])
		and color.b8 == int(expected[2])
	)
