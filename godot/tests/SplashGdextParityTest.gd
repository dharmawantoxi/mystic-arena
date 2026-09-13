# SplashGdextParityTest — splash_screen.py -> godot++ (C++).
#
# Scene ini memutar ULANG SplashParityTest (oracle Python: timeline 4 skenario
# x 200 frame, rantai 46 partikel x 120 langkah, 48 batang gradien + 70
# bingkai vignette + 9 probe piksel, logo, glow judul, hint, draw_order) dengan
# backend DIPAKSA ke GDExtension C++ (`MysticSplash`, lib hasil build
# godot/gdext/mystic_splash). Jadi yang diuji bukan "C++ sama dengan C++",
# melainkan "C++ sama dengan Python", lewat rantai:
#
#   splash_screen.py --(tools/test_godot_splash_parity.py)--> fixture
#   fixture <--dibandingkan--> SplashBackend -> MysticSplash (C++)
#
# SplashScreen.gd mengambil SEMUA angkanya dari SplashBackend, jadi memaksa
# backend di loader sudah cukup untuk mengalihkan splash ke C++ tanpa
# menyentuh renderer-nya.
#
# Ditambah baterai A/B backend: seluruh permukaan API (62 fungsi) dikumpulkan
# dua kali — C++ lalu GDScript — dan dibandingkan kunci demi kunci lewat
# str(Variant), yang ikut mengunci URUTAN kunci Dictionary, tipe nilai, dan
# presisi double: konstanta + timing, timeline 4 x 200 baris (title_alpha,
# overall_alpha, done, varian semantik Godot lama), rantai partikel 120 frame +
# triplet gambar, 48 batang + 70 vignette + kompositor 9 piksel, tabel grow
# logo + 64 cincin glow, rect glow judul + fill + garis aksen, dan hint.
#
# Scene ini HANYA berarti kalau lib GDExt sudah dibuild:
#   cd godot/gdext/mystic_splash
#   ln -s ../godot-cpp godot-cpp   (atau clone godot-4.3-stable)
#   scons platform=linux target=template_debug -j4
# Tanpa lib, scene GAGAL (bukan skip) — CI .github/workflows/godot-gdext.yml
# yang membuild lib lalu menjalankannya. Jalur GDScript murni tetap dijaga
# SplashParityTest di godot-check.yml (tanpa compiler), dan angka C++ di luar
# engine dikunci tools/test_splash_cpp_selftest.py (1585/1580 cek, g++ saja).
#
# godot --headless --path godot res://tests/SplashGdextParityTest.tscn --quit-after 200
# Require "[SplashGdextParityTest] PASS" + "GDExtension MysticSplash aktif".
extends "res://tests/SplashParityTest.gd"


func _boot() -> void:
	if not Backend.gdext_available():
		_fail_gdext("class MysticSplash tidak terdaftar engine",
			"build lib GDExt dulu (godot/gdext/mystic_splash/README.md) lalu "
			+ "jalankan scene ini — tanpa lib, jalur C++ tidak teruji")
		_abort()
		return
	Backend.force_backend("gdext")
	if not Backend.is_using_gdext():
		_fail_gdext("force_backend('gdext') tidak mengaktifkan jalur C++",
			"SplashBackend gagal instantiate MysticSplash")
		_abort()
		return
	backend_override = "gdext"
	print("[SplashGdextParityTest] backend=%s (class MysticSplash termuat, "
		% Backend.backend_name()
		+ "model %s)" % str(Backend.api_signature()))

	# A/B butuh fixture; base _boot() memuatnya lagi (murah).
	_load_fixture()
	if not _fx.is_empty():
		_ab_battery()

	# Sisa baterai = persis SplashParityTest, tapi tiap panggilan kini
	# masuk ke C++.
	super._boot()


## A/B backend: kumpulkan seluruh permukaan API satu backend, lalu bandingkan.
## Backend DIPAKSA per-batch (bukan per panggilan) — force_backend()
## me-resolve loader, jadi memanggilnya ribuan kali hanya menenggelamkan log.
func _ab_battery() -> void:
	var got_c := _collect("gdext")
	var got_g := _collect("gdscript")
	# Label backend BUKAN bagian permukaan API yang dibandingkan — isinya justru
	# HARUS beda. Kalau sama, force_backend() tidak benar-benar berpindah dan
	# seluruh A/B ini tidak berarti, jadi labelnya dijadikan assertion sendiri
	# lalu dibuang sebelum kamus dibandingkan kunci demi kunci.
	_expect(str(got_c.get("backend")) == "gdext"
		and str(got_g.get("backend")) == "gdscript",
		"force_backend() tidak mengganti backend (A=%s, B=%s) — A/B tidak "
		% [str(got_c.get("backend")), str(got_g.get("backend"))]
		+ "berarti")
	got_c.erase("backend")
	got_g.erase("backend")
	Backend.force_backend("gdext")
	var keys := got_c.keys()
	keys.sort()
	var mismatch := 0
	for k in keys:
		_checks += 1
		if str(got_c[k]) == str(got_g.get(k)):
			continue
		mismatch += 1
		_fail_gdext(str(k), "C++ %s vs GDScript %s"
			% [_canon(got_c[k]), _canon(got_g.get(k))])
	print("[SplashGdextParityTest] A/B backend: %d kunci (konstanta + "
		% keys.size()
		+ "timeline + partikel + latar + logo + glow judul + hint), "
		+ "mismatch %d" % mismatch)


func _collect(backend: String) -> Dictionary:
	Backend.force_backend(backend)
	var out := {}
	# Kunci "backend" = label batch ini (dipakai _ab_battery sebagai bukti
	# force_backend() bekerja); dihapus sebelum kamus A dan B dibandingkan.
	out["backend"] = Backend.backend_name()
	out["signature"] = str(Backend.api_signature())
	out["modules"] = str(Backend.module_names())
	out["texts"] = str([Backend.game_name(), Backend.tagline(),
		Backend.hint_text(), Backend.logo_paths()])
	out["colors"] = str([Backend.accent(), Backend.accent_2(),
		Backend.text_main(), Backend.text_dim(), Backend.gradient_stops(),
		Backend.particle_colors()])
	out["fonts"] = str([Backend.font_sizes(), Backend.font_fallback_sizes(),
		Backend.font_styles()])
	out["particles_meta"] = str([Backend.particle_count(),
		Backend.particle_ranges(), Backend.timings()])

	# Timeline: 4 skenario x 200 baris, semua predikat + alpha.
	var scenarios: Array = _fx.get("timeline")
	for scen_v in scenarios:
		var scen: Dictionary = scen_v
		var skip_at: Variant = scen.get("skip_at")
		var rows: Array = scen.get("rows")
		var acc: Array = []
		for row_v in rows:
			var row: Array = row_v
			var elapsed := float(row[0])
			var skipped_u := bool(row[4])
			var skipped_a := bool(row[5])
			var skip_t := 0.0
			if skipped_a and skip_at != null:
				skip_t = maxf(0.0, elapsed - float(skip_at))
			var skip_t_u := 0.0
			if skipped_u and skip_at != null:
				skip_t_u = maxf(0.0, elapsed - float(skip_at))
			acc.append([Backend.title_alpha(elapsed),
				Backend.overall_alpha(elapsed, skipped_a),
				Backend.is_done(elapsed, skipped_u),
				Backend.draw_visible(float(row[2])),
				Backend.title_alpha_drawn(int(row[1]), float(row[2])),
				Backend.overall_alpha_godot(elapsed, skipped_a, skip_t),
				Backend.is_done_godot(elapsed, skipped_u, skip_t_u),
				Backend.fade_in(elapsed),
				Backend.fade_out_normal(elapsed),
				Backend.fade_out_skip(elapsed)])
		out["timeline:" + str(scen.get("name"))] = str(acc)

	# Partikel: rantai 120 langkah + triplet gambar + helper satuan.
	var psec: Dictionary = _fx.get("particles")
	var initial: Array = psec.get("initial")
	var respawn: Array = psec.get("respawn")
	var dt := float((_sec("meta")).get("dt"))
	var states := _replay(initial, int(psec.get("frames")), respawn, dt)
	out["particles:chain"] = str(states)
	out["particles:draw"] = str(_triplets(states, 1.5))
	out["particles:helpers"] = str([
		Backend.particle_move(100.0, 50.0, 0.25, 0.1, 1.0, 1.5),
		Backend.particle_wrapped(-6.5), Backend.particle_wrapped(-6.0),
		Backend.particle_wrap_y(720.0), Backend.particle_twinkle(1.5, 0.7),
		Backend.particle_channel(255, 0.35),
		Backend.particle_draw_color(Color8(255, 210, 120), 0.6),
		Backend.particle_draw_radius(2.4),
		Backend.particle_draw_pos(1237.06, 317.33)])

	# Latar: batang gradien, vignette, dan kompositor probe piksel.
	var bands: Array = Backend.bg_bands(1280, 720)
	var vig: Array = Backend.vignette_frames(1280, 720)
	out["bg:step"] = str([Backend.bg_step_h(720), Backend.bg_band_count(720)])
	out["bg:bands"] = str(bands)
	out["bg:vignette"] = str(vig)
	var probes: Array = []
	for key in (_sec("bg").get("pixels") as Dictionary):
		var parts := str(key).split(",")
		probes.append([key, _composite(bands, vig,
			Vector2i(int(parts[0]), int(parts[1])))])
	out["bg:pixels"] = str(probes)

	# Logo + konten.
	var lsec: Dictionary = _fx.get("logo")
	var img: Array = lsec.get("image")
	var base: Vector2 = Backend.logo_base_size(int(img[0]), int(img[1]))
	var grow_acc: Array = []
	for row_v in lsec.get("grow_table"):
		var row: Dictionary = row_v
		var t := float(row.get("elapsed"))
		var gq := Backend.logo_grow_quant(t)
		var size: Vector2 = Backend.logo_grow_size(base, gq)
		grow_acc.append([t, gq, size,
			Backend.logo_glow_radius(int(size.x), int(size.y))])
	out["logo:grow"] = str(grow_acc)
	out["logo:rings"] = str(Backend.logo_glow_rings(190))
	out["logo:geom"] = str([Backend.logo_scale(int(img[0]), int(img[1])), base,
		Backend.content_center(1280, 720),
		Backend.logo_center_y(360.0, true), Backend.logo_center_y(360.0, false),
		Backend.logo_offsets(),
		Backend.logo_glow_rect(640.0, 334.0, 190)])

	# Glow judul + aksen + hint.
	var tsec: Dictionary = _fx.get("title_glow")
	var text_rect := _rect4(tsec.get("text_rect"))
	var surf_acc: Array = []
	for s_v in tsec.get("surfaces"):
		var want: Dictionary = s_v
		surf_acc.append(Backend.title_glow_surface(text_rect,
			int(want.get("layer")), int(want.get("spread"))))
	out["glow:surfaces"] = str(surf_acc)
	out["glow:layers"] = str([Backend.title_glow_layers(true),
		Backend.title_glow_layers(false)])
	var fill_acc: Array = []
	for f_v in tsec.get("fills"):
		var row: Array = f_v
		fill_acc.append(Backend.title_glow_fill(float(row[0])))
	out["glow:fills"] = str(fill_acc)
	var accent_acc: Array = []
	for a_v in tsec.get("accent"):
		var row: Dictionary = a_v
		accent_acc.append([Backend.accent_gap(int(text_rect.size.x)),
			Backend.accent_lines(float(row.get("alpha")))])
	out["glow:accent"] = str(accent_acc)
	var hint_acc: Array = []
	for h_v in (_sec("hint").get("rows") as Array):
		var row: Dictionary = h_v
		hint_acc.append([Backend.hint_alpha(float(row.get("overall"))),
			Backend.hint_pos(1280, 720)])
	out["hint"] = str([Backend.hint_text(), hint_acc])
	return out


## Rantai partikel: dipakai A/B, jadi ditulis sekali di sini (base punya
## versinya sendiri dengan assertion per langkah).
func _replay(initial: Array, frames: int, respawn: Array, dt: float) -> Array:
	var states: Array = []
	for p_v in initial:
		var p: Dictionary = p_v
		states.append({"x": float(p["x"]), "y": float(p["y"]),
			"r": float(p["r"]), "speed": float(p["speed"]),
			"drift": float(p["drift"]), "phase": float(p["phase"]),
			"color": p["color"]})
	var elapsed := 0.0
	var ri := 0
	for _frame in frames:
		elapsed += dt
		for i in states.size():
			var st: Dictionary = states[i]
			var rx := 0.0
			if ri < respawn.size():
				rx = float((respawn[ri] as Array)[2])
			var res: Dictionary = Backend.particle_advance(float(st["x"]),
				float(st["y"]), float(st["speed"]), float(st["drift"]),
				float(st["phase"]), elapsed, 720.0, rx)
			if bool(res.get("wrapped")):
				ri += 1
			st["x"] = float(res.get("x"))
			st["y"] = float(res.get("y"))
	return states


func _triplets(states: Array, elapsed: float) -> Array:
	var out: Array = []
	for st_v in states:
		var st: Dictionary = st_v
		var tw := Backend.particle_twinkle(elapsed, float(st["phase"]))
		out.append([
			Backend.particle_draw_pos(float(st["x"]), float(st["y"])),
			Backend.particle_draw_radius(float(st["r"])),
			Backend.particle_draw_color(_col(st["color"]), tw), tw])
	return out


func _fail_gdext(tag: String, message: String) -> void:
	# Lewat _fail() base supaya ikut terhitung di _failures (exit code 1) dan
	# tercetak dengan pola "[...Test] ..." yang dibaca godot_log_gate.
	# PENTING: _fail() base hanya menerima SATU argumen (message) — tag
	# dirangkai di sini. Salah jumlah argumen = Parse Error saat scene dimuat
	# (GDScript memeriksa arity lintas berkas, gdparse tidak), jadi bentuk ini
	# dikunci tools/test_godot_splash_parity.py.
	_fail("gdext/%s: %s" % [tag, message])


func _abort() -> void:
	_done = true
	for msg in _errors:
		print(msg)
	print("[SplashGdextParityTest] FAIL: jalur C++ tidak bisa diuji")
	Backend.reset_backend()
	get_tree().quit(1)


func _finish() -> void:
	if _done:
		return
	var failed := int(_failures)
	var checks := int(_checks)
	super._finish()
	Backend.reset_backend()
	if failed == 0:
		print("[SplashGdextParityTest] PASS: splash_screen.py ↔ MysticSplash "
			+ "(C++) — timeline 4x200 frame, rantai 46 partikel x 120 langkah, "
			+ "48 batang + 70 vignette + 9 piksel latar, logo, glow judul, "
			+ "hint, draw_order, %d check" % checks)
		print("[SplashGdextParityTest] PASS")
	else:
		print("[SplashGdextParityTest] FAIL: %d kegagalan di backend gdext"
			% failed)
