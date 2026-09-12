# SplashModel.gd — backend GDScript lapisan MODEL splash (port
# splash_screen.py 1:1, kembaran C++ MysticSplash di
# godot/gdext/mystic_splash/src/splash_processor.cpp).
#
# Bagian dari migrasi splash_screen.py -> godot++ (FASE 38). Jalur default
# produksi: berkas ini lewat SplashBackend.gd. Kalau lib C++ dibuild dan
# mystic/splash/use_gdext_splash=true, SplashBackend meneruskan setiap
# panggilan ke MysticSplash; A/B keduanya dikunci
# tests/SplashGdextParityTest.gd + tools/test_splash_cpp_selftest.py.
#
# KONVENSI ANGKA (sama dengan C++, dikunci oracle pygame
# tools/test_godot_splash_parity.py):
#   * int()/int GDScript = trunc ke arah nol (paritas int() Python);
#   * int/int GDScript = pembagian integer trunc (paritas // Python untuk
#     nilai non-negatif — semua input di sini non-negatif setelah clamp);
#   * round_half_even = round() CPython (kuantisasi tumbuh logo);
#   * metrik font TIDAK ada di sini: lebar/tinggi teks datang sebagai
#     parameter (pola FASE 36).
extends RefCounted
class_name SplashModel

const GAME_NAME := "MYSTIC ARENA"
const TAGLINE := "A MOBA TOWER DEFENSE ADVENTURE"
const HINT_TEXT := "Tap anywhere to skip"

const SPLASH_DURATION := 3.0
const FADE_IN := 0.4
const FADE_OUT := 0.45
const SKIP_FADE := 0.25
const SKIP_DONE := 0.25
const TITLE_DELAY := 0.5
const TITLE_RAMP := 0.6
const TITLE_MAX := 255
const GROW_TIME := 0.9
const GROW_MIN := 0.85
const GROW_SPAN := 0.15
const GROW_QUANT := 20
const ALPHA_EPSILON := 0.001

const MOVE_RATE := 0.8
const MOVE_AMP := 0.05
const WRAP_BELOW := -6
const WRAP_MARGIN := 6
const TWINKLE_RATE := 2.5
const DIM_FLOOR := 0.35
const DIM_SPAN := 0.65
const PARTICLE_MIN_R := 1
const PARTICLE_COUNT := 46

const BAND_TARGET := 48
const GRAD_SPLIT := 0.55
const VIG_START := 140
const VIG_STEP := -2
const VIG_SLOPE := 2.2

const LOGO_LIFT := 26
const LOGO_MAX_W := 340
const LOGO_MAX_H := 320
const GLOW_PAD := 30
const GLOW_STEP := -3
const GLOW_ALPHA := 12
const TITLE_BELOW := 46
const SUB_BELOW := 88
const SUB_TEXT_ONLY := 66

const GLOW_FILL := 0.28
const GLOW_GROW := 2
const GLOW_OFFSET := 1
const ACCENT_PAD := 18
const ACCENT_FAC := 0.85
const ACCENT_LEN := 46
const ACCENT_WIDTH := 2

const HINT_MARGIN := 48
const HINT_ALPHA := 140

const ACCENT := Color("#ffbe3c")
const ACCENT_2 := Color("#c88cff")
const TEXT_MAIN := Color("#f5f0e6")
const TEXT_DIM := Color("#a09baa")
const GRAD_TOP := Color("#080812")
const GRAD_MID := Color("#161026")
const GRAD_BOT := Color("#06060e")

const API_SIGNATURE := "splash_v1:1mod:62fn:"


# ── helper paritas Python ────────────────────────────────────────────────

## round() CPython: half-to-even.
static func round_half_even(value: float) -> int:
	var floored := floorf(value)
	var diff := value - floored
	if diff > 0.5:
		return int(floored) + 1
	if diff < 0.5:
		return int(floored)
	var parity := int(floored)
	return parity if parity % 2 == 0 else parity + 1


## int() CPython: trunc ke arah nol (int GDScript sudah begitu).
static func py_int(value: float) -> int:
	return int(value)


static func _c8(rgb: Color) -> Color:
	return Color(rgb.r8 / 255.0, rgb.g8 / 255.0, rgb.b8 / 255.0)


# ── meta ─────────────────────────────────────────────────────────────────

static func module_names() -> Array:
	return ["splash_screen"]


static func module_names_string() -> String:
	return "splash_screen"


static func api_signature() -> String:
	return API_SIGNATURE


static func game_name() -> String:
	return GAME_NAME


static func tagline() -> String:
	return TAGLINE


static func hint_text() -> String:
	return HINT_TEXT


static func splash_duration() -> float:
	return SPLASH_DURATION


static func logo_paths() -> Array:
	return ["assets/logo.png", "assets/splash_logo.png", "assets/logo.jpg",
		"assets/logo.jpeg"]


# ── warna & font ─────────────────────────────────────────────────────────

static func accent() -> Color:
	return ACCENT


static func accent_2() -> Color:
	return ACCENT_2


static func text_main() -> Color:
	return TEXT_MAIN


static func text_dim() -> Color:
	return TEXT_DIM


static func gradient_stops() -> Dictionary:
	return {"top": GRAD_TOP, "mid": GRAD_MID, "bot": GRAD_BOT}


static func particle_colors() -> Array:
	return [Color("#ffd278"), Color("#e6a0ff"), Color("#fff5e6"),
		Color("#b4c8ff")]


static func font_sizes() -> Dictionary:
	return {"presents": 34, "title": 92, "title_below": 66, "sub": 22,
		"hint": 16}


static func font_fallback_sizes() -> Dictionary:
	return {"presents": 40, "title": 110, "title_below": 80, "sub": 26,
		"hint": 18}


static func font_styles() -> Dictionary:
	return {"presents": "body_bold", "title": "title",
		"title_below": "title", "sub": "body_semibold",
		"hint": "body_medium"}


# ── partikel ─────────────────────────────────────────────────────────────

static func particle_count() -> int:
	return PARTICLE_COUNT


static func particle_ranges() -> Dictionary:
	return {"r_lo": 0.6, "r_hi": 2.4, "speed_lo": 0.08, "speed_hi": 0.35,
		"drift_lo": -0.12, "drift_hi": 0.12, "phase_lo": 0.0,
		"phase_hi": TAU}


static func particle_move(x: float, y: float, speed: float, drift: float,
		phase: float, elapsed: float) -> Dictionary:
	return {"y": y - speed,
		"x": x + drift + sin(elapsed * MOVE_RATE + phase) * MOVE_AMP}


static func particle_wrapped(y: float) -> bool:
	return y < float(WRAP_BELOW)


static func particle_wrap_y(screen_h: float) -> float:
	return screen_h + float(WRAP_MARGIN)


static func particle_advance(x: float, y: float, speed: float, drift: float,
		phase: float, elapsed: float, screen_h: float,
		respawn_x: float) -> Dictionary:
	var moved := particle_move(x, y, speed, drift, phase, elapsed)
	var nx: float = moved["x"]
	var ny: float = moved["y"]
	var wrapped := particle_wrapped(ny)
	if wrapped:
		ny = particle_wrap_y(screen_h)
		nx = respawn_x
	return {"x": nx, "y": ny, "wrapped": wrapped}


static func particle_twinkle(elapsed: float, phase: float) -> float:
	return 0.5 + 0.5 * sin(elapsed * TWINKLE_RATE + phase)


static func particle_channel(channel: int, twinkle: float) -> int:
	return py_int(float(channel) * (DIM_FLOOR + DIM_SPAN * twinkle))


static func particle_draw_color(base: Color, twinkle: float) -> Color:
	var f := DIM_FLOOR + DIM_SPAN * twinkle
	return Color(py_int(float(base.r8) * f) / 255.0,
		py_int(float(base.g8) * f) / 255.0,
		py_int(float(base.b8) * f) / 255.0)


static func particle_draw_radius(r: float) -> int:
	return maxi(PARTICLE_MIN_R, py_int(r))


static func particle_draw_pos(x: float, y: float) -> Vector2:
	return Vector2(py_int(x), py_int(y))


# ── timing & state ───────────────────────────────────────────────────────

static func fade_in(t: float) -> float:
	return minf(1.0, t / FADE_IN)


static func fade_out_normal(t: float) -> float:
	return clampf((SPLASH_DURATION - t) / FADE_OUT, 0.0, 1.0)


static func fade_out_skip(t: float) -> float:
	return maxf(0.0, 1.0 - t / SKIP_FADE)


## Semantik PYGAME: cabang skip memakai elapsed TOTAL.
static func overall_alpha(t: float, skipped: bool) -> float:
	var out := fade_in(t)
	if skipped:
		out *= fade_out_skip(t)
	else:
		out *= fade_out_normal(t)
	return clampf(out, 0.0, 1.0)


## Semantik port Godot pra-FASE 38 (skip_t sejak skip) — pembanding A/B.
static func overall_alpha_godot(t: float, skipped: bool,
		skip_t: float) -> float:
	var out := fade_in(t)
	if skipped:
		out *= fade_out_skip(skip_t)
	else:
		out *= fade_out_normal(t)
	return clampf(out, 0.0, 1.0)


static func title_alpha(t: float) -> int:
	if t < TITLE_DELAY:
		return 0
	return py_int(float(TITLE_MAX) * minf(1.0, (t - TITLE_DELAY) / TITLE_RAMP))


static func title_alpha_drawn(title_alpha_value: int, overall: float) -> int:
	return py_int(float(title_alpha_value) * overall)


static func is_done(t: float, skipped: bool) -> bool:
	if skipped:
		return t >= SKIP_DONE
	return t >= SPLASH_DURATION


static func is_done_godot(t: float, skipped: bool, skip_t: float) -> bool:
	if skipped:
		return skip_t >= SKIP_DONE
	return t >= SPLASH_DURATION


static func draw_visible(alpha: float) -> bool:
	return alpha > ALPHA_EPSILON


static func timings() -> Dictionary:
	return {"duration": SPLASH_DURATION, "fade_in": FADE_IN,
		"fade_out": FADE_OUT, "skip_fade": SKIP_FADE,
		"skip_done": SKIP_DONE, "title_delay": TITLE_DELAY,
		"title_ramp": TITLE_RAMP, "title_max": TITLE_MAX,
		"grow_time": GROW_TIME, "alpha_epsilon": ALPHA_EPSILON}


# ── latar ────────────────────────────────────────────────────────────────

static func bg_step_h(screen_h: int) -> int:
	return maxi(1, screen_h / BAND_TARGET)


static func bg_band_count(screen_h: int) -> int:
	var step := bg_step_h(screen_h)
	return (screen_h + step - 1) / step


static func bg_band_rect(i: int, step_h: int, screen_w: int) -> Rect2:
	return Rect2(0, i, screen_w, step_h)


static func _band_channel(from: int, to: int, f2: float) -> int:
	return py_int(float(from) + (float(to) - float(from)) * f2)


static func bg_band_color(i: int, screen_h: int) -> Color:
	var f := float(i) / float(screen_h)
	var from: Color
	var to: Color
	var f2: float
	if f < GRAD_SPLIT:
		f2 = f / GRAD_SPLIT
		from = GRAD_TOP
		to = GRAD_MID
	else:
		f2 = (f - GRAD_SPLIT) / (1.0 - GRAD_SPLIT)
		from = GRAD_MID
		to = GRAD_BOT
	return Color(_band_channel(from.r8, to.r8, f2) / 255.0,
		_band_channel(from.g8, to.g8, f2) / 255.0,
		_band_channel(from.b8, to.b8, f2) / 255.0)


static func bg_bands(screen_w: int, screen_h: int) -> Array:
	var out: Array = []
	var step := bg_step_h(screen_h)
	var i := 0
	while i < screen_h:
		out.append({"rect": bg_band_rect(i, step, screen_w),
			"color": bg_band_color(i, screen_h)})
		i += step
	return out


static func vignette_frames(screen_w: int, screen_h: int) -> Array:
	var out: Array = []
	var i := VIG_START
	while i > 0:
		var alpha := mini(255, py_int(VIG_SLOPE * float(VIG_START - i)))
		out.append({"rect": Rect2(i, i, screen_w - 2 * i, screen_h - 2 * i),
			"alpha": alpha})
		i += VIG_STEP
	return out


# ── konten & logo ────────────────────────────────────────────────────────

static func content_center(screen_w: int, screen_h: int) -> Vector2:
	return Vector2(screen_w / 2, screen_h / 2)


static func logo_center_y(base_y: float, has_logo: bool) -> float:
	return base_y - float(LOGO_LIFT) if has_logo else base_y


static func logo_scale(img_w: int, img_h: int) -> float:
	return minf(minf(float(LOGO_MAX_W) / float(img_w),
		float(LOGO_MAX_H) / float(img_h)), 1.0)


static func logo_base_size(img_w: int, img_h: int) -> Vector2:
	var s := logo_scale(img_w, img_h)
	return Vector2(maxi(1, py_int(float(img_w) * s)),
		maxi(1, py_int(float(img_h) * s)))


static func logo_grow_quant(elapsed: float) -> float:
	var grow := minf(1.0, elapsed / GROW_TIME)
	return float(round_half_even((GROW_MIN + GROW_SPAN * grow)
		* float(GROW_QUANT))) / float(GROW_QUANT)


static func logo_grow_size(base: Vector2, gq: float) -> Vector2:
	return Vector2(maxi(1, py_int(base.x * gq)), maxi(1, py_int(base.y * gq)))


static func logo_glow_radius(ww: int, hh: int) -> int:
	return maxi(ww, hh) / 2 + GLOW_PAD


static func logo_glow_rect(cx: float, cy: float, glow_r: int) -> Rect2:
	return Rect2(cx - float(glow_r), cy - float(glow_r), glow_r * 2,
		glow_r * 2)


static func logo_glow_rings(glow_r: int) -> Array:
	var out: Array = []
	var g := glow_r
	while g > 0:
		out.append({"r": g,
			"alpha": py_int(float(GLOW_ALPHA)
				* (1.0 - float(g) / float(glow_r)))})
		g += GLOW_STEP
	return out


static func logo_offsets() -> Dictionary:
	return {"logo_lift": LOGO_LIFT, "title_below": TITLE_BELOW,
		"sub_below": SUB_BELOW, "sub_text_only": SUB_TEXT_ONLY}


# ── glow judul + aksen ───────────────────────────────────────────────────

static func title_glow_layers(cheap: bool) -> Array:
	if not cheap:
		return []
	return [{"layer": 24, "spread": 1}, {"layer": 14, "spread": 2},
		{"layer": 8, "spread": 3}]


static func title_glow_surface(text_rect: Rect2, layer: int,
		spread: int) -> Rect2:
	return Rect2(text_rect.position.x - layer - GLOW_OFFSET,
		text_rect.position.y - layer - GLOW_OFFSET,
		text_rect.size.x + layer * 2 + spread * GLOW_GROW,
		text_rect.size.y + layer * 2 + spread * GLOW_GROW)


static func title_glow_fill(alpha: float) -> int:
	return py_int(alpha * GLOW_FILL)


static func accent_gap(text_w: int) -> int:
	return text_w / 2 + ACCENT_PAD


static func accent_lines(alpha: float) -> Array:
	var out: Array = []
	var fac := (alpha / 255.0) * ACCENT_FAC
	for spec in [[-6, ACCENT], [6, ACCENT_2]]:
		var col: Color = spec[1]
		out.append({"off": spec[0],
			"color": Color(py_int(float(col.r8) * fac) / 255.0,
				py_int(float(col.g8) * fac) / 255.0,
				py_int(float(col.b8) * fac) / 255.0),
			"width": ACCENT_WIDTH, "len": ACCENT_LEN})
	return out


# ── hint ─────────────────────────────────────────────────────────────────

static func hint_pos(screen_w: int, screen_h: int) -> Vector2:
	return Vector2(screen_w / 2, screen_h - HINT_MARGIN)


static func hint_alpha(overall: float) -> int:
	return py_int(float(HINT_ALPHA) * overall)
