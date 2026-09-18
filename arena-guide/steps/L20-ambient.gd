# L20 — rune sungai + glow & asap toko (animasi ambient pygame) — FINAL
# SNIPPET: tempel blok di AKHIR Main.gd.
# B. Tambah 1 baris `_anim_t += 9.0` di blok heartbeat _process (L19).
# C. Dua hook: _draw20_river_runes() setelah decor18 sebelum lanes;
#    _draw20_shop_fx() setelah _draw_shops() sebelum loop slots.
# FIX: `var pq: float = roundf(...)` (round → Variant, gagal infer dengan :=).

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

# ---- B. isi blok heartbeat menjadi: ----
# 	if _flame_t >= 0.15:
# 		_flame_t = 0.0
# 		_flame_frame = (_flame_frame + 1) % 4
# 		_anim_t += 9.0
# 		queue_redraw()
