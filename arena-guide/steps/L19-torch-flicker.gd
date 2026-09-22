# L19 — api obor berkedip (animasi 4 frame) + heartbeat _process
# A. HAPUS TOTAL func _draw16_torch lama (versi statis L16), GANTI dengan versi bawah ini.
# B. Paste 2 baris var di AKHIR file.
# C. Heartbeat: kalau func _process BELUM ada → paste blok utuh; kalau SUDAH ada →
#    JANGAN bikin baru, gabungkan 5 baris isi ke _process lama.

# ---- A. pengganti _draw16_torch (animasi) ----
func _draw16_torch(p: Vector2) -> void:
	var x := p.x
	var y := p.y
	var ol := Color8(12, 8, 12)
	var t0 := 9.0
	var t1 := 7.0
	var t2 := 5.0
	var lean := 0.0
	if _flame_frame == 1:
		t0 = 7.0
		t1 = 6.0
		t2 = 4.0
		lean = 1.0
	elif _flame_frame == 2:
		t0 = 10.0
		t1 = 8.0
		t2 = 6.0
		lean = -1.0
	elif _flame_frame == 3:
		t0 = 8.0
		t1 = 6.0
		t2 = 4.0
	var gs := 22 + (_flame_frame % 2) * 3
	for r in range(gs, 0, -4):
		var a := float(25 - r) / 255.0
		if a > 0.0:
			draw_circle(Vector2(x, y - 6), float(r), Color(1.0, 0.706, 0.314, a))
	draw_rect(Rect2(x - 3, y + 2, 6, 8), ol)
	draw_rect(Rect2(x - 3, y + 2, 6, 7), Color8(55, 55, 65))
	draw_rect(Rect2(x - 2, y + 3, 4, 5), Color8(95, 95, 105))
	draw_rect(Rect2(x - 1, y - 2, 2, 4), ol)
	draw_rect(Rect2(x - 1, y - 2, 2, 4), Color8(60, 40, 20))
	var ty := y - 2
	var fx := x + lean
	draw_colored_polygon(PackedVector2Array([Vector2(x - 3, ty), Vector2(x + 3, ty), Vector2(fx, ty - t0)]), Color8(190, 70, 10))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 2, ty), Vector2(x + 2, ty), Vector2(fx, ty - t1)]), Color8(240, 140, 25))
	draw_colored_polygon(PackedVector2Array([Vector2(x - 1, ty), Vector2(x + 1, ty), Vector2(fx, ty - t2)]), Color8(255, 210, 90))
	draw_circle(Vector2(x, ty - 1), 1.0, Color8(255, 245, 200))

# ---- B. member (akhir file) ----
var _flame_t := 0.0
var _flame_frame := 0

# ---- C. heartbeat (baru ATAU gabung ke _process lama) ----
func _process(delta: float) -> void:
	_flame_t += delta
	if _flame_t >= 0.15:
		_flame_t = 0.0
		_flame_frame = (_flame_frame + 1) % 4
		queue_redraw()
