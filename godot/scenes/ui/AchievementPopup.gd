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
	# Main mewarisi ALWAYS untuk input; efek gameplay harus tetap beku
	# selama pause/intro/kematian boss (EffectManager.update pygame).
	process_mode = Node.PROCESS_MODE_PAUSABLE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func _process(delta: float) -> void:
	_accum += delta
	while _accum >= FPS_STEP:
		_accum -= FPS_STEP
		tick()


func reset() -> void:
	queue.clear()
	current = null
	timer = 0
	_accum = 0.0
	queue_redraw()


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

	# Panel gradasi + border emas + sudut (geometri kanon HudLayout).
	var top := Color(0.10, 0.11, 0.17, 0.95 * alpha)
	var bot := Color(0.05, 0.05, 0.09, 0.95 * alpha)
	UiTheme.draw_vgrad(self, rect, top, bot, 10.0)
	draw_style_box(UiTheme.border_style(
		Color(1.0, 0.86, 0.2, alpha), 2.0, 10.0), rect)
	UiTheme.corner_ticks(self, rect, Color(1.0, 0.91, 0.61, alpha), 9.0,
		2.0, 2.0)

	# Header letterspaced + judul + deskripsi (posisi/teks/warna kanon).
	var header_c := Color(HudLayout.ACHIEVEMENT_HEADER_COLOR, alpha)
	var title_c := Color(HudLayout.ACHIEVEMENT_TITLE_COLOR, alpha)
	var desc_c := Color(HudLayout.ACHIEVEMENT_DESC_COLOR, alpha)
	var origin := rect.position + HudLayout.ACHIEVEMENT_TEXT_HEADER
	var fh := UiTheme.font("body_semibold")
	UiTheme.draw_text_shadow(self, fh, HudLayout.letter("ACHIEVEMENT"), 13,
		header_c, origin, Color(0, 0, 0, 0.8 * alpha))
	var ft := UiTheme.font("body_bold")
	UiTheme.draw_text_shadow(self, ft, str(current["title"]), 17, title_c,
		rect.position + HudLayout.ACHIEVEMENT_TEXT_TITLE,
		Color(0, 0, 0, 0.8 * alpha))
	var fd := UiTheme.font("body")
	draw_string(fd, rect.position + HudLayout.ACHIEVEMENT_TEXT_DESC,
		str(current["description"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
		desc_c)

	# Ikon lingkaran emas di kiri (ikon vektor ui_theme pygame).
	var icon_c := rect.position + HudLayout.ACHIEVEMENT_ICON_POS
	draw_circle(icon_c, 16.0, Color(0.24, 0.16, 0.04, alpha))
	draw_arc(icon_c, 16.0, 0.0, TAU, 24, Color(1.0, 0.86, 0.2, alpha), 2.0)
	var icon_name := str(current["icon"])
	if icon_name == "sword":
		icon_name = "swords"
	elif icon_name != "star" and icon_name != "skull" \
			and icon_name != "shield" and icon_name != "coin":
		icon_name = "star"
	UiTheme.draw_icon(self, icon_name, icon_c,
		Color(1.0, 0.86, 0.2, alpha), 0.9)


func _draw_star(c: Vector2, r: float, color: Color) -> void:
	var pts := PackedVector2Array()
	for i in 10:
		var angle := i * PI / 5.0 - PI / 2.0
		var rad := r if i % 2 == 0 else r * 0.5
		pts.append(c + Vector2(cos(angle), sin(angle)) * rad)
	draw_colored_polygon(pts, color)
