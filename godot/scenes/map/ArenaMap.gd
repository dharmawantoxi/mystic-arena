# ArenaMap.gd — Port dari map_components/ + _render.MapRenderer
# Di Pygame: 6 layer blit manual (terrain, river, lane, decor, shop, wall) + cache static_map
# Di Godot: TileMapLayer GPU + Parallax + Light2D — 0 blit manual, semua batched
#
# PENTING (kenapa dulu layar hitam): TileMapLayer Ground/River/Lanes/Decor belum
# punya TileSet (res://assets/tilesets/*.tres belum dibuat — Fase 3 roadmap), jadi
# scene utama tidak menggambar apa-apa sama sekali. Sementara TileSet belum ada,
# map digambar prosedural di _draw() memakai palette ASLI dari
# map_components/themes.py (FOREST/DESERT/ICE/ABYSS) + lane path dari
# PathGenerator.generate_lanes(). Begitu TileSet di-assign, fallback otomatis mati.
extends Node2D

## Tema level (forest/desert/ice/abyss) — diisi dari levels.json["map_theme"]
@export var theme_name: String = "forest"
## Ukuran arena — paritas _core.SCREEN_WIDTH/SCREEN_HEIGHT
@export var arena_size: Vector2 = Vector2(1280, 720)
## true = gambar fallback prosedural; otomatis false begitu Ground punya TileSet
@export var procedural_fallback: bool = true

@onready var ground: TileMapLayer = $Ground
@onready var river: TileMapLayer = $River
@onready var lanes: TileMapLayer = $Lanes
@onready var decor: TileMapLayer = $Decor
@onready var light: DirectionalLight2D = $SunLight
@onready var canvas_modulate: CanvasModulate = $CanvasModulate

# Shop positions (mirip _render.py radiant/dire)
var radiant_shop_pos := Vector2(340, 540)
var dire_shop_pos := Vector2(940, 180)

# Base positions (paritas _core.BLUE_BASE_X/Y, RED_BASE_X/Y)
const BLUE_BASE := Vector2(100, 620)
const RED_BASE := Vector2(1180, 100)

# Lebar jalur (paritas StaticRenderer.draw_lane: lane_width=42, radius = 42/2+4)
const LANE_HALF_WIDTH := 25.0
const RIVER_HALF_WIDTH := 30.0
const TILE := 40.0 # ukuran "tile" ditheran prosedural

# ═══ PALETTE — dipindah dari map_components/themes.py (radiant_grass_*, dire_earth_*,
# path_stone_*, river_*) supaya fallback warna = palette game asli, bukan asal pilih.
const THEMES: Dictionary = {
	"forest": {
		"modulate": Color(1, 1, 1), "light": Color(1, 0.95, 0.9, 1), "energy": 0.85,
		"grass_dark": Color("#1c3720"), "grass_mid": Color("#26482a"),
		"grass": Color("#345c37"), "grass_light": Color("#447346"),
		"moss": Color("#375a28"),
		"earth_dark": Color("#2d201c"), "earth": Color("#412d26"),
		"earth_light": Color("#553c30"), "ash": Color("#3c3732"),
		"path": Color("#554c41"), "path_light": Color("#73695a"),
		"path_bright": Color("#91826c"), "path_border": Color("#3a342d"),
		"river": Color("#230c22"), "river_dark": Color("#080812"),
		"river_glow": Color("#b12e4b"), "river_foam": Color("#ff828c"),
		"tree": Color("#19371e"), "tree_light": Color("#2d5a32"),
		"stone": Color("#555046"),
	},
	"desert": {
		"modulate": Color(1, 0.92, 0.75), "light": Color(1, 0.85, 0.6, 1), "energy": 1.1,
		"grass_dark": Color("#9b733c"), "grass_mid": Color("#b4874b"),
		"grass": Color("#d2a55f"), "grass_light": Color("#e6be78"),
		"moss": Color("#8c6e37"),
		"earth_dark": Color("#5f371e"), "earth": Color("#7d4b28"),
		"earth_light": Color("#965f37"), "ash": Color("#af8c5a"),
		"path": Color("#91734b"), "path_light": Color("#b49164"),
		"path_bright": Color("#d7b482"), "path_border": Color("#6e5537"),
		"river": Color("#194f22"), "river_dark": Color("#081d12"),
		"river_glow": Color("#96dc44"), "river_foam": Color("#dcffa0"),
		"tree": Color("#785f2d"), "tree_light": Color("#a08246"),
		"stone": Color("#aa966e"),
	},
	"ice": {
		"modulate": Color(0.85, 0.9, 1), "light": Color(0.7, 0.85, 1, 1), "energy": 0.9,
		"grass_dark": Color("#b4c8dc"), "grass_mid": Color("#c8dceb"),
		"grass": Color("#dcebf5"), "grass_light": Color("#ebf5fa"),
		"moss": Color("#96b4d2"),
		"earth_dark": Color("#3c5069"), "earth": Color("#556982"),
		"earth_light": Color("#6e87a0"), "ash": Color("#96afc8"),
		"path": Color("#7d91aa"), "path_light": Color("#a0b4cd"),
		"path_bright": Color("#c3d7eb"), "path_border": Color("#5a6e87"),
		"river": Color("#326496"), "river_dark": Color("#14325a"),
		"river_glow": Color("#aadcff"), "river_foam": Color("#e6f5ff"),
		"tree": Color("#7896b4"), "tree_light": Color("#aac8e1"),
		"stone": Color("#96a5b9"),
	},
	"abyss": {
		"modulate": Color(1, 0.75, 0.75), "light": Color(1, 0.5, 0.5, 1), "energy": 0.6,
		"grass_dark": Color("#050406"), "grass_mid": Color("#0c080a"),
		"grass": Color("#160e10"), "grass_light": Color("#231416"),
		"moss": Color("#120a0c"),
		"earth_dark": Color("#020203"), "earth": Color("#080506"),
		"earth_light": Color("#100a0c"), "ash": Color("#1e1012"),
		"path": Color("#140e0e"), "path_light": Color("#281918"),
		"path_bright": Color("#412823"), "path_border": Color("#080607"),
		"river": Color("#550f0f"), "river_dark": Color("#190508"),
		"river_glow": Color("#f04b2d"), "river_foam": Color("#ff9150"),
		"tree": Color("#0a0608"), "tree_light": Color("#1c1012"),
		"stone": Color("#281c1a"),
	},
}

var _decor_points: PackedFloat32Array = PackedFloat32Array() # [x, y, size, kind] x N
var _lane_cache: Dictionary = {}

func _ready():
	z_index = -10 # map selalu di bawah unit/FX
	# Hero/Minion/Boss menanyakan posisi base + lane ke node ini lewat group,
	# jadi tidak ada koordinat arena yang di-hardcode di AI.
	add_to_group("arena_map")
	apply_theme(theme_name)

func apply_theme(t: String):
	theme_name = t
	var d = THEMES.get(t, THEMES["forest"])
	if canvas_modulate:
		canvas_modulate.color = Color(d["modulate"].r, d["modulate"].g, d["modulate"].b, 1.0)
	if light:
		light.color = d["light"]
		light.energy = d["energy"]
	# Load TileSet tema kalau ada (Fase 3). Kalau ketemu, fallback prosedural mundur
	# teratur supaya tidak ada gambar dobel.
	var ts_path = "res://assets/tilesets/%s.tres" % t
	if ResourceLoader.exists(ts_path) and ground:
		ground.tile_set = load(ts_path)
		procedural_fallback = false
	_build_decor()
	queue_redraw()

## Ganti ke tema berikutnya dalam palette (dipakai tombol debug T di Main.gd)
func cycle_theme() -> String:
	var names: Array = THEMES.keys()
	var idx := maxi(names.find(theme_name), 0)
	var nxt: String = names[(idx + 1) % names.size()]
	apply_theme(nxt)
	return nxt

# ═══ LANE PATH — port persis PathGenerator (map_components/generators.py) ═══
# waypoints sama dengan generate_lanes(map_w, map_h) versi pygame.
func get_lane_path(lane: String) -> PackedVector2Array:
	if _lane_cache.has(lane):
		return _lane_cache[lane]
	# Curve2D hasil bake (kalau nanti ada di data/paths) lebih dulu
	var curve_path = "res://data/paths/%s.tres" % lane
	if ResourceLoader.exists(curve_path):
		var curve: Curve2D = load(curve_path)
		var baked := curve.get_baked_points()
		_lane_cache[lane] = baked
		return baked
	var w := arena_size.x
	var h := arena_size.y
	var waypoints := PackedVector2Array()
	match lane:
		"top":
			waypoints = PackedVector2Array([
				Vector2(90, h - 130), Vector2(85, h - 260), Vector2(95, h - 380),
				Vector2(120, h - 500), Vector2(170, 180), Vector2(240, 100),
				Vector2(380, 75), Vector2(550, 70), Vector2(720, 75),
				Vector2(880, 85), Vector2(1030, 110), Vector2(w - 100, 180),
			])
		"bot":
			waypoints = PackedVector2Array([
				Vector2(130, h - 90), Vector2(260, h - 70), Vector2(420, h - 60),
				Vector2(600, h - 60), Vector2(780, h - 65), Vector2(940, h - 75),
				Vector2(1070, h - 100), Vector2(w - 110, h - 220),
				Vector2(w - 90, h - 380), Vector2(w - 85, 250), Vector2(w - 100, 180),
			])
		_: # "mid"
			waypoints = PackedVector2Array([
				Vector2(170, h - 170), Vector2(300, h - 300), Vector2(440, h - 400),
				Vector2(w / 2.0 - 60, h / 2.0 + 40), Vector2(w / 2.0, h / 2.0),
				Vector2(w / 2.0 + 60, h / 2.0 - 40), Vector2(w - 440, 400),
				Vector2(w - 300, 300), Vector2(w - 170, 170),
			])
	var baked := _curved_path(waypoints, 10)
	_lane_cache[lane] = baked
	return baked

func get_river_path() -> PackedVector2Array:
	if _lane_cache.has("river"):
		return _lane_cache["river"]
	var w := arena_size.x
	var h := arena_size.y
	var baked := _curved_path(PackedVector2Array([
		Vector2(0, 200), Vector2(150, 270), Vector2(350, 350),
		Vector2(w / 2.0, h / 2.0), Vector2(w - 350, h - 350),
		Vector2(w - 150, h - 270), Vector2(w, h - 200),
	]), 10)
	_lane_cache["river"] = baked
	return baked

# Catmull-Rom interpolation — port make_curved_path (smoothness=10)
static func _curved_path(waypoints: PackedVector2Array, smoothness: int = 10) -> PackedVector2Array:
	var out := PackedVector2Array()
	if waypoints.size() < 2:
		return waypoints.duplicate()
	var padded: Array = [waypoints[0]]
	for p in waypoints:
		padded.append(p)
	padded.append(waypoints[waypoints.size() - 1])
	for i in range(padded.size() - 3):
		var p0: Vector2 = padded[i]
		var p1: Vector2 = padded[i + 1]
		var p2: Vector2 = padded[i + 2]
		var p3: Vector2 = padded[i + 3]
		for step in smoothness:
			var t := float(step) / float(smoothness)
			var t2 := t * t
			var t3 := t2 * t
			var x := 0.5 * ((2.0 * p1.x) + (-p0.x + p2.x) * t
				+ (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2
				+ (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3)
			var y := 0.5 * ((2.0 * p1.y) + (-p0.y + p2.y) * t
				+ (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2
				+ (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3)
			out.append(Vector2(x, y))
	out.append(waypoints[waypoints.size() - 1])
	return out

# Titik dekor (pohon/batu) — deterministik seed 42 seperti DecorationGenerator.generate_all()
func _build_decor():
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	_decor_points.clear()
	var lane_pts := PackedVector2Array()
	for l in ["top", "mid", "bot"]:
		lane_pts.append_array(get_lane_path(l))
	lane_pts.append_array(get_river_path())
	for _i in range(74):
		var p := Vector2(rng.randf_range(24.0, arena_size.x - 24.0),
			rng.randf_range(24.0, arena_size.y - 24.0))
		if _min_dist_to(lane_pts, p) < 70.0:
			continue # jangan nutupi jalur / river
		if p.distance_to(BLUE_BASE) < 130.0 or p.distance_to(RED_BASE) < 130.0:
			continue
		var size := rng.randf_range(11.0, 21.0)
		var kind := 0.0 if rng.randf() < 0.72 else 1.0 # 0 = pohon, 1 = batu
		_decor_points.append(p.x)
		_decor_points.append(p.y)
		_decor_points.append(size)
		_decor_points.append(kind)

static func _min_dist_to(points: PackedVector2Array, p: Vector2) -> float:
	var best := 1e9
	for q in points:
		var d := p.distance_to(q)
		if d < best:
			best = d
	return best

# ═══ RENDER ═══
func _draw():
	if not procedural_fallback:
		return # TileMapLayer asli yang menggambar
	var d = THEMES.get(theme_name, THEMES["forest"])
	_draw_terrain(d)
	_draw_river(d)
	for lane in ["top", "mid", "bot"]:
		_draw_lane(get_lane_path(lane), d)
	_draw_bases(d)
	_draw_shops(d)
	_draw_decor(d)
	_draw_walls(d)

func _draw_terrain(d: Dictionary):
	var full := Rect2(Vector2.ZERO, arena_size)
	draw_rect(full, d["grass"], true)
	# Dither 2-tone ala draw_terrain pygame: tile 40px, arah diagonal
	var y := 0.0
	var row := 0
	while y < arena_size.y:
		var x := 0.0
		while x < arena_size.x:
			var c: Color = d["grass_mid"] if int(x + y) % int(TILE * 2.0) < int(TILE) else d["grass"]
			draw_rect(Rect2(Vector2(x, y), Vector2(TILE, TILE)), c, true)
			x += TILE
		# strip rumput terang tiap 3 baris (mirip grass_high)
		if row % 3 == 0:
			draw_rect(Rect2(Vector2(0, y), Vector2(arena_size.x, 2.0)), d["grass_light"], true)
		y += TILE
		row += 1
	# Belahan dire (kanan-atas) = tanah kering, dipotong garis river
	var river_pts := get_river_path()
	var poly := PackedVector2Array()
	for i in range(river_pts.size()):
		poly.append(river_pts[i] + Vector2(0, -RIVER_HALF_WIDTH - 6.0))
	poly.append(Vector2(arena_size.x, 0))
	poly.append(Vector2(0, 0))
	draw_colored_polygon(poly, d["earth"])
	# Ash / transisi di tepi dire
	var ash: Color = d["ash"]
	for i in range(0, river_pts.size(), 3):
		var p: Vector2 = river_pts[i] + Vector2(0, -RIVER_HALF_WIDTH - 14.0)
		draw_circle(p, 16.0, Color(ash.r, ash.g, ash.b, 0.25))

func _draw_river(d: Dictionary):
	var pts := get_river_path()
	if pts.size() < 2:
		return
	draw_polyline(pts, d["river_dark"], RIVER_HALF_WIDTH * 2.0 + 10.0)
	draw_polyline(pts, d["river"], RIVER_HALF_WIDTH * 2.0)
	# arus: garis tengah patah-patah (mirip river_foam di pygame)
	var foam: Color = d["river_foam"]
	for i in range(0, pts.size() - 4, 6):
		draw_line(pts[i], pts[i + 4], Color(foam.r, foam.g, foam.b, 0.35), 3.0)

func _draw_lane(pts: PackedVector2Array, d: Dictionary):
	if pts.size() < 2:
		return
	var w := LANE_HALF_WIDTH * 2.0
	draw_polyline(pts, d["path_border"], w + 10.0)
	draw_polyline(pts, d["path"], w)
	var lit: Color = d["path_light"]
	draw_polyline(pts, Color(lit.r, lit.g, lit.b, 0.55), w * 0.45)
	# cobblestone: titik terang berkala (mirip _draw_cobblestone_tile)
	for i in range(0, pts.size(), 5):
		var p: Vector2 = pts[i]
		var n: Vector2 = pts[min(i + 1, pts.size() - 1)]
		var perp := (n - p).orthogonal().normalized()
		var cobble: Color = d["path_bright"]
		for s in [-1, 1]:
			draw_circle(p + perp * s * LANE_HALF_WIDTH * 0.55, 2.4,
				Color(cobble.r, cobble.g, cobble.b, 0.5))

func _draw_bases(d: Dictionary):
	# Radiant (blue) kiri-bawah, Dire (red) kanan-atas — paritas _core base positions
	_draw_base(BLUE_BASE, Color(0.235, 0.47, 1.0), d)
	_draw_base(RED_BASE, Color(0.863, 0.235, 0.235), d)

func _draw_base(center: Vector2, team_color: Color, d: Dictionary):
	draw_circle(center, 112.0, Color(d["stone"].r, d["stone"].g, d["stone"].b, 0.55))
	draw_arc(center, 108.0, 0.0, TAU, 48, team_color, 3.0)
	draw_arc(center, 74.0, 0.0, TAU, 40, Color(team_color.r, team_color.g, team_color.b, 0.55), 2.0)
	# nexus
	draw_rect(Rect2(center - Vector2(26, 26), Vector2(52, 52)), team_color.darkened(0.35), true)
	draw_rect(Rect2(center - Vector2(26, 26), Vector2(52, 52)), Color(1, 1, 1, 0.75), false, 2.0)
	for i in range(4): # turret 4 penjuru
		var a := TAU * float(i) / 4.0
		var p := center + Vector2(cos(a), sin(a)) * 92.0
		draw_circle(p, 11.0, d["stone"].lightened(0.15))
		draw_arc(p, 11.0, 0.0, TAU, 16, team_color, 2.0)

func _draw_shops(d: Dictionary):
	var shop_col: Color = d["path_bright"]
	for pos in [radiant_shop_pos, dire_shop_pos]:
		var r := Rect2(pos - Vector2(34, 26), Vector2(68, 52))
		draw_rect(r, Color(shop_col.r, shop_col.g, shop_col.b, 0.9), true)
		draw_rect(r, Color(1.0, 0.804, 0.333, 0.95), false, 2.0) # gold trim
		# kanopi bergaris ala toko pygame
		for i in range(4):
			var x := r.position.x + 6.0 + float(i) * 16.0
			draw_line(Vector2(x, r.position.y + 2.0), Vector2(x, r.position.y + 12.0),
				Color(0.75, 0.16, 0.24, 0.9), 6.0)

func _draw_decor(d: Dictionary):
	var i := 0
	while i + 3 < _decor_points.size():
		var p := Vector2(_decor_points[i], _decor_points[i + 1])
		var size := _decor_points[i + 2]
		var kind := int(_decor_points[i + 3])
		if kind == 0:
			draw_circle(p + Vector2(0, size * 0.35), size * 0.9, Color(0, 0, 0, 0.22)) # shadow
			draw_rect(Rect2(p + Vector2(-2, 0), Vector2(4, size * 0.8)), d["earth_dark"], true) # trunk
			draw_circle(p, size, d["tree"])
			draw_circle(p + Vector2(-size * 0.3, -size * 0.35), size * 0.62, d["tree_light"])
		else:
			draw_circle(p + Vector2(2, 3), size * 0.8, Color(0, 0, 0, 0.2))
			draw_circle(p, size * 0.75, d["stone"])
			var hl: Color = d["stone"].lightened(0.25)
			draw_circle(p + Vector2(-size * 0.2, -size * 0.25), size * 0.35, hl)
		i += 4

func _draw_walls(d: Dictionary):
	# Tembok arena (biar jelas batas map, tidak "lubang" hitam di tepi)
	var border: Color = d["path_border"]
	var wall: Color = d["stone"]
	draw_rect(Rect2(Vector2.ZERO, arena_size), Color(border.r, border.g, border.b, 0.9), false, 6.0)
	draw_rect(Rect2(Vector2(6, 6), arena_size - Vector2(12, 12)),
		Color(wall.r, wall.g, wall.b, 0.4), false, 2.0)

# Titik tujuan "push" per tim (mirip PUSH di _entity.Hero) — dipakai Hero & Minion
func get_enemy_base(team: String) -> Vector2:
	return RED_BASE if team == "blue" else BLUE_BASE


## Base sendiri (dipakai Hero untuk retreat + regen 180 HP/s di radius 100)
func get_own_base(team: String) -> Vector2:
	return BLUE_BASE if team == "blue" else RED_BASE

func get_spawn_point(team: String, index: int, lane: String = "mid") -> Vector2:
	var pts := get_lane_path(lane)
	if pts.size() < 4:
		return get_enemy_base(team)
	var idx := 2 + (index % 4)
	if team == "blue":
		return pts[idx]
	return pts[maxi(0, pts.size() - 1 - idx)]
