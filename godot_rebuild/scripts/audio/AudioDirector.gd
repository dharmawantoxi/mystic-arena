class_name AudioDirector
extends Node

const SFX := {
	"goblin_spawn": "voice",
	"bullet_hit": "sfx",
	"explosion": "sfx",
	"nexus_hit": "sfx",
	"minion_death": "sfx",
	"tower_destroyed": "sfx",
	"ui_click": "sfx",
	"ui_buy": "sfx",
	"ui_upgrade": "sfx",
	"ui_error": "sfx",
	"ui_sell": "sfx",
	"wave_start": "sfx",
	"victory": "sfx",
	"defeat": "sfx",
	"hero_skill": "sfx",
	"hero_spawn": "sfx",
}
const THROTTLE_MS := {
	"goblin_spawn": 200,
	"minion_death": 120,
	"tower_destroyed": 300,
	"bullet_hit": 40,
	"nexus_hit": 300,
	"ui_click": 50,
}
var bgm := AudioStreamPlayer.new()
var ambient := AudioStreamPlayer.new()
var voices: Array[AudioStreamPlayer] = []
var streams: Dictionary = {}
var settings: Dictionary = GameSettings.DEFAULTS.duplicate()
var background_paused := false
var missing: Array[String] = []
var _paused_players: Array[AudioStreamPlayer] = []
var _last_played: Dictionary = {}
var _next_voice := 0
var _ambient_multiplier := 0.8
var _fade: Tween


func _ready() -> void:
	add_child(bgm)
	add_child(ambient)
	for index in range(32):
		var player := AudioStreamPlayer.new()
		player.name = "SFX%02d" % index
		add_child(player)
		voices.append(player)
	for sound_name: String in SFX:
		var stream := load_stream(sound_name)
		if stream != null:
			streams[sound_name] = stream


func load_stream(sound_name: String) -> AudioStream:
	for extension: String in ["wav", "ogg", "mp3"]:
		var path := "res://assets/sounds/%s.%s" % [sound_name, extension]
		if ResourceLoader.exists(path, "AudioStream"):
			return load(path) as AudioStream
		# Unimported editor/test checkout: raw files still work without an import cache.
		if FileAccess.file_exists(path):
			var bytes := FileAccess.get_file_as_bytes(path)
			if extension == "wav":
				return _read_raw_wav(bytes)
			if extension == "ogg":
				return AudioStreamOggVorbis.load_from_buffer(bytes)
			if extension == "mp3":
				var stream := AudioStreamMP3.new()
				stream.data = bytes
				return stream
	if not sound_name in missing:
		missing.append(sound_name)
	return null


func _loop(stream: AudioStream) -> AudioStream:
	if stream == null:
		return null
	var result := stream.duplicate() as AudioStream
	if result is AudioStreamWAV:
		result.loop_mode = AudioStreamWAV.LOOP_FORWARD
		result.loop_begin = 0
		var bytes_per_frame := 2 if result.format == AudioStreamWAV.FORMAT_16_BITS else 1
		if result.stereo:
			bytes_per_frame *= 2
		result.loop_end = result.data.size() / bytes_per_frame
	elif result is AudioStreamOggVorbis or result is AudioStreamMP3:
		result.loop = true
	return result


func apply_settings(values: Dictionary) -> void:
	settings = values.duplicate()
	_update_volumes()


func _db(volume: float) -> float:
	return linear_to_db(maxf(volume, 0.0001))


func _bgm_volume() -> float:
	return settings.master_volume * settings.bgm_volume


func _ambient_volume() -> float:
	return settings.master_volume * settings.ambient_volume * _ambient_multiplier


func _update_volumes() -> void:
	if _fade != null and _fade.is_valid():
		_fade.kill()
	bgm.volume_db = _db(_bgm_volume())
	ambient.volume_db = _db(_ambient_volume())


func play_bgm(sound_name := "bgm_battle", fade_seconds := 3.0) -> void:
	var stream := _loop(load_stream(sound_name))
	if stream == null:
		return
	if _fade != null and _fade.is_valid():
		_fade.kill()
	bgm.stream = stream
	bgm.volume_db = -80.0 if fade_seconds > 0.0 else _db(_bgm_volume())
	bgm.play()
	if fade_seconds > 0.0:
		_fade = create_tween()
		_fade.tween_property(bgm, "volume_db", _db(_bgm_volume()), fade_seconds)


func play_ambient(sound_name := "ambient_forest", volume_multiplier := 0.8) -> void:
	_ambient_multiplier = volume_multiplier
	ambient.stream = _loop(load_stream(sound_name))
	ambient.volume_db = _db(_ambient_volume())
	if ambient.stream != null:
		ambient.play()


func play_sfx(sound_name: String, volume_multiplier := 1.0, now_ms := -1) -> bool:
	if not streams.has(sound_name):
		return false
	if now_ms < 0:
		now_ms = Time.get_ticks_msec()
	var cooldown: int = THROTTLE_MS.get(sound_name, 50)
	if now_ms - int(_last_played.get(sound_name, -100000)) < cooldown:
		return false
	_last_played[sound_name] = now_ms
	var player := voices[_next_voice]
	_next_voice = (_next_voice + 1) % voices.size()
	var category: String = SFX[sound_name]
	var base: float = settings.sfx_volume if category == "sfx" else 0.5
	player.stream = streams[sound_name]
	player.volume_db = _db(settings.master_volume * base * volume_multiplier)
	player.play()
	return true


func set_background_paused(paused: bool) -> void:
	if paused == background_paused:
		return
	background_paused = paused
	if paused:
		_paused_players.clear()
		for player: AudioStreamPlayer in [bgm, ambient] + voices:
			if player.playing and not player.stream_paused:
				player.stream_paused = true
				_paused_players.append(player)
	else:
		for player: AudioStreamPlayer in _paused_players:
			player.stream_paused = false
		_paused_players.clear()


func stop_all() -> void:
	if _fade != null and _fade.is_valid():
		_fade.kill()
	for player: AudioStreamPlayer in [bgm, ambient] + voices:
		player.stop()
		player.stream_paused = false
	_paused_players.clear()
	background_paused = false


func _read_raw_wav(bytes: PackedByteArray) -> AudioStreamWAV:
	if bytes.size() < 12 or bytes.slice(0, 4).get_string_from_ascii() != "RIFF":
		return null
	if bytes.slice(8, 12).get_string_from_ascii() != "WAVE":
		return null
	var stream := AudioStreamWAV.new()
	var offset := 12
	var has_format := false
	var bits := 16
	while offset + 8 <= bytes.size():
		var chunk := bytes.slice(offset, offset + 4).get_string_from_ascii()
		var length := bytes.decode_u32(offset + 4)
		var start := offset + 8
		if start + length > bytes.size():
			return null
		if chunk == "fmt " and length >= 16:
			if bytes.decode_u16(start) != 1:
				return null
			stream.stereo = bytes.decode_u16(start + 2) == 2
			stream.mix_rate = bytes.decode_u32(start + 4)
			bits = bytes.decode_u16(start + 14)
			has_format = true
		elif chunk == "data" and has_format:
			stream.format = (
				AudioStreamWAV.FORMAT_16_BITS if bits == 16 else AudioStreamWAV.FORMAT_8_BITS
			)
			stream.data = bytes.slice(start, start + length)
			return stream if bits in [8, 16] else null
		offset = start + length + (length % 2)
	return null


func dispose_streams() -> void:
	stop_all()
	for player: AudioStreamPlayer in [bgm, ambient] + voices:
		player.stream = null
	streams.clear()


func _exit_tree() -> void:
	dispose_streams()
