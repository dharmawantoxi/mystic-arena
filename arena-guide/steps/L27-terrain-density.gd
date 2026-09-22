# L27 — ground micro-detail density + palette fix (paritas bake) — SNIPPET
# BUKAN append: GANTI dua fungsi yang sudah ada di Main.gd.
# 1) Ganti SELURUH func _draw_terrain() ... (sampai sebelum _draw_terrain_details)
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
