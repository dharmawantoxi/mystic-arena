extends "res://scenes/combat/combat_screen.gd"

const Siege = preload("res://scripts/combat/siege_battle.gd")
const SiegeSession = preload("res://scripts/simulation/siege_session.gd")
const Structure = preload("res://scripts/combat/structure_state.gd")


func _ready() -> void:
	super._ready()
	%TeamMode.add_item("Kedua tim")
	%TeamMode.add_item("Biru")
	%TeamMode.add_item("Merah")


func _process(delta: float) -> void:
	super._process(delta)
	var world := simulation.world as Siege
	var blue := world.nexuses[0]
	var red := world.nexuses[1]
	%StatusLabel.text = (
		"Nexus B %.0f (+%.0f)  /  R %.0f (+%.0f)" % [blue.hp, blue.shield, red.hp, red.shield]
	)
	var count := 6 if %TeamMode.selected == 0 else 3
	%SpawnButton.disabled = (
		not world.is_running()
		or get_tree().paused
		or simulation.pending_wave >= 0
		or world.units.size() + count > world.MAX_UNITS
	)
	var selected := world.get_unit(simulation.selected_id)
	if selected is Structure:
		var structure := selected as Structure
		%SelectionLabel.text += (
			" · Shield %.0f/%.0f" % [structure.shield, structure.settings().shield_capacity]
		)
	elif selected == null:
		%SelectionLabel.text = "Klik unit/bangunan · Uji satu tim · Shield nexus gratis sampai wave 10"
	if not world.is_running():
		%ArenaTitle.text = "BIRU MENANG" if world.winner == 0 else "MERAH MENANG"
		%SelectionLabel.text = "Nexus hancur. Tanpa progres tersimpan. Jeda → Mulai ulang / Menu."
		%PauseButton.text = "Hasil [Esc]"


func _request_wave() -> void:
	(simulation as SiegeSession).request_assault(%MinionType.selected, %TeamMode.selected - 1)


func pause_match() -> void:
	super.pause_match()
	var world := simulation.world as Siege
	if not world.is_running():
		%PauseTitle.text = "BIRU MENANG" if world.winner == 0 else "MERAH MENANG"
		%ResumeButton.hide()
