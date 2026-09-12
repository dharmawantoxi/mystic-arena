# AudioManager.gd — autoload audio: BGM per level (hook bgm_track) + SFX + volume.
#
# Port awal dari _system.py SoundManager (baris 463-620). pygame memuat 24
# berkas audio dari assets/sounds/ lewat SoundManager.load_all(); di Godot file
# itu harus ada DI DALAM project (res://assets/sounds/) —
# tools/convert_to_godot.py yang menyalinnya (folder itu di-gitignore karena
# duplikat 15 MB dari assets/sounds/ repo pygame, sumber kebenarannya tetap di
# sana). Nama berkas di assets/sounds/ TIDAK selalu jujur: SDL_mixer mengendus
# isi berkas, jadi pygame santai saja memutar 7 Ogg Vorbis dan 1 MP3 yang
# bernama ".wav". Godot memilih importer dari EKSTENSI, sehingga converter
# meluruskan ekstensi salinannya (16 .wav + 7 .ogg + 1 .mp3) dan pemindaian di
# bawah menerima ketiganya.
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
## Ekstensi yang importer audio Godot 4.3 kenal: WAV (AudioStreamWAV),
## Ogg Vorbis (AudioStreamOggVorbis), MP3 (AudioStreamMP3). Salinan dari
## assets/sounds/ bisa bercampur ketiganya — lihat audio_container_ext() di
## tools/convert_to_godot.py. Kunci _streams tetap nama TANPA ekstensi
## (get_basename), jadi play("ui_click") tidak peduli kontainernya apa.
const AUDIO_EXTS: Array = [".wav", ".ogg", ".mp3"]
## Seluruh berkas yang dimuat SoundManager.load_all (_system.py:543-574) +
## 7 suara tempur mobile/combat_audio.py. Hanya dokumentasi: _scan_sounds()
## memuat apa pun yang ada di folder, jadi berkas baru langsung kebaca.
const SFX_NAMES: Array = [
	# UI (paritas load_all 'UI')
	"ui_click", "ui_error", "ui_buy", "ui_sell", "ui_upgrade",
	# Events
	"victory", "defeat", "wave_start",
	# Unit
	"hero_spawn", "hero_skill", "goblin_spawn", "minion_death",
	# Tempur (mobile/combat_audio.py — berkas terpisah, bukan SoundManager)
	"minion_hit", "hero_melee", "hero_ranged",
	"tower_archer", "tower_cannon", "tower_ice", "tower_mage",
	# Benturan
	"nexus_hit", "tower_destroyed", "explosion", "bullet_hit",
]
## Rate-limit per nama (ms) — paritas SoundManager.throttle_ms _system.py:507-513.
## Nama yang tidak terdaftar pakai THROTTLE_DEFAULT, sama seperti pygame yang
## menulis `self.throttle_ms.get(name, 50)` (_system.py:578).
const THROTTLE_MS := {
	"goblin_spawn": 200, "minion_death": 120, "tower_destroyed": 300,
	"bullet_hit": 40, "nexus_hit": 300, "ui_click": 50, "hero_spawn": 200,
	# "explosion" tidak ada di pygame (dipakai ledakan boss _render.py:1764-1769
	# yang memang satu kali per boss). 120 ms di sini supaya splash cannon
	# beruntun dari beberapa menara tidak menumpuk jadi dengung.
	"explosion": 120,
}
const THROTTLE_DEFAULT := 50

## Volume master pygame (SoundManager.master_volume _system.py:493). Semua
## suara pygame = master × kategori × volume_mult, jadi tanpa pengali ini
## Godot terdengar ~43% lebih keras daripada pygame.
const MASTER_VOLUME_DEFAULT := 0.7
## Nilai RUNTIME — pygame punya slider "Master Volume" di SETTINGS; port
## Godot mematahkannya lewat settings key "master" (apply_settings).
var master_volume: float = MASTER_VOLUME_DEFAULT

## Volume kategori 'ambient' pygame (SoundManager.ambient_volume
## _system.py:497). Sengaja TIDAK dibaca dari SaveManager: pygame juga tidak
## punya slider ambient, hanya master/sfx/bgm.
const AMBIENT_VOLUME := 0.25
## Nama berkas ambient satu-satunya di repo pygame
## (load_all: load('ambient_forest', 'ambient_forest.wav', 'ambient')
## _system.py:551, dipanggil main.py:164).
const AMBIENT_TRACK := "ambient_forest"
## volume_mult di call site main.py:164 — play_ambient(..., volume_mult=0.8)
const AMBIENT_MULT := 0.8
## fade_ms pygame: masuk 2000 ms (channel.play fade_ms=2000, _system.py:704),
## keluar 1500 ms (stop_ambient fade_ms=1500, _system.py:706-710).
const AMBIENT_FADE_IN := 2.0
const AMBIENT_FADE_OUT := 1.5

# ══════════════════════════════════════════════════════════
#  SUARA TEMPUR — port mobile/combat_audio.py (skema v35)
# ══════════════════════════════════════════════════════════
# pygame memisahkan 7 suara tempur dari SoundManager karena frekuensinya
# tinggi (tiap serangan/tembakan). Tiga pengamannya ikut diport:
#   1. jeda per jenis (minion 140 ms, menara 110 ms, hero 90 ms)
#   2. anggaran 4 suara baru per frame
#   3. volume dasar per jenis (0.50 - 0.78)
## jenis -> {volume: volume dasar, throttle_ms: jeda minimum}
## (paritas combat_audio._KONFIG, combat_audio.py:41-49)
const COMBAT_SFX := {
	"hero_melee": {"volume": 0.78, "throttle_ms": 90},
	"hero_ranged": {"volume": 0.72, "throttle_ms": 90},
	"tower_archer": {"volume": 0.62, "throttle_ms": 110},
	"tower_cannon": {"volume": 0.62, "throttle_ms": 110},
	"tower_ice": {"volume": 0.62, "throttle_ms": 110},
	"tower_mage": {"volume": 0.62, "throttle_ms": 110},
	"minion_hit": {"volume": 0.50, "throttle_ms": 140},
}
## Anggaran suara tempur baru per frame (combat_audio._sisa_frame = 4)
const COMBAT_BUDGET := 4
## Ambang jarak melee/ranged (combat_audio.AMBANG_RANGED)
const AMBIG_RANGED := 100.0

var sfx_volume: float = 0.6
## Paritas SoundManager.voice_volume (_system.py:495): kategori 'voice'
## (_system.py:599-604) dikali master saat play. Repo tidak punya file
## berkategori voice, jadi variabel ini (sengaja) tidak punya konsumen —
## di pygame keadaannya sama; yang diport adalah persist setting-nya.
var voice_volume: float = 0.5
var bgm_volume: float = 0.35

## Status pause yang DIMINTA — paritas `mixer.pause()/unpause()` main.py.
## Disimpan terpisah dari `stream_paused` engine karena AudioStreamPlayer
## MENGABAIKAN `stream_paused` saat tidak ada playback aktif (mis. aset .wav
## belum disalin converter, atau BGM belum pernah diputar): nilainya tidak
## bisa dibaca balik dan pause jadi hilang begitu musik akhirnya mulai.
## Flag ini selalu benar, dan diterapkan ulang tiap kali player di-play.
var bgm_paused: bool = false
var ambient_paused: bool = false

var _bgm_player: AudioStreamPlayer = null
## Player ambient TERPISAH dari BGM — paritas pygame yang memakai
## ambient_channel sendiri (_system.py:504/701) supaya musik dan suara
## lingkungan bisa hidup bersamaan dan di-fade sendiri-sendiri.
var _ambient_player: AudioStreamPlayer = null
## Tween fade ambient yang sedang jalan; disimpan supaya start cepat setelah
## stop tidak diserobot fade lama (tween Godot tetap jalan walau player
## sudah di-play ulang).
var _ambient_tween: Tween = null
var _sfx_players: Array = []
var _streams: Dictionary = {}
var _last_played_ms: Dictionary = {}
var _current_bgm: String = ""
var _sounds_available: bool = false
## Sisa anggaran suara tempur frame ini (combat_audio._sisa_frame)
var _combat_budget: int = COMBAT_BUDGET
## Statistik penolakan, dicetak sekali per 10 detik (paritas combat_audio.stats)
var _combat_stats := {"main": 0, "tolak_jeda": 0, "tolak_anggaran": 0, "tolak_kanal": 0}
var _stats_timer: float = 0.0


func _ready() -> void:
	# Selalu jalan walau SceneTree pause (menu PAUSE tetap bisa klik SFX).
	process_mode = Node.PROCESS_MODE_ALWAYS
	_bgm_player = AudioStreamPlayer.new()
	_bgm_player.name = "BGM"
	add_child(_bgm_player)
	_ambient_player = AudioStreamPlayer.new()
	_ambient_player.name = "Ambient"
	add_child(_ambient_player)
	# Pool 16 kanal SFX (pygame: mixer 32 kanal; 16 cukup untuk suara tempur
	# yang sudah dibatasi anggaran 4/frame + throttle per jenis).
	for i in range(16):
		var p := AudioStreamPlayer.new()
		p.name = "SFX%d" % i
		add_child(p)
		_sfx_players.append(p)
	# Loop ambient dikendalikan sendiri (lihat _on_ambient_finished).
	_ambient_player.finished.connect(_on_ambient_finished)
	_scan_sounds()
	apply_settings()


## Reset anggaran suara tempur tiap frame (paritas combat_audio.new_frame(),
## dipanggil main.py sekali per iterasi loop). Di Godot cukup di sini supaya
## tidak ada yang lupa memanggilnya dari scene.
func _process(delta: float) -> void:
	_combat_budget = COMBAT_BUDGET
	_stats_timer += delta
	if _stats_timer >= 10.0:
		_stats_timer = 0.0
		_report_stats()


## Cek sekali saat boot: berkas audio harus ADA di res://assets/sounds/ (hasil
## convert_to_godot.py). Kalau belum, semua play_* jadi no-op + log —
## sama seperti SoundManager.enabled=false saat mixer.init() gagal.
func _scan_sounds() -> void:
	var dir := DirAccess.open(SOUNDS_DIR)
	if dir == null:
		# Catatan: tanda kurung WAJIB — di GDScript '%' mengikat lebih kuat
		# daripada '+', jadi tanpa kurung '%s' di baris pertama tak terisi
		# ("not all arguments converted during string formatting").
		push_warning(("[AudioManager] %s belum ada — jalankan tools/convert_to_godot.py "
			+ "--assets agar 24 berkas audio disalin. Audio no-op sampai itu.") % SOUNDS_DIR)
		return
	dir.list_dir_begin()
	var file := dir.get_next()
	while not file.is_empty():
		# BUKAN hanya ".wav": 8 dari 24 berkas pygame sebenarnya Ogg Vorbis /
		# MP3 dan converter menamainya sesuai kontainer supaya Godot mau
		# mengimpornya (kalau dipaksa .wav, importer WAV menolak dengan
		# "Not a WAV file ... found 'OggS'" dan 8 SFX itu senyap).
		if AUDIO_EXTS.has(file.get_extension().to_lower()):
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
	master_volume = SaveManager.get_setting("master", MASTER_VOLUME_DEFAULT)
	sfx_volume = SaveManager.get_setting("sfx", 0.6)
	voice_volume = SaveManager.get_setting("voice", 0.5)
	bgm_volume = SaveManager.get_setting("bgm", 0.35)
	_apply_playing_volumes()


## Volume player yang sedang bunyi ikut berubah saat slider digeser live.
## Tidak ada tulis file di sini — SaveManager hanya dibaca, jadi menggeser
## slider SETTINGS tidak memicu I/O per frame.
func _apply_playing_volumes() -> void:
	_bgm_player.volume_db = _db(master_volume * bgm_volume)
	if _ambient_player != null and _ambient_player.playing:
		_ambient_player.volume_db = _ambient_db()
	for p in _sfx_players:
		p.volume_db = _db(master_volume * sfx_volume)


## Volume linear -> dB dengan clamp (0 linear = -80 dB, bukan -inf).
static func _db(linear: float) -> float:
	return linear_to_db(clampf(linear, 0.0001, 1.0))


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
	# levels.json/AppShell menulis NAMA BERKAS ("bgm_battle.wav") sedangkan
	# kunci _streams adalah nama tanpa ekstensi — tanpa normalisasi ini BGM
	# tidak pernah ketemu dan boot selalu mencetak "belum tersedia" walau 24
	# berkas audio sudah disalin. _current_bgm tetap menyimpan nama apa adanya
	# (dikunci MainEntryParityTest == AppShell.BOOT_BGM).
	var key := track_name.get_basename()
	if not _sounds_available or not _streams.has(key):
		# HOOK: jangan error — level tetap jalan tanpa musik.
		print("[AudioManager] bgm '%s' tidak tersedia (%s) — hook aktif" % [
			track_name,
			"aset belum disalin" if not _sounds_available
				else "tidak ada di %d stream termuat" % _streams.size()])
		_current_bgm = track_name
		return
	_current_bgm = track_name
	_bgm_player.stream = _streams[key]
	# pygame play_bgm: set_volume(master_volume * bgm_volume) — _system.py:632
	_bgm_player.volume_db = _db(master_volume * bgm_volume)
	_bgm_player.play()
	# Terapkan status pause yang tertunda (mis. app ke latar sebelum track
	# ini sempat diputar).
	_bgm_player.stream_paused = bgm_paused
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
	_bgm_player.volume_db = _db(master_volume * bgm_volume)


func pause_bgm(paused: bool) -> void:
	# StreamPaused saat tree pause supaya musik tidak berhenti total lalu
	# menyala ulang aneh — menu PAUSE tetap ingin musik pelan (pygame juga
	# hanya mem-pause BGM saat menu pause, bukan mematikannya).
	bgm_paused = paused
	if _bgm_player.playing:
		# Tanpa penjaga ini, `stream_paused` hilang (engine mengabaikannya
		# saat tidak ada playback) dan musik menyala lagi begitu diputar.
		_bgm_player.stream_paused = paused


# ══════════════════════════════════════════════════════════
#  AMBIENT LOOP — port SoundManager.play_ambient (_system.py:688-710)
# ══════════════════════════════════════════════════════════
# pygame memutar 'ambient_forest' sekali saat masuk match (main.py:164) di
# kanal khusus, loop tanpa henti, volume master × ambient_volume × 0.8.
# Di Godot: AudioStreamPlayer sendiri + loop dipaksa lewat finished ->
# play() (stream .wav hasil import belum tentu punya loop=true, jadi jangan
# bergantung pada properti resource).
#
# CATATAN: play_positional (_system.py:615-629) SENGAJA tidak diport —
# tidak ada satu pun call site di repo pygame, jadi itu dead code.

## Volume akhir ambient dalam dB (master × ambient × volume_mult call site).
func _ambient_db(mult: float = AMBIENT_MULT) -> float:
	return _db(master_volume * AMBIENT_VOLUME * mult)


## Mulai loop ambient. GameManager.start_level() memanggilnya tiap masuk
## match, sama seperti main.py:164 yang memanggil sekali saat game mulai.
## Kalau track sudah berbunyi, panggilan berikutnya diabaikan (pygame
## menghentikan kanal lama lalu memutar ulang; di sini tidak perlu karena
## track-nya cuma satu dan restart bikin loop "meloncat").
func play_ambient(track_name: String = AMBIENT_TRACK, volume_mult: float = AMBIENT_MULT) -> void:
	if not _sounds_available or not _streams.has(track_name):
		# HOOK sama seperti play_bgm: aset belum disalin -> jangan error.
		print("[AudioManager] ambient '%s' belum tersedia (aset belum disalin)" % track_name)
		return
	if _ambient_player.playing and _ambient_player.stream == _streams[track_name]:
		return
	_kill_ambient_tween()
	_ambient_player.stream = _streams[track_name]
	var target := _ambient_db(volume_mult)
	# fade-in 2 detik (pygame fade_ms=2000): mulai pelan lalu naik.
	_ambient_player.volume_db = target - 18.0
	_ambient_player.play()
	_ambient_player.stream_paused = ambient_paused
	_ambient_tween = create_tween()
	_ambient_tween.tween_property(_ambient_player, "volume_db", target, AMBIENT_FADE_IN)


## Loop manual: sinyal finished -> putar lagi (pygame loops=-1).
## Disambung di _ready supaya berlaku untuk semua track ambient.
func _on_ambient_finished() -> void:
	if _ambient_player.stream != null:
		_ambient_player.play()
		# play() membuat playback baru: status pause harus diterapkan ulang.
		_ambient_player.stream_paused = ambient_paused


## Paritas stop_ambient(fade_ms=1500) — dipanggil GameManager.end_match()
## dan return_to_menu(), pasangan dari stop_bgm().
func stop_ambient(fade_sec: float = AMBIENT_FADE_OUT) -> void:
	if _ambient_player == null or not _ambient_player.playing:
		return
	_kill_ambient_tween()
	_ambient_tween = create_tween()
	_ambient_tween.tween_property(_ambient_player, "volume_db", -60.0, fade_sec)
	_ambient_tween.tween_callback(_ambient_stop_now)


func _ambient_stop_now() -> void:
	_ambient_player.stop()
	_ambient_player.volume_db = _ambient_db()


## Hentikan fade yang sedang jalan supaya tidak dua tween menulis volume_db
## player yang sama (mis. return_to_menu lalu start_level cepat).
func _kill_ambient_tween() -> void:
	if _ambient_tween != null and _ambient_tween.is_valid():
		_ambient_tween.kill()
	_ambient_tween = null


## Ambient ikut senyap saat menu PAUSE (sama seperti pause_bgm).
func pause_ambient(paused: bool) -> void:
	ambient_paused = paused
	if _ambient_player.playing:
		_ambient_player.stream_paused = paused


# ══════════════════════════════════════════════════════════
#  SFX
# ══════════════════════════════════════════════════════════

## Paritas SoundManager.play(name, volume_mult) _system.py:571-600: cari kanal
## kosong, throttle nama yang sama biar tidak menumpuk (mis. minion_death tiap
## frame). Volume akhir = MASTER × sfx_volume × volume_mult (pygame: master ×
## kategori × volume_mult, kategori sfx = sfx_volume).
## `force` = lewati throttle. Dipakai kejadian sekali-per-match yang tidak
## boleh tertelan suara berulang: ledakan kematian boss berbagi nama 'explosion'
## dengan splash cannon (throttle 120 ms), jadi tanpa force boss bisa mati
## dalam diam kalau ada meriam yang baru saja mengenai target.
func play_sfx(sound_name: String, volume_mult: float = 1.0, force: bool = false) -> void:
	if not _sounds_available or not _streams.has(sound_name):
		return
	var now := Time.get_ticks_msec()
	if not force:
		var limit := int(THROTTLE_MS.get(sound_name, THROTTLE_DEFAULT))
		var last := int(_last_played_ms.get(sound_name, 0))
		if now - last < limit:
			return
	_last_played_ms[sound_name] = now
	for p in _sfx_players:
		if not p.playing:
			p.stream = _streams[sound_name]
			p.volume_db = _db(master_volume * sfx_volume * volume_mult)
			p.play()
			return


# ══════════════════════════════════════════════════════════
#  SFX TEMPUR — port combat_audio.play(jenis, volume_mult)
# ══════════════════════════════════════════════════════════

## Bunyikan satu suara tempur (hero_melee/hero_ranged/tower_*/minion_hit).
## Tiga pengaman combat_audio.py ikut jalan: jeda per jenis, anggaran
## 4/frame, dan kanal terbatas (tolak_kanal). Return false kalau ditolak.
func play_combat(kind: String, volume_mult: float = 1.0) -> bool:
	if not _sounds_available or not _streams.has(kind):
		return false
	var cfg = COMBAT_SFX.get(kind)
	if not (cfg is Dictionary):
		# Bukan jenis tempur -> jalur SoundManager biasa. play_sfx() void,
		# jadi TIDAK boleh `return play_sfx(...)`: mengembalikan ekspresi void
		# dari fungsi bertipe `-> bool` adalah compile error di Godot 4
		# (gdparse hanya memeriksa sintaks, jadi tidak menangkapnya).
		play_sfx(kind, volume_mult)
		return true
	var now := Time.get_ticks_msec()
	if now - int(_last_played_ms.get(kind, -99999)) < int(cfg["throttle_ms"]):
		_combat_stats["tolak_jeda"] += 1
		return false
	if _combat_budget <= 0:
		_combat_stats["tolak_anggaran"] += 1
		return false
	for p in _sfx_players:
		if not p.playing:
			p.stream = _streams[kind]
			# combat_audio: dasar × volume_mult × (master × sfx_volume)
			p.volume_db = _db(master_volume * sfx_volume
				* float(cfg["volume"]) * volume_mult)
			p.play()
			_last_played_ms[kind] = now
			_combat_budget -= 1
			_combat_stats["main"] += 1
			return true
	_combat_stats["tolak_kanal"] += 1
	return false


## Jenis suara tembakan menara (paritas combat_audio.jenis_tower:
## tipe tak dikenal jatuh ke archer).
## Bukan `static`: method publik autoload di repo ini instance method semua
## (lihat TowerDB.build_cost/CombatSystem.enemies_in_radius), dan dipanggil
## dari script lain sebagai `AudioManager.tower_sfx(...)`.
func tower_sfx(tower_type: String) -> String:
	match tower_type:
		"cannon": return "tower_cannon"
		"ice": return "tower_ice"
		"mage": return "tower_mage"
		_: return "tower_archer"


## Jenis suara serangan dasar hero/boss (paritas combat_audio.play_hero_basic
## + jenis_serangan): flag is_melee_hero lebih dulu, kalau tidak ada pakai
## ambang jarak AMBANG_RANGED = 100. `is_melee` = null untuk boss (tidak punya
## flag itu; pygame juga memakai jangkauan di BaseBoss._suara_serangan).
func basic_attack_sfx(is_melee, attack_range: float) -> String:
	if is_melee != null:
		return "hero_melee" if bool(is_melee) else "hero_ranged"
	return "hero_ranged" if attack_range >= AMBIG_RANGED else "hero_melee"


## Ringkasan penolakan suara tempur, dicetak 10 detik sekali (bukan per event)
## supaya log tidak kebanjiran — paritas combat_audio.ringkas().
func _report_stats() -> void:
	var s := _combat_stats
	var tolak := int(s["tolak_jeda"]) + int(s["tolak_anggaran"]) + int(s["tolak_kanal"])
	if int(s["main"]) == 0 and tolak == 0:
		return
	print("[AudioManager] suara tempur 10 dtk: main %d · ditolak %d (jeda %d / anggaran %d / kanal %d)"
		% [s["main"], tolak, s["tolak_jeda"], s["tolak_anggaran"], s["tolak_kanal"]])
	_combat_stats = {"main": 0, "tolak_jeda": 0, "tolak_anggaran": 0, "tolak_kanal": 0}
