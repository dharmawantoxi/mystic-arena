# L26 — bayangan hitam bawah dekor lama (paritas bake) — DONE
# SNIPPET: tempel di AKHIR Main.gd (setelah blok L25).
# Hook di _draw(): panggil _draw_decor26() SETELAH _draw_border_wall() SEBELUM _draw_decor().
#   urutan: ... border_wall, decor26, decor, decor25, decor17, decor16, decor24, shops ...
# Bayangan digambar DULU supaya dekor menimpa di atasnya (seperti ellipse pygame).
# Referensi pygame: dark_trees alpha100 size×size; dead_trees 80; bushes 80; rocks 80; grave 100.

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
