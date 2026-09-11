# SplashScreen.gd — splashscreen pembuka (port splash_screen.py 1:1).
#
# Logo + judul MYSTIC ARENA + tagline + partikel bintang + hint skip.
# Auto-selesai 3.0 detik, bisa di-skip kapan saja (klik / tombol).
# Main.tscn menumpuknya di atas segalanya saat boot (layer 100), lalu
# memunculkan menu utama setelah signal `finished`.
extends CanvasLayer
class_name SplashScreen

signal finished

const GAME_NAME := "MYSTIC ARENA"
const TAGLINE := "A MOBA TOWER DEFENSE ADVENTURE"
const SPLASH_DURATION := 3.0

const ACCENT := Color("#ffbe3c")
const ACCENT_2 := Color("#c88cff")
const TEXT_MAIN := Color("#f5f0e6")
const TEXT_DIM := Color("#a09baa")

var _elapsed: float = 0.0
var _skipped: bool = false
var _skip_t: float = 0.0
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
	var rng := RandomNumberGenerator.new()
	rng.seed = 777
	var cols := [Color("#ffd278"), Color("#e6a0ff"), Color("#fff5e6"),
		Color("#b4c8ff")]
	for i in range(46):
		_particles.append({
			"x": rng.randf_range(0, 1280),
			"y": rng.randf_range(0, 720),
			"r": rng.randf_range(0.6, 2.4),
			"speed": rng.randf_range(0.08, 0.35),
			"drift": rng.randf_range(-0.12, 0.12),
			"phase": rng.randf_range(0, TAU),
			"c": cols[rng.randi_range(0, 3)],
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
	if not _done and not _skipped:
		_skipped = true
		_skip_t = 0.0


func _process(delta: float) -> void:
	if _done:
		return
	_elapsed += delta
	if _skipped:
		_skip_t += delta
		if _skip_t >= 0.25:
			_finish()
			return
	elif _elapsed >= SPLASH_DURATION:
		_finish()
		return
	# Partikel naik + drift sinusoidal (paritas update()).
	for p in _particles:
		var d: Dictionary = p
		d["y"] = float(d["y"]) - float(d["speed"])
		d["x"] = float(d["x"]) + float(d["drift"]) \
			+ sin(_elapsed * 0.8 + float(d["phase"])) * 0.05
		if float(d["y"]) < -6.0:
			d["y"] = 726.0
			d["x"] = randf_range(0.0, 1280.0)
	if _view != null:
		_view.queue_redraw()


func _finish() -> void:
	_done = true
	finished.emit()
	queue_free()


## Alpha keseluruhan (fade in 0.4s + fade out 0.45s; skip = 0.25s).
func _overall_alpha() -> float:
	var fade_in := minf(1.0, _elapsed / 0.4)
	var fade_out := 1.0
	if _skipped:
		fade_out = maxf(0.0, 1.0 - _skip_t / 0.25)
	else:
		fade_out = clampf((SPLASH_DURATION - _elapsed) / 0.45, 0.0, 1.0)
	return clampf(fade_in * fade_out, 0.0, 1.0)


## Alpha judul (muncul setelah 0.5s, penuh setelah 1.1s).
func _title_alpha() -> float:
	if _elapsed < 0.5:
		return 0.0
	return minf(1.0, (_elapsed - 0.5) / 0.6)


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

	func _draw() -> void:
		if splash == null or size.x <= 0.0:
			return
		var a := splash._overall_alpha()
		if a <= 0.001:
			return
		draw_set_transform(Vector2.ZERO, 0.0,
			Vector2(size.x / 1280.0, size.y / 720.0))
		_draw_bg()
		_draw_particles()
		_draw_content(a)
		_draw_hint(a)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	func _draw_bg() -> void:
		var top := Color("#080812")
		var mid := Color("#161026")
		var bot := Color("#06060e")
		var bands := 48
		for i in range(bands):
			var f := float(i) / float(bands - 1)
			var c := top.lerp(mid, f / 0.55) if f < 0.55 \
				else mid.lerp(bot, (f - 0.55) / 0.45)
			draw_rect(Rect2(0, f * 720.0, 1280.0,
				720.0 / float(bands) + 1.0), c)
		# Vignette (70 bingkai -> pendekatan 35 bingkai ganda).
		for i in range(0, 140, 4):
			var alpha := minf(255.0, 2.2 * float(140 - i)) / 255.0
			draw_rect(Rect2(i, i, 1280 - i * 2, 720 - i * 2),
				Color(0, 0, 0, alpha * 0.5), false, 4.0)

	func _draw_particles() -> void:
		for p in splash._particles:
			var d: Dictionary = p
			var tw := 0.5 + 0.5 * sin(splash._elapsed * 2.5 \
				+ float(d["phase"]))
			var c: Color = d["c"]
			var f := 0.35 + 0.65 * tw
			draw_circle(Vector2(float(d["x"]), float(d["y"])),
				maxf(1.0, float(d["r"])),
				Color(c.r * f, c.g * f, c.b * f))

	func _draw_content(a: float) -> void:
		var ta := splash._title_alpha() * a
		if ta <= 0.001:
			return
		var cx := 640.0
		var base_y := 360.0
		if splash._logo != null:
			var img := splash._logo
			var iw := float(img.get_width())
			var ih := float(img.get_height())
			var sc := minf(340.0 / iw, 320.0 / ih)
			sc = minf(sc, 1.0)
			var w := iw * sc
			var h := ih * sc
			var grow := minf(1.0, splash._elapsed / 0.9)
			var gq := 0.85 + 0.15 * grow
			var ww := w * gq
			var hh := h * gq
			var logo_cy := base_y - 26.0
			# Glow emas di belakang logo.
			var glow_r := maxf(ww, hh) * 0.5 + 30.0
			UiTheme.draw_glow(self,
				Rect2(cx - glow_r, logo_cy - glow_r, glow_r * 2,
					glow_r * 2),
				SplashScreen.ACCENT, 0.35 * ta, 10)
			draw_set_transform(Vector2(cx, logo_cy), 0.0,
				Vector2(sc * gq, sc * gq) \
					* Vector2(size.x / 1280.0, size.y / 720.0))
			draw_texture(img, Vector2(-iw * 0.5, -ih * 0.5),
				Color(1, 1, 1, ta))
			draw_set_transform(Vector2.ZERO, 0.0,
				Vector2(size.x / 1280.0, size.y / 720.0))
			var rect_bottom := logo_cy + hh * 0.5
			_draw_glow_title(SplashScreen.GAME_NAME, cx,
				rect_bottom + 46.0, ta, 66)
			UiTheme.draw_text_centered(self, UiTheme.body_semibold(),
				SplashScreen.TAGLINE, 22, Color(SplashScreen.TEXT_DIM.r,
					SplashScreen.TEXT_DIM.g, SplashScreen.TEXT_DIM.b,
					ta),
				Vector2(cx, rect_bottom + 88.0), false)
		else:
			_draw_glow_title(SplashScreen.GAME_NAME, cx, base_y, ta,
				92)
			UiTheme.draw_text_centered(self, UiTheme.body_semibold(),
				SplashScreen.TAGLINE, 22, Color(SplashScreen.TEXT_DIM.r,
					SplashScreen.TEXT_DIM.g, SplashScreen.TEXT_DIM.b,
					ta),
				Vector2(cx, base_y + 66.0), false)

	func _draw_glow_title(text: String, cx: float, cy: float, ta: float,
			font_size: int) -> void:
		var font := UiTheme.title_font()
		var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT,
			-1, font_size).x
		var th := font.get_height(font_size)
		# Glow emas berlapis di belakang teks.
		UiTheme.draw_glow(self,
			Rect2(cx - tw * 0.5 - 24, cy - th * 0.5 - 14,
				tw + 48, th + 28),
			SplashScreen.ACCENT, 0.28 * ta, 8)
		UiTheme.draw_text_centered(self, font, text, font_size,
			Color(SplashScreen.TEXT_MAIN.r, SplashScreen.TEXT_MAIN.g,
				SplashScreen.TEXT_MAIN.b, ta),
			Vector2(cx, cy), false)
		# Aksen garis kiri-kanan (emas + ungu).
		var gap := tw * 0.5 + 18.0
		for spec in [[-6.0, SplashScreen.ACCENT],
				[6.0, SplashScreen.ACCENT_2]]:
			var off: float = spec[0]
			var col: Color = spec[1]
			var lc := Color(col.r, col.g, col.b, ta * 0.85)
			draw_line(Vector2(cx - gap, cy + off),
				Vector2(cx - gap + 46, cy + off), lc, 2.0)
			draw_line(Vector2(cx + gap, cy + off),
				Vector2(cx + gap - 46, cy + off), lc, 2.0)

	func _draw_hint(a: float) -> void:
		var font := UiTheme.body_medium()
		UiTheme.draw_text_centered(self, font, "Tap anywhere to skip",
			16, Color(SplashScreen.TEXT_DIM.r, SplashScreen.TEXT_DIM.g,
				SplashScreen.TEXT_DIM.b, 140.0 / 255.0 * a),
			Vector2(640, 672), false)
