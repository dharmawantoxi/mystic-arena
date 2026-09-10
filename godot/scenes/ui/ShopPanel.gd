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
var _scrim: ColorRect = null
var _close_button: Button = null
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
	MobileLayout.layout_changed.connect(_layout_panel)
	_layout_panel()
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

## Popup TOWER/CASTLE tampil di panel kanan (rail); HERO/ITEM sebagai modal
## besar di tengah — pembagian yang sama dengan screenshot pygame.
const RAIL_TABS := ["tower", "nexus"]

func _build() -> void:
	# Latar gelap modal (hanya untuk HERO SHOP / ITEM FORGE) — menelan klik
	# supaya tombol di belakang modal tidak ikut tertekan.
	_scrim = ColorRect.new()
	_scrim.name = "Scrim"
	_scrim.color = Color(0.02, 0.02, 0.04, 0.55)
	_scrim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_scrim.mouse_filter = Control.MOUSE_FILTER_STOP
	_scrim.visible = false
	add_child(_scrim)

	_panel = PygamePanel.new(COL_BORDER, 2.0, 12.0)
	_panel.name = "Panel"
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	# Anchor kiri-atas + offset absolut: SEMUA posisi dihitung _layout_panel
	# dari MobileLayout, jadi panel tidak pernah keluar frame.
	_panel.anchor_left = 0.0
	_panel.anchor_top = 0.0
	_panel.anchor_right = 0.0
	_panel.anchor_bottom = 0.0
	(_panel as PygamePanel).set_margins(14, 10, 14, 10)
	add_child(_panel)

	# PEMBATAS UKURAN: _panel adalah PanelContainer — minimum size-nya
	# mengikuti konten (isi tab menara bisa >2000 px) sehingga offset
	# _layout_panel di-clamp engine ke tinggi konten dan popup/modal
	# meluber keluar frame. Control polos ini memutus rantai minimum-size
	# (anak Control polos tidak menyumbang min-size): _panel mengepas clip
	# ke rect-nya, vbox full-rect di dalam clip, dan ScrollContainer
	# benar-benar menggulir isi panjang di ruang yang tersedia.
	var clip := Control.new()
	clip.name = "ShopClip"
	clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(clip)

	var vbox := VBoxContainer.new()
	vbox.name = "ShopBox"
	vbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	vbox.add_theme_constant_override("separation", 8)
	clip.add_child(vbox)

	# ── header: judul + gold + tombol tutup ──
	var header := HBoxContainer.new()
	header.name = "ShopHeader"
	header.add_theme_constant_override("separation", 10)
	vbox.add_child(header)

	_title = Label.new()
	UiTheme.style_label(_title, "TOKO", UiTheme.title_font(), 24,
		COL_GOLD)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_title.clip_text = true
	header.add_child(_title)

	_gold_label = Label.new()
	UiTheme.style_label(_gold_label, "", UiTheme.body_bold(), 17,
		COL_GOLD)
	header.add_child(_gold_label)

	# Tombol tutup TIDAK boleh menyusut/terpotong: ukuran minimum tetap dan
	# selalu di dalam margin panel.
	var close_btn := PygameButton.pill_button("TUTUP  (H)", "neutral",
		"", 104, 28, 13)
	close_btn.name = "ShopClose"
	close_btn.custom_minimum_size = Vector2(104, 28)
	close_btn.size_flags_horizontal = Control.SIZE_SHRINK_END
	close_btn.mouse_filter = Control.MOUSE_FILTER_STOP
	close_btn.set_meta("ui_key", "shop_close")
	close_btn.pressed.connect(func(): GameManager.close_shop())
	header.add_child(close_btn)
	_close_button = close_btn

	# ── tab ──
	_tab_box = HBoxContainer.new()
	_tab_box.name = "ShopTabs"
	_tab_box.add_theme_constant_override("separation", 6)
	vbox.add_child(_tab_box)
	var group := ButtonGroup.new()
	var tab_accents := {"tower": Color(1.0, 0.7, 0.4),
		"item": UiTheme.VIOLET, "hero": UiTheme.GREEN, "nexus": COL_GOLD}
	for pair in TABS:
		var tab_id := str(pair[0])
		var b := PygameButton.tab_button(str(pair[1]),
			tab_accents.get(tab_id, COL_GOLD), 110, 30, 15)
		b.button_group = group
		b.mouse_filter = Control.MOUSE_FILTER_STOP
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.set_meta("ui_key", "to_" + tab_id)
		b.pressed.connect(_on_tab_pressed.bind(tab_id))
		_tab_box.add_child(b)
		_tab_buttons[tab_id] = b

	# ── isi (bisa di-scroll: 33 item tidak muat sekali lihat) ──
	_scroll = ScrollContainer.new()
	_scroll.name = "ShopScroll"
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(_scroll)

	_body = VBoxContainer.new()
	_body.name = "ShopBody"
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_theme_constant_override("separation", 5)
	_scroll.add_child(_body)

	# ── footer: konteks pilihan + gold ──
	_context = Label.new()
	_context.name = "ShopContext"
	_context.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_context.custom_minimum_size = Vector2(0, 30)
	UiTheme.style_label(_context, "", UiTheme.body_regular(), 11,
		COL_DIM)
	vbox.add_child(_context)


## true kalau tab aktif memakai popup panel kanan (TOWER/CASTLE SHOP).
func _uses_rail_popup() -> bool:
	return MobileLayout.has_side_panel() and RAIL_TABS.has(_tab)


## Tempatkan panel: popup di panel kanan (tower/castle) atau modal tengah
## (hero/item). Semua koordinat dijepit ke dalam viewport supaya tombol tidak
## pernah keluar frame.
func _layout_panel() -> void:
	if _panel == null:
		return
	var rect: Rect2
	if _uses_rail_popup():
		rect = MobileLayout.rail_popup_rect()
		_scrim.visible = false
	else:
		rect = MobileLayout.modal_rect()
		_scrim.visible = visible
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		rect = MobileLayout.modal_rect()
	var vp := MobileLayout.viewport_size
	rect.position.x = clampf(rect.position.x, 0.0,
		maxf(0.0, vp.x - rect.size.x))
	rect.position.y = clampf(rect.position.y, 0.0,
		maxf(0.0, vp.y - rect.size.y))
	_panel.anchor_left = 0.0
	_panel.anchor_top = 0.0
	_panel.anchor_right = 0.0
	_panel.anchor_bottom = 0.0
	_panel.offset_left = rect.position.x
	_panel.offset_top = rect.position.y
	_panel.offset_right = rect.position.x + rect.size.x
	_panel.offset_bottom = rect.position.y + rect.size.y
	_apply_compact(rect.size.x < 420.0)


## Popup panel kanan sempit (±280 px): judul & tab dikecilkan, teks tombol
## tutup dipendekkan supaya semuanya tetap muat dan bisa diklik.
func _apply_compact(compact: bool) -> void:
	if _title != null:
		_title.add_theme_font_size_override("font_size", 16 if compact else 24)
	if _gold_label != null:
		_gold_label.add_theme_font_size_override("font_size",
			12 if compact else 17)
	if _close_button != null:
		_close_button.text = "X" if compact else "TUTUP  (H)"
		_close_button.custom_minimum_size = Vector2(
			34 if compact else 104, 28)
	if _tab_box != null:
		_tab_box.add_theme_constant_override("separation", 3 if compact else 6)
		for key in _tab_buttons:
			var b: Button = _tab_buttons[key]
			b.custom_minimum_size = Vector2(0, 26 if compact else 30)
			b.add_theme_font_size_override("font_size", 10 if compact else 15)
	if _context != null:
		_context.visible = not compact


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


func open_tab(tab_id: String) -> void:
	if TABS.any(func(pair): return str(pair[0]) == tab_id):
		_tab = tab_id
	GameManager.open_shop()
	_layout_panel()
	# open_shop() no-op kalau toko SUDAH buka (tanpa emit) — badan harus
	# dibangun ulang sinkron, kalau tidak tab menampilkan isi basi (bug yang
	# dikunci UiHudParityTest: kunci koleksi seusai open_tab).
	_sync_tab_buttons()
	_update_gold_label()
	_rebuild_body()


func _on_shop_changed() -> void:
	# Tab yang diminta eksplisit (ITEM FORGE) menang atas tab terakhir.
	if GameManager.requested_shop_tab != "":
		_tab = GameManager.requested_shop_tab
		GameManager.requested_shop_tab = ""
	visible = GameManager.shop_open and GameManager.state == "playing"
	_layout_panel()
	if visible:
		_update_gold_label()
		_sync_tab_buttons()
		_rebuild_body()
	elif _scrim != null:
		_scrim.visible = false


func collect_ui_keys() -> Array:
	var keys: Array = []
	_collect_keys_in(self, keys)
	return keys


func _collect_keys_in(node: Node, keys: Array) -> void:
	for c in node.get_children():
		if c is Button and c.has_meta("ui_key"):
			keys.append(str(c.get_meta("ui_key")))
		_collect_keys_in(c, keys)


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
	_layout_panel()
	_rebuild_body()


func _sync_tab_buttons() -> void:
	for key in _tab_buttons:
		var b: Button = _tab_buttons[key]
		b.set_pressed_no_signal(str(key) == _tab)


func _update_gold_label() -> void:
	_gold_label.text = "%s gold  (+%s/s)" % [
		HudLayout.format_thousands(GameManager.gold),
		GameManager.format_gold_rate(GameManager.gold_per_second)]


# ══════════════════════════════════════════════════════════
#  ISI PANEL
# ══════════════════════════════════════════════════════════

func _rebuild_body() -> void:
	for c in _body.get_children():
		_body.remove_child(c)
		c.queue_free()
	# Grid 2 kolom tidak muat di popup panel kanan -> jadi 1 kolom.
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
		parts.append("hero: %s Lv.%d" % [str(h.get("hero_type")), int(h.get("level"))])
	var t = GameManager.selected_tower
	if t != null and is_instance_valid(t):
		parts.append("menara: %s" % str(t.get("display_name")))
	var s: Dictionary = GameManager.slot(GameManager.selected_slot)
	if not s.is_empty():
		parts.append("slot: lane %s (%s)" % [str(s["lane"]),
			"Radiant" if str(s["team"]) == "blue" else "Dire"])
	var nx = GameManager.blue_nexus
	if nx != null and is_instance_valid(nx):
		parts.append("nexus: Lv.%d" % int(nx.get("level")))
	_context.text = "[%s]  %s · gold %d · AI %d · difficulty %s" % [
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
		grid.columns = _pair_columns()
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 6)
		_body.add_child(grid)
		for tt in TowerDB.tower_types():
			var ti: Dictionary = TowerDB.type_info(str(tt))
			var afford := GameManager.gold >= cost
			var b := _make_button("%s %s — %d g" % [
					str(ti.get("icon", "")), str(ti.get("name", tt)), cost],
				"%s\n%s\nCatatan: stat Lv1 semua jalur sama (Archer Lv1); "
				% [str(ti.get("desc", "")), str(ti.get("special", ""))]
				+ "kekuatannya baru muncul setelah upgrade ke Lv2.",
				_build_tower.bind(str(tt)), afford, "build_" + str(tt),
				{"cost": cost, "blocked": "" if afford else "POOR"}, "gold")
			b.custom_minimum_size = Vector2(_row_width(_pair_columns()), 34)
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
			grid.columns = _pair_columns()
			grid.add_theme_constant_override("h_separation", 6)
			grid.add_theme_constant_override("v_separation", 6)
			_body.add_child(grid)
			for tt in TowerDB.tower_types():
				var ti: Dictionary = TowerDB.type_info(str(tt))
				var cost: int = t.upgrade_cost(str(tt))
				var afford := GameManager.gold >= cost
				var b := _make_button("%s — %d g" % [str(ti.get("name", tt)), cost],
					"%s\n%s" % [str(ti.get("desc", "")), str(ti.get("special", ""))],
					_pick_path.bind(t, str(tt)), afford, "repath_" + str(tt),
					{"cost": cost, "blocked": "" if afford else "POOR"}, "gold")
				b.custom_minimum_size = Vector2(_row_width(_pair_columns()), 34)
				grid.add_child(b)
		else:
			var cost: int = t.upgrade_cost(str(t.get("tower_type")))
			var afford := GameManager.gold >= cost
			_add_button("Upgrade ke Lv.%d — %d gold" % [int(t.get("level")) + 1, cost],
				"HP x%.2f, damage & jangkauan naik." % TowerDB.hp_multiplier(),
				# ui_upgrade 0.5 — paritas _core.py:2481 / 7243 / 7341
				func(): _run(func(): GameManager.try_upgrade_tower(""), "ui_upgrade", 0.5),
				afford, "upgrade_tower",
				{"cost": cost, "blocked": "" if afford else "POOR"}, "gold")
	else:
		_add_label("Level maksimum (%d) tercapai." % TowerDB.max_level(), COL_DIM)

	if bool(t.get("regen_shield_active")):
		_add_label("Regen Shield: AKTIF (shield pulih setelah 3 detik tidak kena damage)",
			Color(0.55, 0.95, 0.65))
	elif t.has_method("can_activate_regen_shield") and t.can_activate_regen_shield():
		var rcost := int(t.regen_shield_cost())
		var afford := GameManager.gold >= rcost
		_add_button("Beli Regen Shield — %d gold" % rcost,
			"Shield menara ikut regen (paritas Tower.activate_regen_shield).",
			# ui_upgrade 0.5 — paritas _try_activate_regen_shield _core.py:8240
			func(): _run(func(): GameManager.try_buy_tower_regen_shield(), "ui_upgrade", 0.5),
			afford, "tower_regen",
			{"cost": rcost, "blocked": "" if afford else "POOR"}, "cyan")
	else:
		_add_label("Regen Shield terbuka di Lv.%d+ (harga %d gold)" % [
			TowerDB.regen_shield_min_level(), TowerDB.regen_shield_cost()], COL_DIM, 11)

	# Popup tower Lv1 pygame TAK punya tombol jual (refund +50 fallback cuma
	# terjangkau via handler) — tombol disembunyikan di Lv1.
	if int(t.get("level")) > 1:
		_add_button("Jual menara (+%d gold)" % int(t.sell_value()),
			"Refund 50% dari total biaya upgrade yang sudah dibayar.",
			# ui_sell 1.0 — paritas _try_sell_tower _core.py:8219
			func(): _run(func(): GameManager.try_sell_tower(), "ui_sell"), true,
			"sell_tower", {"refund": int(t.sell_value())}, "danger")


func _build_tower(tower_type: String) -> void:
	# ui_buy 1.0 — paritas Game.try_build_tower _core.py:1652
	_run(func(): GameManager.try_build_tower(tower_type), "ui_buy")


func _pick_path(t, target_type: String) -> void:
	GameManager.select_tower(t)
	_run(func(): GameManager.try_upgrade_tower(target_type), "ui_upgrade", 0.5)


# ── TAB ITEM ──────────────────────────────────────────────

func _build_item_tab() -> void:
	var h = _player_hero()
	if h == null:
		_add_label("Pilih hero Radiant dulu (klik hero biru di arena).", COL_TEXT, 14)
		_add_label("Item dibeli per hero: 6 slot, harga 4500-6000 gold per tier.", COL_DIM)
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
		grid.columns = _grid_columns()
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 4)
		_body.add_child(grid)
		for item_id in grouped[cat]:
			var iid := str(item_id)
			var cost := ItemDB.item_cost(iid)
			var can: bool = items != null and items.can_equip(iid)
			var have: bool = items != null and items.has(iid)
			var afford := GameManager.gold >= cost
			var reason := ""
			if items != null:
				reason = items.equip_block_reason(iid)
			if reason == "" and not afford:
				reason = "POOR"
			var label := "%s — %d g" % [ItemDB.item_name(iid), cost]
			if have:
				label = "%s — dimiliki" % ItemDB.item_name(iid)
			var tip := "%s\n%s" % [ItemDB.item_desc(iid), _item_reason_tip(reason)]
			var b := _make_button(label, tip, _buy_item.bind(iid),
				can and not have and afford, "item_buy_" + iid,
				{"cost": cost, "blocked": reason})
			b.custom_minimum_size = Vector2(_row_width(_grid_columns()), 30)
			b.add_theme_color_override("font_color",
				ItemDB.item_color(iid) if (can and not have) else COL_DIM)
			grid.add_child(b)


## Teks alasan disabled item (MELEE ONLY/MAGIC ONLY = label kartu pygame).
static func _item_reason_tip(reason: String) -> String:
	match reason:
		"OWNED":
			return "Sudah dimiliki"
		"FULL":
			return "Slot penuh (6/6)"
		"MELEE ONLY":
			return "MELEE ONLY — hero ini ranged"
		"MAGIC ONLY":
			return "MAGIC ONLY — hero ini bukan magic"
		"POOR":
			return "Gold kurang"
	return ""


func _buy_item(item_id: String) -> void:
	# ui_buy 1.0 — paritas pembelian item di toko (_core.py:2637)
	_run(func(): GameManager.try_buy_item(item_id), "ui_buy")


# ── TAB HERO ──────────────────────────────────────────────

func _build_hero_tab() -> void:
	var h = _player_hero()
	if h != null:
		var hdata: Dictionary = HeroDB.get_hero(str(h.get("hero_type")))
		_add_label("%s — Lv.%d / %d" % [
			str(hdata.get("name", h.get("hero_type"))), int(h.get("level")),
			HeroDB.max_hero_level], COL_GOLD, 15)
		_add_label("HP %d/%d · DMG %d · Skill DMG %d · Armor %.0f · MR %.0f · RNG %d" % [
			int(h.get("hp")), int(h.get("max_hp")), int(h.get("damage")),
			int(h.get("skill_damage")), float(h.get("armor")),
			float(h.get("magic_resist")), int(h.get("attack_range"))], COL_DIM, 11)
		if h.can_upgrade():
			var cost: int = h.upgrade_cost()
			var next: Dictionary = HeroDB.level_data(int(h.get("level")) + 1)
			var afford := GameManager.gold >= cost
			_add_button("Upgrade ke Lv.%d — %d gold" % [int(h.get("level")) + 1, cost],
				"HP x%.2f · damage x%.2f · skill x%.2f" % [
					float(next.get("hp_mult", 1.0)), float(next.get("dmg_mult", 1.0)),
					float(next.get("skill_mult", 1.0))],
				# ui_upgrade 0.6 — paritas upgrade hero _core.py:7243
				func(): _run(func(): GameManager.try_upgrade_hero(), "ui_upgrade", 0.6),
				afford, "upgrade_hero",
				{"cost": cost, "blocked": "" if afford else "POOR"}, "gold")
		else:
			_add_label("Level maksimum tercapai.", COL_DIM)
	else:
		_add_label("Pilih hero Radiant untuk melihat status & upgrade.", COL_TEXT, 14)

	_add_label("Beli hero (%d/%d dimiliki, termasuk yang respawn):" % [
		GameManager.owned_heroes().size(), GameManager.max_heroes_owned], COL_TEXT, 13)
	var unlocked = SaveManager.data.get("unlocked_heroes", [])
	if not (unlocked is Array):
		unlocked = []
	var grid := GridContainer.new()
	grid.columns = _pair_columns()
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 4)
	_body.add_child(grid)
	var roster_full := GameManager.owned_heroes().size() >= GameManager.max_heroes_owned
	for ht in unlocked:
		var htype := str(ht)
		var d: Dictionary = HeroDB.get_hero(htype)
		if d.is_empty():
			continue
		var cost := int(d.get("cost", 400))
		var can := GameManager.can_buy_hero(htype)
		var blocked := ""
		if GameManager.owns_hero(htype):
			blocked = "OWNED"
		elif roster_full:
			blocked = "FULL"
		elif GameManager.gold < cost:
			blocked = "POOR"
		elif not can:
			blocked = "LOCKED"
		var b := _make_button("%s (%s) — %d g" % [
				str(d.get("name", htype)), str(d.get("role", "-")), cost],
			"%s\nHP %d · DMG %d · RANGE %d · %s" % [str(d.get("description", "")),
				int(d.get("hp", 0)), int(d.get("damage", 0)), int(d.get("range", 0)),
				str(d.get("dmg_type", "PHYSICAL"))],
			_buy_hero.bind(htype), can, "buy_hero_" + htype,
			{"cost": cost, "blocked": blocked}, "gold")
		if blocked == "OWNED":
			b.text += " · DIMILIKI"
		elif blocked == "FULL":
			b.text += " · MAX"
		b.custom_minimum_size = Vector2(_row_width(_pair_columns()), 30)
		grid.add_child(b)
	_add_label("Hero lain (%d total di heroes.json) terbuka lewat progres level — "
		% HeroDB.get_all_types().size()
		+ "lihat SaveManager.unlocked_heroes.", COL_DIM, 11)


func _buy_hero(hero_type: String) -> void:
	# ui_buy 1.0 + hero_spawn (dibunyikan GameManager.try_buy_hero,
	# paritas _core.py:2637-2638 yang memanggil keduanya berurutan)
	_run(func(): GameManager.try_buy_hero(hero_type), "ui_buy")


# ── TAB NEXUS ─────────────────────────────────────────────

func _build_nexus_tab() -> void:
	var nx = GameManager.blue_nexus
	if nx == null or not is_instance_valid(nx) or bool(nx.get("is_dead")):
		_add_label("Radiant Nexus sudah hancur.", Color(1, 0.5, 0.5), 14)
		return
	_add_label("Radiant Nexus — %s Lv.%d / %d" % [
		HudLayout.castle_name(int(nx.get("level"))), int(nx.get("level")),
		TowerDB.nexus_max_level()], COL_GOLD, 15)
	_add_label("HP %d/%d · Shield %d/%d · DMG %d · RNG %d · skala minion %.2fx" % [
		int(nx.get("hp")), int(nx.get("max_hp")), int(nx.get("shield")),
		int(nx.get("shield_max")), int(nx.get("damage")), int(nx.get("attack_range")),
		float(nx.get("minion_scale"))], COL_DIM, 11)
	if nx.can_upgrade():
		var cost: int = nx.upgrade_cost()
		var nxt: Dictionary = TowerDB.nexus_stats(int(nx.get("level")) + 1)
		var afford := GameManager.gold >= cost
		_add_button("Upgrade Nexus ke Lv.%d — %d gold" % [int(nx.get("level")) + 1, cost],
			"HP %d · DMG %d · RNG %d · shield ratio HP naik" % [
				int(nxt.get("hp", 0)), int(nxt.get("damage", 0)), int(nxt.get("range", 0))],
			# ui_upgrade 0.5 — paritas try_upgrade_nexus _core.py:2668
			func(): _run(func(): GameManager.try_upgrade_nexus(), "ui_upgrade", 0.5),
			afford, "upgrade_nexus",
			{"cost": cost, "blocked": "" if afford else "POOR"}, "gold")
	else:
		_add_label("Nexus sudah level maksimum.", COL_DIM)
	if bool(nx.get("shield_active")) and bool(nx.get("free_shield_active")):
		_add_label("Castle Shield GRATIS aktif (sampai wave 10) — damage tersisa "
			+ "dikurangi %.0f%%." % (float(nx.get("shield_damage_reduction")) * 100.0),
			Color(0.6, 0.85, 1.0), 11)
	if nx.can_buy_shield():
		var cost: int = nx.shield_cost()
		var afford := GameManager.gold >= cost
		_add_button("Beli Castle Shield — %d gold" % cost,
			"Shield permanen: menyerap damage 1:1, sisanya dimitigasi %.0f%%."
			% (float(nx.get("shield_damage_reduction")) * 100.0),
			# ui_upgrade 0.5 — paritas try_activate_castle_shield _core.py:2652
			func(): _run(func(): GameManager.try_buy_nexus_shield(), "ui_upgrade", 0.5),
			afford, "nexus_shield",
			{"cost": cost, "blocked": "" if afford else "POOR"}, "cyan")
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
## Semua aksi toko lewat sini, jadi umpan balik suara cukup dipasang SATU kali.
##
## `action` = Callable GameManager.try_*() yang mengembalikan bool (true =
## berhasil). Berhasil -> `sfx`; gagal (gold kurang / syarat tidak terpenuhi) ->
## "ui_error" 0.4 — persis pola pygame yang memanggil
## SoundManager().play('ui_error') di tiap cabang gagal lalu
## play('ui_buy'/'ui_upgrade'/'ui_sell') di jalur sukses
## (_core.py:2605-2670, 8207-8246).
##
## Tidak ada tulis file di sini: volume dibaca AudioManager dari
## SaveManager.data["settings"] yang sudah di-memory, jadi slider SETTINGS
## langsung berlaku tanpa I/O per klik.
func _run(action: Callable, sfx: String = "ui_buy", volume_mult: float = 1.0) -> void:
	if get_tree().paused:
		return # SkillBar/ShopPanel PROCESS_MODE_ALWAYS -> kunci aksi saat pause
	var ok := true
	if action.is_valid():
		var result = action.call()
		if result is bool:
			ok = result
	if ok:
		AudioManager.play_sfx(sfx, volume_mult)
	else:
		AudioManager.play_sfx("ui_error", 0.4)
	_update_gold_label()
	_rebuild_body()


## Jumlah kolom grid item: 3 di modal besar, 1 di popup panel kanan sempit.
func _grid_columns() -> int:
	if _panel != null and _panel.size.x > 0.0 and _panel.size.x < 420.0:
		return 1
	return ITEM_COLUMNS


## 2 kolom di modal, 1 kolom di popup panel kanan.
func _pair_columns() -> int:
	return 1 if _grid_columns() == 1 else 2


## Lebar minimum tombol baris supaya isi TIDAK PERNAH melebar keluar panel
## (penyebab tombol terpotong / tidak bisa diklik di popup panel kanan).
func _row_width(columns: int) -> float:
	var w := 690.0
	if _panel != null and _panel.size.x > 0.0:
		w = _panel.size.x
	var inner := maxf(80.0, w - 40.0)
	return maxf(80.0, (inner - 8.0 * float(maxi(1, columns) - 1))
		/ float(maxi(1, columns)))


func _add_label(text_val: String, col: Color = COL_TEXT, font_size: int = 12) -> Label:
	var l := Label.new()
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	UiTheme.style_label(l, text_val,
		UiTheme.body_semibold() if font_size >= 13 else UiTheme.body_medium(),
		font_size, col)
	_body.add_child(l)
	return l


func _add_button(label: String, tooltip: String, cb: Callable, enabled: bool,
		ui_key: String = "", ui_data: Dictionary = {},
		kind: String = "neutral") -> Button:
	var b := _make_button(label, tooltip, cb, enabled, ui_key, ui_data,
		kind)
	b.custom_minimum_size = Vector2(0, 32)
	_body.add_child(b)
	return b


func _make_button(label: String, tooltip: String, cb: Callable, enabled: bool,
		ui_key: String = "", ui_data: Dictionary = {},
		kind: String = "neutral") -> Button:
	var b := Button.new()
	b.text = label
	b.tooltip_text = tooltip
	b.disabled = not enabled
	# ui_key/ui_data = identitas stabil tombol untuk audit closed-world
	# UiHudParityTest (daftar tertutup di HudLayout.shop_ui_keys()).
	if ui_key != "":
		b.set_meta("ui_key", ui_key)
	if not ui_data.is_empty():
		b.set_meta("ui_data", ui_data)
	b.focus_mode = Control.FOCUS_NONE
	UiTheme.apply_row_button(b, "locked" if not enabled else kind, 12,
		true)
	if enabled and cb.is_valid():
		b.pressed.connect(cb)
	return b
