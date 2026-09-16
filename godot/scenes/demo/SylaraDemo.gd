# SylaraDemo.gd — showcase rig Sylara (Godot native).
#
# Siklus otomatis memutar SELURUH set animasi + FX skill:
#   IDLE → WALK → RUN → ATTACK (loop tembak)
#   → Q FOCUS FIRE (tembak cepat) → W WINDRUN (sprint + trail)
#   → E SHACKLE SHOT (tether) → R POWERSHOT (channel + kerucut)
#   → HURT → DEATH → VICTORY → ulang (flip arah tiap siklus).
#
# Fitur khas Godot yang dipamerkan:
#   * BIDIK 360°: rig membidik node AimNode yang mengorbit — busur
#     berputar bebas mengikuti posisi target (dunia → lokal).
#   * Event-driven: panah "terbang" sebagai streak VFX di sinyal
#     bow_released; skill FX & feel dari sinyal skill_cast/skill_released.
#
# Kontrol keyboard:
#   SPACE serangan | 1/2/3/4 skill Q/W/E/R
#   H hurt | D death | V victory | F flip | R reset siklus
#
# Jalankan: godot --path godot res://scenes/demo/SylaraDemo.tscn
extends Node2D

const CYCLE_LEN := 24.0
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

@onready var sylara = $SylaraRoot/SylaraSkeleton
@onready var aim_node: Node2D = $SylaraRoot/AimNode
@onready var label_mode: Label = $CanvasLayer/VBox/ModeLabel
@onready var label_stats: Label = $CanvasLayer/VBox/StatsLabel
@onready var phase_bar: ProgressBar = $CanvasLayer/VBox/PhaseBar

var phase := 0.0
var cycle_t := 0.0
var facing := 1
var action := "idle"
var attack_progress := 0.0
var skill_key := ""
var is_moving := false

# ── Override manual (keyboard) ──
var _manual_attack := 0.0
var _manual_skill := ""
var _manual_skill_t := 0.0

var _last_seg := ""
var _ui_timer := 0.0


func _ready() -> void:
	# Pamerkan bidik 360°: rig membidik node orbit di sekelilingnya.
	if sylara != null:
		sylara.aim_override = aim_node
		if sylara.has_signal("bow_released"):
			sylara.bow_released.connect(_on_bow_released)
		if sylara.has_signal("skill_cast"):
			sylara.skill_cast.connect(_on_skill_cast)


func _process(delta: float) -> void:
	phase += delta * 6.0
	cycle_t += delta
	_run_auto_cycle()
	_apply_manual(delta)
	_move_rig(delta)
	_move_aim_node()

	if sylara != null and sylara.has_method("drive"):
		var ap := attack_progress
		if _manual_attack > 0.0:
			ap = 1.0 - clampf(_manual_attack / 0.55, 0.0, 1.0)
		sylara.scale.x = -1.0 if facing < 0 else 1.0
		sylara.drive(phase, action, ap, facing, is_moving, skill_key, delta)

	_ui_timer += delta
	if _ui_timer > 0.1:
		_ui_timer = 0.0
		_update_labels()
	queue_redraw()


# ══════════════════════════════════════════════════════════
#  SIKLUS OTOMATIS
# ══════════════════════════════════════════════════════════

func _run_auto_cycle() -> void:
	if _manual_skill != "" or _manual_attack > 0.0:
		return
	var ct := fmod(cycle_t, CYCLE_LEN)
	action = "idle"
	attack_progress = 0.0
	skill_key = ""
	is_moving = false

	var seg := ""
	if ct < 2.0:
		seg = "IDLE"
	elif ct < 4.0:
		seg = "WALK"
		is_moving = true
	elif ct < 6.0:
		seg = "RUN"
		action = "run"
		is_moving = true
	elif ct < 7.5:
		seg = "ATTACK"
		action = "attack"
		attack_progress = clampf((ct - 6.0) / 1.0, 0.0, 1.0)
	elif ct < 10.5:
		seg = "Q FOCUS FIRE"
		skill_key = "q"
		action = "attack"
		# Tembak cepat: ap berputar tiap 0.35 dtk (rate Focus Fire).
		attack_progress = fmod((ct - 7.5) / 0.35, 1.0)
	elif ct < 13.5:
		seg = "W WINDRUN"
		skill_key = "w"
		is_moving = true
	elif ct < 16.0:
		seg = "E SHACKLE"
		skill_key = "e"
	elif ct < 17.5:
		seg = "R POWERSHOT"
		skill_key = "r"
	elif ct < 18.25:
		seg = "R POWERSHOT"
		# release flourish — skill sudah lepas, pose burst berjalan.
	elif ct < 19.5:
		seg = "HURT"
		action = "hurt"
	elif ct < 21.5:
		seg = "DEATH"
		action = "death"
	elif ct < 24.0:
		seg = "VICTORY"
		action = "victory"

	if seg != _last_seg:
		_last_seg = seg
		if seg == "HURT" or seg == "DEATH" or seg == "VICTORY":
			if sylara != null and sylara.has_method("play"):
				var dur := 1.2 if seg == "DEATH" else (1.0 if seg == "VICTORY" else 0.4)
				sylara.play(seg.to_lower(), dur)


## Rig berjalan di tempat saat WALK/RUN/WINDRUN; posisi dibungkus.
func _move_rig(delta: float) -> void:
	if is_moving and (action == "idle" or skill_key == "w"):
		var speed := 100.0 if _last_seg == "WALK" else 180.0
		if skill_key == "w":
			speed = 220.0
		$SylaraRoot.position.x += speed * delta * facing
		# Wrap posisi.
		if absf($SylaraRoot.position.x) > 260.0:
			$SylaraRoot.position.x = -260.0 * signf($SylaraRoot.position.x)


## Titik bidik mengorbit — pamerkan aim 360° ruang dunia → lokal.
func _move_aim_node() -> void:
	if aim_node == null:
		return
	var a := phase * 0.16
	aim_node.position = Vector2(cos(a) * 150.0, -26.0 + sin(a * 0.7) * 46.0)


# ══════════════════════════════════════════════════════════
#  INPUT
# ══════════════════════════════════════════════════════════

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_SPACE:
				_manual_attack = 0.55
			KEY_1:
				_manual_skill = "q"
				_manual_skill_t = 3.0
			KEY_2:
				_manual_skill = "w"
				_manual_skill_t = 3.0
			KEY_3:
				_manual_skill = "e"
				_manual_skill_t = 2.5
			KEY_4:
				_manual_skill = "r"
				_manual_skill_t = 1.0
			KEY_H:
				if sylara != null and sylara.has_method("play"):
					sylara.play("hurt", 0.4)
			KEY_D:
				if sylara != null and sylara.has_method("play"):
					sylara.play("death", 1.5)
			KEY_V:
				if sylara != null and sylara.has_method("play"):
					sylara.play("victory", 2.0)
			KEY_F:
				facing = -facing
			KEY_R:
				cycle_t = 0.0
				_manual_attack = 0.0
				_manual_skill = ""


func _apply_manual(delta: float) -> void:
	if _manual_attack > 0.0:
		action = "attack"
		_manual_attack -= delta
		if _manual_attack <= 0.0:
			_manual_attack = 0.0
			action = "idle"
	if _manual_skill != "":
		skill_key = _manual_skill
		_manual_skill_t -= delta
		if _manual_skill_t <= 0.0:
			_manual_skill = ""
			skill_key = ""


# ══════════════════════════════════════════════════════════
#  UI + FX AKTOR SHOWCASE
# ══════════════════════════════════════════════════════════

func _update_labels() -> void:
	if label_mode != null:
		label_mode.text = "SYLARA // %s" % _last_seg
	if label_stats != null:
		label_stats.text = ("SylaraRenderer _draw() 360°-aim | "
			+ "SylaraAnimator pose loop | sinyal event-driven | VFXManager pool")
	if phase_bar != null:
		phase_bar.value = fmod(cycle_t, CYCLE_LEN) / CYCLE_LEN * 100.0


## Sinyal root: tali lepas → panah "melesat" (streak + flash + suara).
## Di arena ini dilakukan Hero.gd via hook spawn_attack_projectile.
func _on_bow_released() -> void:
	AudioManager.play_combat("hero_ranged", 0.85)
	if sylara == null or not is_instance_valid(sylara):
		return
	var spawn_pos: Vector2 = sylara.get_arrow_spawn_global()
	var target_pos := aim_node.global_position if aim_node != null \
		else spawn_pos + Vector2(170.0 * facing, 0.0)
	VFXManager.flash(spawn_pos, 7.0, Pal.WIND_BRIGHT, 0.0, 0.10)
	VFXManager.streak(spawn_pos, target_pos, Pal.WIND, 0.0, 0.18, 4.0)
	VFXManager.ring(target_pos, 12.0, Pal.WIND_LIGHT, 0.12, 0.22, 2.0)


func _on_skill_cast(key: String) -> void:
	AudioManager.play_sfx("hero_skill", 0.85)


func _draw() -> void:
	# Ground line.
	draw_line(Vector2(-400, 0), Vector2(400, 0),
		Color(0.15, 0.2, 0.12, 0.5), 1.0)
	# Grid subtle.
	for x in range(-400, 401, 50):
		draw_line(Vector2(x, -2), Vector2(x, 2),
			Color(0.12, 0.16, 0.10, 0.3), 1.0)
	# Marker titik bidik (crosshair di posisi GLOBAL AimNode — SylaraRoot
	# bergeser saat WALK/RUN/WINDRUN).
	if aim_node != null:
		var p: Vector2 = to_local(aim_node.global_position)
		var col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.6)
		draw_arc(p, 9.0, 0.0, TAU, 20, col, 1.2, true)
		draw_line(p + Vector2(-13.0, 0.0), p + Vector2(13.0, 0.0), col, 1.0)
		draw_line(p + Vector2(0.0, -13.0), p + Vector2(0.0, 13.0), col, 1.0)
		draw_circle(p, 1.6, col)
