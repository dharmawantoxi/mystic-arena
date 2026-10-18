extends RefCounted
## Layer 9bj: baked source art for the map layers Godot does not rasterise.
## `MapRenderer._render_static_map` paints terrain, river and lanes (layers 1-3,
## native tiles), then `DecorationRenderer.draw_all` (4) and `ShopRenderer.draw`
## (5), then the border wall (6). `bake/bake_map_overlay.py` runs layers 4-5 of the
## original pygame code once per theme and stores every pixel they change, so
## this overlay drawn over the layer 1-3 base reproduces the source composite.

const ROOT := "res://assets/art/map/"
const MANIFEST := "res://data/art/map_overlay.json"
const SIZE := Vector2i(1280, 720)
static var _manifest: Dictionary = {}
static var _textures: Dictionary = {}


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if parsed is Dictionary:
			_manifest = parsed
	return _manifest


static func themes() -> Array:
	var listed: Dictionary = manifest().get("themes", {})
	var names: Array = listed.keys()
	names.sort()
	return names


static func overlay_path(theme: String) -> String:
	return ROOT + theme + ".png"


static func has_overlay(theme: String) -> bool:
	var listed: Dictionary = manifest().get("themes", {})
	return listed.has(theme)


## The theme's baked overlay, or null when the theme is unknown or not imported.
static func overlay_texture(theme: String) -> Texture2D:
	if not has_overlay(theme):
		return null
	if not _textures.has(theme):
		var texture: Texture2D = null
		if ResourceLoader.exists(overlay_path(theme)):
			texture = load(overlay_path(theme)) as Texture2D
		_textures[theme] = texture
	var cached: Variant = _textures[theme]
	return cached as Texture2D
