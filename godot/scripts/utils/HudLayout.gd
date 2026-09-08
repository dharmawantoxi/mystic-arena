# HudLayout — kanon aturan UI/HUD in-match (paritas pygame).
#
# Semua konstanta layout, format teks HUD, easing banner wave, nama castle,
# predikat equip item, geometri touch HUD, dan daftar TERTUTUP ui_key tombol
# ShopPanel tinggal di sini supaya SAMA dipakai HUD/ShopPanel/Manajer dan
# dikunci UiHudParityTest. Sumber: _core.py (InputHandler._touch_rect,
# Game._draw_gold_hud, format_gold_rate, gate equip, Menu._draw_pause_buttons),
# _render.py (WaveAnnouncer + easing, format match time), ui_components/
# _bundle.py (Overlay.draw, HeroPanel, MobileTouchHUD, castle_names),
# hero_items.py (_touch_hit, gate range 80, is_magic_hero), ui_theme.letter.
#
# Replay: UiHudParityTest vs seksi ui_hud di match_parity.json.
extends RefCounted
class_name HudLayout

## Gate melee untuk equip item (hero_items.py:4057): DENY melee_only kalau
## range > 80. (Hero.is_melee_hero memakai < 110 — itu gate audio/animasi +
## get_range_bonus, JANGAN dipakai di sini. 0 dari 222 hero punya range
## 80..110 jadi keduanya tak pernah divergen, tapi 80 adalah nilai
## evidence-anchored untuk equip.)
const MELEE_RANGE_MAX := 80

## Ukuran banner wave (WaveAnnouncer.draw: 400x80, blit di (cx-200, cy-40)).
const WAVE_BANNER_SIZE := Vector2(400, 80)
## Posisi banner saat hold (cx=640, cy=240: (440, 200)).
const WAVE_BANNER_POS := Vector2(440, 200)
## Durasi banner: 120 frame @60fps (WaveAnnouncer.update decrement 1/frame).
const WAVE_BANNER_FRAMES := 120
## Fraksi fase slide-in / hold / slide-out (draw: p<0.2 masuk, p<0.7 tahan).
const WAVE_PHASE_IN := 0.2
const WAVE_PHASE_HOLD := 0.7
## Lebar fase slide-out HARUS literal ini (pygame membagi (progress-0.7)/0.3).
const WAVE_PHASE_OUT := 0.3
## Durasi tween Godot per fase (detik): 120 frame @60fps = 2.0 total;
## 0.2*2=0.4 masuk, 0.5*2=1.0 tahan, 0.3*2=0.6 keluar.
const WAVE_TWEEN_IN := 0.4
const WAVE_TWEEN_HOLD := 1.0
const WAVE_TWEEN_OUT := 0.6

## Urutan tombol pause pygame (Menu._draw_pause_buttons).
const PAUSE_BUTTON_ORDER := ["resume", "settings_pause", "main_menu", "quit"]
## Ukuran tiap tombol pause (300x48, x=490 terpusat).
const PAUSE_BUTTON_SIZE := Vector2(300, 48)
## Panel pause 400x400 terpusat (=(1280-400)/2, (720-400)/2 = (440, 160)).
const PAUSE_PANEL_SIZE := Vector2(400, 400)
const PAUSE_PANEL_POS := Vector2(440, 160)

## Nama castle per level nexus (_bundle.py:3632-3636; level 6+ = CITADEL).
const CASTLE_NAMES := {
	1: "OUTPOST", 2: "WATCHTOWER", 3: "FORTRESS",
	4: "STRONGHOLD", 5: "ROYAL CASTLE",
}
const CASTLE_NAME_DEFAULT := "CITADEL"

## Target sentuh minimum 48px (_touch_rect/_touch_hit: minimum=48, padding=6).
const TOUCH_MINIMUM := 48.0
const TOUCH_PADDING := 6.0

## ── COMBO (ComboCounter.draw pygame; data dikunci match_scoring) ──
## Pusat counter: cx = screen_w - 100, cy = 100 (kanan atas).
const COMBO_CENTER_FROM_RIGHT := 100.0
const COMBO_CENTER_Y := 100.0
## Bar jam pasir 80x4 di (cx - 40, cy + 40) — hanya digambar count >= 2.
const COMBO_BAR_SIZE := Vector2(80, 4)
const COMBO_BAR_OFFSET := Vector2(0, 40)
## Label ambang dipusatkan di (cx, cy - 30) — hanya count >= 5.
const COMBO_LABEL_OFFSET := Vector2(0, -30)

## ── POPUP ACHIEVEMENT (AchievementPopup.draw pygame) ──
## Panel 280x60 di (screen_w - 280 - 20 + slide, 180) — di bawah combo.
const ACHIEVEMENT_PANEL_SIZE := Vector2(280, 60)
const ACHIEVEMENT_PANEL_MARGIN := 20.0
const ACHIEVEMENT_PANEL_Y := 180.0
## Durasi tampil satu popup: 180 frame @60fps = 3 detik.
const ACHIEVEMENT_FRAMES := 180
## Slide 300px dari kanan: masuk < 0.15 (ease-out-back), tahan, keluar
## >= 0.85 (linear). Pembanding fase HARUS literal 0.15 seperti pygame
## ((progress - 0.85) / 0.15) — lihat catatan WAVE_PHASE_OUT soal selisih
## ulp pembagian.
const ACHIEVEMENT_SLIDE_PX := 300.0
const ACHIEVEMENT_PHASE_IN := 0.15
const ACHIEVEMENT_PHASE_OUT := 0.85
## Offset teks di dalam panel (blit langsung pygame): header (55, 7),
## judul (55, 24), deskripsi (55, 45); ikon lingkaran di (15, 30).
const ACHIEVEMENT_TEXT_HEADER := Vector2(55, 7)
const ACHIEVEMENT_TEXT_TITLE := Vector2(55, 24)
const ACHIEVEMENT_TEXT_DESC := Vector2(55, 45)
const ACHIEVEMENT_ICON_POS := Vector2(15, 30)
## Warna teks panel (font render pygame — data, bukan piksel).
const ACHIEVEMENT_HEADER_COLOR := Color(1.0, 220.0 / 255.0, 50.0 / 255.0)
const ACHIEVEMENT_TITLE_COLOR := Color.WHITE
const ACHIEVEMENT_DESC_COLOR := Color(205.0 / 255.0, 210.0 / 255.0, 225.0 / 255.0)

## Tombol MobileTouchHUD: id -> [x, y, w, h] + label (fixture touchhud).
const TOUCH_BUTTONS := {
	"pause": {"rect": [22, 76, 52, 52], "label": "II"},
	"debug": {"rect": [106, 76, 52, 52], "label": "FPS"},
	"skip": {"rect": [1110, 646, 160, 58], "label": "SKIP  >>"},
	"replay": {"rect": [330, 620, 165, 62], "label": "REPLAY"},
	"next_level": {"rect": [525, 620, 200, 62], "label": "NEXT LEVEL"},
	"menu": {"rect": [755, 620, 165, 62], "label": "MENU"},
	"back": {"rect": [8, 6, 104, 58], "label": "< BACK"},
}
## Visibilitas tombol touch per state (fixture touchhud.visibility).
const TOUCH_VISIBILITY := {
	"game_playing": {"pause": true, "debug": true, "skip": false,
		"replay": false, "next_level": false, "menu": false, "back": false},
	"game_playing_cine": {"pause": false, "debug": false, "skip": true,
		"replay": false, "next_level": false, "menu": false, "back": false},
	"game_victory_L1": {"pause": false, "debug": true, "skip": false,
		"replay": true, "next_level": true, "menu": true, "back": false},
	"game_victory_L54": {"pause": false, "debug": true, "skip": false,
		"replay": true, "next_level": false, "menu": true, "back": false},
	"game_defeat": {"pause": false, "debug": true, "skip": false,
		"replay": true, "next_level": false, "menu": true, "back": false},
	# Layar menu/pause pygame (sync(game=None)): hanya tombol debug FPS.
	"menu": {"pause": false, "debug": true, "skip": false,
		"replay": false, "next_level": false, "menu": false, "back": false},
	"pause": {"pause": false, "debug": true, "skip": false,
		"replay": false, "next_level": false, "menu": false, "back": false},
}


## Daftar TERTUTUP ui_key tombol ShopPanel — audit closed-world di
## UiHudParityTest menolak key asing/hilang. Pola dinamis (pilihan menara,
## daftar hero, daftar item) dinyatakan sebagai prefix + koleksi sumber.
static func shop_ui_keys() -> Dictionary:
	return {
		"tabs": ["to_hero", "to_tower", "to_nexus", "to_item", "shop_close"],
		"heroes": {"prefix": "buy_hero_",
			"source": HeroDB.get_all_types()},
		"hero_selected": ["upgrade_hero"],
		"tower_build": {"prefix": "build_",
			"source": TowerDB.tower_types()},
		"tower_selected": ["upgrade_tower", "sell_tower", "tower_regen"],
		"tower_repath": {"prefix": "repath_",
			"source": TowerDB.tower_types()},
		"nexus": ["upgrade_nexus", "nexus_shield"],
		"item": {"prefix": "item_buy_",
			"source": ItemDB.items.keys()},
	}


## Format ribuan pygame (f"{gold:,}" → "1,234,567").
static func format_thousands(value: int) -> String:
	var neg := value < 0
	var digits := str(absi(value))
	var out := ""
	while digits.length() > 3:
		out = "," + digits.right(3) + out
		digits = digits.left(digits.length() - 3)
	return ("-" if neg else "") + digits + out


## Format laju gold pygame: f"{rate:.1f}".rstrip("0").rstrip(".").
## Python membulatkan NILAI BINER eksak ke desimal terdekat (ties-to-even),
## jadi replika memakai bit IEEE-754 langsung — "%.1f" GDScript TIDAK
## diverifikasi identik dan shortest-repr SALAH untuk 2.675 (desimal "2.675"
## terlihat seperti tie, tapi doube-nya 2.6749999... → "2.7").
## Terbukti identik untuk semua finite double; UiHudParityTest mengunci baterai
## oracle (3.0/3.75/5.7/7.125/0.0/2.675/4.5/2.475/3.25/6.75).
static func format_gold_rate(rate: float) -> String:
	var bits := _double_bits(rate)
	var neg := bits < 0
	var exp := int((bits >> 52) & 0x7FF)
	var mant := bits & 0xFFFFFFFFFFFFF
	if exp == 0x7FF:
		# inf/nan: Python f"{x:.1f}" = "inf"/"nan" (tanpa strip).
		return ("-" if neg else "") + ("inf" if mant == 0 else "nan")
	var m: int
	var e: int
	if exp == 0:
		m = mant # subnormal (m=0 → nol)
		e = -1074
	else:
		m = mant | 0x10000000000000
		e = exp - 1075
	if m == 0:
		return "-0" if neg else "0" # f"{-0.0:.1f}".rstrip.. = "-0"
	# tenths = round_half_even(|rate| * 10); |rate|*10 = (m*5) * 2^(e+1).
	var d := m * 5
	var k2 := e + 1
	var tenths := 0
	if k2 >= 0:
		var room := 0
		if k2 < 63:
			room = 9223372036854775807 >> k2
		if d > room:
			# Di luar jangkauan realistis (> ~1e17/s): fallback format engine.
			return _strip_rate("%.1f" % rate)
		tenths = d << k2
	else:
		var k := -k2
		if k >= 63:
			tenths = 0 # |rate|*10 < 2^-7 → 0 (frac selalu < 1/2)
		else:
			var q0 := d >> k
			var r := d - (q0 << k)
			var twice := r * 2
			var half := 1 << k
			if twice > half:
				tenths = q0 + 1
			elif twice < half:
				tenths = q0
			else:
				tenths = q0 if q0 % 2 == 0 else q0 + 1
	var s := "%d.%d" % [tenths / 10, tenths % 10]
	return ("-" if neg else "") + _strip_rate(s)


## rstrip("0").rstrip(".") untuk string "%.1f".
static func _strip_rate(s: String) -> String:
	if s.ends_with("0"):
		s = s.substr(0, s.length() - 1)
	if s.ends_with("."):
		s = s.substr(0, s.length() - 1)
	return s


## Bit IEEE-754 double sebagai int64 (round-trip encode/decode eksak).
static func _double_bits(rate: float) -> int:
	var b := PackedByteArray()
	b.resize(8)
	b.encode_double(0, rate)
	return b.decode_s64(0)


## Format match time m:ss (_draw_stats: f"{m}:{s:02d}").
static func format_match_time(total_seconds: int) -> String:
	return "%d:%02d" % [int(total_seconds / 60), total_seconds % 60]


## Kata badge mode (_draw_gold_hud: easy→EASY, hard→HARD, else→NORMAL).
static func mode_label(difficulty: String) -> String:
	if difficulty == "easy":
		return "EASY"
	if difficulty == "hard":
		return "HARD"
	return "NORMAL"


## Warna badge mode (easy biru, hard merah, else hijau).
static func mode_color(difficulty: String) -> Color:
	if difficulty == "easy":
		return Color(100.0 / 255.0, 210.0 / 255.0, 255.0 / 255.0)
	if difficulty == "hard":
		return Color(255.0 / 255.0, 120.0 / 255.0, 120.0 / 255.0)
	return Color(120.0 / 255.0, 230.0 / 255.0, 150.0 / 255.0)


## Detik cooldown dari sisa frame (HeroPanel: cooldown // 60 + 1; 0 = siap,
## tanpa label).
static func cooldown_seconds(frames: int) -> int:
	if frames <= 0:
		return 0
	return frames / 60 + 1


## Letter-spacing manual (ui_theme.letter: gap.join(list(text))).
static func letter(text: String, gap: String = " ") -> String:
	var out := PackedStringArray()
	for i in text.length():
		out.append(text.substr(i, 1))
	return gap.join(out)


## Judul banner wave ("WAVE 1").
static func wave_title(wave_num: int) -> String:
	return "WAVE %d" % wave_num


## Subtitle banner (letter("ENEMIES INCOMING") — WaveAnnouncer TAK punya
## varian boss; banner intro boss komponen terpisah).
static func wave_subtitle() -> String:
	return letter("ENEMIES INCOMING")


## Offset x banner wave pada timer tersisa (WaveAnnouncer.draw, IEEE-754
## identik: int() trunc-to-zero dua sisi, ease_out_back c1=1.70158).
static func wave_slide_x(timer: int) -> int:
	var progress := 1.0 - float(timer) / float(WAVE_BANNER_FRAMES)
	if progress < WAVE_PHASE_IN:
		return -1280 + int(1280.0 * _ease_out_back(progress / WAVE_PHASE_IN))
	if progress < WAVE_PHASE_HOLD:
		return 0
	# PEMBAGI HARUS literal 0.3 seperti pygame ((progress - 0.7) / 0.3):
	# 1.0 - 0.7 = 0.30000000000000004 (DOUBLE BERBEDA) menggeser satu titik
	# kurva (t=0: 1719 vs 1720) — dikunci baterai 121 titik.
	return int(1280.0 * _ease_in_back(
		(progress - WAVE_PHASE_HOLD) / WAVE_PHASE_OUT))


## Rect layar penuh banner pada timer tersisa (posisi + 400x80).
static func wave_banner_rect(timer: int) -> Rect2:
	return Rect2(WAVE_BANNER_POS + Vector2(wave_slide_x(timer), 0),
		WAVE_BANNER_SIZE)


## Pusat combo di layar (ComboCounter.draw: cx = screen_w - 100, cy = 100).
static func combo_center(screen_w: float = 1280.0) -> Vector2:
	return Vector2(screen_w - COMBO_CENTER_FROM_RIGHT, COMBO_CENTER_Y)


## Rect bar jam pasir combo (timer_w = 80, timer_x = cx - 40, y = cy + 40).
static func combo_bar_rect(screen_w: float = 1280.0) -> Rect2:
	var c := combo_center(screen_w)
	return Rect2(c + COMBO_BAR_OFFSET - Vector2(COMBO_BAR_SIZE.x * 0.5, 0),
		COMBO_BAR_SIZE)


## Offset x popup achievement pada sisa timer (AchievementPopup.draw:
## masuk = int((1-ease_out_back(p/0.15))*300), tahan 0, keluar linear).
static func achievement_slide_x(timer: int) -> int:
	var progress := 1.0 - float(timer) / float(ACHIEVEMENT_FRAMES)
	if progress < ACHIEVEMENT_PHASE_IN:
		var eased := _ease_out_back(progress / ACHIEVEMENT_PHASE_IN)
		return int((1.0 - eased) * ACHIEVEMENT_SLIDE_PX)
	if progress < ACHIEVEMENT_PHASE_OUT:
		return 0
	return int((progress - ACHIEVEMENT_PHASE_OUT) / ACHIEVEMENT_PHASE_IN
		* ACHIEVEMENT_SLIDE_PX)


## Rect panel popup pada sisa timer (screen_w - 280 - 20 + slide, 180).
static func achievement_panel_rect(timer: int, screen_w: float = 1280.0) -> Rect2:
	return Rect2(
		Vector2(screen_w - ACHIEVEMENT_PANEL_SIZE.x - ACHIEVEMENT_PANEL_MARGIN
			+ achievement_slide_x(timer), ACHIEVEMENT_PANEL_Y),
		ACHIEVEMENT_PANEL_SIZE)


## Alpha popup per fase (slide-in ramp, tahan 255, slide-out ramp) —
## visual; dikembalikan 0..1 (pygame int 0..255).
static func achievement_alpha(timer: int) -> float:
	var progress := 1.0 - float(timer) / float(ACHIEVEMENT_FRAMES)
	if progress < ACHIEVEMENT_PHASE_IN:
		return progress / ACHIEVEMENT_PHASE_IN
	if progress < ACHIEVEMENT_PHASE_OUT:
		return 1.0
	return 1.0 - (progress - ACHIEVEMENT_PHASE_OUT) / ACHIEVEMENT_PHASE_IN


static func _ease_out_back(t: float) -> float:
	# Asosiasi PERSIS pygame: 1 + c3*(t1*t1*t1) + c1*(t1*t1). Bentuk
	# kiri-asosiatif ((c3*t1)*t1)*t1 membulatkan berbeda di ulp terakhir.
	var c1 := 1.70158
	var c3 := c1 + 1.0
	var t1 := t - 1.0
	return 1.0 + c3 * (t1 * t1 * t1) + c1 * (t1 * t1)


static func _ease_in_back(t: float) -> float:
	var c1 := 1.70158
	var c3 := c1 + 1.0
	return c3 * t * t * t - c1 * t * t


## Nama castle untuk level nexus (level 6+ = CITADEL).
static func castle_name(nexus_level: int) -> String:
	return str(CASTLE_NAMES.get(nexus_level, CASTLE_NAME_DEFAULT))


## True kalau range hero termasuk MELEE untuk equip item (NOT range > 80 —
## 0/None di pygame juga melee; di Godot range selalu > 0).
static func is_melee_range(attack_range: float) -> bool:
	return not attack_range > float(MELEE_RANGE_MAX)


## Area sentuh ramah jari (InputHandler._touch_rect): rect diperluas minimum
## 48x48 berpusat di center INTEGER pygame (floor(x + w/2) — Rect2.get_center
## float DIVERGEN untuk lebar ganjil, mis. 21 -> 10.5 vs 10).
static func touch_hit_rect(rect: Rect2, minimum: float = TOUCH_MINIMUM,
		padding: float = TOUCH_PADDING) -> Rect2:
	var w := maxf(rect.size.x + padding * 2.0, minimum)
	var h := maxf(rect.size.y + padding * 2.0, minimum)
	var cx := floorf(rect.position.x + rect.size.x * 0.5)
	var cy := floorf(rect.position.y + rect.size.y * 0.5)
	return Rect2(cx - floorf(w * 0.5), cy - floorf(h * 0.5), w, h)


## Uji titik di area sentuh (_touch_hit: collidepoint; tepi kanan/bawah
## eksklusif — sama di Rect2.has_point).
static func touch_hit(rect: Rect2, point: Vector2,
		minimum: float = TOUCH_MINIMUM,
		padding: float = TOUCH_PADDING) -> bool:
	return touch_hit_rect(rect, minimum, padding).has_point(point)


## Visibilitas tombol touch per state game (matriks fixture touchhud).
static func touch_visibility(state_key: String) -> Dictionary:
	return (TOUCH_VISIBILITY.get(state_key, {}) as Dictionary).duplicate()
