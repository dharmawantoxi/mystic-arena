class_name IntegrationView
extends GameplayPort

var detail: Label


func _ready() -> void:
	var center := CenterContainer.new()
	add_child(center)
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var panel := Ui.panel()
	panel.custom_minimum_size = Vector2(760, 0)
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 18)
	panel.add_child(column)
	column.add_child(Ui.label("MODE INTEGRASI", 16, Ui.GOLD))
	column.add_child(Ui.label("Gameplay belum terhubung", 34, Ui.TEXT, true))
	detail = Ui.label("", 21)
	detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(detail)
	var explanation := Ui.label(
		(
			"Splash, menu, pause, input, audio, dan siklus hidup sudah berjalan di Godot. "
			+ "Hero, boss, pertarungan, dan penyimpanan level masih perlu diport dari Python."
		),
		20,
		Ui.MUTED
	)
	explanation.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(explanation)
	var hint := Ui.label(
		(
			"Integrasi: Main.game_scene → scene turunan GameplayPort.\n"
			+ "Esc / JEDA menguji alur pause tanpa memulai pertarungan palsu."
		),
		17,
		Ui.GOLD
	)
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(hint)
	var back := Ui.button("Kembali ke menu", true)
	back.pressed.connect(func() -> void: menu_requested.emit())
	column.add_child(back)
	configure(level_number, is_replay)


func configure(level: int, replay := false) -> void:
	super.configure(level, replay)
	if detail != null:
		detail.text = (
			"Level %02d%s • kontrak gameplay siap dihubungkan"
			% [level, " • replay" if replay else ""]
		)
