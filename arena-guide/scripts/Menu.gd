extends Control
## Langkah 11-12: menu utama - MAIN / LEVEL / HELP + kunci + bunyi.

const LevelDB = preload("res://scripts/LevelDB.gd")

var _box: VBoxContainer
var _info_l: Label


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color("#0B0A12")
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var title := Label.new()
	title.text = "MYSTIC ARENA"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.position = Vector2(0, 110)
	title.size = Vector2(1280, 100)
	title.add_theme_font_size_override("font_size", 72)
	title.add_theme_color_override("font_color", Color("#C9A227"))
	add_child(title)
	_info_l = Label.new()
	_info_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_info_l.position = Vector2(240, 225)
	_info_l.size = Vector2(800, 70)
	_info_l.add_theme_font_size_override("font_size", 20)
	_info_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(_info_l)
	_box = VBoxContainer.new()
	_box.position = Vector2(480, 310)
	_box.size = Vector2(320, 330)
	_box.add_theme_constant_override("separation", 12)
	add_child(_box)
	_show_main()


func _clear_box() -> void:
	for c in _box.get_children():
		c.queue_free()


func _make_btn(text: String) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(320, 54)
	b.add_theme_font_size_override("font_size", 24)
	_box.add_child(b)
	return b


func _go_main() -> void:
	Sound.play("click")
	_show_main()


func _go_level() -> void:
	Sound.play("click")
	_show_level()


func _go_help() -> void:
	Sound.play("click")
	_show_help()


func _pick_level(i: int) -> void:
	Sound.play("click")
	App.start_level(i)


func _show_main() -> void:
	_clear_box()
	_info_l.text = "Godot 4.7.1  •  Renderer Mobile"
	var b1 := _make_btn("MULAI GAME")
	b1.pressed.connect(_go_level)
	var b2 := _make_btn("BANTUAN")
	b2.pressed.connect(_go_help)
	var b3 := _make_btn("KELUAR")
	b3.pressed.connect(func(): get_tree().quit())


func _show_level() -> void:
	_clear_box()
	_info_l.text = "Pilih level:"
	for i in App.levels.size():
		var nm: String = "Level %d" % (i + 1)
		var d: Dictionary = LevelDB.load_level(str(App.levels[i]))
		if not d.is_empty():
			nm = "%d. %s" % [i + 1, str(d.get("name", nm))]
		var b := _make_btn(nm)
		if i + 1 > App.unlocked:
			b.text = "%d. ??? (kunci)" % (i + 1)
			b.disabled = true
		else:
			b.pressed.connect(_pick_level.bind(i))
	var back := _make_btn("KEMBALI")
	back.pressed.connect(_go_main)


func _show_help() -> void:
	_clear_box()
	_info_l.text = "Klik hero = pilih, klik map = jalan, klik slot biru = bangun (100g). Q/W/E/R = skill. ESC = pause. Hancurkan nexus merah!"
	var back := _make_btn("KEMBALI")
	back.pressed.connect(_go_main)
