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
# (panel_available) + jejak hold_start/hold_end. PIKSEL (chip "HOLD",
# sorot warna, font persis sidepanel) = aproksimasi, BELUM TERUJI.
extends Control

const COMMANDS: Array = [
	["gather", "GATHER [G]", Color(0.39, 0.62, 1.0)],
	["protect_tower", "PROTECT TOWER [T]", Color(0.40, 0.90, 0.47)],
	["protect_castle", "PROTECT CASTLE [C]", Color(1.0, 0.80, 0.33)],
	["attack_boss", "ATTACK BOSS [B]", Color(0.95, 0.35, 0.35)],
	["attack_damage_dealer", "ATTACK DMG DEALER [D]", Color(0.72, 0.51, 1.0)],
]

var _box: PanelContainer = null
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
## True hanya kalau layar menyisakan rail untuk kotak command (lihat
## _layout). Tanpa rail kotak TIDAK digambar — peta tidak boleh tertutup.
var _has_slot: bool = false

func _ready() -> void:
	name = "TacticalBar"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_to_group("tactical_bar")
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build()
	MobileLayout.layout_changed.connect(_layout)
	_layout()
	GameManager.selection_changed.connect(_refresh)
	GameManager.shop_changed.connect(_refresh)
	GameManager.game_over.connect(func(_v): _refresh())
	GameManager.hero_died.connect(func(_h): _refresh())
	GameManager.boss_spawned.connect(func(_b): _refresh())
	GameManager.tower_destroyed.connect(func(_t, _k): _refresh())
	_refresh()

## Tempatkan kotak command di dasar panel kanan (paritas _gambar_tactical).
##
## TANPA RAIL = TANPA KOTAK. Layar 16:9 atau lebih sempit tidak menyisakan
## ruang di luar arena (x < 1280 semua milik peta), dan pygame memang tidak
## menggambar tombol command sama sekali di sana (SidePanel tidak aktif ->
## `draw`/`hit_test` keluar lebih awal). Versi lama kotak ini "jatuh" ke
## sudut kanan-bawah ARENA — menutupi peta persis saat pemain perlu
## melihatnya. Sekarang kotak disembunyikan; perintah taktis tetap bisa
## dipakai lewat hotkey G/F/T/C/B/D (Main._tactical_hotkey), sama seperti
## pygame di 16:9.
func _layout() -> void:
	if _box == null:
		return
	var rect := MobileLayout.tactical_rect()
	# Invariant keras: kotak command tidak pernah menyentuh peta. Cek
	# intersects juga menolak rect kosong (Rect2() = 0x0) sehingga satu
	# kondisi ini sekaligus menangani "rail tidak ada".
	_has_slot = rect.size.x > 0.0 and rect.size.y > 0.0 \
		and not rect.intersects(MobileLayout.arena_rect())
	_box.mouse_filter = Control.MOUSE_FILTER_STOP if _has_slot \
		else Control.MOUSE_FILTER_IGNORE
	if not _has_slot:
		_box.visible = false
		return
	_box.position = rect.position
	_box.size = rect.size
	_refresh()

## Rect efektif kotak command (Rect2() kosong saat tidak ada rail).
## Dipakai harness paritas: inilah yang dijamin tidak menutupi peta.
func command_rect() -> Rect2:
	if not _has_slot or _box == null:
		return Rect2()
	return Rect2(_box.position, _box.size)


func _process(delta: float) -> void:
	# Visibilitas tombol mengikuti kondisi medan (hero hidup / boss aktif).
	# 5 Hz cukup (paritas draw per-frame pygame bukan target piksel).
	_timer += delta
	if _timer >= 0.2:
		_timer = 0.0
		_refresh()

func _build() -> void:
	_box = PygamePanel.new(Color(0.32, 0.38, 0.55, 0.9), 2.0, 9.0)
	_box.name = "TacticalBox"
	_box.mouse_filter = Control.MOUSE_FILTER_STOP
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

static func _tooltip(action: String) -> String:
	match action:
		"gather":
			return "Semua hero kumpul & serang bersama (tahan untuk terus aktif)"
		"protect_tower":
			return "Min 2 hero lindungi tower (tahan untuk terus aktif)"
		"protect_castle":
			return "Semua hero lindungi castle (tahan untuk terus aktif)"
		"attack_boss":
			return "Semua hero serang boss (tahan untuk terus aktif)"
		"attack_damage_dealer":
			return "Fokus hero musuh damage terbesar (tahan untuk terus aktif)"
	return ""

# ══════════════════════════════════════════════════════════
#  VISIBILITAS (port _gambar_tactical mobile/sidepanel.py)
# ══════════════════════════════════════════════════════════

## Segarkan visibilitas tombol dari kondisi medan live. Dipanggil _process
## dan oleh harness (production code yang sama, dipicu sinkron).
func _refresh() -> void:
	var playing := GameManager.state == "playing" and not GameManager.in_menu
	# Kotak hanya tampil saat match berjalan DAN layar punya rail (x >= 1280).
	# Tanpa rail tidak ada tempat di luar peta, jadi kotak tidak digambar.
	_box.visible = playing and _has_slot
	if not playing or not _has_slot:
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
