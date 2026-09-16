# SylaraSkillFX.gd — sequencer FX skill Sylara (Godot 4.x Masterwork Rebuild).
#
# Tanggung jawab: Menerjemahkan trigger skill dari Hero / Skeleton menjadi
# rangkaian efek visual bertingkat (PRE-CAST → CHARGE → CAST → IMPACT → AFTERMATH).
#
# Hierarki visual (MASTER PROMPT Section 11):
#   PRIMARY EFFECT (70%) = Bentuk solid (panah angin, sabit pita, sulur, koridor gale)
#   SECONDARY FX   (20%) = Partikel terarah / percikan daun terkontrol via VFXManager
#   ACCENT FX      (10%) = Kilatan flash nock, glint, subtle glow
#
# Performa Android:
#   * Menggunakan VFXManager object pooling — ZERO instantiate/free saat bermain.
#   * Tidak ada _process polling — event-driven lewat notify_drive().
class_name SylaraSkillFX
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

## Posisi frame sebelumnya (diisi root).
var prev_pos := Vector2.ZERO
## Posisi saat skill dimulai.
var _cast_pos := Vector2.ZERO
var _last_skill := ""
var _hero = null


## Hero di-resolve lewat pohon scene (Hero/Visual/<rig>).
func resolve_hero() -> void:
	var n: Node = get_parent()
	if n != null:
		n = n.get_parent()
	if n != null and "kit" in n and "global_position" in n:
		_hero = n


## Dipanggil root tiap drive().
func notify_drive(skill_key: String, hero_pos: Vector2, facing: int,
		_delta: float) -> void:
	if skill_key != "" and skill_key != _last_skill:
		_cast_pos = hero_pos
		_cast(skill_key, hero_pos, facing)
	_last_skill = skill_key


func _cast(key: String, pos: Vector2, facing: int) -> void:
	match key:
		"q":
			_cast_q(pos, facing)
		"w":
			_cast_w(pos, facing)
		"e":
			_cast_e(pos, facing)
		"r":
			_cast_r(pos, facing)


## Hero.gd melewatkan FX skill generik karena Sylara menangani FX-nya sendiri.
func handles_skill_fx(key: String) -> bool:
	return key in ["q", "w", "e", "r"]


# ══════════════════════════════════════════════════════════
#  Q — FOCUS FIRE (Rapid Volley Barrage)
#
#  Urutan panah angin beruntun (5 tembakan cepat), percikan daun
#  pada nock busur, dan impact berbobot di titik target.
# ══════════════════════════════════════════════════════════

func _cast_q(pos: Vector2, facing: int) -> void:
	var bow_pos := pos + Vector2(16.0 * facing, -18.0)

	# 1. PRE-CAST (10% Accent): Flash di nock busur
	VFXManager.flash(bow_pos, 8.0, Pal.WIND_BRIGHT, 0.0, 0.12)
	VFXManager.glow(bow_pos, 16.0, Pal.WIND, 0.0, 0.25)

	# 2. PRIMARY (70%): 5 tembakan beruntun dengan sedikit variasi sudut
	for i in 5:
		var delay := 0.10 + float(i) * 0.18
		var spread_y := -10.0 + float(i % 3) * 6.0 - float(i) * 1.5
		var start := bow_pos + Vector2(float(i) * 6.0 * facing, float(i % 2) * 2.0)
		var end := start + Vector2(160.0 * facing, spread_y)

		# Streak panah angin utama
		VFXManager.streak(start, end, Pal.WIND, delay, 0.22, 4.5)
		# Inti panah cerah
		VFXManager.streak(start, end, Pal.WIND_BRIGHT, delay + 0.02, 0.18, 1.8)

		# Impact di target
		VFXManager.ring(end, 11.0 + float(i) * 1.5, Pal.WIND_LIGHT,
			delay + 0.14, 0.22, 2.0)
		VFXManager.flash(end, 5.5, Pal.WIND_WHITE, delay + 0.14, 0.08)

	# 3. SECONDARY (20%): Percikan daun pada titik pelepasan
	VFXManager.sparks(bow_pos, 0.0 if facing > 0 else PI,
		6, 130.0, Pal.LEAF, 0.08, 0.32, 0.65)

	# 4. AFTERMATH: Cincin aura hembusan angin di kaki
	VFXManager.ring(pos, 40.0, Pal.WIND_DEEP, 0.05, 0.35, 1.6)


# ══════════════════════════════════════════════════════════
#  W — WINDRUN (Gale Aura + Evasion + Speed)
#
#  Gelombang ekspansi daun dan angin melingkar 8-arah, cincin batas
#  aura, siklon hembusan, dan aura pemulihan tanah.
# ══════════════════════════════════════════════════════════

func _cast_w(pos: Vector2, facing: int) -> void:
	var center := pos + Vector2(0.0, -10.0)

	# 1. PRE-CAST & BUFF FLASH (10% Accent)
	VFXManager.flash(center + Vector2(0.0, -10.0), 12.0, Pal.WIND_WHITE, 0.0, 0.16)

	# 2. PRIMARY (70%): Gelombang hembusan melingkar 8-arah
	for i in 8:
		var ang := float(i) * TAU / 8.0
		var dir := Vector2(cos(ang), sin(ang))
		var end := center + dir * 55.0
		VFXManager.streak(center, end, Pal.WIND, 0.0, 0.32, 3.2)

	# Cincin batas aura (radius 70px)
	VFXManager.ring(pos, 70.0, Pal.WIND, 0.04, 0.48, 2.8)
	VFXManager.ring(pos, 52.0, Pal.WIND_LIGHT, 0.08, 0.38, 1.8)

	# Siklon sabit angin berputar di sekeliling Sylara
	for i in 3:
		var ang := float(i) * TAU / 3.0
		VFXManager.slash(center, ang, 26.0, 1.25, Pal.CAPE_LIGHT,
			0.08 + float(i) * 0.06, 0.38, 2.6, 3.2)

	# 3. SECONDARY (20%): Percikan daun melayang ke atas
	VFXManager.sparks(center, HALF_PI, 6, 110.0,
		Pal.LEAF_GOLD, 0.06, 0.42, 1.1)

	# 4. AFTERMATH: Ground healing glow
	VFXManager.glow(pos + Vector2(0, 4), 38.0, Pal.WIND, 0.12, 1.8)


# ══════════════════════════════════════════════════════════
#  E — SHACKLE SHOT (Vine Binding Tether)
#
#  Proyektil sulur bercabang dari busur ke target, meledak menjadi
#  cincin pengikat akar/duri yang melumpuhkan lawan.
# ══════════════════════════════════════════════════════════

func _cast_e(pos: Vector2, facing: int) -> void:
	var bow_pos := pos + Vector2(15.0 * facing, -18.0)
	var target_dist := 170.0
	var end := bow_pos + Vector2(target_dist * facing, 0.0)

	# 1. PRE-CAST (10% Accent): Konsentrasi energi sulur pada grip
	VFXManager.flash(bow_pos, 8.0, Pal.VINE_LIGHT, 0.0, 0.12)
	VFXManager.glow(bow_pos, 16.0, Pal.VINE, 0.0, 0.22)

	# 2. PRIMARY (70%): Dua untai sulur paralel melesat cepat
	VFXManager.streak(bow_pos + Vector2(0, -3.5), end + Vector2(0, -3.5),
		Pal.VINE, 0.06, 0.38, 5.2)
	VFXManager.streak(bow_pos + Vector2(0, 3.5), end + Vector2(0, 3.5),
		Pal.VINE_DARK, 0.10, 0.36, 4.2)
	VFXManager.streak(bow_pos, end,
		Pal.VINE_LIGHT, 0.08, 0.32, 2.0)

	# Impact Shackle di titik target
	var impact_time := 0.32
	VFXManager.ring(end, 20.0, Pal.VINE_LIGHT, impact_time, 0.35, 3.0)
	VFXManager.ring(end, 32.0, Pal.VINE, impact_time + 0.05, 0.40, 2.0)
	VFXManager.flash(end, 10.0, Pal.VINE_LIGHT, impact_time, 0.15)

	# 3. SECONDARY (20%): Node daun merambat sepanjang sulur & burst di target
	for i in 4:
		var t := float(i + 1) / 5.0
		var node_pos := bow_pos.lerp(end, t)
		VFXManager.flash(node_pos + Vector2(0, -4.0), 4.0,
			Pal.LEAF_GOLD, 0.12 + t * 0.18, 0.16)

	VFXManager.sparks(end, HALF_PI, 5, 90.0, Pal.LEAF,
		impact_time, 0.35, 1.2)

	# 4. AFTERMATH: Area lumpuh (glow hijau lumut di tanah)
	VFXManager.glow(end, 24.0, Pal.VINE, impact_time + 0.1, 1.6)


# ══════════════════════════════════════════════════════════
#  R — POWERSHOT (Charged Gale Cone Beam)
#
#  Fase charge: Cincin tekanan menyusut ke nock + daun tersedot.
#  Fase release: Ledakan kerucut 5-panah badai + gale tunnel tebal +
#  screen shake + hit-stop berbobot.
# ══════════════════════════════════════════════════════════

func _cast_r(pos: Vector2, facing: int) -> void:
	var bow_pos := pos + Vector2(14.0 * facing, -18.0)

	# ── 1. CHARGE PHASE (0.0s - 0.45s) ──
	# Cincin tekanan mengecil bertahap
	VFXManager.ring(bow_pos, 48.0, Pal.WIND_DARK, 0.0, 0.55, 3.2)
	VFXManager.ring(bow_pos, 32.0, Pal.WIND, 0.10, 0.45, 2.6)
	VFXManager.ring(bow_pos, 18.0, Pal.WIND_LIGHT, 0.22, 0.35, 2.2)

	# Daun tersedot masuk ke titik nock
	for i in 6:
		var ang := float(i) * TAU / 6.0
		var suction_start := bow_pos + Vector2(cos(ang), sin(ang)) * 52.0
		VFXManager.streak(suction_start, bow_pos, Pal.LEAF,
			0.08 + float(i) * 0.04, 0.32, 2.4)

	# Inti memutih menjelang pelepasan
	VFXManager.flash(bow_pos, 15.0, Pal.WIND_WHITE, 0.32, 0.22)
	VFXManager.glow(bow_pos, 24.0, Pal.WIND_LIGHT, 0.20, 0.45)

	# ── 2. RELEASE PHASE (0.45s) ──
	var rel_delay := 0.45
	var beam_len := 290.0

	# 5 proyektil badai menyebar dalam kerucut (cone)
	for i in 5:
		var spread := (float(i) - 2.0) * 0.12  # ±0.24 rad ≈ ±14°
		var dir := Vector2(cos(spread) * facing, -sin(spread))
		var end := bow_pos + dir * beam_len

		# PRIMARY: Streak badai besar
		VFXManager.streak(bow_pos, end, Pal.WIND,
			rel_delay + float(i) * 0.02, 0.34, 7.5)
		# Inti cahaya putih tajam
		VFXManager.streak(bow_pos, end, Pal.WIND_WHITE,
			rel_delay + float(i) * 0.02 + 0.02, 0.26, 2.8)

	# Gale tunnel di garis tengah
	var main_end := bow_pos + Vector2(beam_len * facing, 0.0)
	VFXManager.streak(bow_pos, main_end, Pal.WIND_LIGHT,
		rel_delay + 0.05, 0.50, 11.0)

	# Secondary impact rings di sepanjang jalur
	for i in 3:
		var t := float(i + 1) / 4.0
		var imp_pos := bow_pos + Vector2(beam_len * facing * t, 0.0)
		VFXManager.ring(imp_pos, 14.0 + float(i) * 5.0, Pal.WIND_LIGHT,
			rel_delay + 0.10 + t * 0.15, 0.28, 2.2)

	# Semburan percikan di busur saat lepas
	var spark_dir := 0.0 if facing > 0 else PI
	VFXManager.sparks(bow_pos, spark_dir, 8, 220.0,
		Pal.WIND_BRIGHT, rel_delay, 0.36, 0.6)

	# ── 3. IMPACT TIER 3 (Camera Shake + Hit-Stop) ──
	VFXManager.impact(main_end, 3, Pal.WIND)
	_shake_camera(0.14)


func _shake_camera(trauma: float) -> void:
	var tree := get_tree()
	if tree != null:
		tree.call_group("camera", "add_trauma", trauma)
