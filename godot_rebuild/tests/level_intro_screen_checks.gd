extends RefCounted
## Replays the `_render.py::LevelIntroScreen` source oracle fixture through the
## native port. `level_intro_screen_source_oracle.py` runs the real `draw()`
## under a pygame / font shim and reads the fade curve, the theme tint, the
## difficulty bars and the gold / passive / boss-tag / prompt text off the
## frame with `settrace`, so the numbers here are the source's, not a copy.

const LevelIntroScreen = preload("res://scripts/ui/level_intro_screen.gd")
const FIXTURE := "res://tests/fixtures/level_intro_screen_source.json"

const KEY_BY_NAME := {"space": KEY_SPACE, "return": KEY_ENTER, "letter_a": KEY_A}


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Level intro fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed

	_check_constants(check, data)
	_check_setup(check, data)
	_check_timeline(check, data)
	_check_skips(check, data)
	_check_difficulty(check, data)
	_check_themes(check, data)
	_check_literals(check)


func _check_constants(check: Callable, data: Dictionary) -> void:
	var fade_duration: int = int(data["fade_in_duration"])
	check.call(
		fade_duration == LevelIntroScreen.FADE_IN_DURATION, "Level intro fade-in matches source"
	)
	var gold_rate: int = int(data["gold_per_second"])
	check.call(
		gold_rate == LevelIntroScreen.GOLD_PER_SECOND, "Level intro passive rate matches source"
	)
	var prompt: String = String(data["begin_prompt"])
	check.call(prompt == LevelIntroScreen.PROMPT_TEXT, "Level intro prompt text matches source")


func _check_setup(check: Callable, data: Dictionary) -> void:
	var level: Dictionary = data["level"]
	var boss: Dictionary = data["boss_snapshot"]
	var card := LevelIntroScreen.new()
	card.setup(level, boss, 1280, 720)
	check.call(card.level_num == int(level["level_number"]), "Level intro reads level_number")
	check.call(card.level_name == String(level["name"]), "Level intro reads level name")
	check.call(card.map_theme == String(level["map_theme"]), "Level intro reads map theme")
	check.call(card.boss_name == String(boss["name"]), "Level intro reads boss name")
	check.call(card.boss_title == String(boss["title"]), "Level intro reads boss title")
	check.call(card.boss_class == String(boss["boss_class"]), "Level intro reads boss class")
	check.call(
		card.boss_entrance_color == _rgb(boss["entrance_color"]),
		"Level intro reads boss entrance colour"
	)
	check.call(
		card.boss_color_dark == _rgb(boss["color_dark"]), "Level intro reads boss dark colour"
	)
	check.call(card.is_active(), "Level intro starts active")

	var bare := LevelIntroScreen.new()
	bare.setup({"level_number": 9, "name": "Bare", "description": ""}, {}, 1280, 720)
	check.call(
		bare.boss_name == "Unknown" and bare.boss_title == "The Boss",
		"Missing boss falls back to source defaults"
	)
	check.call(bare.boss_class == "true", "Missing boss class defaults to true")
	check.call(bare.get_boss_tag()["text"] == "TRUE BOSS", "Default boss tag is TRUE BOSS")


func _check_timeline(check: Callable, data: Dictionary) -> void:
	var card := LevelIntroScreen.new()
	card.setup(data["level"], data["boss_snapshot"], 1280, 720)
	var sound: Array = data["sound_on_first_update"]
	var timeline: Array = data["timeline"]
	var sound_ok := true
	var drift := -1
	for index in range(timeline.size()):
		var step: Array = timeline[index]
		var sound_now := card.update()
		if index == 0 and sound_now != bool(sound[0]):
			sound_ok = false
		if index > 0 and sound_now:
			sound_ok = false
		if not _timeline_matches(card, step):
			drift = index
			break
	check.call(sound_ok, "Wave-start sound is requested on the first tick only")
	if drift >= 0:
		check.call(false, "Level intro timeline drifted from source at tick %d" % drift)
		return
	check.call(true, "Level intro replays %d source ticks exactly" % timeline.size())

	var end: Array = data["timeline_end"]
	card.update()
	var skipped := card.handle_skip(KEY_SPACE)
	check.call(skipped == bool(end[2]), "Space ends the intro after the fade")
	check.call(card.is_active() == bool(end[1]), "Intro is inactive after space")


func _timeline_matches(card, step: Array) -> bool:
	var same_clock: bool = card.timer == int(step[0]) and card.is_active() == bool(step[1])
	if not same_clock:
		return false
	if not card.is_active():
		return true
	var prompt_ok: bool = step[5] == null or card.get_begin_prompt() == String(step[5])
	return (
		card.get_fade_alpha() == int(step[2])
		and card.get_theme_tint_alpha() == int(step[3])
		and card.get_show_prompt() == bool(step[4])
		and prompt_ok
	)


func _check_skips(check: Callable, data: Dictionary) -> void:
	var skips: Array = data["skips"]
	var all_ok := true
	for row in skips:
		var entry: Array = row
		var name := String(entry[0])
		var card := LevelIntroScreen.new()
		card.setup(data["level"], data["boss_snapshot"], 1280, 720)
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
	check.call(all_ok, "Skip inputs match source (space, enter, click, other key, inactive)")


func _check_difficulty(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["difficulty_rows"]
	var failures := 0
	var first_failure := ""
	for raw in rows:
		var row: Dictionary = raw
		var card := LevelIntroScreen.new()
		card.setup(row["level"], row["boss"], 1280, 720)
		for _tick in range(40):
			card.update()
		var problem := _difficulty_problem(card, row)
		if problem != "":
			failures += 1
			if first_failure == "":
				first_failure = problem
	if failures > 0:
		check.call(false, "Difficulty card drifted in %d rows: %s" % [failures, first_failure])
		return
	check.call(true, "Difficulty card matches source for %d level/difficulty rows" % rows.size())


func _difficulty_problem(card, row: Dictionary) -> String:
	var label := "%s/%s" % [row["level"]["level_number"], row["difficulty_setting"]]
	if (
		card.get_fade_alpha() != int(row["fade_alpha"])
		or card.get_theme_tint_alpha() != int(row["tint_alpha"])
	):
		return label + " fade/tint"
	var info: Dictionary = card.get_difficulty_info(String(row["difficulty_setting"]))
	var want: Dictionary = row["difficulty"]
	if String(info["title"]) != String(want["title"]) or int(info["level"]) != int(want["level"]):
		return label + " difficulty title/level"
	if info["color"] != _rgb(want["color"]):
		return label + " difficulty colour"
	var bars: Array = row["bars"]
	for index in range(bars.size()):
		if card.get_bar_color(index, int(info["level"])) != _rgb(bars[index]):
			return label + " bar %d" % index
	return _text_problem(card, row, label)


func _text_problem(card, row: Dictionary, label: String) -> String:
	if card.get_starting_gold() != int(row["starting_gold"]):
		return label + " starting gold"
	if card.get_passive_text() != String(row["passive_text"]):
		return label + " passive text"
	var tag: Dictionary = card.get_boss_tag()
	var want_tag: Dictionary = row["boss_tag"]
	if String(tag["text"]) != String(want_tag["text"]) or tag["color"] != _rgb(want_tag["color"]):
		return label + " boss tag"
	if card.get_begin_prompt() != String(row["prompt_text"]):
		return label + " prompt"
	return ""


func _check_themes(check: Callable, data: Dictionary) -> void:
	var rows: Array = data["themes"]
	var failures := 0
	var first_failure := ""
	for raw in rows:
		var row: Array = raw
		var level: Dictionary = data["level"].duplicate()
		level["map_theme"] = String(row[0])
		var card := LevelIntroScreen.new()
		card.setup(level, data["boss_snapshot"], 1280, 720)
		for _tick in range(60):
			card.update()
		var want_rgba: Array = row[1]
		var got: Array = card.get_theme_tint_rgba()
		if got != [int(want_rgba[0]), int(want_rgba[1]), int(want_rgba[2]), int(want_rgba[3])]:
			failures += 1
			if first_failure == "":
				first_failure = String(row[0])
	if failures > 0:
		check.call(false, "Theme tint drifted from source for %s" % first_failure)
		return
	check.call(true, "Theme tint matches source for %d themes" % rows.size())


func _check_literals(check: Callable) -> void:
	var card := LevelIntroScreen.new()
	card.setup(
		{"level_number": 1, "name": "Literal", "description": "", "meta_gold_reward_win": 3000},
		{},
		1280,
		720
	)
	check.call(
		card.get_starting_gold_text() == "1,000 GOLD",
		"Starting gold text groups thousands with commas"
	)
	check.call(card.get_reward_text() == "+3000 HERO GOLD", "Reward text matches source f-string")
	check.call(card.get_begin_prompt(true) == "TAP TO BEGIN", "Touch mode uses the tap prompt")
	check.call(
		LevelIntroScreen._with_commas(1234567) == "1,234,567", "Thousands grouping handles millions"
	)
	check.call(
		LevelIntroScreen._with_commas(999) == "999", "Thousands grouping leaves short numbers alone"
	)


func _rgb(value: Variant) -> Array:
	var source: Array = value
	return [int(source[0]), int(source[1]), int(source[2])]
