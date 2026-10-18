extends RefCounted
## Layer 9bj: the baked decoration + shop overlays (`bake/bake_map_overlay.py`).
## Every theme the 54 levels use ships one overlay PNG; the manifest pins its
## size and covered-pixel count, and the view paints it between the lanes and the
## border wall exactly like `MapRenderer._render_static_map` layers 4-5.

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
	var tint := base.find("_draw_map_overlay()", wall)
	check.call(
		lane != -1 and lane < decor and decor < wall and wall < tint,
		"Decor sits over the lanes and under the border wall and the tint"
	)
