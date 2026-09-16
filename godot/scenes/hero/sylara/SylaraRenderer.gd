# SylaraRenderer.gd — renderer prosedural pixel-art fantasy Sylara (Godot 4.x).
#
# Satu-satunya tugas: menggambar karakter Sylara dari SylaraPose lewat _draw().
#
# Standar Visual: High-Polish Pixel-Art Fantasy Heroine (selaras dengan Kaizen & sprite orisinal):
#   * Tudung elven beludru hijau hutan berbordir emas yang membingkai wajah elven
#   * Wajah cantik elven 3/4 view: kulit porselen hangat, mata zamrud fokus berbinar,
#     hidung & bibir manis, telinga runcing elven berhias anting emas
#   * Rambut auburn tembaga berombak alami dengan poni dan sidelock membingkai pipi
#   * Korset kulit petualang elven dengan tali silang & gesper emas
#   * Tunik sutra hijau kelopak dengan belahan berpiping emas
#   * Celana ketat & knee-high leather boots ber-cuff terlipat dengan strap emas
#   * Quiver kulit di punggung dengan 4 fletching bulu zamrud elven
#   * Busur pusaka recurve kayu pusaka dengan urat emas, ujung tanduk gading,
#     dan tali sihir angin berkilau mint dengan efek tarikan tali dinamis
#   * Bayangan kontak tanah, rim light dingin, dan partikel aura angin laminar
#
# 100% KODE tanpa aset eksternal. Semua koordinat di-snap ke piksel bulat
# (_sn) untuk ketajaman kristal di semua tingkat zoom kamera (Android & PC).
class_name SylaraRenderer
extends Node2D

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

# ── Metrik tubuh elven proporsional (pixel art; anchor = tanah di antara dua kaki) ──
const HIP_Y := -26.0
const SPINE_LEN := 12.0
const CHEST_LEN := 8.5
const HEAD_R := 6.5
const LEG_UPPER := 12.0
const LEG_LOWER := 11.0
const FOOT_LEN := 6.5
const ARM_UPPER := 9.0
const ARM_LOWER := 8.5
const BOW_LEN := 23.5        # panjang setengah busur recurve (grip → tip)
const CAPE_SEGS: Array = [9.0, 9.0, 10.5]
const CAPE_W: Array = [6.0, 5.2, 4.0]
const HOOD_SEGS: Array = [5.5, 5.0]
const HAIR_SEGS: Array = [8.5, 7.5, 7.5]
const HAIR_W: Array = [4.2, 3.2, 2.0]

## Pose aktif (di-set root tiap frame sebelum queue_redraw).
var pose: SylaraPose = null
## Fase global (untuk rotasi aura angin, wisp angin & shimmer).
var phase := 0.0

## Cache geometri busur — dipakai SkillFX / Skeleton untuk anchor nock/tip/grip.
var _bow_grip := Vector2.ZERO
var _bow_tip := Vector2.ZERO
var _bow_nock := Vector2.ZERO
var _bow_dir := Vector2.RIGHT


func get_bow_grip() -> Vector2:
	return _bow_grip


func get_bow_tip() -> Vector2:
	return _bow_tip


func get_bow_nock() -> Vector2:
	return _bow_nock


func get_bow_dir() -> Vector2:
	return _bow_dir


func _draw() -> void:
	if pose == null:
		return
	var p: SylaraPose = pose
	if p.alpha <= 0.02:
		return
	var j: Dictionary = _solve(p)

	# 0. AMBIENT MAGIC & GROUND SHADOW
	_draw_ground_magic(p)
	_draw_shadow(p, j)

	# 1. BACK (lapisan belakang: jubah, rambut, quiver, kaki/lengan belakang)
	_draw_cape(p, j)
	_draw_hair(p, j)
	_draw_quiver(j)
	_draw_arm(p, j, true)
	_draw_calf(p, j, true)

	# 2. BODY (lapisan kaki depan, sepatu bot, tunik & torso)
	_draw_calf(p, j, false)
	_draw_feet(j)
	_draw_tunic(p, j)
	_draw_torso(p, j)

	# 3. ARMOR & KORSET (korset kulit petualang, sabuk gesper emas, mantle bahu)
	_draw_belt(j)
	_draw_corset(j)
	_draw_mantle(j)

	# 4. KEPALA & WAJAH CANTIK (tudung elven, wajah tirus, mata zamrud, rambut)
	_draw_head_and_hood(p, j)

	# 5. WEAPON (lengan depan, pauldron bahu, busur recurve pusaka)
	_draw_arm(p, j, false)
	_draw_bow(p, j)

	# 6. HIGHLIGHT & MAGIC ACCENT
	_draw_rim(j)
	_draw_wind_wisps(p, j)

	# 7. FEEDBACK DAMAGE
	if p.hurt_tint > 0.01:
		_draw_hurt_flash(p, j)


# ══════════════════════════════════════════════════════════
#  FK — satu sumber kebenaran posisi tulang
# ══════════════════════════════════════════════════════════

static func _down(a: float) -> Vector2:
	return Vector2(sin(a), cos(a))


static func _fwd(a: float) -> Vector2:
	return Vector2(cos(a), -sin(a))


func _solve(p: SylaraPose) -> Dictionary:
	var hip: Vector2 = Vector2(p.root_x, HIP_Y + p.root_y)
	var up1: Vector2 = Vector2(sin(p.torso_lean), -cos(p.torso_lean))
	var chest: Vector2 = hip + up1 * SPINE_LEN
	var up2: Vector2 = Vector2(sin(p.torso_lean + p.chest_flex),
		-cos(p.torso_lean + p.chest_flex))
	var neck: Vector2 = chest + up2 * CHEST_LEN
	var head_c: Vector2 = neck + up2 * HEAD_R
	var sh_f: Vector2 = chest + Vector2(4.4, -0.6)
	var sh_b: Vector2 = chest + Vector2(-4.4, -1.2)
	var hip_f: Vector2 = hip + Vector2(3.2, 1.8)
	var hip_b: Vector2 = hip + Vector2(-3.2, 2.2)

	var knee_f: Vector2 = hip_f + _down(p.leg_f_hip) * LEG_UPPER
	var ankle_f: Vector2 = knee_f + _down(p.leg_f_hip + p.leg_f_knee) * LEG_LOWER
	var toe_f: Vector2 = ankle_f + _fwd(p.leg_f_foot) * FOOT_LEN

	var knee_b: Vector2 = hip_b + _down(p.leg_b_hip) * LEG_UPPER
	var ankle_b: Vector2 = knee_b + _down(p.leg_b_hip + p.leg_b_knee) * LEG_LOWER
	var toe_b: Vector2 = ankle_b + _fwd(p.leg_b_foot) * FOOT_LEN

	var elb_f: Vector2 = sh_f + _down(p.arm_f_sh) * ARM_UPPER
	var hand_f: Vector2 = elb_f + _down(p.arm_f_sh + p.arm_f_el) * ARM_LOWER + p.bow_off
	var elb_b: Vector2 = sh_b + _down(p.arm_b_sh) * ARM_UPPER
	var hand_b: Vector2 = elb_b + _down(p.arm_b_sh + p.arm_b_el) * ARM_LOWER

	var bow_dir: Vector2 = _fwd(p.bow_angle)
	var bow_perp: Vector2 = Vector2(-bow_dir.y, bow_dir.x)
	_bow_dir = bow_dir
	_bow_grip = hand_f
	_bow_tip = hand_f + bow_dir * BOW_LEN
	var bow_mid: Vector2 = hand_f + bow_dir * BOW_LEN * 0.5
	_bow_nock = hand_f - bow_perp * (p.bow_draw * 11.5)

	var j := {
		"hip": hip, "chest": chest, "neck": neck, "head_c": head_c,
		"sh_f": sh_f, "sh_b": sh_b, "hip_f": hip_f, "hip_b": hip_b,
		"knee_f": knee_f, "knee_b": knee_b,
		"ankle_f": ankle_f, "ankle_b": ankle_b,
		"toe_f": toe_f, "toe_b": toe_b,
		"elb_f": elb_f, "elb_b": elb_b,
		"hand_f": hand_f, "hand_b": hand_b,
		"bow_grip": hand_f, "bow_tip": _bow_tip,
		"bow_mid": bow_mid, "bow_nock": _bow_nock,
		"bow_dir": bow_dir, "bow_perp": bow_perp,
	}
	_clamp_ground(j)
	return j


static func _clamp_ground(j: Dictionary) -> void:
	for key in ["hip", "chest", "neck", "head_c", "knee_f", "ankle_f", "toe_f",
			"knee_b", "ankle_b", "toe_b", "elb_f", "hand_f", "elb_b", "hand_b"]:
		var pt: Vector2 = j[key]
		if pt.y > -0.5:
			j[key] = Vector2(pt.x, -0.5)


# ══════════════════════════════════════════════════════════
#  PRIMITIF PIXEL-ART
# ══════════════════════════════════════════════════════════

func _c(col: Color) -> Color:
	if pose == null or pose.alpha >= 0.999:
		return col
	return Color(col.r, col.g, col.b, col.a * pose.alpha)


static func _sn(v: Vector2) -> Vector2:
	return v.round()


func _poly(pts: PackedVector2Array, col: Color) -> void:
	for i in pts.size():
		pts[i] = _sn(pts[i])
	draw_colored_polygon(pts, _c(col))


func _capsule(a: Vector2, b: Vector2, w: float, col: Color,
		outline: bool = true, outline_col: Color = Pal.INK) -> void:
	var pts := _capsule_pts(a, b, w)
	if outline:
		_poly(_capsule_pts(a, b, w + 2.2), outline_col)
	_poly(pts, col)


func _capsule_pts(a: Vector2, b: Vector2, w: float) -> PackedVector2Array:
	var d := (b - a)
	var ln := d.length()
	if ln < 0.001:
		d = Vector2(0.001, 0.0)
		ln = 0.001
	d /= ln
	var n := Vector2(-d.y, d.x)
	var h := w * 0.5
	return PackedVector2Array([
		a - d * h + n * h, a + n * h, b + n * h,
		b + d * h, b - n * h, a - n * h,
	])


func _taper(a: Vector2, wa: float, b: Vector2, wb: float, col: Color,
		outline: bool = true, outline_col: Color = Pal.INK) -> void:
	if outline:
		_poly(_taper_pts(a, wa + 2.2, b, wb + 2.2), outline_col)
	_poly(_taper_pts(a, wa, b, wb), col)


func _taper_pts(a: Vector2, wa: float, b: Vector2, wb: float) -> PackedVector2Array:
	var d := b - a
	var ln := d.length()
	if ln < 0.001:
		d = Vector2(0.001, 0.0)
	else:
		d /= ln
	var n := Vector2(-d.y, d.x)
	var ha := wa * 0.5
	var hb := wb * 0.5
	return PackedVector2Array([
		a + n * ha, b + n * hb, b - d * hb, b - n * hb, a - n * ha, a - d * ha,
	])


# ══════════════════════════════════════════════════════════
#  0. AMBIENT GROUND MAGIC & SHADOW
# ══════════════════════════════════════════════════════════

func _draw_ground_magic(p: SylaraPose) -> void:
	var c := Vector2(p.root_x * 0.35, 0.0)
	var rot := phase * 0.70

	var ring_col := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.18 * p.alpha)
	var glow_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.28 * p.alpha)

	for i in 3:
		var start_a: float = rot + float(i) * TAU / 3.0
		var end_a: float = start_a + 1.2
		draw_arc(c, 20.0, start_a, end_a, 12, ring_col, 1.2, true)
		var glyph_p: Vector2 = c + Vector2(cos(end_a), sin(end_a) * 0.45) * 20.0
		draw_circle(glyph_p, 1.2, glow_col)

	for i in 3:
		var a: float = rot * 1.3 + float(i) * TAU / 3.0
		var r: float = 16.0 + sin(phase * 2.0 + float(i)) * 3.0
		var lp: Vector2 = c + Vector2(cos(a) * r, sin(a) * (r * 0.42) - 2.0)
		var leaf_c := Pal.LEAF_GOLD if (i % 2 == 0) else Pal.LEAF
		draw_circle(lp, 1.0, Color(leaf_c.r, leaf_c.g, leaf_c.b, 0.45 * p.alpha))


func _draw_shadow(p: SylaraPose, _j: Dictionary) -> void:
	var rx := 14.0 + absf(p.root_x) * 0.3
	var c := Vector2(p.root_x * 0.5, 1.0)
	var pts := PackedVector2Array()
	for i in 14:
		var a := float(i) * TAU / 14.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * 3.8))
	_poly(pts, Pal.SHADOW_GROUND)


# ══════════════════════════════════════════════════════════
#  1. CAPE (Jubah Angin Berlapis Berbordir Emas)
# ══════════════════════════════════════════════════════════

func _draw_cape(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["chest"] as Vector2) + Vector2(-3.4, -2.0)
	var prev := anchor

	# Lapisan dalam jubah
	for i in 3:
		var seg_len: float = float(CAPE_SEGS[i])
		var seg_w: float = float(CAPE_W[i]) * 1.05 + p.cape_flare * (0.35 + float(i) * 0.2)
		var ang: float = float(p.cape[i]) + 0.05
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.45, next + perp * seg_w * 0.55,
			next - perp * seg_w * 0.55, prev - perp * seg_w * 0.45,
		])
		_poly(poly, Pal.CAPE_DARK)
		prev = next

	# Lapisan luar hijau zamrud bertrim emas
	prev = anchor
	for i in 3:
		var seg_len: float = float(CAPE_SEGS[i])
		var seg_w: float = float(CAPE_W[i]) + p.cape_flare * (0.3 + float(i) * 0.2)
		var ang: float = float(p.cape[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.48, next + perp * seg_w * 0.56,
			next - perp * seg_w * 0.56, prev - perp * seg_w * 0.48,
		])
		var col: Color = Pal.CAPE if i < 2 else Pal.CAPE_LIGHT
		_poly(poly, col)
		# Kilau lipatan kain
		draw_line(_sn(prev + perp * 0.6), _sn(next + perp * 0.8), _c(Pal.CAPE_BRIGHT), 1.0)
		# Trim emas di ujung hem
		if i == 2:
			draw_line(_sn(poly[1]), _sn(poly[2]), _c(Pal.GOLD_LIGHT), 1.2)
		prev = next


# ══════════════════════════════════════════════════════════
#  2. HAIR (Rambut Auburn Tembaga Hangat Berombak)
# ══════════════════════════════════════════════════════════

func _draw_hair(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["head_c"] as Vector2) + Vector2(-2.5, -0.6)
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(HAIR_SEGS[i])
		var seg_w: float = float(HAIR_W[i])
		var ang: float = float(p.hair[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.50, next + perp * seg_w * 0.35,
			next - perp * seg_w * 0.35, prev - perp * seg_w * 0.50,
		])
		var col: Color = Pal.HAIR if i != 1 else Pal.HAIR_LIGHT
		_poly(poly, col)
		draw_line(_sn(prev + perp * 0.3), _sn(next + perp * 0.2), _c(Pal.HAIR_SHINE), 0.9)
		prev = next


# ══════════════════════════════════════════════════════════
#  3. QUIVER (Tempat Anak Panah & Bulu Zamrud)
# ══════════════════════════════════════════════════════════

func _draw_quiver(j: Dictionary) -> void:
	var base: Vector2 = (j["chest"] as Vector2) + Vector2(-4.6, 1.0)
	var q_poly := PackedVector2Array([
		base + Vector2(-3.0, -8.5), base + Vector2(3.0, -8.5),
		base + Vector2(3.6, 5.5), base + Vector2(-2.4, 5.5),
	])
	_poly(q_poly, Pal.QUIVER)
	draw_line(_sn(base + Vector2(-3.0, -8.5)), _sn(base + Vector2(3.0, -8.5)), _c(Pal.GOLD_DARK), 1.2)
	draw_line(_sn(base + Vector2(-2.6, -3.8)), _sn(base + Vector2(3.2, -3.8)), _c(Pal.GOLD_LIGHT), 1.1)

	# 4 Arrow fletchings (bulu zamrud khas elven)
	for i in 4:
		var ax: float = base.x - 2.2 + float(i) * 1.4
		var ay: float = base.y - 9.0
		draw_line(_sn(Vector2(ax, ay)), _sn(Vector2(ax - 0.5, ay - 4.5)), _c(Pal.SHAFT), 1.0)
		draw_line(_sn(Vector2(ax - 0.5, ay - 4.5)), _sn(Vector2(ax - 1.2, ay - 3.2)), _c(Pal.FEATHER), 1.2)
		draw_line(_sn(Vector2(ax - 0.5, ay - 4.5)), _sn(Vector2(ax + 0.2, ay - 3.2)), _c(Pal.FEATHER), 1.2)
		draw_circle(_sn(Vector2(ax - 0.5, ay - 4.5)), 0.6, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  4. LIMBS & BOOTS (Kaki & Lengan Anggun)
# ══════════════════════════════════════════════════════════

func _draw_arm(p: SylaraPose, j: Dictionary, is_back: bool) -> void:
	var sh: Vector2 = (j["sh_b"] if is_back else j["sh_f"]) as Vector2
	var elb: Vector2 = (j["elb_b"] if is_back else j["elb_f"]) as Vector2
	var hand: Vector2 = (j["hand_b"] if is_back else j["hand_f"]) as Vector2
	var sleeve_col := Pal.CLOTH_DARK if is_back else Pal.CLOTH
	var skin_col := Pal.SKIN_SHADOW if is_back else Pal.SKIN

	# Lengan atas
	_taper(sh, 5.2 if not is_back else 4.6, elb, 4.2 if not is_back else 3.8, sleeve_col)

	# Lengan bawah (bracer kulit pada lengan depan)
	if not is_back:
		_taper(elb, 3.8, hand, 3.2, Pal.LEATHER)
		draw_line(_sn(elb.lerp(hand, 0.4)), _sn(elb.lerp(hand, 0.6)), _c(Pal.GOLD_LIGHT), 1.1)
	else:
		_taper(elb, 3.6, hand, 3.0, skin_col)

	# Telapak tangan lentik
	draw_circle(_sn(hand), 2.0, _c(skin_col))


func _draw_calf(_p: SylaraPose, j: Dictionary, is_back: bool) -> void:
	var hip_j: Vector2 = (j["hip_b"] if is_back else j["hip_f"]) as Vector2
	var knee: Vector2 = (j["knee_b"] if is_back else j["knee_f"]) as Vector2
	var ankle: Vector2 = (j["ankle_b"] if is_back else j["ankle_f"]) as Vector2
	var pants_col := Pal.CLOTH_DARK if is_back else Pal.CLOTH

	# Paha (celana ketat hijau petualang)
	_taper(hip_j, 5.4, knee, 4.4, pants_col)
	# Lutut
	draw_circle(_sn(knee), 2.2, _c(pants_col))
	# Betis / boots atas
	var boot_col := Pal.LEATHER_DARK if is_back else Pal.LEATHER
	_taper(knee, 4.6, ankle, 3.6, boot_col)


func _draw_feet(j: Dictionary) -> void:
	var keys: Array[String] = ["ankle_b", "ankle_f"]
	for ankle_key in keys:
		var is_front: bool = ankle_key == "ankle_f"
		var toe_key: String = "toe_f" if is_front else "toe_b"
		var ankle: Vector2 = j[ankle_key] as Vector2
		var toe: Vector2 = j[toe_key] as Vector2
		var col: Color = Pal.LEATHER if is_front else Pal.LEATHER_DARK

		# Sepatu bot kulit petualang
		_capsule(ankle + Vector2(0.0, 0.8), toe + Vector2(0.5, 0.8), 3.4, col)

		# Cuff lipatan boot & gesper emas
		if is_front:
			var cuff_a := ankle + Vector2(-2.2, -1.8)
			var cuff_b := ankle + Vector2(2.2, -1.8)
			_capsule(cuff_a, cuff_b, 2.4, Pal.LEATHER_LIGHT)
			draw_circle(_sn(ankle + Vector2(0.8, -1.8)), 0.8, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  5. TUNIC & TORSO (Tunik Beludru Hijau & Korset Kulit)
# ══════════════════════════════════════════════════════════

func _draw_tunic(p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var flare: float = 1.6 + p.cape_flare * 2.2

	# Rok tunik hijau elven berbelah tengah dengan bordir emas
	var poly := PackedVector2Array([
		hip + Vector2(-4.2, -2.0),
		hip + Vector2(4.2, -2.0),
		hip + Vector2(4.8 + flare, 5.0),
		hip + Vector2(2.4 + flare, 7.8),
		hip + Vector2(0.0, 5.8),           # belahan tengah rok tunik
		hip + Vector2(-2.4 - flare, 7.8),
		hip + Vector2(-4.8 - flare, 5.0),
	])
	_poly(poly, Pal.CLOTH)
	draw_line(_sn(hip + Vector2(-2.4 - flare, 7.8)), _sn(hip + Vector2(0.0, 5.8)), _c(Pal.GOLD), 1.0)
	draw_line(_sn(hip + Vector2(0.0, 5.8)), _sn(hip + Vector2(2.4 + flare, 7.8)), _c(Pal.GOLD), 1.0)


func _draw_torso(j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var chest: Vector2 = j["chest"] as Vector2
	var neck: Vector2 = j["neck"] as Vector2
	_taper(hip, 11.0, chest, 9.8, Pal.CLOTH_DARK)
	_taper(chest, 9.8, neck, 6.8, Pal.CLOTH)


func _draw_belt(j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	_capsule(hip + Vector2(-4.8, -0.6), hip + Vector2(4.8, -0.6), 2.8, Pal.LEATHER_DARK)
	# Gesper emas di tengah
	_capsule(hip + Vector2(-0.8, -0.6), hip + Vector2(1.2, -0.6), 2.0, Pal.GOLD)


func _draw_corset(j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var hip: Vector2 = j["hip"] as Vector2

	# Korset kulit yang pas di lekuk tubuh
	var poly := PackedVector2Array([
		chest + Vector2(-3.8, -3.2), chest + Vector2(3.8, -3.2),
		hip + Vector2(4.0, -1.2), hip + Vector2(-4.0, -1.2),
	])
	_poly(poly, Pal.LEATHER)
	# Highlight tepi kulit & bayangan sisi
	draw_line(_sn(chest + Vector2(-3.8, -3.2)), _sn(hip + Vector2(-4.0, -1.2)), _c(Pal.LEATHER_DARK), 1.1)
	draw_line(_sn(chest + Vector2(3.8, -3.2)), _sn(hip + Vector2(4.0, -1.2)), _c(Pal.LEATHER_LIGHT), 1.1)

	# Tali silang korset emas (cross-lacing)
	draw_line(_sn(chest + Vector2(-1.4, -2.2)), _sn(chest + Vector2(1.4, -0.4)), _c(Pal.GOLD_LIGHT), 0.9)
	draw_line(_sn(chest + Vector2(-1.4, -0.4)), _sn(chest + Vector2(1.4, -2.2)), _c(Pal.GOLD_LIGHT), 0.9)
	draw_line(_sn(chest + Vector2(-1.4, 0.4)), _sn(chest + Vector2(1.4, 2.2)), _c(Pal.GOLD_LIGHT), 0.9)
	draw_line(_sn(chest + Vector2(-1.4, 2.2)), _sn(chest + Vector2(1.4, 0.4)), _c(Pal.GOLD_LIGHT), 0.9)


func _draw_mantle(j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var neck: Vector2 = j["neck"] as Vector2

	# Mantle / cowl bahu hijau dengan bordir emas (seperti sprite)
	var mantle_poly := PackedVector2Array([
		neck + Vector2(-3.8, 1.2), neck + Vector2(3.8, 1.2),
		chest + Vector2(5.2, -1.6), chest + Vector2(2.4, 0.4),
		chest + Vector2(-2.4, 0.4), chest + Vector2(-5.2, -1.6),
	])
	_poly(mantle_poly, Pal.HOOD)
	draw_line(_sn(chest + Vector2(-5.2, -1.6)), _sn(chest + Vector2(-2.4, 0.4)), _c(Pal.GOLD), 1.1)
	draw_line(_sn(chest + Vector2(-2.4, 0.4)), _sn(chest + Vector2(2.4, 0.4)), _c(Pal.GOLD), 1.1)
	draw_line(_sn(chest + Vector2(2.4, 0.4)), _sn(chest + Vector2(5.2, -1.6)), _c(Pal.GOLD), 1.1)

	# Permata angin di tengah dada
	draw_circle(_sn(chest + Vector2(0.0, -0.6)), 1.4, _c(Pal.GOLD_LIGHT))
	draw_circle(_sn(chest + Vector2(0.0, -0.6)), 0.8, _c(Pal.WIND_BRIGHT))


# ══════════════════════════════════════════════════════════
#  6. HOOD & WAJAH CANTIK ELVEN (GORGEOUS ELVEN HEROINE)
# ══════════════════════════════════════════════════════════

func _draw_head_and_hood(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var lean: float = p.head_lean

	# 1. Kubah tudung elven (Hood Dome) yang membulat alami
	var hood_pts := PackedVector2Array([
		head_c + Vector2(-5.2 + lean, -2.5),
		head_c + Vector2(-5.6 + lean, -HEAD_R - 0.5),
		head_c + Vector2(-2.8 + lean, -HEAD_R - 2.8),
		head_c + Vector2(2.2 + lean, -HEAD_R - 2.2),
		head_c + Vector2(4.2 + lean, -2.5),
		head_c + Vector2(2.4 + lean, 1.2),
		head_c + Vector2(-2.2 + lean, 2.0),
	])
	_poly(hood_pts, Pal.HOOD)
	draw_line(_sn(head_c + Vector2(-5.6 + lean, -HEAD_R - 0.5)),
		_sn(head_c + Vector2(-2.8 + lean, -HEAD_R - 2.8)), _c(Pal.HOOD_LIGHT), 1.2)
	draw_line(_sn(head_c + Vector2(-2.8 + lean, -HEAD_R - 2.8)),
		_sn(head_c + Vector2(2.2 + lean, -HEAD_R - 2.2)), _c(Pal.HOOD_LIGHT), 1.2)

	# Bayangan dalam tudung
	var cowl_shadow := PackedVector2Array([
		head_c + Vector2(-2.8 + lean, -HEAD_R - 0.2),
		head_c + Vector2(1.8 + lean, -HEAD_R + 0.4),
		head_c + Vector2(2.8 + lean, -2.0),
		head_c + Vector2(-0.8 + lean, 1.2),
		head_c + Vector2(-3.0 + lean, -1.0),
	])
	_poly(cowl_shadow, Pal.HOOD_DARK)

	# 2. Wajah elven tirus & cantik (3/4 Profile elven)
	var face_pts := PackedVector2Array([
		head_c + Vector2(-0.6 + lean * 1.5, -HEAD_R + 1.2),  # dahi
		head_c + Vector2(2.0 + lean * 1.5, -HEAD_R + 2.0),
		head_c + Vector2(3.6 + lean * 1.5, -1.6),            # pelipis
		head_c + Vector2(3.9 + lean * 1.5, 1.0),             # pipi halus
		head_c + Vector2(2.8 + lean * 1.5, 3.8),             # rahang
		head_c + Vector2(1.4 + lean * 1.5, 5.2),             # dagu elven mungil
		head_c + Vector2(-0.6 + lean * 1.5, 3.5),
	])
	_poly(face_pts, Pal.SKIN)
	draw_line(_sn(head_c + Vector2(-0.6 + lean * 1.5, 3.5)),
		_sn(head_c + Vector2(2.6 + lean * 1.5, 3.8)), _c(Pal.SKIN_SHADOW), 0.8)

	# 3. Telinga elven runcing (Pointed Elven Ear)
	var ear := PackedVector2Array([
		head_c + Vector2(-0.8 + lean * 1.5, -1.2),
		head_c + Vector2(-4.8 + lean * 1.5, -3.5),
		head_c + Vector2(-1.2 + lean * 1.5, 1.2),
	])
	_poly(ear, Pal.SKIN)
	draw_line(_sn(ear[0]), _sn(ear[1]), _c(Pal.SKIN_LIGHT), 0.7)
	draw_line(_sn(ear[1]), _sn(ear[2]), _c(Pal.INK_SOFT), 0.7)
	# Anting emas di telinga elven
	draw_circle(_sn(head_c + Vector2(-3.6 + lean * 1.5, -2.6)), 0.6, _c(Pal.GOLD_LIGHT))

	# 4. Mata zamrud tajam & berbinar (Focused Archer's Eye)
	var eye_c := head_c + Vector2(2.2 + lean * 1.5, -1.0)
	var open: float = 1.0 - clampf(p.eye_blink, 0.0, 1.0)
	if open > 0.4:
		# Eyeliner elven tegas
		draw_line(_sn(eye_c + Vector2(-1.4, -0.8)), _sn(eye_c + Vector2(1.4, -0.6)), _c(Pal.INK), 1.1)
		# Iris zamrud
		draw_circle(_sn(eye_c + Vector2(0.2, 0.0)), 1.2, _c(Pal.EYE))
		# Pupil
		draw_circle(_sn(eye_c + Vector2(0.4, -0.1)), 0.6, _c(Pal.INK))
		# Sparkle binar mata
		draw_circle(_sn(eye_c + Vector2(0.6, -0.5)), 0.5, _c(Color.WHITE))
	else:
		# Kedipan senyum
		draw_line(_sn(eye_c + Vector2(-1.2, 0.0)), _sn(eye_c + Vector2(1.4, 0.0)), _c(Pal.INK), 1.2)

	# Alis auburn melengkung
	draw_line(_sn(eye_c + Vector2(-1.2, -2.2)), _sn(eye_c + Vector2(1.4, -1.8)), _c(Pal.HAIR_DARK), 0.9)

	# Hidung porselen & bibir mawar manis
	draw_circle(_sn(head_c + Vector2(3.8 + lean * 1.5, 0.6)), 0.5, _c(Pal.SKIN_LIGHT))
	var lip_p := head_c + Vector2(2.0 + lean * 1.5, 2.8)
	draw_line(_sn(lip_p + Vector2(-0.8, 0.0)), _sn(lip_p + Vector2(0.8, 0.0)), _c(Pal.LIP), 0.9)

	# Blush pipi lembut
	draw_circle(_sn(head_c + Vector2(2.4 + lean * 1.5, 1.2)), 1.4,
		_c(Color(Pal.SKIN_BLUSH.r, Pal.SKIN_BLUSH.g, Pal.SKIN_BLUSH.b, 0.38)))

	# 5. Rambut auburn membingkai wajah (Bangs & Sidelock)
	draw_line(_sn(head_c + Vector2(-0.6 + lean, -HEAD_R + 1.2)),
		_sn(head_c + Vector2(1.4 + lean, -HEAD_R + 3.2)), _c(Pal.HAIR), 1.2)
	draw_line(_sn(head_c + Vector2(-0.6 + lean, -1.0)),
		_sn(head_c + Vector2(0.3 + lean, 3.2)), _c(Pal.HAIR), 1.1)
	draw_line(_sn(head_c + Vector2(-0.2 + lean, -0.5)),
		_sn(head_c + Vector2(0.5 + lean, 3.4)), _c(Pal.HAIR_SHINE), 0.7)

	# 6. Bordir emas di tepi bukaan tudung
	draw_line(_sn(head_c + Vector2(-2.8 + lean, -HEAD_R - 2.8)),
		_sn(head_c + Vector2(2.2 + lean, -HEAD_R - 2.2)), _c(Pal.GOLD_LIGHT), 1.1)
	draw_line(_sn(head_c + Vector2(2.2 + lean, -HEAD_R - 2.2)),
		_sn(head_c + Vector2(4.2 + lean, -2.5)), _c(Pal.GOLD_LIGHT), 1.1)

	# Ekor tudung melambai di belakang leher (secondary motion)
	var prev_hood: Vector2 = head_c + Vector2(-3.4, -HEAD_R + 2.0)
	for i in 2:
		var seg_len: float = float(HOOD_SEGS[i])
		var ang: float = float(p.hood[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var next_hood: Vector2 = prev_hood + d * seg_len
		draw_line(_sn(prev_hood), _sn(next_hood), _c(Pal.HOOD_LIGHT), 2.2)
		draw_line(_sn(prev_hood), _sn(next_hood), _c(Pal.GOLD_LIGHT), 0.8)
		prev_hood = next_hood


# ══════════════════════════════════════════════════════════
#  7. WEAPON — BUSUR PUSAKA RECURVE & BENANG ANGIN BERKILAU
# ══════════════════════════════════════════════════════════

func _draw_bow(p: SylaraPose, j: Dictionary) -> void:
	var grip: Vector2 = j["bow_grip"] as Vector2
	var bow_dir: Vector2 = j["bow_dir"] as Vector2
	var bow_perp: Vector2 = j["bow_perp"] as Vector2

	# Grip busur berbalut kulit & cincin emas
	_capsule(grip - bow_dir * 3.0, grip + bow_dir * 3.0, 3.0, Pal.WOOD_DARK)
	draw_line(_sn(grip - bow_perp * 1.5), _sn(grip + bow_perp * 1.5), _c(Pal.GOLD_LIGHT), 1.0)

	# Limb atas & bawah (recurve elven mulus)
	var tip_upper: Vector2 = grip + bow_dir * BOW_LEN
	var ctrl_upper: Vector2 = grip + bow_dir * BOW_LEN * 0.55 + bow_perp * 4.6
	_draw_recurve_limb(grip + bow_dir * 3.0, ctrl_upper, tip_upper, 3.0, 1.4)

	var tip_lower: Vector2 = grip - bow_dir * BOW_LEN
	var ctrl_lower: Vector2 = grip - bow_dir * BOW_LEN * 0.55 - bow_perp * 4.6
	_draw_recurve_limb(grip - bow_dir * 3.0, ctrl_lower, tip_lower, 3.0, 1.4)

	# Ujung tanduk gading & cincin emas
	var tip_upper_end: Vector2 = tip_upper - bow_perp * 3.0
	var tip_lower_end: Vector2 = tip_lower + bow_perp * 3.0
	draw_line(_sn(tip_upper), _sn(tip_upper_end), _c(Pal.HORN_TIP), 2.0)
	draw_line(_sn(tip_lower), _sn(tip_lower_end), _c(Pal.HORN_TIP), 2.0)
	draw_circle(_sn(tip_upper), 1.2, _c(Pal.GOLD_LIGHT))
	draw_circle(_sn(tip_lower), 1.2, _c(Pal.GOLD_LIGHT))

	# Tali busur ajaib (Luminous Mana String)
	var string_top: Vector2 = tip_upper_end
	var string_bot: Vector2 = tip_lower_end
	var pull_dist: float = p.bow_draw * 11.5

	if pull_dist > 0.01:
		var mid: Vector2 = (string_top + string_bot) * 0.5
		var nock_pt: Vector2 = mid - bow_perp * pull_dist

		# Glow tali & benang mana
		draw_line(_sn(string_top), _sn(nock_pt), _c(Pal.STRING_GLOW), 2.4)
		draw_line(_sn(nock_pt), _sn(string_bot), _c(Pal.STRING_GLOW), 2.4)
		draw_line(_sn(string_top), _sn(nock_pt), _c(Pal.STRING), 1.2)
		draw_line(_sn(nock_pt), _sn(string_bot), _c(Pal.STRING), 1.2)

		# Anak panah kristal saat busur ditarik
		if p.bow_draw > 0.2:
			var arrow_tip: Vector2 = grip + bow_dir * (BOW_LEN + 8.5)
			_draw_arrow(nock_pt, arrow_tip)
	else:
		draw_line(_sn(string_top), _sn(string_bot), _c(Pal.STRING_GLOW), 2.0)
		draw_line(_sn(string_top), _sn(string_bot), _c(Pal.STRING), 1.1)


func _draw_recurve_limb(start: Vector2, ctrl: Vector2, end: Vector2,
		w_start: float, w_end: float) -> void:
	var steps := 8
	var p_prev := start
	for i in range(1, steps + 1):
		var t := float(i) / float(steps)
		var pt := (1.0 - t) * (1.0 - t) * start + 2.0 * (1.0 - t) * t * ctrl + t * t * end
		var w := lerpf(w_start, w_end, t)
		draw_line(_sn(p_prev), _sn(pt), _c(Pal.WOOD), w)
		draw_line(_sn(p_prev), _sn(pt), _c(Pal.GOLD_LIGHT), 0.8)
		p_prev = pt


func _draw_arrow(nock: Vector2, tip: Vector2) -> void:
	draw_line(_sn(nock), _sn(tip), _c(Pal.SHAFT), 1.5)
	draw_line(_sn(nock), _sn(tip), _c(Pal.WOOD_SHINE), 0.7)
	var d: Vector2 = (tip - nock).normalized()
	var perp: Vector2 = Vector2(-d.y, d.x)

	# Mata panah kristal perak berkilau
	var head_poly := PackedVector2Array([
		tip + d * 2.6,
		tip - d * 4.0 + perp * 2.2,
		tip - d * 3.0,
		tip - d * 4.0 - perp * 2.2,
	])
	_poly(head_poly, Pal.HEAD)
	draw_line(_sn(tip + d * 2.0), _sn(tip - d * 3.6), _c(Pal.HEAD_SHINE), 0.9)

	# Fletching bulu zamrud ganda
	var f_base: Vector2 = nock + d * 3.6
	draw_line(_sn(f_base), _sn(f_base - d * 3.2 + perp * 2.4), _c(Pal.FEATHER), 1.3)
	draw_line(_sn(f_base), _sn(f_base - d * 3.2 - perp * 2.4), _c(Pal.FEATHER), 1.3)
	draw_line(_sn(f_base + perp * 1.0), _sn(f_base - perp * 1.0), _c(Pal.GOLD_LIGHT), 1.1)


# ══════════════════════════════════════════════════════════
#  8. RIM LIGHT & MAGIC ACCENT
# ══════════════════════════════════════════════════════════

func _draw_rim(j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var rim_col := Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b, 0.45 * pose.alpha)
	draw_arc(head_c + Vector2(-1.0, -1.0), HEAD_R + 0.8, 2.7, 4.3, 6, rim_col, 1.2, true)
	var sh_f: Vector2 = j["sh_f"] as Vector2
	draw_line(_sn(sh_f + Vector2(-1.0, -2.0)), _sn(sh_f + Vector2(2.0, -2.8)), rim_col, 1.1)


func _draw_wind_wisps(p: SylaraPose, j: Dictionary) -> void:
	if p.wind_glow < 0.05:
		return
	var glow: float = p.wind_glow
	var bow_tip: Vector2 = j["bow_tip"] as Vector2

	var wisp_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.55 * glow * p.alpha)
	for i in 3:
		var t: float = phase * 3.2 + float(i) * 2.1
		var off: Vector2 = Vector2(sin(t) * 4.6, cos(t * 1.4) * 3.6)
		draw_circle(_sn(bow_tip + off), 1.5 + sin(t * 2.0) * 0.5, wisp_col)

	if p.bow_draw > 0.2:
		var nock: Vector2 = j["bow_nock"] as Vector2
		var ring_alpha: float = 0.5 * p.bow_draw * p.alpha
		draw_arc(_sn(nock), 4.8 * p.bow_draw, 0.0, TAU, 12,
			Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, ring_alpha), 1.2, true)
		draw_circle(_sn(nock), 3.2 * p.bow_draw,
			Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b, 0.75 * p.bow_draw * p.alpha))


func _draw_hurt_flash(p: SylaraPose, j: Dictionary) -> void:
	var a: float = 0.38 * p.hurt_tint * p.alpha
	var col := Color(Pal.HURT_TINT.r, Pal.HURT_TINT.g, Pal.HURT_TINT.b, a)
	draw_circle(_sn(j["head_c"] as Vector2), 6.5, col)
	draw_circle(_sn((j["chest"] as Vector2) + Vector2(0.0, -1.0)), 8.5, col)
	draw_circle(_sn(j["hip"] as Vector2), 7.5, col)
