extends RefCounted
## Opens the real MainMenu audio panel and verifies it controls live playback.

const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const AudioManagerScript = preload("res://scripts/audio/audio_manager.gd")
const PresentationStore = preload("res://scripts/settings/presentation_settings_store.gd")
const ThemeToggle = preload("res://scripts/ui/ui_theme_toggle.gd")
const ThemeSlider = preload("res://scripts/ui/ui_theme_slider.gd")


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var manager: Variant = tree.root.get_node_or_null("AudioManager")
	check.call(manager != null, "playable menu scene has the native audio manager")
	if manager == null:
		return
	var original := {
		"master": manager.get_volume("master"),
		"sfx": manager.get_volume("sfx"),
		"bgm": manager.get_volume("bgm"),
	}
	var had_presentation_file := FileAccess.file_exists(PresentationStore.PATH)
	var original_presentation := PresentationStore.load_settings()
	manager.set_mix_volume("master", AudioManagerScript.DEFAULT_MASTER_VOLUME)
	manager.set_mix_volume("sfx", AudioManagerScript.DEFAULT_SFX_VOLUME)
	manager.set_mix_volume("bgm", AudioManagerScript.DEFAULT_BGM_VOLUME)

	var menu = app.current_screen
	var panel: Control = menu.get("audio_settings_panel")
	check.call(menu.name == "MainMenu" and panel != null, "MainMenu owns the audio settings panel")
	if panel == null:
		_restore_mix(manager, original)
		return
	check.call(not panel.visible, "audio controls begin closed")
	menu.get_node("%SettingsButton").pressed.emit()
	await _settle(tree)
	check.call(panel.visible, "Settings button opens the live audio panel")
	var master_value := panel.find_child("MasterValue", true, false) as Label
	var sfx_value := panel.find_child("SfxValue", true, false) as Label
	var bgm_value := panel.find_child("BgmValue", true, false) as Label
	check.call(
		(
			master_value != null
			and sfx_value != null
			and bgm_value != null
			and master_value.text == "70%"
			and sfx_value.text == "60%"
			and bgm_value.text == "35%"
		),
		"open panel displays source mixer defaults"
	)
	var shake_toggle := panel.find_child("ScreenShakeToggle", true, false) as Button
	var damage_toggle := panel.find_child("DamageNumbersToggle", true, false) as Button
	var master_meter := panel.find_child("MasterMeter", true, false) as Control
	check.call(
		(
			shake_toggle != null
			and damage_toggle != null
			and shake_toggle.get_script() == ThemeToggle
			and damage_toggle.get_script() == ThemeToggle
		),
		"screen-shake and damage-number settings use the source toggle skin"
	)
	check.call(
		(
			master_meter != null
			and master_meter.get_script() == ThemeSlider
			and is_equal_approx(float(master_meter.get("value")), manager.get_volume("master"))
		),
		"volume uses the source gradient slider at the live mixer value"
	)
	if shake_toggle != null and damage_toggle != null:
		check.call(
			(
				shake_toggle.button_pressed == bool(original_presentation.screen_shake)
				and damage_toggle.button_pressed == bool(original_presentation.damage_numbers)
			),
			"open panel restores the persisted source toggle states"
		)
		shake_toggle.call("set_value", true)
		shake_toggle.toggled.emit(true)
		damage_toggle.call("set_value", false)
		damage_toggle.toggled.emit(false)
		check.call(
			PresentationStore.load_settings() == {"screen_shake": true, "damage_numbers": false},
			"the visible source toggles persist their changed values"
		)

	var master_plus := panel.find_child("MasterPlus", true, false) as Button
	var sfx_minus := panel.find_child("SfxMinus", true, false) as Button
	var bgm_plus := panel.find_child("BgmPlus", true, false) as Button
	check.call(
		master_plus != null and sfx_minus != null and bgm_plus != null,
		"all active mixer channels expose source-step controls"
	)
	if master_plus != null and sfx_minus != null and bgm_plus != null:
		master_plus.pressed.emit()
		sfx_minus.pressed.emit()
		bgm_plus.pressed.emit()
		check.call(
			(
				is_equal_approx(manager.master_volume, 0.8)
				and is_equal_approx(manager.sfx_volume, 0.5)
				and is_equal_approx(manager.bgm_volume, 0.45)
			),
			"settings buttons update live mixer state by the source 0.1 step"
		)
		check.call(
			(
				is_equal_approx(manager.music.volume_db, linear_to_db(0.8 * 0.45))
				and is_equal_approx(manager.effects.volume_db, linear_to_db(0.8 * 0.5))
			),
			"menu controls immediately alter current music and SFX output"
		)
		check.call(
			master_value.text == "80%" and sfx_value.text == "50%" and bgm_value.text == "45%",
			"panel values refresh after live changes"
		)

	var close_button := panel.find_child("CloseButton", true, false) as Button
	check.call(close_button != null, "audio panel has an explicit back action")
	if close_button != null:
		close_button.pressed.emit()
	check.call(not panel.visible, "back closes the audio panel")

	app.start_prototype()
	await _settle(tree)
	check.call(
		app.current_screen.name == "PrototypeMatch", "updated mix survives into playable combat"
	)
	var current_screen: Node = app.get("current_screen") as Node
	var simulation: Node = current_screen.get_node("Simulation")
	var world: Variant = simulation.get("world")
	var effects: Variant = world.get("effects") if world != null else null
	check.call(
		effects != null and effects.screen_shake_enabled and not effects.damage_numbers_enabled,
		"saved menu toggles configure the playable match effects"
	)
	AudioRuntime.play("hero_skill")
	var skill_stream: AudioStream = load("res://assets/audio/hero_skill.wav")
	check.call(
		(
			manager.effects.stream == skill_stream
			and is_equal_approx(manager.effects.volume_db, linear_to_db(0.8 * 0.5))
		),
		"combat SFX uses the menu-selected mix on its actual audio player"
	)
	app.show_menu()
	await _settle(tree)
	check.call(app.current_screen.name == "MainMenu", "audio scene test returns cleanly to menu")

	_restore_mix(manager, original)
	check.call(
		_restore_presentation(had_presentation_file, original_presentation),
		"scene test restores the previous on-disk presentation preferences"
	)


func _restore_presentation(had_file: bool, values: Dictionary) -> bool:
	if had_file:
		return PresentationStore.save_settings(values)
	for suffix in ["", ".tmp", ".bak"]:
		var path: String = PresentationStore.PATH + String(suffix)
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	return not FileAccess.file_exists(PresentationStore.PATH)


func _restore_mix(manager: Variant, values: Dictionary) -> void:
	manager.set_mix_volume("master", float(values.master))
	manager.set_mix_volume("sfx", float(values.sfx))
	manager.set_mix_volume("bgm", float(values.bgm))


func _settle(tree: SceneTree) -> void:
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
