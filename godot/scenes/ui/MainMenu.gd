# MainMenu.gd — Menu utama + sub-menu, dibangun 100% dari kode.
#
# Port state machine `class MenuState` pygame (_core.py:3097-3105):
#   MAIN · LEVEL_SELECT · HERO_SHOP · SETTINGS · HOW_TO_PLAY · CREDITS · PAUSE
# pygame menggambar semuanya manual per frame di Menu.draw(); di Godot cukup
# bangun ulang isi container tiap pindah state (pola HUD.gd/ShopPanel.gd —
# tanpa .tscn besar, tanpa per-frame draw).
#
# Sinyal keluar (dipasang Main.gd):
#   play_requested(level_num) — LEVEL_SELECT/CONTINUE -> mulai match
#   resume_requested          — PAUSE -> lanjut main
#   main_menu_requested       — PAUSE/victory -> buang match, balik MAIN
# Difficulty diubah langsung lewat GameManager.set_difficulty() (paritas
# toggle_level_difficulty), pembelian hero lewat SaveManager (paritas
# _unlock_hero_in_meta_shop _core.py:5298-5328).
extends Control

# Satu sumber tipografi untuk seluruh UI menu. Pygame menggunakan Barlow
# sebagai font body; sebelumnya Control yang dibuat runtime jatuh ke fallback
# Godot sehingga ukuran glyph, wrapping, dan lebar tombol berbeda antar layar.
const UI_FONT: Font = preload("res://assets/fonts/Barlow-Regular.ttf")
const UI_FONT_BOLD: Font = preload("res://assets/fonts/Barlow-SemiBold.ttf")

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

## Layar menu non-PAUSE = LAYAR PENUH opak total (arena di belakangnya
## disembunyikan Main.gd — alpha 1.0 jadi tidak ada celah transparansi).
# Palet dikunci dari ui_theme.py pygame (RGB integer), bukan aproksimasi.
const COL_BG := Color8(9, 12, 26)
## PAUSE = dim gelap semi-transparan di atas arena BEKU (paritas pygame
## pause menu yang menggambar frame game terakhir + overlay gelap).
const COL_BG_PAUSE := Color(0.035, 0.047, 0.102, 0.62)
const COL_PANEL := Color8(21, 26, 48)
const COL_BORDER := Color8(176, 144, 82)
const COL_TEXT := Color8(240, 244, 255)
const COL_DIM := Color8(132, 142, 170)
const COL_GOLD := Color8(255, 220, 110)
const COL_BLUE := Color8(102, 184, 255)
const COL_GREEN := Color8(107, 230, 140)
const COL_RED := Color8(255, 107, 107)
const COL_LOCKED := Color8(96, 106, 136)

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

var state: int = State.MAIN
## True kalau menu dibuka dari dalam match (PAUSE) — MAIN-nya jadi "MAIN MENU"
## yang kembali ke permainan, bukan menutup game.
var from_pause: bool = false

var _bg: PanelContainer = null
var _bg_style: StyleBoxFlat = null
var _root: VBoxContainer = null      # dibangun ulang tiap ganti state
var _confirm: PanelContainer = null  # dialog keluar (paritas exit_confirm)
var _pause_panel: PanelContainer = null # panel pause 400x400 (anak MainMenu)
var _hero_tab: String = "starter"    # paritas Menu.shop_tab _core.py:4810
## Slot yang menunggu konfirmasi hapus (-1 = tidak ada) — paritas
## `Menu.slot_delete_confirm` _core.py:3134, dan state yang harus
## ditampilkan setelah dialog selesai (kartu slot ATAU pengaturan).
var _slot_delete_confirm: int = -1
## (nilai awal = State.SLOT_SELECT; selalu diset ulang oleh
## `_open_slot_delete_dialog` sebelum dialog dibangun)
var _slot_delete_return: int = 1


func _ready() -> void:
	# Theme diwariskan ke semua Label/Button/LineEdit yang dibangun runtime.
	# Ini menjaga metrik teks sama di MAIN, SLOT_SELECT, shop, settings,
	# pause, dan dialog modal; override warna/ukuran lokal tetap berlaku.
	var ui_theme := Theme.new()
	ui_theme.default_font = UI_FONT
	ui_theme.set_font("font", "Label", UI_FONT)
	ui_theme.set_font("font", "Button", UI_FONT_BOLD)
	ui_theme.set_font("font", "LineEdit", UI_FONT)
	theme = ui_theme
	name = "MainMenu"
	add_to_group("main_menu")
	# Harus tetap hidup saat SceneTree di-pause (menu PAUSE dibuka justru
	# ketika get_tree().paused = true).
	process_mode = Node.PROCESS_MODE_ALWAYS
	# Layar PENUH eksplisit (anchors + offsets): backdrop menu tidak boleh
	# pernah lebih kecil dari viewport — bug layout lama membuat menu
	# menempel di kiri layar sementara arena+HUD tetap kelihatan di samping.
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
	_bg = PanelContainer.new()
	_bg.name = "Backdrop"
	# anchors + offsets eksplisit (bukan set_anchors_preset saja): panel
	# backdrop WAJIB menutup seluruh viewport — tanpa offset eksplisit ada
	# risiko rect tetap 0x0 di beberapa urutan layout.
	_bg.anchor_left = 0.0
	_bg.anchor_top = 0.0
	_bg.anchor_right = 1.0
	_bg.anchor_bottom = 1.0
	_bg.offset_left = 0.0
	_bg.offset_top = 0.0
	_bg.offset_right = 0.0
	_bg.offset_bottom = 0.0
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_BG
	sb.border_color = COL_BORDER
	sb.border_width_bottom = 2
	# padding konten (pygame: panel mulai x=... ; di sini margin global)
	sb.content_margin_left = 44.0
	sb.content_margin_right = 44.0
	sb.content_margin_top = 18.0
	sb.content_margin_bottom = 14.0
	_bg_style = sb
	_bg.add_theme_stylebox_override("panel", sb)
	add_child(_bg)


## Bersihkan isi lalu bangun state baru — padanan Menu.draw() yang memanggil
## _draw_main_menu()/_draw_level_select()/dst. per frame (kita sekali saja).
func _show(new_state: int) -> void:
	state = new_state
	show()
	# Warna backdrop per state + status penutupan terhadap arena (Main.gd
	# yang mengikuti: non-PAUSE = arena disembunyikan, PAUSE = arena beku
	# di belakang dim).
	if _bg_style != null:
		_bg_style.bg_color = COL_BG_PAUSE if new_state == State.PAUSE else COL_BG
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
	_root = VBoxContainer.new()
	_root.name = "Content"
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
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


## Judul layar (paritas ui_theme.screen_title) + tombol KEMBALI di kanan.
func _screen_header(title: String, back_to: int = -1) -> void:
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	_root.add_child(header)
	var label := Label.new()
	label.text = title
	label.add_theme_font_size_override("font_size", 30)
	label.add_theme_color_override("font_color", COL_GOLD)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(label)
	if back_to >= 0:
		header.add_child(_make_button("KEMBALI (ESC)", COL_DIM,
			_show.bind(back_to), Vector2(150, 30)))


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
	center.add_theme_constant_override("separation", 8)
	_root.add_child(center)
	# spacer supaya blok tombol jatuh di tengah-bawah seperti pygame (y=336+)
	var spacer_top := Control.new()
	spacer_top.custom_minimum_size = Vector2(0, 96)
	spacer_top.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(spacer_top)

	var title := Label.new()
	title.text = "MYSTIC ARENA"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 58)
	title.add_theme_color_override("font_color", COL_GOLD)
	title.add_theme_color_override("font_outline_color", Color(0.1, 0.06, 0.02, 1))
	title.add_theme_constant_override("outline_size", 8)
	center.add_child(title)
	var subtitle := Label.new()
	subtitle.text = "BATTLE ARENA  ·  Dark Fantasy MOBA / Tower Defense"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_font_size_override("font_size", 15)
	subtitle.add_theme_color_override("font_color", COL_BLUE)
	center.add_child(subtitle)

	# ── tombol: LANJUTKAN + MULAI GAME sejajar (paritas CONTINUE/PLAY GAME) ──
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	center.add_child(row)
	var cont := GameManager.next_level_number(_highest_completed())
	if cont <= 0 and GameManager.level_count() > 0:
		cont = int(SaveManager.data.get("last_played_level", 1))
	cont = maxi(cont, 1) # data level belum ada -> mulai dari 1, jangan "LEVEL 0"
	row.add_child(_make_button("LANJUTKAN — LEVEL %d" % cont, COL_BLUE,
		func(): _request_play(cont), Vector2(250, 44), 18))
	# Paritas _on_button_click "play" _core.py:7022-7023: MULAI GAME lewat
	# layar PILIH SLOT dulu (slot aktif ditentukan di situ). LANJUTKAN
	# mem-bypass slot select seperti pygame.
	row.add_child(_make_button("MULAI GAME", COL_GREEN,
		_show.bind(State.SLOT_SELECT), Vector2(250, 44), 18))

	var buttons: Array = [
		["HERO SHOP", COL_GOLD, _show.bind(State.HERO_SHOP)],
		["CARA MAIN (HOW TO PLAY)", COL_BLUE, _show.bind(State.HOW_TO_PLAY)],
		["PENGATURAN (SETTINGS)", Color(0.85, 0.75, 0.45), _show.bind(State.SETTINGS)],
		["KREDIT", Color(0.8, 0.55, 0.85), _show.bind(State.CREDITS)],
		["KELUAR GAME", COL_RED, _open_exit_confirm],
	]
	for pair in buttons:
		center.add_child(_make_button(str(pair[0]), pair[1], pair[2],
			Vector2(360, 38), 15))

	var spacer_bottom := Control.new()
	spacer_bottom.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(spacer_bottom)
	var meta := SaveManager.meta_gold()
	var info := Label.new()
	info.text = "Meta gold: %d  ·  %d / %d level selesai  ·  %d hero dimiliki" % [
		meta, _completed_count(), GameManager.level_count(),
		(SaveManager.data.get("unlocked_heroes", []) as Array).size()]
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.add_theme_font_size_override("font_size", 12)
	info.add_theme_color_override("font_color", COL_DIM)
	center.add_child(info)
	var version := Label.new()
	version.text = "v2.0  ·  Port Godot 4  ·  sumber kebenaran gameplay: pygame"
	version.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	version.add_theme_font_size_override("font_size", 10)
	version.add_theme_color_override("font_color", Color(0.5, 0.54, 0.66))
	center.add_child(version)


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


## Dialog konfirmasi keluar (paritas exit_confirm _core.py:4348-4351: keluar
## tidak pernah langsung tanpa persetujuan pemain).
func _open_exit_confirm() -> void:
	if _confirm != null and is_instance_valid(_confirm):
		_confirm.queue_free()
	_confirm = PanelContainer.new()
	_confirm.name = "ExitConfirm"
	# PRESET_CENTER dengan mode MINSIZE: dialog seukuran kontennya, persis
	# di tengah layar (set_anchors_preset saja meninggalkan offset 0 -> pojok).
	_confirm.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_confirm.mouse_filter = Control.MOUSE_FILTER_STOP
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_PANEL
	sb.border_color = COL_RED
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 18.0
	sb.content_margin_right = 18.0
	sb.content_margin_top = 12.0
	sb.content_margin_bottom = 12.0
	_confirm.add_theme_stylebox_override("panel", sb)
	add_child(_confirm)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	_confirm.add_child(box)
	var q := Label.new()
	q.text = "Keluar dari Mystic Arena?"
	q.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	q.add_theme_font_size_override("font_size", 17)
	q.add_theme_color_override("font_color", COL_TEXT)
	box.add_child(q)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	box.add_child(row)
	row.add_child(_make_button("YA, KELUAR", COL_RED,
		func(): get_tree().quit(), Vector2(140, 32)))
	row.add_child(_make_button("BATAL", COL_GREEN,
		func(): _confirm.visible = false, Vector2(140, 32)))


# ══════════════════════════════════════════════════════════
#  SLOT_SELECT (paritas _draw_slot_select _core.py:3217-3262)
# ══════════════════════════════════════════════════════════

func _build_slot_select() -> void:
	_screen_header("PILIH SLOT SAVE", State.MAIN)
	var sub := Label.new()
	sub.text = "Pilih slot untuk lanjut, atau mulai permainan baru"
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_font_size_override("font_size", 13)
	sub.add_theme_color_override("font_color", COL_DIM)
	_root.add_child(sub)

	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", SLOT_CARD_GAP)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(row)
	for i in range(1, SaveManager.NUM_SLOTS + 1):
		row.add_child(_slot_card(i))

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
## Beda disengaja yang terdokumentasi: label UI Godot berbahasa Indonesia
## (KOSONG / LEVEL TERTINGGI / HAPUS SAVE / ...); nilai datanya identik
## dengan pygame. Truncasi nama level adalah FITUR PIKSEL (metrik font
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

	var card := PanelContainer.new()
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
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.08, 0.11) if is_empty else COL_PANEL
	sb.border_color = COL_LOCKED if is_empty else COL_BORDER
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(12)
	sb.content_margin_left = 16.0
	sb.content_margin_right = 16.0
	sb.content_margin_top = 12.0
	sb.content_margin_bottom = 14.0
	card.add_theme_stylebox_override("panel", sb)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	card.add_child(box)

	var tag := Label.new()
	tag.text = "SAVE GAME"
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tag.add_theme_font_size_override("font_size", 12)
	tag.add_theme_color_override(
		"font_color", COL_DIM if is_empty else COL_GOLD)
	box.add_child(tag)
	var num := Label.new()
	num.text = str(slot_num)
	num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	num.add_theme_font_size_override("font_size", 46)
	num.add_theme_color_override(
		"font_color", COL_LOCKED if is_empty else COL_GOLD)
	box.add_child(num)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(spacer)

	if is_empty:
		var empty := Label.new()
		empty.text = "KOSONG"
		empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty.add_theme_font_size_override("font_size", 22)
		empty.add_theme_color_override("font_color", COL_LOCKED)
		box.add_child(empty)
		var hint := Label.new()
		hint.text = "Ketuk untuk mulai permainan baru"
		hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		hint.add_theme_font_size_override("font_size", 12)
		hint.add_theme_color_override("font_color", COL_DIM)
		box.add_child(hint)
	else:
		if highest > 0:
			box.add_child(_slot_line("LEVEL TERTINGGI SELESAI", COL_DIM, 11))
			box.add_child(_slot_line("LV. %d" % highest, COL_GOLD, 24))
			box.add_child(_slot_line(level_name, COL_TEXT, 15))
		else:
			box.add_child(_slot_line("Belum ada level selesai", COL_DIM, 13))
		box.add_child(_slot_line("%s Gold" % _format_grouped(gold),
			COL_GOLD, 18))
		box.add_child(_slot_line("Hero: %d" % heroes, COL_BLUE, 13))
		box.add_child(_slot_line("Boss: %d" % bosses, COL_RED, 13))
		box.add_child(_slot_line("TERAKHIR DIMAINKAN", COL_DIM, 11))
		box.add_child(_slot_line(last_played, COL_TEXT, 15))

	# ── tombol aksi (paritas pill CONTINUE/START NEW GAME + DELETE SAVE) ──
	var play_label := "MULAI BARU" if is_empty else "LANJUTKAN"
	card.set_meta("play_label", play_label)
	box.add_child(_make_button(play_label,
		COL_BLUE if is_empty else COL_GREEN,
		_on_slot_select.bind(slot_num), Vector2(280, 40), 15))
	if not is_empty:
		card.set_meta("delete_label", "HAPUS SAVE")
		box.add_child(_make_button("HAPUS SAVE", COL_RED,
			_open_slot_delete_dialog.bind(slot_num), Vector2(280, 30), 13))
	else:
		card.set_meta("delete_label", "")
	card.set_meta("has_delete", not is_empty)
	return card


## Satu baris teks kartu slot.
func _slot_line(text: String, color: Color, font_size: int) -> Label:
	var lab := Label.new()
	lab.text = text
	lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lab.add_theme_font_size_override("font_size", font_size)
	lab.add_theme_color_override("font_color", color)
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
## _core.py:3471-3570 ("Delete SLOT n?" + "This action cannot be undone!"
## + tombol YES/NO). Modal: menutupi kartu slot.
func _build_slot_delete_dialog(slot_num: int) -> void:
	if _confirm != null and is_instance_valid(_confirm):
		_confirm.queue_free()
	_confirm = PanelContainer.new()
	_confirm.name = "SlotDeleteConfirm"
	_confirm.set_meta("slot_delete", slot_num)
	_confirm.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_confirm.mouse_filter = Control.MOUSE_FILTER_STOP
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.16, 0.10, 0.12)
	sb.border_color = COL_RED
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(12)
	sb.content_margin_left = 24.0
	sb.content_margin_right = 24.0
	sb.content_margin_top = 16.0
	sb.content_margin_bottom = 16.0
	_confirm.add_theme_stylebox_override("panel", sb)
	add_child(_confirm)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	_confirm.add_child(box)
	var title := Label.new()
	title.text = "HAPUS SLOT?"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", COL_RED)
	box.add_child(title)
	var msg := Label.new()
	msg.text = "Hapus SAVE GAME %d?" % slot_num
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg.add_theme_font_size_override("font_size", 16)
	msg.add_theme_color_override("font_color", COL_TEXT)
	box.add_child(msg)
	var warn := Label.new()
	warn.text = "Tindakan ini tidak bisa dibatalkan!"
	warn.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	warn.add_theme_font_size_override("font_size", 12)
	warn.add_theme_color_override("font_color", Color(0.86, 0.7, 0.7))
	box.add_child(warn)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	box.add_child(row)
	row.add_child(_make_button("YA, HAPUS", COL_RED,
		_on_slot_delete_confirm.bind(true), Vector2(160, 36)))
	row.add_child(_make_button("BATAL", COL_GREEN,
		_on_slot_delete_confirm.bind(false), Vector2(160, 36)))


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
	_screen_header("PILIH LEVEL", State.MAIN)

	# ── pemilih difficulty (paritas tombol MODE: EASY/NORMAL/HARD 3957-3984) ──
	var diff_row := HBoxContainer.new()
	diff_row.alignment = BoxContainer.ALIGNMENT_CENTER
	diff_row.add_theme_constant_override("separation", 10)
	_root.add_child(diff_row)
	var group := ButtonGroup.new()
	for d in [["easy", "MUDAH", Color(0.4, 0.85, 1.0)],
			["normal", "NORMAL", COL_GREEN],
			["hard", "SULIT", COL_RED]]:
		var mode := str(d[0])
		var b := Button.new()
		b.text = str(d[1])
		b.toggle_mode = true
		b.button_group = group
		b.custom_minimum_size = Vector2(150, 30)
		b.set_pressed_no_signal(GameManager.difficulty == mode)
		b.pressed.connect(GameManager.set_difficulty.bind(mode))
		b.pressed.connect(AudioManager.play_sfx.bind("ui_click"))
		b.add_theme_color_override("font_color",
			d[2] if GameManager.difficulty == mode else COL_DIM)
		diff_row.add_child(b)

	# ── progres (paritas "COMPLETED: x / total" + progress bar 3988-3996) ──
	var done := _completed_count()
	var total := GameManager.level_count()
	var prog := Label.new()
	prog.text = "SELESAI: %d / %d  ·  hard = musuh +15%% HP, +10%% damage (scaling aktif)" % [
		done, total]
	prog.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prog.add_theme_font_size_override("font_size", 13)
	prog.add_theme_color_override("font_color", Color(0.5, 0.85, 0.95))
	_root.add_child(prog)
	var bar := ProgressBar.new()
	bar.max_value = maxf(1.0, float(total))
	bar.value = float(done)
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(0, 8)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb_bg := StyleBoxFlat.new()
	sb_bg.bg_color = Color(0.1, 0.12, 0.18)
	sb_bg.set_corner_radius_all(3)
	var sb_fill := StyleBoxFlat.new()
	sb_fill.bg_color = COL_GREEN
	sb_fill.set_corner_radius_all(3)
	bar.add_theme_stylebox_override("background", sb_bg)
	bar.add_theme_stylebox_override("fill", sb_fill)
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
		# levels.json belum ada/belum dikonversi — layar level select harus
		# menjelaskan, bukan hening.
		var warn := Label.new()
		warn.text = "LEVELS JSON BELUM DIMUAT — jalankan dulu:\npython tools/convert_to_godot.py"
		warn.add_theme_color_override("font_color", COL_RED)
		warn.add_theme_font_size_override("font_size", 14)
		grid.add_child(warn)


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
	lab.add_theme_font_size_override("font_size", 10)
	lab.add_theme_color_override("font_color", COL_STAT_LABEL)
	cell.add_child(lab)
	var val := Label.new()
	val.text = value
	val.add_theme_font_size_override("font_size", 16)
	val.add_theme_color_override("font_color", color)
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

	var card := PanelContainer.new()
	card.set_meta("level_num", level_num)
	# 3 kolom x 380 + 2 x 14 gap = 1148 px — muat di 1192 px area konten
	# (1280 - margin backdrop 88), tanpa scroll horizontal.
	card.custom_minimum_size = Vector2(380, 158)
	var sb := StyleBoxFlat.new()
	# gradasi per status (paritas LOCKED/DONE/OPEN_BG_TOP)
	if not unlocked:
		sb.bg_color = Color(0.07, 0.08, 0.11)
		sb.border_color = COL_LOCKED
	elif completed:
		sb.bg_color = Color(0.05, 0.11, 0.07)
		sb.border_color = Color(0.3, 0.75, 0.45)
	else:
		sb.bg_color = COL_PANEL
		sb.border_color = COL_BORDER if unlocked else COL_LOCKED
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 12.0
	sb.content_margin_right = 12.0
	sb.content_margin_top = 8.0
	sb.content_margin_bottom = 8.0
	card.add_theme_stylebox_override("panel", sb)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	card.add_child(box)

	# ── baris 1: LEVEL n + badge status ──
	var head := HBoxContainer.new()
	box.add_child(head)
	var title := Label.new()
	title.text = "LEVEL %d" % level_num
	title.add_theme_font_size_override("font_size", 15)
	title.add_theme_color_override("font_color",
		COL_GOLD if unlocked else COL_LOCKED)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	var badge := Label.new()
	if completed:
		badge.text = "SELESAI"
		badge.add_theme_color_override("font_color", Color(0.55, 0.95, 0.7))
	elif not unlocked:
		badge.text = "TERKUNCI"
		badge.add_theme_color_override("font_color", COL_LOCKED)
	else:
		badge.text = "SIAP MAIN"
		badge.add_theme_color_override("font_color", COL_GREEN)
	badge.add_theme_font_size_override("font_size", 11)
	head.add_child(badge)

	# ── baris 2: nama + deskripsi ──
	var name_l := Label.new()
	name_l.text = str(lv.get("name", "Level %d" % level_num))
	name_l.add_theme_font_size_override("font_size", 17)
	name_l.add_theme_color_override("font_color",
		COL_TEXT if unlocked else Color(0.55, 0.58, 0.68))
	box.add_child(name_l)
	var desc := Label.new()
	desc.text = str(lv.get("description", ""))
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.add_theme_font_size_override("font_size", 11)
	desc.add_theme_color_override("font_color", COL_DIM)
	box.add_child(desc)

	# ── baris 3: tema map + boss (data sudah di levels.json, sekarang dibaca) ──
	var true_boss := str(lv.get("true_boss", ""))
	var true_name := str(BossDB.get_boss(true_boss).get("name", true_boss))
	var minis: Array = []
	var mini_dict: Dictionary = lv.get("mini_bosses", {})
	for wave in mini_dict:
		var bt := str(mini_dict[wave])
		minis.append(str(BossDB.get_boss(bt).get("name", bt)))
	var info := Label.new()
	info.text = "Tema: %s  ·  Mini boss: %s  ·  True boss: %s" % [
		str(lv.get("map_theme", "forest")).to_upper(),
		", ".join(minis) if not minis.is_empty() else "-",
		true_name if not true_name.is_empty() else "-"]
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_font_size_override("font_size", 11)
	info.add_theme_color_override("font_color", Color(0.95, 0.62, 0.62))
	box.add_child(info)

	# ── baris 3.5: blok stat (FASE 20 — paritas _core.py:4247-4291) ──
	# pygame hanya menggambar blok ini untuk kartu TERBUKA; attempts == 0
	# menampilkan "No stats yet" (Godot: "Belum ada statistik" — beda
	# bahasa yang dikunci eksplisit, nilai datanya tetap paritas).
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
			grid.add_child(_stat_cell("SKOR TERBAIK",
				_fit_stat_text(_format_level_score(int(
					stats.get("best_score", 0))), 20),
				COL_STAT_SCORE, "score"))
			# Slot waktu (kolom 2): label + nilai warna CYAN_SOFT.
			grid.add_child(_stat_cell("WAKTU TERBAIK",
				_fit_stat_text(SaveManager.format_time(int(
					stats.get("best_time_seconds", 0))), 19),
				COL_STAT_TIME, "time"))
			# Baris 2 (paritas row2_y = stats_y + 40): attempts + win rate.
			grid.add_child(_stat_cell("ATTEMPT",
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
			empty.text = "Belum ada statistik"
			empty.add_theme_font_size_override("font_size", 11)
			empty.add_theme_color_override("font_color", COL_STAT_LABEL)
			box.add_child(empty)

	# ── baris 4: aksi ──
	if unlocked:
		var label := "MAIN" if not completed else "MAIN LAGI"
		var btn := _make_button(label, COL_GREEN, _request_play.bind(level_num),
			Vector2(0, 30), 13)
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(btn)
	else:
		# paritas teks kunci _core.py:4303 "Complete Level X first"
		var lock := Label.new()
		var req := int(lv.get("unlock_after_level", 0))
		lock.text = "Selesaikan Level %d dulu untuk membuka" % req
		lock.add_theme_font_size_override("font_size", 11)
		lock.add_theme_color_override("font_color", COL_LOCKED)
		box.add_child(lock)
	return card


# ══════════════════════════════════════════════════════════
#  HERO SHOP (paritas _draw_hero_shop _core.py:4808-5300)
# ══════════════════════════════════════════════════════════

## Meta gold dipakai untuk membuka hero (paritas _unlock_hero_in_meta_shop
## _core.py:5298: cek unlock_require_boss dulu, lalu meta_gold, baru append
## ke purchased_heroes — di Godot: SaveManager.unlock_hero()).
func _build_hero_shop() -> void:
	_screen_header("HERO SHOP", State.MAIN)

	# ── chip meta gold (paritas "HERO GOLD" chip _core.py:4821-4826) ──
	var chips := HBoxContainer.new()
	chips.alignment = BoxContainer.ALIGNMENT_CENTER
	chips.add_theme_constant_override("separation", 16)
	_root.add_child(chips)
	var gold_chip := Label.new()
	gold_chip.text = "HERO GOLD: %d" % SaveManager.meta_gold()
	gold_chip.add_theme_font_size_override("font_size", 18)
	gold_chip.add_theme_color_override("font_color", COL_GOLD)
	chips.add_child(gold_chip)
	var boss_chip := Label.new()
	boss_chip.text = "BOSS DIKALAHKAN: %d" % (SaveManager.data.get(
		"unlocked_bosses", []) as Array).size()
	boss_chip.add_theme_font_size_override("font_size", 18)
	boss_chip.add_theme_color_override("font_color", Color(0.5, 0.85, 0.95))
	chips.add_child(boss_chip)

	# ── tab STARTER / MINI BOSS / TRUE BOSS (paritas 4837-4857) ──
	var tabs := HBoxContainer.new()
	tabs.alignment = BoxContainer.ALIGNMENT_CENTER
	tabs.add_theme_constant_override("separation", 8)
	_root.add_child(tabs)
	var group := ButtonGroup.new()
	for pair in [["starter", "STARTER", Color(0.4, 0.8, 1.0)],
			["mini", "MINI BOSS", Color(1.0, 0.6, 0.4)],
			["true", "TRUE BOSS", Color(1.0, 0.35, 0.4)]]:
		var tab_id := str(pair[0])
		var b := Button.new()
		b.text = str(pair[1])
		b.toggle_mode = true
		b.button_group = group
		b.set_pressed_no_signal(_hero_tab == tab_id)
		b.custom_minimum_size = Vector2(150, 30)
		b.pressed.connect(_select_hero_tab.bind(tab_id))
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
		empty.text = "Tidak ada hero di kategori ini." if not HeroDB.heroes.is_empty() \
			else "heroes.json BELUM DIMUAT — jalankan dulu: python tools/convert_to_godot.py"
		empty.add_theme_color_override("font_color",
			COL_DIM if not HeroDB.heroes.is_empty() else COL_RED)
		empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		grid.add_child(empty)


## Satu kartu hero: stat + status (DIMILIKI / buka dengan meta gold / terkunci
## sampai boss dikalahkan). Paritas _unlock_hero_in_meta_shop _core.py:5302-5327.
func _hero_card(hero_type: String, d: Dictionary) -> Control:
	var card := PanelContainer.new()
	# 2 kolom x 585 + 12 gap = 1182 px < 1192 px area konten menu
	card.custom_minimum_size = Vector2(585, 0)
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_PANEL
	sb.border_color = COL_BORDER
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(8)
	sb.content_margin_left = 12.0
	sb.content_margin_right = 12.0
	sb.content_margin_top = 8.0
	sb.content_margin_bottom = 8.0
	card.add_theme_stylebox_override("panel", sb)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	card.add_child(box)

	var head := HBoxContainer.new()
	box.add_child(head)
	var title := Label.new()
	title.text = "%s — %s" % [str(d.get("name", hero_type)), str(d.get("title", ""))]
	title.add_theme_font_size_override("font_size", 15)
	title.add_theme_color_override("font_color", COL_TEXT)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)

	var owned: bool = SaveManager.is_unlocked(hero_type)
	var cost := int(d.get("unlock_cost", 600))
	# JSON null (starter tanpa syarat boss) — str(null) = "<null>" yang
	# bikin starter dianggap terkunci boss; normalkan ke "" (FASE 20).
	var req_raw = d.get("unlock_require_boss", "")
	var req_boss := "" if req_raw == null else str(req_raw)
	var boss_ready: bool = req_boss.is_empty() or SaveManager.is_boss_unlocked(req_boss)
	# Keputusan kartu dihitung sekali di sini (paritas _draw_meta_hero_card
	# _core.py:5050-5060: can_unlock = DEV off AND gold >= cost). Meta di
	# akhir fungsi dipakai replay MetaShopTxnParityTest.
	var affordable: bool = SaveManager.meta_gold() >= cost

	var stat := Label.new()
	stat.text = "HP %d · DMG %d · RANGE %d · %s" % [
		int(d.get("hp", 0)), int(d.get("damage", 0)), int(d.get("range", 0)),
		str(d.get("dmg_type", "PHYSICAL"))]
	stat.add_theme_font_size_override("font_size", 11)
	stat.add_theme_color_override("font_color", COL_DIM)
	box.add_child(stat)

	var action := HBoxContainer.new()
	action.add_theme_constant_override("separation", 10)
	box.add_child(action)
	if owned:
		var own := Label.new()
		own.text = "DIMILIKI"
		own.add_theme_font_size_override("font_size", 13)
		own.add_theme_color_override("font_color", COL_GREEN)
		action.add_child(own)
		var note := Label.new()
		note.text = "beli di TOKO dalam game (B) untuk men-summon"
		note.add_theme_font_size_override("font_size", 10)
		note.add_theme_color_override("font_color", COL_DIM)
		action.add_child(note)
	elif not boss_ready:
		# paritas 5311-5314: unlock_require_boss belum dikalahkan -> tolak
		var boss_name := str(BossDB.get_boss(req_boss).get("name", req_boss))
		var lock := Label.new()
		lock.text = "TERKUNCI — kalahkan %s dulu" % boss_name
		lock.add_theme_font_size_override("font_size", 12)
		lock.add_theme_color_override("font_color", COL_LOCKED)
		action.add_child(lock)
	else:
		var label := "GRATIS" if cost <= 0 else "BUKA — %d" % cost
		var btn := _make_button(label, COL_GOLD if affordable else COL_LOCKED,
			_try_unlock_hero.bind(hero_type), Vector2(140, 28), 12)
		btn.disabled = not affordable
		action.add_child(btn)
		var bal := Label.new()
		bal.text = "(gold %d / %d)" % [SaveManager.meta_gold(), cost]
		bal.add_theme_font_size_override("font_size", 10)
		bal.add_theme_color_override("font_color", COL_DIM)
		action.add_child(bal)
	# Meta keputusan kartu untuk replay MetaShopTxnParityTest (FASE 20):
	# padanan status _draw_meta_hero_card pygame (OWNED / boss-locked /
	# pill label+kind) tanpa mengubah tampilan apa pun.
	card.set_meta("hero_type", hero_type)
	card.set_meta("owned", owned)
	card.set_meta("boss_ready", boss_ready)
	card.set_meta("affordable", affordable)
	card.set_meta("unlock_cost", cost)
	return card


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
#  SETTINGS (paritas _draw_settings _core.py:6221-6390, kolom AUDIO)
# ══════════════════════════════════════════════════════════

## Layout 2 kolom — paritas struktur _draw_settings pygame
## (_core.py:6221-6390): KOLOM KIRI = AUDIO + CLOUD SAVE, KOLOM KANAN =
## GAMEPLAY + DANGER ZONE. Opsi yang tidak punya padanan kerja di port
## Godot (voice, game speed, language, FPS limit) sengaja TIDAK
## dipalsukan — ditulis sebagai catatan apa adanya.
func _build_settings() -> void:
	_screen_header("PENGATURAN", State.PAUSE if from_pause else State.MAIN)

	var panel := PanelContainer.new()
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_PANEL
	sb.border_color = COL_BORDER
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 36.0
	sb.content_margin_right = 36.0
	sb.content_margin_top = 18.0
	sb.content_margin_bottom = 18.0
	panel.add_theme_stylebox_override("panel", sb)
	_root.add_child(panel)

	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 36)
	panel.add_child(cols)

	# ── KOLOM KIRI: AUDIO + CLOUD SAVE ──
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 12)
	cols.add_child(left)
	left.add_child(_settings_header("AUDIO"))
	# pygame: master/sfx/bgm/voice. Port Godot punya master + sfx + bgm
	# (voice TIDAK ada — semua audio di repo pygame adalah SFX/BGM, tidak
	# ada file voice, jadi slider-nya tidak akan berfungsi dan tidak
	# dipasang).
	left.add_child(_volume_slider("Volume Master", "master", 0.7))
	left.add_child(_volume_slider("Volume SFX", "sfx", 0.6))
	left.add_child(_volume_slider("Volume Musik (BGM)", "bgm", 0.35))

	left.add_child(_settings_header("CLOUD SAVE"))
	var cloud := Label.new()
	cloud.text = "Cloud save (Play Games) belum di-port ke Godot — progres " \
		+ "disimpan di 3 SLOT LOKAL (layar PILIH SLOT). Upload/_download " \
		+ "manual tersedia di versi Pygame."
	cloud.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cloud.add_theme_font_size_override("font_size", 11)
	cloud.add_theme_color_override("font_color", COL_DIM)
	left.add_child(cloud)
	var cloud_pad := Control.new()
	cloud_pad.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(cloud_pad)

	# ── KOLOM KANAN: GAMEPLAY + PROGRESI ──
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 12)
	cols.add_child(right)
	right.add_child(_settings_header("GAMEPLAY"))

	# Difficulty: pygame menggemboknya sampai semua level selesai dan
	# menggantinya lewat settings; port Godot memutuskannya di layar PILIH
	# LEVEL (sedikit di atas grid) — tampilkan nilai aktif + arahnya.
	var diff_row := HBoxContainer.new()
	diff_row.add_theme_constant_override("separation", 10)
	var diff_label := Label.new()
	diff_label.text = "Difficulty"
	diff_label.custom_minimum_size = Vector2(200, 0)
	diff_label.add_theme_font_size_override("font_size", 14)
	diff_label.add_theme_color_override("font_color", COL_TEXT)
	diff_row.add_child(diff_label)
	var diff_val := Label.new()
	diff_val.text = "MODE: %s" % HudLayout.mode_label(GameManager.difficulty)
	diff_val.add_theme_font_size_override("font_size", 14)
	diff_val.add_theme_color_override("font_color",
		HudLayout.mode_color(GameManager.difficulty))
	diff_row.add_child(diff_val)
	right.add_child(diff_row)
	var diff_note := Label.new()
	diff_note.text = "Dipilih di layar PILIH LEVEL, sebelum match dimulai."
	diff_note.add_theme_font_size_override("font_size", 11)
	diff_note.add_theme_color_override("font_color", COL_DIM)
	right.add_child(diff_note)

	# Screen shake — paritas toggle pygame "Screen Shake"
	# (GameSettings.screen_shake_enabled); kini BENAR-BENAR berfungsi:
	# Camera2D masuk grup "camera" (Main._ready) + guard di Boss._shake.
	right.add_child(_make_toggle(
		"Screen Shake", "screen_shake", 1.0,
		func(): _show(State.SETTINGS)))
	# Damage numbers — paritas toggle pygame "Damage Numbers"; flag sudah
	# dikonsumsi WorldPopups (start_level), kini bisa diubah live.
	right.add_child(_make_toggle(
		"Damage Numbers", "damage_numbers_enabled", 1.0,
		func(): _show(State.SETTINGS)))

	var gp_pad := Control.new()
	gp_pad.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(gp_pad)

	# ── PROGRESI (paritas DANGER ZONE: RESET SAVE SLOT) ──
	right.add_child(_settings_header("PROGRESI"))
	# Hapus SLOT AKTIF (paritas tombol RESET SAVE _core.py:7012-7016)
	# lengkap dengan dialog konfirmasinya.
	right.add_child(_make_button(
		"HAPUS SAVE GAME %d" % SaveManager.get_current_slot(), COL_RED,
		_open_slot_delete_dialog.bind(SaveManager.get_current_slot()),
		Vector2(320, 36), 14))
	var note := Label.new()
	note.text = "Volume & toggle disimpan di SaveManager.data[\"settings\"] " \
		+ "per slot dan langsung berlaku."
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.add_theme_font_size_override("font_size", 11)
	note.add_theme_color_override("font_color", COL_DIM)
	right.add_child(note)


func _settings_header(text: String) -> Label:
	var h := Label.new()
	h.text = text
	h.add_theme_font_size_override("font_size", 18)
	h.add_theme_color_override("font_color", Color(0.5, 0.85, 0.95))
	return h


## Toggle tombol (paritas _draw_toggle_setting pygame): teks
## "● LABEL: AKTIF/MATIU" — status dari SaveManager settings (float 0/1).
func _make_toggle(label_text: String, key: String, default_on: float,
		refresh: Callable) -> Button:
	var on := SaveManager.get_setting(key, default_on) > 0.5
	var b := Button.new()
	b.name = "Toggle_" + key
	b.custom_minimum_size = Vector2(360, 38)
	b.add_theme_font_size_override("font_size", 14)
	var accent := COL_GREEN if on else COL_LOCKED
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(accent.r, accent.g, accent.b, 0.13)
	normal.border_color = Color(accent.r, accent.g, accent.b, 0.75)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(6)
	var hover := normal.duplicate()
	hover.bg_color = Color(accent.r, accent.g, accent.b, 0.3)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", hover)
	b.add_theme_color_override("font_color", accent)
	b.text = "●  %s: %s" % [label_text.to_upper(), "AKTIF" if on else "MATIU"]
	b.pressed.connect(func():
		var now := SaveManager.get_setting(key, default_on) > 0.5
		if key == "screen_shake":
			GameManager.set_screen_shake(not now)
		elif key == "damage_numbers_enabled":
			GameManager.set_damage_numbers(not now)
		SaveManager.set_setting(key, 0.0 if now else 1.0, true)
		AudioManager.play_sfx("ui_click", 0.5)
		refresh.call()
	)
	return b


func _volume_slider(label_text: String, key: String, default_vol: float = 0.6) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	var label := Label.new()
	label.text = label_text
	label.custom_minimum_size = Vector2(190, 0)
	label.add_theme_font_size_override("font_size", 14)
	label.add_theme_color_override("font_color", COL_TEXT)
	row.add_child(label)
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.value = SaveManager.get_setting(key, default_vol)
	slider.custom_minimum_size = Vector2(420, 24)
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var value_label := Label.new()
	value_label.text = "%d%%" % int(round(slider.value * 100.0))
	value_label.custom_minimum_size = Vector2(48, 0)
	value_label.add_theme_font_size_override("font_size", 13)
	value_label.add_theme_color_override("font_color", COL_GOLD)
	row.add_child(slider)
	row.add_child(value_label)
	# Live-apply tanpa nulis file (file ditulis saat drag selesai).
	slider.value_changed.connect(_on_volume_changed.bind(key, slider, value_label))
	slider.drag_ended.connect(_on_volume_drag_ended.bind(key, slider))
	return row


## Geser slider: terapkan ke AudioManager + label persentase, TANPA save
## (menulis file tiap langkah slider itu boros — pygame menulis settings
## saat menu ditutup).
func _on_volume_changed(_value: float, key: String, slider: HSlider,
		value_label: Label) -> void:
	SaveManager.set_setting(key, slider.value, false)
	AudioManager.apply_settings()
	value_label.text = "%d%%" % int(round(slider.value * 100.0))


## Lepas slider: satu kali tulis ke user:// (SaveManager.save()).
func _on_volume_drag_ended(_changed: bool, key: String, slider: HSlider) -> void:
	SaveManager.set_setting(key, slider.value, true)


# ══════════════════════════════════════════════════════════
#  HOW TO PLAY (paritas _draw_how_to_play _core.py:6144-6212)
# ══════════════════════════════════════════════════════════

func _build_how_to_play() -> void:
	_screen_header("CARA MAIN", State.MAIN)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_root.add_child(scroll)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(box)
	# Terjemahan bebas dari sections pygame, disesuaikan kontrol port Godot.
	var sections: Array = [
		["TUJUAN", [
			"Hancurkan Nexus (castle) Dire sebelum Nexus Radiant hancur.",
			"Menang = meta gold untuk membuka hero di HERO SHOP."]],
		["MEMBANGUN MENARA", [
			"Klik lingkaran slot kosong (+) di lane lalu bangun menara (100 gold).",
			"4 jalur: Archer / Cannon / Ice / Mage. Upgrade Lv1→Lv2 memilih jalur."]],
		["HERO & SKILL", [
			"Mulai tanpa hero. Buka B → HERO untuk membeli hero yang sudah di-unlock.",
			"Maksimal 5 hero unik. Hero mati respawn setelah 10 detik dengan level/item tetap.",
			"Klik hero Radiant untuk memilihnya, lalu Q/W/E/R untuk skill (R = ultimate).",
			"Hero yang tidak dipilih bertarung sendiri (auto-cast)."]],
		["WAVE MINION", [
			"Wave pertama setelah 5 detik. Minion keluar bertahap di ketiga lane.",
			"Wave berikutnya menunggu 25 detik dan semua minion wave lama habis."]],
		["TOKO (B)", [
			"4 tab: MENARA / ITEM / HERO / NEXUS. Item = 6 slot per hero.",
			"Upgrade nexus menaikkan HP + skala minion timmu."]],
		["PROGRESI", [
			"Menang pertama: 3000 meta gold. Replay menang: 1500 (sekali), lalu 200.",
			"Boss yang dikalahkan + castle jatuh = heronya terbuka GRATIS.",
			"ENTER setelah menang = lanjut level berikutnya (tema & boss baru)."]],
		["MODE SULIT", [
			"Hard: musuh +15% HP, +10% damage, castle Dire mulai lebih tinggi.",
			"Gold income lebih kecil (x0.75). Mudah: x1.25."]],
	]
	for section in sections:
		var head := Label.new()
		head.text = str(section[0])
		head.add_theme_font_size_override("font_size", 15)
		head.add_theme_color_override("font_color", COL_GOLD)
		box.add_child(head)
		for line in section[1]:
			var body := Label.new()
			body.text = "·  " + str(line)
			body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			body.add_theme_font_size_override("font_size", 12)
			body.add_theme_color_override("font_color", COL_TEXT)
			box.add_child(body)
		var gap := Control.new()
		gap.custom_minimum_size = Vector2(0, 10)
		box.add_child(gap)


# ══════════════════════════════════════════════════════════
#  CREDITS (paritas _draw_credits _core.py:6859-6925)
# ══════════════════════════════════════════════════════════

func _build_credits() -> void:
	_screen_header("KREDIT", State.MAIN)
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 12)
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(center)
	var credits: Array = [
		["Tower Defense Battle Arena", COL_GOLD, 24],
		["Game Design & Programming", COL_DIM, 12],
		["Dharmawan Toxi", COL_TEXT, 18],
		["Art Direction", COL_DIM, 12],
		["Dark Fantasy Vector Style", COL_TEXT, 16],
		["Sound Effects & Music", COL_DIM, 12],
		["Custom SFX Library", COL_TEXT, 16],
		["Port Godot 4", COL_DIM, 12],
		["Pygame Community  •  Python 3.10+  •  Godot 4.3", COL_TEXT, 14],
	]
	for row in credits:
		var l := Label.new()
		l.text = str(row[0])
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.add_theme_font_size_override("font_size", int(row[2]))
		l.add_theme_color_override("font_color", row[1])
		center.add_child(l)


# ══════════════════════════════════════════════════════════
#  PAUSE (paritas _draw_pause_menu _core.py:6930-7000)
# ══════════════════════════════════════════════════════════

func _build_pause() -> void:
	# Panel 400x400 terpusat (paritas geometri pause pygame) — anak LANGSUNG
	# MainMenu (Control biasa, BUKAN container) dengan posisi/ukuran eksplisit:
	# di dalam VBox _root/_bg geometrinya dikendalikan layout (bug: rect jadi
	# (44,18,400,408) — margin backdrop + tinggi konten).
	var panel := PanelContainer.new()
	panel.name = "PausePanel"
	panel.position = HudLayout.PAUSE_PANEL_POS
	panel.size = HudLayout.PAUSE_PANEL_SIZE
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_PANEL
	sb.border_color = COL_BORDER
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(12)
	sb.content_margin_left = 20.0
	sb.content_margin_right = 20.0
	sb.content_margin_top = 16.0
	sb.content_margin_bottom = 16.0
	panel.add_theme_stylebox_override("panel", sb)
	add_child(panel)
	_pause_panel = panel

	var inner := VBoxContainer.new()
	inner.alignment = BoxContainer.ALIGNMENT_CENTER
	# separation 7 (bukan 10): minimum gabungan konten + margin stylebox
	# harus <= 400, kalau tidak Control.size dijepit naik ke minimum
	# (bug: panel jadi 400x408). 5 gap x 3px = 15px dihemat -> min ~393.
	inner.add_theme_constant_override("separation", 7)
	panel.add_child(inner)

	var title := Label.new()
	title.text = "PAUSED"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 46)
	title.add_theme_color_override("font_color", COL_GOLD)
	inner.add_child(title)

	# badge difficulty (paritas mode badge 6949-6960)
	var mode := Label.new()
	mode.name = "PauseMode"
	mode.text = "MODE: %s  ·  LEVEL %d  ·  WAVE %d" % [
		HudLayout.mode_label(GameManager.difficulty), GameManager.level_number,
		GameManager.wave_number]
	mode.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mode.add_theme_font_size_override("font_size", 14)
	mode.add_theme_color_override("font_color",
		HudLayout.mode_color(GameManager.difficulty))
	inner.add_child(mode)

	# Urutan paritas PAUSE_BUTTON_ORDER; label Indonesia disengaja (MainMenu
	# Godot berbahasa Indonesia); ukuran 300x48 = pygame.
	var buttons: Array = [
		["PauseResume", "LANJUT MAIN (RESUME)", COL_GREEN, _do_resume],
		["PauseSettings", "PENGATURAN", Color(0.85, 0.75, 0.45), _show.bind(State.SETTINGS)],
		["PauseMenu", "MENU UTAMA", COL_BLUE, _do_main_menu],
		["PauseQuit", "KELUAR GAME", COL_RED, func(): get_tree().quit()],
	]
	for pair in buttons:
		var b := _make_button(str(pair[1]), pair[2], pair[3],
			HudLayout.PAUSE_BUTTON_SIZE, 15)
		b.name = str(pair[0])
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		inner.add_child(b)


# ══════════════════════════════════════════════════════════
#  WIDGET HELPER
# ══════════════════════════════════════════════════════════

## Tombol dengan aksen warna pygame-style (tiap tombol menu punya warna
## sendiri di _draw_main_menu). Klik -> SFX ui_click (paritas SoundManager).
func _make_button(label_text: String, accent: Color, handler: Callable,
		min_size: Vector2 = Vector2(0, 34), font_size: int = 14) -> Button:
	var b := Button.new()
	b.text = label_text
	b.custom_minimum_size = min_size
	b.add_theme_font_size_override("font_size", font_size)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(accent.r, accent.g, accent.b, 0.13)
	normal.border_color = Color(accent.r, accent.g, accent.b, 0.75)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(6)
	normal.content_margin_left = 12.0
	normal.content_margin_right = 12.0
	var hover := normal.duplicate()
	hover.bg_color = Color(accent.r, accent.g, accent.b, 0.3)
	var pressed := normal.duplicate()
	pressed.bg_color = Color(accent.r, accent.g, accent.b, 0.42)
	var disabled := normal.duplicate()
	disabled.bg_color = Color(0.08, 0.09, 0.13, 0.7)
	disabled.border_color = Color(0.3, 0.32, 0.4, 0.6)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("disabled", disabled)
	b.add_theme_color_override("font_color", accent)
	b.add_theme_color_override("font_hover_color", accent.lightened(0.25))
	b.add_theme_color_override("font_pressed_color", accent.lightened(0.1))
	b.add_theme_color_override("font_disabled_color", Color(0.45, 0.47, 0.55))
	# Dua koneksi terpisah: SFX ui_click selalu bunyi dulu, lalu aksinya
	# (paritas SoundManager().play('ui_click') di setiap handler menu pygame).
	if handler.is_valid():
		b.pressed.connect(AudioManager.play_sfx.bind("ui_click", 0.5))
		b.pressed.connect(handler)
	return b
