# SylaraAnimator.gd — state machine pose Sylara (logika Godot native).
#
# Tanggung jawab SATU hal: (state, fase, progress) → tulis SylaraPose
# target ke instance PAKAI-ULANG (nol alokasi per frame).
#
# Referensi gerak: Wind Ranger (Dota 2) — pemanah elven:
#   * Serangan dasar = SIKLUS LOOP tembak terus:
#     RELEASE → FOLLOW-THROUGH → RAISE → DRAW → (wrap) RELEASE.
#     Lepas tali di DEPAN siklus supaya saat hero menembak beruntun
#     (cooldown pendek, dsb. Focus Fire) animasi terbaca sebagai pemanah
#     nyata: setiap tembakan adalah hasil DRAW dari ekor siklus sebelumnya.
#   * Focus Fire: pose hold-draw stabil antar tembakan + tembak cepat.
#   * Windrun: sprint cepat condong maju, cape & rambut mengalir.
#   * Shackle Shot: angkat-draw-snap ke arah bidik, lalu pose tahan
#     tether (busur setengah turun, masih membidik target yang terkunci).
#   * Powershot: channel 1 detik (kuda-kuda lebar, full draw, tremor
#     kecil di puncak charge) lalu burst release (lunge ke depan).
#
# Kaidah animasi profesional dijaga di semua aksi:
# ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY.
#
# Secondary motion (cape 3 segmen, hood 2 segmen, rambut 3 segmen,
# kedip mata) dihitung kontinu berbasis fase kain & kecepatan gerak.
class_name SylaraAnimator
extends RefCounted

# ── Siklus serangan (loop tembak beruntun) ──
const ATK_RELEASE_END := 0.14   # tali snap + recoil kecil
const ATK_FOLLOW_END := 0.46    # follow through → busur turun
const ATK_RAISE_END := 0.64     # angkat busur ke garis bidik
# DRAW = 0.64 .. 1.00 (wrap kembali ke RELEASE)

# Jadwal kedip acak mandiri agar wajah hidup
var _blink_cd := 2.5
var _blink_t := -1.0

# Kain & secondary motion
var _cloth_phase := 0.0
var _cloth_speed := 1.0


static func ss(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


## Dipanggil root tiap frame (delta asli).
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
## `skill_prog` = progress 0..1 jendela skill aktual (dibaca root dari
## timer kit hero, bukan perkiraan durasi tetap).
func compute(state: String, phase: float, attack_progress: float,
		skill_prog: float, extra: Dictionary, out: SylaraPose) -> void:
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
			_attack(out, attack_progress)
		"focus":
			_focus(out, phase)
		"windrun":
			_windrun(out, phase)
		"shackle_cast":
			# Jendela E total 2.5 dtk; porsi cast = 0.45 dtk pertama.
			var cp := clampf(skill_prog / 0.2, 0.0, 1.0)
			_shackle_cast(out, cp)
		"shackle_hold":
			_shackle_hold(out, phase)
		"channel":
			_channel(out, skill_prog, phase)
		"release":
			_release(out, float(extra.get("t", 0.0)))
		"hurt":
			_hurt(out, float(extra.get("t", 0.0)))
		"death":
			_death(out, float(extra.get("t", 0.0)))
		"victory":
			_victory(out, phase)
		_:
			_idle(out, phase)
	# Secondary motion untuk kain & rambut.
	_cloth(out, state)


# ══════════════════════════════════════════════════════════
#  1. IDLE (stance waspada ranger, busur dipegang rendah)
# ══════════════════════════════════════════════════════════

func _idle(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.0
	var breath := sin(phase * 1.8) * 0.02
	p.root_y = sin(phase * 1.8) * 0.70
	p.torso_lean = breath
	p.chest_flex = breath * 0.7
	p.head_lean = sin(phase * 1.4 + 0.3) * 0.02

	# Lengan depan memegang busur rileks dengan keanggunan elven.
	p.arm_f_sh = 0.34 + sin(phase * 1.8) * 0.02
	p.arm_f_el = 0.62
	# Lengan belakang rileks di samping.
	p.arm_b_sh = -0.07 + sin(phase * 2.0 + 1.0) * 0.02
	p.arm_b_el = 0.42

	# Kaki terbuka mantap (archer stance).
	p.leg_f_hip = 0.07
	p.leg_f_knee = -0.05
	p.leg_b_hip = -0.08
	p.leg_b_knee = -0.04
	p.leg_f_foot = 0.12
	p.leg_b_foot = 0.10

	# Busur dipegang diagonal rendah di depan.
	p.bow_offset = 0.42 + sin(phase * 1.5) * 0.03
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  2. WALK (langkah ranger anggun)
# ══════════════════════════════════════════════════════════

func _walk(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.45
	var cycle := phase * 4.6
	var s := sin(cycle)
	var c := cos(cycle)

	p.root_y = absf(s) * 1.8 - 0.5
	p.root_x = s * 0.85
	p.torso_lean = s * 0.045
	p.chest_flex = 0.02
	p.head_lean = -s * 0.025

	# Kaki berjalan.
	p.leg_f_hip = s * 0.36
	p.leg_f_knee = -absf(s) * 0.36 - 0.05
	p.leg_b_hip = -s * 0.36
	p.leg_b_knee = -absf(c) * 0.36 - 0.05
	p.leg_f_foot = 0.10 + s * 0.08
	p.leg_b_foot = 0.10 - s * 0.08

	# Lengan mengayun harmonis.
	p.arm_f_sh = 0.30 - s * 0.14
	p.arm_f_el = 0.55 + absf(s) * 0.10
	p.arm_b_sh = -0.06 + s * 0.14
	p.arm_b_el = 0.42 + absf(c) * 0.10

	p.bow_offset = 0.40 + s * 0.06
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  3. RUN (lari cepat, busur tetap siap)
# ══════════════════════════════════════════════════════════

func _run(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 2.2
	var cycle := phase * 7.2
	var s := sin(cycle)
	var c := cos(cycle)

	p.root_y = absf(s) * 3.4 - 1.3
	p.root_x = s * 2.0
	p.torso_lean = 0.14 + s * 0.065
	p.chest_flex = 0.05
	p.head_lean = -0.045

	# Langkah lari panjang.
	p.leg_f_hip = s * 0.58
	p.leg_f_knee = -absf(s) * 0.68 - 0.12
	p.leg_b_hip = -s * 0.58
	p.leg_b_knee = -absf(c) * 0.68 - 0.12
	p.leg_f_foot = 0.16 + s * 0.12
	p.leg_b_foot = 0.16 - s * 0.12

	# Lengan depan menahan busur stabil ke depan.
	p.arm_f_sh = 0.58 + s * 0.08
	p.arm_f_el = 0.72
	p.arm_b_sh = -0.32 + s * 0.28
	p.arm_b_el = 0.72 + absf(c) * 0.20

	p.bow_offset = 0.26 + s * 0.06
	p.bow_draw = 0.0


# ══════════════════════════════════════════════════════════
#  4. ATTACK (siklus loop tembak beruntun — gaya Wind Ranger)
#
#  ap 0.00 = tali DILEPAS (panah melesat). Siklus: RELEASE → FOLLOW →
#  RAISE → DRAW, lalu wrap ke RELEASE lagi. Saat hero menembak cepat,
#  wrap ini membuat satu loop animasi kontinu tanpa jeda "siaga".
# ══════════════════════════════════════════════════════════

func _attack(p: SylaraPose, ap: float) -> void:
	_cloth_speed = 1.85

	if ap < ATK_RELEASE_END:
		# RELEASE: tali snap, panah melesat; lengan busur lurus ke depan.
		var t := ap / ATK_RELEASE_END
		p.arm_f_sh = 1.50
		p.arm_f_el = 0.05
		p.arm_b_sh = lerpf(-1.55, -0.55, t)
		p.arm_b_el = lerpf(2.85, 0.90, t)
		p.bow_offset = 0.0
		p.bow_draw = lerpf(1.0, 0.0, t * t)
		p.root_x = lerpf(1.6, 0.5, t)
		p.torso_lean = lerpf(0.06, 0.02, t)
		p.chest_flex = lerpf(-0.02, 0.0, t)
		p.wind_glow = lerpf(0.55, 0.20, t)
	elif ap < ATK_FOLLOW_END:
		# FOLLOW-THROUGH: lengan tali kembali, busur turun bertahap.
		var t := ss((ap - ATK_RELEASE_END) / (ATK_FOLLOW_END - ATK_RELEASE_END))
		p.arm_f_sh = lerpf(1.50, 0.55, t)
		p.arm_f_el = lerpf(0.05, 0.40, t)
		p.arm_b_sh = lerpf(-0.55, -0.15, t)
		p.arm_b_el = lerpf(0.90, 0.50, t)
		p.bow_offset = lerpf(0.0, 0.18, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.5, 0.0, t)
		p.wind_glow = lerpf(0.20, 0.05, t)
	elif ap < ATK_RAISE_END:
		# RAISE: angkat busur ke garis bidik, tangan tarik mundur.
		var t := ss((ap - ATK_FOLLOW_END) / (ATK_RAISE_END - ATK_FOLLOW_END))
		p.arm_f_sh = lerpf(0.55, 1.46, t)
		p.arm_f_el = lerpf(0.40, 0.06, t)
		p.arm_b_sh = lerpf(-0.15, -1.40, t)
		p.arm_b_el = lerpf(0.50, 2.60, t)
		p.bow_offset = lerpf(0.18, -0.02, t)
		p.bow_draw = 0.0
		p.root_x = lerpf(0.0, -1.8, t)
		p.torso_lean = lerpf(0.0, -0.06, t)
	else:
		# DRAW: tarik tali ke jangkar pipi untuk tembakan berikutnya.
		var t := ss((ap - ATK_RAISE_END) / (1.0 - ATK_RAISE_END))
		p.arm_f_sh = lerpf(1.46, 1.52, t)
		p.arm_f_el = lerpf(0.06, 0.04, t)
		p.arm_b_sh = lerpf(-1.40, -1.55, t)
		p.arm_b_el = lerpf(2.60, 2.85, t)
		p.bow_offset = lerpf(-0.02, 0.0, t)
		p.bow_draw = t
		p.root_x = lerpf(-1.8, -2.8, t)
		p.torso_lean = lerpf(-0.06, -0.10, t)
		p.chest_flex = t * 0.05
		p.wind_glow = t * 0.45

	p.leg_f_hip = 0.16
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  5. FOCUS (Focus Fire — pose hold-draw antar tembakan cepat)
# ══════════════════════════════════════════════════════════

func _focus(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.3
	var sway := sin(phase * 2.4) * 0.015
	p.arm_f_sh = 1.42 + sway
	p.arm_f_el = 0.08
	p.arm_b_sh = -1.30 + sway
	p.arm_b_el = 2.45
	p.bow_offset = 0.0
	p.bow_draw = 0.72 + sin(phase * 2.4) * 0.05
	p.torso_lean = -0.08
	p.root_x = -2.2
	p.wind_glow = 0.35
	p.leg_f_hip = 0.16
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  6. WINDRUN (Gale sprint — "melarut ke angin")
# ══════════════════════════════════════════════════════════

func _windrun(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 3.0
	var cycle := phase * 9.5
	var s := sin(cycle)
	var c := cos(cycle)

	p.root_y = absf(s) * 3.0 - 1.2
	p.root_x = s * 2.2
	p.torso_lean = 0.16 + s * 0.05
	p.chest_flex = 0.05
	p.head_lean = -0.06

	# Sprint tinggi, condong ke arah gerak.
	p.leg_f_hip = s * 0.62
	p.leg_f_knee = -absf(s) * 0.74 - 0.14
	p.leg_b_hip = -s * 0.62
	p.leg_b_knee = -absf(c) * 0.74 - 0.14
	p.leg_f_foot = 0.18 + s * 0.14
	p.leg_b_foot = 0.18 - s * 0.14

	p.arm_f_sh = 0.50 + s * 0.10
	p.arm_f_el = 0.45
	p.arm_b_sh = -0.50 + s * 0.20
	p.arm_b_el = 0.60

	p.bow_offset = 0.30 + s * 0.06
	p.bow_draw = 0.0
	p.wind_glow = 0.55 + sin(phase * 7.0) * 0.15


# ══════════════════════════════════════════════════════════
#  7. SHACKLE CAST (angkat-draw-snap ke arah bidik)
# ══════════════════════════════════════════════════════════

func _shackle_cast(p: SylaraPose, cp: float) -> void:
	_cloth_speed = 1.65
	if cp < 0.45:
		var t := ss(cp / 0.45)
		p.arm_f_sh = lerpf(0.35, 1.02, t)
		p.arm_f_el = lerpf(0.65, 0.12, t)
		p.arm_b_sh = lerpf(-0.08, -1.10, t)
		p.arm_b_el = lerpf(0.45, 2.00, t)
		p.bow_offset = lerpf(0.45, 0.0, t)
		p.bow_draw = t * 0.9
		p.torso_lean = lerpf(0.0, -0.12, t)
		p.root_x = lerpf(0.0, -2.0, t)
		p.head_lean = -0.06
	else:
		var t := ss((cp - 0.45) / 0.55)
		p.arm_f_sh = lerpf(1.02, 1.50, t)
		p.arm_f_el = lerpf(0.12, 0.05, t)
		p.arm_b_sh = lerpf(-1.10, -0.15, t)
		p.arm_b_el = lerpf(2.00, 0.60, t)
		p.bow_offset = 0.0
		p.bow_draw = lerpf(0.9, 0.0, t * t)
		p.torso_lean = lerpf(-0.12, 0.08, t)
		p.root_x = lerpf(-2.0, 1.8, t)
		p.wind_glow = lerpf(0.15, 0.5, t)
	p.leg_f_hip = 0.16
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  8. SHACKLE HOLD (tether aktif — masih membidik target terkunci)
# ══════════════════════════════════════════════════════════

func _shackle_hold(p: SylaraPose, phase: float) -> void:
	_cloth_speed = 1.2
	var sway := sin(phase * 2.2) * 0.012
	p.arm_f_sh = 1.30 + sway
	p.arm_f_el = 0.15
	p.arm_b_sh = -0.25 + sway
	p.arm_b_el = 0.60
	p.bow_offset = 0.02
	p.bow_draw = 0.15
	p.torso_lean = 0.03
	p.root_x = 1.0
	p.wind_glow = 0.25 + sin(phase * 4.0) * 0.08
	p.leg_f_hip = 0.16
	p.leg_f_knee = -0.09
	p.leg_b_hip = -0.19
	p.leg_b_knee = -0.07


# ══════════════════════════════════════════════════════════
#  9. CHANNEL (Powershot — charge penuh, string tegang)
# ══════════════════════════════════════════════════════════

func _channel(p: SylaraPose, charge: float, phase: float) -> void:
	_cloth_speed = 1.0
	var t := ss(charge)
	# Kuda-kuda lebar ke belakang, busur terangkat horizontal.
	p.arm_f_sh = lerpf(0.35, 1.54, t)
	p.arm_f_el = lerpf(0.65, 0.03, t)
	p.arm_b_sh = lerpf(-0.08, -1.58, t)
	p.arm_b_el = lerpf(0.45, 2.90, t)
	p.bow_offset = lerpf(0.45, 0.0, t)
	p.bow_draw = t
	p.torso_lean = lerpf(0.0, -0.16, t)
	p.root_x = lerpf(0.0, -4.0, t)
	p.root_y = lerpf(0.0, -1.4, t)
	p.chest_flex = t * 0.06
	p.wind_glow = t
	p.leg_f_hip = 0.22
	p.leg_f_knee = -0.11
	p.leg_b_hip = -0.24
	p.leg_b_knee = -0.09
	# Tremor kecil di puncak charge (ketegangan sebelum lepas).
	if t > 0.75:
		p.head_lean += sin(phase * 42.0) * 0.008


# ══════════════════════════════════════════════════════════
#  10. RELEASE (Powershot lepas — lunge ke depan, string snap)
# ══════════════════════════════════════════════════════════

func _release(p: SylaraPose, rt: float) -> void:
	_cloth_speed = 2.4
	var t := ss(rt)
	p.arm_f_sh = lerpf(1.54, 1.15, t)
	p.arm_f_el = lerpf(0.03, 0.18, t)
	p.arm_b_sh = lerpf(-1.58, -0.10, t)
	p.arm_b_el = lerpf(2.90, 0.40, t)
	p.bow_offset = 0.0
	p.bow_draw = lerpf(1.0, 0.0, minf(rt * 2.2, 1.0))
	p.torso_lean = lerpf(-0.16, 0.12, t)
	p.root_x = lerpf(-4.0, 3.6, t)
	p.root_y = lerpf(-1.4, 0.4, rt)
	p.chest_flex = lerpf(0.06, -0.03, t)
	p.wind_glow = lerpf(1.0, 0.3, t)
	p.leg_f_hip = 0.22
	p.leg_f_knee = -0.11
	p.leg_b_hip = -0.24
	p.leg_b_knee = -0.09


# ══════════════════════════════════════════════════════════
#  11. HURT (recoil kena pukul)
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
	p.bow_offset = 0.45 + recoil * 0.32
	p.hurt_tint = recoil * 0.85
	p.leg_f_hip = 0.07 + recoil * 0.11
	p.leg_b_hip = -0.08 - recoil * 0.11


# ══════════════════════════════════════════════════════════
#  12. DEATH (roboh dramatis + fade ke angin — showcase)
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
	p.bow_offset = 0.45 + fall * 1.25
	p.wind_glow = 0.55 * (1.0 - fall * 0.5)
	p.leg_f_hip = fall * 0.42
	p.leg_f_knee = -fall * 0.52
	p.leg_b_hip = -fall * 0.22
	p.leg_b_knee = -fall * 0.32
	p.alpha = lerpf(1.0, 0.0, ss(clampf((t - 0.35) / 0.65, 0.0, 1.0)))


# ══════════════════════════════════════════════════════════
#  13. VICTORY (angkat busur kemenangan)
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
	p.bow_offset = 1.35 + wave * 0.08
	p.head_lean = -0.11 + wave * 0.03
	p.wind_glow = 0.35 + wave * 0.15
	p.leg_f_hip = 0.11
	p.leg_b_hip = -0.13


# ══════════════════════════════════════════════════════════
#  14. SECONDARY MOTION — KAIN & RAMBUT
# ══════════════════════════════════════════════════════════

func _cloth(p: SylaraPose, state: String) -> void:
	var cp := _cloth_phase
	var cape_base := PI + 0.10

	# 3 segmen cape — gelombang multi-harmonik (pergerakan kain alami).
	for i in 3:
		var seg_speed := 0.13 + float(i) * 0.08
		var wave := (sin(cp + float(i) * 0.68) * 0.75
				+ sin(cp * 1.8 + float(i) * 1.1) * 0.25) * seg_speed
		p.cape[i] = cape_base + wave + float(i) * 0.06

	# 2 segmen hood cowl.
	for i in 2:
		var wave := (sin(cp * 0.85 + float(i) * 0.9) * 0.8
				+ sin(cp * 1.6) * 0.2) * 0.08
		p.hood[i] = PI + wave

	# 3 segmen rambut — gravitasi + angin.
	for i in 3:
		var seg_speed := 0.11 + float(i) * 0.07
		var wave := (sin(cp * 1.15 + float(i) * 0.58 + 1.2) * 0.7
				+ sin(cp * 2.2 + float(i)) * 0.3) * seg_speed
		p.hair[i] = PI + 0.14 + wave + float(i) * 0.05

	# Kibaran ekstra saat berlari / skill kuat.
	if state in ["run", "windrun"]:
		for i in 3:
			p.cape[i] += 0.26 + float(i) * 0.10
			p.hair[i] += 0.18 + float(i) * 0.07
	elif state in ["channel", "release"]:
		for i in 3:
			p.cape[i] += 0.16
	elif state == "attack":
		for i in 3:
			p.cape[i] += 0.08
