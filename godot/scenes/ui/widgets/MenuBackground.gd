# MenuBackground.gd — latar menu MYSTIC ARENA (port _build_main_background
# + _draw_main_background + _draw_portal + _draw_rune_crystal 1:1).
#
# Langit malam mystic, nebula, bintang, bulan besar, glow arcane/emas,
# rune ring, pegunungan siluet, 3 lane bercahaya, 2 portal, kristal rune,
# grid perspektif, vignette, tint ungu — plus kabut parallax 2 lapis dan
# 64 partikel (ember naik + arcane melayang).
#
# Semua angka koordinat = angka pygame (ruang 1280x720, diskala ke ukuran
# Control aktual via draw_set_transform). Waktu berbasis frame @60fps
# (paritas animation_time += 1).
extends Control
class_name MenuBackground

const W := 1280.0
const H := 720.0

var _t: float = 0.0
var _rng := RandomNumberGenerator.new()

# Geometri statis (di-seed sekali — stabil antar frame).
var _nebulae: Array = []
var _stars: Array = []
var _mountains_far: PackedVector2Array = PackedVector2Array()
var _mountains_near: PackedVector2Array = PackedVector2Array()
var _lanes: Array = []
var _lane_glows: Array = [Color("#5f73ff"), Color("#7d55e1"),
	Color("#469bff")]
var _fog_blobs: Array = [[], []]
var _particles: Array = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_static()
	_build_particles()


func _process(delta: float) -> void:
	_t += delta * 60.0
	_update_particles()
	queue_redraw()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		queue_redraw()


func _build_static() -> void:
	_rng.seed = 2026
	# Nebula: 8 blob.
	var neb_cols := [Color("#7846c8"), Color("#3c5ac8"), Color("#c85a3c"),
		Color("#963ca5"), Color("#4678dc")]
	for i in range(8):
		_nebulae.append({
			"x": _rng.randf_range(0, W),
			"y": _rng.randf_range(0, H * 0.55),
			"r": _rng.randi_range(90, 250),
			"c": neb_cols[_rng.randi_range(0, neb_cols.size() - 1)],
		})
	# Bintang: 170.
	var star_cols := [Color("#c8dcff"), Color("#fff0c8"),
		Color("#dcc8ff"), Color("#a0c8ff")]
	for i in range(170):
		var rad := 1
		if _rng.randf() < 0.25:
			rad = 2
		_stars.append({
			"x": _rng.randf_range(0, W),
			"y": _rng.randf_range(0, H * 0.6),
			"r": rad,
			"c": star_cols[_rng.randi_range(0, star_cols.size() - 1)],
			"a": _rng.randi_range(40, 170),
		})
	# Pegunungan 2 lapis.
	_mountains_far = _mountain_poly(7, H * 0.74, 62.0, 46)
	_mountains_near = _mountain_poly(21, H * 0.83, 44.0, 34)
	# 3 lane (kurva Bezier kuadratik, 90 segmen).
	var lane_defs := [
		[Vector2(90, 670), Vector2(520, 430), Vector2(1210, 150)],
		[Vector2(150, 730), Vector2(560, 500), Vector2(1150, 240)],
		[Vector2(40, 560), Vector2(480, 340), Vector2(1180, 60)],
	]
	for ld in lane_defs:
		_lanes.append(_bezier(ld[0], ld[1], ld[2], 90))
	# Kabut 2 lapis (seed 99).
	var frng := RandomNumberGenerator.new()
	frng.seed = 99
	var fw := W + 220.0
	for li in range(2):
		var n_blobs := 9 if li == 0 else 7
		for i in range(n_blobs):
			(_fog_blobs[li] as Array).append({
				"x": frng.randf_range(0, fw),
				"y": frng.randf_range(H * 0.55, H),
				"r": frng.randi_range(60, 160),
			})


func _mountain_poly(seed_val: int, base_y: float, amp: float,
		step: int) -> PackedVector2Array:
	var r2 := RandomNumberGenerator.new()
	r2.seed = seed_val
	var pts := PackedVector2Array([Vector2(0, H)])
	var x := 0.0
	while x <= W:
		pts.append(Vector2(x, base_y - r2.randf_range(amp * 0.4, amp)))
		x += step
	pts.append(Vector2(W, H))
	return pts


func _bezier(p0: Vector2, p1: Vector2, p2: Vector2,
		n: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(n + 1):
		var t := float(i) / float(n)
		var u := 1.0 - t
		pts.append(Vector2(
			u * u * p0.x + 2.0 * u * t * p1.x + t * t * p2.x,
			u * u * p0.y + 2.0 * u * t * p1.y + t * t * p2.y))
	return pts


func _build_particles() -> void:
	var prng := RandomNumberGenerator.new()
	prng.seed = 4242
	var ember_cols := [Color("#ffbe50"), Color("#ffdc78"),
		Color("#ff9632"), Color("#ffeba0")]
	var arcane_cols := [Color("#a082ff"), Color("#78beff"),
		Color("#e6b4ff"), Color("#8cdcff")]
	for i in range(64):
		var is_ember := prng.randf() < 0.55
		if is_ember:
			_particles.append({
				"kind": "ember",
				"x": prng.randf_range(0, W),
				"y": prng.randf_range(H * 0.4, H),
				"vx": prng.randf_range(-0.35, 0.35),
				"vy": prng.randf_range(-0.9, -0.35),
				"s": prng.randi_range(1, 3),
				"c": ember_cols[prng.randi_range(0, 3)],
				"a": prng.randi_range(80, 180),
				"ph": prng.randf_range(0, 6.28),
			})
		else:
			_particles.append({
				"kind": "arcane",
				"x": prng.randf_range(0, W),
				"y": prng.randf_range(0, H),
				"vx": prng.randf_range(-0.2, 0.2),
				"vy": prng.randf_range(-0.35, -0.05),
				"s": prng.randi_range(1, 2),
				"c": arcane_cols[prng.randi_range(0, 3)],
				"a": prng.randi_range(60, 150),
				"ph": prng.randf_range(0, 6.28),
			})


func _update_particles() -> void:
	var step_frames := 1.0 # dipanggil tiap frame visual
	for p in _particles:
		var d: Dictionary = p
		if str(d["kind"]) == "arcane":
			d["x"] = float(d["x"]) + float(d["vx"]) \
				+ sin(float(d["ph"])) * 0.08
			d["ph"] = float(d["ph"]) + 0.01 * step_frames
		else:
			d["x"] = float(d["x"]) + float(d["vx"])
		d["y"] = float(d["y"]) + float(d["vy"]) * step_frames
		if float(d["y"]) < -10.0:
			d["y"] = H + 10.0
			d["x"] = _rng.randf_range(0, W)
		if float(d["x"]) < -10.0:
			d["x"] = W + 10.0
		elif float(d["x"]) > W + 10.0:
			d["x"] = -10.0


func _draw() -> void:
	if size.x <= 0.0 or size.y <= 0.0:
		return
	draw_set_transform(Vector2.ZERO, 0.0,
		Vector2(size.x / W, size.y / H))
	_draw_sky()
	_draw_nebulae()
	_draw_stars()
	_draw_moon()
	_draw_glows()
	_draw_runes()
	draw_colored_polygon(_mountains_far, Color("#0b0d1c"))
	draw_colored_polygon(_mountains_near, Color("#060815"))
	_draw_lanes()
	_draw_portal(Vector2(120, 612), Color("#9682ff"), Color("#5f96ff"))
	_draw_portal(Vector2(1135, 168), Color("#ffcd78"), Color("#ff965a"))
	_draw_crystals()
	_draw_grid()
	_draw_vignette()
	draw_rect(Rect2(0, 0, W, H), Color(0.235, 0.118, 0.431, 12.0 / 255.0))
	_draw_fog()
	_draw_particles()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_sky() -> void:
	# 48 pita (pygame 720 garis — hasil visual identik, 15x lebih murah).
	var bands := 48
	for i in range(bands):
		var t := float(i) / float(bands - 1)
		var r := 6.0 + t * 18.0
		var g := 10.0 + t * 22.0
		var b := 32.0 + t * 50.0
		if t > 0.62:
			var warm := (t - 0.62) / 0.38
			r += 26.0 * warm
			g += 14.0 * warm
		draw_rect(Rect2(0, t * H, W, H / float(bands) + 1.0),
			Color(r / 255.0, g / 255.0, b / 255.0))


func _soft_circles(center: Vector2, max_r: float, color: Color,
		peak: float, step: float) -> void:
	var rad := max_r
	while rad > 0.0:
		var a := peak * (1.0 - rad / max_r)
		if a > 0.004:
			draw_circle(center, rad,
				Color(color.r, color.g, color.b, a))
		rad -= step


func _draw_nebulae() -> void:
	for n in _nebulae:
		var d: Dictionary = n
		_soft_circles(Vector2(float(d["x"]), float(d["y"])),
			float(d["r"]), d["c"] as Color, 7.0 / 255.0, 16.0)


func _draw_stars() -> void:
	for s in _stars:
		var d: Dictionary = s
		var c: Color = d["c"]
		var a := float(d["a"]) / 255.0
		var pos := Vector2(float(d["x"]), float(d["y"]))
		draw_circle(pos, float(d["r"]), Color(c.r, c.g, c.b, a))
		if int(d["r"]) == 2:
			draw_arc(pos, 5.0, 0, TAU, 16,
				Color(c.r, c.g, c.b, 32.0 / 255.0), 1.0)


func _draw_moon() -> void:
	var mx := W * 0.22
	var my := H * 0.16
	var mr := 48.0
	_soft_circles(Vector2(mx, my), mr * 3.0, Color("#e1d2ff"),
		11.0 / 255.0, 8.0)
	draw_circle(Vector2(mx, my), mr, Color("#eee6fa"))
	draw_arc(Vector2(mx, my), mr, 0, TAU, 48, Color("#d2c8ee"), 1.0)
	for crater in [[-14, -12, 9], [12, -8, 7], [0, 14, 10], [-6, 4, 5]]:
		draw_circle(Vector2(mx + crater[0], my + crater[1]), crater[2],
			Color("#cdc3e8"))


func _draw_glows() -> void:
	_soft_circles(Vector2(W * 0.5, 220), 390.0, Color("#7346c8"),
		15.0 / 255.0, 12.0)
	_soft_circles(Vector2(W * 0.5, 650), 330.0, Color("#ffc85a"),
		11.0 / 255.0, 12.0)


func _draw_runes() -> void:
	var c := Vector2(W * 0.5, 218)
	var rc := Color("#af87ff")
	for spec in [[158, 26, 2], [136, 15, 1], [180, 11, 1]]:
		draw_arc(c, spec[0], 0, TAU, 72,
			Color(rc.r, rc.g, rc.b, float(spec[1]) / 255.0),
			float(spec[2]))
	for i in range(12):
		var ang := float(i) * TAU / 12.0
		draw_circle(c + Vector2(cos(ang), sin(ang)) * 158.0, 3.0,
			Color("#cda5ff", 42.0 / 255.0))
	for i in range(4):
		var ang2 := float(i) * TAU / 4.0 + PI / 4.0
		draw_line(c, c + Vector2(cos(ang2), sin(ang2)) * 136.0,
			Color(rc.r, rc.g, rc.b, 26.0 / 255.0), 1.0)


func _draw_lanes() -> void:
	for li in range(_lanes.size()):
		var pts: PackedVector2Array = _lanes[li]
		var glow_c: Color = _lane_glows[li % _lane_glows.size()]
		# Glow luar lebar (3 garis bertumpuk sbg pendekatan alpha).
		draw_polyline(pts, Color(glow_c.r, glow_c.g, glow_c.b,
			26.0 / 255.0), 72.0)
		draw_polyline(pts, Color("#0a0d1c"), 44.0)
		draw_polyline(pts, Color("#101428"), 36.0)
		var i := 0
		while i < pts.size() - 8:
			draw_line(pts[i], pts[i + 6], Color("#3e392e"), 2.0)
			i += 12
		draw_polyline(pts, Color("#5f5c96"), 1.0)


func _draw_portal(p: Vector2, color: Color, color2: Color) -> void:
	_soft_circles(p, 74.0, color, 10.0 / 255.0, 6.0)
	draw_arc(p, 42.0, 0, TAU, 48, color * Color(0.45, 0.45, 0.45), 3.0)
	draw_arc(p, 36.0, 0, TAU, 48, color, 2.0)
	_soft_circles(p, 35.0, color, 9.0 / 255.0, 6.0)
	draw_circle(p, 10.0, color2)
	draw_circle(p, 4.0, Color.WHITE)
	for i in range(6):
		var ang := float(i) * TAU / 6.0
		draw_circle(p + Vector2(cos(ang), sin(ang)) * 30.0, 2.0,
			Color(color.r, color.g, color.b, 200.0 / 255.0))


func _draw_crystals() -> void:
	var cols := [Color("#8caaff"), Color("#b48cff"), Color("#78c8ff")]
	for li in range(_lanes.size()):
		var pts: PackedVector2Array = _lanes[li]
		var col: Color = cols[li % cols.size()]
		for frac in [0.3, 0.55, 0.8]:
			var idx := int(float(pts.size()) * frac)
			var p: Vector2 = pts[idx] + Vector2(0, -46)
			_draw_rune_crystal(p, col)


func _draw_rune_crystal(p: Vector2, color: Color) -> void:
	_soft_circles(p, 26.0, color, 8.0 / 255.0, 6.0)
	var dark := color * Color(0.5, 0.5, 0.5)
	var body := PackedVector2Array([p + Vector2(0, -16),
		p + Vector2(10, -4), p + Vector2(0, 12), p + Vector2(-10, -4)])
	draw_colored_polygon(body, dark)
	draw_polyline(PackedVector2Array([body[0], body[1], body[2], body[3],
		body[0]]), color, 1.0)
	var light := Color(minf(1.0, color.r + 60.0 / 255.0),
		minf(1.0, color.g + 60.0 / 255.0),
		minf(1.0, color.b + 60.0 / 255.0))
	draw_line(p + Vector2(-4, -10), p + Vector2(-2, -2), light, 2.0)
	draw_circle(p + Vector2(0, -2), 2.0, Color.WHITE)


func _draw_grid() -> void:
	for i in range(1, 9):
		var y := 440.0 + float(i) * 40.0
		draw_line(Vector2(0, y), Vector2(W, y),
			Color(1, 1, 1, 9.0 / 255.0), 1.0)
	for i in range(-8, 17):
		var x := W * 0.5 + float(i) * 90.0
		draw_line(Vector2(x, 450), Vector2(W * 0.5 + float(i) * 55.0, H),
			Color(1, 1, 1, 7.0 / 255.0), 1.0)


func _draw_vignette() -> void:
	# 26 bingkai konsentris -> total ~52 alpha di tepi (pendekatan mulus).
	for i in range(26):
		var a := 2.0 / 255.0
		draw_rect(Rect2(i * 2, i * 2, W - i * 4, H - i * 4),
			Color(0.047, 0.035, 0.102, a), false, 2.0)


func _draw_fog() -> void:
	var fw := W + 220.0
	var cols := [Color("#cdcdff"), Color("#b4beeb")]
	var speeds := [0.35, 0.6]
	var alphas := [26.0, 18.0]
	for li in range(2):
		var off := fmod(_t * float(speeds[li]), fw)
		var blobs: Array = _fog_blobs[li]
		var pulse := 5.0 * sin(_t * 0.008 + float(li) * 2.0)
		var layer_a: float = clampf(float(alphas[li]) + pulse, 8.0, 80.0)
		for ox in [-off, fw - off]:
			for b in blobs:
				var d: Dictionary = b
				var center := Vector2(float(d["x"]) + ox, float(d["y"]))
				_soft_circles(center, float(d["r"]),
					cols[li] as Color,
					15.0 / 255.0 * (layer_a / 26.0), 20.0)


func _draw_particles() -> void:
	for p in _particles:
		var d: Dictionary = p
		var s := float(d["s"])
		var c: Color = d["c"]
		var a := float(d["a"]) / 255.0
		if str(d["kind"]) == "ember":
			a *= 0.75 + 0.25 * sin(_t * 0.05 + float(d["ph"]))
		var pos := Vector2(float(d["x"]), float(d["y"]))
		draw_circle(pos, s * 2.0, Color(c.r, c.g, c.b, a * 0.25))
		draw_circle(pos, s, Color(c.r, c.g, c.b, a))
