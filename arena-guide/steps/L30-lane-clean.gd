# L30 — lane-clean (REVISI 2026-09-23: PARITAS PYGAME — BATALKAN L30a lama)
# Tiga suntingan terpisah:
#   A) KEMBALIKAN const LANE_MID_WP ke waypoint pygame FINAL (jangan pakai versi halus)
#   B) Ganti func _draw_lanes + _draw_cobble (hapus cobble di bawah bata L23) — TETAP
#   C) Di Hud.gd: sembunyikan _hint_l (teks "Klik hero = pilih ...") — TETAP
#
# REVISI: L30a lama (280,450→400,380→...) adalah deviasi visual yang memutus
# paritas pygame. Atas instruksi user 2026-09-23: posisi & visual pygame FINAL,
# maka LANE_MID_WP DIKEMBALIKAN ke nilai pygame asli (PathGenerator.generate_lanes).
# Bata patah di tengah memang ada di pygame asli — jangan dihaluskan.
# Penyebab "banyak tulisan": Hud.gd label hint kanan-bawah menimpa map.

# ═══════════════════════════════════════════
# A — KEMBALIKAN const LANE_MID_WP ke PYGAME FINAL (biarkan TOP/BOT — sudah paritas)
# ═══════════════════════════════════════════
const LANE_MID_WP = [
	Vector2(170, 550), Vector2(300, 420), Vector2(440, 320),
	Vector2(580, 400), Vector2(640, 360), Vector2(700, 320),
	Vector2(840, 400), Vector2(980, 300), Vector2(1110, 170)
]
# PARITAS: map_components/_bundle.py → PathGenerator.generate_lanes(1280,720)
# mid smooth = 8 (bukan 10). Nilai DULU yang SALAH (jangan dipakai):
# [ (170,550),(280,450),(400,380),(520,350),(640,340),(760,330),(880,300),(1000,240),(1110,170) ]

# ═══════════════════════════════════════════
# B — ganti _draw_lanes (tanpa cobble; hanya base + L23 yang menutupi)
#    _draw_cobble boleh dibiarkan di file (tidak dipanggil) ATAU dihapus.
# ═══════════════════════════════════════════
func _draw_lanes() -> void:
	if map_theme.is_empty():
		return
	var p1: Color = map_theme["p1"]
	for li in lane_paths.size():
		var path: PackedVector2Array = lane_paths[li]
		# dasar gelap sedikit lebih lebar dari bata agar tepi tidak bolong
		draw_polyline(path, Color8(12, 8, 12), 52.0)
		draw_polyline(path, p1, 46.0)

# ═══════════════════════════════════════════
# C — di Hud.gd, di setup() SETELAH _hint_l dibuat, tambah:
# ═══════════════════════════════════════════
#	_hint_l.visible = false
# (atau hapus baris _hint_l.text = "Klik hero ...")
