# MobileLayout.gd — responsive landscape metrics shared by HUD and shops.
# The viewport is allowed to expand horizontally (like pygame create_display),
# while the arena keeps its 16:9 play area and the command rail lives at right.
extends Node

signal layout_changed

const DESIGN_SIZE := Vector2(1280.0, 720.0)
const SIDE_PANEL_WIDTH := 280.0
const SIDE_PANEL_MIN_WIDTH := 980.0
var viewport_size := DESIGN_SIZE

func _ready() -> void:
	get_tree().root.size_changed.connect(_on_viewport_changed)
	_on_viewport_changed()

func _on_viewport_changed() -> void:
	viewport_size = get_viewport().get_visible_rect().size
	layout_changed.emit()

func has_side_panel() -> bool:
	return viewport_size.x >= SIDE_PANEL_MIN_WIDTH and viewport_size.x > viewport_size.y

func side_panel_rect() -> Rect2:
	if not has_side_panel():
		return Rect2()
	return Rect2(viewport_size.x - SIDE_PANEL_WIDTH, 0.0,
		SIDE_PANEL_WIDTH, viewport_size.y)

func content_width() -> float:
	return maxf(0.0, viewport_size.x - (SIDE_PANEL_WIDTH if has_side_panel() else 0.0))
