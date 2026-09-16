# SylaraArrow.gd — proyektil basic attack Sylara (Godot 4.x).
#
# Subclass TowerBullet yang HANYA meng-override _draw(). Seluruh perilaku
# (homing, hit-test, damage, lifetime, wind-wall/evasion guards) diwarisi
# 1:1 dari TowerBullet sehingga paritas gameplay dan DeathDispatch harness
# tidak berubah — yang berbeda hanya gambarnya.
#
# Bahasa visual: panah wind-ranger — shaft ramping, fletching hijau zamrud
# ganda, mata panah perak-hijau terang, dan jejak angin PENDEK (3 titik).
# Trail panjang dilarang: battlefield harus tetap terbaca saat banyak
# proyektil beterbangan.
#
# Dipakai lewat hook Hero._shoot_projectile → SylaraSkeleton.
# spawn_attack_projectile() (method opt-in; hero lain tidak tersentuh).
class_name SylaraArrow extends "res://scenes/tower/TowerBullet.gd"

const Pal = preload("res://scenes/hero/sylara/SylaraPalette.gd")

## Panjang total panah (px lokal). Ujung TEPAT di (0,0) = global_position,
## badan memanjang ke belakang — sama seperti _draw_hd_arrow induk.
const ARROW_LEN := 16.0


func _draw() -> void:
	var dir := Vector2.RIGHT
	if target != null and is_instance_valid(target):
		var d: Vector2 = (target as Node2D).global_position - global_position
		if d.length_squared() > 0.01:
			dir = d.normalized()
	var perp := dir.orthogonal()

	# ── Jejak angin pendek: 3 titik dari _trail induk (global → lokal) ──
	# Sama murahnya dengan induk (3 lingkaran), hanya warnanya identitas
	# angin Sylara, bukan warna tim generik.
	var n := _trail.size()
	for i in n:
		var a: float = 0.10 + 0.14 * float(i + 1) / 3.0
		var r: float = 1.1 + 0.5 * float(i)
		draw_circle(to_local(_trail[i]), r,
			Color(Pal.WIND.r, Pal.WIND.g, Pal.WIND.b, a))

	var tail := -dir * (ARROW_LEN * 0.5)
	var head := dir * (ARROW_LEN * 0.5)

	# ── Shaft ramping: outline gelap + inti terang ──
	var shaft_a := tail + dir * 2.0
	var shaft_b := head - dir * 2.5
	draw_line(shaft_a, shaft_b, Pal.WOOD_DARK, 2.6)
	draw_line(shaft_a, shaft_b, Pal.SHAFT, 1.4)
	draw_line(shaft_a + perp * 0.5, shaft_b + perp * 0.5, Pal.WOOD_SHINE, 0.7)

	# ── Mata panah perak-hijau: bentuk solid + tepi terang + glint ──
	var tip := head + dir * 3.2
	var base := head - dir * 2.0
	draw_colored_polygon(PackedVector2Array([
		tip, base + perp * 3.1, base - perp * 3.1,
	]), Pal.HEAD)
	draw_line(tip, base + perp * 3.1, Pal.HEAD_SHINE, 1.0)
	draw_line(tip, base - perp * 3.1, Pal.INK, 0.8)
	draw_circle(tip - dir * 0.6, 0.9, Color.WHITE)

	# ── Fletching zamrud ganda (identitas wind-ranger) ──
	for side in [-1.0, 1.0]:
		var vane := PackedVector2Array([
			tail + dir * 1.5,
			tail - dir * 2.6 + perp * 3.4 * side,
			tail - dir * 4.2 + perp * 1.2 * side,
		])
		draw_colored_polygon(vane, Pal.FEATHER)
		draw_line(vane[0], vane[1], Pal.FEATHER_DARK, 0.9)

	# ── Aksen angin: 1 garis hembusan pendek di sisi shaft ──
	var wisp_a := tail + dir * 3.0 + perp * 2.6
	draw_line(wisp_a, wisp_a + dir * 5.0,
		Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, 0.55), 1.2)
