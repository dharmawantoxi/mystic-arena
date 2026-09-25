extends Control

signal menu_requested
signal restart_requested

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const Session = preload("res://scripts/simulation/combat_session.gd")
const View = preload("res://scenes/combat/minion_view.gd")

@onready var simulation: Session = $Simulation
@onready var arena: View = $Arena
@onready var pause_overlay: Control = %PauseOverlay


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UI_THEME.create_theme()
	arena.session = simulation
	UI_THEME.title(%ArenaTitle, 23)
	UI_THEME.title(%PauseTitle, 32)
	for definition in Session.DEFINITIONS:
		%MinionType.add_item(definition.display_name)
	%SpawnButton.pressed.connect(_request_wave)
	%PauseButton.pressed.connect(pause_match)
	%ResumeButton.pressed.connect(resume_match)
	%RestartButton.pressed.connect(func() -> void: restart_requested.emit())
	%MenuButton.pressed.connect(func() -> void: menu_requested.emit())
	%BackButton.pressed.connect(func() -> void: menu_requested.emit())
	%PauseButton.grab_focus()


func _process(_delta: float) -> void:
	var world := simulation.world
	%TickLabel.text = (
		"WAVE UJI %02d  ·  %.1f s  ·  %d unit"
		% [world.wave_count, world.tick_count / 60.0, world.units.size()]
	)
	%StatusLabel.text = (
		"Kill B/R: %d / %d   |   Tiba di ujung B/R: %d / %d"
		% [world.kills[0], world.kills[1], world.escaped[0], world.escaped[1]]
	)
	%SpawnButton.disabled = (
		get_tree().paused
		or simulation.pending_wave >= 0
		or world.units.size() + 6 > world.MAX_UNITS
	)
	var selected := world.get_unit(simulation.selected_id)
	if selected == null:
		%SelectionLabel.text = "Klik minion untuk inspeksi · 3 lane asli · stat nexus level 1"
	else:
		%SelectionLabel.text = (
			"%s #%d · %s · HP %.1f/%d · CD %d tick · Target #%d"
			% [
				selected.definition.display_name,
				selected.id,
				"BIRU" if selected.team == 0 else "MERAH",
				selected.hp,
				selected.definition.max_hp,
				selected.cooldown_ticks,
				selected.target_id
			]
		)


func _request_wave() -> void:
	simulation.request_wave(%MinionType.selected)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and not event.is_echo():
		if get_tree().paused:
			resume_match()
		else:
			pause_match()
		get_viewport().set_input_as_handled()
		return
	if get_tree().paused:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if event.device != InputEvent.DEVICE_ID_EMULATION:
			_select(event.position)
	elif event is InputEventScreenTouch and event.pressed:
		_select(event.position)


func _select(point: Vector2) -> void:
	var local_point := arena.get_global_transform_with_canvas().affine_inverse() * point
	simulation.selected_id = simulation.world.select_at(local_point)
	get_viewport().set_input_as_handled()


func pause_match() -> void:
	if get_tree().paused:
		return
	simulation.cancel_pending_input()
	pause_overlay.show()
	get_tree().paused = true
	%ResumeButton.grab_focus()


func resume_match() -> void:
	pause_overlay.hide()
	get_tree().paused = false
	%PauseButton.grab_focus()
