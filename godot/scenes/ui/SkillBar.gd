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
var _hp_bar: ProgressBar = null
var _hp_label: Label = null
var _stats_label: Label = null
var _item_row: HBoxContainer = null
var _item_chips: Array = []
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
	# tengah-bawah, di atas baris hint keyboard (HUD HintLabel y = -46..-18)
	_root.anchor_left = 0.5
	_root.anchor_right = 0.5
	_root.anchor_top = 1.0
	_root.anchor_bottom = 1.0
	_root.offset_left = -286.0
	_root.offset_right = 286.0
	_root.offset_top = -152.0
	_root.offset_bottom = -52.0
	_root.add_theme_constant_override("separation", 12)
	add_child(_root)

	# ── panel info hero ──
	var panel := PanelContainer.new()
	panel.name = "HeroPanel"
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.custom_minimum_size = Vector2(250, 0)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.055, 0.09, 0.9)
	sb.border_color = Color(0.35, 0.5, 0.95, 0.85)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 10.0
	sb.content_margin_right = 10.0
	sb.content_margin_top = 6.0
	sb.content_margin_bottom = 6.0
	panel.add_theme_stylebox_override("panel", sb)
	_root.add_child(panel)

	_info = VBoxContainer.new()
	_info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_info.add_theme_constant_override("separation", 3)
	panel.add_child(_info)

	_name_label = Label.new()
	_name_label.add_theme_font_size_override("font_size", 15)
	_name_label.add_theme_color_override("font_color", Color(0.85, 0.92, 1.0))
	_name_label.text = "tidak ada hero dipilih"
	_info.add_child(_name_label)

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
	_hp_label.add_theme_font_size_override("font_size", 11)
	_hp_label.add_theme_color_override("font_color", Color(0.75, 0.95, 0.78))
	_info.add_child(_hp_label)

	_stats_label = Label.new()
	_stats_label.add_theme_font_size_override("font_size", 11)
	_stats_label.add_theme_color_override("font_color", Color(0.72, 0.78, 0.9))
	_info.add_child(_stats_label)

	_item_row = HBoxContainer.new()
	_item_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_item_row.add_theme_constant_override("separation", 4)
	_info.add_child(_item_row)
	for i in range(ITEM_SLOTS):
		var chip := Panel.new()
		chip.custom_minimum_size = Vector2(18, 18)
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var csb := StyleBoxFlat.new()
		csb.bg_color = Color(0.1, 0.11, 0.16, 0.95)
		csb.border_color = Color(0.3, 0.33, 0.42, 0.9)
		csb.set_border_width_all(1)
		csb.set_corner_radius_all(4)
		chip.add_theme_stylebox_override("panel", csb)
		chip.tooltip_text = "slot item %d kosong" % (i + 1)
		_item_row.add_child(chip)
		_item_chips.append(chip)

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
	hint.text = "klik hero untuk memilih · QWER / tombol = skill · B = toko"
	hint.add_theme_font_size_override("font_size", 10)
	hint.add_theme_color_override("font_color", Color(0.7, 0.76, 0.9, 0.75))
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


## Bagian yang tidak berubah tiap frame: nama hero, level, slot item
func _refresh_static() -> void:
	var h = GameManager.selected_hero
	if h != null and is_instance_valid(h) and not bool(h.get("is_dead")):
		_hero = h
	else:
		_hero = null
	var hero = _hero
	if hero == null:
		_name_label.text = "tidak ada hero dipilih"
		_stats_label.text = "B → HERO: beli hero, lalu klik untuk memilih"
		_hp_bar.value = 0.0
		_hp_label.text = ""
		_sync_items([])
		for k in SKILL_KEYS:
			_buttons[k].update_state(null)
		return
	var hdata: Dictionary = HeroDB.get_hero(str(hero.get("hero_type")))
	_name_label.text = "%s  ·  Lv %d" % [
		str(hdata.get("name", hero.get("hero_type"))), int(hero.get("level"))]
	_stats_label.text = "DMG %d · ARM %.0f · MR %.0f · RNG %d" % [
		int(hero.get("damage")), float(hero.get("armor")),
		float(hero.get("magic_resist")), int(hero.get("attack_range"))]
	var items = hero.get("items")
	_sync_items(items.item_ids() if items != null else [])
	for k in SKILL_KEYS:
		_buttons[k].update_state(hero)


func _sync_items(ids: Array) -> void:
	for i in range(_item_chips.size()):
		var chip: Panel = _item_chips[i]
		var sb := chip.get_theme_stylebox("panel") as StyleBoxFlat
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
			chip.tooltip_text = "slot item %d kosong" % (i + 1)
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
	_hp_label.text = "HP %d / %d%s" % [int(hp), int(max_hp),
		"  ·  MUNDUR" if bool(hero.get("is_retreating")) else ""]
	for k in SKILL_KEYS:
		_buttons[k].update_state(hero)
