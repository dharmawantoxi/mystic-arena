# L24 — landmark dead-knight abaddon + panji (paritas bake) — DONE
# SNIPPET: tempel di AKHIR Main.gd.
# Hook: _draw_decor24() SETELAH _draw_decor16() SEBELUM _draw_shops().
# Clearance menumpang _decor16_ok (min_lane 74) + posisi L16 (anti-tumpuk).

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
