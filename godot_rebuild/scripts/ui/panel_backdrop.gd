extends Control
## The stone strip `platform_utils._gambar_panel_samping` paints into the
## leftover width of the Android display surface.
##
## `create_display()` draws it once on the FULL surface, before the menu or the
## match exist, so on a 2436x1080 device the 344 px right of the 1280 px arena
## are stone on every screen. The match dock already reproduces that wall
## (`side_panel.gd`); the main menu has no dock, so this node fills the strip
## there and the menu art stays anchored to the arena instead of being centred.
##
## Keep the node full-rect: it draws only the dock rect for the current logical
## width (`SidePanelLayout.panel_rect`).

const Layout = preload("res://scripts/ui/side_panel_layout.gd")
const PanelStone = preload("res://scripts/ui/panel_stone.gd")

var panel := Rect2i()
var stone: Array = []
var draw_count := 0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	resized.connect(_refresh)
	_refresh()


## Logical width of the surface the node spans (1280 on 16:9, 1624 on the
## 2436x1080 test device).
func logical_width() -> int:
	return int(round(size.x))


func _refresh() -> void:
	panel = Layout.panel_rect(logical_width())
	stone = PanelStone.bricks(panel)
	visible = panel.size.x > 0
	if is_inside_tree():
		queue_redraw()


func _draw() -> void:
	if panel.size.x <= 0:
		return
	draw_set_transform(Vector2(panel.position), 0.0, Vector2.ONE)
	PanelStone.paint(self, Vector2(panel.size), stone)
	draw_set_transform(Vector2.ZERO)
	draw_count += 1
