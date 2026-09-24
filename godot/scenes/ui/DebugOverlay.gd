# DebugOverlay.gd — port `mobile/debug.py` (DebugOverlay) 1:1: 4 mode.
#
# Overlay debug on-device. Cara pakai (paritas header debug.py:5-12):
#   * tombol "FPS" di TouchHUD mengsiklus mode:
#       OFF -> RINGKAS (mini) -> LENGKAP (full) -> GRAFIK -> OFF;
#   * TAHAN tombol jeda >= 450 ms = siklus yang sama + getar 30 ms
#     (padanan main.py:407-413 — long-press dari TouchGestures.gd);
#   * F8 memakai MESIN YANG SAMA. Sebelumnya F8 membuka `FpsCounter`
#     (panel `_system.py`, jalur desktop LEGACY pygame) dan tombol FPS membuka
#     info-baris HUD; `main.py` (entry HIDUP) hanya kenal DebugOverlay 4 mode.
#     Panel FpsCounter tetap ada + bisa dipanggil (tests/SystemPerfParityTest
#     menguncinya), tapi bukan lagi target tombol FPS;
#   * baris `[PERF]` tiap 5 detik masuk ke stdout -> logcat di Android.
#
# Aturan debug.py yang dibawa apa adanya:
#   * riwayat 180 sampel fps + frame-ms (`deque(maxlen=180)`);
#   * peak ms + penghitung frame lambat (`frame_ms > 33`);
#   * log console tiap `log_interval` (5,0 dtk) dengan format
#     `[PERF] fps=... frame=...ms upd=... draw=... q=... ent=... mem=...`;
#   * mini: `"%3.0f FPS  %4.1fms"` di (safe.left+6, safe.top+6), kotak panel
#     = posisi teks digeser (-4,-3) lalu dibesarkan (+12,+8), teks final di
#     (x+2, y+1) — geseran yang sama, dua kali dipakai;
#   * lengkap: buffer OPAQUE (8,8,14) + tepi (90,90,120) 1px di
#     (safe.left+4, safe.top+4); lebar = teks terlebar + 18, tinggi = jumlah
#     baris * 19 + 12; teks baris i di (8, 6 + i*19);
#   * ISI teks baris lengkap diperbarui maksimal 4x/detik
#     (`JEDA_SEGAR_MS = 250`) — aturan "alat ukur tidak boleh mengganggu yang
#     diukur" (debug.py:228-241);
#   * grafik: 240x70 di (safe.left+4, safe.top+145), garis panduan 16,7 ms +
#     33,3 ms dan poly-line pada `y = at.y + h - int(min(ms,50)/50*h)`;
#   * MODE_GRAFIK = LENGKAP + grafik (bukan mode terpisah), persis `draw()`;
#   * lingkaran jari: cincin (90,220,255) r=26 tebal 2 + titik putih r=3
#     untuk tiap titik aktif (`_draw_touch`).
#
# DEVIASI yang disengaja (sumber datanya milik pygame, bukan perilakunya):
#   1. Baris "konversi sprite", "fastblit + cache HERO/BOSS", "memori cache",
#      "font cache" serta blok `blitwatch` / `perf.PHASES` TIDAK dirender:
#      tidak ada pemotong sprite SDL, cache blit, maupun font cache di Godot
#      (bake PNG + GPU). Baris "memori" dan "mem …" digabung menjadi satu
#      `mem <RSS>`; urutan baris yang tersisa dipertahankan.
#   2. `hemat:` dibaca dari `UiTheme.cheap_alpha()` yang di Godot selalu true
#      (komposisi alpha di GPU) -> baris entity tampil `hemat:off` + warna
#      KUNING, persis pygame di perangkat yang blit-alpha-nya murah. `sprite:`
#      = true (bake PNG = cache permanen, selalu hit).
#   3. `_memory_str` pygame membaca `/proc/self/statm` x page size; Godot
#      membaca `VmRSS` dari `/proc/self/status` (kB, tidak perlu page size).
#   4. `_build_label()` pygame mengimpor `mobile/buildinfo.py`, yang tidak
#      ikut ke ekspor Godot -> stamp diambil dari `application/config/version`
#      (CI menambalnya dari tag vX.Y.Z); tanpa itu "BUILD ?" = persis cabang
#      `except` di `_build_label`.
#   5. `update(fps, frame_ms)` menerima angka, bukan sebuah `clock`: Godot
#      tidak punya `pygame.time.Clock`, dan frame-ms WAJIB jam nyata
#      (`Time.get_ticks_usec`) karena `Engine.time_scale` 0,5/2,0 (game speed)
#      menskalakan `delta` — angka akan bohong kalau delta yang dipakai.
#      `clock.get_fps()` padanannya `Engine.get_frames_per_second()`.
#   6. Fase `event|update|draw|flip` memakai port `perf.FrameTimer`
#      (`_FrameTimer` di bawah; smoothing 0,9 + `report()` rata-rata per
#      fase). Fase tanpa batas nyata di Godot tetap 0,0 — persis perilaku
#      `t.get("fase", 0)` pygame untuk fase yang belum pernah di-mark.
#
# Semua geometri/warna/teks dibangun fungsi murni `build_ops()` /
# `build_lines()` supaya bisa direplay headless tanpa GPU (pola
# `FpsCounter.gd`). `measure` = Callable(text, size) -> Vector2(lebar,
# tinggi) — padanan `font.size()` pygame yang mengembalikan DUA angka.
extends Control
class_name DebugOverlay

signal mode_changed(mode: int)

## ── mode (debug.py:22-23) ──
const MODE_OFF := 0
const MODE_MINI := 1
const MODE_FULL := 2
const MODE_GRAPH := 3
## debug.py:23 `_MODE_NAMES` — dipakai pesan toggle.
const MODE_NAMES := ["off", "mini", "full", "graph"]

## ── palet (debug.py:26-30 + literal di badan fungsi) ──
## 0..255 supaya fixture dibandingkan langsung (konvensi `FpsCounter.gd`).
const BG: Array = [0, 0, 0, 170]
const OK: Array = [120, 235, 140]
const WARN: Array = [255, 205, 90]
const BAD: Array = [255, 110, 110]
const TXT: Array = [225, 228, 240]
const PANEL_BORDER: Array = [90, 90, 120]
## Isi buffer opaque `_render_lines` + cabang mahal `_panel`.
const PANEL_FILL: Array = [8, 8, 14]
const MEM_COLOR: Array = [190, 190, 220]
const BUILD_COLOR: Array = [140, 230, 160]
const DEVICE_COLOR: Array = [150, 170, 210]
const EXTRA_COLOR: Array = [200, 190, 140]
const AUDIO_COLOR: Array = [200, 180, 230]
const TOUCH_RING: Array = [90, 220, 255]
const TOUCH_DOT: Array = [255, 255, 255]
const GRAPH_LINE: Array = [150, 220, 255]
const GUIDE_FAST: Array = [70, 120, 70]
const GUIDE_SLOW: Array = [120, 80, 60]

## ── geometri ──
const MINI_FONT := 20
const FULL_FONT := 16
## debug.py:243 `JEDA_SEGAR_MS = 250` — seegar teks baris lengkap (ms).
const JEDA_SEGAR_MS := 250.0
## debug.py:52 `log_interval=5.0` (detik).
const LOG_INTERVAL_SEC := 5.0
## debug.py:53-54 `deque(maxlen=180)`.
const HISTORY_MAX := 180
## debug.py:87 `if frame_ms > 33: _slow_frames += 1`.
const SLOW_MS := 33.0
## debug.py:204-213 (mini).
const MINI_AT := Vector2(6, 6)
const MINI_PANEL_POS_OFF := Vector2(-4, -3)
const MINI_PANEL_SIZE_OFF := Vector2(12, 8)
const MINI_TEXT_INNER_OFF := Vector2(2, 1)
## debug.py:343 `x, y = safe.left + 4, safe.top + 4`.
const FULL_AT := Vector2(4, 4)
## debug.py:341-342 `w = max(lebar) + 18`; `h = len(lines) * 19 + 12`.
const FULL_PAD_W := 18.0
const FULL_LINE_PITCH := 19.0
const FULL_PAD_H := 12.0
## debug.py:355 `buf.blit(font.render(...), (8, 6 + idx * 19))`.
const FULL_TEXT_AT := Vector2(8, 6)
## debug.py:361-365 `w, h = 240, 70`; `y = safe.top + 145`.
const GRAPH_SIZE := Vector2(240, 70)
const GRAPH_AT := Vector2(4, 145)
## debug.py:368 `min(ms, 50) / 50.0 * h`.
const GRAPH_MS_MAX := 50.0
const GUIDE_FAST_MS := 16.7
const GUIDE_SLOW_MS := 33.3
## debug.py:371 `data = list(self.frame_ms_history)[-w:]`.
const GRAPH_WINDOW := 240
## debug.py:437-443 `_draw_touch`.
const TOUCH_RING_R := 26.0
const TOUCH_RING_W := 2.0
const TOUCH_DOT_R := 3.0

## ── state (paritas DebugOverlay.__init__) ──
var mode: int = MODE_OFF
var fps_history: Array = []
var frame_ms_history: Array = []
## debug.py:60 `self.extra` — baris tambahan `"k: v"` di ujung panel.
var extra: Dictionary = {}
var log_to_console: bool = true
var log_interval: float = LOG_INTERVAL_SEC
## debug.py:58 `self.device = plat.get_device_info()`.
var device: Dictionary = {}
var _peak_ms: float = 0.0
var _slow_frames: int = 0
var _frames: int = 0
var _last_log_ms: float = 0.0
var _lines_cache: Array = []
var _lines_at: float = 0.0
var _have_lines: bool = false
var _timer: _FrameTimer = null
var _last_frame_us: int = -1
## Sumber lingkaran jari + biaya fase event (diset Main.gd).
var _gestures: Node = null


func _ready() -> void:
	name = "DebugOverlay"
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	MobileLayout.fill_parent(self)
	_timer = _FrameTimer.new()
	device = device_info()
	if not MobileLayout.is_connected("layout_changed", _on_layout_changed):
		MobileLayout.layout_changed.connect(_on_layout_changed)


func _on_layout_changed() -> void:
	if is_enabled(mode):
		queue_redraw()


## Padanan `platform_utils.get_device_info()` (debug.py membaca 5 kolom).
static func device_info() -> Dictionary:
	var engine := str(Engine.get_version_info().get("string", "?"))
	var model := OS.get_model_name()
	if model.is_empty():
		model = OS.get_processor_name()
	var android := OS.get_name().to_lower() == "android"
	return {
		"platform": OS.get_name().to_lower(),
		"model": model,
		# padanan persis platform_utils.get_device_info(): kolom Android
		# terisi HANYA di Android, "-" di mesin lain.
		"android_release": (OS.get_version_alias()
			if android else "-"),
		# `ro.build.version.sdk` hanya terbaca lewat JNI/plugin; TIDAK
		# ditebak -> "-" (kolom tetap tampil, isinya tidak diarang).
		"api_level": "-",
		"godot": engine,
		"sdl": DisplayServer.get_name(),
	}


# ══════════════════════════════════════════════════════════
#  ATURAN MURNI — direplay tes tanpa engine
# ══════════════════════════════════════════════════════════

static func mode_names() -> Array:
	return MODE_NAMES.duplicate()


## debug.py:66-69 `toggle`: `self.mode = (self.mode + 1) % 4`.
static func next_mode(m: int) -> int:
	return (m + 1) % 4


## debug.py:71-72 `set_mode`: `self.mode = mode % 4`. `posmod` = `%` Python
## (hasil selalu non-negatif, jadi mode -1 pun jatuh ke 3).
static func wrap_mode(m: int) -> int:
	return posmod(m, 4)


## debug.py:74-76 `enabled`: `mode != MODE_OFF`.
static func is_enabled(m: int) -> bool:
	return m != MODE_OFF


## debug.py:39-45 `_color_for_fps`: >= 50 OK, >= 30 WARN, selain itu BAD.
static func color_for_fps(fps: float) -> Array:
	if fps >= 50.0:
		return OK
	if fps >= 30.0:
		return WARN
	return BAD


## debug.py:87 ambang frame lambat.
static func slow_frame(frame_ms: float) -> bool:
	return frame_ms > SLOW_MS


## debug.py:205 `"%3.0f FPS  %4.1fms"`.
static func mini_text(fps: float, avg_frame_ms: float) -> String:
	return "%3.0f FPS  %4.1fms" % [fps, avg_frame_ms]


## debug.py:184-190 `_entity_counts` — `"m%d/t%d/h%d/p%d"`.
static func entity_counts(minions: int, towers: int, heroes: int,
		projectiles: int) -> String:
	return "m%d/t%d/h%d/p%d" % [minions, towers, heroes, projectiles]


## debug.py:95-102 `_log_line`.
static func perf_log_line(fps: float, avg_frame_ms: float, upd_ms: float,
		draw_ms: float, quality: String, counts: String,
		memory: String) -> String:
	return ("[PERF] fps=%.1f frame=%.1fms upd=%.1f draw=%.1f q=%s ent=%s "
			+ "mem=%s") % [fps, avg_frame_ms, upd_ms, draw_ms, quality,
				counts, memory]


## debug.py:104-107 `_avg(seq)` — rata-rata riwayat, 0.0 kalau kosong.
static func avg(values: Array) -> float:
	if values.is_empty():
		return 0.0
	var total := 0.0
	for v in values:
		total += float(v)
	return total / float(values.size())


## debug.py:113-118 `_memory_str` (deviasi #3 untuk sumbernya).
static func memory_str() -> String:
	var f := FileAccess.open("/proc/self/status", FileAccess.READ)
	if f == null:
		return "n/a"
	var text := f.get_as_text()
	f.close()
	for line in text.split("\n"):
		var s := str(line)
		if not s.begins_with("VmRSS:"):
			continue
		for part in s.replace(":", " ").split(" ", false):
			if part.is_valid_int():
				return "%.0fMB" % (float(int(part)) / 1024.0)
		break
	return "n/a"


## debug.py:33-36 `_build_label` (deviasi #4).
static func build_label() -> String:
	var v := str(ProjectSettings.get_setting("application/config/version",
		""))
	if v == "":
		return "BUILD ?"
	return "BUILD %s" % v


## debug.py:285-287 baris perangkat. pygame memformat SATU string saja —
## bagian "Android ..." ikut tercetak di desktop juga — jadi port ini tidak
## bercabang per platform: yang berbeda hanyalah ISI kolomnya.
static func device_text(info: Dictionary) -> String:
	return "%s | Android %s (API %s) | Godot %s / %s" % [
		str(info.get("model", "-")),
		str(info.get("android_release", "-")),
		str(info.get("api_level", "-")),
		str(info.get("godot", "-")),
		str(info.get("sdl", "-"))]


## debug.py:253-257 baris 1: fps + frame + peak.
static func line_perf(fps: float, avg_frame_ms: float,
		peak_ms: float) -> String:
	return "%3.0f FPS   frame %4.1f ms   peak %4.1f ms" % [fps, avg_frame_ms,
		peak_ms]


## debug.py:258-261 baris 2: fase frame.
static func line_phases(t: Dictionary) -> String:
	return "event %4.1f | update %4.1f | draw %4.1f | flip %4.1f ms" % [
		float(t.get("event", 0.0)), float(t.get("update", 0.0)),
		float(t.get("draw", 0.0)), float(t.get("flip", 0.0))]


## debug.py:262-267 baris 3: entity + quality + hemat + sprite + slow.
static func line_entity(counts: String, quality: String, cheap: bool,
		sprite_cache: bool, slow_frames: int, frames: int) -> String:
	return "entity %s  quality %s  hemat:%s  sprite:%s  slow %d/%d" % [
		counts, quality, "ON" if not cheap else "off",
		"ON" if sprite_cache else "off", slow_frames, frames]


## debug.py:276-278 baris "mem" (gabungan baris 6 + 9, deviasi #1).
static func line_memory(memory: String) -> String:
	return "mem %s" % memory


## mobile/combat_audio.ringkas() — baris audio tempur.
static func line_audio(main: int, tolak_jeda: int, tolak_anggaran: int,
		tolak_channel: int) -> String:
	return ("suara: main %d  ditolak %d (jeda %d / anggaran %d / kanal %d)"
		% [main, tolak_jeda + tolak_anggaran + tolak_channel, tolak_jeda,
			tolak_anggaran, tolak_channel])


## debug.py:252-296 `_build_lines`, dibatasi baris yang punya sumber data di
## Godot (deviasi #1). `s` = snapshot state (lihat `state_snapshot()`).
static func build_lines(s: Dictionary) -> Array:
	var fps := float(s.get("fps", 0.0))
	var cheap := bool(s.get("cheap_alpha", true))
	var lines: Array = []
	lines.append([line_perf(fps, float(s.get("frame_avg", 0.0)),
		float(s.get("peak", 0.0))), color_for_fps(fps)])
	lines.append([line_phases(s.get("phases", {}) as Dictionary), TXT])
	lines.append([line_entity(str(s.get("entities", "-")),
		str(s.get("quality", "high")), cheap,
		bool(s.get("sprite_cache", true)), int(s.get("slow_frames", 0)),
		int(s.get("frames", 0))), OK if not cheap else WARN])
	# debug.py:273 baris 7 SELALU ada (cabang except pun mengembalikan
	# string "suara: -"), jadi tidak ada kondisi di sini.
	lines.append([str(s.get("audio", line_audio(0, 0, 0, 0))), AUDIO_COLOR])
	lines.append([line_memory(str(s.get("memory", "n/a"))), MEM_COLOR])
	lines.append([str(s.get("build", "BUILD ?")), BUILD_COLOR])
	lines.append([device_text(s.get("device", {}) as Dictionary),
		DEVICE_COLOR])
	var ex: Dictionary = s.get("extra", {}) as Dictionary
	for key in ex:
		lines.append(["%s: %s" % [str(key), str(ex[key])], EXTRA_COLOR])
	return lines


## debug.py:341-343 ukuran panel LENGKAP dari barisnya.
static func full_panel_size(lines: Array, measure: Callable) -> Vector2:
	var widest := 0.0
	for entry in lines:
		var line: Array = entry
		var wh: Vector2 = measure.call(str(line[0]), FULL_FONT)
		widest = maxf(widest, wh.x)
	return Vector2(widest + FULL_PAD_W,
		float(lines.size()) * FULL_LINE_PITCH + FULL_PAD_H)


## debug.py:368 + :375 `y + h - int(min(ms, 50) / 50.0 * h)`.
static func graph_y(at_y: float, h: float, ms: float) -> int:
	return int(at_y) + int(h) - int(minf(ms, GRAPH_MS_MAX) / GRAPH_MS_MAX * h)


## debug.py:370-377 titik poly-line grafik.
static func graph_points(at: Vector2, size: Vector2, history: Array) -> Array:
	var pts: Array = []
	var first: int = maxi(0, history.size() - GRAPH_WINDOW)
	var data: Array = history.slice(first)
	if data.size() <= 1:
		return pts
	var step := size.x / float(maxi(1, data.size() - 1))
	for i in data.size():
		pts.append(Vector2(at.x + float(i) * step,
			float(graph_y(at.y, size.y, float(data[i])))))
	return pts


## debug.py:361-377 panel grafik + garis panduan + poly-line.
static func graph_ops(safe: Rect2, s: Dictionary) -> Array:
	var ops: Array = []
	var at := Vector2(safe.position.x + GRAPH_AT.x,
		safe.position.y + GRAPH_AT.y)
	ops.append({"op": "panel_alpha", "rect": Rect2(at, GRAPH_SIZE),
		"bg": BG.duplicate(), "border": PANEL_BORDER.duplicate()})
	for guide in [[GUIDE_FAST_MS, GUIDE_FAST], [GUIDE_SLOW_MS, GUIDE_SLOW]]:
		var gy := float(graph_y(at.y, GRAPH_SIZE.y, float(guide[0])))
		ops.append({"op": "line", "x1": at.x, "y1": gy,
			"x2": at.x + GRAPH_SIZE.x, "y2": gy,
			"color": (guide[1] as Array).duplicate()})
	var pts: Array = graph_points(at, GRAPH_SIZE,
		s.get("frame_ms_history", []) as Array)
	if pts.size() > 1:
		ops.append({"op": "poly", "points": pts,
			"color": GRAPH_LINE.duplicate(), "width": 1.0})
	return ops


## debug.py:437-443 `_draw_touch`: tiap titik jari = cincin + titik pusat.
static func touch_ops(points: Array) -> Array:
	var ops: Array = []
	for entry in points:
		var pos := entry as Vector2
		ops.append({"op": "circle", "at": pos, "r": TOUCH_RING_R,
			"color": TOUCH_RING.duplicate(), "filled": false,
			"width": TOUCH_RING_W})
		ops.append({"op": "circle", "at": pos, "r": TOUCH_DOT_R,
			"color": TOUCH_DOT.duplicate(), "filled": true, "width": 1.0})
	return ops


## SATU-SATUNYA pembangun op. `lines` boleh dari luar (jalur cache 250 ms di
## `_draw`); kalau absen, dibangun dari state — persis `_build_lines`.
static func build_ops(s: Dictionary, lines: Array,
		measure: Callable) -> Array:
	var ops: Array = []
	var m := int(s.get("mode", MODE_OFF))
	if not is_enabled(m):
		return ops
	var safe: Rect2 = s.get("safe", Rect2(0, 0, 1280, 720))
	if m == MODE_MINI:
		var fps := float(s.get("fps", 0.0))
		var text := mini_text(fps, float(s.get("frame_avg", 0.0)))
		var wh: Vector2 = measure.call(text, MINI_FONT)
		var at := Vector2(safe.position.x + MINI_AT.x,
			safe.position.y + MINI_AT.y)
		ops.append({"op": "panel_alpha",
			"rect": Rect2(at + MINI_PANEL_POS_OFF,
				Vector2(wh.x + MINI_PANEL_SIZE_OFF.x,
					wh.y + MINI_PANEL_SIZE_OFF.y)),
			"bg": BG.duplicate(), "border": PANEL_BORDER.duplicate()})
		ops.append({"op": "text", "text": text, "size": MINI_FONT,
			"weight": "body_bold",
			"x": int(at.x + MINI_TEXT_INNER_OFF.x),
			"y": int(at.y + MINI_TEXT_INNER_OFF.y),
			"color": color_for_fps(fps), "w": int(wh.x)})
	else:
		var rows := lines
		if rows.is_empty():
			rows = build_lines(s)
		var at2 := Vector2(safe.position.x + FULL_AT.x,
			safe.position.y + FULL_AT.y)
		ops.append({"op": "panel_opaque", "rect": Rect2(at2,
			full_panel_size(rows, measure)),
			"bg": PANEL_FILL.duplicate(),
			"border": PANEL_BORDER.duplicate()})
		for i in rows.size():
			var line: Array = rows[i]
			ops.append({"op": "text", "text": str(line[0]),
				"size": FULL_FONT, "weight": "body",
				"x": int(at2.x + FULL_TEXT_AT.x),
				"y": int(at2.y + FULL_TEXT_AT.y) + i * int(FULL_LINE_PITCH),
				"color": line[1] as Array})
		if m == MODE_GRAPH:
			ops.append_array(graph_ops(safe, s))
	ops.append_array(touch_ops(s.get("points", []) as Array))
	return ops


static func _rgb(arr: Array) -> Color:
	return Color(float(arr[0]) / 255.0, float(arr[1]) / 255.0,
		float(arr[2]) / 255.0, 1.0)


static func _rgba(arr: Array) -> Color:
	var a := 255.0 if arr.size() < 4 else float(arr[3])
	return Color(float(arr[0]) / 255.0, float(arr[1]) / 255.0,
		float(arr[2]) / 255.0, a / 255.0)


# ══════════════════════════════════════════════════════════
#  KONTROL
# ══════════════════════════════════════════════════════════

## debug.py:66-69 `toggle()` — siklus + cetak `[DEBUG] overlay = <nama>`.
func toggle() -> int:
	set_mode(next_mode(mode))
	return mode


func set_mode(m: int) -> void:
	mode = wrap_mode(m)
	_have_lines = false
	print("[DEBUG] overlay = %s" % str(MODE_NAMES[mode]))
	mode_changed.emit(mode)
	queue_redraw()


func enabled() -> bool:
	return is_enabled(mode)


## Sumber lingkaran jari + fase "event" (Main.gd).
func bind_gestures(gestures: Node) -> void:
	_gestures = gestures


# ══════════════════════════════════════════════════════════
#  PENGUMPULAN DATA — debug.py:79-93 `update`
# ══════════════════════════════════════════════════════════

func _now_ms() -> float:
	return float(Time.get_ticks_usec()) / 1000.0


func _append(history: Array, value: float) -> void:
	history.append(value)
	if history.size() > HISTORY_MAX:
		history.pop_front()


func _timer_or_new() -> _FrameTimer:
	if _timer == null:
		_timer = _FrameTimer.new()
	return _timer


## fps + frame_ms masuk sebagai argumen (deviasi #5). Riwayat jalan TERUS
## walau mode OFF — persis pygame, yang hanya mencek mode di `draw()`, jadi
## overlay menyala dengan angka hangat.
func update(fps: float, frame_ms: float) -> void:
	_append(fps_history, fps)
	_append(frame_ms_history, frame_ms)
	_frames += 1
	if frame_ms > _peak_ms:
		_peak_ms = frame_ms
	if slow_frame(frame_ms):
		_slow_frames += 1
	var now := _now_ms()
	if log_to_console and now - _last_log_ms >= log_interval * 1000.0:
		_last_log_ms = now
		var t := phase_report()
		print(perf_log_line(fps, avg(frame_ms_history),
			float(t.get("update", 0.0)), float(t.get("draw", 0.0)),
			str(AppShell.quality_level), _entity_counts(), memory_str()))


func _count_live(group: String) -> int:
	var n := 0
	for node in get_tree().get_nodes_in_group(group):
		if is_instance_valid(node) and not bool(node.get("is_dead")):
			n += 1
	return n


## debug.py:181-190 `_entity_counts(game)`. Godot membaca grup scene;
## `game.projectiles` = peluru menara (grup "bullets"). SkillProjectile punya
## grup sendiri dan TIDAK dihitung — sama seperti pygame. Unit yang masih
## memainkan animasi mati terhitung sampai dibebaskan (deviasi mesin 1-2
## frame, dicatat di README).
func _entity_counts() -> String:
	return entity_counts(_count_live("minions"), _count_live("towers"),
		_count_live("heroes"), _count_live("bullets"))


func _audio_summary() -> String:
	var a: Dictionary = AudioManager.combat_stats()
	return line_audio(int(a.get("main", 0)), int(a.get("tolak_jeda", 0)),
		int(a.get("tolak_anggaran", 0)), int(a.get("tolak_kanal", 0)))


func _active_points() -> Array:
	var out: Array = []
	if _gestures == null or not is_instance_valid(_gestures):
		return out
	var pts = _gestures.get("points")
	if not (pts is Dictionary):
		return out
	for tid in (pts as Dictionary):
		var tp: Variant = (pts as Dictionary)[tid]
		if tp is Dictionary and ((tp as Dictionary)["pos"] is Vector2):
			out.append((tp as Dictionary)["pos"] as Vector2)
	return out


## State mentah untuk `build_lines` / `build_ops`.
func state_snapshot() -> Dictionary:
	var s := {
		"mode": mode,
		"audio": _audio_summary(),
		"fps": Engine.get_frames_per_second(),
		"frame_avg": avg(frame_ms_history),
		"peak": _peak_ms,
		"phases": phase_report(),
		"entities": _entity_counts(),
		"quality": str(AppShell.quality_level),
		"cheap_alpha": UiTheme.cheap_alpha(),
		"sprite_cache": true,
		"slow_frames": _slow_frames,
		"frames": _frames,
		"memory": memory_str(),
		"build": build_label(),
		"device": device,
		"extra": extra,
		"frame_ms_history": frame_ms_history,
		"points": _active_points(),
		"safe": MobileLayout.safe_area(),
	}
	return s


## Fase frame (baris 2). Padanan `perf.FrameTimer.report()` versi Godot:
##   * "event"  = biaya lapisan gesture menerjemahkan + mengirim aksi frame
##     ini (dimarkan Main lewat `note_event`) — pengganti `pygame.event.get()`
##     yang di Godot dilakukan engine, jadi yang terukur bagian milik kita;
##   * "update" = `Performance.TIME_PHYSICS_PROCESS` = langkah simulasi 60 Hz,
##     padanan langsung `game.update()` pygame;
##   * "draw"   = `TIME_PROCESS` (satu frame penuh) dikurangi simulasi = render
##     + present Godot (engine tidak memisahkan swap buffers);
##   * "flip"   = tidak ada batas nyata di Godot -> 0,0, persis perilaku
##     `t.get("flip", 0)` untuk fase yang belum pernah di-mark.
func phase_report() -> Dictionary:
	var frame_ms := Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
	var sim_ms := Performance.get_monitor(
		Performance.TIME_PHYSICS_PROCESS) * 1000.0
	var t := _timer_or_new().report()
	var out := {
		"event": float(t.get("event", 0.0)),
		"update": sim_ms,
		"draw": maxf(0.0, frame_ms - sim_ms),
		"flip": 0.0,
	}
	return out


func _process(_delta: float) -> void:
	# frame-ms dari jam NYATA (deviasi #5): `delta` ikut Engine.time_scale.
	var now_us := Time.get_ticks_usec()
	var frame_ms := 1000.0 / 60.0
	if _last_frame_us >= 0:
		frame_ms = float(now_us - _last_frame_us) / 1000.0
	_last_frame_us = now_us
	update(Engine.get_frames_per_second(), frame_ms)
	if is_enabled(mode):
		queue_redraw()


func _default_measurer() -> Callable:
	var font := UiTheme.font_for_weight("body")
	var bold := UiTheme.font_for_weight("body_bold")
	return func(text: String, size: int) -> Vector2:
		var f: Font = bold if size >= MINI_FONT else font
		if f == null:
			return Vector2(float(text.length()) * float(size) * 0.5,
				float(size))
		return Vector2(
			f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x,
			f.get_height(size))


# ══════════════════════════════════════════════════════════
#  RENDER — daftar op dieksekusi, tidak ada logika di sini
# ══════════════════════════════════════════════════════════

## debug.py:243-251: teks panel LENGKAP/GRAFIK cukup diperbarui 4x/detik
## (mode MINI dihitung tiap frame, persis `_draw_mini`).
func _lines_throttled(s: Dictionary) -> Array:
	var sekarang := _now_ms()
	if not _have_lines or sekarang - _lines_at >= JEDA_SEGAR_MS:
		_lines_cache = build_lines(s)
		_lines_at = sekarang
		_have_lines = true
	return _lines_cache


func _draw() -> void:
	if not is_enabled(mode):
		return
	var s := state_snapshot()
	var lines: Array = []
	if mode != MODE_MINI:
		lines = _lines_throttled(s)
	for entry in build_ops(s, lines, _default_measurer()):
		_exec_op(entry as Dictionary)


func _exec_op(op: Dictionary) -> void:
	match str(op["op"]):
		"panel_alpha":
			_panel(op["rect"] as Rect2, _rgba(op["bg"] as Array),
				_rgb(op["border"] as Array))
		"panel_opaque":
			_panel(op["rect"] as Rect2, _rgb(op["bg"] as Array),
				_rgb(op["border"] as Array))
		"text":
			var font := UiTheme.font_for_weight(str(op["weight"]))
			if font == null:
				return
			# pygame me-blit surface teks di TOP-LEFT; `draw_string` memakai
			# BASELINE -> ascent ditambahkan (deviasi #3 di FpsCounter.gd).
			# Tanpa bayangan: debug.py memakai `font.render(text, True, c)`.
			var at := Vector2(float(op["x"]), float(op["y"]))
			draw_string(font, at + Vector2(0.0,
				font.get_ascent(int(op["size"]))), str(op["text"]),
				HORIZONTAL_ALIGNMENT_LEFT, -1, int(op["size"]),
				_rgba(op["color"] as Array))
		"line":
			draw_line(Vector2(float(op["x1"]), float(op["y1"])),
				Vector2(float(op["x2"]), float(op["y2"])),
				_rgb(op["color"] as Array), float(op.get("width", 1.0)))
		"poly":
			var raw: Array = op["points"] as Array
			if raw.size() < 2:
				return
			var path := PackedVector2Array()
			for p in raw:
				path.append(p as Vector2)
			draw_polyline(path, _rgb(op["color"] as Array),
				float(op.get("width", 1.0)), true)
		"circle":
			if bool(op["filled"]):
				draw_circle(op["at"] as Vector2, float(op["r"]),
					_rgb(op["color"] as Array))
			else:
				draw_arc(op["at"] as Vector2, float(op["r"]), 0.0, TAU, 24,
					_rgb(op["color"] as Array), float(op["width"]), true)


## debug.py:193-202 `_panel`. Godot selalu punya komposisi alpha di GPU, jadi
## cabang "hemat" (SRCALPHA + alpha 170) yang dipakai untuk mini/grafik;
## panel LENGKAP memakai buffer opaque persis `_render_lines`.
func _panel(rect: Rect2, bg: Color, border: Color) -> void:
	draw_rect(rect, bg, true)
	_border(rect, border)


## pygame `draw.rect(..., width=1)` menggambar tepi DI DALAM rect; garis Godot
## jatuh di sepanjang tepi (setengah di luar) -> digambar manual 1px dalam.
func _border(rect: Rect2, color: Color) -> void:
	var x0 := rect.position.x
	var y0 := rect.position.y
	var x1 := rect.end.x - 1.0
	var y1 := rect.end.y - 1.0
	draw_line(Vector2(x0, y0), Vector2(x1, y0), color, 1.0)
	draw_line(Vector2(x0, y1), Vector2(x1, y1), color, 1.0)
	draw_line(Vector2(x0, y0), Vector2(x0, y1), color, 1.0)
	draw_line(Vector2(x1, y0), Vector2(x1, y1), color, 1.0)


## Padanan `perf.FrameTimer` (mobile/perf.py:962-991): smoothing 0,9 per
## fase; `report()` = rata-rata per fase; fase yang belum di-mark absen dari
## dict (pemakai memakai `.get(fase, 0)` — persis `t.get("event", 0)`).
class _FrameTimer:
	var smooth := 0.9
	var marks := {}
	var avg := {}
	var _t0 := 0.0
	var _phase: String = ""

	func start(phase: String) -> void:
		var now := float(Time.get_ticks_usec()) / 1000.0
		if _phase != "":
			_close(now)
		_phase = phase
		_t0 = now

	func _close(now: float) -> void:
		note(_phase, now - _t0)

	func note(phase: String, ms: float) -> void:
		marks[phase] = ms
		var prev = avg.get(phase, ms)
		avg[phase] = float(prev) * smooth + ms * (1.0 - smooth)

	func report() -> Dictionary:
		return avg


## Fase "event" = waktu yang dipakai lapisan gesture menerjemahkan +
## mengirim aksi frame ini (Main.gd). Tidak ada padanan `pygame.event.get()`
## di Godot, jadi inilah angka yang paling dekat.
func note_event(ms: float) -> void:
	_timer_or_new().note("event", ms)
