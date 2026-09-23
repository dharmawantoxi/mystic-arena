# MainMenu.gd — Menu utama + sub-menu, dibangun 100% dari kode.
#
# Port state machine `class MenuState` pygame (_core.py:3097-3105):
#   MAIN · SLOT_SELECT · LEVEL_SELECT · HERO_SHOP · SETTINGS · HOW_TO_PLAY ·
#   CREDITS · PAUSE
# Visual = port ui_theme + _draw_* pygame 1:1 (MenuBackground animasi,
# ScreenTitle Cinzel, Flourish, PygameButton/PygamePanel, chip, tab, pill,
# toggle, slider emas). Geometri + gaya = pygame.
#
# BAHASA (permintaan user 2026-09-13: "saat ganti ke English semuanya
# Inggris, starting dari main menu"): SEMUA label layar dibangun lewat
# `_loc(kunci)` -> MysticLocalization, dan `GameManager.language_changed`
# memicu `_show(state)` ulang. Teks yang SUDAH Inggris di kedua bahasa (merek
# "MYSTIC ARENA"/"v2.0 • MOBA Tower Defense", badge "LV. %d"/"TRUE BOSS", tab
# "STARTER HEROES"/"MINI BOSS", judul "HERO SHOP"/"TOP UP") sengaja tanpa
# kunci — tidak ada yang bisa diterjemahkan. Karena nilai "id" tabel = string
# yang dulu di-hardcode di sini, pemain Indonesia tidak melihat perubahan.
# Audit closed-world tools/test_godot_localization_parity.py menjaga tiap
# `_loc("kunci")` nyata ada di tabel.
#
# Sinyal keluar (dipasang Main.gd):
#   play_requested(level_num) — LEVEL_SELECT/CONTINUE -> mulai match
#   resume_requested          — PAUSE -> lanjut main
#   main_menu_requested       — PAUSE/victory -> buang match, balik MAIN
# Difficulty diubah langsung lewat GameManager.set_difficulty() (paritas
# toggle_level_difficulty), pembelian hero lewat SaveManager (paritas
# _unlock_hero_in_meta_shop _core.py:5298-5328).
extends Control

signal play_requested(level_num: int)
signal resume_requested
signal main_menu_requested
## Dipancarkan tiap kali menu dibuka/ditutup/diganti state — Main.gd
## menyembunyikan arena+HUD selama menu non-PAUSE menutupi layar penuh
## (layar berantakan "menu di samping arena" tidak boleh bisa terjadi),
## dan menampilkan arena beku di belakang dim selama PAUSE (paritas
## pygame: pause = frame game beku + overlay gelap + panel).
signal menu_coverage_changed(covers: bool, is_pause: bool)

## Satu-satunya pintu teks menu: kunci tabel -> string bahasa aktif.
## Pintasan `_loc` (pola ShopPanel/SkillBar/HUD/GameOverOverlay) dipakai di
## SEMUA layar supaya tidak ada satu pun label Indonesia yang tersisa di
## berkas ini — audit `tools/test_godot_localization_parity.py` menjaga tiap
## `_loc("kunci")` benar-benar ada di tabel, dan gate bahasa di
## LocalizationParityTest memastikan layar Inggris tidak menyisakan teks
## Indonesia.
func _loc(key: String) -> String:
	return MysticLocalization.tr_text(key)


func _on_language_changed(_language: String) -> void:
	if is_inside_tree() and visible:
		_show(state)


## Paritas MenuState _core.py:3099-3105 — SEMUA state termasuk SLOT_SELECT
## (FASE 21: multi-slot save + migrasi legacy sudah diport).
enum State { MAIN, SLOT_SELECT, LEVEL_SELECT, HERO_SHOP, SETTINGS, HOW_TO_PLAY, CREDITS, PAUSE }

## Layar menu non-PAUSE = LAYAR PENUH opak total (arena di belakangnya
## disembunyikan Main.gd — alpha 1.0 jadi tidak ada celah transparansi).
const COL_BG := Color(0.031, 0.033, 0.058, 1.0)
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
## 3 kartu per baris — paritas grid HERO SHOP pygame (gap 15/12; kartu
## 380x145 di pygame, HERO_CARD_W x 145 di Godot — lihat catatan di bawah).
const HERO_COLUMNS := 3
## Lebar kartu hero shop: pygame 380px, di Godot 366px supaya 3 kolom +
## 2 gap 15px + scrollbar vertikal 12px SELALU muat di konten panel 1148px
## (3*366 + 2*15 = 1128 <= 1148 - 12). Dengan 380px (3*380 + 2*15 = 1170)
## grid sudah 22px lebih lebar dari panel, dan tab MINI/TRUE yang panjang
## selalu memunculkan scrollbar sehingga kolom kanan terpotong tepat di
## kedua tab itu. Tinggi tetap 145 paritas pygame.
const HERO_CARD_W := 366.0
const HERO_CARD_H := 145.0
## Lebar kolom info tengah kartu = kartu - margin(12+12) - potret(78) -
## separasi row(10+10) - kolom tombol(104). SEMUA teks kartu (nama, judul,
## chip role+sekolah, status) wajib di-fit ke lebar ini — paritas
## max_info_w _core.py:5113. Role boss panjang ("TRUE BOSS/SPECTRAL CHAIN
## WARDEN") kalau tidak di-fit meluber menabrak tombol kanan.
const HERO_INFO_W := HERO_CARD_W - 226.0

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
var _menubg: MenuBackground = null
var _margin: MarginContainer = null
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


## FASE 24 — lapisan gamepad (paritas `menu.controller_mgr` pygame yang
## dipasang main_desktop_legacy.py:59). Diisi Main._ready.
var controller_mgr = null
## Label INPUT kiri-bawah (paritas _input_label _core.py:3834-3843).
var _input_label_node: Label = null


func _ready() -> void:
	name = "MainMenu"
	add_to_group("main_menu")
	# Bahasa berganti (SETTINGS/pause) -> layar yang sedang tampil dibangun
	# ulang, karena seluruh teks menu sekarang dibaca lewat tabel
	# MysticLocalization (permintaan user: English = SEMUA layar Inggris).
	# pygame tidak butuh sinyal ini (menggambar ulang tiap frame), Godot
	# membangun Control sekali per layar — pola yang sama dengan
	# ShopPanel/SkillBar/HUD/GameOverOverlay.
	GameManager.language_changed.connect(_on_language_changed)
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
	# Margin konten NOL: background animasi harus menutup seluruh layar
	# sampai tepi (margin konten dulu 44/18 — sekarang dipegang
	# MarginContainer di bawah supaya MenuBackground full-bleed).
	sb.content_margin_left = 0.0
	sb.content_margin_right = 0.0
	sb.content_margin_top = 0.0
	sb.content_margin_bottom = 0.0
	_bg_style = sb
	_bg.add_theme_stylebox_override("panel", sb)
	add_child(_bg)
	# Latar menu animasi pygame (langit malam + nebula + portal + lane).
	# PanelContainer menumpuk SEMUA anak seluas penuh — background di bawah,
	# konten di atasnya.
	_menubg = MenuBackground.new()
	_bg.add_child(_menubg)
	_margin = MarginContainer.new()
	_margin.name = "ContentMargin"
	_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_margin.add_theme_constant_override("margin_left", 44)
	_margin.add_theme_constant_override("margin_right", 44)
	_margin.add_theme_constant_override("margin_top", 18)
	_margin.add_theme_constant_override("margin_bottom", 14)
	_bg.add_child(_margin)


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
	# PAUSE = arena beku di belakang dim — background menu disembunyikan.
	if _menubg != null:
		_menubg.visible = new_state != State.PAUSE
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
	_root.add_theme_constant_override("separation", 6)
	_root.mouse_filter = Control.MOUSE_FILTER_PASS
	_margin.add_child(_root)
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


## Judul layar (paritas ui_theme.screen_title: Cinzel 64 + glow) + ornamen
## opsional. Tombol BACK pygame selalu di bawah-tengah (back_button) —
## dipasang per layar via _add_back_button() di AKHIR build.
func _screen_header(title: String, ornament: bool = false) -> void:
	var t := ScreenTitle.new(title, 64, true)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_root.add_child(t)
	if ornament:
		var f := Flourish.new()
		f.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_root.add_child(f)


## Tombol BACK bawah-tengah (paritas ui_theme.back_button: 200x42 netral +
## ikon panah).
func _add_back_button(back_to: int) -> void:
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(row)
	var b := PygameButton.pill_button(_loc("menu_back"), "neutral", "back",
		200, 42, 20)
	b.pressed.connect(_show.bind(back_to))
	# SFX ui_click sudah otomatis dari PygameButton.
	row.add_child(b)


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
#  MAIN (paritas _draw_main_menu _core.py:4698-4800)
# ══════════════════════════════════════════════════════════

func _build_main() -> void:
	# Spacer atas: judul jatuh di y~124 seperti pygame.
	var spacer_top := Control.new()
	spacer_top.custom_minimum_size = Vector2(0, 30)
	spacer_top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(spacer_top)

	# ── judul MYSTIC ARENA (Cinzel 72 + glow denyut + bob ±3px) ──
	var title := ScreenTitle.new("MYSTIC ARENA", 72, true, true)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_root.add_child(title)

	# ── subtitle plate (letter BATTLE ARENA 32 + padding 60/48) ──
	var plate_row := HBoxContainer.new()
	plate_row.alignment = BoxContainer.ALIGNMENT_CENTER
	plate_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(plate_row)
	var plate := PygamePanel.new(UiTheme.EDGE_GOLD, 1.0, 10.0)
	plate.set_margins(30, 8, 30, 8)
	plate.show_ticks = false
	plate_row.add_child(plate)
	var sub := Label.new()
	UiTheme.style_label(sub, UiTheme.letter("BATTLE ARENA"),
		UiTheme.body_semibold(), 32, Color(150.0 / 255.0, 195.0 / 255.0, 1.0),
		HORIZONTAL_ALIGNMENT_CENTER)
	plate.add_child(sub)

	var tag := Label.new()
	UiTheme.style_label(tag, "Dark Fantasy MOBA  •  Tower Defense",
		UiTheme.body_medium(), 22, UiTheme.TEXT_DIM,
		HORIZONTAL_ALIGNMENT_CENTER)
	_root.add_child(tag)

	var f := Flourish.new()
	f.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_root.add_child(f)

	# ── tombol: LANJUTKAN + MULAI GAME sejajar (paritas CONTINUE/PLAY GAME,
	# 2x 300x50, tengah di cx±170 = gap 40) ──
	var cont := GameManager.next_level_number(_highest_completed())
	if cont <= 0 and GameManager.level_count() > 0:
		cont = int(SaveManager.data.get("last_played_level", 1))
	cont = maxi(cont, 1) # data level belum ada -> mulai dari 1, jangan "LEVEL 0"
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 40)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(row)
	# Paritas _on_button_click "play" _core.py:7022-7023: MULAI GAME lewat
	# layar PILIH SLOT dulu (slot aktif ditentukan di situ). LANJUTKAN
	# mem-bypass slot select seperti pygame.
	row.add_child(_make_button(_loc("menu_continue") % cont,
		Color(140.0 / 255.0, 225.0 / 255.0, 1.0),
		func(): _request_play(cont), Vector2(300, 50), 22, "continue"))
	row.add_child(_make_button(_loc("menu_play"),
		Color(100.0 / 255.0, 220.0 / 255.0, 110.0 / 255.0),
		_show.bind(State.SLOT_SELECT), Vector2(300, 50), 22, "play"))

	# ── tumpukan tombol 360x50 gap 53 (paritas buttons_data pygame) ──
	var buttons: Array = [
		["HERO SHOP", Color(1.0, 220.0 / 255.0, 100.0 / 255.0), _show.bind(State.HERO_SHOP), "coin"],
		# Paritas tombol "input_select" (_core.py:4774 + :7025-7037): toggle
		# keyboard <-> controller, rescan kalau belum terdeteksi.
		["INPUT", Color(100.0 / 255.0, 200.0 / 255.0, 220.0 / 255.0),
			_toggle_input_mode, "pad"],
		[_loc("menu_how_to_play"), Color(110.0 / 255.0, 180.0 / 255.0, 1.0), _show.bind(State.HOW_TO_PLAY), "help"],
		[_loc("menu_settings"), Color(205.0 / 255.0, 180.0 / 255.0, 105.0 / 255.0), _show.bind(State.SETTINGS), "gear"],
		[_loc("menu_credits"), Color(200.0 / 255.0, 130.0 / 255.0, 210.0 / 255.0), _show.bind(State.CREDITS), "star"],
		[_loc("menu_quit"), Color(225.0 / 255.0, 90.0 / 255.0, 90.0 / 255.0), _open_exit_confirm, "quit"],
	]
	var stack := VBoxContainer.new()
	stack.alignment = BoxContainer.ALIGNMENT_CENTER
	stack.add_theme_constant_override("separation", 3)
	stack.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(stack)
	for pair in buttons:
		var b := _make_button(str(pair[0]), pair[1], pair[2],
			Vector2(360, 50), 19, str(pair[3]))
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		stack.add_child(b)

	var spacer_bottom := Control.new()
	spacer_bottom.size_flags_vertical = Control.SIZE_EXPAND_FILL
	spacer_bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(spacer_bottom)
	var meta := SaveManager.meta_gold()
	var info := Label.new()
	UiTheme.style_label(info,
		_loc("menu_meta_summary") % [
			meta, _completed_count(), GameManager.level_count(),
			(SaveManager.data.get("unlocked_heroes", []) as Array).size()],
		UiTheme.body_regular(), 12, UiTheme.TEXT_DIM,
		HORIZONTAL_ALIGNMENT_CENTER)
	_root.add_child(info)
	# Footer pygame: label input kiri-bawah + versi tengah-bawah.
	var foot := HBoxContainer.new()
	foot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(foot)
	var input_lab := Label.new()
	UiTheme.style_label(input_lab, _input_mode_text(),
		UiTheme.body_regular(), 15, Color(110.0 / 255.0, 200.0 / 255.0, 210.0 / 255.0))
	_input_label_node = input_lab
	foot.add_child(input_lab)
	var version := Label.new()
	UiTheme.style_label(version, "v2.0  •  MOBA Tower Defense",
		UiTheme.body_regular(), 15, UiTheme.TEXT_FAINT,
		HORIZONTAL_ALIGNMENT_CENTER)
	version.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(version)
	var pad := Control.new()
	pad.custom_minimum_size = Vector2(190, 0)
	pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	foot.add_child(pad)


## Paritas Menu._toggle_input_mode / cabang "input_select"
## (_core.py:7025-7037, :7630-7647): mode controller -> keyboard; kalau
## belum ada controller, rescan dulu (debug_print pygame = log [CONTROLLER]).
func _toggle_input_mode() -> void:
	if controller_mgr == null or not is_instance_valid(controller_mgr):
		print("[INPUT] No controller layer")
		return
	if not controller_mgr.is_controller_mode() and not controller_mgr.connected:
		controller_mgr.rescan()
		if controller_mgr.connected:
			controller_mgr.debug_print()
	controller_mgr.toggle_input_mode()
	_refresh_input_label()


## Paritas Menu.draw _core.py:3834-3843 (build Android pygame menulis
## "INPUT: TOUCHSCREEN" karena main.py tidak memasang controller_mgr).
func _input_mode_text() -> String:
	if controller_mgr != null and is_instance_valid(controller_mgr):
		return controller_mgr.input_mode_label()
	return "INPUT: KEYBOARD + MOUSE"


func _refresh_input_label() -> void:
	if _input_label_node != null and is_instance_valid(_input_label_node):
		_input_label_node.text = _input_mode_text()


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
	_confirm = PygamePanel.new(COL_RED, 2.0, 10.0)
	_confirm.name = "ExitConfirm"
	# PRESET_CENTER dengan mode MINSIZE: dialog seukuran kontennya, persis
	# di tengah layar (set_anchors_preset saja meninggalkan offset 0 -> pojok).
	_confirm.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_confirm.mouse_filter = Control.MOUSE_FILTER_STOP
	_confirm.configure(Color(0.13, 0.08, 0.1), Color(0.07, 0.05, 0.07),
		COL_RED, 2.0, 10.0, true, true)
	_confirm.set_margins(18, 12, 18, 12)
	add_child(_confirm)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	_confirm.add_child(box)
	var q := Label.new()
	UiTheme.style_label(q, _loc("menu_exit_question"),
		UiTheme.body_semibold(), 17, UiTheme.TEXT_WHITE,
		HORIZONTAL_ALIGNMENT_CENTER)
	box.add_child(q)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	box.add_child(row)
	var yes := PygameButton.pill_button(_loc("menu_exit_yes"), "danger", "", 140, 32)
	yes.pressed.connect(func(): get_tree().quit())
	row.add_child(yes)
	var no := PygameButton.pill_button(_loc("menu_cancel"), "success", "", 140, 32)
	no.pressed.connect(func(): _confirm.visible = false)
	row.add_child(no)


# ══════════════════════════════════════════════════════════
#  SLOT_SELECT (paritas _draw_slot_select _core.py:3217-3262)
# ══════════════════════════════════════════════════════════

func _build_slot_select() -> void:
	_screen_header(_loc("slot_title"))
	var sub := Label.new()
	UiTheme.style_label(sub, _loc("slot_subtitle"),
		UiTheme.body_medium(), 20, UiTheme.TEXT_BODY,
		HORIZONTAL_ALIGNMENT_CENTER)
	_root.add_child(sub)

	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", SLOT_CARD_GAP)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(row)
	for i in range(1, SaveManager.NUM_SLOTS + 1):
		var card := _slot_card(i)
		# Kartu 460px di tengah area sisa (paritas start_y=170 pygame).
		card.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(card)

	_add_back_button(State.MAIN)

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

	var card := PygamePanel.new()
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
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.hoverable = true
	if is_empty:
		card.configure(UiTheme.OPEN_BG_TOP, UiTheme.OPEN_BG_BOTTOM,
			UiTheme.OPEN_EDGE, 2.0, 12.0, false, true)
	else:
		card.configure(UiTheme.PANEL_TOP, UiTheme.PANEL_BOTTOM,
			UiTheme.EDGE_GOLD, 2.0, 12.0, true, true)
	card.set_margins(16, 12, 16, 14)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(box)

	var tag := Label.new()
	UiTheme.style_label(tag, UiTheme.letter("SAVE GAME"),
		UiTheme.body_semibold(), 18,
		UiTheme.TEXT_DIM if is_empty else UiTheme.GOLD_TEXT,
		HORIZONTAL_ALIGNMENT_CENTER)
	box.add_child(tag)
	var num := Label.new()
	UiTheme.style_label(num, str(slot_num), UiTheme.body_bold(), 58,
		UiTheme.TEXT_FAINT if is_empty else UiTheme.GOLD_BRIGHT,
		HORIZONTAL_ALIGNMENT_CENTER)
	if not is_empty:
		num.add_theme_color_override("font_outline_color",
			Color(0.1, 0.06, 0.02))
		num.add_theme_constant_override("outline_size", 6)
	box.add_child(num)
	var sep := HSeparator.new()
	sep.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_separator(sep, Color(52.0 / 255.0, 58.0 / 255.0, 84.0 / 255.0))
	box.add_child(sep)

	if is_empty:
		# Lingkaran plus tema.
		var circ_row := HBoxContainer.new()
		circ_row.alignment = BoxContainer.ALIGNMENT_CENTER
		circ_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(circ_row)
		var circ := PanelContainer.new()
		circ.custom_minimum_size = Vector2(60, 60)
		circ.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var csb := StyleBoxFlat.new()
		csb.bg_color = UiTheme.PANEL_FILL
		csb.border_color = UiTheme.OPEN_EDGE
		csb.set_border_width_all(2)
		csb.set_corner_radius_all(30)
		circ.add_theme_stylebox_override("panel", csb)
		circ_row.add_child(circ)
		var plus := VectorIcon.new("plus", UiTheme.CYAN_SOFT, 1.5)
		plus.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		plus.size_flags_vertical = Control.SIZE_EXPAND_FILL
		circ.add_child(plus)
		var empty := Label.new()
		UiTheme.style_label(empty, UiTheme.letter(_loc("slot_empty")),
			UiTheme.body_semibold(), 28, UiTheme.SLATE,
			HORIZONTAL_ALIGNMENT_CENTER)
		box.add_child(empty)
		var hint := Label.new()
		UiTheme.style_label(hint, _loc("slot_empty_hint"),
			UiTheme.body_medium(), 16, UiTheme.TEXT_DIM,
			HORIZONTAL_ALIGNMENT_CENTER)
		box.add_child(hint)
	else:
		if highest > 0:
			box.add_child(_slot_line(UiTheme.letter(_loc("slot_highest")),
				UiTheme.TEXT_DIM, 13))
			var lv_big := Label.new()
			UiTheme.style_label(lv_big, "LV. %d" % highest,
				UiTheme.body_bold(), 30, UiTheme.GOLD_BRIGHT,
				HORIZONTAL_ALIGNMENT_CENTER)
			box.add_child(lv_big)
			box.add_child(_slot_line(UiTheme.fit_ellipsis(
				UiTheme.body_medium(), 17, level_name, SLOT_CARD_W - 40),
				UiTheme.TEXT_BODY, 17))
		else:
			box.add_child(_slot_line(_loc("slot_no_levels"),
				UiTheme.TEXT_DIM, 16))
		box.add_child(_icon_line("coin", UiTheme.GOLD,
			"%s Gold" % _format_grouped(gold), UiTheme.GOLD_TEXT, 20, 0.8))
		box.add_child(_icon_line("swords", UiTheme.CYAN_SOFT,
			"Hero: %d" % heroes, UiTheme.CYAN_SOFT, 16, 0.6))
		box.add_child(_icon_line("skull", Color(1.0, 150.0 / 255.0, 150.0 / 255.0),
			"Boss: %d" % bosses, Color(1.0, 150.0 / 255.0, 150.0 / 255.0),
			16, 0.6))
		box.add_child(_slot_line(UiTheme.letter(_loc("slot_last_played")),
			UiTheme.TEXT_DIM, 13))
		box.add_child(_slot_line(last_played, UiTheme.TEXT_BODY, 17))

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(spacer)

	# ── tombol aksi (paritas pill CONTINUE/START NEW GAME + DELETE SAVE) ──
	var play_label := _loc("slot_start_new") if is_empty \
		else _loc("slot_continue")
	card.set_meta("play_label", play_label)
	var play_btn := PygameButton.pill_button(play_label,
		"cyan" if is_empty else "success", "play", 280, 40, 20)
	play_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	play_btn.pressed.connect(_on_slot_select.bind(slot_num))
	box.add_child(play_btn)
	if not is_empty:
		card.set_meta("delete_label", _loc("slot_delete"))
		var del_btn := PygameButton.pill_button(_loc("slot_delete"), "danger",
			"quit", 280, 30, 16)
		del_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		del_btn.pressed.connect(_open_slot_delete_dialog.bind(slot_num))
		box.add_child(del_btn)
	else:
		card.set_meta("delete_label", "")
	card.set_meta("has_delete", not is_empty)
	return card


## Satu baris teks kartu slot.
func _slot_line(text: String, color: Color, font_size: int) -> Label:
	var lab := Label.new()
	UiTheme.style_label(lab, text, UiTheme.body_medium(), font_size,
		color, HORIZONTAL_ALIGNMENT_CENTER)
	return lab


## Satu baris ikon + teks (rata tengah) untuk kartu slot.
func _icon_line(icon_name: String, icon_color: Color, text: String,
		color: Color, font_size: int, icon_scale: float) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var icon := VectorIcon.new(icon_name, icon_color, icon_scale)
	row.add_child(icon)
	var lab := Label.new()
	UiTheme.style_label(lab, text, UiTheme.body_semibold(), font_size,
		color)
	row.add_child(lab)
	return row


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
	_confirm = PygamePanel.new(COL_RED, 3.0, 12.0)
	_confirm.name = "SlotDeleteConfirm"
	_confirm.set_meta("slot_delete", slot_num)
	_confirm.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_confirm.mouse_filter = Control.MOUSE_FILTER_STOP
	_confirm.configure(Color(0.16, 0.1, 0.12), Color(0.09, 0.06, 0.08),
		COL_RED, 3.0, 12.0, true, true)
	_confirm.set_margins(24, 16, 24, 16)
	add_child(_confirm)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	_confirm.add_child(box)
	# Judul + ikon warn vektor.
	var head := HBoxContainer.new()
	head.alignment = BoxContainer.ALIGNMENT_CENTER
	head.add_theme_constant_override("separation", 10)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(head)
	head.add_child(VectorIcon.new("warn", COL_RED, 1.1))
	var title := Label.new()
	UiTheme.style_label(title, _loc("slot_delete_title"), UiTheme.body_bold(), 24,
		COL_RED)
	box.add_child(title)
	var msg := Label.new()
	UiTheme.style_label(msg, _loc("slot_delete_question") % slot_num,
		UiTheme.body_semibold(), 20, UiTheme.TEXT_WHITE,
		HORIZONTAL_ALIGNMENT_CENTER)
	box.add_child(msg)
	var warn := Label.new()
	UiTheme.style_label(warn, _loc("slot_delete_warning"),
		UiTheme.body_medium(), 16, Color(0.86, 0.7, 0.7),
		HORIZONTAL_ALIGNMENT_CENTER)
	box.add_child(warn)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(row)
	var yes := PygameButton.pill_button(_loc("slot_delete_yes"), "danger", "", 160, 36)
	yes.pressed.connect(_on_slot_delete_confirm.bind(true))
	row.add_child(yes)
	var no := PygameButton.pill_button(_loc("menu_cancel"), "success", "", 160, 36)
	no.pressed.connect(_on_slot_delete_confirm.bind(false))
	row.add_child(no)


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
	_screen_header(_loc("lvl_title"))

	# ── pemilih difficulty (3 tab: paritas MODE EASY/NORMAL/HARD) ──
	var diff_row := HBoxContainer.new()
	diff_row.alignment = BoxContainer.ALIGNMENT_CENTER
	diff_row.add_theme_constant_override("separation", 10)
	diff_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(diff_row)
	var group := ButtonGroup.new()
	for d in [["easy", _loc("lvl_diff_easy"), Color(0.4, 0.85, 1.0)],
			["normal", _loc("lvl_diff_normal"), COL_GREEN],
			["hard", _loc("lvl_diff_hard"), COL_RED]]:
		var mode := str(d[0])
		var b := PygameButton.tab_button(str(d[1]), d[2], 150, 34, 18)
		b.button_group = group
		b.set_pressed_no_signal(GameManager.difficulty == mode)
		b.pressed.connect(GameManager.set_difficulty.bind(mode))
		diff_row.add_child(b)

	# ── progres (paritas "COMPLETED: x / total" + progress bar 3988-3996) ──
	var done := _completed_count()
	var total := GameManager.level_count()
	var prog := Label.new()
	UiTheme.style_label(prog,
		_loc("lvl_progress") % [done, total],
		UiTheme.body_semibold(), 18, Color(0.5, 0.85, 0.95),
		HORIZONTAL_ALIGNMENT_CENTER)
	_root.add_child(prog)
	var bar_row := HBoxContainer.new()
	bar_row.alignment = BoxContainer.ALIGNMENT_CENTER
	bar_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(bar_row)
	var bar := ProgressBar.new()
	bar.max_value = maxf(1.0, float(total))
	bar.value = float(done)
	bar.custom_minimum_size = Vector2(300, 8)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_progress_bar(bar, UiTheme.GREEN,
		Color(0.1, 0.12, 0.18), 4)
	bar_row.add_child(bar)

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
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scroll.add_child(grid)
	for lv_data in BossDB.levels:
		if lv_data is Dictionary:
			grid.add_child(_level_card(lv_data))
	if BossDB.levels.is_empty():
		# levels.json belum ada/belum dikonversi — layar level select harus
		# menjelaskan, bukan hening.
		var warn := Label.new()
		UiTheme.style_label(warn,
			_loc("lvl_json_missing"),
			UiTheme.body_medium(), 14, COL_RED)
		grid.add_child(warn)

	_add_back_button(State.MAIN)


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
	cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lab := Label.new()
	UiTheme.style_label(lab, label, UiTheme.body_semibold(), 10,
		COL_STAT_LABEL)
	cell.add_child(lab)
	var val := Label.new()
	UiTheme.style_label(val, value, UiTheme.body_bold(), 16, color)
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

	var card := PygamePanel.new()
	card.set_meta("level_num", level_num)
	# 3 kolom x 380 + 2 x 14 gap = 1148 px — muat di 1192 px area konten
	# (1280 - margin backdrop 88), tanpa scroll horizontal.
	card.custom_minimum_size = Vector2(380, 158)
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.hoverable = unlocked
	# gradasi per status (paritas LOCKED/DONE/OPEN_BG_TOP)
	if not unlocked:
		card.configure(UiTheme.LOCKED_BG_TOP, UiTheme.LOCKED_BG_BOTTOM,
			UiTheme.LOCKED_EDGE, 2.0, 10.0, false, true)
	elif completed:
		card.configure(UiTheme.DONE_BG_TOP, UiTheme.DONE_BG_BOTTOM,
			UiTheme.DONE_EDGE, 2.0, 10.0, true, true)
	else:
		card.configure(UiTheme.OPEN_BG_TOP, UiTheme.OPEN_BG_BOTTOM,
			UiTheme.OPEN_EDGE, 2.0, 10.0, false, true)
	card.set_margins(12, 8, 12, 8)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(box)

	# ── baris 1: LEVEL n + badge status ──
	var head := HBoxContainer.new()
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(head)
	var title := Label.new()
	UiTheme.style_label(title, "LEVEL %d" % level_num,
		UiTheme.body_bold(), 15,
		UiTheme.GOLD_TEXT if unlocked else COL_LOCKED)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	# Badge status + ikon vektor (paritas badge DONE pygame).
	var badge_row := HBoxContainer.new()
	badge_row.add_theme_constant_override("separation", 4)
	badge_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(badge_row)
	var badge := Label.new()
	if completed:
		badge_row.add_child(VectorIcon.new("check",
			Color(0.55, 0.95, 0.7), 0.55))
		UiTheme.style_label(badge, _loc("lvl_badge_done"), UiTheme.body_bold(), 11,
			Color(0.55, 0.95, 0.7))
	elif not unlocked:
		badge_row.add_child(VectorIcon.new("lock", COL_LOCKED, 0.55))
		UiTheme.style_label(badge, _loc("lvl_badge_locked"), UiTheme.body_bold(), 11,
			COL_LOCKED)
	else:
		badge_row.add_child(VectorIcon.new("play", COL_GREEN, 0.55))
		UiTheme.style_label(badge, _loc("lvl_badge_ready"), UiTheme.body_bold(), 11,
			COL_GREEN)
	badge_row.add_child(badge)

	# ── baris 2: nama + deskripsi ──
	var name_l := Label.new()
	UiTheme.style_label(name_l,
		str(lv.get("name", "Level %d" % level_num)),
		UiTheme.body_semibold(), 17,
		UiTheme.TEXT_WHITE if unlocked else Color(0.55, 0.58, 0.68))
	box.add_child(name_l)
	var desc := Label.new()
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(desc, str(lv.get("description", "")),
		UiTheme.body_medium(), 11, COL_DIM)
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
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(info, _loc("lvl_theme_line") % [
		str(lv.get("map_theme", "forest")).to_upper(),
		", ".join(minis) if not minis.is_empty() else "-",
		true_name if not true_name.is_empty() else "-"],
		UiTheme.body_medium(), 11, Color(0.95, 0.62, 0.62))
	box.add_child(info)

	# ── baris 3.5a: difficulty + 5 pip (paritas info kartu pygame) ──
	if unlocked:
		box.add_child(_diff_pip_row(lv))

	# ── baris 3.5b: blok stat (FASE 20 — paritas _core.py:4247-4291) ──
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
			grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
			box.add_child(grid)
			var wins := int(stats.get("wins", 0))
			var wr := _level_win_rate(wins, attempts)
			# Slot skor (kolom 1): label + nilai warna GOLD_TEXT.
			# Truncasi diukur pada px SETARA pygame (20/19 — val_font_bold/
			# val_font _core.py:4262-4263) meski render lebih kecil, agar
			# rasio string terhadap ambang 120px pygame dipertahankan.
			grid.add_child(_stat_cell(_loc("lvl_stat_score"),
				_fit_stat_text(_format_level_score(int(
					stats.get("best_score", 0))), 20),
				COL_STAT_SCORE, "score"))
			# Slot waktu (kolom 2): label + nilai warna CYAN_SOFT.
			grid.add_child(_stat_cell(_loc("lvl_stat_time"),
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
			UiTheme.style_label(empty, _loc("lvl_stat_none"),
				UiTheme.body_medium(), 11, COL_STAT_LABEL)
			box.add_child(empty)

	# ── baris 4: aksi ──
	if unlocked:
		var label := _loc("lvl_play") if not completed else _loc("lvl_replay")
		var btn := PygameButton.pill_button(label, "success", "play",
			0, 30, 18)
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		btn.pressed.connect(_request_play.bind(level_num))
		box.add_child(btn)
	else:
		# paritas teks kunci _core.py:4303 "Complete Level X first"
		var lock := Label.new()
		var req := int(lv.get("unlock_after_level", 0))
		UiTheme.style_label(lock,
			_loc("lvl_locked_hint") % req,
			UiTheme.body_medium(), 11, COL_LOCKED)
		box.add_child(lock)
		var lock_btn := PygameButton.pill_button(_loc("lvl_badge_locked"),
			"locked", "lock", 0, 28, 16)
		lock_btn.disabled = true
		lock_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(lock_btn)
	return card


## Baris difficulty kartu level: label + 5 pip (paritas _core.py:4203-4230).
func _diff_pip_row(lv: Dictionary) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var diff := GameManager.difficulty
	var diff_title := _loc("lvl_diff_normal")
	var diff_color := UiTheme.GREEN
	var diff_level := 1
	if diff == "hard":
		var mult := float(lv.get("enemy_hp_mult", 1.0))
		var pct := int(round((mult - 1.0) * 100.0))
		diff_title = _loc("lvl_diff_hard_pct") % pct if pct > 0 \
			else _loc("lvl_diff_hard")
		diff_color = Color(1.0, 120.0 / 255.0, 100.0 / 255.0)
		diff_level = mini(5, maxi(1, int(mult * 2.5)))
	elif diff == "easy":
		diff_title = _loc("lvl_diff_easy")
		diff_color = UiTheme.CYAN
		diff_level = 1
	var lab := Label.new()
	UiTheme.style_label(lab, diff_title, UiTheme.body_bold(), 13,
		diff_color)
	row.add_child(lab)
	var pips := DiffPips.new(diff_level, 14, 6, 4)
	pips.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(pips)
	return row


# ══════════════════════════════════════════════════════════
#  HERO SHOP (paritas _draw_hero_shop _core.py:4808-5300)
# ══════════════════════════════════════════════════════════

## Meta gold dipakai untuk membuka hero (paritas _unlock_hero_in_meta_shop
## _core.py:5298: cek unlock_require_boss dulu, lalu meta_gold, baru append
## ke purchased_heroes — di Godot: SaveManager.unlock_hero()).
func _build_hero_shop() -> void:
	_screen_header("HERO SHOP")

	# ── chip HERO GOLD + TOP UP (kiri) + BOSSES (kanan) ──
	var chips := HBoxContainer.new()
	chips.add_theme_constant_override("separation", 12)
	chips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(chips)
	chips.add_child(_shop_chip("coin", UiTheme.GOLD, "HERO GOLD",
		_format_grouped(SaveManager.meta_gold()), UiTheme.GOLD_TEXT))
	var topup := PygameButton.pill_button("TOP UP", "success", "plus",
		118, 34, 18)
	topup.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	topup.pressed.connect(_open_topup)
	chips.add_child(topup)
	var chip_mid := Control.new()
	chip_mid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chip_mid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chips.add_child(chip_mid)
	chips.add_child(_shop_chip("skull", UiTheme.CYAN, "BOSSES DEFEATED",
		str((SaveManager.data.get("unlocked_bosses", []) as Array).size()),
		UiTheme.CYAN_SOFT))

	# ── tab STARTER / MINI BOSS / TRUE BOSS (paritas 4837-4857) ──
	var tabs := HBoxContainer.new()
	tabs.alignment = BoxContainer.ALIGNMENT_CENTER
	tabs.add_theme_constant_override("separation", 10)
	tabs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(tabs)
	var group := ButtonGroup.new()
	var tab_font := UiTheme.body_semibold()
	for pair in [["starter", "STARTER HEROES", Color(0.4, 0.8, 1.0)],
			["mini", "MINI BOSSES", Color(1.0, 0.6, 0.4)],
			["true", "TRUE BOSSES", Color(1.0, 0.35, 0.4)]]:
		var tab_id := str(pair[0])
		var spaced := UiTheme.letter(str(pair[1]))
		var tw: float = tab_font.get_string_size(spaced,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 20).x
		var b := PygameButton.tab_button(spaced, pair[2],
			maxf(150.0, tw + 48.0), 34, 20)
		b.use_letter_spacing = false
		b.button_group = group
		b.set_pressed_no_signal(_hero_tab == tab_id)
		b.pressed.connect(_select_hero_tab.bind(tab_id))
		tabs.add_child(b)

	# ── panel konten (border warna tab aktif, paritas 4871-4887) ──
	var tab_border := Color(0.4, 0.8, 1.0)
	if _hero_tab == "mini":
		tab_border = Color(1.0, 0.6, 0.4)
	elif _hero_tab == "true":
		tab_border = Color(1.0, 0.35, 0.4)
	var panel := PygamePanel.new(tab_border, 2.0, 12.0)
	panel.configure(Color(24.0 / 255.0, 30.0 / 255.0, 54.0 / 255.0),
		Color(15.0 / 255.0, 19.0 / 255.0, 36.0 / 255.0),
		tab_border, 2.0, 12.0, true, true)
	panel.set_margins(22, 12, 22, 8)
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_root.add_child(panel)
	var pbox := VBoxContainer.new()
	pbox.add_theme_constant_override("separation", 4)
	pbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(pbox)
	# ── section header + legenda ──
	var sec := _section_titles()[_hero_tab] as Array
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 8)
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pbox.add_child(head)
	head.add_child(VectorIcon.new(str(sec[1]), UiTheme.GOLD_TEXT, 0.8))
	var sec_title := Label.new()
	UiTheme.style_label(sec_title, UiTheme.letter(str(sec[0])),
		UiTheme.body_semibold(), 22, UiTheme.GOLD_TEXT)
	head.add_child(sec_title)
	var rule := HSeparator.new()
	rule.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rule.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_separator(rule, UiTheme.EDGE_GOLD_DIM)
	head.add_child(rule)
	var desc_row := HBoxContainer.new()
	desc_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pbox.add_child(desc_row)
	var sec_desc := Label.new()
	UiTheme.style_label(sec_desc, str(sec[2]), UiTheme.body_medium(), 16,
		UiTheme.TEXT_DIM)
	sec_desc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	desc_row.add_child(sec_desc)
	var legend := Label.new()
	UiTheme.style_label(legend,
		_loc("hshop_legend"),
		UiTheme.body_semibold(), 13, Color(150.0 / 255.0, 156.0 / 255.0, 180.0 / 255.0))
	desc_row.add_child(legend)
	var hline := HSeparator.new()
	hline.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_separator(hline, Color(48.0 / 255.0, 54.0 / 255.0, 80.0 / 255.0))
	pbox.add_child(hline)

	# ── grid hero ──
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	# Lebar scrollbar vertikal di-pin 12px supaya cadangannya
	# deterministik: grid 3*366 + 2*15 = 1128 selalu muat di 1148 - 12.
	# Tab MINI (162 kartu) & TRUE (54 kartu) selalu memunculkan scrollbar;
	# tanpa pin ini kolom kanan terpotong tepat di kedua tab itu.
	scroll.get_v_scroll_bar().custom_minimum_size = Vector2(12, 0)
	pbox.add_child(scroll)
	var grid := GridContainer.new()
	grid.columns = HERO_COLUMNS
	grid.add_theme_constant_override("h_separation", 15)
	grid.add_theme_constant_override("v_separation", 12)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
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
		var no_data := HeroDB.heroes.is_empty()
		UiTheme.style_label(empty,
			_loc("hshop_empty") if not no_data else _loc("hshop_json_missing"),
			UiTheme.body_medium(), 18, COL_DIM if not no_data else COL_RED)
		empty.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		grid.add_child(empty)

	_add_back_button(State.MAIN)


func _section_titles() -> Dictionary:
	return {
		"starter": ["BASE HEROES", "gem", "Available from the start"],
		"mini": ["MINI BOSS HEROES", "skull", "Defeat wave bosses to unlock"],
		"true": ["TRUE BOSS HEROES", "crown", "Ultimate endgame rewards"],
	}


## Chip status auto-size (port ui_theme.chip): ikon + label + nilai.
func _shop_chip(icon_name: String, accent: Color, label: String,
		value: String, value_color: Color) -> PygamePanel:
	var chip := PygamePanel.new(accent, 1.0, 15.0)
	chip.configure(Color(32.0 / 255.0, 38.0 / 255.0, 64.0 / 255.0),
		Color(18.0 / 255.0, 22.0 / 255.0, 40.0 / 255.0),
		accent, 1.0, 15.0, false, false)
	chip.set_margins(14, 4, 14, 4)
	chip.custom_minimum_size = Vector2(0, 30)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(row)
	var icon := VectorIcon.new(icon_name, accent, 0.75)
	icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(icon)
	var lab := Label.new()
	UiTheme.style_label(lab, UiTheme.letter(label),
		UiTheme.body_semibold(), 18, UiTheme.TEXT_BODY)
	row.add_child(lab)
	var val := Label.new()
	UiTheme.style_label(val, value, UiTheme.body_semibold(), 18,
		value_color)
	row.add_child(val)
	return chip


## Buka dialog TOP UP (paritas tombol topup_open _core.py:4831).
func _open_topup() -> void:
	var dlg := TopupDialog.new()
	add_child(dlg)
	# Chip gold disegarkan saat dialog ditutup (gold mungkin bertambah).
	dlg.closed.connect(_show.bind(State.HERO_SHOP))


## Satu kartu hero kompak (HERO_CARD_W x 145) — paritas
## _draw_meta_hero_card (_core.py:5046-5295): potret + info + chip
## role/sekolah + tag kategori + baris status + tombol kanan. Keputusan
## buka dihitung sekali (paritas can_unlock _core.py:5050-5060); meta di
## akhir untuk replay MetaShopTxnParityTest.
func _hero_card(hero_type: String, d: Dictionary) -> Control:
	var owned: bool = SaveManager.is_unlocked(hero_type)
	var cost := int(d.get("unlock_cost", 600))
	# JSON null (starter tanpa syarat boss) — str(null) = "<null>" yang
	# bikin starter dianggap terkunci boss; normalkan ke "" (FASE 20).
	var req_raw = d.get("unlock_require_boss", "")
	var req_boss := "" if req_raw == null else str(req_raw)
	var boss_ready: bool = req_boss.is_empty() or SaveManager.is_boss_unlocked(req_boss)
	var affordable: bool = SaveManager.meta_gold() >= cost
	var hero_col := HeroDB.get_hero_color(hero_type)

	var card := PygamePanel.new()
	card.custom_minimum_size = Vector2(HERO_CARD_W, HERO_CARD_H)
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.hoverable = true
	if owned:
		card.configure(UiTheme.DONE_BG_TOP, UiTheme.DONE_BG_BOTTOM,
			UiTheme.DONE_EDGE, 2.0, 8.0, false, true)
	elif not boss_ready:
		card.configure(UiTheme.LOCKED_BG_TOP, UiTheme.LOCKED_BG_BOTTOM,
			UiTheme.LOCKED_EDGE, 2.0, 8.0, false, true)
	else:
		card.configure(UiTheme.OPEN_BG_TOP, UiTheme.OPEN_BG_BOTTOM,
			UiTheme.OPEN_EDGE, 2.0, 8.0, false, true)
	card.set_margins(12, 10, 12, 10)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(row)

	# ── kiri: potret 72 ──
	var frame := PanelContainer.new()
	frame.custom_minimum_size = Vector2(78, 78)
	frame.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var fsb := StyleBoxFlat.new()
	fsb.bg_color = Color(12.0 / 255.0, 16.0 / 255.0, 28.0 / 255.0)
	fsb.border_color = hero_col if boss_ready \
		else Color(80.0 / 255.0, 84.0 / 255.0, 108.0 / 255.0)
	fsb.set_border_width_all(2)
	fsb.set_corner_radius_all(4)
	frame.add_theme_stylebox_override("panel", fsb)
	row.add_child(frame)
	# ── KIRI: potret DIRENDER dari unit aslinya (port HeroPortraits.draw
	# _bundle.py:215 — boss/hero renderer → crop bbox → scale 60x70 →
	# grayscale untuk kartu terkunci; tanpa strip bake: fallback generik).
	var port := UnitPortrait.new()
	port.setup_unit(hero_type, hero_col, hero_col.darkened(0.45),
		not boss_ready)
	frame.add_child(port)

	# ── tengah: info ──
	var info := VBoxContainer.new()
	info.add_theme_constant_override("separation", 2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(info)
	var name_c := UiTheme.TEXT_WHITE if boss_ready \
		else Color(150.0 / 255.0, 154.0 / 255.0, 178.0 / 255.0)
	var name_l := Label.new()
	UiTheme.style_label(name_l,
		UiTheme.fit_ellipsis(UiTheme.body_bold(), 22,
			str(d.get("name", hero_type)), HERO_INFO_W),
		UiTheme.body_bold(), 22, name_c)
	info.add_child(name_l)
	var title_l := Label.new()
	UiTheme.style_label(title_l,
		UiTheme.fit_ellipsis(UiTheme.body_medium(), 16,
			str(d.get("title", "")), HERO_INFO_W),
		UiTheme.body_medium(), 16, UiTheme.TEXT_DIM)
	info.add_child(title_l)
	# Chip role + sekolah damage — paritas fit pygame (_core.py:5157-5182):
	# role boss panjang ("TRUE BOSS/SPECTRAL CHAIN WARDEN") dipendekkan
	# dengan elipsis sampai chip sekolah ikut muat dalam kolom info.
	# Tanpa ini teks role meluber menabrak tombol kanan (mini/true boss
	# "terpotong"); starter aman karena role-nya pendek.
	var chips := HBoxContainer.new()
	chips.add_theme_constant_override("separation", 8)
	chips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	info.add_child(chips)
	var sch := _school_info(d)
	var school_chip: Control = null
	var school_w := 0.0
	if str(sch[0]) != "":
		school_chip = _mini_chip(str(sch[0]), str(sch[2]),
			sch[1], UiTheme.body_bold(), 13)
		school_w = school_chip.get_combined_minimum_size().x
	# Lebar teks role = kolom info - gap(8) - chip sekolah - padding chip(18).
	var role_avail := HERO_INFO_W - 8.0 - school_w - 18.0
	if role_avail < 30.0 and school_chip != null:
		# Kolom terlalu sempit untuk keduanya: chip sekolah
		# disembunyikan (paritas _fit_school pygame), role dapat lebar penuh.
		school_chip.queue_free()
		school_chip = null
		role_avail = HERO_INFO_W - 18.0
	var role_text := UiTheme.fit_ellipsis(UiTheme.body_bold(), 13,
		str(d.get("role", "-")).to_upper(), maxf(24.0, role_avail))
	chips.add_child(_mini_chip(role_text,
		"", hero_col.lightened(0.25), UiTheme.body_bold(), 13))
	if school_chip != null:
		chips.add_child(school_chip)
	# Tag kategori.
	var tag_row := HBoxContainer.new()
	tag_row.add_theme_constant_override("separation", 6)
	tag_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	info.add_child(tag_row)
	var is_boss := bool(d.get("is_boss_hero", false))
	var bclass := str(d.get("boss_class", "mini"))
	if is_boss and bclass == "true":
		tag_row.add_child(VectorIcon.new("crown",
			Color(1.0, 110.0 / 255.0, 110.0 / 255.0), 0.6))
		var tag_t := Label.new()
		UiTheme.style_label(tag_t, UiTheme.letter("TRUE BOSS"),
			UiTheme.body_bold(), 14,
			Color(1.0, 110.0 / 255.0, 110.0 / 255.0))
		tag_row.add_child(tag_t)
	elif is_boss:
		tag_row.add_child(VectorIcon.new("gem",
			Color(1.0, 175.0 / 255.0, 100.0 / 255.0), 0.6))
		var tag_m := Label.new()
		UiTheme.style_label(tag_m, UiTheme.letter("MINI BOSS"),
			UiTheme.body_bold(), 14,
			Color(1.0, 175.0 / 255.0, 100.0 / 255.0))
		tag_row.add_child(tag_m)
	else:
		var tag_s := Label.new()
		UiTheme.style_label(tag_s, UiTheme.letter("STARTER"),
			UiTheme.body_bold(), 14, UiTheme.TEXT_DIM)
		tag_row.add_child(tag_s)
	# Baris status tunggal.
	var st_row := HBoxContainer.new()
	st_row.add_theme_constant_override("separation", 6)
	st_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	info.add_child(st_row)
	if owned:
		st_row.add_child(VectorIcon.new("check", UiTheme.GREEN, 0.55))
		var st_o := Label.new()
		UiTheme.style_label(st_o, UiTheme.letter(_loc("hshop_owned")),
			UiTheme.body_bold(), 15, UiTheme.GREEN)
		st_row.add_child(st_o)
	elif not boss_ready:
		var boss_name := str(BossDB.get_boss(req_boss).get("name", req_boss))
		st_row.add_child(VectorIcon.new("lock",
			Color(200.0 / 255.0, 120.0 / 255.0, 120.0 / 255.0), 0.55))
		var st_l := Label.new()
		UiTheme.style_label(st_l,
			UiTheme.fit_ellipsis(UiTheme.body_medium(), 15,
				_loc("hshop_defeat") % boss_name, HERO_INFO_W - 20.0),
			UiTheme.body_medium(), 15,
			Color(205.0 / 255.0, 150.0 / 255.0, 150.0 / 255.0))
		st_row.add_child(st_l)
	else:
		st_row.add_child(VectorIcon.new("coin", UiTheme.GOLD, 0.55))
		var cost_text := _loc("hshop_free") if cost <= 0 \
			else "%s G" % _format_grouped(cost)
		var st_c := Label.new()
		UiTheme.style_label(st_c, cost_text, UiTheme.body_bold(), 16,
			UiTheme.GREEN if cost <= 0 else UiTheme.GOLD_TEXT)
		st_row.add_child(st_c)

	# ── kanan: tombol 104x34 ──
	var right := VBoxContainer.new()
	right.alignment = BoxContainer.ALIGNMENT_CENTER
	right.add_theme_constant_override("separation", 4)
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(right)
	if owned:
		var own_btn := PygameButton.pill_button("OWNED", "owned", "check",
			104, 34, 15)
		own_btn.disabled = true
		right.add_child(own_btn)
	elif not boss_ready:
		var lock_btn := PygameButton.pill_button("LOCKED", "locked",
			"lock", 104, 34, 15)
		lock_btn.disabled = true
		right.add_child(lock_btn)
	else:
		var label := _loc("hshop_free") if cost <= 0 else _loc("hshop_unlock")
		var btn := PygameButton.pill_button(label,
			"gold" if affordable else "neutral", "coin", 104, 34, 15)
		btn.disabled = not affordable
		btn.pressed.connect(_try_unlock_hero.bind(hero_type))
		right.add_child(btn)
		var bal := Label.new()
		UiTheme.style_label(bal, "%s/%s" % [
			_format_grouped(SaveManager.meta_gold()),
			_format_grouped(cost)], UiTheme.body_medium(), 10, COL_DIM,
			HORIZONTAL_ALIGNMENT_CENTER)
		right.add_child(bal)

	# Meta keputusan kartu untuk replay MetaShopTxnParityTest (FASE 20):
	# padanan status _draw_meta_hero_card pygame (OWNED / boss-locked /
	# pill label+kind) tanpa mengubah tampilan apa pun.
	card.set_meta("hero_type", hero_type)
	card.set_meta("owned", owned)
	card.set_meta("boss_ready", boss_ready)
	card.set_meta("affordable", affordable)
	card.set_meta("unlock_cost", cost)
	return card


## [label, warna, ikon] sekolah damage kartu (PHY/MAG + TNK).
func _school_info(d: Dictionary) -> Array:
	var sch := str(d.get("dmg_type", "PHYSICAL")).to_upper()
	var is_tank := str(d.get("role", "")).to_upper() == "TANK"
	var col := Color(130.0 / 255.0, 226.0 / 255.0, 168.0 / 255.0) \
		if is_tank \
		else (Color(1.0, 178.0 / 255.0, 92.0 / 255.0)
			if sch == "PHYSICAL"
			else Color(150.0 / 255.0, 196.0 / 255.0, 1.0))
	var label: String = str({"PHYSICAL": "PHY", "MAGIC": "MAG"}.get(sch,
		"PHY"))
	if is_tank:
		label += "·TNK"
	var icon := "shield" if is_tank \
		else ("swords" if sch == "PHYSICAL" else "bolt")
	return [label, col, icon]


## Chip pil kecil (role / sekolah damage kartu hero).
func _mini_chip(text: String, icon_name: String, color: Color,
		font: Font, font_size: int) -> PanelContainer:
	var chip := PanelContainer.new()
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(14.0 / 255.0, 17.0 / 255.0, 30.0 / 255.0)
	sb.border_color = color
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 9.0
	sb.content_margin_right = 9.0
	sb.content_margin_top = 1.0
	sb.content_margin_bottom = 1.0
	chip.add_theme_stylebox_override("panel", sb)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(row)
	if icon_name != "":
		var icon := VectorIcon.new(icon_name, color, 0.5)
		icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(icon)
	var lab := Label.new()
	UiTheme.style_label(lab, text, font, font_size, color)
	row.add_child(lab)
	return chip


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

## Layout 2 kolom — paritas struktur _draw_settings pygame
## (_core.py:6221-6390): KOLOM KIRI = AUDIO + CLOUD SAVE, KOLOM KANAN =
## GAMEPLAY + DANGER ZONE. Opsi pygame yang tidak punya padanan kerja di
## port Godot sengaja TIDAK dipalsukan — ditulis sebagai catatan apa
## adanya (voice: tidak ada aset voice di kedua engine). Baris BAHASA
## (_core.py:6321-6329) hidup lewat port localization.py — lihat
## _language_row() + docs/AUDIT_ULANG_DARI_AWAL.md.
func _build_settings() -> void:
	_screen_header(_loc("set_title"))

	var center := HBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(center)
	var panel := PygamePanel.new(UiTheme.EDGE_GOLD, 2.0, 12.0)
	panel.custom_minimum_size = Vector2(900, 500)
	panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	panel.set_margins(40, 24, 40, 24)
	center.add_child(panel)

	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 40)
	cols.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(cols)

	# ── KOLOM KIRI: AUDIO + CLOUD SAVE ──
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 12)
	left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cols.add_child(left)
	left.add_child(_settings_header("AUDIO", "speaker", UiTheme.CYAN))
	# pygame: master/sfx/bgm/voice (_draw_settings). Slider VOICE dipasang
	# paritas: kategori 'voice' ada di SoundManager pygame (_system.py:599-604)
	# tapi repo tidak punya file voice — di KEDUA engine slider-nya tidak
	# mengubah bunyi apa pun; yang diport adalah persist setting-nya.
	left.add_child(_volume_slider(_loc("set_volume_master"), "master", 0.7))
	left.add_child(_volume_slider(_loc("set_volume_sfx"), "sfx", 0.6))
	left.add_child(_volume_slider(_loc("set_volume_bgm"), "bgm", 0.35))
	left.add_child(_volume_slider(_loc("set_volume_voice"), "voice", 0.5))

	left.add_child(_settings_header("CLOUD SAVE", "cloud",
		UiTheme.CYAN_SOFT))
	# Paritas _draw_cloud_buttons (_core.py:6395-6455) dalam kondisi PC
	# (cloud tidak tersedia): status OFF + tombol upload/download + baris
	# status. Plugin Play Games belum di-port — tombol inert dengan umpan
	# balik status, perilaku yang sama seperti PC pygame.
	left.add_child(PygameButton.pill_button(
		_loc("set_cloud_off"), "locked", "cloud", 340, 32, 15))
	var cloud_up := PygameButton.pill_button(
		_loc("set_cloud_upload"), "neutral", "upload", 340, 32, 15)
	var cloud_down := PygameButton.pill_button(
		_loc("set_cloud_download"), "success", "download", 340, 32, 15)
	left.add_child(cloud_up)
	left.add_child(cloud_down)
	var cloud_note := Label.new()
	UiTheme.style_label(cloud_note,
		_loc("set_cloud_note"),
		UiTheme.body_medium(), 12, Color(0.55, 0.59, 0.69))
	cloud_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(cloud_note)
	cloud_up.pressed.connect(_cloud_unavailable.bind(cloud_note))
	cloud_down.pressed.connect(_cloud_unavailable.bind(cloud_note))
	var cloud_pad := Control.new()
	cloud_pad.size_flags_vertical = Control.SIZE_EXPAND_FILL
	cloud_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	left.add_child(cloud_pad)

	# ── KOLOM KANAN: GAMEPLAY + PROGRESI ──
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 12)
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cols.add_child(right)
	right.add_child(_settings_header("GAMEPLAY", "swords",
		Color(110.0 / 255.0, 235.0 / 255.0, 160.0 / 255.0)))

	# Difficulty: pygame menggemboknya sampai semua level selesai dan
	# menggantinya lewat settings; port Godot memutuskannya di layar PILIH
	# LEVEL (sedikit di atas grid) — tampilkan nilai aktif + arahnya.
	right.add_child(_difficulty_row())
	var diff_note := Label.new()
	UiTheme.style_label(diff_note,
		_loc("set_diff_note"),
		UiTheme.body_medium(), 11, UiTheme.TEXT_DIM)
	right.add_child(diff_note)

	# Screen shake — paritas toggle pygame "Screen Shake"
	# (GameSettings.screen_shake_enabled); kini BENAR-BENAR berfungsi:
	# Camera2D masuk grup "camera" (Main._ready) + guard di Boss._shake.
	right.add_child(_settings_toggle_row(
		"Screen Shake", "screen_shake", 1.0))
	# Damage numbers — paritas toggle pygame "Damage Numbers"; flag sudah
	# dikonsumsi WorldPopups (start_level), kini bisa diubah live.
	right.add_child(_settings_toggle_row(
		"Damage Numbers", "damage_numbers_enabled", 1.0))
	# Game Speed — paritas cycler speed_prev/next (_core.py:7273-7293,
	# opsi 0.5/1.0/1.5/2.0; quirk 1.5x pygame dipertahankan di
	# GameManager.apply_game_speed).
	right.add_child(_cycler_row("Game Speed", [0.5, 1.0, 1.5, 2.0],
		"game_speed", 1.0))
	# Bahasa antarmuka — paritas baris "Interface language" pygame
	# (_core.py:6321-6329), posisinya persis: SETELAH Game Speed, SEBELUM
	# seksi GRAPHICS. Label + nilainya berasal dari port localization.py.
	right.add_child(_language_row())

	# ── GRAPHICS (paritas seksi FPS LIMIT pygame) ──
	right.add_child(_settings_header("GRAPHICS", "gear", UiTheme.EDGE_GOLD))
	# FPS Limit — paritas cycler fps_prev/next (_core.py:7307-7330,
	# opsi 30/60/120/0; 0 = tanpa batas, sama konvensi Engine.max_fps).
	right.add_child(_cycler_row("FPS Limit", [30.0, 60.0, 120.0, 0.0],
		"fps_limit", 60.0))

	var gp_pad := Control.new()
	gp_pad.size_flags_vertical = Control.SIZE_EXPAND_FILL
	gp_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	right.add_child(gp_pad)

	# ── PROGRESI (paritas DANGER ZONE: RESET SAVE SLOT) ──
	right.add_child(_settings_header(_loc("set_progression"), "warn", UiTheme.RED))
	# Hapus SLOT AKTIF (paritas tombol RESET SAVE _core.py:7012-7016)
	# lengkap dengan dialog konfirmasinya.
	var del_btn := PygameButton.pill_button(
		_loc("set_delete_save") % SaveManager.get_current_slot(),
		"danger", "warn", 340, 40, 18)
	del_btn.pressed.connect(_open_slot_delete_dialog.bind(
		SaveManager.get_current_slot()))
	right.add_child(del_btn)
	var note := Label.new()
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(note,
		_loc("set_store_note"),
		UiTheme.body_medium(), 11, UiTheme.TEXT_DIM)
	right.add_child(note)

	_add_back_button(State.PAUSE if from_pause else State.MAIN)


## Header section: ikon + judul letter-spaced + garis hairline
## (paritas ui_theme.section_header).
func _settings_header(text: String, icon_name: String,
		color: Color) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(VectorIcon.new(icon_name, color, 0.8))
	var h := Label.new()
	UiTheme.style_label(h, UiTheme.letter(text),
		UiTheme.body_semibold(), 22, color)
	row.add_child(h)
	var rule := HSeparator.new()
	rule.custom_minimum_size = Vector2(250, 0)
	rule.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_separator(rule, UiTheme.EDGE_GOLD_DIM)
	row.add_child(rule)
	return row


## Baris difficulty: label + nilai MODE berwarna.
func _difficulty_row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lab := Label.new()
	UiTheme.style_label(lab, "Difficulty", UiTheme.body_medium(), 20,
		UiTheme.TEXT_BODY)
	lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(lab)
	var val := Label.new()
	UiTheme.style_label(val, "MODE: %s" % HudLayout.mode_label(
		GameManager.difficulty), UiTheme.body_semibold(), 20,
		HudLayout.mode_color(GameManager.difficulty))
	row.add_child(val)
	return row


## Baris cycler (paritas tombol speed_prev/next & fps_prev/next _core.py:
## 7273-7330): label + "< nilai >" — nilai persist di SaveManager dan
## langsung diterapkan (game_speed -> Engine.time_scale via GameManager,
## fps_limit -> Engine.max_fps).
func _cycler_row(label_text: String, options: Array, key: String,
		default_val: float) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lab := Label.new()
	UiTheme.style_label(lab, label_text, UiTheme.body_medium(), 20,
		UiTheme.TEXT_BODY)
	lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(lab)
	var val_label := Label.new()
	UiTheme.style_label(val_label, "", UiTheme.body_semibold(), 20,
		UiTheme.GOLD_TEXT)
	val_label.custom_minimum_size = Vector2(120, 0)
	val_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var state := {"idx": options.find(
		SaveManager.get_setting(key, default_val))}
	if int(state["idx"]) < 0:
		state["idx"] = options.find(default_val)
	var apply_val := func(v: float) -> void:
		SaveManager.set_setting(key, v, true)
		val_label.text = _cycler_label(key, v)
		if key == "game_speed":
			GameManager.apply_game_speed(v)
		elif key == "fps_limit":
			GameManager.apply_fps_limit(v)
	var prev := PygameButton.pill_button("<", "neutral", "", 28, 28)
	prev.pressed.connect(func():
		state["idx"] = (int(state["idx"]) - 1 + options.size()) \
			% options.size()
		apply_val.call(options[int(state["idx"])]))
	var next := PygameButton.pill_button(">", "neutral", "", 28, 28)
	next.pressed.connect(func():
		state["idx"] = (int(state["idx"]) + 1) % options.size()
		apply_val.call(options[int(state["idx"])]))
	row.add_child(prev)
	row.add_child(val_label)
	row.add_child(next)
	val_label.text = _cycler_label(key, options[int(state["idx"])])
	return row


## Teks nilai cycler: kecepatan "1.0x", FPS "60 FPS" / "TANPA BATAS" (0).
func _cycler_label(key: String, v: float) -> String:
	if key == "game_speed":
		return "%.1fx" % v
	if key == "fps_limit":
		return _loc("set_fps_unlimited") if int(v) == 0 else \
			"%d FPS" % int(v)
	return str(v)


## Baris BAHASA — paritas `_draw_option_setting(col2_x, y, 340,
## tr("language"), get_language_label(settings.language), "language")`
## (_core.py:6321-6329). Bentuk barisnya mengikuti _cycler_row (label +
## `<` nilai `>`) karena pygame juga memakai tombol language_prev/
## language_next (_core.py:7295-7303).
##
## Label baris ini SENDIRI terlokalisasi ("Bahasa" / "Language") dan
## nilainya adalah label manusia ("Bahasa Indonesia" / "English") — jadi
## setelah bahasa berubah layar dibangun ulang (pygame menggambar ulang
## seluruh menu tiap frame; Godot sekali per _show()).
func _language_row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lab := Label.new()
	UiTheme.style_label(lab, MysticLocalization.tr_text("language"),
		UiTheme.body_medium(), 20, UiTheme.TEXT_BODY)
	lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(lab)
	# Nilai = label bahasa AKTIF. pygame membaca `settings.language`
	# (_core.py:6327) yang selalu sinkron dengan localization karena
	# set_language menulis keduanya; padanan Godot-nya adalah cermin
	# GameManager.language (diisi AppShell saat boot dari save).
	var val_label := Label.new()
	UiTheme.style_label(val_label,
		MysticLocalization.get_language_label(GameManager.language),
		UiTheme.body_semibold(), 20, UiTheme.GOLD_TEXT)
	val_label.custom_minimum_size = Vector2(170, 0)
	val_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var prev := PygameButton.pill_button("<", "neutral", "", 28, 28)
	prev.pressed.connect(_cycle_language.bind(-1))
	var next := PygameButton.pill_button(">", "neutral", "", 28, 28)
	next.pressed.connect(_cycle_language.bind(1))
	row.add_child(prev)
	row.add_child(val_label)
	row.add_child(next)
	return row


## Putar bahasa — paritas handler language_prev/language_next
## (_core.py:7295-7303): `languages = ["id", "en"]`, index bahasa aktif
## (tidak dikenal -> 0), delta -1/+1, membungkus modulo, lalu
## `settings.set_language(...)` (validasi + simpan + sinkron localization).
func _cycle_language(direction: int) -> void:
	var options: Array = MysticLocalization.languages()
	if options.is_empty():
		return
	var idx := options.find(GameManager.language)
	if idx < 0:
		idx = 0
	idx = (idx + direction + options.size()) % options.size()
	# set_language memancarkan language_changed -> _on_language_changed
	# membangun ulang layar AKTIF (semua state, bukan hanya SETTINGS), jadi
	# tidak perlu `_show(State.SETTINGS)` eksplisit lagi di sini.
	GameManager.set_language(str(options[idx]))


## Umpan balik tombol cloud di PC pygame: status berubah, tanpa akses
## (mobile/cloud_save.py hanya aktif dengan Play Games di Android).
func _cloud_unavailable(note: Label) -> void:
	note.text = _loc("set_cloud_unavailable")


## Baris toggle (paritas _draw_toggle_setting pygame): label + sakelar pil.
func _settings_toggle_row(label_text: String, key: String,
		default_on: float) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lab := Label.new()
	UiTheme.style_label(lab, label_text, UiTheme.body_medium(), 20,
		UiTheme.TEXT_BODY)
	lab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(lab)
	var on := SaveManager.get_setting(key, default_on) > 0.5
	var t := PygameToggle.new(on)
	t.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	t.pressed.connect(func():
		var now := SaveManager.get_setting(key, default_on) > 0.5
		if key == "screen_shake":
			GameManager.set_screen_shake(not now)
		elif key == "damage_numbers_enabled":
			GameManager.set_damage_numbers(not now)
		SaveManager.set_setting(key, 0.0 if now else 1.0, true)
		t.set_on(not now)
	)
	row.add_child(t)
	return row


## Slider volume premium (paritas _draw_volume_slider: label + % + bar emas
## + tombol -/+ 32px). Live-apply tanpa tulis file; file ditulis saat drag
## selesai / stepper ditekan.
func _volume_slider(label_text: String, key: String,
		default_vol: float = 0.6) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(top)
	var label := Label.new()
	UiTheme.style_label(label, label_text, UiTheme.body_medium(), 20,
		UiTheme.TEXT_BODY)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(label)
	var value_label := Label.new()
	UiTheme.style_label(value_label, "", UiTheme.body_bold(), 20,
		UiTheme.GOLD_TEXT)
	top.add_child(value_label)
	var bot := HBoxContainer.new()
	bot.add_theme_constant_override("separation", 14)
	bot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(bot)
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.value = SaveManager.get_setting(key, default_vol)
	slider.custom_minimum_size = Vector2(0, 24)
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	UiTheme.style_volume_slider(slider)
	value_label.text = "%d%%" % int(round(slider.value * 100.0))
	bot.add_child(slider)
	var minus := PygameButton.pill_button("", "danger", "minus", 32, 32)
	minus.pressed.connect(func():
		slider.value = clampf(slider.value - 0.05, 0.0, 1.0)
		SaveManager.set_setting(key, slider.value, true))
	bot.add_child(minus)
	var plus := PygameButton.pill_button("", "success", "plus", 32, 32)
	plus.pressed.connect(func():
		slider.value = clampf(slider.value + 0.05, 0.0, 1.0)
		SaveManager.set_setting(key, slider.value, true))
	bot.add_child(plus)
	# Live-apply tanpa nulis file (file ditulis saat drag selesai).
	slider.value_changed.connect(_on_volume_changed.bind(key, slider,
		value_label))
	slider.drag_ended.connect(_on_volume_drag_ended.bind(key, slider))
	return box


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
	_screen_header(_loc("howto_title"), true)
	var center := HBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(center)
	var panel := PygamePanel.new(UiTheme.EDGE_GOLD, 2.0, 12.0)
	panel.custom_minimum_size = Vector2(900, 460)
	panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	panel.set_margins(40, 22, 40, 22)
	center.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	panel.add_child(scroll)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scroll.add_child(box)
	# Terjemahan bebas dari sections pygame, disesuaikan kontrol port Godot.
	var sections: Array = [
		[_loc("howto_goal"), "shield", [
			_loc("howto_goal_1"), _loc("howto_goal_2")]],
		[_loc("howto_towers"), "gem", [
			_loc("howto_towers_1"), _loc("howto_towers_2")]],
		[_loc("howto_heroes"), "crown", [
			_loc("howto_heroes_1"), _loc("howto_heroes_2"),
			_loc("howto_heroes_3"), _loc("howto_heroes_4")]],
		[_loc("howto_waves"), "swords", [
			_loc("howto_waves_1"), _loc("howto_waves_2")]],
		[_loc("howto_shop"), "coin", [
			_loc("howto_shop_1"), _loc("howto_shop_2")]],
		[_loc("howto_progress"), "plus", [
			_loc("howto_progress_1"), _loc("howto_progress_2"),
			_loc("howto_progress_3")]],
		[_loc("howto_hard"), "skull", [
			_loc("howto_hard_1"), _loc("howto_hard_2")]],
	]
	for section in sections:
		var head := HBoxContainer.new()
		head.add_theme_constant_override("separation", 10)
		head.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(head)
		head.add_child(VectorIcon.new(str(section[1]), UiTheme.GOLD, 0.8))
		var h := Label.new()
		UiTheme.style_label(h, UiTheme.letter(str(section[0])),
			UiTheme.body_bold(), 21, UiTheme.GOLD_TEXT)
		head.add_child(h)
		# section = [judul, ikon, baris]. Bug lama: loop ini memakai
		# section[1] (Nama IKON) sehingga yang tergambar satu bullet per
		# huruf ikon ("· s", "· h", "· i", ...) dan isi CARA MAIN tidak
		# pernah tampil sama sekali.
		for line in section[2]:
			var body := Label.new()
			body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			UiTheme.style_label(body, "·  " + str(line),
				UiTheme.body_medium(), 17, UiTheme.TEXT_BODY)
			box.add_child(body)
		var gap := Control.new()
		gap.custom_minimum_size = Vector2(0, 8)
		gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(gap)

	_add_back_button(State.MAIN)


# ══════════════════════════════════════════════════════════
#  CREDITS (paritas _draw_credits _core.py:6859-6925)
# ══════════════════════════════════════════════════════════

func _build_credits() -> void:
	_screen_header(_loc("menu_credits"), true)
	var center := HBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(center)
	var panel := PygamePanel.new(UiTheme.EDGE_GOLD, 2.0, 12.0)
	panel.custom_minimum_size = Vector2(700, 450)
	panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	panel.set_margins(36, 42, 36, 30)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 4)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(box)
	var credits: Array = [
		["Tower Defense Battle Arena", UiTheme.GOLD_TEXT, 26],
		["Game Design & Programming", UiTheme.TEXT_DIM, 15],
		["Dharmawan Toxi", UiTheme.TEXT_WHITE, 22],
		["Art Direction", UiTheme.TEXT_DIM, 15],
		["Dark Fantasy Vector Style", UiTheme.TEXT_WHITE, 20],
		["Sound Effects & Music", UiTheme.TEXT_DIM, 15],
		["Custom SFX Library", UiTheme.TEXT_WHITE, 20],
		["Port Godot 4", UiTheme.TEXT_DIM, 15],
		["Pygame Community  •  Python 3.10+  •  Godot 4.3", UiTheme.TEXT_WHITE, 17],
	]
	var first := true
	for row in credits:
		if not first and int(row[2]) <= 15:
			var gap := Control.new()
			gap.custom_minimum_size = Vector2(0, 6)
			gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
			box.add_child(gap)
		first = false
		var l := Label.new()
		var txt := UiTheme.letter(str(row[0])) if int(row[2]) <= 15 \
			else str(row[0])
		UiTheme.style_label(l, txt, UiTheme.body_semibold(), int(row[2]),
			row[1], HORIZONTAL_ALIGNMENT_CENTER)
		box.add_child(l)
	var pad := Control.new()
	pad.size_flags_vertical = Control.SIZE_EXPAND_FILL
	pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(pad)
	# "Made with ♥" (hati vektor, bukan emoji).
	var heart := HBoxContainer.new()
	heart.alignment = BoxContainer.ALIGNMENT_CENTER
	heart.add_theme_constant_override("separation", 6)
	heart.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(heart)
	var hl := Label.new()
	UiTheme.style_label(hl, "Made with ", UiTheme.body_medium(), 17,
		Color(1.0, 150.0 / 255.0, 200.0 / 255.0))
	heart.add_child(hl)
	heart.add_child(VectorIcon.new("heart",
		Color(1.0, 120.0 / 255.0, 170.0 / 255.0), 0.7))
	var hr := Label.new()
	UiTheme.style_label(hr, " using Pygame", UiTheme.body_medium(), 17,
		Color(1.0, 150.0 / 255.0, 200.0 / 255.0))
	heart.add_child(hr)

	_add_back_button(State.MAIN)


# ══════════════════════════════════════════════════════════
#  PAUSE (paritas _draw_pause_menu _core.py:6930-7000)
# ══════════════════════════════════════════════════════════

func _build_pause() -> void:
	# Panel 400x400 terpusat (paritas geometri pause pygame) — anak LANGSUNG
	# MainMenu (Control biasa, BUKAN container) dengan posisi/ukuran eksplisit:
	# di dalam VBox _root/_bg geometrinya dikendalikan layout (bug: rect jadi
	# (44,18,400,408) — margin backdrop + tinggi konten).
	var panel := PygamePanel.new(UiTheme.GOLD, 2.0, 12.0)
	panel.name = "PausePanel"
	panel.position = HudLayout.PAUSE_PANEL_POS
	panel.size = HudLayout.PAUSE_PANEL_SIZE
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.set_margins(20, 12, 20, 12)
	add_child(panel)
	_pause_panel = panel

	var inner := VBoxContainer.new()
	inner.alignment = BoxContainer.ALIGNMENT_CENTER
	inner.add_theme_constant_override("separation", 7)
	inner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(inner)

	var title := Label.new()
	UiTheme.style_label(title, "PAUSED", UiTheme.title_font(), 46,
		UiTheme.GOLD_BRIGHT, HORIZONTAL_ALIGNMENT_CENTER)
	title.add_theme_color_override("font_outline_color",
		Color(0.03, 0.04, 0.07))
	title.add_theme_constant_override("outline_size", 4)
	inner.add_child(title)

	# badge difficulty (paritas mode badge 6949-6960)
	var mode := Label.new()
	mode.name = "PauseMode"
	UiTheme.style_label(mode, "MODE: %s  ·  LEVEL %d  ·  WAVE %d" % [
		HudLayout.mode_label(GameManager.difficulty), GameManager.level_number,
		GameManager.wave_number],
		UiTheme.body_semibold(), 14,
		HudLayout.mode_color(GameManager.difficulty),
		HORIZONTAL_ALIGNMENT_CENTER)
	inner.add_child(mode)

	var line := HSeparator.new()
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_separator(line, UiTheme.EDGE_GOLD)
	inner.add_child(line)

	# Urutan paritas PAUSE_BUTTON_ORDER; label Indonesia disengaja (MainMenu
	# Godot berbahasa Indonesia); ukuran 300x48 = pygame.
	var buttons: Array = [
		["PauseResume", _loc("pause_resume"), Color(100.0 / 255.0, 200.0 / 255.0, 100.0 / 255.0), _do_resume, "play"],
		["PauseSettings", _loc("set_title"), Color(200.0 / 255.0, 180.0 / 255.0, 100.0 / 255.0), _show.bind(State.SETTINGS), "gear"],
		["PauseMenu", _loc("pause_menu"), Color(100.0 / 255.0, 180.0 / 255.0, 1.0), _do_main_menu, "back"],
		["PauseQuit", _loc("menu_quit"), Color(220.0 / 255.0, 80.0 / 255.0, 80.0 / 255.0), func(): get_tree().quit(), "quit"],
	]
	for pair in buttons:
		var b := _make_button(str(pair[1]), pair[2], pair[3],
			HudLayout.PAUSE_BUTTON_SIZE, 19, str(pair[4]))
		b.name = str(pair[0])
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		inner.add_child(b)


# ══════════════════════════════════════════════════════════
#  WIDGET HELPER
# ══════════════════════════════════════════════════════════

## Tombol menu premium (port ui_theme.button 1:1 via PygameButton Mode.MENU:
## gradasi, aksen kiri, badge ikon, sudut emas, glow hover). Klik -> SFX
## ui_click otomatis (paritas SoundManager).
func _make_button(label_text: String, accent: Color, handler: Callable,
		min_size: Vector2 = Vector2(0, 34), font_size: int = 14,
		icon_name: String = "") -> Button:
	var b := PygameButton.menu_button(label_text, accent, icon_name,
		min_size.x, min_size.y, font_size)
	if handler.is_valid():
		b.pressed.connect(handler)
	return b
