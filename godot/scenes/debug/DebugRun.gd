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
var _t: float = 0.0
var _frames: int = 0


func _ready() -> void:
	# ALWAYS: intro level mem-pause SceneTree, dan run 30 detik yang bekunya
	# sendiri hanya menghasilkan satu screenshot.
	process_mode = Node.PROCESS_MODE_ALWAYS
	_parse_args(OS.get_cmdline_user_args())
	set_process(false)
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
	_print_banner()

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
	add_child(_world)
	await _wait_frames(3)

	if scenario in ["level", "battle", "shop"]:
		await _start_match()
		if _done:
			return
	elif scenario == "scene":
		print("[DebugRun] skenario scene: %s apa adanya (tanpa match)"
				% scene_path)

	if fps_limit > 0 and not AppShell.headless():
		# Satu-satunya penulis Engine.max_fps tetap AppShell.apply_fps_limit
		# (dikunci MainEntryParityTest) — harness tidak menyentuh properti itu.
		AppShell.apply_fps_limit(float(fps_limit))
		print("[DebugRun] batas FPS %d lewat AppShell.apply_fps_limit" % fps_limit)
	if _probe != null and _probe.has_method("configure"):
		_probe.configure(out_dir, shot_every, max_shots)
	_running = true
	set_process(true)
	print("[DebugRun] mulai · skenario=%s · level=%d · batas %.1f detik / %d frame"
			% [scenario, level, seconds, max_frames])


func _start_match() -> void:
	if not _world.has_method("_on_key"):
		_hard_fail("skenario %s butuh scene utama (%s) — Main._on_key tidak ada "
				+ "di %s" % [scenario, MAIN_SCENE, scene_path])
		return
	var connector := get_tree().get_first_node_in_group("game_connector")
	if connector == null:
		_hard_fail("GameManagerConnector tidak ada di grup 'game_connector' — "
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
	if not _running or _done:
		return
	_t += delta
	_frames += 1
	if max_frames > 0 and _frames >= max_frames:
		_finish("batas %d frame tercapai" % max_frames)
		return
	if seconds > 0.0 and _t >= seconds:
		_finish("batas %.1f detik tercapai" % seconds)
		return
	if _probe != null and int(_t) != int(_t - delta):
		print(_probe.status_line())


func _finish(reason: String) -> void:
	if _done:
		return
	_done = true
	_running = false
	set_process(false)
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
		print("[DebugRun] PASS — %s · %d frame · %d screenshot · laporan: %s"
				% [reason, _frames, report.get("shots", []).size(),
				out_dir.path_join("report.json")])
		for note in _notes:
			print("[DebugRun] catatan: %s" % note)
		get_tree().quit(0)
	else:
		for failure in _failures:
			print("[DebugRun] FAIL: %s" % failure)
		print("[DebugRun] FAIL — %s · %d frame" % [reason, _frames])
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

func _note(message: String) -> void:
	_notes.append(message)
	print("[DebugRun] catatan: %s" % message)


func _hard_fail(message: String) -> void:
	_failures.append(message)
	_done = true
	_running = false
	print("[DebugRun] FAIL: %s" % message)
	get_tree().quit(1)


func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	return event


func _wait_frames(count: int) -> void:
	for _i in range(count):
		await get_tree().process_frame
