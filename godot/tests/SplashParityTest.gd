extends Node
## Tes paritas splash_screen.py <-> godot/scripts/ui/SplashModel.gd (FASE 38).
##
## Semua angka pembanding datang dari fixture yang direkam ORACLE PYTHON
## (tools/test_godot_splash_parity.py). Oracle itu MENJALANKAN SplashScreen
## pygame ASLI (SDL dummy + font palsu 7px/karakter + TrackSurface) lalu
## merekam:
##   * timeline 4 skenario x 200 frame: title_alpha, _overall_alpha(), done,
##     dan DUA bendera skip (yang berlaku saat update() — menentukan `done` —
##     serta yang berlaku saat alpha direkam, karena skip() hanya menyetel
##     bendera dan done baru dihitung update() frame berikutnya),
##   * partikel: 46 partikel ber-seed, 120 langkah update + nilai respawn RNG
##     (random.uniform di-spy) + triplet gambar (posisi trunc, radius, warna
##     twinkle) pada elapsed 1.5,
##   * latar: 48 batang gradien + 70 bingkai vignette + 9 probe PIKSEL hasil
##     render (membuktikan interior layar HITAM pekat karena alpha vignette
##     menjenuh ke 255 pada i <= 24, 12 bingkai),
##   * logo: skala, ukuran dasar, tabel grow 10 baris, 64 cincin glow,
##   * glow judul: 3 lapisan, rect permukaan, fill, 4 baris garis aksen,
##   * hint: alpha + posisi,
##   * draw_order: urutan blit + primitif gambar 2 skenario (dengan/tanpa logo).
##
## Scene ini memutar ulang fixture itu lewat SplashBackend dengan backend
## DIPAKSA "gdscript" (SplashModel.gd) — jalur default produksi, tanpa
## compiler. Jalur C++ (MysticSplash) diuji SplashGdextParityTest.gd di
## godot-gdext.yml; angka C++ sendiri dikunci tools/test_splash_cpp_selftest.py
## (1585 cek dengan checkout godot-cpp, 1580 tanpa; tanpa engine) terhadap
## fixture yang sama.
##
## Jalankan:
##   godot --headless --path godot res://tests/SplashParityTest.tscn \
##       --quit-after 200
## Regenerasi fixture (setelah splash_screen.py berubah):
##   python3 tools/test_godot_splash_parity.py --write-fixture

const FIXTURE := "res://tests/fixtures/splash_parity.json"
const LABEL := "SplashParityTest"
const Backend := preload("res://scripts/ui/SplashBackend.gd")
const SCREEN_W := 1280
const SCREEN_H := 720

## Backend yang dipaksa scene ini; SplashGdextParityTest menimpanya ke "gdext".
var backend_override := "gdscript"

var _fx: Dictionary = {}
var _checks := 0
var _failures := 0
var _done := false
var _errors: Array[String] = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	Backend.force_backend(backend_override)
	_load_fixture()
	if _failures == 0:
		_test_meta()
		_test_constants()
		_test_timeline()
		_test_particles()
		_test_bg()
		_test_logo()
		_test_title_glow()
		_test_hint()
		_test_draw_order()
		await _test_scene_smoke()
	_finish()


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════

func _load_fixture() -> void:
	var parsed: Variant = JSON.parse_string(
		FileAccess.get_file_as_string(FIXTURE))
	_expect(parsed is Dictionary,
		"fixture splash_parity.json terbaca (jalankan python3 tools/"
		+ "test_godot_splash_parity.py --write-fixture)")
	if parsed is Dictionary:
		_fx = parsed


func _sec(section: String) -> Dictionary:
	var v: Variant = _fx.get(section)
	_expect(v is Dictionary, "seksi fixture \"%s\" ada" % section)
	return v if v is Dictionary else {}


func _arr(section: String) -> Array:
	var v: Variant = _fx.get(section)
	_expect(v is Array, "seksi fixture \"%s\" berupa Array" % section)
	return v if v is Array else []


## Warna pygame direkam oracle sebagai [r, g, b] (alpha 255).
func _col(rgb: Variant) -> Color:
	return Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))


func _rect4(a: Variant) -> Rect2:
	return Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3]))


func _v2(a: Variant) -> Vector2:
	return Vector2(float(a[0]), float(a[1]))


func _expect(cond: bool, msg: String) -> void:
	_checks += 1
	if not cond:
		_fail(msg)


func _expect_near(got: float, want: float, tol: float, msg: String) -> void:
	_checks += 1
	if absf(got - want) > tol:
		_fail("%s: dapat %.10f, mau %.10f (tol %g)" % [msg, got, want, tol])


func _expect_color(got: Color, want: Variant, msg: String) -> void:
	_checks += 1
	var target := _col(want)
	if got.r8 != target.r8 or got.g8 != target.g8 or got.b8 != target.b8:
		_fail("%s: dapat [%d, %d, %d], mau %s"
			% [msg, got.r8, got.g8, got.b8, want])


## Probe piksel: pembulatan blend pygame bisa beda 1/255 dari float Godot.
func _expect_color_near(got: Color, want: Variant, msg: String) -> void:
	var target := _col(want)
	for pair in [[got.r8, target.r8, "r"], [got.g8, target.g8, "g"],
			[got.b8, target.b8, "b"]]:
		_expect_near(float(pair[0]), float(pair[1]), 1.0,
			"%s.%s" % [msg, pair[2]])


## Rect pygame bulat; sisi Godot float -> toleransi sangat sempit.
func _expect_rect(got: Rect2, want: Variant, msg: String) -> void:
	var parts := ["x", "y", "w", "h"]
	var got4 := [got.position.x, got.position.y, got.size.x, got.size.y]
	for i in 4:
		_expect_near(float(got4[i]), float(want[i]), 0.001,
			"%s.%s" % [msg, parts[i]])


func _expect_v2(got: Vector2, want: Variant, msg: String) -> void:
	_expect(int(got.x) == int(want[0]) and int(got.y) == int(want[1]),
		"%s: dapat (%d, %d), mau %s" % [msg, int(got.x), int(got.y), want])


func _expect_deep(a: Variant, b: Variant, msg: String) -> void:
	_checks += 1
	if not _deep_eq(a, b):
		_fail("%s: dapat %s, mau %s" % [msg, _canon(a), _canon(b)])


func _expect_dict_int(got: Dictionary, want: Variant, msg: String) -> void:
	_expect(want is Dictionary, "%s: terekam di fixture" % msg)
	if not (want is Dictionary):
		return
	_expect(got.size() == (want as Dictionary).size(),
		"%s: jumlah kunci %d != %d" % [msg, got.size(),
		(want as Dictionary).size()])
	for key in (want as Dictionary):
		_expect(got.has(key), "%s: kunci \"%s\" ada" % [msg, key])
		if got.has(key):
			_expect(int(got[key]) == int((want as Dictionary)[key]),
				"%s.%s: dapat %s, mau %s" % [msg, key, str(got[key]),
				str((want as Dictionary)[key])])


func _expect_dict_str(got: Dictionary, want: Variant, msg: String) -> void:
	_expect(want is Dictionary, "%s: terekam di fixture" % msg)
	if not (want is Dictionary):
		return
	_expect(got.size() == (want as Dictionary).size(),
		"%s: jumlah kunci" % msg)
	for key in (want as Dictionary):
		_expect(str(got.get(key)) == str((want as Dictionary)[key]),
			"%s.%s: dapat %s, mau %s" % [msg, key, str(got.get(key)),
			str((want as Dictionary)[key])])


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
	if (a is float or a is int) and (b is float or b is int):
		return absf(float(a) - float(b)) < 0.000000001
	return a == b


func _canon(v: Variant) -> String:
	var text := str(v)
	if text.length() > 300:
		return text.substr(0, 300) + "…"
	return text


# ══════════════════════════════════════════════════════════
#  META + KONSTANTA
# ══════════════════════════════════════════════════════════

func _test_meta() -> void:
	var meta := _sec("meta")
	_expect(str(meta.get("source")) == "splash_screen.py", "meta.source")
	_expect_v2(_v2(meta.get("screen")), [SCREEN_W, SCREEN_H], "meta.screen")
	_expect_near(float(meta.get("dt")), 1.0 / 60.0, 0.000000000001, "meta.dt")
	_expect_deep(Backend.module_names(), ["splash_screen"], "module_names()")
	_expect(str(Backend.module_names_string()) == "splash_screen",
		"module_names_string()")
	var signature := str(Backend.api_signature())
	_expect(signature == "splash_v1:1mod:62fn:",
		"api_signature(): dapat %s" % signature)
	_expect(str(Backend.backend_name()) == backend_override,
		"backend_name(): dapat %s, mau %s"
		% [str(Backend.backend_name()), backend_override])


func _test_constants() -> void:
	var c := _sec("constants")
	_expect(str(Backend.game_name()) == str(c.get("game_name")), "GAME_NAME")
	_expect(str(Backend.tagline()) == str(c.get("tagline")), "TAGLINE")
	_expect(str(Backend.hint_text()) == str(c.get("hint_text")), "HINT_TEXT")
	_expect_near(Backend.splash_duration(), float(c.get("duration")),
		0.000000000001, "SPLASH_DURATION")
	_expect_deep(Backend.logo_paths(), c.get("logo_paths"), "logo_paths()")
	_expect_color(Backend.accent(), c.get("accent"), "ACCENT")
	_expect_color(Backend.accent_2(), c.get("accent_2"), "ACCENT_2")
	_expect_color(Backend.text_main(), c.get("text_main"), "TEXT_MAIN")
	_expect_color(Backend.text_dim(), c.get("text_dim"), "TEXT_DIM")

	var grad: Dictionary = Backend.gradient_stops()
	var want_grad: Dictionary = c.get("gradient")
	for key in ["top", "mid", "bot"]:
		_expect_color(grad.get(key), want_grad.get(key), "GRAD_%s" % key)

	var cols: Array = Backend.particle_colors()
	var want_cols: Array = c.get("particle_colors")
	_expect(cols.size() == want_cols.size(),
		"particle_colors(): %d != %d" % [cols.size(), want_cols.size()])
	for i in cols.size():
		_expect_color(cols[i], want_cols[i], "particle_colors()[%d]" % i)

	_expect_dict_int(Backend.font_sizes(), c.get("font_sizes"), "font_sizes()")
	_expect_dict_int(Backend.font_fallback_sizes(),
		c.get("font_fallback_sizes"), "font_fallback_sizes()")
	_expect_dict_str(Backend.font_styles(), c.get("font_styles"),
		"font_styles()")
	_expect(Backend.particle_count() == int(c.get("particle_count")),
		"PARTICLE_COUNT: dapat %d, mau %d"
		% [Backend.particle_count(), int(c.get("particle_count"))])

	var ranges: Dictionary = Backend.particle_ranges()
	var want_ranges: Dictionary = c.get("particle_ranges")
	for key in ["r", "speed", "drift", "phase"]:
		var pair: Array = want_ranges.get(key)
		_expect_near(float(ranges.get(str(key) + "_lo")), float(pair[0]),
			0.000000000001, "particle_ranges().%s_lo" % key)
		_expect_near(float(ranges.get(str(key) + "_hi")), float(pair[1]),
			0.000000000001, "particle_ranges().%s_hi" % key)

	var t: Dictionary = Backend.timings()
	var want_t: Dictionary = c.get("timings")
	_expect(t.size() == want_t.size(),
		"timings(): %d kunci != %d" % [t.size(), want_t.size()])
	for key in want_t:
		_expect(t.has(key), "timings() punya \"%s\"" % key)
		if t.has(key):
			_expect_near(float(t[key]), float(want_t[key]),
				0.000000000001, "timings().%s" % key)

	# glow_layers + accent_offsets pygame terkunci lewat API turunannya.
	var want_layers: Array = c.get("glow_layers")
	var layers: Array = Backend.title_glow_layers(true)
	_expect(layers.size() == want_layers.size(),
		"title_glow_layers(true): %d != %d" % [layers.size(),
		want_layers.size()])
	for i in layers.size():
		var got: Dictionary = layers[i]
		var want: Array = want_layers[i]
		_expect(int(got.get("layer")) == int(want[0])
			and int(got.get("spread")) == int(want[1]),
			"title_glow_layers(true)[%d]: dapat %s, mau %s"
			% [i, _canon(got), _canon(want)])
	_expect_deep(Backend.title_glow_layers(false), [],
		"title_glow_layers(false) kosong (alpha murahan pygame)")

	var want_off: Array = c.get("accent_offsets")
	var lines: Array = Backend.accent_lines(255.0)
	_expect(lines.size() == want_off.size(),
		"accent_lines(): %d != %d" % [lines.size(), want_off.size()])
	for i in lines.size():
		_expect(int((lines[i] as Dictionary).get("off")) == int(want_off[i][0]),
			"accent_lines()[%d].off" % i)


# ══════════════════════════════════════════════════════════
#  TIMELINE (4 skenario x 200 frame)
# ══════════════════════════════════════════════════════════

func _test_timeline() -> void:
	var scenarios := _arr("timeline")
	var t: Dictionary = Backend.timings()
	var duration := float(t.get("duration"))
	var fade_in_t := float(t.get("fade_in"))
	var fade_out_t := float(t.get("fade_out"))
	var skip_fade := float(t.get("skip_fade"))
	var skip_done := float(t.get("skip_done"))
	var epsilon := float(t.get("alpha_epsilon"))
	for scen_v in scenarios:
		var scen: Dictionary = scen_v
		var sname := str(scen.get("name"))
		var skip_at: Variant = scen.get("skip_at")
		var rows: Array = scen.get("rows")
		_expect(rows.size() == 200, "%s: 200 baris (dapat %d)"
			% [sname, rows.size()])
		for idx in rows.size():
			var row: Array = rows[idx]
			var elapsed := float(row[0])
			var want_title := int(row[1])
			var want_overall := float(row[2])
			var want_done := bool(row[3])
			var skipped_update := bool(row[4])
			var skipped_alpha := bool(row[5])
			var tag := "%s[%d]" % [sname, idx]

			_expect(Backend.title_alpha(elapsed) == want_title,
				"%s title_alpha: dapat %d, mau %d"
				% [tag, Backend.title_alpha(elapsed), want_title])
			_expect_near(Backend.overall_alpha(elapsed, skipped_alpha),
				want_overall, 0.000000001, "%s overall_alpha" % tag)
			# `done` direkam SESUDAH skip() frame itu, tapi skip() hanya
			# menyetel bendera — jadi update() yang menghitungnya masih
			# memakai bendera LAMA (row[4]).
			_expect(Backend.is_done(elapsed, skipped_update) == want_done,
				"%s is_done: dapat %s, mau %s"
				% [tag, str(Backend.is_done(elapsed, skipped_update)),
				str(want_done)])
			_expect(Backend.draw_visible(want_overall)
				== (want_overall > epsilon), "%s draw_visible" % tag)
			_expect(Backend.title_alpha_drawn(want_title, want_overall)
				== int(float(want_title) * want_overall),
				"%s title_alpha_drawn" % tag)

			# Semantik port Godot LAMA (skip_t sejak tombol skip) — dikunci
			# sebagai cermin supaya deviasi FASE 38 tetap terlihat di A/B.
			var skip_t := 0.0
			if skipped_alpha and skip_at != null:
				skip_t = maxf(0.0, elapsed - float(skip_at))
			var want_fade := 0.0
			if skipped_alpha:
				want_fade = maxf(0.0, 1.0 - skip_t / skip_fade)
			else:
				want_fade = minf(1.0, maxf(0.0,
					(duration - elapsed) / fade_out_t))
			_expect_near(Backend.overall_alpha_godot(elapsed, skipped_alpha,
				skip_t), clampf(minf(1.0, elapsed / fade_in_t) * want_fade,
				0.0, 1.0), 0.000000000001, "%s overall_alpha_godot" % tag)
			var skip_t_u := 0.0
			if skipped_update and skip_at != null:
				skip_t_u = maxf(0.0, elapsed - float(skip_at))
			var want_done_g := false
			if skipped_update:
				want_done_g = skip_t_u >= skip_done
			else:
				want_done_g = elapsed >= duration
			_expect(Backend.is_done_godot(elapsed, skipped_update, skip_t_u)
				== want_done_g, "%s is_done_godot" % tag)
			_expect_near(Backend.fade_in(elapsed),
				minf(1.0, elapsed / fade_in_t), 0.000000000001,
				"%s fade_in" % tag)
			_expect_near(Backend.fade_out_normal(elapsed),
				minf(1.0, maxf(0.0, (duration - elapsed) / fade_out_t)),
				0.000000000001, "%s fade_out_normal" % tag)
			_expect_near(Backend.fade_out_skip(elapsed),
				maxf(0.0, 1.0 - elapsed / skip_fade), 0.000000000001,
				"%s fade_out_skip" % tag)


# ══════════════════════════════════════════════════════════
#  PARTIKEL (rantai 120 frame + triplet gambar)
# ══════════════════════════════════════════════════════════

func _test_particles() -> void:
	var sec := _sec("particles")
	var frames := int(sec.get("frames"))
	var initial: Array = sec.get("initial")
	var respawn: Array = sec.get("respawn")
	var want_final: Array = sec.get("final")
	_expect(initial.size() == Backend.particle_count(),
		"jumlah partikel fixture == particle_count()")

	# Rantai: posisi awal fixture -> 120 x particle_advance. Nilai respawn RNG
	# pygame (random.uniform di-spy oracle) disuapkan berurutan.
	var states := _clone_particles(initial)
	var dt := float((_sec("meta")).get("dt"))
	var elapsed := 0.0
	var ri := 0
	var wraps := 0
	for _frame in frames:
		# pygame mengakumulasi elapsed (+= dt), bukan (frame+1)*dt — bit-bit
		# terakhirnya beda dan ikut menentukan ambang wrap.
		elapsed += dt
		for i in states.size():
			var st: Dictionary = states[i]
			var rx := 0.0
			if ri < respawn.size():
				rx = float((respawn[ri] as Array)[2])
			var res: Dictionary = Backend.particle_advance(float(st["x"]),
				float(st["y"]), float(st["speed"]), float(st["drift"]),
				float(st["phase"]), elapsed, float(SCREEN_H), rx)
			if bool(res.get("wrapped")):
				wraps += 1
				ri += 1
			st["x"] = float(res.get("x"))
			st["y"] = float(res.get("y"))
	_expect(ri == respawn.size(),
		"respawn RNG terpakai %d dari %d" % [ri, respawn.size()])
	_expect(wraps == respawn.size(),
		"jumlah wrap %d != respawn %d" % [wraps, respawn.size()])

	for i in states.size():
		var st: Dictionary = states[i]
		var want: Dictionary = want_final[i]
		_expect_near(float(st["x"]), float(want["x"]), 0.000000001,
			"partikel[%d].x final" % i)
		_expect_near(float(st["y"]), float(want["y"]), 0.000000001,
			"partikel[%d].y final" % i)
		for key in ["r", "speed", "drift", "phase"]:
			_expect_near(float(st[key]), float(want[key]),
				0.000000000001, "partikel[%d].%s tak berubah" % [i, key])

	# Triplet gambar pada elapsed 1.5 (posisi = hasil rantai 120 frame).
	var draws: Array = sec.get("draw_at_1_5")
	_expect(draws.size() == states.size(), "draw_at_1_5: %d baris"
		% draws.size())
	for i in states.size():
		var st: Dictionary = states[i]
		var want: Dictionary = draws[i]
		var tw := Backend.particle_twinkle(1.5, float(st["phase"]))
		_expect_near(tw, float(want.get("twinkle")), 0.000000000001,
			"particle_twinkle[%d]" % i)
		_expect_color(Backend.particle_draw_color(_col(st["color"]), tw),
			want.get("color"), "particle_draw_color[%d]" % i)
		_expect(Backend.particle_draw_radius(float(st["r"]))
			== int(want.get("radius")),
			"particle_draw_radius[%d]: dapat %d, mau %d"
			% [i, Backend.particle_draw_radius(float(st["r"])),
			int(want.get("radius"))])
		_expect_v2(Backend.particle_draw_pos(float(st["x"]), float(st["y"])),
			want.get("pos"), "particle_draw_pos[%d]" % i)

	# Ambang + helper satuan.
	_expect(Backend.particle_wrapped(-6.5)
		and not Backend.particle_wrapped(-6.0)
		and not Backend.particle_wrapped(0.0),
		"particle_wrapped: ambang y < -6 (bukan <=)")
	_expect_near(Backend.particle_wrap_y(float(SCREEN_H)), 726.0,
		0.000000000001, "particle_wrap_y(720) = h + 6")
	_expect_near(Backend.particle_twinkle(0.0, 0.0), 0.5,
		0.000000000001, "particle_twinkle(0, 0) = 0.5")
	_expect(Backend.particle_channel(255, 1.0) == 255
		and Backend.particle_channel(255, 0.0) == 89,
		"particle_channel: 255 -> 255 (twinkle 1) / 89 (twinkle 0)")
	var moved: Dictionary = Backend.particle_move(100.0, 50.0, 0.25, 0.1,
		1.0, 1.5)
	_expect_near(float(moved.get("y")), 49.75, 0.000000000001,
		"particle_move().y = y - speed")
	_expect_near(float(moved.get("x")),
		100.0 + 0.1 + sin(1.5 * 0.8 + 1.0) * 0.05, 0.000000000001,
		"particle_move().x = x + drift + sin(t*0.8+phase)*0.05")


func _clone_particles(initial: Array) -> Array:
	var out: Array = []
	for p_v in initial:
		var p: Dictionary = p_v
		out.append({"x": float(p["x"]), "y": float(p["y"]),
			"r": float(p["r"]), "speed": float(p["speed"]),
			"drift": float(p["drift"]), "phase": float(p["phase"]),
			"color": p["color"]})
	return out


# ══════════════════════════════════════════════════════════
#  LATAR (48 batang gradien + 70 bingkai vignette + piksel)
# ══════════════════════════════════════════════════════════

func _test_bg() -> void:
	var sec := _sec("bg")
	var want_bands: Array = sec.get("bands")
	var want_vig: Array = sec.get("vignette")
	_expect(Backend.bg_step_h(SCREEN_H) == 15,
		"bg_step_h(720): dapat %d, mau 15" % Backend.bg_step_h(SCREEN_H))
	_expect(Backend.bg_band_count(SCREEN_H) == want_bands.size(),
		"bg_band_count(720) == 48 batang fixture")

	var bands: Array = Backend.bg_bands(SCREEN_W, SCREEN_H)
	_expect(bands.size() == want_bands.size(),
		"bg_bands(): %d != %d" % [bands.size(), want_bands.size()])
	# Argumen pertama bg_band_rect/bg_band_color adalah Y PIKSEL — pygame
	# menulis `for i in range(0, self.h, step_h)` sehingga `i` di sana adalah
	# baris piksel, bukan indeks batang. Mengirim indeks batang membuat
	# f = i/720 selalu < 0.55 dan semua batang keluar berwarna batang 0
	# (46 cek engine merah di CI sebelum ini diperbaiki).
	var step_h: int = Backend.bg_step_h(SCREEN_H)
	for i in bands.size():
		var got: Dictionary = bands[i]
		var want: Dictionary = want_bands[i]
		var y: int = i * step_h
		_expect_rect(got.get("rect"), want.get("rect"),
			"bg_bands[%d].rect" % i)
		_expect_color(got.get("color"), want.get("color"),
			"bg_bands[%d].color" % i)
		_expect_rect(Backend.bg_band_rect(y, step_h, SCREEN_W),
			want.get("rect"), "bg_band_rect(y=%d)" % y)
		_expect_color(Backend.bg_band_color(y, SCREEN_H), want.get("color"),
			"bg_band_color(y=%d)" % y)

	var vig: Array = Backend.vignette_frames(SCREEN_W, SCREEN_H)
	_expect(vig.size() == want_vig.size(),
		"vignette_frames(): %d != %d" % [vig.size(), want_vig.size()])
	var saturated := 0
	for i in vig.size():
		var got: Dictionary = vig[i]
		var want: Dictionary = want_vig[i]
		_expect_rect(got.get("rect"), want.get("rect"),
			"vignette[%d].rect" % i)
		_expect(int(got.get("alpha")) == int(want.get("alpha")),
			"vignette[%d].alpha: dapat %s, mau %s"
			% [i, str(got.get("alpha")), str(want.get("alpha"))])
		if int(want.get("alpha")) >= 255:
			saturated += 1
	# Temuan oracle: alpha menjenuh ke 255 pada 12 bingkai terakhir (i <= 24)
	# sehingga interior layar HITAM pekat dan hanya rim 2px (i < 2) yang
	# menampakkan gradien — port lama menggambar vignette tipis (salah).
	_expect(saturated == 12,
		"vignette: 12 bingkai alpha 255 (interior hitam), dapat %d" % saturated)

	var pixels: Dictionary = sec.get("pixels")
	_expect(pixels.size() == 9, "bg.pixels: 9 probe")
	for key in pixels:
		var parts := str(key).split(",")
		var probe := Vector2i(int(parts[0]), int(parts[1]))
		_expect_color_near(_composite(bands, vig, probe), pixels[key],
			"bg.pixels[%s]" % key)


## Kompositor paritas pygame: batang gradien ditimpa bingkai vignette hitam
## ber-alpha (SDL blend = dst * (255 - a) / 255 untuk sumber hitam).
func _composite(bands: Array, vig: Array, at: Vector2i) -> Color:
	var base := Color8(0, 0, 0)
	var probe := Vector2(float(at.x), float(at.y))
	for b_v in bands:
		var b: Dictionary = b_v
		if (b.get("rect") as Rect2).has_point(probe):
			base = b.get("color")
	var ch := [float(base.r8), float(base.g8), float(base.b8)]
	for v_v in vig:
		var v: Dictionary = v_v
		var a := int(v.get("alpha"))
		if a > 0 and (v.get("rect") as Rect2).has_point(probe):
			for k in 3:
				ch[k] = ch[k] * float(255 - a) / 255.0
	return Color8(int(ch[0]), int(ch[1]), int(ch[2]))


# ══════════════════════════════════════════════════════════
#  LOGO (skala, grow, cincin glow)
# ══════════════════════════════════════════════════════════

func _test_logo() -> void:
	var sec := _sec("logo")
	var img: Array = sec.get("image")
	var iw := int(img[0])
	var ih := int(img[1])
	_expect_near(Backend.logo_scale(iw, ih), float(sec.get("scale")),
		0.000000000001, "logo_scale(%d, %d)" % [iw, ih])
	var want_base: Array = sec.get("base")
	var base: Vector2 = Backend.logo_base_size(iw, ih)
	_expect_v2(base, want_base, "logo_base_size(%d, %d)" % [iw, ih])

	var grow: Array = sec.get("grow_table")
	for row_v in grow:
		var row: Dictionary = row_v
		var t := float(row.get("elapsed"))
		var gq := Backend.logo_grow_quant(t)
		_expect_near(gq, float(row.get("gq")), 0.000000000001,
			"logo_grow_quant(%s)" % str(t))
		var size: Vector2 = Backend.logo_grow_size(base, gq)
		_expect_v2(size, row.get("size"), "logo_grow_size(t=%s)" % str(t))
		_expect(Backend.logo_glow_radius(int(size.x), int(size.y))
			== int(row.get("glow_radius")),
			"logo_glow_radius(t=%s): dapat %d, mau %d"
			% [str(t), Backend.logo_glow_radius(int(size.x), int(size.y)),
			int(row.get("glow_radius"))])

	var want_rings: Array = sec.get("rings_at_190")
	var rings: Array = Backend.logo_glow_rings(190)
	_expect(rings.size() == want_rings.size(),
		"logo_glow_rings(190): %d != %d" % [rings.size(), want_rings.size()])
	for i in rings.size():
		var got: Dictionary = rings[i]
		var want: Array = want_rings[i]
		_expect(int(got.get("r")) == int(want[0])
			and int(got.get("alpha")) == int(want[1]),
			"logo_glow_rings(190)[%d]: dapat %s, mau %s"
			% [i, _canon(got), _canon(want)])
	# Cincin HARUS mengecil (langkah -3): +3 = loop tak berujung di C++.
	_expect(rings.size() > 1
		and int((rings[1] as Dictionary).get("r"))
		< int((rings[0] as Dictionary).get("r")),
		"logo_glow_rings menurun (langkah -3)")

	var center: Vector2 = Backend.content_center(SCREEN_W, SCREEN_H)
	_expect_v2(center, [SCREEN_W / 2, SCREEN_H / 2], "content_center")
	var lift := int(sec.get("center_y_lift"))
	_expect_near(Backend.logo_center_y(center.y, true),
		center.y - float(lift), 0.000000000001, "logo_center_y(ada logo)")
	_expect_near(Backend.logo_center_y(center.y, false), center.y,
		0.000000000001, "logo_center_y(tanpa logo)")
	var offs: Dictionary = Backend.logo_offsets()
	_expect(offs.size() == 4, "logo_offsets(): 4 kunci")
	_expect(int(offs.get("logo_lift")) == lift,
		"logo_offsets().logo_lift == %d" % lift)
	for key in ["title_below", "sub_below", "sub_text_only"]:
		_expect(offs.has(key), "logo_offsets() punya \"%s\"" % key)

	var glow_r := 190
	var cy := Backend.logo_center_y(center.y, true)
	_expect_rect(Backend.logo_glow_rect(center.x, cy, glow_r),
		[center.x - float(glow_r), cy - float(glow_r),
		float(glow_r * 2), float(glow_r * 2)], "logo_glow_rect")


# ══════════════════════════════════════════════════════════
#  GLOW JUDUL + AKSEN
# ══════════════════════════════════════════════════════════

func _test_title_glow() -> void:
	var sec := _sec("title_glow")
	var text_rect := _rect4(sec.get("text_rect"))
	var want_layers: Array = sec.get("layers")
	var layers: Array = Backend.title_glow_layers(
		bool((_sec("meta")).get("cheap_alpha")))
	_expect(layers.size() == want_layers.size(),
		"title_glow_layers: %d != %d" % [layers.size(), want_layers.size()])
	for i in layers.size():
		var got: Dictionary = layers[i]
		var want: Array = want_layers[i]
		_expect(int(got.get("layer")) == int(want[0])
			and int(got.get("spread")) == int(want[1]),
			"title_glow_layers[%d]" % i)

	var surfaces: Array = sec.get("surfaces")
	for s_v in surfaces:
		var want: Dictionary = s_v
		var got: Rect2 = Backend.title_glow_surface(text_rect,
			int(want.get("layer")), int(want.get("spread")))
		_expect_rect(got, want.get("rect"),
			"title_glow_surface(layer=%d, spread=%d)"
			% [int(want.get("layer")), int(want.get("spread"))])

	for f_v in sec.get("fills"):
		var row: Array = f_v
		_expect(Backend.title_glow_fill(float(row[0])) == int(row[1]),
			"title_glow_fill(%d): dapat %d, mau %d"
			% [int(row[0]), Backend.title_glow_fill(float(row[0])),
			int(row[1])])

	var text_w := int(text_rect.size.x)
	for a_v in sec.get("accent"):
		var row: Dictionary = a_v
		var alpha := int(row.get("alpha"))
		_expect(Backend.accent_gap(text_w) == int(row.get("gap")),
			"accent_gap(%d): dapat %d, mau %d"
			% [text_w, Backend.accent_gap(text_w), int(row.get("gap"))])
		var lines: Array = Backend.accent_lines(float(alpha))
		var found := false
		for line_v in lines:
			var line: Dictionary = line_v
			if int(line.get("off")) != int(row.get("off")):
				continue
			found = true
			_expect_color(line.get("color"), row.get("color"),
				"accent_lines(%d) off=%d warna" % [alpha, int(row.get("off"))])
			_expect(int(line.get("width")) == int(row.get("width")),
				"accent_lines(%d) off=%d lebar" % [alpha,
				int(row.get("off"))])
			var left: Array = row.get("left")
			_expect(int(line.get("len")) == int(left[2]) - int(left[0]),
				"accent_lines(%d) off=%d panjang" % [alpha,
				int(row.get("off"))])
		_expect(found, "accent_lines(%d) punya off=%d"
			% [alpha, int(row.get("off"))])


# ══════════════════════════════════════════════════════════
#  HINT
# ══════════════════════════════════════════════════════════

func _test_hint() -> void:
	var sec := _sec("hint")
	_expect(str(Backend.hint_text()) == str(sec.get("text")), "hint_text()")
	var rows: Array = sec.get("rows")
	_expect(rows.size() == 4, "hint.rows: 4 baris")
	for r_v in rows:
		var row: Dictionary = r_v
		var overall := float(row.get("overall"))
		_expect(Backend.hint_alpha(overall) == int(row.get("alpha")),
			"hint_alpha(%s): dapat %d, mau %d"
			% [str(overall), Backend.hint_alpha(overall),
			int(row.get("alpha"))])
		_expect_v2(Backend.hint_pos(SCREEN_W, SCREEN_H), row.get("pos"),
			"hint_pos (overall=%s)" % str(overall))


# ══════════════════════════════════════════════════════════
#  DRAW ORDER (urutan blit + primitif yang direkam pygame)
# ══════════════════════════════════════════════════════════

func _test_draw_order() -> void:
	var scenarios := _arr("draw_order")
	_expect(scenarios.size() == 2, "draw_order: 2 skenario")
	var initial: Array = (_sec("particles")).get("initial")
	for scen_v in scenarios:
		var scen: Dictionary = scen_v
		var with_logo := bool(scen.get("with_logo"))
		var elapsed := float(scen.get("elapsed"))
		var tag := "draw_order(logo=%s, t=%s)" % [str(with_logo), str(elapsed)]
		var seq: Array = scen.get("sequence")
		var blits: Array = []
		var circles: Array = []
		var lines: Array = []
		for op_v in seq:
			var op: Dictionary = op_v
			match str(op.get("kind")):
				"blit":
					blits.append(op)
				"circle":
					circles.append(op)
				"line":
					lines.append(op)
		_expect(blits.size() == int(scen.get("blit_count")),
			"%s: jumlah blit" % tag)
		_expect(circles.size() + lines.size()
			== int(scen.get("screen_draw_count")),
			"%s: jumlah primitif draw" % tag)

		# Partikel digambar dari state AWAL (oracle menyetel elapsed tanpa
		# update) -> triplet harus cocok dengan posisi fixture apa adanya.
		_expect(circles.size() == initial.size(),
			"%s: %d circle partikel" % [tag, circles.size()])
		for i in circles.size():
			var args: Array = (circles[i] as Dictionary).get("args")
			var st: Dictionary = initial[i]
			var tw := Backend.particle_twinkle(elapsed, float(st["phase"]))
			_expect_color(Backend.particle_draw_color(_col(st["color"]), tw),
				args[0], "%s circle[%d].color" % [tag, i])
			_expect_v2(Backend.particle_draw_pos(float(st["x"]),
				float(st["y"])), args[1], "%s circle[%d].pos" % [tag, i])
			_expect(Backend.particle_draw_radius(float(st["r"]))
				== int(args[2]), "%s circle[%d].radius" % [tag, i])

		# Latar selalu blit pertama di (0, 0).
		_expect(str((blits[0] as Dictionary).get("src")) == "bg",
			"%s: blit pertama = bg" % tag)
		_expect_deep((blits[0] as Dictionary).get("dest"), [0, 0],
			"%s: bg di (0, 0)" % tag)

		var tg := _sec("title_glow")
		var text_rect := _rect4(tg.get("text_rect"))
		var surfaces: Array = tg.get("surfaces")
		if with_logo:
			var srcs: Array = []
			for b_v in blits:
				srcs.append(str((b_v as Dictionary).get("src")))
			_expect_deep(srcs, ["bg", "logo_glow", "logo_img",
				"glow_title_0", "glow_title_1", "glow_title_2", "title_copy",
				"text:A MOBA TOWER DEFENSE ADVENTURE@22",
				"text:Tap anywhere to skip@16"],
				"%s: urutan blit dengan logo" % tag)
			# Rect glow + gambar logo dari API model (grow pada t=1.5 -> 1.0).
			var center: Vector2 = Backend.content_center(SCREEN_W, SCREEN_H)
			var cy := Backend.logo_center_y(center.y, true)
			var base: Vector2 = Backend.logo_base_size(1024, 1024)
			var size: Vector2 = Backend.logo_grow_size(base,
				Backend.logo_grow_quant(elapsed))
			var glow_r := Backend.logo_glow_radius(int(size.x), int(size.y))
			var glow_rect := Backend.logo_glow_rect(center.x, cy, glow_r)
			_expect_v2(_v2((blits[1] as Dictionary).get("dest")),
				[int(glow_rect.position.x), int(glow_rect.position.y)],
				"%s: dest logo_glow" % tag)
			_expect_v2(_v2((blits[2] as Dictionary).get("dest")),
				[int(center.x - size.x * 0.5), int(cy - size.y * 0.5)],
				"%s: dest logo_img" % tag)
		else:
			# Tanpa logo: rect glow judul == rect hasil title_glow_surface.
			for i in surfaces.size():
				var want: Dictionary = surfaces[i]
				var got: Rect2 = Backend.title_glow_surface(text_rect,
					int(want.get("layer")), int(want.get("spread")))
				var blit: Dictionary = blits[1 + i]
				_expect(str(blit.get("src")) == "glow_title_%d" % i,
					"%s: blit[%d] = glow_title_%d" % [tag, 1 + i, i])
				_expect_v2(_v2(blit.get("dest")),
					[int(got.position.x), int(got.position.y)],
					"%s: dest glow_title_%d" % [tag, i])
			var title_blit: Dictionary = blits[1 + surfaces.size()]
			_expect(str(title_blit.get("src")) == "title_copy",
				"%s: judul di-blit sesudah 3 lapisan glow" % tag)
			_expect_v2(_v2(title_blit.get("dest")),
				[int(text_rect.position.x), int(text_rect.position.y)],
				"%s: dest title_copy == text_rect" % tag)

		# 4 garis aksen: 2 warna x (kiri, kanan), panjang 46, lebar 2.
		var want_lines: Array = Backend.accent_lines(255.0)
		_expect(lines.size() == 4, "%s: 4 garis aksen (dapat %d)"
			% [tag, lines.size()])
		for i in lines.size():
			var args: Array = (lines[i] as Dictionary).get("args")
			var want: Dictionary = want_lines[i / 2]
			_expect_color(_col(args[0]),
				[(want.get("color") as Color).r8,
				(want.get("color") as Color).g8,
				(want.get("color") as Color).b8],
				"%s line[%d].color" % [tag, i])
			_expect(int(args[3]) == int(want.get("width")),
				"%s line[%d].width" % [tag, i])
			var p1: Array = args[1]
			var p2: Array = args[2]
			_expect(absi(int(p2[0]) - int(p1[0])) == int(want.get("len")),
				"%s line[%d].len" % [tag, i])
			_expect(int(p1[1]) == int(p2[1]),
				"%s line[%d] horizontal" % [tag, i])


# ══════════════════════════════════════════════════════════
#  SMOKE: scene SplashScreen betulan (renderer, bukan model)
# ══════════════════════════════════════════════════════════

func _test_scene_smoke() -> void:
	var splash := SplashScreen.new()
	var fired := [false]
	splash.finished.connect(func() -> void: fired[0] = true)
	add_child(splash)
	for _i in 8:
		await get_tree().process_frame
	_expect(is_instance_valid(splash), "SplashScreen hidup selama fade in")
	if not is_instance_valid(splash):
		return
	_expect(not splash.is_done(), "SplashScreen belum selesai di frame 8")
	# Partikel benar-benar bergerak lewat Backend.particle_advance.
	splash.skip()
	var waited := 0
	while is_instance_valid(splash) and not splash.is_done() and waited < 180:
		await get_tree().process_frame
		waited += 1
	_expect(fired[0], "signal finished dipancarkan setelah skip()")
	_expect(waited < 180,
		"skip() menyelesaikan splash (paritas elapsed >= 0.25 total)")
	if is_instance_valid(splash):
		splash.queue_free()


func _finish() -> void:
	if _done:
		return
	_done = true
	if _failures == 0:
		print("[%s] PASS: splash_screen.py ↔ SplashModel.gd backend %s "
			% [LABEL, backend_override]
			+ "(timeline 4x200 frame, rantai 46 partikel x 120 langkah, "
			+ "48 batang + 70 vignette + 9 piksel latar, logo, glow judul, "
			+ "hint, draw_order) — %d checks" % _checks)
		print("[%s] PASS" % LABEL)
	else:
		for msg in _errors:
			print(msg)
		print("[%s] FAIL: %d failures dari %d checks"
			% [LABEL, _failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
