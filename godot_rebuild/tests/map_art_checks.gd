extends RefCounted
## Layer 9bj: the baked decoration + shop overlays (`bake/bake_map_overlay.py`).
## Every theme the 54 levels use ships one overlay PNG; the manifest pins its
## size and covered-pixel count, and the view paints it between the lanes and the
## border wall exactly like `MapRenderer._render_static_map` layers 4-5.
## Layer 9bj2 adds the baked base (layers 1-3, `bake/bake_map_base.py`) and the
## border wall (layer 6) that replace the native tile rasters in the view.

const MapArt = preload("res://scripts/ui/map_art.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const PALETTE := "res://data/levels/theme_palette.json"
const MINION_VIEW := "res://scenes/combat/minion_view.gd"


func run(check: Callable) -> void:
	var manifest := MapArt.manifest()
	check.call(not manifest.is_empty(), "Map overlay manifest parses")
	_check_manifest(check, manifest)
	_check_files(check, manifest)
	_check_textures(check)
	_check_view_wiring(check)
	_check_base_manifest(check)
	_check_base_files(check)
	_check_base_textures(check)
	_check_base_view(check)


func _check_manifest(check: Callable, manifest: Dictionary) -> void:
	var palette: Variant = JSON.parse_string(FileAccess.get_file_as_string(PALETTE))
	check.call(palette is Dictionary, "Theme palette parses")
	if not (palette is Dictionary):
		return
	var palette_themes: Array = (palette as Dictionary).keys()
	palette_themes.sort()
	check.call(MapArt.themes() == palette_themes, "One baked overlay per palette theme")
	check.call(MapArt.themes().size() == 54, "54 map themes ship an overlay")
	check.call(
		Vector2i(MapArt.SIZE) == Vector2i(1280, 720), "Overlays cover the 1280x720 source map"
	)
	check.call(String(manifest.get("generator", "")).ends_with("bake_map_overlay.py"), "Generator")
	check.call(MapArt.overlay_texture("not_a_theme") == null, "Unknown themes have no overlay")


func _check_files(check: Callable, manifest: Dictionary) -> void:
	var listed: Dictionary = manifest.get("themes", {})
	var missing: Array = []
	var wrong_size: Array = []
	var thin: Array = []
	for theme in MapArt.themes():
		var entry: Dictionary = listed[theme]
		var path := MapArt.overlay_path(String(theme))
		if not FileAccess.file_exists(path):
			missing.append(theme)
			continue
		var image := Image.load_from_file(path)
		if image == null or image.get_size() != Vector2i(MapArt.SIZE):
			wrong_size.append(theme)
		if int(entry.get("covered_pixels", 0)) < 10000:
			thin.append(theme)
	check.call(missing.is_empty(), "Every overlay PNG exists: %s" % str(missing))
	check.call(wrong_size.is_empty(), "Every overlay decodes at 1280x720: %s" % str(wrong_size))
	check.call(thin.is_empty(), "Every overlay covers real decoration pixels: %s" % str(thin))


func _check_textures(check: Callable) -> void:
	for theme in ["forest", "haunted", "volcanic"]:
		var texture := MapArt.overlay_texture(theme)
		check.call(texture != null, "The %s overlay loads as a texture" % theme)
		if texture != null:
			check.call(
				texture.get_size() == Vector2(MapArt.SIZE), "The %s texture is 1280x720" % theme
			)
	var first := MapArt.overlay_texture("forest")
	var second := MapArt.overlay_texture("forest")
	check.call(first == second, "The overlay texture is cached per theme")


func _check_view_wiring(check: Callable) -> void:
	var view := PrototypeView.new()
	check.call(view.has_method("_draw_map_decor"), "The prototype view overrides the decor hook")
	view.free()
	var base := FileAccess.get_file_as_string(MINION_VIEW)
	var lane := base.find("draw_texture(lane_texture")
	var decor := base.find("_draw_map_decor()", lane)
	var wall := base.find("draw_texture(wall_texture")
	var dynamic := base.find("_draw_map_dynamic()", wall)
	var tint := base.find("_draw_map_overlay()", dynamic)
	check.call(
		lane != -1 and lane < decor and decor < wall and wall < dynamic and dynamic < tint,
		"Decor, wall, DynamicRenderer, then tint follow the source order"
	)


func _check_base_manifest(check: Callable) -> void:
	var manifest := MapArt.base_manifest()
	check.call(not manifest.is_empty(), "Map base manifest parses")
	check.call(MapArt.base_themes() == MapArt.themes(), "One baked base per overlay theme")
	check.call(
		String(manifest.get("generator", "")).ends_with("bake_map_base.py"), "Map base generator"
	)
	check.call(
		String(manifest.get("seed", "")) == "{theme}:base",
		"The base keeps the seed the overlays were composed against"
	)
	check.call(MapArt.base_texture("not_a_theme") == null, "Unknown themes have no baked base")


func _check_base_files(check: Callable) -> void:
	var listed: Dictionary = MapArt.base_manifest().get("themes", {})
	var broken: Array = []
	var off_probe: Array = []
	for theme in MapArt.base_themes():
		var image := Image.load_from_file(MapArt.base_path(String(theme)))
		if (
			image == null
			or image.get_size() != MapArt.SIZE
			or image.detect_alpha() != Image.ALPHA_NONE
		):
			broken.append(theme)
			continue
		for probe in listed[theme].get("probes", []):
			var rgb: Array = probe[2]
			var pixel := image.get_pixel(int(probe[0]), int(probe[1]))
			if [pixel.r8, pixel.g8, pixel.b8] != [int(rgb[0]), int(rgb[1]), int(rgb[2])]:
				off_probe.append("%s@%d,%d" % [theme, int(probe[0]), int(probe[1])])
	check.call(broken.is_empty(), "Every base decodes as an opaque 1280x720 map: %s" % str(broken))
	check.call(
		off_probe.is_empty(), "Every base holds the source probe pixels: %s" % str(off_probe)
	)
	var wall := Image.load_from_file(MapArt.wall_path())
	var framed := wall != null and wall.get_size() == MapArt.SIZE
	check.call(framed, "The baked border wall decodes at 1280x720")
	if framed:
		check.call(
			wall.get_pixel(0, 0).a8 == 255 and wall.get_pixel(640, 360).a8 == 0,
			"The border wall frames the map and leaves the arena clear"
		)


func _check_base_textures(check: Callable) -> void:
	for theme in ["forest", "desert", "volcanic"]:
		var texture := MapArt.base_texture(theme)
		check.call(
			texture != null and texture.get_size() == Vector2(MapArt.SIZE),
			"The %s base loads as a 1280x720 texture" % theme
		)
	var wall := MapArt.wall_texture()
	check.call(
		wall != null and wall.get_size() == Vector2(MapArt.SIZE),
		"The border wall loads as a 1280x720 texture"
	)


func _check_base_view(check: Callable) -> void:
	var view := PrototypeView.new()
	view.cache_static_map("haunted")
	check.call(
		(
			view.baked_static_base
			and view.terrain_texture == MapArt.base_texture("haunted")
			and view.river_texture == null
			and view.lane_texture == null
			and view.cached_river_theme == "haunted"
		),
		"The view caches the baked base instead of the native tile rasters"
	)
	check.call(
		view.wall_texture != null and view.wall_texture == MapArt.wall_texture(),
		"The view paints the baked border wall"
	)
	view.free()
	var base := FileAccess.get_file_as_string(MINION_VIEW)
	var guard := base.find("if not baked_static_base:")
	check.call(
		(
			guard != -1
			and guard < base.find("draw_texture(river_texture")
			and base.find("draw_texture(lane_texture") < base.find("_draw_map_decor()")
		),
		"The baked base skips the native river and lanes and stays under the decor"
	)
