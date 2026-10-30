extends RefCounted
## Whole `map_components/` folder coverage, proven from the source inventory.
##
## `map_components/` is two files (7.504 lines) holding the seven map modules
## merged into `_bundle.py`. `tests/map_components_source_oracle.py` imports the
## bundle with pygame stubbed out, executes the real `PathGenerator` and
## `DecorationGenerator` at the source seed (`random.seed(42)`) and classifies
## every public symbol of the folder: 31 native ports, 112 data keys, 39 baked
## pixels, 9 executed generators, 1 internal cache and 2 import-shim entries.
##
## This suite proves the accounting natively:
##
## * the folder shape and the seven merged module ranges inside `_bundle.py`;
## * the 52 `palettes.py` colours (now `data/levels/map_palette.json`) and
##   `TILE_SIZE`, so no rasteriser hard-codes a palette colour again;
## * the 54 theme dictionaries: name, boss identity, particle type and full key
##   count, theme by theme, against `data/art/map_dynamic.json`;
## * the executed geometry: `LaneLayout.create_paths()` point by point, the
##   61-point river, and the four decoration arrays the runtime reads every
##   frame (`bones`, `gravestones`, `rocks_mossy`, `torch_stones`);
## * the two arrays only the bake touches (`boss_landmarks`, `crystals_blue`)
##   are classified, not silently dropped;
## * the seed ledger: two fixed seeds (42, 100) and two entropy reseeds, and
##   that the decoration generator is repeatable;
## * every classification entry's target file and token, so a "ported" claim
##   always has a file behind it.

const FIXTURE := "res://tests/fixtures/map_components_source.json"
const MAP_PALETTE := "res://data/levels/map_palette.json"
const DYNAMIC := "res://data/art/map_dynamic.json"
const THEME_PALETTE := "res://data/levels/theme_palette.json"
const RIVER := "res://data/levels/river_path.json"
const OVERLAY := "res://data/art/map_overlay.json"
const BASE := "res://data/art/map_base.json"
const LAYOUT_GD := "res://scripts/ui/dynamic_map_layout.gd"
const PALETTE_GD := "res://scripts/ui/terrain_palette.gd"

const MapPalette = preload("res://scripts/ui/map_palette.gd")
const LaneLayout = preload("res://scripts/data/lane_layout.gd")
const TerrainPalette = preload("res://scripts/ui/terrain_palette.gd")
const WallTiles = preload("res://scripts/ui/wall_tiles.gd")
const DynamicMap = preload("res://scripts/ui/dynamic_map_renderer.gd")
const MapArt = preload("res://scripts/ui/map_art.gd")

const SOURCE_THEMES := 54
const SOURCE_PALETTE_COLOURS := 52
const SOURCE_SYMBOLS := 194
const SOURCE_LINES := 7504
const PARTICLE_TYPES := ["acid", "ash", "ember", "firefly", "sand", "snow", "spirit"]
const BOSS_IDENTITIES := ["abaddon", "alchemist", "ignis_drachorn", "krobellus"]


func run(check: Callable) -> void:
	var source := _fixture()
	check.call(not source.is_empty(), "The map_components/ inventory fixture parses")
	if source.is_empty():
		return
	_check_folder(check, source)
	_check_palette(check, source)
	_check_themes(check, source)
	_check_geometry(check, source)
	_check_decorations(check, source)
	_check_seeds(check, source)
	_check_aliases(check, source)
	_check_classification(check, source)
	_check_bakes(check, source)
	_check_native_tokens(check)


func _fixture() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	return parsed if parsed is Dictionary else {}


func _json(path: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


func _same(left: Variant, right: Variant) -> bool:
	# JSON round-trip keeps the comparison order-insensitive and deep, which
	# Dictionary `==` is not across Godot versions.
	var encoded_left := JSON.stringify(_sorted(left))
	var encoded_right := JSON.stringify(_sorted(right))
	return encoded_left == encoded_right


func _sorted(value: Variant) -> Variant:
	if value is Dictionary:
		var source: Dictionary = value
		var keys: Array = source.keys()
		keys.sort()
		var ordered := {}
		for key in keys:
			ordered[key] = _sorted(source[key])
		return ordered
	if value is Array:
		var listed: Array = []
		for item in value:
			listed.append(_sorted(item))
		return listed
	return value


func _check_folder(check: Callable, source: Dictionary) -> void:
	var folder: Dictionary = source.get("folder", {})
	check.call(int(folder.get("count", 0)) == 2, "map_components/ holds two Python files")
	check.call(int(folder.get("lines", 0)) == SOURCE_LINES,
		"map_components/ is 7.504 source lines")
	var files: Dictionary = folder.get("files", {})
	check.call(int(files.get("_bundle.py", 0)) == 7403,
		"_bundle.py is the 7.403-line merged map")
	check.call(int(files.get("__init__.py", 0)) == 101,
		"__init__.py is the 101-line sys.modules shim")
	var modules: Array = source.get("modules", [])
	var names: Array = []
	var total := 0
	var ordered := true
	var previous := 0
	for entry in modules:
		var row: Dictionary = entry
		names.append(row.get("module", ""))
		total += int(row.get("lines", 0))
		ordered = ordered and int(row.get("start", 0)) > previous
		previous = int(row.get("end", 0))
	check.call(names == [
		"palettes", "themes", "generators", "static_renderer",
		"dynamic_renderer", "decoration_renderer", "shop_renderer",
	], "the merge keeps the seven modules in source order: %s" % str(names))
	var header := int(modules[0].get("start", 0)) - 1 if modules.size() > 0 else 0
	check.call(ordered and total == 7368 and total + header == 7403,
		"the seven ranges tile the bundle after its %d-line header: %d lines"
		% [header, total])


func _check_palette(check: Callable, source: Dictionary) -> void:
	var palette: Dictionary = source.get("palette", {})
	var colours: Dictionary = palette.get("colors", {})
	check.call(colours.size() == SOURCE_PALETTE_COLOURS,
		"palettes.py is 52 theme-independent colours")
	check.call(int(palette.get("tile_size", 0)) == 16 and MapPalette.tile_size() == 16,
		"TILE_SIZE is 16 on both sides")
	var expected := {}
	for name in colours:
		var rgb: Array = colours[name]
		expected[String(name).to_lower()] = rgb
	var shipped := MapPalette.colors()
	check.call(_same(shipped, expected),
		"data/levels/map_palette.json carries every palettes.py colour verbatim")
	check.call(MapPalette.color("outline") == Color8(12, 8, 12)
		and MapPalette.color("stone_mid") == Color8(95, 95, 105)
		and MapPalette.color("stone_high") == Color8(175, 175, 185),
		"the palette loader resolves OUTLINE and the stone ramp")
	var image := WallTiles.raster()
	check.call(image.get_pixel(0, 0) == MapPalette.color("outline")
		and image.get_pixel(2, 2) == MapPalette.color("stone_high")
		and image.get_pixel(5, 10) == MapPalette.color("stone_mid"),
		"the wall rasteriser now reads the palette instead of literals")
	var shipped_palette: Dictionary = _json(MAP_PALETTE)
	check.call(String(shipped_palette.get("source", "")) == "map_components/_bundle.py::palettes",
		"map_palette.json names its source section")


func _check_themes(check: Callable, source: Dictionary) -> void:
	var themes: Dictionary = source.get("themes", {})
	var consts: Dictionary = themes.get("consts", {})
	check.call(int(themes.get("count", 0)) == SOURCE_THEMES,
		"themes.py holds 54 theme dictionaries")
	check.call(consts.size() == SOURCE_THEMES,
		"every theme has exactly one *_THEME constant")
	var meta: Dictionary = themes.get("meta", {})
	var palette: Dictionary = _json(THEME_PALETTE)
	var dynamic: Dictionary = _json(DYNAMIC)
	var dynamic_themes: Dictionary = dynamic.get("themes", {})
	check.call(palette.size() == SOURCE_THEMES and dynamic_themes.size() == SOURCE_THEMES,
		"both native theme tables carry all 54 themes")
	var drifting: Array = []
	var fallback_variant: Array = []
	for key in meta:
		var row: Dictionary = meta[key]
		var native: Dictionary = dynamic_themes.get(key, {})
		var theme: Dictionary = native.get("theme", {})
		if String(theme.get("name", "")) != String(row.get("name", "")):
			drifting.append(key)
		elif String(theme.get("boss_identity", "")) != String(row.get("boss_identity", "")):
			drifting.append(key)
		elif String(theme.get("particle_type", "")) != String(row.get("particle_type", "")):
			drifting.append(key)
		elif theme.size() != int(row.get("key_count", 0)):
			drifting.append(key)
		var particle := String(row.get("particle_type", ""))
		if not PARTICLE_TYPES.has(particle):
			fallback_variant.append(key)
	check.call(drifting.is_empty(),
		"all 54 theme names, boss identities, particle types and key counts match: %s"
		% str(drifting))
	check.call(fallback_variant.is_empty(),
		"every theme particle type is one of the seven the layout knows: %s"
		% str(fallback_variant))
	var fallback: Dictionary = source.get("fallback", {})
	check.call(bool(fallback.get("equals_forest", false))
		and bool(fallback.get("known_returns_self", false)),
		"get_theme falls back to FOREST_THEME for unknown names")
	var missing := TerrainPalette.for_theme("__missing__")
	var forest := TerrainPalette.for_theme("forest")
	var desert: Dictionary = palette.get("desert", {})
	var forest_row: Dictionary = palette.get("forest", {})
	var expected_desert := {}
	for key in desert:
		var rgb: Array = desert[key]
		expected_desert[key] = Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
	check.call(_same(missing, forest)
		and _same(TerrainPalette.for_theme("desert"), expected_desert),
		"the native palette lookup keeps the same forest fallback")
	check.call(forest_row.size() == 25,
		"theme_palette.json keeps the 25 colour keys per theme")


func _check_geometry(check: Callable, source: Dictionary) -> void:
	var generators: Dictionary = source.get("generators", {})
	var lanes: Array = generators.get("lane_points", [])
	var native := LaneLayout.create_paths()
	check.call(native.size() == lanes.size() and lanes.size() == 3,
		"generate_lanes returns the three lanes")
	if native.size() != lanes.size():
		return
	var drifting: Array = []
	for index in range(lanes.size()):
		var expected: Array = lanes[index]
		var curve: PackedVector2Array = native[index]
		if curve.size() != expected.size():
			drifting.append("%s size %d" % [LaneLayout.NAMES[index], curve.size()])
			continue
		for point in range(expected.size()):
			var pair: Array = expected[point]
			if curve[point] != Vector2(int(pair[0]), int(pair[1])):
				drifting.append("%s@%d" % [LaneLayout.NAMES[index], point])
				break
	check.call(drifting.is_empty(),
		"LaneLayout.create_paths() matches the executed source spline: %s" % str(drifting))
	var river: Dictionary = generators.get("river", {})
	var points: Array = river.get("points", [])
	var native_river := TerrainPalette.river_path()
	check.call(native_river.size() == points.size() and points.size() == 61,
		"the river is the 61-point source spline")
	var river_drift := false
	if native_river.size() == points.size():
		for index in range(points.size()):
			var pair: Array = points[index]
			river_drift = river_drift or native_river[index] != Vector2(int(pair[0]), int(pair[1]))
	check.call(not river_drift,
		"river_path.json equals the executed source points")


func _check_decorations(check: Callable, source: Dictionary) -> void:
	var generators: Dictionary = source.get("generators", {})
	var decorations: Dictionary = generators.get("decorations", {})
	var dynamic: Dictionary = _json(DYNAMIC)
	var layout: Dictionary = dynamic.get("layout", {})
	check.call(decorations.size() == 14,
		"DecorationGenerator.generate_all() returns fourteen arrays")
	var counts: Dictionary = generators.get("counts", {})
	var expected_counts := {
		"ancient_ruins": 4, "bones": 4, "boss_landmarks": 30, "crystals_blue": 4,
		"crystals_red": 2, "dark_bushes": 3, "dark_trees": 8, "dead_trees": 5,
		"glow_flowers": 6, "gravestones": 1, "mushrooms_dark": 6, "rocks_mossy": 8,
		"spike_traps": 2, "torch_stones": 18,
	}
	check.call(_same(counts, expected_counts),
		"seed 42 places the same 14 decoration counts as the source run")
	var drifting: Array = []
	for key in layout:
		if key == "river_points":
			continue
		if not _same(layout[key], decorations.get(key)):
			drifting.append(key)
	check.call(drifting.is_empty(),
		"the four runtime-read decoration arrays match the source seed: %s" % str(drifting))
	check.call(layout.size() == 5 and layout.has("river_points"),
		"map_dynamic.json carries the five layout arrays the renderer needs")
	var reads: Array = source.get("decoration_reads", [])
	check.call(reads == ["bones", "boss_landmarks", "crystals_blue", "gravestones",
		"rocks_mossy", "torch_stones"],
		"the live renderer reads exactly six decoration arrays: %s" % str(reads))
	check.call(source.get("bake_only_arrays", []) == ["boss_landmarks", "crystals_blue"],
		"boss_landmarks and crystals_blue are the two bake-only arrays")
	check.call(bool(generators.get("repeatable", false)),
		"generate_all() is repeatable because it seeds 42 explicitly")


func _check_seeds(check: Callable, source: Dictionary) -> void:
	var seeds: Array = source.get("seeds", [])
	var arguments: Array = []
	var kinds: Array = []
	for entry in seeds:
		var row: Dictionary = entry
		arguments.append(String(row.get("argument", "")))
		kinds.append(String(row.get("kind", "")))
	check.call(arguments == ["42", "", "100", ""],
		"the folder seeds twice with fixed values and reseeds entropy twice: %s"
		% str(arguments))
	check.call(kinds == ["fixed", "entropy", "fixed", "entropy"],
		"seed kinds are classified per site: %s" % str(kinds))
	var generators: Dictionary = source.get("generators", {})
	check.call(int(generators.get("seed", 0)) == 42,
		"the decoration layout is pinned at seed 42")
	var arrays: Array = source.get("runtime_arrays", [])
	check.call(arrays == ["bones", "boss_landmarks", "crystals_blue", "dire_shop_pos",
		"gravestones", "map_height", "map_width", "radiant_shop_pos", "river_points",
		"rocks_mossy", "torch_stones"],
		"the runtime reads eleven renderer fields: %s" % str(arrays))


func _check_aliases(check: Callable, source: Dictionary) -> void:
	var aliases: Dictionary = source.get("aliases", {})
	var aliased: Array = aliases.get("aliased", [])
	check.call(aliased == ["generators", "static_renderer", "shop_renderer",
		"palettes", "themes", "dynamic_renderer", "decoration_renderer"],
		"__init__.py re-registers all seven module names in sys.modules")
	var extra: Dictionary = aliases.get("extra", {})
	var plain: Dictionary = aliases.get("plain", {})
	var shop_symbols: Array = extra.get("shop_renderer", [])
	var static_symbols: Array = extra.get("static_renderer", [])
	check.call(extra.size() == 3 and plain.size() == 4,
		"three modules keep a namespace wrapper and four stay flat")
	check.call(shop_symbols.size() == 54 and static_symbols.size() == 5,
		"the alias tables keep their exact symbol counts")
	var reexports: Array = aliases.get("reexports", [])
	check.call(reexports.has("DecorationRenderer") and reexports.has("StaticRenderer")
		and reexports.has("ShopRenderer") and reexports.has("DynamicRenderer")
		and reexports.has("PathGenerator") and reexports.has("DecorationGenerator"),
		"the shim re-exports the six renderer classes: %s" % str(reexports))


func _check_classification(check: Callable, source: Dictionary) -> void:
	var entries: Dictionary = source.get("classification", {})
	check.call(int(source.get("symbol_count", 0)) == SOURCE_SYMBOLS
		and entries.size() == SOURCE_SYMBOLS,
		"all 194 symbols of the folder carry a classification")
	var kinds: Dictionary = source.get("classification_kinds", {})
	check.call(int(kinds.get("native", 0)) == 31 and int(kinds.get("data", 0)) == 112
		and int(kinds.get("bake", 0)) == 39 and int(kinds.get("executed", 0)) == 9
		and int(kinds.get("meta", 0)) == 2 and int(kinds.get("internal", 0)) == 1,
		"the kind histogram is 31/112/39/9/2/1: %s" % str(kinds))
	check.call(source.get("stale_entries", []).is_empty(),
		"no classification entry points at a symbol the folder no longer has")
	var cache := {}
	var missing_file: Array = []
	var missing_token: Array = []
	var source_only: Array = []
	for name in entries:
		var entry: Dictionary = entries[name]
		var target := String(entry.get("target", ""))
		if not target.begins_with("godot_rebuild/"):
			# The two `__init__.py` entries live in the read-only Pygame oracle
			# above the Godot project; the validator checks those (9cb).
			source_only.append(name)
			continue
		var path := "res://" + target.trim_prefix("godot_rebuild/")
		if not cache.has(path):
			var text := FileAccess.get_file_as_string(path)
			cache[path] = text
			if text.is_empty():
				missing_file.append(target)
		var token := String(entry.get("token", ""))
		var body: String = cache[path]
		if not missing_file.has(target) and not body.contains(token):
			missing_token.append("%s -> %s" % [name, token])
	check.call(source_only.size() == 2,
		"only the two shim entries live outside the Godot project: %s" % str(source_only))
	check.call(missing_file.is_empty(),
		"every classification target exists in the Godot tree: %s" % str(missing_file))
	check.call(missing_token.is_empty(),
		"every classification token is present in its target: %s" % str(missing_token))


func _check_bakes(check: Callable, source: Dictionary) -> void:
	var overlay: Dictionary = _json(OVERLAY)
	var base: Dictionary = _json(BASE)
	var overlay_themes: Dictionary = overlay.get("themes", {})
	var base_themes: Dictionary = base.get("themes", {})
	check.call(overlay_themes.size() == SOURCE_THEMES and base_themes.size() == SOURCE_THEMES,
		"the decoration overlay and the base bake cover all 54 themes")
	var bad_overlay: Array = []
	for key in overlay_themes:
		var row: Dictionary = overlay_themes[key]
		if String(row.get("sha256", "")).length() != 64 or int(row.get("bytes", 0)) <= 0:
			bad_overlay.append(key)
	check.call(bad_overlay.is_empty(),
		"every overlay carries a sha256 and a size: %s" % str(bad_overlay))
	check.call(MapArt.themes().size() == SOURCE_THEMES
		and MapArt.base_themes().size() == SOURCE_THEMES,
		"map_art.gd exposes the 54 overlays and the 54 bases")
	var theme_table: Dictionary = source.get("themes", {})
	var themes: Array = theme_table.get("names", [])
	var untextured: Array = []
	for name in themes:
		if not MapArt.has_overlay(String(name)) or not MapArt.has_base(String(name)):
			untextured.append(name)
	check.call(untextured.is_empty(),
		"every source theme resolves to an overlay and a base: %s" % str(untextured))


func _check_native_tokens(check: Callable) -> void:
	var layout := FileAccess.get_file_as_string(LAYOUT_GD)
	var identities: Array = []
	for identity in BOSS_IDENTITIES:
		if layout.contains('"%s"' % identity):
			identities.append(identity)
	check.call(identities.size() == BOSS_IDENTITIES.size(),
		"the layout carries the four source boss identities: %s" % str(identities))
	check.call(layout.contains("Haunted Veil") and layout.contains('"krobellus"'),
		"the Haunted Veil theme still overrides its identity to krobellus")
	var particles: Array = []
	for particle in PARTICLE_TYPES:
		if layout.contains('"%s"' % particle):
			particles.append(particle)
	check.call(particles.size() == PARTICLE_TYPES.size(),
		"all seven particle types survive in the layout: %s" % str(particles))
	var palette_source := FileAccess.get_file_as_string(PALETTE_GD)
	check.call(palette_source.contains("palettes.get(\"forest\""),
		"terrain_palette.gd keeps the forest fallback of get_theme")
	check.call(DynamicMap.themes().size() == SOURCE_THEMES,
		"the dynamic renderer lists the same 54 themes")
	check.call(FileAccess.file_exists(RIVER) and FileAccess.file_exists(MAP_PALETTE),
		"the river path and the palette data ship with the project")
