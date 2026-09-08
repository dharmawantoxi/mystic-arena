# AchievementPopup.gd — port _render.AchievementPopup pygame (FASE 13).
#
# Popup notifikasi achievement DI MAP (layar arena, kanan atas di bawah
# combo counter — paritas EffectManager.draw_ui yang memanggil
# achievement.draw(surface, screen_w, screen_h)).
#
# State machine + kurva slide = 1:1 pygame dan dikunci MatchScoringParityTest
# vs fixture match_scoring.achievement:
#   • unlock(title, desc, icon) -> antri (queue),
#   • tick() = SATU frame pygame: countdown 180 frame (3 detik), lalu
#     popup berikutnya dari antrean langsung menggantikan di frame yang
#     sama (paritas AchievementPopup.update),
#   • slide: masuk dari kanan 300px ease-out-back (fase < 0.15), tahan,
#     keluar linear (fase >= 0.85) — kurva 181 titik direplay.
#
# KOMPOSIT PIKSEL (gradien, border emas + sudut, ikon bintang/pedang/
# tengkorak, glow) adalah aproksimasi draw Godot — TIDAK diaudit piksel;
# posisi/ukuran/teks/warna kanonnya dari HudLayout.
extends Control

const FPS_STEP := 1.0 / 60.0

## Antrean popup: [{"title": String, "description": String, "icon": String}].
var queue: Array = []
## Popup yang sedang tampil (Dictionary) atau null — paritas ap.current.
var current = null
## Sisa frame popup aktif (180 -> 0).
var timer: int = 0

var _accum: float = 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func _process(delta: float) -> void:
	_accum += delta
	while _accum >= FPS_STEP:
		_accum -= FPS_STEP
		tick()


## Paritas AchievementPopup.unlock — antri popup baru.
func unlock(title: String, description: String, icon: String = "star") -> void:
	queue.append({
		"title": title,
		"description": description,
		"icon": icon,
	})


## Paritas AchievementPopup.update — SATU frame pygame (@60fps).
func tick() -> void:
	var changed := false
	# Countdown current (slide/alpha animasi bergerak tiap frame aktif)
	if current != null:
		timer -= 1
		if timer <= 0:
			current = null
		changed = true

	# Show next in queue (frame yang sama saat yang lama habis)
	if current == null and not queue.is_empty():
		current = queue.pop_front()
		timer = HudLayout.ACHIEVEMENT_FRAMES
		changed = true
	if changed:
		queue_redraw()


func _draw() -> void:
	if current == null:
		return
	var rect := HudLayout.achievement_panel_rect(timer)
	var alpha := HudLayout.achievement_alpha(timer)

	# Panel gelap + border emas (aproximasi piksel; geometri kanon).
	draw_rect(rect, Color(0.07, 0.07, 0.11, 0.92 * alpha))
	draw_rect(rect, Color(1.0, 0.86, 0.2, alpha), false, 3.0)

	# Header letterspaced + judul + deskripsi (posisi/teks/warna kanon).
	var font := ThemeDB.fallback_font
	var header_color := Color(HudLayout.ACHIEVEMENT_HEADER_COLOR, alpha)
	var title_color := Color(HudLayout.ACHIEVEMENT_TITLE_COLOR, alpha)
	var desc_color := Color(HudLayout.ACHIEVEMENT_DESC_COLOR, alpha)
	var origin := rect.position + HudLayout.ACHIEVEMENT_TEXT_HEADER
	draw_string(font, origin, HudLayout.letter("ACHIEVEMENT"),
		HORIZONTAL_ALIGNMENT_LEFT, -1, 13, header_color)
	draw_string(font, rect.position + HudLayout.ACHIEVEMENT_TEXT_TITLE,
		str(current["title"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, title_color)
	draw_string(font, rect.position + HudLayout.ACHIEVEMENT_TEXT_DESC,
		str(current["description"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
		desc_color)

	# Ikon lingkaran emas di kiri (aproximasi _draw_icon pygame).
	var icon_c := rect.position + HudLayout.ACHIEVEMENT_ICON_POS
	draw_circle(icon_c, 16.0, Color(0.24, 0.16, 0.04, alpha))
	draw_arc(icon_c, 16.0, 0.0, TAU, 24, Color(1.0, 0.86, 0.2, alpha), 2.0)
	match str(current["icon"]):
		"star":
			_draw_star(icon_c, 8.0, Color(1.0, 0.86, 0.2, alpha))
		"sword":
			draw_line(icon_c + Vector2(0, -9), icon_c + Vector2(0, 7),
				Color(0.85, 0.85, 0.95, alpha), 3.0)
			draw_line(icon_c + Vector2(-5, 4), icon_c + Vector2(5, 4),
				Color(0.5, 0.3, 0.15, alpha), 3.0)
		"skull":
			draw_circle(icon_c + Vector2(0, -2), 6.5,
				Color(0.95, 0.95, 0.9, alpha))
			draw_rect(Rect2(icon_c + Vector2(-4, 3), Vector2(8, 5)),
				Color(0.95, 0.95, 0.9, alpha))
		_:
			draw_circle(icon_c, 6.0, Color(1.0, 0.86, 0.2, alpha))


func _draw_star(c: Vector2, r: float, color: Color) -> void:
	var pts := PackedVector2Array()
	for i in 10:
		var angle := i * PI / 5.0 - PI / 2.0
		var rad := r if i % 2 == 0 else r * 0.5
		pts.append(c + Vector2(cos(angle), sin(angle)) * rad)
	draw_colored_polygon(pts, color)
