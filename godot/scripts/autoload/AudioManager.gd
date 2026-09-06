# AudioManager.gd — autoload audio: BGM per level (hook bgm_track) + SFX + volume.
#
# Port awal dari _system.py SoundManager (baris 463-620). pygame memuat 24 file
# .wav dari assets/sounds/ lewat SoundManager.load_all(); di Godot file itu
# harus ada DI DALAM project (res://assets/sounds/) — tools/convert_to_godot.py
# yang menyalinnya (folder itu di-gitignore karena duplikat 15 MB dari
# assets/sounds/ repo pygame, sumber kebenarannya tetap di sana).
#
# Sengaja dibuat TIDAK pernah crash kalau aset belum disalin: hook bgm_track
# (_core.py level_data "bgm_track") tetap jalan dan hanya mencatat log, jadi
# alur "pilih level -> tema -> bgm" bisa diuji sebelum aset audio di-import.
#
# Volume sfx/bgm dibaca dari SaveManager.data["settings"] (kunci sudah ada
# sejak awal port, sekarang benar-benar dipakai — default 0.6/0.35 paritas
# SoundManager.__init__ _system.py:493-496).
extends Node

const SOUNDS_DIR := "res://assets/sounds/"
## SFX yang benar-benar dipakai port saat ini (subset load_all _system.py:554-574)
const SFX_NAMES: Array = [
	"ui_click", "ui_error", "ui_buy", "ui_sell", "ui_upgrade",
	"victory", "defeat", "wave_start", "hero_spawn", "nexus_hit",
	"tower_destroyed", "minion_death",
]
## Rate-limit per nama (ms) — paritas SoundManager.throttle_ms _system.py:507-513
const THROTTLE_MS := {
	"ui_click": 50, "minion_death": 120, "tower_destroyed": 300,
	"nexus_hit": 300, "hero_spawn": 200,
}

var sfx_volume: float = 0.6
var bgm_volume: float = 0.35

var _bgm_player: AudioStreamPlayer = null
var _sfx_players: Array = []
var _streams: Dictionary = {}
var _last_played_ms: Dictionary = {}
var _current_bgm: String = ""
var _sounds_available: bool = false


func _ready() -> void:
	# Selalu jalan walau SceneTree pause (menu PAUSE tetap bisa klik SFX).
	process_mode = Node.PROCESS_MODE_ALWAYS
	_bgm_player = AudioStreamPlayer.new()
	_bgm_player.name = "BGM"
	add_child(_bgm_player)
	# Pool 8 kanal SFX (pygame: mixer 32 kanal, 8 cukup untuk subset ini).
	for i in range(8):
		var p := AudioStreamPlayer.new()
		p.name = "SFX%d" % i
		add_child(p)
		_sfx_players.append(p)
	_scan_sounds()
	apply_settings()


## Cek sekali saat boot: file wav harus ADA di res://assets/sounds/ (hasil
## convert_to_godot.py). Kalau belum, semua play_* jadi no-op + log —
## sama seperti SoundManager.enabled=false saat mixer.init() gagal.
func _scan_sounds() -> void:
	var dir := DirAccess.open(SOUNDS_DIR)
	if dir == null:
		# Catatan: tanda kurung WAJIB — di GDScript '%' mengikat lebih kuat
		# daripada '+', jadi tanpa kurung '%s' di baris pertama tak terisi
		# ("not all arguments converted during string formatting").
		push_warning(("[AudioManager] %s belum ada — jalankan tools/convert_to_godot.py "
			+ "agar 24 file .wav disalin. Audio no-op sampai itu.") % SOUNDS_DIR)
		return
	dir.list_dir_begin()
	var file := dir.get_next()
	while not file.is_empty():
		if file.ends_with(".wav"):
			var path := SOUNDS_DIR + file
			var stream := load(path)
			if stream is AudioStream:
				_streams[file.get_basename()] = stream
		file = dir.get_next()
	dir.list_dir_end()
	_sounds_available = not _streams.is_empty()
	if _sounds_available:
		print("[AudioManager] %d file audio dimuat dari %s" % [_streams.size(), SOUNDS_DIR])


## Volume dari save (menu SETTINGS menggeser slider -> sini).
func apply_settings() -> void:
	sfx_volume = SaveManager.get_setting("sfx", 0.6)
	bgm_volume = SaveManager.get_setting("bgm", 0.35)
	_apply_playing_volumes()


## Volume player yang sedang bunyi ikut berubah saat slider digeser live.
func _apply_playing_volumes() -> void:
	_bgm_player.volume_db = linear_to_db(clampf(bgm_volume, 0.0001, 1.0))
	for p in _sfx_players:
		p.volume_db = linear_to_db(clampf(sfx_volume, 0.0001, 1.0))


# ══════════════════════════════════════════════════════════
#  BGM — hook "bgm_track" per level (levels.json)
# ══════════════════════════════════════════════════════════

## GameManager.start_level() memanggil ini dengan levels.json["bgm_track"]
## (semua level saat ini "bgm_battle.wav" — paritas main.py:163/521 yang
## play_bgm('bgm_battle.wav', loop=True) tiap masuk match).
func play_bgm(track_name: String, fade_sec: float = 1.5) -> void:
	if track_name.is_empty():
		return
	if track_name == _current_bgm and _bgm_player.playing:
		return
	if not _sounds_available or not _streams.has(track_name):
		# HOOK: jangan error — level tetap jalan tanpa musik.
		print("[AudioManager] bgm '%s' belum tersedia (aset belum disalin) — hook aktif" % track_name)
		_current_bgm = track_name
		return
	_current_bgm = track_name
	_bgm_player.stream = _streams[track_name]
	_bgm_player.volume_db = linear_to_db(clampf(bgm_volume, 0.0001, 1.0))
	_bgm_player.play()
	if fade_sec > 0.0:
		# fade-in sederhana (pygame pakai fade_ms; di Godot tween volume)
		var from_db := _bgm_player.volume_db
		_bgm_player.volume_db = from_db - 12.0
		var tw := create_tween()
		tw.tween_property(_bgm_player, "volume_db", from_db, fade_sec)


## Paritas SoundManager.stop_bgm(fade_ms) — dipanggil saat menang/kalah
## (_core.py:2285/2291) sebelum sfx victory/defeat dibunyikan.
func stop_bgm(fade_sec: float = 0.5) -> void:
	if not _bgm_player.playing:
		return
	var tw := create_tween()
	tw.tween_property(_bgm_player, "volume_db", -40.0, fade_sec)
	tw.tween_callback(_bgm_stop_now)


func _bgm_stop_now() -> void:
	_bgm_player.stop()
	_bgm_player.volume_db = linear_to_db(clampf(bgm_volume, 0.0001, 1.0))


func pause_bgm(paused: bool) -> void:
	# StreamPaused saat tree pause supaya musik tidak berhenti total lalu
	# menyala ulang aneh — menu PAUSE tetap ingin musik pelan (pygame juga
	# hanya mem-pause BGM saat menu pause, bukan mematikannya).
	_bgm_player.stream_paused = paused


# ══════════════════════════════════════════════════════════
#  SFX
# ══════════════════════════════════════════════════════════

## Paritas SoundManager.play(name, volume_mult): cari kanal kosong, throttle
## nama yang sama biar tidak menumpuk (mis. minion_death tiap frame).
func play_sfx(sound_name: String, volume_mult: float = 1.0) -> void:
	if not _sounds_available or not _streams.has(sound_name):
		return
	var now := Time.get_ticks_msec()
	var limit := int(THROTTLE_MS.get(sound_name, 0))
	if limit > 0:
		var last := int(_last_played_ms.get(sound_name, 0))
		if now - last < limit:
			return
		_last_played_ms[sound_name] = now
	for p in _sfx_players:
		if not p.playing:
			p.stream = _streams[sound_name]
			p.volume_db = linear_to_db(clampf(sfx_volume * volume_mult, 0.0001, 1.0))
			p.play()
			return
