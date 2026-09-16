# SylaraAnimator.gd — state machine animasi prosedural Sylara (Godot 4.x Masterwork Rebuild).
#
# Tanggung jawab SATU hal: (state, fase, progress) → SylaraPose target.
#
# Mengikuti kaidah animasi dan game feel profesional:
#   ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY
#
# Secondary motion (cape 3 segmen, hood 2 segmen, hair 3 segmen, bow string,
# eye blinking) dihitung kontinu berbasis fase cloth dan kecepatan gerak.
extends RefCounted

const PoseScript = preload("res://scenes/hero/sylara/SylaraPose.gd")

# ── Timing serangan ranged (draw & release) ──
const ATK_DRAW_START := 0.08     # anticipation selesai, mulai tarik tali
const ATK_DRAW_END := 0.48       # tali full drawn (tegangan maksimum)
const ATK_RELEASE := 0.52        # IMPACT — lepas tali busur
const ATK_FOLLOW_END := 0.72     # follow through

# ── Timing serangan melee (sapuan busur jarak dekat) ──
const SWING_WINDUP_END := 0.22
const SWING_STRIKE_END := 0.55
const SWING_HOLD_END := 0.68

# Blink: jadwal kedip acak mandiri agar wajah hidup
var _blink_cd := 2.5
var _blink_t := -1.0

# Kain & secondary motion
var _cloth_phase := 0.0
var _cloth_speed := 1.0


static func D(deg: float) -> float:
	return deg * PI / 180.0


static func ss(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


## Interpolasi sudut dalam derajat tanpa wrap.
static func sweep(from_deg: float, to_deg: float, t: float) -> float:
	return D(lerpf(from_deg, to_deg, clampf(t, 0.0, 1.0)))


## Dipanggil root tiap physics frame (delta asli).
func tick(delta: float) -> void:
	_cloth_phase += delta * 6.0 * _cloth_speed
	if _blink_t >= 0.0:
		_blink_t += delta
		if _blink_t > 0.16:
			_blink_t = -1.0
			_blink_cd = randf_range(1.8, 3.8)
	else:
		_blink_cd -= delta
		if _blink_cd <= 0.0:
			_blink_t = 0.0


func _blink_amount() -> float:
	if _blink_t < 0.0:
		return 0.0
	return sin(clampf(_blink_t / 0.16, 0.0, 1.0) * PI)


## Hitung pose target berdasarkan state, progress, dan skill time.
func compute(state: String, phase: float, attack_progress: float,
		skill_t: float, extra: Dictionary) -> Object:
	var p = PoseScript.new()
	p.eye_blink = _blink_amount()

	match state:
		"idle":
			_idle(p, phase)
		"walk":
			_walk(p, phase)
		"run":
			_run(p, phase)
		"attack":
			_attack(p, attack_progress, phase)
		"swing":
			_swing(p, attack_progress, phase)
		"skill_q":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 3.0, 0.0, 1.0)
			_skill_q(p, prog, phase)
		"skill_w":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 3.0, 0.0, 1.0)
			_skill_w(p, prog, phase, skill_t)
		"skill_e":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 2.5, 0.0, 1.0)
			_skill_e(p, prog, phase)
		"skill_r":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 1.35, 0.0, 1.0)
			_skill_r(p, prog, phase, skill_t)
		"hurt":
			_hurt(p, float(extra.get("t", 0.0)), phase)
		"death":
			_death(p, float(extra.get("t", 0.0)))
		"victory":
			_victory(p, phase)
		_:
			_idle(p, phase)

	# Secondary motion untuk kain & rambut
	_cloth(p, state, phase)
	return p


# ══════════════════════════════════════════════════════════
#  1. IDLE (Stance Waspada Ranger)
# ══════════════════════════════════════════════════════════

func _idle(p: Object, phase: float) -> void:
	_cloth_speed = 1.0
	var breath := sin(phase * 2.4) * 0.02
	p.root_y = sin(phase * 2.4) * 0.65
	p.torso_lean = breath
	p.chest_flex = breath * 0.5
	p.head_lean = sin(phase * 1.8 + 0.4) * 0.025

	# Lengan depan memegang busur rileks
	p.arm_f_sh = 0.35 + sin(phase * 2.0) * 0.02
	p.arm_f_el = 0.65
	# Lengan belakang rileks di samping
	p.arm_b_sh = -0.08 + sin(phase * 2.2 + 1.0) * 0.02
	p.arm_b_el = 0.45

	# Kaki terbuka mantap (archer stance)
	p.leg_f_hip = 0.07
	p.leg_f_knee = -0.05
	p.leg_b_hip = -0.08
	p.leg_b_knee = -0.04
	p.leg_f_foot = 0.12
	p.leg_b_foot = 0.10

	# Busur dipegang diagonal rendah
	p.bow_angle = -0.45 + sin(phase * 1.6) * 0.03
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  2. WALK (Langkah Ranger Anggun)
# ══════════════════════════════════════════════════════════

func _walk(p: Object, phase: float) -> void:
	_cloth_speed = 1.45
	var cycle := phase * 4.6
	var s := sin(cycle)
	var c := cos(cycle)

	p.root_y = abs(s) * 1.8 - 0.5
	p.root_x = s * 0.85
	p.torso_lean = s * 0.045
	p.chest_flex = 0.02
	p.head_lean = -s * 0.025

	# Kaki berjalan
	p.leg_f_hip = s * 0.36
	p.leg_f_knee = -abs(s) * 0.36 - 0.05
	p.leg_b_hip = -s * 0.36
	p.leg_b_knee = -abs(c) * 0.36 - 0.05
	p.leg_f_foot = 0.10 + s * 0.08
	p.leg_b_foot = 0.10 - s * 0.08

	# Lengan mengayun harmonis
	p.arm_f_sh = 0.30 - s * 0.14
	p.arm_f_el = 0.55 + abs(s) * 0.1
	p.arm_b_sh = -0.06 + s * 0.14
	p.arm_b_el = 0.42 + abs(c) * 0.1

	p.bow_angle = -0.40 + s * 0.07
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  3. RUN (Lari Cepat dengan Busur Siap)
# ══════════════════════════════════════════════════════════

func _run(p: Object, phase: float) -> void:
	_cloth_speed = 2.2
	var cycle := phase * 7.2
	var s := sin(cycle)
	var c := cos(cycle)

	p.root_y = abs(s) * 3.4 - 1.3
	p.root_x = s * 2.0
	p.torso_lean = 0.14 + s * 0.065
	p.chest_flex = 0.05
	p.head_lean = -0.045

	# Langkah lari panjang
	p.leg_f_hip = s * 0.58
	p.leg_f_knee = -abs(s) * 0.68 - 0.12
	p.leg_b_hip = -s * 0.58
	p.leg_b_knee = -abs(c) * 0.68 - 0.12
	p.leg_f_foot = 0.16 + s * 0.12
	p.leg_b_foot = 0.16 - s * 0.12

	# Lengan depan menahan busur stabil ke depan
	p.arm_f_sh = 0.58 + s * 0.08
	p.arm_f_el = 0.72
	p.arm_b_sh = -0.32 + s * 0.28
	p.arm_b_el = 0.72 + abs(c) * 0.2

	p.bow_angle = -0.22 + s * 0.08
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  4. ATTACK (Ranged — Tarik & Lepas Panah Penuh Bobot)
# ══════════════════════════════════════════════════════════

func _attack(p: Object, ap: float, phase: float) -> void:
	_cloth_speed = 1.85

	if ap < ATK_DRAW_START:
		# ANTICIPATION: Angkat busur, condong ke belakang menyiapkan tarikan
		var t := ss(ap / ATK_DRAW_START)
		p.torso_lean = lerpf(0.0, -0.07, t)
		p.arm_f_sh = lerpf(0.35, 0.88, t)
		p.arm_f_el = lerpf(0.65, 0.22, t)
		p.arm_b_sh = lerpf(-0.08, -0.52, t)
		p.arm_b_el = lerpf(0.45, 1.15, t)
		p.bow_angle = lerpf(-0.45, 0.12, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.0, -1.6, t)

	elif ap < ATK_DRAW_END:
		# DRAW: Tarik tali busur ke belakang (tension building)
		var t := ss((ap - ATK_DRAW_START) / (ATK_DRAW_END - ATK_DRAW_START))
		p.torso_lean = lerpf(-0.07, -0.11, t)
		p.arm_f_sh = 0.88 + t * 0.06
		p.arm_f_el = lerpf(0.22, 0.12, t)    # lengan depan lurus membidik
		p.arm_b_sh = lerpf(-0.52, -0.88, t)   # siku belakang ditarik kuat
		p.arm_b_el = lerpf(1.15, 1.48, t)
		p.bow_angle = lerpf(0.12, 0.04, t)
		p.bow_draw = t                        # tali tertarik penuh
		p.root_x = lerpf(-1.6, -2.6, t)
		p.chest_flex = t * 0.05
		p.wind_glow = t * 0.35

	elif ap < ATK_RELEASE:
		# RELEASE (IMPACT Frame): Tali lepas, panah melesat, recoil forward kick
		var t := (ap - ATK_DRAW_END) / (ATK_RELEASE - ATK_DRAW_END)
		p.torso_lean = lerpf(-0.11, 0.05, t)
		p.arm_f_sh = 0.92
		p.arm_f_el = 0.10
		p.arm_b_sh = lerpf(-0.88, -0.28, t)
		p.arm_b_el = lerpf(1.48, 0.55, t)
		p.bow_angle = 0.04
		p.bow_draw = lerpf(1.0, 0.0, t * t)   # tali snap seketika
		p.root_x = lerpf(-2.6, 1.2, t)
		p.chest_flex = lerpf(0.05, -0.02, t)
		p.wind_glow = 0.5
		p.trail = t < 0.55

	else:
		# FOLLOW THROUGH & RECOVERY: Kembali ke sikap siaga
		var t := ss((ap - ATK_RELEASE) / (1.0 - ATK_RELEASE))
		p.torso_lean = lerpf(0.05, 0.0, t)
		p.arm_f_sh = lerpf(0.92, 0.35, t)
		p.arm_f_el = lerpf(0.10, 0.65, t)
		p.arm_b_sh = lerpf(-0.28, -0.08, t)
		p.arm_b_el = lerpf(0.55, 0.45, t)
		p.bow_angle = lerpf(0.04, -0.45, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(1.2, 0.0, t)
		p.chest_flex = lerpf(-0.02, 0.0, t)
		p.wind_glow = lerpf(0.5, 0.0, t)

	p.leg_f_hip = 0.16 + sin(phase * 0.5) * 0.02
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  5. SWING (Melee Riposte — Tebasan Busur Jarak Dekat)
# ══════════════════════════════════════════════════════════

func _swing(p: Object, ap: float, _phase: float) -> void:
	_cloth_speed = 2.1

	if ap < SWING_WINDUP_END:
		var t := ss(ap / SWING_WINDUP_END)
		p.torso_lean = lerpf(0.0, -0.16, t)
		p.arm_f_sh = lerpf(0.35, -0.65, t)
		p.arm_f_el = lerpf(0.65, 0.95, t)
		p.bow_angle = lerpf(-0.45, 1.85, t)
		p.root_x = lerpf(0.0, -2.2, t)
	elif ap < SWING_STRIKE_END:
		var t := ss((ap - SWING_WINDUP_END) / (SWING_STRIKE_END - SWING_WINDUP_END))
		p.torso_lean = lerpf(-0.16, 0.20, t)
		p.arm_f_sh = lerpf(-0.65, 1.25, t)
		p.arm_f_el = lerpf(0.95, 0.28, t)
		p.bow_angle = lerpf(1.85, -1.25, t)
		p.root_x = lerpf(-2.2, 3.2, t)
		p.chest_flex = lerpf(0.0, 0.09, t)
		p.trail = true
	else:
		var t := ss((ap - SWING_STRIKE_END) / (1.0 - SWING_STRIKE_END))
		p.torso_lean = lerpf(0.20, 0.0, t)
		p.arm_f_sh = lerpf(1.25, 0.35, t)
		p.arm_f_el = lerpf(0.28, 0.65, t)
		p.bow_angle = lerpf(-1.25, -0.45, t)
		p.root_x = lerpf(3.2, 0.0, t)
		p.chest_flex = lerpf(0.09, 0.0, t)
		p.trail = t < 0.3

	p.leg_f_hip = 0.22
	p.leg_f_knee = -0.11
	p.leg_b_hip = -0.24
	p.leg_b_knee = -0.09
	p.arm_b_sh = -0.16
	p.arm_b_el = 0.52


# ══════════════════════════════════════════════════════════
#  6. SKILL Q — FOCUS FIRE (Rapid Volley Barrage)
# ══════════════════════════════════════════════════════════

func _skill_q(p: Object, prog: float, _phase: float) -> void:
	_cloth_speed = 2.1

	if prog < 0.08:
		var t := ss(prog / 0.08)
		p.arm_f_sh = lerpf(0.35, 1.02, t)
		p.arm_f_el = lerpf(0.65, 0.18, t)
		p.bow_angle = lerpf(-0.45, 0.22, t)
		p.torso_lean = lerpf(0.0, -0.09, t)
	elif prog < 0.88:
		var volley_t := (prog - 0.08) / 0.80
		var cycle := sin(volley_t * TAU * 4.5)
		var draw_t := (cycle + 1.0) * 0.5

		p.arm_f_sh = 0.92 + draw_t * 0.12
		p.arm_f_el = 0.14 + (1.0 - draw_t) * 0.16
		p.arm_b_sh = -0.52 - draw_t * 0.42
		p.arm_b_el = 0.82 + draw_t * 0.62
		p.bow_angle = 0.14 + sin(volley_t * TAU * 4.5 + 0.5) * 0.09
		p.bow_draw = draw_t
		p.torso_lean = -0.09 + cycle * 0.035
		p.root_x = -2.2 + cycle * 1.1
		p.wind_glow = 0.45 + draw_t * 0.45
	else:
		var t := ss((prog - 0.88) / 0.12)
		p.arm_f_sh = lerpf(0.96, 0.35, t)
		p.arm_f_el = lerpf(0.18, 0.65, t)
		p.arm_b_sh = lerpf(-0.72, -0.08, t)
		p.arm_b_el = lerpf(1.22, 0.45, t)
		p.bow_angle = lerpf(0.14, -0.45, t)
		p.bow_draw = lerpf(0.4, 0.0, t)
		p.torso_lean = lerpf(-0.07, 0.0, t)
		p.wind_glow = lerpf(0.6, 0.0, t)
		p.root_x = lerpf(-1.6, 0.0, t)

	p.leg_f_hip = 0.16
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  7. SKILL W — WINDRUN (Gale Aura Sprint)
# ══════════════════════════════════════════════════════════

func _skill_w(p: Object, prog: float, phase: float, skill_t: float) -> void:
	_cloth_speed = 2.9

	if prog < 0.10:
		var t := ss(prog / 0.10)
		p.root_y = lerpf(0.0, -3.2, t)
		p.torso_lean = lerpf(0.0, -0.07, t)
		p.arm_f_sh = lerpf(0.35, 0.72, t)
		p.arm_f_el = lerpf(0.65, 0.28, t)
		p.arm_b_sh = lerpf(-0.08, -0.62, t)
		p.arm_b_el = lerpf(0.45, 0.28, t)
		p.bow_angle = lerpf(-0.45, 0.32, t)
		p.wind_glow = t * 0.75
	elif prog < 0.88:
		var run_c := phase * 7.2
		var s := sin(run_c)
		p.root_y = -3.2 + abs(s) * 2.2
		p.root_x = s * 1.3
		p.torso_lean = 0.09 + s * 0.045
		p.arm_f_sh = 0.62 + s * 0.09
		p.arm_f_el = 0.38
		p.arm_b_sh = -0.42 + s * 0.16
		p.arm_b_el = 0.48
		p.bow_angle = -0.12 + s * 0.07
		p.leg_f_hip = s * 0.52
		p.leg_f_knee = -abs(s) * 0.52 - 0.11
		p.leg_b_hip = -s * 0.52
		p.leg_b_knee = -abs(cos(run_c)) * 0.52 - 0.11
		p.wind_glow = 0.65 + sin(skill_t * 5.2) * 0.22
	else:
		var t := ss((prog - 0.88) / 0.12)
		p.root_y = lerpf(-3.2, 0.0, t)
		p.torso_lean = lerpf(0.09, 0.0, t)
		p.arm_f_sh = lerpf(0.62, 0.35, t)
		p.arm_f_el = lerpf(0.38, 0.65, t)
		p.arm_b_sh = lerpf(-0.42, -0.08, t)
		p.arm_b_el = lerpf(0.48, 0.45, t)
		p.bow_angle = lerpf(-0.12, -0.45, t)
		p.wind_glow = lerpf(0.55, 0.0, t)
		p.leg_f_hip = lerpf(0.3, 0.07, t)
		p.leg_f_knee = lerpf(-0.3, -0.05, t)
		p.leg_b_hip = lerpf(-0.3, -0.08, t)
		p.leg_b_knee = lerpf(-0.3, -0.04, t)


# ══════════════════════════════════════════════════════════
#  8. SKILL E — SHACKLE SHOT (Precision Vine Loose)
# ══════════════════════════════════════════════════════════

func _skill_e(p: Object, prog: float, _phase: float) -> void:
	_cloth_speed = 1.65

	if prog < 0.15:
		var t := ss(prog / 0.15)
		p.arm_f_sh = lerpf(0.35, 1.02, t)
		p.arm_f_el = lerpf(0.65, 0.14, t)
		p.arm_b_sh = lerpf(-0.08, -0.92, t)
		p.arm_b_el = lerpf(0.45, 1.52, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t * 0.85
		p.torso_lean = lerpf(0.0, -0.13, t)
		p.root_x = lerpf(0.0, -2.1, t)
		p.head_lean = -0.07
	elif prog < 0.25:
		var t := ss((prog - 0.15) / 0.10)
		p.arm_f_sh = 1.02
		p.arm_f_el = 0.12
		p.arm_b_sh = lerpf(-0.92, -0.22, t)
		p.arm_b_el = lerpf(1.52, 0.52, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(0.85, 0.0, t * t)
		p.torso_lean = lerpf(-0.13, 0.07, t)
		p.root_x = lerpf(-2.1, 1.6, t)
		p.wind_glow = lerpf(0.0, 0.55, t)
	elif prog < 0.78:
		var t := (prog - 0.25) / 0.53
		p.arm_f_sh = 0.88
		p.arm_f_el = 0.18
		p.arm_b_sh = -0.22
		p.arm_b_el = 0.52
		p.bow_angle = 0.05
		p.bow_draw = 0.0
		p.torso_lean = 0.04
		p.wind_glow = 0.42 + sin(t * TAU * 2.0) * 0.16
	else:
		var t := ss((prog - 0.78) / 0.22)
		p.arm_f_sh = lerpf(0.88, 0.35, t)
		p.arm_f_el = lerpf(0.18, 0.65, t)
		p.arm_b_sh = lerpf(-0.22, -0.08, t)
		p.arm_b_el = lerpf(0.52, 0.45, t)
		p.bow_angle = lerpf(0.05, -0.45, t)
		p.torso_lean = lerpf(0.04, 0.0, t)
		p.wind_glow = lerpf(0.3, 0.0, t)
		p.root_x = lerpf(1.2, 0.0, t)

	p.leg_f_hip = 0.16
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  9. SKILL R — POWERSHOT (Charged Gale Blast Ultimate)
# ══════════════════════════════════════════════════════════

func _skill_r(p: Object, prog: float, _phase: float, _skill_t: float) -> void:
	_cloth_speed = 2.6

	if prog < 0.35:
		# CHARGE: Posisi kuda-kuda kokoh, tarikan busur maksimal
		var t := ss(prog / 0.35)
		p.arm_f_sh = lerpf(0.35, 1.08, t)
		p.arm_f_el = lerpf(0.65, 0.07, t)
		p.arm_b_sh = lerpf(-0.08, -1.05, t)
		p.arm_b_el = lerpf(0.45, 1.65, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t
		p.torso_lean = lerpf(0.0, -0.15, t)
		p.root_x = lerpf(0.0, -3.8, t)
		p.root_y = lerpf(0.0, -1.6, t)
		p.chest_flex = t * 0.07
		p.wind_glow = t * 0.95

	elif prog < 0.45:
		# RELEASE: Ledakan badai kerucut 5-panah gale
		var t := ss((prog - 0.35) / 0.10)
		p.arm_f_sh = 1.08
		p.arm_f_el = 0.06
		p.arm_b_sh = lerpf(-1.05, -0.10, t)
		p.arm_b_el = lerpf(1.65, 0.38, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(1.0, 0.0, t * t)
		p.torso_lean = lerpf(-0.15, 0.14, t)
		p.root_x = lerpf(-3.8, 4.2, t)
		p.root_y = lerpf(-1.6, 0.6, t)
		p.chest_flex = lerpf(0.07, -0.04, t)
		p.wind_glow = 1.0
		p.trail = true

	elif prog < 0.72:
		# GALE TUNNEL: Follow through pose
		var t := (prog - 0.45) / 0.27
		p.arm_f_sh = lerpf(1.08, 0.82, t)
		p.arm_f_el = lerpf(0.06, 0.24, t)
		p.arm_b_sh = -0.10
		p.arm_b_el = 0.38
		p.bow_angle = lerpf(0.0, 0.10, t)
		p.torso_lean = lerpf(0.14, 0.04, t)
		p.root_x = lerpf(4.2, 1.6, t)
		p.wind_glow = lerpf(1.0, 0.4, t)
		p.trail = t < 0.38

	else:
		# RECOVERY
		var t := ss((prog - 0.72) / 0.28)
		p.arm_f_sh = lerpf(0.82, 0.35, t)
		p.arm_f_el = lerpf(0.24, 0.65, t)
		p.arm_b_sh = lerpf(-0.10, -0.08, t)
		p.arm_b_el = lerpf(0.38, 0.45, t)
		p.bow_angle = lerpf(0.10, -0.45, t)
		p.torso_lean = lerpf(0.04, 0.0, t)
		p.root_x = lerpf(1.6, 0.0, t)
		p.wind_glow = lerpf(0.3, 0.0, t)

	p.leg_f_hip = 0.22
	p.leg_f_knee = -0.11
	p.leg_b_hip = -0.24
	p.leg_b_knee = -0.09


# ══════════════════════════════════════════════════════════
#  10. HURT & HIT REACTION
# ══════════════════════════════════════════════════════════

func _hurt(p: Object, t: float, _phase: float) -> void:
	_cloth_speed = 1.6
	var recoil := sin(t * PI)
	p.root_x = -recoil * 3.2
	p.root_y = -recoil * 1.6
	p.torso_lean = -recoil * 0.22
	p.head_lean = -recoil * 0.16
	p.arm_f_sh = 0.35 + recoil * 0.32
	p.arm_f_el = 0.65 + recoil * 0.22
	p.arm_b_sh = -0.08 - recoil * 0.32
	p.arm_b_el = 0.45 + recoil * 0.22
	p.bow_angle = -0.45 - recoil * 0.32
	p.hurt_tint = recoil * 0.85
	p.leg_f_hip = 0.07 + recoil * 0.11
	p.leg_b_hip = -0.08 - recoil * 0.11


# ══════════════════════════════════════════════════════════
#  11. DEATH (Roboh Dramatis & Alpha Dissolve)
# ══════════════════════════════════════════════════════════

func _death(p: Object, t: float) -> void:
	_cloth_speed = 0.45
	var fall := ss(minf(t * 1.5, 1.0))

	p.root_y = fall * 19.0
	p.root_x = -fall * 5.2
	p.torso_lean = -fall * 0.82
	p.chest_flex = -fall * 0.32
	p.head_lean = -fall * 0.52
	p.arm_f_sh = -fall * 0.62
	p.arm_f_el = fall * 0.82
	p.arm_b_sh = -fall * 0.82
	p.arm_b_el = fall * 0.62
	p.bow_angle = -0.45 - fall * 1.25
	p.leg_f_hip = fall * 0.42
	p.leg_f_knee = -fall * 0.52
	p.leg_b_hip = -fall * 0.22
	p.leg_b_knee = -fall * 0.32
	p.alpha = lerpf(1.0, 0.25, ss(maxf(0.0, (t - 0.6) / 0.4)))


# ══════════════════════════════════════════════════════════
#  12. VICTORY (Angkat Busur Kemenangan)
# ══════════════════════════════════════════════════════════

func _victory(p: Object, phase: float) -> void:
	_cloth_speed = 1.25
	var wave := sin(phase * 2.0)

	p.root_y = -2.2 + wave * 1.1
	p.torso_lean = -0.05 + wave * 0.03
	p.arm_f_sh = 2.25 + wave * 0.10
	p.arm_f_el = 0.14
	p.arm_b_sh = -0.32 + wave * 0.06
	p.arm_b_el = 0.42
	p.bow_angle = 1.45 + wave * 0.08
	p.head_lean = -0.11 + wave * 0.03
	p.wind_glow = 0.35 + wave * 0.15
	p.leg_f_hip = 0.11
	p.leg_b_hip = -0.13


# ══════════════════════════════════════════════════════════
#  13. SECONDARY MOTION — KAIN & RAMBUT
# ══════════════════════════════════════════════════════════

func _cloth(p: Object, state: String, _phase: float) -> void:
	var cp := _cloth_phase
	var cape_base := PI + 0.10

	# 3 segmen cape
	for i in 3:
		var seg_speed := 0.12 + float(i) * 0.08
		var wave := sin(cp + float(i) * 0.72) * seg_speed
		p.cape[i] = cape_base + wave + float(i) * 0.06

	# 2 segmen hood cowl
	for i in 2:
		var wave := sin(cp * 0.82 + float(i) * 0.92) * 0.08
		p.hood[i] = PI + wave

	# 3 segmen rambut
	for i in 3:
		var seg_speed := 0.10 + float(i) * 0.07
		var wave := sin(cp * 1.12 + float(i) * 0.62 + 1.2) * seg_speed
		p.hair[i] = PI + 0.15 + wave + float(i) * 0.05

	# Kibaran ekstra saat berlari / skill
	if state in ["run", "skill_w"]:
		for i in 3:
			p.cape[i] += 0.22 + float(i) * 0.08
		for i in 3:
			p.hair[i] += 0.16 + float(i) * 0.06
	elif state in ["skill_r"] or p.trail:
		for i in 3:
			p.cape[i] += 0.14
		for i in 3:
			p.hair[i] += 0.09
