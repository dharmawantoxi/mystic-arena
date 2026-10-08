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
var _cloud_status: Label
var _cloud_sign_in: Button
var _cloud_upload: Button
var _cloud_download: Button
var _cloud_confirm: PanelContainer
var _cloud_confirm_label: Label
var _cloud_confirm_yes: Button
var _cloud_confirm_no: Button
var _cloud_pending_action := ""
var _cloud_pending_payload: Dictionary = {}
var _cloud_runtime: Node


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	_build()
	_cloud_runtime = get_tree().root.get_node_or_null("CloudSave")
	if _cloud_runtime != null and _cloud_runtime.has_signal("status_changed"):
		if not _cloud_runtime.is_connected("status_changed", _on_cloud_status_changed):
			_cloud_runtime.connect("status_changed", _on_cloud_status_changed)
	_update_cloud_controls()


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
		if _cloud_pending_action == "restore" and _cloud_runtime != null:
			_cloud_runtime.call("dismiss_restore_prompt")
		_cloud_pending_action = ""
		_cloud_pending_payload.clear()
		if _confirm != null:
			_confirm.visible = false
		if _cloud_confirm != null:
			_cloud_confirm.visible = false


func show_cloud_restore_prompt(payload: Dictionary, summary: Dictionary) -> void:
	_cloud_pending_action = "restore"
	_cloud_pending_payload = payload.duplicate(true)
	_cloud_confirm_label.text = (
		"Restore cloud progress? Level %d · Hero Gold %d · %d slot(s). Local slots are empty."
		% [
			int(summary.get("highest_level", 0)),
			int(summary.get("meta_gold", 0)),
			int(summary.get("slot_count", 0)),
		]
	)
	_cloud_confirm.visible = true
	visible = true
	_cloud_confirm_yes.grab_focus()


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
	card.position = Vector2(-570, -340)
	card.size = Vector2(1140, 680)
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

	_build_cloud_section(column)

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


func _build_cloud_section(column: VBoxContainer) -> void:
	var section := VBoxContainer.new()
	section.add_theme_constant_override("separation", 8)
	column.add_child(section)
	var heading := Label.new()
	heading.text = "GOOGLE PLAY GAMES CLOUD SAVE"
	heading.add_theme_font_size_override("font_size", 18)
	section.add_child(heading)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 10)
	section.add_child(actions)
	_cloud_status = Label.new()
	_cloud_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_cloud_status.text = "Cloud status is loading."
	actions.add_child(_cloud_status)
	_cloud_sign_in = Button.new()
	_cloud_sign_in.text = "SIGN IN"
	_cloud_sign_in.custom_minimum_size = Vector2(145, 44)
	_cloud_sign_in.pressed.connect(_request_cloud_sign_in)
	actions.add_child(_cloud_sign_in)
	_cloud_upload = Button.new()
	_cloud_upload.text = "UPLOAD"
	_cloud_upload.custom_minimum_size = Vector2(145, 44)
	_cloud_upload.pressed.connect(_ask_cloud_upload)
	actions.add_child(_cloud_upload)
	_cloud_download = Button.new()
	_cloud_download.text = "DOWNLOAD"
	_cloud_download.custom_minimum_size = Vector2(145, 44)
	_cloud_download.pressed.connect(_ask_cloud_download)
	actions.add_child(_cloud_download)

	_cloud_confirm = PanelContainer.new()
	_cloud_confirm.visible = false
	section.add_child(_cloud_confirm)
	var confirm_row := HBoxContainer.new()
	confirm_row.alignment = BoxContainer.ALIGNMENT_CENTER
	confirm_row.add_theme_constant_override("separation", 12)
	_cloud_confirm.add_child(confirm_row)
	_cloud_confirm_label = Label.new()
	_cloud_confirm_label.custom_minimum_size = Vector2(560, 0)
	_cloud_confirm_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	confirm_row.add_child(_cloud_confirm_label)
	_cloud_confirm_yes = Button.new()
	_cloud_confirm_yes.text = "CONFIRM"
	_cloud_confirm_yes.custom_minimum_size = Vector2(130, 44)
	_cloud_confirm_yes.pressed.connect(_confirm_cloud_action)
	confirm_row.add_child(_cloud_confirm_yes)
	_cloud_confirm_no = Button.new()
	_cloud_confirm_no.text = "CANCEL"
	_cloud_confirm_no.custom_minimum_size = Vector2(120, 44)
	_cloud_confirm_no.pressed.connect(_cancel_cloud_action)
	confirm_row.add_child(_cloud_confirm_no)


func _build_slot_card(row: HBoxContainer, slot: int) -> void:
	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(350, 310)
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
	_update_cloud_controls()


func _update_cloud_controls() -> void:
	if _cloud_status == null:
		return
	if _cloud_runtime == null or not is_instance_valid(_cloud_runtime):
		_cloud_status.text = "Cloud save tersedia di Android dengan Google Play Games."
		_cloud_sign_in.disabled = true
		_cloud_upload.disabled = true
		_cloud_download.disabled = true
		return
	var status: Dictionary = _cloud_runtime.call("get_status")
	_cloud_status.text = String(status.get("message", "Cloud status unavailable."))
	var usable := bool(status.get("available", false))
	var authenticated := bool(status.get("signed_in", false))
	var pending := bool(status.get("busy", false))
	_cloud_sign_in.text = "SIGNED IN" if authenticated else "SIGN IN"
	_cloud_sign_in.disabled = not usable or authenticated or pending
	_cloud_upload.disabled = not usable or not authenticated or pending
	_cloud_download.disabled = not usable or not authenticated or pending


func _on_cloud_status_changed(
	_ok: bool, message: String, _available: bool, _signed_in: bool, _busy: bool
) -> void:
	if _cloud_status != null:
		_cloud_status.text = message
	_update_cloud_controls()


func _request_cloud_sign_in() -> void:
	if _cloud_runtime == null:
		return
	_cloud_runtime.call("sign_in")


func _ask_cloud_upload() -> void:
	if _cloud_runtime == null:
		return
	_cloud_pending_action = "upload"
	_cloud_pending_payload.clear()
	_cloud_confirm_label.text = (
		"Replace the Google Play cloud copy with all saves " + "and settings on this device?"
	)
	_cloud_confirm.visible = true
	_cloud_confirm_yes.grab_focus()


func _ask_cloud_download() -> void:
	if _cloud_runtime == null:
		return
	var has_local_save := false
	for info in _infos:
		if not info.is_empty():
			has_local_save = true
			break
	if not has_local_save:
		_cloud_runtime.call("download_payload", true)
		return
	_cloud_pending_action = "download"
	_cloud_pending_payload.clear()
	_cloud_confirm_label.text = (
		"Replace all local save slots and the game-speed setting " + "with the cloud copy?"
	)
	_cloud_confirm.visible = true
	_cloud_confirm_yes.grab_focus()


func _confirm_cloud_action() -> void:
	var action := _cloud_pending_action
	var payload := _cloud_pending_payload.duplicate(true)
	_cloud_pending_action = ""
	_cloud_pending_payload.clear()
	_cloud_confirm.visible = false
	if _cloud_runtime == null:
		return
	if action == "upload":
		_cloud_runtime.call("upload_payload")
	elif action == "download":
		_cloud_runtime.call("download_payload", true)
	elif action == "restore":
		var result: Dictionary = _cloud_runtime.call("apply_payload", payload)
		if not bool(result.get("ok", false)):
			_cloud_status.text = String(result.get("error", "Cloud restore failed."))
		_refresh()


func _cancel_cloud_action() -> void:
	if _cloud_pending_action == "restore" and _cloud_runtime != null:
		_cloud_runtime.call("dismiss_restore_prompt")
	_cloud_pending_action = ""
	_cloud_pending_payload.clear()
	_cloud_confirm.visible = false


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
