# VFXActor.gd — satu node FX generik yang DI-POOL oleh VFXManager.
#
# Prinsip desain (lihat MASTER kualitas FX proyek):
#   JUICE = TIMING + MOTION + CONTRAST + SHAPE + IMPACT, bukan jumlah
#   partikel. Setiap actor menggambar BENTUK SOLID yang kontras + satu
#   garis tepi terang + (opsional) inti kecil — glow hanyalah aksen.
#
# Semua mode digambar lewat _draw() (CPU, tanpa shader partikel) sehingga
# aman di renderer Compatibility/GLES Android dan tidak mengalokasikan
# node baru per efek. VFXManager tidak pernah instantiate saat gameplay:
# actor diambil dari pool, di-reset, dan dikembalikan.
class_name VFXActor
extends Node2D

enum Mode { NONE, RING, SLASH, FLASH, STREAK, SPARKS, GLOW, WALL }

const MAX_SPARKS := 10

var mode: int = Mode.NONE
var active := false
## Delay sebelum efek mulai (untuk menyusun sequenced skill FX).
var delay := 0.0
var t := 0.0
var dur := 0.3
## Urutan spawn — dipakai VFXManager untuk mencuri actor tertua saat pool habis.
var generation := 0

# ── Parameter bersama ──
var color := Color.WHITE
var color2 := Color.WHITE
var radius := 10.0
var angle := 0.0
var sweep := TAU
var thickness := 4.0
var spin := 0.0
var size_pt := 6.0
var pt_a := Vector2.ZERO
var pt_b := Vector2.ZERO

# ── Sparks (disimulasikan CPU, maksimal 10 titik) ──
var spark_pos := PackedVector2Array()
var spark_vel := PackedVector2Array()
var spark_count := 0

# ── WALL: mengikuti unit pemakai ──
var follow: Node2D = null
var follow_off := Vector2.ZERO


static func _dir(a: float) -> Vector2:
	return Vector2(cos(a), -sin(a))


static func _ss(x: float) -> float:
	x = clampf(x, 0.0, 1.0)
	return x * x * (3.0 - 2.0 * x)


func _process(delta: float) -> void:
	if not active:
		return
	if delay > 0.0:
		delay -= delta
		return
	t += delta
	if mode == Mode.WALL:
		if follow != null and is_instance_valid(follow):
			global_position = follow.global_position + follow_off
			z_index = int(global_position.y) + 1
		else:
			_finish()
			return
	elif mode == Mode.SPARKS:
		_simulate_sparks(delta)
	if t >= dur:
		_finish()
		return
	queue_redraw()


func _simulate_sparks(delta: float) -> void:
	var drag := exp(-2.8 * delta)
	for i in spark_count:
		spark_vel[i] = spark_vel[i] * drag
		spark_pos[i] = spark_pos[i] + spark_vel[i] * delta


func _finish() -> void:
	active = false
	visible = false
	mode = Mode.NONE
	follow = null
	set_process(false)
	VFXManager.release_actor(self)


func activate() -> void:
	active = true
	visible = true
	t = 0.0
	z_as_relative = false
	z_index = int(global_position.y) + 1
	set_process(true)
	queue_redraw()


# ══════════════════════════════════════════════════════════
#  GAMBAR
# ══════════════════════════════════════════════════════════

func _draw() -> void:
	if not active or delay > 0.0:
		return
	var k := clampf(t / maxf(0.001, dur), 0.0, 1.0)
	match mode:
		Mode.RING:
			_draw_ring(k)
		Mode.SLASH:
			_draw_slash(k)
		Mode.FLASH:
			_draw_flash(k)
		Mode.STREAK:
			_draw_streak(k)
		Mode.SPARKS:
			_draw_sparks(k)
		Mode.GLOW:
			_draw_glow(k)
		Mode.WALL:
			_draw_wall(k)


func _draw_ring(k: float) -> void:
	var ease := 1.0 - pow(1.0 - k, 2.2)
	var r := radius * (0.25 + 0.75 * ease)
	var a := 1.0 - k
	draw_arc(Vector2.ZERO, r, 0.0, TAU, 36,
		Color(color.r, color.g, color.b, a * 0.85),
		maxf(1.0, thickness * (1.0 - k * 0.6)))
	draw_arc(Vector2.ZERO, r * 0.78, 0.0, TAU, 28,
		Color(color2.r, color2.g, color2.b, a * 0.38), 1.5)


## Sabit tebasan: sektor annulus yang tumbuh cepat lalu memudar.
## Ujung sabit meruncing (ketebalan = sin sepanjang busur) — bentuk kuat,
## langsung terbaca sebagai "tebasan angin".
func _draw_slash(k: float) -> void:
	var grow := _ss(minf(1.0, k / 0.42))
	var fade := 1.0 - _ss(maxf(0.0, (k - 0.55) / 0.45))
	if fade <= 0.01 or grow <= 0.02:
		return
	var rot := angle + spin * k
	var r_out := radius * (0.82 + 0.22 * grow)
	var sweep_now := sweep * grow
	var n := 14
	var pts := PackedVector2Array()
	var inner := PackedVector2Array()
	for i in n + 1:
		var u := float(i) / float(n)
		var a := rot + sweep_now * u
		var th := thickness * sin(u * PI) + 0.6
		var d := _dir(a)
		pts.append(d * r_out)
		inner.append(d * (r_out - th))
	var poly := PackedVector2Array()
	for v in pts:
		poly.append(v)
	for i in range(inner.size() - 1, -1, -1):
		poly.append(inner[i])
	draw_colored_polygon(poly,
		Color(color.r, color.g, color.b, 0.85 * fade))
	# Tepi luar terang — kontras membaca arah tebasan.
	for i in range(pts.size() - 1):
		draw_line(pts[i], pts[i + 1],
			Color(color2.r, color2.g, color2.b, 0.9 * fade), 1.6)


func _draw_flash(k: float) -> void:
	var alpha := pow(1.0 - k, 1.6)
	var sc := size_pt * (1.25 - 0.25 * k)
	if k < 0.3:
		sc = size_pt * (k / 0.3) * 1.25
	# Bintang 4-spike (bentuk solid) + inti kecil terang.
	var spike := PackedVector2Array()
	for i in 8:
		var a := float(i) * TAU / 8.0 + PI / 8.0
		var r := sc if i % 2 == 0 else sc * 0.38
		spike.append(Vector2(cos(a), sin(a)) * r)
	draw_colored_polygon(spike, Color(color.r, color.g, color.b, 0.8 * alpha))
	draw_circle(Vector2.ZERO, sc * 0.34,
		Color(color2.r, color2.g, color2.b, 0.95 * alpha))


func _draw_streak(k: float) -> void:
	var alpha := pow(1.0 - k, 1.8)
	var d := pt_b - pt_a
	var ln := d.length()
	if ln < 0.001:
		return
	d /= ln
	var perp := Vector2(-d.y, d.x)
	var head := pt_a + d * ln * (0.55 + 0.45 * _ss(minf(1.0, k / 0.4)))
	# Ekor meruncing dari kepala ke ekor.
	var poly := PackedVector2Array([
		pt_a + perp * 1.0,
		head + perp * size_pt,
		pt_b + perp * size_pt * 0.55,
		pt_b - perp * size_pt * 0.55,
		head - perp * size_pt,
		pt_a - perp * 1.0,
	])
	draw_colored_polygon(poly, Color(color.r, color.g, color.b, 0.5 * alpha))
	# Inti garis arah — informasi gerakan yang paling penting.
	draw_line(pt_a, head, Color(color2.r, color2.g, color2.b, 0.85 * alpha), 1.8)


func _draw_sparks(k: float) -> void:
	var alpha := pow(1.0 - k, 1.4)
	for i in spark_count:
		var sp: Vector2 = spark_pos[i]
		draw_rect(Rect2(sp.x - 1.0, sp.y - 1.0, 2.0, 2.0),
			Color(color.r, color.g, color.b, alpha))
	# Kilau kecil di titik-titik tercepat (aksen, bukan glow penuh).
	if spark_count > 0 and k < 0.5:
		var sp: Vector2 = spark_pos[0]
		draw_rect(Rect2(sp.x - 1.0, sp.y - 1.0, 2.0, 2.0),
			Color(color2.r, color2.g, color2.b, alpha * 0.9))


func _draw_glow(k: float) -> void:
	var alpha := (1.0 - k) * 0.28
	var r := radius * (0.75 + 0.25 * k)
	draw_circle(Vector2.ZERO, r, Color(color.r, color.g, color.b, alpha))
	draw_arc(Vector2.ZERO, r * 1.04, 0.0, TAU, 30,
		Color(color2.r, color2.g, color2.b, alpha * 0.6), 1.4)


## Dinding angin Kaizen (W): tiga sabit berorbit + garis hembusan vertikal.
func _draw_wall(k: float) -> void:
	var fade_in := _ss(minf(1.0, t / 0.14))
	var fade_out := _ss(clampf((dur - t) / 0.4, 0.0, 1.0))
	var vis := fade_in * fade_out
	if vis <= 0.01:
		return
	# Tiga sabit mengorbit — bentuk utama (70%).
	for i in 3:
		var base := t * 3.4 + float(i) * TAU / 3.0
		var a_col := Color(color.r, color.g, color.b, 0.62 * vis)
		draw_arc(Vector2.ZERO, radius, base, base + 1.15, 12, a_col, 3.2)
		draw_arc(Vector2.ZERO, radius - 2.0, base + 0.08, base + 1.05, 10,
			Color(color2.r, color2.g, color2.b, 0.5 * vis), 1.2)
	# Hembusan vertikal — FX sekunder (20%), sedikit saja.
	for i in 2:
		var x := sin(t * 2.4 + float(i) * 2.6) * 9.0
		var y0 := -radius - 6.0 + float(i) * 7.0
		draw_line(Vector2(x, y0), Vector2(x, y0 + 9.0),
			Color(color2.r, color2.g, color2.b, 0.34 * vis), 1.4)
