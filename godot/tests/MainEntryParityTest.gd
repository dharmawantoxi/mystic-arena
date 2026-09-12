# MainEntryParityTest — port entry point `main.py` (FASE 27).
#
# Mengunci lapisan APLIKASI yang tidak punya pemilik lain di Godot:
#   1. kebijakan LOOP — fixed 60 Hz + pembatas kejaran 4 langkah
#      (paritas FIXED_DT_MS / MAX_CATCHUP main.py:335-336);
#   2. boot — banner, crash_log.txt di direktori writable, BGM + ambient
#      sejak aplikasi mulai (main.py:161-164, mobile/debug.py:427-450);
#   3. preset kualitas + adaptive quality (mobile/perf.py:861-911);
#   4. batas FPS dari settings dengan pembatas preset (main.py:620-641);
#   5. siklus hidup app — audio dibekukan saat ke latar, TIDAK dihidupkan
#      kalau pemain sedang di menu PAUSE (main.py:139-166);
#   6. boot mendarat di MENU (STATE_SPLASH -> STATE_MENU main.py:405-412),
#      dengan splash yang sengaja DILEWATI di headless.
#
# Bukan tes oracle pygame: main.py mengimpor `game`/`menu`/`settings`/
# `sound_manager` yang sudah tidak ada di repo (modul itu melebur ke
# _core.py/_system.py), jadi berkasnya sendiri tidak bisa dijalankan — yang
# dikunci di sini adalah KONSTANTA dan cabang keputusannya, direkam dari teks
# sumber main.py. Perilaku yang sudah punya port lama (transisi match,
# mesin state, HUD sentuh) dikunci tes lain.
#
# godot --headless --path godot res://tests/MainEntryParityTest.tscn --quit-after 240
# Require "[MainEntryParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const MainScene = preload("res://scenes/main.tscn")

## Sampel yang diumpankan ke adaptive quality. Jauh lebih besar daripada
## `ADAPTIVE_WINDOW` (90) karena `_update_adaptive_quality()` SELALU
## menambahkan satu sampel NYATA (`Engine.get_frames_per_second()`) sebelum
## menghitung rata-rata — di headless angkanya bisa ratusan. Dengan 500
## sampel, satu sampel nyata tidak bisa membalikkan keputusan (batas 26/52).
const FEED_COUNT := 500

var _failures: int = 0
var _checks: int = 0
var _done: bool = false
var _messages: Array[String] = []

var _prev_quality: String = ""
var _prev_adaptive: bool = true
var _prev_force_touch: bool = false
var _prev_fps_setting: float = 0.0
var _main = null


func _ready() -> void:
	# Tes menjeda tree sendiri (bagian siklus hidup) — jangan ikut beku.
	process_mode = Node.PROCESS_MODE_ALWAYS
	_boot.call_deferred()


func _boot() -> void:
	_snapshot()
	_test_loop_policy()
	_test_boot_artifacts()
	_test_fps_limit()
	_test_adaptive_quality()
	_test_lifecycle()
	await _test_boot_lands_in_menu()
	_restore()
	_finish()


func _snapshot() -> void:
	_prev_quality = AppShell.quality_level
	_prev_adaptive = AppShell.adaptive_enabled
	_prev_force_touch = AppShell.force_touch
	_prev_fps_setting = SaveManager.get_setting("fps_limit", 0.0)
	# Sampling FPS headless (angka acak karena tanpa vsync) tidak boleh
	# mengubah preset di tengah tes.
	AppShell.adaptive_enabled = false


func _restore() -> void:
	AppShell.quality_level = _prev_quality
	AppShell.adaptive_enabled = _prev_adaptive
	AppShell.force_touch = _prev_force_touch
	AppShell._samples.clear()
	AppShell._cooldown = 0
	SaveManager.set_setting("fps_limit", _prev_fps_setting, false)
	AppShell.apply_fps_limit(_prev_fps_setting)
	AudioManager.pause_bgm(false)
	AudioManager.pause_ambient(false)
	if get_tree().paused:
		get_tree().paused = false
		GameManager.set_paused(false)


# ══════════════════════════════════════════════════════════
#  1. KEBIJAKAN LOOP
# ══════════════════════════════════════════════════════════

func _test_loop_policy() -> void:
	_expect(AppShell.boot_done(), "AppShell._ready harus selesai sebelum tes")
	_expect(AppShell.MAX_CATCHUP == 4,
			"MAX_CATCHUP main.py:336 = 4 (bukan bawaan engine 8)")
	_expect(int(ProjectSettings.get_setting(
			"physics/common/max_physics_steps_per_frame", 8))
			== AppShell.MAX_CATCHUP,
			"project.godot: max_physics_steps_per_frame harus ikut MAX_CATCHUP")
	_expect(int(ProjectSettings.get_setting(
			"physics/common/physics_ticks_per_second", 0)) == 60,
			"project.godot: physics_ticks_per_second = 60 (FIXED_DT_MS main.py)")


# ══════════════════════════════════════════════════════════
#  2. BOOT — crash log + audio
# ══════════════════════════════════════════════════════════

func _test_boot_artifacts() -> void:
	_expect(FileAccess.file_exists(AppShell.CRASH_LOG_PATH),
			"crash_log.txt harus ditulis saat boot (mobile/debug.py:427-450)")
	# Isi log harus memuat baris SESSION START yang ditulis boot terakhir.
	if FileAccess.file_exists(AppShell.CRASH_LOG_PATH):
		var rf := FileAccess.open(AppShell.CRASH_LOG_PATH, FileAccess.READ)
		var text := rf.get_as_text() if rf != null else ""
		if rf != null:
			rf.close()
		_expect(text.contains("SESSION START"),
				"crash_log.txt harus memuat penanda SESSION START")
	# BGM boot: pygame memutar 'bgm_battle.wav' SEBELUM menu dibuat
	# (main.py:163). AudioManager no-op + catat nama walau aset audio belum
	# disalin converter, jadi nama track-nya tetap bisa dikunci di CI.
	_expect(AudioManager._current_bgm == AppShell.BOOT_BGM,
			"boot harus memutar BGM %s (main.py:163)" % AppShell.BOOT_BGM)
	# Audio benar-benar TERMUAT, bukan cuma tersalin. 8 berkas di
	# assets/sounds/ bernama ".wav" padahal kontainernya Ogg Vorbis (7) / MP3
	# (1); importer Godot dipilih dari EKSTENSI, jadi salinan yang salah nama
	# tetap ada di disk namun ditolak ("Not a WAV file ... found 'OggS'") dan
	# SFX-nya senyap tanpa membuat tes lain gagal. CI selalu menyalin aset
	# (langkah 0 godot-check.yml) -> jumlah stream harus == jumlah berkas.
	# Tanpa aset (clone segar) cek ini lolos trivial.
	if DirAccess.dir_exists_absolute(AudioManager.SOUNDS_DIR):
		var berkas := 0
		for f in DirAccess.get_files_at(AudioManager.SOUNDS_DIR):
			if AudioManager.AUDIO_EXTS.has(f.get_extension().to_lower()):
				berkas += 1
		_expect(berkas == 0 or AudioManager._streams.size() == berkas,
			"semua berkas audio termuat (%d stream / %d berkas)"
				% [AudioManager._streams.size(), berkas])
	if AudioManager._sounds_available:
		# Kunci _streams memakai nama TANPA ekstensi: play_bgm("bgm_battle.wav")
		# harus menormalkannya, kalau tidak BGM tidak pernah dapat stream
		# (gejalanya: baris "bgm ... tidak tersedia" walau aset sudah disalin).
		_expect(AudioManager._bgm_player.stream != null,
			"BGM boot %s dapat stream (kunci stream = nama tanpa ekstensi)"
				% AppShell.BOOT_BGM)


# ══════════════════════════════════════════════════════════
#  3. BATAS FPS (paritas main.py:620-641)
# ══════════════════════════════════════════════════════════

func _test_fps_limit() -> void:
	AppShell.force_touch = false
	AppShell.quality_level = AppShell.QUALITY_HIGH
	_expect(AppShell.resolve_fps_limit(0.0) == 60,
			"setting 0 + kualitas high -> target 60 (main.py:638)")
	_expect(AppShell.resolve_fps_limit(120.0) == 120,
			"desktop: setting boleh menaikkan di atas target (main.py:640)")
	_expect(AppShell.resolve_fps_limit(30.0) == 30,
			"desktop: setting menurunkan batas apa adanya")
	AppShell.quality_level = AppShell.QUALITY_LOW
	_expect(AppShell.target_fps() == 30,
			"preset LOW -> target 30 FPS (mobile/perf.py:529)")
	_expect(AppShell.resolve_fps_limit(0.0) == 30,
			"setting 0 + kualitas low -> target 30")

	# Mode sentuh (paritas MYSTIC_FORCE_TOUCH=1): setting hanya boleh
	# MENURUNKAN — `limit = min(limit, Quality.target_fps)` main.py:641.
	AppShell.force_touch = true
	_expect(AppShell.touch_mode(), "force_touch harus mengaktifkan mode sentuh")
	_expect(AppShell.resolve_fps_limit(120.0) == 30,
			"sentuh + preset low: 120 dipotong ke target 30 (main.py:641)")
	_expect(AppShell.resolve_fps_limit(20.0) == 20,
			"sentuh: setting di bawah target tetap dipakai")
	_expect(AppShell.resolve_fps_limit(0.0) == 30,
			"sentuh + setting 0 -> target preset 30")
	AppShell.force_touch = false

	# apply_fps_limit adalah satu-satunya penulis Engine.max_fps.
	AppShell.quality_level = AppShell.QUALITY_HIGH
	AppShell.apply_fps_limit(0.0)
	_expect(Engine.max_fps == 60, "apply_fps_limit(0) -> Engine.max_fps 60")
	AppShell.apply_fps_limit(45.0)
	_expect(Engine.max_fps == 45, "apply_fps_limit(45) -> Engine.max_fps 45")


# ══════════════════════════════════════════════════════════
#  4. ADAPTIVE QUALITY (paritas mobile/perf.py:877-911)
# ══════════════════════════════════════════════════════════

func _feed_samples(fps: float, count: int = -1) -> void:
	var n := FEED_COUNT if count < 0 else count
	AppShell._samples.clear()
	for _i in range(n):
		AppShell._samples.append(fps)


func _test_adaptive_quality() -> void:
	AppShell.adaptive_enabled = true
	AppShell.force_touch = false
	AppShell.quality_level = AppShell.QUALITY_HIGH
	AppShell._samples.clear()
	AppShell._cooldown = 0

	# Jendela 90 frame: baru bertindak setelah sampel ke-90. Dua dikurangi
	# karena _update_adaptive_quality() menambahkan satu sampel nyata.
	_feed_samples(60.0, AppShell.ADAPTIVE_WINDOW - 2)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_HIGH,
			"adaptive tidak boleh bertindak sebelum jendela 90 sampel penuh")
	_expect(AppShell._samples.size() == AppShell.ADAPTIVE_WINDOW - 1,
			"sampel belum dikosongkan sebelum jendela penuh")

	# Rata-rata 20 (< 26) -> turun SATU tingkat: high -> medium.
	_feed_samples(20.0)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_MEDIUM,
			"FPS 20 -> preset turun high->medium (mobile/perf.py:902-903)")
	_expect(AppShell._cooldown == AppShell.ADAPTIVE_COOLDOWN_DOWN,
			"setelah menurunkan, cooldown 180 frame")
	_expect(AppShell._samples.is_empty(), "sampel dikosongkan tiap jendela")

	# Cooldown menahan keputusan berikutnya walau sampel sudah penuh.
	_feed_samples(20.0)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_MEDIUM,
			"cooldown menahan penurunan kedua")
	_expect(AppShell._cooldown == AppShell.ADAPTIVE_COOLDOWN_DOWN - 1,
			"cooldown berkurang 1 per frame")

	# Lewati cooldown -> medium -> low.
	AppShell._cooldown = 0
	_feed_samples(20.0)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_LOW,
			"FPS 20 lagi -> preset turun medium->low")

	# Sudah di LOW: tidak ada tingkat lebih bawah.
	AppShell._cooldown = 0
	_feed_samples(10.0)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_LOW,
			"LOW adalah dasar tangga kualitas")
	_expect(AppShell._cooldown == 0, "tidak ada cooldown kalau preset tak berubah")

	# Rata-rata 60 (> 52) -> naik: low -> medium -> high.
	AppShell._cooldown = 0
	_feed_samples(60.0)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_MEDIUM,
			"FPS 60 -> preset naik low->medium (mobile/perf.py:907-908)")
	_expect(AppShell._cooldown == AppShell.ADAPTIVE_COOLDOWN_UP,
			"setelah menaikkan, cooldown 300 frame")
	AppShell._cooldown = 0
	_feed_samples(60.0)
	AppShell._update_adaptive_quality()
	_expect(AppShell.quality_level == AppShell.QUALITY_HIGH,
			"FPS 60 lagi -> preset naik medium->high")

	# Perubahan preset langsung menulis batas FPS (di perangkat sentuh: 30).
	AppShell.force_touch = true
	AppShell.quality_level = AppShell.QUALITY_HIGH
	AppShell._cooldown = 0
	_feed_samples(20.0)
	AppShell._update_adaptive_quality()
	SaveManager.set_setting("fps_limit", 0.0, false)
	AppShell._apply_fps_limit()
	_expect(AppShell.quality_level == AppShell.QUALITY_MEDIUM,
			"sentuh: FPS 20 -> medium")
	_expect(Engine.max_fps == 60, "sentuh + medium -> batas 60")
	AppShell.force_touch = false
	AppShell._cooldown = 0
	_feed_samples(20.0)
	AppShell._update_adaptive_quality()
	AppShell._apply_fps_limit()
	_expect(AppShell.quality_level == AppShell.QUALITY_LOW,
			"sentuh: FPS 20 lagi -> low")
	_expect(Engine.max_fps == 30, "sentuh + low -> batas 30 (mobile/perf.py:529)")
	AppShell.adaptive_enabled = false


# ══════════════════════════════════════════════════════════
#  5. SIKLUS HIDUP APP (paritas _handle_background main.py:139-166)
# ══════════════════════════════════════════════════════════

func _test_lifecycle() -> void:
	GameManager.set_paused(false)
	get_tree().paused = false
	AudioManager.pause_bgm(false)
	AudioManager.pause_ambient(false)

	# Status dibaca dari flag `bgm_paused`/`ambient_paused`, bukan
	# `stream_paused` engine: AudioStreamPlayer mengabaikan properti itu saat
	# tidak ada playback aktif (di CI aset .wav belum disalin converter),
	# jadi `stream_paused` tak bisa dibaca balik. Kalau player memang
	# berbunyi, keduanya harus sama.
	AppShell._notification(NOTIFICATION_APPLICATION_PAUSED)
	_expect(AudioManager.bgm_paused,
			"app ke latar -> BGM dibekukan (mixer.pause main.py:142)")
	_expect(AudioManager.ambient_paused,
			"app ke latar -> ambient dibekukan (main.py:143)")
	if AudioManager._bgm_player.playing:
		_expect(AudioManager._bgm_player.stream_paused,
				"BGM yang sedang berbunyi ikut di-stream_paused")
	# PAUSED kedua tanpa RESUMED tidak boleh menggandakan apa pun.
	AppShell._notification(NOTIFICATION_APPLICATION_PAUSED)
	_expect(AudioManager.bgm_paused,
			"PAUSED ganda tetap membekukan (idempoten)")

	AppShell._notification(NOTIFICATION_APPLICATION_RESUMED)
	_expect(not AudioManager.bgm_paused,
			"app kembali -> BGM dilanjutkan (main.py:157)")
	_expect(not AudioManager.ambient_paused,
			"app kembali -> ambient dilanjutkan")

	# RESUMED tanpa PAUSED = no-op (jangan hidupkan audio yang tak dibekukan).
	AudioManager.pause_bgm(true)
	AppShell._notification(NOTIFICATION_APPLICATION_RESUMED)
	_expect(AudioManager.bgm_paused,
			"RESUMED tanpa PAUSED tidak menyentuh audio")
	AudioManager.pause_bgm(false)

	# Sedang di menu PAUSE: app kembali TIDAK boleh menghidupkan musik di
	# balik layar pause (menu pause membekukan audio lewat jalurnya sendiri).
	get_tree().paused = true
	GameManager.set_paused(true)
	AudioManager.pause_bgm(true)
	AudioManager.pause_ambient(true)
	AppShell._notification(NOTIFICATION_APPLICATION_RESUMED)
	_expect(AudioManager.bgm_paused,
			"menu PAUSE aktif: app kembali tidak menghidupkan BGM")
	get_tree().paused = false
	GameManager.set_paused(false)
	AudioManager.pause_bgm(false)
	AudioManager.pause_ambient(false)


# ══════════════════════════════════════════════════════════
#  6. BOOT MENDARAT DI MENU (paritas STATE_SPLASH -> STATE_MENU)
# ══════════════════════════════════════════════════════════

func _test_boot_lands_in_menu() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	_main = MainScene.instantiate()
	add_child(_main)
	await get_tree().process_frame
	await get_tree().process_frame

	# Splash DILEWATI di headless (layar presentasi 3 detik tanpa efek
	# gameplay) — kalau ikut tampil, semua input sintetis tes tertelan.
	_expect(get_tree().get_nodes_in_group("splash").is_empty(),
			"splash tidak boleh tampil di headless (input tes tidak tertelan)")

	# Boot = menu utama terbuka (STATE_MENU main.py:407-412), dan Main siap
	# memulai match dari tombol MULAI.
	_expect(_main != null and is_instance_valid(_main), "Main scene harus hidup")
	var menu = get_tree().get_first_node_in_group("main_menu")
	_expect(menu != null and is_instance_valid(menu),
			"MainMenu harus ada di grup main_menu")
	if menu != null and is_instance_valid(menu):
		_expect(bool(menu.is_open()),
				"boot harus mendarat di menu utama (menu terbuka)")
		_expect(int(menu.state) != int(menu.State.PAUSE),
				"boot bukan menu PAUSE (STATE_MENU, bukan STATE_PAUSE)")
	var connector := get_tree().get_first_node_in_group("game_connector")
	_expect(connector != null and connector.has_method("start_match"),
			"GameManagerConnector harus siap menerima start_match")


# ═══ harness ═══

func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[MainEntryParityTest] %s" % message
		_messages.append(line)
		if _messages.size() <= 40:
			push_error(line)


func _finish() -> void:
	if _done:
		return
	_done = true
	if _failures == 0:
		print("[MainEntryParityTest] PASS: %d cek entry point main.py" % _checks)
		print("[MainEntryParityTest] PASS")
	else:
		for msg in _messages:
			print(msg)
		print("[MainEntryParityTest] FAIL: %d failures dari %d checks"
				% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
