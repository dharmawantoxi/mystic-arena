# HitSpark.gd — port 1:1 `_render.HitParticle` (`_render.py:418-493`).
#
# Percikan kecil saat unit kena pukul. Murni DATA (posisi/kecepatan/sisa
# umur) tanpa node: `SparkField` yang memegang list-nya (paritas
# `EffectManager.particles`) dan `SparkLayer` yang menggambar.
#
# Yang dikunci `tools/test_render_parity.py` + `godot/tests/RenderFxParityTest`
# (fixture `render_fx.json`, jejak `pygame.draw.circle` + `blit` SUNGGUHAN):
#   * gerak  : x += vx; y += vy; vy += gravity(0.15); vx *= 0.95; life -= 1
#              (posisi diperbarui SEBELUM gravitasi — urutan pygame)
#   * draw   : ratio = life/max_life; alpha = int(255*ratio);
#              ukuran = max(1, int(size*ratio)); lewat kalau alpha <= 0
#   * bentuk : DUA lingkaran sepusat di (int(x), int(y)) — inti warna lalu
#              titik putih. Pygame menggambar keduanya SEKALI ke sprite
#              3*base px (`_psurf`) lalu men-scale ke 3*ukuran px tiap frame,
#              jadi radius ikut skala: base -> ukuran, max(1, base//2) ->
#              max(1, base//2) * ukuran / base. Alpha sprite (set_alpha)
#              mengalikan alpha kedua lingkaran.
#
# RASTER tidak dibandingkan (Godot `draw_circle` vs hasil `transform.scale`
# pygame); yang dibandingkan geometri, warna, alpha, dan urutan perintah.
extends RefCounted
class_name HitSpark

## `self.gravity = 0.15` (`_render.py:438`).
const GRAVITY := 0.15
## `self.vx *= 0.95` (`_render.py:462`).
const FRICTION := 0.95
## Warna bawaan `(255, 200, 100)`.
const DEFAULT_COLOR: Array = [255, 200, 100]
## `lifetime=15` bawaan signature pygame.
const DEFAULT_LIFETIME := 15
## `size=2` bawaan signature pygame.
const DEFAULT_SIZE := 2
## Rentang kecepatan acak saat `velocity` tidak diberikan (`_render.py:432`).
const SPEED_MIN := 1.0
const SPEED_MAX := 3.0

var x := 0.0
var y := 0.0
var color: Array = DEFAULT_COLOR.duplicate()
var vx := 0.0
var vy := 0.0
var lifetime: int = DEFAULT_LIFETIME
var max_lifetime: int = DEFAULT_LIFETIME
var size: int = DEFAULT_SIZE
var alive := true
var gravity := GRAVITY
## Radius lingkaran warna pada sprite pra-render (`self._pbase` pygame).
var pbase := 1


## `velocity` = Array/Vector2 [vx, vy] atau null (acak radial seperti pygame).
## `rng` = objek ber-`uniform(a, b)` untuk harness replay; produksi = null
## (pakai `randf_range` global).
func _init(px: float = 0.0, py: float = 0.0, pcolor: Array = DEFAULT_COLOR,
		velocity = null, plifetime: int = DEFAULT_LIFETIME,
		psize: int = DEFAULT_SIZE, rng = null) -> void:
	x = px
	y = py
	color = pcolor
	if velocity != null:
		vx = float(velocity[0])
		vy = float(velocity[1])
	else:
		var angle := uniform(rng, 0.0, TAU)
		var speed := uniform(rng, SPEED_MIN, SPEED_MAX)
		vx = cos(angle) * speed
		vy = sin(angle) * speed
	lifetime = plifetime
	max_lifetime = plifetime
	size = psize
	pbase = maxi(1, int(size))


## `HitParticle.update` (`_render.py:461-472`): SATU frame pygame.
func update() -> void:
	if not alive:
		return
	x += vx
	y += vy
	vy += gravity
	vx *= FRICTION
	lifetime -= 1
	if lifetime <= 0:
		alive = false


## Daftar perintah gambar satu partikel (paritas `HitParticle.draw`).
## Kosong = pygame juga tidak menggambar apa pun pada frame ini.
##
## Pusat lingkaran BUKAN sekadar (int(x), int(y)): pygame menggambar sprite
## ke kanvas 3*base px, men-scale-nya ke 3*ukuran px, lalu mem-blit di
## `int(x) - ukuran*3//2`. Pusat optis sprite hasil scale adalah
## `posisi_blit + pusat_kanvas * faktor_skala`, yang bisa jatuh di setengah
## piksel (base genap + ukuran gasal) — jejak fixture mengunci angka itu.
func build_ops() -> Array:
	if not alive:
		return []
	var ratio := float(lifetime) / float(max_lifetime)
	var alpha := int(255.0 * ratio)
	var radius := maxi(1, int(float(size) * ratio))
	if alpha <= 0 or radius <= 0:
		return []
	var side := float(radius * 3)
	var factor := side / float(pbase * 3)
	var center := float(int(floorf(float(pbase * 3) / 2.0)))
	var cx := float(int(x)) - float(int(floorf(side / 2.0))) + center * factor
	var cy := float(int(y)) - float(int(floorf(side / 2.0))) + center * factor
	var inner := float(maxi(1, int(floorf(float(pbase) / 2.0))))
	var out: Array = []
	out.append({"op": "circle", "x": cx, "y": cy, "r": float(pbase) * factor,
		"color": [int(color[0]), int(color[1]), int(color[2]), alpha]})
	out.append({"op": "circle", "x": cx, "y": cy, "r": inner * factor,
		"color": [255, 255, 255, alpha]})
	return out


## `random.uniform` pygame — lewat `rng` kalau harness memasangnya.
static func uniform(rng, lo: float, hi: float) -> float:
	if rng != null:
		return float(rng.uniform(lo, hi))
	return randf_range(lo, hi)
