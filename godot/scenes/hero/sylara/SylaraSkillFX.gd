# SylaraSkillFX.gd — sequencer FX skill Sylara (Godot 4.x rebuild).
#
# Tanggung jawab: menerjemahkan transisi skill key dari Hero.gd menjadi
# urutan FX yang terbaca: PRE CAST → CHARGE → CAST → IMPACT → AFTERMATH.
# Semua bentuk datang dari VFXManager (pooled) — TIDAK ada instantiate.
#
# Identitas warna: hijau angin + emas daun (SylaraPalette.WIND*/LEAF*).
# Di battlefield penuh, skill Sylara dikenali dari BENTUK PANAH + CINCIN
# DAUN + SULUR, bukan dari jumlah partikel.
#
# Node ini TIDAK menjalankan _process: semua berjalan lewat
# notify_drive() (dari root) + parameter `delay` di VFXActor.
class_name SylaraSkillFX
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

## Posisi frame sebelumnya (diisi root).
var prev_pos := Vector2.ZERO
## Posisi saat skill dimulai (untuk streak/aftermath).
var _cast_pos := Vector2.ZERO
var _last_skill := ""
var _hero = null


## Hero di-resolve lewat pohon scene (rig dipasang di Hero/Visual).
func resolve_hero() -> void:
	var n: Node = get_parent()
	if n != null:
		n = n.get_parent()
	if n != null and "kit" in n and "global_position" in n:
		_hero = n


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
			_cast_e(pos, facing)
		"r":
			_cast_r(pos, facing)


## Dipanggil root saat handles_skill_fx dibutuhkan Hero.gd.
func handles_skill_fx(key: String) -> bool:
	return key in ["q", "w", "e", "r"]


# ══════════════════════════════════════════════════════════
#  Q — FOCUS FIRE (rapid volley)
#
#  Kipas pita angin dari nock, daun tersedot, koridor volley +
#  chevron berjalan di tanah. Durasi 180 frame (3.0 detik).
# ══════════════════════════════════════════════════════════

func _cast_q(pos: Vector2, facing: int) -> void:
	var fx_pos := pos + Vector2(18.0 * facing, -18.0)
	# PRE CAST: flash di nock — tanda skill dimulai.
	VFXManager.flash(pos + Vector2(8.0 * facing, -20.0), 8.0,
		Pal.WIND_LIGHT, 0.0, 0.14)
	# PRIMARY: sabit kipas — 3 lapis berurutan, mewakili volley panah.
	for i in 5:
		var delay := 0.12 + float(i) * 0.22
		var ang := 0.2 + float(i) * 0.08 if facing > 0 else PI - 0.2 - float(i) * 0.08
		var sweep_dir := 1.0 if facing > 0 else -1.0
		# Panah FX — streak pendek.
		var start := fx_pos + Vector2(float(i) * 12.0 * facing, -float(i) * 2.0)
		var end := start + Vector2(80.0 * facing, -10.0 + float(i) * 5.0)
		VFXManager.streak(start, end, Pal.WIND, delay, 0.2, 4.0)
		# Impact ring di ujung.
		VFXManager.ring(end, 12.0 + float(i) * 3.0, Pal.WIND_LIGHT,
			delay + 0.15, 0.25, 2.0)
	# SECONDARY: percikan daun di titik tembak.
	VFXManager.sparks(fx_pos, -0.3 if facing > 0 else PI + 0.3,
		6, 140.0, Pal.LEAF, 0.08, 0.35, 0.8)
	# AFTERMATH: cincin tipis di kaki — jangkauan skill.
	VFXManager.ring(pos, 42.0, Pal.WIND_DEEP, 0.05, 0.4, 1.8)
	# ACCENT: kilau kecil di ujung tiap streak.
	for i in 3:
		var end := fx_pos + Vector2(80.0 * facing + float(i) * 10.0 * facing,
			-10.0 + float(i) * 8.0)
		VFXManager.flash(end, 5.0, Pal.WIND_BRIGHT,
			0.25 + float(i) * 0.2, 0.1)


# ══════════════════════════════════════════════════════════
#  W — WINDRUN (speed + heal aura)
#
#  Ledakan daun melingkar, halo rumput r=70 dunia, siklon daun
#  mengencang, lembar angin dash. Durasi 180 frame (3.0 detik).
# ══════════════════════════════════════════════════════════

func _cast_w(pos: Vector2, facing: int) -> void:
	# PRIMARY: ledakan daun melingkar — 8 arah, terkontrol.
	for i in 8:
		var ang := float(i) * TAU / 8.0
		var dir := Vector2(cos(ang), sin(ang))
		var end := pos + dir * 55.0
		VFXManager.streak(pos + Vector2(0, -8), end + Vector2(0, -8),
			Pal.LEAF, 0.0, 0.35, 3.0)
	# SECONDARY: cincin ekspansi — batas aura.
	VFXManager.ring(pos, 70.0, Pal.WIND, 0.05, 0.5, 2.6)
	VFXManager.ring(pos, 50.0, Pal.WIND_LIGHT, 0.1, 0.4, 1.8)
	# ACCENT: percikan daun ke atas.
	VFXManager.sparks(pos + Vector2(0, -12), HALF_PI, 5, 100.0,
		Pal.LEAF_GOLD, 0.08, 0.4, 1.2)
	# AFTERMATH: glow lembut di tanah — aura penyembuhan.
	VFXManager.glow(pos + Vector2(0, 4), 40.0, Pal.WIND, 0.15, 2.5)
	# Flash di hero — tanda buff aktif.
	VFXManager.flash(pos + Vector2(0, -20), 10.0, Pal.WIND_BRIGHT, 0.0, 0.16)
	# Siklon kecil — 3 slash berputar di sekeliling hero.
	for i in 3:
		var ang := float(i) * TAU / 3.0
		VFXManager.slash(pos + Vector2(0, -10), ang, 28.0,
			1.2, Pal.CAPE_LIGHT, 0.1 + float(i) * 0.06, 0.4, 2.5, 3.5)


# ══════════════════════════════════════════════════════════
#  E — SHACKLE SHOT (vine projectile stun)
#
#  Dua untai sulur berkelok dari busur ke target + daun merambat,
#  halo rumput di kaki target, impact vine. Durasi 150 frame (2.5 detik).
# ══════════════════════════════════════════════════════════

func _cast_e(pos: Vector2, facing: int) -> void:
	var fx_pos := pos + Vector2(14.0 * facing, -18.0)
	# PRE CAST: flash di bow grip — energi sulur berkumpul.
	VFXManager.flash(fx_pos, 7.0, Pal.VINE_LIGHT, 0.0, 0.12)
	# PRIMARY: sulur melesat — streak hijau dari bow ke depan.
	var target_dist := 160.0  # range E = 200 dunia
	var end := fx_pos + Vector2(target_dist * facing, 0.0)
	# Dua untai sulur — paralel, sedikit offset.
	VFXManager.streak(fx_pos + Vector2(0, -3),
		end + Vector2(0, -3), Pal.VINE, 0.08, 0.4, 5.0)
	VFXManager.streak(fx_pos + Vector2(0, 3),
		end + Vector2(0, 3), Pal.VINE_DARK, 0.12, 0.38, 4.0)
	# SECONDARY: impact di ujung — cincin sulur.
	VFXManager.ring(end, 18.0, Pal.VINE_LIGHT, 0.35, 0.35, 2.8)
	VFXManager.flash(end + Vector2(0, -4), 9.0, Pal.VINE_LIGHT, 0.32, 0.14)
	# Percikan daun di titik impact.
	VFXManager.sparks(end, HALF_PI, 4, 80.0, Pal.LEAF, 0.3, 0.3, 1.0)
	# AFTERMATH: glow di tanah titik impact — shackle zone.
	VFXManager.glow(end, 22.0, Pal.VINE, 0.4, 1.8)
	# Daun merambat — percikan kecil sepanjang jalur.
	for i in 4:
		var t := float(i) / 4.0
		var leaf_pos := fx_pos.lerp(end, t + 0.1)
		VFXManager.flash(leaf_pos + Vector2(0, -6), 3.5,
			Pal.LEAF_GOLD, 0.15 + t * 0.2, 0.18)


# ══════════════════════════════════════════════════════════
#  R — POWERSHOT (charged cone gale)
#
#  Cincin tekanan mengecil + inti memutih, lalu RELEASE: 5 proyektil
#  gale, gale tunnel, shake 9.0, hit-stop 0.062 s.
#  Durasi 60 frame charge (1.0 detik) + aftermath.
# ══════════════════════════════════════════════════════════

func _cast_r(pos: Vector2, facing: int) -> void:
	var fx_pos := pos + Vector2(10.0 * facing, -18.0)
	# CHARGE PHASE: cincin tekanan mengecil — energi terkonsentrasi.
	VFXManager.ring(fx_pos, 45.0, Pal.WIND_DARK, 0.0, 0.6, 3.0)
	VFXManager.ring(fx_pos, 30.0, Pal.WIND, 0.1, 0.5, 2.4)
	VFXManager.ring(fx_pos, 18.0, Pal.WIND_LIGHT, 0.2, 0.4, 2.0)
	# Inti memutih — konsentrasi energi.
	VFXManager.flash(fx_pos, 14.0, Pal.WIND_BRIGHT, 0.35, 0.25)
	VFXManager.glow(fx_pos, 20.0, Pal.WIND, 0.2, 0.5)
	# Daun tersedot ke dalam — sparks mengarah ke pusat.
	for i in 6:
		var ang := float(i) * TAU / 6.0
		var start := fx_pos + Vector2(cos(ang), sin(ang)) * 50.0
		VFXManager.streak(start, fx_pos, Pal.LEAF,
			0.1 + float(i) * 0.04, 0.35, 2.5)
	# RELEASE: 5 panah gale menyebar cone 30°.
	var release_delay := 0.5
	for i in 5:
		var spread := (float(i) - 2.0) * 0.13  # ±0.26 rad ≈ 15° per sisi
		var dir := Vector2(cos(spread) * facing, -sin(spread))
		var end := fx_pos + dir * 280.0
		# PRIMARY: gale streak — besar, kuat.
		VFXManager.streak(fx_pos, end, Pal.WIND,
			release_delay + float(i) * 0.03, 0.35, 8.0)
		# Inti terang.
		VFXManager.streak(fx_pos, end, Pal.WIND_BRIGHT,
			release_delay + float(i) * 0.03 + 0.02, 0.28, 3.0)
	# Impact besar di ujung cone — tier 2 (skill).
	var impact_center := fx_pos + Vector2(260.0 * facing, 0.0)
	VFXManager.impact(impact_center, 2, Pal.WIND)
	# AFTERMATH: gale tunnel — garis angin panjang.
	VFXManager.streak(fx_pos, fx_pos + Vector2(280.0 * facing, 0.0),
		Pal.WIND_LIGHT, release_delay + 0.2, 0.6, 12.0)
	# Secondary impacts di sepanjang cone.
	for i in 3:
		var t := float(i + 1) / 4.0
		var imp_pos := fx_pos + Vector2(280.0 * facing * t, 0.0)
		VFXManager.ring(imp_pos, 14.0 + float(i) * 4.0, Pal.WIND_LIGHT,
			release_delay + 0.15 + t * 0.2, 0.3, 2.0)
	# Percikan di titik release.
	VFXManager.sparks(fx_pos, facing > 0.0 ? 0.0 : PI, 8, 200.0,
		Pal.WIND_LIGHT, release_delay, 0.35, 0.6)
	# Camera shake tier 3 — Powershot adalah ultimate.
	# (VFXManager.impact sudah menangani shake untuk tier 2+, tapi
	#  Powershot layak mendapat shake ekstra.)
	_shake_camera(0.12)


func _shake_camera(trauma: float) -> void:
	var tree := get_tree()
	if tree != null:
		tree.call_group("camera", "add_trauma", trauma)
