# LevelIntro.gd — port LevelIntroScreen (effects_level_intro.py _render.py:2679)
#
# Layar intro split-screen sebelum tiap level (paritas Game.reset _core.py:1608):
#   kiri  = LEVEL <nomor> raksasa, nama, deskripsi, bar kesulitan,
#           VICTORY REWARD / STARTING GOLD / PASSIVE income,
#   kanan = FINAL BOSS: tag kelas, siluet boss (aura + sinar + mahkota + mata),
#           nama + gelar, "PREPARE FOR BATTLE" berdenyut,
#   bawah = prompt "PRESS SPACE TO BEGIN" (muncul setelah fade-in).
#
# Gameplay PAUSE selama intro aktif (update() pygame return lebih dulu,
# _core.py:1978-1981); skip = SPACE / ENTER / klik (handle_skip :2752).
# Dibangun seluruhnya dari kode (tanpa .tscn) mengikuti pola MainMenu.gd.
extends CanvasLayer

const SCREEN_W := 1280.0
const SCREEN_H := 720.0
const FADE_IN_FRAMES := 30.0 # 0,5 dtk @60fps

## Tint per tema map — port persis tabel if/elif LevelIntroScreen.draw
## (_render.py:2797-2841). Kunci yang tidak ada jatuh ke forest.
const THEME_TINTS: Dictionary = {
	"desert": Color(0.392, 0.235, 0.078),
	"ice": Color(0.157, 0.314, 0.510),
	"ocean": Color(0.118, 0.275, 0.471),
	"abyss": Color(0.157, 0.039, 0.039),
	"nethervenom": Color(0.098, 0.216, 0.059),
	"spectral": Color(0.059, 0.196, 0.216),
	"sundered": Color(0.275, 0.118, 0.031),
	"empyrean": Color(0.275, 0.216, 0.059),
	"solaris": Color(0.333, 0.196, 0.039),
	"abysstide": Color(0.039, 0.196, 0.196),
	"crimsonmatriarch": Color(0.235, 0.039, 0.059),
	"astral": Color(0.059, 0.098, 0.235),
	"shadowchain": Color(0.176, 0.047, 0.235),
	"frostveil": Color(0.098, 0.176, 0.333),
	"warshade": Color(0.039, 0.157, 0.188),
	"outlaw": Color(0.314, 0.176, 0.137),
	"hexbound": Color(0.216, 0.098, 0.294),
	"voidbound": Color(0.176, 0.071, 0.275),
	"earthborn": Color(0.176, 0.216, 0.098),
	"heartbane": Color(0.235, 0.071, 0.216),
	"sunfist": Color(0.314, 0.216, 0.047),
	"voidwing": Color(0.176, 0.059, 0.255),
	"crimsondevourer": Color(0.235, 0.039, 0.059),
	"elementweave": Color(0.216, 0.118, 0.294),
	"tempest": Color(0.078, 0.157, 0.353),
	"sawmill": Color(0.275, 0.176, 0.071),
	"croweye": Color(0.216, 0.047, 0.071),
	"crystalstorm": Color(0.118, 0.176, 0.333),
	"eternalwarlord": Color(0.275, 0.059, 0.078),
	"explosiveart": Color(0.275, 0.071, 0.071),
	"sandshadow": Color(0.333, 0.137, 0.086),
	"emberweaver": Color(0.373, 0.110, 0.086),
	"skyfury": Color(0.275, 0.176, 0.078),
	"forest": Color(0.078, 0.157, 0.078),
}

var active: bool = true
## True kalau intro ini yang membekukan SceneTree (finish() wajib melepasnya).
var _owns_pause: bool = false
var level_config: Dictionary = {}
var level_num: int = 1

# Cache info boss (dari bosses.json lewat BossDB)
var boss_type_s: String = "abaddon"
var boss_name: String = "Unknown"
var boss_title: String = "The Boss"
var boss_class: String = "true"
var boss_color: Color = Color(0.59, 0.39, 0.78)
var boss_entrance: Color = Color(0.59, 0.39, 0.78)

var _frame: float = 0.0
var _time: float = 0.0
var _root: Control = null
var _bg: ColorRect = null
var _tint: ColorRect = null
var _vignette: Control = null
var _shapes: Control = null
var _labels: Array = []
var _prompt_bar: Control = null
var _prompt_label: Label = null
var _tag_bg_rect: Rect2 = Rect2()

var _font_title: Font = null
var _font_semibold: Font = null
var _font_medium: Font = null
var _font_regular: Font = null
var _font_bold: Font = null


func setup(cfg: Dictionary, level_number: int) -> void:
	level_config = cfg
	level_num = level_number
	var bt := str(cfg.get("true_boss", "abaddon"))
	boss_type_s = bt
	var bd: Dictionary = BossDB.get_boss(bt)
	boss_name = str(bd.get("name", "Unknown"))
	boss_title = str(bd.get("title", "The Boss"))
	boss_class = str(bd.get("boss_class", "true"))
	boss_color = _parse_color(bd.get("color"), Color(0.59, 0.39, 0.78))
	boss_entrance = _parse_color(bd.get("entrance_color"), boss_color)
	_build()
	# SFX pembuka intro (paritas LevelIntroScreen.update _render.py:2737)
	AudioManager.play_sfx("wave_start", 1.0)


func _ready():
	layer = 30
	# Intro tetap beranimasi walau SceneTree di-pause (gameplay dibekukan
	# selama intro aktif, paritas _core.py:1978-1981).
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("cinematic")


func _build() -> void:
	_font_title = load("res://assets/fonts/Cinzel.ttf")
	_font_semibold = load("res://assets/fonts/Barlow-SemiBold.ttf")
	_font_medium = load("res://assets/fonts/Barlow-Medium.ttf")
	_font_regular = load("res://assets/fonts/Barlow-Regular.ttf")
	_font_bold = load("res://assets/fonts/Barlow-Bold.ttf")

	_root = Control.new()
	MobileLayout.fill_parent(_root)
	# Klik ditangani Main._unhandled_input (paritas Game.handle_click yang
	# mengecek intro sebelum InputHandler) — jangan telan event di sini.
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)

	_bg = ColorRect.new()
	MobileLayout.fill_parent(_bg)
	_bg.color = Color(0, 0, 0, 0)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_bg)

	_tint = ColorRect.new()
	MobileLayout.fill_parent(_tint)
	var theme := str(level_config.get("map_theme", "forest"))
	var tint_c: Color = THEME_TINTS.get(theme, THEME_TINTS["forest"])
	_tint.color = Color(tint_c.r, tint_c.g, tint_c.b, 0)
	_tint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_tint)

	_vignette = Control.new()
	MobileLayout.fill_parent(_vignette)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vignette.draw.connect(_draw_vignette)
	_root.add_child(_vignette)

	_shapes = Control.new()
	MobileLayout.fill_parent(_shapes)
	_shapes.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_shapes.draw.connect(_draw_shapes)
	_root.add_child(_shapes)

	_build_left_labels()
	_build_right_labels()
	_build_prompt()


static func _parse_color(v, fallback: Color) -> Color:
	if v is Color:
		return v
	if typeof(v) == TYPE_STRING and String(v).begins_with("#"):
		return Color(String(v))
	return fallback


func _label(parent: Control, text: String, font: Font, size: int,
		color: Color, center: Vector2, shadow: bool = false) -> Label:
	var l := Label.new()
	l.text = text
	if font != null:
		l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if shadow:
		l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.31))
		l.add_theme_constant_override("shadow_offset_x", 4)
		l.add_theme_constant_override("shadow_offset_y", 4)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(l)
	# Label diukur dulu, baru dipusatkan (get_rect butuh size terisi).
	var sz := l.get_combined_minimum_size()
	l.position = center - sz / 2.0
	_labels.append(l)
	return l


func _build_left_labels() -> void:
	var cx := SCREEN_W / 4.0
	_label(_root, "LEVEL", _font_semibold, 32, Color(0.706, 0.784, 0.863),
		Vector2(cx, 130))
	_label(_root, str(level_num), _font_title, 200, Color(1.0, 0.863, 0.392),
		Vector2(cx, 230), true)
	# lv_name/level_desc: JANGAN pakai "name" — bayangi Node.name (warning)
	var lv_name := str(level_config.get("name", ""))
	if lv_name != "":
		_label(_root, lv_name, _font_title, 46, Color(0.941, 0.941, 0.980),
			Vector2(cx, 390), true)
	var level_desc := str(level_config.get("description", ""))
	if level_desc != "":
		_label(_root, level_desc, _font_medium, 24, Color(0.706, 0.784, 0.863),
			Vector2(cx, 440))
	# ── Difficulty (label saja; 5 bar digambar _draw_shapes) ──
	var diff := GameManager.difficulty
	var diff_title := "DIFFICULTY: NORMAL"
	var diff_color := Color(0.392, 0.863, 0.588)
	if diff == "hard":
		diff_title = "DIFFICULTY: HARD"
		diff_color = Color(1.0, 0.471, 0.392)
	elif diff == "easy":
		diff_title = "DIFFICULTY: EASY"
		diff_color = Color(0.392, 0.824, 1.0)
	_label(_root, diff_title, _font_regular, 20, diff_color, Vector2(cx, 500))
	# ── VICTORY REWARD (koin digambar _draw_shapes) ──
	_label(_root, "VICTORY REWARD", _font_regular, 20, Color(0.588, 0.667, 0.745),
		Vector2(cx, 560))
	var reward := int(level_config.get("meta_gold_reward_win", 500))
	var rl := _label(_root, "+%d HERO GOLD" % reward, _font_semibold, 32,
		Color(1.0, 0.863, 0.392), Vector2.ZERO)
	rl.position = Vector2(cx - 60.0 + 18.0, 578)
	# ── STARTING GOLD — angka pakai rumus yang sama dengan Game.reset supaya
	# intro selalu jujur (paritas _render.py:3067-3073) ──
	_label(_root, "STARTING GOLD", _font_regular, 20, Color(0.588, 0.667, 0.745),
		Vector2(cx, 638))
	var sg := GameManager.compute_starting_gold(level_config, level_num)
	var sl := _label(_root, "%s GOLD" % _format_thousands(sg), _font_semibold, 32,
		Color(1.0, 0.863, 0.392), Vector2.ZERO)
	sl.position = Vector2(cx - 60.0 + 18.0, 656)
	# ── PASSIVE INCOME ──
	var rate := GameManager.compute_gold_per_second(level_num)
	_label(_root, "PASSIVE +%s/s" % GameManager.format_gold_rate(rate),
		_font_regular, 20, Color(0.769, 0.945, 0.659), Vector2(cx, 696))


func _build_right_labels() -> void:
	var cx := SCREEN_W * 3.0 / 4.0
	_label(_root, "FINAL BOSS", _font_semibold, 32, Color(1.0, 0.392, 0.392),
		Vector2(cx, 130))
	var tag_text := "TRUE BOSS"
	var tag_color := Color(1.0, 0.314, 0.314)
	if boss_class != "true":
		tag_text = "MINI BOSS"
		tag_color = Color(1.0, 0.784, 0.392)
	var tag := _label(_root, tag_text, _font_medium, 24, tag_color,
		Vector2(cx, 165))
	# Tag bg digambar _draw_shapes; ukurannya dari label (inflate 30/8,
	# paritas _render.py:3113)
	_tag_bg_rect = Rect2(tag.position - Vector2(15, 4),
		tag.get_combined_minimum_size() + Vector2(30, 8))
	_label(_root, boss_name, _font_title, 46, boss_entrance,
		Vector2(cx, 540), true)
	_label(_root, "\"%s\"" % boss_title, _font_semibold, 32,
		Color(0.784, 0.784, 0.863), Vector2(cx, 585), true)
	# ui_theme.letter(): pygame menyelipkan spasi antar huruf (tracking manual)
	_label(_root, _letter("PREPARE FOR BATTLE"), _font_medium, 24,
		Color(1.0, 0.431, 0.392), Vector2(cx, 635))


func _build_prompt() -> void:
	var cx := SCREEN_W / 2.0
	var prompt_y := SCREEN_H - 60.0
	_prompt_bar = Control.new()
	_prompt_bar.position = Vector2(cx - 200, prompt_y - 22.5)
	_prompt_bar.size = Vector2(400, 45)
	_prompt_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_bar.draw.connect(_draw_prompt_bar)
	_prompt_bar.visible = false
	_root.add_child(_prompt_bar)
	_prompt_label = _label(_prompt_bar, "PRESS SPACE TO BEGIN", _font_semibold,
		32, Color(1.0, 0.863, 0.392), Vector2(200, 22.5), true)


## Paritas ui_theme.letter (ui_theme.py:171): "ABC" -> "A B C"
static func _letter(text: String) -> String:
	return HudLayout.letter(text)


## Paritas f"{n:,}" Python (pemisah ribuan koma)
static func _format_thousands(n: int) -> String:
	var s := str(absi(n))
	var out := ""
	var i := 0
	while i < s.length():
		if i > 0 and (s.length() - i) % 3 == 0:
			out += ","
		out += s[i]
		i += 1
	return ("-" if n < 0 else "") + out


func _process(delta: float) -> void:
	# _root null = setup() belum dipanggil (frame antara add_child & setup)
	if not active or _root == null:
		return
	_frame += delta * 60.0
	_time += delta
	var fade := clampf(_frame / FADE_IN_FRAMES, 0.0, 1.0)
	# darken(surface, min(255, fade_alpha+30)) — latar sedikit lebih cepat pekat
	_bg.color.a = minf(1.0, fade + 30.0 / 255.0)
	_tint.color.a = fade * 30.0 / 255.0
	for l in _labels:
		if is_instance_valid(l):
			l.modulate.a = fade
	if _frame > FADE_IN_FRAMES:
		_prompt_bar.visible = true
		_prompt_bar.queue_redraw()
		_prompt_label.modulate.a = 1.0
	_shapes.queue_redraw()
	_vignette.queue_redraw()


# ══════════════════════════════════════════════════════════
#  GAMBAR PROSEDURAL (divider, siluet, koin, bar kesulitan)
# ══════════════════════════════════════════════════════════

func _draw_vignette() -> void:
	var fade := clampf(_frame / FADE_IN_FRAMES, 0.0, 1.0)
	if fade <= 0.0:
		return
	# 60 ring persegi makin gelap ke tepi (paritas _paint_vignette :2869-2874)
	for i in range(60):
		var a := float(i) * 3.0 / 255.0 * fade
		_vignette.draw_rect(Rect2(float(i), float(i),
			SCREEN_W - float(i) * 2.0, SCREEN_H - float(i) * 2.0),
			Color(0, 0, 0, a), false, 1.0)


func _draw_shapes() -> void:
	var fade := clampf(_frame / FADE_IN_FRAMES, 0.0, 1.0)
	if fade <= 0.0:
		return
	var cx_l := SCREEN_W / 4.0
	var cx_r := SCREEN_W * 3.0 / 4.0
	# ── Divider tengah + 3 berlian emas (paritas :2903-2915) ──
	var div_x := SCREEN_W / 2.0
	_shapes.draw_line(Vector2(div_x, 100), Vector2(div_x, SCREEN_H - 100),
		Color(0.392, 0.392, 0.510, fade), 2.0)
	for i in range(3):
		var y := 250.0 + float(i) * 200.0
		var pts := PackedVector2Array([
			Vector2(div_x, y - 8), Vector2(div_x + 8, y),
			Vector2(div_x, y + 8), Vector2(div_x - 8, y),
		])
		_shapes.draw_colored_polygon(pts, Color(1.0, 0.863, 0.392, fade))
	# ── Garis dekor di bawah angka level ──
	_shapes.draw_line(Vector2(cx_l - 150, 350), Vector2(cx_l + 150, 350),
		Color(1.0, 0.863, 0.392, fade), 2.0)
	_shapes.draw_line(Vector2(cx_l - 100, 353), Vector2(cx_l + 100, 353),
		Color(1.0, 1.0, 0.784, fade), 1.0)
	_draw_difficulty_bars(cx_l, fade)
	_draw_coin(Vector2(cx_l - 60, 590), fade)
	_draw_coin(Vector2(cx_l - 60, 668), fade)
	_draw_tag_bg(fade)
	_draw_silhouette(Vector2(cx_r, SCREEN_H / 2.0 - 20.0), fade)


func _draw_difficulty_bars(cx: float, fade: float) -> void:
	var hp_mult := float(level_config.get("enemy_hp_mult", 1.0))
	var diff_level := 1
	if GameManager.difficulty == "hard":
		diff_level = clampi(int(hp_mult * 2.5), 1, 5)
	var bar_start_x := cx - float(5 * 22) / 2.0
	for i in range(5):
		var bar_col := Color(0.235, 0.235, 0.275)
		if i < diff_level:
			if i >= 3:
				bar_col = Color(1.0, 0.392, 0.314)
			elif i >= 1:
				bar_col = Color(1.0, 0.784, 0.314)
			else:
				bar_col = Color(0.392, 0.863, 0.392)
		bar_col.a = fade
		_shapes.draw_rect(Rect2(bar_start_x + float(i) * 22.0, 520, 18, 10),
			bar_col, true)


func _draw_coin(pos: Vector2, fade: float) -> void:
	_shapes.draw_circle(pos, 12.0, Color(1.0, 0.784, 0.196, fade))
	_shapes.draw_arc(pos, 12.0, 0.0, TAU, 24, Color(0.784, 0.588, 0.118, fade), 2.0)
	if _font_bold != null:
		var s := "$"
		var fs: Vector2 = _font_bold.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, 24)
		_shapes.draw_string(_font_bold, pos - Vector2(fs.x / 2.0, -fs.y / 4.0),
			s, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(0.392, 0.235, 0.039, fade))


func _draw_tag_bg(fade: float) -> void:
	var tag_color := Color(1.0, 0.314, 0.314) if boss_class == "true" else Color(1.0, 0.784, 0.392)
	var fill := tag_color
	fill.a = fade / 4.0
	var border := tag_color
	border.a = fade
	# RoundRect tidak ada di draw API; StyleBoxFlat tidak bisa digambar langsung —
	# cukup persegi sudut kecil: gambar polygon + border.
	_shapes.draw_rect(_tag_bg_rect, fill, true)
	_shapes.draw_rect(_tag_bg_rect, border, false, 2.0)


func _draw_silhouette(c: Vector2, fade: float) -> void:
	# ═══ ENERGY AURA (paritas _draw_boss_silhouette :3199-3212) ═══
	var aura_pulse := sin(_time * 3.0) * 0.3 + 0.7
	var aura_r := 140.0 * aura_pulse
	var r := aura_r
	while r > 20.0:
		var a := (aura_r - r) * 1.5 / 255.0 * fade
		if a > 0.0:
			_shapes.draw_circle(c, r, Color(boss_entrance.r, boss_entrance.g,
				boss_entrance.b, a))
		r -= 6.0
	# ═══ RADIATING RAYS (desktop: 12 sinar, paritas :3225-3234) ═══
	var ray_alpha := 50.0 / 255.0 * fade
	for i in range(12):
		var ang := float(i) * TAU / 12.0 + _time * 0.5
		var sx := c.x + cos(ang) * 90.0
		var sy := c.y + sin(ang) * 90.0
		var ex := c.x + cos(ang) * 180.0
		var ey := c.y + sin(ang) * 180.0
		_shapes.draw_line(Vector2(sx, sy), Vector2(ex, ey),
			Color(boss_entrance.r, boss_entrance.g, boss_entrance.b, ray_alpha), 3.0)
	# ═══ BADAN SILUET (polygon sama persis dengan pygame :3237-3252) ═══
	var body_pts := PackedVector2Array([
		c + Vector2(-55, -20), c + Vector2(-35, -75), c + Vector2(0, -95),
		c + Vector2(35, -75), c + Vector2(55, -20), c + Vector2(65, 35),
		c + Vector2(45, 85), c + Vector2(-45, 85), c + Vector2(-65, 35),
	])
	var shadow_pts := PackedVector2Array()
	for p in body_pts:
		shadow_pts.append(p + Vector2(3, 3))
	_shapes.draw_colored_polygon(shadow_pts, Color(0, 0, 0, fade / 2.0))
	_shapes.draw_colored_polygon(body_pts, Color(0, 0, 0, fade))
	var inner_pts := PackedVector2Array([
		c + Vector2(-50, -15), c + Vector2(-30, -70), c + Vector2(0, -90),
		c + Vector2(30, -70), c + Vector2(50, -15), c + Vector2(60, 30),
		c + Vector2(40, 80), c + Vector2(-40, 80), c + Vector2(-60, 30),
	])
	var dark := boss_color.darkened(0.35)
	_shapes.draw_colored_polygon(inner_pts, Color(dark.r, dark.g, dark.b, fade / 3.0))
	# ═══ MAHKOTA (true=5 duri, mini=3 — paritas :3255-3264) ═══
	var num_spikes := 5 if boss_class == "true" else 3
	for i in range(num_spikes):
		var spike_x := (c.x - 40.0 + float(i) * 20.0) if num_spikes == 5 else (c.x - 20.0 + float(i) * 20.0)
		var spike_y := c.y - 95.0
		var spike_h := 25.0 + float(i % 2) * 10.0
		_shapes.draw_colored_polygon(PackedVector2Array([
			Vector2(spike_x - 6, spike_y),
			Vector2(spike_x, spike_y - spike_h),
			Vector2(spike_x + 6, spike_y),
		]), Color(0, 0, 0, fade))
	# ═══ MATA MENYALA (paritas :3277-3290) ═══
	var eye_pulse := sin(_time * 8.0) * 0.3 + 0.7
	for eye_x in [c.x - 20.0, c.x + 20.0]:
		var eye_c := Vector2(eye_x, c.y - 55.0)
		var gr := 12.0
		while gr > 0.0:
			var a := (200.0 * eye_pulse * fade - gr * 12.0) / 255.0
			if a > 0.0:
				_shapes.draw_circle(eye_c, gr,
					Color(boss_entrance.r, boss_entrance.g, boss_entrance.b, a))
			gr -= 2.0


func _draw_prompt_bar() -> void:
	if not _prompt_bar.visible:
		return
	# Denyut dari jam (paritas sin(ticks*0.005)*0.3+0.7)
	var pulse := sin(_time * 5.0) * 0.3 + 0.7
	var w := _prompt_bar.size.x
	var h := _prompt_bar.size.y
	_prompt_bar.draw_rect(Rect2(0, 0, w, h), Color(0, 0, 0, 150.0 / 255.0 * pulse), true)
	_prompt_bar.draw_rect(Rect2(0, 0, w, h),
		Color(1.0, 0.863, 0.392, 220.0 / 255.0 * pulse), false, 2.0)
	if pulse > 0.5:
		_corner_ticks(_prompt_bar, Rect2(0, 0, w, h),
			Color(1.0, 0.863, 0.471, pulse), 10.0, 2.0, 4.0)
	_prompt_label.modulate.a = pulse


## Paritas ui_theme.corner_ticks (ui_theme.py:509): tanda L emas di 4 sudut
static func _corner_ticks(cv: CanvasItem, rect: Rect2, color: Color,
		length: float, width: float, inset: float) -> void:
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


# ══════════════════════════════════════════════════════════
#  SKIP / SELESAI
# ══════════════════════════════════════════════════════════

func cinematic_active() -> bool:
	return active


## Paritas handle_skip (SPACE / ENTER / klik) — ESC sengaja TIDAK skip
## (_render.py:2752-2757), supaya ESC tetap bisa membuka menu pause seperti pygame.
func skip_key(event: InputEventKey) -> bool:
	if not active:
		return false
	if event.keycode == KEY_SPACE or event.keycode == KEY_ENTER \
			or event.keycode == KEY_KP_ENTER:
		finish()
		return true
	return false


func skip_click() -> bool:
	if not active:
		return false
	finish()
	return true


func finish() -> void:
	if not active:
		return
	active = false
	if _owns_pause:
		get_tree().paused = false
		GameManager.set_paused(false)
	queue_free()


## Dipanggil Main saat membekukan match: intro memegang kendali pause.
func take_pause_ownership() -> void:
	_owns_pause = true
