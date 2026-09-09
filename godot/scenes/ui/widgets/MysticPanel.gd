# MysticPanel.gd — panel kaca gelap (port ui_theme.panel).
#
# Gradasi vertikal + border + sorot tepi atas + sudut emas + bayangan,
# digambar di _draw() sehingga selalu DI BELAKANG anak konten (dipakai
# sebagai PanelContainer biasa: tambah Margin/VBox/HBox di dalamnya).
extends PanelContainer
class_name MysticPanel

@export var fill_top: Color = UiTheme.PANEL_TOP
@export var fill_bottom: Color = UiTheme.PANEL_BOTTOM
@export var border_color: Color = UiTheme.EDGE_GOLD
@export var border_width: float = 1.0
@export var radius: float = 12.0
@export var show_ticks: bool = true
@export var tick_color: Color = UiTheme.GOLD
@export var tick_length: float = 11.0
@export var show_shadow: bool = true
@export var shadow_alpha: float = 0.45
@export var show_highlight: bool = false


func _init(p_top: Color = UiTheme.PANEL_TOP,
		p_bottom: Color = UiTheme.PANEL_BOTTOM,
		p_border: Color = UiTheme.EDGE_GOLD, p_radius: float = 12.0,
		p_border_w: float = 1.0, p_ticks: bool = true) -> void:
	fill_top = p_top
	fill_bottom = p_bottom
	border_color = p_border
	radius = p_radius
	border_width = p_border_w
	show_ticks = p_ticks
	var empty := StyleBoxEmpty.new()
	add_theme_stylebox_override("panel", empty)
	resized.connect(queue_redraw)


func set_fills(top: Color, bottom: Color) -> void:
	fill_top = top
	fill_bottom = bottom
	queue_redraw()


func set_border(c: Color, w: float = -1.0) -> void:
	border_color = c
	if w >= 0.0:
		border_width = w
	queue_redraw()


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	if show_shadow:
		draw_style_box(UiTheme.shadow_style(radius, shadow_alpha), rect)
	UiTheme.draw_vgrad(self, rect, fill_top, fill_bottom, radius)
	if border_width > 0.0:
		draw_style_box(UiTheme.border_style(border_color, border_width,
			radius), rect)
	if show_highlight:
		draw_line(Vector2(rect.position.x + 12, rect.position.y + 1),
			Vector2(rect.end.x - 12, rect.position.y + 1),
			Color(1, 1, 1, 0.28), 1.0)
	if show_ticks:
		UiTheme.corner_ticks(self, rect, tick_color, tick_length, 2.0, 2.0)
