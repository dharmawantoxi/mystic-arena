# L32 — lane rapi total (anti-berantakan) — SNIPPET
# Masalah \"jalur lane berantakan\":
#   1) MID zig-zag (project/Main.gd lama): 4 belokan >60° di tengah → bata 16px axis-aligned retak
#   2) LANE_SMOOTH [10,8,10] — mid hanya 8 step/Catmull segmen → sudut patah kelihatan
#   3) _draw_lanes lama menggambar cobble 14x38 per 16px + border stone dobel di bawah bata L23 → dobel tekstur, berat, retak
#   4) _gen_decor23 radius 25px terlalu kecil → tepi lane bolong stair-step; border tiap 6 idx tidak merata
#   5) crack tiap 7 tile + moss 15% terlalu ramai → lane terlihat bercak-bercak
#
# Solusi (paritas pygame PathGenerator + StaticRenderer.draw_lane):
#   A) WAYPOINT RAPI: TOP/BOT tetap, MID monotonic diagonal halus (9 titik, tanpa belokan tajam)
#   B) SMOOTH UNIFORM [12,12,12]: mid dari 8→12, top/bot 10→12 — kurva Catmull lebih halus, join bulat
#   C) _draw_lanes MINIMAL: hanya outline 52px + p1 46px (bata di _decor23 yang menutup) — tanpa cobble dobel
#   D) Bata 16px lebih rapat: radius 27px (729) + border jarak-tempuh 32px (bukan tiap 6 idx) → tepi tidak bolong, batu merata
#   E) Dekor lane lebih bersih: crack %7→%11, moss >85→>90, highlight tengah tipis untuk kedalaman

# ═══════════════════════════════════════════
# A+B — ganti const waypoint + smooth (tempel di atas, ganti 3 baris lama)
# ═══════════════════════════════════════════
const LANE_TOP_WP = [Vector2(90, 590), Vector2(85, 460), Vector2(95, 340), Vector2(115, 230), Vector2(165, 175), Vector2(235, 110), Vector2(360, 78), Vector2(520, 68), Vector2(690, 70), Vector2(860, 80), Vector2(1020, 115), Vector2(1180, 180)]
const LANE_MID_WP = [Vector2(170, 550), Vector2(280, 450), Vector2(400, 380), Vector2(520, 350), Vector2(640, 340), Vector2(760, 330), Vector2(880, 300), Vector2(1000, 240), Vector2(1110, 170)]
const LANE_BOT_WP = [Vector2(130, 630), Vector2(265, 652), Vector2(415, 662), Vector2(590, 665), Vector2(770, 660), Vector2(935, 650), Vector2(1065, 625), Vector2(1135, 565), Vector2(1170, 500), Vector2(1185, 410), Vector2(1190, 320), Vector2(1185, 235), Vector2(1180, 180)]
const LANE_SMOOTH = [12, 12, 12]

# ═══════════════════════════════════════════
# C — ganti func _draw_lanes (hapus cobble lama)
# ═══════════════════════════════════════════
func _draw_lanes() -> void:
	if map_theme.is_empty():
		return
	var p1: Color = map_theme["p1"]
	var p2: Color = map_theme["p2"]
	for li in lane_paths.size():
		var path: PackedVector2Array = lane_paths[li]
		# outline gelap sedikit lebih lebar agar bata 16px tidak bocor di tepi diagonal
		draw_polyline(path, Color8(12, 8, 12), 52.0, true)
		draw_polyline(path, p1, 46.0, true)
		# highlight tengah tipis — kedalaman tanpa menambah tekstur (alpha rendah, tidak dobel)
		draw_polyline(path, Color(p2.r, p2.g, p2.b, 0.28), 10.0, true)

# _draw_cobble / _draw_border_stone boleh dibiarkan (tidak dipanggil) — legacy.

# ═══════════════════════════════════════════
# D+E — ganti func _gen_decor23 + _draw23_tile (rapi, tidak berantakan)
# ═══════════════════════════════════════════
var _decor23_tiles: Array = []
var _decor23_borders: Array = []

func _gen_decor23() -> void:
	_decor23_tiles.clear()
	_decor23_borders.clear()
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, int(LANE_SMOOTH[0])),
		_curved_path(LANE_MID_WP, int(LANE_SMOOTH[1])),
		_curved_path(LANE_BOT_WP, int(LANE_SMOOTH[2])),
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
					# 27px radius (729) — sebelumnya 25px (625) menyisakan celah stair-step di diagonal
					if ox * ox + oy * oy > 729.0:
						continue
					seen[key] = true
					_decor23_tiles.append(Vector2i(tx, ty))
		# border batu jarak-tempuh 32px (merata, bukan tiap 6 indeks yang rapat-renggang)
		var acc := 0.0
		var next_border := 0.0
		for i in range(n - 1):
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			var seg := b - a
			var seglen := seg.length()
			if seglen < 0.01:
				continue
			var dir := seg / seglen
			var nrm := Vector2(-dir.y, dir.x)
			while next_border <= acc + seglen:
				var t := (next_border - acc) / seglen
				var p: Vector2 = a.lerp(b, t)
				for side in [1.0, -1.0]:
					var bx := int(p.x + nrm.x * side * 23.0)
					var by := int(p.y + nrm.y * side * 23.0)
					if bx > 5 and bx < 1275 and by > 5 and by < 715:
						_decor23_borders.append(Vector2i(bx, by))
				next_border += 32.0
			acc += seglen

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
	# crack lebih jarang: %11 (9% tile) — sebelumnya %7 (14%) terlalu ramai & memotong bata
	if (t.x + t.y) % 11 == 0:
		draw_line(Vector2(tx + 3, ty + 4), Vector2(tx + 10, ty + 7), Color8(170, 36, 61), 1.0)
	# moss lebih jarang: >90 (10%) — sebelumnya >85 (15%) bikin bercak hijau berlebihan
	if variant > 90:
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
