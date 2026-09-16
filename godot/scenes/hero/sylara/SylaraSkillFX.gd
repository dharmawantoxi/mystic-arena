# SylaraSkillFX.gd — identitas visual per-skill Sylara (v2 rebuild).
#
# `handles_skill_fx() = true` → Hero melewatkan FX skill generik; file ini
# punya SELURUH identitas visual Q/W/E/R. Semua FX memakai VFXManager
# (actor ter-pool, gambar CPU) + beberapa bentuk custom ringan yang
# digambar node ini (ruang LOKAL — ikut flip hero, konsisten).
#
# Hierarki (MASTER FX): PRIMARY 70% / SECONDARY 20% / ACCENT 10%.
# Aturan feel (dipakai barean SylaraCombat):
#   * Q volley & E shackle  → VFXManager.impact tier 1-2 (shake kecil)
#   * R release             → VFXManager.impact tier 3 (hit-stop + shake)
#   * Serangan DASAR        → TIDAK ADA impact FX (kontrak)
class_name SylaraSkillFX
extends Node2D

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

## Fallback target untuk showcase/demo (tanpa hero): koordinat DUNIA.
## Vector2.ZERO = pakai titik default relatif (140, -34) di depan hero.
var demo_target := Vector2.ZERO

## Di-set root (SylaraSkeleton) sebelum notify_drive tiap frame.
var prev_pos := Vector2.ZERO

var _skeleton: Node2D = null
var _hero = null
var _seq_key := ""
var _seq_t := -1.0
var _fired: Dictionary = {}
## FX custom aktif (digambar _draw lokal): {kind, t, dur, data}
var _fx: Array = []

## Durasi visual per skill (dtk) — sinkron VISUAL_DURATION kit
## (q/w=180f, e=150f, r=60f @60fps).
const SKILL_DUR := {"q": 3.0, "w": 3.0, "e": 2.5, "r": 1.0}


func _ready() -> void:
	_skeleton = get_parent()
	resolve_hero()
	if _skeleton != null:
		_skeleton.skill_cast.connect(_on_skill_cast)
		_skeleton.skill_release.connect(_on_skill_release)


## Demo/arena: hero ada beberapa level di atas (Hero/Visual/<rig>).
## Jalan naik sampai menemukan node dengan `hp` + `kit` (maks 5 level).
func resolve_hero() -> void:
	_hero = null
	var n: Node = get_parent()
	for i in 5:
		if n == null:
			break
		if "hp" in n and "kit" in n:
			_hero = n
			break
		n = n.get_parent()


## Dipanggil root tiap physics frame.
func notify_drive(skill: String, pos: Vector2, facing: int,
		delta: float) -> void:
	_advance(delta)
	_update_live_fx()


# ══════════════════════════════════════════════════════════
#  SEQUENCER
# ══════════════════════════════════════════════════════════

func _on_skill_cast(key: String) -> void:
	_seq_key = key
	_seq_t = 0.0
	_fired.clear()
	match key:
		"q":
			_cast_q()
		"w":
			_cast_w()
		"e":
			_cast_e()
		"r":
			_cast_r()


## Edge kit Powershot (charge true→false) = momen release R.
func _on_skill_release(key: String) -> void:
	if key == "r":
		_release_r()


func _advance(delta: float) -> void:
	for i in range(_fx.size() - 1, -1, -1):
		var f: Dictionary = _fx[i]
		f.t = float(f.t) + delta
		if f.t >= float(f.dur):
			_fx.remove_at(i)
	if not _fx.is_empty():
		queue_redraw()
	if _seq_t < 0.0:
		return
	_seq_t += delta
	var dur: float = float(SKILL_DUR.get(_seq_key, 2.0))
	if _seq_t >= dur:
		_seq_key = ""
		_seq_t = -1.0
		_fired.clear()
		return
	_fire_events()


## Satu event = satu spawn (atau satu set kecil). `_vt` menjamin tiap
## event jalan PERSIS SEKALI.
func _vt(id: String, at: float) -> bool:
	if _seq_t < at or _fired.has(id):
		return false
	_fired[id] = true
	return true


func _fire_events() -> void:
	match _seq_key:
		"q":
			for i in 5:
				if _vt("q_v%d" % i, 0.15 + i * 0.42):
					_volley_q()
			if _vt("q_l1", 0.35):
				_leaf_burst(_target_world(), 3, 90.0)
			if _vt("q_l2", 1.05):
				_leaf_burst(_target_world(), 3, 90.0)
			if _vt("q_l3", 1.75):
				_leaf_burst(_target_world(), 3, 90.0)
		"w":
			for i in 4:
				if _vt("w_p%d" % i, 0.30 + i * 0.60):
					VFXManager.ring(_skeleton.global_position + Vector2(0, -4),
						38.0, Pal.WIND.darkened(0.35), 0.0, 0.38, 2.0)
			for i in 3:
				if _vt("w_l%d" % i, 0.50 + i * 0.85):
					_wind_trail()
		"e":
			if _vt("e_hit", 0.30):
				_shackle_land()
			if _vt("e_thorn", 0.45):
				var tgt := _target_world()
				VFXManager.sparks(tgt, randf() * TAU, 5, 120.0, Pal.VINE_DARK,
					0.0, 0.24, 0.5)
			for i in 3:
				if _vt("e_c%d" % i, 0.80 + i * 0.50):
					VFXManager.ring(_target_world(), 13.0, Pal.VINE_DARK,
						0.0, 0.26, 2.0)
			for i in 3:
				if _vt("e_l%d" % i, 0.60 + i * 0.60):
					_leaf_burst(_target_world(), 3, 80.0)
		"r":
			pass  # charge = FX custom (suck/halo); release via edge


# ══════════════════════════════════════════════════════════
#  CAST — satu-shot pembuka per skill
# ══════════════════════════════════════════════════════════

func _cast_q() -> void:
	var nock := _bow_nock_world()
	var tip := _bow_tip_world()
	var tgt := _target_world()
	VFXManager.flash(nock, 10.0, Pal.WIND_LIGHT, 0.0, 0.12)
	VFXManager.ring(nock, 16.0, Pal.WIND, 0.0, 0.35, 2.5)
	var aim := _aim_vec(tip, tgt)
	VFXManager.slash(tip, _aim_rad(aim), 26.0, 1.25, Pal.WIND,
		0.0, 0.28, 0.7, 4.0)
	# Koridor bidik (custom, live-aim) selama durasi skill
	_fx.append({"kind": "corridor", "t": 0.0, "dur": 3.0, "data": {}})


func _cast_w() -> void:
	var feet := _skeleton.global_position + Vector2(0, 20)
	VFXManager.flash(feet, 12.0, Pal.WIND_LIGHT, 0.0, 0.14)
	VFXManager.ring(feet, 34.0, Pal.WIND, 0.0, 0.45, 3.0)
	# Siklon angin mengorbit hero — WALL mode (3 busur berputar, ikut unit)
	VFXManager.wall(_skeleton, Vector2(0, -6), 2.6, 26.0, Pal.WIND)
	VFXManager.glow(feet, 26.0, Pal.WIND_DEEP, 0.05, 0.8)


func _cast_e() -> void:
	var nock := _bow_nock_world()
	VFXManager.flash(nock, 8.0, Pal.VINE_LIGHT, 0.0, 0.12)
	VFXManager.ring(nock, 14.0, Pal.VINE, 0.0, 0.30, 2.5)


func _cast_r() -> void:
	var nock := _bow_nock_world()
	VFXManager.flash(nock, 9.0, Pal.WIND_LIGHT, 0.0, 0.12)
	# Suction: cincin-cincin menyusut ke nock (custom, live)
	_fx.append({"kind": "suck", "t": 0.0, "dur": 0.85, "data": {}})
	# Halo charge di nock (custom)
	_fx.append({"kind": "halo", "t": 0.0, "dur": 0.95, "data": {}})


# ══════════════════════════════════════════════════════════
#  PERISTIWA
# ══════════════════════════════════════════════════════════

func _volley_q() -> void:
	var tip := _bow_tip_world()
	var nock := _bow_nock_world()
	var tgt := _target_world()
	var aim := _aim_vec(tip, tgt)
	var ar := _aim_rad(aim)
	# Panah angin (streak pendek cepat, dua lapis)
	VFXManager.streak(tip, tip + aim * 95.0, Pal.WIND, 0.0, 0.14, 5.0)
	VFXManager.streak(tip + aim * 10.0, tip + aim * 140.0, Pal.WIND_LIGHT,
		0.02, 0.12, 3.0)
	# Impact kuat di target (tier 1 — tanpa freeze)
	VFXManager.impact(tgt, 1, Pal.WIND)
	# Accent daun
	VFXManager.sparks(tgt, ar, 4, 150.0, Pal.LEAF, 0.0, 0.26, 0.5)
	VFXManager.flash(nock, 6.0, Pal.WIND_LIGHT, 0.0, 0.10)


func _shackle_land() -> void:
	var nock := _bow_nock_world()
	var tip := _bow_tip_world()
	var tgt := _target_world()
	var aim := _aim_vec(tip, tgt)
	# Sulur hidup (custom, live-aim ke target) — PRIMARY
	_fx.append({"kind": "vine", "t": 0.0, "dur": 2.2, "data": {}})
	# Impact skill (tier 2 — shake 0.06)
	VFXManager.impact(tgt, 2, Pal.VINE)
	# Cincin constriction + percikan
	VFXManager.ring(tgt, 18.0, Pal.VINE, 0.05, 0.35, 3.0)
	VFXManager.sparks(tgt, _aim_rad(aim), 6, 170.0, Pal.VINE_LIGHT,
		0.0, 0.30, 0.6)
	VFXManager.flash(nock, 7.0, Pal.VINE_LIGHT, 0.0, 0.10)


func _release_r() -> void:
	var tip := _bow_tip_world()
	var tgt := _target_world()
	var aim := _aim_vec(tip, tgt)
	var ar := _aim_rad(aim)
	var perp := Vector2(-aim.y, aim.x)
	# GALE: 5 streak paralel (PRIMARY — dinding angin)
	for i in 5:
		var off := (float(i) - 2.0) * 7.0
		var col: Color = Pal.WIND if i % 2 == 0 else Pal.WIND_LIGHT
		VFXManager.streak(
			tip + aim * 8.0 + perp * off,
			tip + aim * (150.0 + float(i) * 42.0) + perp * off * 1.4,
			col, float(i) * 0.025, 0.20 + float(i) * 0.02,
			6.0 - float(i) * 0.8)
	# Terowongan angin di belakang gale (custom, lokal)
	_fx.append({"kind": "tunnel", "t": 0.0, "dur": 0.22, "data": {}})
	# IMPACT ultimit di target (tier 3: hit-stop + shake bawaan)
	VFXManager.impact(tgt, 3, Pal.WIND)
	# Burst daun (SECONDARY) + kilatan putih (ACCENT)
	VFXManager.sparks(tgt, ar, 8, 240.0, Pal.LEAF, 0.03, 0.40, 0.9)
	VFXManager.flash(tgt, 18.0, Pal.WIND_WHITE, 0.0, 0.16)
	VFXManager.ring(tgt, 34.0, Pal.WIND_LIGHT, 0.04, 0.42, 3.0)


func _leaf_burst(pos: Vector2, n: int, speed: float) -> void:
	VFXManager.sparks(pos, randf() * TAU, n, speed, Pal.LEAF_GOLD,
		0.0, 0.30, 1.0)


func _wind_trail() -> void:
	var vel := _skeleton.global_position - prev_pos
	if vel.length() < 0.05:
		return
	var vn: Vector2 = vel.normalized()
	var perp := Vector2(-vn.y, vn.x)
	for i in 2:
		var p0 := _skeleton.global_position + Vector2(0, -6) \
			- vn * 16.0 + perp * (float(i) - 0.5) * 14.0
		VFXManager.streak(p0, p0 + vn * 34.0 + perp * (float(i) - 0.5) * 6.0,
			Pal.WIND_LIGHT, float(i) * 0.03, 0.20, 3.0)


# ══════════════════════════════════════════════════════════
#  FX CUSTOM — ruang lokal (ikut flip), live-aim
# ══════════════════════════════════════════════════════════

func _update_live_fx() -> void:
	for f in _fx:
		var kind: String = str(f.kind)
		if kind in ["corridor", "vine", "tunnel"]:
			f.data.tgt_local = to_local(_target_world())


func _draw() -> void:
	if _fx.is_empty() or _skeleton == null:
		return
	var nock := _skeleton.get_bow_nock_local() if _skeleton.has_method(
		"get_bow_nock_local") else Vector2(14, 10)
	for f in _fx:
		var kind: String = str(f.kind)
		var t: float = float(f.t)
		var dur: float = float(f.dur)
		var data: Dictionary = f.data
		match kind:
			"corridor":
				_draw_corridor(nock, data, t / dur)
			"vine":
				_draw_vine(nock, data, t)
			"suck":
				_draw_suck(nock, t)
			"halo":
				_draw_halo(nock, t, dur)
			"tunnel":
				_draw_tunnel(nock, data, t / dur)


func _col(c: Color, a: float) -> Color:
	return Color(c.r, c.g, c.b, a)


func _draw_corridor(nock: Vector2, data: Dictionary, k: float) -> void:
	var tgt: Vector2 = data.get("tgt_local", nock + Vector2(300, 0))
	var dist_v: Vector2 = tgt - nock
	if dist_v.length() < 10.0:
		return
	var dir: Vector2 = dist_v.normalized()
	var len := clampf(dist_v.length(), 60.0, 480.0)
	var fade: float = (1.0 - k) * (0.55 + 0.45 * sin(k * PI))
	var end := nock + dir * len
	# Band berlapis (lebar→tipis) — telegraph bidik yang elegan
	draw_line(nock, end, _col(Pal.WIND_DEEP, 0.10 * fade), 26.0)
	draw_line(nock, end, _col(Pal.WIND, 0.14 * fade), 12.0)
	draw_line(nock, end, _col(Pal.WIND_LIGHT, 0.30 * fade), 3.0)
	# Dash berjalan di garis inti
	for i in 4:
		var u0: float = fmod(_t_dir(k, i), 1.0)
		var p0 := nock + dir * (len * (u0 * 0.9))
		draw_line(p0, p0 + dir * 16.0, _col(Pal.WIND_BRIGHT, 0.4 * fade), 2.0)


## Parameter bergerak dash (deterministik per-dash).
func _t_dir(k: float, i: int) -> float:
	return k * 2.5 + float(i) * 0.25


func _draw_vine(nock: Vector2, data: Dictionary, t: float) -> void:
	var tgt: Vector2 = data.get("tgt_local", nock + Vector2(200, 0))
	var segs := 14
	var pts := PackedVector2Array()
	var per := (tgt - nock)
	if per.length() < 4.0:
		return
	var dn: Vector2 = per.normalized()
	var perp := Vector2(-dn.y, dn.x)
	for i in segs + 1:
		var u := float(i) / float(segs)
		var base: Vector2 = nock + per * u
		var amp: float = sin(u * PI) * (6.0 - t * 1.2)
		var off: float = sin(u * PI * 2.2 + t * 4.0) * amp
		pts.append(base + perp * off)
	var u: float = clampf((t - 1.6) / 0.6, 0.0, 1.0)
	var fade := 1.0 - u * u * (3.0 - 2.0 * u)
	# Batang: lapis gelap lalu terang
	for i in range(pts.size() - 1):
		draw_line(pts[i], pts[i + 1], _col(Pal.VINE_DARK, 0.75 * fade), 3.0)
	for i in range(pts.size() - 1):
		draw_line(pts[i], pts[i + 1], _col(Pal.VINE_LIGHT, 0.8 * fade), 1.3)
	# Daun di sepanjang sulur (accent)
	for i in 5:
		var u := 0.15 + float(i) * 0.17
		var li: int = int(u * float(segs))
		if li >= pts.size():
			li = pts.size() - 1
		draw_circle(pts[li] + perp * (2.5 if i % 2 == 0 else -2.5), 1.7,
			_col(Pal.LEAF, 0.85 * fade))


func _draw_suck(nock: Vector2, t: float) -> void:
	for i in 3:
		var prog: float = fmod(t * 1.1 + float(i) / 3.0, 1.0)
		var r: float = lerpf(44.0, 7.0, prog * prog)
		var a: float = (1.0 - prog) * 0.5
		draw_arc(nock, r, 0.0, TAU, 26, _col(Pal.WIND, a), 1.8)
		var r2: float = r * 0.72
		draw_arc(nock, r2, 0.0, TAU, 22, _col(Pal.WIND_LIGHT, a * 0.5), 1.2)


func _draw_halo(nock: Vector2, t: float, dur: float) -> void:
	var k: float = t / maxf(0.001, dur)
	var r: float = 5.0 + t * 11.0
	var a: float = (1.0 - k) * 0.14
	draw_circle(nock, r, _col(Pal.WIND, a))
	draw_arc(nock, r * 1.15, 0.0, TAU, 26, _col(Pal.WIND_LIGHT, a * 2.2), 1.4)


func _draw_tunnel(nock: Vector2, data: Dictionary, k: float) -> void:
	var tgt: Vector2 = data.get("tgt_local", nock + Vector2(300, 0))
	var dist_v: Vector2 = tgt - nock
	if dist_v.length() < 10.0:
		return
	var dir: Vector2 = dist_v.normalized()
	var perp := Vector2(-dir.y, dir.x)
	var len: float = clampf(dist_v.length(), 80.0, 420.0)
	var grow: float = minf(1.0, k / 0.35)
	var fade: float = 1.0 - k
	var offs := [-7.0, 0.0, 7.0]
	var alphas := [0.30, 0.50, 0.30]
	for i in 3:
		var o: float = offs[i]
		var p0 := nock + perp * o
		var p1 := nock + dir * (len * grow) + perp * o * 1.5
		draw_line(p0, p1, _col(Pal.WIND_LIGHT, alphas[i] * fade),
			3.0 - float(i) * 0.6)


# ══════════════════════════════════════════════════════════
#  HELPERS GEOMETRI (posisi global untuk VFXManager)
# ══════════════════════════════════════════════════════════

func _bow_nock_world() -> Vector2:
	if _skeleton != null and _skeleton.has_method("get_bow_nock_global"):
		return _skeleton.get_bow_nock_global()
	return global_position


func _bow_tip_world() -> Vector2:
	if _skeleton != null and _skeleton.has_method("get_bow_tip_global"):
		return _skeleton.get_bow_tip_global()
	return global_position


## Target dunia: hero.target bila ada; fallback demo_target (dunia) atau
## titik default di depan hero.
func _target_world() -> Vector2:
	if _hero != null and is_instance_valid(_hero) and "target" in _hero:
		var t: Node = _hero.get("target")
		if is_instance_valid(t) and t is Node2D:
			return t.global_position
	if demo_target != Vector2.ZERO:
		return demo_target
	return _skeleton.global_position + Vector2(140.0, -34.0)


func _aim_vec(from: Vector2, to: Vector2) -> Vector2:
	var v: Vector2 = to - from
	if v.length() < 1.0:
		return Vector2(400.0, 0.0)
	return v.normalized()


## Sudut VFXActor: 0 = +x, positif = CCW (layar y-ke-bawah).
func _aim_rad(v: Vector2) -> float:
	return atan2(-v.y, v.x)
