# SylaraSkeleton.gd — root controller karakter Sylara (Godot 4.x).
#
# Arsitektur modular (satu script = satu tanggung jawab):
#   SylaraSkeleton.gd    (root: state machine, blending, drive() API, sinyal)
#   ├── SylaraRenderer.gd   (pose → gambar _draw() berlapis, pixel art)
#   ├── SylaraSkillFX.gd    (skill key → urutan VFX pooled via VFXManager)
#   ├── SylaraCombatFeel.gd (attack/skill → audio + shake + hit-stop + arc)
#   ├── SylaraAnimator.gd   (state → pose target, tulis pakai-ulang)
#   ├── SylaraPose.gd       (data transfer pose tulang & secondary motion)
#   ├── SylaraArrow.gd      (visual proyektil basic attack)
#   └── SylaraPalette.gd    (warna terkontrol & hierarki kontras)
#
# Kontrak dengan Hero.gd:
#   * drive(phase, action, attack_progress, facing, is_moving, skill, delta)
#     dipanggil Hero._drive_visual tiap physics frame.
#   * Digambar menghadap +x; Hero mem-flip Visual.scale.x — rig TIDAK
#     melakukan flip sendiri (menghindari double-flip).
#   * handles_skill_fx() = true → Hero melewatkan FX skill generik supaya
#     tidak dobel (NO VISUAL NOISE).
#   * spawn_attack_projectile() = hook opt-in: Hero memakai SylaraArrow
#     (visual khas) dengan parameter TowerBullet yang identik (paritas).
#
# Kontrak demo/showcase: play("hurt"/"death"/"victory"/"run", durasi)
# memaksa state sementara di luar drive() Hero.
class_name SylaraSkeleton
extends Node2D

const AnimatorScript = preload("res://scenes/hero/sylara/SylaraAnimator.gd")
const ArrowScript = preload("res://scenes/hero/sylara/SylaraArrow.gd")
const PoseScript = preload("res://scenes/hero/sylara/SylaraPose.gd")

signal attack_started
signal attack_impact
signal skill_cast(skill_key: String)
signal skill_impact(skill_key: String, target_pos: Vector2)
signal character_hurt
signal character_died

## Momen tali dilepas / tebasan menghantam. Sinkron dengan desain
## RELEASE-FIRST animator: spawn proyektil & damage instan terjadi di ap=0,
## jadi sinyal impact harus di awal siklus, bukan di tengah.
const ATTACK_IMPACT_PROGRESS := 0.08

## Jarak target di bawah ini → melee riposte ("swing"), bukan tembakan.
const MELEE_RANGE := 64.0

@onready var renderer: SylaraRenderer = $Renderer
@onready var skill_fx: SylaraSkillFX = $SkillFX
@onready var feel: SylaraCombatFeel = $Feel

var animator: SylaraAnimator = null
var pose_current: SylaraPose = null
var pose_target: SylaraPose = null

## Jenis serangan terakhir ("shot" / "swing") — dibaca Feel untuk memilih
## kilatan nock vs sabit tebasan saat attack_impact menyala.
var last_attack_kind := "shot"

## State override dari play() (demo / showcase / death anim Hero).
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
var _hero = null
var _hero_hp := -1.0
var facing: int = 1


func _ready() -> void:
	add_to_group("sylara_skeleton")
	animator = AnimatorScript.new()
	# Dua pose pakai-ulang: tidak ada alokasi per frame (Android).
	pose_current = PoseScript.new()
	pose_target = PoseScript.new()
	animator.compute("idle", 0.0, 0.0, 0.0, {}, pose_current)
	# Hero (kalau ada di arena) = kakek node: Hero/Visual/<rig>.
	if skill_fx != null and skill_fx.has_method("resolve_hero"):
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
	animator.compute(state, phase, ap, skill_t, extra, pose_target)
	var rate := _blend_rate(state)
	var k := 1.0 - exp(-rate * delta)
	_blend_pose(pose_current, pose_target, k)

	# ── Serahkan ke renderer + skill FX ──
	if renderer != null:
		renderer.pose = pose_current
		renderer.phase = phase
		renderer.queue_redraw()

	if skill_fx != null and skill_fx.has_method("notify_drive"):
		skill_fx.notify_drive(p_skill, global_position, facing, delta)



## Showcase/demo + death anim Hero: paksa state selama `dur` detik.
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


## Hook opt-in Hero._shoot_projectile: SylaraArrow dengan parameter
## TowerBullet yang IDENTIK (target, damage, team, speed 520, school,
## source) — hanya spawn dari ujung busur + gambar khas wind-ranger.
## Perilaku homing/hit/damage diwarisi 1:1 (paritas utuh).
func spawn_attack_projectile(t: Node2D, dmg: float) -> Node2D:
	var arrow = ArrowScript.new()
	var team := "blue"
	var school := ""
	var col := Color(0.55, 0.95, 0.45)
	if _hero != null and is_instance_valid(_hero):
		team = str(_hero.get("team"))
		school = str(_hero.get("dmg_school"))
		var fc = _hero.get("fill_color")
		if fc is Color:
			col = (fc as Color).lightened(0.35)
	arrow.setup(t, dmg, team, "normal", {}, 520.0, col, _hero, school)
	arrow.global_position = get_arrow_spawn_global()
	GameManager.attach_fx(arrow)
	return arrow


# ══════════════════════════════════════════════════════════
#  INTERNAL
# ══════════════════════════════════════════════════════════

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
		# Melee riposte bila target sangat dekat, default tembakan busur.
		# Dibaca dari jarak target hero (tanpa mengubah Hero.gd).
		if _hero_target_in_melee():
			return "swing"
		return "attack"
	if action == "swing":
		return "swing"
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


func _hero_target_in_melee() -> bool:
	if _hero == null or not is_instance_valid(_hero):
		return false
	var tgt = _hero.get("target")
	if tgt == null or not is_instance_valid(tgt) or not (tgt is Node2D):
		return false
	if bool((tgt as Node).get("is_dead")):
		return false
	return global_position.distance_to((tgt as Node2D).global_position) <= MELEE_RANGE


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
	if state == "attack" or state == "swing":
		if not _attack_started_emitted:
			_attack_started_emitted = true
			_impact_emitted = false
			last_attack_kind = "swing" if state == "swing" else "shot"
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
func _blend_pose(cur: SylaraPose, tgt: SylaraPose, k: float) -> void:
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
	cur.bow_angle = lerp_angle(cur.bow_angle, tgt.bow_angle, k)
	cur.bow_draw = lerpf(cur.bow_draw, tgt.bow_draw, k)
	cur.bow_off = cur.bow_off.lerp(tgt.bow_off, k)
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


# ══════════════════════════════════════════════════════════
#  API PUBLIK — Posisi Global Senjata & Efek
# ══════════════════════════════════════════════════════════

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


func get_arrow_spawn_global() -> Vector2:
	if renderer == null:
		return global_position
	# Anak panah lahir dari grip ke arah busur (sesuai pose bidikan).
	var grip: Vector2 = renderer.get_bow_grip()
	var tip: Vector2 = renderer.get_bow_tip()
	var dir := (tip - grip).normalized()
	return renderer.to_global(grip + dir * 18.0)
