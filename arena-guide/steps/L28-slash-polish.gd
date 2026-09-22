# L28 — polish slash L17 → crack 1px tipis (paritas bake) — SNIPPET
# BUKAN append: GANTI hanya func _draw17_slashes() yang sudah ada (blok L17).
# Hook: sudah dipanggil dari _draw_decor17() — tidak ubah _draw() / urutan.
#
# Masalah: L17 lama garis 2px + highlight, panjang 10–18px → terlalu "darah tebal".
# Pygame lane crack: draw_line 1px warna path_crack (170,36,61), span ~7px di tile.
# Perubahan:
#   - count 42 → 28 (lebih jarang, mirip density crack bata L23)
#   - panjang half-span 2.5–4.5 (total ~5–9px)
#   - width 1.0 saja, warna Color8(170, 36, 61) = Forest path_crack
#   - hilangkan garis highlight kedua (yang bikin tebal)
#   - offset lateral -10..10 (sedikit lebih ke dalam lane)

# ═══════════════════════════════════════════
# LANGKAH 28 — ganti _draw17_slashes saja
# ═══════════════════════════════════════════
func _draw17_slashes() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1700
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var crack := Color8(170, 36, 61)
	for i in range(28):
		var pts: Array = lanes[rng.randi_range(0, 2)]
		var idx: int = rng.randi_range(0, pts.size() - 1)
		var a: Vector2 = pts[max(idx - 1, 0)]
		var b: Vector2 = pts[min(idx + 1, pts.size() - 1)]
		var tang: Vector2 = b - a
		var nrm := Vector2.UP
		if tang.length() > 0.01:
			nrm = Vector2(-tang.y, tang.x).normalized()
		var p: Vector2 = pts[idx] + nrm * rng.randf_range(-10.0, 10.0)
		var ang := rng.randf_range(0.0, PI)
		var half := rng.randf_range(2.5, 4.5)
		var d := Vector2(cos(ang), sin(ang)) * half
		draw_line(p - d, p + d, crack, 1.0)
