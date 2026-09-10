# UiTheme.gd — design system Mystic Arena untuk Godot (port ui_theme.py 1:1).
#
# Satu sumber kebenaran tampilan menu & HUD: palet warna, font (Cinzel +
# Barlow), ikon vektor, dan helper gambar (gradasi vertikal, glow radial,
# bayangan, corner ticks, teks outline/gradasi). Padanan Godot dari
# ui_theme.py — nilai RGB diambil PERSIS dari sana.
#
# Pola pakai:
#   * Warna: UiTheme.GOLD, UiTheme.PANEL_TOP, ...
#   * Font: UiTheme.title_font() / UiTheme.body_bold() (+ ukuran via theme
#     override atau draw_string).
#   * Panel/tombol siap pakai: PygamePanel / PygameButton (widgets/).
#   * Gambar kustom: UiTheme.draw_vgrad(), draw_glow(), draw_corner_ticks(),
#     draw_icon(), draw_text_centered(), draw_outline_text().
extends RefCounted
class_name UiTheme

# ═══════════════════════════════════════════════════════════
# PALET (dark-fantasy: midnight + gold + aksen team)
# Nilai persis ui_theme.py.
# ═══════════════════════════════════════════════════════════

const BG_DEEP := Color("#090c1a")
const PANEL_TOP := Color("#1e2542")
const PANEL_BOTTOM := Color("#111528")
const PANEL_FILL := Color("#151a30")

const GOLD := Color("#ffcd55")
const GOLD_BRIGHT := Color("#ffe99e")
const GOLD_DEEP := Color("#9e7428")
const GOLD_TEXT := Color("#ffdc6e")
const EDGE_GOLD := Color("#b09052")
const EDGE_GOLD_DIM := Color("#685c42")

const CYAN := Color("#6ec3ff")
const CYAN_SOFT := Color("#a5dcff")
const VIOLET := Color("#b08aff")
const ORANGE := Color("#ffa860")
const GREEN := Color("#70e284")
const GREEN_DEEP := Color("#22743a")
const RED := Color("#ff6c6c")
const RED_DEEP := Color("#842c2c")
const SLATE := Color("#949ebc")

const TEXT_WHITE := Color("#f0f4ff")
const TEXT_BODY := Color("#c6cfe6")
const TEXT_DIM := Color("#848eaa")
const TEXT_FAINT := Color("#606a88")

const LOCKED_BG_TOP := Color("#1e1c28")
const LOCKED_BG_BOTTOM := Color("#14131d")
const LOCKED_EDGE := Color("#54566e")
const DONE_BG_TOP := Color("#1a2c24")
const DONE_BG_BOTTOM := Color("#111e18")
const DONE_EDGE := Color("#56b270")
const OPEN_BG_TOP := Color("#1c2640")
const OPEN_BG_BOTTOM := Color("#12182c")
const OPEN_EDGE := Color("#6098d6")

const SHADOW_COLOR := Color(0, 0, 0, 110.0 / 255.0)
const TEXT_SHADOW := Color("#05060c")

# Ukuran layar acuan (semua layout menu pygame 1280x720).
const SCREEN_W := 1280.0
const SCREEN_H := 720.0


# ═══════════════════════════════════════════════════════════
# FONT (Cinzel judul + Barlow isi — berkas sama dengan pygame)
# ═══════════════════════════════════════════════════════════

static var _font_cache: Dictionary = {}


static func _load_font(file_name: String) -> Font:
	if _font_cache.has(file_name):
		return _font_cache[file_name] as Font
	var f: Font = load("res://assets/fonts/" + file_name) as Font
	if f == null:
		f = ThemeDB.fallback_font
	_font_cache[file_name] = f
	return f


## Cinzel — judul layar (MYSTIC ARENA, VICTORY, ...).
static func title_font() -> Font:
	return _load_font("Cinzel.ttf")


## Barlow-Bold — label tombol, angka, badge.
static func body_bold() -> Font:
	return _load_font("Barlow-Bold.ttf")


## Barlow-SemiBold — sub-judul, nama kartu.
static func body_semibold() -> Font:
	return _load_font("Barlow-SemiBold.ttf")


## Barlow-Medium — teks isi.
static func body_medium() -> Font:
	return _load_font("Barlow-Medium.ttf")


## Barlow-Regular — teks kecil/redup.
static func body_regular() -> Font:
	return _load_font("Barlow-Regular.ttf")


## Padanan _core.get_font(size, weight): kembalikan font sesuai bobot pygame.
static func font_for_weight(weight: String) -> Font:
	match weight:
		"body_bold":
			return body_bold()
		"body_semibold":
			return body_semibold()
		"body_medium":
			return body_medium()
		"body", "body_regular":
			return body_regular()
		"title":
			return title_font()
	return body_regular()


## Terapkan font + ukuran + warna ke Label (jalan pintas).
static func style_label(l: Label, text: String, font: Font, size: int,
		color: Color, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT,
		shadow: bool = false) -> Label:
	l.text = text
	if font != null:
		l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = align
	if shadow:
		l.add_theme_color_override("font_shadow_color", TEXT_SHADOW)
		l.add_theme_constant_override("shadow_offset_x", 2)
		l.add_theme_constant_override("shadow_offset_y", 2)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


# ═══════════════════════════════════════════════════════════
# TEKS (port letter / fit_ellipsis / draw_text / outline_text)
# ═══════════════════════════════════════════════════════════

## Letter-spacing manual (paritas ui_theme.letter).
static func letter(text: String, gap: String = " ") -> String:
	return HudLayout.letter(text, gap)


## Truncate dengan elipsis memakai metrik font Godot.
static func fit_ellipsis(font: Font, font_size: int, text: String,
		max_w: float) -> String:
	var s := str(text)
	if font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1,
			font_size).x <= max_w:
		return s
	var ell := "…"
	while s.length() > 1:
		var cand := s.substr(0, s.length() - 1)
		if font.get_string_size(cand + ell, HORIZONTAL_ALIGNMENT_LEFT, -1,
				font_size).x <= max_w:
			return cand + ell
		s = cand
	return ell


## Teks rata kiri dari posisi topleft, dengan bayangan opsional.
static func draw_text(cv: CanvasItem, font: Font, text: String, size: int,
		color: Color, topleft: Vector2, shadow: bool = true,
		shadow_offset: Vector2 = Vector2(2, 2)) -> void:
	var baseline := topleft.y + font.get_ascent(size)
	if shadow:
		cv.draw_string(font, Vector2(topleft.x, baseline) + shadow_offset,
			text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, TEXT_SHADOW)
	cv.draw_string(font, Vector2(topleft.x, baseline), text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)


## Teks terpusat di `center`, dengan bayangan opsional.
static func draw_text_centered(cv: CanvasItem, font: Font, text: String,
		size: int, color: Color, center: Vector2, shadow: bool = true,
		shadow_offset: Vector2 = Vector2(2, 2),
		max_width: float = -1.0) -> void:
	var w := max_width
	if w <= 0.0:
		w = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			size).x + 4.0
	var baseline := center.y + (font.get_ascent(size) - font.get_descent(size)) * 0.5
	var pos := Vector2(center.x - w * 0.5, baseline)
	if shadow:
		cv.draw_string(font, pos + shadow_offset, text,
			HORIZONTAL_ALIGNMENT_CENTER, w, size, TEXT_SHADOW)
	cv.draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_CENTER, w, size,
		color)


## Judul tebal dengan outline gelap 8 arah + isi terang (paritas
## ui_theme.outline_text; gradasi isi didekati warna terang solid —
## Godot tidak bisa masking gradasi ke glif tanpa render target).
static func draw_outline_text(cv: CanvasItem, font: Font, text: String,
		size: int, center: Vector2, body_color: Color = GOLD_BRIGHT,
		outline_color: Color = Color("#080912"),
		outline_size: int = 2) -> void:
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
		size).x + outline_size * 2.0 + 4.0
	var baseline := center.y + (font.get_ascent(size) - font.get_descent(size)) * 0.5
	var pos := Vector2(center.x - w * 0.5, baseline)
	cv.draw_string_outline(font, pos, text, HORIZONTAL_ALIGNMENT_CENTER, w,
		size, outline_size, outline_color)
	cv.draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_CENTER, w, size,
		body_color)


# ═══════════════════════════════════════════════════════════
# GAMBAR PRIMITIF (port _vgrad / _radial / _shadow / corner_ticks)
# ═══════════════════════════════════════════════════════════

## Gradasi vertikal mengisi rect sudut membulat (port _vgrad + mask radius).
## Dipanggil dari _draw() saja (bukan tiap frame) — loops ratusan baris aman.
static func draw_vgrad(cv: CanvasItem, rect: Rect2, top: Color,
		bottom: Color, radius: float = 0.0) -> void:
	var h := int(rect.size.y)
	if h <= 0 or rect.size.x <= 0.0:
		return
	var r := minf(radius, rect.size.y * 0.5, rect.size.x * 0.5)
	for y in range(h):
		var t := float(y) / float(maxi(1, h - 1))
		var col := top.lerp(bottom, t)
		var yy := rect.position.y + float(y) + 0.5
		var x0 := rect.position.x
		var x1 := rect.position.x + rect.size.x
		if r > 0.0:
			var dy: float = minf(float(y), float(h - 1 - y))
			if dy < r:
				var dx: float = r - sqrt(r * r - (r - dy) * (r - dy))
				x0 += dx
				x1 -= dx
		if x1 > x0:
			cv.draw_line(Vector2(x0, yy), Vector2(x1, yy), col, 1.0)


## Glow radial elips di tengah rect (port _radial — pendekatan lingkaran
## konsentris; dipanggil dari _draw() saja).
static func draw_glow(cv: CanvasItem, rect: Rect2, color: Color,
		alpha: float, steps: int = 14) -> void:
	var c := rect.get_center()
	var max_r := minf(rect.size.x, rect.size.y) * 0.5
	if max_r <= 0.0:
		return
	var sx := rect.size.x / maxf(1.0, rect.size.y)
	for i in range(steps, 0, -1):
		var f := float(i) / float(steps)
		var a := alpha * (1.0 - f) * (1.0 - f)
		if a <= 0.004:
			continue
		var col := Color(color.r, color.g, color.b, a)
		# Elips via poligon (Godot tidak punya draw_ellipse).
		var pts := PackedVector2Array()
		var n := 28
		for k in range(n):
			var ang := TAU * float(k) / float(n)
			pts.append(c + Vector2(cos(ang) * max_r * f * sx,
				sin(ang) * max_r * f))
		cv.draw_colored_polygon(pts, col)


## Bayangan lembut: persegi membulat berlapis (port _shadow).
static func draw_shadow(cv: CanvasItem, rect: Rect2, radius: float = 12.0,
		alpha: float = 110.0 / 255.0, spread: float = 4.0) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.shadow_color = Color(0, 0, 0, alpha)
	sb.shadow_size = int(spread * 3.0)
	sb.shadow_offset = Vector2(2, 3)
	sb.set_corner_radius_all(int(radius))
	cv.draw_style_box(sb, rect)


## Persegi membulat isi solid (helper ikon & badge).
static func draw_rr(cv: CanvasItem, rect: Rect2, color: Color,
		radius: float) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.set_corner_radius_all(int(radius))
	sb.anti_aliasing = true
	cv.draw_style_box(sb, rect)


## Outline persegi membulat (helper ikon & badge).
static func draw_rr_outline(cv: CanvasItem, rect: Rect2, color: Color,
		radius: float, width: float = 1.0) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	sb.border_color = color
	sb.set_border_width_all(int(ceil(width)))
	sb.set_corner_radius_all(int(radius))
	sb.anti_aliasing = true
	cv.draw_style_box(sb, rect)


## Tanda sudut emas — identitas visual Mystic Arena (port corner_ticks).
static func draw_corner_ticks(cv: CanvasItem, rect: Rect2,
		color: Color = GOLD, length: float = 11.0, width: float = 2.0,
		inset: float = 2.0) -> void:
	var pts: Array = [
		[rect.position + Vector2(inset, inset), Vector2(1, 0), Vector2(0, 1)],
		[Vector2(rect.end.x - inset, rect.position.y + inset), Vector2(-1, 0), Vector2(0, 1)],
		[rect.position + Vector2(inset, rect.size.y - inset), Vector2(1, 0), Vector2(0, -1)],
		[rect.end - Vector2(inset, inset), Vector2(-1, 0), Vector2(0, -1)],
	]
	for p in pts:
		var anchor: Vector2 = p[0]
		var dx: Vector2 = p[1]
		var dy: Vector2 = p[2]
		cv.draw_line(anchor, anchor + dx * length, color, width)
		cv.draw_line(anchor, anchor + dy * length, color, width)


# ═══════════════════════════════════════════════════════════
# STYLEBOX (pendekatan solid untuk container Godot biasa)
# ═══════════════════════════════════════════════════════════

## Style panel: isi gelap + border + sudut + bayangan (pendekatan solid
## dari ui_theme.panel; versi gradasi eksak = PygamePanel).
static func panel_style(border: Color = EDGE_GOLD, border_w: int = 1,
		radius: int = 12, fill: Color = PANEL_FILL,
		shadow: bool = true) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = fill
	sb.border_color = border
	sb.set_border_width_all(border_w)
	sb.set_corner_radius_all(radius)
	sb.anti_aliasing = true
	if shadow:
		sb.shadow_color = SHADOW_COLOR
		sb.shadow_size = 12
		sb.shadow_offset = Vector2(2, 3)
	return sb


## Style tombol generik beraksen (pendekatan solid; versi eksak =
## PygameButton Mode.MENU).
static func button_style(accent: Color, hover: bool = false,
		pressed: bool = false) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	var a := 0.30 if hover else 0.13
	if pressed:
		a = 0.42
	sb.bg_color = Color(accent.r, accent.g, accent.b, a)
	sb.border_color = Color(accent.r, accent.g, accent.b, 0.75)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 12.0
	sb.content_margin_right = 12.0
	return sb


## Warna pill per kind (port tabel ui_theme.pill): [top, bottom, edge, text].
static func pill_colors(kind: String) -> Array:
	match kind:
		"gold":
			return [Color("#564216"), Color("#34280e"), GOLD, GOLD_TEXT]
		"success":
			return [Color("#267a3c"), Color("#164a24"), GREEN,
				Color("#d6ffde")]
		"danger":
			return [Color("#7a2a2a"), Color("#4a1a1a"), RED,
				Color("#ffd6d6")]
		"locked":
			return [Color("#303242"), Color("#1e202c"), SLATE, TEXT_DIM]
		"owned":
			return [Color("#226030"), Color("#14381e"), GREEN,
				Color("#befaca")]
		"violet":
			return [Color("#4a3076"), Color("#2c1c4e"), Color("#c496ff"),
				Color("#e2cdff")]
		"cyan":
			return [Color("#24546e"), Color("#163448"), Color("#8cd6ff"),
				Color("#cdf0ff")]
		_: # "neutral"
			return [Color("#343a54"), Color("#1e2338"), SLATE, TEXT_BODY]


## Bar HP/mana premium (port ui_theme.hp_bar).
static func draw_hp_bar(cv: CanvasItem, pos: Vector2, w: float, h: float,
		ratio: float, color: Color = GREEN) -> void:
	var r := Rect2(pos, Vector2(w, h))
	draw_rr(cv, r, Color("#10121e"), h * 0.5)
	var fw := w * clampf(ratio, 0.0, 1.0)
	if fw > 3.0:
		var light := Color(minf(1.0, color.r + 50.0 / 255.0),
			minf(1.0, color.g + 50.0 / 255.0),
			minf(1.0, color.b + 50.0 / 255.0))
		draw_vgrad(cv, Rect2(pos, Vector2(fw, h)), light, color, h * 0.5)
	draw_rr_outline(cv, r, Color("#565c78"), h * 0.5, 1.0)


## Bar progres emas (port ui_theme.progress_bar).
static func draw_progress_bar(cv: CanvasItem, pos: Vector2, w: float,
		frac: float, color: Color = GOLD, h: float = 8.0) -> void:
	var r := Rect2(pos, Vector2(w, h))
	draw_rr(cv, r, Color("#1e2236"), h * 0.5)
	var fw := w * clampf(frac, 0.0, 1.0)
	if fw > 3.0:
		var light := Color(minf(1.0, color.r + 40.0 / 255.0),
			minf(1.0, color.g + 40.0 / 255.0),
			minf(1.0, color.b + 40.0 / 255.0))
		draw_vgrad(cv, Rect2(pos, Vector2(fw, h)), light, color, h * 0.5)
	draw_rr_outline(cv, r, Color("#60607e"), h * 0.5, 1.0)


# ═══════════════════════════════════════════════════════════
# IKON VEKTOR (port ui_theme.draw_icon 1:1 — semua 26 ikon)
# ═══════════════════════════════════════════════════════════

static func _poly(cv: CanvasItem, pts: Array, color: Color) -> void:
	cv.draw_colored_polygon(PackedVector2Array(pts), color)


## Gambar satu ikon vektor; cx/cy = pusat, s=1 -> ~16px (sama persis pygame).
static func draw_icon(cv: CanvasItem, icon_name: String, cx: float, cy: float,
		color: Color, s: float = 1.0) -> void:
	var dark := Color("#0a0c16")
	match icon_name:
		"play":
			_poly(cv, [Vector2(cx - 6 * s, cy - 10 * s),
				Vector2(cx - 6 * s, cy + 10 * s),
				Vector2(cx + 11 * s, cy)], color)
		"continue":
			_poly(cv, [Vector2(cx - 11 * s, cy - 9 * s),
				Vector2(cx - 11 * s, cy + 9 * s),
				Vector2(cx - 1 * s, cy)], color)
			_poly(cv, [Vector2(cx, cy - 9 * s),
				Vector2(cx, cy + 9 * s),
				Vector2(cx + 11 * s, cy)], color)
		"coin":
			cv.draw_circle(Vector2(cx, cy), 9 * s, Color("#ffcd42"))
			cv.draw_arc(Vector2(cx, cy), 9 * s, 0, TAU, 32,
				Color("#be8c20"), 2.0)
			cv.draw_circle(Vector2(cx, cy), 5 * s, Color("#e6af32"))
			cv.draw_line(Vector2(cx, cy - 3.5 * s),
				Vector2(cx, cy + 3.5 * s), Color("#be8c20"), 2.0)
		"pad":
			draw_rr(cv, Rect2(cx - 12 * s, cy - 7 * s, 24 * s, 15 * s),
				color, 7 * s)
			cv.draw_circle(Vector2(cx - 6 * s, cy), 2 * s, dark)
			cv.draw_circle(Vector2(cx + 5 * s, cy + 2 * s), 2 * s, dark)
		"help":
			var r := 5.5 * s
			cv.draw_arc(Vector2(cx, cy - 9 * s + r), r, 3.4, 6.9, 16,
				color, 2.0)
			cv.draw_line(Vector2(cx + 4.5 * s, cy - 0.3 * s),
				Vector2(cx, cy + 2.5 * s), color, 2.0)
			cv.draw_circle(Vector2(cx, cy + 6.5 * s), 1.6 * s, color)
		"gear":
			cv.draw_arc(Vector2(cx, cy), 7 * s, 0, TAU, 24, color, 2.0)
			for i in range(6):
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
			draw_rr(cv, Rect2(bx, by, bw, bh), color, 3 * s)
			cv.draw_arc(Vector2(cx, by - 2 * s), bw * 0.3, PI, TAU, 16,
				color, 2.0)
			cv.draw_circle(Vector2(cx, by + bh * 0.45), 2 * s, dark)
		"speaker":
			cv.draw_rect(Rect2(cx - 9 * s, cy - 3 * s, 5 * s, 6 * s),
				color)
			_poly(cv, [Vector2(cx - 4 * s, cy - 3 * s),
				Vector2(cx + 1 * s, cy - 8 * s),
				Vector2(cx + 1 * s, cy + 8 * s),
				Vector2(cx - 4 * s, cy + 3 * s)], color)
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
				Vector2(cx - 5 * s, cy + 9 * s), dark, 3.0)
			cv.draw_line(Vector2(cx + 9 * s, cy + 5 * s),
				Vector2(cx + 5 * s, cy + 9 * s), dark, 3.0)
			cv.draw_circle(Vector2(cx, cy), 2.5 * s, color)
		"monitor":
			draw_rr_outline(cv, Rect2(cx - 9 * s, cy - 7 * s, 18 * s,
				12 * s), color, 2 * s, 2.0)
			cv.draw_line(Vector2(cx, cy + 5 * s), Vector2(cx, cy + 9 * s),
				color, 2.0)
			cv.draw_line(Vector2(cx - 5 * s, cy + 9 * s),
				Vector2(cx + 5 * s, cy + 9 * s), color, 2.0)
		"cloud":
			cv.draw_circle(Vector2(cx - 5 * s, cy + 2 * s), 5 * s, color)
			cv.draw_circle(Vector2(cx, cy - 3 * s), 6 * s, color)
			cv.draw_circle(Vector2(cx + 6 * s, cy + 2 * s), 5 * s, color)
			cv.draw_rect(Rect2(cx - 5 * s, cy + 2 * s, 11 * s, 4 * s),
				color)
		"warn":
			_poly(cv, [Vector2(cx, cy - 9 * s),
				Vector2(cx + 10 * s, cy + 8 * s),
				Vector2(cx - 10 * s, cy + 8 * s)], color)
			cv.draw_line(Vector2(cx, cy - 4 * s), Vector2(cx, cy + 2 * s),
				dark, 2.0)
			cv.draw_circle(Vector2(cx, cy + 5 * s), 1.5 * s, dark)
		"heart":
			var hr := 4.2 * s
			cv.draw_circle(Vector2(cx - hr, cy - hr * 0.4), hr, color)
			cv.draw_circle(Vector2(cx + hr, cy - hr * 0.4), hr, color)
			_poly(cv, [Vector2(cx - hr * 1.85, cy),
				Vector2(cx + hr * 1.85, cy),
				Vector2(cx, cy + hr * 2.1)], color)
		"check":
			cv.draw_line(Vector2(cx - 7 * s, cy),
				Vector2(cx - 2 * s, cy + 5 * s), color, 3.0)
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
			draw_rr(cv, Rect2(cx - 3.5 * s, cy + 2.5 * s, 7 * s, 5 * s),
				color, 2.0)
			cv.draw_circle(Vector2(cx - 2.6 * s, cy - 3.5 * s), 2 * s,
				dark)
			cv.draw_circle(Vector2(cx + 2.6 * s, cy - 3.5 * s), 2 * s,
				dark)
		"bolt":
			_poly(cv, [Vector2(cx + 2 * s, cy - 10 * s),
				Vector2(cx - 6 * s, cy + 1 * s),
				Vector2(cx - 1 * s, cy + 1 * s),
				Vector2(cx - 3 * s, cy + 10 * s),
				Vector2(cx + 6 * s, cy - 1 * s),
				Vector2(cx + 1 * s, cy - 1 * s)], color)
		"crown":
			_poly(cv, [Vector2(cx - 9 * s, cy + 6 * s),
				Vector2(cx - 9 * s, cy - 4 * s),
				Vector2(cx - 4 * s, cy + 1 * s),
				Vector2(cx, cy - 7 * s),
				Vector2(cx + 4 * s, cy + 1 * s),
				Vector2(cx + 9 * s, cy - 4 * s),
				Vector2(cx + 9 * s, cy + 6 * s)], color)
		"gem":
			_poly(cv, [Vector2(cx, cy - 8 * s),
				Vector2(cx + 7 * s, cy - 2 * s),
				Vector2(cx, cy + 8 * s),
				Vector2(cx - 7 * s, cy - 2 * s)], color)
			cv.draw_line(Vector2(cx - 7 * s, cy - 2 * s),
				Vector2(cx + 7 * s, cy - 2 * s), Color.WHITE, 1.0)
		"trophy":
			_poly(cv, [Vector2(cx - 7 * s, cy - 8 * s),
				Vector2(cx + 7 * s, cy - 8 * s),
				Vector2(cx + 5 * s, cy),
				Vector2(cx, cy + 4 * s),
				Vector2(cx - 5 * s, cy)], color)
			cv.draw_line(Vector2(cx, cy + 4 * s), Vector2(cx, cy + 7 * s),
				color, 2.0)
			cv.draw_line(Vector2(cx - 5 * s, cy + 9 * s),
				Vector2(cx + 5 * s, cy + 9 * s), color, 2.0)
			cv.draw_arc(Vector2(cx - 7.5 * s, cy - 4.5 * s), 3.5 * s,
				1.4, 4.6, 10, color, 2.0)
			cv.draw_arc(Vector2(cx + 7.5 * s, cy - 4.5 * s), 3.5 * s,
				-1.4, 1.6, 10, color, 2.0)
		"shield":
			_poly(cv, [Vector2(cx, cy - 9 * s),
				Vector2(cx + 8 * s, cy - 5 * s),
				Vector2(cx + 8 * s, cy + 3 * s),
				Vector2(cx, cy + 9 * s),
				Vector2(cx - 8 * s, cy + 3 * s),
				Vector2(cx - 8 * s, cy - 5 * s)], color)
		"upload":
			cv.draw_line(Vector2(cx, cy + 8 * s), Vector2(cx, cy - 6 * s),
				color, 2.0)
			_poly(cv, [Vector2(cx - 5 * s, cy - 2 * s),
				Vector2(cx + 5 * s, cy - 2 * s),
				Vector2(cx, cy - 8 * s)], color)
			cv.draw_line(Vector2(cx - 7 * s, cy + 8 * s),
				Vector2(cx + 7 * s, cy + 8 * s), color, 2.0)
		"download":
			cv.draw_line(Vector2(cx, cy - 8 * s), Vector2(cx, cy + 6 * s),
				color, 2.0)
			_poly(cv, [Vector2(cx - 5 * s, cy + 2 * s),
				Vector2(cx + 5 * s, cy + 2 * s),
				Vector2(cx, cy + 8 * s)], color)
			cv.draw_line(Vector2(cx - 7 * s, cy + 8 * s),
				Vector2(cx + 7 * s, cy + 8 * s), color, 2.0)


# ═══════════════════════════════════════════════════════════
# WIDGET NATIF (gaya premium untuk Button/HSlider/ProgressBar biasa —
# dipakai di tempat teks .text native dikunci test: SkillBar, ShopPanel)
# ═══════════════════════════════════════════════════════════

## Gaya tombol baris beraksen (pendekatan solid dari ui_theme.pill):
## isi gelap + border aksen + sudut + font Barlow-Bold. `kind` memakai
## tabel pill_colors ("gold"/"success"/"danger"/"locked"/"neutral"/...).
static func apply_row_button(b: Button, kind: String = "neutral",
		font_size: int = 12, align_left: bool = true) -> Button:
	var cols: Array = pill_colors(kind)
	var top: Color = cols[0]
	var edge: Color = cols[2]
	var tcol: Color = cols[3]
	b.add_theme_font_override("font", body_bold())
	b.add_theme_font_size_override("font_size", font_size)
	if align_left:
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	var normal := StyleBoxFlat.new()
	normal.bg_color = top
	normal.border_color = edge
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(6)
	normal.content_margin_left = 10.0
	normal.content_margin_right = 10.0
	normal.content_margin_top = 5.0
	normal.content_margin_bottom = 5.0
	var hover := normal.duplicate() as StyleBoxFlat
	hover.bg_color = Color(minf(1.0, top.r + 0.07),
		minf(1.0, top.g + 0.07), minf(1.0, top.b + 0.07))
	hover.border_color = GOLD if kind == "gold" else edge.lightened(0.3)
	var pressed := normal.duplicate() as StyleBoxFlat
	pressed.bg_color = top.darkened(0.15)
	var disabled := normal.duplicate() as StyleBoxFlat
	disabled.bg_color = Color(0.07, 0.075, 0.1, 0.9)
	disabled.border_color = Color(0.3, 0.32, 0.4, 0.6)
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("focus", hover)
	b.add_theme_stylebox_override("disabled", disabled)
	b.add_theme_color_override("font_color", tcol)
	b.add_theme_color_override("font_hover_color", GOLD_BRIGHT)
	b.add_theme_color_override("font_pressed_color", tcol)
	b.add_theme_color_override("font_disabled_color",
		Color(0.45, 0.47, 0.55))
	return b


## Slider volume emas (port ui_theme.slider): track gelap + isi emas +
## knob cincin. Dipanggil sekali per HSlider.
static func style_volume_slider(s: HSlider) -> void:
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.09, 0.1, 0.15)
	bg.set_corner_radius_all(4)
	bg.content_margin_top = 4.0
	bg.content_margin_bottom = 4.0
	var fill := StyleBoxFlat.new()
	fill.bg_color = GOLD
	fill.set_corner_radius_all(4)
	fill.content_margin_top = 4.0
	fill.content_margin_bottom = 4.0
	s.add_theme_stylebox_override("slider", bg)
	s.add_theme_stylebox_override("grabber_area", fill)
	s.add_theme_icon_override("grabber", _knob_texture(false))
	s.add_theme_icon_override("grabber_highlight", _knob_texture(true))


static var _knob_cache: Dictionary = {}


## Knob cincin emas 22px (digambar prosedural — tanpa berkas gambar).
static func _knob_texture(hot: bool) -> Texture2D:
	var key := "hot" if hot else "idle"
	if _knob_cache.has(key):
		return _knob_cache[key] as Texture2D
	var size := 22
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var c := Vector2(size * 0.5, size * 0.5)
	var ring := GOLD_BRIGHT if hot else GOLD
	for y in range(size):
		for x in range(size):
			var d := Vector2(x + 0.5, y + 0.5).distance_to(c)
			if d <= 10.0 and d >= 6.5:
				img.set_pixel(x, y, ring)
			elif d < 6.5:
				img.set_pixel(x, y, Color(0.07, 0.08, 0.13))
	var tex := ImageTexture.create_from_image(img)
	_knob_cache[key] = tex
	return tex


## ProgressBar premium (track + isi membulat).
static func style_progress_bar(bar: ProgressBar, fill: Color,
		track: Color = Color(0.1, 0.12, 0.18),
		radius: int = 4) -> void:
	var bg := StyleBoxFlat.new()
	bg.bg_color = track
	bg.set_corner_radius_all(radius)
	var fg := StyleBoxFlat.new()
	fg.bg_color = fill
	fg.set_corner_radius_all(radius)
	bar.add_theme_stylebox_override("background", bg)
	bar.add_theme_stylebox_override("fill", fg)
	bar.show_percentage = false


## Hairline emas untuk HSeparator/VSeparator.
static func style_separator(sep: Separator, color: Color = EDGE_GOLD) -> void:
	var sb := StyleBoxLine.new()
	sb.color = color
	sb.thickness = 1
	sep.add_theme_stylebox_override("separator", sb)
