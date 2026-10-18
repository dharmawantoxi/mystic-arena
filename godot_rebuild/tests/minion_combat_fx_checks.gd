extends RefCounted
## Layer 9bt: verifies the source-baked minion slash/death sheets, source-derived
## key cases, view-side clocks, and the inherited painter path used by both match views.

const FxArt = preload("res://scripts/ui/minion_combat_fx_art.gd")
const MinionAnim = preload("res://scripts/ui/minion_anim.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const GOBLIN = preload("res://data/minions/goblin.tres")
const MINION_VIEW := "res://scenes/combat/minion_view.gd"
const SIEGE_VIEW := "res://scenes/siege/siege_view.gd"
const PROTOTYPE_VIEW := "res://scenes/prototype/prototype_view.gd"
const TYPES := ["goblin", "orc", "troll", "undead", "dark_rider"]


func run(check: Callable) -> void:
	var manifest := FxArt.manifest()
	check.call(not manifest.is_empty(), "Minion combat FX manifest parses")
	_check_manifest(check, manifest)
	_check_atlases(check, manifest)
	_check_source_cases(check, manifest)
	_check_clocks(check)
	_check_view_wiring(check)


func _check_manifest(check: Callable, manifest: Dictionary) -> void:
	check.call(manifest.get("types", []) == TYPES, "All five source minion types are baked")
	check.call(
		int(manifest.get("angle_steps", 0)) == FxArt.ANGLE_STEPS,
		"The slash atlas angle quantization matches its loader"
	)
	check.call(
		(
			int(manifest.get("slash_life", 0)) == MinionAnim.SLASH_LIFE
			and int(manifest.get("death_life", 0)) == MinionAnim.DEATH_LIFE
		),
		"The presentation clocks match the source effect lifetimes"
	)
	check.call(FxArt.atlases().size() == TYPES.size(), "Each minion type has one FX atlas")


func _check_atlases(check: Callable, manifest: Dictionary) -> void:
	var missing: Array[String] = []
	var bad_frames: Array[String] = []
	var atlases: Dictionary = manifest.get("atlases", {})
	for type_id in TYPES:
		if not atlases.has(type_id):
			missing.append(type_id)
			continue
		var entry: Dictionary = atlases[type_id]
		var path := FxArt.atlas_path(type_id)
		if not FileAccess.file_exists(path):
			missing.append(type_id)
			continue
		var image := Image.load_from_file(path)
		var size: Array = entry["size"]
		if image == null or image.get_width() != int(size[0]) or image.get_height() != int(size[1]):
			bad_frames.append("%s: manifest size" % type_id)
			continue
		var rows: Dictionary = entry.get("frames", {})
		if rows.size() != FxArt.SLASH_LIFE * FxArt.ANGLE_STEPS + FxArt.DEATH_LIFE:
			bad_frames.append("%s: frame count" % type_id)
		for life in range(1, FxArt.SLASH_LIFE + 1):
			for angle_index in range(FxArt.ANGLE_STEPS):
				var slash_key := "slash%02d:%02d" % [life, angle_index]
				if not rows.has(slash_key):
					bad_frames.append("%s: %s" % [type_id, slash_key])
		for life in range(1, FxArt.DEATH_LIFE + 1):
			var death_key := "death%02d" % life
			if not rows.has(death_key):
				bad_frames.append("%s: %s" % [type_id, death_key])
		for row_value in rows.values():
			var row: Array = row_value
			var x := int(row[0])
			var y := int(row[1])
			var width := int(row[2])
			var height := int(row[3])
			if (
				x < 0
				or y < 0
				or width != int(entry["cell"][0])
				or height != int(entry["cell"][1])
				or x + width > int(size[0])
				or y + height > int(size[1])
				or int(row[4]) != (width >> 1)
				or int(row[5]) != (height >> 1)
			):
				bad_frames.append("%s: crop bounds/anchor" % type_id)
				break
		check.call(FxArt.atlas_texture(type_id) != null, "The %s FX atlas is imported" % type_id)
		check.call(
			not FxArt.slash_frame(type_id, 12, 0.0).is_empty(), "%s has a baked slash" % type_id
		)
		check.call(
			not FxArt.death_frame(type_id, 20).is_empty(), "%s has a baked death frame" % type_id
		)
	check.call(missing.is_empty(), "Every FX atlas file exists: %s" % str(missing))
	check.call(bad_frames.is_empty(), "Every FX frame fits its atlas: %s" % str(bad_frames))
	check.call(FxArt.frame("not_a_minion", "death20").is_empty(), "Unknown type falls back safely")
	var oriented := FxArt.slash_frame("goblin", 6, PI / 2.0)
	check.call(
		String(oriented.get("key", "")) == "slash06:08", "Slash direction selects its baked case"
	)


func _check_source_cases(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("key_cases", [])
	var slashes := 0
	var deaths := 0
	var invalid: Array[String] = []
	var atlases: Dictionary = manifest.get("atlases", {})
	for row_value in cases:
		var row: Dictionary = row_value
		var type_id := String(row.get("type", ""))
		var digest := String(row.get("rgba_sha256", ""))
		if digest.length() != 64:
			invalid.append("%s: missing source render digest" % type_id)
		if String(row.get("kind", "")) == "slash":
			slashes += 1
			var slash_entry: Dictionary = atlases.get(type_id, {})
			if (
				int(row.get("max_life", 0)) != MinionAnim.SLASH_LIFE
				or int(row.get("distance", 0)) != int(slash_entry.get("slash_distance", -1))
				or int(row.get("life", 0)) not in [1, 6, 12]
			):
				invalid.append("%s: slash source parameters" % type_id)
		elif String(row.get("kind", "")) == "death":
			deaths += 1
			var death_entry: Dictionary = atlases.get(type_id, {})
			if (
				int(row.get("radius", -1)) != int(death_entry.get("radius", -2))
				or int(row.get("life", 0)) not in [1, 11, 20]
			):
				invalid.append("%s: death source parameters" % type_id)
		else:
			invalid.append("%s: unknown source case" % type_id)
	check.call(slashes == TYPES.size() * 12, "Source slash key cases cover life and facing samples")
	check.call(deaths == TYPES.size() * 3, "Source death key cases cover start, middle and end")
	check.call(invalid.is_empty(), "Source render key cases are recorded: %s" % str(invalid))


func _check_clocks(check: Callable) -> void:
	var animation := MinionAnim.new()
	var unit := UnitState.new()
	unit.id = 701
	unit.team = 0
	unit.definition = GOBLIN
	unit.nexus_level = 1
	unit.position = Vector2(100, 100)
	unit.hp = 45.0
	var idle := animation.observe(unit, 0, Vector2(110, 120))
	check.call(int(idle["slash_life"]) == 0, "A new minion has no slash effect")
	unit.cooldown_ticks = 45
	var slash := animation.observe(unit, 1, Vector2(110, 120))
	check.call(int(slash["slash_life"]) == MinionAnim.SLASH_LIFE, "Cooldown starts the slash")
	check.call(
		is_equal_approx(float(slash["slash_angle"]), atan2(20.0, 10.0)),
		"Slash angle points at the source target"
	)
	unit.cooldown_ticks = 42
	slash = animation.observe(unit, 4, Vector2(110, 120))
	check.call(int(slash["slash_life"]) == 9, "Slash lifetime decays with simulation ticks")
	var deaths := (
		animation
		. take_death_snapshots(
			[
				{"kind": "hit", "target_id": unit.id, "to": Vector2(125, 135)},
				{"kind": "death", "target_id": unit.id},
			]
		)
	)
	check.call(deaths.size() == 1, "A death event captures the tracked minion")
	if deaths.size() == 1:
		check.call(
			int(deaths[0]["life"]) == MinionAnim.DEATH_LIFE, "Death starts at source frame 20"
		)
		check.call(
			deaths[0]["position"] == Vector2(125, 135), "Death uses the hit's exact position"
		)
	check.call(animation.tracked() == 0, "Captured corpses leave the live pose table")


func _check_view_wiring(check: Callable) -> void:
	var minion_text := FileAccess.get_file_as_string(MINION_VIEW)
	var siege_text := FileAccess.get_file_as_string(SIEGE_VIEW)
	var prototype_text := FileAccess.get_file_as_string(PROTOTYPE_VIEW)
	check.call(
		(
			minion_text.contains("const MinionCombatFxArt = preload(")
			and minion_text.contains("MinionCombatFxArt.draw_slash(")
			and minion_text.contains("MinionCombatFxArt.draw_death(")
		),
		"The minion view draws both baked effects"
	)
	var capture := minion_text.find("take_death_snapshots")
	var prune := minion_text.find("minion_anim.prune(session.world.units)")
	check.call(capture >= 0 and capture < prune, "Death snapshots are captured before retirement")
	check.call(
		(
			siege_text.contains('extends "res://scenes/combat/minion_view.gd"')
			and prototype_text.contains('extends "res://scenes/siege/siege_view.gd"')
		),
		"Siege and prototype inherit the shared minion FX painter"
	)
