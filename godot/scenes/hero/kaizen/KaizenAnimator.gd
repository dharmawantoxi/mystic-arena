# KaizenAnimator.gd — state machine animasi prosedural Kaizen (v4 rebuild).
#
# Tanggung jawab SATU hal: (state, fase, progress) → KaizenPose target.
# Tidak menyentuh node, tidak menggambar, tidak spawn FX — itu urusan
# KaizenRenderer / KaizenSkillFX. Dipakai KaizenSkeleton.gd (arena) dan
# KaizenDemo.gd (showcase).
#
# Setiap state mengikuti hukum game-feel:
#   ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY
# dan secondary motion (scarf, ponytail, hachimaki) dihitung sebagai fungsi
# fase + "stream factor" supaya kain bereaksi terhadap kecepatan gerak.
extends RefCounted

const PoseScript = preload("res://scenes/hero/kaizen/KaizenPose.gd")

# ── Timing serangan dasar (mirip kurva pygame _NS_kaizen, ditala ulang) ──
const ATK_WINDUP_END := 0.22
const ATK_SWING_END := 0.55
const ATK_HOLD_END := 0.68
# Sudut bilah (derajat): siaga → angkat belakang-atas → tebas depan-bawah
const ATK_REST_ANG := -32.0
const ATK_RAISE_ANG := 148.0
const ATK_END_ANG := -58.0

# Blink: jadwal kedip mandiri supaya wajah hidup.
var _blink_cd := 2.3
var _blink_t := -1.0


static func D(deg: float) -> float:
	return deg * PI / 180.0


static func ss(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


## Dipanggil root tiap frame (delta asli). Mengatur kedip mata.
func tick(delta: float) -> void:
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
## state: idle/walk/run/attack/skill_q/skill_dash/skill_w/skill_e/skill_r/
##        hurt/death/victory
## phase: fase global (Hero.anim_phase) untuk siklus periodik.
## attack_progress: 0..1 saat state == "attack".
## skill_t: detik sejak skill dimulai (untuk sequenced skill).
## extra: {"t": durasi-normal 0..1 untuk hurt/death}
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
		"skill_q":
			# Hero tidak mengirim attack_progress untuk skill — pakai
			# skill_t sebagai progress iai 0.6 dtk (sinkron dengan FX).
			var prog := attack_progress
			if prog <= 0.0:
				prog = clampf(skill_t / 0.6, 0.0, 1.0)
			_skill_q(p, prog, phase)
		"skill_dash":
			_skill_dash(p, phase, skill_t)
		"skill_w":
			_skill_w(p, phase, skill_t)
		"skill_e":
			_skill_e(p, skill_t)
		"skill_r":
			_skill_r(p, skill_t)
		"hurt":
			_hurt(p, float(extra.get("t", 0.0)), phase)
		"death":
			_death(p, float(extra.get("t", 0.0)))
		"victory":
			_victory(p, phase)
		_:
			_idle(p, phase)
	return p


# ══════════════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════════════

func _idle(p: Object, phase: float) -> void:
	var br := sin(phase * 0.9)
	p.root_y = br * 1.6
	p.torso_lean = D(2.0) + sin(phase * 0.5) * 0.02
	p.chest_flex = sin(phase * 0.9 + 0.8) * 0.02
	p.head_lean = sin(phase * 0.7 + 1.4) * 0.05
	# Kaki sedikit terbuka, berat di belakang — stance assassin santai.
	p.leg_f_hip = D(7.0)
	p.leg_f_knee = D(-5.0)
	p.leg_b_hip = D(-8.0)
	p.leg_b_knee = D(-4.0)
	p.leg_f_foot = D(6.0)
	p.leg_b_foot = D(4.0)
	# Tangan pedang rileks di depan paha, bilah menunjuk depan-bawah.
	p.arm_f_sh = D(10.0) + br * 0.02
	p.arm_f_el = D(30.0)
	p.arm_b_sh = D(-9.0) - br * 0.02
	p.arm_b_el = D(24.0)
	p.weapon_angle = D(ATK_REST_ANG) + sin(phase * 0.9 + 0.4) * 0.03
	p.skirt_flare = 0.6 + br * 0.4
	_secondary(p, phase, 1.0, 0.10)


func _walk(p: Object, phase: float) -> void:
	var stride := sin(phase * 1.72)
	var stride2 := sin(phase * 1.72 + PI)
	p.root_y = sin(phase * 3.44) * 1.9 - 1.5
	p.root_x = 1.0
	p.torso_lean = D(5.0) + stride * 0.02
	p.head_lean = -stride * 0.04
	# Kaki: ayunan berlawanan fase; lutut menekuk saat mengayun.
	p.leg_f_hip = D(24.0) * stride
	p.leg_f_knee = D(-8.0) + maxf(0.0, -stride) * D(34.0)
	p.leg_f_foot = D(10.0) + stride * D(9.0)
	p.leg_b_hip = D(24.0) * stride2
	p.leg_b_knee = D(-8.0) + maxf(0.0, -stride2) * D(34.0)
	p.leg_b_foot = D(10.0) + stride2 * D(9.0)
	# Lengan berayun kontra-kaki; tangan pedang tetap tenang (tidak kaku).
	p.arm_f_sh = D(8.0) + stride2 * D(10.0)
	p.arm_f_el = D(26.0)
	p.arm_b_sh = D(-6.0) + stride * D(12.0)
	p.arm_b_el = D(20.0)
	p.weapon_angle = D(ATK_REST_ANG + 6.0) + stride2 * 0.06
	p.skirt_flare = 1.5 + absf(stride) * 3.0
	_secondary(p, phase, 2.2, 0.16)


func _run(p: Object, phase: float) -> void:
	var stride := sin(phase * 2.3)
	var stride2 := sin(phase * 2.3 + PI)
	p.root_y = sin(phase * 4.6) * 2.6 - 3.0
	p.root_x = 4.0
	p.torso_lean = D(16.0)
	p.chest_flex = D(3.0)
	p.head_lean = D(-4.0)
	p.leg_f_hip = D(38.0) * stride
	p.leg_f_knee = D(-14.0) + maxf(0.0, -stride) * D(52.0)
	p.leg_f_foot = D(16.0) + stride * D(14.0)
	p.leg_b_hip = D(38.0) * stride2
	p.leg_b_knee = D(-14.0) + maxf(0.0, -stride2) * D(52.0)
	p.leg_b_foot = D(16.0) + stride2 * D(14.0)
	# Bilah diseret di belakang punggung — siluet "lari ninja".
	p.arm_f_sh = D(-16.0)
	p.arm_f_el = D(34.0)
	p.arm_b_sh = D(30.0) + stride * D(16.0)
	p.arm_b_el = D(38.0)
	p.weapon_angle = D(172.0) + stride * 0.05
	p.skirt_flare = 4.5 + absf(stride) * 2.5
	_secondary(p, phase, 3.2, 0.42)


func _attack(p: Object, ap: float, phase: float) -> void:
	ap = clampf(ap, 0.0, 1.0)
	if ap < ATK_WINDUP_END:
		# ANTICIPATION — tarik bilah ke belakang-atas, tubuh merendah.
		var t := ss(ap / ATK_WINDUP_END)
		p.root_y = 3.0 * t
		p.root_x = -1.5 * t
		p.torso_lean = D(2.0) - D(12.0) * t
		p.head_lean = -D(4.0) * t
		p.leg_f_hip = D(7.0) + D(9.0) * t
		p.leg_f_knee = D(-5.0) - D(14.0) * t
		p.leg_b_hip = D(-8.0) - D(7.0) * t
		p.leg_b_knee = D(-4.0) - D(10.0) * t
		p.arm_f_sh = D(10.0) - D(66.0) * t
		p.arm_f_el = D(30.0) + D(74.0) * t
		p.arm_b_sh = D(-9.0) + D(22.0) * t
		p.arm_b_el = D(24.0) + D(18.0) * t
		p.weapon_angle = lerp_angle(D(ATK_REST_ANG), D(ATK_RAISE_ANG), t)
		p.skirt_flare = 0.6 + t * 1.4
		p.trail = false
	elif ap < ATK_SWING_END:
		# ACTION — tebasan cepat; kurva ease-in supaya ada "berat".
		var t := pow((ap - ATK_WINDUP_END) / (ATK_SWING_END - ATK_WINDUP_END), 1.45)
		p.root_y = lerp(3.0, -1.0, t)
		p.root_x = lerp(-1.5, 7.0, t)
		p.torso_lean = lerp_angle(D(-10.0), D(13.0), t)
		p.head_lean = D(3.0) * t
		p.leg_f_hip = D(16.0) + D(20.0) * t
		p.leg_f_knee = D(-19.0) + D(12.0) * t
		p.leg_b_hip = D(-15.0) - D(12.0) * t
		p.leg_b_knee = D(-14.0) + D(4.0) * t
		p.arm_f_sh = lerp_angle(D(-56.0), D(58.0), t)
		p.arm_f_el = lerp(D(104.0), D(16.0), t)
		p.arm_b_sh = D(13.0) - D(30.0) * t
		p.arm_b_el = D(42.0)
		p.weapon_angle = lerp_angle(D(ATK_RAISE_ANG), D(ATK_END_ANG), t)
		p.skirt_flare = 2.0 + t * 4.0
		p.trail = true
	elif ap < ATK_HOLD_END:
		# IMPACT HOLD — brief settle; jejak bilah masih terlihat.
		var t := ss((ap - ATK_SWING_END) / (ATK_HOLD_END - ATK_SWING_END))
		p.root_y = lerp(-1.0, 0.5, t)
		p.root_x = lerp(7.0, 5.5, t)
		p.torso_lean = D(13.0) - D(3.0) * t
		p.head_lean = D(3.0) - D(1.0) * t
		p.leg_f_hip = D(36.0) - D(6.0) * t
		p.leg_f_knee = D(-7.0)
		p.leg_b_hip = D(-27.0) + D(4.0) * t
		p.leg_b_knee = D(-10.0)
		p.arm_f_sh = D(58.0) - D(8.0) * t
		p.arm_f_el = D(16.0) + D(4.0) * t
		p.arm_b_sh = D(-17.0)
		p.arm_b_el = D(40.0)
		p.weapon_angle = D(ATK_END_ANG) + 0.04 * sin(phase * 30.0) * (1.0 - t)
		p.skirt_flare = 6.0 - t * 1.5
		p.trail = true
	else:
		# RECOVERY — kembali ke siaga (dipotong halus oleh blending root).
		var t := ss((ap - ATK_HOLD_END) / (1.0 - ATK_HOLD_END))
		p.root_y = lerp(0.5, 0.0, t)
		p.root_x = lerp(5.5, 0.0, t)
		p.torso_lean = lerp_angle(D(10.0), D(2.0), t)
		p.leg_f_hip = lerp(D(30.0), D(7.0), t)
		p.leg_f_knee = lerp(D(-7.0), D(-5.0), t)
		p.leg_b_hip = lerp(D(-23.0), D(-8.0), t)
		p.leg_b_knee = lerp(D(-10.0), D(-4.0), t)
		p.arm_f_sh = lerp_angle(D(50.0), D(10.0), t)
		p.arm_f_el = lerp(D(20.0), D(30.0), t)
		p.arm_b_sh = lerp(D(-17.0), D(-9.0), t)
		p.arm_b_el = lerp(D(40.0), D(24.0), t)
		p.weapon_angle = lerp_angle(D(ATK_END_ANG), D(ATK_REST_ANG), t)
		p.skirt_flare = lerp(4.5, 0.6, t)
		p.trail = t < 0.4
	_secondary(p, phase, 2.6, 0.24)


## Q1 Steel Wind — iai cepat: anticipation lebih pendek, tebasan lebih lebar.
func _skill_q(p: Object, ap: float, phase: float) -> void:
	_attack(p, ap, phase)
	# Tambahkan karakter "steel wind": stance lebih rendah + bilah lebih turun.
	p.root_y += 2.0
	p.torso_lean += D(3.0)
	p.weapon_angle -= D(10.0)
	p.wind_glow = 0.8
	_secondary(p, phase, 3.0, 0.30)


## Q2 Dash Strike — pose melayang selama dash.
func _skill_dash(p: Object, phase: float, skill_t: float) -> void:
	var settle := ss(minf(1.0, skill_t / 0.45))
	p.root_x = lerp(9.0, 3.0, settle)
	p.root_y = lerp(-4.0, 1.0, settle)
	p.torso_lean = lerp(D(26.0), D(8.0), settle)
	p.head_lean = lerp(D(-6.0), D(0.0), settle)
	p.leg_f_hip = lerp(D(46.0), D(18.0), settle)
	p.leg_f_knee = lerp(D(-30.0), D(-10.0), settle)
	p.leg_b_hip = lerp(D(-40.0), D(-14.0), settle)
	p.leg_b_knee = lerp(D(-16.0), D(-8.0), settle)
	p.leg_f_foot = D(24.0)
	p.leg_b_foot = D(18.0)
	# Bilah terseret lurus ke belakang — garis dash terbaca jelas.
	p.arm_f_sh = D(-24.0)
	p.arm_f_el = D(12.0)
	p.arm_b_sh = D(38.0)
	p.arm_b_el = D(30.0)
	p.weapon_angle = D(168.0)
	p.skirt_flare = 5.0
	p.wind_glow = 1.0
	p.trail = settle < 0.6
	_secondary(p, phase, 4.0, 0.85)


## W Wind Wall — dorongan telapak ke depan, kuda-kuda belakang.
func _skill_w(p: Object, phase: float, skill_t: float) -> void:
	var push := ss(minf(1.0, skill_t / 0.16))
	var hold_wave := sin(phase * 2.6)
	p.root_y = 2.0
	p.root_x = -2.0 * push
	p.torso_lean = D(4.0) + D(6.0) * push
	p.head_lean = D(2.0) * push
	p.leg_f_hip = D(22.0) * push + D(7.0)
	p.leg_f_knee = D(-12.0) - D(8.0) * push
	p.leg_b_hip = D(-16.0) - D(8.0) * push
	p.leg_b_knee = D(-10.0) - D(8.0) * push
	# Lengan depan lurus ke depan (telapak terbuka mendorong angin).
	p.arm_f_sh = lerp_angle(D(10.0), D(86.0), push)
	p.arm_f_el = lerp(D(30.0), D(4.0), push)
	# Bilah dipegang rendah di tangan belakang.
	p.arm_b_sh = D(-30.0) * push - D(9.0)
	p.arm_b_el = D(24.0) + D(10.0) * push
	p.weapon_angle = D(-118.0) - D(8.0) * hold_wave * push
	p.skirt_flare = 2.0 + push * 1.5
	p.wind_glow = 0.5 + 0.3 * push + 0.2 * maxf(0.0, hold_wave)
	_secondary(p, phase, 2.8, 0.34)


## E Whirlwind — putaran bilah dua kali di sekeliling tubuh.
func _skill_e(p: Object, skill_t: float) -> void:
	var spin_dur := 0.55
	var k := clampf(skill_t / spin_dur, 0.0, 1.0)
	var wind_down := clampf((skill_t - spin_dur) / 0.25, 0.0, 1.0)
	# Kurva putaran: cepat di tengah (ease in-out) supaya terasa bertenaga.
	var ang := D(-30.0) + ss(k) * TAU * 2.0
	p.root_y = 2.5
	p.torso_lean = D(4.0) + sin(k * TAU * 2.0) * 0.06
	p.head_lean = D(2.0)
	p.leg_f_hip = D(18.0)
	p.leg_f_knee = D(-16.0)
	p.leg_b_hip = D(-18.0)
	p.leg_b_knee = D(-14.0)
	p.leg_f_foot = D(12.0)
	p.leg_b_foot = D(8.0)
	# Lengan pedang mengikuti putaran; lengan belakang menjaga keseimbangan.
	p.arm_f_sh = D(64.0) + sin(ang) * 0.25
	p.arm_f_el = D(8.0)
	p.arm_b_sh = D(-40.0) - sin(ang) * 0.2
	p.arm_b_el = D(36.0)
	p.weapon_angle = ang
	p.skirt_flare = 4.0 + sin(k * PI) * 3.0
	p.wind_glow = 0.9 * (1.0 - wind_down)
	p.trail = k < 1.0
	_secondary(p, skill_t * 12.0, 3.4, 0.5)


## R Tempest Fury — crouch dalam → tebasan naik menyilang.
func _skill_r(p: Object, skill_t: float) -> void:
	if skill_t < 0.16:
		# PRE-CAST: menarik napas, merendah, bilah ke belakang-bawah.
		var t := ss(skill_t / 0.16)
		p.root_y = 6.0 * t
		p.torso_lean = D(-6.0) * t
		p.head_lean = -D(5.0) * t
		p.leg_f_hip = D(7.0) + D(20.0) * t
		p.leg_f_knee = D(-5.0) - D(30.0) * t
		p.leg_b_hip = D(-8.0) - D(16.0) * t
		p.leg_b_knee = D(-4.0) - D(26.0) * t
		p.arm_f_sh = D(10.0) - D(70.0) * t
		p.arm_f_el = D(30.0) + D(40.0) * t
		p.arm_b_sh = D(-9.0) + D(14.0) * t
		p.arm_b_el = D(24.0) + D(16.0) * t
		p.weapon_angle = D(-32.0) - D(120.0) * t
		p.wind_glow = t
	elif skill_t < 0.42:
		# RELEASE: meledak ke atas, bilah naik vertikal.
		var t := pow((skill_t - 0.16) / 0.26, 1.35)
		p.root_y = lerp(6.0, -5.0, t)
		p.root_x = 3.0 * t
		p.torso_lean = lerp_angle(D(-6.0), D(9.0), t)
		p.head_lean = lerp(D(-5.0), D(2.0), t)
		p.leg_f_hip = lerp(D(27.0), D(14.0), t)
		p.leg_f_knee = lerp(D(-35.0), D(-8.0), t)
		p.leg_b_hip = lerp(D(-24.0), D(-18.0), t)
		p.leg_b_knee = lerp(D(-30.0), D(-12.0), t)
		p.arm_f_sh = lerp_angle(D(-60.0), D(96.0), t)
		p.arm_f_el = lerp(D(70.0), D(6.0), t)
		p.arm_b_sh = D(5.0) - D(30.0) * t
		p.arm_b_el = D(40.0)
		p.weapon_angle = lerp_angle(D(-152.0), D(104.0), t)
		p.skirt_flare = 3.0 + t * 4.0
		p.wind_glow = 1.0
		p.trail = true
	else:
		# AFTERMATH: turun kembali ke siaga, sisa angin memudar.
		var t := ss(minf(1.0, (skill_t - 0.42) / 0.7))
		p.root_y = lerp(-5.0, 0.0, t)
		p.root_x = lerp(3.0, 0.0, t)
		p.torso_lean = lerp_angle(D(9.0), D(2.0), t)
		p.leg_f_hip = lerp(D(14.0), D(7.0), t)
		p.leg_f_knee = lerp(D(-8.0), D(-5.0), t)
		p.leg_b_hip = lerp(D(-18.0), D(-8.0), t)
		p.leg_b_knee = lerp(D(-12.0), D(-4.0), t)
		p.arm_f_sh = lerp_angle(D(96.0), D(10.0), t)
		p.arm_f_el = lerp(D(6.0), D(30.0), t)
		p.arm_b_sh = lerp(D(-25.0), D(-9.0), t)
		p.arm_b_el = lerp(D(40.0), D(24.0), t)
		p.weapon_angle = lerp_angle(D(104.0), D(-32.0), t)
		p.wind_glow = 1.0 - t * 0.75
	_secondary(p, skill_t * 14.0, 3.0, 0.4)


func _hurt(p: Object, t: float, phase: float) -> void:
	var k := 1.0 - ss(t)  # kuat di awal, pulih di akhir
	var shiver := sin(t * 42.0) * 1.4 * k
	p.root_x = -3.0 * k + shiver
	p.root_y = 2.0 * k
	p.torso_lean = -D(16.0) * k
	p.chest_flex = -D(6.0) * k
	p.head_lean = -D(14.0) * k
	p.arm_f_sh = D(10.0) + D(34.0) * k
	p.arm_f_el = D(30.0) + D(20.0) * k
	p.arm_b_sh = D(-9.0) - D(26.0) * k
	p.arm_b_el = D(24.0) + D(30.0) * k
	p.weapon_angle = D(ATK_REST_ANG) - D(26.0) * k
	p.leg_f_hip = D(7.0) + D(6.0) * k
	p.leg_f_knee = D(-5.0) - D(10.0) * k
	p.leg_b_hip = D(-8.0) - D(10.0) * k
	p.leg_b_knee = D(-4.0) - D(14.0) * k
	p.hurt_tint = k
	p.skirt_flare = 1.0 + k
	_secondary(p, phase, 2.0, 0.2)


func _death(p: Object, t: float) -> void:
	# Roboh ke belakang: pinggul turun, torso rebah, bilah terlepas.
	var k := ss(t)
	p.root_y = 19.0 * k
	p.root_x = -6.0 * k
	p.torso_lean = -D(72.0) * k
	p.chest_flex = -D(10.0) * k
	p.head_lean = -D(20.0) * k
	p.arm_f_sh = D(10.0) + D(60.0) * k
	p.arm_f_el = D(30.0) - D(10.0) * k
	p.arm_b_sh = D(-9.0) - D(52.0) * k
	p.arm_b_el = D(24.0) + D(20.0) * k
	p.leg_f_hip = D(7.0) + D(56.0) * k
	p.leg_f_knee = D(-5.0) - D(70.0) * k
	p.leg_b_hip = D(-8.0) + D(38.0) * k
	p.leg_b_knee = D(-4.0) - D(54.0) * k
	p.weapon_angle = D(ATK_REST_ANG) - D(60.0) * k
	p.skirt_flare = 3.0 * k
	p.alpha = 1.0 - 0.4 * k
	_secondary(p, 0.0, 0.4, 0.05)


func _victory(p: Object, phase: float) -> void:
	var br := sin(phase * 1.4)
	# Bilah ditegakkan ke atas (flourish), scarf berkibar bangga.
	p.root_y = br * 1.2
	p.torso_lean = D(-2.0)
	p.head_lean = D(-6.0)
	p.arm_f_sh = D(74.0) + br * 0.03
	p.arm_f_el = D(-16.0)
	p.arm_b_sh = D(-16.0)
	p.arm_b_el = D(18.0)
	p.weapon_angle = D(86.0) + sin(phase * 1.4 + 0.5) * 0.02
	p.leg_f_hip = D(9.0)
	p.leg_f_knee = D(-6.0)
	p.leg_b_hip = D(-10.0)
	p.leg_b_knee = D(-5.0)
	p.skirt_flare = 1.5 + br * 0.5
	p.wind_glow = 0.35 + 0.15 * maxf(0.0, br)
	_secondary(p, phase, 2.4, 0.22)


# ══════════════════════════════════════════════════════════
#  SECONDARY MOTION (scarf / ponytail / hachimaki)
# ══════════════════════════════════════════════════════════

## `speed_factor` = seberapa cepat kain harus berkibar (1 = idle, 4 = dash).
## `stream` = 0..1; 1 = ekor kain lurus terseret ke belakang (gerakan cepat).
func _secondary(p: Object, phase: float, speed_factor: float, stream: float) -> void:
	var w1 := sin(phase * 1.35 * speed_factor)
	var w2 := sin(phase * 1.35 * speed_factor + 0.9)
	var w3 := sin(phase * 1.35 * speed_factor + 1.8)
	var amp := 0.16 * (1.0 - stream * 0.6)
	# Scarf: tiga segmen, makin ke ujung makin liar.
	p.scarf[0] = lerp(2.98, PI, stream) + w1 * amp
	p.scarf[1] = lerp(3.10, PI + 0.06, stream) + w2 * amp * 1.4
	p.scarf[2] = lerp(2.86, PI - 0.05, stream) + w3 * amp * 1.8
	# Ponytail: lebih berat, frekuensi sedikit berbeda.
	var q1 := sin(phase * 1.15 * speed_factor + 0.5)
	var q2 := sin(phase * 1.15 * speed_factor + 1.4)
	var q3 := sin(phase * 1.15 * speed_factor + 2.2)
	p.pony[0] = lerp(3.05, PI + 0.1, stream) + q1 * amp * 0.8
	p.pony[1] = lerp(3.18, PI + 0.14, stream) + q2 * amp * 1.2
	p.pony[2] = lerp(2.95, PI + 0.02, stream) + q3 * amp * 1.6
	# Tali hachimaki: pendek, responsif.
	var b1 := sin(phase * 1.7 * speed_factor + 0.3)
	var b2 := sin(phase * 1.7 * speed_factor + 1.2)
	p.band[0] = lerp(2.85, PI - 0.12, stream) + b1 * amp * 1.1
	p.band[1] = lerp(3.10, PI + 0.02, stream) + b2 * amp * 1.5
	# Condongkan torso sedikit melawan arah kain (aksi-reaksi halus).
	p.torso_lean += stream * 0.02
