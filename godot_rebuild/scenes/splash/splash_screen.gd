extends Control
## Layer 9at: the boot splash (`splash_screen.py` `SplashScreen` +
## `main.py` STATE_SPLASH). Pure numbers live in `splash_timeline.gd`; this
## node bakes the gradient + vignette once into a texture (the source bakes
## it once into an opaque surface), advances the timeline with the frame
## delta clamped to 0.05 s, draws particles / logo / glowing title / hint and
## emits `finished` when the timeline is done. Any tap, click or key skips.

signal finished

const Timeline = preload("res://scripts/ui/splash_timeline.gd")
const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const LOGO_PATH := "res://assets/logo.png"
const WIDTH := 1280
const HEIGHT := 720

var elapsed := 0.0
var skipped := false
var done := false
var particles: Array = []
var logo_texture: Texture2D
var logo_base := Vector2i.ZERO
var background: ImageTexture
var rng := RandomNumberGenerator.new()
var _finished_emitted := false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_ALL
	rng.randomize()
	particles = Timeline.make_particles(float(WIDTH), float(HEIGHT), rng)
	_load_logo()
	background = _bake_background()
	grab_focus()
	queue_redraw()


func _load_logo() -> void:
	# `_load_logo`: the first readable logo file wins; none -> text title.
	if not ResourceLoader.exists(LOGO_PATH):
		return
	var texture := load(LOGO_PATH) as Texture2D
	if texture == null or texture.get_width() <= 0:
		return
	logo_texture = texture
	logo_base = Timeline.logo_scaled_size(Vector2i(texture.get_width(), texture.get_height()))


## Gradient rows + vignette rings composited once (`_bg_cache`). The source
## vignette overwrites (no blending), so only pixels closer than
## `vignette_alpha(d) == 0` to an edge keep the gradient; see the timeline.
func _bake_background() -> ImageTexture:
	var image := Image.create(WIDTH, HEIGHT, false, Image.FORMAT_RGB8)
	var rows: Array = Timeline.gradient_rows(WIDTH, HEIGHT)
	var step := maxi(1, HEIGHT / Timeline.GRADIENT_STEPS)
	var edge := Timeline.VIGNETTE_MAX
	var factors: Array[float] = []
	for d in range(edge + 1):
		factors.append(Timeline.vignette_factor(d))
	for y in range(HEIGHT):
		var dy := mini(y, HEIGHT - 1 - y)
		var base: Color = rows[mini(y / step, rows.size() - 1)]["color"]
		var row_factor := factors[mini(dy, edge)]
		image.fill_rect(Rect2i(0, y, WIDTH, 1), base * row_factor)
		for x in range(mini(edge, WIDTH / 2)):
			var factor := factors[mini(dy, x)]
			if is_equal_approx(factor, row_factor):
				continue
			image.set_pixel(x, y, base * factor)
			image.set_pixel(WIDTH - 1 - x, y, base * factor)
	return ImageTexture.create_from_image(image)


## `main.py`: `dt = min(0.05, frame time)`; `splash.update(dt)`.
func advance(delta: float) -> void:
	if done:
		return
	var dt := minf(Timeline.MAX_DT, delta)
	elapsed += dt
	Timeline.step_particles(particles, elapsed, float(WIDTH), float(HEIGHT), rng)
	if Timeline.is_done(elapsed, skipped):
		done = true
		if not _finished_emitted:
			_finished_emitted = true
			finished.emit()
	queue_redraw()


func _process(delta: float) -> void:
	advance(delta)


func skip() -> void:
	if not done:
		skipped = true


func _gui_input(event: InputEvent) -> void:
	if (
		(event is InputEventScreenTouch and event.pressed)
		or (event is InputEventMouseButton and event.pressed)
	):
		accept_event()
		skip()


func _unhandled_input(event: InputEvent) -> void:
	if (
		(event is InputEventKey and event.pressed)
		or (event is InputEventJoypadButton and event.pressed)
	):
		skip()


func _measure(text: String, font_size: int) -> Vector2i:
	var font := _font_for(font_size)
	var box := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	return Vector2i(int(ceilf(box.x)), int(ceilf(font.get_height(font_size))))


func _font_for(font_size: int) -> Font:
	if font_size >= Timeline.TITLE_BELOW_SIZE:
		return UI_THEME.TITLE_FONT
	if font_size == Timeline.SUB_SIZE:
		return UI_THEME.STRONG_FONT
	return UI_THEME.BODY_FONT


func _draw() -> void:
	var frame: Dictionary = Timeline.layout(elapsed, skipped, WIDTH, HEIGHT, logo_base, _measure)
	if not bool(frame["drawn"]):
		return
	if background != null:
		draw_texture(background, Vector2.ZERO)
	for particle_value in particles:
		var particle: Dictionary = particle_value
		draw_circle(
			Vector2(int(particle["x"]), int(particle["y"])),
			float(Timeline.particle_radius(particle)),
			Timeline.particle_color(particle, elapsed)
		)
	var ta := int(frame["title_alpha"])
	if bool(frame["has_logo"]) and logo_texture != null:
		var radius := int(frame["glow_radius"])
		var center := Vector2(frame["glow_center"])
		for ring_value in Timeline.glow_rings((frame["logo_rect"] as Rect2i).size):
			var ring: Dictionary = ring_value
			var alpha := int(ring["alpha"])
			if alpha > 0:
				draw_circle(center, float(ring["g"]), Color(Timeline.ACCENT, alpha / 255.0))
		draw_texture_rect(
			logo_texture, Rect2(frame["logo_rect"]), false, Color(1, 1, 1, ta / 255.0)
		)
	_draw_glow_title(frame["title_rect"], int(frame["title_size"]), ta)
	_draw_text(frame["sub_rect"], Timeline.SUBTITLE, Timeline.SUB_SIZE, Timeline.TEXT_DIM, ta)
	_draw_text(
		frame["hint_rect"],
		Timeline.HINT,
		Timeline.HINT_SIZE,
		Timeline.TEXT_DIM,
		int(frame["hint_alpha"])
	)
	for line_value in frame["lines"]:
		var line: Dictionary = line_value
		draw_line(Vector2(line["a"]), Vector2(line["b"]), line["color"], 2.0)


func _draw_text(rect: Rect2i, text: String, font_size: int, color: Color, alpha: int) -> void:
	if alpha <= 0:
		return
	var font := _font_for(font_size)
	var pos := Vector2(rect.position.x, rect.position.y + font.get_ascent(font_size))
	draw_string(
		font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(color, alpha / 255.0)
	)


## `_draw_glow_title`: three gold glow layers (24/14/8 px) under the title
## at 28 % alpha - rendered as outlines, the vector adapter of the source's
## blurred copies - then the title itself.
func _draw_glow_title(rect: Rect2i, font_size: int, alpha: int) -> void:
	if alpha <= 0:
		return
	var font := _font_for(font_size)
	var pos := Vector2(rect.position.x, rect.position.y + font.get_ascent(font_size))
	var glow := Color(Timeline.ACCENT, (alpha / 255.0) * 0.28)
	for layer in [24, 14, 8]:
		draw_string_outline(
			font, pos, Timeline.GAME_NAME, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, layer, glow
		)
	draw_string(
		font,
		pos,
		Timeline.GAME_NAME,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		font_size,
		Color(Timeline.TEXT_MAIN, alpha / 255.0)
	)
