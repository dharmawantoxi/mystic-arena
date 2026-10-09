extends Control
## Shared native settings panel for audio, render-frame, and language controls.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const AudioManagerScript = preload("res://scripts/audio/audio_manager.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const CHANNELS := [
	{"id": "master", "label_key": "set_volume_master"},
	{"id": "sfx", "label_key": "set_volume_sfx"},
	{"id": "bgm", "label_key": "set_volume_bgm"},
]

var _value_labels: Dictionary = {}
var _meters: Dictionary = {}
var _channel_labels: Dictionary = {}
var _close_button: Button
var _settings_title: Label
var _frame_limit_value: Label
var _language_label: Label
var _language_value: Label
var _frame_rate_runtime: Node
var _localization_runtime: Node


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build()
	_frame_rate_runtime = get_tree().root.get_node_or_null("FrameRateLimit")
	_localization_runtime = get_tree().root.get_node_or_null("Localization")
	if is_instance_valid(_localization_runtime):
		_localization_runtime.connect("language_changed", _refresh_localized_labels)
	_refresh_localized_labels()
	hide()


func open() -> void:
	visible = true
	refresh()
	_close_button.grab_focus()


func set_open(value: bool) -> void:
	visible = value
	if value:
		refresh()


func refresh() -> void:
	for entry in CHANNELS:
		var channel: String = entry.id
		var volume := clampf(AudioRuntime.get_volume(channel), 0.0, 1.0)
		var percent := roundi(volume * 100.0)
		var label: Label = _value_labels[channel]
		var meter: ProgressBar = _meters[channel]
		label.text = "%d%%" % percent
		meter.value = percent
	_refresh_localized_labels()
	_refresh_frame_limit()


func _build() -> void:
	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.008, 0.012, 0.025, 0.92)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(shade)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(center)

	var card := PanelContainer.new()
	card.custom_minimum_size = Vector2(640, 580)
	center.add_child(card)

	var margin := MarginContainer.new()
	for side in ["margin_left", "margin_top", "margin_right", "margin_bottom"]:
		margin.add_theme_constant_override(side, 28)
	card.add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 18)
	margin.add_child(column)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 16)
	column.add_child(header)
	var title := Label.new()
	title.name = "SettingsTitle"
	title.text = "SETTINGS"
	_settings_title = title
	UI_THEME.title(title, 30)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	_close_button = Button.new()
	_close_button.name = "CloseButton"
	_close_button.text = "Back"
	_close_button.custom_minimum_size = Vector2(130, 44)
	_close_button.pressed.connect(set_open.bind(false))
	header.add_child(_close_button)

	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 12)
	rows.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(rows)
	for entry in CHANNELS:
		_build_volume_row(rows, String(entry.id), String(entry.label_key))

	var graphics_title := Label.new()
	graphics_title.text = "GRAPHICS"
	UI_THEME.muted(graphics_title)
	column.add_child(graphics_title)
	var frame_rate_row := HBoxContainer.new()
	frame_rate_row.add_theme_constant_override("separation", 12)
	column.add_child(frame_rate_row)
	var frame_rate_label := Label.new()
	frame_rate_label.text = "FPS Limit"
	frame_rate_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	frame_rate_row.add_child(frame_rate_label)
	var previous := Button.new()
	previous.name = "FrameRatePrevious"
	previous.text = "‹"
	previous.custom_minimum_size = Vector2(52, 42)
	previous.pressed.connect(_cycle_frame_limit.bind(-1))
	frame_rate_row.add_child(previous)
	_frame_limit_value = Label.new()
	_frame_limit_value.name = "FrameRateValue"
	_frame_limit_value.custom_minimum_size = Vector2(120, 0)
	_frame_limit_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	frame_rate_row.add_child(_frame_limit_value)
	var next := Button.new()
	next.name = "FrameRateNext"
	next.text = "›"
	next.custom_minimum_size = Vector2(52, 42)
	next.pressed.connect(_cycle_frame_limit.bind(1))
	frame_rate_row.add_child(next)
	_build_language_row(column)


func _build_language_row(parent: VBoxContainer) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	parent.add_child(row)
	_language_label = Label.new()
	_language_label.name = "LanguageLabel"
	_language_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(_language_label)
	var previous := Button.new()
	previous.name = "LanguagePrevious"
	previous.text = "‹"
	previous.custom_minimum_size = Vector2(52, 42)
	previous.pressed.connect(_cycle_language.bind(-1))
	row.add_child(previous)
	_language_value = Label.new()
	_language_value.name = "LanguageValue"
	_language_value.custom_minimum_size = Vector2(160, 0)
	_language_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	row.add_child(_language_value)
	var next := Button.new()
	next.name = "LanguageNext"
	next.text = "›"
	next.custom_minimum_size = Vector2(52, 42)
	next.pressed.connect(_cycle_language.bind(1))
	row.add_child(next)


func _build_volume_row(parent: VBoxContainer, channel: String, label_key: String) -> void:
	var row := VBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	parent.add_child(row)

	var heading := HBoxContainer.new()
	heading.add_theme_constant_override("separation", 12)
	row.add_child(heading)
	var label := Label.new()
	label.name = _node_name(channel, "Label")
	label.text = label_key
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(label)
	_channel_labels[channel] = label
	var value := Label.new()
	value.name = _node_name(channel, "Value")
	value.custom_minimum_size = Vector2(64, 0)
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	heading.add_child(value)
	_value_labels[channel] = value

	var controls := HBoxContainer.new()
	controls.add_theme_constant_override("separation", 12)
	row.add_child(controls)
	var minus := Button.new()
	minus.name = _node_name(channel, "Minus")
	minus.text = "−"
	minus.custom_minimum_size = Vector2(48, 42)
	minus.pressed.connect(_adjust.bind(channel, -AudioManagerScript.VOLUME_STEP))
	controls.add_child(minus)

	var meter := ProgressBar.new()
	meter.name = _node_name(channel, "Meter")
	meter.min_value = 0.0
	meter.max_value = 100.0
	meter.show_percentage = false
	meter.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	meter.custom_minimum_size = Vector2(0, 18)
	controls.add_child(meter)
	_meters[channel] = meter

	var plus := Button.new()
	plus.name = _node_name(channel, "Plus")
	plus.text = "+"
	plus.custom_minimum_size = Vector2(48, 42)
	plus.pressed.connect(_adjust.bind(channel, AudioManagerScript.VOLUME_STEP))
	controls.add_child(plus)


func _node_name(channel: String, suffix: String) -> String:
	return "%s%s" % [channel.capitalize(), suffix]


func _adjust(channel: String, delta: float) -> void:
	if AudioRuntime.adjust_volume(channel, delta):
		refresh()


func _translate(key: String) -> String:
	if is_instance_valid(_localization_runtime):
		return String(_localization_runtime.call("translate", key))
	return key


func _refresh_localized_labels(_language: String = "") -> void:
	if _settings_title == null:
		return
	_settings_title.text = _translate("set_title")
	_close_button.text = _translate("menu_back")
	for entry in CHANNELS:
		var channel := String(entry.id)
		var label: Label = _channel_labels[channel]
		label.text = _translate(String(entry.label_key))
	if _language_label != null:
		_language_label.text = _translate("language")
	if _language_value != null:
		if is_instance_valid(_localization_runtime):
			_language_value.text = String(_localization_runtime.call("get_language_label"))
		else:
			_language_value.text = "Bahasa Indonesia"


func _cycle_language(direction: int) -> void:
	if is_instance_valid(_localization_runtime):
		_localization_runtime.call("cycle_language", direction)


func _refresh_frame_limit() -> void:
	if is_instance_valid(_frame_rate_runtime) and _frame_limit_value != null:
		_frame_limit_value.text = String(_frame_rate_runtime.call("limit_label"))


func _cycle_frame_limit(direction: int) -> void:
	if is_instance_valid(_frame_rate_runtime):
		_frame_rate_runtime.call("cycle_limit", direction)
		_refresh_frame_limit()


func _unhandled_key_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		set_open(false)
		get_viewport().set_input_as_handled()
