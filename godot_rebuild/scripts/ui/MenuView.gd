class_name MenuView
extends Control

signal play_requested(level: int)
signal resume_requested
signal menu_requested
signal quit_requested
signal settings_changed
signal sound_requested(sound_name: String)

var settings := GameSettings.new()
var catalog := LevelCatalog.new()
var selected_level := 1
var pause_mode := false
var page := "main"
var background: ColorRect
var root: VBoxContainer
var heading: Label
var subheading: Label
var confirm_action := ""
var _fps: OptionButton
var _first_button: Button


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	background = ColorRect.new()
	background.color = Color("090914")
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var margin := MarginContainer.new()
	add_child(margin)
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side: String in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 36)
	var layout := HBoxContainer.new()
	layout.add_theme_constant_override("separation", 48)
	margin.add_child(layout)
	var brand := VBoxContainer.new()
	brand.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	brand.alignment = BoxContainer.ALIGNMENT_CENTER
	brand.add_theme_constant_override("separation", 16)
	layout.add_child(brand)
	if ResourceLoader.exists("res://assets/logo.png"):
		var logo := TextureRect.new()
		logo.texture = load("res://assets/logo.png")
		logo.custom_minimum_size = Vector2(260, 250)
		logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
		brand.add_child(logo)
	var title := Ui.label("MYSTIC\nARENA", 57, Ui.TEXT, true)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	brand.add_child(title)
	var tagline := Ui.label("MOBA  /  TOWER DEFENSE", 18, Ui.GOLD)
	tagline.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	brand.add_child(tagline)
	var note := Ui.label(
		"GODOT 4  •  APPLICATION SHELL\n54 level dalam katalog • gameplay belum diport",
		16,
		Ui.MUTED
	)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	brand.add_child(note)
	var panel := Ui.panel()
	panel.custom_minimum_size = Vector2(575, 0)
	layout.add_child(panel)
	root = VBoxContainer.new()
	root.alignment = BoxContainer.ALIGNMENT_CENTER
	root.add_theme_constant_override("separation", 12)
	panel.add_child(root)
	show_main()


func _clear() -> void:
	for child: Node in root.get_children():
		root.remove_child(child)
		child.free()


func _title(title: String, subtitle: String) -> void:
	heading = Ui.label(title, 32, Ui.TEXT, true)
	root.add_child(heading)
	subheading = Ui.label(subtitle, 17, Ui.MUTED)
	subheading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(subheading)


func _button(text: String, action: Callable, primary := false) -> Button:
	var button := Ui.button(text, primary)
	var first_button := root.get_child_count() == 2
	root.add_child(button)
	if first_button:
		_first_button = button
		_focus_first.call_deferred()
	button.pressed.connect(func() -> void: sound_requested.emit("ui_click"))
	button.pressed.connect(action)
	return button


func _focus_first() -> void:
	if (
		is_instance_valid(_first_button)
		and _first_button.is_inside_tree()
		and _first_button.is_visible_in_tree()
	):
		_first_button.grab_focus()


func show_main() -> void:
	background.color = Color("090914")
	page = "main"
	pause_mode = false
	_clear()
	_title("Selamat datang", "Masuki arena. Bangun pertahanan. Pimpin hero Anda.")
	_button("Pilih level", show_levels, true)
	_button("Pengaturan", func() -> void: show_settings(settings))
	_button("Cara bermain", show_help)
	_button("Tentang", show_credits)
	_button("Keluar", func() -> void: confirm("quit"))


func show_levels() -> void:
	page = "levels"
	_clear()
	_title("Pilih arena", "Katalog metadata Python. Kunci progres/save belum dimigrasikan.")
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 330)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(scroll)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 8)
	scroll.add_child(list)
	for entry: Dictionary in catalog.entries:
		var level := int(entry.level_number)
		var button := Ui.button("%02d   %s" % [level, entry.name], level == selected_level)
		button.tooltip_text = str(entry.get("description", ""))
		button.pressed.connect(
			func() -> void:
				sound_requested.emit("ui_click")
				selected_level = level
				play_requested.emit(level)
		)
		list.add_child(button)
	if catalog.entries.is_empty():
		list.add_child(
			Ui.label("Katalog kosong. Jalankan tools/prepare_godot_main.py.", 18, Ui.MUTED)
		)
	_button("Kembali", show_main)


func show_settings(values: GameSettings) -> void:
	settings = values
	page = "settings"
	_clear()
	_title("Pengaturan", "Preferensi Godot terpisah; progres Python tidak ditimpa.")
	for setting: Array in [
		["Master", "master_volume"],
		["Musik", "bgm_volume"],
		["Efek", "sfx_volume"],
		["Ambient", "ambient_volume"]
	]:
		var row := HBoxContainer.new()
		root.add_child(row)
		var label := Ui.label(setting[0], 19)
		label.custom_minimum_size.x = 100
		row.add_child(label)
		var slider := HSlider.new()
		slider.min_value = 0
		slider.max_value = 1
		slider.step = 0.05
		slider.value = values.values[setting[1]]
		slider.custom_minimum_size = Vector2(220, 40)
		slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var key: String = setting[1]
		slider.value_changed.connect(
			func(value: float) -> void:
				values.set_value(key, value)
				settings_changed.emit()
		)
		row.add_child(slider)
	var fps_row := HBoxContainer.new()
	root.add_child(fps_row)
	var fps_label := Ui.label("Batas FPS", 19)
	fps_label.custom_minimum_size.x = 100
	fps_row.add_child(fps_label)
	_fps = OptionButton.new()
	_fps.custom_minimum_size.y = 44
	for option: Array in [[30, "30 FPS"], [60, "60 FPS"], [120, "120 FPS"], [0, "Otomatis"]]:
		_fps.add_item(option[1], option[0])
	_fps.select([30, 60, 120, 0].find(int(values.values.fps_limit)))
	_fps.item_selected.connect(
		func(index: int) -> void:
			values.set_value("fps_limit", _fps.get_item_id(index))
			settings_changed.emit()
	)
	fps_row.add_child(_fps)
	var note := Ui.label(
		(
			"Android dibatasi maksimal 60 FPS; simulasi tetap 60 Hz.\n"
			+ "Tombol FPS tersedia saat MYSTIC_DEBUG=1 atau --debug."
		),
		16,
		Ui.MUTED
	)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(note)
	_button("Kembali", _settings_back)


func _settings_back() -> void:
	if pause_mode:
		show_pause()
	else:
		show_main()


func show_help() -> void:
	page = "help"
	_clear()
	_title("Cara bermain", "Kontrol aplikasi yang tersedia dalam port ini.")
	var text := Ui.label(
		(
			"Sentuh / klik: pilih menu dan berinteraksi dengan arena.\n"
			+ "Esc atau JEDA: pause / lanjut; tombol Android Back setara.\n"
			+ "Tahan JEDA 450 ms: buka/tutup diagnostik.\n"
			+ "Q W E R: skill • H: toko (diteruskan ke adapter gameplay).\n"
			+ "G/F, T, C, B, D: tahan perintah tactical, lepas untuk berhenti.\n"
			+ "F8: FPS • F7/F9/F10/F11: review Sylara/Kaizen/Vex/Grimjaw.\n\n"
			+ "Combat, hero, boss, dan save slot memerlukan adapter native."
		),
		19
	)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(text)
	_button("Kembali", show_main)


func show_credits() -> void:
	page = "credits"
	_clear()
	_title("Mystic Arena", "A MOBA Tower Defense Adventure")
	var text := Ui.label(
		(
			"Proyek asli: dharmawantoxi/mystic-arena.\n"
			+ "Entry point native: Godot 4 / GDScript.\n\n"
			+ "Musik: cynicmusic — Battle Theme A (CC0).\n"
			+ "Ambient: TinyWorlds — Forest Ambience (CC0).\n"
			+ "Efek: Kenney dan sumber CC0 lain; lihat assets/sounds/LISENSI_DAN_SUMBER.txt.\n\n"
			+ "Bagian Python tetap menjadi referensi gameplay."
		),
		19
	)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(text)
	_button("Kembali", show_main)


func show_pause() -> void:
	background.color = Color(0.02, 0.02, 0.05, 0.78)
	page = "pause"
	pause_mode = true
	_clear()
	_title("Jeda", "Pertempuran dibekukan. Tidak ada langkah simulasi saat pause.")
	_button("Lanjutkan", func() -> void: resume_requested.emit(), true)
	_button("Pengaturan", func() -> void: show_settings(settings))
	_button("Menu utama", func() -> void: confirm("menu"))
	_button("Keluar", func() -> void: confirm("quit"))


func confirm(action: String) -> void:
	confirm_action = action
	page = "confirm"
	_clear()
	_title(
		"Yakin ingin keluar?" if action == "quit" else "Kembali ke menu?",
		"Progres pertandingan yang belum disimpan oleh adapter dapat hilang."
	)
	_button(
		"Ya, lanjutkan",
		func() -> void:
			if confirm_action == "quit":
				quit_requested.emit()
			else:
				menu_requested.emit(),
		true
	)
	_button("Batalkan", _cancel)


func _cancel() -> void:
	if pause_mode:
		show_pause()
	else:
		show_main()


func back() -> bool:
	if page == "pause":
		resume_requested.emit()
	elif page == "main":
		confirm("quit")
	elif page != "confirm":
		_cancel()
	else:
		_cancel()
	return true
