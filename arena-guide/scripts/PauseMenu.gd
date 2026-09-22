extends CanvasLayer
class_name PauseMenu
## Langkah 11-12: overlay pause - LANJUTKAN / MENU UTAMA.

var _main = null


func setup(main_ref) -> void:
	_main = main_ref
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 10
	hide()
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var title := Label.new()
	title.text = "PAUSE"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.position = Vector2(0, 210)
	title.size = Vector2(1280, 80)
	title.add_theme_font_size_override("font_size", 64)
	title.add_theme_color_override("font_color", Color("#C9A227"))
	add_child(title)
	var b1 := _make_btn("LANJUTKAN", 320.0)
	b1.pressed.connect(_on_resume)
	var b2 := _make_btn("MENU UTAMA", 384.0)
	b2.pressed.connect(_on_menu)


func _make_btn(text: String, y: float) -> Button:
	var b := Button.new()
	b.text = text
	b.position = Vector2(540, y)
	b.size = Vector2(200, 52)
	b.add_theme_font_size_override("font_size", 22)
	add_child(b)
	return b


func _on_resume() -> void:
	Sound.play("click")
	if _main != null and is_instance_valid(_main):
		_main.toggle_pause()


func _on_menu() -> void:
	Sound.play("click")
	App.to_menu()
