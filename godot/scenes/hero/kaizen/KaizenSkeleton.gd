# KaizenSkeleton.gd — root controller karakter Kaizen (v4 rebuild).
#
# Arsitektur modular (satu script = satu tanggung jawab):
#   KaizenSkeleton.gd  (root: state, blending, drive() API, sinyal)
#   ├── KaizenAnimator.gd   (state → pose target)
#   ├── KaizenRenderer.gd   (pose → gambar _draw() berlapis)
#   └── KaizenSkillFX.gd    (skill key → urutan VFX pooled)
#
# Kontrak dengan Hero.gd (tidak berubah dari rig lama):
#   * drive(phase, action, attack_progress, facing, is_moving, skill, delta)
#     dipanggil Hero._drive_visual tiap physics frame.
#   * Digambar menghadap +x; Hero mem-flip Visual.scale.x — rig TIDAK
#     melakukan flip sendiri (menghindari double-flip).
#   * handles_skill_fx() = true → Hero melewatkan FX skill generik supaya
#     tidak dobel (NO VISUAL NOISE).
#
# Kontrak demo/showcase: play("hurt"/"death"/"victory"/"run", durasi)
# memaksa state sementara di luar drive() Hero.
class_name KaizenSkeleton
extends Node2D

const AnimatorScript = preload("res://scenes/hero/kaizen/KaizenAnimator.gd")

signal attack_started
signal attack_impact
signal skill_cast(skill_key: String)

## Dipakai Hero.gd untuk memilih renderer; dipertahankan dari rig lama.
const ATTACK_IMPACT_PROGRESS := 0.55

@onready var renderer: KaizenRenderer = $Renderer
@onready var skill_fx: KaizenSkillFX = $SkillFX

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
var _prev_pos := Vector2.ZERO
var _hero = null
var _hero_hp := -1.0
var facing: int = 1


func _ready() -> void:
	add_to_group("kaizen_skeleton")
	animator = AnimatorScript.new()
	pose_current = animator.compute("idle", 0.0, 0.0, 0.0, {})
	_prev_pos = global_position
	# Hero (kalau ada di arena) = kakek node: Hero/Visual/<rig>.
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

	# ── State efektif: override (play) > skill > attack > gerak > idle ──
	var state := _derive_state(p_action, p_moving, p_skill)
	var extra := {}
	if _override_state != "":
		_override_t += delta
		extra["t"] = clampf(_override_t / maxf(0.001, _override_dur), 0.0, 1.0)
		state = _override_state
		if _override_t >= _override_dur:
			_override_state = ""

	# ── Sinyal combat feel (dipakai demo; sistem lain boleh listen) ──
	_emit_combat_signals(state, ap)

	# ── Pose target + blending (transisi halus, anti-robotic) ──
	var skill_t := _skill_time if p_skill != "" else 0.0
	var target = animator.compute(state, phase, ap, skill_t, extra)
	var rate := _blend_rate(state)
	var k := 1.0 - exp(-rate * delta)
	_blend_pose(pose_current, target, k)

	# ── Serahkan ke renderer + trail + skill FX ──
	renderer.pose = pose_current
	renderer.phase = phase
	_update_trail(pose_current)
	renderer.queue_redraw()
	skill_fx.prev_pos = _prev_pos
	skill_fx.notify_drive(p_skill, global_position, facing, delta)
	_prev_pos = global_position


## Showcase/demo: paksa state (hurt/death/victory/run) selama `dur` detik.
func play(state: String, dur: float = 0.5) -> void:
	_override_state = state
	_override_t = 0.0
	_override_dur = maxf(0.05, dur)


## Hero.gd melewatkan FX skill generik bila rig menanganinya sendiri.
func handles_skill_fx(_key: String) -> bool:
	return true


# ══════════════════════════════════════════════════════════
#  INTERNAL
# ══════════════════════════════════════════════════════════

func _derive_state(action: String, moving: bool, skill: String) -> String:
	if skill != "":
		match skill:
			"q":
				return "skill_dash" if _is_dash_variant() else "skill_q"
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
	return "idle"


## Q2 Dash Strike vs Q1 Steel Wind: kit menandai dash; fallback = lompatan
## posisi (teleport 70% jarak target terjadi di frame cast).
func _is_dash_variant() -> bool:
	if _hero != null and is_instance_valid(_hero):
		if bool(_hero.kit.get("_is_dashing", false)):
			return true
	return _prev_pos.distance_to(global_position) > 24.0


func _track_skill(skill: String, delta: float) -> void:
	if skill == "":
		_skill_key = ""
		_skill_time = 0.0
		return
	if skill != _skill_key:
		_skill_key = skill
		_skill_time = 0.0
		skill_cast.emit(skill)
	else:
		_skill_time += delta


func _emit_combat_signals(state: String, ap: float) -> void:
	if state == "attack":
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
	if hp_now < _hero_hp - 0.5 and _override_state == "":
		play("hurt", 0.3)
	_hero_hp = hp_now


func _update_trail(p) -> void:
	if p.trail:
		renderer.trail_pts.append(
			renderer.to_global(renderer.get_blade_tip_local()))
		if renderer.trail_pts.size() > 9:
			renderer.trail_pts.remove_at(0)
	elif not renderer.trail_pts.is_empty():
		renderer.trail_pts.remove_at(0)


func _blend_rate(state: String) -> float:
	match state:
		"attack", "skill_q", "skill_dash":
			return 26.0
		"skill_e", "skill_r":
			return 24.0
		"hurt":
			return 20.0
		"death":
			return 9.0
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
	cur.weapon_angle = lerp_angle(cur.weapon_angle, tgt.weapon_angle, k)
	cur.weapon_off = cur.weapon_off.lerp(tgt.weapon_off, k)
	for i in 3:
		cur.scarf[i] = lerp_angle(cur.scarf[i], tgt.scarf[i], k)
		cur.pony[i] = lerp_angle(cur.pony[i], tgt.pony[i], k)
	for i in 2:
		cur.band[i] = lerp_angle(cur.band[i], tgt.band[i], k)
	cur.skirt_flare = lerpf(cur.skirt_flare, tgt.skirt_flare, k)
	cur.eye_blink = lerpf(cur.eye_blink, tgt.eye_blink, k)
	cur.wind_glow = lerpf(cur.wind_glow, tgt.wind_glow, k)
	cur.hurt_tint = lerpf(cur.hurt_tint, tgt.hurt_tint, k)
	cur.alpha = lerpf(cur.alpha, tgt.alpha, k)
	# trail: ambil dari target (keputusan animator), bukan diblend.
	cur.trail = tgt.trail


# ══════════════════════════════════════════════════════════
#  API PUBLIK LAMA (dipakai KaizenDemo + sistem FX)
# ══════════════════════════════════════════════════════════

func get_katana_tip_global() -> Vector2:
	return renderer.to_global(renderer.get_blade_tip_local())


func get_katana_grip_global() -> Vector2:
	if renderer.pose == null:
		return global_position
	var j := renderer._solve(renderer.pose)
	return renderer.to_global(j["hand_f"])
