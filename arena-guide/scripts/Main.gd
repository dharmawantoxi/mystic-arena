extends Node2D
## Mystic Arena - Main DIAGONAL ala pygame (langkah 15).

const LevelDB = preload("res://scripts/LevelDB.gd")
const HeroScene = preload("res://scenes/Hero.tscn")
const MinionScene = preload("res://scenes/Minion.tscn")
const TowerScene = preload("res://scenes/Tower.tscn")
const NexusScene = preload("res://scenes/Nexus.tscn")

const ARENA = Rect2(0, 0, 1280, 720)
const BASE_BLUE = Vector2(130, 595)
const BASE_RED = Vector2(1145, 175)
const HERO_SPAWN = Vector2(250, 580)
const INCOME_PER_SEC = 3.0
const SHOP_BLUE = Vector2(340, 540)
const SHOP_RED = Vector2(940, 180)

const LANE_TOP_WP = [Vector2(90, 590), Vector2(85, 460), Vector2(95, 340), Vector2(120, 220), Vector2(170, 180), Vector2(240, 100), Vector2(380, 75), Vector2(550, 70), Vector2(720, 75), Vector2(880, 85), Vector2(1030, 110), Vector2(1180, 180)]
const LANE_MID_WP = [Vector2(170, 550), Vector2(300, 420), Vector2(440, 320), Vector2(580, 400), Vector2(640, 360), Vector2(700, 320), Vector2(840, 400), Vector2(980, 300), Vector2(1110, 170)]
const LANE_BOT_WP = [Vector2(130, 630), Vector2(260, 650), Vector2(420, 660), Vector2(600, 660), Vector2(780, 655), Vector2(940, 645), Vector2(1070, 620), Vector2(1170, 500), Vector2(1190, 340), Vector2(1195, 250), Vector2(1180, 180)]
const LANE_SMOOTH = [10, 8, 10]
const RIVER_WP = [Vector2(0, 200), Vector2(150, 270), Vector2(350, 350), Vector2(640, 360), Vector2(930, 370), Vector2(1130, 450), Vector2(1280, 520)]
const RIVER_SMOOTH = 10
const SLOT_BLUE_FRAC = [[0.15, 0.30, 0.45], [0.10, 0.25, 0.40], [0.15, 0.30, 0.45]]
const SLOT_RED_FRAC = [[0.85, 0.70, 0.55], [0.90, 0.75, 0.60], [0.85, 0.70, 0.55]]

var level_data: Dictionary = {}
var slots: Array = []
var hero: HeroUnit = null
var wave_count: int = 0
var wave_timer: float = 5.0
var wave_interval: float = 25.0
var gold: float = 0.0
var match_over: bool = false
var victory: bool = false
var hud: Hud = null
var pause_layer: PauseMenu = null
var shop = null # ShopUI L34
var map_theme: Dictionary = {}
var map_seed: int = 7
var decor: Array = []
var lane_paths: Array = []
var lane_hit: Array = []
var river_pts := PackedVector2Array()


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	$Camera2D.position = Vector2(640, 360)
	$Camera2D.limit_left = 0
	$Camera2D.limit_top = 0
	$Camera2D.limit_right = 1280
	$Camera2D.limit_bottom = 720
	print("[Main] Ready - tekan H (toko) / ESC (pause) untuk tes input.")
	level_data = LevelDB.load_level(App.level_path())
	if level_data.is_empty():
		print("[Main] GAGAL baca level.")
		return
	_build_paths()
	map_theme = MapTheme.get_theme(str(level_data.get("theme", "forest")))
	map_seed = int(level_data.get("level", 1)) * 1000 + 7
	print("[Main] Level %d: %s | gold awal %d | Tema map: %s." % [int(level_data["level"]), str(level_data["name"]), int(level_data["starting_gold"]), str(map_theme.get("name", "?"))])
	var heroes: Array = level_data["heroes"]
	print("[Main] Hero tersedia: %d (contoh: %s, HP %d)" % [heroes.size(), str(heroes[0]["name"]), int(heroes[0]["hp"])])
	slots = _generate_slots()
	print("[Main] Slot menara: %d" % slots.size())
	_generate_decor()
	_spawn_hero()
	_start_waves()
	gold = float(level_data.get("starting_gold", 450))
	print("[Main] Gold awal: %d. Klik slot biru kosong untuk bangun menara." % int(gold))
	_spawn_starting_towers()
	_spawn_nexuses()
	hud = Hud.new()
	add_child(hud)
	hud.setup(self)
	pause_layer = PauseMenu.new()
	add_child(pause_layer)
	pause_layer.setup(self)
	# L34 shop
	var ShopUIScript = load("res://scripts/Shop.gd")
	shop = ShopUIScript.new()
	add_child(shop)
	shop.setup(self)


func _threshold_y(x: float) -> float:
	return 200.0 + 320.0 * x / 1280.0


func _side_of(p: Vector2) -> String:
	if p.y > _threshold_y(p.x) + 20.0:
		return "radiant"
	if p.y < _threshold_y(p.x) - 20.0:
		return "dire"
	return "mid"


func _curved_path(waypoints: Array, smoothness: int) -> PackedVector2Array:
	var pts: Array = [waypoints[0]] + waypoints + [waypoints[waypoints.size() - 1]]
	var out := PackedVector2Array()
	for i in range(pts.size() - 3):
		var p0: Vector2 = pts[i]
		var p1: Vector2 = pts[i + 1]
		var p2: Vector2 = pts[i + 2]
		var p3: Vector2 = pts[i + 3]
		for step in smoothness:
			var t := float(step) / float(smoothness)
			var t2 := t * t
			var t3 := t2 * t
			var x := 0.5 * ((2.0 * p1.x) + (-p0.x + p2.x) * t + (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2 + (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3)
			var y := 0.5 * ((2.0 * p1.y) + (-p0.y + p2.y) * t + (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2 + (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3)
			out.append(Vector2(int(x), int(y))) # L32 trunc pygame — dulu float bikin bata meleset 0.5px
	out.append(waypoints[waypoints.size() - 1])
	return out


func _build_paths() -> void:
	lane_paths.clear()
	lane_hit.clear()
	var wps: Array = [LANE_TOP_WP, LANE_MID_WP, LANE_BOT_WP]
	for li in 3:
		var pts := _curved_path(wps[li], int(LANE_SMOOTH[li]))
		lane_paths.append(pts)
		var hit := PackedVector2Array()
		var i := 0
		while i < pts.size():
			hit.append(pts[i])
			i += 4
		lane_hit.append(hit)
	river_pts = _curved_path(RIVER_WP, RIVER_SMOOTH)
	print("[Main] Jalur siap: top %d / mid %d / bot %d titik, sungai %d titik." % [lane_paths[0].size(), lane_paths[1].size(), lane_paths[2].size(), river_pts.size()])


func _dist_to_pts(p: Vector2, pts: PackedVector2Array, step: int) -> float:
	var best := 1000000.0
	var i := 0
	while i < pts.size():
		best = minf(best, p.distance_to(pts[i]))
		i += step
	return best


func _generate_slots() -> Array:
	var out: Array = []
	for li in lane_paths.size():
		var path: PackedVector2Array = lane_paths[li]
		var blues: Array = SLOT_BLUE_FRAC[li]
		var reds: Array = SLOT_RED_FRAC[li]
		for f in blues:
			var idx := mini(int(path.size() * float(f)), path.size() - 1)
			out.append({"team": "blue", "lane": li, "taken": false, "pos": path[idx]})
		for f in reds:
			var idx := mini(int(path.size() * float(f)), path.size() - 1)
			out.append({"team": "red", "lane": li, "taken": false, "pos": path[idx]})
	return out


func _draw() -> void:
	_draw_terrain()
	_draw_terrain_details()
	_draw_river()
	_draw_decor18()
	_draw20_river_runes()
	_draw_lanes()
	_draw_decor23() 
	_draw_base_plates()
	_draw_border_wall()
	_draw_decor26()
	_draw_decor()
	_draw_decor25()
	_draw_decor17()
	_draw_decor16()
	_draw_decor24()
	_draw_shops()
	_draw20_shop_fx()
	_draw21_particles()
	for s in slots:
		if bool(s.get("taken", false)):
			continue
		var pos: Vector2 = s["pos"]
		var ring: Color = Color("#3E7CB1") if str(s["team"]) == "blue" else Color("#B13E3E")
		draw_circle(pos, 22.0, Color("#0E1A12"))
		draw_arc(pos, 22.0, 0.0, TAU, 32, ring, 3.0)
		draw_circle(pos, 5.0, ring)
	_draw22_fog()
	if shop != null:
		shop.draw_on(self)
	if match_over:
		draw_rect(ARENA, Color(0, 0, 0, 0.72))
		var font: Font = ThemeDB.fallback_font
		var text: String = "VICTORY!" if victory else "DEFEAT"
		var col: Color = Color("#C9A227") if victory else Color("#B13E3E")
		var w: float = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 96).x
		draw_string(font, Vector2((1280.0 - w) * 0.5, 350.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 96, col)
		var sub := "R ulangi  |  ENTER lanjut  |  ESC menu"
		var w2: float = font.get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 32).x
		draw_string(font, Vector2((1280.0 - w2) * 0.5, 410.0), sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 32, Color.WHITE)


func _draw_terrain() ... (sampai sebelum _draw_terrain_details)
# 2) Ganti SELURUH func _draw_terrain_details() ... (sampai sebelum _draw_river)
# Hook: sudah dipanggil di _draw() — tidak perlu ubah urutan.
#
# Perubahan vs L15:
# - Radiant: tambah tuft daun (v55-70) + moss kedua (v70-85) + speck r_high (v85-92)
# - Dire: pakai d3 untuk highlight; tambah ash speck (v68-80) + burnt patch (v80-90)
# - Transition: highlight pakai t2 (bukan t1) — fix bug scripts
# - Pebble dire: hash deterministic (sudah) + 1 speck ekstra
# - terrain_details: 50→120 radiant, 40→90 dire (seed 100 tetap)

# ═══════════════════════════════════════════
# LANGKAH 27 — ganti _draw_terrain + _draw_terrain_details
# ═══════════════════════════════════════════
func _draw_terrain() -> void:
	if map_theme.is_empty():
		draw_rect(ARENA, Color("#1B2B20"))
		return
	var r1: Color = map_theme["r1"]
	var r2: Color = map_theme["r2"]
	var r3: Color = map_theme["r3"]
	var r4: Color = map_theme["r4"]
	var r_high: Color = map_theme["r_high"]
	var r_moss: Color = map_theme["r_moss"]
	var d2: Color = map_theme["d2"]
	var d3: Color = map_theme["d3"]
	var d4: Color = map_theme["d4"]
	var d_ash: Color = map_theme["d_ash"]
	var d_burnt: Color = map_theme["d_burnt"]
	var t1: Color = map_theme["t1"]
	var t2: Color = map_theme["t2"]
	var pebble := Color8(60, 60, 70)
	for ty in range(0, 720, 16):
		for tx in range(0, 1280, 16):
			var thr := _threshold_y(float(tx) + 8.0)
			var cyy := float(ty) + 8.0
			var v: int = (tx * 7 + ty * 13) % 100
			if cyy > thr + 20.0:
				draw_rect(Rect2(tx, ty, 16, 16), r2)
				if v < 20:
					for i in 3:
						var gx: int = tx + 2 + i * 5
						var gy: int = ty + 8 + (i % 2) * 3
						draw_rect(Rect2(gx, gy, 1, 3), r3)
						draw_rect(Rect2(gx, gy, 1, 1), r4)
				elif v < 35:
					draw_rect(Rect2(tx + 3, ty + 4, 8, 4), r1)
				elif v < 45:
					draw_rect(Rect2(tx + 5, ty + 6, 6, 4), r_moss)
				elif v < 55:
					draw_rect(Rect2(tx + 6, ty + 4, 2, 2), r_high)
				elif v < 70:
					# tuft daun ekstra (density bake)
					draw_rect(Rect2(tx + 2, ty + 3, 1, 2), r3)
					draw_rect(Rect2(tx + 7, ty + 9, 1, 3), r4)
					draw_rect(Rect2(tx + 12, ty + 5, 1, 2), r3)
				elif v < 85:
					draw_rect(Rect2(tx + 9, ty + 10, 5, 3), r_moss)
					draw_rect(Rect2(tx + 10, ty + 10, 3, 1), r3)
				elif v < 92:
					draw_rect(Rect2(tx + 3, ty + 11, 2, 2), r_high)
					draw_rect(Rect2(tx + 11, ty + 2, 2, 2), r4)
			elif cyy < thr - 20.0:
				draw_rect(Rect2(tx, ty, 16, 16), d2)
				if v < 20:
					draw_line(Vector2(tx + 2, ty + 6), Vector2(tx + 10, ty + 8), d_burnt, 1.0)
					draw_line(Vector2(tx + 6, ty + 4), Vector2(tx + 8, ty + 12), d_burnt, 1.0)
				elif v < 35:
					draw_rect(Rect2(tx + 3, ty + 5, 5, 3), d_ash)
				elif v < 50:
					var px: int = tx + 2 + (tx * 13 + ty * 7) % 11
					var py: int = ty + 2 + (tx * 5 + ty * 11) % 11
					draw_rect(Rect2(px, py, 2, 2), pebble)
					var qx: int = tx + 2 + (tx * 7 + ty * 3 + 5) % 11
					var qy: int = ty + 2 + (tx * 11 + ty * 5 + 3) % 11
					draw_rect(Rect2(qx, qy, 2, 2), pebble)
					# speck ketiga (density)
					var rx: int = tx + 2 + (tx * 3 + ty * 17 + 2) % 11
					var ry: int = ty + 2 + (tx * 19 + ty * 7 + 1) % 11
					draw_rect(Rect2(rx, ry, 1, 1), pebble)
				elif v < 60:
					draw_rect(Rect2(tx + 4, ty + 6, 4, 3), d_burnt)
				elif v < 68:
					draw_rect(Rect2(tx + 5, ty + 3, 3, 2), d4)
				elif v < 80:
					draw_rect(Rect2(tx + 2, ty + 10, 3, 2), d_ash)
					draw_rect(Rect2(tx + 10, ty + 4, 2, 2), d3)
				elif v < 90:
					draw_rect(Rect2(tx + 7, ty + 8, 4, 2), d_burnt)
					draw_rect(Rect2(tx + 1, ty + 2, 2, 1), d3)
			else:
				draw_rect(Rect2(tx, ty, 16, 16), t1)
				if v < 30:
					draw_rect(Rect2(tx + 4, ty + 6, 4, 2), t2)
				elif v < 50:
					draw_rect(Rect2(tx + 9, ty + 3, 3, 2), t2)
				elif v < 65:
					draw_rect(Rect2(tx + 2, ty + 11, 5, 2), t2)

func _draw_terrain_details() -> void:
	if map_theme.is_empty():
		return
	var r1: Color = map_theme["r1"]
	var de1: Color = map_theme["d1"]
	var burnt: Color = map_theme["d_burnt"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 100
	for i in 120:
		var x := rng.randf_range(0.0, 1280.0)
		var y := rng.randf_range(360.0, 720.0)
		if rng.randf() > 0.55:
			draw_circle(Vector2(x, y), 3.0, r1)
			if rng.randf() > 0.7:
				draw_circle(Vector2(x + 4.0, y - 2.0), 2.0, r1)
	for i in 90:
		var x2 := rng.randf_range(0.0, 1280.0)
		var y2 := rng.randf_range(0.0, 360.0)
		if rng.randf() > 0.5:
			draw_circle(Vector2(x2, y2), 4.0, burnt)
			draw_circle(Vector2(x2 - 1.0, y2 - 1.0), 2.0, de1)
			if rng.randf() > 0.65:
				draw_circle(Vector2(x2 + 5.0, y2 + 3.0), 2.0, burnt)

func _draw_river() -> void:
	if map_theme.is_empty() or river_pts.is_empty():
		return
	var deep: Color = map_theme["rv_deep"]
	var mid: Color = map_theme["rv_mid"]
	var glow: Color = map_theme["rv_glow"]
	var foam: Color = map_theme["rv_foam"]
	draw_polyline(river_pts, Color8(55, 55, 65), 58.0)
	draw_polyline(river_pts, mid, 46.0)
	draw_polyline(river_pts, deep, 30.0)
	var i := 0
	var k := 0
	while i < river_pts.size():
		var rp: Vector2 = river_pts[i]
		if i % 3 == 0:
			draw_rect(Rect2(rp.x - 2, rp.y - 2, 4, 4), glow)
			draw_rect(Rect2(rp.x - 1, rp.y - 1, 2, 2), foam)
		if i % 4 == 0:
			var j0 := maxi(0, i - 1)
			var j1 := mini(river_pts.size() - 1, i + 1)
			var d: Vector2 = river_pts[j1] - river_pts[j0]
			if d.length() > 1.0:
				var pp := Vector2(-d.y, d.x).normalized()
				var s := 30.0 if k % 2 == 0 else -30.0
				var bp: Vector2 = rp + pp * s
				draw_rect(Rect2(bp.x - 3, bp.y - 3, 6, 6), Color8(55, 55, 65))
				draw_rect(Rect2(bp.x - 2, bp.y - 2, 4, 4), Color8(95, 95, 105))
				k += 1
		i += 1


func _draw_lanes() -> void:
	if map_theme.is_empty():
		return
	var p1: Color = map_theme["p1"]
	for li in lane_paths.size():
		var path: PackedVector2Array = lane_paths[li]
		draw_polyline(path, Color8(12, 8, 12), 52.0)
		draw_polyline(path, p1, 46.0)



func _draw_cobble(p: Vector2, ang: float, n: int, p1: Color, p2: Color, p3: Color, p4: Color, moss: Color, crack: Color) -> void:
	var v := (n * 37) % 100
	var c: Color = p2 if v < 40 else (p3 if v < 70 else p1)
	draw_set_transform(p, ang, Vector2.ONE)
	draw_rect(Rect2(-7, -19, 14, 38), c)
	draw_rect(Rect2(-7, -19, 14, 3), p4)
	if n % 7 == 0:
		draw_line(Vector2(-4, -8), Vector2(3, 6), crack, 1.0)
	if v > 85:
		draw_rect(Rect2(-3, -4, 5, 4), moss)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_border_stone(p: Vector2) -> void:
	draw_rect(Rect2(p.x - 5, p.y - 4, 10, 9), Color8(12, 8, 12))
	draw_rect(Rect2(p.x - 4, p.y - 3, 8, 7), Color8(55, 55, 65))
	draw_rect(Rect2(p.x - 3, p.y - 2, 6, 5), Color8(95, 95, 105))
	draw_rect(Rect2(p.x - 3, p.y - 2, 6, 2), Color8(135, 135, 145))


func _draw_base_plates() -> void:
	if map_theme.is_empty():
		return
	var p1: Color = map_theme["p1"]
	var p2: Color = map_theme["p2"]
	var p4: Color = map_theme["p4"]
	for b in [BASE_BLUE, BASE_RED]:
		var bp: Vector2 = b
		draw_circle(bp, 62.0, Color8(12, 8, 12))
		draw_circle(bp, 58.0, p1)
		draw_circle(bp, 46.0, p2)
		draw_arc(bp, 52.0, 0.0, TAU, 48, p4, 3.0)


func _draw_border_wall() -> void:
	for x in range(0, 1280, 16):
		_draw_wall_block(Rect2(x, 0, 16, 20))
		_draw_wall_block(Rect2(x, 700, 16, 20))
	for yy in range(20, 700, 16):
		_draw_wall_block(Rect2(0, yy, 20, 16))
		_draw_wall_block(Rect2(1260, yy, 20, 16))
	for x in range(30, 1250, 40):
		var xf := float(x)
		draw_colored_polygon(PackedVector2Array([Vector2(xf - 3, 20), Vector2(xf + 3, 20), Vector2(xf, 26)]), Color8(12, 8, 12))
		draw_colored_polygon(PackedVector2Array([Vector2(xf - 2, 21), Vector2(xf + 2, 21), Vector2(xf, 25)]), Color8(95, 95, 105))


func _draw_wall_block(r: Rect2) -> void:
	draw_rect(r, Color8(12, 8, 12))
	draw_rect(Rect2(r.position + Vector2(1, 1), r.size - Vector2(2, 2)), Color8(55, 55, 65))
	draw_rect(Rect2(r.position + Vector2(2, 2), r.size - Vector2(4, 4)), Color8(95, 95, 105))
	draw_rect(Rect2(r.position + Vector2(2, 2), Vector2(r.size.x - 4, 2)), Color8(135, 135, 145))


func _generate_decor() -> void:
	decor.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = map_seed
	var tname := str(map_theme.get("name", "Forest"))
	var plan: Array = []
	match tname:
		"Desert":
			plan = [
				["cactus", "radiant", 10], ["rock", "any", 6],
				["bones", "dire", 6], ["dead_tree", "dire", 6],
				["crystal_amber", "dire", 4], ["ruins", "dire", 3],
				["rock", "radiant", 4],
			]
		"Volcanic":
			plan = [
				["dead_tree", "any", 10], ["rock_obs", "any", 6],
				["bones", "dire", 5], ["lavaflower", "any", 6],
				["crystal_red", "dire", 4], ["rock_obs", "radiant", 3],
			]
		_:
			plan = [
				["dark_tree", "radiant", 12], ["bush", "radiant", 6],
				["mushroom", "radiant", 6], ["rock", "any", 6],
				["crystal_blue", "radiant", 3], ["dead_tree", "dire", 8],
				["gravestone", "dire", 4], ["bones", "dire", 5],
				["crystal_red", "dire", 3],
			]
	for entry in plan:
		var kind: String = str(entry[0])
		var zone: String = str(entry[1])
		var count: int = int(entry[2])
		for i in count:
			var p := _decor_spot(rng, zone)
			if p.x >= 0.0:
				decor.append({"kind": kind, "pos": p, "v": rng.randi_range(0, 2)})
	print("[Main] Dekorasi: %d." % decor.size())


func _decor_spot(rng: RandomNumberGenerator, zone: String) -> Vector2:
	for t in 40:
		var p := Vector2(rng.randf_range(40.0, 1240.0), rng.randf_range(40.0, 680.0))
		if zone != "any" and _side_of(p) != zone:
			continue
		if _decor_spot_free(p):
			return p
	return Vector2(-1, -1)


func _decor_spot_free(p: Vector2) -> bool:
	for lp in lane_hit:
		var lhp: PackedVector2Array = lp
		if _dist_to_pts(p, lhp, 1) < 55.0:
			return false
	if _dist_to_pts(p, river_pts, 2) < 60.0:
		return false
	if p.distance_to(SHOP_BLUE) < 100.0 or p.distance_to(SHOP_RED) < 100.0:
		return false
	if p.distance_to(BASE_BLUE) < 130.0 or p.distance_to(BASE_RED) < 130.0:
		return false
	for s in slots:
		var sp: Vector2 = s["pos"]
		if sp.distance_to(p) < 45.0:
			return false
	for d in decor:
		var dp: Vector2 = d["pos"]
		if dp.distance_to(p) < 34.0:
			return false
	return true


func _draw_decor() -> void:
	for d in decor:
		var kind: String = str(d["kind"])
		var p: Vector2 = d["pos"]
		var v: int = int(d["v"])
		match kind:
			"dark_tree":
				_draw_dark_tree(p, v)
			"dead_tree":
				_draw_dead_tree(p, v)
			"rock":
				_draw_rock(p, v, false)
			"rock_obs":
				_draw_rock(p, v, true)
			"mushroom":
				_draw_mushroom(p, v)
			"bones":
				_draw_bones(p)
			"gravestone":
				_draw_gravestone(p)
			"crystal_blue":
				_draw_crystal(p, v, "blue")
			"crystal_red":
				_draw_crystal(p, v, "red")
			"crystal_amber":
				_draw_crystal(p, v, "amber")
			"bush":
				_draw_bush(p, v)
			"cactus":
				_draw_cactus(p, v)
			"ruins":
				_draw_ruins(p)
			"lavaflower":
				_draw_lavaflower(p, v)


func _draw_dark_tree(p: Vector2, v: int) -> void:
	var k := 0.85 + 0.15 * float(v)
	draw_rect(Rect2(p.x - 3 * k, p.y, 6 * k, 14 * k), Color8(32, 20, 15))
	draw_circle(p + Vector2(0, -8 * k), 13 * k, Color8(18, 42, 22))
	draw_circle(p + Vector2(-6 * k, -14 * k), 9 * k, Color8(32, 65, 35))
	draw_circle(p + Vector2(5 * k, -15 * k), 8 * k, Color8(55, 95, 55))
	draw_circle(p + Vector2(2 * k, -18 * k), 3 * k, Color8(80, 130, 70))


func _draw_dead_tree(p: Vector2, v: int) -> void:
	var k := 0.85 + 0.15 * float(v)
	var c := Color8(55, 42, 35)
	draw_line(p, p + Vector2(0, -26 * k), c, 4.0 * k)
	draw_line(p + Vector2(0, -14 * k), p + Vector2(-10 * k, -22 * k), c, 2.5 * k)
	draw_line(p + Vector2(0, -18 * k), p + Vector2(9 * k, -27 * k), c, 2.5 * k)
	if v == 2:
		draw_line(p + Vector2(0, -10 * k), p + Vector2(8 * k, -15 * k), c, 2.0)


func _draw_rock(p: Vector2, v: int, obs: bool) -> void:
	var k := 0.8 + 0.2 * float(v)
	var dark := Color8(40, 36, 52) if obs else Color8(55, 55, 65)
	var midc := Color8(80, 70, 95) if obs else Color8(95, 95, 105)
	var lite := Color8(130, 115, 150) if obs else Color8(135, 135, 145)
	draw_circle(p + Vector2(-6 * k, 0), 8 * k, dark)
	draw_circle(p + Vector2(5 * k, -2 * k), 10 * k, midc)
	draw_circle(p + Vector2(3 * k, -5 * k), 4 * k, lite)


func _draw_mushroom(p: Vector2, v: int) -> void:
	var k := 0.8 + 0.2 * float(v)
	draw_rect(Rect2(p.x - 2 * k, p.y - 8 * k, 4 * k, 8 * k), Color8(210, 195, 170))
	draw_circle(p + Vector2(0, -9 * k), 7 * k, Color8(120, 40, 60))
	draw_circle(p + Vector2(-2 * k, -10 * k), 1.8 * k, Color8(230, 220, 235))
	draw_circle(p + Vector2(2.5 * k, -8 * k), 1.4 * k, Color8(230, 220, 235))


func _draw_bones(p: Vector2) -> void:
	var c := Color8(200, 190, 170)
	draw_line(p + Vector2(-8, 2), p + Vector2(8, -2), c, 2.0)
	draw_line(p + Vector2(-6, -4), p + Vector2(6, 4), c, 2.0)
	draw_circle(p + Vector2(10, 2), 3.0, c)


func _draw_gravestone(p: Vector2) -> void:
	draw_rect(Rect2(p.x - 7, p.y - 18, 14, 18), Color8(12, 8, 12))
	draw_rect(Rect2(p.x - 6, p.y - 17, 12, 16), Color8(95, 95, 105))
	draw_rect(Rect2(p.x - 6, p.y - 17, 12, 3), Color8(135, 135, 145))
	draw_line(p + Vector2(0, -13), p + Vector2(0, -5), Color8(55, 55, 65), 2.0)
	draw_line(p + Vector2(-3, -11), p + Vector2(3, -11), Color8(55, 55, 65), 2.0)


func _draw_crystal(p: Vector2, v: int, tint: String) -> void:
	var dark := Color8(25, 55, 100)
	var midc := Color8(55, 100, 170)
	var lite := Color8(100, 170, 240)
	if tint == "red":
		dark = Color8(100, 20, 30)
		midc = Color8(170, 40, 55)
		lite = Color8(230, 80, 100)
	elif tint == "amber":
		dark = Color8(140, 80, 20)
		midc = Color8(200, 130, 40)
		lite = Color8(250, 190, 90)
	var k := 0.8 + 0.2 * float(v)
	draw_colored_polygon(PackedVector2Array([p + Vector2(-6 * k, 0), p + Vector2(6 * k, 0), p + Vector2(0, -22 * k)]), dark)
	draw_colored_polygon(PackedVector2Array([p + Vector2(-3 * k, 0), p + Vector2(3 * k, 0), p + Vector2(0, -22 * k)]), midc)
	draw_line(p + Vector2(0, -2 * k), p + Vector2(0, -20 * k), lite, 2.0)
	draw_circle(p + Vector2(0, -22 * k), 1.6, Color.WHITE)


func _draw_bush(p: Vector2, v: int) -> void:
	var k := 0.8 + 0.2 * float(v)
	draw_circle(p + Vector2(-7 * k, 0), 8 * k, Color8(18, 42, 22))
	draw_circle(p + Vector2(7 * k, 0), 8 * k, Color8(18, 42, 22))
	draw_circle(p + Vector2(0, -5 * k), 9 * k, Color8(32, 65, 35))
	draw_circle(p + Vector2(-2 * k, -7 * k), 3 * k, Color8(55, 95, 55))


func _draw_cactus(p: Vector2, v: int) -> void:
	var k := 0.85 + 0.15 * float(v)
	var c := Color8(60, 140, 70)
	var cd := Color8(35, 95, 45)
	draw_rect(Rect2(p.x - 4 * k, p.y - 26 * k, 8 * k, 26 * k), cd)
	draw_rect(Rect2(p.x - 3 * k, p.y - 26 * k, 6 * k, 26 * k), c)
	draw_rect(Rect2(p.x - 11 * k, p.y - 18 * k, 5 * k, 10 * k), c)
	draw_rect(Rect2(p.x + 6 * k, p.y - 22 * k, 5 * k, 12 * k), c)


func _draw_ruins(p: Vector2) -> void:
	draw_rect(Rect2(p.x - 7, p.y - 22, 14, 22), Color8(12, 8, 12))
	draw_rect(Rect2(p.x - 6, p.y - 21, 12, 20), Color8(125, 100, 70))
	draw_rect(Rect2(p.x - 6, p.y - 21, 12, 3), Color8(165, 135, 95))
	draw_rect(Rect2(p.x + 8, p.y - 6, 12, 6), Color8(95, 75, 52))


func _draw_lavaflower(p: Vector2, v: int) -> void:
	draw_circle(p + Vector2(0, -8), 12.0, Color(1.0, 0.45, 0.1, 0.25))
	draw_line(p, p + Vector2(0, -10), Color8(95, 45, 22), 2.0)
	for a in 5:
		var ang := TAU * float(a) / 5.0 + float(v)
		draw_circle(p + Vector2(cos(ang), sin(ang)) * 5.0 + Vector2(0, -12), 3.5, Color8(240, 120, 30))
	draw_circle(p + Vector2(0, -12), 3.0, Color8(255, 230, 130))


func _draw_shops() -> void:
	_draw_shop(SHOP_BLUE, "item")
	_draw_shop(SHOP_RED, "hero")


func _draw_shop(pos: Vector2, kind: String) -> void:
	var roof: Color = Color8(70, 40, 100) if kind == "item" else Color8(80, 30, 30)
	var roof_l: Color = Color8(120, 70, 160) if kind == "item" else Color8(130, 50, 50)
	var win: Color = Color8(180, 120, 255) if kind == "item" else Color8(255, 100, 100)
	var sign_tx := "ITEM" if kind == "item" else "SHOP"
	var cx := pos.x
	var cy := pos.y
	draw_rect(Rect2(cx - 35, cy + 22, 70, 14), Color8(12, 8, 12))
	draw_rect(Rect2(cx - 34, cy + 23, 68, 12), Color8(55, 55, 65))
	draw_rect(Rect2(cx - 33, cy + 24, 66, 3), Color8(95, 95, 105))
	draw_rect(Rect2(cx - 30, cy - 12, 60, 36), Color8(12, 8, 12))
	draw_rect(Rect2(cx - 28, cy - 10, 56, 32), Color8(60, 40, 30))
	draw_rect(Rect2(cx - 28, cy - 10, 4, 32), Color8(90, 60, 40))
	for i in range(1, 4):
		var py := cy - 10 + i * 8
		draw_line(Vector2(cx - 28, py), Vector2(cx + 28, py), Color8(40, 25, 20), 1.0)
	draw_rect(Rect2(cx - 8, cy + 2, 16, 20), Color8(12, 8, 12))
	draw_rect(Rect2(cx - 7, cy + 3, 14, 18), Color8(40, 25, 15))
	draw_line(Vector2(cx, cy + 3), Vector2(cx, cy + 21), Color8(30, 15, 10), 1.0)
	draw_rect(Rect2(cx + 3, cy + 11, 2, 3), Color8(200, 160, 40))
	draw_rect(Rect2(cx - 26, cy - 2, 9, 9), Color8(12, 8, 12))
	draw_rect(Rect2(cx - 25, cy - 1, 7, 7), win)
	draw_rect(Rect2(cx + 17, cy - 2, 9, 9), Color8(12, 8, 12))
	draw_rect(Rect2(cx + 18, cy - 1, 7, 7), win)
	draw_colored_polygon(PackedVector2Array([Vector2(cx - 36, cy - 10), Vector2(cx + 36, cy - 10), Vector2(cx, cy - 38)]), Color8(12, 8, 12))
	draw_colored_polygon(PackedVector2Array([Vector2(cx - 33, cy - 11), Vector2(cx + 33, cy - 11), Vector2(cx, cy - 36)]), roof)
	draw_line(Vector2(cx, cy - 36), Vector2(cx + 33, cy - 11), roof_l, 2.0)
	draw_rect(Rect2(cx - 16, cy - 12, 32, 10), Color8(12, 8, 12))
	draw_rect(Rect2(cx - 15, cy - 11, 30, 8), Color8(30, 22, 16))
	var font: Font = ThemeDB.fallback_font
	var tw: float = font.get_string_size(sign_tx, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
	draw_string(font, Vector2(cx - tw * 0.5, cy - 4), sign_tx, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color8(200, 160, 40))


func _spawn_hero() -> void:
	var heroes: Array = level_data["heroes"]
	var data: Dictionary = heroes[0]
	hero = HeroScene.instantiate() as HeroUnit
	add_child(hero)
	hero.setup(data, "blue", HERO_SPAWN)
	print("[Main] Hero muncul: %s - klik hero untuk pilih, klik map untuk jalan." % hero.hero_name)


func _on_left_click(point: Vector2) -> void:
	if shop != null and shop.open:
		if shop.handle_click(point):
			queue_redraw()
			return
	# klik gedung ITEM forge
	if point.distance_to(SHOP_BLUE) <= 60.0:
		if shop != null:
			shop.toggle_mode("item")
			queue_redraw()
			print("[Shop] klik gedung ITEM %s" % str(point))
		return
	if point.distance_to(SHOP_RED) <= 60.0:
		if shop != null:
			shop.toggle_mode("hero")
			queue_redraw()
			print("[Shop] klik gedung SHOP %s" % str(point))
		return
	if hero == null:
		return
	if hero.position.distance_to(point) <= 30.0:
		hero.set_selected(true)
		Sound.play("click")
		print("[Main] %s dipilih." % hero.hero_name)
		return
	var slot_index: int = _slot_at(point)
	if slot_index >= 0:
		_try_build(slot_index)
		return
	if hero.selected:
		hero.move_to(point)
		Sound.play("move")
		print("[Main] %s jalan ke (%d, %d)." % [hero.hero_name, int(point.x), int(point.y)])
	else:
		print("[Main] Klik hero dulu untuk memilih.")


func _start_waves() -> void:
	var waves: Dictionary = level_data["waves"]
	wave_timer = float(waves.get("first_delay", 5.0))
	wave_interval = float(waves.get("interval", 25.0))
	print("[Main] Wave pertama dalam %.0f detik." % wave_timer)


func _process(delta: float) -> void:
	if match_over or level_data.is_empty():
		return
	gold += INCOME_PER_SEC * delta
	wave_timer -= delta
	if wave_timer <= 0.0:
		wave_count += 1
		_spawn_wave(wave_count)
		wave_timer = wave_interval
	_flame_t += delta
	if _flame_t >= 0.15:
		_flame_t = 0.0
		_flame_frame = (_flame_frame + 1) % 4
		_anim_t += 9.0
		queue_redraw()


func _spawn_wave(n: int) -> void:
	var waves: Dictionary = level_data["waves"]
	var per_lane: int = int(waves.get("minions_per_lane", 3))
	var spawned: int = 0
	for li in lane_paths.size():
		var lp: PackedVector2Array = lane_paths[li]
		for i in per_lane:
			var lat: float = float(i - 1) * 22.0
			_spawn_minion("blue", lp, true, lat)
			_spawn_minion("red", lp, false, lat)
			spawned += 2
	Sound.play("wave")
	print("[Main] Wave %d: %d minion turun." % [n, spawned])


func _spawn_minion(team_name: String, lane_path: PackedVector2Array, forward: bool, lateral: float) -> void:
	var m := MinionScene.instantiate() as MinionUnit
	add_child(m)
	m.setup(team_name, lane_path, forward, lateral)


func _slot_at(point: Vector2) -> int:
	for i in slots.size():
		var s: Dictionary = slots[i]
		var pos: Vector2 = s["pos"]
		if pos.distance_to(point) <= 26.0:
			return i
	return -1


func _try_build(slot_index: int) -> void:
	var s: Dictionary = slots[slot_index]
	if str(s["team"]) != "blue":
		print("[Main] Slot itu milik musuh.")
		Sound.play("error")
		return
	if bool(s.get("taken", false)):
		print("[Main] Slot sudah ada menara.")
		Sound.play("error")
		return
	var towers: Array = level_data["towers"]
	var data: Dictionary = towers[0]
	var cost: int = int(data.get("cost", 100))
	if int(gold) < cost:
		print("[Main] Gold kurang (butuh %d, sisa %d)." % [cost, int(gold)])
		Sound.play("error")
		return
	gold -= cost
	Sound.play("build")
	_build_tower(slot_index, "blue")
	print("[Main] Menara %s dibangun (sisa gold %d)." % [str(data.get("name", "Archer")), int(gold)])


func _build_tower(slot_index: int, team_name: String) -> void:
	var s: Dictionary = slots[slot_index]
	s["taken"] = true
	var towers: Array = level_data["towers"]
	var data: Dictionary = towers[0]
	var t := TowerScene.instantiate() as TowerUnit
	add_child(t)
	t.destroyed.connect(_on_tower_destroyed)
	var pos: Vector2 = s["pos"]
	t.setup(data, team_name, pos, slot_index)
	queue_redraw()


func _spawn_starting_towers() -> void:
	for i in slots.size():
		var s: Dictionary = slots[i]
		if str(s["team"]) == "red" and int(s["lane"]) == 1:
			_build_tower(i, "red")
			print("[Main] Menara merah berdiri di lane tengah.")
			break


func _on_tower_destroyed(tower: TowerUnit) -> void:
	if tower.slot_index >= 0 and tower.slot_index < slots.size():
		var s: Dictionary = slots[tower.slot_index]
		s["taken"] = false
		queue_redraw()
	print("[Main] Slot %d kosong lagi." % tower.slot_index)


func _spawn_nexuses() -> void:
	var nhp: float = float(level_data.get("nexus_hp", 1500.0))
	var nb := NexusScene.instantiate() as NexusUnit
	add_child(nb)
	nb.destroyed.connect(_on_nexus_destroyed)
	nb.setup("blue", BASE_BLUE, nhp)
	var nr := NexusScene.instantiate() as NexusUnit
	add_child(nr)
	nr.destroyed.connect(_on_nexus_destroyed)
	nr.setup("red", BASE_RED, nhp)
	print("[Main] Kedua nexus berdiri (%d HP). Hancurkan nexus merah!" % int(nhp))


func _on_nexus_destroyed(nexus: NexusUnit) -> void:
	if match_over:
		return
	match_over = true
	victory = nexus.team == "red"
	get_tree().paused = true
	if hud != null:
		hud.hide()
	queue_redraw()
	if victory:
		Sound.play("win")
		App.register_win()
		print("[Main] VICTORY! Nexus merah hancur. Tekan R untuk ulangi.")
	else:
		Sound.play("lose")
		print("[Main] DEFEAT... Nexus biru hancur. Tekan R untuk ulangi.")


# --- TACTICAL COMMANDS L33 ---
const BOSS_POS := Vector2(640, 360)

func tactical_gather() -> void:
	if hero == null or not hero.is_alive():
		print("[Tactical] GATHER gagal — hero gugur/belum spawn.")
		return
	hero.move_to(Vector2(250, 580))
	Sound.play("move")
	print("[Tactical] GATHER → hero kumpul di base (250,580)")

func tactical_protect_tower() -> void:
	if hero == null or not hero.is_alive():
		return
	var t := _nearest_blue_tower()
	if t != null:
		hero.move_to(t.position)
		print("[Tactical] PROTECT TOWER → %s di (%d,%d)" % [t.tower_name, int(t.position.x), int(t.position.y)])
	else:
		var p := _nearest_blue_slot_pos()
		hero.move_to(p)
		print("[Tactical] PROTECT TOWER → slot biru (%d,%d) (belum ada tower)" % [int(p.x), int(p.y)])
	Sound.play("move")

func tactical_protect_castle() -> void:
	if hero == null or not hero.is_alive():
		return
	hero.move_to(BASE_BLUE)
	Sound.play("move")
	print("[Tactical] PROTECT CASTLE → %s" % str(BASE_BLUE))

func tactical_attack_boss() -> void:
	if hero == null or not hero.is_alive():
		return
	hero.move_to(BOSS_POS)
	Sound.play("move")
	print("[Tactical] ATTACK BOSS → tengah sungai %s" % str(BOSS_POS))

func tactical_attack_dd() -> void:
	if hero == null or not hero.is_alive():
		return
	var target = _nearest_enemy_for_dd()
	if target != null:
		hero.move_to(target.position)
		print("[Tactical] ATTACK DD → kejar %s" % str(target.position))
	else:
		hero.move_to(BASE_RED)
		print("[Tactical] ATTACK DD → fallback nexus merah")
	Sound.play("move")

func _nearest_blue_tower() -> TowerUnit:
	var best = null
	var best_d := 999999.0
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team != "blue" or not t.is_alive():
			continue
		var d := hero.position.distance_to(t.position) if hero != null else 0.0
		if d < best_d:
			best = t
			best_d = d
	return best

func _nearest_blue_slot_pos() -> Vector2:
	var best := BASE_BLUE
	var best_d := 999999.0
	for s in slots:
		if str(s["team"]) != "blue":
			continue
		var p: Vector2 = s["pos"]
		var d := hero.position.distance_to(p) if hero != null else p.distance_to(BASE_BLUE)
		if d < best_d:
			best = p
			best_d = d
	return best

func _nearest_enemy_for_dd():
	var best = null
	var best_d := 999999.0
	for n in get_tree().get_nodes_in_group("heroes"):
		var h := n as HeroUnit
		if h == null or h.team == "blue" or not h.is_alive():
			continue
		var d := hero.position.distance_to(h.position)
		if d < best_d:
			best = h
			best_d = d
	if best != null:
		return best
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m.team == "blue" or not m.is_alive():
			continue
		var d := hero.position.distance_to(m.position)
		if d < best_d:
			best = m
			best_d = d
	if best != null:
		return best
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team == "blue" or not t.is_alive():
			continue
		var d := hero.position.distance_to(t.position)
		if d < best_d:
			best = t
			best_d = d
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx == null or nx.team == "blue" or not nx.is_alive():
			continue
		var d := hero.position.distance_to(nx.position)
		if d < best_d:
			best = nx
			best_d = d
	return best
# --- END TACTICAL L33 ---

func cast_hero_skill(i: int) -> void:
	if match_over or hero == null:
		return
	hero.cast_skill(i)


func toggle_pause() -> void:
	if match_over:
		return
	get_tree().paused = not get_tree().paused
	if get_tree().paused:
		pause_layer.show()
		print("[Main] Pause.")
	else:
		pause_layer.hide()
		print("[Main] Lanjut.")


func _next_or_menu() -> void:
	if victory:
		if not App.next_level():
			print("[Main] Level terakhir tamat! Kembali ke menu.")
			App.to_menu()
	else:
		App.restart_level()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey:
		var k := event as InputEventKey
		if k.pressed and not k.echo:
			if k.keycode == KEY_M:
				var m: bool = Sound.toggle_mute()
				print("[Main] Suara: %s." % ("MATI" if m else "NYALA"))
				return
			if match_over and k.keycode == KEY_R:
				App.restart_level()
				return
			if match_over and (k.keycode == KEY_ENTER or k.keycode == KEY_KP_ENTER):
				_next_or_menu()
				return
			if match_over and k.keycode == KEY_ESCAPE:
				App.to_menu()
				return
			if k.keycode == KEY_G:
				tactical_gather()
				return
			if k.keycode == KEY_T:
				tactical_protect_tower()
				return
			if k.keycode == KEY_C:
				tactical_protect_castle()
				return
			if k.keycode == KEY_B:
				tactical_attack_boss()
				return
			if k.keycode == KEY_D:
				tactical_attack_dd()
				return
			if k.keycode == KEY_H:
				if shop != null and not match_over:
					shop.toggle_mode("item")
					queue_redraw()
				return
			if k.keycode == KEY_ESCAPE and shop != null and shop.open:
				shop.toggle_mode(shop.mode)
				queue_redraw()
				return
	if match_over:
		return
	if shop != null and shop.open and event.is_action_pressed("pause"):
		shop.toggle_mode(shop.mode)
		queue_redraw()
		return
	if event.is_action_pressed("pause"):
		toggle_pause()
		return
	if event.is_action_pressed("toggle_shop"):
		if shop != null and not match_over:
			shop.toggle_mode("item")
			queue_redraw()
		return
	if event.is_action_pressed("skill_q"):
		cast_hero_skill(0)
		return
	if event.is_action_pressed("skill_w"):
		cast_hero_skill(1)
		return
	if event.is_action_pressed("skill_e"):
		cast_hero_skill(2)
		return
	if event.is_action_pressed("skill_r"):
		cast_hero_skill(3)
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			_on_left_click(get_global_mouse_position())
		if mb.button_index == MOUSE_BUTTON_RIGHT and mb.pressed:
			if shop != null and shop.open:
				if shop.handle_right_click(get_global_mouse_position()):
					queue_redraw()
					return
			if hero != null:
				hero.set_selected(false)
				print("[Main] Pilihan dibatalkan.")

# ═══════════════════════════════════════════
# LANGKAH 16 — ruins, spike trap, glow flower, torch (paritas pygame)
# ═══════════════════════════════════════════
const DECOR16_SEED := 1600
const TORCH16_XS := [120, 320, 520, 720, 920, 1120]
const TORCH16_YS := [120, 320, 520]
var _decor16_cache: Array = []

func _d16_min_dist(p: Vector2, pts: Array) -> float:
	var best := 99999.0
	for q in pts:
		var d: float = p.distance_to(q)
		if d < best:
			best = d
	return best

func _decor16_ok(p: Vector2, lanes: Array, river: Array, placed: Array, min_lane: float, want: String) -> bool:
	if p.x < 48.0 or p.x > 1232.0 or p.y < 48.0 or p.y > 672.0:
		return false
	var radiant: bool = p.y > _threshold_y(p.x)
	if want == "radiant" and not radiant:
		return false
	if want == "dire" and radiant:
		return false
	for pts in lanes:
		if _d16_min_dist(p, pts) < min_lane:
			return false
	if _d16_min_dist(p, river) < 60.0:
		return false
	if p.distance_to(BASE_BLUE) < 130.0:
		return false
	if p.distance_to(BASE_RED) < 130.0:
		return false
	if p.distance_to(Vector2(340, 540)) < 100.0:
		return false
	if p.distance_to(Vector2(940, 180)) < 100.0:
		return false
	for s in slots:
		var sp: Vector2 = s["pos"]
		if p.distance_to(sp) < 45.0:
			return false
	for q in placed:
		if p.distance_to(q) < 34.0:
			return false
	return true

func _gen_decor16() -> void:
	_decor16_cache.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = DECOR16_SEED
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var river: Array = _curved_path(RIVER_WP, 10)
	var placed: Array = []
	for i in range(10):
		var p := Vector2(rng.randf_range(48.0, 1232.0), rng.randf_range(48.0, 672.0))
		if _decor16_ok(p, lanes, river, placed, 60.0, "any"):
			placed.append(p)
			_decor16_cache.append(["ruin", p, rng.randi_range(0, 2)])
	for i in range(8):
		var p := Vector2(rng.randf_range(48.0, 1232.0), rng.randf_range(48.0, 672.0))
		if _decor16_ok(p, lanes, river, placed, 55.0, "dire"):
			placed.append(p)
			_decor16_cache.append(["spike", p, 0])
	for i in range(20):
		var p := Vector2(rng.randf_range(48.0, 1232.0), rng.randf_range(48.0, 672.0))
		if _decor16_ok(p, lanes, river, placed, 55.0, "radiant"):
			placed.append(p)
			_decor16_cache.append(["flower", p, rng.randi_range(0, 3)])

func _draw_decor16() -> void:
	if _decor16_cache.is_empty():
		_gen_decor16()
	for e in _decor16_cache:
		if e[0] == "ruin":
			_draw16_ruin(e[1], int(e[2]))
		elif e[0] == "spike":
			_draw16_spike(e[1])
		else:
			_draw16_flower(e[1], int(e[2]))
	for x in TORCH16_XS:
		_draw16_torch(Vector2(x, 32))
		_draw16_torch(Vector2(x, 688))
	for y in TORCH16_YS:
		_draw16_torch(Vector2(32, y))
		_draw16_torch(Vector2(1248, y))

func _draw16_ruin(p: Vector2, v: int) -> void:
	var x := p.x
	var y := p.y
	var ol := Color8(12, 8, 12)
	var sd := Color8(55, 55, 65)
	var sm := Color8(95, 95, 105)
	var sl := Color8(135, 135, 145)
	if v == 0:
		draw_rect(Rect2(x - 4, y - 15, 8, 17), ol)
		draw_rect(Rect2(x - 3, y - 14, 6, 15), sd)
		draw_rect(Rect2(x - 3, y - 14, 6, 12), sm)
		draw_rect(Rect2(x - 3, y - 14, 2, 12), sl)
		draw_colored_polygon(PackedVector2Array([Vector2(x - 4, y - 15), Vector2(x - 2, y - 18), Vector2(x + 1, y - 16), Vector2(x + 3, y - 19), Vector2(x + 4, y - 15)]), ol)
		draw_rect(Rect2(x - 6, y, 12, 4), ol)
		draw_rect(Rect2(x - 5, y + 1, 10, 3), sm)
	elif v == 1:
		draw_rect(Rect2(x - 8, y - 10, 3, 12), ol)
		draw_rect(Rect2(x - 7, y - 9, 2, 11), sm)
		draw_rect(Rect2(x + 5, y - 10, 3, 12), ol)
		draw_rect(Rect2(x + 6, y - 9, 2, 11), sm)
		draw_rect(Rect2(x - 8, y - 12, 5, 3), ol)
		draw_rect(Rect2(x - 7, y - 11, 3, 2), sm)
	else:
		draw_rect(Rect2(x - 6, y - 8, 12, 10), ol)
		draw_rect(Rect2(x - 5, y - 7, 10, 9), sd)
		draw_rect(Rect2(x - 5, y - 7, 10, 6), sm)
		draw_rect(Rect2(x - 5, y - 7, 4, 6), sl)
		draw_line(Vector2(x - 3, y - 5), Vector2(x + 2, y), ol, 1.0)
		draw_line(Vector2(x, y - 3), Vector2(x - 3, y + 1), ol, 1.0)

func _draw16_spike(p: Vector2) -> void:
	draw_set_transform(p + Vector2(0, 1), 0.0, Vector2(1.0, 0.375))
	draw_circle(Vector2.ZERO, 8.0, Color8(12, 8, 12))
	draw_circle(Vector2.ZERO, 7.0, Color8(30, 20, 18))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var y := p.y
	for i in range(4):
		var sx := p.x - 6.0 + float(i) * 4.0
		draw_colored_polygon(PackedVector2Array([Vector2(sx - 2, y), Vector2(sx + 2, y), Vector2(sx, y - 7)]), Color8(12, 8, 12))
		draw_colored_polygon(PackedVector2Array([Vector2(sx - 1, y - 1), Vector2(sx + 1, y - 1), Vector2(sx, y - 6)]), Color8(95, 95, 105))
		draw_rect(Rect2(sx, y - 6, 1, 2), Color8(150, 20, 20))

func _draw16_flower(p: Vector2, ci: int) -> void:
	var cols := [Color8(100, 170, 240), Color8(150, 100, 200), Color8(100, 200, 150), Color8(255, 200, 100)]
	var col: Color = cols[ci]
	var x := p.x
	var y := p.y
	for r in range(6, 2, -1):
		var a := float(40 - r * 5) / 255.0
		if a > 0.0:
			draw_circle(Vector2(x, y), float(r), Color(col.r, col.g, col.b, a))
	draw_rect(Rect2(x, y - 4, 1, 5), Color8(30, 60, 30))
	draw_rect(Rect2(x - 2, y - 1, 3, 2), Color8(60, 100, 50))
	draw_rect(Rect2(x - 2, y - 6, 5, 2), col)
	draw_rect(Rect2(x - 1, y - 8, 3, 5), col)
	draw_rect(Rect2(x - 1, y - 7, 2, 2), Color(minf(1.0, col.r + 0.235), minf(1.0, col.g + 0.235), minf(1.0, col.b + 0.235)))
	draw_rect(Rect2(x, y - 6, 1, 1), Color8(255, 240, 100))

func _draw16_torch(p: Vector2) -> void:
	var x := p.x
	var y := p.y
	var ol := Color8(12, 8, 12)
	var t0 := 9.0
	var t1 := 7.0
	var t2 := 5.0
	var lean := 0.0
	if _flame_frame == 1:
		t0 = 7.0
		t1 = 6.0
		t2 = 4.0
		lean = 1.0
	elif _flame_frame == 2:
		t0 = 10.0
		t1 = 8.0
		t2 = 6.0
		lean = -1.0
	elif _flame_frame == 3:
		t0 = 8.0
		t1 = 6.0
		t2 = 4.0
	var gs := 22 + (_flame_frame % 2) * 3
	for r in range(gs, 0, -4):
		var a := float(25 - r) / 255.0
		if a > 0.0:
			draw_circle(Vector2(x, y - 6), float(r), Color(1.0, 0.706, 0.314, a))
	draw_rect(Rect2(x - 3, y + 2, 6, 8), ol)
	draw_rect(Rect2(x - 3, y + 2, 6, 7), Color8(55, 55, 65))
	draw_rect(Rect2(x - 2, y + 3, 4, 5), Color8(95, 95, 105))
	draw_rect(Rect2(x - 1, y - 2, 2, 4), ol)
	draw_rect(Rect2(x - 1, y - 2, 2, 4), Color8(60, 40, 20))
	var ty := y - 2
	var fx := x + lean
	draw_colored_polygon(PackedVector2Array([Vector2(x - 3, ty), Vector2(x + 3, ty), Vector2(fx, ty - t0)]), Color8(190, 70, 10))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 2, ty), Vector2(x + 2, ty), Vector2(fx, ty - t1)]), Color8(240, 140, 25))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 1, ty), Vector2(x + 1, ty), Vector2(fx, ty - t2)]), Color8(255, 210, 90))
	draw_circle(Vector2(fx, ty - 1), 1.0, Color8(255, 245, 200))
	# ═══════════════════════════════════════════
# LANGKAH 17 — bayangan dekor16 + goresan merah lane (paritas bake)
# ═══════════════════════════════════════════
func _draw17_shadow(p: Vector2, w: float) -> void:
	draw_set_transform(p + Vector2(0, 2), 0.0, Vector2(1.0, 0.42))
	draw_circle(Vector2.ZERO, w, Color(0, 0, 0, 0.45))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw17_slashes() yang sudah ada (blok L17).
# Hook: sudah dipanggil dari _draw_decor17() — tidak ubah _draw() / urutan.
#
# Masalah: L17 lama garis 2px + highlight, panjang 10–18px → terlalu "darah tebal".
# Pygame lane crack: draw_line 1px warna path_crack (170,36,61), span ~7px di tile.
# Perubahan:
#   - count 42 → 28 (lebih jarang, mirip density crack bata L23)
#   - panjang half-span 2.5–4.5 (total ~5–9px)
#   - width 1.0 saja, warna Color8(170, 36, 61) = Forest path_crack
#   - hilangkan garis highlight kedua (yang bikin tebal)
#   - offset lateral -10..10 (sedikit lebih ke dalam lane)

# ═══════════════════════════════════════════
# LANGKAH 28 — ganti _draw17_slashes saja
# ═══════════════════════════════════════════
func _draw17_slashes() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1700
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var crack := Color8(170, 36, 61)
	for i in range(28):
		var pts: Array = lanes[rng.randi_range(0, 2)]
		var idx: int = rng.randi_range(0, pts.size() - 1)
		var a: Vector2 = pts[max(idx - 1, 0)]
		var b: Vector2 = pts[min(idx + 1, pts.size() - 1)]
		var tang: Vector2 = b - a
		var nrm := Vector2.UP
		if tang.length() > 0.01:
			nrm = Vector2(-tang.y, tang.x).normalized()
		var p: Vector2 = pts[idx] + nrm * rng.randf_range(-10.0, 10.0)
		var ang := rng.randf_range(0.0, PI)
		var half := rng.randf_range(2.5, 4.5)
		var d := Vector2(cos(ang), sin(ang)) * half
		draw_line(p - d, p + d, crack, 1.0)

func _draw_decor17() -> void:
	if _decor16_cache.is_empty():
		_gen_decor16()
	for e in _decor16_cache:
		var w := 5.0
		if e[0] == "ruin":
			w = 14.0 if int(e[2]) == 1 else 12.0
		elif e[0] == "spike":
			w = 9.0
		_draw17_shadow(e[1], w)
	_draw17_slashes()

# ═══════════════════════════════════════════
# LANGKAH 18 — bank sungai checker + titik magenta (paritas bake)
# ═══════════════════════════════════════════
func _draw_decor18() -> void:
	var river: Array = _curved_path(RIVER_WP, 10)
	if river.size() < 2:
		return
	var tile := 14.0
	var off := 36.0
	var c0 := Color8(10, 6, 14)
	var c1 := Color8(52, 22, 68)
	var dot := Color8(220, 80, 180)
	var half := Vector2(tile, tile) * 0.5
	var carry := tile * 0.5
	var k := 0
	for i in range(river.size() - 1):
		var a: Vector2 = river[i]
		var b: Vector2 = river[i + 1]
		var seg: Vector2 = b - a
		var seglen := seg.length()
		if seglen < 0.01:
			continue
		var dir: Vector2 = seg / seglen
		var nrm := Vector2(-dir.y, dir.x)
		var d := tile - carry
		while d < seglen:
			var c: Vector2 = a + dir * d
			var p1: Vector2 = c + nrm * off
			var p2: Vector2 = c - nrm * off
			draw_rect(Rect2(p1 - half, half * 2.0), c0 if k % 2 == 0 else c1)
			draw_rect(Rect2(p2 - half, half * 2.0), c1 if k % 2 == 0 else c0)
			if k % 4 == 0:
				var e1: Vector2 = c + nrm * 29.0
				var e2: Vector2 = c - nrm * 29.0
				draw_rect(Rect2(e1 - Vector2(1.5, 1.5), Vector2(3, 3)), dot)
				draw_rect(Rect2(e2 - Vector2(1.5, 1.5), Vector2(3, 3)), dot)
			k += 1
			d += tile
		carry = seglen - (d - tile)
var _flame_t := 0.0
var _flame_frame := 0

# ═══════════════════════════════════════════
# LANGKAH 20 — rune sungai + glow & asap toko (animasi ambient pygame)
# ═══════════════════════════════════════════
var _anim_t := 0.0

func _draw20_river_runes() -> void:
	var river: Array = _curved_path(RIVER_WP, 10)
	var glow := Color8(80, 150, 200)
	var foam := Color8(180, 210, 230)
	for i in range(river.size()):
		if i % 10 != 0:
			continue
		var pulse := (sin(_anim_t * 0.05 + float(i)) + 1.0) * 0.5
		if pulse <= 0.5:
			continue
		var pq: float = roundf(pulse * 10.0) / 10.0
		var r := maxf(1.0, pq * 4.0)
		var p: Vector2 = river[i]
		draw_circle(p, r * 2.0, Color(glow.r, glow.g, glow.b, 150.0 * pq / 255.0))
		draw_circle(p, r, Color(foam.r, foam.g, foam.b, 200.0 * pq / 255.0))

func _draw20_shop_fx() -> void:
	var pulse := (sin(_anim_t * 0.05) + 1.0) * 0.5
	var glow_r := 45.0 + pulse * 8.0
	var shops := [
		[Vector2(340, 540), Color8(100, 200, 255)],
		[Vector2(940, 180), Color8(255, 80, 80)],
	]
	for s in shops:
		var c: Vector2 = s[0]
		var col: Color = s[1]
		var r := glow_r
		while r > 15.0:
			var a := (glow_r - r) * 2.0 / 255.0
			if a > 0.0:
				draw_circle(Vector2(c.x, c.y - 5.0), r, Color(col.r, col.g, col.b, a))
			r -= 4.0
		var chim := Vector2(c.x + 19.0, c.y - 32.0)
		for j in range(3):
			var phase := fmod(_anim_t * 0.03 + float(j) * 2.0, 6.0)
			var sy := chim.y - phase * 8.0
			var sx := chim.x + sin(phase * 2.0 + float(j)) * 3.0
			var size := 3 - int(phase / 2.0)
			if size <= 0:
				continue
			var alpha := 180.0 - phase * 25.0
			if alpha <= 0.0:
				continue
			var ab := alpha / 255.0
			var smoke1 := Color8(100, 100, 110)
			smoke1.a = ab
			var smoke2 := Color8(150, 150, 160)
			smoke2.a = ab
			draw_circle(Vector2(sx, sy), float(size) * 2.0, smoke1)
			draw_circle(Vector2(sx, sy), float(size), smoke2)
			
# ═══════════════════════════════════════════
# LANGKAH 21 — kunang-kunang ambient (paritas pygame)
# ═══════════════════════════════════════════
var _decor21_cache: Array = []

func _gen_decor21() -> void:
	_decor21_cache.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = 2100
	var cols_r := [Color8(100, 200, 255), Color8(150, 255, 200), Color8(255, 220, 100)]
	var cols_d := [Color8(255, 100, 50), Color8(200, 50, 200), Color8(255, 50, 100)]
	for i in range(30):
		var b := Vector2(rng.randf_range(50.0, 1230.0), rng.randf_range(50.0, 670.0))
		var radiant: bool = b.y > _threshold_y(b.x)
		var col: Color = cols_r[rng.randi_range(0, 2)] if radiant else cols_d[rng.randi_range(0, 2)]
		var sz := 1
		if rng.randi_range(0, 2) == 2:
			sz = 2
		_decor21_cache.append([b,
			Vector2(rng.randf_range(6.0, 14.0), rng.randf_range(6.0, 14.0)),
			rng.randf_range(0.02, 0.035),
			rng.randf_range(0.0, TAU),
			sz, col])

func _draw21_particles() -> void:
	if _decor21_cache.is_empty():
		_gen_decor21()
	for e in _decor21_cache:
		var base: Vector2 = e[0]
		var amp: Vector2 = e[1]
		var sp: float = e[2]
		var ph: float = e[3]
		var size: int = e[4]
		var col: Color = e[5]
		var p := base + Vector2(sin(_anim_t * sp + ph) * amp.x, cos(_anim_t * sp * 0.8 + ph) * amp.y)
		var bright := (sin(_anim_t * 0.05 + ph) + 1.0) * 0.5
		if bright < 0.3:
			continue
		if bright > 0.7:
			var gr := float(size + 2)
			draw_circle(p, gr * 2.0, Color(col.r, col.g, col.b, 60.0 / 255.0))
			draw_circle(p, gr, Color(col.r, col.g, col.b, 120.0 / 255.0))
		draw_rect(Rect2(p, Vector2(size, size)), col)
		draw_rect(Rect2(p, Vector2(1, 1)), Color.WHITE)

# ═══════════════════════════════════════════
# LANGKAH 22 — kabut menggantung sisi dire (paritas pygame)
# ═══════════════════════════════════════════
var _decor22_cache: Array = []

func _gen_decor22() -> void:
	_decor22_cache.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = 2200
	for i in range(15):
		var bx := rng.randf_range(0.0, 1280.0)
		var by := rng.randf_range(0.0, 360.0)
		by = minf(by, _threshold_y(bx) - 30.0)
		by = maxf(by, 20.0)
		_decor22_cache.append([Vector2(bx, by),
			rng.randf_range(30.0, 60.0),
			rng.randf_range(-0.1, 0.1)])

func _draw22_fog() -> void:
	if _decor22_cache.is_empty():
		_gen_decor22()
	var col := Color8(80, 60, 60)
	col.a = 30.0 / 255.0
	for e in _decor22_cache:
		var base: Vector2 = e[0]
		var size: float = e[1]
		var vx: float = e[2]
		var x := fposmod(base.x + _anim_t * vx + 80.0, 1440.0) - 80.0
		draw_set_transform(Vector2(x, base.y), 0.0, Vector2(1.0, 0.5))
		draw_circle(Vector2.ZERO, size, col)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

# ═══════════════════════════════════════════
# LANGKAH 23 — lantai lane bata 16px + border stone (paritas draw_lane)
# ═══════════════════════════════════════════
var _decor23_tiles: Array = []
var _decor23_borders: Array = []

func _gen_decor23() -> void:
	_decor23_tiles.clear()
	_decor23_borders.clear()
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var seen := {}
	for pts in lanes:
		var n: int = pts.size()
		for i in range(n):
			var lp: Vector2 = pts[i]
			for dy in range(-42, 42, 16):
				for dx in range(-42, 42, 16):
					var tx := floori((lp.x + float(dx)) / 16.0) * 16
					var ty := floori((lp.y + float(dy)) / 16.0) * 16
					if tx < 0 or ty < 0 or tx >= 1280 or ty >= 720:
						continue
					var key := tx * 4096 + ty
					if seen.has(key):
						continue
					var ox := float(tx) + 8.0 - lp.x
					var oy := float(ty) + 8.0 - lp.y
					if ox * ox + oy * oy > 625.0:
						continue
					seen[key] = true
					_decor23_tiles.append(Vector2i(tx, ty))
		for i in range(0, n, 6):
			if i >= n - 1:
				continue
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			var dd: Vector2 = b - a
			var seglen := dd.length()
			if seglen < 0.01:
				continue
			var nx := -dd.y / seglen
			var ny := dd.x / seglen
			for side in [1.0, -1.0]:
				var bx := int(a.x + nx * side * 23.0)
				var by := int(a.y + ny * side * 23.0)
				if bx > 5 and bx < 1275 and by > 5 and by < 715:
					_decor23_borders.append(Vector2i(bx, by))

func _draw23_tile(t: Vector2i) -> void:
	var tx := float(t.x)
	var ty := float(t.y)
	var ps1 := Color8(58, 52, 45)
	var ps2 := Color8(85, 76, 65)
	var ps3 := Color8(115, 105, 90)
	var ps4 := Color8(145, 130, 108)
	var variant := (t.x * 3 + t.y * 7) % 100
	draw_rect(Rect2(tx, ty, 16, 16), ps1)
	if variant < 40:
		draw_rect(Rect2(tx + 1, ty + 1, 14, 14), ps2)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 12), ps3)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 2), ps4)
	elif variant < 70:
		draw_rect(Rect2(tx + 1, ty + 1, 14, 7), ps2)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 5), ps3)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 1), ps4)
		draw_rect(Rect2(tx + 1, ty + 9, 14, 6), ps2)
		draw_rect(Rect2(tx + 2, ty + 10, 12, 4), ps3)
	else:
		for sy_off in [0.0, 8.0]:
			for sx_off in [0.0, 8.0]:
				draw_rect(Rect2(tx + sx_off + 1, ty + sy_off + 1, 6, 6), ps2)
				draw_rect(Rect2(tx + sx_off + 2, ty + sy_off + 2, 4, 4), ps3)
				draw_rect(Rect2(tx + sx_off + 2, ty + sy_off + 2, 4, 1), ps4)
	if (t.x + t.y) % 7 == 0:
		draw_line(Vector2(tx + 3, ty + 4), Vector2(tx + 10, ty + 7), Color8(170, 36, 61), 1.0)
	if variant > 85:
		draw_rect(Rect2(tx + 3, ty + 3, 3, 2), Color8(65, 90, 45))
		draw_rect(Rect2(tx + 3, ty + 3, 2, 1), Color8(55, 90, 40))

func _draw23_border(b: Vector2i) -> void:
	var bx := float(b.x)
	var by := float(b.y)
	draw_rect(Rect2(bx - 5, by - 4, 10, 9), Color8(12, 8, 12))
	draw_rect(Rect2(bx - 4, by - 3, 8, 7), Color8(55, 55, 65))
	draw_rect(Rect2(bx - 3, by - 2, 6, 5), Color8(95, 95, 105))
	draw_rect(Rect2(bx - 3, by - 2, 6, 2), Color8(135, 135, 145))
	draw_rect(Rect2(bx - 3, by - 2, 3, 1), Color8(175, 175, 185))

func _draw_decor23() -> void:
	if _decor23_tiles.is_empty():
		_gen_decor23()
	for t in _decor23_tiles:
		_draw23_tile(t)
	for b in _decor23_borders:
		_draw23_border(b)

# ═══════════════════════════════════════════
# LANGKAH 24 — landmark dead-knight abaddon + panji (paritas bake)
# ═══════════════════════════════════════════
var _decor24_cache: Array = []

func _gen_decor24() -> void:
	_decor24_cache.clear()
	if _decor16_cache.is_empty():
		_gen_decor16()
	var rng := RandomNumberGenerator.new()
	rng.seed = 2400
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var river: Array = _curved_path(RIVER_WP, 10)
	var placed: Array = []
	for e in _decor16_cache:
		placed.append(e[1])
	var attempts := 0
	while _decor24_cache.size() < 30 and attempts < 240:
		attempts += 1
		var p := Vector2(float(rng.randi_range(3, 77)) * 16.0, float(rng.randi_range(3, 42)) * 16.0)
		if _decor16_ok(p, lanes, river, placed, 74.0, "any"):
			placed.append(p)
			_decor24_cache.append([p, rng.randi_range(0, 3)])

func _draw24_landmark(p: Vector2, v: int, banner: bool) -> void:
	var x := p.x
	var y := p.y
	draw_set_transform(Vector2(x, y + 7.5), 0.0, Vector2(1.0, 0.27))
	draw_circle(Vector2.ZERO, 13.0, Color8(6, 5, 10))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	draw_set_transform(Vector2(x, y + 0.5), 0.0, Vector2(1.0, 0.5))
	draw_circle(Vector2.ZERO, 9.0, Color8(52, 43, 53))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	draw_circle(Vector2(x - 8, y - 8), 5.0, Color8(70, 61, 71))
	draw_rect(Rect2(x - 12, y - 12, 8, 6), Color8(31, 25, 35))
	draw_line(Vector2(x + 2, y - 2), Vector2(x + 13, y - 20), Color8(161, 139, 145), 2.0)
	draw_line(Vector2(x + 9, y - 14), Vector2(x + 15, y - 19), Color8(195, 55, 73), 1.0)
	if v == 0:
		draw_line(Vector2(x - 5, y - 1), Vector2(x + 7, y - 1), Color8(120, 104, 112), 1.0)
		draw_line(Vector2(x - 2, y - 4), Vector2(x - 4, y + 4), Color8(120, 104, 112), 1.0)
	if banner:
		draw_line(Vector2(x - 16, y - 1), Vector2(x - 16, y - 27), Color8(89, 24, 43), 2.0)
		draw_colored_polygon(PackedVector2Array([Vector2(x - 16, y - 26), Vector2(x - 2, y - 21), Vector2(x - 16, y - 15)]), Color8(132, 25, 47))

func _draw_decor24() -> void:
	if _decor24_cache.is_empty():
		_gen_decor24()
	for i in range(_decor24_cache.size()):
		var e: Array = _decor24_cache[i]
		_draw24_landmark(e[0], int(e[1]), i % 6 == 0)

# ═══════════════════════════════════════════
# LANGKAH 25 — pohon mati twisted 2-tone + bayangan (paritas bake)
# ═══════════════════════════════════════════
var _decor25_cache: Array = []

func _gen_decor25() -> void:
	_decor25_cache.clear()
	if _decor16_cache.is_empty():
		_gen_decor16()
	if _decor24_cache.is_empty():
		_gen_decor24()
	var rng := RandomNumberGenerator.new()
	rng.seed = 2500
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var river: Array = _curved_path(RIVER_WP, 10)
	var placed: Array = []
	for e in _decor16_cache:
		placed.append(e[1])
	for e in _decor24_cache:
		placed.append(e[0])
	for d in decor:
		placed.append(d["pos"])
	var attempts := 0
	while _decor25_cache.size() < 35 and attempts < 400:
		attempts += 1
		var p := Vector2(float(rng.randi_range(2, 77)) * 16.0, float(rng.randi_range(2, 42)) * 16.0)
		if _decor16_ok(p, lanes, river, placed, 50.0, "dire"):
			placed.append(p)
			var sizes: Array = [14.0, 18.0, 22.0]
			_decor25_cache.append([p, sizes[rng.randi_range(0, 2)]])

func _draw25_dead_tree(p: Vector2, size: float) -> void:
	var s := size
	var d1 := Color8(28, 20, 18)
	var d2 := Color8(55, 42, 35)
	var ol := Color8(12, 8, 12)
	var shadow := Color(0.0, 0.0, 0.0, 80.0 / 255.0)
	var h := s * 0.5
	var q3 := float(floori(s / 3.0))
	# pygame: ellipse (x-size//2, y+size//3-2, size, size//3) → pusat + scale Y
	draw_set_transform(Vector2(p.x, p.y + q3 - 2.0 + q3 * 0.5), 0.0, Vector2(1.0, q3 / maxf(h * 2.0, 0.001)))
	draw_circle(Vector2.ZERO, h, shadow)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var tw := 4.0
	draw_rect(Rect2(p.x - tw * 0.5 - 1.0, p.y - s, tw + 2.0, s + 1.0), ol)
	draw_rect(Rect2(p.x - tw * 0.5, p.y - s, tw, s), d1)
	draw_rect(Rect2(p.x - tw * 0.5, p.y - s, 2.0, s), d2)
	var branches: Array = [
		[Vector2(p.x, p.y - h), Vector2(p.x - h, p.y - s + 4.0), 3.0],
		[Vector2(p.x, p.y - h + 4.0), Vector2(p.x + h, p.y - s + 4.0), 3.0],
		[Vector2(p.x, p.y - s + 4.0), Vector2(p.x - q3, p.y - s - 4.0), 2.0],
		[Vector2(p.x, p.y - s + 4.0), Vector2(p.x + q3, p.y - s - 2.0), 2.0],
	]
	for b in branches:
		var a: Vector2 = b[0]
		var e2: Vector2 = b[1]
		var w: float = b[2]
		draw_line(a, e2, d1, w)
		draw_line(a, e2, ol, 1.0)
		# tip cabang: ganti random.randint pygame → hash stabil dari posisi
		var jx := float((int(p.x) * 7 + int(p.y) * 13 + int(s)) % 7 - 3)
		var jy := float(-((int(p.x) * 5 + int(p.y) * 11 + int(s)) % 5))
		draw_line(e2, e2 + Vector2(jx, jy), d1, 1.0)

func _draw_decor25() -> void:
	if _decor25_cache.is_empty():
		_gen_decor25()
	for e in _decor25_cache:
		_draw25_dead_tree(e[0], float(e[1]))

# ═══════════════════════════════════════════
# LANGKAH 26 — bayangan hitam bawah dekor lama (paritas bake)
# ═══════════════════════════════════════════
func _draw26_shadow(p: Vector2, rx: float, ry: float, alpha: float) -> void:
	if rx <= 0.0 or ry <= 0.0:
		return
	draw_set_transform(p, 0.0, Vector2(1.0, ry / rx))
	draw_circle(Vector2.ZERO, rx, Color(0.0, 0.0, 0.0, alpha))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_decor26() -> void:
	for d in decor:
		var kind: String = str(d["kind"])
		var p: Vector2 = d["pos"]
		var v: int = int(d["v"])
		var k := 0.85 + 0.15 * float(v)
		match kind:
			"dark_tree":
				_draw26_shadow(Vector2(p.x, p.y + 14.0 * k), 12.0 * k, 6.0 * k, 100.0 / 255.0)
			"dead_tree":
				_draw26_shadow(Vector2(p.x, p.y + 6.0), 9.0 * k, 4.0 * k, 80.0 / 255.0)
			"bush":
				_draw26_shadow(Vector2(p.x, p.y + 5.0), 8.0 * k, 3.0 * k, 80.0 / 255.0)
			"rock", "rock_obs":
				_draw26_shadow(Vector2(p.x, p.y + 6.0 * k), 9.0 * k, 6.0 * k, 80.0 / 255.0)
			"gravestone":
				_draw26_shadow(Vector2(p.x, p.y + 7.0), 6.0, 2.0, 100.0 / 255.0)
