# L25 — pohon mati twisted 2-tone + bayangan (paritas bake) — SNIPPET
# SNIPPET: tempel di AKHIR Main.gd (setelah blok L24).
# Hook di _draw(): panggil _draw_decor25() SETELAH _draw_decor() SEBELUM _draw_decor17().
#   urutan: ... border_wall, decor, decor25, decor17, decor16, decor24, shops ...
# Placement: sisi DIRE saja, seed 2500, max 35, size [14,18,22], grid 16px.
# Clearance menumpang _decor16_ok (min_lane 50) + posisi L16/L24 + decor lama.
# Warna: DEAD_TREE_1=(28,20,18) DEAD_TREE_2=(55,42,35) OUTLINE=(12,8,12)
# Bayangan elips alpha 80 (pygame: ellipse size//2 × size//3 di y+size//3-2).
# Cabang tip: deterministik dari (x,y,size) — tanpa RandomNumberGenerator di _draw.

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
