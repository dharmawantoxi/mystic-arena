extends Node
## Migrated audio facade for the Godot client.
## Keeps gameplay code independent from AudioStreamPlayer details and safely
## degrades when a platform has no audio device.

const ROOT := "res://assets/audio/"
const DEFAULT_MASTER_VOLUME := 0.7
const DEFAULT_SFX_VOLUME := 0.6
const DEFAULT_BGM_VOLUME := 0.35
const AMBIENT_VOLUME := 0.25
const VOLUME_STEP := 0.1
const MIN_VOLUME_DB := -80.0
const VOLUME_CHANNELS := ["master", "sfx", "bgm"]
const STREAMS := {
	"bgm_battle": "bgm_battle.wav",
	"ambient_forest": "ambient_forest.mp3",
	"victory": "victory.ogg",
	"defeat": "defeat.wav",
	"ui_click": "ui_click.ogg",
	"ui_buy": "ui_buy.ogg",
	"ui_error": "ui_error.ogg",
	"ui_sell": "ui_sell.ogg",
	"ui_upgrade": "ui_upgrade.ogg",
	"wave_start": "wave_start.wav",
	"hero_skill": "hero_skill.wav",
	"nexus_hit": "nexus_hit.wav",
}

## Layer 9ar: `combat_audio.init()` raises the mixer to 24 channels and
## `play()` takes an idle one without stealing; the pool mirrors that.
const COMBAT_CHANNELS := 24
## Source `SoundManager.throttle_ms` default for a name it does not list.
const SFX_THROTTLE_MS := 50
## Layer 9ci: `SoundManager.throttle_ms` itself (ms per sound name).
const THROTTLE_MS := {
	"goblin_spawn": 200,
	"minion_death": 120,
	"tower_destroyed": 300,
	"bullet_hit": 40,
	"nexus_hit": 300,
	"ui_click": 50,
}
## `SoundManager.voice_volume` / the fade timings of the BGM + ambient paths.
const VOICE_VOLUME := 0.5
const BGM_FADE_MS := 2000
const BGM_STOP_FADE_MS := 1000
const AMBIENT_FADE_MS := 2000
const AMBIENT_STOP_FADE_MS := 1500
## `SoundManager.play_positional`: full falloff at 800 px, floored at 0.15 and silent
## past the radius.
const POSITIONAL_MAX_DISTANCE := 800.0
const POSITIONAL_MIN_VOLUME := 0.15

var music: AudioStreamPlayer
var effects: AudioStreamPlayer
var ambient: AudioStreamPlayer
var combat_players: Array[AudioStreamPlayer] = []
var enabled := true
var master_volume := DEFAULT_MASTER_VOLUME
var sfx_volume := DEFAULT_SFX_VOLUME
var bgm_volume := DEFAULT_BGM_VOLUME
var _sfx_throttle := {}


func _ready() -> void:
	music = _make_player("Music")
	effects = _make_player("Effects")
	ambient = _make_player("Ambient")
	_apply_mix()
	play_music("bgm_battle")
	play_ambient("ambient_forest")


func _exit_tree() -> void:
	shutdown()


func shutdown() -> void:
	enabled = false
	var players: Array[AudioStreamPlayer] = [music, effects, ambient]
	players.append_array(combat_players)
	for player in players:
		if is_instance_valid(player):
			player.stop()
			player.stream = null


func _make_player(player_name: String) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.name = player_name
	add_child(player)
	return player


func _stream(key: String) -> AudioStream:
	if not STREAMS.has(key):
		return null
	return load(ROOT + String(STREAMS[key])) as AudioStream


## `SoundManager.throttle_ms.get(name, 50)`.
static func throttle_ms_for(sound_name: String) -> int:
	return int(THROTTLE_MS.get(sound_name, SFX_THROTTLE_MS))


## `SoundManager.play_positional`'s distance term: linear falloff from the listener,
## floored at `POSITIONAL_MIN_VOLUME`; 0 past `max_distance` (the source returns early).
static func positional_falloff(
	x: float,
	y: float,
	player_x: float,
	player_y: float,
	max_distance: float = POSITIONAL_MAX_DISTANCE
) -> float:
	var distance := Vector2(x - player_x, y - player_y).length()
	if max_distance <= 0.0 or distance > max_distance:
		return 0.0
	return maxf(POSITIONAL_MIN_VOLUME, 1.0 - distance / max_distance)


## Source `play_positional`: distance term times the caller's multiplier, clamped.
static func positional_volume(
	x: float,
	y: float,
	player_x: float,
	player_y: float,
	max_distance: float = POSITIONAL_MAX_DISTANCE,
	volume_mult: float = 1.0
) -> float:
	var falloff := positional_falloff(x, y, player_x, player_y, max_distance)
	if falloff <= 0.0:
		return 0.0
	return clampf(volume_mult * falloff, 0.0, 1.0)


## Source `_volume_global`: master*sfx, 0 when sound is disabled.
func combat_global_volume() -> float:
	if not enabled:
		return 0.0
	return master_volume * sfx_volume


## Source `pygame.mixer.find_channel()` availability over the 24 channels.
func combat_free_channels() -> int:
	if not enabled:
		return 0
	var busy := 0
	for player in combat_players:
		if is_instance_valid(player) and player.playing:
			busy += 1
	return COMBAT_CHANNELS - busy


## Plays one combat file on an idle channel at an absolute linear volume (the
## gate already folded master*sfx in, like `Sound.set_volume` in the source).
func play_combat(file_name: String, linear_volume: float) -> bool:
	if not enabled or file_name.is_empty():
		return false
	var player := _idle_combat_player()
	if player == null:
		return false
	var stream := load(ROOT + file_name) as AudioStream
	if stream == null:
		return false
	player.stream = stream
	_apply_player_volume(player, linear_volume)
	player.play()
	return true


func _idle_combat_player() -> AudioStreamPlayer:
	for player in combat_players:
		if is_instance_valid(player) and not player.playing:
			return player
	if combat_players.size() >= COMBAT_CHANNELS:
		return null
	var player := _make_player("Combat%d" % combat_players.size())
	combat_players.append(player)
	return player


func play_music(key: String) -> void:
	if not enabled or music == null:
		return
	var stream := _stream(key)
	if stream == null:
		return
	music.stream = stream
	music.play()


func play_ambient(key: String) -> void:
	if not enabled or ambient == null:
		return
	var stream := _stream(key)
	if stream == null:
		return
	ambient.stream = stream
	ambient.play()


func play(key: String) -> void:
	if not enabled or effects == null:
		return
	var stream := _stream(key)
	if stream == null:
		return
	effects.stream = stream
	# A scaled skill cast leaves its own volume on the shared player; a plain
	# play restores the source mix volume (master*sfx).
	_apply_player_volume(effects, combat_global_volume())
	effects.play()


## Source `SoundManager.play(name, volume_mult)`: the per-name throttle from
## `throttle_ms` (50 ms for a name it does not list) and a
## `master * category * volume_mult` volume, clamped. Layer 9ci added the real table
## and the `voice`/`ambient` category volumes; `hero_skill` is not listed there, so the
## Pygame skill cast keeps its 50 ms gate.
func play_scaled(key: String, volume_mult: float, category: String = "sfx") -> bool:
	if not enabled or effects == null:
		return false
	var stream := _stream(key)
	if stream == null:
		return false
	var now := Time.get_ticks_msec()
	var spacing := throttle_ms_for(key)
	var last := int(_sfx_throttle.get(key, -spacing))
	if now - last < spacing:
		return false
	_sfx_throttle[key] = now
	var base_volume := sfx_volume
	if category == "voice":
		base_volume = VOICE_VOLUME
	elif category == "ambient":
		base_volume = AMBIENT_VOLUME
	effects.stream = stream
	_apply_player_volume(effects, clampf(master_volume * base_volume * volume_mult, 0.0, 1.0))
	effects.play()
	return true


## `SoundManager.play_positional(name, x, y, player_x, player_y, max_distance,
## volume_mult)`: the falloff feeds the ordinary throttled `play`.
func play_positional(
	key: String,
	x: float,
	y: float,
	player_x: float,
	player_y: float,
	max_distance: float = POSITIONAL_MAX_DISTANCE,
	volume_mult: float = 1.0
) -> bool:
	var falloff := positional_falloff(x, y, player_x, player_y, max_distance)
	if falloff <= 0.0:
		return false
	return play_scaled(key, volume_mult * falloff)


## `SoundManager.pause_bgm` / `resume_bgm`.
func pause_music() -> void:
	if enabled and music != null and music.playing:
		music.stream_paused = true


func resume_music() -> void:
	if enabled and music != null and music.stream_paused:
		music.stream_paused = false


## `SoundManager.stop_all`: mixer channels and the music stream.
func stop_all() -> void:
	if not enabled:
		return
	effects.stop()
	ambient.stop()
	music.stop()
	for player in combat_players:
		if is_instance_valid(player):
			player.stop()


func get_volume(channel: String) -> float:
	match channel:
		"master":
			return master_volume
		"sfx":
			return sfx_volume
		"bgm":
			return bgm_volume
		_:
			return -1.0


func set_mix_volume(channel: String, value: float) -> bool:
	if not VOLUME_CHANNELS.has(channel) or not is_finite(value):
		return false
	var clamped := clampf(value, 0.0, 1.0)
	match channel:
		"master":
			master_volume = clamped
		"sfx":
			sfx_volume = clamped
		"bgm":
			bgm_volume = clamped
	_apply_mix()
	return true


func adjust_volume(channel: String, delta: float) -> bool:
	var current := get_volume(channel)
	if current < 0.0 or not is_finite(delta):
		return false
	return set_mix_volume(channel, current + delta)


func _apply_mix() -> void:
	_apply_player_volume(music, master_volume * bgm_volume)
	_apply_player_volume(effects, master_volume * sfx_volume)
	_apply_player_volume(ambient, master_volume * AMBIENT_VOLUME)


func _apply_player_volume(player: AudioStreamPlayer, linear_volume: float) -> void:
	if not is_instance_valid(player):
		return
	player.volume_db = MIN_VOLUME_DB if linear_volume <= 0.0 else linear_to_db(linear_volume)


func set_enabled(value: bool) -> void:
	enabled = value
	if not enabled:
		music.stop()
		ambient.stop()
		effects.stop()
	else:
		play_music("bgm_battle")
		play_ambient("ambient_forest")
