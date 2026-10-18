extends RefCounted
## Layer 9bp: the baked source tower bullets (`bake/bake_bullet_atlas.py`). The bearing
## picker is replayed against the buckets the REAL `_get_bullet_sprite` chose.

const BulletArt = preload("res://scripts/ui/bullet_art.gd")
const SIEGE_VIEW := "res://scenes/siege/siege_view.gd"
const KINDS := ["normal", "cannon", "ice", "mage"]


func run(check: Callable) -> void:
	var manifest := BulletArt.manifest()
	check.call(not manifest.is_empty(), "Bullet atlas manifest parses")
	_check_sheet(check, manifest)
	_check_buckets(check, manifest)
	_check_frames(check)
	_check_view_wiring(check)


func _check_sheet(check: Callable, manifest: Dictionary) -> void:
	var sheet: Dictionary = manifest.get("sheet", {})
	var size: Array = sheet.get("size", [0, 0])
	check.call(FileAccess.file_exists(BulletArt.SHEET), "The bullet sheet exists")
	var image := Image.load_from_file(BulletArt.SHEET)
	check.call(
		image != null and image.get_size() == Vector2i(int(size[0]), int(size[1])),
		"The bullet sheet decodes at its size"
	)
	var rows := BulletArt.frames()
	check.call(rows.size() == 38, "Sixteen arrows and three bolts per team: %d" % rows.size())
	var inside := true
	for key in rows:
		var row: Array = rows[key]
		var right := int(row[0]) + int(row[2])
		var bottom := int(row[1]) + int(row[3])
		inside = inside and int(row[2]) > 0 and int(row[3]) > 0
		inside = inside and right <= int(size[0]) and bottom <= int(size[1])
		inside = inside and int(row[4]) <= int(row[2]) and int(row[5]) <= int(row[3])
	check.call(inside, "Every bullet frame lies inside the sheet with its anchor in the crop")
	for team in ["blue", "red"]:
		var complete := true
		for bucket in range(BulletArt.BUCKETS):
			complete = complete and rows.has("normal:%s:%d" % [team, bucket])
		for kind in ["cannon", "ice", "mage"]:
			complete = complete and rows.has("%s:%s" % [kind, team])
		check.call(complete, "The %s team has every bullet frame" % team)


func _check_buckets(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("angle_cases", [])
	check.call(
		cases.size() >= 60, "The manifest carries the source bucket choices: %d" % cases.size()
	)
	var mismatched := 0
	var seen := {}
	for row in cases:
		var wanted := int(row[1])
		seen[wanted] = true
		if BulletArt.bucket(float(row[0])) != wanted:
			mismatched += 1
	check.call(mismatched == 0, "The bearing picker matches the source: %d differ" % mismatched)
	check.call(seen.size() == BulletArt.BUCKETS, "The cases reach every bucket: %d" % seen.size())
	# A target dead left on the same row is the one bearing that reaches bucket 8.
	check.call(BulletArt.bucket(Vector2(-100, 0).angle()) == 8, "Due left is bucket 8")
	check.call(BulletArt.bucket(Vector2(100, 0).angle()) == 0, "Due right is bucket 0")
	check.call(BulletArt.bucket(Vector2(0, 100).angle()) == 4, "Straight down is bucket 4")
	check.call(BulletArt.bucket(Vector2(0, -100).angle()) == 12, "Straight up is bucket 12")


func _check_frames(check: Callable) -> void:
	var found := 0
	for kind in KINDS:
		for team in [0, 1]:
			var art := BulletArt.frame(kind, team, 0.9)
			if not art.is_empty() and art["texture"] is Texture2D:
				found += 1
	check.call(found == 8, "Every bullet kind resolves for both teams: %d" % found)
	check.call(BulletArt.frame("bogus", 0, 0.0).is_empty(), "An unknown kind falls back to the dot")
	var key_blue := BulletArt.frame_key("normal", 0, 0.9)
	var key_red := BulletArt.frame_key("normal", 1, 0.9)
	check.call(key_blue != key_red, "The arrow is keyed by team")
	check.call(
		BulletArt.frame_key("cannon", 0, 1.0) == BulletArt.frame_key("cannon", 0, -2.0),
		"A bolt ignores its bearing"
	)


func _check_view_wiring(check: Callable) -> void:
	var source := FileAccess.get_file_as_string(SIEGE_VIEW)
	check.call(
		source.contains("BulletArt.frame(shot.kind, shot.team, bearing)"),
		"The siege view draws the baked bullet for each shot"
	)
	check.call(
		source.contains("draw_circle(shot.position, 4, color)"), "The old dot stays as the fallback"
	)
