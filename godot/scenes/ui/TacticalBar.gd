# TacticalBar.gd — FASE 18: panel TACTICAL COMMANDS (HOLD) di HUD.
#
# Port pemicu UI pygame untuk perintah taktis (FASE 17 = TacticalCommands.gd):
#   * mobile/sidepanel.py::_gambar_tactical — 5 tombol GATHER [G] /
#     PROTECT TOWER [T] / PROTECT CASTLE [C] / ATTACK BOSS [B] /
#     ATTACK DMG DEALER [D], hanya tampak saat state == "playing".
#     Kelima kotak SELALU digambar; yang syaratnya tak terpenuhi tampil
#     ABU tak-bisa-ditekan (pygame menggambar bg (45,45,50) + border
#     (80,80,85) + teks (120,120,125) untuk not-enabled — btn.visible
#     pygame HANYA mematikan hit-test, bukan gambar kotaknya).
#     Perintah yang sedang DITAHAN menyala + chip "HOLD" (paritas sorot
#     held_cmd pygame).
#   * mobile/hud.py::apply_hud_action — tekan = hold_start (gather TANPA
#     posisi mouse, protect_tower pakai selected_tower biru bila ada).
#   * main.py cabang release/pause/APP_BG — lepas sentuhan = hold_end(nama),
#     pause / aplikasi ke latar = hold_end() (lepas semuanya).
#
# KEYBOARD TIDAK DIHANDLE DI SINI: tuts G/F/T/C/B/D dimiliki Main._on_key
# (paritas InputHandler.handle_key pygame — hotkey gather MEMAKAI posisi
# mouse + follow_mouse, beda dari tombol panel). Panel dan hotkey sama-sama
# berakhir di TacticalCommands.gd yang sama, jadi tidak ada logika ganda.
#
# Yang dibandingkan harness TacticalInputParityTest: visibilitas tombol
# (panel_available) + jejak hold_start/hold_end. Feedback command kini ikut
# ditampilkan di layar seperti tactical_commands.py; raster font/panel tetap
# aproksimasi, bukan assertion piksel.
extends Control

const COMMANDS: Array = [
	["gather", "GATHER [G]", Color(0.39, 0.62, 1.0)],
	["protect_tower", "PROTECT TOWER [T]", Color(0.40, 0.90, 0.47)],
	["protect_castle", "PROTECT CASTLE [C]", Color(1.0, 0.80, 0.33)],
	["attack_boss", "ATTACK BOSS [B]", Color(0.95, 0.35, 0.35)],
	["attack_damage_dealer", "ATTACK DMG DEALER [D]", Color(0.72, 0.51, 1.0)],
]

## ── LIPATAN PANEL (Godot-only, layar TANPA rail kanan) ──
## Di pygame kotak TACTICAL COMMANDS hidup DI DALAM panel kanan; tanpa panel
## (16:9 persis dan lebih sempit) pygame sama sekali tidak menggambar tombol
## command — pemain memakai hotkey G/F/T/C/B/D. Godot dulu menaruh kotak
## 220x210 mengambang di kanan-bawah ARENA saat rail tidak ada, jadi map
## tertutup dan ketukan di sana tak sampai ke unit. Sekarang kotak itu
## DILIPAT default menjadi chip kecil "TACTICAL" di kanan-bawah arena:
## map bersih, tombol command tetap satu ketukan dari HP tanpa keyboard.
## Tiga lapis supaya tidak pernah "menghalangi map": (1) kotak mengambang
## CLICK-THROUGH — hanya tombol perintah yang menelan klik, sela panel tetap
## milik map; (2) klik di luar kotak sekaligus melipatnya (kebiasaan
## dropdown); (3) chip + kotak disembunyikan selama popup modal terbuka.
const TOGGLE_W := 148.0
const TOGGLE_H := 32.0
const TOGGLE_GAP := 6.0
## Jarak dasar dari sisi bawah (di atas tombol SKIP TouchHUD 646..704).
const TOGGLE_BOTTOM_INSET := 78.0

var _box: PanelContainer = null
var _toggle: Button = null
## Terbuka hanya relevan saat tidak ada rail (lihat _apply_visibility).
var _expanded: bool = false
var _title: Label = null
var _buttons: Dictionary = {}
## action -> {font: Color, bg: Color} — warna dasar tombol untuk
## dipulihkan setelah sorot HOLD dilepas.
var _btn_base: Dictionary = {}
## Perintah yang sedang ditahan lewat tombol panel (mirror held_tac main.py:
## sentuhan -> nama perintah). Pelepasan dirutekan berdasar SENTUHAN yang
## menekan — bukan tombol yang sedang aktif di manajer — paritas release
## claimed-touch pygame (hold_end nama salah = no-op di manajer).
var _held: Dictionary = {}
var _timer: float = 0.0
## Feedback command menggantikan TacticalCommandManager.draw_ui pygame.
## Node ini full-rect dan mouse-transparent, jadi tetap tampil saat rail
## dilipat tanpa mengganggu hit-test map/panel.
var _feedback_panel: PanelContainer = null
var _feedback_label: Label = null
var _feedback_style: StyleBoxFlat = null

func _ready() -> void:
	name = "TacticalBar"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_to_group("tactical_bar")
	MobileLayout.fill_parent(self)
	_build()
	MobileLayout.layout_changed.connect(_layout)
	_layout()
	GameManager.selection_changed.connect(_refresh)
	GameManager.shop_changed.connect(_refresh)
	GameManager.game_over.connect(func(_v): _refresh())
	GameManager.hero_died.connect(func(_h): _refresh())
	GameManager.boss_spawned.connect(func(_b): _refresh())
	GameManager.tower_destroyed.connect(func(_t, _k): _refresh())
	# Ganti bahasa -> tooltip dibangun ulang (dibuat sekali di _build).
	GameManager.language_changed.connect(func(_l): _rebuild_tooltips())
	_refresh()

## Tempatkan kotak command di dasar panel kanan (paritas _gambar_tactical),
## atau — kalau panel kanan tidak ada — lipat jadi chip kecil di kanan-bawah
## arena dengan kotak command tepat di atasnya saat dibuka.
func _layout() -> void:
	if _box == null or _toggle == null:
		return
	var rect := MobileLayout.tactical_rect()
	if rect.size.x > 0.0:
		# Ada rail: kotak command di dasar rail, chip tidak dipakai
		# (paritas pygame — command selalu tampil selama panelnya ada).
		_box.position = rect.position
		_box.size = rect.size
		_apply_visibility(true)
		return
	# Tanpa rail: chip menempel di kanan-bawah FRAME ARENA (bukan kanan-bawah
	# viewport) — di jendela desktop yang lebih tinggi/lebar dari 16:9 pusat
	# dan tepi viewport ada di luar peta, jadi chip-nya tampak melayang di
	# area kosong kalau memakai viewport (lihat catatan MobileLayout).
	var frame := MobileLayout.arena_frame_rect()
	var chip := Vector2(maxf(frame.position.x + 8.0,
		frame.position.x + frame.size.x - TOGGLE_W - 8.0),
		maxf(frame.position.y + 8.0,
			frame.position.y + frame.size.y - TOGGLE_BOTTOM_INSET - TOGGLE_H))
	_toggle.position = chip
	_toggle.size = Vector2(TOGGLE_W, TOGGLE_H)
	var w := minf(220.0, maxf(120.0, frame.size.x - 16.0))
	var h := minf(MobileLayout.TACTICAL_HEIGHT, maxf(90.0, frame.size.y - 32.0))
	_box.position = Vector2(chip.x + TOGGLE_W - w,
		maxf(8.0, chip.y - TOGGLE_GAP - h))
	_box.size = Vector2(w, h)
	_apply_visibility(false)


## Visibilitas kotak + chip. Pygame tidak punya padanan chip: ini lapisan
## Godot supaya map tidak tertutup saat rail tidak ada.
## Popup modal (ShopPanel/TOP UP) menutup hampir seluruh arena: chip + kotak
## mengambang ikut DILIPAT & disembunyikan supaya tidak menumpuk di atas
## lapisan gelap dan tak sengaja tertekan saat pemain berbelanja (rail kanan
## tetap tampil — paritas panel pygame yang memang hidup di luar peta).
func _apply_visibility(has_rail: bool) -> void:
	var playing := GameManager.state == "playing" and not GameManager.in_menu
	var modal := GameManager.shop_open
	if not playing or modal:
		# Keluar dari gameplay / popup terbuka: panel kembali terlipat supaya
		# match berikutnya mulai dengan map bersih.
		_expanded = false
	_toggle.visible = playing and not has_rail and not modal
	_box.visible = playing and (has_rail or _expanded)


## Buka/tutup panel command saat layar tidak punya rail (dipakai chip +
## harness paritas).
func set_expanded(value: bool) -> void:
	_expanded = value
	_refresh()


func is_expanded() -> bool:
	return _expanded


func _process(delta: float) -> void:
	# Feedback harus disinkronkan tiap frame agar fade tidak tersendat
	# walau visibilitas tombol cukup diperbarui 5 Hz.
	_sync_feedback()
	# Visibilitas tombol mengikuti kondisi medan (hero hidup / boss aktif).
	# 5 Hz cukup (paritas draw per-frame pygame bukan target piksel).
	_timer += delta
	if _timer >= 0.2:
		_timer = 0.0
		_refresh()

func _build() -> void:
	_box = PygamePanel.new(Color(0.32, 0.38, 0.55, 0.9), 2.0, 9.0)
	_box.name = "TacticalBox"
	# CLICK-THROUGH: panel mengambang (tanpa rail) TIDAK boleh menelan klik
	# yang jatuh di luar tombol perintah — dulu MOUSE_FILTER_STOP membuat
	# seluruh kotak 220x210 "menghalangi map": ketukan di sela tombol tak
	# sampai ke unit. PygamePanel default IGNORE; hanya tombol perintah yang
	# STOP, jadi sela panel, judul, dan margin tetap milik map (klik di luar
	# sekaligus melipat panel lewat _input — kebiasaan dropdown).
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Posisi diatur _layout() dari MobileLayout.tactical_rect() (jalur dasar
	# panel kanan). Anchor kiri-atas + offset absolut = tidak pernah keluar
	# frame walau viewport berubah.
	_box.anchor_left = 0.0
	_box.anchor_right = 0.0
	_box.anchor_top = 0.0
	_box.anchor_bottom = 0.0
	(_box as PygamePanel).show_ticks = false
	(_box as PygamePanel).set_margins(10, 6, 10, 8)
	add_child(_box)

	var col := VBoxContainer.new()
	col.name = "TacticalColumn"
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_theme_constant_override("separation", 6)
	_box.add_child(col)

	_title = Label.new()
	UiTheme.style_label(_title, "TACTICAL COMMANDS (HOLD)",
		UiTheme.body_bold(), 11, Color(0.85, 0.88, 0.98),
		HORIZONTAL_ALIGNMENT_CENTER)
	col.add_child(_title)

	for spec in COMMANDS:
		var action := str(spec[0])
		var btn := Button.new()
		btn.name = "Cmd_" + action
		btn.text = str(spec[1])
		btn.focus_mode = Control.FOCUS_NONE
		btn.custom_minimum_size = Vector2(0, 30)
		var c: Color = spec[2]
		UiTheme.apply_row_button(btn, "neutral", 11, false)
		btn.add_theme_color_override("font_color", c.lightened(0.25))
		btn.tooltip_text = _tooltip(action)
		_btn_base[action] = {
			"font": c.lightened(0.25),
			"bg": (btn.get_theme_stylebox("normal") as StyleBoxFlat).bg_color,
		}
		# Chip "HOLD" (paritas kotak kecil kanan tombol pygame): panel
		# gelap + border warna command, di kanan-tengah tombol.
		var chip := PanelContainer.new()
		chip.name = "HoldChip"
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var csb := StyleBoxFlat.new()
		csb.bg_color = Color8(20, 18, 30)
		csb.border_color = c
		csb.set_border_width_all(1)
		csb.set_corner_radius_all(4)
		csb.content_margin_left = 4.0
		csb.content_margin_right = 4.0
		csb.content_margin_top = 1.0
		csb.content_margin_bottom = 1.0
		chip.add_theme_stylebox_override("panel", csb)
		var chip_label := Label.new()
		UiTheme.style_label(chip_label, "HOLD", UiTheme.body_regular(), 9,
			Color.WHITE, HORIZONTAL_ALIGNMENT_CENTER)
		chip_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		chip_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		chip.add_child(chip_label)
		chip.anchor_left = 1.0
		chip.anchor_right = 1.0
		chip.anchor_top = 0.5
		chip.anchor_bottom = 0.5
		chip.offset_left = -54.0
		chip.offset_right = -8.0
		chip.offset_top = -9.0
		chip.offset_bottom = 9.0
		chip.visible = false
		btn.add_child(chip)
		# Tekan = MULAI menahan (main.py: hit -> held_tac + apply_hud_action).
		btn.button_down.connect(_on_button_down.bind(action))
		# Lepas = berhenti menahan (main.py cabang release untuk claimed tid).
		btn.button_up.connect(_on_button_up.bind(action))
		col.add_child(btn)
		_buttons[action] = btn

	# Chip pelipat — hanya dipakai saat rail kanan tidak ada (lihat _layout).
	_toggle = Button.new()
	_toggle.name = "TacticalToggle"
	_toggle.text = "TACTICAL"
	_toggle.focus_mode = Control.FOCUS_NONE
	_toggle.custom_minimum_size = Vector2(TOGGLE_W, TOGGLE_H)
	_toggle.tooltip_text = MysticLocalization.tr_text("tac_toggle_tip")
	UiTheme.apply_row_button(_toggle, "neutral", 12, false)
	_toggle.add_theme_color_override("font_color", Color(0.85, 0.88, 0.98))
	_toggle.pressed.connect(_on_toggle_pressed)
	add_child(_toggle)
	_build_feedback()


## Feedback UI dari `TacticalCommandManager.feedback_*`.
## Pygame menaruhnya di (640, 90), fade-in 30 frame dan fade-out 30
## frame; PanelContainer memberi padanan aman untuk bg/border rounded.
func _build_feedback() -> void:
	_feedback_panel = PanelContainer.new()
	_feedback_panel.name = "TacticalFeedback"
	_feedback_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_feedback_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_feedback_panel.offset_left = -310.0
	_feedback_panel.offset_right = 310.0
	_feedback_panel.offset_top = 68.0
	_feedback_panel.offset_bottom = 116.0
	_feedback_style = StyleBoxFlat.new()
	_feedback_style.bg_color = Color(0.02, 0.02, 0.05, 0.86)
	_feedback_style.border_color = Color(1.0, 0.86, 0.4, 0.95)
	_feedback_style.set_border_width_all(2)
	_feedback_style.set_corner_radius_all(6)
	_feedback_style.content_margin_left = 10.0
	_feedback_style.content_margin_right = 10.0
	_feedback_style.content_margin_top = 5.0
	_feedback_style.content_margin_bottom = 5.0
	_feedback_panel.add_theme_stylebox_override("panel", _feedback_style)
	_feedback_label = Label.new()
	UiTheme.style_label(_feedback_label, "", UiTheme.body_bold(), 20,
		Color.WHITE, HORIZONTAL_ALIGNMENT_CENTER, true)
	_feedback_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_feedback_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_feedback_panel.add_child(_feedback_label)
	add_child(_feedback_panel)
	_feedback_panel.visible = false


## Ulang pemasangan tooltip setelah bahasa aktif berubah.
func _rebuild_tooltips() -> void:
	if _toggle != null:
		_toggle.tooltip_text = MysticLocalization.tr_text("tac_toggle_tip")
	for action in _buttons:
		(_buttons[action] as Button).tooltip_text = _tooltip(action)


## Ambil manajer dari Main, bukan membuat state taktik kedua di HUD.
func _sync_feedback() -> void:
	if _feedback_panel == null:
		return
	var main = get_tree().get_first_node_in_group("main")
	var tac = main.get("_tactical") if main != null \
			and is_instance_valid(main) else null
	if tac == null or not is_instance_valid(tac) \
			or GameManager.in_menu:
		_feedback_panel.visible = false
		return
	var timer := int(tac.get("feedback_timer"))
	var text := str(tac.get("feedback_text"))
	if timer <= 0 or text.is_empty():
		_feedback_panel.visible = false
		return
	_feedback_panel.visible = true
	_feedback_label.text = text
	var alpha := 1.0
	var y_offset := 0.0
	if timer < 30:
		alpha = clampf(float(timer) / 30.0, 0.0, 1.0)
	elif timer > 150:
		var progress := clampf((180.0 - float(timer)) / 30.0,
			0.0, 1.0)
		alpha = progress
		y_offset = (1.0 - progress) * 20.0
	_feedback_panel.modulate = Color(1.0, 1.0, 1.0, alpha)
	_feedback_panel.offset_top = 68.0 + y_offset
	_feedback_panel.offset_bottom = 116.0 + y_offset
	var c = tac.get("feedback_color")
	if c is Color and _feedback_style != null:
		_feedback_style.border_color = Color(c.r, c.g, c.b, 0.95)

## Tooltip perintah lewat tabel teks (MysticLocalization) supaya pilihan
## English benar-benar berlaku di HUD, bukan hanya di menu. Kunci per aksi —
## daftar tertutupnya diaudit tools/test_godot_localization_parity.py.
const TOOLTIPS := {
	"gather": "tac_gather_tip",
	"protect_tower": "tac_protect_tower_tip",
	"protect_castle": "tac_protect_castle_tip",
	"attack_boss": "tac_attack_boss_tip",
	"attack_damage_dealer": "tac_attack_dd_tip",
}


static func _tooltip(action: String) -> String:
	var key := str(TOOLTIPS.get(action, ""))
	if key.is_empty():
		return ""
	return MysticLocalization.tr_text(key)

# ══════════════════════════════════════════════════════════
#  VISIBILITAS (port _gambar_tactical mobile/sidepanel.py)
# ══════════════════════════════════════════════════════════

## Segarkan visibilitas tombol dari kondisi medan live. Dipanggil _process
## dan oleh harness (production code yang sama, dipicu sinkron).
func _refresh() -> void:
	var playing := GameManager.state == "playing" and not GameManager.in_menu
	var has_rail := MobileLayout.tactical_rect().size.x > 0.0
	var modal := GameManager.shop_open
	if not playing or modal:
		_expanded = false
	_toggle.visible = playing and not has_rail and not modal
	_box.visible = playing and (has_rail or _expanded)
	if not playing:
		# pygame _tactical_sembunyikan: tombol tanpa gambar frame ini mati.
		for action in _buttons:
			(_buttons[action] as Button).visible = false
		return
	var alive_blue := 0
	for h in GameManager.owned_heroes("blue"):
		if is_instance_valid(h) and not bool(h.get("is_dead")):
			alive_blue += 1
	var alive_red := 0
	for h in GameManager.owned_heroes("red"):
		if is_instance_valid(h) and not bool(h.get("is_dead")):
			alive_red += 1
	var main = get_tree().get_first_node_in_group("main")
	var has_boss := false
	var held_cmd = null
	if main != null and is_instance_valid(main):
		var boss = main.get("active_boss")
		has_boss = boss != null and is_instance_valid(boss) \
			and not bool(boss.get("is_dead"))
		var tac = main.get("_tactical")
		if tac != null and is_instance_valid(tac):
			held_cmd = tac.get("held_command")
	# enabled persis _gambar_tactical: gather/castle > 0, tower >= 1,
	# boss aktif, dealer ada hero merah hidup. Tombol TAK PERNAH hilang:
	# yang tak memenuhi syarat tampil ABU + tak-bisa-ditekan (paritas
	# kotak abu pygame; hit-test-nya mati seperti btn.visible pygame).
	for action in _buttons:
		var enabled := false
		match str(action):
			"gather":
				enabled = alive_blue > 0
			"protect_tower":
				enabled = alive_blue >= 1
			"protect_castle":
				enabled = alive_blue > 0
			"attack_boss":
				enabled = has_boss
			"attack_damage_dealer":
				enabled = alive_red > 0
		var btn: Button = _buttons[action]
		btn.visible = true
		btn.disabled = not enabled
		btn.mouse_filter = Control.MOUSE_FILTER_STOP if enabled \
			else Control.MOUSE_FILTER_IGNORE
		# Sorot HOLD (paritas di_hold pygame): tombol menyala + chip.
		var held := enabled and held_cmd != null \
			and str(held_cmd) == str(action)
		var chip: Control = btn.get_node("HoldChip")
		chip.visible = held
		var base: Dictionary = _btn_base.get(str(action), {})
		var normal_sb := btn.get_theme_stylebox("normal") as StyleBoxFlat
		if held:
			btn.add_theme_color_override("font_color", Color.WHITE)
			if normal_sb != null and base.has("bg"):
				normal_sb.bg_color = (base["bg"] as Color).lightened(0.25)
		else:
			if base.has("font"):
				btn.add_theme_color_override("font_color", base["font"])
			if normal_sb != null and base.has("bg"):
				normal_sb.bg_color = base["bg"]

## Kamus ketersediaan tombol (dipakai harness paritas; cermin
## panel_available oracle dari _gambar_tactical pygame asli).
func panel_available() -> Dictionary:
	var out := {}
	for action in _buttons:
		var b := _buttons[action] as Button
		out[str(action)] = b.visible and not b.disabled
	return out

## Popup yang MENUTUPI panel perintah pygame (sidepanel.ada_popup_game):
## popup tower/nexus (popup_target), popup build slot, panel hero terpilih.
# Padanan Godot: ShopPanel terbuka DENGAN seleksi tower/nexus/slot, atau
# hero hidup sedang dipilih (SkillBar). Klik semacam itu harus sampai ke
# popup, bukan "tembus" ke tombol perintah di baliknya.
func _popup_blocks() -> bool:
	var sel = GameManager.selected_hero
	if sel != null and is_instance_valid(sel) and not bool(sel.get("is_dead")):
		return true
	if GameManager.shop_open:
		if GameManager.selected_tower != null or GameManager.selected_nexus != null:
			return true
		if int(GameManager.selected_slot) >= 0:
			return true
	return false

# ══════════════════════════════════════════════════════════
#  INPUT (port apply_hud_action + cabang release main.py)
# ══════════════════════════════════════════════════════════

func _on_button_down(action: String) -> void:
	var btn := _buttons.get(action) as Button
	# Tombol abu (syarat tak terpenuhi) tak bisa ditekan — paritas hit_test
	# pygame yang melewatkan tombol invisible. Button disabled Godot memang
	# tak memancarkan button_down, tapi guard eksplisit menutup jalur
	# pemanggilan langsung.
	if btn != null and (not btn.visible or btn.disabled):
		return
	var main = get_tree().get_first_node_in_group("main")
	if main == null or not is_instance_valid(main) \
			or not main.has_method("_tactical_panel_press"):
		return
	if _popup_blocks():
		return
	_held[action] = true
	main._tactical_panel_press(action)

func _on_button_up(action: String) -> void:
	_release_panel_hold(action)
	# Tanpa rail: panel kembali terlipat begitu perintah dilepas supaya map
	# tidak ditinggal tertutup kotak yang mengambang.
	_collapse_if_floating()


## Chip: buka/tutup panel command (hanya ada saat tidak ada rail).
func _on_toggle_pressed() -> void:
	set_expanded(not _expanded)


## Lipat lagi panel mengambang (dipakai setelah hold lepas & klik di luar).
func _collapse_if_floating() -> void:
	if _expanded and MobileLayout.tactical_rect().size.x <= 0.0:
		set_expanded(false)


## Titik ini milik panel/chip command? (klik di luar = lipat, event tetap
## diteruskan ke map oleh Main._unhandled_input.)
func _hit_panel(pos: Vector2) -> bool:
	if _box != null and _box.visible and _box.get_global_rect().has_point(pos):
		return true
	return _toggle != null and _toggle.visible \
		and _toggle.get_global_rect().has_point(pos)

## Rute pelepasan "claimed touch" pygame: main.py melepas hold berdasar
## touch-id yang diklaim tombol, APA PUN yang kini ada di bawah kursor.
## Godot: pelepasan klik kiri di mana pun melepas hold panel aktif (mouse
## fisik hanya satu, jadi setidaknya satu entri; multi-touch dirutekan
## per tombol lewat button_up di atas).
func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if not mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			for action in _held.keys():
				_release_panel_hold(str(action))
			return
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT \
				and _expanded and not _hit_panel(mb.position):
			# Klik di map saat panel mengambang terbuka: lipat lagi
			# (kebiasaan dropdown) — event TIDAK dikonsumsi, jadi kliknya
			# tetap sampai ke map lewat Main._unhandled_input.
			_collapse_if_floating()

func _release_panel_hold(action: String) -> void:
	if not _held.has(action):
		return
	_held.erase(action)
	var main = get_tree().get_first_node_in_group("main")
	if main != null and is_instance_valid(main) \
			and main.has_method("_tactical_panel_release"):
		main._tactical_panel_release(action)

## Lepas SEMUA hold panel (pause / aplikasi ke latar — mirror main.py
## `held_tac.clear()`; manager hold_end() tanpa nama dipanggil Main).
func release_all() -> void:
	_held.clear()
