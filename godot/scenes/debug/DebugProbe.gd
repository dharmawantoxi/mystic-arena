# DebugProbe.gd — perekam untuk harness debug (lihat scenes/debug/DebugRun.gd).
#
# Kenapa dipisah dari DebugRun.gd: satu berkas mengurus LIFECYCLE (kapan mulai,
# skenario apa, kapan berhenti, kapan lapor), satu berkas mengurus PENGAMATAN
# (screenshot + cuplikan keadaan). Saat debugging biasanya yang diubah cuma
# "apa yang diamati", dan itu tidak boleh menyentuh jalur produksi.
#
# YANG DIREKAM
#   * `shots/frame_NNNN.png` — isi viewport, tepat SESUDAH frame digambar
#     (RenderingServer.frame_post_draw, resep resmi Godot: get_viewport() ->
#     get_texture() -> get_image()). Headless tidak punya konteks render, jadi
#     screenshot dilewati (bukan gagal) dan report menulis `headless: true`.
#   * cuplikan keadaan tiap SAMPLE_EVERY detik: state, wave, gold, jumlah hero
#     per tim, jumlah minion — kolom yang paling sering ditanya saat "kenapa
#     game-nya begini?".
#
# PENTING: probe ini process_mode ALWAYS (diatur di _ready). Kalau tidak, intro
# level (yang mem-pause tree) akan membekukan perekamnya juga, dan run 30 detik
# hanya menghasilkan satu screenshot.
extends Node

## Jarak antar cuplikan keadaan (detik).
const SAMPLE_EVERY := 0.5
## Frame awal (boot, import, alokasi) tidak dihitung ke statistik FPS.
const FPS_WARMUP := 30

var enabled: bool = false
var out_dir: String = ""
var shot_every: float = 1.0
var max_shots: int = 40

var _headless: bool = false
var _elapsed: float = 0.0
var _frames: int = 0
var _next_shot: float = 0.0
var _next_sample: float = 0.0
var _pending_shot: bool = false
var _shot_failed: bool = false
var _shots: Array = []
var _samples: Array = []
var _fps: Array = []


func _ready() -> void:
	# Lihat catatan "PENTING" di atas.
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(false)


## Dipanggil DebugRun setelah argumen diurai dan scene mulai berjalan.
func configure(dir: String, every: float, shots_max: int) -> void:
	out_dir = dir
	shot_every = every
	max_shots = shots_max
	_headless = DisplayServer.get_name().to_lower().contains("headless") \
			or DisplayServer.get_name().to_lower().contains("dummy")
	_elapsed = 0.0
	_frames = 0
	_next_shot = 0.0
	_next_sample = SAMPLE_EVERY
	_shots.clear()
	_samples.clear()
	_fps.clear()
	enabled = true
	set_process(true)
	print("[DebugRun] probe aktif: screenshot tiap %.2f s (maks %d), %s"
			% [shot_every, max_shots,
			"HEADLESS — tanpa screenshot" if _headless else "berjendela"])
	if shot_every > 0.0 and not _headless:
		# Satu gambar langsung: kalau layar virtual/GPU-nya bermasalah, itu
		# ketahuan di detik pertama, bukan di akhir run 30 detik.
		_request_shot()


func _process(delta: float) -> void:
	if not enabled:
		return
	_elapsed += delta
	_frames += 1
	_fps.append(int(Engine.get_frames_per_second()))
	if _elapsed >= _next_sample:
		_next_sample = _elapsed + SAMPLE_EVERY
		_samples.append(_sample())
	if shot_every > 0.0 and _elapsed >= _next_shot \
			and _shots.size() < max_shots:
		_next_shot = _elapsed + shot_every
		_request_shot()


# ══════════════════════════════════════════════════════════════════════════
#  SCREENSHOT
# ══════════════════════════════════════════════════════════════════════════

func _request_shot() -> void:
	if _headless or _pending_shot or out_dir.is_empty():
		return
	if not RenderingServer.frame_post_draw.is_connected(_on_frame_post_draw):
		RenderingServer.frame_post_draw.connect(_on_frame_post_draw,
				CONNECT_ONE_SHOT)
	_pending_shot = true


## Dipanggil engine TEPAT sesudah frame selesai digambar — satu-satunya saat
## viewport bisa dibaca tanpa balapan dengan renderer.
func _on_frame_post_draw() -> void:
	_pending_shot = false
	if not enabled or not is_inside_tree():
		return
	var viewport := get_viewport()
	if viewport == null:
		_note_shot_failure("viewport tidak tersedia")
		return
	var texture := viewport.get_texture()
	if texture == null:
		_note_shot_failure("ViewportTexture tidak tersedia")
		return
	var image := texture.get_image()
	if image == null:
		_note_shot_failure("get_image() mengembalikan null")
		return
	# Viewport bisa RGBAF/RGBAH (2D HDR, Forward+): PNG butuh 8 bit per kanal.
	if image.get_format() != Image.FORMAT_RGBA8:
		image.convert(Image.FORMAT_RGBA8)
	var file_name := "frame_%04d.png" % (_shots.size() + 1)
	var path := out_dir.path_join("shots").path_join(file_name)
	var err := image.save_png(path)
	if err != OK:
		_note_shot_failure("save_png gagal (%d) di %s" % [err, path])
		return
	_shots.append(file_name)
	print("[DebugRun] shot %d: %s (%dx%d) t=%.1fs"
			% [_shots.size(), file_name, image.get_width(),
			image.get_height(), _elapsed])


func _note_shot_failure(reason: String) -> void:
	if _shot_failed:
		return
	_shot_failed = true
	# Bukan push_error: berjendela tanpa konteks render itu keadaan yang mungkin
	# (mis. GL gagal di runner), dan laporan + baris FAIL di bawah sudah cukup
	# menjelaskan. push_error akan mengotori gerbang log sebagai "SCRIPT ERROR".
	print("[DebugRun] PERINGATAN: screenshot gagal — %s" % reason)


# ══════════════════════════════════════════════════════════════════════════
#  CUPLIKAN KEADAAN
# ══════════════════════════════════════════════════════════════════════════

func _sample() -> Dictionary:
	return {
		"t": snappedf(_elapsed, 0.1),
		"fps": int(Engine.get_frames_per_second()),
		"state": str(GameManager.state),
		"wave": int(GameManager.wave_number),
		"gold": int(GameManager.gold),
		"blue": GameManager.owned_heroes("blue").size(),
		"red": GameManager.owned_heroes("red").size(),
		"heroes": _count_group("heroes"),
		"minions": _count_group("minions"),
		"towers": _count_group("towers"),
	}


## Hitung anggota grup yang masih hidup. HANYA memakai API Node
## (is_instance_valid + is_queued_for_deletion): membaca properti dinamis
## seperti `node.get("is_dead")` pada grup campuran bisa mencetak error engine,
## dan satu baris error di run.log bikin gerbang log (godot_log_gate) gagal —
## alat debug tidak boleh mengotori log yang ia sendiri periksa.
func _count_group(group: String) -> int:
	var live := 0
	for node in get_tree().get_nodes_in_group(group):
		if not is_instance_valid(node):
			continue
		if node.is_queued_for_deletion():
			continue
		live += 1
	return live


## Baris status untuk log (dibaca di tab Actions tanpa mengunduh apa pun).
func status_line() -> String:
	return ("[DebugRun] t=%.1fs frame=%d fps=%d state=%s wave=%d gold=%d "
			+ "hero=%d/%d minion=%d shot=%d") % [
		_elapsed, _frames, int(Engine.get_frames_per_second()),
		str(GameManager.state), int(GameManager.wave_number),
		int(GameManager.gold),
		GameManager.owned_heroes("blue").size(),
		GameManager.owned_heroes("red").size(),
		_count_group("minions"), _shots.size(),
	]


# ══════════════════════════════════════════════════════════════════════════
#  LAPORAN
# ══════════════════════════════════════════════════════════════════════════

func fps_stats() -> Dictionary:
	# Ekor awal (boot + impor resource) tidak mewakili performa gameplay.
	var values := _fps.slice(mini(FPS_WARMUP, _fps.size()), _fps.size())
	if values.is_empty():
		values = _fps
	if values.is_empty():
		return {"fps_avg": 0, "fps_min": 0, "fps_max": 0}
	var total := 0
	var lowest := 2147483647
	var highest := 0
	for value in values:
		total += int(value)
		lowest = mini(lowest, int(value))
		highest = maxi(highest, int(value))
	return {
		"fps_avg": int(round(float(total) / float(values.size()))),
		"fps_min": lowest,
		"fps_max": highest,
	}


## Dipakai DebugRun untuk memutuskan lulus/gagal: "screenshot diminta tetapi
## tidak ada satu pun berkas" itu kegagalan, bukan detail.
func shots() -> Array:
	return _shots.duplicate()


func is_headless() -> bool:
	return _headless


func build_report() -> Dictionary:
	var report := {
		"engine": str(Engine.get_version_info().get("string", "?")),
		"headless": _headless,
		"display_driver": DisplayServer.get_name(),
		"rendering_method": str(ProjectSettings.get_setting(
				"rendering/renderer/rendering_method", "?")),
		"video_adapter": RenderingServer.get_video_adapter_name(),
		"video_api": RenderingServer.get_video_adapter_api_version(),
		"out_dir": out_dir,
		"frames": _frames,
		"elapsed": snappedf(_elapsed, 0.1),
		"shot_every": shot_every,
		"shots": _shots.duplicate(),
		"samples": _samples.duplicate(true),
	}
	report.merge(fps_stats())
	return report
