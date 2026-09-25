extends Control
## UI/input adapter. No combat, economy, saves, or simulation updates here.

signal menu_requested
signal restart_requested

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const ArenaView = preload("res://scenes/match/arena_view.gd")
const Simulation = preload("res://scripts/simulation/sandbox_simulation.gd")

@onready var simulation: Simulation = $Simulation
@onready var arena: ArenaView = $Arena
@onready var pause_overlay: Control = %PauseOverlay


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UI_THEME.create_theme()
	arena.simulation = simulation
	UI_THEME.title(%ArenaTitle, 23)
	UI_THEME.title(%PauseTitle, 32)
	%PauseButton.pressed.connect(pause_match)
	%ResumeButton.pressed.connect(resume_match)
	%RestartButton.pressed.connect(_restart)
	%MenuButton.pressed.connect(_return_to_menu)
	%BackButton.pressed.connect(_return_to_menu)
	%PauseButton.grab_focus()


func _process(_delta: float) -> void:
	%TickLabel.text = (
		"SIMULASI  %06d tick  ·  %.1f s" % [simulation.tick_count, simulation.tick_count / 60.0]
	)
	%SelectionLabel.text = (
		"PENANDA DIPILIH · Klik kanan / ketuk arena untuk bergerak"
		if simulation.is_selected
		else "Klik / ketuk penanda hijau untuk memilih"
	)


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
	if event is InputEventMouseButton and event.pressed:
		# Touch has its own route; ignore synthetic mouse events on touch devices.
		if event.device == InputEvent.DEVICE_ID_EMULATION:
			return
		var point: Vector2 = (
			arena.get_global_transform_with_canvas().affine_inverse() * event.position
		)
		if event.button_index == MOUSE_BUTTON_LEFT:
			simulation.select_at(point)
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			simulation.command_move(point)
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenTouch and event.pressed:
		var point: Vector2 = (
			arena.get_global_transform_with_canvas().affine_inverse() * event.position
		)
		if simulation.probe_position.distance_to(point) <= 32.0:
			simulation.select_at(point)
		elif simulation.is_selected:
			simulation.command_move(point)
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


func _restart() -> void:
	get_tree().paused = false
	restart_requested.emit()


func _return_to_menu() -> void:
	get_tree().paused = false
	menu_requested.emit()
