# MysticBar.gd — bar progres bergaya forge (port approval-bar pygame:
# track dua-lapis + gradasi emas/oranye + segmen pips).
# kind approve: track (44,30,18)/(26,18,10), edge (196,138,42), teks gold.
# kind forge:   track (24,27,43), edge (150,108,62), header gold ratus.
extends Control
class_name MysticBar

@export var fill_ratio: float = 0.0:
	set(v):
		fill_ratio = clampf(v, 0.0, 1.0)
		queue_redraw()
@export var bar_kind: String = "approve":
	set(v):
		bar_kind = v
		queue_redraw()
@export var pips: int = 0:
	set(v):
		pips = v
		queue_redraw()
@export var show_text: bool = true:
	set(v):
		show_text = v
		queue_redraw()
@export var bar_text: String = "":
	set(v):
		bar_text = v
		queue_redraw()
@export var fill_top: Color = UiTheme.GOLD_BRIGHT:
	set(v):
		fill_top = v
		queue_redraw()
@export var fill_bottom: Color = UiTheme.ORANGE:
	set(v):
		fill_bottom = v
		queue_redraw()
@export var track_top: Color = Color8(44, 30, 18):
	set(v):
		track_top = v
		queue_redraw()
@export var track_bottom: Color = Color8(26, 18, 10):
	set(v):
		track_bottom = v
		queue_redraw()
@export var edge_color: Color = Color8(196, 138, 42):
	set(v):
		edge_color = v
		queue_redraw()


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(queue_redraw)


func set_fill(current: float, maximum: float) -> void:
	fill_ratio = clampf(current / maxf(1.0, maximum), 0.0, 1.0)


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	# Track: bayangan 2px + gradasi + border.
	draw_rect(Rect2(rect.position.x + 2, rect.position.y + 2, rect.size.x,
		rect.size.y), Color(0, 0, 0, 0.4))
	UiTheme.draw_vgrad(self, rect, track_top, track_bottom, 5.0)
	draw_style_box(UiTheme.border_style(edge_color, 1.0, 5.0), rect)
	# Isi.
	var fw := rect.size.x * fill_ratio
	if fw > 1.0:
		UiTheme.draw_vgrad(self,
			Rect2(rect.position + Vector2(1, 1), Vector2(fw - 2,
				rect.size.y - 2)), fill_top, fill_bottom, 4.0)
	# Pips segmen.
	if pips > 1:
		for i in range(1, pips):
			var x := rect.position.x + rect.size.x * float(i) / float(pips)
			draw_line(Vector2(x, rect.position.y + 1),
				Vector2(x, rect.end.y - 1), Color(0, 0, 0, 0.5), 2.0)
	# Teks tengah dengan bayangan.
	if show_text and bar_text != "":
		var f := UiTheme.font("body_bold")
		var bp := UiTheme.baseline_center(f, bar_text, rect.get_center(),
			13)
		UiTheme.draw_text_shadow(self, f, bar_text, 13, UiTheme.GOLD_TEXT,
			bp)
