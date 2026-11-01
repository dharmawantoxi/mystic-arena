class_name DebugView
extends PanelContainer

var mode := 0
var label: Label
var history := PackedFloat32Array()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	label = Ui.label("", 16, Ui.GOLD)
	add_child(label)
	position = Vector2(938, 20)
	custom_minimum_size = Vector2(320, 100)
	visible = false


func toggle() -> void:
	mode = (mode + 1) % 3
	visible = mode != 0


func refresh(fps: float, state: String, clock: FixedClock, game: GameplayPort) -> void:
	if mode == 0:
		return
	history.append(fps)
	if history.size() > 60:
		history.remove_at(0)
	label.text = (
		"FPS %.0f • %s\nSimulasi: %s\nTicks: %d • %s"
		% [
			fps,
			state,
			clock.status(),
			clock.total_steps,
			"combat" if game != null and game.combat_ready() else "integrasi"
		]
	)
	if mode == 2:
		var sum := 0.0
		for sample: float in history:
			sum += sample
		label.text += "\nRata-rata %.1f FPS • %d sampel" % [sum / history.size(), history.size()]
