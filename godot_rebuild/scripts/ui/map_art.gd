extends RefCounted
## Layer 9bj: baked source art for the map layers Godot does not rasterise.
## `MapRenderer._render_static_map` paints terrain, river and lanes (layers 1-3,
## baked by 9bj2 below; native tiles before), then `DecorationRenderer.draw_all`
## (4) and `ShopRenderer.draw` (5), then the border wall (6).
## `bake/bake_map_overlay.py` runs layers 4-5 of the original pygame code once per
## theme and stores every pixel they change, so this overlay drawn over the layer
## 1-3 base reproduces the source composite.

const ROOT := "res://assets/art/map/"
const MANIFEST := "res://data/art/map_overlay.json"
const SIZE := Vector2i(1280, 720)
## Layer 9bj2: the baked base (layers 1-3) and border wall (layer 6).
const BASE_ROOT := "res://assets/art/map_base/"
const BASE_MANIFEST := "res://data/art/map_base.json"
const WALL_NAME := "border_wall"
static var _manifest: Dictionary = {}
static var _textures: Dictionary = {}
static var _base_manifest: Dictionary = {}


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


# ── Layer 9bj2: the baked source base (layers 1-3) and border wall (layer 6) ──
# `bake/bake_map_base.py` renders layers 1-3 with the same seed the overlay above
# was composed against and proves base + overlay + wall == the source static map,
# so the view no longer needs its native tile rasters when these are imported.
# Textures are not kept here: the view holds the current theme's, so a long
# session does not pin every map in memory.


static func base_manifest() -> Dictionary:
	if _base_manifest.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(BASE_MANIFEST))
		if parsed is Dictionary:
			_base_manifest = parsed
	return _base_manifest


static func base_themes() -> Array:
	var listed: Dictionary = base_manifest().get("themes", {})
	var names: Array = listed.keys()
	names.sort()
	return names


static func base_path(theme: String) -> String:
	return BASE_ROOT + theme + ".png"


static func wall_path() -> String:
	return BASE_ROOT + WALL_NAME + ".png"


static func has_base(theme: String) -> bool:
	var listed: Dictionary = base_manifest().get("themes", {})
	return listed.has(theme)


## The theme's baked terrain, river and lanes, or null when unknown or not imported.
static func base_texture(theme: String) -> Texture2D:
	if not has_base(theme) or not ResourceLoader.exists(base_path(theme)):
		return null
	return load(base_path(theme)) as Texture2D


## The baked border wall (the source ignores the theme), or null when not imported.
static func wall_texture() -> Texture2D:
	if base_manifest().get("wall", {}).is_empty() or not ResourceLoader.exists(wall_path()):
		return null
	return load(wall_path()) as Texture2D
