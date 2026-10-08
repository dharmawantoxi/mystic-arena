extends Control
## Live mix controls for the playback channels present in the native client.

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const AudioManagerScript = preload("res://scripts/audio/audio_manager.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const CHANNELS := [
	{"id": "master", "label": "Master Volume"},
	{"id": "sfx", "label": "SFX Volume"},
	{"id": "bgm", "label": "Music Volume"},
]

var _value_labels: Dictionary = {}
var _meters: Dictionary = {}
var _close_button: Button


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build()
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
	card.custom_minimum_size = Vector2(640, 440)
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
	title.text = "AUDIO SETTINGS"
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
		_build_volume_row(rows, String(entry.id), String(entry.label))


func _build_volume_row(parent: VBoxContainer, channel: String, label_text: String) -> void:
	var row := VBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	parent.add_child(row)

	var heading := HBoxContainer.new()
	heading.add_theme_constant_override("separation", 12)
	row.add_child(heading)
	var label := Label.new()
	label.text = label_text
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(label)
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


func _unhandled_key_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		set_open(false)
		get_viewport().set_input_as_handled()
