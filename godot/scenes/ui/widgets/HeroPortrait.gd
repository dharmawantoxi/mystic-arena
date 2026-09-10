# HeroPortrait.gd — potret hero generatif (port
# HeroPortraits._draw_generic 1:1 — fallback yang dipakai semua kartu).
#
# Mahkota 5 duri emas + wajah lingkaran + mata + badan + permata.
# Ukuran acuan 72x72 (portrait_size kartu meta shop pygame).
extends Control
class_name HeroPortrait

var color_main: Color = Color(0.4, 0.72, 1.0)
var color_dark: Color = Color(0.16, 0.3, 0.55)
var dimmed: bool = false


func _init(p_main: Color = Color(0.4, 0.72, 1.0),
		p_dark: Color = Color(0.16, 0.3, 0.55),
		p_dimmed: bool = false) -> void:
	color_main = p_main
	color_dark = p_dark
	dimmed = p_dimmed
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(72, 72)


func setup(p_main: Color, p_dark: Color, p_dimmed: bool = false) -> void:
	color_main = p_main
	color_dark = p_dark
	dimmed = p_dimmed
	queue_redraw()


func _draw() -> void:
	var main_c := color_main
	var dark_c := color_dark
	if dimmed:
		main_c = Color(main_c.r * 0.45, main_c.g * 0.45, main_c.b * 0.45)
		dark_c = Color(dark_c.r * 0.45, dark_c.g * 0.45, dark_c.b * 0.45)
	# Skala dari ruang acuan 72px ke ukuran aktual.
	var s := minf(size.x, size.y) / 72.0
	var cx := size.x * 0.5
	var cy := size.y * 0.5 + 3.0 * s
	# Mahkota 5 duri.
	for i in range(5):
		var px := cx - 8.0 * s + float(i) * 4.0 * s
		draw_colored_polygon(PackedVector2Array([
			Vector2(px, cy - 16.0 * s),
			Vector2(px + 2.0 * s, cy - 22.0 * s),
			Vector2(px + 4.0 * s, cy - 16.0 * s)]),
			Color(1.0, 200.0 / 255.0, 60.0 / 255.0))
	# Wajah + mata.
	draw_circle(Vector2(cx, cy - 8.0 * s), 10.0 * s, Color.BLACK)
	draw_circle(Vector2(cx, cy - 8.0 * s), 9.0 * s, main_c)
	draw_circle(Vector2(cx - 3.0 * s, cy - 10.0 * s), 1.0 * s, Color.WHITE)
	draw_circle(Vector2(cx + 3.0 * s, cy - 10.0 * s), 1.0 * s, Color.WHITE)
	# Badan + permata.
	UiTheme.draw_rr(self,
		Rect2(cx - 10.0 * s, cy + 2.0 * s, 20.0 * s, 18.0 * s),
		dark_c, 4.0 * s)
	UiTheme.draw_rr(self,
		Rect2(cx - 9.0 * s, cy + 3.0 * s, 18.0 * s, 16.0 * s),
		main_c, 3.0 * s)
	draw_circle(Vector2(cx, cy + 10.0 * s), 3.0 * s,
		Color(1.0, 220.0 / 255.0, 100.0 / 255.0))
	draw_circle(Vector2(cx, cy + 10.0 * s), 1.0 * s, Color.WHITE)
