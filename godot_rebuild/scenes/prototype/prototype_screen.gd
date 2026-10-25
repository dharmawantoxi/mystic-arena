# gdlint:disable=max-returns,max-file-lines
extends "res://scenes/combat/combat_screen.gd"
## Separate playable subset; shared input/pause plumbing, no manual laboratory wave controls.

signal next_level_requested(level_number: int)

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const HeroDefinition = preload("res://scripts/data/hero_definition.gd")
const HeroItemInventory = preload("res://scripts/match/hero_item_inventory.gd")
const HeroPanelLayout = preload("res://scripts/ui/hero_panel_layout.gd")
const BuildPopupLayout = preload("res://scripts/ui/build_popup_layout.gd")
const ItemForgePanel = preload("res://scripts/ui/item_forge_panel.gd")
const HeroShopPanel = preload("res://scripts/ui/hero_shop_panel.gd")
const SidePanel = preload("res://scripts/ui/side_panel.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const SaveSlotStore = preload("res://scripts/match/save_slot_store.gd")
const LevelCatalog = preload("res://scripts/match/level_catalog.gd")
const EndOverlayLayout = preload("res://scripts/ui/end_overlay_layout.gd")
## The pause card's dim (PrototypeMatch.tscn); the result layout clears it.
const PAUSE_DIM := Color(0.0392, 0.0392, 0.0784, 0.7843)
const GameSpeedStore = preload("res://scripts/simulation/game_speed_store.gd")
const TouchGestureRuntime = preload("res://scripts/input/touch_gesture_runtime.gd")
const TOUCH_TARGET_MIN := 48.0
const TOUCH_PADDING := 6.0
const TACTICAL_KEYS := {
	KEY_G: "gather",
	KEY_F: "gather",
	KEY_T: "protect_tower",
	KEY_C: "protect_castle",
	KEY_B: "attack_boss",
	KEY_D: "attack_damage_dealer",
}

var progress_path := ProgressStore.PATH
var slot_path_template := SaveSlotStore.PATH_TEMPLATE
var is_replay := false
var result_shown := false
## Layer 9bv5: NEW BEST flags of the saved result, for the overlay's stats panel.
var end_new_best_score := false
var end_new_best_time := false
## Layer 9bv6: `save_data['completed_levels']` after the result was saved.
var end_completed_levels: Array = []
var forge_panel: ItemForgePanel
var hero_shop_panel: HeroShopPanel
var hero_shop_toggle: Button
var side_panel: SidePanel
var ai_toggle: Button
var migration_status: Label
var touch_gestures = TouchGestureRuntime.new()
var _tactical_panel_open := false
var _touch_tactical_claims: Dictionary = {}
@onready var match_session: PrototypeSession = $Simulation
@onready var controller_cursor = %ControllerCursor


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UI_THEME.create_theme()
	arena.session = simulation
	UI_THEME.title(%ArenaTitle, 19)
	UI_THEME.title(%PauseTitle, 32)
	var selected_world := match_session.world as Prototype
	$HUD/TopBar/Row/Names/Description.text = (
		"Lv.%d · %s"
		% [
			selected_world.level_number,
			selected_world.difficulty,
		]
	)
	$HUD/TopBar/Row/Names/Description.tooltip_text = String(
		selected_world.level_config.get("name", "?")
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
	%TacticalToggleButton.toggled.connect(_set_tactical_panel_open)
	%CommandDockToggle.toggled.connect(_set_command_dock_open)
	_build_forge_ui()
	_build_hero_shop_ui()
	_build_ai_toggle()
	_build_migration_status()
	_setup_game_speed_control()
	_build_side_panel()
	%PauseButton.pressed.connect(pause_match)
	%ResumeButton.pressed.connect(resume_match)
	%RestartButton.pressed.connect(func() -> void: restart_requested.emit())
	%NextLevelButton.pressed.connect(_request_next_level)
	%MenuButton.pressed.connect(func() -> void: menu_requested.emit())
	%BackButton.pressed.connect(func() -> void: menu_requested.emit())
	%SaveRetryButton.pressed.connect(_save_result)
	controller_cursor.action_requested.connect(_route_controller_action)
	%SaveRetryButton.hide()
	%NextLevelButton.hide()
	if ai_toggle != null:
		ai_toggle.text = "AI:ON" if match_session.world.ai_enabled else "AI:OFF"
	%PauseButton.grab_focus()


func _setup_game_speed_control() -> void:
	var selector: OptionButton = %GameSpeedSelector
	var speed_runtime: Node = get_tree().root.get_node("GameSpeed")
	for speed in GameSpeedStore.PRESETS:
		selector.add_item("%.1fx" % speed)
	selector.select(int(speed_runtime.call("speed_index")))
	selector.item_selected.connect(_on_game_speed_selected)
	speed_runtime.connect("speed_changed", _sync_game_speed_selector)


func _on_game_speed_selected(index: int) -> void:
	get_tree().root.get_node("GameSpeed").call("set_speed_index", index)


func _sync_game_speed_selector(_speed: float) -> void:
	%GameSpeedSelector.select(int(get_tree().root.get_node("GameSpeed").call("speed_index")))


func _process(_delta: float) -> void:
	var world := simulation.world as Prototype
	_route_touch_actions(touch_gestures.advance(float(Time.get_ticks_msec())))
	var pointer := get_viewport().get_mouse_position()
	if controller_cursor.active:
		pointer = controller_cursor.cursor_position
	var cursor_local := arena.get_global_transform_with_canvas().affine_inverse() * pointer
	match_session.set_tactical_cursor(
		cursor_local, Rect2(Vector2.ZERO, Vector2(1280, 720)).has_point(cursor_local)
	)
	_update_controller_hover()
	_update_tactical_hud(world)
	var hero_panel_state := _hero_panel_state(world, match_session)
	var build_popup_state := _build_popup_state(world, match_session)
	_update_side_panel(world, hero_panel_state, build_popup_state)
	if forge_panel != null and forge_panel.visible:
		forge_panel.refresh()
	if hero_shop_panel != null and hero_shop_panel.visible:
		hero_shop_panel.command_pending = not match_session.command.is_empty()
		hero_shop_panel.refresh()
	# Layer 9bv2: the player's gold and income live in the source gold chip the arena
	# paints at the top-left (only while the side panel is off, like `_draw_gold_hud`);
	# the bar keeps the opponent's gold, which pygame never shows.
	arena.set("gold_hud_visible", side_panel == null or not side_panel.is_active())
	%GoldLabel.text = "AI:%d" % world.economy.gold[1]
	# Layer 9bv4: `_draw_input_hints` only shows the hint bar in controller mode, with the
	# context victory / defeat / shop (the hero shop) / game.
	var hint_context := "game"
	if not world.is_running():
		hint_context = "victory" if world.winner == 0 else "defeat"
	elif hero_shop_panel != null and hero_shop_panel.visible:
		hint_context = "shop"
	var hints: Array = controller_cursor.get_hints(hint_context) if controller_cursor.active else []
	arena.set("input_hints", hints)
	# Layer 9bv7: while an empty build slot is selected the arena paints the source
	# build-tower popup at the slot.
	arena.set("build_popup_state", build_popup_state)
	# Layer 9bv8/9bv9: the hero panel is drawn from this snapshot; pointer and controller
	# actions are routed separately through PrototypeSession and the existing forge.
	arena.set("hero_panel_state", hero_panel_state)
	# Layer 9bv5: once the match ends the arena paints the source victory / defeat overlay.
	arena.set("end_overlay_state", {} if world.is_running() else _end_overlay_state(world))
	%GoldLabel.tooltip_text = (
		"Emas: %d G · Lawan: %d G"
		% [
			world.economy.gold[0],
			world.economy.gold[1],
		]
	)
	var next_wave := "Bersih"
	if world.scheduler.remaining_ticks > 0:
		next_wave = "%.1f s" % (world.scheduler.remaining_ticks / 60.0)
	elif world.scheduler.pending_count() > 0:
		next_wave = "Antrean"
	%TickLabel.text = "W%02d · %s" % [world.wave_count, next_wave]
	%TickLabel.tooltip_text = (
		"Gelombang %02d · berikut: %s"
		% [
			world.wave_count,
			next_wave,
		]
	)
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
	var path_row := tower_option or regen_context or castle_context
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
	%Paths.visible = path_row and not hero_row
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


func _request_next_level() -> void:
	var world := simulation.world as Prototype
	if world.is_running() or world.winner != world.BLUE:
		return
	var next_level := LevelCatalog.get_next_level(world.level_number)
	if next_level >= 0:
		next_level_requested.emit(next_level)


func _save_result() -> void:
	var world := simulation.world as Prototype
	if world.is_running():
		return
	var committed := world.commit_level_result(progress_path, is_replay, slot_path_template)
	if committed.is_empty():
		%Hint.text = ("Progres BELUM tersimpan. Periksa file progres, lalu coba lagi.")
		%SaveRetryButton.show()
		return
	%Hint.text = (
		"Score: %d  ·  +%d Meta Gold tersimpan."
		% [int(committed.match_stats.score), int(committed.reward)]
	)
	%SaveRetryButton.hide()
	end_new_best_score = bool(committed.get("is_new_best_score", false))
	end_new_best_time = bool(committed.get("is_new_best_time", false))
	var saved: Dictionary = committed.get("state", {})
	end_completed_levels = saved.get("completed_levels", []).duplicate()


## Layer 9bv7/9bv9: popup snapshot for the selected empty slot, including its command id.
func _build_popup_state(world: Prototype, match_session: PrototypeSession) -> Dictionary:
	if not world.is_running():
		return {}
	var slot_id := match_session.selected_slot_id
	if slot_id < 0:
		return {}
	var slot := world.get_slot(slot_id)
	if slot == null or slot.structure_id != -1:
		return {}
	var state := {
		"slot_id": slot_id,
		"x": int(slot.position.x),
		"y": int(slot.position.y),
		"gold": int(world.economy.gold[0]),
	}
	if side_panel != null and side_panel.is_active():
		state.merge(BuildPopupLayout.mobile_geometry(side_panel.panel), true)
	return state


## Layer 9bv8/9bv9: selected live hero snapshot shared by the arena painter and input router.
func _hero_panel_state(world: Prototype, match_session: PrototypeSession) -> Dictionary:
	var selected := world.get_unit(match_session.selected_id) as HeroState
	if selected == null or not selected.alive or selected.team != world.BLUE:
		return {}
	var definition: HeroDefinition = selected.settings()
	if definition == null:
		return {}
	var inventory: HeroItemInventory = selected.items
	var item_rows: Array = []
	for index in range(6):
		var item_id := ""
		if inventory != null and index < inventory.slots.size():
			var raw_id: Variant = inventory.slots[index]
			if raw_id != null:
				item_id = String(raw_id)
		if item_id.is_empty():
			item_rows.append({})
			continue
		var item_data: Dictionary = inventory.item(item_id)
		var item_color := _hero_panel_rgb(item_data.get("color", [66, 74, 104]), [66, 74, 104])
		var item_glow := _hero_panel_rgb(item_data.get("glow", item_color), item_color)
		(
			item_rows
			. append(
				{
					"id": item_id,
					"name": String(item_data.get("name", item_id)),
					"color": item_color,
					"glow": item_glow,
					"active": _hero_panel_item_active(inventory, item_id),
					"cooldown": int(inventory.blood_frenzy_cd) if item_id == "demon_maw" else 0,
				}
			)
		)
	var skill_labels: Array = ["Q", "W", "E", "R"]
	if controller_cursor.active:
		skill_labels = [
			String(controller_cursor.get_action_label("skill_q")),
			String(controller_cursor.get_action_label("skill_w")),
			String(controller_cursor.get_action_label("skill_e")),
			String(controller_cursor.get_action_label("skill_r")),
		]
	var state := {
		"alive": true,
		"name": String(definition.title),
		"level": int(selected.level),
		"max_level": HeroDefinition.MAX_HERO_LEVEL,
		"hp": float(selected.hp),
		"max_hp": float(selected.max_hp),
		# The prototype's blue team accent stands in for the source hero-specific tint.
		"color": [115, 203, 187],
		"gold": int(world.economy.gold[world.BLUE]),
		"upgrade_cost": int(selected.upgrade_cost()),
		"auto_cast": bool(selected.auto_cast_enabled),
		"cooldowns":
		[selected.skill_timer, selected.w_cooldown, selected.e_cooldown, selected.r_cooldown],
		"cooldown_max":
		[
			selected.skill_cd_max,
			selected.w_cooldown_max,
			selected.e_cooldown_max,
			selected.r_cooldown_max
		],
		"skill_labels": skill_labels,
		"items": item_rows,
		"cheap_alpha": true,
	}
	if side_panel != null and side_panel.is_active():
		var mobile_origin: Variant = HeroPanelLayout.mobile_panel_origin(side_panel.panel)
		if mobile_origin is Vector2i:
			state["panel_pos"] = [mobile_origin.x, mobile_origin.y]
	return state


func _hero_panel_item_active(inventory: HeroItemInventory, item_id: String) -> bool:
	match item_id:
		"demon_maw":
			return inventory.blood_frenzy_timer > 0
		"scarlet_bulwark":
			return inventory.guard_timer > 0
		"tempest_vane":
			return inventory.veil_timer > 0
		"thunder_coil":
			return inventory.static_timer > 0
		"sanguine_thorn":
			return inventory.rend_timer > 0
		"razor_carapace":
			return inventory.thorn_timer > 0
		"gale_pike":
			return inventory.gale_timer > 0
		"searbrand":
			return _hero_panel_item_cooldown_active(inventory, item_id, "searbrand_cd")
		"astral_codex":
			return _hero_panel_item_cooldown_active(inventory, item_id, "arcane_cd")
		"spectral_charm":
			return inventory.ghost_timer > 0
		"fulgur_scepter":
			return _hero_panel_item_cooldown_active(inventory, item_id, "fulgur_cd")
		"hex_idol":
			return _hero_panel_item_cooldown_active(inventory, item_id, "hex_cd")
		"rift_veil":
			return _hero_panel_item_cooldown_active(inventory, item_id, "rift_cd")
		"vital_stone":
			return _hero_panel_item_cooldown_active(inventory, item_id, "pact_cd")
	return false


func _hero_panel_item_cooldown_active(
	inventory: HeroItemInventory, item_id: String, timer_name: String
) -> bool:
	var cooldown := int(inventory.get(timer_name))
	if cooldown <= 0:
		return false
	var item_data := inventory.item(item_id)
	var active: Dictionary = item_data.get("active", {})
	return cooldown > int(active.get("cooldown", 0)) - 30


func _hero_panel_rgb(value: Variant, fallback: Array) -> Array:
	if value is Array and value.size() >= 3:
		return [int(value[0]), int(value[1]), int(value[2])]
	if value is Color:
		return [int(value.r8), int(value.g8), int(value.b8)]
	return fallback.duplicate()


## `Game.draw`'s arguments for `ui.draw_overlay`: title, colour and action line (input labels
## follow the controller like `_input_label`), plus the stats `Overlay._draw_stats` reads.
func _end_overlay_state(world: Prototype) -> Dictionary:
	var victory := world.winner == world.BLUE
	var labels := {"next_level": "N", "replay": "R", "to_menu": "ESC"}
	if controller_cursor.active:
		for action in labels.keys():
			labels[action] = controller_cursor.get_action_label(action)
	var has_next := LevelCatalog.get_next_level(world.level_number) >= 0
	var stats := world.match_stats_snapshot()
	return {
		"title": ("VICTORY! LV.%d" if victory else "DEFEAT LV.%d") % world.level_number,
		"victory": victory,
		"color": EndOverlayLayout.VICTORY_COLOR if victory else EndOverlayLayout.DEFEAT_COLOR,
		"action": EndOverlayLayout.action_text(victory, has_next, labels),
		"stats":
		[
			int(stats.get("score", 0)),
			int(stats.get("time_seconds", 0)),
			world.wave_count,
			int(stats.get("kills", 0)),
			int(stats.get("combo", 0)),
			end_new_best_score,
			end_new_best_time,
		],
		"achievements": world.achievements_unlocked.size(),
		"unlock": _unlock_popup_state(world) if victory else {},
	}


## Layer 9bv6: `_get_newly_unlocked_level` + `get_level_config` + the true boss entry the
## unlock popup reads; empty unless this win just opened a level that was never won.
func _unlock_popup_state(world: Prototype) -> Dictionary:
	var next_level := LevelCatalog.get_next_level(world.level_number)
	if next_level < 0:
		return {}
	if world.level_number not in end_completed_levels or next_level in end_completed_levels:
		return {}
	var config := LevelCatalog.get_level_config(next_level)
	if config.is_empty():
		return {}
	var bosses: Dictionary = world.boss_table.get("bosses", {})
	var entry: Dictionary = bosses.get(String(config.get("true_boss", "abaddon")), {})
	return {
		"level": next_level,
		"name": String(config.get("name", "")),
		"hp_mult": float(config.get("enemy_hp_mult", 1.0)),
		"difficulty": world.difficulty,
		"boss":
		{
			"name": String(entry.get("name", "???")),
			"boss_class": String(entry.get("boss_class", "true")),
			"color": _rgb(entry.get("color", null)),
			"entrance_color": _rgb(entry.get("entrance_color", null)),
		},
	}


static func _rgb(value: Variant) -> Array:
	if value is Array and value.size() >= 3:
		return [int(value[0]), int(value[1]), int(value[2])]
	if value is Color:
		return [value.r8, value.g8, value.b8]
	return [150, 100, 200]


## Layer 9bv5: at the end the painted source overlay owns the screen, so the pause card loses
## its dim and title and moves to the bottom-left as a compact button card (touch still works).
func _set_result_layout(result: bool) -> void:
	var dim := pause_overlay as ColorRect
	if dim != null:
		dim.color = Color(0.0, 0.0, 0.0, 0.0) if result else PAUSE_DIM
	# The see-through result layer lets clicks reach the painted PLAY NEXT LEVEL button.
	pause_overlay.mouse_filter = (
		Control.MOUSE_FILTER_IGNORE if result else Control.MOUSE_FILTER_STOP
	)
	%PauseTitle.visible = not result
	var center: Control = $HUD/PauseOverlay/Center
	if result:
		center.set_anchors_and_offsets_preset(
			Control.PRESET_BOTTOM_LEFT, Control.PRESET_MODE_MINSIZE, 16
		)
	else:
		center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


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
	# Layer 9bi2: the feedback banner is painted by the arena view (`draw_ui` order).


func _build_side_panel() -> void:
	# Layer 9as: `mobile/sidepanel.py` - on screens wider than 16:9 the
	# leftover width right of the 1280 px arena becomes the stone panel with
	# PAUSE / STATUS / HEROES / TACTICAL COMMANDS; the floating tactical box
	# moves there, exactly like the source hid its floating panels.
	side_panel = SidePanel.new()
	side_panel.name = "SidePanel"
	side_panel.pause_requested.connect(pause_match)
	side_panel.tactical_down.connect(_start_panel_tactical)
	side_panel.tactical_up.connect(_finish_tactical)
	side_panel.overlay_pressed.connect(_handle_side_panel_overlay_press)
	$HUD.add_child(side_panel)
	get_viewport().size_changed.connect(_layout_side_panel)
	_layout_side_panel()


func _layout_side_panel() -> void:
	if side_panel == null:
		return
	side_panel.configure(int(get_viewport().get_visible_rect().size.x))
	var docked := side_panel.is_active()
	%TacticalToggleButton.visible = not docked
	%TacticalPanel.visible = _tactical_panel_open and not docked


func _set_tactical_panel_open(open: bool) -> void:
	_tactical_panel_open = open
	if side_panel == null or not side_panel.is_active():
		%TacticalPanel.visible = open


func _set_command_dock_open(open: bool) -> void:
	%BottomBar.visible = open
	%CommandDockToggle.text = "Tutup" if open else "Kontrol"


func _update_side_panel(
	world: Prototype, hero_panel_state: Dictionary, build_popup_state: Dictionary
) -> void:
	if side_panel == null or not side_panel.is_active():
		return
	var snapshot := _side_panel_snapshot(world)
	snapshot["hero_panel_state"] = hero_panel_state
	snapshot["build_popup_state"] = build_popup_state
	# Match SidePanel.hit_test: visible popups cover dock tactical controls.
	snapshot["popup_open"] = (
		bool(snapshot.get("popup_open", false))
		or not hero_panel_state.is_empty()
		or not build_popup_state.is_empty()
	)
	side_panel.update_snapshot(snapshot)


## Source `SidePanel.draw(game)` reads: gold, difficulty, level/wave, the
## castle shield flag, `game.heroes` (paid blue roster in summon order with
## `is_skill_ready`), the live boss, the AI roster and the held command.
func _side_panel_snapshot(world: Prototype) -> Dictionary:
	var state := "playing"
	if not world.is_running():
		state = "victory" if world.winner == 0 else "defeat"
	var heroes: Array = []
	for hero_value in world.player_roster():
		var hero: HeroState = hero_value
		var ready: Array = []
		if hero.skill_timer <= 0:
			ready.append("q")
		if hero.w_cooldown <= 0:
			ready.append("w")
		if hero.e_cooldown <= 0:
			ready.append("e")
		if hero.r_cooldown <= 0:
			ready.append("r")
		(
			heroes
			. append(
				{
					"name": hero.settings().display_name,
					"alive": hero.alive,
					"level": hero.level,
					"hp": hero.hp,
					"max_hp": hero.max_hp,
					"ready": ready,
				}
			)
		)
	var has_enemy_hero := false
	for enemy in world.ai_roster_heroes():
		if enemy.alive:
			has_enemy_hero = true
	var blue_nexus = world.nexuses[0]
	return {
		"state": state,
		"gold": int(world.economy.gold[0]),
		"difficulty": world.difficulty,
		"wave": world.wave_count,
		"level": world.level_number,
		"shield_active": blue_nexus != null and bool(blue_nexus.shield_active),
		"heroes": heroes,
		"has_boss": world.active_boss != null and world.active_boss.alive,
		"has_enemy_hero": has_enemy_hero,
		"held": world.tactical.held_command,
		"popup_open":
		(
			(forge_panel != null and forge_panel.visible)
			or (hero_shop_panel != null and hero_shop_panel.visible)
		),
	}


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
	toggle.text = "Item"
	toggle.custom_minimum_size = Vector2(84, 36)
	toggle.tooltip_text = "Item Forge [I]"
	toggle.pressed.connect(_toggle_forge)
	%PauseButton.get_parent().add_child(toggle)
	%PauseButton.get_parent().move_child(toggle, %PauseButton.get_index())


func _build_hero_shop_ui() -> void:
	hero_shop_toggle = Button.new()
	hero_shop_toggle.name = "HeroShopButton"
	hero_shop_toggle.text = "Hero"
	hero_shop_toggle.custom_minimum_size = Vector2(76, 36)
	hero_shop_toggle.tooltip_text = "Hero Shop [H]"
	hero_shop_toggle.toggle_mode = true
	hero_shop_toggle.pressed.connect(_toggle_hero_shop)
	var top_row: HBoxContainer = $HUD/TopBar/Row
	top_row.add_child(hero_shop_toggle)
	top_row.move_child(hero_shop_toggle, %PauseButton.get_index())
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
	if hero_shop_toggle != null:
		hero_shop_toggle.button_pressed = hero_shop_panel.is_open


func _toggle_forge() -> void:
	if get_tree().paused or not match_session.world.is_running():
		return
	if hero_shop_panel != null and hero_shop_panel.is_open:
		hero_shop_panel.set_open(false)
		if hero_shop_toggle != null:
			hero_shop_toggle.button_pressed = false
	forge_panel.toggle_open()
	forge_panel.refresh()


func _build_ai_toggle() -> void:
	# AIPlayer is opt-in in the playable prototype: the default replay remains
	# the historical scheduled-Archer opponent, while this control exposes the
	# migrated red-side policy/recruitment/item/upgrade adapters for manual QA.
	ai_toggle = Button.new()
	ai_toggle.name = "AIToggle"
	ai_toggle.text = "AI:OFF"
	ai_toggle.custom_minimum_size = Vector2(76, 36)
	ai_toggle.tooltip_text = "Aktifkan AIPlayer native untuk sisi merah [A]"
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
		ai_toggle.text = "AI:ON" if world.ai_enabled else "AI:OFF"


func _handle_keyboard_input(event: InputEvent) -> bool:
	if not (event is InputEventKey):
		return false
	var key_event := event as InputEventKey
	var world := match_session.world as Prototype
	if not world.is_running():
		if not key_event.pressed or key_event.echo:
			return false
		match key_event.physical_keycode:
			KEY_R:
				restart_requested.emit()
			KEY_N:
				_request_next_level()
			KEY_ESCAPE:
				menu_requested.emit()
			_:
				return false
		return true
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
				var skipped_intro := world.skip_boss_intro(KEY_ESCAPE)
				var skipped_death := world.skip_boss_death(KEY_ESCAPE)
				handled = skipped_intro or skipped_death
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
		KEY_SPACE, KEY_ENTER:
			var code := key_event.physical_keycode
			var skipped_level := world.skip_level_intro(code)
			var skipped_intro := world.skip_boss_intro(code)
			var skipped_death := world.skip_boss_death(code)
			handled = skipped_level or skipped_intro or skipped_death
		_:
			handled = false
	return handled


func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch or event is InputEventScreenDrag:
		_handle_touch_event(event)


func _handle_touch_event(event: InputEvent, now_ms: float = -1.0) -> bool:
	if now_ms < 0.0:
		now_ms = float(Time.get_ticks_msec())
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		var touch_id := int(touch.index)
		if touch.pressed:
			var tactical_button := _touch_tactical_button_at(touch.position)
			if tactical_button != null and not tactical_button.disabled:
				_touch_tactical_claims[touch_id] = tactical_button
				tactical_button.button_down.emit()
			else:
				_route_touch_actions(touch_gestures.touch_down(touch_id, touch.position, now_ms))
		else:
			var claimed := _touch_tactical_claims.get(touch_id) as Button
			if claimed != null:
				_touch_tactical_claims.erase(touch_id)
				claimed.button_up.emit()
			elif touch.canceled:
				touch_gestures.cancel_touch(touch_id)
			else:
				_route_touch_actions(touch_gestures.touch_up(touch_id, touch.position, now_ms))
		get_viewport().set_input_as_handled()
		return true
	if event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		var touch_id := int(drag.index)
		if not _touch_tactical_claims.has(touch_id):
			_route_touch_actions(touch_gestures.touch_motion(touch_id, drag.position))
		get_viewport().set_input_as_handled()
		return true
	return false


func _route_touch_actions(actions: Array[Dictionary]) -> void:
	for action in actions:
		match String(action.kind):
			"tap":
				_touch_tap(Vector2(action.pos))
			"long_press":
				_touch_long_press(Vector2(action.pos))
			"scroll":
				var amount := -50 if float(action.value) < 0.0 else 50
				_scroll_ui(amount, Vector2(action.pos))


func _touch_tap(point: Vector2) -> void:
	if _overlay_action_rect_at(point) != null or _overlay_panel_captures_pointer(point):
		_primary_action(point)
		return
	var button := _touch_button_at(point)
	if button != null:
		if not button.disabled:
			if button.toggle_mode:
				button.button_pressed = not button.button_pressed
			button.pressed.emit()
		return
	if forge_panel != null and forge_panel.visible:
		_touch_forge_background(point, MOUSE_BUTTON_LEFT)
		return
	if get_tree().paused or _controller_modal_open():
		return
	_primary_action(point)


func _touch_long_press(point: Vector2) -> void:
	if _overlay_panel_captures_pointer(point):
		_handle_overlay_pointer(point, MOUSE_BUTTON_RIGHT)
		return
	var button := _touch_button_at(point)
	if button != null:
		if not button.disabled:
			var mouse := InputEventMouseButton.new()
			mouse.button_index = MOUSE_BUTTON_RIGHT
			mouse.pressed = true
			mouse.position = point
			button.gui_input.emit(mouse)
		return
	if forge_panel != null and forge_panel.visible:
		_touch_forge_background(point, MOUSE_BUTTON_RIGHT)
		return
	if get_tree().paused or _controller_modal_open():
		return
	if _handle_overlay_pointer(point, MOUSE_BUTTON_RIGHT):
		return
	_command_move(point)


func _touch_forge_background(point: Vector2, button_index: int) -> void:
	var mouse := InputEventMouseButton.new()
	mouse.button_index = (
		MOUSE_BUTTON_RIGHT if button_index == MOUSE_BUTTON_RIGHT else MOUSE_BUTTON_LEFT
	)
	mouse.pressed = true
	mouse.position = point
	forge_panel._input(mouse)


func _touch_button_rect(button: Button) -> Rect2:
	var rect := button.get_global_rect().grow(TOUCH_PADDING)
	if rect.size.x < TOUCH_TARGET_MIN:
		rect = (
			rect
			. grow_individual(
				(TOUCH_TARGET_MIN - rect.size.x) * 0.5,
				0.0,
				(TOUCH_TARGET_MIN - rect.size.x) * 0.5,
				0.0,
			)
		)
	if rect.size.y < TOUCH_TARGET_MIN:
		rect = (
			rect
			. grow_individual(
				0.0,
				(TOUCH_TARGET_MIN - rect.size.y) * 0.5,
				0.0,
				(TOUCH_TARGET_MIN - rect.size.y) * 0.5,
			)
		)
	return rect


func _touch_button_at(point: Vector2) -> Button:
	for button in _controller_buttons(true):
		if _touch_button_rect(button).has_point(point):
			return button
	return null


func _touch_tactical_button_at(point: Vector2) -> Button:
	if get_tree().paused or not simulation.world.is_running() or _controller_modal_open():
		return null
	for button in [
		%GatherButton,
		%ProtectTowerButton,
		%ProtectCastleButton,
		%AttackBossButton,
		%AttackDealerButton,
	]:
		if button.is_visible_in_tree() and _touch_button_rect(button).has_point(point):
			return button
	return null


func _cancel_touch_input() -> void:
	for value in _touch_tactical_claims.values():
		var button := value as Button
		if button != null:
			button.button_up.emit()
	_touch_tactical_claims.clear()
	touch_gestures.cancel()


func _point_in_arena(point: Vector2) -> bool:
	var local := arena.get_global_transform_with_canvas().affine_inverse() * point
	return Rect2(Vector2.ZERO, Vector2(1280, 720)).has_point(local)


func _handle_side_panel_overlay_press(screen_position: Vector2i, button_index: int) -> void:
	_handle_overlay_pointer(Vector2(screen_position), button_index)


func _touch_target_rect(rect: Rect2i) -> Rect2i:
	# Source InputHandler._touch_rect: minimum 48 px, centred on the visual rect,
	# with 6 px padding for larger controls. It is used by mouse and touch alike.
	var target_size := Vector2i(
		maxi(rect.size.x + int(TOUCH_PADDING * 2.0), int(TOUCH_TARGET_MIN)),
		maxi(rect.size.y + int(TOUCH_PADDING * 2.0), int(TOUCH_TARGET_MIN))
	)
	var center := rect.position + Vector2i(rect.size.x >> 1, rect.size.y >> 1)
	var half := Vector2i(target_size.x >> 1, target_size.y >> 1)
	return Rect2i(center - half, target_size)


func _hero_panel_action_entries(state: Dictionary) -> Array[Dictionary]:
	var screen_space := state.has("panel_pos")
	var entries: Array[Dictionary] = [
		{
			"id": "hero_close",
			"rect": HeroPanelLayout.close_rect(state),
			"screen_space": screen_space,
		},
		{
			"id": "toggle_autocast",
			"rect": HeroPanelLayout.autocast_rect(state),
			"screen_space": screen_space,
		},
	]
	for index in range(HeroPanelLayout.ITEM_COUNT):
		(
			entries
			. append(
				{
					"id": "hero_item_slot_%d" % index,
					"rect": HeroPanelLayout.item_slot_rect(state, index),
					"screen_space": screen_space,
				}
			)
		)
	(
		entries
		. append(
			{
				"id": "hero_open_items",
				"rect": HeroPanelLayout.item_shop_rect(state),
				"screen_space": screen_space,
			}
		)
	)
	if int(state.get("level", 1)) < int(state.get("max_level", HeroDefinition.MAX_HERO_LEVEL)):
		(
			entries
			. append(
				{
					"id": "popup_upgrade_hero",
					"rect": HeroPanelLayout.upgrade_rect(state),
					"screen_space": screen_space,
				}
			)
		)
	return entries


func _build_popup_action_entries(state: Dictionary) -> Array[Dictionary]:
	var screen_space := state.has("panel_pos")
	var entries: Array[Dictionary] = [
		{
			"id": "build_close",
			"rect": BuildPopupLayout.state_close_rect(state),
			"screen_space": screen_space,
		}
	]
	for index in range(4):
		var path: String = ["archer", "cannon", "ice", "mage"][index]
		(
			entries
			. append(
				{
					"id": "build_" + path,
					"rect": BuildPopupLayout.state_button_rect(state, index),
					"screen_space": screen_space,
				}
			)
		)
	return entries


func _overlay_action_entries() -> Array[Dictionary]:
	var entries: Array[Dictionary] = []
	if get_tree().paused or _controller_modal_open():
		return entries
	var world := match_session.world as Prototype
	if world == null or not world.is_running():
		return entries
	var hero_state: Dictionary = arena.get("hero_panel_state")
	if not hero_state.is_empty():
		entries.append_array(_hero_panel_action_entries(hero_state))
	var build_state: Dictionary = arena.get("build_popup_state")
	if not build_state.is_empty():
		entries.append_array(_build_popup_action_entries(build_state))
	return entries


func _overlay_point(point: Vector2, state: Dictionary) -> Vector2i:
	if state.has("panel_pos"):
		return Vector2i(point)
	return Vector2i(arena.get_global_transform_with_canvas().affine_inverse() * point)


func _overlay_target_screen_rect(entry: Dictionary, target: Rect2i) -> Rect2:
	if bool(entry.get("screen_space", false)):
		return Rect2(Vector2(target.position), Vector2(target.size))
	var transform := arena.get_global_transform_with_canvas()
	var corners: Array[Vector2] = [
		transform * Vector2(target.position),
		transform * Vector2(target.position + Vector2i(target.size.x, 0)),
		transform * Vector2(target.position + target.size),
		transform * Vector2(target.position + Vector2i(0, target.size.y)),
	]
	var left := corners[0].x
	var top := corners[0].y
	var right := corners[0].x
	var bottom := corners[0].y
	for corner in corners:
		left = minf(left, corner.x)
		top = minf(top, corner.y)
		right = maxf(right, corner.x)
		bottom = maxf(bottom, corner.y)
	return Rect2(Vector2(left, top), Vector2(right - left, bottom - top))


func _overlay_action_rect_at(point: Vector2) -> Variant:
	for entry in _overlay_action_entries():
		var state_point := Vector2i(point)
		if not bool(entry.get("screen_space", false)):
			state_point = Vector2i(
				arena.get_global_transform_with_canvas().affine_inverse() * point
			)
		var target: Rect2i = _touch_target_rect(entry["rect"])
		if target.has_point(state_point):
			return _overlay_target_screen_rect(entry, target)
	return null


func _overlay_panel_captures_pointer(point: Vector2) -> bool:
	if get_tree().paused or _controller_modal_open():
		return false
	var world := match_session.world as Prototype
	if world == null or not world.is_running():
		return false
	var hero_state: Dictionary = arena.get("hero_panel_state")
	if (
		not hero_state.is_empty()
		and HeroPanelLayout.panel_rect(hero_state).has_point(_overlay_point(point, hero_state))
	):
		return true
	var build_state: Dictionary = arena.get("build_popup_state")
	if not build_state.is_empty():
		var panel_rect := Rect2i(
			BuildPopupLayout.state_origin(build_state),
			Vector2i(BuildPopupLayout.state_width(build_state), BuildPopupLayout.POPUP_H)
		)
		return panel_rect.has_point(_overlay_point(point, build_state))
	return false


func _overlay_captures_pointer(point: Vector2) -> bool:
	if _overlay_panel_captures_pointer(point):
		return true
	# BuildPopup closes on an unclaimed click before the source dispatches the world click.
	var build_state: Dictionary = arena.get("build_popup_state")
	return not build_state.is_empty() and not get_tree().paused and not _controller_modal_open()


func _handle_overlay_pointer(point: Vector2, button_index: int) -> bool:
	if get_tree().paused or _controller_modal_open():
		return false
	var world := match_session.world as Prototype
	if world == null or not world.is_running():
		return false
	var hero_state: Dictionary = arena.get("hero_panel_state")
	if not hero_state.is_empty():
		var hero_point := _overlay_point(point, hero_state)
		if button_index == MOUSE_BUTTON_LEFT:
			for entry in _hero_panel_action_entries(hero_state):
				var rect: Rect2i = entry["rect"]
				if _touch_target_rect(rect).has_point(hero_point):
					_activate_hero_panel_action(String(entry["id"]))
					return true
		if HeroPanelLayout.panel_rect(hero_state).has_point(hero_point):
			# The source handler consumes every click inside HeroPanel. Its intended
			# right-click item-drop branch is unreachable behind its button == 1 guard.
			return true

	var build_state: Dictionary = arena.get("build_popup_state")
	if build_state.is_empty():
		return false
	if button_index == MOUSE_BUTTON_LEFT:
		var build_point := _overlay_point(point, build_state)
		for entry in _build_popup_action_entries(build_state):
			var rect: Rect2i = entry["rect"]
			if not _touch_target_rect(rect).has_point(build_point):
				continue
			var action := String(entry["id"])
			if action == "build_close":
				match_session.selected_slot_id = -1
			else:
				var slot_id := int(build_state.get("slot_id", match_session.selected_slot_id))
				match_session.request_build(slot_id, action.replace("build_", ""))
			return true
	# Source closes an unclaimed build popup and continues dispatching the click to the world.
	match_session.selected_slot_id = -1
	return false


func _activate_hero_panel_action(action_id: String) -> void:
	if action_id == "hero_close":
		match_session.selected_id = -1
		return
	var world := match_session.world as Prototype
	var hero := world.get_unit(match_session.selected_id) as HeroState
	if hero == null or not hero.alive or hero.team != world.BLUE:
		return
	match action_id:
		"popup_upgrade_hero":
			match_session.request_hero_upgrade(hero.id)
		"toggle_autocast":
			match_session.request_autocast(hero.id)
		"hero_open_items":
			_open_item_forge_for_hero(hero.id)
		_:
			if action_id.begins_with("hero_item_slot_"):
				var slot_index := int(action_id.substr("hero_item_slot_".length()))
				var inspect_item := ""
				if slot_index >= 0 and slot_index < hero.items.slots.size():
					var raw_item: Variant = hero.items.slots[slot_index]
					if raw_item != null:
						var item_id := String(raw_item)
						if not hero.items.item(item_id).is_empty():
						inspect_item = item_id
				_open_item_forge_for_hero(hero.id, inspect_item)


func _open_item_forge_for_hero(hero_id: int, inspect_item: String = "") -> void:
	var world := match_session.world as Prototype
	if forge_panel == null or world.forge == null:
		return
	if hero_shop_panel != null and hero_shop_panel.is_open:
		hero_shop_panel.set_open(false)
		if hero_shop_toggle != null:
			hero_shop_toggle.button_pressed = false
	world.forge.set_selected(hero_id)
	world.forge.set_target(hero_id)
	var shop: Object = forge_panel.shop()
	if shop == null:
		return
	if not inspect_item.is_empty():
		shop.inspect_item = inspect_item
	forge_panel.set_open(true)


func _primary_action(point: Vector2) -> void:
	if get_tree().paused or _controller_modal_open():
		return
	if _handle_overlay_pointer(point, MOUSE_BUTTON_LEFT):
		return
	var world := simulation.world as Prototype
	if not world.is_running() or not _point_in_arena(point):
		return
	world.skip_level_intro(-1, true)
	world.skip_boss_intro(-1, true)
	world.skip_boss_death(-1, true)
	var local := arena.get_global_transform_with_canvas().affine_inverse() * point
	var slot_id := world.slot_at(local)
	if slot_id >= 0:
		match_session.select_at(local)
		return
	var marked := world.select_at(local)
	var target := world.get_unit(marked)
	if target == null and _handle_shop_click(world, local):
		return
	var selected := world.get_unit(match_session.selected_id) as HeroState
	var target_hero := target as HeroState
	var target_structure := target as Structure
	var structure_is_selectable := false
	if target_structure != null:
		structure_is_selectable = (
			target_structure.team == world.BLUE
			or target_structure.settings().structure_kind == "nexus"
		)
	if (target_hero != null and target_hero.team == world.BLUE) or structure_is_selectable:
		match_session.select_at(local)
	elif selected != null and selected.alive and selected.team == world.BLUE:
		if target != null and target.alive and target.team != world.BLUE:
			match_session.request_hero_follow(selected.id, target.id)
		else:
			match_session.request_hero_move(selected.id, local)
	else:
		match_session.select_at(local)


func _handle_shop_click(world: Prototype, local: Vector2) -> bool:
	var clicked_shop: Variant = world.clicked_shop_at(local)
	if clicked_shop == null:
		return false
	var label := String(clicked_shop)
	if label == "item":
		_toggle_forge()
		return true
	if label == "hero":
		_toggle_hero_shop()
		return true
	return false


func level_intro_state() -> Dictionary:
	var world := match_session.world as Prototype
	return world.level_intro_state(OS.has_feature("android"))


func boss_intro_state() -> Dictionary:
	var world := match_session.world as Prototype
	return world.boss_intro_state()


func boss_death_state() -> Dictionary:
	var world := match_session.world as Prototype
	return world.boss_death_state()


func _route_controller_action(action: String) -> void:
	var world := match_session.world as Prototype
	if not world.is_running():
		_route_controller_result(action, world)
		return
	if get_tree().paused:
		_route_controller_pause(action)
		return
	match action:
		"confirm":
			if not _controller_activate_hover() and not _controller_modal_open():
				_select(controller_cursor.cursor_position)
		"cancel":
			if hero_shop_panel != null and hero_shop_panel.is_open:
				hero_shop_panel.set_open(false)
			elif forge_panel != null and forge_panel.visible:
				forge_panel.set_open(false)
			elif match_session.selected_id >= 0 or match_session.selected_slot_id >= 0:
				match_session.selected_id = -1
				match_session.selected_slot_id = -1
			else:
				pause_match()
		"skill_q":
			match_session.request_skill_q(match_session.selected_id)
			controller_cursor.rumble(0.4, 10)
		"skill_w":
			match_session.request_skill_w(match_session.selected_id)
			controller_cursor.rumble(0.4, 10)
		"skill_e":
			match_session.request_skill_e(match_session.selected_id)
			controller_cursor.rumble(0.4, 10)
		"skill_r":
			match_session.request_skill_r(match_session.selected_id)
			controller_cursor.rumble(0.8, 20)
		"start", "back":
			pause_match()
		"left_trigger":
			_toggle_hero_shop()
		"right_trigger":
			_command_move(controller_cursor.cursor_position)
		"stick_right":
			_controller_snap()
		"scroll_up":
			_controller_scroll(-50)
		"scroll_down":
			_controller_scroll(50)
		"dpad_up":
			if _controller_modal_open():
				_controller_scroll(-50)
			else:
				controller_cursor.nudge_cursor(Vector2(0, -80))
		"dpad_down":
			if _controller_modal_open():
				_controller_scroll(50)
			else:
				controller_cursor.nudge_cursor(Vector2(0, 80))
		"dpad_left":
			controller_cursor.nudge_cursor(Vector2(-100, 0))
		"dpad_right":
			controller_cursor.nudge_cursor(Vector2(100, 0))


func _route_controller_result(action: String, world: Prototype) -> void:
	match action:
		"confirm":
			if world.winner == world.BLUE and LevelCatalog.get_next_level(world.level_number) >= 0:
				controller_cursor.rumble(0.4, 10)
				_request_next_level()
			else:
				_controller_activate_hover()
		"skill_q":
			controller_cursor.rumble(0.4, 10)
			restart_requested.emit()
		"skill_r":
			controller_cursor.rumble(0.8, 20)
			if world.winner == world.BLUE and LevelCatalog.get_next_level(world.level_number) >= 0:
				_request_next_level()
			else:
				restart_requested.emit()
		"back":
			menu_requested.emit()
		"stick_right":
			_controller_snap()
		"scroll_up":
			_controller_scroll(-50)
		"scroll_down":
			_controller_scroll(50)


func _route_controller_pause(action: String) -> void:
	match action:
		"confirm":
			_controller_activate_hover()
		"cancel", "start", "back":
			resume_match()
		"stick_right":
			_controller_snap()


func _controller_modal_open() -> bool:
	return (
		(hero_shop_panel != null and hero_shop_panel.is_open)
		or (forge_panel != null and forge_panel.visible)
	)


func _controller_button_roots() -> Array[Node]:
	var roots: Array[Node] = []
	var world := match_session.world as Prototype
	if get_tree().paused or not world.is_running():
		roots.append(%PauseOverlay)
	elif hero_shop_panel != null and hero_shop_panel.is_open:
		roots.append(hero_shop_panel)
	elif forge_panel != null and forge_panel.visible:
		roots.append(forge_panel)
	else:
		roots.append(self)
	return roots


func _controller_buttons(include_disabled: bool = false) -> Array[Button]:
	var buttons: Array[Button] = []
	for root_node in _controller_button_roots():
		for node in root_node.find_children("*", "Button", true, false):
			var button := node as Button
			if (
				button != null
				and button.is_visible_in_tree()
				and (include_disabled or not button.disabled)
			):
				buttons.append(button)
	return buttons


func _controller_hover_button() -> Button:
	for button in _controller_buttons():
		if button.get_global_rect().has_point(controller_cursor.cursor_position):
			return button
	return null


func _controller_activate_hover() -> bool:
	var pointer := controller_cursor.cursor_position
	if _overlay_action_rect_at(pointer) != null or _overlay_panel_captures_pointer(pointer):
		_primary_action(pointer)
		return true
	var button := _controller_hover_button()
	if button != null:
		button.pressed.emit()
		return true
	if _overlay_captures_pointer(pointer):
		_primary_action(pointer)
		return true
	return false


func _controller_snap() -> void:
	var rects: Array[Rect2] = []
	for button in _controller_buttons():
		var button_rect := button.get_global_rect()
		if _overlay_panel_captures_pointer(button_rect.get_center()):
			continue
		rects.append(button_rect)
	for entry in _overlay_action_entries():
		var target: Rect2i = _touch_target_rect(entry["rect"])
		rects.append(_overlay_target_screen_rect(entry, target))
	controller_cursor.snap_to_nearest(rects)
	_update_controller_hover()


func _controller_scroll(amount: int) -> void:
	_scroll_ui(amount, controller_cursor.cursor_position)


func _scroll_ui(amount: int, point: Vector2) -> void:
	var fallback: ScrollContainer
	for root_node in _controller_button_roots():
		for node in root_node.find_children("*", "ScrollContainer", true, false):
			var scroll := node as ScrollContainer
			if scroll == null or not scroll.is_visible_in_tree():
				continue
			if fallback == null:
				fallback = scroll
			if scroll.get_global_rect().has_point(point):
				scroll.scroll_vertical += amount
				return
	if fallback != null:
		fallback.scroll_vertical += amount


func _update_controller_hover() -> void:
	if not controller_cursor.active:
		controller_cursor.set_hover_rect(Rect2(), false)
		return
	var overlay_rect: Variant = _overlay_action_rect_at(controller_cursor.cursor_position)
	if overlay_rect is Rect2:
		controller_cursor.set_hover_rect(overlay_rect, true)
		return
	if _overlay_panel_captures_pointer(controller_cursor.cursor_position):
		controller_cursor.set_hover_rect(Rect2(), false)
		return
	var button := _controller_hover_button()
	controller_cursor.set_hover_rect(
		Rect2() if button == null else button.get_global_rect(), button != null
	)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch or event is InputEventScreenDrag:
		# Screen gestures are consumed in _input before GUI/unhandled routing.
		get_viewport().set_input_as_handled()
		return
	if _handle_keyboard_input(event):
		get_viewport().set_input_as_handled()
		return
	if result_shown and event is InputEventMouseButton:
		# Layer 9bv6: only the painted PLAY NEXT LEVEL button takes clicks on the result
		# screen (the arena stays inert, as it was under the old full-screen card).
		if event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			var local: Vector2 = (
				arena.get_global_transform_with_canvas().affine_inverse() * event.position
			)
			var button: Rect2 = arena.call("unlock_play_rect")
			if button.has_area() and button.has_point(local):
				_request_next_level()
		get_viewport().set_input_as_handled()
		return
	if (
		event is InputEventMouseButton
		and event.pressed
		and event.device != InputEvent.DEVICE_ID_EMULATION
	):
		if event.button_index == MOUSE_BUTTON_LEFT:
			_primary_action(event.position)
			get_viewport().set_input_as_handled()
			return
		if event.button_index == MOUSE_BUTTON_RIGHT:
			if _handle_overlay_pointer(event.position, MOUSE_BUTTON_RIGHT):
				get_viewport().set_input_as_handled()
				return
			_command_move(event.position)
			return
	super._unhandled_input(event)


func _command_move(point: Vector2) -> void:
	var world := simulation.world as Prototype
	if (
		get_tree().paused
		or _controller_modal_open()
		or not world.is_running()
		or not _point_in_arena(point)
	):
		return
	var selected := world.get_unit(match_session.selected_id) as HeroState
	if selected == null or not selected.alive or selected.team != world.BLUE:
		return
	var local := arena.get_global_transform_with_canvas().affine_inverse() * point
	match_session.request_hero_move(selected.id, local)
	get_viewport().set_input_as_handled()


func _select(point: Vector2) -> void:
	_primary_action(point)
	get_viewport().set_input_as_handled()


func pause_match() -> void:
	_cancel_touch_input()
	match_session.request_tactical_end()
	if hero_shop_panel != null:
		hero_shop_panel.set_open(false)
	if forge_panel != null:
		forge_panel.set_open(false)
	super.pause_match()
	var world := simulation.world as Prototype
	if world.is_running():
		_set_result_layout(false)
		%PauseTitle.text = "Permainan Dijeda"
		%ResumeButton.show()
		%NextLevelButton.hide()
		return
	_set_result_layout(true)
	%PauseTitle.text = "BIRU MENANG" if world.winner == world.BLUE else "MERAH MENANG"
	%ResumeButton.hide()
	var has_next := (
		world.winner == world.BLUE and LevelCatalog.get_next_level(world.level_number) >= 0
	)
	%NextLevelButton.visible = has_next
	if has_next:
		%NextLevelButton.grab_focus()
	else:
		%RestartButton.grab_focus()


func resume_match() -> void:
	if simulation.world.is_running():
		super.resume_match()
