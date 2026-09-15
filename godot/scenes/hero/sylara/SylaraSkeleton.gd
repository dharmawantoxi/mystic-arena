# SylaraSkeleton.gd — root controller karakter Sylara (sprite-based version).
#
# Arsitektur modular (satu script = satu tanggung jawab):
#   SylaraSkeleton.gd    (root: state machine, drive() API, sinyal)
#   ├── AnimatedSprite2D  (sprite-based animation via SpriteFrames)
#   └── SylaraSkillFX.gd  (skill key → urutan VFX pooled)
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

const SpriteSetupScript = preload("res://scenes/hero/sylara/SylaraSpriteSetup.gd")

signal attack_started
signal attack_impact
signal skill_cast(skill_key: String)

## Dipakai Hero.gd untuk memilih renderer; dipertahankan dari rig Kaizen.
const ATTACK_IMPACT_PROGRESS := 0.52

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var skill_fx: SylaraSkillFX = $SkillFX

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
## Track current animation to avoid redundant play() calls.
var _current_anim := ""


func _ready() -> void:
	add_to_group("sylara_skeleton")
	_prev_pos = global_position
	# Setup sprite frames from strips.
	SpriteSetupScript.setup_animated_sprite(sprite)
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
	var ap := clampf(p_attack_progress, 0.0, 1.0)

	_watch_hero()
	_track_skill(p_skill, delta)

	# ── State efektif: override (play) > skill > attack > swing > gerak > idle ──
	var state := _derive_state(p_action, p_moving, p_skill)
	if _override_state != "":
		_override_t += delta
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

	# ── Sinyal attack ──
	if state == "attack" or state == "swing":
		if not _attack_started_emitted and ap > 0.01:
			_attack_started_emitted = true
			attack_started.emit()
		if not _impact_emitted and ap >= ATTACK_IMPACT_PROGRESS:
			_impact_emitted = true
			attack_impact.emit()

	# ── Play sprite animation ──
	_play_animation(state)

	# ── Notify SkillFX ──
	skill_fx.prev_pos = _prev_pos
	skill_fx.notify_drive(p_skill, global_position, facing, delta)
	_prev_pos = global_position


## Play the appropriate sprite animation for the given state.
func _play_animation(state: String) -> void:
	# Map state to animation name.
	var anim_name := state
	# Handle states that don't have dedicated animations.
	if not sprite.sprite_frames.has_animation(anim_name):
		anim_name = "idle"
	
	# Only play if animation changed (avoid restarting looped anims).
	if anim_name != _current_anim:
		_current_anim = anim_name
		sprite.play(anim_name)


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


## API demo/showcase — paksa state sementara.
func play(state: String, duration: float = 1.0) -> void:
	_override_state = state
	_override_t = 0.0
	_override_dur = duration


## Dipanggil Hero.gd untuk cek apakah rig menangani FX skill sendiri.
func handles_skill_fx(key: String) -> bool:
	return skill_fx.handles_skill_fx(key)
