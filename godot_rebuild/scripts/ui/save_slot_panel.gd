extends Control
## Request-only three-slot chooser. Save mutation remains in MainMenu/SaveSlotStore.

signal slot_requested(slot: int)
signal delete_requested(slot: int)

const Slots = preload("res://scripts/match/save_slot_store.gd")

var current_slot := 1
var pending_delete := -1
var _infos: Array[Dictionary] = []
var _slot_labels: Array[Label] = []
var _slot_buttons: Array[Button] = []
var _delete_buttons: Array[Button] = []
var _confirm: PanelContainer
var _confirm_label: Label
var _confirm_yes: Button
var _confirm_no: Button


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	_build()


func open_with_slots(infos: Array[Dictionary], selected_slot: int) -> void:
	_replace_infos(infos)
	current_slot = selected_slot
	pending_delete = -1
	_refresh()
	visible = true
	if valid_slot_button(selected_slot):
		_slot_buttons[selected_slot - 1].grab_focus()


func set_open(is_open: bool) -> void:
	visible = is_open
	if not is_open:
		pending_delete = -1
		if _confirm != null:
			_confirm.visible = false


func valid_slot_button(slot: int) -> bool:
	return Slots.valid_slot(slot) and _slot_buttons.size() == Slots.SLOT_COUNT


func refresh_slots(infos: Array[Dictionary], selected_slot: int) -> void:
	_replace_infos(infos)
	current_slot = selected_slot
	pending_delete = -1
	_refresh()


func _replace_infos(infos: Array[Dictionary]) -> void:
	_infos.clear()
	for info in infos:
		_infos.append(info.duplicate(true))
	while _infos.size() < Slots.SLOT_COUNT:
		_infos.append({})


func _build() -> void:
	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.015, 0.025, 0.035, 0.96)
	add_child(shade)

	var card := PanelContainer.new()
	card.set_anchors_preset(Control.PRESET_CENTER)
	card.position = Vector2(-570, -285)
	card.size = Vector2(1140, 570)
	add_child(card)
	var margin := MarginContainer.new()
	for side in ["margin_left", "margin_top", "margin_right", "margin_bottom"]:
		margin.add_theme_constant_override(side, 24)
	card.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	margin.add_child(column)

	var title := Label.new()
	title.text = "SELECT SAVE GAME"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 32)
	column.add_child(title)
	var hint := Label.new()
	hint.text = "Choose one isolated progression slot. Corrupt data must be deleted explicitly."
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(hint)

	var row := HBoxContainer.new()
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation", 14)
	column.add_child(row)
	for index in range(Slots.SLOT_COUNT):
		_build_slot_card(row, index + 1)

	_confirm = PanelContainer.new()
	_confirm.visible = false
	column.add_child(_confirm)
	var confirm_row := HBoxContainer.new()
	confirm_row.alignment = BoxContainer.ALIGNMENT_CENTER
	confirm_row.add_theme_constant_override("separation", 12)
	_confirm.add_child(confirm_row)
	_confirm_label = Label.new()
	confirm_row.add_child(_confirm_label)
	_confirm_yes = Button.new()
	_confirm_yes.text = "DELETE"
	_confirm_yes.custom_minimum_size = Vector2(120, 44)
	_confirm_yes.pressed.connect(_confirm_delete)
	confirm_row.add_child(_confirm_yes)
	_confirm_no = Button.new()
	_confirm_no.text = "CANCEL"
	_confirm_no.custom_minimum_size = Vector2(120, 44)
	_confirm_no.pressed.connect(_cancel_delete)
	confirm_row.add_child(_confirm_no)

	var close := Button.new()
	close.text = "BACK"
	close.custom_minimum_size = Vector2(160, 46)
	close.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	close.pressed.connect(set_open.bind(false))
	column.add_child(close)


func _build_slot_card(row: HBoxContainer, slot: int) -> void:
	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(350, 340)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(card)
	var margin := MarginContainer.new()
	for side in ["margin_left", "margin_top", "margin_right", "margin_bottom"]:
		margin.add_theme_constant_override(side, 16)
	card.add_child(margin)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	margin.add_child(column)
	var heading := Label.new()
	heading.text = "SAVE GAME %d" % slot
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	heading.add_theme_font_size_override("font_size", 22)
	column.add_child(heading)
	var info := Label.new()
	info.size_flags_vertical = Control.SIZE_EXPAND_FILL
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	column.add_child(info)
	_slot_labels.append(info)
	var select := Button.new()
	select.custom_minimum_size = Vector2(0, 52)
	select.pressed.connect(_request_slot.bind(slot))
	column.add_child(select)
	_slot_buttons.append(select)
	var remove := Button.new()
	remove.text = "DELETE SAVE"
	remove.custom_minimum_size = Vector2(0, 44)
	remove.pressed.connect(_ask_delete.bind(slot))
	column.add_child(remove)
	_delete_buttons.append(remove)


func _refresh() -> void:
	if _slot_labels.size() != Slots.SLOT_COUNT:
		return
	for index in range(Slots.SLOT_COUNT):
		var slot := index + 1
		var info: Dictionary = _infos[index]
		var corrupt := bool(info.get("corrupt", false))
		var empty := info.is_empty()
		if corrupt:
			_slot_labels[index].text = "CORRUPT SAVE\n\nDelete this slot explicitly\nbefore starting again."
			_slot_buttons[index].text = "UNAVAILABLE"
			_slot_buttons[index].disabled = true
			_delete_buttons[index].disabled = false
		elif empty:
			_slot_labels[index].text = "NEW GAME\n\nNo progression saved"
			_slot_buttons[index].text = "USE SLOT %d" % slot
			_slot_buttons[index].disabled = false
			_delete_buttons[index].disabled = true
		else:
			_slot_labels[index].text = (
				"Highest Level  %d\nHero Gold  %d\nHeroes  %d\nPlaytime  %s\nLast played  %s"
				% [
					int(info.get("highest_level", 0)),
					int(info.get("meta_gold", 0)),
					(info.get("purchased_heroes", []) as Array).size(),
					Slots.format_playtime(int(info.get("playtime_seconds", 0))),
					Slots.format_last_played(float(info.get("slot_last_played", 0.0))),
				]
			)
			_slot_buttons[index].text = "CONTINUE" if slot == current_slot else "SELECT"
			_slot_buttons[index].disabled = false
			_delete_buttons[index].disabled = false
	_confirm.visible = pending_delete >= 0


func _request_slot(slot: int) -> void:
	if not valid_slot_button(slot) or _slot_buttons[slot - 1].disabled:
		return
	slot_requested.emit(slot)


func _ask_delete(slot: int) -> void:
	if not Slots.valid_slot(slot) or _delete_buttons[slot - 1].disabled:
		return
	pending_delete = slot
	_confirm_label.text = "Delete SAVE GAME %d permanently?" % slot
	_confirm.visible = true
	_confirm_no.grab_focus()


func _confirm_delete() -> void:
	if not Slots.valid_slot(pending_delete):
		return
	var slot := pending_delete
	pending_delete = -1
	_confirm.visible = false
	delete_requested.emit(slot)


func _cancel_delete() -> void:
	pending_delete = -1
	_confirm.visible = false
