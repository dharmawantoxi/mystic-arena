# SylaraArrow.gd — proyektil basic attack Sylara (Godot 4.x).
#
# Subclass TowerBullet yang HANYA meng-override _draw(). Seluruh perilaku
# (homing, hit-test, damage, lifetime, wind-wall/evasion guards) diwarisi
# 1:1 dari TowerBullet sehingga paritas gameplay dan DeathDispatch harness
# tidak berubah — yang berbeda hanya gambarnya.
#
# Bahasa visual: panah wind-ranger — shaft ramping, fletching hijau zamrud
# ganda, mata panah kristal perak dengan kilau permata, dan jejak angin PENDEK.
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
	var n := _trail.size()
	for i in n:
		var a: float = 0.12 + 0.18 * float(i + 1) / 3.0
		var r: float = 1.2 + 0.6 * float(i)
		draw_circle(to_local(_trail[i]), r,
			Color(Pal.WIND_LIGHT.r, Pal.WIND_LIGHT.g, Pal.WIND_LIGHT.b, a))

	var tail := -dir * (ARROW_LEN * 0.5)
	var head := dir * (ARROW_LEN * 0.5)

	# ── Shaft ramping halus ──
	var shaft_a := tail + dir * 2.0
	var shaft_b := head - dir * 2.5
	draw_line(shaft_a, shaft_b, Pal.WOOD_DARK, 2.4, true)
	draw_line(shaft_a, shaft_b, Pal.SHAFT, 1.4, true)
	draw_line(shaft_a + perp * 0.4, shaft_b + perp * 0.4, Pal.WOOD_SHINE, 0.8, true)

	# ── Mata panah kristal perak berkilau ──
	var tip := head + dir * 3.2
	var base := head - dir * 2.0
	var head_poly := PackedVector2Array([
		tip, base + perp * 3.0, base - perp * 3.0,
	])
	draw_colored_polygon(head_poly, Pal.HEAD)
	draw_line(tip, base + perp * 3.0, Pal.HEAD_SHINE, 1.0, true)
	draw_line(tip, base - perp * 3.0, Pal.HEAD_SHINE, 1.0, true)
	draw_line(base + perp * 3.0, base - perp * 3.0, Pal.INK_SOFT, 0.8, true)
	draw_circle(tip - dir * 0.6, 1.0, Color.WHITE)

	# ── Fletching zamrud ganda dengan lilitan emas ──
	for side in [-1.0, 1.0]:
		var vane := PackedVector2Array([
			tail + dir * 1.5,
			tail - dir * 2.6 + perp * 3.4 * side,
			tail - dir * 4.2 + perp * 1.2 * side,
		])
		draw_colored_polygon(vane, Pal.FEATHER)
		draw_line(vane[0], vane[1], Pal.FEATHER_DARK, 0.9, true)

	draw_line(tail + dir * 1.6 + perp * 1.2, tail + dir * 1.6 - perp * 1.2,
		Pal.GOLD_LIGHT, 1.2, true)

	# ── Aksen angin bercahaya di sisi shaft ──
	var wisp_a := tail + dir * 3.0 + perp * 2.4
	draw_line(wisp_a, wisp_a + dir * 5.0,
		Color(Pal.WIND_BRIGHT.r, Pal.WIND_BRIGHT.g, Pal.WIND_BRIGHT.b, 0.65), 1.2, true)
