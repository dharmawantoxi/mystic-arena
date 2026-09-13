# HUD.gd — Port _core.py Game._draw_gold_hud + _render.WaveAnnouncer + banner
# menang/kalah.
# Di Pygame: chip emas dan banner digambar manual tiap frame. Di Godot:
# Control statis untuk angka yang jarang berubah; bagian yang baru
# (banner victory/defeat, SkillBar, ShopPanel) dibangun dari kode supaya
# HUD.tscn tidak perlu dirombak.
#
# DUA DIHAPUS (permintaan user, 2026-09-13) — keduanya penemuan port, bukan
# pygame:
#   1. bar HP "RADIANT/DIRE NEXUS" tengah-atas arena (_draw_castle_bars,
#      blok 600x60 menutupi peta). HP/shield nexus hidup di castle masing-
#      masing (Nexus.gd) seperti pygame, yang hanya menggambar bar SHIELD
#      kecil + crest di atas kastil — lihat Nexus._draw_overlays.
#   2. baris teks DI BAWAH badge LEVEL/WAVE: "medan: n hero · n minion · …"
#      (FieldStatus) dan "difficulty: … · gold x…" (DifficultyLabel).
#      pygame tidak punya dua baris itu; chip emas + badge level/wave +
#      banner wave adalah seluruh HUD-nya.
#
# Teks HUD (baris hint) dibaca lewat MysticLocalization supaya pilihan
# "English" di SETTINGS berlaku di dalam game.
extends Control

const SkillBarScript = preload("res://scenes/ui/SkillBar.gd")
const ShopPanelScript = preload("res://scenes/ui/ShopPanel.gd")
const ComboBadgeScript = preload("res://scenes/ui/ComboBadge.gd")
const AchievementPopupScript = preload("res://scenes/ui/AchievementPopup.gd")
const TacticalBarScript = preload("res://scenes/ui/TacticalBar.gd")
const SidePanelScript = preload("res://scenes/ui/SidePanel.gd")
const WavePlateScript = preload("res://scenes/ui/widgets/WavePlate.gd")
const TouchHUDScript = preload("res://scenes/ui/TouchHUD.gd")

var _banner_tween: Tween
var _wave_sub: Label = null
## Dekorasi banner wave (port WaveAnnouncer): panel di belakang teks +
## bayangan teks +2/+2 — keduanya ikut tween slide/alpha banner.
var _wave_plate: Control = null
var _wave_shadow: Label = null
var _over_root: GameOverOverlay = null
var _over_panel: PanelContainer = null
var _over_title: Label = null
var _over_stats: Label = null
var _over_body: Label = null
var _next_button: Button = null
## Baris HBoxContainer hint bar (isi digantikan _refresh_hints per konteks)
var _hint_row: HBoxContainer = null
var _combo_badge: Control = null
var _achievement_popup: Control = null
## Overlay FPS (target tombol debug TouchHUD) — dibuat malas, mati default.
var _debug_overlay: Label = null

@onready var gold_label: Label = $TopLeft/GoldChip/GoldRow/GoldValue
@onready var income_label: Label = $TopLeft/GoldChip/GoldRow/IncomeValue
@onready var level_label: Label = $TopLeft/LevelBadge/LevelRow/LevelValue
@onready var wave_label: Label = $TopLeft/LevelBadge/LevelRow/WaveValue
@onready var wave_banner: Label = $WaveBanner

func _ready():
	wave_banner.modulate.a = 0.0
	wave_banner.set_meta("base_l", wave_banner.offset_left)
	wave_banner.set_meta("base_r", wave_banner.offset_right)
	_build_wave_sub()
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.wave_started.connect(_on_wave_started)
	GameManager.level_started.connect(_on_level_started)
	# FASE 24 — ControllerRouter mencari HUD lewat grup ini untuk aksi
	# stick_left/F8 (pygame: fps_counter.toggle()).
	add_to_group("hud")
	GameManager.game_over.connect(_on_game_over)
	GameManager.shop_changed.connect(_on_shop_changed)
	# Bahasa antarmuka berganti -> baris hint dibangun ulang (satu-satunya
	# teks HUD yang punya padanan Indonesia/Inggris; "LEVEL"/"WAVE" dan
	# label banner mengikuti pygame dan identik di kedua bahasa).
	GameManager.language_changed.connect(_on_language_changed)
	_build_game_over_panel()
	_build_hint_bar()
	# ── Z-ORDER HUD (bawah -> atas) ──
	# 1. SidePanel  : dinding batu panel kanan (latar semua kontrol rail),
	# 2. TacticalBar: 5 tombol command DI ATAS dinding (harus bisa diklik),
	# 3. SkillBar   : bar skill hero,
	# 4. ShopPanel  : popup/modal toko — PALING ATAS supaya klik popup tidak
	#    tembus ke tombol rail di baliknya (paritas ada_popup_game pygame).
	var side_panel = SidePanelScript.new()
	side_panel.name = "SidePanel"
	add_child(side_panel)
	# FASE 18 — panel TACTICAL COMMANDS (HOLD): pemicu UI perintah taktis
	# (port sidepanel _gambar_tactical + apply_hud_action; tekan/lepas =
	# hold_start/hold_end di TacticalCommands.gd).
	var tactical_bar = TacticalBarScript.new()
	tactical_bar.name = "TacticalBar"
	add_child(tactical_bar)
	add_child(SkillBarScript.new())
	add_child(ShopPanelScript.new())
	# FASE 13 — klaster skor: badge combo kanan-atas (port ComboCounter.draw)
	# + popup achievement di layar arena (port AchievementPopup; trigger
	# GameManager.unlock_achievement, mis. NEW HERO UNLOCKED! saat menang).
	_combo_badge = ComboBadgeScript.new()
	_combo_badge.name = "ComboBadge"
	add_child(_combo_badge)
	_achievement_popup = AchievementPopupScript.new()
	_achievement_popup.name = "AchievementPopup"
	add_child(_achievement_popup)
	# FASE 23 — tombol sentuh (port mobile/hud.py TouchHUD): PALING ATAS —
	# pygame menggambar hud.draw() TERAKHIR di STATE_GAME (main.py:560),
	# di atas overlay game-over & popup. Main.gd menyambung hud_action.
	var touch_hud = TouchHUDScript.new()
	touch_hud.name = "TouchHUD"
	add_child(touch_hud)
	GameManager.achievement_unlocked.connect(
		_achievement_popup.unlock)
	GameManager.boss_reward_effects_tick.connect(_achievement_popup.tick)
	refresh()


func _process(_delta: float) -> void:
	if _debug_overlay != null and _debug_overlay.visible:
		_refresh_debug_overlay()
	_sync_hint_visibility()


## Paritas _draw_input_hints (_core.py:2701-2736): bar digambar hanya saat
## controller mode, dan TIDAK selama cinematic aktif (prompt skip digambar
## sendiri oleh layar intro/banner/perayaan).
func _sync_hint_visibility() -> void:
	var host: Label = get_node_or_null(^"HintLabel")
	if host == null:
		return
	var mgr = _controller_mgr()
	var on: bool = mgr != null and bool(mgr.is_controller_mode())
	if on:
		var m = get_tree().get_first_node_in_group("main")
		if m != null and is_instance_valid(m) and m.has_method("_cinematic_active") \
				and m._cinematic_active():
			on = false
	if host.visible != on:
		host.visible = on
		if on:
			_refresh_hints()


# ══════════════════════════════════════════════════════════
#  OVERLAY DEBUG (target tombol FPS TouchHUD)
# ══════════════════════════════════════════════════════════

## Overlay FPS (paritas esensi mobile/debug.py DebugOverlay — BUKAN port
## penuh: pygame 450 baris dengan 4 mode + grafik frame + log periodik.
## Yang dibawa hanya info baris [PERF]-nya: FPS + ms/frame + hitungan unit.
## Mati default; tombol FPS-nya sendiri env-gated MYSTIC_DEBUG=1 di kedua
## engine, jadi overlay ini tak pernah muncul di rilis tanpa sengaja.)
func toggle_debug_overlay() -> void:
	if _debug_overlay == null:
		_build_debug_overlay()
	_debug_overlay.visible = not _debug_overlay.visible
	print("[HUD] overlay debug %s" % ("ON" if _debug_overlay.visible else "OFF"))


func _build_debug_overlay() -> void:
	var lab := Label.new()
	lab.name = "DebugOverlay"
	lab.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lab.anchor_left = 0.5
	lab.anchor_right = 0.5
	lab.offset_left = -320.0
	lab.offset_right = 320.0
	lab.offset_top = 78.0
	lab.offset_bottom = 100.0
	lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UiTheme.style_label(lab, "", UiTheme.body_bold(), 14,
		Color("#78c8ff"))
	lab.add_theme_color_override("font_outline_color",
		Color(0.0, 0.0, 0.0, 0.9))
	lab.add_theme_constant_override("outline_size", 4)
	lab.visible = false
	add_child(lab)
	_debug_overlay = lab


func _refresh_debug_overlay() -> void:
	if _debug_overlay == null or not _debug_overlay.visible:
		return
	var tree := get_tree()
	var heroes := 0
	for h in tree.get_nodes_in_group("heroes"):
		if is_instance_valid(h) and not bool(h.get("is_dead")):
			heroes += 1
	var minions := 0
	for m in tree.get_nodes_in_group("minions"):
		if is_instance_valid(m) and not bool(m.get("is_dead")):
			minions += 1
	var towers := 0
	for t in tree.get_nodes_in_group("towers"):
		if is_instance_valid(t) and not bool(t.get("is_dead")):
			towers += 1
	var bosses := 0
	for b in tree.get_nodes_in_group("bosses"):
		if is_instance_valid(b) and not bool(b.get("is_dead")):
			bosses += 1
	_debug_overlay.text = "%d FPS · %.1f ms · H%d M%d T%d B%d" % [
		int(Engine.get_frames_per_second()),
		# get_process_delta_time milik Node (bukan static Engine).
		get_process_delta_time() * 1000.0,
		heroes, minions, towers, bosses]

# Sinkronkan seluruh HUD dari state GameManager (dipakai saat _ready + level_started)
func refresh():
	_on_gold_changed(GameManager.gold)
	# "LEVEL"/"WAVE" dipakai apa adanya di kedua bahasa — persis teks
	# `WaveAnnouncer`/badge pygame (kata serapan, bukan terjemahan).
	level_label.text = "LEVEL %d" % GameManager.level_number
	wave_label.text = "WAVE %d" % GameManager.wave_number

func _on_gold_changed(new_gold: int):
	gold_label.text = _format_thousands(new_gold)
	income_label.text = "+%s/s" % _format_gold_rate(GameManager.gold_per_second)

func _on_level_started(_level_num: int):
	if _achievement_popup != null:
		_achievement_popup.reset()
	# Level baru (PLAY/ENTER-next/R) -> sembunyikan panel menang/kalah lama.
	if _over_root != null:
		_over_root.hide_overlay()
	_refresh_hints()
	refresh()

func _on_wave_started(wave_num: int):
	wave_label.text = "WAVE %d" % wave_num
	announce_wave(wave_num)

# Subtitle banner ("E N E M I E S   I N C O M I N G") — posisi di bawah judul.
func _build_wave_sub() -> void:
	_wave_sub = Label.new()
	_wave_sub.name = "WaveSub"
	_wave_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_wave_sub.anchor_left = 0.5
	_wave_sub.anchor_top = 0.5
	_wave_sub.anchor_right = 0.5
	_wave_sub.anchor_bottom = 0.5
	_wave_sub.offset_left = -300.0
	_wave_sub.offset_top = -66.0
	_wave_sub.offset_right = 300.0
	_wave_sub.offset_bottom = -36.0
	_wave_sub.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_wave_sub.grow_vertical = Control.GROW_DIRECTION_BOTH
	_wave_sub.add_theme_font_override("font", UiTheme.body_semibold())
	_wave_sub.add_theme_font_size_override("font_size", 22)
	_wave_sub.add_theme_color_override("font_color", Color(0.78, 0.78, 0.86))
	_wave_sub.add_theme_color_override("font_outline_color", Color(0.03, 0.03, 0.05, 1))
	_wave_sub.add_theme_constant_override("outline_size", 4)
	_wave_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_wave_sub.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_wave_sub.modulate.a = 0.0
	_wave_sub.set_meta("base_l", _wave_sub.offset_left)
	_wave_sub.set_meta("base_r", _wave_sub.offset_right)
	add_child(_wave_sub)
	_build_wave_decor()


## Dekorasi banner wave (port WaveAnnouncer.draw _render.py:1022-1103):
## panel 400x80 (gradasi + border emas + diagonal + corner ticks) di
## belakang teks, pusatnya +8px di bawah pusat teks, dan bayangan teks
## (8,8,14) offset +2/+2. Urutan gambar: plate -> shadow -> banner teks
## (pygame: blit panel, lalu shadow, lalu teks gradasi). Warna teks banner
## memakai puncak gradien pygame (255,242,175) — gradien per-glyph sendiri
## masih milik bucket piksel (kebijakan gradasi-pendekatan).
func _build_wave_decor() -> void:
	# Paritas warna: pygame gradasi (255,242,175)->(196,138,40); Godot flat
	# diambil puncaknya + outline dimatikan (pygame memakai shadow, bukan
	# outline).
	wave_banner.add_theme_color_override("font_color",
		Color(1.0, 242.0 / 255.0, 175.0 / 255.0))
	wave_banner.add_theme_constant_override("outline_size", 0)
	_wave_plate = WavePlateScript.new()
	_wave_plate.name = "WavePlate"
	_wave_plate.offset_left = -200.0
	_wave_plate.offset_right = 200.0
	_wave_plate.offset_top = -112.0 # pusat panel = pusat teks + 8px
	_wave_plate.offset_bottom = -32.0
	_wave_plate.modulate.a = 0.0
	add_child(_wave_plate)
	_wave_shadow = Label.new()
	_wave_shadow.name = "WaveShadow"
	_wave_shadow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_wave_shadow.anchor_left = 0.5
	_wave_shadow.anchor_top = 0.5
	_wave_shadow.anchor_right = 0.5
	_wave_shadow.anchor_bottom = 0.5
	_wave_shadow.offset_left = -298.0 # base banner +2/+2 (shadow pygame)
	_wave_shadow.offset_right = 302.0
	_wave_shadow.offset_top = -138.0
	_wave_shadow.offset_bottom = -18.0
	_wave_shadow.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_wave_shadow.grow_vertical = Control.GROW_DIRECTION_BOTH
	_wave_shadow.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_wave_shadow.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_wave_shadow.add_theme_font_override("font", UiTheme.title_font())
	_wave_shadow.add_theme_font_size_override("font_size", 46)
	_wave_shadow.add_theme_color_override("font_color",
		Color(8.0 / 255.0, 8.0 / 255.0, 14.0 / 255.0, 200.0 / 255.0))
	_wave_shadow.modulate.a = 0.0
	add_child(_wave_shadow)
	# Urutan gambar (bawah -> atas): plate, shadow, WaveBanner, WaveSub.
	move_child(_wave_plate, wave_banner.get_index())
	move_child(_wave_shadow, wave_banner.get_index())
	# Meta base offset utk kurva slide tween announce_wave.
	_wave_plate.set_meta("base_l", _wave_plate.offset_left)
	_wave_plate.set_meta("base_r", _wave_plate.offset_right)
	_wave_shadow.set_meta("base_l", _wave_shadow.offset_left)
	_wave_shadow.set_meta("base_r", _wave_shadow.offset_right)


## Banner "WAVE N" — port gerak WaveAnnouncer: slide-in 0.4s (BACK OUT =
## ease_out_back, c1 1.70158 sama) -> tahan 1.0s -> slide-out 0.6s (BACK IN).
## Kurva frame-per-frame dikunci di HudLayout.wave_slide_x (120 titik fixture).
func announce_wave(wave_num: int):
	wave_banner.text = HudLayout.wave_title(wave_num)
	_wave_sub.text = HudLayout.wave_subtitle()
	if _banner_tween and _banner_tween.is_valid():
		_banner_tween.kill()
	wave_banner.scale = Vector2.ONE
	_banner_tween = create_tween()
	_banner_tween.set_parallel(true)
	_banner_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	for lab in [wave_banner, _wave_sub]:
		var base_l := float(lab.get_meta("base_l"))
		var base_r := float(lab.get_meta("base_r"))
		lab.offset_left = base_l - 1280.0
		lab.offset_right = base_r - 1280.0
		lab.modulate.a = 0.0
		_banner_tween.tween_property(lab, "offset_left", base_l, HudLayout.WAVE_TWEEN_IN)
		_banner_tween.tween_property(lab, "offset_right", base_r, HudLayout.WAVE_TWEEN_IN)
		_banner_tween.tween_property(lab, "modulate:a", 1.0, HudLayout.WAVE_TWEEN_IN)
	_banner_tween.set_parallel(false)
	_banner_tween.tween_interval(HudLayout.WAVE_TWEEN_HOLD)
	_banner_tween.set_parallel(true)
	_banner_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	for lab in [wave_banner, _wave_sub, _wave_shadow, _wave_plate]:
		var base_l := float(lab.get_meta("base_l"))
		var base_r := float(lab.get_meta("base_r"))
		_banner_tween.tween_property(lab, "offset_left", base_l + 1280.0, HudLayout.WAVE_TWEEN_OUT)
		_banner_tween.tween_property(lab, "offset_right", base_r + 1280.0, HudLayout.WAVE_TWEEN_OUT)
		_banner_tween.tween_property(lab, "modulate:a", 0.0, HudLayout.WAVE_TWEEN_OUT)

# 1234567 -> "1,234,567" — kanon HudLayout, delegasi tipis (dipakai income_label).
static func _format_thousands(n: int) -> String:
	return HudLayout.format_thousands(n)

# 3.0 -> "3", 5.7 -> "5.7", 3.75 -> "3.8" — kanon HudLayout, delegasi tipis.
static func _format_gold_rate(rate: float) -> String:
	return HudLayout.format_gold_rate(rate)


# ══════════════════════════════════════════════════════════
#  BANNER MENANG/KALAH
# ══════════════════════════════════════════════════════════

func _build_game_over_panel() -> void:
	# Overlay VICTORY/DEFEAT penuh (port Overlay.draw) — dibangun &
	# dimiliki GameOverOverlay; member audit di-alias ke sana.
	_over_root = GameOverOverlay.new()
	add_child(_over_root)
	_over_root.menu_requested.connect(_goto_main_menu)
	# Panel stat dibuat saat show_result; alias awal null-aman di bawah.
	_over_panel = null
	_over_title = _over_root.title_label
	_over_stats = _over_root.stats_label
	_over_body = _over_root.body_label
	_next_button = null
func _goto_main_menu() -> void:
	if _over_root != null:
		_over_root.hide_overlay()
	var main = get_tree().get_first_node_in_group("main")
	if main != null and is_instance_valid(main) and main.has_method("_on_menu_main_menu"):
		main.call("_on_menu_main_menu")
		return
	# fallback kalau scene uji tidak memasang Main.gd
	GameManager.return_to_menu()
	var menu = get_tree().get_first_node_in_group("main_menu")
	if menu != null and is_instance_valid(menu) and menu.has_method("show_main"):
		menu.show_main()


func _on_game_over(victory: bool) -> void:
	if _over_root == null:
		return
	_over_root.show_result(victory)
	# Panel stat & tombol next dibuat ulang tiap result — alias ulang.
	_over_panel = _over_root.stats_panel
	_next_button = _over_root.next_button


# ══════════════════════════════════════════════════════════
#  HINT BAR (port draw_hint_bar: keycap + label, tengah-bawah)
# ══════════════════════════════════════════════════════════

## Baris hint per konteks — port InputManager.get_hints (_core.py:10102)
## dengan label keyboard port Godot (bukan tabel controller pygame) dan
## bahasa Indonesia (kebijakan UI Godot). B/D TIDAK ada di daftar: sejak
## FASE 18 keduanya hotkey perintah taktis (ATTACK BOSS / ATTACK TOP
## DEALER), bukan toko/difficulty; toko = H, dan SPASI hanya melewati
## intro (level/boss) — paritas _draw_input_hints yang mematikan hint
## selama cinematic (_core.py:2720-2727).
## Mode controller = tabel label PERSIS pygame (get_hints bahasa Inggris);
## keyboard = label Indonesia Godot (bar-nya toh tersembunyi di mode itu).
func _controller_mgr():
	var tree := get_tree()
	if tree == null:
		return null
	var mgr = tree.get_first_node_in_group("controller")
	if mgr == null or not is_instance_valid(mgr):
		return null
	return mgr


func _hint_rows(context: String) -> Array:
	var mgr = _controller_mgr()
	if mgr != null and mgr.is_controller_mode():
		var rows: Array = []
		for h in mgr.get_hints(context):
			rows.append([str(h[0]), str(h[1])])
		return rows
	var click := _loc("hud_hint_click")
	var right_click := _loc("hud_hint_right_click")
	match context:
		"victory":
			return [["ENTER", _loc("hud_hint_next")],
				["R", _loc("hud_hint_replay")], ["ESC", _loc("hud_hint_menu")]]
		"defeat":
			return [["R", _loc("hud_hint_replay")], ["ESC", _loc("hud_hint_menu")]]
		"shop":
			return [[click, _loc("hud_hint_buy")], ["H", _loc("hud_hint_close")]]
		_:
			return [
				[click, _loc("hud_hint_select")],
				["QWER", _loc("hud_hint_skill")],
				["H", _loc("hud_hint_shop")],
				[right_click, _loc("hud_hint_close")],
				["P", _loc("hud_hint_pause")],
			]


## Konteks aktif dihitung ulang dari state GameManager — prioritas persis
## _draw_input_hints (_core.py:2721-2731): victory > defeat > shop > game.
## Dipanggil dari sinyal game_over / level_started / shop_changed.
func _refresh_hints() -> void:
	var ctx := "game"
	if GameManager.state == "victory":
		ctx = "victory"
	elif GameManager.state == "defeat":
		ctx = "defeat"
	elif GameManager.shop_open:
		ctx = "shop"
	if _hint_row == null:
		return
	for c in _hint_row.get_children():
		_hint_row.remove_child(c)
		c.queue_free()
	for h in _hint_rows(ctx):
		_hint_row.add_child(_hint_item(str(h[0]), str(h[1])))


func _on_shop_changed() -> void:
	_refresh_hints()


## Bahasa berganti -> baris hint ditulis ulang (panel lain punya hook sendiri).
func _on_language_changed(_language: String) -> void:
	_refresh_hints()


## Pintu teks HUD ke tabel teks bersama (localization.py <-> Localization.gd).
func _loc(key: String) -> String:
	return MysticLocalization.tr_text(key)


func _build_hint_bar() -> void:
	var host: Label = $HintLabel
	host.text = ""
	var bg := PanelContainer.new()
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.set_anchors_preset(Control.PRESET_CENTER)
	bg.grow_horizontal = Control.GROW_DIRECTION_BOTH
	bg.grow_vertical = Control.GROW_DIRECTION_BOTH
	var bgsb := StyleBoxFlat.new()
	bgsb.bg_color = Color(0, 0, 0, 140.0 / 255.0)
	bgsb.set_corner_radius_all(6)
	bgsb.content_margin_left = 7.0
	bgsb.content_margin_right = 7.0
	bgsb.content_margin_top = 4.0
	bgsb.content_margin_bottom = 4.0
	bg.add_theme_stylebox_override("panel", bgsb)
	host.add_child(bg)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.add_child(row)
	_hint_row = row
	_refresh_hints()
	# ── KEBIJAKAN TAMPIL (paritas _draw_input_hints _core.py:2709-2714) ──
	# Pygame menggambar hint bar HANYA di mode CONTROLLER (tanpa
	# controller_mgr / mode keyboard = return tanpa menggambar); build
	# Android pygame (main.py:250) bahkan tidak memasang controller_mgr.
	# FASE 24 memport lapisan gamepad, jadi bar ini kini HIDUP saat mode
	# controller dan tetap SEMBUNYI untuk keyboard/sentuh — diperiksa tiap
	# frame di _process (mode bisa berganti lewat tombol INPUT di menu).
	_sync_hint_visibility()


func _hint_item(key: String, desc: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 5)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var cap := PanelContainer.new()
	cap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(48.0 / 255.0, 52.0 / 255.0, 70.0 / 255.0)
	sb.border_color = Color(120.0 / 255.0, 130.0 / 255.0, 165.0 / 255.0)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 5.0
	sb.content_margin_right = 5.0
	sb.content_margin_top = 1.0
	sb.content_margin_bottom = 1.0
	cap.add_theme_stylebox_override("panel", sb)
	row.add_child(cap)
	var k := Label.new()
	UiTheme.style_label(k, key, UiTheme.body_bold(), 15,
		Color(1.0, 235.0 / 255.0, 140.0 / 255.0))
	cap.add_child(k)
	var d := Label.new()
	UiTheme.style_label(d, desc, UiTheme.body_medium(), 15,
		Color(205.0 / 255.0, 210.0 / 255.0, 225.0 / 255.0))
	d.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(d)
	return row
