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
const OUTLINE_DARK := Color("#080912")   # (8, 9, 18)
#   Warna outline gradient_text/outline_text. ui_theme.py menulisnya
#   inline di tiap pemanggil, jadi ini bukan konstanta BARU — hanya
#   diberi nama supaya tidak ditulis ulang di GradientText/ScreenTitle
#   (lihat tools/visual_parity_audit.py bagian HARDCODE).

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


## Port `_has_glyph(font, ch)`: pygame merender karakter lalu membandingkannya
## dengan karakter yang pasti tidak ada; Godot bertanya langsung ke font.
static func has_glyph(font: Font, ch: String) -> bool:
	if font == null or ch.is_empty():
		return false
	return font.has_char(ch.unicode_at(0))


## Truncate dengan elipsis memakai metrik font Godot.
static func fit_ellipsis(font: Font, font_size: int, text: String,
		max_w: float) -> String:
	var s := str(text)
	if font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1,
			font_size).x <= max_w:
		return s
	# Paritas ui_theme.fit_ellipsis: "…" hanya kalau font punya glifnya,
	# kalau tidak jatuh ke "..." (font tanpa U+2026 menggambar kotak).
	var ell := "…" if has_glyph(font, "…") else "..."
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
		outline_color: Color = OUTLINE_DARK,
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
	var r := minf(radius, minf(rect.size.y * 0.5, rect.size.x * 0.5))
	for y in range(h):
		# Warna baris = port PERSIS loop `_vgrad` (kuantisasi 8-bit int()).
		var col := vgrad_row_color(top, bottom, y, h)
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


## Glow radial elips (port `_radial` 1:1 — tekstur di-cache persis seperti
## permukaan cache pygame, lalu satu blit). `rect` = rect tujuan blit
## (pemanggil pygame sudah membesarkannya, mis. `_radial(w+44, h+36)` di
## blit `(x-22, y-18)`).
##
## `_steps` dipertahankan hanya supaya pemanggil lama tidak berubah;
## glow sekarang eksak (bukan lagi pendekatan lingkaran konsentris).
static func draw_glow(cv: CanvasItem, rect: Rect2, color: Color,
		alpha: float, _steps: int = 14) -> void:
	if rect.size.x < 1.0 or rect.size.y < 1.0:
		return
	var tex := radial_texture(rect.size.x, rect.size.y, color,
		roundi(alpha * 255.0))
	if tex == null:
		return
	cv.draw_texture_rect(tex, Rect2(rect.position,
		Vector2(tex.get_width(), tex.get_height())), false)


## Bayangan lembut (port `_shadow` 1:1 — persegi membulat 1/8 ukuran yang
## di-scale halus, di-cache seperti permukaan pygame).
##
## `offset` = posisi blit relatif terhadap rect: `panel()` pygame memakai
## `(r.x - 4, r.y - 4)` (= -spread, bayangan simetris) sedangkan `button()`
## memakai `(rect.x - 2, rect.y - 2)` (bayangan turun-kanan 2px).
static func draw_shadow(cv: CanvasItem, rect: Rect2, radius: float = 12.0,
		alpha: float = 110.0 / 255.0, spread: float = 4.0,
		offset: Vector2 = Vector2.INF) -> void:
	var tex := shadow_texture(rect.size.x, rect.size.y, radius,
		roundi(alpha * 255.0), spread)
	if tex == null:
		return
	var off := Vector2(-spread, -spread) if offset == Vector2.INF else offset
	cv.draw_texture_rect(tex, Rect2(rect.position + off,
		Vector2(tex.get_width(), tex.get_height())), false)


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
	var r := pyrect(Rect2(pos, Vector2(w, h)))
	var rad := floor(r.size.y / 2.0)
	draw_rr(cv, r, Color("#10121e"), rad)
	var fw := bar_fill_w(r.size.x, ratio)
	if fw > 3:
		# pygame: `tuple(min(255, c + 50) for c in color)` (ruang 8-bit).
		draw_vgrad(cv, Rect2(r.position, Vector2(fw, r.size.y)),
			add_rgb(color, 50), color, rad)
	draw_rr_outline(cv, r, Color("#565c78"), rad, 1.0)


## Bar progres emas (port ui_theme.progress_bar).
static func draw_progress_bar(cv: CanvasItem, pos: Vector2, w: float,
		frac: float, color: Color = GOLD, h: float = 8.0) -> void:
	var r := pyrect(Rect2(pos, Vector2(w, h)))
	var rad := floor(r.size.y / 2.0)
	draw_rr(cv, r, Color("#1e2236"), rad)
	var fw := bar_fill_w(r.size.x, frac)
	if fw > 3:
		draw_vgrad(cv, Rect2(r.position, Vector2(fw, r.size.y)),
			add_rgb(color, 40), color, rad)
	draw_rr_outline(cv, r, Color("#60607e"), rad, 1.0)


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


# ═══════════════════════════════════════════════════════════
# KUALITAS & CACHE (port cheap_alpha / clear_caches / math_hyp)
# ═══════════════════════════════════════════════════════════

## Override jalur alpha: -1 = auto, 0 = paksa HEMAT (bentuk solid murah),
## 1 = paksa penuh (glow/bayangan/gradasi). Padanan `Quality.cheap_alpha`
## yang di-set `mobile/perf.py:746/755/797`.
static var cheap_alpha_override: int = -1


## Port `ui_theme.cheap_alpha()`.
##
## Di pygame ini PROPERTI PERANGKAT yang diukur sekali oleh
## `perf.apply_device_profile()`: False kalau satu blit alpha layar penuh
## lebih mahal dari 5 ms (`mobile/perf.py:796-797`) sehingga glow, bayangan
## lembut, dan gradasi diganti bentuk solid murah. Di Godot komposisi alpha
## terjadi di GPU (tidak ada biaya per piksel di CPU), jadi jalur "mahal"
## selalu terjangkau -> auto = True. Kedua cabang TETAP diport 1:1 supaya
## bentuk visual mode hemat bisa dipakai/diuji lewat `cheap_alpha_override`.
static func cheap_alpha() -> bool:
	if cheap_alpha_override != -1:
		return cheap_alpha_override == 1
	return true


## Port `ui_theme.clear_caches()` — buang semua permukaan/tekstur cache.
## Dipanggil saat memori menipis atau saat tes butuh keadaan bersih.
static func clear_caches() -> void:
	_glow_cache.clear()
	_shadow_cache.clear()
	_font_cache.clear()
	_knob_cache.clear()


## Port `ui_theme.math_hyp(x, y)`.
static func hyp(x: float, y: float) -> float:
	return sqrt(x * x + y * y)


## pygame.Rect memotong (bukan membulatkan) koordinat float ke int. Semua
## komponen di bawah melewati rect ini supaya geometrinya identik.
static func pyrect(r: Rect2) -> Rect2:
	return Rect2(Vector2(float(int(r.position.x)), float(int(r.position.y))),
		Vector2(float(int(r.size.x)), float(int(r.size.y))))


# ═══════════════════════════════════════════════════════════
# MATEMATIKA WARNA & GRADASI (fungsi murni — dikunci oracle
# tools/test_godot_ui_theme_parity.py terhadap ui_theme.py ASLI)
# ═══════════════════════════════════════════════════════════

## Port `_dim(color, f=0.55)` — `int(c * f)` Python = truncation ke nol.
static func dim(color: Color, f: float = 0.55) -> Color:
	return Color8(int(float(color.r8) * f), int(float(color.g8) * f),
		int(float(color.b8) * f))


## Port `tuple(min(255, c + n) for c in color)` — dipakai hover pill (+18/+14),
## isi `hp_bar` (+50), dan `progress_bar` (+40).
static func add_rgb(color: Color, amount: int) -> Color:
	return Color8(mini(255, color.r8 + amount),
		mini(255, color.g8 + amount), mini(255, color.b8 + amount))


## Warna baris gradasi ke-`y` dari `h` baris — port PERSIS loop `_vgrad`:
## `t = y / max(1, h - 1)` lalu `int(top + (bottom - top) * t)` per kanal.
static func vgrad_row_color(top: Color, bottom: Color, y: int, h: int) -> Color:
	var rows := maxi(2, h)
	var t := float(y) / float(maxi(1, rows - 1))
	return Color8(
		int(float(top.r8) + float(bottom.r8 - top.r8) * t),
		int(float(top.g8) + float(bottom.g8 - top.g8) * t),
		int(float(top.b8) + float(bottom.b8 - top.b8) * t))


## Kuantisasi alpha glow — port `a = max(4, min(120, int(alpha) // 8 * 8))`
## di `_radial` (kunci cache dibulatkan ke kelipatan 8).
static func radial_alpha_key(alpha: int) -> int:
	return maxi(4, mini(120, int(floor(float(alpha) / 8.0)) * 8))


## Alpha satu blok glow — port `aa = int(a * (1 - d) ** 2)` di `_radial`,
## dengan `d` = jarak titik ke pusat dibagi jarak pusat-ke-sudut.
static func glow_alpha_at(alpha_key: int, d: float) -> int:
	if d >= 1.0:
		return 0
	var f := 1.0 - d
	return int(float(alpha_key) * f * f)


## Lebar isi bar/ slider — port `int(w * max(0.0, min(1.0, ratio)))`
## (`hp_bar`, `progress_bar`, `slider`).
static func bar_fill_w(w: float, frac: float) -> int:
	return int(w * clampf(frac, 0.0, 1.0))


## Ukuran permukaan bayangan — port `_shadow`: `max(2, int(w) + spread * 2)`.
static func shadow_surface_size(w: float, h: float,
		spread: float = 4.0) -> Vector2i:
	return Vector2i(maxi(2, int(w) + int(spread) * 2),
		maxi(2, int(h) + int(spread) * 2))


## Ukuran sel kecil bayangan sebelum di-scale — port `max(4, w // 8)`.
static func shadow_small_size(w: float, h: float,
		spread: float = 4.0) -> Vector2i:
	var s := shadow_surface_size(w, h, spread)
	return Vector2i(maxi(4, int(floor(float(s.x) / 8.0))),
		maxi(4, int(floor(float(s.y) / 8.0))))


## Warna per pita gradasi teks — port loop `y` di `gradient_text()`
## (`int(top + (bottom - top) * t)`, t = y / (h - 1)) yang di sini
## dievaluasi di tengah pita supaya `n` pita mewakili seluruh tinggi glif.
static func gradient_bands(top: Color, bottom: Color, n: int) -> Array:
	var out: Array = []
	var bands := maxi(1, n)
	for i in range(bands):
		var t := (float(i) + 0.5) / float(bands)
		out.append(Color8(
			int(float(top.r8) + float(bottom.r8 - top.r8) * t),
			int(float(top.g8) + float(bottom.g8 - top.g8) * t),
			int(float(top.b8) + float(bottom.b8 - top.b8) * t)))
	return out


# ═══════════════════════════════════════════════════════════
# CACHE TEKSTUR (padanan _GLOW_CACHE / _SHADOW_CACHE pygame)
# ═══════════════════════════════════════════════════════════

static var _glow_cache: Dictionary = {}
static var _shadow_cache: Dictionary = {}


## Glow radial elips sebagai tekstur (port `_radial` baris demi baris,
## termasuk langkah 2px dan kuantisasi alpha kelipatan 8).
static func radial_texture(w: float, h: float, color: Color,
		alpha: int) -> ImageTexture:
	var ww := maxi(8, int(w))
	var hh := maxi(8, int(h))
	var a := radial_alpha_key(alpha)
	var key := "%d,%d,%s,%d" % [ww, hh, color.to_html(false), a]
	if _glow_cache.has(key):
		return _glow_cache[key] as ImageTexture
	var img := Image.create(ww, hh, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var cx := float(ww) / 2.0
	var cy := float(hh) / 2.0
	var maxd := hyp(cx, cy)
	for y in range(0, hh, 2):
		for x in range(0, ww, 2):
			var d := hyp(float(x) - cx, float(y) - cy) / maxd
			if d < 1.0:
				var aa := glow_alpha_at(a, d)
				if aa > 0:
					img.fill_rect(Rect2i(x, y, 2, 2),
						Color(color.r, color.g, color.b, float(aa) / 255.0))
	var tex := ImageTexture.create_from_image(img)
	_glow_cache[key] = tex
	return tex


## Bayangan lembut sebagai tekstur (port `_shadow`: persegi membulat di sel
## 1/8 ukuran lalu `smoothscale` ke ukuran penuh).
static func shadow_texture(w: float, h: float, radius: float = 12.0,
		alpha: int = 110, spread: float = 4.0) -> ImageTexture:
	var full := shadow_surface_size(w, h, spread)
	var key := "%d,%d,%d,%d" % [full.x, full.y, int(radius), alpha]
	if _shadow_cache.has(key):
		return _shadow_cache[key] as ImageTexture
	var small := shadow_small_size(w, h, spread)
	var img := Image.create(small.x, small.y, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	_fill_rounded(img, Rect2i(0, 0, small.x, small.y),
		Color(0, 0, 0, float(alpha) / 255.0),
		maxf(1.0, floor(float(radius) / 8.0)))
	# pygame.transform.smoothscale -> resize halus (Lanczos).
	img.resize(full.x, full.y, Image.INTERPOLATION_LANCZOS)
	var tex := ImageTexture.create_from_image(img)
	_shadow_cache[key] = tex
	return tex


## Isi persegi membulat ke Image (uji SDF per piksel; dipakai sel kecil
## bayangan — hanya puluhan piksel, jadi murah).
static func _fill_rounded(img: Image, rect: Rect2i, color: Color,
		radius: float) -> void:
	var r := minf(maxf(radius, 0.0),
		minf(float(rect.size.x), float(rect.size.y)) * 0.5)
	for y in range(rect.position.y, rect.end.y):
		var py := float(y) + 0.5
		var cy := clampf(py, float(rect.position.y) + r,
			float(rect.end.y) - r)
		for x in range(rect.position.x, rect.end.x):
			var px := float(x) + 0.5
			var cx := clampf(px, float(rect.position.x) + r,
				float(rect.end.x) - r)
			if Vector2(px, py).distance_to(Vector2(cx, cy)) <= r:
				img.set_pixel(x, y, color)


# ═══════════════════════════════════════════════════════════
# GEOMETRI & WARNA KOMPONEN (fungsi murni — satu sumber untuk
# jalur immediate-mode DI BAWAH dan widget Control di
# scenes/ui/widgets/; semuanya dikunci oracle pygame)
# ═══════════════════════════════════════════════════════════

## Rect hit-test tombol menu — port `button()`: `base.inflate(18, 8)` saat
## hover (quirk pygame dipertahankan: rect interaktif MELEBAR 9px x 4px).
static func button_hit_rect(cx: float, cy: float, w: float, h: float,
		hover: bool) -> Rect2:
	var base := Rect2(float(int(cx - floor(w / 2.0))),
		float(int(cy - floor(h / 2.0))), w, h)
	if hover:
		return Rect2(base.position - Vector2(9, 4),
			base.size + Vector2(18, 8))
	return base


## Gradasi tombol menu — port `button()`: hover (44,52,86)->(24,29,52),
## idle (34,41,70)->(17,21,38).
static func menu_button_colors(hover: bool) -> Array:
	if hover:
		return [Color8(44, 52, 86), Color8(24, 29, 52)]
	return [Color8(34, 41, 70), Color8(17, 21, 38)]


## Pusat label tombol menu — port clamp di `button()`: label digeser +14px
## (ruang badge ikon) lalu dijepit agar tidak menimpa badge (kiri) atau
## keluar tepi kanan; kalau tetap tidak muat, dipusatkan di antaranya.
static func button_label_cx(base_x: float, w: float, text_w: float,
		has_icon: bool, hit: Rect2) -> float:
	if not has_icon:
		return hit.get_center().x
	var left_min := hit.position.x + 56.0
	var right_max := hit.end.x - 10.0
	var text_cx := base_x + floor(w / 2.0) + 14.0
	if text_cx - text_w * 0.5 < left_min:
		text_cx = left_min + text_w * 0.5
	if text_cx + text_w * 0.5 > right_max:
		text_cx = right_max - text_w * 0.5
	if text_cx - text_w * 0.5 < left_min:
		text_cx = (left_min + right_max) * 0.5
	return text_cx


## Diameter knob toggle — port `knob = 18` di `toggle()` (satu sumber supaya
## widget PygameToggle dan jalur immediate-mode tidak bisa menyimpang).
static func toggle_knob_size() -> float:
	return 18.0


## Warna toggle — port `toggle()`: [top, bottom, edge] per (is_on, hover).
static func toggle_colors(is_on: bool, hover: bool) -> Array:
	if is_on:
		if hover:
			return [Color8(92, 214, 118), Color8(46, 138, 70),
				Color8(160, 255, 180)]
		return [Color8(70, 190, 96), Color8(34, 116, 58), Color8(120, 235, 145)]
	if hover:
		return [Color8(92, 96, 118), Color8(56, 60, 80), Color8(150, 156, 180)]
	return [Color8(74, 78, 100), Color8(44, 48, 68), Color8(120, 126, 150)]


## Warna tab — port `tab()`: [top, bottom, edge, text] per (active, hover).
## `accent` dipakai sebagai edge+text saat aktif.
static func tab_colors(active: bool, hover: bool, accent: Color) -> Array:
	if active:
		return [Color8(46, 56, 92), Color8(26, 32, 58), accent, accent]
	if hover:
		return [Color8(34, 39, 62), Color8(20, 24, 42), Color8(120, 130, 160),
			TEXT_BODY]
	return [Color8(22, 26, 44), Color8(15, 18, 32), Color8(72, 80, 106),
		TEXT_DIM]


## Gradasi chip status — port `chip()`: (32,38,64)->(18,22,40),
## fallback hemat (22,26,46).
static func chip_colors() -> Array:
	return [Color8(32, 38, 64), Color8(18, 22, 40), Color8(22, 26, 46)]


## Rect chip auto-size — port `chip()`: 26 + (22 kalau ada ikon) + lebar
## teks letter-spaced + (10 + lebar nilai kalau ada nilai), tinggi 30;
## `align == "right"` -> `pos` adalah sudut KANAN-atas.
static func chip_rect(pos: Vector2, text_w: float, value_w: float,
		has_icon: bool, has_value: bool, align: String = "left") -> Rect2:
	var total_w := 26.0
	if has_icon:
		total_w += 22.0
	total_w += text_w
	if has_value:
		total_w += 10.0 + value_w
	var h := 30.0
	var x := pos.x - total_w if align == "right" else pos.x
	return Rect2(x, pos.y, total_w, h)


## Ukuran chip untuk `custom_minimum_size` widget — mengukur teks dengan
## metrik font Godot lalu memakai rumus `chip_rect()` yang sama.
static func chip_size(text: String, font: Font, font_size: int,
		icon: String = "", value: String = "") -> Vector2:
	var spaced := letter(text)
	var text_w := font.get_string_size(spaced, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size).x
	var value_w := 0.0
	if not value.is_empty():
		value_w = font.get_string_size(value, HORIZONTAL_ALIGNMENT_LEFT, -1,
			font_size).x
	return chip_rect(Vector2.ZERO, text_w, value_w, not icon.is_empty(),
		not value.is_empty()).size


## Ukuran header section untuk `custom_minimum_size` widget — port
## `section_header()`: lebar = ikon(28) + judul + 14 + garis, tinggi 34.
static func section_header_size(title: String, font: Font, font_size: int,
		rule_w: float = 240.0) -> Vector2:
	var title_w := font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size).x
	return Vector2(title_w + 28.0 + 14.0 + rule_w, 34.0)


## Geometri header section — port `section_header()`. `title_w` = lebar
## JUDUL TANPA letter-spacing (pygame mengukur `title`, bukan `letter(title)`).
## Keluaran: ikon, teks, garis hairline aksen, garis redup, dan y berikutnya.
static func section_header_geom(pos: Vector2, title_w: float,
		rule_w: float = 240.0) -> Dictionary:
	var x := pos.x
	var y := pos.y
	var tw := title_w + 28.0
	return {
		"icon": Vector2(x + 10.0, y + 11.0),
		"text": Vector2(x + 28.0, y),
		"rule_from": Vector2(x + tw + 14.0, y + 14.0),
		"rule_to": Vector2(x + tw + 14.0 + rule_w, y + 14.0),
		"dim_from": Vector2(x + 28.0, y + 26.0),
		"dim_to": Vector2(x + tw + 14.0, y + 26.0),
		"next_y": y + 34.0,
	}


## Geometri slider — port `slider()`: track 8px, isi emas, knob di x+fill.
static func slider_geom(pos: Vector2, w: float, value: float) -> Dictionary:
	var track_h := 8.0
	var fill_w := float(bar_fill_w(w, value))
	return {
		"track": Rect2(pos, Vector2(w, track_h)),
		"fill_w": fill_w,
		"knob": Vector2(pos.x + fill_w, pos.y + floor(track_h / 2.0)),
	}


## Geometri cycler opsi — port `option_cycler()`: lebar kotak nilai mengikuti
## teks (`max(110, vw + 26)` lalu dibatasi `width - 66`), tombol chevron 24px
## di kiri/kanan kotak dengan jarak 6px.
static func cycler_geom(pos: Vector2, width: float,
		value_w: float) -> Dictionary:
	var vw := maxf(110.0, value_w + 26.0)
	vw = minf(vw, width - 66.0)
	var vh := 30.0
	var vx := pos.x + width - vw - 56.0
	var vy := pos.y + 7.0
	var box := Rect2(vx, vy, vw, vh)
	var bw := 24.0
	return {
		"label": Vector2(pos.x, pos.y + 10.0),
		"box": box,
		"prev": Rect2(box.position.x - bw - 6.0, vy, bw, vh),
		"next": Rect2(box.end.x + 6.0, vy, bw, vh),
		"next_y": vy + vh,
	}


## Rect thumb indikator scroll — port `scroll_indicator()`:
## `ratio = height / (height + max_scroll)`, `thumb_h = max(18, int(h*ratio))`,
## `thumb_y = y + int((height - thumb_h) * (scroll_pos / max_scroll))`.
static func scroll_thumb_rect(pos: Vector2, height: float, scroll_pos: float,
		max_scroll: float, width: float = 6.0) -> Rect2:
	var track := Rect2(pos, Vector2(width, height))
	if max_scroll <= 0.0:
		return Rect2(track.position, Vector2(width, 0))
	var ratio := height / (height + max_scroll)
	var thumb_h := float(maxi(18, int(height * ratio)))
	var thumb_y := pos.y + float(int((height - thumb_h)
		* (scroll_pos / max_scroll)))
	return Rect2(pos.x, thumb_y, width, thumb_h)


## Lebar tab auto — port `tab_width()`: `max(min_w, lebar(letter(label)) + 36)`.
## `measured_w` = lebar teks letter-spaced TERUKUR (metrik font milik engine
## masing-masing, jadi oracle memasukkan angka, bukan mengukur sendiri).
static func tab_width_for(measured_w: float, min_w: float = 150.0) -> float:
	return maxf(min_w, measured_w + 36.0)


## Rect tombol BACK — port `back_button()`: 200x42 di pusat (cx, y).
static func back_button_rect(cx: float, y: float) -> Rect2:
	return Rect2(cx - 100.0, y - 21.0, 200.0, 42.0)


## Geometri judul layar — port `screen_title()`: glow 620x150, ornamen di
## y+52 (garis ±220/±18, wajik, dot ±230), plate subtitle di fy+12 tinggi 44
## dengan lebar = teks + 56.
static func screen_title_geom(cx: float, y: float,
		sub_w: float = 0.0) -> Dictionary:
	var fy := y + 52.0
	# pygame: `cx - (lebar_sub + 56) // 2` -> pembagian bulat, bukan 0.5.
	var plate_w := sub_w + 56.0
	var plate := Rect2(cx - floor(plate_w / 2.0), fy + 12.0, plate_w, 44.0)
	return {
		"glow": Rect2(cx - 310.0, y - 62.0, 620.0, 150.0),
		"ornament_y": fy,
		"line_l": [Vector2(cx - 220.0, fy), Vector2(cx - 18.0, fy)],
		"line_r": [Vector2(cx + 18.0, fy), Vector2(cx + 220.0, fy)],
		"gem": [Vector2(cx - 8.0, fy), Vector2(cx, fy - 7.0),
			Vector2(cx + 8.0, fy), Vector2(cx, fy + 7.0)],
		"dot_l": Vector2(cx - 230.0, fy),
		"dot_r": Vector2(cx + 230.0, fy),
		"sub_plate": plate,
	}


# ═══════════════════════════════════════════════════════════
# KOMPONEN — JALUR IMMEDIATE-MODE (port 1:1 fungsi gambar
# ui_theme.py; `btns` = Dictionary id -> Rect2 supaya hit-test
# tetap satu jalur seperti Menu.handle_click pygame)
#
# Widget Control di scenes/ui/widgets/ memanggil *_visual() di
# bawah, jadi geometri/warna hanya punya SATU sumber.
# ═══════════════════════════════════════════════════════════

## Port `panel()` — panel kaca gelap: bayangan + gradasi + border + sudut emas.
static func draw_panel(cv: CanvasItem, rect: Rect2, border: Color = EDGE_GOLD,
		fill_top: Color = PANEL_TOP, fill_bottom: Color = PANEL_BOTTOM,
		ticks: bool = true, shadow: bool = true,
		border_w: float = 1.0) -> void:
	var r := pyrect(rect)
	if shadow and cheap_alpha():
		draw_shadow(cv, r, 12.0)
	elif shadow:
		draw_rr(cv, Rect2(r.position + Vector2(3, 4), r.size),
			Color8(6, 7, 14), 12.0)
	if cheap_alpha():
		draw_vgrad(cv, r, fill_top, fill_bottom, 12.0)
	else:
		draw_rr(cv, r, PANEL_FILL, 12.0)
	draw_rr_outline(cv, r, border, 12.0, border_w)
	if ticks:
		draw_corner_ticks(cv, r, GOLD)


## Port `panel_solid()` — panel tanpa alpha sama sekali (jalur hemat).
static func draw_panel_solid(cv: CanvasItem, rect: Rect2,
		border: Color = EDGE_GOLD) -> void:
	var r := pyrect(rect)
	draw_rr(cv, r, PANEL_FILL, 12.0)
	draw_rr_outline(cv, r, border, 12.0, 1.0)
	draw_corner_ticks(cv, r, GOLD)


## Visual tombol menu (tanpa registrasi hit-test) — port badan `button()`.
static func draw_button_visual(cv: CanvasItem, rect: Rect2, base: Rect2,
		label: String, accent: Color, font: Font, font_size: int,
		icon: String = "", hover: bool = false, letter_gap: bool = true,
		pressed: bool = false, enabled: bool = true,
		icon_scale: float = 0.9) -> void:
	var r := pyrect(rect)
	# Glow hover (radial di sekitar tombol).
	if hover and enabled:
		if cheap_alpha():
			draw_glow(cv, Rect2(r.position - Vector2(22, 18),
				r.size + Vector2(44, 36)), accent, 74.0 / 255.0)
		else:
			draw_rr_outline(cv, Rect2(r.position - Vector2(5, 5),
				r.size + Vector2(10, 10)), accent, 14.0, 2.0)
	# Bayangan (blit (x-2, y-2) — beda 2px dari panel, lihat draw_shadow).
	if cheap_alpha():
		draw_shadow(cv, r, 12.0, 110.0 / 255.0, 4.0, Vector2(-2, -2))
	# Panel tombol.
	var cols: Array = menu_button_colors(hover and enabled)
	var top: Color = cols[0]
	var bot: Color = cols[1]
	if pressed:
		top = top.darkened(0.12)
		bot = bot.darkened(0.12)
	if cheap_alpha():
		draw_vgrad(cv, r, top, bot, 12.0)
	else:
		draw_rr(cv, r, top, 12.0)
	# Sorot tepi atas.
	cv.draw_line(Vector2(r.position.x + 12, r.position.y + 1),
		Vector2(r.end.x - 12, r.position.y + 1), Color.WHITE, 1.0)
	# Aksen kiri (warna identitas) + glow lembutnya.
	draw_rr(cv, Rect2(r.position.x + 6, r.position.y + 10, 4,
		r.size.y - 20), accent, 2.0)
	if cheap_alpha():
		# pygame menulis `(*accent, 70)` ke permukaan display TANPA SRCALPHA,
		# jadi komponen alpha-nya DIABAIKAN dan strip 8px ini keluar opaque
		# (terverifikasi oracle: tools/test_godot_ui_theme_parity.py). Port
		# setia = opaque, bukan alpha 70/255.
		draw_rr(cv, Rect2(r.position.x + 4, r.position.y + 8, 8,
			r.size.y - 16), accent, 3.0)
	# Border.
	var bcol := accent if (hover and enabled) else EDGE_GOLD
	draw_rr_outline(cv, r, bcol, 12.0, 2.0 if (hover and enabled) else 1.0)
	# Sudut emas.
	draw_corner_ticks(cv, r, GOLD)
	# Badge ikon.
	var has_icon := not icon.is_empty()
	if has_icon:
		var ic := Vector2(r.position.x + 34, r.get_center().y)
		cv.draw_circle(ic, 17.0, Color8(12, 14, 26))
		cv.draw_arc(ic, 17.0, 0, TAU, 40, accent, 2.0)
		draw_icon(cv, icon, ic.x, ic.y, accent, icon_scale)
	# Label (clamp terhadap badge & tepi kanan).
	var text := letter(label) if letter_gap else label
	var tw := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size).x
	var text_cx := button_label_cx(base.position.x, base.size.x, tw,
		has_icon, r)
	var tcol := TEXT_WHITE if enabled else TEXT_FAINT
	draw_text_centered(cv, font, text, font_size, tcol,
		Vector2(text_cx, r.get_center().y))


## Port `button()` — tombol menu utama premium; kembalikan rect hit-test.
static func draw_button(cv: CanvasItem, btns: Dictionary, bid: String,
		label: String, center: Vector2, accent: Color, font: Font,
		font_size: int, w: float = 300.0, h: float = 50.0, icon: String = "",
		hover: bool = false, letter_gap: bool = true) -> Rect2:
	var base := Rect2(float(int(center.x - floor(w / 2.0))),
		float(int(center.y - floor(h / 2.0))), w, h)
	var hit := button_hit_rect(center.x, center.y, w, h, hover)
	draw_button_visual(cv, hit, base, label, accent, font, font_size, icon,
		hover, letter_gap)
	btns[bid] = hit
	return hit


## Visual pill (tanpa registrasi hit-test) — port badan `pill()`.
static func draw_pill_visual(cv: CanvasItem, rect: Rect2, kind: String,
		font: Font, font_size: int, label: String, hover: bool = false,
		enabled: bool = true, icon: String = "", letter_gap: bool = true,
		pressed: bool = false, icon_scale: float = 0.8) -> void:
	var r := pyrect(rect)
	var cols: Array = pill_colors(kind)
	var top: Color = cols[0]
	var bot: Color = cols[1]
	var edge: Color = cols[2]
	var tcol: Color = cols[3]
	if hover and enabled:
		top = add_rgb(top, 18)
		bot = add_rgb(bot, 14)
	if pressed:
		top = top.darkened(0.12)
		bot = bot.darkened(0.12)
	if cheap_alpha():
		draw_vgrad(cv, r, top, bot, 7.0)
	else:
		draw_rr(cv, r, top, 7.0)
	draw_rr_outline(cv, r, edge, 7.0, 2.0 if enabled else 1.0)
	if hover and enabled and cheap_alpha():
		draw_glow(cv, Rect2(r.position - Vector2(15, 12),
			r.size + Vector2(30, 24)), edge, 66.0 / 255.0)
	var cx := r.get_center().x
	if not icon.is_empty():
		draw_icon(cv, icon, r.position.x + 22, r.get_center().y, edge,
			icon_scale)
		cx = r.position.x + 22.0 + floor((r.size.x - 22.0) / 2.0)
	draw_text_centered(cv, font, letter(label) if letter_gap else label,
		font_size, tcol if enabled else TEXT_FAINT,
		Vector2(cx, r.get_center().y))


## Port `pill()` — tombol aksi kecil; hanya didaftarkan ke `btns` bila enabled
## (persis pygame: tombol mati tidak bisa diklik).
static func draw_pill(cv: CanvasItem, btns: Dictionary, bid: String,
		label: String, rect: Rect2, kind: String, font: Font, font_size: int,
		hover: bool = false, enabled: bool = true, icon: String = "",
		letter_gap: bool = true) -> Rect2:
	var r := pyrect(rect)
	draw_pill_visual(cv, r, kind, font, font_size, label, hover, enabled,
		icon, letter_gap)
	if enabled:
		btns[bid] = r
	return r


## Port `chip()` — chip status auto-size (ikon + label + nilai opsional).
static func draw_chip(cv: CanvasItem, pos: Vector2, text: String,
		accent: Color, font: Font, font_size: int, icon: String = "",
		icon_color = null, value = null, value_color = null,
		align: String = "left") -> Rect2:
	var spaced := letter(text)
	var text_w := font.get_string_size(spaced, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size).x
	var has_value := value != null
	var value_text := "" if value == null else str(value)
	var value_w := 0.0
	if has_value:
		value_w = font.get_string_size(value_text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	var r := pyrect(chip_rect(pos, text_w, value_w, not icon.is_empty(),
		has_value, align))
	var h := r.size.y
	if cheap_alpha():
		var cc: Array = chip_colors()
		draw_vgrad(cv, r, cc[0], cc[1], floor(h / 2.0))
	else:
		draw_rr(cv, r, Color8(22, 26, 46), floor(h / 2.0))
	draw_rr_outline(cv, r, accent, floor(h / 2.0), 1.0)
	var ix := r.position.x + 14.0
	var iy := r.get_center().y
	if not icon.is_empty():
		var icol: Color = accent if icon_color == null else Color(icon_color)
		draw_icon(cv, icon, ix, iy, icol, 0.75)
		ix += 22.0
	draw_text(cv, font, spaced, font_size, TEXT_BODY, Vector2(ix,
		r.position.y + 7.0), false)
	ix += text_w
	if has_value:
		ix += 10.0
		var vcol: Color = accent if value_color == null else Color(value_color)
		draw_text(cv, font, value_text, font_size, vcol,
			Vector2(ix, r.position.y + 7.0), false)
	return r


## Port `section_header()` — ikon + judul letter-spaced + dua garis hairline.
## Mengembalikan y berikutnya (y + 34).
static func draw_section_header(cv: CanvasItem, pos: Vector2, title: String,
		icon_name: String, color: Color, font: Font, font_size: int,
		rule_w: float = 240.0) -> float:
	var title_w := font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1,
		font_size).x
	var g := section_header_geom(pos, title_w, rule_w)
	draw_icon(cv, icon_name, (g["icon"] as Vector2).x, (g["icon"] as Vector2).y,
		color, 0.9)
	draw_text(cv, font, letter(title), font_size, color, g["text"] as Vector2,
		false)
	cv.draw_line(g["rule_from"] as Vector2, g["rule_to"] as Vector2, color, 1.0)
	cv.draw_line(g["dim_from"] as Vector2, g["dim_to"] as Vector2,
		dim(color), 1.0)
	return float(g["next_y"])


## Visual toggle (tanpa registrasi hit-test) — port badan `toggle()`.
static func draw_toggle_visual(cv: CanvasItem, rect: Rect2, is_on: bool,
		font: Font, font_size: int, hover: bool = false) -> void:
	var r := pyrect(rect)
	var cols: Array = toggle_colors(is_on, hover)
	var top: Color = cols[0]
	var bot: Color = cols[1]
	var edge: Color = cols[2]
	if cheap_alpha():
		draw_vgrad(cv, r, top, bot, floor(r.size.y / 2.0))
	else:
		draw_rr(cv, r, top, floor(r.size.y / 2.0))
	draw_rr_outline(cv, r, edge, floor(r.size.y / 2.0), 2.0)
	# Knob (bayangan gelap 1px, cincin warna tepi).
	var knob := toggle_knob_size()
	var kx := r.end.x - knob - 6.0 if is_on else r.position.x + 6.0
	var ky := r.get_center().y
	cv.draw_circle(Vector2(kx + 1, ky + 2), knob * 0.5, Color8(12, 14, 24))
	cv.draw_circle(Vector2(kx, ky), knob * 0.5, Color8(245, 248, 255))
	cv.draw_arc(Vector2(kx, ky), knob * 0.5, 0, TAU, 24, edge, 1.0)
	# Label di sisi berlawanan knob.
	var lx := r.position.x + floor(r.size.x / 2.0) - 8.0 if is_on \
		else r.position.x + floor(r.size.x / 2.0) + 8.0
	draw_text_centered(cv, font, "ON" if is_on else "OFF", font_size,
		Color8(210, 255, 220) if is_on else TEXT_BODY, Vector2(lx, ky), false)


## Port `toggle()` — sakelar pill ON/OFF.
static func draw_toggle(cv: CanvasItem, btns: Dictionary, bid: String,
		rect: Rect2, is_on: bool, font: Font, font_size: int,
		hover: bool = false) -> Rect2:
	var r := pyrect(rect)
	draw_toggle_visual(cv, r, is_on, font, font_size, hover)
	btns[bid] = r
	return r


## Port `slider()` — track + isi emas + knob cincin; kembalikan x knob
## (dipakai pemanggil pygame untuk menaruh tombol -/+).
static func draw_slider(cv: CanvasItem, pos: Vector2, w: float, value: float,
		knob_hover: bool = false) -> float:
	var g := slider_geom(pos, w, value)
	var track: Rect2 = g["track"]
	var fill_w: float = g["fill_w"]
	var knob: Vector2 = g["knob"]
	draw_rr(cv, track, Color8(34, 38, 58), 4.0)
	if fill_w > 4.0:
		if cheap_alpha():
			draw_vgrad(cv, Rect2(track.position, Vector2(fill_w,
				track.size.y)), GOLD_BRIGHT, Color8(196, 138, 40), 4.0)
		else:
			draw_rr(cv, Rect2(track.position, Vector2(fill_w, track.size.y)),
				GOLD, 4.0)
	draw_rr_outline(cv, track, Color8(120, 110, 86), 4.0, 1.0)
	if knob_hover and cheap_alpha():
		draw_glow(cv, Rect2(knob - Vector2(18, 18), Vector2(36, 36)), GOLD,
			80.0 / 255.0)
	cv.draw_circle(knob, 11.0, Color8(12, 14, 24))
	cv.draw_circle(knob, 8.0, Color8(245, 248, 255))
	cv.draw_arc(knob, 8.0, 0, TAU, 28, GOLD, 2.0)
	return knob.x


## Port `option_cycler()` — label + kotak nilai auto-width + chevron < >.
## Mengembalikan y berikutnya (vy + 30). `hover` = id tombol yang sedang
## disorot ("" kalau tidak ada) — pygame membandingkan dengan `id_base +
## "_prev"/"_next"`.
static func draw_option_cycler(cv: CanvasItem, btns: Dictionary,
		id_base: String, label_text: String, value_text: String, pos: Vector2,
		width: float, label_font: Font, label_size: int, value_font: Font,
		value_size: int, hover: String = "") -> float:
	draw_text(cv, label_font, label_text, label_size, TEXT_BODY,
		Vector2(pos.x, pos.y + 10.0), false)
	var value_w := value_font.get_string_size(value_text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, value_size).x
	var g := cycler_geom(pos, width, value_w)
	var box: Rect2 = pyrect(g["box"])
	var prev_rect: Rect2 = pyrect(g["prev"])
	var next_rect: Rect2 = pyrect(g["next"])
	var box_hover := hover == id_base + "_prev" or hover == id_base + "_next"
	if cheap_alpha():
		draw_vgrad(cv, box, Color8(40, 48, 80), Color8(20, 24, 44), 6.0)
	else:
		draw_rr(cv, box, Color8(28, 34, 58), 6.0)
	draw_rr_outline(cv, box, EDGE_GOLD if box_hover else Color8(96, 106, 138),
		6.0, 1.0)
	draw_text_centered(cv, value_font, value_text, value_size, GOLD_TEXT,
		box.get_center(), false)
	var sides: Array = [
		[prev_rect, id_base + "_prev", "chevron_l"],
		[next_rect, id_base + "_next", "chevron_r"],
	]
	for side in sides:
		var b: Rect2 = side[0]
		var bid: String = side[1]
		var icon: String = side[2]
		var bh := hover == bid
		var top := Color8(64, 74, 110) if bh else Color8(42, 48, 74)
		if cheap_alpha():
			draw_vgrad(cv, b, top, Color8(26, 30, 52), 6.0)
		else:
			draw_rr(cv, b, top, 6.0)
		draw_rr_outline(cv, b,
			Color8(150, 160, 196) if bh else Color8(96, 106, 138), 6.0, 1.0)
		draw_icon(cv, icon, b.get_center().x, b.get_center().y,
			Color8(200, 210, 240), 0.6)
		btns[bid] = b
	return float(g["next_y"])


## Visual tab (tanpa registrasi hit-test) — port badan `tab()`.
static func draw_tab_visual(cv: CanvasItem, rect: Rect2, label_text: String,
		accent: Color, font: Font, font_size: int, active: bool,
		hover: bool = false) -> void:
	var r := pyrect(rect)
	var cols: Array = tab_colors(active, hover, accent)
	var top: Color = cols[0]
	var bot: Color = cols[1]
	var edge: Color = cols[2]
	var tcol: Color = cols[3]
	if cheap_alpha():
		draw_vgrad(cv, r, top, bot, 8.0)
	else:
		draw_rr(cv, r, top, 8.0)
	draw_rr_outline(cv, r, edge, 8.0, 2.0 if active else 1.0)
	if active:
		# Underline aksen 3px di dasar tab.
		draw_rr(cv, Rect2(r.position.x + 8, r.end.y - 4, r.size.x - 16, 3),
			accent, 1.0)
	draw_text_centered(cv, font, letter(label_text), font_size, tcol,
		r.get_center(), false)


## Port `tab()` — tab kategori (hero shop / toko item).
static func draw_tab(cv: CanvasItem, btns: Dictionary, bid: String,
		rect: Rect2, label_text: String, accent: Color, font: Font,
		font_size: int, active: bool, hover: bool = false) -> Rect2:
	var r := pyrect(rect)
	draw_tab_visual(cv, r, label_text, accent, font, font_size, active, hover)
	btns[bid] = r
	return r


## Port `tab_width()` — lebar tab mengikuti teks letter-spaced TERUKUR.
static func tab_width(font: Font, font_size: int, label_text: String,
		min_w: float = 150.0) -> float:
	var measured := font.get_string_size(letter(label_text),
		HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	return tab_width_for(measured, min_w)


## Port `screen_title()` — glow + judul outline + ornamen + plate subtitle.
static func draw_screen_title(cv: CanvasItem, text: String, cx: float,
		y: float, glow: bool = true, sub: String = "",
		sub_color: Color = CYAN_SOFT, ornament: bool = true,
		title_size: int = 64, sub_size: int = 30) -> void:
	var sub_w := 0.0
	if not sub.is_empty():
		sub_w = body_semibold().get_string_size(letter(sub),
			HORIZONTAL_ALIGNMENT_LEFT, -1, sub_size).x
	var g := screen_title_geom(cx, y, sub_w)
	if glow and cheap_alpha():
		draw_glow(cv, g["glow"] as Rect2, Color8(255, 205, 90),
			46.0 / 255.0)
	draw_outline_text(cv, title_font(), text, title_size, Vector2(cx, y))
	if ornament:
		draw_title_ornament(cv, g)
	if not sub.is_empty():
		draw_title_sub(cv, g, sub, sub_color, sub_size)


## Ornamen judul layar "garis - wajik - garis" (bagian dari `screen_title()`;
## juga dipakai widget Flourish/ScreenTitle supaya geometrinya satu sumber).
static func draw_title_ornament(cv: CanvasItem, geom: Dictionary) -> void:
	var ll: Array = geom["line_l"]
	var lr: Array = geom["line_r"]
	var gem: Array = geom["gem"]
	cv.draw_line(ll[0] as Vector2, ll[1] as Vector2, EDGE_GOLD, 2.0)
	cv.draw_line(lr[0] as Vector2, lr[1] as Vector2, EDGE_GOLD, 2.0)
	_poly(cv, [gem[0] as Vector2, gem[1] as Vector2,
		gem[2] as Vector2, gem[3] as Vector2], GOLD)
	cv.draw_circle(geom["dot_l"] as Vector2, 3.0, GOLD_BRIGHT)
	cv.draw_circle(geom["dot_r"] as Vector2, 3.0, GOLD_BRIGHT)


## Plate subtitle judul layar (bagian dari `screen_title()`): plate 44px
## gradasi (26,32,58)->(14,18,34) + border emas + sudut emas 8px + teks
## letter-spaced Barlow-SemiBold.
static func draw_title_sub(cv: CanvasItem, geom: Dictionary, sub: String,
		sub_color: Color = CYAN_SOFT, sub_size: int = 30) -> void:
	var plate: Rect2 = geom["sub_plate"]
	if cheap_alpha():
		draw_vgrad(cv, plate, Color8(26, 32, 58), Color8(14, 18, 34), 10.0)
	else:
		draw_rr(cv, plate, Color8(16, 20, 38), 10.0)
	draw_rr_outline(cv, plate, EDGE_GOLD, 10.0, 1.0)
	draw_corner_ticks(cv, plate, GOLD, 8.0, 1.0, 3.0)
	draw_text_centered(cv, body_semibold(), letter(sub), sub_size, sub_color,
		plate.get_center(), false)


## Port `back_button()` — tombol BACK seragam (200x42, netral, ikon panah).
static func draw_back_button(cv: CanvasItem, btns: Dictionary, bid: String,
		cx: float, y: float, hover: bool = false, label_text: String = "BACK",
		font_size: int = 26) -> Rect2:
	var r := back_button_rect(cx, y)
	return draw_pill(cv, btns, bid, label_text, r, "neutral", body_semibold(),
		font_size, hover, true, "back")


## Port `scroll_indicator()` — indikator scroll ramping; kembalikan track.
static func draw_scroll_indicator(cv: CanvasItem, pos: Vector2, height: float,
		scroll_pos: float, max_scroll: float,
		width: float = 6.0) -> Rect2:
	var track := Rect2(pos, Vector2(width, height))
	draw_rr(cv, track, Color8(28, 32, 52), 3.0)
	if max_scroll > 0.0:
		var thumb := scroll_thumb_rect(pos, height, scroll_pos, max_scroll,
			width)
		if thumb.size.y > 0.0:
			if cheap_alpha():
				draw_vgrad(cv, thumb, GOLD_BRIGHT, Color8(196, 138, 40), 3.0)
			else:
				draw_rr(cv, thumb, GOLD, 3.0)
	return track


# ═══════════════════════════════════════════════════════════
# IKON VEKTOR — daftar tertutup (closed world)
# ═══════════════════════════════════════════════════════════

## 29 nama ikon yang dikenali `draw_icon()` — sama persis dengan cabang
## `if name == ...` di `ui_theme.draw_icon`. Oracle
## tools/test_godot_ui_theme_parity.py membandingkan daftar ini dengan nama
## yang diparse dari ui_theme.py, jadi ikon baru di pygame yang belum diport
## langsung gagal di CI.
const ICON_NAMES := ["back", "bolt", "check", "chevron_l", "chevron_r",
	"cloud", "coin", "continue", "crown", "download", "gear", "gem", "heart",
	"help", "lock", "minus", "monitor", "pad", "play", "plus", "quit",
	"shield", "skull", "speaker", "star", "swords", "trophy", "upload", "warn"]


## Daftar nama ikon (lihat ICON_NAMES).
static func icon_names() -> Array:
	return Array(ICON_NAMES)


## True kalau nama ikon dikenali `draw_icon()` (pygame: cabang if/elif tidak
## menggambar apa pun untuk nama tak dikenal).
static func has_icon(icon_name: String) -> bool:
	return ICON_NAMES.has(icon_name)
