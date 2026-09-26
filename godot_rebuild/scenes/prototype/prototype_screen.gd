extends "res://scenes/combat/combat_screen.gd"
## Separate playable subset; shared input/pause plumbing, no manual laboratory wave controls.

const Prototype = preload("res://scripts/match/prototype_battle.gd")
const PrototypeSession = preload("res://scripts/simulation/prototype_session.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")

var result_shown := false
@onready var match_session: PrototypeSession = $Simulation


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UI_THEME.create_theme()
	arena.session = simulation
	UI_THEME.title(%ArenaTitle, 23)
	UI_THEME.title(%PauseTitle, 32)
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
	%NexusButton.pressed.connect(
		func() -> void: match_session.request_nexus_upgrade(match_session.selected_id)
	)
	%PauseButton.pressed.connect(pause_match)
	%ResumeButton.pressed.connect(resume_match)
	%RestartButton.pressed.connect(func() -> void: restart_requested.emit())
	%MenuButton.pressed.connect(func() -> void: menu_requested.emit())
	%BackButton.pressed.connect(func() -> void: menu_requested.emit())
	%PauseButton.grab_focus()


func _process(_delta: float) -> void:
	var world := simulation.world as Prototype
	%GoldLabel.text = "GOLD  %d G   ·   Lawan %d G" % [world.economy.gold[0], world.economy.gold[1]]
	var next_wave := "menunggu lane bersih"
	if world.scheduler.remaining_ticks > 0:
		next_wave = "%.1f s" % (world.scheduler.remaining_ticks / 60.0)
	elif world.scheduler.pending_count() > 0:
		next_wave = "menunggu antrean spawn"
	%TickLabel.text = "WAVE %02d  ·  Berikut: %s" % [world.wave_count, next_wave]
	var blue := world.nexuses[0]
	var red := world.nexuses[1]
	%StatusLabel.text = (
		"Nexus B %.0f (+%.0f)  /  R %.0f (+%.0f)" % [blue.hp, blue.shield, red.hp, red.shield]
	)
	var slot := world.get_slot(match_session.selected_slot_id)
	var selected := world.get_unit(simulation.selected_id)
	var tower := selected as Structure
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
	# Contextual paths: Cannon/Ice appear only for a blue level-1 tower,
	# and Nexus steps aside while they do. At most five buttons show.
	%CannonButton.visible = path_choice
	%IceButton.visible = path_choice
	%NexusButton.visible = not path_choice
	var nexus_price := world.nexus_upgrade_price(simulation.selected_id)
	%NexusButton.disabled = locked or nexus_price <= 0 or world.economy.gold[0] < nexus_price
	%UpgradeButton.text = "Upgrade Archer"
	%CannonButton.text = "Cannon Lv.2"
	%IceButton.text = "Ice Lv.2"
	%NexusButton.text = "Upgrade Nexus"
	%SellButton.text = "Jual tower"
	if tower != null and tower.settings().structure_kind == "tower":
		%SellButton.text = "Jual · %d G" % tower.settings().sale_refund
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
		%SelectionLabel.text = (
			"%s #%d · %s · HP %.0f/%d"
			% [
				selected.definition.display_name,
				selected.id,
				"BIRU" if selected.team == 0 else "MERAH",
				selected.hp,
				selected.definition.max_hp
			]
		)
		if tower != null and tower.settings().structure_kind == "tower":
			var ammo := "panah"
			if tower.settings().tower_path == "cannon":
				ammo = "peluru"
			elif tower.settings().tower_path == "ice":
				ammo = "kristal"
			%SelectionLabel.text += (
				" · Shield %.0f · DMG %d · %d %s"
				% [tower.shield, tower.definition.damage, tower.settings().volley_count, ammo]
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
