# WavePlate.gd — panel dekorasi banner wave (port WaveAnnouncer.draw panel,
# _render.py:1022-1076): latar gradasi vertikal gelap + border emas 3px +
# garis dalam terang 1px + garis diagonal + corner ticks emas. Semua warna &
# ukuran persis pygame (panel 400x80, diag tiap 10px, ticks length 12 /
# width 2 / inset 5). Alpha fade ditangani modulate node oleh tween HUD,
# jadi _draw selalu alpha penuh.
extends Control

const PANEL_W := 400.0
const PANEL_H := 80.0
const GOLD_BORDER := Color(1.0, 220.0 / 255.0, 50.0 / 255.0)
const GOLD_INNER := Color(1.0, 250.0 / 255.0, 180.0 / 255.0)
const BG := Color(16.0 / 255.0, 20.0 / 255.0, 40.0 / 255.0)


func _init() -> void:
	custom_minimum_size = Vector2(PANEL_W, PANEL_H)
	size = Vector2(PANEL_W, PANEL_H)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	var w := size.x
	var h := size.y
	# Latar gradasi vertikal (16,20,40) — alpha "melengkung" 0.3 di tepi
	# atas/bawah (paritas grad_alpha pygame: 1 - |i-h/2|/(h/2)*0.3).
	var rows := 32
	for i in range(rows):
		var t := (float(i) + 0.5) / float(rows)
		var edge := 1.0 - absf(t - 0.5) * 2.0 * 0.3
		draw_rect(Rect2(0.0, t * h, w, h / float(rows) + 1.0),
			Color(BG.r, BG.g, BG.b, edge))
	# Border emas 3px + garis dalam terang 1px (offset 2px).
	draw_rect(Rect2(0, 0, w, h), GOLD_BORDER, false, 3.0)
	draw_rect(Rect2(2, 2, w - 4, h - 4), GOLD_INNER, false, 1.0)
	# Garis diagonal tiap 10px, alpha 1/4 (paritas pygame).
	var diag := Color(GOLD_BORDER.r, GOLD_BORDER.g, GOLD_BORDER.b, 0.25)
	var x := 0.0
	while x < w:
		draw_line(Vector2(x, 0.0), Vector2(x + 10.0, h), diag, 1.0)
		x += 10.0
	# Corner ticks emas: length 12, width 2, inset 5.
	var length := 12.0
	var inset := 5.0
	for corner in [Vector2(inset, inset), Vector2(w - inset, inset),
			Vector2(inset, h - inset), Vector2(w - inset, h - inset)]:
		var sx := 1.0 if corner.x < w * 0.5 else -1.0
		var sy := 1.0 if corner.y < h * 0.5 else -1.0
		draw_line(corner, corner + Vector2(length * sx, 0.0),
			GOLD_BORDER, 2.0)
		draw_line(corner, corner + Vector2(0.0, length * sy),
			GOLD_BORDER, 2.0)
