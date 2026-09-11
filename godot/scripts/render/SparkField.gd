# SparkField.gd — port bagian partikel/ledakan `_render.EffectManager`
# (`_render.py:601-839`): `self.particles`, `self.explosions`, batas
# `MAX_PARTICLES`/`MAX_EXPLOSIONS`, `add_hit_particles`,
# `add_death_explosion`, dan bagian `update()`/`draw()` milik keduanya.
#
# Bagian EffectManager yang LAIN sudah punya rumah sendiri di Godot dan
# TIDAK diulang di sini: floating text = `FloatingTextQueue`/`WorldPopups`,
# combo = `ComboCounter`, wave announcer = `HUD`/`WavePlate`, achievement =
# `AchievementPopup`, screen shake = `GameCamera`. Path preview =
# `scenes/fx/PathPreview.gd` (state-nya milik scene karena jalur lane dibaca
# dari ArenaMap).
#
# Pemilik instance: `GameManager.spark_fx` (satu lapangan global, sama seperti
# satu `EffectManager` pygame). Di-tick `GameManager._process` lewat
# `advance(delta)` (kadens 60 Hz, paritas `EffectManager.update` yang
# dipanggil sekali per `Game.update`); harness memanggil `tick()` per frame.
extends RefCounted
class_name SparkField

const HitSparkScript = preload("res://scripts/render/HitSpark.gd")
const DeathBurstScript = preload("res://scripts/render/DeathBurst.gd")

## `EffectManager.MAX_PARTICLES` (`_render.py:610`).
const MAX_PARTICLES := 500
## `EffectManager.MAX_EXPLOSIONS` (`_render.py:611`).
const MAX_EXPLOSIONS := 80
## Palet percikan pukulan (`_render.py:722-725`) — BEDA dari palet ledakan.
const HIT_BLUE: Array = [[100, 200, 255], [200, 240, 255]]
const HIT_RED: Array = [[255, 150, 100], [255, 200, 150]]
## `random.uniform(1, 2.5)` (`_render.py:729`).
const HIT_SPEED_MIN := 1.0
const HIT_SPEED_MAX := 2.5
## `randint(12, 20)` / `randint(2, 3)` (`_render.py:734-735`).
const HIT_LIFE_MIN := 12
const HIT_LIFE_MAX := 20
const HIT_SIZE_MIN := 2
const HIT_SIZE_MAX := 3
const FPS := 60.0

var particles: Array = []
var explosions: Array = []
## Padanan `Quality.particle_ratio` / `Quality.particles` (`mobile/perf.py:483-508`)
## yang dibaca `add_hit_particles` pygame. Sengaja 1.0/true: lapisan adaptive
## quality belum diport (lihat SYSTEM_PY_COVERAGE.md §3), jadi preset kualitas
## belum memangkas partikel di Godot. Knob-nya ada supaya port perf nanti tidak
## perlu menyentuh berkas ini.
var particle_ratio := 1.0
var particles_enabled := true
## RNG terkontrol untuk harness (lihat DeathBurst._init); null = RNG global.
var rng = null
var _accum := 0.0


func reset() -> void:
	particles.clear()
	explosions.clear()
	_accum = 0.0


## Paritas `EffectManager.add_hit_particles` (`_render.py:712-741`).
## `count` pygame per situs panggilan: minion 4 (`_entity.py:5842`),
## boss 6 (`base_boss.py:6057`), castle 10 (`_entity.py:1816`),
## chain item 6 (`hero_items.py:2737`).
func add_hit_particles(px: float, py: float, team: String = "red",
		count: int = 5) -> void:
	if not particles_enabled:
		return
	var n := maxi(0, _py_round(float(count) * particle_ratio))
	if n <= 0:
		return
	var colors: Array = HIT_BLUE if team == "blue" else HIT_RED
	for _i in range(n):
		var angle := HitSparkScript.uniform(rng, 0.0, TAU)
		var speed := HitSparkScript.uniform(rng, HIT_SPEED_MIN, HIT_SPEED_MAX)
		var vel: Array = [cos(angle) * speed, sin(angle) * speed]
		var col: Array = DeathBurstScript.choose(rng, colors)
		particles.append(HitSparkScript.new(px, py, col, vel,
			DeathBurstScript.randint(rng, HIT_LIFE_MIN, HIT_LIFE_MAX),
			DeathBurstScript.randint(rng, HIT_SIZE_MIN, HIT_SIZE_MAX), null))
	if particles.size() > MAX_PARTICLES:
		# `del self.particles[0:len-MAX]` — buang yang TERTUA sekaligus.
		for _drop in range(particles.size() - MAX_PARTICLES):
			particles.pop_front()


## Paritas `EffectManager.add_death_explosion` (`_render.py:743-747`).
func add_death_explosion(px: float, py: float, team: String = "red",
		size: String = "medium") -> void:
	explosions.append(DeathBurstScript.new(px, py, team, size, rng))
	if explosions.size() > MAX_EXPLOSIONS:
		explosions.pop_front()


## Bagian partikel/ledakan dari `EffectManager.update` (`_render.py:766-786`).
func tick() -> void:
	for p in particles:
		(p as HitSpark).update()
	var kept: Array = []
	for p in particles:
		if (p as HitSpark).alive:
			kept.append(p)
	particles = kept
	for e in explosions:
		(e as DeathBurst).update()
	var live: Array = []
	for e in explosions:
		if (e as DeathBurst).is_alive():
			live.append(e)
	explosions = live


## Akumulator 60 Hz (pola yang sama dengan `GameManager._tick_combo`), supaya
## kadens frame pygame tetap tepat di refresh rate berapa pun.
func advance(delta: float) -> void:
	_accum += delta
	while _accum >= 1.0 / FPS:
		_accum -= 1.0 / FPS
		tick()


## Urutan gambar `EffectManager.draw` (`_render.py:788-796`): ledakan dulu,
## lalu percikan. (path_preview lebih dulu lagi — milik PathPreview.gd;
## floating text belakangan — milik WorldPopups.gd.)
func build_ops() -> Array:
	var out: Array = []
	for e in explosions:
		out.append_array((e as DeathBurst).build_ops())
	for p in particles:
		out.append_array((p as HitSpark).build_ops())
	return out


## Python `round()` = setengah-ke-genap (banker's rounding), bukan
## setengah-menjauh seperti `roundf` Godot. Dipakai supaya pemangkasan
## `count * particle_ratio` tetap identik kalau rasio != 1.0 suatu hari.
static func _py_round(value: float) -> int:
	var low := floorf(value)
	var diff := value - low
	if diff > 0.5:
		return int(low) + 1
	if diff < 0.5:
		return int(low)
	var base := int(low)
	return base if base % 2 == 0 else base + 1
