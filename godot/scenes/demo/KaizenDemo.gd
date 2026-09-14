# KaizenDemo.gd — showcase rig Kaizen v4 (Godot rebuild).
#
# Siklus otomatis memutar SELURUH set animasi + FX skill:
#   IDLE → WALK → RUN → ATTACK → Q (Steel Wind) → Q2 (Dash Strike)
#   → W (Wind Wall) → E (Whirlwind) → R (Tempest Fury)
#   → HURT → DEATH → VICTORY → ulang (flip arah tiap siklus).
#
# Kontrol keyboard:
#   SPACE serangan | 1/2/3/4 skill Q/W/E/R | tekan 1 dua kali = Dash Strike
#   H hurt | D death | V victory | F flip | R reset siklus
#
# Jalankan: godot --path godot res://scenes/demo/KaizenDemo.tscn
extends Node2D

const DMG_NUMBER_SCENE := "res://scenes/fx/DamageNumber.tscn"
const CYCLE_LEN := 21.6

@onready var kaizen: KaizenSkeleton = $KaizenRoot/KaizenSkeleton
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
var _last_q_press := -10.0

var _last_seg := ""
var _ui_timer := 0.0


func _ready() -> void:
	if kaizen != null and kaizen.has_signal("attack_impact"):
		kaizen.attack_impact.connect(_on_attack_impact)
		kaizen.skill_cast.connect(_on_skill_cast)


func _process(delta: float) -> void:
	phase += delta * 6.0
	cycle_t += delta
	_run_auto_cycle()
	_apply_manual(delta)
	_move_rig(delta)

	if kaizen != null and kaizen.has_method("drive"):
		var ap := attack_progress
		if _manual_attack > 0.0:
			ap = 1.0 - clampf(_manual_attack / 0.55, 0.0, 1.0)
		# Di arena flip dilakukan Hero/Visual; demo melakukannya sendiri.
		kaizen.scale.x = -1.0 if facing < 0 else 1.0
		kaizen.drive(phase, action, ap, facing, is_moving, skill_key, delta)

	_ui_timer += delta
	if _ui_timer > 0.1:
		_ui_timer = 0.0
		_update_labels()
	queue_redraw()


# ══════════════════════════════════════════════════════════
#  SIKLUS OTOMATIS (deteksi transisi segmen)
# ══════════════════════════════════════════════════════════

func _run_auto_cycle() -> void:
	# Manual override aktif → siklus menunggu.
	if _manual_skill != "" or _manual_attack > 0.0:
		return
	var ct := fmod(cycle_t, CYCLE_LEN)
	action = "idle"
	attack_progress = 0.0
	skill_key = ""
	is_moving = false

	var seg := "idle"
	if ct >= 2.5 and ct < 5.0:
		seg = "walk"
	elif ct >= 5.0 and ct < 6.4:
		seg = "run"
	elif ct >= 6.4 and ct < 8.0:
		seg = "attack"
	elif ct >= 8.0 and ct < 9.0:
		seg = "q"
	elif ct >= 9.0 and ct < 9.9:
		seg = "dash"
	elif ct >= 9.9 and ct < 12.9:
		seg = "w"
	elif ct >= 12.9 and ct < 14.1:
		seg = "e"
	elif ct >= 14.1 and ct < 15.9:
		seg = "r"
	elif ct >= 15.9 and ct < 16.7:
		seg = "hurt"
	elif ct >= 16.7 and ct < 18.3:
		seg = "death"
	elif ct >= 18.3:
		seg = "victory"

	match seg:
		"walk", "run":
			action = "walk"
			is_moving = true
		"attack":
			action = "attack"
			attack_progress = fmod((ct - 6.4) * 1.6, 1.0)
		"q", "w", "e", "r":
			skill_key = seg
		"dash":
			skill_key = "q"

	if seg != _last_seg:
		_on_segment_enter(seg)
		_last_seg = seg
	# Flip arah tiap siklus baru.
	var lap := int(cycle_t / CYCLE_LEN)
	facing = -1 if lap % 2 == 1 else 1


func _on_segment_enter(seg: String) -> void:
	if kaizen == null or not kaizen.has_method("play"):
		return
	match seg:
		"run":
			kaizen.play("run", 1.35)
		"dash":
			_teleport_dash()
		"hurt":
			kaizen.play("hurt", 0.35)
		"death":
			kaizen.play("death", 1.5)
		"victory":
			kaizen.play("victory", 2.2)


func _teleport_dash() -> void:
	# Lompatan posisi = sinyal dash untuk rig (paritas Q2 HeroSkillKit:
	# hero dipindah 70% jarak ke target pada frame cast).
	if kaizen == null:
		return
	var root_node: Node2D = kaizen.get_parent()
	if root_node == null:
		return
	root_node.position.x = clampf(
		root_node.position.x + 80.0 * facing, -240.0, 240.0)


func _move_rig(delta: float) -> void:
	if not is_moving or kaizen == null:
		return
	if skill_key != "" or action == "attack":
		return
	var root_node: Node2D = kaizen.get_parent()
	if root_node == null:
		return
	root_node.position.x = clampf(
		root_node.position.x + 90.0 * facing * delta, -240.0, 240.0)


# ══════════════════════════════════════════════════════════
#  MANUAL (keyboard)
# ══════════════════════════════════════════════════════════

func _apply_manual(delta: float) -> void:
	if _manual_attack > 0.0:
		_manual_attack -= delta
		action = "attack"
		is_moving = false
		skill_key = ""
		return
	if _manual_skill != "":
		_manual_skill_t -= delta
		if _manual_skill_t <= 0.0:
			_manual_skill = ""
			skill_key = ""
		else:
			skill_key = _manual_skill
			action = "idle"
			is_moving = false


func _trigger_skill(key: String) -> void:
	match key:
		"q":
			if cycle_t - _last_q_press < 2.5:
				_teleport_dash()
			_last_q_press = cycle_t
			_manual_skill = "q"
			_manual_skill_t = 1.0
		"w":
			_manual_skill = "w"
			_manual_skill_t = 1.5
		"e":
			_manual_skill = "e"
			_manual_skill_t = 1.0
		"r":
			_manual_skill = "r"
			_manual_skill_t = 1.7


func _input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed:
		return
	var k: InputEventKey = event
	match k.keycode:
		KEY_SPACE:
			_manual_attack = 0.55
		KEY_1:
			_trigger_skill("q")
		KEY_2:
			_trigger_skill("w")
		KEY_3:
			_trigger_skill("e")
		KEY_4:
			_trigger_skill("r")
		KEY_H:
			if kaizen != null and kaizen.has_method("play"):
				kaizen.play("hurt", 0.4)
		KEY_D:
			if kaizen != null and kaizen.has_method("play"):
				kaizen.play("death", 1.6)
		KEY_V:
			if kaizen != null and kaizen.has_method("play"):
				kaizen.play("victory", 2.4)
		KEY_F:
			facing = -facing
		KEY_R:
			cycle_t = 0.0
			_last_seg = ""
			_manual_skill = ""
			_manual_attack = 0.0
			skill_key = ""
			if kaizen != null:
				var root_node: Node2D = kaizen.get_parent()
				if root_node != null:
					root_node.position = Vector2.ZERO


# ══════════════════════════════════════════════════════════
#  SINYAL + UI + LATAR
# ══════════════════════════════════════════════════════════

func _on_attack_impact() -> void:
	if kaizen == null or not ResourceLoader.exists(DMG_NUMBER_SCENE):
		return
	if randf() < 0.55:
		var dn = load(DMG_NUMBER_SCENE).instantiate()
		dn.setup(str(randi_range(88, 142)), randf() < 0.18)
		var tip: Vector2 = kaizen.get_katana_tip_global() \
			if kaizen.has_method("get_katana_tip_global") else kaizen.global_position
		dn.global_position = tip + Vector2(randf_range(-6.0, 6.0), -8.0)
		get_tree().current_scene.add_child(dn)


func _on_skill_cast(key: String) -> void:
	if label_stats != null:
		label_stats.text = "skill_cast: %s — VFXManager pooled shapes, no particle spam" % key.to_upper()


func _update_labels() -> void:
	if label_mode != null:
		var shown := action.to_upper() if skill_key == "" \
			else "SKILL " + skill_key.to_upper()
		var extra := ""
		if skill_key == "" and action == "attack":
			extra = "  ap=%.2f" % attack_progress
		label_mode.text = "KAIZEN v4 // %s%s — phase %.1f — FPS %d" % [
			shown, extra, phase, Engine.get_frames_per_second()]
	if phase_bar != null:
		phase_bar.value = attack_progress * 100.0 if action == "attack" \
			else fmod(phase, 1.0) * 100.0


func _draw() -> void:
	# Latar panggung (digambar langsung, tanpa node tambahan).
	draw_rect(Rect2(-700, -360, 1400, 760), Color(0.07, 0.08, 0.11))
	draw_rect(Rect2(-700, 30, 1400, 400), Color(0.11, 0.12, 0.16))
	for x in range(-700, 701, 40):
		draw_line(Vector2(x, 30), Vector2(x, 130), Color(0.16, 0.17, 0.21), 1.0)
	for y in range(30, 131, 20):
		draw_line(Vector2(-700, y), Vector2(700, y),
			Color(0.16, 0.17, 0.21, 0.5), 1.0)
