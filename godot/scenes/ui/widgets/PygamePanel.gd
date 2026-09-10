# PygamePanel.gd — panel kaca gelap port ui_theme.panel 1:1.
#
# Gradasi vertikal + border + sudut emas + bayangan, digambar di _draw()
# (bukan StyleBoxFlat yang cuma bisa solid).
#
# extends PanelContainer (BUKAN Control): perilaku container satu-anak-penuh
# + margin konten diwarisi native, dan — yang paling penting — test paritas
# menemukan kartu menu lewat find_children("*", "PanelContainer")
# (SaveSlot/LevelSelect/MetaShop ParityTest). Style "panel" native dibuat
# transparan (hanya menyumbang content margin); SEMUA visual digambar di
# _draw() di atasnya.
extends PanelContainer
class_name PygamePanel

var fill_top: Color = UiTheme.PANEL_TOP
var fill_bottom: Color = UiTheme.PANEL_BOTTOM
var border_color: Color = UiTheme.EDGE_GOLD
var border_w: float = 1.0
var corner_radius: float = 12.0
var show_ticks: bool = true
var ticks_color: Color = UiTheme.GOLD
var show_shadow: bool = true
## Kalau true, border diterangkan + glow radial saat mouse di atas kartu
## (paritas hover kartu pygame).
var hoverable: bool = false

var margin_left: float = 14.0
var margin_top: float = 10.0
var margin_right: float = 14.0
var margin_bottom: float = 10.0


func _init(p_border: Color = UiTheme.EDGE_GOLD,
		p_border_w: float = 1.0, p_radius: float = 12.0) -> void:
	border_color = p_border
	border_w = p_border_w
	corner_radius = p_radius
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_refresh_style()
	mouse_entered.connect(_on_hover_changed)
	mouse_exited.connect(_on_hover_changed)


func _on_hover_changed() -> void:
	if hoverable:
		queue_redraw()


func configure(p_fill_top: Color, p_fill_bottom: Color, p_border: Color,
		p_border_w: float = 1.0, p_radius: float = 12.0,
		p_ticks: bool = true, p_shadow: bool = true) -> PygamePanel:
	fill_top = p_fill_top
	fill_bottom = p_fill_bottom
	border_color = p_border
	border_w = p_border_w
	corner_radius = p_radius
	show_ticks = p_ticks
	show_shadow = p_shadow
	queue_redraw()
	return self


func set_margins(l: float, t: float, r: float, b: float) -> PygamePanel:
	margin_left = l
	margin_top = t
	margin_right = r
	margin_bottom = b
	_refresh_style()
	queue_redraw()
	return self


## Style native dibuat transparan total (nol piksel) — hanya content margin
## yang dipakai PanelContainer untuk mengepas anak.
func _refresh_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.border_color = Color(0, 0, 0, 0)
	sb.set_border_width_all(0)
	sb.set_corner_radius_all(0)
	sb.content_margin_left = margin_left
	sb.content_margin_top = margin_top
	sb.content_margin_right = margin_right
	sb.content_margin_bottom = margin_bottom
	sb.shadow_color = Color(0, 0, 0, 0)
	sb.shadow_size = 0
	add_theme_stylebox_override("panel", sb)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	var rect := Rect2(Vector2.ZERO, size)
	var hover := hoverable and is_hovered()
	if hover:
		UiTheme.draw_glow(self, rect.grow(Vector2(13, 13)), border_color,
			60.0 / 255.0)
	if show_shadow:
		UiTheme.draw_shadow(self, rect, corner_radius)
	UiTheme.draw_vgrad(self, rect, fill_top, fill_bottom, corner_radius)
	if border_w > 0.0:
		var bcol := border_color
		if hover:
			bcol = Color(minf(1.0, bcol.r + 90.0 / 255.0),
				minf(1.0, bcol.g + 90.0 / 255.0),
				minf(1.0, bcol.b + 90.0 / 255.0))
		UiTheme.draw_rr_outline(self, rect, bcol, corner_radius, border_w)
	if show_ticks:
		UiTheme.draw_corner_ticks(self, rect, ticks_color)
