extends RefCounted
## Layer 9bq: the baked source boss bodies (`bake/bake_boss_atlas.py`). The 216 sheets are
## cross-checked against the Godot boss table, and the facing rule against the REAL
## `_boss_cache_key`.

const BossArt = preload("res://scripts/ui/boss_art.gd")
const STATS := "res://data/bosses/boss_stats.json"
const VIEW := "res://scenes/prototype/prototype_view.gd"


func run(check: Callable) -> void:
	var manifest := BossArt.manifest()
	check.call(not manifest.is_empty(), "Boss atlas manifest parses")
	_check_roster(check)
	_check_sheets(check)
	_check_facing(check, manifest)
	_check_frames(check)
	_check_view_wiring(check)


func _stats() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(STATS))
	var table: Dictionary = parsed if parsed is Dictionary else {}
	var rows: Dictionary = table.get("bosses", {})
	return rows


func _check_roster(check: Callable) -> void:
	var stats := _stats()
	var baked := BossArt.entries()
	check.call(baked.size() == 216, "All 216 bosses are baked: %d" % baked.size())
	var missing := 0
	var drift := 0
	for boss_type in stats:
		if not baked.has(boss_type):
			missing += 1
			continue
		var facts: Dictionary = stats[boss_type]
		var row: Dictionary = baked[boss_type]
		if int(facts.get("radius", -1)) != int(row.get("radius", -2)):
			drift += 1
		if str(facts.get("boss_class", "")) != str(row.get("class", "?")):
			drift += 1
	check.call(missing == 0, "Every boss in the Godot table has a body: %d missing" % missing)
	check.call(drift == 0, "Baked radius and class match the Godot table: %d differ" % drift)


func _check_sheets(check: Callable) -> void:
	var decoded := 0
	var wrong_size := 0
	var outside := 0
	var baked := BossArt.entries()
	for boss_type in baked:
		var row: Dictionary = baked[boss_type]
		var size: Array = row["size"]
		var image := Image.load_from_file(BossArt.path_for(boss_type))
		if image == null:
			continue
		decoded += 1
		if image.get_size() != Vector2i(int(size[0]), int(size[1])):
			wrong_size += 1
		var frames: Dictionary = row["frames"]
		for facing in ["-1", "1"]:
			var cell: Array = frames.get(facing, [0, 0, 0, 0, 1, 1])
			var fits := int(cell[2]) > 0 and int(cell[3]) > 0
			fits = fits and int(cell[0]) + int(cell[2]) <= int(size[0])
			fits = fits and int(cell[1]) + int(cell[3]) <= int(size[1])
			fits = fits and int(cell[4]) <= int(cell[2]) and int(cell[5]) <= int(cell[3])
			if not fits:
				outside += 1
	check.call(decoded == baked.size(), "Every boss sheet decodes: %d" % decoded)
	check.call(wrong_size == 0, "Every sheet decodes at its manifest size: %d differ" % wrong_size)
	check.call(outside == 0, "Both crops of every sheet lie inside it with anchors: %d" % outside)


func _check_facing(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("facing_cases", [])
	check.call(
		cases.size() >= 5, "The manifest carries the source facing choices: %d" % cases.size()
	)
	var mismatched := 0
	for row in cases:
		if BossArt.facing(int(row[0])) != int(row[1]):
			mismatched += 1
	check.call(mismatched == 0, "The facing rule matches the source key: %d differ" % mismatched)
	check.call(BossArt.facing(0) == -1, "A boss with no direction faces left")


func _check_frames(check: Callable) -> void:
	var left := BossArt.frame("abaddon", -1)
	var right := BossArt.frame("abaddon", 1)
	check.call(
		not left.is_empty() and left["texture"] is Texture2D, "A baked boss resolves its left crop"
	)
	check.call(not right.is_empty(), "A baked boss resolves its right crop")
	if not left.is_empty() and not right.is_empty():
		check.call(
			(left["src"] as Rect2) != (right["src"] as Rect2), "The two facings are two crops"
		)
	check.call(
		BossArt.frame("not_a_boss", 1).is_empty(), "An unknown boss falls back to the plain body"
	)
	check.call(
		BossArt.label_top("abaddon", 42) == 63,
		"The plate sits above the sprite top (BOSS_LABEL_TOP)"
	)
	check.call(
		BossArt.label_top("abaddon", 100) == 100, "A body wider than its top keeps the radius"
	)
	check.call(BossArt.label_top("not_a_boss", 30) == 30, "An unknown boss anchors on its radius")


func _check_view_wiring(check: Callable) -> void:
	var source := FileAccess.get_file_as_string(VIEW)
	check.call(
		source.contains("BossArt.frame(boss.boss_type, boss.direction)"),
		"The match view asks for the baked boss body"
	)
	check.call(
		source.contains("func _draw_boss_plain(") and source.contains("_draw_boss_plain(boss)"),
		"The crowned circle stays as the fallback body"
	)
	check.call(
		source.contains("bar_top = point.y - head_top - 6.0 - bar_height"),
		"The bar sits 6 px above the sprite top"
	)
