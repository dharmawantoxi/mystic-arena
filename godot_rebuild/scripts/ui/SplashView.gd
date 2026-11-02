class_name SplashView
extends Control

signal finished

## Native splash driven by the generated splash_screen.py contract. The view
## owns no gameplay state; Main advances it with the same dt clamp as main.py.
var model := SplashModel.new()
var quality: Dictionary = RenderQuality.preset("high")
var done := false
var _finished := false
var _logo_source: Image = null
var _logo_path := ""
var _fonts: Dictionary = {}


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sync_size()
	_load_logo()
	queue_redraw()


func configure(preset: Dictionary) -> void:
	quality = preset
	queue_redraw()


func reset() -> void:
	model = SplashModel.new()
	_finished = false
	done = false
	_sync_size()
	_load_logo()
	queue_redraw()


func skip() -> void:
	model.skip()


func advance(delta: float) -> void:
	if _finished:
		return
	if not model.valid():
		_finish()
		return
	_sync_size()
	model.update(minf(delta, 0.05))
	done = model.done
	queue_redraw()
	if done:
		_finish()


func _finish() -> void:
	if _finished:
		return
	_finished = true
	done = true
	finished.emit()


func _sync_size() -> void:
	model.resize(Vector2i(size))


func _load_logo() -> void:
	_logo_source = null
	_logo_path = ""
	for relative: String in model.config.get("logo_paths", []):
		var path := "res://" + relative
		var image := Image.load_from_file(path)
		if image == null or image.is_empty():
			var texture := load(path) as Texture2D
			if texture != null:
				image = texture.get_image()
		if image != null and not image.is_empty() and image.get_width() > 0:
			_logo_source = image
			_logo_path = path
			return


func _font(style: String) -> Font:
	if _fonts.has(style):
		return _fonts[style]
	var file := str(model.font_files.get(style, ""))
	var font: Font = null
	if not file.is_empty():
		var path := "res://assets/fonts/" + file
		if ResourceLoader.exists(path):
			font = load(path) as Font
	if font == null:
		font = ThemeDB.fallback_font
	_fonts[style] = font
	return font


func _measure(font: Font, text: String, font_size: int) -> Vector2i:
	var width := ceili(font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x)
	return Vector2i(maxi(1, width), maxi(1, font.get_height(font_size)))


func _draw() -> void:
	if not model.valid():
		return
	_sync_size()
	var alpha := model.overall_alpha()
	var background := SplashEffects.background(model, Vector2i(size))
	if background != null:
		draw_texture(background, Vector2.ZERO)
	for particle: Dictionary in model.particles:
		var row := model.particle_draw(particle)
		draw_circle(Vector2(row.pos), float(row.radius), row.color)
	if alpha <= model.f("alpha_epsilon"):
		return
	var has_logo := _logo_source != null
	var title_size := model.font_size("title_below") if has_logo else model.font_size("title")
	var title_font := _font("title")
	var sub_font := _font(str(model.config.get("style_sub", "body_medium")))
	var hint_font := _font(str(model.config.get("style_hint", "body_medium")))
	var title_text := model.text("game_name")
	var sub_text := model.text("tagline")
	var hint_text := model.text("hint_text")
	var geometry := model.layout(
		_logo_source.get_size() if has_logo else Vector2i.ZERO,
		_measure(title_font, title_text, title_size),
		_measure(sub_font, sub_text, model.font_size("sub")),
		_measure(hint_font, hint_text, model.font_size("hint")),
		has_logo
	)
	var ta := model.title_alpha
	if has_logo:
		var logo_geo := model.logo_geometry(_logo_source.get_size())
		var radius: int = logo_geo.glow_radius
		var glow := SplashEffects.logo_glow(model, radius)
		var logo_rect: Rect2i = geometry.logo_rect
		if glow != null:
			draw_texture(glow, Vector2(logo_rect.get_center()) - Vector2(radius, radius))
		var frame := SplashEffects.logo_frame(_logo_source, logo_geo.size)
		if frame != null:
			draw_texture_rect(frame, Rect2(logo_rect), false, Color(1, 1, 1, float(ta) / 255.0))
	var title_rect: Rect2i = geometry.title_rect
	var ascent := title_font.get_ascent(title_size)
	if ta > 0:
		# Source default is Quality.cheap_alpha=True; the pygame benchmark that
		# can disable it is not ported, so do not let a visual preset retune it.
		if model.cheap_alpha_default:
			var fill_alpha := int(float(ta) * model.f("glow_fill"))
			var glow_color := model.color("accent", float(fill_alpha) / 255.0)
			var original := Rect2(title_rect)
			for rect: Rect2i in model.title_glow_rects(title_rect):
				var scaled := Rect2(rect)
				var scale := Vector2(
					scaled.size.x / original.size.x, scaled.size.y / original.size.y
				)
				draw_set_transform(scaled.position, 0.0, scale)
				draw_string(
					title_font,
					Vector2(0, ascent),
					title_text,
					HORIZONTAL_ALIGNMENT_LEFT,
					-1,
					title_size,
					glow_color
				)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		draw_string(
			title_font,
			Vector2(title_rect.position.x, title_rect.position.y + ascent),
			title_text,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1,
			title_size,
			model.color("text_main", float(ta) / 255.0)
		)
		for line: Dictionary in model.accent_lines(title_rect, ta):
			draw_line(line.start, line.end, line.color, float(line.width))
	var sub_rect: Rect2i = geometry.subtitle_rect
	draw_string(
		sub_font,
		Vector2(
			sub_rect.position.x, sub_rect.position.y + sub_font.get_ascent(model.font_size("sub"))
		),
		sub_text,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		model.font_size("sub"),
		model.color("text_dim", float(ta) / 255.0)
	)
	var hint_rect: Rect2i = geometry.hint_rect
	var hint_alpha := int(model.f("hint_alpha") * alpha)
	draw_string(
		hint_font,
		Vector2(
			hint_rect.position.x,
			hint_rect.position.y + hint_font.get_ascent(model.font_size("hint"))
		),
		hint_text,
		HORIZONTAL_ALIGNMENT_LEFT,
		-1,
		model.font_size("hint"),
		model.color("text_dim", float(hint_alpha) / 255.0)
	)
