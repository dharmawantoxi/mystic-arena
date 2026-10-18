extends RefCounted
## Layer 9bl: the baked tower, castle and armor-crest sprites
## (`bake/bake_structure_atlas.py`) and the view-side clocks that pick a pose.

const StructureArt = preload("res://scripts/ui/structure_art.gd")
const StructureAnim = preload("res://scripts/ui/structure_anim.gd")
const SiegeView = preload("res://scenes/siege/siege_view.gd")
const StructureState = preload("res://scripts/combat/structure_state.gd")
const StructureDefinition = preload("res://scripts/data/structure_definition.gd")
const DEFINITIONS := "res://data/structures/"
const SIEGE_VIEW := "res://scenes/siege/siege_view.gd"
const MINION_VIEW := "res://scenes/combat/minion_view.gd"
const TOWER_PATHS := ["archer", "cannon", "ice", "mage"]


func run(check: Callable) -> void:
	var manifest := StructureArt.manifest()
	check.call(not manifest.is_empty(), "Structure atlas manifest parses")
	_check_manifest(check, manifest)
	_check_sheets(check, manifest)
	_check_definitions(check)
	_check_lookups(check)
	_check_clocks(check, manifest)
	_check_view_wiring(check)


func _check_manifest(check: Callable, manifest: Dictionary) -> void:
	check.call(manifest.get("tower_types", []) == TOWER_PATHS, "The four tower paths are baked")
	var levels: Dictionary = manifest.get("tower_levels", {})
	check.call(
		(
			(levels.get("archer", []) as Array).size() == 6
			and (levels.get("cannon", []) as Array).size() == 5
			and (levels.get("ice", []) as Array).size() == 5
			and (levels.get("mage", []) as Array).size() == 5
		),
		"Archer levels 1-6, the other paths 2-6"
	)
	check.call(StructureArt.section("towers").size() == 42, "21 tower sheets per team")
	check.call(StructureArt.section("castles").size() == 10, "5 castle sheets per team")
	check.call(StructureArt.section("crests").get("frames", {}).size() == 88, "88 crest frames")
	var castle: Dictionary = manifest.get("castle", {})
	var size: Array = castle.get("size", [])
	var anchor: Array = castle.get("anchor", [])
	check.call(
		(
			is_equal_approx(float(castle.get("scale", 0.0)), 0.85)
			and int(size[0]) == StructureArt.CASTLE_WIDTH
			and int(size[1]) == StructureArt.CASTLE_HEIGHT
			and int(anchor[0]) == (StructureArt.CASTLE_WIDTH >> 1)
			and int(anchor[1]) == StructureArt.CASTLE_HEIGHT - 35
		),
		"The castle is the source 0.85 scale, blitted at x - 76, y - 101"
	)


func _stems(manifest: Dictionary) -> Dictionary:
	var stems := {}
	for name in StructureArt.section("towers"):
		stems["tower_" + String(name)] = StructureArt.section("towers")[name]
	for name in StructureArt.section("castles"):
		stems["castle_" + String(name)] = StructureArt.section("castles")[name]
	stems["crests"] = manifest.get("crests", {})
	return stems


func _row_in_bounds(row: Variant, size: Array) -> bool:
	if not (row is Array) or (row as Array).size() != 6:
		return false
	var v: Array = row
	var inside := float(v[0]) >= 0.0 and float(v[1]) >= 0.0 and float(v[2]) > 0.0
	inside = inside and float(v[3]) > 0.0
	inside = inside and float(v[0]) + float(v[2]) <= float(size[0])
	inside = inside and float(v[1]) + float(v[3]) <= float(size[1])
	return inside and float(v[4]) <= float(v[2]) and float(v[5]) <= float(v[3])


func _check_sheets(check: Callable, manifest: Dictionary) -> void:
	var missing: Array = []
	var wrong_size: Array = []
	var bad_rows: Array = []
	var stems := _stems(manifest)
	for stem in stems:
		var entry: Dictionary = stems[stem]
		var path := StructureArt.sheet_path(String(stem))
		if not FileAccess.file_exists(path):
			missing.append(stem)
			continue
		var size: Array = entry["size"]
		var image := Image.load_from_file(path)
		if image == null or image.get_size() != Vector2i(int(size[0]), int(size[1])):
			wrong_size.append(stem)
		var rows: Dictionary = entry["frames"]
		var want := 5 if String(stem).begins_with("castle_") else 8
		if String(stem) == "crests":
			want = 88
		if rows.size() != want:
			bad_rows.append(stem)
		for key in rows:
			if not _row_in_bounds(rows[key], size):
				bad_rows.append("%s %s" % [stem, key])
	check.call(missing.is_empty(), "Every structure sheet exists: %s" % str(missing))
	check.call(wrong_size.is_empty(), "Every sheet decodes at its size: %s" % str(wrong_size))
	check.call(bad_rows.is_empty(), "Every frame lies inside its sheet: %s" % str(bad_rows))


func _check_definitions(check: Callable) -> void:
	var directory := DirAccess.open(DEFINITIONS)
	check.call(directory != null, "The structure definitions can be listed")
	if directory == null:
		return
	var uncovered: Array = []
	var seen := 0
	for file in directory.get_files():
		if not file.ends_with(".tres"):
			continue
		var definition := load(DEFINITIONS + file) as StructureDefinition
		if definition == null:
			uncovered.append(file)
			continue
		seen += 1
		for team in [0, 1]:
			var art: Dictionary = {}
			if definition.structure_kind == "nexus":
				art = StructureArt.castle_frame(team, definition.level, 0)
			else:
				art = StructureArt.tower_frame(definition.tower_path, team, definition.level, 0, 0)
			if art.is_empty():
				uncovered.append("%s team %d" % [file, team])
	check.call(seen == 26, "26 structure definitions: %d" % seen)
	check.call(uncovered.is_empty(), "Every structure level has art: %s" % str(uncovered))


func _check_lookups(check: Callable) -> void:
	check.call(StructureArt.tower_top_y("archer", 1) == -28, "Archer 1 bars sit 28 px up")
	check.call(StructureArt.tower_top_y("mage", 6) == -63, "Mage 6 bars sit 63 px up")
	check.call(StructureArt.tower_top_y("nobody", 1) == -26, "The source y - 26 fallback")
	check.call(
		StructureArt.crest_bucket(0.0) == 0 and StructureArt.crest_bucket(1.0) == 10, "Crest"
	)
	check.call(
		StructureArt.crest_bucket(0.55) == 6 and StructureArt.crest_bucket(0.04) == 0, "Round"
	)
	check.call(StructureArt.castle_name(1, 9) == "red_5", "Castle levels clamp")
	check.call(StructureArt.tower_frame("nobody", 0, 1, 0, 0).is_empty(), "Unknown path: no art")
	var tower := StructureArt.tower_frame("cannon", 1, 4, 1, 3)
	check.call(not tower.is_empty(), "A red level-4 cannon firing right loads from the sheet")
	check.call(not StructureArt.castle_frame(0, 5, 4).is_empty(), "A level-5 castle flame frame")
	check.call(not StructureArt.crest_frame(18, 1, 0.5, true).is_empty(), "A bright castle crest")
	if not tower.is_empty():
		check.call((tower["texture"] as Texture2D).get_width() > 0, "The sheet is a real texture")


func _structure(definition_name: String, structure_id: int) -> StructureState:
	var structure := StructureState.new()
	structure.id = structure_id
	structure.definition = load(DEFINITIONS + definition_name) as StructureDefinition
	return structure


func _check_clocks(check: Callable, manifest: Dictionary) -> void:
	var castle: Dictionary = manifest.get("castle", {})
	var timers: Array = castle.get("timers", [])
	var matches := timers.size() == StructureAnim.FLICKER_STEPS
	for index in range(timers.size()):
		matches = matches and StructureAnim.flicker(int(timers[index])) == index
	check.call(matches, "The flame flicker frames are the ones the bake read at timers 0/3/5/8/10")
	check.call(StructureAnim.flicker(13) == 0 and StructureAnim.flicker(0) == 0, "Flicker wraps")
	var shoots: Array = manifest.get("shoot_timers", [])
	var buckets := shoots.size() == 4
	for index in range(shoots.size()):
		buckets = buckets and StructureAnim.shoot_b(int(shoots[index])) == index
	check.call(buckets, "Shoot timers 0/5/8/10 are buckets 0/1/2/3 (flash // 3)")
	check.call(
		StructureAnim.flash_ticks("cannon") == 10 and StructureAnim.flash_ticks("ice") == 8, "Flash"
	)
	var anim := StructureAnim.new()
	var cannon := _structure("cannon_level_2.tres", 3)
	check.call(int(anim.observe(cannon, 0)["flash"]) == 0, "A quiet tower shows no flash")
	cannon.cooldown_ticks = 30
	var fired := int(anim.observe(cannon, 1)["flash"])
	check.call(
		fired == 10 and StructureAnim.shoot_b(fired) == 3, "A fresh cooldown fires the flash"
	)
	check.call(int(anim.observe(cannon, 4)["flash"]) == 7, "The flash counts down")
	check.call(StructureAnim.shoot_b(int(anim.observe(cannon, 9)["flash"])) == 0, "It ends")
	var archer := _structure("archer_level_1.tres", 4)
	archer.cooldown_ticks = 20
	anim.observe(archer, 0)
	archer.cooldown_ticks = 45
	check.call(int(anim.observe(archer, 1)["flash"]) == 8, "Archers flash for 8 ticks")
	check.call(anim.tracked() == 2, "Two structures are tracked")
	anim.prune([archer])
	check.call(anim.tracked() == 1, "Structures that are gone are forgotten")


func _check_view_wiring(check: Callable) -> void:
	var view := SiegeView.new()
	check.call(view.has_method("_draw_structure_art"), "The siege view draws structure sprites")
	check.call(view.has_method("_draw_structures"), "The siege view owns the structure layer")
	view.free()
	var siege := FileAccess.get_file_as_string(SIEGE_VIEW)
	var art := siege.find("if not _draw_structure_art(structure):")
	var plain := siege.find("_draw_structure_plain(structure)", art)
	check.call(art != -1 and art < plain, "A missing sheet still draws the plain boxes")
	var base := FileAccess.get_file_as_string(MINION_VIEW)
	var bases := base.find("_draw_base(Layout.RED_BASE")
	var layer := base.find("_draw_structures()", bases)
	var units := base.find("minion_anim.prune(session.world.units)", layer)
	check.call(
		bases != -1 and bases < layer and layer < units,
		"Structures are painted before the units, like Game.draw"
	)
