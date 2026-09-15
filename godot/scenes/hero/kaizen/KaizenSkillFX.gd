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
class_name KaizenSkillFX
extends Node2D

const HALF_PI := PI * 0.5
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
	var jumped := prev_pos.distance_to(hero_pos) > 24.0
	if skill_key != "" and skill_key != _last_skill:
		_cast_pos = hero_pos
		_cast(skill_key, hero_pos, facing)
	elif skill_key == "q" and skill_key == _last_skill and jumped:
		# Dash variant TANPA pergantian key (demo memegang "q" untuk segmen
		# Q1→Q2, pemain spam tombol Q dalam jendela active_skill): tanpa
		# cabang ini Q2 Dash Strike menembus tanpa satu FX pun.
		_cast_dash_strike(prev_pos, hero_pos)
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
	# Steel Wind: tebasan sabit ganda di depan (primari besar + susulan),
	# plus mark tanah — bahasa visual v3 (sabit ganda + goresan tanah).
	var fx_pos := pos + Vector2(16.0 * facing, -16.0)
	var base_ang := 0.35 if facing > 0 else PI - 0.35
	var sweep_dir := 1.0 if facing > 0 else -1.0
	VFXManager.flash(fx_pos, 11.0, Pal.WIND_LIGHT, 0.0, 0.12)
	# PRIMARY: sabit utama 52px — searah tebasan turun rig (atas → bawah).
	VFXManager.slash(fx_pos, base_ang + 1.1 * sweep_dir, 52.0,
		-2.8 * sweep_dir, Pal.WIND, 0.02, 0.3, 0.0, 9.0)
	# Susulan 0.05 dtk kemudian — kesan "dua lapis angin".
	VFXManager.slash(fx_pos + Vector2(6.0 * facing, -4.0),
		base_ang + 0.7 * sweep_dir, 44.0, -2.4 * sweep_dir,
		Pal.WIND_LIGHT, 0.07, 0.26, 0.0, 7.0)
	VFXManager.sparks(fx_pos + Vector2(10.0 * facing, 2.0),
		-0.5 if facing > 0 else PI + 0.5, 6, 210.0, Pal.WIND_LIGHT, 0.05, 0.3, 0.5)
	# Mark tanah + ring tekankan LOKASI dan JANGKAUAN skill.
	VFXManager.ring(pos + Vector2(14.0 * facing, -2.0), 46.0, Pal.WIND_DEEP,
		0.02, 0.32, 2.6)
	VFXManager.ring(pos + Vector2(0.0, -12.0), 40.0, Pal.WIND, 0.08, 0.34, 2.4)
	VFXManager.impact(pos + Vector2(24.0 * facing, -14.0), 2, Pal.WIND_BRIGHT)


func _cast_dash_strike(from_pos: Vector2, to_pos: Vector2) -> void:
	var dir := to_pos - from_pos
	var ln := dir.length()
	var dir_ang := 0.0
	if ln > 0.001:
		dir_ang = atan2(-dir.y, dir.x)
	# PRIMARY: streak tebal sepanjang jalur dash (arah + kecepatan terbaca).
	VFXManager.streak(from_pos + Vector2(0.0, -18.0),
		to_pos + Vector2(0.0, -18.0), Pal.WIND, 0.0, 0.3, 11.0)
	VFXManager.streak(from_pos + Vector2(0.0, -12.0),
		to_pos + Vector2(0.0, -12.0), Pal.WIND_LIGHT, 0.03, 0.24, 6.0)
	# SECONDARY: percikan + debu searah dash di titik berangkat.
	VFXManager.sparks(from_pos + Vector2(0.0, -14.0), dir_ang, 5, 170.0,
		Pal.WIND_LIGHT, 0.0, 0.26, 0.4)
	VFXManager.ring(from_pos + Vector2(0.0, -3.0), 26.0, Pal.WIND_DEEP,
		0.0, 0.26, 2.2)
	# IMPACT di titik tiba: sabit ganda + flash + komposit tier 2.
	VFXManager.slash(to_pos + Vector2(0.0, -14.0), dir_ang + 0.9, 44.0,
		-2.4, Pal.WIND, 0.05, 0.3, 0.0, 8.0)
	VFXManager.slash(to_pos + Vector2(0.0, -14.0), dir_ang + 0.5, 36.0,
		-2.0, Pal.WIND_LIGHT, 0.1, 0.26, 0.0, 6.5)
	VFXManager.flash(to_pos + Vector2(0.0, -16.0), 11.0, Pal.WIND_BRIGHT,
		0.05, 0.14)
	VFXManager.impact(to_pos, 2, Pal.WIND_BRIGHT)


# ══════════════════════════════════════════════════════════
#  W — WIND WALL
# ══════════════════════════════════════════════════════════

func _cast_w(pos: Vector2, facing: int) -> void:
	# Dinding mengikuti hero selama buff aktif (kit._wind_wall_timer).
	var anchor: Node2D = get_parent()
	if anchor == null:
		return
	VFXManager.wall(anchor, Vector2(14.0 * facing, -22.0), _wall_duration(),
		34.0, Pal.WIND)
	# Cincin pembentukan + dua hembusan pendek — momen "dinding naik" terbaca.
	VFXManager.ring(pos + Vector2(14.0 * facing, -18.0), 44.0, Pal.WIND_LIGHT,
		0.0, 0.3, 2.6)
	VFXManager.sparks(pos + Vector2(18.0 * facing, -22.0),
		HALF_PI, 4, 140.0, Pal.WIND_BRIGHT, 0.05, 0.3, 0.5)
	VFXManager.sparks(pos + Vector2(18.0 * facing, -22.0),
		HALF_PI, 4, 140.0, Pal.WIND_BRIGHT, 0.7, 0.3, 0.5)
	VFXManager.flash(pos + Vector2(14.0 * facing, -20.0), 13.0,
		Pal.WIND_LIGHT, 0.0, 0.16)


# ══════════════════════════════════════════════════════════
#  E — WHIRLWIND SLASH
# ══════════════════════════════════════════════════════════

func _cast_e(pos: Vector2) -> void:
	var c := pos + Vector2(0.0, -18.0)
	# Dua sabit berlawanan fase berputar mengelilingi tubuh (bentuk utama),
	# ukuran mengikuti radius gameplay E (100px).
	VFXManager.slash(c, 0.6, 62.0, 2.6, Pal.WIND, 0.0, 0.56, TAU * 1.55, 9.0)
	VFXManager.slash(c, 0.6 + PI, 62.0, 2.6, Pal.WIND_LIGHT, 0.06, 0.5,
		TAU * 1.55, 6.5)
	# Sabit susulan tipis — putaran terasa dua kali, bukan sekali.
	VFXManager.slash(c, 0.6 + HALF_PI, 52.0, 2.6, Pal.WIND_BRIGHT, 0.24, 0.4,
		TAU * 1.4, 5.0)
	# Cincin tanah ganda menandai area (readability: DI MANA terjadinya).
	VFXManager.ring(pos + Vector2(0.0, -4.0), 68.0, Pal.WIND, 0.0, 0.5, 3.0)
	VFXManager.ring(pos + Vector2(0.0, -4.0), 52.0, Pal.WIND_DEEP, 0.1, 0.42, 2.2)
	VFXManager.sparks(c, HALF_PI, 8, 190.0, Pal.WIND_BRIGHT, 0.1, 0.32,
		TAU * 0.5)


# ══════════════════════════════════════════════════════════
#  R — TEMPEST FURY (ultimate)
# ══════════════════════════════════════════════════════════

func _cast_r(pos: Vector2) -> void:
	var c := pos + Vector2(0.0, -20.0)
	# PRE CAST (0–0.16): kilat kecil + cahaya terkumpul + cincin hisap.
	VFXManager.flash(c, 14.0, Pal.WIND_LIGHT, 0.0, 0.16)
	VFXManager.glow(pos, 40.0, Pal.WIND_DEEP, 0.0, 0.5)
	VFXManager.ring(pos + Vector2(0.0, -3.0), 44.0, Pal.WIND_LIGHT, 0.0, 0.24,
		2.4)
	# RELEASE (0.16–0.42): tebasan naik vertikal — searah sweep rig
	# (bilah naik lewat depan), ekor streak mengikuti.
	VFXManager.slash(c, HALF_PI + 0.8, 70.0, -2.8, Pal.WIND, 0.16, 0.34,
		0.0, 10.0)
	VFXManager.slash(c, HALF_PI + 0.4, 58.0, -2.4, Pal.WIND_BRIGHT, 0.2, 0.28,
		0.0, 7.0)
	# IMPACT (0.34+): silang-X besar setinggi radius gameplay R (150px)
	# + komposit ultimate (hit-stop + shake ada di VFXManager.impact).
	VFXManager.slash(c, 0.85, 80.0, 3.0, Pal.WIND, 0.3, 0.42, 0.0, 10.0)
	VFXManager.slash(c, PI - 0.85, 80.0, -3.0, Pal.WIND, 0.3, 0.42, 0.0, 10.0)
	VFXManager.ring(c, 96.0, Pal.WIND_LIGHT, 0.34, 0.5, 3.4)
	VFXManager.ring(pos + Vector2(0.0, -3.0), 72.0, Pal.WIND_DEEP, 0.38, 0.46,
		2.6)
	VFXManager.sparks(c, HALF_PI, 10, 260.0, Pal.WIND_BRIGHT, 0.34, 0.36,
		TAU * 0.5)
	VFXManager.impact(c, 3, Pal.WIND_BRIGHT)
	# AFTERMATH: sisa angin memudar pelan (tanpa glow berlebihan).
	VFXManager.glow(pos, 72.0, Pal.WIND, 0.5, 0.7)
