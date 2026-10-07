extends "res://scenes/combat/combat_screen.gd"
## Separate playable subset; shared input/pause plumbing, no manual laboratory wave controls.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const ItemForgePanel = preload("res://scripts/ui/item_forge_panel.gd")
const ProgressStore = preload("res://scripts/match/level_progress_store.gd")
const Tactical = preload("res://scripts/match/tactical_commands.gd")
## Port of the `mobile/sidepanel.py` "TACTICAL COMMANDS (HOLD)" box: the five
## source orders with their labels, colors, tooltips and enable rules. The
## desktop keys G/F/T/C/B/D drive the same manager (`_core.py` KEYDOWN/KEYUP).
const TACTICAL_ORDER := [
	{
		"command": Tactical.GATHER,
		"node": "TacticalGather",
		"label": "GATHER [G]",
		"color": Color8(120, 200, 255),
		"tip": "Semua hero kumpul & serang bersama"
	},
	{
		"command": Tactical.PROTECT_TOWER,
		"node": "TacticalProtectTower",
		"label": "PROTECT TOWER [T]",
		"color": Color8(120, 235, 140),
		"tip": "Min 2 hero lindungi tower"
	},
	{
		"command": Tactical.PROTECT_CASTLE,
		"node": "TacticalProtectCastle",
		"label": "PROTECT CASTLE [C]",
		"color": Color8(255, 205, 90),
		"tip": "Semua hero lindungi castle"
	},
	{
		"command": Tactical.ATTACK_BOSS,
		"node": "TacticalAttackBoss",
		"label": "ATTACK BOSS [B]",
		"color": Color8(255, 110, 110),
		"tip": "Semua hero serang boss"
	},
	{
		"command": Tactical.ATTACK_DAMAGE_DEALER,
		"node": "TacticalAttackDamageDealer",
		"label": "ATTACK DMG DEALER [D]",
		"color": Color8(190, 165, 255),
		"tip": "Fokus hero musuh damage terbesar"
	}
]

var progress_path := ProgressStore.PATH
var result_shown := false
var forge_panel: ItemForgePanel
var ai_toggle: Button
var migration_status: Label
var tactical_bar: VBoxContainer
var tactical_buttons: Dictionary = {}
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
	%CannonButton.pressed.connect(
		func() -> void: match_session.request_upgrade(match_session.selected_id, "cannon")
	)
	%IceButton.pressed.connect(
		func() -> void: match_session.request_upgrade(match_session.selected_id, "ice")
	)
	%MageButton.pressed.connect(
		func() -> void: match_session.request_upgrade(match_session.selected_id, "mage")
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
	_build_forge_ui()
	_build_ai_toggle()
	_build_migration_status()
	_build_tactical_bar()
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
	var cursor := _arena_point(get_viewport().get_mouse_position())
	match_session.set_mouse_position(cursor)
	if forge_panel != null and forge_panel.visible:
		forge_panel.refresh()
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
		# `TacticalCommandManager.get_status_text` is the source HUD/debug line.
		migration_status.text = (
			"%s   |   %s   |   %s" % [boss_text, ai_text, world.tactical.status_text()]
		)
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
	%BuildButton.disabled = (
		locked
		or slot == null
		or slot.team != 0
		or slot.structure_id != -1
		or world.economy.gold[0] < world.Economy.BUILD_COST
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
	var cannon_price := world.upgrade_price(simulation.selected_id, "cannon")
	var ice_price := world.upgrade_price(simulation.selected_id, "ice")
	var path_choice := (
		tower != null
		and tower.settings().structure_kind == "tower"
		and tower.team == 0
		and tower.settings().level == 1
	)
	%CannonButton.disabled = (
		locked or not path_choice or cannon_price <= 0 or world.economy.gold[0] < cannon_price
	)
	%IceButton.disabled = (
		locked or not path_choice or ice_price <= 0 or world.economy.gold[0] < ice_price
	)
	var mage_price := world.upgrade_price(simulation.selected_id, "mage")
	%MageButton.disabled = (
		locked or not path_choice or mage_price <= 0 or world.economy.gold[0] < mage_price
	)
	# Contextual paths: Cannon/Ice/Mage appear only for a blue level-1
	# tower, and Nexus steps aside while they do. Paths get their own
	# row so seven buttons never share one.
	%CannonButton.visible = path_choice
	%IceButton.visible = path_choice
	%MageButton.visible = path_choice
	%Paths.visible = path_choice
	%NexusButton.visible = not path_choice
	var nexus_price := world.nexus_upgrade_price(simulation.selected_id)
	%NexusButton.disabled = locked or nexus_price <= 0 or world.economy.gold[0] < nexus_price
	var hero_ready := hero != null and hero.team == 0 and world.blue_q_ready()
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
	%UpgradeButton.text = "Upgrade Archer"
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
	%SelectionLabel.text = "Slot biru: bangun Archer. Tower biru: jual kembali."
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
	_refresh_tactical_bar(world, locked)
	%ActionLabel.text = match_session.last_action
	if not world.is_running() and not result_shown:
		result_shown = true
		%ArenaTitle.text = "BIRU MENANG" if world.winner == 0 else "MERAH MENANG"
		%PauseButton.text = "Hasil [Esc]"
		pause_match()
		_save_result()


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


func _toggle_forge() -> void:
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


func _build_tactical_bar() -> void:
	## Right-side order bar. Source buttons are hidden unless their precondition
	## holds (`btn.visible = bool(enabled)`), and a press is a HOLD that keeps the
	## order enforced until release (`main.py` tracks the same press/release).
	tactical_bar = VBoxContainer.new()
	tactical_bar.name = "TacticalBar"
	tactical_bar.position = Vector2(1092, 140)
	tactical_bar.add_theme_constant_override("separation", 4)
	var title := Label.new()
	title.name = "TacticalTitle"
	title.text = "TACTICAL COMMANDS (HOLD)"
	title.add_theme_font_size_override("font_size", 12)
	title.modulate = Color("ffd15a")
	tactical_bar.add_child(title)
	for entry in TACTICAL_ORDER:
		var command := String(entry.command)
		var button := Button.new()
		button.name = String(entry.node)
		button.text = String(entry.label)
		button.tooltip_text = String(entry.tip)
		button.custom_minimum_size = Vector2(180, 30)
		button.add_theme_font_size_override("font_size", 12)
		button.add_theme_color_override("font_color", entry.color)
		button.button_down.connect(_tactical_panel_press.bind(command))
		button.button_up.connect(_tactical_panel_release.bind(command))
		tactical_bar.add_child(button)
		tactical_buttons[command] = button
	$HUD.add_child(tactical_bar)


func _refresh_tactical_bar(world: Prototype, locked: bool) -> void:
	if tactical_bar == null:
		return
	var tactical := world.tactical
	var blue_heroes := tactical.alive_blue_heroes().size()
	var boss_ready := world.active_boss != null and world.active_boss.alive
	var dealer_ready := not tactical.red_heroes().is_empty()
	for entry in TACTICAL_ORDER:
		var command := String(entry.command)
		var button: Button = tactical_buttons[command]
		var ready := false
		match command:
			Tactical.PROTECT_TOWER:
				ready = blue_heroes >= 1
			Tactical.ATTACK_BOSS:
				ready = boss_ready
			Tactical.ATTACK_DAMAGE_DEALER:
				ready = dealer_ready
			_:
				ready = blue_heroes > 0
		button.visible = ready
		button.disabled = locked or not ready
		var held := ready and tactical.held_command == command
		button.text = ("%s  HOLD" % String(entry.label)) if held else String(entry.label)


func _tactical_panel_press(command: String) -> void:
	# The side panel issues the order without coordinates (mobile/hud.py), so a
	# panel GATHER uses the source default point instead of the cursor.
	match_session.request_tactical_hold(command)


func _tactical_panel_release(command: String) -> void:
	match_session.request_tactical_release(command)


func _tactical_key_press(command: String) -> void:
	# `_core.py`: GATHER at the cursor when it is inside the arena, and the point
	# keeps following the cursor while the key is held (follow_mouse=True).
	var local := _arena_point(get_viewport().get_mouse_position())
	var gather := command == Tactical.GATHER
	var tactical := (simulation.world as Prototype).tactical
	match_session.request_tactical_hold(
		command, local, gather and tactical.inside_arena(local), gather
	)


func _tactical_command_for(keycode: int) -> String:
	# `_core.py::InputHandler.TACTICAL_KEY_TO_COMMAND`.
	match keycode:
		KEY_G, KEY_F:
			return Tactical.GATHER
		KEY_T:
			return Tactical.PROTECT_TOWER
		KEY_C:
			return Tactical.PROTECT_CASTLE
		KEY_B:
			return Tactical.ATTACK_BOSS
		KEY_D:
			return Tactical.ATTACK_DAMAGE_DEALER
	return ""


func _arena_point(point: Vector2) -> Vector2:
	return arena.get_global_transform_with_canvas().affine_inverse() * point


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


func _unhandled_input(event: InputEvent) -> void:
	if _handle_hotkey(event):
		return
	if _handle_tactical_key(event):
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


func _handle_hotkey(event: InputEvent) -> bool:
	# Existing single-press hotkeys: AI toggle, item forge and the blue QWER.
	if not (event is InputEventKey) or not event.pressed or event.echo:
		return false
	match event.physical_keycode:
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
			return false
	get_viewport().set_input_as_handled()
	return true


func _handle_tactical_key(event: InputEvent) -> bool:
	## Port of `_core.py::InputHandler.handle_key` / `handle_key_up` for the
	## tactical keys. Key repeat (echo) is passed through on purpose: the source
	## KEYDOWN repeat reaches `hold_start`, which ignores a repeated press of the
	## command it already holds.
	if not (event is InputEventKey):
		return false
	var command := _tactical_command_for(event.physical_keycode)
	if command.is_empty():
		return false
	if event.pressed:
		_tactical_key_press(command)
	else:
		match_session.request_tactical_release(command)
	get_viewport().set_input_as_handled()
	return true


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
	super.pause_match()
	var world := simulation.world as Prototype
	if not world.is_running():
		%PauseTitle.text = "BIRU MENANG" if world.winner == 0 else "MERAH MENANG"
		%ResumeButton.hide()
		%RestartButton.grab_focus()


func resume_match() -> void:
	if simulation.world.is_running():
		super.resume_match()
