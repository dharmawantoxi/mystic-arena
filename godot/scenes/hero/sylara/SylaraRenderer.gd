# SylaraRenderer.gd — renderer prosedural berlapis Sylara (v2 rebuild).
#
# Satu-satunya tugas: menggambar karakter Sylara dari SylaraPose lewat _draw().
# SATU CanvasItem per karakter — ringan untuk Android (tanpa node tambahan,
# tanpa shader partikel; semua bentuk = polygon/arc/line CPU).
#
# Disiplin visual (sumber: masterwork pygame v2, di-bake ke assets/units/
# sylara.png — kualitas benchmark internal, bukan aset yang disalin):
#   * Ramp 4–5 nilai per material dengan hue-shift (bayangan dingin,
#     highlight hangat) — tidak ada potongan yang warna-datar.
#   * Selout tinta 1 px pada tepi luar — siluet terbaca saat zoom out.
#   * Siluet bergerigi deterministik (tuft cape, rambut) — aman cache.
#   * Specular sebagai cluster 1–2 px (glint busur/emas) yang berputar.
#   * Key light kiri-atas konsisten (LIGHT_DIR = (-1,-1)).
#
# Urutan gambar (setiap lapis punya tujuan visual):
#   1.  GROUND      — bayangan kontak + platform angin (identitas)
#   2.  CAPE        — jubah angin 3 segmen + hem ber-tuft (secondary motion)
#   3.  HAIR BACK   — massa rambut oranye + untaian belakang
#   4.  QUIVER      — strap + quiver kulit + 3 anak panah (aksen identitas)
#   5.  LIMBS BACK  — lengan belakang + kaki belakang (ramp bayangan)
#   6.  LIMBS FRONT — kaki depan + sepatu boots + tunic
#   7.  TORSO       — dada, vest kulit (strap + dither), pauldron, belt
#   8.  HOOD        — tudung runcing + cowl (bayangan dalam)
#   9.  HEAD        — wajah, fringe, mata emerald + blink, alis, bibir
#   10. TRAIL       — jejak sapuan busur (wind, 3 lapis)
#   11. ARM FRONT   — lengan depan + bracer kulit
#   12. BOW         — busur recurve detail + tali + anak panah angin
#   13. RIM/GLOW    — rim light, glint, wisps angin, charge nock
#   14. FEEDBACK    — debu kontak + hurt flash (demo)
class_name SylaraRenderer
extends Node2D

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

# ── Metrik tubuh (pixel lokal; anchor = tanah di antara dua kaki) ──
# Dipakai Animator (solver kaki) & SkillFX lewat konstanta yang sama.
const HIP_Y := -27.0
const SPINE_LEN := 12.0
const CHEST_LEN := 8.5
const HEAD_R := 6.5
const LEG_UPPER := 11.5
const LEG_LOWER := 10.5
const FOOT_LEN := 6.5
const ARM_UPPER := 9.0
const ARM_LOWER := 8.5
const BOW_LEN := 23.0        # panjang busur recurve (grip ke tip)
const BOW_DRAW_PX := 11.0    # tarikan tali maksimum (px)
const CAPE_SEGS: Array[float] = [8.0, 8.0, 9.0]
const CAPE_W: Array[float] = [5.6, 4.8, 3.4]
const HOOD_SEGS: Array[float] = [5.0, 4.5]
const HAIR_SEGS: Array[float] = [7.0, 6.0, 6.0]
const HAIR_W: Array[float] = [4.2, 3.2, 2.0]

## Pose aktif (di-set root tiap frame sebelum queue_redraw).
var pose: SylaraPose = null
## Fase global (shimmer, glint, wisp, platform).
var phase := 0.0
## Jejak trail busur: titik LOKAL renderer, di-push root saat pose.trail.
var trail_pts: PackedVector2Array = PackedVector2Array()

## Cache geometri busur (ruang lokal) — dipakai SkillFX / Skeleton untuk
## anchor nock/tip/grip di posisi GLOBAL (lewat to_global()).
var _bow_grip := Vector2.ZERO
var _bow_tip := Vector2.ZERO
var _bow_tip_lo := Vector2.ZERO
var _bow_nock := Vector2.ZERO
var _bow_dir := Vector2.RIGHT
var _bow_perp := Vector2.DOWN

## Buffer polygon reusable — ZERO alokasi per-frame (Android).
const _BUF_COUNT := 12
var _bufs: Array[PackedVector2Array] = []
var _buf_i := 0


func _ready() -> void:
	for i in _BUF_COUNT:
		_bufs.append(PackedVector2Array())


## Buffer polygon pool: resize+reuse, aman dipakai berurutan dalam satu
## _draw (immediate mode — titik dikonsumsi saat draw_* dipanggil).
func _pbuf(n: int) -> PackedVector2Array:
	_buf_i = (_buf_i + 1) % _BUF_COUNT
	var b := _bufs[_buf_i]
	b.resize(n)
	return b


func get_bow_grip() -> Vector2:
	return _bow_grip


func get_bow_tip() -> Vector2:
	return _bow_tip


func get_bow_tip_lo() -> Vector2:
	return _bow_tip_lo


func get_bow_nock() -> Vector2:
	return _bow_nock


func get_bow_dir() -> Vector2:
	return _bow_dir


func _c(col: Color) -> Color:
	if pose == null:
		return col
	return Color(col.r, col.g, col.b, col.a * pose.alpha)


## Hash deterministik 0..1 (tanpa RNG — aman untuk cache & replikasi).
static func _hash01(i: int, seed: int) -> float:
	var n := i * 374761393 + seed * 668265263
	n = (n ^ (n >> 13)) * 1274126177
	n = n ^ (n >> 16)
	return float(n & 0x7fffffff) / float(0x7fffffff)


## Pulse glint: satu kilau pendek tiap ~1.2 s, fase berbeda per seed.
static func _glint(t: float, seed: float) -> float:
	var cyc := fmod(t * 0.83 + seed, 1.0)
	if cyc < 0.10:
		return sin(cyc / 0.10 * PI)
	return 0.0


# ══════════════════════════════════════════════════════════
#  DRAW — pipeline berlapis
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	if pose == null or _bufs.is_empty():
		return
	var p: SylaraPose = pose
	if p.alpha <= 0.02:
		return
	var j: Dictionary = _solve(p)

	# 1. GROUND (bayangan kontak + platform angin)
	_draw_ground(p, j)

	# 2. CAPE (belakang, secondary motion)
	_draw_cape(p, j)

	# 3. HAIR BACK (massa rambut oranye — identitas)
	_draw_hair_back(p, j)

	# 4. QUIVER
	_draw_quiver(p, j)

	# 5. LIMBS BACK
	_draw_arm(p, j, true)
	_draw_leg(p, j, true)

	# 6. LIMBS FRONT + TUNIC
	_draw_leg(p, j, false)
	_draw_feet(p, j)
	_draw_tunic(p, j)

	# 7. TORSO + ARMOR
	_draw_torso(p, j)
	_draw_vest(p, j)
	_draw_belt(p, j)

	# 8. HOOD
	_draw_hood(p, j)

	# 9. HEAD & WAJAH
	_draw_head(p, j)

	# 10. TRAIL (di bawah senjata)
	_draw_trail(p)

	# 11. ARM FRONT
	_draw_arm(p, j, false)

	# 12. BOW
	_draw_bow(p, j)

	# 13. RIM / GLINT / WISPS
	_draw_rim(p, j)
	_draw_wisps(p, j)

	# 14. FEEDBACK
	_draw_dust(p, j)
	if p.hurt_tint > 0.01:
		_draw_hurt_flash(p, j)


# ══════════════════════════════════════════════════════════
#  FK — satu sumber kebenaran posisi sendi
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
	var hand_f: Vector2 = elb_f + _down(p.arm_f_sh + p.arm_f_el) * ARM_LOWER
	var elb_b: Vector2 = sh_b + _down(p.arm_b_sh) * ARM_UPPER
	var hand_b: Vector2 = elb_b + _down(p.arm_b_sh + p.arm_b_el) * ARM_LOWER

	# ── Busur: orientasi dari bow_angle; nock tertarik MENDARAT (-bow_dir) ──
	var bow_dir: Vector2 = _fwd(p.bow_angle)
	var bow_perp: Vector2 = Vector2(-bow_dir.y, bow_dir.x)
	# Getar charge R: busur + tali bergetar halus saat charge penuh.
	var jitter := 0.0
	if p.charge > 0.01:
		jitter = sin(phase * 62.0) * 0.9 * p.charge
	var grip: Vector2 = hand_f + p.bow_off + bow_perp * jitter

	_bow_dir = bow_dir
	_bow_perp = bow_perp
	_bow_grip = grip
	_bow_tip = grip + bow_dir * BOW_LEN
	_bow_tip_lo = grip - bow_dir * BOW_LEN
	var draw_px: float = p.bow_draw * BOW_DRAW_PX
	var nock: Vector2 = grip - bow_dir * (3.5 + draw_px)
	if p.shiver > 0.01:
		# Tali kempis pasca-release: simpangan sinus kecil di tengah tali.
		nock += bow_perp * (sin(phase * 95.0) * 1.4 * p.shiver)
	_bow_nock = nock

	return {
		"hip": hip, "chest": chest, "neck": neck, "head_c": head_c,
		"up2": up2,
		"sh_f": sh_f, "sh_b": sh_b, "hip_f": hip_f, "hip_b": hip_b,
		"knee_f": knee_f, "knee_b": knee_b,
		"ankle_f": ankle_f, "ankle_b": ankle_b,
		"toe_f": toe_f, "toe_b": toe_b,
		"elb_f": elb_f, "elb_b": elb_b,
		"hand_f": hand_f, "hand_b": hand_b,
		"bow_grip": grip, "bow_tip": _bow_tip, "bow_tip_lo": _bow_tip_lo,
		"bow_nock": nock, "bow_dir": bow_dir, "bow_perp": bow_perp,
	}


# ══════════════════════════════════════════════════════════
#  1. GROUND — bayangan kontak + platform angin
# ══════════════════════════════════════════════════════════

func _draw_ground(p: SylaraPose, _j: Dictionary) -> void:
	var c: Vector2 = Vector2(p.root_x * 0.4, 0.0)

	# Bayangan kontak (ellipse 10 titik — melebar saat tubuh rendah).
	var squish := 1.0 - clampf(-p.root_y, 0.0, 6.0) * 0.03
	var b: PackedVector2Array = _pbuf(10)
	for i in 10:
		var a: float = float(i) / 10.0 * TAU
		var rx: float = 15.0 * (1.0 + 0.10 * squish)
		var ry: float = 5.2
		b[i] = c + Vector2(cos(a) * rx, sin(a) * ry - 0.5)
	draw_colored_polygon(b, _c(Pal.SHADOW_GROUND))

	# Platform angin — identitas Sylara (ada di bake pygame). Cincin tipis
	# berputar + 3 titik daun; alpha rendah supaya tidak mengganggu.
	var t := phase * 1.5
	var n := 16
	var arc1 := _pbuf(n)
	var arc2 := _pbuf(n)
	for i in n:
		var a1: float = t + float(i) / float(n) * 4.6
		var a2: float = -t * 1.3 + 2.2 + float(i) / float(n) * 3.8
		arc1[i] = c + Vector2(cos(a1) * 13.5, sin(a1) * 13.5 * 0.30)
		arc2[i] = c + Vector2(cos(a2) * 10.0, sin(a2) * 10.0 * 0.30)
	draw_polyline(arc1, _c(Color(Pal.WIND_DARK.r, Pal.WIND_DARK.g,
		Pal.WIND_DARK.b, 0.34)), 1.2, true)
	draw_polyline(arc2, _c(Color(Pal.WIND.r, Pal.WIND.g,
		Pal.WIND.b, 0.30)), 1.0, true)
	for i in 3:
		var a: float = t * 0.8 + float(i) * TAU / 3.0
		var pos: Vector2 = c + Vector2(cos(a) * 11.5, sin(a) * 11.5 * 0.30)
		draw_circle(pos, 1.1, _c(Color(Pal.LEAF_GOLD.r, Pal.LEAF_GOLD.g,
		Pal.LEAF_GOLD.b, 0.38)))


# ══════════════════════════════════════════════════════════
#  2. CAPE — jubah angin (secondary motion + hem ber-tuft)
# ══════════════════════════════════════════════════════════

func _draw_cape(p: SylaraPose, j: Dictionary) -> void:
	var anchor: Vector2 = (j["chest"] as Vector2) + Vector2(-3.5, -2.5)
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(CAPE_SEGS[i])
		var seg_w: float = float(CAPE_W[i]) + p.cape_flare * (0.4 + float(i) * 0.3)
		var ang: float = float(p.cape[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len

		var poly := _pbuf(4)
		poly[0] = prev + perp * seg_w * 0.5
		poly[1] = next + perp * (seg_w * 0.5 + 1.2)
		poly[2] = next - perp * (seg_w * 0.5 + 1.2)
		poly[3] = prev - perp * seg_w * 0.5
		var col: Color
		match i:
			0:
				col = Pal.CAPE_DARK
			1:
				col = Pal.CAPE
			_:
				col = Pal.CAPE_LIGHT
		draw_colored_polygon(poly, _c(col))
		# Selout tepi luar + shading dalam (ramp)
		draw_line(poly[0], poly[1], _c(Pal.INK), 1.0)
		draw_line(poly[2], poly[3], _c(Pal.INK), 1.0)
		draw_line(poly[0] + d * 1.0, poly[1] + d * 1.0, _c(Pal.CAPE_DARKEST), 1.0)
		if i < 2:
			# Sisi dalam lebih terang (terlipat menghadap key light)
			draw_line(poly[3] - perp * 0.4, poly[2] - perp * 0.4,
				_c(Pal.CAPE_LIGHT), 0.8)
		if i == 2:
			# Hem ber-tuft (siluet bergerigi deterministik)
			for k in 4:
				var h := _hash01(k, 7)
				var s: float = lerpf(-1.0, 1.0, float(k) / 3.0)
				var base_pt: Vector2 = next + perp * s * (seg_w * 0.5 + 1.0)
				var tip_pt: Vector2 = base_pt + d * (2.0 + h * 2.6) \
					+ perp * s * 1.4
				var tuft := _pbuf(3)
				tuft[0] = base_pt - perp * 1.0
				tuft[1] = tip_pt
				tuft[2] = base_pt + perp * 1.0
				draw_colored_polygon(tuft, _c(Pal.CAPE_LIGHT if k % 2 == 0
					else Pal.CAPE))
				draw_line(tuft[0], tuft[1], _c(Pal.INK), 0.7)
				# Rim angin di ujung tuft (aksen)
				if p.wind_glow > 0.15:
					draw_circle(tip_pt, 0.8, _c(Color(Pal.WIND_LIGHT.r,
						Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.4 * p.wind_glow)))
		prev = next


# ══════════════════════════════════════════════════════════
#  3. HAIR BACK — massa rambut oranye (identitas utama)
# ══════════════════════════════════════════════════════════

func _draw_hair_back(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var anchor: Vector2 = head_c + Vector2(-2.5, -1.0)

	# Massa rambut belakang kepala (blob 8 titik, deterministik)
	var blob := _pbuf(8)
	for i in 8:
		var a: float = float(i) / 8.0 * TAU
		var r: float = 4.4 + _hash01(i, 11) * 1.2
		blob[i] = anchor + Vector2(cos(a) * r * 0.9, sin(a) * r)
	draw_colored_polygon(blob, _c(Pal.HAIR_DARK))
	draw_polyline(blob, _c(Pal.INK), 1.0, true)

	# Untaian berkibar (3 segmen) — secondary motion
	var prev: Vector2 = anchor
	for i in 3:
		var seg_len: float = float(HAIR_SEGS[i])
		var seg_w: float = float(HAIR_W[i])
		var ang: float = float(p.hair[i])
		var d: Vector2 = Vector2(cos(ang), sin(ang))
		var perp: Vector2 = Vector2(-d.y, d.x)
		var next: Vector2 = prev + d * seg_len
		var poly := _pbuf(4)
		poly[0] = prev + perp * seg_w * 0.5
		poly[1] = next + perp * seg_w * 0.35
		poly[2] = next - perp * seg_w * 0.35
		poly[3] = prev - perp * seg_w * 0.5
		var col: Color = Pal.HAIR if i < 2 else Pal.HAIR_LIGHT
		draw_colored_polygon(poly, _c(col))
		draw_line(poly[0], poly[1], _c(Pal.INK), 0.8)
		# Highlight searah helai
		draw_line(prev - perp * seg_w * 0.15, next - perp * seg_w * 0.1,
			_c(Pal.HAIR_SHINE), 0.7)
		# Flicker kilai rambut (1–2 px, berputar)
		var g := _glint(phase, 0.7)
		if g > 0.01 and i == 1:
			var gp: Vector2 = prev.lerp(next, _hash01(3, 5))
			draw_circle(gp, 1.0 * g, _c(Color(Pal.HAIR_HIGH.r,
				Pal.HAIR_HIGH.g, Pal.HAIR_HIGH.b, 0.9 * g)))
		prev = next


# ══════════════════════════════════════════════════════════
#  4. QUIVER — strap bahu + quiver kulit + 3 anak panah
# ══════════════════════════════════════════════════════════

func _draw_quiver(p: SylaraPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var hip_b: Vector2 = j["hip_b"] as Vector2

	# Strap diagonal (bahu depan -> pinggul belakang)
	draw_line(chest + Vector2(2.5, 0.5), hip_b + Vector2(-1.0, 1.5),
		_c(Pal.LEATHER_DARK), 2.2)
	draw_line(chest + Vector2(2.5, 0.5), hip_b + Vector2(-1.0, 1.5),
		_c(Pal.LEATHER), 1.2)

	var base: Vector2 = chest + Vector2(-5.5, 1.5)
	var q_poly := _pbuf(4)
	q_poly[0] = base + Vector2(-3.5, -9.0)
	q_poly[1] = base + Vector2(3.5, -9.0)
	q_poly[2] = base + Vector2(4.5, 6.0)
	q_poly[3] = base + Vector2(-2.5, 6.0)
	draw_colored_polygon(q_poly, _c(Pal.QUIVER))
	draw_polyline(q_poly, _c(Pal.INK), 1.0, true)
	# Mulut quiver (rim gelap) + highlight sisi depan
	draw_line(base + Vector2(-3.5, -9.0), base + Vector2(3.5, -9.0),
		_c(Pal.QUIVER_DARK), 2.0)
	draw_line(base + Vector2(3.8, -8.0), base + Vector2(4.6, 5.0),
		_c(Pal.QUIVER_LIGHT), 0.9)
	# Gold band
	draw_line(base + Vector2(-3.0, -4.0), base + Vector2(3.8, -4.0),
		_c(Pal.GOLD), 1.2)

	# 3 anak panah (tinggi bervariasi deterministik)
	for i in 3:
		var h := _hash01(i, 21)
		var ax: float = base.x - 2.2 + float(i) * 2.4
		var top: float = -9.5 - h * 2.5
		var ay: float = base.y + top
		draw_line(Vector2(ax, ay), Vector2(ax, ay - 4.0), _c(Pal.SHAFT), 1.2)
		# Fletching emerald
		draw_line(Vector2(ax - 1.1, ay - 1.8), Vector2(ax - 2.2, ay - 3.6),
			_c(Pal.FEATHER), 1.0)
		draw_line(Vector2(ax + 1.1, ay - 1.8), Vector2(ax + 2.2, ay - 3.6),
			_c(Pal.FEATHER_DARK), 1.0)
		# Mata panah perak
		draw_line(Vector2(ax - 1.2, ay - 3.4), Vector2(ax, ay - 6.2),
			_c(Pal.HEAD), 1.0)
		draw_line(Vector2(ax + 1.2, ay - 3.4), Vector2(ax, ay - 6.2),
			_c(Pal.HEAD_DARK), 0.8)


# ══════════════════════════════════════════════════════════
#  5 & 11. LIMBS — lengan & kaki (ramp 3 nilai + selout)
# ══════════════════════════════════════════════════════════

func _draw_arm(_p: SylaraPose, j: Dictionary, back: bool) -> void:
	var sh: Vector2 = (j["sh_b"] if back else j["sh_f"]) as Vector2
	var elb: Vector2 = (j["elb_b"] if back else j["elb_f"]) as Vector2
	var hand: Vector2 = (j["hand_b"] if back else j["hand_f"]) as Vector2
	var w: float = 3.4 if back else 3.8

	# Lengan atas (lengan baju tunic)
	_draw_limb(sh, elb, w,
		Pal.CLOTH_DARK if back else Pal.CLOTH,
		Pal.CLOTH_DARKEST, Pal.CLOTH_LIGHT)
	# Lengan bawah (kulit)
	_draw_limb(elb, hand, w * 0.86,
		Pal.SKIN_DARK if back else Pal.SKIN,
		Pal.SKIN_SHADE, Pal.SKIN_LIGHT)
	if not back:
		# Bracer kulit + gesper emas
		var a1: Vector2 = elb + (hand - elb) * 0.25
		var a2: Vector2 = elb + (hand - elb) * 0.75
		var d: Vector2 = (a2 - a1).normalized()
		var perp: Vector2 = Vector2(-d.y, d.x)
		var br := _pbuf(4)
		br[0] = a1 + perp * w * 0.52
		br[1] = a2 + perp * w * 0.48
		br[2] = a2 - perp * w * 0.48
		br[3] = a1 - perp * w * 0.52
		draw_colored_polygon(br, _c(Pal.LEATHER))
		draw_line(br[0], br[1], _c(Pal.INK), 0.8)
		draw_line(br[3], br[2], _c(Pal.INK), 0.8)
		draw_line(a1 - perp * w * 0.3, a2 - perp * w * 0.28,
			_c(Pal.LEATHER_HIGH), 0.8)
		draw_circle(a1 + (a2 - a1) * 0.5, 1.1, _c(Pal.GOLD))
	# Tangan
	draw_circle(hand, 2.3, _c(Pal.SKIN_DARK if back else Pal.SKIN))
	draw_arc(hand, 2.3, 0.4, 1.8, 6, _c(Pal.INK), 0.8)


func _draw_leg(_p: SylaraPose, j: Dictionary, back: bool) -> void:
	var hip_j: Vector2 = (j["hip_b"] if back else j["hip_f"]) as Vector2
	var knee: Vector2 = (j["knee_b"] if back else j["knee_f"]) as Vector2
	var ankle: Vector2 = (j["ankle_b"] if back else j["ankle_f"]) as Vector2
	var w: float = 4.0 if back else 4.4

	# Paha (celana hijau gelap)
	_draw_limb(hip_j, knee, w,
		Pal.CLOTH_DARK if back else Pal.CLOTH,
		Pal.CLOTH_DARKEST, Pal.CLOTH_LIGHT)
	# Proteksi lutut
	draw_circle(knee, w * 0.55, _c(Pal.LEATHER_DARK if back else Pal.LEATHER))
	draw_arc(knee, w * 0.55, 0.6, 2.2, 5, _c(Pal.INK), 0.7)
	# Betis (celana ketat)
	_draw_limb(knee, ankle, w * 0.85,
		Pal.CLOTH_DARK if back else Pal.CLOTH,
		Pal.CLOTH_DARKEST, Pal.CLOTH_LIGHT)


func _draw_limb(a: Vector2, b: Vector2, w: float, col: Color,
		col_sh: Color, col_hi: Color) -> void:
	var d: Vector2 = b - a
	if d.length_squared() < 0.001:
		return
	var dn: Vector2 = d.normalized()
	var perp: Vector2 = Vector2(-dn.y, dn.x)
	var aw: float = w * 0.5
	var bw: float = w * 0.42
	var poly := _pbuf(4)
	poly[0] = a + perp * aw
	poly[1] = b + perp * bw
	poly[2] = b - perp * bw
	poly[3] = a - perp * aw
	draw_colored_polygon(poly, _c(col))
	# Selout dua sisi
	draw_line(poly[0], poly[1], _c(Pal.INK), 0.8)
	draw_line(poly[3], poly[2], _c(Pal.INK), 0.8)
	# Ramp: sisi belakang (-perp diarahkan) = shadow; sisi depan = highlight
	draw_line(a + perp * (aw - 0.2), b + perp * (bw - 0.2), _c(col_sh), 1.1)
	draw_line(a - perp * (aw - 0.2), b - perp * (bw - 0.2), _c(col_hi), 0.8)


func _draw_feet(_p: SylaraPose, j: Dictionary) -> void:
	var keys: Array[String] = ["ankle_b", "ankle_f"]
	for ankle_key in keys:
		var is_front: bool = ankle_key == "ankle_f"
		var toe_key: String = "toe_f" if is_front else "toe_b"
		var ankle: Vector2 = j[ankle_key] as Vector2
		var toe: Vector2 = j[toe_key] as Vector2
		var col: Color = Pal.LEATHER if is_front else Pal.LEATHER_DARK
		var boot := _pbuf(5)
		boot[0] = ankle + Vector2(-2.5, -2.0)
		boot[1] = ankle + Vector2(2.5, -2.0)
		boot[2] = toe + Vector2(1.8, 0.0)
		boot[3] = toe + Vector2(-0.8, 1.6)
		boot[4] = ankle + Vector2(-3.5, 1.6)
		draw_colored_polygon(boot, _c(col))
		draw_polyline(boot, _c(Pal.INK), 0.9, true)
		# Band sepatu (ankle) + tutup toe highlight (ramp)
		draw_line(ankle + Vector2(-2.4, -0.6), ankle + Vector2(2.4, -0.6),
			_c(Pal.LEATHER_DARKEST), 1.2)
		draw_line(ankle + Vector2(0.4, 0.2), toe + Vector2(0.2, -0.4),
			_c(Pal.LEATHER_HIGH), 1.0)


# ══════════════════════════════════════════════════════════
#  6 & 7. TUNIC, TORSO, VEST, BELT
# ══════════════════════════════════════════════════════════

func _draw_tunic(p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var chest: Vector2 = j["chest"] as Vector2
	var sh_f: Vector2 = j["sh_f"] as Vector2
	var sh_b: Vector2 = j["sh_b"] as Vector2
	var flare: float = 2.2 + p.cape_flare * 3.2
	var poly := _pbuf(6)
	poly[0] = sh_b + Vector2(-2.2, -1.0)
	poly[1] = sh_f + Vector2(2.2, -1.0)
	poly[2] = hip + Vector2(5.5 + flare, 4.5)
	poly[3] = hip + Vector2(3.5 + flare, 8.5)
	poly[4] = hip + Vector2(-3.5 - flare, 8.5)
	poly[5] = hip + Vector2(-5.5 - flare, 4.5)
	draw_colored_polygon(poly, _c(Pal.CLOTH))
	draw_polyline(poly, _c(Pal.INK), 1.0, true)

	# Hem tunic (band gelap) + lipatan
	var mid_x: float = (sh_f.x + sh_b.x) * 0.5
	draw_line(hip + Vector2(5.2 + flare, 6.4), hip + Vector2(-5.2 - flare, 6.4),
		_c(Pal.CLOTH_DARK), 1.4)
	draw_line(Vector2(mid_x + 0.6, chest.y + 2.0),
		Vector2(mid_x + 0.6, hip.y + 6.0),
		_c(Color(Pal.CLOTH_DARK.r, Pal.CLOTH_DARK.g, Pal.CLOTH_DARK.b, 0.55)),
		1.2)
	# Highlight sisi depan (key light)
	draw_line(sh_f + Vector2(1.4, -0.4), hip + Vector2(4.6 + flare, 4.0),
		_c(Pal.CLOTH_LIGHT), 1.0)


func _draw_torso(_p: SylaraPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var neck: Vector2 = j["neck"] as Vector2
	var poly := _pbuf(4)
	poly[0] = chest + Vector2(-5.2, -2.0)
	poly[1] = chest + Vector2(5.2, -2.0)
	poly[2] = neck + Vector2(3.2, 1.0)
	poly[3] = neck + Vector2(-3.2, 1.0)
	draw_colored_polygon(poly, _c(Pal.CLOTH_LIGHT))
	# Leher
	draw_line(neck + Vector2(-2.0, 0.5), neck + Vector2(2.0, 0.5),
		_c(Pal.SKIN_DARK), 3.0)


func _draw_vest(_p: SylaraPose, j: Dictionary) -> void:
	var chest: Vector2 = j["chest"] as Vector2
	var sh_f: Vector2 = j["sh_f"] as Vector2
	var sh_b: Vector2 = j["sh_b"] as Vector2

	# Panel dada kiri/kanan (kulit terang)
	var panel_l := _pbuf(4)
	panel_l[0] = chest + Vector2(-4.5, -4.5)
	panel_l[1] = chest + Vector2(-1.2, -5.5)
	panel_l[2] = chest + Vector2(-1.2, 3.2)
	panel_l[3] = chest + Vector2(-4.5, 4.2)
	var panel_r := _pbuf(4)
	panel_r[0] = chest + Vector2(1.2, -5.5)
	panel_r[1] = chest + Vector2(4.5, -4.5)
	panel_r[2] = chest + Vector2(4.5, 4.2)
	panel_r[3] = chest + Vector2(1.2, 3.2)
	draw_colored_polygon(panel_l, _c(Pal.LEATHER_LIGHT))
	draw_colored_polygon(panel_r, _c(Pal.LEATHER))
	draw_polyline(panel_l, _c(Pal.INK), 0.8, true)
	draw_polyline(panel_r, _c(Pal.INK), 0.8, true)

	# Trim emas + dither (tekstur kulit klasik, 4 titik deterministik)
	draw_line(chest + Vector2(-4.5, -4.5), chest + Vector2(-4.5, 4.2),
		_c(Pal.GOLD_DARK), 1.0)
	draw_line(chest + Vector2(4.5, -4.5), chest + Vector2(4.5, 4.2),
		_c(Pal.GOLD_DARK), 1.0)
	for i in 4:
		var hx: float = chest.x + 1.8 + _hash01(i, 31) * 2.2
		var hy: float = chest.y - 3.5 + _hash01(i, 32) * 6.5
		draw_circle(Vector2(hx, hy), 0.5, _c(Color(Pal.LEATHER_DARK.r,
			Pal.LEATHER_DARK.g, Pal.LEATHER_DARK.b, 0.55)))

	# Pauldron (kap bahu)
	draw_circle(sh_f, 2.6, _c(Pal.LEATHER))
	draw_arc(sh_f, 2.6, 0.5, 2.6, 6, _c(Pal.INK), 0.8)
	draw_circle(sh_f + Vector2(-0.8, -0.8), 0.9, _c(Pal.GOLD))
	draw_circle(sh_b, 2.4, _c(Pal.LEATHER_DARK))
	draw_arc(sh_b, 2.4, 0.5, 2.6, 6, _c(Pal.INK), 0.8)


func _draw_belt(_p: SylaraPose, j: Dictionary) -> void:
	var hip: Vector2 = j["hip"] as Vector2
	var belt := _pbuf(4)
	belt[0] = hip + Vector2(-6.5, -1.2)
	belt[1] = hip + Vector2(6.5, -1.2)
	belt[2] = hip + Vector2(6.5, 2.2)
	belt[3] = hip + Vector2(-6.5, 2.2)
	draw_colored_polygon(belt, _c(Pal.LEATHER_DARK))
	draw_polyline(belt, _c(Pal.INK), 0.9, true)
	# Buckle emas
	draw_rect(Rect2(hip.x - 2.5, hip.y - 1.5, 5.0, 3.5), _c(Pal.GOLD))
	draw_rect(Rect2(hip.x - 1.5, hip.y - 0.8, 3.0, 2.2), _c(Pal.GOLD_LIGHT))
	# Pouch samping + strap
	var pouch := Rect2(hip.x - 6.2, hip.y - 0.5, 3.0, 3.8)
	draw_rect(pouch, _c(Pal.LEATHER))
	draw_rect(pouch, _c(Pal.INK), false, 0.9)
	draw_line(hip + Vector2(5.0, 2.2), hip + Vector2(5.8, 6.5),
		_c(Pal.LEATHER), 1.4)


# ══════════════════════════════════════════════════════════
#  8. HOOD — tudung runcing ranger
# ══════════════════════════════════════════════════════════

func _draw_hood(p: SylaraPose, j: Dictionary) -> void:
	var neck: Vector2 = j["neck"] as Vector2
	var head_c: Vector2 = j["head_c"] as Vector2

	# Tudung: puncak runcing sedikit ke belakang (siluet khas ranger)
	var hood_poly := _pbuf(7)
	hood_poly[0] = neck + Vector2(-6.5, -1.0)
	hood_poly[1] = head_c + Vector2(-5.5, -HEAD_R - 2.5)
	hood_poly[2] = head_c + Vector2(-1.5, -HEAD_R - 5.2)   # PUNCAK RUNCING
	hood_poly[3] = head_c + Vector2(4.8, -HEAD_R - 1.5)
	hood_poly[4] = neck + Vector2(5.5, 0.0)
	hood_poly[5] = neck + Vector2(3.5, 2.5)
	hood_poly[6] = neck + Vector2(-4.5, 2.5)
	draw_colored_polygon(hood_poly, _c(Pal.HOOD))
	draw_polyline(hood_poly, _c(Pal.INK), 1.0, true)

	# Rim key light di sisi depan-atas hood
	draw_line(hood_poly[2], hood_poly[3], _c(Pal.HOOD_LIGHT), 1.2)
	draw_line(hood_poly[1], hood_poly[2], _c(Pal.HOOD_DARK), 1.2)
	# Bayangan dalam cowl (wajah berada dalam bayang tudung)
	draw_arc(head_c + Vector2(0.0, -HEAD_R * 0.35), HEAD_R * 0.85,
		PI + 0.35, TAU - 0.35, 8,
		_c(Color(Pal.HOOD_DARKEST.r, Pal.HOOD_DARKEST.g,
		Pal.HOOD_DARKEST.b, 0.55)), 2.0)

	# Cowl edge trailing (secondary motion)
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
#  9. HEAD & WAJAH — fringe oranye + mata emerald + blink
# ══════════════════════════════════════════════════════════

func _draw_head(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var lean: float = p.head_lean + p.look * 0.06

	# Bentuk wajah (12-gon)
	var face_pts := _pbuf(12)
	for i in 12:
		var a: float = float(i) / 12.0 * TAU
		var rx: float = HEAD_R * 0.85
		var ry: float = HEAD_R
		face_pts[i] = head_c + Vector2(cos(a) * rx + lean * 3.0, sin(a) * ry)
	draw_colored_polygon(face_pts, _c(Pal.SKIN))
	draw_polyline(face_pts, _c(Pal.INK), 1.0, true)

	# Bayangan dagu/rahang + sisi belakang (hood shadow)
	draw_arc(head_c + Vector2(lean * 2.0, HEAD_R * 0.45), HEAD_R * 0.52,
		0.3, PI - 0.3, 8,
		_c(Color(Pal.SKIN_SHADE.r, Pal.SKIN_SHADE.g, Pal.SKIN_SHADE.b, 0.4)),
		1.4)
	draw_arc(head_c + Vector2(-1.4 + lean * 2.0, 0.0), HEAD_R * 0.85,
		PI - 0.5, PI + 0.5, 6,
		_c(Color(Pal.HOOD_DARKEST.r, Pal.HOOD_DARKEST.g,
		Pal.HOOD_DARKEST.b, 0.4)), 1.6)

	# Fringe (tumpukan rambut oranye di dahi — membingkai wajah)
	var fx: float = head_c.x + lean * 2.0
	var fringe := _pbuf(6)
	fringe[0] = head_c + Vector2(-4.6 + lean * 3.0, -HEAD_R + 0.4)
	fringe[1] = head_c + Vector2(-1.5 + lean * 3.0, -HEAD_R + 2.6)
	fringe[2] = head_c + Vector2(1.0 + lean * 3.0, -HEAD_R + 1.0)
	fringe[3] = head_c + Vector2(4.0 + lean * 3.0, -HEAD_R + 2.0)
	fringe[4] = head_c + Vector2(4.4 + lean * 3.0, -HEAD_R - 0.6)
	fringe[5] = head_c + Vector2(-4.8 + lean * 3.0, -HEAD_R - 0.6)
	draw_colored_polygon(fringe, _c(Pal.HAIR))
	# Notch helai
	draw_line(Vector2(fx - 2.2, head_c.y - HEAD_R + 2.4),
		Vector2(fx - 2.6, head_c.y - HEAD_R + 0.6), _c(Pal.HAIR_DARK), 0.9)
	draw_line(Vector2(fx + 1.4, head_c.y - HEAD_R + 1.8),
		Vector2(fx + 1.2, head_c.y - HEAD_R + 0.2), _c(Pal.HAIR_LIGHT), 0.9)

	# Mata — iris emerald + specular (titik fokus wajah)
	var eye_x: float = head_c.x + 2.6 + lean * 2.0
	var eye_y: float = head_c.y - 1.2
	var blink: float = p.eye_blink
	if blink < 0.75:
		draw_circle(Vector2(eye_x, eye_y), 2.0, _c(Pal.EYE_WHITE))
		draw_circle(Vector2(eye_x + 0.35, eye_y), 1.35, _c(Pal.EYE))
		draw_circle(Vector2(eye_x + 0.55, eye_y - 0.25), 0.65, _c(Pal.INK))
		draw_circle(Vector2(eye_x + 0.85, eye_y - 0.85), 0.45,
			_c(Color(1, 1, 1, 0.85)))
		# Garis kelopak bawah
		draw_line(Vector2(eye_x - 1.4, eye_y + 1.3), Vector2(eye_x + 1.2,
			eye_y + 1.3), _c(Color(Pal.SKIN_SHADE.r, Pal.SKIN_SHADE.g,
			Pal.SKIN_SHADE.b, 0.5)), 0.8)
	else:
		draw_line(Vector2(eye_x - 1.8, eye_y), Vector2(eye_x + 1.8, eye_y),
			_c(Pal.INK), 1.3)

	# Alis (temaram — fokus tetap pada mata)
	draw_line(Vector2(eye_x - 1.5, eye_y - 2.8), Vector2(eye_x + 1.8,
		eye_y - 2.3), _c(Pal.HAIR_DARK), 1.1)
	# Hidung + mulut
	draw_line(head_c + Vector2(3.0 + lean, -0.2),
		head_c + Vector2(3.3 + lean, 1.2),
		_c(Color(Pal.SKIN_SHADE.r, Pal.SKIN_SHADE.g, Pal.SKIN_SHADE.b, 0.5)),
		0.9)
	draw_line(head_c + Vector2(1.6 + lean, 3.0),
		head_c + Vector2(3.6 + lean, 2.8),
		_c(Color(Pal.SKIN_SHADE.r, Pal.SKIN_SHADE.g, Pal.SKIN_SHADE.b, 0.65)),
		0.9)


# ══════════════════════════════════════════════════════════
#  10. TRAIL — jejak sapuan busur (3 lapis, lebar menyusut)
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
#  12. BOW — busur recurve detail + tali + anak panah angin
# ══════════════════════════════════════════════════════════

func _draw_bow(_p: SylaraPose, j: Dictionary) -> void:
	var grip: Vector2 = j["bow_grip"] as Vector2
	var tip: Vector2 = j["bow_tip"] as Vector2
	var tip_lo: Vector2 = j["bow_tip_lo"] as Vector2
	var nock: Vector2 = j["bow_nock"] as Vector2
	var bow_dir: Vector2 = j["bow_dir"] as Vector2
	var bow_perp: Vector2 = j["bow_perp"] as Vector2
	var draw_amt: float = 0.0 if _p == null else _p.bow_draw

	# Limb atas & bawah (Bézier: melengkung menjauh dari grip)
	var ctrl_hi: Vector2 = grip + bow_dir * BOW_LEN * 0.55 + bow_perp * 4.5
	var ctrl_lo: Vector2 = grip - bow_dir * BOW_LEN * 0.55 - bow_perp * 4.5
	_draw_bow_limb(grip + bow_dir * 3.2, ctrl_hi, tip, 3.2, 1.6, true)
	_draw_bow_limb(grip - bow_dir * 3.2, ctrl_lo, tip_lo, 3.2, 1.6, false)

	# Recurve horn tips (menggelung balik — siluet busur khas)
	var horn_hi: Vector2 = tip + bow_perp * 3.2
	var horn_lo: Vector2 = tip_lo - bow_perp * 3.2
	draw_line(tip, horn_hi, _c(Pal.WOOD_SHINE), 2.2)
	draw_line(tip_lo, horn_lo, _c(Pal.WOOD_SHINE), 2.2)
	draw_line(tip, horn_hi, _c(Pal.WOOD_DARK), 1.0)
	draw_line(tip_lo, horn_lo, _c(Pal.WOOD_DARK), 1.0)

	# Nock emas di kedua tip + glint
	draw_circle(tip, 1.4, _c(Pal.GOLD))
	draw_circle(tip_lo, 1.4, _c(Pal.GOLD))
	var g := _glint(phase, 0.3)
	if g > 0.01:
		draw_circle(tip + bow_perp * 1.6, 0.9 * g, _c(Color(Pal.GOLD_HOT.r,
			Pal.GOLD_HOT.g, Pal.GOLD_HOT.b, 0.95 * g)))
	var g2 := _glint(phase, 0.55)
	if g2 > 0.01:
		draw_circle(tip_lo - bow_perp * 1.6, 0.8 * g2, _c(Color(Pal.GOLD_HOT.r,
			Pal.GOLD_HOT.g, Pal.GOLD_HOT.b, 0.9 * g2)))

	# Grip wrap (pola lilitan)
	var grip_poly := _pbuf(4)
	grip_poly[0] = grip + bow_dir * 3.2 + bow_perp * 1.7
	grip_poly[1] = grip + bow_dir * 3.2 - bow_perp * 1.7
	grip_poly[2] = grip - bow_dir * 3.2 - bow_perp * 1.7
	grip_poly[3] = grip - bow_dir * 3.2 + bow_perp * 1.7
	draw_colored_polygon(grip_poly, _c(Pal.WOOD_DARK))
	for i in 3:
		var off: float = -2.0 + float(i) * 2.0
		draw_line(grip + bow_dir * off + bow_perp * 1.7,
			grip + bow_dir * off - bow_perp * 1.7, _c(Pal.WOOD_LIGHT), 0.8)
	# Gold trim di ujung grip
	draw_circle(grip + bow_dir * 3.4, 1.1, _c(Pal.GOLD))
	draw_circle(grip - bow_dir * 3.4, 1.1, _c(Pal.GOLD))

	# Tali busur (ditarik ke -bow_dir = ke arah panah terseret)
	if draw_amt > 0.01:
		draw_line(tip, nock, _c(Pal.STRING), 1.3)
		draw_line(nock, tip_lo, _c(Pal.STRING), 1.3)
		# Highlight tali (string sheen)
		draw_line(tip, nock, _c(Pal.STRING_SHINE), 0.5)
		# Anak panah angin saat tali terdraw
		if draw_amt > 0.22:
			var arrow_tip: Vector2 = grip + bow_dir * (BOW_LEN + 9.0)
			_draw_arrow(nock, arrow_tip, draw_amt)
	else:
		draw_line(tip, tip_lo, _c(Pal.STRING), 1.3)
		draw_line(tip, tip_lo, _c(Pal.STRING_SHINE), 0.4)

	# Update cache (ruang lokal) — SkillFX mengubah ke global.
	_bow_grip = grip
	_bow_tip = tip
	_bow_tip_lo = tip_lo
	_bow_nock = nock


func _draw_bow_limb(start: Vector2, ctrl: Vector2, end: Vector2,
		w_start: float, w_end: float, upper: bool) -> void:
	var n: int = 8
	var pts_outer := _pbuf(n + 1)
	var pts_inner := _pbuf(n + 1)
	for i in n + 1:
		var t: float = float(i) / float(n)
		var pt: Vector2 = (1.0 - t) * (1.0 - t) * start \
			+ 2.0 * (1.0 - t) * t * ctrl + t * t * end
		var w: float = lerpf(w_start, w_end, t)
		var dt: float = 0.01
		var t2: float = minf(t + dt, 1.0)
		var p2: Vector2 = (1.0 - t2) * (1.0 - t2) * start \
			+ 2.0 * (1.0 - t2) * t2 * ctrl + t2 * t2 * end
		var tangent: Vector2 = (p2 - pt)
		if tangent.length_squared() < 0.001:
			tangent = Vector2.RIGHT
		tangent = tangent.normalized()
		var normal: Vector2 = Vector2(-tangent.y, tangent.x)
		pts_outer[i] = pt + normal * w * 0.5
		pts_inner[i] = pt - normal * w * 0.5

	var poly := _pbuf(2 * (n + 1))
	for i in n + 1:
		poly[i] = pts_outer[i]
		poly[n + 1 + i] = pts_inner[n - i]
	draw_colored_polygon(poly, _c(Pal.WOOD))
	# Selout sisi luar + highlight kayu (ramp 3 nilai)
	var edge := _pbuf(n + 1)
	for i in n + 1:
		edge[i] = pts_outer[i]
	draw_polyline(edge, _c(Pal.INK), 0.8, true)
	var shine := _pbuf(n + 1)
	for i in n + 1:
		var mid: Vector2 = (pts_outer[i] + pts_inner[i]) * 0.5
		var tangent2: Vector2 = pts_outer[i] - pts_inner[i]
		if tangent2.length_squared() > 0.001:
			mid += tangent2.normalized() * (0.5 if upper else -0.5)
		shine[i] = mid
	draw_polyline(shine, _c(Pal.WOOD_SHINE), 0.9, true)


## Anak panah angin: shaft + inti wind + mata perak + fletching emerald.
func _draw_arrow(nock: Vector2, tip: Vector2, draw_amt: float) -> void:
	var d: Vector2 = (tip - nock).normalized()
	var perp: Vector2 = Vector2(-d.y, d.x)

	# Shaft (outline gelap + badan + inti angin)
	draw_line(nock, tip, _c(Pal.SHAFT_DARK), 2.4)
	draw_line(nock, tip, _c(Pal.SHAFT), 1.6)
	draw_line(nock + d * 4.0, tip - d * 3.0,
		_c(Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b,
		0.55 * draw_amt)), 1.0)

	# Mata panah perak runcing
	var head_poly := _pbuf(3)
	head_poly[0] = tip + d * 2.0
	head_poly[1] = tip - d * 4.5 + perp * 2.4
	head_poly[2] = tip - d * 4.5 - perp * 2.4
	draw_colored_polygon(head_poly, _c(Pal.HEAD))
	draw_polyline(head_poly, _c(Pal.INK), 0.8, true)
	draw_line(tip + d * 1.5, tip - d * 4.0, _c(Pal.HEAD_SHINE), 0.8)

	# Fletching bulu hijau zamrud (4 garis — identitas panah Sylara)
	var f_base: Vector2 = nock + d * 3.8
	draw_line(f_base, f_base - d * 3.2 + perp * 2.8, _c(Pal.FEATHER), 1.4)
	draw_line(f_base, f_base - d * 3.2 - perp * 2.8, _c(Pal.FEATHER), 1.4)
	draw_line(f_base - d * 1.0, f_base - d * 3.8 + perp * 2.0,
		_c(Pal.FEATHER_DARK), 1.0)
	draw_line(f_base - d * 1.0, f_base - d * 3.8 - perp * 2.0,
		_c(Pal.FEATHER_DARK), 1.0)


# ══════════════════════════════════════════════════════════
#  13. RIM LIGHT / GLINTS / WISPS
# ══════════════════════════════════════════════════════════

func _draw_rim(p: SylaraPose, j: Dictionary) -> void:
	var head_c: Vector2 = j["head_c"] as Vector2
	var rim_col: Color = Color(Pal.RIM.r, Pal.RIM.g, Pal.RIM.b,
		0.4 * p.alpha)
	# Head rim (sisi atas-kiri = key light)
	draw_arc(head_c + Vector2(-1.2, -1.2), HEAD_R * 0.95, 2.7, 4.3, 6,
		rim_col, 1.2)
	# Hood peak rim
	draw_arc(head_c + Vector2(-1.5, -HEAD_R - 1.0), 3.4, 2.4, 3.9, 5,
		rim_col, 1.0)
	# Shoulder rim
	var sh_f: Vector2 = j["sh_f"] as Vector2
	draw_line(sh_f + Vector2(-1.2, -2.4), sh_f + Vector2(2.2, -3.4),
		rim_col, 1.2)


func _draw_wisps(p: SylaraPose, j: Dictionary) -> void:
	if p.wind_glow < 0.05:
		return
	var glow: float = p.wind_glow
	var bow_tip: Vector2 = j["bow_tip"] as Vector2

	# Wisps di ujung busur (3 titik orbit deterministik)
	var wisp_col: Color = Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g,
		Pal.WIND_LIGHT.b, 0.55 * glow * p.alpha)
	for i in 3:
		var t: float = phase * 3.2 + float(i) * 2.1
		var off: Vector2 = Vector2(sin(t) * 4.5, cos(t * 1.4) * 3.5)
		draw_circle(bow_tip + off, 1.6 + sin(t * 2.0) * 0.5, wisp_col)

	# Daun orbit kecil di sekitar nock saat glow kuat (aksen 10%)
	if glow > 0.4:
		var nock: Vector2 = j["bow_nock"] as Vector2
		for i in 2:
			var t: float = phase * 2.6 + float(i) * PI
			var lp: Vector2 = nock + Vector2(cos(t) * 7.0, sin(t) * 4.5)
			draw_circle(lp, 1.0, _c(Color(Pal.LEAF_GOLD.r, Pal.LEAF_GOLD.g,
				Pal.LEAF_GOLD.b, 0.5 * glow * p.alpha)))

	# Charge glow di nock saat draw
	if p.bow_draw > 0.2:
		var nock2: Vector2 = j["bow_nock"] as Vector2
		var nock_glow: Color = Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g,
			Pal.WIND_BRIGHT.b, 0.65 * p.bow_draw * p.alpha)
		draw_circle(nock2, 3.2 * p.bow_draw, nock_glow)
		draw_circle(nock2, 1.6 * p.bow_draw,
			Color(1, 1, 1, 0.45 * p.bow_draw * p.alpha))


# ══════════════════════════════════════════════════════════
#  14. FEEDBACK — debu kontak + hurt flash
# ══════════════════════════════════════════════════════════

func _draw_dust(p: SylaraPose, j: Dictionary) -> void:
	if p.dust < 0.05:
		return
	var ankle_b: Vector2 = j["ankle_b"] as Vector2
	for i in 3:
		var h := _hash01(i, 41)
		var off: Vector2 = Vector2(-2.0 - h * 4.0 - i * 1.5,
			-0.5 - h * 2.0)
		var r: float = (1.2 + h * 1.2) * (0.5 + p.dust * 0.7)
		var col: Color = Color(Pal.DUST.r, Pal.DUST.g, Pal.DUST.b,
			0.20 * p.dust * p.alpha * (1.0 - float(i) * 0.25))
		draw_circle(ankle_b + off, r, col)


func _draw_hurt_flash(p: SylaraPose, j: Dictionary) -> void:
	# Arena: flash putih datang dari HurtFlash (modulate rig). Lapisan ini
	# tetap untuk scene demo (tanpa Hero -> tanpa HurtFlash).
	var chest: Vector2 = j["chest"] as Vector2
	var head_c: Vector2 = j["head_c"] as Vector2
	var col: Color = Color(Pal.HURT_TINT.r, Pal.HURT_TINT.g, Pal.HURT_TINT.b,
		0.3 * p.hurt_tint * p.alpha)
	draw_circle(chest + Vector2(0.0, -1.0), 7.0, col)
	draw_circle(head_c, 5.0, col)
