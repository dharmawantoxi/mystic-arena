extends Control
## Runtime player Hero Shop. The panel owns no combat state: it renders the
## permanently purchased catalog and emits a source hero_type to the fixed-tick
## PrototypeSession, where the actual debit/spawn transaction is revalidated.

signal hero_requested(hero_type: String)

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const HERO_ROSTER = preload("res://scripts/data/hero_roster.gd").DEFINITIONS
const STARTERS: Array[String] = ["thorne", "grimjaw", "vex", "sylara", "kaizen", "zephyr"]

var world: Object
var is_open := false
var tab := "starter"
var command_pending := false
var _signature := ""
var _title: Label
var _gold: Label
var _roster: Label
var _starter_tab: Button
var _boss_tab: Button
var _grid: GridContainer
var _empty: Label


func bind(battle: Object) -> void:
	world = battle


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build()
	hide()


func set_open(value: bool) -> void:
	is_open = value and world != null
	visible = is_open
	_signature = ""
	if is_open:
		refresh()


func toggle_open() -> void:
	set_open(not is_open)


func _input(event: InputEvent) -> void:
	if not is_open:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode in [KEY_H, KEY_ESCAPE]:
			set_open(false)
			get_viewport().set_input_as_handled()
	elif (
		event is InputEventMouseButton
		and event.pressed
		and event.button_index == MOUSE_BUTTON_RIGHT
	):
		# Source right-click closes the in-match Hero Shop.
		set_open(false)
		get_viewport().set_input_as_handled()


func refresh() -> void:
	if world == null or not is_open:
		return
	var roster: Array = world.player_roster()
	var owned_ids: Array[String] = []
	for hero in roster:
		owned_ids.append(String(hero.definition.id))
	var signature := (
		"%s|%d|%s|%s|%s|%s"
		% [
			tab,
			world.economy.gold[world.BLUE],
			str(world.purchased_heroes),
			str(owned_ids),
			str(command_pending),
			str(world.is_running()),
		]
	)
	if signature == _signature:
		return
	_signature = signature
	_gold.text = "MATCH GOLD  %d G" % world.economy.gold[world.BLUE]
	_roster.text = "%d / %d HERO" % [roster.size(), world.MAX_HEROES_OWNED]
	_starter_tab.disabled = tab == "starter"
	_boss_tab.disabled = tab == "boss"
	_rebuild_cards(roster, owned_ids)


func _build() -> void:
	var dim := ColorRect.new()
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.01, 0.02, 0.03, 0.88)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(center)

	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(1040, 610)
	center.add_child(card)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	card.add_child(column)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 18)
	column.add_child(header)
	_title = Label.new()
	_title.text = "HERO SHOP"
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UI_THEME.title(_title, 30)
	header.add_child(_title)
	_gold = Label.new()
	UI_THEME.title(_gold, 19)
	header.add_child(_gold)
	_roster = Label.new()
	header.add_child(_roster)
	var close := Button.new()
	close.text = "Tutup  [H]"
	close.custom_minimum_size = Vector2(130, 42)
	close.pressed.connect(func() -> void: set_open(false))
	header.add_child(close)

	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 10)
	column.add_child(tabs)
	_starter_tab = Button.new()
	_starter_tab.text = "STARTER"
	_starter_tab.custom_minimum_size = Vector2(170, 40)
	_starter_tab.pressed.connect(func() -> void: _select_tab("starter"))
	tabs.add_child(_starter_tab)
	_boss_tab = Button.new()
	_boss_tab.text = "BOSS HEROES"
	_boss_tab.custom_minimum_size = Vector2(190, 40)
	_boss_tab.pressed.connect(func() -> void: _select_tab("boss"))
	tabs.add_child(_boss_tab)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(1000, 450)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(body)
	_empty = Label.new()
	_empty.text = "Belum ada boss hero yang dibuka."
	_empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty.custom_minimum_size = Vector2(980, 70)
	body.add_child(_empty)
	_grid = GridContainer.new()
	_grid.columns = 2
	_grid.add_theme_constant_override("h_separation", 12)
	_grid.add_theme_constant_override("v_separation", 10)
	_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(_grid)

	var hint := Label.new()
	hint.text = "Summon memakai gold pertandingan; hero mati tetap ACTIVE dan tetap memakai slot."
	UI_THEME.muted(hint)
	column.add_child(hint)


func _select_tab(value: String) -> void:
	tab = value
	_signature = ""
	refresh()


func _rebuild_cards(roster: Array, owned_ids: Array[String]) -> void:
	for child in _grid.get_children():
		_grid.remove_child(child)
		child.queue_free()
	var ids := _visible_ids()
	_empty.visible = ids.is_empty()
	_grid.visible = not ids.is_empty()
	for hero_type in ids:
		var definition = HERO_ROSTER[hero_type]
		var button := Button.new()
		button.custom_minimum_size = Vector2(485, 92)
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		var status := "%d G" % int(definition.cost)
		var disabled := command_pending or not world.is_running()
		if hero_type in owned_ids:
			status = "ACTIVE"
			disabled = true
		elif roster.size() >= world.MAX_HEROES_OWNED:
			status = "MAX"
			disabled = true
		elif world.economy.gold[world.BLUE] < int(definition.cost):
			disabled = true
		button.text = (
			"%s — %s\n%s  ·  HP %d  ·  DMG %d  ·  RNG %d  ·  %s"
			% [
				definition.display_name,
				definition.title,
				definition.role,
				definition.max_hp,
				definition.damage,
				int(definition.attack_range_px),
				status,
			]
		)
		button.tooltip_text = hero_type
		button.disabled = disabled
		button.pressed.connect(_request.bind(hero_type))
		_grid.add_child(button)


func _visible_ids() -> Array[String]:
	var result: Array[String] = []
	if tab == "starter":
		for hero_type in STARTERS:
			if hero_type in world.purchased_heroes and HERO_ROSTER.has(hero_type):
				result.append(hero_type)
		return result
	for hero_type in HERO_ROSTER:
		if hero_type not in world.purchased_heroes:
			continue
		if HERO_ROSTER[hero_type].is_boss_hero:
			result.append(hero_type)
	return result


func _request(hero_type: String) -> void:
	if command_pending:
		return
	hero_requested.emit(hero_type)
	_signature = ""
