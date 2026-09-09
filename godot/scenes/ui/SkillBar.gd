# SkillBar.gd — bar skill QWER + panel hero terpilih.
#
# Port dari _core.Game._draw_skill_bar / _draw_hero_status / baris 6 slot item:
# pygame menggambar semuanya manual di surface tiap frame; di sini semuanya
# Control biasa yang dibangun dari kode (tanpa .tscn) supaya HUD.tscn tetap utuh.
#
# Sumber kebenaran = GameManager.selected_hero. Tombol skill dan keyboard QWER
# memanggil jalur yang sama (hero.cast_q/w/e/r), jadi tidak ada duplikasi logika.
extends Control

const SkillButtonScript = preload("res://scenes/ui/SkillButton.gd")
const SKILL_KEYS: Array = ["q", "w", "e", "r"]
const ITEM_SLOTS: int = 6
## Seberapa sering angka HP/cooldown disinkronkan (20 Hz cukup halus, hemat)
const REFRESH_INTERVAL := 0.05

var _root: HBoxContainer = null
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
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build()
	GameManager.selection_changed.connect(_on_selection_changed)
	GameManager.hero_died.connect(_on_hero_died)
	GameManager.shop_changed.connect(_refresh_static)
	_on_selection_changed()


func _build() -> void:
	_root = HBoxContainer.new()
	_root.name = "BarRoot"
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# tengah-bawah layar
	_root.anchor_left = 0.5
	_root.anchor_right = 0.5
	_root.anchor_top = 1.0
	_root.anchor_bottom = 1.0
	_root.offset_left = -286.0
	_root.offset_right = 286.0
	_root.offset_top = -158.0
	_root.offset_bottom = -52.0
	_root.add_theme_constant_override("separation", 12)
	add_child(_root)

	# ── panel info hero ──
	var panel := MysticPanel.new(Color8(28, 38, 66), Color8(18, 24, 44),
		Color8(96, 152, 214), 10.0, 2.0, false)
	panel.name = "HeroPanel"
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.custom_minimum_size = Vector2(250, 0)
	_root.add_child(panel)
	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_top", 6)
	margin.add_theme_constant_override("margin_bottom", 6)
	panel.add_child(margin)

	_info = VBoxContainer.new()
	_info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info.add_theme_constant_override("separation", 3)
	margin.add_child(_info)

	# Baris nama: "Kaizen" + "Lv.1" + tombol tutup X (paritas teks panel).
	var name_row := HBoxContainer.new()
	name_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	name_row.add_theme_constant_override("separation", 8)
	_info.add_child(name_row)
	_name_label = Label.new()
	UiTheme.style_label(_name_label, 15, "body_semibold",
		Color8(217, 235, 255), true)
	_name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name_label.text = "No hero selected"
	name_row.add_child(_name_label)
	_level_label = Label.new()
	UiTheme.style_label(_level_label, 15, "body_bold", UiTheme.GOLD_TEXT,
		true)
	_level_label.text = ""
	name_row.add_child(_level_label)
	_close_btn = Button.new()
	_close_btn.text = "X"
	_close_btn.custom_minimum_size = Vector2(24, 22)
	_close_btn.focus_mode = Control.FOCUS_NONE
	_close_btn.tooltip_text = "Close panel (deselect hero)"
	_close_btn.add_theme_font_override("font", UiTheme.font("body_bold"))
	_close_btn.add_theme_font_size_override("font_size", 12)
	_close_btn.add_theme_color_override("font_color", UiTheme.TEXT_DIM)
	_close_btn.add_theme_color_override("font_hover_color", UiTheme.RED)
	_close_btn.pressed.connect(_on_close_pressed)
	name_row.add_child(_close_btn)

	_hp_bar = ProgressBar.new()
	_hp_bar.custom_minimum_size = Vector2(0, 14)
	_hp_bar.show_percentage = false
	_hp_bar.max_value = 100.0
	_hp_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var hp_bg := StyleBoxFlat.new()
	hp_bg.bg_color = Color(0.12, 0.05, 0.06, 0.95)
	hp_bg.set_corner_radius_all(4)
	var hp_fill := StyleBoxFlat.new()
	hp_fill.bg_color = Color(0.32, 0.85, 0.42)
	hp_fill.set_corner_radius_all(4)
	_hp_bar.add_theme_stylebox_override("background", hp_bg)
	_hp_bar.add_theme_stylebox_override("fill", hp_fill)
	_info.add_child(_hp_bar)

	_hp_label = Label.new()
	UiTheme.style_label(_hp_label, 11, "body_semibold",
		Color8(191, 242, 199))
	_info.add_child(_hp_label)

	_stats_label = Label.new()
	UiTheme.style_label(_stats_label, 11, "body", Color8(184, 199, 230))
	_info.add_child(_stats_label)

	_item_row = HBoxContainer.new()
	_item_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_item_row.add_theme_constant_override("separation", 4)
	_info.add_child(_item_row)
	for i in range(ITEM_SLOTS):
		# Chip = tombol: klik slot (kosong/isi) membuka ITEM FORGE, paritas
		# panel_slot0_empty (itemshop_open=true).
		var chip := Button.new()
		chip.custom_minimum_size = Vector2(18, 18)
		chip.focus_mode = Control.FOCUS_NONE
		var csb := StyleBoxFlat.new()
		csb.bg_color = Color(0.1, 0.11, 0.16, 0.95)
		csb.border_color = Color(0.3, 0.33, 0.42, 0.9)
		csb.set_border_width_all(1)
		csb.set_corner_radius_all(4)
		chip.add_theme_stylebox_override("normal", csb)
		chip.add_theme_stylebox_override("hover", csb)
		chip.add_theme_stylebox_override("pressed", csb)
		chip.add_theme_stylebox_override("disabled", csb)
		chip.tooltip_text = "item slot %d empty" % (i + 1)
		chip.pressed.connect(_open_forge)
		_item_row.add_child(chip)
		_item_chips.append(chip)

	# ── baris aksi panel (paritas tombol HeroPanel) ──
	_autocast_btn = _make_action_button("AUTO-CAST ON", "neutral", "")
	_autocast_btn.tooltip_text = "Auto-cast is always ON (parity v29: toggle no-op)"
	_autocast_btn.pressed.connect(_on_autocast_pressed)
	_info.add_child(_autocast_btn)
	_forge_btn = _make_action_button("ITEM FORGE  (0/6)", "gold", "gem")
	_forge_btn.tooltip_text = "Open the ITEM FORGE for this hero"
	_forge_btn.pressed.connect(_open_forge)
	_info.add_child(_forge_btn)
	_upgrade_btn = _make_action_button("", "success", "plus")
	_upgrade_btn.pressed.connect(_on_upgrade_pressed)
	_info.add_child(_upgrade_btn)

	# ── 4 tombol skill ──
	var skill_box := VBoxContainer.new()
	skill_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	skill_box.add_theme_constant_override("separation", 2)
	_root.add_child(skill_box)

	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 6)
	skill_box.add_child(row)
	for k in SKILL_KEYS:
		var btn = SkillButtonScript.new(str(k))
		btn.skill_requested.connect(_on_skill_requested)
		row.add_child(btn)
		_buttons[str(k)] = btn

	var hint := Label.new()
	hint.text = "click a hero to select · QWER / buttons = skills · H = shop · G/T/C/B/D = tactical orders"
	UiTheme.style_label(hint, 10, "body", Color(0.7, 0.76, 0.9, 0.75))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	skill_box.add_child(hint)


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
	_close_btn.disabled = hero == null
	_autocast_btn.disabled = hero == null
	_forge_btn.disabled = hero == null
	_upgrade_btn.disabled = hero == null
	if hero == null:
		_name_label.text = "No hero selected"
		_level_label.text = ""
		_stats_label.text = "H = SHOP: buy a hero, then click to select"
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


func _make_action_button(label_text: String, kind: String,
		icon: String) -> Button:
	var b := MysticPill.new(label_text, kind, icon, 11, false)
	b.custom_minimum_size = Vector2(0, 26)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.focus_mode = Control.FOCUS_NONE
	return b


func _sync_items(ids: Array) -> void:
	for i in range(_item_chips.size()):
		var chip: Button = _item_chips[i]
		var sb := chip.get_theme_stylebox("normal") as StyleBoxFlat
		if i < ids.size() and str(ids[i]) != "":
			var item_id := str(ids[i])
			var col: Color = ItemDB.item_color(item_id)
			if sb != null:
				sb.bg_color = Color(col.r, col.g, col.b, 0.85)
				sb.border_color = ItemDB.item_glow(item_id)
			chip.tooltip_text = "%s — %s" % [ItemDB.item_name(item_id), ItemDB.item_desc(item_id)]
		else:
			if sb != null:
				sb.bg_color = Color(0.1, 0.11, 0.16, 0.95)
				sb.border_color = Color(0.3, 0.33, 0.42, 0.9)
			chip.tooltip_text = "item slot %d empty" % (i + 1)
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
		"  ·  RETREATING" if bool(hero.get("is_retreating")) else ""]
	for k in SKILL_KEYS:
		_buttons[k].update_state(hero)
