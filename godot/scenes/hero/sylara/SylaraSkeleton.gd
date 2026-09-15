# SylaraSkeleton.gd — root controller karakter Sylara (Godot 4.x rebuild).
#
# Arsitektur modular (satu script = satu tanggung jawab):
#   SylaraSkeleton.gd  (root: state, blending, drive() API, sinyal)
#   ├── SylaraAnimator.gd   (state → pose target)
#   ├── SylaraRenderer.gd   (pose → gambar _draw() berlapis)
#   └── SylaraSkillFX.gd    (skill key → urutan VFX pooled)
#
# Kontrak dengan Hero.gd (sama seperti KaizenSkeleton):
#   * drive(phase, action, attack_progress, facing, is_moving, skill, delta)
#     dipanggil Hero._drive_visual tiap physics frame.
#   * Digambar menghadap +x; Hero mem-flip Visual.scale.x — rig TIDAK
#     melakukan flip sendiri (menghindari double-flip).
#   * handles_skill_fx() = true → Hero melewatkan FX skill generik supaya
#     tidak dobel (NO VISUAL NOISE).
#
# Kontrak demo/showcase: play("hurt"/"death"/"victory"/"run", durasi)
# memaksa state sementara di luar drive() Hero.
class_name SylaraSkeleton
extends Node2D

const AnimatorScript = preload("res://scenes/hero/sylara/SylaraAnimator.gd")

signal attack_started
signal attack_impact
signal skill_cast(skill_key: String)

## Dipakai Hero.gd untuk memilih renderer; dipertahankan dari rig Kaizen.
const ATTACK_IMPACT_PROGRESS := 0.52

@onready var renderer: SylaraRenderer = $Renderer
@onready var skill_fx: SylaraSkillFX = $SkillFX

var animator = null
var pose_current = null

## State override dari play() (demo / showcase).
var _override_state := ""
var _override_t := 0.0
var _override_dur := 0.0

## Lacak skill aktif untuk skill_t (detik sejak cast).
var _skill_key := ""
var _skill_time := 0.0
var _attack_started_emitted := false
var _impact_emitted := false
## attack_progress frame sebelumnya: ap dihitung Hero dari attack_timer/
## cooldown, jadi kalau cooldown berubah mid-swing ap bisa MUNDUR dan
## pose melompat ke belakang = stutter. Dilacak agar monoton naik.
var _prev_ap := 0.0
var _prev_pos := Vector2.ZERO
var _hero = null
var _hero_hp := -1.0
var facing: int = 1
## Trail buffer — posisi bow tip global.
var _trail_buf: Array = []
const TRAIL_MAX := 10


func _ready() -> void:
	add_to_group("sylara_skeleton")
	animator = AnimatorScript.new()
	pose_current = animator.compute("idle", 0.0, 0.0, 0.0, {})
	_prev_pos = global_position
	skill_fx.resolve_hero()
	var n: Node = get_parent()
	if n != null:
		n = n.get_parent()
	if n != null and "hp" in n and "kit" in n:
		_hero = n
		_hero_hp = float(_hero.hp)


## API Hero.gd — dipanggil tiap physics frame.
func drive(p_phase: float, p_action: String, p_attack_progress: float,
		p_facing: int, p_moving: bool, p_skill: String,
		p_delta: float = 0.016) -> void:
	var delta := p_delta if p_delta > 0.0 else get_process_delta_time()
	facing = 1 if p_facing >= 0 else -1
	var phase := p_phase
	var ap := clampf(p_attack_progress, 0.0, 1.0)

	animator.tick(delta)
	_watch_hero()
	_track_skill(p_skill, delta)

	# ── State efektif: override (play) > skill > attack > swing > gerak > idle ──
	var state := _derive_state(p_action, p_moving, p_skill)
	var extra := {}
	if _override_state != "":
		_override_t += delta
		extra["t"] = clampf(_override_t / maxf(0.001, _override_dur), 0.0, 1.0)
		state = _override_state
		if _override_t >= _override_dur:
			_override_state = ""

	# ── attack_progress monoton naik dalam satu swing ──
	if state == "attack" or state == "swing":
		if ap < _prev_ap - 0.05:
			# Reset — serangan baru dimulai.
			_attack_started_emitted = false
			_impact_emitted = false
		elif _prev_ap > 0.01 and ap > 0.0:
			ap = maxf(ap, _prev_ap)
		_prev_ap = ap
	else:
		_prev_ap = 0.0

	# ── Hitung pose target ──
	var target = animator.compute(state, phase, ap, _skill_time, extra)

	# ── Blend pose saat ini menuju target ──
	if pose_current == null:
		pose_current = target
	else:
		_blend(pose_current, target, delta)

	# ── Sinyal attack ──
	if state == "attack" or state == "swing":
		if not _attack_started_emitted and ap > 0.01:
			_attack_started_emitted = true
			attack_started.emit()
		if not _impact_emitted and ap >= ATTACK_IMPACT_PROGRESS:
			_impact_emitted = true
			attack_impact.emit()

	# ── Update renderer ──
	renderer.pose = pose_current
	renderer.phase = phase
	# Trail management.
	if pose_current.trail:
		var tip := renderer.get_bow_tip()
		_trail_buf.append(to_global(tip))
		if _trail_buf.size() > TRAIL_MAX:
			_trail_buf.pop_front()
	else:
		if not _trail_buf.is_empty():
			_trail_buf.pop_front()
	renderer.trail_pts = _trail_buf.duplicate()

	# ── Notify SkillFX ──
	skill_fx.prev_pos = _prev_pos
	skill_fx.notify_drive(p_skill, global_position, facing, delta)
	_prev_pos = global_position

	renderer.queue_redraw()


## Derive state dari input Hero.
func _derive_state(action: String, moving: bool, skill: String) -> String:
	if _override_state != "":
		return _override_state
	if skill != "":
		return "skill_" + skill
	if action == "attack":
		# Cek apakah melee (swing) atau ranged (attack).
		if _hero != null and is_instance_valid(_hero):
			if _hero.get("target") != null and is_instance_valid(_hero.target):
				var dist := global_position.distance_to(_hero.target.global_position)
				if dist < 64.0:
					return "swing"
		return "attack"
	if action == "hurt":
		return "hurt"
	if action == "death":
		return "death"
	if moving:
		if _hero != null and is_instance_valid(_hero):
			var speed := float(_hero.get("move_speed"))
			if speed > 220.0:
				return "run"
		return "walk"
	return "idle"


## Track skill timer untuk animator.
func _track_skill(skill: String, delta: float) -> void:
	if skill != "" and skill != _skill_key:
		_skill_key = skill
		_skill_time = 0.0
		skill_cast.emit(skill)
	elif skill != "":
		_skill_time += delta
	elif _skill_key != "":
		_skill_key = ""
		_skill_time = 0.0


## Watch hero HP for hurt detection.
func _watch_hero() -> void:
	if _hero == null or not is_instance_valid(_hero):
		return
	var current_hp := float(_hero.hp)
	if current_hp < _hero_hp - 0.5 and _hero_hp >= 0.0:
		# Hero took damage — trigger hurt state via override.
		if _override_state == "":
			play("hurt", 0.3)
	_hero_hp = current_hp


## Blend pose current menuju target (smooth, tidak robotic).
func _blend(cur, target, delta: float) -> void:
	# Kecepatan blend — lebih cepat untuk attack/skill, lebih lambat untuk idle.
	var speed := 12.0
	var t := clampf(delta * speed, 0.0, 1.0)
	# Root.
	cur.root_x = lerpf(cur.root_x, target.root_x, t)
	cur.root_y = lerpf(cur.root_y, target.root_y, t)
	cur.torso_lean = lerpf(cur.torso_lean, target.torso_lean, t)
	cur.chest_flex = lerpf(cur.chest_flex, target.chest_flex, t)
	cur.head_lean = lerpf(cur.head_lean, target.head_lean, t)
	# Arms.
	cur.arm_f_sh = lerpf(cur.arm_f_sh, target.arm_f_sh, t)
	cur.arm_f_el = lerpf(cur.arm_f_el, target.arm_f_el, t)
	cur.arm_b_sh = lerpf(cur.arm_b_sh, target.arm_b_sh, t)
	cur.arm_b_el = lerpf(cur.arm_b_el, target.arm_b_el, t)
	# Legs.
	cur.leg_f_hip = lerpf(cur.leg_f_hip, target.leg_f_hip, t)
	cur.leg_f_knee = lerpf(cur.leg_f_knee, target.leg_f_knee, t)
	cur.leg_f_foot = lerpf(cur.leg_f_foot, target.leg_f_foot, t)
	cur.leg_b_hip = lerpf(cur.leg_b_hip, target.leg_b_hip, t)
	cur.leg_b_knee = lerpf(cur.leg_b_knee, target.leg_b_knee, t)
	cur.leg_b_foot = lerpf(cur.leg_b_foot, target.leg_b_foot, t)
	# Bow.
	cur.bow_angle = lerpf(cur.bow_angle, target.bow_angle, t)
	cur.bow_draw = lerpf(cur.bow_draw, target.bow_draw, t)
	cur.bow_off = cur.bow_off.lerp(target.bow_off, t)
	# Secondary motion — blend lebih lambat untuk kain.
	var ct := clampf(delta * 8.0, 0.0, 1.0)
	for i in 3:
		cur.cape[i] = lerpf(cur.cape[i], target.cape[i], ct)
		cur.hair[i] = lerpf(cur.hair[i], target.hair[i], ct)
	for i in 2:
		cur.hood[i] = lerpf(cur.hood[i], target.hood[i], ct)
	# Expression.
	cur.cape_flare = lerpf(cur.cape_flare, target.cape_flare, ct)
	cur.eye_blink = lerpf(cur.eye_blink, target.eye_blink, t * 2.0)
	cur.wind_glow = lerpf(cur.wind_glow, target.wind_glow, t)
	cur.hurt_tint = lerpf(cur.hurt_tint, target.hurt_tint, t * 1.5)
	cur.alpha = lerpf(cur.alpha, target.alpha, t * 0.5)
	# Trail — langsung (bool).
	cur.trail = target.trail


## API demo/showcase — paksa state sementara.
func play(state: String, duration: float = 1.0) -> void:
	_override_state = state
	_override_t = 0.0
	_override_dur = duration


## Dipanggil Hero.gd untuk cek apakah rig menangani FX skill sendiri.
func handles_skill_fx(key: String) -> bool:
	return skill_fx.handles_skill_fx(key)
