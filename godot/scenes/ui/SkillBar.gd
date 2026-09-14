# SkillBar.gd — panel hero kiri-bawah + 4 tombol skill (QWER).
#
# Port HeroPanel pygame (ui_components: panel 280x276 @ (20, H-296),
# gradasi + border warna tim + sudut emas): nama + chip Lv + tombol X,
# HP bar premium, 4 slot skill 38px-rasa (di sini 54px agar muat nama),
# toggle auto-cast, 6 slot item 30px (ikon assets/items/ lewat ItemIcons.gd),
# ITEM FORGE, upgrade.
#
# Sumber kebenaran = GameManager.selected_hero. Tombol skill dan keyboard
# QWER memanggil jalur yang sama (hero.cast_q/w/e/r), jadi tidak ada
# duplikasi logika. SEMUA teks + member + callback = 1:1 versi lama
# (dikunci UiHudParityTest); yang berubah hanya visual & geometri.
#
# Teks panel (label "tidak ada hero", petunjuk, tooltip) sejak 2026-09-13
# lewat MysticLocalization supaya pilihan bahasa di SETTINGS benar-benar
# berlaku di dalam game. Nilai "id" tabel = teks lama, jadi tampilan
# Indonesia tidak berubah; "en" adalah padanan Inggrisnya.
extends Control

const SkillButtonScript = preload("res://scenes/ui/SkillButton.gd")
const SKILL_KEYS: Array = ["q", "w", "e", "r"]
const ITEM_SLOTS: int = 6
## Chrome slot item — paritas hero_items.py:3026 (bg (14,17,30) radius 5)
## dan :3092 (border warna katalog 2 px kalau terisi, (66,74,104) 1 px kalau
## kosong). Ikonnya 26 px = SLOT_SIZE 30 - 4 di inset 2 (:3080-3082); di sini
## digambar engine lewat Button.expand_icon (content area chip 30 - border 2
## = 26 px, jadi skalanya keluar sama tanpa hitung manual).
const SLOT_BG := Color(14.0 / 255.0, 17.0 / 255.0, 30.0 / 255.0)
const SLOT_BORDER_EMPTY := Color(66.0 / 255.0, 74.0 / 255.0, 104.0 / 255.0)
const SLOT_BORDER_FILLED := 2
## Kotak slot item 30 px — paritas hero_items.py:3010 (cls.SLOT_SIZE).
const SLOT_SIZE_PX := 30.0
## Seberapa sering angka HP/cooldown disinkronkan (20 Hz cukup halus, hemat)
const REFRESH_INTERVAL := 0.05
const PANEL_W := 280.0
const PANEL_H := 276.0

var _root: PygamePanel = null
var _info: VBoxContainer = null
var _name_label: Label = null
var _level_label: Label = null
var _close_btn: Button = null
var _hp_bar: ProgressBar = null
var _hp_label: Label = null
var _stats_label: Label = null
var _item_row: HBoxContainer = null
var _item_chips: Array = []
var _autocast_btn: Button = null
var _forge_btn: Button = null
var _upgrade_btn: Button = null
var _buttons: Dictionary = {}
var _hero = null
var _timer: float = 0.0


func _ready() -> void:
	name = "SkillBar"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	MobileLayout.fill_parent(self)
	_build()
	MobileLayout.layout_changed.connect(_layout)
	GameManager.selection_changed.connect(_on_selection_changed)
	GameManager.hero_died.connect(_on_hero_died)
	GameManager.shop_changed.connect(_refresh_static)
	# Bahasa aktif berganti (SETTINGS/pause) -> label + tooltip panel dibaca
	# ulang; semua teks panel lewat _loc(), padanan tr() pygame.
	GameManager.language_changed.connect(_on_language_changed)
	_layout()
	_on_selection_changed()


## Panel hero diletakkan mengikuti MobileLayout: DI DALAM rail kanan kalau
## ada & cukup lebar (paritas HeroPanel pygame + platform_utils.panel_pos_bawah),
## kalau tidak kiri-bawah arena (fallback pygame 20, H-276-20).
##
## Tingginya diambil dari ukuran MINIMAL konten, bukan 276 buta: tombol
## UPGRADE HERO adalah anak TERAKHIR kolom, jadi kalau kontennya lebih tinggi
## dari 276 (font HP/resolusi beda) tombol itu dulu terdorong ke luar panel
## dan tak pernah kelihatan. Sekarang panelnya ikut memuai.
func _layout() -> void:
	if _root == null:
		return
	var h := maxf(PANEL_H, _root.get_combined_minimum_size().y)
	var rect := MobileLayout.hero_panel_rect(PANEL_W, h)
	_root.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_root.position = rect.position
	_root.size = rect.size


func _build() -> void:
	# Panel 280x276 (paritas HeroPanel pygame). Anchor kiri-atas; posisinya
	# ditentukan _layout() — rail kanan bila ada, kalau tidak kiri-bawah.
	_root = PygamePanel.new(Color(0.35, 0.5, 0.95), 2.0, 10.0)
	_root.name = "BarRoot"
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.set_anchors_preset(Control.PRESET_TOP_LEFT)
	# Nilai awal = fallback pygame (20, H-296); _layout() menimpanya sebelum
	# frame pertama (rail kanan kalau ada, kiri-bawah kalau tidak).
	_root.offset_left = 20.0
	_root.offset_right = 20.0 + PANEL_W
	_root.offset_top = 720.0 - PANEL_H - 20.0
	_root.offset_bottom = 720.0 - 20.0
	_root.set_margins(12, 10, 12, 10)
	# Panel hero pygame HANYA digambar saat ada hero terpilih (HeroPanel.draw
	# `if not h or not h.alive: return`). Di Godot dulu panelnya SELALU ada
	# dengan teks "tidak ada hero dipilih" + tombol upgrade kosong, menutupi
	# map kiri-bawah (base Radiant) dan menelan ketukan hero di sana —
	# hero jadi tak bisa diklik, popup upgrade-nya pun tak pernah muncul.
	_root.visible = false
	add_child(_root)

	_info = VBoxContainer.new()
	_info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info.add_theme_constant_override("separation", 3)
	_root.add_child(_info)

	# Baris nama: "Kaizen" + "Lv.1" + tombol tutup X (paritas teks panel).
	var name_row := HBoxContainer.new()
	name_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	name_row.add_theme_constant_override("separation", 8)
	_info.add_child(name_row)
	_name_label = Label.new()
	_name_label.add_theme_font_override("font", UiTheme.body_medium())
	_name_label.add_theme_font_size_override("font_size", 22)
	_name_label.add_theme_color_override("font_color", UiTheme.TEXT_WHITE)
	_name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name_label.clip_text = true
	_name_label.text = _loc("skillbar_no_hero")
	name_row.add_child(_name_label)
	_level_label = Label.new()
	_level_label.add_theme_font_override("font", UiTheme.body_bold())
	_level_label.add_theme_font_size_override("font_size", 16)
	_level_label.add_theme_color_override("font_color", UiTheme.GOLD_TEXT)
	_level_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_level_label.text = ""
	name_row.add_child(_level_label)
	_close_btn = Button.new()
	_close_btn.text = "X"
	_close_btn.custom_minimum_size = Vector2(22, 22)
	_close_btn.focus_mode = Control.FOCUS_NONE
	_close_btn.tooltip_text = _loc("skillbar_close_tip")
	_close_btn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	UiTheme.apply_row_button(_close_btn, "danger", 13, false)
	_close_btn.pressed.connect(_on_close_pressed)
	name_row.add_child(_close_btn)

	# HP bar premium (h=8) + teks HP di bawahnya.
	_hp_bar = ProgressBar.new()
	_hp_bar.custom_minimum_size = Vector2(0, 8)
	_hp_bar.max_value = 100.0
	_hp_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_progress_bar(_hp_bar, Color(120.0 / 255.0, 220.0 / 255.0,
		120.0 / 255.0), Color(16.0 / 255.0, 18.0 / 255.0, 30.0 / 255.0), 4)
	_info.add_child(_hp_bar)
	_hp_label = Label.new()
	_hp_label.add_theme_font_override("font", UiTheme.body_regular())
	_hp_label.add_theme_font_size_override("font_size", 14)
	_hp_label.add_theme_color_override("font_color",
		Color(200.0 / 255.0, 200.0 / 255.0, 200.0 / 255.0))
	_info.add_child(_hp_label)

	_stats_label = Label.new()
	_stats_label.add_theme_font_override("font", UiTheme.body_medium())
	_stats_label.add_theme_font_size_override("font_size", 11)
	_stats_label.add_theme_color_override("font_color",
		Color(0.72, 0.78, 0.9))
	_info.add_child(_stats_label)

	# ── 4 tombol skill ──
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 10)
	_info.add_child(row)
	for k in SKILL_KEYS:
		var btn = SkillButtonScript.new(str(k))
		btn.skill_requested.connect(_on_skill_requested)
		row.add_child(btn)
		_buttons[str(k)] = btn

	# ── baris aksi panel (paritas tombol HeroPanel; tinggi 22) ──
	_autocast_btn = _make_action_button("AUTO-CAST ON")
	_autocast_btn.tooltip_text = _loc("skillbar_autocast_tip")
	_autocast_btn.pressed.connect(_on_autocast_pressed)
	_info.add_child(_autocast_btn)

	_item_row = HBoxContainer.new()
	_item_row.alignment = BoxContainer.ALIGNMENT_CENTER
	_item_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_item_row.add_theme_constant_override("separation", 4)
	_info.add_child(_item_row)
	for i in range(ITEM_SLOTS):
		# Chip = tombol: klik slot (kosong/isi) membuka ITEM FORGE, paritas
		# panel_slot0_empty (itemshop_open=true).
		var chip := Button.new()
		chip.custom_minimum_size = Vector2(SLOT_SIZE_PX, SLOT_SIZE_PX)
		chip.focus_mode = Control.FOCUS_NONE
		# Ikon item (assets/items/) di-scale engine ke content area chip —
		# lihat ItemIcons.gd. Tanpa expand_icon PNG 256 px digambar apa
		# adanya dan menutup seluruh panel.
		chip.expand_icon = true
		var csb := StyleBoxFlat.new()
		csb.bg_color = SLOT_BG
		csb.border_color = SLOT_BORDER_EMPTY
		csb.set_border_width_all(1)
		csb.set_corner_radius_all(5)
		chip.add_theme_stylebox_override("normal", csb)
		chip.add_theme_stylebox_override("hover", csb)
		chip.add_theme_stylebox_override("pressed", csb)
		chip.add_theme_stylebox_override("disabled", csb)
		chip.tooltip_text = _loc("skillbar_slot_empty") % (i + 1)
		chip.pressed.connect(_open_forge)
		_item_row.add_child(chip)
		_item_chips.append(chip)

	_forge_btn = _make_action_button("ITEM FORGE  (0/6)")
	_forge_btn.tooltip_text = _loc("skillbar_forge_tip")
	_forge_btn.pressed.connect(_open_forge)
	_info.add_child(_forge_btn)
	_upgrade_btn = _make_action_button("")
	_upgrade_btn.pressed.connect(_on_upgrade_pressed)
	_info.add_child(_upgrade_btn)


func _process(delta: float) -> void:
	_timer += delta
	if _timer < REFRESH_INTERVAL:
		return
	_timer = 0.0
	_refresh()


func _on_selection_changed() -> void:
	_hero = GameManager.selected_hero
	if _hero != null and not is_instance_valid(_hero):
		_hero = null
	_refresh_static()
	_refresh()


func _on_language_changed(_language: String) -> void:
	_refresh_static()


func _on_hero_died(hero: Node) -> void:
	if hero == _hero:
		_hero = null
	_refresh_static()


func _on_skill_requested(key: String) -> void:
	var h = _hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		return
	if h.has_method("cast_" + key):
		h.call("cast_" + key)


## X panel: batal pilih hero SAJA (toko tak disentuh) — paritas panel_close
## (selected_after None).
func _on_close_pressed() -> void:
	GameManager.clear_selection()


## Toggle auto-cast pygame v29 = NO-OP (auto_before==auto_after==true):
## tombol ini murni indikator "AUTO-CAST ON".
func _on_autocast_pressed() -> void:
	pass


## Buka toko langsung ke tab ITEM untuk hero terpilih (paritas
## panel_open_items / panel_slot0_empty: itemshop_open=true).
func _open_forge() -> void:
	if _hero == null or not is_instance_valid(_hero):
		return
	GameManager.requested_shop_tab = "item"
	GameManager.open_shop()


## Upgrade dari panel (paritas popup_upgrade_hero); SFX = jalur ShopPanel.
func _on_upgrade_pressed() -> void:
	if GameManager.try_upgrade_hero():
		AudioManager.play_sfx("ui_upgrade", 0.6)
	else:
		AudioManager.play_sfx("ui_error", 0.4)
	_refresh_static()


## Bagian yang tidak berubah tiap frame: nama hero, level, slot item
func _refresh_static() -> void:
	var h = GameManager.selected_hero
	if h != null and is_instance_valid(h) and not bool(h.get("is_dead")):
		_hero = h
	else:
		_hero = null
	var hero = _hero
	# Paritas HeroPanel pygame: panel HANYA tampil saat ada hero terpilih &
	# hidup. Tanpa syarat ini panel 280x276 duduk permanen di atas map
	# kiri-bawah dan menelan ketukan pemain ke hero di base Radiant.
	if _root.visible != (hero != null):
		_root.visible = hero != null
		_layout()
	_close_btn.disabled = hero == null
	_autocast_btn.disabled = hero == null
	_forge_btn.disabled = hero == null
	# Tooltip adalah teks statis yang dipasang di `_build()` — dibaca ulang di
	# sini supaya pergantian bahasa berlaku tanpa membangun panel dari awal.
	_close_btn.tooltip_text = _loc("skillbar_close_tip")
	_autocast_btn.tooltip_text = _loc("skillbar_autocast_tip")
	_forge_btn.tooltip_text = _loc("skillbar_forge_tip")
	_upgrade_btn.disabled = hero == null
	# Border panel = warna hero +30 (paritas HeroPanel pygame).
	if hero == null:
		_root.border_color = Color(0.35, 0.5, 0.95)
	else:
		var hc := HeroDB.get_hero_color(str(hero.get("hero_type")))
		_root.border_color = Color(minf(1.0, hc.r + 30.0 / 255.0),
			minf(1.0, hc.g + 30.0 / 255.0),
			minf(1.0, hc.b + 30.0 / 255.0))
	_root.queue_redraw()
	if hero == null:
		_name_label.text = _loc("skillbar_no_hero")
		_level_label.text = ""
		_stats_label.text = _loc("skillbar_buy_hint")
		_hp_bar.value = 0.0
		_hp_label.text = ""
		_forge_btn.text = "ITEM FORGE  (0/6)"
		_upgrade_btn.text = ""
		_sync_items([])
		for k in SKILL_KEYS:
			_buttons[k].update_state(null)
		return
	var hdata: Dictionary = HeroDB.get_hero(str(hero.get("hero_type")))
	_name_label.text = str(hdata.get("name", hero.get("hero_type")))
	_level_label.text = "Lv.%d" % int(hero.get("level"))
	_stats_label.text = "DMG %d · ARM %.0f · MR %.0f · RNG %d" % [
		int(hero.get("damage")), float(hero.get("armor")),
		float(hero.get("magic_resist")), int(hero.get("attack_range"))]
	var items = hero.get("items")
	var ids: Array = items.item_ids() if items != null else []
	_sync_items(ids)
	# Dua spasi sebelum kurung — persis "ITEM FORGE  (0/6)" pygame.
	_forge_btn.text = "ITEM FORGE  (%d/6)" % ids.filter(
		func(id): return str(id) != "").size()
	if hero.has_method("can_upgrade") and hero.can_upgrade():
		_upgrade_btn.text = "UPGRADE HERO (%dG)" % int(hero.upgrade_cost())
		_upgrade_btn.disabled = false
	else:
		# Level max: label letterspaced, bukan tombol (paritas panel_max).
		_upgrade_btn.text = HudLayout.letter("MAX LEVEL")
		_upgrade_btn.disabled = true
	for k in SKILL_KEYS:
		_buttons[k].update_state(hero)


## Pintu teks panel ke tabel teks bersama (localization.py <-> Localization.gd).
func _loc(key: String) -> String:
	return MysticLocalization.tr_text(key)


func _make_action_button(label_text: String) -> Button:
	var b := Button.new()
	b.text = label_text
	b.custom_minimum_size = Vector2(0, 22)
	b.focus_mode = Control.FOCUS_NONE
	if label_text.begins_with("AUTO"):
		UiTheme.apply_row_button(b, "success", 13, false)
	elif label_text.begins_with("ITEM"):
		UiTheme.apply_row_button(b, "violet", 13, false)
	else:
		UiTheme.apply_row_button(b, "gold", 13, false)
	return b


func _sync_items(ids: Array) -> void:
	for i in range(_item_chips.size()):
		var chip: Button = _item_chips[i]
		var sb := chip.get_theme_stylebox("normal") as StyleBoxFlat
		if i < ids.size() and str(ids[i]) != "":
			var item_id := str(ids[i])
			# Slot terisi (paritas hero_items.py:3031-3095): bg tetap gelap,
			# border = warna katalog 2 px, ikon item di tengah. Glow halo saat
			# item AKTIF (blood frenzy/guard/veil, :3036-3079) belum diport —
			# timer aktifnya belum terbaca dari ItemInventory di panel ini.
			if sb != null:
				sb.bg_color = SLOT_BG
				sb.border_color = ItemDB.item_color(item_id)
				sb.set_border_width_all(SLOT_BORDER_FILLED)
			# PNG asli assets/items/ kalau sudah disalin converter, badge
			# prosedural warna katalog kalau belum (ItemIcons = port get_icon).
			chip.icon = ItemIcons.texture(item_id, ItemIcons.SLOT_ICON_SIZE)
			chip.tooltip_text = "%s — %s" % [ItemDB.item_name(item_id), ItemDB.item_desc(item_id)]
		else:
			if sb != null:
				sb.bg_color = SLOT_BG
				sb.border_color = SLOT_BORDER_EMPTY
				sb.set_border_width_all(1)
			chip.icon = null
			chip.tooltip_text = _loc("skillbar_slot_empty") % (i + 1)
		# StyleBoxFlat yang di-mutate tidak otomatis memicu redraw Panel
		chip.queue_redraw()


## Bagian yang berubah terus: HP + cooldown
func _refresh() -> void:
	var hero = _hero
	if hero == null or not is_instance_valid(hero) or bool(hero.get("is_dead")):
		if hero != null:
			_refresh_static()
		return
	var hp := float(hero.get("hp"))
	var max_hp := maxf(1.0, float(hero.get("max_hp")))
	_hp_bar.value = clampf(100.0 * hp / max_hp, 0.0, 100.0)
	_hp_label.text = "%d/%d%s" % [int(hp), int(max_hp),
		"  ·  MUNDUR" if bool(hero.get("is_retreating")) else ""]
	for k in SKILL_KEYS:
		_buttons[k].update_state(hero)
