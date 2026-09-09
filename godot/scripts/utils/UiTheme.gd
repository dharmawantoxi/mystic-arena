# UiTheme.gd — port 1:1 ui_theme.py (design system Mystic Arena) ke Godot.
#
# Satu sumber kebenaran tampilan: palet, font (Cinzel judul + Barlow body),
# letter-spacing, ellipsis, gradasi vertikal + sudut membulat, glow radial,
# bayangan, ikon vektor, dan tabel warna pill. Widget (MysticPanel,
# MysticButton, MysticPill, ...) memakai helper di sini sehingga tampilannya
# identik dengan pygame tanpa duplikasi rumus.
#
# Catatan port:
#  * _vgrad -> draw_vgrad(): garis per-baris dengan matematika chord sudut
#    yang sama dengan mask BLEND_RGBA_MULT pygame (hasil piksel setara).
#  * _radial -> radial_texture(): GradientTexture2D radial GPU (bukan loop
#    per-piksel) — jauh lebih murah, tampilan sama.
#  * gradient_text/outline_text -> MysticTitle + label_gradient.gdshader
#    (gradasi per-glyph lewat UV) + 8 Label outline susun (9 blit pygame).
extends RefCounted
class_name UiTheme

# ═══════════════════════════════════════════════════════════
# PALET (dark-fantasy: midnight + gold + aksen team) — ui_theme.py
# ═══════════════════════════════════════════════════════════
const BG_DEEP := Color8(9, 12, 26)
const PANEL_TOP := Color8(30, 37, 66)
const PANEL_BOTTOM := Color8(17, 21, 40)
const PANEL_FILL := Color8(21, 26, 48)

const GOLD := Color8(255, 205, 85)
const GOLD_BRIGHT := Color8(255, 233, 158)
const GOLD_DEEP := Color8(158, 116, 40)
const GOLD_TEXT := Color8(255, 220, 110)
const EDGE_GOLD := Color8(176, 144, 82)
const EDGE_GOLD_DIM := Color8(104, 92, 66)

const CYAN := Color8(110, 195, 255)
const CYAN_SOFT := Color8(165, 220, 255)
const VIOLET := Color8(176, 138, 255)
const ORANGE := Color8(255, 168, 96)
const GREEN := Color8(112, 226, 132)
const GREEN_DEEP := Color8(34, 116, 58)
const RED := Color8(255, 108, 108)
const RED_DEEP := Color8(132, 44, 44)
const SLATE := Color8(148, 158, 188)

const TEXT_WHITE := Color8(240, 244, 255)
const TEXT_BODY := Color8(198, 207, 230)
const TEXT_DIM := Color8(132, 142, 170)
const TEXT_FAINT := Color8(96, 106, 136)

const LOCKED_BG_TOP := Color8(30, 28, 40)
const LOCKED_BG_BOTTOM := Color8(20, 19, 29)
const LOCKED_EDGE := Color8(84, 86, 110)
const DONE_BG_TOP := Color8(26, 44, 36)
const DONE_BG_BOTTOM := Color8(17, 30, 24)
const DONE_EDGE := Color8(86, 178, 112)
const OPEN_BG_TOP := Color8(28, 38, 64)
const OPEN_BG_BOTTOM := Color8(18, 24, 44)
const OPEN_EDGE := Color8(96, 152, 214)

const SHADOW_BLACK := Color(0, 0, 0, 1)

# Ukuran viewport kanonik (SCREEN_WIDTH/HEIGHT pygame).
const SCREEN_W := 1280.0
const SCREEN_H := 720.0

static var _fonts: Dictionary = {}
static var _radial_cache: Dictionary = {}
static var _knob_cache: Dictionary = {}
static var _grad_shader: Shader = null


# ═══════════════════════════════════════════════════════════
# FONT (Cinzel judul, Barlow body) — _render.get_font/title_font
# ═══════════════════════════════════════════════════════════

## style: "title" | "body" | "body_medium" | "body_semibold" | "body_bold".
static func font(style: String = "body") -> Font:
	if _fonts.has(style):
		return _fonts[style]
	var path := "res://assets/fonts/Barlow-Regular.ttf"
	match style:
		"title":
			path = "res://assets/fonts/Cinzel.ttf"
		"body_medium":
			path = "res://assets/fonts/Barlow-Medium.ttf"
		"body_semibold":
			path = "res://assets/fonts/Barlow-SemiBold.ttf"
		"body_bold":
			path = "res://assets/fonts/Barlow-Bold.ttf"
	var f: Font = null
	if ResourceLoader.exists(path):
		f = load(path) as Font
	if f == null:
		f = ThemeDB.fallback_font
	_fonts[style] = f
	return f


static func gradient_shader() -> Shader:
	if _grad_shader == null:
		_grad_shader = load(
			"res://assets/shaders/label_gradient.gdshader") as Shader
	return _grad_shader


## Terapkan font + ukuran + warna ke Label (helper satu baris).
static func style_label(l: Label, size: int, style: String, color: Color,
		shadow: bool = false, shadow_offset: Vector2 = Vector2(2, 2)) -> Label:
	l.add_theme_font_override("font", UiTheme.font(style))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if shadow:
		l.add_theme_color_override("font_shadow_color", Color(0.02, 0.02, 0.05, 0.9))
		l.add_theme_constant_override("shadow_offset_x", int(shadow_offset.x))
		l.add_theme_constant_override("shadow_offset_y", int(shadow_offset.y))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


# ═══════════════════════════════════════════════════════════
# TEKS — letter() + fit_ellipsis()
# ═══════════════════════════════════════════════════════════

## Letter-spacing manual (ui_theme.letter).
static func letter(text: String, gap: String = " ") -> String:
	var out := PackedStringArray()
	for i in text.length():
		out.append(text.substr(i, 1))
	return gap.join(out)


## Truncate dengan elipsis (ui_theme.fit_ellipsis).
static func fit_ellipsis(f: Font, text: String, max_w: float,
		font_size: int) -> String:
	var s := str(text)
	if f.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x <= max_w:
		return s
	var ell := "…"
	var t := s
	while t.length() > 1:
		var cand := t.substr(0, t.length() - 1)
		if f.get_string_size(cand + ell, HORIZONTAL_ALIGNMENT_LEFT, -1,
				font_size).x <= max_w:
			return cand + ell
		t = cand
	return ell


## Posisi baseline draw_string dari titik tengah (draw_string memakai baseline).
static func baseline_center(f: Font, text: String, center: Vector2,
		font_size: int,
		align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT) -> Vector2:
	var sz := f.get_string_size(text, align, -1, font_size)
	var cy := center.y + (f.get_ascent(font_size) - f.get_descent(font_size)) * 0.5
	return Vector2(center.x - sz.x * 0.5, cy)


## Posisi baseline draw_string dari pojok kiri-atas.
static func baseline_topleft(f: Font, topleft: Vector2,
		font_size: int) -> Vector2:
	return Vector2(topleft.x, topleft.y + f.get_ascent(font_size))


## Teks dengan bayangan gelap 1 arah (ui_theme.draw_text).
static func draw_text_shadow(cv: CanvasItem, f: Font, text: String,
		font_size: int, color: Color, pos_baseline: Vector2,
		shadow_color: Color = Color(0.02, 0.02, 0.05, 1.0),
		offset: Vector2 = Vector2(2, 2)) -> void:
	cv.draw_string(f, pos_baseline + offset, text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, shadow_color)
	cv.draw_string(f, pos_baseline, text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)


## Teks outline 8 arah + badan solid (varian outline_text tanpa gradasi).
static func draw_text_outline(cv: CanvasItem, f: Font, text: String,
		font_size: int, color: Color, pos_baseline: Vector2,
		outline_color: Color = Color(0.03, 0.035, 0.07, 1.0),
		width: float = 2.0) -> void:
	for off in [Vector2(-width, 0), Vector2(width, 0), Vector2(0, -width),
			Vector2(0, width), Vector2(-width, -width), Vector2(width, width),
			Vector2(-width, width), Vector2(width, -width)]:
		cv.draw_string(f, pos_baseline + off, text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, outline_color)
	cv.draw_string(f, pos_baseline, text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)


# ═══════════════════════════════════════════════════════════
# GRADASI + GLOW + BAYANGAN
# ═══════════════════════════════════════════════════════════

## Gradasi vertikal dengan sudut membulat (port _vgrad + mask radius).
## Chord sudut dihitung analitik — setara mask BLEND_RGBA_MULT pygame.
static func draw_vgrad(cv: CanvasItem, rect: Rect2, top: Color,
		bottom: Color, radius: float = 0.0) -> void:
	var x0 := rect.position.x
	var y0 := rect.position.y
	var w := rect.size.x
	var h := rect.size.y
	if w <= 0.0 or h <= 0.0:
		return
	var r := clampf(radius, 0.0, minf(w, h) * 0.5)
	var rows := int(ceil(h))
	for i in rows:
		var t := float(i) / float(maxi(1, rows - 1))
		var c := Color(
			lerpf(top.r, bottom.r, t),
			lerpf(top.g, bottom.g, t),
			lerpf(top.b, bottom.b, t),
			lerpf(top.a, bottom.a, t))
		var inset := 0.0
		if r > 0.0:
			var yy := float(i) + 0.5
			if yy < r:
				var d := r - yy
				inset = r - sqrt(maxf(0.0, r * r - d * d))
			elif yy > h - r:
				var d2 := yy - (h - r)
				inset = r - sqrt(maxf(0.0, r * r - d2 * d2))
		cv.draw_line(Vector2(x0 + inset, y0 + float(i) + 0.5),
			Vector2(x0 + w - inset, y0 + float(i) + 0.5), c, 1.0)


## Glow radial elips (port _radial — versi GPU, di-cache per ukuran/warna).
static func radial_texture(w: float, h: float, color: Color,
		alpha: float) -> GradientTexture2D:
	var wi := maxi(8, int(w))
	var hi := maxi(8, int(h))
	var a := clampi(int(alpha) / 8 * 8, 4, 120)
	var key := "%dx%d_%s_%d" % [wi, hi, color.to_html(), a]
	if _radial_cache.has(key):
		return _radial_cache[key]
	var grad := Gradient.new()
	grad.offsets = PackedFloat32Array([0.0, 1.0])
	var c := Color(color.r, color.g, color.b, float(a) / 255.0)
	grad.colors = PackedColorArray([c, Color(c.r, c.g, c.b, 0.0)])
	# Peluruhan kuadrat ala pygame ((1-d)^2): titik tengah tambahan.
	grad.add_point(0.5, Color(c.r, c.g, c.b, c.a * 0.25))
	var tex := GradientTexture2D.new()
	tex.gradient = grad
	tex.width = wi
	tex.height = hi
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	_radial_cache[key] = tex
	return tex


## Gambar glow radial langsung ke canvas (pusat center, ukuran size).
static func draw_glow(cv: CanvasItem, center: Vector2, size: Vector2,
		color: Color, alpha: float) -> void:
	var tex := radial_texture(size.x, size.y, color, alpha)
	cv.draw_texture(tex, center - size * 0.5)


## StyleBox bayangan lembut (dipakai lewat draw_style_box sebelum gradasi).
static func shadow_style(radius: float,
		alpha: float = 0.45, size: float = 10.0) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.shadow_color = Color(0, 0, 0, alpha)
	sb.shadow_size = int(size)
	sb.shadow_offset = Vector2(2, 3)
	sb.set_corner_radius_all(int(radius))
	return sb


## StyleBox border-saja bersudut (draw_center=false).
static func border_style(color: Color, width: float,
		radius: float) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.draw_center = false
	sb.border_color = color
	sb.set_border_width_all(int(width))
	sb.set_corner_radius_all(int(radius))
	sb.anti_aliasing = true
	return sb


## Tanda sudut emas — identitas visual Mystic Arena (corner_ticks).
static func corner_ticks(cv: CanvasItem, rect: Rect2, color: Color,
		length: float = 11.0, width: float = 2.0,
		inset: float = 2.0) -> void:
	var l := rect.position + Vector2(inset, inset)
	var rb := rect.end - Vector2(inset, inset)
	var corners := [
		[l, Vector2(1, 0), Vector2(0, 1)],
		[Vector2(rb.x, l.y), Vector2(-1, 0), Vector2(0, 1)],
		[rb, Vector2(-1, 0), Vector2(0, -1)],
		[Vector2(l.x, rb.y), Vector2(1, 0), Vector2(0, -1)],
	]
	for cn in corners:
		var p: Vector2 = cn[0]
		var dx: Vector2 = cn[1]
		var dy: Vector2 = cn[2]
		cv.draw_line(p, p + dx * length, color, width)
		cv.draw_line(p, p + dy * length, color, width)


## Lingkaran outline (bantuan; draw_arc penuh).
static func draw_ring(cv: CanvasItem, center: Vector2, radius: float,
		color: Color, width: float = 2.0) -> void:
	if radius > 0.5:
		cv.draw_arc(center, radius, 0.0, TAU,
			maxi(12, int(radius * 2.0)), color, width, true)


# ═══════════════════════════════════════════════════════════
# TABEL WARNA PILL (ui_theme.pill kinds)
# ═══════════════════════════════════════════════════════════

## kind -> [top, bottom, edge, text].
static func pill_colors(kind: String) -> Array:
	match kind:
		"gold":
			return [Color8(86, 66, 22), Color8(52, 40, 14), GOLD, GOLD_TEXT]
		"success":
			return [Color8(38, 122, 60), Color8(22, 74, 36), GREEN,
				Color8(214, 255, 222)]
		"danger":
			return [Color8(122, 42, 42), Color8(74, 26, 26), RED,
				Color8(255, 214, 214)]
		"locked":
			return [Color8(48, 50, 66), Color8(30, 32, 44), SLATE, TEXT_DIM]
		"owned":
			return [Color8(34, 96, 48), Color8(20, 56, 30), GREEN,
				Color8(190, 250, 200)]
		"violet":
			return [Color8(74, 48, 118), Color8(44, 28, 78),
				Color8(196, 150, 255), Color8(226, 205, 255)]
		"cyan":
			return [Color8(36, 84, 110), Color8(22, 52, 72),
				Color8(140, 214, 255), Color8(205, 240, 255)]
		_:
			return [Color8(52, 58, 84), Color8(30, 35, 56), SLATE, TEXT_BODY]


## Lebar tab auto (ui_theme.tab_width).
static func tab_width(f: Font, label_text: String, font_size: int,
		min_w: float = 150.0) -> float:
	return maxf(min_w, f.get_string_size(letter(label_text),
		HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x + 36.0)


## Knob slider (lingkaran putih + ring emas + bayangan) sebagai texture.
static func knob_texture(highlight: bool = false) -> ImageTexture:
	var key := "knob_hl" if highlight else "knob"
	if _knob_cache.has(key):
		return _knob_cache[key]
	var d := 26 if highlight else 22
	var img := Image.create(d, d, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var c := Vector2(d, d) * 0.5
	var glow_r := float(d) * 0.5
	for y in d:
		for x in d:
			var dist := Vector2(x + 0.5, y + 0.5).distance_to(c)
			var col := Color(0, 0, 0, 0)
			if highlight and dist <= glow_r:
				var t := 1.0 - dist / glow_r
				col = Color(GOLD.r, GOLD.g, GOLD.b, 0.35 * t * t)
			if dist <= 11.0:
				col = Color8(12, 14, 24)
			if dist <= 8.0:
				col = Color8(245, 248, 255)
			if dist <= 8.0 and dist > 6.0:
				col = GOLD
			if col.a > 0.0:
				img.set_pixel(x, y, col)
	var tex := ImageTexture.create_from_image(img)
	_knob_cache[key] = tex
	return tex


# ═══════════════════════════════════════════════════════════
# IKON VEKTOR — port draw_icon() ui_theme.py (s=1 -> ~16px)
# ═══════════════════════════════════════════════════════════

static func draw_icon(cv: CanvasItem, icon_name: String, center: Vector2,
		color: Color, s: float = 1.0) -> void:
	var cx := center.x
	var cy := center.y
	match icon_name:
		"play":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 6 * s, cy - 10 * s),
				Vector2(cx - 6 * s, cy + 10 * s),
				Vector2(cx + 11 * s, cy)]), color)
		"continue":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 11 * s, cy - 9 * s),
				Vector2(cx - 11 * s, cy + 9 * s),
				Vector2(cx - 1 * s, cy)]), color)
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx, cy - 9 * s), Vector2(cx, cy + 9 * s),
				Vector2(cx + 11 * s, cy)]), color)
		"coin":
			cv.draw_circle(Vector2(cx, cy), 9 * s, Color8(255, 205, 66))
			draw_ring(cv, Vector2(cx, cy), 9 * s, Color8(190, 140, 32), 2.0)
			cv.draw_circle(Vector2(cx, cy), 5 * s, Color8(230, 175, 50))
			cv.draw_line(Vector2(cx, cy - 3.5 * s), Vector2(cx, cy + 3.5 * s),
				Color8(190, 140, 32), 2.0)
		"pad":
			cv.draw_rect(Rect2(cx - 12 * s, cy - 7 * s, 24 * s, 15 * s),
				color)
			cv.draw_circle(Vector2(cx - 6 * s, cy), 2 * s,
				Color8(10, 12, 22))
			cv.draw_circle(Vector2(cx + 5 * s, cy + 2 * s), 2 * s,
				Color8(10, 12, 22))
		"help":
			var r := 5.5 * s
			cv.draw_arc(Vector2(cx, cy - 9 * s + r), r, 3.4, 6.9, 16,
				color, 2.0)
			cv.draw_line(Vector2(cx + 4.5 * s, cy - 0.3 * s),
				Vector2(cx, cy + 2.5 * s), color, 2.0)
			cv.draw_circle(Vector2(cx, cy + 6.5 * s), 1.6 * s, color)
		"gear":
			draw_ring(cv, Vector2(cx, cy), 7 * s, color, 2.0)
			for i in 6:
				var a := float(i) * PI / 3.0
				cv.draw_line(
					Vector2(cx + cos(a) * 7 * s, cy + sin(a) * 7 * s),
					Vector2(cx + cos(a) * 11 * s, cy + sin(a) * 11 * s),
					color, 2.0)
		"star":
			for d in [Vector2(1, 0), Vector2(0, 1), Vector2(1, 1),
					Vector2(1, -1)]:
				cv.draw_line(
					Vector2(cx - d.x * 8 * s, cy - d.y * 8 * s),
					Vector2(cx + d.x * 8 * s, cy + d.y * 8 * s), color, 2.0)
			cv.draw_circle(Vector2(cx, cy), 3 * s, color)
		"quit":
			cv.draw_line(Vector2(cx - 7 * s, cy - 7 * s),
				Vector2(cx + 7 * s, cy + 7 * s), color, 3.0)
			cv.draw_line(Vector2(cx + 7 * s, cy - 7 * s),
				Vector2(cx - 7 * s, cy + 7 * s), color, 3.0)
		"lock":
			var bw := 14 * s
			var bh := 11 * s
			var bx := cx - bw * 0.5
			var by := cy - bh * 0.5 + 2 * s
			cv.draw_rect(Rect2(bx, by, bw, bh), color)
			cv.draw_arc(Vector2(cx, by), bw * 0.3, PI, TAU, 12, color, 2.0)
			cv.draw_circle(Vector2(cx, by + bh * 0.45), 2 * s,
				Color8(10, 12, 22))
		"speaker":
			cv.draw_rect(Rect2(cx - 9 * s, cy - 3 * s, 5 * s, 6 * s), color)
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 4 * s, cy - 3 * s),
				Vector2(cx + 1 * s, cy - 8 * s),
				Vector2(cx + 1 * s, cy + 8 * s),
				Vector2(cx - 4 * s, cy + 3 * s)]), color)
			cv.draw_arc(Vector2(cx + 7 * s, cy), 7 * s, -1.0, 1.0, 12,
				color, 2.0)
			cv.draw_arc(Vector2(cx + 10 * s, cy), 10 * s, -0.9, 0.9, 14,
				color, 2.0)
		"swords":
			cv.draw_line(Vector2(cx - 8 * s, cy - 8 * s),
				Vector2(cx + 8 * s, cy + 8 * s), color, 3.0)
			cv.draw_line(Vector2(cx + 8 * s, cy - 8 * s),
				Vector2(cx - 8 * s, cy + 8 * s), color, 3.0)
			cv.draw_line(Vector2(cx - 9 * s, cy + 5 * s),
				Vector2(cx - 5 * s, cy + 9 * s), Color8(10, 12, 22), 3.0)
			cv.draw_line(Vector2(cx + 9 * s, cy + 5 * s),
				Vector2(cx + 5 * s, cy + 9 * s), Color8(10, 12, 22), 3.0)
			cv.draw_circle(Vector2(cx, cy), 2.5 * s, color)
		"monitor":
			cv.draw_rect(Rect2(cx - 9 * s, cy - 7 * s, 18 * s, 12 * s),
				color, false, 2.0)
			cv.draw_line(Vector2(cx, cy + 5 * s), Vector2(cx, cy + 9 * s),
				color, 2.0)
			cv.draw_line(Vector2(cx - 5 * s, cy + 9 * s),
				Vector2(cx + 5 * s, cy + 9 * s), color, 2.0)
		"cloud":
			cv.draw_circle(Vector2(cx - 5 * s, cy + 2 * s), 5 * s, color)
			cv.draw_circle(Vector2(cx, cy - 3 * s), 6 * s, color)
			cv.draw_circle(Vector2(cx + 6 * s, cy + 2 * s), 5 * s, color)
			cv.draw_rect(Rect2(cx - 5 * s, cy + 2 * s, 11 * s, 4 * s), color)
		"warn":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx, cy - 9 * s), Vector2(cx + 10 * s, cy + 8 * s),
				Vector2(cx - 10 * s, cy + 8 * s)]), color)
			cv.draw_line(Vector2(cx, cy - 4 * s), Vector2(cx, cy + 2 * s),
				Color8(10, 12, 22), 2.0)
			cv.draw_circle(Vector2(cx, cy + 5 * s), 1.5 * s,
				Color8(10, 12, 22))
		"heart":
			var r2 := 4.2 * s
			cv.draw_circle(Vector2(cx - r2, cy - r2 * 0.4), r2, color)
			cv.draw_circle(Vector2(cx + r2, cy - r2 * 0.4), r2, color)
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - r2 * 1.85, cy), Vector2(cx + r2 * 1.85, cy),
				Vector2(cx, cy + r2 * 2.1)]), color)
		"check":
			cv.draw_line(Vector2(cx - 7 * s, cy), Vector2(cx - 2 * s, cy + 5 * s),
				color, 3.0)
			cv.draw_line(Vector2(cx - 2 * s, cy + 5 * s),
				Vector2(cx + 7 * s, cy - 5 * s), color, 3.0)
		"back":
			cv.draw_line(Vector2(cx + 4 * s, cy - 7 * s),
				Vector2(cx - 5 * s, cy), color, 3.0)
			cv.draw_line(Vector2(cx - 5 * s, cy),
				Vector2(cx + 4 * s, cy + 7 * s), color, 3.0)
		"chevron_l", "chevron_r":
			var d := -1.0 if icon_name == "chevron_l" else 1.0
			cv.draw_line(Vector2(cx + 4 * s * d, cy - 6 * s),
				Vector2(cx - 4 * s * d, cy), color, 3.0)
			cv.draw_line(Vector2(cx - 4 * s * d, cy),
				Vector2(cx + 4 * s * d, cy + 6 * s), color, 3.0)
		"plus":
			cv.draw_line(Vector2(cx - 6 * s, cy), Vector2(cx + 6 * s, cy),
				color, 3.0)
			cv.draw_line(Vector2(cx, cy - 6 * s), Vector2(cx, cy + 6 * s),
				color, 3.0)
		"minus":
			cv.draw_line(Vector2(cx - 6 * s, cy), Vector2(cx + 6 * s, cy),
				color, 3.0)
		"skull":
			cv.draw_circle(Vector2(cx, cy - 2.5 * s), 6.5 * s, color)
			cv.draw_rect(Rect2(cx - 3.5 * s, cy + 2.5 * s, 7 * s, 5 * s),
				color)
			cv.draw_circle(Vector2(cx - 2.6 * s, cy - 3.5 * s), 2 * s,
				Color8(10, 12, 22))
			cv.draw_circle(Vector2(cx + 2.6 * s, cy - 3.5 * s), 2 * s,
				Color8(10, 12, 22))
		"bolt":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx + 2 * s, cy - 10 * s),
				Vector2(cx - 6 * s, cy + 1 * s),
				Vector2(cx - 1 * s, cy + 1 * s),
				Vector2(cx - 3 * s, cy + 10 * s),
				Vector2(cx + 6 * s, cy - 1 * s),
				Vector2(cx + 1 * s, cy - 1 * s)]), color)
		"crown":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 9 * s, cy + 6 * s),
				Vector2(cx - 9 * s, cy - 4 * s),
				Vector2(cx - 4 * s, cy + 1 * s),
				Vector2(cx, cy - 7 * s),
				Vector2(cx + 4 * s, cy + 1 * s),
				Vector2(cx + 9 * s, cy - 4 * s),
				Vector2(cx + 9 * s, cy + 6 * s)]), color)
		"gem":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx, cy - 8 * s), Vector2(cx + 7 * s, cy - 2 * s),
				Vector2(cx, cy + 8 * s), Vector2(cx - 7 * s, cy - 2 * s)]),
				color)
			cv.draw_line(Vector2(cx - 7 * s, cy - 2 * s),
				Vector2(cx + 7 * s, cy - 2 * s), Color.WHITE, 1.0)
		"trophy":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 7 * s, cy - 8 * s),
				Vector2(cx + 7 * s, cy - 8 * s),
				Vector2(cx + 5 * s, cy), Vector2(cx, cy + 4 * s),
				Vector2(cx - 5 * s, cy)]), color)
			cv.draw_line(Vector2(cx, cy + 4 * s), Vector2(cx, cy + 7 * s),
				color, 2.0)
			cv.draw_line(Vector2(cx - 5 * s, cy + 9 * s),
				Vector2(cx + 5 * s, cy + 9 * s), color, 2.0)
			cv.draw_arc(Vector2(cx - 7.5 * s, cy - 4.5 * s), 3.5 * s,
				1.4, 4.6, 10, color, 2.0)
			cv.draw_arc(Vector2(cx + 7.5 * s, cy - 4.5 * s), 3.5 * s,
				-1.4, 1.6, 10, color, 2.0)
		"shield":
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx, cy - 9 * s), Vector2(cx + 8 * s, cy - 5 * s),
				Vector2(cx + 8 * s, cy + 3 * s), Vector2(cx, cy + 9 * s),
				Vector2(cx - 8 * s, cy + 3 * s),
				Vector2(cx - 8 * s, cy - 5 * s)]), color)
		"upload":
			cv.draw_line(Vector2(cx, cy + 8 * s), Vector2(cx, cy - 6 * s),
				color, 2.0)
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 5 * s, cy - 2 * s),
				Vector2(cx + 5 * s, cy - 2 * s),
				Vector2(cx, cy - 8 * s)]), color)
			cv.draw_line(Vector2(cx - 7 * s, cy + 8 * s),
				Vector2(cx + 7 * s, cy + 8 * s), color, 2.0)
		"download":
			cv.draw_line(Vector2(cx, cy - 8 * s), Vector2(cx, cy + 6 * s),
				color, 2.0)
			cv.draw_colored_polygon(PackedVector2Array([
				Vector2(cx - 5 * s, cy + 2 * s),
				Vector2(cx + 5 * s, cy + 2 * s),
				Vector2(cx, cy + 8 * s)]), color)
			cv.draw_line(Vector2(cx - 7 * s, cy + 8 * s),
				Vector2(cx + 7 * s, cy + 8 * s), color, 2.0)
		"pause":
			cv.draw_rect(Rect2(cx - 6 * s, cy - 8 * s, 4.5 * s, 16 * s),
				color)
			cv.draw_rect(Rect2(cx + 1.5 * s, cy - 8 * s, 4.5 * s, 16 * s),
				color)
