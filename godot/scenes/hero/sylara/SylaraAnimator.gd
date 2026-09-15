# SylaraAnimator.gd — state machine animasi prosedural Sylara (Godot 4.x).
#
# Tanggung jawab SATU hal: (state, fase, progress) → SylaraPose target.
# Tidak menyentuh node, tidak menggambar, tidak spawn FX — itu urusan
# SylaraRenderer / SylaraSkillFX.
#
# Setiap state mengikuti hukum game-feel:
#   ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY
# dan secondary motion (cape, hood, hair) dihitung sebagai fungsi
# fase + "stream factor" supaya kain bereaksi terhadap kecepatan gerak.
#
# Sylara adalah RANGED ARCHER: animasi serangan utama = draw & release
# busur, dengan sapuan melee sebagai riposte jarak dekat.
extends RefCounted

const PoseScript = preload("res://scenes/hero/sylara/SylaraPose.gd")

# ── Timing serangan ranged (draw & release) ──
const ATK_DRAW_START := 0.08     # anticipation selesai, mulai tarik
const ATK_DRAW_END := 0.48       # tali full drawn
const ATK_RELEASE := 0.52        # IMPACT — lepas tali
const ATK_FOLLOW_END := 0.72     # follow through
# Timing serangan melee (sapuan busur)
const SWING_WINDUP_END := 0.22
const SWING_STRIKE_END := 0.55
const SWING_HOLD_END := 0.68

# Blink: jadwal kedip mandiri supaya wajah hidup.
var _blink_cd := 2.3
var _blink_t := -1.0

# Kain (cape/hood/hair): fase diakumulasi di tick() dengan laju variabel.
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


## Dipanggil root tiap frame (delta asli).
func tick(delta: float) -> void:
	_cloth_phase += delta * 6.0 * _cloth_speed
	if _blink_t >= 0.0:
		_blink_t += delta
		if _blink_t > 0.17:
			_blink_t = -1.0
			_blink_cd = randf_range(1.9, 3.8)
	else:
		_blink_cd -= delta
		if _blink_cd <= 0.0:
			_blink_t = 0.0


func _blink_amount() -> float:
	if _blink_t < 0.0:
		return 0.0
	return sin(clampf(_blink_t / 0.17, 0.0, 1.0) * PI)


## Hitung pose target.
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
	# Secondary motion — kain bereaksi terhadap state.
	_cloth(p, state, phase)
	return p


# ══════════════════════════════════════════════════════════
#  IDLE
# ══════════════════════════════════════════════════════════

func _idle(p: Object, phase: float) -> void:
	_cloth_speed = 1.0
	var breath := sin(phase * 2.4) * 0.018
	p.root_y = sin(phase * 2.4) * 0.6
	p.torso_lean = breath
	p.chest_flex = breath * 0.5
	p.head_lean = sin(phase * 1.8 + 0.4) * 0.025
	# Lengan depan memegang busur santai — sedikit ke depan-bawah.
	p.arm_f_sh = 0.35 + sin(phase * 2.0) * 0.02
	p.arm_f_el = 0.65
	# Lengan belakang rileks di sisi.
	p.arm_b_sh = -0.08 + sin(phase * 2.2 + 1.0) * 0.02
	p.arm_b_el = 0.45
	# Kaki sedikit terbuka — stance archer.
	p.leg_f_hip = 0.06
	p.leg_f_knee = -0.04
	p.leg_b_hip = -0.08
	p.leg_b_knee = -0.03
	# Busur dipegang rendah, sedikit miring ke depan.
	p.bow_angle = -0.45 + sin(phase * 1.6) * 0.03
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  WALK
# ══════════════════════════════════════════════════════════

func _walk(p: Object, phase: float) -> void:
	_cloth_speed = 1.4
	var cycle := phase * 4.5
	var s := sin(cycle)
	var c := cos(cycle)
	p.root_y = abs(s) * 1.8 - 0.5
	p.root_x = s * 0.8
	p.torso_lean = s * 0.04
	p.chest_flex = 0.02
	p.head_lean = -s * 0.02
	# Kaki berjalan — siklus standar.
	p.leg_f_hip = s * 0.35
	p.leg_f_knee = -abs(s) * 0.35 - 0.05
	p.leg_b_hip = -s * 0.35
	p.leg_b_knee = -abs(c) * 0.35 - 0.05
	p.leg_f_foot = 0.1 + s * 0.08
	p.leg_b_foot = 0.1 - s * 0.08
	# Lengan berayun berlawanan kaki.
	p.arm_f_sh = 0.3 - s * 0.12
	p.arm_f_el = 0.55 + abs(s) * 0.1
	p.arm_b_sh = -0.05 + s * 0.12
	p.arm_b_el = 0.4 + abs(c) * 0.1
	# Busur diayun sedikit mengikuti langkah.
	p.bow_angle = -0.4 + s * 0.06
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════

func _run(p: Object, phase: float) -> void:
	_cloth_speed = 2.2
	var cycle := phase * 7.0
	var s := sin(cycle)
	var c := cos(cycle)
	p.root_y = abs(s) * 3.2 - 1.2
	p.root_x = s * 1.8
	p.torso_lean = 0.12 + s * 0.06    # condong ke depan
	p.chest_flex = 0.05
	p.head_lean = -0.04
	# Kaki berlari — amplitudo besar, cepat.
	p.leg_f_hip = s * 0.55
	p.leg_f_knee = -abs(s) * 0.65 - 0.1
	p.leg_b_hip = -s * 0.55
	p.leg_b_knee = -abs(c) * 0.65 - 0.1
	p.leg_f_foot = 0.15 + s * 0.12
	p.leg_b_foot = 0.15 - s * 0.12
	# Lengan — depan pegang busur stabil, belakang pompa.
	p.arm_f_sh = 0.55 + s * 0.08
	p.arm_f_el = 0.7
	p.arm_b_sh = -0.3 + s * 0.25
	p.arm_b_el = 0.7 + abs(c) * 0.2
	# Busur lebih horizontal saat lari.
	p.bow_angle = -0.2 + s * 0.08
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  ATTACK (ranged — draw & release)
# ══════════════════════════════════════════════════════════

func _attack(p: Object, ap: float, phase: float) -> void:
	_cloth_speed = 1.8
	if ap < ATK_DRAW_START:
		# ANTICIPATION: angkat busur, condong sedikit ke belakang.
		var t := ss(ap / ATK_DRAW_START)
		p.torso_lean = lerpf(0.0, -0.06, t)
		p.arm_f_sh = lerpf(0.35, 0.85, t)
		p.arm_f_el = lerpf(0.65, 0.25, t)
		p.arm_b_sh = lerpf(-0.08, -0.5, t)
		p.arm_b_el = lerpf(0.45, 1.1, t)
		p.bow_angle = lerpf(-0.45, 0.1, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.0, -1.5, t)
	elif ap < ATK_DRAW_END:
		# DRAW: tarik tali — tension building.
		var t := ss((ap - ATK_DRAW_START) / (ATK_DRAW_END - ATK_DRAW_START))
		p.torso_lean = lerpf(-0.06, -0.1, t)
		p.arm_f_sh = 0.85 + t * 0.05
		p.arm_f_el = lerpf(0.25, 0.15, t)    # lengan depan lurus
		p.arm_b_sh = lerpf(-0.5, -0.85, t)    # tarik ke belakang
		p.arm_b_el = lerpf(1.1, 1.45, t)
		p.bow_angle = lerpf(0.1, 0.05, t)
		p.bow_draw = t                        # tali tertarik bertahap
		p.root_x = lerpf(-1.5, -2.5, t)
		p.chest_flex = t * 0.04
	elif ap < ATK_RELEASE:
		# RELEASE — IMPACT frame: tali lepas, recoil kecil.
		var t := (ap - ATK_DRAW_END) / (ATK_RELEASE - ATK_DRAW_END)
		p.torso_lean = lerpf(-0.1, 0.04, t)
		p.arm_f_sh = 0.9
		p.arm_f_el = 0.12
		p.arm_b_sh = lerpf(-0.85, -0.3, t)    # tangan tarik lepas
		p.arm_b_el = lerpf(1.45, 0.6, t)
		p.bow_angle = 0.05
		p.bow_draw = lerpf(1.0, 0.0, t * t)   # tali snap kembali
		p.root_x = lerpf(-2.5, 1.0, t)
		p.chest_flex = lerpf(0.04, -0.02, t)
		p.trail = t < 0.5
	else:
		# FOLLOW + RECOVERY: kembali ke idle.
		var t := ss((ap - ATK_RELEASE) / (1.0 - ATK_RELEASE))
		p.torso_lean = lerpf(0.04, 0.0, t)
		p.arm_f_sh = lerpf(0.9, 0.35, t)
		p.arm_f_el = lerpf(0.12, 0.65, t)
		p.arm_b_sh = lerpf(-0.3, -0.08, t)
		p.arm_b_el = lerpf(0.6, 0.45, t)
		p.bow_angle = lerpf(0.05, -0.45, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(1.0, 0.0, t)
		p.chest_flex = lerpf(-0.02, 0.0, t)
	# Kaki stance archer — sedikit spread, stabil.
	p.leg_f_hip = 0.15 + sin(phase * 0.5) * 0.02
	p.leg_f_knee = -0.08
	p.leg_b_hip = -0.18
	p.leg_b_knee = -0.06


# ══════════════════════════════════════════════════════════
#  SWING (melee riposte — sapuan busur jarak dekat)
# ══════════════════════════════════════════════════════════

func _swing(p: Object, ap: float, phase: float) -> void:
	_cloth_speed = 2.0
	if ap < SWING_WINDUP_END:
		# ANTICIPATION: busur ditarik ke belakang.
		var t := ss(ap / SWING_WINDUP_END)
		p.torso_lean = lerpf(0.0, -0.15, t)
		p.arm_f_sh = lerpf(0.35, -0.6, t)
		p.arm_f_el = lerpf(0.65, 0.9, t)
		p.bow_angle = lerpf(-0.45, 1.8, t)
		p.root_x = lerpf(0.0, -2.0, t)
	elif ap < SWING_STRIKE_END:
		# STRIKE: sapuan busur ke depan.
		var t := ss((ap - SWING_WINDUP_END) / (SWING_STRIKE_END - SWING_WINDUP_END))
		p.torso_lean = lerpf(-0.15, 0.18, t)
		p.arm_f_sh = lerpf(-0.6, 1.2, t)
		p.arm_f_el = lerpf(0.9, 0.3, t)
		p.bow_angle = lerpf(1.8, -1.2, t)
		p.root_x = lerpf(-2.0, 3.0, t)
		p.chest_flex = lerpf(0.0, 0.08, t)
		p.trail = true
	else:
		# FOLLOW + RECOVERY.
		var t := ss((ap - SWING_STRIKE_END) / (1.0 - SWING_STRIKE_END))
		p.torso_lean = lerpf(0.18, 0.0, t)
		p.arm_f_sh = lerpf(1.2, 0.35, t)
		p.arm_f_el = lerpf(0.3, 0.65, t)
		p.bow_angle = lerpf(-1.2, -0.45, t)
		p.root_x = lerpf(3.0, 0.0, t)
		p.chest_flex = lerpf(0.08, 0.0, t)
		p.trail = t < 0.3
	p.leg_f_hip = 0.2
	p.leg_f_knee = -0.1
	p.leg_b_hip = -0.22
	p.leg_b_knee = -0.08
	p.arm_b_sh = -0.15
	p.arm_b_el = 0.5


# ══════════════════════════════════════════════════════════
#  SKILL Q — FOCUS FIRE (rapid volley)
# ══════════════════════════════════════════════════════════

func _skill_q(p: Object, prog: float, phase: float) -> void:
	_cloth_speed = 2.0
	# Kipas pita angin dari nock, panah bertubi-tubi.
	if prog < 0.1:
		# Pre-cast: angkat busur tinggi.
		var t := ss(prog / 0.1)
		p.arm_f_sh = lerpf(0.35, 1.0, t)
		p.arm_f_el = lerpf(0.65, 0.2, t)
		p.bow_angle = lerpf(-0.45, 0.2, t)
		p.torso_lean = lerpf(0.0, -0.08, t)
	elif prog < 0.85:
		# Rapid fire: draw-release berulang, oscillating.
		var volley_t := (prog - 0.1) / 0.75
		var cycle := sin(volley_t * TAU * 4.0)  # 4 siklus draw
		var draw_t := (cycle + 1.0) * 0.5
		p.arm_f_sh = 0.9 + draw_t * 0.1
		p.arm_f_el = 0.15 + (1.0 - draw_t) * 0.15
		p.arm_b_sh = -0.5 - draw_t * 0.4
		p.arm_b_el = 0.8 + draw_t * 0.6
		p.bow_angle = 0.15 + sin(volley_t * TAU * 4.0 + 0.5) * 0.08
		p.bow_draw = draw_t
		p.torso_lean = -0.08 + cycle * 0.03
		p.root_x = -2.0 + cycle * 1.0
		p.wind_glow = 0.4 + draw_t * 0.4
	else:
		# Recovery.
		var t := ss((prog - 0.85) / 0.15)
		p.arm_f_sh = lerpf(0.95, 0.35, t)
		p.arm_f_el = lerpf(0.2, 0.65, t)
		p.arm_b_sh = lerpf(-0.7, -0.08, t)
		p.arm_b_el = lerpf(1.2, 0.45, t)
		p.bow_angle = lerpf(0.15, -0.45, t)
		p.bow_draw = lerpf(0.5, 0.0, t)
		p.torso_lean = lerpf(-0.06, 0.0, t)
		p.wind_glow = lerpf(0.6, 0.0, t)
		p.root_x = lerpf(-1.5, 0.0, t)
	p.leg_f_hip = 0.15
	p.leg_f_knee = -0.08
	p.leg_b_hip = -0.18
	p.leg_b_knee = -0.06


# ══════════════════════════════════════════════════════════
#  SKILL W — WINDRUN (speed aura + heal)
# ══════════════════════════════════════════════════════════

func _skill_w(p: Object, prog: float, phase: float, skill_t: float) -> void:
	_cloth_speed = 2.8
	# Ledakan daun melingkar, siklon daun, kecepatan bertambah.
	if prog < 0.12:
		# Charge: condong ke atas, tangan terbuka.
		var t := ss(prog / 0.12)
		p.root_y = lerpf(0.0, -3.0, t)
		p.torso_lean = lerpf(0.0, -0.06, t)
		p.arm_f_sh = lerpf(0.35, 0.7, t)
		p.arm_f_el = lerpf(0.65, 0.3, t)
		p.arm_b_sh = lerpf(-0.08, -0.6, t)
		p.arm_b_el = lerpf(0.45, 0.3, t)
		p.bow_angle = lerpf(-0.45, 0.3, t)
		p.wind_glow = t * 0.7
	elif prog < 0.85:
		# Active: berlari dengan aura, sedikit melayang.
		var run_c := phase * 7.0
		var s := sin(run_c)
		p.root_y = -3.0 + abs(s) * 2.0
		p.root_x = s * 1.2
		p.torso_lean = 0.08 + s * 0.04
		p.arm_f_sh = 0.6 + s * 0.08
		p.arm_f_el = 0.4
		p.arm_b_sh = -0.4 + s * 0.15
		p.arm_b_el = 0.5
		p.bow_angle = -0.1 + s * 0.06
		p.leg_f_hip = s * 0.5
		p.leg_f_knee = -abs(s) * 0.5 - 0.1
		p.leg_b_hip = -s * 0.5
		p.leg_b_knee = -abs(cos(run_c)) * 0.5 - 0.1
		p.wind_glow = 0.6 + sin(skill_t * 5.0) * 0.2
	else:
		# Fade out.
		var t := ss((prog - 0.85) / 0.15)
		p.root_y = lerpf(-3.0, 0.0, t)
		p.torso_lean = lerpf(0.08, 0.0, t)
		p.arm_f_sh = lerpf(0.6, 0.35, t)
		p.arm_f_el = lerpf(0.4, 0.65, t)
		p.arm_b_sh = lerpf(-0.4, -0.08, t)
		p.arm_b_el = lerpf(0.5, 0.45, t)
		p.bow_angle = lerpf(-0.1, -0.45, t)
		p.wind_glow = lerpf(0.5, 0.0, t)
		# Kaki kembali ke stance idle.
		p.leg_f_hip = lerpf(0.3, 0.06, t)
		p.leg_f_knee = lerpf(-0.3, -0.04, t)
		p.leg_b_hip = lerpf(-0.3, -0.08, t)
		p.leg_b_knee = lerpf(-0.3, -0.03, t)


# ══════════════════════════════════════════════════════════
#  SKILL E — SHACKLE SHOT (vine projectile)
# ══════════════════════════════════════════════════════════

func _skill_e(p: Object, prog: float, phase: float) -> void:
	_cloth_speed = 1.6
	if prog < 0.15:
		# Aim: tarik busur ke samping, membidik.
		var t := ss(prog / 0.15)
		p.arm_f_sh = lerpf(0.35, 1.0, t)
		p.arm_f_el = lerpf(0.65, 0.15, t)
		p.arm_b_sh = lerpf(-0.08, -0.9, t)
		p.arm_b_el = lerpf(0.45, 1.5, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t * 0.8
		p.torso_lean = lerpf(0.0, -0.12, t)
		p.root_x = lerpf(0.0, -2.0, t)
		p.head_lean = -0.06  # fokus membidik
	elif prog < 0.25:
		# Release: sulur melesat.
		var t := ss((prog - 0.15) / 0.1)
		p.arm_f_sh = 1.0
		p.arm_f_el = 0.12
		p.arm_b_sh = lerpf(-0.9, -0.2, t)
		p.arm_b_el = lerpf(1.5, 0.5, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(0.8, 0.0, t * t)
		p.torso_lean = lerpf(-0.12, 0.06, t)
		p.root_x = lerpf(-2.0, 1.5, t)
		p.wind_glow = lerpf(0.0, 0.5, t)
	elif prog < 0.75:
		# Sulur merambat — pose menahan.
		var t := (prog - 0.25) / 0.5
		p.arm_f_sh = 0.85
		p.arm_f_el = 0.2
		p.arm_b_sh = -0.2
		p.arm_b_el = 0.5
		p.bow_angle = 0.05
		p.bow_draw = 0.0
		p.torso_lean = 0.04
		p.wind_glow = 0.4 + sin(t * TAU * 2.0) * 0.15
	else:
		# Recovery.
		var t := ss((prog - 0.75) / 0.25)
		p.arm_f_sh = lerpf(0.85, 0.35, t)
		p.arm_f_el = lerpf(0.2, 0.65, t)
		p.arm_b_sh = lerpf(-0.2, -0.08, t)
		p.arm_b_el = lerpf(0.5, 0.45, t)
		p.bow_angle = lerpf(0.05, -0.45, t)
		p.torso_lean = lerpf(0.04, 0.0, t)
		p.wind_glow = lerpf(0.3, 0.0, t)
		p.root_x = lerpf(1.0, 0.0, t)
	p.leg_f_hip = 0.15
	p.leg_f_knee = -0.08
	p.leg_b_hip = -0.18
	p.leg_b_knee = -0.06


# ══════════════════════════════════════════════════════════
#  SKILL R — POWERSHOT (charged cone gale)
# ══════════════════════════════════════════════════════════

func _skill_r(p: Object, prog: float, phase: float, skill_t: float) -> void:
	_cloth_speed = 2.5
	if prog < 0.35:
		# CHARGE: tarik tali penuh, energi berkumpul.
		var t := ss(prog / 0.35)
		p.arm_f_sh = lerpf(0.35, 1.05, t)
		p.arm_f_el = lerpf(0.65, 0.08, t)
		p.arm_b_sh = lerpf(-0.08, -1.0, t)
		p.arm_b_el = lerpf(0.45, 1.6, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t
		p.torso_lean = lerpf(0.0, -0.14, t)
		p.root_x = lerpf(0.0, -3.5, t)
		p.root_y = lerpf(0.0, -1.5, t)
		p.chest_flex = t * 0.06
		p.wind_glow = t * 0.9
	elif prog < 0.45:
		# RELEASE: 5 panah gale melesat, recoil besar.
		var t := ss((prog - 0.35) / 0.1)
		p.arm_f_sh = 1.05
		p.arm_f_el = 0.06
		p.arm_b_sh = lerpf(-1.0, -0.1, t)
		p.arm_b_el = lerpf(1.6, 0.4, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(1.0, 0.0, t * t)
		p.torso_lean = lerpf(-0.14, 0.12, t)
		p.root_x = lerpf(-3.5, 4.0, t)
		p.root_y = lerpf(-1.5, 0.5, t)
		p.chest_flex = lerpf(0.06, -0.04, t)
		p.wind_glow = 1.0
		p.trail = true
	elif prog < 0.7:
		# Gale tunnel — pose follow through.
		var t := (prog - 0.45) / 0.25
		p.arm_f_sh = lerpf(1.05, 0.8, t)
		p.arm_f_el = lerpf(0.06, 0.25, t)
		p.arm_b_sh = -0.1
		p.arm_b_el = 0.4
		p.bow_angle = lerpf(0.0, 0.1, t)
		p.torso_lean = lerpf(0.12, 0.04, t)
		p.root_x = lerpf(4.0, 1.5, t)
		p.wind_glow = lerpf(1.0, 0.4, t)
		p.trail = t < 0.4
	else:
		# Recovery.
		var t := ss((prog - 0.7) / 0.3)
		p.arm_f_sh = lerpf(0.8, 0.35, t)
		p.arm_f_el = lerpf(0.25, 0.65, t)
		p.arm_b_sh = lerpf(-0.1, -0.08, t)
		p.arm_b_el = lerpf(0.4, 0.45, t)
		p.bow_angle = lerpf(0.1, -0.45, t)
		p.torso_lean = lerpf(0.04, 0.0, t)
		p.root_x = lerpf(1.5, 0.0, t)
		p.wind_glow = lerpf(0.3, 0.0, t)
	p.leg_f_hip = 0.2
	p.leg_f_knee = -0.1
	p.leg_b_hip = -0.22
	p.leg_b_knee = -0.08


# ══════════════════════════════════════════════════════════
#  HURT
# ══════════════════════════════════════════════════════════

func _hurt(p: Object, t: float, phase: float) -> void:
	_cloth_speed = 1.5
	var recoil := sin(t * PI)  # naik-turun cepat
	p.root_x = -recoil * 3.0
	p.root_y = -recoil * 1.5
	p.torso_lean = -recoil * 0.2
	p.head_lean = -recoil * 0.15
	p.arm_f_sh = 0.35 + recoil * 0.3
	p.arm_f_el = 0.65 + recoil * 0.2
	p.arm_b_sh = -0.08 - recoil * 0.3
	p.arm_b_el = 0.45 + recoil * 0.2
	p.bow_angle = -0.45 - recoil * 0.3
	p.hurt_tint = recoil * 0.8
	p.leg_f_hip = 0.06 + recoil * 0.1
	p.leg_b_hip = -0.08 - recoil * 0.1


# ══════════════════════════════════════════════════════════
#  DEATH
# ══════════════════════════════════════════════════════════

func _death(p: Object, t: float) -> void:
	_cloth_speed = 0.5
	var fall := ss(minf(t * 1.5, 1.0))
	p.root_y = fall * 18.0       # jatuh ke tanah
	p.root_x = -fall * 5.0       # mundur
	p.torso_lean = -fall * 0.8   # roboh ke belakang
	p.chest_flex = -fall * 0.3
	p.head_lean = -fall * 0.5
	p.arm_f_sh = -fall * 0.6
	p.arm_f_el = fall * 0.8
	p.arm_b_sh = -fall * 0.8
	p.arm_b_el = fall * 0.6
	p.bow_angle = -0.45 - fall * 1.2
	p.leg_f_hip = fall * 0.4
	p.leg_f_knee = -fall * 0.5
	p.leg_b_hip = -fall * 0.2
	p.leg_b_knee = -fall * 0.3
	p.alpha = lerpf(1.0, 0.3, ss(maxf(0.0, (t - 0.6) / 0.4)))


# ══════════════════════════════════════════════════════════
#  VICTORY
# ══════════════════════════════════════════════════════════

func _victory(p: Object, phase: float) -> void:
	_cloth_speed = 1.2
	var wave := sin(phase * 2.0)
	p.root_y = -2.0 + wave * 1.0
	p.torso_lean = -0.05 + wave * 0.03
	# Busur diangkat ke atas — pose kemenangan.
	p.arm_f_sh = 2.2 + wave * 0.1
	p.arm_f_el = 0.15
	p.arm_b_sh = -0.3 + wave * 0.05
	p.arm_b_el = 0.4
	p.bow_angle = 1.4 + wave * 0.08
	p.head_lean = -0.1 + wave * 0.03
	p.wind_glow = 0.3 + wave * 0.15
	p.leg_f_hip = 0.1
	p.leg_b_hip = -0.12


# ══════════════════════════════════════════════════════════
#  SECONDARY MOTION — cape, hood, hair
# ══════════════════════════════════════════════════════════

func _cloth(p: Object, state: String, phase: float) -> void:
	var cp := _cloth_phase
	# Cape: 3 segmen, makin ujung makin bebas.
	var cape_base := PI + 0.1  # dasar: ke belakang
	for i in 3:
		var seg_speed := 0.12 + float(i) * 0.08
		var wave := sin(cp + float(i) * 0.7) * seg_speed
		p.cape[i] = cape_base + wave + float(i) * 0.06
	# Hood: 2 segmen, lebih kaku.
	for i in 2:
		var wave := sin(cp * 0.8 + float(i) * 0.9) * 0.08
		p.hood[i] = PI + wave
	# Hair: 3 segmen, lebih panjang dari hood.
	for i in 3:
		var seg_speed := 0.1 + float(i) * 0.07
		var wave := sin(cp * 1.1 + float(i) * 0.6 + 1.2) * seg_speed
		p.hair[i] = PI + 0.15 + wave + float(i) * 0.05
	# Kibaran ekstra saat run/skill.
	if state in ["run", "skill_w"]:
		for i in 3:
			p.cape[i] += 0.2 + float(i) * 0.08
		for i in 3:
			p.hair[i] += 0.15 + float(i) * 0.06
	elif state in ["skill_r"] or p.trail:
		for i in 3:
			p.cape[i] += 0.12
		for i in 3:
			p.hair[i] += 0.08
