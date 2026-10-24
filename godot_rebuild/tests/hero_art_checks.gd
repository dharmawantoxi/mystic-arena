extends RefCounted
## All-roster source hero atlases and the view-side pose clocks. Blue source frames
## cover 222 heroes; six non-boss heroes have red sheets, while 216 red boss-heroes
## resolve through their animated BossArt frames at the source hero scale.

const HeroArt = preload("res://scripts/ui/hero_art.gd")
const HeroAnim = preload("res://scripts/ui/hero_anim.gd")
const BossArt = preload("res://scripts/ui/boss_art.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const PROTOTYPE_VIEW := "res://scenes/prototype/prototype_view.gd"
const DEFINITIONS := "res://data/heroes/"
const NON_BOSS := ["grimjaw", "kaizen", "sylara", "thorne", "vex", "zephyr"]


func run(check: Callable) -> void:
	var manifest := HeroArt.manifest()
	check.call(not manifest.is_empty(), "Hero atlas manifest parses")
	_check_manifest(check, manifest)
	_check_atlases(check)
	_check_lookups(check)
	_check_shared_bosses(check, manifest)
	_check_key_cases(check, manifest)
	_check_clocks(check)
	_check_view_wiring(check)


func _check_manifest(check: Callable, manifest: Dictionary) -> void:
	var heroes: Array = manifest.get("heroes", [])
	var shared: Array = manifest.get("shared_red_bosses", [])
	check.call(heroes.size() == 222, "All 222 roster heroes have source facts: %d" % heroes.size())
	check.call(shared.size() == 216, "216 red boss-heroes share boss frames: %d" % shared.size())
	check.call(manifest.get("non_boss", []) == NON_BOSS, "The six non-boss heroes keep red atlases")
	check.call(manifest.get("teams", []) == ["blue", "red"], "Both teams resolve")
	check.call(
		(
			manifest.get("skill_heroes", []) == NON_BOSS
			and int(manifest.get("skill_quant", 0)) == HeroAnim.SKILL_QUANT
			and int(manifest.get("skill_samples", 0)) == 2
		),
		"The six non-boss heroes carry two source keyframes per skill"
	)
	check.call(HeroArt.section("atlases").size() == 228, "222 blue + 6 non-boss red atlases")
	check.call(HeroArt.section("meta").size() == 222, "Every hero has source metadata")
	check.call(
		(
			int(manifest.get("phases", 0)) == HeroAnim.PHASES
			and int(manifest.get("atk_quant", 0)) == HeroAnim.ATK_QUANT
		),
		"The pose clock uses the source phase count and attack quantum"
	)
	var expected := {}
	for hero_id in heroes:
		expected[String(hero_id) + "_blue"] = true
		if String(hero_id) in NON_BOSS:
			expected[String(hero_id) + "_red"] = true
		var facts := HeroArt.meta(String(hero_id))
		var ok := not facts.is_empty() and not String(facts.get("name", "")).is_empty()
		ok = ok and int(facts.get("radius", 0)) == 16 and int(facts.get("cooldown", 0)) > 0
		ok = ok and int(facts.get("top_offset", 0)) > 0
		ok = ok and float(facts.get("hero_scale", 0.0)) > 0.0
		check.call(ok, "Source facts exist for %s" % hero_id)
		check.call(
			ResourceLoader.exists(DEFINITIONS + String(hero_id) + ".tres"),
			"Definition exists for " + String(hero_id)
		)
	var expected_names := expected.keys()
	var actual_names := HeroArt.section("atlases").keys()
	expected_names.sort()
	actual_names.sort()
	check.call(expected_names == actual_names, "Atlas IDs equal the roster contract")


func _pose_names(facts: Dictionary) -> Array:
	var names: Array = []
	for phase in range(HeroAnim.PHASES):
		names.append("idle%d" % phase)
		if bool(facts.get("walk_poses", false)):
			names.append("walk%d" % phase)
	for index in range(floori(float(facts.get("cooldown", 0)) / float(HeroAnim.ATK_QUANT)) + 1):
		names.append("atk%d" % index)
	return names


func _row_in_bounds(row: Variant, size: Array) -> bool:
	if not (row is Array) or (row as Array).size() != 6:
		return false
	var v: Array = row
	var inside := float(v[0]) >= 0.0 and float(v[1]) >= 0.0 and float(v[2]) > 0.0
	inside = inside and float(v[3]) > 0.0
	inside = inside and float(v[0]) + float(v[2]) <= float(size[0])
	inside = inside and float(v[1]) + float(v[3]) <= float(size[1])
	return inside and float(v[4]) <= float(v[2]) and float(v[5]) <= float(v[3])


func _check_atlases(check: Callable) -> void:
	var missing: Array = []
	var wrong_size: Array = []
	var bad_rows: Array = []
	var atlases := HeroArt.section("atlases")
	for name in atlases:
		var entry: Dictionary = atlases[name]
		var path := HeroArt.atlas_path(String(name))
		if not FileAccess.file_exists(path):
			missing.append(name)
			continue
		var size: Array = entry["size"]
		var image := Image.load_from_file(path)
		if image == null or image.get_size() != Vector2i(int(size[0]), int(size[1])):
			wrong_size.append(name)
		var hero_id := String(name).rsplit("_", true, 1)[0]
		var rows: Dictionary = entry["frames"]
		var poses := _pose_names(HeroArt.meta(hero_id))
		var skills: Dictionary = entry.get("skills", {})
		if (hero_id in NON_BOSS) != (skills.size() == 4):
			bad_rows.append("%s has wrong skill families" % name)
		for skill in skills:
			var skill_poses: Array = skills[skill]
			if skill_poses.size() != 2:
				bad_rows.append("%s skill %s needs two poses" % [name, skill])
			for pose in skill_poses:
				poses.append(pose)
		if rows.size() != poses.size() * 2:
			bad_rows.append("%s has %d frames" % [name, rows.size()])
		for pose in poses:
			for facing in [1, -1]:
				if not _row_in_bounds(rows.get("%s:%d" % [pose, facing]), size):
					bad_rows.append("%s %s:%d" % [name, pose, facing])
		if int(entry.get("unique_frames", 0)) <= 0:
			bad_rows.append("%s has no unique pixel frames" % name)
	check.call(missing.is_empty(), "Every hero atlas exists: %s" % str(missing))
	check.call(
		wrong_size.is_empty(), "Every lossless WebP decodes at its size: %s" % str(wrong_size)
	)
	check.call(bad_rows.is_empty(), "Every pose has an in-bounds frame: %s" % str(bad_rows))


func _check_lookups(check: Callable) -> void:
	check.call(HeroArt.team_name(0) == "blue" and HeroArt.team_name(1) == "red", "Team names")
	check.call(HeroArt.atlas_name("vex", 1) == "vex_red", "Atlas names")
	check.call(HeroArt.frame_key("idle3", -0.2) == "idle3:-1", "Left-facing key")
	check.call(HeroArt.frame("nobody", 0, "idle0", 1.0).is_empty(), "An unknown hero has no art")
	var walking := HeroArt.frame("kaizen", 0, "walk3", -1.0)
	check.call(not walking.is_empty(), "A kaizen walk frame loads from the imported atlas")
	if not walking.is_empty():
		var src: Rect2 = walking["src"]
		var row: Array = HeroArt.section("atlases")["kaizen_blue"]["frames"]["walk3:-1"]
		check.call(
			src.size == Vector2(float(row[2]), float(row[3])), "The frame keeps its crop size"
		)
		check.call((walking["texture"] as Texture2D).get_width() > 0, "The atlas is a real texture")
	var still := HeroArt.frame("alchemist", 1, "walk3", 1.0)
	check.call(not still.is_empty(), "A hero with no walk poses shows its idle pose")
	var clamped := HeroArt.frame("kaizen", 0, "atk99", 1.0)
	var last_attack := HeroArt.frame("kaizen", 0, "atk9", 1.0)
	check.call(not clamped.is_empty(), "An attack timer past the baked range still draws")
	check.call(clamped.get("src") == last_attack.get("src"), "It uses the last baked attack pose")
	var skill := HeroArt.frame("kaizen", 0, "skill_q_7", 1.0)
	check.call(not skill.is_empty(), "A non-boss hero resolves a skill keyframe")
	check.call(
		String(skill.get("pose", "")).begins_with("skill_q_"),
		"Skill lookup uses the nearest baked keyframe"
	)


func _check_shared_bosses(check: Callable, manifest: Dictionary) -> void:
	var missing: Array = []
	var wrong_scale: Array = []
	var shared: Array = manifest.get("shared_red_bosses", [])
	for index in range(shared.size()):
		var id := String(shared[index])
		var row: Dictionary = BossArt.entries().get(id, {})
		var key := BossArt.resolve(row.get("frames", {}), "idle0", 1)
		if key.is_empty():
			missing.append(id)
		var scale := float(HeroArt.meta(id).get("hero_scale", 0.0))
		if scale <= 0.0:
			wrong_scale.append(id)
		# Resolve every row, but only retain a representative set of large textures.
		if index % 24 != 0 and id != "raz" and index != shared.size() - 1:
			continue
		var art := HeroArt.frame(id, 1, "idle0", 1.0)
		if art.is_empty():
			missing.append(id + " (texture)")
			continue
		if not is_equal_approx(float(art.get("scale", 0.0)), scale):
			wrong_scale.append(id)
		if art.get("texture") != BossArt.texture(id):
			missing.append(id + " (not shared)")
	var skill_checked := false
	for value in shared:
		var id := String(value)
		var row: Dictionary = BossArt.entries().get(id, {})
		var skills: Dictionary = row.get("skills", {})
		if skills.is_empty():
			continue
		var skill := String(skills.keys()[0])
		var pose := String(skills[skill][0])
		for team in [0, 1]:
			var art := HeroArt.frame(id, team, pose, 1.0)
			if art.is_empty() or art.get("texture") != BossArt.texture(id):
				missing.append(id + " (skill team %d)" % team)
			if not is_equal_approx(
				float(art.get("scale", 0.0)), float(HeroArt.meta(id).get("hero_scale", 0.0))
			):
				wrong_scale.append(id + " (skill)")
		skill_checked = true
		break
	check.call(skill_checked, "A source smart-skill pose resolves for both hero teams")
	check.call(missing.is_empty(), "Every red boss-hero resolves its boss body: %s" % str(missing))
	check.call(
		wrong_scale.is_empty(), "Shared hero bodies use the source scale: %s" % str(wrong_scale)
	)


func _check_key_cases(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("key_cases", [])
	check.call(cases.size() >= 200, "The bake recorded the source pose keys: %d" % cases.size())
	var mismatches: Array = []
	for row in cases:
		var got := HeroAnim.pose_key(int(row[0]), int(row[1]) == 1, float(row[2]))
		var want := "%s%d" % [String(row[3]), int(row[4])]
		if got != want:
			mismatches.append("%s != %s for %s" % [got, want, str(row)])
	check.call(mismatches.is_empty(), "Pose picker matches the source key: %s" % str(mismatches))


func _hero(hero_id: int) -> HeroState:
	var hero := HeroState.new()
	hero.id = hero_id
	hero.position = Vector2(100, 100)
	return hero


func _check_clocks(check: Callable) -> void:
	var anim := HeroAnim.new()
	var hero := _hero(5)
	var start := anim.observe(hero, 0)
	var pose := HeroAnim.pose_key(hero.attack_timer, bool(start["moving"]), float(start["pulse"]))
	check.call(pose == "idle0", "A new hero idles at phase 0")
	var later := anim.observe(hero, 5)
	pose = HeroAnim.pose_key(hero.attack_timer, bool(later["moving"]), float(later["pulse"]))
	check.call(pose == "idle1", "The pulse advances 0.1 per tick: phase 1 after 5 ticks")
	hero.position = Vector2(102, 100)
	var walking := anim.observe(hero, 6)
	check.call(bool(walking["moving"]), "Two pixels in one tick is walking")
	pose = HeroAnim.pose_key(hero.attack_timer, bool(walking["moving"]), float(walking["pulse"]))
	check.call(pose == "walk1", "Walking uses the walk poses on the same phase clock")
	hero.position = Vector2(102.2, 100)
	check.call(not bool(anim.observe(hero, 7)["moving"]), "Under 0.3 px per tick is standing")
	hero.attack_timer = 28
	check.call(HeroAnim.pose_key(hero.attack_timer, false, 1.0) == "atk9", "Attack 28 is pose 9")
	check.call(HeroAnim.pose_key(3, true, 1.0) == "atk1", "Attacking wins over walking")
	check.call(HeroAnim.pose_key(2, false, 1.0) == "atk0", "The last ticks are pose 0")
	check.call(
		HeroAnim.pose_key(28, true, 1.0, "q", 61) == "skill_q_30",
		"An active skill wins over attack and uses the source skill quantum"
	)
	check.call(anim.tracked() == 1, "One hero is tracked")
	anim.prune([hero])
	check.call(anim.tracked() == 1, "Live heroes are kept")
	anim.prune([])
	check.call(anim.tracked() == 0, "Heroes that left are forgotten")


func _check_view_wiring(check: Callable) -> void:
	var view := PrototypeView.new()
	check.call(view.has_method("_draw_hero_sprite"), "The view draws baked heroes")
	view.free()
	var text := FileAccess.get_file_as_string(PROTOTYPE_VIEW)
	var sprite := text.find("if _draw_hero_sprite(hero):")
	var marker := text.find("HeroMarker.silhouette(point, radius", sprite)
	check.call(sprite != -1 and sprite < marker, "The baked hero is tried before the marker")
	var prune := text.find("hero_anim.prune(session.world.units)")
	check.call(prune != -1, "Hero clocks are pruned every frame")
	check.call(
		(
			text.find("hero.active_skill, hero.active_skill_timer") != -1
			and text.find("art.is_empty() and not hero.active_skill.is_empty()") != -1
		),
		"The view passes skill state and falls back to the normal body when needed"
	)
