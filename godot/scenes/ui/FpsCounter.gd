# FpsCounter.gd — port _system.py:202-398 (blok `fps_counter.py`).
#
# Panel debug kecil yang DIHIDUPKAN/MATIKAN dengan F8, sama seperti
# `main_desktop_legacy.py:99/169/300` (pygame menanganinya SEBELUM dispatch
# state, jadi panelnya tampil di splash, menu, match, dan pause sekaligus).
# Kelasnya dipindah 1:1, termasuk angka-angka layoutnya.
#
# Semua geometri/warna/waktu tinggal di SATU fungsi murni `build_ops()` —
# `_draw()` hanya mengeksekusi daftar op. Kenapa: replay headless Godot tidak
# punya GPU, jadi tes tidak bisa men-screenshot panelnya; yang BISA dikunci
# adalah daftar perintah gambar yang DIHASILKAN kode, dan itu dibandingkan
# dengan jejak `pygame.draw.*`/`font.render`/`Surface.blit` sungguhan dari
# fixture `system_perf.json["fps"]["ops"]` (tools/test_system_perf_parity.py).
#
# Aturan yang dikunci (semuanya dari `FPSCounter` pygame):
#   * riwayat 120 sampel; yang ditampilkan = 30 sampel TERAKHIR; angka hanya
#     diperbarui setiap 10 frame (quirk pygame: panel membeku 10 frame);
#   * ambang warna 55 / 40 / 25 — tangga teks (100,255,100) / (255,255,100) /
#     (255,150,50) / (255,60,60) + status SMOOTH/OK/SLOW/LAG!, dan tangga BAR
#     yang lebih gelap (50,160,50) / (160,160,50) / (160,90,40) / (160,40,40);
#   * panel 200x95 di (10,45), radius 8, hitam alpha 200, tepi (60,70,90) 1px;
#   * angka size 40 di (12,6); "FPS" size 16 di 12+lebar+5 / y 22; status
#     size 15 rata kanan di (200-w-10, 10); "[F8] toggle" size 12 di
#     (200-w-8, 95-15); AVG/MIN/MAX size 14 di x 10/80/145, y 48, MIN memerah
#     di bawah 30; grafik 180x22 di (10,65) dengan garis 60 (60,80,60) dan
#     garis 30 (80,40,40) di `y = 65+22-int(22*min(n,80)/80)`; bar selebar
#     `max(1, 180//n)` dengan tinggi `int(22*min(f,80)/80)`.
#
# DEVIASI yang disengaja (mesin, bukan perilaku kelas):
#   1. `clock.get_fps()` -> `Engine.get_frames_per_second()` (keduanya rata-rata
#      window ±1 detik, bukan fps sesaat);
#   2. pygame memanggil `update()` DUA kali per frame karena blok
#      `main_desktop_legacy.py:455-456` diduplikasi di `:461-462` — di sana
#      riwayat terisi 2 sampel/frame sehingga jendela 30 sampel hanya menutupi
#      15 frame. Godot men-sampling sekali per frame. Yang dikunci adalah
#      aturan di KELAS (append / trim 120 / jendela 30 / tiap 10 frame),
#      bukan bug duplikasi di call site legacy;
#   3. posisi teks disimpan sebagai TOP-LEFT (semantik `blit` pygame);
#      `_draw()` menambahkan ascent karena `draw_string` memakai baseline.
#      Metrik font Godot tidak identik piksel-per-piksel dengan TTF pygame,
#      jadi `lebar teks` (dipakai untuk me-rata-kan "FPS" dan status) ikut
#      font engine — yang identik adalah aturan letaknya, bukan hasil raster;
#   4. `main.py` (entry HIDUP pygame) tidak memakai overlay ini — di sana
#      overlay debug milik `mobile/debug.py` dengan 4 mode (off/mini/full/
#      grafik) + tombol FPS di TouchHUD. Yang diport di sini adalah kelas
#      `_system.py` (jalur desktop legacy, satu-satunya konsumennya).
#      Tombol FPS 4-mode `mobile/debug.py` MASIH terbuka; lihat
#      docs/SYSTEM_PY_COVERAGE.md.
extends Control

## Geometri panel — paritas `base_x/base_y/panel_w/panel_h` (_system.py:259-266)
const PANEL_POS := Vector2(10, 45)
const PANEL_W := 200.0
const PANEL_H := 95.0
## Paritas `self.history_size = 120` + jendela tampil 30 + refresh tiap 10
const HISTORY_SIZE := 120
const DISPLAY_WINDOW := 30
const DISPLAY_EVERY := 10
## Paritas blok grafik (_system.py:366-375)
const GRAPH_X := 10.0
const GRAPH_Y := 65.0
const GRAPH_H := 22.0
const GRAPH_SCALE_MAX := 80.0
## Letak teks di DALAM panel — paritas tiap `panel_surf.blit(...)`
## (`_system.py:270-355`). Semua relatif terhadap sudut kiri-atas panel.
const FPS_AT := Vector2(12, 6)          # `blit(fps_surf, (12, 6))`
const LABEL_GAP := 5                    # 5px di belakang angka FPS
const LABEL_Y := 22
const STATUS_PAD := 10                  # `panel_w - w - 10`
const STATUS_Y := 10
const HINT_PAD := 8                     # `panel_w - w - 8`
const HINT_BOTTOM := 15                 # `panel_h - 15`
const STATS_Y := 48
const AVG_X := 10
const MIN_X := 80
const MAX_X := 145
const GRAPH_PAD := 20                   # `graph_w = panel_w - 20`
const MIN_WARN := 30.0                  # MIN memerah di bawah 30 fps
## Sudut membulat (pygame `border_radius`)
const PANEL_RADIUS := 8
const GRAPH_RADIUS := 3
## Ukuran font per elemen (`_system.py:271,286,296,307,330,341,352`)
const NUM_SIZE := 40
const LABEL_SIZE := 16
const STATUS_SIZE := 15
const STATS_SIZE := 14
const HINT_SIZE := 12
## Warna panel/grafik (pygame menulisnya 0..255; disimpan apa adanya supaya
## fixture bisa dibandingkan langsung)
const PANEL_BG: Array = [0, 0, 0]
const PANEL_BG_ALPHA := 200
const PANEL_BORDER: Array = [60, 70, 90, 255]
const GRAPH_BG: Array = [15, 20, 35]
const GRAPH_BORDER: Array = [50, 60, 80]
const GUIDE_60: Array = [60, 80, 60]
const GUIDE_30: Array = [80, 40, 40]
const LABEL_COLOR: Array = [160, 170, 190]
const HINT_COLOR: Array = [120, 130, 150]
const STAT_COLOR: Array = [180, 200, 220]
const STAT_MIN_COLOR: Array = [255, 130, 130]
## Tangga angka FPS + status (`_system.py:276-285`): ambang 55/40/25.
const COLOR_EXCELLENT: Array = [100, 255, 100]
const COLOR_GOOD: Array = [255, 255, 100]
const COLOR_FAIR: Array = [255, 150, 50]
const COLOR_POOR: Array = [255, 60, 60]
## Tangga warna BAR (`_system.py:382-389`) — versi LEBIH GELAP dari tangga di
## atas.pygame punya dua tangga berbeda untuk teks dan bar; keduanya dipertahankan.
const BAR_EXCELLENT: Array = [50, 160, 50]
const BAR_GOOD: Array = [160, 160, 50]
const BAR_FAIR: Array = [160, 90, 40]
const BAR_POOR: Array = [160, 40, 40]

var enabled: bool = false
var fps_history: Array = []
var frame_count: int = 0
var display_fps: float = 0.0
var display_avg: float = 0.0
var display_min: float = 0.0
var display_max: float = 0.0

var _panel_box: StyleBoxFlat = null
var _graph_box: StyleBoxFlat = null
var _font_body: Font = null


func _ready() -> void:
	position = PANEL_POS
	size = Vector2(PANEL_W, PANEL_H)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# pygame meng-update counter di LUAR dispatch state: pause/menu/splash
	# tetap menghitung frame.
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = enabled
	_panel_box = StyleBoxFlat.new()
	_panel_box.bg_color = Color(float(PANEL_BG[0]) / 255.0,
		float(PANEL_BG[1]) / 255.0, float(PANEL_BG[2]) / 255.0,
		float(PANEL_BG_ALPHA) / 255.0)
	_panel_box.set_border_width_all(1)
	_panel_box.border_color = _rgba(PANEL_BORDER)
	_panel_box.set_corner_radius_all(PANEL_RADIUS)
	_graph_box = StyleBoxFlat.new()
	_graph_box.bg_color = _rgb(GRAPH_BG)
	_graph_box.set_border_width_all(1)
	_graph_box.border_color = _rgb(GRAPH_BORDER)
	_graph_box.set_corner_radius_all(GRAPH_RADIUS)
	_font_body = UiTheme.body_regular()


## Paritas `FPSCounter.toggle()` — termasuk cetak `[FPS COUNTER] ON/OFF`.
func toggle() -> void:
	set_enabled(not enabled)


func set_enabled(value: bool) -> void:
	enabled = value
	visible = enabled
	print("[FPS COUNTER] %s" % ("ON" if enabled else "OFF"))
	if enabled:
		queue_redraw()


## Paritas `FPSCounter.update(clock)`: TIDAK memanggil `clock.tick()` sendiri
## (komentar pygame: "Panggil setiap frame dengan clock yang sudah ada"), jadi
## angka fps masuk sebagai argumen — itu yang membuat aturan riwayat bisa
## direplay harness tanpa Engine.
func update(current_fps: float) -> void:
	fps_history.append(current_fps)
	if fps_history.size() > HISTORY_SIZE:
		fps_history.pop_front()
	frame_count += 1
	if frame_count >= DISPLAY_EVERY:
		frame_count = 0
		if not fps_history.is_empty():
			var begin: int = maxi(0, fps_history.size() - DISPLAY_WINDOW)
			var recent: Array = fps_history.slice(begin)
			display_fps = float(recent[recent.size() - 1])
			var total := 0.0
			var lo := INF
			var hi := -INF
			for f in recent:
				var v := float(f)
				total += v
				lo = minf(lo, v)
				hi = maxf(hi, v)
			display_avg = total / float(recent.size())
			display_min = lo
			display_max = hi


func _process(_delta: float) -> void:
	# pygame memanggil update() TANPA melihat `enabled` (hanya draw yang
	# dicek), jadi riwayat tetap jalan saat panel mati dan panel menyala
	# dengan angka yang sudah hangat. Redraw hanya saat terlihat.
	update(Engine.get_frames_per_second())
	if enabled:
		queue_redraw()


# ══════════════════════════════════════════════════════════
#  TANGGA WARNA — dipisah dari render supaya bisa dikunci tes
# ══════════════════════════════════════════════════════════

## Paritas `_system.py:275-285`: ambang 55 / 40 / 25.
static func status_for(fps: float) -> String:
	if fps >= 55.0:
		return "SMOOTH"
	elif fps >= 40.0:
		return "OK"
	elif fps >= 25.0:
		return "SLOW"
	return "LAG!"


## Warna angka FPS + status (`_system.py:276-285`).
static func number_color_for(fps: float) -> Array:
	if fps >= 55.0:
		return COLOR_EXCELLENT
	elif fps >= 40.0:
		return COLOR_GOOD
	elif fps >= 25.0:
		return COLOR_FAIR
	return COLOR_POOR


## Warna bar grafik — tangga KEDUA yang lebih gelap (`_system.py:382-389`).
static func bar_color_for(fps: float) -> Array:
	if fps >= 55.0:
		return BAR_EXCELLENT
	elif fps >= 40.0:
		return BAR_GOOD
	elif fps >= 25.0:
		return BAR_FAIR
	return BAR_POOR


## Tinggi bar: `int(graph_h * min(f, 80) / 80)` (`_system.py:379`).
static func bar_height_for(fps: float) -> int:
	return int(GRAPH_H * minf(fps, GRAPH_SCALE_MAX) / GRAPH_SCALE_MAX)


static func _rgb(arr: Array) -> Color:
	return Color(float(arr[0]) / 255.0, float(arr[1]) / 255.0,
		float(arr[2]) / 255.0, 1.0)


static func _rgba(arr: Array) -> Color:
	var a := 255.0 if arr.size() < 4 else float(arr[3])
	return Color(float(arr[0]) / 255.0, float(arr[1]) / 255.0,
		float(arr[2]) / 255.0, a / 255.0)


## Daftar perintah gambar panel, sebagai fungsi MURNI dari state.
## `measurer` = Callable(text, size) -> lebar piksel; produksi memakai font
## Godot, harness mengirim pengukur palsu supaya op bisa dibandingkan dengan
## jejak pygame secara deterministik (fixture menyimpan lebar teks pygame).
static func build_ops(state: Dictionary, measurer: Callable) -> Array:
	var ops: Array = []
	var fps := float(state.get("display_fps", 0.0))
	var avg := float(state.get("display_avg", 0.0))
	var mn := float(state.get("display_min", 0.0))
	var mx := float(state.get("display_max", 0.0))
	var hist: Array = state.get("fps_history", [])
	var col := number_color_for(fps)
	# Panel: fill hitam alpha 200 + tepi 1px (dua rect pygame pada (0,0,200,95)
	# di dalam surface panel, lalu surface-nya di-blit ke (10,45)).
	ops.append({"op": "panel", "x": int(PANEL_POS.x), "y": int(PANEL_POS.y),
		"w": int(PANEL_W), "h": int(PANEL_H), "radius": PANEL_RADIUS,
		"bg": [PANEL_BG[0], PANEL_BG[1], PANEL_BG[2], PANEL_BG_ALPHA],
		"border": PANEL_BORDER.duplicate()})
	# Angka FPS (size 40) + label "FPS" (size 16) 5px di belakangnya.
	# `w` ikut disimpan supaya posisi yang bergantung lebar teks (label,
	# status, petunjuk) bisa dibandingkan dengan jejak render pygame — yang
	# direplay adalah ATTRURNYA, bukan raster font Godot.
	var num_text := "%d" % int(fps)
	var num_w := int(measurer.call(num_text, NUM_SIZE))
	ops.append(_text_op(num_text, NUM_SIZE, int(FPS_AT.x), int(FPS_AT.y), col,
		num_w))
	ops.append(_text_op("FPS", LABEL_SIZE, int(FPS_AT.x) + num_w + LABEL_GAP,
		LABEL_Y, LABEL_COLOR, int(measurer.call("FPS", LABEL_SIZE))))
	# Status rata kanan (panel_w - w - 10, 10)
	var status := status_for(fps)
	var st_w := int(measurer.call(status, STATUS_SIZE))
	ops.append(_text_op(status, STATUS_SIZE, int(PANEL_W) - st_w - STATUS_PAD,
		STATUS_Y, col, st_w))
	# Petunjuk tombol (panel_w - w - 8, panel_h - 15)
	var hint := "[F8] toggle"
	var hint_w := int(measurer.call(hint, HINT_SIZE))
	ops.append(_text_op(hint, HINT_SIZE, int(PANEL_W) - hint_w - HINT_PAD,
		int(PANEL_H) - HINT_BOTTOM, HINT_COLOR, hint_w))
	# Baris AVG/MIN/MAX (y 48; MIN memerah di bawah 30)
	ops.append(_text_op("AVG %d" % int(avg), STATS_SIZE, AVG_X, STATS_Y,
		STAT_COLOR, int(measurer.call("AVG %d" % int(avg), STATS_SIZE))))
	var min_text := "MIN %d" % int(mn)
	ops.append(_text_op(min_text, STATS_SIZE, MIN_X, STATS_Y,
		STAT_MIN_COLOR if mn < MIN_WARN else STAT_COLOR,
		int(measurer.call(min_text, STATS_SIZE))))
	ops.append(_text_op("MAX %d" % int(mx), STATS_SIZE, MAX_X, STATS_Y,
		STAT_COLOR, int(measurer.call("MAX %d" % int(mx), STATS_SIZE))))
	# Grafik: bg + tepi (radius 3), dua garis panduan, lalu bar
	var graph_w := int(PANEL_W) - GRAPH_PAD
	ops.append({"op": "graph", "x": int(GRAPH_X), "y": int(GRAPH_Y),
		"w": graph_w, "h": int(GRAPH_H), "bg": GRAPH_BG.duplicate(),
		"border": GRAPH_BORDER.duplicate(), "radius": GRAPH_RADIUS})
	var base_y: float = GRAPH_Y + GRAPH_H
	ops.append({"op": "line", "y1": int(base_y) - bar_height_for(60.0),
		"x1": int(GRAPH_X), "x2": int(GRAPH_X) + graph_w, "color": GUIDE_60.duplicate()})
	ops.append({"op": "line", "y1": int(base_y) - bar_height_for(30.0),
		"x1": int(GRAPH_X), "x2": int(GRAPH_X) + graph_w, "color": GUIDE_30.duplicate()})
	if hist.size() <= 1:
		return ops
	var num_bars: int = mini(hist.size(), graph_w)
	var bar_w: int = maxi(1, graph_w / num_bars)
	var start_idx: int = maxi(0, hist.size() - num_bars)
	for i in num_bars:
		var idx: int = start_idx + i
		if idx >= hist.size():
			break
		var f := float(hist[idx])
		var bh := bar_height_for(f)
		if bh <= 0:
			continue
		ops.append({"op": "bar", "x": int(GRAPH_X) + i * bar_w,
			"y": int(base_y) - bh, "w": maxi(1, bar_w - 1), "h": bh,
			"color": bar_color_for(f)})
	return ops


func _default_measurer() -> Callable:
	var font: Font = _font_body if _font_body != null else ThemeDB.fallback_font
	return func(text: String, size: int) -> float:
		if font == null:
			return float(text.length()) * float(size) * 0.5
		return font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			size).x


func _draw() -> void:
	if not enabled:
		return
	var font: Font = _font_body if _font_body != null else ThemeDB.fallback_font
	if _panel_box != null:
		draw_style_box(_panel_box, Rect2(Vector2.ZERO, Vector2(PANEL_W, PANEL_H)))
	var ops: Array = build_ops({
		"display_fps": display_fps, "display_avg": display_avg,
		"display_min": display_min, "display_max": display_max,
		"fps_history": fps_history,
	}, _default_measurer())
	# Op "panel"/"graph" sudah digambar sebagai stylebox di atas (radius +
	# garis tepi 1px = padanan `border_radius` pygame); sisanya dieksekusi.
	# Semua koordinat op RELATIF TERHADAP PANEL — node ini sendiri sudah
	# dipasang di PANEL_POS, jadi tidak ada offset lagi di sini.
	for entry in ops:
		var op: Dictionary = entry
		var kind := str(op["op"])
		if kind == "text":
			# posisi op = TOP-LEFT (semantik blit pygame); draw_string memakai
			# baseline, jadi ascent ditambahkan (deviasi #3).
			_text(font, int(op["size"]), Vector2(float(op["x"]), float(op["y"])),
				str(op["text"]), _rgba(op["color"] as Array))
		elif kind == "line":
			var ly := float(op["y1"])
			draw_line(Vector2(float(op["x1"]), ly), Vector2(float(op["x2"]), ly),
				_rgb(op["color"] as Array), 1.0)
		elif kind == "bar":
			draw_rect(Rect2(Vector2(float(op["x"]), float(op["y"])),
				Vector2(float(op["w"]), float(op["h"]))),
				_rgb(op["color"] as Array), true)


static func _text_op(text: String, size: int, x: int, y: int,
		color: Array, w: int) -> Dictionary:
	return {"op": "text", "text": text, "size": size, "x": x, "y": y,
		"color": color, "w": w}


## pygame me-blit surface teks di TOP-LEFT; draw_string memakai BASELINE.
func _text(font: Font, size: int, at: Vector2, text: String,
		color: Color) -> void:
	if font == null:
		return
	draw_string(font, at + Vector2(0.0, font.get_ascent(size)), text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
