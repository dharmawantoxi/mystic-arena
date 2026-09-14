# BossIntroBanner.gd — port BossIntroCinematic (effects_intro.py _render.py:2152)
#
# Banner kompak di atas layar saat mini/true boss turun (paritas
# _core.py:1826 mini boss / 2105 true boss). Versi pygame terbaru BUKAN
# overlay fullscreen: hanya strip 600x92 yang meluncur dari kiri, jadi
# gameplay TIDAK di-pause selama banner tampil (docstring draw :2246-2251).
#
# Timeline 100 frame @60fps (~1,7 dtk, paritas duration=100 :2168):
#   fade in 12f · slide ease-out 18f · fade out 20 frame terakhir.
# Isi: tag kelas (TRUE BOSS merah / MINI BOSS oranye), nama boss warna
# entrance_color, gelar dalam tanda kutip, HP bar preview mengisi selama
# duration*0.85, sudut emas saat alpha>60.
# Skip: SPACE / ESC / klik (handle_skip :2238) — klik DITELAN (return),
# paritas Game.handle_click _core.py:2567-2569.
extends CanvasLayer

const SCREEN_W := 1280.0
const DURATION_FRAMES := 100.0
const SLIDE_FRAMES := 18.0
const FADE_IN_FRAMES := 12.0
const FADE_OUT_FRAMES := 20.0
const BANNER_W := 600.0
const BANNER_H := 92.0
const BANNER_Y := 12.0

var active: bool = true
var boss_name: String = "Boss"
var boss_title: String = ""
var boss_class: String = "mini"
var entrance_color: Color = Color(0.8, 0.6, 1.0)

var _frame: float = 0.0
var _time: float = 0.0
var _root: Control = null
var _banner: Control = null
var _tag: Label = null
var _name: Label = null
var _title: Label = null


func setup(boss_data: Dictionary) -> void:
	boss_name = str(boss_data.get("name", "Boss"))
	boss_title = str(boss_data.get("title", ""))
	boss_class = str(boss_data.get("boss_class", "mini"))
	var ec = boss_data.get("entrance_color")
	if typeof(ec) == TYPE_STRING and String(ec).begins_with("#"):
		entrance_color = Color(String(ec))
	elif ec is Color:
		entrance_color = ec
	_build()
	# Suara dramatis boss muncul (paritas BossIntroCinematic.update :2222-2229:
	# nexus_hit volume 1.0, diputar sekali di awal)
	AudioManager.play_sfx("nexus_hit", 1.0)


func _ready():
	layer = 28
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("cinematic")


func _build() -> void:
	_root = Control.new()
	MobileLayout.fill_parent(_root)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)

	_banner = Control.new()
	_banner.size = Vector2(BANNER_W, BANNER_H)
	# Posisi frame-0 = hasil rumus elapsed=0 (paritas: x_offset -640) supaya
	# tidak ada kilatan 1 frame di sudut kiri atas; alpha frame-0 = 0 dijaga
	# oleh modulate label + alpha internal _draw_banner.
	_banner.position = Vector2((SCREEN_W - BANNER_W) / 2.0 - 640.0, BANNER_Y)
	_banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.draw.connect(_draw_banner)
	_root.add_child(_banner)

	var font_title: Font = load("res://assets/fonts/Cinzel.ttf")
	var font_medium: Font = load("res://assets/fonts/Barlow-Medium.ttf")

	# ── Tag kelas (font_small 24 @ +14,+8) ──
	_tag = Label.new()
	_tag.text = "TRUE BOSS" if boss_class == "true" else "MINI BOSS"
	if font_medium != null:
		_tag.add_theme_font_override("font", font_medium)
	_tag.add_theme_font_size_override("font_size", 24)
	_tag.add_theme_color_override("font_color",
		Color(1.0, 0.353, 0.353) if boss_class == "true" else Color(1.0, 0.784, 0.392))
	_tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tag.position = Vector2(14, 8)
	_banner.add_child(_tag)

	# ── Nama boss (font_big = Cinzel 46 @ +14,+26) ──
	_name = Label.new()
	_name.text = boss_name
	if font_title != null:
		_name.add_theme_font_override("font", font_title)
	_name.add_theme_font_size_override("font_size", 46)
	_name.add_theme_color_override("font_color", entrance_color)
	_name.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_name.position = Vector2(14, 26)
	_banner.add_child(_name)

	# ── Gelar (font_small 24 @ +14,+64) ──
	_title = Label.new()
	_title.text = "\"%s\"" % boss_title
	if font_medium != null:
		_title.add_theme_font_override("font", font_medium)
	_title.add_theme_font_size_override("font_size", 24)
	_title.add_theme_color_override("font_color", Color(0.843, 0.843, 0.922))
	_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_title.position = Vector2(14, 64)
	_banner.add_child(_title)

	# Fade-in 12 frame dimulai dari alpha 0 (paritas :2256-2258)
	_tag.modulate.a = 0.0
	_name.modulate.a = 0.0
	_title.modulate.a = 0.0


func _process(delta: float) -> void:
	# _banner null = setup() belum dipanggil (frame antara add_child & setup)
	if not active or _banner == null:
		return
	_frame += delta * 60.0
	_time += delta
	var remaining := DURATION_FRAMES - _frame
	if remaining <= 0.0:
		finish()
		return
	# Posisi banner: tengah + offset slide dari kiri, ease-out kubik
	# (paritas x_offset = (1-eased) * -640, :2263-2266)
	var sp := minf(1.0, _frame / SLIDE_FRAMES)
	var eased := 1.0 - pow(1.0 - sp, 3.0)
	var x_offset := (1.0 - eased) * -640.0
	_banner.position = Vector2((SCREEN_W - BANNER_W) / 2.0 + x_offset, BANNER_Y)
	var alpha := _alpha255(remaining)
	_tag.modulate.a = alpha / 255.0
	_name.modulate.a = alpha / 255.0
	_title.modulate.a = alpha / 255.0
	_banner.queue_redraw()


func _alpha255(remaining: float) -> float:
	# Fade in 12 frame awal, fade out 20 frame akhir (paritas :2256-2261)
	if _frame < FADE_IN_FRAMES:
		return 255.0 * _frame / FADE_IN_FRAMES
	if remaining < FADE_OUT_FRAMES:
		return 255.0 * remaining / FADE_OUT_FRAMES
	return 255.0


func _draw_banner() -> void:
	var remaining := DURATION_FRAMES - _frame
	var alpha := _alpha255(remaining)
	var a := alpha / 255.0
	var rect := Rect2(0, 0, BANNER_W, BANNER_H)
	# Latar gelap + border entrance_color (paritas :2269-2274)
	_banner.draw_rect(rect, Color(10.0 / 255.0, 10.0 / 255.0, 18.0 / 255.0,
		210.0 / 255.0 * a), true)
	_banner.draw_rect(rect, Color(entrance_color.r, entrance_color.g,
		entrance_color.b, a), false, 2.0)
	# Sudut emas hanya setelah alpha > 60 (paritas :2277-2281)
	if alpha > 60.0:
		_corner_ticks(_banner, rect, Color(1.0, 0.863, 0.471, a), 12.0, 2.0, 5.0)
	# ── HP bar preview mengisi selama duration*0.85 (paritas :2300-2311) ──
	var hp_progress := minf(1.0, _frame / (DURATION_FRAMES * 0.85))
	var bar_w := 150.0
	var bar_h := 12.0
	var bx := BANNER_W - bar_w - 16.0
	var by := BANNER_H / 2.0 - bar_h / 2.0
	_banner.draw_rect(Rect2(bx, by, bar_w, bar_h), Color(0.157, 0.031, 0.047), true)
	var fill := bar_w * hp_progress
	if fill > 0.0:
		_banner.draw_rect(Rect2(bx, by, fill, bar_h), entrance_color, true)
	_banner.draw_rect(Rect2(bx, by, bar_w, bar_h), Color(1, 1, 1), false, 1.0)


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
#  SKIP / SELESAI (banner tidak pernah pause gameplay)
# ══════════════════════════════════════════════════════════

func cinematic_active() -> bool:
	return active


func skip_key(event: InputEventKey) -> bool:
	if not active:
		return false
	if event.keycode == KEY_SPACE or event.keycode == KEY_ESCAPE:
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
	queue_free()
