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

var music: AudioStreamPlayer
var effects: AudioStreamPlayer
var ambient: AudioStreamPlayer
var enabled := true
var master_volume := DEFAULT_MASTER_VOLUME
var sfx_volume := DEFAULT_SFX_VOLUME
var bgm_volume := DEFAULT_BGM_VOLUME


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
	effects.play()


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
