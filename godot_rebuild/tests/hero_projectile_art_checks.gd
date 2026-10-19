extends RefCounted
## Layer 9bu: verify frames baked from the original hero projectile painter.

const HeroProjectileArtScript = preload("res://scripts/ui/hero_projectile_art.gd")
const TEXTURE_PREFIX := "res://assets/art/hero_projectiles/"
const HERO_DIRECTORY := "res://data/heroes/"


func run(check: Callable) -> void:
	var art = HeroProjectileArtScript.new()
	var manifest: Dictionary = art.manifest_data()
	check.call(
		manifest.get("source", "") == "_entity.py:4976 Hero._draw_projectile",
		"Hero projectile atlas pins the source painter"
	)
	var hero_types: Array = manifest.get("hero_types", [])
	var hero_files := DirAccess.get_files_at(HERO_DIRECTORY)
	var hero_file_count := 0
	for file_name in hero_files:
		if String(file_name).ends_with(".tres"):
			hero_file_count += 1
	check.call(
		hero_types.size() == hero_file_count, "Every Godot hero has a baked projectile style"
	)
	check.call(hero_types.size() == 222, "The source hero roster has 222 projectile entries")

	var expected_specials := {
		"sylara": "arrow",
		"vex": "orb",
		"zephyr": "bolt",
		"morgath": "lightning",
		"ancient_apparition": "ice_shard",
	}
	check.call(
		manifest.get("special_types", {}) == expected_specials,
		"The five source-specific projectile branches are present"
	)
	var atlases: Dictionary = manifest.get("atlases", {})
	for atlas_name in atlases:
		var atlas: Dictionary = atlases[atlas_name]
		var png_path := TEXTURE_PREFIX + String(atlas.get("file", ""))
		check.call(
			ResourceLoader.exists(png_path), "Hero projectile atlas imports: %s" % atlas_name
		)
		var size: Array = atlas.get("size", [])
		check.call(
			(
				size.size() == 2
				and int(size[0]) == int(atlas.get("columns", 0)) * int(atlas.get("cell", 0))
				and int(size[1]) >= int(atlas.get("cell", 0))
				and int(atlas.get("frames", 0)) > 0
			),
			"Hero projectile frame bounds are valid: %s" % atlas_name
		)

	var attack: Dictionary = art.frame_for("vex", 72, 0.0, 1, false)
	var skill: Dictionary = art.frame_for("vex", 36, TAU * 12.0 / 32.0, 0, false)
	var bolt: Dictionary = art.frame_for("zephyr", 72, TAU * 31.0 / 32.0, 1, false)
	var crit_bolt: Dictionary = art.frame_for("zephyr", 36, TAU * 16.0 / 32.0, 1, true)
	var lightning: Dictionary = art.frame_for("morgath", 36, TAU * 16.0 / 32.0, 1, false)
	var arrow: Dictionary = art.frame_for("sylara", 72, TAU * 11.0 / 32.0, 1, false)
	var shard: Dictionary = art.frame_for("ancient_apparition", 0, TAU * 16.0 / 32.0, 1, false)
	check.call(attack.get("atlas", "") == "vex_attack", "Vex basic attacks select attack orbs")
	check.call(skill.get("atlas", "") == "vex_skill", "Vex zero-damage shots select skill orbs")
	check.call(bolt.get("atlas", "") == "zephyr_basic", "Zephyr basic shots select standard bolts")
	check.call(crit_bolt.get("atlas", "") == "zephyr_crit", "Zephyr crits select crit bolts")
	check.call(lightning.get("atlas", "") == "morgath", "Morgath selects animated lightning")
	check.call(int(arrow.get("index", -1)) == 11, "Sylara selects the nearest baked arrow angle")
	check.call(
		int(shard.get("index", -1)) == 16, "Ancient Apparition selects the baked shard angle"
	)
	check.call(
		int(attack.get("index", -1)) == 72 * 32, "Projectile age clamps to its last source frame"
	)
	var normal: Dictionary = art.frame_for("kaizen", 0, 0.0, 1, false)
	var crit: Dictionary = art.frame_for("kaizen", 0, 0.0, 1, true)
	check.call(normal.get("atlas", "") == "generic", "Other heroes use their source color fallback")
	check.call(
		int(normal.get("index", -1)) != int(crit.get("index", -1)),
		"Generic crit art has its own frame"
	)
	check.call(
		art.frame_for("unknown_hero", 0, 0.0, 1, false).is_empty(),
		"Unknown heroes use painter fallback"
	)

	var key_cases: Array = manifest.get("key_cases", [])
	var valid_key_cases := key_cases.size() == 22
	for case_value in key_cases:
		var key_case: Dictionary = case_value
		valid_key_cases = (
			valid_key_cases and String(key_case.get("pygame_rgb_sha256", "")).length() == 64
		)
		valid_key_cases = valid_key_cases and String(key_case.get("rgba_sha256", "")).length() == 64
	check.call(valid_key_cases, "The Pygame source key-case render hashes are pinned")
