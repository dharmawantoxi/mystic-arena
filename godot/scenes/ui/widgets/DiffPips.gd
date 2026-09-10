# DiffPips.gd — 5 pip indikator difficulty (port kartu level/unlock pygame).
#
# Pip menyala: hijau - emas - emas - merah - merah; mati: abu gelap.
extends Control
class_name DiffPips

var level: int = 1
var pip_w: float = 14.0
var pip_h: float = 6.0
var gap: float = 4.0


func _init(p_level: int = 1, p_w: float = 14.0, p_h: float = 6.0,
		p_gap: float = 4.0) -> void:
	level = clampi(p_level, 0, 5)
	pip_w = p_w
	pip_h = p_h
	gap = p_gap
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(5.0 * p_w + 4.0 * p_gap, p_h)


func set_level(p_level: int) -> void:
	level = clampi(p_level, 0, 5)
	queue_redraw()


func _draw() -> void:
	for i in range(5):
		var col: Color
		if i < level:
			if i >= 3:
				col = Color(1.0, 100.0 / 255.0, 80.0 / 255.0)
			elif i >= 1:
				col = Color(1.0, 200.0 / 255.0, 80.0 / 255.0)
			else:
				col = UiTheme.GREEN
		else:
			col = Color(46.0 / 255.0, 50.0 / 255.0, 66.0 / 255.0)
		UiTheme.draw_rr(self,
			Rect2(i * (pip_w + gap), 0, pip_w, pip_h), col, 2.0)
