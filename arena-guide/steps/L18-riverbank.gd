# L18 — bank sungai checker + titik magenta (paritas bake)
# SNIPPET: tempel di AKHIR Main.gd.
# Hook: _draw_decor18() SETELAH _draw_river() SEBELUM _draw_lanes().

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
