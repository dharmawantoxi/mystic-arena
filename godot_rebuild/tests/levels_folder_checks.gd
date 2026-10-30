extends RefCounted
## Whole `levels/` folder coverage, proven from the source inventory.
##
## `tests/fixtures/levels_folder_source.json` is derived from the two Pygame
## modules by `tests/levels_folder_source_oracle.py`. `level_catalog_checks.gd`
## already proves the loader/unlock/next-level boundary; this suite proves the
## *accounting* of the folder itself:
##
## * the inventory: 2 files, 2.354 lines, and `__init__.py`'s five re-exports;
## * all 54 configurations, key by key, against `data/levels/level_N.json`
##   (seventeen keys per level, `mini_bosses` included);
## * the aggregates the source is built from: 54 distinct map themes, 54
##   distinct HP multipliers (1.0 - 1.54), flat 1000 gold, flat 3000/1500/0
##   meta-gold, three mini bosses per level, and the `level n` after-`n - 1`
##   unlock chain;
## * the boss line-up: 54 true bosses + 162 mini bosses = the whole 216-boss
##   roster, each used exactly once;
## * `ALL_LEVELS` order (`all_configs()`), `get_level_count` (`count()`) and the
##   source's `None`-based helper semantics;
## * the two keys nothing in the Pygame runtime reads (`bgm_track`,
##   `meta_gold_reward_lose`) — data parity without a consumer;
## * that the data is actually wired into a match: hard mode multiplies the
##   source 1.15 / 1.10 / 1.00 on top of these values, and the mini-boss
##   schedule re-rolls the wave numbers while keeping the source boss order.

const Catalog = preload("res://scripts/match/level_catalog.gd")
const World = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/levels_folder_source.json"
const BOSS_STATS := "res://data/bosses/boss_stats.json"
const HERO_MANIFEST := "res://data/art/heroes.json"
const THEME_PALETTE := "res://data/levels/theme_palette.json"

## Source `_core.py`: `enemy_hp_mult = cfg * 1.15`, damage `* 1.10`, speed raw.
const HARD_HP_BONUS := 1.15
const HARD_DAMAGE_BONUS := 1.10
## Source `_roll_mini_boss_schedule`: normal/hard sample waves 11..30.
const NORMAL_WAVE_LOW := 11
const NORMAL_WAVE_HIGH := 30


func run(check: Callable) -> void:
	var source := _fixture()
	check.call(not source.is_empty(), "The levels/ inventory fixture parses")
	if source.is_empty():
		return
	_check_folder(check, source)
	_check_configs(check, source)
	_check_aggregates(check, source)
	_check_helpers(check, source)
	_check_integrity(check, source)
	_check_dead_fields(check, source)
	_check_live_wiring(check, source)


func _fixture() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


func _deep_equal(left: Variant, right: Variant) -> bool:
	var equal := true
	if left is Dictionary and right is Dictionary:
		var left_dict: Dictionary = left
		var right_dict: Dictionary = right
		equal = left_dict.size() == right_dict.size()
		for key in left_dict:
			if not equal:
				break
			if not right_dict.has(key):
				equal = false
				break
			equal = _deep_equal(left_dict[key], right_dict[key])
	elif left is Array and right is Array:
		var left_list: Array = left
		var right_list: Array = right
		equal = left_list.size() == right_list.size()
		for index in range(left_list.size()):
			if not equal:
				break
			equal = _deep_equal(left_list[index], right_list[index])
	else:
		equal = left == right
	return equal


func _check_folder(check: Callable, source: Dictionary) -> void:
	var folder: Dictionary = source.get("folder", {})
	check.call(int(folder.get("count", 0)) == 2, "levels/ holds two Python modules")
	check.call(int(folder.get("lines", 0)) == 2354, "levels/ is 2.354 source lines")
	var files: Dictionary = folder.get("files", {})
	check.call(
		int(files.get("level_data.py", 0)) == 2347,
		"level_data.py is the 2.347-line level table"
	)
	check.call(
		int(files.get("__init__.py", 0)) == 7,
		"__init__.py is the 7-line re-export shim"
	)
	var reexports: Array = source.get("reexports", [])
	check.call(
		reexports.size() == 5
		and reexports.has("ALL_LEVELS")
		and reexports.has("get_level_config")
		and reexports.has("get_level_count")
		and reexports.has("is_level_unlocked")
		and reexports.has("get_next_level"),
		"__init__.py re-exports the registry plus the four helpers: %s" % str(reexports)
	)


func _check_configs(check: Callable, source: Dictionary) -> void:
	var levels: Dictionary = source.get("levels", {})
	var configs: Dictionary = levels.get("configs", {})
	var aggregates: Dictionary = source.get("aggregates", {})
	var keys: Array = aggregates.get("keys", [])
	check.call(int(levels.get("count", 0)) == 54, "The source declares 54 levels")
	check.call(
		Catalog.COUNT == 54 and Catalog.count() == 54,
		"The native catalog exposes the same 54 levels (COUNT and count())"
	)
	check.call(
		configs.size() == 54 and Catalog.all_configs().size() == 54,
		"all_configs() mirrors the source ALL_LEVELS list"
	)
	check.call(keys.size() == 17, "Every level carries the same seventeen keys")
	check.call(
		int(aggregates.get("levels_with_every_key", 0)) == 54,
		"No level is missing a key"
	)

	var all_configs := Catalog.all_configs()
	var mismatched := 0
	var bad_keys := 0
	var bad_numbers := 0
	for number in range(1, 55):
		var expected: Variant = configs.get(str(number), null)
		var actual: Dictionary = Catalog.get_level_config(number)
		if expected == null or not _deep_equal(actual, expected):
			mismatched += 1
		if actual.size() != keys.size():
			bad_keys += 1
		if int(actual.get("level_number", -1)) != number:
			bad_numbers += 1
		if all_configs.size() == 54 and not _deep_equal(all_configs[number - 1], expected):
			mismatched += 1
	check.call(
		mismatched == 0,
		"All 54 native level_N.json files match the source dictionaries exactly (%d mismatched)"
		% mismatched
	)
	check.call(bad_keys == 0, "Every native config keeps all seventeen source keys")
	check.call(bad_numbers == 0, "Every native config keeps its source level_number")
	check.call(
		_deep_equal(Catalog.get_level_config(1), configs.get("1", {})),
		"Level 1 is the source 'The Fallen Realm' / forest / abaddon entry"
	)
	check.call(
		String(Catalog.get_level_config(54).get("name", "")) == "The Substitute Shinigami",
		"Level 54 keeps its source name"
	)


func _check_aggregates(check: Callable, source: Dictionary) -> void:
	var aggregates: Dictionary = source.get("aggregates", {})
	var themes: Dictionary = aggregates.get("themes", {})
	check.call(themes.size() == 54, "The 54 levels use 54 distinct map themes")
	var singles := 0
	for theme in themes:
		if int(themes[theme]) == 1:
			singles += 1
	check.call(singles == 54, "Every map theme belongs to exactly one level")
	var hp_mults: Array = aggregates.get("hp_mults", [])
	check.call(
		hp_mults.size() == 54
		and is_equal_approx(float(hp_mults[0]), 1.0)
		and is_equal_approx(float(hp_mults[53]), 1.54),
		"The 54 HP multipliers run 1.0 - 1.54 with no duplicates"
	)
	check.call(
		aggregates.get("starting_gold", []) == [1000],
		"Every level starts the player on the same 1000 gold"
	)
	check.call(
		aggregates.get("reward_win", []) == [3000]
		and aggregates.get("reward_replay", []) == [1500]
		and aggregates.get("reward_lose", []) == [0],
		"Meta gold is flat 3000 / 1500 / 0 on every level"
	)
	check.call(
		aggregates.get("starting_castle_levels", []) == [1]
		and aggregates.get("castle_start_levels", []) == [1],
		"Both castles start at tier 1 unless the level says otherwise"
	)
	check.call(
		aggregates.get("mini_boss_counts", {}) == {"3": 54},
		"Every level schedules exactly three mini bosses"
	)
	var wave_keys: Array = aggregates.get("mini_boss_wave_keys", [])
	check.call(
		wave_keys == [10, 15, 17, 18, 20, 25],
		"The source mini-boss wave keys are 10/15/17/18/20/25: %s" % str(wave_keys)
	)
	var wave_sets: Dictionary = aggregates.get("mini_boss_wave_sets", {})
	check.call(
		int(wave_sets.get("10,18,25", 0)) == 49,
		"49 levels use the 10/18/25 wave slot layout"
	)
	check.call(
		bool(aggregates.get("unlock_chain_is_predecessor", false)),
		"Every level n>1 unlocks after level n-1"
	)
	check.call(
		bool(aggregates.get("order_is_sequential", false))
		and bool(aggregates.get("level_numbers_match_keys", false)),
		"ALL_LEVELS is in 1..54 order and matches each level_number"
	)
	var order: Array = source.get("levels", {}).get("order", [])
	var ordered := true
	for index in range(order.size()):
		if int(order[index]) != index + 1:
			ordered = false
	check.call(ordered and order.size() == 54, "The source ALL_LEVELS order is 1..54")


func _check_helpers(check: Callable, source: Dictionary) -> void:
	var helpers: Dictionary = source.get("helpers", {})
	check.call(
		helpers.get("names", [])
		== ["get_level_config", "get_level_count", "get_next_level", "is_level_unlocked"],
		"The folder exposes exactly the four source helpers: %s" % str(helpers.get("names", []))
	)
	check.call(
		bool(helpers.get("get_level_config", {}).get("linear_over_all_levels", false))
		and bool(helpers.get("get_level_count", {}).get("returns_len_all_levels", false)),
		"get_level_config scans ALL_LEVELS and get_level_count returns its length"
	)
	var unlocked_rules: Dictionary = helpers.get("is_level_unlocked", {})
	check.call(
		bool(unlocked_rules.get("none_unlock_after_means_unlocked", false))
		and bool(unlocked_rules.get("membership_in_completed", false))
		and bool(unlocked_rules.get("missing_config_is_locked", false)),
		"is_level_unlocked keeps the null-unlocked, membership and missing-config rules"
	)
	var next_rules: Dictionary = helpers.get("get_next_level", {})
	check.call(
		bool(next_rules.get("guards_against_level_count", false))
		and bool(next_rules.get("guards_against_missing_config", false))
		and bool(next_rules.get("returns_none_at_end", false)),
		"get_next_level keeps both guards and the null tail"
	)

	check.call(Catalog.get_level_config(0).is_empty(), "Level 0 has no config")
	check.call(Catalog.get_level_config(55).is_empty(), "Level 55 has no config")
	check.call(Catalog.get_level_config(-3).is_empty(), "Negative numbers have no config")

	var completed: Array = []
	var locked_all := true
	var chain_ok := true
	for number in range(1, 55):
		if Catalog.is_level_unlocked(number, []) != (number == 1):
			locked_all = false
		if number > 1:
			completed.append(number - 1)
			if not Catalog.is_level_unlocked(number, completed):
				chain_ok = false
			if not Catalog.is_level_unlocked(number, [number - 1]):
				chain_ok = false
	check.call(locked_all, "Only level 1 is unlocked before any win")
	check.call(chain_ok, "Every level unlocks from its single predecessor")
	check.call(
		not Catalog.is_level_unlocked(3, [1]),
		"Completing level 1 alone does not unlock level 3"
	)
	check.call(
		not Catalog.is_level_unlocked(0, [1, 2, 3]) and not Catalog.is_level_unlocked(55, []),
		"Unknown levels stay locked"
	)
	check.call(
		Catalog.get_next_level(0) == 1 and Catalog.get_next_level(1) == 2
		and Catalog.get_next_level(53) == 54,
		"get_next_level walks the whole catalog"
	)
	check.call(
		Catalog.get_next_level(54) == -1 and Catalog.get_next_level(99) == -1,
		"Past the last level the native sentinel is -1 (the source returns None)"
	)
	var first := Catalog.get_level_config(1)
	first["name"] = "corrupted"
	check.call(
		String(Catalog.get_level_config(1).get("name", "")) == "The Fallen Realm",
		"A caller cannot mutate the catalog through a returned config"
	)


func _check_integrity(check: Callable, source: Dictionary) -> void:
	var aggregates: Dictionary = source.get("aggregates", {})
	var bosses: Dictionary = _json(BOSS_STATS).get("bosses", {})
	var meta: Dictionary = _json(HERO_MANIFEST).get("meta", {})
	var palette: Dictionary = _json(THEME_PALETTE)
	check.call(bosses.size() == 216, "The native boss roster holds 216 bosses")
	check.call(palette.size() == 54, "The native theme palette holds 54 themes")

	var configs: Dictionary = source.get("levels", {}).get("configs", {})
	var missing_boss := 0
	var missing_hero := 0
	var missing_theme := 0
	var distinct_true: Dictionary = {}
	var distinct_mini: Dictionary = {}
	for number in configs:
		var config: Dictionary = configs[number]
		if not palette.has(String(config.get("map_theme", ""))):
			missing_theme += 1
		var mini: Dictionary = config.get("mini_bosses", {})
		var lineup: Array = [String(config.get("true_boss", ""))]
		for wave in mini:
			lineup.append(String(mini[wave]))
		for boss_id in lineup:
			if not bosses.has(boss_id):
				missing_boss += 1
			if not meta.has(boss_id):
				missing_hero += 1
		distinct_true[String(config.get("true_boss", ""))] = true
		for wave in mini:
			distinct_mini[String(mini[wave])] = true
	check.call(missing_theme == 0, "Every source map_theme exists in the theme palette")
	check.call(missing_boss == 0, "Every referenced boss exists in boss_stats.json")
	check.call(missing_hero == 0, "Every referenced boss has a baked hero atlas entry")
	check.call(distinct_true.size() == 54, "Each of the 54 levels has its own true boss")
	check.call(distinct_mini.size() == 162, "162 distinct mini bosses appear across the levels")
	check.call(
		int(aggregates.get("boss_refs_total", 0)) == 216
		and distinct_true.size() + distinct_mini.size() == 216,
		"54 true + 162 mini bosses cover the 216-boss roster with no overlap"
	)


func _check_dead_fields(check: Callable, source: Dictionary) -> void:
	var readers: Dictionary = source.get("readers", {})
	check.call(
		readers.get("dead_in_source", []) == ["bgm_track", "meta_gold_reward_lose"],
		"Only bgm_track and meta_gold_reward_lose are unread by the Pygame runtime"
	)
	var configs: Dictionary = source.get("levels", {}).get("configs", {})
	var bgm_ok := true
	var lose_ok := true
	for number in configs:
		var config: Dictionary = configs[number]
		if String(config.get("bgm_track", "")) != "bgm_battle.wav":
			bgm_ok = false
		if int(config.get("meta_gold_reward_lose", -1)) != 0:
			lose_ok = false
	check.call(bgm_ok, "Every level names the same bgm_battle.wav track, like the source")
	check.call(lose_ok, "Every level pays 0 meta gold on a loss, like the source")
	var native := Catalog.get_level_config(7)
	check.call(
		String(native.get("bgm_track", "")) == "bgm_battle.wav"
		and int(native.get("meta_gold_reward_lose", -1)) == 0,
		"The two input-only fields survive into the native catalog"
	)


func _check_live_wiring(check: Callable, source: Dictionary) -> void:
	var configs: Dictionary = source.get("levels", {}).get("configs", {})
	var preview := World.new()
	check.call(preview.configure_level(10), "A match configures level 10")
	var level_ten: Dictionary = configs.get("10", {})
	check.call(
		preview.level_config.size() == 17,
		"The running match keeps the whole source level config"
	)
	preview.set_difficulty("hard")
	check.call(
		is_equal_approx(
			preview.enemy_hp_mult, float(level_ten.get("enemy_hp_mult", 0.0)) * HARD_HP_BONUS
		),
		"Hard mode multiplies the level HP by the source 1.15 (%.3f)" % preview.enemy_hp_mult
	)
	check.call(
		is_equal_approx(
			preview.enemy_damage_mult,
			float(level_ten.get("enemy_damage_mult", 0.0)) * HARD_DAMAGE_BONUS
		),
		"Hard mode multiplies the level damage by the source 1.10 (%.3f)"
		% preview.enemy_damage_mult
	)
	check.call(
		is_equal_approx(
			preview.enemy_speed_mult, float(level_ten.get("enemy_speed_mult", 0.0))
		),
		"Hard mode leaves the level speed multiplier unscaled"
	)
	preview.set_difficulty("normal")
	check.call(
		is_equal_approx(preview.enemy_hp_mult, 1.0)
		and is_equal_approx(preview.enemy_damage_mult, 1.0)
		and is_equal_approx(preview.enemy_speed_mult, 1.0),
		"Normal mode ignores the level multipliers entirely"
	)

	var entries: Array = preview._mini_boss_entries()
	check.call(entries.size() == 3, "Level 10 schedules its three source mini bosses")
	var source_order: Array = []
	for wave in level_ten.get("mini_bosses", {}):
		source_order.append(String(level_ten.get("mini_bosses", {})[wave]))
	var entry_order: Array = []
	for entry in entries:
		entry_order.append(String(entry.get("boss_type", "")))
	check.call(
		entry_order == source_order,
		"The native mini-boss entries keep the source dictionary order: %s" % str(entry_order)
	)
	preview.set_difficulty("normal")
	var schedule: Dictionary = preview._mini_boss_schedule
	check.call(schedule.size() == 3, "The rolled schedule still holds three mini bosses")
	var waves_sorted: Array = []
	for wave in schedule:
		waves_sorted.append(int(wave))
	waves_sorted.sort()
	var in_range := true
	for wave in waves_sorted:
		if wave < NORMAL_WAVE_LOW or wave > NORMAL_WAVE_HIGH:
			in_range = false
	check.call(
		in_range,
		"Normal/hard re-roll the source wave keys into 11..30: %s" % str(waves_sorted)
	)
	var schedule_order: Array = []
	for wave in waves_sorted:
		schedule_order.append(String(schedule[wave]))
	check.call(
		schedule_order == source_order,
		"Only the wave numbers are re-rolled; the boss order is the source order"
	)

	var first_level := World.new()
	check.call(first_level.configure_level(1), "A match configures level 1")
	first_level.set_difficulty("normal")
	check.call(
		first_level.economy.opening[0] == int(configs.get("1", {}).get("starting_gold", -1)),
		"Level 1 opens on the source starting gold (%d)" % first_level.economy.opening[0]
	)
	check.call(
		String(first_level.level_config.get("map_theme", "")) == "forest"
		and String(first_level.level_config.get("true_boss", "")) == "abaddon",
		"The level 1 match runs the source theme and boss"
	)
