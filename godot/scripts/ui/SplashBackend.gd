# SplashBackend.gd — pilih implementasi lapisan MODEL splash: GDExt
# (MysticSplash, godot++ C++) atau GDScript (SplashModel.gd).
#
# Bagian dari migrasi splash_screen.py -> godot++ (FASE 38):
#   python side   splash_screen.py                          (sumber kebenaran)
#   GDScript side godot/scripts/ui/SplashModel.gd           (fallback default)
#   C++ side      godot/gdext/mystic_splash/src/*           (tools/gen_splash_cpp.py)
# C++ dibangkitkan dari AST splash_screen.py, jadi angka kedua backend datang
# dari satu sumber; loader ini murni saklar — SplashScreen.gd tidak tahu
# backend mana yang jalan (pola MapDBLoader.gd/LevelDBLoader.gd).
#
# Kapan pakai C++: mystic/splash/use_gdext_splash=true DI project.godot DAN
# lib hasil scons ada di addons/mystic_splash/bin/. Kalau lib belum dibuild,
# fallback ke GDScript — tidak ada error, tidak ada perubahan perilaku.
#
# PENTING: tidak boleh menyebut `MysticSplash` sebagai IDENTIFIER di sini. Di
# CI headless lib .so tidak ikut repo, jadi referensi langsung ke class GDExt
# akan Parse Error dan mematikan seluruh project. Semua akses lewat
# ClassDB.class_exists/instantiate dengan string.

extends RefCounted
class_name SplashBackend

const ModelGD = preload("res://scripts/ui/SplashModel.gd")

## Nama class yang didaftarkan register_types.cpp (GDCLASS MysticSplash).
const GDEXT_CLASS := "MysticSplash"
## Setting project yang menyalakan jalur C++.
const SETTING := "mystic/splash/use_gdext_splash"

static var _use_gdext: bool = false
static var _checked: bool = false
## "" = ikut ProjectSettings; "gdext"/"gdscript" = paksa (harness paritas).
static var _forced: String = ""
## Instance GDExt di-cache: semua method MysticSplash static, tapi Godot butuh
## sebuah Object untuk callv() (pola HeroSkillKitLoader/MapDBLoader).
static var _inst: Object = null
## Backend terakhir yang DIUMUMKAN ke log (harness A/B memanggil force_backend
## ratusan kali; satu baris log per panggilan menenggelamkan error sungguhan).
static var _announced: String = "__belum__"


## True kalau lib C++ termuat engine (terlepas dari setting/force).
static func gdext_available() -> bool:
	return ClassDB.class_exists(GDEXT_CLASS)


static func _resolve() -> void:
	_checked = true
	_use_gdext = false
	_inst = null
	var want := _forced
	if want == "":
		var flag := false
		if ProjectSettings.has_setting(SETTING):
			flag = bool(ProjectSettings.get_setting(SETTING))
		want = "gdext" if flag else "gdscript"
	if want == "gdext":
		if not ClassDB.class_exists(GDEXT_CLASS):
			if _forced == "":
				_announce("gdext-hilang", "[SplashBackend] flag "
					+ "use_gdext_splash=true tapi GDExt tidak ditemukan, "
					+ "fallback GDScript")
		else:
			var inst = ClassDB.instantiate(GDEXT_CLASS)
			if inst == null:
				_announce("gdext-gagal", "[SplashBackend] GAGAL instantiate "
					+ "%s, fallback GDScript" % GDEXT_CLASS)
			else:
				_inst = inst
				_use_gdext = true
				# Baris ini di-require CI (godot-gdext.yml): bukti jalur C++
				# benar-benar dipakai, bukan fallback diam-diam. Frasa
				# "GDExtension MysticSplash aktif" harus SATU literal utuh
				# (dicek statis tools/test_godot_splash_parity.py).
				var signature := str(_call_gdext("api_signature", []))
				_announce("gdext", "[SplashBackend] GDExtension MysticSplash "
					+ "aktif (godot++ C++) — model " + signature)
	if not _use_gdext:
		_announce("gdscript", "[SplashBackend] backend GDScript "
			+ "(SplashModel.gd)")


## Cetak sekali per PERUBAHAN backend.
static func _announce(key: String, message: String) -> void:
	if _announced == key:
		return
	_announced = key
	print(message)


static func _ensure_checked() -> void:
	if not _checked:
		_resolve()


## Paksa backend — dipakai harness paritas supaya jalur C++ bisa diuji tanpa
## mengubah project.godot (default false demi CI tanpa compiler).
static func force_backend(backend: String) -> void:
	_forced = backend
	_checked = false
	_inst = null
	_resolve()


static func reset_backend() -> void:
	force_backend("")


## "gdext" kalau jalur C++ aktif, selain itu "gdscript".
static func backend_name() -> String:
	_ensure_checked()
	return "gdext" if _use_gdext else "gdscript"


static func is_using_gdext() -> bool:
	_ensure_checked()
	return _use_gdext


## Panggil method static MysticSplash lewat instance cache. Null kalau backend
## GDScript aktif / method tidak ada — pemakai jatuh ke SplashModel.
static func _call_gdext(method: String, args: Array):
	_ensure_checked()
	if _inst == null:
		return null
	if not _inst.has_method(method):
		push_error("[SplashBackend] %s tidak punya method %s — regenerasi "
			% [GDEXT_CLASS, method]
			+ "tools/gen_splash_cpp.py lalu build ulang lib")
		return null
	return _inst.callv(method, args)


static func _gdext_ready(method: String) -> bool:
	_ensure_checked()
	if not _use_gdext or _inst == null:
		return false
	if not _inst.has_method(method):
		push_error("[SplashBackend] %s tidak punya method %s — regenerasi "
			% [GDEXT_CLASS, method]
			+ "tools/gen_splash_cpp.py lalu build ulang lib")
		return false
	return true


# ══════════════════════════════════════════════════════════
#  API model splash (62 fungsi — urutan = splash_processor.h)
# ══════════════════════════════════════════════════════════


static func module_names() -> Array:
	if _gdext_ready("module_names"):
		var got = _call_gdext("module_names", [])
		if got is Array:
			return got
	return ModelGD.module_names()

static func module_names_string() -> String:
	if _gdext_ready("module_names_string"):
		return str(_call_gdext("module_names_string", []))
	return ModelGD.module_names_string()

static func api_signature() -> String:
	if _gdext_ready("api_signature"):
		return str(_call_gdext("api_signature", []))
	return ModelGD.api_signature()

static func game_name() -> String:
	if _gdext_ready("game_name"):
		return str(_call_gdext("game_name", []))
	return ModelGD.game_name()

static func tagline() -> String:
	if _gdext_ready("tagline"):
		return str(_call_gdext("tagline", []))
	return ModelGD.tagline()

static func hint_text() -> String:
	if _gdext_ready("hint_text"):
		return str(_call_gdext("hint_text", []))
	return ModelGD.hint_text()

static func splash_duration() -> float:
	if _gdext_ready("splash_duration"):
		return float(_call_gdext("splash_duration", []))
	return ModelGD.splash_duration()

static func logo_paths() -> Array:
	if _gdext_ready("logo_paths"):
		var got = _call_gdext("logo_paths", [])
		if got is Array:
			return got
	return ModelGD.logo_paths()

static func accent() -> Color:
	if _gdext_ready("accent"):
		var got = _call_gdext("accent", [])
		if got is Color:
			return got
	return ModelGD.accent()

static func accent_2() -> Color:
	if _gdext_ready("accent_2"):
		var got = _call_gdext("accent_2", [])
		if got is Color:
			return got
	return ModelGD.accent_2()

static func text_main() -> Color:
	if _gdext_ready("text_main"):
		var got = _call_gdext("text_main", [])
		if got is Color:
			return got
	return ModelGD.text_main()

static func text_dim() -> Color:
	if _gdext_ready("text_dim"):
		var got = _call_gdext("text_dim", [])
		if got is Color:
			return got
	return ModelGD.text_dim()

static func gradient_stops() -> Dictionary:
	if _gdext_ready("gradient_stops"):
		var got = _call_gdext("gradient_stops", [])
		if got is Dictionary:
			return got
	return ModelGD.gradient_stops()

static func particle_colors() -> Array:
	if _gdext_ready("particle_colors"):
		var got = _call_gdext("particle_colors", [])
		if got is Array:
			return got
	return ModelGD.particle_colors()

static func font_sizes() -> Dictionary:
	if _gdext_ready("font_sizes"):
		var got = _call_gdext("font_sizes", [])
		if got is Dictionary:
			return got
	return ModelGD.font_sizes()

static func font_fallback_sizes() -> Dictionary:
	if _gdext_ready("font_fallback_sizes"):
		var got = _call_gdext("font_fallback_sizes", [])
		if got is Dictionary:
			return got
	return ModelGD.font_fallback_sizes()

static func font_styles() -> Dictionary:
	if _gdext_ready("font_styles"):
		var got = _call_gdext("font_styles", [])
		if got is Dictionary:
			return got
	return ModelGD.font_styles()

static func particle_count() -> int:
	if _gdext_ready("particle_count"):
		return int(_call_gdext("particle_count", []))
	return ModelGD.particle_count()

static func particle_ranges() -> Dictionary:
	if _gdext_ready("particle_ranges"):
		var got = _call_gdext("particle_ranges", [])
		if got is Dictionary:
			return got
	return ModelGD.particle_ranges()

static func particle_move(x: float, y: float, speed: float, drift: float, phase: float, elapsed: float) -> Dictionary:
	if _gdext_ready("particle_move"):
		var got = _call_gdext("particle_move", [x, y, speed, drift, phase, elapsed])
		if got is Dictionary:
			return got
	return ModelGD.particle_move(x, y, speed, drift, phase, elapsed)

static func particle_wrapped(y: float) -> bool:
	if _gdext_ready("particle_wrapped"):
		return bool(_call_gdext("particle_wrapped", [y]))
	return ModelGD.particle_wrapped(y)

static func particle_wrap_y(screen_h: float) -> float:
	if _gdext_ready("particle_wrap_y"):
		return float(_call_gdext("particle_wrap_y", [screen_h]))
	return ModelGD.particle_wrap_y(screen_h)

static func particle_advance(x: float, y: float, speed: float, drift: float, phase: float, elapsed: float, screen_h: float, respawn_x: float) -> Dictionary:
	if _gdext_ready("particle_advance"):
		var got = _call_gdext("particle_advance", [x, y, speed, drift, phase, elapsed, screen_h, respawn_x])
		if got is Dictionary:
			return got
	return ModelGD.particle_advance(x, y, speed, drift, phase, elapsed, screen_h, respawn_x)

static func particle_twinkle(elapsed: float, phase: float) -> float:
	if _gdext_ready("particle_twinkle"):
		return float(_call_gdext("particle_twinkle", [elapsed, phase]))
	return ModelGD.particle_twinkle(elapsed, phase)

static func particle_channel(channel: int, twinkle: float) -> int:
	if _gdext_ready("particle_channel"):
		return int(_call_gdext("particle_channel", [channel, twinkle]))
	return ModelGD.particle_channel(channel, twinkle)

static func particle_draw_color(base: Color, twinkle: float) -> Color:
	if _gdext_ready("particle_draw_color"):
		var got = _call_gdext("particle_draw_color", [base, twinkle])
		if got is Color:
			return got
	return ModelGD.particle_draw_color(base, twinkle)

static func particle_draw_radius(r: float) -> int:
	if _gdext_ready("particle_draw_radius"):
		return int(_call_gdext("particle_draw_radius", [r]))
	return ModelGD.particle_draw_radius(r)

static func particle_draw_pos(x: float, y: float) -> Vector2:
	if _gdext_ready("particle_draw_pos"):
		var got = _call_gdext("particle_draw_pos", [x, y])
		if got is Vector2:
			return got
	return ModelGD.particle_draw_pos(x, y)

static func fade_in(t: float) -> float:
	if _gdext_ready("fade_in"):
		return float(_call_gdext("fade_in", [t]))
	return ModelGD.fade_in(t)

static func fade_out_normal(t: float) -> float:
	if _gdext_ready("fade_out_normal"):
		return float(_call_gdext("fade_out_normal", [t]))
	return ModelGD.fade_out_normal(t)

static func fade_out_skip(t: float) -> float:
	if _gdext_ready("fade_out_skip"):
		return float(_call_gdext("fade_out_skip", [t]))
	return ModelGD.fade_out_skip(t)

static func overall_alpha(t: float, skipped: bool) -> float:
	if _gdext_ready("overall_alpha"):
		return float(_call_gdext("overall_alpha", [t, skipped]))
	return ModelGD.overall_alpha(t, skipped)

static func overall_alpha_godot(t: float, skipped: bool, skip_t: float) -> float:
	if _gdext_ready("overall_alpha_godot"):
		return float(_call_gdext("overall_alpha_godot", [t, skipped, skip_t]))
	return ModelGD.overall_alpha_godot(t, skipped, skip_t)

static func title_alpha(t: float) -> int:
	if _gdext_ready("title_alpha"):
		return int(_call_gdext("title_alpha", [t]))
	return ModelGD.title_alpha(t)

static func title_alpha_drawn(title_alpha_value: int, overall: float) -> int:
	if _gdext_ready("title_alpha_drawn"):
		return int(_call_gdext("title_alpha_drawn", [title_alpha_value, overall]))
	return ModelGD.title_alpha_drawn(title_alpha_value, overall)

static func is_done(t: float, skipped: bool) -> bool:
	if _gdext_ready("is_done"):
		return bool(_call_gdext("is_done", [t, skipped]))
	return ModelGD.is_done(t, skipped)

static func is_done_godot(t: float, skipped: bool, skip_t: float) -> bool:
	if _gdext_ready("is_done_godot"):
		return bool(_call_gdext("is_done_godot", [t, skipped, skip_t]))
	return ModelGD.is_done_godot(t, skipped, skip_t)

static func draw_visible(alpha: float) -> bool:
	if _gdext_ready("draw_visible"):
		return bool(_call_gdext("draw_visible", [alpha]))
	return ModelGD.draw_visible(alpha)

static func timings() -> Dictionary:
	if _gdext_ready("timings"):
		var got = _call_gdext("timings", [])
		if got is Dictionary:
			return got
	return ModelGD.timings()

static func bg_step_h(screen_h: int) -> int:
	if _gdext_ready("bg_step_h"):
		return int(_call_gdext("bg_step_h", [screen_h]))
	return ModelGD.bg_step_h(screen_h)

static func bg_band_count(screen_h: int) -> int:
	if _gdext_ready("bg_band_count"):
		return int(_call_gdext("bg_band_count", [screen_h]))
	return ModelGD.bg_band_count(screen_h)

static func bg_band_rect(i: int, step_h: int, screen_w: int) -> Rect2:
	if _gdext_ready("bg_band_rect"):
		var got = _call_gdext("bg_band_rect", [i, step_h, screen_w])
		if got is Rect2:
			return got
	return ModelGD.bg_band_rect(i, step_h, screen_w)

static func bg_band_color(i: int, screen_h: int) -> Color:
	if _gdext_ready("bg_band_color"):
		var got = _call_gdext("bg_band_color", [i, screen_h])
		if got is Color:
			return got
	return ModelGD.bg_band_color(i, screen_h)

static func bg_bands(screen_w: int, screen_h: int) -> Array:
	if _gdext_ready("bg_bands"):
		var got = _call_gdext("bg_bands", [screen_w, screen_h])
		if got is Array:
			return got
	return ModelGD.bg_bands(screen_w, screen_h)

static func vignette_frames(screen_w: int, screen_h: int) -> Array:
	if _gdext_ready("vignette_frames"):
		var got = _call_gdext("vignette_frames", [screen_w, screen_h])
		if got is Array:
			return got
	return ModelGD.vignette_frames(screen_w, screen_h)

static func content_center(screen_w: int, screen_h: int) -> Vector2:
	if _gdext_ready("content_center"):
		var got = _call_gdext("content_center", [screen_w, screen_h])
		if got is Vector2:
			return got
	return ModelGD.content_center(screen_w, screen_h)

static func logo_center_y(base_y: float, has_logo: bool) -> float:
	if _gdext_ready("logo_center_y"):
		return float(_call_gdext("logo_center_y", [base_y, has_logo]))
	return ModelGD.logo_center_y(base_y, has_logo)

static func logo_scale(img_w: int, img_h: int) -> float:
	if _gdext_ready("logo_scale"):
		return float(_call_gdext("logo_scale", [img_w, img_h]))
	return ModelGD.logo_scale(img_w, img_h)

static func logo_base_size(img_w: int, img_h: int) -> Vector2:
	if _gdext_ready("logo_base_size"):
		var got = _call_gdext("logo_base_size", [img_w, img_h])
		if got is Vector2:
			return got
	return ModelGD.logo_base_size(img_w, img_h)

static func logo_grow_quant(elapsed: float) -> float:
	if _gdext_ready("logo_grow_quant"):
		return float(_call_gdext("logo_grow_quant", [elapsed]))
	return ModelGD.logo_grow_quant(elapsed)

static func logo_grow_size(base: Vector2, gq: float) -> Vector2:
	if _gdext_ready("logo_grow_size"):
		var got = _call_gdext("logo_grow_size", [base, gq])
		if got is Vector2:
			return got
	return ModelGD.logo_grow_size(base, gq)

static func logo_glow_radius(ww: int, hh: int) -> int:
	if _gdext_ready("logo_glow_radius"):
		return int(_call_gdext("logo_glow_radius", [ww, hh]))
	return ModelGD.logo_glow_radius(ww, hh)

static func logo_glow_rect(cx: float, cy: float, glow_r: int) -> Rect2:
	if _gdext_ready("logo_glow_rect"):
		var got = _call_gdext("logo_glow_rect", [cx, cy, glow_r])
		if got is Rect2:
			return got
	return ModelGD.logo_glow_rect(cx, cy, glow_r)

static func logo_glow_rings(glow_r: int) -> Array:
	if _gdext_ready("logo_glow_rings"):
		var got = _call_gdext("logo_glow_rings", [glow_r])
		if got is Array:
			return got
	return ModelGD.logo_glow_rings(glow_r)

static func logo_offsets() -> Dictionary:
	if _gdext_ready("logo_offsets"):
		var got = _call_gdext("logo_offsets", [])
		if got is Dictionary:
			return got
	return ModelGD.logo_offsets()

static func title_glow_layers(cheap: bool) -> Array:
	if _gdext_ready("title_glow_layers"):
		var got = _call_gdext("title_glow_layers", [cheap])
		if got is Array:
			return got
	return ModelGD.title_glow_layers(cheap)

static func title_glow_surface(text_rect: Rect2, layer: int, spread: int) -> Rect2:
	if _gdext_ready("title_glow_surface"):
		var got = _call_gdext("title_glow_surface", [text_rect, layer, spread])
		if got is Rect2:
			return got
	return ModelGD.title_glow_surface(text_rect, layer, spread)

static func title_glow_fill(alpha: float) -> int:
	if _gdext_ready("title_glow_fill"):
		return int(_call_gdext("title_glow_fill", [alpha]))
	return ModelGD.title_glow_fill(alpha)

static func accent_gap(text_w: int) -> int:
	if _gdext_ready("accent_gap"):
		return int(_call_gdext("accent_gap", [text_w]))
	return ModelGD.accent_gap(text_w)

static func accent_lines(alpha: float) -> Array:
	if _gdext_ready("accent_lines"):
		var got = _call_gdext("accent_lines", [alpha])
		if got is Array:
			return got
	return ModelGD.accent_lines(alpha)

static func hint_pos(screen_w: int, screen_h: int) -> Vector2:
	if _gdext_ready("hint_pos"):
		var got = _call_gdext("hint_pos", [screen_w, screen_h])
		if got is Vector2:
			return got
	return ModelGD.hint_pos(screen_w, screen_h)

static func hint_alpha(overall: float) -> int:
	if _gdext_ready("hint_alpha"):
		return int(_call_gdext("hint_alpha", [overall]))
	return ModelGD.hint_alpha(overall)
