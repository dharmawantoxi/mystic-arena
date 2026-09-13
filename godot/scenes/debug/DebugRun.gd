# DebugRun.gd — HARNESS DEBUG dari command line (satu scene, banyak skenario).
#
# Kenapa berkas ini ada: menguji/melihat port Godot selama ini berarti menjalankan
# salah satu dari 60+ scene `tests/*.tscn` (semuanya headless, tidak menampilkan
# apa-apa) atau membuka editor. Tidak ada cara untuk mengatakan "jalankan game
# seperti pemain, 30 detik, ambil screenshot tiap detik, lalu ceritakan apa yang
# terjadi" — baik di laptop maupun di GitHub Actions.
#
# Scene ini membungkus scene produksi APA ADANYA (default res://scenes/main.tscn,
# jadi tidak ada satu baris pun gameplay yang diubah) dan menambahkan:
#   * skenario (menu / level / battle / shop / scene apa pun),
#   * perekam `DebugProbe` (screenshot + cuplikan keadaan → report.json),
#   * batas waktu (detik atau frame) lalu keluar sendiri dengan baris
#     `[DebugRun] PASS` / `[DebugRun] FAIL: …` yang dibaca gerbang log.
#
# JALANKAN (dari akar repo):
#   # lokal
#   python3 tools/godot_debug_run.py --scenario battle --level 1 --seconds 30
#   # manual, tanpa wrapper (juga jalan: harness-nya yang penting)
#   godot --path godot res://scenes/debug/DebugRun.tscn --quit-after 3600 -- \
#         --scenario=battle --level=1 --seconds=30 --out=/tmp/debug
#
# KONTRAK
#   SCENARIOS dan ARG_KEYS di bawah HARUS sama dengan
#   tools/godot_debug_run.py (SCENARIOS / ENGINE_ARGS) dan dropdown
#   .github/workflows/godot-run.yml. Drift-nya dijaga
#   `python3 tools/test_godot_debug_runner.py` (tanpa engine).
extends Node

const MAIN_SCENE := "res://scenes/main.tscn"
## Nama skenario — HARUS sama dengan tools/godot_debug_run.py.
const SCENARIOS: Array = ["menu", "level", "battle", "shop", "scene"]
## Kunci argumen setelah `--` (OS.get_cmdline_user_args()) — HARUS sama dengan
## tools/godot_debug_run.py (ENGINE_ARGS).
const ARG_KEYS: Array = ["scenario", "scene", "level", "seconds", "shot-every",
		"max-shots", "max-frames", "fps", "out", "label"]

## Default kalau tidak ada `--out=`: tetap di dalam user:// supaya tidak ada
## berkas debug yang tercecer di repo kalau dijalankan manual.
const DEFAULT_OUT := "user://debug"

## Batas boot (detik nyata). Kalau tahap persiapan tidak selesai sampai sini,
## harness MELAPOR dan keluar sendiri — jangan pernah menggantung sampai rem
## darurat luar (dulu: langkah CI 30 detik berjalan 9 menit lalu dibunuh tanpa
## satu pun petunjuk). Longgar karena CI tanpa GPU bisa ~4 fps.
const BOOT_DEADLINE := 60.0
## Jejak boot: ditulis ke berkas + flush tiap baris, jadi tetap ada walau
## engine dibunuh paksa (stdout-nya bisa tertahan buffer blok).
const TRACE_FILE := "trace.log"

var scenario: String = "menu"
var scene_path: String = MAIN_SCENE
var level: int = 1
var seconds: float = 30.0
var shot_every: float = 1.0
var max_shots: int = 40
var max_frames: int = 0
var fps_limit: int = 0
var out_dir: String = DEFAULT_OUT
var label: String = "debug"

# SENGAJA tak bertipe (Variant): `_world._on_key(...)` dan
# `_probe.configure(...)` adalah panggilan dinamis ke skrip lain — nilai
# bertipe `Node` akan ditolak compiler GDScript ("Function not found in
# base 'Node'"), sama seperti pola tests/BattleSmokeTest.gd.
@onready var _probe = $Probe

var _world = null
var _failures: Array = []
var _notes: Array = []
var _running: bool = false
var _done: bool = false
var _booted: bool = false
var _boot_ms: int = 0
var _stage: String = "belum mulai"
var _trace_file: FileAccess = null
## Detik JAM GAME (jumlah delta) dan detik JAM DINDING (Time.get_ticks_msec()).
## Batas run memakai jam dinding: Engine.time_scale milik game (hit-stop hero/boss
## menyetelnya ke 0.05, setting Game Speed 0.5x-2x) mengalikan `delta`, jadi
## batas berbasis delta bisa molor 20x — run "30 detik" pernah berjalan 9 menit
## di CI karena itu. Batas game-time tetap dicatat di laporan sebagai info.
var _t: float = 0.0
var _wall: float = 0.0
var _start_ms: int = 0
var _next_status: float = 0.0
var _frames: int = 0


func _ready() -> void:
	# ALWAYS: intro level mem-pause SceneTree, dan run 30 detik yang bekunya
	# sendiri hanya menghasilkan satu screenshot.
	process_mode = Node.PROCESS_MODE_ALWAYS
	_boot_ms = Time.get_ticks_msec()
	_parse_args(OS.get_cmdline_user_args())
	# proses TETAP aktif selama boot: itu yang menjalankan watchdog boot di
	# _process() — kalau _boot() menggantung (menunggu frame yang tidak datang,
	# sinyal yang tidak pernah dipancarkan, input yang tidak ada), kita berhenti
	# dengan pesan yang menyebut TAHAP terakhir, bukan mati dibunuh dari luar.
	set_process(true)
	_boot.call_deferred()


# ══════════════════════════════════════════════════════════════════════════
#  ARGUMEN
# ══════════════════════════════════════════════════════════════════════════

func _parse_args(argv: PackedStringArray) -> void:
	for raw in argv:
		var text := str(raw)
		if not text.begins_with("--"):
			print("[DebugRun] PERINGATAN: argumen tanpa -- dilewati: %s" % text)
			continue
		var body := text.substr(2)
		var eq := body.find("=")
		var key := body if eq < 0 else body.substr(0, eq)
		var value := "" if eq < 0 else body.substr(eq + 1)
		if not ARG_KEYS.has(key):
			print("[DebugRun] PERINGATAN: argumen tak dikenal --%s" % key)
			continue
		match key:
			"scenario":
				if SCENARIOS.has(value):
					scenario = value
				else:
					print("[DebugRun] PERINGATAN: skenario '%s' tidak dikenal "
							% value + "(pilihan: %s) — pakai menu" % str(SCENARIOS))
			"scene":
				scene_path = value if not value.is_empty() else MAIN_SCENE
			"level":
				level = maxi(1, int(value))
			"seconds":
				seconds = maxf(0.0, float(value))
			"shot-every":
				shot_every = maxf(0.0, float(value))
			"max-shots":
				max_shots = maxi(0, int(value))
			"max-frames":
				max_frames = maxi(0, int(value))
			"fps":
				fps_limit = maxi(0, int(value))
			"out":
				out_dir = value if not value.is_empty() else DEFAULT_OUT
			"label":
				label = value


## Path keluaran -> absolut. `res://` / `user://` diglobalisasi, path relatif
## dihitung dari direktori project (godot/), sisanya dibiarkan apa adanya.
func _absolute(path: String) -> String:
	if path.begins_with("res://") or path.begins_with("user://"):
		return ProjectSettings.globalize_path(path)
	if path.is_absolute_path():
		return path
	return ProjectSettings.globalize_path("res://").path_join(path)


# ══════════════════════════════════════════════════════════════════════════
#  BOOT + SKENARIO
# ══════════════════════════════════════════════════════════════════════════

func _boot() -> void:
	out_dir = _absolute(out_dir)
	var err := DirAccess.make_dir_recursive_absolute(out_dir.path_join("shots"))
	if err != OK:
		_hard_fail("tidak bisa membuat direktori keluaran %s (error %d)"
				% [out_dir, err])
		return
	_open_trace()
	_trace("boot: direktori keluaran siap")
	_print_banner()

	_trace("memuat scene %s" % scene_path)
	var packed := load(scene_path) as PackedScene
	if packed == null:
		_hard_fail("scene %s tidak bisa dimuat" % scene_path)
		return
	_world = packed.instantiate()
	if _world == null:
		_hard_fail("scene %s gagal di-instance" % scene_path)
		return
	# proses PAUSABLE eksplisit: root harness ini ALWAYS (lihat _ready), dan
	# tanpa baris ini seluruh gameplay ikut mengabaikan pause intro/pause menu.
	_world.process_mode = Node.PROCESS_MODE_PAUSABLE
	_trace("menambahkan world ke tree")
	add_child(_world)
	await _wait_frames(3)
	_trace("world sudah 3 frame di dalam tree")

	if scenario in ["level", "battle", "shop"]:
		_trace("skenario %s: mulai match" % scenario)
		await _start_match()
		if _done:
			return
		_trace("match siap (state=%s)" % GameManager.state)
	elif scenario == "scene":
		print("[DebugRun] skenario scene: %s apa adanya (tanpa match)"
				% scene_path)
		_trace("skenario scene: apa adanya")

	if fps_limit > 0 and not AppShell.headless():
		# Satu-satunya penulis Engine.max_fps tetap AppShell.apply_fps_limit
		# (dikunci MainEntryParityTest) — harness tidak menyentuh properti itu.
		AppShell.apply_fps_limit(float(fps_limit))
		print("[DebugRun] batas FPS %d lewat AppShell.apply_fps_limit" % fps_limit)
	if _probe != null and _probe.has_method("configure"):
		_probe.configure(out_dir, shot_every, max_shots)
	_running = true
	_booted = true
	_start_ms = Time.get_ticks_msec()
	_next_status = 1.0
	_trace("probe aktif — batas run dimulai")
	print("[DebugRun] mulai · skenario=%s · level=%d · batas %.1f detik NYATA / "
			% [scenario, level, seconds]
			+ "%d frame (time_scale=%.2f — batas detik memakai jam dinding)"
			% [max_frames, Engine.time_scale])


func _start_match() -> void:
	if not _world.has_method("_on_key"):
		_hard_fail("skenario %s butuh scene utama (%s) — Main._on_key tidak ada "
				+ "di %s" % [scenario, MAIN_SCENE, scene_path])
		return
	# `get_first_node_in_group` bertipe Node: memanggil method di luar Node
	# LANGSUNG dari variabel ini bukan sekadar gagal di runtime — analyzer
	# GDScript menolaknya saat skrip dikompilasi ("Function not found in base
	# 'Node'"), dan skrip yang gagal dikompilasi membuat SELURUH harness bisu:
	# scene tetap dimuat, `_ready` tidak pernah jalan, tidak ada report.json,
	# dan run hanya berakhir karena rem darurat. Karena itu pola repo ini
	# (lihat tests/BattleSmokeTest.gd) diikuti: cek `has_method` lebih dulu.
	var connector := get_tree().get_first_node_in_group("game_connector")
	if connector == null:
		_hard_fail("GameManagerConnector tidak ada di grup 'game_connector' — "
				+ "skenario %s butuh %s" % [scenario, MAIN_SCENE])
		return
	if not connector.has_method("start_match"):
		_hard_fail("GameManagerConnector tidak punya start_match() — "
				+ "skenario %s butuh %s" % [scenario, MAIN_SCENE])
		return
	# Pola yang sama dengan tests/BattleSmokeTest.gd: menu utama terbuka
	# (GameManager.in_menu), jadi match dimulai lewat connector seperti pemain
	# menekan PLAY — bukan dengan memanggil internal GameManager.
	connector.start_match(level)
	await _wait_frames(5)
	if GameManager.state != "playing":
		_note("state setelah start_match = '%s' (diharapkan 'playing')"
				% GameManager.state)
	# Intro cinematic membekukan gameplay sampai SPACE/ENTER/klik; debug tidak
	# perlu menunggu tiap kali.
	for _i in range(30):
		var intro = _world.get("_level_intro")
		if not (is_instance_valid(intro) and intro.cinematic_active()):
			break
		_world._on_key(_key(KEY_SPACE))
		await get_tree().process_frame
	if scenario == "battle":
		if not GameManager.try_buy_hero("kaizen"):
			_note("try_buy_hero('kaizen') menolak (gold/unlock) — run dilanjutkan")
		else:
			print("[DebugRun] hero pembuka 'kaizen' dibeli (gold=%d)"
					% int(GameManager.gold))
	elif scenario == "shop":
		# H = buka/tutup toko (satu-satunya hotkey toko, paritas pygame).
		_world._on_key(_key(KEY_H))
		await _wait_frames(2)
		print("[DebugRun] toko dibuka lewat hotkey H")


func _print_banner() -> void:
	print("=".repeat(72))
	print("  [DebugRun] harness debug — jalankan lewat tools/godot_debug_run.py")
	print("  skenario=%s scene=%s level=%d label=%s"
			% [scenario, scene_path, level, label])
	print("  batas: %.1f detik · %d frame · screenshot tiap %.2f s (maks %d)"
			% [seconds, max_frames, shot_every, max_shots])
	print("  engine=%s · tampilan=%s · metode=%s · headless=%s"
			% [str(Engine.get_version_info().get("string", "?")),
			DisplayServer.get_name(),
			str(ProjectSettings.get_setting(
					"rendering/renderer/rendering_method", "?")),
			str(AppShell.headless())])
	print("  keluaran=%s" % out_dir)
	print("=".repeat(72))


# ══════════════════════════════════════════════════════════════════════════
#  LOOP + SELESAI
# ══════════════════════════════════════════════════════════════════════════

func _process(delta: float) -> void:
	if _done:
		return
	if not _booted:
		# Watchdog boot (lihat BOOT_DEADLINE). Tahap terakhir ada di pesan +
		# trace.log, jadi kegagalan selalu menunjuk baris yang salah.
		var boot_s := float(Time.get_ticks_msec() - _boot_ms) / 1000.0
		if boot_s >= BOOT_DEADLINE:
			_hard_fail(("persiapan tidak selesai dalam %.0f detik — tahap "
					+ "terakhir: %s (lihat %s)")
					% [BOOT_DEADLINE, _stage, out_dir.path_join(TRACE_FILE)])
		return
	if not _running:
		return
	_t += delta
	_frames += 1
	_wall = float(Time.get_ticks_msec() - _start_ms) / 1000.0
	if max_frames > 0 and _frames >= max_frames:
		_finish("batas %d frame tercapai" % max_frames)
		return
	if seconds > 0.0 and _wall >= seconds:
		_finish("batas %.1f detik tercapai" % seconds)
		return
	if _wall >= _next_status:
		_next_status = _wall + 1.0
		if _probe != null:
			print(_probe.status_line())


func _finish(reason: String) -> void:
	if _done:
		return
	_done = true
	_running = false
	set_process(false)
	_trace("selesai: %s" % reason)
	if _trace_file != null:
		_trace_file.close()
		_trace_file = null
	if _probe != null:
		_probe.enabled = false
	var report := {}
	if _probe != null and _probe.has_method("build_report"):
		report = _probe.build_report()
	report["scenario"] = scenario
	report["scene"] = scene_path
	report["level"] = level
	report["label"] = label
	report["seconds_requested"] = seconds
	report["max_frames"] = max_frames
	report["harness_frames"] = _frames
	report["harness_seconds_wall"] = snappedf(_wall, 0.1)
	report["harness_seconds_game"] = snappedf(_t, 0.1)
	report["time_scale"] = snappedf(Engine.time_scale, 0.01)
	if _probe != null and shot_every > 0.0 and not _probe.is_headless() \
			and _probe.shots().is_empty():
		# Diminta screenshot tetapi tidak ada satu berkas pun: hampir selalu
		# konteks render (GL di runner) yang gagal — jangan lulus diam-diam.
		_failures.append("screenshot diminta (shot-every=%.2f) tetapi tidak ada "
				% shot_every + "berkas yang tertulis — lihat PERINGATAN di log")
	report["failures"] = _failures.duplicate()
	report["notes"] = _notes.duplicate()
	report["ok"] = _failures.is_empty()
	report["reason"] = reason
	_write_report(report)

	if _failures.is_empty():
		print("[DebugRun] PASS — %s · %d frame · %.1f s nyata · %d screenshot "
				% [reason, _frames, _wall]
				+ "· laporan: %s" % out_dir.path_join("report.json"))
		for note in _notes:
			print("[DebugRun] catatan: %s" % note)
		get_tree().quit(0)
	else:
		for failure in _failures:
			print("[DebugRun] FAIL: %s" % failure)
		print("[DebugRun] FAIL — %s · %d frame · %.1f s nyata"
				% [reason, _frames, _wall])
		get_tree().quit(1)


func _write_report(report: Dictionary) -> void:
	var path := out_dir.path_join("report.json")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		print("[DebugRun] PERINGATAN: report.json tidak bisa ditulis: %s" % path)
		return
	file.store_string(JSON.stringify(report, "\t"))
	file.close()


# ══════════════════════════════════════════════════════════════════════════
#  UTIL
# ══════════════════════════════════════════════════════════════════════════

## Jejak boot: satu baris per tahap, LANGSUNG di-flush. stdout engine bisa
## tertahan di buffer blok (dan hilang saat proses dibunuh), jadi berkas inilah
## yang menjawab "harness berhenti di mana" tanpa perlu mengunduh apa pun.
func _open_trace() -> void:
	_trace_file = FileAccess.open(out_dir.path_join(TRACE_FILE), FileAccess.WRITE)
	if _trace_file == null:
		print("[DebugRun] PERINGATAN: %s tidak bisa ditulis" % TRACE_FILE)


func _trace(stage: String) -> void:
	_stage = stage
	var seconds := float(Time.get_ticks_msec() - _boot_ms) / 1000.0
	print("[DebugRun] %.2fs · %s" % [seconds, stage])
	if _trace_file == null:
		return
	_trace_file.store_line("%.3f	%s" % [seconds, stage])
	_trace_file.flush()


func _note(message: String) -> void:
	_notes.append(message)
	print("[DebugRun] catatan: %s" % message)


func _hard_fail(message: String) -> void:
	_failures.append(message)
	_done = true
	_running = false
	print("[DebugRun] FAIL: %s" % message)
	if _trace_file != null:
		_trace_file.store_line("%.3f\tGAGAL: %s"
				% [float(Time.get_ticks_msec() - _boot_ms) / 1000.0, message])
		_trace_file.flush()
		_trace_file.close()
		_trace_file = null
	get_tree().quit(1)


func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _wait_frames(count: int) -> void:
	for _i in range(count):
		await get_tree().process_frame
