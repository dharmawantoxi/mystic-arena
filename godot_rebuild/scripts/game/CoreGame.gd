class_name CoreGame
extends GameplayPort

## Native _core.Game replacement: simulation + input + shop + dev + rewards.
const ArenaViewScript := preload("res://scripts/game/ArenaView.gd")
var model := MatchModel.new()
var dev := DevMode.new()
var save_repo := SaveRepository.new()
var settings := GameSettings.new()
var cloud_port: CloudSavePort
var topup_port: TopupPort
var voucher := VoucherService.new()
var controller: ControllerManager
var view: Control
var shop_open := false
var item_shop_open := false
var item_page := 0
var build_popup := false
var result_visible := false
var result_victory := false
var reward_summary: Dictionary = {}
var button_rects: Dictionary = {}
var speed_accumulator := 0.0
var map_view := MapView.new()
var effects := CombatEffects.new()
var cinematics := RenderCinematics.new()
var _reward_granted := false
var _context_attached := false


func _exit_tree() -> void:
	model.clear_unit_refs()
	EntityVisuals.clear_cache()
	RenderCache.clear_cache()
	effects.clear()
	cinematics.clear()


func attach_context(
	repo: SaveRepository,
	settings_ref: GameSettings,
	cloud: CloudSavePort,
	topup: TopupPort,
	voucher_service: VoucherService,
	controller_ref: ControllerManager
) -> void:
	save_repo = repo
	settings = settings_ref
	cloud_port = cloud
	topup_port = topup
	voucher = voucher_service
	controller = controller_ref
	_context_attached = true


func configure(level: int, replay := false) -> void:
	level_number = level
	is_replay = replay
	var config := model.data.level(level)
	if config.is_empty():
		config = model.data.level(1)
		level_number = 1
	if not _context_attached:
		settings.load_values()
	var save_data := save_repo.load_slot()
	model.setup(config, save_data, str(settings.values.difficulty), replay)
	if not model.match_finished.is_connected(_on_match_finished):
		model.match_finished.connect(_on_match_finished)
	if not model.render_event.is_connected(_on_render_event):
		model.render_event.connect(_on_render_event)
	effects.configure(settings.values)
	effects.clear()
	cinematics.clear()
	map_view.configure(
		str(config.get("map_theme", "forest")),
		model.data,
		RenderQuality.from_settings(settings.values)
	)
	cinematics.start_level_intro(config, model.data, str(settings.values.difficulty))
	view = ArenaViewScript.new()
	view.game = self
	add_child(view)
	view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_layout_buttons()


func combat_ready() -> bool:
	return model.data.valid() and not model.level_config.is_empty()


func cinematic_active() -> bool:
	return cinematics.blocking()


func skip_cinematic() -> void:
	cinematics.skip()
	if view != null:
		view.queue_redraw()


func simulation_step() -> void:
	if not combat_ready() or result_visible:
		return
	if cinematics.blocking():
		cinematics.update()
		if view != null:
			view.queue_redraw()
		return
	speed_accumulator += clampf(float(settings.values.game_speed), 0.5, 2.0)
	while speed_accumulator >= 1.0:
		speed_accumulator -= 1.0
		model.step()
		effects.update()
		map_view.update(model.frame)
		cinematics.update()
		if model.state != "playing":
			break
	if view != null:
		view.queue_redraw()


func apply_render_quality(level: String) -> void:
	if str(effects.quality.get("level", "high")) == level:
		return
	var preset := RenderQuality.preset(level)
	effects.quality = preset
	map_view.configure(map_view.theme_name, model.data, preset)


func _on_render_event(kind: String, data: Dictionary) -> void:
	match kind:
		"damage":
			effects.add_damage_number(
				data.pos,
				int(data.amount),
				bool(data.get("critical", false)),
				str(data.get("type", "normal"))
			)
		"gold":
			effects.add_gold_popup(data.pos, int(data.amount))
		"popup":
			effects.add_popup(data.pos, str(data.text), data.color)
		"effect":
			effects.add_effect(data.pos, str(data.type), data.color, int(data.radius))
		"shake":
			effects.add_shake(float(data.amount))
		"death":
			effects.add_death_explosion(data.pos, str(data.team), str(data.get("size", "medium")))
		"combo_kill":
			effects.register_combo_kill()
		"wave":
			effects.announce_wave(int(data.number))
		"path_preview":
			effects.show_path_preview(data.paths)
		"achievement":
			effects.unlock_achievement(
				str(data.title), str(data.description), str(data.get("icon", "star"))
			)
		"boss_intro":
			cinematics.start_boss_intro(data.unit, model.data)
		"boss_death":
			cinematics.start_boss_death(data.unit)
			effects.add_shake(25.0)


func pointer_action(action: Dictionary) -> void:
	if cinematics.blocking():
		cinematics.skip()
		return
	var pos: Vector2 = action.get("pos", Vector2.ZERO)
	var kind := str(action.get("kind", "tap"))
	if kind == "scroll":
		if item_shop_open:
			item_page = clampi(item_page + int(action.get("value", 1)), 0, 1)
		return
	if kind not in ["tap", "long_press", "double_tap"]:
		return
	for name: String in button_rects:
		if button_rects[name].has_point(pos):
			_ui_action(name)
			return
	if result_visible or shop_open or item_shop_open or build_popup:
		_close_popups()
		return
	if _handle_map_shop(pos):
		return
	if kind == "long_press":
		var slot := _slot_at(pos)
		if slot >= 0:
			model.selected_slot = slot
			build_popup = true
			_layout_buttons()
		return
	if _select_unit_at(pos):
		return
	var slot := _slot_at(pos)
	if slot >= 0:
		model.selected_slot = slot
		build_popup = true
		_layout_buttons()
		return
	if model.selected_hero != null and model.selected_hero.alive:
		model.selected_hero.move_toward_point(pos)


func _select_unit_at(pos: Vector2) -> bool:
	for hero: BattleUnit in model.heroes:
		if hero.alive and hero.pos.distance_to(pos) <= hero.radius + 12:
			model.selected_hero = hero
			model.selected_tower = null
			_layout_buttons()
			return true
	for tower: BattleUnit in model.towers:
		if tower.alive and tower.pos.distance_to(pos) <= tower.radius + 10:
			model.selected_tower = tower
			model.selected_hero = null
			_layout_buttons()
			return true
	if model.blue_base.pos.distance_to(pos) <= model.blue_base.radius + 10:
		model.selected_tower = model.blue_base
		_layout_buttons()
		return true
	return false


func _handle_map_shop(pos: Vector2) -> bool:
	var shop := map_view.shop_at(pos)
	if shop == "item":
		item_shop_open = true
		effects.popup_show()
		_layout_buttons()
		return true
	if shop == "hero":
		_toggle_shop()
		return true
	return false


func _slot_at(pos: Vector2) -> int:
	for index in range(model.build_slots_blue.size()):
		var slot := model.build_slots_blue[index]
		if not bool(slot.taken) and pos.distance_to(slot.pos) <= 24.0:
			return index
	return -1


func key_pressed(key: Key) -> void:
	if cinematics.blocking() and key in [KEY_SPACE, KEY_ENTER]:
		cinematics.skip()
		return
	if handle_dev_key(key):
		return
	match key:
		KEY_Q:
			model.cast_skill("q")
		KEY_W:
			model.cast_skill("w")
		KEY_E:
			model.cast_skill("e")
		KEY_R:
			model.cast_skill("r")
		KEY_H:
			_toggle_shop()
		KEY_I:
			item_shop_open = not item_shop_open
			shop_open = false
			_layout_buttons()
		KEY_U:
			_upgrade_selected()
		KEY_X:
			model.sell_selected_tower()
		KEY_ESCAPE:
			_close_popups()
		_:
			pass


func handle_dev_key(key: Key) -> bool:
	return dev.handle_hotkey(key, model)


func hud_action(action: String) -> void:
	match action:
		"shop":
			_toggle_shop()
		"q", "w", "e", "r":
			model.cast_skill(action)
		"item_shop":
			item_shop_open = not item_shop_open
			shop_open = false
			_layout_buttons()
		"upgrade":
			_upgrade_selected()
		"sell":
			model.sell_selected_tower()
		"castle_shield":
			model.buy_castle_shield()
		"regen_shield":
			model.buy_tower_regen_shield()


func hold_begin(action: String) -> void:
	model.tactical.hold_begin(action, Time.get_ticks_msec() / 1000.0)


func hold_end(action: String) -> void:
	model.tactical.hold_end(action, Time.get_ticks_msec() / 1000.0)


func release_all_holds() -> void:
	model.tactical.release_all()


func _toggle_shop() -> void:
	shop_open = not shop_open
	item_shop_open = false
	build_popup = false
	if shop_open:
		effects.popup_show()
	else:
		effects.popup_hide()
	_layout_buttons()


func _close_popups() -> void:
	shop_open = false
	item_shop_open = false
	build_popup = false
	effects.popup_hide()
	_layout_buttons()


func _upgrade_selected() -> void:
	if model.selected_tower == model.blue_base:
		model.upgrade_base()
	elif model.selected_tower != null:
		if model.selected_tower.level == 1:
			model.upgrade_selected_tower("archer")
		else:
			model.upgrade_selected_tower()
	elif model.selected_hero != null:
		model.upgrade_selected_hero()


func _ui_action(name: String) -> void:
	if name.begins_with("buy_hero:"):
		model.buy_hero(name.get_slice(":", 1))
	elif name.begins_with("build:"):
		model.build_tower(model.selected_slot, name.get_slice(":", 1))
		build_popup = false
	elif name.begins_with("buy_item:"):
		model.buy_item(name.get_slice(":", 1))
	elif name.begins_with("tower_path:"):
		model.upgrade_selected_tower(name.get_slice(":", 1))
	else:
		match name:
			"close":
				_close_popups()
			"item_page":
				item_page = 1 - item_page
			"upgrade":
				_upgrade_selected()
			"sell":
				model.sell_selected_tower()
			"castle_shield":
				model.buy_castle_shield()
			"regen_shield":
				model.buy_tower_regen_shield()
			"next":
				next_level_requested.emit()
			"replay":
				replay_requested.emit()
			"menu":
				menu_requested.emit()
	_layout_buttons()


func _layout_buttons() -> void:
	button_rects = {}
	if result_visible:
		button_rects["next"] = Rect2(440, 470, 180, 52)
		button_rects["replay"] = Rect2(640, 470, 180, 52)
		button_rects["menu"] = Rect2(540, 535, 180, 52)
		return
	if build_popup:
		var index := 0
		for path: String in ["archer", "cannon", "ice", "mage"]:
			button_rects["build:" + path] = Rect2(430 + index * 110, 330, 100, 56)
			index += 1
		button_rects["close"] = Rect2(590, 400, 100, 44)
		return
	if shop_open:
		var index := 0
		for hero_type: String in model.purchased_heroes:
			if index >= 8:
				break
			button_rects["buy_hero:" + hero_type] = Rect2(
				250 + (index % 4) * 200, 210 + int(index / 4) * 110, 185, 96
			)
			index += 1
		button_rects["close"] = Rect2(590, 560, 100, 44)
		return
	if item_shop_open:
		var index := 0
		var items: Dictionary = model.data.data.get("items", {})
		for item_id: String in items:
			var item: Dictionary = items[item_id]
			var tier := int(item.get("tier", 1))
			if tier != item_page + 1:
				continue
			if index >= 10:
				break
			button_rects["buy_item:" + item_id] = Rect2(
				230 + (index % 5) * 170, 200 + int(index / 5) * 130, 160, 118
			)
			index += 1
		button_rects["item_page"] = Rect2(430, 500, 180, 44)
		button_rects["close"] = Rect2(650, 500, 100, 44)
		return
	if model.selected_tower != null and model.selected_tower.alive:
		if model.selected_tower == model.blue_base:
			button_rects["upgrade"] = Rect2(24, 230, 180, 46)
			button_rects["castle_shield"] = Rect2(24, 284, 180, 46)
		else:
			button_rects["upgrade"] = Rect2(24, 230, 180, 46)
			button_rects["sell"] = Rect2(24, 284, 180, 46)
			button_rects["regen_shield"] = Rect2(24, 338, 180, 46)
			if model.selected_tower.level == 1:
				var index := 0
				for path: String in ["archer", "cannon", "ice", "mage"]:
					button_rects["tower_path:" + path] = Rect2(220 + index * 110, 230, 100, 46)
					index += 1
	elif model.selected_hero != null and model.selected_hero.alive:
		button_rects["upgrade"] = Rect2(24, 230, 180, 46)


func _on_match_finished(victory: bool) -> void:
	if _reward_granted:
		return
	_reward_granted = true
	result_visible = true
	result_victory = victory
	var save_data := save_repo.load_slot()
	reward_summary = SaveRepository.grant_match_result(
		save_data,
		level_number,
		model.level_config,
		victory,
		is_replay,
		model.difficulty,
		model.match_stats(),
		model.bosses_defeated,
		model.data.data.get("levels", []).size(),
		Time.get_unix_time_from_system()
	)
	save_repo.save_slot(save_data, -1, Time.get_unix_time_from_system())
	if cloud_port != null:
		var payload := CloudSaveCodec.build_payload(
			save_repo, settings.values, Time.get_unix_time_from_system()
		)
		cloud_port.upload(payload)
	_layout_buttons()
	if view != null:
		view.queue_redraw()
