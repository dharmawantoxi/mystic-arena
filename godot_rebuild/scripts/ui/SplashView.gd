class_name SplashView
extends Control

signal finished

const DURATION := 3.0
var elapsed := 0.0
var skipped := false
var done := false
var content: CenterContainer
var logo: TextureRect
var _particles: Array[Vector4] = []


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var random := RandomNumberGenerator.new()
	random.seed = 1947
	for index in range(46):
		_particles.append(
			Vector4(
				random.randf_range(0, 1280),
				random.randf_range(0, 720),
				random.randf_range(10, 35),
				random.randf_range(0, TAU)
			)
		)


func _ready() -> void:
	content = CenterContainer.new()
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(content)
	content.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column := VBoxContainer.new()
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_theme_constant_override("separation", 18)
	content.add_child(column)
	if ResourceLoader.exists("res://assets/logo.png"):
		logo = TextureRect.new()
		logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
		logo.texture = load("res://assets/logo.png")
		logo.custom_minimum_size = Vector2(260, 245)
		logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		column.add_child(logo)
	var title := Ui.label("MYSTIC ARENA", 54, Ui.TEXT, true)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(title)
	var subtitle := Ui.label("A MOBA TOWER DEFENSE ADVENTURE", 18, Ui.GOLD)
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(subtitle)
	var hint := Ui.label("Ketuk / tekan tombol untuk melewati", 17, Ui.MUTED)
	hint.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hint.offset_top = -52
	hint.offset_bottom = -20
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(hint)


func _draw() -> void:
	draw_rect(Rect2(0, 0, 1280, 720), Color("090914"))
	draw_rect(Rect2(0, 230, 1280, 270), Color("151021"))
	for particle: Vector4 in _particles:
		var twinkle := 0.4 + 0.3 * sin(elapsed * 2.5 + particle.w)
		draw_circle(Vector2(particle.x, particle.y), 1.7, Color(0.85, 0.66, 0.4, twinkle))


func skip() -> void:
	if not done:
		skipped = true


func advance(delta: float) -> void:
	if done:
		return
	elapsed += clampf(delta, 0.0, 0.05)
	for index in range(_particles.size()):
		_particles[index].y -= _particles[index].z * delta
		if _particles[index].y < -6:
			_particles[index].y = 726
	var alpha := minf(elapsed / 0.4, 1.0)
	if skipped:
		alpha *= maxf(0.0, 1.0 - elapsed / 0.25)
		done = elapsed >= 0.25
	else:
		alpha *= clampf((DURATION - elapsed) / 0.45, 0.0, 1.0)
		done = elapsed >= DURATION
	if content != null:
		content.modulate.a = alpha
	queue_redraw()
	if done:
		finished.emit()
