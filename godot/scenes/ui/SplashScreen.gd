# SplashScreen.gd — splashscreen pembuka (port splash_screen.py 1:1, FASE 38).
#
# Logo + judul MYSTIC ARENA + tagline + partikel bintang + hint skip.
# Auto-selesai SPLASH_DURATION detik, bisa di-skip kapan saja (klik / tombol).
# Main.tscn menumpuknya di atas segalanya saat boot (layer 100), lalu
# memunculkan menu utama setelah signal `finished`.
#
# FASE 38 (godot++): SEMUA angka (timing, fade, alpha judul, gerak partikel,
# gradien+vignette latar, geometri logo, glow judul, garis aksen, hint) datang
# dari SplashBackend (MysticSplash C++ atau SplashModel.gd) — berkas ini hanya
# renderer piksel, pola FASE 36. Dua deviasi port lama DITUTUP di sini karena
# oracle pygame (tools/test_godot_splash_parity.py) membuktikan perilakunya:
#   1. LATAR: loop vignette pygame menjenuh ke alpha 255 (i <= 24) sehingga
#      interior latar HITAM pekat dengan rim gradien 2px — port lama menggambar
#      gradien ungu + vignette tipis (salah). Kini 48 batang gradien + 70
#      bingkai vignette digambar apa adanya dari backend (urutan luar-dalam
#      membuat bingkai terakhir menimpa interior, sama seperti pygame).
#   2. SKIP: pygame mengukur ambang selesai/fade skip dengan elapsed TOTAL
#      (splash_screen.py:151,172) — skip sesudah 0.25 dtk langsung selesai.
#      Port lama memakai timer sejak skip (_skip_t); semantik lama tetap ada
#      di backend sebagai overall_alpha_godot/is_done_godot untuk A/B harness.
extends CanvasLayer
class_name SplashScreen

signal finished

const Backend = preload("res://scripts/ui/SplashBackend.gd")

var _elapsed: float = 0.0
var _skipped: bool = false
var _done: bool = false
var _particles: Array = []
var _logo: Texture2D = null
var _view: Control = null


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	# FASE 24 — routing gamepad membaca STATE_SPLASH lewat grup ini
	# (main_desktop_legacy.py:154-157: tombol pad apa pun = skip splash).
	add_to_group("splash")
	_logo = load("res://assets/logo.png") as Texture2D
	if _logo == null:
		_logo = load("res://assets/icon.png") as Texture2D
	# RNG partikel: pygame memakai RNG global TAK ber-seed (tidak ada stream
	# yang bisa diklaim paritas), jadi Godot memakai seed tetap supaya boot
	# deterministik — deviasi terdokumentasi, dikunci fixture sisi model.
	var rng := RandomNumberGenerator.new()
	rng.seed = 777
	var cols := Backend.particle_colors()
	var ranges := Backend.particle_ranges()
	for i in range(Backend.particle_count()):
		_particles.append({
			"x": rng.randf_range(0, 1280),
			"y": rng.randf_range(0, 720),
			"r": rng.randf_range(float(ranges["r_lo"]),
				float(ranges["r_hi"])),
			"speed": rng.randf_range(float(ranges["speed_lo"]),
				float(ranges["speed_hi"])),
			"drift": rng.randf_range(float(ranges["drift_lo"]),
				float(ranges["drift_hi"])),
			"phase": rng.randf_range(float(ranges["phase_lo"]),
				float(ranges["phase_hi"])),
			"c": cols[rng.randi_range(0, cols.size() - 1)],
		})
	_view = _SplashView.new(self)
	_view.set_anchors_preset(Control.PRESET_FULL_RECT)
	# STOP (bukan IGNORE): selama splash aktif, klik TIDAK boleh tembus ke
	# tombol menu utama yang ada di baliknya — paritas STATE_SPLASH main.py
	# (:461-464) yang tidak pernah meneruskan sentuhan ke menu. Kliknya
	# ditangkap `_SplashView._gui_input` lalu melewati splash.
	_view.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_view)


func _unhandled_input(event: InputEvent) -> void:
	if _done:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			skip()
			get_viewport().set_input_as_handled()
	elif event is InputEventKey:
		var k := event as InputEventKey
		if k.pressed and not k.echo:
			skip()
			get_viewport().set_input_as_handled()


## Paritas splash.is_done() (splash_screen.py) — dipakai routing pad.
func is_done() -> bool:
	return _done


func skip() -> void:
	if not _done:
		_skipped = true


func _process(delta: float) -> void:
	if _done:
		return
	_elapsed += delta
	# Gerakkan partikel (paritas update(): gerak per FRAME, bukan per detik).
	for p in _particles:
		var d: Dictionary = p
		var moved := Backend.particle_advance(float(d["x"]), float(d["y"]),
			float(d["speed"]), float(d["drift"]), float(d["phase"]),
			_elapsed, 720.0, randf_range(0.0, 1280.0))
		d["x"] = moved["x"]
		d["y"] = moved["y"]
	if Backend.is_done(_elapsed, _skipped):
		_finish()
		return
	if _view != null:
		_view.queue_redraw()


func _finish() -> void:
	_done = true
	finished.emit()
	queue_free()


# ── View (semua gambar di satu _draw, ruang 1280x720 diskala) ──

class _SplashView extends Control:
	var splash: SplashScreen

	func _init(s: SplashScreen) -> void:
		splash = s
		# Lihat komentar di SplashScreen._ready: STOP supaya klik tidak
		# tembus ke tombol menu di belakang splash.
		mouse_filter = Control.MOUSE_FILTER_STOP

	func _gui_input(event: InputEvent) -> void:
		# Jalur GUI: klik mouse fisik maupun sentuhan (di-emulasi jadi mouse
		# lewat emulate_mouse_from_touch). Tombol keyboard tetap ditangani
		# `_unhandled_input` milik SplashScreen di luar kelas ini.
		if splash == null or splash._done:
			return
		if event is InputEventMouseButton:
			var mb := event as InputEventMouseButton
			if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
				splash.skip()
				get_viewport().set_input_as_handled()

	func _scale() -> Vector2:
		return Vector2(size.x / 1280.0, size.y / 720.0)

	func _draw() -> void:
		if splash == null or size.x <= 0.0:
			return
		var a := Backend.overall_alpha(splash._elapsed, splash._skipped)
		if not Backend.draw_visible(a):
			return
		draw_set_transform(Vector2.ZERO, 0.0, _scale())
		_draw_bg()
		_draw_particles()
		_draw_content(a)
		_draw_hint(a)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	## Latar: 48 batang gradien + 70 bingkai vignette dari backend (paritas
	## _bg_cache pygame; bingkai terakhir ber-alpha 255 menimpa interior).
	func _draw_bg() -> void:
		for row in Backend.bg_bands(1280, 720):
			var rect: Rect2 = row["rect"]
			var color: Color = row["color"]
			draw_rect(rect, color)
		for row in Backend.vignette_frames(1280, 720):
			var rect: Rect2 = row["rect"]
			var alpha: int = row["alpha"]
			draw_rect(rect, Color(0, 0, 0, float(alpha) / 255.0))

	func _draw_particles() -> void:
		for p in splash._particles:
			var d: Dictionary = p
			var tw := Backend.particle_twinkle(splash._elapsed,
				float(d["phase"]))
			var color: Color = Backend.particle_draw_color(d["c"], tw)
			var pos: Vector2 = Backend.particle_draw_pos(float(d["x"]),
				float(d["y"]))
			draw_circle(pos, float(Backend.particle_draw_radius(
				float(d["r"]))), color)

	func _draw_content(a: float) -> void:
		var ta := Backend.title_alpha_drawn(
			Backend.title_alpha(splash._elapsed), a)
		if ta <= 0:
			return
		var center: Vector2 = Backend.content_center(1280, 720)
		var cx := center.x
		var base_y := center.y
		if splash._logo != null:
			_draw_logo(cx, Backend.logo_center_y(base_y, true), ta)
		else:
			_draw_glow_title(Backend.game_name(), cx, base_y, ta, 92)
			_draw_tagline(cx, base_y
				+ float(Backend.logo_offsets()["sub_text_only"]), ta)

	func _draw_logo(cx: float, logo_cy: float, ta: float) -> void:
		var img := splash._logo
		var base: Vector2 = Backend.logo_base_size(img.get_width(),
			img.get_height())
		var gq := Backend.logo_grow_quant(splash._elapsed)
		var grown: Vector2 = Backend.logo_grow_size(base, gq)
		var ww := int(grown.x)
		var hh := int(grown.y)
		var glow_r := Backend.logo_glow_radius(ww, hh)
		# Cincin glow emas: pygame menggambar disk bertingkat ke surface
		# SRCALPHA (tiap cincin MENIMPA, bukan menumpuk) — di Godot tiap
		# cincin digambar sebagai busur lebar 3px supaya tidak akumulatif.
		for ring in Backend.logo_glow_rings(glow_r):
			var r: int = ring["r"]
			var alpha: int = ring["alpha"]
			if alpha <= 0:
				continue
			draw_arc(Vector2(cx, logo_cy), float(r) - 1.5, 0.0, TAU, 24,
				Color(Backend.accent().r, Backend.accent().g,
					Backend.accent().b, float(alpha) / 255.0),
				3.0)
		var rect := Rect2(cx - float(ww) * 0.5, logo_cy - float(hh) * 0.5,
			float(ww), float(hh))
		draw_texture_rect(img, rect, false, Color(1, 1, 1, float(ta) / 255.0))
		var bottom := rect.position.y + rect.size.y
		var offsets := Backend.logo_offsets()
		_draw_glow_title(Backend.game_name(), cx,
			bottom + float(offsets["title_below"]), ta, 66)
		_draw_tagline(cx, bottom + float(offsets["sub_below"]), ta)

	func _draw_tagline(cx: float, cy: float, ta: float) -> void:
		var dim: Color = Backend.text_dim()
		UiTheme.draw_text_centered(self, UiTheme.body_semibold(),
			Backend.tagline(), 22,
			Color(dim.r, dim.g, dim.b, float(ta) / 255.0),
			Vector2(cx, cy), false)

	func _draw_glow_title(text: String, cx: float, cy: float, ta: float,
			font_size: int) -> void:
		var font := UiTheme.title_font()
		var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT,
			-1, font_size).x
		var th := font.get_height(font_size)
		var text_rect := Rect2(cx - tw * 0.5, cy - th * 0.5, tw, th)
		# Glow emas berlapis: rect permukaan + alpha isi dari backend
		# (piksel glow tetap pendekatan UiTheme.draw_glow — pola FASE 36).
		for layer_row in Backend.title_glow_layers(true):
			var layer: int = layer_row["layer"]
			var spread: int = layer_row["spread"]
			var glow_rect: Rect2 = Backend.title_glow_surface(text_rect,
				layer, spread)
			UiTheme.draw_glow(self, glow_rect, Backend.accent(),
				float(Backend.title_glow_fill(float(ta))) / 255.0, 8)
		var main: Color = Backend.text_main()
		UiTheme.draw_text_centered(self, font, text, font_size,
			Color(main.r, main.g, main.b, float(ta) / 255.0),
			Vector2(cx, cy), false)
		# Aksen garis kiri-kanan (emas + ungu), angka dari backend.
		var gap := float(Backend.accent_gap(int(tw)))
		for spec in Backend.accent_lines(float(ta)):
			var off: float = float(spec["off"])
			var col: Color = spec["color"]
			var width: float = float(spec["width"])
			var length: float = float(spec["len"])
			draw_line(Vector2(cx - gap, cy + off),
				Vector2(cx - gap + length, cy + off), col, width)
			draw_line(Vector2(cx + gap, cy + off),
				Vector2(cx + gap - length, cy + off), col, width)

	func _draw_hint(a: float) -> void:
		var alpha := float(Backend.hint_alpha(a)) / 255.0
		var dim: Color = Backend.text_dim()
		var pos: Vector2 = Backend.hint_pos(1280, 720)
		UiTheme.draw_text_centered(self, UiTheme.body_medium(),
			Backend.hint_text(), 16, Color(dim.r, dim.g, dim.b, alpha),
			pos, false)
