# ArmorCrest.gd — port `_build_armor_crest` / `_draw_armor_crest`
# `_entity.py:437-526`. Perisai heraldik kecil sebagai indikator shield
# (pengganti gelembung transparan). Dipakai Tower & Nexus overlay.
class_name ArmorCrest
extends Object


## Gambar crest berpusat di `center` (koordinat lokal CanvasItem).
## fill_ratio 0..1 terisi dari BAWAH; bright = regen flash.
static func draw(canvas: CanvasItem, center: Vector2, size: float,
		base: Color, fill_ratio: float, bright: bool = false) -> void:
	if canvas == null or size < 4.0:
		return
	var w := size * 0.82
	var h := size
	var half_w := w * 0.5
	var pts := PackedVector2Array([
		center + Vector2(-half_w, -h * 0.5),
		center + Vector2(half_w, -h * 0.5),
		center + Vector2(half_w, -h * 0.5 + h * 0.55),
		center + Vector2(0.0, h * 0.5),
		center + Vector2(-half_w, -h * 0.5 + h * 0.55),
	])
	var dark := Color(
		maxf(0.0, base.r - 90.0 / 255.0),
		maxf(0.0, base.g - 90.0 / 255.0),
		maxf(0.0, base.b - 90.0 / 255.0),
		235.0 / 255.0)
	var bump := 90.0 if bright else 40.0
	var lite := Color(
		minf(1.0, base.r + bump / 255.0),
		minf(1.0, base.g + bump / 255.0),
		minf(1.0, base.b + bump / 255.0),
		1.0)
	canvas.draw_colored_polygon(pts, dark)
	var ratio := clampf(fill_ratio, 0.0, 1.0)
	if ratio > 0.0:
		var y_cut := center.y + h * 0.5 - h * ratio
		var filled := _clip_below(pts, y_cut)
		if filled.size() >= 3:
			var fill_col := Color(base.r, base.g, base.b, 245.0 / 255.0)
			canvas.draw_colored_polygon(filled, fill_col)
	var cx0 := center.x
	var cy0 := center.y - h * 0.5 + h * 0.42
	var arm := maxf(2.0, size / 6.0)
	var cross := Color(lite.r, lite.g, lite.b, 230.0 / 255.0)
	canvas.draw_line(Vector2(cx0 - arm, cy0), Vector2(cx0 + arm, cy0), cross, 2.0)
	canvas.draw_line(Vector2(cx0, cy0 - arm), Vector2(cx0, cy0 + arm), cross, 2.0)
	canvas.draw_polyline(pts + PackedVector2Array([pts[0]]), lite, 2.0, true)


## Sutherland–Hodgman: sisakan sisi y >= y_cut (bawah layar Godot).
static func _clip_below(pts: PackedVector2Array, y_cut: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	var n := pts.size()
	if n < 3:
		return out
	for i in n:
		var a := pts[i]
		var b := pts[(i + 1) % n]
		var ain := a.y >= y_cut
		var bin := b.y >= y_cut
		if ain:
			out.append(a)
		if ain != bin:
			var dy := b.y - a.y
			var t := 0.0 if is_zero_approx(dy) else (y_cut - a.y) / dy
			out.append(a.lerp(b, t))
	return out
