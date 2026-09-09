# MysticSplash.gd — splashscreen pembuka (port splash_screen.py).
#
# Logo studio (res://assets/logo.png, fallback emblem teks) + grow 0.85->1.0
# + glow radial aksen + judul MYSTIC ARENA + partikel naik (46, ungu/emas,
# deterministik) + "Tap anywhere to skip". Durasi 3.0 dtk (fade-in 0.4,
# fade-out 0.45, skip -> 0.25). Sinyal finished -> Main membuang node ini.
extends CanvasLayer
class_name MysticSplash

signal finished

const DURATION := 3.0
const FADE_IN := 0.4
const FADE_OUT := 0.45
const SKIP_FADE := 0.25

var _time := 0.0
var _fading := false
var _fade := 0.0
var _fade_len := FADE_OUT
var _done := false
var _particles: Array = []  # [x(0..1), y(0..1), speed, size, gold?]
var _root: Control = null
var _logo: TextureRect = null
var _logo_tex: Texture2D = null


func _init() -> void:
	layer = 100


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242
	for i in 46:
		_particles.append([rng.randf(), rng.randf(),
			rng.randf_range(24.0, 70.0), rng.randf_range(1.5, 4.0),
			rng.randf() < 0.35])
	_root = _SplashDraw.new()
	_root.splash = self
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_root)
	_root.gui_input.connect(_on_gui_input)
	if ResourceLoader.exists("res://assets/logo.png"):
		_logo_tex = load("res://assets/logo.png") as Texture2D
		_logo = TextureRect.new()
		_logo.texture = _logo_tex
		_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_logo.set_anchors_preset(Control.PRESET_FULL_RECT)
		_root.add_child(_logo)


func _on_gui_input(event: InputEvent) -> void:
	if _done:
		return
	if event is InputEventMouseButton:
		var b := event as InputEventMouseButton
		if b.pressed and b.button_index == MOUSE_BUTTON_LEFT:
			_skip()
	elif event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		if t.pressed:
			_skip()


func _unhandled_key_input(event: InputEvent) -> void:
	if _done:
		return
	if event is InputEventKey:
		var k := event as InputEventKey
		if k.pressed and not k.echo:
			_skip()


func _skip() -> void:
	if _fading:
		return
	_fading = true
	_fade = 0.0
	_fade_len = SKIP_FADE


func _process(delta: float) -> void:
	if _done:
		return
	_time += delta
	for p in _particles:
		p[1] = p[1] - p[2] * delta / 720.0
		if p[1] < -0.05:
			p[1] = 1.05
			p[0] = fmod(p[0] + 0.37, 1.0)
	var grow := clampf(_time / DURATION, 0.0, 1.0)
	grow = 0.85 + 0.15 * grow
	# Kuantisasi 5% ala pygame (logo tumbuh berjenjang, bukan mulus).
	grow = floor(grow * 20.0) / 20.0
	if _logo != null:
		var vp := get_viewport().get_visible_rect().size
		var side := 340.0 * grow
		_logo.position = Vector2((vp.x - side) * 0.5, 150.0)
		_logo.size = Vector2(side, side)
	var alpha := 1.0
	if _time < FADE_IN:
		alpha = _time / FADE_IN
	if _fading:
		_fade += delta
		alpha = 1.0 - clampf(_fade / _fade_len, 0.0, 1.0)
	elif _time >= DURATION - FADE_OUT and _time < DURATION + 1.0:
		alpha = clampf((DURATION - _time) / FADE_OUT, 0.0, 1.0)
		_fading = _time >= DURATION - FADE_OUT
		_fade = _time - (DURATION - FADE_OUT)
	if _fading and _fade >= _fade_len:
		alpha = 0.0
	_root.modulate.a = clampf(alpha, 0.0, 1.0)
	_root.queue_redraw()
	if alpha <= 0.0 and (_fading or _time >= DURATION):
		_done = true
		finished.emit()


## Lapisan gambar splash: bg + bintang + glow + judul + hint.
class _SplashDraw extends Control:
	var splash: MysticSplash = null

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		if splash == null:
			return
		var vp := size
		if vp.x <= 0.0 or vp.y <= 0.0:
			return
		# Latar gelap + glow pusat.
		draw_rect(Rect2(Vector2.ZERO, vp), UiTheme.BG_DEEP)
		UiTheme.draw_glow(self, Vector2(vp.x * 0.5, vp.y * 0.40),
			Vector2(vp.x * 0.8, vp.y * 0.7), Color8(90, 70, 160), 40.0)
		# Partikel naik.
		for p in splash._particles:
			var pos := Vector2(p[0] * vp.x, p[1] * vp.y)
			var c := UiTheme.GOLD if p[4] else UiTheme.VIOLET
			c.a = 0.7
			draw_circle(pos, p[3], c)
		# Glow di belakang logo.
		var grow := clampf(splash._time / MysticSplash.DURATION, 0.0, 1.0)
		grow = 0.85 + 0.15 * grow
		var side := 340.0 * grow
		var lc := Vector2(vp.x * 0.5, 150.0 + side * 0.5)
		UiTheme.draw_glow(self, lc, Vector2(side * 1.5, side * 1.5),
			UiTheme.GOLD, 30.0)
		# Fallback emblem teks bila logo hilang.
		if splash._logo_tex == null:
			UiTheme.draw_icon(self, "crown", lc, UiTheme.GOLD, 6.0)
		# Judul + subtitle.
		var f := UiTheme.font("title")
		var t := "MYSTIC ARENA"
		var bp := UiTheme.baseline_center(f, t,
			Vector2(vp.x * 0.5, 150.0 + side + 44.0), 54)
		UiTheme.draw_text_outline(self, f, t, 54, UiTheme.GOLD_TEXT, bp,
			Color8(8, 9, 18), 3.0)
		var f2 := UiTheme.font("body_medium")
		var st := UiTheme.letter("A MOBA TOWER DEFENSE ADVENTURE")
		var bp2 := UiTheme.baseline_center(f2, st,
			Vector2(vp.x * 0.5, 150.0 + side + 76.0), 16)
		draw_string(f2, bp2, st, HORIZONTAL_ALIGNMENT_LEFT, -1, 16,
			UiTheme.TEXT_DIM)
		# Hint bawah (kedip lembut).
		var blink := 0.55 + 0.35 * sin(splash._time * 3.0)
		var f3 := UiTheme.font("body")
		var ht := "Tap anywhere to skip"
		var bp3 := UiTheme.baseline_center(f3, ht,
			Vector2(vp.x * 0.5, vp.y - 48.0), 15)
		draw_string(f3, bp3, ht, HORIZONTAL_ALIGNMENT_LEFT, -1, 15,
			Color(0.66, 0.71, 0.84, blink))
