# SidePanel.gd — panel kanan landscape "dinding batu", port mobile/sidepanel.py.
#
# Isi panel mengikuti urutan pygame (SidePanel._gambar_*):
#
#   * tombol JEDA (ikon dua batang) di jalur atas,
#   * kotak STATUS  : GOLD besar, difficulty, LV, WAVE + status SHIELD,
#   * kotak HEROES  : maksimal 5 baris (nama, Lv, bar HP, titik skill q/w/e/r),
#   * pintu masuk toko: TOWER SHOP / CASTLE SHOP (popup panel kanan) dan
#     HERO SHOP / ITEM FORGE (modal tengah) — tambahan Godot, pygame tak punya,
#   * TACTICAL COMMANDS di DASAR panel — kotaknya dimiliki TacticalBar.gd,
#     panel ini hanya menyediakan jalurnya (MobileLayout.tactical_rect).
#
# Latar = bata batu port _gambar_panel_samping (digambar ulang hanya saat
# ukuran rail berubah, paritas "digambar SEKALI"). Panel hanya ADA saat layar
# lebih lebar dari 16:9 (sisa >= 120 px) — di 16:9 rail disembunyikan total
# dan arena memakai lebar penuh, paritas "di layar 16:9 panelnya tidak ada".
#
# Z-ORDER: node ini ditambahkan setelah gameplay tapi SEBELUM TacticalBar &
# ShopPanel di HUD.gd, dan latar batunya MOUSE_FILTER_STOP hanya di area rail
# sehingga arena di kiri tetap bisa diklik dan tombol taktis di atasnya tetap
# menerima klik.
extends Control


## Latar bata batu — port platform_utils._gambar_panel_samping 1:1
## (warna, ukuran bata 34 px, selang-seling tiap baris, gradasi kiri,
## garis emas pemisah arena). Anak PERTAMA rail sehingga tergambar di
## belakang kotak isi.
class StoneBG:
	extends Control

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		resized.connect(queue_redraw)

	func _draw() -> void:
		var full := Rect2(Vector2.ZERO, size)
		var dasar := Color8(16, 14, 24)
		var batu_gelap := Color8(26, 23, 38)
		var batu := Color8(34, 30, 48)
		var garis := Color8(58, 50, 78)
		var emas := Color8(150, 120, 60)
		draw_rect(full, dasar)
		var bh := 34.0
		var bw := float(maxi(28, int(size.x) / 4))
		var i := 0
		var y := -bh
		while y < size.y + bh:
			var geser := (bw * 0.5) if (i % 2 == 1) else 0.0
			var x := -bw
			while x < size.x + bw:
				var r := Rect2(x + geser + 1.0, y + 1.0, bw - 2.0,
					bh - 2.0).intersection(full)
				if r.size.x > 0.0 and r.size.y > 0.0:
					# (i + x) % 3 ala Python: x bisa negatif, GDScript %
					# memotong ke nol sehingga dinormalkan dulu.
					var m := (i + int(x)) % 3
					if m < 0:
						m += 3
					draw_rect(r, batu if m != 0 else batu_gelap)
					draw_rect(r, garis, false, 1.0)
				x += bw
			y += bh
			i += 1
		# Gradasi gelap 20 px di sisi kiri supaya menyatu dengan arena.
		for g in 20:
			var a := 1.0 - float(g) / 20.0
			draw_line(Vector2(g, 0), Vector2(g, size.y),
				Color(dasar.r * a, dasar.g * a, dasar.b * a))
		# Bingkai emas pemisah arena.
		draw_line(Vector2(1, 0), Vector2(1, size.y), emas, 2.0)


const BG_TOP := Color(0.075, 0.068, 0.105, 0.98)
const BG_BOTTOM := Color(0.042, 0.038, 0.065, 0.99)
const EDGE := Color(0.42, 0.34, 0.22, 1.0)
const BOX_BG := Color(0.086, 0.074, 0.125, 0.95)
const BOX_EDGE := Color(0.25, 0.22, 0.34, 1.0)
const TEXT := Color(0.894, 0.902, 0.949)
const DIM := Color(0.572, 0.588, 0.674)
const GOLD := Color(1.0, 0.804, 0.353)
const OK := Color(0.470, 0.921, 0.549)
const DANGER := Color(1.0, 0.431, 0.431)
const CYAN := Color(0.392, 0.784, 1.0)
## Titik kesiapan skill (paritas _gambar_hero: UNGU siap / gelap belum).
const DOT_ON := Color(0.745, 0.647, 1.0)
const DOT_OFF := Color(0.235, 0.220, 0.306)
## 5 hero x 38 px + judul (paritas _gambar_hero pygame).
const MAX_HERO_ROWS := 5
const REFRESH_INTERVAL := 0.25

var _rail: PygamePanel = null
var _stone_bg: Control = null
var _pause_button: Button = null
var _status_box: PygamePanel = null
var _gold_value: Label = null
var _gold_caption: Label = null
var _mode_label: Label = null
var _level_label: Label = null
var _wave_label: Label = null
var _shield_label: Label = null
var _heroes_box: PygamePanel = null
var _heroes_rows: VBoxContainer = null
var _heroes_empty: Label = null
var _shop_box: PygamePanel = null
var _shop_buttons: Array[Button] = []
var _timer: float = 0.0


func _ready() -> void:
	name = "SidePanel"
	MobileLayout.fill_parent(self)
	# Root tembus klik: hanya rail (dan tombolnya) yang menahan input.
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	MobileLayout.layout_changed.connect(_layout)
	GameManager.gold_changed.connect(func(_g): _refresh())
	GameManager.wave_started.connect(func(_w): _refresh())
	GameManager.level_started.connect(func(_l): _refresh())
	GameManager.difficulty_changed.connect(func(_d): _refresh())
	GameManager.shop_changed.connect(_refresh)
	_layout()
	_refresh()


func _process(delta: float) -> void:
	_timer += delta
	if _timer < REFRESH_INTERVAL:
		return
	_timer = 0.0
	_refresh()


# ══════════════════════════════════════════════════════════
#  KERANGKA
# ══════════════════════════════════════════════════════════

func _build() -> void:
	_rail = PygamePanel.new(Color(0, 0, 0, 0), 0.0, 0.0)
	_rail.name = "StoneRail"
	# Latar digambar StoneBG (bata batu pygame), bukan gradien panel —
	# wadah ini dibuat transparan total (paritas _gambar_panel_samping).
	_rail.configure(Color(0, 0, 0, 0), Color(0, 0, 0, 0),
		Color(0, 0, 0, 0), 0.0, 0.0, false, false)
	# Rail menahan klik supaya sentuhan di panel tidak "tembus" ke arena
	# (paritas SidePanel.blocks pygame).
	_rail.mouse_filter = Control.MOUSE_FILTER_STOP
	_rail.set_margins(0, 0, 0, 0)
	add_child(_rail)

	# Bata batu = anak PERTAMA (di belakang kotak isi). PanelContainer
	# mengepas tiap anak ke seluruh area, jadi latar selalu pas ukuran rail.
	var bg := StoneBG.new()
	bg.name = "StoneBG"
	MobileLayout.fill_parent(bg)
	_rail.add_child(bg)
	_stone_bg = bg

	# Anak-anak rail diposisikan absolut (jalur tetap) supaya tidak pernah
	# saling menimpa — sama dengan pembagian zona pygame.
	var host := Control.new()
	host.name = "RailHost"
	host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	MobileLayout.fill_parent(host)
	_rail.add_child(host)

	_pause_button = _make_pause_button()
	host.add_child(_pause_button)
	_status_box = _make_status_box()
	host.add_child(_status_box)
	_heroes_box = _make_heroes_box()
	host.add_child(_heroes_box)
	_shop_box = _make_shop_box()
	host.add_child(_shop_box)


func _make_pause_button() -> Button:
	var b := Button.new()
	b.name = "RailPause"
	b.text = "II"
	b.tooltip_text = MysticLocalization.tr_text("rail_pause_tip")
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	b.custom_minimum_size = Vector2(58, 58)
	UiTheme.apply_row_button(b, "gold", 20, false)
	b.set_meta("ui_key", "rail_pause")
	b.pressed.connect(_on_pause_pressed)
	return b


func _make_box(box_name: String, title: String) -> PygamePanel:
	var p := PygamePanel.new(BOX_EDGE, 1.0, 8.0)
	p.name = box_name
	p.configure(BOX_BG, BOX_BG, BOX_EDGE, 1.0, 8.0, false, false)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.set_margins(9, 6, 9, 8)
	var col := VBoxContainer.new()
	col.name = "Col"
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_theme_constant_override("separation", 2)
	p.add_child(col)
	var t := Label.new()
	t.name = "BoxTitle"
	UiTheme.style_label(t, title, UiTheme.body_bold(), 12, DIM)
	col.add_child(t)
	return p


func _make_status_box() -> PygamePanel:
	var box := _make_box("StatusBox", "STATUS")
	var col: VBoxContainer = box.get_node("Col")

	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 6)
	col.add_child(row)

	var left := VBoxContainer.new()
	left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 0)
	row.add_child(left)

	_gold_value = Label.new()
	_gold_value.name = "GoldValue"
	UiTheme.style_label(_gold_value, "0", UiTheme.body_bold(), 22, GOLD)
	_gold_value.clip_text = true
	left.add_child(_gold_value)

	_gold_caption = Label.new()
	_gold_caption.name = "GoldCaption"
	UiTheme.style_label(_gold_caption, "GOLD", UiTheme.body_regular(), 12, DIM)
	left.add_child(_gold_caption)

	_mode_label = Label.new()
	_mode_label.name = "ModeLabel"
	UiTheme.style_label(_mode_label, "NORMAL", UiTheme.body_regular(), 12, OK)
	left.add_child(_mode_label)

	var right := VBoxContainer.new()
	right.name = "StatusRight"
	right.mouse_filter = Control.MOUSE_FILTER_IGNORE
	right.alignment = BoxContainer.ALIGNMENT_BEGIN
	right.add_theme_constant_override("separation", 2)
	row.add_child(right)

	_level_label = Label.new()
	_level_label.name = "LevelLabel"
	UiTheme.style_label(_level_label, "LV 1", UiTheme.body_bold(), 16, TEXT,
		HORIZONTAL_ALIGNMENT_RIGHT)
	right.add_child(_level_label)

	_wave_label = Label.new()
	_wave_label.name = "WaveLabel"
	UiTheme.style_label(_wave_label, "Wave 0", UiTheme.body_regular(), 13, DIM,
		HORIZONTAL_ALIGNMENT_RIGHT)
	right.add_child(_wave_label)

	_shield_label = Label.new()
	_shield_label.name = "ShieldLabel"
	UiTheme.style_label(_shield_label, "", UiTheme.body_regular(), 12, CYAN,
		HORIZONTAL_ALIGNMENT_RIGHT)
	right.add_child(_shield_label)
	return box


func _make_heroes_box() -> PygamePanel:
	var box := _make_box("HeroesBox", "HEROES")
	var col: VBoxContainer = box.get_node("Col")
	_heroes_empty = Label.new()
	_heroes_empty.name = "NoHeroes"
	UiTheme.style_label(_heroes_empty, "No heroes", UiTheme.body_regular(),
		13, DIM)
	col.add_child(_heroes_empty)
	_heroes_rows = VBoxContainer.new()
	_heroes_rows.name = "HeroRows"
	_heroes_rows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_heroes_rows.add_theme_constant_override("separation", 4)
	col.add_child(_heroes_rows)
	return box


func _make_shop_box() -> PygamePanel:
	var box := _make_box("ShopBox", "SHOP & FORGE")
	var col: VBoxContainer = box.get_node("Col")
	var grid := GridContainer.new()
	grid.name = "ShopGrid"
	grid.columns = 2
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	grid.add_theme_constant_override("h_separation", 5)
	grid.add_theme_constant_override("v_separation", 4)
	col.add_child(grid)
	_add_shop_button(grid, "TOWER SHOP", "tower", "rail_shop_tower")
	_add_shop_button(grid, "CASTLE SHOP", "nexus", "rail_shop_castle")
	_add_shop_button(grid, "HERO SHOP", "hero", "rail_shop_hero")
	_add_shop_button(grid, "ITEM FORGE", "item", "rail_shop_item")
	return box


func _add_shop_button(grid: GridContainer, label: String, tab: String,
		ui_key: String) -> void:
	var b := Button.new()
	b.name = "Rail_" + tab
	b.text = label
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	b.custom_minimum_size = Vector2(0, 30)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.clip_text = true
	UiTheme.apply_row_button(b, "gold" if tab == "tower" or tab == "nexus"
		else "neutral", 11, false)
	b.set_meta("ui_key", ui_key)
	b.pressed.connect(_open_shop.bind(tab))
	grid.add_child(b)
	_shop_buttons.append(b)


# ══════════════════════════════════════════════════════════
#  AKSI
# ══════════════════════════════════════════════════════════

## Paritas `side.aktif` (main.py membaca tombol jeda rail HANYA saat panel
## kanan aktif). Di Godot panel aktif = rail punya lebar.
func rail_active() -> bool:
	return MobileLayout.has_side_panel()


## Paritas `side.buttons["pause"].contains(pos)` (main.py:408-410): saat panel
## kanan aktif, tombol jeda ada di rail — TAHAN di atasnya harus memicu
## overlay debug juga, seperti TouchHUD.
func rail_pause_contains(pos: Vector2) -> bool:
	if _pause_button == null or not is_instance_valid(_pause_button):
		return false
	if not _pause_button.visible:
		return false
	return _pause_button.get_global_rect().has_point(pos)


func _on_pause_pressed() -> void:
	# Getar 15 ms = paritas `if hit: plat.vibrate(15)` di cabang `down`
	# main.py:423-426 (setiap sentuhan yang ditangkap panel kanan bergetar).
	MobileLayout.vibrate(15)
	var main = get_tree().get_first_node_in_group("main")
	if main != null and is_instance_valid(main) and main.has_method("_toggle_pause"):
		main.call("_toggle_pause")


func _open_shop(tab: String) -> void:
	if GameManager.state != "playing":
		return
	MobileLayout.vibrate(15)
	GameManager.requested_shop_tab = tab
	if GameManager.shop_open:
		# Toko sudah terbuka: pindahkan tab langsung (open_shop() no-op).
		var shop = get_parent().find_child("ShopPanel", true, false) \
			if get_parent() != null else null
		if shop != null and shop.has_method("open_tab"):
			GameManager.requested_shop_tab = ""
			shop.call("open_tab", tab)
			return
	GameManager.open_shop()


# ══════════════════════════════════════════════════════════
#  TATA LETAK (jalur tetap, mengikuti MobileLayout)
# ══════════════════════════════════════════════════════════

func _layout() -> void:
	if _rail == null:
		return
	var rect := MobileLayout.side_panel_rect()
	var show_rail := MobileLayout.has_side_panel()
	_rail.visible = show_rail
	# Layar kecil/potret: rail disembunyikan TOTAL termasuk hit-test, HUD
	# kembali ke tata letak tengah.
	_rail.mouse_filter = Control.MOUSE_FILTER_STOP if show_rail \
		else Control.MOUSE_FILTER_IGNORE
	if not show_rail:
		return
	_rail.position = rect.position
	_rail.size = rect.size
	if _stone_bg != null:
		_stone_bg.queue_redraw()

	var pad := MobileLayout.RAIL_PAD
	var inner := rect.size.x - pad * 2.0
	_pause_button.position = Vector2(pad, 14.0)
	_pause_button.size = Vector2(58, 58)

	_place(_status_box, pad, MobileLayout.STATUS_TOP, inner,
		MobileLayout.STATUS_HEIGHT)
	_place(_heroes_box, pad, MobileLayout.HEROES_TOP, inner,
		MobileLayout.HEROES_HEIGHT)
	_place(_shop_box, pad, MobileLayout.SHOP_TOP, inner,
		MobileLayout.SHOP_HEIGHT)


func _place(node: Control, x: float, y: float, w: float, h: float) -> void:
	if node == null:
		return
	node.position = Vector2(x, y)
	node.size = Vector2(maxf(0.0, w), maxf(0.0, h))


# ══════════════════════════════════════════════════════════
#  ISI (disegarkan 4 Hz seperti JEDA_SEGAR_MS pygame)
# ══════════════════════════════════════════════════════════

func _refresh() -> void:
	if _rail == null or not _rail.visible:
		return
	# Paritas dalam_gp pygame: STATUS/HEROES tampil selama playing/victory/
	# defeat (bukan cuma playing); tactical tetap playing-only (TacticalBar).
	# Di luar gameplay panel dikosongkan (paritas _bersihkan_panel).
	var in_game := (GameManager.state == "playing"
		or GameManager.state == "victory" or GameManager.state == "defeat") \
		and not GameManager.in_menu
	_status_box.visible = in_game
	_heroes_box.visible = in_game
	_shop_box.visible = in_game
	_pause_button.visible = in_game
	if not in_game:
		return
	_refresh_status()
	_refresh_heroes()


func _refresh_status() -> void:
	var gold := int(GameManager.gold)
	_gold_value.text = ("%.1fK" % (gold / 1000.0)) if gold >= 10000 \
		else HudLayout.format_thousands(gold)
	_mode_label.text = HudLayout.mode_label(GameManager.difficulty)
	_mode_label.add_theme_color_override("font_color",
		HudLayout.mode_color(GameManager.difficulty))
	var wave := int(GameManager.wave_number)
	var shielded := false
	var nx = GameManager.blue_nexus
	if nx != null and is_instance_valid(nx):
		shielded = bool(nx.get("shield_active"))
	# Paritas _gambar_status: "LV n [SHIELDED]" (shield aktif & wave < 10),
	# "Wave n (Shield)" (wave < 10). Label SHIELD terpisah = indikator Godot.
	if shielded and wave < 10:
		_level_label.text = "LV %d [SHIELDED]" % int(GameManager.level_number)
	else:
		_level_label.text = "LV %d" % int(GameManager.level_number)
	if wave < 10:
		_wave_label.text = "Wave %d (Shield)" % wave
		_wave_label.add_theme_color_override("font_color", CYAN)
	else:
		_wave_label.text = "Wave %d" % wave
		_wave_label.add_theme_color_override("font_color", DIM)
	if shielded:
		_shield_label.text = "SHIELDED"
		_shield_label.add_theme_color_override("font_color", CYAN)
	else:
		_shield_label.text = ""
		_shield_label.add_theme_color_override("font_color", DIM)


func _refresh_heroes() -> void:
	var heroes: Array = []
	for h in GameManager.owned_heroes("blue"):
		if is_instance_valid(h):
			heroes.append(h)
	var shown: Array = heroes.slice(0, MAX_HERO_ROWS)
	_heroes_empty.visible = shown.is_empty()
	while _heroes_rows.get_child_count() < shown.size():
		_heroes_rows.add_child(_make_hero_row())
	for i in _heroes_rows.get_child_count():
		var row: Control = _heroes_rows.get_child(i)
		row.visible = i < shown.size()
		if i >= shown.size():
			continue
		var hero = shown[i]
		var alive := not bool(hero.get("is_dead"))
		var nm: Label = row.get_node("Top/Name")
		var lv: Label = row.get_node("Top/Level")
		var bar: ProgressBar = row.get_node("HP")
		var hdata: Dictionary = HeroDB.get_hero(str(hero.get("hero_type")))
		nm.text = str(hdata.get("name", hero.get("hero_type"))).substr(0, 12)
		nm.add_theme_color_override("font_color", TEXT if alive else DANGER)
		lv.text = "Lv%d" % int(hero.get("level"))
		var max_hp := maxf(1.0, float(hero.get("max_hp")))
		var ratio := clampf(float(hero.get("hp")) / max_hp, 0.0, 1.0)
		bar.value = ratio * 100.0
		UiTheme.style_progress_bar(bar,
			OK if ratio > 0.5 else (GOLD if ratio > 0.25 else DANGER),
			Color(0.188, 0.055, 0.055, 1.0), 3)
		var dots: HBoxContainer = row.get_node("Skills")
		for k in ["q", "w", "e", "r"]:
			var d: Panel = dots.get_node("Dot_" + k)
			var ready := false
			if hero.has_method("is_skill_ready"):
				ready = bool(hero.call("is_skill_ready", k))
			(d.get_theme_stylebox("panel") as StyleBoxFlat).bg_color = \
				DOT_ON if ready else DOT_OFF


func _make_hero_row() -> Control:
	var row := VBoxContainer.new()
	row.name = "HeroRow"
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 1)
	var top := HBoxContainer.new()
	top.name = "Top"
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(top)
	var nm := Label.new()
	nm.name = "Name"
	nm.clip_text = true
	nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UiTheme.style_label(nm, "", UiTheme.body_bold(), 14, TEXT)
	top.add_child(nm)
	var lv := Label.new()
	lv.name = "Level"
	UiTheme.style_label(lv, "", UiTheme.body_regular(), 12, GOLD,
		HORIZONTAL_ALIGNMENT_RIGHT)
	top.add_child(lv)
	var bar := ProgressBar.new()
	bar.name = "HP"
	bar.show_percentage = false
	bar.max_value = 100.0
	bar.custom_minimum_size = Vector2(0, 6)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiTheme.style_progress_bar(bar, OK, Color(0.188, 0.055, 0.055, 1.0), 3)
	row.add_child(bar)
	# Titik kesiapan skill q/w/e/r (paritas lingkaran r=4, pitch 14 px).
	var dots := HBoxContainer.new()
	dots.name = "Skills"
	dots.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dots.add_theme_constant_override("separation", 6)
	row.add_child(dots)
	for k in ["q", "w", "e", "r"]:
		var d := Panel.new()
		d.name = "Dot_" + k
		var sb := StyleBoxFlat.new()
		sb.bg_color = DOT_OFF
		sb.set_corner_radius_all(4)
		d.add_theme_stylebox_override("panel", sb)
		d.custom_minimum_size = Vector2(8, 8)
		d.mouse_filter = Control.MOUSE_FILTER_IGNORE
		dots.add_child(d)
	return row
