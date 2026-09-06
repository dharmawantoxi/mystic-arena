# ArenaMap.gd — Port dari map_components/ + _render.MapRenderer
# Di Pygame: 6 layer blit manual (terrain, river, lane, decor, shop, wall) + cache static_map
# Di Godot: TileMapLayer GPU + Parallax + Light2D — 0 blit manual, semua batched
extends Node2D

@export var theme_name: String = "forest"
@onready var ground: TileMapLayer = $Ground
@onready var river: TileMapLayer = $River
@onready var lanes: TileMapLayer = $Lanes
@onready var decor: TileMapLayer = $Decor
@onready var light: DirectionalLight2D = $SunLight
@onready var canvas_modulate: CanvasModulate = $CanvasModulate

# Shop positions (mirip _render.py radiant/dire)
var radiant_shop_pos := Vector2(340, 540)
var dire_shop_pos := Vector2(940, 180)

func _ready():
	apply_theme(theme_name)

func apply_theme(t: String):
	theme_name = t
	# Theme -> Godot TileSet + modulate + light color
	# Contoh forest: ground TileSet forest.tres, light warm
	var theme_data = {
		"forest": {"modulate": Color(1,1,1), "light": Color(1,0.95,0.9,1), "energy": 0.85},
		"desert": {"modulate": Color(1,0.92,0.75), "light": Color(1,0.85,0.6,1), "energy": 1.1},
		"ice": {"modulate": Color(0.85,0.9,1), "light": Color(0.7,0.85,1,1), "energy": 0.9},
		"abyss": {"modulate": Color(1,0.75,0.75), "light": Color(1,0.5,0.5,1), "energy": 0.6},
	}
	var d = theme_data.get(t, theme_data["forest"])
	if canvas_modulate:
		canvas_modulate.color = Color(d["modulate"].r, d["modulate"].g, d["modulate"].b, 1.0)
	if light:
		light.color = d["light"]
		light.energy = d["energy"]
	# Load TileSet tema kalau ada
	var ts_path = "res://assets/tilesets/%s.tres" % t
	if ResourceLoader.exists(ts_path) and ground:
		ground.tile_set = load(ts_path)

func get_lane_path(lane: String) -> PackedVector2Array:
	# Port PathGenerator.generate_lanes — sekarang jadi Curve2D resource
	var curve_path = "res://data/paths/%s.tres" % lane
	if ResourceLoader.exists(curve_path):
		var curve: Curve2D = load(curve_path)
		return curve.get_baked_points()
	return PackedVector2Array()
