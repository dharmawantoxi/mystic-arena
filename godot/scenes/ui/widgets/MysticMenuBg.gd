# MysticMenuBg.gd — latar menu (port MenuBackground pygame):
# gradasi midnight -> bintang kelip deterministik -> siluet kastil ->
# puncak bukit -> garis cakrawala emas -> vignette. Fullscreen Control,
# digambar di _draw dengan waktu berjalan (mati saat visible=false).
extends Control
class_name MysticMenuBg

var _time := 0.0
var _stars: Array = []  # [x(0..1), y(0..1), r, phase]
var _seeded := false


func _init() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	resized.connect(queue_redraw)


func _seed_stars() -> void:
	_seeded = true
	var rng := RandomNumberGenerator.new()
	rng.seed = 1337
	for i in 140:
		_stars.append([rng.randf(), rng.randf(),
			rng.randf_range(0.6, 2.2), rng.randf_range(0.0, TAU)])


func _process(delta: float) -> void:
	_time += delta
	if visible:
		queue_redraw()


func _draw() -> void:
	if not _seeded:
		_seed_stars()
	var w := size.x
	var h := size.y
	if w <= 0.0 or h <= 0.0:
		return
	# Gradasi midnight (draw per 4px untuk hemat draw-call).
	var rows := int(h / 4.0) + 1
	for i in rows:
		var t := float(i) / float(maxi(1, rows - 1))
		var c := Color(lerpf(0.035, 0.05, t), lerpf(0.045, 0.06, t),
			lerpf(0.10, 0.16, t))
		draw_rect(Rect2(0, float(i) * 4.0, w, 4.0), c)
	# Glow radial pusat.
	UiTheme.draw_glow(self, Vector2(w * 0.5, h * 0.42),
		Vector2(w * 0.9, h * 0.85), Color8(64, 72, 140), 44.0)
	# Bintang kelip.
	for st in _stars:
		var sx: float = st[0] * w
		var sy: float = st[1] * h * 0.72
		var tw: float = 0.45 + 0.55 * (0.5 + 0.5 * sin(_time * 1.7 + st[3]))
		var a := tw * 0.75
		draw_circle(Vector2(sx, sy), st[2], Color(0.85, 0.9, 1.0, a))
	# Bulan sabit + halo.
	var moon := Vector2(w * 0.82, h * 0.16)
	UiTheme.draw_glow(self, moon, Vector2(190, 190), Color8(190, 205, 255),
		30.0)
	draw_circle(moon, 34.0, Color8(214, 226, 248))
	draw_circle(moon + Vector2(12, -8), 30.0, Color(0.045, 0.055, 0.12))
	# Siluet kastil.
	var horizon := h * 0.78
	_draw_castle(Vector2(w * 0.5, horizon), w)
	# Puncak bukit berlapis.
	_draw_hills(w, horizon)
	# Garis cakrawala emas.
	draw_line(Vector2(0, horizon), Vector2(w, horizon),
		Color(1.0, 0.8, 0.33, 0.35), 2.0)
	draw_line(Vector2(0, horizon + 3), Vector2(w, horizon + 3),
		Color(1.0, 0.8, 0.33, 0.12), 1.0)
	# Tanah depan gelap.
	draw_rect(Rect2(0, horizon + 4, w, h - horizon),
		Color(0.03, 0.035, 0.08))
	# Vignette (4 tepi).
	var step := 26.0
	for i in 5:
		var a2 := 0.10 * float(5 - i)
		var inset := float(i) * step
		draw_rect(Rect2(inset, inset, w - inset * 2.0, h - inset * 2.0),
			Color(0, 0, 0, a2 * 0.4), false, step)


func _draw_castle(base: Vector2, w: float) -> void:
	var s := w / 1280.0
	var c_far := Color(0.06, 0.07, 0.15)
	var c_mid := Color(0.05, 0.06, 0.125)
	var c_near := Color(0.04, 0.05, 0.10)
	# Menara belakang.
	for tx in [-330.0, -260.0, 260.0, 330.0]:
		var tw := 54.0 * s
		var th := 190.0 * s
		var x := base.x + tx * s - tw * 0.5
		draw_rect(Rect2(x, base.y - th, tw, th), c_far)
		draw_colored_polygon(PackedVector2Array([
			Vector2(x, base.y - th),
			Vector2(x + tw, base.y - th),
			Vector2(x + tw * 0.5, base.y - th - 46 * s)]), c_far)
	# Badan tengah.
	var bw := 560.0 * s
	var bh := 150.0 * s
	draw_rect(Rect2(base.x - bw * 0.5, base.y - bh, bw, bh), c_mid)
	# Merlon.
	var my := base.y - bh
	var mx := base.x - bw * 0.5
	while mx < base.x + bw * 0.5:
		draw_rect(Rect2(mx, my - 14 * s, 16 * s, 14 * s), c_mid)
		mx += 30.0 * s
	# Menara utama + mahkota + jendela emas.
	var cw := 120.0 * s
	var ch := 250.0 * s
	var cx := base.x - cw * 0.5
	draw_rect(Rect2(cx, base.y - ch, cw, ch), c_near)
	draw_colored_polygon(PackedVector2Array([
		Vector2(cx - 10 * s, base.y - ch),
		Vector2(cx + cw + 10 * s, base.y - ch),
		Vector2(base.x, base.y - ch - 70 * s)]), c_near)
	var win := Color(1.0, 0.78, 0.35, 0.85)
	for wy in [0.35, 0.5, 0.65]:
		draw_rect(Rect2(base.x - 6 * s, base.y - ch * wy, 12 * s,
			20 * s), win)
	# Menara samping dekat.
	for tx in [-190.0, 190.0]:
		var tw2 := 70.0 * s
		var th2 := 190.0 * s
		var x2 := base.x + tx * s - tw2 * 0.5
		draw_rect(Rect2(x2, base.y - th2, tw2, th2), c_near)
		draw_colored_polygon(PackedVector2Array([
			Vector2(x2 - 8 * s, base.y - th2),
			Vector2(x2 + tw2 + 8 * s, base.y - th2),
			Vector2(x2 + tw2 * 0.5, base.y - th2 - 52 * s)]), c_near)
	# Gerbang bercahaya.
	var gw := 90.0 * s
	var gh := 70.0 * s
	var gate := Rect2(base.x - gw * 0.5, base.y - gh, gw, gh)
	draw_rect(gate, Color(1.0, 0.75, 0.3, 0.9))
	UiTheme.draw_glow(self, gate.get_center(),
		Vector2(gw * 3.2, gh * 2.6), Color8(255, 190, 90), 40.0)


func _draw_hills(w: float, horizon: float) -> void:
	var back := PackedVector2Array()
	back.append(Vector2(0, horizon))
	var x := 0.0
	var flip := false
	while x <= w:
		back.append(Vector2(x, horizon - (46.0 if flip else 18.0)))
		x += w / 9.0
		flip = not flip
	back.append(Vector2(w, horizon))
	draw_colored_polygon(back, Color(0.045, 0.055, 0.12))
	var front := PackedVector2Array()
	front.append(Vector2(0, horizon + 26))
	x = 0.0
	flip = true
	while x <= w:
		front.append(
			Vector2(x, horizon + 26 - (40.0 if flip else 12.0)))
		x += w / 7.0
		flip = not flip
	front.append(Vector2(w, horizon + 26))
	draw_colored_polygon(front, Color(0.035, 0.045, 0.095))
