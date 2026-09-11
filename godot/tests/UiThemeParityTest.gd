extends Node
## Tes paritas ui_theme.py <-> godot/scripts/utils/UiTheme.gd + widget-nya.
##
## Semua angka pembanding datang dari fixture yang direkam ORACLE PYTHON
## (tools/test_godot_ui_theme_parity.py). Oracle itu memanggil fungsi pygame
## ASLI dengan permukaan + font palsu lalu merekam:
##   * warna per baris `_vgrad`/`gradient_text` dan alpha per blok `_radial`
##     -> matematika gradasi & glow terkunci per kanal,
##   * KUNCI cache `_GRAD_CACHE`/`_GLOW_CACHE` yang terpakai tiap komponen
##     -> (w, h, top, bottom, radius) dan (w, h, color, alpha) persis,
##   * rect hit-test, pusat label hasil clamp (dibaca dari piksel TEXT_WHITE),
##     rentang garis section_header, thumb scroll, geometri cycler/slider.
##
## Font palsu oracle = 7 px/karakter. Karena itu sisi Godot memasukkan LEBAR
## TERUKUR yang sama ke fungsi murninya (chip_rect, cycler_geom,
## tab_width_for, button_label_cx, section_header_geom) — geometri terkunci
## tanpa bergantung metrik font engine mana pun.
##
## Jalankan:
##   godot --headless --path godot res://tests/UiThemeParityTest.tscn \
##       --quit-after 200
## Regenerasi fixture (setelah ui_theme.py berubah):
##   python3 tools/test_godot_ui_theme_parity.py --write-fixture

const FIXTURE := "res://tests/fixtures/ui_theme.json"
const LABEL := "UiThemeParityTest"

## Warna literal pygame yang direkam oracle dari kunci cache (bukan palet).
const GOLD_DEEP_BODY := Color8(196, 138, 40)

var _fx: Dictionary = {}
var _checks := 0
var _failures := 0
var _done := false
var _errors: Array[String] = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_load_fixture()
	if _failures == 0:
		_test_palette_live()
		_test_math()
		_test_panel()
		_test_button()
		_test_pill()
		_test_chip()
		_test_section_header()
		_test_toggle()
		_test_slider()
		_test_cycler()
		_test_tab()
		_test_screen_title()
		_test_back_button()
		_test_scroll()
		_test_bars()
		_test_gradient_text()
		_test_icons()
		_test_widgets()
		await _test_draw_smoke()
		await _test_widgets_in_tree()
		_test_caches()
	_finish()


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════

func _load_fixture() -> void:
	var parsed: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(FIXTURE))
	_expect(parsed is Dictionary,
		"fixture ui_theme.json terbaca (jalankan python3 tools/"
		+ "test_godot_ui_theme_parity.py --write-fixture)")
	if parsed is Dictionary:
		_fx = parsed


func _sec(section: String) -> Dictionary:
	var v: Variant = _fx.get(section)
	_expect(v is Dictionary, "seksi fixture \"%s\" ada" % section)
	return v if v is Dictionary else {}


func _cases(section: String) -> Array:
	var v: Variant = _sec(section).get("cases")
	_expect(v is Array, "seksi fixture \"%s\" punya cases" % section)
	return v if v is Array else []


func _col(rgb: Variant) -> Color:
	return Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))


func _rgb(c: Color) -> Array:
	return [c.r8, c.g8, c.b8]


func _rect4(a: Array) -> Rect2:
	return Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3]))


func _num(v: Variant) -> float:
	return float(v)


## Rect pygame bulat; Godot float -> toleransi setengah piksel.
func _expect_rect(got: Rect2, want: Array, msg: String) -> void:
	var parts := ["x", "y", "w", "h"]
	var got4 := [got.position.x, got.position.y, got.size.x, got.size.y]
	for i in 4:
		_expect_near(float(got4[i]), float(want[i]), 0.51,
			"%s.%s" % [msg, parts[i]])


func _expect_near(got: float, want: float, tol: float, msg: String) -> void:
	_checks += 1
	if absf(got - want) > tol:
		_fail("%s: dapat %.4f, mau %.4f (tol %.3f)" % [msg, got, want, tol])


func _expect_color(got: Color, want: Variant, msg: String) -> void:
	_checks += 1
	var target := _col(want)
	if got.r8 != target.r8 or got.g8 != target.g8 or got.b8 != target.b8:
		_fail("%s: dapat %s, mau %s" % [msg, _rgb(got), want])


## Kunci `_GRAD_CACHE` pygame: (w, h, top, bottom, radius) — persis.
func _expect_grad(got: Dictionary, want: Variant, msg: String) -> void:
	_expect(want is Dictionary, "%s: kunci gradasi terekam" % msg)
	if not (want is Dictionary):
		return
	_expect_near(_num(got["w"]), _num(want["w"]), 0.51, "%s.w" % msg)
	_expect_near(_num(got["h"]), _num(want["h"]), 0.51, "%s.h" % msg)
	_expect_color(got["top"], want["top"], "%s.top" % msg)
	_expect_color(got["bottom"], want["bottom"], "%s.bottom" % msg)
	_expect_near(_num(got["radius"]), _num(want["radius"]), 0.51,
		"%s.radius" % msg)


## Kunci `_GLOW_CACHE` pygame: (w, h, color, alpha_terkuantisasi).
func _expect_glow(got: Dictionary, want: Variant, msg: String) -> void:
	_expect(want is Dictionary, "%s: kunci glow terekam" % msg)
	if not (want is Dictionary):
		return
	_expect_near(_num(got["w"]), _num(want["w"]), 0.51, "%s.w" % msg)
	_expect_near(_num(got["h"]), _num(want["h"]), 0.51, "%s.h" % msg)
	_expect_color(got["color"], want["color"], "%s.color" % msg)
	_expect(int(got["alpha"]) == int(want["alpha"]),
		"%s.alpha: dapat %d, mau %d" % [msg, int(got["alpha"]),
		int(want["alpha"])])


func _expect(cond: bool, msg: String) -> void:
	_checks += 1
	if not cond:
		_fail(msg)


func _expect_deep(a: Variant, b: Variant, msg: String) -> void:
	_checks += 1
	if not _deep_eq(a, b):
		_fail("%s: dapat %s, mau %s" % [msg, _canon(a), _canon(b)])


func _fail(msg: String) -> void:
	var line := "[%s] %s" % [LABEL, msg]
	_errors.append(line)
	_failures += 1
	push_error(line)


func _deep_eq(a: Variant, b: Variant) -> bool:
	if a is Array and b is Array:
		if (a as Array).size() != (b as Array).size():
			return false
		for i in (a as Array).size():
			if not _deep_eq(a[i], b[i]):
				return false
		return true
	if a is Dictionary and b is Dictionary:
		if (a as Dictionary).size() != (b as Dictionary).size():
			return false
		for k in a:
			if not b.has(k) or not _deep_eq(a[k], b[k]):
				return false
		return true
	return a == b


func _canon(v: Variant) -> String:
	var text := str(v)
	if text.length() > 300:
		return text.substr(0, 300) + "…"
	return text


func _font(weight: String) -> Font:
	var f := UiTheme.font_for_weight(weight)
	if f == null:
		f = ThemeDB.fallback_font
	return f


# ══════════════════════════════════════════════════════════
#  PALET (seksi "palette_live")
# ══════════════════════════════════════════════════════════

func _test_palette_live() -> void:
	var live := _sec("palette_live")
	# Tabel 32 warna juga dibandingkan ketat dua arah di sisi Python (statik,
	# dari sumber .gd). Di sini tiap konstanta dibandingkan terhadap NILAI
	# RUNTIME modul pygame — bukan salinan angka.
	var mine := {
		"BG_DEEP": UiTheme.BG_DEEP,
		"PANEL_TOP": UiTheme.PANEL_TOP,
		"PANEL_BOTTOM": UiTheme.PANEL_BOTTOM,
		"PANEL_FILL": UiTheme.PANEL_FILL,
		"GOLD": UiTheme.GOLD,
		"GOLD_BRIGHT": UiTheme.GOLD_BRIGHT,
		"GOLD_DEEP": UiTheme.GOLD_DEEP,
		"GOLD_TEXT": UiTheme.GOLD_TEXT,
		"EDGE_GOLD": UiTheme.EDGE_GOLD,
		"EDGE_GOLD_DIM": UiTheme.EDGE_GOLD_DIM,
		"CYAN": UiTheme.CYAN,
		"CYAN_SOFT": UiTheme.CYAN_SOFT,
		"VIOLET": UiTheme.VIOLET,
		"ORANGE": UiTheme.ORANGE,
		"GREEN": UiTheme.GREEN,
		"GREEN_DEEP": UiTheme.GREEN_DEEP,
		"RED": UiTheme.RED,
		"RED_DEEP": UiTheme.RED_DEEP,
		"SLATE": UiTheme.SLATE,
		"TEXT_WHITE": UiTheme.TEXT_WHITE,
		"TEXT_BODY": UiTheme.TEXT_BODY,
		"TEXT_DIM": UiTheme.TEXT_DIM,
		"TEXT_FAINT": UiTheme.TEXT_FAINT,
		"LOCKED_BG_TOP": UiTheme.LOCKED_BG_TOP,
		"LOCKED_BG_BOTTOM": UiTheme.LOCKED_BG_BOTTOM,
		"LOCKED_EDGE": UiTheme.LOCKED_EDGE,
		"DONE_BG_TOP": UiTheme.DONE_BG_TOP,
		"DONE_BG_BOTTOM": UiTheme.DONE_BG_BOTTOM,
		"DONE_EDGE": UiTheme.DONE_EDGE,
		"OPEN_BG_TOP": UiTheme.OPEN_BG_TOP,
		"OPEN_BG_BOTTOM": UiTheme.OPEN_BG_BOTTOM,
		"OPEN_EDGE": UiTheme.OPEN_EDGE,
	}
	_expect(mine.size() == live.size(),
		"jumlah warna palet %d == %d" % [mine.size(), live.size()])
	for key in live:
		_expect(mine.has(key), "konstanta Godot %s ada" % key)
		if mine.has(key):
			_expect_color(mine[key], live[key], "palet %s" % key)
	# Bayangan teks pygame (5,6,12) = TEXT_SHADOW di Godot.
	_expect_color(UiTheme.TEXT_SHADOW, [5, 6, 12], "TEXT_SHADOW")


# ══════════════════════════════════════════════════════════
#  MATEMATIKA (seksi "math")
# ══════════════════════════════════════════════════════════

func _test_math() -> void:
	var m := _sec("math")

	# _vgrad: warna tiap baris, per kanal, persis pygame.
	for case in m["vgrad"]:
		var top := _col(case["top"])
		var bottom := _col(case["bottom"])
		var rows: Array = case["rows"]
		for y in rows.size():
			_expect_color(UiTheme.vgrad_row_color(top, bottom, y,
				int(case["h"])), rows[y],
				"vgrad_row_color(h=%d,y=%d)" % [int(case["h"]), y])

	# _radial: kuantisasi alpha + alpha per blok 2px + tekstur jadi.
	for case in m["radial"]:
		var ww := int(case["w"])
		var hh := int(case["h"])
		var alpha := int(case["alpha"])
		_expect(UiTheme.radial_alpha_key(alpha) == int(case["alpha_key"]),
			"radial_alpha_key(%d) == %d" % [alpha, int(case["alpha_key"])])
		var color := _col(case["color"])
		var tex := UiTheme.radial_texture(ww, hh, color, alpha)
		_expect(tex != null, "radial_texture(%d,%d) jadi" % [ww, hh])
		var cx := ww / 2.0
		var cy := hh / 2.0
		var maxd := UiTheme.hyp(cx, cy)
		for sample in case["samples"]:
			var x := int(sample["x"])
			var y := int(sample["y"])
			var d := UiTheme.hyp(float(x) - cx, float(y) - cy) / maxd
			_expect(UiTheme.glow_alpha_at(int(case["alpha_key"]), d)
				== int(sample["a"]),
				"glow_alpha_at(%d,%d) w=%d h=%d a=%d" % [x, y, ww, hh,
				int(sample["a"])])
			if tex != null:
				_expect(int(tex.get_image().get_pixel(x, y).a8)
					== int(sample["a"]),
					"piksel radial_texture(%d,%d) w=%d h=%d" % [x, y, ww, hh])

	# _shadow: ukuran permukaan + sel kecil + tekstur.
	for case in m["shadow"]:
		var w := _num(case["w"])
		var h := _num(case["h"])
		var spread := _num(case["spread"])
		var want := Vector2i(int(case["size"][0]), int(case["size"][1]))
		_expect(UiTheme.shadow_surface_size(w, h, spread) == want,
			"shadow_surface_size(%d,%d,%d) == %s" % [int(w), int(h),
			int(spread), want])
		var want_small := Vector2i(int(case["small"][0]),
			int(case["small"][1]))
		_expect(UiTheme.shadow_small_size(w, h, spread) == want_small,
			"shadow_small_size(%d,%d) == %s" % [int(w), int(h), want_small])
		var tex := UiTheme.shadow_texture(w, h, _num(case["radius"]),
			int(case["alpha"]), spread)
		_expect(tex != null and Vector2i(tex.get_width(), tex.get_height())
			== want, "shadow_texture(%d,%d) berukuran %s" % [int(w), int(h),
			want])

	# _dim.
	for case in m["dim"]:
		_expect_color(UiTheme.dim(_col(case["color"]), _num(case["f"])),
			case["out"], "dim(%s,%s)" % [case["color"], case["f"]])

	# letter().
	for case in m["letter"]:
		_expect(UiTheme.letter(str(case["text"]), str(case["gap"]))
			== str(case["out"]),
			"letter('%s','%s')" % [case["text"], case["gap"]])

	# math_hyp().
	for case in m["hyp"]:
		_expect_near(UiTheme.hyp(_num(case["x"]), _num(case["y"])),
			_num(case["out"]), 0.000000001,
			"hyp(%s,%s)" % [case["x"], case["y"]])

	# fit_ellipsis(): metrik font Godot beda dari FakeFont oracle, jadi yang
	# dikunci ATURANNYA (dihitung ulang di sini dari metrik font yang sama).
	var font := _font("body_regular")
	if font == null:
		return
	var size := 16
	for case in m["ellipsis"]:
		var text := str(case["text"])
		var max_w := _num(case["max_w"])
		var out := UiTheme.fit_ellipsis(font, size, text, max_w)
		var full := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			size).x
		var tag := "fit_ellipsis('%s',%d)" % [text, int(max_w)]
		if full <= max_w:
			_expect(out == text, "%s -> teks utuh" % tag)
			continue
		_expect(out != text, "%s -> terpotong" % tag)
		var ell := "…" if UiTheme.has_glyph(font, "…") else "..."
		_expect(out.ends_with(ell), "%s -> berakhiran elipsis" % tag)
		var kept := out.substr(0, out.length() - ell.length())
		_expect(text.begins_with(kept),
			"%s -> sisa teks adalah prefix aslinya" % tag)
		_expect(font.get_string_size(out, HORIZONTAL_ALIGNMENT_LEFT, -1,
			size).x <= max_w, "%s -> muat di max_w" % tag)
		# Satu karakter lebih panjang harus sudah melewati batas.
		if kept.length() < text.length():
			var longer := text.substr(0, kept.length() + 1) + ell
			_expect(font.get_string_size(longer, HORIZONTAL_ALIGNMENT_LEFT,
				-1, size).x > max_w, "%s -> prefix terpanjang" % tag)


# ══════════════════════════════════════════════════════════
#  PANEL (seksi "panel")
# ══════════════════════════════════════════════════════════

func _test_panel() -> void:
	var sec := _sec("panel")
	var keys: Array = sec["grad"]
	_expect(keys.size() == 1, "panel: satu kunci gradasi")
	if keys.is_empty():
		return
	var key: Dictionary = keys[0]
	var size := Vector2(_num(key["w"]), _num(key["h"]))
	_expect_grad({"w": size.x, "h": size.y, "top": UiTheme.PANEL_TOP,
		"bottom": UiTheme.PANEL_BOTTOM, "radius": 12.0}, key,
		"panel gradasi PANEL_TOP->PANEL_BOTTOM r12")
	_expect_color(UiTheme.PANEL_FILL, sec["solid_fill"],
		"PANEL_FILL (jalur hemat panel_solid)")
	_expect(UiTheme.shadow_surface_size(size.x, size.y, 4.0)
		== Vector2i(int(sec["shadow_size"][0]), int(sec["shadow_size"][1])),
		"panel shadow_surface_size")
	_expect(UiTheme.shadow_small_size(size.x, size.y, 4.0)
		== Vector2i(int(sec["shadow_small"][0]), int(sec["shadow_small"][1])),
		"panel shadow_small_size")
	# Radius 12 juga yang dipakai StyleBox (widget PygamePanel).
	var style := UiTheme.panel_style()
	_expect(style.corner_radius_top_left == 12
		and style.corner_radius_bottom_right == 12, "panel_style radius 12")
	_expect_color(style.border_color,
		_sec("palette_live")["EDGE_GOLD"], "panel_style border EDGE_GOLD")


# ══════════════════════════════════════════════════════════
#  BUTTON (seksi "button")
# ══════════════════════════════════════════════════════════

func _test_button() -> void:
	var sec := _sec("button")
	for case in sec["cases"]:
		var hover: bool = case["hover"]
		var tag := "button(hover=%s,icon=%s)" % [hover, case["icon"]]
		var hit := UiTheme.button_hit_rect(350.0, 170.0, 300.0, 50.0, hover)
		_expect_rect(hit, case["rect"], tag + " rect")
		_expect_deep(case["btns"]["b"], case["rect"], tag + " btns == rect")
		var cols: Array = UiTheme.menu_button_colors(hover)
		_expect_grad({"w": hit.size.x, "h": hit.size.y, "top": cols[0],
			"bottom": cols[1], "radius": 12.0}, case["grad"][0],
			tag + " gradasi")
		# Border: EDGE_GOLD saat idle, accent saat hover (piksel asli pygame).
		var want_edge: Variant = case["border_px"]
		_expect_color(UiTheme.GOLD if hover else UiTheme.EDGE_GOLD, want_edge,
			tag + " border")
		var glows: Array = case["glow"]
		if hover:
			_expect(glows.size() == 1, tag + " glow terekam")
			if glows.size() == 1:
				_expect_glow({"w": hit.size.x + 44.0,
					"h": hit.size.y + 36.0, "color": UiTheme.GOLD,
					"alpha": UiTheme.radial_alpha_key(74)}, glows[0],
					tag + " glow (+44/+36, alpha 74)")
		else:
			_expect(glows.is_empty(), tag + " tanpa glow")
		# Bayangan tombol: spread 4 -> permukaan membesar 8px dua arah.
		_expect(UiTheme.shadow_surface_size(hit.size.x, hit.size.y, 4.0)
			== Vector2i(int(hit.size.x) + 8, int(hit.size.y) + 8),
			tag + " ukuran bayangan")

	# Pusat label: oracle membaca piksel TEXT_WHITE hasil render pygame,
	# termasuk tombol sempit tempat badge ikon mendorong label ke kanan.
	for entry in sec["labels"]:
		var hit := _rect4(entry["rect"])
		var text_w := _num(entry["text_w"])
		var tag := "button_label_cx(w=%d,tw=%d,icon=%s,gap=%s)" \
			% [int(entry["w"]), int(text_w), entry["has_icon"],
			entry["letter_gap"]]
		var got := UiTheme.button_label_cx(hit.position.x, _num(entry["w"]),
			text_w, bool(entry["has_icon"]), hit)
		_expect_near(got, _num(entry["center"]), 1.0, tag)
		# Blok piksel harus selebar teks terukur (letter() ikut terhitung).
		var block: Array = entry["block"]
		_expect_near(_num(block[1]) - _num(block[0]), text_w, 1.0,
			tag + " lebar blok piksel")


# ══════════════════════════════════════════════════════════
#  PILL (seksi "pill")
# ══════════════════════════════════════════════════════════

func _test_pill() -> void:
	var sec := _sec("pill")
	var table: Dictionary = sec["table"]
	_expect(table.size() == 8, "tabel pill 8 kind (dapat %d)" % table.size())
	for kind in table:
		var got: Array = UiTheme.pill_colors(str(kind))
		_expect(got.size() == 4, "pill_colors('%s') 4 warna" % kind)
		if got.size() == 4:
			_expect_color(got[0], table[kind][0], "pill %s top" % kind)
			_expect_color(got[1], table[kind][1], "pill %s bottom" % kind)
			_expect_color(got[2], table[kind][2], "pill %s edge" % kind)
			_expect_color(got[3], table[kind][3], "pill %s teks" % kind)
	# Kind tak dikenal -> neutral (persis `colors.get(kind, colors["neutral"])`).
	_expect_deep(UiTheme.pill_colors("kind-tak-ada"),
		UiTheme.pill_colors("neutral"), "pill kind tak dikenal -> neutral")

	for case in sec["cases"]:
		var kind := str(case["kind"])
		var hover: bool = case["hover"]
		var tag := "pill(%s,hover=%s)" % [kind, hover]
		var rect := _rect4(case["rect"])
		var base: Array = table[kind]
		var top := _col(base[0])
		var bottom := _col(base[1])
		if hover:
			# Aturan hover pygame: top+18, bottom+14 (bukan angka salinan).
			top = UiTheme.add_rgb(top, 18)
			bottom = UiTheme.add_rgb(bottom, 14)
		_expect_grad({"w": rect.size.x, "h": rect.size.y, "top": top,
			"bottom": bottom, "radius": 7.0}, case["grad"][0],
			tag + " gradasi r7")
		var glows: Array = case["glow"]
		if hover:
			_expect(glows.size() == 1, tag + " glow terekam")
			if glows.size() == 1:
				_expect_glow({"w": rect.size.x + 30.0,
					"h": rect.size.y + 24.0, "color": _col(base[2]),
					"alpha": UiTheme.radial_alpha_key(66)}, glows[0],
					tag + " glow (+30/+24, alpha 66)")
		else:
			_expect(glows.is_empty(), tag + " tanpa glow")

	# Pill mati: rect TIDAK didaftarkan ke btns (tidak bisa diklik).
	var off: Dictionary = sec["disabled"]
	_expect((off["btns"] as Array).is_empty(),
		"pill enabled=false tidak mendaftar btns")
	_expect_rect(UiTheme.back_button_rect(640.0, 600.0), off["rect"],
		"rect pill mati == back_button_rect")


# ══════════════════════════════════════════════════════════
#  CHIP (seksi "chip")
# ══════════════════════════════════════════════════════════

func _test_chip() -> void:
	var sec := _sec("chip")
	var colors: Array = UiTheme.chip_colors()
	for case in sec["cases"]:
		var has_icon: bool = case["icon"] != null
		var has_value: bool = case["value"] != null
		var align := str(case["align"])
		var tag := "chip('%s',align=%s,icon=%s,value=%s)" % [case["label"],
			align, has_icon, has_value]
		# align="right": pos = sudut KANAN-atas (pygame: x = pos[0] - lebar).
		var pos := Vector2(_num(case["rect"][0]), _num(case["rect"][1]))
		if align == "right":
			pos = Vector2(_num(case["rect"][0]) + _num(case["rect"][2]),
				_num(case["rect"][1]))
		var got := UiTheme.chip_rect(pos, _num(case["text_w"]),
			_num(case["value_w"]), has_icon, has_value, align)
		_expect_rect(got, case["rect"], tag)
		_expect_grad({"w": got.size.x, "h": got.size.y, "top": colors[0],
			"bottom": colors[1], "radius": floor(got.size.y / 2.0)},
			case["grad"][0], tag + " gradasi")
	_expect_near(_num(sec["height"]), 30.0, 0.001, "tinggi chip 30")
	_expect_color(colors[2], [22, 26, 46], "chip warna jalur hemat")


# ══════════════════════════════════════════════════════════
#  SECTION HEADER (seksi "section_header")
# ══════════════════════════════════════════════════════════

func _test_section_header() -> void:
	for case in _cases("section_header"):
		var pos := Vector2(_num(case["x"]), _num(case["y"]))
		var color := _col(case["color"])
		var tag := "section_header('%s')" % case["title"]
		var g := UiTheme.section_header_geom(pos, _num(case["title_w"]),
			_num(case["rule_w"]))
		_expect_near(_num(g["next_y"]), _num(case["next_y"]), 0.51,
			tag + " next_y")
		# Garis redup diukur dari piksel: x+28 sampai x+title_w+28+14.
		var span: Array = case["dim_span"]
		_expect_near((g["dim_from"] as Vector2).x, _num(span[0]), 0.51,
			tag + " dim_from.x")
		_expect_near((g["dim_to"] as Vector2).x + 1.0, _num(span[1]), 0.51,
			tag + " dim_to.x")
		_expect_near((g["dim_from"] as Vector2).y, pos.y + 26.0, 0.001,
			tag + " garis redup y+26")
		# Ujung garis aksen (piksel asli) = x + title_w + 28 + 14 + rule_w.
		_expect_near((g["rule_to"] as Vector2).x + 1.0,
			_num(case["rule_end"]), 0.51, tag + " rule_to.x")
		_expect_near((g["rule_from"] as Vector2).x,
			(g["dim_to"] as Vector2).x, 0.001,
			tag + " rule_from.x == dim_to.x")
		_expect_near((g["rule_from"] as Vector2).y, pos.y + 14.0, 0.001,
			tag + " garis aksen y+14")
		_expect_near((g["icon"] as Vector2).x, pos.x + 10.0, 0.001,
			tag + " ikon x+10")
		_expect_near((g["icon"] as Vector2).y, pos.y + 11.0, 0.001,
			tag + " ikon y+11")
		_expect_near((g["text"] as Vector2).x, pos.x + 28.0, 0.001,
			tag + " teks x+28")
		_expect_color(UiTheme.dim(color), case["dim_px"],
			tag + " warna garis redup")
		_expect_color(color, case["rule_px"], tag + " warna garis aksen")
		_expect_deep(case["dim_expected"], case["dim_px"],
			tag + " _dim pygame == piksel")
	# Tinggi blok (34px) = next_y - y pengukuran oracle.
	var first: Dictionary = _cases("section_header")[0]
	var head_font := _font("body_semibold")
	if head_font != null:
		_expect_near(UiTheme.section_header_size(str(first["title"]),
			head_font, 22, _num(first["rule_w"])).y,
			_num(first["next_y"]) - _num(first["y"]), 0.001,
			"section_header_size().y == 34")


# ══════════════════════════════════════════════════════════
#  TOGGLE (seksi "toggle")
# ══════════════════════════════════════════════════════════

func _test_toggle() -> void:
	var sec := _sec("toggle")
	_expect_near(_num(sec["knob"]), UiTheme.toggle_knob_size(), 0.001,
		"toggle_knob_size() == 18")
	for case in sec["cases"]:
		var is_on: bool = case["is_on"]
		var hover: bool = case["hover"]
		var tag := "toggle(on=%s,hover=%s)" % [is_on, hover]
		var rect := _rect4(case["rect"])
		var cols: Array = UiTheme.toggle_colors(is_on, hover)
		_expect_grad({"w": rect.size.x, "h": rect.size.y, "top": cols[0],
			"bottom": cols[1], "radius": floor(rect.size.y / 2.0)},
			case["grad"][0], tag + " gradasi")
		_expect_color(cols[2], case["edge_px"], tag + " warna tepi")
		_expect_deep(case["btns"]["t"], case["rect"], tag + " btns == rect")
		# Knob: kanan saat ON (right - 18 - 6), kiri saat OFF (x + 6).
		var kx := rect.end.x - UiTheme.toggle_knob_size() - 6.0 if is_on \
			else rect.position.x + 6.0
		_expect(kx > rect.position.x and kx < rect.end.x,
			tag + " knob di dalam track")


# ══════════════════════════════════════════════════════════
#  SLIDER (seksi "slider")
# ══════════════════════════════════════════════════════════

func _test_slider() -> void:
	var sec := _sec("slider")
	for case in sec["cases"]:
		var pos := Vector2(_num(case["x"]), _num(case["y"]))
		var w := _num(case["w"])
		var value := _num(case["value"])
		var tag := "slider(value=%s)" % value
		var g := UiTheme.slider_geom(pos, w, value)
		_expect_rect(g["track"], [case["x"], case["y"], case["w"], 8],
			tag + " track 8px")
		_expect_near(_num(g["fill_w"]), _num(case["fill_w"]), 0.51,
			tag + " fill_w")
		_expect_near(_num(case["knob_x"]), (g["knob"] as Vector2).x, 0.51,
			tag + " knob_x == x + fill_w")
		_expect_near((g["knob"] as Vector2).y, pos.y + 4.0, 0.001,
			tag + " knob_y")
		_expect_near(_num(g["fill_w"]), float(UiTheme.bar_fill_w(w, value)),
			0.001, tag + " fill_w == bar_fill_w")
		var grads: Array = case["grad"]
		if grads.is_empty():
			_expect(_num(g["fill_w"]) <= 4.0,
				tag + " fill <= 4 -> tanpa gradasi")
		else:
			_expect_grad({"w": _num(g["fill_w"]), "h": 8.0,
				"top": UiTheme.GOLD_BRIGHT, "bottom": GOLD_DEEP_BODY,
				"radius": 4.0}, grads[0], tag + " gradasi isi")
		if case["track_px"] != null:
			_expect_color(_col(sec["track_color"]), case["track_px"],
				tag + " warna track")
	_expect_color(_col(sec["track_color"]), [34, 38, 58],
		"track slider (34,38,58)")
	_expect_color(_col(sec["border_color"]), [120, 110, 86],
		"border slider (120,110,86)")
	# Glow knob saat hover: 36x36, alpha 80 (terkuantisasi).
	var glows: Array = sec["glow"]
	_expect(glows.size() == 1, "slider glow terekam")
	if glows.size() == 1:
		_expect_glow({"w": 36.0, "h": 36.0, "color": UiTheme.GOLD,
			"alpha": UiTheme.radial_alpha_key(80)}, glows[0],
			"glow knob slider")


# ══════════════════════════════════════════════════════════
#  OPTION CYCLER (seksi "cycler")
# ══════════════════════════════════════════════════════════

func _test_cycler() -> void:
	var sec := _sec("cycler")
	for case in sec["cases"]:
		var pos := Vector2(_num(case["x"]), _num(case["y"]))
		var tag := "cycler('%s',value_w=%d)" % [case["value"],
			int(case["value_w"])]
		var g := UiTheme.cycler_geom(pos, _num(case["width"]),
			_num(case["value_w"]))
		_expect_rect(g["box"], case["box"], tag + " box")
		_expect_rect(g["prev"], case["prev"], tag + " chevron kiri")
		_expect_rect(g["next"], case["next"], tag + " chevron kanan")
		_expect_near(_num(g["next_y"]), _num(case["next_y"]), 0.51,
			tag + " next_y")
		_expect_near((g["label"] as Vector2).x, pos.x, 0.001,
			tag + " label x")
		_expect_near((g["label"] as Vector2).y, pos.y + 10.0, 0.001,
			tag + " label y+10")
		var keys: Array = case["grad"]
		_expect(keys.size() == 2, tag + " 2 kunci gradasi")
		if keys.size() == 2:
			var box: Rect2 = g["box"]
			_expect_grad({"w": box.size.x, "h": box.size.y,
				"top": Color8(40, 48, 80), "bottom": Color8(20, 24, 44),
				"radius": 6.0}, keys[0], tag + " box gradasi")
			_expect_grad({"w": 24.0, "h": 30.0, "top": Color8(42, 48, 74),
				"bottom": Color8(26, 30, 52), "radius": 6.0}, keys[1],
				tag + " chevron gradasi")
	# Hover chevron: chevron yang disorot memakai (64,74,110).
	var hover_sec: Dictionary = sec["hover"]
	var hkeys: Array = hover_sec["grad"]
	_expect(hkeys.size() == 3, "cycler hover merekam 3 kunci gradasi")
	if hkeys.size() == 3:
		_expect_color(_col(hkeys[2]["top"]), [64, 74, 110],
			"chevron hover top (64,74,110)")
		_expect_color(_col(hkeys[1]["top"]), [42, 48, 74],
			"chevron idle top (42,48,74)")
	_expect((hover_sec["btns"] as Dictionary).has("speed_prev")
		and (hover_sec["btns"] as Dictionary).has("speed_next"),
		"cycler hover mendaftarkan id_base + _prev/_next")


# ══════════════════════════════════════════════════════════
#  TAB (seksi "tab")
# ══════════════════════════════════════════════════════════

func _test_tab() -> void:
	var sec := _sec("tab")
	for case in sec["cases"]:
		var active: bool = case["active"]
		var hover: bool = case["hover"]
		var tag := "tab(active=%s,hover=%s)" % [active, hover]
		var rect := _rect4(case["rect"])
		var cols: Array = UiTheme.tab_colors(active, hover, UiTheme.CYAN)
		_expect_grad({"w": rect.size.x, "h": rect.size.y, "top": cols[0],
			"bottom": cols[1], "radius": 8.0}, case["grad"][0],
			tag + " gradasi r8")
		_expect_color(cols[2], case["border_px"], tag + " border")
		if active:
			# Underline aksen 3px hanya saat aktif.
			_expect_color(cols[2], case["underline_px"], tag + " underline")
		else:
			_expect(case["underline_px"] == null,
				tag + " tanpa underline")
		_expect_deep(case["btns"]["tab"], case["rect"], tag + " btns == rect")
	# Lebar tab: max(min_w, lebar(letter(label)) + 36) dengan metrik oracle.
	var char_w := int(sec["char_w"])
	for case in sec["tab_width"]:
		var measured: int = char_w \
			* UiTheme.letter(str(case["label"]), " ").length()
		_expect_near(UiTheme.tab_width_for(float(measured),
			_num(case["min_w"])), _num(case["w"]), 0.51,
			"tab_width_for('%s',min=%d)" % [case["label"],
			int(case["min_w"])])
	# Jalur font Godot harus memakai rumus yang sama.
	var font := _font("body_bold")
	if font != null:
		var text := "PILIHAN"
		var measured := font.get_string_size(UiTheme.letter(text),
			HORIZONTAL_ALIGNMENT_LEFT, -1, 18).x
		_expect_near(UiTheme.tab_width(font, 18, text, 150.0),
			UiTheme.tab_width_for(measured, 150.0), 0.001,
			"tab_width() == tab_width_for(lebar terukur)")


# ══════════════════════════════════════════════════════════
#  SCREEN TITLE (seksi "screen_title")
# ══════════════════════════════════════════════════════════

func _test_screen_title() -> void:
	var sec := _sec("screen_title")
	var cx := _num(sec["cx"])
	var y := _num(sec["y"])
	var sub_w := _num(sec["sub_w"])
	var g := UiTheme.screen_title_geom(cx, y, sub_w)
	var consts: Dictionary = sec["consts"]
	var derived: Dictionary = sec["derived"]

	# Glow radial 620x150 di (cx-310, y-62), alpha 46 -> kunci 40.
	var glow: Rect2 = g["glow"]
	_expect_glow({"w": glow.size.x, "h": glow.size.y,
		"color": Color8(255, 205, 90),
		"alpha": UiTheme.radial_alpha_key(46)}, (sec["glow"] as Array)[0],
		"screen_title glow")
	_expect_near(glow.position.x, cx + _num(consts["glow_offset"][0]), 0.51,
		"screen_title glow x")
	_expect_near(glow.position.y, y + _num(consts["glow_offset"][1]), 0.51,
		"screen_title glow y")

	# Ornamen: offset diturunkan oracle dari PIKSEL render pygame.
	_expect_near(_num(g["ornament_y"]), _num(sec["ornament_y"]), 0.51,
		"screen_title ornament_y")
	_expect_near(_num(g["ornament_y"]) - y, _num(consts["ornament_dy"]),
		0.001, "ornament dy == y+52")
	var line_l: Array = g["line_l"]
	var line_r: Array = g["line_r"]
	var gem: Array = g["gem"]
	var fy := _num(g["ornament_y"])
	_expect_near(cx - (line_l[0] as Vector2).x, _num(derived["line_left"]),
		0.51, "ornamen garis kiri mulai (cx-220)")
	_expect_near(cx - (line_l[1] as Vector2).x, _num(derived["line_inner"]),
		0.51, "ornamen garis kiri berakhir (cx-18)")
	_expect_near((line_r[0] as Vector2).x - cx, _num(derived["line_inner"]),
		0.51, "ornamen garis kanan mulai (cx+18)")
	_expect_near((line_r[1] as Vector2).x - cx, _num(derived["line_left"]),
		0.51, "ornamen garis kanan berakhir (cx+220)")
	_expect_near((gem[2] as Vector2).x - cx, _num(derived["gem_dx"]), 0.51,
		"ornamen wajik dx")
	_expect_near(fy - (gem[1] as Vector2).y, _num(derived["gem_dy"]), 0.51,
		"ornamen wajik dy")
	_expect_near(cx - (g["dot_l"] as Vector2).x, _num(derived["dot"]), 0.51,
		"ornamen dot kiri")
	_expect_near((g["dot_r"] as Vector2).x - cx, _num(derived["dot"]), 0.51,
		"ornamen dot kanan")

	# Plate subtitle: lebar = sub_w + 56, x memakai pembagian bulat pygame.
	var plate: Rect2 = g["sub_plate"]
	_expect_grad({"w": plate.size.x, "h": plate.size.y,
		"top": Color8(26, 32, 58), "bottom": Color8(14, 18, 34),
		"radius": 10.0}, (sec["grad"] as Array)[0],
		"screen_title plate gradasi")
	_expect_near(plate.position.x, _num(derived["plate_x"]), 0.51,
		"plate x (pembagian bulat pygame)")
	_expect_near(plate.size.x, _num(derived["plate_w"]), 0.51, "plate w")
	_expect_near(plate.size.x, sub_w + _num(consts["plate_pad"]), 0.51,
		"plate w == sub_w + 56")
	_expect_near(plate.position.y - y, _num(derived["plate_y"]), 0.51,
		"plate y == y + 52 + 12")
	_expect_near(plate.size.y, _num(consts["plate_h"]), 0.001,
		"plate tinggi 44")


# ══════════════════════════════════════════════════════════
#  BACK BUTTON (seksi "back_button")
# ══════════════════════════════════════════════════════════

func _test_back_button() -> void:
	var sec := _sec("back_button")
	_expect_rect(UiTheme.back_button_rect(640.0, 600.0), sec["rect"],
		"back_button_rect(640,600)")
	_expect_deep(sec["hover_rect"], sec["rect"],
		"pill tidak menggelembung saat hover")
	_expect_deep(sec["btns"]["back"], sec["rect"], "btns['back'] == rect")
	# Widget: properti back_button() == pengukuran oracle.
	var back := PygameButton.back_button()
	_expect_near(back.custom_minimum_size.x, _num(sec["rect"][2]), 0.51,
		"PygameButton.back_button lebar 200")
	_expect_near(back.custom_minimum_size.y, _num(sec["rect"][3]), 0.51,
		"PygameButton.back_button tinggi 42")
	_expect(back.label_text == "BACK", "back_button label default 'BACK'")
	_expect(back.pill_kind == "neutral", "back_button kind neutral")
	_expect(back.icon_name == "back", "back_button ikon 'back'")
	_expect(back.use_letter_spacing, "back_button letter-spacing aktif")
	_expect_near(back.icon_scale, 0.8, 0.001, "back_button icon_scale 0.8")
	_expect(back.font_weight == "body_semibold",
		"back_button font body_semibold")
	back.free()


# ══════════════════════════════════════════════════════════
#  SCROLL INDICATOR (seksi "scroll")
# ══════════════════════════════════════════════════════════

func _test_scroll() -> void:
	var sec := _sec("scroll")
	var width := _num(sec["width"])
	for case in sec["cases"]:
		var pos := Vector2(_num(case["x"]), _num(case["y"]))
		var height := _num(case["height"])
		var sp := _num(case["scroll_pos"])
		var ms := _num(case["max_scroll"])
		var tag := "scroll(h=%d,max=%d,pos=%d)" % [int(height), int(ms),
			int(sp)]
		_expect_rect(Rect2(pos, Vector2(width, height)), case["track"],
			tag + " track")
		var thumb := UiTheme.scroll_thumb_rect(pos, height, sp, ms, width)
		if case["thumb_y"] == null:
			_expect_near(thumb.size.y, 0.0, 0.001, tag + " tanpa thumb")
		else:
			_expect_near(thumb.position.y, _num(case["thumb_y"]), 0.51,
				tag + " thumb_y")
			_expect_near(thumb.size.y, _num(case["thumb_h"]), 0.51,
				tag + " thumb_h")
			_expect_near(thumb.size.x, width, 0.001, tag + " lebar thumb")
			_expect(thumb.position.y >= pos.y - 0.51
				and thumb.end.y <= pos.y + height + 0.51,
				tag + " thumb di dalam track")
	# Gradasi thumb: GOLD_BRIGHT -> (196,138,40), radius 3.
	var keys: Array = sec["grad"]
	_expect(keys.size() == 1, "scroll gradasi terekam")
	if keys.size() == 1:
		_expect_color(UiTheme.GOLD_BRIGHT, keys[0]["top"], "thumb top")
		_expect_color(GOLD_DEEP_BODY, keys[0]["bottom"], "thumb bottom")
		_expect_near(_num(keys[0]["radius"]), 3.0, 0.001, "thumb radius 3")
	_expect_color(_col(sec["track_color"]), [28, 32, 52],
		"track scroll (28,32,52)")
	# Aturan thumb: minimum 18px, tak pernah lebih tinggi dari track.
	for pair in [[100.0, 0.0], [100.0, 50.0], [100.0, 5000.0], [400.0, 10.0],
			[18.0, 900.0], [900.0, 0.5], [300.0, 400.0]]:
		var t := UiTheme.scroll_thumb_rect(Vector2.ZERO, pair[0], pair[1],
			pair[0] * 3.0, width)
		_expect(t.size.y >= 18.0,
			"thumb >= 18 (h=%d,pos=%d)" % [int(pair[0]), int(pair[1])])
		_expect(t.end.y <= pair[0] + 0.51,
			"thumb <= track (h=%d,pos=%d)" % [int(pair[0]), int(pair[1])])


# ══════════════════════════════════════════════════════════
#  BAR HP / PROGRES (seksi "bars")
# ══════════════════════════════════════════════════════════

func _test_bars() -> void:
	for case in _cases("bars"):
		var w := _num(case["w"])
		var h := _num(case["h"])
		var ratio := _num(case["ratio"])
		var color := _col(case["color"])
		var kind := str(case["kind"])
		var tag := "%s_bar(w=%d,ratio=%s)" % [kind, int(w), ratio]
		_expect_near(float(UiTheme.bar_fill_w(w, ratio)),
			_num(case["fill_w"]), 0.51, tag + " fill_w")
		var grads: Array = case["grad"]
		if grads.is_empty():
			_expect(_num(case["fill_w"]) <= 3.0,
				tag + " fill <= 3 -> tanpa gradasi")
			continue
		# hp_bar: light = color + 50; progress_bar: color + 40 (pygame).
		var light := UiTheme.add_rgb(color, 50 if kind == "hp" else 40)
		_expect_grad({"w": _num(case["fill_w"]), "h": h, "top": light,
			"bottom": color, "radius": floor(h / 2.0)}, grads[0],
			tag + " gradasi")


# ══════════════════════════════════════════════════════════
#  GRADIENT TEXT (seksi "gradient_text")
# ══════════════════════════════════════════════════════════

func _test_gradient_text() -> void:
	var sec := _sec("gradient_text")
	# Warna per baris `gradient_text()` pygame == rumus baris `_vgrad` Godot.
	var top := _col(sec["row_top"])
	var bottom := _col(sec["row_bottom"])
	var rows: Array = sec["rows"]
	_expect(rows.size() > 1, "gradient_text merekam baris")
	for y in rows.size():
		_expect_color(UiTheme.vgrad_row_color(top, bottom, y, rows.size()),
			rows[y], "gradient_text baris %d" % y)
	# outline_text() pygame: body default GOLD_BRIGHT -> (196,138,40).
	_expect((sec["body"] as Array).size() == 1, "satu kunci gradient_text")
	var body: Array = (sec["body"] as Array)[0]
	_expect_color(UiTheme.GOLD_BRIGHT, body[0], "outline_text body top")
	_expect_color(GOLD_DEEP_BODY, body[1], "outline_text body bottom")
	_expect_color(_col(sec["outline"]), [8, 9, 18], "outline (8,9,18)")
	_expect(int(sec["outline_width"]) == 2, "outline width 2")

	# Widget GradientText: default sama, pita monoton, ujung mendekati warna.
	var gt := GradientText.new()
	_expect_color(gt.top_color, body[0], "GradientText.top_color default")
	_expect_color(gt.bottom_color, body[1],
		"GradientText.bottom_color default")
	_expect_color(gt.outline_color, sec["outline"],
		"GradientText.outline_color default")
	_expect(int(gt.outline_size) == int(sec["outline_width"]),
		"GradientText.outline_size default")
	_expect(not gt.outline, "GradientText.outline mati secara default")
	gt.free()

	var bands: Array = UiTheme.gradient_bands(top, bottom, 12)
	_expect(bands.size() == 12, "gradient_bands jumlah pita")
	for i in 11:
		_expect((bands[i] as Color).r8 >= (bands[i + 1] as Color).r8,
			"gradient_bands monoton band %d" % i)
	# Pita dievaluasi di tengah pita -> selisih maks satu langkah.
	var step := absf(float(top.r8 - bottom.r8)) / 12.0
	_expect_near(float((bands[0] as Color).r8), float(top.r8), step,
		"gradient_bands[0] dekat top")
	_expect_near(float((bands[11] as Color).r8), float(bottom.r8), step,
		"gradient_bands[11] dekat bottom")
	var single: Array = UiTheme.gradient_bands(top, bottom, 1)
	_expect_near(float((single[0] as Color).r8),
		float(top.r8 + bottom.r8) / 2.0, 1.0, "gradient_bands n=1 -> tengah")


# ══════════════════════════════════════════════════════════
#  IKON (seksi "icons")
# ══════════════════════════════════════════════════════════

func _test_icons() -> void:
	var want: Variant = _fx.get("icons")
	_expect(want is Array, "seksi fixture \"icons\" ada")
	if not (want is Array):
		return
	_expect_deep(UiTheme.icon_names(), want,
		"ICON_NAMES == kunci _icon_paths pygame")
	for name in want:
		_expect(UiTheme.has_icon(str(name)), "has_icon('%s')" % name)
	_expect(not UiTheme.has_icon("ikon-tak-ada"),
		"has_icon nama tak dikenal -> false")


# ══════════════════════════════════════════════════════════
#  WIDGET (tanpa tree)
# ══════════════════════════════════════════════════════════

func _test_widgets() -> void:
	# ── PygameChip: custom_minimum_size dari rumus chip_rect ──
	var chip_case: Dictionary = _cases("chip")[0]
	var chip := PygameChip.new()
	chip.label_text = str(chip_case["label"])
	chip.icon_name = ""
	chip.value_text = ""
	var chip_font := UiTheme.font_for_weight(chip.font_weight)
	if chip_font != null:
		var text_w := chip_font.get_string_size(
			UiTheme.letter(chip.label_text), HORIZONTAL_ALIGNMENT_LEFT, -1,
			chip.font_size).x
		_expect_near(chip.custom_minimum_size.y, _num(chip_case["rect"][3]),
			0.51, "PygameChip tinggi == 30 oracle")
		_expect_near(chip.custom_minimum_size.x, 26.0 + text_w, 0.51,
			"PygameChip lebar == 26 + lebar teks")
		chip.value_text = "1234"
		var value_w := chip_font.get_string_size("1234",
			HORIZONTAL_ALIGNMENT_LEFT, -1, chip.font_size).x
		_expect_near(chip.custom_minimum_size.x, 26.0 + text_w + 10.0
			+ value_w, 0.51, "PygameChip lebar dengan value")
	chip.free()

	# ── SectionHeader: tinggi 34 == pengukuran oracle ──
	var sh_case: Dictionary = _cases("section_header")[0]
	var head := SectionHeader.new()
	head.title = str(sh_case["title"])
	_expect_near(head.custom_minimum_size.y,
		_num(sh_case["next_y"]) - _num(sh_case["y"]), 0.51,
		"SectionHeader tinggi == next_y - y")
	head.free()

	# ── PygameSlider: ratio + track_rect (koordinat lokal Control) ──
	var sl_cases: Array = _cases("slider")
	var sl_case: Dictionary = sl_cases[0]
	var slider := PygameSlider.new()
	slider.position = Vector2(_num(sl_case["x"]), _num(sl_case["y"]))
	slider.size = Vector2(_num(sl_case["w"]), 34.0)
	var seen: Array = []
	slider.value_changed.connect(func(v: float) -> void: seen.append(v))
	slider.value = 0.5
	_expect_near(slider.ratio(), 0.5, 0.000001, "PygameSlider.ratio() 0.5")
	_expect_rect(slider.track_rect(), [0, 13, sl_case["w"], 8],
		"PygameSlider.track_rect() lokal")
	_expect_near(slider.track_rect().size.y,
		_num((sl_cases[1]["grad"] as Array)[0]["h"]), 0.001,
		"PygameSlider TRACK_H == tinggi gradasi oracle (8)")
	slider.value = 3.0
	_expect_near(slider.value, 1.0, 0.000001, "PygameSlider clamp atas")
	slider.value = -2.0
	_expect_near(slider.value, 0.0, 0.000001, "PygameSlider clamp bawah")
	slider.value = 0.75
	_expect_near(slider.ratio(), 0.75, 0.000001, "PygameSlider.ratio() 0.75")
	_expect(seen.size() >= 3, "PygameSlider memancarkan value_changed")
	slider.free()

	# ── OptionCycler: hit rects + cycle + sinyal ──
	var cyc_case: Dictionary = _cases("cycler")[0]
	var cyc := OptionCycler.new()
	cyc.id_base = "c"
	cyc.set_options(["A", "B", "C"], [], 0)
	cyc.size = Vector2(_num(cyc_case["width"]), 40.0)
	var log: Array = []
	cyc.value_changed.connect(func(i: int, v: Variant) -> void:
		log.append([i, v]))
	var hits := cyc.hit_rects()
	_expect(hits.has("c_prev") and hits.has("c_next") and hits.has("box"),
		"OptionCycler.hit_rects() kunci prev/next/box")
	var prev: Rect2 = hits["c_prev"]
	var next_r: Rect2 = hits["c_next"]
	var box: Rect2 = hits["box"]
	_expect_near(box.size.y, _num(cyc_case["box"][3]), 0.51,
		"OptionCycler tinggi kotak 30")
	_expect_near(box.position.y,
		_num(cyc_case["box"][1]) - _num(cyc_case["y"]), 0.51,
		"OptionCycler kotak y == y+7 (lokal)")
	_expect_rect(prev, [box.position.x - 30.0, box.position.y,
		_num(cyc_case["prev"][2]), _num(cyc_case["prev"][3])],
		"OptionCycler chevron kiri 24x30, jarak 6")
	_expect_rect(next_r, [box.end.x + 6.0, box.position.y,
		_num(cyc_case["next"][2]), _num(cyc_case["next"][3])],
		"OptionCycler chevron kanan 24x30, jarak 6")
	_expect_near(_num(cyc_case["next_y"]) - _num(cyc_case["y"]), 37.0, 0.001,
		"option_cycler next_y == y + 37")
	cyc.press("next")
	_expect(cyc.index == 1, "OptionCycler.press('next') -> 1")
	_expect_deep(log[0], [1, "B"], "OptionCycler sinyal value_changed")
	cyc.cycle(-1)
	_expect(cyc.index == 0, "OptionCycler.cycle(-1) -> 0")
	cyc.cycle(-1)
	_expect(cyc.index == 2, "OptionCycler membungkus ke bawah")
	cyc.set_index(9)
	_expect(cyc.index == 0, "OptionCycler.set_index(9) -> modulo 0")
	_expect(str(cyc.value()) == "A", "OptionCycler.value() == 'A'")
	_expect(cyc.value_text() == "A", "OptionCycler.value_text() == 'A'")
	cyc.set_options(["X"], ["Label X"], 0)
	_expect(cyc.value_text() == "Label X",
		"OptionCycler.value_text() memakai labels")
	cyc.free()

	# ── ScrollIndicator: thumb_rect == pengukuran oracle ──
	var sc_cases: Array = _cases("scroll")
	var sc: Dictionary = sc_cases[0]
	var si := ScrollIndicator.new()
	si.bar_width = _num(_sec("scroll")["width"])
	si.size = Vector2(si.bar_width, _num(sc["height"]))
	si.set_scroll(0.0, 400.0)
	_expect_near(si.thumb_rect().size.y, _num(sc["thumb_h"]), 0.51,
		"ScrollIndicator thumb_h pos=0")
	_expect_near(si.thumb_rect().position.y, 0.0, 0.51,
		"ScrollIndicator thumb_y pos=0 (lokal)")
	_expect_near(si.thumb_rect().size.x, si.bar_width, 0.001,
		"ScrollIndicator lebar thumb")
	var last: Dictionary = sc_cases[2]
	si.set_scroll(_num(last["scroll_pos"]), _num(last["max_scroll"]))
	_expect_near(si.thumb_rect().position.y,
		_num(last["thumb_y"]) - _num(last["y"]), 0.51,
		"ScrollIndicator thumb_y pos=max")
	si.set_scroll(0.0, 0.0)
	_expect_near(si.thumb_rect().size.y, 0.0, 0.001,
		"ScrollIndicator tanpa max_scroll -> thumb 0")
	si.free()

	# ── PygameToggle: ukuran widget = rect toggle oracle ──
	var tog_case: Dictionary = _cases("toggle")[3]
	var tg := PygameToggle.new()
	tg.set_on(bool(tog_case["is_on"]))
	tg.size = Vector2(_num(tog_case["rect"][2]), _num(tog_case["rect"][3]))
	_expect(tg.is_on == bool(tog_case["is_on"]), "PygameToggle.set_on")
	_expect_near(tg.size.x, 60.0, 0.001, "PygameToggle lebar 60")
	_expect_near(tg.size.y, 26.0, 0.001, "PygameToggle tinggi 26")
	tg.free()

	# ── PygameButton: tiga mode memakai *_visual yang sama ──
	var menu := PygameButton.menu_button("MULAI", UiTheme.GOLD)
	_expect(menu.mode == PygameButton.Mode.MENU, "menu_button mode MENU")
	_expect(menu.use_letter_spacing, "menu_button letter-spacing aktif")
	_expect_near(menu.icon_scale, 0.9, 0.001, "menu_button icon_scale 0.9")
	menu.free()
	var pillb := PygameButton.pill_button("PLAY", "gold")
	_expect(pillb.mode == PygameButton.Mode.PILL, "pill_button mode PILL")
	_expect(pillb.pill_kind == "gold", "pill_button kind gold")
	pillb.free()
	var tabb := PygameButton.tab_button("HERO", UiTheme.CYAN)
	_expect(tabb.mode == PygameButton.Mode.TAB, "tab_button mode TAB")
	tabb.free()


func _test_widgets_in_tree() -> void:
	# GradientText membangun `bands` pita clip (masing-masing 1 BandText).
	var body: Array = (_sec("gradient_text")["body"] as Array)[0]
	var gt := GradientText.new()
	gt.font_size = 40
	gt.set_text("MYSTIC ARENA")
	gt.set_gradient(_col(body[0]), _col(body[1]), 6)
	gt.size = Vector2(400, 44)
	add_child(gt)
	await get_tree().process_frame
	_expect(gt.get_child_count() == 6,
		"GradientText membangun 6 pita (dapat %d)" % gt.get_child_count())
	if gt.get_child_count() > 0:
		var band := gt.get_child(0) as Control
		_expect(band != null and band.clip_contents,
			"GradientText pita memakai clip_contents")
	gt.set_gradient(_col(body[1]), _col(body[0]), 4)
	# Pita lama dibuang dengan queue_free -> butuh lebih dari satu frame.
	await get_tree().process_frame
	await get_tree().process_frame
	_expect(gt.get_child_count() == 4,
		"GradientText rebuild setelah set_gradient (dapat %d)"
		% gt.get_child_count())
	gt.queue_free()

	# ScreenTitle: judul gradasi + plate subtitle + ornamen opsional.
	var st := ScreenTitle.new()
	st.set_title("MYSTIC ARENA", "")
	st.position = Vector2(300, 80)
	st.size = Vector2(500, 90)
	add_child(st)
	await get_tree().process_frame
	_expect(st.gradient_body, "ScreenTitle.gradient_body default aktif")
	_expect_color(st.body_top, body[0], "ScreenTitle.body_top default")
	_expect_color(st.body_bottom, body[1], "ScreenTitle.body_bottom default")
	var before := st.get_child_count()
	st.set_title("MYSTIC ARENA", "AUDIO & GAMEPLAY")
	st.ornament = true
	await get_tree().process_frame
	_expect(st.get_child_count() >= before,
		"ScreenTitle subtitle tidak mengurangi anak")
	_expect(st.sub_text == "AUDIO & GAMEPLAY", "ScreenTitle.sub_text")
	st.queue_free()


# ══════════════════════════════════════════════════════════
#  SMOKE IMMEDIATE-MODE (butuh _draw nyata)
# ══════════════════════════════════════════════════════════

class DrawProbe extends Control:
	var drawn := 0
	var icons := 0
	var btns_idle := {}
	var btns_hover := {}
	var btns_pill_on := {}
	var btns_pill_off := {}
	var btns_cycler := {}
	var btns_toggle := {}
	var btns_tab := {}
	var btns_back := {}
	var btns_back_hover := {}
	var next_y_header := 0.0
	var next_y_cycler := 0.0
	var knob_x := 0.0
	var scroll_track := Rect2()
	var chip_rect := Rect2()
	var back_rect := Rect2()
	var tab_rect := Rect2()
	var toggle_rect := Rect2()

	func _draw() -> void:
		drawn += 1
		var font: Font = UiTheme.body_bold()
		var semibold: Font = UiTheme.body_semibold()
		# Tombol menu: idle + hover (rect hit harus sama dengan oracle).
		UiTheme.draw_button(self, btns_idle, "b", "MULAI GAME",
			Vector2(350, 170), UiTheme.GOLD, font, 20, 300.0, 50.0, "play",
			false)
		UiTheme.draw_button(self, btns_hover, "b", "MULAI GAME",
			Vector2(350, 170), UiTheme.GOLD, font, 20, 300.0, 50.0, "play",
			true)
		# Pill hidup vs mati (mati tidak boleh mendaftar rect hit).
		UiTheme.draw_pill(self, btns_pill_on, "p", "PLAY",
			Rect2(120, 90, 170, 40), "gold", semibold, 18, false, true,
			"play")
		UiTheme.draw_pill(self, btns_pill_off, "p", "OFF",
			Rect2(120, 90, 170, 40), "gold", semibold, 18, false, false)
		# Cycler (hover chevron kanan) + next_y.
		next_y_cycler = UiTheme.draw_option_cycler(self, btns_cycler, "c",
			"KECEPATAN", "1.0x", Vector2(40, 80), 340.0, font, 20, semibold,
			20, "c_next")
		# Toggle ON + hover.
		toggle_rect = UiTheme.draw_toggle(self, btns_toggle, "t",
			Rect2(200, 100, 60, 26), true, font, 15, true)
		# Slider: x knob bebas metrik font -> harus persis.
		knob_x = UiTheme.draw_slider(self, Vector2(60, 120), 200.0, 0.5)
		# Tab aktif.
		tab_rect = UiTheme.draw_tab(self, btns_tab, "tab",
			Rect2(100, 60, 180, 34), "PILIHAN", UiTheme.CYAN, font, 18, true)
		# Back button: rect 200x42 bebas metrik font.
		back_rect = UiTheme.draw_back_button(self, btns_back, "back", 640.0,
			600.0, false, "BACK", 26)
		UiTheme.draw_back_button(self, btns_back_hover, "back", 640.0, 600.0,
			true, "BACK", 26)
		# Scroll indicator.
		scroll_track = UiTheme.draw_scroll_indicator(self, Vector2(500, 40),
			300.0, 0.0, 400.0)
		# Chip + section header (next_y bebas metrik font).
		chip_rect = UiTheme.draw_chip(self, Vector2(300, 80), "HERO GOLD",
			UiTheme.CYAN, semibold, 18)
		next_y_header = UiTheme.draw_section_header(self, Vector2(40, 60),
			"AUDIO", "gear", UiTheme.CYAN, semibold, 22, 240.0)
		# Judul layar + ornamen + plate subtitle.
		UiTheme.draw_screen_title(self, "MYSTIC ARENA", 700.0, 100.0, true,
			"AUDIO & GAMEPLAY")
		UiTheme.draw_title_ornament(self,
			UiTheme.screen_title_geom(700.0, 100.0, 0.0))
		UiTheme.draw_title_sub(self,
			UiTheme.screen_title_geom(700.0, 100.0, 217.0),
			"AUDIO & GAMEPLAY")
		# Panel + bar + teks + primitif.
		UiTheme.draw_panel(self, Rect2(40, 400, 300, 200))
		UiTheme.draw_panel_solid(self, Rect2(360, 400, 200, 120))
		UiTheme.draw_hp_bar(self, Vector2(40, 640), 200.0, 14.0, 0.5)
		UiTheme.draw_progress_bar(self, Vector2(260, 640), 120.0, 0.4)
		UiTheme.draw_corner_ticks(self, Rect2(600, 400, 80, 60))
		UiTheme.draw_vgrad(self, Rect2(600, 500, 80, 40), UiTheme.PANEL_TOP,
			UiTheme.PANEL_BOTTOM, 8.0)
		UiTheme.draw_glow(self, Rect2(560, 560, 160, 80), UiTheme.GOLD,
			70.0 / 255.0)
		UiTheme.draw_shadow(self, Rect2(400, 620, 120, 60))
		UiTheme.draw_rr(self, Rect2(700, 400, 40, 40), UiTheme.PANEL_FILL,
			6.0)
		UiTheme.draw_rr_outline(self, Rect2(700, 400, 40, 40),
			UiTheme.EDGE_GOLD, 6.0, 1.0)
		if font != null:
			UiTheme.draw_text(self, font, "MULAI GAME", 18,
				UiTheme.TEXT_WHITE, Vector2(40, 300))
			UiTheme.draw_text_centered(self, font, "MULAI GAME", 18,
				UiTheme.TEXT_WHITE, Vector2(350, 320))
			UiTheme.draw_outline_text(self, UiTheme.title_font(),
				"MYSTIC ARENA", 64, Vector2(700, 100))
		for name in UiTheme.icon_names():
			UiTheme.draw_icon(self, str(name), 20.0, 20.0, Color.WHITE, 1.0)
			icons += 1
		# Jalur hemat (cheap_alpha false) untuk semua komponen: kedua cabang
		# pygame harus tetap jalan tanpa error.
		UiTheme.cheap_alpha_override = 0
		UiTheme.draw_button_visual(self, Rect2(40, 460, 300, 50),
			Rect2(40, 460, 300, 50), "MULAI", UiTheme.GOLD, font, 20, "play",
			true)
		UiTheme.draw_pill_visual(self, Rect2(40, 520, 170, 40), "gold", font,
			18, "PLAY", true)
		UiTheme.draw_toggle_visual(self, Rect2(40, 570, 60, 26), false, font,
			15)
		UiTheme.draw_tab_visual(self, Rect2(120, 570, 150, 34), "TAB",
			UiTheme.CYAN, font, 18, false, true)
		UiTheme.draw_panel(self, Rect2(400, 460, 200, 120))
		UiTheme.draw_chip(self, Vector2(400, 600), "CHIP", UiTheme.CYAN, font,
			18)
		UiTheme.draw_slider(self, Vector2(400, 640), 160.0, 0.4)
		UiTheme.draw_scroll_indicator(self, Vector2(620, 460), 200.0, 40.0,
			400.0)
		UiTheme.draw_screen_title(self, "JUDUL", 700.0, 300.0, true, "SUB")
		UiTheme.draw_title_sub(self,
			UiTheme.screen_title_geom(700.0, 300.0, 60.0), "SUB")
		UiTheme.cheap_alpha_override = -1


func _test_draw_smoke() -> void:
	var probe := DrawProbe.new()
	probe.size = Vector2(960, 720)
	add_child(probe)
	await get_tree().process_frame
	await get_tree().process_frame
	if probe.drawn == 0:
		push_warning("[%s] _draw() tidak dipanggil di headless; smoke "
			% LABEL + "immediate-mode dilewati")
		probe.queue_free()
		return
	var sec_btn := _sec("button")
	var idle: Dictionary = {}
	var hovered: Dictionary = {}
	for case in sec_btn["cases"]:
		if case["icon"] == "play" and not case["hover"]:
			idle = case
		if case["icon"] == "play" and case["hover"]:
			hovered = case
	_expect_rect(probe.btns_idle["b"], idle["rect"],
		"draw_button idle -> btns['b']")
	_expect_rect(probe.btns_hover["b"], hovered["rect"],
		"draw_button hover -> btns['b'] (inflate 18x8)")
	_expect_rect(probe.btns_pill_on["p"], _sec("pill")["disabled"]["rect"],
		"draw_pill -> btns['p']")
	_expect(probe.btns_pill_off.is_empty(),
		"draw_pill(enabled=false) tidak mendaftar btns")

	var cyc_case: Dictionary = _cases("cycler")[0]
	_expect(probe.btns_cycler.has("c_prev")
		and probe.btns_cycler.has("c_next"),
		"draw_option_cycler -> chevron terdaftar")
	_expect_near(probe.next_y_cycler, _num(cyc_case["next_y"]), 0.51,
		"draw_option_cycler next_y")

	var tog_case: Dictionary = _cases("toggle")[3]
	_expect_rect(probe.toggle_rect, tog_case["rect"],
		"draw_toggle rect == oracle")
	_expect_rect(probe.btns_toggle["t"], tog_case["rect"],
		"draw_toggle -> btns['t']")

	_expect_near(probe.knob_x, _num(_cases("slider")[1]["knob_x"]), 0.51,
		"draw_slider knob_x value=0.5")

	var tab_case: Dictionary = _cases("tab")[0]
	_expect_rect(probe.tab_rect, tab_case["rect"], "draw_tab rect")
	_expect_rect(probe.btns_tab["tab"], tab_case["rect"],
		"draw_tab -> btns['tab']")

	var back := _sec("back_button")
	_expect_rect(probe.back_rect, back["rect"], "draw_back_button rect")
	_expect_rect(probe.btns_back["back"], back["rect"],
		"draw_back_button -> btns['back']")
	_expect_rect(probe.btns_back_hover["back"], back["hover_rect"],
		"draw_back_button hover -> rect sama")

	_expect_rect(probe.scroll_track, _cases("scroll")[0]["track"],
		"draw_scroll_indicator track")

	var chip_case: Dictionary = _cases("chip")[0]
	_expect_near(probe.chip_rect.size.y, _num(chip_case["rect"][3]), 0.51,
		"draw_chip tinggi 30")
	_expect_near(probe.chip_rect.position.x, _num(chip_case["rect"][0]), 0.51,
		"draw_chip x == pos.x (align kiri)")

	_expect_near(probe.next_y_header,
		_num(_cases("section_header")[0]["next_y"]), 0.51,
		"draw_section_header next_y")

	_expect(probe.icons == (_fx["icons"] as Array).size(),
		"semua ikon tergambar tanpa crash (%d)" % probe.icons)
	probe.queue_free()


# ══════════════════════════════════════════════════════════
#  CACHE + cheap_alpha
# ══════════════════════════════════════════════════════════

func _test_caches() -> void:
	var before := UiTheme.cheap_alpha_override
	UiTheme.cheap_alpha_override = 1
	_expect(UiTheme.cheap_alpha(), "cheap_alpha_override=1 -> true")
	UiTheme.cheap_alpha_override = 0
	_expect(not UiTheme.cheap_alpha(), "cheap_alpha_override=0 -> false")
	UiTheme.cheap_alpha_override = -1
	_expect(UiTheme.cheap_alpha(),
		"cheap_alpha_override=-1 (auto di Godot) -> true")
	UiTheme.cheap_alpha_override = before

	var a := UiTheme.radial_texture(42, 22, UiTheme.GOLD, 74)
	var b := UiTheme.radial_texture(42, 22, UiTheme.GOLD, 74)
	_expect(a == b, "radial_texture kunci sama -> instance sama")
	_expect(a != UiTheme.radial_texture(42, 22, UiTheme.GOLD, 72),
		"radial_texture alpha beda -> instance beda")
	_expect(a != UiTheme.radial_texture(42, 22, UiTheme.CYAN, 74),
		"radial_texture warna beda -> instance beda")
	var s1 := UiTheme.shadow_texture(100, 50, 12.0, 110, 4.0)
	var s2 := UiTheme.shadow_texture(100, 50, 12.0, 110, 4.0)
	_expect(s1 == s2, "shadow_texture kunci sama -> instance sama")
	UiTheme.clear_caches()
	_expect(a != UiTheme.radial_texture(42, 22, UiTheme.GOLD, 74),
		"clear_caches() mengosongkan cache glow")
	_expect(s1 != UiTheme.shadow_texture(100, 50, 12.0, 110, 4.0),
		"clear_caches() mengosongkan cache bayangan")
	# pyrect: pygame.Rect memotong (bukan membulatkan) koordinat float.
	_expect(UiTheme.pyrect(Rect2(10.7, -2.3, 30.9, 4.1))
		== Rect2(10, -2, 30, 4), "pyrect memotong ke int")


func _finish() -> void:
	if _done:
		return
	_done = true
	if _failures == 0:
		print("[%s] PASS: ui_theme.py ↔ UiTheme.gd (%d checks)"
			% [LABEL, _checks])
	else:
		for msg in _errors:
			print(msg)
		print("[%s] FAIL: %d failures dari %d checks"
			% [LABEL, _failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
