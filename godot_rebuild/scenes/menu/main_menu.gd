extends Control

signal prototype_requested(level_number: int, difficulty: String)
signal siege_requested
signal combat_requested
signal play_requested
signal quit_requested
signal progress_slot_changed(slot: int, path: String)

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")
const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")
const Catalog = preload("res://scripts/match/level_catalog.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const LevelStats = preload("res://scripts/match/level_stats.gd")
const HeroUnlockStore = preload("res://scripts/match/hero_unlock_store.gd")
const SaveSlotStore = preload("res://scripts/match/save_slot_store.gd")
const PygameSaveImport = preload("res://scripts/match/pygame_save_import.gd")
const MetaHeroShopPanel = preload("res://scripts/ui/meta_hero_shop_panel.gd")
const TopupFlow = preload("res://scripts/match/topup_flow.gd")
const TopupCurrency = preload("res://scripts/match/topup_currency.gd")
const TopupClient = preload("res://scripts/net/topup_client.gd")
const TopupPanel = preload("res://scripts/ui/topup_panel.gd")
const SaveSlotPanel = preload("res://scripts/ui/save_slot_panel.gd")
const AudioSettingsPanel = preload("res://scripts/ui/audio_settings_panel.gd")
const SourceUiButton = preload("res://scripts/ui/source_ui_button.gd")
const MenuBackdrop = preload("res://scripts/ui/menu_backdrop.gd")

const SOURCE_MENU_SIZE := Vector2(1280.0, 720.0)
## `_core.py::_draw_main_menu` in the 1280x720 reference frame. The Android
## screenshots (`tests/fixtures/android_screenshot_reference.json`) pin these
## numbers, and `tests/android_layout_checks.gd` replays them.
const SOURCE_BUTTON_RECTS := {
	"ContinueButton": Rect2(320.0, 311.0, 300.0, 50.0),
	"PlayButton": Rect2(660.0, 311.0, 300.0, 50.0),
	"HeroShopButton": Rect2(460.0, 364.0, 360.0, 50.0),
	"InputButton": Rect2(460.0, 417.0, 360.0, 50.0),
	"HowToPlayButton": Rect2(460.0, 470.0, 360.0, 50.0),
	"SettingsButton": Rect2(460.0, 523.0, 360.0, 50.0),
	"CreditsButton": Rect2(460.0, 576.0, 360.0, 50.0),
	"QuitButton": Rect2(460.0, 629.0, 360.0, 50.0),
}
const SOURCE_ROW_BUTTONS := ["ContinueButton", "PlayButton"]
var slot_path_template := SaveSlotStore.PATH_TEMPLATE
var pygame_import_template := PygameSaveImport.STAGED_TEMPLATE
var progress_path := SaveSlotStore.current_path(slot_path_template)
var active_slot := SaveSlotStore.get_current_slot()
var hero_shop_panel: MetaHeroShopPanel
var topup_flow: TopupFlow
var topup_client: TopupClient
var topup_panel: TopupPanel
var save_slot_panel: SaveSlotPanel
var audio_settings_panel: AudioSettingsPanel
var _localization_runtime: Node
var _play_after_slot_selection := false


func _ready() -> void:
	theme = UI_THEME.create_theme()
	_localization_runtime = get_tree().root.get_node_or_null("Localization")
	if is_instance_valid(_localization_runtime):
		_localization_runtime.connect("language_changed", _refresh_localized_labels)
	UI_THEME.title(%Title, 72)
	%Subtitle.add_theme_font_override("font", UI_THEME.STRONG_FONT)
	%Subtitle.add_theme_font_size_override("font_size", 32)
	%Subtitle.add_theme_color_override("font_color", Color8(150, 195, 255))
	%Scope.add_theme_font_override("font", UI_THEME.BODY_FONT)
	%Scope.add_theme_font_size_override("font_size", 22)
	UI_THEME.muted(%Scope)
	%InputStatus.add_theme_font_override("font", UI_THEME.BODY_FONT)
	%InputStatus.add_theme_font_size_override("font_size", 20)
	%InputStatus.add_theme_color_override("font_color", Color8(110, 200, 210))
	%Version.add_theme_font_override("font", UI_THEME.BODY_FONT)
	%Version.add_theme_font_size_override("font_size", 20)
	UI_THEME.muted(%Version)
	%PlayButton.pressed.connect(_open_new_game)
	%QuitButton.pressed.connect(func() -> void: _click_and_emit(quit_requested))
	%CombatButton.pressed.connect(func() -> void: _click_and_emit(combat_requested))
	%SiegeButton.pressed.connect(func() -> void: _click_and_emit(siege_requested))
	%PrototypeButton.pressed.connect(func() -> void: _click_and_start())
	%MatchTestButton.pressed.connect(func() -> void: _click_and_emit(play_requested))
	%ContinueButton.pressed.connect(_start_continue_level)
	%HeroShopButton.pressed.connect(_open_hero_shop)
	%InputButton.pressed.connect(_toggle_input_mode)
	%HowToPlayButton.pressed.connect(_open_how_to_play)
	%CreditsButton.pressed.connect(_open_credits)
	%SaveGamesButton.pressed.connect(_open_save_slots)
	%SettingsButton.pressed.connect(_open_audio_settings)
	%LevelChoice.item_selected.connect(_update_level_stats_label)
	resized.connect(_layout_source_menu)
	var selected_from_path := SaveSlotStore.slot_for_path(progress_path, slot_path_template)
	if selected_from_path > 0:
		active_slot = selected_from_path
		SaveSlotStore.set_current_slot(active_slot)
	_build_hero_shop()
	_build_save_slots()
	_build_audio_settings()
	_refresh_localized_labels()
	_update_active_slot_label()
	refresh_levels()
	_layout_source_menu()
	%ContinueButton.grab_focus()


func _process(_delta: float) -> void:
	if not is_node_ready() or size.x <= 0.0 or size.y <= 0.0:
		return
	var arena := MenuBackdrop.arena_rect(size)
	var fit := arena.size.x / SOURCE_MENU_SIZE.x
	var origin := arena.position
	var ornaments := get_node("Ornaments") as Control
	var pulse := sin(float(ornaments.get("animation_time")) * 0.02) * 3.0
	%Title.position.y = origin.y + (74.0 + pulse) * fit


## Source `_draw_main_menu()` positions in its 1280x720 reference frame.
func _layout_source_menu() -> void:
	if not is_node_ready():
		return
	# `platform_utils.create_display` keeps the arena at the surface origin and
	# collects the leftover width into the stone dock, so the menu frame is
	# anchored left instead of being centred.
	var arena := MenuBackdrop.arena_rect(size)
	var fit := arena.size.x / SOURCE_MENU_SIZE.x
	if fit <= 0.0:
		return
	var origin := arena.position
	_place_arena_layer("Backdrop", arena)
	_place_arena_layer("Ambient", arena)
	_place_arena_layer("Ornaments", arena)
	_place_source_control("Title", Rect2(190.0, 74.0, 900.0, 100.0), origin, fit)
	_place_source_control("Subtitle", Rect2(470.0, 190.0, 340.0, 48.0), origin, fit)
	_place_source_control("Scope", Rect2(280.0, 244.0, 720.0, 32.0), origin, fit)
	for button_name in SOURCE_BUTTON_RECTS:
		_place_source_control(button_name, SOURCE_BUTTON_RECTS[button_name], origin, fit)
	_place_source_control("InputStatus", Rect2(24.0, 692.0, 340.0, 24.0), origin, fit)
	_place_source_control("Version", Rect2(420.0, 686.0, 440.0, 24.0), origin, fit)
	for button_name in [
		"ContinueButton",
		"PlayButton",
		"HeroShopButton",
		"InputButton",
		"HowToPlayButton",
		"SettingsButton",
		"CreditsButton",
		"QuitButton",
	]:
		var button := get_node("%" + button_name) as Button
		if button.has_method("set_label_font_size"):
			var base_font := 36 if button_name in SOURCE_ROW_BUTTONS else 44
			button.call("set_label_font_size", maxi(8, roundi(float(base_font) * fit)))


## Decorative layers span exactly the arena, so their internal transforms land
## at 1:1 and the stone dock is never painted over.
func _place_arena_layer(node_name: String, arena: Rect2) -> void:
	var layer := get_node(node_name) as Control
	layer.position = arena.position
	layer.size = arena.size


func _place_source_control(
	node_name: String, base_rect: Rect2, origin: Vector2, fit: float
) -> void:
	var control := get_node("%" + node_name) as Control
	control.position = origin + base_rect.position * fit
	control.size = base_rect.size * fit
	if control is Button:
		(control as Button).custom_minimum_size = control.size


func _toggle_input_mode() -> void:
	var devices := Input.get_connected_joypads()
	if devices.is_empty():
		%InputStatus.text = "INPUT: KEYBOARD + MOUSE"
		AudioRuntime.play("ui_error")
		return
	if %InputStatus.text.contains("CONTROLLER"):
		%InputStatus.text = "INPUT: KEYBOARD + MOUSE"
	else:
		%InputStatus.text = "INPUT: CONTROLLER"
	AudioRuntime.play("ui_click")


func _open_how_to_play() -> void:
	_show_info_dialog(
		"HOW TO PLAY",
		(
			"OBJECTIVE\nDestroy the enemy castle before they destroy yours.\n\n"
			+ "BUILDING TOWERS\nTap empty build slots (+) to build towers. Cost: 100 gold.\n\n"
			+ "HEROES\nBuy heroes from Hero Shop. Select a hero, then tap an enemy to attack.\n\n"
			+ "TACTICAL COMMANDS\nG = Gather heroes   ·   T = Protect tower   ·   C = Protect castle\n"
			+ "B = Attack boss   ·   D = Attack top damage dealer\n\n"
			+ "SKILLS & UPGRADES\nQ, W, E, R auto-cast near enemies. "
			+ "Select towers, castle, or hero to upgrade."
		)
	)


func _open_credits() -> void:
	_show_info_dialog(
		"CREDITS",
		(
			"Tower Defense Battle Arena\n\n"
			+ "GAME DESIGN & PROGRAMMING\nDharmawan Toxi\n\n"
			+ "ART DIRECTION\nDark Fantasy Vector Style\n\n"
			+ "SOUND EFFECTS & MUSIC\nCustom SFX Library\n\n"
			+ "SPECIAL THANKS\nPygame Community  •  Python 3.10+\n\n"
			+ "Made with ♥ using Godot"
		)
	)


func _show_info_dialog(title_text: String, body_text: String) -> void:
	var old_overlay := get_node_or_null("MenuInfoOverlay")
	if old_overlay != null:
		old_overlay.queue_free()
	var overlay := Control.new()
	overlay.name = "MenuInfoOverlay"
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	overlay.z_index = 100
	add_child(overlay)
	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.02, 0.025, 0.06, 0.88)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	overlay.add_child(shade)
	var card := PanelContainer.new()
	card.set_anchors_preset(Control.PRESET_CENTER)
	card.position = Vector2(-450.0, -250.0)
	card.size = Vector2(900.0, 500.0)
	overlay.add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 18)
	card.add_child(column)
	var title := Label.new()
	title.text = title_text
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	UI_THEME.title(title, 34)
	column.add_child(title)
	var body := Label.new()
	body.text = body_text
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	body.add_theme_font_size_override("font_size", 19)
	body.add_theme_color_override("font_color", UI_THEME.BODY)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(body)
	var close := Button.new()
	close.text = "BACK"
	close.custom_minimum_size = Vector2(180.0, 48.0)
	close.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	close.set_script(SourceUiButton)
	close.set("source_style_key", "help")
	close.set("icon_name", "help")
	close.set("label_font_size", 20)
	close.pressed.connect(overlay.queue_free)
	column.add_child(close)
	close.grab_focus()


func _refresh_localized_labels(_language: String = "") -> void:
	if not is_instance_valid(_localization_runtime):
		return
	%PlayButton.text = String(_localization_runtime.call("translate", "menu_play"))
	%QuitButton.text = String(_localization_runtime.call("translate", "menu_quit"))
	%SaveGamesButton.text = String(_localization_runtime.call("translate", "slot_title"))
	%SettingsButton.text = String(_localization_runtime.call("translate", "menu_settings"))


func _open_new_game() -> void:
	_play_after_slot_selection = true
	_open_save_slots()


func _start_continue_level() -> void:
	var progress := ProgressStore.load_state(progress_path)
	var completed: Array[int] = []
	for value in progress.get("completed_levels", []):
		completed.append(int(value))
	var level_number := int(progress.get("last_played_level", 1))
	if not completed.is_empty():
		var highest: int = int(completed.max())
		var next_level := Catalog.get_next_level(highest)
		level_number = next_level if next_level > 0 else highest
	if not Catalog.is_level_unlocked(level_number, completed):
		level_number = 1
	var difficulty := String(progress.get("run_difficulty", "normal"))
	if difficulty not in ["easy", "normal", "hard"]:
		difficulty = "normal"
	if progress.get("run_difficulty") == null:
		progress = HeroUnlockStore.bootstrap_state(progress)
		progress["run_difficulty"] = difficulty
		if not SaveSlotStore.save_path(progress, progress_path, -1.0, slot_path_template):
			AudioRuntime.play("ui_error")
			return
	AudioRuntime.play("ui_click")
	prototype_requested.emit(level_number, difficulty)


func _click_and_emit(signal_value: Signal) -> void:
	AudioRuntime.play("ui_click")
	signal_value.emit()


func _click_and_start() -> void:
	AudioRuntime.play("ui_click")
	_start_selected_level()


func _build_hero_shop() -> void:
	hero_shop_panel = MetaHeroShopPanel.new()
	hero_shop_panel.name = "MetaHeroShop"
	hero_shop_panel.unlock_requested.connect(_unlock_hero)
	hero_shop_panel.topup_requested.connect(_open_topup)
	add_child(hero_shop_panel)
	_build_topup()


## Layer 9au: top-up dialog over the hero shop (simulation without
## MYSTIC_TOPUP_URL, QRIS server flow with it) + voucher redeem.
func _build_topup() -> void:
	topup_flow = TopupFlow.new()
	topup_flow.currency = TopupCurrency.detect_currency()
	topup_flow.save_callable = _save_topup_profile
	topup_flow.sound_requested.connect(func(key: String) -> void: AudioRuntime.play(key))
	topup_client = TopupClient.new()
	topup_client.name = "TopupClient"
	add_child(topup_client)
	topup_client.configure(topup_flow)
	topup_panel = TopupPanel.new()
	topup_panel.name = "TopupPanel"
	topup_panel.bind(topup_flow)
	add_child(topup_panel)


func _open_topup() -> void:
	AudioRuntime.play("ui_click")
	topup_flow.profile = HeroUnlockStore.bootstrap_state(ProgressStore.load_state(progress_path))
	topup_flow.click("topup_open")


func _save_topup_profile(profile: Dictionary) -> bool:
	var saved := SaveSlotStore.save_path(profile, progress_path, -1.0, slot_path_template)
	if not saved:
		AudioRuntime.play("ui_error")
	elif hero_shop_panel.is_open:
		hero_shop_panel.apply_state(
			profile, "Hero Gold sekarang %d." % int(profile.get("meta_gold", 0))
		)
	return saved


func _open_hero_shop() -> void:
	AudioRuntime.play("ui_click")
	var profile := HeroUnlockStore.bootstrap_state(ProgressStore.load_state(progress_path))
	hero_shop_panel.open_with_state(profile)


func _build_save_slots() -> void:
	save_slot_panel = SaveSlotPanel.new()
	save_slot_panel.name = "SaveSlotPanel"
	save_slot_panel.slot_requested.connect(_select_save_slot)
	save_slot_panel.delete_requested.connect(_delete_save_slot)
	save_slot_panel.import_requested.connect(_import_pygame_saves)
	save_slot_panel.closed.connect(_on_save_slots_closed)
	add_child(save_slot_panel)
	var cloud := get_tree().root.get_node_or_null("CloudSave")
	if cloud != null:
		cloud.call("configure_native_paths", slot_path_template)
		if (
			cloud.has_signal("restore_available")
			and not cloud.is_connected("restore_available", _on_cloud_restore_available)
		):
			cloud.connect("restore_available", _on_cloud_restore_available)
		if (
			cloud.has_signal("restored")
			and not cloud.is_connected("restored", refresh_after_cloud_restore)
		):
			cloud.connect("restored", refresh_after_cloud_restore)
		var pending: Dictionary = cloud.call("get_pending_restore")
		if pending.has("payload"):
			var local_slots_empty := true
			for slot in range(1, SaveSlotStore.SLOT_COUNT + 1):
				var path := SaveSlotStore.slot_path(slot, slot_path_template)
				if (
					SaveSlotStore.slot_exists(slot, slot_path_template)
					or FileAccess.file_exists(path + ".tmp")
				):
					local_slots_empty = false
					break
			if local_slots_empty:
				_on_cloud_restore_available(pending.payload, pending.summary)
			else:
				cloud.call("dismiss_restore_prompt")


func _on_cloud_restore_available(payload: Dictionary, summary: Dictionary) -> void:
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)
	save_slot_panel.show_cloud_restore_prompt(payload, summary)


func refresh_after_cloud_restore() -> void:
	progress_path = SaveSlotStore.slot_path(active_slot, slot_path_template)
	_update_active_slot_label()
	refresh_levels()
	if save_slot_panel != null:
		save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)


func _on_save_slots_closed() -> void:
	_play_after_slot_selection = false


func _open_save_slots() -> void:
	AudioRuntime.play("ui_click")
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	if audio_settings_panel != null:
		audio_settings_panel.set_open(false)
	save_slot_panel.open_with_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)


func _build_audio_settings() -> void:
	audio_settings_panel = AudioSettingsPanel.new()
	audio_settings_panel.name = "AudioSettingsPanel"
	add_child(audio_settings_panel)


func _open_audio_settings() -> void:
	AudioRuntime.play("ui_click")
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	if save_slot_panel != null:
		save_slot_panel.set_open(false)
	audio_settings_panel.open()


func _select_save_slot(slot: int) -> void:
	if not SaveSlotStore.set_current_slot(slot):
		AudioRuntime.play("ui_error")
		return
	var start_after_selection := _play_after_slot_selection
	_play_after_slot_selection = false
	active_slot = slot
	progress_path = SaveSlotStore.slot_path(slot, slot_path_template)
	_update_active_slot_label()
	refresh_levels()
	save_slot_panel.set_open(false)
	progress_slot_changed.emit(slot, progress_path)
	AudioRuntime.play("ui_click")
	if start_after_selection:
		_start_selected_level()


func _delete_save_slot(slot: int) -> void:
	if not SaveSlotStore.delete_slot(slot, slot_path_template):
		AudioRuntime.play("ui_error")
	else:
		AudioRuntime.play("ui_click")
	if slot == active_slot:
		refresh_levels()
	save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)


func _import_pygame_saves() -> void:
	var report := PygameSaveImport.import_staged_slots(
		pygame_import_template, slot_path_template, -1.0, true
	)
	if (report.get("imported", []) as Array).is_empty():
		AudioRuntime.play("ui_error")
	else:
		AudioRuntime.play("ui_click")
	if save_slot_panel != null:
		save_slot_panel.refresh_slots(SaveSlotStore.all_slot_info(slot_path_template), active_slot)
		save_slot_panel.show_import_report(report)
	refresh_levels()
	_update_active_slot_label()


func configure_pygame_import_template(template: String) -> bool:
	if not template.contains("%d"):
		return false
	pygame_import_template = template
	return true


func _update_active_slot_label() -> void:
	%ActiveSlotLabel.text = "SAVE GAME %d" % active_slot


func configure_slot_paths(path_template: String, slot: int = 1) -> bool:
	if not path_template.contains("%d") or not SaveSlotStore.set_current_slot(slot):
		return false
	slot_path_template = path_template
	active_slot = slot
	progress_path = SaveSlotStore.slot_path(slot, path_template)
	var cloud := get_tree().root.get_node_or_null("CloudSave")
	if cloud != null:
		cloud.call("configure_native_paths", slot_path_template)
	if is_node_ready():
		_update_active_slot_label()
		refresh_levels()
		if save_slot_panel != null and save_slot_panel.visible:
			save_slot_panel.refresh_slots(
				SaveSlotStore.all_slot_info(slot_path_template), active_slot
			)
	progress_slot_changed.emit(slot, progress_path)
	return true


func _unlock_hero(hero_type: String) -> void:
	var before := HeroUnlockStore.bootstrap_state(ProgressStore.load_state(progress_path))
	var result := HeroUnlockStore.try_unlock(before, hero_type)
	if not String(result.error).is_empty():
		AudioRuntime.play("ui_error")
		hero_shop_panel.show_error(String(result.error))
		return
	if not SaveSlotStore.save_path(result.state, progress_path, -1.0, slot_path_template):
		AudioRuntime.play("ui_error")
		hero_shop_panel.show_error("save")
		return
	AudioRuntime.play("ui_buy")
	var item := HeroUnlockStore.entry(hero_type)
	var suffix := " gratis"
	if int(result.cost) > 0:
		suffix = " seharga %d Hero Gold" % int(result.cost)
	hero_shop_panel.apply_state(
		result.state, "%s dibuka%s." % [item.definition.display_name, suffix]
	)


func refresh_levels() -> void:
	var progress := ProgressStore.load_state(progress_path)
	var completed: Array[int] = []
	for value in progress.get("completed_levels", []):
		completed.append(int(value))
	%LevelChoice.clear()
	for number in range(1, Catalog.COUNT + 1):
		var config := Catalog.get_level_config(number)
		%LevelChoice.add_item("%02d · %s" % [number, String(config.get("name", "?"))], number)
		%LevelChoice.set_item_disabled(number - 1, not Catalog.is_level_unlocked(number, completed))
	var selected := int(progress.get("last_played_level", 1))
	if not Catalog.is_level_unlocked(selected, completed):
		selected = 1
	%LevelChoice.select(selected - 1)
	%DifficultyChoice.clear()
	var lock_value: Variant = progress.get("run_difficulty")
	var locked := "" if lock_value == null else String(lock_value)
	for label in ["easy", "normal", "hard"]:
		if locked == "" or locked == label:
			%DifficultyChoice.add_item(label.capitalize())
			%DifficultyChoice.set_item_metadata(%DifficultyChoice.item_count - 1, label)
	%DifficultyChoice.select(0)
	if locked == "":
		%DifficultyChoice.select(1)  # Normal default.
	_update_level_stats_label()


func _update_level_stats_label(_index: int = -1) -> void:
	var level_number: int = %LevelChoice.get_selected_id()
	var stats := LevelStats.get_level_stats(ProgressStore.load_state(progress_path), level_number)
	var attempts := int(stats.total_attempts)
	if attempts <= 0:
		%LevelStatsLabel.text = "NO STATS YET"
		return
	var wins := int(stats.wins)
	var win_rate := int((float(wins) / float(attempts)) * 100.0)
	%LevelStatsLabel.text = (
		"BEST %d  ·  TIME %s  ·  %dW/%d  ·  %d%%"
		% [
			int(stats.best_score),
			LevelStats.format_time(int(stats.best_time_seconds)),
			wins,
			attempts,
			win_rate,
		]
	)


func _start_selected_level() -> void:
	var number: int = %LevelChoice.get_selected_id()
	var progress := ProgressStore.load_state(progress_path)
	var completed: Array[int] = []
	for value in progress.get("completed_levels", []):
		completed.append(int(value))
	if not Catalog.is_level_unlocked(number, completed):
		return
	var difficulty := String(%DifficultyChoice.get_selected_metadata())
	var lock_value: Variant = progress.get("run_difficulty")
	var locked := "" if lock_value == null else String(lock_value)
	if difficulty not in ["easy", "normal", "hard"] or (locked != "" and locked != difficulty):
		return
	if locked == "":
		progress = HeroUnlockStore.bootstrap_state(progress)
		progress["run_difficulty"] = difficulty
		if not SaveSlotStore.save_path(progress, progress_path, -1.0, slot_path_template):
			AudioRuntime.play("ui_error")
			return
	prototype_requested.emit(number, difficulty)
