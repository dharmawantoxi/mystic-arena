# SylaraRenderer.gd — renderer prosedural Sylara (Godot native, 100% kode).
#
# PASS PIXEL-ART (v3, 2026-09-17): seluruh bentuk ditulis ulang meniru
# referensi sprite sheet "Wind Ranger — The Wind's Arrow" (pixel art):
# cel-shading flat (BASE + satu tingkat SHADOW, tanpa gradient halus),
# outline tinta 1 px di setiap siluet, hood runcing berekor, rambut oranye
# mengalir ke bawah-belakang, jubah hijau berhem zig-zag, rok bergerigi,
# belt kulit bergesper emas persegi, boots lutut bercuff, quiver diagonal
# dengan fletching di atas bahu, dan busur recurve keemasan.
#
# Satu-satunya tugas: menggambar karakter Sylara dari SylaraPose lewat
# _draw(). TIDAK ADA aset eksternal — seluruh bentuk lahir dari primitif
# CanvasItem (draw_polygon / draw_line / draw_circle / draw_arc).
#
#   * Cel-shading flat + outline INK 1 px (gaya pixel art sheet).
#   * FK 2-bone + IK jangkar pipi untuk busur: saat membidik/menarik tali,
#     lengan busur lurus ke arah bidik, tali & nock ditarik ke jangkar
#     wajah, anak panah sejajar garis bidik.
#   * BIDIK 360°: busur diarahkan ke pose.aim_angle (ruang lokal) yang
#     diisi root dari posisi target nyata (dunia → lokal) — tubuh tetap
#     menghadap sumbu hadap, busur berputar.
#   * Gravity droop: segmen jubah & rambut diberi bias sudut ke bawah
#     (y-down) di renderer supaya kain "jatuh" seperti di sheet, bukan
#     melayang horizontal.
#   * Aura per-skill digambar langsung di sini (nol aktor pool):
#     Focus Fire (cincin energi + ring tubuh + swirl tanah), Windrun
#     (swoosh angin di belakang), Shackle Shot (tether sulur ke target),
#     Powershot (channel: panah menyala hijau + sedotan angin + garis bidik).
#
# Koordinat di-snap ke piksel bulat (_sn) untuk ketajaman di semua zoom.
class_name SylaraRenderer
extends Node2D

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

# ── Metrik tubuh (anchor = tanah di antara dua kaki) ──
const HIP_Y := -26.0
const SPINE_LEN := 12.0
const CHEST_LEN := 8.5
const HEAD_R := 6.5
const LEG_UPPER := 12.0
const LEG_LOWER := 11.0
const FOOT_LEN := 6.5
const ARM_UPPER := 9.0
const ARM_LOWER := 8.5
const BOW_LEN := 19.5        # panjang setengah busur recurve (grip → tip)
const DRAW_REACH := 13.0     # jarak tarikan tali maksimum (full draw)
const CAPE_SEGS: Array = [9.0, 9.0, 10.5]
const CAPE_W: Array = [6.0, 5.2, 4.0]
const CAPE_DROOP := 0.45     # bias gravitasi segmen jubah (rad, y-down)
const HAIR_SEGS: Array = [8.5, 7.5, 7.5]
const HAIR_W: Array = [5.0, 3.2, 2.0]
const HAIR_DROOP := 0.35     # bias gravitasi segmen rambut

## Pose aktif (di-set root tiap frame sebelum queue_redraw).
var pose: SylaraPose = null
## Fase global (rotasi aura, wisp angin, shimmer).
var phase := 0.0

## Cache geometri busur — dipakai Skeleton/SkillFX untuk anchor.
var _bow_grip := Vector2.ZERO
var _bow_tip := Vector2.ZERO
var _bow_nock := Vector2.ZERO
var _bow_dir := Vector2.RIGHT
var _bow_up := Vector2.UP


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

	# 0. AMBIENT MAGIC & GROUND SHADOW & WINDRUN TRAIL
	_draw_ground_magic(p)
	_draw_shadow(p)
	_draw_windrun_trail(p)

	# 1. BACK (jubah, rambut, quiver, lengan penarik belakang, kaki belakang)
	_draw_cape(p, j)
	_draw_hair(p, j)
	_draw_quiver(j)
	_draw_drawing_arm(p, j)
	_draw_calf(p, j, true)
	_draw_foot(j, true)

	# 2. BODY (kaki depan, boots, rok, torso, belt)
	_draw_calf(p, j, false)
	_draw_foot(j, false)
	_draw_skirt(p, j)
	_draw_torso(j)
	_draw_belt(j)
	_draw_pauldron(j)

	# 3. KEPALA & WAJAH (hood runcing, poni oranye, mata zamrud)
	_draw_head_and_hood(p, j)

	# 4. WEAPON (lengan busur depan & busur recurve + tali + panah)
	_draw_bow_arm(p, j)
	_draw_bow(p, j)

	# 5. AURA & MAGIC (fokus, channel, tether, rim, wisp)
	_draw_focus_aura(p, j)
	_draw_channel(p, j)
	_draw_tether(p, j)
	_draw_rim(j)
	_draw_wind_wisps(p, j)

	# 6. FEEDBACK DAMAGE
	if p.hurt_tint > 0.01:
		_draw_hurt_flash(p, j)


# ══════════════════════════════════════════════════════════
#  FK — SATU SUMBER POSISI TULANG (busur bebas 360°)
# ══════════════════════════════════════════════════════════

static func _down(a: float) -> Vector2:
	return Vector2(sin(a), cos(a))


func _solve(p: SylaraPose) -> Dictionary:
	var hip: Vector2 = Vector2(p.root_x, HIP_Y + p.root_y)
	# Torso sedikit "twist" mengikuti arah bidik (membaca natural di 2D).
	var aim := p.aim_angle + p.bow_offset
	var lean := p.torso_lean + sin(aim) * 0.05
	var up1: Vector2 = Vector2(sin(lean), -cos(lean))
	var chest: Vector2 = hip + up1 * SPINE_LEN
	var up2: Vector2 = Vector2(sin(lean + p.chest_flex),
		-cos(lean + p.chest_flex))
	var neck: Vector2 = chest + up2 * CHEST_LEN
	var head_c: Vector2 = neck + up2 * HEAD_R
	var sh_f: Vector2 = chest + Vector2(4.4, -0.6)
	var sh_b: Vector2 = chest + Vector2(-3.8, -1.0)
	var hip_f: Vector2 = hip + Vector2(3.2, 1.8)
	var hip_b: Vector2 = hip + Vector2(-3.2, 2.2)

	var knee_f: Vector2 = hip_f + _down(p.leg_f_hip) * LEG_UPPER
	var ankle_f: Vector2 = knee_f + _down(p.leg_f_hip + p.leg_f_knee) * LEG_LOWER
	var toe_f: Vector2 = ankle_f + Vector2(cos(p.leg_f_foot),
		-sin(p.leg_f_foot)) * FOOT_LEN

	var knee_b: Vector2 = hip_b + _down(p.leg_b_hip) * LEG_UPPER
	var ankle_b: Vector2 = knee_b + _down(p.leg_b_hip + p.leg_b_knee) * LEG_LOWER
	var toe_b: Vector2 = ankle_b + Vector2(cos(p.leg_b_foot),
		-sin(p.leg_b_foot)) * FOOT_LEN

	# ── ORIENTASI BUSUR: arah bidik lokal penuh (0..2PI) ──
	var bow_dir := Vector2(cos(aim), sin(aim))
	var bow_up := Vector2(sin(aim), -cos(aim))

	# ── LENGAN DEPAN (bow arm): lurus ke arah busur saat membidik ──
	var elb_f: Vector2 = sh_f + _down(p.arm_f_sh) * ARM_UPPER
	var hand_f: Vector2 = elb_f + _down(p.arm_f_sh + p.arm_f_el) * ARM_LOWER + p.bow_off
	_bow_grip = hand_f
	_bow_tip = hand_f + bow_up * BOW_LEN

	# Nock: ditarik mundur searah -bidik.
	var pull_dist: float = p.bow_draw * DRAW_REACH
	_bow_nock = hand_f - bow_dir * pull_dist

	# ── LENGAN BELAKANG (drawing arm): IK — tangan menempel nock ──
	var hand_b: Vector2
	var elb_b: Vector2
	if p.bow_draw > 0.05:
		hand_b = _bow_nock
		var to_hand: Vector2 = hand_b - sh_b
		var n := to_hand.length()
		var mid: Vector2 = sh_b + to_hand * 0.5
		if n > 0.001:
			var perp: Vector2 = Vector2(-to_hand.y, to_hand.x) / n
			elb_b = mid + perp * 1.6
		else:
			elb_b = mid
	else:
		elb_b = sh_b + _down(p.arm_b_sh) * ARM_UPPER
		hand_b = elb_b + _down(p.arm_b_sh + p.arm_b_el) * ARM_LOWER

	_bow_up = bow_up
	_bow_dir = bow_dir

	var j := {
		"hip": hip, "chest": chest, "neck": neck, "head_c": head_c,
		"sh_f": sh_f, "sh_b": sh_b, "hip_f": hip_f, "hip_b": hip_b,
		"knee_f": knee_f, "knee_b": knee_b,
		"ankle_f": ankle_f, "ankle_b": ankle_b,
		"toe_f": toe_f, "toe_b": toe_b,
		"elb_f": elb_f, "elb_b": elb_b,
		"hand_f": hand_f, "hand_b": hand_b,
		"bow_grip": hand_f, "bow_tip": _bow_tip,
		"bow_up": bow_up, "bow_dir": bow_dir,
		"bow_nock": _bow_nock,
	}
	_clamp_ground(j)
	return j


static func _clamp_ground(j: Dictionary) -> void:
	for key in ["hip", "chest", "neck", "head_c", "elb_f", "hand_f",
			"elb_b", "hand_b", "knee_f", "ankle_f", "toe_f",
			"knee_b", "ankle_b", "toe_b"]:
		var pt: Vector2 = j[key]
		if pt.y > -0.5:
			j[key] = Vector2(pt.x, -0.5)


# ══════════════════════════════════════════════════════════
#  PRIMITIF — CEL-SHADING FLAT + OUTLINE TINTA 1 PX
# ══════════════════════════════════════════════════════════

func _c(col: Color) -> Color:
	if pose == null or pose.alpha >= 0.999:
		return col
	return Color(col.r, col.g, col.b, col.a * pose.alpha)


static func _sn(v: Vector2) -> Vector2:
	return v.round()


## Poligon flat + outline tinta tertutup (gaya pixel art).
func _shape(pts: PackedVector2Array, col: Color, outline: bool = true) -> void:
	var snapped := PackedVector2Array()
	for pt in pts:
		snapped.append(_sn(pt))
	draw_colored_polygon(snapped, _c(col))
	if outline and snapped.size() > 2:
		var closed := PackedVector2Array(snapped)
		closed.append(snapped[0])
		draw_polyline(closed, _c(Pal.INK), 1.0)


func _poly(pts: PackedVector2Array, col: Color) -> void:
	_shape(pts, col, false)


func _line(a: Vector2, b: Vector2, w: float, col: Color) -> void:
	draw_line(_sn(a), _sn(b), _c(col), w)


func _capsule(a: Vector2, b: Vector2, w: float, col: Color) -> void:
	_poly(_capsule_pts(a, b, w + 1.6), Pal.INK)
	_poly(_capsule_pts(a, b, w), col)


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
		outline: bool = true) -> void:
	if outline:
		_poly(_taper_pts(a, wa + 1.6, b, wb + 1.6), Pal.INK)
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
#  0. AMBIENT GROUND MAGIC & SHADOW & WINDRUN TRAIL
# ══════════════════════════════════════════════════════════

func _draw_ground_magic(p: SylaraPose) -> void:
	var c := Vector2(p.root_x * 0.35, 0.0)
	var rot := phase * 0.70

	# Halo lembut sihir angin di tanah.
	draw_circle(c, 24.0, Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.10 * p.alpha))

	var ring_col := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.22 * p.alpha)
	var glow_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g,
		Pal.WIND_LIGHT.b, 0.35 * p.alpha)
	for i in 3:
		var start_a: float = rot + float(i) * TAU / 3.0
		var end_a: float = start_a + 1.25
		draw_arc(c, 20.0, start_a, end_a, 12, ring_col, 1.2, true)
		var glyph_p: Vector2 = c + Vector2(cos(end_a), sin(end_a) * 0.45) * 20.0
		draw_circle(glyph_p, 1.4, glow_col)

	# Daun melayang mengitari sang ranger.
	for i in 3:
		var a: float = rot * 1.3 + float(i) * TAU / 3.0
		var r: float = 16.5 + sin(phase * 2.0 + float(i)) * 3.0
		var lp: Vector2 = c + Vector2(cos(a) * r, sin(a) * (r * 0.42) - 2.0)
		var leaf_c := Pal.LEAF_GOLD if (i % 2 == 0) else Pal.LEAF
		draw_circle(lp, 1.1, Color(leaf_c.r, leaf_c.g, leaf_c.b, 0.50 * p.alpha))


func _draw_shadow(p: SylaraPose) -> void:
	var rx := 14.0 + absf(p.root_x) * 0.3
	var c := Vector2(p.root_x * 0.5, 1.0)
	var pts := PackedVector2Array()
	for i in 14:
		var a := float(i) * TAU / 14.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * 3.8))
	_poly(pts, Pal.SHADOW_GROUND)


## Trail angin Windrun: swoosh horizontal mengalir ke belakang seperti
## streak di sprite sheet (garis tapered + curl di ekor), digambar
## renderer supaya durasi buff 3 dtk tetap gratis (nol aktor pool).
func _draw_windrun_trail(p: SylaraPose) -> void:
	if p.windrun < 0.03:
		return
	var a_base := 0.55 * p.windrun * p.alpha
	var col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, a_base)
	var col2 := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, a_base * 0.8)
	for i in 3:
		var t: float = phase * 5.0 + float(i) * 1.9
		var y: float = -34.0 + float(i) * 9.0 + sin(t) * 1.5
		var x0: float = -7.0 - float(i) * 1.5
		var len: float = 22.0 + 8.0 * (0.5 + 0.5 * sin(t * 1.3))
		# Swoosh utama: tebal di depan, menipis ke ekor.
		_line(Vector2(x0, y), Vector2(x0 - len * 0.6, y + 1.0), 2.2, col)
		_line(Vector2(x0 - len * 0.6, y + 1.0), Vector2(x0 - len, y + 2.0), 1.2, col)
		# Curl angin di ekor swoosh.
		draw_arc(_sn(Vector2(x0 - len, y + 2.0)), 2.6, PI * 0.6, PI * 1.7, 8, col2, 1.2, true)
	# Jejak gale di tanah (elips tipis ke belakang).
	var tc := Vector2(p.root_x * 0.5 - 10.0, 1.5)
	draw_arc(tc, 12.0, PI * 0.75, PI * 1.25, 8, col2, 1.4, true)


# ══════════════════════════════════════════════════════════
#  1. CAPE (jubah hijau berhem zig-zag, jatuh ke belakang)
# ══════════════════════════════════════════════════════════

func _draw_cape(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["chest"] as Vector2) + Vector2(-3.4, -2.0)
	var prev := anchor
	var layers: Array = []

	# Rantai segmen dengan gravity droop (kain jatuh seperti di sheet).
	for i in 3:
		var ang: float = float(p.cape[i]) - CAPE_DROOP - float(i) * 0.22
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * float(CAPE_SEGS[i])
		layers.append([prev, next, perp, float(CAPE_W[i]), d, ang])
		prev = next

	# Lapisan dalam (bayangan) — tanpa outline.
	for L in layers:
		var a: Vector2 = L[0]; var b: Vector2 = L[1]; var perp: Vector2 = L[2]
		var w: float = L[3]
		_poly(PackedVector2Array([
			a + perp * w * 0.50, b + perp * w * 0.55,
			b - perp * w * 0.55, a - perp * w * 0.50,
		]), Pal.CAPE_DARK)

	# Lapisan luar hijau + hem zig-zag dua titik di segmen akhir.
	for i in 3:
		var L: Array = layers[i]
		var a: Vector2 = L[0]; var b: Vector2 = L[1]; var perp: Vector2 = L[2]
		var w: float = L[3] + p.cape_flare * (0.3 + float(i) * 0.2)
		var d: Vector2 = L[4]
		var pts := PackedVector2Array([
			a + perp * w * 0.48, b + perp * w * 0.56,
		])
		if i == 2:
			pts.append(b + perp * w * 0.30 - d * 2.5)
			pts.append(b - d * 1.0)
			pts.append(b - perp * w * 0.30 - d * 2.5)
		pts.append(b - perp * w * 0.56)
		pts.append(a - perp * w * 0.48)
		_shape(pts, Pal.CAPE)
		# Kilau kain di tepi atas.
		_line(a + perp * 0.6, b + perp * 0.8, 1.0, Pal.CAPE_LIGHT)


# ══════════════════════════════════════════════════════════
#  2. HAIR (ekor rambut oranye mengalir ke bawah-belakang)
# ══════════════════════════════════════════════════════════

func _draw_hair(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["head_c"] as Vector2) + Vector2(-2.5, -0.6)
	var prev: Vector2 = anchor
	for i in 3:
		var ang: float = float(p.hair[i]) - HAIR_DROOP - float(i) * 0.15
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * float(HAIR_SEGS[i])
		var col: Color = Pal.HAIR_DARK if i == 2 else Pal.HAIR
		_taper(prev, float(HAIR_W[i]), next, float(HAIR_W[i]) * 0.6, col)
		_line(prev + perp * 0.3, next + perp * 0.2, 0.9, Pal.HAIR_SHINE)
		prev = next


# ══════════════════════════════════════════════════════════
#  3. QUIVER (diagonal di punggung, fletching di atas bahu)
# ══════════════════════════════════════════════════════════

func _draw_quiver(j: Dictionary) -> void:
	var base: Vector2 = (j["chest"] as Vector2) + Vector2(-4.6, 1.0)
	var qdir := Vector2(-0.42, -0.91)   # arah atas-belakang
	var qperp := Vector2(0.91, -0.42)
	var qtop: Vector2 = base + qdir * 13.0
	_shape(PackedVector2Array([
		base + qperp * 2.6, qtop + qperp * 2.2,
		qtop - qperp * 2.2, base - qperp * 2.6,
	]), Pal.LEATHER)
	# Band emas di mulut quiver.
	_line(base + qperp * 2.4 + qdir * 10.0, qtop + qperp * 2.0, 1.1, Pal.GOLD_LIGHT)

	# 3 anak panah: shaft + fletching zamrud menyembul di atas bahu.
	for i in 3:
		var off: float = (float(i) - 1.0) * 1.5
		var b: Vector2 = qtop + qperp * off
		var t: Vector2 = b + qdir * 4.5
		_line(b, t, 1.0, Pal.SHAFT)
		_line(t, t + Vector2(-1.2, 1.4), 1.2, Pal.FEATHER)
		_line(t, t + Vector2(1.2, 1.4), 1.2, Pal.FEATHER)
		draw_circle(_sn(t), 0.6, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  4. ARMS & LEGS (lengan panahan + kaki boots lutut)
# ══════════════════════════════════════════════════════════

func _draw_drawing_arm(_p: SylaraPose, j: Dictionary) -> void:
	var sh: Vector2 = j["sh_b"] as Vector2
	var elb: Vector2 = j["elb_b"] as Vector2
	var hand: Vector2 = j["hand_b"] as Vector2
	_taper(sh, 4.6, elb, 3.8, Pal.CLOTH_DARK)
	_taper(elb, 3.6, hand, 3.0, Pal.SKIN_SHADOW)
	draw_circle(_sn(hand), 2.0, _c(Pal.SKIN_SHADOW))


func _draw_bow_arm(_p: SylaraPose, j: Dictionary) -> void:
	var sh: Vector2 = j["sh_f"] as Vector2
	var elb: Vector2 = j["elb_f"] as Vector2
	var hand: Vector2 = j["hand_f"] as Vector2
	_taper(sh, 5.2, elb, 4.2, Pal.CLOTH_LIGHT)
	# Bracer kulit di lengan depan.
	_taper(elb, 4.0, hand, 3.4, Pal.LEATHER_LIGHT)
	_line(elb.lerp(hand, 0.4), elb.lerp(hand, 0.6), 1.1, Pal.GOLD_LIGHT)
	draw_circle(_sn(hand), 2.0, _c(Pal.SKIN))


func _draw_calf(_p: SylaraPose, j: Dictionary, is_back: bool) -> void:
	var hip_j: Vector2 = (j["hip_b"] if is_back else j["hip_f"]) as Vector2
	var knee: Vector2 = (j["knee_b"] if is_back else j["knee_f"]) as Vector2
	var ankle: Vector2 = (j["ankle_b"] if is_back else j["ankle_f"]) as Vector2
	var pants_col: Color = Pal.CLOTH_DARK if is_back else Pal.CLOTH
	_taper(hip_j, 5.4, knee, 4.4, pants_col)
	draw_circle(_sn(knee), 2.2, _c(pants_col))
	# Boots lutut kulit.
	var boot_col: Color = Pal.LEATHER_DARK if is_back else Pal.LEATHER
	_taper(knee, 4.6, ankle, 3.6, boot_col)


func _draw_foot(j: Dictionary, is_back: bool) -> void:
	var ankle: Vector2 = (j["ankle_b"] if is_back else j["ankle_f"]) as Vector2
	var toe: Vector2 = (j["toe_b"] if is_back else j["toe_f"]) as Vector2
	var col: Color = Pal.LEATHER_DARK if is_back else Pal.LEATHER
	_capsule(ankle + Vector2(0.0, 0.8), toe + Vector2(0.5, 0.8), 3.4, col)
	if not is_back:
		# Cuff boots terlipat + rivet emas.
		_capsule(ankle + Vector2(-2.2, -1.8), ankle + Vector2(2.2, -1.8), 2.4, Pal.LEATHER_LIGHT)
		draw_circle(_sn(ankle + Vector2(0.8, -1.8)), 0.8, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  5. SKIRT / TORSO / BELT / PAULDRON
# ══════════════════════════════════════════════════════════

## Rok tunik dengan hem bergerigi tiga titik (sprite sheet).
func _draw_skirt(p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var flare: float = 1.6 + p.cape_flare * 2.2
	_shape(PackedVector2Array([
		hip + Vector2(-4.2, -2.0),
		hip + Vector2(4.2, -2.0),
		hip + Vector2(4.8 + flare, 5.0),
		hip + Vector2(2.4 + flare, 7.8),
		hip + Vector2(0.0, 5.8),
		hip + Vector2(-2.4 - flare, 7.8),
		hip + Vector2(-4.8 - flare, 5.0),
	]), Pal.CLOTH)
	# Bayangan hard-edge di separuh belakang rok.
	_poly(PackedVector2Array([
		hip + Vector2(-4.2, -2.0),
		hip + Vector2(-1.0, -2.0),
		hip + Vector2(-1.0, 5.8),
		hip + Vector2(-2.4 - flare, 7.8),
		hip + Vector2(-4.8 - flare, 5.0),
	]), Pal.CLOTH_DARK)


func _draw_torso(j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var chest: Vector2 = j["chest"] as Vector2
	var neck: Vector2 = j["neck"] as Vector2
	_taper(hip, 11.0, chest, 9.8, Pal.CLOTH_DARK)
	_taper(chest, 9.8, neck, 6.8, Pal.CLOTH)
	# Tali quiver menyilang di dada.
	_line(chest + Vector2(3.6, -2.6), hip + Vector2(-3.6, -0.6), 1.6, Pal.LEATHER_DARK)


func _draw_belt(j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	_capsule(hip + Vector2(-4.8, -0.6), hip + Vector2(4.8, -0.6), 2.8, Pal.LEATHER_DARK)
	# Gesper emas persegi (pixel sheet).
	_shape(PackedVector2Array([
		hip + Vector2(-0.2, -2.0), hip + Vector2(2.2, -2.0),
		hip + Vector2(2.2, 0.6), hip + Vector2(-0.2, 0.6),
	]), Pal.GOLD)
	draw_circle(_sn(hip + Vector2(1.0, -0.7)), 0.6, _c(Pal.GOLD_HOT))


func _draw_pauldron(j: Dictionary) -> void:
	var sh_f: Vector2 = j["sh_f"] as Vector2
	_shape(PackedVector2Array([
		sh_f + Vector2(-2.6, -2.2), sh_f + Vector2(2.8, -1.6),
		sh_f + Vector2(2.2, 1.6), sh_f + Vector2(-2.8, 1.0),
	]), Pal.LEATHER)
	draw_circle(_sn(sh_f + Vector2(0.0, -0.4)), 0.7, _c(Pal.GOLD_LIGHT))


# ══════════════════════════════════════════════════════════
#  6. HOOD RUNCING & WAJAH
# ══════════════════════════════════════════════════════════

func _draw_head_and_hood(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	# Kepala sedikit mengikuti arah bidik.
	var lean: float = p.head_lean + sin(p.aim_angle + p.bow_offset) * 0.04
	var lc := head_c + Vector2(lean * 1.5, 0.0)

	# Wajah (kulit) — lingkaran + outline tinta.
	draw_circle(_sn(head_c), HEAD_R, _c(Pal.SKIN))
	draw_arc(_sn(head_c), HEAD_R + 0.4, 0.0, TAU, 12, _c(Pal.INK), 1.0)

	# Hood runcing: menutupi puncak & belakang kepala + ekor terjuntai.
	_shape(PackedVector2Array([
		lc + Vector2(4.2, -2.5),
		lc + Vector2(2.2, -HEAD_R - 2.2),
		lc + Vector2(-2.8, -HEAD_R - 2.8),
		lc + Vector2(-5.6, -HEAD_R - 0.5),
		lc + Vector2(-6.6, -0.6),
		lc + Vector2(-8.2, 2.6),      # ujung hood terjuntai ke belakang
		lc + Vector2(-5.2, 1.6),
		lc + Vector2(-2.2, 0.4),
	]), Pal.HOOD)
	_line(lc + Vector2(-2.8, -HEAD_R - 2.8), lc + Vector2(2.2, -HEAD_R - 2.2), 1.2, Pal.HOOD_LIGHT)

	# Poni oranye bergerigi di bawah rim hood.
	_shape(PackedVector2Array([
		lc + Vector2(-1.0, -HEAD_R + 1.0),
		lc + Vector2(3.4, -HEAD_R + 1.6),
		lc + Vector2(4.0, -2.6),
		lc + Vector2(2.6, -3.4),
		lc + Vector2(1.8, -1.8),
		lc + Vector2(0.6, -3.2),
		lc + Vector2(-0.2, -1.6),
	]), Pal.HAIR)
	# Side lock menjuntai di sisi wajah.
	_taper(lc + Vector2(-1.4, -1.0), 2.2, lc + Vector2(-2.2, 4.6), 1.0, Pal.HAIR)

	# Mata zamrud + alis + mulut.
	var eye_c := lc + Vector2(2.2, -1.0)
	var open: float = 1.0 - clampf(p.eye_blink, 0.0, 1.0)
	if open > 0.4:
		_line(eye_c + Vector2(-1.4, -1.6), eye_c + Vector2(1.4, -1.2), 0.9, Pal.HAIR_DARK)
		draw_circle(_sn(eye_c), 1.1, _c(Pal.EYE_DARK))
		draw_circle(_sn(eye_c + Vector2(0.2, -0.1)), 0.6, _c(Pal.EYE))
		draw_circle(_sn(eye_c + Vector2(0.4, -0.4)), 0.4, _c(Pal.EYE_WHITE))
	else:
		_line(eye_c + Vector2(-1.2, 0.0), eye_c + Vector2(1.4, 0.0), 1.2, Pal.INK)
	_line(lc + Vector2(1.8, 2.8), lc + Vector2(3.2, 2.8), 0.9, Pal.LIP)
	draw_circle(_sn(lc + Vector2(2.6, 1.4)), 1.2,
		_c(Color(Pal.SKIN_BLUSH.r, Pal.SKIN_BLUSH.g, Pal.SKIN_BLUSH.b, 0.30)))


# ══════════════════════════════════════════════════════════
#  7. WEAPON — BUSUR RECURVE KEEMASAN (arah bebas 360°)
# ══════════════════════════════════════════════════════════

func _draw_bow(p: SylaraPose, j: Dictionary) -> void:
	var grip: Vector2 = j["bow_grip"] as Vector2
	var bow_up: Vector2 = j["bow_up"] as Vector2
	var bow_dir: Vector2 = j["bow_dir"] as Vector2

	# Grip busur berbalut kulit gelap.
	_capsule(grip - bow_up * 3.0, grip + bow_up * 3.0, 3.0, Pal.WOOD_DARK)
	_line(grip - bow_dir * 1.5, grip + bow_dir * 1.5, 1.0, Pal.GOLD_LIGHT)

	# Limb atas & bawah (recurve melengkung ke arah bidik).
	var tip_upper: Vector2 = grip + bow_up * BOW_LEN
	var ctrl_upper: Vector2 = grip + bow_up * (BOW_LEN * 0.55) + bow_dir * 4.2
	_draw_recurve_limb(grip + bow_up * 3.0, ctrl_upper, tip_upper)

	var tip_lower: Vector2 = grip - bow_up * BOW_LEN
	var ctrl_lower: Vector2 = grip - bow_up * (BOW_LEN * 0.55) + bow_dir * 4.2
	_draw_recurve_limb(grip - bow_up * 3.0, ctrl_lower, tip_lower)

	# Ujung tanduk gading + cincin emas.
	var tip_upper_end: Vector2 = tip_upper - bow_dir * 2.4
	var tip_lower_end: Vector2 = tip_lower - bow_dir * 2.4
	_line(tip_upper, tip_upper_end, 2.0, Pal.HORN_TIP)
	_line(tip_lower, tip_lower_end, 2.0, Pal.HORN_TIP)
	draw_circle(_sn(tip_upper), 1.0, _c(Pal.GOLD_LIGHT))
	draw_circle(_sn(tip_lower), 1.0, _c(Pal.GOLD_LIGHT))

	# Powershot: limb busur menyala hijau saat channel.
	if p.channel > 0.05:
		var gcol := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b,
			0.55 * p.channel * p.alpha)
		_draw_limb_glow(grip + bow_up * 3.0, ctrl_upper, tip_upper, gcol)
		_draw_limb_glow(grip - bow_up * 3.0, ctrl_lower, tip_lower, gcol)

	# Tali busur.
	if p.bow_draw > 0.02:
		var nock: Vector2 = j["bow_nock"] as Vector2
		_line(tip_upper_end, nock, 2.0, Pal.STRING_GLOW)
		_line(nock, tip_lower_end, 2.0, Pal.STRING_GLOW)
		_line(tip_upper_end, nock, 1.0, Pal.STRING)
		_line(nock, tip_lower_end, 1.0, Pal.STRING)
		# Anak panah sejajar garis bidik.
		var arrow_tip: Vector2 = grip + bow_dir * 11.5
		_draw_arrow(nock, arrow_tip)
		# Powershot: panah charge menyala hijau-kuning (sheet).
		if p.channel > 0.03:
			_draw_charged_arrow(nock, arrow_tip, bow_dir, p.channel)
	else:
		_line(tip_upper_end, tip_lower_end, 1.6, Pal.STRING_GLOW)
		_line(tip_upper_end, tip_lower_end, 1.0, Pal.STRING)


func _draw_recurve_limb(start: Vector2, ctrl: Vector2, end: Vector2) -> void:
	var steps := 8
	var pts := PackedVector2Array([start])
	for i in range(1, steps + 1):
		var t := float(i) / float(steps)
		pts.append((1.0 - t) * (1.0 - t) * start + 2.0 * (1.0 - t) * t * ctrl + t * t * end)
	# Pass outline tinta, lalu kayu flat, lalu urat kayu terang.
	for i in range(steps):
		var w := lerpf(3.0, 1.4, float(i) / float(steps))
		_line(pts[i], pts[i + 1], w + 1.4, Pal.INK)
	for i in range(steps):
		var w := lerpf(3.0, 1.4, float(i) / float(steps))
		_line(pts[i], pts[i + 1], w, Pal.WOOD)
	for i in range(steps):
		_line(pts[i], pts[i + 1], 0.8, Pal.WOOD_LIGHT)


func _draw_limb_glow(start: Vector2, ctrl: Vector2, end: Vector2, col: Color) -> void:
	var steps := 6
	var p_prev := start
	for i in range(1, steps + 1):
		var t := float(i) / float(steps)
		var pt := (1.0 - t) * (1.0 - t) * start + 2.0 * (1.0 - t) * t * ctrl + t * t * end
		draw_line(_sn(p_prev), _sn(pt), _c(col), 1.4)
		p_prev = pt


## Panah charge Powershot: shaft + kepala bersinar hijau-kuning.
func _draw_charged_arrow(nock: Vector2, tip: Vector2, d: Vector2, ch: float) -> void:
	var a := ch * (pose.alpha if pose != null else 1.0)
	var glow := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.55 * a)
	var bright := Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b, 0.9 * a)
	_line(nock, tip, 3.2, glow)
	_line(nock, tip + d * 2.0, 1.2, bright)
	draw_circle(_sn(tip + d * 1.5), 2.2 + 2.0 * ch, glow)
	draw_circle(_sn(tip + d * 1.5), 1.2 + 1.0 * ch, bright)
	# Percik angin di ekor panah.
	for i in 2:
		var t: float = phase * 6.0 + float(i) * PI
		var off := Vector2(cos(t), sin(t)) * (3.0 + 2.0 * ch)
		draw_circle(_sn(nock + off), 1.0,
			Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.6 * a))


func _draw_arrow(nock: Vector2, tip: Vector2) -> void:
	_line(nock, tip, 1.5, Pal.SHAFT)
	_line(nock, tip, 0.7, Pal.WOOD_SHINE)
	var d: Vector2 = (tip - nock).normalized()
	var perp: Vector2 = Vector2(-d.y, d.x)
	# Mata panah perak.
	_shape(PackedVector2Array([
		tip + d * 2.6,
		tip - d * 3.8 + perp * 2.0,
		tip - d * 2.8,
		tip - d * 3.8 - perp * 2.0,
	]), Pal.HEAD)
	_line(tip + d * 2.0, tip - d * 3.4, 0.9, Pal.HEAD_SHINE)
	# Fletching bulu zamrud ganda.
	var f_base: Vector2 = nock + d * 3.4
	_line(f_base, f_base - d * 3.0 + perp * 2.2, 1.3, Pal.FEATHER)
	_line(f_base, f_base - d * 3.0 - perp * 2.2, 1.3, Pal.FEATHER)
	_line(f_base + perp * 1.0, f_base - perp * 1.0, 1.1, Pal.GOLD_LIGHT)


# ══════════════════════════════════════════════════════════
#  8. AURA PER-SKILL (digambar renderer — nol aktor pool)
# ══════════════════════════════════════════════════════════

## Focus Fire: cincin energi di busur + ring tubuh + swirl tanah (sheet R).
func _draw_focus_aura(p: SylaraPose, j: Dictionary) -> void:
	if p.focus_glow < 0.03:
		return
	var grip: Vector2 = j["bow_grip"] as Vector2
	var nock: Vector2 = j["bow_nock"] as Vector2
	var chest: Vector2 = j["chest"] as Vector2
	var g: float = p.focus_glow * p.alpha
	var col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.30 * g)
	var rot := phase * 2.6
	draw_arc(grip, 16.0, rot, rot + 1.8, 14, col, 1.2, true)
	draw_arc(grip, 20.0, rot + PI, rot + PI + 1.8, 14, col, 1.0, true)

	# Ring melingkar di sekeliling tubuh (fokus konsentrasi).
	var body_col := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.40 * g)
	draw_arc(_sn(chest + Vector2(0.0, 4.0)), 22.0, rot * 0.8, rot * 0.8 + 2.2, 16, body_col, 1.4, true)
	draw_arc(_sn(chest + Vector2(0.0, 4.0)), 22.0, rot * 0.8 + PI, rot * 0.8 + PI + 2.2, 16, body_col, 1.4, true)

	# Swirl rune di tanah (lingkaran sihir sheet).
	var gc := Vector2(p.root_x * 0.35, 0.0)
	draw_arc(gc, 15.0, -rot, -rot + 2.6, 16, body_col, 1.6, true)
	draw_arc(gc, 11.0, -rot + 1.5, -rot + 3.6, 12, col, 1.2, true)

	# Ember kecil mengelilingi nock.
	var ea: float = phase * 4.2
	draw_circle(nock + Vector2(cos(ea), sin(ea)) * 5.0, 1.2,
		Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b, 0.5 * g))
	draw_circle(nock + Vector2(cos(ea + PI), sin(ea + PI)) * 5.0, 1.0,
		Color(Pal.LEAF_GOLD.r, Pal.LEAF_GOLD.g, Pal.LEAF_GOLD.b, 0.45 * g))


## Powershot channel: inti nock + sedotan angin + garis bidik.
func _draw_channel(p: SylaraPose, j: Dictionary) -> void:
	if p.channel < 0.03:
		return
	var nock: Vector2 = j["bow_nock"] as Vector2
	var ch: float = p.channel * p.alpha

	# Inti energi membesar di nock.
	draw_circle(_sn(nock), 2.0 + 3.0 * p.channel,
		Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b, 0.85 * ch))
	draw_circle(_sn(nock), 4.5 + 3.0 * p.channel,
		Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.30 * ch))

	# Sedotan angin: 3 busur yang MENYUSUT ke nock seiring charge.
	var suck_r: float = 26.0 * (1.0 - p.channel) + 9.0
	var rot := phase * 3.4
	var col := Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.40 * ch)
	for i in 3:
		var a0: float = rot + float(i) * TAU / 3.0
		draw_arc(_sn(nock), suck_r, a0, a0 + 1.1, 10, col, 1.3, true)

	# Garis bidik samar menuju titik sasaran (4 segmen putus-putus).
	var aim_pt: Vector2 = p.aim_point_local
	var d: Vector2 = aim_pt - nock
	if d.length() > 30.0:
		var dn: Vector2 = d.normalized()
		var line_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g,
			Pal.WIND_LIGHT.b, 0.22 * ch)
		for i in 4:
			var t0: float = 0.15 + float(i) * 0.20
			draw_line(nock + dn * (d.length() * t0),
				nock + dn * (d.length() * (t0 + 0.15)), line_col, 1.2)
		# Titik sasaran.
		draw_circle(_sn(aim_pt), 2.4, Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g,
			Pal.WIND_BRIGHT.b, 0.4 * ch))
		draw_line(_sn(aim_pt + Vector2(-4.0, 0.0)), _sn(aim_pt + Vector2(4.0, 0.0)),
			Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.35 * ch), 1.0)


## Shackle Shot: sulur dari nock ke target (terikat, berdenyut).
func _draw_tether(p: SylaraPose, j: Dictionary) -> void:
	if not p.tether_on or p.tether_alpha < 0.02:
		return
	var nock: Vector2 = j["bow_nock"] as Vector2
	var end: Vector2 = p.tether_local
	var a: float = p.tether_alpha * p.alpha
	if a <= 0.01:
		return
	var d: Vector2 = end - nock
	if d.length() < 8.0:
		return
	# Kurva sulur (quadratic bezier dengan sag).
	var mid: Vector2 = nock + d * 0.5
	var perp: Vector2 = d.normalized().orthogonal()
	mid += perp * (4.0 + 3.0 * sin(phase * 3.0))
	var col_vine := Color(Pal.VINE.r, Pal.VINE.g, Pal.VINE.b, 0.9 * a)
	var col_vine_l := Color(Pal.VINE_LIGHT.r, Pal.VINE_LIGHT.g, Pal.VINE_LIGHT.b, 0.8 * a)
	var prev: Vector2 = nock
	for i in range(1, 6):
		var t := float(i) / 5.0
		var q1: Vector2 = (1.0 - t) * (1.0 - t) * nock \
			+ 2.0 * (1.0 - t) * t * mid + t * t * end
		draw_line(_sn(prev), _sn(q1), col_vine, 2.2 * a + 0.4)
		draw_line(_sn(prev), _sn(q1), col_vine_l, 0.9 * a)
		prev = q1
	# Node daun di sepanjang sulur.
	for t in [0.32, 0.62]:
		var q: Vector2 = (1.0 - t) * (1.0 - t) * nock \
			+ 2.0 * (1.0 - t) * t * mid + t * t * end
		draw_circle(_sn(q + perp * 2.0), 1.6, Color(Pal.LEAF.r, Pal.LEAF.g, Pal.LEAF.b, 0.85 * a))
		draw_circle(_sn(q - perp * 2.0), 1.3, Color(Pal.LEAF_GOLD.r, Pal.LEAF_GOLD.g, Pal.LEAF_GOLD.b, 0.7 * a))
	# Cincin akar berdenyut di target.
	var pulse: float = 1.0 + 0.18 * sin(phase * 6.0)
	draw_arc(_sn(end), 7.0 * pulse, 0.0, TAU, 16, col_vine_l, 1.6)
	draw_circle(_sn(end), 2.0, Color(Pal.VINE_LIGHT.r, Pal.VINE_LIGHT.g, Pal.VINE_LIGHT.b, 0.5 * a))


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
	var wisp_col := Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b,
		0.55 * glow * p.alpha)
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
			Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b,
			0.75 * p.bow_draw * p.alpha))


func _draw_hurt_flash(p: SylaraPose, j: Dictionary) -> void:
	var a: float = 0.38 * p.hurt_tint * p.alpha
	var col := Color(Pal.HURT_TINT.r, Pal.HURT_TINT.g, Pal.HURT_TINT.b, a)
	draw_circle(_sn(j["head_c"] as Vector2), 6.5, col)
	draw_circle(_sn((j["chest"] as Vector2) + Vector2(0.0, -1.0)), 8.5, col)
	draw_circle(_sn(j["hip"] as Vector2), 7.5, col)
