# SylaraRenderer.gd — renderer prosedural berlapis Sylara (Godot 4.x Masterwork Rebuild).
#
# Satu-satunya tugas: menggambar karakter Sylara dari SylaraPose lewat _draw().
#
# Lapisan gambar (Sesuai MASTER PROMPT Section 4 & Visual Hierarchy):
#   1. SHADOW (tanah — soft elliptical contour)
#   2. BACK (cape, hair, quiver, lengan belakang, betis belakang)
#   3. BODY (tunic, betis depan, sepatu boots ranger, torso)
#   4. ARMOR (leather vest/cuirass, belt emas, hood cowl)
#   5. KEPALA & DETAIL (wajah, mata emerald ekspresif + blink, bibir)
#   6. WEAPON (lengan depan + bracer + busur recurve + anak panah angin)
#   7. DETAIL & WEAPON TRAIL (buckles, fletching, rim light)
#   8. MAGIC ACCENT (wind wisps, charge nock glow, aura daun)
#   9. FEEDBACK (hurt flash tint saat kena hit)
#
# Gaya: Pixel-Art Fantasy Polish — outline tinta 1px, palet terkontrol
# SylaraPalette, FK geometri deterministik, biaya per-frame 1 CanvasItem
# (ringan dan teroptimasi untuk Android).
class_name SylaraRenderer
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

# ── Metrik tubuh (pixel lokal; anchor = tanah di antara dua kaki) ──
const HIP_Y := -27.0
const SPINE_LEN := 12.0
const CHEST_LEN := 8.5
const HEAD_R := 6.5
const LEG_UPPER := 11.5
const LEG_LOWER := 10.5
const FOOT_LEN := 6.5
const ARM_UPPER := 9.0
const ARM_LOWER := 8.5
const BOW_LEN := 23.0        # panjang busur recurve (tip to tip / 2)
const CAPE_SEGS: Array[float] = [8.5, 8.5, 9.5]
const CAPE_W: Array[float] = [5.5, 4.6, 3.2]
const HOOD_SEGS: Array[float] = [5.5, 5.0]
const HAIR_SEGS: Array[float] = [7.5, 6.5, 6.5]
const HAIR_W: Array[float] = [4.0, 3.0, 1.8]

## Pose aktif (di-set root tiap frame sebelum queue_redraw).
var pose: SylaraPose = null
## Fase global (untuk hamon shimmer, glint, wisp angin).
var phase := 0.0
## Jejak trail busur: titik GLOBAL, di-push root saat pose.trail aktif.
var trail_pts: Array[Vector2] = []

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

	# 1. SHADOW (tanah)
	_draw_shadow(p, j)

	# 2. BACK (lapisan belakang)
	_draw_cape(p, j)
	_draw_hair(p, j)
	_draw_quiver(p, j)
	_draw_arm(p, j, true)
	_draw_calf(p, j, true)

	# 3. BODY (lapisan tubuh & kaki)
	_draw_calf(p, j, false)
	_draw_feet(p, j)
	_draw_tunic(p, j)
	_draw_torso(p, j)

	# 4. ARMOR (vest kulit + belt + hood)
	_draw_belt(p, j)
	_draw_vest(p, j)
	_draw_hood(p, j)

	# 5. KEPALA & WAJAH
	_draw_head(p, j)

	# 6. WEAPON (lengan depan + busur recurve + anak panah)
	_draw_trail(p)
	_draw_arm(p, j, false)
	_draw_bow(p, j)

	# 7. HIGHLIGHT & MAGIC ACCENT
	_draw_rim(p, j)
	_draw_wind_wisps(p, j)

	# 8. FEEDBACK DAMAGE
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
	var sh_f: Vector2 = chest + Vector2(4.5, -0.6)
	var sh_b: Vector2 = chest + Vector2(-4.5, -1.2)
	var hip_f: Vector2 = hip + Vector2(3.5, 2.0)
	var hip_b: Vector2 = hip + Vector2(-3.5, 2.5)

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
	_bow_nock = hand_f - bow_dir * 3.5 + bow_perp * (p.bow_draw * 11.0)

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


# ══════════════════════════════════════════════════════════
#  1. SHADOW (tanah)
# ══════════════════════════════════════════════════════════

func _draw_shadow(p: SylaraPose, _j: Dictionary) -> void:
	var c: Vector2 = Vector2(p.root_x * 0.4, 0.0)
	var poly: PackedVector2Array = PackedVector2Array([
		c + Vector2(15, 0), c + Vector2(13, 3), c + Vector2(7, 5.5),
		c + Vector2(-7, 5.5), c + Vector2(-13, 3), c + Vector2(-15, 0),
		c + Vector2(-13, -3), c + Vector2(-7, -4.5), c + Vector2(7, -4.5),
		c + Vector2(13, -3),
	])
	draw_colored_polygon(poly, _c(Pal.SHADOW_GROUND))


# ══════════════════════════════════════════════════════════
#  2. CAPE (secondary motion jubah angin)
# ══════════════════════════════════════════════════════════

func _draw_cape(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["chest"] as Vector2) + Vector2(-3.5, -2.5)
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(CAPE_SEGS[i])
		var seg_w: float = float(CAPE_W[i]) + p.cape_flare * (0.4 + float(i) * 0.25)
		var ang: float = float(p.cape[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly: PackedVector2Array = PackedVector2Array([
			prev + perp * seg_w * 0.5,
			next + perp * (seg_w * 0.5 + 1.2),
			next - perp * (seg_w * 0.5 + 1.2),
			prev - perp * seg_w * 0.5,
		])
		var col: Color = Pal.CAPE_DARK if i == 0 else (Pal.CAPE if i == 1 else Pal.CAPE_LIGHT)
		draw_colored_polygon(poly, _c(col))
		# Trim tinta / outline
		draw_line(poly[0], poly[1], _c(Pal.INK), 1.0)
		draw_line(poly[2], poly[3], _c(Pal.INK), 1.0)
		if i == 2:
			# Hem cape ujung bawah
			draw_line(poly[1], poly[2], _c(Pal.CAPE_LIGHT), 1.0)
		prev = next


# ══════════════════════════════════════════════════════════
#  3. HAIR (rambut hijau gelap berkibar)
# ══════════════════════════════════════════════════════════

func _draw_hair(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["head_c"] as Vector2) + Vector2(-2.5, -1.0)
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(HAIR_SEGS[i])
		var seg_w: float = float(HAIR_W[i])
		var ang: float = float(p.hair[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly: PackedVector2Array = PackedVector2Array([
			prev + perp * seg_w * 0.5,
			next + perp * seg_w * 0.35,
			next - perp * seg_w * 0.35,
			prev - perp * seg_w * 0.5,
		])
		var col: Color = Pal.HAIR if i < 2 else Pal.HAIR_LIGHT
		draw_colored_polygon(poly, _c(col))
		draw_line(poly[0], poly[1], _c(Pal.INK), 0.8)
		prev = next


# ══════════════════════════════════════════════════════════
#  4. QUIVER (tempat anak panah kulit + fletching)
# ══════════════════════════════════════════════════════════

func _draw_quiver(_p: SylaraPose, j: Dictionary) -> void:
	var base: Vector2 = (j["chest"] as Vector2) + Vector2(-5.5, 1.5)
	var q_poly: PackedVector2Array = PackedVector2Array([
		base + Vector2(-3.5, -9), base + Vector2(3.5, -9),
		base + Vector2(4.5, 6), base + Vector2(-2.5, 6),
	])
	draw_colored_polygon(q_poly, _c(Pal.QUIVER))
	draw_polyline(q_poly, _c(Pal.INK), 1.0)
	# Gold band pada quiver
	draw_line(base + Vector2(-3.0, -4.0), base + Vector2(3.8, -4.0), _c(Pal.GOLD), 1.2)
	# 3 Arrow shafts & heads
	for i in 3:
		var ax: float = base.x - 2.2 + float(i) * 2.4
		var ay: float = base.y - 9.5
		# Shaft
		draw_line(Vector2(ax, ay), Vector2(ax, ay - 4.5), _c(Pal.SHAFT), 1.2)
		# Fletching
		draw_line(Vector2(ax - 1.2, ay - 2.0), Vector2(ax - 2.4, ay - 4.0), _c(Pal.FEATHER), 1.0)
		draw_line(Vector2(ax + 1.2, ay - 2.0), Vector2(ax + 2.4, ay - 4.0), _c(Pal.FEATHER), 1.0)
		# Arrowhead tip
		draw_line(Vector2(ax - 1.5, ay - 4.0), Vector2(ax, ay - 7.5), _c(Pal.HEAD), 1.0)
		draw_line(Vector2(ax + 1.5, ay - 4.0), Vector2(ax, ay - 7.5), _c(Pal.HEAD), 1.0)


# ══════════════════════════════════════════════════════════
#  5. LIMBS (Lengan & Kaki)
# ══════════════════════════════════════════════════════════

func _draw_arm(_p: SylaraPose, j: Dictionary, back: bool) -> void:
	var sh: Vector2 = (j["sh_b"] if back else j["sh_f"]) as Vector2
	var elb: Vector2 = (j["elb_b"] if back else j["elb_f"]) as Vector2
	var hand: Vector2 = (j["hand_b"] if back else j["hand_f"]) as Vector2
	var w: float = 3.4 if back else 3.8

	# Upper arm (tunic sleeve)
	_draw_limb(sh, elb, w, Pal.CLOTH_DARK if back else Pal.CLOTH)
	# Forearm (kulit + bracer)
	_draw_limb(elb, hand, w * 0.86, Pal.SKIN_SHADOW if back else Pal.SKIN)
	# Leather bracer pada lengan depan
	if not back:
		var mid_arm: Vector2 = (elb + hand) * 0.5
		_draw_limb(elb + (hand - elb) * 0.2, mid_arm + (hand - elb) * 0.25,
			w * 0.95, Pal.LEATHER)
		draw_circle(mid_arm, 1.2, _c(Pal.GOLD))
	# Hand / sarung tangan
	draw_circle(hand, 2.3, _c(Pal.SKIN_SHADOW if back else Pal.SKIN))


func _draw_calf(_p: SylaraPose, j: Dictionary, back: bool) -> void:
	var hip_j: Vector2 = (j["hip_b"] if back else j["hip_f"]) as Vector2
	var knee: Vector2 = (j["knee_b"] if back else j["knee_f"]) as Vector2
	var ankle: Vector2 = (j["ankle_b"] if back else j["ankle_f"]) as Vector2
	var w: float = 4.0 if back else 4.4

	# Thigh (celana ketat hijau gelap)
	_draw_limb(hip_j, knee, w, Pal.CLOTH_DARK if back else Pal.CLOTH)
	# Knee protector
	draw_circle(knee, w * 0.55, _c(Pal.LEATHER_DARK if back else Pal.LEATHER))
	# Shin
	_draw_limb(knee, ankle, w * 0.85, Pal.CLOTH_DARK if back else Pal.CLOTH)


func _draw_limb(a: Vector2, b: Vector2, w: float, col: Color) -> void:
	var d: Vector2 = (b - a).normalized()
	if d.length_squared() < 0.001:
		return
	var perp: Vector2 = Vector2(-d.y, d.x)
	var poly: PackedVector2Array = PackedVector2Array([
		a + perp * w * 0.5,
		b + perp * w * 0.42,
		b - perp * w * 0.42,
		a - perp * w * 0.5,
	])
	draw_colored_polygon(poly, _c(col))
	draw_line(a + perp * w * 0.5, b + perp * w * 0.42, _c(Pal.INK), 0.8)
	draw_line(a - perp * w * 0.5, b - perp * w * 0.42, _c(Pal.INK), 0.8)


func _draw_feet(_p: SylaraPose, j: Dictionary) -> void:
	var keys: Array[String] = ["ankle_b", "ankle_f"]
	for ankle_key in keys:
		var is_front: bool = ankle_key == "ankle_f"
		var toe_key: String = "toe_f" if is_front else "toe_b"
		var ankle: Vector2 = j[ankle_key] as Vector2
		var toe: Vector2 = j[toe_key] as Vector2
		var col: Color = Pal.LEATHER if is_front else Pal.LEATHER_DARK
		var boot: PackedVector2Array = PackedVector2Array([
			ankle + Vector2(-2.5, -2), ankle + Vector2(2.5, -2),
			toe + Vector2(1.5, 0), toe + Vector2(-1.0, 1.5),
			ankle + Vector2(-3.5, 1.5),
		])
		draw_colored_polygon(boot, _c(col))
		draw_polyline(boot, _c(Pal.INK), 0.9)
		# Toe wrap highlight
		draw_line(ankle + Vector2(0, 0), toe + Vector2(0, -0.5), _c(Pal.LEATHER_LIGHT), 1.0)


# ══════════════════════════════════════════════════════════
#  6. TUNIC & TORSO
# ══════════════════════════════════════════════════════════

func _draw_tunic(p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var chest: Vector2 = j["chest"] as Vector2
	var sh_f: Vector2 = j["sh_f"] as Vector2
	var sh_b: Vector2 = j["sh_b"] as Vector2
	var flare: float = 2.2 + p.cape_flare * 3.2
	var poly: PackedVector2Array = PackedVector2Array([
		sh_b + Vector2(-2.2, -1.0),
		sh_f + Vector2(2.2, -1.0),
		hip + Vector2(5.5 + flare, 4.5),
		hip + Vector2(3.5 + flare, 8.5),
		hip + Vector2(-3.5 - flare, 8.5),
		hip + Vector2(-5.5 - flare, 4.5),
	])
	draw_colored_polygon(poly, _c(Pal.CLOTH))
	draw_polyline(poly, _c(Pal.INK), 1.0)

	# Shading lipatan jubah
	var mid_x: float = (sh_f.x + sh_b.x) * 0.5
	draw_line(Vector2(mid_x, chest.y + 2.0), Vector2(mid_x, hip.y + 6.5),
		_c(Color(Pal.CLOTH_DARK.r, Pal.CLOTH_DARK.g, Pal.CLOTH_DARK.b, 0.45)), 1.4)


func _draw_torso(_p: SylaraPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var neck: Vector2 = j["neck"] as Vector2
	var poly: PackedVector2Array = PackedVector2Array([
		chest + Vector2(-5.2, -2.0),
		chest + Vector2(5.2, -2.0),
		neck + Vector2(3.2, 1.0),
		neck + Vector2(-3.2, 1.0),
	])
	draw_colored_polygon(poly, _c(Pal.CLOTH_LIGHT))


# ══════════════════════════════════════════════════════════
#  7. BELT & ARMOR VEST
# ══════════════════════════════════════════════════════════

func _draw_belt(_p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var belt: PackedVector2Array = PackedVector2Array([
		hip + Vector2(-6.5, -1.2), hip + Vector2(6.5, -1.2),
		hip + Vector2(6.5, 2.2), hip + Vector2(-6.5, 2.2),
	])
	draw_colored_polygon(belt, _c(Pal.LEATHER_DARK))
	# Buckle emas
	draw_rect(Rect2(hip.x - 2.5, hip.y - 1.5, 5.0, 3.5), _c(Pal.GOLD))
	draw_rect(Rect2(hip.x - 1.5, hip.y - 0.8, 3.0, 2.2), _c(Pal.GOLD_LIGHT))
	# Pouch samping
	draw_rect(Rect2(hip.x - 6.0, hip.y - 0.5, 3.0, 3.5), _c(Pal.LEATHER))


func _draw_vest(_p: SylaraPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var panel_l: PackedVector2Array = PackedVector2Array([
		chest + Vector2(-4.5, -4.5), chest + Vector2(-1.2, -5.5),
		chest + Vector2(-1.2, 3.2), chest + Vector2(-4.5, 4.2),
	])
	var panel_r: PackedVector2Array = PackedVector2Array([
		chest + Vector2(1.2, -5.5), chest + Vector2(4.5, -4.5),
		chest + Vector2(4.5, 4.2), chest + Vector2(1.2, 3.2),
	])
	draw_colored_polygon(panel_l, _c(Pal.LEATHER_LIGHT))
	draw_colored_polygon(panel_r, _c(Pal.LEATHER_LIGHT))
	# Trim emas
	draw_line(chest + Vector2(-4.5, -4.5), chest + Vector2(-4.5, 4.2), _c(Pal.GOLD_DARK), 1.0)
	draw_line(chest + Vector2(4.5, -4.5), chest + Vector2(4.5, 4.2), _c(Pal.GOLD_DARK), 1.0)


# ══════════════════════════════════════════════════════════
#  8. HOOD (Tudung Ranger)
# ══════════════════════════════════════════════════════════

func _draw_hood(p: SylaraPose, j: Dictionary) -> void:
	var neck: Vector2 = j["neck"] as Vector2
	var head_c: Vector2 = j["head_c"] as Vector2
	var hood_poly: PackedVector2Array = PackedVector2Array([
		neck + Vector2(-6.5, -1.0),
		head_c + Vector2(-5.5, -HEAD_R - 2.5),
		head_c + Vector2(0.0, -HEAD_R - 4.5),
		head_c + Vector2(4.8, -HEAD_R - 1.5),
		neck + Vector2(5.5, 0.0),
		neck + Vector2(3.5, 2.5),
		neck + Vector2(-4.5, 2.5),
	])
	draw_colored_polygon(hood_poly, _c(Pal.HOOD))
	draw_polyline(hood_poly, _c(Pal.INK), 1.0)
	# Shadow bagian dalam cowl
	draw_line(neck + Vector2(-4.2, -2.0), head_c + Vector2(-3.2, -HEAD_R + 1.0),
		_c(Color(Pal.HOOD_DARK.r, Pal.HOOD_DARK.g, Pal.HOOD_DARK.b, 0.6)), 2.2)

	# Hood cowl edge trailing (secondary motion)
	var anchor: Vector2 = head_c + Vector2(-3.2, -HEAD_R + 1.5)
	var prev: Vector2 = anchor
	for i in 2:
		var seg_len: float = float(HOOD_SEGS[i])
		var ang: float = float(p.hood[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var next: Vector2 = prev + d * seg_len
		draw_line(prev, next, _c(Pal.HOOD), 3.2)
		draw_line(prev, next, _c(Pal.INK), 0.8)
		prev = next


# ══════════════════════════════════════════════════════════
#  9. HEAD & FACE
# ══════════════════════════════════════════════════════════

func _draw_head(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var lean: float = p.head_lean

	# Bentuk wajah
	var face_pts: PackedVector2Array = PackedVector2Array()
	for i in 12:
		var a: float = float(i) / 12.0 * TAU
		var rx: float = HEAD_R * 0.85
		var ry: float = HEAD_R
		face_pts.append(head_c + Vector2(cos(a) * rx + lean * 3.0, sin(a) * ry))
	draw_colored_polygon(face_pts, _c(Pal.SKIN))
	draw_polyline(face_pts, _c(Pal.INK), 1.0)

	# Shadow dagu / rahang
	draw_arc(head_c + Vector2(lean * 2.0, HEAD_R * 0.45), HEAD_R * 0.52,
		0.3, PI - 0.3, 8,
		_c(Color(Pal.SKIN_SHADOW.r, Pal.SKIN_SHADOW.g, Pal.SKIN_SHADOW.b, 0.45)), 1.5)

	# Mata — iris emerald terang + specular highlight
	var eye_x: float = head_c.x + 2.6 + lean * 2.0
	var eye_y: float = head_c.y - 1.6
	var blink: float = p.eye_blink
	if blink < 0.75:
		# Sclera putih
		draw_circle(Vector2(eye_x, eye_y), 2.1, _c(Color.WHITE))
		# Iris hijau zamrud
		draw_circle(Vector2(eye_x + 0.35, eye_y), 1.35, _c(Pal.EYE))
		# Pupil hitam
		draw_circle(Vector2(eye_x + 0.55, eye_y - 0.25), 0.65, _c(Pal.INK))
		# Specular glint
		draw_circle(Vector2(eye_x + 0.85, eye_y - 0.85), 0.45,
			_c(Color(1, 1, 1, 0.85)))
	else:
		# Garis kedip mata
		draw_line(Vector2(eye_x - 1.8, eye_y), Vector2(eye_x + 1.8, eye_y),
			_c(Pal.INK), 1.3)

	# Alis tajam
	draw_line(Vector2(eye_x - 1.5, eye_y - 2.8), Vector2(eye_x + 1.8, eye_y - 2.3),
		_c(Pal.HAIR), 1.0)
	# Mulut
	draw_line(head_c + Vector2(1.6 + lean, 3.2),
		head_c + Vector2(3.6 + lean, 3.0),
		_c(Color(Pal.SKIN_SHADOW.r, Pal.SKIN_SHADOW.g, Pal.SKIN_SHADOW.b, 0.65)), 0.9)


# ══════════════════════════════════════════════════════════
#  10. WEAPON — BUSUR RECURVE & ANAK PANAH ANGIN
# ══════════════════════════════════════════════════════════

func _draw_bow(p: SylaraPose, j: Dictionary) -> void:
	var grip: Vector2 = j["bow_grip"] as Vector2
	var bow_dir: Vector2 = j["bow_dir"] as Vector2
	var bow_perp: Vector2 = j["bow_perp"] as Vector2

	# Grip busur (tengah)
	var grip_poly: PackedVector2Array = PackedVector2Array([
		grip + bow_dir * 3.2 + bow_perp * 1.6,
		grip + bow_dir * 3.2 - bow_perp * 1.6,
		grip - bow_dir * 3.2 - bow_perp * 1.6,
		grip - bow_dir * 3.2 + bow_perp * 1.6,
	])
	draw_colored_polygon(grip_poly, _c(Pal.WOOD_DARK))

	# Upper limb (melengkung ke atas)
	var tip_upper: Vector2 = grip + bow_dir * BOW_LEN
	var ctrl_upper: Vector2 = grip + bow_dir * BOW_LEN * 0.55 + bow_perp * 4.5
	_draw_bow_limb(grip + bow_dir * 3.2, ctrl_upper, tip_upper, 3.2, 1.6)

	# Lower limb (melengkung ke bawah)
	var tip_lower: Vector2 = grip - bow_dir * BOW_LEN
	var ctrl_lower: Vector2 = grip - bow_dir * BOW_LEN * 0.55 - bow_perp * 4.5
	_draw_bow_limb(grip - bow_dir * 3.2, ctrl_lower, tip_lower, 3.2, 1.6)

	# Recurve horn tips
	var tip_upper_end: Vector2 = tip_upper - bow_perp * 3.2
	var tip_lower_end: Vector2 = tip_lower + bow_perp * 3.2
	draw_line(tip_upper, tip_upper_end, _c(Pal.WOOD_SHINE), 2.2)
	draw_line(tip_lower, tip_lower_end, _c(Pal.WOOD_SHINE), 2.2)

	# Gold brackets di nock tips
	draw_circle(tip_upper, 1.4, _c(Pal.GOLD))
	draw_circle(tip_lower, 1.4, _c(Pal.GOLD))

	# Tali busur
	var string_top: Vector2 = tip_upper_end
	var string_bot: Vector2 = tip_lower_end
	if p.bow_draw > 0.01:
		var mid: Vector2 = (string_top + string_bot) * 0.5
		var pull: Vector2 = bow_perp * (-p.bow_draw * 11.0)
		draw_line(string_top, mid + pull, _c(Pal.STRING), 1.3)
		draw_line(mid + pull, string_bot, _c(Pal.STRING), 1.3)
		# Anak panah saat ditarik
		if p.bow_draw > 0.25:
			var arrow_nock: Vector2 = mid + pull
			var arrow_tip: Vector2 = grip + bow_dir * (BOW_LEN + 8.0)
			_draw_arrow(arrow_nock, arrow_tip, p.bow_draw)
	else:
		draw_line(string_top, string_bot, _c(Pal.STRING), 1.3)

	# Gold trim di grip
	draw_rect(Rect2(grip.x - 1.6 + bow_perp.x, grip.y - 1.6 + bow_perp.y,
		3.2, 3.2), _c(Pal.GOLD))
	draw_rect(Rect2(grip.x - 0.8 + bow_perp.x, grip.y - 0.8 + bow_perp.y,
		1.6, 1.6), _c(Pal.GOLD_LIGHT))

	# Simpan cache koordinat busur
	_bow_grip = grip
	_bow_tip = tip_upper
	_bow_nock = (string_top + string_bot) * 0.5


func _draw_bow_limb(start: Vector2, ctrl: Vector2, end: Vector2,
		w_start: float, w_end: float) -> void:
	var n: int = 8
	var pts_outer: PackedVector2Array = PackedVector2Array()
	var pts_inner: PackedVector2Array = PackedVector2Array()
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

	var poly: PackedVector2Array = PackedVector2Array()
	for v in pts_outer:
		poly.append(v)
	for i in range(pts_inner.size() - 1, -1, -1):
		poly.append(pts_inner[i])
	draw_colored_polygon(poly, _c(Pal.WOOD))
	draw_polyline(poly, _c(Pal.INK), 0.8)

	# Highlight kayu
	for i in range(pts_outer.size() - 1):
		draw_line(pts_outer[i], pts_outer[i + 1], _c(Pal.WOOD_LIGHT), 0.9)


func _draw_arrow(nock: Vector2, tip: Vector2, _draw_amt: float) -> void:
	# Shaft kayu
	draw_line(nock, tip, _c(Pal.SHAFT), 1.6)
	var d: Vector2 = (tip - nock).normalized()
	var perp: Vector2 = Vector2(-d.y, d.x)

	# Mata panah perak runcing
	var head_poly: PackedVector2Array = PackedVector2Array([
		tip + d * 2.0,
		tip - d * 4.5 + perp * 2.4,
		tip - d * 4.5 - perp * 2.4,
	])
	draw_colored_polygon(head_poly, _c(Pal.HEAD))
	draw_polyline(head_poly, _c(Pal.INK), 0.8)
	draw_line(tip + d * 1.5, tip - d * 4.0, _c(Pal.HEAD_SHINE), 0.8)

	# Fletching bulu hijau zamrud
	var f_base: Vector2 = nock + d * 3.8
	draw_line(f_base, f_base - d * 3.2 + perp * 2.8, _c(Pal.FEATHER), 1.4)
	draw_line(f_base, f_base - d * 3.2 - perp * 2.8, _c(Pal.FEATHER), 1.4)
	draw_line(f_base - d * 1.0, f_base - d * 3.8 + perp * 2.0, _c(Pal.FEATHER_DARK), 1.0)
	draw_line(f_base - d * 1.0, f_base - d * 3.8 - perp * 2.0, _c(Pal.FEATHER_DARK), 1.0)


# ══════════════════════════════════════════════════════════
#  11. TRAIL & WEAPON SWING
# ══════════════════════════════════════════════════════════

func _draw_trail(p: SylaraPose) -> void:
	if trail_pts.size() < 3:
		return
	var n: int = trail_pts.size()
	var widths: Array[float] = [6.0, 3.5, 1.4]
	var cols: Array[Color] = [Pal.WIND_DARK, Pal.WIND, Pal.WIND_BRIGHT]
	for layer in 3:
		var w: float = widths[layer]
		var col: Color = cols[layer]
		for i in range(1, n):
			var alpha: float = float(i) / float(n)
			var c: Color = Color(col.r, col.g, col.b, alpha * 0.75 * p.alpha)
			var a: Vector2 = trail_pts[i - 1]
			var b: Vector2 = trail_pts[i]
			draw_line(a, b, c, w * alpha)


# ══════════════════════════════════════════════════════════
#  12. RIM LIGHT
# ══════════════════════════════════════════════════════════

func _draw_rim(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var rim_col: Color = Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b, 0.4 * p.alpha)
	# Head & Hood rim
	draw_arc(head_c + Vector2(-1.2, -1.2), HEAD_R * 0.95, 2.7, 4.3, 6, rim_col, 1.2)
	# Shoulder rim
	var sh_f: Vector2 = j["sh_f"] as Vector2
	draw_line(sh_f + Vector2(-1.2, -2.2), sh_f + Vector2(2.2, -3.2), rim_col, 1.2)


# ══════════════════════════════════════════════════════════
#  13. MAGIC ACCENT — WISPS & CHARGE GLOW
# ══════════════════════════════════════════════════════════

func _draw_wind_wisps(p: SylaraPose, j: Dictionary) -> void:
	if p.wind_glow < 0.05:
		return
	var glow: float = p.wind_glow
	var bow_tip: Vector2 = j["bow_tip"] as Vector2

	# Wisps di ujung busur
	var wisp_col: Color = Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b,
		0.55 * glow * p.alpha)
	for i in 3:
		var t: float = phase * 3.2 + float(i) * 2.1
		var off: Vector2 = Vector2(sin(t) * 4.5, cos(t * 1.4) * 3.5)
		draw_circle(bow_tip + off, 1.6 + sin(t * 2.0) * 0.5, wisp_col)

	# Charge glow di nock saat draw
	if p.bow_draw > 0.2:
		var nock: Vector2 = j["bow_nock"] as Vector2
		var nock_glow: Color = Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g,
			Pal.WIND_BRIGHT.b, 0.65 * p.bow_draw * p.alpha)
		draw_circle(nock, 3.2 * p.bow_draw, nock_glow)
		draw_circle(nock, 1.6 * p.bow_draw,
			Color(1, 1, 1, 0.45 * p.bow_draw * p.alpha))


func _draw_hurt_flash(p: SylaraPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var head_c: Vector2 = j["head_c"] as Vector2
	var col: Color = Color(Pal.HURT_TINT.r, Pal.HURT_TINT.g, Pal.HURT_TINT.b, 0.3 * p.hurt_tint)
	draw_circle(chest + Vector2(0.0, -1.0), 7.0, _c(col))
	draw_circle(head_c, 5.0, _c(col))
