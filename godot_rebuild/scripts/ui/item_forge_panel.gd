extends Control
## Pygame-mobile ITEM FORGE presentation port. Geometry, copy, icons, colours,
## card states and detail content are sourced from hero_items.py; all actions
## still route through item_shop_ui.gd / forge.gd, so this Control owns no game
## state or purchase rules.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const PopupAnimation = preload("res://scripts/ui/popup_animation.gd")
const PRESENTATION := "res://data/ui/item_shop_presentation.json"
const ICONS := "res://assets/art/items/"
const ARENA_SIZE := Vector2(1280, 720)
const PANEL_RECT := Rect2(90, 0, 1100, 720)
const DETAIL_RECT := Rect2(200, 60, 880, 600)
const CARD_SIZE := Vector2(250, 200)
const CARD_GAP := Vector2(12, 14)
const SHOP_TEXT := {
	"title": "ITEM FORGE",
	"close": "Tutup",
	"buy": "BUY",
	"buy_for": "BUY FOR:",
	"dead": "mati",
	"queued": "dipesan",
	"delivery_after_respawn": "dikirim setelah respawn",
	"no_hero": "Belum ada hero",
	"no_hero_banner": "Belum ada hero hidup. Panggil hero untuk membeli item.",
	"inventory_full": "Slot item penuh",
	"magic_only_denied": "Hanya hero magic",
	"item_dropped": "Item dijatuhkan",
	"forge_purchase": "Terbeli",
	"forge_queued": "Dipesan (menunggu respawn)",
	"detail_hint": "Ketuk kartu item untuk info lengkap",
	"description": "DESKRIPSI LENGKAP",
	"stats": "STAT & EFEK",
	"flavor": "RIWAYAT / FLAVOR",
	"close_hint": "Ketuk di luar panel atau X untuk menutup",
	"inventory": "INVENTORY",
	"inventory_hint": "Ketuk item untuk info · klik kanan untuk menjatuhkan",
	"select_hero": "Pilih hero penerima item di atas",
}
const DETAIL_SECTIONS := [
	"stats", "passive", "on_attack", "multishot", "bash", "block", "active", "aura"
]

var world: Object = null
var popup_animation := PopupAnimation.new()
var _was_open := false
var _chrome: Control
var _dim: ColorRect
var _card: PanelContainer
var _gold: Label
var _chips: HBoxContainer
var _tabs: HBoxContainer
var _grid: GridContainer
var _slots: HBoxContainer
var _inventory_label: Label
var _notice: Label
var _detail_scrim: ColorRect
var _detail: PanelContainer
var _detail_body: VBoxContainer
var _detail_item := ""
var _render_key := ""
var _presentation_cache: Dictionary = {}


func _init() -> void:
	popup_animation.hide()
	popup_animation.progress = 0.0


func bind(battle: Object) -> void:
	world = battle
	set_process_input(true)


func _process(_delta: float) -> void:
	if _was_open or not is_equal_approx(popup_animation.progress, popup_animation.target):
		popup_animation.update()


func popup_animation_state() -> Dictionary:
	return {
		"is_open": _was_open,
		"progress": popup_animation.progress,
		"target": popup_animation.target,
		"scale": popup_animation.get_scale(),
		"offset_y": popup_animation.get_offset_y(),
	}


func shop() -> Object:
	return null if world == null else world.item_shop


func forge() -> Object:
	return null if world == null else world.forge


func set_open(is_open: bool) -> void:
	if shop() == null:
		return
	shop().is_open = is_open
	refresh()


func toggle_open() -> void:
	if shop() == null:
		return
	set_open(not shop().is_open)


func press(button_id: String, button: int = 1) -> bool:
	if shop() == null:
		return false
	var handled := bool(shop().handle_click(world, forge(), button_id, button))
	if is_inside_tree():
		notify_redraw.call_deferred()
	else:
		notify_redraw()
	return handled


func notify_redraw() -> void:
	refresh()


func status_text(status: String) -> String:
	return String(SHOP_TEXT.get(status, status))


func refresh() -> void:
	var shop_ui: Object = shop()
	if shop_ui == null:
		if _was_open:
			_was_open = false
			popup_animation.hide()
		visible = false
		return
	var now_open := bool(shop_ui.is_open)
	if now_open and not _was_open:
		popup_animation.show()
	elif not now_open and _was_open:
		popup_animation.hide()
	_was_open = now_open
	visible = now_open
	if not visible:
		_render_key = ""
		return
	if _chrome == null:
		_build_chrome()
	var next_render_key := _render_state_key(shop_ui)
	if next_render_key == _render_key:
		return
	_render_key = next_render_key
	_clear(_chips)
	_clear(_tabs)
	_clear(_grid)
	_clear(_slots)
	_build_hero_chips(shop_ui)
	_build_page_tabs(shop_ui)
	_build_cards(shop_ui)
	_build_slots(shop_ui)
	_gold.text = "◉ GOLD  " + _format_gold(forge().player_gold(world))
	_notice.text = shop_ui.notice_text()
	_refresh_detail(shop_ui)


func _input(event: InputEvent) -> void:
	# Native/root-delivered input follows the same modal boundaries as pygame.
	if visible and event is InputEventMouseButton:
		var mouse := event as InputEventMouseButton
		if mouse.pressed and mouse.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			var shop_ui: Object = shop()
			if shop_ui != null and bool(shop_ui.is_open):
				var point := mouse.position
				if Rect2(Vector2.ZERO, ARENA_SIZE).has_point(point):
					if String(shop_ui.inspect_item) != "":
						if not DETAIL_RECT.has_point(point):
							shop_ui.inspect_item = ""
							refresh()
							get_viewport().set_input_as_handled()
					elif not PANEL_RECT.has_point(point):
						if mouse.button_index == MOUSE_BUTTON_LEFT:
							shop_ui.click_outside_panel()
						else:
							shop_ui.is_open = false
						refresh()
						get_viewport().set_input_as_handled()


func _on_background_input(event: InputEvent) -> void:
	if not event is InputEventMouseButton:
		return
	var mouse := event as InputEventMouseButton
	if not mouse.pressed or mouse.button_index not in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
		return
	var shop_ui: Object = shop()
	if shop_ui == null or not bool(shop_ui.is_open):
		return
	var point := get_global_mouse_position()
	if String(shop_ui.inspect_item) != "":
		if DETAIL_RECT.has_point(point):
			get_viewport().set_input_as_handled()
			return
		shop_ui.inspect_item = ""
		refresh()
		get_viewport().set_input_as_handled()
		return
	if mouse.button_index == MOUSE_BUTTON_LEFT and PANEL_RECT.has_point(point):
		get_viewport().set_input_as_handled()
		return
	if mouse.button_index == MOUSE_BUTTON_RIGHT:
		shop_ui.is_open = false
	else:
		shop_ui.click_outside_panel()
	refresh()
	get_viewport().set_input_as_handled()


func _build_chrome() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dim = ColorRect.new()
	_dim.name = "ItemForgeArenaDimmer"
	_dim.color = Color(0.0, 0.0, 0.0, 215.0 / 255.0)
	_dim.position = Vector2.ZERO
	_dim.size = ARENA_SIZE
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_dim.gui_input.connect(_on_background_input)
	add_child(_dim)

	_card = PanelContainer.new()
	_card.name = "ItemForgePanel"
	_card.position = PANEL_RECT.position
	_card.size = PANEL_RECT.size
	_card.custom_minimum_size = PANEL_RECT.size
	_card.mouse_filter = Control.MOUSE_FILTER_STOP
	_card.add_theme_stylebox_override(
		"panel", _panel_style(Color8(22, 26, 44), UI_THEME.GOLD, 3, 14)
	)
	_card.gui_input.connect(_on_background_input)
	add_child(_card)
	_chrome = Control.new()
	_chrome.name = "ItemForgeChrome"
	_chrome.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.add_child(_chrome)

	_gold = _label("ItemForgeGold", "", 20, UI_THEME.GOLD_TEXT, true)
	_gold.position = Vector2(22, 16)
	_gold.size = Vector2(250, 32)
	_chrome.add_child(_gold)
	var title := _label("ItemForgeTitle", String(SHOP_TEXT.title), 46, UI_THEME.GOLD_MID, true)
	UI_THEME.title(title, 46)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.position = Vector2(300, 5)
	title.size = Vector2(500, 56)
	_chrome.add_child(title)
	var hint := _label("ItemForgeHint", String(SHOP_TEXT.detail_hint), 14, UI_THEME.FAINT)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hint.position = Vector2(750, 24)
	hint.size = Vector2(276, 24)
	_chrome.add_child(hint)
	_notice = _label("ItemForgeNotice", "", 14, UI_THEME.CYAN)
	_notice.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_notice.position = Vector2(680, 48)
	_notice.size = Vector2(346, 20)
	_chrome.add_child(_notice)
	var close := Button.new()
	close.name = "ItemForgeClose"
	close.text = "X"
	close.custom_minimum_size = Vector2(44, 44)
	close.position = Vector2(1044, 8)
	close.add_theme_font_size_override("font_size", 26)
	close.add_theme_stylebox_override(
		"normal", _panel_style(Color8(170, 48, 48), Color.WHITE, 2, 22)
	)
	close.add_theme_stylebox_override(
		"hover", _panel_style(Color8(220, 70, 70), Color.WHITE, 2, 22)
	)
	close.add_theme_stylebox_override(
		"pressed", _panel_style(Color8(130, 38, 38), Color.WHITE, 2, 22)
	)
	close.pressed.connect(func() -> void: press("itemshop_close"))
	_chrome.add_child(close)

	var buy_for := _label(
		"ItemForgeBuyFor", String(SHOP_TEXT.buy_for), 20, UI_THEME.GOLD_TEXT, true
	)
	buy_for.position = Vector2(22, 66)
	buy_for.size = Vector2(104, 28)
	_chrome.add_child(buy_for)
	_chips = HBoxContainer.new()
	_chips.name = "ItemForgeChips"
	_chips.position = Vector2(126, 57)
	_chips.size = Vector2(954, 42)
	_chips.add_theme_constant_override("separation", 8)
	_chrome.add_child(_chips)

	var summary_frame := Panel.new()
	summary_frame.name = "ItemForgeHeroSummaryFrame"
	summary_frame.position = Vector2(20, 105)
	summary_frame.size = Vector2(1060, 49)
	summary_frame.add_theme_stylebox_override(
		"panel", _panel_style(Color8(30, 36, 58), Color8(85, 125, 190), 2, 8)
	)
	_chrome.add_child(summary_frame)
	var summary := _label("ItemForgeHeroSummary", "", 16, UI_THEME.BODY)
	summary.position = Vector2(12, 1)
	summary.size = Vector2(1036, 46)
	summary.autowrap_mode = TextServer.AUTOWRAP_OFF
	summary_frame.add_child(summary)
	var no_hero := Panel.new()
	no_hero.name = "ItemForgeNoHeroBanner"
	no_hero.position = Vector2(20, 96)
	no_hero.size = Vector2(1060, 52)
	no_hero.add_theme_stylebox_override(
		"panel", _panel_style(Color8(40, 28, 28), Color8(200, 90, 90), 2, 8)
	)
	no_hero.visible = false
	_chrome.add_child(no_hero)
	var no_hero_text := _label(
		"ItemForgeNoHeroText", String(SHOP_TEXT.no_hero_banner), 24, Color8(255, 190, 190), true
	)
	no_hero_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	no_hero_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	no_hero_text.position = Vector2(8, 0)
	no_hero_text.size = Vector2(1044, 52)
	no_hero.add_child(no_hero_text)

	_tabs = HBoxContainer.new()
	_tabs.name = "ItemForgeTabs"
	_tabs.position = Vector2(55, 158)
	_tabs.size = Vector2(990, 40)
	_tabs.add_theme_constant_override("separation", 10)
	_chrome.add_child(_tabs)
	_grid = GridContainer.new()
	_grid.name = "ItemForgeGrid"
	_grid.columns = 4
	_grid.position = Vector2(32, 202)
	_grid.size = Vector2(1036, 414)
	_grid.custom_minimum_size = _grid.size
	_grid.add_theme_constant_override("h_separation", int(CARD_GAP.x))
	_grid.add_theme_constant_override("v_separation", int(CARD_GAP.y))
	_chrome.add_child(_grid)

	_inventory_label = _label("ItemForgeInventoryLabel", "", 17, UI_THEME.BODY, true)
	_inventory_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_inventory_label.position = Vector2(150, 628)
	_inventory_label.size = Vector2(800, 24)
	_chrome.add_child(_inventory_label)
	_slots = HBoxContainer.new()
	_slots.name = "ItemForgeSlots"
	_slots.position = Vector2(368, 654)
	_slots.size = Vector2(364, 54)
	_slots.add_theme_constant_override("separation", 8)
	_chrome.add_child(_slots)
	var no_slots_hint := _label(
		"ItemForgeSelectHeroHint", String(SHOP_TEXT.select_hero), 15, UI_THEME.FAINT
	)
	no_slots_hint.name = "ItemForgeSelectHeroHint"
	no_slots_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	no_slots_hint.position = Vector2(220, 660)
	no_slots_hint.size = Vector2(660, 28)
	no_slots_hint.visible = false
	_chrome.add_child(no_slots_hint)

	_detail_scrim = ColorRect.new()
	_detail_scrim.name = "ItemForgeDetailScrim"
	_detail_scrim.color = Color(0.0, 0.0, 0.0, 150.0 / 255.0)
	_detail_scrim.position = Vector2.ZERO
	_detail_scrim.size = ARENA_SIZE
	_detail_scrim.visible = false
	_detail_scrim.mouse_filter = Control.MOUSE_FILTER_STOP
	_detail_scrim.gui_input.connect(_on_background_input)
	add_child(_detail_scrim)
	_detail = PanelContainer.new()
	_detail.name = "ItemForgeDetail"
	_detail.position = DETAIL_RECT.position
	_detail.size = DETAIL_RECT.size
	_detail.custom_minimum_size = DETAIL_RECT.size
	_detail.visible = false
	_detail.mouse_filter = Control.MOUSE_FILTER_STOP
	var detail_style := _panel_style(Color8(24, 28, 48), UI_THEME.GOLD, 3, 14)
	detail_style.content_margin_left = 22
	detail_style.content_margin_right = 22
	detail_style.content_margin_top = 16
	detail_style.content_margin_bottom = 16
	_detail.add_theme_stylebox_override("panel", detail_style)
	_detail_body = VBoxContainer.new()
	_detail_body.name = "ItemForgeDetailBody"
	_detail_body.add_theme_constant_override("separation", 6)
	_detail.add_child(_detail_body)
	add_child(_detail)


func _label(
	node_name: String, text: String, font_size: int, color: Color, strong := false
) -> Label:
	var label := Label.new()
	label.name = node_name
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if strong:
		label.add_theme_font_override("font", preload("res://assets/fonts/Barlow-SemiBold.ttf"))
	return label


func _panel_style(fill: Color, edge: Color, width: int, radius: int) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = edge
	box.set_border_width_all(width)
	box.set_corner_radius_all(radius)
	box.content_margin_left = 0
	box.content_margin_right = 0
	box.content_margin_top = 0
	box.content_margin_bottom = 0
	return box


func _card_style(data: Dictionary, can_buy: bool, hovered: bool) -> StyleBoxFlat:
	var fill := Color8(34, 40, 68) if can_buy else Color8(26, 26, 38)
	var edge := _rgb(data.get("color", []), UI_THEME.GOLD) if can_buy else Color8(70, 70, 80)
	if hovered and can_buy:
		fill = fill.lightened(0.1)
	var style := _panel_style(fill, edge, 2, 8)
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style


func _clear(container: Node) -> void:
	for node in container.get_children():
		container.remove_child(node)
		node.free()


func _build_hero_chips(shop_ui: Object) -> void:
	var heroes: Array = forge()._player_heroes(world)
	var chip_data_list: Array = shop_ui.hero_chips(world, forge())
	if heroes.is_empty():
		_chips.add_child(
			_label("ItemForgeNoHeroes", String(SHOP_TEXT.no_hero), 18, Color8(255, 150, 150), true)
		)
	else:
		var gap := 8.0
		var chip_width := clampf(
			(954.0 - gap * float(heroes.size() - 1)) / float(heroes.size()), 110.0, 180.0
		)
		for index in range(heroes.size()):
			var hero: Object = heroes[index]
			var chip_data: Dictionary = chip_data_list[index]
			var button := Button.new()
			button.custom_minimum_size = Vector2(chip_width, 42)
			button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			button.toggle_mode = true
			button.button_pressed = bool(chip_data.is_target)
			button.text = "● %s\n%s" % [String(hero.settings().title), String(chip_data.label)]
			button.add_theme_font_size_override("font_size", 13)
			button.add_theme_color_override("font_color", Color8(240, 245, 255))
			var fill := Color8(48, 64, 100) if bool(chip_data.is_target) else Color8(26, 30, 48)
			var edge := Color8(100, 180, 255) if bool(chip_data.is_target) else Color8(70, 80, 110)
			button.add_theme_stylebox_override("normal", _panel_style(fill, edge, 2, 8))
			button.add_theme_stylebox_override(
				"hover", _panel_style(fill.lightened(0.12), edge, 2, 8)
			)
			var chip_id := "itemshop_hero_%d" % index
			button.pressed.connect(func() -> void: press(chip_id))
			_chips.add_child(button)
	var buyer: Object = forge()._shop_hero(world)
	var summary_frame := _chrome.get_node("ItemForgeHeroSummaryFrame") as Panel
	var summary := summary_frame.get_node("ItemForgeHeroSummary") as Label
	var no_hero := _chrome.get_node("ItemForgeNoHeroBanner") as Panel
	no_hero.visible = buyer == null
	summary_frame.visible = buyer != null
	if buyer != null:
		var settings = buyer.settings()
		var inv: Object = buyer.items
		var kind := "MELEE" if bool(buyer.is_melee) else "RANGED"
		if _is_magic(settings.role):
			kind += "  MAGIC"
		var line_one := "%s  Lv.%d" % [String(settings.title), int(buyer.level)]
		var line_two := (
			"%s   DMG %d→%d   HP %d   Armor %.0f   AS x%.2f   LS %d%%   CDR %d%%"
			% [
				kind,
				int(buyer.damage),
				int(buyer.damage + inv.get_bonus_damage()),
				int(buyer.max_hp),
				inv.get_armor(),
				inv.get_attack_speed_mult(),
				int(inv.get_lifesteal_pct() * 100.0),
				int(inv.get_cooldown_reduction() * 100.0),
			]
		)
		var range_bonus := float(inv.get_range_bonus())
		if range_bonus > 0.0:
			line_two += "   RNG +%d" % int(range_bonus)
		summary.text = line_one + "\n" + line_two
		if not bool(buyer.alive):
			var pending := buyer.pending_items.size()
			summary.text += "   · " + String(SHOP_TEXT.delivery_after_respawn)
			if pending > 0:
				summary.text += " (%d %s)" % [pending, String(SHOP_TEXT.queued)]
	_inventory_label.text = (
		String(SHOP_TEXT.inventory) + "   ·   " + String(SHOP_TEXT.inventory_hint)
	)
	_inventory_label.visible = buyer != null
	var hint := _chrome.get_node("ItemForgeSelectHeroHint") as Label
	hint.visible = buyer == null
	_slots.visible = buyer != null


func _build_page_tabs(shop_ui: Object) -> void:
	var labels: Array = shop_ui.page_tabs()
	var meta: Array = shop_ui.page_meta
	for index in range(labels.size()):
		var button := Button.new()
		button.text = String(labels[index])
		button.custom_minimum_size = Vector2(150, 36)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.toggle_mode = true
		button.button_pressed = index == int(shop_ui.page)
		var class_id := String(meta[index][0])
		var accent := Color8(255, 150, 80)
		if class_id == "magic":
			accent = Color8(200, 145, 255)
		elif class_id == "tank":
			accent = Color8(115, 225, 145)
		button.add_theme_color_override("font_color", accent)
		button.add_theme_stylebox_override(
			"normal", _panel_style(Color8(18, 22, 36), accent.darkened(0.45), 1, 7)
		)
		button.add_theme_stylebox_override(
			"pressed", _panel_style(Color8(48, 52, 70), accent, 2, 7)
		)
		button.add_theme_stylebox_override("hover", _panel_style(Color8(34, 40, 60), accent, 2, 7))
		var tab_id := "itemshop_page_%d" % index
		button.pressed.connect(func() -> void: press(tab_id))
		_tabs.add_child(button)


func _build_cards(shop_ui: Object) -> void:
	for card in shop_ui.item_cards(world, forge()):
		var item_id := String(card.id)
		var visual: Dictionary = _item_data(item_id)
		var cell := VBoxContainer.new()
		cell.custom_minimum_size = CARD_SIZE
		cell.add_theme_constant_override("separation", 6)
		var button := Button.new()
		button.name = "ItemForgeCard_%s" % item_id
		button.text = ""
		button.custom_minimum_size = Vector2(CARD_SIZE.x, 164)
		button.size_flags_vertical = Control.SIZE_EXPAND_FILL
		button.add_theme_stylebox_override("normal", _card_style(visual, bool(card.can_buy), false))
		button.add_theme_stylebox_override("hover", _card_style(visual, bool(card.can_buy), true))
		button.add_theme_stylebox_override("pressed", _card_style(visual, bool(card.can_buy), true))
		var content := VBoxContainer.new()
		content.name = "CardContent"
		content.position = Vector2(8, 6)
		content.size = Vector2(234, 150)
		content.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.add_theme_constant_override("separation", 2)
		var header := HBoxContainer.new()
		header.custom_minimum_size = Vector2(0, 58)
		header.add_theme_constant_override("separation", 8)
		header.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var icon := _icon(item_id, 56)
		header.add_child(icon)
		var info := VBoxContainer.new()
		info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		info.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var title := _label(
			"",
			String(visual.get("name", card.name)),
			19,
			_rgb(visual.get("glow", []), UI_THEME.GOLD_TEXT),
			true
		)
		title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		info.add_child(title)
		var badge := _label(
			"",
			(
				"%s · %s"
				% [
					String(visual.get("class_label", card.get("class", ""))),
					String(visual.get("category_label", ""))
				]
			),
			13,
			_rgb(visual.get("category_color", []), UI_THEME.CYAN),
			true
		)
		badge.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		info.add_child(badge)
		var price_color := UI_THEME.GOLD_TEXT if bool(card.can_buy) else Color8(200, 80, 80)
		var foot_text := "%dG" % int(card.cost)
		if int(card.owned_count) > 0:
			foot_text += "   Owned: %d" % int(card.owned_count)
		var price := _label("", foot_text, 16, price_color, true)
		info.add_child(price)
		header.add_child(info)
		content.add_child(header)
		var description := _label("", _description(visual), 14, UI_THEME.BODY)
		description.custom_minimum_size = Vector2(0, 58)
		description.size_flags_vertical = Control.SIZE_EXPAND_FILL
		description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		description.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		content.add_child(description)
		button.add_child(content)
		var card_id := "itemshop_card_%s" % item_id
		button.pressed.connect(func() -> void: press(card_id))
		cell.add_child(button)
		var buy := Button.new()
		buy.name = "ItemForgeBuy_%s" % item_id
		buy.text = String(SHOP_TEXT.buy) if bool(card.can_buy) else String(card.disabled_reason)
		buy.custom_minimum_size = Vector2(230, 26)
		buy.disabled = not bool(card.can_buy)
		buy.add_theme_font_size_override("font_size", 15)
		var buy_fill := Color8(54, 132, 86) if bool(card.can_buy) else Color8(58, 54, 62)
		var buy_edge := Color8(120, 225, 150) if bool(card.can_buy) else Color8(80, 78, 88)
		buy.add_theme_stylebox_override("normal", _panel_style(buy_fill, buy_edge, 1, 7))
		buy.add_theme_stylebox_override(
			"hover", _panel_style(buy_fill.lightened(0.12), buy_edge, 1, 7)
		)
		buy.add_theme_stylebox_override("disabled", _panel_style(buy_fill, buy_edge, 1, 7))
		var buy_id := "itemshop_buy_%s" % item_id
		buy.pressed.connect(func() -> void: press(buy_id))
		cell.add_child(buy)
		_grid.add_child(cell)


func _build_slots(_shop_ui: Object) -> void:
	var hero: Object = forge()._shop_hero(world)
	if hero == null:
		return
	for index in range(int(hero.items.max_slots())):
		var button := Button.new()
		button.custom_minimum_size = Vector2(54, 54)
		button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		var item_id: Variant = hero.items.slots[index]
		if item_id == null:
			button.text = ""
			button.add_theme_stylebox_override(
				"normal", _panel_style(Color8(14, 17, 30), Color8(66, 74, 104), 1, 6)
			)
			button.disabled = true
		else:
			var item := String(item_id)
			var visual := _item_data(item)
			var slot_icon := _icon(item, 46)
			slot_icon.position = Vector2(3, 3)
			button.add_child(slot_icon)
			button.add_theme_stylebox_override(
				"normal",
				_panel_style(Color8(14, 17, 30), _rgb(visual.get("color", []), UI_THEME.GOLD), 2, 6)
			)
			button.add_theme_stylebox_override(
				"hover",
				_panel_style(Color8(30, 34, 50), _rgb(visual.get("glow", []), UI_THEME.GOLD), 2, 6)
			)
		var slot_id := "itemshop_slot_%d" % index
		button.pressed.connect(func() -> void: press(slot_id))
		button.gui_input.connect(
			func(event: InputEvent) -> void:
				if event is InputEventMouseButton:
					var mouse := event as InputEventMouseButton
					if mouse.pressed and mouse.button_index == MOUSE_BUTTON_RIGHT:
						press(slot_id, 3)
						get_viewport().set_input_as_handled()
		)
		_slots.add_child(button)


func _refresh_detail(_shop_ui: Object) -> void:
	var item_id := String(shop().inspect_item)
	_detail_scrim.visible = item_id != ""
	_detail.visible = item_id != ""
	if item_id == "":
		_detail_item = ""
		return
	if item_id == _detail_item:
		return
	_detail_item = item_id
	_clear(_detail_body)
	_build_detail_content(item_id)


func _build_detail_content(item_id: String) -> void:
	var data := _item_data(item_id)
	var header := HBoxContainer.new()
	header.custom_minimum_size = Vector2(0, 82)
	header.add_theme_constant_override("separation", 14)
	var icon := _icon(item_id, 64)
	header.add_child(icon)
	var identity := VBoxContainer.new()
	identity.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var title := _label(
		"",
		String(data.get("name", item_id)),
		32,
		_rgb(data.get("glow", []), UI_THEME.GOLD_TEXT),
		true
	)
	identity.add_child(title)
	var class_category := _label(
		"",
		(
			"%s   ·   %s"
			% [String(data.get("class_label", "")), String(data.get("category_label", ""))]
		),
		15,
		_rgb(data.get("category_color", []), UI_THEME.CYAN),
		true
	)
	identity.add_child(class_category)
	var desc := _label("", _description(data), 19, UI_THEME.BODY)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var right := VBoxContainer.new()
	var price := _label("", "%d G" % int(data.get("cost", 0)), 26, UI_THEME.GOLD_TEXT, true)
	price.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(price)
	var hero: Object = forge()._shop_hero(world)
	if hero != null:
		var owned := hero.items.count(item_id)
		if owned > 0:
			var own_label := _label("", "Owned: %d" % owned, 17, Color8(150, 255, 170), true)
			own_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			right.add_child(own_label)
	var requirements := []
	if bool(data.get("melee_only", false)):
		requirements.append("MELEE ONLY")
	if bool(data.get("magic_only", false)):
		requirements.append("MAGIC ONLY")
	if not requirements.is_empty():
		var req := _label("", " · ".join(requirements), 14, Color8(255, 170, 90), true)
		req.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		right.add_child(req)
	header.add_child(identity)
	header.add_child(right)
	var close := Button.new()
	close.name = "ItemForgeDetailClose"
	close.text = "X"
	close.custom_minimum_size = Vector2(40, 40)
	close.add_theme_stylebox_override(
		"normal", _panel_style(Color8(170, 48, 48), Color.WHITE, 2, 20)
	)
	close.add_theme_stylebox_override(
		"hover", _panel_style(Color8(220, 70, 70), Color.WHITE, 2, 20)
	)
	close.pressed.connect(func() -> void: press("itemshop_detail_close"))
	header.add_child(close)
	_detail_body.add_child(header)
	var separator := HSeparator.new()
	_detail_body.add_child(separator)
	_detail_body.add_child(_label("", String(SHOP_TEXT.description), 15, UI_THEME.MUTED, true))
	desc.custom_minimum_size = Vector2(0, 48)
	_detail_body.add_child(desc)
	_detail_body.add_child(_section_label(String(SHOP_TEXT.stats), null, UI_THEME.MUTED))
	var columns := HBoxContainer.new()
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	columns.add_theme_constant_override("separation", 26)
	var left := VBoxContainer.new()
	var right_column := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var section_index := 0
	for section in DETAIL_SECTIONS:
		if not data.has(section):
			continue
		var target: VBoxContainer = left if section_index % 2 == 0 else right_column
		target.add_child(
			_section_label(
				String(section).to_upper(), data[section], _rgb(data.get("glow", []), UI_THEME.BODY)
			)
		)
		section_index += 1
	columns.add_child(left)
	columns.add_child(right_column)
	_detail_body.add_child(columns)
	if data.has("flavor") and String(data.flavor) != "":
		_detail_body.add_child(_section_label(String(SHOP_TEXT.flavor), data.flavor, UI_THEME.BODY))
	var close_hint := _label("", String(SHOP_TEXT.close_hint), 14, UI_THEME.FAINT)
	close_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_detail_body.add_child(close_hint)


func _section_label(title: String, value: Variant, color: Color) -> Control:
	if value == null:
		var heading := _label("", title, 15, color, true)
		return heading
	var row := VBoxContainer.new()
	row.add_theme_constant_override("separation", 2)
	var heading := _label("", title, 15, color, true)
	row.add_child(heading)
	var body := _label("", _format_value(value), 16, UI_THEME.BODY)
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	row.add_child(body)
	return row


func _icon(item_id: String, size: int) -> TextureRect:
	var icon := TextureRect.new()
	icon.name = "ItemIcon_%s" % item_id
	icon.custom_minimum_size = Vector2(size, size)
	icon.size = Vector2(size, size)
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var path := ICONS + item_id + ".png"
	if ResourceLoader.exists(path):
		icon.texture = load(path)
	return icon


func _render_state_key(shop_ui: Object) -> String:
	var state: Array = [
		int(shop_ui.page),
		forge().player_gold(world),
		String(shop_ui.inspect_item),
		String(shop_ui.notice_text()),
	]
	for hero in forge()._player_heroes(world):
		(
			state
			. append(
				[
					int(hero.id),
					bool(hero.alive),
					int(hero.level),
					int(hero.damage),
					int(hero.max_hp),
					hero.items.slots,
					hero.pending_items,
				]
			)
		)
	return str(state)


func _item_data(item_id: String) -> Dictionary:
	if _presentation_cache.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PRESENTATION))
		if parsed != null:
			_presentation_cache = parsed.get("items", {})
	return _presentation_cache.get(item_id, {})


func _description(data: Dictionary) -> String:
	var locale := OS.get_locale_language().to_lower()
	if locale.begins_with("en"):
		return String(data.get("desc_en", data.get("desc", "")))
	return String(data.get("desc", ""))


func _is_magic(role: String) -> bool:
	var lowered := role.to_lower()
	if lowered.contains("anti-mage"):
		return false
	for keyword in [
		"mage",
		"magic",
		"sorcer",
		"caster",
		"warlock",
		"witch",
		"sage",
		"prophet",
		"priestess",
		"pyro",
		"necro",
		"shaman",
		"summoner",
		"chorister",
		"farseer",
		"starweaver",
		"hex",
		"eldritch"
	]:
		if lowered.contains(keyword):
			return true
	return false


func _rgb(value: Variant, fallback: Color) -> Color:
	if value is Array and value.size() >= 3:
		return Color8(int(value[0]), int(value[1]), int(value[2]))
	return fallback


func _format_gold(amount: int) -> String:
	var digits := str(amount)
	var result := ""
	while digits.length() > 3:
		result = "," + digits.substr(digits.length() - 3, 3) + result
		digits = digits.substr(0, digits.length() - 3)
	return digits + result


func _format_value(value: Variant) -> String:
	if value is Dictionary:
		var parts: Array[String] = []
		for key in value:
			parts.append(
				"%s: %s" % [String(key).replace("_", " ").capitalize(), _format_value(value[key])]
			)
		return ", ".join(parts)
	if value is Array:
		var parts: Array[String] = []
		for entry in value:
			parts.append(_format_value(entry))
		return ", ".join(parts)
	return str(value)
