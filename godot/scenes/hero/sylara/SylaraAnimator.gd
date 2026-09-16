# SylaraAnimator.gd — state machine animasi prosedural Sylara (Godot 4.x).
#
# Tanggung jawab SATU hal: (state, fase, progress) → tulis SylaraPose target.
# Pose target ditulis ke instance PAKAI-ULANG (tanpa alokasi per frame).
#
# Mengikuti kaidah animasi dan game feel profesional:
#   ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY
#
# PENTING — sinkronisasi serangan dasar: Hero.try_attack() melepaskan
# proyektil / damage INSTAN di ap=0 (paritas pygame, tidak boleh digeser).
# Karena itu siklus attack/swing dirancang RELEASE-FIRST: ap 0.0 = momen
# tali dilepas / tebasan menghantam, lalu follow-through, recovery, dan
# anticipation+draw untuk tembakan BERIKUTNYA di ekor siklus. Hasilnya
# panah beterbangan tepat saat tali snap — bukan 0.3 detik sebelumnya.
#
# Secondary motion (cape 3 segmen, hood 2 segmen, hair 3 segmen, bow string,
# eye blinking) dihitung kontinu berbasis fase cloth dan kecepatan gerak.
class_name SylaraAnimator
extends RefCounted

# ── Siklus serangan ranged: RELEASE dulu (spawn instan di ap=0) ──
const ATK_RELEASE_END := 0.12    # tali snap + recoil kick
const ATK_FOLLOW_END := 0.40     # follow through → sikap siaga
const ATK_READY_END := 0.68      # siaga bernapas (breathing ready)
const ATK_ANTICIP_END := 0.86    # anticipation; draw 0.86–1.00

# ── Siklus melee riposte: STRIKE dulu (damage instan di ap=0) ──
const SWING_STRIKE_END := 0.30
const SWING_HOLD_END := 0.55
const SWING_RECOVER_END := 0.80  # windup 0.80–1.00

# Blink: jadwal kedip acak mandiri agar wajah hidup
var _blink_cd := 2.5
var _blink_t := -1.0

# Kain & secondary motion
var _cloth_phase := 0.0
var _cloth_speed := 1.0


static func ss(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


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


## Hitung pose target ke `out` (pakai-ulang, tanpa alokasi).
func compute(state: String, phase: float, attack_progress: float,
		skill_t: float, extra: Dictionary, out: SylaraPose) -> void:
	out.reset()
	out.eye_blink = _blink_amount()

	match state:
		"idle":
			_idle(out, phase)
		"walk":
			_walk(out, phase)
		"run":
			_run(out, phase)
		"attack":
			_attack(out, attack_progress, phase)
		"swing":
			_swing(out, attack_progress)
		"skill_q":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 3.0, 0.0, 1.0)
			_skill_q(out, prog)
		"skill_w":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 3.0, 0.0, 1.0)
			_skill_w(out, prog, phase, skill_t)
		"skill_e":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 2.5, 0.0, 1.0)
			_skill_e(out, prog)
		"skill_r":
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 1.35, 0.0, 1.0)
			_skill_r(out, prog)
		"hurt":
			_hurt(out, float(extra.get("t", 0.0)))
		"death":
			_death(out, float(extra.get("t", 0.0)))
		"victory":
			_victory(out, phase)
		_:
			_idle(out, phase)

	# Secondary motion untuk kain & rambut
	_cloth(out, state)


# ══════════════════════════════════════════════════════════
#  1. IDLE (Stance Waspada Ranger)
# ══════════════════════════════════════════════════════════

func _idle(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.0
	var breath := sin(phase * 1.8) * 0.02
	p.root_y = sin(phase * 1.8) * 0.70
	p.torso_lean = breath
	p.chest_flex = breath * 0.7
	p.head_lean = sin(phase * 1.4 + 0.3) * 0.02

	# Lengan depan memegang busur rileks dengan keanggunan elven
	p.arm_f_sh = 0.34 + sin(phase * 1.8) * 0.02
	p.arm_f_el = 0.62
	# Lengan belakang rileks di samping
	p.arm_b_sh = -0.07 + sin(phase * 2.0 + 1.0) * 0.02
	p.arm_b_el = 0.42

	# Kaki terbuka mantap & anggun (archer stance)
	p.leg_f_hip = 0.07
	p.leg_f_knee = -0.05
	p.leg_b_hip = -0.08
	p.leg_b_knee = -0.04
	p.leg_f_foot = 0.12
	p.leg_b_foot = 0.10

	# Busur dipegang diagonal rendah
	p.bow_angle = -0.42 + sin(phase * 1.5) * 0.03
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  2. WALK (Langkah Ranger Anggun)
# ══════════════════════════════════════════════════════════

func _walk(p: SylaraPose, phase: float) -> void:
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

func _run(p: SylaraPose, phase: float) -> void:
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
#  4. ATTACK (Ranged — RELEASE-FIRST, sinkron spawn instan)
#
#  ap 0.00 = tali dilepas + proyektil beterbangan (Hero.try_attack).
#  Siklus: RELEASE → FOLLOW → READY → ANTICIPATION → DRAW (wrap = lepas).
# ══════════════════════════════════════════════════════════

func _attack(p: SylaraPose, ap: float, phase: float) -> void:
	_cloth_speed = 1.85

	if ap < ATK_RELEASE_END:
		# RELEASE (IMPACT): tali snap, panah melesat, lengan busur tetap lurus horizontal setinggi dada.
		var t := ap / ATK_RELEASE_END
		p.torso_lean = lerpf(0.07, 0.02, t)
		p.arm_f_sh = 1.50
		p.arm_f_el = 0.05
		p.arm_b_sh = lerpf(-1.55, -0.60, t)
		p.arm_b_el = lerpf(2.85, 0.85, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(1.0, 0.0, t * t)
		p.root_x = lerpf(1.4, 0.4, t)
		p.chest_flex = lerpf(-0.02, 0.0, t)
		p.wind_glow = lerpf(0.6, 0.25, t)

	elif ap < ATK_FOLLOW_END:
		# FOLLOW THROUGH: lengan tali kembali, busur turun bertahap ke siaga.
		var t := ss((ap - ATK_RELEASE_END) / (ATK_FOLLOW_END - ATK_RELEASE_END))
		p.torso_lean = lerpf(0.02, 0.0, t)
		p.arm_f_sh = lerpf(1.50, 0.55, t)
		p.arm_f_el = lerpf(0.05, 0.38, t)
		p.arm_b_sh = lerpf(-0.60, -0.12, t)
		p.arm_b_el = lerpf(0.85, 0.45, t)
		p.bow_angle = lerpf(0.0, -0.20, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.4, 0.0, t)
		p.wind_glow = lerpf(0.25, 0.05, t)

	elif ap < ATK_READY_END:
		# READY: siaga bernapas, busur setengah terangkat.
		var sway := sin(phase * 2.0) * 0.02
		p.torso_lean = sway
		p.arm_f_sh = 0.55 + sway
		p.arm_f_el = 0.38
		p.arm_b_sh = -0.12 + sway
		p.arm_b_el = 0.45
		p.bow_angle = -0.20 + sway
		p.bow_draw = 0.0
		p.root_x = 0.0
		p.wind_glow = 0.05

	elif ap < ATK_ANTICIP_END:
		# ANTICIPATION: angkat busur ke setinggi bahu/dada, condong ke belakang.
		var t := ss((ap - ATK_READY_END) / (ATK_ANTICIP_END - ATK_READY_END))
		p.torso_lean = lerpf(0.0, -0.07, t)
		p.arm_f_sh = lerpf(0.55, 1.48, t)
		p.arm_f_el = lerpf(0.38, 0.06, t)
		p.arm_b_sh = lerpf(-0.12, -1.45, t)
		p.arm_b_el = lerpf(0.45, 2.70, t)
		p.bow_angle = lerpf(-0.20, 0.02, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.0, -1.6, t)

	else:
		# DRAW: tarik tali hingga penuh ke anchor point pipi/dagu!
		var t := ss((ap - ATK_ANTICIP_END) / (1.0 - ATK_ANTICIP_END))
		p.torso_lean = lerpf(-0.07, -0.11, t)
		p.arm_f_sh = 1.48 + t * 0.04
		p.arm_f_el = lerpf(0.06, 0.04, t)
		p.arm_b_sh = lerpf(-1.45, -1.55, t)
		p.arm_b_el = lerpf(2.70, 2.85, t)
		p.bow_angle = lerpf(0.02, 0.0, t)
		p.bow_draw = t
		p.root_x = lerpf(-1.6, -2.6, t)
		p.chest_flex = t * 0.05
		p.wind_glow = t * 0.45

	p.leg_f_hip = 0.16 + sin(phase * 0.5) * 0.02
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  5. SWING (Melee Riposte — STRIKE-FIRST, sinkron damage instan)
#
#  ap 0.00 = busur menghantam (damage sudah mendarat di try_attack).
#  Siklus: STRIKE → HOLD → RECOVER → WINDUP (wrap = hantam).
# ══════════════════════════════════════════════════════════

func _swing(p: SylaraPose, ap: float) -> void:
	_cloth_speed = 2.1

	if ap < SWING_STRIKE_END:
		# STRIKE: sapuan cepat atas-belakang → bawah-depan + lunge.
		var t := ss(ap / SWING_STRIKE_END)
		p.torso_lean = lerpf(-0.16, 0.20, t)
		p.arm_f_sh = lerpf(-0.65, 1.25, t)
		p.arm_f_el = lerpf(0.95, 0.28, t)
		p.bow_angle = lerpf(1.85, -1.25, t)
		p.root_x = lerpf(-2.2, 3.2, t)
		p.chest_flex = lerpf(0.0, 0.09, t)
		p.wind_glow = lerpf(0.45, 0.15, t)
	elif ap < SWING_HOLD_END:
		# HOLD: tahan ujung sapuan sepersekian detik (bobot).
		var t := (ap - SWING_STRIKE_END) / (SWING_HOLD_END - SWING_STRIKE_END)
		p.torso_lean = lerpf(0.20, 0.14, t)
		p.arm_f_sh = 1.25
		p.arm_f_el = 0.28
		p.bow_angle = -1.25
		p.root_x = lerpf(3.2, 2.4, t)
		p.chest_flex = 0.09
		p.wind_glow = lerpf(0.15, 0.05, t)
	elif ap < SWING_RECOVER_END:
		# RECOVER: kembali ke guard.
		var t := ss((ap - SWING_HOLD_END) / (SWING_RECOVER_END - SWING_HOLD_END))
		p.torso_lean = lerpf(0.14, 0.0, t)
		p.arm_f_sh = lerpf(1.25, 0.35, t)
		p.arm_f_el = lerpf(0.28, 0.65, t)
		p.bow_angle = lerpf(-1.25, -0.45, t)
		p.root_x = lerpf(2.4, 0.0, t)
		p.chest_flex = lerpf(0.09, 0.0, t)
		p.wind_glow = 0.05
	else:
		# WINDUP: angkat busur untuk hantaman berikutnya.
		var t := ss((ap - SWING_RECOVER_END) / (1.0 - SWING_RECOVER_END))
		p.torso_lean = lerpf(0.0, -0.16, t)
		p.arm_f_sh = lerpf(0.35, -0.65, t)
		p.arm_f_el = lerpf(0.65, 0.95, t)
		p.bow_angle = lerpf(-0.45, 1.85, t)
		p.root_x = lerpf(0.0, -2.2, t)
		p.wind_glow = t * 0.2

	p.leg_f_hip = 0.22
	p.leg_f_knee = -0.11
	p.leg_b_hip = -0.24
	p.leg_b_knee = -0.09
	p.arm_b_sh = -0.16
	p.arm_b_el = 0.52


# ══════════════════════════════════════════════════════════
#  6. SKILL Q — FOCUS FIRE (Rapid Volley Barrage)
# ══════════════════════════════════════════════════════════

func _skill_q(p: SylaraPose, prog: float) -> void:
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

func _skill_w(p: SylaraPose, prog: float, phase: float, skill_t: float) -> void:
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

func _skill_e(p: SylaraPose, prog: float) -> void:
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

func _skill_r(p: SylaraPose, prog: float) -> void:
	_cloth_speed = 2.6

	if prog < 0.35:
		# CHARGE: kuda-kuda kokoh, busur terangkat horizontal, tarikan tali ke pipi maksimal.
		var t := ss(prog / 0.35)
		p.arm_f_sh = lerpf(0.35, 1.52, t)
		p.arm_f_el = lerpf(0.65, 0.04, t)
		p.arm_b_sh = lerpf(-0.08, -1.55, t)
		p.arm_b_el = lerpf(0.45, 2.85, t)
		p.bow_angle = lerpf(-0.45, 0.0, t)
		p.bow_draw = t
		p.torso_lean = lerpf(0.0, -0.15, t)
		p.root_x = lerpf(0.0, -3.8, t)
		p.root_y = lerpf(0.0, -1.6, t)
		p.chest_flex = t * 0.07
		p.wind_glow = t * 0.95

	elif prog < 0.45:
		# RELEASE: ledakan badai kerucut 5-panah gale.
		var t := ss((prog - 0.35) / 0.10)
		p.arm_f_sh = 1.52
		p.arm_f_el = 0.04
		p.arm_b_sh = lerpf(-1.55, -0.10, t)
		p.arm_b_el = lerpf(2.85, 0.40, t)
		p.bow_angle = 0.0
		p.bow_draw = lerpf(1.0, 0.0, t * t)
		p.torso_lean = lerpf(-0.15, 0.14, t)
		p.root_x = lerpf(-3.8, 4.2, t)
		p.root_y = lerpf(-1.6, 0.6, t)
		p.chest_flex = lerpf(0.07, -0.04, t)
		p.wind_glow = 1.0

	elif prog < 0.72:
		# GALE TUNNEL: follow through pose.
		var t := (prog - 0.45) / 0.27
		p.arm_f_sh = lerpf(1.52, 1.10, t)
		p.arm_f_el = lerpf(0.04, 0.20, t)
		p.arm_b_sh = -0.10
		p.arm_b_el = 0.38
		p.bow_angle = lerpf(0.0, 0.10, t)
		p.torso_lean = lerpf(0.14, 0.04, t)
		p.root_x = lerpf(4.2, 1.6, t)
		p.wind_glow = lerpf(1.0, 0.4, t)

	else:
		# RECOVERY
		var t := ss((prog - 0.72) / 0.28)
		p.arm_f_sh = lerpf(1.10, 0.35, t)
		p.arm_f_el = lerpf(0.20, 0.65, t)
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

func _hurt(p: SylaraPose, t: float) -> void:
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

func _death(p: SylaraPose, t: float) -> void:
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

func _victory(p: SylaraPose, phase: float) -> void:
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

func _cloth(p: SylaraPose, state: String) -> void:
	var cp := _cloth_phase
	var cape_base := PI + 0.10

	# 3 segmen cape dengan perpaduan gelombang multi-harmonik (gerakan kain alami)
	for i in 3:
		var seg_speed := 0.13 + float(i) * 0.08
		var wave := (sin(cp + float(i) * 0.68) * 0.75 + sin(cp * 1.8 + float(i) * 1.1) * 0.25) * seg_speed
		p.cape[i] = cape_base + wave + float(i) * 0.06

	# 2 segmen hood cowl
	for i in 2:
		var wave := (sin(cp * 0.85 + float(i) * 0.9) * 0.8 + sin(cp * 1.6) * 0.2) * 0.08
		p.hood[i] = PI + wave

	# 3 segmen rambut auburn yang melambai lembut dengan gravitasi & angin
	for i in 3:
		var seg_speed := 0.11 + float(i) * 0.07
		var wave := (sin(cp * 1.15 + float(i) * 0.58 + 1.2) * 0.7 + sin(cp * 2.2 + float(i)) * 0.3) * seg_speed
		p.hair[i] = PI + 0.14 + wave + float(i) * 0.05

	# Kibaran ekstra saat berlari / skill
	if state in ["run", "skill_w"]:
		for i in 3:
			p.cape[i] += 0.22 + float(i) * 0.08
		for i in 3:
			p.hair[i] += 0.16 + float(i) * 0.06
	elif state in ["skill_r", "swing"]:
		for i in 3:
			p.cape[i] += 0.14
		for i in 3:
			p.hair[i] += 0.09
