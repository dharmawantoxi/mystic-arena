extends Control

signal combat_requested
signal play_requested
signal quit_requested

const UI_THEME = preload("res://scripts/ui/rebuild_theme.gd")


func _ready() -> void:
	theme = UI_THEME.create_theme()
	UI_THEME.title(%Title, 56)
	UI_THEME.muted(%Subtitle)
	UI_THEME.muted(%Scope)
	%PlayButton.pressed.connect(func() -> void: play_requested.emit())
	%QuitButton.pressed.connect(func() -> void: quit_requested.emit())
	%CombatButton.pressed.connect(func() -> void: combat_requested.emit())
	%CombatButton.grab_focus()
