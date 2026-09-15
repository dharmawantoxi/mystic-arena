# SylaraRenderer.gd — renderer prosedural berlapis Sylara (Godot 4.x rebuild).
#
# Satu-satunya tugas: menggambar Sylara dari SylaraPose lewat _draw().
# Tidak ada logika gameplay di sini.
#
# Lapisan gambar (sesuai standar proyek):
#   SHADOW (tanah) → BACK (cape, hair, quiver, lengan/kaki belakang)
#   → BODY (tunic, torso, kepala) → ARMOR (leather vest, belt, hood)
#   → WEAPON (lengan depan + busur recurve) → DETAIL (mata, trim, buckles)
#   → HIGHLIGHT (rim light) → MAGIC (aksen angin, hanya saat glow > 0)
#
# Gaya: pixel-art fantasy — outline tinta 1px, warna flat terkontrol dari
# SylaraPalette, semua titik di-snap ke piksel bulat supaya tajam saat
# kamera zoom. Geometri = FK sederhana dari pose (bukan node per-bagian),
# jadi biaya per-frame hanya satu CanvasItem + puluhan draw call kecil:
# aman untuk Android.
class_name SylaraRenderer
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

# ── Metrik tubuh (pixel lokal; anchor = tanah di antara dua kaki) ──
const HIP_Y := -27.0
const SPINE_LEN := 12.0
const CHEST_LEN := 8.0
const HEAD_R := 6.0
const LEG_UPPER := 11.0
const LEG_LOWER := 10.0
const FOOT_LEN := 6.0
const ARM_UPPER := 9.0
const ARM_LOWER := 8.0
const BOW_LEN := 22.0        # panjang busur recurve (tip to tip / 2)
const BOW_LIMB := 14.0       # panjang limb busur
const CAPE_SEGS: Array = [8.0, 8.0, 9.0]
const CAPE_W: Array = [5.0, 4.2, 3.0]
const HOOD_SEGS: Array = [5.0, 4.5]
const HAIR_SEGS: Array = [7.0, 6.0, 6.0]
const HAIR_W: Array = [3.8, 2.8, 1.6]

## Pose aktif (di-set root tiap frame sebelum queue_redraw).
var pose = null
## Fase global (untuk hamon shimmer, glint, wisp angin).
var phase := 0.0
## Jejak trail busur: titik GLOBAL, di-push root saat pose.trail aktif.
var trail_pts: Array = []
## Cache geometri busur — dipakai SkillFX untuk anchor nock/tip.
var _bow_grip := Vector2.ZERO
var _bow_tip := Vector2.ZERO
var _bow_nock := Vector2.ZERO


func get_bow_grip() -> Vector2:
	return _bow_grip


func get_bow_tip() -> Vector2:
	return _bow_tip


func get_bow_nock() -> Vector2:
	return _bow_nock


func _draw() -> void:
	if pose == null:
		return
	var p = pose
	if p.alpha <= 0.02:
		return
	var j := _solve(p)
	_draw_shadow(p, j)
	# ── BACK ──
	_draw_cape(p, j)
	_draw_hair(p, j)
	_draw_quiver(p, j)
	_draw_arm(p, j, true)
	_draw_calf(p, j, true)
	# ── BODY ──
	_draw_calf(p, j, false)
	_draw_tunic(p, j)
	_draw_feet(p, j)
	_draw_torso(p, j)
	# ── ARMOR ──
	_draw_belt(p, j)
	_draw_vest(p, j)
	_draw_hood(p, j)
	# ── Kepala + DETAIL ──
	_draw_head(p, j)
	# ── WEAPON ──
	_draw_trail(p)
	_draw_arm(p, j, false)
	_draw_bow(p, j)
	# ── HIGHLIGHT + MAGIC ──
	_draw_rim(p, j)
	_draw_wind_wisps(p, j)
	# ── Feedback kena pukul ──
	if p.hurt_tint > 0.01:
		draw_circle(j["chest"] + Vector2(1.0, -2.0), 5.0,
			_c(Color(Pal.HURT_TINT.r, Pal.HURT_TINT.g, Pal.HURT_TINT.b,
				0.24 * p.hurt_tint)))


# ══════════════════════════════════════════════════════════
#  FK — satu sumber kebenaran posisi tulang
# ══════════════════════════════════════════════════════════

static func _down(a: float) -> Vector2:
	return Vector2(sin(a), cos(a))


static func _fwd(a: float) -> Vector2:
	return Vector2(cos(a), -sin(a))


func _solve(p) -> Dictionary:
	var hip := Vector2(p.root_x, HIP_Y + p.root_y)
	var up1 := Vector2(sin(p.torso_lean), -cos(p.torso_lean))
	var chest := hip + up1 * SPINE_LEN
	var up2 := Vector2(sin(p.torso_lean + p.chest_flex),
		-cos(p.torso_lean + p.chest_flex))
	var neck := chest + up2 * CHEST_LEN
	var head_c := neck + up2 * HEAD_R
	var sh_f := chest + Vector2(4.2, -0.5)
	var sh_b := chest + Vector2(-4.2, -1.0)
	var hip_f := hip + Vector2(3.2, 2.0)
	var hip_b := hip + Vector2(-3.2, 2.4)
	var knee_f := hip_f + _down(p.leg_f_hip) * LEG_UPPER
	var ankle_f := knee_f + _down(p.leg_f_hip + p.leg_f_knee) * LEG_LOWER
	var toe_f := ankle_f + _fwd(p.leg_f_foot) * FOOT_LEN
	var knee_b := hip_b + _down(p.leg_b_hip) * LEG_UPPER
	var ankle_b := knee_b + _down(p.leg_b_hip + p.leg_b_knee) * LEG_LOWER
	var toe_b := ankle_b + _fwd(p.leg_b_foot) * FOOT_LEN
	var elb_f := sh_f + _down(p.arm_f_sh) * ARM_UPPER
	var hand_f := elb_f + _down(p.arm_f_sh + p.arm_f_el) * ARM_LOWER + p.bow_off
	var elb_b := sh_b + _down(p.arm_b_sh) * ARM_UPPER
	var hand_b := elb_b + _down(p.arm_b_sh + p.arm_b_el) * ARM_LOWER
	# Bow grip = hand_f, bow tip dihitung dari bow_angle.
	var bow_dir := _fwd(p.bow_angle)
	var bow_perp := Vector2(-bow_dir.y, bow_dir.x)
	_bow_grip = hand_f
	_bow_tip = hand_f + bow_dir * BOW_LEN
	var bow_mid := hand_f + bow_dir * BOW_LEN * 0.5
	_bow_nock = hand_f - bow_dir * 4.0 + bow_perp * (p.bow_draw * 10.0)
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


# ══════════════════════════════════════════════════════════
#  WARNA HELPER — alpha modulasi
# ══════════════════════════════════════════════════════════

func _c(col: Color) -> Color:
	if pose == null:
		return col
	return Color(col.r, col.g, col.b, col.a * pose.alpha)


# ══════════════════════════════════════════════════════════
#  SHADOW (tanah)
# ══════════════════════════════════════════════════════════

func _draw_shadow(p, j: Dictionary) -> void:
	var c := Vector2(0.0, 0.0)
	draw_colored_polygon(PackedVector2Array([
		c + Vector2(14, 0), c + Vector2(12, 3), c + Vector2(6, 5),
		c + Vector2(-6, 5), c + Vector2(-12, 3), c + Vector2(-14, 0),
		c + Vector2(-12, -3), c + Vector2(-6, -4), c + Vector2(6, -4),
		c + Vector2(12, -3),
	]), _c(Pal.SHADOW_GROUND))


# ══════════════════════════════════════════════════════════
#  CAPE (secondary motion)
# ══════════════════════════════════════════════════════════

func _draw_cape(p, j: Dictionary) -> void:
	var anchor := j["chest"] + Vector2(-3.0, -2.0)
	var prev := anchor
	var w := 6.0 + p.cape_flare
	for i in 3:
		var seg_len: float = CAPE_SEGS[i]
		var seg_w: float = CAPE_W[i] + p.cape_flare * (0.3 + float(i) * 0.2)
		var ang: float = p.cape[i]
		var d := Vector2(cos(ang), sin(ang))
		var perp := Vector2(-d.y, d.x)
		var next := prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.5,
			next + perp * (seg_w * 0.5 + 1.0),
			next - perp * (seg_w * 0.5 + 1.0),
			prev - perp * seg_w * 0.5,
		])
		var col := Pal.CAPE_DARK if i == 0 else (Pal.CAPE if i == 1 else Pal.CAPE_LIGHT)
		draw_colored_polygon(poly, _c(col))
		# Outline
		draw_line(poly[0], poly[1], _c(Pal.INK), 1.0)
		draw_line(poly[2], poly[3], _c(Pal.INK), 1.0)
		prev = next


# ══════════════════════════════════════════════════════════
#  HAIR (secondary motion)
# ══════════════════════════════════════════════════════════

func _draw_hair(p, j: Dictionary) -> void:
	var anchor := j["head_c"] + Vector2(-2.0, -1.0)
	var prev := anchor
	for i in 3:
		var seg_len: float = HAIR_SEGS[i]
		var seg_w: float = HAIR_W[i]
		var ang: float = p.hair[i]
		var d := Vector2(cos(ang), sin(ang))
		var perp := Vector2(-d.y, d.x)
		var next := prev + d * seg_len
		var poly := PackedVector2Array([
			prev + perp * seg_w * 0.5,
			next + perp * seg_w * 0.35,
			next - perp * seg_w * 0.35,
			prev - perp * seg_w * 0.5,
		])
		var col := Pal.HAIR if i < 2 else Pal.HAIR_LIGHT
		draw_colored_polygon(poly, _c(col))
		prev = next


# ══════════════════════════════════════════════════════════
#  QUIVER (di punggung)
# ══════════════════════════════════════════════════════════

func _draw_quiver(p, j: Dictionary) -> void:
	var base := j["chest"] + Vector2(-5.0, 2.0)
	# Tabung quiver.
	var q_poly := PackedVector2Array([
		base + Vector2(-3, -8), base + Vector2(3, -8),
		base + Vector2(4, 6), base + Vector2(-2, 6),
	])
	draw_colored_polygon(q_poly, _c(Pal.QUIVER))
	draw_polyline(q_poly, _c(Pal.INK), 1.0)
	# Ujung anak panah mencuat.
	for i in 3:
		var ax := base.x - 2.0 + float(i) * 2.5
		var ay := base.y - 9.0
		draw_line(Vector2(ax, ay), Vector2(ax, ay - 4.0), _c(Pal.SHAFT), 1.2)
		# Arrowhead.
		draw_line(Vector2(ax - 1.5, ay - 3.0), Vector2(ax, ay - 6.0), _c(Pal.HEAD), 1.0)
		draw_line(Vector2(ax + 1.5, ay - 3.0), Vector2(ax, ay - 6.0), _c(Pal.HEAD), 1.0)


# ══════════════════════════════════════════════════════════
#  LIMBS — lengan & betis
# ══════════════════════════════════════════════════════════

func _draw_arm(p, j: Dictionary, back: bool) -> void:
	var sh := j["sh_b"] if back else j["sh_f"]
	var elb := j["elb_b"] if back else j["elb_f"]
	var hand := j["hand_b"] if back else j["hand_f"]
	var w := 3.2 if back else 3.6
	# Upper arm.
	_draw_limb(sh, elb, w, Pal.CLOTH_DARK if back else Pal.CLOTH)
	# Forearm — kulit terlihat.
	_draw_limb(elb, hand, w * 0.85, Pal.SKIN_SHADOW if back else Pal.SKIN)
	# Hand.
	draw_circle(hand, 2.2, _c(Pal.SKIN_SHADOW if back else Pal.SKIN))


func _draw_calf(p, j: Dictionary, back: bool) -> void:
	var hip_j := j["hip_b"] if back else j["hip_f"]
	var knee := j["knee_b"] if back else j["knee_f"]
	var ankle := j["ankle_b"] if back else j["ankle_f"]
	var w := 3.8 if back else 4.2
	# Thigh (tertutup tunic / celana).
	_draw_limb(hip_j, knee, w, Pal.CLOTH_DARK if back else Pal.CLOTH)
	# Shin — celana ketat.
	_draw_limb(knee, ankle, w * 0.82, Pal.CLOTH_DARK if back else Pal.CLOTH)


func _draw_limb(a: Vector2, b: Vector2, w: float, col: Color) -> void:
	var d := (b - a).normalized()
	var perp := Vector2(-d.y, d.x)
	var poly := PackedVector2Array([
		a + perp * w * 0.5,
		b + perp * w * 0.42,
		b - perp * w * 0.42,
		a - perp * w * 0.5,
	])
	draw_colored_polygon(poly, _c(col))
	# Outline tipis.
	draw_line(a + perp * w * 0.5, b + perp * w * 0.42, _c(Pal.INK), 0.8)
	draw_line(a - perp * w * 0.5, b - perp * w * 0.42, _c(Pal.INK), 0.8)


func _draw_feet(p, j: Dictionary) -> void:
	for ankle_key in ["ankle_f", "ankle_b"]:
		var toe_key := "toe_f" if ankle_key == "ankle_f" else "toe_b"
		var ankle := j[ankle_key] as Vector2
		var toe := j[toe_key] as Vector2
		var boot := PackedVector2Array([
			ankle + Vector2(-2, -1), ankle + Vector2(2, -1),
			toe + Vector2(1, 0), toe + Vector2(-1, 1),
			ankle + Vector2(-3, 1),
		])
		draw_colored_polygon(boot, _c(Pal.LEATHER))
		draw_polyline(boot, _c(Pal.INK), 0.8)


# ══════════════════════════════════════════════════════════
#  TUNIC (baju utama)
# ══════════════════════════════════════════════════════════

func _draw_tunic(p, j: Dictionary) -> void:
	var hip := j["hip"] as Vector2
	var chest := j["chest"] as Vector2
	var sh_f := j["sh_f"] as Vector2
	var sh_b := j["sh_b"] as Vector2
	# Body tunic — dari bahu ke pinggul, melebar di bawah.
	var flare := 2.0 + p.cape_flare * 3.0
	var poly := PackedVector2Array([
		sh_b + Vector2(-2, -1),
		sh_f + Vector2(2, -1),
		hip + Vector2(5 + flare, 4),
		hip + Vector2(3 + flare, 8),
		hip + Vector2(-3 - flare, 8),
		hip + Vector2(-5 - flare, 4),
	])
	draw_colored_polygon(poly, _c(Pal.CLOTH))
	# Outline.
	draw_polyline(poly, _c(Pal.INK), 1.0)
	# Shadow fold — garis vertikal di tengah.
	var mid_x := (sh_f.x + sh_b.x) * 0.5
	draw_line(Vector2(mid_x, chest.y + 2), Vector2(mid_x, hip.y + 6),
		_c(Color(Pal.CLOTH_DARK.r, Pal.CLOTH_DARK.g, Pal.CLOTH_DARK.b, 0.4)), 1.2)


# ══════════════════════════════════════════════════════════
#  TORSO (dada atas)
# ══════════════════════════════════════════════════════════

func _draw_torso(p, j: Dictionary) -> void:
	var chest := j["chest"] as Vector2
	var neck := j["neck"] as Vector2
	# Area dada — tunic upper.
	var poly := PackedVector2Array([
		chest + Vector2(-5, -2),
		chest + Vector2(5, -2),
		neck + Vector2(3, 1),
		neck + Vector2(-3, 1),
	])
	draw_colored_polygon(poly, _c(Pal.CLOTH_LIGHT))


# ══════════════════════════════════════════════════════════
#  BELT (ikat pinggang)
# ══════════════════════════════════════════════════════════

func _draw_belt(p, j: Dictionary) -> void:
	var hip := j["hip"] as Vector2
	var belt := PackedVector2Array([
		hip + Vector2(-6, -1), hip + Vector2(6, -1),
		hip + Vector2(6, 2), hip + Vector2(-6, 2),
	])
	draw_colored_polygon(belt, _c(Pal.LEATHER))
	# Buckle emas.
	draw_rect(Rect2(hip.x - 2, hip.y - 1, 4, 3), _c(Pal.GOLD))
	draw_rect(Rect2(hip.x - 1.5, hip.y - 0.5, 3, 2), _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  VEST (armor kulit)
# ══════════════════════════════════════════════════════════

func _draw_vest(p, j: Dictionary) -> void:
	var chest := j["chest"] as Vector2
	# Vest — dua panel di depan dada.
	var panel_l := PackedVector2Array([
		chest + Vector2(-4, -4), chest + Vector2(-1, -5),
		chest + Vector2(-1, 3), chest + Vector2(-4, 4),
	])
	var panel_r := PackedVector2Array([
		chest + Vector2(1, -5), chest + Vector2(4, -4),
		chest + Vector2(4, 4), chest + Vector2(1, 3),
	])
	draw_colored_polygon(panel_l, _c(Pal.LEATHER_LIGHT))
	draw_colored_polygon(panel_r, _c(Pal.LEATHER_LIGHT))
	# Trim emas.
	draw_line(chest + Vector2(-4, -4), chest + Vector2(-4, 4), _c(Pal.GOLD_DARK), 1.0)
	draw_line(chest + Vector2(4, -4), chest + Vector2(4, 4), _c(Pal.GOLD_DARK), 1.0)


# ══════════════════════════════════════════════════════════
#  HOOD (tudung)
# ══════════════════════════════════════════════════════════

func _draw_hood(p, j: Dictionary) -> void:
	var neck := j["neck"] as Vector2
	var head_c := j["head_c"] as Vector2
	# Hood menutupi bahu dan sisi kepala.
	var hood_poly := PackedVector2Array([
		neck + Vector2(-6, -1),
		head_c + Vector2(-5, -HEAD_R - 2),
		head_c + Vector2(0, -HEAD_R - 4),
		head_c + Vector2(4, -HEAD_R - 1),
		neck + Vector2(5, 0),
		neck + Vector2(3, 2),
		neck + Vector2(-4, 2),
	])
	draw_colored_polygon(hood_poly, _c(Pal.HOOD))
	draw_polyline(hood_poly, _c(Pal.INK), 1.0)
	# Shadow dalam hood.
	draw_line(neck + Vector2(-4, -2), head_c + Vector2(-3, -HEAD_R),
		_c(Color(Pal.HOOD_DARK.r, Pal.HOOD_DARK.g, Pal.HOOD_DARK.b, 0.5)), 2.0)
	# Hood edges (secondary motion).
	var anchor := head_c + Vector2(-3, -HEAD_R + 1)
	var prev := anchor
	for i in 2:
		var seg_len: float = HOOD_SEGS[i]
		var ang: float = p.hood[i]
		var d := Vector2(cos(ang), sin(ang))
		var next := prev + d * seg_len
		draw_line(prev, next, _c(Pal.HOOD), 3.0)
		draw_line(prev, next, _c(Pal.INK), 0.8)
		prev = next


# ══════════════════════════════════════════════════════════
#  HEAD
# ══════════════════════════════════════════════════════════

func _draw_head(p, j: Dictionary) -> void:
	var head_c := j["head_c"] as Vector2
	var lean := p.head_lean
	# Wajah — sedikit oval.
	var face_pts := PackedVector2Array()
	for i in 12:
		var a := float(i) / 12.0 * TAU
		var rx := HEAD_R * 0.85
		var ry := HEAD_R
		face_pts.append(head_c + Vector2(cos(a) * rx + lean * 3.0, sin(a) * ry))
	draw_colored_polygon(face_pts, _c(Pal.SKIN))
	# Outline.
	draw_polyline(face_pts, _c(Pal.INK), 1.0)
	# Shadow dagu.
	draw_arc(head_c + Vector2(lean * 2.0, HEAD_R * 0.4), HEAD_R * 0.5,
		0.3, PI - 0.3, 8,
		_c(Color(Pal.SKIN_SHADOW.r, Pal.SKIN_SHADOW.g, Pal.SKIN_SHADOW.b, 0.4)), 1.5)
	# Mata — iris hijau terang.
	var eye_x := head_c.x + 2.5 + lean * 2.0
	var eye_y := head_c.y - 1.5
	var blink := p.eye_blink
	if blink < 0.8:
		# Mata terbuka.
		draw_circle(Vector2(eye_x, eye_y), 2.0, _c(Color.WHITE))
		draw_circle(Vector2(eye_x + 0.3, eye_y), 1.3, _c(Pal.EYE))
		draw_circle(Vector2(eye_x + 0.5, eye_y - 0.3), 0.6, _c(Pal.INK))
		# Kilau mata.
		draw_circle(Vector2(eye_x + 0.8, eye_y - 0.8), 0.4,
			_c(Color(1, 1, 1, 0.8)))
	else:
		# Mata tertutup (blink).
		draw_line(Vector2(eye_x - 1.5, eye_y), Vector2(eye_x + 1.5, eye_y),
			_c(Pal.INK), 1.2)
	# Mulut — garis kecil.
	draw_line(head_c + Vector2(1.5 + lean, 3.0),
		head_c + Vector2(3.5 + lean, 2.8),
		_c(Color(Pal.SKIN_SHADOW.r, Pal.SKIN_SHADOW.g, Pal.SKIN_SHADOW.b, 0.6)), 0.8)


# ══════════════════════════════════════════════════════════
#  BOW (busur recurve — senjata utama)
# ══════════════════════════════════════════════════════════

func _draw_bow(p, j: Dictionary) -> void:
	var grip := j["bow_grip"] as Vector2
	var bow_dir := j["bow_dir"] as Vector2
	var bow_perp := j["bow_perp"] as Vector2
	# Busur recurve: dua limb melengkung dari grip.
	# Grip (tengah).
	var grip_poly := PackedVector2Array([
		grip + bow_dir * 3.0 + bow_perp * 1.5,
		grip + bow_dir * 3.0 - bow_perp * 1.5,
		grip - bow_dir * 3.0 - bow_perp * 1.5,
		grip - bow_dir * 3.0 + bow_perp * 1.5,
	])
	draw_colored_polygon(grip_poly, _c(Pal.WOOD))
	# Upper limb — melengkung ke atas-depan.
	var tip_upper := grip + bow_dir * BOW_LEN
	var ctrl_upper := grip + bow_dir * BOW_LEN * 0.55 + bow_perp * 4.0
	_draw_bow_limb(grip + bow_dir * 3.0, ctrl_upper, tip_upper, 3.0, 1.5)
	# Lower limb — melengkung ke bawah-depan.
	var tip_lower := grip - bow_dir * BOW_LEN
	var ctrl_lower := grip - bow_dir * BOW_LEN * 0.55 - bow_perp * 4.0
	_draw_bow_limb(grip - bow_dir * 3.0, ctrl_lower, tip_lower, 3.0, 1.5)
	# Recurve tips — ujung melengkung balik.
	var tip_upper_end := tip_upper - bow_perp * 3.0
	var tip_lower_end := tip_lower + bow_perp * 3.0
	draw_line(tip_upper, tip_upper_end, _c(Pal.WOOD_LIGHT), 2.0)
	draw_line(tip_lower, tip_lower_end, _c(Pal.WOOD_LIGHT), 2.0)
	# Tali busur — lurus dari tip ke tip, melengkung saat ditarik.
	var string_top := tip_upper_end
	var string_bot := tip_lower_end
	if p.bow_draw > 0.01:
		# Tali ditarik — midpoint mundur.
		var mid := (string_top + string_bot) * 0.5
		var pull := bow_perp * (-p.bow_draw * 10.0)
		# Upper half.
		draw_line(string_top, mid + pull, _c(Pal.STRING), 1.2)
		# Lower half.
		draw_line(mid + pull, string_bot, _c(Pal.STRING), 1.2)
		# Anak panah di tali.
		if p.bow_draw > 0.3:
			var arrow_nock := mid + pull
			var arrow_tip := grip + bow_dir * (BOW_LEN + 6.0)
			_draw_arrow(arrow_nock, arrow_tip, p.bow_draw)
	else:
		draw_line(string_top, string_bot, _c(Pal.STRING), 1.2)
	# Gold trim di grip.
	draw_rect(Rect2(grip.x - 1.5 + bow_perp.x, grip.y - 1.5 + bow_perp.y,
		3.0, 3.0), _c(Pal.GOLD))
	# Simpan untuk SkillFX.
	_bow_grip = grip
	_bow_tip = tip_upper
	_bow_nock = (string_top + string_bot) * 0.5


func _draw_bow_limb(start: Vector2, ctrl: Vector2, end: Vector2,
		w_start: float, w_end: float) -> void:
	var n := 8
	var pts_outer := PackedVector2Array()
	var pts_inner := PackedVector2Array()
	for i in n + 1:
		var t := float(i) / float(n)
		# Quadratic bezier.
		var p := (1.0 - t) * (1.0 - t) * start + 2.0 * (1.0 - t) * t * ctrl + t * t * end
		var w := lerpf(w_start, w_end, t)
		# Normal.
		var dt := 0.01
		var t2 := minf(t + dt, 1.0)
		var p2 := (1.0 - t2) * (1.0 - t2) * start + 2.0 * (1.0 - t2) * t2 * ctrl + t2 * t2 * end
		var tangent := (p2 - p).normalized()
		var normal := Vector2(-tangent.y, tangent.x)
		pts_outer.append(p + normal * w * 0.5)
		pts_inner.append(p - normal * w * 0.5)
	var poly := PackedVector2Array()
	for v in pts_outer:
		poly.append(v)
	for i in range(pts_inner.size() - 1, -1, -1):
		poly.append(pts_inner[i])
	draw_colored_polygon(poly, _c(Pal.WOOD))
	# Highlight line.
	for i in range(pts_outer.size() - 1):
		draw_line(pts_outer[i], pts_outer[i + 1], _c(Pal.WOOD_LIGHT), 0.8)


func _draw_arrow(nock: Vector2, tip: Vector2, draw_amt: float) -> void:
	# Shaft.
	draw_line(nock, tip, _c(Pal.SHAFT), 1.5)
	# Arrowhead.
	var d := (tip - nock).normalized()
	var perp := Vector2(-d.y, d.x)
	var head_poly := PackedVector2Array([
		tip, tip - d * 4.0 + perp * 2.0, tip - d * 4.0 - perp * 2.0,
	])
	draw_colored_polygon(head_poly, _c(Pal.HEAD))
	draw_line(tip, tip - d * 4.0 + perp * 2.0, _c(Pal.HEAD_SHINE), 0.6)
	# Fletching.
	var f_base := nock + d * 4.0
	draw_line(f_base, f_base - d * 3.0 + perp * 2.5, _c(Pal.FEATHER), 1.2)
	draw_line(f_base, f_base - d * 3.0 - perp * 2.5, _c(Pal.FEATHER), 1.2)


# ══════════════════════════════════════════════════════════
#  TRAIL (weapon swing trail)
# ══════════════════════════════════════════════════════════

func _draw_trail(p) -> void:
	if trail_pts.size() < 3:
		return
	# Multi-layer trail: outer glow → body → core.
	var n := trail_pts.size()
	for layer in 3:
		var w := [5.0, 3.0, 1.2][layer]
		var col := [Pal.WIND_DARK, Pal.WIND, Pal.WIND_BRIGHT][layer]
		for i in range(1, n):
			var alpha := float(i) / float(n)
			var c := Color(col.r, col.g, col.b, alpha * 0.7 * p.alpha)
			draw_line(trail_pts[i - 1], trail_pts[i], c, w * alpha)


# ══════════════════════════════════════════════════════════
#  RIM LIGHT
# ══════════════════════════════════════════════════════════

func _draw_rim(p, j: Dictionary) -> void:
	# Rim light dari atas-kiri — tipis, kontras.
	var head_c := j["head_c"] as Vector2
	var chest := j["chest"] as Vector2
	var rim_col := Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b, 0.35 * p.alpha)
	# Head rim.
	draw_arc(head_c + Vector2(-1, -1), HEAD_R * 0.9, 2.8, 4.2, 6, rim_col, 1.0)
	# Shoulder rim.
	draw_line(j["sh_f"] + Vector2(-1, -2), j["sh_f"] + Vector2(2, -3), rim_col, 1.0)


# ══════════════════════════════════════════════════════════
#  MAGIC — wind wisps (aksen, bukan dominan)
# ══════════════════════════════════════════════════════════

func _draw_wind_wisps(p, j: Dictionary) -> void:
	if p.wind_glow < 0.05:
		return
	var glow := p.wind_glow
	var grip := j["bow_grip"] as Vector2
	var bow_tip := j["bow_tip"] as Vector2
	# Wisp kecil di ujung busur.
	var wisp_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b,
		0.5 * glow * p.alpha)
	for i in 3:
		var t := phase * 3.0 + float(i) * 2.1
		var off := Vector2(sin(t) * 4.0, cos(t * 1.3) * 3.0)
		var wisp_pos := bow_tip + off
		draw_circle(wisp_pos, 1.5 + sin(t * 2.0) * 0.5, wisp_col)
	# Glow di nock saat draw.
	if p.bow_draw > 0.2:
		var nock := j["bow_nock"] as Vector2
		var nock_glow := Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g,
			Pal.WIND_BRIGHT.b, 0.6 * p.bow_draw * p.alpha)
		draw_circle(nock, 3.0 * p.bow_draw, nock_glow)
		draw_circle(nock, 1.5 * p.bow_draw,
			Color(1, 1, 1, 0.4 * p.bow_draw * p.alpha))
