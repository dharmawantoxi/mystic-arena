extends RefCounted
## Layer 9bv15 closes the last recorded migration candidate. The "castle level-6
## magic aura" is dead code in the Python source: MAX_NEXUS_LEVEL = 5, NEXUS_LEVELS
## has keys 1-5, and Castle.upgrade() refuses level >= 5. Godot's 1-5 nexus
## catalog and the 9bl bake are already at parity, so no visual is missing.

const FIXTURE := "res://tests/fixtures/castle_aura_reach_source.json"
const NEXUS_UPGRADES_PATH := "res://scripts/match/nexus_upgrades.gd"
const STRUCTURES_MANIFEST := "res://data/art/structures.json"
const MAX_LEVEL := 5


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Castle aura reach fixture parses")
	if not (data is Dictionary):
		return
	_check_source(check, data)
	_check_native(check)


func _check_source(check: Callable, data: Dictionary) -> void:
	check.call(
		(
			String(data["layer"]) == "9bv15"
			and int(data["max_nexus_level"]) == MAX_LEVEL
			and String(data["max_castle_level_ref"]) == "MAX_NEXUS_LEVEL"
			and String(data["castle_levels_ref"]) == "NEXUS_LEVELS"
		),
		"Source caps the nexus and castle at level 5"
	)
	var keys: Array = data["nexus_level_keys"]
	check.call(
		(
			keys.size() == MAX_LEVEL
			and int(keys[0]) == 1
			and int(keys[1]) == 2
			and int(keys[2]) == 3
			and int(keys[3]) == 4
			and int(keys[4]) == MAX_LEVEL
		),
		"NEXUS_LEVELS has exactly keys 1-5, so level 6 has no data"
	)
	var dispatch: Array = data["castle_dispatch_levels"]
	check.call(
		(
			dispatch.size() == MAX_LEVEL
			and int(dispatch[0]) == 1
			and int(dispatch[4]) == MAX_LEVEL
			and String(data["castle_else_renderer"]) == "_render_castle_lvl6"
			and String(data["citadel_function"]) == "_render_castle_lvl6"
		),
		"_render_castle_lvl6 is only the dispatcher else-branch"
	)
	check.call(
		(
			String(data["magic_aura_function"]) == "_draw_castle_magic_aura"
			and String(data["aura_guard"]) == "lvl >= 6"
			and (data["aura_call_sites"] as Array).size() == 2
		),
		"The magic aura has two call sites, both guarded by lvl >= 6"
	)
	check.call(
		(
			String(data["upgrade_guard"]) == "self.level >= MAX_NEXUS_LEVEL"
			and bool(data["gate_returns_false"])
			and not bool(data["aura_reachable_in_source"])
		),
		"Castle.upgrade refuses level >= 5, so the aura is unreachable"
	)
	var walk: Dictionary = data["upgrade_walk"]
	var results: Array = walk["results"]
	var levels: Array = walk["levels"]
	var walk_ok: bool = (
		results.size() == 8
		and levels.size() == 8
		and bool(results[0])
		and bool(results[1])
		and bool(results[2])
		and bool(results[3])
		and not bool(results[4])
		and not bool(results[5])
		and int(levels[3]) == MAX_LEVEL
		and int(levels[7]) == MAX_LEVEL
		and int(walk["final_level"]) == MAX_LEVEL
		and int(walk["apply_level_stats_calls"]) == 4
	)
	check.call(walk_ok, "Executing the real Castle.upgrade walks 1->5 then stops")
	var bake: Array = data["bake_castle_levels"]
	check.call(
		bake.size() == MAX_LEVEL and int(bake[0]) == 1 and int(bake[4]) == MAX_LEVEL,
		"The 9bl structure bake covers exactly castle levels 1-5"
	)


func _check_native(check: Callable) -> void:
	var upgrades := FileAccess.get_file_as_string(NEXUS_UPGRADES_PATH)
	check.call(
		(
			upgrades.count("nexus_level_") == MAX_LEVEL
			and upgrades.contains("nexus_level_5.tres")
			and not upgrades.contains("nexus_level_6.tres")
		),
		"Native NexusUpgrades.LEVELS has five entries and no level-6 resource"
	)
	var structures := DirAccess.open("res://data/structures/")
	check.call(
		structures != null and not structures.file_exists("nexus_level_6.tres"),
		"No level-6 nexus resource exists in the rebuild"
	)
	var manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string(STRUCTURES_MANIFEST))
	var ok: bool = false
	if manifest is Dictionary:
		var castle: Variant = (manifest as Dictionary).get("castle")
		var sheets: Variant = (manifest as Dictionary).get("castles")
		if castle is Dictionary and sheets is Dictionary:
			var levels: Variant = (castle as Dictionary).get("levels")
			if levels is Array and (levels as Array).size() == MAX_LEVEL:
				ok = (
					not (sheets as Dictionary).has("blue_6")
					and not (sheets as Dictionary).has("red_6")
				)
	check.call(ok, "Baked castle manifest has five levels and no level-6 sheet")
