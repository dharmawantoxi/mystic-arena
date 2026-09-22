# L23 — lantai lane bata 16px + border stone (paritas draw_lane) — FINAL
# SNIPPET: tempel di AKHIR Main.gd.
# Hook: _draw_decor23() SETELAH _draw_lanes() SEBELUM _draw_base_plates().
# FIX: `len` → `seglen` (SHADOWED_GLOBAL_IDENTIFIER).

# ═══════════════════════════════════════════
# LANGKAH 23 — lantai lane bata 16px + border stone (paritas draw_lane)
# ═══════════════════════════════════════════
var _decor23_tiles: Array = []
var _decor23_borders: Array = []

func _gen_decor23() -> void:
	_decor23_tiles.clear()
	_decor23_borders.clear()
	var lanes: Array = [
		_curved_path(LANE_TOP_WP, 10),
		_curved_path(LANE_MID_WP, 8),
		_curved_path(LANE_BOT_WP, 10),
	]
	var seen := {}
	for pts in lanes:
		var n: int = pts.size()
		for i in range(n):
			var lp: Vector2 = pts[i]
			for dy in range(-42, 42, 16):
				for dx in range(-42, 42, 16):
					var tx := floori((lp.x + float(dx)) / 16.0) * 16
					var ty := floori((lp.y + float(dy)) / 16.0) * 16
					if tx < 0 or ty < 0 or tx >= 1280 or ty >= 720:
						continue
					var key := tx * 4096 + ty
					if seen.has(key):
						continue
					var ox := float(tx) + 8.0 - lp.x
					var oy := float(ty) + 8.0 - lp.y
					if ox * ox + oy * oy > 625.0:
						continue
					seen[key] = true
					_decor23_tiles.append(Vector2i(tx, ty))
		for i in range(0, n, 6):
			if i >= n - 1:
				continue
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			var dd: Vector2 = b - a
			var seglen := dd.length()
			if seglen < 0.01:
				continue
			var nx := -dd.y / seglen
			var ny := dd.x / seglen
			for side in [1.0, -1.0]:
				var bx := int(a.x + nx * side * 23.0)
				var by := int(a.y + ny * side * 23.0)
				if bx > 5 and bx < 1275 and by > 5 and by < 715:
					_decor23_borders.append(Vector2i(bx, by))

func _draw23_tile(t: Vector2i) -> void:
	var tx := float(t.x)
	var ty := float(t.y)
	var ps1 := Color8(58, 52, 45)
	var ps2 := Color8(85, 76, 65)
	var ps3 := Color8(115, 105, 90)
	var ps4 := Color8(145, 130, 108)
	var variant := (t.x * 3 + t.y * 7) % 100
	draw_rect(Rect2(tx, ty, 16, 16), ps1)
	if variant < 40:
		draw_rect(Rect2(tx + 1, ty + 1, 14, 14), ps2)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 12), ps3)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 2), ps4)
	elif variant < 70:
		draw_rect(Rect2(tx + 1, ty + 1, 14, 7), ps2)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 5), ps3)
		draw_rect(Rect2(tx + 2, ty + 2, 12, 1), ps4)
		draw_rect(Rect2(tx + 1, ty + 9, 14, 6), ps2)
		draw_rect(Rect2(tx + 2, ty + 10, 12, 4), ps3)
	else:
		for sy_off in [0.0, 8.0]:
			for sx_off in [0.0, 8.0]:
				draw_rect(Rect2(tx + sx_off + 1, ty + sy_off + 1, 6, 6), ps2)
				draw_rect(Rect2(tx + sx_off + 2, ty + sy_off + 2, 4, 4), ps3)
				draw_rect(Rect2(tx + sx_off + 2, ty + sy_off + 2, 4, 1), ps4)
	if (t.x + t.y) % 7 == 0:
		draw_line(Vector2(tx + 3, ty + 4), Vector2(tx + 10, ty + 7), Color8(170, 36, 61), 1.0)
	if variant > 85:
		draw_rect(Rect2(tx + 3, ty + 3, 3, 2), Color8(65, 90, 45))
		draw_rect(Rect2(tx + 3, ty + 3, 2, 1), Color8(55, 90, 40))

func _draw23_border(b: Vector2i) -> void:
	var bx := float(b.x)
	var by := float(b.y)
	draw_rect(Rect2(bx - 5, by - 4, 10, 9), Color8(12, 8, 12))
	draw_rect(Rect2(bx - 4, by - 3, 8, 7), Color8(55, 55, 65))
	draw_rect(Rect2(bx - 3, by - 2, 6, 5), Color8(95, 95, 105))
	draw_rect(Rect2(bx - 3, by - 2, 6, 2), Color8(135, 135, 145))
	draw_rect(Rect2(bx - 3, by - 2, 3, 1), Color8(175, 175, 185))

func _draw_decor23() -> void:
	if _decor23_tiles.is_empty():
		_gen_decor23()
	for t in _decor23_tiles:
		_draw23_tile(t)
	for b in _decor23_borders:
		_draw23_border(b)
