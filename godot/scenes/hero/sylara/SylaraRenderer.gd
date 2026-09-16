# SylaraRenderer.gd — renderer prosedural berlapis Sylara (Godot 4.x).
#
# Satu-satunya tugas: menggambar karakter Sylara dari SylaraPose lewat _draw().
#
# Standar Visual: High-Polish Fantasy Heroine — siluet elven yang anggun,
# wajah cantik tirus dengan mata zamrud berbinar, rambut auburn bervolume,
# jubah beludru hijau hutan bertrim emas, korset kulit berenda silang emas,
# busur pusaka recurve dengan benang sihir angin bercahaya mint, dan aura
# sihir angin lembut di tanah.
#
# 100% KODE tanpa aset grafis eksternal, memanfaatkan rendering CanvasItem
# Godot (antialiased polylines, subpixel curves, procedural lighting & VFX).
class_name SylaraRenderer
extends Node2D

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

# ── Metrik tubuh elven proporsional (anchor = tanah di antara dua kaki) ──
const HIP_Y := -27.0
const SPINE_LEN := 12.0
const CHEST_LEN := 8.5
const HEAD_R := 6.5
const LEG_UPPER := 12.0
const LEG_LOWER := 11.0
const FOOT_LEN := 6.5
const ARM_UPPER := 9.0
const ARM_LOWER := 8.5
const BOW_LEN := 23.5        # panjang setengah busur recurve (grip → tip)
const CAPE_SEGS: Array[float] = [9.0, 9.0, 10.5]
const CAPE_W: Array[float] = [6.0, 5.2, 4.0]
const HOOD_SEGS: Array[float] = [5.5, 5.0]
const HAIR_SEGS: Array[float] = [8.5, 7.5, 7.5]
const HAIR_W: Array[float] = [4.2, 3.2, 2.0]

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
	_draw_shadow(p)

	# 1. BACK (lapisan belakang: jubah, rambut, quiver, kaki/lengan belakang)
	_draw_cape(p, j)
	_draw_hair(p, j)
	_draw_quiver(j)
	_draw_arm(j, true)
	_draw_calf(j, true)

	# 2. BODY (lapisan tubuh & kaki)
	_draw_calf(j, false)
	_draw_feet(j)
	_draw_tunic(p, j)
	_draw_torso(j)

	# 3. ARMOR & KORSET (korset kulit berenda silang emas, sabuk, belati)
	_draw_belt(j)
	_draw_vest(j)

	# 4. KEPALA & WAJAH CANTIK (tudung pelindung, wajah elven, mata zamrud, rambut)
	_draw_hood_back(p, j)
	_draw_head(p, j)
	_draw_hood_front(p, j)

	# 5. WEAPON (lengan depan, pauldron bahu, busur recurve berurat emas)
	_draw_arm(j, false)
	_draw_pauldron(j)
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
	var sh_f: Vector2 = chest + Vector2(4.2, -0.6)
	var sh_b: Vector2 = chest + Vector2(-4.2, -1.2)
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

	# Busur: orientasi dari bow_angle
	var bow_dir: Vector2 = _fwd(p.bow_angle)
	var bow_perp: Vector2 = Vector2(-bow_dir.y, bow_dir.x)
	_bow_dir = bow_dir
	_bow_grip = hand_f
	_bow_tip = hand_f + bow_dir * BOW_LEN
	var bow_mid: Vector2 = hand_f + bow_dir * BOW_LEN * 0.5
	_bow_nock = hand_f - bow_perp * (p.bow_draw * 11.5)

	return {
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


func _c(col: Color) -> Color:
	if pose == null:
		return col
	return Color(col.r, col.g, col.b, col.a * pose.alpha)


## Outline tinta tertutup dengan antialiasing aktif.
func _ink(pts: PackedVector2Array, w: float = 1.0, col: Color = Pal.INK_SOFT) -> void:
	if pts.size() < 2:
		return
	var loop := pts.duplicate()
	loop.append(pts[0])
	draw_polyline(loop, _c(col), w, true)


# ══════════════════════════════════════════════════════════
#  0. AMBIENT GROUND MAGIC & SHADOW
# ══════════════════════════════════════════════════════════

func _draw_ground_magic(p: SylaraPose) -> void:
	var c := Vector2(p.root_x * 0.35, 0.0)
	var rot := phase * 0.70

	# Cincin sihir angin berputar lembut di tanah
	var ring_col := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.18 * p.alpha)
	var glow_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.28 * p.alpha)

	# 3 busur angin laminar berputar di sekeliling kaki
	for i in 3:
		var start_a: float = rot + float(i) * TAU / 3.0
		var end_a: float = start_a + 1.2
		draw_arc(c, 22.0, start_a, end_a, 12, ring_col, 1.2, true)
		var glyph_p: Vector2 = c + Vector2(cos(end_a), sin(end_a) * 0.45) * 22.0
		draw_circle(glyph_p, 1.2, glow_col)

	# Partikel daun kecil mengorbit di sekitar tapak
	for i in 4:
		var a: float = rot * 1.3 + float(i) * TAU / 4.0
		var r: float = 17.0 + sin(phase * 2.0 + float(i)) * 3.5
		var lp: Vector2 = c + Vector2(cos(a) * r, sin(a) * (r * 0.42) - 2.0)
		var leaf_c := Pal.LEAF_GOLD if (i % 2 == 0) else Pal.LEAF
		draw_circle(lp, 1.0, Color(leaf_c.r, leaf_c.g, leaf_c.b, 0.42 * p.alpha))


func _draw_shadow(p: SylaraPose) -> void:
	var c := Vector2(p.root_x * 0.35, 0.0)
	# Soft outer shadow
	var outer := PackedVector2Array([
		c + Vector2(16, 0), c + Vector2(13, 3.2), c + Vector2(7, 5.5),
		c + Vector2(-7, 5.5), c + Vector2(-13, 3.2), c + Vector2(-16, 0),
		c + Vector2(-13, -3.2), c + Vector2(-7, -4.5), c + Vector2(7, -4.5),
		c + Vector2(13, -3.2),
	])
	draw_colored_polygon(outer, _c(Color(Pal.SHADOW_GROUND.r, Pal.SHADOW_GROUND.g, Pal.SHADOW_GROUND.b, 0.14)))

	# Contact shadow
	var inner := PackedVector2Array([
		c + Vector2(11, 0), c + Vector2(8, 2.2), c + Vector2(4, 3.5),
		c + Vector2(-4, 3.5), c + Vector2(-8, 2.2), c + Vector2(-11, 0),
		c + Vector2(-8, -2.2), c + Vector2(-4, -3.0), c + Vector2(4, -3.0),
		c + Vector2(8, -2.2),
	])
	draw_colored_polygon(inner, _c(Pal.SHADOW_GROUND))


# ══════════════════════════════════════════════════════════
#  1. CAPE (Jubah Angin Berlapis Berbordir Emas)
# ══════════════════════════════════════════════════════════

func _draw_cape(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["chest"] as Vector2) + Vector2(-3.2, -2.2)

	# Lapisan dalam gelap (inner lining)
	var prev_inner := anchor + Vector2(-0.6, 1.0)
	for i in 3:
		var seg_len: float = float(CAPE_SEGS[i])
		var seg_w: float = float(CAPE_W[i]) * 1.08 + p.cape_flare * (0.4 + float(i) * 0.25)
		var ang: float = float(p.cape[i]) + 0.06
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next_inner: Vector2 = prev_inner + d * seg_len
		var poly_in := PackedVector2Array([
			prev_inner + perp * seg_w * 0.45,
			next_inner + perp * (seg_w * 0.55),
			next_inner - perp * (seg_w * 0.55),
			prev_inner - perp * seg_w * 0.45,
		])
		draw_colored_polygon(poly_in, _c(Pal.CAPE_DARK))
		prev_inner = next_inner

	# Lapisan luar hijau zamrud dengan highlight lipatan & trim emas
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(CAPE_SEGS[i])
		var seg_w: float = float(CAPE_W[i]) + p.cape_flare * (0.35 + float(i) * 0.22)
		var ang: float = float(p.cape[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.48,
			next + perp * (seg_w * 0.56),
			next - perp * (seg_w * 0.56),
			prev - perp * seg_w * 0.48,
		])
		var col: Color = Pal.CAPE if i < 2 else Pal.CAPE_LIGHT
		draw_colored_polygon(poly, _c(col))

		# Highlight lipatan kain sutra berkilau di punggung jubah
		draw_line(prev + perp * 0.8, next + perp * 1.1, _c(Pal.CAPE_BRIGHT), 1.0, true)
		# Garis tinta lembut
		draw_line(poly[0], poly[1], _c(Pal.INK_SOFT), 0.9, true)
		draw_line(poly[2], poly[3], _c(Pal.INK_SOFT), 0.9, true)

		# Bordir emas di hem ujung jubah
		if i == 2:
			draw_line(poly[1], poly[2], _c(Pal.GOLD_LIGHT), 1.3, true)
		prev = next


# ══════════════════════════════════════════════════════════
#  2. HAIR (Rambut Auburn / Tembaga Berombak Lembut)
# ══════════════════════════════════════════════════════════

func _draw_hair(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["head_c"] as Vector2) + Vector2(-2.2, -0.8)
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(HAIR_SEGS[i])
		var seg_w: float = float(HAIR_W[i])
		var ang: float = float(p.hair[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.52,
			next + perp * seg_w * 0.36,
			next - perp * seg_w * 0.36,
			prev - perp * seg_w * 0.52,
		])
		var col: Color = Pal.HAIR if i == 0 else (Pal.HAIR_LIGHT if i == 1 else Pal.HAIR)
		draw_colored_polygon(poly, _c(col))

		# Kilau sutra tembaga keemasan di tengah helai rambut
		draw_line(prev + perp * 0.4, next + perp * 0.3, _c(Pal.HAIR_SHINE), 0.9, true)
		# Bayangan rambut bagian bawah
		draw_line(poly[2], poly[3], _c(Pal.HAIR_DARK), 0.8, true)
		prev = next


# ══════════════════════════════════════════════════════════
#  3. QUIVER (Tempat Anak Panah Kulit Berhias Emas)
# ══════════════════════════════════════════════════════════

func _draw_quiver(j: Dictionary) -> void:
	var base: Vector2 = (j["chest"] as Vector2) + Vector2(-5.2, 1.2)
	var q_poly := PackedVector2Array([
		base + Vector2(-3.2, -9.0), base + Vector2(3.4, -9.0),
		base + Vector2(4.2, 6.2), base + Vector2(-2.4, 6.2),
	])
	draw_colored_polygon(q_poly, _c(Pal.QUIVER))
	_ink(q_poly, 0.9, Pal.INK_SOFT)

	# Highlight kulit quiver
	draw_line(base + Vector2(-2.2, -8.0), base + Vector2(-1.6, 5.0), _c(Pal.LEATHER_LIGHT), 0.9, true)
	# Sabuk emas berukir daun pada quiver
	draw_line(base + Vector2(-2.8, -4.2), base + Vector2(3.6, -4.2), _c(Pal.GOLD_LIGHT), 1.3, true)

	# 3 Arrow shafts & emerald fletching
	for i in 3:
		var ax: float = base.x - 2.0 + float(i) * 2.2
		var ay: float = base.y - 9.5
		# Shaft kayu
		draw_line(Vector2(ax, ay), Vector2(ax, ay - 4.8), _c(Pal.SHAFT), 1.1, true)
		# Bulu fletching zamrud elegan ganda
		draw_line(Vector2(ax - 1.2, ay - 2.0), Vector2(ax - 2.4, ay - 4.4), _c(Pal.FEATHER), 1.1, true)
		draw_line(Vector2(ax + 1.2, ay - 2.0), Vector2(ax + 2.4, ay - 4.4), _c(Pal.FEATHER), 1.1, true)
		draw_circle(Vector2(ax, ay - 4.8), 0.7, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  4. LIMBS & BOOTS (Kaki & Lengan Anggun)
# ══════════════════════════════════════════════════════════

func _draw_arm(j: Dictionary, back: bool) -> void:
	var sh: Vector2 = (j["sh_b"] if back else j["sh_f"]) as Vector2
	var elb: Vector2 = (j["elb_b"] if back else j["elb_f"]) as Vector2
	var hand: Vector2 = (j["hand_b"] if back else j["hand_f"]) as Vector2
	var w: float = 3.0 if back else 3.4

	# Lengan atas (lengan baju beludru hijau bertrim emas)
	_draw_contoured_limb(sh, elb, w, Pal.CLOTH_DARK if back else Pal.CLOTH,
		Pal.CLOTH_LIGHT if not back else Pal.CLOTH)

	# Lengan bawah (kulit porselen elven)
	_draw_contoured_limb(elb, hand, w * 0.86, Pal.SKIN_SHADOW if back else Pal.SKIN,
		Pal.SKIN_LIGHT if not back else Pal.SKIN)

	# Bracer kulit pemanah dengan aksen emas di lengan depan
	if not back:
		var bracer_start: Vector2 = elb + (hand - elb) * 0.22
		var bracer_end: Vector2 = elb + (hand - elb) * 0.78
		_draw_contoured_limb(bracer_start, bracer_end, w * 0.90, Pal.LEATHER, Pal.LEATHER_LIGHT)
		draw_circle((bracer_start + bracer_end) * 0.5, 1.1, _c(Pal.GOLD_LIGHT))

	# Telapak tangan lentik
	draw_circle(hand, 2.0, _c(Pal.SKIN_SHADOW if back else Pal.SKIN))


func _draw_calf(j: Dictionary, back: bool) -> void:
	var hip_j: Vector2 = (j["hip_b"] if back else j["hip_f"]) as Vector2
	var knee: Vector2 = (j["knee_b"] if back else j["knee_f"]) as Vector2
	var ankle: Vector2 = (j["ankle_b"] if back else j["ankle_f"]) as Vector2
	var w: float = 3.6 if back else 4.0

	# Paha (celana ketat hijau hutan lentur)
	_draw_contoured_limb(hip_j, knee, w, Pal.CLOTH_DARK if back else Pal.CLOTH,
		Pal.CLOTH_LIGHT if not back else Pal.CLOTH)

	# Pelindung lutut kulit berkontur halus
	draw_circle(knee, w * 0.50, _c(Pal.LEATHER_DARK if back else Pal.LEATHER))
	if not back:
		draw_circle(knee + Vector2(0.4, -0.4), 1.1, _c(Pal.LEATHER_LIGHT))

	# Betis
	_draw_contoured_limb(knee, ankle, w * 0.82, Pal.CLOTH_DARK if back else Pal.CLOTH,
		Pal.CLOTH_LIGHT if not back else Pal.CLOTH)


func _draw_contoured_limb(a: Vector2, b: Vector2, w: float, col_base: Color, col_hi: Color) -> void:
	var d: Vector2 = b - a
	if d.length_squared() < 0.001:
		return
	d = d.normalized()
	var perp: Vector2 = Vector2(-d.y, d.x)
	var poly := PackedVector2Array([
		a + perp * w * 0.5,
		b + perp * w * 0.42,
		b - perp * w * 0.42,
		a - perp * w * 0.5,
	])
	draw_colored_polygon(poly, _c(col_base))

	# Highlight longitudinal (arah cahaya atas-kiri)
	draw_line(a - perp * w * 0.20, b - perp * w * 0.16, _c(col_hi), 1.0, true)
	# Garis outline lembut
	draw_line(poly[0], poly[1], _c(Pal.INK_SOFT), 0.8, true)
	draw_line(poly[2], poly[3], _c(Pal.INK_SOFT), 0.8, true)


func _draw_feet(j: Dictionary) -> void:
	var keys: Array[String] = ["ankle_b", "ankle_f"]
	for ankle_key in keys:
		var is_front: bool = ankle_key == "ankle_f"
		var toe_key: String = "toe_f" if is_front else "toe_b"
		var ankle: Vector2 = j[ankle_key] as Vector2
		var toe: Vector2 = j[toe_key] as Vector2
		var col: Color = Pal.LEATHER if is_front else Pal.LEATHER_DARK
		var boot := PackedVector2Array([
			ankle + Vector2(-2.4, -2.4), ankle + Vector2(2.4, -2.4),
			toe + Vector2(1.8, 0.2), toe + Vector2(-1.0, 1.6),
			ankle + Vector2(-3.2, 1.4),
		])
		draw_colored_polygon(boot, _c(col))
		_ink(boot, 0.8, Pal.INK_SOFT)

		# Manset boot terlipat (cuff) dengan strap kulit hangat
		draw_line(ankle + Vector2(-2.6, -2.4), ankle + Vector2(2.6, -2.4),
			_c(Pal.LEATHER_LIGHT), 1.6, true)
		# Gesper emas pada boots
		draw_circle(ankle + Vector2(1.0, -0.9), 0.8, _c(Pal.GOLD_LIGHT))
		# Sol boot
		draw_line(toe + Vector2(-1.0, 1.5), toe + Vector2(1.8, 0.3), _c(Pal.LEATHER_DARK), 1.1, true)


# ══════════════════════════════════════════════════════════
#  5. TUNIC & TORSO (Tunik Beludru Hijau Bertrim Emas)
# ══════════════════════════════════════════════════════════

func _draw_tunic(p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var chest: Vector2 = j["chest"] as Vector2
	var sh_f: Vector2 = j["sh_f"] as Vector2
	var sh_b: Vector2 = j["sh_b"] as Vector2
	var flare: float = 1.8 + p.cape_flare * 2.8

	# Tunik berpotongan kelopak anggun
	var poly := PackedVector2Array([
		sh_b + Vector2(-2.0, -1.0),
		sh_f + Vector2(2.0, -1.0),
		hip + Vector2(4.8 + flare, 4.0),
		hip + Vector2(2.8 + flare, 8.4),
		hip + Vector2(0.0, 6.4),           # belahan tengah rok tunik
		hip + Vector2(-2.8 - flare, 8.4),
		hip + Vector2(-4.8 - flare, 4.0),
	])
	draw_colored_polygon(poly, _c(Pal.CLOTH))
	_ink(poly, 0.9, Pal.INK_SOFT)

	# Bordir emas pada belahan bawah tunik
	draw_line(hip + Vector2(-2.8 - flare, 8.4), hip + Vector2(0.0, 6.4), _c(Pal.GOLD_LIGHT), 1.0, true)
	draw_line(hip + Vector2(0.0, 6.4), hip + Vector2(2.8 + flare, 8.4), _c(Pal.GOLD_LIGHT), 1.0, true)

	# Shading lipatan kain beludru di samping pinggang
	var mid_x: float = (sh_f.x + sh_b.x) * 0.5
	draw_line(Vector2(mid_x - 1.0, chest.y + 1.8), Vector2(mid_x - 0.8, hip.y + 5.5),
		_c(Color(Pal.CLOTH_DARK.r, Pal.CLOTH_DARK.g, Pal.CLOTH_DARK.b, 0.45)), 1.2, true)


func _draw_torso(j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var neck: Vector2 = j["neck"] as Vector2
	var poly := PackedVector2Array([
		chest + Vector2(-4.8, -1.8),
		chest + Vector2(4.8, -1.8),
		neck + Vector2(2.8, 1.0),
		neck + Vector2(-2.8, 1.0),
	])
	draw_colored_polygon(poly, _c(Pal.CLOTH_LIGHT))


# ══════════════════════════════════════════════════════════
#  6. KORSET KULIT, SABUK & GEM ANGIN
# ══════════════════════════════════════════════════════════

func _draw_belt(j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var belt := PackedVector2Array([
		hip + Vector2(-5.8, -1.2), hip + Vector2(5.8, -1.2),
		hip + Vector2(5.8, 2.0), hip + Vector2(-5.8, 2.0),
	])
	draw_colored_polygon(belt, _c(Pal.LEATHER_DARK))
	# Gesper emas antik di tengah sabuk
	draw_rect(Rect2(hip.x - 2.4, hip.y - 1.5, 4.8, 3.4), _c(Pal.GOLD))
	draw_rect(Rect2(hip.x - 1.4, hip.y - 0.8, 2.8, 2.0), _c(Pal.GOLD_LIGHT))

	# Belati elven ramping bertatah emas di pinggang kanan
	var sheath := Vector2(hip.x + 6.2, hip.y + 0.4)
	draw_line(sheath + Vector2(0, -2.4), sheath + Vector2(0.8, 3.4),
		_c(Pal.LEATHER_DARK), 2.0, true)
	draw_line(sheath + Vector2(-1.4, -3.0), sheath + Vector2(1.4, -3.0),
		_c(Pal.WOOD), 1.2, true)
	draw_circle(sheath + Vector2(0, -3.6), 0.9, _c(Pal.GOLD_LIGHT))


func _draw_vest(j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	# Korset kulit yang pas membalut lekuk dada elven
	var panel_l := PackedVector2Array([
		chest + Vector2(-4.0, -4.2), chest + Vector2(-0.8, -5.2),
		chest + Vector2(-0.8, 3.0), chest + Vector2(-4.0, 3.8),
	])
	var panel_r := PackedVector2Array([
		chest + Vector2(0.8, -5.2), chest + Vector2(4.0, -4.2),
		chest + Vector2(4.0, 3.8), chest + Vector2(0.8, 3.0),
	])
	draw_colored_polygon(panel_l, _c(Pal.LEATHER_LIGHT))
	draw_colored_polygon(panel_r, _c(Pal.LEATHER_LIGHT))

	# Tali silang korset emas (cross-lacing)
	draw_line(chest + Vector2(-0.9, -3.2), chest + Vector2(0.9, -1.4), _c(Pal.GOLD_LIGHT), 0.9, true)
	draw_line(chest + Vector2(-0.9, -1.4), chest + Vector2(0.9, -3.2), _c(Pal.GOLD_LIGHT), 0.9, true)
	draw_line(chest + Vector2(-0.9, -0.4), chest + Vector2(0.9, 1.4), _c(Pal.GOLD_LIGHT), 0.9, true)
	draw_line(chest + Vector2(-0.9, 1.4), chest + Vector2(0.9, -0.4), _c(Pal.GOLD_LIGHT), 0.9, true)

	# Clasp permata angin (bros daun emas dengan permata zamrud bercahaya)
	var gem: Vector2 = chest + Vector2(0.0, -1.2)
	draw_circle(gem, 1.8, _c(Pal.GOLD_LIGHT))
	draw_circle(gem, 1.1, _c(Pal.WIND_BRIGHT))
	draw_circle(gem + Vector2(-0.3, -0.3), 0.5, _c(Color.WHITE))


func _draw_pauldron(j: Dictionary) -> void:
	# Pelindung bahu kulit berlapis bertrim emas di bahu depan
	var sh: Vector2 = j["sh_f"] as Vector2
	draw_circle(sh, 2.8, _c(Pal.LEATHER))
	draw_circle(sh + Vector2(0.2, -0.2), 1.2, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  7. HOOD & WAJAH CANTIK ELVEN (GORGEOUS ELVEN HEROINE)
# ══════════════════════════════════════════════════════════

func _draw_hood_back(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	# Kubah tudung melengkung halus di bagian belakang kepala
	draw_circle(head_c + Vector2(-1.0, -0.5), HEAD_R + 1.2, _c(Pal.HOOD))

	# Bayangan dalam tudung (cowl shadow) yang membingkai wajah elven
	var shadow_poly := PackedVector2Array([
		head_c + Vector2(-2.0, -HEAD_R + 0.5),
		head_c + Vector2(1.8, -HEAD_R + 0.8),
		head_c + Vector2(3.0, -2.0),
		head_c + Vector2(0.0, HEAD_R * 0.7),
		head_c + Vector2(-2.5, HEAD_R * 0.3),
	])
	draw_colored_polygon(shadow_poly, _c(Pal.HOOD_DARK))


func _draw_head(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var lean: float = p.head_lean

	# Leher elven ramping
	var neck_top: Vector2 = head_c + Vector2(0.5 + lean, 5.0)
	var neck_bot: Vector2 = (j["neck"] as Vector2) + Vector2(0.5, 0.0)
	draw_line(neck_top, neck_bot, _c(Pal.SKIN), 2.4, true)

	# ── 1. Wajah Elven Tirus & Cantik ──
	var face_pts := PackedVector2Array([
		head_c + Vector2(-0.5 + lean * 1.5, -HEAD_R + 1.2),  # dahi
		head_c + Vector2(2.4 + lean * 1.5, -HEAD_R + 2.0),
		head_c + Vector2(3.8 + lean * 1.5, -1.8),            # pelipis
		head_c + Vector2(4.2 + lean * 1.5, 1.2),             # tulang pipi halus
		head_c + Vector2(3.2 + lean * 1.5, 4.2),             # rahang
		head_c + Vector2(1.6 + lean * 1.5, 5.8),             # dagu elven mungil
		head_c + Vector2(-0.2 + lean * 1.5, 4.2),            # rahang kiri
		head_c + Vector2(-1.0 + lean * 1.5, 0.0),
	])
	draw_colored_polygon(face_pts, _c(Pal.SKIN))
	# Bayangan lembut rahang
	draw_line(head_c + Vector2(-0.2 + lean * 1.5, 4.2), head_c + Vector2(2.8 + lean * 1.5, 4.2),
		_c(Pal.SKIN_SHADOW), 0.9, true)

	# ── 2. Telinga Elf Ramping Panjang (Elven Pointed Ear) ──
	var ear := PackedVector2Array([
		head_c + Vector2(-1.0 + lean * 1.5, -1.2),
		head_c + Vector2(-6.0 + lean * 1.5, -3.8),          # ujung runcing telinga elf
		head_c + Vector2(-1.5 + lean * 1.5, 1.8),
	])
	draw_colored_polygon(ear, _c(Pal.SKIN))
	draw_line(ear[0], ear[1], _c(Pal.SKIN_LIGHT), 0.8, true)
	draw_line(ear[1], ear[2], _c(Pal.INK_SOFT), 0.8, true)
	# Anting emas elven mungil di telinga
	draw_circle(head_c + Vector2(-4.2 + lean * 1.5, -2.8), 0.7, _c(Pal.GOLD_LIGHT))

	# ── 3. Blush Pipi Mawar Lembut (Rosy Elven Glow) ──
	var blush_pos := head_c + Vector2(2.5 + lean * 1.5, 1.6)
	draw_circle(blush_pos, 1.6, _c(Color(Pal.SKIN_BLUSH.r, Pal.SKIN_BLUSH.g, Pal.SKIN_BLUSH.b, 0.45)))

	# ── 4. Mata Zamrud Anime Cantik & Berbinar ──
	var eye_x: float = head_c.x + 2.4 + lean * 1.5
	var eye_y: float = head_c.y - 1.2
	var blink: float = p.eye_blink

	if blink < 0.65:
		# Sclera putih bersih
		draw_circle(Vector2(eye_x, eye_y), 1.7, _c(Pal.EYE_WHITE))
		# Iris zamrud bercahaya
		draw_circle(Vector2(eye_x + 0.15, eye_y), 1.25, _c(Pal.EYE_DARK))
		draw_circle(Vector2(eye_x + 0.25, eye_y + 0.15), 0.95, _c(Pal.EYE))
		# Pupil hitam
		draw_circle(Vector2(eye_x + 0.35, eye_y - 0.15), 0.5, _c(Pal.INK))
		# Double catchlight sparkle (bintang binar mata hidup!)
		draw_circle(Vector2(eye_x + 0.65, eye_y - 0.55), 0.55, _c(Color.WHITE))
		draw_circle(Vector2(eye_x - 0.15, eye_y + 0.45), 0.32, _c(Color(1, 1, 1, 0.85)))

		# Eyeliner lentik bersayap (winged lash)
		draw_line(Vector2(eye_x - 1.2, eye_y - 1.2), Vector2(eye_x + 1.2, eye_y - 1.4),
			_c(Pal.INK), 1.2, true)
		draw_line(Vector2(eye_x + 1.0, eye_y - 1.4), Vector2(eye_x + 2.0, eye_y - 1.9),
			_c(Pal.INK), 0.9, true)
	else:
		# Kedipan senyum manis
		draw_arc(Vector2(eye_x, eye_y - 0.5), 1.6, 0.2, PI - 0.2, 6,
			_c(Pal.INK), 1.3, true)

	# Alis auburn melengkung anggun
	draw_line(Vector2(eye_x - 1.2, eye_y - 2.8), Vector2(eye_x + 1.2, eye_y - 2.5),
		_c(Pal.HAIR_DARK), 0.8, true)

	# Hidung mungil & bibir mawar manis
	draw_circle(head_c + Vector2(4.0 + lean * 1.5, 0.8), 0.5,
		_c(Color(Pal.SKIN_LIGHT.r, Pal.SKIN_LIGHT.g, Pal.SKIN_LIGHT.b, 0.85)))
	var lip_pos := head_c + Vector2(2.4 + lean * 1.5, 3.2)
	draw_line(lip_pos + Vector2(-0.8, 0.0), lip_pos + Vector2(0.9, 0.0), _c(Pal.LIP), 1.1, true)
	draw_circle(lip_pos + Vector2(0.2, 0.3), 0.4, _c(Pal.LIP_SHINE))

	# ── 5. Poni Rambut Auburn Membingkai Wajah ──
	var bang_poly := PackedVector2Array([
		head_c + Vector2(-0.5 + lean, -HEAD_R + 1.2),
		head_c + Vector2(1.2 + lean, -HEAD_R + 3.0),
		head_c + Vector2(2.2 + lean, -HEAD_R + 1.8),
	])
	draw_colored_polygon(bang_poly, _c(Pal.HAIR_LIGHT))

	# Sidelock membingkai pipi
	var sidelock := PackedVector2Array([
		head_c + Vector2(-0.5 + lean, -1.0),
		head_c + Vector2(0.2 + lean, 3.8),
		head_c + Vector2(-0.8 + lean, 4.2),
		head_c + Vector2(-1.5 + lean, 0.5),
	])
	draw_colored_polygon(sidelock, _c(Pal.HAIR))
	draw_line(head_c + Vector2(-0.3 + lean, 0.5), head_c + Vector2(0.0 + lean, 3.8),
		_c(Pal.HAIR_SHINE), 0.8, true)


func _draw_hood_front(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2

	# Lengkungan kubah tudung atas dengan trim emas
	var dome_pts := PackedVector2Array()
	var n := 8
	for i in n + 1:
		var t: float = float(i) / float(n)
		var a: float = lerpf(PI + 0.3, TAU - 0.2, t)
		dome_pts.append(head_c + Vector2(cos(a) * (HEAD_R + 1.4), sin(a) * (HEAD_R + 1.4)))
	draw_polyline(dome_pts, _c(Pal.GOLD_LIGHT), 1.2, true)

	# Ekor tudung yang melayang di belakang leher (secondary motion)
	var anchor: Vector2 = head_c + Vector2(-3.0, -HEAD_R + 2.0)
	var prev: Vector2 = anchor
	for i in 2:
		var seg_len: float = float(HOOD_SEGS[i])
		var ang: float = float(p.hood[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var next: Vector2 = prev + d * seg_len
		draw_line(prev, next, _c(Pal.HOOD_LIGHT), 2.4, true)
		draw_line(prev, next, _c(Pal.GOLD_LIGHT), 0.8, true)
		prev = next


# ══════════════════════════════════════════════════════════
#  8. WEAPON — BUSUR PUSAKA RECURVE & BENANG ANGIN BERCANTIK
# ══════════════════════════════════════════════════════════

func _draw_bow(p: SylaraPose, j: Dictionary) -> void:
	var grip: Vector2 = j["bow_grip"] as Vector2
	var bow_dir: Vector2 = j["bow_dir"] as Vector2
	var bow_perp: Vector2 = j["bow_perp"] as Vector2

	# Handle grip busur dibalut kulit + cincin emas antik
	var grip_poly := PackedVector2Array([
		grip + bow_dir * 3.2 + bow_perp * 1.5,
		grip + bow_dir * 3.2 - bow_perp * 1.5,
		grip - bow_dir * 3.2 - bow_perp * 1.5,
		grip - bow_dir * 3.2 + bow_perp * 1.5,
	])
	draw_colored_polygon(grip_poly, _c(Pal.WOOD_DARK))
	_ink(grip_poly, 0.8, Pal.INK_SOFT)

	# Lilitan kawat emas di grip
	for off in [-1.6, 0.0, 1.6]:
		var gc: Vector2 = grip + bow_dir * off
		draw_line(gc + bow_perp * 1.5, gc - bow_perp * 1.5, _c(Pal.GOLD_LIGHT), 0.9, true)

	# Limb busur atas (recurve melengkung anggun)
	var tip_upper: Vector2 = grip + bow_dir * BOW_LEN
	var ctrl_upper: Vector2 = grip + bow_dir * BOW_LEN * 0.55 + bow_perp * 4.6
	_draw_ornate_limb(grip + bow_dir * 3.2, ctrl_upper, tip_upper, 3.2, 1.4, true)

	# Limb busur bawah
	var tip_lower: Vector2 = grip - bow_dir * BOW_LEN
	var ctrl_lower: Vector2 = grip - bow_dir * BOW_LEN * 0.55 - bow_perp * 4.6
	_draw_ornate_limb(grip - bow_dir * 3.2, ctrl_lower, tip_lower, 3.2, 1.4, false)

	# Ujung recurve tanduk gading (horn tips) berukir emas
	var tip_upper_end: Vector2 = tip_upper - bow_perp * 3.2
	var tip_lower_end: Vector2 = tip_lower + bow_perp * 3.2
	draw_line(tip_upper, tip_upper_end, _c(Pal.HORN_TIP), 2.0, true)
	draw_line(tip_lower, tip_lower_end, _c(Pal.HORN_TIP), 2.0, true)
	draw_circle(tip_upper, 1.4, _c(Pal.GOLD_LIGHT))
	draw_circle(tip_lower, 1.4, _c(Pal.GOLD_LIGHT))

	# ── TALI BUSUR AJAIB: Benang Angin Mana Bercahaya Mint ──
	var string_top: Vector2 = tip_upper_end
	var string_bot: Vector2 = tip_lower_end
	var pull_dist: float = p.bow_draw * 11.5

	if pull_dist > 0.01:
		var mid: Vector2 = (string_top + string_bot) * 0.5
		var pull: Vector2 = -bow_perp * pull_dist
		var nock_pt: Vector2 = mid + pull

		# Glow luar benang sihir angin
		draw_line(string_top, nock_pt, _c(Color(Pal.STRING_GLOW.r, Pal.STRING_GLOW.g, Pal.STRING_GLOW.b, 0.45)), 2.6, true)
		draw_line(nock_pt, string_bot, _c(Color(Pal.STRING_GLOW.r, Pal.STRING_GLOW.g, Pal.STRING_GLOW.b, 0.45)), 2.6, true)
		# Inti terang benang mana
		draw_line(string_top, nock_pt, _c(Pal.STRING), 1.2, true)
		draw_line(nock_pt, string_bot, _c(Pal.STRING), 1.2, true)

		# Anak panah yang sedang ditarik di busur
		if p.bow_draw > 0.2:
			var arrow_tip: Vector2 = grip + bow_dir * (BOW_LEN + 8.5)
			_draw_arrow(nock_pt, arrow_tip)
	else:
		# Tali santai berkilau lembut
		draw_line(string_top, string_bot, _c(Color(Pal.STRING_GLOW.r, Pal.STRING_GLOW.g, Pal.STRING_GLOW.b, 0.35)), 2.2, true)
		draw_line(string_top, string_bot, _c(Pal.STRING), 1.1, true)


func _draw_ornate_limb(start: Vector2, ctrl: Vector2, end: Vector2,
		w_start: float, w_end: float, _is_upper: bool) -> void:
	var n: int = 8
	var pts_outer := PackedVector2Array()
	var pts_inner := PackedVector2Array()
	var pts_mid := PackedVector2Array()

	for i in n + 1:
		var t: float = float(i) / float(n)
		var pt: Vector2 = (1.0 - t) * (1.0 - t) * start + 2.0 * (1.0 - t) * t * ctrl + t * t * end
		var w: float = lerpf(w_start, w_end, t)
		var dt: float = 0.01
		var t2: float = minf(t + dt, 1.0)
		var p2: Vector2 = (1.0 - t2) * (1.0 - t2) * start + 2.0 * (1.0 - t2) * t2 * ctrl + t2 * t2 * end
		var tangent: Vector2 = (p2 - pt).normalized()
		var normal: Vector2 = Vector2(-tangent.y, tangent.x)
		pts_outer.append(pt + normal * w * 0.5)
		pts_inner.append(pt - normal * w * 0.5)
		pts_mid.append(pt)

	var poly := PackedVector2Array()
	for v in pts_outer:
		poly.append(v)
	for i in range(pts_inner.size() - 1, -1, -1):
		poly.append(pts_inner[i])

	# Badan busur kayu pusaka
	draw_colored_polygon(poly, _c(Pal.WOOD))
	_ink(poly, 0.8, Pal.INK_SOFT)

	# Urat emas bertatah di tengah limb busur
	for i in range(pts_mid.size() - 1):
		draw_line(pts_mid[i], pts_mid[i + 1], _c(Pal.GOLD_LIGHT), 1.0, true)

	# Highlight kayu di sisi luar
	for i in range(pts_outer.size() - 1):
		draw_line(pts_outer[i], pts_outer[i + 1], _c(Pal.WOOD_SHINE), 0.8, true)


func _draw_arrow(nock: Vector2, tip: Vector2) -> void:
	# Shaft kayu halus
	draw_line(nock, tip, _c(Pal.SHAFT), 1.5, true)
	draw_line(nock, tip, _c(Pal.WOOD_SHINE), 0.7, true)
	var d: Vector2 = (tip - nock).normalized()
	var perp: Vector2 = Vector2(-d.y, d.x)

	# Mata panah kristal perak elven
	var head_poly := PackedVector2Array([
		tip + d * 2.6,
		tip - d * 4.2 + perp * 2.3,
		tip - d * 3.2,
		tip - d * 4.2 - perp * 2.3,
	])
	draw_colored_polygon(head_poly, _c(Pal.HEAD))
	_ink(head_poly, 0.8, Pal.INK_SOFT)
	draw_line(tip + d * 2.0, tip - d * 3.8, _c(Pal.HEAD_SHINE), 0.9, true)

	# Fletching bulu zamrud ganda
	var f_base: Vector2 = nock + d * 3.8
	draw_line(f_base, f_base - d * 3.4 + perp * 2.6, _c(Pal.FEATHER), 1.3, true)
	draw_line(f_base, f_base - d * 3.4 - perp * 2.6, _c(Pal.FEATHER), 1.3, true)
	draw_line(f_base + perp * 1.2, f_base - perp * 1.2, _c(Pal.GOLD_LIGHT), 1.1, true)


# ══════════════════════════════════════════════════════════
#  9. RIM LIGHT & MAGIC ACCENT
# ══════════════════════════════════════════════════════════

func _draw_rim(j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var rim_col := Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b, 0.45 * pose.alpha)
	# Rim tudung & mahkota kepala
	draw_arc(head_c + Vector2(-1.0, -1.0), HEAD_R + 0.8, 2.7, 4.3, 6, rim_col, 1.2, true)
	# Rim bahu depan
	var sh_f: Vector2 = j["sh_f"] as Vector2
	draw_line(sh_f + Vector2(-1.0, -2.2), sh_f + Vector2(2.2, -3.0), rim_col, 1.1, true)


func _draw_wind_wisps(p: SylaraPose, j: Dictionary) -> void:
	if p.wind_glow < 0.05:
		return
	var glow: float = p.wind_glow
	var bow_tip: Vector2 = j["bow_tip"] as Vector2

	# Wisps angin ajaib yang menari di ujung busur
	var wisp_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.55 * glow * p.alpha)
	for i in 3:
		var t: float = phase * 3.2 + float(i) * 2.1
		var off: Vector2 = Vector2(sin(t) * 4.6, cos(t * 1.4) * 3.6)
		draw_circle(bow_tip + off, 1.5 + sin(t * 2.0) * 0.5, wisp_col)

	# Kilau sihir nock saat busur ditarik
	if p.bow_draw > 0.2:
		var nock: Vector2 = j["bow_nock"] as Vector2
		var ring_alpha: float = 0.5 * p.bow_draw * p.alpha
		draw_arc(nock, 4.8 * p.bow_draw, 0.0, TAU, 12,
			Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, ring_alpha), 1.2, true)
		draw_circle(nock, 3.2 * p.bow_draw,
			Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b, 0.75 * p.bow_draw * p.alpha))
		draw_circle(nock, 1.6 * p.bow_draw,
			Color(1, 1, 1, 0.65 * p.bow_draw * p.alpha))


func _draw_hurt_flash(p: SylaraPose, j: Dictionary) -> void:
	var a: float = 0.38 * p.hurt_tint * p.alpha
	var col := Color(Pal.HURT_TINT.r, Pal.HURT_TINT.g, Pal.HURT_TINT.b, a)
	draw_circle((j["head_c"] as Vector2), 6.5, col)
	draw_circle((j["chest"] as Vector2) + Vector2(0.0, -1.0), 8.5, col)
	draw_circle((j["hip"] as Vector2), 7.5, col)
	draw_circle((j["hand_f"] as Vector2), 4.0, col)
	draw_circle((j["knee_f"] as Vector2), 5.0, col)
	draw_circle((j["knee_b"] as Vector2), 5.0, col)
