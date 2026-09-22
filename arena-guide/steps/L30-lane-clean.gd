# L30 — lane rapi (mid smooth) + hilangkan teks hint di map — SNIPPET
# Tiga suntingan terpisah:
#   A) Ganti const LANE_MID_WP (titik lebih halus, tanpa zig-zag tajam)
#   B) Ganti func _draw_lanes + _draw_cobble (hapus cobble di bawah bata L23)
#   C) Di Hud.gd: sembunyikan _hint_l (teks "Klik hero = pilih ...")
#
# Penyebab "lane patah":
#   mid WP lama punya 4 belokan >60° di tengah → bata 16px axis-aligned
#   terlihat retak/patah; cobble L15 di bawah L23 juga dobel-tekstur.
# Penyebab "banyak tulisan":
#   Hud.gd label hint kanan-bawah menimpa map (selain GOLD/WAVE/skill yang sah).

# ═══════════════════════════════════════════
# A — ganti const LANE_MID_WP (biarkan TOP/BOT)
# ═══════════════════════════════════════════
const LANE_MID_WP = [
	Vector2(170, 550), Vector2(280, 450), Vector2(400, 380),
	Vector2(520, 350), Vector2(640, 340), Vector2(760, 330),
	Vector2(880, 300), Vector2(1000, 240), Vector2(1110, 170)
]

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
