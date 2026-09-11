# PygameSlider.gd — slider volume emas (port ui_theme.slider 1:1).
#
# Track 8px (34,38,58) radius 4 + isi gradasi GOLD_BRIGHT->(196,138,40) +
# border (120,110,86) + knob cincin (bayangan r11, putih r8, cincin emas 2px)
# dan glow radial 36px saat knob disorot.
#
# extends HSlider: perilaku native (drag, klik track, panah keyboard, sinyal
# `value_changed`) dipertahankan; SEMUA visual native dikosongkan dan
# digambar ulang di _draw() lewat UiTheme.draw_slider — jadi angka geometrinya
# satu sumber dengan jalur immediate-mode pygame.
extends HSlider
class_name PygameSlider

## Tinggi track pygame (konstanta `track_h = 8` di ui_theme.slider).
const TRACK_H := 8.0

var _mouse_inside: bool = false

static var _blank_grabber: Texture2D = null


func _init(p_value: float = 0.6) -> void:
	min_value = 0.0
	max_value = 1.0
	step = 0.05
	value = clampf(p_value, 0.0, 1.0)
	custom_minimum_size = Vector2(0, 24)
	focus_mode = Control.FOCUS_ALL
	_clear_native_visuals()
	mouse_entered.connect(_set_inside.bind(true))
	mouse_exited.connect(_set_inside.bind(false))
	value_changed.connect(func(_v: float) -> void: queue_redraw())


## Style + ikon grabber native dikosongkan (grabber transparan 1px, bukan
## `null` — override null berarti jatuh ke tema default yang terlihat).
func _clear_native_visuals() -> void:
	var empty := StyleBoxEmpty.new()
	for style_name in ["slider", "grabber_area", "grabber_area_highlight"]:
		add_theme_stylebox_override(style_name, empty)
	if _blank_grabber == null:
		var img := Image.create(1, 1, false, Image.FORMAT_RGBA8)
		img.fill(Color(0, 0, 0, 0))
		_blank_grabber = ImageTexture.create_from_image(img)
	add_theme_icon_override("grabber", _blank_grabber)
	add_theme_icon_override("grabber_highlight", _blank_grabber)
	add_theme_icon_override("tick", _blank_grabber)


func _set_inside(v: bool) -> void:
	_mouse_inside = v
	queue_redraw()


## Ratio 0..1 dari nilai slider (pygame `slider(..., value)` menerima 0..1).
func ratio() -> float:
	var span := max_value - min_value
	if span <= 0.0:
		return 0.0
	return clampf((value - min_value) / span, 0.0, 1.0)


## Rect track di koordinat Control (track dipusatkan vertikal).
func track_rect() -> Rect2:
	return Rect2(0, floorf((size.y - TRACK_H) * 0.5), size.x, TRACK_H)


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _draw() -> void:
	if size.x <= 0.0:
		return
	var tr := track_rect()
	var g := UiTheme.slider_geom(tr.position, tr.size.x, ratio())
	var knob: Vector2 = g["knob"]
	var hover := _mouse_inside
	if hover:
		# pygame: `knob_hover` disorot saat kursor di atas knob (Menu
		# menghitung jarak ke knob sebelum menggambar).
		hover = (get_local_mouse_position() - knob).length() <= 14.0
	UiTheme.draw_slider(self, tr.position, tr.size.x, ratio(), hover)
