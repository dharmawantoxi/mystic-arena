extends Control
## Main-menu permanent Hero Shop. This panel is request-only: Hero Gold and
## save state are mutated atomically by MainMenu through HeroUnlockStore.

signal unlock_requested(hero_type: String)

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const HeroShopCard = preload("res://scripts/ui/hero_shop_card.gd")
const PopupAnimation = preload("res://scripts/ui/popup_animation.gd")
const HeroUnlockStore = preload("res://scripts/match/hero_unlock_store.gd")

var state: Dictionary = {}
var is_open := false
var tab := "starter"
var notice := ""
var popup_animation := PopupAnimation.new()
var _signature := ""
var _gold: Label
var _bosses: Label
var _starter_tab: Button
var _mini_tab: Button
var _true_tab: Button
var _grid: GridContainer
var _empty: Label
var _notice: Label
var _close: Button


func _init() -> void:
	popup_animation.hide()
	popup_animation.progress = 0.0


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build()
	hide()


func _process(_delta: float) -> void:
	if is_open or not is_equal_approx(popup_animation.progress, popup_animation.target):
		popup_animation.update()


func open_with_state(profile: Dictionary) -> void:
	var was_open := is_open
	state = profile.duplicate(true)
	is_open = true
	visible = true
	if not was_open:
		popup_animation.show()
	notice = ""
	_signature = ""
	refresh()
	if is_inside_tree():
		_close.grab_focus()


func set_open(value: bool) -> void:
	var was_open := is_open
	is_open = value
	visible = value
	if is_open and not was_open:
		popup_animation.show()
	elif not is_open and was_open:
		popup_animation.hide()
	_signature = ""
	if value:
		refresh()


func popup_animation_state() -> Dictionary:
	return {
		"is_open": is_open,
		"progress": popup_animation.progress,
		"target": popup_animation.target,
		"scale": popup_animation.get_scale(),
		"offset_y": popup_animation.get_offset_y(),
	}


func apply_state(profile: Dictionary, message: String) -> void:
	state = profile.duplicate(true)
	notice = message
	_signature = ""
	refresh()


func show_error(error: String) -> void:
	notice = (
		{
			"hero": "Hero tidak ditemukan di katalog native.",
			"owned": "Hero itu sudah dimiliki.",
			"locked": "Kalahkan boss ini dahulu.",
			"gold": "Hero Gold tidak cukup.",
			"profile": "Data progres tidak valid.",
			"save": "Progres gagal disimpan; transaksi dibatalkan.",
		}
		. get(error, "Transaksi ditolak.")
	)
	_signature = ""
	refresh()


func refresh() -> void:
	if not is_open:
		return
	var purchased: Array = state.get("purchased_heroes", [])
	var defeated: Array = state.get("unlocked_bosses", [])
	var signature := (
		"%s|%d|%s|%s|%s"
		% [tab, int(state.get("meta_gold", 0)), str(purchased), str(defeated), notice]
	)
	if signature == _signature:
		return
	_signature = signature
	_gold.text = "HERO GOLD  %d G" % int(state.get("meta_gold", 0))
	_bosses.text = "BOSS DIKALAHKAN  %d" % defeated.size()
	_notice.text = notice
	_starter_tab.disabled = tab == "starter"
	_mini_tab.disabled = tab == "mini"
	_true_tab.disabled = tab == "true"
	_rebuild_cards(purchased, defeated)


func _build() -> void:
	var dim := ColorRect.new()
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.008, 0.012, 0.025, 0.96)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(center)

	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(1120, 650)
	center.add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	card.add_child(column)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 16)
	column.add_child(header)
	var title := Label.new()
	title.text = "HERO SHOP"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UI_THEME.title(title, 30)
	header.add_child(title)
	_gold = Label.new()
	UI_THEME.title(_gold, 18)
	header.add_child(_gold)
	_bosses = Label.new()
	header.add_child(_bosses)
	_close = Button.new()
	_close.text = "Kembali  [Esc]"
	_close.custom_minimum_size = Vector2(155, 42)
	_close.pressed.connect(func() -> void: set_open(false))
	header.add_child(_close)

	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 10)
	column.add_child(tabs)
	_starter_tab = _tab_button(tabs, "STARTER HEROES", "starter")
	_mini_tab = _tab_button(tabs, "MINI BOSSES", "mini")
	_true_tab = _tab_button(tabs, "TRUE BOSSES", "true")

	_notice = Label.new()
	_notice.custom_minimum_size = Vector2(0, 24)
	_notice.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UI_THEME.muted(_notice)
	column.add_child(_notice)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(1080, 470)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(body)
	_empty = Label.new()
	_empty.text = "Tidak ada hero native dalam kategori ini."
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty.custom_minimum_size = Vector2(1060, 70)
	body.add_child(_empty)
	_grid = GridContainer.new()
	_grid.columns = 2
	_grid.add_theme_constant_override("h_separation", 12)
	_grid.add_theme_constant_override("v_separation", 10)
	_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(_grid)

	var hint := Label.new()
	hint.text = ("Starter gratis; boss harus dikalahkan dahulu dan membutuhkan 4.500 Hero Gold.")
	UI_THEME.muted(hint)
	column.add_child(hint)


func _tab_button(parent: Control, label: String, value: String) -> Button:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(190, 40)
	button.pressed.connect(func() -> void: _select_tab(value))
	parent.add_child(button)
	return button


func _select_tab(value: String) -> void:
	tab = value
	notice = ""
	_signature = ""
	refresh()


func _rebuild_cards(purchased: Array, defeated: Array) -> void:
	for child in _grid.get_children():
		_grid.remove_child(child)
		child.queue_free()
	var ids := _visible_ids()
	_empty.visible = ids.is_empty()
	_grid.visible = not ids.is_empty()
	for hero_type in ids:
		var item := HeroUnlockStore.entry(hero_type)
		if item.is_empty():
			continue
		var definition = item.definition
		var owned: bool = hero_type in purchased
		var boss_ready: bool = not bool(item.is_boss_hero) or hero_type in defeated
		var cost := int(item.unlock_cost)
		var status := "FREE" if cost == 0 else "%d G" % cost
		var disabled := false
		if owned:
			status = "OWNED"
			disabled = true
		elif not boss_ready:
			status = "LOCKED · KALAHKAN %s" % String(definition.display_name).to_upper()
			disabled = true
		elif int(state.get("meta_gold", 0)) < cost:
			disabled = true
		var summary := (
			"%s — %s\n%s  ·  HP %d  ·  DMG %d  ·  %s"
			% [
				definition.display_name,
				definition.title,
				definition.role,
				definition.max_hp,
				definition.damage,
				status,
			]
		)
		var button := HeroShopCard.new()
		button.setup(hero_type, summary, disabled, 525.0, definition)
		button.pressed.connect(_request.bind(hero_type))
		_grid.add_child(button)


func _visible_ids() -> Array[String]:
	return HeroUnlockStore.ids_for_tab(tab)


func _request(hero_type: String) -> void:
	unlock_requested.emit(hero_type)


func _input(event: InputEvent) -> void:
	if not is_open:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_ESCAPE:
			set_open(false)
			get_viewport().set_input_as_handled()
	elif (
		event is InputEventMouseButton
		and event.pressed
		and event.button_index == MOUSE_BUTTON_RIGHT
	):
		set_open(false)
		get_viewport().set_input_as_handled()
