extends RefCounted
## Layer 9bk: the baked minion sprites (`bake/bake_minion_atlas.py`) and the view-side
## clocks that pick a pose. The pose picker is replayed against rows the bake read from
## the REAL `_minion_cache_key`, so a drift from the source fails here, not on screen.

const MinionArt = preload("res://scripts/ui/minion_art.gd")
const MinionAnim = preload("res://scripts/ui/minion_anim.gd")
const MinionView = preload("res://scenes/combat/minion_view.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const MINION_VIEW := "res://scenes/combat/minion_view.gd"
const DEFINITIONS := "res://data/minions/"
const TYPES := ["goblin", "orc", "troll", "undead", "dark_rider"]


func run(check: Callable) -> void:
	var manifest := MinionArt.manifest()
	check.call(not manifest.is_empty(), "Minion atlas manifest parses")
	_check_manifest(check, manifest)
	_check_atlases(check, manifest)
	_check_frames(check)
	_check_key_cases(check, manifest)
	_check_clocks(check)
	_check_spawn_level(check)
	_check_view_wiring(check)


func _check_manifest(check: Callable, manifest: Dictionary) -> void:
	check.call(manifest.get("types", []) == TYPES, "The five source minion types are baked")
	check.call(manifest.get("teams", []) == ["blue", "red"], "Both teams are baked")
	var levels: Array = manifest.get("levels", [])
	check.call(
		levels.size() == 5 and int(levels[0]) == 1 and int(levels[4]) == 5,
		"Nexus levels 1-5 are baked"
	)
	check.call(MinionArt.atlases().size() == 50, "5 types x 2 teams x 5 levels = 50 atlases")
	var states: Dictionary = manifest.get("states", {})
	check.call(
		(
			int(states.get("atk", 0)) == 13
			and int(states.get("walk", 0)) == MinionAnim.WALK_POSES
			and int(states.get("idle", 0)) == MinionAnim.IDLE_POSES
		),
		"13 attack, 8 walk and 4 idle poses per sheet"
	)
	check.call(
		int(manifest.get("attack_anim_max", 0)) == MinionAnim.ATTACK_ANIM_MAX,
		"The clock uses the source attack_anim_max"
	)
	for type_id in TYPES:
		check.call(
			ResourceLoader.exists(DEFINITIONS + type_id + ".tres"),
			"Definition exists for %s" % type_id
		)


func _pose_names(manifest: Dictionary) -> Array:
	var states: Dictionary = manifest.get("states", {})
	var names: Array = []
	for kind in ["atk", "walk", "idle"]:
		for index in range(int(states.get(kind, 0))):
			names.append("%s%d" % [kind, index])
	return names


func _check_atlases(check: Callable, manifest: Dictionary) -> void:
	var poses := _pose_names(manifest)
	var missing: Array = []
	var wrong_size: Array = []
	var bad_rows: Array = []
	for name in MinionArt.atlases():
		var entry: Dictionary = MinionArt.atlases()[name]
		var path := MinionArt.atlas_path(String(name))
		if not FileAccess.file_exists(path):
			missing.append(name)
			continue
		var image := Image.load_from_file(path)
		var size: Array = entry["size"]
		if image == null or image.get_size() != Vector2i(int(size[0]), int(size[1])):
			wrong_size.append(name)
		var rows: Dictionary = entry["frames"]
		if rows.size() != poses.size() * 2:
			bad_rows.append(name)
		for pose in poses:
			for facing in [1, -1]:
				var row: Variant = rows.get("%s:%d" % [pose, facing])
				if not _row_in_bounds(row, size):
					bad_rows.append("%s %s:%d" % [name, pose, facing])
	check.call(missing.is_empty(), "Every atlas PNG exists: %s" % str(missing))
	check.call(wrong_size.is_empty(), "Every atlas decodes at its size: %s" % str(wrong_size))
	check.call(
		bad_rows.is_empty(), "Every pose/direction has an in-bounds frame: %s" % str(bad_rows)
	)


func _row_in_bounds(row: Variant, size: Array) -> bool:
	if not (row is Array) or (row as Array).size() != 6:
		return false
	var values: Array = row
	var x := float(values[0])
	var y := float(values[1])
	var width := float(values[2])
	var height := float(values[3])
	var inside := x >= 0.0 and y >= 0.0 and width > 0.0 and height > 0.0
	inside = inside and x + width <= float(size[0]) and y + height <= float(size[1])
	return inside and float(values[4]) <= width and float(values[5]) <= height


func _check_frames(check: Callable) -> void:
	check.call(MinionArt.team_name(0) == "blue" and MinionArt.team_name(1) == "red", "Team names")
	check.call(MinionArt.atlas_name("orc", 1, 9) == "orc_red_5", "Levels clamp to the sheet range")
	check.call(MinionArt.atlas_name("orc", 0, 0) == "orc_blue_1", "Levels clamp from below")
	check.call(MinionArt.frame_key("idle1", -0.5) == "idle1:-1", "Left-facing key")
	check.call(MinionArt.frame_key("idle1", 0.0) == "idle1:1", "A zero facing counts as right")
	check.call(MinionArt.frame("nobody", 0, 1, "idle0", 1.0).is_empty(), "Unknown type: no art")
	check.call(MinionArt.frame("goblin", 0, 1, "swim9", 1.0).is_empty(), "Unknown pose: no art")
	var art := MinionArt.frame("goblin", 0, 3, "walk2", 1.0)
	check.call(not art.is_empty(), "A goblin walk frame loads from the imported atlas")
	if art.is_empty():
		return
	var src: Rect2 = art["src"]
	var row: Array = MinionArt.atlases()["goblin_blue_3"]["frames"]["walk2:1"]
	check.call(src.size == Vector2(float(row[2]), float(row[3])), "The frame keeps its crop size")
	check.call((art["texture"] as Texture2D).get_width() > 0, "The atlas is a real texture")
	check.call(not MinionArt.frame("dark_rider", 1, 5, "atk12", -1.0).is_empty(), "Red rider")


func _check_key_cases(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("key_cases", [])
	check.call(cases.size() >= 90, "The bake recorded the source pose keys: %d" % cases.size())
	var mismatches: Array = []
	for row in cases:
		var got := MinionAnim.pose_key(int(row[0]), int(row[1]) == 1, float(row[2]), int(row[3]))
		var want := "%s%d" % [String(row[4]), int(row[5])]
		if got != want:
			mismatches.append("%s != %s for %s" % [got, want, str(row)])
	check.call(mismatches.is_empty(), "Pose picker matches the source key: %s" % str(mismatches))


func _unit(unit_id: int) -> UnitState:
	var unit := UnitState.new()
	unit.id = unit_id
	unit.hp = 45.0
	unit.position = Vector2(100, 100)
	return unit


func _pose(clocks: Dictionary) -> String:
	return MinionAnim.pose_key(
		int(clocks["attack"]), bool(clocks["moving"]), float(clocks["walk"]), int(clocks["anim"])
	)


func _check_clocks(check: Callable) -> void:
	var anim := MinionAnim.new()
	var unit := _unit(7)
	check.call(_pose(anim.observe(unit, 0)) == "idle0", "A new unit idles")
	check.call(_pose(anim.observe(unit, 19)) == "idle0", "Idle holds for 20 ticks")
	check.call(_pose(anim.observe(unit, 20)) == "idle1", "Idle advances every 20 ticks")
	check.call(_pose(anim.observe(unit, 20)) == "idle1", "No ticks, no change")
	unit.position = Vector2(104, 100)
	var walking := anim.observe(unit, 24)
	check.call(bool(walking["moving"]) and is_equal_approx(float(walking["walk"]), 1.0), "Walks")
	check.call(_pose(walking) == "walk2", "Four ticks of walking is pose 2 (0.25 per tick)")
	unit.cooldown_ticks = 45
	check.call(_pose(anim.observe(unit, 25)) == "atk12", "A fresh cooldown starts the swing")
	check.call(not bool(anim.observe(unit, 25)["moving"]), "A still unit is not walking")
	check.call(_pose(anim.observe(unit, 35)) == "atk7", "The swing counts down 24..1")
	check.call(_pose(anim.observe(unit, 60)).begins_with("idle"), "The swing ends")
	unit.hp = 40.0
	check.call(int(anim.observe(unit, 61)["hurt"]) == MinionAnim.HURT_FLASH_TICKS, "Hit: flash")
	check.call(int(anim.observe(unit, 69)["hurt"]) == 0, "The flash lasts 8 ticks")
	check.call(anim.tracked() == 1, "One unit is tracked")
	anim.prune([unit])
	check.call(anim.tracked() == 1, "Live units are kept")
	anim.prune([])
	check.call(anim.tracked() == 0, "Units that left the field are forgotten")


func _check_spawn_level(check: Callable) -> void:
	var world := Prototype.new()
	world.economy.gold[0] = 20000
	world.economy.opening[0] = 20000
	world.setup_arena()
	var veteran: UnitState = world.spawn_unit(GOBLIN, 0, 1)
	check.call(veteran != null and veteran.nexus_level == 1, "A tier-one spawn is level 1")
	world.upgrade_nexus(world.nexuses[0].id, 1)
	var recruit: UnitState = world.spawn_unit(GOBLIN, 0, 1)
	check.call(recruit != null and recruit.nexus_level == 2, "A spawn reads the live nexus tier")
	check.call(veteran.nexus_level == 1, "Earlier spawns keep their tier")
	var rival: UnitState = world.spawn_unit(GOBLIN, 1, 1)
	check.call(rival != null and rival.nexus_level == 1, "Each team has its own tier")


func _check_view_wiring(check: Callable) -> void:
	var view := MinionView.new()
	check.call(view.has_method("_draw_minion_sprite"), "The view draws minion sprites")
	check.call(view.has_method("_draw_minion_hp_bar"), "The view draws the source HP bar")
	view.free()
	var text := FileAccess.get_file_as_string(MINION_VIEW)
	var sprite := text.find("_draw_minion_sprite(unit)")
	var circle := text.find("draw_circle(point + Vector2(0, 4), radius + 2")
	check.call(
		sprite != -1 and sprite < circle,
		"The sprite path runs before the fallback circle, so a missing atlas still draws"
	)
	var prune := text.find("minion_anim.prune(session.world.units)")
	var loop := text.find("_draw_unit(unit)", prune)
	check.call(prune != -1 and prune < loop, "Clocks are pruned before the units are drawn")
