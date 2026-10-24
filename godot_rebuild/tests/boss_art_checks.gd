extends RefCounted
## Animated source boss bodies: all 216 lossless WebP sheets, idle/walk/attack
## keyframes, source smart-skill samples, cache-key pose selection and live view wiring.

const BossArt = preload("res://scripts/ui/boss_art.gd")
const BossAnim = preload("res://scripts/ui/boss_anim.gd")
const BossState = preload("res://scripts/match/boss_state.gd")
const STATS := "res://data/bosses/boss_stats.json"
const VIEW := "res://scenes/prototype/prototype_view.gd"


func run(check: Callable) -> void:
	var manifest := BossArt.manifest()
	check.call(not manifest.is_empty(), "Boss atlas manifest parses")
	_check_roster(check, manifest)
	_check_sheets(check)
	_check_facing(check, manifest)
	_check_pose_keys(check)
	_check_live_skill_poses(check)
	_check_frames(check)
	_check_view_wiring(check)


func _stats() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(STATS))
	var table: Dictionary = parsed if parsed is Dictionary else {}
	var rows: Dictionary = table.get("bosses", {})
	return rows


func _check_roster(check: Callable, manifest: Dictionary) -> void:
	var stats := _stats()
	var baked := BossArt.entries()
	check.call(baked.size() == 216, "All 216 bosses are baked: %d" % baked.size())
	check.call(int(manifest.get("phases", 0)) == BossAnim.PHASES, "Eight source idle phases")
	check.call(manifest.get("smart_bosses", []).size() == 79, "79 source smart-skill bosses")
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


func _pose_names(row: Dictionary) -> Array:
	var poses: Array = []
	for phase in range(BossAnim.PHASES):
		poses.append("idle%d" % phase)
		if bool(row.get("walk_poses", false)):
			poses.append("walk%d" % phase)
	poses.append_array(row.get("attack_poses", []))
	for skill in row.get("skills", {}):
		poses.append_array(row["skills"][skill])
	return poses


func _check_sheets(check: Callable) -> void:
	var decoded := 0
	var wrong_size := 0
	var outside := 0
	var overlaps := 0
	var incomplete := 0
	var unbaked := 0
	var walking := 0
	var skills := 0
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
		var poses := _pose_names(row)
		if frames.size() != poses.size() * 2:
			incomplete += 1
		if bool(row.get("walk_poses", false)):
			walking += 1
		skills += (row.get("skills", {}) as Dictionary).size()
		unbaked += (row.get("unbaked_poses", []) as Array).size()
		var placed := {}
		var rectangles: Array = []
		for pose in poses:
			for facing in ["-1", "1"]:
				var cell: Array = frames.get("%s:%s" % [pose, facing], [])
				if cell.size() != 6:
					incomplete += 1
					continue
				var fits := int(cell[2]) > 0 and int(cell[3]) > 0
				fits = fits and int(cell[0]) + int(cell[2]) <= int(size[0])
				fits = fits and int(cell[1]) + int(cell[3]) <= int(size[1])
				fits = fits and int(cell[4]) <= int(cell[2]) and int(cell[5]) <= int(cell[3])
				if not fits:
					outside += 1
				var rect := Rect2(cell[0], cell[1], cell[2], cell[3])
				var signature := "%d:%d:%d:%d" % cell.slice(0, 4)
				if not placed.has(signature):
					for other in rectangles:
						if rect.intersects(other):
							overlaps += 1
					placed[signature] = true
					rectangles.append(rect)
	check.call(decoded == baked.size(), "Every boss sheet decodes: %d" % decoded)
	check.call(wrong_size == 0, "Every WebP decodes at its manifest size: %d differ" % wrong_size)
	check.call(outside == 0, "Every crop and anchor lies inside its sheet: %d" % outside)
	check.call(overlaps == 0, "Unique tight-packed crops never overlap: %d" % overlaps)
	check.call(incomplete == 0, "Every listed pose has both facings: %d problems" % incomplete)
	check.call(walking > 0, "Movement-capable bosses include walk keyframes: %d" % walking)
	check.call(skills >= 300, "Source smart-skill families have keyframes: %d" % skills)
	check.call(
		unbaked == 0, "Direct-render fallback captured every requested pose: %d missing" % unbaked
	)


func _check_facing(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("facing_cases", [])
	check.call(cases.size() >= 5, "The manifest carries source facing choices: %d" % cases.size())
	var mismatched := 0
	for row in cases:
		if BossArt.facing(int(row[0])) != int(row[1]):
			mismatched += 1
	check.call(mismatched == 0, "The facing rule matches the source key: %d differ" % mismatched)
	check.call(BossArt.facing(0) == -1, "A boss with no direction faces left")


func _check_pose_keys(check: Callable) -> void:
	var mismatches: Array = []
	for boss_type in BossArt.entries():
		var row: Dictionary = BossArt.entries()[boss_type]
		var attack_quant := int(row.get("attack_quant", 0))
		var skill_quant := int(row.get("skill_quant", 0))
		if attack_quant <= 0 or skill_quant <= 0:
			mismatches.append(boss_type + " quantum")
			continue
		var attack := BossAnim.pose_key(boss_type, attack_quant, "", 0, false, 0.0)
		var skill := BossAnim.pose_key(boss_type, 0, "q", skill_quant, false, 0.0)
		if attack != "atk1" or skill != "skill_q_1":
			mismatches.append(boss_type)
	check.call(
		mismatches.is_empty(), "Every boss uses its source pose quantum: %s" % str(mismatches)
	)
	check.call(BossAnim.pose_key("abaddon", 0, "", 0, false, 0.55) == "idle1", "Idle phase")
	check.call(BossAnim.pose_key("abaddon", 0, "", 0, true, 0.55) == "walk1", "Walk phase")
	check.call(
		BossAnim.pose_key("abaddon", 30, "q", 30, true, 0.55).begins_with("skill_q_"),
		"Skill wins over attack and walking"
	)


## nyxareth's source smart AI casts the numbered keys "1".."4"; they are baked like Q/W/E/R.
## `from_boss` still names only baked skills, so an unknown key keeps the animated body
## instead of freezing on the idle0 fallback.
func _check_live_skill_poses(check: Callable) -> void:
	var boss := BossState.new()
	boss.boss_type = "nyxareth"
	boss.pulse = 0.55
	boss.active_skill = "4"
	boss.active_skill_timer = 95
	var skills: Dictionary = BossArt.entries()["nyxareth"]["skills"]
	check.call(
		skills.keys().size() == 4 and skills.has("1") and skills.has("4"),
		"nyxareth's numbered source skills are baked: %s" % str(skills.keys())
	)
	var cast := BossAnim.from_boss(boss)
	check.call(cast == "skill_4_95", "nyxareth's ultimate names its skill pose: %s" % cast)
	var art := BossArt.frame("nyxareth", 1, cast)
	check.call(String(art.get("pose", "")) == "skill_4_95:1", "That cast resolves to its keyframe")
	boss.active_skill = "z"
	check.call(BossAnim.from_boss(boss) == "idle1", "An unbaked cast keeps the idle phase")
	boss.moving_cached = true
	check.call(BossAnim.from_boss(boss) == "walk1", "An unbaked cast keeps the walk phase")
	boss.timer = 30
	var attack := BossAnim.from_boss(boss)
	check.call(attack == "atk30", "An unbaked cast keeps the attack pose: %s" % attack)
	art = BossArt.frame("nyxareth", 1, attack)
	check.call(
		String(art.get("pose", "")).begins_with("atk"),
		"That attack pose resolves to an attack crop"
	)
	boss.boss_type = "abaddon"
	boss.active_skill = "q"
	boss.active_skill_timer = 30
	check.call(BossAnim.from_boss(boss) == "skill_q_5", "A baked cast still wins: abaddon Q")


func _check_frames(check: Callable) -> void:
	var left := BossArt.frame("abaddon", -1, "idle0")
	var right := BossArt.frame("abaddon", 1, "idle0")
	check.call(
		not left.is_empty() and left["texture"] is Texture2D, "A baked boss resolves its left crop"
	)
	check.call(not right.is_empty(), "A baked boss resolves its right crop")
	if not left.is_empty() and not right.is_empty():
		check.call(
			(left["src"] as Rect2) != (right["src"] as Rect2), "The two facings are two crops"
		)
	var animated := BossArt.frame("abaddon", 1, "idle1")
	check.call(
		String(animated.get("pose", "")).begins_with("idle1:"), "Idle phase resolves exactly"
	)
	var attack := BossArt.frame("abaddon", 1, "atk999")
	check.call(
		String(attack.get("pose", "")).begins_with("atk"),
		"Large attack timers use an attack keyframe"
	)
	var unknown := BossArt.frame("abaddon", 1, "skill_z_99")
	check.call(
		String(unknown.get("pose", "")).begins_with("idle0:"),
		"Unknown skills use the idle fallback"
	)
	check.call(BossArt.frame("not_a_boss", 1).is_empty(), "An unknown boss has no baked body")
	check.call(BossArt.label_top("abaddon", 42) == 63, "The plate sits above the sprite top")
	check.call(BossArt.label_top("abaddon", 100) == 100, "A wider body keeps the radius")
	check.call(BossArt.label_top("not_a_boss", 30) == 30, "An unknown boss anchors on its radius")


func _check_view_wiring(check: Callable) -> void:
	var source := FileAccess.get_file_as_string(VIEW)
	check.call(
		source.contains("var pose := BossAnim.from_boss(boss)"),
		"The match view selects a source pose"
	)
	check.call(
		source.contains("BossArt.frame(boss.boss_type, boss.direction, pose)"),
		"The match view asks for that animated body"
	)
	check.call(
		source.contains("boss_pose_draws[pose]"), "The live scene records resolved boss poses"
	)
	check.call(
		source.contains("func _draw_boss_plain(") and source.contains("_draw_boss_plain(boss)"),
		"The crowned circle stays as the fallback body"
	)
	check.call(
		source.contains("bar_top = point.y - head_top - 6.0 - bar_height"),
		"The bar sits 6 px above the sprite top"
	)
