# SylaraSkillFX.gd — sequencer FX skill Sylara (Godot native).
#
# Satu tanggung jawab: menerjemahkan SINYAL root (skill_cast /
# skill_released / bow_released) menjadi rangkaian efek visual bertingkat
# (PRE-CAST → CHARGE → RELEASE → IMPACT → AFTERMATH) via VFXManager.
#
# Pola Godot: node ini TIDAK polling — ia menghubungkan sinyal root di
# _ready() dan bereaksi saat sinyal memancar (event-driven, nol _process).
#
# Hierarki visual:
#   PRIMARY (70%) = bentuk solid (streak panah, kerucut gale, sulur)
#   SECONDARY (20%) = percikan terarah terkontrol
#   ACCENT (10%) = kilatan nock, ring tipis, glow
#
# Anggaran pool (VFXManager = 32 aktor SELURUH arena): tiap skill dibatasi
# ~12 aktor puncak sehingga dua hero yang cast bersamaan tidak saling
# memakan efek. Aura per-durasi (trail Windrun, tether Shackle, cincin
# Focus, garis bidik channel) digambar RENDERER — nol aktor pool.
#
# Bidik: FX diarahkan ke TARGET ASLI hero (bukan offset tetap) dan lahir
# dari nock busur aktual renderer.
class_name SylaraSkillFX
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

var _skel: SylaraSkeleton = null


func _ready() -> void:
	var p := get_parent()
	if p is SylaraSkeleton:
		_skel = p as SylaraSkeleton
		_skel.skill_cast.connect(_on_skill_cast)
		_skel.skill_released.connect(_on_skill_released)
		_skel.bow_released.connect(_on_bow_released)


# ══════════════════════════════════════════════════════════
#  HANDLER SINYAL
# ══════════════════════════════════════════════════════════

func _on_skill_cast(key: String) -> void:
	match key:
		"q":
			_cast_q()
		"w":
			_cast_w()
		"e":
			_cast_e()
		"r":
			_charge_r()


## Powershot TEBAAR — kerucut 5 panah + gale tunnel; impact dijadwalkan
## Feel pada momen mendarat (bukan saat tebar).
func _on_skill_released(key: String, aim_point: Vector2) -> void:
	if key != "r" or _skel == null:
		return
	var nock := _skel.get_bow_nock_global()
	var dir: Vector2 = aim_point - nock
	var ang := 0.0
	if dir.length_squared() > 0.01:
		dir = dir.normalized()
		ang = atan2(-dir.y, dir.x)
	else:
		dir = Vector2(float(_skel.facing), 0.0)
		ang = 0.0 if _skel.facing > 0 else PI
	var beam_len := maxf(dir.length(), 240.0)

	# 5 panah badai menyebar dalam kerucut ±0.6 rad.
	for i in 5:
		var spread := (float(i) - 2.0) * 0.12
		var d := Vector2(cos(ang + spread), -sin(ang + spread))
		VFXManager.streak(nock, nock + d * beam_len, Pal.WIND,
			float(i) * 0.02, 0.34, 7.0)
	# Gale tunnel terang di garis tengah (inti koridor).
	VFXManager.streak(nock, nock + dir * beam_len, Pal.WIND_LIGHT,
		0.05, 0.50, 11.0)
	# Semburan percikan di busur saat lepas.
	VFXManager.sparks(nock, ang, 6, 230.0, Pal.WIND_BRIGHT, 0.0, 0.32, 0.55)


## Tembak cepat Focus Fire: SATU streak tipis per panah (1 aktor, 0.14 dtk).
func _on_bow_released() -> void:
	if _skel == null or not _skel.focus_active():
		return
	var nock := _skel.get_bow_nock_global()
	var t := _skel.get_aim_node()
	if t == null:
		return
	VFXManager.streak(nock, t.global_position + Vector2(0.0, -8.0),
		Pal.WIND, 0.0, 0.14, 3.0)


# ══════════════════════════════════════════════════════════
#  SEKUENS PER-SKILL
# ══════════════════════════════════════════════════════════

## Q — FOCUS FIRE (±6 aktor). Lock-on: kilat nock + streak ke target asli
## + ring impact di target + hembusan kaki. Tiap tembakan berikutnya
## disorot _on_bow_released (1 aktor/panah, durasi pendek).
func _cast_q() -> void:
	var nock := _skel.get_bow_nock_global()
	var t := _skel.get_aim_node()
	var end: Vector2 = _skel.get_aim_point_global(175.0)
	var ang := 0.0
	var d: Vector2 = end - nock
	if d.length_squared() > 0.01:
		ang = atan2(-d.normalized().y, d.normalized().x)

	# 1. PRE-CAST (Accent): kilatan konsentrasi di nock.
	VFXManager.flash(nock, 9.0, Pal.WIND_BRIGHT, 0.0, 0.12)
	# 2. PRIMARY (70%): garis gale ke arah target + impact di target.
	VFXManager.streak(nock, end, Pal.WIND, 0.0, 0.25, 4.0)
	VFXManager.ring(end, 14.0, Pal.WIND_LIGHT, 0.18, 0.26, 2.0)
	if t != null:
		VFXManager.ring(t.global_position, 18.0, Pal.WIND, 0.20, 0.30, 1.6)
	# 3. SECONDARY (20%): percikan daun di titik pelepasan.
	VFXManager.sparks(nock, ang, 5, 120.0, Pal.LEAF, 0.04, 0.30, 0.6)
	# 4. AFTERMATH: cincin hembusan di kaki.
	VFXManager.ring(_skel.global_position, 34.0, Pal.WIND_DEEP, 0.02, 0.4, 1.4)


## W — WINDRUN (±10 aktor). Ledakan gale 6-arah + cincin batas aura
## 70px + daun melayang + glow tanah. Durasi 3 dtk ditopang trail
## renderer (gratis) — bukan aktor pool.
func _cast_w() -> void:
	var pos := _skel.global_position
	var center := pos + Vector2(0.0, -12.0)

	# 1. PRE-CAST & BUFF FLASH (Accent).
	VFXManager.flash(center, 14.0, Pal.WIND_WHITE, 0.0, 0.16)
	# 2. PRIMARY (70%): hembusan 6-arah + cincin batas aura.
	for i in 6:
		var a := float(i) * TAU / 6.0 + 0.26
		var dir := Vector2(cos(a), sin(a))
		VFXManager.streak(center, center + dir * 58.0, Pal.WIND, 0.0, 0.30, 3.0)
	VFXManager.ring(pos, 70.0, Pal.WIND, 0.04, 0.5, 2.6)
	# 3. SECONDARY (20%): daun melayang ke atas.
	VFXManager.sparks(center, HALF_PI, 6, 110.0, Pal.LEAF_GOLD, 0.05, 0.40, 1.1)
	# 4. AFTERMATH: ground glow.
	VFXManager.glow(pos + Vector2(0.0, 4.0), 38.0, Pal.WIND, 0.10, 1.6)


## E — SHACKLE SHOT (±8 aktor). Sulur melesat nock → target, ledak
## menjadi cincin akar; tick damage berikutnya terlihat lewat tether
## renderer (gratis selama 2.5 dtk).
func _cast_e() -> void:
	var nock := _skel.get_bow_nock_global()
	var t := _skel.get_aim_node()
	var end: Vector2 = _skel.get_aim_point_global(200.0)
	if t != null:
		end = t.global_position + Vector2(0.0, -8.0)

	# 1. PRE-CAST (Accent): konsentrasi energi sulur di nock.
	VFXManager.flash(nock, 8.0, Pal.VINE_LIGHT, 0.0, 0.10)
	# 2. PRIMARY (70%): sulur utama + inti terang.
	VFXManager.streak(nock, end, Pal.VINE, 0.05, 0.28, 5.0)
	VFXManager.streak(nock, end, Pal.VINE_LIGHT, 0.07, 0.24, 2.0)
	# 3. IMPACT di target: cincin akar + kilat + percikan daun.
	var impact_time := 0.22
	VFXManager.ring(end, 18.0, Pal.VINE_LIGHT, impact_time, 0.35, 2.6)
	VFXManager.flash(end, 9.0, Pal.VINE_LIGHT, impact_time, 0.12)
	VFXManager.sparks(end, HALF_PI, 5, 90.0, Pal.LEAF, impact_time, 0.35, 1.2)
	# 4. AFTERMATH: area terkunci (glow hijau lumut di tanah).
	VFXManager.glow(end, 24.0, Pal.VINE, impact_time + 0.1, 1.8)


## R — POWERSHOT CHARGE (±7 aktor selama 1 dtk). Cincin tekanan menyusut
## + daun tersedot + inti memutih menjelang tebar. Tebar & impact:
## _on_skill_released + Feel.
func _charge_r() -> void:
	var nock := _skel.get_bow_nock_global()

	VFXManager.ring(nock, 46.0, Pal.WIND_DARK, 0.0, 0.9, 3.0)
	VFXManager.ring(nock, 30.0, Pal.WIND, 0.10, 0.8, 2.4)
	# Daun tersedot masuk ke titik nock (3 untai, terselirah).
	for i in 3:
		var a := float(i) * TAU / 3.0 + 0.5
		var start := nock + Vector2(cos(a), sin(a)) * 52.0
		VFXManager.streak(start, nock, Pal.LEAF,
			0.15 + float(i) * 0.2, 0.25, 2.4)
	# Inti memutih menjelang pelepasan.
	VFXManager.flash(nock, 12.0, Pal.WIND_WHITE, 0.75, 0.25)
	VFXManager.glow(nock, 22.0, Pal.WIND_LIGHT, 0.5, 0.6)
