# VirtualCursor.gd — FASE 24: port ControllerManager.draw_cursor
# (_core.py:9837-9934). Kursor crosshair + kotak sorot UI versi pygame,
# digambar di atas CanvasLayer UI (pygame: di-blit paling akhir oleh
# _render.py:1615 setelah semua lapisan UI).
#
# Geometri/warna port 1:1:
#   pulse      = sin(t * 0.1) * 0.3 + 0.7   (t = nomor frame)
#   hover glow = rect.inflate(20, 20), fill (255,255,100, 80*pulse), radius 12
#   border     = hover_rect, warna (255,255,200), lebar 3, radius 8
#   bracket    = panjang 12, warna (255,255,100), lebar 3, offset ±5 (4 sudut)
#   glow       = lingkaran r12 (surface 30x30), (255,255,100, 60*pulse)
#   crosshair  = 4 garis 5 px (±3..±8), (255,255,200), lebar 2
#   center     = lingkaran r2 putih + r1 (255,200,50)
#
# Deviasi: kotak beradius pygame digambar dengan StyleBoxFlat (Panel anak)
# karena CanvasItem tidak punya draw_rect beradius; sisanya draw API.
# Piksel anti-alias/glow tetap milik bucket piksel (kebijakan repo).
extends Control

const GLOW_COLOR := Color(1.0, 1.0, 100.0 / 255.0)
const CROSS_COLOR := Color(1.0, 1.0, 200.0 / 255.0)
const BRACKET_LEN := 12
const BRACKET_INSET := 5

var manager = null
var hover_rect := Rect2()
var animation_time := 0

var _glow_box: Panel = null
var _border_box: Panel = null


func _ready() -> void:
	name = "VirtualCursor"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	z_index = 100
	_build_boxes()
	visible = false


func _build_boxes() -> void:
	_glow_box = Panel.new()
	_glow_box.name = "HoverGlow"
	_glow_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var glow_sb := StyleBoxFlat.new()
	glow_sb.bg_color = Color(GLOW_COLOR.r, GLOW_COLOR.g, GLOW_COLOR.b, 0.0)
	glow_sb.set_corner_radius_all(12)
	_glow_box.add_theme_stylebox_override("panel", glow_sb)
	add_child(_glow_box)

	_border_box = Panel.new()
	_border_box.name = "HoverBorder"
	_border_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var border_sb := StyleBoxFlat.new()
	border_sb.bg_color = Color(0, 0, 0, 0)
	border_sb.border_color = CROSS_COLOR
	border_sb.set_border_width_all(3)
	border_sb.set_corner_radius_all(8)
	_border_box.add_theme_stylebox_override("panel", border_sb)
	add_child(_border_box)


func _process(_delta: float) -> void:
	if manager == null or not is_instance_valid(manager):
		visible = false
		return
	# Paritas draw_cursor: tanpa cursor_visible / mode controller = tidak
	# digambar sama sekali (return di dua baris pertama fungsi pygame).
	var show_cursor: bool = bool(manager.cursor_visible) \
		and manager.is_controller_mode()
	visible = show_cursor
	if not show_cursor:
		return
	animation_time += 1
	_layout_boxes()
	queue_redraw()


func _pulse() -> float:
	return sin(float(animation_time) * 0.1) * 0.3 + 0.7


func _layout_boxes() -> void:
	if hover_rect.size == Vector2.ZERO:
		_glow_box.visible = false
		_border_box.visible = false
		return
	var pulse := _pulse()
	var glow := Rect2(hover_rect.position - Vector2(10, 10),
		hover_rect.size + Vector2(20, 20))
	_glow_box.visible = true
	_glow_box.position = glow.position
	_glow_box.size = glow.size
	var sb := _glow_box.get_theme_stylebox("panel") as StyleBoxFlat
	if sb != null:
		sb.bg_color = Color(GLOW_COLOR.r, GLOW_COLOR.g, GLOW_COLOR.b,
			80.0 / 255.0 * pulse)
	_border_box.visible = true
	_border_box.position = hover_rect.position
	_border_box.size = hover_rect.size


func _draw() -> void:
	if manager == null or not is_instance_valid(manager):
		return
	var c := Vector2(float(manager.get_cursor_pos().x),
		float(manager.get_cursor_pos().y))
	var pulse := _pulse()

	# Glow kursor (pygame: surface 30x30, lingkaran r12 di (15,15)).
	draw_circle(c, 12.0, Color(GLOW_COLOR.r, GLOW_COLOR.g, GLOW_COLOR.b,
		60.0 / 255.0 * pulse))

	# Crosshair.
	draw_line(c + Vector2(-8, 0), c + Vector2(-3, 0), CROSS_COLOR, 2.0)
	draw_line(c + Vector2(3, 0), c + Vector2(8, 0), CROSS_COLOR, 2.0)
	draw_line(c + Vector2(0, -8), c + Vector2(0, -3), CROSS_COLOR, 2.0)
	draw_line(c + Vector2(0, 3), c + Vector2(0, 8), CROSS_COLOR, 2.0)

	# Center.
	draw_circle(c, 2.0, Color.WHITE)
	draw_circle(c, 1.0, Color(1.0, 200.0 / 255.0, 50.0 / 255.0))

	# Corner brackets (JRPG style) — hanya saat ada rect UI di-hover.
	if hover_rect.size == Vector2.ZERO:
		return
	var l := hover_rect.position.x - BRACKET_INSET
	var t := hover_rect.position.y - BRACKET_INSET
	var r := hover_rect.end.x + BRACKET_INSET
	var b := hover_rect.end.y + BRACKET_INSET
	draw_line(Vector2(l, t), Vector2(l + BRACKET_LEN, t), GLOW_COLOR, 3.0)
	draw_line(Vector2(l, t), Vector2(l, t + BRACKET_LEN), GLOW_COLOR, 3.0)
	draw_line(Vector2(r, t), Vector2(r - BRACKET_LEN, t), GLOW_COLOR, 3.0)
	draw_line(Vector2(r, t), Vector2(r, t + BRACKET_LEN), GLOW_COLOR, 3.0)
	draw_line(Vector2(l, b), Vector2(l + BRACKET_LEN, b), GLOW_COLOR, 3.0)
	draw_line(Vector2(l, b), Vector2(l, b - BRACKET_LEN), GLOW_COLOR, 3.0)
	draw_line(Vector2(r, b), Vector2(r - BRACKET_LEN, b), GLOW_COLOR, 3.0)
	draw_line(Vector2(r, b), Vector2(r, b - BRACKET_LEN), GLOW_COLOR, 3.0)
