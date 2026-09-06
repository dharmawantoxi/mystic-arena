# ShopPanel.gd — panel toko terpadu: MENARA / ITEM / HERO / NEXUS.
#
# Port dari _core.py: build popup (try_build_tower), shop item 6 slot
# (hero_items.ITEM_CATALOG), shop hero (unlocked_heroes) dan Castle upgrade
# (NEXUS_LEVELS + CASTLE_SHIELD_COST). pygame menggambar semua ini manual di
# surface; di Godot semuanya Control yang dibangun dari kode supaya HUD.tscn
# tidak perlu dirombak dan panel bisa dibuka/tutup lewat GameManager.shop_open.
#
# Semua aksi membeli lewat GameManager.try_*() — panel ini TIDAK memegang gold
# maupun state unit, jadi keyboard dan mouse memakai jalur yang sama.
extends Control

const TABS: Array = [["tower", "MENARA"], ["item", "ITEM"],
	["hero", "HERO"], ["nexus", "NEXUS"]]
const ITEM_COLUMNS := 3
## Seberapa sering panel menyegarkan angka yang bergerak (HP nexus / gold)
const REFRESH_INTERVAL := 0.25

const COL_BG := Color(0.045, 0.05, 0.085, 0.96)
const COL_BORDER := Color(1.0, 0.804, 0.333, 0.9)
const COL_TEXT := Color(0.86, 0.9, 1.0)
const COL_DIM := Color(0.68, 0.73, 0.85, 0.85)
const COL_GOLD := Color(1.0, 0.87, 0.38)

var _panel: PanelContainer = null
var _title: Label = null
var _gold_label: Label = null
var _tab_box: HBoxContainer = null
var _tab_buttons: Dictionary = {}
var _scroll: ScrollContainer = null
var _body: VBoxContainer = null
var _context: Label = null
var _tab: String = "tower"
var _refresh_timer: float = 0.0


func _ready() -> void:
	name = "ShopPanel"
	# root tembus klik; yang menahan klik hanya _panel (biar arena tetap bisa
	# diklik saat toko terbuka)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_build()
	GameManager.shop_changed.connect(_on_shop_changed)
	GameManager.selection_changed.connect(_on_selection_changed)
	GameManager.gold_changed.connect(_on_gold_changed)
	GameManager.tower_built.connect(_on_tower_built)
	GameManager.nexus_upgraded.connect(_on_nexus_upgraded)
	GameManager.difficulty_changed.connect(_on_difficulty_changed)
	_on_shop_changed()


# ══════════════════════════════════════════════════════════
#  KERANGKA UI
# ══════════════════════════════════════════════════════════

func _build() -> void:
	_panel = PanelContainer.new()
	_panel.name = "Panel"
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_panel.anchor_left = 0.5
	_panel.anchor_right = 0.5
	_panel.anchor_top = 0.5
	_panel.anchor_bottom = 0.5
	_panel.offset_left = -345.0
	_panel.offset_right = 345.0
	_panel.offset_top = -258.0
	_panel.offset_bottom = 132.0
	var sb := StyleBoxFlat.new()
	sb.bg_color = COL_BG
	sb.border_color = COL_BORDER
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(12)
	sb.content_margin_left = 14.0
	sb.content_margin_right = 14.0
	sb.content_margin_top = 10.0
	sb.content_margin_bottom = 10.0
	sb.shadow_color = Color(0, 0, 0, 0.5)
	sb.shadow_size = 12
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var vbox := VBoxContainer.new()
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.add_theme_constant_override("separation", 8)
	_panel.add_child(vbox)

	# ── header: judul + gold + tombol tutup ──
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	vbox.add_child(header)

	_title = Label.new()
	_title.text = "TOKO"
	_title.add_theme_font_size_override("font_size", 19)
	_title.add_theme_color_override("font_color", COL_GOLD)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(_title)

	_gold_label = Label.new()
	_gold_label.add_theme_font_size_override("font_size", 17)
	_gold_label.add_theme_color_override("font_color", COL_GOLD)
	header.add_child(_gold_label)

	var close_btn := Button.new()
	close_btn.text = "TUTUP  (B)"
	close_btn.custom_minimum_size = Vector2(96, 28)
	close_btn.pressed.connect(func(): GameManager.close_shop())
	header.add_child(close_btn)

	# ── tab ──
	_tab_box = HBoxContainer.new()
	_tab_box.add_theme_constant_override("separation", 6)
	vbox.add_child(_tab_box)
	var group := ButtonGroup.new()
	for pair in TABS:
		var b := Button.new()
		b.text = str(pair[1])
		b.toggle_mode = true
		b.button_group = group
		b.custom_minimum_size = Vector2(110, 30)
		b.pressed.connect(_on_tab_pressed.bind(str(pair[0])))
		_tab_box.add_child(b)
		_tab_buttons[str(pair[0])] = b

	# ── isi (bisa di-scroll: 33 item tidak muat sekali lihat) ──
	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(_scroll)

	_body = VBoxContainer.new()
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation", 5)
	_scroll.add_child(_body)

	# ── footer: konteks pilihan + gold ──
	_context = Label.new()
	_context.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_context.custom_minimum_size = Vector2(0, 30)
	_context.add_theme_font_size_override("font_size", 11)
	_context.add_theme_color_override("font_color", COL_DIM)
	vbox.add_child(_context)


# ══════════════════════════════════════════════════════════
#  SINKRON STATE
# ══════════════════════════════════════════════════════════

func _process(delta: float) -> void:
	if not visible:
		return
	_refresh_timer += delta
	if _refresh_timer < REFRESH_INTERVAL:
		return
	_refresh_timer = 0.0
	_update_gold_label()
	# Tab yang angkanya bergerak terus (HP nexus / HP hero) disegarkan berkala;
	# tab menara & item cukup disegarkan saat ada event.
	if _tab == "nexus" or _tab == "hero":
		_rebuild_body()


func _on_shop_changed() -> void:
	visible = GameManager.shop_open and GameManager.state == "playing"
	if visible:
		_update_gold_label()
		_sync_tab_buttons()
		_rebuild_body()


func _on_selection_changed() -> void:
	# Pilihan unit menentukan isi tab -> otomatis pindah ke tab yang relevan
	var t = GameManager.selected_tower
	var slot: Dictionary = GameManager.slot(GameManager.selected_slot)
	if t != null and is_instance_valid(t) and _tab != "tower":
		_tab = "tower"
	elif not slot.is_empty() and _tab != "tower":
		_tab = "tower"
	elif GameManager.selected_nexus != null and _tab != "nexus":
		_tab = "nexus"
	if visible:
		_sync_tab_buttons()
		_rebuild_body()


func _on_gold_changed(_amount: int) -> void:
	_update_gold_label()
	if visible and (_tab == "item" or _tab == "hero" or _tab == "tower"):
		_rebuild_body()


func _on_tower_built(_tower: Node) -> void:
	if visible:
		_rebuild_body()


func _on_nexus_upgraded(_team: String, _level: int) -> void:
	if visible:
		_rebuild_body()


func _on_difficulty_changed(_d: String) -> void:
	if visible:
		_rebuild_body()


func _on_tab_pressed(tab_id: String) -> void:
	_tab = tab_id
	_sync_tab_buttons()
	_rebuild_body()


func _sync_tab_buttons() -> void:
	for key in _tab_buttons:
		var b: Button = _tab_buttons[key]
		b.set_pressed_no_signal(str(key) == _tab)


func _update_gold_label() -> void:
	_gold_label.text = "%d gold  (+%s/s)" % [
		GameManager.gold, GameManager.format_gold_rate(GameManager.gold_per_second)]


# ══════════════════════════════════════════════════════════
#  ISI PANEL
# ══════════════════════════════════════════════════════════

func _rebuild_body() -> void:
	for c in _body.get_children():
		_body.remove_child(c)
		c.queue_free()
	match _tab:
		"item":
			_build_item_tab()
		"hero":
			_build_hero_tab()
		"nexus":
			_build_nexus_tab()
		_:
			_build_tower_tab()
	_update_context()


func _update_context() -> void:
	var parts: Array = []
	var h = GameManager.selected_hero
	if h != null and is_instance_valid(h):
		parts.append("hero: %s Lv%d" % [str(h.get("hero_type")), int(h.get("level"))])
	var t = GameManager.selected_tower
	if t != null and is_instance_valid(t):
		parts.append("menara: %s" % str(t.get("display_name")))
	var s: Dictionary = GameManager.slot(GameManager.selected_slot)
	if not s.is_empty():
		parts.append("slot: lane %s (%s)" % [str(s["lane"]),
			"Radiant" if str(s["team"]) == "blue" else "Dire"])
	var nx = GameManager.blue_nexus
	if nx != null and is_instance_valid(nx):
		parts.append("nexus: Lv%d" % int(nx.get("level")))
	_context.text = "[%s]  %s · gold %d · AI %d · difficulty %s · D ganti difficulty" % [
		_tab.to_upper(), " | ".join(parts) if not parts.is_empty() else "tidak ada yang dipilih",
		GameManager.gold, GameManager.ai_gold, GameManager.difficulty.to_upper()]


# ── TAB MENARA ────────────────────────────────────────────

func _build_tower_tab() -> void:
	var t = GameManager.selected_tower
	if t != null and is_instance_valid(t) and not bool(t.get("is_dead")):
		_tower_detail(t)
		return
	var s: Dictionary = GameManager.slot(GameManager.selected_slot)
	if not s.is_empty():
		if str(s["team"]) != "blue":
			_add_label("Slot ini milik Dire — tidak bisa dibangun.", COL_DIM)
			return
		if bool(s["taken"]):
			_add_label("Slot sudah terisi menara.", COL_DIM)
			return
		var cost := TowerDB.build_cost()
		_add_label("Slot kosong di lane %s — bangun menara Lv1 (%d gold)" % [
			str(s["lane"]).to_upper(), cost], COL_TEXT, 15)
		var grid := GridContainer.new()
		grid.columns = 2
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 6)
		_body.add_child(grid)
		for tt in TowerDB.tower_types():
			var ti: Dictionary = TowerDB.type_info(str(tt))
			var b := _make_button("%s %s — %d g" % [
					str(ti.get("icon", "")), str(ti.get("name", tt)), cost],
				"%s\n%s\nCatatan: stat Lv1 semua jalur sama (Archer Lv1); "
				% [str(ti.get("desc", "")), str(ti.get("special", ""))]
				+ "kekuatannya baru muncul setelah upgrade ke Lv2.",
				_build_tower.bind(str(tt)), GameManager.gold >= cost)
			b.custom_minimum_size = Vector2(320, 34)
			grid.add_child(b)
		_add_label("Upgrade Lv1 -> Lv2 memilih jalur dan menaikkan HP x%.2f."
			% TowerDB.hp_multiplier(), COL_DIM, 11)
		return
	_add_label("Klik lingkaran slot di lane untuk membangun menara.", COL_TEXT, 14)
	_add_label("Slot kosong: Radiant %d · Dire %d  (3 slot per lane per tim)" % [
		GameManager.free_slots_for("blue").size(), GameManager.free_slots_for("red").size()],
		COL_DIM)
	_add_label("Klik menara milikmu untuk upgrade / jual / Regen Shield.", COL_DIM)


func _tower_detail(t) -> void:
	var info: Dictionary = TowerDB.type_info(str(t.get("tower_type")))
	_add_label("%s" % str(t.get("display_name")), COL_GOLD, 16)
	_add_label("%s — %s" % [str(info.get("name", "")), str(info.get("desc", ""))], COL_TEXT, 12)
	_add_label("HP %d/%d · Shield %d/%d · DMG %d (%s) · RNG %d · CD %.2fs · Armor %d" % [
		int(t.get("hp")), int(t.get("max_hp")), int(t.get("shield")), int(t.get("shield_max")),
		int(t.get("damage")), str(t.get("dmg_school")), int(t.get("attack_range")),
		float(t.get("attack_cooldown")), int(t.get("armor"))], COL_DIM, 11)
	_add_label("Spesial: %s" % str(info.get("special", "-")), COL_DIM, 11)
	if not bool(t.get("is_player_built")):
		_add_label("Menara Dire — tidak bisa di-upgrade atau dijual.", COL_DIM)
		return

	if t.can_upgrade():
		if TowerDB.can_choose_path(int(t.get("level"))):
			_add_label("Pilih jalur upgrade ke Lv2:", COL_TEXT, 13)
			var grid := GridContainer.new()
			grid.columns = 2
			grid.add_theme_constant_override("h_separation", 6)
			grid.add_theme_constant_override("v_separation", 6)
			_body.add_child(grid)
			for tt in TowerDB.tower_types():
				var ti: Dictionary = TowerDB.type_info(str(tt))
				var cost: int = t.upgrade_cost(str(tt))
				var b := _make_button("%s — %d g" % [str(ti.get("name", tt)), cost],
					"%s\n%s" % [str(ti.get("desc", "")), str(ti.get("special", ""))],
					_pick_path.bind(t, str(tt)), GameManager.gold >= cost)
				b.custom_minimum_size = Vector2(320, 34)
				grid.add_child(b)
		else:
			var cost: int = t.upgrade_cost(str(t.get("tower_type")))
			_add_button("Upgrade ke Lv%d — %d gold" % [int(t.get("level")) + 1, cost],
				"HP x%.2f, damage & jangkauan naik." % TowerDB.hp_multiplier(),
				func(): _run(func(): GameManager.try_upgrade_tower("")),
				GameManager.gold >= cost)
	else:
		_add_label("Level maksimum (%d) tercapai." % TowerDB.max_level(), COL_DIM)

	if bool(t.get("regen_shield_active")):
		_add_label("Regen Shield: AKTIF (shield pulih setelah 3 detik tidak kena damage)",
			Color(0.55, 0.95, 0.65))
	elif t.has_method("can_activate_regen_shield") and t.can_activate_regen_shield():
		_add_button("Beli Regen Shield — %d gold" % t.regen_shield_cost(),
			"Shield menara ikut regen (paritas Tower.activate_regen_shield).",
			func(): _run(func(): GameManager.try_buy_tower_regen_shield()),
			GameManager.gold >= int(t.regen_shield_cost()))
	else:
		_add_label("Regen Shield terbuka di Lv%d+ (harga %d gold)" % [
			TowerDB.regen_shield_min_level(), TowerDB.regen_shield_cost()], COL_DIM, 11)

	_add_button("Jual menara (+%d gold)" % int(t.sell_value()),
		"Refund 50% dari total biaya upgrade yang sudah dibayar.",
		func(): _run(func(): GameManager.try_sell_tower()), true)


func _build_tower(tower_type: String) -> void:
	_run(func(): GameManager.try_build_tower(tower_type))


func _pick_path(t, target_type: String) -> void:
	GameManager.select_tower(t)
	_run(func(): GameManager.try_upgrade_tower(target_type))


# ── TAB ITEM ──────────────────────────────────────────────

func _build_item_tab() -> void:
	var h = _player_hero()
	if h == null:
		_add_label("Pilih hero Radiant dulu (klik hero biru di arena).", COL_TEXT, 14)
		_add_label("Item dibeli per hero: 6 slot, harga flat %d gold." % ItemDB.flat_cost(), COL_DIM)
		return
	var items = h.get("items")
	var hdata: Dictionary = HeroDB.get_hero(str(h.get("hero_type")))
	_add_label("%s — %d/%d slot item" % [
		str(hdata.get("name", h.get("hero_type"))),
		items.count() if items != null else 0, ItemDB.max_slots()], COL_GOLD, 15)
	_add_label("Tipe serangan: %s · %s — item bertanda hanya untuk tipe itu." % [
		str(h.get("dmg_school")), "MELEE" if bool(h.get("is_melee_hero")) else "RANGED"], COL_DIM, 11)
	# baris item yang sudah dimiliki
	var owned: Array = items.item_ids() if items != null else []
	var owned_text: Array = []
	for id in owned:
		if str(id) != "":
			owned_text.append(ItemDB.item_name(str(id)))
	_add_label("Dimiliki: %s" % (", ".join(owned_text) if not owned_text.is_empty() else "-"),
		Color(0.6, 0.9, 0.7), 11)

	var grouped: Dictionary = ItemDB.grouped()
	for cat in grouped:
		var col: Color = ItemDB.category_color(str(cat))
		_add_label("%s" % ItemDB.category_label(str(cat)), col, 13)
		var grid := GridContainer.new()
		grid.columns = ITEM_COLUMNS
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 4)
		_body.add_child(grid)
		for item_id in grouped[cat]:
			var iid := str(item_id)
			var cost := ItemDB.item_cost(iid)
			var can: bool = items != null and items.can_equip(iid)
			var have: bool = items != null and items.has(iid)
			var label := "%s — %d g" % [ItemDB.item_name(iid), cost]
			if have:
				label = "%s — dimiliki" % ItemDB.item_name(iid)
			var tip := "%s\n%s" % [ItemDB.item_desc(iid),
				"" if can else ("Sudah dimiliki" if have else "Tidak cocok untuk hero ini")]
			var b := _make_button(label, tip, _buy_item.bind(iid),
				can and not have and GameManager.gold >= cost)
			b.custom_minimum_size = Vector2(214, 30)
			b.add_theme_color_override("font_color",
				ItemDB.item_color(iid) if (can and not have) else COL_DIM)
			grid.add_child(b)


func _buy_item(item_id: String) -> void:
	_run(func(): GameManager.try_buy_item(item_id))


# ── TAB HERO ──────────────────────────────────────────────

func _build_hero_tab() -> void:
	var h = _player_hero()
	if h != null:
		var hdata: Dictionary = HeroDB.get_hero(str(h.get("hero_type")))
		_add_label("%s — Lv %d / %d" % [
			str(hdata.get("name", h.get("hero_type"))), int(h.get("level")),
			HeroDB.max_hero_level], COL_GOLD, 15)
		_add_label("HP %d/%d · DMG %d · Skill DMG %d · Armor %.0f · MR %.0f · RNG %d" % [
			int(h.get("hp")), int(h.get("max_hp")), int(h.get("damage")),
			int(h.get("skill_damage")), float(h.get("armor")),
			float(h.get("magic_resist")), int(h.get("attack_range"))], COL_DIM, 11)
		if h.can_upgrade():
			var cost: int = h.upgrade_cost()
			var next: Dictionary = HeroDB.level_data(int(h.get("level")) + 1)
			_add_button("Upgrade ke Lv%d — %d gold" % [int(h.get("level")) + 1, cost],
				"HP x%.2f · damage x%.2f · skill x%.2f" % [
					float(next.get("hp_mult", 1.0)), float(next.get("dmg_mult", 1.0)),
					float(next.get("skill_mult", 1.0))],
				func(): _run(func(): GameManager.try_upgrade_hero()),
				GameManager.gold >= cost)
		else:
			_add_label("Level maksimum tercapai.", COL_DIM)
	else:
		_add_label("Pilih hero Radiant untuk melihat status & upgrade.", COL_TEXT, 14)

	_add_label("Beli hero (yang sudah di-unlock):", COL_TEXT, 13)
	var unlocked = SaveManager.data.get("unlocked_heroes", [])
	if not (unlocked is Array):
		unlocked = []
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 4)
	_body.add_child(grid)
	for ht in unlocked:
		var htype := str(ht)
		var d: Dictionary = HeroDB.get_hero(htype)
		if d.is_empty():
			continue
		var cost := int(d.get("cost", 400))
		var b := _make_button("%s (%s) — %d g" % [
				str(d.get("name", htype)), str(d.get("role", "-")), cost],
			"%s\nHP %d · DMG %d · RANGE %d · %s" % [str(d.get("description", "")),
				int(d.get("hp", 0)), int(d.get("damage", 0)), int(d.get("range", 0)),
				str(d.get("dmg_type", "PHYSICAL"))],
			_buy_hero.bind(htype), GameManager.gold >= cost)
		b.custom_minimum_size = Vector2(320, 30)
		grid.add_child(b)
	_add_label("Hero lain (%d total di heroes.json) terbuka lewat progres level — "
		% HeroDB.get_all_types().size()
		+ "lihat SaveManager.unlocked_heroes.", COL_DIM, 11)


func _buy_hero(hero_type: String) -> void:
	_run(func(): GameManager.try_buy_hero(hero_type))


# ── TAB NEXUS ─────────────────────────────────────────────

func _build_nexus_tab() -> void:
	var nx = GameManager.blue_nexus
	if nx == null or not is_instance_valid(nx) or bool(nx.get("is_dead")):
		_add_label("Radiant Nexus sudah hancur.", Color(1, 0.5, 0.5), 14)
		return
	_add_label("Radiant Nexus — Lv %d / %d" % [int(nx.get("level")), TowerDB.nexus_max_level()],
		COL_GOLD, 15)
	_add_label("HP %d/%d · Shield %d/%d · DMG %d · RNG %d · skala minion %.2fx" % [
		int(nx.get("hp")), int(nx.get("max_hp")), int(nx.get("shield")),
		int(nx.get("shield_max")), int(nx.get("damage")), int(nx.get("attack_range")),
		float(nx.get("minion_scale"))], COL_DIM, 11)
	if nx.can_upgrade():
		var cost: int = nx.upgrade_cost()
		var nxt: Dictionary = TowerDB.nexus_stats(int(nx.get("level")) + 1)
		_add_button("Upgrade Nexus ke Lv%d — %d gold" % [int(nx.get("level")) + 1, cost],
			"HP %d · DMG %d · RNG %d · shield ratio HP naik" % [
				int(nxt.get("hp", 0)), int(nxt.get("damage", 0)), int(nxt.get("range", 0))],
			func(): _run(func(): GameManager.try_upgrade_nexus()),
			GameManager.gold >= cost)
	else:
		_add_label("Nexus sudah level maksimum.", COL_DIM)
	if bool(nx.get("shield_active")) and bool(nx.get("free_shield_active")):
		_add_label("Castle Shield GRATIS aktif (sampai wave 10) — damage tersisa "
			+ "dikurangi %.0f%%." % (float(nx.get("shield_damage_reduction")) * 100.0),
			Color(0.6, 0.85, 1.0), 11)
	if nx.can_buy_shield():
		var cost: int = nx.shield_cost()
		_add_button("Beli Castle Shield — %d gold" % cost,
			"Shield permanen: menyerap damage 1:1, sisanya dimitigasi %.0f%%."
			% (float(nx.get("shield_damage_reduction")) * 100.0),
			func(): _run(func(): GameManager.try_buy_nexus_shield()),
			GameManager.gold >= cost)
	elif bool(nx.get("castle_shield_purchased")):
		_add_label("Castle Shield sudah dibeli.", Color(0.6, 0.95, 0.7))

	var enemy = GameManager.red_nexus
	if enemy != null and is_instance_valid(enemy):
		_add_label("Dire Nexus: Lv%d · HP %d/%d · shield %d/%d — hancurkan untuk MENANG." % [
			int(enemy.get("level")), int(enemy.get("hp")), int(enemy.get("max_hp")),
			int(enemy.get("shield")), int(enemy.get("shield_max"))],
			Color(1.0, 0.62, 0.62), 12)


# ══════════════════════════════════════════════════════════
#  WIDGET HELPER
# ══════════════════════════════════════════════════════════

## Hero Radiant yang sedang dipilih (masih hidup)
func _player_hero():
	var h = GameManager.selected_hero
	if h == null or not is_instance_valid(h) or bool(h.get("is_dead")):
		return null
	if str(h.get("team")) != "blue":
		return null
	return h


## Jalankan aksi beli lalu segarkan panel (signal GameManager bisa tidak muncul
## kalau aksinya gagal — gold kurang, slot terisi, dsb)
func _run(action: Callable) -> void:
	if get_tree().paused:
		return # SkillBar/ShopPanel PROCESS_MODE_ALWAYS -> kunci aksi saat pause
	if action.is_valid():
		action.call()
	_update_gold_label()
	_rebuild_body()


func _add_label(text_val: String, col: Color = COL_TEXT, font_size: int = 12) -> Label:
	var l := Label.new()
	l.text = text_val
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", col)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_body.add_child(l)
	return l


func _add_button(label: String, tooltip: String, cb: Callable, enabled: bool) -> Button:
	var b := _make_button(label, tooltip, cb, enabled)
	b.custom_minimum_size = Vector2(0, 32)
	_body.add_child(b)
	return b


func _make_button(label: String, tooltip: String, cb: Callable, enabled: bool) -> Button:
	var b := Button.new()
	b.text = label
	b.tooltip_text = tooltip
	b.disabled = not enabled
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 12)
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.11, 0.13, 0.2, 0.95) if enabled else Color(0.08, 0.09, 0.13, 0.9)
	normal.border_color = Color(0.42, 0.5, 0.72, 0.85) if enabled else Color(0.22, 0.24, 0.3, 0.7)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(6)
	normal.content_margin_left = 10.0
	normal.content_margin_right = 10.0
	normal.content_margin_top = 5.0
	normal.content_margin_bottom = 5.0
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color(0.18, 0.22, 0.33, 1.0)
	hover.border_color = COL_GOLD
	var pressed := normal.duplicate() as StyleBoxFlat
	pressed.bg_color = Color(0.26, 0.22, 0.1, 1.0)
	var disabled := normal.duplicate() as StyleBoxFlat
	disabled.bg_color = Color(0.07, 0.075, 0.1, 0.9)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("focus", hover)
	b.add_theme_stylebox_override("disabled", disabled)
	b.add_theme_color_override("font_color", COL_TEXT if enabled else Color(0.45, 0.47, 0.55))
	b.add_theme_color_override("font_hover_color", Color(1, 0.95, 0.7))
	if enabled and cb.is_valid():
		b.pressed.connect(cb)
	return b
