# L22 — kabut menggantung sisi dire (paritas pygame)
# SNIPPET: tempel di AKHIR Main.gd.
# Hook: _draw22_fog() tepat SEBELUM `if match_over:` (1 Tab, di dalam _draw()).

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
