extends Node
## Migrated audio facade for the Godot client.
## Keeps gameplay code independent from AudioStreamPlayer details and safely
## degrades when a platform has no audio device.

const ROOT := "res://assets/audio/"
const STREAMS := {
	"bgm_battle": "bgm_battle.wav",
	"ambient_forest": "ambient_forest.wav",
	"victory": "victory.wav",
	"defeat": "defeat.wav",
	"ui_click": "ui_click.wav",
	"ui_buy": "ui_buy.wav",
	"ui_error": "ui_error.wav",
	"ui_sell": "ui_sell.wav",
	"ui_upgrade": "ui_upgrade.wav",
	"wave_start": "wave_start.wav",
	"hero_skill": "hero_skill.wav",
	"nexus_hit": "nexus_hit.wav",
}

var music: AudioStreamPlayer
var effects: AudioStreamPlayer
var ambient: AudioStreamPlayer
var enabled := true


func _ready() -> void:
	music = _make_player("Music", -8.0)
	effects = _make_player("Effects", -2.0)
	ambient = _make_player("Ambient", -12.0)
	play_music("bgm_battle")
	play_ambient("ambient_forest")


func _make_player(player_name: String, volume: float) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.name = player_name
	player.volume_db = volume
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


func set_enabled(value: bool) -> void:
	enabled = value
	if not enabled:
		music.stop()
		ambient.stop()
		effects.stop()
	else:
		play_music("bgm_battle")
		play_ambient("ambient_forest")
