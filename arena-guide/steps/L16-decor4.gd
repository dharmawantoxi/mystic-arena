# L16 — ruins, spike trap, glow flower, torch (paritas pygame) — FINAL
# SNIPPET: tempel seluruh blok di AKHIR Main.gd.
# Hook: _draw_decor16() di antara _draw_decor() dan _draw_shops().
# Catatan: versi final sudah memakai member slots asli (s["pos"]); JANGAN kembalikan
# blok hitung slot lama (menyebabkan SHADOWED_VARIABLE + error Dictionary).
# Api di sini versi STATIS; versi animasi ada di L19-torch-flicker.gd.

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
	for r in range(22, 0, -4):
		var a := float(25 - r) / 255.0
		if a > 0.0:
			draw_circle(Vector2(x, y - 6), float(r), Color(1.0, 0.706, 0.314, a))
	draw_rect(Rect2(x - 3, y + 2, 6, 8), ol)
	draw_rect(Rect2(x - 3, y + 2, 6, 7), Color8(55, 55, 65))
	draw_rect(Rect2(x - 2, y + 3, 4, 5), Color8(95, 95, 105))
	draw_rect(Rect2(x - 1, y - 2, 2, 4), ol)
	draw_rect(Rect2(x - 1, y - 2, 2, 4), Color8(60, 40, 20))
	var ty := y - 2
	draw_colored_polygon(PackedVector2Array([Vector2(x - 3, ty), Vector2(x + 3, ty), Vector2(x, ty - 9)]), Color8(190, 70, 10))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 2, ty), Vector2(x + 2, ty), Vector2(x, ty - 7)]), Color8(240, 140, 25))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 1, ty), Vector2(x + 1, ty), Vector2(x, ty - 5)]), Color8(255, 210, 90))
	draw_circle(Vector2(x, ty - 1), 1.0, Color8(255, 245, 200))
