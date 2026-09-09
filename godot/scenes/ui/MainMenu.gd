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

signal play_requested(level_num: int)
signal resume_requested
signal main_menu_requested

## Paritas MenuState _core.py:3099-3106, termasuk SLOT_SELECT multi-slot.
enum State { MAIN, SLOT_SELECT, LEVEL_SELECT, HERO_SHOP, SETTINGS, HOW_TO_PLAY, CREDITS, PAUSE }

const COL_BG := Color(0.031, 0.033, 0.058, 0.985)
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

var state: int = State.MAIN
## True kalau menu dibuka dari dalam match (PAUSE) — MAIN-nya jadi "MAIN MENU"
## yang kembali ke permainan, bukan menutup game.
var from_pause: bool = false

var _bg: PanelContainer = null
var _root: VBoxContainer = null      # dibangun ulang tiap ganti state
var _confirm: PanelContainer = null  # dialog keluar (paritas exit_confirm)
var _pause_panel: PanelContainer = null # panel pause 400x400 (anak MainMenu)
var _hero_tab: String = "starter"    # paritas Menu.shop_tab _core.py:4810


func _ready() -> void:
	name = "MainMenu"
	add_to_group("main_menu")
	# Harus tetap hidup saat SceneTree di-pause (menu PAUSE dibuka justru
	# ketika get_tree().paused = true).
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_preset(Control.PRESET_FULL_RECT)
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
		_confirm.visible = false
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
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_BG
	sb.border_color = COL_BORDER
	sb.border_width_bottom = 2
	# padding konten (pygame: panel mulai x=... ; di sini margin global)
	sb.content_margin_left = 44.0
	sb.content_margin_right = 44.0
	sb.content_margin_top = 18.0
	sb.content_margin_bottom = 14.0
	_bg.add_theme_stylebox_override("panel", sb)
	add_child(_bg)


## Bersihkan isi lalu bangun state baru — padanan Menu.draw() yang memanggil
## _draw_main_menu()/_draw_level_select()/dst. per frame (kita sekali saja).
func _show(new_state: int) -> void:
	state = new_state
	show()
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


## Pilih slot save sebelum memilih level (paritas MenuState.SLOT_SELECT).
func _build_slot_select() -> void:
	_screen_header("PILIH SAVE GAME", State.MAIN)
	var subtitle := Label.new()
	subtitle.text = "Pilih save untuk melanjutkan atau mulai game baru"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_font_size_override("font_size", 14)
	subtitle.add_theme_color_override("font_color", COL_DIM)
	_root.add_child(subtitle)

	var grid := GridContainer.new()
	grid.columns = SaveManager.NUM_SLOTS
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 10)
	grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_root.add_child(grid)
	for slot_num in range(1, SaveManager.NUM_SLOTS + 1):
		grid.add_child(_slot_card(slot_num, SaveManager.get_slot_info(slot_num)))

	var hint := Label.new()
	hint.text = "Slot kosong akan dibuat saat progres pertama disimpan."
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.add_theme_font_size_override("font_size", 11)
	hint.add_theme_color_override("font_color", COL_DIM)
	_root.add_child(hint)


func _slot_card(slot_num: int, info) -> Control:
	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(370, 300)
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_PANEL if info != null else Color(0.055, 0.065, 0.1)
	sb.border_color = COL_BORDER if info != null else COL_BLUE
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 14.0
	sb.content_margin_right = 14.0
	sb.content_margin_top = 12.0
	sb.content_margin_bottom = 12.0
	card.add_theme_stylebox_override("panel", sb)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 7)
	card.add_child(box)
	var title := Label.new()
	title.text = "SAVE GAME %d" % slot_num
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", COL_GOLD if info != null else COL_BLUE)
	box.add_child(title)
	var rule := HSeparator.new()
	box.add_child(rule)
	if info == null:
		var empty := Label.new()
		empty.text = "KOSONG\n\nMulai game baru"
		empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		empty.size_flags_vertical = Control.SIZE_EXPAND_FILL
		empty.add_theme_color_override("font_color", COL_DIM)
		box.add_child(empty)
	else:
		var summary := Label.new()
		summary.text = "Level tertinggi: %d\nLevel terakhir: %d\nMeta gold: %d\nHero: %d  ·  Boss: %d\nPlaytime: %s" % [
			int(info["highest_level"]), int(info["last_played_level"]),
			int(info["meta_gold"]), (info["purchased_heroes"] as Array).size(),
			(info["unlocked_bosses"] as Array).size(),
			_format_playtime(int(info["playtime_seconds"]))]
		summary.add_theme_font_size_override("font_size", 13)
		summary.add_theme_color_override("font_color", COL_TEXT)
		summary.size_flags_vertical = Control.SIZE_EXPAND_FILL
		box.add_child(summary)
	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	actions.add_theme_constant_override("separation", 8)
	box.add_child(actions)
	actions.add_child(_make_button("PILIH", COL_GREEN,
		_select_slot.bind(slot_num), Vector2(150, 34), 14))
	if info != null:
		actions.add_child(_make_button("HAPUS", COL_RED,
		_delete_slot.bind(slot_num), Vector2(110, 34), 13))
	return card


func _format_playtime(seconds: int) -> String:
	var hours := int(seconds / 3600)
	var minutes := int((seconds % 3600) / 60)
	return "%dh %dm" % [hours, minutes] if hours > 0 else "%dm" % minutes


func _select_slot(slot_num: int) -> void:
	if not SaveManager.set_current_slot(slot_num, true):
		return
	_show(State.LEVEL_SELECT)


func _delete_slot(slot_num: int) -> void:
	var dialog := ConfirmationDialog.new()
	dialog.title = "Hapus Save Game"
	dialog.dialog_text = "Hapus permanen Save Game %d?" % slot_num
	dialog.confirmed.connect(func():
		SaveManager.delete_slot(slot_num)
		_show(State.SLOT_SELECT)
		dialog.queue_free())
	dialog.canceled.connect(dialog.queue_free)
	add_child(dialog)
	dialog.popup_centered()


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


## State-only view model untuk kartu level. Nilainya berasal dari save yang
## sedang aktif; formatter waktu adalah SaveManager.format_time Pygame.
## Replay test memanggil fungsi ini lewat MainMenu produksi.
func level_stat_display(level_num: int) -> Dictionary:
	var stats := SaveManager.get_level_stats(SaveManager.data, level_num)
	var attempts := int(stats.get("total_attempts", 0))
	var score := int(stats.get("best_score", 0))
	var score_text := ("%.1fK" % (float(score) / 1000.0)) if score >= 10000 else HudLayout.format_thousands(score)
	var wins := int(stats.get("wins", 0))
	var win_rate := int(float(wins) / float(attempts) * 100.0) if attempts > 0 else 0
	return {
		"has_stats": attempts > 0,
		"score": score,
		"score_text": score_text,
		"time_seconds": int(stats.get("best_time_seconds", 0)),
		"time_text": SaveManager.format_time(int(stats.get("best_time_seconds", 0))),
		"attempts": attempts,
		"wins": wins,
		"win_rate": win_rate,
	}


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


## Satu kartu level — paritas _draw_level_card (_core.py:4121-4320): nomor +
## nama + deskripsi + info boss + badge DONE/LOCKED. Klik kartu = main
## (pygame: rect klik = seluruh kartu).
func _level_card(lv: Dictionary) -> Control:
	var level_num := int(lv.get("level_number", 0))
	var unlocked: bool = GameManager.is_level_unlocked(level_num)
	var completed: bool = SaveManager.is_level_completed(level_num)

	var card := PanelContainer.new()
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

	# ── baris 4: statistik LEVEL SELECT (paritas _core.py:4257-4289) ──
	# State dipisah dari pixel layout: nilai dan formatter harus sama dengan
	# Pygame, termasuk --:-- untuk waktu yang belum pernah dicatat. Pygame
	# hanya menampilkan bagian ini setelah level terbuka.
	if unlocked:
		var stats := level_stat_display(level_num)
		var stat_label := Label.new()
		if bool(stats["has_stats"]):
			stat_label.text = "BEST SCORE  %s   ·   BEST TIME  %s\nATTEMPTS  %dW/%d   ·   WIN RATE  %d%%" % [
				str(stats["score_text"]), str(stats["time_text"]),
				int(stats["wins"]), int(stats["attempts"]), int(stats["win_rate"])]
			stat_label.add_theme_color_override("font_color", COL_TEXT)
		else:
			stat_label.text = "No stats yet"
			stat_label.add_theme_color_override("font_color", COL_DIM)
		stat_label.add_theme_font_size_override("font_size", 10)
		stat_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(stat_label)

	# ── baris 5: aksi ──
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
		empty.text = "Tidak ada hero di kategori ini."
		empty.add_theme_color_override("font_color", COL_DIM)
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
	var req_boss := str(d.get("unlock_require_boss", ""))
	var boss_ready: bool = req_boss.is_empty() or SaveManager.is_boss_unlocked(req_boss)

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
		var affordable: bool = SaveManager.meta_gold() >= cost
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
	return card


## Paritas _unlock_hero_in_meta_shop (_core.py:5298-5328): validasi katalog +
## boss requirement + saldo, potong meta_gold, lalu tulis satu transaksi.
## Return view state agar replay test tidak hanya menguji tampilan tombol.
func hero_shop_transaction(hero_type: String) -> Dictionary:
	if HeroDB.get_hero(hero_type).is_empty():
		return {"ok": false, "reason": "invalid_hero", "hero": hero_type}
	if SaveManager.is_unlocked(hero_type):
		return {"ok": false, "reason": "already_owned", "hero": hero_type}
	var d: Dictionary = HeroDB.get_hero(hero_type)
	var req_boss := str(d.get("unlock_require_boss", ""))
	if not req_boss.is_empty() and not SaveManager.is_boss_unlocked(req_boss):
		return {"ok": false, "reason": "boss_required", "hero": hero_type,
			"boss": req_boss}
	var cost := int(d.get("unlock_cost", 600))
	if SaveManager.meta_gold() < cost:
		return {"ok": false, "reason": "insufficient_gold", "hero": hero_type,
			"cost": cost}
	var before_gold := SaveManager.meta_gold()
	if not SaveManager.commit_hero_purchase(hero_type, cost):
		return {"ok": false, "reason": "commit_failed", "hero": hero_type}
	return {"ok": true, "reason": "purchased", "hero": hero_type,
		"cost": cost, "gold_before": before_gold,
		"gold_after": SaveManager.meta_gold(),
		"owned": SaveManager.is_unlocked(hero_type)}


func _try_unlock_hero(hero_type: String) -> void:
	var result := hero_shop_transaction(hero_type)
	if not bool(result["ok"]):
		AudioManager.play_sfx("ui_error")
		return
	AudioManager.play_sfx("ui_buy")
	print("[HeroShop] %s dibuka (-%d meta gold)" % [hero_type, int(result["cost"])])
	_show(State.HERO_SHOP) # segarkan chip gold + status kartu


# ══════════════════════════════════════════════════════════
#  SETTINGS (paritas _draw_settings _core.py:6221-6390, kolom AUDIO)
# ══════════════════════════════════════════════════════════

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
	sb.content_margin_left = 40.0
	sb.content_margin_right = 40.0
	sb.content_margin_top = 20.0
	sb.content_margin_bottom = 20.0
	panel.add_theme_stylebox_override("panel", sb)
	_root.add_child(panel)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 18)
	panel.add_child(box)

	var audio_header := Label.new()
	audio_header.text = "AUDIO"
	audio_header.add_theme_font_size_override("font_size", 18)
	audio_header.add_theme_color_override("font_color", Color(0.5, 0.85, 0.95))
	box.add_child(audio_header)
	# pygame punya 4 slider (master/sfx/bgm/voice); port Godot baru punya bus
	# sfx + bgm, jadi cuma 2 yang benar-benar berfungsi — sisanya jangan dipalsukan.
	box.add_child(_volume_slider("Volume SFX", "sfx"))
	box.add_child(_volume_slider("Volume Musik (BGM)", "bgm"))

	var note := Label.new()
	note.text = "Volume disimpan di SaveManager.data[\"settings\"] dan langsung " \
		+ "diterapkan ke AudioManager. Difficulty diganti di layar PILIH LEVEL " \
		+ "(sebelum mulai pertandingan)."
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.add_theme_font_size_override("font_size", 11)
	note.add_theme_color_override("font_color", COL_DIM)
	box.add_child(note)


func _volume_slider(label_text: String, key: String) -> Control:
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
	slider.value = SaveManager.get_setting(key, 0.6)
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
