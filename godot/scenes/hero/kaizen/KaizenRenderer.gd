# KaizenRenderer.gd — renderer prosedural berlapis Kaizen (v4 rebuild).
#
# Satu-satunya tugas: menggambar KaizenSkeleton dari KaizenPose lewat
# _draw(). Tidak ada logika gameplay di sini.
#
# Lapisan gambar (sesuai standar proyek):
#   SHADOW (tanah) → BACK (ponytail, scarf, saya, lengan/kaki belakang)
#   → BODY (hakama, torso, kepala) → ARMOR (obi, pelat dada, pauldron)
#   → WEAPON (lengan depan + katana) → DETAIL (mata, bekas luka, trim)
#   → HIGHLIGHT (rim light) → MAGIC (aksen angin, hanya saat glow > 0)
#
# Gaya: pixel-art fantasy — outline tinta 1px, warna flat terkontrol dari
# KaizenPalette, semua titik di-snap ke piksel bulat supaya tajam saat
# kamera zoom. Geometri = FK sederhana dari pose (bukan node per-bagian),
# jadi biaya per-frame hanya satu CanvasItem + puluhan draw call kecil:
# aman untuk Android.
class_name KaizenRenderer
extends Node2D

const HALF_PI := PI * 0.5
const Pal = preload("res://scenes/hero/kaizen/KaizenPalette.gd")

# ── Metrik tubuh (pixel lokal; anchor = tanah di antara dua kaki) ──
const HIP_Y := -27.0
const SPINE_LEN := 13.0
const CHEST_LEN := 9.0
const HEAD_R := 6.5
const LEG_UPPER := 12.0
const LEG_LOWER := 11.0
const FOOT_LEN := 7.0
const ARM_UPPER := 10.0
const ARM_LOWER := 9.0
const BLADE_LEN := 34.0
const GRIP_LEN := 8.0
const SCARF_SEGS: Array = [7.0, 7.0, 8.0]
const SCARF_W: Array = [4.6, 3.6, 2.6]
const PONY_SEGS: Array = [8.0, 7.0, 7.0]
const PONY_W: Array = [4.4, 3.2, 2.0]
const BAND_SEGS: Array = [6.0, 5.0]

## Pose aktif (di-set root tiap frame sebelum queue_redraw).
var pose = null
## Fase global (untuk hamon shimmer, glint, wisp angin).
var phase := 0.0
## Jejak bilah: titik GLOBAL, di-push root saat pose.trail aktif.
var trail_pts: Array = []


func _draw() -> void:
	if pose == null:
		return
	var p = pose
	if p.alpha <= 0.02:
		return
	var j := _solve(p)
	_draw_shadow(p, j)
	# ── BACK ──
	_draw_ponytail(p, j)
	_draw_scarf(p, j)
	_draw_saya(p, j)
	_draw_arm(p, j, true)
	_draw_calf(p, j, true)
	# ── BODY ──
	_draw_calf(p, j, false)
	_draw_hakama(p, j)
	_draw_feet(p, j)
	_draw_torso(p, j)
	# ── ARMOR ──
	_draw_obi(p, j)
	_draw_chest_plate(p, j)
	# ── Kepala + DETAIL ──
	_draw_head(p, j)
	# ── WEAPON ──
	_draw_trail(p)
	_draw_arm(p, j, false)
	_draw_katana(p, j)
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


func _solve(p: KaizenPose) -> Dictionary:
	var hip := Vector2(p.root_x, HIP_Y + p.root_y)
	var up1 := Vector2(sin(p.torso_lean), -cos(p.torso_lean))
	var chest := hip + up1 * SPINE_LEN
	var up2 := Vector2(sin(p.torso_lean + p.chest_flex),
		-cos(p.torso_lean + p.chest_flex))
	var neck := chest + up2 * CHEST_LEN
	var head_c := neck + up2 * HEAD_R
	var sh_f := chest + Vector2(4.6, -0.5)
	var sh_b := chest + Vector2(-4.6, -1.0)
	var hip_f := hip + Vector2(3.6, 2.0)
	var hip_b := hip + Vector2(-3.6, 2.4)
	var knee_f := hip_f + _down(p.leg_f_hip) * LEG_UPPER
	var ankle_f := knee_f + _down(p.leg_f_hip + p.leg_f_knee) * LEG_LOWER
	var toe_f := ankle_f + _fwd(p.leg_f_foot) * FOOT_LEN
	var knee_b := hip_b + _down(p.leg_b_hip) * LEG_UPPER
	var ankle_b := knee_b + _down(p.leg_b_hip + p.leg_b_knee) * LEG_LOWER
	var toe_b := ankle_b + _fwd(p.leg_b_foot) * FOOT_LEN
	var elb_f := sh_f + _down(p.arm_f_sh) * ARM_UPPER
	var hand_f := elb_f + _down(p.arm_f_sh + p.arm_f_el) * ARM_LOWER + p.weapon_off
	var elb_b := sh_b + _down(p.arm_b_sh) * ARM_UPPER
	var hand_b := elb_b + _down(p.arm_b_sh + p.arm_b_el) * ARM_LOWER
	var bdir := _fwd(p.weapon_angle)
	var tip := hand_f + bdir * BLADE_LEN
	var grip_end := hand_f - bdir * GRIP_LEN
	return {
		"hip": hip, "chest": chest, "neck": neck, "head": head_c,
		"up1": up1, "up2": up2,
		"sh_f": sh_f, "sh_b": sh_b,
		"knee_f": knee_f, "ankle_f": ankle_f, "toe_f": toe_f,
		"knee_b": knee_b, "ankle_b": ankle_b, "toe_b": toe_b,
		"elb_f": elb_f, "hand_f": hand_f,
		"elb_b": elb_b, "hand_b": hand_b,
		"bdir": bdir, "tip": tip, "grip_end": grip_end,
	}


## Ujung bilah (lokal) — dipakai root untuk API publik / FX.
func get_blade_tip_local() -> Vector2:
	if pose == null:
		return Vector2(0.0, -20.0)
	var j := _solve(pose)
	return j["tip"]


# ══════════════════════════════════════════════════════════
#  PRIMITIF
# ══════════════════════════════════════════════════════════

## Warna dengan alpha pose (death fade) — TIDAK menyentuh modulate supaya
## tidak memicu redraw berantai.
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


## Capsule dengan outline tinta: siluet terbaca saat zoom out.
func _capsule(a: Vector2, b: Vector2, w: float, col: Color,
		outline: bool = true) -> void:
	var pts := _capsule_pts(a, b, w)
	if outline:
		_poly(_capsule_pts(a, b, w + 2.4), Pal.INK)
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


## Limb menyempit (bahu→pergelangan).
func _taper(a: Vector2, wa: float, b: Vector2, wb: float, col: Color,
		outline: bool = true) -> void:
	if outline:
		_poly(_taper_pts(a, wa + 2.2, b, wb + 2.2), Pal.INK)
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


func _chain(origin: Vector2, angles: Array, segs: Array, widths: Array,
		cols: Array, outline_first: bool = true) -> void:
	var pos := origin
	for i in angles.size():
		var nxt := pos + _fwd(angles[i]) * float(segs[i])
		var col: Color = cols[mini(i, cols.size() - 1)]
		_taper(pos, float(widths[i]), nxt,
			float(widths[mini(i + 1, widths.size() - 1)]) * 0.82, col,
			outline_first or i == 0)
		pos = nxt


# ══════════════════════════════════════════════════════════
#  BAGIAN TUBUH
# ══════════════════════════════════════════════════════════

func _draw_shadow(p: KaizenPose, j: Dictionary) -> void:
	var rx := 15.0 + absf(p.root_x) * 0.35 + p.skirt_flare * 0.5
	var c := Vector2(p.root_x * 0.5, 1.5)
	var pts := PackedVector2Array()
	for i in 16:
		var a := float(i) * TAU / 16.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * 4.2))
	_poly(pts, Pal.SHADOW_GROUND)


func _draw_ponytail(p: KaizenPose, j: Dictionary) -> void:
	_chain(j["head"] + Vector2(-4.0, -3.0), p.pony, PONY_SEGS, PONY_W,
		[Pal.HAIR, Pal.HAIR, Pal.HAIR_LIGHT])


func _draw_scarf(p: KaizenPose, j: Dictionary) -> void:
	_chain(j["neck"] + Vector2(-3.0, 2.0), p.scarf, SCARF_SEGS, SCARF_W,
		[Pal.SCARF_DARK, Pal.SCARF, Pal.SCARF_LIGHT])


func _draw_saya(p: KaizenPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"]
	var a := hip + Vector2(-3.0, -2.0)
	var b := hip + Vector2(-20.0, 6.0)
	_capsule(a, b, 3.4, Color("#241f28"))
	# Cincin emas dekat pangkal + sageo (tali) kecil.
	var ring_pos := a.lerp(b, 0.18)
	draw_line(_sn(ring_pos + Vector2(0.0, -2.6)), _sn(ring_pos + Vector2(0.0, 2.6)),
		_c(Pal.GOLD_DARK), 1.4)
	draw_line(_sn(ring_pos + Vector2(-1.5, 1.0)), _sn(ring_pos + Vector2(-4.5, 4.5)),
		_c(Pal.SCARF_DARK), 1.2)


func _draw_arm(p: KaizenPose, j: Dictionary, is_back: bool) -> void:
	var sh: Vector2 = j["sh_b"] if is_back else j["sh_f"]
	var elb: Vector2 = j["elb_b"] if is_back else j["elb_f"]
	var hand: Vector2 = j["hand_b"] if is_back else j["hand_f"]
	var sleeve_col := Pal.CLOTH_DARK if is_back else Pal.CLOTH
	var skin_col := Pal.SKIN_SHADOW if is_back else Pal.SKIN
	# Lengan atas = lengan gi; lengan bawah kulit (lengan digulung).
	_taper(sh, 6.6 if not is_back else 6.0, elb, 5.4 if not is_back else 5.0,
		sleeve_col)
	_taper(elb, 4.8, hand, 4.0, skin_col)
	draw_circle(_sn(hand), 2.6, _c(skin_col))
	if not is_back:
		# Garis bayangan bawah lengan — depth tanpa biaya.
		draw_line(_sn(elb + Vector2(0.0, 2.0)), _sn(hand + Vector2(0.0, 1.6)),
			_c(Color(Pal.SKIN_SHADOW.r, Pal.SKIN_SHADOW.g, Pal.SKIN_SHADOW.b, 0.7)), 1.2)


func _draw_calf(p: KaizenPose, j: Dictionary, is_back: bool) -> void:
	var knee: Vector2 = j["knee_b"] if is_back else j["knee_f"]
	var ankle: Vector2 = j["ankle_b"] if is_back else j["ankle_f"]
	var col := Pal.HAKAMA_DARK if is_back else Pal.HAKAMA
	_taper(knee, 5.6, ankle, 4.4, col)
	# Kyahan (pembungkus betis) — garis kain melintang.
	var mid := knee.lerp(ankle, 0.55)
	draw_line(_sn(mid + Vector2(-2.6, 0.0)), _sn(mid + Vector2(2.6, 0.6)),
		_c(Pal.CLOTH_DARK), 1.4)


func _draw_feet(p: KaizenPose, j: Dictionary) -> void:
	# Belakang dulu, depan menimpa (tabi gelap).
	_capsule(j["ankle_b"] + Vector2(0.5, 1.0), j["toe_b"] + Vector2(0.0, 1.0),
		3.6, Color("#241f28"))
	_capsule(j["ankle_f"] + Vector2(0.5, 1.0), j["toe_f"] + Vector2(0.0, 1.0),
		3.6, Color("#332c38"))


func _draw_hakama(p: KaizenPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"]
	var knee_f: Vector2 = j["knee_f"]
	var knee_b: Vector2 = j["knee_b"]
	var skew := (knee_f.x - knee_b.x) * 0.18
	var half_w := 12.0 + p.skirt_flare
	var hem_y := -8.5
	var pts := PackedVector2Array([
		hip + Vector2(-8.0, -3.0),
		hip + Vector2(8.0, -3.0),
		Vector2(hip.x + 6.0 + half_w * 0.62 + skew, hem_y),
		Vector2(hip.x + half_w * 0.18 + skew * 0.6, hem_y + 1.5),
		Vector2(hip.x - half_w * 0.22 + skew * 0.6, hem_y + 1.0),
		Vector2(hip.x - 6.0 - half_w * 0.62 + skew, hem_y),
	])
	_poly(pts, Pal.HAKAMA)
	# Lipatan (pleat): dua garis gelap mengipas dari pinggang ke hem.
	var pleat_a := Vector2(hip.x - 3.0, hip.y - 2.0)
	var pleat_b := Vector2(hip.x - 4.0 - half_w * 0.3 + skew, hem_y + 0.5)
	draw_line(_sn(pleat_a), _sn(pleat_b), _c(Pal.HAKAMA_DARK), 1.6)
	pleat_a = Vector2(hip.x + 3.5, hip.y - 2.0)
	pleat_b = Vector2(hip.x + 4.5 + half_w * 0.3 + skew, hem_y + 0.5)
	draw_line(_sn(pleat_a), _sn(pleat_b), _c(Pal.HAKAMA_DARK), 1.6)
	# Bayangan sisi belakang rok.
	var shade := PackedVector2Array([
		hip + Vector2(-8.0, -3.0),
		hip + Vector2(-2.0, -3.0),
		Vector2(hip.x - half_w * 0.22 + skew * 0.6, hem_y + 1.0),
		Vector2(hip.x - 6.0 - half_w * 0.62 + skew, hem_y),
	])
	_poly(shade, Color(Pal.HAKAMA_DARK.r, Pal.HAKAMA_DARK.g,
		Pal.HAKAMA_DARK.b, 0.6))


func _draw_torso(p: KaizenPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"]
	var chest: Vector2 = j["chest"]
	var neck: Vector2 = j["neck"]
	# Gi bawah (pinggul → dada).
	_taper(hip, 15.0, chest, 13.0, Pal.CLOTH)
	# Dada sedikit lebih terang (terkena cahaya atas).
	_taper(chest, 13.0, neck, 9.0, Pal.CLOTH_LIGHT)
	# Bayangan sisi belakang torso.
	var up: Vector2 = j["up1"]
	var n := Vector2(-up.y, up.x)
	_poly(PackedVector2Array([
		hip - n * 7.0, chest - n * 6.0,
		chest - n * 2.0, hip - n * 2.0,
	]), Color(Pal.CLOTH_DARK.r, Pal.CLOTH_DARK.g, Pal.CLOTH_DARK.b, 0.72))
	# Kerah V putih (detail ikonik gi).
	var collar_col := Color(Pal.BAND.r, Pal.BAND.g, Pal.BAND.b, 0.9)
	draw_line(_sn(neck + Vector2(-3.5, -1.0)), _sn(chest + Vector2(0.5, 3.0)),
		_c(collar_col), 1.6)
	draw_line(_sn(neck + Vector2(3.5, -1.0)), _sn(chest + Vector2(0.5, 3.0)),
		_c(collar_col), 1.6)


func _draw_obi(p: KaizenPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"]
	_poly(PackedVector2Array([
		hip + Vector2(-9.0, -3.5), hip + Vector2(9.0, -3.5),
		hip + Vector2(8.5, 2.5), hip + Vector2(-8.5, 2.5),
	]), Pal.GOLD_DARK)
	_poly(PackedVector2Array([
		hip + Vector2(-9.0, -3.5), hip + Vector2(9.0, -3.5),
		hip + Vector2(8.8, -1.0), hip + Vector2(-8.8, -1.0),
	]), Pal.GOLD)
	# Simpul kecil di depan.
	_poly(PackedVector2Array([
		hip + Vector2(0.0, -3.0), hip + Vector2(4.0, -2.0),
		hip + Vector2(3.5, 2.0), hip + Vector2(-0.5, 1.5),
	]), Pal.GOLD)


func _draw_chest_plate(p: KaizenPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"]
	var up: Vector2 = j["up2"]
	var n := Vector2(-up.y, up.x)
	var top := chest + up * 3.5
	var bot := chest - up * 4.5
	_poly(PackedVector2Array([
		top - n * 6.5, top + n * 6.5,
		bot + n * 5.5, bot - n * 5.5,
	]), Pal.CLOTH_DARK)
	# Trim emas di tepi bawah pelat.
	draw_line(_sn(bot - n * 5.5), _sn(bot + n * 5.5), _c(Pal.GOLD), 1.4)
	# Pauldron kecil di bahu depan.
	var sh: Vector2 = j["sh_f"]
	_capsule(sh + Vector2(-1.5, -1.5), sh + Vector2(2.5, 2.5), 6.4,
		Pal.CLOTH_DARK)
	draw_line(_sn(sh + Vector2(-3.0, 2.0)), _sn(sh + Vector2(4.0, 4.0)),
		_c(Pal.GOLD_DARK), 1.2)


func _draw_head(p: KaizenPose, j: Dictionary) -> void:
	var hc: Vector2 = j["head"]
	var up: Vector2 = j["up2"]
	# Kepala (kulit) — hexagon dengan rahang menyempit.
	var head_pts := PackedVector2Array([
		hc + Vector2(-5.5, -4.0), hc + Vector2(5.5, -4.0),
		hc + Vector2(6.0, 1.0), hc + Vector2(3.2, 5.5),
		hc + Vector2(-3.2, 5.5), hc + Vector2(-6.0, 1.0),
	])
	# Outline tinta di sekeliling kepala (siluet kuat saat zoom out).
	var outlined := PackedVector2Array()
	for v in head_pts:
		outlined.append(v + (v - hc).normalized() * 1.2)
	_poly(outlined, Pal.INK)
	_poly(head_pts, Pal.SKIN)
	# Bayangan sisi belakang kepala.
	_poly(PackedVector2Array([
		hc + Vector2(-5.5, -4.0), hc + Vector2(-2.0, -4.0),
		hc + Vector2(-2.4, 5.2), hc + Vector2(-3.2, 5.5), hc + Vector2(-6.0, 1.0),
	]), Color(Pal.SKIN_SHADOW.r, Pal.SKIN_SHADOW.g, Pal.SKIN_SHADOW.b, 0.6))
	# Rambut: spike di atas + samping.
	var hair_pts := PackedVector2Array([
		hc + Vector2(-6.6, -2.6), hc + Vector2(-4.6, -8.4),
		hc + Vector2(-1.6, -6.2), hc + Vector2(1.2, -9.2),
		hc + Vector2(3.8, -6.6), hc + Vector2(6.4, -3.2),
		hc + Vector2(6.0, -1.2), hc + Vector2(-6.2, -1.2),
	])
	_poly(hair_pts, Pal.HAIR)
	# Helai highlight.
	draw_line(_sn(hc + Vector2(-3.4, -7.0)), _sn(hc + Vector2(-1.0, -3.4)),
		_c(Color(Pal.HAIR_LIGHT.r, Pal.HAIR_LIGHT.g, Pal.HAIR_LIGHT.b, 0.8)), 1.2)
	# Hachimaki: pita dahi + dua ekor berkibar (secondary motion).
	_poly(PackedVector2Array([
		hc + Vector2(-6.2, -4.4), hc + Vector2(6.2, -4.4),
		hc + Vector2(6.2, -2.6), hc + Vector2(-6.2, -2.6),
	]), Pal.BAND)
	draw_line(_sn(hc + Vector2(-6.2, -2.6)), _sn(hc + Vector2(6.2, -2.6)),
		_c(Pal.BAND_SHADOW), 1.0)
	var knot := hc + Vector2(-5.8, -3.4)
	var pos := knot
	for i in 2:
		var nxt := pos + _fwd(p.band[i]) * float(BAND_SEGS[i])
		_taper(pos, 1.8, nxt, 1.0, Pal.BAND_SHADOW if i == 1 else Pal.BAND, false)
		pos = nxt
	# Mata: amber tajam (satu jelas + satu sugestif untuk 3/4 view).
	var open := 1.0 - clampf(p.eye_blink, 0.0, 1.0)
	var eye_h := maxf(0.4, 1.8 * open)
	draw_rect(Rect2(_sn(hc + Vector2(1.6, -0.6 - eye_h * 0.5)),
		Vector2(2.6, eye_h)), _c(Pal.EYE))
	if open > 0.5:
		draw_rect(Rect2(_sn(hc + Vector2(4.2, -0.9)), Vector2(0.9, 0.9)),
			_c(Color(Pal.INK.r, Pal.INK.g, Pal.INK.b, 0.9)))
	else:
		draw_line(_sn(hc + Vector2(1.4, -0.4)), _sn(hc + Vector2(4.4, -0.2)),
			_c(Pal.INK), 1.0)
	draw_rect(Rect2(_sn(hc + Vector2(-2.2, -0.5 - eye_h * 0.3)),
		Vector2(1.8, eye_h * 0.7)),
		_c(Color(Pal.EYE.r, Pal.EYE.g, Pal.EYE.b, 0.45)))
	# Alis tegas.
	draw_line(_sn(hc + Vector2(1.2, -2.2)), _sn(hc + Vector2(4.6, -1.8)),
		_c(Pal.INK), 1.2)
	# Bekas luka di pipi — identitas Kaizen.
	draw_line(_sn(hc + Vector2(3.0, 1.2)), _sn(hc + Vector2(4.4, 3.8)),
		_c(Color(0.62, 0.38, 0.32, 0.95)), 1.0)


func _draw_trail(p: KaizenPose) -> void:
	# Jejak bilah saat tebasan: pita dua-nada (angin luar + inti terang).
	if trail_pts.size() < 3:
		return
	var n := trail_pts.size()
	var local_pts := PackedVector2Array()
	for gp in trail_pts:
		local_pts.append(to_local(gp))
	var fade := 1.0 if p.trail else 0.45
	# Luar (wind).
	for i in range(n - 1):
		var t0 := float(i) / float(n - 1)
		var t1 := float(i + 1) / float(n - 1)
		var a: Vector2 = local_pts[i]
		var b: Vector2 = local_pts[i + 1]
		var d := b - a
		if d.length() < 0.001:
			continue
		var perp := Vector2(-d.y, d.x).normalized()
		var w0 := 1.0 + 7.0 * t0
		var w1 := 1.0 + 7.0 * t1
		_poly(PackedVector2Array([
			a + perp * w0, b + perp * w1, b - perp * w1 * 0.4, a - perp * w0 * 0.4,
		]), Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, 0.30 * fade * t1))
		_poly(PackedVector2Array([
			a + perp * w0 * 0.4, b + perp * w1 * 0.4,
			b - perp * w1 * 0.25, a - perp * w0 * 0.25,
		]), Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b,
			0.42 * fade * t1))


func _draw_katana(p: KaizenPose, j: Dictionary) -> void:
	var hand: Vector2 = j["hand_f"]
	var bdir: Vector2 = j["bdir"]
	var tip: Vector2 = j["tip"]
	var grip_end: Vector2 = j["grip_end"]
	var perp := Vector2(-bdir.y, bdir.x)
	# Tsuka (gagang) — bungkus gelap + lilitan emas.
	_capsule(hand, grip_end, 3.0, Pal.HAIR)
	for k in [0.25, 0.5, 0.75]:
		var wp := hand.lerp(grip_end, k)
		draw_line(_sn(wp - perp * 1.6), _sn(wp + perp * 1.6),
			_c(Pal.GOLD_DARK), 1.0)
	# Tsuba (guard) emas.
	var tsuba_c := hand - bdir * 1.2
	_poly(PackedVector2Array([
		tsuba_c - perp * 4.2 - bdir * 1.0, tsuba_c + perp * 4.2 - bdir * 1.0,
		tsuba_c + perp * 3.6 + bdir * 1.2, tsuba_c - perp * 3.6 + bdir * 1.2,
	]), Pal.GOLD_DARK)
	draw_line(_sn(tsuba_c - perp * 4.0), _sn(tsuba_c + perp * 4.0),
		_c(Pal.GOLD), 1.2)
	# Bilah: punggung gelap + muka baja + sisi tajam terang.
	var b_start := hand + bdir * 1.6
	_capsule(b_start, tip, 3.2, Pal.STEEL)
	var edge_a := b_start - perp * 1.2
	var edge_b := tip - perp * 1.0
	draw_line(_sn(edge_a), _sn(edge_b), _c(Pal.STEEL_LIGHT), 1.5)
	# Hamon: garis temper bergelombang (identitas bilah Kaizen).
	var hamon_pts := PackedVector2Array()
	for i in 9:
		var t := float(i) / 8.0
		var pos := b_start.lerp(tip, 0.06 + t * 0.9)
		var wob := sin(t * 22.0 - phase * 5.0) * 0.9
		hamon_pts.append(pos + perp * (0.2 - wob * 0.5))
	for i in range(hamon_pts.size() - 1):
		draw_line(_sn(hamon_pts[i]), _sn(hamon_pts[i + 1]),
			_c(Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b,
				0.55)), 0.8)
	# Kissaki (ujung) — titik cahaya.
	draw_line(_sn(tip - bdir * 3.0), _sn(tip), _c(Pal.STEEL_SHINE), 1.6)
	# Glint berjalan saat bilah aktif.
	if p.trail or p.wind_glow > 0.5:
		var gt := fmod(phase * 0.9, 1.0)
		var gp := b_start.lerp(tip, 0.1 + gt * 0.8)
		draw_line(_sn(gp - perp * 2.2), _sn(gp + perp * 2.2),
			_c(Color(1.0, 1.0, 1.0, 0.75)), 1.2)


func _draw_rim(p: KaizenPose, j: Dictionary) -> void:
	# Rim light dingin dari atas-kiri: 3 goresan tipis, biaya minimal.
	var chest: Vector2 = j["chest"]
	var head: Vector2 = j["head"]
	var up: Vector2 = j["up2"]
	var n := Vector2(-up.y, up.x)
	var rim := Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b, 0.4)
	draw_line(_sn(chest + up * 2.0 + n * 5.6),
		_sn(chest - up * 5.0 + n * 6.0), _c(rim), 1.2)
	draw_line(_sn(head + Vector2(-5.0, -5.0)), _sn(head + Vector2(-1.0, -8.6)),
		_c(rim), 1.2)
	var hip: Vector2 = j["hip"]
	draw_line(_sn(hip + Vector2(7.5, -2.0)), _sn(hip + Vector2(8.5, -6.0)),
		_c(Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b, 0.25)), 1.0)


func _draw_wind_wisps(p: KaizenPose, j: Dictionary) -> void:
	if p.wind_glow <= 0.02:
		return
	# Tiga lidah angin kecil berputar di sekitar dada/bilah — AKSEN saja.
	var center: Vector2 = j["chest"] + Vector2(4.0, -2.0)
	for i in 3:
		var a := phase * 2.2 + float(i) * TAU / 3.0
		var pos := center + Vector2(cos(a), sin(a) * 0.6) * 15.0
		var dir := Vector2(cos(a + HALF_PI), sin(a + HALF_PI) * 0.6)
		var s := 3.0 + sin(phase * 3.0 + float(i) * 2.0) * 1.0
		var alpha := 0.5 * p.wind_glow * (0.6 + 0.4 * sin(phase * 4.0 + float(i)))
		_poly(PackedVector2Array([
			pos - dir * s * 1.8,
			pos + Vector2(-dir.y, dir.x) * s * 0.55,
			pos + dir * s * 1.2,
			pos - Vector2(-dir.y, dir.x) * s * 0.55,
		]), Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, alpha))
