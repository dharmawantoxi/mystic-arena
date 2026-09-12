# ================================
# BossOverlay.gd — port lapisan OVERLAY `Boss.draw()` (bosses/base_boss.py:6124-6430)
#
# Pygame menggambar boss dalam urutan tetap (base_boss.py:6124):
#
#   1. ENTRANCE  (kalau entrance_timer > 0) -> cincin membesar + teks
#      `entrance_text` berdenyut di tengah layar, lalu RETURN: badan, aura,
#      HP bar dan papan nama TIDAK digambar sama sekali selama entrance.
#   2. aura ability (`ability_active`)      — lingkaran ISI bergradien
#   3. aura enrage/frenzy (`is_enraged`)    — cincin GARIS width 2
#   4. aura ekstra true boss                — lingkaran ISI bergradien
#   5. bayangan (ellipse hitam alpha 120)
#   6. indikator debuff menara (`_core.py:1037` `_draw_tower_debuff_fx`)
#   7. BADAN (renderer per boss / `_draw_generic_body`)
#   8. HP bar (bg + fill + border)
#   9. papan nama (bg radius 3 + border + teks)
#
# Langkah 1-6 (+ badan generik 7) digambar node Boss sendiri — CanvasItem
# menggambar dirinya SEBELUM anak-anaknya, jadi otomatis DI BAWAH badan;
# langkah 8-9 digambar `BossPlate.gd` (anak Node2D sesudah Visual) supaya DI
# ATAS badan. Keduanya memanggil modul ini: tidak ada geometri kedua.
#
# ── JEBAKAN ALPHA: pygame.draw.circle MENIMPA, tidak mem-blend ──
# Aura ability & aura true boss dibangun dari lingkaran ISI yang digambar
# dari besar ke kecil di atas Surface SRCALPHA: tiap piksel memakai alpha
# lingkaran TERKECIL yang menutupinya, jadi hasilnya PITA (band) alpha rata,
# BUKAN gradien yang makin pekat ke pusat. `CanvasItem.draw_circle()` Godot
# sebaliknya MEM-BLEND, sehingga port naif "N draw_circle bertumpuk" membuat
# pusat aura ~3x lebih pekat (dikunci tools/test_boss_true_aura_parity.py).
# Karena itu kedua aura diekspresikan sebagai op `band` (anulus alpha rata)
# yang tidak saling menimpa: inner < d <= outer, digambar `draw_arc` dengan
# width = outer - inner (atau `draw_circle` bila inner <= 0).
#
# ── KOORDINAT ──
# Op memakai koordinat dunia PERSIS pygame (arena 1280x720 == layar; kamera
# Godot zoom 1 di (640,360) tanpa scroll). Titik (x, y) boss adalah titik
# yang sama dengan yang dipakai strip bake: `heroes.render_boss` mem-blit
# sprite di `(x - ax, y - ay)` (:3344) dan `BakedSprite.gd` menaruh anchor
# yang sama di origin node (:124) — jadi origin node Boss == (x, y) pygame,
# TANPA offset. (Boss._draw lama menggeser aura -0.7*radius karena mengira
# origin Godot di telapak kaki sementara pygame di tengah badan; pengukuran
# strip bake membantah itu: BOSS_LABEL_TOP["gornak"] = 57 == 53 px tinta di
# atas anchor + margin, dan aura pygame memang berpusat di anchor.)
#
# ── FORMAT OP ──
# Semua op Dictionary dengan kunci "k"; warna SELALU array [r,g,b] atau
# [r,g,b,a] 0..255 — sama persis dengan tuple pygame, supaya fixture oracle
# dan kode bisa diaudit bersebelahan. Lihat `exec()` untuk rasterisasinya.
#
# ── METRIK FONT ──
# Lebar/tinggi/ascent teks diukur font Godot (Barlow .ttf yang sama dengan
# pygame) kecuali state membawa kunci "metrics" (disuntik fixture oracle):
# selisih metrik antar engine (SDL_ttf vs HarfBuzz) bukan bug geometri, jadi
# oracle membandingkan geometri dengan metrik pygame. Produksi tidak pernah
# mengisi "metrics".
#
# Dikunci: tools/test_boss_draw_parity.py (oracle pygame ASLI) +
# godot/tests/BossDrawParityTest.tscn (replay).
extends Object

const UiTheme = preload("res://scripts/utils/UiTheme.gd")

## Lebar layar arena pygame (settings.SCREEN_WIDTH = _core.py:88).
const SCREEN_W := 1280
## Batas wrap teks entrance (base_boss.py:6404 `<= 1000`).
const ENTRANCE_WRAP_W := 1000
## Margin clamp papan nama (base_boss.py:6265 `margin = 2`).
const PLATE_MARGIN := 2

# ── Aura true boss (base_boss.py:6351-6375) ──
## rad/detik = 0.1 per frame pygame x 60 fps (base_boss.py:580)
const PULSE_SPEED := 6.0
## jumlah langkah pygame `range(aura_r, aura_r - 15, -2)` -> 8 (pertama alpha 0)
const AURA_RINGS := 8
const AURA_STEP := 2.0
const AURA_MARGIN := 15.0
## alpha = (aura_r - r_off) * 5 * pulse
const AURA_ALPHA_STEP := 5.0

# ── Aura ability (base_boss.py:6139-6159) ──
## `range(aura_r, aura_r - 20, -3)` -> 7 langkah, pertama alpha 0.
const ABILITY_RINGS := 7
const ABILITY_STEP := 3.0
## alpha = (aura_r - ar) * 8 * pulse
const ABILITY_ALPHA_STEP := 8.0
## denyut: sin(anim_time * 0.2) * 0.3 + 0.7 (anim_time = frame)
const ABILITY_PULSE_RATE := 0.2

# ── Aura enrage / frenzy (base_boss.py:6277-6300) ──
## `range(aura_r, max(5, aura_r - 18), -3)`
const ENRAGE_STEP := 3
const ENRAGE_SPAN := 18
const ENRAGE_MIN_R := 5
## alpha = (aura_r - r_off) * 12 * pulse, clamp 200
const ENRAGE_ALPHA_STEP := 12.0
const ENRAGE_ALPHA_MAX := 200
## aura_r = radius + int(14 * pulse)
const ENRAGE_MARGIN := 14.0
## ketebalan garis cincin (pygame width=2)
const ENRAGE_RING_W := 2.0
const ENRAGE_COLOR_TRUE := [255, 50, 40]
const ENRAGE_COLOR_MINI := [255, 140, 30]

# ── Entrance (base_boss.py:6376-6430) ──
const ENTRANCE_TRUE_FRAMES := 180
const ENTRANCE_MINI_FRAMES := 120
const ENTRANCE_DISC_ALPHA := 200
const ENTRANCE_TEXT_ALPHA := 255
const ENTRANCE_SHADOW_ALPHA := 200
const ENTRANCE_SHADOW_OFFSET := 2
## start_y = 84 - (baris - 1) * 18 ; ly = start_y + i * 34
const ENTRANCE_BASE_Y := 84
const ENTRANCE_LINE_COMPACT := 18
const ENTRANCE_LINE_STEP := 34
const ENTRANCE_SIZE_TRUE := 28
const ENTRANCE_SIZE_MINI := 24

# ── HP bar + papan nama (base_boss.py:6225-6276) ──
const BAR_W_TRUE := 70
const BAR_W_MINI := 60
const BAR_H_TRUE := 10
const BAR_H_MINI := 8
const BAR_GAP := 6
const BAR_BG := [40, 0, 0]
const HP_HIGH := [100, 220, 100]
const HP_MID := [240, 220, 60]
const HP_LOW := [240, 60, 60]
const BORDER_ENRAGED := [255, 60, 60]
const BORDER_TRUE := [255, 100, 100]
const BORDER_MINI := [255, 200, 50]
const LABEL_TRUE := [255, 100, 100]
const LABEL_MINI := [255, 220, 100]
const LABEL_ENRAGED := [255, 60, 60]
const PLATE_BG := [0, 0, 0]
const PLATE_RADIUS := 3
## inflate(8, 4): +8 lebar (4 tiap sisi), +4 tinggi (2 tiap sisi)
const PLATE_INFLATE_X := 8
const PLATE_INFLATE_Y := 4
## dasar teks 5 px DI ATAS tepi bar (base_boss.py:6262)
const PLATE_TEXT_GAP := 5
const PLATE_SIZE_TRUE := 20
const PLATE_SIZE_MINI := 18

# ── Bayangan (base_boss.py:6166-6169) ──
const SHADOW_COLOR := [0, 0, 0, 120]
const SHADOW_H := 12
const SHADOW_DY := 5
const SHADOW_TRUE_EXTRA := 10

# ── Indikator debuff menara (_core.py:1037-1085) ──
const DEBUFF_SLOW_RING := [150, 220, 255]
const DEBUFF_BURN_OUTER := [255, 140, 40]
const DEBUFF_BURN_INNER := [255, 220, 90]
const DEBUFF_PIP_BG := [10, 10, 14]
## Urutan pip = urutan pemeriksaan pygame — jangan diubah: posisi tiap pip
## bergantung pada jumlah pip sebelumnya.
const DEBUFF_PIP_ORDER: Array = ["slow", "atk_slow", "skill_down",
	"anti_heal", "burn"]
const DEBUFF_PIP_COLORS := {
	"slow": [150, 220, 255],
	"atk_slow": [90, 160, 255],
	"skill_down": [200, 120, 255],
	"anti_heal": [255, 90, 140],
	"burn": [255, 130, 40],
}
const DEBUFF_PIP_STEP := 5
const DEBUFF_PIP_SIZE := 4
const DEBUFF_PIP_DY := 12

# ── Badan generik (base_boss.py:6301-6350) ──
const GENERIC_BLACK := [0, 0, 0]
const GENERIC_CROWN_TRUE := [255, 100, 100]
const GENERIC_CROWN_MINI := [255, 200, 50]
const GENERIC_CROWN_INNER := [255, 255, 200]
const GENERIC_EYE_TRUE := [100, 200, 255]
const GENERIC_EYE_MINI := [255, 50, 50]
const GENERIC_HURT := [255, 255, 255]
const GENERIC_GLOW_ALPHA := 100
const GENERIC_HL_ADD := 50

## Segmen ellipse (pygame meraster sendiri; selisih raster didokumentasikan).
const ELLIPSE_SEGMENTS := 28


# ═══════════════════════════════════════════════════════════════════
# Utilitas numerik (semantik Python)
# ═══════════════════════════════════════════════════════════════════

## `a // b` Python (floor, bukan trunc) — dipakai `r // 3`, `bar_w // 2`.
static func idiv(a: int, b: int) -> int:
	return int(floor(float(a) / float(b)))


## `max(0, min(255, int(v)))` pygame; int() memotong ke arah nol.
static func a255(v: float) -> int:
	return clampi(int(v), 0, 255)


## `max(0, min(200, int(v)))` (alpha aura enrage).
static func a200(v: float) -> int:
	return clampi(int(v), 0, ENRAGE_ALPHA_MAX)


## Warna state -> array [r,g,b] / [r,g,b,a] (0..255, format tuple pygame).
static func col_arr(state: Dictionary, key: String, fallback: Array) -> Array:
	var v = state.get(key)
	if v is Array and (v as Array).size() >= 3:
		var a: Array = v
		return [int(a[0]), int(a[1]), int(a[2]),
			int(a[3]) if a.size() > 3 else 255]
	if v is Color:
		var c := v as Color
		return [int(c.r8), int(c.g8), int(c.b8), int(c.a8)]
	if v is String and not String(v).is_empty():
		var cs := Color(String(v))
		return [int(cs.r8), int(cs.g8), int(cs.b8), int(cs.a8)]
	return fallback


## Ganti/set alpha: `tuple(c[:3]) + (alpha,)` pygame.
static func with_alpha(c: Array, alpha: int) -> Array:
	return [int(c[0]), int(c[1]), int(c[2]), int(alpha)]


## `tuple(min(255, ch + add) for ch in c[:3]) + (255,)` pygame.
static func lighten(c: Array, add: int = GENERIC_HL_ADD) -> Array:
	return [mini(255, int(c[0]) + add), mini(255, int(c[1]) + add),
		mini(255, int(c[2]) + add), 255]


static func is_true(state: Dictionary) -> bool:
	return str(state.get("boss_class", "mini")) == "true"


# ═══════════════════════════════════════════════════════════════════
# Metrik teks
# ═══════════════════════════════════════════════════════════════════

static func font_for(style: String) -> Font:
	match style:
		"body_bold":
			return UiTheme.body_bold()
		"body_semibold":
			return UiTheme.body_semibold()
		"body_medium":
			return UiTheme.body_medium()
		"title":
			return UiTheme.title_font()
	return UiTheme.body_regular()


## [lebar, tinggi, ascent] untuk `text` pada `size`/`style`.
## State yang membawa "metrics" (fixture oracle) memakai angka pygame.
static func text_metrics(state: Dictionary, text: String, size: int,
		style: String) -> Array:
	var injected: Dictionary = state.get("metrics", {})
	var key := "%s|%d|%s" % [text, size, style]
	if injected.has(key):
		var m: Array = injected[key]
		return [int(m[0]), int(m[1]),
			int(m[2]) if m.size() > 2 else int(m[1])]
	var f := font_for(style)
	if f == null:
		return [0, 0, 0]
	var sz := f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size)
	# Tinggi permukaan teks pygame = ascent + descent font pada ukuran itu
	# (SDL_ttf TTF_FontHeight), BUKAN `Font.get_height()` Godot yang ikut
	# menghitung line gap (terukur di CI: 48 px vs 29 px pygame pada size 24 —
	# kotak papan nama jadi dua kali terlalu tinggi). Lebar tetap dari shaping
	# engine: font-nya berkas yang sama, tapi HarfBuzz dan SDL_ttf bisa selisih
	# ~0,5% (426 vs 428 px) — deviasi terdokumentasi, posisi blit dikunci
	# fixture lewat metrik yang disuntik.
	var asc := int(f.get_ascent(size))
	return [int(sz.x), asc + int(f.get_descent(size)), asc]


static func text_width(state: Dictionary, text: String, size: int,
		style: String) -> int:
	return int(text_metrics(state, text, size, style)[0])


# ═══════════════════════════════════════════════════════════════════
# Pembangun op — satu lapisan per fungsi (urutan = urutan pygame)
# ═══════════════════════════════════════════════════════════════════

## Langkah 1: ENTRANCE (eksklusif — pygame `return` setelahnya).
static func entrance_ops(state: Dictionary) -> Array:
	var ops: Array = []
	var timer := int(state.get("entrance_timer", 0))
	var max_timer := int(state.get("entrance_max",
		ENTRANCE_TRUE_FRAMES if is_true(state) else ENTRANCE_MINI_FRAMES))
	if max_timer <= 0:
		return ops
	var progress := 1.0 - float(timer) / float(max_timer)
	var radius := int(state.get("radius", 30))
	var size := int(float(radius) * progress * 2.0)
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var ecol := col_arr(state, "entrance_color", [140, 100, 220, 255])
	if size > 0:
		ops.append({"k": "disc", "c": [x, y], "r": size,
			"col": with_alpha(ecol, a255(ENTRANCE_DISC_ALPHA * (1.0 - progress)))})
	# Teks hanya di paruh pertama entrance (base_boss.py:6390 `> max // 2`)
	if timer > idiv(max_timer, 2):
		var font_size := ENTRANCE_SIZE_TRUE if is_true(state) else ENTRANCE_SIZE_MINI
		var pulse := sin(float(int(state.get("anim_time", 0))) * ABILITY_PULSE_RATE) * 0.3 + 0.7
		var alpha := a255(float(ENTRANCE_TEXT_ALPHA) * pulse)
		var shadow_alpha := a255(float(ENTRANCE_SHADOW_ALPHA) * pulse)
		var lines := wrap_entrance(state, str(state.get("entrance_text", "")), font_size)
		var start_y := ENTRANCE_BASE_Y - (lines.size() - 1) * ENTRANCE_LINE_COMPACT
		var cx := idiv(int(state.get("screen_w", SCREEN_W)), 2)
		for li in range(lines.size()):
			var ly := start_y + li * ENTRANCE_LINE_STEP
			var line := str(lines[li])
			var m := text_metrics(state, line, font_size, "body_semibold")
			# get_rect(center=(cx, ly)) pygame -> TOPLEFT (cx - w//2,
			# ly - h//2). Op teks SELALU membawa topleft + wh + ascent supaya
			# fixture oracle (yang merekam dest blit) bisa dibandingkan langsung.
			var tx0 := cx - idiv(int(m[0]), 2)
			var ty0 := ly - idiv(int(m[1]), 2)
			var op_base := {"k": "text", "text": line, "size": font_size,
				"style": "body_semibold", "anchor": "topleft",
				"wh": [int(m[0]), int(m[1])], "asc": int(m[2])}
			# Bayangan digambar DULUAN (offset +2,+2), lalu teksnya.
			var sh := op_base.duplicate()
			sh["col"] = with_alpha(GENERIC_BLACK, shadow_alpha)
			sh["pos"] = [tx0 + ENTRANCE_SHADOW_OFFSET,
				ty0 + ENTRANCE_SHADOW_OFFSET]
			ops.append(sh)
			var tx := op_base.duplicate()
			tx["col"] = with_alpha(ecol, alpha)
			tx["pos"] = [tx0, ty0]
			ops.append(tx)
	return ops


## Wrap per kata, maks `ENTRANCE_WRAP_W` px (base_boss.py:6396-6412).
static func wrap_entrance(state: Dictionary, text: String, size: int) -> Array:
	var lines: Array = []
	var cur := ""
	for w in text.split(" ", false):
		var trial := (cur + " " + w).strip_edges()
		if text_width(state, trial, size, "body_semibold") <= ENTRANCE_WRAP_W:
			cur = trial
		else:
			if cur != "":
				lines.append(cur)
			cur = w
	if cur != "":
		lines.append(cur)
	if lines.is_empty():
		lines.append(text)
	return lines


## Langkah 2: aura ability (lingkaran ISI -> pita alpha; lihat kepala berkas).
static func ability_aura_ops(state: Dictionary) -> Array:
	var pulse := sin(float(int(state.get("anim_time", 0))) * ABILITY_PULSE_RATE) * 0.3 + 0.7
	var aura_r := int(float(state.get("ability_range", 0.0)) * pulse)
	# ABILITY_RINGS (7), BUKAN AURA_RINGS (8): pygame menggambar
	# `for r in range(aura_r, aura_r - 18, -3)` -> 6 lingkaran + inti
	# (base_boss.py:6139-6159). Salah konstanta di sini menambah satu pita.
	return filled_aura_bands([int(state.get("x", 0)), int(state.get("y", 0))],
		aura_r, ABILITY_RINGS, ABILITY_STEP, ABILITY_ALPHA_STEP, pulse,
		col_arr(state, "entrance_color", [140, 100, 220, 255]))


## Langkah 3: aura enrage / frenzy — cincin GARIS width 2. Cincin berjarak
## 3 px dengan lebar 2 px, jadi tidak pernah tumpang tindih: aman di-blend.
static func enrage_aura_ops(state: Dictionary) -> Array:
	var ops: Array = []
	var pulse := sin(float(state.get("enrage_pulse", 0.0))) * 0.3 + 0.7
	var radius := int(state.get("radius", 30))
	var aura_r := radius + int(ENRAGE_MARGIN * pulse)
	var col: Array = ENRAGE_COLOR_TRUE if is_true(state) else ENRAGE_COLOR_MINI
	var stop := maxi(ENRAGE_MIN_R, aura_r - ENRAGE_SPAN)
	var c: Array = [int(state.get("x", 0)), int(state.get("y", 0))]
	var r_off := aura_r
	while r_off > stop:
		var alpha := a200(float(aura_r - r_off) * ENRAGE_ALPHA_STEP * pulse)
		if alpha > 0 and r_off > 0:
			ops.append({"k": "ring", "c": c, "r": r_off, "w": ENRAGE_RING_W,
				"col": with_alpha(col, alpha)})
		r_off -= ENRAGE_STEP
	return ops


## Langkah 4: aura ekstra true boss (lingkaran ISI -> pita alpha).
static func true_aura_ops(state: Dictionary) -> Array:
	var pulse := sin(float(state.get("pulse", 0.0))) * 0.3 + 0.7
	var aura_r := int(state.get("radius", 30)) + int(AURA_MARGIN)
	return filled_aura_bands([int(state.get("x", 0)), int(state.get("y", 0))],
		aura_r, AURA_RINGS, AURA_STEP, AURA_ALPHA_STEP, pulse,
		col_arr(state, "color", [140, 100, 220, 255]))


## Lingkaran ISI pygame (draw.circle tanpa width, besar -> kecil, MENIMPA)
## -> pita alpha rata. `rings` = jumlah langkah `range()` pygame; langkah
## pertama (i=0) selalu alpha 0 dan dilewati pygame (`if alpha > 0`).
static func filled_aura_bands(c: Array, aura_r: int, rings: int, step: float,
		alpha_step: float, pulse: float, col: Array) -> Array:
	var ops: Array = []
	if aura_r <= 0:
		return ops
	var radii: Array = []
	var alphas: Array = []
	for i in range(1, rings):
		var r_off := aura_r - int(step * float(i))
		if r_off <= 0:
			continue
		var alpha := a255(float(aura_r - r_off) * alpha_step * pulse)
		if alpha <= 0:
			continue
		radii.append(r_off)
		alphas.append(alpha)
	# Pita: (radius berikutnya, radius ini] memakai alpha lingkaran ini;
	# lingkaran terkecil menutup pusat (inner 0) — persis hasil timpa pygame.
	for i2 in range(radii.size()):
		var outer := int(radii[i2])
		var inner := int(radii[i2 + 1]) if i2 + 1 < radii.size() else 0
		ops.append({"k": "band", "c": c, "ri": inner, "ro": outer,
			"col": with_alpha(col, int(alphas[i2]))})
	return ops


## Langkah 5: bayangan ellipse (base_boss.py:6166-6169).
static func shadow_ops(state: Dictionary) -> Array:
	var radius := int(state.get("radius", 30))
	var w := radius * 2 + (SHADOW_TRUE_EXTRA if is_true(state) else 0)
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	return [{"k": "ellipse", "w": 0,
		"rect": [x - idiv(w, 2), y + radius - SHADOW_DY, w, SHADOW_H],
		"col": SHADOW_COLOR}]


## Langkah 6: indikator debuff menara (port `_core.py:1037-1085`).
static func debuff_ops(state: Dictionary) -> Array:
	var ops: Array = []
	var debuff: Dictionary = state.get("debuff", {})
	var radius := int(state.get("radius", 30))
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	# ── Ring slow di kaki ──
	if bool(debuff.get("slow", false)):
		ops.append({"k": "ellipse", "w": 1,
			"rect": [x - radius - 2, y + radius - 7, (radius + 2) * 2, 10],
			"col": with_alpha(DEBUFF_SLOW_RING, 255)})
	# ── BURN: tiga lidah api flicker (anim_time = frame, bukan detik) ──
	if bool(debuff.get("burn", false)):
		var anim := float(int(state.get("anim_time", 0)))
		var flick := int(1.5 + 1.5 * sin(anim * 0.6))
		var flames := [[-radius + 2, -radius - 2, 2 + flick],
			[radius - 2, -radius - 3, 2], [0, -radius - 6, 3 + flick]]
		for fl in flames:
			var fr := int(fl[2])
			var fc: Array = [x + int(fl[0]), y + int(fl[1])]
			ops.append({"k": "disc", "c": fc, "r": fr,
				"col": with_alpha(DEBUFF_BURN_OUTER, 255)})
			ops.append({"k": "disc", "c": fc, "r": maxi(1, fr - 1),
				"col": with_alpha(DEBUFF_BURN_INNER, 255)})
	# ── Pip ikon debuff (baris kecil di bawah kaki) ──
	var pips: Array = []
	for key in DEBUFF_PIP_ORDER:
		if bool(debuff.get(str(key), false)):
			pips.append(DEBUFF_PIP_COLORS[key])
	if not pips.is_empty():
		var pip_y := y + radius + DEBUFF_PIP_DY
		var total_w := pips.size() * DEBUFF_PIP_STEP - 1
		var px := x - idiv(total_w, 2)
		for c in pips:
			ops.append({"k": "rect", "w": 0, "radius": 0,
				"rect": [px - 1, pip_y - 1, DEBUFF_PIP_STEP, DEBUFF_PIP_STEP],
				"col": with_alpha(DEBUFF_PIP_BG, 255)})
			ops.append({"k": "rect", "w": 0, "radius": 0,
				"rect": [px, pip_y, DEBUFF_PIP_SIZE, DEBUFF_PIP_SIZE],
				"col": with_alpha(c, 255)})
			px += DEBUFF_PIP_STEP
	return ops


## Langkah 7-fallback: badan generik boss tanpa renderer (base_boss.py:6301).
static func generic_body_ops(state: Dictionary) -> Array:
	var ops: Array = []
	var radius := int(state.get("radius", 30))
	var x := int(state.get("x", 0))
	var y := int(state.get("y", 0))
	var true_boss := is_true(state)
	var body := col_arr(state, "color", [140, 100, 220, 255])
	if bool(state.get("hurt_flash", false)):
		body = GENERIC_HURT
	var dark := col_arr(state, "color_dark", body)
	ops.append({"k": "disc", "c": [x + 1, y + 1], "r": radius + 2,
		"col": with_alpha(GENERIC_BLACK, 255)})
	ops.append({"k": "disc", "c": [x, y], "r": radius,
		"col": with_alpha(body, 255)})
	ops.append({"k": "ring", "c": [x, y], "r": radius, "w": 3.0,
		"col": with_alpha(dark, 255)})
	ops.append({"k": "disc",
		"c": [x - idiv(radius, 3), y - idiv(radius, 3)],
		"r": idiv(radius, 2), "col": lighten(body)})
	# Crown
	var crown_count := 7 if true_boss else 5
	var crown: Array = GENERIC_CROWN_TRUE if true_boss else GENERIC_CROWN_MINI
	var spike_h := 8 if true_boss else 6
	for i in range(crown_count):
		var angle := PI + float(i - idiv(crown_count, 2)) * 0.25
		var sx := x + int(cos(angle) * float(radius + 3))
		var sy := y + int(sin(angle) * float(radius + 3))
		ops.append({"k": "poly", "col": with_alpha(crown, 255),
			"pts": [[sx - 2, sy], [sx, sy - spike_h], [sx + 2, sy]]})
		if true_boss:
			ops.append({"k": "poly",
				"col": with_alpha(GENERIC_CROWN_INNER, 255),
				"pts": [[sx - 1, sy], [sx, sy - spike_h + 2], [sx + 1, sy]]})
	# Eyes
	var eye: Array = GENERIC_EYE_TRUE if true_boss else GENERIC_EYE_MINI
	ops.append({"k": "disc", "c": [x - idiv(radius, 3), y - idiv(radius, 4)],
		"r": 4, "col": with_alpha(GENERIC_BLACK, 255)})
	ops.append({"k": "disc", "c": [x + idiv(radius, 3), y - idiv(radius, 4)],
		"r": 4, "col": with_alpha(GENERIC_BLACK, 255)})
	ops.append({"k": "disc", "c": [x - idiv(radius, 3), y - idiv(radius, 4)],
		"r": 2, "col": with_alpha(eye, 255)})
	ops.append({"k": "disc", "c": [x + idiv(radius, 3), y - idiv(radius, 4)],
		"r": 2, "col": with_alpha(eye, 255)})
	# Glow mata (ellipse 20x8 alpha 100 di surface sendiri lalu di-blit)
	ops.append({"k": "ellipse", "w": 0,
		"rect": [x - 10, y - idiv(radius, 4) - 4, 20, 8],
		"col": with_alpha(eye, GENERIC_GLOW_ALPHA)})
	return ops


## Puncak sprite: jangkar HP bar (base_boss.py:6219-6223).
static func head_top(state: Dictionary) -> int:
	var radius := int(state.get("radius", 30))
	if not bool(state.get("has_renderer", true)):
		return radius + 12
	var label_top := int(state.get("label_top", 0))
	if label_top <= 0:
		label_top = radius # paritas BOSS_LABEL_TOP.get(boss_type, r)
	return maxi(label_top, radius)


## Tepi atas HP bar (jangkar papan nama): `y - head_top - 6 - bar_h`.
static func bar_top_y(state: Dictionary) -> int:
	var bar_h := BAR_H_TRUE if is_true(state) else BAR_H_MINI
	return int(state.get("y", 0)) - head_top(state) - BAR_GAP - bar_h


static func bar_width(state: Dictionary) -> int:
	return BAR_W_TRUE if is_true(state) else BAR_W_MINI


static func bar_height(state: Dictionary) -> int:
	return BAR_H_TRUE if is_true(state) else BAR_H_MINI


static func border_color(state: Dictionary) -> Array:
	if bool(state.get("is_enraged", false)):
		return BORDER_ENRAGED
	return BORDER_TRUE if is_true(state) else BORDER_MINI


static func label_color(state: Dictionary) -> Array:
	if bool(state.get("is_enraged", false)):
		return LABEL_ENRAGED
	return LABEL_TRUE if is_true(state) else LABEL_MINI


## Teks papan nama: `TRUE BOSS: Nama [ENRAGED]` / `BOSS: Nama [FRENZY]`.
static func plate_text(state: Dictionary) -> String:
	var prefix := "TRUE BOSS" if is_true(state) else "BOSS"
	var tag := ""
	if bool(state.get("is_enraged", false)):
		tag = " [ENRAGED]" if is_true(state) else " [FRENZY]"
	return "%s: %s%s" % [prefix, str(state.get("name", "Boss")), tag]


static func plate_font_size(state: Dictionary) -> int:
	return PLATE_SIZE_TRUE if is_true(state) else PLATE_SIZE_MINI


## Langkah 8: HP bar (bg -> fill -> border).
static func hp_bar_ops(state: Dictionary) -> Array:
	var bar_w := bar_width(state)
	var bar_h := bar_height(state)
	var x := int(state.get("x", 0))
	var bx := x - idiv(bar_w, 2)
	var by := bar_top_y(state)
	var ops: Array = []
	ops.append({"k": "rect", "w": 0, "radius": 0,
		"rect": [bx, by, bar_w, bar_h], "col": with_alpha(BAR_BG, 255)})
	var max_hp := maxf(1.0, float(state.get("max_hp", 1.0)))
	var ratio := float(state.get("hp", 0.0)) / max_hp
	var fill := int(float(bar_w) * ratio)
	if fill > 0:
		var hpc: Array = HP_LOW
		if ratio > 0.5:
			hpc = HP_HIGH
		elif ratio > 0.25:
			hpc = HP_MID
		ops.append({"k": "rect", "w": 0, "radius": 0,
			"rect": [bx, by, fill, bar_h], "col": with_alpha(hpc, 255)})
	ops.append({"k": "rect", "w": 1, "radius": 0,
		"rect": [bx, by, bar_w, bar_h], "col": with_alpha(border_color(state), 255)})
	return ops


## Langkah 9: papan nama (bg hitam radius 3 + border + teks), di-clamp
## supaya tidak keluar layar (base_boss.py:6246-6276).
static func name_plate_ops(state: Dictionary) -> Array:
	var ops: Array = []
	var by := bar_top_y(state)
	var font_size := plate_font_size(state)
	var text := plate_text(state)
	var m := text_metrics(state, text, font_size, "body_bold")
	var tw := int(m[0])
	var th := int(m[1])
	var x := int(state.get("x", 0))
	# get_rect(midbottom=(x, by - 5)) -> left = x - w//2, top = bottom - h
	var nx := x - idiv(tw, 2)
	var ny := by - PLATE_TEXT_GAP - th
	# inflate(8, 4): tumbuh 4 px tiap sisi horizontal, 2 px tiap sisi vertikal
	var bx := nx - idiv(PLATE_INFLATE_X, 2)
	var byy := ny - idiv(PLATE_INFLATE_Y, 2)
	var bw := tw + PLATE_INFLATE_X
	var bh := th + PLATE_INFLATE_Y
	# Nama panjang dekat tepi layar: geser, jangan sampai terpotong.
	var screen_w := int(state.get("screen_w", SCREEN_W))
	var shift := 0
	if bx < PLATE_MARGIN:
		shift = PLATE_MARGIN - bx
	elif bx + bw > screen_w - PLATE_MARGIN:
		shift = -(bx + bw - (screen_w - PLATE_MARGIN))
	if shift != 0:
		nx += shift
		bx += shift
	ops.append({"k": "rect", "w": 0, "radius": PLATE_RADIUS,
		"rect": [bx, byy, bw, bh], "col": with_alpha(PLATE_BG, 255)})
	ops.append({"k": "rect", "w": 1, "radius": PLATE_RADIUS,
		"rect": [bx, byy, bw, bh],
		"col": with_alpha(border_color(state), 255)})
	ops.append({"k": "text", "text": text, "size": font_size,
		"style": "body_bold", "col": with_alpha(label_color(state), 255),
		"anchor": "topleft", "pos": [nx, ny], "wh": [tw, th],
		"asc": int(m[2])})
	return ops


# ═══════════════════════════════════════════════════════════════════
# Rangkaian op per lapisan
# ═══════════════════════════════════════════════════════════════════

static func is_entrance(state: Dictionary) -> bool:
	return int(state.get("entrance_timer", 0)) > 0


## Lapisan BAWAH badan (digambar node Boss sendiri).
static func underlay_ops(state: Dictionary) -> Array:
	if is_entrance(state):
		return entrance_ops(state)
	var ops: Array = []
	if bool(state.get("ability_active", false)):
		ops.append_array(ability_aura_ops(state))
	if bool(state.get("is_enraged", false)):
		ops.append_array(enrage_aura_ops(state))
	if is_true(state):
		ops.append_array(true_aura_ops(state))
	ops.append_array(shadow_ops(state))
	ops.append_array(debuff_ops(state))
	if not bool(state.get("has_renderer", true)):
		ops.append_array(generic_body_ops(state))
	return ops


## Lapisan ATAS badan (digambar BossPlate). Kosong selama entrance —
## pygame tidak menggambar bar/papan nama sama sekali di jalur itu.
static func over_ops(state: Dictionary) -> Array:
	if is_entrance(state):
		return []
	var ops := hp_bar_ops(state)
	ops.append_array(name_plate_ops(state))
	return ops


# ═══════════════════════════════════════════════════════════════════
# Eksekusi op -> CanvasItem
# ═══════════════════════════════════════════════════════════════════

## Segmen draw_arc ikut radius: lingkaran besar butuh lebih banyak titik
## supaya tetap bundar (pygame meraster lingkaran penuh).
static func arc_segments(r: float) -> int:
	return clampi(int(r * 1.5), 24, 180)


static var _style_cache: Dictionary = {}


static func _style_box(col: Color, radius: int, border_w: int) -> StyleBoxFlat:
	var key := "%d,%d,%d,%d|%d|%d" % [int(col.r8), int(col.g8), int(col.b8),
		int(col.a8), radius, border_w]
	if _style_cache.has(key):
		return _style_cache[key]
	var sb := StyleBoxFlat.new()
	sb.corner_radius_top_left = radius
	sb.corner_radius_top_right = radius
	sb.corner_radius_bottom_left = radius
	sb.corner_radius_bottom_right = radius
	sb.anti_aliasing = false
	if border_w > 0:
		# pygame draw.rect(width=1) menggambar border DI DALAM rect;
		# StyleBoxFlat juga menggambar border di dalam box.
		sb.bg_color = Color(0, 0, 0, 0)
		sb.border_color = col
		sb.border_width_left = border_w
		sb.border_width_right = border_w
		sb.border_width_top = border_w
		sb.border_width_bottom = border_w
	else:
		sb.bg_color = col
	_style_cache[key] = sb
	return sb


static func to_color(arr) -> Color:
	if arr is Color:
		return arr
	var a: Array = arr
	return Color(float(int(a[0])) / 255.0, float(int(a[1])) / 255.0,
		float(int(a[2])) / 255.0,
		float(int(a[3])) / 255.0 if a.size() > 3 else 1.0)


static func _v2(arr) -> Vector2:
	return Vector2(float(arr[0]), float(arr[1]))


static func _rect(arr, origin: Vector2) -> Rect2:
	var a: Array = arr
	return Rect2(Vector2(float(a[0]), float(a[1])) - origin,
		Vector2(float(a[2]), float(a[3])))


## Gambar satu rangkaian op. `origin` = posisi node (op memakai koordinat
## dunia; CanvasItem menggambar dalam koordinat lokal).
static func exec(ci: CanvasItem, ops: Array, origin: Vector2) -> void:
	for o in ops:
		var op: Dictionary = o
		match str(op.get("k", "")):
			"disc":
				ci.draw_circle(_v2(op["c"]) - origin, float(op["r"]),
					to_color(op["col"]))
			"ring":
				var rr := float(op["r"])
				ci.draw_arc(_v2(op["c"]) - origin, rr, 0.0, TAU,
					arc_segments(rr), to_color(op["col"]), float(op.get("w", 1.0)))
			"band":
				var inner := float(op["ri"])
				var outer := float(op["ro"])
				var bc := _v2(op["c"]) - origin
				var bcol := to_color(op["col"])
				if inner <= 0.0:
					ci.draw_circle(bc, outer, bcol)
				else:
					ci.draw_arc(bc, (inner + outer) * 0.5, 0.0, TAU,
						arc_segments(outer), bcol, outer - inner)
			"rect":
				var rect := _rect(op["rect"], origin)
				var rad := int(op.get("radius", 0))
				var rw := int(op.get("w", 0))
				if rad > 0:
					ci.draw_style_box(_style_box(to_color(op["col"]), rad, rw),
						rect)
				elif rw > 0:
					ci.draw_rect(rect, to_color(op["col"]), false, float(rw))
				else:
					ci.draw_rect(rect, to_color(op["col"]), true)
			"ellipse":
				var er := _rect(op["rect"], origin)
				var ecol := to_color(op["col"])
				var ew := int(op.get("w", 0))
				var pts := ellipse_points(er)
				if ew > 0:
					pts.append(pts[0])
					ci.draw_polyline(pts, ecol, float(ew))
				else:
					ci.draw_colored_polygon(pts, ecol)
			"poly":
				var poly := PackedVector2Array()
				for p in op["pts"]:
					poly.append(_v2(p) - origin)
				ci.draw_colored_polygon(poly, to_color(op["col"]))
			"text":
				var f := font_for(str(op.get("style", "body")))
				if f == null:
					continue
				var size := int(op.get("size", 18))
				var tcol := to_color(op["col"])
				var pos := _v2(op["pos"]) - origin
				var ascent := float(op.get("asc", int(f.get_ascent(size))))
				# Op membawa TOPLEFT rect teks (paritas `blit(text_surf, rect)`
				# pygame); draw_string memakai BASELINE -> turun sebesar ascent.
				ci.draw_string(f, pos + Vector2(0.0, ascent),
					str(op.get("text", "")), HORIZONTAL_ALIGNMENT_LEFT, -1,
					size, tcol)


static func ellipse_points(rect: Rect2,
		segments: int = ELLIPSE_SEGMENTS) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var c := rect.position + rect.size * 0.5
	var rx := rect.size.x * 0.5
	var ry := rect.size.y * 0.5
	for i in range(segments):
		var a := TAU * float(i) / float(segments)
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	return pts


# ═══════════════════════════════════════════════════════════════════
# Profil alpha radial (dipakai oracle + replay test mengunci pita aura)
# ═══════════════════════════════════════════════════════════════════

## Alpha hasil op pada jarak 0..max_d px dari `center`. Meniru raster pygame:
## pita menutup inner < d <= outer, cakram d <= r, cincin |d - r| <= w/2.
## Op yang pusatnya bukan `center` diabaikan (satu sistem aura per profil).
static func radial_profile(ops: Array, center: Array, max_d: int) -> Array:
	var prof := []
	prof.resize(max_d + 1)
	for i in range(prof.size()):
		prof[i] = 0
	var c := _v2(center)
	for o in ops:
		var op: Dictionary = o
		var kind := str(op.get("k", ""))
		if kind != "band" and kind != "disc" and kind != "ring":
			continue
		if not op.has("c"):
			continue
		var oc := _v2(op["c"])
		if absf(oc.x - c.x) > 0.5 or absf(oc.y - c.y) > 0.5:
			continue
		var alpha := int(to_color(op["col"]).a8)
		if kind == "band":
			var inner := float(op["ri"])
			var outer := float(op["ro"])
			for d in range(prof.size()):
				# ri <= 0 = cakram penuh (menutup pusat d = 0); selain itu
				# pita menutup inner < d <= outer.
				if float(d) <= outer and (float(d) > inner or inner <= 0.0):
					prof[d] = alpha
		elif kind == "disc":
			var r := float(op["r"])
			for d2 in range(prof.size()):
				if float(d2) <= r:
					prof[d2] = alpha
		else:
			var rr := float(op["r"])
			var hw := float(op.get("w", 1.0)) * 0.5
			for d3 in range(prof.size()):
				if absf(float(d3) - rr) <= hw:
					prof[d3] = alpha
	return prof
