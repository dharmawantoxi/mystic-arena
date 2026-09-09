# MysticSliderRow.gd — baris volume settings (port _draw_volume_row):
# label kiri + bar gradasi vertikal + pill −/+ + label persen. Update:
# set_value(v, maxv) menggambar ulang; sinyal changed(value) dipancar.
extends Control
class_name MysticSliderRow

signal changed(value: float)

@export var row_label: String = "Volume":
	set(v):
		row_label = v
		queue_redraw()
@export var max_value: float = 1.0:
	set(v):
		max_value = v
		queue_redraw()
@export var row_value: float = 0.7:
	set(v):
		row_value = v
		queue_redraw()
@export var step: float = 0.05

var _minus_rect := Rect2()
var _plus_rect := Rect2()
var _bar_rect := Rect2()
var _minus_hover := false
var _plus_hover := false


func _init(p_label: String = "Volume", p_value: float = 0.7,
		p_max: float = 1.0) -> void:
	row_label = p_label
	row_value = p_value
	max_value = p_max
	custom_minimum_size = Vector2(280, 56)
	mouse_filter = Control.MOUSE_FILTER_STOP


func set_value(v: float, silent: bool = true) -> void:
	row_value = clampf(v, 0.0, max_value)
	if not silent:
		changed.emit(row_value)
	queue_redraw()


func _ready() -> void:
	mouse_exited.connect(func() -> void:
		_minus_hover = false
		_plus_hover = false
		queue_redraw())


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var m := event as InputEventMouseMotion
		_minus_hover = _minus_rect.has_point(m.position)
		_plus_hover = _plus_rect.has_point(m.position)
		queue_redraw()
	elif event is InputEventMouseButton:
		var b := event as InputEventMouseButton
		if b.button_index == MOUSE_BUTTON_LEFT and b.pressed:
			if _minus_rect.has_point(b.position):
				set_value(row_value - step, false)
			elif _plus_rect.has_point(b.position):
				set_value(row_value + step, false)
			elif _bar_rect.has_point(b.position):
				var t := (b.position.x - _bar_rect.position.x) / maxf(1.0,
					_bar_rect.size.x)
				set_value(t * max_value, false)


func _draw() -> void:
	var w := size.x
	# Label kiri (letter-spaced, 14px semibold putih).
	var f := UiTheme.font("body_semibold")
	var lab := UiTheme.letter(row_label)
	var bp := UiTheme.baseline_topleft(f, Vector2(0, 18), 14)
	UiTheme.draw_text_shadow(self, f, lab, 14, UiTheme.TEXT_WHITE, bp)
	# Bar dinamis: label 150px, lalu bar, minus/plus 40px, persen 52px.
	var bx := 158.0
	var bw := maxf(50.0, w - bx - 12.0 - 40.0 - 6.0 - 40.0 - 10.0 - 52.0)
	_bar_rect = Rect2(bx, 14, bw, 22)
	var t := clampf(row_value / maxf(0.001, max_value), 0.0, 1.0)
	# Track + isi gradasi.
	UiTheme.draw_vgrad(self, _bar_rect, Color8(26, 30, 52),
		Color8(16, 19, 34), 4.0)
	var fw := bw * t
	if fw > 1.0:
		UiTheme.draw_vgrad(self,
			Rect2(bx + 1, 15, fw - 2, 20), UiTheme.GOLD_BRIGHT,
			Color8(196, 138, 42), 3.0)
	draw_style_box(UiTheme.border_style(UiTheme.EDGE_GOLD, 1.0, 4.0),
		_bar_rect)
	# Knob.
	var kx := bx + fw
	draw_circle(Vector2(kx, 25), 10.0, Color8(12, 14, 24))
	draw_circle(Vector2(kx, 25), 7.0, Color8(245, 248, 255))
	UiTheme.draw_ring(Vector2(kx, 25), 7.0, UiTheme.GOLD, 2.0)
	# Pill minus/plus 40x26 di kanan bar.
	_minus_rect = Rect2(bx + bw + 12, 12, 40, 26)
	_plus_rect = Rect2(bx + bw + 58, 12, 40, 26)
	_draw_mini(_minus_rect, "minus", _minus_hover)
	_draw_mini(_plus_rect, "plus", _plus_hover)
	# Label persen kanan (gold semibold 14px).
	var pct := "%d%%" % int(round(t * 100.0))
	var pf := UiTheme.font("body_semibold")
	var pw := pf.get_string_size(pct, HORIZONTAL_ALIGNMENT_LEFT, -1,
		14).x
	var pp := Vector2(w - 4 - pw, 18)
	UiTheme.draw_text_shadow(self, pf, pct, 14, UiTheme.GOLD_TEXT,
		UiTheme.baseline_topleft(pf, pp, 14))


func _draw_mini(r: Rect2, glyph: String, hov: bool) -> void:
	var cols: Array = UiTheme.pill_colors("neutral")
	if hov:
		UiTheme.draw_glow(self, r.get_center(), r.size + Vector2(20, 16),
			cols[2], 66.0)
	UiTheme.draw_vgrad(self, r,
		Color8(64, 70, 98) if hov else cols[0],
		Color8(38, 43, 66) if hov else cols[1], 6.0)
	draw_style_box(UiTheme.border_style(
		UiTheme.GOLD if hov else cols[2], 1.0, 6.0), r)
	UiTheme.draw_icon(self, glyph, r.get_center(), UiTheme.TEXT_WHITE,
		0.75)
