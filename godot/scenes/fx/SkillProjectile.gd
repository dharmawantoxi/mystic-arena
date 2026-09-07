# SkillProjectile.gd — proyektil SKILL visual-only (port _entity.py).
#
# pygame: `_spawn_skill_projectile` (—_entity.py:4509-4530) membuat proyektil
# homing dengan damage = 0 dan is_skill = True; damage skill yang otoritatif
# tetap instan di hero_skills/_bundle.py. Tujuan satu-satunya: skill ranged
# (Sylara R & Vex Q/E) punya visual TERARAH, tanpa menumpuk damage.
#
# Di sini Node2D yang menggambar dirinya sendiri (pola sama dengan
# TowerBullet.gd), tidak perlu .tscn maupun physics body.
#
# Referensi paritas:
#   - spawn      : _entity.py:4509-4530 (_spawn_skill_projectile)
#   - update loop: _entity.py:3827-3943 (homing, age, jarak, snap, impact FX)
#   - batas      : _entity.py:3225-3232 (_HERO_PROJ_MAX=6, umur, jarak)
#   - gambar     : _entity.py:4976-5210 (_draw_projectile per hero)
#   - call site  : _bundle.py:4461 (Sylara R), 4820 (Vex Q), 4924 (Vex E)
extends Node2D

const FPS := 60.0
## Kecepatan pygame 13 px/frame → px/detik (paritas speed=13.0 _entity.py:4509)
const SPEED := 13.0 * FPS
## Umur maksimal 72 frame ≈ 1,2 detik (paritas _HERO_PROJ_MAX_AGE 3229)
const MAX_AGE_SEC := 72.0 / FPS
## Target mati: tidak boleh terbang selamanya — 36 frame ≈ 0,6 detik
## (paritas _HERO_PROJ_DEAD_AGE 3230)
const DEAD_TARGET_AGE_SEC := 36.0 / FPS
## Kalau proyektil sudah menempuh >380 px, hapus (paritas _HERO_PROJ_MAX_DIST)
const MAX_DIST := 380.0
## Ambang "sudah sampai": dist < speed+5 px per frame (paritas 3854)
const ARRIVE_SLACK := 5.0
## Durasi tampil FX benturan (pygame memindahkan tampilan ke FX director
## milik hero; di Godot node ini yang menggambar ledakannya)
const IMPACT_SEC := 0.45

var target: Node2D = null
var source = null              # Hero pemilik (untuk kredit & cap per hero)
var hero_type: String = ""
var team: String = "blue"
var age: float = 0.0           # detik (dipakai cap "drop paling tua")

var _origin := Vector2.ZERO
var _last_pos := Vector2.ZERO
var _angle: float = 0.0
var _hit_applied: bool = false
var _impact_active: bool = false
var _impact_time: float = 0.0
var _impact_color := Color(0.7, 0.9, 0.5)
var _kind: String = "orb"      # "arrow" (Sylara) | "orb" (Vex) | "generic"
var _draw_color := Color("#c8c8c8")


func setup(p_target: Node2D, p_hero_type: String, p_source) -> void:
	target = p_target
	hero_type = p_hero_type
	source = p_source
	if source != null and is_instance_valid(source):
		team = str(source.get("team"))
		var fc = source.get("fill_color")
		if fc != null:
			_draw_color = fc
	match hero_type:
		"sylara":
			_kind = "arrow"
			_impact_color = Color(0.45, 0.9, 0.5)
		"vex":
			_kind = "orb"
			_impact_color = Color(0.78, 0.5, 1.0)
		_:
			_kind = "generic"
			_impact_color = _draw_color


func _ready() -> void:
	add_to_group("skill_projectiles")
	z_index = 400
	z_as_relative = false
	_origin = global_position
	if target != null and is_instance_valid(target):
		_last_pos = target.global_position


func _physics_process(delta: float) -> void:
	# Frame setelah benturan: pygame menghapus proyektil (3943) dan FX
	# benturan hidup di director terpisah. Di Godot node ini beralih ke mode
	# ledakan (ring + partikel) lalu bebas.
	if _hit_applied:
		if _impact_active:
			_impact_time -= delta
			if _impact_time <= 0.0:
				queue_free()
		else:
			queue_free()
		return

	age += delta
	var target_dead := target == null or not is_instance_valid(target) \
		or bool(target.get("is_dead"))
	var tx := _last_pos.x
	var ty := _last_pos.y
	if not target_dead:
		tx = target.global_position.x
		ty = target.global_position.y
		_last_pos = Vector2(tx, ty)

	# Urutan cek = pygame (3845-3861): umur → target mati → jarak tempuh.
	if age > MAX_AGE_SEC:
		queue_free()
		return
	if target_dead and age > DEAD_TARGET_AGE_SEC:
		queue_free()
		return
	if global_position.distance_to(_origin) > MAX_DIST:
		queue_free()
		return

	var to := Vector2(tx, ty) - global_position
	var dist := to.length()
	if dist > 0.01:
		_angle = to.angle()
	if dist < SPEED * delta + ARRIVE_SLACK:
		# Snap ke posisi target: frame terakhir proyektil MENEMPEL
		# (tidak terpotong beberapa px sebelum target) — paritas 3865-3869.
		global_position = Vector2(tx, ty)
		if not _hit_applied:
			_hit_applied = true
			# Impact FX hanya kalau target masih hidup (paritas 3881):
			# target yang mati kena damage instan skill yang sama -> proyektil
			# terbang ke posisi terakhirnya lalu hilang SENYAP.
			if not target_dead:
				_impact()
		return
	global_position += to / dist * SPEED * delta
	queue_redraw()


## FX benturan: burst partikel + ring memancar (padanan
## notify_projectile_impact heroes/sylara_fx.py & vex_fx.py — power 0.75
## karena damage=0, offset y-10 dari modul FX).
func _impact() -> void:
	_impact_active = true
	_impact_time = IMPACT_SEC
	var p := CPUParticles2D.new()
	p.one_shot = true
	p.explosiveness = 1.0
	p.amount = 12
	p.lifetime = 0.32
	p.position = Vector2(0, -10)
	# CPUParticles2D TIDAK punya `process_material` — itu milik GPUParticles2D.
	# Parameter emisinya diset langsung sebagai properti node, dengan tipe 2D
	# (Vector2, bukan Vector3) dan nama `scale_amount_*`, bukan `scale_*`.
	# Salah satu saja -> "Invalid assignment of property ... on a base object
	# of type 'CPUParticles2D'" saat proyektil skill membentur target.
	# CPU dipilih (bukan GPU) supaya burst 12 partikel sekali pakai ini tidak
	# perlu kompilasi shader partikel — aman juga di Android/GLES, sama
	# alasannya dengan partikel cuaca ArenaMap.gd.
	p.direction = Vector2(0, -1)
	p.spread = 180.0
	p.initial_velocity_min = 60.0
	p.initial_velocity_max = 150.0
	p.gravity = Vector2.ZERO
	p.scale_amount_min = 1.0
	p.scale_amount_max = 2.4
	p.color = _impact_color
	add_child(p)
	p.emitting = true
	queue_redraw()


func _draw() -> void:
	if _hit_applied and _impact_active:
		_draw_impact()
		return
	match _kind:
		"arrow":
			_draw_arrow()
		"orb":
			_draw_orb()
		_:
			_draw_generic()


## Panah Sylara — port _draw_arrow_projectile _entity.py:4994-5058.
## Ujung TEPAT di (0,0) = global_position; badan memanjang ke belakang.
func _draw_arrow() -> void:
	var dir := Vector2(cos(_angle), sin(_angle))
	var perp := dir.orthogonal()
	# Trail (motion blur), alpha 150-30i / 255
	for i in range(4):
		var alpha: float = (150.0 - float(i) * 30.0) / 255.0
		draw_circle(-dir * float(i + 1) * 4.0, 2.0,
			Color(110.0 / 255.0, 220.0 / 255.0, 110.0 / 255.0, alpha))
	# Shaft kayu (2 px gelap + 1 px terang)
	var tail := -dir * 11.0
	draw_line(tail, Vector2.ZERO, Color(100.0 / 255.0, 65.0 / 255.0, 30.0 / 255.0), 2.0)
	draw_line(tail, Vector2.ZERO, Color(150.0 / 255.0, 105.0 / 255.0, 55.0 / 255.0), 1.0)
	# Mata panah hijau menyala
	draw_colored_polygon([Vector2.ZERO, -dir * 5.0 + perp * 3.0, -dir * 5.0 - perp * 3.0],
		Color(60.0 / 255.0, 140.0 / 255.0, 60.0 / 255.0))
	draw_colored_polygon([Vector2.ZERO, -dir * 3.0 + perp * 2.0, -dir * 3.0],
		Color(120.0 / 255.0, 220.0 / 255.0, 120.0 / 255.0))
	# Kilau ujung (1 px di pygame -> titik kecil)
	draw_circle(Vector2.ZERO, 0.8, Color(200.0 / 255.0, 255.0 / 255.0, 200.0 / 255.0))
	# Bulu ekor
	for side in [-1.0, 1.0]:
		draw_colored_polygon([tail, tail - dir * 3.0 + perp * 3.0 * side, tail - dir * 4.0],
			Color(80.0 / 255.0, 160.0 / 255.0, 80.0 / 255.0))
	# Glow
	draw_circle(Vector2.ZERO, 6.0, Color(100.0 / 255.0, 220.0 / 255.0, 100.0 / 255.0, 80.0 / 255.0))


## Orb void Vex (kind="skill") — port FALLBACK pygame
## _draw_magic_orb_projectile _entity.py:5116-5170 (pygame normalnya pakai
## heroes/vex_fx.draw_arcane_orb dengan aksen emas untuk kind="skill"; modul
## FX per-hero itu bagian fase visual, bukan runtime skill — fallback dipakai
## supaya proyektil tidak pernah hilang).
func _draw_orb() -> void:
	var dir := Vector2(cos(_angle), sin(_angle))
	# Trail orb bercahaya (radius 3 - i//2, alpha 120-22i)
	for i in range(5):
		var alpha: float = (120.0 - float(i) * 22.0) / 255.0
		draw_circle(-dir * float(i + 1) * 3.0,
			maxf(1.0, 3.0 - floor(float(i) / 2.0)),
			Color(180.0 / 255.0, 100.0 / 255.0, 240.0 / 255.0, alpha))
	# Glow berlapis (alpha naik ke inti: 50, 75, ..., 175)
	for r in range(6, 0, -1):
		var alpha: float = (200.0 - float(r) * 25.0) / 255.0
		draw_circle(Vector2.ZERO, float(r),
			Color(180.0 / 255.0, 100.0 / 255.0, 240.0 / 255.0, alpha))
	# Inti
	draw_circle(Vector2.ZERO, 3.0, Color(220.0 / 255.0, 180.0 / 255.0, 255.0 / 255.0))
	draw_circle(Vector2.ZERO, 1.0, Color.WHITE)


## Generic 200+ hero (fallback _entity.py:5039-5051): lingkaran warna hero
## + inti putih + ekor tipis. Hanya dipakai kalau ada call site baru di luar
## Sylara/Vex — dua hero itu sudah punya drawing khusus di atas.
func _draw_generic() -> void:
	var dir := Vector2(cos(_angle), sin(_angle))
	# r = max(4, radius hero × 0.6), trail = max(2, r//2) — paritas 5039-5047
	var src_r := 16.0
	if source != null and is_instance_valid(source):
		src_r = float(source.get("radius"))
	var r := maxf(4.0, src_r * 0.6)
	draw_line(-dir * r * 2.5, Vector2.ZERO,
		Color(_draw_color.r, _draw_color.g, _draw_color.b, 0.7), maxf(2.0, r * 0.5))
	draw_circle(Vector2.ZERO, r, _draw_color)
	draw_circle(Vector2.ZERO, maxf(2.0, r - 2.0), Color.WHITE)


## Ring memancar saat benturan (padanan partikel impact FX director).
func _draw_impact() -> void:
	var t: float = 1.0 - clampf(_impact_time / IMPACT_SEC, 0.0, 1.0)
	var alpha: float = 0.85 * (1.0 - t)
	draw_arc(Vector2(0, -10), 6.0 + 16.0 * t, 0.0, TAU, 24,
		Color(_impact_color.r, _impact_color.g, _impact_color.b, alpha), 2.5)
	draw_arc(Vector2(0, -10), 3.0 + 8.0 * t, 0.0, TAU, 20,
		Color(1.0, 1.0, 1.0, alpha * 0.7), 1.5)
