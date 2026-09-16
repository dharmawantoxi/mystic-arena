# SylaraDemo.gd — showcase rig Sylara (Godot 4.x rebuild).
#
# Siklus otomatis memutar SELURUH set animasi + FX skill:
#   IDLE → WALK → RUN → ATTACK (ranged) → SWING (melee)
#   → Q (Focus Fire) → W (Windrun) → E (Shackle Shot) → R (Powershot)
#   → HURT → DEATH → VICTORY → ulang (flip arah tiap siklus).
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
	if sylara != null and sylara.has_signal("attack_impact"):
		sylara.attack_impact.connect(_on_attack_impact)
		sylara.skill_cast.connect(_on_skill_cast)


func _process(delta: float) -> void:
	phase += delta * 6.0
	cycle_t += delta
	_run_auto_cycle()
	_apply_manual(delta)
	_move_rig(delta)

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
		is_moving = true
	elif ct < 7.2:
		seg = "ATTACK"
		action = "attack"
		attack_progress = clampf((ct - 6.0) / 1.0, 0.0, 1.0)
	elif ct < 8.4:
		seg = "SWING"
		action = "attack"
		attack_progress = clampf((ct - 7.2) / 1.0, 0.0, 1.0)
	elif ct < 11.4:
		seg = "Q FOCUS FIRE"
		skill_key = "q"
	elif ct < 14.4:
		seg = "W WINDRUN"
		skill_key = "w"
		is_moving = true
	elif ct < 16.9:
		seg = "E SHACKLE"
		skill_key = "e"
	elif ct < 18.25:
		seg = "R POWERSHOT"
		skill_key = "r"
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


func _move_rig(delta: float) -> void:
	if is_moving and action == "idle":
		var speed := 100.0 if _last_seg == "WALK" else 180.0
		$SylaraRoot.position.x += speed * delta * facing
		# Wrap posisi.
		if abs($SylaraRoot.position.x) > 260.0:
			$SylaraRoot.position.x = -260.0 * sign($SylaraRoot.position.x)


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
				_manual_skill_t = 1.35
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
#  UI
# ══════════════════════════════════════════════════════════

func _update_labels() -> void:
	if label_mode != null:
		label_mode.text = "SYLARA // %s" % _last_seg
	if label_stats != null:
		label_stats.text = "SylaraRenderer _draw() layered | SylaraAnimator pose blending | SylaraSkillFX + VFXManager pool"
	if phase_bar != null:
		phase_bar.value = fmod(cycle_t, CYCLE_LEN) / CYCLE_LEN * 100.0


func _on_attack_impact() -> void:
	AudioManager.play_combat("hero_ranged", 0.85)
	if sylara != null and is_instance_valid(sylara):
		var spawn_pos: Vector2 = sylara.get_arrow_spawn_global()
		var target_pos := spawn_pos + Vector2(170.0 * facing, 0.0)
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
