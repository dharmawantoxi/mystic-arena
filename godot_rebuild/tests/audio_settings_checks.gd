extends RefCounted
## Native checks for Python-mapped volume defaults, clamping, and live mixing.

const AudioManagerScript = preload("res://scripts/audio/audio_manager.gd")
const FIXTURE := "res://tests/fixtures/audio_settings_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary, "audio settings source fixture parses")
	if not fixture is Dictionary:
		return
	var manager: Variant = (Engine.get_main_loop() as SceneTree).root.get_node_or_null(
		"AudioManager"
	)
	check.call(manager != null, "native audio mixer autoload is available")
	if manager == null:
		return

	var defaults: Dictionary = fixture.get("defaults", {})
	check.call(
		(
			is_equal_approx(
				AudioManagerScript.DEFAULT_MASTER_VOLUME, float(defaults.get("master", -1))
			)
			and is_equal_approx(
				AudioManagerScript.DEFAULT_SFX_VOLUME, float(defaults.get("sfx", -1))
			)
			and is_equal_approx(
				AudioManagerScript.DEFAULT_BGM_VOLUME, float(defaults.get("bgm", -1))
			)
			and is_equal_approx(
				AudioManagerScript.AMBIENT_VOLUME, float(defaults.get("ambient", -1))
			)
		),
		"Godot mixer defaults match source SoundManager defaults"
	)
	check.call(
		AudioManagerScript.VOLUME_CHANNELS == ["master", "sfx", "bgm"],
		"native controls expose only active, source-mapped mix channels"
	)
	check.call(
		not AudioManagerScript.STREAMS.has("goblin_spawn"),
		"voice control is not exposed without the source voice stream in Godot"
	)
	check.call(
		(
			is_equal_approx(AudioManagerScript.VOLUME_STEP, float(fixture.adjustment_steps[1]))
			and fixture.clamp == [0.0, 1.0]
		),
		"native step and bounds match the source controls"
	)

	var original := {
		"master": manager.get_volume("master"),
		"sfx": manager.get_volume("sfx"),
		"bgm": manager.get_volume("bgm"),
	}
	for channel in AudioManagerScript.VOLUME_CHANNELS:
		check.call(
			is_equal_approx(manager.get_volume(channel), float(defaults[channel])),
			"native %s starts at its source default" % channel
		)

	check.call(manager.set_mix_volume("master", 0.5), "master mix accepts a valid value")
	check.call(
		(
			is_equal_approx(manager.music.volume_db, _volume_db(0.5 * manager.bgm_volume))
			and is_equal_approx(manager.effects.volume_db, _volume_db(0.5 * manager.sfx_volume))
			and is_equal_approx(
				manager.ambient.volume_db, _volume_db(0.5 * AudioManagerScript.AMBIENT_VOLUME)
			)
		),
		"master changes are applied to current BGM, SFX, and ambient output"
	)
	var music_before_sfx := manager.music.volume_db
	check.call(manager.set_mix_volume("sfx", 0.2), "SFX category accepts a valid value")
	check.call(
		(
			is_equal_approx(manager.effects.volume_db, _volume_db(0.5 * 0.2))
			and is_equal_approx(manager.music.volume_db, music_before_sfx)
		),
		"SFX control changes only the active effects channel"
	)
	check.call(manager.set_mix_volume("bgm", 0.8), "music category accepts a valid value")
	check.call(
		is_equal_approx(manager.music.volume_db, _volume_db(0.5 * 0.8)),
		"music control updates the current BGM stream"
	)
	check.call(
		manager.set_mix_volume("sfx", 2.0), "volume above source range is accepted then clamped"
	)
	check.call(is_equal_approx(manager.sfx_volume, 1.0), "volume upper bound clamps to one")
	check.call(
		manager.adjust_volume("sfx", -2.0), "large negative adjustment is accepted then clamped"
	)
	check.call(is_equal_approx(manager.sfx_volume, 0.0), "volume lower bound clamps to zero")
	check.call(not manager.adjust_volume("voice", 0.1), "unsupported voice channel is rejected")
	check.call(not manager.set_mix_volume("unknown", 0.5), "unknown channel is rejected")
	check.call(manager.set_mix_volume("master", 0.0), "silent master mix is accepted")
	check.call(
		(
			manager.music.volume_db == AudioManagerScript.MIN_VOLUME_DB
			and manager.effects.volume_db == AudioManagerScript.MIN_VOLUME_DB
			and manager.ambient.volume_db == AudioManagerScript.MIN_VOLUME_DB
		),
		"zero master is applied as a silent output level without invalid dB"
	)

	for channel in AudioManagerScript.VOLUME_CHANNELS:
		manager.set_mix_volume(channel, float(original[channel]))


func _volume_db(value: float) -> float:
	return AudioManagerScript.MIN_VOLUME_DB if value <= 0.0 else linear_to_db(value)
