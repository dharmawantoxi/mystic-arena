# MainMenu.gd — Menu utama + sub-menu, dibangun 100% dari kode.
#
# Port state machine `class MenuState` pygame (_core.py:3097-3105):
#   MAIN · SLOT_SELECT · LEVEL_SELECT · HERO_SHOP · SETTINGS ·
#   HOW_TO_PLAY · CREDITS · PAUSE
# pygame menggambar semuanya manual per frame di Menu.draw(); di Godot cukup
# bangun ulang isi container tiap pindah state.
#
# Tampilan = 1:1 ui_theme pygame (MysticMenuBg, MysticPanel, MysticButton,
# MysticPill, MysticTab, MysticTitle, MysticChip — lihat scenes/ui/widgets/).
# String = verbatim pygame (mayoritas Inggris; segelintir yang aslinya
# Indonesia di pygame — legenda PHY/MAG/TNK, label cloud — ikut apa adanya).
#
# Sinyal keluar (dipasang Main.gd):
#   play_requested(level_num) — LEVEL_SELECT/CONTINUE -> mulai match
#   resume_requested          — PAUSE -> lanjut main
#   main_menu_requested       — PAUSE/victory -> buang match, balik MAIN
# Difficulty diubah langsung lewat GameManager.set_difficulty() (paritas
# toggle_level_difficulty), pembelian hero lewat SaveManager (paritas
# _unlock_hero_in_meta_shop _core.py:5298-5328).
extends Control

const BakedUnitDBScript = preload("res://scripts/render/BakedUnitDB.gd")

signal play_requested(level_num: int)
signal resume_requested
signal main_menu_requested
## Dipancarkan tiap kali menu dibuka/ditutup/diganti state — Main.gd
## menyembunyikan arena+HUD selama menu non-PAUSE menutupi layar penuh
## (layar berantakan "menu di samping arena" tidak boleh bisa terjadi),
## dan menampilkan arena beku di belakang dim selama PAUSE (paritas
## pygame: pause = frame game beku + overlay gelap + panel).
signal menu_coverage_changed(covers: bool, is_pause: bool)

## Paritas MenuState _core.py:3099-3105 — SEMUA state termasuk SLOT_SELECT
## (FASE 21: multi-slot save + migrasi legacy sudah diport).
enum State { MAIN, SLOT_SELECT, LEVEL_SELECT, HERO_SHOP, SETTINGS, HOW_TO_PLAY, CREDITS, PAUSE }

## PAUSE = dim gelap semi-transparan di atas arena BEKU (paritas pygame
## pause menu yang menggambar frame game terakhir + overlay gelap).
const COL_BG_PAUSE := Color(0.031, 0.033, 0.058, 0.62)
const COL_PANEL := Color(0.045, 0.05, 0.085, 0.97)
const COL_BORDER := Color(1.0, 0.804, 0.333, 0.9)
const COL_TEXT := Color(0.86, 0.9, 1.0)
const COL_DIM := Color(0.66, 0.71, 0.84, 0.9)
const COL_GOLD := Color(1.0, 0.87, 0.38)
const COL_BLUE := Color(0.4, 0.72, 1.0)
const COL_GREEN := Color(0.42, 0.9, 0.55)
const COL_RED := Color(1.0, 0.42, 0.42)
const COL_LOCKED := Color(0.42, 0.45, 0.56)

## 3 kartu per baris — paritas layout LEVEL_SELECT pygame (max 4 kolom,
## 3 kalau lebih dari 4 level; kita punya 54).
const LEVEL_COLUMNS := 3

## Geometri kartu SLOT_SELECT — paritas _draw_slot_select _core.py:3237-3244
## (3 kartu x 320px, gap 30). Konstanta pygame di-pin apa adanya walau
## lebar layar Godot berbeda; nilai DATA kartu yang dikunci oracle.
const SLOT_CARD_W := 320.0
const SLOT_CARD_H := 460.0
const SLOT_CARD_GAP := 30

## Ambang truncasi string stat kartu level — paritas pygame `w // 2 - 20`
## pada kartu 280px (_core.py:4260/4268: val_font.size > 120 → potong 8
## karakter). Konstanta pygame di-pin apa adanya supaya keluaran STRING
## sama, walau lebar kartu Godot (380) berbeda; metrik font tetap milik
## Godot (batas tepatnya bergantung raster — terdokumentasi terbuka).
const LEVEL_STAT_WIDTH_LIMIT := 120.0

## Warna slot stat kartu level — data ui_theme pygame yang sama
## (GOLD_TEXT / CYAN_SOFT / TEXT_BODY / TEXT_FAINT + 3 band win-rate).
const COL_STAT_LABEL := Color8(96, 106, 136)
const COL_STAT_SCORE := Color8(255, 220, 110)
const COL_STAT_TIME := Color8(165, 220, 255)
const COL_STAT_ATTEMPTS := Color8(198, 207, 230)
const COL_WR_LOW := Color8(255, 150, 100)
const COL_WR_GOLD := Color8(255, 220, 110)
const COL_WR_GREEN := Color8(112, 226, 132)

## Opsi settings (paritas GameSettings._system pygame).
const FPS_OPTIONS := [30, 60, 120, 0]
const SPEED_OPTIONS := [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

## Cache potret hero shop (hero_type -> AtlasTexture frame idle pertama).
static var _portrait_cache: Dictionary = {}

var state: int = State.MAIN
## True kalau menu dibuka dari dalam match (PAUSE) — MAIN-nya jadi "MAIN MENU"
## yang kembali ke permainan, bukan menutup game.
var from_pause: bool = false

var _bg: Control = null
var _menubg: MysticMenuBg = null
var _dim: ColorRect = null
var _root: VBoxContainer = null      # dibangun ulang tiap ganti state
var _confirm: PanelContainer = null  # dialog keluar (paritas exit_confirm)
var _pause_panel: PanelContainer = null # panel pause 400x400 (anak MainMenu)
var _topup: MysticTopup = null       # dialog top up (anak MainMenu)
var _hero_tab: String = "starter"    # paritas Menu.shop_tab _core.py:4810
## Slot yang menunggu konfirmasi hapus (-1 = tidak ada) — paritas
## `Menu.slot_delete_confirm` _core.py:3134, dan state yang harus
## ditampilkan setelah dialog selesai (kartu slot ATAU pengaturan).
var _slot_delete_confirm: int = -1
## (nilai awal = State.SLOT_SELECT; selalu diset ulang oleh
## `_open_slot_delete_dialog` sebelum dialog dibangun)
var _slot_delete_return: int = 1


func _ready() -> void:
	name = "MainMenu"
	add_to_group("main_menu")
	# Harus tetap hidup saat SceneTree di-pause (menu PAUSE dibuka justru
	# ketika get_tree().paused = true).
	process_mode = Node.PROCESS_MODE_ALWAYS
	anchor_left = 0.0
	anchor_top = 0.0
	anchor_right = 1.0
	anchor_bottom = 1.0
	offset_left = 0.0
	offset_top = 0.0
	offset_right = 0.0
	offset_bottom = 0.0
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build_backdrop()
	_show(State.MAIN)


# ══════════════════════════════════════════════════════════
#  API untuk Main.gd
# ══════════════════════════════════════════════════════════

func is_open() -> bool:
	return visible


## Paritas menu.pause_mode: menu PAUSE dari dalam match (Main._toggle_pause).
func open_pause() -> void:
	from_pause = true
	_show(State.PAUSE)


## Kembali ke menu utama dengan match dibuang (Main._on_menu_main_menu).
func show_main() -> void:
	from_pause = false
	_show(State.MAIN)


func close() -> void:
	hide()
	menu_coverage_changed.emit(false, false)


# ══════════════════════════════════════════════════════════
#  INPUT
# ══════════════════════════════════════════════════════════

func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event is InputEventKey:
		var key := event as InputEventKey
		if key.pressed and not key.echo and key.keycode == KEY_ESCAPE:
			_handle_escape()
			get_viewport().set_input_as_handled()


## Paritas Menu.handle_key ESC (_core.py:4343-4370): MAIN -> konfirmasi keluar,
## sub-menu -> kembali, PAUSE -> resume.
func _handle_escape() -> void:
	if _confirm != null and _confirm.visible:
		# Paritas _core.py:4356-4363: ESC membatalkan konfirmasi hapus slot
		# (state-nya ikut dibuang, bukan cuma dialog yang disembunyikan).
		if _confirm.has_meta("slot_delete"):
			_slot_delete_confirm = -1
		_confirm.visible = false
		return
	if _slot_delete_confirm > 0:
		# Bug lama: di sini flag tidak di-reset, jadi tiap _show() berikutnya
		# membangun ulang dialog hapus di atas kartu.
		_slot_delete_confirm = -1
		return
	match state:
		State.MAIN:
			if from_pause:
				# menu MAIN yang dibuka dari pause: kembali ke panel PAUSE
				_show(State.PAUSE)
			else:
				_open_exit_confirm()
		State.PAUSE:
			close()
			resume_requested.emit()
		_:
			_show(State.PAUSE if from_pause and state == State.SETTINGS else State.MAIN)


# ══════════════════════════════════════════════════════════
#  KERANGKA
# ══════════════════════════════════════════════════════════

func _build_backdrop() -> void:
	_bg = Control.new()
	_bg.name = "Backdrop"
	_bg.anchor_left = 0.0
	_bg.anchor_top = 0.0
	_bg.anchor_right = 1.0
	_bg.anchor_bottom = 1.0
	_bg.offset_left = 0.0
	_bg.offset_top = 0.0
	_bg.offset_right = 0.0
	_bg.offset_bottom = 0.0
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)
	_menubg = MysticMenuBg.new()
	_menubg.name = "MenuBackground"
	_bg.add_child(_menubg)
	_dim = ColorRect.new()
	_dim.name = "Dim"
	_dim.color = Color(0, 0, 0, 0)
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bg.add_child(_dim)


## Bersihkan isi lalu bangun state baru — padanan Menu.draw() yang memanggil
## _draw_main_menu()/_draw_level_select()/dst. per frame (kita sekali saja).
func _show(new_state: int) -> void:
	state = new_state
	show()
	# PAUSE = arena beku di belakang dim; non-PAUSE = MenuBackground penuh
	# (arena disembunyikan Main.gd).
	var is_pause := new_state == State.PAUSE
	_menubg.visible = not is_pause
	_dim.color = COL_BG_PAUSE if is_pause else Color(0, 0, 0, 0)
	if _root != null:
		_root.queue_free()
	# dialog konfirmasi keluar tidak boleh nyangkut di state baru (pygame
	# memperlakukan exit_confirm sebagai modal yang menutup semua input).
	if _confirm != null and is_instance_valid(_confirm):
		_confirm.queue_free()
	_confirm = null
	if _pause_panel != null and is_instance_valid(_pause_panel):
		_pause_panel.queue_free()
	_pause_panel = null
	if _topup != null and is_instance_valid(_topup):
		_topup.queue_free()
	_topup = null
	_root = VBoxContainer.new()
	_root.name = "Content"
	_root.anchor_left = 0.0
	_root.anchor_top = 0.0
	_root.anchor_right = 1.0
	_root.anchor_bottom = 1.0
	_root.offset_left = 44.0
	_root.offset_top = 18.0
	_root.offset_right = -44.0
	_root.offset_bottom = -14.0
	_root.add_theme_constant_override("separation", 6)
	_root.mouse_filter = Control.MOUSE_FILTER_PASS
	_bg.add_child(_root)
	match state:
		State.SLOT_SELECT:
			_build_slot_select()
		State.LEVEL_SELECT:
			_build_level_select()
		State.HERO_SHOP:
			_build_hero_shop()
		State.SETTINGS:
			_build_settings()
		State.HOW_TO_PLAY:
			_build_how_to_play()
		State.CREDITS:
			_build_credits()
		State.PAUSE:
			_build_pause()
		_:
			_build_main()
	menu_coverage_changed.emit(true, state == State.PAUSE)


## Judul layar tengah (paritas ui_theme.screen_title).
func _screen_header(title: String) -> void:
	var t := MysticTitle.new(title, 30)
	t.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_root.add_child(t)


## Tombol BACK seragam di tengah bawah (paritas ui_theme.back_button:
## pill netral 200x42 + ikon panah).
func _screen_footer_back(back_to: int) -> void:
	var center := CenterContainer.new()
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(center)
	var back := MysticPill.new("BACK", "neutral", "back", 20, false)
	back.custom_minimum_size = Vector2(200, 42)
	center.add_child(back)
	back.pressed.connect(AudioManager.play_sfx.bind("ui_click", 0.5))
	back.pressed.connect(_show.bind(back_to))


## Tombol menu premium + SFX ui_click (paritas SoundManager tiap handler).
func _mbtn(label_text: String, accent: Color, icon: String,
		handler: Callable, min_size: Vector2, font_size: int = 15) -> MysticButton:
	var b := MysticButton.new(label_text, accent, icon, font_size)
	b.custom_minimum_size = min_size
	if handler.is_valid():
		b.pressed.connect(AudioManager.play_sfx.bind("ui_click", 0.5))
		b.pressed.connect(handler)
	return b


## Pill aksi + SFX ui_click.
func _mpill(label_text: String, kind: String, icon: String,
		handler: Callable, min_size: Vector2, font_size: int = 15,
		letter_gap: bool = true) -> MysticPill:
	var b := MysticPill.new(label_text, kind, icon, font_size, letter_gap)
	b.custom_minimum_size = min_size
	if handler.is_valid():
		b.pressed.connect(AudioManager.play_sfx.bind("ui_click", 0.5))
		b.pressed.connect(handler)
	return b


# ══════════════════════════════════════════════════════════
#  AKSI PAUSE (menu tutup dirinya dulu, Main yang unpause/bersih-bersih)
# ══════════════════════════════════════════════════════════

## RESUME: sembunyikan menu baru kemudian minta Main unpause tree — kalau
## dibalik, satu frame menu tertutup tapi simulasi masih beku (terasa jank).
func _do_resume() -> void:
	close()
	resume_requested.emit()


## MAIN MENU: match dibuang — cukup emit; Main._on_menu_main_menu() yang
## meng-unpause, membersihkan arena, DAN memanggil show_main() (satu tempat
## supaya ESC-dari-HUD dan tombol-menu menjalankan alur yang sama).
func _do_main_menu() -> void:
	main_menu_requested.emit()


# ══════════════════════════════════════════════════════════
#  MAIN (paritas _draw_main_menu _core.py:4728-4800)
# ══════════════════════════════════════════════════════════

func _build_main() -> void:
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 6)
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(center)
	var spacer_top := Control.new()
	spacer_top.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(spacer_top)

	var title := MysticTitle.new("MYSTIC ARENA", 54)
	title.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(title)
	# ── pelat subtitle BATTLE ARENA (letterspaced, 32 semibold cyan) ──
	var plate_wrap := CenterContainer.new()
	center.add_child(plate_wrap)
	var plate := MysticPanel.new(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
		UiTheme.EDGE_GOLD, 10.0, 1.0, false)
	plate.show_shadow = false
	plate_wrap.add_child(plate)
	var plate_margin := MarginContainer.new()
	plate_margin.add_theme_constant_override("margin_left", 30)
	plate_margin.add_theme_constant_override("margin_right", 30)
	plate_margin.add_theme_constant_override("margin_top", 6)
	plate_margin.add_theme_constant_override("margin_bottom", 6)
	plate.add_child(plate_margin)
	var sub := Label.new()
	sub.text = UiTheme.letter("BATTLE ARENA")
	UiTheme.style_label(sub, 26, "body_semibold", Color8(150, 195, 255))
	plate_margin.add_child(sub)
	# ── tagline + flourish ──
	var tag := Label.new()
	tag.text = "Dark Fantasy MOBA  •  Tower Defense"
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(tag, 18, "body_medium", UiTheme.TEXT_DIM)
	center.add_child(tag)
	var fl_wrap := CenterContainer.new()
	center.add_child(fl_wrap)
	var fl := MysticFlourish.new(true)
	fl.custom_minimum_size = Vector2(460, 18)
	fl_wrap.add_child(fl)

	# ── baris pertama: CONTINUE + PLAY GAME sejajar ──
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	center.add_child(row)
	var cont := GameManager.next_level_number(_highest_completed())
	if cont <= 0 and GameManager.level_count() > 0:
		cont = int(SaveManager.data.get("last_played_level", 1))
	cont = maxi(cont, 1) # data level belum ada -> mulai dari 1, jangan "LEVEL 0"
	row.add_child(_mbtn("CONTINUE", Color8(140, 225, 255), "continue",
		func(): _request_play(cont), Vector2(300, 50), 20))
	# Paritas _on_button_click "play" _core.py:7022-7023: PLAY GAME lewat
	# layar PILIH SLOT dulu (slot aktif ditentukan di situ). CONTINUE
	# mem-bypass slot select seperti pygame.
	row.add_child(_mbtn("PLAY GAME", Color8(100, 220, 110), "play",
		_show.bind(State.SLOT_SELECT), Vector2(300, 50), 20))

	var buttons: Array = [
		["HERO SHOP", Color8(255, 220, 100), "coin", _show.bind(State.HERO_SHOP)],
		["HOW TO PLAY", Color8(110, 180, 255), "help", _show.bind(State.HOW_TO_PLAY)],
		["SETTINGS", Color8(205, 180, 105), "gear", _show.bind(State.SETTINGS)],
		["CREDITS", Color8(200, 130, 210), "star", _show.bind(State.CREDITS)],
		["QUIT GAME", Color8(225, 90, 90), "quit", _open_exit_confirm],
	]
	for pair in buttons:
		var b := _mbtn(str(pair[0]), pair[1], str(pair[2]), pair[3],
			Vector2(360, 46), 17)
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		center.add_child(b)

	var spacer_bottom := Control.new()
	spacer_bottom.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(spacer_bottom)
	# ── footer: input mode (kiri) + version (tengah) ──
	var footer := Control.new()
	footer.custom_minimum_size = Vector2(0, 24)
	footer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(footer)
	var input_lab := Label.new()
	input_lab.text = "INPUT: KEYBOARD + MOUSE"
	UiTheme.style_label(input_lab, 12, "body", Color8(110, 200, 210))
	input_lab.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	input_lab.position = Vector2(-20, -24)
	footer.add_child(input_lab)
	var version := Label.new()
	version.text = "v2.0  •  MOBA Tower Defense"
	version.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(version, 12, "body", UiTheme.TEXT_FAINT)
	version.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	version.offset_top = -24
	footer.add_child(version)


## Ganti tab Hero Shop (paritas shop_tab) lalu bangun ulang grid.
func _select_hero_tab(tab_id: String) -> void:
	_hero_tab = tab_id
	_show(State.HERO_SHOP)


## Paritas _get_continue_level (_core.py:6990-6996): level setelah level
## tertinggi yang selesai; kalau sudah tamat semua -> level terakhir.
func _highest_completed() -> int:
	var highest := 0
	for lv in SaveManager.data.get("completed_levels", []):
		highest = maxi(highest, int(lv))
	return highest


func _completed_count() -> int:
	var completed = SaveManager.data.get("completed_levels", [])
	return completed.size() if completed is Array else 0


func _request_play(level_num: int) -> void:
	# Tutup menu dulu baru minta mulai — Main yang memanggil connector.
	close()
	play_requested.emit(level_num)


## Dialog konfirmasi keluar (paritas _draw_exit_confirm_dialog: keluar
## tidak pernah langsung tanpa persetujuan pemain).
func _open_exit_confirm() -> void:
	_confirm = _make_dialog(Color8(255, 105, 105))
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	_dialog_add(box)
	var t := MysticTitle.new("QUIT GAME?", 26, UiTheme.GOLD_TEXT,
		UiTheme.GOLD_DEEP)
	t.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(t)
	var msg := Label.new()
	msg.text = "Are you sure you want to close the game?"
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(msg, 15, "body", UiTheme.TEXT_BODY)
	box.add_child(msg)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	box.add_child(row)
	row.add_child(_mpill("YES, EXIT", "danger", "", func(): get_tree().quit(),
		Vector2(150, 40), 15, false))
	row.add_child(_mpill("NO, STAY", "success", "", _hide_confirm,
		Vector2(150, 40), 15, false))


func _hide_confirm() -> void:
	if _confirm != null and is_instance_valid(_confirm):
		_confirm.visible = false


## Dialog modal tengah-layar: dim + MysticPanel + MarginContainer.
## Return panel; isi ditambah via _dialog_add().
var _dialog_margin: MarginContainer = null

func _make_dialog(edge: Color) -> MysticPanel:
	if _confirm != null and is_instance_valid(_confirm):
		_confirm.queue_free()
	_confirm = null
	var dim := ColorRect.new()
	dim.name = "DialogDim"
	dim.color = Color(0, 0, 0, 180.0 / 255.0)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)
	var panel := MysticPanel.new(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
		edge, 12.0, 2.0, true)
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.name = "ConfirmDialog"
	add_child(panel)
	_confirm = panel
	# Dim ikut hilang bersama dialog.
	panel.tree_exiting.connect(dim.queue_free)
	_dialog_margin = MarginContainer.new()
	_dialog_margin.add_theme_constant_override("margin_left", 24)
	_dialog_margin.add_theme_constant_override("margin_right", 24)
	_dialog_margin.add_theme_constant_override("margin_top", 18)
	_dialog_margin.add_theme_constant_override("margin_bottom", 18)
	panel.add_child(_dialog_margin)
	return panel


func _dialog_add(c: Control) -> void:
	_dialog_margin.add_child(c)


## Pusatkan dialog ke ukuran minimum kontennya. (PRESET_CENTER saja
## meninggalkan size 0x0 pada panel baru — MainMenu bukan container yang
## bisa men-sort anaknya, jadi ukuran + posisi harus eksplisit.)
func _center_dialog() -> void:
	if _confirm == null or not is_instance_valid(_confirm):
		return
	var ms := _confirm.get_combined_minimum_size()
	var vp := get_viewport_rect().size
	if vp.x <= 0.0 or vp.y <= 0.0:
		vp = Vector2(1280, 720)
	_confirm.size = ms
	_confirm.position = (vp - ms) * 0.5


# ══════════════════════════════════════════════════════════
#  SLOT_SELECT (paritas _draw_slot_select _core.py:3217-3262)
# ══════════════════════════════════════════════════════════

func _build_slot_select() -> void:
	_screen_header("SELECT SAVE SLOT")
	var sub := Label.new()
	sub.text = "Select a slot to continue, or start a new game"
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(sub, 13, "body", UiTheme.TEXT_DIM)
	_root.add_child(sub)

	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", SLOT_CARD_GAP)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(row)
	for i in range(1, SaveManager.NUM_SLOTS + 1):
		row.add_child(_slot_card(i))
	_screen_footer_back(State.MAIN)

	# Dialog konfirmasi hapus (paritas slot_delete_confirm) dibangun
	# TERAKHIR supaya menutupi kartu — pygame menggambarnya setelah kartu
	# dan menganggapnya modal yang memblokir semua input.
	if _slot_delete_confirm > 0:
		_build_slot_delete_dialog(_slot_delete_confirm)


## Satu kartu slot — paritas `_draw_slot_card` + `_draw_slot_content` +
## `_draw_slot_action_buttons` (_core.py:3264-3468). Nilai DATA yang
## dikunci oracle `save_slots` disimpan di meta kartu (nomor slot, status
## kosong, level tertinggi + nama level, string gold, jumlah hero/boss,
## string terakhir dimainkan, dan label tombol aksi) supaya
## SaveSlotParityTest bisa mereplaynya lewat jalur produksi.
##
## Truncasi nama level adalah FITUR PIKSEL (metrik font
## `ui_theme.fit_ellipsis`) dan tidak diklaim paritas.
func _slot_card(slot_num: int) -> Control:
	var info = SaveManager.get_slot_info(slot_num)
	var is_empty: bool = not (info is Dictionary)
	var highest := 0
	var level_name := ""
	var gold := 0
	var heroes := 0
	var bosses := 0
	var last_played := ""
	if not is_empty:
		var d: Dictionary = info
		highest = int(d.get("highest_level", 0))
		var hero_arr = d.get("purchased_heroes", [])
		var boss_arr = d.get("unlocked_bosses", [])
		heroes = hero_arr.size() if hero_arr is Array else 0
		bosses = boss_arr.size() if boss_arr is Array else 0
		gold = int(d.get("meta_gold", 0))
		last_played = SaveManager.format_last_played(
			float(d.get("slot_last_played", 0)))
		if highest > 0:
			level_name = str(BossDB.get_level(highest).get("name", ""))

	var card := MysticPanel.new(
		UiTheme.LOCKED_BG_TOP if is_empty else UiTheme.PANEL_TOP,
		UiTheme.LOCKED_BG_BOTTOM if is_empty else UiTheme.PANEL_BOTTOM,
		UiTheme.LOCKED_EDGE if is_empty else UiTheme.EDGE_GOLD,
		12.0, 2.0, not is_empty)
	card.set_meta("slot_num", slot_num)
	card.set_meta("is_empty", is_empty)
	card.set_meta("highest_level", highest)
	card.set_meta("level_name", level_name)
	card.set_meta("gold", gold)
	card.set_meta("gold_text", "%s Gold" % _format_grouped(gold))
	card.set_meta("heroes", heroes)
	card.set_meta("bosses", bosses)
	card.set_meta("last_played", last_played)
	card.custom_minimum_size = Vector2(SLOT_CARD_W, SLOT_CARD_H)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 16)
	margin.add_theme_constant_override("margin_right", 16)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_bottom", 14)
	card.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	margin.add_child(box)

	var tag := Label.new()
	tag.text = UiTheme.letter("SAVE GAME")
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(tag, 12, "body_semibold",
		UiTheme.TEXT_DIM if is_empty else UiTheme.GOLD_TEXT)
	box.add_child(tag)
	var num := MysticTitle.new(str(slot_num), 46,
		UiTheme.TEXT_DIM if is_empty else UiTheme.GOLD_TEXT,
		UiTheme.TEXT_FAINT if is_empty else UiTheme.GOLD_DEEP)
	num.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(num)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(spacer)

	if is_empty:
		var empty := Label.new()
		empty.text = UiTheme.letter("EMPTY")
		empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		UiTheme.style_label(empty, 22, "body_bold", UiTheme.TEXT_DIM, true)
		box.add_child(empty)
		var hint := Label.new()
		hint.text = "Tap to start a new game"
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		UiTheme.style_label(hint, 12, "body", UiTheme.TEXT_DIM)
		box.add_child(hint)
	else:
		if highest > 0:
			box.add_child(_slot_line(UiTheme.letter("HIGHEST LEVEL COMPLETED"),
				UiTheme.TEXT_DIM, 11))
			box.add_child(_slot_line("LV. %d" % highest, UiTheme.GOLD_TEXT,
				24, "body_bold"))
			box.add_child(_slot_line(level_name, UiTheme.TEXT_BODY, 15,
				"body_semibold"))
		else:
			box.add_child(_slot_line("No levels completed", UiTheme.TEXT_DIM,
				13))
		var grow := HBoxContainer.new()
		grow.alignment = BoxContainer.ALIGNMENT_CENTER
		grow.add_theme_constant_override("separation", 6)
		box.add_child(grow)
		grow.add_child(MysticIcon.new("coin", UiTheme.GOLD, 0.9))
		var gv := Label.new()
		gv.text = "%s Gold" % _format_grouped(gold)
		UiTheme.style_label(gv, 18, "body_bold", UiTheme.GOLD_TEXT, true)
		grow.add_child(gv)
		box.add_child(_slot_line("Heroes: %d" % heroes, UiTheme.CYAN, 13,
			"body_semibold"))
		box.add_child(_slot_line("Bosses: %d" % bosses, UiTheme.RED, 13,
			"body_semibold"))
		box.add_child(_slot_line(UiTheme.letter("LAST PLAYED"),
			UiTheme.TEXT_DIM, 11))
		box.add_child(_slot_line(last_played, UiTheme.TEXT_BODY, 15,
			"body_semibold"))

	# ── tombol aksi (paritas pill CONTINUE/START NEW GAME + DELETE SAVE) ──
	var play_label := "START NEW GAME" if is_empty else "CONTINUE"
	card.set_meta("play_label", play_label)
	var play := _mpill(play_label, "success", "play",
		_on_slot_select.bind(slot_num), Vector2(0, 40), 15, false)
	play.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_child(play)
	if not is_empty:
		card.set_meta("delete_label", "DELETE SAVE")
		var delete := _mpill("DELETE SAVE", "danger", "quit",
			_open_slot_delete_dialog.bind(slot_num), Vector2(0, 30), 13,
			false)
		delete.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(delete)
	else:
		card.set_meta("delete_label", "")
	card.set_meta("has_delete", not is_empty)
	return card


## Satu baris teks kartu slot.
func _slot_line(text: String, color: Color, font_size: int,
		style: String = "body") -> Label:
	var lab := Label.new()
	lab.text = text
	lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(lab, font_size, style, color, true)
	return lab


## Pilih slot: jadikan slot aktif, muat ulang progresinya, lalu lanjut ke
## PILIH LEVEL — paritas handler `slot_select_N` _core.py:7427-7432.
func _on_slot_select(slot_num: int) -> void:
	SaveManager.set_current_slot(slot_num)
	# Paritas `Menu.reload_progress` _core.py:3576-3578: save_data diganti
	# dengan isi slot yang baru aktif.
	SaveManager.load_save()
	_show(State.LEVEL_SELECT)


## Buka dialog konfirmasi hapus untuk slot ini (paritas `slot_delete_N`
## _core.py:7438-7444 + tombol RESET SAVE di pengaturan _core.py:7016).
func _open_slot_delete_dialog(slot_num: int) -> void:
	_slot_delete_confirm = slot_num
	if state == State.SLOT_SELECT or state == State.SETTINGS:
		_slot_delete_return = state
	else:
		_slot_delete_return = State.SLOT_SELECT
	_build_slot_delete_dialog(slot_num)


## Dialog konfirmasi hapus — paritas `_draw_delete_confirm_dialog`
## (DELETE SLOT? + "Delete SLOT n?" + "This action cannot be undone!" +
## YES, DELETE/CANCEL). Modal: menutupi kartu slot.
func _build_slot_delete_dialog(slot_num: int) -> void:
	_make_dialog(Color8(255, 105, 105))
	_confirm.name = "SlotDeleteConfirm"
	_confirm.set_meta("slot_delete", slot_num)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	_dialog_add(box)
	var title := Label.new()
	title.text = "DELETE SLOT?"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(title, 24, "title", Color8(255, 100, 100), true)
	box.add_child(title)
	var msg := Label.new()
	msg.text = "Delete SLOT %d?" % slot_num
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(msg, 17, "body_semibold", UiTheme.TEXT_WHITE)
	box.add_child(msg)
	var warn := Label.new()
	warn.text = "This action cannot be undone!"
	warn.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(warn, 13, "body", Color8(220, 180, 180))
	box.add_child(warn)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	box.add_child(row)
	row.add_child(_mpill("YES, DELETE", "danger", "",
		_on_slot_delete_confirm.bind(true), Vector2(160, 40), 15, false))
	row.add_child(_mpill("CANCEL", "neutral", "",
		_on_slot_delete_confirm.bind(false), Vector2(160, 40), 15, false))


## Paritas handler `slot_delete_yes` / `slot_delete_no` _core.py:7406-7420
## dan `reset_confirm_yes` _core.py:7333-7341: hapus berkas slot lalu
## muat ulang progresi (slot yang dihapus jadi kosong).
func _on_slot_delete_confirm(confirmed: bool) -> void:
	var slot_num := _slot_delete_confirm
	_slot_delete_confirm = -1
	if confirmed and slot_num > 0:
		SaveManager.delete_slot(slot_num)
		SaveManager.load_save()
	_show(_slot_delete_return)

# ══════════════════════════════════════════════════════════
#  LEVEL_SELECT (paritas _draw_level_select _core.py:3946-4100)
# ══════════════════════════════════════════════════════════

func _build_level_select() -> void:
	_screen_header("SELECT LEVEL")

	# ── pemilih difficulty (paritas tab MODE EASY/NORMAL/HARD 3957-3984) ──
	var diff_row := HBoxContainer.new()
	diff_row.alignment = BoxContainer.ALIGNMENT_CENTER
	diff_row.add_theme_constant_override("separation", 10)
	_root.add_child(diff_row)
	var group := ButtonGroup.new()
	for d in [["easy", "EASY", Color8(100, 210, 255)],
			["normal", "NORMAL", Color8(110, 225, 150)],
			["hard", "HARD", Color8(255, 120, 120)]]:
		var mode := str(d[0])
		var b := MysticTab.new(str(d[1]), d[2], 15)
		b.button_group = group
		b.custom_minimum_size = Vector2(150, 30)
		b.set_pressed_no_signal(GameManager.difficulty == mode)
		b.pressed.connect(GameManager.set_difficulty.bind(mode))
		b.pressed.connect(AudioManager.play_sfx.bind("ui_click", 0.5))
		diff_row.add_child(b)

	# ── progres (paritas "COMPLETED: x / total" + progress bar 3988-3996) ──
	var done := _completed_count()
	var total := GameManager.level_count()
	var prog := Label.new()
	prog.text = "COMPLETED: %d / %d" % [done, total]
	prog.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(prog, 13, "body_semibold", UiTheme.CYAN_SOFT, true)
	_root.add_child(prog)
	var bar := MysticBar.new()
	bar.custom_minimum_size = Vector2(0, 8)
	bar.fill_top = Color8(112, 226, 132)
	bar.fill_bottom = Color8(34, 116, 58)
	bar.track_top = Color8(26, 30, 52)
	bar.track_bottom = Color8(16, 19, 34)
	bar.edge_color = Color8(72, 80, 106)
	bar.show_text = false
	bar.set_fill(float(done), float(total))
	_root.add_child(bar)

	# ── grid kartu level (ScrollContainer; pygame pakai clip+scroll manual) ──
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_root.add_child(scroll)
	var grid := GridContainer.new()
	grid.columns = LEVEL_COLUMNS
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 12)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(grid)
	for lv_data in BossDB.levels:
		if lv_data is Dictionary:
			grid.add_child(_level_card(lv_data))
	if BossDB.levels.is_empty():
		var warn := Label.new()
		warn.text = "LEVELS JSON NOT LOADED — run first:\npython tools/convert_to_godot.py"
		UiTheme.style_label(warn, 14, "body", COL_RED)
		grid.add_child(warn)
	_screen_footer_back(State.MAIN)


## ═══ FASE 20 — helper stat kartu level (paritas _core.py:4257-4278) ═══

## Ribuan koma ala f"{n:,}" Python: 9999 -> "9,999".
func _format_grouped(n: int) -> String:
	var s := str(n)
	var out := ""
	for i in range(s.length()):
		if i > 0 and (s.length() - i) % 3 == 0:
			out += ","
		out += s[i]
	return out


## Paritas skor kartu (_core.py:4257-4259): >= 10000 -> "%.1fK" dari
## pembagian float, di bawahnya -> ribuan koma.
func _format_level_score(score: int) -> String:
	if score >= 10000:
		return "%0.1fK" % (score / 1000.0)
	return _format_grouped(score)


## Paritas truncasi [:8] (_core.py:4260-4261/4266-4267): kalau lebar teks
## terukur melebihi LEVEL_STAT_WIDTH_LIMIT (pygame 280//2-20), potong ke 8
## karakter pertama. Pengukuran memakai metrik font nilai Godot.
func _fit_stat_text(s: String, font_size: int) -> String:
	var width := ThemeDB.fallback_font.get_string_size(
		s, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	if width > LEVEL_STAT_WIDTH_LIMIT:
		return s.substr(0, 8)
	return s


## Paritas win rate (_core.py:4271-4277): int((wins/attempts)*100) —
## truncation ala int() Python — lalu band warna 3 tingkat
## (>=75 hijau / >=50 emas / sisanya oranye). Return (rate, band).
func _level_win_rate(wins: int, attempts: int) -> Vector2i:
	var rate := 0
	if attempts > 0:
		rate = int(float(wins) / float(attempts) * 100.0)
	var band := 2 if rate >= 75 else (1 if rate >= 50 else 0)
	return Vector2i(rate, band)


## Satu sel stat: label kecil redup + nilai (meta `parity` untuk replay
## LevelSelectStatsParityTest — produksi tetap biasa tanpa harness).
func _stat_cell(label: String, value: String, color: Color,
		parity_key: String) -> VBoxContainer:
	var cell := VBoxContainer.new()
	cell.add_theme_constant_override("separation", 0)
	var lab := Label.new()
	lab.text = label
	UiTheme.style_label(lab, 10, "body_semibold", COL_STAT_LABEL)
	cell.add_child(lab)
	var val := Label.new()
	val.text = value
	UiTheme.style_label(val, 16, "body_bold", color, true)
	val.set_meta("parity", parity_key)
	val.set_meta("parity_rgb", [int(color.r8), int(color.g8),
		int(color.b8)])
	cell.add_child(val)
	return cell


## Satu kartu level — paritas _draw_level_card (_core.py:4121-4320): nomor +
## nama + deskripsi + info boss + badge DONE/LOCKED + blok stat BEST SCORE/
## BEST TIME/ATTEMPTS/WIN RATE (FASE 20, _core.py:4247-4291). Klik kartu =
## main (pygame: rect klik = seluruh kartu).
func _level_card(lv: Dictionary) -> Control:
	var level_num := int(lv.get("level_number", 0))
	var unlocked: bool = GameManager.is_level_unlocked(level_num)
	var completed: bool = SaveManager.is_level_completed(level_num)

	var card := MysticPanel.new(
		UiTheme.LOCKED_BG_TOP if not unlocked
			else (UiTheme.DONE_BG_TOP if completed else UiTheme.OPEN_BG_TOP),
		UiTheme.LOCKED_BG_BOTTOM if not unlocked
			else (UiTheme.DONE_BG_BOTTOM if completed else UiTheme.OPEN_BG_BOTTOM),
		UiTheme.LOCKED_EDGE if not unlocked
			else (UiTheme.DONE_EDGE if completed else UiTheme.OPEN_EDGE),
		10.0, 2.0, unlocked)
	card.set_meta("level_num", level_num)
	# 3 kolom x 380 + 2 x 14 gap = 1148 px — muat di 1192 px area konten
	# (1280 - margin backdrop 88), tanpa scroll horizontal.
	card.custom_minimum_size = Vector2(380, 158)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_bottom", 8)
	card.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	margin.add_child(box)

	# ── baris 1: LEVEL n + badge status ──
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 6)
	box.add_child(head)
	var title := Label.new()
	title.text = "LEVEL %d" % level_num
	UiTheme.style_label(title, 15, "body_bold",
		UiTheme.GOLD_TEXT if unlocked else UiTheme.TEXT_FAINT, true)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	if completed:
		head.add_child(MysticIcon.new("check", Color8(140, 255, 175), 0.7))
	elif not unlocked:
		head.add_child(MysticIcon.new("lock", UiTheme.TEXT_FAINT, 0.7))
	var badge := Label.new()
	if completed:
		badge.text = "DONE"
		UiTheme.style_label(badge, 11, "body_bold", Color8(140, 255, 175))
	elif not unlocked:
		badge.text = "LOCKED"
		UiTheme.style_label(badge, 11, "body_bold", UiTheme.TEXT_FAINT)
	else:
		badge.text = "READY"
		UiTheme.style_label(badge, 11, "body_bold", UiTheme.GREEN)
	head.add_child(badge)

	# ── baris 2: nama + deskripsi ──
	var name_l := Label.new()
	name_l.text = str(lv.get("name", "Level %d" % level_num))
	UiTheme.style_label(name_l, 17, "body_semibold",
		UiTheme.TEXT_WHITE if unlocked else Color8(140, 148, 174), true)
	box.add_child(name_l)
	var desc := Label.new()
	desc.text = str(lv.get("description", ""))
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(desc, 11, "body", UiTheme.TEXT_DIM)
	box.add_child(desc)

	# ── baris 3: tema map + boss ──
	var true_boss := str(lv.get("true_boss", ""))
	var true_name := str(BossDB.get_boss(true_boss).get("name", true_boss))
	var minis: Array = []
	var mini_dict: Dictionary = lv.get("mini_bosses", {})
	for wave in mini_dict:
		var bt := str(mini_dict[wave])
		minis.append(str(BossDB.get_boss(bt).get("name", bt)))
	var info := Label.new()
	info.text = "Theme: %s  ·  Mini Boss: %s  ·  True Boss: %s" % [
		str(lv.get("map_theme", "forest")).to_upper(),
		", ".join(minis) if not minis.is_empty() else "-",
		true_name if not true_name.is_empty() else "-"]
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(info, 11, "body_medium", Color8(242, 158, 158))
	box.add_child(info)

	# ── baris 3.5: blok stat (FASE 20 — paritas _core.py:4247-4291) ──
	# pygame hanya menggambar blok ini untuk kartu TERBUKA; attempts == 0
	# menampilkan "No stats yet".
	if unlocked:
		var stats: Dictionary = SaveManager.get_level_stats(
			SaveManager.data, level_num)
		var attempts := int(stats.get("total_attempts", 0))
		if attempts > 0:
			var grid := GridContainer.new()
			grid.columns = 2
			grid.add_theme_constant_override("h_separation", 16)
			grid.add_theme_constant_override("v_separation", 4)
			box.add_child(grid)
			var wins := int(stats.get("wins", 0))
			var wr := _level_win_rate(wins, attempts)
			# Slot skor (kolom 1): label + nilai warna GOLD_TEXT.
			# Truncasi diukur pada px SETARA pygame (20/19 — val_font_bold/
			# val_font _core.py:4262-4263) meski render lebih kecil, agar
			# rasio string terhadap ambang 120px pygame dipertahankan.
			grid.add_child(_stat_cell("BEST SCORE",
				_fit_stat_text(_format_level_score(int(
					stats.get("best_score", 0))), 20),
				COL_STAT_SCORE, "score"))
			# Slot waktu (kolom 2): label + nilai warna CYAN_SOFT.
			grid.add_child(_stat_cell("BEST TIME",
				_fit_stat_text(SaveManager.format_time(int(
					stats.get("best_time_seconds", 0))), 19),
				COL_STAT_TIME, "time"))
			# Baris 2 (paritas row2_y = stats_y + 40): attempts + win rate.
			grid.add_child(_stat_cell("ATTEMPTS",
				"%dW/%d" % [wins, attempts], COL_STAT_ATTEMPTS,
				"attempts"))
			# Band warna win rate (paritas _core.py:4274-4277):
			# >=75 hijau / >=50 emas / sisanya oranye.
			var wr_color: Color = COL_WR_LOW
			if wr.y >= 2:
				wr_color = COL_WR_GREEN
			elif wr.y == 1:
				wr_color = COL_WR_GOLD
			grid.add_child(_stat_cell("WIN RATE", "%d%%" % wr.x, wr_color,
				"win_rate"))
		else:
			var empty := Label.new()
			empty.text = "No stats yet"
			UiTheme.style_label(empty, 11, "body", COL_STAT_LABEL)
			box.add_child(empty)

	# ── baris 4: aksi ──
	if unlocked:
		var label := "REPLAY" if completed else "PLAY"
		var btn := _mpill(label, "success", "play",
			_request_play.bind(level_num), Vector2(0, 32), 15, false)
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(btn)
	else:
		# paritas teks kunci _core.py:4303 "Complete Level X first"
		var req := int(lv.get("unlock_after_level", 0))
		var lock := Label.new()
		lock.text = "Complete Level %d first" % req
		UiTheme.style_label(lock, 11, "body", UiTheme.TEXT_FAINT)
		box.add_child(lock)
		var lock_pill := MysticPill.new("LOCKED", "locked", "lock", 14, false)
		lock_pill.custom_minimum_size = Vector2(0, 30)
		lock_pill.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		lock_pill.disabled = true
		box.add_child(lock_pill)
	return card


# ══════════════════════════════════════════════════════════
#  HERO SHOP (paritas _draw_hero_shop _core.py:4808-5300)
# ══════════════════════════════════════════════════════════

## Meta gold dipakai untuk membuka hero (paritas _unlock_hero_in_meta_shop
## _core.py:5298: cek unlock_require_boss dulu, lalu meta_gold, baru append
## ke purchased_heroes — di Godot: SaveManager.unlock_hero()).
func _build_hero_shop() -> void:
	_screen_header("HERO SHOP")

	# ── chip meta gold (paritas "HERO GOLD" chip _core.py:4821-4826) ──
	var chips := HBoxContainer.new()
	chips.alignment = BoxContainer.ALIGNMENT_CENTER
	chips.add_theme_constant_override("separation", 12)
	_root.add_child(chips)
	var gold_chip := MysticChip.new("coin",
		"HERO GOLD: %d" % SaveManager.meta_gold(), UiTheme.GOLD, 16)
	gold_chip.custom_minimum_size = Vector2(240, 34)
	chips.add_child(gold_chip)
	var boss_chip := MysticChip.new("skull",
		"BOSSES DEFEATED: %d" % (SaveManager.data.get(
			"unlocked_bosses", []) as Array).size(), UiTheme.CYAN_SOFT, 16)
	boss_chip.custom_minimum_size = Vector2(280, 34)
	chips.add_child(boss_chip)
	chips.add_child(_mpill("TOP UP", "success", "coin", _open_topup,
		Vector2(130, 34), 14, false))
	# ── legenda singkatan sekolah damage (verbatim pygame) ──
	var legend := Label.new()
	legend.text = ("PHY = fisik kena armor  ·  MAG = sihir tembus armor  "
		+ "·  TNK = badak")
	legend.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	UiTheme.style_label(legend, 13, "body_semibold", Color8(150, 156, 180))
	legend.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chips.add_child(legend)

	# ── tab STARTER HEROES / MINI BOSSES / TRUE BOSSES (paritas 4837-4857) ──
	var tabs := HBoxContainer.new()
	tabs.alignment = BoxContainer.ALIGNMENT_CENTER
	tabs.add_theme_constant_override("separation", 8)
	_root.add_child(tabs)
	var group := ButtonGroup.new()
	var tab_font := UiTheme.font("body_semibold")
	for pair in [["starter", "STARTER HEROES", Color8(100, 200, 255)],
			["mini", "MINI BOSSES", Color8(255, 160, 100)],
			["true", "TRUE BOSSES", Color8(255, 110, 110)]]:
		var tab_id := str(pair[0])
		var b := MysticTab.new(str(pair[1]), pair[2], 15)
		b.button_group = group
		b.custom_minimum_size = Vector2(UiTheme.tab_width(tab_font,
			str(pair[1]), 15, 150.0), 32)
		b.set_pressed_no_signal(_hero_tab == tab_id)
		b.pressed.connect(_select_hero_tab.bind(tab_id))
		b.pressed.connect(AudioManager.play_sfx.bind("ui_click", 0.5))
		tabs.add_child(b)

	# ── grid hero ──
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_root.add_child(scroll)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 10)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(grid)
	# Filter paritas 4925-4946: starter = bukan boss hero; mini/true per boss_class.
	var shown := 0
	for hero_type in HeroDB.heroes:
		var d: Dictionary = HeroDB.get_hero(str(hero_type))
		if d.is_empty():
			continue
		var is_boss := bool(d.get("is_boss_hero", false))
		var bclass := str(d.get("boss_class", "mini"))
		if _hero_tab == "starter" and is_boss:
			continue
		if _hero_tab == "mini" and (not is_boss or bclass != "mini"):
			continue
		if _hero_tab == "true" and (not is_boss or bclass != "true"):
			continue
		grid.add_child(_hero_card(str(hero_type), d))
		shown += 1
	if shown == 0:
		var empty := Label.new()
		# Katalog kosong = data belum dikonversi — jangan biarkan layar
		# "kosong diam-diam"; tunjukkan penyebab + perbaikannya.
		empty.text = "No heroes in this category." if not HeroDB.heroes.is_empty() \
			else "heroes.json NOT LOADED — run first: python tools/convert_to_godot.py"
		UiTheme.style_label(empty, 13, "body",
			UiTheme.TEXT_DIM if not HeroDB.heroes.is_empty() else COL_RED)
		empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		grid.add_child(empty)
	_screen_footer_back(State.MAIN)


## Satu kartu hero — paritas _draw_meta_hero_card _core.py:5050-5296:
## potret + nama + stat + status (OWNED / Defeat: X / cost) + pill kanan
## (OWNED / LOCKED / FREE / UNLOCK). Keputusan kartu dihitung sekali di
## sini; meta di akhir fungsi dipakai replay MetaShopTxnParityTest.
func _hero_card(hero_type: String, d: Dictionary) -> Control:
	var card := MysticPanel.new(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
		UiTheme.EDGE_GOLD, 8.0, 1.0, false)
	# 2 kolom x 585 + 12 gap = 1182 px < 1192 px area konten menu
	card.custom_minimum_size = Vector2(585, 0)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_bottom", 8)
	card.add_child(margin)

	var owned: bool = SaveManager.is_unlocked(hero_type)
	var cost := int(d.get("unlock_cost", 600))
	# JSON null (starter tanpa syarat boss) — str(null) = "<null>" yang
	# bikin starter dianggap terkunci boss; normalkan ke "" (FASE 20).
	var req_raw = d.get("unlock_require_boss", "")
	var req_boss := "" if req_raw == null else str(req_raw)
	var boss_ready: bool = req_boss.is_empty() or SaveManager.is_boss_unlocked(req_boss)
	# Keputusan kartu (paritas _draw_meta_hero_card _core.py:5050-5060:
	# can_unlock = DEV off AND gold >= cost).
	var affordable: bool = SaveManager.meta_gold() >= cost

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	margin.add_child(row)
	# ── potret (frame idle bake; gelap kalau boss-locked) ──
	var port := TextureRect.new()
	port.custom_minimum_size = Vector2(72, 72)
	port.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	port.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	port.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var atlas := _portrait(hero_type)
	if atlas != null:
		port.texture = atlas
		if owned or boss_ready:
			port.modulate = Color.WHITE
		else:
			port.modulate = Color(0.3, 0.3, 0.38)
	else:
		port.modulate = Color(0.3, 0.32, 0.4)
	row.add_child(port)
	# Bingkai potret emas tipis (di belakang: sibling sebelum = kegambar duluan).
	# (Digambar sebagai Panel di bawah TextureRect via show_behind... TextureRect
	# bukan container — bingkai digambar manual lewat sibling ColorRect? Lewatkan:
	# MysticIcon fallback bila atlas kosong.)
	if atlas == null:
		var fb := MysticIcon.new("shield", UiTheme.TEXT_DIM, 2.0)
		fb.custom_minimum_size = Vector2(72, 72)
		row.add_child(fb)
		port.queue_free()

	# ── info tengah ──
	var info := VBoxContainer.new()
	info.add_theme_constant_override("separation", 2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(info)
	var title := Label.new()
	title.text = "%s — %s" % [str(d.get("name", hero_type)), str(d.get("title", ""))]
	UiTheme.style_label(title, 15, "body_semibold", UiTheme.TEXT_WHITE, true)
	info.add_child(title)
	var stat := Label.new()
	stat.text = "HP %d · DMG %d · RNG %d · %s" % [
		int(d.get("hp", 0)), int(d.get("damage", 0)), int(d.get("range", 0)),
		str(d.get("dmg_type", "PHYSICAL"))]
	UiTheme.style_label(stat, 11, "body", UiTheme.TEXT_DIM)
	info.add_child(stat)
	# Chip role + sekolah damage.
	var chips := HBoxContainer.new()
	chips.add_theme_constant_override("separation", 8)
	info.add_child(chips)
	var role := Label.new()
	role.text = str(d.get("role", "-"))
	UiTheme.style_label(role, 11, "body_semibold", UiTheme.TEXT_DIM)
	chips.add_child(role)
	var sch: Array = _school_chip(d)
	var sch_lab := Label.new()
	sch_lab.text = str(sch[0])
	UiTheme.style_label(sch_lab, 11, "body_bold", sch[1])
	chips.add_child(sch_lab)
	chips.add_child(MysticIcon.new(str(sch[2]), sch[1], 0.55))
	# ── status (ikon + teks, paritas status_y) ──
	var status := HBoxContainer.new()
	status.add_theme_constant_override("separation", 6)
	info.add_child(status)
	if owned:
		status.add_child(MysticIcon.new("check", UiTheme.GREEN, 0.55))
		var own := Label.new()
		own.text = UiTheme.letter("OWNED")
		UiTheme.style_label(own, 14, "body_bold", UiTheme.GREEN)
		status.add_child(own)
	elif not boss_ready:
		status.add_child(MysticIcon.new("lock", Color8(200, 120, 120), 0.55))
		var boss_name := str(BossDB.get_boss(req_boss).get("name", req_boss))
		var lock := Label.new()
		lock.text = "Defeat: %s" % boss_name
		UiTheme.style_label(lock, 13, "body_medium", Color8(205, 150, 150))
		status.add_child(lock)
	else:
		status.add_child(MysticIcon.new("coin", UiTheme.GOLD, 0.55))
		var cost_lab := Label.new()
		if cost <= 0:
			cost_lab.text = "FREE"
			UiTheme.style_label(cost_lab, 14, "body_bold", UiTheme.GREEN)
		else:
			cost_lab.text = "%s G" % _format_grouped(cost)
			UiTheme.style_label(cost_lab, 14, "body_bold", UiTheme.GOLD_TEXT)
		status.add_child(cost_lab)

	# ── pill kanan 104x34 (paritas btn_rect) ──
	var pill_wrap := CenterContainer.new()
	row.add_child(pill_wrap)
	if owned:
		var p := MysticPill.new("OWNED", "owned", "check", 13, false)
		p.custom_minimum_size = Vector2(104, 34)
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		pill_wrap.add_child(p)
	elif not boss_ready:
		var p2 := MysticPill.new("LOCKED", "locked", "lock", 13, false)
		p2.custom_minimum_size = Vector2(104, 34)
		p2.disabled = true
		pill_wrap.add_child(p2)
	else:
		var label := "FREE" if cost <= 0 else "UNLOCK"
		var p3 := _mpill(label, "gold" if affordable else "neutral", "coin",
			_try_unlock_hero.bind(hero_type), Vector2(104, 34), 13, false)
		pill_wrap.add_child(p3)

	# Meta keputusan kartu untuk replay MetaShopTxnParityTest (FASE 20):
	# padanan status _draw_meta_hero_card pygame (OWNED / boss-locked /
	# pill label+kind) tanpa mengubah tampilan apa pun.
	card.set_meta("hero_type", hero_type)
	card.set_meta("owned", owned)
	card.set_meta("boss_ready", boss_ready)
	card.set_meta("affordable", affordable)
	card.set_meta("unlock_cost", cost)
	return card


## Chip sekolah damage (paritas _core.py:5142-5168): PHY oranye /
## MAG biru / +·TNK hijau untuk tank.
func _school_chip(d: Dictionary) -> Array:
	var sch := str(d.get("dmg_type", "PHYSICAL")).to_upper()
	var role := str(d.get("role", "")).to_upper()
	var is_tank := "TANK" in role
	if is_tank:
		return ["PHY·TNK" if sch != "MAGIC" else "MAG·TNK",
			Color8(130, 226, 168), "shield"]
	if sch == "MAGIC":
		return ["MAG", Color8(150, 196, 255), "bolt"]
	return ["PHY", Color8(255, 178, 92), "swords"]


## Potret hero: frame idle pertama strip bake (di-cache per tipe).
static func _portrait(hero_type: String) -> AtlasTexture:
	if _portrait_cache.has(hero_type):
		return _portrait_cache[hero_type]
	var atlas: AtlasTexture = null
	var entry: Dictionary = BakedUnitDB.entry(hero_type)
	var tex: Texture2D = BakedUnitDB.texture(hero_type)
	if not entry.is_empty() and tex != null:
		atlas = AtlasTexture.new()
		atlas.atlas = tex
		atlas.region = Rect2(0, 0, float(entry.get("frame_w", 64)),
			float(entry.get("frame_h", 64)))
		_portrait_cache[hero_type] = atlas
	return atlas


## Buka dialog TOP UP HERO GOLD (paritas tombol TOP UP 4828-4831).
func _open_topup() -> void:
	if _topup != null and is_instance_valid(_topup):
		_topup.queue_free()
	_topup = MysticTopup.new()
	add_child(_topup)
	_topup.closed.connect(_on_topup_closed)
	_topup.open()


func _on_topup_closed() -> void:
	if _topup != null and is_instance_valid(_topup):
		_topup.queue_free()
	_topup = null
	if state == State.HERO_SHOP:
		_show(State.HERO_SHOP) # segarkan chip gold + status kartu


## Paritas _unlock_hero_in_meta_shop (_core.py:5298-5328): validasi katalog +
## boss requirement + saldo, potong meta_gold, lalu SaveManager.unlock_hero().
func _try_unlock_hero(hero_type: String) -> void:
	if HeroDB.get_hero(hero_type).is_empty():
		AudioManager.play_sfx("ui_error")
		return
	if SaveManager.is_unlocked(hero_type):
		AudioManager.play_sfx("ui_error")
		return
	var d: Dictionary = HeroDB.get_hero(hero_type)
	# JSON null (starter tanpa syarat boss) — normalkan ke "" (FASE 20;
	# str(null) = "<null>" dulu bikin beli semua starter selalu ditolak).
	var req_raw = d.get("unlock_require_boss", "")
	var req_boss := "" if req_raw == null else str(req_raw)
	if not req_boss.is_empty() and not SaveManager.is_boss_unlocked(req_boss):
		AudioManager.play_sfx("ui_error")
		return
	var cost := int(d.get("unlock_cost", 600))
	if SaveManager.meta_gold() < cost:
		AudioManager.play_sfx("ui_error")
		return
	SaveManager.add_meta_gold(-cost)
	SaveManager.unlock_hero(hero_type)
	AudioManager.play_sfx("ui_buy")
	print("[HeroShop] %s dibuka (-%d meta gold)" % [hero_type, cost])
	_show(State.HERO_SHOP) # segarkan chip gold + status kartu


# ══════════════════════════════════════════════════════════
#  SETTINGS (paritas _draw_settings _core.py:6221-6390)
# ══════════════════════════════════════════════════════════

## Layout 2 kolom 900px — paritas struktur _draw_settings pygame:
## KOLOM KIRI = AUDIO + CLOUD SAVE, KOLOM KANAN = GAMEPLAY + GRAPHICS +
## DANGER ZONE. Voice tidak dipasang (tidak ada file voice di repo —
## slider-nya tidak akan berfungsi); Language terkunci ENGLISH.
func _build_settings() -> void:
	_screen_header("SETTINGS")

	var center := CenterContainer.new()
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(center)
	var panel := MysticPanel.new(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
		UiTheme.EDGE_GOLD, 12.0, 2.0, true)
	panel.custom_minimum_size = Vector2(900, 540)
	center.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 40)
	margin.add_theme_constant_override("margin_right", 40)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 24)
	panel.add_child(margin)
	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 40)
	margin.add_child(cols)

	# ── KOLOM KIRI: AUDIO + CLOUD SAVE ──
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 10)
	cols.add_child(left)
	left.add_child(_settings_header("AUDIO", "speaker", UiTheme.CYAN))
	left.add_child(_volume_row("Master Volume", "master", 0.7))
	left.add_child(_volume_row("SFX Volume", "sfx", 0.6))
	left.add_child(_volume_row("Music Volume", "bgm", 0.35))
	left.add_child(_settings_header("CLOUD SAVE", "cloud", UiTheme.CYAN_SOFT))
	# Cloud save (Play Games) tidak di-port — tombol tampil disabled
	# verbatim pygame + status jujur (bukan dipalsukan berfungsi).
	for spec in [["SIGN IN TO CLOUD", "cloud"],
			["UPLOAD SAVE KE CLOUD", "upload"],
			["DOWNLOAD SAVE DARI CLOUD", "download"]]:
		var cb := MysticPill.new(str(spec[0]), "locked", str(spec[1]), 12,
			false)
		cb.custom_minimum_size = Vector2(0, 32)
		cb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		cb.disabled = true
		left.add_child(cb)
	var cloud := Label.new()
	cloud.text = ("Cloud save is not available in the Godot port — "
		+ "progress is stored in 3 LOCAL SLOTS.")
	cloud.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(cloud, 11, "body", UiTheme.TEXT_DIM)
	left.add_child(cloud)

	# ── KOLOM KANAN: GAMEPLAY + GRAPHICS + DANGER ZONE ──
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 10)
	cols.add_child(right)
	right.add_child(_settings_header("GAMEPLAY", "swords",
		Color8(110, 235, 160)))
	right.add_child(_option_row("Difficulty",
		HudLayout.mode_label(GameManager.difficulty),
		HudLayout.mode_color(GameManager.difficulty),
		_cycle_difficulty))
	# Screen shake — paritas toggle pygame; BENAR-BENAR berfungsi:
	# Camera2D masuk grup "camera" (Main._ready) + guard di Boss._shake.
	right.add_child(_toggle_row("Screen Shake", "screen_shake", 1.0,
		func(on: bool): GameManager.set_screen_shake(on)))
	# Damage numbers — flag dikonsumsi WorldPopups, bisa diubah live.
	right.add_child(_toggle_row("Damage Numbers", "damage_numbers_enabled",
		1.0, func(on: bool): GameManager.set_damage_numbers(on)))
	right.add_child(_option_row("Game Speed", _speed_label(),
		UiTheme.TEXT_WHITE, _cycle_speed))
	right.add_child(_static_row("Language", "ENGLISH", UiTheme.TEXT_DIM))
	right.add_child(_settings_header("GRAPHICS", "monitor", UiTheme.ORANGE))
	right.add_child(_option_row("FPS Limit", _fps_label(),
		UiTheme.TEXT_WHITE, _cycle_fps))
	right.add_child(_settings_header("DANGER ZONE", "warn", UiTheme.RED))
	var reset := _mpill("RESET SAVE SLOT", "danger", "warn",
		_open_slot_delete_dialog.bind(SaveManager.get_current_slot()),
		Vector2(0, 40), 15, false)
	reset.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_child(reset)

	_screen_footer_back(State.PAUSE if from_pause else State.MAIN)


## Header seksi settings: ikon + label letterspaced + garis aturan.
func _settings_header(text: String, icon: String, color: Color) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.add_child(MysticIcon.new(icon, color, 0.9))
	var lab := Label.new()
	lab.text = UiTheme.letter(text)
	UiTheme.style_label(lab, 17, "body_semibold", color)
	row.add_child(lab)
	var rule := ColorRect.new()
	rule.color = Color(color.r, color.g, color.b, 0.35)
	rule.custom_minimum_size = Vector2(0, 2)
	rule.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rule.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(rule)
	return row


## Baris volume (port _draw_volume_row): label + bar + pill -/+ + persen.
func _volume_row(label_text: String, key: String,
		default_vol: float) -> Control:
	var row := MysticSliderRow.new(label_text,
		SaveManager.get_setting(key, default_vol), 1.0)
	row.custom_minimum_size = Vector2(0, 56)
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.changed.connect(func(v: float) -> void:
		SaveManager.set_setting(key, v, true)
		AudioManager.apply_settings()
		AudioManager.play_sfx("ui_click", 0.3))
	return row


## Baris toggle (port _draw_toggle_setting): label + MysticToggle.
func _toggle_row(label_text: String, key: String, default_on: float,
		apply: Callable) -> Control:
	var opt := MysticOptionRow.new(label_text)
	opt.name = "Toggle_" + key
	var t := MysticToggle.new(SaveManager.get_setting(key, default_on) > 0.5)
	t.custom_minimum_size = Vector2(76, 28)
	t.toggled_on.connect(func(on: bool) -> void:
		apply.call(on)
		SaveManager.set_setting(key, 1.0 if on else 0.0, true)
		AudioManager.play_sfx("ui_click", 0.5))
	opt.right_box.add_child(t)
	return opt


## Baris opsi dengan chevron < nilai > (port _draw_option_setting).
func _option_row(label_text: String, value_text: String, value_color: Color,
		cycle: Callable) -> Control:
	var opt := MysticOptionRow.new(label_text)
	var left := _chevron("chevron_l")
	opt.right_box.add_child(left)
	var val := Label.new()
	val.text = value_text
	val.custom_minimum_size = Vector2(110, 0)
	val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(val, 15, "body_semibold", value_color, true)
	opt.right_box.add_child(val)
	var right := _chevron("chevron_r")
	opt.right_box.add_child(right)
	left.pressed.connect(func() -> void: cycle.call(-1))
	right.pressed.connect(func() -> void: cycle.call(1))
	return opt


## Baris statis label: nilai (untuk opsi terkunci/non-interaktif).
func _static_row(label_text: String, value_text: String,
		value_color: Color) -> Control:
	var opt := MysticOptionRow.new(label_text)
	var val := Label.new()
	val.text = value_text
	UiTheme.style_label(val, 15, "body_semibold", value_color)
	opt.right_box.add_child(val)
	return opt


func _chevron(icon: String) -> Button:
	var b := Button.new()
	b.text = ""
	b.custom_minimum_size = Vector2(34, 30)
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color8(36, 44, 66)
	normal.border_color = Color8(100, 110, 140)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(6)
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color8(56, 64, 96)
	hover.border_color = UiTheme.GOLD
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", hover)
	b.add_theme_stylebox_override("focus", normal)
	var icon_c := MysticIcon.new(icon, UiTheme.TEXT_WHITE, 0.7)
	icon_c.set_anchors_preset(Control.PRESET_FULL_RECT)
	b.add_child(icon_c)
	return b


func _cycle_difficulty(direction: int) -> void:
	var modes := ["easy", "normal", "hard"]
	var idx := modes.find(GameManager.difficulty)
	if idx < 0:
		idx = 1
	GameManager.set_difficulty(modes[(idx + direction) % 3])
	AudioManager.play_sfx("ui_click", 0.5)
	_show(State.SETTINGS)


func _speed_label() -> String:
	var v := float(SaveManager.get_setting("game_speed", 1.0))
	var s := "%.2f" % v
	while s.ends_with("0") and not s.ends_with(".0"):
		s = s.substr(0, s.length() - 1)
	return s + "x"


func _cycle_speed(direction: int) -> void:
	var v := float(SaveManager.get_setting("game_speed", 1.0))
	var idx := 2
	var best := 999.0
	for i in SPEED_OPTIONS.size():
		var dist: float = absf(float(SPEED_OPTIONS[i]) - v)
		if dist < best:
			best = dist
			idx = i
	var next: float = SPEED_OPTIONS[(idx + direction) % SPEED_OPTIONS.size()]
	SaveManager.set_setting("game_speed", next, true)
	Engine.time_scale = next
	AudioManager.play_sfx("ui_click", 0.5)
	_show(State.SETTINGS)


func _fps_label() -> String:
	var v := int(SaveManager.get_setting("fps_limit", 60))
	if v == 0:
		return "Unlimited"
	return "%d FPS" % v


func _cycle_fps(direction: int) -> void:
	var v := int(SaveManager.get_setting("fps_limit", 60))
	var idx := FPS_OPTIONS.find(v)
	if idx < 0:
		idx = 1
	var next: int = FPS_OPTIONS[(idx + direction) % FPS_OPTIONS.size()]
	SaveManager.set_setting("fps_limit", next, true)
	Engine.max_fps = next
	AudioManager.play_sfx("ui_click", 0.5)
	_show(State.SETTINGS)


# ══════════════════════════════════════════════════════════
#  HOW TO PLAY (paritas _draw_how_to_play _core.py:6144-6212)
# ══════════════════════════════════════════════════════════

func _build_how_to_play() -> void:
	_screen_header("HOW TO PLAY")
	var center := CenterContainer.new()
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(center)
	var panel := MysticPanel.new(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
		UiTheme.EDGE_GOLD, 12.0, 2.0, true)
	panel.custom_minimum_size = Vector2(900, 0)
	center.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 28)
	margin.add_theme_constant_override("margin_right", 28)
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_bottom", 20)
	panel.add_child(margin)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	margin.add_child(scroll)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(box)
	# Verbatim pygame (sections _core.py:6161-6192).
	var sections: Array = [
		["OBJECTIVE", "shield", [
			"Destroy the enemy castle before they destroy yours!"]],
		["BUILDING TOWERS", "gem", [
			"Tap empty build slots (+) to build towers. Cost: 100 gold."]],
		["HEROES", "crown", [
			"Buy heroes from Hero Shop. Tap to select, tap enemy to attack."]],
		["TACTICAL COMMANDS", "swords", [
			"G = GATHER all heroes together",
			"T = PROTECT TOWER (min 2)   |   C = PROTECT CASTLE (all)",
			"B = ATTACK BOSS (all)   |   D = ATTACK TOP DEALER (all)"]],
		["SKILLS", "bolt", [
			"Q, W, E, R auto-cast when enemies nearby. R = Ultimate!"]],
		["UPGRADES", "plus", [
			"Tap towers, castle, or hero to upgrade. Stronger = win!"]],
		["CASTLE SHIELD", "shield", [
			"At Castle Level 4, buy a permanent shield for 850 gold."]],
	]
	for section in sections:
		var head := HBoxContainer.new()
		head.add_theme_constant_override("separation", 8)
		box.add_child(head)
		head.add_child(MysticIcon.new(str(section[1]), UiTheme.GOLD, 0.8))
		var h := Label.new()
		h.text = UiTheme.letter(str(section[0]))
		UiTheme.style_label(h, 17, "body_bold", UiTheme.GOLD_TEXT)
		head.add_child(h)
		for line in section[2]:
			var body := Label.new()
			body.text = str(line)
			body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			UiTheme.style_label(body, 15, "body_medium", UiTheme.TEXT_BODY)
			body.offset_left = 30.0
			box.add_child(body)
		var gap := Control.new()
		gap.custom_minimum_size = Vector2(0, 8)
		box.add_child(gap)
	_screen_footer_back(State.MAIN)


# ══════════════════════════════════════════════════════════
#  CREDITS (paritas _draw_credits _core.py:6859-6925)
# ══════════════════════════════════════════════════════════

func _build_credits() -> void:
	_screen_header("CREDITS")
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 6)
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(center)
	var game_title := MysticTitle.new("Tower Defense Battle Arena", 30)
	game_title.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	center.add_child(game_title)
	var gap0 := Control.new()
	gap0.custom_minimum_size = Vector2(0, 10)
	center.add_child(gap0)
	var credits: Array = [
		["Game Design & Programming", "Dharmawan Toxi"],
		["Art Direction", "Dark Fantasy Vector Style"],
		["Sound Effects & Music", "Custom SFX Library"],
		["Special Thanks", "Pygame Community  •  Python 3.10+"],
	]
	for row in credits:
		var role := Label.new()
		role.text = UiTheme.letter(str(row[0]))
		role.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		UiTheme.style_label(role, 13, "body_medium", UiTheme.TEXT_DIM)
		center.add_child(role)
		var who := Label.new()
		who.text = str(row[1])
		who.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		UiTheme.style_label(who, 17, "body_semibold", UiTheme.TEXT_WHITE,
			true)
		center.add_child(who)
		var gap := Control.new()
		gap.custom_minimum_size = Vector2(0, 8)
		center.add_child(gap)
	# "Made with ♥ using Pygame" (hati digambar, bukan emoji).
	var heart_row := HBoxContainer.new()
	heart_row.alignment = BoxContainer.ALIGNMENT_CENTER
	heart_row.add_theme_constant_override("separation", 8)
	center.add_child(heart_row)
	var left := Label.new()
	left.text = "Made with"
	UiTheme.style_label(left, 15, "body_medium", Color8(255, 150, 200))
	heart_row.add_child(left)
	heart_row.add_child(MysticIcon.new("heart", Color8(255, 120, 160), 0.9))
	var right := Label.new()
	right.text = "using Pygame"
	UiTheme.style_label(right, 15, "body_medium", Color8(255, 150, 200))
	heart_row.add_child(right)
	_screen_footer_back(State.MAIN)


# ══════════════════════════════════════════════════════════
#  PAUSE (paritas _draw_pause_menu _core.py:6930-7000)
# ══════════════════════════════════════════════════════════

func _build_pause() -> void:
	# Panel 400x400 terpusat (paritas geometri pause pygame) — anak LANGSUNG
	# MainMenu (Control biasa, BUKAN container) dengan posisi/ukuran eksplisit:
	# di dalam VBox _root/_bg geometrinya dikendalikan layout (bug: rect jadi
	# (44,18,400,408) — margin backdrop + tinggi konten).
	var panel := MysticPanel.new(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
		UiTheme.EDGE_GOLD, 12.0, 2.0, true)
	panel.name = "PausePanel"
	panel.position = HudLayout.PAUSE_PANEL_POS
	panel.size = HudLayout.PAUSE_PANEL_SIZE
	add_child(panel)
	_pause_panel = panel

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_bottom", 14)
	panel.add_child(margin)
	var inner := VBoxContainer.new()
	inner.alignment = BoxContainer.ALIGNMENT_CENTER
	# separation 7: minimum gabungan konten + margin harus <= 400, kalau
	# tidak Control.size dijepit naik ke minimum (bug lama: 400x408).
	inner.add_theme_constant_override("separation", 7)
	margin.add_child(inner)

	var title := MysticTitle.new("PAUSED", 42)
	title.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	inner.add_child(title)

	# badge difficulty (paritas mode badge 6949-6960)
	var mode := Label.new()
	mode.name = "PauseMode"
	mode.text = "MODE: %s" % HudLayout.mode_label(GameManager.difficulty)
	mode.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(mode, 14, "body_semibold",
		HudLayout.mode_color(GameManager.difficulty))
	inner.add_child(mode)
	inner.add_child(MysticFlourish.new(false))

	# Urutan paritas PAUSE_BUTTON_ORDER; ukuran 300x48 = pygame.
	var buttons: Array = [
		["PauseResume", "RESUME", Color8(100, 200, 100), "play", _do_resume],
		["PauseSettings", "SETTINGS", Color8(200, 180, 100), "gear",
			_show.bind(State.SETTINGS)],
		["PauseMenu", "MAIN MENU", Color8(100, 180, 255), "back",
			_do_main_menu],
		["PauseQuit", "QUIT GAME", Color8(220, 80, 80), "quit",
			func(): get_tree().quit()],
	]
	for pair in buttons:
		var b := _mbtn(str(pair[1]), pair[2], str(pair[3]), pair[4],
			HudLayout.PAUSE_BUTTON_SIZE, 16)
		b.name = str(pair[0])
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		inner.add_child(b)
