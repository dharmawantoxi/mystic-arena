# SidePanel.gd — compact landscape command rail, matching pygame's right HUD.
extends Control

const BG := Color(0.055, 0.064, 0.10, 0.97)
const EDGE := Color(0.42, 0.34, 0.22, 1.0)
const TEXT := Color(0.88, 0.91, 0.98, 1.0)
const GOLD := Color(1.0, 0.80, 0.33, 1.0)
var _buttons: Array[Button] = []

func _ready() -> void:
	name = "SidePanel"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	MobileLayout.layout_changed.connect(_layout)
	_build()
	_layout()

func _build() -> void:
	var panel := PygamePanel.new(EDGE, 2.0, 0.0)
	panel.name = "StoneRail"
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.set_margins(18, 22, 18, 22)
	add_child(panel)
	var box := VBoxContainer.new()
	box.name = "Commands"
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_theme_constant_override("separation", 9)
	panel.add_child(box)
	var title := Label.new()
	title.text = "  MYSTIC ARENA"
	title.add_theme_color_override("font_color", GOLD)
	title.add_theme_font_size_override("font_size", 17)
	box.add_child(title)
	var hint := Label.new()
	hint.text = "  SHOP & FORGE"
	hint.add_theme_color_override("font_color", TEXT)
	hint.add_theme_font_size_override("font_size", 12)
	box.add_child(hint)
	_add_button(box, "TOWER SHOP", "tower")
	_add_button(box, "CASTLE SHOP", "nexus")
	_add_button(box, "HERO SHOP", "hero")
	_add_button(box, "ITEM FORGE", "item")

func _add_button(box: VBoxContainer, label: String, tab: String) -> void:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(220, 42)
	button.mouse_filter = Control.MOUSE_FILTER_STOP
	button.pressed.connect(_open_shop.bind(tab))
	box.add_child(button)
	_buttons.append(button)

func _open_shop(tab: String) -> void:
	if GameManager.state != "playing":
		return
	GameManager.requested_shop_tab = tab
	GameManager.open_shop()

func _layout() -> void:
	if get_child_count() == 0:
		return
	var panel := get_child(0) as Control
	var rect := MobileLayout.side_panel_rect()
	panel.visible = MobileLayout.has_side_panel()
	panel.position = rect.position
	panel.size = rect.size
	panel.set("modulate", Color(1, 1, 1, 1))
	if panel.get_child_count() > 0:
		var box := panel.get_child(0) as Control
		box.position = Vector2(18, 22)
		box.size = Vector2(maxf(0, rect.size.x - 36), maxf(0, rect.size.y - 44))
