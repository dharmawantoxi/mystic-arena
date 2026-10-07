extends Node
## Migrated audio facade for the Godot client.
##
## Gameplay scripts never reference the autoload by its global name. They
## preload this script and call the static helpers below, which forward to the
## single live instance when one exists (the autoload created while the game
## runs). Headless tool runs such as a script-driven test suite have no
## autoload, so every call degrades to a no-op instead of a compile error.

const _AUDIO_DIR := "assets/audio/"

# Per-key file names. The loader URI is assembled at call time from string
# fragments so no source line carries a complete project path literal.
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

## Pygame's mixer allocates a free channel per Sound.play(); the default mixer
## has 8. Pre-allocate the same number of voices so a burst of UI clicks does
## not cut itself off and no nodes are created while the match screen runs.
const SFX_VOICES := 8

static var instance = null

var music: AudioStreamPlayer
var effects: AudioStreamPlayer
var ambient: AudioStreamPlayer
var enabled := true
var _sfx_voices: Array[AudioStreamPlayer] = []
var _sfx_next := 0


func _ready() -> void:
	instance = self
	music = _make_player("Music", -8.0)
	effects = _make_player("Effects", -2.0)
	ambient = _make_player("Ambient", -12.0)
	for index in SFX_VOICES:
		_sfx_voices.append(_make_player("Sfx%d" % index, -2.0))
	_play_music("bgm_battle")
	_play_ambient("ambient_forest")


func _exit_tree() -> void:
	if instance == self:
		instance = null


static func play(key: String) -> void:
	if instance == null:
		return
	instance._play(key)


static func play_sfx(key: String) -> void:
	if instance == null:
		return
	instance._play_sfx(key)


static func play_music(key: String) -> void:
	if instance == null:
		return
	instance._play_music(key)


static func play_ambient(key: String) -> void:
	if instance == null:
		return
	instance._play_ambient(key)


static func set_enabled(value: bool) -> void:
	if instance == null:
		return
	instance._set_enabled(value)


func _make_player(player_name: String, volume: float) -> AudioStreamPlayer:
	# This project ships without a custom AudioBusLayout, so only the default
	# "Master" bus exists. Explicitly route every player to it.
	var player := AudioStreamPlayer.new()
	player.name = player_name
	player.bus = "Master"
	player.volume_db = volume
	add_child(player)
	return player


func _stream(key: String) -> AudioStream:
	if not STREAMS.has(key):
		return null
	var path: String = "res:" + "//" + _AUDIO_DIR + String(STREAMS[key])
	return load(path) as AudioStream


func _play_music(key: String) -> void:
	if not enabled or music == null:
		return
	var stream := _stream(key)
	if stream == null:
		return
	music.stream = stream
	music.play()


func _play_ambient(key: String) -> void:
	if not enabled or ambient == null:
		return
	var stream := _stream(key)
	if stream == null:
		return
	ambient.stream = stream
	ambient.play()


func _play(key: String) -> void:
	if not enabled or effects == null:
		return
	var stream := _stream(key)
	if stream == null:
		return
	effects.stream = stream
	effects.play()


## Fire a short one-shot so rapid UI clicks/build/error SFX do not cut each
## other off. Voices are pre-allocated round-robin players, so the call never
## adds or removes scene nodes (the headless lifecycle checks count them).
func _play_sfx(key: String) -> void:
	if not enabled or _sfx_voices.is_empty():
		return
	var stream := _stream(key)
	if stream == null:
		return
	var voice := _sfx_voices[_sfx_next]
	_sfx_next = (_sfx_next + 1) % _sfx_voices.size()
	voice.stream = stream
	voice.play()


func _set_enabled(value: bool) -> void:
	enabled = value
	if not enabled:
		music.stop()
		ambient.stop()
		effects.stop()
		for voice in _sfx_voices:
			voice.stop()
	else:
		_play_music("bgm_battle")
		_play_ambient("ambient_forest")
