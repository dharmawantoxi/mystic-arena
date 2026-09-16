# SylaraAnimator.gd — state machine animasi prosedural Sylara (v2 rebuild).
#
# Tanggung jawab SATU hal: (state, fase, progress) → SylaraPose target.
#
# Kaidah animasi & game feel:
#   ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY
#
# Peningkatan v2 dibanding v1:
#   * SOLVER KAKI (2-bone IK) — telapak menapak di tanah (tanpa slide),
#     lutut menekuk benar, toe-off & heel-strike terbaca + debu kontak.
#   * Easing nyata (smoothstep, ease-in/out cubic, ease-out back overshoot)
#     — gerakan tidak lagi sinus linier yang robotic.
#   * Head lead/lag + drift pandangan idle.
#   * Lengan busur STABIL saat jalan/lari (membawa senjata siaga),
#     hanya lengan belakang yang mengayun — identitas ranger.
#   * Reaksi badan per-skill: Q volley cepat, W sprint wind, E aim presisi,
#     R charge crouch + getar + lunge release.
#   * String shiver pasca-release; wind glow; cape/hair/hood secondary
#     motion berbasis kecepatan (velocity-driven lag).
extends RefCounted

const PoseScript = preload("res://scenes/hero/sylara/SylaraPose.gd")
const RIG = preload("res://scenes/hero/sylara/SylaraRenderer.gd")

# ── Timeline serangan ranged (fraksi 0..1) ──
const ATK_DRAW_START := 0.08     # anticipation selesai, mulai tarik tali
const ATK_DRAW_END := 0.46       # full draw (tegangan maksimum)
const ATK_RELEASE := 0.52        # IMPACT — lepas tali busur
const ATK_FOLLOW_END := 0.74     # akhir follow-through

# ── Timeline sapuan melee (riposte dekat < SWING_RANGE) ──
const SWING_WINDUP_END := 0.22
const SWING_STRIKE_END := 0.55
const SWING_ARC_START := -1.24   # rad (bawaan dari pose idle)
const SWING_ARC_MID := -0.26
const SWING_ARC_END := 0.86      # overshoot ke depan-bawah

# Durasi skill (detik) — sinkron VISUAL_DURATION HeroSkillKit ("sylara"):
# q=180f, w=180f, e=150f, r=60f.
const SKILL_DUR: Dictionary = {"q": 3.0, "w": 3.0, "e": 2.5, "r": 1.0}

## Mata: jadwal kedip acak mandiri (wajah hidup).
var _blink_cd := 2.5
var _blink_t := -1.0
## Fase cloth (kapas/rambut/hood) — maju di tick().
var _cloth_phase := 0.0
var _cloth_speed := 1.0


# ══════════════════════════════════════════════════════════
#  MATH
# ══════════════════════════════════════════════════════════

static func ss(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


static func ease_in_cubic(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * t


static func ease_out_cubic(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	var u: float = 1.0 - t
	return 1.0 - u * u * u


## Overshoot lembut — puncak sapuan/release terasa "melebihi target".
static func ease_out_back(t: float, s: float = 1.7) -> float:
	t = clampf(t, 0.0, 1.0)
	var u: float = t - 1.0
	return 1.0 + u * u * ((s + 1.0) * u + s)


## 2-bone IK: hip=(0,0), panjang l1/l2 → posisi knee. bend=-1 = lutut depan.
static func _ik2(foot: Vector2, l1: float, l2: float, bend: float) -> Vector2:
	var d: Vector2 = foot
	var dist := clampf(d.length(), absf(l1 - l2) + 0.05, l1 + l2 - 0.05)
	var dn: Vector2 = d / maxf(0.001, dist)
	var a: float = (l1 * l1 - l2 * l2 + dist * dist) / (2.0 * dist)
	var h := sqrt(maxf(0.0, l1 * l1 - a * a))
	var mid: Vector2 = dn * a
	var perp: Vector2 = Vector2(-dn.y, dn.x)
	return mid + perp * h * bend


## Sudut basis _down: 0 = lurus bawah, + = ke depan (+x).
static func _ang(v: Vector2) -> float:
	return atan2(v.x, v.y)


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


# ══════════════════════════════════════════════════════════
#  SOLVER KAKI — telapak menapak, tidak slide
# ══════════════════════════════════════════════════════════

## Setel satu kaki dari target ankle (ruang pinggul: hip=(0,0)).
func _solve_leg(p: SylaraPose, foot_rel: Vector2, foot_ang: float,
		front: bool) -> void:
	var hip_off: Vector2 = Vector2(3.5, 2.0) if front else Vector2(-3.5, 2.5)
	var ankle: Vector2 = foot_rel - hip_off
	var knee: Vector2 = _ik2(ankle, RIG.LEG_UPPER, RIG.LEG_LOWER, -1.0)
	var a_hip := _ang(knee)
	var a_knee := _ang(ankle - knee) - a_hip
	if front:
		p.leg_f_hip = a_hip
		p.leg_f_knee = a_knee
		p.leg_f_foot = foot_ang
	else:
		p.leg_b_hip = a_hip
		p.leg_b_knee = a_knee
		p.leg_b_foot = foot_ang


## Satu kaki gait: `theta` fase siklus. Menapak di x>0 → x<0, swing
## (terangkat) kembali x<0 → x>0.
func _gait_foot(p: SylaraPose, theta: float, stride: float, lift: float,
		front: bool) -> void:
	var u: float = fmod(theta, TAU)
	var fx: float = cos(theta) * stride
	var swing := 0.0
	if u > PI:
		swing = -sin(u)          # 0 → 1 → 0 (mid-swing = terangkat penuh)
	var plant_y: float = 24.0 - p.root_y
	var foot_ang: float = lerpf(0.06, -0.45, swing)
	_solve_leg(p, Vector2(fx, plant_y - swing * lift), foot_ang, front)


## Sikap statis (attack/skill): dua kaki menapak, separasi & crouch.
func _stance(p: SylaraPose, front_x: float, back_x: float, crouch: float) -> void:
	var plant_y: float = 24.0 - p.root_y - crouch * 2.4
	_solve_leg(p, Vector2(front_x, plant_y), 0.05, true)
	_solve_leg(p, Vector2(back_x, plant_y), 0.05, false)


## Debu kontak: puncak saat telapak menapak (2x per siklus gait).
static func _dust(u: float, strength: float) -> float:
	return pow(absf(cos(u)), 9.0) * strength


# ══════════════════════════════════════════════════════════
#  COMPUTE — state → pose target
# ══════════════════════════════════════════════════════════

## Dipanggil root tiap physics frame. `extra`: t (override), aim (rad),
## speed01 (0..1, kecepatan hero).
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
			_attack(p, attack_progress, phase, float(extra.get("aim", 0.0)))
		"swing":
			_swing(p, attack_progress)
		"skill_q":
			_skill_q(p, attack_progress, skill_t)
		"skill_w":
			_skill_w(p, attack_progress, phase, skill_t)
		"skill_e":
			_skill_e(p, attack_progress, skill_t)
		"skill_r":
			_skill_r(p, attack_progress, skill_t)
		"hurt":
			_hurt(p, float(extra.get("t", 0.0)))
		"death":
			_death(p, float(extra.get("t", 0.0)))
		"victory":
			_victory(p, phase)
		_:
			_idle(p, phase)

	_cloth(p, state, extra)
	return p


# ══════════════════════════════════════════════════════════
#  1. IDLE — stance siaga ranger (napas + geser berat + pandang)
# ══════════════════════════════════════════════════════════

func _idle(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.0
	var breath := sin(phase * 2.4)
	var weight := sin(phase * 0.7 + 1.2) * 0.5

	p.root_y = breath * 0.6
	p.root_x = weight * 0.5
	p.torso_lean = breath * 0.022
	p.chest_flex = breath * 0.045
	p.head_lean = sin(phase * 0.9 + 0.4) * 0.03
	p.look = sin(phase * 0.53 + 2.0)

	# Lengan depan memegang busur siaga (stabil, tidak bergoyang)
	p.arm_f_sh = 0.35 + breath * 0.015
	p.arm_f_el = 0.62
	# Lengan belakang rileks
	p.arm_b_sh = -0.08 + sin(phase * 2.2 + 1.0) * 0.018
	p.arm_b_el = 0.45

	# Kaki: archer stance menapak (tanpa slide)
	_stance(p, 4.2 + weight * 0.8, -4.6 - weight * 0.8, 0.0)

	# Busur diagonal rendah
	p.bow_angle = -0.45 + sin(phase * 1.6) * 0.03
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  2. WALK — gait solver; lengan busur stabil
# ══════════════════════════════════════════════════════════

func _walk(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.5
	var cycle := phase * 4.6
	var s := sin(cycle)
	var c := cos(cycle)

	p.root_y = absf(s) * 1.6 - 0.4
	p.root_x = s * 0.7
	p.torso_lean = s * 0.045
	p.chest_flex = 0.02
	p.head_lean = -s * 0.03

	# Lengan busur: koreksi kecil (senjata tetap di bidik)
	p.arm_f_sh = 0.30 - s * 0.05
	p.arm_f_el = 0.60 + absf(s) * 0.05
	# Lengan belakang mengayun natural
	p.arm_b_sh = -0.06 + s * 0.16
	p.arm_b_el = 0.42 + absf(c) * 0.10

	p.bow_angle = -0.40 + s * 0.05
	p.bow_draw = 0.0

	_gait_foot(p, cycle, 6.5, 3.2, true)
	_gait_foot(p, cycle + PI, 6.5, 3.2, false)
	p.dust = _dust(fmod(cycle, TAU), 0.55)


# ══════════════════════════════════════════════════════════
#  3. RUN — langkah panjang + float antar-langkah
# ══════════════════════════════════════════════════════════

func _run(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 2.3
	var cycle := phase * 7.2
	var s := sin(cycle)
	var c := cos(cycle)

	# Bob lari: rendah saat menapak, melayang di mid-cycle
	p.root_y = -absf(s) * 2.8 + 1.0
	p.root_x = s * 1.8
	p.torso_lean = 0.15 + s * 0.06
	p.chest_flex = 0.05
	p.head_lean = -0.05

	# Busur dijulur siaga (stabil), lengan belakang mengayun kuat
	p.arm_f_sh = 0.58 + s * 0.06
	p.arm_f_el = 0.70
	p.arm_b_sh = -0.32 + s * 0.30
	p.arm_b_el = 0.70 + absf(c) * 0.22

	p.bow_angle = -0.22 + s * 0.08
	p.bow_draw = 0.0

	_gait_foot(p, cycle, 9.5, 5.5, true)
	_gait_foot(p, cycle + PI, 9.5, 5.5, false)
	p.dust = _dust(fmod(cycle, TAU), 0.7)


# ══════════════════════════════════════════════════════════
#  4. ATTACK (ranged) — tarik penuh, lepaskan di IMPACT 0.52
# ══════════════════════════════════════════════════════════

func _attack(p: SylaraPose, ap: float, phase: float, aim: float) -> void:
	_cloth_speed = 1.9
	var aim_clamped := clampf(aim, -0.45, 0.45)

	if ap < ATK_DRAW_START:
		# ANTICIPATION: angkat busur, condong belakang siapkan tarikan
		var t := ss(ap / ATK_DRAW_START)
		p.torso_lean = lerpf(0.0, -0.07, t)
		p.arm_f_sh = lerpf(0.35, 0.88, t)
		p.arm_f_el = lerpf(0.62, 0.20, t)
		p.arm_b_sh = lerpf(-0.08, -0.52, t)
		p.arm_b_el = lerpf(0.45, 1.15, t)
		p.bow_angle = lerpf(-0.45, aim_clamped, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.0, -1.6, t)
		p.head_lean = -t * 0.03
		_stance(p, 4.5, -5.0, t * 0.4)

	elif ap < ATK_DRAW_END:
		# DRAW: tarik tali ke belakang (tension building)
		var t := ss((ap - ATK_DRAW_START) / (ATK_DRAW_END - ATK_DRAW_START))
		p.torso_lean = lerpf(-0.07, -0.11, t)
		p.arm_f_sh = 0.88 + t * 0.06
		p.arm_f_el = lerpf(0.20, 0.10, t)     # lengan depan lurus membidik
		p.arm_b_sh = lerpf(-0.52, -0.88, t)    # siku belakang ditarik kuat
		p.arm_b_el = lerpf(1.15, 1.50, t)
		p.bow_angle = aim_clamped
		p.bow_draw = t                          # tali tertarik penuh
		p.root_x = lerpf(-1.6, -2.6, t)
		p.chest_flex = t * 0.05
		p.wind_glow = t * 0.4
		p.head_lean = -0.04
		_stance(p, 4.5, -5.2, 0.4 + t * 0.3)

	elif ap < ATK_RELEASE:
		# RELEASE (IMPACT): tali lepas, recoil maju, shiver
		var t := (ap - ATK_DRAW_END) / (ATK_RELEASE - ATK_DRAW_END)
		p.torso_lean = lerpf(-0.11, 0.05, t)
		p.arm_f_sh = 0.94
		p.arm_f_el = 0.08
		p.arm_b_sh = lerpf(-0.88, -0.28, t)
		p.arm_b_el = lerpf(1.50, 0.55, t)
		p.bow_angle = aim_clamped
		p.bow_draw = lerpf(1.0, 0.0, t * t)     # tali snap seketika
		p.shiver = 1.0 - t
		p.root_x = lerpf(-2.6, 1.2, t)
		p.chest_flex = lerpf(0.05, -0.02, t)
		p.wind_glow = 0.55
		p.trail = false
		_stance(p, 5.0, -4.6, 0.2)
		p.dust = 0.35 * (1.0 - t)

	else:
		# FOLLOW THROUGH & RECOVERY: kembali ke sikap siaga
		var t := ss((ap - ATK_RELEASE) / (1.0 - ATK_RELEASE))
		p.torso_lean = lerpf(0.05, 0.0, t)
		p.arm_f_sh = lerpf(0.94, 0.35, t)
		p.arm_f_el = lerpf(0.08, 0.62, t)
		p.arm_b_sh = lerpf(-0.28, -0.08, t)
		p.arm_b_el = lerpf(0.55, 0.45, t)
		p.bow_angle = lerpf(aim_clamped, -0.45, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(1.2, 0.0, t)
		p.chest_flex = lerpf(-0.02, 0.0, t)
		p.wind_glow = lerpf(0.5, 0.0, t)
		_stance(p, lerpf(5.0, 4.2, t), lerpf(-4.6, -4.6, t),
			lerpf(0.2, 0.0, t))


# ══════════════════════════════════════════════════════════
#  5. SWING (melee riposte) — busur berputar mengelilingi bahu,
#  angular shaping: ease-in windup, strike cepat + overshoot.
# ══════════════════════════════════════════════════════════

func _swing(p: SylaraPose, ap: float) -> void:
	_cloth_speed = 2.2

	if ap < SWING_WINDUP_END:
		var t := ease_in_cubic(ap / SWING_WINDUP_END)
		p.torso_lean = lerpf(0.0, -0.16, t)
		p.arm_f_sh = lerpf(0.35, -0.65, t)
		p.arm_f_el = lerpf(0.62, 0.95, t)
		p.bow_angle = lerpf(-0.45, SWING_ARC_START, t)
		p.root_x = lerpf(0.0, -2.2, t)
		p.bow_off = Vector2(0.0, 0.0)
	elif ap < SWING_STRIKE_END:
		var u: float = (ap - SWING_WINDUP_END) / (SWING_STRIKE_END - SWING_WINDUP_END)
		if u < 0.5:
			# Accelarasi menuju tengah busur (cepat)
			var t := ease_in_cubic(u / 0.5)
			p.bow_angle = lerpf(SWING_ARC_START, SWING_ARC_MID, t)
			p.arm_f_sh = lerpf(-0.65, 0.35, t)
		else:
			# Strike + overshoot (melampaui target lalu kembali)
			var t := ease_out_back((u - 0.5) / 0.5, 1.6)
			p.bow_angle = lerpf(SWING_ARC_MID, SWING_ARC_END, t)
			p.arm_f_sh = lerpf(0.35, 1.25, t)
		p.arm_f_el = lerpf(0.95, 0.28, u)
		p.torso_lean = lerpf(-0.16, 0.20, u)
		p.root_x = lerpf(-2.2, 3.2, u)
		p.chest_flex = u * 0.09
		p.trail = true
		# Pivot radius membesar saat strike (rasa bobot)
		p.bow_off = Vector2(lerpf(0.0, 8.0, u), -1.5)
	else:
		var t := ss((ap - SWING_STRIKE_END) / (1.0 - SWING_STRIKE_END))
		p.torso_lean = lerpf(0.20, 0.0, t)
		p.arm_f_sh = lerpf(1.25, 0.35, t)
		p.arm_f_el = lerpf(0.28, 0.62, t)
		p.bow_angle = lerpf(SWING_ARC_END, -0.45, t)
		p.root_x = lerpf(3.2, 0.0, t)
		p.chest_flex = lerpf(0.09, 0.0, t)
		p.bow_off = Vector2(lerpf(8.0, 0.0, t), 0.0)
		p.trail = t < 0.3

	p.arm_b_sh = -0.16
	p.arm_b_el = 0.52
	p.head_lean = -0.03
	# Sikap dinamis: kaki belakang condong ke belakang saat strike
	var stride: float = 5.5 if ap < SWING_STRIKE_END else 4.5
	_stance(p, stride, -stride - 1.0, 0.3)
	if ap < SWING_STRIKE_END and ap > SWING_WINDUP_END:
		p.dust = 0.5


# ══════════════════════════════════════════════════════════
#  6. SKILL Q — FOCUS FIRE: 5 volley cepat (3.0 dtk)
# ══════════════════════════════════════════════════════════

func _skill_q(p: SylaraPose, prog: float, skill_t: float) -> void:
	_cloth_speed = 2.1
	if prog <= 0.0:
		prog = clampf(skill_t / float(SKILL_DUR["q"]), 0.0, 1.0)

	if prog < 0.08:
		var t := ss(prog / 0.08)
		p.arm_f_sh = lerpf(0.35, 1.0, t)
		p.arm_f_el = lerpf(0.62, 0.16, t)
		p.bow_angle = lerpf(-0.45, 0.10, t)
		p.torso_lean = lerpf(0.0, -0.09, t)
		_stance(p, 4.5, -5.0, 0.3)
	elif prog < 0.88:
		var volley_t: float = (prog - 0.08) / 0.80
		var cyc5: float = fmod(volley_t * 5.0, 1.0)
		var draw_t: float = pow(absf(1.0 - 2.0 * cyc5), 0.75)
		p.arm_f_sh = 0.90 + draw_t * 0.10
		p.arm_f_el = 0.16 + (1.0 - draw_t) * 0.14
		p.arm_b_sh = -0.50 - draw_t * 0.40
		p.arm_b_el = 0.85 + draw_t * 0.60
		p.bow_angle = 0.10 + sin(volley_t * TAU * 5.0 + 0.5) * 0.05
		p.bow_draw = draw_t
		p.torso_lean = -0.09 + sin(volley_t * TAU * 5.0) * 0.035
		p.root_x = -2.0 + sin(volley_t * TAU * 5.0) * 0.8
		p.wind_glow = 0.45 + draw_t * 0.45
		_stance(p, 4.5, -5.0, 0.3)
	else:
		var t := ss((prog - 0.88) / 0.12)
		p.arm_f_sh = lerpf(0.96, 0.35, t)
		p.arm_f_el = lerpf(0.18, 0.62, t)
		p.arm_b_sh = lerpf(-0.72, -0.08, t)
		p.arm_b_el = lerpf(1.22, 0.45, t)
		p.bow_angle = lerpf(0.10, -0.45, t)
		p.bow_draw = lerpf(0.4, 0.0, t)
		p.torso_lean = lerpf(-0.07, 0.0, t)
		p.wind_glow = lerpf(0.6, 0.0, t)
		p.root_x = lerpf(-1.6, 0.0, t)
		_stance(p, lerpf(4.5, 4.2, t), -4.6, 0.2)


# ══════════════════════════════════════════════════════════
#  7. SKILL W — WINDRUN: sprint wind 3.0 dtk (low crouch + gait cepat)
# ══════════════════════════════════════════════════════════

func _skill_w(p: SylaraPose, prog: float, phase: float, skill_t: float) -> void:
	_cloth_speed = 3.0
	if prog <= 0.0:
		prog = clampf(skill_t / float(SKILL_DUR["w"]), 0.0, 1.0)

	if prog < 0.10:
		var t := ss(prog / 0.10)
		p.root_y = lerpf(0.0, -3.2, t)
		p.torso_lean = lerpf(0.0, -0.07, t)
		p.arm_f_sh = lerpf(0.35, 0.66, t)
		p.arm_f_el = lerpf(0.62, 0.30, t)
		p.arm_b_sh = lerpf(-0.08, -0.55, t)
		p.arm_b_el = lerpf(0.45, 0.30, t)
		p.bow_angle = lerpf(-0.45, 0.30, t)
		p.wind_glow = t * 0.75
		p.cape_flare = lerpf(0.5, 1.0, t)
		_stance(p, 5.0, -5.0, t * 0.8)
	elif prog < 0.88:
		var run_c := phase * 8.4
		var s := sin(run_c)
		p.root_y = -3.2 + absf(s) * 2.4
		p.root_x = s * 1.4
		p.torso_lean = 0.10 + s * 0.05
		p.chest_flex = 0.04
		p.head_lean = -0.05
		p.arm_f_sh = 0.60 + s * 0.08
		p.arm_f_el = 0.36
		p.arm_b_sh = -0.40 + s * 0.16
		p.arm_b_el = 0.46
		p.bow_angle = -0.10 + s * 0.06
		p.cape_flare = 1.0
		p.wind_glow = 0.65 + sin(skill_t * 5.2) * 0.22
		_gait_foot(p, run_c, 7.5, 4.4, true)
		_gait_foot(p, run_c + PI, 7.5, 4.4, false)
		p.dust = _dust(fmod(run_c, TAU), 0.8)
	else:
		var t := ss((prog - 0.88) / 0.12)
		p.root_y = lerpf(-3.2, 0.0, t)
		p.torso_lean = lerpf(0.10, 0.0, t)
		p.arm_f_sh = lerpf(0.60, 0.35, t)
		p.arm_f_el = lerpf(0.36, 0.62, t)
		p.arm_b_sh = lerpf(-0.40, -0.08, t)
		p.arm_b_el = lerpf(0.46, 0.45, t)
		p.bow_angle = lerpf(-0.10, -0.45, t)
		p.cape_flare = lerpf(1.0, 0.5, t)
		p.wind_glow = lerpf(0.55, 0.0, t)
		_stance(p, lerpf(5.0, 4.2, t), -4.6, 0.2)


# ══════════════════════════════════════════════════════════
#  8. SKILL E — SHACKLE SHOT: aim presisi + tarikan lambat (2.5 dtk)
# ══════════════════════════════════════════════════════════

func _skill_e(p: SylaraPose, prog: float, skill_t: float) -> void:
	_cloth_speed = 1.7
	if prog <= 0.0:
		prog = clampf(skill_t / float(SKILL_DUR["e"]), 0.0, 1.0)

	if prog < 0.30:
		# PRE CAST: bidik presisi, tarik tali lambat penuh
		var t := ss(prog / 0.30)
		p.arm_f_sh = lerpf(0.35, 1.02, t)
		p.arm_f_el = lerpf(0.62, 0.14, t)
		p.arm_b_sh = lerpf(-0.08, -0.92, t)
		p.arm_b_el = lerpf(0.45, 1.52, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t * 0.9
		p.torso_lean = lerpf(0.0, -0.13, t)
		p.root_x = lerpf(0.0, -2.1, t)
		p.head_lean = -0.07
		_stance(p, 4.5, -5.2, 0.3 + t * 0.2)
	elif prog < 0.42:
		# CAST: lepas sulur (snap + shiver)
		var t := ss((prog - 0.30) / 0.12)
		p.arm_f_sh = 1.02
		p.arm_f_el = 0.12
		p.arm_b_sh = lerpf(-0.92, -0.22, t)
		p.arm_b_el = lerpf(1.52, 0.52, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(0.9, 0.0, t * t)
		p.shiver = 1.0 - t
		p.torso_lean = lerpf(-0.13, 0.07, t)
		p.root_x = lerpf(-2.1, 1.6, t)
		p.wind_glow = lerpf(0.0, 0.55, t)
		p.dust = 0.4 * (1.0 - t)
		_stance(p, 5.0, -4.6, 0.2)
	else:
		# HOLD: sulur mengikat target — badan tenang, napas halus
		var hold_t: float = (prog - 0.42) / 0.58
		var br := sin(hold_t * TAU * 1.2) * 0.02
		p.arm_f_sh = 0.88 + br
		p.arm_f_el = 0.18
		p.arm_b_sh = -0.22
		p.arm_b_el = 0.52
		p.bow_angle = 0.05
		p.torso_lean = 0.04 + br
		p.head_lean = -0.04
		p.wind_glow = 0.38 + sin(hold_t * TAU * 2.0) * 0.12
		p.root_x = lerpf(1.6, 0.8, ss(hold_t))
		_stance(p, 4.6, -4.8, 0.2)


# ══════════════════════════════════════════════════════════
#  9. SKILL R — POWERSHOT: charge crouch 1.0 dtk → lunge release
#  (damage kit terjadi di akhir charge — visual release mengikutinya)
# ══════════════════════════════════════════════════════════

func _skill_r(p: SylaraPose, prog: float, skill_t: float) -> void:
	_cloth_speed = 2.6
	if prog <= 0.0:
		prog = clampf(skill_t / float(SKILL_DUR["r"]), 0.0, 1.0)

	if prog < 0.85:
		# CHARGE: kuda-kuda kokoh, tarik busur maksimal, getar naik
		var t := ss(prog / 0.85)
		p.arm_f_sh = lerpf(0.35, 1.08, t)
		p.arm_f_el = lerpf(0.62, 0.07, t)
		p.arm_b_sh = lerpf(-0.08, -1.05, t)
		p.arm_b_el = lerpf(0.45, 1.65, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t
		p.charge = t
		p.torso_lean = lerpf(0.0, -0.15, t)
		p.root_x = lerpf(0.0, -3.8, t)
		p.root_y = lerpf(0.0, -2.0, t)
		p.chest_flex = t * 0.07
		p.head_lean = -0.10
		p.wind_glow = t * 0.95
		_stance(p, 5.5, -5.8, 0.6 + t * 0.4)
	else:
		# RELEASE: snap + lunge (damage kit fire di t≈1.0)
		var t := clampf((prog - 0.85) / 0.15, 0.0, 1.0)
		p.arm_f_sh = 1.08
		p.arm_f_el = 0.06
		p.arm_b_sh = lerpf(-1.05, -0.10, t)
		p.arm_b_el = lerpf(1.65, 0.38, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(1.0, 0.0, t * t)
		p.charge = 0.0
		p.shiver = 1.0
		p.trail = true
		p.torso_lean = lerpf(-0.15, 0.14, t)
		p.root_x = lerpf(-3.8, 4.2, t)
		p.root_y = lerpf(-2.0, 0.4, t)
		p.chest_flex = lerpf(0.07, -0.04, t)
		p.wind_glow = 1.0
		p.dust = 0.9 * (1.0 - t)
		_stance(p, 6.0, -5.0, 0.2)


# ══════════════════════════════════════════════════════════
#  10. HURT — recoil + flinch
# ══════════════════════════════════════════════════════════

func _hurt(p: SylaraPose, t: float) -> void:
	_cloth_speed = 1.6
	var recoil := sin(t * PI)
	p.root_x = -recoil * 3.4
	p.root_y = -recoil * 1.4
	p.torso_lean = -recoil * 0.24
	p.head_lean = -recoil * 0.18
	p.arm_f_sh = 0.35 + recoil * 0.30
	p.arm_f_el = 0.62 + recoil * 0.25
	p.arm_b_sh = -0.08 - recoil * 0.30
	p.arm_b_el = 0.45 + recoil * 0.25
	p.bow_angle = -0.45 - recoil * 0.32
	p.shiver = recoil * 0.6
	p.hurt_tint = recoil
	_stance(p, 4.2 + recoil * 0.6, -5.2 - recoil * 0.6, 0.1)


# ══════════════════════════════════════════════════════════
#  11. DEATH — stagger fall + bow drop + alpha dissolve
# ══════════════════════════════════════════════════════════

func _death(p: SylaraPose, t: float) -> void:
	_cloth_speed = 0.45
	var fall := ss(minf(t * 1.6, 1.0))
	var settle := ss(clampf((t - 0.55) / 0.45, 0.0, 1.0))

	p.root_y = fall * 20.0
	p.root_x = -fall * 5.5
	p.torso_lean = -fall * 0.85 + settle * 0.18
	p.chest_flex = -fall * 0.35
	p.head_lean = -fall * 0.55
	p.arm_f_sh = -fall * 0.68
	p.arm_f_el = fall * 0.85
	p.arm_b_sh = -fall * 0.85
	p.arm_b_el = fall * 0.65
	# Busur terlepas jatuh
	p.bow_angle = -0.45 - fall * 1.35
	p.bow_off = Vector2(fall * 2.0, fall * 4.0)
	p.leg_f_hip = fall * 0.5
	p.leg_f_knee = -fall * 0.55
	p.leg_f_foot = 0.1
	p.leg_b_hip = -fall * 0.25
	p.leg_b_knee = -fall * 0.35
	p.leg_b_foot = 0.1
	# Mata tertutup + pandangan berhenti (wajah rileks)
	p.eye_blink = 1.0
	p.look = 0.0
	p.alpha = lerpf(1.0, 0.25, ss(clampf((t - 0.6) / 0.4, 0.0, 1.0)))


# ══════════════════════════════════════════════════════════
#  12. VICTORY — angkat busur kemenangan
# ══════════════════════════════════════════════════════════

func _victory(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.3
	var wave := sin(phase * 2.2)

	p.root_y = -2.4 + wave * 1.2
	p.torso_lean = -0.06 + wave * 0.03
	p.head_lean = -0.14 + wave * 0.03
	p.arm_f_sh = 2.35 + wave * 0.08
	p.arm_f_el = 0.15
	p.arm_b_sh = -0.32 + wave * 0.06
	p.arm_b_el = 0.42
	p.bow_angle = 1.50 + wave * 0.06
	p.cape_flare = 0.8 + wave * 0.2
	p.wind_glow = 0.35 + wave * 0.15
	_stance(p, 4.5, -4.8, 0.1)


# ══════════════════════════════════════════════════════════
#  13. SECONDARY MOTION — cape/hood/hair (velocity-driven lag)
# ══════════════════════════════════════════════════════════

func _cloth(p: SylaraPose, state: String, extra: Dictionary) -> void:
	var cp := _cloth_phase
	var speed01: float = clampf(float(extra.get("speed01", 0.0)), 0.0, 1.0)
	var lag: float = speed01 * 0.55

	# 3 segmen cape (tertinggal di belakang + flare dari kecepatan)
	var cape_base: float = PI + 0.10 + lag
	for i in 3:
		var seg_speed: float = 0.12 + float(i) * 0.08 + speed01 * 0.18
		var wave: float = sin(cp + float(i) * 0.72) * seg_speed
		p.cape[i] = cape_base + wave + float(i) * 0.06

	# 2 segmen hood cowl
	for i in 2:
		var wave: float = sin(cp * 0.82 + float(i) * 0.92) * 0.08
		p.hood[i] = PI + wave + lag * 0.5

	# 3 segmen rambut oranye (lebih ringan cape — lebih cepat)
	for i in 3:
		var seg_speed: float = 0.10 + float(i) * 0.07 + speed01 * 0.2
		var wave: float = sin(cp * 1.12 + float(i) * 0.62 + 1.2) * seg_speed
		p.hair[i] = PI + 0.15 + wave + float(i) * 0.05 + lag * 0.8

	# Flare ekstra per-state
	if state in ["run", "skill_w"]:
		for i in 3:
			p.cape[i] += 0.24 + float(i) * 0.09
			p.hair[i] += 0.16 + float(i) * 0.06
	elif state == "skill_r" or p.trail:
		for i in 3:
			p.cape[i] += 0.15
			p.hair[i] += 0.09
	if state == "death":
		# Kain ikut roboh
		for i in 3:
			p.cape[i] = lerp_angle(p.cape[i], PI + 0.9, 0.55)
			p.hair[i] = lerp_angle(p.hair[i], PI + 0.7, 0.45)
