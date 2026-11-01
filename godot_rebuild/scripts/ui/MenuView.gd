class_name MenuView
extends Control

signal play_requested(level: int, replay: bool)
signal resume_requested
signal menu_requested
signal quit_requested
signal settings_changed
signal sound_requested(sound_name: String)

var settings := GameSettings.new()
var catalog := LevelCatalog.new()
var core_data := CoreData.new()
var save_repo := SaveRepository.new()
var cloud_port: CloudSavePort
var topup_port: TopupPort
var voucher := VoucherService.new()
var selected_level := 1
var pause_mode := false
var page := "main"
var background: ColorRect
var root: VBoxContainer
var heading: Label
var subheading: Label
var confirm_action := ""
var service_message := ""
var _fps: OptionButton
var _first_button: Button
var _voucher_input: LineEdit
var _status_label: Label


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
		"GODOT 4  •  NATIVE CORE\n54 level • 3 save slot • layanan eksplisit", 16, Ui.MUTED
	)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	brand.add_child(note)
	var panel := Ui.panel()
	panel.custom_minimum_size = Vector2(575, 0)
	layout.add_child(panel)
	root = VBoxContainer.new()
	root.alignment = BoxContainer.ALIGNMENT_CENTER
	root.add_theme_constant_override("separation", 10)
	panel.add_child(root)
	show_main()


func _clear() -> void:
	for child: Node in root.get_children():
		root.remove_child(child)
		child.free()
	_status_label = null
	_voucher_input = null


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


func _scroll_list(height := 330) -> VBoxContainer:
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, height)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(scroll)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 8)
	scroll.add_child(list)
	return list


func _message(text: String) -> void:
	service_message = text
	if _status_label != null:
		_status_label.text = text


func show_main() -> void:
	background.color = Color("090914")
	page = "main"
	pause_mode = false
	_clear()
	var save_data := save_repo.load_slot()
	var gold := int(save_data.get("meta_gold", 0))
	_title(
		"Selamat datang",
		"Slot %d • Hero Gold %d • %s" % [save_repo.current_slot, gold, settings.difficulty_label()]
	)
	_button("Pilih level", show_levels, true)
	_button("Save slot", show_slots)
	_button("Hero shop", show_heroes)
	_button("Top up / voucher", show_topup)
	_button("Cloud save", show_cloud)
	_button("Pengaturan", func() -> void: show_settings(settings))
	_button("Cara bermain", show_help)
	_button("Tentang", show_credits)
	_button("Keluar", func() -> void: confirm("quit"))


func show_slots() -> void:
	page = "slots"
	_clear()
	_title("Save slot", "Tiga slot lokal native. Progres Python tidak ditimpa.")
	for slot in range(1, SaveRepository.NUM_SLOTS + 1):
		var info := save_repo.slot_info(slot)
		var label := "Slot %d — kosong" % slot
		if not info.is_empty():
			label = (
				"Slot %d — Level %d • %d gold"
				% [slot, int(info.highest_level), int(info.meta_gold)]
			)
		if slot == save_repo.current_slot:
			label += " (aktif)"
		var row := HBoxContainer.new()
		root.add_child(row)
		var select := Ui.button(label, slot == save_repo.current_slot)
		select.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var slot_num := slot
		select.pressed.connect(
			func() -> void:
				save_repo.set_current_slot(slot_num)
				sound_requested.emit("ui_click")
				show_slots()
		)
		row.add_child(select)
		if not info.is_empty():
			var del := Ui.button("Hapus")
			del.pressed.connect(func() -> void: confirm("delete_slot:%d" % slot_num))
			row.add_child(del)
	_button("Kembali", show_main)


func show_levels() -> void:
	page = "levels"
	_clear()
	var save_data := save_repo.load_slot()
	var completed: Array = save_data.get("completed_levels", [])
	var locked_diff: Variant = save_data.get("run_difficulty", null)
	var diff_text := settings.difficulty_label()
	if locked_diff != null and completed.size() < catalog.entries.size():
		diff_text = str(locked_diff).to_upper() + " LOCKED"
	_title(
		"Pilih arena",
		"Mode: %s • Selesai %d/%d" % [diff_text, completed.size(), catalog.entries.size()]
	)
	var diff_button := Ui.button("Mode: " + diff_text)
	diff_button.disabled = locked_diff != null and completed.size() < catalog.entries.size()
	diff_button.pressed.connect(
		func() -> void:
			settings.cycle_difficulty()
			settings_changed.emit()
			show_levels()
	)
	root.add_child(diff_button)
	var list := _scroll_list()
	for entry: Dictionary in catalog.entries:
		var level := int(entry.level_number)
		var unlocked := SaveRepository.is_level_unlocked(entry, completed)
		var done := level in completed
		var label := "%02d   %s" % [level, entry.name]
		if done:
			label += "  ✓"
		elif not unlocked:
			label += "  🔒"
		var button := Ui.button(label, level == selected_level)
		button.disabled = not unlocked
		button.tooltip_text = str(entry.get("description", ""))
		button.pressed.connect(
			func() -> void:
				sound_requested.emit("ui_click")
				selected_level = level
				play_requested.emit(level, done)
		)
		list.add_child(button)
	_button("Kembali", show_main)


func show_heroes() -> void:
	page = "heroes"
	_clear()
	var save_data := save_repo.load_slot()
	var purchased: Array = save_data.get("purchased_heroes", [])
	_title(
		"Hero shop",
		(
			"Hero Gold: %d • Boss yang dikalahkan terbuka gratis saat menang."
			% int(save_data.get("meta_gold", 0))
		)
	)
	var list := _scroll_list()
	var heroes: Dictionary = core_data.data.get("heroes", {})
	for hero_type: String in heroes:
		var stats: Dictionary = heroes[hero_type]
		var owned := hero_type in purchased
		var cost := int(stats.get("unlock_cost", stats.get("cost", 0)))
		var arch := core_data.archetypes
		var label := (
			"%s — %s\n%s · %s"
			% [
				stats.get("name", hero_type),
				"OWNED" if owned else "%d G" % cost,
				arch.short_label(hero_type, stats),
				arch.detail_label(hero_type, stats),
			]
		)
		var button := Ui.button(label, owned)
		button.custom_minimum_size = Vector2(0, 72)
		button.add_theme_font_size_override("font_size", 17)
		button.tooltip_text = (
			(
				"%s\nTier/Power adalah snapshot analisis sumber, bukan DPS runtime.\n"
				% arch.detail_label(hero_type, stats)
			)
			+ "PHY ditahan armor boss; MAG ditahan magic resistance."
		)
		button.disabled = owned
		var ht := hero_type
		var c := cost
		button.pressed.connect(
			func() -> void:
				var data := save_repo.load_slot()
				if SaveRepository.purchase_hero(data, ht, c) and save_repo.save_slot(data):
					_message("Hero terbuka: %s" % ht)
					show_heroes()
				else:
					_message("Gold tidak cukup atau hero sudah dimiliki.")
					show_heroes()
		)
		list.add_child(button)
	_status_label = Ui.label(service_message, 16, Ui.GOLD)
	root.add_child(_status_label)
	_button("Kembali", show_main)


func show_settings(values: GameSettings) -> void:
	settings = values
	page = "settings"
	_clear()
	_title("Pengaturan", "Preferensi native terpisah; progres Python tidak ditimpa.")
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 360)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(scroll)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 8)
	scroll.add_child(box)
	for setting: Array in [
		["Master", "master_volume"],
		["Musik", "bgm_volume"],
		["Efek", "sfx_volume"],
		["Ambient", "ambient_volume"],
		["Voice", "voice_volume"],
	]:
		var row := HBoxContainer.new()
		box.add_child(row)
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
	_option_row(
		box,
		"Difficulty",
		["easy", "normal", "hard"],
		str(values.values.difficulty),
		func(value: String) -> void:
			values.set_value("difficulty", value)
			settings_changed.emit()
	)
	_option_row(
		box,
		"Speed",
		["0.5", "1.0", "1.5", "2.0"],
		"%.1f" % float(values.values.game_speed),
		func(value: String) -> void:
			values.set_value("game_speed", float(value))
			settings_changed.emit()
	)
	_option_row(
		box,
		"Language",
		["id", "en"],
		str(values.values.language),
		func(value: String) -> void:
			values.set_value("language", value)
			settings_changed.emit()
	)
	_option_row(
		box,
		"Input",
		["keyboard", "controller"],
		str(values.values.input_mode),
		func(value: String) -> void:
			values.set_value("input_mode", value)
			settings_changed.emit()
	)
	_check_row(
		box,
		"Screen shake",
		bool(values.values.screen_shake_enabled),
		func(value: bool) -> void:
			values.set_value("screen_shake_enabled", value)
			settings_changed.emit()
	)
	_check_row(
		box,
		"Damage numbers",
		bool(values.values.damage_numbers_enabled),
		func(value: bool) -> void:
			values.set_value("damage_numbers_enabled", value)
			settings_changed.emit()
	)
	var fps_row := HBoxContainer.new()
	box.add_child(fps_row)
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
	_button("Kembali", _settings_back)


func _option_row(
	parent: Node, label_text: String, options: Array, current: String, callback: Callable
) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var label := Ui.label(label_text, 19)
	label.custom_minimum_size.x = 100
	row.add_child(label)
	var option := OptionButton.new()
	option.custom_minimum_size = Vector2(220, 44)
	for value: String in options:
		option.add_item(value)
	option.select(maxi(0, options.find(current)))
	option.item_selected.connect(func(index: int) -> void: callback.call(options[index]))
	row.add_child(option)


func _check_row(parent: Node, label_text: String, current: bool, callback: Callable) -> void:
	var check := CheckBox.new()
	check.text = label_text
	check.button_pressed = current
	check.add_theme_font_size_override("font_size", 19)
	check.toggled.connect(func(value: bool) -> void: callback.call(value))
	parent.add_child(check)


func _settings_back() -> void:
	if pause_mode:
		show_pause()
	else:
		show_main()


func show_topup() -> void:
	page = "topup"
	_clear()
	var rules: Dictionary = core_data.data.get("rules", {})
	var packages: Array = rules.get("TOPUP_PACKAGES", [])
	var methods: Array = rules.get("TOPUP_PAYMENT_METHODS", [])
	var available := topup_port != null and topup_port.available()
	_title(
		"Top up / voucher",
		"Server: %s" % ("tersedia" if available else "belum dikonfigurasi (MYSTIC_TOPUP_URL)")
	)
	var list := _scroll_list(220)
	for pack: Dictionary in packages:
		var label := (
			"%s — %d gold — Rp %d"
			% [pack.get("label", "Paket"), int(pack.get("gold", 0)), int(pack.get("price", 0))]
		)
		var button := Ui.button(label)
		button.disabled = not available
		var index := packages.find(pack)
		button.pressed.connect(
			func() -> void:
				if topup_port != null:
					var method := str(methods[0].get("id", "")) if not methods.is_empty() else ""
					var result := topup_port.create(index, method, rules)
					_message(str(result.get("message", result.get("code", "pending"))))
					show_topup()
		)
		list.add_child(button)
	var method_text := (
		"Metode: "
		+ ", ".join(
			methods.map(func(m: Dictionary) -> String: return str(m.get("label", m.get("id", ""))))
		)
	)
	root.add_child(Ui.label(method_text, 16, Ui.MUTED))
	_voucher_input = LineEdit.new()
	_voucher_input.placeholder_text = "MA-123456"
	_voucher_input.custom_minimum_size.y = 48
	root.add_child(_voucher_input)
	_button(
		"Redeem voucher",
		func() -> void:
			var code := _voucher_input.text if _voucher_input != null else ""
			var result := voucher.redeem(save_repo, code, Time.get_ticks_msec())
			_message(
				"Voucher: %s (+%d gold)" % [result.get("reason", "?"), int(result.get("gold", 0))]
			)
			show_topup(),
		true
	)
	_status_label = Ui.label(service_message, 16, Ui.GOLD)
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_status_label)
	_button("Kembali", show_main)


func show_cloud() -> void:
	page = "cloud"
	_clear()
	var status := (
		cloud_port.status
		if cloud_port != null
		else {"available": false, "message": "Play Games plugin not configured"}
	)
	_title("Cloud save", str(status.get("message", "Tidak tersedia")))
	_button(
		"Sign in Play Games",
		func() -> void:
			if cloud_port != null:
				var result := cloud_port.sign_in()
				_message(str(result.get("message", result.get("code", "unavailable"))))
				show_cloud()
	)
	_button(
		"Upload ke cloud",
		func() -> void:
			if cloud_port != null:
				var payload := CloudSaveCodec.build_payload(
					save_repo, settings.values, Time.get_unix_time_from_system()
				)
				var result := cloud_port.upload(payload)
				_message(str(result.get("message", result.get("code", "unavailable"))))
				show_cloud()
	)
	_button(
		"Download dari cloud",
		func() -> void:
			if cloud_port != null:
				var result := cloud_port.download()
				if bool(result.get("ok", false)) and result.get("payload") is Dictionary:
					var parsed := CloudSaveCodec.parse_payload(JSON.stringify(result.payload))
					if (
						bool(parsed.get("ok", false))
						and CloudSaveCodec.apply_payload(save_repo, parsed.payload, settings)
					):
						_message("Restore cloud selesai.")
					else:
						_message(str(parsed.get("error", "Restore gagal.")))
				else:
					_message(str(result.get("message", result.get("code", "unavailable"))))
				show_cloud()
	)
	_button(
		"Export backup lokal",
		func() -> void:
			var payload := CloudSaveCodec.build_payload(
				save_repo, settings.values, Time.get_unix_time_from_system()
			)
			if payload.is_empty():
				_message("Tidak ada slot untuk diexport.")
			else:
				var file := FileAccess.open("user://godot_core/cloud_backup.json", FileAccess.WRITE)
				if file != null:
					file.store_string(JSON.stringify(payload, "\t"))
					_message("Backup lokal: user://godot_core/cloud_backup.json")
				else:
					_message("Gagal menulis backup.")
			show_cloud()
	)
	_button(
		"Import backup lokal",
		func() -> void:
			var path := "user://godot_core/cloud_backup.json"
			if not FileAccess.file_exists(path):
				_message("Backup lokal tidak ditemukan.")
			else:
				var file := FileAccess.open(path, FileAccess.READ)
				var parsed := CloudSaveCodec.parse_payload(file.get_as_text())
				if (
					bool(parsed.get("ok", false))
					and CloudSaveCodec.apply_payload(save_repo, parsed.payload, settings)
				):
					_message("Import backup selesai.")
				else:
					_message(str(parsed.get("error", "Import gagal.")))
			show_cloud()
	)
	_status_label = Ui.label(service_message, 16, Ui.GOLD)
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_status_label)
	_button("Kembali", show_main)


func show_help() -> void:
	page = "help"
	_clear()
	_title("Cara bermain", "Kontrol native core.")
	var text := Ui.label(
		(
			"Sentuh / klik: pilih menu, hero, tower, slot build, atau tujuan gerak.\n"
			+ "Tahan slot kosong: buka popup build. Klik tower: upgrade/sell/shield.\n"
			+ "Esc: pause / tutup popup. H: hero shop. I: item forge. U: upgrade. X: sell.\n"
			+ "Q W E R: skill hero terpilih.\n"
			+ "G/F, T, C, B, D: tahan perintah tactical; lepas untuk berhenti.\n"
			+ "F1 dev mode, F2 panel, F3 debug (debug build / MYSTIC_DEV=1).\n"
			+ "Controller: stick kiri cursor, A confirm, B back, X/Y/LB/RB skill, Start pause.\n\n"
			+ "Layanan Play Games/top-up nyata memerlukan plugin/server; status tidak dipalsukan."
		),
		18
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
			+ "Entry point + core native: Godot 4 / GDScript.\n\n"
			+ "Musik: cynicmusic — Battle Theme A (CC0).\n"
			+ "Ambient: TinyWorlds — Forest Ambience (CC0).\n"
			+ "Efek: Kenney dan sumber CC0 lain; lihat assets/sounds/LISENSI_DAN_SUMBER.txt.\n\n"
			+ "Python tetap menjadi referensi parity; skill/rig bespoke dilacak di docs."
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
	var title := "Yakin ingin keluar?"
	var subtitle := "Progres pertandingan yang belum disimpan dapat hilang."
	if action == "menu":
		title = "Kembali ke menu?"
	elif action.begins_with("delete_slot:"):
		title = "Hapus save slot?"
		subtitle = "Slot lokal akan dihapus. Cloud tidak otomatis dihapus."
	_title(title, subtitle)
	_button(
		"Ya, lanjutkan",
		func() -> void:
			if confirm_action == "quit":
				quit_requested.emit()
			elif confirm_action == "menu":
				menu_requested.emit()
			elif confirm_action.begins_with("delete_slot:"):
				var slot := int(confirm_action.get_slice(":", 1))
				save_repo.delete_slot(slot)
				show_slots(),
		true
	)
	_button("Batalkan", _cancel)


func _cancel() -> void:
	if confirm_action.begins_with("delete_slot:"):
		show_slots()
	elif pause_mode:
		show_pause()
	else:
		show_main()


func back() -> bool:
	if page == "pause":
		resume_requested.emit()
	elif page == "main":
		confirm("quit")
	elif page == "confirm":
		_cancel()
	elif page in ["settings", "topup", "cloud", "heroes", "slots"]:
		if pause_mode and page == "settings":
			show_pause()
		else:
			show_main()
	else:
		_cancel()
	return true


func controller_action(action: String) -> void:
	if action == "confirm":
		var focus := get_viewport().gui_get_focus_owner()
		if focus is Button and focus.is_visible_in_tree():
			focus.pressed.emit()
	elif action == "cancel" or action == "back":
		back()
	elif action.begins_with("dpad_"):
		var buttons := root.find_children("*", "Button", true, false)
		var visible: Array[Button] = []
		for button: Button in buttons:
			if button.is_visible_in_tree() and not button.disabled:
				visible.append(button)
		if visible.is_empty():
			return
		var focus := get_viewport().gui_get_focus_owner()
		var index := visible.find(focus)
		var step := -1 if action in ["dpad_0_-1", "dpad_-1_0"] else 1
		index = (index + step) % visible.size()
		if index < 0:
			index += visible.size()
		visible[index].grab_focus()
