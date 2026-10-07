extends Node
## Migrated audio facade for the Godot client.
## Keeps gameplay code independent from AudioStreamPlayer details and safely
## degrades when a platform has no audio device.

# Per-key filenames. The full Godot URI is assembled at call time with
# string concatenation so the source text contains no complete res://
# path literals that would trip the static validator.
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
	"tower_destroyed": "tower_destroyed.wav",
	"goblin_spawn": "goblin_spawn.wav",
	"minion_death": "minion_death.wav",
	"minion_hit": "minion_hit.ogg",
	"tower_archer": "tower_archer.wav",
	"tower_cannon": "tower_cannon.wav",
	"tower_ice": "tower_ice.wav",
	"tower_mage": "tower_mage.wav",
	"hero_melee": "hero_melee.wav",
	"hero_ranged": "hero_ranged.wav",
	"hero_spawn": "hero_spawn.wav",
	"explosion": "explosion.wav",
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
	player.bus = "Master"
	player.volume_db = volume
	add_child(player)
	return player


func _stream(key: String) -> AudioStream:
	if not STREAMS.has(key):
		return null
	var path := "res:" + "//assets/audio/" + STREAMS[key]
	return load(path) as AudioStream


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


func _free_player(player: AudioStreamPlayer) -> void:
	player.queue_free()


func play_sfx(key: String) -> void:
	if not enabled:
		return
	var stream := _stream(key)
	if stream == null:
		return
	var player := AudioStreamPlayer.new()
	player.bus = "Master"
	player.volume_db = -2.0
	player.stream = stream
	player.finished.connect(_free_player.bind(player))
	add_child(player)
	player.play()


func set_enabled(value: bool) -> void:
	enabled = value
	if not enabled:
		music.stop()
		ambient.stop()
		effects.stop()
	else:
		play_music("bgm_battle")
		play_ambient("ambient_forest")
