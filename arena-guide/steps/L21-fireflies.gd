# L21 — kunang-kunang ambient (paritas pygame)
# SNIPPET: tempel di AKHIR Main.gd.
# Hook: _draw21_particles() setelah _draw20_shop_fx() sebelum loop slots.
# Catatan: warna ikut sisi DIAGONAL (deviasi disengaja dari pygame halves).

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
