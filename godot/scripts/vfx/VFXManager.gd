# VFXManager.gd — sistem VFX reusable + object pooling (autoload).
#
# Standar proyek (MASTER FX): efek harus POWERFUL / VISIBLE / CLEAN /
# ELEGANT — bukan particle spam. Manager ini menyediakan bentuk-bentuk
# dasar yang dipakai SEMUA efek (hero, skill, impact) sehingga hierarki
# visual konsisten:
#
#   PRIMARY EFFECT (70%)  = slash / ring / wall  — bentuk solid besar
#   SECONDARY FX   (20%)  = sparks terarah        — sedikit, pendek, bertujuan
#   ACCENT FX      (10%)  = flash / glow kecil    — kilatan singkat
#
# Performa Android:
#   * POOLING penuh — tidak ada instantiate()/queue_free() saat gameplay.
#   * Semua actor digambar via _draw() (CPU) — aman GLES/Compatibility,
#     tanpa shader partikel.
#   * Saat pool habis, actor TERTUA dicuri (efek lama pasti hampir selesai);
#     jumlah efek di layar dengan demikian selalu terbatas.
extends Node

const ActorScript = preload("res://scripts/vfx/VFXActor.gd")
const POOL_SIZE := 32

var _actors: Array = []
var _free: Array = []
var _seq := 0


func _ready() -> void:
	for i in POOL_SIZE:
		var a = ActorScript.new()
		a.visible = false
		a.set_process(false)
		add_child(a)
		_actors.append(a)
		_free.append(a)


# ══════════════════════════════════════════════════════════
#  POOL
# ══════════════════════════════════════════════════════════

func release_actor(actor: Node2D) -> void:
	if actor == null:
		return
	if not _free.has(actor):
		_free.append(actor)


func _acquire() -> Object:
	var actor = null
	if not _free.is_empty():
		actor = _free.pop_back()
	else:
		# Pool habis: curi actor aktif paling lama (pasti hampir selesai).
		var oldest_gen := 2147483647
		for a in _actors:
			if a.active and a.generation < oldest_gen:
				oldest_gen = a.generation
				actor = a
		if actor == null:
			actor = _actors[0]
	_seq += 1
	actor.generation = _seq
	actor.delay = 0.0
	actor.t = 0.0
	actor.spark_count = 0
	actor.follow = null
	_host(actor)
	return actor


## Actor efek dunia dipasang di container FX arena (CanvasLayer di atas
## unit) bila ada; demo/scene lain jatuh ke current_scene — sama seperti
## konvensi GameManager.attach_fx.
func _host(actor: Node2D) -> void:
	var host: Node = GameManager.fx_container
	if host == null or not is_instance_valid(host):
		host = get_tree().current_scene
	if host == null:
		host = get_tree().root
	if actor.get_parent() != host:
		if actor.get_parent() != null:
			actor.get_parent().remove_child(actor)
		host.add_child(actor)


# ══════════════════════════════════════════════════════════
#  API PUBLIK — semua posisi GLOBAL
# ══════════════════════════════════════════════════════════

## Cincin ekspansi (impact, AoE). PRIMARY/SECONDARY tergantung radius.
func ring(pos: Vector2, radius_px: float, col: Color, delay := 0.0,
		dur := 0.4, width := 3.0) -> void:
	var a = _acquire()
	a.mode = ActorScript.Mode.RING
	a.global_position = pos
	a.radius = maxf(4.0, radius_px)
	a.color = col
	a.color2 = col.lightened(0.45)
	a.thickness = width
	a.dur = dur
	a.activate()
	a.delay = delay


## Sabit tebasan. `angle` radian (0 = +x, positif = naik/CCW layar).
func slash(pos: Vector2, angle_rad: float, radius_px: float, sweep_rad: float,
		col: Color, delay := 0.0, dur := 0.3, spin_rad := 0.0,
		thickness_px := 6.0) -> void:
	var a = _acquire()
	a.mode = ActorScript.Mode.SLASH
	a.global_position = pos
	a.radius = maxf(6.0, radius_px)
	a.angle = angle_rad
	a.sweep = sweep_rad
	a.spin = spin_rad
	a.thickness = thickness_px
	a.color = col
	a.color2 = col.lightened(0.6)
	a.dur = dur
	a.activate()
	a.delay = delay


## Kilatan singkat (aksen 10%).
func flash(pos: Vector2, size_px: float, col: Color, delay := 0.0,
		dur := 0.14) -> void:
	var a = _acquire()
	a.mode = ActorScript.Mode.FLASH
	a.global_position = pos
	a.size_pt = maxf(2.0, size_px)
	a.color = col
	a.color2 = col.lightened(0.75)
	a.dur = dur
	a.activate()
	a.delay = delay


## Garis dash/streak dari A ke B (dash strike, proyektil cepat).
func streak(a_pos: Vector2, b_pos: Vector2, col: Color, delay := 0.0,
		dur := 0.26, width := 7.0) -> void:
	var a = _acquire()
	a.mode = ActorScript.Mode.STREAK
	a.global_position = a_pos
	a.pt_a = Vector2.ZERO
	a.pt_b = b_pos - a_pos
	a.size_pt = width
	a.color = col
	a.color2 = col.lightened(0.6)
	a.dur = dur
	a.activate()
	a.delay = delay


## Percikan TERARAH: sedikit (<=10), pendek umurnya, ada arah — bukan
## semburan acak memenuhi layar.
func sparks(pos: Vector2, dir_rad: float, count: int, speed: float,
		col: Color, delay := 0.0, life := 0.34, spread_rad := 0.7) -> void:
	var a = _acquire()
	a.mode = ActorScript.Mode.SPARKS
	a.global_position = pos
	a.color = col
	a.color2 = col.lightened(0.7)
	a.dur = life
	var n := clampi(count, 1, ActorScript.MAX_SPARKS)
	a.spark_count = n
	a.spark_pos = PackedVector2Array()
	a.spark_vel = PackedVector2Array()
	for i in n:
		var ang := dir_rad + randf_range(-spread_rad, spread_rad)
		var sp := speed * randf_range(0.55, 1.15)
		a.spark_pos.append(Vector2.ZERO)
		a.spark_vel.append(Vector2(cos(ang), -sin(ang)) * sp)
	a.activate()
	a.delay = delay


## Sisa cahaya lembut (aftermath) — alpha rendah, bukan bloom.
func glow(pos: Vector2, radius_px: float, col: Color, delay := 0.0,
		dur := 0.6) -> void:
	var a = _acquire()
	a.mode = ActorScript.Mode.GLOW
	a.global_position = pos
	a.radius = maxf(6.0, radius_px)
	a.color = col
	a.color2 = col.lightened(0.4)
	a.dur = dur
	a.activate()
	a.delay = delay


## Dinding/aura yang mengikuti unit (Wind Wall Kaizen).
func wall(follow: Node2D, offset: Vector2, duration: float, radius_px: float,
		col: Color) -> Object:
	var a = _acquire()
	a.mode = ActorScript.Mode.WALL
	a.follow = follow
	a.follow_off = offset
	a.global_position = follow.global_position + offset
	a.radius = maxf(8.0, radius_px)
	a.color = col
	a.color2 = col.lightened(0.55)
	a.dur = maxf(0.4, duration)
	a.activate()
	return a


## Impact komposit bertingkat — SATU panggilan menyinkronkan flash + bentuk
## + percikan (+ hit-stop + camera shake untuk tier tinggi).
## tier: 0 = normal hit, 1 = strong, 2 = skill, 3 = ultimate/boss.
func impact(pos: Vector2, tier: int, col: Color) -> void:
	tier = clampi(tier, 0, 3)
	var sizes := [5.0, 8.0, 12.0, 17.0]
	var rings := [0.0, 16.0, 26.0, 42.0]
	var counts := [2, 3, 5, 8]
	flash(pos, sizes[tier], col.lightened(0.35), 0.0, 0.12 + 0.02 * tier)
	if rings[tier] > 0.0:
		ring(pos, rings[tier], col, 0.02, 0.3 + 0.05 * tier, 2.6)
	sparks(pos, randf() * TAU, counts[tier], 120.0 + 40.0 * tier, col,
		0.0, 0.26 + 0.04 * tier, TAU * 0.5)
	if tier >= 3:
		# Ultimate: hit-stop singkat + guncangan kamera proporsional.
		# Durasi dijaga pendek supaya game tidak terasa beku.
		GameManager.request_hit_stop(0.05, 0.05)
		_shake_camera(0.14)
	elif tier == 2:
		_shake_camera(0.06)


func _shake_camera(trauma: float) -> void:
	var tree := get_tree()
	if tree != null:
		tree.call_group("camera", "add_trauma", trauma)
