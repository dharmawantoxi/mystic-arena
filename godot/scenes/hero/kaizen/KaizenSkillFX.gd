# KaizenSkillFX.gd — sequencer FX skill Kaizen (v4 rebuild).
#
# Tanggung jawab: menerjemahkan transisi skill key dari Hero.gd menjadi
# urutan FX yang terbaca: PRE CAST → CHARGE → CAST → IMPACT → AFTERMATH.
# Semua bentuk datang dari VFXManager (pooled) — TIDAK ada instantiate.
#
# Identitas warna: angin cyan-putih (KaizenPalette.WIND*). Di battlefield
# penuh, skill Kaizen dikenali dari BENTUK SABIT + streak, bukan dari
# jumlah partikel.
#
# Node ini TIDAK menjalankan _process: semua berjalan lewat
# notify_drive() (dari root) + parameter `delay` di VFXActor.
extends Node2D

const Pal = preload("res://scenes/hero/kaizen/KaizenPalette.gd")

## Posisi frame sebelumnya (diisi root) — untuk deteksi teleport dash Q2.
var prev_pos := Vector2.ZERO
## Posisi saat skill dimulai (untuk streak/aftermath).
var _cast_pos := Vector2.ZERO
var _last_skill := ""
var _hero = null


## Hero di-resolve lewat pohon scene (rig dipasang di Hero/Visual).
## Di scene demo tidak ada hero -> null (FX tetap jalan dengan durasi baku).
func resolve_hero() -> void:
	var n: Node = get_parent()
	if n != null:
		n = n.get_parent()
	if n != null and "kit" in n and "global_position" in n:
		_hero = n


func _wall_duration() -> float:
	if _hero != null and is_instance_valid(_hero):
		var frames = _hero.kit.get("_wind_wall_timer", 0)
		if int(frames) > 0:
			return float(int(frames)) / 60.0
	return 3.0


## Dipanggil root tiap drive(). hero_pos/facing = kondisi root frame ini.
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
			_cast_e(pos)
		"r":
			_cast_r(pos)


# ══════════════════════════════════════════════════════════
#  Q — STEEL WIND / DASH STRIKE
# ══════════════════════════════════════════════════════════

func _cast_q(pos: Vector2, facing: int) -> void:
	# Dash strike memindahkan hero 70% jarak ke target SEBELUM frame ini:
	# lompatan posisi = varian dash (tanpa perlu membaca kit).
	var jumped := prev_pos.distance_to(pos) > 24.0
	if jumped:
		_cast_dash_strike(prev_pos, pos)
		return
	# Steel Wind: tebasan sabit di depan — bentuk utama besar & bersih.
	var fx_pos := pos + Vector2(16.0 * facing, -16.0)
	var base_ang := 0.35 if facing > 0 else PI - 0.35
	var sweep_dir := 1.0 if facing > 0 else -1.0
	VFXManager.flash(fx_pos, 9.0, Pal.WIND_LIGHT, 0.0, 0.12)
	VFXManager.slash(fx_pos, base_ang + 0.9 * sweep_dir, 34.0,
		-2.6 * sweep_dir, Pal.WIND, 0.02, 0.32, 0.0, 7.0)
	VFXManager.sparks(fx_pos + Vector2(8.0 * facing, 0.0),
		0.0 if facing > 0 else PI, 6, 190.0, Pal.WIND_LIGHT, 0.06, 0.3, 0.55)
	VFXManager.ring(pos + Vector2(0.0, -12.0), 40.0, Pal.WIND, 0.08, 0.34, 2.4)
	VFXManager.impact(pos + Vector2(22.0 * facing, -14.0), 1, Pal.WIND_BRIGHT)


func _cast_dash_strike(from_pos: Vector2, to_pos: Vector2) -> void:
	var dir := to_pos - from_pos
	var ln := dir.length()
	var dir_ang := 0.0
	if ln > 0.001:
		dir_ang = atan2(-dir.y, dir.x)
	# PRIMARY: streak sepanjang jalur dash (informasi arah + kecepatan).
	VFXManager.streak(from_pos + Vector2(0.0, -18.0),
		to_pos + Vector2(0.0, -18.0), Pal.WIND, 0.0, 0.3, 7.0)
	# SECONDARY: percikan searah dash di titik berangkat.
	VFXManager.sparks(from_pos + Vector2(0.0, -14.0), dir_ang, 4, 150.0,
		Pal.WIND_LIGHT, 0.0, 0.26, 0.4)
	# IMPACT di titik tiba: sabit + komposit tier 1.
	VFXManager.slash(to_pos + Vector2(0.0, -14.0), dir_ang + 0.9, 30.0,
		-2.4, Pal.WIND, 0.05, 0.3, 0.0, 6.5)
	VFXManager.flash(to_pos + Vector2(0.0, -16.0), 8.0, Pal.WIND_BRIGHT,
		0.05, 0.12)
	VFXManager.impact(to_pos, 1, Pal.WIND_BRIGHT)


# ══════════════════════════════════════════════════════════
#  W — WIND WALL
# ══════════════════════════════════════════════════════════

func _cast_w(pos: Vector2, facing: int) -> void:
	# Dinding mengikuti hero selama buff aktif (kit._wind_wall_timer).
	var anchor: Node2D = get_parent()
	if anchor == null:
		return
	VFXManager.wall(anchor, Vector2(14.0 * facing, -20.0), _wall_duration(),
		26.0, Pal.WIND)
	# Dua hembusan pendek saat dinding terbentuk — pembentukan terbaca.
	VFXManager.sparks(pos + Vector2(18.0 * facing, -22.0),
		HALF_PI, 3, 120.0, Pal.WIND_BRIGHT, 0.05, 0.3, 0.5)
	VFXManager.sparks(pos + Vector2(18.0 * facing, -22.0),
		HALF_PI, 3, 120.0, Pal.WIND_BRIGHT, 0.7, 0.3, 0.5)
	VFXManager.flash(pos + Vector2(14.0 * facing, -20.0), 10.0,
		Pal.WIND_LIGHT, 0.0, 0.16)


# ══════════════════════════════════════════════════════════
#  E — WHIRLWIND SLASH
# ══════════════════════════════════════════════════════════

func _cast_e(pos: Vector2) -> void:
	var c := pos + Vector2(0.0, -18.0)
	# Dua sabit berlawanan fase berputar mengelilingi tubuh (bentuk utama).
	VFXManager.slash(c, 0.6, 46.0, 2.4, Pal.WIND, 0.0, 0.56, TAU * 1.55, 7.5)
	VFXManager.slash(c, 0.6 + PI, 46.0, 2.4, Pal.WIND_LIGHT, 0.06, 0.5,
		TAU * 1.55, 5.5)
	# Cincin tanah menandai area (readability: DI MANA terjadinya).
	VFXManager.ring(pos + Vector2(0.0, -4.0), 52.0, Pal.WIND, 0.0, 0.5, 2.8)
	VFXManager.sparks(c, HALF_PI, 6, 170.0, Pal.WIND_BRIGHT, 0.1, 0.32,
		TAU * 0.5)


# ══════════════════════════════════════════════════════════
#  R — TEMPEST FURY (ultimate)
# ══════════════════════════════════════════════════════════

func _cast_r(pos: Vector2) -> void:
	var c := pos + Vector2(0.0, -20.0)
	# PRE CAST (0–0.16): kilat kecil + cahaya terkumpul.
	VFXManager.flash(c, 12.0, Pal.WIND_LIGHT, 0.0, 0.16)
	VFXManager.glow(pos, 34.0, Pal.WIND_DEEP, 0.0, 0.5)
	# RELEASE (0.16–0.42): tebasan naik vertikal.
	VFXManager.slash(c, HALF_PI + 0.8, 54.0, -2.6, Pal.WIND, 0.16, 0.34,
		0.0, 8.0)
	# IMPACT (0.34+): silang-X besar + komposit ultimate
	# (hit-stop singkat + shake proporsional ada di VFXManager.impact).
	VFXManager.slash(c, 0.85, 62.0, 2.9, Pal.WIND, 0.3, 0.42, 0.0, 8.5)
	VFXManager.slash(c, PI - 0.85, 62.0, -2.9, Pal.WIND, 0.3, 0.42, 0.0, 8.5)
	VFXManager.ring(c, 78.0, Pal.WIND_LIGHT, 0.34, 0.5, 3.2)
	VFXManager.sparks(c, HALF_PI, 8, 240.0, Pal.WIND_BRIGHT, 0.34, 0.36,
		TAU * 0.5)
	VFXManager.impact(c, 3, Pal.WIND_BRIGHT)
	# AFTERMATH: sisa angin memudar pelan (tanpa glow berlebihan).
	VFXManager.glow(pos, 56.0, Pal.WIND, 0.5, 0.7)
