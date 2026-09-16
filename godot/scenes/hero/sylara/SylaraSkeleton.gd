# SylaraSkeleton.gd — root controller karakter Sylara (logika Godot native).
#
# Arsitektur modular (satu script = satu tanggung jawab):
#   SylaraSkeleton.gd    (root: state machine, blending, drive() API, sinyal)
#   ├── SylaraRenderer.gd   (pose → gambar _draw() berlapis, 100% kode)
#   ├── SylaraSkillFX.gd    (skill key → rangkaian VFX pooled via sinyal)
#   ├── SylaraCombatFeel.gd (audio + shake + hit-stop, event-driven sinyal)
#   ├── SylaraAnimator.gd   (state → pose target, tulis pakai-ulang)
#   ├── SylaraPose.gd       (data transfer pose tulang & secondary motion)
#   ├── SylaraArrow.gd      (visual proyektil basic attack)
#   └── SylaraPalette.gd    (warna terkontrol & hierarki kontras)
#
# Pola Godot yang dipakai (bukan pola port):
#   * EVENT-DRIVEN via sinyal: root memancarkan bow_released / skill_cast /
#     skill_released; SkillFX & Feel mendengarkan — tanpa polling per frame.
#   * OBSERVASI STATE HERO (read-only): animasi skill disinkronkan ke timer
#     kit hero ASLI (focus_fire/windrun/shackle/powershot), bukan durasi
#     perkiraan. Gameplay (damage/cooldown/kit) tetap milik HeroSkillKit.
#   * BIDIK 360°: root mengubah posisi target (dunia) ke ruang lokal rig dan
#     me-smooth aim dengan lerp_angle — busur membidik target nyata.
#
# Kontrak dengan Hero.gd (generik, sama untuk semua rig):
#   * drive(phase, action, attack_progress, facing, is_moving, skill, delta)
#     dipanggil Hero._drive_visual tiap physics frame.
#   * Digambar menghadap +x; Hero mem-flip Visual.scale.x — rig TIDAK
#     melakukan flip sendiri (menghindari double-flip).
#   * handles_skill_fx() = true → Hero melewatkan FX skill generik.
#   * spawn_attack_projectile() = hook opt-in: Hero memakai SylaraArrow
#     (visual khas wind-ranger) dengan parameter TowerBullet identik.
#
# Kontrak showcase/demo: play("hurt"/"death"/"victory", durasi) memaksa
# state sementara di luar drive() Hero.
class_name SylaraSkeleton
extends Node2D

const AnimatorScript = preload("res://scenes/hero/sylara/SylaraAnimator.gd")
const ArrowScript = preload("res://scenes/hero/sylara/SylaraArrow.gd")
const PoseScript = preload("res://scenes/hero/sylara/SylaraPose.gd")

## Tali dilepas / panah melesat (dimulai setiap siklus serangan).
signal bow_released
## Skill mulai aktif (key "q"/"w"/"e"/"r").
signal skill_cast(skill_key: String)
## Powershot TEBAR (charge habis) — aim_point = ujung kerucut (global).
signal skill_released(skill_key: String, aim_point: Vector2)
signal character_hurt
signal character_died

## Kecepatan proyektil basic attack (px/dtk) — parameter TowerBullet.
const ARROW_SPEED := 520.0
## Durasi pose burst setelah Powershot lepas (detik).
const RELEASE_WINDOW := 0.55
## Durasi jendela skill (frame 60fps) — dipakai FALLBACK saat kit hero
## tidak tersedia (demo standalone). Nilai ASLI dibaca dari kit.
const FOCUS_FRAMES := 180
const WINDRUN_FRAMES := 180
const SHACKLE_FRAMES := 150
const CHANNEL_FRAMES := 60
## Durasi porsi cast Shackle Shot (detik) — sisanya pose tahan tether.
const SHACKLE_CAST_SEC := 0.45
## Laju smoothing arah bidik (1/dtk).
const AIM_TRACK_RATE := 16.0
## Jarak bidik maksimum Powershot (px) — sama dengan max_range kit.
const POWERSHOT_RANGE := 300.0

@onready var renderer: SylaraRenderer = $Renderer
@onready var skill_fx: SylaraSkillFX = $SkillFX
@onready var feel: SylaraCombatFeel = $Feel

var animator: SylaraAnimator = null
var pose_current: SylaraPose = null
var pose_target: SylaraPose = null

## 1 / -1. Dipakai hanya untuk fallback arah bidik & spawn.
var facing := 1
## Showcase: node dunia yang dipaksa menjadi titik bidik (demo).
var aim_override: Node2D = null

var _hero = null
var _hero_hp := -1.0
var _override_state := ""
var _override_t := 0.0
var _override_dur := 0.0
var _skill_key := ""
var _skill_time := 0.0
var _release_t := -1.0
var _was_attacking := false
var _prev_ap := 0.0
var _aim_local := 0.0


func _ready() -> void:
	add_to_group("sylara_skeleton")
	animator = AnimatorScript.new()
	# Dua pose pakai-ulang: nol alokasi per frame (Android).
	pose_current = PoseScript.new()
	pose_target = PoseScript.new()
	animator.compute("idle", 0.0, 0.0, 0.0, {}, pose_current)
	# Hero (kalau ada di arena) = kakek node: Hero/Visual/<rig>.
	var n: Node = get_parent()
	if n != null:
		n = n.get_parent()
	if n != null and "hp" in n and "kit" in n:
		_hero = n
		_hero_hp = float(_hero.hp)


# ══════════════════════════════════════════════════════════
#  API Hero.gd — dipanggil tiap physics frame
# ══════════════════════════════════════════════════════════

func drive(p_phase: float, p_action: String, p_attack_progress: float,
		p_facing: int, p_moving: bool, p_skill: String,
		p_delta: float) -> void:
	var delta := p_delta if p_delta > 0.0 else get_physics_process_delta_time()
	if delta <= 0.0:
		delta = 1.0 / 60.0
	facing = 1 if p_facing >= 0 else -1
	var ap := clampf(p_attack_progress, 0.0, 1.0)

	animator.tick(delta)
	_track_skill(p_skill, delta)
	_watch_hero()
	_update_aim(delta)

	# ── State efektif: override (play) > release R > skill > attack > gerak ──
	var state := _derive_state(p_action, p_moving, p_skill)
	var prog := _skill_progress(p_skill)
	var extra := {}
	if _release_t >= 0.0:
		_release_t += delta
		if _release_t < RELEASE_WINDOW:
			state = "release"
			extra["t"] = clampf(_release_t / RELEASE_WINDOW, 0.0, 1.0)
		else:
			_release_t = -1.0
	if _override_state != "":
		_override_t += delta
		extra["t"] = clampf(_override_t / maxf(0.001, _override_dur), 0.0, 1.0)
		state = _override_state
		if _override_t >= _override_dur:
			_override_state = ""

	# ── Sinyal bow_released: tali lepas. Tercetus saat (a) masuk state
	# attack, atau (b) ap WRAP (tembakan baru dalam fire-rate cepat —
	# ap turun dari >0.5 ke <0.3 berarti attack_timer di-set ulang). ──
	var shot_started := false
	if state == "attack":
		if not _was_attacking and ap < 0.18:
			shot_started = true
		elif _prev_ap > 0.5 and ap < 0.3:
			shot_started = true
	_prev_ap = ap if state == "attack" else 0.0
	_was_attacking = state == "attack"
	if shot_started:
		bow_released.emit()

	# ── Pose target + blending (transisi halus, anti-robotic) ──
	animator.compute(state, p_phase, ap, prog, extra, pose_target)
	_publish_pose(p_skill)
	var k := 1.0 - exp(-_blend_rate(state) * delta)
	_blend_pose(pose_current, pose_target, k)

	# ── Serahkan ke renderer ──
	if renderer != null:
		renderer.pose = pose_current
		renderer.phase = p_phase
		renderer.queue_redraw()


## Showcase/demo + death anim: paksa state selama `dur` detik.
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
## TowerBullet identik (target, damage, team, speed, school, source) —
## hanya titik spawn (ujung tali busur) + gambar khas wind-ranger yang
## berbeda. Perilaku homing/hit/damage diwarisi utuh dari TowerBullet.
func spawn_attack_projectile(t: Node2D, dmg: float) -> Node2D:
	var arrow = ArrowScript.new()
	var team := "blue"
	var school := ""
	var col := Color(0.62, 0.98, 0.55)
	if _hero != null and is_instance_valid(_hero):
		team = str(_hero.get("team"))
		school = str(_hero.get("dmg_school"))
		var fc = _hero.get("fill_color")
		if fc is Color:
			col = (fc as Color).lightened(0.25)
	arrow.setup(t, dmg, team, "normal", {}, ARROW_SPEED, col, _hero, school)
	arrow.global_position = get_bow_nock_global()
	GameManager.attach_fx(arrow)
	return arrow


# ══════════════════════════════════════════════════════════
#  API PUBLIK — posisi global senjata & titik bidik
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


## Titik lahir anak panah: sedikit di depan tali, searah bidik.
func get_arrow_spawn_global() -> Vector2:
	if renderer == null:
		return global_position
	return renderer.to_global(renderer.get_bow_nock()
		+ renderer.get_bow_dir() * 6.0)


## Node dunia yang sedang dibidik (aim_override > target hero > null).
func get_aim_node() -> Node2D:
	if aim_override != null and is_instance_valid(aim_override):
		return aim_override
	if _hero == null or not is_instance_valid(_hero):
		return null
	var tgt = _hero.get("target")
	if tgt != null and is_instance_valid(tgt) \
			and not bool((tgt as Node).get("is_dead")):
		return tgt
	return null


## Titik akhir bidik (global) — dipakai SkillFX/Feel saat skill lepas.
func get_aim_point_global(max_len: float) -> Vector2:
	var t := get_aim_node()
	if t != null:
		var d: Vector2 = t.global_position - global_position
		if d.length() > 4.0:
			return global_position + d.normalized() * minf(d.length(), max_len)
	return global_position + Vector2(float(facing), 0.0) * max_len


## Status Focus Fire untuk SkillFX (aura tembak cepat).
func focus_active() -> bool:
	var kit := _kit()
	return bool(kit.get("_focus_fire_active", false))


# ══════════════════════════════════════════════════════════
#  INTERNAL
# ══════════════════════════════════════════════════════════

func _kit() -> Dictionary:
	if _hero != null and is_instance_valid(_hero) and "kit" in _hero:
		return _hero.get("kit")
	return {}


func _derive_state(action: String, moving: bool, skill: String) -> String:
	if skill != "":
		match skill:
			"q":
				# Focus Fire = tembak cepat: ikuti siklus attack bila
				# sedang menembak, pose hold-draw di jeda antar tembakan.
				return "attack" if action == "attack" else "focus"
			"w":
				return "windrun" if moving else "idle"
			"e":
				if _skill_time < SHACKLE_CAST_SEC:
					return "shackle_cast"
				return "shackle_hold"
			"r":
				return "channel"
	if action == "attack":
		return "attack"
	if action == "run":
		return "run"
	if action == "walk" or moving:
		return "walk"
	if action == "hurt":
		return "hurt"
	if action == "death":
		return "death"
	if action == "victory":
		return "victory"
	return "idle"


## Lacak transisi skill; r→(bukan r) = momen Powershot TEBAAR.
func _track_skill(skill: String, delta: float) -> void:
	if skill != _skill_key:
		if _skill_key == "r":
			_on_powershot_release()
		_skill_key = skill
		_skill_time = 0.0
		if skill != "":
			skill_cast.emit(skill)
	else:
		_skill_time += delta


func _on_powershot_release() -> void:
	_release_t = 0.0
	skill_released.emit("r", get_aim_point_global(POWERSHOT_RANGE))


## Deteksi kena pukul dari HP hero → pose hurt singkat. Read-only:
## hanya membaca properti, tanpa modifikasi state hero.
func _watch_hero() -> void:
	if _hero == null or not is_instance_valid(_hero):
		return
	var hp_now := float(_hero.hp)
	if hp_now < _hero_hp - 0.5 and _override_state == "":
		play("hurt", 0.3)
	_hero_hp = hp_now


## Arah bidik ruang lokal: posisi target dunia → lokal (memperhitungkan
# flip scale.x Hero), di-smooth supaya busur mengunci target dengan halus.
func _update_aim(delta: float) -> void:
	var t := get_aim_node()
	var desired := 0.0
	if t != null:
		var local_pt := to_local(t.global_position) - Vector2(0.0, -30.0)
		if local_pt.length_squared() > 4.0:
			desired = local_pt.angle()
	_aim_local = lerp_angle(_aim_local, desired,
		1.0 - exp(-AIM_TRACK_RATE * delta))


## Progress 0..1 jendela skill — dari timer kit ASLI bila tersedia,
# fallback durasi tetap untuk demo standalone.
func _skill_progress(skill: String) -> float:
	var kit := _kit()
	match skill:
		"q":
			if kit.has("_focus_fire_timer"):
				return clampf(1.0 - float(kit["_focus_fire_timer"])
					/ float(FOCUS_FRAMES), 0.0, 1.0)
			return clampf(_skill_time / 3.0, 0.0, 1.0)
		"w":
			if kit.has("_windrun_timer"):
				return clampf(1.0 - float(kit["_windrun_timer"])
					/ float(WINDRUN_FRAMES), 0.0, 1.0)
			return clampf(_skill_time / 3.0, 0.0, 1.0)
		"e":
			if kit.has("_shackle_timer"):
				return clampf(1.0 - float(kit["_shackle_timer"])
					/ float(SHACKLE_FRAMES), 0.0, 1.0)
			return clampf(_skill_time / 2.5, 0.0, 1.0)
		"r":
			if kit.has("_powershot_timer"):
				return clampf(1.0 - float(kit["_powershot_timer"])
					/ float(CHANNEL_FRAMES), 0.0, 1.0)
			return clampf(_skill_time / 1.0, 0.0, 1.0)
	return 0.0


## Tuliskan data aura/tether (state kit read-only) ke pose target.
func _publish_pose(skill: String) -> void:
	var kit := _kit()
	var pt := pose_target
	pt.aim_angle = _aim_local
	pt.focus_glow = 1.0 \
		if bool(kit.get("_focus_fire_active", false)) or skill == "q" else 0.0
	pt.windrun = 1.0 \
		if bool(kit.get("_windrun_active", false)) or skill == "w" else 0.0
	if bool(kit.get("_powershot_charging", false)) \
			and kit.has("_powershot_timer"):
		pt.channel = clampf(1.0 - float(kit["_powershot_timer"])
			/ float(CHANNEL_FRAMES), 0.0, 1.0)
	elif skill == "r":
		pt.channel = clampf(_skill_time
			/ maxf(0.001, float(CHANNEL_FRAMES) / 60.0), 0.0, 1.0)
	# Tether Shackle: target terkunci dari kit, fallback node bidik (demo).
	var tether_target: Node2D = null
	if bool(kit.get("_shackle_active", false)) or skill == "e":
		var shackle_t: Node2D = kit.get("_shackle_target", null)
		if shackle_t != null and is_instance_valid(shackle_t) \
				and not bool(shackle_t.get("is_dead")):
			tether_target = shackle_t
		else:
			tether_target = get_aim_node()
	pt.tether_on = tether_target != null
	if tether_target != null:
		pt.tether_local = to_local(tether_target.global_position) \
			+ Vector2(0.0, -6.0)
	pt.aim_point_local = to_local(get_aim_point_global(POWERSHOT_RANGE))


## Lerp pose-ke-pose (sudut lewat lerp_angle, auranya lewat lerpf).
func _blend_rate(state: String) -> float:
	match state:
		"attack", "shackle_cast", "release":
			return 26.0
		"channel":
			return 14.0
		"focus", "shackle_hold":
			return 12.0
		"windrun":
			return 16.0
		"hurt":
			return 22.0
		"death":
			return 8.0
		"walk", "run":
			return 12.0
	return 10.0


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
	cur.aim_angle = lerp_angle(cur.aim_angle, tgt.aim_angle, k)
	cur.bow_offset = lerpf(cur.bow_offset, tgt.bow_offset, k)
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
	cur.focus_glow = lerpf(cur.focus_glow, tgt.focus_glow, k)
	cur.windrun = lerpf(cur.windrun, tgt.windrun, k)
	cur.channel = lerpf(cur.channel, tgt.channel, k)
	cur.hurt_tint = lerpf(cur.hurt_tint, tgt.hurt_tint, k)
	cur.alpha = lerpf(cur.alpha, tgt.alpha, k)
	# Tether: fade halus masuk/keluar (posisi langsung lerp).
	var target_a: float = 1.0 if tgt.tether_on else 0.0
	cur.tether_alpha = lerpf(cur.tether_alpha, target_a, k)
	cur.tether_on = cur.tether_alpha > 0.01
	if tgt.tether_on:
		cur.tether_local = tgt.tether_local
	cur.aim_point_local = cur.aim_point_local.lerp(tgt.aim_point_local, k)
