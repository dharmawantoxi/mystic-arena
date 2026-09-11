# DeathBurst.gd — port 1:1 `_render.DeathExplosion` (`_render.py:494-571`).
#
# Ledakan radial saat unit mati: `count` percikan `HitSpark` + kilat pusat
# 8 frame. Murni data; digambar `SparkLayer`.
#
# Yang dikunci fixture `render_fx.json` (oracle menjalankan kelas pygame
# SUNGGUHAN dan merekam nilai `random.uniform/choice/randint` yang
# DIKONSUMSI): jumlah partikel per preset, palet per tim, rentang spark,
# urutan konsumsi RNG (angle -> speed -> warna -> ukuran -> lifetime),
# geometri kilat pusat (radius int(20*intensity) + int(20*intensity)//2),
# dan aturan `alive` (partikel habis DAN kilat selesai).
extends RefCounted
class_name DeathBurst

const HitSparkScript = preload("res://scripts/render/HitSpark.gd")

## `self.flash_timer = 8` / `flash_max = 8` (`_render.py:533-534`).
const FLASH_MAX := 8
## `size = int(20 * intensity)` (`_render.py:547`).
const FLASH_RADIUS := 20
## Warna kilat: `(255,255,200,int(200*i))` luar, `(255,255,255,int(255*i))` inti.
const FLASH_COLOR: Array = [255, 255, 200]
const FLASH_CORE: Array = [255, 255, 255]
## Preset `size` (`_render.py:506-516`): jumlah partikel + rentang spark.
const PRESET_SMALL_COUNT := 8
const PRESET_SMALL_SPARK: Array = [2, 4]
const PRESET_MEDIUM_COUNT := 15
const PRESET_MEDIUM_SPARK: Array = [3, 5]
const PRESET_LARGE_COUNT := 25
const PRESET_LARGE_SPARK: Array = [4, 6]
## Palet tim (`_render.py:502-505`).
const TEAM_BLUE: Array = [[100, 200, 255], [150, 220, 255], [200, 240, 255]]
const TEAM_RED: Array = [[255, 100, 100], [255, 150, 100], [255, 200, 100]]
## `random.uniform(1.5, 4)` (`_render.py:520`) + `randint(20, 35)` (`:529`).
const SPEED_MIN := 1.5
const SPEED_MAX := 4.0
const LIFE_MIN := 20
const LIFE_MAX := 35

var x := 0.0
var y := 0.0
var particles: Array = []
var flash_timer := FLASH_MAX
var flash_max := FLASH_MAX


## `rng` = objek ber-`uniform(a,b)`/`choice(list)`/`randint(a,b)` (harness
## replay memasang skrip nilai dari oracle); null = RNG global produksi.
func _init(px: float = 0.0, py: float = 0.0, team: String = "red",
		size: String = "medium", rng = null) -> void:
	x = px
	y = py
	var colors: Array = TEAM_BLUE if team == "blue" else TEAM_RED
	var count := PRESET_MEDIUM_COUNT
	var spark_range: Array = PRESET_MEDIUM_SPARK
	if size == "small":
		count = PRESET_SMALL_COUNT
		spark_range = PRESET_SMALL_SPARK
	elif size == "large":
		count = PRESET_LARGE_COUNT
		spark_range = PRESET_LARGE_SPARK
	for _i in range(count):
		var angle := HitSparkScript.uniform(rng, 0.0, TAU)
		var speed := HitSparkScript.uniform(rng, SPEED_MIN, SPEED_MAX)
		var vel: Array = [cos(angle) * speed, sin(angle) * speed]
		var col: Array = choose(rng, colors)
		var spark := randint(rng, int(spark_range[0]), int(spark_range[1]))
		particles.append(HitSparkScript.new(px, py, col, vel,
			randint(rng, LIFE_MIN, LIFE_MAX), spark, null))
	flash_timer = FLASH_MAX
	flash_max = FLASH_MAX


## `DeathExplosion.update` (`_render.py:536-542`): SATU frame pygame.
func update() -> void:
	for p in particles:
		(p as HitSpark).update()
	var kept: Array = []
	for p in particles:
		if (p as HitSpark).alive:
			kept.append(p)
	particles = kept
	if flash_timer > 0:
		flash_timer -= 1


## `@property alive` (`_render.py:568-570`).
func is_alive() -> bool:
	return not particles.is_empty() or flash_timer > 0


## Paritas `DeathExplosion.draw` (`_render.py:544-566`): kilat pusat dulu,
## lalu partikel (urutan blit pygame).
func build_ops() -> Array:
	var out: Array = []
	if flash_timer > 0:
		var intensity := float(flash_timer) / float(flash_max)
		var radius := int(float(FLASH_RADIUS) * intensity)
		if radius > 0:
			var cx := float(int(x))
			var cy := float(int(y))
			out.append({"op": "circle", "x": cx, "y": cy, "r": float(radius),
				"color": [int(FLASH_COLOR[0]), int(FLASH_COLOR[1]),
					int(FLASH_COLOR[2]), int(200.0 * intensity)]})
			out.append({"op": "circle", "x": cx, "y": cy,
				"r": float(int(floorf(float(radius) / 2.0))),
				"color": [int(FLASH_CORE[0]), int(FLASH_CORE[1]),
					int(FLASH_CORE[2]), int(255.0 * intensity)]})
	for p in particles:
		out.append_array((p as HitSpark).build_ops())
	return out


## `random.choice` pygame — indeksnya ikut tercatat di fixture.
static func choose(rng, options: Array) -> Array:
	if rng != null:
		return rng.choice(options)
	return options[randi() % options.size()]


## `random.randint` pygame (inklusif kedua ujung).
static func randint(rng, lo: int, hi: int) -> int:
	if rng != null:
		return int(rng.randint(lo, hi))
	return randi_range(lo, hi)
