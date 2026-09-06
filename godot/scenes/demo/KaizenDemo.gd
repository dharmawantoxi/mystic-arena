# KaizenDemo.gd — showcase Kaizen Skeleton2D (menggantikan pygame _NS_kaizen demo)
# Siklus otomatis: idle 3s → walk 3s → attack loop 4s → repeat
# Jalankan: godot --path godot res://scenes/demo/KaizenDemo.tscn  atau F5 di editor

extends Node2D

@onready var kaizen: Node2D = $KaizenRoot/KaizenSkeleton
@onready var label_mode: Label = $CanvasLayer/VBox/ModeLabel
@onready var label_stats: Label = $CanvasLayer/VBox/StatsLabel
@onready var phase_bar: ProgressBar = $CanvasLayer/VBox/PhaseBar

var phase: float = 0.0
var cycle_time: float = 0.0
var mode: String = "idle"
var attack_progress: float = 0.0

# Info untuk overlay
var fps_label_timer: float = 0.0

func _ready():
	# Center Kaizen
	if kaizen:
		kaizen.position = Vector2(0, -12)
		print("[KaizenDemo] Skeleton loaded: %s bones=%d" % [kaizen.name, kaizen.get_child_count()])
	# Background grid agar gerak terlihat
	queue_redraw()

func _process(delta):
	cycle_time += delta
	phase += delta * 6.0

	# Siklus: 0-3 idle, 3-6 walk, 6-10 attack loop, then reset
	var ct = fmod(cycle_time, 10.0)
	if ct < 3.0:
		mode = "idle"
		attack_progress = 0.0
	elif ct < 6.0:
		mode = "walk"
		attack_progress = 0.0
	else:
		mode = "attack"
		# attack loop 0..1 tiap 0.65s  (mimic 32 frame @60fps)
		var local = ct - 6.0
		attack_progress = fmod(local * 1.55, 1.0)

	# Drive skeleton (pure, tanpa Hero AI)
	if kaizen and kaizen.has_method("drive"):
		var facing = 1
		# Flip tiap siklus biar kelihatan dua arah
		if int(cycle_time / 10.0) % 2 == 1:
			facing = -1
		var is_moving = (mode == "walk")
		kaizen.drive(phase, mode, attack_progress, facing, is_moving, "", delta)

	# UI update ~10fps
	fps_label_timer += delta
	if fps_label_timer > 0.1:
		fps_label_timer = 0.0
		if label_mode:
			var extra = ""
			if mode == "attack":
				extra = "  ap=%.2f  angle=%.1f°" % [attack_progress, kaizen.get("attack_progress") if kaizen else 0]
			label_mode.text = "KAIZEN // %s%s  —  phase %.1f  —  FPS %d" % [mode.to_upper(), extra, phase, Engine.get_frames_per_second()]
		if label_stats:
			label_stats.text = "Skeleton2D 25 bones  |  hamon shader  |  wind ribbon  |  scarf+ponytail inertia  |  bone_pos->Polygon2D (no PNG)"
		if phase_bar:
			phase_bar.value = attack_progress * 100 if mode == "attack" else fmod(phase, 1.0) * 100

	# Spawn fake damage number tiap attack peak
	if mode == "attack" and attack_progress > 0.52 and attack_progress < 0.56 and randf() < 0.12:
		_spawn_fake_damage()

func _spawn_fake_damage():
	var dn_scene = preload("res://scenes/fx/DamageNumber.tscn")
	if not ResourceLoader.exists("res://scenes/fx/DamageNumber.tscn"):
		return
	var dn = dn_scene.instantiate()
	dn.setup(str(randi_range(88, 142)), randf() < 0.18)
	var tip = kaizen.get_katana_tip_global() if kaizen and kaizen.has_method("get_katana_tip_global") else kaizen.global_position + Vector2(30, -20)
	dn.global_position = tip + Vector2(randf_range(-6,6), -8)
	get_tree().current_scene.add_child(dn)

func _draw():
	# Grid floor (menggantikan pygame.draw.rect floor)
	draw_rect(Rect2(Vector2(-600, 36), Vector2(1200, 80)), Color(0.12, 0.13, 0.16, 1))
	for x in range(-600, 601, 40):
		draw_line(Vector2(x, 36), Vector2(x, 116), Color(0.18, 0.19, 0.22, 1), 1.0)
	for y in range(36, 117, 20):
		draw_line(Vector2(-600, y), Vector2(600, y), Color(0.18, 0.19, 0.22, 0.45), 1.0)
	# Center shadow ellipse — Godot 4.3 tidak punya CanvasItem.draw_ellipse
	# (baru di 4.6 dengan signature Vector2,float,float,Color). Fallback pakai polygon.
	var _ellipse_center := Vector2(0, 38)
	var _ellipse_rx := 26.0
	var _ellipse_ry := 9.0
	var _ellipse_col := Color(0, 0, 0, 0.22)
	var _ellipse_pts := PackedVector2Array()
	for _i in 32:
		var _a := _i * TAU / 32.0
		_ellipse_pts.append(_ellipse_center + Vector2(cos(_a) * _ellipse_rx, sin(_a) * _ellipse_ry))
	draw_colored_polygon(_ellipse_pts, _ellipse_col)

func _input(event):
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE:
			# Force attack
			cycle_time = 6.1
		if event.keycode == KEY_F:
			# Flip facing handled otomatis tiap 10s, tapi bisa paksa
			if kaizen:
				kaizen.facing *= -1
		if event.keycode == KEY_R:
			cycle_time = 0.0
