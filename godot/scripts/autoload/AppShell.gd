# AppShell.gd — autoload: port ENTRY POINT `main.py` (boot + loop + lifecycle).
#
# Kenapa autoload baru, bukan menambah Main.gd / GameManager: main.py adalah
# lapisan APLIKASI — ia hidup lebih lama dari match mana pun dan tidak tahu
# apa-apa tentang arena:
#
#   * banner boot + direktori simpan (main.py:271-282),
#   * kebijakan LOOP (fixed timestep 60 Hz + pembatas kejaran,
#     main.py:290-336),
#   * preset kualitas + adaptive quality (main.py:161 + mobile/perf.py),
#   * batas FPS dari settings (main.py:620-641),
#   * BGM + ambient sejak boot (main.py:161-164),
#   * siklus hidup Android: app ke latar -> audio dibekukan
#     (main.py:139-166),
#   * crash_log.txt di direktori writable (mobile/debug.py:427-450).
#
# Yang TIDAH ada di sini (sudah punya pemilik masing-masing, jangan
# diduplikasi supaya tidak drift):
#   * mesin state SPLASH/MENU/GAME/PAUSE -> ControllerRouter.current_state()
#     (FASE 24) + Main._apply_menu_coverage + TouchHUD.sync_from_match,
#   * transisi match (play/replay/next_level/return_to_menu) -> GameManager,
#   * pipeline sentuh -> emulate_mouse_from_touch + TouchHUD/SidePanel.
#
# Dipasang PALING AKHIR di project.godot: AppShell._ready memanggil
# AudioManager dan SaveManager, jadi keduanya harus sudah siap.
extends Node

## ══ LOOP (paritas main.py:290-336) ══
## Logika game berbasis FRAME: 1 langkah = 1/60 detik. main.py mengejar waktu
## nyata dengan `while sim_acc >= FIXED_DT_MS and sim_steps < MAX_CATCHUP`.
## Di Godot yang setara adalah physics tick 60 Hz + batas langkah per frame:
##   physics/common/physics_ticks_per_second = 60   (sudah ada sejak Fase 0)
##   physics/common/max_physics_steps_per_frame = 4 (nilai bawaan engine = 8)
## Angka 4 DITURUNKAN dari 8 di main.py dengan alasan yang tercatat di sana:
## 8 langkah kejaran memakan SELURUH anggaran frame berikutnya di HP ("spiral
## kematian"), 4 langkah masih mengejar penuh sampai 15 FPS. Nilai ini dibaca
## engine saat startup, jadi ditulis di project.godot — baris ini hanya
## pemeriksaan (jangan ada yang mengubahnya tanpa sengaja).
const MAX_CATCHUP := 4
const FIXED_TICKS_PER_SECOND := 60

## ══ KUALITAS (paritas mobile/perf.py:861-911) ══
const QUALITY_LOW := "low"
const QUALITY_MEDIUM := "medium"
const QUALITY_HIGH := "high"
## Target FPS per preset — persis `Quality.apply`: 30 di LOW, 60 selainnya.
const TARGET_FPS := {
	QUALITY_LOW: 30,
	QUALITY_MEDIUM: 60,
	QUALITY_HIGH: 60,
}
## `AdaptiveQuality(window=90)`: rata-rata 90 frame, bukan 90 detik.
const ADAPTIVE_WINDOW := 90
## Di bawah ini -> turunkan preset (mobile/perf.py:884 `low_fps=26`).
const ADAPTIVE_LOW_FPS := 26.0
## Di atas ini -> naikkan preset (`high_fps=52`).
const ADAPTIVE_HIGH_FPS := 52.0
## Jeda dalam FRAME setelah menurunkan/menaikkan (180 / 300).
const ADAPTIVE_COOLDOWN_DOWN := 180
const ADAPTIVE_COOLDOWN_UP := 300

## ══ AUDIO BOOT (paritas main.py:163-164) ══
## pygame memutar BGM + ambient SEKALU di awal aplikasi (fade 3000 ms),
## jadi menu utama sudah berbunyi — bukan baru saat match dimulai.
const BOOT_BGM := "bgm_battle.wav"
const BOOT_BGM_FADE := 3.0
const BOOT_AMBIENT := "ambient_forest"
const BOOT_AMBIENT_MULT := 0.8

## ══ CRASH LOG (paritas mobile/debug.py:427-450 + main.py:86-105) ══
## pygame menulis crash_log.txt ke direktori writable supaya bug di HP tetap
## terbaca tanpa adb. Godot tidak punya sys.excepthook, TETAPI juga tidak
## perlu: satu error di _process/_physics_process hanya mencetak SCRIPT ERROR
## lalu engine melanjutkan frame berikutnya (aplikasi tidak mati) — itulah
## maksud `try/except` di main.py. Yang diport adalah bagian yang tersisa:
## log permanen di direktori writable, ditulis tiap boot.
const CRASH_LOG_PATH := "user://crash_log.txt"
## Rotasi sederhana: potong ekor 256 KB terakhir (HP bisa menahannya lama).
const CRASH_LOG_MAX_BYTES := 262144

## Preset kualitas aktif. Dipakai pembatas FPS dan dibaca AppShell sendiri;
## adaptive quality mengubahnya saat FPS rata-rata jeblok.
var quality_level: String = QUALITY_HIGH
## Matikan untuk harness/tes (paritas: AdaptiveQuality(enabled=adaptive)).
## Otomatis mati saat headless — lihat _headless().
var adaptive_enabled: bool = true
## Paksa mode sentuh di PC — paritas `MYSTIC_FORCE_TOUCH=1 python main.py`
## (mobile/platform_utils.py:60) untuk menguji layout HP tanpa perangkat.
var force_touch: bool = false

var _samples: Array = []
var _cooldown: int = 0
var _bg_paused: bool = false
var _boot_done: bool = false


func _ready() -> void:
	# Autoload: tetap jalan walau SceneTree di-pause (menu PAUSE, intro level).
	process_mode = Node.PROCESS_MODE_ALWAYS
	force_touch = OS.has_environment("MYSTIC_FORCE_TOUCH") \
		and OS.get_environment("MYSTIC_FORCE_TOUCH") == "1"
	# Headless (CI, `godot --headless`): tidak ada layar dan tidak ada vsync,
	# jadi "FPS" yang diukur tidak bermakna dan pembatas hanya memperlambat
	# run yang waktunya dihitung dalam FRAME (--quit-after N).
	if headless():
		adaptive_enabled = false
		Engine.max_fps = 0
	_check_loop_policy()
	# URUTAN PENTING: preset kualitas harus sudah terdeteksi SEBELUM batas
	# FPS dihitung (target 30 FPS di HP vs 60 di desktop).
	_detect_quality()
	if not headless():
		_apply_fps_limit()
	_start_boot_audio()
	_apply_interface_language()
	_write_session_log()
	_print_boot_banner()
	_boot_done = true


## ══ BAHASA ANTARMUKA (paritas localization.py + GameSettings) ══
## pygame menyinkronkan bahasa aktif saat singleton GameSettings dibuat
## (_core.py:9116) dan setiap kali settings.json dibaca (_core.py:9170),
## jadi teks UI sudah benar sebelum menu pertama digambar.
##
## Di Godot langkah ini milik AppShell karena autoload ini dipasang PALING
## AKHIR (project.godot): saat `_ready()`-nya jalan, `SaveManager._ready()`
## sudah selesai membaca berkas slot, sedangkan `GameManager._ready()` jalan
## SEBELUM itu (urutan autoload) dan hanya melihat nilai default.
func _apply_interface_language() -> void:
	GameManager.apply_language(SaveManager.get_setting_str("language",
		MysticLocalization.DEFAULT_LANGUAGE))


## true untuk `godot --headless` / server tanpa layar. Nama server tampilan
## dibandingkan longgar ("headless"/"dummy") supaya tidak bergantung pada
## satu ejaan versi engine; kalau tidak cocok, yang dipakai perilaku produksi
## (bukan sebaliknya).
func headless() -> bool:
	var n := DisplayServer.get_name().to_lower()
	return n.contains("headless") or n.contains("dummy")


# ══════════════════════════════════════════════════════════
#  LOOP
# ══════════════════════════════════════════════════════════

## Konfirmasi kebijakan loop (jangan diam-diam berubah jadi 8 langkah).
## Dicetak sekali saat boot; nilai aslinya ada di project.godot karena engine
## membacanya sebelum autoload ini di-_ready().
func _check_loop_policy() -> void:
	var steps := int(ProjectSettings.get_setting(
			"physics/common/max_physics_steps_per_frame", 8))
	var ticks := int(ProjectSettings.get_setting(
			"physics/common/physics_ticks_per_second", 60))
	if steps != MAX_CATCHUP or ticks != FIXED_TICKS_PER_SECOND:
		push_warning(("[AppShell] kebijakan loop %d tick/s · catch-up %d "
				% [ticks, steps])
				+ (" — paritas main.py = %d tick/s · catch-up %d"
				% [FIXED_TICKS_PER_SECOND, MAX_CATCHUP]))


# ══════════════════════════════════════════════════════════
#  KUALITAS + BATAS FPS (paritas main.py:620-641)
# ══════════════════════════════════════════════════════════

## Tebakan awal presisi perangkat — paritas `perf.auto_detect_quality`:
## Android/iOS MULAI DARI LOW (lebih baik 30 FPS stabil sejak detik pertama,
## pemain bisa menaikkan di SETTINGS), desktop HIGH.
func _detect_quality() -> void:
	quality_level = QUALITY_LOW if touch_mode() else QUALITY_HIGH


func touch_mode() -> bool:
	if force_touch:
		return true
	# `OS.get_name()` mengembalikan "Android" / "iOS" / "Linux" / "Windows" /
	# "macOS" / "Web" — dibandingkan lowercase supaya tidak bergantung ejaan.
	# (Lokal `os_name`, bukan `name`: `name` properti Node.)
	var os_name := OS.get_name().to_lower()
	return os_name == "android" or os_name == "ios"


func target_fps() -> int:
	return int(TARGET_FPS.get(quality_level, 60))


## Terjemahkan setting pemain -> batas FPS:
##   0 (atau tidak ada) = ikut target preset kualitas,
##   di perangkat sentuh setting hanya boleh MENURUNKAN, bukan menaikkan.
func resolve_fps_limit(setting: float) -> int:
	var limit := int(setting)
	var target := target_fps()
	if limit <= 0:
		limit = target
	elif touch_mode():
		limit = mini(limit, target)
	return limit


## Satu-satunya tempat Engine.max_fps ditulis. GameManager.apply_fps_limit
## (slider SETTINGS) mendelegasikan ke sini supaya pembatas preset kualitas
## tidak bisa dilangkahi.
func apply_fps_limit(fps: float) -> void:
	Engine.max_fps = resolve_fps_limit(fps)


func _apply_fps_limit() -> void:
	apply_fps_limit(SaveManager.get_setting("fps_limit", 0.0))


## AdaptiveQuality.update(fps) — dipanggil tiap frame dari _process.
func _update_adaptive_quality() -> void:
	if not adaptive_enabled:
		return
	if _cooldown > 0:
		_cooldown -= 1
		return
	_samples.append(Engine.get_frames_per_second())
	if _samples.size() < ADAPTIVE_WINDOW:
		return
	var avg := 0.0
	for s in _samples:
		avg += float(s)
	avg /= float(_samples.size())
	_samples.clear()
	if avg < ADAPTIVE_LOW_FPS and quality_level != QUALITY_LOW:
		# HIGH -> MEDIUM, MEDIUM -> LOW (persis mobile/perf.py:902-903)
		_apply_quality(QUALITY_LOW if quality_level == QUALITY_MEDIUM \
				else QUALITY_MEDIUM)
		_cooldown = ADAPTIVE_COOLDOWN_DOWN
	elif avg > ADAPTIVE_HIGH_FPS and quality_level != QUALITY_HIGH:
		# LOW -> MEDIUM, MEDIUM -> HIGH (persis mobile/perf.py:907-908)
		_apply_quality(QUALITY_HIGH if quality_level == QUALITY_MEDIUM \
				else QUALITY_MEDIUM)
		_cooldown = ADAPTIVE_COOLDOWN_UP


func _apply_quality(level: String) -> void:
	quality_level = level
	_apply_fps_limit()
	print("[PERF] adaptive quality -> %s (target %d FPS, batas %d)"
			% [quality_level, target_fps(), Engine.max_fps])


func _process(_delta: float) -> void:
	_update_adaptive_quality()


# ══════════════════════════════════════════════════════════
#  AUDIO BOOT
# ══════════════════════════════════════════════════════════

## pygame: sound_mgr.play_bgm('bgm_battle.wav', loop=True, fade_ms=3000) lalu
## play_ambient('ambient_forest', volume_mult=0.8) SEBELUM menu dibuat, jadi
## menu utama pun berbunyi. GameManager.start_level tetap memanggil keduanya
## per level (fade 1500 ms) — itu no-op kalau track-nya sama.
func _start_boot_audio() -> void:
	AudioManager.play_bgm(BOOT_BGM, BOOT_BGM_FADE)
	AudioManager.play_ambient(BOOT_AMBIENT, BOOT_AMBIENT_MULT)


# ══════════════════════════════════════════════════════════
#  SIKLUS HIDUP (paritas _handle_background main.py:139-166)
# ══════════════════════════════════════════════════════════
# Android mematikan render saat app di-minimize. pygame memanggil
# mixer.pause() + music.pause() lalu TIDUR sampai event APP_FG datang; Godot
# menahan loop sendiri, jadi yang tersisa untuk diport hanyalah pembekuan
# audio — dan pelepasan hold taktis yang sudah ada di Main._notification
# (tanpa event release, perintah akan "nyangkut" aktif selamanya).

func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_PAUSED:
			_on_app_background()
		NOTIFICATION_APPLICATION_RESUMED:
			_on_app_foreground()


func _on_app_background() -> void:
	if _bg_paused:
		return
	_bg_paused = true
	AudioManager.pause_bgm(true)
	AudioManager.pause_ambient(true)
	print("[LIFECYCLE] app masuk background - audio dibekukan")


func _on_app_foreground() -> void:
	if not _bg_paused:
		return
	_bg_paused = false
	# Jangan hidupkan lagi kalau pemain TIDAK sedang bermain: menu PAUSE
	# membekukan audio lewat jalurnya sendiri (Main._toggle_pause), dan
	# menyalakannya dari sini akan menghidupkan musik di balik layar pause.
	if get_tree().paused or GameManager.is_paused:
		print("[LIFECYCLE] app kembali - audio tetap beku (menu PAUSE aktif)")
		return
	AudioManager.pause_bgm(false)
	AudioManager.pause_ambient(false)
	print("[LIFECYCLE] app kembali ke depan - audio dilanjutkan")


# ══════════════════════════════════════════════════════════
#  BOOT BANNER + CRASH LOG
# ══════════════════════════════════════════════════════════

## Paritas blok cetak main.py:271-282 (device / android / save / input /
## quality). Beberapa kolom tidak punya padanan engine (API level Android,
## versi SDL) — diganti info yang setara di Godot.
func _print_boot_banner() -> void:
	var engine_info: Dictionary = Engine.get_version_info()
	var device := OS.get_model_name()
	if device.is_empty():
		device = OS.get_processor_name()
	print("=".repeat(60))
	print("  MYSTIC ARENA - GODOT BUILD")
	print("  engine  : %s" % str(engine_info.get("string", "?")))
	print("  device  : %s" % device)
	print("  platform: %s (%s)" % [OS.get_name(),
			DisplayServer.get_name()])
	print("  save    : %s" % ProjectSettings.globalize_path("user://"))
	print("  input   : %s" % ("TOUCH" if touch_mode() else "MOUSE/KEYBOARD"))
	print("  quality : %s (target %d FPS · adaptive %s)"
			% [quality_level, target_fps(),
			"ON" if adaptive_enabled else "OFF"])
	print("  bahasa  : %s (%s)" % [GameManager.language,
		MysticLocalization.get_language_label()])
	print("  layar   : %s" % ("HEADLESS" if headless() else "JENDELA"))
	print("  loop    : fixed %d Hz · catch-up %d langkah"
			% [int(ProjectSettings.get_setting(
					"physics/common/physics_ticks_per_second", 60)),
			int(ProjectSettings.get_setting(
					"physics/common/max_physics_steps_per_frame", 8))])
	print("  audio   : bgm %s + ambient %s (batas FPS %d)"
			% [BOOT_BGM, BOOT_AMBIENT, Engine.max_fps])
	print("=".repeat(60))


## Tulis log permanen ke direktori writable (paritas crash_log.txt pygame
## yang ditulis install_crash_log_handler). Dipanggil tiap boot, dan terbuka
## untuk kode lain lewat write_crash_log().
func _write_session_log() -> void:
	var info: Dictionary = Engine.get_version_info()
	# `lang=` ikut tercatat: bug UI dari laporan pemain sering hanya bisa
	# direproduksi kalau bahasa antarmukanya diketahui (localization.py).
	write_crash_log("SESSION START · %s · %s · %s · quality=%s · lang=%s"
		% [str(info.get("string", "?")), OS.get_name(),
		OS.get_model_name(), quality_level, GameManager.language])


func write_crash_log(text: String) -> void:
	var existing := ""
	if FileAccess.file_exists(CRASH_LOG_PATH):
		var rf := FileAccess.open(CRASH_LOG_PATH, FileAccess.READ)
		if rf != null:
			existing = rf.get_as_text()
			rf.close()
	if existing.length() > CRASH_LOG_MAX_BYTES:
		existing = existing.substr(
				existing.length() - CRASH_LOG_MAX_BYTES)
	var wf := FileAccess.open(CRASH_LOG_PATH, FileAccess.WRITE)
	if wf == null:
		push_warning("[AppShell] gagal menulis %s" % CRASH_LOG_PATH)
		return
	wf.store_string(existing)
	wf.store_string("\n===== %s =====\n%s\n"
			% [Time.get_datetime_string_from_system(), text])
	wf.close()


## true setelah _ready selesai (dipakai tes: urutan autoload tidak boleh
## membuat AppShell dipanggil sebelum kualitas terdeteksi).
func boot_done() -> bool:
	return _boot_done
