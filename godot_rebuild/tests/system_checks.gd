extends RefCounted
## Layer 9ci: whole `_system.py` coverage — the five merged system modules.
##
## `_system.py` is 1.125 lines: `performance.py`, `fps_counter.py`, `fps_limiter.py`,
## `sound_manager.py` and `save_manager.py` merged behind a two-helper prelude. This
## layer proves the coverage instead of re-porting what the rebuild already carried:
##
## * the inventory (six sections, six classes, 47 `def`s, three module functions, four
##   module assigns) matches the source, and every one of the 66 symbols is classified
##   with a target file that really contains its token. Reachability is computed per
##   class from the public API and the constructor, so `FPSCounter` — the F8 overlay
##   that only `main_desktop_legacy.py` still draws — is `dead` instead of a silent
##   "ported";
## * `tests/system_source_oracle.py` imports the REAL module (stub `pygame` with a
##   recording mixer, `_core` settings namespace, a temporary `storage_paths.SAVE_DIR`
##   and a frozen clock) and this suite replays the numbers: the 80 px cull boundary,
##   the cell-60 grid query **order**, the throttle table with its 0.15 positional
##   floor, the 3-slot lifecycle with its `%d %b %Y` fallback, and the level-stats
##   transaction that only updates best score/time on a win;
## * two symbols are the only ones without a native counterpart: the older
##   `_system.py::AdaptiveQuality` (superseded by the active `mobile/perf.py` governor
##   the rebuild already ports) and `FPSCounter`. Both are named in the report.
##
## Sync: python3 godot_rebuild/tests/system_source_oracle.py --write

const FrustumCull = preload("res://scripts/ui/frustum_cull.gd")
const AudioFacade = preload("res://scripts/audio/audio_manager.gd")
const SaveSlots = preload("res://scripts/match/save_slot_store.gd")
const LevelStats = preload("res://scripts/match/level_stats.gd")
const FIXTURE := "res://tests/fixtures/system_source.json"

const TOTALS := {
	"lines": 1125,
	"sections": 6,
	"classes": 6,
	"methods": 47,
	"top_functions": 3,
	"assigns": 4,
}
const SECTION_NAMES := [
	"prelude",
	"performance",
	"fps_counter",
	"fps_limiter",
	"sound_manager",
	"save_manager",
]
const KINDS := {"data": 5, "dead": 8, "deviation": 2, "folded": 0, "ported": 51}
const SYMBOL_COUNT := 66
const TARGET_SOURCE_ONLY := ["dead", "deviation", "meta"]
const DEAD_SYMBOLS := [
	"class:FPSCounter",
	"class:FPSCounter.__init__",
	"class:FPSCounter.__new__",
	"class:FPSCounter._get_font",
	"class:FPSCounter.draw",
	"class:FPSCounter.toggle",
	"class:FPSCounter.update",
	"module:fps_counter",
]
const FROZEN_NOW := 1700000000.0


static func _json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


static func _target_text(path: String) -> String:
	if not path.begins_with("godot_rebuild/"):
		return ""
	var local: String = "res://" + path.trim_prefix("godot_rebuild/")
	if not FileAccess.file_exists(local):
		return ""
	return FileAccess.get_file_as_string(local)


func run(check: Callable) -> void:
	var data: Dictionary = _json(FIXTURE)
	check.call(not data.is_empty(), "_system fixture parses")
	if data.is_empty():
		return
	_check_inventory(check, data)
	_check_classification(check, data)
	_check_cull(check, data)
	_check_grid(check, data)
	_check_audio(check, data)
	_check_save(check, data)
	_check_stats(check, data)
	_check_dead(check, data)
	SpatialGrid.reset_shared()


## The file really is the five-module system bundle this layer claims.
func _check_inventory(check: Callable, data: Dictionary) -> void:
	var file: Dictionary = data["file"]
	for key in TOTALS:
		check.call(
			int(file.get(key, -1)) == TOTALS[key],
			"_system.py %s is %s (got %s)" % [key, TOTALS[key], str(file.get(key))]
		)
	check.call(String(file.get("file", "")) == "_system.py", "the oracle reads the source file")
	var sections: Array = data["sections"]
	check.call(sections.size() == 6, "the system bundle keeps its six sections")
	var names: Array = []
	for index in range(sections.size()):
		var row: Dictionary = sections[index]
		names.append(String(row["name"]))
		check.call(
			int(row["lines"]) == int(row["end"]) - int(row["start"]) + 1,
			"section %s spans its own range" % row["name"]
		)
		if index + 1 < sections.size():
			check.call(
				int(sections[index + 1]["start"]) == int(row["end"]) + 1,
				"sections stay contiguous after %s" % row["name"]
			)
	check.call(names == SECTION_NAMES, "the merged modules keep the source order")
	check.call(
		int(sections[0]["start"]) == 1 and int(sections[5]["end"]) == 1125,
		"the sections cover the whole file"
	)


## Every symbol of `_system.py` is classified and its target really has the token.
func _check_classification(check: Callable, data: Dictionary) -> void:
	var symbols: Dictionary = data["symbols"]
	check.call(
		int(symbols["count"]) == SYMBOL_COUNT,
		"%d symbols are classified (got %s)" % [SYMBOL_COUNT, str(symbols["count"])]
	)
	var kinds: Dictionary = symbols["kinds"]
	for kind in KINDS:
		check.call(
			int(kinds.get(kind, -1)) == KINDS[kind],
			"kind %s counts %s (got %s)" % [kind, KINDS[kind], str(kinds.get(kind))]
		)
	var rows: Dictionary = data["classification"]
	check.call(rows.size() == SYMBOL_COUNT, "every symbol has one classification row")
	var broken: Array = []
	var untargeted: Array = []
	for symbol in rows:
		var row: Dictionary = rows[symbol]
		var target := String(row["target"])
		var token := String(row["token"])
		if target.is_empty() or token.is_empty():
			if not TARGET_SOURCE_ONLY.has(String(row["kind"])):
				untargeted.append(symbol)
			continue
		if not _target_text(target).contains(token):
			broken.append(symbol)
	check.call(
		broken.is_empty(),
		"every classification token is present in its target (broken: %s)" % str(broken)
	)
	check.call(
		untargeted.is_empty(),
		"only dead/deviation/meta rows may skip a Godot target (%s)" % str(untargeted)
	)
	check.call(
		(data["dead_helpers"] as Array) == DEAD_SYMBOLS,
		"the legacy F8 overlay stays the only dead module"
	)
	check.call(
		data["duplicates"] is Dictionary and (data["duplicates"] as Dictionary).is_empty(),
		"_system.py has no duplicated symbol"
	)


## `FrustumCuller.is_visible`: the 80 px margin is inclusive on both edges.
func _check_cull(check: Callable, data: Dictionary) -> void:
	var cull: Dictionary = data["cull"]
	check.call(int(cull["margin"]) == FrustumCull.MARGIN, "the cull margin stays 80")
	check.call(
		int(cull["screen"][0]) == int(FrustumCull.SCREEN_SIZE.x)
		and int(cull["screen"][1]) == int(FrustumCull.SCREEN_SIZE.y),
		"the cull box stays the 1280x720 logical surface"
	)
	var mismatched: Array = []
	for row in cull["cases"]:
		var case: Dictionary = row
		var actual := FrustumCull.is_visible(
			float(case["x"]), float(case["y"]), float(case["radius"])
		)
		if actual != bool(case["visible"]):
			mismatched.append("%s,%s,%s" % [case["x"], case["y"], case["radius"]])
	check.call(
		mismatched.is_empty(),
		"the cull verdict matches pygame at every boundary (%s)" % str(mismatched)
	)
	check.call(
		FrustumCull.is_visible(-110.0, 0.0, 30.0) and not FrustumCull.is_visible(-110.1, 0.0, 30.0),
		"an entity exactly on the margin is still visible"
	)
	check.call(
		is_equal_approx(FrustumCull.cull_margin(30.0), 110.0)
		and is_equal_approx(FrustumCull.cull_margin(0.0), 80.0),
		"the margin adds the entity radius, like the source"
	)


## `SpatialGrid`: cell 60, one bucket per entity, and the exact query order.
func _check_grid(check: Callable, data: Dictionary) -> void:
	var grid_data: Dictionary = data["grid"]
	check.call(
		int(grid_data["cell_size"]) == SpatialGrid.DEFAULT_CELL_SIZE,
		"the grid keeps the source cell size 60"
	)
	var grid = SpatialGrid.new(int(grid_data["cell_size"]))
	var entities: Array = grid_data["entities"]
	for raw in entities:
		grid.insert(raw)
	check.call(
		grid.bucket_count() == int(grid_data["bucket_count"]),
		"the entities fill %s buckets" % grid_data["bucket_count"]
	)
	var buckets: Dictionary = grid_data["buckets"]
	var bucket_errors: Array = []
	for key in buckets:
		var parts := String(key).split(",")
		var expected: Array = buckets[key]
		var actual: Array = []
		var bucket_key := Vector2i(int(parts[0]), int(parts[1]))
		if grid.grid.has(bucket_key):
			for entity in grid.grid[bucket_key]:
				actual.append(String(entity["id"]))
		if actual != expected:
			bucket_errors.append(key)
	check.call(
		bucket_errors.is_empty(),
		"every entity sits in the floor(x/60), floor(y/60) bucket (%s)" % str(bucket_errors)
	)
	check.call(
		grid.bucket_of(-30.0, 10.0) == Vector2i(-1, 0)
		and grid.bucket_of(59.0, 59.0) == Vector2i(0, 0)
		and grid.bucket_of(60.0, 60.0) == Vector2i(1, 1),
		"negative and edge coordinates floor like Python's //"
	)
	var order_errors: Array = []
	for raw in grid_data["queries"]:
		var query: Dictionary = raw
		var team: Variant = query["team"]
		var found: Array = grid.query_range(
			float(query["x"]), float(query["y"]), float(query["radius"]), team
		)
		var ids: Array = []
		for entity in found:
			ids.append(String(entity["id"]))
		if ids != (query["ids"] as Array):
			order_errors.append("%s,%s" % [query["x"], query["radius"]])
	check.call(
		order_errors.is_empty(),
		"the query returns the source order and the team filter (%s)" % str(order_errors)
	)

	SpatialGrid.reset_shared()
	var living: Array = []
	for raw in entities:
		living.append(raw)
	SpatialGrid.update_spatial_grid(living.slice(0, 6), living.slice(6))
	check.call(
		SpatialGrid.shared().bucket_count() == int(grid_data["global_bucket_count"]),
		"the module grid indexes only the living minions and heroes"
	)
	var global_errors: Array = []
	for raw in grid_data["global_queries"]:
		var query: Dictionary = raw
		var found: Array = SpatialGrid.query_enemies_in_range(
			float(query["x"]), float(query["y"]), float(query["radius"]), query["team"]
		)
		var ids: Array = []
		for entity in found:
			ids.append(String(entity["id"]))
		if ids != (query["ids"] as Array):
			global_errors.append("%s,%s" % [query["x"], query["radius"]])
	check.call(
		global_errors.is_empty(),
		"query_enemies_in_range matches the source output (%s)" % str(global_errors)
	)


## `SoundManager`: volumes, throttle table and the positional falloff.
func _check_audio(check: Callable, data: Dictionary) -> void:
	var sound: Dictionary = data["sound"]
	var volumes: Dictionary = sound["volumes"]
	check.call(
		is_equal_approx(AudioFacade.DEFAULT_MASTER_VOLUME, float(volumes["master"]))
		and is_equal_approx(AudioFacade.DEFAULT_SFX_VOLUME, float(volumes["sfx"]))
		and is_equal_approx(AudioFacade.DEFAULT_BGM_VOLUME, float(volumes["bgm"]))
		and is_equal_approx(AudioFacade.AMBIENT_VOLUME, float(volumes["ambient"]))
		and is_equal_approx(AudioFacade.VOICE_VOLUME, float(volumes["voice"])),
		"the five source volumes survive as defaults"
	)
	check.call(
		int(AudioFacade.SFX_THROTTLE_MS) == 50
		and is_equal_approx(AudioFacade.POSITIONAL_MAX_DISTANCE, 800.0)
		and is_equal_approx(AudioFacade.POSITIONAL_MIN_VOLUME, 0.15)
		and int(AudioFacade.BGM_FADE_MS) == 2000
		and int(AudioFacade.BGM_STOP_FADE_MS) == 1000
		and int(AudioFacade.AMBIENT_FADE_MS) == 2000
		and int(AudioFacade.AMBIENT_STOP_FADE_MS) == 1500,
		"the positional floor/radius and the four fades keep the source timings"
	)
	var throttle: Dictionary = sound["throttle_ms"]
	var throttle_errors: Array = []
	for name in throttle:
		if AudioFacade.throttle_ms_for(String(name)) != int(throttle[name]):
			throttle_errors.append(name)
	check.call(
		throttle_errors.is_empty() and throttle.size() == 6,
		"SoundManager.throttle_ms keeps its six names (%s)" % str(throttle_errors)
	)
	check.call(
		AudioFacade.throttle_ms_for("hero_skill") == 50
		and AudioFacade.throttle_ms_for("unknown_sound") == 50,
		"an unlisted sound falls back to the 50 ms default"
	)
	var positional_errors: Array = []
	for raw in data["positional"]:
		var row: Dictionary = raw
		var falloff := AudioFacade.positional_falloff(
			float(row["x"]),
			float(row["y"]),
			float(row["player_x"]),
			float(row["player_y"]),
			float(row["max_distance"])
		)
		var volume := AudioFacade.positional_volume(
			float(row["x"]),
			float(row["y"]),
			float(row["player_x"]),
			float(row["player_y"]),
			float(row["max_distance"]),
			float(row["volume_mult"])
		)
		var plays := float(row["falloff"]) > 0.0
		if plays != bool(row["plays"]) \
				or absf(falloff - float(row["falloff"])) > 1e-6 \
				or absf(volume - float(row["volume_mult_final"])) > 1e-6:
			positional_errors.append("%s,%s" % [row["x"], row["player_x"]])
	check.call(
		positional_errors.is_empty(),
		"play_positional keeps the linear falloff, the floor and the 800 px cutoff (%s)"
		% str(positional_errors)
	)
	check.call(
		is_equal_approx(
			AudioFacade.positional_falloff(760.0, 100.0, 0.0, 100.0), 0.15
		)
		and is_equal_approx(
			AudioFacade.positional_falloff(900.0, 100.0, 0.0, 100.0), 0.0
		),
		"the falloff floors at 0.15 and dies past the radius"
	)


## `SaveManager`: three slots, the ten default fields and the format helpers.
func _check_save(check: Callable, data: Dictionary) -> void:
	var save: Dictionary = data["save"]
	check.call(
		int(save["num_slots"]) == SaveSlots.SLOT_COUNT,
		"the rebuild keeps three save slots"
	)
	var slot_files := []
	for slot in range(1, 4):
		slot_files.append(SaveSlots.slot_path(slot).get_file())
	check.call(
		slot_files == (save["slot_files"] as Array),
		"slot paths are the source slot_%d.json (%s)" % str(slot_files)
	)
	var initial_slot := SaveSlots.get_current_slot()
	check.call(
		initial_slot >= 1 and initial_slot <= SaveSlots.SLOT_COUNT,
		"the active slot stays inside 1..3 (got %d)" % initial_slot
	)
	SaveSlots.set_current_slot(1)
	check.call(SaveSlots.get_current_slot() == int(save["default_slot"]),
		"slot 1 is the default active slot")
	check.call(
		SaveSlots.set_current_slot(2) and SaveSlots.get_current_slot() == 2,
		"set_current_slot accepts 1..3"
	)
	check.call(
		not SaveSlots.set_current_slot(9) and SaveSlots.get_current_slot() == 2,
		"an out-of-range slot is refused"
	)
	SaveSlots.set_current_slot(initial_slot)
	var empty: Dictionary = save["empty"]
	var native_empty: Dictionary = SaveSlots.empty_state(FROZEN_NOW)
	var empty_errors: Array = []
	for key in empty:
		if not native_empty.has(key):
			empty_errors.append(key)
		elif not _value_equal(native_empty[key], empty[key]):
			empty_errors.append(key)
	check.call(
		empty_errors.is_empty() and native_empty.size() == 10,
		"get_empty_save's ten fields survive as empty_state (%s)" % str(empty_errors)
	)
	var playtime: Array = save["playtime"]
	var playtime_errors: Array = []
	for index in range(playtime.size()):
		var seconds: int = [0, 59, 60, 3599, 3600, 3660, 7325][index]
		if SaveSlots.format_playtime(seconds) != String(playtime[index]):
			playtime_errors.append(str(seconds))
	check.call(
		playtime_errors.is_empty(),
		"format_playtime matches the source matrix (%s)" % str(playtime_errors)
	)
	var stamps: Array = [
		0.0,
		FROZEN_NOW - 30.0,
		FROZEN_NOW - 120.0,
		FROZEN_NOW - 7200.0,
		FROZEN_NOW - 90000.0,
		FROZEN_NOW - 700000.0,
		FROZEN_NOW - 10000000.0,
	]
	var last_played: Array = save["last_played"]
	var stamp_errors: Array = []
	for index in range(stamps.size()):
		var actual := SaveSlots.format_last_played(float(stamps[index]), FROZEN_NOW)
		if actual != String(last_played[index]):
			stamp_errors.append("%s -> %s" % [last_played[index], actual])
	check.call(
		stamp_errors.is_empty(),
		"format_last_played keeps Never/Just now/Xm/Xh/Xd and the %%d %%b %%Y fallback (%s)"
		% str(stamp_errors)
	)
	var time_cases: Array = save["time"]
	var time_errors: Array = []
	var seconds_cases: Array = [0, 5, 65, 600, 3599]
	for index in range(time_cases.size()):
		if SaveSlots.format_time(int(seconds_cases[index])) != String(time_cases[index]):
			time_errors.append(str(seconds_cases[index]))
	check.call(
		time_errors.is_empty(),
		"format_time keeps M:SS and the --:-- empty value (%s)" % str(time_errors)
	)


## `SaveManager.update_level_stats`: only a win can move best score/time.
func _check_stats(check: Callable, data: Dictionary) -> void:
	var save: Dictionary = data["save"]
	var empty_stats = LevelStats.get_level_stats({"level_stats": {}}, 3)
	check.call(
		_value_equal(empty_stats, save["stats_default"]),
		"get_level_stats returns the seven defaults"
	)
	var state: Dictionary = {"level_stats": {}}
	var loss: Dictionary = LevelStats.update_level_stats(state, 3, {
		"won": false,
		"score": 900,
		"time_seconds": 300,
		"kills": 5,
		"combo": 7,
		"playtime_seconds": 120,
	})
	state = loss["state"]
	var win: Dictionary = LevelStats.update_level_stats(state, 3, {
		"won": true,
		"score": 1200,
		"time_seconds": 240,
		"kills": 9,
		"combo": 11,
		"playtime_seconds": 90,
	})
	state = win["state"]
	var slower: Dictionary = LevelStats.update_level_stats(state, 3, {
		"won": true,
		"score": 1100,
		"time_seconds": 400,
		"kills": 1,
		"combo": 2,
		"playtime_seconds": 30,
	})
	for pair in [["stats_loss", loss], ["stats_win", win], ["stats_win_worse", slower]]:
		var expected: Dictionary = save[pair[0]]
		var actual: Dictionary = pair[1]
		check.call(
			bool(actual["is_new_best_score"]) == bool(expected["flags"][0])
			and bool(actual["is_new_best_time"]) == bool(expected["flags"][1]),
			"%s keeps the source new-best flags" % pair[0]
		)
		check.call(
			_value_equal(actual["new_stats"], expected["stats"]),
			"%s keeps the executed stat totals" % pair[0]
		)
	check.call(
		_value_equal(slower["state"]["level_stats"]["3"], save["stats_saved"]),
		"the stored level stats match the source transaction"
	)
	check.call(
		not is_same(loss["new_stats"], win["new_stats"]) and bool(save["stats_aliases"]),
		"the rebuild returns copies where the source aliases the stored dict"
	)
	check.call(
		LevelStats.update_level_stats({"level_stats": {}}, 3, {"won": true}).is_empty(),
		"the native transaction rejects an incomplete match dict (documented deviation)"
	)


## The two dead symbols are named instead of quietly dropped.
func _check_dead(check: Callable, data: Dictionary) -> void:
	var rows: Dictionary = data["classification"]
	check.call(
		String(rows["module:fps_counter"]["kind"]) == "dead"
		and String(rows["class:FPSCounter"]["kind"]) == "dead",
		"the F8 overlay module and class stay dead with their reason"
	)
	check.call(
		(rows["module:fps_counter"]["note"] as String).contains("main_desktop_legacy"),
		'the dead reason names the legacy desktop entry'
	)
	check.call(
		String(rows["class:AdaptiveQuality"]["kind"]) == "deviation"
		and (rows["class:AdaptiveQuality"]["note"] as String).contains("tick()"),
		"the older adaptive governor is a documented deviation"
	)


static func _value_equal(left: Variant, right: Variant) -> bool:
	if right is Dictionary:
		if not (left is Dictionary):
			return false
		var expected: Dictionary = right
		var actual: Dictionary = left
		if actual.size() != expected.size():
			return false
		for key in expected:
			if not actual.has(key) or not _value_equal(actual[key], expected[key]):
				return false
		return true
	if right is Array:
		if not (left is Array) or (left as Array).size() != (right as Array).size():
			return false
		for index in range((right as Array).size()):
			if not _value_equal((left as Array)[index], (right as Array)[index]):
				return false
		return true
	if right is float or right is int:
		return (left is float or left is int) and is_equal_approx(
			float(left), float(right)
		)
	if right == null:
		return left == null
	return str(left) == str(right)
