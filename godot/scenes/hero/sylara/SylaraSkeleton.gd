# SylaraSkeleton.gd — root controller karakter Sylara (v2 rebuild).
#
# Arsitektur modular (satu script = satu tanggung jawab):
#   SylaraSkeleton.gd    (root: state machine, blending, drive() API, sinyal,
#                         keputusan combat: swing-riposte, aim, skill release)
#   ├── SylaraRenderer.gd (pose → gambar _draw() berlapis, pixel art)
#   ├── SylaraSkillFX.gd  (skill key → sequencer durasi via VFXManager pooled)
#   ├── SylaraAnimator.gd (state → pose target berbobot & solver kaki)
#   ├── SylaraPose.gd     (data transfer pose tulang & secondary motion)
#   ├── SylaraPalette.gd  (warna terkontrol & hierarki kontras)
#   └── SylaraCombat.gd   (policy hit-stop / camera response per MASTER PROMPT)
#
# Kontrak dengan Hero.gd (TIDAK diubah — dikunci GameplayParityTest):
#   * drive(phase, action, attack_progress, facing, is_moving, skill, delta)
#     dipanggil Hero._drive_visual tiap physics frame.
#   * Digambar menghadap +x; Hero mem-flip Visual.scale.x — rig TIDAK
#     melakukan flip sendiri (menghindari double-flip).
#   * handles_skill_fx() = true → Hero melewatkan FX skill generik supaya
#     tidak dobel (NO VISUAL NOISE).
#   * style_projectile(b) → hook opsional: Hero._shoot_projectile memanggil
#     rig untuk memberi identitas panah pada proyektil serangan dasar.
#
# Keputusan combat feel di root (satu-satunya pembaca state kit):
#   * SWING riposte: target < SWING_RANGE → pose sapuan busur (visual only;
#     damage tetap lewat jalur ranged Hero — paritas pygame SWING_RANGE).
#   * AIM: sudut bidik vertikal ke target di-lock saat serangan dimulai.
#   * SKILL RELEASE R: edge kit `_powershot_charging` true→false → sinyal
#     skill_release (SkillFX = FX gale; Combat = hit-stop + trauma).
class_name SylaraSkeleton
extends Node2D

const AnimatorScript = preload("res://scenes/hero/sylara/SylaraAnimator.gd")

signal attack_started
signal attack_impact
signal skill_cast(skill_key: String)
signal skill_release(skill_key: String)
signal skill_impact(skill_key: String, target_pos: Vector2)
signal character_hurt
signal character_died

## Timing pelepasan panah (draw → release) dalam timeline serangan.
const ATTACK_IMPACT_PROGRESS := 0.52
## Target lebih dekat dari ini → sapuan melee (riposte), padanan
## `heroes/sylara_fx.py` pygame (SWING_RANGE = 64 dunia).
const SWING_RANGE := 64.0

@onready var renderer: SylaraRenderer = $Renderer
@onready var skill_fx: SylaraSkillFX = $SkillFX
@onready var combat: SylaraCombat = $Combat

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
## cooldown, jadi kalau cooldown berubah mid-swing ap bisa MUNDUR dan pose
## melompat ke belakang = stutter. Dilacak agar monoton naik.
var _prev_ap := 0.0
var _prev_action := ""
var _prev_pos := Vector2.ZERO
var _hero = null
var _hero_hp := -1.0
var _swing_mode := false
## Showcase: paksa mode sapuan di demo (tanpa hero/target).
var demo_swing := false
var _aim_ang := 0.0
var _prev_charging := false
var _r_released := false
var _speed01 := 0.0
var facing: int = 1


func _ready() -> void:
	add_to_group("sylara_skeleton")
	animator = AnimatorScript.new()
	pose_current = animator.compute("idle", 0.0, 0.0, 0.0, {})
	_prev_pos = global_position
	# Hero (kalau ada di arena) = kakek node: Hero/Visual/<rig>.
	if skill_fx != null and skill_fx.has_method("resolve_hero"):
		skill_fx.resolve_hero()
	if combat != null and combat.has_method("setup"):
		combat.setup(self)
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
	_watch_skill_release()

	# ── Keputusan combat: swing-riposte & aim di EDGE serangan ──
	if p_action == "attack" and _prev_action != "attack":
		_swing_mode = false
		_aim_ang = 0.0
		var tgt: Node = _hero_target()
		if _hero != null and is_instance_valid(_hero) \
				and is_instance_valid(tgt) and "global_position" in tgt:
			var dist := _hero.global_position.distance_to(
				(tgt as Node2D).global_position)
			_swing_mode = dist < SWING_RANGE
			_aim_ang = _aim_to(tgt as Node2D)
		elif _hero == null:
			# Demo/showcase (tanpa hero): sapuan bila diminta.
			_swing_mode = demo_swing
	elif p_action != "attack":
		_swing_mode = false
	_prev_action = p_action

	# ── State efektif: override (play) > skill > attack > gerak > idle ──
	var state := _derive_state(p_action, p_moving, p_skill)
	if state == "attack" and _swing_mode:
		state = "swing"
	var extra := {"aim": _aim_ang, "speed01": _speed01}
	if _override_state != "":
		_override_t += delta
		extra["t"] = clampf(_override_t / maxf(0.001, _override_dur), 0.0, 1.0)
		state = _override_state
		if _override_t >= _override_dur:
			_override_state = ""

	# ── attack_progress monoton naik dalam satu swing ──
	if state == "attack" or state == "swing":
		if _prev_ap > 0.5 and ap < _prev_ap - 0.4:
			# Serangan baru dimulai (wrap/reset).
			_attack_started_emitted = false
			_impact_emitted = false
		elif ap < _prev_ap:
			ap = _prev_ap
		_prev_ap = ap
	else:
		_prev_ap = 0.0

	# ── Sinyal combat feel (sinkron dengan timing impact panah/busur) ──
	_emit_combat_signals(state, ap)

	# ── Pose target + blending (transisi halus, anti-robotic) ──
	var skill_t := _skill_time if p_skill != "" else 0.0
	var target = animator.compute(state, phase, ap, skill_t, extra)
	var rate := _blend_rate(state)
	var k := 1.0 - exp(-rate * delta)
	_blend_pose(pose_current, target, k)

	# ── Serahkan ke renderer + trail + skill FX ──
	if renderer != null:
		renderer.pose = pose_current
		renderer.phase = phase
		_update_trail(pose_current)
		renderer.queue_redraw()

	# Kecepatan (untuk secondary motion cloth) + posisi-terdahulu untuk FX
	# (di-update TERAKHIR — FX memakai posisi sebelum bergerak).
	if skill_fx != null:
		skill_fx.prev_pos = _prev_pos
	if delta > 0.0:
		var speed_now: float = _prev_pos.distance_to(global_position) / delta
		_speed01 = lerpf(_speed01, clampf(speed_now / 320.0, 0.0, 1.0),
			1.0 - exp(-8.0 * delta))
	_prev_pos = global_position

	if skill_fx != null and skill_fx.has_method("notify_drive"):
		skill_fx.notify_drive(p_skill, global_position, facing, delta)


## Showcase/demo: paksa state (hurt/death/victory/run) selama `dur` detik.
func play(state: String, dur: float = 0.5) -> void:
	_override_state = state
	_override_t = 0.0
	_override_dur = maxf(0.05, dur)
	if state == "hurt":
		character_hurt.emit()
	elif state == "death":
		character_died.emit()


## Hero.gd melewatkan FX skill generik bila rig menanganinya sendiri.
func handles_skill_fx(_key: String) -> bool:
	return true


## Hook Hero._shoot_projectile: identitas panah angin pada proyektil
## serangan dasar (visual only — damage tetap milik TowerBullet).
func style_projectile(bullet: Node) -> void:
	if bullet != null and bullet.has_method("set_arrow_style"):
		bullet.set_arrow_style("wind")


## Showcase/demo: target dunia tetap untuk FX skill (tanpa hero).
func set_demo_target(pos: Vector2) -> void:
	if skill_fx != null and "demo_target" in skill_fx:
		skill_fx.demo_target = pos


## ── API PUBLIK — posisi global senjata (dipakai SkillFX) ──

func get_bow_grip_global() -> Vector2:
	if renderer == null:
		return global_position
	return renderer.to_global(renderer.get_bow_grip())


func get_bow_tip_global() -> Vector2:
	if renderer == null:
		return global_position
	return renderer.to_global(renderer.get_bow_tip())


func get_bow_nock_global() -> Vector2:
	if renderer == null:
		return global_position
	return renderer.to_global(renderer.get_bow_nock())


func get_bow_nock_local() -> Vector2:
	if renderer == null:
		return global_position
	return renderer.get_bow_nock()


func get_arrow_spawn_global() -> Vector2:
	if renderer == null:
		return global_position
	var grip: Vector2 = renderer.get_bow_grip()
	var tip: Vector2 = renderer.get_bow_tip()
	var dir := (tip - grip).normalized()
	return renderer.to_global(grip + dir * 18.0)


# ══════════════════════════════════════════════════════════
#  INTERNAL
# ══════════════════════════════════════════════════════════

func _hero_target() -> Node:
	if _hero != null and is_instance_valid(_hero) and "target" in _hero:
		return _hero.get("target")
	return null


## Sudut bidik vertikal ke target (rad; + = ke atas). Dipakai pose attack.
func _aim_to(tgt: Node2D) -> float:
	if _hero == null or not is_instance_valid(_hero):
		return 0.0
	var hy: float = _hero.global_position.y - 12.0
	var dx: float = absf(tgt.global_position.x - _hero.global_position.x)
	var dy: float = hy - tgt.global_position.y
	if dx < 4.0:
		return 0.0
	return atan2(dy, dx)


func _derive_state(action: String, moving: bool, skill: String) -> String:
	if skill != "":
		match skill:
			"q":
				return "skill_q"
			"w":
				return "skill_w"
			"e":
				return "skill_e"
			"r":
				return "skill_r"
	if action == "attack":
		return "attack"
	if action == "walk" or moving:
		return "walk"
	if action == "run":
		return "run"
	if action == "hurt":
		return "hurt"
	if action == "death":
		return "death"
	if action == "victory":
		return "victory"
	return "idle"


func _track_skill(skill: String, delta: float) -> void:
	if skill == "":
		if _skill_key != "":
			_skill_key = ""
			_skill_time = 0.0
			_prev_charging = false
			_r_released = false
		return
	if skill != _skill_key:
		_skill_key = skill
		_skill_time = 0.0
		skill_cast.emit(skill)
	else:
		_skill_time += delta


## Edge kit Powershot: charge true→false = momen release (damage kit terjadi
## di frame yang sama). Demo (tanpa hero) memakai fallback waktu.
func _watch_skill_release() -> void:
	if _skill_key != "r":
		return
	if _r_released:
		return
	if _hero != null and is_instance_valid(_hero) and "kit" in _hero:
		var kit: Dictionary = _hero.kit
		var charging := bool(kit.get("_powershot_charging", false))
		if _prev_charging and not charging:
			_r_released = true
			skill_release.emit("r")
		_prev_charging = charging
	elif _skill_time >= 0.95:
		_r_released = true
		skill_release.emit("r")


func _emit_combat_signals(state: String, ap: float) -> void:
	if state == "attack" or state == "swing":
		if not _attack_started_emitted:
			_attack_started_emitted = true
			_impact_emitted = false
			attack_started.emit()
		if not _impact_emitted and ap >= ATTACK_IMPACT_PROGRESS:
			_impact_emitted = true
			attack_impact.emit()
	else:
		_attack_started_emitted = false


## Deteksi kena pukul dari HP hero → pose hurt singkat (tanpa coupling:
## hanya baca properti, tanpa sinyal lintas-node).
func _watch_hero() -> void:
	if _hero == null or not is_instance_valid(_hero):
		return
	var hp_now := float(_hero.hp)
	if hp_now < _hero_hp - 0.5 and _override_state == "" \
			and not bool(_hero.get("is_dead")):
		play("hurt", 0.3)
	_hero_hp = hp_now


func _update_trail(p) -> void:
	if renderer == null:
		return
	if p.trail:
		# Trail disimpan di ruang LOKAL renderer (stabil terhadap flip
		# parent — menghindari jejak yang melenceng saat hero bergerak).
		renderer.trail_pts.append(renderer.get_bow_tip())
		if renderer.trail_pts.size() > 10:
			renderer.trail_pts.remove_at(0)
	elif not renderer.trail_pts.is_empty():
		renderer.trail_pts.remove_at(0)


func _blend_rate(state: String) -> float:
	match state:
		"attack", "swing", "skill_q":
			return 26.0
		"skill_e", "skill_r":
			return 24.0
		"skill_w":
			return 20.0
		"hurt":
			return 22.0
		"death":
			return 8.0
		"walk", "run":
			return 12.0
	return 10.0


## Lerp pose-ke-pose (sudut lewat lerp_angle). `k` sudah dihitung root.
func _blend_pose(cur, tgt, k: float) -> void:
	k = clampf(k, 0.0, 1.0)
	cur.root_x = lerpf(cur.root_x, tgt.root_x, k)
	cur.root_y = lerpf(cur.root_y, tgt.root_y, k)
	cur.torso_lean = lerp_angle(cur.torso_lean, tgt.torso_lean, k)
	cur.chest_flex = lerp_angle(cur.chest_flex, tgt.chest_flex, k)
	cur.head_lean = lerp_angle(cur.head_lean, tgt.head_lean, k)
	cur.look = lerpf(cur.look, tgt.look, k)
	cur.arm_f_sh = lerp_angle(cur.arm_f_sh, tgt.arm_f_sh, k)
	cur.arm_f_el = lerp_angle(cur.arm_f_el, tgt.arm_f_el, k)
	cur.arm_b_sh = lerp_angle(cur.arm_b_sh, tgt.arm_b_sh, k)
	cur.arm_b_el = lerp_angle(cur.arm_b_el, tgt.arm_b_el, k)
	cur.leg_f_hip = lerp_angle(cur.leg_f_hip, tgt.leg_f_hip, k)
	cur.leg_f_knee = lerpf(cur.leg_f_knee, tgt.leg_f_knee, k)
	cur.leg_f_foot = lerpf(cur.leg_f_foot, tgt.leg_f_foot, k)
	cur.leg_b_hip = lerp_angle(cur.leg_b_hip, tgt.leg_b_hip, k)
	cur.leg_b_knee = lerpf(cur.leg_b_knee, tgt.leg_b_knee, k)
	cur.leg_b_foot = lerpf(cur.leg_b_foot, tgt.leg_b_foot, k)
	cur.bow_angle = lerp_angle(cur.bow_angle, tgt.bow_angle, k)
	cur.bow_draw = lerpf(cur.bow_draw, tgt.bow_draw, k)
	cur.bow_off = cur.bow_off.lerp(tgt.bow_off, k)
	cur.shiver = lerpf(cur.shiver, tgt.shiver, k)
	cur.charge = lerpf(cur.charge, tgt.charge, k)
	cur.dust = lerpf(cur.dust, tgt.dust, k)
	for i in 3:
		cur.cape[i] = lerp_angle(cur.cape[i], tgt.cape[i], k)
		cur.hair[i] = lerp_angle(cur.hair[i], tgt.hair[i], k)
	for i in 2:
		cur.hood[i] = lerp_angle(cur.hood[i], tgt.hood[i], k)
	cur.cape_flare = lerpf(cur.cape_flare, tgt.cape_flare, k)
	cur.eye_blink = lerpf(cur.eye_blink, tgt.eye_blink, k)
	cur.wind_glow = lerpf(cur.wind_glow, tgt.wind_glow, k)
	cur.hurt_tint = lerpf(cur.hurt_tint, tgt.hurt_tint, k)
	cur.alpha = lerpf(cur.alpha, tgt.alpha, k)
	# trail: ambil langsung dari keputusan animator (bukan di-blend)
	cur.trail = tgt.trail
