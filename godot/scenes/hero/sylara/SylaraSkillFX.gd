# SylaraSkillFX.gd — sequencer FX skill Sylara (Godot 4.x).
#
# Tanggung jawab: menerjemahkan trigger skill dari Hero / Skeleton menjadi
# rangkaian efek visual bertingkat (PRE-CAST → CHARGE → CAST → IMPACT →
# AFTERMATH).
#
# Hierarki visual:
#   PRIMARY EFFECT (70%) = bentuk solid (panah angin, aura, sulur, koridor gale)
#   SECONDARY FX   (20%) = percikan terarah terkontrol via VFXManager
#   ACCENT FX      (10%) = kilatan nock, glint, glow tipis
#
# Anggaran pool (VFXManager = 32 aktor untuk SELURUH arena): tiap skill
# dibatasi ±12 aktor konkuren supaya dua hero yang cast bersamaan tidak
# saling memakan efek. Q≈7, W≈12, E≈8, R≈12 (puncak sesaat, lalu meluruh).
#
# Bidik: FX diarahkan ke TARGET ASLI hero bila ada (bukan offset tetap),
# dan lahir dari nock busur aktual renderer (bukan tebakan koordinat).
#
# Performa Android:
#   * VFXManager object pooling — ZERO instantiate/free saat bermain.
#   * Tidak ada _process polling — event-driven lewat notify_drive().
class_name SylaraSkillFX
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

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
		_cast(skill_key, hero_pos, facing)
	_last_skill = skill_key


func _cast(key: String, pos: Vector2, facing: int) -> void:
	_refresh_hero()
	match key:
		"q":
			_cast_q(pos, facing)
		"w":
			_cast_w(pos, facing)
		"e":
			_cast_e(pos, facing)
		"r":
			_cast_r(pos, facing)


func _refresh_hero() -> void:
	if _hero != null and is_instance_valid(_hero):
		return
	resolve_hero()


## Skeleton induk (sumber anchor busur).
func _skel() -> SylaraSkeleton:
	return get_parent() as SylaraSkeleton


## Lapisan feel (penjadwal audio & impact tertunda skill R).
func _feel() -> SylaraCombatFeel:
	var p := get_parent()
	if p == null:
		return null
	return p.get_node_or_null("Feel") as SylaraCombatFeel


## Titik nock busur aktual; fallback offset bila renderer belum siap.
func _nock(pos: Vector2, facing: int) -> Vector2:
	var s := _skel()
	if s != null:
		return s.get_bow_nock_global()
	return pos + Vector2(16.0 * facing, -18.0)


## Arah bidik ke TARGET ASLI (maks `max_len`); fallback arah facing.
## Return [dir, target_pos].
func _aim(pos: Vector2, facing: int, max_len: float) -> Array:
	var dir := Vector2(float(facing), 0.0)
	var tgt: Vector2 = pos + dir * max_len
	if _hero != null and is_instance_valid(_hero):
		var ht = _hero.get("target")
		if ht is Node2D and is_instance_valid(ht) and not bool((ht as Node).get("is_dead")):
			var d: Vector2 = (ht as Node2D).global_position - pos
			if d.length() > 8.0:
				dir = d.normalized()
				tgt = pos + dir * minf(d.length(), max_len)
	return [dir, tgt]


# ══════════════════════════════════════════════════════════
#  Q — FOCUS FIRE (Rapid Volley Barrage, ±7 aktor)
#
#  5 panah angin beruntun ke arah target + SATU impact bersama +
#  percikan daun di nock + hembusan kaki.
# ══════════════════════════════════════════════════════════

func _cast_q(pos: Vector2, facing: int) -> void:
	var nock := _nock(pos, facing)
	var aim: Array = _aim(pos, facing, 175.0)
	var dir: Vector2 = aim[0]
	var tgt: Vector2 = aim[1]
	var perp := Vector2(-dir.y, dir.x)

	# 1. PRE-CAST (10% Accent): flash di nock busur
	VFXManager.flash(nock, 8.0, Pal.WIND_BRIGHT, 0.0, 0.12)

	# 2. PRIMARY (70%): 5 tembakan beruntun, SATU streak per panah
	var spread := [-14.0, -7.0, 0.0, 7.0, 14.0]
	for i in 5:
		var delay := 0.08 + float(i) * 0.15
		var start: Vector2 = nock + perp * (spread[i] * 0.25)
		var end: Vector2 = tgt + perp * spread[i]
		VFXManager.streak(start, end, Pal.WIND, delay, 0.22, 4.5)

	# SATU impact bersama di titik target (bukan 5 ring + 5 flash)
	VFXManager.ring(tgt, 13.0, Pal.WIND_LIGHT, 0.28, 0.24, 2.2)
	VFXManager.flash(tgt, 6.0, Pal.WIND_WHITE, 0.28, 0.09)

	# 3. SECONDARY (20%): percikan daun pada titik pelepasan
	var d_ang := atan2(-dir.y, dir.x)
	VFXManager.sparks(nock, d_ang, 5, 130.0, Pal.LEAF, 0.08, 0.32, 0.65)

	# 4. AFTERMATH: cincin hembusan di kaki
	VFXManager.ring(pos, 40.0, Pal.WIND_DEEP, 0.05, 0.35, 1.6)


# ══════════════════════════════════════════════════════════
#  W — WINDRUN (Gale Aura + Evasion + Speed, ±12 aktor)
#
#  Ledakan hembusan 6-arah + SATU cincin aura + 2 sabit siklon +
#  daun melayang + glow tanah.
# ══════════════════════════════════════════════════════════

func _cast_w(pos: Vector2, _facing: int) -> void:
	var center := pos + Vector2(0.0, -10.0)

	# 1. PRE-CAST & BUFF FLASH (10% Accent)
	VFXManager.flash(center + Vector2(0.0, -10.0), 12.0, Pal.WIND_WHITE, 0.0, 0.16)

	# 2. PRIMARY (70%): hembusan 6-arah + cincin batas aura 70px
	for i in 6:
		var ang := float(i) * TAU / 6.0 + 0.26
		var dir := Vector2(cos(ang), sin(ang))
		var end := center + dir * 55.0
		VFXManager.streak(center, end, Pal.WIND, 0.0, 0.32, 3.2)

	VFXManager.ring(pos, 70.0, Pal.WIND, 0.04, 0.48, 2.8)

	# 2 sabit siklon berputar (cukup 2 — hemat 1 aktor dari sebelumnya 3)
	for i in 2:
		var ang := float(i) * PI + 0.5
		VFXManager.slash(center, ang, 26.0, 1.25, Pal.CAPE_LIGHT,
			0.08 + float(i) * 0.08, 0.38, 2.6, 3.2)

	# 3. SECONDARY (20%): percikan daun melayang ke atas
	VFXManager.sparks(center, HALF_PI, 6, 110.0,
		Pal.LEAF_GOLD, 0.06, 0.42, 1.1)

	# 4. AFTERMATH: ground glow
	VFXManager.glow(pos + Vector2(0, 4), 38.0, Pal.WIND, 0.12, 1.8)


# ══════════════════════════════════════════════════════════
#  E — SHACKLE SHOT (Vine Binding Tether, ±8 aktor)
#
#  Sulur melesat dari nock ke target, meledak menjadi cincin pengikat;
#  impact dirapatkan ke 0.24 dtk (damage & lock instan saat cast).
# ══════════════════════════════════════════════════════════

func _cast_e(pos: Vector2, facing: int) -> void:
	var nock := _nock(pos, facing)
	var aim: Array = _aim(pos, facing, 200.0)
	var end: Vector2 = (aim[1] as Vector2) + Vector2(0.0, -6.0)

	# 1. PRE-CAST (10% Accent): konsentrasi energi sulur pada nock
	VFXManager.flash(nock, 8.0, Pal.VINE_LIGHT, 0.0, 0.12)

	# 2. PRIMARY (70%): sulur utama + inti terang
	VFXManager.streak(nock, end, Pal.VINE, 0.05, 0.30, 5.2)
	VFXManager.streak(nock, end, Pal.VINE_LIGHT, 0.07, 0.26, 2.0)

	# Impact Shackle di titik target
	var impact_time := 0.24
	VFXManager.ring(end, 20.0, Pal.VINE_LIGHT, impact_time, 0.35, 3.0)
	VFXManager.flash(end, 10.0, Pal.VINE_LIGHT, impact_time, 0.15)

	# 3. SECONDARY (20%): node daun merambat + burst di target
	for i in 3:
		var t := float(i + 1) / 4.0
		var node_pos: Vector2 = nock.lerp(end, t)
		VFXManager.flash(node_pos + Vector2(0, -4.0), 4.0,
			Pal.LEAF_GOLD, 0.10 + t * 0.14, 0.16)

	VFXManager.sparks(end, HALF_PI, 5, 90.0, Pal.LEAF,
		impact_time, 0.35, 1.2)

	# 4. AFTERMATH: area lumpuh (glow hijau lumut di tanah)
	VFXManager.glow(end, 24.0, Pal.VINE, impact_time + 0.1, 1.6)


# ══════════════════════════════════════════════════════════
#  R — POWERSHOT (Charged Gale Cone, ±12 aktor puncak)
#
#  CHARGE (0.0–0.45): cincin tekanan menyusut + daun tersedot + inti memutih.
#  RELEASE (0.45): 5 panah badai kerucut + gale tunnel + audio busur.
#  IMPACT (0.95, = momen damage): flash + ring + sparks + hit-stop + shake
#  via Feel (TERJADWAL — bukan instan saat cast seperti sebelumnya).
# ══════════════════════════════════════════════════════════

func _cast_r(pos: Vector2, facing: int) -> void:
	var nock := _nock(pos, facing)
	var aim: Array = _aim(pos, facing, 290.0)
	var base_dir: Vector2 = aim[0]
	var base_ang := atan2(-base_dir.y, base_dir.x)

	# ── 1. CHARGE PHASE (0.0s – 0.45s) ──
	VFXManager.ring(nock, 48.0, Pal.WIND_DARK, 0.0, 0.55, 3.2)
	VFXManager.ring(nock, 32.0, Pal.WIND, 0.10, 0.45, 2.6)

	# Daun tersedot masuk ke titik nock (3 untai)
	for i in 3:
		var ang := float(i) * TAU / 3.0 + 0.5
		var suction_start := nock + Vector2(cos(ang), sin(ang)) * 52.0
		VFXManager.streak(suction_start, nock, Pal.LEAF,
			0.08 + float(i) * 0.05, 0.30, 2.4)

	# Inti memutih menjelang pelepasan
	VFXManager.flash(nock, 15.0, Pal.WIND_WHITE, 0.32, 0.22)
	VFXManager.glow(nock, 24.0, Pal.WIND_LIGHT, 0.20, 0.45)

	# ── 2. RELEASE PHASE (0.45s) ──
	var rel_delay := 0.45
	var beam_len := 290.0

	# 5 proyektil badai menyebar dalam kerucut (±14°)
	for i in 5:
		var spread := (float(i) - 2.0) * 0.12
		var dir := Vector2(cos(base_ang + spread), -sin(base_ang + spread))
		var end := nock + dir * beam_len
		VFXManager.streak(nock, end, Pal.WIND,
			rel_delay + float(i) * 0.02, 0.34, 7.0)

	# Gale tunnel terang di garis tengah (inti koridor)
	var main_end := nock + base_dir * beam_len
	VFXManager.streak(nock, main_end, Pal.WIND_LIGHT,
		rel_delay + 0.05, 0.50, 11.0)

	# Semburan percikan di busur saat lepas
	VFXManager.sparks(nock, base_ang, 5, 220.0,
		Pal.WIND_BRIGHT, rel_delay, 0.36, 0.6)

	# ── 3. AUDIO + IMPACT TERJADWAL (momen damage, bukan cast) ──
	var feel := _feel()
	if feel != null:
		feel.schedule_r_release(rel_delay)
		feel.schedule_r_impact(main_end, base_dir, 0.95)
