class_name MapRenderer
extends RefCounted
## State-only port of `_render.py::MapRenderer`.
##
## The source coordinator delegates static and dynamic pixel drawing to pygame
## renderer components. That drawing is intentionally not ported. This class
## keeps generated map data, theme/shop state, hit-testing and presentation
## readiness available through getters.

const MAP_WIDTH := 1280
const MAP_HEIGHT := 720
const SHOP_SIZE := 60
const SpriteCache = preload("res://scripts/ui/sprite_cache.gd")
const RenderCache = preload("res://scripts/ui/render_cache.gd")
const STATIC_LAYERS := [
	"terrain",
	"terrain_details",
	"river",
	"lane",
	"lane",
	"lane",
	"decorations",
	"shops",
	"border_wall",
]

var screen: Variant
var map_width := MAP_WIDTH
var map_height := MAP_HEIGHT
var theme_name := "forest"
var theme: Dictionary = {}
var radiant_shop_pos: Array = [340, 540]
var dire_shop_pos: Array = [940, 180]
var shop_size := SHOP_SIZE
var top_lane_points: Array = []
var mid_lane_points: Array = []
var bot_lane_points: Array = []
var river_points: Array = []
var decoration_data: Dictionary = {}
var static_map_ready := false
var dynamic_ready := false


## The lane/river/decoration arguments are the source-oracle replay seam. In
## the running Godot rebuild, a map data provider can pass generated values;
## no pygame renderer or pixel surface is required here.
func configure(
	requested_theme: String = "forest",
	lane_data: Dictionary = {},
	river_data: Array = [],
	decorations: Dictionary = {},
	theme_data: Dictionary = {}
) -> void:
	theme_name = requested_theme
	theme = theme_data.duplicate(true)
	if theme.is_empty():
		theme = {"name": theme_name, "ambient_tint": null}
	if lane_data.is_empty():
		top_lane_points = []
		mid_lane_points = []
		bot_lane_points = []
	else:
		top_lane_points = (lane_data.get("top", []) as Array).duplicate(true)
		mid_lane_points = (lane_data.get("mid", []) as Array).duplicate(true)
		bot_lane_points = (lane_data.get("bot", []) as Array).duplicate(true)
	river_points = river_data.duplicate(true)
	decoration_data = decorations.duplicate(true)
	static_map_ready = true
	dynamic_ready = true


func get_lane_path(lane_name: String) -> Array:
	if lane_name == "top":
		return top_lane_points.duplicate(true)
	if lane_name == "mid":
		return mid_lane_points.duplicate(true)
	if lane_name == "bot":
		return bot_lane_points.duplicate(true)
	return []


func get_shop_positions() -> Dictionary:
	return {
		"radiant": radiant_shop_pos.duplicate(),
		"dire": dire_shop_pos.duplicate(),
		"size": shop_size,
	}


func is_click_on_shop(mx: float, my: float) -> bool:
	for position in [radiant_shop_pos, dire_shop_pos]:
		if _distance_to(position, mx, my) <= float(shop_size):
			return true
	return false


func get_clicked_shop(mx: float, my: float) -> Variant:
	for entry in [
		{"label": "item", "position": radiant_shop_pos},
		{"label": "hero", "position": dire_shop_pos},
	]:
		var position: Array = entry["position"]
		if _distance_to(position, mx, my) <= float(shop_size):
			return entry["label"]
	return null


func get_state() -> Dictionary:
	return {
		"map_width": map_width,
		"map_height": map_height,
		"theme_name": theme_name,
		"theme": theme.duplicate(true),
		"shop_positions": get_shop_positions(),
		"lanes":
		{
			"top": top_lane_points.duplicate(true),
			"mid": mid_lane_points.duplicate(true),
			"bot": bot_lane_points.duplicate(true),
		},
		"river": river_points.duplicate(true),
		"decorations": decoration_data.duplicate(true),
		"static_layers": STATIC_LAYERS.duplicate(),
		"static_map_ready": static_map_ready,
		"dynamic_ready": dynamic_ready,
	}


func get_decoration_state() -> Dictionary:
	return decoration_data.duplicate(true)


func cache_theme_assets(
	sprite_cache: SpriteCache = null, render_cache: RenderCache = null
) -> Dictionary:
	var sc: SpriteCache = sprite_cache if sprite_cache != null else SpriteCache.get_shared()
	var rc: RenderCache = render_cache if render_cache != null else RenderCache.get_shared()
	var static_surface: Variant = sc.get_or_render(
		["map_static", theme_name], map_width, map_height, Callable(self, "_render_static_map")
	)
	var item_shop_badge: Variant = sc.get_or_render(
		["shop_badge", "item", theme_name],
		shop_size * 2,
		shop_size * 2,
		Callable(self, "_render_item_shop_badge")
	)
	var hero_shop_badge: Variant = sc.get_or_render(
		["shop_badge", "hero", theme_name],
		shop_size * 2,
		shop_size * 2,
		Callable(self, "_render_hero_shop_badge")
	)
	var radiant_glow: Variant = rc.get_glow_surface(shop_size, [115, 203, 187], 5)
	var dire_glow: Variant = rc.get_glow_surface(shop_size, [215, 133, 121], 5)
	var shop_font: Variant = rc.get_font(16, "title", true)
	return {
		"static_map": sc.get_surface_snapshot(static_surface),
		"item_shop_badge": sc.get_surface_snapshot(item_shop_badge),
		"hero_shop_badge": sc.get_surface_snapshot(hero_shop_badge),
		"radiant_glow": rc.get_surface_snapshot(radiant_glow),
		"dire_glow": rc.get_surface_snapshot(dire_glow),
		"shop_font": rc.get_font_snapshot(shop_font),
	}


func _render_static_map(surface: Variant) -> void:
	if surface is Dictionary:
		var dict: Dictionary = surface
		dict["marker"] = "map_static:%s" % theme_name
		dict["bounds"] = [0, 0, map_width, map_height]


func _render_item_shop_badge(surface: Variant) -> void:
	if surface is Dictionary:
		var dict: Dictionary = surface
		dict["marker"] = "shop_badge:item:%s" % theme_name
		dict["bounds"] = [0, 0, shop_size * 2, shop_size * 2]


func _render_hero_shop_badge(surface: Variant) -> void:
	if surface is Dictionary:
		var dict: Dictionary = surface
		dict["marker"] = "shop_badge:hero:%s" % theme_name
		dict["bounds"] = [0, 0, shop_size * 2, shop_size * 2]


func _distance_to(position: Array, mx: float, my: float) -> float:
	var dx: float = mx - float(position[0])
	var dy: float = my - float(position[1])
	return sqrt(dx * dx + dy * dy)
