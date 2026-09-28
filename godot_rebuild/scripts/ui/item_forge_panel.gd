extends Control
## ITEM FORGE panel view (layer 5f-3): the Control half of the source
## ItemShopUI drawing. It owns no gameplay state — `refresh()` renders the view
## data of `scripts/match/item_shop_ui.gd` (chips, tabs, cards, inventory slots,
## detail popup) and every press is routed straight back through
## `handle_click(world, forge, button_id, button)`, the same vocabulary the
## source hit-tests produce.
##
## The source localization (`tr()`) is not ported: SHOP_TEXT holds the rebuild's
## own Indonesian strings for the same keys, and `status_text()` maps the forge
## status keys of `forge.gd` onto them. Layout uses Godot containers instead of
## the source's fixed pygame rects (PANEL_W/H, ui_buttons), so no geometry
## constants are duplicated here.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const METADATA := "res://data/ai/item_catalog.json"
const SHOP_TEXT := {
	"title": "ITEM FORGE",
	"close": "Tutup",
	"buy": "BELI",
	"buy_for": "BELI UNTUK",
	"dead": "mati",
	"queued": "dipesan",
	"delivery_after_respawn": "dikirim setelah respawn",
	"no_hero": "Belum ada hero",
	"inventory_full": "Slot item penuh",
	"magic_only_denied": "Hanya hero magic",
	"item_dropped": "Item dijatuhkan",
	"forge_purchase": "Terbeli",
	"forge_queued": "Dipesan (menunggu respawn)",
}
# Section keys the detail popup prints for the inspected item.
const DETAIL_SECTIONS := ["stats", "passive", "on_attack", "multishot", "bash", "active", "aura"]

var world: Object = null
var _chrome: VBoxContainer
var _chips: HBoxContainer
var _tabs: HBoxContainer
var _grid: GridContainer
var _slots: HBoxContainer
var _notice: Label
var _detail: PanelContainer
var _detail_body: VBoxContainer
var _detail_item := ""


func bind(battle: Object) -> void:
	world = battle


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
	# The Control that hit-tests a real button calls this with the button id.
	if shop() == null:
		return false
	var handled := bool(shop().handle_click(world, forge(), button_id, button))
	if is_inside_tree():
		# Deferred: the redraw frees the very Button whose signal called us.
		notify_redraw.call_deferred()
	else:
		# Detached (headless test): no signal frame is running, redraw now.
		notify_redraw()
	return handled


func notify_redraw() -> void:
	# Source notifies through game.ui.add_notification; the panel prints them.
	refresh()


func status_text(status: String) -> String:
	return String(SHOP_TEXT.get(status, status))


func refresh() -> void:
	var shop_ui: Object = shop()
	if shop_ui == null:
		visible = false
		return
	visible = bool(shop_ui.is_open)
	if not visible:
		return
	if _chrome == null:
		_build_chrome()
	_clear(_chips)
	_clear(_tabs)
	_clear(_grid)
	_clear(_slots)
	_build_hero_chips(shop_ui)
	_build_page_tabs(shop_ui)
	_build_cards(shop_ui)
	_build_slots(shop_ui)
	_notice.text = shop_ui.notice_text()
	_refresh_detail(shop_ui)


func _build_chrome() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.color = Color(0.015, 0.03, 0.04, 0.72)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var card := PanelContainer.new()
	card.set_anchors_preset(Control.PRESET_CENTER)
	card.custom_minimum_size = Vector2(940, 620)
	card.position = Vector2(-470, -310)
	add_child(card)
	_chrome = VBoxContainer.new()
	_chrome.add_theme_constant_override("separation", 10)
	card.add_child(_chrome)
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	_chrome.add_child(header)
	var title := Label.new()
	title.text = String(SHOP_TEXT.title)
	UI_THEME.title(title, 26)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	_notice = Label.new()
	_notice.add_theme_font_size_override("font_size", 16)
	header.add_child(_notice)
	var close := Button.new()
	close.text = String(SHOP_TEXT.close)
	close.custom_minimum_size = Vector2(110, 44)
	close.pressed.connect(func() -> void: press("itemshop_close"))
	header.add_child(close)
	_chips = _row()
	_chips.name = "ItemForgeChips"
	_tabs = _row()
	_tabs.name = "ItemForgeTabs"
	_grid = GridContainer.new()
	_grid.name = "ItemForgeGrid"
	_grid.columns = 4
	_grid.add_theme_constant_override("h_separation", 10)
	_grid.add_theme_constant_override("v_separation", 10)
	_chrome.add_child(_grid)
	_slots = _row()
	_slots.name = "ItemForgeSlots"
	_detail = PanelContainer.new()
	_detail.name = "ItemForgeDetail"
	_detail.visible = false
	_detail_body = VBoxContainer.new()
	_detail.add_child(_detail_body)
	_chrome.add_child(_detail)


func _clear(container: Node) -> void:
	# Detach before freeing so the rebuilt rows are immediately countable and
	# no orphan node survives the frame (headless tests never pump one).
	for node in container.get_children():
		container.remove_child(node)
		node.free()


func _row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_chrome.add_child(row)
	return row


func _build_hero_chips(shop_ui: Object) -> void:
	for chip in shop_ui.hero_chips(world, forge()):
		var button := Button.new()
		button.text = "%s %d\n%s" % [String(SHOP_TEXT.buy_for), int(chip.index), String(chip.label)]
		button.custom_minimum_size = Vector2(210, 58)
		button.toggle_mode = true
		button.button_pressed = bool(chip.is_target)
		button.disabled = false
		var chip_id := "itemshop_hero_%d" % int(chip.index)
		button.pressed.connect(func() -> void: press(chip_id))
		_chips.add_child(button)


func _build_page_tabs(shop_ui: Object) -> void:
	var labels: Array = shop_ui.page_tabs()
	for index in range(labels.size()):
		var button := Button.new()
		button.text = String(labels[index])
		button.custom_minimum_size = Vector2(150, 40)
		button.toggle_mode = true
		button.button_pressed = index == int(shop_ui.page)
		var tab_id := "itemshop_page_%d" % index
		button.pressed.connect(func() -> void: press(tab_id))
		_tabs.add_child(button)


func _build_cards(shop_ui: Object) -> void:
	for card in shop_ui.item_cards(world, forge()):
		var button := Button.new()
		var tag := " (dimiliki)" if bool(card.owned) else ""
		button.text = "%s\n%d G%s" % [String(card.name), int(card.cost), tag]
		button.custom_minimum_size = Vector2(220, 92)
		button.disabled = not bool(card.affordable)
		var card_id := "itemshop_card_%s" % String(card.id)
		button.pressed.connect(func() -> void: press(card_id))
		var buy := Button.new()
		buy.text = "%s · %s" % [String(SHOP_TEXT.buy), String(card.name)]
		buy.custom_minimum_size = Vector2(96, 34)
		buy.disabled = not bool(card.affordable)
		var buy_id := "itemshop_buy_%s" % String(card.id)
		buy.pressed.connect(func() -> void: press(buy_id))
		var cell := VBoxContainer.new()
		cell.add_child(button)
		cell.add_child(buy)
		_grid.add_child(cell)


func _build_slots(_shop_ui: Object) -> void:
	# The slot row belongs to the current buyer (source: itemshop_target_hero,
	# falling back to the resolved target when that hero is gone).
	var hero: Object = forge()._shop_hero(world)
	if hero == null:
		return
	for index in range(int(hero.items.max_slots())):
		var button := Button.new()
		var item_id: Variant = hero.items.slots[index]
		button.text = "-" if item_id == null else String(item_id)
		button.custom_minimum_size = Vector2(150, 44)
		button.disabled = item_id == null
		var slot_id := "itemshop_slot_%d" % index
		button.pressed.connect(func() -> void: press(slot_id))
		# Right click (source button 3) drops the item: no refund.
		button.gui_input.connect(
			func(event: InputEvent) -> void:
				if event is InputEventMouseButton:
					var mouse := event as InputEventMouseButton
					if mouse.pressed and mouse.button_index == MOUSE_BUTTON_RIGHT:
						press(slot_id, 3)
		)
		_slots.add_child(button)


func _refresh_detail(_shop_ui: Object) -> void:
	var item_id := String(shop().inspect_item)
	_detail.visible = item_id != ""
	if not _detail.visible:
		_detail_item = ""
		return
	if item_id == _detail_item:
		return
	_detail_item = item_id
	_clear(_detail_body)
	var data: Dictionary = _item_data(item_id)
	var title := Label.new()
	title.text = "%s · %d G" % [String(data.get("name", item_id)), int(data.get("cost", 0))]
	UI_THEME.title(title, 20)
	_detail_body.add_child(title)
	for section in DETAIL_SECTIONS:
		if not data.has(section):
			continue
		_detail_body.add_child(_section_label(section, data[section]))
	var close := Button.new()
	close.text = String(SHOP_TEXT.close)
	close.custom_minimum_size = Vector2(120, 36)
	close.pressed.connect(func() -> void: press("itemshop_detail_close"))
	_detail_body.add_child(close)


func _section_label(section: String, value: Variant) -> Label:
	var label := Label.new()
	label.add_theme_font_size_override("font_size", 15)
	label.text = "%s: %s" % [section.to_upper(), str(value)]
	UI_THEME.muted(label)
	return label


func _item_data(item_id: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
	if parsed == null:
		return {}
	return (parsed as Dictionary).get("items", {}).get(item_id, {})
