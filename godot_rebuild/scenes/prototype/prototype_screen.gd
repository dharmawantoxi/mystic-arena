extends "res://scenes/combat/combat_screen.gd"
## Separate playable subset; shared input/pause plumbing, no manual laboratory wave controls.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const ItemForgePanel = preload("res://scripts/ui/item_forge_panel.gd")
const HeroShopPanel = preload("res://scripts/ui/hero_shop_panel.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const TACTICAL_KEYS := {
	KEY_G: "gather",
	KEY_F: "gather",
	KEY_T: "protect_tower",
	KEY_C: "protect_castle",
	KEY_B: "attack_boss",
	KEY_D: "attack_damage_dealer",
}

var progress_path := ProgressStore.PATH
var result_shown := false
var forge_panel: ItemForgePanel
var hero_shop_panel: HeroShopPanel
var hero_shop_toggle: Button
var ai_toggle: Button
var migration_status: Label
@onready var match_session: PrototypeSession = $Simulation


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UI_THEME.create_theme()
	arena.session = simulation
	UI_THEME.title(%ArenaTitle, 23)
	UI_THEME.title(%PauseTitle, 32)
	var selected_world := match_session.world as Prototype
	$HUD/TopBar/Row/Names/Description.text = (
		"Lv.%d · %s · %s · uji konfigurasi, belum parity penuh"
		% [
			selected_world.level_number,
			selected_world.difficulty,
			selected_world.level_config.get("name", "?")
		]
	)
	%BuildButton.pressed.connect(
		func() -> void: match_session.request_build(match_session.selected_slot_id)
	)
	%SellButton.pressed.connect(
		func() -> void: match_session.request_sell(match_session.selected_id)
	)
	%UpgradeButton.pressed.connect(
		func() -> void: match_session.request_upgrade(match_session.selected_id, "archer")
	)
	%CannonButton.pressed.connect(_request_tower_path.bind("cannon"))
	%IceButton.pressed.connect(_request_tower_path.bind("ice"))
	%MageButton.pressed.connect(_request_tower_path.bind("mage"))
	%RegenShieldButton.pressed.connect(
		func() -> void: match_session.request_regen_shield(match_session.selected_id)
	)
	%CastleShieldButton.pressed.connect(
		func() -> void: match_session.request_castle_shield(match_session.selected_id)
	)
	%NexusButton.pressed.connect(
		func() -> void: match_session.request_nexus_upgrade(match_session.selected_id)
	)
	%SkillQButton.pressed.connect(
		func() -> void: match_session.request_skill_q(match_session.selected_id)
	)
	%SkillWButton.pressed.connect(
		func() -> void: match_session.request_skill_w(match_session.selected_id)
	)
	%SkillEButton.pressed.connect(
		func() -> void: match_session.request_skill_e(match_session.selected_id)
	)
	%SkillRButton.pressed.connect(
		func() -> void: match_session.request_skill_r(match_session.selected_id)
	)
	%HeroUpgradeButton.pressed.connect(
		func() -> void: match_session.request_hero_upgrade(match_session.selected_id)
	)
	%AutoCastButton.pressed.connect(
		func() -> void: match_session.request_autocast(match_session.selected_id)
	)
	_bind_tactical_button(%GatherButton, "gather")
	_bind_tactical_button(%ProtectTowerButton, "protect_tower")
	_bind_tactical_button(%ProtectCastleButton, "protect_castle")
	_bind_tactical_button(%AttackBossButton, "attack_boss")
	_bind_tactical_button(%AttackDealerButton, "attack_damage_dealer")
	_build_forge_ui()
	_build_hero_shop_ui()
	_build_ai_toggle()
	_build_migration_status()
	%PauseButton.pressed.connect(pause_match)
	%ResumeButton.pressed.connect(resume_match)
	%RestartButton.pressed.connect(func() -> void: restart_requested.emit())
	%MenuButton.pressed.connect(func() -> void: menu_requested.emit())
	%BackButton.pressed.connect(func() -> void: menu_requested.emit())
	%SaveRetryButton.pressed.connect(_save_result)
	%SaveRetryButton.hide()
	if ai_toggle != null:
		ai_toggle.text = (
			"AI lawan  [A] : ON" if match_session.world.ai_enabled else "AI lawan  [A] : OFF"
		)
	%PauseButton.grab_focus()


func _process(_delta: float) -> void:
	var world := simulation.world as Prototype
	var cursor_local := (
		arena.get_global_transform_with_canvas().affine_inverse()
		* get_viewport().get_mouse_position()
	)
	match_session.set_tactical_cursor(
		cursor_local, Rect2(Vector2.ZERO, Vector2(1280, 720)).has_point(cursor_local)
	)
	_update_tactical_hud(world)
	if forge_panel != null and forge_panel.visible:
		forge_panel.refresh()
	if hero_shop_panel != null and hero_shop_panel.visible:
		hero_shop_panel.command_pending = not match_session.command.is_empty()
		hero_shop_panel.refresh()
	%GoldLabel.text = "GOLD  %d G   ·   Lawan %d G" % [world.economy.gold[0], world.economy.gold[1]]
	var next_wave := "menunggu lane bersih"
	if world.scheduler.remaining_ticks > 0:
		next_wave = "%.1f s" % (world.scheduler.remaining_ticks / 60.0)
	elif world.scheduler.pending_count() > 0:
		next_wave = "menunggu antrean spawn"
	%TickLabel.text = "WAVE %02d  ·  Berikut: %s" % [world.wave_count, next_wave]
	if migration_status != null:
		var active_boss: Object = world.active_boss
		var boss_text := "Boss: belum muncul"
		if active_boss != null and active_boss.alive:
			boss_text = (
				"Boss: %s  HP %.0f/%.0f"
				% [active_boss.display_name, active_boss.hp, active_boss.max_hp]
			)
		var ai_text := (
			"AI %s · H%d · build %d · upgrade %d"
			% [
				"ON" if world.ai_enabled else "OFF",
				world._ai_roster().size(),
				world.ai_build.total_built,
				world.ai_upgrades.total_upgraded
			]
		)
		migration_status.text = "%s   |   %s" % [boss_text, ai_text]
	var blue := world.nexuses[0]
	var red := world.nexuses[1]
	%StatusLabel.text = (
		"Nexus B %.0f (+%.0f)  /  R %.0f (+%.0f)" % [blue.hp, blue.shield, red.hp, red.shield]
	)
	var slot := world.get_slot(match_session.selected_slot_id)
	var selected := world.get_unit(simulation.selected_id)
	var tower := selected as Structure
	var hero := selected as HeroState
	var locked := (
		get_tree().paused or not world.is_running() or not match_session.command.is_empty()
	)
	var build_choice := slot != null and slot.team == 0 and slot.structure_id == -1
	%BuildButton.disabled = (
		locked or not build_choice or world.economy.gold[0] < world.Economy.BUILD_COST
	)
	%SellButton.disabled = (
		locked
		or tower == null
		or not tower.alive
		or tower.team != 0
		or tower.settings().structure_kind != "tower"
	)
	var price := world.upgrade_price(simulation.selected_id)
	%UpgradeButton.disabled = locked or price <= 0 or world.economy.gold[0] < price
	var path_choice := (
		tower != null
		and tower.alive
		and tower.settings().structure_kind == "tower"
		and tower.team == 0
		and tower.settings().level == 1
	)
	var tower_option := build_choice or path_choice
	var cannon_price := (
		world.Economy.BUILD_COST
		if build_choice
		else world.upgrade_price(simulation.selected_id, "cannon")
	)
	var ice_price := (
		world.Economy.BUILD_COST
		if build_choice
		else world.upgrade_price(simulation.selected_id, "ice")
	)
	var mage_price := (
		world.Economy.BUILD_COST
		if build_choice
		else world.upgrade_price(simulation.selected_id, "mage")
	)
	%CannonButton.disabled = (
		locked or not tower_option or cannon_price <= 0 or world.economy.gold[0] < cannon_price
	)
	%IceButton.disabled = (
		locked or not tower_option or ice_price <= 0 or world.economy.gold[0] < ice_price
	)
	%MageButton.disabled = (
		locked or not tower_option or mage_price <= 0 or world.economy.gold[0] < mage_price
	)
	%CannonButton.visible = tower_option
	%IceButton.visible = tower_option
	%MageButton.visible = tower_option

	var regen_context := (
		tower != null
		and tower.alive
		and tower.team == 0
		and tower.settings().structure_kind == "tower"
		and tower.settings().level >= Structure.REGEN_SHIELD_MIN_LEVEL
	)
	%RegenShieldButton.visible = regen_context
	%RegenShieldButton.disabled = (
		locked
		or not regen_context
		or not tower.can_activate_regen_shield()
		or world.economy.gold[0] < Structure.REGEN_SHIELD_COST
	)
	%RegenShieldButton.text = (
		"Regen Shield · ON"
		if regen_context and tower.regen_shield_active
		else "Regen Shield · %d G" % Structure.REGEN_SHIELD_COST
	)
	var castle_context := (
		tower != null
		and tower.alive
		and tower.team == 0
		and tower.settings().structure_kind == "nexus"
	)
	%CastleShieldButton.visible = castle_context
	%CastleShieldButton.disabled = (
		locked
		or not castle_context
		or not tower.can_activate_castle_shield()
		or world.economy.gold[0] < Structure.CASTLE_SHIELD_COST
	)
	if castle_context and tower.free_shield_active:
		%CastleShieldButton.text = "Castle Shield · FREE (wave 1-10)"
	elif castle_context and tower.castle_shield_purchased:
		%CastleShieldButton.text = "Castle Shield · ON"
	else:
		%CastleShieldButton.text = "Aktifkan Castle Shield · %d G" % Structure.CASTLE_SHIELD_COST
	%Paths.visible = tower_option or regen_context or castle_context
	%NexusButton.visible = not path_choice
	var nexus_price := world.nexus_upgrade_price(simulation.selected_id)
	%NexusButton.disabled = locked or nexus_price <= 0 or world.economy.gold[0] < nexus_price
	var hero_ready := hero != null and hero.team == 0 and world.blue_q_ready(hero.id)
	%SkillQButton.visible = hero != null and hero.team == 0
	%SkillQButton.disabled = locked or not hero_ready
	%SkillQButton.text = (
		"Q · CD %d" % hero.skill_timer if hero != null and hero.skill_timer > 0 else "Skill Q"
	)
	var w_ready := (
		hero != null and hero.team == 0 and hero.alive and world._can_cast_hero_w(hero.id)
	)
	%SkillWButton.visible = hero != null and hero.team == 0
	%SkillWButton.disabled = locked or not w_ready
	%SkillWButton.text = (
		"W · CD %d" % hero.w_cooldown if hero != null and hero.w_cooldown > 0 else "Skill W"
	)
	var e_ready := (
		hero != null and hero.team == 0 and world._can_cast_hero_e(hero.id, world.structures)
	)
	%SkillEButton.visible = hero != null and hero.team == 0
	%SkillEButton.disabled = locked or not e_ready
	%SkillEButton.text = (
		"E · CD %d" % hero.e_cooldown if hero != null and hero.e_cooldown > 0 else "Skill E"
	)
	var r_ready := (
		hero != null and hero.team == 0 and world._can_cast_hero_r(hero.id, world.structures)
	)
	%SkillRButton.visible = hero != null and hero.team == 0
	%SkillRButton.disabled = locked or not r_ready
	%SkillRButton.text = (
		"R · CD %d" % hero.r_cooldown if hero != null and hero.r_cooldown > 0 else "Skill R"
	)
	# Hero row: the QWER, auto-cast and hero-upgrade controls share a
	# dedicated row so all of them stay inside the 1280x720 viewport.
	var hero_row := hero != null and hero.team == 0
	%HeroCommands.visible = hero_row
	%AutoCastButton.visible = hero_row
	%AutoCastButton.disabled = locked or not hero_row or not hero.alive
	if hero_row:
		%AutoCastButton.text = ("Auto-cast · ON" if hero.auto_cast_enabled else "Auto-cast · OFF")
	var hero_cost := 0
	if hero != null and hero.alive and hero.team == 0:
		hero_cost = hero.upgrade_cost()
	%HeroUpgradeButton.visible = hero != null and hero.team == 0
	%HeroUpgradeButton.disabled = (
		locked
		or hero == null
		or not hero.alive
		or hero_cost <= 0
		or world.economy.gold[0] < hero_cost
	)
	%HeroUpgradeButton.text = (
		"Hero Lv.%d · %d G" % [hero.level + 1, hero_cost]
		if hero != null and hero_cost > 0
		else "Hero maksimum"
	)
	%BuildButton.text = "Bangun Archer · %d G" % world.Economy.BUILD_COST
	%UpgradeButton.text = "Upgrade Archer"
	if build_choice:
		%CannonButton.text = "Bangun Cannon · %d G" % cannon_price
		%IceButton.text = "Bangun Ice · %d G" % ice_price
		%MageButton.text = "Bangun Mage · %d G" % mage_price
	else:
		%CannonButton.text = "Cannon Lv.2"
		%IceButton.text = "Ice Lv.2"
		%MageButton.text = "Mage Lv.2"
	%NexusButton.text = "Upgrade Nexus"
	%SellButton.text = "Jual tower"
	if tower != null and tower.settings().structure_kind == "tower":
		%SellButton.text = "Jual · %d G" % tower.sale_value()
		%UpgradeButton.text = (
			"Upgrade Lv.%d · %d G" % [tower.settings().level + 1, price]
			if price > 0
			else "Archer maksimum" if tower.settings().level == 6 else "Tower lawan"
		)
		if tower.team == 0 and tower.settings().level == 1 and cannon_price > 0:
			%CannonButton.text = "Cannon Lv.2 · %d G" % cannon_price
		elif tower.team != 0:
			%CannonButton.text = "Tower lawan"
		if tower.team == 0 and tower.settings().level == 1 and ice_price > 0:
			%IceButton.text = "Ice Lv.2 · %d G" % ice_price
		elif tower.team != 0:
			%IceButton.text = "Tower lawan"
		if tower.team == 0 and tower.settings().level == 1 and mage_price > 0:
			%MageButton.text = "Mage Lv.2 · %d G" % mage_price
		elif tower.team != 0:
			%MageButton.text = "Tower lawan"
	if tower != null and tower.settings().structure_kind == "nexus":
		if tower.team == 0:
			%NexusButton.text = (
				"Nexus Lv.%d · %d G" % [tower.settings().level + 1, nexus_price]
				if nexus_price > 0
				else "Nexus maksimum"
			)
		else:
			%NexusButton.text = "Nexus lawan"
	%SelectionLabel.text = "Slot biru: pilih Archer, Cannon, Ice, atau Mage (100 G)."
	if selected != null:
		var max_hp := selected.definition.max_hp
		if hero != null:
			max_hp = int(hero.max_hp)
		%SelectionLabel.text = (
			"%s #%d · %s · HP %.0f/%d"
			% [
				selected.definition.display_name,
				selected.id,
				"BIRU" if selected.team == 0 else "MERAH",
				selected.hp,
				max_hp
			]
		)
		if hero != null:
			%SelectionLabel.text += (
				" · Lv.%d · Q stack %d · skill CD %d" % [hero.level, hero.q_stack, hero.skill_timer]
			)
			if not hero.alive:
				%SelectionLabel.text += " · respawn %d" % hero.respawn_timer
			elif hero.is_retreating:
				%SelectionLabel.text += " · mundur"
		elif tower != null and tower.settings().structure_kind == "tower":
			var ammo := "panah"
			var shots: int = tower.settings().volley_count
			if tower.settings().tower_path == "cannon":
				ammo = "peluru"
			elif tower.settings().tower_path == "ice":
				ammo = "kristal"
			elif tower.settings().tower_path == "mage":
				ammo = "bolt"
				shots = tower.settings().chain_count
			%SelectionLabel.text += (
				" · Shield %.0f · DMG %d · %d %s"
				% [tower.shield, tower.definition.damage, shots, ammo]
			)
		elif tower != null:
			%SelectionLabel.text += (
				" · Shield %.0f · DMG %d" % [tower.shield, tower.definition.damage]
			)
	elif slot != null:
		%SelectionLabel.text = (
			"Slot %d · %s · Lane %s"
			% [
				slot.id + 1,
				"BIRU" if slot.team == 0 else "MERAH",
				["atas", "tengah", "bawah"][slot.lane]
			]
		)
	%ActionLabel.text = match_session.last_action
	if not world.is_running() and not result_shown:
		result_shown = true
		%ArenaTitle.text = "BIRU MENANG" if world.winner == 0 else "MERAH MENANG"
		%PauseButton.text = "Hasil [Esc]"
		pause_match()
		_save_result()


func _request_tower_path(tower_path: String) -> void:
	var world := match_session.world as Prototype
	var slot := world.get_slot(match_session.selected_slot_id)
	if slot != null and slot.team == world.BLUE and slot.structure_id == -1:
		match_session.request_build(slot.id, tower_path)
	else:
		match_session.request_upgrade(match_session.selected_id, tower_path)


func _save_result() -> void:
	var world := simulation.world as Prototype
	if world.is_running():
		return
	var committed := world.commit_level_result(progress_path)
	if committed.is_empty():
		%Hint.text = ("Progres BELUM tersimpan. Periksa file progres, lalu coba lagi.")
		%SaveRetryButton.show()
		return
	%Hint.text = ("+%d Meta Gold tersimpan (save pengembangan Godot)." % int(committed.reward))
	%SaveRetryButton.hide()


func _bind_tactical_button(button: Button, command_name: String) -> void:
	button.button_down.connect(_start_panel_tactical.bind(command_name))
	button.button_up.connect(_finish_tactical.bind(command_name))


func _start_panel_tactical(command_name: String) -> void:
	_start_tactical(command_name, false)


func _start_tactical(command_name: String, follow_cursor: bool) -> void:
	var world := match_session.world as Prototype
	if get_tree().paused or not world.is_running():
		return
	var selected := world.get_unit(match_session.selected_id)
	var target_id := -1
	var tower := selected as Structure
	if (
		command_name == "protect_tower"
		and tower != null
		and tower.alive
		and tower.team == world.BLUE
		and tower.settings().structure_kind == "tower"
	):
		target_id = tower.id
	var selected_hero_id := -1
	var hero := selected as HeroState
	if hero != null and hero.alive and hero.team == world.BLUE:
		selected_hero_id = hero.id
	var has_point := (
		follow_cursor and command_name == "gather" and match_session.tactical_cursor_valid
	)
	match_session.request_tactical_start(
		command_name,
		match_session.tactical_cursor,
		has_point,
		target_id,
		selected_hero_id,
		follow_cursor and command_name == "gather"
	)


func _finish_tactical(command_name: String) -> void:
	match_session.request_tactical_end(command_name)


func _update_tactical_hud(world: Prototype) -> void:
	var locked := get_tree().paused or not world.is_running()
	for button in [
		%GatherButton,
		%ProtectTowerButton,
		%ProtectCastleButton,
		%AttackBossButton,
		%AttackDealerButton,
	]:
		button.disabled = locked
	%TacticalStatus.text = world.tactical.status_text(world)
	var visible_feedback: bool = world.tactical.feedback_timer > 0
	%TacticalFeedback.visible = visible_feedback
	if not visible_feedback:
		return
	%TacticalFeedback.text = world.tactical.feedback_text
	var alpha := 1.0
	var y_offset := 0.0
	if world.tactical.feedback_timer < 30:
		alpha = float(world.tactical.feedback_timer) / 30.0
	elif world.tactical.feedback_timer > 150:
		var progress := float(180 - world.tactical.feedback_timer) / 30.0
		alpha = clampf(progress, 0.0, 1.0)
		y_offset = (1.0 - alpha) * 20.0
	%TacticalFeedback.position.y = 112.0 + y_offset
	%TacticalFeedback.modulate = Color(world.tactical.feedback_color, alpha)


func _build_forge_ui() -> void:
	# Layer 5f-3: the ITEM FORGE panel draws the item_shop_ui view data and
	# routes every press back through the source click vocabulary.
	forge_panel = ItemForgePanel.new()
	forge_panel.name = "ItemForge"
	forge_panel.bind(match_session.world)
	forge_panel.visible = false
	$HUD.add_child(forge_panel)
	var toggle := Button.new()
	toggle.name = "ForgeButton"
	toggle.text = "Item Forge  [I]"
	toggle.custom_minimum_size = Vector2(170, 52)
	toggle.pressed.connect(_toggle_forge)
	%PauseButton.get_parent().add_child(toggle)
	%PauseButton.get_parent().move_child(toggle, %PauseButton.get_index())


func _build_hero_shop_ui() -> void:
	hero_shop_toggle = Button.new()
	hero_shop_toggle.name = "HeroShopButton"
	hero_shop_toggle.text = "Hero Shop  [H]"
	hero_shop_toggle.position = Vector2(1066, 112)
	hero_shop_toggle.size = Vector2(190, 44)
	hero_shop_toggle.pressed.connect(_toggle_hero_shop)
	$HUD.add_child(hero_shop_toggle)
	hero_shop_panel = HeroShopPanel.new()
	hero_shop_panel.name = "HeroShop"
	hero_shop_panel.bind(match_session.world)
	hero_shop_panel.hero_requested.connect(_request_hero)
	$HUD.add_child(hero_shop_panel)


func _request_hero(hero_type: String) -> void:
	if match_session.request_hero_buy(hero_type):
		hero_shop_panel.command_pending = true
		hero_shop_panel.refresh()


func _toggle_hero_shop() -> void:
	if get_tree().paused or not match_session.world.is_running():
		return
	if forge_panel != null and forge_panel.visible:
		forge_panel.set_open(false)
	hero_shop_panel.toggle_open()


func _toggle_forge() -> void:
	if get_tree().paused or not match_session.world.is_running():
		return
	if hero_shop_panel != null and hero_shop_panel.is_open:
		hero_shop_panel.set_open(false)
	forge_panel.toggle_open()
	forge_panel.refresh()


func _build_ai_toggle() -> void:
	# AIPlayer is opt-in in the playable prototype: the default replay remains
	# the historical scheduled-Archer opponent, while this control exposes the
	# migrated red-side policy/recruitment/item/upgrade adapters for manual QA.
	ai_toggle = Button.new()
	ai_toggle.name = "AIToggle"
	ai_toggle.text = "AI lawan  [A] : OFF"
	ai_toggle.custom_minimum_size = Vector2(190, 52)
	ai_toggle.tooltip_text = "Aktifkan AIPlayer native untuk sisi merah"
	ai_toggle.pressed.connect(_toggle_ai)
	%PauseButton.get_parent().add_child(ai_toggle)
	%PauseButton.get_parent().move_child(ai_toggle, %PauseButton.get_index())


func _build_migration_status() -> void:
	# Keep migrated boss/AI state visible without changing the authored scene
	# layout; this also makes Windows QA failures immediately diagnosable.
	migration_status = Label.new()
	migration_status.name = "MigrationStatus"
	migration_status.position = Vector2(28, 104)
	migration_status.size = Vector2(760, 28)
	migration_status.add_theme_font_size_override("font_size", 15)
	migration_status.modulate = Color("b9c7d9")
	$HUD.add_child(migration_status)


func _toggle_ai() -> void:
	var world := match_session.world
	# AI mode is a match transaction: do not change controller ownership while
	# the session is paused or a result overlay has frozen the world.
	if world == null or get_tree().paused or not world.is_running():
		return
	world.set_ai_enabled(not world.ai_enabled)
	if world.ai_enabled:
		world.reset_ai()
	if ai_toggle != null:
		ai_toggle.text = "AI lawan  [A] : ON" if world.ai_enabled else "AI lawan  [A] : OFF"


func _handle_keyboard_input(event: InputEvent) -> bool:
	if not (event is InputEventKey):
		return false
	var key_event := event as InputEventKey
	var tactical_name: String = TACTICAL_KEYS.get(key_event.physical_keycode, "")
	if not tactical_name.is_empty():
		if key_event.echo:
			return true
		if key_event.pressed:
			_start_tactical(tactical_name, tactical_name == "gather")
		else:
			_finish_tactical(tactical_name)
		return true
	if not key_event.pressed or key_event.echo:
		return false
	var handled := true
	match key_event.physical_keycode:
		KEY_ESCAPE:
			if hero_shop_panel != null and hero_shop_panel.is_open:
				hero_shop_panel.set_open(false)
			else:
				handled = false
		KEY_H:
			_toggle_hero_shop()
		KEY_A:
			_toggle_ai()
		KEY_I:
			_toggle_forge()
		KEY_Q:
			match_session.request_skill_q(match_session.selected_id)
		KEY_W:
			match_session.request_skill_w(match_session.selected_id)
		KEY_E:
			match_session.request_skill_e(match_session.selected_id)
		KEY_R:
			match_session.request_skill_r(match_session.selected_id)
		_:
			handled = false
	return handled


func _unhandled_input(event: InputEvent) -> void:
	if _handle_keyboard_input(event):
		get_viewport().set_input_as_handled()
		return
	if (
		event is InputEventMouseButton
		and event.pressed
		and event.button_index == MOUSE_BUTTON_RIGHT
		and event.device != InputEvent.DEVICE_ID_EMULATION
	):
		_command_move(event.position)
		return
	super._unhandled_input(event)


func _command_move(point: Vector2) -> void:
	if not simulation.world.is_running():
		return
	var local := arena.get_global_transform_with_canvas().affine_inverse() * point
	var world := simulation.world as Prototype
	var marked := world.select_at(local)
	var target := world.get_unit(marked)
	if target != null and target.alive and target.team != 0:
		match_session.request_hero_follow(match_session.selected_id, marked)
	else:
		match_session.request_hero_move(match_session.selected_id, local)
	get_viewport().set_input_as_handled()


func _select(point: Vector2) -> void:
	if not simulation.world.is_running():
		return
	match_session.select_at(arena.get_global_transform_with_canvas().affine_inverse() * point)
	get_viewport().set_input_as_handled()


func pause_match() -> void:
	match_session.request_tactical_end()
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	if forge_panel != null:
		forge_panel.set_open(false)
	super.pause_match()
	var world := simulation.world as Prototype
	if not world.is_running():
		%PauseTitle.text = "BIRU MENANG" if world.winner == 0 else "MERAH MENANG"
		%ResumeButton.hide()
		%RestartButton.grab_focus()


func resume_match() -> void:
	if simulation.world.is_running():
		super.resume_match()
